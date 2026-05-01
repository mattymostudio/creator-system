#!/usr/bin/env python3
"""
Screenshot Content Extractor — OCRs screenshots and classifies them by content type.

Categories:
  - Messages      (iMessage, WhatsApp, Telegram, SMS)
  - Social_Media  (Instagram, Twitter/X, TikTok, Facebook, Reddit)
  - Web_Articles  (Safari, Chrome browser content)
  - Maps          (Apple Maps, Google Maps)
  - Receipts      (purchase confirmations, transaction records)
  - Settings      (iOS Settings, app settings)
  - Notes         (Apple Notes, other note apps)
  - Other         (anything else)

Output:
  Organized/Screenshots_Processed/
  ├── Messages/
  │   ├── 2025-07/
  │   │   ├── XXXX.PNG
  │   │   └── XXXX.txt    (extracted text)
  │   └── ...
  ├── Social_Media/
  └── ...

Usage:
    python3 extract_screenshots.py [--organized-dir <dir>] [--dry-run] [--limit N]
"""

import argparse
import json
import logging
import os
import re
import sys
import warnings
from collections import Counter
from pathlib import Path

logging.getLogger('exifread').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

import pytesseract
from PIL import Image


# Classification patterns — keywords/phrases that indicate content type
CLASSIFICATION_RULES = [
    ('Messages', [
        r'imessage', r'delivered', r'read \d{1,2}:\d{2}',
        r'message\b', r'(send|type) (a )?message',
        r'whatsapp', r'telegram', r'signal',
        r'tapback', r'iMessage',
        r'\b(today|yesterday) \d{1,2}:\d{2}\s*(am|pm)',
    ]),
    ('Social_Media', [
        r'instagram', r'@\w+', r'follow(ers|ing)',
        r'(like|comment|share|retweet|repost)',
        r'twitter|tweet', r'\bx\.com\b',
        r'tiktok', r'reddit', r'r/',
        r'facebook', r'fb\.com',
        r'snapchat', r'snap',
        r'linkedin', r'youtube',
        r'(stories|reels|posts)',
        r'(upvote|downvote)',
    ]),
    ('Receipts', [
        r'(order|receipt|invoice|transaction)',
        r'(total|subtotal|tax|paid|amount)',
        r'\$\d+\.\d{2}', r'(credit|debit) card',
        r'(confirmation|tracking)\s*(number|#)',
        r'(shipped|delivered|estimated delivery)',
        r'(visa|mastercard|amex|paypal|venmo|zelle|apple pay)',
        r'(purchase|payment)',
    ]),
    ('Maps', [
        r'(directions|navigate|route)',
        r'(miles?|km|min(utes?)?) (away|left)',
        r'(apple|google) maps',
        r'(arrive|arrival|eta|depart)',
        r'(highway|interstate|freeway|exit)',
    ]),
    ('Web_Articles', [
        r'(safari|chrome|firefox|brave)',
        r'(aA|aa)\s*\|\s*',  # Safari URL bar
        r'https?://', r'www\.',
        r'(read more|continue reading|subscribe)',
        r'(article|blog|news)',
    ]),
    ('Settings', [
        r'\bsettings?\b.*\b(general|display|privacy|notifications)',
        r'(toggle|switch|slider)',
        r'(wi-?fi|bluetooth|cellular|airplane)',
        r'(do not disturb|focus|screen time)',
    ]),
    ('Notes', [
        r'\bnotes?\b', r'(checklist|to-?do)',
        r'(bullet|numbered list)',
    ]),
]


def extract_text(filepath):
    """Extract text from a screenshot using OCR."""
    try:
        img = Image.open(filepath)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        text = pytesseract.image_to_string(img, lang='eng')
        return text.strip()
    except Exception as e:
        return None


def classify_screenshot(text):
    """Classify screenshot content based on extracted text."""
    if not text or len(text.strip()) < 10:
        return 'Other'

    text_lower = text.lower()

    scores = Counter()
    for category, patterns in CLASSIFICATION_RULES:
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            scores[category] += len(matches)

    if not scores or scores.most_common(1)[0][1] == 0:
        return 'Other'

    return scores.most_common(1)[0][0]


def process_screenshots(organized_dir, dry_run=False, limit=None):
    """Process all screenshots: OCR and classify."""
    organized = Path(organized_dir)
    screenshots_dir = organized / 'Screenshots'
    output_dir = organized / 'Screenshots_Processed'

    if not screenshots_dir.exists():
        print(f"Error: {screenshots_dir} not found")
        sys.exit(1)

    # Gather all screenshot files
    all_files = []
    for month_dir in sorted(screenshots_dir.iterdir()):
        if not month_dir.is_dir():
            continue
        for f in sorted(month_dir.iterdir()):
            if f.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
                all_files.append((f, month_dir.name))

    if limit:
        all_files = all_files[:limit]

    total = len(all_files)
    print(f"Processing {total} screenshots...\n")

    stats = Counter()
    results = []

    # Build set of already-processed files (by checking existing .txt files)
    already_done = set()
    if output_dir.exists():
        for cat_dir in output_dir.iterdir():
            if not cat_dir.is_dir() or cat_dir.name.startswith('.'):
                continue
            for month_dir in cat_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                for txt in month_dir.glob('*.txt'):
                    already_done.add(txt.stem)

    skipped = len(already_done)
    if skipped:
        print(f"Skipping {skipped} already-processed screenshots\n", flush=True)

    for i, (filepath, month) in enumerate(all_files, 1):
        if i % 50 == 0 or i == total:
            print(f"  Processing: {i}/{total} ({i*100//total}%)", flush=True)

        # Skip already-processed
        if filepath.stem in already_done:
            stats['skipped'] += 1
            continue

        # OCR
        text = extract_text(str(filepath))
        if text is None:
            stats['errors'] += 1
            continue

        # Classify
        category = classify_screenshot(text)
        stats[category] += 1

        results.append({
            'file': filepath.name,
            'month': month,
            'category': category,
            'text_length': len(text),
            'text_preview': text[:200].replace('\n', ' '),
        })

        if not dry_run:
            dest_dir = output_dir / category / month
            dest_dir.mkdir(parents=True, exist_ok=True)

            dest_img = dest_dir / filepath.name
            if not dest_img.exists():
                os.symlink(filepath.resolve(), dest_img)

            # Save extracted text
            txt_name = filepath.stem + '.txt'
            dest_txt = dest_dir / txt_name
            if text:
                dest_txt.write_text(text, encoding='utf-8')

    # Summary
    print(f"\n{'=' * 50}")
    print(f"{'DRY RUN' if dry_run else 'DONE'}")
    print(f"{'=' * 50}")
    print(f"\nScreenshot content types:")
    for cat, count in stats.most_common():
        if cat != 'errors':
            print(f"  {cat:15}: {count:5}")
    if stats['errors']:
        print(f"  {'Errors':15}: {stats['errors']:5}")
    print(f"  {'TOTAL':15}: {total:5}")

    # Save classification report
    if not dry_run:
        report_path = output_dir / 'classification_report.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed report saved to: {report_path}")

    return stats


# Need shutil for copying
import shutil

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract and classify screenshot content')
    parser.add_argument('--organized-dir', '-d', default='Organized',
                        help='Path to Organized directory')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show classification without copying')
    parser.add_argument('--limit', '-l', type=int, default=None,
                        help='Process only first N screenshots (for testing)')
    args = parser.parse_args()

    process_screenshots(args.organized_dir, dry_run=args.dry_run, limit=args.limit)
