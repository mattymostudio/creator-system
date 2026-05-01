#!/usr/bin/env python3
"""
Retry remaining failed articles using the Wayback Machine cached versions.
"""

import re
import time
import json
import logging
from pathlib import Path
from urllib.parse import urlparse, quote

import requests
from bs4 import BeautifulSoup, Comment
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_DIR = Path(__file__).parent
SCREENSHOTS_DIR = BASE_DIR / "press-screenshots"
HTML_DIR = BASE_DIR / "press-html"
LOG_FILE = BASE_DIR / "press-processing-log.md"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

# DUMMY DATA — replace with your own failed-article list from retry round 1
# Each entry: {"url": ..., "year": ..., "outlet": ..., "headline": ...}
STILL_FAILED = [
    {"url": "https://www.example-magazine.example/2024/05/sample-artist-profile/", "year": "2024", "outlet": "example-magazine", "headline": "Sample Artist Profile"},
    {"url": "https://www.example-news.example/arts/2023/sample-exhibition.html", "year": "2023", "outlet": "example-news", "headline": "Sample Exhibition Opens"},
    {"url": "https://www.example-paper.example/story/2022/community-art-project/12345.html", "year": "2022", "outlet": "example-paper", "headline": "Community Art Project Launches"},
]

REMOVE_SELECTORS = [
    "nav", "header", "footer", ".nav", ".header", ".footer",
    ".sidebar", "aside", ".ad", ".ads", ".advertisement",
    ".social-share", ".share-buttons", ".social-buttons",
    ".newsletter", ".signup", ".subscribe",
    ".related", ".recommended", ".more-stories", ".read-next",
    ".comments", "#comments", ".comment-section",
    ".cookie", ".consent", ".gdpr", ".privacy-banner",
    "script", "style", "noscript",
    ".sponsored", ".promo", ".promotion",
    ".breadcrumb", ".breadcrumbs",
    ".paywall", ".subscriber-only",
    ".modal", ".overlay", ".popup",
    # Wayback Machine UI elements
    "#wm-ipp-base", "#wm-ipp", "#donato", "#wm-btm",
    ".wb-autocomplete-suggestions",
]


def get_wayback_url(original_url):
    """Look up the best Wayback Machine snapshot for a URL."""
    api_url = f"https://archive.org/wayback/available?url={quote(original_url, safe='')}"
    try:
        resp = requests.get(api_url, timeout=15)
        data = resp.json()
        snapshot = data.get("archived_snapshots", {}).get("closest", {})
        if snapshot and snapshot.get("available"):
            wb_url = snapshot["url"]
            # Use the raw/id_ version to avoid Wayback toolbar
            wb_url = wb_url.replace("/http", "id_/http")
            log.info(f"  Wayback snapshot found: {wb_url}")
            return wb_url
        else:
            log.warning(f"  No Wayback snapshot available")
            return None
    except Exception as e:
        log.error(f"  Wayback API error: {e}")
        return None


def extract_from_page(page, url, original_url):
    """Extract article content from a rendered page."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(5000)

        # Dismiss overlays
        for selector in [
            "button:has-text('Accept')", "button:has-text('OK')",
            "button:has-text('Got it')", "button:has-text('Continue')",
            "[class*='cookie'] button", "[class*='consent'] button",
            "button:has-text('I agree')", "button:has-text('Allow')",
        ]:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=1000):
                    btn.click(timeout=2000)
                    page.wait_for_timeout(500)
                    break
            except:
                continue

        # Scroll for lazy content
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 2/3)")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        raw_html = page.content()
        return clean_article(raw_html, original_url)

    except PlaywrightTimeout:
        log.warning(f"  Timeout")
        try:
            raw_html = page.content()
            return clean_article(raw_html, original_url)
        except:
            return None
    except Exception as e:
        log.error(f"  Error: {e}")
        return None


def clean_article(raw_html, url):
    """Extract and clean article content from HTML."""
    soup = BeautifulSoup(raw_html, "lxml")
    parsed = urlparse(url)

    # Get metadata first
    title = ""
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title:
        title = og_title.get("content", "")
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
    if not title and soup.find("title"):
        title = soup.find("title").get_text(strip=True)

    author = ""
    meta_author = soup.find("meta", attrs={"name": "author"})
    if meta_author:
        author = meta_author.get("content", "")

    date = ""
    meta_date = soup.find("meta", attrs={"property": "article:published_time"})
    if meta_date:
        date = meta_date.get("content", "")[:10]
    if not date:
        time_el = soup.find("time")
        if time_el:
            date = time_el.get("datetime", "") or time_el.get_text(strip=True)

    sitename = ""
    og_site = soup.find("meta", attrs={"property": "og:site_name"})
    if og_site:
        sitename = og_site.get("content", "")

    # Find article container
    article = None
    for selector_fn in [
        lambda s: s.find("article"),
        lambda s: s.find(attrs={"role": "article"}),
        lambda s: s.find(class_=re.compile(r"article.*(body|content)", re.I)),
        lambda s: s.find(class_=re.compile(r"(post|entry|story).*(content|body)", re.I)),
        lambda s: s.find(id=re.compile(r"article|story|content|post", re.I)),
        lambda s: s.find(class_=re.compile(r"^article$|^post$|^story$", re.I)),
        lambda s: s.find("main"),
        lambda s: s.find(id="main"),
        lambda s: s.find(class_="main-content"),
        # Forbes-specific
        lambda s: s.find(class_=re.compile(r"article-body|body-content", re.I)),
        lambda s: s.find(class_=re.compile(r"fs-article", re.I)),
        # NYT-specific
        lambda s: s.find(class_=re.compile(r"StoryBodyCompanionColumn", re.I)),
        lambda s: s.find(attrs={"data-testid": re.compile(r"article|story", re.I)}),
    ]:
        result = selector_fn(soup)
        if result:
            article = result
            break

    if not article:
        article = soup.find("body")

    if not article:
        return None

    # Remove unwanted elements
    for selector in REMOVE_SELECTORS:
        for el in article.select(selector):
            el.decompose()

    # Remove comments
    for comment in article.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove hidden elements
    for el in article.find_all(style=re.compile(r"display:\s*none|visibility:\s*hidden")):
        el.decompose()

    # Process images
    ad_patterns = [
        "ad", "ads", "advert", "banner", "promo", "sponsor",
        "pixel", "tracking", "beacon", "analytics",
        "doubleclick", "googlesyndication", "taboola", "outbrain",
        "1x1", "spacer", "blank.gif", "clear.gif",
    ]

    for img in article.find_all("img"):
        src = img.get("src", "") or img.get("data-src", "") or img.get("data-lazy-src", "")
        if not src:
            img.decompose()
            continue

        # Replace lazy-loaded src
        real_src = img.get("data-src", "") or img.get("data-lazy-src", "") or img.get("data-original", "")
        if real_src and ("data:" in img.get("src", "") or "placeholder" in img.get("src", "").lower()):
            src = real_src
            img["src"] = src

        should_remove = False
        src_lower = src.lower()
        for pattern in ad_patterns:
            if pattern in src_lower:
                should_remove = True
                break

        # Fix Wayback Machine URLs - get original image URL
        if "web.archive.org" in src:
            # Extract original URL from wayback format
            match = re.search(r'https?://web\.archive\.org/web/\d+(?:id_)?/(https?://.+)', src)
            if match:
                src = match.group(1)
                img["src"] = src

        try:
            w = int(str(img.get("width", "0")).replace("px", ""))
            h = int(str(img.get("height", "0")).replace("px", ""))
            if w and h and (w < 50 or h < 50):
                should_remove = True
        except (ValueError, TypeError):
            pass

        if src.startswith("data:"):
            should_remove = True

        # Fix relative URLs
        if not src.startswith(("http://", "https://", "data:")):
            if src.startswith("//"):
                img["src"] = "https:" + src
            elif src.startswith("/"):
                img["src"] = f"{parsed.scheme}://{parsed.netloc}{src}"

        if should_remove:
            parent = img.parent
            img.decompose()
            if parent and parent.name == "figure" and not parent.find("img"):
                parent.decompose()

    # Strip unnecessary attributes
    for tag in article.find_all(True):
        if tag.name == "img":
            allowed = {"src", "alt", "title", "width", "height"}
        elif tag.name == "a":
            allowed = {"href"}
        else:
            allowed = set()
        attrs = dict(tag.attrs)
        for attr in attrs:
            if attr not in allowed:
                del tag[attr]

    # Remove empty elements
    for tag in article.find_all(["div", "span", "section"]):
        if not tag.get_text(strip=True) and not tag.find("img"):
            tag.decompose()

    body_html = ""
    for child in article.children:
        s = str(child).strip()
        if s:
            body_html += s + "\n"

    text_content = article.get_text(strip=True)
    if len(text_content) < 100:
        return None

    return {
        "title": title,
        "author": author,
        "date": date,
        "sitename": sitename,
        "body_html": body_html,
        "text_length": len(text_content),
    }


def generate_clean_html(content, article_info):
    """Generate clean HTML file."""
    title = content.get("title") or article_info.get("headline", "Article")
    author = content.get("author", "")
    date = content.get("date", "")
    sitename = content.get("sitename", "") or article_info.get("outlet", "")
    body_html = content.get("body_html", "")
    url = article_info["url"]

    byline_parts = []
    if author:
        byline_parts.append(f"By {author}")
    if date:
        byline_parts.append(date)
    byline = " &middot; ".join(byline_parts)

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
    h1 {{ font-size: 2em; line-height: 1.2; margin: 0 0 16px 0; }}
    h2, h3 {{ font-size: 1.3em; margin-top: 1.5em; margin-bottom: 0.5em; }}
    .byline {{ font-size: 14px; color: #666; margin-bottom: 32px; }}
    .article-body p {{ margin-bottom: 1.2em; }}
    .article-body img {{ max-width: 100%; height: auto; margin: 24px 0; display: block; }}
    .article-body figure {{ margin: 24px 0; }}
    .article-body figcaption {{ font-size: 13px; color: #888; margin-top: 8px; }}
    .article-body a {{ color: #333; text-decoration: underline; }}
    .original-link {{
      margin-top: 48px; padding-top: 16px;
      border-top: 1px solid #e0e0e0; font-size: 13px; color: #999;
    }}
    .original-link a {{ color: #666; }}
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


def main():
    log.info(f"Retrying {len(STILL_FAILED)} articles via Wayback Machine")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        success = 0
        still_failed = 0

        for i, article in enumerate(STILL_FAILED):
            url = article["url"]
            year = article["year"]
            outlet = article["outlet"]
            headline = article["headline"]

            log.info(f"\n[{i+1}/{len(STILL_FAILED)}] Retrying via Wayback: {outlet} ({year})")
            log.info(f"  Original URL: {url}")

            # Get Wayback Machine URL
            wb_url = get_wayback_url(url)
            if not wb_url:
                log.warning(f"  No archive available, skipping")
                still_failed += 1
                continue

            # Extract content from archived version
            content = extract_from_page(page, wb_url, url)
            if not content:
                log.warning(f"  Could not extract content from archive")
                still_failed += 1
                continue

            # Take screenshot if we don't have one
            ss_path = SCREENSHOTS_DIR / f"{year}-{outlet}-screenshot.png"
            if not ss_path.exists():
                try:
                    page.screenshot(path=str(ss_path), full_page=True)
                    log.info(f"  Screenshot saved: {ss_path.name}")
                except:
                    log.warning(f"  Screenshot failed")

            # Generate clean HTML
            html_output = generate_clean_html(content, article)
            html_path = HTML_DIR / f"{year}-{outlet}.html"
            html_path.write_text(html_output, encoding="utf-8")

            img_count = content["body_html"].count("<img")
            log.info(f"  HTML saved: {html_path.name} ({content['text_length']} chars, {img_count} images)")

            success += 1
            time.sleep(2)  # Be polite to archive.org

        browser.close()

    log.info(f"\n{'='*60}")
    log.info(f"Archive retry complete: {success} recovered, {still_failed} still failed")
    log.info(f"{'='*60}")


if __name__ == "__main__":
    main()
