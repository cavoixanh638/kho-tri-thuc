# Notes UX integration — 20/11/2026

Status: IN_PROGRESS. User authorized integration and joint tests, **no PR merge
and no Windows deployment**. Branch: codex/notes-ux-integration.

Baseline main: 7044b4a0f50a7c831a391f27b1f90cc4aaa21d8b.
Inputs PR48–56 pinned in Git history; combined source code at 5576d84.
Source PRs remain open and unmerged. This branch is a review candidate only.

Owners and acceptance:
- Root: host editor/template/illustration glue, joint API/UI regression,
  isolated PostgreSQL full suite/readiness/restore, integration PR and CI.
- ux_ci: automatic frontend test discovery and portable Docker fixtures,
  all frontend unit tests/build; notes-ux-ci branch.
- ux_viewer: owner/version checked private Range endpoint and source viewer
  binding, tests with synthetic storage; notes-ux-viewer branch.
- ux_review: gated provider-free review host and version-safe API integration,
  tests; notes-ux-review branch. No paid/external AI.

Completion: one integration PR containing all code, automated unit/build
checks, authenticated joint capture/edit/template/backlink/view/review flows,
source byte Range ownership/version checks, consistent backup/restore evidence,
latest-head CI PASS, explicit external gaps. No production data or credentials.

Current tests: NOT_RUN on combined tree. Individual PR evidence remains
historical and does not establish combined PASS.
Next: implement independent glue/runner/source delivery, cherry-pick worker
commits, run joint suites and resolve failures, push evidence and open PR.
