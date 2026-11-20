export type Group = { id: number; name: string; path?: string };

export const groupKinds = [
  { kind: 'topic', field: 'topics', filter: 'topic_id', label: 'Mục lục' },
  { kind: 'project', field: 'projects', filter: 'project_id', label: 'Dự án' },
  { kind: 'tag', field: 'tags', filter: 'tag_id', label: 'Nhãn' },
] as const;

export type GroupKind = (typeof groupKinds)[number]['kind'];
export type GroupField = (typeof groupKinds)[number]['field'];
export type GroupFilter = (typeof groupKinds)[number]['filter'];

export type Groups = Record<GroupField, Group[]>;

export function groupSearchHref(filter: GroupFilter, id: number) {
  if (filter === 'topic_id') return `#/thu-vien?node=${id}`;
  const params = new URLSearchParams({ q: '', [filter]: String(id) });
  return `#/tim-kiem?${params}`;
}
