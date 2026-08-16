#!/usr/bin/env bash
# AIHOT Agent Skill installer.
# Downloads and validates the complete runtime package before one directory swap.

set -euo pipefail

SITE="https://aihot.virxact.com"
TARGET=""
INSTALL_DIR=""
ACTOR_ID=""
ACTOR_MODE_SET=0
ACTOR_DISABLED=0
SKIP_ACTOR_GENERATION=0
MIGRATE_LEGACY=0
SHARED_TARGET=0
CLAUDE_COMPAT_LINK=""
CLAUDE_COMPAT_CREATED=0
TARGET_ACTIVATED=0
TMP_ROOT=""
TARGET_BACKUP=""
COMMITTED=0
LEGACY_PATHS=()
LEGACY_BACKUPS=()
LEGACY_COUNT=0
INSTALL_LOCK_DIR=""
INSTALL_LOCK_OWNER=""
INSTALL_LOCK_OWNED=0

usage() {
  cat <<'EOF'
Usage:
  install.sh --target <claude|codex|gemini|copilot|opencode|agents> [--migrate-legacy] [--actor <uuid-v4> | --no-actor]
  install.sh --dir <absolute-or-home-relative-path> [--actor <uuid-v4> | --no-actor]

Targets:
  codex|gemini|copilot|opencode|agents  ~/.agents/skills/aihot
  claude                                ~/.agents/skills/aihot + ~/.claude/skills/aihot symlink

Examples:
  bash install.sh --target codex
  # Optional: copy your own Actor UUID from https://aihot.virxact.com/agent
  bash install.sh --target codex --actor <uuid-v4-from-agent-page>
  bash install.sh --target codex --no-actor
  bash install.sh --target agents --migrate-legacy
  bash install.sh --dir "$HOME/.agents/skills/aihot"

The installer never uses sudo. It downloads the complete runtime package,
validates every SHA-256, then replaces one explicit target directory.

If an older AIHOT Skill ran this script without a target, do not guess or
retry with sudo. Open https://aihot.virxact.com/aihot-skill/README.md and give
its recommended update prompt to the Agent that owns the current Skill folder.
EOF
}

fail() {
  echo "[ERR] $*" >&2
  exit 1
}

normalize_actor_id() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

validate_actor_id() {
  [[ "$1" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$ ]]
}

generate_actor_id() {
  local generated=""
  if command -v uuidgen >/dev/null 2>&1; then
    if generated="$(uuidgen | tr '[:upper:]' '[:lower:]')"; then
      if validate_actor_id "$generated"; then printf '%s\n' "$generated"; return 0; fi
    fi
  fi
  if command -v python3 >/dev/null 2>&1; then
    if generated="$(python3 -c 'import uuid; print(uuid.uuid4())')"; then
      if validate_actor_id "$generated"; then printf '%s\n' "$generated"; return 0; fi
    fi
  fi
  if command -v node >/dev/null 2>&1; then
    if generated="$(node -e 'console.log(require("node:crypto").randomUUID())')"; then
      if validate_actor_id "$generated"; then printf '%s\n' "$generated"; return 0; fi
    fi
  fi
  return 1
}

expand_home_path() {
  case "$1" in
    "~") printf '%s\n' "$HOME" ;;
    \~/*) printf '%s/%s\n' "$HOME" "${1#\~/}" ;;
    *) printf '%s\n' "$1" ;;
  esac
}

validate_target_path() {
  case "$INSTALL_DIR" in
    ""|"/"|"$HOME")
      fail "refusing unsafe install path: ${INSTALL_DIR:-<empty>}"
      ;;
  esac
  [[ "$INSTALL_DIR" = /* ]] || fail "--dir must be absolute or start with ~/"
  [[ "$(basename "$INSTALL_DIR")" == "aihot" ]] || {
    fail "Skill directory must be named aihot: $INSTALL_DIR"
  }
  [[ ! -f "$INSTALL_DIR" ]] || fail "target is a file, not a Skill directory: $INSTALL_DIR"
  [[ ! -L "$INSTALL_DIR" ]] || fail "target is a symlink; choose its real directory explicitly: $INSTALL_DIR"
  if [[ -d "$INSTALL_DIR" && -f "$INSTALL_DIR/SKILL.md" ]]; then
    skill_frontmatter_has_line "$INSTALL_DIR/SKILL.md" "name: aihot" || {
      fail "target contains a different Skill and will not be overwritten: $INSTALL_DIR"
    }
  elif [[ -d "$INSTALL_DIR" ]] && [[ -n "$(ls -A "$INSTALL_DIR")" ]]; then
    fail "target is a non-empty directory without an AIHOT SKILL.md: $INSTALL_DIR"
  fi
}

skill_frontmatter_has_line() {
  local file="$1"
  local expected="$2"
  awk -v expected="$expected" '
    NR == 1 {
      if ($0 != "---") exit 1
      next
    }
    $0 == "---" {
      closed = 1
      exit found ? 0 : 1
    }
    $0 == expected {
      found = 1
    }
    END {
      if (!closed) exit 1
    }
  ' "$file"
}

cleanup_committed_backup() {
  local backup="$1"
  if [[ -n "$backup" && -e "$backup" ]] && ! rm -rf -- "$backup"; then
    echo "[WARN] The new Skill is active, but an old backup remains at: $backup" >&2
    echo "[WARN] After confirming the Skill works, remove that backup manually." >&2
  fi
}

release_install_lock() {
  if [[ "$INSTALL_LOCK_OWNED" -ne 1 || -z "$INSTALL_LOCK_DIR" ]]; then return; fi
  if [[ -f "$INSTALL_LOCK_DIR/owner" ]] \
    && [[ "$(cat "$INSTALL_LOCK_DIR/owner" 2>/dev/null || true)" == "$INSTALL_LOCK_OWNER" ]]; then
    rm -f -- "$INSTALL_LOCK_DIR/owner"
    rmdir -- "$INSTALL_LOCK_DIR" 2>/dev/null || true
  fi
  INSTALL_LOCK_OWNED=0
}

acquire_install_lock() {
  # Legacy migration can touch several clients' Skill directories, so every
  # install for this OS account must share one lock outside every target tree.
  INSTALL_LOCK_DIR="${HOME:?HOME is required}/.aihot-skill-install.lock"
  INSTALL_LOCK_OWNER="$$:${RANDOM}:${SECONDS}"
  if ! mkdir "$INSTALL_LOCK_DIR" 2>/dev/null; then
    echo "[ERR] another AIHOT Skill install is running, or a prior interrupted install left this lock:" >&2
    echo "  $INSTALL_LOCK_DIR" >&2
    echo "Confirm no install.sh process is active before removing that exact directory." >&2
    exit 4
  fi
  if ! printf '%s\n' "$INSTALL_LOCK_OWNER" > "$INSTALL_LOCK_DIR/owner"; then
    rm -f -- "$INSTALL_LOCK_DIR/owner"
    rmdir -- "$INSTALL_LOCK_DIR" 2>/dev/null || true
    fail "cannot record the AIHOT Skill installer lock owner"
  fi
  INSTALL_LOCK_OWNED=1
}

hash_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    fail "neither shasum nor sha256sum is available"
  fi
}

restore_on_failure() {
  local i
  if [[ "$COMMITTED" -eq 0 ]]; then
    if [[ "$CLAUDE_COMPAT_CREATED" -eq 1 && -L "$CLAUDE_COMPAT_LINK" ]]; then
      rm -f -- "$CLAUDE_COMPAT_LINK" || true
    fi
    if [[ "$TARGET_ACTIVATED" -eq 1 && -e "$INSTALL_DIR" ]]; then
      rm -rf -- "$INSTALL_DIR" || true
    fi
    if [[ -n "$TARGET_BACKUP" && -e "$TARGET_BACKUP" && ! -e "$INSTALL_DIR" ]]; then
      mv "$TARGET_BACKUP" "$INSTALL_DIR" || true
    fi
    for ((i = 0; i < LEGACY_COUNT; i++)); do
      if [[ -n "${LEGACY_BACKUPS[$i]:-}" && -e "${LEGACY_BACKUPS[$i]}" && ! -e "${LEGACY_PATHS[$i]}" ]]; then
        mv "${LEGACY_BACKUPS[$i]}" "${LEGACY_PATHS[$i]}" || true
      fi
    done
  fi
  if [[ -n "$TMP_ROOT" && -d "$TMP_ROOT" ]]; then
    rm -rf "$TMP_ROOT"
  fi
  release_install_lock
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || { echo "[ERR] --target requires a value" >&2; exit 2; }
      [[ -z "$TARGET" && -z "$INSTALL_DIR" ]] || {
        echo "[ERR] choose exactly one --target or --dir" >&2
        exit 2
      }
      TARGET="$2"
      shift 2
      ;;
    --dir)
      [[ $# -ge 2 ]] || { echo "[ERR] --dir requires a value" >&2; exit 2; }
      [[ -z "$TARGET" && -z "$INSTALL_DIR" ]] || {
        echo "[ERR] choose exactly one --target or --dir" >&2
        exit 2
      }
      INSTALL_DIR="$(expand_home_path "$2")"
      TARGET="custom"
      shift 2
      ;;
    --migrate-legacy)
      MIGRATE_LEGACY=1
      shift
      ;;
    --actor)
      [[ $# -ge 2 ]] || { echo "[ERR] --actor requires a UUID v4" >&2; exit 2; }
      [[ "$ACTOR_MODE_SET" -eq 0 ]] || { echo "[ERR] choose exactly one --actor or --no-actor" >&2; exit 2; }
      ACTOR_MODE_SET=1
      ACTOR_ID="$(normalize_actor_id "$2")"
      validate_actor_id "$ACTOR_ID" || { echo "[ERR] --actor must be an RFC 4122 UUID v4" >&2; exit 2; }
      shift 2
      ;;
    --no-actor)
      [[ "$ACTOR_MODE_SET" -eq 0 ]] || { echo "[ERR] choose exactly one --actor or --no-actor" >&2; exit 2; }
      ACTOR_MODE_SET=1
      ACTOR_DISABLED=1
      SKIP_ACTOR_GENERATION=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ERR] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "[ERR] no target selected; the installer will not guess Claude or another Agent" >&2
  usage >&2
  exit 2
fi

case "$TARGET" in
  claude)
    INSTALL_DIR="$HOME/.agents/skills/aihot"
    SHARED_TARGET=1
    CLAUDE_COMPAT_LINK="$HOME/.claude/skills/aihot"
    ;;
  codex|gemini|copilot|opencode|agents)
    INSTALL_DIR="$HOME/.agents/skills/aihot"
    SHARED_TARGET=1
    ;;
  custom)
    [[ "$MIGRATE_LEGACY" -eq 0 ]] || {
      echo "[ERR] --migrate-legacy cannot be combined with --dir" >&2
      exit 2
    }
    ;;
  *)
    echo "[ERR] unsupported target: $TARGET" >&2
    usage >&2
    exit 2
    ;;
esac

INSTALL_DIR="$(expand_home_path "$INSTALL_DIR")"
INSTALL_PARENT="$(dirname "$INSTALL_DIR")"
mkdir -p "$INSTALL_PARENT"
acquire_install_lock
trap restore_on_failure EXIT
validate_target_path

if [[ "$SHARED_TARGET" -eq 1 ]]; then
  LEGACY_CANDIDATES=(
    "$HOME/.claude/skills/aihot"
    "${CODEX_HOME:-$HOME/.codex}/skills/aihot"
    "$HOME/.gemini/skills/aihot"
    "$HOME/.copilot/skills/aihot"
    "$HOME/.config/opencode/skills/aihot"
  )
  for legacy in "${LEGACY_CANDIDATES[@]}"; do
    [[ "$legacy" != "$INSTALL_DIR" ]] || continue
    # 厂商目录本身可能已链接到 ~/.agents/skills；同一实体不算重复副本。
    if [[ -e "$INSTALL_DIR" && -e "$legacy" && "$legacy" -ef "$INSTALL_DIR" ]]; then
      continue
    fi
    if [[ -e "$legacy" || -L "$legacy" ]]; then
      [[ -d "$legacy" && ! -L "$legacy" && -f "$legacy/SKILL.md" ]] || {
        fail "legacy path is not a regular Skill directory: $legacy"
      }
      skill_frontmatter_has_line "$legacy/SKILL.md" "name: aihot" || {
        fail "legacy path contains a different Skill and will not be touched: $legacy"
      }
      LEGACY_PATHS[$LEGACY_COUNT]="$legacy"
      LEGACY_COUNT=$((LEGACY_COUNT + 1))
    fi
  done

  # 迁移会移除 ~/.claude/skills/aihot。README 承诺迁移后 Claude Code 的入口是
  # 指向共享安装的软链，因此当本次迁移包含该旧路径时补回兼容软链目标；
  # --target claude 已自行设置，未涉及该路径时不新建 Claude 入口。
  if [[ -z "$CLAUDE_COMPAT_LINK" && "$MIGRATE_LEGACY" -eq 1 ]]; then
    for ((i = 0; i < LEGACY_COUNT; i++)); do
      [[ "${LEGACY_PATHS[$i]}" == "$HOME/.claude/skills/aihot" ]] || continue
      CLAUDE_COMPAT_LINK="$HOME/.claude/skills/aihot"
      break
    done
  fi

  if [[ "$LEGACY_COUNT" -gt 0 && "$MIGRATE_LEGACY" -eq 0 ]]; then
    echo "[ERR] legacy AIHOT Skill copies found; refusing to create a duplicate:" >&2
    for ((i = 0; i < LEGACY_COUNT; i++)); do
      echo "  - ${LEGACY_PATHS[$i]}" >&2
    done
    echo "Re-run with --migrate-legacy to replace them with one shared copy," >&2
    echo "or use --dir <existing-path> to update one location explicitly." >&2
    exit 3
  fi
fi

TMP_ROOT="$(mktemp -d "$INSTALL_PARENT/.aihot-install.XXXXXX")"
PACKAGE_DIR="$TMP_ROOT/package"
MANIFEST_FILE="$TMP_ROOT/manifest.sha256"
mkdir -p "$PACKAGE_DIR"

echo ""
echo "Installing AIHOT Agent Skill"
echo "  target: $TARGET"
echo "  path:   $INSTALL_DIR"
echo ""

curl -fsSL --max-time 30 "$SITE/aihot-skill/manifest.sha256" -o "$MANIFEST_FILE"
[[ -s "$MANIFEST_FILE" ]] || fail "downloaded manifest is empty"

FILE_COUNT=0
SEEN_FILES=$'\n'
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ "$line" =~ ^([0-9a-f]{64})[[:space:]][[:space:]]([A-Za-z0-9._/-]+)$ ]] || {
    fail "invalid manifest line"
  }
  expected_hash="${BASH_REMATCH[1]}"
  relative_path="${BASH_REMATCH[2]}"
  [[ "$relative_path" != /* && "$relative_path" != *".."* && "$relative_path" != *"//"* ]] || {
    fail "unsafe package path: $relative_path"
  }
  case "$relative_path" in
    SKILL.md|LICENSE|agents/openai.yaml|references/api.md|references/sync.md|references/errors.md) ;;
    *) fail "unexpected non-runtime package path: $relative_path" ;;
  esac
  [[ "$SEEN_FILES" != *$'\n'"$relative_path"$'\n'* ]] || fail "duplicate manifest path: $relative_path"
  SEEN_FILES+="$relative_path"$'\n'
  FILE_COUNT=$((FILE_COUNT + 1))
  [[ "$FILE_COUNT" -le 50 ]] || fail "manifest contains too many files"

  output_path="$PACKAGE_DIR/$relative_path"
  mkdir -p "$(dirname "$output_path")"
  curl -fsSL --max-time 30 "$SITE/aihot-skill/$relative_path" -o "$output_path"
  actual_hash="$(hash_file "$output_path")"
  [[ "$actual_hash" == "$expected_hash" ]] || {
    fail "SHA-256 mismatch for $relative_path; existing installation was not changed"
  }
  chmod 0644 "$output_path"
done < "$MANIFEST_FILE"

[[ "$FILE_COUNT" -eq 6 ]] || fail "runtime package must contain exactly 6 files"

for required in \
  SKILL.md \
  LICENSE \
  agents/openai.yaml \
  references/api.md \
  references/sync.md \
  references/errors.md
do
  [[ -f "$PACKAGE_DIR/$required" ]] || fail "runtime package is missing $required"
done

skill_frontmatter_has_line "$PACKAGE_DIR/SKILL.md" "name: aihot" || {
  fail "downloaded SKILL.md failed identity validation"
}
skill_frontmatter_has_line "$PACKAGE_DIR/SKILL.md" "license: MIT. See LICENSE" || {
  fail "downloaded SKILL.md failed license validation"
}
grep -q '^interface:$' "$PACKAGE_DIR/agents/openai.yaml" || {
  fail "downloaded agents/openai.yaml failed validation"
}
[[ ! -e "$PACKAGE_DIR/README.md" ]] || fail "README.md must not enter the runtime package"

# Next.js 不提供 dotfile，因此 `.gitignore` 不从公网下载、不进入 manifest；只在远端运行包
# 完整验签后本地生成，防止项目级安装时误提交假名 Actor 或持久退出标记。
printf '/.aihot-actor-id\n/.aihot-actor-disabled\n' > "$PACKAGE_DIR/.gitignore"
chmod 0644 "$PACKAGE_DIR/.gitignore"

# 随机假名 Actor 与持久退出标记都是本机安装状态，不属于可执行 Skill 包，也不进入 manifest。
# 更新／迁移时尊重退出优先于旧 ID；显式 --actor 才重新加入。它只是可选分析身份，任何
# 读取、迁移或生成失败都绝不能阻断 Skill 安装。
if [[ "$ACTOR_MODE_SET" -eq 0 && -f "$INSTALL_DIR/.aihot-actor-disabled" ]]; then
  ACTOR_DISABLED=1
  SKIP_ACTOR_GENERATION=1
fi
if [[ "$ACTOR_MODE_SET" -eq 0 && "$ACTOR_DISABLED" -eq 0 && "$LEGACY_COUNT" -gt 0 ]]; then
  for ((i = 0; i < LEGACY_COUNT; i++)); do
    if [[ -f "${LEGACY_PATHS[$i]}/.aihot-actor-disabled" ]]; then
      ACTOR_DISABLED=1
      SKIP_ACTOR_GENERATION=1
      break
    fi
  done
fi
if [[ "$ACTOR_DISABLED" -eq 0 && -z "$ACTOR_ID" && -f "$INSTALL_DIR/.aihot-actor-id" ]]; then
  ACTOR_ID="$(normalize_actor_id "$(tr -d '[:space:]' < "$INSTALL_DIR/.aihot-actor-id")")"
  if ! validate_actor_id "$ACTOR_ID"; then
    echo "[WARN] Existing .aihot-actor-id is invalid; rotating or continuing without it." >&2
    ACTOR_ID=""
  fi
fi
if [[ "$ACTOR_DISABLED" -eq 0 && -z "$ACTOR_ID" && "$LEGACY_COUNT" -gt 0 ]]; then
  for ((i = 0; i < LEGACY_COUNT; i++)); do
    legacy_actor_file="${LEGACY_PATHS[$i]}/.aihot-actor-id"
    [[ -f "$legacy_actor_file" ]] || continue
    legacy_actor="$(normalize_actor_id "$(tr -d '[:space:]' < "$legacy_actor_file")")"
    if ! validate_actor_id "$legacy_actor"; then
      echo "[WARN] Ignoring an invalid legacy .aihot-actor-id at ${LEGACY_PATHS[$i]}." >&2
      continue
    fi
    if [[ -z "$ACTOR_ID" ]]; then
      ACTOR_ID="$legacy_actor"
    elif [[ "$ACTOR_ID" != "$legacy_actor" ]]; then
      echo "[WARN] Legacy copies have conflicting Actor IDs; installing without one." >&2
      echo "[WARN] Re-run later with --actor <uuid-v4> if you want cross-channel deduplication." >&2
      ACTOR_ID=""
      SKIP_ACTOR_GENERATION=1
      break
    fi
  done
fi
if [[ "$ACTOR_DISABLED" -eq 0 && -z "$ACTOR_ID" && "$SKIP_ACTOR_GENERATION" -eq 0 ]]; then
  if generated_actor="$(generate_actor_id)"; then
    ACTOR_ID="$generated_actor"
  else
    echo "[WARN] No UUID v4 generator is available; installing without optional Actor analytics." >&2
  fi
fi
if [[ -n "$ACTOR_ID" ]]; then
  printf '%s\n' "$ACTOR_ID" > "$PACKAGE_DIR/.aihot-actor-id"
  chmod 0600 "$PACKAGE_DIR/.aihot-actor-id"
elif [[ "$ACTOR_DISABLED" -eq 1 ]]; then
  printf 'disabled\n' > "$PACKAGE_DIR/.aihot-actor-disabled"
  chmod 0600 "$PACKAGE_DIR/.aihot-actor-disabled"
fi

for ((i = 0; i < LEGACY_COUNT; i++)); do
  legacy="${LEGACY_PATHS[$i]}"
  backup="$(dirname "$legacy")/.aihot-migrate.$$.${i}"
  [[ ! -e "$backup" ]] || fail "temporary migration path already exists: $backup"
  mv "$legacy" "$backup"
  LEGACY_BACKUPS[$i]="$backup"
done

if [[ -e "$INSTALL_DIR" ]]; then
  TARGET_BACKUP="$INSTALL_PARENT/.aihot-previous.$$"
  [[ ! -e "$TARGET_BACKUP" ]] || fail "temporary update path already exists: $TARGET_BACKUP"
  mv "$INSTALL_DIR" "$TARGET_BACKUP"
fi

if ! mv "$PACKAGE_DIR" "$INSTALL_DIR"; then
  fail "failed to activate the validated package"
fi
TARGET_ACTIVATED=1

if [[ -n "$CLAUDE_COMPAT_LINK" ]]; then
  mkdir -p "$(dirname "$CLAUDE_COMPAT_LINK")"
  if [[ -e "$CLAUDE_COMPAT_LINK" ]]; then
    [[ "$CLAUDE_COMPAT_LINK" -ef "$INSTALL_DIR" ]] || {
      fail "Claude compatibility path points somewhere else: $CLAUDE_COMPAT_LINK"
    }
  else
    ln -s "$INSTALL_DIR" "$CLAUDE_COMPAT_LINK" || {
      fail "failed to create Claude compatibility symlink: $CLAUDE_COMPAT_LINK"
    }
    CLAUDE_COMPAT_CREATED=1
  fi
fi
COMMITTED=1

cleanup_committed_backup "$TARGET_BACKUP"
for ((i = 0; i < LEGACY_COUNT; i++)); do
  cleanup_committed_backup "${LEGACY_BACKUPS[$i]}"
done

VERSION="$(sed -n 's/^  version: "\([0-9][0-9.]*\)"$/\1/p' "$INSTALL_DIR/SKILL.md" | head -n 1)"

echo "✓ Installed${VERSION:+ v$VERSION} as one complete package."
if [[ -n "$ACTOR_ID" ]]; then
  echo "✓ Preserved a local pseudonymous Actor ID for cross-channel deduplication (not authentication)."
else
  echo "✓ Installed without optional Actor analytics; all Skill features remain available."
fi
if [[ "$LEGACY_COUNT" -gt 0 ]]; then
  echo "✓ Replaced $LEGACY_COUNT legacy copy/copies with the shared installation."
fi
if [[ -n "$CLAUDE_COMPAT_LINK" ]]; then
  echo "✓ Claude Code compatibility points to the shared installation: $CLAUDE_COMPAT_LINK"
fi
echo ""
echo "Next: restart your Agent or start a new conversation, then ask:"
echo "  过去 24 小时 AI 圈最重要的 5 件事是什么？"
echo ""
echo "Success means the Agent finds exactly one aihot Skill, states the time window,"
echo "and links titles to AIHOT."
