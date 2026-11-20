import { Button, MultiSelect } from '@mantine/core';
import { useRef, useState, type SubmitEvent } from 'react';
import { request } from './api';
import { groupKinds, groupSearchHref, type Group, type GroupField, type GroupKind, type Groups } from './groups';
import { Empty, ErrorNotice, Loading, useResource } from './views';
import { RelatedSources } from './RelatedSources';

type Assignment = Group & { origin: string; user_pinned: boolean };
type Organization = { status: string } & Record<GroupField, Assignment[]>;
type EditableGroups = Record<GroupField, string[]>;
type GroupPatch = Partial<Record<`${GroupKind}_ids`, number[]>>;

function selectedGroups(value: Organization): EditableGroups {
  function ids(field: GroupField) {
    return value[field].filter((entry) => entry.user_pinned || entry.origin === 'user').map((entry) => String(entry.id));
  }
  return { topics: ids('topics'), projects: ids('projects'), tags: ids('tags') };
}

function changedGroups(initial: EditableGroups, selected: EditableGroups) {
  const body: GroupPatch = {};
  for (const group of groupKinds) {
    const before = initial[group.field];
    const after = selected[group.field];
    if (before.length !== after.length || after.some((id) => !before.includes(id))) {
      body[`${group.kind}_ids`] = after.map(Number);
    }
  }
  return body;
}

function GroupEditor({ id, csrf, current, onSaved, onCancel }: {
  id: string;
  csrf: string;
  current: Organization;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const groups = useResource<Groups>('/groups');
  const [initial] = useState(() => selectedGroups(current));
  const [selected, setSelected] = useState(initial);
  const inFlight = useRef(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(false);
  const body = changedGroups(initial, selected);

  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current || !groups.data || !Object.keys(body).length) return;
    inFlight.current = true;
    setSaving(true);
    setError(false);
    try {
      await request<Organization>(`/items/${encodeURIComponent(id)}/organization`, { method: 'PATCH', body, csrf });
      onSaved();
    } catch {
      setError(true);
    } finally {
      inFlight.current = false;
      setSaving(false);
    }
  }

  return <form className="form-stack" onSubmit={save}>
    <p className="group-edit-caption">Chọn nhánh mục lục để xếp bài; có thể chọn nhiều nhánh mà không nhân bản nội dung. Các nhóm đã tự xếp vẫn được giữ.</p>
    {groups.error ? <ErrorNotice retry={groups.retry}>Chưa tải được các nhóm có thể chọn.</ErrorNotice>
      : !groups.data ? <Loading />
        : groupKinds.map((group) => {
          const available = new Map<number, Group>();
          for (const entry of current[group.field]) available.set(entry.id, entry);
          for (const entry of groups.data?.[group.field] ?? []) available.set(entry.id, entry);
          return <MultiSelect key={group.kind} label={group.label} disabled={saving} searchable
            nothingFoundMessage="Không tìm thấy nhóm." value={selected[group.field]}
            data={[...available.values()].map((entry) => ({ value: String(entry.id), label: entry.path || entry.name }))}
            onChange={(value) => setSelected({ ...selected, [group.field]: value })} />;
        })}
    {error && <ErrorNotice>Chưa lưu được các nhóm. Hãy thử lại.</ErrorNotice>}
    <div className="form-actions">
      <Button type="submit" disabled={!groups.data || !Object.keys(body).length} loading={saving}>Lưu nhóm</Button>
      <Button variant="default" disabled={saving} onClick={onCancel}>Hủy</Button>
    </div>
  </form>;
}

export function ItemOrganization({ id, csrf, deleted, refreshKey, onSaved }: { id: string; csrf: string; deleted: boolean; refreshKey?: string; onSaved?: () => void }) {
  const organization = useResource<Organization>(`/items/${encodeURIComponent(id)}/organization`, { refreshKey });
  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);
  const current = organization.data;

  return <section className="panel" aria-labelledby="item-group-title">
    <div className="panel-heading">
      <h2 id="item-group-title">Nhóm của mục</h2>
      {current && !editing && !deleted && <Button variant="default" size="compact-sm" onClick={() => {
        setSaved(false);
        setEditing(true);
      }}>Chỉnh nhóm</Button>}
    </div>
    {organization.error ? <ErrorNotice retry={organization.retry}>Chưa tải được nhóm của mục.</ErrorNotice>
      : !current ? <Loading />
        : <>
          {groupKinds.some((group) => current[group.field].length > 0)
            ? groupKinds.filter((group) => current[group.field].length > 0).map((group) => <div className="group-block" key={group.kind}>
              <h3>{group.label}</h3>
              <ul className="group-list assigned-groups">
                {current[group.field].map((entry) => <li key={entry.id}>
                  <a href={groupSearchHref(group.filter, entry.id)} title="Xem bài trong nhánh hoặc nhóm">{entry.path || entry.name}</a>
                  <span className="list-meta">{entry.user_pinned ? 'Đã cố định' : entry.origin === 'auto' ? 'Tự xếp' : 'Người dùng'}</span>
                </li>)}
              </ul>
            </div>)
            : <Empty>Chưa có nhóm.</Empty>}
          {editing && !deleted && <GroupEditor id={id} csrf={csrf} current={current} onCancel={() => setEditing(false)} onSaved={() => {
            setEditing(false);
            setSaved(true);
            organization.retry();
            onSaved?.();
          }} />}
        </>}
    {saved && <div className="notice" role="status">Đã lưu nhóm.</div>}
  </section>;
}

export function RelatedItems({ id, refreshKey }: { id: string; refreshKey?: string }) {
  return <RelatedSources id={id} refreshKey={refreshKey} />;
}
