"""Exercise deployment checkout safety without touching Docker or GitHub."""
import os
from pathlib import Path
import subprocess

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "deploy-local.sh"


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def deployment(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init", "-b", "main")
    git(source, "config", "user.name", "Test")
    git(source, "config", "user.email", "test@example.invalid")
    (source / "infra").mkdir()
    (source / "infra" / "docker-compose.yml").write_text("services: {}\n")
    (source / ".gitignore").write_text(".env\ndata/\n")
    git(source, "add", ".")
    git(source, "commit", "-m", "initial")
    local = tmp_path / "local"
    git(source, "clone", str(source), str(local))
    (local / ".env").write_text("LOCAL_ONLY=yes\n")
    (local / "data").mkdir()
    (local / "data" / "keep").write_text("keep")
    (source / "version").write_text("new")
    git(source, "add", ".")
    git(source, "commit", "-m", "next")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text('#!/bin/sh\nprintf "%s|%s\\n" "$PWD" "$*" >> "$DOCKER_CALLS"\n')
    docker.chmod(0o755)
    env = dict(os.environ, DEPLOY_ROOT=str(local), GITHUB_WORKSPACE=str(source),
               DEPLOY_SHA=git(source, "rev-parse", "HEAD"),
               PATH=f"{bin_dir}:{os.environ['PATH']}", DOCKER_CALLS=str(tmp_path / "calls"))
    env.pop("GITHUB_STEP_SUMMARY", None)
    return source, local, env


def test_fast_forward_preserves_local_data_and_uses_infra(deployment):
    _, local, env = deployment
    subprocess.run(["bash", str(SCRIPT)], env=env, check=True, capture_output=True)
    assert git(local, "rev-parse", "HEAD") == env["DEPLOY_SHA"]
    assert (local / ".env").read_text() == "LOCAL_ONLY=yes\n"
    assert (local / "data" / "keep").read_text() == "keep"
    assert Path(env["DOCKER_CALLS"]).read_text().splitlines() == [
        f"{local}/infra|compose --env-file ../.env config --quiet",
        f"{local}/infra|compose --env-file ../.env up -d --build --remove-orphans",
    ]


@pytest.mark.parametrize("state", ["dirty", "ahead", "branch"])
def test_unsafe_checkout_never_runs_docker(deployment, state):
    source, local, env = deployment
    if state == "dirty":
        (local / "uncommitted").write_text("preserve")
    elif state == "ahead":
        env["DEPLOY_SHA"] = git(source, "rev-parse", "HEAD~1")
        git(local, "pull", "--ff-only", str(source), "main")
    else:
        git(local, "switch", "-c", "work")
    before = git(local, "rev-parse", "HEAD")
    result = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True)
    assert result.returncode != 0
    assert git(local, "rev-parse", "HEAD") == before
    assert not Path(env["DOCKER_CALLS"]).exists()
