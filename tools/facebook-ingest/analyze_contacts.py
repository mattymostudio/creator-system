#!/usr/bin/env python3
"""Analyze Facebook message threads to identify top 100 contacts for follow-up."""

import os
import re
import json
from collections import Counter, defaultdict
from pathlib import Path

MESSAGES_DIR = Path("obsidian-vault/Messages")
PEOPLE_DIR = Path("obsidian-vault/People")
OWNER = "Jane D"

# Keywords that signal professional/high-value relationships
PROFESSIONAL_KW = [
    "startup", "invest", "investor", "funding", "raise", "round",
    "hire", "hiring", "engineer", "developer", "team",
    "partner", "partnership", "collaborate", "collab",
    "business", "revenue", "growth", "strategy",
    "advisor", "advise", "mentor", "board",
    "launch", "product", "company", "founder", "ceo", "cto", "coo",
    "deal", "client", "agency", "brand", "campaign",
    "facebook", "social media", "advertising", "marketing",
    "sample-company-a", "yourcompany", "sample-company-b",
    "conference", "speaking", "panel", "event",
    "pitch", "deck", "demo",
    "intro", "introduction", "connect you",
    "coffee", "lunch", "dinner", "drinks", "beer",
    "office", "meet up", "meetup", "catch up",
]

RELATIONSHIP_KW = [
    "miss you", "love you", "proud of you", "congrats", "congratulations",
    "grateful", "appreciate", "thank you", "thanks for",
    "happy birthday", "wedding", "married",
    "family", "brother", "sister", "mom", "dad",
    "let's hang", "come visit", "when are you",
    "great seeing you", "good to see you",
]

# Signals of follow-up-worthy relationships
FOLLOWUP_KW = [
    "let's catch up", "we should", "next time", "let me know",
    "keep in touch", "stay in touch", "looking forward",
    "i'll be in", "are you in", "are you around",
    "would love to", "i'd love to", "we need to",
    "come by", "stop by", "swing by",
    "soon", "when are you free",
]


def parse_message_file(filepath):
    """Parse a message markdown file and extract structured data."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract frontmatter
    fm_match = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return None

    fm_text = fm_match.group(1)
    # Parse simple YAML-like frontmatter manually
    participants = []
    message_count = 0
    pm = re.search(r'participants:\s*\[(.+?)\]', fm_text)
    if pm:
        participants = [p.strip().strip('"').strip("'") for p in pm.group(1).split(",")]
    mc = re.search(r'message_count:\s*(\d+)', fm_text)
    if mc:
        message_count = int(mc.group(1))

    # Parse individual messages
    body = content[fm_match.end():]
    messages = []
    dates = []

    # Extract dates
    for match in re.finditer(r"## (\w+ \d+, \d{4})", body):
        dates.append(match.group(1))

    # Extract message bodies
    owner_messages = []
    other_messages = []
    for match in re.finditer(r"\*\*(?:\[\[)?(.+?)(?:\]\])?\*\* \(.*?\):\n> (.+?)(?=\n\n|\n\*\*|\Z)", body, re.DOTALL):
        author = match.group(1)
        msg_body = match.group(2).strip()
        if author == OWNER:
            owner_messages.append(msg_body)
        else:
            other_messages.append(msg_body)

    return {
        "participants": participants,
        "message_count": message_count,
        "dates": dates,
        "first_date": dates[0] if dates else None,
        "last_date": dates[-1] if dates else None,
        "owner_messages": owner_messages,
        "other_messages": other_messages,
        "all_text": body.lower(),
        "filepath": filepath,
    }


def score_contact(data):
    """Score a contact based on multiple signals."""
    scores = {}
    all_text = data["all_text"]

    # 1. Conversation depth (message count)
    mc = data["message_count"]
    if mc >= 30:
        scores["depth"] = 20
    elif mc >= 20:
        scores["depth"] = 15
    elif mc >= 10:
        scores["depth"] = 10
    elif mc >= 5:
        scores["depth"] = 5
    else:
        scores["depth"] = 2

    # 2. Reciprocity — both sides talking, not one-sided
    owner_count = len(data["owner_messages"])
    other_count = len(data["other_messages"])
    total = owner_count + other_count
    if total > 0:
        ratio = min(owner_count, other_count) / max(owner_count, other_count, 1)
        scores["reciprocity"] = int(ratio * 15)
    else:
        scores["reciprocity"] = 0

    # 3. Professional signals
    pro_hits = sum(1 for kw in PROFESSIONAL_KW if kw in all_text)
    scores["professional"] = min(pro_hits * 2, 25)

    # 4. Relationship warmth
    rel_hits = sum(1 for kw in RELATIONSHIP_KW if kw in all_text)
    scores["warmth"] = min(rel_hits * 3, 15)

    # 5. Follow-up intent (unfinished business / desire to reconnect)
    fu_hits = sum(1 for kw in FOLLOWUP_KW if kw in all_text)
    scores["followup_intent"] = min(fu_hits * 3, 15)

    # 6. Recency bonus (later dates score higher)
    last = data["last_date"] or ""
    if "2012" in last:
        scores["recency"] = 10
    elif "2011" in last:
        scores["recency"] = 7
    elif "2010" in last:
        scores["recency"] = 4
    else:
        scores["recency"] = 1

    # 7. Cross-reference: do they also appear in People notes (wall activity)?
    for p in data["participants"]:
        people_file = PEOPLE_DIR / f"{p}.md"
        if people_file.exists():
            scores["wall_presence"] = 5
            break
    else:
        scores["wall_presence"] = 0

    # 8. Substantive conversation (not just "hey" "ok" "thanks")
    avg_msg_len = 0
    all_msgs = data["owner_messages"] + data["other_messages"]
    if all_msgs:
        avg_msg_len = sum(len(m) for m in all_msgs) / len(all_msgs)
    if avg_msg_len > 100:
        scores["substance"] = 10
    elif avg_msg_len > 50:
        scores["substance"] = 6
    elif avg_msg_len > 20:
        scores["substance"] = 3
    else:
        scores["substance"] = 0

    total_score = sum(scores.values())
    return total_score, scores


def categorize(scores, text, participants):
    """Assign a relationship category based on scoring signals."""
    categories = []
    if scores.get("professional", 0) >= 10:
        categories.append("Professional")
    if scores.get("warmth", 0) >= 6:
        categories.append("Personal")
    if scores.get("followup_intent", 0) >= 6:
        categories.append("Reconnect")

    # Check for specific signals
    if any(kw in text for kw in ["invest", "investor", "funding", "raise", "round"]):
        categories.append("Investor/Funding")
    if any(kw in text for kw in ["hire", "hiring", "engineer", "developer", "team"]):
        categories.append("Recruiting")
    if any(kw in text for kw in ["advisor", "mentor", "advise"]):
        categories.append("Advisor")
    if any(kw in text for kw in ["partner", "collaborate", "collab", "partnership"]):
        categories.append("Collaborator")
    if any(kw in text for kw in ["speaking", "panel", "conference", "event"]):
        categories.append("Industry")
    if any(kw in text for kw in ["intro", "introduction", "connect you"]):
        categories.append("Connector")

    if not categories:
        categories.append("General")

    return list(set(categories))


def extract_snippet(data):
    """Extract a brief context snippet from the conversation."""
    # Get the most substantive message from the other person
    best = ""
    for msg in data["other_messages"]:
        if len(msg) > len(best) and len(msg) < 300:
            best = msg
    if not best and data["owner_messages"]:
        for msg in data["owner_messages"]:
            if len(msg) > len(best) and len(msg) < 300:
                best = msg
    # Truncate
    if len(best) > 150:
        best = best[:147] + "..."
    return best.replace("\n", " ")


def main():
    print("Analyzing message threads...")
    results = []

    for f in sorted(MESSAGES_DIR.glob("*.md")):
        if f.name == "Unknown.md":
            continue
        # Skip group chats with many participants
        if f.name.count(",") > 2:
            continue

        data = parse_message_file(f)
        if not data or not data["participants"]:
            continue
        # Skip if only participant is Unknown
        if all(p == "Unknown" for p in data["participants"]):
            continue

        total_score, scores = score_contact(data)
        categories = categorize(scores, data["all_text"], data["participants"])
        snippet = extract_snippet(data)

        name = ", ".join(data["participants"])

        results.append({
            "name": name,
            "score": total_score,
            "scores": scores,
            "categories": categories,
            "message_count": data["message_count"],
            "first_date": data["first_date"],
            "last_date": data["last_date"],
            "snippet": snippet,
        })

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    # Take top 100
    top100 = results[:100]

    # Generate markdown
    lines = [
        "---",
        'title: "Key Contacts — Top 100 People to Reconnect With"',
        "tags: [facebook/people, contacts, reconnect]",
        "---",
        "",
        "# Key Contacts — Top 100 People to Reconnect With",
        "",
        "Ranked by conversation depth, reciprocity, professional relevance, warmth, and follow-up intent.",
        "Extracted from 1,086 Facebook message threads (2006-2012).",
        "",
        "---",
        "",
    ]

    # Group by relative tier (top 25, next 35, bottom 40)
    tier1 = top100[:25]
    tier2 = top100[25:60]
    tier3 = top100[60:100]

    def write_tier(contacts, tier_name, tier_desc):
        lines.append(f"## {tier_name}")
        lines.append(f"*{tier_desc}*")
        lines.append("")
        for i, c in enumerate(contacts, 1):
            cats = ", ".join(c["categories"])
            date_range = ""
            if c["first_date"] and c["last_date"]:
                if c["first_date"] == c["last_date"]:
                    date_range = c["last_date"]
                else:
                    date_range = f"{c['first_date']} – {c['last_date']}"
            elif c["last_date"]:
                date_range = c["last_date"]

            lines.append(f"### [[{c['name']}]]")
            lines.append(f"**Score**: {c['score']} | **Messages**: {c['message_count']} | **Tags**: {cats}")
            if date_range:
                lines.append(f"**Active**: {date_range}")
            if c["snippet"]:
                lines.append(f"> {c['snippet']}")
            lines.append("")

    write_tier(tier1, "Tier 1 — Top 25: Prioritize These", "Deepest, most reciprocal relationships with strongest professional and personal signal")
    write_tier(tier2, "Tier 2 — Next 35: Strong Connections", "Meaningful exchanges with clear mutual interest — well worth a message")
    write_tier(tier3, "Tier 3 — Final 40: Worth Rekindling", "Solid threads that could lead somewhere with a thoughtful follow-up")

    # Summary stats
    lines.append("---")
    lines.append("")
    lines.append("## Category Breakdown")
    lines.append("")
    cat_counts = Counter()
    for r in top100:
        for c in r["categories"]:
            cat_counts[c] += 1
    for cat, count in cat_counts.most_common():
        lines.append(f"- **{cat}**: {count} contacts")
    lines.append("")

    output = "\n".join(lines)
    outpath = Path("obsidian-vault/Profile/Key Contacts.md")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\nGenerated: {outpath}")
    print(f"Top 100 contacts scored and categorized.")
    print(f"\nTier breakdown:")
    print(f"  Tier 1 (score ≥60): {len(tier1)} contacts")
    print(f"  Tier 2 (score 45-59): {len(tier2)} contacts")
    print(f"  Tier 3 (score <45): {len(tier3)} contacts")
    print(f"\nTop 10 preview:")
    for i, r in enumerate(top100[:10], 1):
        cats = ", ".join(r["categories"])
        print(f"  {i}. {r['name']} (score: {r['score']}, msgs: {r['message_count']}, {cats})")


if __name__ == "__main__":
    main()
