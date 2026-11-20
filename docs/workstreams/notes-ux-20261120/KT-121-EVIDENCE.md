# KT-121 — optional Markdown template PoC

Scope authorized explicitly by the user through the KT-114–121 assignment.
This lifts the task's conditional HOLD for this isolated PoC only. No provider,
paid service, migration, production data, merge or deployment is involved.
Baseline `7044b4a0f50a7c831a391f27b1f90cc4aaa21d8b`.

## Storage decision, current primary sources checked 20 November 2026

| Option | Fit and tradeoff | Cost/security/replacement |
| --- | --- | --- |
| Ordinary Markdown in existing Item.note | Chosen. Four patterns plus optional author/date/link are readable/editable text. Existing PATCH, read, export and backup preserve them. No typed-field search/filter promise. | No dependency or schema; fastest to review; no remote calls. Existing safe Markdown renderer remains. Any future structured extractor must preserve raw source. |
| Versioned JSON object/JSONField | Useful when metadata queries and schema version upgrades become necessary; needs schema/API/export/restore changes plus validation. PostgreSQL jsonb can index but does not preserve JSON whitespace/key order. | No new vendor, but introduces migration and dual-source reconciliation. Fields require explicit allowlist, size limits and version handling. Deferred until a real query need. |
| Typed related table | Strong database constraints and predictable queries per content type; many sparse types/joins and migrations for a small optional template are excessive. | Same PostgreSQL, more maintenance and API changes. Appropriate for settled domain requirements, replaceable via explicit migrations. Deferred. |

Sources: [Django JSONField](https://docs.djangoproject.com/en/5.2/ref/models/fields/#jsonfield),
[PostgreSQL 18 JSON](https://www.postgresql.org/docs/18/datatype-json.html),
[PostgreSQL 18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html),
[CommonMark](https://spec.commonmark.org/0.31.2/),
[Django serialization](https://docs.djangoproject.com/en/5.2/topics/serialization/).
PostgreSQL current docs now refer to 19; project/runtime remains PostgreSQL 18.
No vendor template/schema code was copied.

## Component and host contract

Files: NoteTemplateConfig.ts, NoteTemplatePicker.tsx, NoteTemplatePicker.css.
Four optional patterns: Bài học, Sách / Chương, Cuộc họp, Video nguồn. Selecting
only previews; applying is an explicit separate button. Existing draft bytes
remain an unchanged prefix, using its first line-ending convention for the
addition. Fields are optional; source link metadata does not create a Source,
CaptureEvent, locator, transcript or Asset. User can edit/delete all inserted
text. No auto-tag, hierarchy, user-pinned or derived-source mutations.

This PR supplies an isolated component and integration contract, **not wiring
into CaptureScreen or ItemScreen** (owned by other parallel tasks). Main product
UI therefore does not expose templates until G00 applies reviewed glue.

Host imports `NoteTemplatePicker`, `acceptNoteTemplate` and supplies current
**draft.note**, not a source/derived body. The onApply proposal contains
expectedNote/nextNote/templateId/templateVersion. Host compares the latest draft
against expectedNote synchronously with its draft update and returns true only
if accepted. Example for a draft mirrored in a ref by the parent:

```tsx
<NoteTemplatePicker note={draft.note} disabled={busy} onApply={(proposal) => {
  const note = acceptNoteTemplate(draftRef.current.note, proposal);
  if (note === undefined) return false;
  const next = { ...draftRef.current, note };
  draftRef.current = next;
  setDraft(next);
  return true;
}} />
```

The callback must not PATCH immediately, submit a CaptureEvent, change Item ID or
replace other draft fields. Existing host save/cancel/network-draft behavior is
responsible for persistence. Rejection/errors keep selection and draft; pending
callback prevents duplicate apply. No window/localStorage state is used here.

## Checkpoint

- PASS frontend explicit `node --test tests/kt121-templates.test.mjs`: 46 tests,
  including four templates × ten Vietnamese NFC/NFD/emoji/CRLF/CR cases,
  unchanged original prefix, simulated JSON save/reload, stale callback,
  optional fields, URL validation, size/disabled/pending states.
- PASS `npm test`: 19 existing tests; `npm run build` (existing >500 kB bundle
  warning). Main bundle is unchanged because host integration is deferred;
  the production-built browser fixture separately bundles the component.
- PASS PostgreSQL 18: `python manage.py test catalog.test_api
  processing.test_knowledge catalog.test_kt121_templates --noinput -v 1`:
  14/14 tests with `KT121_RESTORE=1`. Four templates × ten synthetic Vietnamese
  Items: actual existing PATCH/GET, ReadKnowledgeService and Markdown/text
  knowledge snapshot exports; raw note bytes, Item/Asset/Source mappings,
  CaptureEvent raw/time, user-pinned relations and DerivedContent remain stable.
  Plain-text export intentionally removes heading markers per the current
  exporter, so it is checked against that documented rendering; raw Markdown
  export and DB round trips are byte-exact. Frontend/backend fixture expectations
  are independent; backend test has no path dependency on frontend files.
- PASS native `pg_dump --format=custom` / fresh `pg_restore` restricted to
  `test_kt121` → `test_kt121_restore` on the authorized loopback QA cluster.
  All rows in the 15 catalog/provenance/job/export collections match; 40/40 note
  bytes and original events match. Final proof dump SHA-256:
  `056145db517fb1477a04ddad6bf13bd013a98f496bae98832aa52eb32a9d96e6`.
  Dump lived in an OS temporary directory outside Git and was removed; test
  source and fresh restore databases were removed. No Drive files downloaded or
  uploaded: StorageLocation IDs are synthetic mapping fixtures only.
- PASS real installed Chromium, headless CDP: four choices do not mutate draft;
  native Enter applies once, original prefix preserved; local fixture save/reload;
  rejected callback retains draft/preview; 1440/768/390 have no horizontal page
  overflow and template action touch targets ≥44px; reduced-motion content stays.
  This browser fixture uses only same-tab synthetic storage, while the separate
  backend tests establish real database/export/restore behavior.
- PASS design source lint 0 FAIL/0 WARN; app inspector initial 0 FAIL/2 WARN,
  selected-preview 0 FAIL/1 WARN. All fold/page screenshots at three widths and
  error-state screenshots were opened. Stronger borders are actual selection
  controls (not decorative panels); initial desktop draft/picker are independent
  tools and do not stretch to matching bottoms. These warnings are accepted.
- PASS backend Ruff check/format and git diff whitespace check.
- Final Code/Tested SHA and CI status are recorded in the PR because a file
  cannot truthfully contain the hash of its own commit.
- NOT_RUN real Android/native IME, production Drive export, main-screen template
  flow until host integration. JSON simulation is not DB/device evidence.

## Repeating the isolated checks

Frontend: run `npm ci`, `npm test`, `npm run build`, and explicitly
`node --test tests/kt121-templates.test.mjs` from apps/web. The shared npm runner
does not discover this file. `node tests/kt121-browser-server.mjs` builds and
serves only the synthetic fixture at loopback port 62221; `KT121_PORT` changes
the port, and `KT121_BUILD_ONLY=1` only builds. Append `?preview=book` to inspect
the preview state without applying it. Set `KT121_CDP_MODULE` to the existing
design skill `scripts/lib/cdp.mjs`, then run
`node --test tests/kt121-browser.test.mjs`. Optional `KT121_BROWSER_URL` chooses
the fixture URL. Without the adapter, browser test explicitly skips.

Backend uses standard temporary POSTGRES_* environment for the authorized QA
cluster and the existing Python runtime. Set POSTGRES_DB=kt121 so Django uses
test_kt121; require that it does not already exist before running the tests.
Enable the separate native restore only with KT121_RESTORE=1 and
KT121_RESTORE_DB=test_kt121_restore and PostgreSQL 18 bin on PATH. It refuses
an existing restore target and accepts only the exact two test database names.
Credentials and generated dumps must not be committed. CI runs persistence
test normally; native restore test skips unless opted in on the QA cluster.

Visual critique: existing brand Geist/type/palette kept for a new component,
without direction draw/redraw. Question: “Which optional structure helps this
draft?” Four named text buttons carry the choice; preview and explicit apply
show its effect. No vanity counts, charts, decorative media or animation. The
phone stacks choices with readable descriptions and touch-sized apply/cancel.
Metadata remains folded/optional. Existing draft is visible alongside desktop
preview and below it on phone; final placement depends on host integration.
All displayed notes and source links are synthetic fixtures only.

Rollback: remove/deactivate optional component. Inserted text is ordinary
Item.note Markdown and remains readable/exportable with the existing renderer;
no migration or asset cleanup is necessary. Copy unsaved host drafts before
changing the editor implementation.
