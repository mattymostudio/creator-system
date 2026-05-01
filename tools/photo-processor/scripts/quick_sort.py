#!/usr/bin/env python3
"""
Quick Sort — fast file organizer. Type + month only, no OCR/AI/faces.

Output:
    Organized/
    ├── Photos/2025-07/
    ├── Screenshots/2025-07/
    ├── Videos/2025-07/
    ├── Saved_Images/2025-07/
    └── Other/2025-07/

Usage:
    python3 quick_sort.py <source_dir> [--output <dir>] [--move] [--dry-run]
"""

import argparse
import os
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import logging
import warnings
logging.getLogger('exifread').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

try:
    import exifread
except ImportError:
    exifread = None

VIDEO_EXT = {'.mov', '.mp4', '.m4v', '.avi', '.mkv', '.webm', '.3gp'}
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.gif',
             '.tiff', '.tif', '.bmp', '.raw', '.cr2', '.nef', '.dng'}

# Known iPhone screenshot resolutions (portrait + landscape)
SCREEN_RES = set()
for w, h in [(1290,2796),(1179,2556),(1170,2532),(1284,2778),(1080,2340),
             (828,1792),(1125,2436),(1242,2688),(750,1334),(640,1136),
             (1080,1920),(2048,2732),(1668,2388),(1668,2224),(1620,2160),
             (1640,2360)]:
    SCREEN_RES.add((w, h))
    SCREEN_RES.add((h, w))


def get_date(filepath):
    """EXIF date or file birth time."""
    if exifread:
        try:
            with open(filepath, 'rb') as f:
                tags = exifread.process_file(f, details=False, stop_tag='DateTimeOriginal')
                dt = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
                if dt:
                    return datetime.strptime(str(dt), '%Y:%m:%d %H:%M:%S')
        except Exception:
            pass
    st = os.stat(filepath)
    ts = st.st_birthtime if hasattr(st, 'st_birthtime') else st.st_mtime
    return datetime.fromtimestamp(ts)


def has_camera_data(filepath):
    """Quick check for camera EXIF (Make/Model)."""
    if not exifread:
        return False
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False, stop_tag='Image Model')
            return 'Image Make' in tags or 'Image Model' in tags
    except Exception:
        return False


def is_screenshot(filepath, ext):
    """Fast screenshot detection — resolution check only, no PIL needed."""
    if ext in ('.heic', '.heif'):
        return False
    if ext in VIDEO_EXT:
        return False
    # For PNG: check dimensions via header bytes (no PIL dependency)
    if ext == '.png':
        try:
            with open(filepath, 'rb') as f:
                header = f.read(32)
                if header[:8] == b'\x89PNG\r\n\x1a\n':
                    w = int.from_bytes(header[16:20], 'big')
                    h = int.from_bytes(header[20:24], 'big')
                    if (w, h) in SCREEN_RES:
                        return True
                    # Phone-like aspect ratio
                    if w > 700 and h > 1200 and 1.5 < h/w < 2.5:
                        return True
                    if h > 700 and w > 1200 and 1.5 < w/h < 2.5:
                        return True
        except Exception:
            pass
    return False


def classify(filepath, ext):
    """Classify into Photos/Screenshots/Videos/Saved_Images/Other."""
    ext = ext.lower()
    if ext in VIDEO_EXT:
        return 'Videos'
    if ext not in IMAGE_EXT:
        return 'Other'
    if is_screenshot(str(filepath), ext):
        return 'Screenshots'
    if ext in ('.heic', '.heif'):
        return 'Photos'
    if ext in ('.jpg', '.jpeg') and has_camera_data(str(filepath)):
        return 'Photos'
    if ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
        return 'Saved_Images'
    if has_camera_data(str(filepath)):
        return 'Photos'
    return 'Other'


def main():
    parser = argparse.ArgumentParser(description='Quick sort: type + month, no AI')
    parser.add_argument('source', help='Source directory')
    parser.add_argument('--output', '-o', default=None, help='Output dir (default: ../Organized)')
    parser.add_argument('--move', action='store_true', help='Move instead of copy')
    parser.add_argument('--dry-run', '-n', action='store_true')
    args = parser.parse_args()

    source = Path(args.source)
    output = Path(args.output) if args.output else source.parent / 'Organized'

    if not source.is_dir():
        print(f'Error: {source} is not a directory')
        sys.exit(1)

    files = [f for f in source.iterdir() if f.is_file() and not f.name.startswith('.')]
    total = len(files)
    print(f'Source:  {source}')
    print(f'Output:  {output}')
    print(f'Mode:    {"MOVE" if args.move else "COPY"}')
    print(f'Files:   {total}\n')

    stats = Counter()

    for i, filepath in enumerate(sorted(files), 1):
        if i % 500 == 0 or i == total:
            print(f'  {i}/{total} ({i*100//total}%)')

        ext = filepath.suffix.lower() or '.unknown'
        category = classify(filepath, ext)
        month = get_date(str(filepath)).strftime('%Y-%m')

        dest_dir = output / category / month
        dest_path = dest_dir / filepath.name

        if dest_path.exists():
            stem, suffix = dest_path.stem, dest_path.suffix
            c = 1
            while dest_path.exists():
                dest_path = dest_dir / f'{stem}_{c}{suffix}'
                c += 1

        stats[category] += 1

        if not args.dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            if args.move:
                shutil.move(str(filepath), str(dest_path))
            else:
                shutil.copy2(str(filepath), str(dest_path))

    print(f'\n{"DRY RUN" if args.dry_run else "Done"}:')
    for cat in ['Photos', 'Screenshots', 'Videos', 'Saved_Images', 'Other']:
        if stats[cat]:
            print(f'  {cat}: {stats[cat]}')
    print(f'  Total: {sum(stats.values())}')


if __name__ == '__main__':
    main()
