#!/usr/bin/env python3
"""
Phase 5: Vault people page integration.

Updates existing vault pages with email-derived content and creates
new pages for significant contacts.

Usage:
    python3 vault_integrate.py <enriched_dir> <people_dir> [--dry-run] [--min-strength 50]
"""

import json
import glob
import os
import re
import argparse
import math
from datetime import datetime


PEOPLE_DIR = "/path/to/your-vault/04_CANON/Shared/People"

PERSON_TEMPLATE = """---
type: person
status: working
last_updated: {today}
aliases:
  - {email}
email_contact: {email}
related_projects:{projects_yaml}
---

# {name}

## Who they are
{who}

## Relationship to Jane D
{relationship}

## Key interactions
| Date | Context | Notes |
|------|---------|-------|
{interactions}

## Projects in common
{projects_list}

## Source notes
- (Source: yourcompany email archive, {date_range})

## Open questions
-
"""


def build_new_page(contact):
    """Build a new person page from enriched contact data."""
    enrichment = contact.get('enrichment', {}) or {}
    matched = contact.get('matched', {}) or {}

    name = matched.get('best_name', '')
    if not name and contact.get('display_names'):
        name = contact['display_names'][0]
    if not name:
        name = contact['email'].split('@')[0]

    email = contact['email']
    role = enrichment.get('role_title', '')
    rel_type = enrichment.get('relationship_type', 'unknown')
    summary = enrichment.get('relationship_summary', '')
    topics = enrichment.get('key_topics', [])
    projects = enrichment.get('projects_in_common', [])
    notable = enrichment.get('notable_context', '')
    comm_style = enrichment.get('communication_style', '')

    # Who they are
    who_parts = []
    if role:
        who_parts.append(role + '.')
    if rel_type != 'unknown':
        who_parts.append(f"Relationship type: {rel_type}.")
    who = ' '.join(who_parts) if who_parts else f"Contact from yourcompany email correspondence."

    # Relationship
    rel_parts = []
    if summary:
        rel_parts.append(summary)
    if notable:
        rel_parts.append(notable)
    if comm_style:
        rel_parts.append(f"Communication style: {comm_style}")
    relationship = '\n'.join(rel_parts) if rel_parts else f"{rel_type.capitalize()} relationship via yourcompany email."

    # Key interactions from email threads
    interactions = ''
    threads = contact.get('threads', [])[:5]
    for t in threads:
        date = t.get('date', '')[:10] if t.get('date') else ''
        subject = t.get('subject', '(no subject)')
        direction = 'Inbound' if t.get('direction') == 'from' else 'Outbound' if t.get('direction') == 'to' else 'CC'
        interactions += f"| {date} | {subject[:60]} | {direction} |\n"
    if not interactions:
        interactions = '| | | |\n'

    # Projects
    projects_yaml = ''
    projects_list = ''
    if projects:
        projects_yaml = '\n' + '\n'.join(f'  - {p}' for p in projects)
        projects_list = '\n'.join(f'- [[{p}]]' for p in projects)
    else:
        projects_yaml = ' []'
        projects_list = '-'

    # Date range
    first = contact.get('first_contact', '')[:10] if contact.get('first_contact') else '?'
    last = contact.get('last_contact', '')[:10] if contact.get('last_contact') else '?'
    date_range = f"{first} to {last}"

    return PERSON_TEMPLATE.format(
        today=datetime.now().strftime('%Y-%m-%d'),
        email=email,
        name=name,
        who=who,
        relationship=relationship,
        interactions=interactions.rstrip(),
        projects_yaml=projects_yaml,
        projects_list=projects_list,
        date_range=date_range,
    )


def build_update_section(contact):
    """Build content to append to an existing person page."""
    enrichment = contact.get('enrichment', {}) or {}

    summary = enrichment.get('relationship_summary', '')
    notable = enrichment.get('notable_context', '')
    projects = enrichment.get('projects_in_common', [])
    topics = enrichment.get('key_topics', [])
    role = enrichment.get('role_title', '')

    first = contact.get('first_contact', '')[:10] if contact.get('first_contact') else '?'
    last = contact.get('last_contact', '')[:10] if contact.get('last_contact') else '?'

    parts = []
    parts.append(f"\n## Email archive context")
    parts.append(f"(Source: yourcompany email archive, {first} to {last})")
    parts.append(f"Total correspondence: {contact.get('total_emails', 0)} emails")
    if role:
        parts.append(f"Role: {role}")
    if summary:
        parts.append(f"\n{summary}")
    if notable:
        parts.append(f"\n{notable}")
    if topics:
        parts.append(f"\nKey topics: {', '.join(topics)}")

    # Add a few interaction rows
    threads = contact.get('threads', [])[:5]
    if threads:
        parts.append(f"\n### Email interactions")
        parts.append("| Date | Subject | Direction |")
        parts.append("|------|---------|-----------|")
        for t in threads:
            date = t.get('date', '')[:10] if t.get('date') else ''
            subject = t.get('subject', '(no subject)')[:60]
            direction = 'Inbound' if t.get('direction') == 'from' else 'Outbound' if t.get('direction') == 'to' else 'CC'
            parts.append(f"| {date} | {subject} | {direction} |")

    return '\n'.join(parts)


def compute_strength(bundle):
    total = bundle.get('total_emails', 0)
    vol = min(15, math.log2(max(1, total)) * 15 / math.log2(500)) if total > 0 else 0
    rec = 0
    if bundle.get('last_contact'):
        try:
            days = (datetime.now() - datetime.fromisoformat(bundle['last_contact'])).days
            rec = max(0, (1 - days / 730)) * 40
        except:
            pass
    ef = bundle.get('emails_from', 0)
    et = bundle.get('emails_to', 0)
    recip = min(ef, et) / max(ef, et) * 45 if ef > 0 and et > 0 else 10 if (ef > 0 or et > 0) else 0
    return round(vol + rec + recip)


def process_integration(enriched_dir, people_dir, dry_run=False, min_strength=50):
    # Load all enriched bundles
    all_files = sorted(glob.glob(os.path.join(enriched_dir, '*.json')))
    bundle_files = [f for f in all_files if not any(
        x in os.path.basename(f) for x in ['manifest', 'megabatch', 'results_', 'batch_']
    )]

    # Categorize
    updates = []  # existing pages to enrich
    creates = []  # new pages to create

    for bf in bundle_files:
        with open(bf) as f:
            bundle = json.load(f)

        matched = bundle.get('matched', {})
        enrichment = bundle.get('enrichment')
        total = bundle.get('total_emails', 0)

        if matched.get('vault_match') and matched.get('vault_match_status') == 'confirmed':
            updates.append(bundle)
        elif enrichment and total >= 10 and 'error' not in (enrichment or {}):
            strength = compute_strength(bundle)
            rel_type = enrichment.get('relationship_type', 'unknown')
            # Create if significant
            if strength >= min_strength or total >= 30 or rel_type in (
                'collaborator', 'investor', 'press', 'legal', 'financial', 'government', 'family', 'friend'
            ):
                bundle['_strength'] = strength
                creates.append(bundle)

    creates.sort(key=lambda b: b.get('_strength', 0), reverse=True)

    print(f"=== Vault Integration ===")
    print(f"Existing pages to update: {len(updates)}")
    print(f"New pages to create: {len(creates)}")

    if dry_run:
        print("\n[DRY RUN] Would update:")
        for b in updates:
            print(f"  {b['matched']['vault_match']}.md — {b['email']} ({b.get('total_emails', 0)} emails)")
        print(f"\n[DRY RUN] Would create {len(creates)} new pages")
        for b in creates[:20]:
            name = b.get('matched', {}).get('best_name', b.get('display_names', [''])[0] if b.get('display_names') else '')
            print(f"  {name}.md — {b['email']} ({b.get('total_emails', 0)} emails, strength {b.get('_strength', 0)})")
        return

    # Process updates
    updated = 0
    for bundle in updates:
        vault_page = bundle['matched']['vault_match']
        page_path = os.path.join(people_dir, f"{vault_page}.md")

        if not os.path.exists(page_path):
            print(f"  SKIP (file not found): {page_path}")
            continue

        with open(page_path, 'r') as f:
            content = f.read()

        # Check if already updated
        if 'Email archive context' in content:
            print(f"  SKIP (already updated): {vault_page}")
            continue

        # Add email contact to frontmatter
        if 'email_contact:' not in content:
            content = content.replace('---\n\n#', f'email_contact: {bundle["email"]}\n---\n\n#', 1)

        # Update last_updated
        today = datetime.now().strftime('%Y-%m-%d')
        content = re.sub(r'last_updated:.*', f'last_updated: {today}', content)

        # Append email context section
        update_section = build_update_section(bundle)
        content += '\n' + update_section + '\n'

        with open(page_path, 'w') as f:
            f.write(content)

        updated += 1
        print(f"  UPDATED: {vault_page}.md (+email context from {bundle.get('total_emails', 0)} emails)")

    # Process creates
    created = 0
    for bundle in creates:
        enrichment = bundle.get('enrichment', {}) or {}
        matched = bundle.get('matched', {}) or {}

        name = matched.get('best_name', '')
        if not name and bundle.get('display_names'):
            name = bundle['display_names'][0]
        if not name:
            # Skip contacts without a real name
            continue

        # Clean name for filename
        clean_name = name.strip().strip("'\"")
        # Skip very short or email-like names
        if len(clean_name) < 3 or '@' in clean_name:
            continue

        # Proper case
        if clean_name == clean_name.lower():
            clean_name = clean_name.title()
        # Remove path-unsafe characters
        clean_name = clean_name.replace('/', '-').replace('\\', '-')

        page_path = os.path.join(people_dir, f"{clean_name}.md")

        if os.path.exists(page_path):
            print(f"  SKIP (already exists): {clean_name}.md")
            continue

        page_content = build_new_page(bundle)

        with open(page_path, 'w') as f:
            f.write(page_content)

        created += 1
        rel_type = enrichment.get('relationship_type', '?')
        print(f"  CREATED: {clean_name}.md ({rel_type}, {bundle.get('total_emails', 0)} emails)")

    print(f"\n=== Results ===")
    print(f"Pages updated: {updated}")
    print(f"Pages created: {created}")
    print(f"Total people pages: {len(glob.glob(os.path.join(people_dir, '*.md')))}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vault people page integration')
    parser.add_argument('enriched_dir', help='Directory with enriched bundles')
    parser.add_argument('people_dir', help='Vault people directory')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--min-strength', type=int, default=50)
    args = parser.parse_args()

    process_integration(args.enriched_dir, args.people_dir, args.dry_run, args.min_strength)
