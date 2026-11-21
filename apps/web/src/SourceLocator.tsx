import { useEffect, useRef, useState } from 'react';
import { ApiError, request } from './api';
import './SourceLocator.css';

export type SourceEvidence = {
  state: 'current' | 'stale' | 'missing' | 'unverified';
  version: string; source_id: number | null; source_url: string | null;
  mime: string | null; asset_version: number | null;
};
export type SourcePart = {
  id: number; kind: string; asset_id: string | null; locator: Record<string, unknown>;
  processor: string; processor_version?: string; source?: SourceEvidence;
};
export type Locator = { kind: 'page'; page: number } | { kind: 'time'; seconds: number; end?: number }
  | { kind: 'section'; section: string };
export type LocatorState = 'AVAILABLE' | 'MISSING_LOCATOR' | 'MISSING_ASSET' | 'STALE_SOURCE' | 'NOT_SUPPORTED';
// A host must supply verified, authenticated byte endpoints. Drive /open and thumbnails are never viewers.
export type SourceViewer = {
  assetId: string; version: string; assetVersion: number; url: string;
} & ({ kind: 'pdf'; pageNavigationVerified: true } | { kind: 'media'; rangeVerified: true });
export type LocatorResolution = { state: LocatorState; locator?: Locator; label: string; reason: string; viewer?: SourceViewer;
  association: { assetId: string | null; sourceId: number | null; version: string | null; processorVersion: string | null } };

const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value) && value >= 0;
export function parseLocator(raw: Record<string, unknown>): Locator | undefined {
  if (raw.schema_version != null && raw.schema_version !== 1) return undefined;
  if ('page' in raw) return Number.isSafeInteger(raw.page) && Number(raw.page) > 0 ? { kind: 'page', page: Number(raw.page) } : undefined;
  if ('start_ms' in raw || 'start_seconds' in raw) {
    if ('start_ms' in raw && 'start_seconds' in raw) return undefined;
    const value = raw.start_ms ?? raw.start_seconds;
    if (!finite(value)) return undefined;
    const seconds = 'start_ms' in raw ? value / 1000 : value;
    const end = raw.end_seconds;
    if (end != null && (!finite(end) || end < seconds)) return undefined;
    return { kind: 'time', seconds, ...(end == null ? {} : { end: Number(end) }) };
  }
  // A section name is descriptive. It is never parsed as a timestamp or invented DOM anchor.
  if (typeof raw.section === 'string' && raw.section.trim()) return { kind: 'section', section: raw.section.trim().slice(0, 200) };
  return undefined;
}
export function transcriptSegments(raw: Record<string, unknown>): { text: string; locator: Record<string, unknown> }[] {
  if (raw.schema_version != null && raw.schema_version !== 1) return [];
  if (!Array.isArray(raw.segments) || raw.segments.length > 1000) return [];
  const rows: { text: string; locator: Record<string, unknown> }[] = [];
  let last = 0;
  let characters = 0;
  for (const row of raw.segments) {
    if (!row || typeof row !== 'object' || !finite(row.start) || !finite(row.end) || row.start < last || row.end < row.start
      || typeof row.text !== 'string' || !row.text.trim()) return [];
    characters += row.text.length;
    if (characters > 100_000) return [];
    rows.push({ text: row.text, locator: { start_seconds: row.start, end_seconds: row.end } });
    last = row.start;
  }
  return rows;
}
export function locatorLabel(locator?: Locator): string {
  if (!locator) return 'Văn bản trích từ nguồn';
  if (locator.kind === 'page') return `Trang ${locator.page}`;
  if (locator.kind === 'section') return locator.section;
  const minutes = Math.floor(locator.seconds / 60);
  return `${minutes}:${(locator.seconds % 60).toFixed(3).padStart(6, '0').replace(/\.?0+$/, '')}`;
}
export function privateViewerUrl(value: string): string | undefined {
  // Relative, same-origin cookie-authenticated endpoints only; no query credentials or remote redirects by construction.
  if (!/^\/api\/v1\/assets\/[A-Za-z0-9_-]{1,128}\/(bytes|stream|content)(?:\/[1-9][0-9]{0,9}\/[a-f0-9]{64})?$/.test(value)) return undefined;
  return value;
}
export function safeOriginalUrl(value: string): string | undefined {
  try {
    const url = new URL(value);
    if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password) return undefined;
    // Never propagate bearer credentials, signed URLs or OAuth data to another tab/referrer.
    for (const parameters of [url.searchParams, new URLSearchParams(url.hash.slice(1))]) {
      for (const key of parameters.keys()) if (/token|secret|signature|credential|authorization|api.?key|bearer/i.test(key)) return undefined;
    }
    return url.href;
  } catch { return undefined; }
}
export function resolveLocator(part: SourcePart, viewer?: SourceViewer): LocatorResolution {
  const locator = parseLocator(part.locator);
  const base = { locator, label: locatorLabel(locator), association: { assetId: part.asset_id, sourceId: part.source?.source_id ?? null, version: part.source?.version ?? null, processorVersion: part.processor_version ?? null } };
  if (part.source?.state === 'stale') return { ...base, state: 'STALE_SOURCE', reason: 'Nguồn đã đổi phiên bản. Cần trích lại trước khi định vị.' };
  if (part.source?.state === 'missing' || (!part.asset_id && !part.source?.source_id)) return { ...base, state: 'MISSING_ASSET', reason: 'Không còn nguồn đã xác minh cho phần trích này.' };
  if (!locator) return { ...base, state: 'MISSING_LOCATOR', reason: 'Chưa có vị trí tin cậy; có thể mở nguồn gốc.' };
  if (!part.source || part.source.state !== 'current' || !part.source.version) return { ...base, state: 'NOT_SUPPORTED', reason: 'Chưa xác minh phiên bản nguồn; không thể định vị.' };
  if (viewer && (viewer.assetId !== part.asset_id || viewer.version !== part.source.version || viewer.assetVersion !== part.source.asset_version)) {
    return { ...base, state: 'STALE_SOURCE', reason: 'Tệp đang mở không khớp phiên bản đã trích. Cần tải lại nguồn.' };
  }
  if (viewer && viewer.url.split('/').length > 6 && viewer.url !== `/api/v1/assets/${part.asset_id}/content/${part.source.asset_version}/${part.source.version}`) {
    return { ...base, state: 'STALE_SOURCE', reason: 'Đường dẫn tệp không khớp phiên bản đã trích. Cần tải lại nguồn.' };
  }
  const supports = viewer && privateViewerUrl(viewer.url) && viewer.url.split('/')[4] === encodeURIComponent(part.asset_id ?? '') && ((locator.kind === 'page' && viewer.kind === 'pdf' && viewer.pageNavigationVerified && part.source.mime === 'application/pdf')
    || (locator.kind === 'time' && viewer.kind === 'media' && viewer.rangeVerified === true && /^(audio|video)\//.test(part.source.mime ?? '')));
  if (!supports) return { ...base, state: 'NOT_SUPPORTED', reason: locator.kind === 'section' ? 'Chưa xác định được đoạn này trên trang gốc. Có thể mở website nguồn.' : 'Chưa thể mở đúng vị trí trong nguồn này. Có thể mở file gốc.' };
  return { ...base, state: 'AVAILABLE', reason: 'Mở vị trí trên nguồn đã xác minh.', viewer };
}
const stateText: Record<LocatorState, string> = {
  AVAILABLE: 'Có thể định vị', MISSING_LOCATOR: 'Thiếu vị trí', MISSING_ASSET: 'Thiếu nguồn', STALE_SOURCE: 'Nguồn đã thay đổi', NOT_SUPPORTED: 'Chưa hỗ trợ định vị',
};
export function seekMedia(media: HTMLMediaElement, seconds: number): void {
  if (!finite(seconds) || !Number.isFinite(media.duration) || seconds > media.duration) throw new Error('invalid_target');
  let seekable = false;
  for (let index = 0; index < media.seekable.length; index += 1) {
    if (media.seekable.start(index) <= seconds && seconds <= media.seekable.end(index)) seekable = true;
  }
  if (!seekable) throw new Error('not_seekable');
  media.currentTime = seconds;
}
function SourceLocatorMedia({ viewer, locator, mime }: { viewer: SourceViewer; locator: Extract<Locator, { kind: 'time' }>; mime: string }) {
  const mediaRef = useRef<HTMLMediaElement>(null);
  const [message, setMessage] = useState('Đang tải nguồn để định vị…');
  const pending = useRef(true);
  useEffect(() => { pending.current = true; setMessage('Đang tải nguồn để định vị…'); }, [viewer.url, locator.seconds]);
  const seek = () => {
    if (!pending.current || !mediaRef.current) return;
    try { seekMedia(mediaRef.current, locator.seconds); pending.current = false; setMessage('Đang chuyển đến mốc đã chọn…'); }
    catch { setMessage('Nguồn chưa cho phép seek tới mốc này. Có thể thử lại sau khi tải.'); }
  };
  const props = { ref: mediaRef, src: viewer.url, controls: true, preload: 'metadata', onLoadedMetadata: seek, onProgress: seek, onCanPlay: seek,
    onSeeked: () => setMessage(Math.abs((mediaRef.current?.currentTime ?? -10) - locator.seconds) <= 1 ? `Đã đến ${locatorLabel(locator)}.` : 'Player chưa đến đúng mốc đã chọn.'),
    onError: () => { pending.current = false; setMessage('Không tải được nguồn (quyền truy cập, tệp hết hạn hoặc định dạng không hỗ trợ).'); } } as const;
  return <div className="source-locator-viewer">
    {mime.startsWith('audio/') ? <audio {...props} ref={mediaRef as React.RefObject<HTMLAudioElement>} /> : <video {...props} ref={mediaRef as React.RefObject<HTMLVideoElement>} />}
    <p role="status">{message}</p><button type="button" onClick={() => { pending.current = true; seek(); }}>Đến mốc đã chọn</button>
  </div>;
}
export function SourceLocatorCitation({ part, viewer, onIllustration }: { part: SourcePart; viewer?: SourceViewer; onIllustration?: (assetId: string) => void }) {
  const [privateViewer, setPrivateViewer] = useState<SourceViewer>();
  const result = resolveLocator(part, viewer ?? privateViewer);
  const [opened, setOpened] = useState(false);
  const [original, setOriginal] = useState<string>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const revision = `${part.id}:${part.asset_id}:${part.source?.source_id}:${part.source?.version}:${part.source?.asset_version}:${part.source?.mime}:${part.source?.state}:${part.processor_version}:${JSON.stringify(part.locator)}`;
  const currentRevision = useRef(revision);
  const inFlight = useRef<AbortController | null>(null);
  currentRevision.current = revision;
  useEffect(() => {
    setOpened(false); setPrivateViewer(undefined); setOriginal(undefined); setError(''); setBusy(false);
    return () => { inFlight.current?.abort(); currentRevision.current = ''; };
  }, [revision]);
  useEffect(() => { currentRevision.current = revision; }, [revision]);
  const loadViewer = async () => {
    if (!part.asset_id || busy) return;
    const controller = new AbortController(); inFlight.current?.abort(); inFlight.current = controller;
    const stillCurrent = () => !controller.signal.aborted && currentRevision.current === revision;
    setBusy(true); setError('');
    try {
      const value = await request<SourceViewer>(`/assets/${encodeURIComponent(part.asset_id)}/viewer`, { signal: controller.signal });
      if (value.url !== `/api/v1/assets/${part.asset_id}/content/${part.source?.asset_version}/${part.source?.version}`) throw new Error('unpinned_viewer');
      const resolved = resolveLocator(part, value);
      if (resolved.state !== 'AVAILABLE') throw new Error('not_supported');
      if (stillCurrent()) { setPrivateViewer(value); setOpened(true); }
    } catch {
      if (stillCurrent()) setError('Chưa định vị được nguồn riêng tư. Tệp có thể đã thay đổi, không hỗ trợ phát hoặc chưa truy cập được Drive. Bạn vẫn có thể mở nguồn gốc.');
    } finally { if (stillCurrent()) setBusy(false); }
  };
  const loadOriginal = async () => {
    const controller = new AbortController(); inFlight.current?.abort(); inFlight.current = controller;
    const stillCurrent = () => !controller.signal.aborted && currentRevision.current === revision;
    setBusy(true); setError('');
    try {
      const value = part.asset_id ? (await request<{ url: string }>(`/assets/${encodeURIComponent(part.asset_id)}/open`, { signal: controller.signal })).url : part.source?.source_url;
      const url = value && safeOriginalUrl(value);
      if (!url) throw new Error('unsafe_source');
      if (stillCurrent()) setOriginal(url);
    } catch (error) {
      if (stillCurrent()) setError(error instanceof ApiError && [401, 403, 404].includes(error.status) ? 'Nguồn không còn tồn tại hoặc bạn chưa có quyền truy cập.' : 'Chưa mở được nguồn. Liên kết có thể hết hạn; hãy thử lại.');
    } finally { if (stillCurrent()) setBusy(false); }
  };
  return <div className="source-locator" data-state={result.state}>
    <div className="source-locator-line"><strong>{result.label}</strong><span>{stateText[result.state]}</span></div>
    <p>{result.reason}</p>
    <div className="source-locator-actions">
      {result.state === 'AVAILABLE' && <button type="button" onClick={() => setOpened(true)}>Đến vị trí nguồn</button>}
      {result.state === 'NOT_SUPPORTED' && (result.locator?.kind === 'time' || result.locator?.kind === 'page') && part.asset_id && part.source?.state === 'current'
        && <button type="button" disabled={busy} onClick={() => void loadViewer()}>{busy ? 'Đang kiểm tra nguồn…' : result.locator.kind === 'page' ? 'Mở và định vị PDF riêng tư' : 'Mở và định vị nguồn riêng tư'}</button>}
      {result.state !== 'MISSING_ASSET' && <button type="button" disabled={busy} onClick={() => void loadOriginal()}>{busy ? 'Đang tìm nguồn…' : 'Mở nguồn gốc'}</button>}
      {part.asset_id && onIllustration && <button type="button" onClick={() => onIllustration(part.asset_id!)}>Xem minh họa từ nguồn</button>}
      {original && <a href={original} target="_blank" rel="noopener noreferrer">Mở file/website gốc (không định vị)</a>}
    </div>
    {error && <p role="alert">{error}</p>}
    {opened && result.viewer && result.locator?.kind === 'time' && <SourceLocatorMedia key={revision} viewer={result.viewer} locator={result.locator} mime={part.source?.mime ?? ''} />}
    {opened && result.viewer && result.locator?.kind === 'page' && <div className="source-locator-viewer"><p>Yêu cầu mở trang {result.locator.page}; kiểm tra số trang trong trình xem PDF.</p><iframe title={`Nguồn PDF trang ${result.locator.page}`} src={`${result.viewer.url}#page=${result.locator.page}`} referrerPolicy="no-referrer" /></div>}
    <small>{part.processor}{part.processor_version ? ` · ${part.processor_version}` : ''}{part.source?.asset_version != null ? ` · Phiên bản file ${part.source.asset_version}` : ''}</small>
  </div>;
}
