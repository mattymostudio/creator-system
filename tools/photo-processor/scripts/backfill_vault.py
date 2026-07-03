#!/usr/bin/env python3
"""
Backfill Vault — one-time migration of all existing screenshots into
an Obsidian-compatible knowledge base vault.

Reads:
  - screenshot_classification_report.json (9,426 entries)
  - Screenshots_Processed/{Category}/{YYYY-MM}/*.txt (full OCR text)
  - Screenshots/{YYYY-MM}/*.PNG (original images for symlinks)

Writes:
  - Vault/Screenshots/{YYYY-MM}/{file}.md (one note per screenshot)
  - Vault/_attachments/{YYYY-MM}/ (image symlinks)
  - Vault/Categories/*.md (MOC index per category)
  - Vault/Daily/*.md (daily digests)
  - Vault/Entities/*.md (aggregated entity pages)
  - Vault/_index.md (master index)

Usage:
    python3 backfill_vault.py [--organized-dir Organized] [--dry-run]
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

from entity_extractor import extract_entities, has_any_entities, summarize_entities
from obsidian_builder import (
    build_note, write_note, create_image_symlink,
    build_category_moc, build_daily_digest, build_entity_page,
    build_master_index, sanitize_category,
)


def build_txt_index(processed_dir):
    """Build a lookup: (file_stem, month) -> path to .txt file."""
    index = {}
    for cat_dir in processed_dir.iterdir():
        if not cat_dir.is_dir() or cat_dir.name.startswith('.'):
            continue
        for month_dir in cat_dir.iterdir():
            if not month_dir.is_dir():
                continue
            for txt in month_dir.glob('*.txt'):
                index[(txt.stem, month_dir.name)] = txt
    return index


def main(organized_dir='Organized', dry_run=False):
    organized = Path(organized_dir)
    vault_dir = organized / 'Vault'
    screenshots_dir = organized / 'Screenshots'
    processed_dir = organized / 'Screenshots_Processed'

    # Load classification data
    class_file = organized / 'screenshot_classification_report.json'
    if not class_file.exists():
        print(f"Error: {class_file} not found. Run classify_detailed.py first.")
        sys.exit(1)

    with open(class_file) as f:
        entries = json.load(f)

    print(f"Loaded {len(entries)} screenshot classifications")

    # Build text file index
    print("Building text file index...")
    txt_index = build_txt_index(processed_dir)
    print(f"Found {len(txt_index)} OCR text files")

    # Process all entries
    total = len(entries)
    category_counts = Counter()
    notes_by_category = defaultdict(list)
    notes_by_date = defaultdict(list)
    all_entities = {}  # file_stem -> entities dict
    entity_stats = Counter()

    print(f"\nGenerating vault notes...\n")

    for i, entry in enumerate(entries, 1):
        if i % 500 == 0 or i == total:
            print(f"  Processing: {i}/{total} ({i*100//total}%)")

        file_stem = entry['file']
        month = entry['month']
        category = entry['category']
        score = entry.get('score', 0)

        # Get full OCR text
        txt_path = txt_index.get((file_stem, month))
        if txt_path:
            ocr_text = txt_path.read_text(encoding='utf-8', errors='ignore')
        else:
            ocr_text = entry.get('text_preview', '')

        # Extract entities
        entities = extract_entities(ocr_text, category=category)
        entities['_month'] = month  # stash for index building
        all_entities[file_stem] = entities

        if has_any_entities(entities):
            entity_stats['with_entities'] += 1

        # Create image symlink and get relative path
        image_path = None
        if not dry_run:
            image_path = create_image_symlink(vault_dir, month, file_stem, screenshots_dir)

        if image_path is None:
            image_path = f'_attachments/{month}/{file_stem}.PNG'

        # Build note
        note_content = build_note(
            file_stem, month, category, score,
            ocr_text, entities, image_path
        )

        if not dry_run:
            write_note(vault_dir, file_stem, month, note_content)

        # Track for indexes
        category_counts[category] += 1
        entry_with_entities = {**entry, 'entities': entities}
        notes_by_category[category].append(entry_with_entities)

        # Group by date (use month as approximate date)
        notes_by_date[month].append(entry_with_entities)

    # Build index files
    print(f"\nBuilding index files...")

    if not dry_run:
        # Category MOCs
        for category, cat_entries in notes_by_category.items():
            build_category_moc(vault_dir, category, cat_entries)

        # Daily digests (by month since we don't have exact dates for most)
        for month, month_entries in notes_by_date.items():
            build_daily_digest(vault_dir, month, month_entries, all_entities)

        # Entity pages
        for key, label in [
            ('products', 'Products'),
            ('services', 'Services'),
            ('people', 'People'),
            ('contacts', 'Contacts'),
            ('todos', 'Action Items'),
            ('prices', 'Prices'),
            ('urls', 'URLs'),
            ('tickers', 'Stock Tickers'),
            ('phones', 'Phone Numbers'),
            ('emails', 'Emails'),
            ('addresses', 'Addresses'),
            ('handles', 'Social Handles'),
        ]:
            build_entity_page(vault_dir, key, label, all_entities)

        # Master index
        months = sorted(notes_by_date.keys())
        date_range = f'{months[0]} to {months[-1]}' if months else 'unknown'
        build_master_index(vault_dir, total, category_counts, date_range)

    # Summary
    print(f"\n{'=' * 50}")
    print(f"{'DRY RUN' if dry_run else 'DONE'}")
    print(f"{'=' * 50}")
    print(f"\nVault: {vault_dir}/")
    print(f"Notes generated: {total}")
    print(f"With extracted entities: {entity_stats['with_entities']}")
    print(f"Categories: {len(category_counts)}")
    print(f"\nTop extracted entities:")

    # Count total entities by type
    type_counts = Counter()
    for entities in all_entities.values():
        for key, values in entities.items():
            if key.startswith('_'):
                continue
            type_counts[key] += len(values)

    for key, count in type_counts.most_common():
        print(f"  {key}: {count}")

    if not dry_run:
        # Verify vault structure
        print(f"\nVault structure:")
        for d in sorted(vault_dir.iterdir()):
            if d.is_dir():
                count = sum(1 for _ in d.rglob('*.md'))
                print(f"  {d.name}/: {count} files")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backfill Obsidian vault from existing screenshots')
    parser.add_argument('--organized-dir', '-d', default='Organized')
    parser.add_argument('--dry-run', '-n', action='store_true')
    args = parser.parse_args()

    main(args.organized_dir, dry_run=args.dry_run)
