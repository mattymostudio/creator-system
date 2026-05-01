#!/usr/bin/env bash
# check-release.sh — verify the Creator System kit is safe to ship publicly.
#
# Three checks:
#   1. Semantic block list — grep for private terms from your block list
#   2. Empty-folders check — source/canon/project/output folders must contain zero files
#   3. Wikilink resolution — flag [[links]] that point to non-existent files
#
# Only scans files that actually ship. Private meta-files are excluded (see PRIVATE_PATHS).
#
# Exit 0 = clean. Exit 1 = leaks / blockers found.
# Warnings (like unresolved wikilinks) do not fail — they're printed for review.

set -uo pipefail

KIT_DIR="${KIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
VAULT_DIR="$KIT_DIR/vault"
SELF="$(basename "${BASH_SOURCE[0]}")"

FAIL=0

echo "==> Kit:   $KIT_DIR"
echo "==> Vault: $VAULT_DIR"
echo

# -----------------------------------------------------------------------------
# Private files NOT scanned (internal tracking, not part of the release)
# -----------------------------------------------------------------------------
PRIVATE_GREP_EXCLUDES=(
  --exclude="RECIPIENTS.md"
  --exclude="email-to-*.md"
  --exclude="RELEASE_NOTES*.md"
  --exclude="GITHUB_DEPLOYMENT_PLAN.md"
  --exclude="ONBOARDING_REDESIGN.md"
  --exclude="COHORT_*_HANDOUT.md"
  --exclude="RECAP.md"
  --exclude="$SELF"
  --exclude-dir="scripts"
  --exclude-dir=".git"
  --exclude-dir="_archive"
  --exclude-dir="site"
  --exclude-dir="cohort-bonus"
  --exclude-dir="_repo_staging"
  --exclude-dir="_build_release"
)

# -----------------------------------------------------------------------------
# 1. Semantic block list
# -----------------------------------------------------------------------------
# The block-list patterns live OUTSIDE this script, because a committed block
# list is itself a map of exactly what you don't want public:
#
#   scripts/blocklist.local.txt   — YOUR real terms (gitignored, never ships)
#   scripts/blocklist.example.txt — documented placeholder format (ships)
#
# Each line: ERE_PATTERN|Category   (# comments and blank lines ignored).
# A few generic built-in patterns below apply to every kit regardless.

PATTERNS=(
  # Generic built-ins — real-looking personal emails and home paths
  "[A-Za-z0-9._%+-]+@(gmail|googlemail|yahoo|hotmail|outlook|icloud|proton|protonmail|aol)\\.com|Real personal email (use *.example)"
  "/Users/[A-Za-z0-9._-]+|Absolute home path"
)

BLOCKLIST_FILE="${BLOCKLIST_FILE:-$KIT_DIR/scripts/blocklist.local.txt}"
if [ ! -f "$BLOCKLIST_FILE" ]; then
  BLOCKLIST_FILE="$KIT_DIR/scripts/blocklist.example.txt"
  echo "  ⚠️  No scripts/blocklist.local.txt found — running with generic"
  echo "     built-ins and example patterns only. Copy blocklist.example.txt"
  echo "     to blocklist.local.txt and add your own terms."
fi
if [ -f "$BLOCKLIST_FILE" ]; then
  while IFS= read -r line; do
    case "$line" in ''|\#*) continue ;; esac
    PATTERNS+=("$line")
  done < "$BLOCKLIST_FILE"
fi

echo "==> [1/3] Semantic block list"
SEMANTIC_FAIL=0
for entry in "${PATTERNS[@]}"; do
  pattern="${entry%%|*}"
  category="${entry##*|}"
  hits=$(grep -rInE \
    --include="*.md" --include="*.txt" --include="*.sh" --include="*.py" \
    --include="*.yml" --include="*.yaml" --include="*.json" \
    "${PRIVATE_GREP_EXCLUDES[@]}" \
    "$pattern" "$KIT_DIR" 2>/dev/null || true)
  if [ -n "$hits" ]; then
    echo "  ❌ [$category] pattern: $pattern"
    echo "$hits" | sed 's|^|     |'
    SEMANTIC_FAIL=1
  fi
done

# Bare "Matty Mo" is personal; "Matty Mo Studio" is the allowed brand.
bare_matty=$(grep -rInE \
  --include="*.md" \
  "${PRIVATE_GREP_EXCLUDES[@]}" \
  "Matty Mo\\b" "$KIT_DIR" 2>/dev/null \
  | grep -v "Matty Mo Studio" || true)
if [ -n "$bare_matty" ]; then
  echo "  ❌ [Personal identity] bare 'Matty Mo' found — use 'Matty Mo Studio' or remove."
  echo "$bare_matty" | sed 's|^|     |'
  SEMANTIC_FAIL=1
fi

if [ "$SEMANTIC_FAIL" -eq 0 ]; then
  echo "  ✅ No semantic leaks."
fi
[ "$SEMANTIC_FAIL" -eq 1 ] && FAIL=1

# -----------------------------------------------------------------------------
# 2. Empty-folders check
# -----------------------------------------------------------------------------
echo
echo "==> [2/3] Content folders are empty"

EMPTY_DIRS=(
  "vault/02_SOURCES"
  "vault/03_SOURCE_NOTES"
  "vault/04_CANON"
  "vault/05_PROJECTS"
  "vault/06_OUTPUTS"
  "vault/_attachments"
)

EMPTY_FAIL=0
for d in "${EMPTY_DIRS[@]}"; do
  full="$KIT_DIR/$d"
  if [ ! -d "$full" ]; then
    echo "  ⚠️  $d does not exist (skipping)"
    continue
  fi
  count=$(find "$full" -type f ! -name ".DS_Store" ! -name ".gitkeep" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$count" -ne 0 ]; then
    echo "  ❌ $d contains $count files (must be empty):"
    find "$full" -type f ! -name ".DS_Store" ! -name ".gitkeep" | sed 's|^|     |'
    EMPTY_FAIL=1
  fi
done

if [ "$EMPTY_FAIL" -eq 0 ]; then
  echo "  ✅ All content folders empty."
fi
[ "$EMPTY_FAIL" -eq 1 ] && FAIL=1

# -----------------------------------------------------------------------------
# 3. Wikilink resolution (warn-only, catches leaked people/pages)
# -----------------------------------------------------------------------------
echo
echo "==> [3/3] Wikilink resolution"

# Known template placeholders — intentional dangling links that don't need to resolve.
ALLOWED_DANGLING=(
  "Your Name"
  "Project - Name"
  "Company Name"
  "Person Name"
  "Decision - Topic"
  "Output - Memo - Subject"
  "Idea Template"
  "Note - Example"
  "Source - Example"
  "idea"
)

is_allowed_dangling() {
  local link="$1"
  for allowed in "${ALLOWED_DANGLING[@]}"; do
    [ "$link" = "$allowed" ] && return 0
  done
  return 1
}

# Collect all unique wikilink targets (strip aliases after |).
# Use a temp file to avoid bash-3.2 mapfile.
LINKS_TMP=$(mktemp)
grep -rhoE '\[\[[^]]+\]\]' "$VAULT_DIR" --include="*.md" 2>/dev/null \
  | sed -E 's/^\[\[//; s/\]\]$//; s/\|.*$//' \
  | sort -u > "$LINKS_TMP" || true

unresolved_count=0
unresolved_tmp=$(mktemp)

while IFS= read -r link; do
  [ -z "$link" ] && continue
  if is_allowed_dangling "$link"; then
    continue
  fi
  # Path-style links like [[10_META/AGENTS.md]] resolve by exact path.
  if [[ "$link" == */* ]]; then
    # Strip .md if present, try both with and without extension.
    path_no_ext="${link%.md}"
    if [ -f "$VAULT_DIR/${path_no_ext}.md" ] || [ -f "$VAULT_DIR/$link" ]; then
      continue
    fi
    echo "     - [[$link]]" >> "$unresolved_tmp"
    unresolved_count=$((unresolved_count + 1))
    continue
  fi
  # Bare links resolve by filename anywhere in the vault.
  if ! find "$VAULT_DIR" -type f -name "${link}.md" 2>/dev/null | grep -q .; then
    echo "     - [[$link]]" >> "$unresolved_tmp"
    unresolved_count=$((unresolved_count + 1))
  fi
done < "$LINKS_TMP"

if [ "$unresolved_count" -gt 0 ]; then
  echo "  ⚠️  $unresolved_count wikilink(s) with no matching file — review for leaked names or broken templates:"
  cat "$unresolved_tmp"
else
  echo "  ✅ All wikilinks resolve (or are known template placeholders)."
fi

rm -f "$LINKS_TMP" "$unresolved_tmp"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo
if [ "$FAIL" -eq 0 ]; then
  echo "✅ Kit passed release checks."
  exit 0
else
  echo "❌ Kit has blockers. Fix before shipping."
  exit 1
fi
