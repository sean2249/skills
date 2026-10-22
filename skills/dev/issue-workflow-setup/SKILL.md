---
name: issue-workflow-setup
description: Use when installing the AI-assisted GitHub issue workflow (raw → needs-info → ai-enhanced → approved, risk-labelled PRs) into a repo for the first time, or when repairing / upgrading a repo where its labels, workflows, PR template, or CLAUDE.md `## Issue workflow` section are missing or outdated (e.g. full copies of the workflows instead of thin callers). Runs once per repo; creates labels, brings existing issues into the flow, writes .github callers for the shared reusable workflows, and records merge mode.
---

# issue-workflow-setup

One-time install of the issue workflow used by `issue-enhance`, `issue-implement`, `article-request`, and `article-write`.

The workflow logic lives once, as reusable workflows in the skills repo (`.github/workflows/issue-status.yml`, `risk-guard.yml`, `article-pending.yml`, and `needs-info-reply.yml`, all `on: workflow_call`). Each repo gets only short callers, so fixes ship to every repo without re-running setup. `<skills-repo>` below is the `<owner>/<repo>` hosting those reusable workflows: the repo this skill came from, or the author's fork. Ask if unsure, and write it into the callers.

**Callers pin `@main` by default.** The upside: change the skills repo once and every repo picks it up on its next run. The cost: these workflows can write issues, labels, and PR comments, so a mistake on the skills repo's `main` hits every repo at once. To lock a repo to a known version instead, change the ref in its callers:

- `uses: <skills-repo>/.github/workflows/risk-guard.yml@v1` (a tag), or `@<full commit sha>` (immutable; safest).
- To upgrade a locked repo: read the skills repo's changes since that ref (`gh api repos/<skills-repo>/compare/<old>...<new>`), then bump the ref in all four callers in one PR (it touches `.github/workflows`, so `risk: high`).

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
| `.github/workflows/issue-status.yml` | exists? caller or old full copy? (see "Recognising an old full copy" below) |
| `.github/workflows/risk-guard.yml` | same |
| `.github/workflows/article-pending.yml` | exists? (repos set up before it existed won't have it) |
| `.github/workflows/needs-info-reply.yml` | exists? (same) |
| Branch protection contexts | `gh api repos/<owner>/<repo>/branches/<default>/protection --jq '.required_status_checks.contexts'` |
| Is this the article repo? | `Article target` in `## Issue workflow` equals this repo (new install: ask in Step 3) |
| `CLAUDE.md` `## Article conventions` (article repo only) | `grep -n '^## Article conventions' CLAUDE.md` |
| `.github/pull_request_template.md` (also `.github/PULL_REQUEST_TEMPLATE/`, root, `docs/`) | file exists? |
| `.github/low-risk-paths.txt` | file exists? |
| `CLAUDE.md` issue-workflow keys | second command below the table. They may sit in a top-level `## Issue workflow`, or (older installs) inside `## Workflow`, e.g. under `### Issue workflow` |
| CI **job** names (needed for branch protection) | `jobs:` keys (or each job's `name:`) in `.github/workflows/*.yml` |

```bash
# open issues that predate the workflow (no status label yet)
gh issue list --state open --limit 500 --json number,title,labels \
  --jq '.[] | select([.labels[].name | startswith("status: ")] | any | not) | "#\(.number) \(.title)"'
# where the issue-workflow keys live today (headings + key lines, with line numbers)
grep -nE '^#+ .*[Ww]orkflow|Merge mode:|Article target:|Verify command:' CLAUDE.md
```

The section is `## Issue workflow`, not `## Workflow`: many repos already use `## Workflow` for local dev commands. Leave that one alone.

**Recognising an old full copy.** Judge by content, not by diffing against an old template (old asset paths no longer exist). A workflow file is an old full copy when it has `runs-on:` / `steps:` and no `uses: <anything>/skills/.github/workflows/` line (or `uses: <skills-repo>/.github/workflows/`). A thin caller has a `uses:` line pointing at the skills repo and no `steps:`. If an old copy has obvious local edits (extra steps, changed triggers), show them to the author and ask before replacing.

```bash
for f in .github/workflows/{issue-status,risk-guard,article-pending,needs-info-reply}.yml; do
  [ -f "$f" ] || { echo "missing  $f"; continue; }
  if grep -qE 'uses: *[^ ]+/\.github/workflows/' "$f" && ! grep -q 'steps:' "$f"; then echo "caller   $f"
  elif grep -q 'runs-on:' "$f"; then echo "OLD COPY $f"
  else echo "unknown  $f (show the author)"; fi
done
```

**Repair / upgrade mode.** For an already-set-up repo, plan:

- Old full-copy workflows → replace with callers (Step 7). Missing `needs-info-reply.yml` → add it. Missing `article-pending.yml` → add it, plus the `article: pending` / `article: requested` labels (Step 5).
- **Old CLAUDE.md layout.** If the issue-workflow keys (`Verify command`, `Merge mode`, `Article target`, …) sit inside `## Workflow` (e.g. under `### Issue workflow`), **move** them: create a top-level `## Issue workflow` from `assets/claude-md-workflow.md` with the existing values, then delete the old sub-section. Never add a second copy beside it. Leave the rest of `## Workflow` (local dev commands) untouched.
- **Required check rename**, in this order (Step 9). Reversing it leaves the upgrade PR waiting forever on the old `risk-guard` check, and auto-merge stalls with it:
  1. Open the upgrade PR (Step 8).
  2. Wait until `risk-guard / check` has run on it (`gh pr checks <PR>`).
  3. Swap the required check from `risk-guard` to `risk-guard / check` in branch protection.
  4. Only then merge the upgrade PR.

Everything else follows the usual merge-only rules.

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

- Every label to create (only the missing ones; existing labels keep their color and description).
- GitHub's default labels to delete (Step 4): unused ones are simply listed; for ones in use, list the affected issues/PRs.
- Each overlapping existing label, with a choice per label: **keep** (leave as is), **rename** into one of the workflow labels (keeps its issues), or **delete**.
- The open issues that will get `status: raw` (Step 6). The author may exclude some.
- Each file to create or merge, and what will be added.
- The `## Issue workflow` keys to add, and the merge-mode result.

Ask for the values only they know: verify command, preview URL, `Article target` (`<owner>/<repo>`, or "none"), and which paths count as low risk.

## Step 4 — Tidy existing labels

Do this **before** Step 5. Renaming into a name that Step 5 has already created fails because the name is taken.

**Overlapping labels** (the author's keep / rename / delete choice from Step 3):

```bash
# rename: the label and all its issues move to the workflow name
gh label edit "<old-name>" --name "<workflow label>"
# delete: only on the author's explicit choice in Step 3
gh label delete "<old-name>" --yes
```

**GitHub's default labels are deleted:** `bug`, `documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`. Labels that bots apply automatically, such as dependabot's `dependencies`, `github_actions`, `javascript`, are **not** defaults; keep them. Check usage first (issues and PRs, open and closed):

```bash
for l in bug documentation duplicate enhancement "good first issue" "help wanted" invalid question wontfix; do
  gh label list --limit 200 --json name --jq '.[].name' | grep -qxF "$l" || continue
  n=$(( $(gh issue list --state all --label "$l" --limit 500 --json number --jq length) \
      + $(gh pr list --state all --label "$l" --limit 500 --json number --jq length) ))
  echo "$n  $l"
done
```

- `0` → in the Step 3 plan as "delete".
- `> 0` → in the Step 3 plan with the affected issues/PRs listed (`gh issue list --state all --label "<l>"`, `gh pr list --state all --label "<l>"`); delete after the author confirms. Deleting a label removes it from those issues/PRs.

```bash
gh label delete "<default label>" --yes
```

## Step 5 — Labels

Create **only the missing** labels. Don't pass `--force`: on an existing label it overwrites the author's color and description (e.g. a description written in another language). Existing labels, including ones just renamed in Step 4, stay as they are.

```bash
existing=$(gh label list --limit 200 --json name --jq '.[].name')
mk() { grep -qxF "$1" <<<"$existing" || gh label create "$1" --color "$2" --description "$3"; }
mk "status: raw"         ededed "New issue, not yet enhanced by AI"
mk "status: needs-info"  fbca04 "AI is blocked on a specific question for the author"
mk "status: ai-enhanced" 1d76db "AI-enhanced, waiting for author review"
mk "status: approved"    0e8a16 "Approved by the author for implementation (author only)"
mk "risk: low"           c2e0c6 "PR touches only allowlisted low-risk paths; may auto-merge"
mk "risk: medium"        fef2c0 "PR needs author review before merge"
mk "risk: high"          b60205 "Auth, migrations, workflows, secrets or billing; author review required"
mk "article"             5319e7 "Write a technical article after this ships"
mk "article: pending"    fbca04 "Merged article PR; article-request not run yet"
mk "article: requested"  0e8a16 "Article request opened in the article repo"
```

`article-pending` adds `article: pending` when an `article` PR merges; `article-request` swaps it for `article: requested`.

**Article repo only** (its `Article target` is itself), also:

```bash
mk "article: devlog"   d4c5f9 "Article reconstructs a decision path"
mk "article: intro"    c5def5 "Article introduces a tool, concept or site"
mk "article: review"   f9d0c4 "Article reviews a work: the author's take"
mk "article: research" bfdadc "Article explores a topic, reasoning kept"
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
| `assets/needs-info-reply.yml` (caller) | `.github/workflows/needs-info-reply.yml` | Same. On an author's reply to a `status: needs-info` issue, switches it back to `status: raw` (no comment) |
| `assets/pull_request_template.md` | `.github/pull_request_template.md` (or the existing template's location) | Append only the sections it lacks |
| `assets/low-risk-paths.txt` | `.github/low-risk-paths.txt` | Keep; append only globs the author asked for |
| `assets/claude-md-workflow.md` | `CLAUDE.md` | Top-level `## Issue workflow` exists → add only missing keys. Keys only inside `## Workflow` → move them into a new top-level `## Issue workflow` and delete the old sub-section (repair mode). Neither → append the section. No `CLAUDE.md` → create it with just this section |
| `assets/claude-md-article-conventions.md` (article repo only) | `CLAUDE.md` | No `## Article conventions` → append with `<fill in>` values, then ask the author to fill them (`article-write` won't run until they do). Exists → leave it |

In all four callers, replace `<skills-repo>` with the real `<owner>/<repo>`.

`low-risk-paths.txt`: keep the header comment, and replace the example globs below it with the author's list from Step 3.

Fill `CLAUDE.md` `## Issue workflow` with the values from Step 3 and the merge mode from Step 2. Leave `<fill in>` for anything the author did not give.

When editing workflow YAML, keep `run:` as a block scalar (`run: |`). A plain inline string containing `"status: raw"` is invalid YAML (`: ` inside a plain scalar). Same for step `name:` values: never put `: ` in them unquoted.

Validate every YAML file you wrote or edited:

```bash
python3 -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" .github/workflows/issue-status.yml
python3 -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" .github/workflows/risk-guard.yml
python3 -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" .github/workflows/article-pending.yml
python3 -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" .github/workflows/needs-info-reply.yml
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

**risk-guard runs twice on a new PR** when it's opened with a label (`opened` + `labeled`). The caller queues the second run behind the first (`cancel-in-progress: false`) instead of cancelling it, so the usual open-with-label case sends no "run cancelled" email, and the last run, which sees the labels, sets the check. GitHub keeps at most one queued run per group, so a third event arriving while one run is queued still cancels that queued run. This is rare (e.g. a push right after opening), and the newest run still decides the check. Dropping `opened` from the triggers would avoid the duplicate, but then a PR opened without a label never reports `risk-guard / check` and stays blocked on the required check. A repo whose caller still has `cancel-in-progress: true` will occasionally email about a cancelled run. That's expected and harmless; switch it to `false` in repair mode.

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

Confirm the exact names with `gh pr checks <PR>` on the setup PR.

**Repair mode:** swap only the contexts, keeping the rest of the protection as is. Do it after `risk-guard / check` has shown up on the upgrade PR, and before merging that PR:

```bash
gh api repos/<owner>/<repo>/branches/<default>/protection/required_status_checks --jq .contexts
gh api -X PATCH repos/<owner>/<repo>/branches/<default>/protection/required_status_checks --input - <<'JSON'
{ "contexts": ["risk-guard / check", "<other existing contexts>"] }
JSON
```

**New install:**

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
- [ ] GitHub's default labels are gone (in-use ones only after the author confirmed the affected issues/PRs); bot labels such as `dependencies` are kept.
- [ ] No existing label's color or description was changed (no `--force`).
- [ ] All 10 workflow labels exist (`gh label list`), including `article: pending` / `article: requested`.
- [ ] Every confirmed pre-existing open issue has `status: raw` (checked with `--json`, not `--label`).
- [ ] The six `.github` files exist, all four workflows (issue-status, risk-guard, article-pending, needs-info-reply) are thin callers with the real `<skills-repo>`, and their YAML parses.
- [ ] Article repo: the four mode labels (`article: devlog` / `intro` / `review` / `research`) exist and `## Article conventions` is in `CLAUDE.md`.
- [ ] `CLAUDE.md` has `## Issue workflow` with merge mode set and the author's values (or `<fill in>` placeholders).
- [ ] Setup PR is open with `risk: high`.
- [ ] `risk-guard / check` ran on the setup PR and passed (`gh pr checks <PR>`).
- [ ] Repair mode: required check swapped to `risk-guard / check` **before** the upgrade PR merged; the CLAUDE.md keys live only in a top-level `## Issue workflow`.
- [ ] Merge mode auto: auto-merge enabled and branch protection set with job names (or the author has the Step 9 commands).
