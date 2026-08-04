#!/usr/bin/env python3
"""Save a Markdown research note into Obsidian, preferring the official CLI."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

SKILL_NAME = "hv-analysis"
CONFIG_FILENAME = "config.yaml"
CONFIG_EXAMPLE_FILENAME = "config.example"
REQUIRED_CONFIG_KEYS = ("vault", "default_path")


def resolve_config_dir() -> Path:
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_home:
        return Path(xdg_home).expanduser() / SKILL_NAME
    return Path.home() / ".config" / SKILL_NAME


def resolve_skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_example_path() -> Path:
    example_path = resolve_skill_dir() / CONFIG_EXAMPLE_FILENAME
    if not example_path.exists():
        raise SystemExit(f"Bundled config example not found: {example_path}")
    return example_path


def parse_simple_yaml(config_path: Path) -> dict[str, str]:
    config: dict[str, str] = {}
    for lineno, raw_line in enumerate(config_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise SystemExit(f"Invalid config line {lineno} in {config_path}: {raw_line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value[:1] == value[-1:] and value[:1] in {'"', "'"}:
            value = value[1:-1]
        config[key] = value
    return config


def load_config_if_exists() -> tuple[Path, Path, dict[str, str]]:
    config_dir = resolve_config_dir()
    config_path = config_dir / CONFIG_FILENAME
    if not config_path.exists():
        return config_dir, config_path, {}
    config = parse_simple_yaml(config_path)
    missing_keys = [key for key in REQUIRED_CONFIG_KEYS if not config.get(key)]
    if missing_keys:
        raise SystemExit(f"Missing config keys in {config_path}: {', '.join(missing_keys)}")
    return config_dir, config_path, config


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "", name).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        cleaned = "untitled_research_note"
    if not cleaned.endswith(".md"):
        cleaned += ".md"
    return cleaned


def derive_filename(markdown: str) -> str:
    title_match = re.search(r'^title:\s*"?(.*?)"?\s*$', markdown, re.MULTILINE)
    if title_match and title_match.group(1).strip():
        return sanitize_filename(title_match.group(1).strip())

    h1_match = re.search(r"^#\s+(.+?)\s*$", markdown, re.MULTILINE)
    if h1_match and h1_match.group(1).strip():
        return sanitize_filename(h1_match.group(1).strip())

    return "untitled_research_note.md"


def strip_frontmatter(markdown: str) -> str:
    lines = markdown.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                return "".join(lines[idx + 1 :])
    return markdown


def compute_word_count(markdown: str) -> int:
    # Follow the local doc convention: count characters after frontmatter.
    return len(strip_frontmatter(markdown))


def maybe_update_word_count(markdown: str) -> str:
    has_trailing_newline = markdown.endswith("\n")
    lines = markdown.splitlines()

    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() != "---":
                continue

            frontmatter_lines = lines[1:idx]
            body_lines = lines[idx + 1 :]
            updated = False
            new_frontmatter: list[str] = []
            for line in frontmatter_lines:
                if re.match(r"^\s*word_count\s*:", line):
                    new_frontmatter.append(f"word_count: {compute_word_count(markdown)}")
                    updated = True
                else:
                    new_frontmatter.append(line)
            if not updated:
                return markdown

            rebuilt = "\n".join(["---", *new_frontmatter, "---", *body_lines])
            if has_trailing_newline:
                rebuilt += "\n"
            return rebuilt

    return markdown


def normalize_markdown(markdown: str) -> str:
    return markdown.replace("\r\n", "\n").rstrip("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Save a Markdown note into Obsidian.")
    parser.add_argument("input", help="Path to the Markdown file to save.")
    parser.add_argument("--filename", help="Target note filename. Defaults to title/H1.")
    parser.add_argument("--path", help="Target folder inside the vault.")
    parser.add_argument("--vault-root", help="Override vault root path from private config.")
    parser.add_argument("--vault", help="Override vault name from private config.")
    parser.add_argument(
        "--write-config",
        action="store_true",
        help="Persist the provided vault/path settings into ~/.config/hv-analysis/config.yaml.",
    )
    return parser


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def quote_yaml(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_config(config_path: Path, vault_name: str, target_folder: str, vault_root: str | None, output_mode: str) -> None:
    lines = [
        f"vault: {quote_yaml(vault_name)}",
    ]
    if vault_root:
        lines.append(f"vault_root: {quote_yaml(vault_root)}")
    lines.extend(
        [
            f"default_path: {quote_yaml(target_folder)}",
            f"default_output_mode: {quote_yaml(output_mode)}",
            "",
        ]
    )
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("\n".join(lines), encoding="utf-8")


def discover_vault_root(vault_name: str) -> Path | None:
    if not vault_name:
        return None
    home_dir = Path.home()
    candidates = [
        home_dir / "Library/Mobile Documents/iCloud~md~obsidian/Documents" / vault_name,
        home_dir / "Documents/obsidian" / vault_name,
        home_dir / "Obsidian" / vault_name,
        home_dir / vault_name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def try_obsidian_create(relative_path: Path, vault_name: str, markdown: str) -> tuple[bool, str]:
    obsidian_cli = shutil.which("obsidian")
    if not obsidian_cli:
        return False, "obsidian CLI not found"

    result = run_command(
        [
            obsidian_cli,
            "create",
            f"path={relative_path.as_posix()}",
            f"content={markdown}",
            "overwrite",
            f"vault={vault_name}",
        ]
    )
    if result.returncode != 0:
        output = (result.stderr or result.stdout).strip()
        return False, output or "obsidian create failed"
    return True, "obsidian create succeeded"


def try_obsidian_read(relative_path: Path, vault_name: str) -> tuple[bool, str]:
    obsidian_cli = shutil.which("obsidian")
    if not obsidian_cli:
        return False, "obsidian CLI not found"

    result = run_command(
        [
            obsidian_cli,
            "read",
            f"path={relative_path.as_posix()}",
            f"vault={vault_name}",
        ]
    )
    if result.returncode != 0:
        output = (result.stderr or result.stdout).strip()
        return False, output or "obsidian read failed"
    return True, result.stdout


def verify_obsidian_content(relative_path: Path, vault_name: str, expected_markdown: str) -> tuple[bool, str]:
    expected = normalize_markdown(expected_markdown)
    last_output = ""

    for attempt in range(3):
        read_ok, read_output = try_obsidian_read(relative_path, vault_name)
        if not read_ok:
            return False, read_output
        if normalize_markdown(read_output) == expected:
            return True, read_output
        last_output = read_output
        time.sleep(0.2 * (attempt + 1))

    return False, (
        "obsidian read content mismatch after write: "
        f"expected {len(expected)} chars, got {len(normalize_markdown(last_output))} chars"
    )


def write_direct(target_path: Path, markdown: str) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(markdown, encoding="utf-8")


def verify_direct(target_path: Path, expected_markdown: str) -> str:
    if not target_path.exists():
        raise SystemExit(f"Direct write verification failed, file not found: {target_path}")
    actual = target_path.read_text(encoding="utf-8")
    if normalize_markdown(actual) != normalize_markdown(expected_markdown):
        raise SystemExit(f"Direct write verification failed, content mismatch: {target_path}")
    return actual


def main() -> int:
    args = build_parser().parse_args()
    config_dir, config_path, config = load_config_if_exists()
    config_existed_before = config_path.exists()
    example_path = resolve_example_path()
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Markdown input not found: {input_path}")

    markdown = maybe_update_word_count(input_path.read_text(encoding="utf-8"))
    vault_name = args.vault or config.get("vault", "")
    vault_root_value = args.vault_root or config.get("vault_root", "")
    target_folder = args.path or config.get("default_path", "")
    output_mode = config.get("default_output_mode", "pdf")

    missing_inputs = []
    if not vault_name:
        missing_inputs.append("vault")
    if not target_folder:
        missing_inputs.append("path")
    if missing_inputs:
        raise SystemExit(
            "Missing Obsidian preferences: "
            + ", ".join(missing_inputs)
            + "\n"
            + "If the user asked for note output and ~/.config/hv-analysis/config.yaml does not exist yet, "
            + "ask them for their Obsidian vault name and target note folder. "
            + "They can either edit the config themselves by copying "
            + f"{example_path} to {config_path}, or you can rerun this script with --vault and --path "
            + "and add --write-config to create the config for them."
        )

    discovered_vault_root = discover_vault_root(vault_name)
    effective_vault_root = vault_root_value or (str(discovered_vault_root) if discovered_vault_root else "")

    if args.write_config:
        write_config(
            config_path=config_path,
            vault_name=vault_name,
            target_folder=target_folder,
            vault_root=effective_vault_root or None,
            output_mode=output_mode,
        )

    filename = sanitize_filename(args.filename) if args.filename else derive_filename(markdown)
    relative_path = Path(str(target_folder).strip("/")) / filename
    target_path = Path(effective_vault_root).expanduser() / relative_path if effective_vault_root else None

    if target_path is not None and target_path.exists():
        write_direct(target_path, markdown)
        verify_direct(target_path, markdown)
        print("Saved note with direct file overwrite")
        print(f"Vault: {vault_name}")
        print(f"Relative path: {relative_path.as_posix()}")
        print(f"Absolute path: {target_path}")
        if args.write_config:
            print(f"Config written: {config_path}")
        elif config_existed_before:
            print(f"Config used: {config_path}")
        else:
            print("Config source: runtime parameters only")
        print(f"Verification: direct file read matched expected content ({compute_word_count(markdown)} chars after frontmatter)")
        return 0

    create_ok, create_message = try_obsidian_create(relative_path, vault_name, markdown)
    if create_ok:
        read_ok, read_output = verify_obsidian_content(relative_path, vault_name, markdown)
        if read_ok:
            print("Saved note with obsidian CLI")
            print(f"Vault: {vault_name}")
            print(f"Relative path: {relative_path.as_posix()}")
            if target_path is not None:
                print(f"Absolute path: {target_path}")
            if args.write_config:
                print(f"Config written: {config_path}")
            elif config_existed_before:
                print(f"Config used: {config_path}")
            else:
                print("Config source: runtime parameters only")
            print(f"Verification: obsidian read matched expected content ({compute_word_count(markdown)} chars after frontmatter)")
            return 0
        print(f"obsidian CLI content verification failed, falling back to direct file write: {read_output}")
    else:
        print(f"obsidian CLI save skipped, falling back to direct file write: {create_message}")

    if target_path is None:
        raise SystemExit(
            "Direct file-write fallback requires vault_root.\n"
            "Provide --vault-root, add vault_root to ~/.config/hv-analysis/config.yaml, "
            "or use a vault location that can be auto-discovered."
        )

    write_direct(target_path, markdown)
    verify_direct(target_path, markdown)
    print("Saved note with direct file write")
    print(f"Vault: {vault_name}")
    print(f"Relative path: {relative_path.as_posix()}")
    print(f"Absolute path: {target_path}")
    if args.write_config:
        print(f"Config written: {config_path}")
    elif config_existed_before:
        print(f"Config used: {config_path}")
    else:
        print("Config source: runtime parameters only")
    print(f"Verification: direct file read matched expected content ({compute_word_count(markdown)} chars after frontmatter)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
