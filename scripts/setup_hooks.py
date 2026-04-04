#!/usr/bin/env python3
"""Install git hooks for the devops_dev_package repository."""

import shutil
import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_SRC = REPO_ROOT / "hooks"
GIT_HOOKS_DIR = REPO_ROOT / ".git" / "hooks"


def install_hooks():
    if not (REPO_ROOT / ".git").is_dir():
        print("Error: .git directory not found. Run 'git init' first.")
        return

    GIT_HOOKS_DIR.mkdir(parents=True, exist_ok=True)

    installed = 0
    for hook_file in sorted(HOOKS_SRC.iterdir()):
        if hook_file.name.startswith("."):
            continue
        dest = GIT_HOOKS_DIR / hook_file.name
        shutil.copy2(hook_file, dest)
        dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"  Installed hook: {hook_file.name}")
        installed += 1

    # Ensure required directories exist
    (REPO_ROOT / "changelogs" / "unreleased").mkdir(parents=True, exist_ok=True)
    (REPO_ROOT / "releases").mkdir(parents=True, exist_ok=True)

    print(f"\n{installed} hook(s) installed successfully.")
    print("Test it: git checkout -b test/verify-hook")


if __name__ == "__main__":
    install_hooks()
