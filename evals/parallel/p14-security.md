# P14 — Independent security audit of frozen PR58 snapshot and PR62 Vault WIP

**Date:** 2026-11-21. **Scope:** frozen base `9716a6a876d6ec41e10b3c3dcbdc095ab4ddd84d` (underlying PR58 code `91fe93950224e688471032313367bc5961385b59`); PR62 read-only WIP `a61cc219f2a30beae7d5496f493469bb986bc54a`. **No merge, deploy, production request, credentials, DB or Drive activity.**

## Executive disposition

**HOLD integration of PR62 Vault until blockers are addressed and adversarial tests pass.** Frozen code contains meaningful auth/owner checks, bounded HTTP fetching, pinned private viewer access and safe Markdown rendering, but this is **not** a runtime penetration-test certification. Existing PR58 baseline CI is FAIL in frontend unit; unrelated later stages were skipped.

- **P14-SEC-01 — HIGH / BLOCKER for portable Vault deployment (PR62):** URL secret screening in `apps/backend/catalog/vault.py:127-135` only rejects a narrow set of query keys. Synthetic references `https://safe.example/?token=synthetic-placeholder` and `?sig=synthetic-placeholder` are not rejected by `check_url`; other secret-like query parameters similarly merit test. The export includes all `Source.original_url` values at `vault.py:150-162, 200-209`. A secret-containing URL can enter the archive unless a different upstream validation blocks it. **Recommended minimum:** centralize an allowlist/reject policy for sensitive query/fragment keys, use a conservative case-insensitive alias set and URL parsing, redact/block before serialization; do not log secret-bearing URLs. Scope: WIP PR62 only, **not integrated on frozen**. Repro: `python tools/security/p14_audit.py --wip-vault /tmp/p14-vault.py SecurityAbuseTests.test_29_vault_unrecognized_secret_url_aliases`. **Expected:** blocked with `VaultError`. **Observed from source:** no rejection for these aliases; runnable regression to confirm when read-only WIP file is provided.
- **P14-SEC-02 — HIGH / BLOCKER for selective Vault import (PR62):** `apply_import` builds *all* topics/projects/tags from `data[name]` at `vault.py:491-511` and *all* collections at `vault.py:606-618`, even when `selected` excludes every associated note. Selection checks govern items, not these writes. This is an unauthorized-scope **integrity and user-expectation** issue, not demonstrated cross-user IDOR. **Recommended minimum:** preview precisely which structure and collections will be imported; apply only selected note dependency closure or get separate explicit authorization for ancillary metadata, with idempotent rollback tests. Repro: `python tools/security/p14_audit.py --wip-vault /tmp/p14-vault.py SecurityAbuseTests.test_30_vault_import_respects_selected_item_scope`. **Expected:** every persisted collection scoped to explicit selection/authorization. **Observed from source:** missing selected guard; DB behavioral confirmation NOT_RUN.
- **P14-SEC-03 — MEDIUM / incomplete archive trust boundary (PR62):** `parse_vault` caps member count, declared uncompressed size and per-file size (`vault.py:254-273`), rejects traversal and symlink entries, but deserializes a manifest without an independent manifest-specific max; a large manifest within the 64 MiB global expansion cap can create avoidable memory/JSON complexity. **Recommended:** explicit manifest cap and schema-specific limits on number/depth of all collections; test adversarially on disposable process.
- **P14-SEC-04 — MEDIUM / authenticated-source URL exposure risk (frozen + WIP):** `catalog/api.py:146-184` returns original source URLs and `processing/knowledge.py:164-175` exports source URLs, while `ingestion/source_identity.py:91-129` enforces syntax/public hostname rather than stripping arbitrary token-bearing query parameters. This is not an inter-user leak (owner scope exists), but can persist or export sensitive URL query strings. **Recommended:** explicit policy warning plus secret-sensitive URL handling at capture/export; avoid logging raw URLs.

## 30 abuse-case matrix

Legend: **SOURCE_CHECK** = reviewed static guards only (does not imply runtime PASS); **HARNESS_READY** = isolated source-function test committed, execution NOT_RUN here; **NOT_RUN** = requires disposable Django/PostgreSQL/browser or PR62 file; **EXPECTED_FAIL** = source-backed regression against PR62, must be executed before clearance. All commands below are relative to repository root; `python tools/security/p14_audit.py -v` runs the 30-case harness (local Python stdlib, no network). Where `--wip-vault` is needed, first obtain exact PR62 `apps/backend/catalog/vault.py` into `/tmp/p14-vault.py` without merging.

| ID | Abuse case | Expected | Source-backed actual / status | Severity if violated |
| --- | --- | --- | --- | --- |
| 01 | Login without CSRF | HTTP 403 | `config/test_session.py:14-29` asserts 403; SOURCE_CHECK, runtime NOT_RUN | HIGH |
| 02 | Logout without CSRF | HTTP 403 | Session DELETE and CSRF middleware present; SOURCE_CHECK, runtime NOT_RUN | HIGH |
| 03 | Anonymous API sweep | Auth denial on private routes | NOT_RUN (DB/API runtime absent) | CRITICAL |
| 04 | Private routers auth | `django_auth` on routers | Source contracts present; HARNESS_READY | HIGH |
| 05 | Read another user's Item UUID | 404/no data | `catalog/api.py:114, 228-230` owner-filtered; SOURCE_CHECK | CRITICAL |
| 06 | Patch another user's Item | 404/no mutation | `catalog/api.py:248-251` owner-filtered; SOURCE_CHECK | CRITICAL |
| 07 | Read another user's Capture history | 404/no data | `ingestion/api.py:150-161` owner-filtered; SOURCE_CHECK | HIGH |
| 08 | Foreign DerivedContent in Clip preview | 404/no excerpt | `processing/clips.py:99-117` owner-filtered; SOURCE_CHECK | HIGH |
| 09 | Reuse cross-owner/expired signed clip receipt | 404/invalid receipt | `processing/clips.py:185-194` TTL 300s and owner comparison; SOURCE_CHECK | HIGH |
| 10 | Read/edit foreign SavedCollection | 404/no data | `catalog/collection_api.py:98-115` owner-filtered; SOURCE_CHECK | HIGH |
| 11 | OAuth state swap/replay/expiry | Reject unauthorized callback | `storage/oauth.py:69-79` owner/state/TTL; SOURCE_CHECK | CRITICAL |
| 12 | SSRF non-HTTP scheme | Block before transport | `processing/source_http.py:68-75`; HARNESS_READY | CRITICAL |
| 13 | SSRF URL userinfo | Block before transport | `source_http.py:74-75`; HARNESS_READY | HIGH |
| 14 | SSRF loopback/RFC1918/metadata IPv4 | Block | `source_http.py:142-167`; HARNESS_READY | CRITICAL |
| 15 | SSRF loopback/ULA/mapped IPv6 | Block | `source_http.py:142-167`; HARNESS_READY | CRITICAL |
| 16 | DNS mixed public/private answers | Block entire resolution | `source_http.py:153-167`; HARNESS_READY | CRITICAL |
| 17 | Redirect to 127.0.0.1 | Revalidate/block | `source_fetch.py:255-286`; HARNESS_READY | CRITICAL |
| 18 | Redirect infinite chain | Bounded denial | `source_fetch.py:255-278`; HARNESS_READY | HIGH |
| 19 | DNS-rebinding/proxy hop | Only validated resolved IP, TLS verify host | `source_http.py:200-269`; SOURCE_CHECK | CRITICAL |
| 20 | Oversized/encoded HTML body | Bounded read, reject unsupported encodings | `source_http.py:221-247`; SOURCE_CHECK | HIGH |
| 21 | Script payload in fetched HTML | Script not extracted | `source_fetch.py:83-94,146-156`; HARNESS_READY | HIGH |
| 22 | Foreign asset viewer UUID | 404/no bytes | `storage/viewer_api.py:46-52,75-82`; SOURCE_CHECK | CRITICAL |
| 23 | Multi-range/invalid Range header | HTTP 416 | `viewer_api.py:101-121`; HARNESS_READY | MEDIUM |
| 24 | Huge/suffix byte range | Cap 4 MiB, valid suffix | `viewer_api.py:101-121`; HARNESS_READY | HIGH |
| 25 | Replay stale preview SHA/If-Range | 409/412, no-store | `viewer_api.py:124-168`; SOURCE_CHECK | HIGH |
| 26 | HTML/JS Markdown link and raw HTML | No executable HTML, no javascript scheme | `KnowledgeText.tsx:9-26`, `api.ts:87-96`; SOURCE_CHECK, browser NOT_RUN | HIGH |
| 27 | ZIP `../`, absolute path or symlink | Reject | PR62 `vault.py:90-98,263-267`; HARNESS_READY with WIP; NOT_RUN | CRITICAL |
| 28 | ZIP decompression bomb | Declared total + file caps | PR62 `vault.py:254-272`; HARNESS_READY with WIP; NOT_RUN | HIGH |
| 29 | Source URL with secret-like `token`/`sig` | Reject at export/import | PR62 `vault.py:127-135`: missing aliases; EXPECTED_FAIL; NOT_RUN | HIGH |
| 30 | Import unselected groups/collections | No unapproved side effects | PR62 `vault.py:491-511,606-618`: unconditional writes; EXPECTED_FAIL; DB NOT_RUN | HIGH |

## Security-specific review and nonclaims

- **CSRF:** `config/settings.py:25-31` includes Django CSRF middleware, `config/session.py` uses GET/POST/DELETE and existing session tests check token rotation. Django Ninja cookie-auth requests also require effective CSRF validation; this has **not been demonstrated across all registered endpoints in a live client**. Make anonymous / cross-site POST/PATCH/DELETE matrix an integration gate.
- **Auth/IDOR:** direct owner filters were found in Item, Capture, Clip, SavedCollection, viewer and navigator routes. This is **not** a verified exhaustive graph/foreign-key review; nested references and restored Vault mappings need cross-owner DB fixtures.
- **Signed previews:** clip receipts are signed/TTL-bound; viewer endpoint returns a **version-pinned same-origin URL, not a presigned URL**, thus no signed viewer URL TTL exists to verify. Do not misreport signed viewer preview TTL.
- **SSRF:** fetch logic uses validated IPs and revalidates redirected URLs. A mock resolver/transport does not prove proxies, host firewall, DNS resolver isolation, TLS or media downloader behavior in production.
- **ZIP:** read-only PR62 WIP is **not registered as an API on frozen**. ZIP test does not authorize deployment or import. Separately, the existing backup ZIP uses a fixed member allowlist and stored entries (`tools/backup/drive_bundle.py:35-100`).
- **Secrets:** there are no real secrets in fixture files. Regex in `processing/knowledge.py:17-20` is not a comprehensive data-loss-prevention system. Never include captured credentials in reports/test logs.
- **Migrations:** catalog migrations 0005/0006/0007 and existing backup schema 3 exist on frozen, but cross-version restoration, schema4 draft, and migration reversibility were not run. G00 must execute fresh-DB migrate/rollback/restore before enabling Vault.
- **Known baseline:** PR58 CI FAIL, so isolated/source checks do not supersede the failing whole-app gate.

## Minimal corrections requested, owned by G00 or relevant module owner

1. **PR62 Vault owner:** harden URL credentials policy and test a realistic spectrum of query/fragment aliases (P14-SEC-01), fail closed on secret-like sources or omit them with a redacted provenance warning.
2. **PR62 Vault owner:** ensure selected-import closure and explicit consent for metadata-only writes; add transactional rollback and cross-owner assertions (P14-SEC-02).
3. **PR62 Vault owner:** bound manifest size/collection counts/depth before deserialization and validate all foreign keys, including metadata-only collections (P14-SEC-03).
4. **G00 integration:** bring P14 harness into test environment; run PostgreSQL two-owner IDOR test matrix, CSRF browser/cookie test, malicious ZIP fixture, actual signature expiry, HTTP Range via authenticated viewer, and migration/restore. Keep PR62 unmerged until the blocking tests pass.

## Reproduction and rollback

- Frozen local checkout: `python tools/security/p14_audit.py -v`.
- Optional WIP audit: `git show a61cc219f2a30beae7d5496f493469bb986bc54a:apps/backend/catalog/vault.py > /tmp/p14-vault.py`, then `python tools/security/p14_audit.py --wip-vault /tmp/p14-vault.py -v`. Do **not** stage, import, merge or execute the WIP module itself.
- All fixture URLs use `safe.example` and synthetic placeholders; transport tests use in-process mock callables. No external endpoints are called.
- G00 can discard P14 by closing its PR/deleting its independent branch. No product/runtime files were touched.

**Test run state in this execution context:** source review and GitHub-file verification completed; Python harness / PostgreSQL / browser / WIP fixture runtime were **NOT_RUN** because this agent does not have a checkout with dependencies and a disposable test database. No assertion of 30 PASS is made.