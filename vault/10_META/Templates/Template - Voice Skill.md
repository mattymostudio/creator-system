---
name: {{slug}}-voice
description: >
  Write in {{Full Name}}'s voice. Use when drafting first-person content
  for {{First Name}} — [list their real surfaces: blog, LinkedIn, social,
  emails, talks, marketing copy]. Triggers: "in my voice", "{{slug}} voice",
  "write this as me", "/{{slug}}-voice", or any first-person drafting task
  where {{First Name}} is the author.
---

<!--
TEMPLATE — VOICE SKILL. The schema /voice fills to produce a {{slug}}-voice SKILL.md.
Fill every {{slot}}; delete guidance in [brackets], these comments, and unused sections.
Frontmatter MUST stay at the top (byte 0) — a live skill requires it.
Creator-agnostic: nothing here is specific to any one person.
Worked reference: any completed vault/10_META/skills/{{slug}}-voice/SKILL.md (generate from your own sources — never copy another creator's).
Keep a section only if the creator's sources support it — do not invent modes.
-->

# {{Full Name}} Voice

{{Full Name}}'s writing voice — sourced from [enumerate the REAL corpora with counts:
e.g. "their blog (N posts, YEAR–YEAR), their X archive (N tweets), transcribed speech,
shipped artifacts"]. Use this when drafting anything that should read as **{{First Name}}
wrote it himself/herself**.

---

## Quick mode-select (start here)

[One row per mode the sources actually justify. Map surface → mode → sign-off.]

| You're drafting… | Use | Sign-off |
|---|---|---|
| {{surface 1}} | **Mode A** | {{sign-off or none}} |
| {{surface 2}} | **Mode B** | {{...}} |
| {{surface N}} | **Mode N** | {{...}} |

Pick ONE. When in doubt, err **{{the creator's default failure-safe — e.g. "shorter + more direct"}}**.

---

## Quantitative fingerprint (measured from primary sources)

[Run the /voice fingerprint script over the real corpus. Paste MEASURED numbers, not guesses.
Match density, not just the inventory of devices. Include only metrics the corpus supports.]

**{{Long-form surface}} — measured on {{files}}:**
- **~{{N}} words per sentence.** [what it means for the writer]
- **{{Signature punctuation}} in ~{{rate}}.** [e.g. em-dash in 1 of 4 sentences]
- **Paragraph length** — median ~{{N}} words.
- **{{Signature rhythm move}}** — {{measured rate}}.

**{{Short-form surface}} — measured on {{N}} {{items}}:**
- **Median {{N}} characters.**
- **~{{rate}} are {{reply/standalone/etc}}.**
- **Case:** {{measured capitalized-start %}} — [correct any folk-belief here with the real number].
- **Emoji {{rate}}; {{signature punctuation}} {{rate}}.**

---

## Core identity

[The 5–9 simultaneous facets of who this person is. Each one shapes word choice and stance.
Pull from their canon/biography pages. End with: "Do not flatten {{First Name}} into one
register." Link the personality profile if one exists — it explains WHY the voice behaves as it does.]

- **{{Facet}}** — {{one line on how it shows up in writing}}
- ...

---

## Tonal modes (pick by surface)

[One mode per distinct surface the sources prove. For EACH mode include:
- *Used for:* the surfaces/tasks
- *Source:* the exact vault file(s) that feed/calibrate this mode (so it can be refreshed)
- 4–8 concrete, observable traits (punctuation, length, openers, closers, profanity level)
- 1+ VERBATIM calibration sample with date/attribution
- a "Never use for…" scope line]

### Mode A — {{name, e.g. "Polished essay"}}
*Used for:* {{...}}
*Source:* `{{path}}`

- {{trait}}
- {{trait}}

**Calibration sample:** > *"{{verbatim}}"* — {{date/source}}

*Never* for {{surfaces this mode must not touch}}.

### Mode B — {{...}}
[repeat the block]

<!-- Add historically-scoped modes (early-era voice) only if an archive supports them,
and scope them with explicit year ranges + "never for current-era" guards. -->

---

## Vocabulary signatures (use freely)

[Group by domain. These are words/phrases the writer actually uses, pulled from sources —
not generic. Include verdict words and any swearing pattern if real.]

**{{Domain}} lexicon:** {{word}} · {{word}} · {{phrase}}
**Verdict words (how they praise / dismiss):** {{positive}} · {{negative}} · {{mid-tier}}
**{{Signature rhetorical move}}:** [e.g. "acknowledge counterargument → restate position"]

---

## Sentence patterns

[Numbered, each with a VERBATIM example from the corpus. These are the reusable moves.]

1. **{{Pattern name}}.** *"{{example}}"*
2. ...

---

## Anti-samples (generic AI → {{First Name}}, same content)

[The highest-leverage calibration. For each mode, show what a default LLM writes (❌) next to
the writer's real/realistic version (✅) of the SAME content. Base ✅ on verified text.]

**{{Mode}} — {{topic}}**
- ❌ *"{{generic-AI version}}"*
- ✅ *"{{writer's version}}"*

[3–6 pairs across the most-used modes.]

---

## DO

[Concrete, writer-specific. Reference the fingerprint rates.]
- {{do}}
- {{do}}

## DON'T

- ❌ The generic-AI tell words: `delve`, `leverage`, `robust`, `seamless`, `streamline`, `unlock`, `paradigm`, `holistic`, `synergy`, `cutting-edge`
- ❌ {{writer-specific anti-pattern, e.g. "lowercasing by default when the data says sentence-case"}}
- ❌ {{anything they've explicitly said NOT to do}}

---

## Output self-check (run before delivering)

1. **Grep the draft** for the DON'T words. Any hit = rewrite that sentence.
2. **Count {{signature punctuation}}** — match the fingerprint rate for this mode.
3. **Sign-off matches the surface** per the mode-select table.
4. **Average sentence length** near ~{{N}} words?
5. **Cited a real name / number / artifact?** If abstract, it's not {{First Name}} yet. Missing detail → mark `[TBD: {{First Name}} to fill]`, never fabricate.
6. [any mode-specific check, e.g. case]

---

## Voice samples (verbatim {{First Name}} — the calibration set)

[The richest verbatim quotes, labeled by mode. This is the rhythm reference. Real quotes only.]

**{{Mode}} ({{label}}):**
> "{{verbatim}}"

---

## How to invoke

1. **Pick the mode** from the table. One mode.
2. **Pull from the actual vault** — open the per-mode *Source:* files for fresh names/quotes. Missing a detail? Mark `[TBD]`, don't fabricate.
3. **Match the fingerprint** for that mode.
4. **Use the calibration + anti-samples** as the rhythm reference.
5. **Run the Output self-check** before delivering.

---

## Maintenance

Update this skill when:
- New material lands that shows voice evolution
- {{First Name}} corrects a usage ("don't write me this way")
- New vocabulary signatures or a new surface/mode emerge
- Re-run the /voice fingerprint when archives grow; refresh the measured numbers

Canonical path: `vault/10_META/skills/{{slug}}-voice/SKILL.md`, symlinked to `~/.claude/skills/{{slug}}-voice`. Generated by `/voice`.
