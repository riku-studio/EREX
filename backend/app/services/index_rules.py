from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Protocol

from app.utils.config import Config
from app.utils.logging import logger


@dataclass
class IndexRule:
    """Represents a single index rule definition."""

    name: str
    pattern: str
    description: str = ""
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "pattern": self.pattern,
            "description": self.description,
            "enabled": self.enabled,
        }


class IndexRuleStore(Protocol):
    async def load_rules(self) -> List[IndexRule]:  # pragma: no cover - interface
        ...


class FileIndexRuleStore:
    def __init__(self, path: str):
        self.path = Path(path)

    async def load_rules(self) -> List[IndexRule]:
        # File-based reads are lightweight; execute synchronously to avoid
        # additional threading overhead in small deployments.
        return self._load_sync()

    def _load_sync(self) -> List[IndexRule]:
        if not self.path.exists():
            logger.warning("Index rules file not found: %s", self.path)
            return []

        try:
            raw = json.loads(self.path.read_text())
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to read index rules file %s: %s", self.path, exc)
            return []

        rules: List[IndexRule] = []
        for item in raw.get("rules", []):
            if not isinstance(item, dict):
                continue
            rule = IndexRule(
                name=str(item.get("name", "")),
                pattern=str(item.get("pattern", "")),
                description=str(item.get("description", "")),
                enabled=bool(item.get("enabled", True)),
            )
            if not rule.name or not rule.pattern:
                logger.debug("Skip invalid index rule entry: %s", item)
                continue
            rules.append(rule)
        return rules


class DatabaseIndexRuleStore:
    def __init__(
        self,
        dsn: str,
        table_name: str,
    ):
        self.dsn = dsn
        self.table_name = self._sanitize_table_name(table_name)

    @staticmethod
    def _sanitize_table_name(table_name: str) -> str:
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table_name):
            raise ValueError("Unsafe index rule table name")
        return table_name

    async def load_rules(self) -> List[IndexRule]:
        try:
            import asyncpg
        except ImportError as exc:  # pragma: no cover - optional dep
            raise RuntimeError(
                "Database index rule source requires asyncpg. Install it before enabling DB mode."
            ) from exc

        try:
            conn = await asyncpg.connect(self.dsn)
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.error("Failed to connect to database for index rules: %s", exc)
            raise

        try:
            rows = await conn.fetch(
                f"""
                SELECT name, pattern, COALESCE(description, '') AS description,
                       COALESCE(enabled, TRUE) AS enabled
                FROM {self.table_name}
                WHERE COALESCE(enabled, TRUE) = TRUE
                ORDER BY name
                """
            )
        finally:
            await conn.close()

        return [
            IndexRule(
                name=row["name"],
                pattern=row["pattern"],
                description=row["description"],
                enabled=row["enabled"],
            )
            for row in rows
        ]


class IndexRuleService:
    def __init__(
        self,
        config: type[Config] = Config,
        store: Optional[IndexRuleStore] = None,
    ):
        self.config = config
        self._store_override = store
        self._store: Optional[IndexRuleStore] = None

    def _create_store(self) -> IndexRuleStore:
        if self._store_override:
            return self._store_override

        source = (self.config.INDEX_RULE_SOURCE or "file").lower()
        if source == "db":
            dsn = self._build_dsn()
            logger.info(
                "Loading index rules from database %s (table=%s)",
                dsn,
                self.config.INDEX_RULE_TABLE,
            )
            return DatabaseIndexRuleStore(dsn=dsn, table_name=self.config.INDEX_RULE_TABLE)

        logger.info("Loading index rules from file: %s", self.config.INDEX_RULES_PATH)
        return FileIndexRuleStore(self.config.INDEX_RULES_PATH)

    def _build_dsn(self) -> str:
        user = self.config.DB_USER
        password = self.config.DB_PASS
        host = self.config.DB_HOST
        port = self.config.DB_PORT
        db = self.config.DB_NAME
        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{db}"
        return f"postgresql://{user}@{host}:{port}/{db}"

    async def list_rules(self) -> List[IndexRule]:
        if self._store is None:
            self._store = self._create_store()
        return await self._store.load_rules()


def get_index_rule_service() -> IndexRuleService:
    return IndexRuleService()
