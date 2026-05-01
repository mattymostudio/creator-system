#!/usr/bin/env python3
"""
NSFW/Sensitive Content Scanner — flags potentially sensitive images.

Uses NudeNet to detect nudity/sensitive content in photos and saved images.
Flagged images are symlinked to a separate folder for review.

Output:
  Organized/Flagged_Sensitive/
  ├── <filename>.ext -> symlink to original
  └── nsfw_report.md

Usage:
    python3 nsfw_scan.py [--organized-dir <dir>] [--threshold 0.5] [--dry-run]
"""

import argparse
import json
import logging
import os
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

logging.getLogger('exifread').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

from nudenet import NudeDetector
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp'}

# NudeNet labels considered sensitive
SENSITIVE_LABELS = {
    'FEMALE_BREAST_EXPOSED',
    'FEMALE_GENITALIA_EXPOSED',
    'MALE_GENITALIA_EXPOSED',
    'BUTTOCKS_EXPOSED',
    'ANUS_EXPOSED',
    'FEMALE_BREAST_COVERED',
    'MALE_BREAST_EXPOSED',
}

# Higher concern labels
HIGH_CONCERN_LABELS = {
    'FEMALE_BREAST_EXPOSED',
    'FEMALE_GENITALIA_EXPOSED',
    'MALE_GENITALIA_EXPOSED',
    'ANUS_EXPOSED',
}


def convert_heic_to_jpg(filepath, tmp_dir):
    """Convert HEIC to temporary JPG for NudeNet (which needs JPG/PNG path)."""
    try:
        img = Image.open(filepath)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        tmp_path = tmp_dir / (Path(filepath).stem + '.jpg')
        img.save(str(tmp_path), 'JPEG', quality=85)
        return str(tmp_path)
    except Exception:
        return None


def scan_nsfw(organized_dir, threshold=0.5, dry_run=False):
    """Scan photos for NSFW content."""
    organized = Path(organized_dir)
    flagged_dir = organized / 'Flagged_Sensitive'
    tmp_dir = organized / '.tmp_nsfw'

    if not dry_run:
        tmp_dir.mkdir(parents=True, exist_ok=True)

    # Initialize detector
    print("Loading NudeNet model...")
    detector = NudeDetector()

    # Gather files from Photos and Saved_Images
    scan_dirs = ['Photos', 'Saved_Images']
    all_files = []
    for category in scan_dirs:
        cat_dir = organized / category
        if not cat_dir.exists():
            continue
        for month_dir in sorted(cat_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for f in sorted(month_dir.iterdir()):
                if f.suffix.lower() in IMAGE_EXTENSIONS:
                    all_files.append((f, category, month_dir.name))

    total = len(all_files)
    print(f"Scanning {total} images for sensitive content...\n")

    flagged = []
    stats = Counter()
    label_counts = Counter()

    for i, (filepath, category, month) in enumerate(all_files, 1):
        if i % 100 == 0 or i == total:
            print(f"  Scanning: {i}/{total} ({i*100//total}%) — {len(flagged)} flagged")

        try:
            # NudeNet needs a file path it can read — convert HEIC if needed
            scan_path = str(filepath)
            cleanup_tmp = False
            if filepath.suffix.lower() in ('.heic', '.heif'):
                if dry_run:
                    # In dry run, still need to convert for detection
                    tmp_dir.mkdir(parents=True, exist_ok=True)
                converted = convert_heic_to_jpg(str(filepath), tmp_dir)
                if converted is None:
                    stats['errors'] += 1
                    continue
                scan_path = converted
                cleanup_tmp = True

            # Run detection
            detections = detector.detect(scan_path)

            # Clean up temp file
            if cleanup_tmp and os.path.exists(scan_path):
                os.remove(scan_path)

            # Check for sensitive detections above threshold
            sensitive_detections = []
            for det in detections:
                label = det.get('class', '')
                score = det.get('score', 0)
                if label in SENSITIVE_LABELS and score >= threshold:
                    sensitive_detections.append({
                        'label': label,
                        'score': round(score, 3),
                        'high_concern': label in HIGH_CONCERN_LABELS,
                    })
                    label_counts[label] += 1

            if sensitive_detections:
                severity = 'HIGH' if any(d['high_concern'] for d in sensitive_detections) else 'MODERATE'
                flagged.append({
                    'file': filepath.name,
                    'path': str(filepath),
                    'category': category,
                    'month': month,
                    'detections': sensitive_detections,
                    'severity': severity,
                })
                stats[severity] += 1

                if not dry_run:
                    # Symlink to flagged folder, organized by severity
                    dest_dir = flagged_dir / severity / month
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    link_path = dest_dir / filepath.name
                    if not link_path.exists():
                        os.symlink(filepath.resolve(), link_path)

            else:
                stats['clean'] += 1

        except Exception as e:
            stats['errors'] += 1

    # Cleanup temp dir
    if tmp_dir.exists():
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # Generate report
    report_lines = [
        "# Sensitive Content Scan Report\n",
        f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"Threshold: {threshold}\n",
        f"Files scanned: {total}\n",
        "---\n",
        f"\n## Summary\n",
        f"- Clean: {stats['clean']}\n",
        f"- High severity: {stats.get('HIGH', 0)}\n",
        f"- Moderate severity: {stats.get('MODERATE', 0)}\n",
        f"- Errors: {stats.get('errors', 0)}\n",
    ]

    if label_counts:
        report_lines.append(f"\n## Detection Types\n")
        for label, count in label_counts.most_common():
            report_lines.append(f"- {label}: {count}\n")

    if flagged:
        report_lines.append(f"\n## Flagged Files\n")
        for item in sorted(flagged, key=lambda x: (x['severity'], x['month'])):
            labels = ', '.join(f"{d['label']} ({d['score']})" for d in item['detections'])
            report_lines.append(f"- **[{item['severity']}]** `{item['file']}` ({item['month']}, {item['category']}) — {labels}\n")

    if not dry_run:
        flagged_dir.mkdir(parents=True, exist_ok=True)
        report_path = flagged_dir / 'nsfw_report.md'
        report_path.write_text(''.join(report_lines), encoding='utf-8')
        print(f"\nReport saved to: {report_path}")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"{'DRY RUN' if dry_run else 'DONE'}")
    print(f"{'=' * 50}")
    print(f"\nResults:")
    print(f"  Clean:            {stats['clean']}")
    print(f"  Flagged HIGH:     {stats.get('HIGH', 0)}")
    print(f"  Flagged MODERATE: {stats.get('MODERATE', 0)}")
    print(f"  Errors:           {stats.get('errors', 0)}")

    if label_counts:
        print(f"\nDetection types:")
        for label, count in label_counts.most_common():
            print(f"  {label}: {count}")

    return flagged


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scan for NSFW/sensitive content')
    parser.add_argument('--organized-dir', '-d', default='Organized',
                        help='Path to Organized directory')
    parser.add_argument('--threshold', '-t', type=float, default=0.5,
                        help='Detection confidence threshold (default: 0.5)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show results without creating folders')
    args = parser.parse_args()

    scan_nsfw(args.organized_dir, threshold=args.threshold, dry_run=args.dry_run)
