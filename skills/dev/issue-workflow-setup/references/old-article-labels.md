# Old article labels

Read this only in repair mode, when Step 1 finds article labels from an earlier version (`article`, `article: pending`, `article: devlog`, `article-type: *`, …). It's part of Step 4 and runs before Step 5.

Article progress in a project repo is now one label, `article-status: request` → `pending` → `handoff`; an article issue in the article repo carries only `post-type: <mode>`. Renaming keeps the label on every issue/PR that has it:

| Old name | New name |
|---|---|
| `article` | `article-status: request` (see the article-repo note below) |
| `article: pending` | `article-status: pending` |
| `article: requested` | `article-status: handoff` |
| `article: devlog` | `post-type: devlog` |
| `article: intro` | `post-type: intro` |
| `article: review` | `post-type: review` |
| `article: research` | `post-type: research` |
| `article-type: devlog` / `intro` / `review` / `research` (briefly used name) | `post-type: devlog` / `intro` / `review` / `research` |

**`post-type:` labels exist only in the article repo** (the repo whose `Article target` is itself). So:

- **Article repo** → rename per the table.
- **Any other repo** → don't rename the type labels (`article: devlog` / `intro` / `review` / `research`, `article-type: *`, `post-type: *`); **delete** them instead. Unused ones go straight into the plan. For ones in use, list the affected issues/PRs in Step 3 and delete after the author confirms (those cards should use `article-status: request` instead). In this case run only the first two `mv_label` lines below, then step 2 (where every `article` is progress → `article-status: request`).

```bash
for l in "article: devlog" "article: intro" "article: review" "article: research" \
         "article-type: devlog" "article-type: intro" "article-type: review" "article-type: research" \
         "post-type: devlog" "post-type: intro" "post-type: review" "post-type: research"; do
  grep -qxF "$l" <<<"$(gh label list --limit 200 --json name --jq '.[].name')" || continue
  echo "$(gh issue list --state all --label "$l" --limit 500 --json number --jq length) issues, $(gh pr list --state all --label "$l" --limit 500 --json number --jq length) PRs  $l"
done
```

1. **Rename everything except `article`** (article repo: all lines; other repos: only the two `article-status:` lines):

```bash
existing=$(gh label list --limit 200 --json name --jq '.[].name')
mv_label() {
  grep -qxF "$1" <<<"$existing" || return 0                      # old name absent: nothing to do
  if grep -qxF "$2" <<<"$existing"; then echo "BOTH exist: $1 / $2 (handle by hand)"; return; fi
  gh label edit "$1" --name "$2"
}
mv_label "article: pending"   "article-status: pending"
mv_label "article: requested" "article-status: handoff"
mv_label "article: devlog"    "post-type: devlog"
mv_label "article: intro"     "post-type: intro"
mv_label "article: review"    "post-type: review"
mv_label "article: research"  "post-type: research"
mv_label "article-type: devlog"   "post-type: devlog"
mv_label "article-type: intro"    "post-type: intro"
mv_label "article-type: review"   "post-type: review"
mv_label "article-type: research" "post-type: research"
```

2. **Then `article`.** In the article repo, `article` on an article issue is a "this is an article issue" marker, not progress. `post-type:` replaces it. Split its issues/PRs:

```bash
gh issue list --state all --label article --limit 500 --json number,labels \
  --jq '.[] | select([.labels[].name | startswith("post-type: ")] | any) | .number'   # markers
gh issue list --state all --label article --limit 500 --json number,labels \
  --jq '.[] | select([.labels[].name | startswith("post-type: ")] | any | not) | .number' # progress
gh pr list --state all --label article --limit 500 --json number --jq '.[].number'      # PRs: progress
```

- Markers → remove `article` from them (`gh issue edit <N> --remove-label article`).
- Progress items left → `mv_label "article" "article-status: request"`. Nothing left (typical for the article repo) → delete `article` (`gh label delete article --yes`); recommended there, since `post-type:` is enough.

If both an old and a new name already exist, don't rename. Add the new label to each issue/PR that has the old one, then delete the old label after the author confirms. List everything found (old labels, marker vs progress issues) in the Step 3 plan for confirmation.
