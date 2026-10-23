---
name: kiwi-voice
description: Use to apply or grow the author's writing voice in a blog repo. Two branches. 套用 (apply): before handing over any post you wrote or edited (post-write runs it before the author edits), check the draft against the repo's voice file rule by rule. 收納 (collect): after each round of the author's edits to an AI-written post, compare the AI draft with the author's version and propose voice-file rules for the author to approve. Holds only the process; the rules live in each repo's voice file, named in its CLAUDE.md.
---

# kiwi-voice

This skill is the process only. The rules live in **one voice file per repo**, whose path the repo's `CLAUDE.md` names (a `Voice file: <path>` line, e.g. `Voice file: docs/voice.md`). Read the rules there and write them there; never keep rules in this skill.

**Find the voice file first.** No `Voice file:` line, or the file doesn't exist → ask the author where it is (or whether to start one, in the structure below). Don't guess.

When the voice file and another writing skill (or the repo's conventions) disagree, the voice file wins. The author's own sentences win over both.

## Voice file structure

```markdown
# <blog> 寫作風格（voice）

## 所有文章
### <rule name>：<one positive sentence: how to write>
- 改前 → 改後（<YYYY-MM-DD>, <post>）

## devlog
## intro
## review
## research
<!-- one section per post type; rules that only hold for that type -->

## 收納紀錄
| 日期 | 文章 | 新增規則 | 補例子 |
|---|---|---|---|
```

## 套用 (apply)

Run before handing over any post, new or revised.

1. Read the whole voice file. Done when: you can say what each rule governs.
2. Settle the draft's content and facts first.
3. Check the draft against every rule in `所有文章`, and every rule in the section for this post's type. Fix what doesn't fit. Done when: every rule was checked and you can list which rules changed which sentences.
4. **Keep the author's own words.** Sentences the author already edited stay exactly as they are, slang and typos included. When the post is transcribed from the author's own note (a vault or personal note), you may adjust wording, but **never delete a sentence the author wrote**, even if a rule (e.g. 重複) seems to call for it. Flag it to the author instead.
5. On hand-over, tell the author in a line or two which rules changed the post.

## 收納 (collect)

Run after **each round** of the author's edits to an AI-written post (in `post-write`, right after the `edit: 作者編修` commit), or when you find a post the author changed.

1. **Find the two versions.** AI draft: the last commit before the author's edits (in `post-write`, the parent of `edit: 作者編修`). Author version: the `edit: 作者編修` commit, uncommitted working-tree changes, or the published version. Posts are often in another worktree: `git worktree list`, then `git status` in each. Done when: `git diff` between them shows only the author's changes.
2. **Read the diff.** `git diff --word-diff <AI draft> <author version> -- <file>` (uncommitted: `git diff --word-diff` in that worktree).
3. **Classify every hunk:**
   - **Style**: different wording, tone, structure, title, a sentence removed, with the facts unchanged.
   - **Fact**: the author corrected content. Not a voice rule; don't repeat the mistake.
   - **One-off**: a choice that only holds for this post.
   Done when: every hunk has a class.
4. **Draft rules for the author**, grouped in three:
   - **新增規則**: a style the voice file doesn't cover yet. `<rule name>：<one positive sentence>`, which section it goes in (`所有文章` or a post type), and how it relates to existing rules (new / narrows `<rule>` / conflicts with `<rule>`).
   - **補例子**: the style fits an existing rule; name the rule.
   - **只屬這篇不收**: one-offs, and why they're not general.
   Each item carries its 改前 → 改後 example from this diff. Present them as a list the author can approve or reject item by item.
5. **Write only what the author approves**: rules under their section, examples under their rule (with date and post), one row in `收納紀錄`. Commit the voice file **as a separate commit in the same post PR** (e.g. `voice: 收納 <post>`); never mixed into the author-edit commit or the post's own changes. Nothing approved → no commit; say so in the PR.
