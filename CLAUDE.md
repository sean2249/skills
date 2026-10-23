# CLAUDE.md

## Issue workflow

Issues move `status: raw` → (`status: needs-info`) → `status: ai-enhanced` → `status: approved`.
Only the author sets `status: approved`. Skills: `issue-enhance`, `issue-implement`.

- Verify command: `python3 -c "import glob,yaml;[yaml.safe_load(open(f)) for f in glob.glob('.github/workflows/*.yml')+glob.glob('skills/**/assets/*.yml',recursive=True)]" && python3 -m py_compile $(git ls-files 'skills/**/*.py')`
- Preview URL: none
- Low-risk paths: `.github/low-risk-paths.txt`
- Merge mode: `auto`
- Article target: none
- Issue assets branch: `issue-assets`
- Mockup path: `<N>/<file>` (inside the issue assets branch; `<N>` = issue number)

This repo is public: only the owner's issues enter the flow, outside issues get `external`, security findings stay out of public PRs and issues, and every mockup, screenshot and run output uses made-up data (README → Public repos). Never name the author's private repos in anything committed or posted here.

Changes to skills (`skills/**`, `.claude-plugin/`) are never `risk: low`: every SKILL.md runs in all of the author's repos with the author's `gh` login.

## Releasing shared workflows

`.github/workflows/issue-status.yml`, `risk-guard.yml`, `needs-info-reply.yml` and `article-pending.yml` are the reusable workflows every repo calls with a pinned tag. This repo's own callers are `.github/workflows/self-*.yml` (not the usual names, which are taken by the reusable workflows) and are pinned to a tag too.

When a PR changes any of those four reusable workflows, its description ends with a reminder, and after it merges:

1. Cut the next tag with release notes (README → Versions): `gh release create v<N> --target main --title v<N> --notes-file <notes.md>`.
2. Bump this repo's `self-*.yml` callers to `@v<N>` in a `risk: high` PR. `issue-workflow-setup` repair mode looks for the usual caller names, so here bump with `sed -i '' -E 's#(uses: *[^ ]+/\.github/workflows/[a-z-]+\.yml)@v[0-9]+#\1@v<N>#' .github/workflows/self-*.yml`.
3. Run `issue-workflow-setup` repair mode in every other repo that uses the workflow, so each one opens its own bump PR.

A published tag is never moved; a fix is a new tag.
