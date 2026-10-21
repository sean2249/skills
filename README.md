# skills

Cross-project Claude Code skills.

## Install

In a Claude Code session:

```
/plugin marketplace add sean2249/skills
/plugin install sean-skills@sean-skills
```

Then turn on updates: run `/plugin`, open **Marketplaces**, select `sean-skills`, and choose **Enable auto-update**. Third-party marketplaces don't auto-update by default. The plugin has no `version`, so every new commit counts as an update. Without auto-update, pull changes with `/plugin marketplace update sean-skills`.

Skills load namespaced, e.g. `sean-skills:issue-enhance`.

## Skills

| Skill | Use when |
|---|---|
| `dev/issue-workflow-setup` | Installing (or repairing) the issue workflow in a repo: labels, callers for the shared workflows, PR template, CLAUDE.md section |
| `dev/issue-enhance` | Turning a `status: raw` issue into a reviewable plan (or an article outline), split into sub-issues |
| `dev/issue-implement` | Implementing a `status: approved` issue: PR with evidence, risk label, merge only `risk: low` |
| `dev/article-request` | Handing a merged `article` PR, or any file, to the article repo as a raw issue |
| `writing/article-write` | Writing an approved article issue as a devlog or intro, following the article repo's conventions |

## Shared workflows

`.github/workflows/issue-status.yml` and `risk-guard.yml` are reusable workflows (`on: workflow_call`). Repos set up with `issue-workflow-setup` call them through short callers, for example:

```yaml
jobs:
  risk-guard:
    uses: <owner>/skills/.github/workflows/risk-guard.yml@main
```

In the calling repo the required check is named `risk-guard / check`.
