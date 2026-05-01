#!/usr/bin/env python3
"""
Phase 4: Build master Airtable-ready CSV from enriched contact bundles.

Merges all enrichment sources (MBOX metadata, Google Contacts, Notion CRM,
LLM enrichment) into a single CSV ready for Airtable import.

Usage:
    python3 build_master_csv.py <enriched_dir> <output_csv>
"""

import json
import csv
import os
import glob
import math
import argparse
from datetime import datetime, date


def compute_relationship_strength(total_emails, last_contact_str, emails_from, emails_to):
    """
    Relationship strength score (0-100).
    Formula: log2(total_emails)*15 + recency_score*40 + reciprocity*45
    """
    # Email volume component (0-15 range for typical volumes)
    if total_emails > 0:
        volume_score = min(15, math.log2(total_emails) * 15 / math.log2(500))
    else:
        volume_score = 0

    # Recency component (0-40, linear decay over 2 years)
    recency_score = 0
    if last_contact_str:
        try:
            last_dt = datetime.fromisoformat(last_contact_str)
            days_ago = (datetime.now() - last_dt).days
            recency_score = max(0, (1 - days_ago / 730)) * 40
        except (ValueError, TypeError):
            pass

    # Reciprocity component (0-45, higher when balanced)
    reciprocity = 0
    if emails_from > 0 and emails_to > 0:
        ratio = min(emails_from, emails_to) / max(emails_from, emails_to)
        reciprocity = ratio * 45
    elif emails_from > 0 or emails_to > 0:
        reciprocity = 10  # One-way but exists

    score = volume_score + recency_score + reciprocity
    return round(min(100, max(0, score)))


def build_master_csv(enriched_dir, output_csv):
    all_files = sorted(glob.glob(os.path.join(enriched_dir, '*.json')))
    # Skip non-bundle files (manifests, megabatches, results)
    bundle_files = [
        f for f in all_files
        if not any(x in os.path.basename(f) for x in ['manifest', 'megabatch', 'results_', 'batch_'])
    ]
    print(f"Processing {len(bundle_files)} enriched bundles (skipped {len(all_files) - len(bundle_files)} non-bundle files)...")

    rows = []
    for bf in bundle_files:
        with open(bf, 'r') as f:
            bundle = json.load(f)

        addr = bundle['email']
        matched = bundle.get('matched', {})
        enrichment = bundle.get('enrichment') or {}
        gc = bundle.get('google_contacts', {})
        crm = bundle.get('notion_crm', {})

        # Best name
        name = matched.get('best_name', '')
        if not name and bundle.get('display_names'):
            name = bundle['display_names'][0]

        # Relationship strength
        strength = compute_relationship_strength(
            bundle.get('total_emails', 0),
            bundle.get('last_contact'),
            bundle.get('emails_from', 0),
            bundle.get('emails_to', 0),
        )

        # Communication gap
        gap_days = None
        if bundle.get('last_contact'):
            try:
                last_dt = datetime.fromisoformat(bundle['last_contact'])
                gap_days = (datetime.now() - last_dt).days
            except (ValueError, TypeError):
                pass

        # Build row
        row = {
            'name': name,
            'email': addr,
            'phone': matched.get('best_phone', '') or '',
            'organization': matched.get('best_org', '') or '',
            'role_title': enrichment.get('role_title') or matched.get('best_title', '') or '',
            'city': matched.get('best_city', '') or '',
            'state': matched.get('best_region', '') or '',
            'relationship_summary': enrichment.get('relationship_summary', '') or '',
            'relationship_type': enrichment.get('relationship_type', '') or '',
            'relationship_strength': strength,
            'key_topics': ', '.join(enrichment.get('key_topics', [])) if enrichment.get('key_topics') else '',
            'projects_in_common': ', '.join(enrichment.get('projects_in_common', [])) if enrichment.get('projects_in_common') else '',
            'notable_context': enrichment.get('notable_context', '') or '',
            'communication_style': enrichment.get('communication_style', '') or '',
            'total_emails': bundle.get('total_emails', 0),
            'emails_from': bundle.get('emails_from', 0),
            'emails_to': bundle.get('emails_to', 0),
            'first_contact': bundle.get('first_contact', '') or '',
            'last_contact': bundle.get('last_contact', '') or '',
            'communication_gap_days': gap_days if gap_days is not None else '',
            'co_correspondents': ', '.join(bundle.get('unique_subjects', [])[:5]) if not enrichment else '',
            'source_account': bundle.get('source_account', ''),
            'vault_page': matched.get('vault_match', '') or '',
            'vault_match_status': matched.get('vault_match_status', '') or '',
            'collector_type': crm.get('crm_collector_type', '') or '',
            'collector_priority': crm.get('crm_priority', '') or '',
            'total_purchases': crm.get('crm_net_sales', '') or '',
            'products_purchased': crm.get('crm_products', '') or '',
            'gc_website': gc.get('gc_website', '') or '',
            'gc_birthday': gc.get('gc_birthday', '') or '',
            'enrichment_tier': bundle.get('enrichment_tier', ''),
            'has_enrichment': bool(enrichment and 'error' not in enrichment),
        }
        rows.append(row)

    # Sort by relationship strength descending
    rows.sort(key=lambda r: r['relationship_strength'], reverse=True)

    # Write CSV
    fieldnames = [
        'name', 'email', 'phone', 'organization', 'role_title',
        'city', 'state', 'relationship_summary', 'relationship_type',
        'relationship_strength', 'key_topics', 'projects_in_common',
        'notable_context', 'communication_style',
        'total_emails', 'emails_from', 'emails_to',
        'first_contact', 'last_contact', 'communication_gap_days',
        'source_account', 'vault_page', 'vault_match_status',
        'collector_type', 'collector_priority', 'total_purchases',
        'products_purchased', 'gc_website', 'gc_birthday',
        'enrichment_tier', 'has_enrichment',
    ]

    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    # Also write drip-campaign-ready subset
    drip_path = output_csv.replace('.csv', '_drip.csv')
    drip_rows = [
        r for r in rows
        if r['relationship_strength'] >= 25
        and r.get('communication_gap_days', 9999) != ''
        and (isinstance(r.get('communication_gap_days'), int) and r['communication_gap_days'] < 730
             or r.get('communication_gap_days') == '')
    ]
    with open(drip_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(drip_rows)

    # Stats
    enriched_count = sum(1 for r in rows if r['has_enrichment'])
    with_phone = sum(1 for r in rows if r['phone'])
    with_org = sum(1 for r in rows if r['organization'])
    collectors = sum(1 for r in rows if r['collector_type'])
    vault_matched = sum(1 for r in rows if r['vault_page'])

    print(f"\n=== Master CSV Built ===")
    print(f"Total contacts: {len(rows)}")
    print(f"LLM-enriched: {enriched_count}")
    print(f"With phone: {with_phone}")
    print(f"With organization: {with_org}")
    print(f"Known collectors: {collectors}")
    print(f"Vault page matched: {vault_matched}")
    print(f"\nDrip campaign subset: {len(drip_rows)} contacts")
    print(f"\nRelationship strength distribution:")
    for threshold in [75, 50, 25, 10, 0]:
        count = sum(1 for r in rows if r['relationship_strength'] >= threshold)
        print(f"  {threshold}+: {count}")

    print(f"\nWritten: {output_csv}")
    print(f"Written: {drip_path}")

    # Top 20 by relationship strength
    print(f"\nTop 20 contacts by relationship strength:")
    for r in rows[:20]:
        print(f"  {r['relationship_strength']:>3}  {r['name']:<35} {r['relationship_type']:<15} {r['organization']}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build master Airtable-ready CSV')
    parser.add_argument('enriched_dir', help='Directory with enriched contact bundles')
    parser.add_argument('output_csv', help='Path for output CSV')
    args = parser.parse_args()

    build_master_csv(args.enriched_dir, args.output_csv)
