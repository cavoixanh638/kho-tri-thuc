import { useEffect, useState } from 'react';
import { type Item } from './api';

type Draft = Pick<Item, 'title' | 'description' | 'note'>;
const prefix = 'kt-markdown-draft-v1:';
const fields = (item: Draft): Draft => ({ title: item.title, description: item.description, note: item.note });
export const sameDraft = (a: Draft, b: Draft) => a.title === b.title && a.description === b.description && a.note === b.note;

export function useMarkdownDraft(item: Item) {
  const key = prefix + item.item_id;
  const [initial] = useState(() => {
    try {
      const stored = JSON.parse(sessionStorage.getItem(key) ?? 'null');
      const valid = (value: Draft | undefined) => value && ['title', 'description', 'note'].every((field) => typeof value[field as keyof Draft] === 'string');
      if (valid(stored?.draft) && valid(stored?.base)) return { draft: fields(stored.draft), base: fields(stored.base), recovered: true };
    } catch { /* Storage may be disabled; keep the draft in memory. */ }
    return { draft: fields(item), base: fields(item), recovered: false };
  });
  const [draft, setDraft] = useState(initial.draft);
  const [base, setBase] = useState(initial.base);
  const [editing, setEditing] = useState(initial.recovered);
  const [recovered, setRecovered] = useState(initial.recovered);
  const [storageError, setStorageError] = useState(false);
  const dirty = editing && !sameDraft(draft, base);

  function clear() { try { sessionStorage.removeItem(key); } catch { /* No persistent draft exists. */ } }
  function finish() { clear(); setEditing(false); setRecovered(false); }
  function start() { setDraft(fields(item)); setBase(fields(item)); setEditing(true); setRecovered(false); }

  useEffect(() => {
    if (!editing) return;
    try {
      if (dirty) sessionStorage.setItem(key, JSON.stringify({ draft, base })); else sessionStorage.removeItem(key);
      setStorageError(false);
    } catch { setStorageError(true); }
  }, [key, editing, dirty, draft, base]);
  useEffect(() => {
    if (!dirty) return;
    const preventLoss = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', preventLoss);
    return () => window.removeEventListener('beforeunload', preventLoss);
  }, [dirty]);
  useEffect(() => {
    const expired = () => {
      try { for (const name of Object.keys(sessionStorage)) if (name.startsWith(prefix)) sessionStorage.removeItem(name); } catch { /* Storage unavailable. */ }
      setEditing(false);
      setDraft(fields(item));
      setRecovered(false);
    };
    window.addEventListener('session-expired', expired);
    return () => window.removeEventListener('session-expired', expired);
  }, [item]);
  return { draft, setDraft, base, editing, dirty, recovered, storageError, start, finish };
}
