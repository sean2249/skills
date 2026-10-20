---
name: issue-implement
description: Use when implementing a GitHub issue labelled `status: approved` — branch, implement, run the repo's verify command, open a PR with per-criterion evidence, classify risk (low / medium / high), and merge only `risk: low` PRs. Refuses issues in any other status.
---

# issue-implement

Implements one approved issue end to end. Requires the repo to have been set up with `setup-issue-workflow`.

## Step 0 — Gate

```bash
gh issue view <N> --json number,title,body,labels,state,comments
```

Refuse and explain if any of these hold:

| Condition | Say |
|---|---|
| Issue is closed | It's closed; nothing to implement. |
| No `status: approved` label | Current status is `<label>`; only the author can approve. Suggest `issue-enhance` for `raw` / `needs-info`, or author review for `ai-enhanced`. |
| Body says `Blocked by #M` and #M is open | Blocked by #M; implement that first. |
| Issue is an overview (has a `## Slices` checklist, no acceptance criteria) | Implement the child issues instead. |

Never add `status: approved` yourself, even if asked.

Every comment you post on the PR or the issue starts with the line `🤖 AI <YYYY-MM-DD>`. The AI posts with the author's `gh` login, so GitHub's author field can't tell AI from author; only this marker can. Implement from the issue body (the author's text plus the AI plan section), not from comments.

Read `CLAUDE.md` `## Workflow`: verify command, preview URL, low-risk paths file, merge mode.

## Step 1 — Branch

```bash
git fetch origin
git switch -c issue-<N>-<short-slug> origin/<default-branch>
```

## Step 2 — Implement

Follow the issue's **Approach** and **Acceptance criteria**. When you must deviate from the approved plan, note what and why as you go; it goes in the PR.

## Step 3 — Verify

Run the verify command from `CLAUDE.md` and any checks listed under the issue's **Verification**. Keep the output; it is the evidence. Check the preview URL when one is configured. Anything you could not verify, write down.

## Step 4 — Classify risk

```bash
git diff --name-only origin/<default-branch>...HEAD
```

Apply in order; the first match wins:

1. **`risk: high`** if any file touches auth, database migrations, `.github/workflows/`, secrets/credentials, or billing/payments.
2. **`risk: low`** if every file matches a glob in `.github/low-risk-paths.txt` and none is under `.github/` (`*` stays in one directory, `**` crosses directories, trailing `/` = whole directory). The `risk-guard` workflow enforces the same rule on the PR.
3. **`risk: medium`** otherwise.

## Step 5 — Open the PR

Fill the repo's PR template:

- `Closes #<N>`.
- **Behaviour summary** (first section; the author reads this to decide whether to let it through, before looking at the diff):
  - Run output: what running the change actually prints or shows (command + output excerpt, or screenshot).
  - What it does: one short paragraph.
  - What it deliberately doesn't do: one short paragraph.
  - Mapped to acceptance criteria: one line per criterion → the part of the behaviour that meets it.
- **Acceptance criteria — evidence**: every criterion from the issue, word for word, each with its evidence (command + output excerpt, screenshot, preview link).
- **Not verified**: say plainly what wasn't checked and why.
- **Deviations from the approved plan**: each with its reason, or "None".
- **Risk**: level and reason.

If the issue has the `article` label, add a `## 文章素材` section **now, in this session**. The article-writing session can't see this conversation:

- Background: why this work happened.
- The author's own words from this session at each decision point (quote them).
- Approach taken.
- Pitfalls hit and how they were resolved.
- Before/after numbers (timings, sizes, counts) where there are any.

```bash
git push -u origin HEAD
gh pr create --title "<title>" --body-file <pr.md> --label "risk: <level>"
# carry the article flag onto the PR so article-handoff can find it
gh pr edit <PR> --add-label article   # only if the issue has `article`
```

## Step 6 — Merge (risk: low only)

`risk: medium` and `risk: high` → stop. Tell the author the PR is ready for their review.

`risk: low`, by `Merge mode` in `CLAUDE.md`:

- **auto**: let GitHub merge once required checks pass.
  ```bash
  gh pr merge <PR> --auto --merge
  ```
- **session**: no native auto-merge (free private repo). Wait, re-check, then merge:
  ```bash
  gh pr checks <PR> --watch --fail-fast
  gh pr view <PR> --json labels --jq '[.labels[].name | select(startswith("risk: "))]'
  # must print exactly ["risk: low"]; otherwise stop
  gh pr merge <PR> --merge
  ```
  If any check fails, stop and report; don't merge.

Don't merge through a GitHub Action using `GITHUB_TOKEN`: merges made with that token don't trigger the `push` workflows on the default branch, so deploys silently don't run.

## Step 6b — Author asks for changes

When the author asks for changes after reviewing the PR, push the fix to the same branch, comment `🤖 AI <YYYY-MM-DD>` with what changed and why, update **Behaviour summary** and evidence, and re-classify risk if the file set changed.

## Step 7 — After merge

If the PR has `article` and merged during this session, run `article-handoff` for it. If it will merge later (auto mode), tell the author to run `article-handoff <PR>` after it merges.

## Done when

- [ ] Verify command ran; output is in the PR.
- [ ] PR opens with **Behaviour summary**: run output, what it does, what it deliberately doesn't do, mapped to criteria.
- [ ] Every acceptance criterion has evidence or is listed under **Not verified**.
- [ ] PR has exactly one risk label, and `Closes #<N>`.
- [ ] `article` issues: PR has `## 文章素材` and the `article` label.
- [ ] Only `risk: low` was merged or queued for auto-merge.
