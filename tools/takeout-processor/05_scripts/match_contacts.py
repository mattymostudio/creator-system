#!/usr/bin/env python3
"""
Phase 2: Match email contacts against existing data sources.

Cross-references contact bundles against:
- Google Contacts CSV (phone, address, org, title)
- Notion CRM CSV (collector type, purchases, priority)
- Vault People pages (fuzzy name matching)

Usage:
    python3 match_contacts.py <bundles_dir> <output_dir> \
        --google-contacts <contacts.csv> \
        --notion-crm <crm.csv> \
        --people-dir <04_CANON/Shared/People/>
"""

import json
import csv
import os
import re
import argparse
import glob
import yaml
from collections import defaultdict


def normalize_name(name):
    """Normalize a name for fuzzy matching."""
    if not name:
        return ''
    name = name.lower().strip()
    name = re.sub(r'[^a-z\s]', '', name)
    name = ' '.join(name.split())
    return name


def name_parts(name):
    """Split a name into parts for matching."""
    parts = normalize_name(name).split()
    return parts


def levenshtein(s1, s2):
    """Simple Levenshtein distance."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]


def name_match_score(name1, name2):
    """Score how well two names match (0-100)."""
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    if not n1 or not n2:
        return 0

    # Exact match
    if n1 == n2:
        return 100

    parts1 = n1.split()
    parts2 = n2.split()

    # Check if last names match and first name starts the same
    if len(parts1) >= 2 and len(parts2) >= 2:
        if parts1[-1] == parts2[-1]:
            # Same last name
            if parts1[0] == parts2[0]:
                return 95  # Same first and last
            if parts1[0][:3] == parts2[0][:3]:
                return 85  # Similar first name, same last
            return 70  # Different first name, same last

    # Levenshtein on full name
    dist = levenshtein(n1, n2)
    max_len = max(len(n1), len(n2))
    if max_len == 0:
        return 0
    similarity = (1 - dist / max_len) * 100
    return max(0, similarity)


def load_google_contacts(csv_path):
    """Load Google Contacts CSV into email-indexed lookup."""
    contacts = {}
    if not csv_path or not os.path.exists(csv_path):
        return contacts

    with open(csv_path, 'r', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for email_col in ['E-mail 1 - Value', 'E-mail 2 - Value', 'E-mail 3 - Value']:
                email_val = row.get(email_col, '').strip().lower()
                if email_val:
                    first = row.get('First Name', '').strip()
                    last = row.get('Last Name', '').strip()
                    full_name = f"{first} {last}".strip()

                    contacts[email_val] = {
                        'gc_name': full_name if full_name else None,
                        'gc_org': row.get('Organization Name', '').strip() or None,
                        'gc_title': row.get('Organization Title', '').strip() or None,
                        'gc_phone': row.get('Phone 1 - Value', '').strip() or None,
                        'gc_phone2': row.get('Phone 2 - Value', '').strip() or None,
                        'gc_city': row.get('Address 1 - City', '').strip() or None,
                        'gc_region': row.get('Address 1 - Region', '').strip() or None,
                        'gc_country': row.get('Address 1 - Country', '').strip() or None,
                        'gc_address': row.get('Address 1 - Formatted', '').strip() or None,
                        'gc_website': row.get('Website 1 - Value', '').strip() or None,
                        'gc_birthday': row.get('Birthday', '').strip() or None,
                        'gc_nickname': row.get('Nickname', '').strip() or None,
                        'gc_notes': row.get('Notes', '').strip() or None,
                    }
    return contacts


def load_notion_crm(csv_path):
    """Load Notion CRM CSV into email-indexed lookup."""
    collectors = {}
    if not csv_path or not os.path.exists(csv_path):
        return collectors

    with open(csv_path, 'r', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email_val = row.get('Email', '').strip().lower()
            if email_val:
                collectors[email_val] = {
                    'crm_name': row.get('Collector Name', '').strip() or None,
                    'crm_phone': row.get('Phone', '').strip() or None,
                    'crm_city': row.get('City', '').strip() or None,
                    'crm_state': row.get('State/Province', '').strip() or None,
                    'crm_country': row.get('Country', '').strip() or None,
                    'crm_collector_type': row.get('Collector Type', '').strip() or None,
                    'crm_priority': row.get('Priority', '').strip() or None,
                    'crm_first_order': row.get('First Order Date', '').strip() or None,
                    'crm_last_order': row.get('Last Order Date', '').strip() or None,
                    'crm_total_orders': row.get('Total Orders', '').strip() or None,
                    'crm_gross_sales': row.get('Gross Sales ($)', '').strip() or None,
                    'crm_net_sales': row.get('Net Sales ($)', '').strip() or None,
                    'crm_products': row.get('Products Purchased', '').strip() or None,
                    'crm_tags': row.get('Tags', '').strip() or None,
                    'crm_outreach_status': row.get('Outreach Status', '').strip() or None,
                    'crm_notes': row.get('Notes', '').strip() or None,
                }
    return collectors


def load_vault_people(people_dir):
    """Load vault people page names and aliases."""
    pages = {}
    if not people_dir or not os.path.exists(people_dir):
        return pages

    for path in glob.glob(os.path.join(people_dir, '*.md')):
        filename = os.path.basename(path)
        page_name = filename.replace('.md', '')

        aliases = []
        # Try to read frontmatter for aliases
        try:
            with open(path, 'r') as f:
                content = f.read()
            if content.startswith('---'):
                end = content.find('---', 3)
                if end > 0:
                    fm = yaml.safe_load(content[3:end])
                    if fm and isinstance(fm, dict):
                        aliases = fm.get('aliases', []) or []
                        if isinstance(aliases, str):
                            aliases = [aliases]
        except Exception:
            pass

        pages[page_name] = {
            'filename': filename,
            'path': path,
            'aliases': aliases,
            'normalized': normalize_name(page_name),
        }

    return pages


def match_to_vault(display_names, vault_pages):
    """Try to match a contact's display names against vault people pages."""
    best_match = None
    best_score = 0

    for name in display_names:
        if not name:
            continue
        for page_name, page_data in vault_pages.items():
            # Match against page name
            score = name_match_score(name, page_name)
            if score > best_score:
                best_score = score
                best_match = page_name

            # Match against aliases
            for alias in page_data.get('aliases', []):
                if alias:
                    score = name_match_score(name, str(alias))
                    if score > best_score:
                        best_score = score
                        best_match = page_name

    return best_match, best_score


def process_matches(bundles_dir, output_dir, google_contacts_path, notion_crm_path, people_dir):
    # Load data sources
    gc = load_google_contacts(google_contacts_path)
    print(f"Loaded {len(gc)} Google Contacts (by email)")

    crm = load_notion_crm(notion_crm_path)
    print(f"Loaded {len(crm)} Notion CRM records")

    vault = load_vault_people(people_dir)
    print(f"Loaded {len(vault)} vault People pages")

    # Process each bundle
    bundle_files = glob.glob(os.path.join(bundles_dir, '*.json'))
    print(f"\nProcessing {len(bundle_files)} contact bundles...")

    match_report = []
    review_needed = []

    for bf in sorted(bundle_files):
        with open(bf, 'r') as f:
            bundle = json.load(f)

        addr = bundle['email']
        names = bundle.get('display_names', [])

        record = {
            'email': addr,
            'display_names': names,
            'total_emails': bundle.get('total_emails', 0),
            'first_contact': bundle.get('first_contact'),
            'last_contact': bundle.get('last_contact'),
            'source_account': bundle.get('source_account', 'unknown'),
        }

        # --- Google Contacts match ---
        gc_data = gc.get(addr)
        if gc_data:
            record['gc_match'] = True
            record.update(gc_data)
        else:
            record['gc_match'] = False

        # --- Notion CRM match ---
        crm_data = crm.get(addr)
        if crm_data:
            record['crm_match'] = True
            record.update(crm_data)
        else:
            record['crm_match'] = False

        # --- Vault People match ---
        vault_match, vault_score = match_to_vault(names, vault)
        if vault_score >= 90:
            record['vault_match'] = vault_match
            record['vault_match_score'] = vault_score
            record['vault_match_status'] = 'confirmed'
        elif vault_score >= 60:
            record['vault_match'] = vault_match
            record['vault_match_score'] = vault_score
            record['vault_match_status'] = 'needs_review'
            review_needed.append({
                'email': addr,
                'display_names': ', '.join(names),
                'proposed_match': vault_match,
                'match_score': vault_score,
                'total_emails': bundle.get('total_emails', 0),
                'action': '',  # for human to fill in
            })
        else:
            record['vault_match'] = None
            record['vault_match_score'] = vault_score
            record['vault_match_status'] = 'no_match'

        # Merge best name
        best_name = ''
        if gc_data and gc_data.get('gc_name'):
            best_name = gc_data['gc_name']
        elif crm_data and crm_data.get('crm_name'):
            best_name = crm_data['crm_name']
        elif names:
            best_name = names[0]
        record['best_name'] = best_name

        # Merge phone
        phone = None
        if gc_data and gc_data.get('gc_phone'):
            phone = gc_data['gc_phone']
        elif crm_data and crm_data.get('crm_phone'):
            phone = crm_data['crm_phone']
        elif bundle.get('phones_from_sig'):
            phone = bundle['phones_from_sig'][0]
        record['best_phone'] = phone

        # Merge org
        org = None
        if gc_data and gc_data.get('gc_org'):
            org = gc_data['gc_org']
        record['best_org'] = org

        # Merge title
        title = None
        if gc_data and gc_data.get('gc_title'):
            title = gc_data['gc_title']
        elif bundle.get('titles_from_sig'):
            title = bundle['titles_from_sig'][0]
        record['best_title'] = title

        # Merge location
        city = gc_data.get('gc_city') if gc_data else None
        region = gc_data.get('gc_region') if gc_data else None
        if not city and crm_data:
            city = crm_data.get('crm_city')
            region = crm_data.get('crm_state')
        record['best_city'] = city
        record['best_region'] = region

        # Enrichment tier
        total = bundle.get('total_emails', 0)
        if total >= 10:
            record['enrichment_tier'] = 'A'
        elif total >= 5:
            record['enrichment_tier'] = 'B'
        else:
            record['enrichment_tier'] = 'C'

        match_report.append(record)

        # Update the bundle file with merged data
        bundle['matched'] = {
            'gc_match': record.get('gc_match', False),
            'crm_match': record.get('crm_match', False),
            'vault_match': record.get('vault_match'),
            'vault_match_score': record.get('vault_match_score', 0),
            'vault_match_status': record.get('vault_match_status'),
            'best_name': best_name,
            'best_phone': phone,
            'best_org': org,
            'best_title': title,
            'best_city': city,
            'best_region': region,
            'enrichment_tier': record['enrichment_tier'],
        }
        if gc_data:
            bundle['google_contacts'] = gc_data
        if crm_data:
            bundle['notion_crm'] = crm_data

        with open(bf, 'w') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)

    # Write match report
    report_path = os.path.join(output_dir, 'match_report.json')
    with open(report_path, 'w') as f:
        json.dump(match_report, f, indent=2, ensure_ascii=False)

    # Write review CSV
    review_path = os.path.join(output_dir, 'match_review.csv')
    if review_needed:
        with open(review_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'email', 'display_names', 'proposed_match', 'match_score', 'total_emails', 'action'
            ])
            writer.writeheader()
            writer.writerows(review_needed)

    # Stats
    gc_matches = sum(1 for r in match_report if r.get('gc_match'))
    crm_matches = sum(1 for r in match_report if r.get('crm_match'))
    vault_confirmed = sum(1 for r in match_report if r.get('vault_match_status') == 'confirmed')
    vault_review = sum(1 for r in match_report if r.get('vault_match_status') == 'needs_review')
    tier_a = sum(1 for r in match_report if r.get('enrichment_tier') == 'A')
    tier_b = sum(1 for r in match_report if r.get('enrichment_tier') == 'B')
    tier_c = sum(1 for r in match_report if r.get('enrichment_tier') == 'C')

    print(f"\n=== Match Report ===")
    print(f"Total contacts: {len(match_report)}")
    print(f"Google Contacts matched: {gc_matches}")
    print(f"Notion CRM matched: {crm_matches}")
    print(f"Vault People confirmed: {vault_confirmed}")
    print(f"Vault People needs review: {vault_review}")
    print(f"No vault match: {len(match_report) - vault_confirmed - vault_review}")
    print(f"\nEnrichment tiers: A={tier_a}, B={tier_b}, C={tier_c}")
    print(f"\nWritten: {report_path}")
    if review_needed:
        print(f"Written: {review_path} ({len(review_needed)} entries to review)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Match contacts across data sources')
    parser.add_argument('bundles_dir', help='Directory with contact bundle JSON files')
    parser.add_argument('output_dir', help='Directory for match report output')
    parser.add_argument('--google-contacts', help='Path to Google Contacts CSV')
    parser.add_argument('--notion-crm', help='Path to Notion CRM CSV')
    parser.add_argument('--people-dir', help='Path to vault People directory')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    process_matches(
        args.bundles_dir, args.output_dir,
        args.google_contacts, args.notion_crm, args.people_dir,
    )
