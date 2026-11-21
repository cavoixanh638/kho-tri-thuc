import { externalHttpUrl } from './api';

export const noteTemplates = [
  { id: 'lesson', version: 1, label: 'Bài học', description: 'Ý chính, ví dụ và việc áp dụng.',
    markdown: '# Bài học\n\n## Ý chính\n\n\n\n## Ví dụ\n\n\n\n## Áp dụng\n\n- [ ] \n' },
  { id: 'book', version: 1, label: 'Sách / Chương', description: 'Luận điểm, trích dẫn và liên hệ.',
    markdown: '# Sách / Chương\n\n## Luận điểm\n\n\n\n## Trích dẫn cần đối chiếu\n\n> \n\n## Liên hệ và ghi chú\n\n' },
  { id: 'meeting', version: 1, label: 'Cuộc họp', description: 'Nội dung, quyết định và việc cần làm.',
    markdown: '# Cuộc họp\n\n## Nội dung trao đổi\n\n\n\n## Quyết định\n\n\n\n## Việc cần làm\n\n- [ ] \n' },
  { id: 'video', version: 1, label: 'Video nguồn', description: 'Quan sát và mốc cần kiểm tra ở nguồn.',
    markdown: '# Video nguồn\n\n## Điều quan sát được\n\n\n\n## Mốc cần đối chiếu\n\n- Thời điểm: \n\n## Ghi chú và câu hỏi\n\n' },
] as const;

export type NoteTemplateId = typeof noteTemplates[number]['id'];
export type NoteTemplateMetadata = { author?: string; sourceDate?: string; sourceUrl?: string };
export type NoteTemplateApplication = { expectedNote: string; nextNote: string; templateId: NoteTemplateId; templateVersion: number };
export const NOTE_TEMPLATE_MAX_LENGTH = 65_536; // Works with both the existing capture and edit contracts.

const inline = (value: string) => value.replace(/[\\`*_{}\[\]<>!#|]/g, '\\$&');

/** Builds an ordinary Markdown insertion. Never reads or writes an Item or source. */
export function proposeNoteTemplate(note: string, templateId: NoteTemplateId, metadata: NoteTemplateMetadata = {}): NoteTemplateApplication {
  const template = noteTemplates.find((entry) => entry.id === templateId);
  if (!template) throw new Error('Mẫu không còn khả dụng.');
  const { author = '', sourceDate = '', sourceUrl = '' } = metadata;
  if (author.length > 200 || /[\r\n\u0000]/.test(author)) throw new Error('Tên tác giả cần nằm trên một dòng, tối đa 200 ký tự.');
  if (sourceDate && (!/^\d{4}-\d{2}-\d{2}$/.test(sourceDate) || Number.isNaN(new Date(sourceDate).getTime()) || new Date(sourceDate).toISOString().slice(0, 10) !== sourceDate)) throw new Error('Ngày nguồn chưa hợp lệ.');
  if (sourceUrl && (sourceUrl.length > 4096 || /[\r\n\u0000]/.test(sourceUrl) || !externalHttpUrl(sourceUrl))) throw new Error('Liên kết nguồn cần là HTTP hoặc HTTPS hợp lệ.');
  const fields = [author && `Tác giả: ${inline(author)}`, sourceDate && `Ngày nguồn: ${sourceDate}`, sourceUrl && `Liên kết nguồn: ${inline(sourceUrl)}`].filter(Boolean);
  const [heading, ...body] = template.markdown.split('\n');
  const content = [heading, ...(fields.length ? ['', ...fields] : []), ...body].join('\n');
  const newline = note.match(/\r\n|\r|\n/)?.[0] ?? '\n';
  const nextNote = note + (note ? newline + newline : '') + content.replace(/\n/g, newline);
  if (nextNote.length > NOTE_TEMPLATE_MAX_LENGTH) throw new Error('Bản nháp quá dài để thêm mẫu. Hãy giữ nội dung hiện có.');
  return { expectedNote: note, nextNote, templateId: template.id, templateVersion: template.version };
}

/** Host applies the proposal against its latest draft, never against a saved source. */
export function acceptNoteTemplate(currentNote: string, proposal: NoteTemplateApplication): string | undefined {
  return currentNote === proposal.expectedNote && proposal.nextNote.startsWith(currentNote) ? proposal.nextNote : undefined;
}
