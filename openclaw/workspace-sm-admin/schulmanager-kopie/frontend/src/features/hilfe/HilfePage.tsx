/**
 * `/hilfe` – Handbuch in der App: Kurzanleitung(en) für die Rolle der angemeldeten Person (`GET /manual`).
 * Der Markdown-Text wird in React-Elemente umgewandelt (`markdown.ts`), nie als HTML eingefügt.
 */
import { Fragment, useState } from 'react';
import { Link } from 'react-router-dom';
import { http } from '../../api/client';
import { ErrorBox, Loading, Tabs } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { parseMarkdown, type Block, type Inline } from './markdown';

interface Guide {
  id: string;
  title: string;
  markdown: string;
}

function Inlines({ items }: { items: Inline[] }) {
  return (
    <>
      {items.map((it, i) => {
        if (it.t === 'text') return <Fragment key={i}>{it.v}</Fragment>;
        if (it.t === 'strong') return <strong key={i}><Inlines items={it.v} /></strong>;
        if (it.t === 'code') return <code key={i} className="mono">{it.v}</code>;
        return it.href.startsWith('/') ? (
          <Link key={i} to={it.href}><Inlines items={it.v} /></Link>
        ) : (
          <a key={i} href={it.href} target="_blank" rel="noopener noreferrer"><Inlines items={it.v} /></a>
        );
      })}
    </>
  );
}

function Blocks({ blocks }: { blocks: Block[] }) {
  return (
    <>
      {blocks.map((b, i) => {
        if (b.t === 'h') {
          const H = (b.level === 1 ? 'h2' : b.level === 2 ? 'h3' : 'h4') as 'h2' | 'h3' | 'h4';
          return <H key={i} id={b.id}><Inlines items={b.v} /></H>;
        }
        if (b.t === 'p') return <p key={i}><Inlines items={b.v} /></p>;
        const List = b.t === 'ul' ? 'ul' : 'ol';
        return (
          <List key={i}>
            {b.items.map((it, k) => (
              <li key={k}><Inlines items={it} /></li>
            ))}
          </List>
        );
      })}
    </>
  );
}

export default function HilfePage() {
  useTitle('Hilfe');
  const q = useApi((signal) => http.get<{ role: string; guides: Guide[] }>('/manual', undefined, { signal }), []);
  const [active, setActive] = useState<string | null>(null);
  const guides = q.data?.guides ?? [];
  const current = guides.find((g) => g.id === active) ?? guides[0];
  return (
    <div className="page page-narrow stack">
      <div className="page-head">
        <h1>Hilfe</h1>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && guides.length === 0 && <p className="muted">Für Ihre Rolle gibt es keine Kurzanleitung.</p>}
      {guides.length > 1 && (
        <Tabs
          label="Anleitungen"
          tabs={guides.map((g) => ({ key: g.id, label: g.title.replace(/^Kurzanleitung für /, '') }))}
          active={current?.id ?? ''}
          onChange={setActive}
        />
      )}
      {current && (
        <article className="card help-article stack-sm" aria-label={current.title}>
          <Blocks blocks={parseMarkdown(current.markdown)} />
        </article>
      )}
    </div>
  );
}
