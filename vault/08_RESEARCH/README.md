---
type: hub
status: canonical
last_updated: 2026-04-14
---

# 08_RESEARCH

External topic knowledge — subjects you want to understand deeply that are **not** about you, your people, your projects, or your places. This is the world-knowledge tier.

Driven by the `/autoresearch` command.

## Structure

- `_Active/` — topics being actively researched (last run within 30 days)
- `_Stable/` — synthesis considered complete; no recent updates needed
- `_Archive/` — superseded or no longer relevant

Per topic, you get either:
- A single flat file in `_Active/` (small topic), or
- A subfolder `_Active/{slug}/` containing `{Topic}.md`, `control.yml`, `log.md`, and optionally `sections/*.md` when the topic grows past 3 sections.

Small topics start flat; graduate to folder structure as they deepen.

## Trust labeling

Research uses a **separate** trust scheme from personal canon (which runs on the L1-L6 biographical hierarchy). Research sources get per-citation tags: `primary | institutional | secondary | opinion | aggregator`. Research pages get a page-level `confidence` in frontmatter: `high | medium | low`, derived from the source mix.

## Raw sources

Fetched raw material from research runs lives in `02_SOURCES/Research/{topic-slug}/` — immutable, same rules as other source folders.

## Promotion to canon

Research never auto-promotes to `04_CANON/`. When a finding matters for a canonical entity, surface it as a suggestion and let `/enrich` or `/diarize` bring it in at the L4 (external) trust level. Translation happens at the promotion boundary.

## Getting started

1. Invoke `/autoresearch` with a topic name
2. Answer a few questions about depth and cadence
3. The loop writes a `control.yml` and a first-pass research page
4. Re-run `/autoresearch` on the topic slug to extend or refresh

See [[Idea Template]] and `10_META/AGENTS.md` for the full research workflow.
