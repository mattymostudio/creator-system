#!/usr/bin/env python3
"""
Event Clustering — groups photos by time proximity into "events".

An event is a cluster of photos taken within a configurable time gap.
If more than `gap` minutes pass between consecutive photos, a new event starts.

Output:
  Organized/Events/
  ├── 2025-07-14_Beach_Trip/        (named by date + time range)
  │   ├── photo1.HEIC -> symlink
  │   └── photo2.HEIC -> symlink
  └── events_report.md              (summary of all events)

Usage:
    python3 event_cluster.py [--organized-dir <dir>] [--gap 120] [--min-photos 3] [--dry-run]
"""

import argparse
import logging
import os
import sys
import warnings
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

logging.getLogger('exifread').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

import exifread

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp'}
VIDEO_EXTENSIONS = {'.mov', '.mp4', '.m4v'}


def get_best_date(filepath):
    """Get EXIF date or fall back to file birth time."""
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False, stop_tag='DateTimeOriginal')
            date_tag = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
            if date_tag:
                return datetime.strptime(str(date_tag), '%Y:%m:%d %H:%M:%S'), 'exif'
    except Exception:
        pass

    st = os.stat(filepath)
    if hasattr(st, 'st_birthtime'):
        return datetime.fromtimestamp(st.st_birthtime), 'file'
    return datetime.fromtimestamp(st.st_mtime), 'file'


def get_exif_location(filepath):
    """Extract GPS coordinates if available."""
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            lat = tags.get('GPS GPSLatitude')
            lon = tags.get('GPS GPSLongitude')
            lat_ref = tags.get('GPS GPSLatitudeRef')
            lon_ref = tags.get('GPS GPSLongitudeRef')
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
                return (lat_dec, lon_dec)
    except Exception:
        pass
    return None


def format_duration(td):
    """Format a timedelta as human-readable."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def cluster_events(organized_dir, gap_minutes=120, min_photos=3, dry_run=False):
    """Cluster photos into events based on time gaps."""
    organized = Path(organized_dir)
    events_dir = organized / 'Events'

    # Scan Photos and Videos folders
    scan_dirs = ['Photos', 'Videos']
    all_media = []

    print("Gathering media files and reading dates...")
    for category in scan_dirs:
        cat_dir = organized / category
        if not cat_dir.exists():
            continue
        for month_dir in sorted(cat_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for f in sorted(month_dir.iterdir()):
                ext = f.suffix.lower()
                if ext in IMAGE_EXTENSIONS or ext in VIDEO_EXTENSIONS:
                    all_media.append(f)

    print(f"Found {len(all_media)} media files. Reading timestamps...")

    # Get dates for all files
    dated_media = []
    for i, filepath in enumerate(all_media, 1):
        if i % 500 == 0:
            print(f"  Reading dates: {i}/{len(all_media)}")
        dt, source = get_best_date(str(filepath))
        loc = get_exif_location(str(filepath)) if filepath.suffix.lower() in IMAGE_EXTENSIONS else None
        dated_media.append((dt, filepath, source, loc))

    # Sort by date
    dated_media.sort(key=lambda x: x[0])

    # Cluster into events
    gap = timedelta(minutes=gap_minutes)
    events = []
    current_event = []

    for dt, filepath, date_source, loc in dated_media:
        if current_event and (dt - current_event[-1][0]) > gap:
            events.append(current_event)
            current_event = []
        current_event.append((dt, filepath, date_source, loc))

    if current_event:
        events.append(current_event)

    # Filter by minimum photos
    events = [e for e in events if len(e) >= min_photos]

    print(f"\nFound {len(events)} events (>= {min_photos} photos, {gap_minutes}min gap)")

    # Create event folders and report
    report_lines = [
        "# Photo Events Report\n",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"Settings: gap={gap_minutes}min, min_photos={min_photos}\n",
        f"Total events: {len(events)}\n",
        f"Total media in events: {sum(len(e) for e in events)}\n",
        "---\n",
    ]

    for idx, event in enumerate(events, 1):
        start_dt = event[0][0]
        end_dt = event[-1][0]
        duration = end_dt - start_dt
        num_photos = sum(1 for _, f, _, _ in event if f.suffix.lower() in IMAGE_EXTENSIONS)
        num_videos = sum(1 for _, f, _, _ in event if f.suffix.lower() in VIDEO_EXTENSIONS)

        # Event folder name
        event_name = start_dt.strftime('%Y-%m-%d_%H%M')
        if duration > timedelta(hours=1):
            event_name += f"__{format_duration(duration).replace(' ', '')}"
        event_folder = f"Event_{idx:03d}__{event_name}"

        # Check for GPS data
        locations = [loc for _, _, _, loc in event if loc is not None]

        # Report entry
        report_lines.append(f"## Event {idx}: {start_dt.strftime('%B %d, %Y')}\n")
        report_lines.append(f"- **Time**: {start_dt.strftime('%I:%M %p')} — {end_dt.strftime('%I:%M %p')}\n")
        report_lines.append(f"- **Duration**: {format_duration(duration)}\n")
        report_lines.append(f"- **Photos**: {num_photos}, **Videos**: {num_videos}\n")
        if locations:
            avg_lat = sum(l[0] for l in locations) / len(locations)
            avg_lon = sum(l[1] for l in locations) / len(locations)
            report_lines.append(f"- **Location**: [{avg_lat:.4f}, {avg_lon:.4f}](https://maps.google.com/?q={avg_lat},{avg_lon})\n")
        report_lines.append(f"- **Folder**: `{event_folder}/`\n")

        # List files
        report_lines.append(f"\n<details><summary>Files ({len(event)})</summary>\n\n")
        for dt, filepath, _, _ in event:
            report_lines.append(f"- `{filepath.name}` ({dt.strftime('%H:%M:%S')})\n")
        report_lines.append(f"\n</details>\n\n---\n")

        if not dry_run:
            dest_dir = events_dir / event_folder
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Create symlinks to original files (no extra disk usage)
            for _, filepath, _, _ in event:
                link_path = dest_dir / filepath.name
                if not link_path.exists():
                    os.symlink(filepath.resolve(), link_path)

    # Write report
    if not dry_run:
        events_dir.mkdir(parents=True, exist_ok=True)
        report_path = events_dir / 'events_report.md'
        report_path.write_text(''.join(report_lines), encoding='utf-8')
        print(f"\nReport saved to: {report_path}")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"{'DRY RUN' if dry_run else 'DONE'}")
    print(f"{'=' * 50}")

    # Top 10 biggest events
    events_sorted = sorted(events, key=lambda e: len(e), reverse=True)
    print(f"\nTop 10 largest events:")
    for i, event in enumerate(events_sorted[:10], 1):
        start = event[0][0]
        dur = event[-1][0] - event[0][0]
        print(f"  {i}. {start.strftime('%b %d, %Y %I:%M%p')} — {len(event)} files, {format_duration(dur)}")

    return events


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cluster photos into events by time')
    parser.add_argument('--organized-dir', '-d', default='Organized',
                        help='Path to Organized directory')
    parser.add_argument('--gap', '-g', type=int, default=120,
                        help='Minutes between events (default: 120)')
    parser.add_argument('--min-photos', '-m', type=int, default=3,
                        help='Minimum photos per event (default: 3)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show events without creating folders')
    args = parser.parse_args()

    cluster_events(args.organized_dir, gap_minutes=args.gap,
                   min_photos=args.min_photos, dry_run=args.dry_run)
