---
description: Find hidden bridges between two domains, topics, or concepts using the vault's link graph. Takes two subjects as input and searches for people, projects, themes, frameworks, or ideas that connect them in non-obvious ways. Use when you want to cross-pollinate between areas of your life and work.
allowed-tools: Read, Glob, Grep
origin: matty-mo-studio-creator-system/1.0
---

# Connect

You are searching this Personal Intelligence System for **hidden bridges** between two subjects that appear unrelated on the surface.

Your job is to find the people, projects, themes, frameworks, places, or ideas that sit at the intersection — connecting both domains in ways the human may not have noticed.

**Working directory:** The vault root (the directory containing 00_HOME through 10_META).

**Input:** The user will provide two topics, domains, or concepts to connect. If only one is provided, ask for the second.

---

## Non-negotiables

1. **Every connection must be grounded in vault evidence.** Cite specific pages with `[[page name]]` links. No speculative bridges without evidence.
2. **Prioritize non-obvious connections.** If two things are already explicitly linked in the vault, that is not a discovery — it is a known relationship. Find what's underneath.
3. **Quality over quantity.** Three strong bridges with real evidence beat ten weak ones.
4. **Distinguish connection types.** A person who works in both domains is a different kind of bridge than a shared theme or a structural parallel.

---

## Process

### Phase 1: Map each domain

For each of the two subjects:
- Search `04_CANON/` for relevant pages
- Search `05_PROJECTS/` for related projects
- Search `09_IDEAS/` for related concepts
- Grep across the vault for mentions
- Note the key people, places, themes, frameworks, and works associated with each

### Phase 2: Find intersections

Look for:

- **Shared people** — individuals who appear in both domains
- **Shared themes** — conceptual patterns that recur in both (e.g., "attention," "spectacle," "scale")
- **Structural parallels** — similar dynamics, business models, strategies, or creative approaches
- **Shared places** — geographic connections
- **Shared frameworks** — methods or playbooks that apply to both
- **Temporal overlaps** — things that happened simultaneously in both domains
- **Causal chains** — where one domain's output became another domain's input
- **Analogies** — where understanding one domain illuminates the other

### Phase 3: Build the connection map

For each bridge found, write:
1. **Bridge name** — what connects them
2. **Type** — person / theme / structural parallel / framework / place / temporal / causal / analogy
3. **Evidence** — the specific vault pages that establish this connection
4. **Insight** — what becomes visible when you see this connection that wasn't visible before
5. **Actionability** — is there something to do with this? A project, an essay, a conversation, an artwork?

---

## Output format

```markdown
## Connections: [Domain A] <-> [Domain B]

### Bridge 1: [Name]
**Type:** [person/theme/parallel/framework/place/temporal/causal/analogy]
**Evidence:**
- [[Page 1]] — [how it connects to Domain A]
- [[Page 2]] — [how it connects to Domain B]
- [[Page 3]] — [how it bridges both]
**Insight:** [what this connection reveals]
**Actionable:** [yes/no — if yes, what could be done]

### Bridge 2: [Name]
...
```

End with a **Synthesis** section: what does the overall connection map suggest? Is there a meta-pattern across the bridges?

---

## What this is NOT

- Not free association (every bridge needs vault evidence)
- Not a Venn diagram of keywords (finding "art" in both domains is not a bridge)
- Not generic advice about interdisciplinary thinking
