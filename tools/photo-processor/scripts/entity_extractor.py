#!/usr/bin/env python3
"""
Entity Extractor — pulls structured, actionable data from OCR text.

Extracts: phone numbers, emails, URLs, @handles, dates, prices,
addresses, stock tickers, to-do items, quotes, contact names.
"""

import re
from collections import OrderedDict


# iOS screenshot chrome patterns to strip before extraction
IOS_CHROME_PATTERNS = [
    r'^\d{1,2}:\d{2}\s*[=\-]?\s*[ao]?[lti!]*\s*(?:5G\+?|LTE|4G|Wi-?Fi)\s*[@&GC()\s]*',  # status bar
    r'\b[aA]{2}\s*[@&]\s*$',  # Safari URL bar "aA @"
    r'^[A-Z]\s+Q\s+[GCS©()\s]+$',  # bottom nav "A Q G) @"
    r'^[A-Z]\s+[CQ]\s+[©()\s]+\s*[pP@]?\s*$',  # bottom nav variations
    r'^\s*(ft|Home)\s+(Friends\s+)?(Inbox\s+)?Profile\s*$',  # TikTok nav
    r'^\s*©?\s*\d*\s*$',  # isolated numbers/symbols
]

# Compile patterns
_chrome_re = [re.compile(p, re.MULTILINE | re.IGNORECASE) for p in IOS_CHROME_PATTERNS]


def clean_ocr_text(text):
    """Strip common iOS screenshot chrome/noise from OCR text."""
    if not text:
        return ''

    # Remove lines that are purely chrome
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        is_chrome = False
        for pattern in _chrome_re:
            if pattern.fullmatch(stripped):
                is_chrome = True
                break
        if not is_chrome:
            cleaned.append(line)

    return '\n'.join(cleaned)


# ── Extraction patterns ──

PHONE_RE = re.compile(
    r'(?<!\d)'                          # not preceded by digit
    r'(?:\+?1[\s.-]?)?'                 # optional country code
    r'(?:\(\d{3}\)|\d{3})'             # area code
    r'[\s.\-]?'
    r'\d{3}'                            # exchange
    r'[\s.\-]?'
    r'\d{4}'                            # subscriber
    r'(?!\d)',                           # not followed by digit
    re.MULTILINE
)

EMAIL_RE = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE
)

URL_RE = re.compile(
    r'https?://[^\s<>"\')\]]+|'
    r'(?:www\.)[^\s<>"\')\]]+|'
    r'[a-zA-Z0-9][\w\-]*\.(?:com|org|net|io|co|app|dev|me|xyz|info|art|design|shop|store|gallery)[^\s<>"\')\],]*',
    re.IGNORECASE
)

HANDLE_RE = re.compile(
    r'@([a-zA-Z0-9_.]{3,30})\b'
)

DATE_RE = re.compile(
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|'
    r'Dec(?:ember)?)\s+\d{1,2}(?:,?\s+\d{4})?|'
    r'\d{1,2}/\d{1,2}/\d{2,4}|'
    r'\d{4}[\-/]\d{2}[\-/]\d{2}',
    re.IGNORECASE
)

PRICE_RE = re.compile(
    r'\$[\d,]+\.?\d{0,2}(?:K|M|B)?'
)

ADDRESS_RE = re.compile(
    r'\d{1,5}\s+(?:[NSEW]\.?\s+)?(?:\w+\s+){1,4}'
    r'(?:Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Road|Rd|Lane|Ln|Way|'
    r'Court|Ct|Place|Pl|Circle|Cir|Highway|Hwy|Route|Rte)'
    r'(?:\s*(?:#|Suite|Ste|Apt|Unit)\s*\w+)?'
    r'(?:,\s*[\w\s]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)?',
    re.IGNORECASE
)

TICKER_RE = re.compile(
    r'\$([A-Z]{2,5})\b'
)

TODO_RE = re.compile(
    r'(?:^|\n)\s*(?:[-•*✓☐□]|\d+[.)]\s)'  # bullet/numbered list items
    r'\s*(.{10,100})',
    re.MULTILINE
)

TODO_KEYWORD_RE = re.compile(
    r'(?:need to|have to|must|should|don\'t forget|remind me|'
    r'to[- ]?do|buy|call|book|schedule|pick up|drop off|'
    r'sign up|apply|register|cancel|renew|return|send|submit)'
    r'\s+(.{5,100})',
    re.IGNORECASE
)

QUOTE_RE = re.compile(
    r'(?:^|\n)\s*["""](.{30,300})["""]',
    re.MULTILINE
)

# Product patterns — brand + model, or "product name" near a price
PRODUCT_RE = re.compile(
    r'(?:'
    # Brand + model patterns (Salomon XT-6, iPhone 16, Ray-Ban Meta, etc.)
    r'(?:Salomon|Nike|Adidas|New Balance|Yeezy|Jordan|Puma|Asics|Vans|Converse'
    r'|Apple|Samsung|Google Pixel|iPhone|iPad|MacBook|AirPods'
    r'|Ray-Ban|Oakley|Gucci|Louis Vuitton|Prada|Balenciaga|Supreme'
    r'|Tesla|Porsche|BMW|Mercedes|Toyota|Honda|Ford|Rivian|Slate'
    r'|DJI|GoPro|Canon|Sony|Nikon|Fujifilm'
    r'|SHERP|Berkley|Bavaria'
    r')\s+[\w\-]+(?:\s+[\w\-]+)?'
    r'|'
    # Generic "Product Name" near a price
    r'(?<=\n)([A-Z][\w\s\-]{5,40}?)(?=\s+\$\d)'
    r')',
    re.IGNORECASE
)

# Service patterns — business names, reservations, subscriptions
SERVICE_KEYWORDS = re.compile(
    r'(?:'
    r'(?:reservation|booking|appointment|check-?in|check-?out)'
    r'|(?:subscription|membership|plan|trial|premium)'
    r'|(?:order\s*#?\s*\d+|invoice|receipt)'
    r'|(?:dine-in|delivery|pickup|takeout)'
    r')',
    re.IGNORECASE
)

# Business name pattern — typically appears near addresses, orders, or "billed to"
BUSINESS_RE = re.compile(
    r'(?:'
    # After "BILLED TO:" — capture the name
    r'BILLED TO:\s*\n?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})'
    r'|'
    # Restaurant/venue names (Capitalized, 2-5 words before "Reservation/Restaurant/Studio/Gallery")
    r'([A-Z][\w]+(?:\s+[A-Z][\w]+){0,4})\s+(?:Reservation|Restaurant|Studio|Gallery|Hotel|Resort|Retreat|Bar|Cafe|Museum|Theater|Theatre)'
    r'|'
    # "Order from [Business]" or "[Business]: A New Order"
    r'(?:order from|ordered from)\s+([A-Z][\w]+(?:\s+[\w]+){0,3})'
    r')',
    re.MULTILINE
)

# People name patterns — more aggressive than contacts
PERSON_NAME_RE = re.compile(
    r'(?:'
    # "Liked by [name]" pattern
    r'Liked by\s+(\w+)'
    r'|'
    # "Followed by [name]" pattern
    r'Followed by\s+(\w+)'
    r'|'
    # "@handle Name" or "handle Name" profile pattern
    r'@(\w{3,20})\s+(?:Follow|Following)'
    r'|'
    # "BILLED TO: First Last"
    r'BILLED TO:\s*\n?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)'
    r'|'
    # Names in message headers (First Last pattern at start of line)
    r'^([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})(?:\s|$)'
    r')',
    re.MULTILINE
)


def _dedup_preserve_order(items):
    """Deduplicate list while preserving order."""
    seen = set()
    result = []
    for item in items:
        normalized = item.strip().lower()
        if normalized not in seen and len(normalized) > 1:
            seen.add(normalized)
            result.append(item.strip())
    return result


def _filter_false_positive_phones(phones, text):
    """Filter out numbers that are likely dates, zip codes, or metrics."""
    filtered = []
    for phone in phones:
        digits = re.sub(r'\D', '', phone)
        # Skip if it's too short or too long
        if len(digits) < 7 or len(digits) > 11:
            continue
        # Skip if it looks like a year range
        if re.match(r'^\d{4}$', digits):
            continue
        # Skip common false positives from engagement metrics
        if re.search(r'(?:followers?|following|posts?|likes?|views?)\s*' + re.escape(phone), text, re.IGNORECASE):
            continue
        filtered.append(phone)
    return filtered


def _filter_false_positive_urls(urls):
    """Filter out OCR noise that looks like URLs."""
    filtered = []
    noise = {'more', 'the', 'and', 'for', 'you', 'all', 'see'}
    for url in urls:
        # Skip very short
        if len(url) < 6:
            continue
        # Skip if domain part is garbage
        domain = url.split('/')[0].split('?')[0]
        if domain.lower() in noise:
            continue
        filtered.append(url)
    return filtered


def extract_entities(text, category=None):
    """
    Extract all structured entities from OCR text.

    Args:
        text: Raw OCR text
        category: Optional classification category (helps refine extraction)

    Returns:
        dict with keys: phones, emails, urls, handles, dates, prices,
                        addresses, tickers, todos, quotes, contacts
    """
    cleaned = clean_ocr_text(text)

    entities = OrderedDict()

    # Phone numbers
    phones = PHONE_RE.findall(cleaned)
    entities['phones'] = _filter_false_positive_phones(phones, cleaned)

    # Emails
    emails = EMAIL_RE.findall(cleaned)
    entities['emails'] = _dedup_preserve_order(emails)

    # URLs
    urls = URL_RE.findall(cleaned)
    entities['urls'] = _dedup_preserve_order(_filter_false_positive_urls(urls))

    # Social handles
    handles = HANDLE_RE.findall(cleaned)
    # Filter out common false positives
    skip_handles = {'gmail', 'yahoo', 'hotmail', 'outlook', 'icloud', 'com', 'org', 'net'}
    entities['handles'] = _dedup_preserve_order(
        ['@' + h for h in handles if h.lower() not in skip_handles]
    )

    # Dates
    dates = DATE_RE.findall(cleaned)
    entities['dates_mentioned'] = _dedup_preserve_order(dates)

    # Prices
    prices = PRICE_RE.findall(cleaned)
    entities['prices'] = _dedup_preserve_order(prices)

    # Addresses
    addresses = ADDRESS_RE.findall(cleaned)
    entities['addresses'] = _dedup_preserve_order(addresses)

    # Stock tickers
    tickers = TICKER_RE.findall(cleaned)
    entities['tickers'] = _dedup_preserve_order(['$' + t for t in tickers])

    # To-do items
    todos = []
    for m in TODO_KEYWORD_RE.finditer(cleaned):
        todos.append(m.group(0).strip())
    entities['todos'] = _dedup_preserve_order(todos)[:10]  # cap at 10

    # Quotes
    quotes = QUOTE_RE.findall(cleaned)
    # Also grab inspirational-looking standalone lines
    if category and 'nspir' in str(category).lower():
        for line in cleaned.split('\n'):
            line = line.strip()
            if 30 < len(line) < 300 and not re.match(r'^[@\d<(]', line):
                if not any(q in line for q in quotes):
                    quotes.append(line)
    entities['quotes'] = _dedup_preserve_order(quotes)[:5]

    # ── Products ──
    products = []
    for m in PRODUCT_RE.finditer(cleaned):
        product = m.group(0).strip()
        # Clean up: remove newlines, trim
        product = re.sub(r'\s*\n\s*', ' ', product).strip()
        noise_products = {'follow', 'explore', 'share', 'order summary', 'checkout',
                          'afterpay', 'item subtotal', 'view', 'close', 'message'}
        if len(product) > 3 and product.lower() not in noise_products:
            products.append(product)
    entities['products'] = _dedup_preserve_order(products)[:10]

    # ── Services / Businesses ──
    services = []
    # Extract business names
    service_noise = {'send', 'message', 'your', 'view', 'follow', 'order summary',
                     'item subtotal', 'billed to', 'checkout', 'close', 'total',
                     'choose', 'returning', 'confirmation', 'item', 'day pass'}
    for m in BUSINESS_RE.finditer(cleaned):
        for g in m.groups():
            if g and len(g.strip()) > 2:
                name = g.strip()
                if name.lower() not in service_noise and not re.match(r'^\d', name):
                    services.append(name)
    # If category suggests a service, extract venue/business from first substantive line
    if category and any(k in str(category).lower() for k in ['receipt', 'purchase', 'restaurant', 'food', 'airbnb', 'review']):
        for line in cleaned.split('\n')[:10]:
            line = line.strip()
            # Look for business name patterns (Capitalized phrase, 2-4 words)
            biz = re.match(r'^([A-Z][\w]+(?:\s+[A-Z][\w]+){0,3})\s*(?::|Reservation|\-|$)', line)
            if biz:
                name = biz.group(1).strip()
                if len(name) > 3 and name.lower() not in ('close', 'choose', 'item', 'total', 'order', 'view'):
                    services.append(name)
    entities['services'] = _dedup_preserve_order(services)[:10]

    # ── People (enhanced) ──
    people = []
    # Named people from various patterns
    for m in PERSON_NAME_RE.finditer(cleaned):
        for g in m.groups():
            if g and len(g.strip()) > 2:
                people.append(g.strip())
    # @handles as people (the primary accounts posting content)
    for handle in entities.get('handles', [])[:5]:
        people.append(handle)
    # Filter noise
    noise_names = {'send', 'message', 'your', 'story', 'explore', 'follow', 'view',
                   'all', 'see', 'add', 'share', 'home', 'shop', 'profile', 'more',
                   'close', 'suggested', 'search', 'friends', 'inbox', 'order',
                   'item', 'total', 'day', 'art', 'gmail.com', 'billed',
                   'choose', 'returning', 'checkout', 'confirmation'}
    entities['people'] = _dedup_preserve_order(
        [p for p in people
         if p.lower().split()[0] not in noise_names
         and len(p) > 2
         and not p.startswith('@gmail')
         and not p.startswith('@yahoo')
         and not p.startswith('@icloud')]
    )[:15]

    # Contact names (from messaging — keep separate for backward compat)
    contacts = []
    if category and any(k in str(category).lower() for k in ['message', 'chat', 'whatsapp', 'dm', 'sms']):
        first_lines = cleaned.strip().split('\n')[:3]
        for line in first_lines:
            name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', line)
            if name_match:
                name = name_match.group(1)
                if len(name) > 3 and name.lower() not in noise_names:
                    contacts.append(name)
                    break
    entities['contacts'] = _dedup_preserve_order(contacts)

    return entities


def has_any_entities(entities):
    """Check if any meaningful entities were extracted."""
    return any(len(v) > 0 for v in entities.values())


def summarize_entities(entities):
    """Return a one-line summary of what was extracted."""
    parts = []
    for key, values in entities.items():
        if values:
            parts.append(f"{len(values)} {key}")
    return ', '.join(parts) if parts else 'no entities'


if __name__ == '__main__':
    # Quick test with sample texts
    samples = [
        ("receipt", "Receipts", """Sample Restaurant Downtown
Prix Fixe Dinner Reservation ($75.00)
Friday, March 14, 2025 7:00pm
123 Main Street, Suite 200, Anytown, CA 90210
Phone: (555) 867-5309
reservations@example.com"""),

        ("stock", "Stocks / Crypto", """$AAPL -- consumer electronics and services
$TSLA -- electric vehicles and energy
$MSFT -- cloud computing and software
$AMZN -- e-commerce and cloud infrastructure"""),

        ("instagram", "Instagram Post", """11:38 al SF @)
Liked by sampleuser42 and 30,738 others
photo.jpeg A beautiful sunset over the mountains
@exampleartist"""),
    ]

    for name, cat, text in samples:
        print(f"\n=== {name} ===")
        entities = extract_entities(text, category=cat)
        for k, v in entities.items():
            if v:
                print(f"  {k}: {v}")
