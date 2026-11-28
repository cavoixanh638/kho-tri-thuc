# Private source viewer — integration checkpoint (20/11/2026)

Status: PASS for the implemented integration scope; branch `codex/notes-ux-viewer`, baseline `5576d84` (PR48–56 combined). Code SHA/Tested SHA: `30a40f0` (full SHA in Git); evidence-only commit follows it.
Scope: private authenticated bytes and lazy source-locator host integration. No PR merge, deployment or production/Drive access.

- Added `storage.viewer_api` to the API: GET descriptor, GET/HEAD bytes pinned by internal Asset UUID/content version/SHA-256. Only owner/nondeleted verified audio/video/PDF assets qualify.
- Extended StoragePort/DriveStorage with a bounded range read. Actual one-byte range probe precedes descriptor acknowledgement. Drive transport requires 206/exact Content-Range/Content-Length, identity encoding, no redirects and at most 4 MiB; checks SHA/revision/identity before and after each read. No disk/cache/full download.
- SourceLocatorCitation obtains that descriptor only after an explicit user action; aborts late responses, validates exact versioned same-origin path, retains original-source fallback. Native PDF page navigation remains NOT_RUN/false.

PASS on the code SHA: 27 affected PostgreSQL/native tests (13 new unit + 1 optional native browser test); 13 locator DOM tests (3 new); frontend build; changed Python files Ruff check/format. A broad legacy storage Ruff check exposes existing migration/import findings outside this change; no unrelated fixes made. Build retains its existing >500 kB bundle warning.

Native Chrome acceptance **PASS**: Chrome157.0.8103.79 on Windows; generated stereo PCM16 WAV48kHz30s (>4MiB) and VP8 WebM320×18022s; actual Django session/descriptor/bytes endpoints with injected synthetic StoragePort. **23 audio +20 video targets**, including audio24/26/28s beyond the first4MiB slice; maximum error0s, tolerance1s. Six explicit HTTP206 probes cover closed/open-ended/tail ranges; anonymous requests401. QA DB `test_kt_ux_viewer_browser`, loopback62224, no provider traffic. Screenshots at1440/768/390 showed no document overflow;1440/390 evidence retained. Both fixtures decoded as their actual codecs/durations, not thumbnails. See [machine report](INTEGRATION-VIEWER-BROWSER.json), [desktop](integration-viewer-1440.png) and [narrow screen](integration-viewer-390.png). These images are the focused test harness, not the complete app screen.

The host boundary is now connected. Production Drive streaming, native PDF page navigation, Android and broader codecs/devices remain NOT_RUN. Unknown/no checksum/revision, stale version, unsupported media or missing private access fail closed and retain the source-original fallback. PDF descriptor exposes range capability but `pageNavigationVerified=false`, so the UI does not claim a page jump. Full GET of files larger than4MiB returns416 requiring a Range; valid `bytes=0-` returns206 capped at4MiB and native Chrome successfully requests/plays later audio positions. Each byte request revalidates provider identity/SHA/monotonic revision around the bounded read. This intentionally trades extra metadata calls for integrity, and needs real Drive quota/latency acceptance before release. There is no persistent cache, migration, external service, new dependency, production write or background transcription.

Commands (environment-only QA secrets omitted):

```powershell
# POSTGRES_HOST=127.0.0.1; POSTGRES_PORT=62224; POSTGRES_DB=kt_ux_viewer_browser
# KT116_BROWSER_NATIVE=1; KT116_CDP_HELPER=<existing design-taste CDP helper>; FFMPEG_BINARY=<installed FFmpeg9.0.2>
python manage.py test storage.test_viewer storage.test_viewer_browser storage.test_drive_storage storage.test_drive_transport processing.test_kt116_locators --noinput -v 1
node --test tests/kt116-locators.test.mjs
npm run build
```

Native browser acceptance is opt-in and skipped by default CI; its PostgreSQL host/DB guard prevents accidental production use. Generated media were temporary and removed; no media/dump/credentials were committed. The small report contains synthetic UUIDs/hashes only. No PR was merged and no Windows runtime was deployed. Rollback: omit this integration commit; the existing original-source link remains available.

Contract docs: Google officially supports partial blob downloads with `Range`, but does not support partial Google Workspace export: <https://developers.google.com/workspace/drive/api/guides/manage-downloads>. This implementation handles original blobs only and uses the existing OAuth/request stack, adding no dependency.
