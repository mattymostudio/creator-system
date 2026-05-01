#!/usr/bin/env python3
"""
Face Detection — scans Photos and Saved_Images folders, copies images
containing faces to an Organized/People/ folder (preserving month structure).

Usage:
    python3 detect_faces.py [--organized-dir <dir>] [--dry-run]
"""

import argparse
import logging
import os
import shutil
import sys
import warnings
from collections import Counter
from pathlib import Path

logging.getLogger('exifread').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

import face_recognition
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

# Max dimension to resize to before face detection (speeds things up significantly)
MAX_DIM = 1200

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp'}


def detect_faces_in_image(filepath):
    """
    Detect faces in an image. Returns the number of faces found.
    Resizes large images for speed.
    """
    try:
        img = Image.open(filepath)

        # Convert HEIC/etc to RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize for speed
        w, h = img.size
        if max(w, h) > MAX_DIM:
            scale = MAX_DIM / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # Convert to numpy array for face_recognition
        import numpy as np
        img_array = np.array(img)

        # Detect faces using HOG model (faster than CNN)
        face_locations = face_recognition.face_locations(img_array, model='hog')
        return len(face_locations)

    except Exception as e:
        return -1  # error


def scan_and_copy_people(organized_dir, dry_run=False):
    """Scan Photos and Saved_Images for faces, copy matches to People/."""
    organized = Path(organized_dir)
    people_dir = organized / 'People'

    # Scan these categories for faces
    scan_dirs = ['Photos', 'Saved_Images']

    # Gather all image files
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
    print(f"Scanning {total} images for faces...\n")

    stats = Counter()
    face_count_dist = Counter()

    for i, (filepath, category, month) in enumerate(all_files, 1):
        if i % 100 == 0 or i == total:
            pct = i * 100 // total
            print(f"  Scanning: {i}/{total} ({pct}%) — {stats['with_faces']} with faces so far")

        num_faces = detect_faces_in_image(str(filepath))

        if num_faces > 0:
            stats['with_faces'] += 1
            face_count_dist[num_faces] += 1

            # Symlink to People/month/
            dest_dir = people_dir / month
            dest_path = dest_dir / filepath.name

            # Handle duplicates
            if dest_path.exists():
                stem = dest_path.stem
                suffix = dest_path.suffix
                counter = 1
                while dest_path.exists():
                    dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

            if not dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
                os.symlink(filepath.resolve(), dest_path)

        elif num_faces == 0:
            stats['no_faces'] += 1
        else:
            stats['errors'] += 1

    # Summary
    print(f"\n{'=' * 50}")
    print(f"{'DRY RUN' if dry_run else 'DONE'}")
    print(f"{'=' * 50}")
    print(f"\nResults:")
    print(f"  Images with faces:    {stats['with_faces']}")
    print(f"  Images without faces: {stats['no_faces']}")
    print(f"  Errors:               {stats['errors']}")
    print(f"\nFace count distribution:")
    for n, count in sorted(face_count_dist.items()):
        print(f"  {n} face{'s' if n > 1 else '':3}: {count} images")

    if not dry_run and stats['with_faces'] > 0:
        print(f"\nFace images copied to: {people_dir}/")
        # Show month breakdown
        for month_dir in sorted(people_dir.iterdir()):
            if month_dir.is_dir():
                count = len(list(month_dir.iterdir()))
                print(f"  {month_dir.name}: {count}")

    return stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Detect faces in organized photos')
    parser.add_argument('--organized-dir', '-d', default='Organized',
                        help='Path to Organized directory (default: Organized)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would happen without copying')
    args = parser.parse_args()

    scan_and_copy_people(args.organized_dir, dry_run=args.dry_run)
