#!/usr/bin/env python3
"""
Canonicalize & Clean — takes raw extracted entities and produces clean,
deduplicated, properly categorized first-pass tables.

Fixes:
  1. Removes UI fragments, geographic noise, generic phrases
  2. Merges duplicate variants (Jane Doe / Jane Doe / @yourhandle)
  3. Reclassifies orgs-as-people (Event Festival → org, Partner Org → org)
  4. Scores on 25-point scale per the operating system spec
  5. Outputs clean markdown tables ready for manual review
"""

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from entity_extractor import extract_entities

# ══════════════════════════════════════════════════
# NOISE LISTS — entities that are never real people/products/services
# ══════════════════════════════════════════════════

PEOPLE_BLOCKLIST = {
    # UI fragments
    'report junk', 'new messages', 'new message', 'people you', 'following followers',
    'processing fee', 'reels friends', 'activity share', 'open call', 'call website',
    'text message', 'learn more', 'view all', 'send message', 'add comment',
    'see all', 'suggested for you', 'post your reply', 'posts followers',
    'photos reviews', 'reviews photos', 'edit select', 'instagram suggested',
    'instagram', 'activity facebook', 'follow', 'comment', 'share', 'reply',
    'worldwide shipping', 'shipping container', 'message', 'following',
    'read more', 'show more', 'load more', 'swipe up', 'tap here',
    'sponsored', 'advertisement', 'ad', 'promoted',
    # Geographic
    'united states', 'united kingdom', 'united economy', 'san francisco',
    'your state', 'new york', 'los angeles', 'mexico city', 'anothertown',
    'black rock', 'rock city', 'palm springs',
    # Generic phrases
    'the most', 'the art', 'the great', 'the future', 'the best',
    'the real', 'the first', 'the last', 'the new', 'the old',
}

SERVICE_BLOCKLIST = {
    'approved', 'add to cart', 'checkout', 'close', 'view', 'item subtotal',
    'total', 'subtotal', 'payment', 'order summary', 'confirmation', 'choose',
    'returning', 'abandoned', 'animation', 'about', 'general', 'privacy',
    'billed to', 'shipping', 'free shipping', 'processing',
}

PRODUCT_BLOCKLIST = {
    'a payment of', 'amount paid', 'all shopping', 'adjustments',
    'almost', 'amount', 'ambulance service', 'abbreviated numbers',
}

# Email-like handles that aren't people
HANDLE_NOISE = {'@gmail.com', '@yahoo.com', '@icloud.com', '@hotmail.com',
                '@outlook.com', '@mac.com'}

# ══════════════════════════════════════════════════
# MANUAL MERGE MAP — known duplicates to canonical name
# ══════════════════════════════════════════════════

PEOPLE_MERGE = {
    # Jane Doe cluster
    'jane doe': 'Jane Doe',
    'jane doe': 'Jane Doe',
    '@yourhandle': 'Jane Doe',
    'your_old_handle': 'Jane Doe',
    'your_alt_handle': 'Jane Doe',
    'your_third_handle': 'Jane Doe',
    '@yourartistname': 'Jane Doe',
    'yourartistname': 'Jane Doe',
    '@yourdomain.example': 'Jane Doe',
    '@yourdomain.co': 'Jane Doe',
    '@yourhand': 'Jane Doe',
    '@yourhandletypo': 'Jane Doe',
    'the most': 'Jane Doe',
    # Sid cluster
    'collaborator one': 'Collaborator One',
    '@collaborator_one': 'Collaborator One',
    # Partner Studio cluster
    '@partner_studio.example': 'Partner Studio',
    # Event Festival → org
    '@event_org.example': '_ORG:Event Festival',
    '@event_org': '_ORG:Event Festival',
    'Event Festival': '_ORG:Event Festival',
    'event shuttle': '_ORG:Event Festival',
    # Your Company → org
    '@yourcompany': '_ORG:Your Company',
    '@yourcompany': '_ORG:Your Company',
    'yourcompany': '_ORG:Your Company',
    '@yourcompany.example': '_ORG:Your Company',
    # Partner Org → org
    'fiat lux': '_ORG:Partner Org',
    '@partner_org.example': '_ORG:Partner Org',
    'fiat': '_ORG:Partner Org',
}


def is_blocked_person(name):
    n = name.lower().strip()
    if n in PEOPLE_BLOCKLIST: return True
    if n in HANDLE_NOISE: return True
    # Too short
    if len(n) < 3: return True
    # Pure numbers
    if re.match(r'^[\d.]+$', n): return True
    # Email domains mistaken as handles
    if re.match(r'^@[\w]+\.(com|org|net|io|co)$', n) and n not in PEOPLE_MERGE: return True
    # Single words that are common English
    if n in {'the', 'and', 'for', 'you', 'all', 'see', 'add', 'new', 'get',
             'how', 'what', 'who', 'this', 'that', 'just', 'your', 'with'}: return True
    return False


def canonicalize_person(name):
    """Return canonical name, or None to skip."""
    n = name.lower().strip()
    if n in PEOPLE_MERGE:
        merged = PEOPLE_MERGE[n]
        if merged.startswith('_ORG:'):
            return None  # will be handled as org
        return merged
    return name


def score_entity(data):
    """25-point scoring per operating system spec."""
    months = sorted(data.get('months', set()))
    count = data.get('count', len(data.get('screenshots', [])))

    # Recency (0-5)
    recency = 0
    if months:
        try:
            latest_dt = datetime.strptime(months[-1], '%Y-%m')
            months_ago = (datetime(2025, 11, 1) - latest_dt).days / 30
            recency = max(0, min(5, int(5 - months_ago / 3)))
        except:
            recency = 2

    # Repetition (0-5)
    if count >= 10: repetition = 5
    elif count >= 5: repetition = 4
    elif count >= 3: repetition = 3
    elif count >= 2: repetition = 2
    else: repetition = 1

    # Contactability (0-5)
    contact = 0
    if data.get('emails'): contact += 2
    if data.get('phones'): contact += 2
    if data.get('handles'): contact += 1
    if data.get('urls'): contact += 1
    contactability = min(5, contact)

    # Relevance (0-5)
    cats = data.get('categories', set())
    high_rel = {'Receipts / Purchases', 'Airbnb / Reviews', 'Food / Restaurants',
                'Real Estate', 'Business / Sponsorship', 'Art / Design',
                'Event Festival', 'Travel / Flights', 'Stocks / Crypto / Finance'}
    relevance = min(5, len(cats & high_rel) * 2 + (1 if count > 1 else 0))

    # Confidence (0-5)
    confidence = 3
    if count >= 3: confidence += 1
    if data.get('emails') or data.get('phones'): confidence += 1
    if len(months) == 1 and count == 1: confidence -= 1
    confidence = max(1, min(5, confidence))

    return {
        'recency': recency, 'repetition': repetition,
        'contactability': contactability, 'relevance': relevance,
        'confidence': confidence,
        'total': recency + repetition + contactability + relevance + confidence,
    }


def main(organized_dir='Organized'):
    organized = Path(organized_dir)

    with open(organized / 'screenshot_classification_report.json') as f:
        entries = json.load(f)

    processed = organized / 'Screenshots_Processed'
    txt_index = {}
    for cat_dir in processed.iterdir():
        if not cat_dir.is_dir() or cat_dir.name.startswith('.'): continue
        for month_dir in cat_dir.iterdir():
            if not month_dir.is_dir(): continue
            for txt in month_dir.glob('*.txt'):
                txt_index[(txt.stem, month_dir.name)] = txt

    print(f'Processing {len(entries)} screenshots...', flush=True)

    # ── Accumulate entities ──
    people = defaultdict(lambda: {'months': set(), 'categories': set(), 'handles': set(),
                                   'emails': set(), 'phones': set(), 'screenshots': [],
                                   'urls': set(), 'count': 0})

    orgs = defaultdict(lambda: {'months': set(), 'categories': set(), 'urls': set(),
                                 'emails': set(), 'phones': set(), 'screenshots': [],
                                 'prices': set(), 'addresses': set(), 'count': 0})

    products = defaultdict(lambda: {'months': set(), 'categories': set(), 'prices': set(),
                                     'screenshots': [], 'urls': set(), 'count': 0})

    domains = defaultdict(lambda: {'months': set(), 'screenshots': [], 'count': 0})

    for i, entry in enumerate(entries):
        if i % 2000 == 0:
            print(f'  {i}/{len(entries)}...', flush=True)

        file_stem = entry['file']
        month = entry['month']
        category = entry['category']

        txt_path = txt_index.get((file_stem, month))
        ocr = txt_path.read_text(encoding='utf-8', errors='ignore') if txt_path else entry.get('text_preview', '')
        ents = extract_entities(ocr, category=category)

        # ── People ──
        for raw_person in ents.get('people', []):
            if is_blocked_person(raw_person): continue
            canonical = canonicalize_person(raw_person)
            if canonical is None:
                # Rerouted to org
                org_name = PEOPLE_MERGE.get(raw_person.lower().strip(), '').replace('_ORG:', '')
                if org_name:
                    o = orgs[org_name]
                    o['months'].add(month); o['categories'].add(category)
                    o['screenshots'].append(file_stem); o['count'] += 1
                    for u in ents.get('urls', []): o['urls'].add(u)
                    for e in ents.get('emails', []): o['emails'].add(e)
                    for p in ents.get('phones', []): o['phones'].add(p)
                continue

            p = people[canonical]
            p['months'].add(month); p['categories'].add(category)
            p['screenshots'].append(file_stem); p['count'] += 1
            for h in ents.get('handles', []): p['handles'].add(h)
            for e in ents.get('emails', []): p['emails'].add(e)
            for ph in ents.get('phones', []): p['phones'].add(ph)

        # ── Services/Orgs ──
        for svc in ents.get('services', []):
            if svc.lower() in SERVICE_BLOCKLIST or len(svc) < 4: continue
            o = orgs[svc]
            o['months'].add(month); o['categories'].add(category)
            o['screenshots'].append(file_stem); o['count'] += 1
            for u in ents.get('urls', []): o['urls'].add(u)
            for e in ents.get('emails', []): o['emails'].add(e)
            for p in ents.get('phones', []): o['phones'].add(p)
            for pr in ents.get('prices', []): o['prices'].add(pr)
            for a in ents.get('addresses', []): o['addresses'].add(a)

        # ── Products ──
        for prod in ents.get('products', []):
            if prod.lower() in PRODUCT_BLOCKLIST or len(prod) < 5: continue
            pr = products[prod]
            pr['months'].add(month); pr['categories'].add(category)
            pr['screenshots'].append(file_stem); pr['count'] += 1
            for price in ents.get('prices', []): pr['prices'].add(price)
            for u in ents.get('urls', []): pr['urls'].add(u)

        # ── Domains ──
        for url in ents.get('urls', []):
            domain = re.sub(r'^https?://(www\.)?', '', url).split('/')[0].split('?')[0].lower()
            if '.' in domain and len(domain) > 4:
                d = domains[domain]
                d['months'].add(month); d['screenshots'].append(file_stem); d['count'] += 1

    # ── Score everything ──
    print('Scoring and ranking...', flush=True)

    def score_and_sort(data_dict):
        scored = []
        for name, data in data_dict.items():
            scores = score_entity(data)
            months = sorted(data['months'])
            scored.append({
                'name': name,
                'data': data,
                'scores': scores,
                'first_seen': months[0] if months else '',
                'last_seen': months[-1] if months else '',
            })
        scored.sort(key=lambda x: -x['scores']['total'])
        return scored

    s_people = score_and_sort(people)
    s_orgs = score_and_sort(orgs)
    s_products = score_and_sort(products)
    s_domains = sorted(domains.items(), key=lambda x: -x[1]['count'])

    # ── Build markdown ──
    lines = []
    lines.append('# Clean First-Pass Entity Tables\n')
    lines.append(f'**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M")}  ')
    lines.append(f'**Source**: {len(entries)} screenshots  ')
    lines.append(f'**Scoring**: 25-point (Recency + Repetition + Contactability + Relevance + Confidence)  ')
    lines.append(f'**Noise filtered**: blocklists + duplicate merging + org reclassification\n')
    lines.append('---\n')

    # Score distribution
    lines.append('## Score Distribution\n')
    for label, data in [('People', s_people), ('Services/Orgs', s_orgs), ('Products', s_products)]:
        tiers = Counter()
        for item in data:
            t = item['scores']['total']
            if t >= 20: tiers['20-25 Immediate'] += 1
            elif t >= 15: tiers['15-19 Research'] += 1
            elif t >= 10: tiers['10-14 Archive'] += 1
            else: tiers['0-9 Ignore'] += 1
        total = sum(tiers.values())
        lines.append(f'**{label}**: {total} total — '
                     f'{tiers["20-25 Immediate"]} immediate, '
                     f'{tiers["15-19 Research"]} research, '
                     f'{tiers["10-14 Archive"]} archive, '
                     f'{tiers["0-9 Ignore"]} ignore  ')
    lines.append('\n---\n')

    # ── PEOPLE ──
    lines.append(f'## People — Top 250 (of {len(s_people)})\n')
    lines.append('| # | Name | Score | Count | First | Last | Emails | Phones | Categories |')
    lines.append('|---:|---|---:|---:|---|---|---|---|---|')
    for i, item in enumerate(s_people[:250], 1):
        d = item['data']
        s = item['scores']
        emails = ', '.join(sorted(d['emails'] - HANDLE_NOISE))[:60]
        phones = ', '.join(sorted(d['phones']))[:30]
        cats = ', '.join(sorted(d['categories']))[:60]
        tier = '🔴' if s['total'] >= 20 else '🟡' if s['total'] >= 15 else '⚪'
        lines.append(f'| {i} | {tier} **{item["name"]}** | {s["total"]} | {d["count"]} | {item["first_seen"]} | {item["last_seen"]} | {emails} | {phones} | {cats} |')
    lines.append('')

    # ── ORGS/SERVICES ──
    lines.append(f'---\n')
    lines.append(f'## Services / Organizations — Top 100 (of {len(s_orgs)})\n')
    lines.append('| # | Name | Score | Count | First | Last | URLs | Emails | Phones | Prices | Categories |')
    lines.append('|---:|---|---:|---:|---|---|---|---|---|---|---|')
    for i, item in enumerate(s_orgs[:100], 1):
        d = item['data']
        s = item['scores']
        urls = ', '.join(sorted(d.get('urls', set())))[:60]
        emails = ', '.join(sorted(d.get('emails', set())))[:40]
        phones = ', '.join(sorted(d.get('phones', set())))[:25]
        prices = ', '.join(sorted(d.get('prices', set())))[:30]
        cats = ', '.join(sorted(d['categories']))[:50]
        tier = '🔴' if s['total'] >= 20 else '🟡' if s['total'] >= 15 else '⚪'
        lines.append(f'| {i} | {tier} **{item["name"]}** | {s["total"]} | {d["count"]} | {item["first_seen"]} | {item["last_seen"]} | {urls} | {emails} | {phones} | {prices} | {cats} |')
    lines.append('')

    # ── PRODUCTS ──
    lines.append(f'---\n')
    lines.append(f'## Products — Top 100 (of {len(s_products)})\n')
    lines.append('| # | Product | Score | Count | First | Last | Prices | URLs | Categories |')
    lines.append('|---:|---|---:|---:|---|---|---|---|---|')
    for i, item in enumerate(s_products[:100], 1):
        d = item['data']
        s = item['scores']
        prices = ', '.join(sorted(d.get('prices', set())))[:40]
        urls = ', '.join(sorted(d.get('urls', set())))[:50]
        cats = ', '.join(sorted(d['categories']))[:50]
        tier = '🔴' if s['total'] >= 20 else '🟡' if s['total'] >= 15 else '⚪'
        lines.append(f'| {i} | {tier} **{item["name"]}** | {s["total"]} | {d["count"]} | {item["first_seen"]} | {item["last_seen"]} | {prices} | {urls} | {cats} |')
    lines.append('')

    # ── DOMAINS ──
    lines.append(f'---\n')
    lines.append(f'## Domains — Top 50 (of {len(s_domains)})\n')
    lines.append('| # | Domain | Count | First | Last |')
    lines.append('|---:|---|---:|---|---|')
    for i, (domain, data) in enumerate(s_domains[:50], 1):
        months = sorted(data['months'])
        lines.append(f'| {i} | **{domain}** | {data["count"]} | {months[0]} | {months[-1]} |')
    lines.append('')

    output = '\n'.join(lines)
    out_path = organized / 'first_pass_clean.md'
    out_path.write_text(output, encoding='utf-8')
    print(f'\nWritten: {len(output):,} chars to {out_path}')
    print(f'People: {len(s_people)} (was ~6500 before dedup)')
    print(f'Orgs/Services: {len(s_orgs)}')
    print(f'Products: {len(s_products)}')
    print(f'Domains: {len(s_domains)}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--organized-dir', '-d', default='Organized')
    args = parser.parse_args()
    main(args.organized_dir)
