#!/usr/bin/env python3
"""
Organize Flat Folders — sorts files within project folders into type subfolders.

Turns:  Projects/MedMen/logo.psd, proposal.pdf, photo.jpg (1811 files flat)
Into:   Projects/MedMen/Design/logo.psd
        Projects/MedMen/Documents/proposal.pdf
        Projects/MedMen/Images/photo.jpg

Only touches folders that are flat (no existing subdirectories).
Preserves folders that already have structure.

Usage:
    python3 scripts/organize_flat_folders.py Organized_Docs/Projects --dry-run
    python3 scripts/organize_flat_folders.py Organized_Docs/Projects
"""

import argparse
import shutil
import sys
from collections import defaultdict
from pathlib import Path

# File extension → subfolder name
TYPE_MAP = {
    # Documents
    '.pdf': 'Documents', '.doc': 'Documents', '.docx': 'Documents',
    '.txt': 'Documents', '.md': 'Documents', '.rtf': 'Documents',
    '.pages': 'Documents', '.odt': 'Documents', '.dot': 'Documents',
    '.epub': 'Documents',
    # Spreadsheets
    '.xls': 'Spreadsheets', '.xlsx': 'Spreadsheets', '.csv': 'Spreadsheets',
    '.numbers': 'Spreadsheets', '.xlsm': 'Spreadsheets',
    # Presentations
    '.ppt': 'Presentations', '.pptx': 'Presentations',
    '.key': 'Presentations', '.keynote': 'Presentations',
    # Design
    '.psd': 'Design', '.ai': 'Design', '.sketch': 'Design',
    '.fig': 'Design', '.indd': 'Design', '.svg': 'Design',
    '.eps': 'Design', '.tif': 'Design', '.tiff': 'Design',
    '.raw': 'Design', '.cr2': 'Design', '.nef': 'Design',
    '.dng': 'Design',
    # Images
    '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images',
    '.gif': 'Images', '.heic': 'Images', '.heif': 'Images',
    '.webp': 'Images', '.bmp': 'Images', '.ico': 'Images',
    # Video
    '.mov': 'Video', '.mp4': 'Video', '.m4v': 'Video',
    '.avi': 'Video', '.mkv': 'Video', '.wmv': 'Video',
    '.webm': 'Video', '.flv': 'Video', '.3gp': 'Video',
    '.mts': 'Video', '.prores': 'Video',
    # Audio
    '.mp3': 'Audio', '.m4a': 'Audio', '.wav': 'Audio',
    '.aac': 'Audio', '.flac': 'Audio', '.ogg': 'Audio',
    '.aiff': 'Audio', '.wma': 'Audio', '.opus': 'Audio',
    # Web
    '.html': 'Web', '.htm': 'Web', '.css': 'Web',
    '.js': 'Web', '.json': 'Web', '.xml': 'Web',
    '.liquid': 'Web',
    # Fonts
    '.otf': 'Fonts', '.ttf': 'Fonts', '.woff': 'Fonts',
    '.woff2': 'Fonts', '.eot': 'Fonts', '.afm': 'Fonts',
    '.pfb': 'Fonts', '.pfm': 'Fonts',
    # Archives
    '.zip': 'Archives', '.gz': 'Archives', '.tar': 'Archives',
    '.rar': 'Archives', '.7z': 'Archives', '.dmg': 'Archives',
    '.sit': 'Archives', '.cpgz': 'Archives',
}


def is_flat(folder):
    """Check if a folder has no subdirectories (only files at root)."""
    for item in folder.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            return False
    return True


def file_count(folder):
    """Count non-hidden files in folder."""
    return sum(1 for f in folder.iterdir() if f.is_file() and not f.name.startswith('.'))


def main():
    parser = argparse.ArgumentParser(description='Organize flat project folders by file type')
    parser.add_argument('projects_dir', help='Path to Projects/ folder')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview without moving')
    parser.add_argument('--min-files', type=int, default=5,
                        help='Only organize folders with at least this many files (default: 5)')
    args = parser.parse_args()

    projects = Path(args.projects_dir).expanduser().resolve()
    if not projects.is_dir():
        print(f'Error: {projects} is not a directory')
        sys.exit(1)

    print('=' * 50)
    print('Organize Flat Folders')
    print('=' * 50)
    print(f'Source:    {projects}')
    print(f'Mode:     {"DRY RUN" if args.dry_run else "LIVE"}')
    print(f'Min files: {args.min_files}')
    print()

    # Find flat folders
    flat_folders = []
    structured_folders = []
    for folder in sorted(projects.iterdir()):
        if not folder.is_dir() or folder.name.startswith('.') or folder.name.startswith('_'):
            continue
        if is_flat(folder):
            count = file_count(folder)
            if count >= args.min_files:
                flat_folders.append((folder, count))
            else:
                structured_folders.append((folder.name, count, 'skipped (too few files)'))
        else:
            count = sum(1 for _ in folder.rglob('*') if _.is_file() and not _.name.startswith('.'))
            structured_folders.append((folder.name, count, 'already has structure'))

    print(f'Flat folders to organize: {len(flat_folders)}')
    for folder, count in flat_folders:
        print(f'  {count:>5}  {folder.name}/')
    print()

    if structured_folders:
        print(f'Skipping {len(structured_folders)} folders:')
        for name, count, reason in structured_folders[:10]:
            print(f'  {count:>5}  {name}/  ({reason})')
        if len(structured_folders) > 10:
            print(f'  ... and {len(structured_folders) - 10} more')
        print()

    # Process each flat folder
    total_moved = 0
    total_errors = 0

    for folder, count in flat_folders:
        print(f'{"[DRY RUN] " if args.dry_run else ""}Organizing {folder.name}/ ({count} files)...')

        type_counts = defaultdict(int)
        errors = 0

        for filepath in sorted(folder.iterdir()):
            if not filepath.is_file() or filepath.name.startswith('.'):
                continue

            ext = filepath.suffix.lower()
            subfolder_name = TYPE_MAP.get(ext, 'Other')
            type_counts[subfolder_name] += 1

            dest_dir = folder / subfolder_name
            dest = dest_dir / filepath.name

            # Handle collision
            if dest.exists():
                stem = filepath.stem
                suffix = filepath.suffix
                counter = 1
                while dest.exists():
                    dest = dest_dir / f'{stem}_{counter}{suffix}'
                    counter += 1

            if not args.dry_run:
                try:
                    dest_dir.mkdir(exist_ok=True)
                    filepath.rename(dest)
                except Exception as e:
                    errors += 1
                    print(f'    Error: {filepath.name}: {e}')

        # Print breakdown for this folder
        for type_name, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f'    {cnt:>5}  {type_name}/')
        total_moved += count
        total_errors += errors

    # Summary
    print()
    print('=' * 50)
    print(f'{"DRY RUN — " if args.dry_run else ""}Done')
    print(f'  Folders organized: {len(flat_folders)}')
    print(f'  Files sorted:      {total_moved}')
    if total_errors:
        print(f'  Errors:            {total_errors}')
    print('=' * 50)


if __name__ == '__main__':
    main()
