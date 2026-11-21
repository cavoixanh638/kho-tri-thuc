# KT126 clipper checkpoint — 21/11/2026

IN_PROGRESS. Root owns processing ClipAnnotation model/migration, clips service/
API and ResearchClipper UI. Base PR57, target integration; no merge/deploy.
Network preview is bounded/public-only and outside write locks. Signed five-minute
preview binds owner/target/source version. Selection/article/link states are
explicit. CaptureService on_created callback saves URL capture+annotation in one
durable transaction; attached file quotes extend the same immutable receipt
contract without inventing a URL. Retry preserves CaptureEvent, explicit resend
creates a new one. App/Item hosts expose the panel; insertion requires explicit
approval and expected edit version. Parser text and authored note stay separate.

PASS:4 PostgreSQL transaction tests, including20 mocked web/selection cases +
10 generated actual PDF extractions (30 exact anchors), Unicode/raw preservation,
retry/send distinction, owned evidence, stale versions and blocked input.
TypeScript/Vite build PASS. UI/component/browser/UAT and20 actual public web
pages still NOT_RUN. Corpus is synthetic; no Drive/production data/provider.

Update saved21/11/2026: code737a4c3 +7dfeecd pushed to PR58.
Eight explicit frontend tests PASS (link/article/selection preview/save,
unverified state, retry key, duplicate click, highlight and approved versioned
insertion).20 actual public Python documentation pages all previewed/saved with
raw note preserved and excerpt match; safe report KT126-PUBLIC-READS.json.
The report stamps HEADb54f892 while test/offset fix were still dirty and later
committed7dfeecd; final clean-SHA acceptance must rerun it, not silently retag.
No remote article text or session credentials are in the report.

Pending: actual integrated source rendering/clip browser journey, source state/
permissions regression, migration/backup/vault schema coverage and latest CI.
Clip UI/API offsets now validated as plain integers; article truncation at60k
characters is explicitly labelled. Authored note changes only on approved insert.
tools/smoke/knowledge_journeys.mjs contains draft real-App clip flow, not yet run.
Do not infer whole KT126 DONE from module tests or public read smoke.
