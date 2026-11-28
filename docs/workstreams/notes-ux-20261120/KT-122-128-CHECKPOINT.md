# KT-122–128 delivery checkpoint — saved21/11/2026

Status: IN_PROGRESS / WIP_SAVED_ON_GITHUB. User explicitly assigned KT122–128.
Combined [PR58](https://github.com/cavoixanh638/kho-tri-thuc/pull/58) branch
codex/knowledge-journeys targets PR57 branch codex/notes-ux-integration.
PR57 base e00b3cacd02decdb852dc6e17e7b297d83acaccf remains open/unmodified.
No merge/deploy/production DB/Drive/AI-provider operation. Entry: INDEX.md +
G00-FEATURE-TRACEABILITY.md and seven task specifications.

| Scope / owner | Code/test milestone and actual state | Durable handoff |
| --- | --- | --- |
| KT122/123 explorer | Codef13add5; API21bb54c, native3603/f13. Module API/concurrency/10k1000folder/DOM/native4width/DnD PASS. Combined home/unfiled consistency and backup remain open. | [PR61](https://github.com/cavoixanh638/kho-tri-thuc/pull/61), KT-122-123-EVIDENCE.md |
| KT124 navigation | Behavior52efd9e, finalvisualc5acff2, evidence72d1e1b.265frontend,3PG+1native PASS;100notes200links/30Markdown/20commands. Host actions require KT128 combined check. | [PR59](https://github.com/cavoixanh638/kho-tri-thuc/pull/59), KT124-CHECKPOINT.md |
| KT125 collections | Code754710b, evidence86f5317.238frontend;8targetedbackend/native PASS;10k100groups5queries301pages P95=117.28ms max7queries. Read-only properties, no typed-fields claim. | [PR60](https://github.com/cavoixanh638/kho-tri-thuc/pull/60), KT125-EVIDENCE.md |
| KT126 clipping / root | Code737a4c3 +7dfeecd.4PG tests with30syntheticweb/PDFanchors,8DOM tests,20actualpublicPythonpages preview/save PASS. Final integrated browser pending. | KT126-CHECKPOINT.md, KT126-PUBLIC-READS.json |
| KT127 portable vault | Drafta61cc21, Python syntax check only; API/UI/backup/roundtrip NOT_DONE. Separate branch codex/kt-127-vault, not yet cherry-picked into combined candidate. | [WIP PR62](https://github.com/cavoixanh638/kho-tri-thuc/pull/62) targets PR58, KT127-CHECKPOINT.md |
| KT128 / root | tools/smoke/knowledge_journeys.mjs drafted; node--check PASS only. Actual combined browser/full suite/restore/CI acceptance NOT_RUN. | This checkpoint and drafted driver |

Combined code through51d0ef9 + worker evidence docs56b0698/6dcdcb1; final
save commit follows. Reports contain original tested SHAs and limits; do not
treat a source-file draft, newer docs HEAD or green source PR as combined PASS.
Public clipping report stamped b54f892 was generated with an uncommitted
test/offset fix later saved in7dfeecd: rerun on final clean SHA before acceptance.

All worker/root work is now on GitHub; account usage limits interrupted the
workers. PRs remain draft, latest CI may run automatically; root must verify
actual final head rather than wait on an obsolete SHA. No UX_COMPLETE claim.

Next (same task, no restart/reset):
1. Finish KT127 service/API/UI+backup schema projection and100Item/30folder/
   200link/5media exact timestamp/UUID/home/parent/clip roundtrip. Read WIP PR62.
2. Reconcile catalog/api.py unfiled filter with explicit home/active parent;
   run real built App KT128 driver, fix failures, include template/manual-review/
   vault journeys and screenshots at1920/1440/768/390.
3. Full PostgreSQL/frontend/migration/10k/backup checks; update CURRENT_STATE,
   G00 traceability and per-task reports; push and verify final-head CI.

Temporary QA only: PostgreSQL loopback62224, role kt_dev (password private env);
fresh browser DB kt_128_browser_20261121 and synthetic user journey-qa1 prepared.
Build task session75290 may be complete; check before continuing. No new browser
QA server62310 was started, driver was not run. Do not use production8009/54329.
Never commit credentials, raw source bodies, media or database dumps.
External Android/nativeIME/productionDrive/PDF/100GB stay NOT_RUN without proof.
Completion still requires all specified journeys; optional phase2/KT129/130
stay deferred. Continue from these checkpoints, without redoing valid task PASS.
