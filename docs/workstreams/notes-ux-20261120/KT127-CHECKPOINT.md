# KT127 portable vault — interrupted WIP saved21/11/2026

Status: WIP / TEST_PENDING / NOT_USABLE_AS_FEATURE.
Branch codex/kt-127-vault; based on combined candidate b54f892 (PR58 ancestry),
which itself is based on PR57 e00b3ca. No merge/deployment/production operations.

Only apps/backend/catalog/vault.py has been drafted. It proposes bounded
Markdown ZIP+manifest serialization, exact datetime precision, stable UUID
links/home/parent/membership, dry-run/conflict/import and owner/receipt checks.
Python py_compile PASS only; this is syntax validation, not functional QA.
No source ZIP, original media, account secret or personal data is committed.

NOT_DONE: API routing, KnowledgeVaultPanel UI, format ADR, schema4 backup
projection/old-version compatibility,100Item/30folder/200link/5media roundtrip,
host mounting, security/failure tests, actual browser/UAT and CI.
Draft source must be reviewed before being imported or executed. In particular
audit archive path/size handling, owner/cross-item foreign keys, exact immutable
CaptureEvent/saved_at timestamps, edited Markdown conflict policy, source
mapping, selected-item relation closure and retry idempotency.

Next:
1. Read KT-127-PORTABLE-VAULT.md and latest KT122/123/126 contracts; finish
   portable service/API/UI with no unbounded media download or external writes.
2. Extend tools/backup schema projection for Item structural fields, collections
   and clip annotations; keep legacy v1/v2/v3 readability and test fresh restore.
3. Run native PostgreSQL roundtrip/safety/browser acceptance, push tested SHA/
   evidence and create/update draft PR; root integrates into PR58, never PR57.

Worker stopped at an account usage limit; all remaining implementation and
tests above stay open. The pushed checkpoint/source is the durable resume point.
