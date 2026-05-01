#!/usr/bin/env bash
# prepare-repo.sh — stage a clean copy of what would be pushed to GitHub,
# then audit it before you push.
#
# Use this as the safety check before any `git push` to a public repo.
# It builds an explicit staging directory containing ONLY public-shippable
# content (anything matching .gitignore is excluded) and runs three audits:
#
#   1. Lists every file that would ship (manifest.txt)
#   2. Greps for any private names / paths / blocked terms
#   3. Runs scripts/check-release.sh against the staged copy
#
# Usage:
#   ./scripts/prepare-repo.sh                    # stages to ./_repo_staging
#   ./scripts/prepare-repo.sh /tmp/my-staging    # custom staging path
#
# After running, manually inspect the staging dir before committing/pushing.

set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGING="${1:-$KIT_DIR/_repo_staging}"

echo "==> Repo staging tool"
echo "    Source:  $KIT_DIR"
echo "    Staging: $STAGING"
echo

# 1. Clean target
rm -rf "$STAGING"
mkdir -p "$STAGING"

# 2. Copy with rsync, respecting .gitignore at every level (nested gitignores honored)
echo "==> Copying public-shippable content (respecting .gitignore at every level)"
cd "$KIT_DIR"
rsync -a \
  --filter=':- .gitignore' \
  --exclude='.git' \
  --exclude='.DS_Store' \
  --exclude='_repo_staging' \
  --exclude='_build_release' \
  --exclude='artifacts' \
  ./ "$STAGING/"
echo

# 3. Generate manifest
echo "==> Generating manifest"
cd "$STAGING"
find . -type f -not -path './.*' | sort > manifest.txt
file_count=$(wc -l < manifest.txt | tr -d ' ')
echo "    $file_count files staged"
echo "    Manifest: $STAGING/manifest.txt"
echo

# 4. Audit: top-level listing
echo "==> Top-level contents"
ls -la | grep -v '^total' | awk '{print "    " $NF}' | grep -v '^\s*\.$\|^\s*\.\.$\|^\s*manifest.txt$' | head -30
echo

# 5. Audit: search for blocked terms / private hints
echo "==> Audit: searching for private terms in staged content"
HITS=0

# Terms that should never appear in shipping content. Private terms load
# from scripts/blocklist.local.txt (gitignored — see blocklist.example.txt);
# only generic internal-filename patterns are hardcoded here.
PATTERNS=(
  '/Users/[A-Za-z0-9._-]+'
  'RECIPIENTS\.md' 'email-to-' 'COHORT_._HANDOUT'
  'GITHUB_DEPLOYMENT_PLAN' 'ONBOARDING_REDESIGN' 'cohort-bonus/'
)
BLOCKLIST_FILE="${BLOCKLIST_FILE:-$KIT_DIR/scripts/blocklist.local.txt}"
if [ -f "$BLOCKLIST_FILE" ]; then
  while IFS= read -r line; do
    case "$line" in ''|\#*) continue ;; esac
    PATTERNS+=("${line%%|*}")
  done < "$BLOCKLIST_FILE"
else
  echo "    ⚠️  No scripts/blocklist.local.txt — private-term audit is generic only"
fi

for pat in "${PATTERNS[@]}"; do
  # Exclude the scripts/ dir from this audit — those scripts contain
  # the enforcement patterns by design (they ARE the rule).
  found=$(grep -rIlE "$pat" \
            --include='*.md' --include='*.py' --include='*.json' --include='*.yml' --include='*.yaml' \
            --exclude-dir='scripts' \
            . 2>/dev/null | grep -v manifest.txt || true)
  if [ -n "$found" ]; then
    echo "    ❌ Pattern '$pat' found in:"
    echo "$found" | sed 's/^/         /'
    HITS=$((HITS + 1))
  fi
done

if [ "$HITS" -eq 0 ]; then
  echo "    ✅ No blocked terms found in any staged file"
fi
echo

# 6. Audit: confirm private files NOT staged
echo "==> Confirming private files are NOT staged"
PRIVATE_FILES=(
  'RECIPIENTS.md' 'COHORT_1_HANDOUT.md' 'COHORT_1_HANDOUT.pdf'
  'GITHUB_DEPLOYMENT_PLAN.md' 'ONBOARDING_REDESIGN.md'
  'scripts/blocklist.local.txt'
)
LEAKS=0
for f in "${PRIVATE_FILES[@]}"; do
  if [ -e "$STAGING/$f" ]; then
    echo "    ❌ LEAK: $f exists in staging"
    LEAKS=$((LEAKS + 1))
  fi
done
for f in "$STAGING"/email-to-*.md; do
  if [ -e "$f" ]; then
    echo "    ❌ LEAK: $(basename "$f") exists in staging"
    LEAKS=$((LEAKS + 1))
  fi
done
for d in cohort-bonus _archive _build _build_tools site; do
  if [ -d "$STAGING/$d" ]; then
    echo "    ❌ LEAK: $d/ directory exists in staging"
    LEAKS=$((LEAKS + 1))
  fi
done
zip_count=$(find "$STAGING" -name '*.zip' 2>/dev/null | wc -l | tr -d ' ')
if [ "$zip_count" -gt 0 ]; then
  echo "    ❌ LEAK: $zip_count zip files in staging"
  find "$STAGING" -name '*.zip' | sed 's/^/         /'
  LEAKS=$((LEAKS + 1))
fi
if [ "$LEAKS" -eq 0 ]; then
  echo "    ✅ No private files / dirs leaked into staging"
fi
echo

# 7. Run check-release.sh against the staging dir
echo "==> Running check-release.sh against staged content"
if [ -f "$STAGING/scripts/check-release.sh" ]; then
  KIT_DIR="$STAGING" bash "$STAGING/scripts/check-release.sh" 2>&1 | grep -E "(✅|❌|==>)" | sed 's/^/    /'
else
  echo "    ⚠️  check-release.sh not found in staging — skipping"
fi
echo

# 8. Final summary
echo "==> Summary"
echo "    Staged:        $file_count files at $STAGING"
echo "    Pattern hits:  $HITS"
echo "    Private leaks: $LEAKS"
echo
if [ "$HITS" -eq 0 ] && [ "$LEAKS" -eq 0 ]; then
  echo "✅ Staging looks clean. Inspect manually:"
  echo "    open $STAGING"
  echo "    less $STAGING/manifest.txt"
  echo
  echo "If you're satisfied, commit and push from this directory (NOT the staging dir)."
else
  echo "❌ Issues found above. Fix before pushing."
  exit 1
fi
