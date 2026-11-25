# P13 — Android Share, IME, offline, receipt/idempotency acceptance

Scope: independent QA only. This runbook never claims that an Android device was tested. It does not install an APK or access real Google Drive.

## Preconditions

- The real Django+PostgreSQL+frontend stack is running on a **disposable** QA instance through the loopback proxy `http://127.0.0.1:5173`. Never run the API probe against production, real accounts, or existing user data.
- A dedicated synthetic account `kt-p13-...` exists and has only fixture data. The database/Compose project must be confirmed isolated before testing.
- Node.js 24. No network is needed for contract tests.
- The PWA manifest currently uses a GET Share Target for title/text/url; **Android native file sharing is unsupported as a share target**. The app's separate file picker is not equivalent.

## Automated steps

1. `node tools/smoke/p13_share_contract.mjs`: reports **SOURCE_PASS/SOURCE_FAIL** only; output in ignored `tmp/p13-source-contract.json`. Checks manifest, 30 synthetic fixture definitions, draft/retry/IME source contracts. It does not start Chromium.
2. `node --test apps/web/tests/p13-capture.test.mjs`: frontend manifest/source contract tests; the existing `apps/web/tests/kt117-capture.test.mjs` provides actual DOM+mock-fetch 30-share cases and failure/retry tests. Run from `apps/web` with `npm test` to include both, rather than treating this source test alone as UX proof.
3. Opt-in real temporary PostgreSQL/API check, after manually creating the synthetic user:
   ```sh
   P13_QA_ISOLATED=YES P13_QA_USER=kt-p13-fixture P13_QA_PASSWORD='<synthetic-only-secret>' node tools/smoke/p13_share_api.mjs
   ```
   The script rejects missing isolation confirmation and non-loopback origins. It asserts: same key -> same receipt / +0 events; genuinely new send -> +1 event for same URL; anonymous write and missing CSRF -> no event; creates only synthetic `.invalid` source URLs. The resulting JSON is local/ignored. Its PASS requires actual execution.
4. Full PWA/Android test needs an actual secure-context installed PWA. Do not pretend headless Chromium or DOM mocks validate Android's share sheet. Record Android version, browser/PWA install mode, observed result, screenshot only with synthetic data, and a test timestamp.

## Manual Android / keyboard matrix (NOT_RUN until performed)

| Case | Steps | Expected |
| --- | --- | --- |
| A01 | Install PWA over trusted HTTPS, inspect Android Share list | Kho Tri Thức appears as URL/text target |
| A02 | Share Unicode/combining Vietnamese text from Chrome | Exact content preserved, sent once, correct server time |
| A03 | Share YouTube and TikTok public URL from each Android app | URL and optional title preserve identity; no auto-Drive-verified assertion |
| A04 | Share text with 2+ embedded links or unsafe `javascript:` URL | Preserved as inert note; no script/navigation |
| A05 | Share same URL twice as two intentional sends | One Item may be reused but two distinct CaptureEvents |
| A06 | Tap Send twice quickly, then retry same request after artificial disconnect | Only one server Event for same idempotency key |
| A07 | Disconnect network before ACK; reconnect and resend | Original text retained and one Event after actual ACK |
| A08 | Session expires (401) while editing then sign in as same user | Same draft and attempt key retained, no false successful receipt |
| A09 | Attempt with missing/expired CSRF (403) | No unauthorized write, editable draft remains |
| A10 | Switch to a second account in same tab | No previous-account draft disclosed |
| A11 | Type Vietnamese with Gboard/Vietnamese IME, including preedit/composition, accents, backspace | No duplicate marks or premature submit; exact typed text |
| A12 | Test Unikey/EVKey via physical keyboard on Windows; test input method behavior on Android separately | Uninterrupted composition and undo behavior |
| A13 | 390px and 768px widths, 200% zoom, reduced motion | Form and receipt usable without horizontal clipping |
| A14 | Share a file through Android native Share menu | Expected **unsupported by current GET target**; document missing feature, do not mark PASS |
| A15 | Select a file through application's file picker and retry on lost network | Same upload key; receipt does not imply Google Drive verification |
| A16 | Close PWA tab/process before ACK | Tab-memory draft **may be lost**. Document limitation; no offline durable queue claim |

Collect screenshots for A01, A03, A07, A11, A13. Verify DB history before/after for A05–A09, rather than only trusting UI notification. Do not include private source content or credentials in evidence.

## Status legend

- `SOURCE_PASS`: static manifest/source/fixture checks only.
- `SIMULATED_PASS`: browser DOM with mocked backend/IME; never Android PASS.
- `API_PASS`: isolated Django/PostgreSQL/CSRF result, not device proof.
- `PASS`: real device observed against a designated disposable environment for that case.
- `NOT_RUN`: no actual execution; never convert this to PASS automatically.
- `FAIL`: reproduction shows mismatch; record exact test and safe evidence.

P13 changes only test/runbook paths; rollback by removing P13-only files. No production source, database migration, credentials, main branch, or deployment changes.
