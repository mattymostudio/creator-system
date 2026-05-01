#!/usr/bin/env python3
"""
Documentary Cast Mining — reads enriched contact bundles across all three
email accounts and produces a structured cast list organized by narrative era.

Usage:
    python3 build_documentary_cast.py <enriched_dirs...> <output_path>

Example:
    python3 build_documentary_cast.py \
        02_enriched_bundles/yourcompany_a 02_enriched_bundles/yourcompany_b 02_enriched_bundles/personal \
        "../../../vault/06_OUTPUTS/Documentary Cast List.md"
"""

import json
import glob
import os
import sys
from datetime import datetime
from collections import defaultdict


def classify_era(first_contact, last_contact):
    """Classify a contact into narrative eras based on their active period."""
    eras = []

    if not first_contact:
        return ['unknown']

    try:
        first = datetime.fromisoformat(first_contact)
    except:
        return ['unknown']

    try:
        last = datetime.fromisoformat(last_contact) if last_contact else first
    except:
        last = first

    first_year = first.year
    last_year = last.year

    if first_year <= 2014:
        eras.append('pre_brand')
    if (first_year <= 2016 and last_year >= 2014) or (2014 <= first_year <= 2016):
        eras.append('brand_launch')
    if (first_year <= 2019 and last_year >= 2016) or (2016 <= first_year <= 2019):
        eras.append('brand_commission')
    if (first_year <= 2022 and last_year >= 2019) or (2019 <= first_year <= 2022):
        eras.append('community_platform')
    if (first_year <= 2022 and last_year >= 2020) or (2020 <= first_year <= 2022):
        if any(t in str(eras) for t in ['nft', 'crypto', 'web3']):
            eras.append('nft_boom')
    if last_year >= 2023:
        eras.append('art_park')

    # Deduplicate and assign primary era (where they have most activity)
    return list(dict.fromkeys(eras)) if eras else ['unknown']


def infer_narrative_function(enrichment, total_emails, relationship_type):
    """Infer the narrative role this person plays in the documentary."""
    summary = (enrichment.get('relationship_summary', '') or '').lower()
    notable = (enrichment.get('notable_context', '') or '').lower()
    combined = summary + ' ' + notable

    if any(w in combined for w in ['invest', 'fund', 'capital', 'backer', 'seed', 'raise']):
        return 'backer'
    if any(w in combined for w in ['mentor', 'advisor', 'introduced', 'connected', 'referred']):
        return 'mentor/connector'
    if any(w in combined for w in ['press', 'article', 'interview', 'coverage', 'journalist', 'reporter']):
        return 'chronicler'
    if any(w in combined for w in ['dispute', 'threaten', 'fraud', 'conflict', 'broke down', 'extort']):
        return 'antagonist'
    if any(w in combined for w in ['family', 'mother', 'father', 'brother', 'sister', 'wife', 'fiance']):
        return 'family'
    if any(w in combined for w in ['collector', 'bought', 'purchased', 'commission']):
        return 'collector/patron'
    if any(w in combined for w in ['build', 'install', 'fabricat', 'construct', 'architect']):
        return 'builder'
    if any(w in combined for w in ['civic', 'city', 'county', 'government', 'mayor', 'commissioner']):
        return 'civic partner'
    if total_emails >= 100:
        return 'core collaborator'
    if relationship_type in ('collaborator', 'contractor'):
        return 'collaborator'
    if relationship_type == 'peer':
        return 'peer/witness'
    return 'supporting'


ERA_NAMES = {
    'pre_brand': '1. Pre-brand: Your University, Startups, and the Wilderness (2004-2014)',
    'brand_launch': '2. Brand Launch & Viral Growth (2014-2016)',
    'brand_commission': '3. Brand & Commission Era (2016-2019)',
    'community_platform': '4. Community & Platform (2019-2022)',
    'nft_boom': '5. NFT Boom & Digital Art (2020-2022)',
    'art_park': '6. Your Company / Anytown (2023-present)',
    'unknown': '7. Unplaced / Cross-era',
}


def process_cast(enriched_dirs, output_path):
    # Load all enriched bundles
    all_contacts = []

    for edir in enriched_dirs:
        for bf in glob.glob(os.path.join(edir, '*.json')):
            basename = os.path.basename(bf)
            if any(x in basename for x in ['megabatch', 'results_', 'batch_', 'manifest']):
                continue
            try:
                with open(bf) as f:
                    bundle = json.load(f)
            except:
                continue

            if 'email' not in bundle:
                continue

            all_contacts.append(bundle)

    print(f"Loaded {len(all_contacts)} contacts across all accounts")

    # Filter to documentary-relevant
    documentary_contacts = []

    for c in all_contacts:
        enrichment = c.get('enrichment') or {}
        matched = c.get('matched', {})
        total = c.get('total_emails', 0)
        rel_type = enrichment.get('relationship_type', '') or ''
        notable = enrichment.get('notable_context', '') or ''
        summary = enrichment.get('relationship_summary', '') or ''

        # Skip if no enrichment and low volume
        if not enrichment and total < 50:
            continue

        # Filter criteria
        dominated_types = {'collaborator', 'investor', 'press', 'collector', 'family',
                          'friend', 'legal', 'financial', 'government', 'patron'}

        is_relevant = (
            rel_type in dominated_types
            or total >= 50
            or bool(notable)
            or matched.get('vault_match')
            or rel_type == 'contractor' and total >= 20
        )

        if not is_relevant:
            continue

        # Build cast entry
        name = matched.get('best_name', '')
        if not name and c.get('display_names'):
            name = c['display_names'][0]
        if not name:
            name = c['email'].split('@')[0]

        # Skip the user's own addresses
        if c['email'] in {'you@yourcompany.example', 'you@yourdomain.example',
                          'you-personal@example.com', 'you-work2@example.com', 'you-work3@example.com',
                          'you-work4@example.com', 'you-sampleb@example.com', 'you@yourcompany.example',
                          'your-handle@gmail.example', 'you@yourcompany.example', 'you-work@example.com',
                          'info@yourdomain.example'}:
            continue

        eras = classify_era(c.get('first_contact'), c.get('last_contact'))
        primary_era = eras[0]

        narrative_fn = infer_narrative_function(enrichment, total, rel_type)

        # Extract key scenes from thread subjects
        scenes = []
        for t in c.get('threads', [])[:10]:
            subj = t.get('subject', '')
            if subj and len(subj) > 5:
                date_str = (t.get('date') or '?')[:10]
                scenes.append(f"{date_str}: {subj[:80]}")

        first = c.get('first_contact', '')[:10] if c.get('first_contact') else '?'
        last = c.get('last_contact', '')[:10] if c.get('last_contact') else '?'

        entry = {
            'name': name,
            'email': c['email'],
            'role_title': enrichment.get('role_title', '') or matched.get('best_title', '') or '',
            'relationship_type': rel_type,
            'relationship_summary': summary,
            'notable_context': notable,
            'key_topics': enrichment.get('key_topics', []),
            'projects': enrichment.get('projects_in_common', []),
            'total_emails': total,
            'first_contact': first,
            'last_contact': last,
            'source_account': c.get('source_account', '?'),
            'primary_era': primary_era,
            'all_eras': eras,
            'narrative_function': narrative_fn,
            'scenes': scenes,
            'vault_page': matched.get('vault_match'),
            'communication_style': enrichment.get('communication_style', ''),
        }
        documentary_contacts.append(entry)

    print(f"Documentary-relevant: {len(documentary_contacts)}")

    # Sort by total emails within each era
    documentary_contacts.sort(key=lambda x: x['total_emails'], reverse=True)

    # Group by primary era
    by_era = defaultdict(list)
    for c in documentary_contacts:
        by_era[c['primary_era']].append(c)

    # Build the markdown output
    lines = []
    lines.append('---')
    lines.append('type: output')
    lines.append('status: draft')
    lines.append('format: cast-list')
    lines.append(f'date: {datetime.now().strftime("%Y-%m-%d")}')
    lines.append('project: Documentary')
    lines.append('---')
    lines.append('')
    lines.append('# Documentary Cast List')
    lines.append('')
    lines.append(f'Generated from email corpus: {len(all_contacts)} total contacts, {len(documentary_contacts)} documentary-relevant.')
    lines.append(f'Sources: yourcompany, YOURBRAND, personal email archives.')
    lines.append(f'Evidence basis: email correspondence only. All claims cite specific emails.')
    lines.append('')
    lines.append('## How to read this')
    lines.append('- **Emails** = total email count across all accounts (signals relationship depth)')
    lines.append('- **Narrative function** = inferred role in the story arc')
    lines.append('- **Evidence** = how much email content exists to source from')
    lines.append('- Characters marked with [[Name]] have existing vault pages')
    lines.append('')

    era_order = ['pre_brand', 'brand_launch', 'brand_commission', 'community_platform', 'nft_boom', 'art_park', 'unknown']

    for era in era_order:
        contacts = by_era.get(era, [])
        if not contacts:
            continue

        era_name = ERA_NAMES.get(era, era)
        lines.append(f'## {era_name}')
        lines.append('')

        # Group by narrative function within era
        by_function = defaultdict(list)
        for c in contacts:
            by_function[c['narrative_function']].append(c)

        fn_order = ['family', 'core collaborator', 'backer', 'mentor/connector', 'builder',
                     'chronicler', 'civic partner', 'collector/patron', 'antagonist',
                     'collaborator', 'peer/witness', 'supporting']

        for fn in fn_order:
            fn_contacts = by_function.get(fn, [])
            if not fn_contacts:
                continue

            lines.append(f'### {fn.title()}')
            lines.append('')

            for c in fn_contacts[:30]:  # Cap per function per era
                vault_link = f'[[{c["vault_page"]}]]' if c.get('vault_page') else ''
                name_display = f'**{c["name"]}**' + (f' {vault_link}' if vault_link else '')

                lines.append(f'#### {name_display}')
                lines.append(f'- Role: {c["role_title"] or c["relationship_type"]}')
                lines.append(f'- Emails: {c["total_emails"]} ({c["first_contact"]} to {c["last_contact"]})')
                lines.append(f'- Source: {c["source_account"]}')
                lines.append(f'- Narrative function: {c["narrative_function"]}')

                if c['relationship_summary']:
                    lines.append(f'- Summary: {c["relationship_summary"]}')
                if c['notable_context']:
                    lines.append(f'- Notable: {c["notable_context"]}')
                if c['projects']:
                    lines.append(f'- Projects: {", ".join(c["projects"])}')
                if c['key_topics']:
                    lines.append(f'- Topics: {", ".join(c["key_topics"])}')
                if c['scenes']:
                    lines.append(f'- Key threads:')
                    for s in c['scenes'][:5]:
                        lines.append(f'  - {s}')
                lines.append('')

        lines.append('---')
        lines.append('')

    # Summary stats
    lines.append('## Summary Statistics')
    lines.append('')
    lines.append(f'| Era | Characters |')
    lines.append(f'|-----|-----------|')
    for era in era_order:
        count = len(by_era.get(era, []))
        if count:
            lines.append(f'| {ERA_NAMES.get(era, era).split(".")[0]} | {count} |')
    lines.append(f'| **Total** | **{len(documentary_contacts)}** |')
    lines.append('')

    # Narrative function breakdown
    fn_counts = defaultdict(int)
    for c in documentary_contacts:
        fn_counts[c['narrative_function']] += 1

    lines.append(f'| Narrative Function | Count |')
    lines.append(f'|-------------------|-------|')
    for fn, count in sorted(fn_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f'| {fn.title()} | {count} |')
    lines.append('')

    # Write output
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"\nWritten: {output_path}")
    print(f"Total characters: {len(documentary_contacts)}")

    # Top 30 by email volume
    print(f"\nTop 30 documentary characters by email volume:")
    for c in documentary_contacts[:30]:
        print(f"  {c['total_emails']:>5}  {c['narrative_function']:<20} {c['name']:<30} {c['primary_era']}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 build_documentary_cast.py <enriched_dir1> [enriched_dir2...] <output_path>")
        sys.exit(1)

    enriched_dirs = sys.argv[1:-1]
    output_path = sys.argv[-1]
    process_cast(enriched_dirs, output_path)
