#!/usr/bin/env python3
"""
Consolidate unreleased changelogs into a weekly release file and update CHANGELOG.md.

Usage:
    python scripts/consolidate_release.py                       # defaults to today's date
    python scripts/consolidate_release.py --date 2026-04-10     # specific date
    python scripts/consolidate_release.py --version v1.2.0      # named version
    python scripts/consolidate_release.py --dry-run              # preview without writing
"""

import argparse
import datetime
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UNRELEASED_DIR = REPO_ROOT / "changelogs" / "unreleased"
RELEASES_DIR = REPO_ROOT / "releases"
CHANGELOG_FILE = REPO_ROOT / "CHANGELOG.md"

# Sections in display order
SECTIONS = [
    "Added",
    "Changed",
    "Fixed",
    "Deprecated",
    "Removed",
    "Security",
    "Breaking Changes",
    "Deployment Steps",
    "Testing Plan",
    "Notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consolidate unreleased changelogs into a release.")
    parser.add_argument("--date", type=str, default=None, help="Release date (YYYY-MM-DD). Defaults to today.")
    parser.add_argument("--version", type=str, default=None, help="Release version label (e.g. v1.2.0).")
    parser.add_argument("--dry-run", action="store_true", help="Preview the release without writing files.")
    return parser.parse_args()


def discover_changelogs() -> list[Path]:
    """Return all .md files in unreleased/, excluding .gitkeep."""
    if not UNRELEASED_DIR.exists():
        return []
    return sorted(
        p for p in UNRELEASED_DIR.iterdir()
        if p.suffix == ".md" and p.name != ".gitkeep"
    )


def parse_changelog(path: Path) -> dict:
    """Parse a single changelog file into metadata and sections."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    metadata = {}
    sections: dict[str, list[str]] = {}
    current_section = None

    for line in lines:
        # Extract metadata from blockquote header
        meta_match = re.match(r"^>\s*\*\*(.+?):\*\*\s*(.+)$", line)
        if meta_match:
            metadata[meta_match.group(1).strip()] = meta_match.group(2).strip()
            continue

        # Detect section headings
        heading_match = re.match(r"^##\s+(.+)$", line)
        if heading_match:
            current_section = heading_match.group(1).strip()
            if current_section not in sections:
                sections[current_section] = []
            continue

        # Collect bullet items under current section
        if current_section:
            item_match = re.match(r"^-\s+\[?[xX ]?\]?\s*(.+)$", line)
            if item_match:
                content = item_match.group(1).strip()
                if content:  # skip empty placeholder bullets
                    sections[current_section].append(line.strip())

    return {"metadata": metadata, "sections": sections}


def merge_changelogs(parsed_list: list[tuple[str, dict]]) -> dict[str, list[str]]:
    """Merge multiple parsed changelogs, annotating items with their source branch."""
    merged: dict[str, list[str]] = {}

    for branch_name, parsed in parsed_list:
        for section, items in parsed["sections"].items():
            if not items:
                continue
            if section not in merged:
                merged[section] = []
            for item in items:
                # Prefix with branch name for traceability
                merged[section].append(f"- ({branch_name}) {item.lstrip('- ')}")

    return merged


def render_release(version_label: str, release_date: str, merged: dict[str, list[str]]) -> str:
    """Render the consolidated release as markdown."""
    lines = [
        f"# Release: {version_label}",
        f"**Date:** {release_date}",
        "",
    ]

    for section in SECTIONS:
        items = merged.get(section, [])
        if not items:
            continue
        lines.append(f"## {section}")
        for item in items:
            lines.append(item)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_release_file(version_label: str, content: str) -> Path:
    """Write the release to releases/<label>.md."""
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    safe_label = version_label.replace("/", "-").replace(" ", "-")
    release_path = RELEASES_DIR / f"release_{safe_label}.md"
    release_path.write_text(content, encoding="utf-8")
    return release_path


def update_running_changelog(content: str):
    """Prepend the new release block to CHANGELOG.md (newest first)."""
    separator = "\n---\n\n"

    if CHANGELOG_FILE.exists():
        existing = CHANGELOG_FILE.read_text(encoding="utf-8")
        # Find the first --- separator (after the header)
        parts = existing.split("---", 1)
        if len(parts) == 2:
            header = parts[0].rstrip()
            rest = parts[1]
            new_content = f"{header}\n\n---\n\n{content}{separator}{rest.lstrip()}"
        else:
            new_content = f"{existing.rstrip()}\n\n---\n\n{content}"
    else:
        new_content = (
            "# Changelog\n\n"
            "All notable changes to this project will be documented in this file.\n"
            "The format is based on [Keep a Changelog](https://keepachangelog.com/).\n\n"
            f"---\n\n{content}"
        )

    CHANGELOG_FILE.write_text(new_content, encoding="utf-8")


def cleanup_unreleased(files: list[Path]):
    """Delete consolidated changelog files, preserving .gitkeep."""
    for f in files:
        f.unlink()


def main():
    args = parse_args()

    files = discover_changelogs()
    if not files:
        print("No unreleased changelogs found. Nothing to consolidate.")
        return

    print(f"Found {len(files)} unreleased changelog(s):")
    for f in files:
        print(f"  - {f.name}")

    parsed_list = [(f.stem, parse_changelog(f)) for f in files]
    merged = merge_changelogs(parsed_list)

    release_date = args.date or datetime.date.today().isoformat()
    version_label = args.version or release_date

    content = render_release(version_label, release_date, merged)

    if args.dry_run:
        print("\n--- DRY RUN: Release preview ---\n")
        print(content)
        return

    release_path = write_release_file(version_label, content)
    update_running_changelog(content)
    cleanup_unreleased(files)

    print(f"\nRelease consolidated: {release_path.relative_to(REPO_ROOT)}")
    print(f"CHANGELOG.md updated.")
    print(f"Cleaned up {len(files)} unreleased changelog(s).")


if __name__ == "__main__":
    main()
