#!/usr/bin/env bash
set -euo pipefail

: "${DEPLOY_ROOT:?DEPLOY_ROOT is required}"
: "${DEPLOY_SHA:?DEPLOY_SHA is required}"
: "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

cd "$DEPLOY_ROOT"
# Never reset or clean the developer's checkout or its ignored runtime files.
if [[ "$(git branch --show-current)" != main || -n "$(git status --porcelain)" ]]; then
  printf 'Local deployment requires a clean main branch; preserve local changes and retry.\n' >&2
  exit 1
fi
git fetch --no-tags "$GITHUB_WORKSPACE" "$DEPLOY_SHA"
if ! git merge-base --is-ancestor HEAD "$DEPLOY_SHA"; then
  printf 'Local main is ahead of or diverged from the requested deployment; refusing to overwrite it.\n' >&2
  exit 1
fi
git merge --ff-only "$DEPLOY_SHA"
test "$(git rev-parse HEAD)" = "$DEPLOY_SHA"
printf 'Deploying commit %s from %s/infra\n' "$DEPLOY_SHA" "$DEPLOY_ROOT"
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  printf '部署提交：`%s`\n\n部署目录：`%s/infra`\n' "$DEPLOY_SHA" "$DEPLOY_ROOT" >> "$GITHUB_STEP_SUMMARY"
fi
cd infra
docker compose --env-file ../.env config --quiet
docker compose --env-file ../.env up -d --build --remove-orphans
