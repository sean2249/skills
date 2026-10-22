---
name: issue-implement
description: Use when implementing a GitHub issue labelled `status: approved` — branch, implement, run the repo's verify command, open a PR with per-criterion evidence, run code and security review (up to 3 rounds), classify risk (low / medium / high), and merge only `risk: low` PRs. Refuses issues in any other status.
---

# issue-implement

Implements one approved issue end to end. Requires the repo to have been set up with `issue-workflow-setup`.

## Step 0 — Gate

```bash
gh issue view <N> --json number,title,body,labels,state,comments,blockedBy,subIssuesSummary
# for each issue listed in blockedBy:
gh issue view <M> --json state --jq .state
```

If `gh` rejects these JSON fields, it's too old: ask the author to upgrade `gh` and stop.

Refuse and explain if any of these hold:

| Condition | Say |
|---|---|
| Issue is closed | It's closed; nothing to implement. |
| No `status: approved` label | Current status is `<label>`; only the author can approve. Suggest `issue-enhance` for `raw` / `needs-info`, or author review for `ai-enhanced`. |
| Any issue in `blockedBy` is still open | Blocked by #M (list each open blocker); implement those first. |
| `subIssuesSummary.total` > 0 (it's a parent) | It's a parent issue; implement its sub-issues instead. |
| Has any `post-type:` label (an article to write, in the article repo) | Use `article-write`. `article-status: request` is fine: it means "write an article after this ships" (Step 5). |

Never add `status: approved` yourself, even if asked.

Every comment you post on the PR or the issue starts with the line `🤖 AI <YYYY-MM-DD>`. The AI posts with the author's `gh` login, so GitHub's author field can't tell AI from author; only this marker can. Implement from the issue body (the author's text plus the AI plan section), not from comments.

Read `CLAUDE.md` `## Issue workflow`: verify command, preview URL, low-risk paths file, merge mode.

## Step 1 — Branch

```bash
git fetch origin
git switch -c issue-<N>-<short-slug> origin/<default-branch>
```

## Step 2 — Implement

Follow the issue's **Approach** and **Acceptance criteria**. Also:

- **Risks**: apply every mitigation listed there. Each one gets accounted for in the PR.
- **Opportunities** marked **this time**: implement them; ones marked later or new issue are out of scope.

When you must deviate from the approved plan, note what and why as you go; it goes in the PR.

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

This is the starting label. Step 5b can raise it, never lower it.

## Step 5 — Open the PR

Fill the repo's PR template:

- `Closes #<N>`.
- **Behaviour summary** (first section; the author reads this to decide whether to let it through, before looking at the diff):
  - Run output: what running the change actually prints or shows (command + output excerpt, or screenshot).
  - What it does: one short paragraph.
  - What it deliberately doesn't do: one short paragraph.
  - Mapped to acceptance criteria: one line per criterion → the part of the behaviour that meets it.
  - Risks: one line per risk in the issue → how the mitigation was handled (or why it wasn't, under **Not verified** / **Deviations**).
  - Opportunities (this time): one line each → where it's done.
- **Acceptance criteria — evidence**: every criterion from the issue, word for word, each with its evidence (command + output excerpt, screenshot, preview link).
- **Not verified**: say plainly what wasn't checked and why.
- **Deviations from the approved plan**: each with its reason, or "None".
- **Risk**: level and reason.
- **Review**: filled in by Step 5b.

If the issue has `article-status: request`, add a `## 文章素材` section **now, in this session**. The article-writing session can't see this conversation:

- Background: why this work happened.
- The author's own words from this session at each decision point (quote them).
- Approach taken.
- Pitfalls hit and how they were resolved.
- Before/after numbers (timings, sizes, counts) where there are any.

```bash
git push -u origin HEAD
gh pr create --title "<title>" --body-file <pr.md> --label "risk: <level>"
# carry the request onto the PR; article-pending swaps it to pending on merge
gh pr edit <PR> --add-label "article-status: request"   # only if the issue has it
```

## Step 5b — Review (code + security), before any merge

Run both reviews on the open PR, using the built-in skills via the Skill tool:

- `code-review` on this PR (`<PR number>`): correctness problems in the diff.
- `security-review`: security review of the branch's diff against the default branch.

Don't pass `--comment` (its comments wouldn't carry the 🤖 marker). Collect the findings and handle them here. **If either skill isn't available in the session**, dispatch a fresh-context subagent (Agent tool, `general-purpose`) for that review instead. Give it only the PR URL and the repo, not your reasoning, and ask for findings with severity and `file:line`. Note in the PR that the fallback was used.

**Handle every finding**: fix it, or decide not to and give the reason (false positive, out of scope, deliberate trade-off). After fixes, push and run both reviews again **on the new changes only**. **At most 3 rounds.** If findings are still unhandled after round 3, stop and hand the PR to the author.

**Record it.** Add a `## Review` section to the PR body. For each review, give how many rounds ran (and whether the fallback was used). For each finding, give its severity, `file:line`, and outcome: fixed (commit), or not fixed plus the reason. Then post a PR comment starting with `🤖 AI <YYYY-MM-DD>` that summarises it.

**Re-check the risk label.** The PR can't be `risk: low`, and isn't merged automatically, if **any** security finding is left unfixed (even one the author agreed to skip), or a **high-severity** code-review finding is left unfixed. Swap the label:

```bash
gh pr edit <PR> --remove-label "risk: low" --add-label "risk: medium"
```

## Step 6 — Merge (risk: low only)

`risk: medium` and `risk: high` → stop. Tell the author the PR is ready for their review.

`risk: low`: first pick a merge method the repo allows. Don't assume merge commits are on:

```bash
gh api repos/<owner>/<repo> --jq '{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge}'
```

Use the first allowed one in this order: `--merge`, `--squash`, `--rebase`. That flag is `<method>` below.

Then, by `Merge mode` in `CLAUDE.md`:

- **auto**: let GitHub merge once required checks pass.
  ```bash
  gh pr merge <PR> --auto <method>
  ```
- **session**: no native auto-merge (free private repo). Wait, re-check, then merge:
  ```bash
  gh pr checks <PR> --watch --fail-fast
  gh pr view <PR> --json labels --jq '[.labels[].name | select(startswith("risk: "))]'
  # must print exactly ["risk: low"]; otherwise stop
  gh pr merge <PR> <method>
  ```
  If any check fails, stop and report; don't merge.

Don't merge through a GitHub Action using `GITHUB_TOKEN`: merges made with that token don't trigger the `push` workflows on the default branch, so deploys silently don't run.

## Step 6b — Author asks for changes

When the author asks for changes after reviewing the PR, push the fix to the same branch, comment `🤖 AI <YYYY-MM-DD>` with what changed and why, update **Behaviour summary** and evidence, and re-classify risk if the file set changed.

## Step 7 — After merge

If the PR has `article-status: request` and merged during this session, run `article-request <PR url>` for it. If it merges later (auto mode or the author's review), the `article-pending` workflow swaps it to `article-status: pending` on merge and comments to remind the author. Running `article-request` with no argument then lists every pending PR.

## Done when

- [ ] Verify command ran; output is in the PR.
- [ ] PR opens with **Behaviour summary**: run output, what it does, what it deliberately doesn't do, mapped to criteria.
- [ ] Every acceptance criterion has evidence or is listed under **Not verified**.
- [ ] Every issue Risk has its mitigation accounted for, and every "this time" Opportunity is mapped, in the Behaviour summary.
- [ ] PR has exactly one risk label, and `Closes #<N>`.
- [ ] `article-status: request` issues: PR has `## 文章素材` and the `article-status: request` label.
- [ ] Both reviews (code + security) ran, at most 3 rounds, before any merge; every finding is fixed or has a reason; the PR has `## Review` and a 🤖 summary comment.
- [ ] No `risk: low` with an unfixed security finding or unfixed high-severity code finding.
- [ ] Only `risk: low` was merged or queued for auto-merge.
