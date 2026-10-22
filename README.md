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
  <img src="docs/workflow.svg" width="960" alt="Issue workflow: an issue goes from status: raw through issue-enhance and a Grill by fresh reviewer subagents (negotiated with the planner; disputes go to the author as A/B decisions with checkboxes in the issue body) to status: ai-enhanced and author approval; issue-implement opens a PR and runs code and security review, risk: low auto-merges and medium/high is merged by the author; work cards labelled article-status: request move to pending on merge (article-pending) and to handoff with article-request, which opens a post-type: article card in the article repo; that card runs the same flow and article-write writes it with a source map.">
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
    J --> RV["Review: code + security<br/>fix or justify · ≤ 3 rounds"]
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
      U["article-write<br/>devlog · intro · review · research + source map"]
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
| `writing/article-write` | Writing an approved article issue in one of four modes (devlog, intro, review, research), following the article repo's conventions, with a source map for note sources |

## Shared workflows

`.github/workflows/issue-status.yml`, `risk-guard.yml`, `article-pending.yml`, and `needs-info-reply.yml` are reusable workflows (`on: workflow_call`). `needs-info-reply` switches a `status: needs-info` issue back to `status: raw` once the author has answered: either the issue's author or the repo owner ticks a box for every decision in the body's `## Pending decisions` (`issues: edited`), or replies in a comment (`issue_comment: created`). It ignores PRs, bots, other users, and comments starting with `🤖 AI` (the AI writes decisions with empty boxes and never ticks one), and posts nothing. Repos set up with `issue-workflow-setup` call them through short callers, for example:

```yaml
jobs:
  risk-guard:
    uses: <owner>/skills/.github/workflows/risk-guard.yml@main
```

In the calling repo the required check is named `risk-guard / check`.

Callers pin `@main`: one change here reaches every repo on its next run. The trade-off is that these workflows can write issues, labels and PR comments, so a mistake on `main` hits every repo at once. To lock a repo, point its callers at a tag (`@v1`) or a full commit SHA (`@<sha>`). To upgrade later, review `gh api repos/<owner>/skills/compare/<old>...<new>` and bump the ref in all callers in one PR.
