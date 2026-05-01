#!/usr/bin/env python3
"""
Location Extractor — pulls GPS coordinates from all photos and exports to CSV.

Scans Photos, Saved_Images, Videos, and Other folders (skips Screenshots).
Extracts EXIF GPS data and date, outputs a CSV for mapping or analysis.

Output:
  <organized-dir>/locations.csv

Usage:
    python3 extract_locations.py -d "/Volumes/YOUR_DRIVE/Photos" [--dry-run]
"""

import argparse
import csv
import logging
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path

logging.getLogger('exifread').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

import exifread

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp',
                    '.tiff', '.tif', '.bmp', '.raw', '.cr2', '.nef', '.dng'}
VIDEO_EXTENSIONS = {'.mov', '.mp4', '.m4v'}
SCAN_DIRS = ['Photos', 'Saved_Images', 'Videos', 'Other']


def get_exif_data(filepath):
    """Extract GPS coordinates and date from EXIF."""
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)

            # Date
            date_tag = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
            dt = None
            if date_tag:
                try:
                    dt = datetime.strptime(str(date_tag), '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    pass

            # GPS
            lat = tags.get('GPS GPSLatitude')
            lon = tags.get('GPS GPSLongitude')
            lat_ref = tags.get('GPS GPSLatitudeRef')
            lon_ref = tags.get('GPS GPSLongitudeRef')
            alt = tags.get('GPS GPSAltitude')

            if lat and lon:
                def to_decimal(tag):
                    vals = tag.values
                    d = float(vals[0].num) / float(vals[0].den)
                    m = float(vals[1].num) / float(vals[1].den)
                    s = float(vals[2].num) / float(vals[2].den)
                    return d + m / 60 + s / 3600

                lat_dec = to_decimal(lat)
                lon_dec = to_decimal(lon)
                if lat_ref and str(lat_ref) == 'S':
                    lat_dec = -lat_dec
                if lon_ref and str(lon_ref) == 'W':
                    lon_dec = -lon_dec

                alt_m = None
                if alt:
                    try:
                        alt_m = round(float(alt.values[0].num) / float(alt.values[0].den), 1)
                    except Exception:
                        pass

                return lat_dec, lon_dec, alt_m, dt

    except Exception:
        pass
    return None, None, None, None


def extract_locations(organized_dir, dry_run=False):
    organized = Path(organized_dir)
    output_csv = organized / 'locations.csv'

    # Gather all media files (skip Screenshots)
    all_files = []
    for category in SCAN_DIRS:
        cat_dir = organized / category
        if not cat_dir.exists():
            continue
        for month_dir in sorted(cat_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for f in sorted(month_dir.iterdir()):
                ext = f.suffix.lower()
                if ext in IMAGE_EXTENSIONS or ext in VIDEO_EXTENSIONS:
                    all_files.append((f, category, month_dir.name))

    total = len(all_files)
    print(f"Scanning {total} files for GPS data...\n")

    rows = []
    geo_count = 0
    errors = 0

    for i, (filepath, category, month) in enumerate(all_files, 1):
        if i % 1000 == 0 or i == total:
            print(f"  {i}/{total} ({i*100//total}%) — {geo_count} with GPS")

        lat, lon, alt, dt = get_exif_data(str(filepath))

        if lat is not None and lon is not None:
            geo_count += 1
            rows.append({
                'filename': filepath.name,
                'category': category,
                'month': month,
                'latitude': round(lat, 6),
                'longitude': round(lon, 6),
                'altitude_m': alt if alt else '',
                'date': dt.strftime('%Y-%m-%d %H:%M:%S') if dt else '',
                'path': str(filepath),
            })

    # Write CSV
    if not dry_run and rows:
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'filename', 'category', 'month', 'latitude', 'longitude',
                'altitude_m', 'date', 'path'
            ])
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nCSV saved to: {output_csv}")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"{'DRY RUN' if dry_run else 'DONE'}")
    print(f"{'=' * 50}")
    print(f"  Total files scanned: {total}")
    print(f"  Files with GPS data: {geo_count} ({geo_count*100//total if total else 0}%)")
    print(f"  Files without GPS:   {total - geo_count - errors}")
    print(f"  Errors:              {errors}")

    # Category breakdown
    from collections import Counter
    cat_counts = Counter(r['category'] for r in rows)
    print(f"\nGPS data by category:")
    for cat in SCAN_DIRS:
        if cat_counts[cat]:
            print(f"  {cat}: {cat_counts[cat]}")

    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract GPS locations from photos')
    parser.add_argument('--organized-dir', '-d', default='Organized',
                        help='Path to organized media directory')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Scan without writing CSV')
    args = parser.parse_args()

    extract_locations(args.organized_dir, dry_run=args.dry_run)
