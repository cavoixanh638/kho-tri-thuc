import { ExtractedContent } from './ExtractedContent';
import { AssetPreview } from './AssetPreview';
import { Button, Textarea, TextInput } from '@mantine/core';
import { useRef, useState, type SubmitEvent } from 'react';
import { externalHttpUrl, request, type Capture, type Item, type Page } from './api';
import { ItemOrganization, RelatedItems } from './ItemOrganization';
import { itemNeedsRefresh } from './itemProcessing';
import { KnowledgeExportPanel } from './KnowledgeExportPanel';
import { KnowledgeText } from './KnowledgeText';
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
  pending: 'Đang chờ', auto_assigned: 'Đã tự xếp nhóm', suggested: 'Có đề xuất',
  unclassified: 'Chưa phân loại', needs_review: 'Cần xem lại',
};

function stateText(value: string | undefined, states: Record<string, string>) {
  return (value && Object.hasOwn(states, value) && states[value]) || '—';
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
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({ title: item.title, description: item.description, note: item.note });
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);
  const [openingAsset, setOpeningAsset] = useState<string>();
  const [error, setError] = useState<string>();
  const [assetError, setAssetError] = useState<string>();
  const [confirmation, setConfirmation] = useState('');
  const sourceUrl = externalHttpUrl(item.original_url);
  const hasSourceContent = item.kind !== 'text' || item.assets.length > 0;
  const evidenceRevision = [item.updated_at, item.source_fetch, item.content_extract, item.classification_status].join(':');

  async function update(patch: Partial<Pick<Item, 'title' | 'description' | 'note' | 'favorite' | 'deleted'>>) {
    if (inFlight.current) return;
    inFlight.current = true;
    setError(undefined);
    setConfirmation('');
    setBusy(true);
    try {
      const result = await request<Item>(`/items/${encodeURIComponent(item.item_id)}`, { method: 'PATCH', csrf, body: patch });
      onUpdated(result);
      if (patch.title !== undefined || patch.note !== undefined || patch.description !== undefined) setEditing(false);
      setConfirmation(patch.deleted === true ? 'Đã chuyển vào thùng rác.'
        : patch.deleted === false ? 'Đã khôi phục mục.'
          : patch.favorite === true ? 'Đã thêm vào yêu thích.'
            : patch.favorite === false ? 'Đã bỏ yêu thích.' : 'Đã lưu chỉnh sửa.');
    } catch {
      setError('Chưa lưu được thay đổi. Hãy thử lại.');
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
    void update(draft);
  }

  return <>
    <a className="back-link" href="#/thu-vien">‹ Thư viện</a>
    <PageTitle title={itemTitle(item)} />
    <div className="detail-view">
      <div className="panel-stack">
        <section className="panel" aria-labelledby="item-content">
          <div className="panel-heading">
            <h2 id="item-content">Tri thức</h2>
            {!editing && <Button variant="default" onClick={() => {
              setDraft({ title: item.title, description: item.description, note: item.note });
              setEditing(true);
            }} disabled={busy || item.deleted}>Chỉnh sửa</Button>}
          </div>
          {editing ? <form className="form-stack" onSubmit={saveNotes}>
            <TextInput label="Tiêu đề" value={draft.title} maxLength={512} disabled={busy} onChange={(event) => setDraft({ ...draft, title: event.currentTarget.value })} />
            <Textarea label="Mô tả" value={draft.description} minRows={3} autosize disabled={busy} onChange={(event) => setDraft({ ...draft, description: event.currentTarget.value })} />
            <Textarea label="Nội dung tri thức (Markdown)" description="Văn bản chính để đọc, tìm kiếm và tổ chức. Nguồn và media được giữ kèm theo." value={draft.note} minRows={10} autosize disabled={busy} onChange={(event) => setDraft({ ...draft, note: event.currentTarget.value })} />
            <div className="form-actions">
              <Button type="submit" loading={busy}>Lưu thay đổi</Button>
              <Button variant="default" disabled={busy} onClick={() => setEditing(false)}>Hủy</Button>
            </div>
          </form> : <>
            {item.note ? <>
              <KnowledgeText text={item.note} title={itemTitle(item)} />
              <details className="raw-knowledge"><summary>Xem Markdown gốc</summary><pre>{item.note}</pre></details>
            </> : <Empty>Chưa có bài tri thức được biên soạn. Bạn có thể chỉnh sửa để thêm nội dung; văn bản trích từ nguồn nằm bên dưới.</Empty>}
            {(item.original_url || item.description) && <details className="source-description"><summary>Nguồn và mô tả</summary>
              {item.original_url && <p className="detail-source">{sourceUrl ? <a href={sourceUrl} target="_blank" rel="noopener noreferrer">{item.original_url}</a> : item.original_url}</p>}
              {item.description && <p className="prose-text">{item.description}</p>}
            </details>}
          </>}
        </section>
        {!item.deleted && hasSourceContent && <ExtractedContent id={item.item_id} refreshKey={evidenceRevision} />}
        {item.assets.length > 0 && <section className="panel assets" aria-labelledby="item-media">
            <h2 id="item-media">Media và tài liệu nguồn</h2>
            <AssetPreview assets={item.assets} />
            <ul>
              {item.assets.map((asset) => <li key={asset.asset_id}>
                <span>
                  <span className="asset-name">{asset.filename}</span>
                  <span className="list-meta">{stateText(asset.status, storageStates)}</span>
                </span>
                {asset.status === 'verified' && <Button variant="default" size="compact-sm" loading={openingAsset === asset.asset_id} disabled={!!openingAsset}
                  onClick={() => void openAsset(asset.asset_id)}>Mở tệp</Button>}
              </li>)}
            </ul>
            {assetError && <ErrorNotice>{assetError}</ErrorNotice>}
          </section>}
        <ItemHistory id={item.item_id} />
        <RelatedItems id={item.item_id} refreshKey={evidenceRevision} />
      </div>
      <div className="panel-stack">
        <section className="panel" aria-labelledby="item-status">
          <h2 id="item-status">Thông tin mục</h2>
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
            {!item.deleted && (item.source_fetch === 'failed' || item.source_fetch === 'partial' || item.asset_storage === 'failed') && <Button variant="default" disabled={busy} onClick={() => void retryProcessing()}>Thử xử lý lại</Button>}
            {item.deleted ? <Button variant="default" disabled={busy} onClick={() => void update({ deleted: false })}>Khôi phục</Button>
              : <>
                <Button variant="default" disabled={busy} onClick={() => void update({ favorite: !item.favorite })}>{item.favorite ? 'Bỏ yêu thích' : 'Thêm yêu thích'}</Button>
                <Button variant="outline" color="red.8" disabled={busy || editing} onClick={() => void update({ deleted: true })}>Chuyển vào thùng rác</Button>
              </>}
          </div>
        </section>
        <ItemOrganization id={item.item_id} csrf={csrf} deleted={item.deleted} refreshKey={evidenceRevision} />
        <KnowledgeExportPanel id={item.item_id} csrf={csrf} deleted={item.deleted} refreshKey={evidenceRevision} />
        {confirmation && <div className="notice" role="status">{confirmation}</div>}
        {error && <ErrorNotice>{error}</ErrorNotice>}
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
