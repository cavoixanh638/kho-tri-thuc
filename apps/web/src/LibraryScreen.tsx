import { SegmentedControl } from '@mantine/core';
import { useState } from 'react';
import type { Item, Page } from './api';
import { Empty, ErrorNotice, itemHref, itemTitle, kindLabels, Loading, PageControls, PageTitle, ServerTime, useResource } from './views';

type Filter = 'all' | 'favorite' | 'deleted';

export function LibraryScreen() {
  const [filter, setFilter] = useState<Filter>('all');
  const [offset, setOffset] = useState(0);
  const query = new URLSearchParams({ limit: '50', offset: String(offset), deleted: String(filter === 'deleted') });
  if (filter === 'favorite') query.set('favorite', 'true');
  const library = useResource<Page<Item>>(`/items?${query}`);

  return <>
    <PageTitle title="Thư viện" description="Mỗi mục có một hồ sơ và có thể xuất hiện trong nhiều lượt gửi." />
    <section className="panel" aria-label="Danh sách mục">
      <div className="filters">
        <SegmentedControl value={filter} aria-label="Lọc thư viện" onChange={(value) => {
          setOffset(0);
          setFilter(value as Filter);
        }} data={[{ label: 'Tất cả', value: 'all' }, { label: 'Yêu thích', value: 'favorite' }, { label: 'Thùng rác', value: 'deleted' }]} />
      </div>
      {library.error ? <ErrorNotice retry={library.retry}>Chưa tải được thư viện.</ErrorNotice>
        : !library.data ? <Loading />
          : library.data.results.length ? <ul className="library-list">
            {library.data.results.map((item) => <li key={item.item_id}>
              <a href={itemHref(item.item_id)} className="library-entry">
                <span className="library-entry-text">
                  <span className="capture-kind">{kindLabels[item.kind]}</span>
                  <span className="library-entry-title">{itemTitle(item)}</span>
                </span>
                <span className="library-entry-time"><span className="list-meta">Nhận lần đầu</span><ServerTime value={item.saved_at} /></span>
              </a>
            </li>)}
          </ul>
            : <Empty>{filter === 'favorite' ? 'Chưa có mục yêu thích.' : filter === 'deleted' ? 'Thùng rác trống.' : <span>Chưa có mục nào. <a href="#/gui">Gửi vào kho</a></span>}</Empty>}
      {library.data && <PageControls offset={offset} nextOffset={library.data.next_offset} onChange={setOffset} />}
    </section>
  </>;
}
