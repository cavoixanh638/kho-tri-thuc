# KT-120 — provider-free review PoC

User explicitly assigned KT-120, so the review PoC is implemented. No provider,
budget, retention or private-data transfer approval exists: **PROVIDER_NOT_RUN**.
No API key/package/provider/paid request was added. The existing no-AI app works.

## Implementation boundary

- `processing/suggestions.py`: immutable signed preview receipt containing owner,
  item ID, source fingerprint, `base_edit_version`, exact before/after, nonce and
  explicit `provider/model=none` provenance. Receipt expires in 900 seconds.
  It is returned only in an authenticated response and POSTed in JSON, never a
  URL, log or localStorage. Signed is **not encrypted**: handle like private note.
- Preview/reject do not write `Item.note` or enqueue anything. The source version
  fingerprints Sources, Assets and DerivedContent including locator/status/version.
- Accept/undo execute in a database transaction with Item row lock. Changed note,
  user edit version or source fingerprint produces409. Successful explicit accept
  changes only note/edit version/updated_at and queues existing organize job;
  undo requires the accepted edit version and restores original bytes. Existing
  note/asset/event/pinned relationships are never synthesized by a provider.
- API paths `/items/{id}/suggestions/{preview,accept,reject,undo}` require the
  existing session/CSRF rules. Feature gate `SUGGESTION_REVIEW_POC_ENABLED` defaults
  false (404); tests use override_settings, production configuration was untouched.
- Standalone `AiSuggestionReview` shows raw before/after and a Unicode code-point
  replacement range, safe escaped text, Accept/Reject/Cancel/Undo. It blocks a
  changed local draft, duplicate clicks and applying a late result to a different
  suggestion. Network/409 keeps current note and requests a state refresh.

For this isolated PoC the receipt is stateless, not a persistent review record.
Reject/Cancel discard it in UI; they do not revoke a copied receipt server-side.
Expiry and note/edit/source checks still apply. Durable audit, terminal rejection
revocation and multi-host issuance require a reviewed persistence design before
production enablement; no misleading audit/history guarantee is made here.

## Validation

Windows / Python3.13 / Node24 / PostgreSQL18 QA cluster62224, unique disposable
`test_kt120` and `test_kt120_full`; no production/Drive/OAuth reads or writes.

| Check | Observed result |
| --- | --- |
| Twenty Vietnamese raw-edit fixture pairs | 20/20 preview/reject leave note unchanged; exact diff input; explicit accept and undo restore original bytes |
| Event/Asset/user-pinned preservation | Entire fixture row dicts match before/after review/undo |
| Version/source conflicts, repeat accept | 409, current note preserved |
| Signed receipt wrong owner/tamper/expiry | Rejected without changing note |
| Disabled gate/auth/CSRF | 404/401/403 respectively |
| `python ... run_tests(['processing.test_suggestions'])` | 4 tests PASS including20 fixture subcases |
| Full backend suite | 215 PASS,0 skip,23.674s; explicit FFmpeg path |
| `node --test tests/kt120-suggestions.test.mjs` | 25 PASS, including20 exact Unicode diff/reject fixtures, explicit accept/undo, stale draft, late result and409/503 |
| `npm test` | Existing19 PASS; does not discover the new file |
| `npm run build` | PASS; TypeScript checks modules, isolated entry is not imported into app bundle |
| Ruff check/format and diff check | PASS |
| Browser/Android/provider | NOT_RUN in this task; in-app browser unavailable, native Chrome was minimized and no usable binding was obtained |

The standalone synthetic browser entry is `tests/kt120-browser.html`; it handles
all requests in memory and must never be cited as server/provider evidence.
Backend and frontend were exercised separately, not claimed as an E2E AI flow.

## Integration and rollback

G00 can mount a keyed `<AiSuggestionReview key={suggestion.receipt} ... />` from
an explicitly reviewed host. Pass current unsaved draft as `currentNote`, CSRF,
and onApplied refresh the same item. API must be the versioned review endpoint,
not unguarded generic PATCH; never accept automatically on preview. Re-fetch item
after an ambiguous response before resending. Shared ItemScreen/KnowledgeReading/
api.ts/styles/test runner/CURRENT_STATE were deliberately not changed here.

No new model/provider decision is being made. When provider permission exists,
compare at least2–3 current options with privacy/retention, price and measured
latency before enabling it. Revert this PR to remove the PoC, no schema/data
migration needed. Keep flag false until integration and remaining gates are
reviewed. This PR is for review only: **do not merge or deploy automatically**.
