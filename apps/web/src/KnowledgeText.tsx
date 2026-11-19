import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { externalHttpUrl } from './api';

/** Source HTML is skipped; images require an explicit click. */
export function KnowledgeText({ text }: { text: string }) {
  return <div className="knowledge-text">
    <Markdown skipHtml remarkPlugins={[remarkGfm]} urlTransform={(url) => externalHttpUrl(url) ?? ''}
      components={{
        h1: ({ children }) => <h3>{children}</h3>, h2: ({ children }) => <h3>{children}</h3>, h3: ({ children }) => <h4>{children}</h4>,
        a: ({ href, children }) => href ? <a href={href} target="_blank" rel="noopener noreferrer">{children}</a> : <span>{children}</span>,
        img: ({ src, alt }) => typeof src === 'string' && src ? <a href={src} target="_blank" rel="noopener noreferrer">Ảnh minh họa: {alt || 'Mở ảnh'}</a> : <span>{alt}</span>,
        table: ({ children }) => <div className="knowledge-table"><table>{children}</table></div>,
      }}>{text}</Markdown>
  </div>;
}

export function knowledgePreview(text: string) {
  return text.replace(/^#{1,6}\s+/gm, '').replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/[`*_~]/g, '').replace(/\s+/g, ' ').trim().slice(0, 220);
}
