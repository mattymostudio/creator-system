#!/bin/bash
# process.sh — Run the full photo processing pipeline on a folder
#
# Usage: ./process.sh <source_folder> [--move|--copy]
#
# Steps:
#   1. Organize by type + month + screenshot detection
#   2. Detect faces → People/ (symlinks)
#   3. OCR screenshots + classify content
#   4. Cluster photos into events (symlinks)
#   5. NSFW/sensitive content scan (symlinks)
#   6. Generate screenshot content report (markdown)
#   7. Detailed classification + Obsidian knowledge base

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/scripts" && pwd)"
SOURCE="${1:?Usage: ./process.sh <source_folder> [--move|--copy]}"
MODE="${2:---move}"

if [ ! -d "$SOURCE" ]; then
    echo "Error: $SOURCE is not a directory"
    exit 1
fi

OUTPUT="$(dirname "$SOURCE")/Organized"

echo "============================================"
echo "Photo Processing Pipeline"
echo "============================================"
echo "Source:  $SOURCE"
echo "Output:  $OUTPUT"
echo "Mode:    $MODE"
echo ""

# Step 1: Organize
echo "[1/8] Organizing files by type and month..."
python3 "$SCRIPT_DIR/organize.py" "$SOURCE" --output "$OUTPUT" $MODE
echo ""

# Step 2: Face detection
echo "[2/8] Detecting faces..."
python3 "$SCRIPT_DIR/detect_faces.py" --organized-dir "$OUTPUT"
echo ""

# Step 3: OCR screenshots
echo "[3/8] OCR-ing screenshots..."
python3 "$SCRIPT_DIR/extract_screenshots.py" --organized-dir "$OUTPUT"
echo ""

# Step 4: Event clustering
echo "[4/8] Clustering events..."
python3 "$SCRIPT_DIR/event_cluster.py" --organized-dir "$OUTPUT"
echo ""

# Step 5: NSFW scan
echo "[5/8] Scanning for sensitive content..."
python3 "$SCRIPT_DIR/nsfw_scan.py" --organized-dir "$OUTPUT"
echo ""

# Step 6: Screenshot report
echo "[6/8] Generating screenshot content report..."
python3 "$SCRIPT_DIR/screenshot_report.py" --organized-dir "$OUTPUT"
echo ""

# Step 7: Detailed classification
echo "[7/8] Running detailed screenshot classification..."
python3 "$SCRIPT_DIR/classify_detailed.py" --organized-dir "$OUTPUT"
echo ""

# Step 8: Obsidian knowledge base
echo "[8/8] Building Obsidian knowledge base..."
python3 "$SCRIPT_DIR/backfill_vault.py" --organized-dir "$OUTPUT"
echo ""

echo "============================================"
echo "Pipeline complete!"
echo "============================================"
echo "Output: $OUTPUT"
du -sh "$OUTPUT"/* 2>/dev/null
