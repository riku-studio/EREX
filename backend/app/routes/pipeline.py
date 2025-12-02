from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.services.email_parser import parse_directory, parse_email_file
from app.services.pipeline import Pipeline
from app.services.pipeline_config import (
    PipelineConfigData,
    PipelineConfigService,
    get_pipeline_config_service,
)
from app.utils.config import Config, PROJECT_ROOT
from app.utils.logging import logger
from app.utils.openai_client import get_openai_client


DATA_DIR = PROJECT_ROOT / "data"
router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class PipelineConfigResponse(BaseModel):
    summary: dict
    steps: List[str]
    line_filter: dict
    semantic_templates: dict
    keywords_tech: dict
    index_rules: dict
    classifier_foreigner: dict
    source: str = "file"

    @classmethod
    def from_service(cls, data: PipelineConfigData, summary: dict, source: str) -> "PipelineConfigResponse":
        return cls(
            summary=summary,
            steps=data.steps,
            line_filter=data.line_filter,
            semantic_templates=data.semantic_templates,
            keywords_tech=data.keywords_tech,
            index_rules=data.index_rules,
            classifier_foreigner=data.classifier_foreigner,
            source=source,
        )


class PipelineRunResponse(BaseModel):
    results: list
    summary: dict


class FileUploadResponse(BaseModel):
    filename: str
    size: int


class FileListItem(BaseModel):
    filename: str
    size: int


class FileDeleteResponse(BaseModel):
    deleted: int
    skipped: int


def _ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


class PipelineConfigPayload(BaseModel):
    steps: List[str]
    line_filter: dict
    semantic_templates: dict
    keywords_tech: dict
    index_rules: dict
    classifier_foreigner: dict

    class Config:
        extra = "ignore"


@router.get("/config", response_model=PipelineConfigResponse)
async def get_pipeline_config(service: PipelineConfigService = Depends(get_pipeline_config_service)):
    config_data, source = await service.load_config()
    return PipelineConfigResponse.from_service(config_data, summary=service.build_summary(), source=source)


@router.post("/upload", response_model=List[FileUploadResponse])
async def upload_files(files: List[UploadFile] = File(description="files[] upload; use field name 'files' or 'files[]'")):
    data_dir = _ensure_data_dir()
    responses: List[FileUploadResponse] = []
    for file in files:
        target = data_dir / Path(file.filename).name
        with target.open("wb") as fp:
            shutil.copyfileobj(file.file, fp)
        responses.append(FileUploadResponse(filename=target.name, size=target.stat().st_size))
    return responses


@router.delete("/files", response_model=FileDeleteResponse)
def delete_files(filenames: List[str]):
    data_dir = _ensure_data_dir()
    deleted = 0
    skipped = 0
    for name in filenames:
        target = data_dir / Path(name).name
        if target.exists():
            try:
                target.unlink()
                deleted += 1
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to delete %s: %s", target, exc)
                skipped += 1
        else:
            skipped += 1
    return FileDeleteResponse(deleted=deleted, skipped=skipped)


@router.put("/config", response_model=PipelineConfigResponse)
async def update_pipeline_config(
    payload: PipelineConfigPayload, service: PipelineConfigService = Depends(get_pipeline_config_service)
):
    try:
        stored, source = await service.save_config(PipelineConfigData.from_dict(payload.dict()))
    except Exception as exc:  # pragma: no cover - db connectivity
        logger.error("Failed to save pipeline config: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to save pipeline configuration to database",
        ) from exc
    return PipelineConfigResponse.from_service(stored, summary=service.build_summary(), source=source)


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(service: PipelineConfigService = Depends(get_pipeline_config_service)):
    await service.load_config()
    data_dir = _ensure_data_dir()
    if not data_dir.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="data directory missing")

    # Parse all files under data_dir (eml/msg/pst)
    contents = []
    for path in data_dir.iterdir():
        if path.is_file():
            contents.extend(parse_email_file(path))
    if not contents:
        return PipelineRunResponse(
            results=[],
            summary={"message_count": 0, "block_count": 0, "keyword_summary": {}, "class_summary": {}},
        )

    pipeline = Pipeline(Config)
    results = pipeline.process_messages(contents)

    serialized: list = []
    all_blocks = []
    for res in results:
        serialized.append(
            {
                "source_path": res.source_path,
                "subject": res.subject,
                "semantic": res.semantic,
                "aggregation": res.aggregation,
            }
        )
        all_blocks.extend(res.blocks)

    # Overall summary across all messages
    overall = pipeline.aggregator.aggregate_blocks(all_blocks) if pipeline.aggregator else {}
    overall["message_count"] = len(results)

    logger.info("Pipeline summary: %s", overall)

    return PipelineRunResponse(results=serialized, summary=overall)


@router.get("/files", response_model=List[FileListItem])
def list_files():
    data_dir = _ensure_data_dir()
    items: List[FileListItem] = []
    for path in data_dir.iterdir():
        if path.is_file():
            items.append(FileListItem(filename=path.name, size=path.stat().st_size))
    return items


class TechInsightRequest(BaseModel):
    keyword: str
    count: int
    ratio: float
    category: str | None = None


class TechInsightResponse(BaseModel):
    keyword: str
    insight: str


@router.post("/tech-insight", response_model=TechInsightResponse)
def tech_insight(payload: TechInsightRequest):
    # Graceful fallback when OpenAI is not configured or unavailable.
    if not Config.OPENAI_API_KEY:
        fallback = (
            f"{payload.keyword}: tech insight unavailable (no OpenAI key). "
            f"Count={payload.count}, ratio={payload.ratio:.2%}"
        )
        if payload.category:
            fallback += f", category={payload.category}"
        return TechInsightResponse(keyword=payload.keyword, insight=fallback)

    client = get_openai_client()
    if client is None:
        fallback = (
            f"{payload.keyword}: tech insight unavailable (OpenAI client missing). "
            f"Count={payload.count}, ratio={payload.ratio:.2%}"
        )
        if payload.category:
            fallback += f", category={payload.category}"
        return TechInsightResponse(keyword=payload.keyword, insight=fallback)

    prompt = (
        "You are a concise tech explainer for a recruitment analytics dashboard. "
        f"The keyword '{payload.keyword}' appeared in {payload.count} blocks "
        f"with a ratio of {payload.ratio:.2%} relative to all blocks. "
        "Describe what this technology is and its typical use cases. "
        "Keep it under 100 words. If applicable, mention how common it is implied by the ratio. "
        "Provide the explanation in Japanese."
    )
    if payload.category:
        prompt += f" Category hint: {payload.category}."

    def _extract_text(content) -> str:
        if isinstance(content, str):
            return content
        try:
            return "".join(getattr(part, "text", "") for part in content if hasattr(part, "text"))
        except Exception:
            return str(content) if content else ""

    try:
        response = client.responses.create(
            model=Config.OPENAI_MODEL,
            input=prompt
        )
        insight = _extract_text(response.output_text) or ""
    except Exception as exc:  # pragma: no cover - network/dep issues
        logger.error("OpenAI request failed: %s", exc)
        fallback = (
            f"{payload.keyword}: tech insight unavailable (OpenAI request failed). "
            f"Count={payload.count}, ratio={payload.ratio:.2%}"
        )
        if payload.category:
            fallback += f", category={payload.category}"
        return TechInsightResponse(keyword=payload.keyword, insight=fallback)

    if not insight.strip():
        insight = (
            f"{payload.keyword}: tech insight unavailable (empty response). "
            f"Count={payload.count}, ratio={payload.ratio:.2%}"
            + (f", category={payload.category}" if payload.category else "")
        )

    return TechInsightResponse(keyword=payload.keyword, insight=insight)
