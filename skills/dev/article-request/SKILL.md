---
name: article-request
description: Use when work should become an article in the repo where articles are written — either a merged PR labelled `article-status: pending` (its `## 文章素材` section is handed over), or a file in any repo, such as a notes page to turn into an article. Opens an issue in the `Article target` repo labelled `status: raw` and one `article-type:` (`devlog`, `intro`, `review`, or `research`), then marks the source PR `article-status: handoff`, with permalinks to the sources and instructions for reading them. Uses the local `gh` login; no PAT needed.
---

# article-request

Hands material to the article repo as a raw issue. There, `issue-enhance` drafts an outline, the author approves it, and `article-write` writes the article.

Article progress in a project repo is one label, `article-status:`: **request** (the work should become an article; the author adds it to the issue, `issue-implement` copies it to the PR) → **pending** (the PR merged; set by the `article-pending` workflow) → **handoff** (this skill opened the article issue; done on this side). In the article repo, an article issue carries only an `article-type:` label.

Runs from any repo's session. Every comment or body you write starts with `🤖 AI <YYYY-MM-DD>`. The AI posts with the author's `gh` login, so the author field can't tell AI from author; only this marker can.

## Step 0 — Identify the source

**No argument**: list every merged PR still waiting for its article, across the current repo's owner, and let the author pick:

```bash
owner=$(gh repo view --json owner --jq .owner.login)
gh search prs --owner "$owner" --label "article-status: pending" --merged --json url,title,repository
```

`article-status: pending` is added on merge by the `article-pending` workflow. Nothing listed → say so and stop.

**A PR** (default mode `article-type: devlog`):

```bash
gh pr view <PR> --json number,url,title,state,labels,body,closingIssuesReferences
```

Stop and explain if the PR isn't merged, if neither it nor its closing issue has `article-status: request` or `article-status: pending` (already `handoff` → it was handed over; report that), or if `## 文章素材` is missing or empty (ask the author to add it to the PR first).

**A file** (default mode `article-type: intro`). Ask the author to pick one of the four modes: `intro` (a tool / concept / site), `review` (their take on a work: book, exhibition, performance…), `research` (a topic exploration), or `devlog` (a decision path). Build a permalink pinned to a pushed commit:

```bash
git status --porcelain -- <path>            # must print nothing: commit the file first
sha=$(git rev-parse HEAD)
git branch -r --contains "$sha" | grep -q . # must succeed: push first
gh repo view --json nameWithOwner,visibility
# permalink: https://github.com/<owner>/<repo>/blob/<sha>/<path>
```

Confirm the mode with the author before Step 4.

## Step 1 — Find the target

Read `Article target: <owner>/<repo>` from the `## Issue workflow` section of the source repo's `CLAUDE.md`. In PR mode that's the PR's repo: read it locally if you're in it, else `gh api -H "Accept: application/vnd.github.raw+json" repos/<o>/<r>/contents/CLAUDE.md`. Missing, placeholder, or `none` (common in a notes repo) → ask the author. Never guess a repo name.

```bash
gh repo view <target> --json nameWithOwner,visibility
```

**Privacy check:** if the source repo is private and the target is public, the issue will expose the private repo's name and file path (the contents stay private). Tell the author and get an explicit OK before going on.

## Step 2 — Don't duplicate

```bash
gh issue list -R <target> --state all --search "<PR url or permalink> in:body" --json number,url
```

If one exists, report its URL. In PR mode, still do Step 5 if the PR has `article-status: pending`. Then stop.

## Step 3 — Ensure labels exist in the target

Create only the missing ones. Don't use `--force`, which would overwrite the target's existing colors and descriptions:

```bash
gh label list -R <target> --limit 200 --json name --jq '.[].name'
gh label create "status: raw"     -R <target> --color ededed --description "New issue, not yet enhanced by AI"
gh label create "article-type: devlog" -R <target> --color d4c5f9 --description "Article reconstructs a decision path"
gh label create "article-type: intro"  -R <target> --color c5def5 --description "Article introduces a tool, concept or site"
gh label create "article-type: review"   -R <target> --color f9d0c4 --description "Article reviews a work: the author's take"
gh label create "article-type: research" -R <target> --color bfdadc --description "Article explores a topic, reasoning kept"
```

## Step 4 — Open the issue

Body. Keep `## Sources` with its read instructions; `article-write` reads only what's listed there:

````markdown
🤖 AI <YYYY-MM-DD> (article-request)

## Sources
- PR: <PR url>. Read with `gh pr view <PR url>` and `gh pr diff <PR url>`.
- Issue: <issue url>. Read with `gh issue view <issue url> --comments`.
- File: <permalink>. Read with `gh api -H "Accept: application/vnd.github.raw+json" "repos/<o>/<r>/contents/<path>?ref=<sha>"`, or `git show <sha>:<path>` in a local clone.

Read only these sources. Don't search the source repos for other files.

## 文章素材
<PR mode: the section copied verbatim from the PR body. File mode: omit this section.>
````

Keep only the source lines that apply.

```bash
gh issue create -R <target> --title "Article: <PR title or file title>" --body-file <body.md> \
  --label "status: raw" --label "article-type: <devlog|intro|review|research>"
```

## Step 5 — Mark the PR as handed off (PR mode)

```bash
gh label create "article-status: handoff" -R <o>/<r> --color 0e8a16 \
  --description "Handed to the article repo; done here" 2>/dev/null || true
gh pr edit <PR url> --remove-label "article-status: pending" --remove-label "article-status: request" \
  --add-label "article-status: handoff"
gh pr comment <PR url> --body "🤖 AI <YYYY-MM-DD>

Article request: <new issue url>"
```

## Done when

- [ ] Exactly one issue in the target for this source, labelled `status: raw` and one `article-type:` label (no `article` label).
- [ ] Its body lists the sources with read instructions (file sources as commit-pinned permalinks) and, for a PR, the full `## 文章素材`.
- [ ] If the source is private and the target public, the author confirmed.
- [ ] PR mode: the source PR has `article-status: handoff` (no longer `pending` / `request`) and a comment linking to the issue.
