#!/usr/bin/env python3
"""
Screenshot Content Report — reads OCR text from processed screenshots and
generates a comprehensive markdown report with refined content type patterns.

Refined categories:
  - Instagram_Posts       (feed posts, reels)
  - Instagram_Profiles    (profile pages, bios)
  - Instagram_Messages    (DMs, message threads)
  - Instagram_Stories     (stories, story replies)
  - WhatsApp_Chats        (WhatsApp conversations)
  - iMessage_Chats        (iMessage/SMS threads)
  - Twitter_X             (tweets, threads, profiles)
  - TikTok               (TikTok content)
  - Reddit               (Reddit posts/comments)
  - Inspirational         (quotes, motivational text)
  - Receipts_Finance      (purchases, transactions, banking)
  - Maps_Navigation       (directions, maps)
  - Web_Articles          (browser content, articles)
  - App_Settings          (settings screens)
  - Notes_Lists           (notes, to-do lists)
  - Music_Podcasts        (Spotify, Apple Music, podcast screens)
  - Dating_Apps           (Tinder, Hinge, Bumble)
  - Food_Delivery         (UberEats, DoorDash, etc.)
  - Other

Usage:
    python3 screenshot_report.py [--organized-dir <dir>] [--output report.md]
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


# Refined classification with weighted patterns
REFINED_RULES = [
    ('Instagram_Messages', 3, [
        r'instagram.*message',
        r'send\s*message.*instagram',
        r'(seen|active)\s+\d+[mh]\s+ago',
        r'vanish\s*mode',
        r'@\w+.*replied to your (story|message)',
    ]),
    ('Instagram_Profiles', 3, [
        r'\d+\s*(posts?|followers?|following)',
        r'(edit profile|share profile)',
        r'(bio|website)\s*:',
        r'www\.instagram\.com',
        r'(followed by|follows you)',
        r'message\s+follow',
    ]),
    ('Instagram_Stories', 3, [
        r'add to your story',
        r'story.*reply',
        r'seen by \d+',
        r'your story',
    ]),
    ('Instagram_Posts', 2, [
        r'instagram',
        r'@\w{3,}',
        r'(liked by|likes?)\s+\w',
        r'(view all|view more)\s+\d+\s+comment',
        r'(reels?|explore)',
        r'sponsored',
    ]),
    ('WhatsApp_Chats', 3, [
        r'whatsapp',
        r'(today|yesterday),?\s+\d{1,2}:\d{2}\s*(am|pm)',
        r'(end-to-end encrypted)',
        r'(voice|video) call',
        r'(online|last seen)',
    ]),
    ('iMessage_Chats', 3, [
        r'imessage',
        r'delivered',
        r'read\s+\d{1,2}:\d{2}',
        r'(tapback|message effect)',
        r'(text message|sms)',
    ]),
    ('Twitter_X', 3, [
        r'(twitter|tweet|retweet)',
        r'x\.com',
        r'(repost|quote\s*tweet)',
        r'(views?|impressions)\s+\d+',
        r'(bookmark|spaces)',
    ]),
    ('TikTok', 3, [
        r'tiktok',
        r'(for you|fyp)',
        r'(duet|stitch)',
    ]),
    ('Reddit', 3, [
        r'reddit',
        r'r/\w+',
        r'(upvote|downvote|karma)',
        r'(subreddit|crosspost)',
    ]),
    ('Inspirational', 2, [
        r'(believe|dream|inspire|motivat|courage|strength)',
        r'(never give up|keep going|you can)',
        r'(success|greatness|purpose|passion)',
        r'(quote|wisdom|mindset)',
        r'(life is|happiness is)',
    ]),
    ('Receipts_Finance', 3, [
        r'\$\d+\.\d{2}',
        r'(order|receipt|invoice|transaction)',
        r'(total|subtotal|tax)',
        r'(visa|mastercard|amex|paypal|venmo|zelle|apple\s*pay)',
        r'(shipped|tracking|delivery)',
        r'(bank|account|balance|transfer)',
        r'(credit|debit)\s*card',
    ]),
    ('Maps_Navigation', 3, [
        r'(directions|navigate|route)',
        r'(miles?|km|min)\s+(away|left)',
        r'(apple|google)\s*maps',
        r'(arrive|arrival|eta)',
        r'(highway|interstate|exit \d)',
    ]),
    ('Music_Podcasts', 3, [
        r'(spotify|apple music|soundcloud)',
        r'(now playing|playing from)',
        r'(podcast|episode \d)',
        r'(shuffle|repeat|queue)',
        r'(playlist|album|artist)',
    ]),
    ('Dating_Apps', 3, [
        r'(tinder|hinge|bumble|match\.com)',
        r'(swipe|super like|rose)',
        r'(it\'?s a match|matched with)',
        r'(dating|looking for)',
    ]),
    ('Food_Delivery', 3, [
        r'(ubereats|doordash|grubhub|postmates|instacart)',
        r'(order (placed|confirmed|delivered))',
        r'(delivery fee|service fee|tip)',
        r'(estimated delivery|your order)',
    ]),
    ('Web_Articles', 1, [
        r'https?://',
        r'www\.',
        r'(safari|chrome|firefox)',
        r'(read more|continue reading)',
        r'(subscribe|newsletter)',
    ]),
    ('App_Settings', 2, [
        r'settings',
        r'(wi-?fi|bluetooth|cellular|airplane)',
        r'(notifications|privacy|general)',
        r'(do not disturb|focus|screen time)',
    ]),
    ('Notes_Lists', 2, [
        r'\bnotes?\b',
        r'(checklist|to-?do|reminder)',
        r'(grocery|shopping)\s*list',
    ]),
]


def classify_refined(text):
    """Classify with refined categories and weighted scoring."""
    if not text or len(text.strip()) < 10:
        return 'Other', {}

    text_lower = text.lower()
    scores = Counter()
    matched_patterns = defaultdict(list)

    for category, weight, patterns in REFINED_RULES:
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                scores[category] += len(matches) * weight
                matched_patterns[category].append(pattern)

    if not scores or scores.most_common(1)[0][1] == 0:
        return 'Other', {}

    return scores.most_common(1)[0][0], dict(matched_patterns)


def generate_report(organized_dir, output_path=None):
    """Generate comprehensive markdown report from OCR'd screenshots."""
    organized = Path(organized_dir)
    screenshots_dir = organized / 'Screenshots'

    if output_path is None:
        output_path = organized / 'screenshot_content_report.md'
    else:
        output_path = Path(output_path)

    # Read all OCR text files from Screenshots_Processed, or OCR directly
    processed_dir = organized / 'Screenshots_Processed'

    # Gather text from processed screenshots
    all_entries = []

    # Check if we have processed text files
    if processed_dir.exists():
        for cat_dir in sorted(processed_dir.iterdir()):
            if not cat_dir.is_dir() or cat_dir.name.startswith('.'):
                continue
            for month_dir in sorted(cat_dir.iterdir()):
                if not month_dir.is_dir():
                    continue
                for txt_file in sorted(month_dir.glob('*.txt')):
                    text = txt_file.read_text(encoding='utf-8', errors='ignore')
                    img_name = txt_file.stem + '.PNG'  # or .JPG
                    all_entries.append({
                        'file': img_name,
                        'month': month_dir.name,
                        'text': text,
                        'original_category': cat_dir.name,
                    })

    if not all_entries:
        print("No processed screenshot text found. Run extract_screenshots.py first.")
        sys.exit(1)

    print(f"Analyzing {len(all_entries)} screenshots...\n")

    # Reclassify with refined rules
    by_category = defaultdict(list)
    category_counts = Counter()

    for entry in all_entries:
        category, matched = classify_refined(entry['text'])
        entry['refined_category'] = category
        entry['matched_patterns'] = matched
        by_category[category].append(entry)
        category_counts[category] += 1

    # Build markdown report
    lines = []
    lines.append("# Screenshot Content Analysis Report\n\n")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"**Total screenshots analyzed**: {len(all_entries)}\n\n")

    # Summary table
    lines.append("## Content Type Breakdown\n\n")
    lines.append("| Category | Count | % |\n")
    lines.append("|---|---|---|\n")
    for cat, count in category_counts.most_common():
        pct = count * 100 / len(all_entries)
        lines.append(f"| {cat} | {count} | {pct:.1f}% |\n")
    lines.append(f"| **TOTAL** | **{len(all_entries)}** | **100%** |\n\n")

    # Monthly trends
    lines.append("## Monthly Distribution\n\n")
    monthly = defaultdict(Counter)
    for entry in all_entries:
        monthly[entry['month']][entry['refined_category']] += 1

    months = sorted(monthly.keys())
    cats = [c for c, _ in category_counts.most_common() if c != 'Other']

    lines.append("| Month | " + " | ".join(cats) + " | Other | Total |\n")
    lines.append("|---" * (len(cats) + 3) + "|\n")
    for month in months:
        row = f"| {month} "
        total = 0
        for cat in cats:
            val = monthly[month].get(cat, 0)
            row += f"| {val} "
            total += val
        other = monthly[month].get('Other', 0)
        total += other
        row += f"| {other} | {total} |\n"
        lines.append(row)
    lines.append("\n")

    # Key patterns observed
    lines.append("## Key Patterns Observed\n\n")

    # Instagram analysis
    ig_total = (category_counts.get('Instagram_Posts', 0) +
                category_counts.get('Instagram_Profiles', 0) +
                category_counts.get('Instagram_Messages', 0) +
                category_counts.get('Instagram_Stories', 0))
    if ig_total:
        lines.append(f"### Instagram ({ig_total} total)\n")
        lines.append(f"- Posts/Feed: {category_counts.get('Instagram_Posts', 0)}\n")
        lines.append(f"- Profiles: {category_counts.get('Instagram_Profiles', 0)}\n")
        lines.append(f"- Messages/DMs: {category_counts.get('Instagram_Messages', 0)}\n")
        lines.append(f"- Stories: {category_counts.get('Instagram_Stories', 0)}\n\n")

    # Messaging
    msg_total = (category_counts.get('iMessage_Chats', 0) +
                 category_counts.get('WhatsApp_Chats', 0))
    if msg_total:
        lines.append(f"### Messaging ({msg_total} total)\n")
        lines.append(f"- iMessage: {category_counts.get('iMessage_Chats', 0)}\n")
        lines.append(f"- WhatsApp: {category_counts.get('WhatsApp_Chats', 0)}\n\n")

    if category_counts.get('Receipts_Finance'):
        lines.append(f"### Financial ({category_counts['Receipts_Finance']} screenshots)\n")
        lines.append(f"Receipts, transactions, and financial screenshots captured.\n\n")

    if category_counts.get('Inspirational'):
        lines.append(f"### Inspirational Content ({category_counts['Inspirational']} screenshots)\n")
        lines.append(f"Quotes, motivational content, and inspiration.\n\n")

    # Detailed content by category
    lines.append("---\n\n")
    lines.append("## Detailed Content by Category\n\n")

    for cat, entries in sorted(by_category.items(), key=lambda x: -len(x[1])):
        lines.append(f"### {cat} ({len(entries)} screenshots)\n\n")

        # Show text previews in collapsible sections
        lines.append(f"<details><summary>View all {len(entries)} entries</summary>\n\n")

        for entry in sorted(entries, key=lambda x: x['month']):
            text_preview = entry['text'][:300].replace('\n', ' ').strip()
            if len(entry['text']) > 300:
                text_preview += '...'
            lines.append(f"**{entry['file']}** ({entry['month']})\n")
            lines.append(f"> {text_preview}\n\n")

        lines.append("</details>\n\n")

    # Write report
    output_path.write_text(''.join(lines), encoding='utf-8')
    print(f"Report saved to: {output_path}")
    print(f"\nCategory breakdown:")
    for cat, count in category_counts.most_common():
        print(f"  {cat:25}: {count:5}")

    return category_counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate screenshot content report')
    parser.add_argument('--organized-dir', '-d', default='Organized',
                        help='Path to Organized directory')
    parser.add_argument('--output', '-o', default=None,
                        help='Output markdown file path')
    args = parser.parse_args()

    generate_report(args.organized_dir, output_path=args.output)
