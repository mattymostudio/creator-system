---
description: Run structural lint checks on the vault and write a report to 10_META/Vault Lint Report.md
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
origin: matty-mo-studio-creator-system/1.0
---

# Vault Lint

You are running a structural lint pass on this Personal Intelligence System. Your job is to scan every file, run 10 checks, and write a clean report.

**Working directory:** The vault root (the directory containing 00_HOME through 10_META).

---

## Phase 1: Collect data

Run these steps to build the datasets every check depends on.

### 1A: File inventory

Use Bash to get every `.md` file in the vault (exclude `.claude/`):

```
find . -name "*.md" -not -path "./.claude/*" | sort
```

Store this as your complete file list. Extract the **base filename** (without path or `.md` extension) for each — this is the wiki-link target space.

### 1B: Wiki link extraction

Use Bash to extract every wiki link target from every file:

```
grep -roP '\[\[\K[^\]|#]+' --include="*.md" . | grep -v '\.claude/'
```

This produces lines like `./path/file.md:Link Target`. Parse into a map of:
- **source file** -> list of link targets
- **link target** -> list of source files (reverse index)

Normalize link targets: trim whitespace. Obsidian is case-insensitive on macOS, so do case-insensitive matching against the filename inventory.

### 1C: Frontmatter extraction

For each `.md` file, read the YAML frontmatter (between the first pair of `---` lines). Extract: `type`, `status`, `last_updated`, `date`, `source_type`, `format`, `stage`, `domain`, `aliases`. Files without frontmatter should be noted.

### 1D: Previous report

Read `10_META/Vault Lint Report.md` if it exists. Parse the Summary Dashboard table to extract previous counts per check. If the file does not exist or the table cannot be parsed, set all previous counts to "-".

---

## Phase 2: Run checks

### CHECK 1 — Broken Wiki Links [CRITICAL]

Compare all unique wiki link targets against the file inventory (case-insensitive match on base filename).

**Exclude these known non-file targets** (folder-level navigation links):
`00_HOME`, `01_INBOX`, `02_SOURCES`, `03_SOURCE_NOTES`, `04_CANON`, `05_PROJECTS`, `06_OUTPUTS`, `07_IDENTITY`, `08_STRATEGY`, `09_IDEAS`, `10_META`, and any target containing `/` (path references like `10_META/AGENTS.md`).

A link is **broken** if the target does not match any `.md` filename in the vault.

**Report:** Total count. List the top 30 broken links sorted by frequency (how many files reference them), with the count and one example source file each. If more than 30, note "and N more".

### BONUS CHECK — Unclosed Frontmatter [CRITICAL]

Files that start with `---` but have no second `---` delimiter to close the YAML block. These are technically malformed. Check the first 30 lines of each file: if line 1 is `---` and no subsequent line is `---`, the frontmatter is unclosed.

**Report:** Total count. List each file path.

### CHECK 2 — Empty/Stub Files [CRITICAL]

For each `.md` file, count lines of **actual content** — exclude frontmatter (everything between the `---` delimiters at the top), blank lines, and lines that are only `---`. Note: some files have unclosed frontmatter (no second `---`). In that case, treat the first blank line after YAML-like content as the end of frontmatter.

Flag files with 0–4 lines of content.

**Report:** Total count. List each file with its path and content line count.

### CHECK 3 — Duplicate Files [CRITICAL]

Find base filenames (without path, without `.md`) that appear in more than one directory.

**Report:** Each duplicate set with all paths listed.

### CHECK 4 — Orphaned Pages [WARNING]

Using the reverse link index from 1B, find files with **zero inbound wiki links** from any other file.

**Exclude from orphan detection** (these are expected to have low/no inbound links):
- All files in `02_SOURCES/` (raw sources)
- All files in `10_META/` (system files)
- All files in `01_INBOX/` (temporary)
- All files in `00_HOME/` (hub/nav files — they are entry points, not link targets)

**Report for these folders only:** `04_CANON/`, `05_PROJECTS/`, `06_OUTPUTS/`, `09_IDEAS/`

Group orphans by folder. Total count.

### CHECK 5 — Frontmatter Validation [WARNING]

Infer expected page type from file location and check required fields:

| Location | Expected type | Required fields |
|----------|--------------|-----------------|
| `03_SOURCE_NOTES/**` | source_note | type, status, source_type, date |
| `04_CANON/Shared/People/**` | person | type, status, last_updated |
| `04_CANON/Business/Companies/**` | entity | type, status, last_updated |
| `04_CANON/Shared/Places/**` | place | type, status, last_updated |
| `04_CANON/Practice/Themes/**` | theme | type, status, last_updated |
| `04_CANON/Practice/Frameworks/**` | framework | type, status, last_updated |
| `04_CANON/Shared/Timeline/**` | timeline | type, status |
| `04_CANON/Business/Decisions/**` | decision | type, status, date |
| `04_CANON/Practice/Works/**` | artwork | type, status |
| `05_PROJECTS/**` | project | type, status, last_updated |
| `06_OUTPUTS/**` | output | type, status, format |
| `09_IDEAS/**` (not Scoreboard/Queue) | idea | type, status, date, domain |

Skip frontmatter checks for: `00_HOME/`, `01_INBOX/`, `02_SOURCES/`, `04_CANON/Personal/`, `10_META/` (these either lack templates or contain raw/operational material).

**Report:** Group by page type. For each type, show the count of files missing each required field. List specific files only for the worst offenders (top 5 per type).

### CHECK 6 — Status Field Validation [WARNING]

Valid status values from AGENTS.md:

**General:** `canonical`, `working`, `speculative`, `mythic`, `archival`, `draft`, `approved`, `archived`

**Project-specific (mapped to folder):**
- Files in `Active/` should have status: `active`
- Files in `Incubating/` should have status: `incubating`
- Files in `Dormant/` should have status: `dormant`
- Files in `Archived/` should have status: `archived`

**Additional accepted values:** `seed` (for ideas — common and intentional).

Flag any file whose `status:` value is NOT in the combined valid list. Also flag project files where status does not match their folder placement.

**Report:** Total count of non-standard statuses. List each violation with file path and the non-standard value.

### CHECK 7 — Naming Convention Check [WARNING]

Check filenames against expected patterns per location:

| Location | Expected pattern | Regex |
|----------|-----------------|-------|
| `03_SOURCE_NOTES/**` | `YYYY-MM-DD - Note - Title` or `YYYY - Note - Title` | `^\d{4}(-\d{2}(-\d{2})?)? - Note - .+` |
| `05_PROJECTS/**` | `Project - Name` | `^Project - .+` |
| `04_CANON/Decisions/**` | `Decision - Topic` | `^Decision - .+` |
| `04_CANON/Timeline/**` | `TL - Title` | `^TL - .+` |

For `06_OUTPUTS/`: check only that template files follow `Output - Template - Name - v1` pattern. Business Network files use company names directly — flag as a naming convention note but not individual violations.

**Report:** Violations by folder with file paths.

### CHECK 8 — Concepts Without Pages [INFO]

From the wiki link extraction (1B), find link targets that:
1. Appear in **3 or more different source files**
2. Do NOT match any existing `.md` filename
3. Are NOT folder-level references

These are candidates for new canon pages.

**Report:** Top 20 by frequency. Show the target name and how many files reference it.

### CHECK 9 — Stale Working Pages [INFO]

Find files where:
- `status: working` in frontmatter
- `last_updated:` is present and more than 90 days before today
- OR `last_updated:` is missing entirely

**Report:** List each file with its last_updated date (or "missing").

### CHECK 10 — Underlinked Canon Pages [INFO]

For each file in `04_CANON/` (all subfolders), count **outbound wiki links** (links FROM the page to other pages).

Flag pages with fewer than 2 outbound links.

Exclude: `04_CANON/Shared/FAQ/`, `04_CANON/Practice/Glossary/`, `04_CANON/Personal/` (list-style or identity-reference pages with different link patterns).

**Report:** List underlinked pages with their outbound link count.

---

## Phase 3: Write the report

Write the full report to `10_META/Vault Lint Report.md` using this format:

```markdown
---
type: meta
status: generated
generated: YYYY-MM-DD HH:MM
---

# Vault Lint Report

Generated: **YYYY-MM-DD HH:MM**
Vault: Personal Intelligence System | Files scanned: N | Wiki links: N unique targets

---

## Summary Dashboard

| # | Check | Severity | Count | Prev | Delta |
|---|-------|----------|-------|------|-------|
| 1 | Broken wiki links | CRITICAL | N | P | +/-D |
| 2 | Empty/stub files | CRITICAL | N | P | +/-D |
| 3 | Duplicate files | CRITICAL | N | P | +/-D |
| 4 | Orphaned pages | WARNING | N | P | +/-D |
| 5 | Frontmatter gaps | WARNING | N | P | +/-D |
| 6 | Non-standard status | WARNING | N | P | +/-D |
| 7 | Naming violations | WARNING | N | P | +/-D |
| 8 | Concepts without pages | INFO | N | P | +/-D |
| 9 | Stale working pages | INFO | N | P | +/-D |
| 10 | Underlinked canon pages | INFO | N | P | +/-D |
| -- | Unclosed frontmatter | CRITICAL | N | P | +/-D |

---

## Critical

### 1. Broken Wiki Links
[findings]

### 2. Empty/Stub Files
[findings]

### 3. Duplicate Files
[findings]

---

## Warnings

### 4. Orphaned Pages
[findings grouped by folder]

### 5. Frontmatter Gaps
[findings grouped by page type]

### 6. Non-Standard Status Values
[findings]

### 7. Naming Convention Violations
[findings]

---

## Info

### 8. Top Concepts Without Pages
[top 20 table]

### 9. Stale Working Pages
[list]

### 10. Underlinked Canon Pages
[list]

---

## Top 5 Recommendations

[Based on the findings, list the 5 highest-impact actions the vault owner should take. Be specific — name files, counts, and what to do.]
```

Use the actual current date/time. If previous counts exist from Phase 1D, compute deltas (positive = more issues, negative = improvement). If no previous data, show "-" for Prev and Delta.

---

## Phase 4: Summary

After writing the report, output a brief summary to the conversation:
- Total issues found per severity level
- The single most important finding
- Confirm the report location

Do NOT modify any vault files other than `10_META/Vault Lint Report.md`. This is a read-only audit with a single write output.
