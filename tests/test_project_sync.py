"""Verify Project API sequencing and failures without external writes."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/sync-project-status.sh"


@pytest.fixture
def run_sync(tmp_path):
    fake = tmp_path / "gh"
    fake.write_text(f"#!{sys.executable}\n" + '''
import json, os, pathlib, sys
log = pathlib.Path(os.environ["CALLS"])
calls = json.loads(log.read_text()) if log.exists() else []
calls.append(sys.argv[1:])
log.write_text(json.dumps(calls))
reply = json.loads(os.environ["REPLIES"])[len(calls) - 1]
print(reply.get("out", ""))
if reply.get("error"):
    print(reply["error"], file=sys.stderr)
sys.exit(reply.get("code", 0))
''')
    fake.chmod(0o755)

    def run(replies, **overrides):
        env = dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}",
                   GH_TOKEN="test-only-placeholder", PROJECT_NUMBER="4",
                   PROJECT_OWNER="riku-studio", CALLS=str(tmp_path / "calls"),
                   REPLIES=json.dumps(replies), GITHUB_STEP_SUMMARY=str(tmp_path / "summary"))
        env.update(overrides)
        result = subprocess.run(["bash", str(SCRIPT),
                                 "https://github.com/riku-studio/EREX/issues/1", "In review"],
                                env=env, text=True, capture_output=True)
        log = tmp_path / "calls"
        calls = json.loads(log.read_text()) if log.exists() else []
        return result, calls, tmp_path / "summary"
    return run


def page(owner="organization", options=True, more=False):
    fields = [{"id": "F", "name": "Status", "options": [
        {"id": "O", "name": "In review"}]}] if options else []
    return {"out": json.dumps({"data": {owner: {"projectV2": {
        "id": "P", "fields": {"nodes": fields, "pageInfo": {
            "hasNextPage": more, "endCursor": "cursor" if more else None}}}}}})}


@pytest.mark.parametrize("owner_type,owner_field", [("Organization", "organization"), ("User", "user")])
def test_syncs_status_with_explicit_owner(run_sync, owner_type, owner_field):
    result, calls, _ = run_sync([{"out": owner_type}, page(owner_field),
                                {"out": "I"}, {"out": "ITEM"}, {}])
    assert result.returncode == 0, result.stderr
    assert f"{owner_field}(login:" in " ".join(calls[1])
    assert "field=F" in calls[-1] and "option=O" in calls[-1]
    assert "Project status updated" in result.stdout


def test_paginates_fields_before_mutations(run_sync):
    result, calls, _ = run_sync([{"out": "Organization"}, page(options=False, more=True),
                                page(), {"out": "I"}, {"out": "ITEM"}, {}])
    assert result.returncode == 0, result.stderr
    assert "after=cursor" in calls[2]


@pytest.mark.parametrize("failure", ["HTTP 401: Bad credentials", "GraphQL: Resource not accessible by personal access token"])
def test_preserves_auth_errors_and_stops(run_sync, failure):
    result, calls, summary = run_sync([{"out": "Organization"}, {"error": failure, "code": 1}])
    assert result.returncode != 0
    assert failure in result.stderr
    assert len(calls) == 2
    assert "Project sync failed" in summary.read_text()
    assert "test-only-placeholder" not in result.stdout + result.stderr


def test_missing_status_does_not_add_item(run_sync):
    result, calls, _ = run_sync([{"out": "Organization"}, page(options=False)])
    assert result.returncode != 0
    assert len(calls) == 2


def test_missing_configuration_warns_without_api_calls(run_sync):
    result, calls, _ = run_sync([], GH_TOKEN="")
    assert result.returncode == 0
    assert "::warning::Project sync skipped" in result.stdout
    assert not calls
