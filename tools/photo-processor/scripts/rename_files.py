#!/usr/bin/env python3
"""
Rename Files — adds full date to filenames.
Preserves all original metadata (creation date, modification date).

Before: Organized/Photos/2025-07/IMG_1234.HEIC
After:  Organized/Photos/2025-07/2025-07-15_IMG_1234.HEIC

Usage:
    python3 scripts/rename_files.py Organized
    python3 scripts/rename_files.py Organized --dry-run
    python3 scripts/rename_files.py /Volumes/MyDrive/Organized
"""

import argparse
import os
import sys
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

# Map folder name → filename prefix
PREFIXES = {
    'Photos': 'Photo',
    'Screenshots': 'Screenshot',
    'Videos': 'Video',
    'Saved_Images': 'Saved',
    'Other': 'Other',
}


def get_date(filepath):
    """Get the original capture date from EXIF, or file birth time."""
    # Try EXIF first
    if exifread:
        try:
            with open(filepath, 'rb') as f:
                tags = exifread.process_file(f, details=False, stop_tag='DateTimeOriginal')
                dt = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
                if dt:
                    return datetime.strptime(str(dt), '%Y:%m:%d %H:%M:%S')
        except Exception:
            pass
    # Fall back to file birth time (macOS) or modification time
    st = os.stat(filepath)
    ts = st.st_birthtime if hasattr(st, 'st_birthtime') else st.st_mtime
    return datetime.fromtimestamp(ts)


def is_already_renamed(filename):
    """Check if file was already renamed by this script (starts with YYYY-MM-DD_)."""
    return len(filename) > 11 and filename[4] == '-' and filename[7] == '-' and filename[10] == '_'


def main():
    parser = argparse.ArgumentParser(description='Rename files with category + date prefix')
    parser.add_argument('organized_dir', help='Path to Organized/ folder')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview without renaming')
    parser.add_argument('--undo', action='store_true', help='Remove prefixes (restore original names)')
    args = parser.parse_args()

    organized = Path(args.organized_dir)
    if not organized.is_dir():
        print(f'Error: {organized} is not a directory')
        sys.exit(1)

    total = 0
    renamed = 0
    skipped = 0

    for folder_name in PREFIXES:
        folder = organized / folder_name
        if not folder.exists():
            continue

        for month_dir in sorted(folder.iterdir()):
            if not month_dir.is_dir():
                continue

            for filepath in sorted(month_dir.iterdir()):
                if not filepath.is_file() or filepath.name.startswith('.'):
                    continue
                if filepath.is_symlink():
                    continue

                total += 1

                if args.undo:
                    # Strip date prefix: 2025-07-15_IMG_1234.HEIC → IMG_1234.HEIC
                    if is_already_renamed(filepath.name):
                        original_name = filepath.name[11:]  # after "2025-07-15_"
                        new_path = month_dir / original_name
                        if not new_path.exists():
                            if not args.dry_run:
                                filepath.rename(new_path)
                            renamed += 1
                            if args.dry_run:
                                print(f'  {filepath.name} → {original_name}')
                    continue

                # Skip if already renamed
                if is_already_renamed(filepath.name):
                    skipped += 1
                    continue

                # Get date
                file_date = get_date(str(filepath))
                date_str = file_date.strftime('%Y-%m-%d')

                # Build new name: 2025-07-15_IMG_1234.HEIC
                new_name = f'{date_str}_{filepath.name}'
                new_path = month_dir / new_name

                # Handle collision
                if new_path.exists():
                    skipped += 1
                    continue

                if not args.dry_run:
                    filepath.rename(new_path)

                renamed += 1

                if args.dry_run and renamed <= 20:
                    print(f'  {filepath.name} → {new_name}')

    action = 'undo' if args.undo else 'rename'
    print(f'\n{"DRY RUN — " if args.dry_run else ""}Done:')
    print(f'  Total files: {total}')
    print(f'  {"Restored" if args.undo else "Renamed"}: {renamed}')
    print(f'  Skipped: {skipped}')

    if args.dry_run and renamed > 20:
        print(f'\n  (showing first 20 of {renamed}, run without --dry-run to apply)')


if __name__ == '__main__':
    main()
