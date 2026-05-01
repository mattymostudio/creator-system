#!/usr/bin/env bash
# package-release.sh — build deterministic zip artifacts for a release.
#
# Usage:
#   ./scripts/package-release.sh [version-tag]
#
# Default version: today's date (YYYY-MM-DD)
#
# Produces:
#   artifacts/creator-system-vault-<version>.zip       — the vault kit
#   artifacts/creator-system-tools-<version>.zip       — the ingestion tools
#
# Both zips are built from a clean staging dir. Private files (RECIPIENTS.md,
# email-to-*.md, _archive/, cohort-bonus/, GITHUB_DEPLOYMENT_PLAN.md,
# ONBOARDING_REDESIGN.md, COHORT_*_HANDOUT.*) are excluded.

set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-$(date +%Y-%m-%d)}"
ARTIFACTS="$KIT_DIR/artifacts"
STAGE="$KIT_DIR/_build_release"

echo "==> Creator System release packager"
echo "    Version: v${VERSION}"
echo "    Kit dir: $KIT_DIR"
echo

# 1. Pre-flight: refuse to build if check-release.sh fails
echo "==> Running check-release.sh"
bash "$KIT_DIR/scripts/check-release.sh"
echo

# 2. Clean stage
rm -rf "$STAGE"
mkdir -p "$STAGE/creator-system-vault" "$STAGE/creator-system-tools" "$ARTIFACTS"

# 3. Stage the vault kit
echo "==> Staging vault kit"
cp -R "$KIT_DIR/vault" "$STAGE/creator-system-vault/"
cp "$KIT_DIR/README.md" \
   "$KIT_DIR/CONTRIBUTING.md" \
   "$KIT_DIR/LICENSE" \
   "$KIT_DIR/RECIPES.md" \
   "$KIT_DIR/RELEASE_NOTES.md" \
   "$KIT_DIR/CHANGELOG.md" \
   "$KIT_DIR/Standard Operating Procedure.md" \
   "$KIT_DIR/Data Sources to Gather.md" \
   "$KIT_DIR/.gitignore" \
   "$STAGE/creator-system-vault/" 2>/dev/null || true
cp -R "$KIT_DIR/.github" "$STAGE/creator-system-vault/" 2>/dev/null || true

# 4. Stage the tools pack
echo "==> Staging tools pack"
cp -R "$KIT_DIR/tools/." "$STAGE/creator-system-tools/"
cp "$KIT_DIR/LICENSE" \
   "$KIT_DIR/RELEASE_NOTES.md" \
   "$STAGE/creator-system-tools/" 2>/dev/null || true

# 5. Strip noise from staging
find "$STAGE" -name '.DS_Store' -delete
find "$STAGE" -name 'RECAP.md' -delete
find "$STAGE" -name 'settings.local.json' -delete
find "$STAGE" -path '*/.obsidian/workspace*' -delete

# 6. Build the zips
echo "==> Building zips"
cd "$STAGE"
rm -f "$ARTIFACTS/creator-system-vault-${VERSION}.zip" \
      "$ARTIFACTS/creator-system-tools-${VERSION}.zip"

zip -r -q -X "$ARTIFACTS/creator-system-vault-${VERSION}.zip" \
    creator-system-vault -x '*.DS_Store'

zip -r -q -X "$ARTIFACTS/creator-system-tools-${VERSION}.zip" \
    creator-system-tools -x '*.DS_Store'

# 7. Print summary + SHA256
cd "$ARTIFACTS"
echo
echo "==> Release artifacts ready"
for f in "creator-system-vault-${VERSION}.zip" "creator-system-tools-${VERSION}.zip"; do
  size=$(ls -la "$f" | awk '{print $5}')
  sha=$(shasum -a 256 "$f" | awk '{print $1}')
  echo "    $f"
  echo "        size:   $size bytes"
  echo "        sha256: $sha"
done

echo
echo "✅ Done. Artifacts in: $ARTIFACTS/"
echo
echo "Next steps:"
echo "  git tag v${VERSION}"
echo "  git push origin main && git push origin v${VERSION}"
echo "  gh release create v${VERSION} \\"
echo "    --title 'Creator System v${VERSION}' \\"
echo "    --notes-file RELEASE_NOTES.md \\"
echo "    artifacts/creator-system-vault-${VERSION}.zip \\"
echo "    artifacts/creator-system-tools-${VERSION}.zip"

# 8. Cleanup stage
rm -rf "$STAGE"
