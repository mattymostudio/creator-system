#!/usr/bin/env python3
"""
Photo Organizer — sorts an iPhone photo dump into a structured folder hierarchy.

Output structure:
    Organized/
    ├── Photos/
    │   ├── 2025-07/
    │   └── ...
    ├── Screenshots/
    │   ├── 2025-07/
    │   └── ...
    ├── Videos/
    │   ├── 2025-07/
    │   └── ...
    ├── Saved_Images/
    │   ├── 2025-07/
    │   └── ...
    └── Other/
        └── 2025-07/

Usage:
    python3 organize.py <source_dir> [--output <dir>] [--dry-run] [--move]
"""

import argparse
import os
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import logging
import warnings

# Suppress noisy exifread/PIL warnings
logging.getLogger('exifread').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore', category=UserWarning)

import exifread
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

# Known iPhone/iPad screenshot resolutions (width x height, portrait)
IPHONE_SCREEN_RESOLUTIONS = {
    # iPhone 15 Pro Max, 14 Pro Max
    (1290, 2796),
    # iPhone 15 Pro, 14 Pro
    (1179, 2556),
    # iPhone 15, 15 Plus, 14, 14 Plus
    (1170, 2532),
    (1284, 2778),
    # iPhone 13 series
    (1170, 2532),
    (1284, 2778),
    (1080, 2340),
    # iPhone 12 series
    (1170, 2532),
    (1284, 2778),
    (1080, 2340),
    # iPhone 11 series
    (828, 1792),
    (1125, 2436),
    (1242, 2688),
    # iPhone SE
    (750, 1334),
    (640, 1136),
    # iPhone X/XS
    (1125, 2436),
    (1242, 2688),
    # iPhone 8/7/6
    (750, 1334),
    (1080, 1920),
    # iPad resolutions (common)
    (2048, 2732),
    (1668, 2388),
    (1668, 2224),
    (1620, 2160),
    (2048, 2732),
    (1640, 2360),
}

# Also allow landscape versions
SCREENSHOT_RESOLUTIONS = set()
for w, h in IPHONE_SCREEN_RESOLUTIONS:
    SCREENSHOT_RESOLUTIONS.add((w, h))
    SCREENSHOT_RESOLUTIONS.add((h, w))

VIDEO_EXTENSIONS = {'.mov', '.mp4', '.m4v', '.avi', '.mkv', '.webm', '.3gp'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.gif',
                    '.tiff', '.tif', '.bmp', '.raw', '.cr2', '.nef', '.dng'}


def get_exif_date(filepath):
    """Extract date from EXIF data. Returns datetime or None."""
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False, stop_tag='DateTimeOriginal')
            date_tag = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
            if date_tag:
                return datetime.strptime(str(date_tag), '%Y:%m:%d %H:%M:%S')
    except Exception:
        pass
    return None


def get_file_date(filepath):
    """Get file creation date (macOS birth time) or modification date."""
    st = os.stat(filepath)
    if hasattr(st, 'st_birthtime'):
        return datetime.fromtimestamp(st.st_birthtime)
    return datetime.fromtimestamp(st.st_mtime)


def get_date(filepath):
    """Get the best available date for a file."""
    exif_date = get_exif_date(filepath)
    if exif_date:
        return exif_date
    return get_file_date(filepath)


def has_camera_exif(filepath):
    """Check if file has camera-specific EXIF metadata."""
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            has_make = 'Image Make' in tags
            has_model = 'Image Model' in tags
            has_lens = 'EXIF LensModel' in tags
            has_focal = 'EXIF FocalLength' in tags
            return has_make or has_model or has_lens or has_focal
    except Exception:
        return False


def is_screenshot(filepath, ext):
    """Detect if an image is a screenshot."""
    # HEIC files are almost always camera photos on iPhone
    if ext in ('.heic', '.heif'):
        return False

    # Videos are never screenshots
    if ext in VIDEO_EXTENSIONS:
        return False

    try:
        img = Image.open(filepath)
        size = img.size  # (width, height)

        # Check if resolution matches a known screen resolution
        if size in SCREENSHOT_RESOLUTIONS:
            # If it also has camera EXIF, it's probably a photo, not a screenshot
            if not has_camera_exif(filepath):
                return True

        # Check for common screenshot indicators in PNG files:
        # - Exact screen resolution
        # - No camera EXIF
        # - RGBA mode (transparency, common in UI screenshots)
        if ext == '.png' and not has_camera_exif(filepath):
            w, h = size
            # Portrait phone-like aspect ratio with high resolution
            if w > 700 and h > 1200 and 1.5 < h / w < 2.5:
                return True
            # Landscape phone/tablet screenshots
            if h > 700 and w > 1200 and 1.5 < w / h < 2.5:
                return True

    except Exception:
        pass

    return False


def classify_file(filepath, ext):
    """
    Classify a file into a category.
    Returns: 'Photos', 'Screenshots', 'Videos', 'Saved_Images', or 'Other'
    """
    ext_lower = ext.lower()

    # Videos
    if ext_lower in VIDEO_EXTENSIONS:
        return 'Videos'

    # Not an image we recognize
    if ext_lower not in IMAGE_EXTENSIONS:
        return 'Other'

    # Screenshot detection
    if is_screenshot(filepath, ext_lower):
        return 'Screenshots'

    # HEIC = camera photo (iPhone native format)
    if ext_lower in ('.heic', '.heif'):
        return 'Photos'

    # JPG/JPEG with camera EXIF = photo
    if ext_lower in ('.jpg', '.jpeg') and has_camera_exif(filepath):
        return 'Photos'

    # JPG/PNG without camera EXIF and not a screenshot = saved/downloaded image
    if ext_lower in ('.jpg', '.jpeg', '.png'):
        return 'Saved_Images'

    # Everything else with camera data = photo
    if has_camera_exif(filepath):
        return 'Photos'

    return 'Other'


def get_month_folder(dt):
    """Format datetime as YYYY-MM folder name."""
    return dt.strftime('%Y-%m')


def safe_dest_path(dest_path):
    """If dest_path exists, add a numeric suffix to avoid overwriting."""
    if not dest_path.exists():
        return dest_path
    stem = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def organize(source_dir, output_dir, dry_run=False, move=False):
    """Main organization logic."""
    source = Path(source_dir)
    output = Path(output_dir)

    if not source.is_dir():
        print(f"Error: {source} is not a directory")
        sys.exit(1)

    # Gather all files
    files = [f for f in source.iterdir() if f.is_file() and not f.name.startswith('.')]
    total = len(files)
    print(f"Found {total} files to process\n")

    stats = Counter()
    month_stats = defaultdict(Counter)
    errors = []

    for i, filepath in enumerate(sorted(files), 1):
        ext = filepath.suffix
        if not ext:
            ext = '.unknown'

        # Progress
        if i % 500 == 0 or i == total:
            print(f"  Processing: {i}/{total} ({i*100//total}%)")

        try:
            # Classify
            category = classify_file(str(filepath), ext)

            # Get date for month folder
            dt = get_date(str(filepath))
            month = get_month_folder(dt)

            # Build destination path
            dest_dir = output / category / month
            dest_path = safe_dest_path(dest_dir / filepath.name)

            stats[category] += 1
            month_stats[category][month] += 1

            if not dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
                if move:
                    shutil.move(str(filepath), str(dest_path))
                else:
                    shutil.copy2(str(filepath), str(dest_path))

        except Exception as e:
            errors.append((filepath.name, str(e)))
            stats['_errors'] += 1

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"{'DRY RUN — no files were moved/copied' if dry_run else 'DONE'}")
    print(f"{'=' * 50}")
    print(f"\nCategory breakdown:")
    for cat in ['Photos', 'Screenshots', 'Videos', 'Saved_Images', 'Other']:
        if stats[cat]:
            print(f"  {cat}: {stats[cat]}")
            months = sorted(month_stats[cat].items())
            for m, c in months:
                print(f"    {m}: {c}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for name, err in errors[:20]:
            print(f"  {name}: {err}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")

    action = "would be moved" if dry_run and move else "would be copied" if dry_run else "moved" if move else "copied"
    print(f"\nTotal: {sum(stats[c] for c in ['Photos', 'Screenshots', 'Videos', 'Saved_Images', 'Other'])} files {action}")

    return stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Organize photos from an iPhone dump')
    parser.add_argument('source', help='Source directory containing photos')
    parser.add_argument('--output', '-o', default=None, help='Output directory (default: <source>/../Organized)')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show what would happen without making changes')
    parser.add_argument('--move', action='store_true', help='Move files instead of copying')
    args = parser.parse_args()

    if args.output is None:
        args.output = str(Path(args.source).parent / 'Organized')

    print(f"Source:  {args.source}")
    print(f"Output:  {args.output}")
    print(f"Mode:    {'MOVE' if args.move else 'COPY'}")
    print(f"Dry run: {'YES' if args.dry_run else 'NO'}")
    print()

    organize(args.source, args.output, dry_run=args.dry_run, move=args.move)
