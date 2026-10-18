import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { matchesQuery } from '../lib/format';

export interface SelectOption {
  value: string;
  label: string;
  /** zusätzlicher Text rechts (z. B. Klasse) */
  sub?: string;
  /** zusätzliche Suchbegriffe */
  keywords?: string;
}

/**
 * Durchsuchbare Auswahl (WAI-ARIA Combobox). Zeigt höchstens `limit` Treffer –
 * damit bleiben auch 2600 Schüler flüssig.
 */
export function SearchSelect({
  options,
  value,
  onChange,
  label,
  placeholder = 'Suchen …',
  limit = 60,
  allowClear,
  id: idProp,
  disabled,
  hideLabel,
}: {
  options: readonly SelectOption[];
  value: string | null | undefined;
  onChange: (value: string | null) => void;
  label: string;
  placeholder?: string;
  limit?: number;
  allowClear?: boolean;
  id?: string;
  disabled?: boolean;
  hideLabel?: boolean;
}) {
  const autoId = useId();
  const id = idProp ?? autoId;
  const listId = `${id}-list`;
  const selected = options.find((o) => o.value === value) ?? null;
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const wrapRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    if (!query.trim()) return options.slice(0, limit);
    const out: SelectOption[] = [];
    for (const o of options) {
      if (matchesQuery(`${o.label} ${o.value} ${o.sub ?? ''} ${o.keywords ?? ''}`, query)) {
        out.push(o);
        if (out.length >= limit) break;
      }
    }
    return out;
  }, [options, query, limit]);

  const total = useMemo(() => {
    if (!query.trim()) return options.length;
    let n = 0;
    for (const o of options) if (matchesQuery(`${o.label} ${o.value} ${o.sub ?? ''} ${o.keywords ?? ''}`, query)) n++;
    return n;
  }, [options, query]);

  useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  useEffect(() => setActive(0), [query]);

  const choose = (o: SelectOption | undefined) => {
    if (!o) return;
    onChange(o.value);
    setQuery('');
    setOpen(false);
  };

  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setOpen(true);
      setActive((a) => Math.min(filtered.length - 1, a + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((a) => Math.max(0, a - 1));
    } else if (e.key === 'Enter') {
      if (open) {
        e.preventDefault();
        choose(filtered[active]);
      }
    } else if (e.key === 'Escape') {
      if (open) {
        e.preventDefault();
        e.stopPropagation();
        setOpen(false);
        setQuery('');
      }
    }
  };

  const display = open ? query : selected ? `${selected.label}${selected.sub ? ` (${selected.sub})` : ''}` : '';

  return (
    <div className="field combo" ref={wrapRef}>
      <label htmlFor={id} className={hideLabel ? 'sr-only' : undefined}>
        {label}
      </label>
      <div className="row" style={{ flexWrap: 'nowrap' }}>
        <input
          ref={inputRef}
          id={id}
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={open && filtered[active] ? `${id}-opt-${active}` : undefined}
          autoComplete="off"
          placeholder={selected ? '' : placeholder}
          value={display}
          disabled={disabled}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => {
            setQuery('');
            setOpen(true);
          }}
          onClick={() => setOpen(true)}
          onKeyDown={onKey}
        />
        {allowClear && selected && !disabled && (
          <button
            type="button"
            className="btn btn-ghost btn-icon"
            aria-label={`${label}: Auswahl entfernen`}
            onClick={() => {
              onChange(null);
              inputRef.current?.focus();
            }}
          >
            ×
          </button>
        )}
      </div>
      {open && (
        <ul className="combo-list" role="listbox" id={listId} aria-label={label}>
          {filtered.length === 0 && <li className="combo-more">Keine Treffer</li>}
          {filtered.map((o, i) => (
            <li
              key={o.value}
              id={`${id}-opt-${i}`}
              role="option"
              aria-selected={i === active}
              className="combo-option"
              onMouseDown={(e) => {
                e.preventDefault();
                choose(o);
              }}
              onMouseEnter={() => setActive(i)}
            >
              <span>{o.label}</span>
              {o.sub && <span className="sub">{o.sub}</span>}
            </li>
          ))}
          {total > filtered.length && (
            <li className="combo-more" aria-hidden="true">
              {total - filtered.length} weitere – bitte Suche verfeinern
            </li>
          )}
        </ul>
      )}
    </div>
  );
}

/** Mehrfachauswahl: Chips + Suchfeld zum Hinzufügen. */
export function MultiSelect({
  options,
  values,
  onChange,
  label,
  placeholder = 'Hinzufügen …',
}: {
  options: readonly SelectOption[];
  values: readonly string[];
  onChange: (values: string[]) => void;
  label: string;
  placeholder?: string;
}) {
  const byValue = useMemo(() => new Map(options.map((o) => [o.value, o])), [options]);
  const remaining = useMemo(() => options.filter((o) => !values.includes(o.value)), [options, values]);
  return (
    <div className="stack-sm">
      <SearchSelect label={label} options={remaining} value={null} onChange={(v) => v && onChange([...values, v])} placeholder={placeholder} />
      {values.length > 0 && (
        <div className="chips" aria-label={`${label}: ausgewählt`}>
          {values.map((v) => (
            <span className="chip" key={v}>
              {byValue.get(v)?.label ?? v}
              <button type="button" onClick={() => onChange(values.filter((x) => x !== v))} aria-label={`${byValue.get(v)?.label ?? v} entfernen`}>
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
