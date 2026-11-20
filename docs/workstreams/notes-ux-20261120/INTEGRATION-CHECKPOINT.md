# Notes UX integration — 20/11/2026

Status: CODE_AND_LOCAL_QA_PASS; awaiting latest-head CI on PR57.
User authorized integration and joint tests, **no PR merge and no Windows
deployment**. Branch: codex/notes-ux-integration.

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

Implemented: all worker commits integrated, host template/review/asset callbacks
connected, authenticated versioned Range endpoint, automatic11-suite runner
and canonical Docker fixtures. No new dependencies or migrations.
Behavior tested04cd942; final UI testedec1cdd3 (only layout/contrast after it).
PASS:231frontend;257backend (2native opt-ins separately PASS); real built-app
HTTP/browser flows;43native media seekmarks;10000Item integrity and15collection
restore;40template-note dump/restore; visual inspector0FAIL0WARN at3widths.
See INTEGRATION-EVIDENCE.md and machine reports for commands/limits.

PR57 is the combined review candidate; original PR48–56 remain unmerged.
CI04cd942 run44763047791 SUCCESS; final evidence-only HEAD creates a new run.
Next: verify that exact PR57 HEAD CI completes successfully, record final run in
PR body, mark ready for review. Do not merge, auto-merge or deploy.
External boundaries remain Drive production/PDF navigation/Android/AIprovider/
100GB media. Review stays default-off PoC with stateless signed receipts.
Private synthetic QA DBs/bundles are outside Git; no credentials or personal data.
