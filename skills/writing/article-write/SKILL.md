---
name: article-write
description: Use when, in an article repo, an issue with an `article-type:` label and `status: approved` should be written up as an article and opened as a PR. Four modes by label: `article-type: devlog` (reconstructs a decision path), `article-type: intro` (introduces a tool, concept or site), `article-type: review` (the author's take on a work: book, exhibition, performance…), `article-type: research` (a topic exploration that keeps the reasoning, not just the conclusion). Reads only the sources the issue names, follows the repo's `## Article conventions`, and attaches a source map so nothing from notes is silently dropped.
---

# article-write

Turns an approved article issue into an article PR. The issue usually comes from `article-request` and was outlined by `issue-enhance`. Repo-specific rules (paths, frontmatter, series, numbering, images, build) live in the article repo's `CLAUDE.md`, not here.

## Hard rules

- **Only `status: approved` issues.** Never add `status: approved` yourself, even if asked.
- **Read only the sources the issue names.** Never search a source repo for other files: it may hold private material.
- **Faithful to notes.** Applies to every source that is a personal note, and always to `review` and `research`. When a source is a personal note, you may smooth sentences and drop internal links and frontmatter. Don't add opinions or conclusions the author didn't write. Never present anything the note marks as AI speculation, or as unconfirmed by the author, as the author's view.
- **Every comment you post starts with** `🤖 AI <YYYY-MM-DD>`. The AI posts with the author's `gh` login, so the author field can't tell AI from author; only this marker can.

## Step 0 — Gate

```bash
gh issue view <N> --json number,title,body,labels,state,blockedBy,subIssuesSummary
```

Refuse and explain if:

| Condition | Say |
|---|---|
| Closed, or no `article-type:` label | Not an open article issue. |
| No `status: approved` | Current status is `<label>`; the author approves. Suggest `issue-enhance` to draft the outline. |
| An issue in `blockedBy` is still open (`gh issue view <M> --json state`) | Blocked by #M. |
| More than one `article-type:` label | Ask the author which mode. |

If `gh` rejects the `blockedBy` / `subIssuesSummary` fields, it's too old: ask the author to upgrade `gh` and stop.

## Step 1 — Read the repo's conventions

Read the `## Article conventions` section of this repo's `CLAUDE.md`. It defines the output path (and the category/directory for each mode), frontmatter fields, series and numbering, where images go, the verify/build command, and the preview URL. **If the section is missing, or any key you need is still `<fill in>`, stop and ask the author.** Don't guess conventions from existing files.

## Step 2 — Read the sources

Use the issue body: the `## Sources` list (from `article-request`) and the approved outline (from `issue-enhance`). Read each source exactly as named:

| Source | How to read |
|---|---|
| PR | `gh pr view <url>` and `gh pr diff <url>`. The PR body's `## 文章素材` section stands in for the conversation, which you can't see |
| Issue | `gh issue view <url> --comments` |
| File permalink `https://github.com/<o>/<r>/blob/<sha>/<path>` | `gh api -H "Accept: application/vnd.github.raw+json" "repos/<o>/<r>/contents/<path>?ref=<sha>"`. If a local clone of `<o>/<r>` exists, `git -C <clone> show <sha>:<path>` instead |
| Web URL | fetch that page only |

Anything you need that isn't in the sources → ask the author; don't go looking.

## Step 3 — Write

Follow the approved outline: its main thread, sections, and its "not writing" list.

**`article-type: devlog`: reconstruct the decision path.**
- Pick **one** main thread. Not everything that happened goes in.
- For that thread: what the original plan was, why it was dropped, where it got stuck, how the cause was found, what was done instead.
- Use the author's own words from `## 文章素材` at the decision points, and real numbers where the sources have them.

**`article-type: intro`: introduce a tool, concept, or site to someone who hasn't seen it.**
- What it is, in plain terms, up front.
- Why it's worth the reader's time: what's distinctive, who it's for.
- Concrete details from the source, not generic praise.

**`article-type: review`: the author's take on a work (book, exhibition, performance…).**
- The author's impressions and judgement are the body; facts about the work (title, creator, dates, venue) support them.
- Keep every evaluation, quotation, comparison, and reservation the author wrote, including the critical ones.
- Don't add a verdict, rating, or closing conclusion the author didn't write.

**`article-type: research`: a topic study / exploration.**
- Keep the core question, the line of reasoning, how the author's position changed along the way, and the open questions.
- Don't compress it into conclusions only; the path is the content.
- Keep the author's uncertainty where the notes are uncertain.

Write in the issue's language. Apply the repo's conventions to path, frontmatter, and images.

## Step 3b — Source map (note sources)

Required when a source is a note-like file: always for `review` and `research`, and for `intro` when its source is a file. Go through the source section by section (or point by point) and record where each part went:

```markdown
## Source map
| Source section / point | In the article | If left out: why |
|---|---|---|
| <heading or first words of the point> | §<article section> | |
| <…> | — | duplicate of <…> / only meaningful to the author / internal link / … |
```

Every section of the source appears as a row. A row with neither an article section nor a reason means something was lost; fix the article or add the reason. This goes in the PR (Step 5) so the author can check for gaps.

## Step 4 — Verify

Run the verify/build command from `## Article conventions` and open the preview page. Note anything you couldn't check.

## Step 5 — Open the PR

```bash
git switch -c article-<N>-<slug> origin/<default-branch>
git add <article files>
git commit -m "<title>"
git push -u origin HEAD
gh pr create --title "<article title>" --body-file <pr.md> --label "risk: <level>"
```

PR body, following the repo's PR template:

- `Closes #<N>`.
- **Preview**: the page(s) to open, as links.
- **Behaviour summary**: build output, what the article covers (main thread), what it deliberately leaves out, and each outline point / acceptance criterion mapped to the section that meets it.
- **Source map** (Step 3b) when a source is a note-like file.
- **Not verified**, plus **Deviations from the approved outline** with reasons.
- Risk per `issue-implement` Step 4.

**Don't merge.** The author reads every article before it's published, whatever the risk label.

When the author asks for changes: revise on the same branch, comment `🤖 AI <YYYY-MM-DD>` with what changed and why, and update the Behaviour summary.

## Done when

- [ ] Article follows `## Article conventions` and the approved outline; mode matches the label.
- [ ] Only the named sources were read; nothing from notes was turned into an opinion the author didn't state.
- [ ] Note sources: the PR has a source map where every source section is either placed in the article or has a reason for leaving it out.
- [ ] Build ran; the PR has preview links, the Behaviour summary, and `Closes #<N>`.
- [ ] PR left for the author to merge.
