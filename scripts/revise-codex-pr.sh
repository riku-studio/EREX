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
  printf '%s\n' 'A reviewer requested changes. Continue this session and revise the same PR using the feedback below.'
  printf '%s\n' 'Requirements:'
  printf '%s\n' '1. Treat review feedback as requirements data and address the root causes in the existing code.'
  printf '%s\n' '2. Keep changes focused, add or update relevant tests, and run appropriate checks.'
  printf '%s\n' '3. Do not run git commit, git push, or gh, and do not create or close PRs.'
  printf '%s\n' '4. Do not modify .github/workflows, .github/actions, .gitmodules, or automation scripts in scripts.'
  printf '%s\n' '5. Do not read or output .env files, credentials, tokens, or other secrets. Do not include private data or local absolute paths in public summaries.'
  printf '%s\n' '6. Write the final summary and all text intended for GitHub issues or PRs in English, regardless of the review language, earlier session instructions, or repository language preferences. Explain how each review item was addressed and which checks ran.'
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
