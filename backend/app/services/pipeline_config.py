from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

from app.utils.config import Config
from app.utils.logging import logger


def _load_json_safe(path: str) -> Dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to load JSON from %s: %s", path, exc)
        return {}


@dataclass
class PipelineConfigData:
    steps: List[str]
    line_filter: Dict[str, Any]
    semantic_templates: Dict[str, Any]
    keywords_tech: Dict[str, Any]
    index_rules: Dict[str, Any]
    classifier_foreigner: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfigData":
        return cls(
            steps=[str(step).strip() for step in data.get("steps", []) if str(step).strip()],
            line_filter=data.get("line_filter", {}) or {},
            semantic_templates=data.get("semantic_templates", {}) or {},
            keywords_tech=data.get("keywords_tech", {}) or {},
            index_rules=data.get("index_rules", {}) or {},
            classifier_foreigner=data.get("classifier_foreigner", {}) or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": self.steps,
            "line_filter": self.line_filter,
            "semantic_templates": self.semantic_templates,
            "keywords_tech": self.keywords_tech,
            "index_rules": self.index_rules,
            "classifier_foreigner": self.classifier_foreigner,
        }


class PipelineConfigRepository:
    """Simple asyncpg-backed key/value storage for pipeline configuration."""

    def __init__(self, config: type[Config] = Config, table_name: str = "pipeline_configs"):
        self.config = config
        self.table_name = table_name

    def _dsn(self) -> str:
        user = self.config.DB_USER
        password = self.config.DB_PASS
        host = self.config.DB_HOST
        port = self.config.DB_PORT
        db = self.config.DB_NAME
        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{db}"
        return f"postgresql://{user}@{host}:{port}/{db}"

    async def _ensure_table(self, conn: asyncpg.Connection) -> None:
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                key TEXT PRIMARY KEY,
                content JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

    async def load(self) -> Optional[PipelineConfigData]:
        conn = await asyncpg.connect(self._dsn())
        try:
            await self._ensure_table(conn)
            row = await conn.fetchrow(
                f"SELECT content FROM {self.table_name} WHERE key = $1",
                "active",
            )
            if not row:
                return None
            return PipelineConfigData.from_dict(row["content"])
        finally:
            await conn.close()

    async def save(self, payload: PipelineConfigData) -> PipelineConfigData:
        conn = await asyncpg.connect(self._dsn())
        try:
            await self._ensure_table(conn)
            await conn.execute(
                f"""
                INSERT INTO {self.table_name} (key, content)
                VALUES ($1, $2)
                ON CONFLICT (key)
                DO UPDATE SET content = EXCLUDED.content, updated_at = NOW()
                """,
                "active",
                payload.to_dict(),
            )
            return payload
        finally:
            await conn.close()


class PipelineConfigService:
    """Manages runtime pipeline configuration, backed by database with file fallbacks."""

    def __init__(self, config: type[Config] = Config, repository: Optional[PipelineConfigRepository] = None):
        self.config = config
        self.repository = repository or PipelineConfigRepository(config=config)
        self.default_paths = {
            "line_filter": config.LINE_FILTER_CONFIG_PATH,
            "semantic_templates": config.SEMANTIC_TEMPLATES_PATH,
            "keywords_tech": config.KEYWORDS_TECH_PATH,
            "index_rules": config.INDEX_RULES_PATH,
            "classifier_foreigner": config.CLASSIFIER_FOREIGNER_PATH,
        }

    def _default_payload(self) -> PipelineConfigData:
        return PipelineConfigData(
            steps=[str(step).strip() for step in self.config.PIPELINE_STEPS if str(step).strip()],
            line_filter=_load_json_safe(self.default_paths["line_filter"]),
            semantic_templates=_load_json_safe(self.default_paths["semantic_templates"]),
            keywords_tech=_load_json_safe(self.default_paths["keywords_tech"]),
            index_rules=_load_json_safe(self.default_paths["index_rules"]),
            classifier_foreigner=_load_json_safe(self.default_paths["classifier_foreigner"]),
        )

    async def load_config(self) -> Tuple[PipelineConfigData, str]:
        try:
            db_config = await self.repository.load()
            if db_config:
                self.apply_to_runtime(db_config, source="db")
                return db_config, "db"
        except Exception as exc:  # pragma: no cover - db connectivity
            logger.error("Failed to load pipeline config from database: %s", exc)

        fallback = self._default_payload()
        self.apply_to_runtime(fallback, source="file")
        return fallback, "file"

    async def save_config(self, payload: PipelineConfigData) -> Tuple[PipelineConfigData, str]:
        saved = await self.repository.save(payload)
        self.apply_to_runtime(saved, source="db")
        return saved, "db"

    def apply_to_runtime(self, payload: PipelineConfigData, source: str) -> None:
        """Push loaded configuration into Config class attributes for runtime consumption."""
        cfg = self.config
        cfg.CONFIG_SOURCE = source
        cfg.PIPELINE_STEPS = tuple(payload.steps)

        cfg._KEYWORDS_TECH = payload.keywords_tech or {}

        semantic = payload.semantic_templates or {}
        cfg._SEMANTIC_TEMPLATES = semantic
        cfg.SEMANTIC_CONTEXT_RADIUS = int(semantic.get("context_radius", cfg.SEMANTIC_CONTEXT_RADIUS))
        cfg.SEMANTIC_JOB_GLOBAL_THRESHOLD = float(
            semantic.get("global_threshold", cfg.SEMANTIC_JOB_GLOBAL_THRESHOLD)
        )
        cfg.SEMANTIC_JOB_FIELD_THRESHOLD = float(semantic.get("field_threshold", cfg.SEMANTIC_JOB_FIELD_THRESHOLD))

        cfg._LINE_FILTER_SETTINGS = payload.line_filter or {}
        cfg.LINE_FILTER_DECORATION_CHARS = cfg._LINE_FILTER_SETTINGS.get("decoration_chars", "")
        cfg.LINE_FILTER_GREETING_PATTERNS = cfg._LINE_FILTER_SETTINGS.get("greeting_patterns", [])
        cfg.LINE_FILTER_CLOSING_PATTERNS = cfg._LINE_FILTER_SETTINGS.get("closing_patterns", [])
        cfg.LINE_FILTER_SIGNATURE_COMPANY_PREFIX = cfg._LINE_FILTER_SETTINGS.get("signature_company_prefix", [])
        cfg.LINE_FILTER_SIGNATURE_KEYWORDS = cfg._LINE_FILTER_SETTINGS.get("signature_keywords", [])
        cfg.LINE_FILTER_FOOTER_PATTERNS = cfg._LINE_FILTER_SETTINGS.get("footer_patterns", [])
        cfg.LINE_FILTER_JOB_KEYWORDS = cfg._LINE_FILTER_SETTINGS.get("job_keywords", [])
        cfg.LINE_FILTER_FORCE_DELETE_PATTERNS = cfg._LINE_FILTER_SETTINGS.get("force_delete_patterns", [])

        cfg.CLASSIFIER_FOREIGNER_CONFIG = payload.classifier_foreigner or {}
        cfg.INDEX_RULES_INLINE = payload.index_rules or {}

    def build_summary(self) -> Dict[str, Any]:
        summary = dict(Config.summary())
        summary["config_source"] = getattr(self.config, "CONFIG_SOURCE", "file")
        summary["pipeline_steps"] = list(self.config.PIPELINE_STEPS)
        return summary


def get_pipeline_config_service() -> PipelineConfigService:
    return PipelineConfigService()
