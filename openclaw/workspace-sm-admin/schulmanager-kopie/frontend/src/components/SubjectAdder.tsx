import { useEffect, useId, useMemo, useRef, useState } from 'react';
import type { Subject } from '../api/types';
import { matchesQuery } from '../lib/format';
import { Icon } from './Icon';
import { NewSubjectDialog } from './NewSubjectDialog';

export interface SubjectChoice {
  id: string;
  name: string;
  room_type?: string | null;
}

/**
 * Der eine Weg, ein Fach in eine Liste zu bringen („Fach hinzufügen“): ein Knopf, darunter eine durchsuchbare Liste der
 * noch nicht verwendeten Fächer – und ganz unten „Neues Fach anlegen …“ (nur mit Recht `masterdata.edit`; ein
 * getippter Name, den es noch nicht gibt, wird als Vorschlag übernommen).
 */
export function SubjectAdder({
  options,
  onPick,
  canCreate,
  onCreated,
  label = 'Fach hinzufügen',
  className = 'btn btn-sm',
}: {
  /** Fächer, die noch gewählt werden dürfen */
  options: readonly SubjectChoice[];
  onPick: (subjectId: string) => void;
  canCreate: boolean;
  /** Ein neues Fach wurde angelegt; Standard: wie `onPick` */
  onCreated?: (s: Subject) => void;
  label?: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [creating, setCreating] = useState<string | null>(null);
  const [active, setActive] = useState(0);
  const wrapRef = useRef<HTMLDivElement>(null);
  const listId = useId();

  const sorted = useMemo(() => [...options].sort((a, b) => a.name.localeCompare(b.name, 'de')), [options]);
  const hits = useMemo(() => (query.trim() ? sorted.filter((o) => matchesQuery(`${o.name} ${o.id} ${o.room_type ?? ''}`, query)) : sorted), [sorted, query]);
  const exact = !!query.trim() && options.some((o) => o.name.toLowerCase() === query.trim().toLowerCase() || o.id.toLowerCase() === query.trim().toLowerCase());
  const createText = query.trim() && !exact ? `„${query.trim()}“ als neues Fach anlegen …` : 'Neues Fach anlegen …';

  useEffect(() => setActive(0), [query]);
  useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  const close = () => {
    setOpen(false);
    setQuery('');
  };
  const pick = (id: string) => {
    onPick(id);
    close();
  };
  const startCreate = () => {
    setCreating(exact ? '' : query.trim());
    close();
  };

  return (
    <div className="combo" ref={wrapRef} style={{ position: 'relative', display: 'inline-block' }}>
      <button type="button" className={className} aria-haspopup="listbox" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <Icon name="plus" /> {label}
      </button>
      {open && (
        <div className="card" style={{ position: 'absolute', zIndex: 20, left: 0, top: '100%', marginTop: 4, width: 'min(320px, 86vw)', padding: 8 }}>
          <input
            type="search"
            role="combobox"
            aria-label="Fach suchen"
            aria-expanded
            aria-controls={listId}
            placeholder="Fach suchen …"
            autoFocus
            autoComplete="off"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'ArrowDown') {
                e.preventDefault();
                setActive((a) => Math.min(hits.length - (canCreate ? 0 : 1), a + 1));
              } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setActive((a) => Math.max(0, a - 1));
              } else if (e.key === 'Enter') {
                e.preventDefault();
                const h = hits[active];
                if (h) pick(h.id);
                else if (canCreate && active === hits.length) startCreate();
              } else if (e.key === 'Escape') {
                e.stopPropagation();
                close();
              }
            }}
          />
          <ul id={listId} role="listbox" aria-label="Fächer" className="list-plain" style={{ maxHeight: 220, overflowY: 'auto', margin: '6px 0 0' }}>
            {hits.map((o, i) => (
              <li key={o.id} role="option" aria-selected={i === active} style={{ padding: 0 }}>
                <button
                  type="button"
                  className="btn btn-ghost w-100"
                  style={{ justifyContent: 'space-between', gap: 8, background: i === active ? 'var(--primary-soft)' : undefined }}
                  onClick={() => pick(o.id)}
                >
                  <span style={{ textAlign: 'left' }}>{o.name}</span>
                  <span className="xsmall muted">
                    {o.id}
                    {o.room_type ? ` · ${o.room_type}` : ''}
                  </span>
                </button>
              </li>
            ))}
            {hits.length === 0 && (
              <li className="small muted" style={{ padding: '6px 8px' }}>
                {sorted.length ? 'Kein passendes Fach.' : 'Alle Fächer sind schon dabei.'}
              </li>
            )}
          </ul>
          {canCreate && (
            <div style={{ borderTop: '1px solid var(--border, #ddd)', marginTop: 6, paddingTop: 6 }}>
              <button
                type="button"
                className="btn btn-ghost btn-sm w-100"
                style={{ justifyContent: 'flex-start', background: active === hits.length ? 'var(--primary-soft)' : undefined }}
                onClick={startCreate}
              >
                <Icon name="plus" /> {createText}
              </button>
            </div>
          )}
        </div>
      )}
      {creating !== null && (
        <NewSubjectDialog
          initialName={creating}
          onClose={() => setCreating(null)}
          onCreated={(s) => {
            if (onCreated) onCreated(s);
            else onPick(s.id);
          }}
        />
      )}
    </div>
  );
}
