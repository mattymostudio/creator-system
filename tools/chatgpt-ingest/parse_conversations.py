#!/usr/bin/env python3
"""Parse ChatGPT conversations.json and extract key content organized by domain."""

import json
import datetime
import re
import os

INPUT_FILE = "ChatGPT Download/conversations.json"
OUTPUT_DIR = "parsed_domains"

# Domain classification rules (checked in order, first match wins for primary)
#
# These keyword lists are GENERIC DEMO EXAMPLES. The whole point of this tool
# is that you replace them with keywords tuned to your own conversation titles
# — add keywords, rename domains, create new ones. It's just a dict.
#
# Privacy note: your tuned keyword lists are derived from your real archive
# and can reveal a lot about you in aggregate. Treat your edited copy of this
# file as private — don't commit it to a public repo.
DOMAIN_RULES = {
    "art_park": {
        "title_keywords": [
            "art park", "sculpture park", "sculpture garden",
            "sculpture trail", "mural festival", "art installation",
            "public art", "art vision", "art-driven", "art driven",
            "revitalization", "cultural campus",
            "gathering", "festival", "campground", "glamping", "campsite",
            "space activation", "skate park",
            "nonprofit setup", "501c3", "foundation overview",
            "master plan", "visitor center",
        ],
    },
    "real_estate": {
        "title_keywords": [
            "real estate", "property", "land deal", "subdivision",
            "seller financ", "mortgage", "loan agreement", "construction loan",
            "1031 exchange", "house sale", "building a house", "home build",
            "well drilling", "water rights", "easement",
            "deal memo", "deal structure", "land purchase",
            "investment property", "adu",
            "drywall", "square footage",
            "concrete", "plywood",
            "permit requirements", "contractor",
            "construction", "home design", "house design",
            "kitchen design", "shelving", "tile coverage",
        ],
    },
    "finance": {
        "title_keywords": [
            "investment", "market", "stock", "bitcoin", "btc", "crypto",
            "gold", "etf", "dividend", "portfolio",
            "recession", "inflation", "tariff",
            "net worth", "financial health", "financial position",
            "ira", "tax", "capital gains",
            "loan payment", "valuation",
            "run rate", "revenue", "budget breakdown",
            "market analysis", "market outlook", "macro trend",
            "interest rate", "bond yield",
            "options trading", "cap rate", "rebalance",
        ],
    },
    "memoir_creative": {
        "title_keywords": [
            "memoir", "artist bio", "artist statement",
            "artistic journey", "hero's journey",
            "authenticity", "art philosophy",
            "manuscript", "book", "writing",
            "podcast", "documentary", "script",
            "brand brief", "brand", "merch",
            "logo", "design", "storefront sign",
            "social media", "content creation", "marketing",
            "ted talk", "manifesto",
            "year in review", "interview", "transcript",
        ],
    },
    "life_personal": {
        "title_keywords": [
            "life vision", "future vision",
            "self discovery", "self-discovery", "personal philosophy",
            "core beliefs", "5 year plan", "goals",
            "life optimization", "life path",
            "dating", "relationship", "marriage", "parenting",
            "meditation", "retreat", "yoga", "fasting",
            "health", "fitness", "sleep", "nutrition",
            "travel", "itinerary", "packing", "jet lag",
            "visa", "residency",
            "homestead", "garden", "harvest", "recipe",
            "birthday", "holiday",
            "gratitude", "journaling",
        ],
    },
    "reference_legal": {
        "title_keywords": [
            "agreement", "contract", "lease", "consignment",
            "dissolution", "termination", "eviction",
            "trademark", "gdpr",
            "bylaws", "ordinance", "zoning",
            "rfp", "loi", "proposal",
            "at-will employment", "severance",
            "resignation",
        ],
    },
}

# Skip patterns - conversations that are just quick calculations or image
# generation. Like DOMAIN_RULES above, these are generic examples — tune them
# to the throwaway-title patterns in your own export.
SKIP_PATTERNS = [
    r"^new chat$",
    r"days (between|until)",
    r"(sq|square) (meters?|feet|footage) to",
    r"^(acres?|gallons?) (in|to|conversion)",
    r"cubic feet",
    r"^(sum|total|percentage|calculate|calculation)",
    r"^date calculation",
    r"unit conversion",
    r"^turn (me|photo)",
    r"^image (creation|transformation|aesthetic)",
    r"^(change|update) (color|image|time)",
    r"^(animate|remix) (a |)photo",
    r"^full body render",
    r"^(explain|read|extract) (image|text|pdf|script)",
    r"synonym for",
    r"quick question",
]


def classify_conversation(title):
    """Classify a conversation into domains based on title."""
    title_lower = title.lower() if title else ""

    # Check skip patterns
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, title_lower):
            return ["skip"]

    domains = []
    for domain, rules in DOMAIN_RULES.items():
        for kw in rules["title_keywords"]:
            if kw in title_lower:
                domains.append(domain)
                break

    return domains if domains else ["uncategorized"]


def extract_messages(conversation):
    """Extract the conversation thread in order."""
    mapping = conversation.get("mapping", {})

    # Build parent->children map
    children_map = {}
    for node_id, node in mapping.items():
        parent = node.get("parent")
        if parent:
            children_map.setdefault(parent, []).append(node_id)

    # Find root
    root = None
    for node_id, node in mapping.items():
        if node.get("parent") is None:
            root = node_id
            break

    if not root:
        return []

    # Walk the main thread (follow current_node path)
    current_node = conversation.get("current_node")
    if not current_node:
        return []

    # Build path from current_node back to root
    path = []
    node_id = current_node
    while node_id:
        path.append(node_id)
        node = mapping.get(node_id, {})
        node_id = node.get("parent")
    path.reverse()

    messages = []
    for node_id in path:
        node = mapping.get(node_id, {})
        msg = node.get("message")
        if not msg:
            continue

        author = msg.get("author", {}).get("role", "unknown")
        content = msg.get("content", {})
        parts = content.get("parts", [])

        text_parts = []
        for part in parts:
            if isinstance(part, str) and part.strip():
                text_parts.append(part.strip())
            elif isinstance(part, dict):
                # Could be image or other content
                if part.get("content_type") == "text":
                    text_parts.append(part.get("text", ""))

        text = "\n".join(text_parts)
        if not text:
            continue

        create_time = msg.get("create_time")

        messages.append({
            "role": author,
            "text": text,
            "timestamp": create_time,
        })

    return messages


def summarize_conversation(title, messages, date):
    """Create a condensed summary focusing on user's ideas, decisions, and key info."""
    # Extract just user messages for the summary
    user_msgs = [m["text"] for m in messages if m["role"] == "user"]
    assistant_msgs = [m["text"] for m in messages if m["role"] == "assistant"]

    # Combine user messages (truncate very long ones)
    user_content = []
    for msg in user_msgs:
        if len(msg) > 2000:
            user_content.append(msg[:2000] + "...")
        else:
            user_content.append(msg)

    # Get key assistant responses (first and last, truncated)
    assistant_summary = []
    if assistant_msgs:
        first = assistant_msgs[0]
        if len(first) > 1500:
            first = first[:1500] + "..."
        assistant_summary.append(first)
        if len(assistant_msgs) > 1:
            last = assistant_msgs[-1]
            if len(last) > 1500:
                last = last[:1500] + "..."
            assistant_summary.append(last)

    return {
        "title": title,
        "date": date,
        "user_messages": user_content,
        "key_responses": assistant_summary,
        "message_count": len(messages),
    }


def main():
    print("Loading conversations...")
    with open(INPUT_FILE) as f:
        data = json.load(f)

    print(f"Total conversations: {len(data)}")

    # Classify and extract
    domains = {}
    skipped = 0
    uncategorized = []

    for conv in data:
        title = conv.get("title", "Untitled")
        ct = conv.get("create_time")
        date = datetime.datetime.fromtimestamp(ct).strftime("%Y-%m-%d") if ct else "Unknown"

        categories = classify_conversation(title)

        if "skip" in categories:
            skipped += 1
            continue

        messages = extract_messages(conv)
        if len(messages) < 3:
            skipped += 1
            continue

        summary = summarize_conversation(title, messages, date)

        if "uncategorized" in categories:
            uncategorized.append(summary)
            continue

        for cat in categories:
            domains.setdefault(cat, []).append(summary)

    # Sort each domain by date
    for domain in domains:
        domains[domain].sort(key=lambda x: x["date"])

    # Save to JSON for further processing
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for domain, convos in domains.items():
        output_file = os.path.join(OUTPUT_DIR, f"{domain}.json")
        with open(output_file, "w") as f:
            json.dump(convos, f, indent=2, ensure_ascii=False)
        print(f"  {domain}: {len(convos)} conversations")

    # Save uncategorized
    with open(os.path.join(OUTPUT_DIR, "uncategorized.json"), "w") as f:
        json.dump(uncategorized, f, indent=2, ensure_ascii=False)
    print(f"  uncategorized: {len(uncategorized)} conversations")
    print(f"  skipped: {skipped} conversations")

    # Print stats
    print("\n=== DOMAIN STATS ===")
    for domain, convos in sorted(domains.items(), key=lambda x: -len(x[1])):
        total_msgs = sum(c["message_count"] for c in convos)
        print(f"  {domain}: {len(convos)} convos, {total_msgs} total messages")


if __name__ == "__main__":
    main()
