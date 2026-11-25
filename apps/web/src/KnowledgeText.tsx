import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { externalHttpUrl } from './api';
import { remarkNoteOutline } from './NoteOutline';
import './NoteNavigation.css';

const internalItemHref = (url: string) => url.length === 42 && /^#\/muc\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(url);

/** Source HTML is skipped; images require an explicit click. */
export function KnowledgeText({ text, title }: { text: string; title?: string }) {
  const heading = /^#[ \t]+([^\r\n]+)(?:\r?\n|$)/.exec(text);
  const body = heading && heading[1].trim() === title?.trim() ? text.slice(heading[0].length) : text;
  return <div className="knowledge-text">
    <Markdown skipHtml remarkPlugins={[remarkGfm, remarkNoteOutline]} urlTransform={(url, key) => key === 'href' && (internalItemHref(url) || /^#kt-heading-[a-z0-9]+-\d+$/.test(url)) ? url : externalHttpUrl(url) ?? ''}
      components={{
        h1: ({ children, id }) => <h2 id={id} tabIndex={-1}>{children}</h2>, h2: ({ children, id }) => <h3 id={id} tabIndex={-1}>{children}</h3>, h3: ({ children, id }) => <h4 id={id} tabIndex={-1}>{children}</h4>,
        h4: ({ children, id }) => <h4 id={id} tabIndex={-1}>{children}</h4>, h5: ({ children, id }) => <h5 id={id} tabIndex={-1}>{children}</h5>, h6: ({ children, id }) => <h6 id={id} tabIndex={-1}>{children}</h6>,
        a: ({ href, children }) => href ? href.startsWith('#kt-heading-') ? <a href={href} onClick={(event) => {
          event.preventDefault();
          const target = event.currentTarget.closest('.knowledge-text')?.querySelector<HTMLElement>(href);
          target?.scrollIntoView?.({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
          target?.focus({ preventScroll: true });
        }}>{children}</a> : internalItemHref(href) ? <a href={href}>{children}</a> : <a href={href} target="_blank" rel="noopener noreferrer">{children}</a> : <span>{children}</span>,
        img: ({ src, alt }) => typeof src === 'string' && src ? <a href={src} target="_blank" rel="noopener noreferrer">Ảnh minh họa: {alt || 'Mở ảnh'}</a> : <span>{alt}</span>,
        table: ({ children }) => <div className="knowledge-table"><table>{children}</table></div>,
      }}>{body}</Markdown>
  </div>;
}

export function knowledgePreview(text: string) {
  return text.replace(/^#[ \t]+[^\r\n]+(?:\r?\n|$)/, '').replace(/^#{1,6}\s+/gm, '').replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/[`*~]/g, '').replace(/\s+/g, ' ').trim().slice(0, 220);
}
