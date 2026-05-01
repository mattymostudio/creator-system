#!/usr/bin/env python3
"""
Ingest scraped press HTML files into the YOURBRAND Obsidian vault.
- Converts HTML to markdown format matching vault conventions
- Checks for existing articles to avoid duplicates
- Adds tags for agent searchability
- Updates existing articles if we have richer content
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

# --- Paths ---
HTML_DIR = Path("/path/to/creator-system/tools/_inputs/press-html")
VAULT_ARTICLES_DIR = Path("/path/to/your-vault/02_SOURCES/YOURBRAND/Articles")

# --- Outlet name mapping (slug -> proper name for vault) ---
OUTLET_NAMES = {
    "time": "TIME",
    "southwest-contemporary": "Southwest Contemporary",
    "albuquerque-journal": "Albuquerque Journal",
    "channel-10-news": "Channel 10 News",
    "your-state-magazine": "Your State Magazine",
    "yahoo-news-uk": "Yahoo News UK",
    "detroit-free-press": "Detroit Free Press",
    "artnet": "Artnet",
    "artnet-2": "Artnet",
    "yourcounty-county-sun": "yourcounty County Sun",
    "nightline": "Nightline",
    "forbes": "Forbes",
    "forbes-2": "Forbes",
    "forbes-3": "Forbes",
    "tennessean": "The Tennessean",
    "new-york-post": "New York Post",
    "conscious-city-guide": "Conscious City Guide",
    "aspen-public-radio": "Aspen Public Radio",
    "cairo-scene": "CairoScene",
    "businesswire": "BusinessWire",
    "la-times": "Los Angeles Times",
    "korea-it-times": "Korea IT Times",
    "daily-mail": "Daily Mail",
    "decrypt": "Decrypt",
    "washington-examiner": "Washington Examiner",
    "metro-uk": "Metro UK",
    "art-newspaper": "The Art Newspaper",
    "new-york-times": "New York Times",
    "business-insider": "Business Insider",
    "business-insider-2": "Business Insider",
    "hypebeast": "Hypebeast",
    "hyperallergic": "Hyperallergic",
    "fox-news": "Fox News",
    "mashable": "Mashable",
    "us-magazine": "US Magazine",
    "page-six": "Page Six",
    "page-six-2": "Page Six",
    "nylon": "Nylon",
    "shemazing": "Shemazing",
    "digiday": "Digiday",
    "heaps": "Heaps",
    "techcrunch": "TechCrunch",
    "vox": "Vox",
    "billboard": "Billboard",
    "elite-daily": "Elite Daily",
    "futurism": "Futurism",
    "superhero-hype": "SuperHeroHype",
    "food-republic": "Food Republic",
    "teen-vogue": "Teen Vogue",
    "elle-australia": "Elle Australia",
    "ktla": "KTLA",
    "curbed": "Curbed LA",
    "cosmopolitan": "Cosmopolitan",
    "daily-beast": "The Daily Beast",
    "art-zealous": "ArtZealous",
    "daily-news": "NY Daily News",
    "facebookcom": "Facebook",
    "uproxx": "Uproxx",
    "nextshark": "NextShark",
    "nextshark-2": "NextShark",
    "nextshark-3": "NextShark",
    "digital-trends": "Digital Trends",
    "widewalls": "WideWalls",
    "widewalls-2": "WideWalls",
    "buzzfeed": "BuzzFeed",
    "los-angeles-magazine": "Los Angeles Magazine",
    "los-angeles-magazine-2": "Los Angeles Magazine",
    "huffpost": "HuffPost",
    "dazed": "Dazed",
    "vogue": "Vogue",
    "groomed-lacom": "Groomed LA",
    "hayo": "Hayo",
    "techzulu": "TechZulu",
    "federalist": "The Federalist",
    "observer": "Observer",
    "thesuncouk": "The Sun",
    "mobilenytimescom": "New York Times",
    "time-2": "TIME",
}

# --- Tag assignment based on content/theme ---
THEME_TAGS = {
    # Your Company / Anytown
    r"art park|Anytown|sculpture park|glamping|your-highway.*your state|sample landmark.*sample venue": [
        "art-park", "Anytown", "your-state"
    ],
    # Monolith
    r"monolith|monoliths|utah.*desert|mysterious.*metal|wales.*monolith": [
        "monolith", "stunt", "viral"
    ],
    # Pink Houses
    r"pink house|hot pink|mid.city.*pink|millennial pink.*house": [
        "pink-houses", "los-angeles", "stunt", "instagram"
    ],
    # Fyre Festival
    r"fyre|fyre festival|fyre experience": [
        "fyre-festival", "stunt", "pop-up"
    ],
    # Private Jet
    r"private jet|selfiecircus|jet.*selfie|gulfstream": [
        "private-jet-experience", "selfie", "los-angeles", "instagram"
    ],
    # NFT / Crypto
    r"\bnft\b|non.fungible|nifty gateway|okcoin|polygon.*nft|treetrunk|web3": [
        "nft", "crypto", "web3"
    ],
    # AI / Technology
    r"\bai\b|artificial intelligence|machine learning|algorithm.*art": [
        "ai", "technology"
    ],
    # Kanye / Celebrity
    r"kanye|yeezy|kanye.*loves": [
        "kanye", "celebrity", "pop-up"
    ],
    # Miley Cyrus
    r"miley|cyrus|hemsworth|instagram.*proposal": [
        "miley-cyrus", "celebrity", "instagram"
    ],
    # Snapchat
    r"snapchat|snap.*inc|yellow.*accelerator|augmented reality": [
        "snapchat", "technology", "social-media"
    ],
    # Instagram / Social Media
    r"instagram|instagrammable|selfie.*backdrop": [
        "instagram", "social-media"
    ],
    # Event Festival
    r"Event Festival": [
        "burning-man"
    ],
    # Cash art / money
    r"cash.*art|selling.*money|stacks.*cash|cash.*brick|bundles.*cash": [
        "cash-art", "stunt", "instagram"
    ],
    # Gucci
    r"gucci": [
        "gucci", "fashion", "collaboration"
    ],
    # Ariana Grande
    r"ariana grande|rainbow mural": [
        "ariana-grande", "mural", "collaboration"
    ],
    # Dog art
    r"french bulldog|chloe.*frenchie|dog.*paint": [
        "chloe-the-dog", "stunt", "viral"
    ],
    # Kaplan Twins
    r"kaplan twins|identical twins": [
        "kaplan-twins", "collaboration"
    ],
    # Your University / early career
    r"your-university|facebook class|sample-accelerator|yourcompany": [
        "your-university", "pre-artist-career", "tech"
    ],
    # Weed / Cannabis
    r"dispensar|cannabis|weed": [
        "cannabis", "mural", "los-angeles"
    ],
    # Art Basel
    r"art basel": [
        "art-basel", "art-world"
    ],
    # Nude Snapchats
    r"nude snapchat|publishing.*nude": [
        "snapchat", "controversy", "stunt"
    ],
}

# Era tags based on year
ERA_TAGS = {
    range(2007, 2015): "pre-artist",
    range(2015, 2017): "early-artist",
    range(2017, 2018): "pink-house-era",
    range(2018, 2020): "private-jet-era",
    range(2020, 2022): "monolith-era",
    range(2022, 2024): "transition-to-Anytown",
    range(2024, 2030): "art-park-era",
}


def get_era_tag(year):
    """Get the era tag for a given year."""
    y = int(year)
    for year_range, tag in ERA_TAGS.items():
        if y in year_range:
            return tag
    return "unknown-era"


def assign_tags(text, year):
    """Assign tags based on article content and year."""
    tags = set()
    text_lower = text.lower()

    # Add era tag
    tags.add(get_era_tag(year))

    # Add press tag to all
    tags.add("press")

    # Match theme tags
    for pattern, theme_tags in THEME_TAGS.items():
        if re.search(pattern, text_lower):
            tags.update(theme_tags)

    # If no specific theme matched, add general tag
    if len(tags) <= 2:  # just press + era
        tags.add("profile")

    return sorted(tags)


def html_to_markdown(html_content):
    """Convert cleaned article HTML to plain markdown text."""
    soup = BeautifulSoup(html_content, "lxml")

    # Find the article body
    body = soup.find(class_="article-body") or soup.find("article") or soup.find("body")
    if not body:
        return ""

    # Process the content
    lines = []
    for el in body.find_all(["p", "h1", "h2", "h3", "h4", "blockquote", "figure", "img", "li", "ul", "ol"]):
        if el.name in ("h1", "h2"):
            text = el.get_text(strip=True)
            if text:
                lines.append(f"\n## {text}\n")
        elif el.name in ("h3", "h4"):
            text = el.get_text(strip=True)
            if text:
                lines.append(f"\n### {text}\n")
        elif el.name == "blockquote":
            text = el.get_text(strip=True)
            if text:
                lines.append(f"\n> {text}\n")
        elif el.name == "img":
            src = el.get("src", "")
            alt = el.get("alt", "")
            if src and not src.startswith("data:"):
                lines.append(f"\n![{alt}]({src})\n")
        elif el.name == "figure":
            img = el.find("img")
            caption = el.find("figcaption")
            if img:
                src = img.get("src", "")
                alt = img.get("alt", "") or (caption.get_text(strip=True) if caption else "")
                if src and not src.startswith("data:"):
                    lines.append(f"\n![{alt}]({src})")
                    if caption:
                        lines.append(f"*{caption.get_text(strip=True)}*\n")
                    else:
                        lines.append("")
        elif el.name == "li":
            text = el.get_text(strip=True)
            if text:
                lines.append(f"- {text}")
        elif el.name == "p":
            # Skip if inside a figure (already handled)
            if el.parent and el.parent.name == "figure":
                continue
            # Skip if inside a blockquote (already handled)
            if el.parent and el.parent.name == "blockquote":
                continue

            text = el.get_text(strip=True)
            if text:
                lines.append(f"\n{text}")

    return "\n".join(lines).strip()


def parse_html_file(html_path):
    """Parse a cleaned HTML file and extract metadata + content."""
    content = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "lxml")

    # Extract metadata from our template structure
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""

    # Get headline
    h1 = soup.find("h1")
    headline = h1.get_text(strip=True) if h1 else ""

    # Get publication name
    pub_el = soup.find(class_="publication-name")
    publisher = pub_el.get_text(strip=True) if pub_el else ""

    # Get byline
    byline_el = soup.find(class_="byline")
    byline = byline_el.get_text(strip=True) if byline_el else ""

    # Parse author and date from byline
    author = ""
    date = ""
    if byline:
        # "By Author Name · 2024-03-12" or "By Author Name · March 12, 2024"
        parts = re.split(r'\s*[·•]\s*', byline)
        if parts:
            author_part = parts[0].strip()
            author = re.sub(r'^By\s+', '', author_part, flags=re.I).strip()
        if len(parts) > 1:
            date = parts[1].strip()

    # Get original URL
    orig_link = soup.find(class_="original-link")
    url = ""
    if orig_link:
        a_tag = orig_link.find("a")
        if a_tag:
            url = a_tag.get("href", "")

    # Convert body to markdown
    body_md = html_to_markdown(content)

    return {
        "headline": headline,
        "publisher": publisher,
        "author": author,
        "date": date,
        "url": url,
        "body_md": body_md,
    }


def find_existing_match(headline, publisher, year, existing_files):
    """Check if an article already exists in the vault."""
    headline_lower = headline.lower()
    publisher_lower = publisher.lower()

    # Normalize for matching
    headline_words = set(re.findall(r'\w+', headline_lower))

    for fname in existing_files:
        fname_lower = fname.lower()

        # Check if publisher name appears in filename
        pub_in_fname = False
        for pub_variant in [publisher_lower, publisher_lower.replace("the ", "")]:
            pub_words = pub_variant.split()
            if any(w in fname_lower for w in pub_words if len(w) > 3):
                pub_in_fname = True
                break

        # Check if year matches
        year_in_fname = str(year) in fname

        if not (pub_in_fname and year_in_fname):
            continue

        # Check headline overlap - if significant words match
        fname_words = set(re.findall(r'\w+', fname_lower))
        overlap = headline_words & fname_words
        significant_overlap = len([w for w in overlap if len(w) > 4])

        if significant_overlap >= 2:
            return fname

    return None


def format_date(date_str):
    """Try to normalize a date string to YYYY-MM-DD."""
    if not date_str:
        return ""

    # Already in YYYY-MM-DD format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str

    # Try common formats
    for fmt in [
        "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y",
        "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d", "%m/%d/%Y",
        "%B %Y", "%b %Y",
    ]:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return date_str


def generate_vault_markdown(data, tags):
    """Generate the vault-format markdown for an article."""
    lines = []

    # Line 1: URL
    lines.append(data["url"])
    lines.append("")

    # Metadata
    lines.append(f"**Author:** {data['author']}" if data["author"] else "**Author:** Unknown")
    lines.append(f"**Publisher:** {data['publisher']}")
    lines.append(f"**Date:** {format_date(data['date'])}")
    lines.append("")

    # Tags
    tag_line = " ".join(f"#{t}" for t in tags)
    lines.append(tag_line)
    lines.append("")

    # Body
    lines.append(data["body_md"])

    return "\n".join(lines)


def generate_vault_filename(year, publisher, headline):
    """Generate the vault filename following naming convention."""
    # Clean headline for filename
    clean_headline = headline
    # Remove special chars but keep basic punctuation
    clean_headline = re.sub(r'[<>:"/\\|?*]', '', clean_headline)
    # Truncate if too long
    if len(clean_headline) > 120:
        clean_headline = clean_headline[:120].rsplit(' ', 1)[0]

    return f"{year} - Headline - {publisher} - {clean_headline}.md"


def main():
    html_files = sorted(HTML_DIR.glob("*.html"))
    existing_vault_files = [f.name for f in VAULT_ARTICLES_DIR.glob("*.md")]

    log.info(f"Found {len(html_files)} HTML files to process")
    log.info(f"Found {len(existing_vault_files)} existing vault articles")

    created = 0
    updated = 0
    skipped = 0
    errors = 0

    results = []

    for html_file in html_files:
        fname = html_file.stem  # e.g. "2024-artnet"
        parts = fname.split("-", 1)
        year = parts[0]
        outlet_slug = parts[1] if len(parts) > 1 else "unknown"

        log.info(f"\nProcessing: {fname}")

        # Parse the HTML
        try:
            data = parse_html_file(html_file)
        except Exception as e:
            log.error(f"  Failed to parse: {e}")
            errors += 1
            continue

        if not data["body_md"] or len(data["body_md"]) < 50:
            log.warning(f"  Body too short ({len(data['body_md'])} chars), skipping")
            skipped += 1
            continue

        # Fix publisher name
        if not data["publisher"] or data["publisher"] == outlet_slug:
            data["publisher"] = OUTLET_NAMES.get(outlet_slug, outlet_slug.replace("-", " ").title())
        # Also try to use our nicer name
        if outlet_slug in OUTLET_NAMES:
            data["publisher"] = OUTLET_NAMES[outlet_slug]

        if not data["headline"]:
            data["headline"] = "Untitled"

        # Assign tags
        full_text = f"{data['headline']} {data['body_md']}"
        tags = assign_tags(full_text, year)

        # Check for existing match
        existing_match = find_existing_match(data["headline"], data["publisher"], year, existing_vault_files)

        if existing_match:
            # Check if we should update (our version has more content)
            existing_path = VAULT_ARTICLES_DIR / existing_match
            existing_content = existing_path.read_text(encoding="utf-8")
            existing_len = len(existing_content)
            new_content = generate_vault_markdown(data, tags)
            new_len = len(new_content)

            # Check if existing already has tags
            has_tags = bool(re.search(r'#\w+', existing_content))

            if not has_tags:
                # Add tags to existing file
                # Insert tags after the date line
                lines = existing_content.split("\n")
                insert_idx = None
                for i, line in enumerate(lines):
                    if line.startswith("**Date:**"):
                        insert_idx = i + 1
                        break

                if insert_idx is not None:
                    tag_line = " ".join(f"#{t}" for t in tags)
                    # Insert blank line + tags after date
                    lines.insert(insert_idx, "")
                    lines.insert(insert_idx + 1, tag_line)
                    existing_path.write_text("\n".join(lines), encoding="utf-8")
                    log.info(f"  Updated existing: {existing_match} (added tags: {tag_line})")
                    updated += 1
                else:
                    log.info(f"  Skipped (already exists): {existing_match}")
                    skipped += 1
            else:
                log.info(f"  Skipped (already exists with tags): {existing_match}")
                skipped += 1

            results.append({"file": fname, "action": "updated" if not has_tags else "skipped", "vault_file": existing_match})
            continue

        # Generate vault filename
        vault_filename = generate_vault_filename(year, data["publisher"], data["headline"])
        vault_path = VAULT_ARTICLES_DIR / vault_filename

        # Check for filename collision
        if vault_path.exists():
            log.info(f"  File already exists: {vault_filename}")
            skipped += 1
            results.append({"file": fname, "action": "skipped", "vault_file": vault_filename})
            continue

        # Generate and write the vault markdown
        vault_content = generate_vault_markdown(data, tags)
        vault_path.write_text(vault_content, encoding="utf-8")
        log.info(f"  Created: {vault_filename}")
        log.info(f"  Tags: {' '.join(f'#{t}' for t in tags)}")
        created += 1
        results.append({"file": fname, "action": "created", "vault_file": vault_filename})

    # Summary
    log.info(f"\n{'='*60}")
    log.info(f"INGEST COMPLETE")
    log.info(f"  Created: {created}")
    log.info(f"  Updated (added tags): {updated}")
    log.info(f"  Skipped (already exists): {skipped}")
    log.info(f"  Errors: {errors}")
    log.info(f"{'='*60}")

    # Write results log
    results_path = Path(__file__).parent / "ingest-results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    log.info(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    main()
