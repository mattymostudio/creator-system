#!/usr/bin/env python3
"""
Merge sub-agent enrichment results back into contact bundles,
then copy all bundles (enriched + Tier C metadata-only) to enriched_bundles/.

Usage:
    python3 merge_enrichments.py <bundles_dir> <enriched_dir>
"""

import json
import glob
import os
import sys
import shutil


def merge_enrichments(bundles_dir, enriched_dir):
    # Load all result files
    result_files = sorted(glob.glob(os.path.join(enriched_dir, 'results_*.json')))
    print(f"Found {len(result_files)} result files")

    # Build email -> enrichment lookup
    enrichments = {}
    for rf in result_files:
        with open(rf) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"  ERROR parsing {rf}: {e}")
                continue

        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict) and 'email' in entry:
                    enrichments[entry['email'].lower().strip()] = entry
        elif isinstance(data, dict):
            # Some agents may return a dict keyed by email
            for email, entry in data.items():
                enrichments[email.lower().strip()] = entry

    print(f"Total enrichments loaded: {len(enrichments)}")

    # Process each bundle
    bundle_files = sorted(glob.glob(os.path.join(bundles_dir, '*.json')))
    merged = 0
    unmatched = 0
    tier_c = 0

    for bf in bundle_files:
        with open(bf) as f:
            bundle = json.load(f)

        email = bundle['email'].lower().strip()
        total = bundle.get('total_emails', 0)

        # Determine tier
        if total >= 10:
            tier = 'A'
        elif total >= 3:
            tier = 'B'
        else:
            tier = 'C'

        # Try to find enrichment
        enrichment = enrichments.get(email)

        if enrichment:
            # Remove email field from enrichment (redundant)
            enrich_data = {k: v for k, v in enrichment.items() if k != 'email'}
            bundle['enrichment'] = enrich_data
            bundle['enrichment_tier'] = tier
            merged += 1
        elif tier in ('A', 'B'):
            # Should have been enriched but wasn't found
            bundle['enrichment'] = None
            bundle['enrichment_tier'] = tier
            unmatched += 1
        else:
            bundle['enrichment'] = None
            bundle['enrichment_tier'] = 'C'
            tier_c += 1

        # Write to enriched directory
        import hashlib
        safe_email = email.replace('@', '_at_').replace('.', '_').replace('/', '_').replace('\\', '_').replace(' ', '_')
        if len(safe_email) > 100 or '/' in email or '\\' in email or ' ' in email:
            safe_email = safe_email[:40] + '_' + hashlib.md5(email.encode()).hexdigest()[:12]
        out_path = os.path.join(enriched_dir, f"{safe_email}.json")
        with open(out_path, 'w') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)

        # Also update original bundle
        with open(bf, 'w') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)

    print(f"\nMerge complete:")
    print(f"  Enriched (A+B): {merged}")
    print(f"  Unmatched (expected enrichment but not found): {unmatched}")
    print(f"  Tier C (metadata only): {tier_c}")
    print(f"  Total bundles: {len(bundle_files)}")

    if unmatched > 0:
        # List the unmatched for debugging
        print(f"\n  Unmatched emails (first 20):")
        count = 0
        for bf in bundle_files:
            with open(bf) as f:
                b = json.load(f)
            if b.get('enrichment') is None and b.get('enrichment_tier') in ('A', 'B'):
                print(f"    {b['email']} (tier {b['enrichment_tier']}, {b.get('total_emails', 0)} emails)")
                count += 1
                if count >= 20:
                    break


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 merge_enrichments.py <bundles_dir> <enriched_dir>")
        sys.exit(1)

    merge_enrichments(sys.argv[1], sys.argv[2])
