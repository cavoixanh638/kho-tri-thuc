type MarkdownNode = { type: string; value?: string; depth?: number; children?: MarkdownNode[]; data?: { hName?: string; hProperties?: Record<string, unknown> } };
export type OutlineHeading = { id: string; depth: number; text: string };
const textOf = (node: MarkdownNode): string => node.value ?? node.children?.map(textOf).join('') ?? '';
export function headingId(text: string, occurrence: number) {
  const normalized = text.normalize('NFC');
  let hash = 2166136261;
  for (const char of normalized) { hash ^= char.codePointAt(0)!; hash = Math.imul(hash, 16777619); }
  return 'kt-heading-' + (hash >>> 0).toString(36) + '-' + occurrence;
}
/** Operates on Markdown AST: fences, escapes, HTML and setext are parsed upstream. */
export function remarkNoteOutline() {
  return (tree: MarkdownNode) => {
    const headings: OutlineHeading[] = [];
    const occurrences = new Map<string, number>();
    const visit = (node: MarkdownNode) => {
      if (node.type === 'heading') {
        const text = textOf(node);
        const key = text.normalize('NFC');
        const number = (occurrences.get(key) ?? 0) + 1; occurrences.set(key, number);
        const id = headingId(text, number);
        node.data = { ...node.data, hProperties: { ...node.data?.hProperties, id, tabIndex: -1 } };
        headings.push({ id, depth: node.depth ?? 1, text });
      }
      node.children?.forEach(visit);
    };
    visit(tree);
    if (headings.length < 2) return;
    tree.children?.unshift({
      type: 'blockquote', data: { hName: 'nav', hProperties: { className: 'note-outline', 'aria-label': 'Mục lục trong bài' } },
      children: [
        { type: 'paragraph', children: [{ type: 'strong', children: [{ type: 'text', value: 'Trong bài này' }] }] },
        { type: 'list', children: headings.map((heading) => ({
          type: 'listItem', data: { hProperties: { 'data-depth': heading.depth } },
          children: [{ type: 'paragraph', children: [{ type: 'link', ...{ url: '#' + heading.id }, children: [{ type: 'text', value: heading.text }] } as MarkdownNode] }],
        })) },
      ],
    });
  };
}
