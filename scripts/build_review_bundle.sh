#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

OUT_FILE="${1:-UNCLE_BOB_REVIEW_BUNDLE.md}"

ORDERED_TMP="$(mktemp)"
TRACKED_TMP="$(mktemp)"
DEDUP_TMP="$(mktemp)"
EXISTING_TMP="$(mktemp)"
trap 'rm -f "$ORDERED_TMP" "$TRACKED_TMP" "$DEDUP_TMP" "$EXISTING_TMP"' EXIT

git ls-files > "$TRACKED_TMP"

add_match() {
  local pattern="$1"
  git ls-files "$pattern" 2>/dev/null || true
}

{
  printf '%s\n' \
    "README.md" \
    "CHANGELOG.md" \
    "CONTRIBUTING.md" \
    "LICENSE" \
    "pyproject.toml" \
    "poetry.lock" \
    "Dockerfile" \
    "docker-compose.yml"
  add_match ".github/workflows/*.yml"
  add_match "docs/*.md"
  add_match "sprints/*.md"
  add_match "scripts/*.sh"
  add_match "scripts/sql/*.sql"
  add_match "src/**/*.py"
  add_match "tests/**/*.py"
  add_match "tests/**/*.html"
} >> "$ORDERED_TMP"

grep -Fxv -f "$ORDERED_TMP" "$TRACKED_TMP" | sort >> "$ORDERED_TMP"
awk 'NF && !seen[$0]++' "$ORDERED_TMP" > "$DEDUP_TMP"

while IFS= read -r file; do
  [[ -f "$file" ]] && echo "$file"
done < "$DEDUP_TMP" > "$EXISTING_TMP"

lang_for_file() {
  case "$1" in
    *.py) echo "python" ;;
    *.md) echo "markdown" ;;
    *.toml) echo "toml" ;;
    *.yml|*.yaml) echo "yaml" ;;
    *.sh) echo "bash" ;;
    *.sql) echo "sql" ;;
    *.html) echo "html" ;;
    *.lock) echo "text" ;;
    Dockerfile) echo "dockerfile" ;;
    *) echo "text" ;;
  esac
}

{
  echo "# GarysGuide-Scraper: Complete Review Bundle"
  echo
  echo "- Repository: $(basename "$REPO_ROOT")"
  echo "- Branch: $(git rev-parse --abbrev-ref HEAD)"
  echo "- Commit: $(git rev-parse --short HEAD)"
  echo "- Generated (UTC): $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "- Source scope: all tracked repository files"
  echo
  echo "## Table of Contents"

  i=1
  while IFS= read -r file; do
    printf '%d. %s\n' "$i" "$file"
    i=$((i + 1))
  done < "$EXISTING_TMP"

  while IFS= read -r file; do
    lang="$(lang_for_file "$file")"
    echo
    echo "---"
    echo
    echo "## FILE: $file"
    echo
    printf '```%s\n' "$lang"
    cat "$file"
    echo
    echo '```'
  done < "$EXISTING_TMP"
} > "$OUT_FILE"

echo "Wrote review bundle: $OUT_FILE"