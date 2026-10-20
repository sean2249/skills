---
name: article-handoff
description: Use when a PR labelled `article` has been merged and its `## 文章素材` section should be handed to the repo where articles are written. Opens an issue in the `Article target` repo from CLAUDE.md, labelled `article` and `status: raw`, with links back to the source repo, issue, and PR. Uses the local `gh` login; no PAT needed.
---

# article-handoff

Hands a shipped piece of work to the article-writing repo as a raw issue. The article session later picks it up with `issue-enhance`.

## Step 0 — Gate

```bash
gh pr view <PR> --json number,url,title,state,mergedAt,labels,body,closingIssuesReferences
```

Stop and explain if:

- The PR isn't merged (`state` != `MERGED`).
- Neither the PR nor its closing issue has the `article` label.
- The body has no `## 文章素材` section, or it's empty. Tell the author to add it to the PR first.

## Step 1 — Find the target

Read `Article target: <owner>/<repo>` from the repo's `CLAUDE.md` `## Issue workflow` section. Missing, placeholder, or `none` → ask the author. Never guess a repo name.

Check access with the local login (`gh auth status` must be the account that can write to the target):

```bash
gh repo view <target> --json nameWithOwner
```

## Step 2 — Don't duplicate

```bash
gh issue list -R <target> --state all --search "<PR url> in:body" --json number,url
```

If one exists, report its URL and stop.

## Step 3 — Ensure labels exist in the target

Create only the missing ones. Don't use `--force`, which would overwrite the target's existing colors and descriptions:

```bash
gh label list -R <target> --limit 200 --json name --jq '.[].name'
gh label create "article"     -R <target> --color 5319e7 --description "Write a technical article"
gh label create "status: raw" -R <target> --color ededed --description "New issue, not yet enhanced by AI"
```

## Step 4 — Open the issue

Extract `## 文章素材` from the PR body: from that heading to the next `## ` heading or the end, verbatim.

Body:

```markdown
🤖 AI <YYYY-MM-DD> (article-handoff)

**Before writing, read the source PR:** `gh pr view <PR url>` and `gh pr diff <PR url>`.

- Source repo: <owner>/<repo>
- Issue: <issue url>
- PR: <PR url>

## 文章素材

<section copied verbatim>
```

```bash
gh issue create -R <target> --title "Article: <PR title>" --body-file <body.md> \
  --label article --label "status: raw"
```

## Step 5 — Link back

```bash
gh pr comment <PR> --body "🤖 AI <YYYY-MM-DD>

Article handoff: <new issue url>"
```

## Done when

- [ ] Exactly one issue in the target links this PR, labelled `article` and `status: raw`.
- [ ] Its body has the source links, the read-the-PR instruction, and the full `## 文章素材`.
- [ ] The source PR has a comment linking to it.
