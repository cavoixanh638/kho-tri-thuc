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

Pending: frontend cases, source rendering/preview browser checks, public read
smoke with redacted hash report, integration/backup/vault adaptation and final CI.
Current local code must be committed/pushed with this checkpoint (TEST_PENDING
for the UI); test output above does not imply whole KT126 DONE.
