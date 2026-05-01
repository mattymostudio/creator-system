#!/usr/bin/env python3
"""
organize_drive.py — Smart recursive organizer for external drive.

Moves files from source to a new output directory on the same drive.
Preserves existing folder hierarchy. At each level, if loose files span
multiple type categories (and there are enough), sorts them into
type subfolders (Documents/, Images/, Design/, Video/, etc.).

Smart rules:
  • Existing named subdirectories always preserved
  • Type subfolders created only when ≥8 files AND ≥2 type categories
  • Single-type or small groups → moved flat (no extra subfolders)
  • Folders already named as a type (Images/, Documents/) aren't re-sorted
  • Recurses to full depth
  • Every move logged to _manifest.csv for reversibility
  • Skips hidden files/folders (.DS_Store, ._ resource forks)

Usage:
    python3 scripts/organize_drive.py /Volumes/2025/Organized /Volumes/2025/Organized_Output --dry-run
    python3 scripts/organize_drive.py /Volumes/2025/Organized /Volumes/2025/Organized_Output
"""

import argparse
import csv
import shutil
import sys
from collections import defaultdict
from pathlib import Path


# ── Extension → type subfolder ───────────────────────────────────────
TYPE_MAP = {
    # Documents
    '.pdf': 'Documents', '.doc': 'Documents', '.docx': 'Documents',
    '.txt': 'Documents', '.md': 'Documents', '.rtf': 'Documents',
    '.pages': 'Documents', '.odt': 'Documents', '.dot': 'Documents',
    '.epub': 'Documents', '.gdoc': 'Documents', '.textclipping': 'Documents',
    # Spreadsheets
    '.xls': 'Spreadsheets', '.xlsx': 'Spreadsheets', '.csv': 'Spreadsheets',
    '.numbers': 'Spreadsheets', '.xlsm': 'Spreadsheets', '.iif': 'Spreadsheets',
    '.gsheet': 'Spreadsheets', '.tsv': 'Spreadsheets',
    # Presentations
    '.ppt': 'Presentations', '.pptx': 'Presentations',
    '.key': 'Presentations', '.keynote': 'Presentations',
    # Design
    '.psd': 'Design', '.ai': 'Design', '.sketch': 'Design',
    '.fig': 'Design', '.indd': 'Design', '.svg': 'Design',
    '.eps': 'Design', '.tif': 'Design', '.tiff': 'Design',
    '.raw': 'Design', '.cr2': 'Design', '.nef': 'Design',
    '.dng': 'Design', '.nib': 'Design',
    '.xmp': 'Design', '.prproj': 'Design', '.aep': 'Design',
    # Images
    '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images',
    '.gif': 'Images', '.heic': 'Images', '.heif': 'Images',
    '.webp': 'Images', '.bmp': 'Images', '.ico': 'Images',
    '.aae': 'Images',
    # Video
    '.mov': 'Video', '.mp4': 'Video', '.m4v': 'Video',
    '.avi': 'Video', '.mkv': 'Video', '.wmv': 'Video',
    '.webm': 'Video', '.flv': 'Video', '.3gp': 'Video',
    '.mts': 'Video', '.prores': 'Video',
    '.mpeg': 'Video', '.mpg': 'Video', '.srt': 'Video',
    # Audio
    '.mp3': 'Audio', '.m4a': 'Audio', '.wav': 'Audio',
    '.aac': 'Audio', '.flac': 'Audio', '.ogg': 'Audio',
    '.aiff': 'Audio', '.wma': 'Audio', '.opus': 'Audio',
    '.aif': 'Audio',
    # Web
    '.html': 'Web', '.htm': 'Web', '.css': 'Web',
    '.js': 'Web', '.json': 'Web', '.xml': 'Web',
    '.liquid': 'Web', '.webloc': 'Web',
    # Fonts
    '.otf': 'Fonts', '.ttf': 'Fonts', '.woff': 'Fonts',
    '.woff2': 'Fonts', '.eot': 'Fonts', '.afm': 'Fonts',
    '.pfb': 'Fonts', '.pfm': 'Fonts',
    # Archives
    '.zip': 'Archives', '.gz': 'Archives', '.tar': 'Archives',
    '.rar': 'Archives', '.7z': 'Archives', '.dmg': 'Archives',
    '.sit': 'Archives', '.cpgz': 'Archives',
    # Code
    '.py': 'Code', '.sol': 'Code', '.jsx': 'Code', '.tsx': 'Code',
    '.ts': 'Code', '.rb': 'Code', '.go': 'Code', '.swift': 'Code',
    '.java': 'Code', '.sh': 'Code', '.yaml': 'Code', '.yml': 'Code',
    '.toml': 'Code', '.rs': 'Code', '.c': 'Code', '.cpp': 'Code',
    '.h': 'Code', '.m': 'Code',
}

# If a folder has one of these names, don't reorganize its contents
TYPE_FOLDER_NAMES = {
    'documents', 'images', 'design', 'video', 'audio', 'web',
    'fonts', 'archives', 'spreadsheets', 'presentations', 'code', 'other',
}

MIN_FILES = 8
MIN_TYPES = 2


def get_type(filepath):
    """Return type category for a file."""
    return TYPE_MAP.get(filepath.suffix.lower(), 'Other')


def unique_dest(dest_dir, filename):
    """Collision-safe destination path."""
    dest = dest_dir / filename
    if not dest.exists():
        return dest
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    # macOS 255-byte limit
    max_stem = 240 - len(suffix.encode('utf-8'))
    if len(stem.encode('utf-8')) > max_stem:
        stem = stem[:max_stem]
    counter = 1
    while dest.exists():
        dest = dest_dir / f'{stem}_{counter}{suffix}'
        counter += 1
    return dest


def process_directory(src, dst, manifest, dry_run, depth, stats, source_root, verbose_dirs, use_move=False):
    """Recursively process one directory level."""
    try:
        items = sorted(src.iterdir())
    except PermissionError:
        stats['errors'] += 1
        return
    except OSError:
        stats['errors'] += 1
        return

    files = [f for f in items if f.is_file() and not f.name.startswith('.')]
    subdirs = [d for d in items if d.is_dir() and not d.name.startswith('.')
               and not d.is_symlink()]

    # ── Decide: organize files into type subfolders? ──
    organize = False
    type_groups = defaultdict(list)

    if files:
        for f in files:
            type_groups[get_type(f)].append(f)

        if (len(files) >= MIN_FILES
                and len(type_groups) >= MIN_TYPES
                and src.name.lower() not in TYPE_FOLDER_NAMES):
            organize = True

    # ── Move files ──
    if files:
        if organize:
            stats['organized_dirs'] += 1
            rel = src.relative_to(source_root)
            breakdown = ', '.join(
                f'{len(flist)} {tname}'
                for tname, flist in sorted(type_groups.items(), key=lambda x: -len(x[1]))
            )
            verbose_dirs.append((str(rel), len(files), breakdown))

            for type_name, type_files in type_groups.items():
                dest_dir = dst / type_name
                for filepath in type_files:
                    dest = unique_dest(dest_dir, filepath.name)
                    if not dry_run:
                        try:
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            if use_move:
                                shutil.move(str(filepath), str(dest))
                            else:
                                shutil.copy2(str(filepath), str(dest))
                            if manifest:
                                manifest.writerow([str(filepath), str(dest)])
                        except Exception as e:
                            stats['errors'] += 1
                            continue
                    stats['moved'] += 1
        else:
            stats['flat_dirs'] += 1
            for filepath in files:
                dest = unique_dest(dst, filepath.name)
                if not dry_run:
                    try:
                        dst.mkdir(parents=True, exist_ok=True)
                        if use_move:
                            shutil.move(str(filepath), str(dest))
                        else:
                            shutil.copy2(str(filepath), str(dest))
                        if manifest:
                            manifest.writerow([str(filepath), str(dest)])
                    except Exception as e:
                        stats['errors'] += 1
                        continue
                stats['moved'] += 1

    # ── Recurse into subdirectories ──
    for subdir in subdirs:
        process_directory(
            subdir, dst / subdir.name, manifest, dry_run,
            depth + 1, stats, source_root, verbose_dirs, use_move=use_move
        )


def main():
    parser = argparse.ArgumentParser(description='Smart recursive drive organizer')
    parser.add_argument('source', help='Source directory')
    parser.add_argument('output', help='Output directory')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview without moving')
    parser.add_argument('--min-files', type=int, default=8,
                        help='Min files to trigger type subfolders (default: 8)')
    parser.add_argument('--min-types', type=int, default=2,
                        help='Min type categories to trigger subfolders (default: 2)')
    parser.add_argument('--move', action='store_true',
                        help='Move files instead of copy (default: copy)')
    args = parser.parse_args()

    global MIN_FILES, MIN_TYPES
    MIN_FILES = args.min_files
    MIN_TYPES = args.min_types

    source = Path(args.source).resolve()
    output = Path(args.output).resolve()

    if not source.is_dir():
        print(f'Error: {source} is not a directory')
        sys.exit(1)

    # Safety: output must not be inside source
    try:
        output.relative_to(source)
        print(f'Error: output is inside source — aborting')
        sys.exit(1)
    except ValueError:
        pass

    print('=' * 65)
    print('Smart Drive Organizer')
    print('=' * 65)
    print(f'Source:     {source}')
    print(f'Output:     {output}')
    transfer = 'move' if args.move else 'copy'
    print(f'Mode:       {"DRY RUN" if args.dry_run else f"LIVE — {transfer}ing files"}')
    print(f'Thresholds: organize when ≥{MIN_FILES} files AND ≥{MIN_TYPES} types')
    print()

    top_folders = sorted([d for d in source.iterdir()
                          if d.is_dir() and not d.name.startswith('.')])

    # Manifest (live mode only)
    manifest_path = output / '_manifest.csv'
    manifest_file = None
    manifest_writer = None
    if not args.dry_run:
        output.mkdir(parents=True, exist_ok=True)
        manifest_file = open(manifest_path, 'w', newline='')
        manifest_writer = csv.writer(manifest_file)
        manifest_writer.writerow(['source', 'destination'])

    grand = {'moved': 0, 'errors': 0, 'organized_dirs': 0, 'flat_dirs': 0}

    for folder in top_folders:
        print(f'━━━ {folder.name} ━━━')

        file_count = sum(1 for f in folder.rglob('*')
                         if f.is_file() and not f.name.startswith('.'))
        dir_count = sum(1 for d in folder.rglob('*')
                        if d.is_dir() and not d.name.startswith('.'))
        print(f'  {file_count:,} files across {dir_count:,} subdirs')

        stats = {'moved': 0, 'errors': 0, 'organized_dirs': 0, 'flat_dirs': 0}
        verbose_dirs = []

        process_directory(
            folder, output / folder.name, manifest_writer, args.dry_run,
            0, stats, source, verbose_dirs, use_move=args.move
        )

        # Show organized dirs (where we created type subfolders)
        if verbose_dirs:
            print(f'  Organized into type subfolders ({stats["organized_dirs"]} dirs):')
            for rel_path, count, breakdown in verbose_dirs[:30]:
                print(f'    {rel_path}/ ({count} files) → {breakdown}')
            if len(verbose_dirs) > 30:
                print(f'    ... and {len(verbose_dirs) - 30} more')

        action_word = 'would transfer' if args.dry_run else ('moved' if args.move else 'copied')
        print(f'  → {stats["moved"]:,} files {action_word}')
        print(f'    {stats["organized_dirs"]:,} dirs organized | {stats["flat_dirs"]:,} preserved as-is')
        if stats['errors']:
            print(f'    ⚠ {stats["errors"]:,} errors')
        print()

        for k in grand:
            grand[k] += stats[k]

    if manifest_file:
        manifest_file.close()

    # ── Grand summary ──
    print('=' * 65)
    print(f'{"DRY RUN — " if args.dry_run else ""}COMPLETE')
    print(f'  Total files:          {grand["moved"]:,}')
    print(f'  Dirs organized:       {grand["organized_dirs"]:,}')
    print(f'  Dirs preserved as-is: {grand["flat_dirs"]:,}')
    if grand['errors']:
        print(f'  Errors:               {grand["errors"]:,}')
    if not args.dry_run:
        print(f'  Manifest:             {manifest_path}')
    print('=' * 65)


if __name__ == '__main__':
    main()
