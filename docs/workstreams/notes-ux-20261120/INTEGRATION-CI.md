# Integration runner and fixture packaging — 20/11/2026

- Status: code delivered for the integration branch; remote container CI is still required.
- Owner: `ux_ci`; branch `codex/notes-ux-ci`; baseline `5576d84` (all PR48–56 changes combined by coordinator).
- Code/Tested SHA: `498e98a`; no production or Windows deployment, no PR merge.

## Changes

`npm test` discovers every `tests/*.test.mjs` except explicitly named native-browser
`*-browser.test.mjs` harnesses. Files run sequentially in separate Node test processes
to isolate JSDOM/fetch/fake clocks and avoid concurrent Vite dependency-cache writes.
New integration suites matching this convention are included automatically.

Compose builds web from the repository root using `apps/web/Dockerfile`.
The Dockerfile copies web sources and only the two canonical backend fixture files
into `/home/node/backend/...`, preserving their relative import paths from web tests.
There is no duplicated/generated corpus to drift. `Dockerfile.dockerignore` restricts
the context to these paths and excludes secrets, runtime output and dependencies.
Direct builds must use `docker build -f apps/web/Dockerfile .` from the repository root.
The existing smoke workflow now runs every DOM/unit suite plus the readiness safety
unit tests. Review PoC Compose flag defaults to `0`; this change does not enable it.

## Verification on the combined baseline

| Command | Actual result |
| --- | --- |
| `cd apps/web && npm test` | **214 PASS, 0 FAIL, 0 SKIP**; 9 discovered files; 43.283 s |
| `cd apps/web && npm run build` | **PASS** TypeScript and Vite; existing bundle-size warning above 500 kB |
| `python -m unittest discover -s tools/readiness -p test_safety.py -v` | **3 PASS**; no database touched |
| `git diff --check` | **PASS** |
| Docker/Compose build and Linux container execution | **NOT_RUN locally:** Docker and Podman executables are absent; coordinator must verify GitHub Actions |

Environment: Windows, Node `v24.15.0`, npm `11.12.1`, locked dependencies installed
with `npm ci`; existing private Python QA venv. No dependency versions changed.
The explicit native Chromium harnesses, Android, external Drive and provider AI are
not included in these unit counts. Root owns final combined acceptance and CI results.

Rollback: revert this runner/packaging change together; the old runner executes only
`ui.test.mjs`, so reverting loses automatic coverage for the new task suites.
