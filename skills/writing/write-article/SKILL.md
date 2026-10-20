---
name: write-article
description: Use when, in an article repo, an issue labelled `article` and `status: approved` should be written up as an article and opened as a PR. Writes a devlog (`article: devlog`, reconstructs the decision path) or an intro (`article: intro`, explains what something is and why it's worth a look), reading only the sources the issue names and following the repo's `## Article conventions`.
---

# write-article

Turns an approved article issue into an article PR. The issue usually comes from `article-handoff` and was outlined by `issue-enhance`. Repo-specific rules (paths, frontmatter, series, numbering, images, build) live in the article repo's `CLAUDE.md`, not here.

## Hard rules

- **Only `status: approved` issues.** Never add `status: approved` yourself, even if asked.
- **Read only the sources the issue names.** Never search a source repo for other files: it may hold private material.
- **Faithful to notes.** When a source is a personal note, you may smooth sentences and drop internal links and frontmatter. Don't add opinions or conclusions the author didn't write. Never present anything the note marks as AI speculation, or as unconfirmed by the author, as the author's view.
- **Every comment you post starts with** `🤖 AI <YYYY-MM-DD>`. The AI posts with the author's `gh` login, so the author field can't tell AI from author; only this marker can.

## Step 0 — Gate

```bash
gh issue view <N> --json number,title,body,labels,state,blockedBy,subIssuesSummary
```

Refuse and explain if:

| Condition | Say |
|---|---|
| Closed, or no `article` label | Not an open article issue. |
| No `status: approved` | Current status is `<label>`; the author approves. Suggest `issue-enhance` to draft the outline. |
| An issue in `blockedBy` is still open (`gh issue view <M> --json state`) | Blocked by #M. |
| Neither or both of `article: devlog` / `article: intro` | Ask the author which mode. |

On a gh without `blockedBy` / `subIssuesSummary` fields, see "Older gh" in `issue-enhance`.

## Step 1 — Read the repo's conventions

Read the `## Article conventions` section of this repo's `CLAUDE.md`. It defines the output path, frontmatter fields, series and numbering, where images go, the verify/build command, and the preview URL. **If the section is missing, or any key you need is still `<fill in>`, stop and ask the author.** Don't guess conventions from existing files.

## Step 2 — Read the sources

Use the issue body: the `## Sources` list (from `article-handoff`) and the approved outline (from `issue-enhance`). Read each source exactly as named:

| Source | How to read |
|---|---|
| PR | `gh pr view <url>` and `gh pr diff <url>`. The PR body's `## 文章素材` section stands in for the conversation, which you can't see |
| Issue | `gh issue view <url> --comments` |
| File permalink `https://github.com/<o>/<r>/blob/<sha>/<path>` | `gh api -H "Accept: application/vnd.github.raw+json" "repos/<o>/<r>/contents/<path>?ref=<sha>"`. If a local clone of `<o>/<r>` exists, `git -C <clone> show <sha>:<path>` instead |
| Web URL | fetch that page only |

Anything you need that isn't in the sources → ask the author; don't go looking.

## Step 3 — Write

Follow the approved outline: its main thread, sections, and its "not writing" list.

**`article: devlog`: reconstruct the decision path.**
- Pick **one** main thread. Not everything that happened goes in.
- For that thread: what the original plan was, why it was dropped, where it got stuck, how the cause was found, what was done instead.
- Use the author's own words from `## 文章素材` at the decision points, and real numbers where the sources have them.

**`article: intro`: introduce it to someone who hasn't seen it.**
- What it is, in plain terms, up front.
- Why it's worth the reader's time: what's distinctive, who it's for.
- Concrete details from the source, not generic praise.

Write in the issue's language. Apply the repo's conventions to path, frontmatter, and images.

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
- **Not verified**, plus **Deviations from the approved outline** with reasons.
- Risk per `issue-implement` Step 4.

**Don't merge.** The author reads every article before it's published, whatever the risk label.

When the author asks for changes: revise on the same branch, comment `🤖 AI <YYYY-MM-DD>` with what changed and why, and update the Behaviour summary.

## Done when

- [ ] Article follows `## Article conventions` and the approved outline; mode matches the label.
- [ ] Only the named sources were read; nothing from notes was turned into an opinion the author didn't state.
- [ ] Build ran; the PR has preview links, the Behaviour summary, and `Closes #<N>`.
- [ ] PR left for the author to merge.
