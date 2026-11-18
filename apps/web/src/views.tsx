import { Button, Skeleton } from '@mantine/core';
import { useEffect, useState, type ReactNode } from 'react';
import { request, type Capture, type Item } from './api';

const vietnamTime = new Intl.DateTimeFormat('vi-VN', {
  timeZone: 'Asia/Ho_Chi_Minh',
  hour: '2-digit',
  minute: '2-digit',
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hourCycle: 'h23',
});

export function ServerTime({ value }: { value: string }) {
  return <time dateTime={value} title="Giờ Việt Nam (UTC+7)">{vietnamTime.format(new Date(value))}</time>;
}

export function PageTitle({ title, description }: { title: string; description?: string }) {
  return <div className="page-title">
    <h1>{title}</h1>
    {description && <p>{description}</p>}
  </div>;
}

export function ErrorNotice({ children, retry }: { children: ReactNode; retry?: () => void }) {
  return <div className="notice notice-error" role="alert">
    <span>{children}</span>
    {retry && <Button variant="default" size="compact-sm" onClick={retry}>Thử lại</Button>}
  </div>;
}

export function Loading({ label = 'Đang tải dữ liệu' }: { label?: string }) {
  return <div role="status" aria-label={label} className="loading">
    <Skeleton animate={false} h={14} w="68%" />
    <Skeleton animate={false} h={14} w="96%" />
    <Skeleton animate={false} h={14} w="80%" />
  </div>;
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty-state">{children}</div>;
}

type Resource<T> = { path: string; data?: T; error?: boolean };

export function useResource<T>(path: string) {
  const [resource, setResource] = useState<Resource<T>>({ path });
  const [revision, setRevision] = useState(0);
  const current = resource.path === path ? resource : { path };

  useEffect(() => {
    const controller = new AbortController();
    void request<T>(path, { signal: controller.signal }).then(
      (data) => {
        if (!controller.signal.aborted) setResource({ path, data });
      },
      () => {
        if (!controller.signal.aborted) setResource({ path, error: true });
      },
    );
    return () => controller.abort();
  }, [path, revision]);

  return {
    ...current,
    retry() {
      setResource({ path });
      setRevision((value) => value + 1);
    },
  };
}

export const itemHref = (id: string) => `#/muc/${encodeURIComponent(id)}`;
export const kindLabels: Record<Item['kind'], string> = { link: 'Liên kết', text: 'Ghi chú', file: 'Tệp' };

export function itemTitle(item: Item) {
  const label = item.title.trim() || (item.kind === 'link' ? item.original_url : item.note.trim().split('\n', 1)[0]);
  const characters = Array.from(label || kindLabels[item.kind]);
  return characters.length > 180 ? characters.slice(0, 179).join('') + '…' : characters.join('');
}

export function CaptureList({ rows, compact = false }: { rows: Capture[]; compact?: boolean }) {
  return <ol className={compact ? 'capture-list compact' : 'capture-list'}>
    {rows.map((entry) => <li key={entry.capture_id}>
      <a className="capture-entry" href={itemHref(entry.item_id)}>
        <span className="capture-main">
          <span className="capture-kind"><span className="entry-mark" aria-hidden="true" />{kindLabels[entry.raw_kind]}</span>
          <span className={compact ? 'capture-preview' : 'capture-original'}>{entry.original_url || entry.raw_text}</span>
          {entry.original_url && entry.raw_text && !compact && <span className="capture-original capture-annotation">{entry.raw_text}</span>}
        </span>
        <ServerTime value={entry.received_at} />
      </a>
    </li>)}
  </ol>;
}

export function PageControls({ offset, nextOffset, onChange }: {
  offset: number;
  nextOffset: number | null;
  onChange: (offset: number) => void;
}) {
  if (offset === 0 && nextOffset === null) return null;
  return <nav aria-label="Phân trang" className="paging">
    <Button variant="default" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - 50))}>Trang trước</Button>
    <Button variant="default" disabled={nextOffset === null} onClick={() => {
      if (nextOffset !== null) onChange(nextOffset);
    }}>Trang sau</Button>
  </nav>;
}
