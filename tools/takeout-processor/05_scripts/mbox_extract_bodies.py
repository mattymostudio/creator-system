#!/usr/bin/env python3
"""
Phase 1: Extract email bodies per contact from MBOX files.

Streams a Google Takeout MBOX, filters to human correspondence,
extracts plain-text bodies, and outputs one JSON bundle per contact.

Usage:
    python3 mbox_extract_bodies.py <mbox_path> <contacts_csv> <output_dir> [--source-account yourcompany]

The contacts CSV should have at minimum an 'email' column.
Output is one JSON file per contact in output_dir.
"""

import mailbox
import email.utils
import email.header
import csv
import json
import re
import sys
import os
import argparse
from collections import defaultdict
from datetime import datetime
from html.parser import HTMLParser


# --- Configuration ---

# the user's known email addresses (excluded from contact list)
MATTS_EMAILS = {
    'you@yourcompany.example', 'you@yourcompany.example',
    'you@yourdomain.example', 'you-personal@example.com',
    'you@yourcompany.example', 'your-handle@gmail.example',
}

# Automation filter patterns
NOREPLY_PATTERNS = [
    'noreply', 'no-reply', 'donotreply', 'notifications@',
    'mailer-daemon', 'automated@', 'marketing@', 'updates@',
    'hello@send.', 'mail@email.', 'editor@members.', 'hi@marketing.',
    'pkginfo@', 'drive-shares', 'workspace-noreply',
    'businessprofile-noreply', 'account-services', 'gustonoreply',
]

BULK_DOMAINS = [
    'hipcamp.com', 'send.hipcamp.com', 'e.stripe.com',
    'crateandbarrel.com', 'mail.crateandbarrel.com',
    'inform.bill.com', 'email.adobe.com', 'e2.overtons.com',
    'email.eastwood.com', 'members.wayfair.com', 'redditmail.com',
    'mail.coinbase.com', 'comm.vosker.com', 'marketing.hipcamp.com',
    'e.newyorktimes.com', 'ccsend.com', 'beehiiv.com',
    'convertkit.com', 'shopify.com', 'klaviyo.com',
    'facebookmail.com', 'marketing.com',
]

# Sampling config
MAX_BODY_CHARS_PER_EMAIL = 2000
MAX_BUNDLE_CHARS = 50000
MAX_EMAILS_FULL = 20  # Include all if contact has fewer than this
SAMPLE_FIRST = 5
SAMPLE_LAST = 5
SAMPLE_MIDDLE = 10

# Signature extraction patterns
PHONE_RE = re.compile(
    r'(?:(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4})'
)
TITLE_RE = re.compile(
    r'^(?:(?:CEO|CTO|CFO|COO|VP|Director|Manager|Partner|Attorney|'
    r'Architect|Engineer|Designer|Founder|President|Principal|'
    r'Associate|Consultant|Advisor|Agent|Broker|Editor|Producer|'
    r'Curator|Professor|Dr\.|PhD)[\w\s,/&-]*)',
    re.IGNORECASE | re.MULTILINE
)


# --- HTML Stripping ---

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script'):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ('style', 'script'):
            self._skip = False
        if tag in ('p', 'div', 'br', 'tr', 'li', 'h1', 'h2', 'h3', 'h4'):
            self.result.append('\n')

    def handle_data(self, data):
        if not self._skip:
            self.result.append(data)

    def get_text(self):
        return ''.join(self.result)


def strip_html(html_str):
    extractor = HTMLTextExtractor()
    try:
        extractor.feed(html_str)
        return extractor.get_text()
    except Exception:
        return html_str


# --- Email Parsing Utilities ---

def safe_str(val):
    if val is None:
        return ''
    try:
        if hasattr(val, 'defects'):
            decoded = email.header.decode_header(str(val))
            parts = []
            for text, charset in decoded:
                if isinstance(text, bytes):
                    parts.append(text.decode(charset or 'utf-8', errors='replace'))
                else:
                    parts.append(text)
            return ' '.join(parts)
        return str(val)
    except Exception:
        return str(val)


def parse_date(msg):
    date_str = safe_str(msg.get('Date', ''))
    if not date_str:
        return None
    try:
        parsed = email.utils.parsedate_tz(date_str)
        if parsed:
            return datetime(*parsed[:6])
    except Exception:
        pass
    return None


def extract_addresses(header_val):
    if not header_val:
        return []
    header_str = safe_str(header_val)
    results = []
    for part in header_str.split(','):
        name, addr = email.utils.parseaddr(part.strip())
        if addr:
            results.append((name.strip(), addr.lower().strip()))
    return results


def is_automated_msg(msg, from_email):
    from_lower = from_email.lower()
    from_domain = from_lower.split('@')[-1] if '@' in from_lower else ''

    for p in NOREPLY_PATTERNS:
        if p in from_lower:
            return True
    for d in BULK_DOMAINS:
        if from_domain.endswith(d):
            return True
    if msg.get('List-Unsubscribe'):
        return True
    if safe_str(msg.get('Precedence', '')).lower() in ('bulk', 'list', 'junk'):
        return True
    return False


def get_body_text(msg, max_chars=MAX_BODY_CHARS_PER_EMAIL):
    """Extract plain text body from a message."""
    try:
        if msg.is_multipart():
            # Prefer text/plain
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == 'text/plain':
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        return payload.decode(charset, errors='replace')[:max_chars]
            # Fallback to text/html stripped
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == 'text/html':
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        html = payload.decode(charset, errors='replace')
                        return strip_html(html)[:max_chars]
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                text = payload.decode(charset, errors='replace')
                if msg.get_content_type() == 'text/html':
                    text = strip_html(text)
                return text[:max_chars]
    except Exception:
        pass
    return ''


def strip_quoted_replies(text):
    """Remove quoted reply chains from email body."""
    lines = text.split('\n')
    cleaned = []
    in_quote = False

    for line in lines:
        stripped = line.strip()
        # Detect "On ... wrote:" patterns
        if re.match(r'^On .+ wrote:$', stripped):
            break
        if re.match(r'^-{3,}\s*Original Message\s*-{3,}', stripped, re.IGNORECASE):
            break
        if re.match(r'^From:\s+', stripped) and any(
            re.match(r'^(Sent|Date|To|Subject):\s+', lines[i].strip())
            for i in range(lines.index(line) + 1, min(lines.index(line) + 4, len(lines)))
            if lines[i].strip()
        ):
            break
        # Skip quoted lines
        if stripped.startswith('>'):
            in_quote = True
            continue
        if in_quote and not stripped:
            continue
        in_quote = False
        cleaned.append(line)

    return '\n'.join(cleaned).strip()


def extract_signature_info(text):
    """Extract phone number and title from email signature area."""
    # Look at last 10 lines for signature content
    lines = text.strip().split('\n')
    sig_area = '\n'.join(lines[-15:]) if len(lines) > 15 else text

    phone = None
    title = None

    # Find phone numbers
    phone_matches = PHONE_RE.findall(sig_area)
    if phone_matches:
        # Take the first one that looks real (7+ digits)
        for p in phone_matches:
            digits = re.sub(r'\D', '', p)
            if len(digits) >= 7:
                phone = p.strip()
                break

    # Look for title after a "--" or similar separator
    sig_start = -1
    for i, line in enumerate(lines):
        if line.strip() in ('--', '---', '—'):
            sig_start = i
            break

    if sig_start >= 0:
        sig_lines = lines[sig_start + 1:]
        for line in sig_lines:
            line = line.strip()
            if line and not PHONE_RE.search(line) and not '@' in line:
                match = TITLE_RE.match(line)
                if match:
                    title = match.group(0).strip()
                    break

    return phone, title


# --- Main Processing ---

def process_mbox(mbox_path, contacts_csv, output_dir, source_account='yourcompany'):
    # Load known contacts
    known_contacts = set()
    with open(contacts_csv, 'r') as f:
        for row in csv.DictReader(f):
            known_contacts.add(row['email'].lower().strip())

    print(f"Loaded {len(known_contacts)} contacts from CSV")
    print(f"Opening MBOX: {mbox_path}")

    mbox = mailbox.mbox(mbox_path)

    # Accumulate per contact
    contact_emails = defaultdict(list)
    contact_names = defaultdict(set)
    total = 0
    human = 0
    skipped_auto = 0

    for msg in mbox:
        total += 1
        if total % 5000 == 0:
            print(f"  ...processed {total} messages ({human} human)")

        from_name, from_email = email.utils.parseaddr(safe_str(msg.get('From', '')))
        from_email = from_email.lower().strip()

        if is_automated_msg(msg, from_email):
            skipped_auto += 1
            continue

        human += 1
        dt = parse_date(msg)
        subject = safe_str(msg.get('Subject', ''))

        # Get all participants
        all_addrs = set()
        all_addrs.add(from_email)
        for h in ['To', 'Cc']:
            for name, addr in extract_addresses(msg.get(h, '')):
                all_addrs.add(addr)
                if addr in known_contacts and addr not in MATTS_EMAILS:
                    contact_names[addr].add(name) if name else None

        if from_email in known_contacts and from_email not in MATTS_EMAILS:
            if from_name:
                contact_names[from_email].add(from_name)

        # Extract body for emails FROM contacts (their voice)
        body = ''
        phone_sig = None
        title_sig = None
        if from_email in known_contacts and from_email not in MATTS_EMAILS:
            raw_body = get_body_text(msg)
            if raw_body and len(raw_body) > 30:
                body = strip_quoted_replies(raw_body)
                phone_sig, title_sig = extract_signature_info(raw_body)

        # Also extract body for emails FROM the user TO contacts (context)
        if from_email in MATTS_EMAILS:
            raw_body = get_body_text(msg)
            if raw_body and len(raw_body) > 30:
                body = strip_quoted_replies(raw_body)

        # Assign this email to relevant contacts
        relevant = (all_addrs & known_contacts) - MATTS_EMAILS
        for addr in relevant:
            direction = 'from' if from_email == addr else 'to' if from_email in MATTS_EMAILS else 'cc'
            contact_emails[addr].append({
                'date': dt.isoformat() if dt else None,
                'subject': subject,
                'direction': direction,
                'body': body if (from_email == addr or from_email in MATTS_EMAILS) else '',
                'phone_sig': phone_sig if from_email == addr else None,
                'title_sig': title_sig if from_email == addr else None,
            })

    print(f"\nDone scanning. Total: {total}, Human: {human}, Auto-filtered: {skipped_auto}")
    print(f"Contacts with emails: {len(contact_emails)}")

    # Now sample and write bundles
    bundles_written = 0
    for addr, emails in contact_emails.items():
        # Sort by date
        emails.sort(key=lambda e: e['date'] or '0')

        # Filter to emails with body content for sampling
        with_body = [e for e in emails if e.get('body') and len(e['body']) > 30]
        without_body = [e for e in emails if not e.get('body') or len(e['body']) <= 30]

        # Sample body emails
        if len(with_body) <= MAX_EMAILS_FULL:
            sampled = with_body
        else:
            first = with_body[:SAMPLE_FIRST]
            last = with_body[-SAMPLE_LAST:]
            middle_pool = with_body[SAMPLE_FIRST:-SAMPLE_LAST]
            # Evenly sample from middle
            step = max(1, len(middle_pool) // SAMPLE_MIDDLE)
            middle = middle_pool[::step][:SAMPLE_MIDDLE]
            # Also include the longest email
            longest = max(with_body, key=lambda e: len(e.get('body', '')))
            sampled = list({id(e): e for e in (first + middle + last + [longest])}.values())
            sampled.sort(key=lambda e: e['date'] or '0')

        # Cap total body chars
        total_chars = 0
        final_sampled = []
        for e in sampled:
            body_len = len(e.get('body', ''))
            if total_chars + body_len > MAX_BUNDLE_CHARS:
                e = {**e, 'body': e['body'][:MAX_BUNDLE_CHARS - total_chars]}
                final_sampled.append(e)
                break
            final_sampled.append(e)
            total_chars += body_len

        # Extract signature info across all emails from this contact
        phones = set()
        titles = set()
        for e in emails:
            if e.get('phone_sig'):
                phones.add(e['phone_sig'])
            if e.get('title_sig'):
                titles.add(e['title_sig'])

        # Get unique subjects for metadata
        all_subjects = list(dict.fromkeys(e['subject'] for e in emails if e.get('subject')))

        # Clean names
        names = contact_names.get(addr, set())
        clean_names = [n for n in names if n and not n.startswith('=?') and len(n) > 1]

        # Count directions
        from_count = sum(1 for e in emails if e['direction'] == 'from')
        to_count = sum(1 for e in emails if e['direction'] == 'to')
        cc_count = sum(1 for e in emails if e['direction'] == 'cc')

        dates = [e['date'] for e in emails if e['date']]

        bundle = {
            'email': addr,
            'display_names': sorted(clean_names, key=len, reverse=True) if clean_names else [],
            'total_emails': len(emails),
            'emails_sampled': len(final_sampled),
            'emails_from': from_count,
            'emails_to': to_count,
            'emails_cc': cc_count,
            'first_contact': min(dates) if dates else None,
            'last_contact': max(dates) if dates else None,
            'phones_from_sig': sorted(phones),
            'titles_from_sig': sorted(titles),
            'unique_subjects': all_subjects[:30],
            'source_account': source_account,
            'threads': [
                {
                    'date': e['date'],
                    'subject': e['subject'],
                    'direction': e['direction'],
                    'body_snippet': e['body'],
                }
                for e in final_sampled
                if e.get('body')
            ],
        }

        # Write bundle
        import hashlib
        safe_email = addr.replace('@', '_at_').replace('.', '_').replace('/', '_').replace('\\', '_').replace(' ', '_')
        # Truncate long filenames or ones with path-unsafe chars
        if len(safe_email) > 100 or '/' in addr or '\\' in addr or ' ' in addr:
            safe_email = safe_email[:40] + '_' + hashlib.md5(addr.encode()).hexdigest()[:12]
        out_path = os.path.join(output_dir, f"{safe_email}.json")
        with open(out_path, 'w') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)
        bundles_written += 1

    print(f"Bundles written: {bundles_written}")

    # Summary stats
    tier_a = sum(1 for e in contact_emails.values() if len(e) >= 10)
    tier_b = sum(1 for e in contact_emails.values() if 5 <= len(e) < 10)
    tier_c = sum(1 for e in contact_emails.values() if len(e) < 5)
    print(f"\nEnrichment tiers:")
    print(f"  Tier A (10+ emails): {tier_a}")
    print(f"  Tier B (5-9 emails): {tier_b}")
    print(f"  Tier C (1-4 emails): {tier_c}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract email bodies per contact from MBOX')
    parser.add_argument('mbox_path', help='Path to the MBOX file')
    parser.add_argument('contacts_csv', help='Path to clean contacts CSV (needs email column)')
    parser.add_argument('output_dir', help='Directory to write contact bundle JSON files')
    parser.add_argument('--source-account', default='yourcompany', help='Account label (default: yourcompany)')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    process_mbox(args.mbox_path, args.contacts_csv, args.output_dir, args.source_account)
