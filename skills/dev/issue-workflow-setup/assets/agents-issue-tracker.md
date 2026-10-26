## This repo's workflow

Added by `issue-workflow-setup`, alongside the conventions above.

- **Create an issue with its labels in the same call.** The `issue-status` Action gives `status: raw` to a new issue that has no `status:` label yet, so a label added afterwards would sit beside it. `/to-spec` and `/to-tickets` create the spec and its tickets with `status: approved`: the author agreed to them in the session.
- **A spec replaces an existing issue**: when `/to-spec` writes up work that started as an issue, comment on that issue `Superseded by #<spec>` and close it.
- **Only the repo owner's issues are worked on.** Issues labelled `external` are left to the owner.
- **Article cards are `post-write`'s.** Issues with a `post-type:` label skip `/triage`: the author says 「請看 #N」 and `post-write` drafts the outline.
- **Shipping**: after `/implement` or `/implement-spec`, run `issue-ship` to open the PR, review it, label its risk and merge it when it's low.
