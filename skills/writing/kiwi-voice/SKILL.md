---
name: kiwi-voice
description: Use to apply, grow or consolidate the author's writing voice in a blog repo. Three branches. 套用 (apply): before handing over any post you wrote or edited (post-write runs it before the author edits), check the draft against the repo's voice rules file rule by rule. 收納 (collect): after each round of the author's edits to an AI-written post, compare the AI draft with the author's version and propose rules or examples for the author to approve. 整併 (consolidate): when the rules file is over its size limit (checked at the start of every 收納) or the author asks, propose merging, generalising or retiring rules and resolving rule/example conflicts. Holds only the process; the rules live in each repo's voice files, named in its CLAUDE.md.
---

# kiwi-voice

This skill is the process only. The voice lives in **two places per repo**, named in the repo's `CLAUDE.md` (`## Article conventions`):

- **Rules file** — `Voice file: <path>` (e.g. `docs/voice.md`). Only rules, each with at most 3 representative examples. 套用 reads only this file.
- **Examples directory** — `Voice examples: <path>`. Optional; default is the rules file's path without `.md` plus `-examples/` (e.g. `docs/voice-examples/`). Every other example, one file per rule. Read only in 收納 and 整併, or when a rule's meaning is unclear.

Read the rules there and write them there; never keep rules in this skill.

**Find the voice files first.** No `Voice file:` line, or the file doesn't exist → ask the author where it is (or whether to start one, in the structure below). Don't guess. A missing examples directory is fine; create it when the first example moves there.

**Precedence.** The author's own sentences win over everything. The voice file wins over other writing skills and the repo's conventions. Inside the voice file, **a rule wins over its examples**: an example that contradicts its rule is a defect to fix in 整併, not a reason to bend the rule.

**AI finds, the author decides.** Whenever rules conflict with each other, with an example, or with a new edit, your job is to find it and lay out the options. Don't pick one, don't resolve it silently.

**Voice changes get their own PR.** Every voice commit (`voice: 標記待整併`, `voice: 整併`, `voice: 收納 <post>`) goes on a branch of its own from the default branch, `voice/<post slug>`, never on the post's branch. A worktree keeps the post branch checked out while you do it: `git worktree add ../voice-<post slug> -b voice/<post slug> origin/<default-branch>`. Open one PR for it after the round's last voice commit, with `Refs #<N>` (not `Closes`, so the post issue stays open) and the approved items in the body, risk classified from its files as in `issue-ship` Step 3, and leave it for the author to merge. Two reasons: the rules file shapes every later post, so a rule change deserves a review of its own rather than riding inside one post; and a post PR can only be `risk: low` while every file is in the blog's low-risk allowlist, which lists posts, not the voice files. Tell the author the voice PR's link so the post PR can name it.

## Size limit

Default: the rules file stays under **8 KB** and **25 rules**. A repo can override either in `CLAUDE.md` with `Voice limits: <KB> KB / <N> rules`.

Measure: `wc -c <rules file>` for size, `grep -c '^### ' <rules file>` for rules. Over either limit → 整併 before any new rule is added (see 收納 step 1).

## Voice file structure

Rules file:

```markdown
# <blog> 寫作風格（voice）

## 所有文章
### <rule name>：<one positive sentence: how to write>
- 改前 → 改後（<YYYY-MM-DD>, <post>）
- <at most 3 examples, each showing a different facet>
- 再次確認 <N> 次（最後：<YYYY-MM-DD>, <post>）

## <post type or group of types>
<!-- rules that only hold for some post types -->
```

Section names are the voice file's own (e.g. one section per `post-type:`, or `技術文章` / `其他文章`). Use the section that covers the post's type; if none matches by name, use the closest and say which.

Examples directory: one file per rule, `<rule name>.md`, a flat list of `- 改前 → 改後（<YYYY-MM-DD>, <post>）`. The rules file's examples aren't repeated there.

No log table: the history is git. Every 收納 is one commit `voice: 收納 <post>`, every 整併 one commit `voice: 整併`. `git log --oneline -- <rules file>` is the record.

A voice file still in the old layout (a `收納紀錄` table, or more than 3 examples per rule) is converted by its next 整併: extra examples move to the examples directory, the table is dropped.

## 套用 (apply)

Run before handing over any post, new or revised.

1. Read the whole rules file (not the examples directory). Done when: you can say what each rule governs.
2. Settle the draft's content and facts first.
3. Check the draft against every rule in `所有文章`, and every rule in the section for this post's type. Fix what doesn't fit. Done when: every rule was checked and you can list which rules changed which sentences.
4. **Rule and example disagree** → follow the rule, and append `（待整併：<one line on the mismatch>）` to that example. Commit it on its own (`voice: 標記待整併`) on the voice branch, never mixed with the post.
5. **Keep the author's own words.** Sentences the author already edited stay exactly as they are, slang and typos included. When the post is transcribed from the author's own note (a vault or personal note), you may adjust wording, but **never delete a sentence the author wrote**, even if a rule (e.g. 重複) seems to call for it. Flag it to the author instead.
6. On hand-over, tell the author in a line or two which rules changed the post, and any example you marked 待整併.

## 收納 (collect)

Run after **each round** of the author's edits to an AI-written post (in `post-write`, right after the `edit: 作者編修` commit), or when you find a post the author changed.

1. **Check the size limit.** Measure the rules file. Over → run 整併 first and commit it; then continue. Still over after 整併 (the author rejected enough of it) → this round adds no new rules: propose them as **暫緩** so the author sees them, but don't write them.
2. **Find the two versions.** AI draft: the last commit before the author's edits (in `post-write`, the parent of `edit: 作者編修`). Author version: the `edit: 作者編修` commit, uncommitted working-tree changes, or the published version. Posts are often in another worktree: `git worktree list`, then `git status` in each. Done when: `git diff` between them shows only the author's changes.
3. **Read the diff.** `git diff --word-diff <AI draft> <author version> -- <file>` (uncommitted: `git diff --word-diff` in that worktree).
4. **Classify every hunk:**
   - **Style**: different wording, tone, structure, title, a sentence removed, with the facts unchanged.
   - **Fact**: the author corrected content. Not a voice rule; don't repeat the mistake.
   - **Private**: the author removed something that shouldn't be public (a name, a private project, a personal detail). Not a voice rule, and its words never go into an example: the voice files are read in full for every later post, and git keeps them even after a later edit. Unsure whether a removal was style or privacy → ask the author.
   - **One-off**: a choice that only holds for this post.
   Done when: every hunk has a class.
5. **Match each style hunk against the rules file**, reading the rule's examples file when needed:
   - Not covered by any rule → **新增規則**.
   - Fits a rule and shows a facet its examples don't → **補例子**.
   - Fits a rule and its existing examples already show the same thing → **再次確認**.
   - Goes against a rule → **衝突**. Never a new rule.
6. **Draft the proposal for the author**, grouped:
   - **新增規則**: `<rule name>：<one positive sentence>`, which section it goes in, and the 改前 → 改後 from this diff.
   - **補例子**: the rule, the new example, and where it goes. Rule has fewer than 3 examples → add it. Already 3 → name the weakest one it replaces; the replaced one moves to the examples directory. Only a new facet earns a place; never add one just because it's newer.
   - **再次確認**: the rule; its `再次確認` line goes up by one, with this post as the latest. No new example.
   - **衝突**: the rule, the edit, and these options, with no recommendation: 縮小規則範圍 (rewrite the rule so it no longer covers this case) / 加例外 (keep the rule, add `例外：…`) / 舊規則退場 (remove the rule; this edit may become a new rule) / 只算這篇的特例 (change nothing).
   - **暫緩** (only when step 1 left it over the limit): new rules not written this round.
   - **只屬這篇不收**: one-offs, and why they're not general.
   Every 改前 is quoted from the AI draft, which may hold details the author then cut. Keep only the words that show the change, and replace anything the published post doesn't contain with `…`, so an example never publishes what the post left out.
   Present them as a list the author can approve or reject item by item.
7. **Write only what the author approves**: rules under their section, examples under their rule, displaced examples into `<examples dir>/<rule name>.md`. Commit the voice files **on the voice branch** (see the top): `voice: 收納 <post>`. Never mix it into the author-edit commit or the post's own changes. Nothing approved → no commit and no voice PR; say so in the post PR.

## 整併 (consolidate)

Run when 收納 step 1 finds the rules file over its limit, when the author asks, or when examples are marked 待整併. Its result is always its own commit, `voice: 整併`, never mixed with 收納.

1. **Read both.** The whole rules file and every file in the examples directory. Note the current size and rule count against the limit.
2. **Find candidates**:
   - **合併**: two or more rules that govern the same thing. Propose the merged `<rule name>：<sentence>`; their examples pool, the best 3 stay in the rules file.
   - **收斂成原則**: several narrow rules (or one rule full of special cases) that one general sentence covers. Propose that sentence.
   - **退場**: rules not confirmed for a long time: 10 or more `voice: 收納` commits since the rule's latest example or `再次確認` date (`git log --oneline --since=<that date> --grep='^voice: 收納' -- <rules file> | wc -l`).
   - **規則互相衝突**: two rules that call for opposite things. Options: merge them, or write the order (`<rule A> 優先於 <rule B>`, or when each applies).
   - **例子不符**: check **every example**, in both files, against its rule; include every `待整併` mark. Options for each: move it to the rule it does fit / delete it / change the rule so it fits (which is a rule change; say so).
   - **舊格式**: a `收納紀錄` table → drop it (git has the history). More than 3 examples on a rule → keep the 3 that show the most different facets, move the rest to the examples directory.
3. **Present a checklist**, one item per candidate, each with its before → after text and its options when it has more than one. Don't choose between options. End with the size and rule count if everything were approved. Done when: the author has ticked or rejected every item.
4. **Apply only what was approved.** Moved examples keep their date and post. A retired rule's examples file is deleted with it (git keeps it). Merged rules' examples files are merged into one.
5. **Commit** `voice: 整併` (on the voice branch, before that round's `voice: 收納`). Report the new size and rule count. Still over the limit → say so; 收納 then holds new rules as 暫緩.
