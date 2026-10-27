---
name: issue-workflow-setup
description: Use when installing the AI-assisted GitHub issue workflow (raw → needs-info → approved, risk-labelled PRs, built on the mattpocock-skills) into a repo for the first time, after `/setup-matt-pocock-skills`, or when repairing / upgrading a repo where its labels, workflows, PR template, CLAUDE.md `## Issue workflow` / `## Public repo` sections, or its kiwi notes in the agent docs are missing or outdated (e.g. full copies of the workflows instead of thin callers, or labels from before the mattpocock-skills). Runs once per repo, and again in repair mode whenever a new shared-workflow tag is released (e.g. "bump the callers to v3", "repair the issue workflow in this repo"); creates labels, brings existing issues into the flow, and writes .github callers for the shared reusable workflows. Nothing it installs merges PRs: the author merges every one.
disable-model-invocation: true
---

# issue-workflow-setup

One-time install of the issue workflow. Triage, specs, tickets and implementation come from the mattpocock-skills (`/triage`, `/to-spec`, `/to-tickets`, `/implement`, `/implement-spec`); this skill adds what they don't cover, for `issue-ship`, `article-request` and `post-write`: the shared GitHub workflows, risk labels, the PR template, and the `CLAUDE.md` sections.

The workflow logic lives once, as reusable workflows in the skills repo (`.github/workflows/issue-status.yml` and `needs-info-reply.yml`, both `on: workflow_call`). Each repo gets only short callers. `<skills-repo>` below is the `<owner>/<repo>` hosting those reusable workflows: the repo this skill came from, or the author's fork. Ask if unsure, and write it into the callers.

**Callers pin a release tag, never `@main`.** These workflows can write issues, labels and PR comments, so a repo only runs a version the author chose. Release tags are `v1`, `v2`, `v3`, … (a plain whole number, one per release) and are never moved or re-pushed once published. `<tag>` in the callers is the latest one:

```bash
gh api --paginate repos/<skills-repo>/tags --jq '.[].name' | grep -E '^v[0-9]+$' | sort -V | tail -1
```

No tag yet → stop and tell the author to tag a release in the skills repo first (README → Versions); don't fall back to `@main`.

This only pins the reusable workflows. The skills themselves (the plugin) still update from the skills repo's `main`.

**Upgrading a repo** (repair / upgrade mode): read what changed (`gh api repos/<skills-repo>/compare/<old tag>...<new tag> --jq '.commits[].commit.message'`, and the release notes), then bump the ref in both callers in one PR (it touches `.github/workflows`, so `risk: high`):

```bash
for f in .github/workflows/{issue-status,needs-info-reply}.yml; do
  [ -f "$f" ] && sed -i.bak -E 's#(uses: *[^ ]+/\.github/workflows/[a-z-]+\.yml)@[^ ]+#\1@<new tag>#' "$f" && rm "$f.bak"
done
grep -n 'uses:' .github/workflows/{issue-status,needs-info-reply}.yml   # both on <new tag>
```

A caller still on `@main` (repos set up before tags) is upgraded the same way, to the latest tag.

**Never overwrite.** Missing files are created; existing files are merged. Show the plan and get the author's OK before changing anything.

## Preconditions

```bash
gh auth status
gh repo view --json nameWithOwner,visibility,defaultBranchRef,isInOrganization \
  --jq '{repo: .nameWithOwner, visibility, default: .defaultBranchRef.name, org: .isInOrganization}'
```

Stop if `gh` is not logged in or the cwd is not a GitHub repo.

Also stop if the repo belongs to an organisation (`org` is `true`), and tell the author why: the shared workflows recognise the author by `author_association` `OWNER`, which GitHub gives only on a repo owned by a personal account. On an organisation's repo the author shows as `MEMBER` like everyone else in it, so `issue-status` would mark the author's own issues `external` and `needs-info-reply` would never switch them back. Nothing would enter the flow until the workflows can recognise the author another way.

## The mattpocock-skills setup comes first

`/setup-matt-pocock-skills` records where issues live, which labels play which triage role, and where domain docs go. Only the author can run it, so check for its output: a `## Agent skills` section in `CLAUDE.md` pointing at `issue-tracker.md`, `triage-labels.md` and `domain.md` (in `docs/agents/`, or wherever the section points).

Missing → stop and ask the author to run `/setup-matt-pocock-skills` with these answers, then run this skill again:

- Issue tracker: GitHub.
- Triage labels: not the defaults; use the mapping below, so `/triage` applies this workflow's labels instead of creating new ones.
- Domain docs: single-context (unless it's a genuine monorepo).

| Role in the mattpocock-skills | Label here |
|---|---|
| `needs-triage` | `status: raw` |
| `needs-info` | `status: needs-info` |
| `ready-for-agent` | `status: approved` |
| `ready-for-human` | `status: ready-for-human` |
| `wontfix` | `status: wontfix` |
| `bug` (category) | `type: bug` |
| `enhancement` (category) | `type: enhancement` |

The category rows aren't in the setup's template; add them to `triage-labels.md` if they're missing. In `issue-tracker.md`, make **Read an issue** and **List issues** keep only the owner's comments (filter on `authorAssociation` `OWNER`), since the template reads everyone's and on a public repo anyone can post a fake agent brief under an approved issue. Also make **List issues** list only the owner's issues and show each issue's author, and **Read an issue** flag, before the title and body, an issue that's `external` or wasn't opened by the owner (write the owner's login into the command), as in this repo's own `docs/agents/issue-tracker.md`. Repair mode adds whichever is missing. GitHub's own default names (`bug`, `enhancement`, `wontfix`) aren't used, since Step 4 deletes them.

**Where the agent docs live.** When the repo's root holds only structural files, or its whole tree is published (a notes vault, a site generator's source), move `docs/agents/` to `.claude/agent-docs/` and update the paths in `## Agent skills`. Not `.claude/agents/`: Claude Code loads every file there as a subagent definition.

## Step 1 — Inventory

Check what already exists, without changing anything:

| Item | How to check |
|---|---|
| Labels | `gh label list --limit 200 --json name,description` |
| Existing labels that overlap in meaning (e.g. `ai-review`, `needs-info`, `approved`, `low-risk`) | read the label list above |
| Open issues with no `status: ` label | command below the table |
| `.github/workflows/issue-status.yml` | exists? caller or old full copy? (see "Recognising an old full copy" below) |
| `.github/workflows/risk-guard.yml` | exists? Retired in v3 (nothing merges automatically any more); repair mode removes it |
| `.github/workflows/article-pending.yml` | exists? Retired in v4 (articles start with `/article-request`); repair mode removes it |
| `.github/workflows/needs-info-reply.yml` | exists? (same) |
| Is this the article repo? | `Article target` in `## Issue workflow` equals this repo (new install: ask in Step 3) |
| `CLAUDE.md` `## Article conventions` (article repo only) | `grep -n '^## Article conventions' CLAUDE.md` |
| `.github/pull_request_template.md` (also `.github/PULL_REQUEST_TEMPLATE/`, root, `docs/`) | file exists? |
| `.github/low-risk-paths.txt` | exists? It's unused since v3 (no allowlist); repair mode deletes it |
| `.claude/settings.json` `permissions.deny` | file exists? which secret-file rules are already there (`python3 -c "import json;print(json.load(open('.claude/settings.json')).get('permissions',{}).get('deny',[]))"`) |
| Secret files this repo actually uses | command below the table |
| `CLAUDE.md` `## Agent skills`, and the files it points at | exists? `triage-labels.md` maps to the labels in the table above? `issue-tracker.md` has the `## This repo's workflow` section (`assets/agents-issue-tracker.md`)? |
| `issue-tracker.md` **Read an issue** / **List issues** | keep only the owner's comments (`authorAssociation == "OWNER"`) and leave out `external` issues? The `## This repo's workflow` section promises both, so check the commands, not just the section |
| `CLAUDE.md` `## Public repo` (public repos only) | exists? |
| `CLAUDE.md` issue-workflow keys | second command below the table. They may sit in a top-level `## Issue workflow`, or (older installs) inside `## Workflow`, e.g. under `### Issue workflow` |

```bash
# open issues that predate the workflow (no status label yet), with who opened them
gh api --paginate "repos/<owner>/<repo>/issues?state=open&per_page=100" --jq '
  .[] | select(.pull_request | not)
  | select([.labels[].name | startswith("status: ")] | any | not)
  | "#\(.number) [\(.author_association)] \(.title)"'
# where the issue-workflow keys live today (headings + key lines, with line numbers)
grep -nE '^#+ .*[Ww]orkflow|Merge mode:|Article target:|Verify command:' CLAUDE.md   # Merge mode is a v1–v2 key
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
for f in .github/workflows/{issue-status,needs-info-reply}.yml; do
  [ -f "$f" ] || { echo "missing  $f"; continue; }
  if grep -qE 'uses: *[^ ]+/\.github/workflows/' "$f" && ! grep -q 'steps:' "$f"; then echo "caller   $f"
  elif grep -q 'runs-on:' "$f"; then echo "OLD COPY $f"
  else echo "unknown  $f (show the author)"; fi
done
```

**Repair / upgrade mode.** For an already-set-up repo, plan:

- Callers on `@main`, or on an older tag than the latest → bump both to the latest tag ("Upgrading a repo" above), after showing the author the compare output.

- **Leftovers from before the mattpocock-skills** (v1–v2 installs):
  - Open issues with `status: ai-enhanced` → list them in the plan and, on the author's OK, swap them to `status: raw`; then delete the `status: ai-enhanced` and `grill` labels. Both happen in Step 6, in that order: deleting a label first would lose which issues had it.
  - Missing `status: ready-for-human`, `status: wontfix`, `type: bug`, `type: enhancement` → add them (Step 5).
  - Old descriptions on `status: raw` ("…not yet enhanced by AI"), `risk: low` ("…allowlisted low-risk paths…" or "…may auto-merge"), `risk: medium` ("PR needs author review before merge") and `risk: high` ("Auth, migrations, …" or "…author review required") → update them to Step 5's, on the author's OK. This is the one place a description changes.
  - `## Issue workflow`: replace its first two lines with the asset's, and remove the `Issue assets branch`, `Mockup path`, `Low-risk paths` and `Merge mode` keys (the `issue-assets` branch itself stays).
  - `kiwi-voice` anywhere in `CLAUDE.md` (e.g. `## Article conventions`) → `writing-voice`, the skill's new name.
  - **The `risk-guard` merge gate is retired** (from v3 the author merges every PR). In this order, since a required check that no longer runs blocks every PR: delete `.github/workflows/risk-guard.yml` and `.github/low-risk-paths.txt` in the upgrade PR, and remove `risk-guard / check` (or an older `risk-guard`) from the default branch's required checks (Step 9) before that PR is merged. In Step 9, whether or not the check is required: switch off the repo's "Allow auto-merge" setting (skip only if the author says no: an older skill version still installed somewhere could otherwise queue a merge once nothing gates it), and turn auto-merge off on every open PR still queued for it (from v2's `risk: low` flow).
  - **The `article-pending` workflow and the `article-status:` labels are retired** (from v4 an article starts with `/article-request`). Delete the caller in the upgrade PR, and the labels in Step 4 after listing the items that still carry `article-status: request` / `pending` (`references/old-article-labels.md`). In `CLAUDE.md`, replace any sentence that describes `article-status:` labels, `article-pending`, or a `## 文章素材` section written into PRs with the new flow (the author runs `/article-request` in the session that did the work); keep `Article target`, which `/article-request` reads.
- Missing `## Public repo` section on a public repo, or the `## This repo's workflow` section in `issue-tracker.md` → add them (Step 7).
- Missing `external` label → add it (Step 5); open issues not opened by the owner that already carry a `status:` label (the repair-mode query in Step 1) → list them in the plan, and on the author's OK swap them to `external` (Step 6). Missing secret-file deny rules in `.claude/settings.json` → add them (Step 7).
- Old full-copy workflows → replace with callers (Step 7). Missing `needs-info-reply.yml` → add it; an existing one without an `issues: types: [edited]` trigger (check: `grep -A3 '^  issues:' .github/workflows/needs-info-reply.yml`) → add that trigger, so ticking the boxes of an older issue's `## Pending decisions` also switches it back. Old article labels (`article`, `article: pending`, `article-status: *`, `article: devlog`, …) → delete or migrate them (Step 4, before Step 5).
- **Old CLAUDE.md layout.** If the issue-workflow keys (`Verify command`, `Article target`, …) sit inside `## Workflow` (e.g. under `### Issue workflow`), **move** them: create a top-level `## Issue workflow` from `assets/claude-md-workflow.md` with the existing values (dropping the retired keys listed above), then delete the old sub-section. Never add a second copy beside it. Leave the rest of `## Workflow` (local dev commands) untouched.
## Step 2 — Required checks

Read the default branch's required status checks (`gh api repos/<owner>/<repo>/branches/<default>/protection --jq '.required_status_checks.contexts'`; a `403` or `404` means there's no protection to read). If `risk-guard / check` or `risk-guard` is among them, plan to remove it (Step 9). Leave every other check and rule as it is.

## Step 3 — Show the plan and wait

List, and ask the author to confirm:

- Every label to create (only the missing ones; existing labels keep their color and description).
- Old article labels to delete or rename (`references/old-article-labels.md`), with how many issues/PRs carry each, and the items still waiting for an article.
- GitHub's default labels to delete (Step 4): unused ones are simply listed; for ones in use, list the affected issues/PRs.
- Each overlapping existing label, with a choice per label: **keep** (leave as is), **rename** into one of the workflow labels (keeps its issues), or **delete**.
- The open issues that will get `status: raw` (Step 6): only ones opened by the owner (`author_association` `OWNER`). The author may exclude some. Issues by anyone else, collaborators included, get `external` instead.
- Each file to create or merge, and what will be added.
- The exact `permissions.deny` rules for `.claude/settings.json` (Step 7), one per line. The author confirms or edits the list before anything is written.
- **Public repo only** (`visibility` is `PUBLIC`): the `## Public repo` section for `CLAUDE.md` (Step 7). Every skill, the mattpocock-skills included, reads `CLAUDE.md`, so this is where the rules about outsiders' text, security details and made-up data live.
- The `## Issue workflow` keys to add.
- Repo settings (Step 9), repair mode on a repo set up before v3: switching off "Allow auto-merge", turning auto-merge off on the open PRs still queued for it (list them), and removing `risk-guard` from the required checks if Step 2 found it there.

Ask for the values only they know: verify command, preview URL, `Article target` (`<owner>/<repo>`, or "none").

## Step 4 — Tidy existing labels

Do this **before** Step 5. Renaming into a name that Step 5 has already created fails because the name is taken.

**Old article labels** (repo set up with an earlier version, e.g. `article`, `article: pending`, `article-type: devlog`): delete or migrate them as `references/old-article-labels.md` says. There are no article progress labels any more, and `post-type:` labels exist only in the article repo.

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
mk "status: raw"         ededed "New issue, not yet triaged"
mk "status: needs-info"  fbca04 "AI is blocked on a specific question for the author"
mk "status: approved"    0e8a16 "Approved by the author; ready for an agent"
mk "status: ready-for-human" c5def5 "Specified, but needs a human to do it"
mk "status: wontfix"     ffffff "Will not be actioned"
mk "type: bug"           d73a4a "Something is broken"
mk "type: enhancement"   a2eeef "New feature or improvement"
mk "risk: low"           c2e0c6 "Two-way door and a clean review; a light read before merging"
mk "risk: medium"        fef2c0 "Read the change before merging"
mk "risk: high"          b60205 "One-way door or cross-repo blast radius; read closely before merging"
mk "external"                  d4c5f9 "Not opened by the repo owner; the owner triages it by hand"
```

`external` is added by the `issue-status` workflow to issues opened by anyone whose `author_association` isn't `OWNER` (collaborators included; bots are skipped entirely). That is why the skill only installs into a repo owned by a personal account (Preconditions). Those issues get no `status:` label, and the `## Public repo` section in `CLAUDE.md` keeps every skill off them. To act on one, the author opens their own issue in their own words and links the outside one. Don't put `status:` labels in issue templates: the workflow strips them from outside issues anyway.

There are no article progress labels: an article starts when the author runs `/article-request`, best in the session where the work happened.

**Article repo only** (its `Article target` is itself), also. Never create `post-type:` labels in any other repo:

```bash
mk "post-type: devlog"   d4c5f9 "Article reconstructs a decision path"
mk "post-type: intro"    c5def5 "Article introduces a tool, concept or site"
mk "post-type: review"   f9d0c4 "Article reviews a work: the author's take"
mk "post-type: research" bfdadc "Article explores a topic, reasoning kept"
```

## Step 6 — Bring existing issues into the flow

`issue-status.yml` only labels issues opened after it's installed, and `/triage` looks for `status: raw`. Label the open issues the author confirmed in Step 3:

```bash
gh issue edit <N> --add-label "status: raw"   # once per confirmed owner issue
gh issue edit <N> --add-label external        # once per issue opened by anyone else
# repair mode: a non-owner issue that already has a status label (Step 1 query), on the author's OK
gh issue edit <N> --remove-label "status: <current>" --add-label external
# repair mode: an issue still on status: ai-enhanced, on the author's OK
gh issue edit <N> --remove-label "status: ai-enhanced" --add-label "status: raw"
# repair mode: then the old labels themselves, once no open issue still needs moving
gh label delete "status: ai-enhanced" --yes
gh label delete grill --yes
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
| `assets/issue-status.yml` (caller) | `.github/workflows/issue-status.yml` | Old full copy → replace with the caller (repair mode). Already a caller → keep; fix `<skills-repo>` if wrong; `@main` or an older tag → the latest tag |
| `assets/needs-info-reply.yml` (caller) | `.github/workflows/needs-info-reply.yml` | Same; also make sure it has both triggers (`issue_comment: created` and `issues: edited`). Switches a `status: needs-info` issue back to `status: raw` (no comment) when the author replies, or ticks a box for every decision in the body's `## Pending decisions` |
| `assets/pull_request_template.md` | `.github/pull_request_template.md` (or the existing template's location) | Append only the sections it lacks. Repair mode: replace the retired sections (`## Behaviour summary`, `## Deviations from the approved plan`, and the old `## Review` comment that names `issue-implement`) with the asset's, in the asset's order |
| `assets/claude-md-workflow.md` | `CLAUDE.md` | Top-level `## Issue workflow` exists → add only missing keys. Keys only inside `## Workflow` → move them into a new top-level `## Issue workflow` and delete the old sub-section (repair mode). Neither → append the section. No `CLAUDE.md` → create it with just this section |
| `assets/claude-md-public-repo.md` (public repo only) | `CLAUDE.md` | No `## Public repo` → append it. Exists → add only the rules it lacks |
| `assets/agents-issue-tracker.md` | `issue-tracker.md` (path from `## Agent skills`) | No `## This repo's workflow` section → append it. Exists → leave it |
| The mapping table above | `triage-labels.md` (path from `## Agent skills`) | Fix rows that point at other labels; add the two category rows if missing |
| `assets/claude-md-article-conventions.md` (article repo only) | `CLAUDE.md` | No `## Article conventions` → append with `<fill in>` values, then ask the author to fill them (`post-write` won't run until they do). Exists → leave it |
| Secret-file deny rules (below) | `.claude/settings.json` | Merge into `permissions.deny`; keep every other key and existing rule. No file → create it with just these rules |

In both callers, replace `<skills-repo>` with the real `<owner>/<repo>` and `<tag>` with the latest release tag (top of this file).

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
- **Public repo:** `.claude/settings.json` is committed, so anyone can read the rules. Write every rule as a pattern by file type (`Read(**/*.p12)`, `Read(**/.npmrc)`), never a path the `find` turned up, so the rules don't list which secret files this repo keeps or where. For the `.env.example` case above, use the common variants (`Read(**/.env.local)`, `Read(**/.env.development)`, `Read(**/.env.production)`, `Read(**/.env.test)`, `Read(**/.env.*.local)`) instead of the ones found. The found files appear only in the Step 3 plan the author reads in the session, not in the commit or the PR.
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

Fill `CLAUDE.md` `## Issue workflow` with the values from Step 3. Leave `<fill in>` for anything the author did not give.

When editing workflow YAML, keep `run:` as a block scalar (`run: |`). A plain inline string containing `"status: raw"` is invalid YAML (`: ` inside a plain scalar). Same for step `name:` values: never put `: ` in them unquoted.

Validate every YAML file you wrote or edited:

```bash
python3 -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" .github/workflows/issue-status.yml
python3 -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" .github/workflows/needs-info-reply.yml
```

## Step 8 — Ship the setup as a PR

The setup touches `.github/workflows`, so it is `risk: high` and the author merges it.

Branch: if you're already on a non-default branch (e.g. a worktree session's branch), use it. Only when on the default branch, create one:

```bash
[ "$(git branch --show-current)" = "<default>" ] && git switch -c chore/issue-workflow-setup
git add .github CLAUDE.md <agent docs folder from ## Agent skills>
[ -f .claude/settings.json ] && git add .claude/settings.json   # only if Step 7 wrote it
git commit -m "Set up issue workflow (labels, shared workflow callers, PR template, secret-file deny rules)"
git push -u origin HEAD
gh pr create --fill --label "risk: high"
```

The `issue-status` workflow only runs once it is on the default branch. If the skills repo is private, its reusable workflows can only be called after its Settings → Actions → Access allows this repo.

## Step 9 — Repo settings (repair mode)

Only for a repo set up before v3, and every change here is the author's to do or approve.

**Auto-merge.** Turn auto-merge off on every open PR still queued for it, then switch off "Allow auto-merge" (unless the author said no), then list again:

```bash
gh pr list --state open --limit 1000 --json number,title,autoMergeRequest --jq '.[] | select(.autoMergeRequest) | "#\(.number) \(.title)"'
gh pr merge <N> --disable-auto                                         # for each one listed
gh api -X PATCH repos/<owner>/<repo> -f allow_auto_merge=false        # unless the author said no
```

**Required check.** Only when Step 2 found `risk-guard / check` (or `risk-guard`) among the required checks. Remove just that context and keep every other check and rule. Do it before the upgrade PR (Step 8) is merged: that PR deletes the caller, so it would wait forever on a check that no longer runs.

```bash
gh api repos/<owner>/<repo>/branches/<default>/protection/required_status_checks --jq .contexts
gh api -X PATCH repos/<owner>/<repo>/branches/<default>/protection/required_status_checks --input - <<'JSON'
{ "contexts": ["<the existing contexts, without risk-guard>"] }
JSON
```

Then run the `gh pr list` above once more and turn off any PR it still shows, in case one was queued in between.

Nothing else in branch protection is set up by this skill. The author merges every PR, so required checks are only the repo's own CI, which the author manages.

## Done when

- [ ] Overlapping labels were kept, renamed, or deleted as the author chose.
- [ ] GitHub's default labels are gone (in-use ones only after the author confirmed the affected issues/PRs); bot labels such as `dependencies` are kept.
- [ ] No existing label's color or description was changed (no `--force`).
- [ ] No old article labels remain (`article`, `article: pending`, … migrated per `references/old-article-labels.md`; article-repo markers removed).
- [ ] All 11 workflow labels exist (`gh label list`): five `status:`, two `type:`, three `risk:`, and `external`; no `article`, `article-status:`, `status: ai-enhanced` or `grill` label.
- [ ] Every confirmed pre-existing open issue by the owner has `status: raw`, and every one by anyone else has `external` and no `status:` label (checked with `--json`, not `--label`).
- [ ] `.claude/settings.json` has the secret-file `permissions.deny` rules the author confirmed, merged with whatever was there before.
- [ ] The mattpocock-skills setup ran first: `## Agent skills` points at the agent docs, `triage-labels.md` maps to this workflow's labels (category rows included), and `issue-tracker.md` has `## This repo's workflow`.
- [ ] Public repo: `CLAUDE.md` has `## Public repo`.
- [ ] `needs-info-reply.yml` triggers on both `issue_comment: created` and `issues: edited`.
- [ ] The `.github` files exist, both workflows (issue-status, needs-info-reply) are thin callers with the real `<skills-repo>` on the latest release tag (no `@main`), and their YAML parses.
- [ ] No `risk-guard` left: not in the required checks (removed first), and no caller or `.github/low-risk-paths.txt`. No `article-pending` caller.
- [ ] Non-article repo: no `post-type:` / `article-type:` / `article: <type>` labels left (deleted, in-use ones after confirmation).
- [ ] Article repo: the four mode labels (`post-type: devlog` / `intro` / `review` / `research`) exist and `## Article conventions` is in `CLAUDE.md`.
- [ ] `CLAUDE.md` has `## Issue workflow` with the author's values (or `<fill in>` placeholders), and no `Merge mode` key.
- [ ] Setup PR is open with `risk: high`.
- [ ] Repair mode: the CLAUDE.md keys live only in a top-level `## Issue workflow`.
- [ ] Public repo: the deny rules in `.claude/settings.json` are patterns by file type, with no path taken from the `find`.
