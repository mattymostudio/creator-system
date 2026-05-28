#!/usr/bin/env bash
# check-codex-readiness.sh — verify Creator System has the files Codex expects.

set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
FAIL=0

pass() { printf '✅ %s\n' "$1"; }
fail() { printf '❌ %s\n' "$1"; FAIL=1; }
warn() { printf '⚠️ %s\n' "$1"; }

exists() {
  local path="$1"
  local label="$2"
  if [ -f "$ROOT/$path" ]; then
    pass "$label"
  else
    fail "$label missing at $path"
  fi
}

max_bytes() {
  local path="$1"
  local limit="$2"
  if [ ! -f "$ROOT/$path" ]; then
    return
  fi
  local size
  size=$(wc -c < "$ROOT/$path" | tr -d ' ')
  if [ "$size" -le "$limit" ]; then
    pass "$path is ${size} bytes, under ${limit}"
  else
    fail "$path is ${size} bytes, over ${limit}"
  fi
}

echo "==> Codex readiness check"
echo "    Root: $ROOT"
echo

exists "AGENTS.md" "Root Codex instructions found"
exists "vault/AGENTS.md" "Vault-level Codex instructions found"
exists ".agents/skills/creator-system-vault/SKILL.md" "Creator System Codex skill found"
exists "docs/CODEX.md" "Codex setup doc found"
exists "CLAUDE.md" "Claude Code root instructions preserved"
exists "vault/CLAUDE.md" "Claude Code vault instructions preserved"

echo

echo "==> Instruction size checks"
# Codex defaults can cap combined project docs; keep the main instruction files concise.
max_bytes "AGENTS.md" 32768
max_bytes "vault/AGENTS.md" 32768
max_bytes ".agents/skills/creator-system-vault/SKILL.md" 32768

echo

echo "==> Skill frontmatter"
SKILL="$ROOT/.agents/skills/creator-system-vault/SKILL.md"
if [ -f "$SKILL" ]; then
  if head -1 "$SKILL" | grep -qx -- '---'; then
    pass "Skill frontmatter opens with ---"
  else
    fail "Skill frontmatter must start with ---"
  fi
  if grep -q '^name: creator-system-vault$' "$SKILL"; then
    pass "Skill name is creator-system-vault"
  else
    fail "Skill name missing or changed"
  fi
  if grep -q '^description: .*Creator System' "$SKILL"; then
    pass "Skill description is present and scoped"
  else
    fail "Skill description missing or too vague"
  fi
fi

echo

echo "==> Legacy workflow specs"
COMMAND_DIR="$ROOT/vault/.claude/commands"
if [ -d "$COMMAND_DIR" ]; then
  count=$(find "$COMMAND_DIR" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')
  if [ "$count" -ge 10 ]; then
    pass "Found $count legacy command specs"
  else
    fail "Expected at least 10 legacy command specs, found $count"
  fi
else
  fail "Legacy command directory missing at vault/.claude/commands"
fi

echo

echo "==> README integration"
if grep -q 'Codex' "$ROOT/README.md"; then
  pass "README mentions Codex"
else
  fail "README does not mention Codex"
fi

if grep -q '.agents/skills' "$ROOT/README.md"; then
  pass "README points to repo-scoped Codex skills"
else
  fail "README does not point to .agents/skills"
fi

echo

if [ "$FAIL" -eq 0 ]; then
  echo "✅ Codex readiness passed."
else
  echo "❌ Codex readiness failed."
  exit 1
fi
