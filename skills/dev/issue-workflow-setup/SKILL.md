---
name: issue-workflow-setup
description: Use when installing the AI-assisted GitHub issue workflow (raw → needs-info → ai-enhanced → approved, risk-labelled PRs) into a repo for the first time, or when repairing / upgrading a repo where its labels, workflows, PR template, or CLAUDE.md `## Issue workflow` section are missing or outdated (e.g. full copies of the workflows instead of thin callers). Runs once per repo; creates labels, brings existing issues into the flow, writes .github callers for the shared reusable workflows, and records merge mode.
---

# issue-workflow-setup

One-time install of the issue workflow used by `issue-enhance`, `issue-implement`, `article-request`, and `post-write`.

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
| `.claude/settings.json` `permissions.deny` | file exists? which secret-file rules are already there (`python3 -c "import json;print(json.load(open('.claude/settings.json')).get('permissions',{}).get('deny',[]))"`) |
| Secret files this repo actually uses | command below the table |
| `CLAUDE.md` issue-workflow keys | second command below the table. They may sit in a top-level `## Issue workflow`, or (older installs) inside `## Workflow`, e.g. under `### Issue workflow` |
| CI **job** names (needed for branch protection) | `jobs:` keys (or each job's `name:`) in `.github/workflows/*.yml` |

```bash
# open issues that predate the workflow (no status label yet), with who opened them
gh api --paginate "repos/<owner>/<repo>/issues?state=open&per_page=100" --jq '
  .[] | select(.pull_request | not)
  | select([.labels[].name | startswith("status: ")] | any | not)
  | "#\(.number) [\(.author_association)] \(.title)"'
# where the issue-workflow keys live today (headings + key lines, with line numbers)
grep -nE '^#+ .*[Ww]orkflow|Merge mode:|Article target:|Verify command:' CLAUDE.md
# secret files in the working tree (tracked or not), for the deny rules in Step 7
find . \( -name node_modules -o -name .git \) -prune -o \
  \( -name '.env*' -o -name '.dev.vars*' -o -name '*.pem' -o -name '*.key' -o -name '*.p12' \
     -o -name '*.pfx' -o -name '*.jks' -o -name '*.keystore' -o -name 'id_rsa*' -o -name 'id_ed25519*' \
     -o -name '.netrc' -o -name '.git-credentials' -o -name '.pypirc' -o -name '.npmrc' \
     -o -name '*.tfvars' -o -name '*.tfstate*' -o -name 'kubeconfig*' -o -name 'secrets.y*ml' \
     -o -name 'credentials*.json' -o -name 'service-account*.json' \
     -o -type d -name secrets \) -print
# repair mode: open issues not opened by the owner that already carry a `status:` label
gh api --paginate "repos/<owner>/<repo>/issues?state=open&per_page=100" --jq '
  .[] | select(.pull_request | not) | select(.author_association != "OWNER")
  | select([.labels[].name | startswith("status: ")] | any)
  | "#\(.number) [\(.author_association)] \(.user.login) \([.labels[].name | select(startswith("status: "))] | join(",")) \(.title)"'
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

- Missing `external` label → add it (Step 5); open issues not opened by the owner that already carry a `status:` label (the repair-mode query in Step 1) → list them in the plan, and on the author's OK swap them to `external` (Step 6). Missing secret-file deny rules in `.claude/settings.json` → add them (Step 7).
- Old full-copy workflows → replace with callers (Step 7). Missing `needs-info-reply.yml` → add it; an existing one without an `issues: types: [edited]` trigger (check: `grep -A3 '^  issues:' .github/workflows/needs-info-reply.yml`) → add that trigger, so ticking the Pending-decisions boxes in an issue body also switches it back. Old article labels (`article`, `article: pending`, `article: devlog`, …) → migrate them to `article-status:` / `post-type:` (Step 4, before Step 5). Missing `article-pending.yml` → add it, plus the `article-status: request` / `article-status: pending` labels (Step 5).
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
- Old-name article labels to rename (Step 4 migration table), with how many issues/PRs carry each.
- GitHub's default labels to delete (Step 4): unused ones are simply listed; for ones in use, list the affected issues/PRs.
- Each overlapping existing label, with a choice per label: **keep** (leave as is), **rename** into one of the workflow labels (keeps its issues), or **delete**.
- The open issues that will get `status: raw` (Step 6): only ones opened by the owner (`author_association` `OWNER`). The author may exclude some. Issues by anyone else, collaborators included, get `external` instead.
- Each file to create or merge, and what will be added.
- The exact `permissions.deny` rules for `.claude/settings.json` (Step 7), one per line. The author confirms or edits the list before anything is written.
- **Public repo only** (`visibility` is `PUBLIC`), a reminder for the author: the `issue-assets` branch is public like the rest of the repo, so every mockup, screenshot and run output the skills post (issues, PRs, `issue-assets`) must use made-up data. Issues opened by outsiders get `external` and are never worked on by the skills (see the README's "Public repos").
- The `## Issue workflow` keys to add, and the merge-mode result.

Ask for the values only they know: verify command, preview URL, `Article target` (`<owner>/<repo>`, or "none"), and which paths count as low risk.

## Step 4 — Tidy existing labels

Do this **before** Step 5. Renaming into a name that Step 5 has already created fails because the name is taken.

**Migrate old article labels** (repo set up with an earlier version). Article progress in a project repo is now one label, `article-status: request` → `pending` → `handoff`; an article issue in the article repo carries only `post-type: <mode>`. Renaming keeps the label on every issue/PR that has it:

| Old name | New name |
|---|---|
| `article` | `article-status: request` (see the article-repo note below) |
| `article: pending` | `article-status: pending` |
| `article: requested` | `article-status: handoff` |
| `article: devlog` | `post-type: devlog` |
| `article: intro` | `post-type: intro` |
| `article: review` | `post-type: review` |
| `article: research` | `post-type: research` |
| `article-type: devlog` / `intro` / `review` / `research` (briefly used name) | `post-type: devlog` / `intro` / `review` / `research` |

**`post-type:` labels exist only in the article repo** (the repo whose `Article target` is itself). So:

- **Article repo** → rename per the table.
- **Any other repo** → don't rename the type labels (`article: devlog` / `intro` / `review` / `research`, `article-type: *`, `post-type: *`); **delete** them instead. Unused ones go straight into the plan. For ones in use, list the affected issues/PRs in Step 3 and delete after the author confirms (those cards should use `article-status: request` instead). In this case run only the first two `mv_label` lines below, then step 2 (where every `article` is progress → `article-status: request`).

```bash
for l in "article: devlog" "article: intro" "article: review" "article: research" \
         "article-type: devlog" "article-type: intro" "article-type: review" "article-type: research" \
         "post-type: devlog" "post-type: intro" "post-type: review" "post-type: research"; do
  grep -qxF "$l" <<<"$(gh label list --limit 200 --json name --jq '.[].name')" || continue
  echo "$(gh issue list --state all --label "$l" --limit 500 --json number --jq length) issues, $(gh pr list --state all --label "$l" --limit 500 --json number --jq length) PRs  $l"
done
```

1. **Rename everything except `article`** (article repo: all lines; other repos: only the two `article-status:` lines):

```bash
existing=$(gh label list --limit 200 --json name --jq '.[].name')
mv_label() {
  grep -qxF "$1" <<<"$existing" || return 0                      # old name absent: nothing to do
  if grep -qxF "$2" <<<"$existing"; then echo "BOTH exist: $1 / $2 (handle by hand)"; return; fi
  gh label edit "$1" --name "$2"
}
mv_label "article: pending"   "article-status: pending"
mv_label "article: requested" "article-status: handoff"
mv_label "article: devlog"    "post-type: devlog"
mv_label "article: intro"     "post-type: intro"
mv_label "article: review"    "post-type: review"
mv_label "article: research"  "post-type: research"
mv_label "article-type: devlog"   "post-type: devlog"
mv_label "article-type: intro"    "post-type: intro"
mv_label "article-type: review"   "post-type: review"
mv_label "article-type: research" "post-type: research"
```

2. **Then `article`.** In the article repo, `article` on an article issue is a "this is an article issue" marker, not progress. `post-type:` replaces it. Split its issues/PRs:

```bash
gh issue list --state all --label article --limit 500 --json number,labels \
  --jq '.[] | select([.labels[].name | startswith("post-type: ")] | any) | .number'   # markers
gh issue list --state all --label article --limit 500 --json number,labels \
  --jq '.[] | select([.labels[].name | startswith("post-type: ")] | any | not) | .number' # progress
gh pr list --state all --label article --limit 500 --json number --jq '.[].number'      # PRs: progress
```

- Markers → remove `article` from them (`gh issue edit <N> --remove-label article`).
- Progress items left → `mv_label "article" "article-status: request"`. Nothing left (typical for the article repo) → delete `article` (`gh label delete article --yes`); recommended there, since `post-type:` is enough.

If both an old and a new name already exist, don't rename. Add the new label to each issue/PR that has the old one, then delete the old label after the author confirms. List everything found (old labels, marker vs progress issues) in the Step 3 plan for confirmation.

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
mk "article-status: request"   5319e7 "Write an article about this after it ships"
mk "article-status: pending"   fbca04 "Merged; waiting for article-request"
mk "article-status: handoff"   0e8a16 "Handed to the article repo; done here"
mk "grill"                     d93f0b "Author asks issue-enhance to run the Grill review"
mk "external"                  d4c5f9 "Not opened by the repo owner; the owner triages it by hand"
```

`external` is added by the `issue-status` workflow to issues opened by anyone whose `author_association` isn't `OWNER` (collaborators included; bots are skipped entirely). On an organisation-owned repo, members' issues usually show as `MEMBER`, so they get `external` too; to work on one, the author opens their own issue. Those issues get no `status:` label, so `issue-enhance` and `issue-implement` never work on them. To act on one, the author opens their own issue in their own words and links the outside one. Don't put `status:` labels in issue templates: the workflow strips them from outside issues anyway.

Article progress is one label: the author adds `article-status: request` to an issue (`issue-implement` copies it to the PR); `article-pending` swaps it to `article-status: pending` when the PR merges; `article-request` swaps that to `article-status: handoff`. There is no separate `article` label.

**Article repo only** (its `Article target` is itself), also. Never create `post-type:` labels in any other repo:

```bash
mk "post-type: devlog"   d4c5f9 "Article reconstructs a decision path"
mk "post-type: intro"    c5def5 "Article introduces a tool, concept or site"
mk "post-type: review"   f9d0c4 "Article reviews a work: the author's take"
mk "post-type: research" bfdadc "Article explores a topic, reasoning kept"
```

## Step 6 — Bring existing issues into the flow

`issue-status.yml` only labels issues opened after it's installed, and `issue-enhance` only picks up `status: raw`. Label the open issues the author confirmed in Step 3:

```bash
gh issue edit <N> --add-label "status: raw"   # once per confirmed owner issue
gh issue edit <N> --add-label external        # once per issue opened by anyone else
# repair mode: a non-owner issue that already has a status label (Step 1 query), on the author's OK
gh issue edit <N> --remove-label "status: <current>" --add-label external
```

Verify with JSON and filter locally. `gh issue list --label` uses the search index, which lags right after a bulk edit and undercounts:

```bash
gh issue list --state open --limit 500 --json number,labels \
  --jq '[.[] | select([.labels[].name] | index("status: raw"))] | length'
gh issue list --state open --limit 500 --json number,labels \
  --jq '.[] | select([.labels[].name | startswith("status: ") or . == "external"] | any | not) | .number'   # should print nothing left over
```

## Step 7 — Files

Source files live in this skill's `assets/` directory.

| Asset | Target | If target exists |
|---|---|---|
| `assets/issue-status.yml` (caller) | `.github/workflows/issue-status.yml` | Old full copy → replace with the caller (repair mode). Already a caller → keep; fix `<skills-repo>` / ref if wrong |
| `assets/risk-guard.yml` (caller) | `.github/workflows/risk-guard.yml` | Same |
| `assets/article-pending.yml` (caller) | `.github/workflows/article-pending.yml` | Missing → add. Already a caller → keep; fix `<skills-repo>` / ref if wrong |
| `assets/needs-info-reply.yml` (caller) | `.github/workflows/needs-info-reply.yml` | Same; also make sure it has both triggers (`issue_comment: created` and `issues: edited`). Switches a `status: needs-info` issue back to `status: raw` (no comment) when the author replies, or ticks a box for every decision in the body's `## Pending decisions` |
| `assets/pull_request_template.md` | `.github/pull_request_template.md` (or the existing template's location) | Append only the sections it lacks |
| `assets/low-risk-paths.txt` | `.github/low-risk-paths.txt` | Keep; append only globs the author asked for |
| `assets/claude-md-workflow.md` | `CLAUDE.md` | Top-level `## Issue workflow` exists → add only missing keys. Keys only inside `## Workflow` → move them into a new top-level `## Issue workflow` and delete the old sub-section (repair mode). Neither → append the section. No `CLAUDE.md` → create it with just this section |
| `assets/claude-md-article-conventions.md` (article repo only) | `CLAUDE.md` | No `## Article conventions` → append with `<fill in>` values, then ask the author to fill them (`post-write` won't run until they do). Exists → leave it |
| Secret-file deny rules (below) | `.claude/settings.json` | Merge into `permissions.deny`; keep every other key and existing rule. No file → create it with just these rules |

In all four callers, replace `<skills-repo>` with the real `<owner>/<repo>`.

**Secret-file deny rules.** Stop Claude Code from reading secret files in this repo, so a session working on an issue can't leak them into an issue, PR or screenshot. Start from this set, then fit it to what the Step 1 `find` turned up: add a rule for any other secret file it found, and drop ones the repo has no use for. Show the final list in the Step 3 plan and write only what the author confirmed.

```text
Read(**/.env)
Read(**/.env.*)
Read(**/.envrc)
Read(**/.dev.vars)
Read(**/.dev.vars.*)
Read(**/*.pem)
Read(**/*.key)
Read(**/*.p12)
Read(**/*.pfx)
Read(**/*.jks)
Read(**/*.keystore)
Read(**/id_rsa*)
Read(**/id_ed25519*)
Read(**/.netrc)
Read(**/.git-credentials)
Read(**/.pypirc)
Read(**/*.tfvars)
Read(**/*.tfstate)
Read(**/*.tfstate.*)
Read(**/kubeconfig*)
Read(**/secrets.yml)
Read(**/secrets.yaml)
Read(**/secrets/**)
Bash(gh auth token*)
Bash(printenv*)
```

- `Read(**/.env.*)` also blocks `.env.example` / `.env.sample`. If the repo has one and sessions need it, replace that rule with the real files the `find` listed (e.g. `Read(**/.env.local)`, `Read(**/.env.production)`) and say so in the plan.
- `.npmrc` / `credentials*.json` / `service-account*.json`: add a rule only if the file holds a token or key.
- `Bash(gh auth token*)` and `Bash(printenv*)` stop the two most direct ways to print the `gh` token or the environment.
- **Limits.** These rules block Claude Code's own file tools (Claude Code's docs say Read rules also apply to Grep and Glob; not tested here). They do **not** stop a shell command such as `cat .env`, `grep -r KEY .`, or `env`, and a Bash prefix rule is easy to get around. Treat them as a guard against accidents and casual steering, not a sandbox. For a real boundary, recommend the author turn on Claude Code's sandbox for Bash (see Claude Code's sandboxing docs) in repos with secrets, and say so in the Step 3 plan.

Merge (pass the confirmed rules as arguments; existing rules and keys stay, duplicates are skipped):

```bash
python3 - "Read(**/.env)" "Read(**/.env.*)" <…confirmed rules> <<'PY'
import json, os, sys
p = ".claude/settings.json"
d = json.load(open(p)) if os.path.exists(p) else {}   # invalid JSON → this fails; show the author, don't overwrite
deny = d.setdefault("permissions", {}).setdefault("deny", [])
added = [r for r in sys.argv[1:] if r not in deny]
deny.extend(added)
os.makedirs(".claude", exist_ok=True)
with open(p, "w") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("added:", added or "nothing")
PY
```

Repair mode runs the same merge: it only adds the confirmed rules that are missing.

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
[ -f .claude/settings.json ] && git add .claude/settings.json   # only if Step 7 wrote it
git commit -m "Set up issue workflow (labels, status/risk-guard workflows, PR template, secret-file deny rules)"
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
- [ ] No old article labels remain (`article`, `article: pending`, … migrated per the Step 4 table; article-repo markers removed).
- [ ] All 12 workflow labels exist (`gh label list`), including `grill`, `external` and `article-status: request` / `pending` / `handoff`; no `article` label.
- [ ] Every confirmed pre-existing open issue by the owner has `status: raw`, and every one by anyone else has `external` and no `status:` label (checked with `--json`, not `--label`).
- [ ] `.claude/settings.json` has the secret-file `permissions.deny` rules the author confirmed, merged with whatever was there before.
- [ ] Public repo: the author was reminded that `issue-assets` is public and that posted mockups, screenshots and output use made-up data.
- [ ] `needs-info-reply.yml` triggers on both `issue_comment: created` and `issues: edited`.
- [ ] The six `.github` files exist, all four workflows (issue-status, risk-guard, article-pending, needs-info-reply) are thin callers with the real `<skills-repo>`, and their YAML parses.
- [ ] Non-article repo: no `post-type:` / `article-type:` / `article: <type>` labels left (deleted, in-use ones after confirmation).
- [ ] Article repo: the four mode labels (`post-type: devlog` / `intro` / `review` / `research`) exist and `## Article conventions` is in `CLAUDE.md`.
- [ ] `CLAUDE.md` has `## Issue workflow` with merge mode set and the author's values (or `<fill in>` placeholders).
- [ ] Setup PR is open with `risk: high`.
- [ ] `risk-guard / check` ran on the setup PR and passed (`gh pr checks <PR>`).
- [ ] Repair mode: required check swapped to `risk-guard / check` **before** the upgrade PR merged; the CLAUDE.md keys live only in a top-level `## Issue workflow`.
- [ ] Merge mode auto: auto-merge enabled and branch protection set with job names (or the author has the Step 9 commands).
