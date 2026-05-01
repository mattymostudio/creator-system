#!/usr/bin/env python3
"""Convert a Facebook HTML data archive into an Obsidian vault."""

import os
import re
import html as html_mod
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup, NavigableString

# ── Config ──────────────────────────────────────────────────────────────────
ARCHIVE_DIR = Path(__file__).parent / "your_fb_archive"
HTML_DIR = ARCHIVE_DIR / "html"
PHOTOS_DIR = ARCHIVE_DIR / "photos"
OUTPUT_DIR = Path(__file__).parent / "obsidian-vault"
OWNER_NAME = "Jane D"
PEOPLE_THRESHOLD = 5  # minimum mentions to get a People note


# ── Helpers ─────────────────────────────────────────────────────────────────
def soup_from(filename):
    path = HTML_DIR / filename
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return BeautifulSoup(f.read(), "html.parser")


def clean_text(el):
    """Extract visible text from a BS element, normalising whitespace."""
    if el is None:
        return ""
    text = el.get_text(separator=" ", strip=True)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_links(el):
    """Return list of (text, href) tuples from <a> tags inside an element."""
    if el is None:
        return []
    return [(a.get_text(strip=True), a.get("href", "")) for a in el.find_all("a", href=True)]


def parse_timestamp(abbr_tag):
    """Parse ISO timestamp from <abbr class='time published' title='...'>."""
    if abbr_tag is None:
        return None
    iso = abbr_tag.get("title", "")
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("+0000", "+00:00"))
    except Exception:
        return None


def date_key(dt):
    """Return 'YYYY-MM' string."""
    return dt.strftime("%Y-%m") if dt else "unknown"


def sanitize_filename(name):
    """Make a string safe for use as a filename."""
    name = name.replace("/", "-").replace("\\", "-")
    name = re.sub(r'[<>:"|?*]', "", name)
    name = name.strip(". ")
    return name[:200] if name else "Untitled"


def mkdir(path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_md(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def entry_content_to_md(entry_el):
    """Convert a feedentry's content element to markdown, preserving links."""
    if entry_el is None:
        return ""
    parts = []
    for child in entry_el.children:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                parts.append(text)
        elif child.name == "a":
            href = child.get("href", "")
            text = child.get_text(strip=True)
            if href and text:
                parts.append(f"[{text}]({href})")
            elif href:
                parts.append(href)
        elif child.name == "br":
            parts.append("\n")
        elif child.name == "table" and "walllink" in (child.get("class") or []):
            link_a = child.find("a", href=True)
            if link_a:
                href = link_a.get("href", "")
                # Get the text description from the second td
                tds = child.find_all("td")
                link_text = ""
                for td in tds:
                    a = td.find("a")
                    if a and a.get_text(strip=True):
                        link_text = a.get_text(strip=True)
                desc_div = child.find("div")
                desc = clean_text(desc_div) if desc_div else ""
                if link_text:
                    parts.append(f"\n> [{link_text}]({href})")
                if desc:
                    parts.append(f"> {desc}")
        elif child.name == "div":
            text = clean_text(child)
            if text:
                parts.append(text)
        else:
            text = clean_text(child)
            if text:
                parts.append(text)
    result = " ".join(parts)
    result = result.replace(" \n ", "\n").replace("  ", " ")
    return result.strip()


# ── Parsers ─────────────────────────────────────────────────────────────────

def parse_profile():
    """Parse profile.html into a dict."""
    soup = soup_from("profile.html")
    if not soup:
        return {}
    profile = {}
    for row in soup.find_all("tr"):
        label_td = row.find("td", class_="profile_label")
        if not label_td:
            continue
        label = clean_text(label_td).rstrip(":")
        value_td = label_td.find_next_sibling("td")
        if not value_td:
            continue
        if label == "Family":
            members = []
            for fn in value_td.find_all("span", class_="fn"):
                name = clean_text(fn)
                # Get the text right after the span for the relationship
                next_text = fn.next_sibling
                rel = ""
                if next_text and isinstance(next_text, NavigableString):
                    rel = str(next_text).strip().strip("()")
                members.append({"name": name, "relationship": rel})
            profile[label] = members
        elif label == "Employers":
            text = clean_text(value_td)
            profile[label] = text
        elif label in ("Activities", "Interests", "Other"):
            pages = [clean_text(p) for p in value_td.find_all("span", class_="page")]
            profile[label] = pages
        else:
            profile[label] = clean_text(value_td)
    return profile


def parse_wall():
    """Parse wall.html into a list of post dicts."""
    soup = soup_from("wall.html")
    if not soup:
        return []
    posts = []
    for entry in soup.find_all("div", class_="feedentry"):
        author_el = entry.find("span", class_="fn")
        author = clean_text(author_el) if author_el else "Unknown"
        content_el = entry.find("span", class_="entry-content")
        content = entry_content_to_md(content_el)
        time_el = entry.find("abbr", class_="time")
        dt = parse_timestamp(time_el)
        time_display = clean_text(time_el) if time_el else ""
        comments = []
        comments_div = entry.find("div", class_="comments")
        if comments_div:
            for c in comments_div.find_all("div", class_="comment"):
                c_author_el = c.find("span", class_="fn")
                c_author = clean_text(c_author_el) if c_author_el else "Unknown"
                c_content_el = c.find("span", class_="entry-content")
                c_content = clean_text(c_content_el) if c_content_el else ""
                c_time_el = c.find("abbr", class_="time")
                c_time = clean_text(c_time_el) if c_time_el else ""
                comments.append({
                    "author": c_author,
                    "content": c_content,
                    "time": c_time,
                })
        posts.append({
            "author": author,
            "content": content,
            "datetime": dt,
            "time_display": time_display,
            "comments": comments,
        })
    return posts


def parse_messages():
    """Parse messages.html into a list of thread dicts."""
    soup = soup_from("messages.html")
    if not soup:
        return []
    threads = []
    for thread_div in soup.find_all("div", class_="thread"):
        messages = []
        for msg in thread_div.find_all("div", class_="message"):
            author_el = msg.find("span", class_="fn")
            author = clean_text(author_el) if author_el else "Unknown"
            time_el = msg.find("abbr", class_="time")
            dt = parse_timestamp(time_el)
            time_display = clean_text(time_el) if time_el else ""
            body_el = msg.find("div", class_="msgbody")
            body = ""
            if body_el:
                body = body_el.get_text(separator="\n", strip=True)
                body = body.replace("\xa0", " ")
            messages.append({
                "author": author,
                "datetime": dt,
                "time_display": time_display,
                "body": body,
            })
        if messages:
            # Identify the other participants (not the owner)
            participants = set()
            for m in messages:
                if m["author"] != OWNER_NAME and m["author"] != "Unknown":
                    participants.add(m["author"])
            thread_name = ", ".join(sorted(participants)) if participants else "Unknown"
            # Sort messages chronologically
            messages.sort(key=lambda m: m["datetime"] or datetime.min)
            threads.append({
                "participants": sorted(participants),
                "name": thread_name,
                "messages": messages,
            })
    return threads


def html_body_to_md(el):
    """Convert a rich HTML note body into markdown with paragraphs and links."""
    if el is None:
        return ""
    parts = []
    for p in el.find_all("p"):
        text_parts = []
        for child in p.children:
            if isinstance(child, NavigableString):
                t = str(child).strip()
                if t:
                    text_parts.append(t)
            elif child.name == "a":
                href = child.get("href", "")
                text = child.get_text(strip=True)
                # Skip twitter intent links, just use the text
                if "twitter.com/intent" in href:
                    text_parts.append(f"*{text}*")
                elif text and href:
                    text_parts.append(f"[{text}]({href})")
                elif text:
                    text_parts.append(text)
            elif child.name == "strong":
                t = child.get_text(strip=True)
                if t:
                    text_parts.append(f"**{t}**")
            elif child.name == "em":
                t = child.get_text(strip=True)
                if t:
                    text_parts.append(f"*{t}*")
            elif child.name == "img":
                # Skip inline images (old CDN links are dead anyway)
                pass
            elif child.name == "span" and child.find("img"):
                pass
            else:
                t = child.get_text(strip=True)
                if t:
                    text_parts.append(t)
        para = " ".join(text_parts).strip()
        if para:
            parts.append(para)
    if not parts:
        return el.get_text(separator="\n\n", strip=True)
    return "\n\n".join(parts)


def parse_notes():
    """Parse notes.html into a list of note dicts."""
    soup = soup_from("notes.html")
    if not soup:
        return []
    notes = []
    for note_div in soup.find_all("div", class_="note"):
        title_el = note_div.find("h2", class_="entry-title")
        title = clean_text(title_el) if title_el else "Untitled"
        time_el = note_div.find("abbr", class_="time", recursive=False)
        if not time_el:
            time_el = note_div.find("abbr", class_="time")
        dt = parse_timestamp(time_el)
        # Don't use get_text — malformed HTML causes it to grab the whole body
        time_display = dt.strftime("%B %d, %Y at %I:%M %p") if dt else ""
        # The actual class is "notebody" (no underscore)
        body_el = note_div.find("div", class_="notebody")
        if body_el:
            body = html_body_to_md(body_el)
        else:
            # Fallback: get just direct text, excluding comments
            comments_div = note_div.find("div", class_="comments")
            if comments_div:
                comments_div.extract()
            body = clean_text(note_div)
        comments = []
        comments_div = note_div.find("div", class_="comments")
        if comments_div:
            for c in comments_div.find_all("div", class_="comment"):
                c_author_el = c.find("span", class_="fn")
                c_author = clean_text(c_author_el) if c_author_el else "Unknown"
                c_content_el = c.find("span", class_="entry-content")
                c_content = clean_text(c_content_el) if c_content_el else ""
                c_time_el = c.find("abbr", class_="time")
                c_time = clean_text(c_time_el) if c_time_el else ""
                comments.append({
                    "author": c_author,
                    "content": c_content,
                    "time": c_time,
                })
        notes.append({
            "title": title,
            "datetime": dt,
            "time_display": time_display,
            "body": body,
            "comments": comments,
        })
    return notes


def parse_events():
    """Parse events.html into a list of event dicts."""
    soup = soup_from("events.html")
    if not soup:
        return []
    events = []
    for ev in soup.find_all("div", class_="event"):
        title_el = ev.find("h2")
        title = clean_text(title_el) if title_el else "Untitled Event"
        host_el = ev.find("span", class_="fn")
        if not host_el:
            host_el = ev.find("span", class_="page")
        host = clean_text(host_el) if host_el else "Unknown"
        desc_el = ev.find("div", class_="description")
        desc = desc_el.get_text(separator="\n", strip=True) if desc_el else ""
        # Location is in text after a <br/> but before the description div
        location = ""
        desc_el_ref = ev.find("div", class_="description")
        for br in ev.find_all("br"):
            # Skip <br/> tags inside the description
            if desc_el_ref and br.find_parent("div", class_="description"):
                continue
            next_text = br.next_sibling
            if next_text and isinstance(next_text, NavigableString):
                loc = str(next_text).strip()
                if loc and loc != "()" and len(loc) > 3 and "(" not in loc[:2]:
                    # Clean trailing () artifact
                    location = re.sub(r'\s*\(\)\s*$', '', loc).strip()
                    break
        events.append({
            "title": title,
            "host": host,
            "description": desc.replace("\n", "\n\n"),
            "location": location,
        })
    return events


def parse_friends():
    """Parse friends.html into a list of names."""
    soup = soup_from("friends.html")
    if not soup:
        return []
    return [clean_text(fn) for fn in soup.find_all("span", class_="fn")]


def parse_albums():
    """Parse album-*.html files and photo directories."""
    albums = []
    for f in sorted(HTML_DIR.glob("album-*.html")):
        album_name = f.stem.replace("album-", "")
        album_name = unquote(album_name)
        soup = soup_from(f.name)
        if not soup:
            continue
        title_el = soup.find("h2")
        title = clean_text(title_el) if title_el else album_name
        photos = []
        for photo_div in soup.find_all("div", class_="photo-container"):
            img = photo_div.find("img", class_="photo")
            src = img.get("src", "") if img else ""
            time_el = photo_div.find("abbr", class_="time")
            dt = parse_timestamp(time_el)
            time_display = clean_text(time_el) if time_el else ""
            # Get caption if any
            caption_parts = []
            for child in photo_div.children:
                if isinstance(child, NavigableString):
                    t = str(child).strip()
                    if t:
                        caption_parts.append(t)
            caption = " ".join(caption_parts)
            photos.append({
                "src": src,
                "datetime": dt,
                "time_display": time_display,
                "caption": caption,
            })
        albums.append({
            "name": title,
            "filename": f.name,
            "photo_count": len(photos),
            "photos": photos,
        })
    return albums


# ── People Frequency Analysis ───────────────────────────────────────────────

def count_people(wall_posts, threads, friends_list):
    """Count how often each person's name appears across all data."""
    counter = Counter()
    # Wall post authors and commenters
    for post in wall_posts:
        if post["author"] != OWNER_NAME:
            counter[post["author"]] += 1
        for c in post["comments"]:
            if c["author"] != OWNER_NAME:
                counter[c["author"]] += 1
    # Message participants
    for thread in threads:
        for p in thread["participants"]:
            counter[p] += len(thread["messages"])
    # Remove 'Unknown'
    counter.pop("Unknown", None)
    return counter


# ── Generators ──────────────────────────────────────────────────────────────

def wikilink(name, key_people_set):
    """Wrap a name in [[wikilinks]] if it's a key person."""
    if name in key_people_set:
        return f"[[{name}]]"
    return name


def generate_profile(profile, key_people):
    out_dir = mkdir(OUTPUT_DIR / "Profile")
    kp = set(key_people)
    lines = [
        "---",
        f'name: "Jane Doe"',
        f'aliases: ["{OWNER_NAME}", "your_fb_archive"]',
        f'birthday: "1985-07-13"',
        f'location: "{profile.get("Current City", "")}"',
        f'education: "Your University"',
        f'employer: "YourCompany (Founder, CEO)"',
        "tags: [facebook/profile]",
        "---",
        "",
        "# Jane Doe",
        "",
        f"> {profile.get('Bio', '')}".replace("<BR>", "\n> "),
        "",
        "## Career",
        f"- **YourCompany** — Founder, CEO (Aug 2011 – present at time of export)",
        f"- **Your University** — Education",
        "",
        "## Family",
    ]
    family = profile.get("Family", [])
    if isinstance(family, list):
        for m in family:
            name = wikilink(m["name"], kp)
            rel = m.get("relationship", "")
            lines.append(f"- {name}" + (f" ({rel})" if rel else ""))
    lines += [
        "",
        "## Timeline",
    ]
    for year in range(2006, 2013):
        lines.append(f"- [[{year}]]")
    lines += [
        "",
        "## Photo Albums",
    ]
    for album_dir in sorted(PHOTOS_DIR.iterdir()):
        if album_dir.is_dir():
            lines.append(f"- [[{album_dir.name}]]")
    lines += [
        "",
        f"## Links",
        f"- Website: {profile.get('Website', '')}",
        f"- Facebook: {profile.get('Facebook Profile', '')}",
        f"- Email: {profile.get('Email', '')}",
    ]
    write_md(out_dir / "Jane Doe.md", "\n".join(lines))


def generate_timeline(wall_posts, key_people):
    kp = set(key_people)
    years_dir = mkdir(OUTPUT_DIR / "Timeline" / "Years")
    months_dir = mkdir(OUTPUT_DIR / "Timeline" / "Months")

    # Group posts by month
    by_month = defaultdict(list)
    for post in wall_posts:
        key = date_key(post["datetime"])
        by_month[key].append(post)

    # Group months by year
    by_year = defaultdict(set)
    for month_key in by_month:
        if month_key != "unknown":
            year = month_key[:4]
            by_year[year].add(month_key)

    # Generate monthly notes
    for month_key, posts in sorted(by_month.items()):
        if month_key == "unknown":
            continue
        posts_sorted = sorted(posts, key=lambda p: p["datetime"] or datetime.min)
        try:
            month_label = datetime.strptime(month_key, "%Y-%m").strftime("%B %Y")
        except Exception:
            month_label = month_key
        lines = [
            "---",
            f"month: {month_key}",
            f"post_count: {len(posts_sorted)}",
            "tags: [facebook/wall, timeline]",
            "---",
            "",
            f"# {month_label}",
            "",
            f"*{len(posts_sorted)} posts*",
            "",
            "---",
            "",
        ]
        for post in posts_sorted:
            author = wikilink(post["author"], kp)
            time_str = post["time_display"] or "unknown time"
            content = post["content"]
            # Add wikilinks for known people in content
            for person in kp:
                if person in content and person != OWNER_NAME:
                    content = content.replace(person, f"[[{person}]]")
            lines.append(f"### {time_str}")
            if post["author"] != OWNER_NAME:
                lines.append(f"**{author}** wrote on your wall:")
            lines.append("")
            if content:
                lines.append(content)
                lines.append("")
            visible_comments = [c for c in post["comments"]
                                if c["author"] != "Unknown" or c["content"]]
            if visible_comments:
                for c in visible_comments:
                    if c["author"] == "Unknown" and not c["content"]:
                        continue
                    c_author = wikilink(c["author"], kp)
                    lines.append(f"- **{c_author}**: {c['content']}")
                lines.append("")
            lines.append("---")
            lines.append("")

        write_md(months_dir / f"{month_key}.md", "\n".join(lines))

    # Generate yearly notes
    for year, months in sorted(by_year.items()):
        total_posts = sum(len(by_month[m]) for m in months)
        # Count top people for this year
        year_people = Counter()
        for m in months:
            for post in by_month[m]:
                if post["author"] != OWNER_NAME:
                    year_people[post["author"]] += 1
                for c in post["comments"]:
                    if c["author"] != OWNER_NAME:
                        year_people[c["author"]] += 1
        year_people.pop("Unknown", None)
        top_people = year_people.most_common(15)
        lines = [
            "---",
            f"year: {year}",
            f"post_count: {total_posts}",
            "tags: [facebook/wall, timeline, yearly]",
            "---",
            "",
            f"# {year}",
            "",
            f"**{total_posts} wall posts** across {len(months)} active months.",
            "",
            "## Months",
            "",
        ]
        for m in sorted(months):
            count = len(by_month[m])
            try:
                label = datetime.strptime(m, "%Y-%m").strftime("%B")
            except Exception:
                label = m
            lines.append(f"- [[{m}|{label}]] ({count} posts)")
        lines += [
            "",
            "## Top People",
            "",
        ]
        for person, count in top_people:
            p = wikilink(person, kp)
            lines.append(f"- {p} ({count} interactions)")
        lines.append("")
        write_md(years_dir / f"{year}.md", "\n".join(lines))


def generate_messages(threads, key_people):
    kp = set(key_people)
    out_dir = mkdir(OUTPUT_DIR / "Messages")
    # Group threads by participant name (merge duplicates)
    by_name = defaultdict(list)
    for thread in threads:
        by_name[thread["name"]].append(thread)

    for name, thread_list in sorted(by_name.items()):
        safe_name = sanitize_filename(name)
        all_messages = []
        for t in thread_list:
            all_messages.extend(t["messages"])
        all_messages.sort(key=lambda m: m["datetime"] or datetime.min)
        participants = set()
        for t in thread_list:
            participants.update(t["participants"])

        lines = [
            "---",
            f'participants: ["{name}"]',
            f"message_count: {len(all_messages)}",
            "tags: [facebook/messages]",
            "---",
            "",
            f"# Messages with {name}",
            "",
        ]
        current_date = None
        for msg in all_messages:
            if not msg["body"] and msg["author"] == "Unknown":
                continue
            msg_date = msg["datetime"].strftime("%Y-%m-%d") if msg["datetime"] else None
            if msg_date and msg_date != current_date:
                current_date = msg_date
                lines.append(f"## {msg['datetime'].strftime('%B %d, %Y') if msg['datetime'] else 'Unknown date'}")
                lines.append("")
            author = wikilink(msg["author"], kp)
            time = msg["datetime"].strftime("%I:%M %p") if msg["datetime"] else ""
            body = msg["body"]
            if body:
                lines.append(f"**{author}** ({time}):")
                lines.append(f"> {body}")
                lines.append("")
        write_md(out_dir / f"{safe_name}.md", "\n".join(lines))


def generate_notes(notes, key_people):
    kp = set(key_people)
    out_dir = mkdir(OUTPUT_DIR / "Notes")
    for note in notes:
        safe_title = sanitize_filename(note["title"])
        date_str = note["datetime"].isoformat() if note["datetime"] else ""
        lines = [
            "---",
            f'title: "{note["title"]}"',
            f'date: "{date_str}"',
            "tags: [facebook/notes, career]",
            "---",
            "",
            f"# {note['title']}",
            "",
            f"*Published: {note['time_display']}*",
            "",
        ]
        # Add body with proper paragraph breaks
        body = note["body"]
        # Add wikilinks for key people
        for person in kp:
            if person in body and person != OWNER_NAME:
                body = body.replace(person, f"[[{person}]]")
        lines.append(body)
        lines.append("")
        if note["comments"]:
            lines.append("---")
            lines.append("")
            lines.append("## Comments")
            lines.append("")
            for c in note["comments"]:
                author = wikilink(c["author"], kp)
                lines.append(f"- **{author}** ({c['time']}): {c['content']}")
            lines.append("")
        write_md(out_dir / f"{safe_title}.md", "\n".join(lines))


def generate_events(events):
    out_dir = mkdir(OUTPUT_DIR / "Events")
    for ev in events:
        safe_title = sanitize_filename(ev["title"])[:80]
        clean_title = ev["title"].replace('"', '\\"')
        clean_loc = ev["location"].replace('"', '\\"').replace('\n', ' ')
        lines = [
            "---",
            f'event: "{clean_title}"',
            f'host: "{ev["host"]}"',
            f'location: "{clean_loc}"',
            "tags: [facebook/events]",
            "---",
            "",
            f"# {ev['title']}",
            "",
            f"**Host**: {ev['host']}",
        ]
        if ev["location"]:
            lines.append(f"**Location**: {ev['location']}")
        lines += [
            "",
            ev["description"],
            "",
        ]
        write_md(out_dir / f"{safe_title}.md", "\n".join(lines))


def generate_albums(albums):
    out_dir = mkdir(OUTPUT_DIR / "Albums")
    for album in albums:
        safe_name = sanitize_filename(album["name"])
        lines = [
            "---",
            f'album: "{album["name"]}"',
            f"photo_count: {album['photo_count']}",
            "tags: [facebook/photos]",
            "---",
            "",
            f"# {album['name']}",
            "",
            f"*{album['photo_count']} photos*",
            "",
        ]
        for photo in album["photos"]:
            src = photo["src"]
            if src.startswith("../"):
                # Convert to relative path from vault
                src = src.replace("../", "")
            time_str = photo["time_display"]
            caption = photo["caption"]
            lines.append(f"- `{src}`" + (f" — {time_str}" if time_str else ""))
            if caption:
                lines.append(f"  {caption}")
        lines.append("")
        write_md(out_dir / f"{safe_name}.md", "\n".join(lines))


def generate_people(people_counts, wall_posts, threads, key_people):
    kp = set(key_people)
    out_dir = mkdir(OUTPUT_DIR / "People")
    for person in sorted(key_people):
        count = people_counts[person]
        # Gather wall post appearances
        wall_mentions = []
        for post in wall_posts:
            dominated = False
            if post["author"] == person:
                dominated = True
            for c in post["comments"]:
                if c["author"] == person:
                    dominated = True
            if dominated:
                date_str = post["datetime"].strftime("%Y-%m-%d") if post["datetime"] else "unknown"
                month = date_key(post["datetime"])
                wall_mentions.append((date_str, month))

        # Gather message thread info
        msg_threads = []
        for t in threads:
            if person in t["participants"]:
                msg_count = len(t["messages"])
                first = t["messages"][0]["datetime"]
                last = t["messages"][-1]["datetime"]
                msg_threads.append((msg_count, first, last))

        safe_name = sanitize_filename(person)
        lines = [
            "---",
            f'name: "{person}"',
            f"mention_count: {count}",
            "tags: [facebook/people]",
            "---",
            "",
            f"# {person}",
            "",
            f"*{count} total interactions across the archive*",
            "",
        ]
        if wall_mentions:
            lines.append("## Wall Activity")
            lines.append("")
            # Summarise by month
            month_counts = Counter(m for _, m in wall_mentions)
            for month, mc in sorted(month_counts.items()):
                lines.append(f"- [[{month}]] — {mc} posts/comments")
            lines.append("")

        if msg_threads:
            lines.append("## Messages")
            lines.append("")
            for mc, first, last in msg_threads:
                first_str = first.strftime("%b %Y") if first else "?"
                last_str = last.strftime("%b %Y") if last else "?"
                lines.append(f"- [[{sanitize_filename(person)}|Conversation]]: {mc} messages ({first_str} – {last_str})")
            lines.append("")

        write_md(out_dir / f"{safe_name}.md", "\n".join(lines))


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    print("Parsing Facebook archive...")

    print("  Profile...")
    profile = parse_profile()

    print("  Wall posts...")
    wall_posts = parse_wall()
    print(f"    → {len(wall_posts)} posts")

    print("  Messages...")
    threads = parse_messages()
    print(f"    → {len(threads)} threads")

    print("  Notes...")
    notes = parse_notes()
    print(f"    → {len(notes)} notes")

    print("  Events...")
    events = parse_events()
    print(f"    → {len(events)} events")

    print("  Friends...")
    friends = parse_friends()
    print(f"    → {len(friends)} friends")

    print("  Albums...")
    albums = parse_albums()
    print(f"    → {len(albums)} albums")

    print("\nAnalysing people frequency...")
    people_counts = count_people(wall_posts, threads, friends)
    key_people = [name for name, count in people_counts.most_common() if count >= PEOPLE_THRESHOLD]
    print(f"  → {len(key_people)} key people (≥{PEOPLE_THRESHOLD} mentions)")

    print("\nGenerating Obsidian vault...")

    print("  Profile...")
    generate_profile(profile, key_people)

    print("  Timeline (yearly + monthly)...")
    generate_timeline(wall_posts, key_people)

    print("  Messages...")
    generate_messages(threads, key_people)

    print("  Notes...")
    generate_notes(notes, key_people)

    print("  Events...")
    generate_events(events)

    print("  Albums...")
    generate_albums(albums)

    print("  People...")
    generate_people(people_counts, wall_posts, threads, key_people)

    # Summary
    file_count = sum(1 for _ in OUTPUT_DIR.rglob("*.md"))
    print(f"\nDone! Generated {file_count} markdown files in {OUTPUT_DIR}")
    print(f"\nVault structure:")
    for d in sorted(OUTPUT_DIR.iterdir()):
        if d.is_dir():
            count = sum(1 for _ in d.rglob("*.md"))
            print(f"  {d.name}/  ({count} files)")


if __name__ == "__main__":
    main()
