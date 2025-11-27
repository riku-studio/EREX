from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.services.email_parser import parse_directory, parse_email_file
from app.services.pipeline import Pipeline
from app.utils.config import Config, PROJECT_ROOT
from app.utils.logging import logger
from app.utils.openai_client import get_openai_client


DATA_DIR = PROJECT_ROOT / "data"
router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class PipelineConfigResponse(BaseModel):
    summary: dict
    steps: List[str]


class PipelineRunResponse(BaseModel):
    results: list
    summary: dict


class FileUploadResponse(BaseModel):
    filename: str
    size: int


class FileDeleteResponse(BaseModel):
    deleted: int
    skipped: int


def _ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


@router.get("/config", response_model=PipelineConfigResponse)
def get_pipeline_config():
    return PipelineConfigResponse(summary=Config.summary(), steps=Config.PIPELINE_STEPS)


@router.post("/upload", response_model=List[FileUploadResponse])
async def upload_files(files: List[UploadFile] = File(...)):
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


@router.post("/run", response_model=PipelineRunResponse)
def run_pipeline():
    data_dir = _ensure_data_dir()
    if not data_dir.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="data directory missing")

    # Parse all files under data_dir (eml/msg/pst)
    contents = []
    for path in data_dir.iterdir():
        if path.is_file():
            contents.extend(parse_email_file(path))
    if not contents:
        return PipelineRunResponse(results=[])

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

    return PipelineRunResponse(results=serialized, summary=overall)


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
    if not Config.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured on the server.",
        )

    client = get_openai_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI client unavailable (missing dependency?).",
        )

    prompt = (
        "You are a concise tech explainer for a recruitment analytics dashboard. "
        f"The keyword '{payload.keyword}' appeared in {payload.count} blocks "
        f"with a ratio of {payload.ratio:.2%} relative to all blocks. "
        "Describe what this technology is and its typical use cases. "
        "Keep it under 100 words. If applicable, mention how common it is implied by the ratio."
    )
    if payload.category:
        prompt += f" Category hint: {payload.category}."

    try:
        completion = client.responses.create(
            model=Config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_output_tokens=200,
        )
        insight = completion.output_text
    except Exception as exc:  # pragma: no cover - network/dep issues
        logger.error("OpenAI request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI request failed: {exc}",
        ) from exc

    return TechInsightResponse(keyword=payload.keyword, insight=insight)
