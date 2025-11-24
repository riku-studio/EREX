import json
from pathlib import Path

import pytest

from app.services.index_rules import (
    DatabaseIndexRuleStore,
    FileIndexRuleStore,
    IndexRule,
    IndexRuleService,
)


@pytest.mark.anyio("asyncio")
async def test_file_index_rule_store_loads_rules(tmp_path: Path):
    payload = {
        "rules": [
            {
                "name": "rule-a",
                "pattern": "foo",
                "description": "test rule",
                "enabled": False,
            }
        ]
    }
    rule_file = tmp_path / "index_rules.json"
    rule_file.write_text(json.dumps(payload))

    store = FileIndexRuleStore(str(rule_file))
    rules = await store.load_rules()

    assert len(rules) == 1
    assert rules[0].name == "rule-a"
    assert rules[0].pattern == "foo"
    assert rules[0].description == "test rule"
    assert rules[0].enabled is False


@pytest.mark.anyio("asyncio")
async def test_index_rule_service_prefers_override_store():
    class DummyStore:
        async def load_rules(self):
            return [IndexRule(name="override", pattern="p")]  # pragma: no cover - simple stub

    service = IndexRuleService(store=DummyStore())
    rules = await service.list_rules()

    assert [rule.name for rule in rules] == ["override"]


@pytest.mark.anyio("asyncio")
async def test_index_rule_service_uses_file_source(tmp_path: Path):
    payload = {"rules": [{"name": "file_rule", "pattern": "bar"}]}
    rule_file = tmp_path / "index_rules.json"
    rule_file.write_text(json.dumps(payload))

    class DummyConfig:
        INDEX_RULE_SOURCE = "file"
        INDEX_RULES_PATH = str(rule_file)
        INDEX_RULE_TABLE = "index_rules"
        DB_USER = "user"
        DB_PASS = ""
        DB_HOST = "localhost"
        DB_PORT = 5432
        DB_NAME = "erex"

    service = IndexRuleService(config=DummyConfig)
    rules = await service.list_rules()

    assert [rule.name for rule in rules] == ["file_rule"]


def test_database_store_validates_table_name():
    with pytest.raises(ValueError):
        DatabaseIndexRuleStore(dsn="postgresql://user@localhost/db", table_name="invalid-name")
