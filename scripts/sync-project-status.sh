#!/usr/bin/env bash

set -euo pipefail

content_url="${1:?Usage: sync-project-status.sh CONTENT_URL STATUS}"
status_name="${2:?Usage: sync-project-status.sh CONTENT_URL STATUS}"

if [[ -z "${GH_TOKEN:-}" || -z "${PROJECT_NUMBER:-}" || -z "${PROJECT_OWNER:-}" ]]; then
  printf 'Project sync skipped: PROJECT_TOKEN, PROJECT_NUMBER or PROJECT_OWNER is not configured.\n'
  exit 0
fi

for tool in gh jq; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Required tool is missing: %s\n' "$tool" >&2
    exit 1
  fi
done

project_id="$(
  gh project view "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --format json \
    | jq -r '.id'
)"
fields_json="$(
  gh project field-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" \
    --limit 100 --format json
)"
status_field_id="$(
  jq -r '.fields[] | select(.name == "Status") | .id' <<< "$fields_json" \
    | sed -n '1p'
)"
status_option_id="$(
  jq -r --arg status "$status_name" \
    '.fields[] | select(.name == "Status") | .options[] | select((.name | ascii_downcase) == ($status | ascii_downcase)) | .id' \
    <<< "$fields_json" | sed -n '1p'
)"

if [[ -z "$project_id" || -z "$status_field_id" || -z "$status_option_id" ]]; then
  printf 'Unable to resolve Project, Status field, or status option: %s\n' "$status_name" >&2
  exit 1
fi

items_json="$(
  gh project item-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" \
    --limit 1000 --format json
)"
item_id="$(
  jq -r --arg url "$content_url" \
    '.items[] | select(.content.url == $url) | .id' <<< "$items_json" \
    | sed -n '1p'
)"
if [[ -z "$item_id" ]]; then
  item_id="$(
    gh project item-add "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" \
      --url "$content_url" --format json | jq -r '.id'
  )"
fi

gh project item-edit \
  --id "$item_id" \
  --project-id "$project_id" \
  --field-id "$status_field_id" \
  --single-select-option-id "$status_option_id" \
  >/dev/null

printf 'Project status updated: %s -> %s\n' "$content_url" "$status_name"
