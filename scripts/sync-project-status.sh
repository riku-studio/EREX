#!/usr/bin/env bash

set -euo pipefail

content_url="${1:?Usage: sync-project-status.sh CONTENT_URL STATUS}"
status_name="${2:?Usage: sync-project-status.sh CONTENT_URL STATUS}"

report_failure() {
  printf '::warning::Project sync failed. Check the API error above, PROJECT_TOKEN access, and Status options.\n' >&2
  if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    printf '\nProject sync failed. Implementation success does not mean that the board was updated. Check the sync step for the API error.\n' >> "$GITHUB_STEP_SUMMARY"
  fi
}
trap report_failure ERR

if [[ -z "${GH_TOKEN:-}" || -z "${PROJECT_NUMBER:-}" || -z "${PROJECT_OWNER:-}" ]]; then
  printf '::warning::Project sync skipped: PROJECT_TOKEN, PROJECT_NUMBER or PROJECT_OWNER is not configured.\n'
  exit 0
fi

for tool in gh jq; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Required tool is missing: %s\n' "$tool" >&2
    exit 1
  fi
done

if [[ ! "$PROJECT_NUMBER" =~ ^[1-9][0-9]*$ ]]; then
  printf 'PROJECT_NUMBER must be a positive integer.\n' >&2
  report_failure
  exit 1
fi

# Avoid gh project's owner autodetection, which can hide authentication errors.
owner_type="$(gh api "users/$PROJECT_OWNER" --jq .type)"
case "$owner_type" in
  Organization) owner_field=organization ;;
  User) owner_field=user ;;
  *) printf 'Unsupported Project owner type.\n' >&2; report_failure; exit 1 ;;
esac

query='query($owner: String!, $number: Int!, $after: String) {
  OWNER_FIELD(login: $owner) {
    projectV2(number: $number) {
      id
      fields(first: 100, after: $after) {
        nodes {
          ... on ProjectV2SingleSelectField { id name options { id name } }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}'
query="${query/OWNER_FIELD/$owner_field}"
cursor=""
fields_json='{"fields":[]}'
while :; do
  cursor_args=()
  if [[ -n "$cursor" ]]; then
    cursor_args=(-f "after=$cursor")
  fi
  page="$(gh api graphql -f query="$query" -f owner="$PROJECT_OWNER" \
    -F number="$PROJECT_NUMBER" "${cursor_args[@]}")"
  project="$(jq -ce --arg owner "$owner_field" '.data[$owner].projectV2 // error("Project is not accessible; check the number and token permissions")' <<< "$page")"
  project_id="$(jq -er '.id' <<< "$project")"
  fields_json="$(jq -cn --argjson old "$fields_json" --argjson page "$project" '{fields: ($old.fields + $page.fields.nodes)}')"
  if [[ "$(jq -r '.fields.pageInfo.hasNextPage' <<< "$project")" != true ]]; then
    break
  fi
  cursor="$(jq -er '.fields.pageInfo.endCursor' <<< "$project")"
done
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
  report_failure
  exit 1
fi

content_id="$(gh api graphql -f query='query($url: URI!) {
  resource(url: $url) {
    ... on Issue { id }
    ... on PullRequest { id }
  }
}' -f url="$content_url" --jq '.data.resource.id')"
[[ -n "$content_id" && "$content_id" != null ]]

# Adding existing content returns the existing item, without an item-list limit.
item_id="$(gh api graphql -f query='mutation($project: ID!, $content: ID!) {
  addProjectV2ItemById(input: {projectId: $project, contentId: $content}) {
    item { id }
  }
}' -f project="$project_id" -f content="$content_id" --jq '.data.addProjectV2ItemById.item.id')"
[[ -n "$item_id" && "$item_id" != null ]]

gh api graphql -f query='mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $project, itemId: $item, fieldId: $field,
    value: {singleSelectOptionId: $option}
  }) { projectV2Item { id } }
}' -f project="$project_id" -f item="$item_id" -f field="$status_field_id" \
  -f option="$status_option_id" >/dev/null

printf 'Project status updated: %s -> %s\n' "$content_url" "$status_name"
