---
description: Write a terse session recap — what changed, what's next, loose ends — and append a dated entry to 00_HOME/Log.md
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
origin: matty-mo-studio-creator-system/1.0
---

# Recap

You are closing out a vault work session. Produce a compact recap so a future agent (or the user returning hours later) can pick up cleanly.

**Working directory:** vault root.

---

## Phase 1: Gather what happened this session

Look at what you actually did in this conversation. Don't invent activity that didn't happen.

Good signals:
- Files you created, edited, or moved (check via `git -C . status` and `git -C . diff --stat` if the vault is a git repo)
- Decisions you reached with the user
- Plans or proposals drafted
- Explicit loose ends you noted

If the session was trivial (one small edit, a question answered), say so and stop — don't pad.

## Phase 2: Write the recap

Write a recap block in this exact format:

```markdown
## Recap — <YYYY-MM-DD HH:MM>

**Session scope:** <one line>

**What changed**
- <bullet; link files using [name](relative/path)>

**What's next**
- <the exact next action>

**Loose ends**
- <partial work, skipped cases, verify-later items>
- <omit this section entirely if empty>
```

Keep it under 15 lines total. If you wrote more than 15, compress.

## Phase 3: Append to the log

1. Read `00_HOME/Log.md`.
2. Append the recap block to the **top** of the log body (after the page's frontmatter/heading), so the most recent recap is first.
3. Save the file.

## Phase 4: Report back

Print the recap block to the chat so the user can see it without opening the Log.

---

## Rules

- **Don't invent work.** If you can't back a bullet with a real file/decision from this session, drop it.
- **Keep it present-tense and concrete.** "Renamed X to Y" not "Did some renaming."
- **Link files, don't paraphrase paths.**
- **No emojis, no filler, no recap of the recap.**
