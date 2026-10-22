## Issue workflow

Issues move `status: raw` → (`status: needs-info`) → `status: ai-enhanced` → `status: approved`.
Only the author sets `status: approved`. Skills: `issue-enhance`, `issue-implement`, `article-request`.

- Verify command: `<fill in, e.g. npm test && npm run build>`
- Preview URL: `<fill in, or "none">`
- Low-risk paths: `.github/low-risk-paths.txt`
- Merge mode: `<auto | session>`
- Article target: `<owner>/<repo>`
- Issue assets branch: `issue-assets`
- Mockup path: `<N>/<file>` (inside the issue assets branch; `<N>` = issue number)
