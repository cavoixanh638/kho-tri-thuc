import { AssetPreview } from './AssetPreview';
import { Button, Textarea, TextInput } from '@mantine/core';
import { useRef, useState, type SubmitEvent } from 'react';
import { externalHttpUrl, request, type Capture, type Item, type Page } from './api';
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

function ItemContent({ initial, csrf }: { initial: Item; csrf: string }) {
  const [item, setItem] = useState(initial);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({ title: initial.title, description: initial.description, note: initial.note });
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);
  const [openingAsset, setOpeningAsset] = useState<string>();
  const [error, setError] = useState<string>();
  const [assetError, setAssetError] = useState<string>();
  const [confirmation, setConfirmation] = useState('');
  const sourceUrl = externalHttpUrl(item.original_url);

  async function update(patch: Partial<Pick<Item, 'title' | 'description' | 'note' | 'favorite' | 'deleted'>>) {
    if (inFlight.current) return;
    inFlight.current = true;
    setError(undefined);
    setConfirmation('');
    setBusy(true);
    try {
      const result = await request<Item>(`/items/${encodeURIComponent(item.item_id)}`, { method: 'PATCH', csrf, body: patch });
      setItem(result);
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
            <h2 id="item-content">Nội dung</h2>
            {!editing && <Button variant="default" onClick={() => {
              setDraft({ title: item.title, description: item.description, note: item.note });
              setEditing(true);
            }} disabled={busy || item.deleted}>Chỉnh sửa</Button>}
          </div>
          {editing ? <form className="form-stack" onSubmit={saveNotes}>
            <TextInput label="Tiêu đề" value={draft.title} maxLength={512} disabled={busy} onChange={(event) => setDraft({ ...draft, title: event.currentTarget.value })} />
            <Textarea label="Mô tả" value={draft.description} minRows={3} autosize disabled={busy} onChange={(event) => setDraft({ ...draft, description: event.currentTarget.value })} />
            <Textarea label="Ghi chú" value={draft.note} minRows={5} autosize disabled={busy} onChange={(event) => setDraft({ ...draft, note: event.currentTarget.value })} />
            <div className="form-actions">
              <Button type="submit" loading={busy}>Lưu thay đổi</Button>
              <Button variant="default" disabled={busy} onClick={() => setEditing(false)}>Hủy</Button>
            </div>
          </form> : <>
            {item.original_url && <p className="detail-source">{sourceUrl ? <a href={sourceUrl} target="_blank" rel="noopener noreferrer">{item.original_url}</a> : item.original_url}</p>}
            {item.description && <p className="prose-text">{item.description}</p>}
            {item.note && <div className="prose-text item-note">{item.note}</div>}
            {!item.original_url && !item.description && !item.note && <Empty>Chưa có nội dung hoặc ghi chú.</Empty>}
          </>}
          {item.assets.length > 0 && <div className="assets">
            <h3>Tệp đính kèm</h3>
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
          </div>}
        </section>
        <ItemHistory id={item.item_id} />
      </div>
      <div className="panel-stack">
        <section className="panel" aria-labelledby="item-status">
          <h2 id="item-status">Thông tin mục</h2>
          <dl className="key-value">
            <div><dt>Loại</dt><dd>{kindLabels[item.kind]}</dd></div>
            <div><dt>Nhận lần đầu</dt><dd><ServerTime value={item.saved_at} /></dd></div>
            <div><dt>Ngày nguồn đăng</dt><dd>{item.published_at ? <ServerTime value={item.published_at} /> : '—'}</dd></div>
            <div><dt>Thu thập nguồn</dt><dd>{stateText(item.source_fetch, fetchStates)}</dd></div>
            <div><dt>Lưu tệp</dt><dd>{stateText(item.asset_storage, storageStates)}</dd></div>
            <div><dt>Trích nội dung</dt><dd>{stateText(item.content_extract, extractStates)}</dd></div>
            <div><dt>Phân loại</dt><dd>{stateText(item.classification_status, organizationStates)}</dd></div>
          </dl>
          <div className="item-actions">
            {item.deleted ? <Button variant="default" disabled={busy} onClick={() => void update({ deleted: false })}>Khôi phục</Button>
              : <>
                <Button variant="default" disabled={busy} onClick={() => void update({ favorite: !item.favorite })}>{item.favorite ? 'Bỏ yêu thích' : 'Thêm yêu thích'}</Button>
                <Button variant="outline" color="red.8" disabled={busy || editing} onClick={() => void update({ deleted: true })}>Chuyển vào thùng rác</Button>
              </>}
          </div>
        </section>
        {confirmation && <div className="notice" role="status">{confirmation}</div>}
        {error && <ErrorNotice>{error}</ErrorNotice>}
      </div>
    </div>
  </>;
}

export function ItemScreen({ id, csrf }: { id: string; csrf: string }) {
  const item = useResource<Item>(`/items/${encodeURIComponent(id)}`);
  if (item.data) return <ItemContent initial={item.data} csrf={csrf} />;
  return <>
    <a className="back-link" href="#/thu-vien">‹ Thư viện</a>
    <PageTitle title="Chi tiết mục" />
    <section className="panel">
      {item.error ? <ErrorNotice retry={item.retry}>Chưa tải được mục này.</ErrorNotice> : <Loading />}
    </section>
  </>;
}
