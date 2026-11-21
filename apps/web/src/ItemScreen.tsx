import { ExtractedContent } from './ExtractedContent';
import { AssetPreview } from './AssetPreview';
import { Button, Textarea, TextInput } from '@mantine/core';
import { Component, useEffect, useRef, useState, type ReactNode, type SubmitEvent } from 'react';
import { ApiError, externalHttpUrl, request, type Capture, type Item, type Page } from './api';
import { ItemOrganization, RelatedItems } from './ItemOrganization';
import { itemNeedsRefresh } from './itemProcessing';
import { KnowledgeExportPanel } from './KnowledgeExportPanel';
import { KnowledgeText } from './KnowledgeText';
import { KnowledgeReading } from './KnowledgeReading';
import { SourceCitationBridge } from './SourceCitationBridge';
import { OrganizationReview } from './OrganizationReview';
import { SourceLinks } from './SourceLinks';
import { MarkdownEditor } from './MarkdownEditor';
import { useMarkdownDraft } from './MarkdownEditorDraft';
import { NoteTemplatePicker } from './NoteTemplatePicker';
import { acceptNoteTemplate } from './NoteTemplateConfig';
import { ItemSuggestionPanel } from './ItemSuggestionPanel';
import { ResearchClipper, ClipAnnotations } from './ResearchClipper';
import { PropertyChips } from './PropertyChips';
import { ItemStructurePanel } from './ItemStructurePanel';
import { CaptureList, Empty, ErrorNotice, itemTitle, kindLabels, Loading, PageControls, PageTitle, ServerTime, useResource } from './views';

const fetchStates: Record<string, string> = {
  not_applicable: 'Không áp dụng', pending: 'Đang chờ', partial: 'Đã lấy một phần', done: 'Đã thu thập', failed: 'Không thu thập được',
};
const storageStates: Record<string, string> = {
  not_applicable: 'Không áp dụng', pending: 'Đang chờ', verified: 'Đã xác minh trên Drive',
  failed: 'Lưu thất bại', missing: 'Không tìm thấy trên Drive', inaccessible: 'Chưa truy cập được',
};
const extractStates: Record<string, string> = {
  not_available: 'Chưa có nội dung', pending: 'Đang chờ', partial: 'Đã trích một phần',
  done: 'Đã trích xuất', failed: 'Không trích xuất được',
};
const organizationStates: Record<string, string> = {
  user_assigned: 'Đã xếp nhóm',
  pending: 'Đang chờ', auto_assigned: 'Đã tự xếp nhóm', suggested: 'Có đề xuất',
  unclassified: 'Chưa phân loại', needs_review: 'Cần xem lại',
};

function stateText(value: string | undefined, states: Record<string, string>) {
  return (value && Object.hasOwn(states, value) && states[value]) || '—';
}

// Structure is an optional module during rolling upgrades. A missing/malformed
// /structure payload must never unmount the source note, editor or capture history.
// Keep the fault boundary at this host; ItemStructurePanel is owned elsewhere.
class OptionalStructureBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) return <section className="panel" aria-label="Cấu trúc bài">
      <h2>Cấu trúc bài</h2>
      <ErrorNotice retry={() => this.setState({ failed: false })}>
        Chưa hiển thị được cấu trúc bài. Kiểm tra phiên bản máy chủ hoặc thử lại; nội dung ghi chú vẫn được giữ.
      </ErrorNotice>
    </section>;
    return this.props.children;
  }
}

function ItemHistory({ id }: { id: string }) {
  const [offset, setOffset] = useState(0);
  const history = useResource<Page<Capture>>(`/items/${encodeURIComponent(id)}/captures?limit=50&offset=${offset}`);
  return <section className="panel" aria-labelledby="item-history">
    <h2 id="item-history">Các lượt tiếp nhận</h2>
    {history.error ? <ErrorNotice retry={history.retry}>Chưa tải được các lượt tiếp nhận.</ErrorNotice>
      : !history.data ? <Loading />
        : history.data.results.length ? <CaptureList rows={history.data.results} />
          : <Empty>Chưa có lượt tiếp nhận.</Empty>}
    {history.data && <PageControls offset={offset} nextOffset={history.data.next_offset} onChange={setOffset} />}
  </section>;
}

function ItemContent({ item, csrf, onUpdated, onRefresh, refreshError, pollingPaused }: {
  item: Item; csrf: string; onUpdated: (item: Item) => void; onRefresh: () => void;
  refreshError?: boolean; pollingPaused?: boolean;
}) {
  const { draft, setDraft, base, editing, dirty, recovered, storageError, start, finish } = useMarkdownDraft(item);
  const composing = useRef(false);
  const draftRef = useRef(draft);
  draftRef.current = draft;
  const [discarding, setDiscarding] = useState(false);
  const [busy, setBusy] = useState(false);
  const [reviewBusy, setReviewBusy] = useState(false);
  const [clipRevision, setClipRevision] = useState(0);
  const inFlight = useRef(false);
  const [openingAsset, setOpeningAsset] = useState<string>();
  const [error, setError] = useState<string>();
  const [assetError, setAssetError] = useState<string>();
  const [confirmation, setConfirmation] = useState('');
  const mediaDetails = useRef<HTMLDetailsElement>(null);
  const sourceUrl = externalHttpUrl(item.original_url);
  const hasSourceContent = item.kind !== 'text' || item.assets.length > 0 || Boolean(item.original_url);
  const evidenceRevision = [item.updated_at, item.source_fetch, item.content_extract, item.classification_status].join(':');
  useEffect(() => {
    const command = (event: Event) => {
      const detail = (event as CustomEvent<{ action?: string; itemId?: string }>).detail;
      if (detail?.action !== 'attach' || detail.itemId !== item.item_id) return;
      const panel = document.getElementById('item-clipper');
      panel?.scrollIntoView?.({ block: 'start' });
      panel?.querySelector<HTMLInputElement>('input')?.focus({ preventScroll: true });
    };
    window.addEventListener('knowledge-command', command);
    return () => window.removeEventListener('knowledge-command', command);
  }, [item.item_id]);

  async function update(patch: Partial<Pick<Item, 'title' | 'description' | 'note' | 'favorite' | 'deleted'>>) {
    if (inFlight.current || reviewBusy) return;
    inFlight.current = true;
    setError(undefined);
    setConfirmation('');
    setBusy(true);
    try {
      const textFields = (['title', 'description', 'note'] as const).filter((field) => patch[field] !== undefined);
      let body: object = patch;
      if (textFields.length) {
        const latest = await request<Item>(`/items/${encodeURIComponent(item.item_id)}`);
        if (latest.deleted || textFields.some((field) => latest[field] !== base[field])) {
          setError('Nội dung đã thay đổi ở phiên khác. Bản nháp vẫn được giữ; sao chép phần cần giữ rồi tải lại để đối chiếu.');
          return;
        }
        if (Number.isSafeInteger(latest.user_edit_version) && latest.user_edit_version! >= 0) {
          body = { ...patch, expected_edit_version: latest.user_edit_version };
        }
      }
      const result = await request<Item>(`/items/${encodeURIComponent(item.item_id)}`, { method: 'PATCH', csrf, body });
      onUpdated(result);
      if (textFields.length) finish();
      setConfirmation(patch.deleted === true ? 'Đã chuyển vào thùng rác.'
        : patch.deleted === false ? 'Đã khôi phục mục.'
          : patch.favorite === true ? 'Đã thêm vào yêu thích.'
            : patch.favorite === false ? 'Đã bỏ yêu thích.' : 'Đã lưu chỉnh sửa.');
    } catch (error) {
      setError(error instanceof ApiError && error.status === 409
        ? 'Nội dung đã thay đổi ở phiên khác. Bản nháp vẫn được giữ; sao chép phần cần giữ rồi tải lại để đối chiếu.'
        : 'Chưa lưu được thay đổi. Hãy thử lại.');
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

  async function openAsset(id: string) {
    setAssetError(undefined);
    setOpeningAsset(id);
    try {
      const result = await request<{ url: string }>(`/assets/${encodeURIComponent(id)}/open`);
      const url = externalHttpUrl(result.url);
      if (!url) throw new Error('Invalid asset URL');
      window.location.assign(url);
    } catch {
      setAssetError('Chưa mở được tệp đã lưu. Kiểm tra lại kết nối Google Drive.');
    } finally {
      setOpeningAsset(undefined);
    }
  }

  async function retryProcessing() {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError(undefined);
    try {
      const result = await request<{ queued: number }>(`/items/${encodeURIComponent(item.item_id)}/retry`, { method: 'POST', csrf });
      setConfirmation(result.queued ? 'Đã đưa vào hàng đợi để thử lại.' : 'Mục đang xử lý hoặc chưa có tác vụ cần thử lại.');
      onRefresh();
    } catch {
      setError('Chưa yêu cầu xử lý lại được. Hãy thử lại.');
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

  function saveNotes(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    saveDraft();
  }

  function saveDraft() {
    if (composing.current || !dirty) return;
    const patch = Object.fromEntries((['title', 'description', 'note'] as const)
      .filter((field) => draft[field] !== base[field]).map((field) => [field, draft[field]]));
    void update(patch);
  }

  function showIllustration(assetId: string) {
    if (!item.assets.some((asset) => asset.asset_id === assetId)) return;
    if (mediaDetails.current) mediaDetails.current.open = true;
    const target = document.getElementById(`item-asset-${assetId}`);
    target?.scrollIntoView?.({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'nearest' });
    target?.focus({ preventScroll: true });
  }

  return <>
    <a className="back-link" href="#/thu-vien">‹ Thư viện</a>
    <PageTitle title={itemTitle(item)} />
    <div className="detail-view markdown-item-detail">
      <div className="panel-stack">
        <section className="panel" aria-labelledby="item-content">
          <div className="panel-heading">
            <h2 id="item-content">Tri thức</h2>
            {!editing && <Button variant="default" onClick={start} disabled={busy || reviewBusy || item.deleted}>Chỉnh sửa</Button>}
          </div>
          {editing ? <form className="form-stack" onSubmit={saveNotes}
            onCompositionStartCapture={() => { composing.current = true; }} onCompositionEndCapture={() => { composing.current = false; }}>
            {recovered && <p role="status">Đã khôi phục bản nháp trong tab này. Chưa lưu lên máy chủ.</p>}
            {storageError && <p role="alert">Không lưu được bản nháp trong tab. Giữ trang mở và sao chép nội dung trước khi rời trang.</p>}
            <TextInput label="Tiêu đề" value={draft.title} maxLength={512} disabled={busy} onChange={(event) => setDraft({ ...draft, title: event.currentTarget.value })} />
            <Textarea label="Mô tả" value={draft.description} minRows={3} autosize disabled={busy} onChange={(event) => setDraft({ ...draft, description: event.currentTarget.value })} />
            <MarkdownEditor value={draft.note} title={draft.title} disabled={busy} onChange={(note) => setDraft((current) => ({ ...current, note }))}
              onSave={saveDraft} onCompositionChange={(value) => { composing.current = value; }} />
            <details className="raw-knowledge"><summary>Thêm mẫu ghi chú</summary>
              <NoteTemplatePicker note={draft.note} disabled={busy} onApply={(proposal) => {
                const note = acceptNoteTemplate(draftRef.current.note, proposal);
                if (note === undefined || composing.current || inFlight.current) return false;
                const next = { ...draftRef.current, note };
                draftRef.current = next;
                setDraft(next);
                return true;
              }} />
            </details>
            <p role="status">{dirty ? 'Bản nháp chưa lưu lên máy chủ.' : 'Chưa có thay đổi.'}</p>
            <div className="form-actions">
              <Button type="submit" loading={busy} disabled={!dirty}>Lưu thay đổi</Button>
              <Button type="button" variant="default" disabled={busy} onClick={() => dirty ? setDiscarding(true) : finish()}>Hủy</Button>
            </div>
            {error && <ErrorNotice>{error}</ErrorNotice>}
            {discarding && <div role="group" aria-label="Xác nhận bỏ bản nháp">
              <p>Bỏ các thay đổi chưa lưu?</p>
              <Button type="button" variant="default" onClick={() => setDiscarding(false)}>Tiếp tục soạn</Button>
              <Button type="button" color="red.8" onClick={() => { finish(); setDiscarding(false); }}>Bỏ bản nháp</Button>
            </div>}
          </form> : <>
            {item.note ? <>
              <KnowledgeText text={item.note} title={itemTitle(item)} />
              {!item.deleted && <SourceCitationBridge id={item.item_id} refreshKey={evidenceRevision} onIllustration={showIllustration} />}
              <details className="raw-knowledge"><summary>Xem Markdown gốc</summary><pre>{item.note}</pre></details>
            </> : !item.deleted ? <KnowledgeReading id={item.item_id} refreshKey={evidenceRevision} onIllustration={showIllustration} /> : <Empty>Bài đang ở thùng rác.</Empty>}
            {(item.original_url || item.description) && <details className="source-description"><summary>Nguồn và mô tả</summary>
              {item.original_url && <p className="detail-source">{sourceUrl ? <a href={sourceUrl} target="_blank" rel="noopener noreferrer">{item.original_url}</a> : item.original_url}</p>}
              {item.description && <p className="prose-text">{item.description}</p>}
            </details>}
          </>}
        </section>
        <ItemSuggestionPanel key={item.item_id} item={item} csrf={csrf} editing={editing || busy} draftDirty={dirty}
          onUpdated={onUpdated} onBusyChange={setReviewBusy} />
        {!item.deleted && <SourceLinks id={item.item_id} csrf={csrf} deleted={item.deleted} onSaved={() => { setConfirmation('Đã gắn nguồn, đang trích văn bản vào bài.'); onRefresh(); }} />}
        {!item.deleted && <div id="item-clipper"><ResearchClipper id={item.item_id} csrf={csrf} onSaved={() => { setClipRevision((value) => value + 1); onRefresh(); }} /></div>}
        {!item.deleted && <ClipAnnotations item={item} csrf={csrf} disabled={editing || busy || reviewBusy} onUpdated={onUpdated}
          refreshKey={evidenceRevision + ':' + clipRevision} onIllustration={showIllustration} />}
        {!item.deleted && hasSourceContent && <details className="source-evidence"><summary>Các phần trích và bằng chứng nguồn</summary><ExtractedContent id={item.item_id} refreshKey={evidenceRevision} /></details>}
        {item.assets.length > 0 && <details ref={mediaDetails} className="panel assets" id="item-media">
            <summary>Video, media và tài liệu minh họa ({item.assets.length})</summary>
            <AssetPreview assets={item.assets} />
            <ul>
              {item.assets.map((asset) => <li key={asset.asset_id} id={`item-asset-${asset.asset_id}`} tabIndex={-1}>
                <span>
                  <span className="asset-name">{asset.filename}</span>
                  <span className="list-meta">{stateText(asset.status, storageStates)}</span>
                </span>
                {asset.status === 'verified' && <Button variant="default" size="compact-sm" loading={openingAsset === asset.asset_id} disabled={!!openingAsset}
                  onClick={() => void openAsset(asset.asset_id)}>Mở tệp</Button>}
              </li>)}
            </ul>
            {assetError && <ErrorNotice>{assetError}</ErrorNotice>}
          </details>}
        <ItemHistory id={item.item_id} />
        <RelatedItems id={item.item_id} refreshKey={evidenceRevision} onOpenAsset={showIllustration} />
      </div>
      <div className="panel-stack">
        <section className="panel" aria-labelledby="item-status">
          <h2 id="item-status">Thông tin mục</h2>
          <PropertyChips item={item} />
          <dl className="key-value">
            <div><dt>Loại</dt><dd>{kindLabels[item.kind]}</dd></div>
            <div><dt>Nhận lần đầu</dt><dd><ServerTime value={item.saved_at} /></dd></div>
            <div><dt>Ngày nguồn đăng</dt><dd>{item.published_at ? <ServerTime value={item.published_at} /> : '—'}</dd></div>
            {hasSourceContent && <>
              <div><dt>Thu thập nguồn</dt><dd>{stateText(item.source_fetch, fetchStates)}</dd></div>
              <div><dt>Lưu tệp</dt><dd>{stateText(item.asset_storage, storageStates)}</dd></div>
              <div><dt>Trích nội dung</dt><dd>{stateText(item.content_extract, extractStates)}</dd></div>
            </>}
            <div><dt>Phân loại</dt><dd>{stateText(item.classification_status, organizationStates)}</dd></div>
          </dl>
          {refreshError ? <ErrorNotice retry={onRefresh}>Chưa cập nhật được trạng thái mới. Dữ liệu đang hiển thị là lần kiểm tra trước.</ErrorNotice>
            : pollingPaused && <div className="notice" role="status">
              <span>Tạm dừng cập nhật tự động.</span>
              <Button variant="default" size="compact-sm" onClick={onRefresh}>Cập nhật trạng thái</Button>
            </div>}
          <div className="item-actions">
            {!item.deleted && (item.source_fetch === 'failed' || item.source_fetch === 'partial' || item.asset_storage === 'failed' || item.content_extract === 'failed' || (hasSourceContent && item.content_extract === 'not_available')) && <Button variant="default" disabled={busy} onClick={() => void retryProcessing()}>Thử xử lý lại</Button>}
            {item.deleted ? <Button variant="default" disabled={busy} onClick={() => void update({ deleted: false })}>Khôi phục</Button>
              : <>
                <Button variant="default" disabled={busy || reviewBusy} onClick={() => void update({ favorite: !item.favorite })}>{item.favorite ? 'Bỏ yêu thích' : 'Thêm yêu thích'}</Button>
                <Button variant="outline" color="red.8" disabled={busy || reviewBusy || editing} onClick={() => void update({ deleted: true })}>Chuyển vào thùng rác</Button>
              </>}
          </div>
        </section>
        <ItemOrganization id={item.item_id} csrf={csrf} deleted={item.deleted} refreshKey={evidenceRevision} onSaved={onRefresh} />
        {!item.deleted && <OrganizationReview id={item.item_id} csrf={csrf} refreshKey={evidenceRevision} onSaved={onRefresh} />}
        {!item.deleted && <OptionalStructureBoundary key={`${item.item_id}:${evidenceRevision}`}>
          <ItemStructurePanel id={item.item_id} csrf={csrf} refreshKey={evidenceRevision} onChanged={onRefresh} />
        </OptionalStructureBoundary>}
        <KnowledgeExportPanel id={item.item_id} csrf={csrf} deleted={item.deleted} refreshKey={evidenceRevision} />
        {confirmation && <div className="notice" role="status">{confirmation}</div>}
        {error && !editing && <ErrorNotice>{error}</ErrorNotice>}
      </div>
    </div>
  </>;
}

export function ItemScreen({ id, csrf }: { id: string; csrf: string }) {
  const item = useResource<Item>(`/items/${encodeURIComponent(id)}`, { pollWhile: itemNeedsRefresh });
  if (item.data) return <ItemContent key={item.data.item_id} item={item.data} csrf={csrf}
    onUpdated={item.replace} onRefresh={item.retry} refreshError={item.refreshError} pollingPaused={item.pollingPaused} />;
  return <>
    <a className="back-link" href="#/thu-vien">‹ Thư viện</a>
    <PageTitle title="Chi tiết mục" />
    <section className="panel">
      {item.error ? <ErrorNotice retry={item.retry}>Chưa tải được mục này.</ErrorNotice> : <Loading />}
    </section>
  </>;
}
