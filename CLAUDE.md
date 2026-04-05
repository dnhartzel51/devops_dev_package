# DevOps Dev Package

Snowflake + dbt project using Azure DevOps for code control and PRs.

## Project Structure

```
release/
├── template.md              # PR changelog template (source of truth for the git hook)
├── unreleased/              # Individual PR changelogs auto-created by git hook
└── <version>/               # Created at release time by consolidation script
    ├── release_<version>.md # Consolidated release notes
    ├── <branch>.md          # Original PR changelogs (moved from unreleased/)
    └── ...                  # Deployment scripts, test notebooks, etc.
scripts/
├── setup_hooks.py           # Installs git hooks from hooks/ into .git/hooks/
└── consolidate_release.py   # Weekly release consolidation script
hooks/
└── post-checkout            # Auto-creates changelog on new branch creation
CHANGELOG.md                 # Running cumulative changelog (newest first)
```

## Branching Convention

Branch names follow: `<work_item_number>_<descriptive_name>` (e.g. `4521_add_inventory_model`).
The post-checkout hook extracts the work item number and populates the changelog template automatically.

## Changelog Workflow

### Setup (once per clone)
```bash
python scripts/setup_hooks.py
```

### Developer flow
1. `git checkout -b 1234_my_feature` — changelog auto-created at `release/unreleased/1234_my_feature.md`
2. Fill out the template sections. Use `- N/A` for sections that don't apply.
3. Submit PR with the changelog included.

### Weekly release
```bash
python scripts/consolidate_release.py --version v1.0.0          # or --date 2026-04-10
python scripts/consolidate_release.py --version v1.0.0 --dry-run # preview first
```

This:
- Creates `release/<version>/` folder with the consolidated release notes
- Moves individual PR changelogs into that folder
- Updates `CHANGELOG.md` (prepends, newest first)
- Deployment Steps and Testing Plan sections are excluded from the consolidated output
- Add any deployment scripts, test notebooks, or other artifacts to the release folder

## Key Design Decisions

- One changelog file per PR prevents merge conflicts in the changelog system
- `hooks/post-checkout` is bash (not Python) for zero-dependency speed
- Template uses HTML comments for section descriptions (invisible in rendered markdown)
- `- N/A` convention for empty sections — filtered out during consolidation
- Individual PR changelogs are preserved (moved to release folder, not deleted)
