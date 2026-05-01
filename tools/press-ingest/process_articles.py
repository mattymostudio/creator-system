#!/usr/bin/env python3
"""
Press Article Processor
Scrapes press articles from YOURBRAND headlines page, takes screenshots,
extracts article content, and generates cleaned HTML files.
"""

import os
import re
import sys
import json
import time
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import trafilatura
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# --- Configuration ---
BASE_DIR = Path(__file__).parent
SCREENSHOTS_DIR = BASE_DIR / "press-screenshots"
HTML_DIR = BASE_DIR / "press-html"
LOG_FILE = BASE_DIR / "press-processing-log.md"
HEADLINES_URL = "https://www.yourdomain.example/headlines"

SCREENSHOTS_DIR.mkdir(exist_ok=True)
HTML_DIR.mkdir(exist_ok=True)

# Sites that are video/social and should be screenshot-only
VIDEO_DOMAINS = {"youtube.com", "youtu.be", "facebook.com", "fb.watch"}
SKIP_CONTENT_DOMAINS = VIDEO_DOMAINS | {"tiktok.com", "instagram.com"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:60]


def extract_year_from_context(link_text: str, surrounding_text: str) -> str:
    """Try to extract the year from the link context."""
    # Look for year patterns in the link text first
    match = re.search(r'(20\d{2}|19\d{2})', link_text)
    if match:
        return match.group(1)
    # Look in surrounding text
    match = re.search(r'(20\d{2}|19\d{2})', surrounding_text)
    if match:
        return match.group(1)
    return "unknown"


def get_domain_name(url: str) -> str:
    """Extract a clean domain name for use in filenames."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    # Map common domains to readable names
    domain_map = {
        "time.com": "time",
        "southwestcontemporary.com": "southwest-contemporary",
        "abqjournal.com": "albuquerque-journal",
        "newschannel10.com": "channel-10-news",
        "newmexicomagazine.org": "your-state-magazine",
        "uk.news.yahoo.com": "yahoo-news-uk",
        "freep.com": "detroit-free-press",
        "news.artnet.com": "artnet",
        "example-newspaper.example": "yourcounty-county-sun",
        "abcnews.go.com": "nightline",
        "forbes.com": "forbes",
        "tennessean.com": "tennessean",
        "nypost.com": "new-york-post",
        "consciouscityguide.com": "conscious-city-guide",
        "aspenpublicradio.org": "aspen-public-radio",
        "cairoscene.com": "cairo-scene",
        "businesswire.com": "businesswire",
        "latimes.com": "la-times",
        "koreaittimes.com": "korea-it-times",
        "dailymail.co.uk": "daily-mail",
        "decrypt.co": "decrypt",
        "washingtonexaminer.com": "washington-examiner",
        "metro.co.uk": "metro-uk",
        "theartnewspaper.com": "art-newspaper",
        "nytimes.com": "new-york-times",
        "insider.com": "business-insider",
        "thisisinsider.com": "business-insider",
        "hypebeast.com": "hypebeast",
        "hyperallergic.com": "hyperallergic",
        "foxnews.com": "fox-news",
        "mashable.com": "mashable",
        "usmagazine.com": "us-magazine",
        "pagesix.com": "page-six",
        "youtube.com": "youtube",
        "nylon.com": "nylon",
        "shemazing.net": "shemazing",
        "digiday.com": "digiday",
        "heapsmag.com": "heaps",
        "techcrunch.com": "techcrunch",
        "vox.com": "vox",
        "billboard.com": "billboard",
        "elitedaily.com": "elite-daily",
        "futurism.com": "futurism",
        "superherohype.com": "superhero-hype",
        "foodrepublic.com": "food-republic",
        "teenvogue.com": "teen-vogue",
        "elle.com.au": "elle-australia",
        "ktla.com": "ktla",
        "la.curbed.com": "curbed",
        "cosmopolitan.com": "cosmopolitan",
        "thedailybeast.com": "daily-beast",
        "artzealous.com": "art-zealous",
        "nydailynews.com": "daily-news",
        "uproxx.com": "uproxx",
        "nextshark.com": "nextshark",
        "digitaltrends.com": "digital-trends",
        "widewalls.ch": "widewalls",
        "buzzfeed.com": "buzzfeed",
        "lamag.com": "los-angeles-magazine",
        "huffingtonpost.com": "huffpost",
        "dazeddigital.com": "dazed",
        "vogue.com": "vogue",
        "hayo.co": "hayo",
        "techzulu.com": "techzulu",
        "thefederalist.com": "federalist",
        "observer.com": "observer",
        "businessinsider.com": "business-insider",
    }
    return domain_map.get(domain, slugify(domain))


def is_video_url(url: str) -> bool:
    """Check if URL points to video/social content."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    return any(vd in domain for vd in VIDEO_DOMAINS)


def scrape_headlines_page() -> list[dict]:
    """Fetch the headlines page and extract all press links."""
    log.info(f"Fetching headlines from {HEADLINES_URL}")
    resp = requests.get(HEADLINES_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    articles = []
    current_year = None

    # Find all text content and links on the page
    main = soup.find("main") or soup.find("body")
    if not main:
        log.error("Could not find main content on headlines page")
        return []

    # Walk through elements to track year headings and article links
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "a", "div", "li", "span"]):
        text = el.get_text(strip=True)

        # Check if this is a year heading
        year_match = re.match(r'^(20\d{2}|19\d{2})$', text)
        if year_match:
            current_year = year_match.group(1)
            continue

        # Check if this element contains a link to an external article
        if el.name == "a" and el.get("href"):
            href = el["href"]
            if not href.startswith("http"):
                continue
            parsed = urlparse(href)
            if "yourdomain.example" in parsed.netloc:
                continue

            # Get the full context text (headline + outlet info)
            parent_text = el.parent.get_text(strip=True) if el.parent else text
            link_text = text

            # Try to extract outlet and date from context
            articles.append({
                "url": href,
                "link_text": link_text,
                "context": parent_text,
                "year": current_year or extract_year_from_context(link_text, parent_text),
                "outlet": get_domain_name(href),
                "is_video": is_video_url(href),
            })

    # Deduplicate by URL
    seen = set()
    unique = []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    log.info(f"Found {len(unique)} unique press articles")
    return unique


def take_screenshot(page, url: str, output_path: Path) -> bool:
    """Navigate to URL and take a full-page screenshot."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for content to render and lazy-load
        page.wait_for_timeout(5000)
        # Dismiss cookie banners if present
        for selector in [
            "button:has-text('Accept')",
            "button:has-text('OK')",
            "button:has-text('Got it')",
            "button:has-text('I agree')",
            "[class*='cookie'] button",
            "[id*='cookie'] button",
            "[class*='consent'] button",
        ]:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=1000):
                    btn.click(timeout=2000)
                    page.wait_for_timeout(500)
                    break
            except:
                continue

        page.screenshot(path=str(output_path), full_page=True)
        log.info(f"  Screenshot saved: {output_path.name}")
        return True
    except PlaywrightTimeout:
        log.warning(f"  Timeout loading page for screenshot")
        try:
            page.screenshot(path=str(output_path), full_page=True)
            log.info(f"  Partial screenshot saved: {output_path.name}")
            return True
        except:
            return False
    except Exception as e:
        log.error(f"  Screenshot failed: {e}")
        return False


def extract_article_content(url: str):
    """Extract article content using trafilatura, preserving images."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            log.warning(f"  Could not fetch URL for content extraction")
            return None

        # First get metadata via JSON output
        json_result = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_images=True,
            include_links=True,
            output_format="json",
            with_metadata=True,
        )

        metadata = {}
        if json_result:
            metadata = json.loads(json_result)

        # Now get the HTML output which preserves images and structure
        html_result = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_images=True,
            include_links=True,
            output_format="xml",
            with_metadata=False,
        )

        # Also get plain HTML format
        html_body = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_images=True,
            include_links=True,
            output_format="html",
            with_metadata=False,
        )

        if not metadata.get("text") and not html_body:
            log.warning(f"  trafilatura returned no content")
            return None

        # Clean up images in the HTML body - keep only article images
        if html_body:
            html_body = clean_article_images(html_body, url)

        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "date": metadata.get("date", ""),
            "sitename": metadata.get("sitename", ""),
            "text": metadata.get("text", ""),
            "description": metadata.get("description", ""),
            "body_html": html_body or "",
        }
    except Exception as e:
        log.error(f"  Content extraction failed: {e}")
        return None


# Patterns in image URLs that indicate ads/promos, not editorial images
AD_IMAGE_PATTERNS = [
    "ad", "ads", "advert", "banner", "promo", "sponsor",
    "pixel", "tracking", "beacon", "analytics",
    "doubleclick", "googlesyndication", "amazon-adsystem",
    "facebook.com/tr", "taboola", "outbrain",
    "related", "recommended", "widget",
    "logo-ad", "commercial", "affiliate",
    "1x1", "spacer", "blank.gif", "clear.gif",
]

# Minimum dimensions to keep — tiny images are usually trackers
MIN_IMAGE_DIMENSION = 50


def clean_article_images(html_body: str, article_url: str) -> str:
    """Remove ad/promo/tracker images, keep editorial article images."""
    soup = BeautifulSoup(html_body, "lxml")
    parsed_article = urlparse(article_url)

    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "").lower()
        src_lower = src.lower()

        should_remove = False

        # Remove tracking pixels and ad images based on URL patterns
        for pattern in AD_IMAGE_PATTERNS:
            if pattern in src_lower:
                should_remove = True
                break

        # Remove images with suspicious dimensions (1x1 tracking pixels etc.)
        width = img.get("width", "")
        height = img.get("height", "")
        try:
            if width and height:
                w = int(str(width).replace("px", ""))
                h = int(str(height).replace("px", ""))
                if w < MIN_IMAGE_DIMENSION or h < MIN_IMAGE_DIMENSION:
                    should_remove = True
        except (ValueError, TypeError):
            pass

        # Remove data: URI images (usually tiny inline icons)
        if src.startswith("data:"):
            should_remove = True

        # Make relative URLs absolute
        if src and not src.startswith(("http://", "https://", "data:")):
            if src.startswith("//"):
                img["src"] = "https:" + src
            elif src.startswith("/"):
                img["src"] = f"{parsed_article.scheme}://{parsed_article.netloc}{src}"

        if should_remove:
            # Remove the img and its parent figure if it exists
            parent = img.parent
            img.decompose()
            if parent and parent.name == "figure" and not parent.find("img"):
                parent.decompose()

    # Convert trafilatura's <graphic> tags to proper <img> tags
    for graphic in soup.find_all("graphic"):
        src = graphic.get("src", "")
        alt = graphic.get("alt", "")
        title = graphic.get("title", "")
        if src:
            img_tag = soup.new_tag("img", src=src, alt=alt)
            if title:
                img_tag["title"] = title
            # Wrap in figure with caption if alt text exists
            if alt:
                figure = soup.new_tag("figure")
                figure.append(img_tag)
                caption = soup.new_tag("figcaption")
                caption.string = alt
                figure.append(caption)
                graphic.replace_with(figure)
            else:
                graphic.replace_with(img_tag)
        else:
            graphic.decompose()

    # Return just the body content, not full HTML document that BS adds
    body = soup.find("body")
    if body:
        return "".join(str(child) for child in body.children)
    return str(soup)


def generate_clean_html(article_data: dict, content: dict, url: str) -> str:
    """Generate a clean HTML file from extracted content."""
    title = content.get("title") or article_data.get("link_text", "Article")
    author = content.get("author", "")
    date = content.get("date", "")
    sitename = content.get("sitename", "") or article_data.get("outlet", "")
    # Prefer HTML with images; fall back to plain text conversion
    body_html = content.get("body_html", "")
    if not body_html.strip():
        text = content.get("text", "")
        paragraphs = text.strip().split("\n")
        parts = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if len(p) < 80 and not p.endswith('.') and not p.endswith('"') and not p.endswith("'"):
                parts.append(f"      <h3>{p}</h3>")
            else:
                parts.append(f"      <p>{p}</p>")
        body_html = "\n".join(parts)

    byline_parts = []
    if author:
        byline_parts.append(f"By {author}")
    if date:
        byline_parts.append(date)
    byline = " · ".join(byline_parts) if byline_parts else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — {sitename}</title>
  <style>
    body {{
      font-family: Georgia, 'Times New Roman', serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 40px 20px;
      color: #1a1a1a;
      line-height: 1.7;
      background: #fff;
    }}
    .publication-branding {{
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid #e0e0e0;
    }}
    .publication-name {{
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #666;
    }}
    h1 {{
      font-size: 2em;
      line-height: 1.2;
      margin: 0 0 16px 0;
    }}
    .byline {{
      font-size: 14px;
      color: #666;
      margin-bottom: 32px;
    }}
    .article-body p {{
      margin-bottom: 1.2em;
    }}
    .article-body h3 {{
      font-size: 1.3em;
      margin-top: 1.5em;
      margin-bottom: 0.5em;
    }}
    .article-body img {{
      max-width: 100%;
      height: auto;
      margin: 24px 0;
    }}
    .article-body figcaption {{
      font-size: 13px;
      color: #888;
      margin-top: -16px;
      margin-bottom: 24px;
    }}
    .original-link {{
      margin-top: 48px;
      padding-top: 16px;
      border-top: 1px solid #e0e0e0;
      font-size: 13px;
      color: #999;
    }}
    .original-link a {{
      color: #666;
    }}
  </style>
</head>
<body>
  <div class="publication-branding">
    <div class="publication-name">{sitename}</div>
  </div>
  <article>
    <h1>{title}</h1>
    <div class="byline">{byline}</div>
    <div class="article-body">
{body_html}
    </div>
  </article>
  <div class="original-link">
    Originally published by <a href="{url}" target="_blank">{sitename}</a>
  </div>
</body>
</html>"""


def append_to_log(status: str, year: str, outlet: str, headline: str,
                  has_screenshot: bool, has_html: bool, notes: str = ""):
    """Append a row to the processing log."""
    ss = "yes" if has_screenshot else "no"
    ht = "yes" if has_html else "no"
    headline_short = headline[:80] + "..." if len(headline) > 80 else headline
    line = f"| {status} | {year} | {outlet} | {headline_short} | {ss} | {ht} | {notes} |\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)


def process_article(page, article: dict, index: int, total: int) -> None:
    """Process a single article: screenshot + content extraction + HTML generation."""
    url = article["url"]
    year = article["year"]
    outlet = article["outlet"]
    link_text = article["link_text"]
    is_video = article["is_video"]

    log.info(f"\n[{index+1}/{total}] Processing: {outlet} ({year})")
    log.info(f"  URL: {url}")

    # Generate filenames - handle duplicate outlets in same year
    base_name = f"{year}-{outlet}"
    ss_path = SCREENSHOTS_DIR / f"{base_name}-screenshot.png"
    html_path = HTML_DIR / f"{base_name}.html"

    # Handle duplicates by appending a number
    counter = 2
    while ss_path.exists() or html_path.exists():
        base_name = f"{year}-{outlet}-{counter}"
        ss_path = SCREENSHOTS_DIR / f"{base_name}-screenshot.png"
        html_path = HTML_DIR / f"{base_name}.html"
        counter += 1

    # Take screenshot
    has_screenshot = take_screenshot(page, url, ss_path)

    # Skip content extraction for videos/social
    if is_video:
        log.info(f"  Skipping content extraction (video/social)")
        append_to_log("skipped", year, outlet, link_text, has_screenshot, False, "video content")
        return

    # Extract article content
    content = extract_article_content(url)
    has_html = False

    if content and content.get("text"):
        html = generate_clean_html(article, content, url)
        html_path.write_text(html, encoding="utf-8")
        has_html = True
        log.info(f"  HTML saved: {html_path.name}")
        status = "done"
        notes = ""
    else:
        status = "partial"
        notes = "content extraction failed"
        log.warning(f"  Could not extract article content")

    if not has_screenshot and not has_html:
        status = "dead-link"
        notes = "could not load page"

    append_to_log(status, year, outlet, link_text, has_screenshot, has_html, notes)


def main():
    # Parse command line args
    start_index = 0
    batch_size = None  # Process all by default

    if len(sys.argv) > 1:
        start_index = int(sys.argv[1])
    if len(sys.argv) > 2:
        batch_size = int(sys.argv[2])

    # Get the list of articles
    articles = scrape_headlines_page()

    if not articles:
        log.error("No articles found. Exiting.")
        return

    # Apply batch limits
    end_index = len(articles) if batch_size is None else min(start_index + batch_size, len(articles))
    batch = articles[start_index:end_index]

    log.info(f"\nProcessing articles {start_index+1} to {end_index} of {len(articles)} total")
    log.info(f"Screenshots dir: {SCREENSHOTS_DIR}")
    log.info(f"HTML dir: {HTML_DIR}")
    log.info(f"Log file: {LOG_FILE}\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for i, article in enumerate(batch):
            try:
                process_article(page, article, start_index + i, len(articles))
            except Exception as e:
                log.error(f"  Unexpected error: {e}")
                append_to_log("dead-link", article["year"], article["outlet"],
                              article["link_text"], False, False, str(e)[:50])
            # Small delay between requests
            time.sleep(1)

        browser.close()

    log.info(f"\nBatch complete! Processed {len(batch)} articles.")
    log.info(f"Screenshots: {SCREENSHOTS_DIR}")
    log.info(f"HTML files: {HTML_DIR}")
    log.info(f"Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
