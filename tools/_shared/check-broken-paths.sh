#!/usr/bin/env bash
# Scan tools/, inbox/, studio/, products/ for references to pre-reorg paths.
# Used after any path-shuffle / reorg to catch hardcoded breakage.
#
# Usage: tools/_shared/check-broken-paths.sh
# Exits 0 if clean, 1 if hits found.

set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

# Patterns that should no longer appear anywhere outside archive/ or backups.
# Tight match — only flags actual path usage (preceded by /, quote, or "Projects/"),
# not prose references to the vault's brand name "YOURBRAND Obsidian vault".
PATTERN='Projects/YOURBRAND Obsidian|path/to/your-photos|path/to/your-chatgpt|path/to/your-press|path/to/your-facebook/|path/to/your-photo-processing|path/to/your-photo-processing|"/YOURBRAND Obsidian|"/path/to/your-photos'

echo "Scanning for stale path references under $ROOT ..."
HITS=$(grep -rnE "$PATTERN" \
    --include="*.py" --include="*.json" --include="*.md" --include="*.sh" --include="*.ts" --include="*.js" --include="*.mjs" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git --exclude-dir=archive --exclude-dir=backups \
    --exclude-dir=01_contact_bundles --exclude-dir=02_enriched_bundles --exclude-dir=00_raw_takeouts --exclude-dir=parsed_domains \
    --exclude=check-broken-paths.sh \
    tools/ inbox/ studio/ products/ 2>/dev/null || true)

if [ -n "$HITS" ]; then
    echo ""
    echo "FOUND stale path references:"
    echo "$HITS"
    exit 1
fi

echo "Clean — no stale path references."
exit 0
