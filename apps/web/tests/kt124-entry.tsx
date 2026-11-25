import { useState } from 'react';
import { MarkdownEditor } from '../src/MarkdownEditor';
export { act, createElement } from 'react';
export { createRoot } from 'react-dom/client';
export { MantineProvider } from '@mantine/core';
export { KnowledgeText } from '../src/KnowledgeText';
export { wikiQuery, wikiInsertion } from '../src/WikiCompletion';
export { headingId } from '../src/NoteOutline';
export { KnowledgeCommandPalette } from '../src/KnowledgeCommandPalette';
export { NoteLinkContext } from '../src/NoteLinkContext';
export function Editor({ initial = '', onChange = () => {} }: { initial?: string; onChange?: (text: string) => void }) {
  const [value, setValue] = useState(initial);
  return <MarkdownEditor value={value} title="Bài" disabled={false} onChange={(text) => { setValue(text); onChange(text); }} onSave={() => {}} onCompositionChange={() => {}} />;
}
