#!/usr/bin/env python3
"""
Retry failed press articles using Playwright-based extraction.
Falls back to extracting content from the rendered DOM since these sites
block server-side fetching but render fine in a real browser.
"""

import os
import re
import json
import time
import logging
from pathlib import Path
from urllib.parse import urlparse

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


# DUMMY DATA — replace with your own failed-article list, extracted from
# the processing log of an earlier run of process_articles.py.
# "dead": True marks links we expect to need the Wayback Machine.
FAILED_ARTICLES = [
    {"url": "https://www.example-magazine.example/2024/05/sample-artist-profile/", "year": "2024", "outlet": "example-magazine", "headline": "Sample Artist Profile"},
    {"url": "https://www.example-news.example/arts/2023/sample-exhibition.html", "year": "2023", "outlet": "example-news", "headline": "Sample Exhibition Opens"},
    {"url": "https://www.example-paper.example/story/2022/community-art-project/12345.html", "year": "2022", "outlet": "example-paper", "headline": "Community Art Project Launches", "dead": True},
]


# Elements to remove from extracted content
REMOVE_SELECTORS = [
    "nav", "header", "footer", ".nav", ".header", ".footer",
    ".sidebar", "aside", ".ad", ".ads", ".advertisement",
    ".social-share", ".share-buttons", ".social-buttons",
    ".newsletter", ".signup", ".subscribe",
    ".related", ".recommended", ".more-stories", ".read-next",
    ".comments", "#comments", ".comment-section",
    ".cookie", ".consent", ".gdpr", ".privacy-banner",
    "script", "style", "noscript", "iframe",
    ".video-player", ".embed",
    "[data-ad]", "[data-advertisement]",
    ".sponsored", ".promo", ".promotion",
    ".breadcrumb", ".breadcrumbs",
    ".tags", ".tag-list",
    ".author-bio", ".author-card",
    "form",
    ".paywall", ".subscriber-only", ".premium-content",
    ".sticky-header", ".sticky-footer",
    ".modal", ".overlay", ".popup",
    ".skip-link", ".screen-reader-text",
]


def extract_via_playwright(page, url):
    """Extract article content from the rendered DOM using Playwright."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(5000)

        # Dismiss cookie/consent banners
        for selector in [
            "button:has-text('Accept')", "button:has-text('OK')",
            "button:has-text('Got it')", "button:has-text('I agree')",
            "button:has-text('Continue')", "button:has-text('Agree')",
            "[class*='cookie'] button", "[id*='cookie'] button",
            "[class*='consent'] button", "button:has-text('Allow')",
        ]:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=1000):
                    btn.click(timeout=2000)
                    page.wait_for_timeout(1000)
                    break
            except:
                continue

        # Try to scroll down to trigger lazy loading
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        page.wait_for_timeout(2000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        # Get the full rendered HTML
        html = page.content()
        return html

    except PlaywrightTimeout:
        log.warning(f"  Timeout loading {url}")
        try:
            return page.content()
        except:
            return None
    except Exception as e:
        log.error(f"  Failed to load {url}: {e}")
        return None


def clean_dom_html(raw_html, url):
    """Parse rendered HTML and extract just the article content with images."""
    soup = BeautifulSoup(raw_html, "lxml")
    parsed = urlparse(url)

    # Try to find the article container
    article = None
    for selector_fn in [
        lambda s: s.find("article"),
        lambda s: s.find(attrs={"role": "article"}),
        lambda s: s.find(class_=re.compile(r"article.*(body|content)", re.I)),
        lambda s: s.find(class_=re.compile(r"(post|entry|story).*(content|body)", re.I)),
        lambda s: s.find(id=re.compile(r"article|story|content|post", re.I)),
        lambda s: s.find(class_=re.compile(r"^article$|^post$|^story$|^content$", re.I)),
        lambda s: s.find(attrs={"data-testid": re.compile(r"article|story", re.I)}),
    ]:
        result = selector_fn(soup)
        if result:
            article = result
            break

    if not article:
        # Fallback: find the main content area
        article = soup.find("main") or soup.find(id="main") or soup.find(class_="main")

    if not article:
        log.warning("  Could not find article container, using body")
        article = soup.find("body")

    if not article:
        return None

    # Remove unwanted elements
    for selector in REMOVE_SELECTORS:
        for el in article.select(selector):
            el.decompose()

    # Remove HTML comments
    for comment in article.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove hidden elements
    for el in article.find_all(style=re.compile(r"display:\s*none|visibility:\s*hidden")):
        el.decompose()

    # Remove empty divs/spans
    for tag in article.find_all(["div", "span"]):
        if not tag.get_text(strip=True) and not tag.find("img"):
            tag.decompose()

    # Extract metadata
    title = ""
    title_el = article.find(["h1", "h2"])
    if title_el:
        title = title_el.get_text(strip=True)

    # Look for author
    author = ""
    for pattern in [r"author", r"byline", r"writer"]:
        author_el = article.find(class_=re.compile(pattern, re.I))
        if author_el:
            author = author_el.get_text(strip=True)
            # Clean up common prefixes
            author = re.sub(r"^(By|Written by|Author:?)\s*", "", author, flags=re.I).strip()
            break

    # If no author in article, check meta tags
    if not author:
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author:
            author = meta_author.get("content", "")

    # Look for date
    date = ""
    time_el = article.find("time")
    if time_el:
        date = time_el.get("datetime", "") or time_el.get_text(strip=True)
    if not date:
        date_el = article.find(class_=re.compile(r"date|time|published", re.I))
        if date_el:
            date = date_el.get_text(strip=True)
    if not date:
        meta_date = soup.find("meta", attrs={"property": "article:published_time"})
        if meta_date:
            date = meta_date.get("content", "")[:10]

    # If no title found in article, try the page title
    if not title:
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title:
            title = og_title.get("content", "")
        elif soup.find("title"):
            title = soup.find("title").get_text(strip=True)

    # Get the sitename
    sitename = ""
    og_site = soup.find("meta", attrs={"property": "og:site_name"})
    if og_site:
        sitename = og_site.get("content", "")

    # Process images - fix relative URLs and remove ad images
    ad_patterns = [
        "ad", "ads", "advert", "banner", "promo", "sponsor",
        "pixel", "tracking", "beacon", "analytics",
        "doubleclick", "googlesyndication", "amazon-adsystem",
        "taboola", "outbrain", "1x1", "spacer", "blank.gif",
        "clear.gif", "logo", "icon", "avatar", "badge",
    ]

    for img in article.find_all("img"):
        src = img.get("src", "") or img.get("data-src", "") or img.get("data-lazy-src", "")
        if not src:
            img.decompose()
            continue

        # Use data-src or data-lazy-src if src is a placeholder
        if "data:" in (img.get("src", "")) or "placeholder" in (img.get("src", "").lower()):
            src = img.get("data-src", "") or img.get("data-lazy-src", "") or img.get("data-original", "")
            if src:
                img["src"] = src

        src_lower = src.lower()

        should_remove = False
        for pattern in ad_patterns:
            if pattern in src_lower and pattern not in url.lower():
                should_remove = True
                break

        # Remove tiny tracking images
        width = img.get("width", "")
        height = img.get("height", "")
        try:
            if width and height:
                w = int(str(width).replace("px", ""))
                h = int(str(height).replace("px", ""))
                if w < 50 or h < 50:
                    should_remove = True
        except (ValueError, TypeError):
            pass

        if src.startswith("data:"):
            should_remove = True

        # Fix relative URLs
        if src and not src.startswith(("http://", "https://", "data:")):
            if src.startswith("//"):
                img["src"] = "https:" + src
            elif src.startswith("/"):
                img["src"] = f"{parsed.scheme}://{parsed.netloc}{src}"

        if should_remove:
            parent = img.parent
            img.decompose()
            if parent and parent.name == "figure" and not parent.find("img"):
                parent.decompose()

    # Strip all attributes except essentials from remaining elements
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

    # Get cleaned body HTML
    body_html = ""
    for child in article.children:
        s = str(child).strip()
        if s:
            body_html += s + "\n"

    return {
        "title": title,
        "author": author,
        "date": date,
        "sitename": sitename,
        "body_html": body_html,
    }


def generate_clean_html(content, article_info):
    """Generate a clean HTML file from extracted content."""
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
    byline = " &middot; ".join(byline_parts) if byline_parts else ""

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
    h2, h3 {{
      font-size: 1.3em;
      margin-top: 1.5em;
      margin-bottom: 0.5em;
    }}
    .byline {{
      font-size: 14px;
      color: #666;
      margin-bottom: 32px;
    }}
    .article-body p {{
      margin-bottom: 1.2em;
    }}
    .article-body img {{
      max-width: 100%;
      height: auto;
      margin: 24px 0;
      display: block;
    }}
    .article-body figure {{
      margin: 24px 0;
    }}
    .article-body figcaption {{
      font-size: 13px;
      color: #888;
      margin-top: 8px;
      margin-bottom: 24px;
    }}
    .article-body a {{
      color: #333;
      text-decoration: underline;
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


def update_log(year, outlet, headline, has_screenshot, has_html, notes=""):
    """Update existing log entry or append new one."""
    ss = "yes" if has_screenshot else "no"
    ht = "yes" if has_html else "no"
    headline_short = headline[:80] + "..." if len(headline) > 80 else headline
    new_line = f"| done | {year} | {outlet} | {headline_short} | {ss} | {ht} | {notes} |"

    log_content = LOG_FILE.read_text()
    lines = log_content.split("\n")

    # Try to find and update existing entry for this outlet/year
    updated = False
    for i, line in enumerate(lines):
        if f"| {year} |" in line and outlet.replace("-2", "").replace("-3", "").replace("-4", "").replace("-5", "").replace("-6", "") in line:
            if "partial" in line or "dead-link" in line:
                lines[i] = new_line
                updated = True
                break

    if updated:
        LOG_FILE.write_text("\n".join(lines))
    else:
        with open(LOG_FILE, "a") as f:
            f.write(new_line + "\n")


def main():
    log.info(f"Retrying {len(FAILED_ARTICLES)} failed articles using Playwright extraction")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        success = 0
        still_failed = 0

        for i, article in enumerate(FAILED_ARTICLES):
            url = article["url"]
            year = article["year"]
            outlet = article["outlet"]
            headline = article["headline"]
            is_dead = article.get("dead", False)

            log.info(f"\n[{i+1}/{len(FAILED_ARTICLES)}] Retrying: {outlet} ({year})")
            log.info(f"  URL: {url}")

            # Get rendered HTML
            raw_html = extract_via_playwright(page, url)
            if not raw_html:
                log.warning(f"  Still cannot load page")
                still_failed += 1
                continue

            # Take screenshot if dead link that now works
            ss_path = SCREENSHOTS_DIR / f"{year}-{outlet}-screenshot.png"
            has_screenshot = ss_path.exists()
            if is_dead and not has_screenshot:
                try:
                    page.screenshot(path=str(ss_path), full_page=True)
                    has_screenshot = True
                    log.info(f"  Screenshot saved: {ss_path.name}")
                except:
                    log.warning(f"  Screenshot failed")

            # Check if we got a real page or an error page
            if "404" in page.title() or "not found" in page.title().lower() or "error" in page.title().lower():
                log.warning(f"  Page returned 404/error")
                still_failed += 1
                continue

            # Extract content from rendered DOM
            content = clean_dom_html(raw_html, url)
            if not content or not content.get("body_html", "").strip():
                log.warning(f"  Could not extract content from rendered page")
                still_failed += 1
                continue

            # Check if we got meaningful content (not just nav/boilerplate)
            text_content = BeautifulSoup(content["body_html"], "lxml").get_text(strip=True)
            if len(text_content) < 100:
                log.warning(f"  Extracted content too short ({len(text_content)} chars)")
                still_failed += 1
                continue

            # Generate clean HTML
            html_output = generate_clean_html(content, article)
            html_path = HTML_DIR / f"{year}-{outlet}.html"
            html_path.write_text(html_output, encoding="utf-8")
            log.info(f"  HTML saved: {html_path.name} ({len(text_content)} chars)")

            # Count images
            img_count = content["body_html"].count("<img")
            if img_count:
                log.info(f"  Images found: {img_count}")

            # Update log
            update_log(year, outlet, headline, has_screenshot, True, "retry-playwright")
            success += 1

            time.sleep(1)

        browser.close()

    log.info(f"\n{'='*60}")
    log.info(f"Retry complete: {success} recovered, {still_failed} still failed")
    log.info(f"{'='*60}")


if __name__ == "__main__":
    main()
