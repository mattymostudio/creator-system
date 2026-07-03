#!/usr/bin/env python3
"""
Obsidian Builder — generates Obsidian-compatible Markdown notes from
classified screenshots with extracted entities.
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from entity_extractor import extract_entities, has_any_entities


def sanitize_category(category):
    """Convert category name to Obsidian-safe filename."""
    return category.replace('/', '-').replace('\\', '-').strip()


def slugify_tag(text):
    """Convert text to a valid Obsidian tag."""
    slug = re.sub(r'[^a-zA-Z0-9_-]', '-', text.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def yaml_list(items):
    """Format a list for YAML frontmatter."""
    if not items:
        return '[]'
    escaped = []
    for item in items:
        item = str(item).replace('"', '\\"')
        escaped.append(f'"{item}"')
    return '[' + ', '.join(escaped) + ']'


def build_note(file_stem, month, category, score, ocr_text, entities, image_rel_path):
    """Build a complete Obsidian Markdown note."""
    safe_cat = sanitize_category(category)
    tag_cat = slugify_tag(category)

    # Tags
    tags = ['screenshot', tag_cat]
    if entities.get('tickers'):
        tags.append('stocks')
    if entities.get('todos'):
        tags.append('action-item')
    if entities.get('prices'):
        tags.append('money')
    if entities.get('contacts'):
        tags.append('contact')

    # YAML frontmatter
    lines = ['---']
    lines.append(f'file: "{file_stem}"')
    lines.append(f'category: "{category}"')
    lines.append(f'month: "{month}"')
    lines.append(f'score: {score}')
    lines.append(f'tags: [{", ".join(tags)}]')
    lines.append(f'phones: {yaml_list(entities.get("phones", []))}')
    lines.append(f'emails: {yaml_list(entities.get("emails", []))}')
    lines.append(f'urls: {yaml_list(entities.get("urls", []))}')
    lines.append(f'handles: {yaml_list(entities.get("handles", []))}')
    lines.append(f'dates_mentioned: {yaml_list(entities.get("dates_mentioned", []))}')
    lines.append(f'prices: {yaml_list(entities.get("prices", []))}')
    lines.append(f'addresses: {yaml_list(entities.get("addresses", []))}')
    lines.append(f'tickers: {yaml_list(entities.get("tickers", []))}')
    lines.append(f'todos: {yaml_list(entities.get("todos", []))}')
    lines.append(f'contacts: {yaml_list(entities.get("contacts", []))}')
    lines.append(f'quotes: {yaml_list(entities.get("quotes", []))}')
    lines.append(f'products: {yaml_list(entities.get("products", []))}')
    lines.append(f'services: {yaml_list(entities.get("services", []))}')
    lines.append(f'people: {yaml_list(entities.get("people", []))}')
    lines.append('---')
    lines.append('')

    # Title
    lines.append(f'# {file_stem} — {category}')
    lines.append('')
    lines.append(f'**Category**: [[Categories/{safe_cat}]]')
    lines.append(f'**Captured**: {month}')
    lines.append('')

    # Extracted data section (only show non-empty)
    entity_sections = []
    for key, label in [
        ('products', 'Products'),
        ('services', 'Services / Businesses'),
        ('people', 'People'),
        ('prices', 'Prices'),
        ('contacts', 'Contacts'),
        ('phones', 'Phone Numbers'),
        ('emails', 'Emails'),
        ('urls', 'URLs'),
        ('handles', 'Social Handles'),
        ('addresses', 'Addresses'),
        ('dates_mentioned', 'Dates'),
        ('tickers', 'Stock Tickers'),
        ('todos', 'Action Items'),
        ('quotes', 'Quotes'),
    ]:
        values = entities.get(key, [])
        if values:
            entity_sections.append((label, values))

    if entity_sections:
        lines.append('## Extracted Data')
        lines.append('')
        for label, values in entity_sections:
            if len(values) == 1:
                lines.append(f'- **{label}**: {values[0]}')
            else:
                lines.append(f'**{label}**:')
                for v in values:
                    lines.append(f'- {v}')
            lines.append('')

    # OCR text
    if ocr_text and ocr_text.strip():
        text_clean = ocr_text.strip()
        if len(text_clean) > 500:
            preview = text_clean[:500]
            lines.append('## OCR Text')
            lines.append('')
            for line in preview.split('\n'):
                lines.append(f'> {line}')
            lines.append('')
            lines.append('<details><summary>Full text</summary>')
            lines.append('')
            for line in text_clean.split('\n'):
                lines.append(f'> {line}')
            lines.append('')
            lines.append('</details>')
        else:
            lines.append('## OCR Text')
            lines.append('')
            for line in text_clean.split('\n'):
                lines.append(f'> {line}')
        lines.append('')

    # Screenshot image
    if image_rel_path:
        lines.append('## Screenshot')
        lines.append(f'![[{image_rel_path}]]')
        lines.append('')

    return '\n'.join(lines)


def write_note(vault_dir, file_stem, month, content):
    """Write a note to the vault."""
    note_dir = vault_dir / 'Screenshots' / month
    note_dir.mkdir(parents=True, exist_ok=True)
    note_path = note_dir / f'{file_stem}.md'
    note_path.write_text(content, encoding='utf-8')
    return note_path


def create_image_symlink(vault_dir, month, file_stem, screenshots_dir):
    """Create a symlink in _attachments/ pointing to the original image."""
    attach_dir = vault_dir / '_attachments' / month
    attach_dir.mkdir(parents=True, exist_ok=True)

    # Find the original image
    source_dir = screenshots_dir / month
    if not source_dir.exists():
        return None

    # Try common extensions
    for ext in ['.PNG', '.png', '.JPG', '.jpg', '.JPEG', '.jpeg']:
        source = source_dir / f'{file_stem}{ext}'
        if source.exists():
            link_path = attach_dir / f'{file_stem}{ext}'
            if not link_path.exists():
                os.symlink(source.resolve(), link_path)
            return f'_attachments/{month}/{file_stem}{ext}'

    return None


def build_category_moc(vault_dir, category, entries):
    """Build a Map of Content file for a category."""
    safe_cat = sanitize_category(category)
    cat_dir = vault_dir / 'Categories'
    cat_dir.mkdir(parents=True, exist_ok=True)

    lines = ['---']
    lines.append(f'type: category-index')
    lines.append(f'category: "{category}"')
    lines.append(f'count: {len(entries)}')
    lines.append('---')
    lines.append('')
    lines.append(f'# {category} ({len(entries)})')
    lines.append('')

    # Group by month
    by_month = defaultdict(list)
    for entry in entries:
        by_month[entry['month']].append(entry)

    for month in sorted(by_month.keys()):
        lines.append(f'## {month}')
        for entry in sorted(by_month[month], key=lambda x: x['file']):
            preview = entry.get('text_preview', '')[:80].replace('\n', ' ')
            lines.append(f'- [[Screenshots/{month}/{entry["file"]}|{entry["file"]}]] — {preview}')
        lines.append('')

    moc_path = cat_dir / f'{safe_cat}.md'
    moc_path.write_text('\n'.join(lines), encoding='utf-8')


def build_daily_digest(vault_dir, date_str, entries, all_entities):
    """Build a daily digest note."""
    daily_dir = vault_dir / 'Daily'
    daily_dir.mkdir(parents=True, exist_ok=True)

    lines = ['---']
    lines.append(f'type: daily-digest')
    lines.append(f'date: "{date_str}"')
    lines.append(f'screenshot_count: {len(entries)}')
    lines.append('---')
    lines.append('')
    lines.append(f'# {date_str}')
    lines.append('')
    lines.append(f'## Screenshots ({len(entries)})')
    lines.append('')

    for entry in entries:
        cat = entry.get('category', 'Unknown')
        lines.append(f'- [[Screenshots/{entry["month"]}/{entry["file"]}|{entry["file"]}]] — {cat}')
    lines.append('')

    # Aggregate entities for the day
    day_entities = defaultdict(list)
    for entry in entries:
        ents = all_entities.get(entry['file'], {})
        for key, values in ents.items():
            for v in values:
                day_entities[key].append((v, entry['file'], entry['month']))

    if any(day_entities.values()):
        lines.append('## Extracted Today')
        lines.append('')
        for key, label in [('contacts', 'Contacts'), ('prices', 'Prices'),
                           ('todos', 'Action Items'), ('urls', 'URLs'),
                           ('tickers', 'Tickers'), ('phones', 'Phone Numbers')]:
            items = day_entities.get(key, [])
            if items:
                lines.append(f'### {label}')
                for val, file, month in items:
                    lines.append(f'- {val} (from [[Screenshots/{month}/{file}]])')
                lines.append('')

    digest_path = daily_dir / f'{date_str}.md'
    digest_path.write_text('\n'.join(lines), encoding='utf-8')


def build_entity_page(vault_dir, entity_key, label, all_entities):
    """Build an aggregated entity page (Contacts.md, Prices.md, etc.)."""
    entity_dir = vault_dir / 'Entities'
    entity_dir.mkdir(parents=True, exist_ok=True)

    # Collect all values with source notes
    items = []
    for file_stem, entities in all_entities.items():
        for value in entities.get(entity_key, []):
            items.append((value, file_stem, entities.get('_month', '')))

    lines = ['---']
    lines.append(f'type: entity-index')
    lines.append(f'entity: "{entity_key}"')
    lines.append(f'count: {len(items)}')
    lines.append('---')
    lines.append('')
    lines.append(f'# {label} ({len(items)})')
    lines.append('')

    if not items:
        lines.append('No entries yet.')
    else:
        # Group by value for dedup
        by_value = defaultdict(list)
        for val, file, month in items:
            by_value[val].append((file, month))

        for val in sorted(by_value.keys()):
            sources = by_value[val]
            if len(sources) == 1:
                f, m = sources[0]
                lines.append(f'- **{val}** — [[Screenshots/{m}/{f}]]')
            else:
                lines.append(f'- **{val}**')
                for f, m in sources[:5]:
                    lines.append(f'  - [[Screenshots/{m}/{f}]]')
                if len(sources) > 5:
                    lines.append(f'  - ...and {len(sources) - 5} more')
        lines.append('')

    page_path = entity_dir / f'{label}.md'
    page_path.write_text('\n'.join(lines), encoding='utf-8')


def build_master_index(vault_dir, total, category_counts, date_range):
    """Build the master vault index."""
    lines = ['# Screenshot Knowledge Base']
    lines.append('')
    lines.append(f'**Total**: {total} screenshots | **Range**: {date_range}')
    lines.append('')
    lines.append('## Categories')
    lines.append('')
    lines.append('| Category | Count |')
    lines.append('|---|---:|')
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        safe_cat = sanitize_category(cat)
        lines.append(f'| [[Categories/{safe_cat}|{cat}]] | {count} |')
    lines.append('')

    lines.append('## Quick Links')
    lines.append('- [[Entities/Contacts]]')
    lines.append('- [[Entities/Action Items]]')
    lines.append('- [[Entities/Prices]]')
    lines.append('- [[Entities/URLs]]')
    lines.append('- [[Entities/Stock Tickers]]')
    lines.append('- [[Entities/Phone Numbers]]')
    lines.append('- [[Entities/Addresses]]')
    lines.append('- [[Entities/Social Handles]]')
    lines.append('- [[Entities/Products]]')
    lines.append('- [[Entities/Services]]')
    lines.append('- [[Entities/People]]')
    lines.append('')

    index_path = vault_dir / '_index.md'
    index_path.write_text('\n'.join(lines), encoding='utf-8')
