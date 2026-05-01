#!/usr/bin/env python3
"""
Merge and deduplicate master contact CSVs across all three email accounts.
Deduplicates on email address, keeping the richest enrichment data.

Usage:
    python3 merge_dedup_csvs.py <csv1> <csv2> [csv3...] <output_csv>
"""

import csv
import sys
import os
from collections import defaultdict


def merge_csvs(input_csvs, output_csv):
    # Read all CSVs
    all_rows = []
    fieldnames = set()

    for csv_path in input_csvs:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames.update(reader.fieldnames or [])
            for row in reader:
                all_rows.append(row)

    print(f"Total rows across all CSVs: {len(all_rows)}")

    # Deduplicate on email
    by_email = defaultdict(list)
    for row in all_rows:
        email = row.get('email', '').lower().strip()
        if email:
            by_email[email].append(row)

    print(f"Unique emails: {len(by_email)}")
    print(f"Duplicates: {len(all_rows) - len(by_email)}")

    # For each email, pick the best row (richest data) and merge
    merged_rows = []
    for email, rows in by_email.items():
        if len(rows) == 1:
            best = rows[0]
            best['source_accounts'] = best.get('source_account', '')
        else:
            # Merge: pick row with enrichment, combine metadata
            rows_with_enrichment = [r for r in rows if r.get('has_enrichment') == 'True']
            best = rows_with_enrichment[0] if rows_with_enrichment else rows[0]

            # Combine source accounts
            accounts = set()
            total_emails = 0
            earliest_first = '9999'
            latest_last = '0000'

            for r in rows:
                accounts.add(r.get('source_account', ''))
                try:
                    total_emails += int(r.get('total_emails', 0))
                except:
                    pass
                fc = r.get('first_contact', '')
                lc = r.get('last_contact', '')
                if fc and fc < earliest_first:
                    earliest_first = fc
                if lc and lc > latest_last:
                    latest_last = lc

                # Fill in blanks from other rows
                for key in ['name', 'phone', 'organization', 'role_title', 'city', 'state',
                            'relationship_summary', 'relationship_type', 'key_topics',
                            'projects_in_common', 'notable_context', 'communication_style',
                            'vault_page', 'collector_type', 'total_purchases', 'gc_website']:
                    if not best.get(key) and r.get(key):
                        best[key] = r[key]

            best['source_accounts'] = ', '.join(sorted(accounts))
            best['total_emails'] = str(total_emails)
            best['first_contact'] = earliest_first if earliest_first != '9999' else ''
            best['last_contact'] = latest_last if latest_last != '0000' else ''

        merged_rows.append(best)

    # Sort by relationship_strength descending
    def get_strength(r):
        try:
            return int(r.get('relationship_strength', 0))
        except:
            return 0

    merged_rows.sort(key=get_strength, reverse=True)

    # Ensure source_accounts is in fieldnames
    fieldnames.add('source_accounts')
    # Remove source_account (singular) from output
    fieldnames.discard('source_account')

    # Order fieldnames sensibly
    ordered_fields = [
        'name', 'email', 'phone', 'organization', 'role_title',
        'city', 'state', 'relationship_summary', 'relationship_type',
        'relationship_strength', 'key_topics', 'projects_in_common',
        'notable_context', 'communication_style',
        'total_emails', 'emails_from', 'emails_to',
        'first_contact', 'last_contact', 'communication_gap_days',
        'source_accounts', 'vault_page', 'vault_match_status',
        'collector_type', 'collector_priority', 'total_purchases',
        'products_purchased', 'gc_website', 'gc_birthday',
        'enrichment_tier', 'has_enrichment',
    ]
    # Add any fields we missed
    for f in sorted(fieldnames):
        if f not in ordered_fields:
            ordered_fields.append(f)

    # Write merged CSV
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=ordered_fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(merged_rows)

    # Stats
    enriched = sum(1 for r in merged_rows if r.get('has_enrichment') == 'True')
    with_phone = sum(1 for r in merged_rows if r.get('phone'))
    multi_account = sum(1 for r in merged_rows if ',' in r.get('source_accounts', ''))
    with_vault = sum(1 for r in merged_rows if r.get('vault_page'))

    print(f"\n=== Merged CSV ===")
    print(f"Total unique contacts: {len(merged_rows)}")
    print(f"LLM-enriched: {enriched}")
    print(f"With phone: {with_phone}")
    print(f"Multi-account contacts: {multi_account}")
    print(f"With vault page: {with_vault}")
    print(f"\nWritten: {output_csv}")

    # Top 20 multi-account contacts
    multi = [r for r in merged_rows if ',' in r.get('source_accounts', '')]
    multi.sort(key=get_strength, reverse=True)
    if multi:
        print(f"\nTop 20 multi-account contacts (appear in multiple email accounts):")
        for r in multi[:20]:
            print(f"  {get_strength(r):>3} str  {r.get('total_emails', '?'):>5} em  {r.get('name', ''):<35} {r.get('source_accounts', '')}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 merge_dedup_csvs.py <csv1> <csv2> [csv3...] <output_csv>")
        sys.exit(1)

    input_csvs = sys.argv[1:-1]
    output_csv = sys.argv[-1]
    merge_csvs(input_csvs, output_csv)
