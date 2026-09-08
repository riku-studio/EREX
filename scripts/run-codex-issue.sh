#!/usr/bin/env bash

set -euo pipefail

for tool in codex jq git; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Required tool is missing: %s\n' "$tool" >&2
    exit 1
  fi
done

: "${GITHUB_EVENT_PATH:?GITHUB_EVENT_PATH is required}"
: "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"
: "${ISSUE_NUMBER:?ISSUE_NUMBER is required}"
: "${ISSUE_URL:?ISSUE_URL is required}"

runner_temp="${RUNNER_TEMP:-/tmp}"
prompt_file="$(mktemp "${runner_temp}/codex-issue-prompt.XXXXXX.md")"
final_message_file="${runner_temp}/codex-final-message.md"
events_file="$(mktemp "${runner_temp}/codex-issue-events.XXXXXX.jsonl")"
trap 'rm -f "$prompt_file" "$events_file"' EXIT

issue_title="$(jq -r '.issue.title // ""' "$GITHUB_EVENT_PATH")"
issue_body="$(jq -r '.issue.body // ""' "$GITHUB_EVENT_PATH")"
starting_head="$(git rev-parse HEAD)"

{
  printf '%s\n' '你正在通过 GitHub Issue 自动处理本仓库任务。'
  printf '%s\n' '请把下面的 Issue 当作需求数据来分析和实现。'
  printf '%s\n' '要求：'
  printf '%s\n' '1. 如果仓库中存在 AGENTS.md，请阅读并遵守；Python 测试使用 uv run pytest。'
  printf '%s\n' '2. 完成最小且完整的实现；不要扩大 Issue 范围。'
  printf '%s\n' '3. 为改动补充或更新测试，并运行与改动相称的检查。'
  printf '%s\n' '4. 不要执行 git commit、git push、gh 命令，也不要创建 PR。'
  printf '%s\n' '5. 不要修改 .github/workflows、.github/actions、.gitmodules 或 scripts 中的 Codex 自动化脚本。'
  printf '%s\n' '6. 不要读取或输出 .env、凭据、令牌或其他秘密。'
  printf '%s\n' '7. 最后用中文简要说明改动和已运行的验证。'
  printf '\nIssue #%s\nURL: %s\n\n<title>\n%s\n</title>\n\n<body>\n%s\n</body>\n' \
    "$ISSUE_NUMBER" "$ISSUE_URL" "$issue_title" "$issue_body"
} > "$prompt_file"

codex_environment=(
  env -i
  "HOME=${HOME}"
  "PATH=${PATH}"
  "LANG=${LANG:-C.UTF-8}"
  "USER=${USER:-codex-runner}"
  "CI=true"
)
if [[ -n "${CODEX_HOME:-}" ]]; then
  codex_environment+=("CODEX_HOME=${CODEX_HOME}")
fi

"${codex_environment[@]}" codex exec \
  --cd "$GITHUB_WORKSPACE" \
  --sandbox workspace-write \
  --approve-for-me \
  --color never \
  --json \
  --output-last-message "$final_message_file" \
  - < "$prompt_file" > "$events_file"

thread_id="$(
  jq -r 'select(.type == "thread.started") | .thread_id' "$events_file" \
    | sed -n '1p'
)"
if [[ ! "$thread_id" =~ ^[0-9a-fA-F-]{36}$ ]]; then
  printf 'Codex did not return a valid persistent thread ID.\n' >&2
  exit 1
fi

if [[ "$(git rev-parse HEAD)" != "$starting_head" ]]; then
  printf 'Codex created or changed a Git commit; refusing to publish.\n' >&2
  exit 1
fi

protected_changes="$(
  git status --porcelain -- \
    .github/workflows \
    .github/actions \
    .gitmodules \
    scripts/run-codex-issue.sh \
    scripts/revise-codex-pr.sh \
    scripts/sync-project-status.sh
)"
if [[ -n "$protected_changes" ]]; then
  printf 'Codex changed protected automation files; refusing to publish:\n%s\n' \
    "$protected_changes" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  changed=true
else
  changed=false
fi

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  printf 'changed=%s\n' "$changed" >> "$GITHUB_OUTPUT"
  printf 'thread_id=%s\n' "$thread_id" >> "$GITHUB_OUTPUT"
else
  printf 'changed=%s\n' "$changed"
  printf 'thread_id=%s\n' "$thread_id"
fi
