import { Button, TextInput } from '@mantine/core';
import { useState, type SubmitEvent } from 'react';
import type { Capture, Page } from './api';
import { CaptureList, Empty, ErrorNotice, Loading, PageControls, PageTitle, useResource } from './views';

function beforeDay(value: string) {
  const day = new Date(`${value}T00:00:00+07:00`);
  day.setTime(day.valueOf() + 86_400_000);
  return day.toISOString();
}

export function HistoryScreen() {
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [range, setRange] = useState({ from: '', to: '' });
  const [offset, setOffset] = useState(0);
  const search = new URLSearchParams({ limit: '50', offset: String(offset) });
  if (range.from) search.set('received_from', `${range.from}T00:00:00+07:00`);
  if (range.to) search.set('received_before', beforeDay(range.to));
  const history = useResource<Page<Capture>>(`/captures?${search}`);

  function filter(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setOffset(0);
    setRange({ from, to });
  }

  return <>
    <PageTitle title="Lịch sử tiếp nhận" description="Mỗi lượt gửi có một dòng. Thời gian hiển thị theo giờ Việt Nam." />
    <section className="panel" aria-label="Lượt tiếp nhận">
      <form className="filters" onSubmit={filter}>
        <TextInput type="date" label="Ngày gửi từ" value={from} max={to || '9999-12-30'} onChange={(e) => setFrom(e.currentTarget.value)} />
        <TextInput type="date" label="Đến hết ngày" value={to} min={from || undefined} max="9999-12-30" onChange={(e) => setTo(e.currentTarget.value)} />
        <Button type="submit" variant="default">Lọc</Button>
        {(from || to || range.from || range.to) && <Button variant="subtle" onClick={() => {
          setFrom('');
          setTo('');
          setOffset(0);
          setRange({ from: '', to: '' });
        }}>Xóa bộ lọc</Button>}
      </form>
      {history.error ? <ErrorNotice retry={history.retry}>Chưa tải được lịch sử tiếp nhận.</ErrorNotice>
        : !history.data ? <Loading />
          : history.data.results.length ? <CaptureList rows={history.data.results} />
            : <Empty>{range.from || range.to ? 'Không có lượt gửi trong khoảng ngày này.' : 'Chưa có lượt gửi. '}{
              !range.from && !range.to && <a href="#/gui">Gửi vào kho</a>
            }</Empty>}
      {history.data && <PageControls offset={offset} nextOffset={history.data.next_offset} onChange={setOffset} />}
    </section>
  </>;
}
