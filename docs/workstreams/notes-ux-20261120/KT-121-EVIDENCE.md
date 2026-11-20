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
- PASS build; the main bundle is unchanged because component integration is
  intentionally deferred. Production-built fixture will separately verify it.
- Backend/restore/browser QA in progress at this checkpoint; final PR records
  exact Code/Tested SHA, commands and PASS/FAIL/NOT_RUN.
- NOT_RUN real Android/native IME, production Drive export, main-screen template
  flow until host integration. JSON simulation is not DB/device evidence.

Rollback: remove/deactivate optional component. Inserted text is ordinary
Item.note Markdown and remains readable/exportable with the existing renderer;
no migration or asset cleanup is necessary. Copy unsaved host drafts before
changing the editor implementation.
