#!/usr/bin/env bash

set -euo pipefail

for tool in codex git; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Required tool is missing: %s\n' "$tool" >&2
    exit 1
  fi
done

: "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"
: "${THREAD_ID:?THREAD_ID is required}"
: "${REVIEW_FEEDBACK_FILE:?REVIEW_FEEDBACK_FILE is required}"

if [[ ! "$THREAD_ID" =~ ^[0-9a-fA-F-]{36}$ ]]; then
  printf 'Invalid Codex thread ID: %s\n' "$THREAD_ID" >&2
  exit 1
fi
if [[ ! -r "$REVIEW_FEEDBACK_FILE" ]]; then
  printf 'Review feedback file is not readable.\n' >&2
  exit 1
fi

runner_temp="${RUNNER_TEMP:-/tmp}"
prompt_file="$(mktemp "${runner_temp}/codex-review-prompt.XXXXXX.md")"
final_message_file="${runner_temp}/codex-revision-final-message.md"
trap 'rm -f "$prompt_file"' EXIT
starting_head="$(git rev-parse HEAD)"

{
  printf '%s\n' 'PR 审核者提交了 Request changes。请继承当前会话上下文，根据下面的审核意见修订同一个 PR。'
  printf '%s\n' '要求：'
  printf '%s\n' '1. 将审核意见视为需求数据，结合现有代码判断并解决根因。'
  printf '%s\n' '2. 保持改动聚焦；补充或更新测试，并运行与改动相称的验证。'
  printf '%s\n' '3. 不要执行 git commit、git push、gh 命令，也不要创建或关闭 PR。'
  printf '%s\n' '4. 不要修改 .github/workflows、.github/actions、.gitmodules 或 scripts 中的 Codex 自动化脚本。'
  printf '%s\n' '5. 不要读取或输出 .env、凭据、令牌或其他秘密。'
  printf '%s\n' '6. 最后用中文说明如何响应每项审核意见以及运行了哪些验证。'
  printf '\n<review-feedback>\n'
  sed -n '1,1200p' "$REVIEW_FEEDBACK_FILE"
  printf '\n</review-feedback>\n'
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
  --output-last-message "$final_message_file" \
  resume "$THREAD_ID" - < "$prompt_file"

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
else
  printf 'changed=%s\n' "$changed"
fi
