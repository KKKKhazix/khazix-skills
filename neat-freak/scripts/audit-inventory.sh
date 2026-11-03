#!/usr/bin/env bash
# Read-only inventory for neat-freak. Prints metadata and paths only; never reads file contents.

set -euo pipefail

usage() {
  echo "usage: $0 <project-root>" >&2
  exit 64
}

[[ $# -eq 1 ]] || usage
[[ -d "$1" ]] || { echo "[ERR] project root is not a directory: $1" >&2; exit 66; }

PROJECT_ROOT="$(cd "$1" && pwd -P)"
SEEN_RULE_FILES=$'\n'

section() {
  printf '\n## %s\n' "$1"
}

file_size() {
  local file="$1"
  local lines bytes
  lines="$(wc -l < "$file" | tr -d ' ')"
  bytes="$(wc -c < "$file" | tr -d ' ')"
  printf '%s\tlines=%s\tbytes=%s\n' "$file" "$lines" "$bytes"
}

describe_rule_file() {
  local file="$1"
  case "$SEEN_RULE_FILES" in
    *$'\n'"$file"$'\n'*) return ;;
  esac
  SEEN_RULE_FILES+="$file"$'\n'
  if [[ -L "$file" ]]; then
    local target state
    target="$(readlink "$file")"
    if [[ -e "$file" ]]; then state="valid"; else state="broken"; fi
    printf '%s\tsymlink=%s\tstate=%s\n' "$file" "$target" "$state"
  elif [[ -f "$file" ]]; then
    file_size "$file"
  fi
}

printf '# neat-freak inventory v2\n'
printf 'project_root=%s\n' "$PROJECT_ROOT"
printf 'generated_at=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

section "platform-directories"
# Common agent home dirs; nonexistent ones are skipped silently.
for dir in "$HOME/.claude" "$HOME/.codex" "$HOME/.cursor" "$HOME/.gemini" \
  "$HOME/.qoder" "$HOME/.trae" "$HOME/.iflow" "$HOME/.codebuddy"; do
  [[ -d "$dir" ]] && printf '%s\n' "$dir"
done

section "other-agent-rule-artifacts"
# Platform-specific rule forms at the project root (existence only).
for rel in .github/copilot-instructions.md .github/instructions .cursorrules .windsurfrules .cursor/rules .qoder .trae .iflow; do
  [[ -e "$PROJECT_ROOT/$rel" ]] && printf '%s\n' "$PROJECT_ROOT/$rel"
done
true

section "git"
if git -C "$PROJECT_ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  GIT_ROOT="$(git -C "$PROJECT_ROOT" rev-parse --show-toplevel)"
  printf 'git_root=%s\n' "$GIT_ROOT"
  printf 'branch=%s\n' "$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || true)"
  printf 'head=%s\n' "$(git -C "$PROJECT_ROOT" rev-parse HEAD)"
  printf 'status_entries=%s\n' "$(git -C "$PROJECT_ROOT" status --porcelain=v1 | wc -l | tr -d ' ')"
  printf 'worktrees=%s\n' "$(git -C "$PROJECT_ROOT" worktree list --porcelain | awk '$1 == "worktree" {n++} END {print n+0}')"
else
  printf 'git_root=none\n'
fi

section "rule-chain-candidates"
cursor="$PROJECT_ROOT"
while :; do
  for rel in AGENTS.override.md AGENTS.md CLAUDE.md CLAUDE.local.md .claude/CLAUDE.md; do
    describe_rule_file "$cursor/$rel"
  done
  [[ "$cursor" == "/" ]] && break
  parent="$(dirname "$cursor")"
  [[ "$parent" == "$cursor" ]] && break
  cursor="$parent"
done
for file in \
  "$HOME/.codex/AGENTS.override.md" \
  "$HOME/.codex/AGENTS.md" \
  "$HOME/.claude/CLAUDE.md"; do
  describe_rule_file "$file"
done

section "project-markdown"
find "$PROJECT_ROOT" \
  \( -name .git -o -name node_modules -o -name .next -o -name dist -o -name build -o -name .venv -o -name venv -o -name __pycache__ -o -name target -o -name vendor -o -name .turbo -o -name .cache \) -prune \
  -o -type f \( -name '*.md' -o -name '*.mdx' \) -print \
  | LC_ALL=C sort

section "project-markdown-count"
find "$PROJECT_ROOT" \
  \( -name .git -o -name node_modules -o -name .next -o -name dist -o -name build -o -name .venv -o -name venv -o -name __pycache__ -o -name target -o -name vendor -o -name .turbo -o -name .cache \) -prune \
  -o -type f \( -name '*.md' -o -name '*.mdx' \) -print \
  | awk 'END {print NR+0}'

section "root-entries"
find "$PROJECT_ROOT" -mindepth 1 -maxdepth 1 -print | LC_ALL=C sort
