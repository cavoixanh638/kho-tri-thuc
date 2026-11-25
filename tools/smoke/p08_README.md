# P08 / KT128 — isolated browser acceptance harness

Scope: `codex/parallel-20261121-p08` against `coord/notes-parallel-20261121-frozen` (base `9716a6a876d6ec41e10b3c3dcbdc095ab4ddd84d`). Test/harness only. No app changes or production deployment. The existing `knowledge_journeys.mjs` is the **real built-App** runner; `p08_cdp.mjs` is a dependency-free Chromium CDP adapter and `p08_report.mjs` enforces truthful per-journey reporting. No mocked fetch in the E2E runner.

## Local preflight and unit tests

From repo root, with Node >=22 and Chromium installed:

```sh
node --check tools/smoke/knowledge_journeys.mjs
node --check tools/smoke/p08_cdp.mjs
node --test tools/smoke/p08_*.test.mjs
```

The native CDP test uses only `about:blank`, tests actual Chromium scripting, viewport changes (390/1920), reduced-motion emulation and PNG capture. **It is not a substitute for E2E**. The isolated environment used for P08 preparation blocked HTTP loopback navigation with `net::ERR_BLOCKED_BY_ADMINISTRATOR`; consequently no built-App screenshots or authenticated DB session were obtained there.

## Real built-App acceptance (run only in a controlled disposable checkout)

Requires Docker/Compose, Chromium, Node >=22, and no parallel production stack. The frontend `apps/web/Dockerfile` runs `npm run build` and serves Vite preview; the backend service runs Django + migrations, and PostgreSQL is a private Compose service. Use a **unique Compose project name** so the smoke test cannot reuse the normal stack or its volumes. Keep credentials in a temporary environment file outside the repo; never commit them. Example using synthetic-only secrets:

```sh
qa_env="$(mktemp /tmp/kt-p08.XXXXXX.env)"
qa_pass="$(openssl rand -hex 24)"
qa_db_pass="$(openssl rand -hex 24)"
qa_django_key="$(openssl rand -hex 32)"
cat > "$qa_env" <<ENV
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=$qa_django_key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,api
POSTGRES_DB=kt_p08_journeys
POSTGRES_USER=kt_p08
POSTGRES_PASSWORD=$qa_db_pass
API_PORT=62311
WEB_PORT=62310
SUGGESTION_REVIEW_POC_ENABLED=1
GOOGLE_DRIVE_CLIENT_ID=
GOOGLE_DRIVE_CLIENT_SECRET=
GOOGLE_DRIVE_REDIRECT_URI=
GOOGLE_DRIVE_TOKEN_KEY=
ENV
chmod 600 "$qa_env"
docker compose -p kt-p08-jouney-20261121 --env-file "$qa_env" up --detach --build --wait --wait-timeout 180 db api web
docker compose -p kt-p08-jouney-20261121 --env-file "$qa_env" exec -T -e DJANGO_SUPERUSER_PASSWORD="$qa_pass" api \
  python manage.py createsuperuser --noinput --username p08-fixture --email p08@example.invalid
KT_JOURNEY_URL=http://127.0.0.1:62310 \
KT_JOURNEY_DB_NAME=kt_p08_journeys KT_JOURNEY_ISOLATED=YES \
KT_JOURNEY_USER=p08-fixture KT_JOURNEY_PASSWORD="$qa_pass" \
KT_JOURNEY_OUT=tmp/p08-kt128 node tools/smoke/knowledge_journeys.mjs
# Review tmp/p08-kt128/p08-results.json and screenshot hashes; copy redacted QA evidence only.
docker compose -p kt-p08-jouney-20261121 --env-file "$qa_env" down --volumes
rm -f "$qa_env"
unset qa_pass qa_db_pass qa_django_key
```

**Safety:** `KT_JOURNEY_URL` must match `http://127.0.0.1:62310` exactly, `KT_JOURNEY_DB_NAME` must be `kt_*` without production-like terms, `KT_JOURNEY_ISOLATED=YES`, and the QA account must have zero Items. These are necessary but not sufficient for isolation: verify the Compose project/volume mapping yourself. Never target main DB/Drive, a personal account, or a deployed URL.

Optional: `KT_JOURNEY_PUBLIC_NETWORK=YES` runs the **public** Python docs article clip. Without opt-in, J3 is `NOT_RUN`. `KT_JOURNEY_PDF_ITEM_ID` and `KT_JOURNEY_MP4_ITEM_ID` must refer to synthetic verified assets in the isolated account; without them J6B is `NOT_RUN`. A browser-generated PDF iframe or media player alone **does not establish accurate native page/time seek**, so J6B stays `BLOCKED` until native manual evidence is attached. J8 vault roundtrip remains `NOT_RUN` on the frozen snapshot: KT127 was not integrated there. J9 10k/1k and backup/restore remain `NOT_RUN` until an isolated large DB and reproducible restore verification are run separately.

## Reporting contract

`p08-results.json` records each journey's expected/actual/status/dependencies/duration; responsive screenshots are generated at 1920, 1440, 768, 390 with SHA256 and pixel evidence only after a real app run. Reports are restricted to synthetic QA; raw quotes, credentials, private URL bodies, Google tokens, and database dumps must never be committed. Statuses: `PASS` (assertions actually executed), `FAIL` (assertion in reachable environment), `BLOCKED` (prerequisite/feature/native acceptance missing), `NOT_RUN` (no attempt). `pass_rate = PASS/(PASS+FAIL)` when denominator >0; BLOCKED/NOT_RUN are excluded but **prevent** overall PASS. Exit codes: 0 all pass, 1 failure, 2 not complete. Use `INTEGRATION_REQUIRED` for endpoints absent from the frozen branch; P08 does not patch app or touch shared workflows.

CI workflow `.github/workflows/smoke.yml` runs frontend/backend smoke but does **not** automatically call P08 real-browser driver. A green CI by itself is not KT128 acceptance; a failing unrelated frontend suite remains a release blocker until G00 integrates fixes.

Rollback: close the P08 PR/delete its isolated branch; no application or DB migration changes were made. The temporary Compose test project must be removed with `down --volumes` **only for that named QA project**.
