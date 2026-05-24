---
description: Generate (or refresh) a personal writing-voice skill from a creator's own sources. Mines first-person writing in 02_SOURCES, detects surfaces, measures a quantitative fingerprint, extracts vocabulary + sentence patterns + verbatim calibration samples, and emits a {slug}-voice/SKILL.md from the voice template, symlinked for global use. Use when a creator wants a "write in my voice" skill, or to refresh one after new sources land.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit, AskUserQuestion
origin: tmfa-creator-system/1.0
---

# Voice

You are building a **personal writing-voice skill** for this vault's creator, entirely from their own primary sources. The output is a `{{slug}}-voice/SKILL.md` that any future Claude session can invoke to draft text that sounds like the creator wrote it.

This command is creator-agnostic. It works for *any* TMFA vault owner by reading *their* `02_SOURCES/`. If a completed voice skill already exists under `vault/10_META/skills/`, read it once to see what "done" looks like — but never copy another creator's content; each voice is generated from its owner's own sources.

**Working directory:** the vault root (the directory containing `00_HOME` through `10_META`).

---

## Non-negotiables

1. **Ground everything in primary sources.** Every mode, vocabulary word, and calibration sample must trace to a real file in `02_SOURCES/`. If you can't cite it, don't claim it.
2. **Measure, don't guess.** The quantitative fingerprint comes from running the script in Phase 3 over the real corpus — never invent the numbers. Correct folk-beliefs with data (e.g. "I write all-lowercase" is often false when measured).
3. **Never fabricate a quote.** Calibration samples are verbatim. If you paraphrase, label it. Missing detail in a generated draft → `[TBD: creator to fill]`.
4. **Detect modes from evidence, not a fixed menu.** A creator with only a blog and tweets gets two modes, not seven. Only add a historically-scoped early-era mode if an archive actually supports it.
5. **Get approval at the surface→mode step (Phase 2) before generating.** Use AskUserQuestion. The creator knows their own surfaces.
6. **The skill is the deliverable + a symlink + a log line.** Write to `10_META/skills/{{slug}}-voice/SKILL.md`, symlink to `~/.claude/skills/{{slug}}-voice`, append to `00_HOME/Log.md`.
7. **Fill the template, don't reinvent it.** Use `10_META/Templates/Template - Voice Skill.md` as the structure. Keep a section only if the sources support it.

---

## What NOT to do

- Do not include any other person's voice traits.
- Do not create a mode for a surface with fewer than ~5 real samples — note it as "thin, revisit when more lands" instead.
- Do not write the DON'T list as generic boilerplate only — include creator-specific anti-patterns you actually observed.
- Do not skip the fingerprint because the corpus is small. A small measured fingerprint beats a guessed one.

---

## Phase 1: Inventory the voice corpus (read-only)

Find every piece of **first-person writing by the creator** in `02_SOURCES/`. Use Glob + Grep. Likely locations and what they map to:

| Source | Typical surface / mode |
|---|---|
| `02_SOURCES/Practice/Articles/` (authored, not press) | long-form essay |
| Blog / monthly-update archives | essay + terse life-log |
| LinkedIn export / profile | professional post |
| `02_SOURCES/Personal/` social exports (X/Twitter, Facebook, Instagram `.tsv`/`.js`) | short-form social (current + historical) |
| `02_SOURCES/Personal/Journals/` (LiveJournal, diaries) | confessional / early-era |
| `02_SOURCES/Practice/Transcripts/` + speech quotes embedded in `04_CANON` decisions | transcribed speech |
| Devotional / faith / family writing | reverent |
| Repo READMEs the creator wrote | technical build post |

Separate **authored** (creator's own words) from **press/external** (someone writing *about* them) and **condensed summaries** (third-person abstracts in the vault) — only authored verbatim text calibrates voice. Note which article files are full primary text vs. summaries.

Produce a short inventory: each source path, rough item count, and the surface it represents.

If no first-person authored sources exist → **NEEDS_CONTEXT**: tell the creator what to add to `02_SOURCES/` (a few blog posts, a social export, or a transcript) and stop.

---

## Phase 2: Detect surfaces → propose modes (get approval)

From the inventory, propose the set of modes. Default mode vocabulary (use only those the sources support; rename to fit the creator):

- **Essay** (polished long-form) · **Professional/social post** (LinkedIn-style) · **Casual/transcribed speech** · **Reverent** (faith/family/grief) · **Technical build post** · **Short-form social** (current) · **Historical early-era** (scoped by year, from an archive) · **Terse life-log**

Read the creator's identity/bio and personality pages (`04_CANON/Shared/People/`, any `Personality Profile`) to draft the **Core identity** facets and *why* the voice behaves as it does.

Present via **AskUserQuestion**: the proposed mode list (which surfaces → which modes), and confirm the creator's name, slug, primary surfaces, and any "never write me like X" rules. Adjust to their answer before continuing.

---

## Phase 3: Measure the quantitative fingerprint

Adapt and run this script over the creator's real files (long-form essays + any social `.tsv`). It prints per-surface numbers — paste the measured values into the skill.

```python
#!/usr/bin/env python3
import csv, re, statistics
csv.field_size_limit(10**7)

def clean_prose(text):
    text = re.sub(r'^---.*?---\n', '', text, count=1, flags=re.DOTALL)
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s: out.append(""); continue
        if s.startswith('#') or s.startswith('---'): continue
        if s.startswith('>'): s = s.lstrip('> ').strip()
        if re.match(r'^\*.*\*$', s): continue   # italic bylines
        out.append(s)
    return "\n".join(out)

def essay_stats(label, *paths):
    blob = ""
    for p in paths:
        blob += "\n\n" + clean_prose(open(p, encoding="utf-8").read())
    paras = [p.strip() for p in re.split(r'\n\s*\n', blob) if p.strip()]
    sents = [s for s in re.split(r'(?<=[.!?])\s+', blob) if any(c.isalpha() for c in s)]
    words = re.findall(r"\b[\w'-]+\b", blob)
    em = blob.count("—")
    single = sum(1 for p in paras if len(re.split(r'(?<=[.!?])\s+', p)) == 1)
    pw = [len(re.findall(r"\b[\w'-]+\b", p)) for p in paras]
    print(f"\n=== ESSAY: {label} ===")
    print(f"words {len(words)} | sentences {len(sents)} | paragraphs {len(paras)}")
    print(f"avg words/sentence {len(words)/max(len(sents),1):.1f}")
    print(f"em-dash {em} | /1000w {em/max(len(words),1)*1000:.1f} | %sentences {sum('—' in s for s in sents)/max(len(sents),1)*100:.0f}%")
    print(f"median words/paragraph {statistics.median(pw):.0f} | single-sentence paras {single}/{len(paras)} ({single/max(len(paras),1)*100:.0f}%)")

def tsv_stats(label, path, textcol, replycol=None):
    rows = list(csv.DictReader(open(path, encoding="utf-8", errors="replace"), delimiter="\t"))
    texts = [(r.get(textcol) or "").strip() for r in rows]; texts = [t for t in texts if t]
    L = [len(t) for t in texts]
    print(f"\n=== SHORT-FORM: {label} ===")
    print(f"entries {len(texts)} | avg chars {statistics.mean(L):.0f} | median {statistics.median(L):.0f}")
    print(f"start @ {sum(t.startswith('@') for t in texts)/len(texts)*100:.0f}% | lowercase-start {sum(t[:1].islower() for t in texts)/len(texts)*100:.0f}%")
    print(f"emoji {sum(bool(re.search(r'[\U0001F000-\U0001FAFF]', t)) for t in texts)/len(texts)*100:.0f}% | em-dash {sum('—' in t for t in texts)/len(texts)*100:.1f}%")
    if replycol: print(f"true replies {sum((r.get(replycol) or '').strip() not in ('','0','None','nan') for r in rows)/len(rows)*100:.0f}%")

# edit these to the creator's real files, then run:
# essay_stats("Essays", "02_SOURCES/.../essay1.md", "02_SOURCES/.../essay2.md")
# tsv_stats("X", "02_SOURCES/Personal/X Archive/_parsed_tweets.tsv", "full_text", "in_reply_to")
```

Detect the `.tsv` text/reply column names from the header first (`head -1`). Record the per-surface numbers; these become the fingerprint section.

---

## Phase 4: Extract vocabulary, patterns, and verbatim samples

For each approved mode:

1. **Vocabulary signatures** — surface the creator's distinctive words/phrases. Grep the corpus for repeated turns of phrase; compare against ordinary usage to find what's *theirs*. Group by domain. Capture verdict words (how they praise vs. dismiss) and any profanity pattern if real.
2. **Sentence patterns** — pull 4–7 reusable structural moves, each with a verbatim example.
3. **Calibration samples** — pull the richest verbatim quotes per mode, with dates/attribution. These are the rhythm reference.
4. **Per-mode source pointers** — record the exact file(s) that calibrate each mode so it can be refreshed later.

---

## Phase 5: Build anti-samples and the DON'T list

1. **Anti-sample pairs** (highest-leverage): for the 3–6 most-used modes, write the generic-AI version (❌) of a piece of content next to the creator's real/realistic version (✅) of the *same* content. Base the ✅ side on verified text.
2. **DON'T list**: the generic-AI tell words (`delve, leverage, robust, seamless, streamline, unlock, paradigm, holistic, synergy, cutting-edge`) PLUS creator-specific anti-patterns you observed (and anything they said in Phase 2 to avoid).
3. **Output self-check**: a runnable checklist — grep for DON'T words, count signature punctuation against the fingerprint, verify sign-off matches surface.

---

## Phase 6: Emit the skill

1. Copy `10_META/Templates/Template - Voice Skill.md` into `10_META/skills/{{slug}}-voice/SKILL.md` and fill every `{{slot}}` with the material from Phases 2–5. Delete all template guidance comments and unused sections.
2. Symlink for global invocation:
   ```bash
   ln -sfn "$(pwd)/vault/10_META/skills/{{slug}}-voice" ~/.claude/skills/{{slug}}-voice
   ```
   (Run from the repo root, not the vault subdir. Verify with `ls -l ~/.claude/skills/{{slug}}-voice`.)
3. Sanity-check the generated skill against its own Output self-check.

---

## Phase 7: Log and verify

Append to `00_HOME/Log.md`:

```
## [YYYY-MM-DD] voice | {{slug}}-voice [created | refreshed]

- Sources mined: [paths / counts]
- Modes: [list]
- Fingerprint: [one-line headline numbers]
- Output: 10_META/skills/{{slug}}-voice/SKILL.md (symlinked to ~/.claude/skills/{{slug}}-voice)
```

Then report to the creator: the mode list, the headline fingerprint numbers, and how to invoke it (`/{{slug}}-voice` or "write this in my voice").

---

## Refresh mode

If `{{slug}}-voice/SKILL.md` already exists and the creator wants to update it (new sources landed): re-run Phases 1, 3, and 4 only over the *new* material, then **add** to the existing skill (new samples, refreshed fingerprint numbers) rather than overwriting. Preserve any hand-edits the creator made. Note in the log what changed.

---

## Escape hatches

- **No authored first-person sources** → NEEDS_CONTEXT. List what to add, stop.
- **Only one surface** (e.g. just tweets) → build a single-mode skill; don't pad with empty modes. Note it's expandable.
- **Sources are mostly press/summaries, not the creator's own words** → DONE_WITH_CONCERNS. Build what you can; flag that calibration is thin and which authored sources would strengthen it.
- **`.tsv`/export schema unrecognized** → inspect the header, adapt the script's column names; if still unparseable, sample by hand and note it.

---

## Completion

End with:

```
## Status: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]
[one-line explanation if not DONE]
```
