import { Button, NativeSelect, TextInput } from '@mantine/core';
import { useState, type SubmitEvent } from 'react';
import { groupKinds, type GroupFilter, type Groups } from './groups';
import { Empty, ErrorNotice, itemHref, Loading, PageTitle, useResource } from './views';

type Criteria = { q: string } & Record<GroupFilter, string>;
type Cursor = { score: number | string; item_id: string };
type Evidence = { source: string; snippet: string; locator?: unknown; provenance?: unknown };
type Verification = { answer: 'yes' | 'no'; quotes: string[] };
type Result = {
  item_id: string;
  title: string;
  score: number | string;
  evidence: Evidence[];
  verification?: Verification;
};
type SearchPage = {
  results: Result[];
  next_cursor: Cursor | null;
  match_kind?: 'standard' | 'partial';
  can_expand?: boolean;
  quote_check?: { status: 'checked' | 'unavailable' };
};

const sourceLabels: Record<string, string> = {
  item: 'Mục thư viện',
  title: 'Tiêu đề',
  note: 'Ghi chú',
  description: 'Mô tả',
  derived: 'Nội dung đã trích',
  derived_content: 'Nội dung đã trích',
  capture: 'Lượt tiếp nhận',
  capture_annotation: 'Ghi chú kèm lượt gửi',
};

function criteriaFor(path: string): Criteria {
  const params = new URLSearchParams(path.split('?', 2)[1]);
  return {
    q: params.get('q') ?? '',
    topic_id: params.get('topic_id') ?? '',
    project_id: params.get('project_id') ?? '',
    tag_id: params.get('tag_id') ?? '',
  };
}

function hasCriteria(criteria: Criteria) {
  return Boolean(criteria.q.trim() || groupKinds.some((group) => criteria[group.filter]));
}

function parameters(criteria: Criteria, expanded = false) {
  const params = new URLSearchParams({ q: criteria.q.trim() });
  for (const group of groupKinds) {
    if (criteria[group.filter]) params.set(group.filter, criteria[group.filter]);
  }
  if (expanded) params.set('expand', 'true');
  return params;
}

function formatLocator(value: unknown) {
  if (typeof value === 'string') return value;
  if (value && typeof value === 'object') {
    if ('page' in value && typeof value.page === 'number') return `Trang ${value.page}`;
    if ('sheet' in value && typeof value.sheet === 'string') return `Trang tính ${value.sheet}`;
  }
}

function ResultEvidence({ result, checked }: { result: Result; checked: boolean }) {
  const verification = checked && result.verification;
  if (verification) {
    return <div className="search-evidence search-verification">
      <p>Câu trả lời theo nguồn <strong>{verification.answer === 'yes' ? 'Có' : 'Không'}</strong></p>
      <span className="list-meta">Trích nguyên văn từ mục này</span>
      {verification.quotes.map((quote, index) => <blockquote className="search-quote" cite={itemHref(result.item_id)} key={index}>
        <p>{quote}</p>
      </blockquote>)}
    </div>;
  }
  return result.evidence.map((evidence, index) => {
    const label = Object.hasOwn(sourceLabels, evidence.source) ? sourceLabels[evidence.source] : 'Nội dung đã lưu';
    const locator = formatLocator(evidence.locator);
    return <div className="search-evidence" key={index}>
      <span className="list-meta">{label}{locator && ` · ${locator}`}</span>
      {evidence.snippet && <p>{evidence.snippet}</p>}
    </div>;
  });
}

function SearchResults({ criteria, expanded }: { criteria: Criteria; expanded: boolean }) {
  const [cursors, setCursors] = useState<(Cursor | null)[]>([null]);
  const cursor = cursors.at(-1);
  const params = parameters(criteria, expanded);
  params.set('limit', '25');
  if (cursor) {
    params.set('cursor_score', String(cursor.score));
    params.set('cursor_item_id', cursor.item_id);
  }
  const results = useResource<SearchPage>(`/search?${params}`);
  const quoteStatus = expanded ? results.data?.quote_check?.status : undefined;
  const checked = quoteStatus === 'checked';
  const unavailable = quoteStatus === 'unavailable';
  const partial = !quoteStatus && results.data?.match_kind === 'partial' && results.data.results.length > 0;

  return <section className="panel search-results" aria-labelledby="search-results-title">
    <h2 id="search-results-title">{criteria.q.trim() ? 'Kết quả tìm kiếm' : 'Mục trong nhóm'}</h2>
    {partial && <p id="search-partial-match" role="status">Ghi chú khớp một phần từ khóa</p>}
    {unavailable && <p id="search-quote-unavailable" role="status">Chưa kiểm tra được trích dẫn. Các gợi ý trên trang này chưa được đối chiếu với câu hỏi.</p>}
    {results.error ? <ErrorNotice retry={results.retry}>Chưa tải được kết quả tìm kiếm.</ErrorNotice>
      : !results.data ? <Loading label={expanded ? 'Đang tải kết quả tìm gần đúng' : undefined} />
        : results.data.results.length ? <ol className="search-list"
          aria-describedby={unavailable ? 'search-quote-unavailable' : partial ? 'search-partial-match' : undefined}>
          {results.data.results.map((result) => <li key={result.item_id} className="search-result">
            <h3><a href={itemHref(result.item_id)}>{result.title || 'Mở mục trong thư viện'}</a></h3>
            <ResultEvidence result={result} checked={checked} />
          </li>)}
        </ol> : checked
          ? <div id="search-insufficient-evidence" role="status"><Empty>Chưa tìm thấy trích dẫn đủ để trả lời trên trang này.</Empty></div>
          : <Empty>Không tìm thấy mục phù hợp.</Empty>}
    {expanded
      ? <Button component="a" variant="subtle" href={`#/tim-kiem?${parameters(criteria)}`}>Về kết quả ban đầu</Button>
      : results.data?.can_expand && <Button component="a" variant="default"
        href={`#/tim-kiem?${parameters(criteria, true)}`}>Tìm gần đúng</Button>}
    {results.data && (cursors.length > 1 || results.data.next_cursor !== null) && <nav aria-label="Phân trang" className="paging">
      <Button variant="default" disabled={cursors.length === 1} onClick={() => setCursors((current) => current.slice(0, -1))}>Trang trước</Button>
      <Button variant="default" disabled={results.data.next_cursor === null} onClick={() => {
        const next = results.data?.next_cursor;
        if (next) setCursors((current) => [...current, next]);
      }}>Trang sau</Button>
    </nav>}
  </section>;
}

export function SearchScreen({ path }: { path: string }) {
  const criteria = criteriaFor(path);
  const expanded = new URLSearchParams(path.split('?', 2)[1]).get('expand') === 'true';
  const [draft, setDraft] = useState(criteria);
  const groups = useResource<Groups>('/groups');

  function search(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (hasCriteria(draft)) window.location.hash = `#/tim-kiem?${parameters(draft)}`;
  }

  return <>
    <PageTitle title="Tìm kiếm" />
    <section className="panel">
      <form className="form-stack search-form" role="search" aria-label="Tìm trong kho tri thức" onSubmit={search}>
        <div className="search-input-row">
          <TextInput type="search" label="Từ khóa" value={draft.q} onChange={(event) => {
            setDraft({ ...draft, q: event.currentTarget.value });
          }} />
          <Button type="submit" disabled={!hasCriteria(draft)}>Tìm</Button>
        </div>
        <fieldset className="search-filters">
          <legend>Thu hẹp theo nhóm</legend>
          <div className="search-filter-grid">
            {groupKinds.map((group) => <NativeSelect key={group.kind} label={group.label} value={draft[group.filter]}
              disabled={!groups.data} onChange={(event) => {
                setDraft({ ...draft, [group.filter]: event.currentTarget.value });
              }} data={[
                { value: '', label: 'Tất cả' },
                ...(groups.data?.[group.field].map((entry) => ({ value: String(entry.id), label: entry.name })) ?? []),
              ]} />)}
          </div>
        </fieldset>
        {groups.error && <ErrorNotice retry={groups.retry}>Chưa tải được nhóm.</ErrorNotice>}
        {(hasCriteria(draft) || hasCriteria(criteria)) && <div>
          <Button variant="subtle" onClick={() => {
            setDraft(criteriaFor('#/tim-kiem'));
            window.location.hash = '#/tim-kiem';
          }}>Xóa bộ lọc</Button>
        </div>}
      </form>
    </section>
    {hasCriteria(criteria)
      ? <SearchResults criteria={criteria} expanded={expanded} />
      : <section className="panel search-results" aria-label="Kết quả tìm kiếm"><Empty>Nhập từ khóa hoặc chọn một nhóm để tìm mục.</Empty></section>}
  </>;
}
