#!/usr/bin/env python3
"""
Phase 3: LLM-powered contact enrichment.

Reads contact bundles with email body snippets and uses Claude to generate
relationship summaries, role inference, topic extraction, and project mapping.

Tier A (10+ emails): Full enrichment with body content
Tier B (5-9 emails): Light enrichment (role + 1-line summary)
Tier C (1-4 emails): Skipped (metadata only)

Usage:
    python3 llm_enrich.py <bundles_dir> <enriched_dir> [--tier A] [--resume] [--dry-run]
"""

import json
import os
import glob
import time
import argparse
import sys

import anthropic

# Service/automated accounts that slipped through the Phase 1 filter
SKIP_EMAILS = {
    'support@earthclassmail.com', 'dse_na4@docusign.net',
    'messenger@messaging.squareup.com', 'messaging-service@post.xero.com',
}
SKIP_DOMAINS = [
    'reply2.squareup.com', 'brex.com', 'docusign.net',
    'squareup.com', 'xero.com', 'stripe.com',
]

def should_skip_enrichment(email_addr):
    if email_addr in SKIP_EMAILS:
        return True
    domain = email_addr.split('@')[-1] if '@' in email_addr else ''
    return any(domain.endswith(d) for d in SKIP_DOMAINS)

SYSTEM_PROMPT = """You are analyzing email correspondence between Jane Doe (also known as Your Handle / Your Artist Brand) and a contact. The user runs YourCompany Inc, an art-focused compound in Anytown, YS, and previously ran Your Artist Brand (YOURBRAND), a viral art brand. He also works on public art, real estate projects, and various creative ventures.

Based on the email excerpts and metadata provided, produce a structured JSON analysis of this contact's relationship to the user. Be specific and grounded in the actual email content — do not speculate beyond what the emails show.

Your response must be valid JSON with these fields:
{
  "role_title": "Their likely role/title (inferred from emails, signatures, context)",
  "relationship_type": "One of: collaborator, vendor, contractor, patron, collector, press, peer, family, friend, legal, financial, government, investor, unknown",
  "relationship_summary": "2-3 sentences describing who this person is and their relationship to the user, grounded in the email content",
  "key_topics": ["Up to 5 key topics discussed"],
  "projects_in_common": ["Specific projects mentioned (Your Company, YOURBRAND, Your Property, etc.)"],
  "notable_context": "One sentence of anything especially noteworthy about this relationship or person",
  "communication_style": "Brief note on their communication style if evident (responsive, formal, casual, etc.)"
}

Respond with ONLY the JSON object, no markdown formatting or explanation."""

SYSTEM_PROMPT_LIGHT = """You are analyzing email metadata about a contact of Jane Doe (Your Handle / Your Artist Brand). Based on the limited information provided (subject lines and basic metadata), produce a brief JSON analysis.

Your response must be valid JSON with these fields:
{
  "role_title": "Best guess at their role (or null if unclear)",
  "relationship_type": "One of: collaborator, vendor, contractor, patron, collector, press, peer, family, friend, legal, financial, government, investor, unknown",
  "relationship_summary": "One sentence describing the likely relationship",
  "key_topics": ["Up to 3 topics from subject lines"]
}

Respond with ONLY the JSON object, no markdown formatting or explanation."""


def build_tier_a_prompt(bundle):
    """Build prompt for full enrichment (contacts with 10+ emails)."""
    parts = [f"Contact: {bundle.get('display_names', ['Unknown'])[0] if bundle.get('display_names') else 'Unknown'}"]
    parts.append(f"Email: {bundle['email']}")

    if bundle.get('matched', {}).get('best_org'):
        parts.append(f"Organization: {bundle['matched']['best_org']}")
    if bundle.get('matched', {}).get('best_title'):
        parts.append(f"Title: {bundle['matched']['best_title']}")

    parts.append(f"Total emails: {bundle.get('total_emails', 0)}")
    parts.append(f"Emails from them: {bundle.get('emails_from', 0)}")
    parts.append(f"Emails to them: {bundle.get('emails_to', 0)}")
    parts.append(f"Date range: {bundle.get('first_contact', '?')} to {bundle.get('last_contact', '?')}")

    # Subject lines
    subjects = bundle.get('unique_subjects', [])[:15]
    if subjects:
        parts.append(f"\nSubject lines ({len(subjects)} of {len(bundle.get('unique_subjects', []))}):")
        for s in subjects:
            parts.append(f"  - {s}")

    # Email body snippets
    threads = bundle.get('threads', [])
    if threads:
        parts.append(f"\nEmail excerpts ({len(threads)} sampled):")
        for t in threads:
            direction = t.get('direction', '?')
            label = 'FROM them' if direction == 'from' else 'TO them (from the user)' if direction == 'to' else 'CC'
            parts.append(f"\n[{t.get('date', '?')}] {label} — Subject: {t.get('subject', '(no subject)')}")
            body = t.get('body_snippet', '')
            if body:
                # Truncate long bodies
                if len(body) > 800:
                    body = body[:800] + '...'
                parts.append(body)

    return '\n'.join(parts)


def build_tier_b_prompt(bundle):
    """Build prompt for light enrichment (contacts with 5-9 emails)."""
    parts = [f"Contact: {bundle.get('display_names', ['Unknown'])[0] if bundle.get('display_names') else 'Unknown'}"]
    parts.append(f"Email: {bundle['email']}")

    if bundle.get('matched', {}).get('best_org'):
        parts.append(f"Organization: {bundle['matched']['best_org']}")

    parts.append(f"Total emails: {bundle.get('total_emails', 0)}")
    parts.append(f"Date range: {bundle.get('first_contact', '?')} to {bundle.get('last_contact', '?')}")

    subjects = bundle.get('unique_subjects', [])[:10]
    if subjects:
        parts.append(f"\nSubject lines:")
        for s in subjects:
            parts.append(f"  - {s}")

    return '\n'.join(parts)


def enrich_batch(client, bundles, tier, model="claude-sonnet-4-20250514"):
    """Enrich a batch of contacts via API."""
    results = {}

    system = SYSTEM_PROMPT if tier == 'A' else SYSTEM_PROMPT_LIGHT

    for bundle in bundles:
        addr = bundle['email']
        prompt = build_tier_a_prompt(bundle) if tier == 'A' else build_tier_b_prompt(bundle)

        try:
            response = client.messages.create(
                model=model,
                max_tokens=500,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()
            # Strip markdown code fences if present
            if text.startswith('```'):
                text = text.split('\n', 1)[1] if '\n' in text else text[3:]
                if text.endswith('```'):
                    text = text[:-3]
                text = text.strip()

            enrichment = json.loads(text)
            results[addr] = enrichment

        except json.JSONDecodeError as e:
            print(f"  JSON parse error for {addr}: {e}")
            results[addr] = {'error': f'JSON parse error: {str(e)}', 'raw': text[:200]}
        except anthropic.RateLimitError:
            print(f"  Rate limited — waiting 30s...")
            time.sleep(30)
            # Retry once
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=500,
                    system=system,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = response.content[0].text.strip()
                if text.startswith('```'):
                    text = text.split('\n', 1)[1] if '\n' in text else text[3:]
                    if text.endswith('```'):
                        text = text[:-3]
                    text = text.strip()
                enrichment = json.loads(text)
                results[addr] = enrichment
            except Exception as e2:
                print(f"  Retry failed for {addr}: {e2}")
                results[addr] = {'error': str(e2)}
        except Exception as e:
            print(f"  Error for {addr}: {e}")
            results[addr] = {'error': str(e)}

        time.sleep(0.5)  # Rate limiting

    return results


def process_enrichment(bundles_dir, enriched_dir, tier_filter=None, resume=False, dry_run=False):
    client = anthropic.Anthropic()

    # Load all bundles
    bundle_files = sorted(glob.glob(os.path.join(bundles_dir, '*.json')))
    print(f"Found {len(bundle_files)} contact bundles")

    # Classify by tier
    tier_a = []
    tier_b = []
    tier_c = []

    for bf in bundle_files:
        with open(bf, 'r') as f:
            bundle = json.load(f)
        total = bundle.get('total_emails', 0)
        if total >= 10:
            tier_a.append((bf, bundle))
        elif total >= 3:
            tier_b.append((bf, bundle))
        else:
            tier_c.append((bf, bundle))

    print(f"Tier A (10+ emails): {len(tier_a)}")
    print(f"Tier B (5-9 emails): {len(tier_b)}")
    print(f"Tier C (1-4 emails): {len(tier_c)} (skipping LLM)")

    if dry_run:
        print("\n[DRY RUN] Would process:")
        if not tier_filter or tier_filter == 'A':
            print(f"  Tier A: {len(tier_a)} contacts")
        if not tier_filter or tier_filter == 'B':
            print(f"  Tier B: {len(tier_b)} contacts")
        return

    os.makedirs(enriched_dir, exist_ok=True)

    # Track already-enriched for resume
    already_done = set()
    if resume:
        for ef in glob.glob(os.path.join(enriched_dir, '*.json')):
            with open(ef, 'r') as f:
                data = json.load(f)
            if 'enrichment' in data and 'error' not in data.get('enrichment', {}):
                already_done.add(data.get('email', ''))
        print(f"Resuming — {len(already_done)} already enriched")

    # Process Tier A
    if not tier_filter or tier_filter == 'A':
        print(f"\n=== Processing Tier A ({len(tier_a)} contacts) ===")
        for i, (bf, bundle) in enumerate(tier_a):
            addr = bundle['email']
            if addr in already_done:
                continue
            if should_skip_enrichment(addr):
                print(f"  [{i+1}/{len(tier_a)}] SKIP (service): {addr}")
                continue

            print(f"  [{i+1}/{len(tier_a)}] {addr} ({bundle.get('total_emails', 0)} emails)...")
            results = enrich_batch(client, [bundle], 'A')

            if addr in results:
                bundle['enrichment'] = results[addr]
                bundle['enrichment_tier'] = 'A'

                safe_email = addr.replace('@', '_at_').replace('.', '_')
                out_path = os.path.join(enriched_dir, f"{safe_email}.json")
                with open(out_path, 'w') as f:
                    json.dump(bundle, f, indent=2, ensure_ascii=False)

                # Also update original bundle
                with open(bf, 'w') as f:
                    json.dump(bundle, f, indent=2, ensure_ascii=False)

            if (i + 1) % 25 == 0:
                print(f"  --- Checkpoint: {i+1}/{len(tier_a)} complete ---")

    # Process Tier B
    if not tier_filter or tier_filter == 'B':
        print(f"\n=== Processing Tier B ({len(tier_b)} contacts) ===")
        for i, (bf, bundle) in enumerate(tier_b):
            addr = bundle['email']
            if addr in already_done:
                continue
            if should_skip_enrichment(addr):
                print(f"  [{i+1}/{len(tier_b)}] SKIP (service): {addr}")
                continue

            print(f"  [{i+1}/{len(tier_b)}] {addr} ({bundle.get('total_emails', 0)} emails)...")
            results = enrich_batch(client, [bundle], 'B')

            if addr in results:
                bundle['enrichment'] = results[addr]
                bundle['enrichment_tier'] = 'B'

                safe_email = addr.replace('@', '_at_').replace('.', '_')
                out_path = os.path.join(enriched_dir, f"{safe_email}.json")
                with open(out_path, 'w') as f:
                    json.dump(bundle, f, indent=2, ensure_ascii=False)

                with open(bf, 'w') as f:
                    json.dump(bundle, f, indent=2, ensure_ascii=False)

            if (i + 1) % 25 == 0:
                print(f"  --- Checkpoint: {i+1}/{len(tier_b)} complete ---")

    # Tier C — just copy bundles to enriched dir with metadata tier
    if not tier_filter or tier_filter == 'C':
        print(f"\n=== Processing Tier C ({len(tier_c)} contacts, metadata only) ===")
        for bf, bundle in tier_c:
            bundle['enrichment_tier'] = 'C'
            bundle['enrichment'] = None
            safe_email = bundle['email'].replace('@', '_at_').replace('.', '_')
            out_path = os.path.join(enriched_dir, f"{safe_email}.json")
            with open(out_path, 'w') as f:
                json.dump(bundle, f, indent=2, ensure_ascii=False)

    # Final stats
    enriched_files = glob.glob(os.path.join(enriched_dir, '*.json'))
    enriched_with_data = 0
    errors = 0
    for ef in enriched_files:
        with open(ef, 'r') as f:
            data = json.load(f)
        if data.get('enrichment') and 'error' not in data.get('enrichment', {}):
            enriched_with_data += 1
        elif data.get('enrichment') and 'error' in data.get('enrichment', {}):
            errors += 1

    print(f"\n=== Enrichment Complete ===")
    print(f"Total enriched files: {len(enriched_files)}")
    print(f"Successfully enriched: {enriched_with_data}")
    print(f"Errors: {errors}")
    print(f"Metadata only (Tier C): {len(tier_c)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LLM-powered contact enrichment')
    parser.add_argument('bundles_dir', help='Directory with contact bundle JSON files')
    parser.add_argument('enriched_dir', help='Directory for enriched output')
    parser.add_argument('--tier', choices=['A', 'B'], help='Only process specific tier')
    parser.add_argument('--resume', action='store_true', help='Skip already-enriched contacts')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed')
    args = parser.parse_args()

    process_enrichment(args.bundles_dir, args.enriched_dir, args.tier, args.resume, args.dry_run)
