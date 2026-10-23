# skills

Cross-project Claude Code skills.

## Install

In a Claude Code session:

```
/plugin marketplace add sean2249/skills
/plugin install kiwi-skills@kiwi-skills
```

Then turn on updates: run `/plugin`, open **Marketplaces**, select `kiwi-skills`, and choose **Enable auto-update**. Third-party marketplaces don't auto-update by default. The plugin has no `version`, so every new commit counts as an update. Without auto-update, pull changes with `/plugin marketplace update kiwi-skills`.

Skills load namespaced, e.g. `kiwi-skills:issue-enhance`.

### Migrating from the old name

The plugin and its marketplace used to be called `sean-skills`. If you installed it under that name, re-add it under the new one (in a shell):

```bash
claude plugin marketplace remove sean-skills
claude plugin marketplace add sean2249/skills
claude plugin install kiwi-skills@kiwi-skills
```

Then turn on auto-update for `kiwi-skills` as above.

## Workflow

This is my personal development workflow. The skills are designed around it, so adjust it to your own habits if you use them.

<p align="center">
  <img src="docs/workflow.svg" width="960" alt="Issue workflow: an issue goes from status: raw through issue-enhance and a Grill by fresh reviewer subagents (negotiated with the planner; disputes go to the author as A/B decisions with checkboxes in the issue body) to status: ai-enhanced and author approval; issue-implement opens a PR and runs code and security review (up to 3 rounds; round 3's findings are all fixed with no further review), risk: low auto-merges and medium/high is merged by the author; work cards labelled article-status: request move to pending on merge (article-pending) and to handoff with article-request, which opens a post-type: article card in the article repo; that card runs the same flow and post-write writes it with a source map.">
</p>

Highlighted nodes (glowing in the image, yellow in the text version) are where the author steps in: ticking a box for each pending decision in the issue body (needs-info questions and the Grill's A/B items; never asked in chat), approving an issue, reviewing and merging `risk: medium` / `high` PRs, and merging article PRs. Everything else is done by the skills or GitHub Actions. The image follows your system's light/dark setting, and its animation stops if you've asked your OS for reduced motion.

<details>
<summary>Text version (mermaid)</summary>

```mermaid
flowchart TD
  subgraph ISSUE["1 · Issue (any repo)"]
    A(["Author opens an issue"]):::author --> B["status: raw<br/>(added by the issue-status Action)"]
    B --> C["issue-enhance<br/>check code · settle scope"]
    C -->|missing info| D["status: needs-info<br/>decisions in the issue body"]
    D --> E(["Author ticks a box<br/>per decision"]):::author
    E -->|"ticked → auto back to raw<br/>(needs-info-reply)"| B
    C -->|too big| F["Split into native sub-issues<br/>ordered with blocked-by"]
    C --> P["Write the plan"]
    F --> P
    subgraph GRILL["Grill (optional) · up to 3 rounds · fresh reviewers each round"]
      R1["Reviewer subagents<br/>2–4 angles · parallel · fresh context"] --> R2["Negotiate with the planner<br/>agree → change · withdraw · for author"]
      R2 --> R3(["A / B tables in the issue body<br/>author ticks · no planner recommendation"]):::author
    end
    P -->|"grill label or<br/>high-risk paths"| R1
    P -->|default| G
    R3 --> G["status: ai-enhanced<br/>plan (+ Risks / Opportunities if grilled)"]
    G --> H(["Author approves<br/>sets status: approved"]):::author
  end

  subgraph IMPL["2 · Implementation"]
    H --> I["issue-implement (new session)<br/>applies risk mitigations"]
    I --> J["PR with evidence + behaviour summary"]
    J --> RV["Review: code + security<br/>fix or justify · ≤ 3 rounds<br/>round 3: fix all, no re-review"]
    RV --> K{"risk label<br/>(unfixed security → not low)"}
    K -->|"risk: low<br/>allowlist · risk-guard / check"| L["Auto-merge"]
    K -->|"risk: medium / high"| M(["Author reviews and merges"]):::author
  end

  subgraph ART["3 · Article"]
    L --> N{"Work card has<br/>article-status: request?"}
    M --> N
    N -->|no| Z["Done"]
    subgraph WORK["Work card · article-status: (project repo)"]
      O["article-pending<br/>article-status: request → pending · reminder"]
      Q["article-request<br/>pending → handoff · opens a post-type: card"]
      X["Any file<br/>(e.g. a notes page)"]
    end
    subgraph CARD["Article card · post-type: (article repo only)"]
      S["Article card<br/>post-type: devlog / intro / review / research<br/>outline → Grill → approved"]
      U["post-write<br/>devlog · intro · review · research + source map<br/>kiwi-voice 套用 → author edits → 收納 → PR"]
      V(["Author merges the article<br/>checks the source map"]):::author
    end
    N -->|yes| O
    O --> Q
    X --> Q
    Q --> S
    S --> U
    U --> V
  end

  classDef author fill:#fde68a,stroke:#b45309,color:#1f2937,stroke-width:2px
```

</details>

### How I run it

This is how I personally operate the workflow day to day: parallel child sessions, with GitHub issues as the only handoff. It needs no extra skill. The parallelism comes from asking Claude, in a main session, to start child sessions.

<p align="center">
  <img src="docs/operating.svg" width="960" alt="How the author runs the workflow: a main session picks a batch of about three raw issues and starts one child session per issue running issue-enhance; children write plans and Pending decisions into the issue bodies and never talk to each other. The main session reports what waits; the author reviews, ticks boxes and approves (adding article-status: request for articles). A new main session picks approved, unblocked issues (at most one or two per repo) and starts child sessions running issue-implement, which open PRs. The author merges; an Action sets article-status: pending; the author runs article-request in the main session, which opens a post-type: article card in the article repo that goes through the same steps.">
</p>

1. **Main session:** find `status: raw` issues and start one child session per issue running `issue-enhance`. Each batch is only as many as I can review in a day or two (about 3).
2. **Child sessions** write each plan into its issue body; decisions for me go in `## Pending decisions` as checkboxes. Children never talk to each other: the issue (labels + body) is the only handoff.
3. **Main session** reports what waits for me: `status: ai-enhanced` (review the plan), `status: needs-info` (tick the boxes), and PRs to look at.
4. **I review**, set `status: approved`, and add `article-status: request` to anything that should become an article.
5. **A new main session** picks approved issues, skips any blocked by an open issue, takes at most 1–2 per repo at a time, and starts a child session per issue running `issue-implement`. Each opens a PR with screenshots, preview, behaviour summary and review.
6. **I look and merge.** The Action switches the label to `article-status: pending`.
7. **I run `article-request` in the main session.** The AI suggests a `post-type:` with its reasoning and I confirm, which opens an article card in the article repo. It can also start from any file, such as a notes page.
8. **The article card goes back to step 1:** `issue-enhance` drafts the outline, I approve, a child session runs `post-write` and hands me the draft; I edit it in place and say I'm done, the AI commits my edits and opens the PR, and I check the preview and merge.

<details>
<summary>Text version (mermaid)</summary>

```mermaid
flowchart TD
  subgraph MAIN["Main session"]
    M1["Pick raw issues<br/>a batch of ~3 (1–2 days of review)"]
    M2["Report what waits<br/>ai-enhanced · needs-info · PRs"]
    M3["New session: pick approved<br/>skip blocked · ≤ 1–2 per repo"]
    M5["article-request<br/>AI suggests post-type + reasons; author confirms"]
  end
  subgraph CHILD["Child sessions · one per issue, in parallel"]
    C1["issue-enhance ×3<br/>plan into the issue body"]
    C3["issue-implement ×1–2<br/>PR · screenshots · preview · summary · review"]
  end
  subgraph BOARD["GitHub issues & labels · the handoff board"]
    B1["Plan in the body<br/>ai-enhanced, or needs-info + ☐ decisions"]
    B2["status: approved<br/>+ article-status: request"]
    B3["Pull request"]
    B4["Merged<br/>Action sets article-status: pending"]
    B5["Article card<br/>post-type: · article repo · back to step 1 → post-write"]
  end
  A2(["Author: review · tick · approve"]):::author
  A4(["Author: look at it · merge"]):::author
  A5(["Author: confirm post-type · merge the article"]):::author

  M1 --> M2 --> M3 --> M5
  M1 -->|spawn| C1 -->|write| B1
  B1 --> A2 -->|approve| B2
  B2 -->|pick| M3
  M3 -->|spawn| C3 --> B3
  B3 --> A4 -->|merge| B4
  B4 -->|pending| M5
  X["Any file<br/>(e.g. a notes page)"] -->|or a file| M5
  M5 -->|opens| B5 --> A5

  classDef author fill:#fde68a,stroke:#b45309,color:#1f2937,stroke-width:2px
```

</details>

### Labels

| Label | Where | Meaning |
|---|---|---|
| `status: raw` → `needs-info` → `ai-enhanced` → `approved` | every repo | Issue progress; only the author sets `approved` |
| `risk: low` / `medium` / `high` | every repo, on PRs | Merge gate; only `low` merges automatically |
| `grill` | every repo, on issues | The author asks `issue-enhance` to run the optional Grill review (it also runs automatically when a plan touches high-risk paths) |
| `article-status: request` → `pending` → `handoff` | project repos (including the article repo's own feature cards) | This work should become an article, and how far the handoff got |
| `post-type: devlog` / `intro` / `review` / `research` | **article repo only**, on article cards | How the article is written; never used in other repos |

## Skills

| Skill | Use when |
|---|---|
| `dev/issue-workflow-setup` | Installing (or repairing) the issue workflow in a repo: labels, callers for the shared workflows, PR template, CLAUDE.md section |
| `dev/issue-enhance` | Turning a `status: raw` issue into a reviewable plan (or an article outline), split into sub-issues |
| `dev/issue-implement` | Implementing a `status: approved` issue: PR with evidence, risk label, merge only `risk: low` |
| `dev/article-request` | Handing a merged `article-status: pending` PR, or any file, to the article repo as a raw issue; marks the PR `article-status: handoff` |
| `writing/post-write` | Writing an approved article issue in one of four modes (devlog, intro, review, research), following the article repo's conventions, with a cover, blog links for `wiki:` targets, and a source map for note sources; hands the draft to the author to edit before opening the PR |
| `writing/kiwi-voice` | Applying the repo's voice file to a post (套用), and after the author's edits proposing new voice rules for the author to approve (收納). Rules live in each repo's voice file, not in the skill |

## Shared workflows

`.github/workflows/issue-status.yml`, `risk-guard.yml`, `article-pending.yml`, and `needs-info-reply.yml` are reusable workflows (`on: workflow_call`). `needs-info-reply` switches a `status: needs-info` issue back to `status: raw` once the author has answered: either the issue's author or the repo owner ticks a box for every decision in the body's `## Pending decisions` (`issues: edited`), or replies in a comment (`issue_comment: created`). It ignores PRs, bots, other users, and comments starting with `🤖 AI` (the AI writes decisions with empty boxes and never ticks one), and posts nothing. Repos set up with `issue-workflow-setup` call them through short callers, for example:

```yaml
jobs:
  risk-guard:
    uses: <owner>/skills/.github/workflows/risk-guard.yml@main
```

In the calling repo the required check is named `risk-guard / check`.

Callers pin `@main`: one change here reaches every repo on its next run. The trade-off is that these workflows can write issues, labels and PR comments, so a mistake on `main` hits every repo at once. To lock a repo, point its callers at a tag (`@v1`) or a full commit SHA (`@<sha>`). To upgrade later, review `gh api repos/<owner>/skills/compare/<old>...<new>` and bump the ref in all callers in one PR.
