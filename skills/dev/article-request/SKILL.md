---
name: article-request
description: Use when work should become an article in the repo where articles are written — either a merged PR labelled `article` (its `## 文章素材` section is handed over), or a file in any repo, such as a notes page to turn into an article. Opens an issue in the `Article target` repo labelled `article`, `status: raw`, and `article: devlog` or `article: intro`, with permalinks to the sources and instructions for reading them. Uses the local `gh` login; no PAT needed.
---

# article-request

Hands material to the article repo as a raw issue. There, `issue-enhance` drafts an outline, the author approves it, and `article-write` writes the article.

Runs from any repo's session. Every comment or body you write starts with `🤖 AI <YYYY-MM-DD>`. The AI posts with the author's `gh` login, so the author field can't tell AI from author; only this marker can.

## Step 0 — Identify the source

**A PR** (default mode `article: devlog`):

```bash
gh pr view <PR> --json number,url,title,state,labels,body,closingIssuesReferences
```

Stop and explain if the PR isn't merged, if neither it nor its closing issue has `article`, or if `## 文章素材` is missing or empty (ask the author to add it to the PR first).

**A file** (default mode `article: intro`; the author may switch it). Build a permalink pinned to a pushed commit:

```bash
git status --porcelain -- <path>            # must print nothing: commit the file first
sha=$(git rev-parse HEAD)
git branch -r --contains "$sha" | grep -q . # must succeed: push first
gh repo view --json nameWithOwner,visibility
# permalink: https://github.com/<owner>/<repo>/blob/<sha>/<path>
```

Confirm the mode with the author.

## Step 1 — Find the target

Read `Article target: <owner>/<repo>` from this repo's `CLAUDE.md` `## Issue workflow` section. Missing, placeholder, or `none` (common in a notes repo) → ask the author. Never guess a repo name.

```bash
gh repo view <target> --json nameWithOwner,visibility
```

**Privacy check:** if the source repo is private and the target is public, the issue will expose the private repo's name and file path (the contents stay private). Tell the author and get an explicit OK before going on.

## Step 2 — Don't duplicate

```bash
gh issue list -R <target> --state all --search "<PR url or permalink> in:body" --json number,url
```

If one exists, report its URL and stop.

## Step 3 — Ensure labels exist in the target

Create only the missing ones. Don't use `--force`, which would overwrite the target's existing colors and descriptions:

```bash
gh label list -R <target> --limit 200 --json name --jq '.[].name'
gh label create "article"         -R <target> --color 5319e7 --description "Write a technical article"
gh label create "status: raw"     -R <target> --color ededed --description "New issue, not yet enhanced by AI"
gh label create "article: devlog" -R <target> --color d4c5f9 --description "Article reconstructs a decision path"
gh label create "article: intro"  -R <target> --color c5def5 --description "Article introduces something to new readers"
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
  --label article --label "status: raw" --label "article: <devlog|intro>"
```

## Step 5 — Link back (PR mode)

```bash
gh pr comment <PR> --body "🤖 AI <YYYY-MM-DD>

Article request: <new issue url>"
```

## Done when

- [ ] Exactly one issue in the target for this source, labelled `article`, `status: raw`, and one `article:` mode.
- [ ] Its body lists the sources with read instructions (file sources as commit-pinned permalinks) and, for a PR, the full `## 文章素材`.
- [ ] If the source is private and the target public, the author confirmed.
- [ ] PR mode: the source PR has a comment linking to the issue.
