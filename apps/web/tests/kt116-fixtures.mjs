// Synthetic ground truth: each row names the expected asset/source version independently.
export const locatorCases = [
  ['pdf-first', 'pdf-a', 'hash-a', { page: 1 }, 'pdf', 'AVAILABLE', 1],
  ['pdf-last', 'pdf-b', 'hash-b', { page: 200 }, 'pdf', 'AVAILABLE', 200],
  ['pdf-other-version', 'pdf-b', 'hash-c', { page: 8 }, 'pdf', 'AVAILABLE', 8],
  ['pdf-schema1', 'pdf-a', 'hash-a', { schema_version: 1, page: 4 }, 'pdf', 'AVAILABLE', 4],
  ['pdf-zero', 'pdf-a', 'hash-a', { page: 0 }, 'pdf', 'MISSING_LOCATOR'],
  ['pdf-fraction', 'pdf-a', 'hash-a', { page: 1.2 }, 'pdf', 'MISSING_LOCATOR'],
  ['pdf-string', 'pdf-a', 'hash-a', { page: '4' }, 'pdf', 'MISSING_LOCATOR'],
  ['pdf-future-schema', 'pdf-a', 'hash-a', { schema_version: 2, page: 4 }, 'pdf', 'MISSING_LOCATOR'],
  ['audio-zero', 'audio-a', 'hash-d', { start_ms: 0 }, 'media', 'AVAILABLE', 0],
  ['audio-ms', 'audio-a', 'hash-d', { start_ms: 1250 }, 'media', 'AVAILABLE', 1.25],
  ['audio-seconds', 'audio-b', 'hash-e', { start_seconds: 12.345 }, 'media', 'AVAILABLE', 12.345],
  ['audio-negative', 'audio-a', 'hash-d', { start_seconds: -1 }, 'media', 'MISSING_LOCATOR'],
  ['audio-ambiguous', 'audio-a', 'hash-d', { start_seconds: 2, start_ms: 2000 }, 'media', 'MISSING_LOCATOR'],
  ['audio-bad-end', 'audio-a', 'hash-d', { start_seconds: 5, end_seconds: 4 }, 'media', 'MISSING_LOCATOR'],
  ['video-seconds', 'video-a', 'hash-f', { start_seconds: 20 }, 'media', 'AVAILABLE', 20],
  ['video-ms', 'video-b', 'hash-g', { start_ms: 999 }, 'media', 'AVAILABLE', .999],
  ['video-segment', 'video-a', 'hash-f', { start_seconds: 1, end_seconds: 3 }, 'media', 'AVAILABLE', 1],
  ['video-section-no-inference', 'video-a', 'hash-f', { section: '00:01–00:04' }, 'media', 'NOT_SUPPORTED'],
  ['web-section', null, 'web-hash-a', { source_id: 21, section: 'Introduction' }, 'web', 'NOT_SUPPORTED'],
  ['web-source-only', null, 'web-hash-b', { source_id: 22 }, 'web', 'MISSING_LOCATOR'],
  ['web-missing-source', null, 'web-hash-b', { source_id: 22, section: 'Text' }, 'missing', 'MISSING_ASSET'],
  ['web-stale', null, 'web-hash-c', { source_id: 23, section: 'Text' }, 'stale', 'STALE_SOURCE'],
  ['asset-missing', 'pdf-a', 'hash-a', { page: 3 }, 'missing', 'MISSING_ASSET'],
  ['asset-stale', 'pdf-a', 'hash-old', { page: 3 }, 'stale', 'STALE_SOURCE'],
  ['asset-unverified', 'pdf-a', 'hash-a', { page: 3 }, 'unverified', 'NOT_SUPPORTED'],
  ['no-locator', 'pdf-a', 'hash-a', {}, 'pdf', 'MISSING_LOCATOR'],
  ['unsupported-sheet', 'sheet-a', 'hash-h', { sheet: 'Data', row: 3 }, 'sheet', 'MISSING_LOCATOR'],
  ['thumbnail-is-not-stream', 'video-a', 'hash-f', { start_seconds: 2 }, 'thumbnail', 'NOT_SUPPORTED'],
  ['drive-is-not-stream', 'video-a', 'hash-f', { start_seconds: 2 }, 'drive', 'NOT_SUPPORTED'],
  ['wrong-viewer-version', 'pdf-a', 'hash-a', { page: 1 }, 'wrong-version', 'STALE_SOURCE'],
];
export function materialize(row, index) {
  const [name, asset, version, locator, mode] = row;
  const mime = asset?.startsWith('pdf') ? 'application/pdf' : asset?.startsWith('audio') ? 'audio/wav' : 'video/webm';
  const part = { id: index, kind: asset ? 'document_text' : 'web_text', asset_id: asset, locator, processor: 'fixture', processor_version: 'v1',
    source: { state: ['missing', 'stale', 'unverified'].includes(mode) ? mode : 'current', version, asset_version: asset ? 7 : null,
      source_id: asset ? null : locator.source_id, source_url: asset ? null : 'https://example.invalid/article', mime: asset ? mime : null } };
  let viewer;
  if (asset && ['pdf', 'media', 'wrong-version', 'thumbnail', 'drive'].includes(mode)) {
    viewer = { assetId: asset, assetVersion: 7, version: mode === 'wrong-version' ? 'different' : version,
      url: mode === 'thumbnail' ? `/api/v1/assets/${asset}/thumbnail` : mode === 'drive' ? 'https://drive.google.com/open?id=fixture' : `/api/v1/assets/${asset}/stream`,
      kind: mime === 'application/pdf' ? 'pdf' : 'media', pageNavigationVerified: true, rangeVerified: true };
  }
  return { name, part, viewer };
}
