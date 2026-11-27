type MarkdownNode = { type: string; value?: string; depth?: number; children?: MarkdownNode[]; data?: { hName?: string; hProperties?: Record<string, unknown> } };
export type OutlineHeading = { id: string; depth: number; text: string };
const textOf = (node: MarkdownNode): string => node.value ?? node.children?.map(textOf).join('') ?? '';
export function headingId(text: string, occurrence: number) {
  const normalized = text.normalize('NFC');
  let hash = 2166136261;
  for (const char of normalized) { hash ^= char.codePointAt(0)!; hash = Math.imul(hash, 16777619); }
  return 'kt-heading-' + (hash >>> 0).toString(36) + '-' + occurrence;
}
/** Group only actual root-level Markdown headings. Nested blockquotes/lists and
 * fenced code keep their original AST and semantics. A parent folds its entire
 * subtree until the next equal or higher Markdown heading, not visual H-level. */
function foldSections(tree: MarkdownNode) {
  type Section={heading:MarkdownNode;depth:number;body:MarkdownNode[]};
  const result:MarkdownNode[]=[], stack:Section[]=[];
  const append=(node:MarkdownNode)=>(stack.at(-1)?.body??result).push(node);
  const finish=()=>{
    const section=stack.pop()!;
    const heading=section.heading;
    const headingKey=heading.data?.hProperties?.id;
    if(!section.body.length||typeof headingKey!=='string'){append(heading);return;}
    append({
      type:'blockquote', data:{hName:'details',hProperties:{className:'kt-fold-section',id:'kt-fold-'+headingKey,open:true}},
      children:[
        {type:'blockquote',data:{hName:'summary'},children:[heading]},
        ...section.body,
      ],
    });
  };
  for(const node of tree.children??[]){
    if(node.type==='heading'){
      const depth=node.depth??1;
      while(stack.length&&stack.at(-1)!.depth>=depth)finish();
      stack.push({heading:node,depth,body:[]});
    }else append(node);
  }
  while(stack.length)finish();
  tree.children=result;
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
    foldSections(tree);
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
