import { Button, NativeSelect, TextInput } from '@mantine/core';
import { useRef, useState, type SubmitEvent } from 'react';
import { ApiError, request } from './api';
import { groupKinds, type Group, type GroupKind, type Groups } from './groups';
import { ErrorNotice, Loading, useResource } from './views';

export function GroupsManager({ csrf }: { csrf: string }) {
  const groups = useResource<Groups>('/groups');
  const [kind, setKind] = useState<GroupKind>('topic');
  const [name, setName] = useState('');
  const inFlight = useRef(false);
  const [saving, setSaving] = useState(false);
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState('');

  async function createGroup(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current || !name.trim()) return;
    inFlight.current = true;
    setSaving(true);
    setError('');
    setConfirmation('');
    try {
      const created = await request<Group>('/groups', {
        method: 'POST', csrf, body: { kind, name: name.trim() },
      });
      setName('');
      setConfirmation(`Đã tạo nhóm “${created.name}”.`);
      groups.retry();
    } catch (error) {
      setError(error instanceof ApiError && error.status === 409
        ? 'Tên nhóm đã có. Hãy chọn tên khác.'
        : 'Chưa tạo được nhóm. Kiểm tra tên rồi thử lại.');
    } finally {
      inFlight.current = false;
      setSaving(false);
    }
  }

  return <div className="panel group-catalog">
    {groups.error ? <ErrorNotice retry={groups.retry}>Chưa tải được danh sách nhóm.</ErrorNotice>
      : !groups.data ? <Loading />
        : groupKinds.map((group) => {
          const entries = groups.data?.[group.field] ?? [];
          return <div className="group-block" key={group.kind}>
            <h3>{group.label}</h3>
            {entries.length ? <ul className="group-list">{entries.map((entry) => <li key={entry.id}>{entry.name}</li>)}</ul>
              : <span className="list-meta">—</span>}
          </div>;
        })}
    <form className="form-stack" onSubmit={createGroup}>
      <NativeSelect label="Loại nhóm" value={kind} disabled={saving} onChange={(event) => setKind(event.currentTarget.value as GroupKind)}
        data={groupKinds.map((group) => ({ value: group.kind, label: group.label }))} />
      <TextInput label="Tên nhóm" value={name} maxLength={120} required disabled={saving} onChange={(event) => setName(event.currentTarget.value)} />
      {error && <ErrorNotice>{error}</ErrorNotice>}
      {confirmation && <div className="notice" role="status">{confirmation}</div>}
      <div className="form-actions"><Button type="submit" loading={saving} disabled={!name.trim()}>Tạo nhóm</Button></div>
    </form>
  </div>;
}
