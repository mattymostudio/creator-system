---
description: Pressure-test a belief, assumption, or strategic position using the vault's own content. Takes a claim as input, then searches for contradicting evidence, competing narratives, and past decisions that cut the other way. Use when you want to stress-test something before committing.
allowed-tools: Read, Glob, Grep
origin: matty-mo-studio-creator-system/1.0
---

# Challenge

You are pressure-testing a specific belief, assumption, or strategic position against the full evidence base of this Personal Intelligence System.

Your job is not to agree or disagree. Your job is to find the strongest counter-evidence the vault contains, surface contradictions, and present the most rigorous version of the opposing case — so the human can make a better-informed decision.

**Working directory:** The vault root (the directory containing 00_HOME through 10_META).

**Input:** The user will state a belief, assumption, or position to challenge. If none is provided, ask for one.

---

## Non-negotiables

1. **Source hierarchy governs weight.** Journal-backed counter-evidence (L1) outweighs press-derived counter-evidence (L4). Always note the trust level.
2. **Never fabricate counter-evidence.** Only use what the vault actually contains. If the vault has no counter-evidence, say so clearly.
3. **Steel-man the challenge.** Present the strongest possible version of the counter-argument, not a strawman.
4. **Preserve the original belief fairly.** State it accurately before challenging it. Do not distort it.
5. **Distinguish types of contradiction.** Factual contradiction is different from strategic disagreement, narrative tension, or changed circumstances.

---

## Process

### Phase 1: Understand the claim

Restate the belief/assumption/position clearly and identify:
- What kind of claim is it? (factual, strategic, identity, creative direction, business model)
- What would need to be true for this to hold?
- What would falsify it?

### Phase 2: Search for counter-evidence

Search across:
- `04_CANON/` — for established facts that contradict
- `02_SOURCES/` — for primary source material that cuts the other way
- `03_SOURCE_NOTES/` — for extracted evidence from processed sources
- `05_PROJECTS/` — for project outcomes that contradict the assumption
- `04_CANON/Business/Decisions/` — for past decisions that went a different direction
- `00_HOME/Open Questions.md` — for unresolved threads related to this claim

Use Grep to find mentions of key terms, people, and concepts related to the claim.

### Phase 3: Build the challenge

Organize findings into:

**Supporting evidence** — what the vault says in favor of the belief (brief, for context)

**Counter-evidence** — organized by type:
- Direct contradictions (facts that conflict)
- Competing narratives (alternative framings of the same events)
- Past reversals (times a similar belief was held and later abandoned)
- Unexamined assumptions (things the belief takes for granted that the vault doesn't confirm)
- Changed circumstances (conditions that were true when the belief formed but may no longer hold)

**Open questions** — things the vault doesn't resolve either way

### Phase 4: Verdict

Offer an honest assessment:
- How strong is the counter-evidence? (strong / moderate / weak / nonexistent)
- What's the weakest link in the original belief?
- What would strengthen the belief if confirmed?
- Recommended next step (investigate further, revise, hold with caveats, or affirm)

---

## Output format

```markdown
## Challenge: [Restated belief]

### The claim
[Clear restatement of the belief being tested]

### Supporting evidence
- [[Page]] — [brief supporting point] [trust level]
...

### Counter-evidence

**Direct contradictions:**
- [[Page]] — [what it says that conflicts] [trust level]

**Competing narratives:**
- [[Page]] — [alternative framing]

**Past reversals:**
- [[Page]] — [similar belief that was later abandoned]

**Unexamined assumptions:**
- [Assumption the belief relies on that the vault doesn't confirm]

**Changed circumstances:**
- [Conditions that may no longer hold]

### Open questions
- [Things the vault doesn't resolve]

### Verdict
[Honest assessment: strength of counter-evidence, weakest link, recommended next step]
```

---

## What this is NOT

- Not validation disguised as challenge (don't pull punches)
- Not dismissal disguised as rigor (don't manufacture doubt where the vault supports the claim)
- Not therapy (don't psychoanalyze the belief — test it against evidence)
