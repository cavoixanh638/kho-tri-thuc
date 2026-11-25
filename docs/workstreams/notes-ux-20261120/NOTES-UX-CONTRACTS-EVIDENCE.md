# Notes UX shared contracts — stacked follow-up

Stack dependency: PR #51 (`codex/kt-115-editor`), baseline
`4aa645f8ec7f896f28135d9effa79ad7bd064db6`. This PR targets that branch, not main.
Root explicitly assigned these cross-file fixes discovered by KT-115 and KT-119.
No merge, deploy, migration, dependency or production-data action.

## Edit API extension

GET item/list and successful PATCH ItemSummary now expose the existing integer
`user_edit_version`. It is an authored-text edit version, not a Source, Asset,
capture, extraction or organization version. The database field already exists;
no schema change. No new source-version claim is invented.

PATCH accepts optional `expected_edit_version`: strict integer ≥0, or omitted/
null for the legacy path. Under the same existing `transaction.atomic` and
`select_for_update` lock used for mutation, compare with current
`item.user_edit_version`. A mismatch returns HTTP 409 `{"code":"edit_conflict"}`
before writing anything or enqueuing a job. Versioned text writes to a deleted
item also return 409, covering deletion between preflight and PATCH. Auth/owner
lookup happens first, so other owners get 404 without a version disclosure.

The precondition is removed from mutation fields; title/description/note changes
increment the existing version once, unchanged text/favorite-only changes retain
it. No-op requests with a stale precondition still conflict. Existing clients
without a precondition continue their previous behavior; atomic conflict
protection is guaranteed only for clients that send the real version.

ItemScreen still reads fresh values before PATCH to catch observed drift in
changed fields and preserve worker/other edits to untouched fields. If that
read returns a safe nonnegative integer version, PATCH sends it as the
precondition. If a legacy server omits it, the field is omitted instead of
inventing zero. Server 409 keeps the editor open and retains the exact raw draft
and tab recovery storage, with the existing explicit conflict notice beside
the form. The preflight/PATCH race identified in PR #51 is therefore closed
against this updated server. No automatic overwrite/retry/merge of notes.

## Markdown navigation extension

KnowledgeText allows only `href="#/muc/<UUID>"` with exact length and the strict
hex/hyphen UUID shape. Those links use same-tab hash navigation. All other
internal/relative routes, suffixes, queries, encoded IDs, active schemes and
scheme-relative URLs remain inert. External HTTP(S) links keep
`target="_blank" rel="noopener noreferrer"` and credential checks.

The allowlist applies only to anchor hrefs. Image src remains HTTP(S)-only;
internal image URLs stay inert. Source HTML remains skipped and actual image
elements are not created. A syntactically valid internal UUID is not a permission
grant: ItemScreen GET/API ownership checks remain authoritative; the renderer
does not fetch target metadata or reveal target titles. This enables KT-119's
verified explicit backlinks without pretending lexical RelatedItem is a link.

## Verification

- PASS PostgreSQL 18, dedicated `test_ux_contracts` on authorized QA loopback
  cluster: `python manage.py test catalog.test_notes_ux_contracts catalog.test_api
  --noinput -v 1`, 10/10. Test DB removed after the run. Includes two simultaneous
  independent clients at expected version 0: exactly one 200 and one 409;
  winning raw bytes/version/job count and immutable CaptureEvent preserved.
  Also checks old-client compatibility, no-op/nontext behavior, strict validation,
  owner scope, and deletion after preflight.
- PASS `node --test tests/notes-ux-contracts.test.mjs`, 5/5: post-preflight 409
  retains raw draft/storage, zero version sent correctly, absent version omitted,
  strict internal link same-tab hash navigation and unsafe URL/image rejection.
- PASS `node --test tests/kt115-editor.test.mjs`, 47/47; inherited 40 raw/HTML
  fixtures remain unchanged (`unexpected_changed_bytes=0`).
- PASS existing `npm test`, 19/19, and `npm run build` (existing >500 kB chunk
  warning remains); backend Ruff check/format and whitespace diff check.
- Frontend contract tests use JSDOM/mocked transport, **not device proof**.
  Native browser/Android/IME not rerun for this nonvisual contract follow-up.
  Prior KT-115 browser evidence remains scoped to its tested SHA.
- No live production, Google Drive or provider calls. No personal fixtures.

New frontend tests require the explicit command because shared npm runner remains
unchanged. Backend test fixtures are self-contained in the API image. Exact
Code/Tested SHA and CI appear in the PR (a file cannot contain its own commit).

Rollback: revert this follow-up; notes, IDs and existing version field remain.
Older clients/server retain legacy save behavior; internal Markdown links become
inert again if KnowledgeText is reverted. Copy any dirty editor draft before
changing the running UI. Root updates canonical integration state after review.
