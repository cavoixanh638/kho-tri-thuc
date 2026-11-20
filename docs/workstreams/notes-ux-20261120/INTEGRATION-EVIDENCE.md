# KT-114–121 joint integration acceptance — 20/11/2026

[Integration PR57](https://github.com/cavoixanh638/kho-tri-thuc/pull/57)
contains PR48–56 by cherry-pick, including PR56's dependency on PR51. Main stays
7044b4a0f50a7c831a391f27b1f90cc4aaa21d8b. No source PR was merged or changed.
No Windows runtime, production DB, Google account or AI provider was used.

## Implemented integration

- The real ItemScreen editor exposes four optional Markdown templates in a
  disclosure. Selection previews only; explicit apply compares the latest raw
  draft, appends without replacing it, and waits for the normal atomic save.
- Related evidence and source citations focus the exact attached Asset UUID.
  Internal Markdown links use the same-tab item route. Versioned PATCH rejects
  stale edits without replacing drafts, history or original assets.
- Opt-in manual suggestion review is mounted in ItemScreen, disabled during
  draft editing, with preview/accept/reject/cancel/undo and current note/version/
  updated_at acknowledgement. Default flag is zero. The UI explicitly says
  manual proposal and no AI provider; no synthetic AI results appear by default.
- Source citations resolve private, version/hash-pinned same-origin media
  descriptors on explicit action. Bounded Range reads verify remote provenance
  before/after each read, cap at4MiB, reject remote redirects and credentials in
  UI, and require owner/nondeleted/verified originals.
- npm test discovers all11 DOM/unit suites. Docker uses the two canonical
  backend corpora without duplication. GitHub CI builds those actual images,
  runs the discovered suites, migration round trips, worker/API/capture/upload
  smoke and fresh-DB backup/restore.

## Evidence tied to code

Behavior code/tested SHA:04cd9427ff48ed912b2606ef4a55afca82741943.
Final UI code/tested SHA:ec1cdd323b911d327c8bdd6c48733656f131aa25
adds only tablet layout/menu and disabled-text contrast fixes. Evidence-only
commits follow. The final PR check must be read at its actual head, not inferred
from an earlier green SHA.

| Check | Actual result / limits |
| --- | --- |
| Frontend default runner |231 PASS,0 FAIL,0 SKIP across11 discovered suites; no uncaught TypeError/ReferenceError in final log. Includes6 joint editor/template/conflict/asset-focus flows and8 review-host cases. |
| Full PostgreSQL backend |259 discovered:257 PASS,2 explicit opt-in skips; no failures. FFmpeg9.0.2 available via PATH. Optional skipped native tests were executed separately below. |
| Joint HTTP workflow |2 PASS: capture/retry→template-shaped note→version conflict→manual preview/accept/undo→backlink→read/export; preserves exact Unicode/CRLF, Event raw/time, Item UUID, Asset and pinned groups. |
| Native template restore |2 PASS with KT121_RESTORE=1:40/40 notes and15 collections identical after pg_dump/fresh pg_restore; dump SHA865bff859689ca69bab17b7284e87f4c4b0959feae20ab504ad632e3e5b27b89. Private archive removed by test; no restore overwrite. |
| Native authenticated viewer |23 WAV+20 VP8 seek targets, maximum error0s (tolerance1s), including audio24/26/28s after first4MiB;6 real206 probes; unauthenticated401. Actual Django API/session, synthetic StoragePort only. [Report](INTEGRATION-VIEWER-BROWSER.json). |
| Actual built app browser |Real Chrome/native input with Django session/CSRF and PostgreSQL: login/capture/template/save/reload/Vietnamese Ctrl+Enter/review/undo/backlink PASS. Four library modes show the same2 actual API Item IDs at1440/768/390. [Report](INTEGRATION-BROWSER.json). |
| Final visual inspection |After fixing clipped tablet menu and disabled review contrast:0 FAIL/0 WARN at1440/768/390. [Measurements](INTEGRATION-INSPECTION.json). Source lint0 FAIL/0 WARN. |
|10000 Item readiness/restore |PASS:138 tree nodes,221 paginated service reads,zero missing/duplicate IDs, pinned rows unchanged, retry creates0 extra Events, all15 restored collection hashes match. Source/restore DBs are new QA DBs; [machine report](INTEGRATION-READINESS.json). |
| Build/checks |TypeScript/Vite PASS; Django check/makemigrations--check PASS; changed integration Python Ruff check/format from repo root PASS; readiness isolation3 PASS; git diff--check PASS. Existing bundle warning708.51kB remains. |

Native environment: Windows, Python3.13/Django5.2/PostgreSQL18, Node24,
Chrome157.0.8103.79, FFmpeg9.0.2. Separate loopback QA PostgreSQL62224;
temporary actual built-app server62300. The Windows production service8009
and its PostgreSQL54329 were not used. No worker ran against browser fixtures.
Synthetic capture jobs therefore correctly remain pending, rather than claiming
classification or Drive completion.

Screenshots are synthetic QA data from the actual integrated application:
[1440](integration-editor-1440.png), [768](integration-editor-768.png),
[390](integration-editor-390.png). Style retains the existing achromatic ledger
direction, palette/type/shell (seed236088050, no redraw/new assets/dependencies).
Question: can I read and safely edit my text while retaining its sources?
The text editor is primary; template/review/source tools remain optional.

## Reproduction

Use a full repo checkout and installed pinned requirements. Environment secrets
belong outside Git. Run from apps/web: npm test and npm run build.
Run from apps/backend with an isolated QA DSN: python manage.py test --noinput -v1.
Native restore opt-in is hard-guarded to test_kt121/test_kt121_restore; native
viewer browser opt-in is guarded to QA62224 and test_kt_ux_viewer*.
Exact native viewer command is in [viewer evidence](INTEGRATION-VIEWER.md).

The repeatable joint browser driver is tools/smoke/notes_ux_browser.mjs; it
requires a new empty synthetic account, KT_UX_BROWSER_URL=http://127.0.0.1:62300,
KT_UX_BROWSER_USER/PASSWORD, KT_UX_CDP_MODULE pointing to the installed
design-taste skill's CDP helper, and a temporary actual build/API QA server.
It has no mocked fetch and refuses any other base URL. Browser textareas use
LF natively; backend fixtures independently cover exact CRLF/NFD/emoji.
Visual measurements reuse the skill probe/layout/app rules in the logged-in
browser; production screenshot paths are not substituted for QA evidence.

Readiness command from repo root: python tools/readiness/run.py --work-dir
<new-private-directory-outside-repo> --report <report.json>, with
KT_READINESS_PASSWORD and PostgreSQL binaries in PATH. The guarded harness
creates two new marked QA DBs. The report contains safe row hashes only; dump,
portable manifest and synthetic original stay outside Git. The local private
receipt can resume or explicitly clean these fixtures; no credentials in Git.

## Remaining external / conditional boundaries

- Production Drive Range latency/quota/permission changes, private native PDF
  page navigation, Android/native IME, other codecs and100GB media are NOT_RUN.
  PDF pageNavigationVerified stays false; original-source fallback remains.
- AI provider/model/cost/data policy are not configured. Provider-free review
  is a gated PoC. Reject/cancel discard the current view; they do not durably
  revoke a copied signed receipt, which expires after15min and still requires
  matching owner/item/source/note/edit version. Keep this feature off for release
  until a production receipt lifecycle/provider decision is explicitly accepted.
- No combined Windows deployment, production upgrade/rollback or live Drive
  write acceptance is claimed. User explicitly prohibited merge/deployment.
  A future authorized integration must use PR57 as the combined candidate,
  not independently reapply its source PR patches.

Rollback before merge/deployment: omit this candidate branch; deployed code/data
are unchanged. No new migrations or runtime dependencies were introduced.
