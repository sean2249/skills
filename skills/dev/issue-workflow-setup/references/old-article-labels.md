# Old article labels

Read this only in repair mode, when Step 1 finds article labels from an earlier version. It's part of Step 4 and runs before Step 5.

From v4 there are no article **progress** labels: an article starts when the author runs `/article-request`, best in the session where the work happened. An article issue in the article repo carries only `post-type: <mode>`.

## Progress labels: delete

`article`, `article: pending`, `article: requested`, `article-status: request`, `article-status: pending`, `article-status: handoff`.

1. List the open issues and PRs, and the merged PRs, that still carry `article-status: request` / `pending` (or `article` / `article: pending`). Those are articles the author wanted and hasn't handed over yet. Put them in the Step 3 plan, so the author can still hand over any they want: a merged PR with `/article-request <PR>`; open work by running `/article-request` in the session that finishes it.
   ```bash
   for l in "article-status: request" "article-status: pending" article "article: pending"; do
     gh issue list --state all --label "$l" --json number,title,state --jq '.[] | "issue #\(.number) \(.state) \(.title)"'
     gh pr list --state all --label "$l" --json number,title,state --jq '.[] | "PR #\(.number) \(.state) \(.title)"'
   done
   ```
2. After the author confirms, delete the labels (`gh label delete "<label>" --yes`). Deleting a label removes it from every issue and PR.

In the article repo, an `article` label on an issue that already has a `post-type:` label is only a "this is an article issue" marker: deleting it loses nothing.

## Type labels: rename in the article repo, delete elsewhere

| Old name | New name |
|---|---|
| `article: devlog` / `article-type: devlog` | `post-type: devlog` |
| `article: intro` / `article-type: intro` | `post-type: intro` |
| `article: review` / `article-type: review` | `post-type: review` |
| `article: research` / `article-type: research` | `post-type: research` |

- **Article repo** (its `Article target` is itself): rename per the table. Renaming keeps the label on every issue and PR that has it. If both the old and the new name exist, add the new label to each issue/PR with the old one, then delete the old one after the author confirms.
- **Any other repo**: `post-type:` labels exist only in the article repo, so delete the type labels (`article: <type>`, `article-type: <type>`, `post-type: <type>`). For ones in use, list the affected issues/PRs in Step 3 and delete after the author confirms.

```bash
# how many issues and PRs carry each old label
for l in article "article: pending" "article: requested" \
         "article-status: request" "article-status: pending" "article-status: handoff" \
         "article: devlog" "article: intro" "article: review" "article: research" \
         "article-type: devlog" "article-type: intro" "article-type: review" "article-type: research"; do
  gh label list --limit 200 --json name --jq '.[].name' | grep -qxF "$l" || continue
  echo "$(gh issue list --state all --label "$l" --limit 500 --json number --jq length) issues, $(gh pr list --state all --label "$l" --limit 500 --json number --jq length) PRs  $l"
done
# rename (article repo only)
gh label edit "article: devlog" --name "post-type: devlog"
```
