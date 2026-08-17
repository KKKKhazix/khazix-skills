#!/usr/bin/env bash
set -euo pipefail

# Regression: `--target agents --migrate-legacy` removes ~/.claude/skills/aihot,
# so it must leave the documented Claude compatibility symlink behind. Before the
# fix the link was only set for `--target claude`, and the documented migration
# command left Claude with no aihot Skill at all.
#
# The installer is driven end to end against a stub `curl` that serves a package
# built from the repository copy, so no network access is needed.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INSTALLER="$REPO_ROOT/aihot/install.sh"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

SITE_ROOT="$TMP_ROOT/site/aihot-skill"
FAKE_HOME="$TMP_ROOT/home"
BIN="$TMP_ROOT/bin"
mkdir -p "$SITE_ROOT" "$FAKE_HOME" "$BIN"

# Package the repository copy as the payload the installer expects.
while IFS= read -r relative_path; do
  [ -n "$relative_path" ] || continue
  mkdir -p "$SITE_ROOT/$(dirname "$relative_path")"
  cp "$REPO_ROOT/aihot/$relative_path" "$SITE_ROOT/$relative_path"
done < <(awk '{ print $2 }' "$REPO_ROOT/aihot/manifest.sha256")
cp "$REPO_ROOT/aihot/manifest.sha256" "$SITE_ROOT/manifest.sha256"

# Stub curl: serve $SITE/aihot-skill/<path> from the local package tree.
cat > "$BIN/curl" <<'BASH'
#!/usr/bin/env bash
set -euo pipefail
url=
output=
while [ "$#" -gt 0 ]; do
  case "$1" in
    -o) output="$2"; shift 2 ;;
    --max-time) shift 2 ;;
    -*) shift ;;
    *) url="$1"; shift ;;
  esac
done
relative="${url#*/aihot-skill/}"
source_path="$FAKE_SITE_ROOT/$relative"
[ -f "$source_path" ] || exit 22
if [ -n "$output" ]; then
  mkdir -p "$(dirname "$output")"
  cp "$source_path" "$output"
else
  cat "$source_path"
fi
BASH
chmod +x "$BIN/curl"

# A legacy Claude copy is what the documented migration replaces.
mkdir -p "$FAKE_HOME/.claude/skills/aihot"
cp "$REPO_ROOT/aihot/SKILL.md" "$FAKE_HOME/.claude/skills/aihot/SKILL.md"

HOME="$FAKE_HOME" \
  FAKE_SITE_ROOT="$SITE_ROOT" \
  PATH="$BIN:$PATH" \
  bash "$INSTALLER" --target agents --migrate-legacy --no-actor \
  > "$TMP_ROOT/install.out" 2> "$TMP_ROOT/install.err" || {
    echo "FAIL: documented migration command exited non-zero" >&2
    cat "$TMP_ROOT/install.err" >&2
    exit 1
  }

# The shared installation exists.
[ -f "$FAKE_HOME/.agents/skills/aihot/SKILL.md" ] || {
  echo "FAIL: shared installation missing" >&2
  exit 1
}

# Claude keeps a working entry, and it is the promised symlink to the shared copy.
[ -L "$FAKE_HOME/.claude/skills/aihot" ] || {
  echo "FAIL: Claude compatibility symlink was not created by the migration" >&2
  exit 1
}
[ "$FAKE_HOME/.claude/skills/aihot" -ef "$FAKE_HOME/.agents/skills/aihot" ] || {
  echo "FAIL: Claude compatibility path does not resolve to the shared installation" >&2
  exit 1
}
[ -f "$FAKE_HOME/.claude/skills/aihot/SKILL.md" ] || {
  echo "FAIL: Claude can no longer read the Skill through its compatibility path" >&2
  exit 1
}
rg -F 'Claude Code compatibility points to the shared installation' "$TMP_ROOT/install.out" >/dev/null || {
  echo "FAIL: migration did not report the Claude compatibility path" >&2
  exit 1
}

# Without a legacy Claude copy the installer must not invent a Claude entry.
SECOND_HOME="$TMP_ROOT/home2"
mkdir -p "$SECOND_HOME"
HOME="$SECOND_HOME" \
  FAKE_SITE_ROOT="$SITE_ROOT" \
  PATH="$BIN:$PATH" \
  bash "$INSTALLER" --target agents --no-actor \
  > "$TMP_ROOT/second.out" 2> "$TMP_ROOT/second.err" || {
    echo "FAIL: plain shared install exited non-zero" >&2
    cat "$TMP_ROOT/second.err" >&2
    exit 1
  }
[ -f "$SECOND_HOME/.agents/skills/aihot/SKILL.md" ] || {
  echo "FAIL: plain shared install did not install" >&2
  exit 1
}
[ ! -e "$SECOND_HOME/.claude/skills/aihot" ] && [ ! -L "$SECOND_HOME/.claude/skills/aihot" ] || {
  echo "FAIL: shared install created an unrequested Claude entry" >&2
  exit 1
}

echo "aihot migrate-legacy Claude compatibility tests passed"
