#!/usr/bin/env python3
"""
Detailed Screenshot Classifier — reads all OCR text files and produces a
comprehensive per-file classification report in Markdown.

Categories are granular and specific to real content observed in the data.
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


# Each rule: (category, patterns_with_weights)
# Higher weight = stronger signal. A match scores its weight.
# Category with highest total score wins.
RULES = [
    # ── Google Search ──
    ('Google Search', [
        (10, r'AlMode.{0,5}All Images'),
        (10, r'Al Overview'),
        (8, r'Q\..{3,50}\s+G\s*@'),  # Q. <search term> G @
        (8, r'All Images (Shopping|Videos|News)'),
        (6, r'Google\s+Q\.'),
        (5, r'Search instead for'),
        (5, r'Images may be subject to copyright'),
    ]),

    # ── Google Maps / Apple Maps / Navigation ──
    ('Google Maps / Navigation', [
        (10, r'(Directions|DIRECTIONS)\s'),
        (8, r'\d+\s*(mi|miles?|km)\s+\d+\s*(min|hr|hours?)'),
        (8, r'(ETA|arrival|Arrive)\s*:?\s*\d'),
        (8, r'(Navigate|Route\s+overview)'),
        (6, r'(Google Maps|Apple Maps|maps\.google|maps\.apple)'),
        (5, r'(State Route|Interstate|Highway|Freeway)\s+\d'),
        (5, r'(exit|Exit)\s+\d'),
        (5, r'Economy Seat|Plane Changes|Flight'),
    ]),

    # ── Stocks / Crypto / Trading ──
    ('Stocks / Crypto / Finance', [
        (10, r'\$[A-Z]{2,5}\b'),  # stock tickers like $AAPL
        (8, r'(Mkt Cap|Market Cap|Liquidity)'),
        (8, r'(stock|shares?|portfolio|dividend|earnings)'),
        (8, r'(bitcoin|ethereum|crypto|token|presale|defi|solana|SOL)'),
        (6, r'(bull|bear)\s*(market|run|ish)'),
        (5, r'(trading|trader|invest(ing|ment|or))'),
        (5, r'(hedge fund|capital|equity|yield|bond)'),
        (5, r'(buy|sell)\s+(stock|share|position)'),
        (4, r'(Dow|S&P|NASDAQ|NYSE)'),
    ]),

    # ── Receipts / Purchases / Shopping ──
    ('Receipts / Purchases', [
        (10, r'(CHECKOUT|checkout|Order\s+(placed|confirmed))'),
        (8, r'\$\d+\.\d{2}.{0,20}(afterpay|Klarna|payment)'),
        (8, r'(receipt|invoice|order\s+total)'),
        (6, r'(Add to Cart|Shop now|Buy now)'),
        (5, r'\$\d+\.\d{2}'),
        (4, r'(shipping|delivery fee|tax|subtotal)'),
        (4, r'(Salomon|Nike|shoe|sneaker|kickscrew)'),
    ]),

    # ── Instagram Feed / Posts ──
    ('Instagram Post', [
        (6, r'(Liked by|likes)\s+\w'),
        (5, r'View all \d+ comment'),
        (4, r'Suggested for you'),
        (3, r'@\w{3,}'),
        (3, r'Follow\s+(eee|see|vee|\.\.\.)'),
        (2, r'A\s+Q\s+[GCS©]\)'),  # bottom nav bar pattern
        (2, r'(hours?|minutes?|days?)\s+ago'),
    ]),

    # ── Instagram Profile ──
    ('Instagram Profile', [
        (10, r'\d+\s*posts?\s+\d+\s*followers?\s+\d+\s*following'),
        (8, r'(Edit [Pp]rofile|Share [Pp]rofile)'),
        (8, r'Followed by \w+ and [\d,.]+[Kk]? others'),
        (6, r'(Posts|Reels|Tagged)\s+(Posts|Reels|Tagged)'),
    ]),

    # ── Instagram Stories ──
    ('Instagram Story', [
        (10, r'Your story\s+\w'),
        (8, r'Add to your story'),
        (6, r'Send message\.\.\.'),
        (3, r'Close Friends'),
    ]),

    # ── Instagram DMs / Messages ──
    ('Instagram DM', [
        (10, r'@\)?\s*Message\s+\w'),
        (8, r'Send message\.\.\.\s*CO'),
        (8, r'vanish\s*mode'),
    ]),

    # ── Twitter / X ──
    ('Twitter / X', [
        (10, r'(Post your reply|Repost|Quote\s*Tweet)'),
        (8, r'@\w+\s*:?\s*\d+[mhd]'),
        (6, r'(x\.com|twitter\.com)'),
        (5, r'(tl\)?\s*\d+\s*©\s*[\d.]+[Kk]?\s*il)'),  # engagement metrics pattern
        (4, r'(Retweet|Repost|Bookmark)'),
    ]),

    # ── TikTok ──
    ('TikTok', [
        (10, r'(tiktok|TikTok)'),
        (8, r'(Home\s+Friends\s+Inbox\s+Profile)'),
        (6, r'(Search\s*-\s*.{3,30}\s*>)'),  # TikTok search bar
        (6, r'(For\s*You|FYP)'),
        (5, r'(Watch full reel)'),
        (4, r'(Creator earns commission)'),
    ]),

    # ── Facebook ──
    ('Facebook', [
        (10, r'(facebook|Facebook)\s'),
        (8, r'(Like\s+Q?\s*Comment.{0,10}Share)'),
        (6, r'(fb\.com|Home Video Marketplace)'),
        (6, r'People you may know'),
        (5, r'Comment as \w'),
    ]),

    # ── Reddit ──
    ('Reddit', [
        (10, r'r/\w{3,}'),
        (8, r'(upvote|downvote|karma)'),
        (6, r'(subreddit|reddit\.com)'),
    ]),

    # ── WhatsApp ──
    ('WhatsApp', [
        (10, r'(WhatsApp|whatsapp)'),
        (8, r'end-to-end encrypted'),
        (6, r'(online|last seen \w+ ago)'),
    ]),

    # ── iMessage / SMS ──
    ('iMessage / SMS', [
        (10, r'(iMessage|iMESSAGE)'),
        (8, r'(Delivered|Read\s+\d{1,2}:\d{2})'),
        (5, r'(Text Message|SMS)'),
    ]),

    # ── Group Chat / Messaging ──
    ('Group Chat', [
        (8, r'(joined using this group|requested to join)'),
        (6, r'(UNREAD MESSAGE|group.{0,10}invite link)'),
        (5, r'(\d+:\d{2}\s*(AM|PM)\s+~)'),  # timestamp + ~ sender pattern
    ]),

    # ── ChatGPT / AI ──
    ('ChatGPT / AI', [
        (10, r'(ChatGPT|chatgpt)'),
        (8, r'(GPT-[34]|OpenAI|Claude)'),
        (6, r'(\.claude/|agents/|SKILL\.md)'),
        (5, r'(AI|Al)\s*(assistant|model|prompt|engineer)'),
    ]),

    # ── Email / Gmail ──
    ('Email / Gmail', [
        (10, r'(Gmail|gmail)'),
        (8, r'(Inbox|inbox).{0,20}(starred|sent|draft)'),
        (5, r'(Subject:|From:|Reply to)'),
    ]),

    # ── Airbnb / Lodging Reviews ──
    ('Airbnb / Reviews', [
        (10, r'(Overall rating|Public review)'),
        (8, r'(Glamping|glamping|campsite|Airbnb)'),
        (6, r'(Check-in|Responsive host|stars?\s*\d)'),
        (5, r'(review of your place|reservation)'),
    ]),

    # ── Real Estate / Property ──
    ('Real Estate', [
        (8, r'(real estate|property|auction|acreage|acres)'),
        (6, r'(mortgage|foreclosure|MLS|listing)'),
        (5, r'(bedroom|bathroom|sq\s*ft|square feet)'),
    ]),

    # ── Music / Spotify / Podcasts ──
    ('Music / Podcasts', [
        (10, r'(Spotify|spotify|Apple Music)'),
        (8, r'(Now [Pp]laying|[Pp]laying from)'),
        (6, r'(podcast|Episode\s+\d)'),
        (3, r'[fF][12i]\s+[\w\s]+-\s+[\w\s]+'),  # fi ArtistName - SongName pattern
    ]),

    # ── Dating Apps ──
    ('Dating Apps', [
        (10, r'(Tinder|Hinge|Bumble|match\.com)'),
        (8, r'(swipe|Super Like|rose|it.s a match)'),
        (5, r'(Dating|Notifications\s+Menu)'),
    ]),

    # ── Food / Restaurant / Delivery ──
    ('Food / Restaurants', [
        (10, r'(UberEats|DoorDash|Grubhub|Postmates)'),
        (8, r'(reservation|Omakase|dine.in|restaurant)'),
        (6, r'(menu|appetizer|entree|dessert)'),
        (5, r'(delivery fee|service fee|tip\b)'),
    ]),

    # ── Travel / Flights ──
    ('Travel / Flights', [
        (8, r'(flight|boarding pass|airport|airline)'),
        (8, r'(Economy Seat|Gate\s+\w\d|Terminal\s+\d)'),
        (6, r'(hotel|hostel|resort|check.in|check.out)'),
        (5, r'(Copenhagen|Bora Bora|Venice|itinerary)'),
    ]),

    # ── Inspirational / Quotes ──
    ('Inspirational / Quotes', [
        (5, r'(type .yes. if you agree)'),
        (4, r'(never give up|keep going|you can do)'),
        (3, r'(growth|healing|self.?worth|self.?love|mindset)'),
        (3, r'(relationship|partner|love|trust|respect).{5,60}(relationship|partner|love|trust|respect)'),
        (2, r'(toxic|boundaries|ego|peace|energy|alignment)'),
        (2, r'(inspire|motivat|courage|strength|wisdom)'),
    ]),

    # ── Astrology / Spirituality ──
    ('Astrology / Spirituality', [
        (10, r'(horoscope|birth chart|natal chart|zodiac)'),
        (8, r'(Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|Sagittarius|Capricorn|Aquarius|Pisces)\s*:'),
        (6, r'(Moon in|Venus in|Mercury in|Saturn in)'),
        (5, r'(Nakshatra|Ascendant|planetary)'),
        (4, r'(chakra|spiritual|ceremony|sacred|shaman)'),
    ]),

    # ── Event Festival ──
    ('Event Festival', [
        (10, r'(Event Festival|Event Festival|event attendee|festival grounds)'),
        (8, r'(Black Rock|Ticket Aid|BRC)'),
        (5, r'(Burn|camp|radical self)'),
    ]),

    # ── Art / Architecture / Design ──
    ('Art / Design', [
        (6, r'(Your Company|yourcompany|YourCompany)'),
        (5, r'(sculpture|installation|gallery|exhibit)'),
        (4, r'(architect|design|Illustrator|Adobe)'),
        (3, r'(museum|curator|contemporary art)'),
    ]),

    # ── Legal / Court Records ──
    ('Legal / Government', [
        (10, r'(CHARGE CODE|BOND AMOUNT|CHARGE DESCRIPTION)'),
        (8, r'(Department of|Internal Revenue|IRS|Tax Exempt)'),
        (6, r'(court|arrest|felony|misdemeanor|probation)'),
        (5, r'(license|permit|certificate)'),
    ]),

    # ── Cannabis / Dispensary ──
    ('Cannabis', [
        (10, r'(dispensary|cannabis|THC|CBD|sativa|indica)'),
        (8, r'(strain|flower|edible|concentrate)'),
        (5, r'(half ounce|\d+\.?\d*%\s*THC)'),
    ]),

    # ── News / Current Events ──
    ('News', [
        (6, r'(BREAKING|EXCLUSIVE|breaking news)'),
        (5, r'(news3lv|CNN|NBC|ABC|MSNBC|Fox News)'),
        (4, r'(monolith|election|president|congress)'),
    ]),

    # ── Vehicles / Auto ──
    ('Vehicles / Auto', [
        (8, r'(SHERP|UTV|off-road|4x4)'),
        (6, r'(truck|SUV|vehicle|wrapping|racing)'),
        (5, r'(Slate|EV|electric vehicle|Tesla)'),
    ]),

    # ── Wi-Fi / Phone Settings ──
    ('Phone Settings', [
        (10, r'(Settings\s+Wi-?Fi|Wi-Fi\s+Settings)'),
        (8, r'(Bluetooth|Cellular|Airplane Mode)'),
        (6, r'(Ask to Join Networks|Auto-Join Hotspot)'),
    ]),

    # ── Domain Names / Web ──
    ('Domain Names', [
        (10, r'(Expires on|domain|registrar|WHOIS)'),
        (8, r'\w+\.\w+\s+Expires'),
    ]),

    # ── Memes / Humor ──
    ('Meme / Humor', [
        (6, r'(meme|funny|lol|lmao|bruh|bro)'),
        (4, r'(challenges? you|dare you)'),
    ]),

    # ── Facebook Messenger ──
    ('Facebook Messenger', [
        (10, r'(Messenger|messenger).{0,20}(facebook|mobile\.facebook)'),
        (8, r'mobile\.facebook\.com'),
        (6, r'(Chat Heads|Messenger Rooms)'),  # common Messenger UI elements
    ]),

    # ── Drone / Camera Footage ──
    ('Drone / Camera', [
        (10, r'(DJI|dji)[\s_]'),
        (6, r'(drone|aerial|GoPro)'),
    ]),

    # ── Sponsorship / Business ──
    ('Business / Sponsorship', [
        (8, r'(SPONSORSHIP|sponsorship|partnership)'),
        (6, r'(COMPREHENSIVE REPORT|proposal|pitch deck)'),
        (5, r'(billboard|renewal|invoice|contract)'),
    ]),

    # ── Festival / Events ──
    ('Festival / Events', [
        (6, r'(festival|concert|garbicz|coachella|sxsw)'),
        (5, r'(lineup|stage|tent|camp|dome)'),
    ]),
]

# ── Fallback patterns for short/ambiguous text ──
FALLBACK_RULES = [
    # Short Instagram indicators
    ('Instagram Post', [
        (5, r'^.{0,50}(Add comment)'),
        (4, r'(Liked by|Explore|Follow)'),
        (3, r'@\w{3,}'),
    ]),
    ('Instagram DM', [
        (6, r'(Send message|send message)'),
        (5, r'Message \w+\.\.\.'),
    ]),
    ('Instagram Story', [
        (8, r'Your story'),
        (5, r'Close Friends'),
    ]),
    ('TikTok', [
        (5, r'(Home\s+Friends.{0,10}Profile|Home\s+.*Profile)'),
        (4, r'Search\s*-'),
    ]),
    ('Facebook', [
        (5, r'(facebook\.com|d>\s*Like)'),
    ]),
]


def classify(text):
    """Classify text into the best-matching category with confidence."""
    if not text or len(text.strip()) < 5:
        return 'Unreadable', 0, {}

    text_lower = text.lower()
    scores = Counter()
    matched = defaultdict(list)

    for category, patterns in RULES:
        for weight, pattern in patterns:
            try:
                hits = re.findall(pattern, text_lower if weight < 8 else text)
            except re.error:
                hits = re.findall(pattern, text_lower)
            if not hits:
                # Try case-insensitive on high-weight too
                try:
                    hits = re.findall(pattern, text_lower)
                except re.error:
                    continue
            if hits:
                scores[category] += len(hits) * weight
                matched[category].append(pattern)

    # If no strong match, try fallback rules
    if not scores or scores.most_common(1)[0][1] < 3:
        for category, patterns in FALLBACK_RULES:
            for weight, pattern in patterns:
                try:
                    hits = re.findall(pattern, text_lower)
                except re.error:
                    continue
                if hits:
                    scores[category] += len(hits) * weight

    if not scores:
        return 'Uncategorized', 0, {}

    top = scores.most_common(3)
    winner = top[0][0]
    score = top[0][1]

    # Return top category, score, and runner-ups
    return winner, score, {cat: s for cat, s in top}


def main(organized_dir='Organized', output=None):
    organized = Path(organized_dir)
    processed = organized / 'Screenshots_Processed'

    if not processed.exists():
        print(f"Error: {processed} not found")
        sys.exit(1)

    if output is None:
        output = organized / 'screenshot_classification_report.md'
    else:
        output = Path(output)

    # Read all text files
    entries = []
    for cat_dir in sorted(processed.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith('.'):
            continue
        for month_dir in sorted(cat_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for txt in sorted(month_dir.glob('*.txt')):
                text = txt.read_text(encoding='utf-8', errors='ignore')
                img_name = txt.stem  # filename without .txt
                entries.append({
                    'file': img_name,
                    'month': month_dir.name,
                    'old_category': cat_dir.name,
                    'text': text,
                })

    total = len(entries)
    print(f"Classifying {total} screenshots...\n")

    # Classify all
    category_counts = Counter()
    by_category = defaultdict(list)

    for entry in entries:
        cat, score, alt = classify(entry['text'])
        entry['category'] = cat
        entry['score'] = score
        entry['alternatives'] = alt
        category_counts[cat] += 1
        by_category[cat].append(entry)

    # Build report
    lines = []
    lines.append("# Screenshot Classification Report\n\n")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    lines.append(f"**Total screenshots**: {total}\n\n")

    # Summary table
    lines.append("## Summary\n\n")
    lines.append("| Category | Count | % |\n")
    lines.append("|---|---:|---:|\n")
    for cat, count in category_counts.most_common():
        pct = count * 100 / total
        lines.append(f"| {cat} | {count} | {pct:.1f}% |\n")
    lines.append(f"| **TOTAL** | **{total}** | **100%** |\n\n")

    # Monthly heatmap for top categories
    top_cats = [c for c, _ in category_counts.most_common(10)]
    monthly = defaultdict(Counter)
    for entry in entries:
        monthly[entry['month']][entry['category']] += 1

    months = sorted(monthly.keys())
    lines.append("## Monthly Distribution (Top 10 Categories)\n\n")
    header = "| Month | " + " | ".join(top_cats) + " | Total |\n"
    lines.append(header)
    lines.append("|---" * (len(top_cats) + 2) + "|\n")
    for month in months:
        row = f"| {month} "
        total_m = 0
        for cat in top_cats:
            val = monthly[month].get(cat, 0)
            row += f"| {val} "
            total_m += val
        other = sum(monthly[month].values()) - total_m
        row += f"| {total_m + other} |\n"
        lines.append(row)
    lines.append("\n")

    # Google Search section — extract search terms
    if 'Google Search' in by_category:
        lines.append("## Google Searches\n\n")
        for entry in sorted(by_category['Google Search'], key=lambda x: x['month']):
            # Try to extract the search query
            m = re.search(r'Q\.?\s*(.{3,60}?)\s*(G\s*@|&|All\s+Images)', entry['text'])
            query = m.group(1).strip() if m else '(could not extract)'
            lines.append(f"- **{entry['month']}** `{entry['file']}` — *{query}*\n")
        lines.append("\n")

    # Stocks section — extract tickers
    if 'Stocks / Crypto / Finance' in by_category:
        lines.append("## Stocks / Crypto Mentions\n\n")
        all_tickers = Counter()
        for entry in by_category['Stocks / Crypto / Finance']:
            tickers = re.findall(r'\$([A-Z]{2,5})\b', entry['text'])
            for t in tickers:
                all_tickers[t] += 1
        if all_tickers:
            lines.append("**Tickers mentioned:**\n")
            for ticker, count in all_tickers.most_common(30):
                lines.append(f"- ${ticker}: {count}x\n")
            lines.append("\n")

        for entry in sorted(by_category['Stocks / Crypto / Finance'], key=lambda x: x['month']):
            tickers = re.findall(r'\$[A-Z]{2,5}\b', entry['text'])
            preview = entry['text'][:150].replace('\n', ' ')
            lines.append(f"- **{entry['month']}** `{entry['file']}` — {' '.join(tickers) if tickers else ''} {preview}...\n")
        lines.append("\n")

    # Per-category detailed listings
    lines.append("---\n\n## All Screenshots by Category\n\n")

    for cat, items in sorted(by_category.items(), key=lambda x: -len(x[1])):
        lines.append(f"### {cat} ({len(items)})\n\n")
        lines.append(f"<details><summary>View all {len(items)} entries</summary>\n\n")
        lines.append("| File | Month | Preview |\n")
        lines.append("|---|---|---|\n")
        for entry in sorted(items, key=lambda x: (x['month'], x['file'])):
            preview = entry['text'][:120].replace('\n', ' ').replace('|', '/').strip()
            if len(entry['text']) > 120:
                preview += '...'
            lines.append(f"| `{entry['file']}` | {entry['month']} | {preview} |\n")
        lines.append(f"\n</details>\n\n")

    # Write
    output.write_text(''.join(lines), encoding='utf-8')
    print(f"Report saved to: {output}")
    print(f"\nCategory breakdown:")
    for cat, count in category_counts.most_common():
        print(f"  {cat:30}: {count:5}")

    # Also save as JSON for programmatic use
    json_out = output.with_suffix('.json')
    json_data = [{
        'file': e['file'],
        'month': e['month'],
        'category': e['category'],
        'score': e['score'],
        'text_preview': e['text'][:200],
    } for e in entries]
    with open(json_out, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"JSON data saved to: {json_out}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--organized-dir', '-d', default='Organized')
    parser.add_argument('--output', '-o', default=None)
    args = parser.parse_args()
    main(args.organized_dir, args.output)
