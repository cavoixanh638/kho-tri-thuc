# KT-120 integration — manual review host

Status: **PASS within provider-free development scope**, pending root's combined
ItemScreen/browser/CI acceptance. No PR merge or Windows deployment.
Branch: `codex/notes-ux-review`; integration baseline `5576d84`.
Code/Tested SHA: `5c8e6fa9c9b524d786072483eca6bd17800bf982`.

## Changes and host contract

- New `ItemSuggestionPanel` mounts into the real ItemScreen via root integration.
  Props: `item`, `csrf`, `editing`, `draftDirty`, `onUpdated`, optional
  `onBusyChange`. Root must block editor/trash mutations while review is pending.
- Authenticated, owner-scoped GET
  `/api/v1/items/{item_id}/suggestions/capabilities` returns `enabled`,
  `provider_configured: false`, `mode: manual_review_poc`, TTL900seconds.
  Other-owner/deleted Items are404; unauthenticated access401. Reads are inert.
- `SUGGESTION_REVIEW_POC_ENABLED=0` by default; only exact `1` opts into the
  development UI/API. Missing/disabled capability leaves optional UI hidden.
  There is no AI model, external request or provider credential.
- A user explicitly enters replacement text, previews differences, and then
  accepts/rejects/cancels/undoes. Preview/reject never updates the host note.
  Editing/dirty drafts block acceptance and undo. Pending acceptance disables
  proposal replacement; repeated clicks produce one request.
- Accept/undo ACK supplies raw note, shared `user_edit_version` and actual server
  `updated_at`; host refresh keys update from that timestamp. A delayed ACK must
  not overwrite a newer host version.409/503 keep manual input and existing note.
- Review and editor use the same PostgreSQL Item row lock/version counter:
  accepting a proposal invalidates older editor PATCH versions; later explicit
  editor saves invalidate proposal undo. No model/schema/dependency change.

## Executed checks (20/11/2026)

Windows, Node24, Python3.13, PostgreSQL18 isolated QA loopback62224.
No production database/Drive, personal input, OAuth token, AI call or media.
Temporary Django test database `test_kt_ux_review` created/destroyed by runner.

| Command | Result |
| --- | --- |
| `node --test tests/kt120-integration.test.mjs tests/kt120-suggestions.test.mjs` | 33PASS,0FAIL,0SKIP (8new host cases +25existing review cases) |
| `npm test` (existing runner at baseline) | 19PASS,0FAIL,0SKIP; all test discovery is owned by CI integration worker |
| `npm run build` | TypeScript/Vite PASS; existing >500KB chunk advisory retained |
| `python manage.py test processing.test_suggestions processing.test_suggestion_integration catalog.test_notes_ux_contracts --noinput` | 13PASS,0FAIL,0SKIP; includes20fixture subcases and3new capability/shared-version tests |
| Ruff check/format for touched Python, `git diff --check` | PASS |

Initial host test mistakenly asserted no text including Mantine-generated CSS;
corrected it to assert no proposal controls. Final33case run passed after fix.

## Limits and rollback

PROVIDER_NOT_RUN; actual native-browser host integration is root's joint test,
not claimed from jsdom. This remains an explicit development-only PoC:
receipts are signed/expiring, not encrypted and not durably stored/revoked.
Reject/cancel discard this UI view; a copied signed receipt remains usable until
expiry/version conflict. No production AI/audit/revocation claim is made.
Keep the flag0 to disable both manual review actions and host UI. Root can revert
the two integration commits to remove this host while retaining the original
isolated review PR. No migration or data rollback is needed.
