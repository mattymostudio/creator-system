#!/usr/bin/env python3
"""
Timeline Reconstruction — extracts factual events from email threads
across all accounts and produces a chronological spine.

CONSTRAINT: Facts only. No assumptions. Every event cites source emails.
Events classified by evidence strength.

Usage:
    python3 build_timeline.py <bundles_dirs...> <output_dir>
"""

import json
import csv
import glob
import os
import sys
import re
from collections import defaultdict
from datetime import datetime


# Event signal patterns in subjects/bodies
EVENT_PATTERNS = [
    # Financial events
    (r'invoice|payment|paid|receipt|wire transfer|deposit|refund', 'financial'),
    (r'signed|executed|agreement|contract|nda|mou|term sheet', 'legal'),
    (r'purchased|bought|sold|sale|acquisition|closed', 'transaction'),
    # Project milestones
    (r'launch|launched|live|published|released|shipped|delivered', 'launch'),
    (r'approved|granted|permit|licensed|certified|accepted', 'approval'),
    (r'completed|finished|done|wrapped|final|delivered', 'completion'),
    (r'hired|started|joined|onboarded|welcome aboard', 'hiring'),
    (r'terminated|fired|resigned|departed|last day|offboarded', 'departure'),
    # Press/public
    (r'article|published|featured|interview|podcast|press|coverage', 'press'),
    (r'award|won|recognized|nominated|selected|chosen', 'recognition'),
    # Physical events
    (r'installed|built|constructed|erected|assembled|mounted', 'installation'),
    (r'moved|relocated|arrived|delivered|shipped', 'logistics'),
    (r'opened|grand opening|ribbon cutting|unveil', 'opening'),
    # Meetings/events
    (r'confirmed|booked|scheduled|rsvp|attending', 'scheduled'),
    (r'cancelled|postponed|rescheduled|declined', 'cancelled'),
]

MATTS_EMAILS = {
    'you@yourcompany.example', 'you@yourcompany.example',
    'you@yourdomain.example', 'you-personal@example.com',
    'you@yourcompany.example', 'your-handle@gmail.example',
    'you-work2@example.com', 'you-work3@example.com',
    'you-work4@example.com', 'you-sampleb@example.com',
    'you-work@example.com', 'info@yourdomain.example',
}


def classify_event_type(subject, body=''):
    """Classify what type of event a thread represents."""
    text = (subject + ' ' + body[:200]).lower()
    for pattern, event_type in EVENT_PATTERNS:
        if re.search(pattern, text):
            return event_type
    return None


def extract_events(bundle_dirs, output_dir):
    # Collect all threads with dates
    all_threads = []

    for bdir in bundle_dirs:
        for bf in sorted(glob.glob(os.path.join(bdir, '*.json'))):
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

            email = bundle['email']
            if email in MATTS_EMAILS:
                continue

            matched = bundle.get('matched', {})
            enrichment = bundle.get('enrichment') or {}
            name = matched.get('best_name', '')
            if not name and bundle.get('display_names'):
                name = bundle['display_names'][0]

            for thread in bundle.get('threads', []):
                date = thread.get('date')
                subject = thread.get('subject', '')
                body = thread.get('body_snippet', '')
                direction = thread.get('direction', '')

                if not date or not subject:
                    continue

                # Check if this thread contains an event signal
                event_type = classify_event_type(subject, body)
                if not event_type:
                    continue

                all_threads.append({
                    'date': date[:10] if date else '?',
                    'full_date': date,
                    'subject': subject,
                    'body_preview': body[:300] if body else '',
                    'event_type': event_type,
                    'contact_email': email,
                    'contact_name': name,
                    'direction': direction,
                    'source_account': bundle.get('source_account', '?'),
                    'relationship_type': enrichment.get('relationship_type', ''),
                    'projects': enrichment.get('projects_in_common', []) or [],
                })

    print(f"Extracted {len(all_threads)} event-signal threads")

    # Sort chronologically
    all_threads.sort(key=lambda t: t.get('full_date') or '0')

    # Deduplicate similar events (same date + similar subject)
    deduped = []
    seen_keys = set()
    for t in all_threads:
        # Create dedup key from date + normalized subject
        norm_subj = re.sub(r'^(re:|fwd:|fw:)\s*', '', t['subject'].lower()).strip()[:40]
        key = f"{t['date']}:{norm_subj}"
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(t)

    print(f"After deduplication: {len(deduped)} events")

    # Classify evidence strength
    # For now, all events are 'single_source' since we're extracting from one thread
    # Cross-referencing (checking if the event is confirmed by later emails) would
    # require a more complex pass that reads subsequent threads — flagged for follow-up
    for t in deduped:
        t['evidence_strength'] = 'single_source'

    # Write timeline CSV
    csv_path = os.path.join(output_dir, 'timeline_events.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'date', 'event_type', 'subject', 'contact_name', 'contact_email',
            'direction', 'source_account', 'relationship_type',
            'projects', 'evidence_strength', 'body_preview'
        ])
        writer.writeheader()
        for t in deduped:
            writer.writerow({
                'date': t['date'],
                'event_type': t['event_type'],
                'subject': t['subject'][:120],
                'contact_name': t['contact_name'],
                'contact_email': t['contact_email'],
                'direction': t['direction'],
                'source_account': t['source_account'],
                'relationship_type': t['relationship_type'],
                'projects': ', '.join(t['projects']) if t['projects'] else '',
                'evidence_strength': t['evidence_strength'],
                'body_preview': t['body_preview'][:200],
            })

    # Write timeline markdown
    md_path = os.path.join(output_dir, 'Email Timeline (2008-2026).md')
    lines = []
    lines.append('---')
    lines.append('type: output')
    lines.append('status: draft')
    lines.append('format: timeline')
    lines.append(f'date: {datetime.now().strftime("%Y-%m-%d")}')
    lines.append('project: Documentary')
    lines.append('---')
    lines.append('')
    lines.append('# Email Timeline (2008-2026)')
    lines.append('')
    lines.append('Factual events extracted from email correspondence across yourcompany, YOURBRAND, and personal accounts.')
    lines.append('**Evidence basis:** Each event cites the specific email thread it derives from.')
    lines.append(f'**Total events:** {len(deduped)}')
    lines.append('')
    lines.append('> **Evidence strength key:**')
    lines.append('> - `confirmed` = verified by multiple emails or follow-up correspondence')
    lines.append('> - `single_source` = one email thread references this event')
    lines.append('> - `planned_unverified` = discussed but no confirmation found')
    lines.append('')
    lines.append('---')
    lines.append('')

    # Group by year
    by_year = defaultdict(list)
    for t in deduped:
        try:
            year = t['date'][:4]
        except:
            year = '????'
        by_year[year].append(t)

    for year in sorted(by_year.keys()):
        events = by_year[year]
        lines.append(f'## {year}')
        lines.append('')

        # Group by month
        by_month = defaultdict(list)
        for e in events:
            month = e['date'][:7] if len(e['date']) >= 7 else year
            by_month[month].append(e)

        for month in sorted(by_month.keys()):
            month_events = by_month[month]
            lines.append(f'### {month}')
            lines.append('')

            for e in month_events[:30]:  # Cap per month to avoid overwhelming output
                icon = {
                    'financial': '$',
                    'legal': 'L',
                    'transaction': 'T',
                    'launch': 'R',
                    'approval': 'A',
                    'completion': 'C',
                    'hiring': 'H',
                    'departure': 'D',
                    'press': 'P',
                    'recognition': 'W',
                    'installation': 'I',
                    'logistics': 'M',
                    'opening': 'O',
                    'scheduled': 'S',
                    'cancelled': 'X',
                }.get(e['event_type'], '?')

                lines.append(f'- `[{icon}]` **{e["date"]}** — {e["subject"][:100]}')
                lines.append(f'  - Contact: {e["contact_name"]} ({e["contact_email"]})')
                lines.append(f'  - Evidence: {e["evidence_strength"]} | Source: {e["source_account"]}')
                if e['projects']:
                    lines.append(f'  - Projects: {", ".join(e["projects"])}')

            lines.append('')

    # Stats
    type_counts = defaultdict(int)
    for e in deduped:
        type_counts[e['event_type']] += 1

    lines.append('## Event Type Summary')
    lines.append('')
    lines.append('| Type | Count |')
    lines.append('|------|-------|')
    for etype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f'| {etype} | {count} |')
    lines.append('')

    with open(md_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"\nWritten:")
    print(f"  {csv_path} ({len(deduped)} events)")
    print(f"  {md_path}")

    # Year distribution
    print(f"\nEvents by year:")
    for year in sorted(by_year.keys()):
        print(f"  {year}: {len(by_year[year])}")

    print(f"\nEvent types:")
    for etype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {etype}: {count}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 build_timeline.py <bundles_dir1> [dir2...] <output_dir>")
        sys.exit(1)

    bundle_dirs = sys.argv[1:-1]
    output_dir = sys.argv[-1]
    os.makedirs(output_dir, exist_ok=True)
    extract_events(bundle_dirs, output_dir)
