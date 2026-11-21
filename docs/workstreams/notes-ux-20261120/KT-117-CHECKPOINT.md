# KT-117 checkpoint — 20/11/2026

**Code SHA / Tested SHA:** app `3b777a46f18cb0a8107d1f195a58936ea0421360`, fixture packaging fix `16925a09aaade25eb59ff2f04e6cb9bc2310cee3`.

CI44711839148 tìm ra fixture JSON ở frontend không có trong backend Docker image.
Root chuyển **một bản canonical** sang `apps/backend/ingestion/fixtures/`; cả
frontend45 case và backend30-lượt corpus đọc đúng file này. Không đổi bytes của
fixture hay mã ứng dụng. Chạy lại explicit frontend45 PASS, backend corpus1 test
(30case) trên DB riêng PASS, Ruff/format/diff PASS; chờ CI latest head, không lấy
run cũ FAIL làm kết luận cuối. Phần ứng dụng không cần deploy hoặc đổi schema.
The checkpoint commit changes documentation only. Base: `7044b4a0f50a7c831a391f27b1f90cc4aaa21d8b`.
Branch: `codex/kt-117-quick-capture`. No merge or deployment.

## Result and boundaries

- Shared inputs keep full Unicode/raw annotation, including CRLF and surrounding
  spaces. Oversized content remains visible and requires correction, rather than
  silently truncating. An explicit HTTP(S) URL becomes a link; prose/multiple URLs
  stay one note. Invalid/active/credential URLs are retained as inert note text.
- Drafts and pending retry keys survive CaptureScreen unmount and the real App
  401/login path, scoped by authenticated username. Unsent file selections and
  their retry keys also survive screen navigation. File objects stay in memory.
  No persistent storage, offline queue or automatic resubmission was added.
  Reloading/closing the tab loses drafts; the form says so. If the extra session
  identity check is unavailable, the existing form remains usable but account
  scoped recovery cannot be established until identity is available.
- A successful share still needs one submit tap after the share screen opens;
  retry needs one additional tap. OS share-sheet/install steps are not included.
  Clear is explicit. Reusing acknowledged content creates a fresh request key.
- A receipt shows the Event ID, link to its Item, server receipt time and client
  submit-to-response latency. Link/upload ACK never claims a verified Drive MP4.
  Upload receipts follow the existing upload contract, without inventing an Event.
- Existing manifest share target, API, schema, Drive permissions and ACK transaction
  remain unchanged. No common runner, styles, API client or CURRENT_STATE edits.

## Verification

Environment: Windows, Node 24.15.0, Python 3.13, project virtualenv,
PostgreSQL on loopback with unique disposable `test_kt117` database. Synthetic
fixtures only; no worker, public-site fetch, OAuth, Drive or production catalogue.

| Check | Result | Evidence |
| --- | --- | --- |
| `node --test tests/kt117-capture.test.mjs` in `apps/web` | PASS, 45/45 | 30 shared fixtures plus network, actual timeout abort, 401/403, double submit, auth unmount/relogin, account isolation, selected-file navigation/file retry, oversized input, exact payload/receipt and manifest checks |
| `npm test` in `apps/web` | PASS, 19/19 | Existing UI suite; does **not** discover the new file, which was run explicitly |
| `npm run build` in `apps/web` | PASS | TypeScript + Vite production output; existing >500 kB chunk warning remains |
| `ingestion.test_kt117_capture` through Django test runner | PASS, 1 corpus test, 30/30 fixtures | Exact Event raw_kind/raw_text/original_url/annotation + receipt; 30 retries add zero Events; 30 deliberate resends add 30 Events; final 60 Events, zero Assets |
| Ruff check/format of the new backend test; `git diff --check` | PASS | No migrations/backend implementation changes |
| Chrome fixture at 1440 / 768 / 390 px | PASS | Network failure keeps draft and no receipt; retry clears only after ACK; no horizontal overflow or JS exceptions |
| design-taste app inspector at 1440 / 768 / 390 px | PASS, 0 FAIL / 3 WARN | Dev-only fixture; empty history creates intentional blank/right-short-column warnings. All six listed fold/page screenshots inspected, plus six failure/receipt screenshots |
| Design source lint | PASS, 0 FAIL / 1 WARN | Existing cryptographic key hex zero-padding is not decorative numbering |
| Android installed/uninstalled PWA, Chrome/YT/TikTok/file browser share, OS permissions/routing | **ANDROID_NOT_RUN** | No physical Android device was supplied; desktop/jsdom fixtures do not prove Android acceptance |

Backend command from `apps/backend`, with the test environment variables set
outside Git and the project virtualenv Python:

```python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
from django.conf import settings
settings.DATABASES['default']['TEST'] = {'NAME': 'test_kt117'}
django.setup()
from django.test.utils import get_runner
raise SystemExit(bool(get_runner(settings)(interactive=False).run_tests(
    ['ingestion.test_kt117_capture']
)))
```

## Browser reproduction and observations

Run Vite on loopback and open `/tests/kt117-browser.html` with the standard
`shared_title`, `shared_text`, `shared_url` query parameters. `fixture=failure`
injects one network failure. This independent test entry intercepts **every**
API request in tab memory and rejects unexpected paths. It is absent from the
production bundle. Do not use its receipt as server/Drive evidence.

Local screenshots and inspector/interactions JSON are in the sibling workspace
artifact directory `kt117-browser-evidence` (outside Git). The measured synthetic
retry ACKs were 12 / 13 / 12 ms at 1440 / 768 / 390 px. These are fixture response
measurements, **not** backend/Android latency or an SLA. A deterministic UI test
also verifies a 234 ms client interval.

Visual review: the composer remains the main action, with the existing neutral
palette/type; the shared URL/annotation and submit fit the 390 px first screen.
Network errors appear beside the retained draft; long receipt IDs wrap on mobile.
The empty history intentionally stays short instead of adding synthetic rows.
No product-wide restyle was attempted.

## Integration and rollback

Review/cherry-pick this branch independently of KT-114–121. The new test file
must be included explicitly in integration validation until G00 changes shared
test discovery. G00 owns CURRENT_STATE after review/merge. Keep Android gate open.

Rollback by reverting the capture code/test commit; there are no migrations,
data transformations, external writes, permission or deployment changes.
