from __future__ import annotations

import asyncio
import shutil
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.services.email_parser import parse_email_file
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
SUPPORTED_EMAIL_SUFFIXES = {".eml", ".msg", ".pst"}
_PIPELINE_JOBS: Dict[str, Dict[str, Any]] = {}
_PIPELINE_JOBS_LOCK = Lock()


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


class PipelineRunStartResponse(BaseModel):
    job_id: str
    status: str


class PipelineRunProgressResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    stage: str
    message: str
    current: int
    total: int
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_run_response() -> PipelineRunResponse:
    return PipelineRunResponse(
        results=[],
        summary={"message_count": 0, "block_count": 0, "keyword_summary": {}, "class_summary": {}},
    )


def _create_pipeline_job() -> str:
    job_id = uuid4().hex
    with _PIPELINE_JOBS_LOCK:
        _PIPELINE_JOBS[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0.0,
            "stage": "queued",
            "message": "任务已创建，等待执行",
            "current": 0,
            "total": 0,
            "error": None,
            "started_at": None,
            "finished_at": None,
            "result": None,
        }
    return job_id


def _update_pipeline_job(job_id: str, **kwargs: Any) -> None:
    with _PIPELINE_JOBS_LOCK:
        state = _PIPELINE_JOBS.get(job_id)
        if state is None:
            return
        state.update(kwargs)


def _get_pipeline_job(job_id: str) -> Dict[str, Any]:
    with _PIPELINE_JOBS_LOCK:
        state = _PIPELINE_JOBS.get(job_id)
        if state is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
        return dict(state)


def _execute_pipeline_run(
    progress_hook: Callable[[float, str, str, int, int], None] | None = None,
) -> PipelineRunResponse:
    def _notify(progress: float, stage_name: str, message: str, current: int, total: int) -> None:
        if progress_hook is None:
            return
        bounded = min(100.0, max(0.0, float(progress)))
        progress_hook(bounded, stage_name, message, current, total)

    data_dir = _ensure_data_dir()
    if not data_dir.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="data directory missing")

    files = [path for path in data_dir.iterdir() if path.is_file()]
    email_files = [path for path in files if path.suffix.lower() in SUPPORTED_EMAIL_SUFFIXES]
    total_files = len(email_files)

    if total_files == 0:
        _notify(100.0, "completed", "没有可处理的邮件文件", 0, 0)
        return _empty_run_response()

    contents = []
    _notify(2.0, "parse", "扫描并解析邮件文件", 0, total_files)
    for index, path in enumerate(email_files, start=1):
        contents.extend(parse_email_file(path))
        _notify(5.0 + (20.0 * index / total_files), "parse", f"已解析: {path.name}", index, total_files)

    if not contents:
        _notify(100.0, "completed", "邮件解析完成，但无有效消息", total_files, total_files)
        return _empty_run_response()

    pipeline = Pipeline(Config)

    def _on_pipeline_progress(percent: float, stage_name: str, message: str, current: int, total: int) -> None:
        mapped = 28.0 + (68.0 * percent / 100.0)
        _notify(mapped, stage_name, message, current, total)

    _notify(28.0, "pipeline", "进入语义与统计处理", 0, len(contents))
    results = pipeline.process_messages(contents, progress_callback=_on_pipeline_progress)
    _notify(97.0, "finalize", "整理统计结果", len(results), len(results))

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

    overall = pipeline.aggregator.aggregate_blocks(all_blocks) if pipeline.aggregator else {}
    overall["message_count"] = len(results)

    logger.info("Pipeline summary: %s", overall)
    _notify(100.0, "completed", "处理完成", len(results), len(results))

    return PipelineRunResponse(results=serialized, summary=overall)


async def _run_pipeline_job(job_id: str) -> None:
    _update_pipeline_job(
        job_id,
        status="running",
        progress=1.0,
        stage="starting",
        message="加载运行配置",
        started_at=_utc_now(),
    )
    try:
        service = get_pipeline_config_service()
        await service.load_config()

        def _progress(percent: float, stage_name: str, message: str, current: int, total: int) -> None:
            _update_pipeline_job(
                job_id,
                status="running",
                progress=percent,
                stage=stage_name,
                message=message,
                current=current,
                total=total,
            )

        result = await asyncio.to_thread(_execute_pipeline_run, _progress)
        _update_pipeline_job(
            job_id,
            status="completed",
            progress=100.0,
            stage="completed",
            message="任务执行完成",
            result=result.dict(),
            finished_at=_utc_now(),
        )
    except Exception as exc:  # pragma: no cover - runtime safety
        logger.exception("Pipeline job failed: %s", exc)
        _update_pipeline_job(
            job_id,
            status="failed",
            progress=100.0,
            stage="failed",
            message="任务执行失败",
            error=str(exc),
            finished_at=_utc_now(),
        )


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
    stored, source = await service.save_config(PipelineConfigData.from_dict(payload.dict()))
    if source != "db":
        logger.warning("Pipeline config stored using file fallback; database unavailable.")
    return PipelineConfigResponse.from_service(stored, summary=service.build_summary(), source=source)


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(service: PipelineConfigService = Depends(get_pipeline_config_service)):
    await service.load_config()
    return _execute_pipeline_run()


@router.post("/run/start", response_model=PipelineRunStartResponse)
async def start_pipeline_run():
    job_id = _create_pipeline_job()
    asyncio.create_task(_run_pipeline_job(job_id))
    return PipelineRunStartResponse(job_id=job_id, status="queued")


@router.get("/run/{job_id}/progress", response_model=PipelineRunProgressResponse)
def get_pipeline_progress(job_id: str):
    state = _get_pipeline_job(job_id)
    return PipelineRunProgressResponse(
        job_id=job_id,
        status=str(state.get("status", "unknown")),
        progress=float(state.get("progress", 0.0)),
        stage=str(state.get("stage", "unknown")),
        message=str(state.get("message", "")),
        current=int(state.get("current", 0)),
        total=int(state.get("total", 0)),
        error=state.get("error"),
        started_at=state.get("started_at"),
        finished_at=state.get("finished_at"),
    )


@router.get("/run/{job_id}/result", response_model=PipelineRunResponse)
def get_pipeline_result(job_id: str):
    state = _get_pipeline_job(job_id)
    state_status = str(state.get("status", "unknown"))
    if state_status == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=state.get("error") or "pipeline job failed",
        )
    if state_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"job not completed (status={state_status})",
        )
    payload = state.get("result") or _empty_run_response().dict()
    return PipelineRunResponse(**payload)


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
