# P17 — Offline media intake / fault-injection evaluation

**Scope:** frozen HEAD `9716a6a876d6ec41e10b3c3dcbdc095ab4ddd84d`; this is not a production deployment. All URLs and bytes are **synthetic**. Nothing here requests the public websites, Google Drive, PostgreSQL, FFmpeg, or ASR, nor claims 10,000 actual media downloads.

## Reproduce (from repository root)

```sh
python -m unittest discover -s tools/media -p 'p17_test.py' -v
python tools/media/p17_media_eval.py --output /tmp/p17-results.json
```

The first command checks independent fixtures and strict full-byte verification oracle; the last test invokes the **actual source identity / video manifest / network boundary code** only when the repo source files exist. The second command requires the checkout with `apps/backend` and imports these modules without Django/DB. If the original production code cannot be imported or behavior differs, it **fails closed**. No network connection or credentials are needed.

Fixture files:
- `sources.json`: **50 unique synthetic URLs** (20 Facebook, 15 YouTube Shorts, 15 TikTok). Facebook direct downloader accepts only supported URL shapes, other platforms are **metadata/link only** for this download path. URL recognition does not mean playback or downloaded bytes.
- `states.json`: **8 distinct media/transcript/thumbnail combinations**, distinguishing captured/metadata-only/downloaded-unverified/stored-verified/transcript-pending/done/unavailable/failed.
- `faults.json`: **47 cases**: 14 actual `video_download._result` manifest cases; 21 full-byte storage verification **oracle** cases; 12 retry-policy **mirror** cases. The mirror does not exercise `JobRepository` or Drive API.

**Definition of verified:** source bytes, source SHA-256 and length, asset UUID & owner identity, nonempty Drive file locator, verified location, remote byte length and remote SHA-256, **complete Drive readback bytes** with the same digest. Metadata-only, DB status `verified`, checksum supplied by a fake provider, and a single HTTP range do not constitute live verification.

## Findings / potential bugs requiring independent integration follow-up

1. **P17-MANIFEST-JSON:** `processing.video_download._result` loads child `result.json` via `json.loads` without catching `JSONDecodeError`. A malformed child result reaches the parent as an unhandled exception; `download_facebook` catches only `VideoDownloadError`, `OSError`, `ValueError`, and subprocess errors. Since `JSONDecodeError` subclasses `ValueError`, `download_facebook` maps this to generic `video_download_failed` / retryable; standalone `_result` still escapes raw `JSONDecodeError` (fault fixture M-10). Confirm through full worker path; do not change shared source in P17.
2. **P17-HTTP-CODES:** child error taxonomy does not encode HTTP 429 or 403 separately: generic `video_download_failed` is non-retryable for child-reported `video_429` or `video_403` in `_result` (M-07/M-08). Real platform responses remain **NOT_RUN**, so these are contract injections, not observed online HTTP behavior.
3. **P17-DRIVE-EVIDENCE:** `DriveStorage._record_verified` can set DB status `verified` on remote metadata without a full byte-by-byte Drive readback; if Drive does not return `sha256Checksum`, the code still accepts matching size/MIME and (optionally) MD5. Under P17's stricter **stored_media_verified** criterion this is **INSUFFICIENT_EVIDENCE**, not a claim that the uploaded file is corrupt.
4. **P17-PLATFORM-COVERAGE:** direct downloader is Facebook-only; YouTube/TikTok URLs may still produce page metadata, but cannot satisfy 10k original-media storage objective by this path.
5. **P17-BOUNDS:** `MAX_VIDEO_BYTES=128MiB`, `TIMEOUT_SECONDS=120`; video probe requires audio and video, ASR requires verified Drive location, local model, and bounded duration. Do not infer support for arbitrary 100GB media or large individual files.
6. **P17-RETRY:** worker repository policy max five attempts and backoff 5/10/20/40 seconds (5th retryable failure terminal); lease 10 minutes. Resumable upload transport does not mean resumable **Facebook downloading** across process restart (`continuedl=False`).

## Metrics and limitations

`synthetic_metadata.items=10000` measures only in-memory indexing of synthetic records; no DB query/worker throughput, media byte storage, concurrency, cache quota, Drive readback latency, rate limits or long-running recovery were measured. The 21 readback cases are strict **simulation/oracle**, not a Drive client adapter nor a successful real Drive round-trip. Real PDF thumbnails, video decode and ASR are all NOT_RUN. Failure status and retry expectation coverage are **contracts**, not throughput benchmarks.

**G00 integration request:** Add a separate integration test with ephemeral PostgreSQL + fake Drive client that injects 429/403/timeouts and verifies Asset/StorageLocation + Job lease/idempotency; run explicit full Drive readback of consented small files under test account, then staged 100/1k/10k consented objects and >=100GB only when resource/permission budget is approved. Keep existing user data untouched. No changes to worker/Drive/API were made in this PR.
