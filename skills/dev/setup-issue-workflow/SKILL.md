---
name: setup-issue-workflow
description: Use when installing the AI-assisted GitHub issue workflow (raw → needs-info → ai-enhanced → approved, risk-labelled PRs) into a repo for the first time, or when repairing a repo where its labels, workflows, PR template, or CLAUDE.md `## Workflow` section are missing. Runs once per repo; creates labels, writes .github files from bundled assets, and records merge mode.
---

# setup-issue-workflow

One-time install of the issue workflow used by `issue-enhance`, `issue-implement`, and `article-handoff`.

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
| Labels | `gh label list --limit 200 --json name --jq '.[].name'` |
| `.github/workflows/issue-status.yml` | file exists? |
| `.github/workflows/risk-guard.yml` | file exists? |
| `.github/pull_request_template.md` (also `.github/PULL_REQUEST_TEMPLATE/`, root, `docs/`) | file exists? |
| `.github/low-risk-paths.txt` | file exists? |
| `CLAUDE.md` `## Workflow` section | `grep -n '^## Workflow' CLAUDE.md` |
| Existing CI check names (needed for branch protection) | `ls .github/workflows/`, job names in each file |

## Step 2 — Detect merge mode

- **Public repo** → `Merge mode: auto` (native auto-merge + branch protection).
- **Private repo** → probe branch protection:
  ```bash
  gh api repos/<owner>/<repo>/branches/<default>/protection
  ```
  - `403` with "Upgrade to GitHub Pro" → free plan, no branch protection, no native auto-merge → `Merge mode: session`.
  - `404 Branch not protected` or `200` → paid plan, protection available → `Merge mode: auto`.

## Step 3 — Show the plan and wait

List every label to create, each file to create or merge (with what will be added), the `## Workflow` keys to add, and the merge-mode result. Ask the author to confirm, and ask for the values only they know: verify command, preview URL, `Article target` (`<owner>/<repo>`, or "none"), and which paths count as low risk.

## Step 4 — Labels

`--force` makes this idempotent (it updates color/description if the label exists).

```bash
gh label create "status: raw"         --force --color ededed --description "New issue, not yet enhanced by AI"
gh label create "status: needs-info"  --force --color fbca04 --description "AI is blocked on a specific question for the author"
gh label create "status: ai-enhanced" --force --color 1d76db --description "AI-enhanced, waiting for author review"
gh label create "status: approved"    --force --color 0e8a16 --description "Approved by the author for implementation (author only)"
gh label create "risk: low"           --force --color c2e0c6 --description "PR touches only allowlisted low-risk paths; may auto-merge"
gh label create "risk: medium"        --force --color fef2c0 --description "PR needs author review before merge"
gh label create "risk: high"          --force --color b60205 --description "Auth, migrations, workflows, secrets or billing; author review required"
gh label create "article"             --force --color 5319e7 --description "Write a technical article after this ships"
```

## Step 5 — Files

Source files live in this skill's `assets/` directory.

| Asset | Target | If target exists |
|---|---|---|
| `assets/issue-status.yml` | `.github/workflows/issue-status.yml` | Diff; add the missing behaviour, keep the author's version |
| `assets/risk-guard.yml` | `.github/workflows/risk-guard.yml` | Diff; add the missing behaviour, keep the author's version |
| `assets/pull_request_template.md` | `.github/pull_request_template.md` (or the existing template's location) | Append only the sections it lacks |
| `assets/low-risk-paths.txt` | `.github/low-risk-paths.txt` | Keep; append only globs the author asked for |
| `assets/claude-md-workflow.md` | `CLAUDE.md` | No `## Workflow` → append the section. Section exists → add only missing keys. No `CLAUDE.md` → create it with just this section |

Fill `CLAUDE.md` `## Workflow` with the values from Step 3 and the merge mode from Step 2. Leave `<fill in>` for anything the author did not give.

When editing workflow YAML, keep `run:` as a block scalar (`run: |`). A plain inline string containing `"status: raw"` is invalid YAML (`: ` inside a plain scalar). Same for step `name:` values: never put `: ` in them unquoted.

Validate every YAML file you wrote or edited:

```bash
python3 -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" .github/workflows/issue-status.yml
python3 -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" .github/workflows/risk-guard.yml
```

## Step 6 — Ship the setup as a PR

The setup touches `.github/workflows`, so it is `risk: high` and the author merges it.

```bash
git switch -c chore/issue-workflow-setup
git add .github CLAUDE.md
git commit -m "Set up issue workflow (labels, status/risk-guard workflows, PR template)"
git push -u origin chore/issue-workflow-setup
gh pr create --fill --label "risk: high"
```

The `issue-status` workflow only runs once it is on the default branch.

## Step 7 — Merge settings (after the setup PR is merged)

**Merge mode: auto.** Tell the author to run these, or run them after they confirm — they change repo settings:

```bash
gh api -X PATCH repos/<owner>/<repo> -f allow_auto_merge=true
```

Branch protection so CI and `risk-guard` must pass before auto-merge fires. Put the repo's own CI job names in `contexts`:

```bash
gh api -X PUT repos/<owner>/<repo>/branches/<default>/protection --input - <<'JSON'
{
  "required_status_checks": { "strict": false, "contexts": ["risk-guard", "<ci-job-name>"] },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
JSON
```

A required check only appears in the list after it has run once, so open a test PR first if the API rejects a context.

**Merge mode: session.** Nothing to configure. `issue-implement` waits for checks with `gh pr checks --watch` and merges in-session. Make sure `CLAUDE.md` says `Merge mode: session`.

## Done when

- [ ] All 8 labels exist (`gh label list`).
- [ ] The four `.github` files exist and both YAML files parse.
- [ ] `CLAUDE.md` has `## Workflow` with merge mode set and the author's values (or `<fill in>` placeholders).
- [ ] Setup PR is open with `risk: high`.
- [ ] The author has been told the Step 7 commands for their merge mode.
