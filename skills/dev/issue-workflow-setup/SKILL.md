---
name: issue-workflow-setup
description: Use when installing the AI-assisted GitHub issue workflow (raw → needs-info → ai-enhanced → approved, risk-labelled PRs) into a repo for the first time, or when repairing / upgrading a repo where its labels, workflows, PR template, or CLAUDE.md `## Issue workflow` section are missing or outdated (e.g. full copies of the workflows instead of thin callers). Runs once per repo; creates labels, brings existing issues into the flow, writes .github callers for the shared reusable workflows, and records merge mode.
---

# issue-workflow-setup

One-time install of the issue workflow used by `issue-enhance`, `issue-implement`, `article-request`, and `article-write`.

The workflow logic lives once, as reusable workflows in the skills repo (`.github/workflows/issue-status.yml`, `risk-guard.yml`, and `article-pending.yml`, all `on: workflow_call`). Each repo gets only short callers, so fixes ship to every repo without re-running setup. `<skills-repo>` below is the `<owner>/<repo>` hosting those reusable workflows: the repo this skill came from, or the author's fork. Ask if unsure, and write it into the callers.

**Never overwrite.** Missing files are created; existing files are merged. Show the plan and get the author's OK before changing anything.

## Preconditions

```bash
gh auth status
gh repo view --json nameWithOwner,visibility,defaultBranchRef \
  --jq '{repo: .nameWithOwner, visibility, default: .defaultBranchRef.name}'
```

Stop if `gh` is not logged in or the cwd is not a GitHub repo.

## Step 1 — Inventory

Check what already exists, without changing anything:

| Item | How to check |
|---|---|
| Labels | `gh label list --limit 200 --json name,description` |
| Existing labels that overlap in meaning (e.g. `ai-review`, `needs-info`, `approved`, `low-risk`) | read the label list above |
| Open issues with no `status: ` label | command below the table |
| `.github/workflows/issue-status.yml` | exists? a thin caller (`uses: <skills-repo>/.github/workflows/issue-status.yml@…`) or an old full copy (has `runs-on:` / `steps:`)? |
| `.github/workflows/risk-guard.yml` | same: caller or old full copy (has `python3 - <<'PY'`)? |
| `.github/workflows/article-pending.yml` | exists? (repos set up before it existed won't have it) |
| Branch protection contexts | `gh api repos/<owner>/<repo>/branches/<default>/protection --jq '.required_status_checks.contexts'` |
| Is this the article repo? | `Article target` in `## Issue workflow` equals this repo (new install: ask in Step 3) |
| `CLAUDE.md` `## Article conventions` (article repo only) | `grep -n '^## Article conventions' CLAUDE.md` |
| `.github/pull_request_template.md` (also `.github/PULL_REQUEST_TEMPLATE/`, root, `docs/`) | file exists? |
| `.github/low-risk-paths.txt` | file exists? |
| `CLAUDE.md` `## Issue workflow` section | `grep -n '^## Issue workflow' CLAUDE.md` |
| CI **job** names (needed for branch protection) | `jobs:` keys (or each job's `name:`) in `.github/workflows/*.yml` |

```bash
# open issues that predate the workflow (no status label yet)
gh issue list --state open --limit 500 --json number,title,labels \
  --jq '.[] | select([.labels[].name | startswith("status: ")] | any | not) | "#\(.number) \(.title)"'
```

The section is `## Issue workflow`, not `## Workflow`: many repos already use `## Workflow` for local dev commands. Leave that one alone.

**Repair / upgrade mode.** If either workflow is an old full copy, plan to replace it with the caller (Step 7). If `article-pending.yml` is missing, plan to add it, plus the `article: pending` / `article: requested` labels (Step 5). Also: the required check name changes from `risk-guard` to `risk-guard / check` (Step 9). If the old copy was customized beyond the shipped template, show the diff and ask before replacing. Everything else in an already-set-up repo follows the usual merge-only rules.

## Step 2 — Detect merge mode

- **Public repo** → `Merge mode: auto` (native auto-merge + branch protection).
- **Private repo** → probe branch protection:
  ```bash
  gh api repos/<owner>/<repo>/branches/<default>/protection
  ```
  - `403` with "Upgrade to GitHub Pro" → free plan, no branch protection, no native auto-merge → `Merge mode: session`.
  - `404 Branch not protected` or `200` → paid plan, protection available → `Merge mode: auto`.

## Step 3 — Show the plan and wait

List, and ask the author to confirm:

- Every label to create.
- Each overlapping existing label, with a choice per label: **keep** (leave as is), **rename** into one of the workflow labels (keeps its issues), or **delete**.
- The open issues that will get `status: raw` (Step 6). The author may exclude some.
- Each file to create or merge, and what will be added.
- The `## Issue workflow` keys to add, and the merge-mode result.

Ask for the values only they know: verify command, preview URL, `Article target` (`<owner>/<repo>`, or "none"), and which paths count as low risk.

## Step 4 — Reconcile overlapping labels

Do this **before** Step 5. Renaming into a name that `gh label create --force` has already created fails because the name is taken.

```bash
# rename: the label and all its issues move to the workflow name
gh label edit "<old-name>" --name "<workflow label>"
# delete: only on the author's explicit choice in Step 3
gh label delete "<old-name>" --yes
```

## Step 5 — Labels

`--force` makes this idempotent (it updates color/description if the label exists, including ones just renamed in Step 4).

```bash
gh label create "status: raw"         --force --color ededed --description "New issue, not yet enhanced by AI"
gh label create "status: needs-info"  --force --color fbca04 --description "AI is blocked on a specific question for the author"
gh label create "status: ai-enhanced" --force --color 1d76db --description "AI-enhanced, waiting for author review"
gh label create "status: approved"    --force --color 0e8a16 --description "Approved by the author for implementation (author only)"
gh label create "risk: low"           --force --color c2e0c6 --description "PR touches only allowlisted low-risk paths; may auto-merge"
gh label create "risk: medium"        --force --color fef2c0 --description "PR needs author review before merge"
gh label create "risk: high"          --force --color b60205 --description "Auth, migrations, workflows, secrets or billing; author review required"
gh label create "article"             --force --color 5319e7 --description "Write a technical article after this ships"
gh label create "article: pending"    --force --color fbca04 --description "Merged article PR; article-request not run yet"
gh label create "article: requested"  --force --color 0e8a16 --description "Article request opened in the article repo"
```

`article-pending` adds `article: pending` when an `article` PR merges; `article-request` swaps it for `article: requested`.

**Article repo only** (its `Article target` is itself), also:

```bash
gh label create "article: devlog" --force --color d4c5f9 --description "Article reconstructs a decision path"
gh label create "article: intro"  --force --color c5def5 --description "Article introduces something to new readers"
```

## Step 6 — Bring existing issues into the flow

`issue-status.yml` only labels issues opened after it's installed, and `issue-enhance` only picks up `status: raw`. Label the open issues the author confirmed in Step 3:

```bash
gh issue edit <N> --add-label "status: raw"   # once per confirmed issue
```

Verify with JSON and filter locally. `gh issue list --label` uses the search index, which lags right after a bulk edit and undercounts:

```bash
gh issue list --state open --limit 500 --json number,labels \
  --jq '[.[] | select([.labels[].name] | index("status: raw"))] | length'
gh issue list --state open --limit 500 --json number,labels \
  --jq '.[] | select([.labels[].name | startswith("status: ")] | any | not) | .number'   # should print nothing left over
```

## Step 7 — Files

Source files live in this skill's `assets/` directory.

| Asset | Target | If target exists |
|---|---|---|
| `assets/issue-status.yml` (caller) | `.github/workflows/issue-status.yml` | Old full copy → replace with the caller (repair mode). Already a caller → keep; fix `<skills-repo>` / ref if wrong |
| `assets/risk-guard.yml` (caller) | `.github/workflows/risk-guard.yml` | Same |
| `assets/article-pending.yml` (caller) | `.github/workflows/article-pending.yml` | Missing → add. Already a caller → keep; fix `<skills-repo>` / ref if wrong |
| `assets/pull_request_template.md` | `.github/pull_request_template.md` (or the existing template's location) | Append only the sections it lacks |
| `assets/low-risk-paths.txt` | `.github/low-risk-paths.txt` | Keep; append only globs the author asked for |
| `assets/claude-md-workflow.md` | `CLAUDE.md` | No `## Issue workflow` → append the section. Section exists → add only missing keys. No `CLAUDE.md` → create it with just this section |
| `assets/claude-md-article-conventions.md` (article repo only) | `CLAUDE.md` | No `## Article conventions` → append with `<fill in>` values, then ask the author to fill them (`article-write` won't run until they do). Exists → leave it |

In all three callers, replace `<skills-repo>` with the real `<owner>/<repo>`.

`low-risk-paths.txt`: keep the header comment, and replace the example globs below it with the author's list from Step 3.

Fill `CLAUDE.md` `## Issue workflow` with the values from Step 3 and the merge mode from Step 2. Leave `<fill in>` for anything the author did not give.

When editing workflow YAML, keep `run:` as a block scalar (`run: |`). A plain inline string containing `"status: raw"` is invalid YAML (`: ` inside a plain scalar). Same for step `name:` values: never put `: ` in them unquoted.

Validate every YAML file you wrote or edited:

```bash
python3 -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" .github/workflows/issue-status.yml
python3 -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" .github/workflows/risk-guard.yml
python3 -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" .github/workflows/article-pending.yml
```

## Step 8 — Ship the setup as a PR

The setup touches `.github/workflows`, so it is `risk: high` and the author merges it.

Branch: if you're already on a non-default branch (e.g. a worktree session's branch), use it. Only when on the default branch, create one:

```bash
[ "$(git branch --show-current)" = "<default>" ] && git switch -c chore/issue-workflow-setup
git add .github CLAUDE.md
git commit -m "Set up issue workflow (labels, status/risk-guard workflows, PR template)"
git push -u origin HEAD
gh pr create --fill --label "risk: high"
```

The `issue-status` workflow only runs once it is on the default branch. `risk-guard` runs on this PR itself; with `risk: high` it passes without reading the allowlist. If the skills repo is private, its reusable workflows can only be called after its Settings → Actions → Access allows this repo.

## Step 9 — Merge settings (right after the setup PR is opened)

No need to wait for the merge. Once the PR exists, `risk-guard` has run once, so it can be named as a required check.

**Merge mode: auto.** These change repo settings, so get the author's OK before running them:

```bash
gh api -X PATCH repos/<owner>/<repo> -f allow_auto_merge=true
```

Branch protection so CI and `risk-guard` must pass before auto-merge fires. `contexts` takes **check** names, which are job names, not workflow names:

- A plain job: its `jobs:` key or `name:`, e.g. `ci` (not the workflow name `CI`).
- A job that calls a reusable workflow: `<caller job> / <called job>`. For risk-guard that's **`risk-guard / check`**.

Confirm the exact names with `gh pr checks <PR>` on the setup PR. In repair mode, replace an old `risk-guard` context with `risk-guard / check`. Otherwise the old required check never reports and auto-merge stalls.

```bash
gh api -X PUT repos/<owner>/<repo>/branches/<default>/protection --input - <<'JSON'
{
  "required_status_checks": { "strict": false, "contexts": ["risk-guard / check", "<ci-job-name>"] },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
JSON
```

**Merge mode: session.** Nothing to configure. `issue-implement` waits for checks with `gh pr checks --watch` and merges in-session. Make sure `CLAUDE.md` says `Merge mode: session`.

## Done when

- [ ] Overlapping labels were kept, renamed, or deleted as the author chose.
- [ ] All 10 workflow labels exist (`gh label list`), including `article: pending` / `article: requested`.
- [ ] Every confirmed pre-existing open issue has `status: raw` (checked with `--json`, not `--label`).
- [ ] The five `.github` files exist, all three workflows are thin callers with the real `<skills-repo>`, and their YAML parses.
- [ ] Article repo: `article: devlog` / `article: intro` labels exist and `## Article conventions` is in `CLAUDE.md`.
- [ ] `CLAUDE.md` has `## Issue workflow` with merge mode set and the author's values (or `<fill in>` placeholders).
- [ ] Setup PR is open with `risk: high`.
- [ ] `risk-guard / check` ran on the setup PR and passed (`gh pr checks <PR>`).
- [ ] Merge mode auto: auto-merge enabled and branch protection set with job names (or the author has the Step 9 commands).
