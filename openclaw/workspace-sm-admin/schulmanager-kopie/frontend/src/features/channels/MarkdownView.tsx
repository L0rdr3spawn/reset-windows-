/** Anzeige von Markdown-Text (siehe `markdown.ts`) – nur React-Elemente, Links in neuem Tab ohne Referrer. */
import { Fragment, lazy, Suspense, type ReactNode } from 'react';
import { parseMarkdown, type Block, type Inline } from './markdown';

/** Formeln (KaTeX) kommen erst in einem eigenen Bündel, wenn ein Text eine enthält. */
const MathView = lazy(() => import('./MathView'));

function math(tex: string, display: boolean, key: string | number): ReactNode {
  return (
    <Suspense key={key} fallback={<code className="kr-math-src">{display ? `$$${tex}$$` : `$${tex}$`}</code>}>
      <MathView tex={tex} display={display} />
    </Suspense>
  );
}

function inlines(nodes: Inline[], keyPrefix = ''): ReactNode[] {
  return nodes.map((n, i) => {
    const key = `${keyPrefix}${i}`;
    switch (n.t) {
      case 'text':
        return <Fragment key={key}>{n.v}</Fragment>;
      case 'br':
        return <br key={key} />;
      case 'code':
        return <code key={key}>{n.v}</code>;
      case 'math':
        return math(n.v, !!n.display, key);
      case 'strong':
        return <strong key={key}>{inlines(n.c, `${key}-`)}</strong>;
      case 'em':
        return <em key={key}>{inlines(n.c, `${key}-`)}</em>;
      case 'link':
        return (
          <a key={key} href={n.href} target="_blank" rel="noopener noreferrer nofollow">
            {inlines(n.c, `${key}-`)}
          </a>
        );
      default:
        return null;
    }
  });
}

function block(b: Block, i: number): ReactNode {
  switch (b.t) {
    case 'h': {
      // Seitenüberschriften sind h1/h2 – Text-Überschriften beginnen bei h3
      const Tag = (['h3', 'h4', 'h5'] as const)[b.level - 1]!;
      return <Tag key={i}>{inlines(b.c)}</Tag>;
    }
    case 'p':
      return <p key={i}>{inlines(b.c)}</p>;
    case 'ul':
      return (
        <ul key={i}>
          {b.items.map((it, j) => (
            <li key={j}>{inlines(it)}</li>
          ))}
        </ul>
      );
    case 'ol':
      return (
        <ol key={i}>
          {b.items.map((it, j) => (
            <li key={j}>{inlines(it)}</li>
          ))}
        </ol>
      );
    case 'quote':
      return <blockquote key={i}>{inlines(b.c)}</blockquote>;
    case 'math':
      return (
        <div key={i} className="kr-math-block">
          {math(b.v, true, i)}
        </div>
      );
    case 'pre':
      return (
        <pre key={i}>
          <code>{b.v}</code>
        </pre>
      );
    default:
      return null;
  }
}

export function Markdown({ text, className }: { text: string; className?: string }) {
  const blocks = parseMarkdown(text);
  if (!blocks.length) return null;
  return <div className={`kr-md${className ? ` ${className}` : ''}`}>{blocks.map(block)}</div>;
}

export default Markdown;
