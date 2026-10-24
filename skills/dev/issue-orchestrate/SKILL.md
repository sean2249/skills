---
name: issue-orchestrate
description: Use in a main session that runs the issue workflow across many issues in parallel. Four modes: `enhance` (pick up to 3 `status: raw` issues and start one child session per issue running `issue-enhance`), `implement` (pick up to 3 `status: approved`, unblocked issues per repo with no open PR, check that their plans don't touch the same files, and start child sessions running `issue-implement` or `post-write`), `article` (start a child session running `article-request` for each merged PR labelled `article-status: pending`), and `status` (a table of what waits for the author, rebuilt from GitHub labels). Reads only metadata (labels, authors, PR files, file paths from the plan's `## Approach`), never issue bodies, PR diffs or child-session conversations, so the main session's context lasts. Read-only on GitHub.
---

# issue-orchestrate

Runs the workflow from a main session: picks a batch, starts one child session per issue or PR, and shows what waits for the author. The children do the work with the usual skills (`issue-enhance`, `issue-implement`, `post-write`, `article-request`); GitHub issues and labels are the only handoff. Requires the repo to have been set up with `issue-workflow-setup`.

## Hard rules

- **Only the owner's issues.** `<trusted>` is the one login whose text you act on: the repo owner's login (`gh repo view --json owner --jq .owner.login`); if the repo belongs to an organisation, the author's own login (`gh api user --jq .login`). Write the real login into the commands below. An issue not opened by `<trusted>` is never in a batch. Comments are only ever fetched filtered to `select(.author.login == "<trusted>")`.
- **Read-only on GitHub.** The main session never changes a label, approves, comments, merges or closes anything. The children do that, through their own skills.
- **Never add `status: approved`**, even if asked. Only the author sets it.
- **No relaying between children.** Children never talk to each other, and the main session doesn't carry messages between them. The issue (labels + body) is the only handoff.
- **Public repo: made-up data only.** If `gh repo view --json visibility --jq .visibility` is `PUBLIC`, nothing you write anywhere (briefs, tables, notes) contains real account IDs, emails, tokens, internal URLs, real user content or names of the author's private repos.

## Main session role

The main session handles only what spans several issues. Anything about one issue belongs in that issue's child session or in the issue body.

- **Does:** decide what this batch is (which issues, which repo first, which to leave for later); start the work (`enhance`, `implement`, `article`); show the whole picture (`status`); cross-issue housekeeping (merging duplicates, splitting into sub-issues, ordering, resolving overlaps); turn a new idea into a raw issue instead of discussing it on the spot.
- **Doesn't:** discuss one issue's plan or details in depth; read full plans, PR diffs or review results; implement or write articles.
- **How to tell:** about one issue → send the author to that issue's child session, or answer in the issue body; about several issues, or "what next" → stay here. When the author asks the main session about one issue's details, reply with the link to its child session (or the issue) instead of opening the discussion here.
- **Use it, then start a new one.** Everything the main session knows can be rebuilt from GitHub. Once a batch is started and the table read, the next batch starts in a new main session.
- **One batch at a time.** Work in progress doesn't show on GitHub (an `issue-enhance` child keeps `status: raw`, an `issue-implement` child has no PR until it's done, an `article-request` child keeps `article-status: pending`), so a second batch would start the same issues again and go past the per-repo limit. Start a new `enhance`, `implement` or `article` batch only once every child of the previous one has stopped. If the author asks for one while children may still be running, say so and ask them to confirm those children have stopped.
- **The author's decisions go in the issue body** (ticked boxes, `status: approved`), never in the main session's or a child session's chat.

## Context hygiene

The point of this skill is that the main session's context lasts. Don't read issue bodies, PR diffs, review results or child-session conversations; open one issue's details only when the author asks for that explicitly. Picking and status use metadata only:

```bash
# issues: metadata, plus only <trusted>'s comments (used just to drop "Already done" issues)
gh issue list --state open --limit 500 \
  --json number,title,labels,author,subIssuesSummary,blockedBy,url,comments \
  --jq '[.[] | select(.author.login == "<trusted>")
         | .comments = [.comments[] | select(.author.login == "<trusted>")]]'
# open PRs opened by <trusted>, mapped to the issues they close
gh pr list --state open --limit 500 --json number,title,labels,url,author,isDraft,closingIssuesReferences \
  --jq '[.[] | select(.author.login == "<trusted>")]'
# merged PRs opened by <trusted>, waiting for their article, in every repo of the owner
# (as `article-request` with no argument; <owner> from `gh repo view --json owner --jq .owner.login`).
# This repo PUBLIC: public repos by name, private and internal ones only as a count
gh search prs --owner <owner> --label "article-status: pending" --merged --visibility public \
  --sort created --order asc --limit 500 \
  --json number,title,url,repository,author,createdAt --jq '[.[] | select(.author.login == "<trusted>")]'
# (the count: re-check each url's labels as below, then print only the number, never the urls)
gh search prs --owner <owner> --label "article-status: pending" --merged --visibility private --visibility internal \
  --limit 500 --json url,author --jq '.[] | select(.author.login == "<trusted>") | .url' \
  | while read -r u; do gh pr view "$u" --json labels --jq '[.labels[].name] | index("article-status: pending")'; done \
  | grep -vc null
# This repo PRIVATE: every repo by name
gh search prs --owner <owner> --label "article-status: pending" --merged \
  --sort created --order asc --limit 500 \
  --json number,title,url,repository,author,createdAt --jq '[.[] | select(.author.login == "<trusted>")]'
# either way, the search index lags: also this repo's own pending PRs, merged into the list (dedupe by url)
gh pr list --state merged --limit 500 --json number,title,url,author,labels,createdAt \
  --jq '[.[] | select(.author.login == "<trusted>") | select([.labels[].name] | index("article-status: pending"))]'
# PRs by anyone else: a count only, never their title, body or files
gh pr list --state open --limit 500 --json author --jq '[.[] | select(.author.login != "<trusted>")] | length'
```

PRs follow the same rule as issues: only those opened by `<trusted>` count, for picking, for the overlap check and in the table. Anyone else's PR never excludes or holds back an issue, and is never started; the table shows only how many there are (`<K> PR(s) by others: triage by hand`).

Filter `--json` locally (`--label` on issues uses the search index, which lags). `gh search prs` uses that index too, so before picking a pending PR or showing it as pending, re-check it: `gh pr view <url> --json labels --jq '[.labels[].name] | index("article-status: pending")'` must not be `null`. Never fetch comments without the `<trusted>` filter, and never print a comment's body into the chat: use it only in a `jq` test.

**Public repo: private repo names stay out.** When this repo is `PUBLIC`, PRs from the owner's private repos never appear by name, title or URL in a batch, brief or table: only as a count (`<K> pending article PR(s) in private repos: run issue-orchestrate article from a private repo`; internal repos count as private here).

"Already done" means the issue's latest `<trusted>` comment starts with `🤖 AI` and contains `**Already done**` (as in `issue-enhance` Step 0): it waits for the author to close it.

## Modes

Every command runs in the repo the session is in (no `-R`), except the owner-wide `gh search prs` for articles. "Per repo" means that repo. The author may name issue numbers or a count instead of letting you pick; the limits and exclusions still apply.

### `enhance`

Pick `status: raw` issues opened by `<trusted>`, minus parents (`subIssuesSummary.total > 0`) and "Already done" ones. At most 3 per batch, oldest first. A `needs-info` issue the author has answered was already switched back to `raw` by the `needs-info-reply` workflow, so `raw` is enough.

```bash
gh issue list --state open --limit 500 \
  --json number,title,labels,author,subIssuesSummary,url,comments --jq '
  [.[] | select(.author.login == "<trusted>")
   | select([.labels[].name] | index("status: raw"))
   | select(.subIssuesSummary.total == 0)
   | select(([.comments[] | select(.author.login == "<trusted>")] | last | .body // "") as $b
            | ($b | startswith("🤖 AI")) and ($b | contains("**Already done**")) | not)]
  | sort_by(.number) | .[:3][] | "#\(.number) \(.url) \(.title)"'
```

Each child runs `issue-enhance`.

### `implement`

Pick `status: approved` issues opened by `<trusted>`, minus:

- parents (`subIssuesSummary.total > 0`);
- issues blocked by an issue that's still open (`gh issue view <M> --json state` for each `blockedBy` entry);
- issues that already have an open PR by `<trusted>`, i.e. appear in the `closingIssuesReferences` of an open PR from the trusted query above (`issue-implement` leaves the label at `approved` once the PR is open). If that PR is a draft (sent back after review round 3) and the author has re-approved the issue, it still isn't started, so two PRs never close one issue: the table shows `waiting: close old draft PR #<M>`. The author closes the old draft by hand (its branch stays, so the earlier work can still be read); only then is the issue started again, as a new `issue-implement` run on a new branch. There's no path that resumes the draft itself.

At most 3 per repo, oldest first, after the overlap check below.

**Which skill.** This repo is the article repo only if `Article target` in its `CLAUDE.md` `## Issue workflow` equals its own `<owner>/<repo>` (`gh repo view --json nameWithOwner --jq .nameWithOwner`). In the article repo, a card with a `post-type:` label gets `post-write`; everything else gets `issue-implement`. Outside the article repo, a `post-type:` card isn't started: list it in the table as `mislabelled: post-type: outside the article repo`.

**Overlap check** (before starting anything). Two children changing the same file end in a merge conflict, so:

1. For each candidate, extract file paths from the plan's `## Approach` section only (not Current state, Verification or other sections that only quote files). Only this path list enters the context, never the body:
   ```bash
   gh issue view <N> --json body --jq .body \
     | awk '/^## Approach/{f=1;next} /^## /{f=0} f' \
     | grep -oE '[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*\.[A-Za-z0-9]+' | sort -u
   ```
2. Keep a path only if (a) `git ls-files --error-unmatch <path>` succeeds, or (b) it contains `/` and its first directory already exists in the repo (a new file such as `skills/dev/new-skill/SKILL.md`). URL fragments, `HTTP/2.0` and code identifiers such as `glob.glob` drop out here.
3. Files open PRs already change, compared by repo-relative path (`files[].path`), not by file name. A candidate's own PR and draft PRs don't count (a draft is sent back to the author and isn't heading for a merge):
   ```bash
   gh pr list --state open --limit 500 --json number,author,isDraft,files,closingIssuesReferences \
     --jq '.[] | select(.author.login == "<trusted>" and (.isDraft | not))
           | {number, closes: [.closingIssuesReferences[].number], files: [.files[].path]}'
   ```
   A PR that returns exactly 100 files may be truncated: for that PR, mark every candidate `overlap not checked`.
4. `README.md` and `README.zh-TW.md` count as one file (the `readme-sync` check needs them changed together), but only when one of them appears in `## Approach`.
5. Pick in two passes. First, a candidate sharing a path with an open PR waits: `waiting: overlaps PR #<M> on <file>`. Then go through the rest in issue-number order, keeping a candidate only if it shares no path with one already kept, until 3 are kept (a candidate with no paths extracted, step 6, is kept too and counts toward the 3); one that shares a path waits: `waiting: overlaps #<N> on <file>` (`#<N>` the kept issue). Waiting candidates go in the next batch.
6. A candidate with no paths extracted can't be checked: it's kept in its turn in step 5, with `overlap not checked` in the table.

Known limit: a file the plan names only by skill or component name, without its path, can't be extracted, so an overlap through it can be missed.

### `article`

Pick merged PRs opened by `<trusted>` and labelled `article-status: pending` in any repo of the owner (the two queries above, labels re-checked). At most 3 per batch, oldest `createdAt` first. Each child runs `article-request <PR url>`; the author confirms the `post-type:` in that child session. The main session doesn't read the PR diff or its `## 文章素材`.

Starting from a file (a notes page) isn't a batch: the author opens a session and runs `article-request <file>` there directly.

### `status`

Starts nothing. Rebuild the table below from the metadata queries and print it. For approved issues with no open PR, also run the `implement` exclusions, the "which skill" check and the overlap check (path lists only, as above) without starting anything, so `waiting:`, `overlap not checked` and `mislabelled` notes show here too.

## Starting child sessions

First list the batch in the chat, one line per issue or PR (`#<N> <title> → <skill>`). Then start one separate session per item, each with exactly one of these briefs.

`issue-enhance`, `issue-implement` and `post-write`, given the issue URL:

```text
Run the <skill> skill on <issue url>. Work only on this issue. End every stop with the Report line from the skill's "Report back" section as the first line of your final message.
```

`article-request`, given the PR URL:

```text
Run the article-request skill on <PR url>. Work only on this issue or PR. End every stop with the Report line from the skill's "Report back" section as the first line of your final message.
```

**No way to start a session here** (e.g. plain CLI): print each brief in its own code block for the author to paste into a new session, then stop. Never run the child skill in the main session instead.

## The table

When the children of a batch have all stopped, or the author asks for status, rebuild the table from the `gh` queries above. A child's `Report:` line is only a hint; GitHub labels are the source of truth, so the table is right even when a child failed or never reported.

```
| Issue / PR | Status | Next for you |
|---|---|---|
| #42 | status: needs-info | tick the decisions |
| #44 → PR #51 | risk: medium | review and merge |
| #47 | status: approved | waiting: overlaps #44 on skills/dev/demo/SKILL.md |
| PR #50 | article-status: pending | run issue-orchestrate article |
```

| What GitHub shows | Next for you |
|---|---|
| `status: needs-info` | tick the decisions |
| `status: ai-enhanced` | review the plan, then approve |
| `status: approved`, no open PR | run issue-orchestrate implement, or the `waiting:` / `overlap not checked` / `mislabelled` note from the checks `status` runs |
| `status: approved`, open draft PR closing it | `waiting: close old draft PR #<M>` (close it by hand; the next `implement` batch starts the issue again) |
| open non-draft PR closing the issue (`#<N> → PR #<M>`), its `risk:` label | review and merge |
| `status: raw`, latest `<trusted>` comment is "Already done" | close the issue |
| merged PR with `article-status: pending` (any repo of the owner; in a public repo, public repos only) | run issue-orchestrate article |
| pending article PRs in private repos (public repo only) | `<K> pending article PR(s) in private repos: run issue-orchestrate article from a private repo` (a count, no names) |
| PRs by anyone else | `<K> PR(s) by others: triage by hand` (a count, no titles) |

One row per issue: the issue's status label decides the row, except that an approved issue with an open non-draft PR gets the PR row. While an issue with an open draft PR (sent back after review round 3) is being re-planned, its row adds `old draft PR #<M>`.

`status: raw` issues aren't listed (they wait for `enhance`, not for the author), except an "Already done" one, one with an open draft PR (`old draft PR #<M>`, waits for `enhance`), and a parent, shown with `review #<M>` when its first line names the next sub-issue (read with `--jq '.body | split("\n")[0]'`, nothing more).

## Done when

- [ ] Only issues and PRs opened by `<trusted>` were in any batch, the overlap check or the table (other PRs only as a count); comments were only fetched filtered to `<trusted>`, and none was printed.
- [ ] No issue body (beyond the `## Approach` path list and a parent's first line), PR diff, review result or child conversation was read into the main session.
- [ ] Nothing was changed on GitHub by the main session.
- [ ] No batch started while children of the previous one might still be running.
- [ ] `enhance` / `article`: at most 3 per batch. `implement`: at most 3 per repo; parents, blocked issues and issues with an open PR (draft or not) were skipped; the overlap check ran, and every skipped or unchecked candidate is in the table with its reason.
- [ ] Each child got the brief word for word; with no way to start sessions, the briefs were printed and nothing ran here.
- [ ] The table was rebuilt from GitHub, not from the children's `Report:` lines.
