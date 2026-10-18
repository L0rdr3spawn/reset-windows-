import { useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { collator, visibleRange } from '../lib/format';

export interface Column<T> {
  key: string;
  header: ReactNode;
  render: (row: T) => ReactNode;
  /** Wert zum Sortieren (Klick auf Spaltenkopf) */
  sortValue?: (row: T) => string | number;
  className?: string;
  width?: string;
}

/**
 * Virtualisierte Tabelle: rendert nur sichtbare Zeilen (flüssig auch bei > 5000 Zeilen).
 * Echte <table>-Semantik mit Platzhalterzeilen oben/unten; Spaltenköpfe sortierbar.
 */
export function VirtualTable<T>({
  rows,
  columns,
  rowKey,
  height = 560,
  rowHeight = 40,
  onRowClick,
  selectedKey,
  caption,
  emptyText = 'Keine Einträge',
  rowClassName,
}: {
  rows: readonly T[];
  columns: Column<T>[];
  rowKey: (row: T) => string;
  height?: number | string;
  rowHeight?: number;
  onRowClick?: (row: T) => void;
  selectedKey?: string | null;
  caption: string;
  emptyText?: string;
  rowClassName?: (row: T) => string | undefined;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [viewport, setViewport] = useState(typeof height === 'number' ? height : 600);
  const [sort, setSort] = useState<{ key: string; dir: 1 | -1 } | null>(null);
  // tatsächliche Zeilenhöhe messen (Rahmen/Zeilenumbrüche), damit Platzhalter exakt passen
  const [measured, setMeasured] = useState(rowHeight);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    setViewport(el.clientHeight || viewport);
    const row = el.querySelector<HTMLTableRowElement>('tbody tr[data-row]');
    if (row) {
      const h = row.getBoundingClientRect().height;
      if (h > 0 && Math.abs(h - measured) > 0.5) setMeasured(h);
    }
  });

  const sorted = useMemo(() => {
    if (!sort) return rows;
    const col = columns.find((c) => c.key === sort.key);
    if (!col?.sortValue) return rows;
    const sv = col.sortValue;
    return rows.slice().sort((a, b) => {
      const x = sv(a);
      const y = sv(b);
      const r = typeof x === 'number' && typeof y === 'number' ? x - y : collator.compare(String(x), String(y));
      return r * sort.dir;
    });
  }, [rows, columns, sort]);

  const rh = measured || rowHeight;
  const [start, end] = visibleRange(scrollTop, viewport, rh, sorted.length);
  const visible = sorted.slice(start, end);

  return (
    <div>
      <div
        ref={ref}
        className="virtual-scroll"
        style={{ maxHeight: height, ['--row-h' as string]: `${rowHeight}px` }}
        onScroll={(e) => {
          setScrollTop(e.currentTarget.scrollTop);
          setViewport(e.currentTarget.clientHeight);
        }}
        tabIndex={0}
        role="region"
        aria-label={caption}
      >
        <table className="table">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr>
              {columns.map((c) => {
                const active = sort?.key === c.key;
                return (
                  <th
                    key={c.key}
                    scope="col"
                    style={c.width ? { width: c.width } : undefined}
                    className={c.className}
                    aria-sort={active ? (sort?.dir === 1 ? 'ascending' : 'descending') : undefined}
                  >
                    {c.sortValue ? (
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        style={{ padding: 0, minHeight: 0, fontWeight: 600 }}
                        onClick={() =>
                          setSort((s) => (s?.key === c.key ? (s.dir === 1 ? { key: c.key, dir: -1 } : null) : { key: c.key, dir: 1 }))
                        }
                      >
                        {c.header}
                        <span aria-hidden="true">{active ? (sort?.dir === 1 ? ' ▲' : ' ▼') : ''}</span>
                      </button>
                    ) : (
                      c.header
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {start > 0 && (
              <tr aria-hidden="true" style={{ height: start * rh }}>
                <td colSpan={columns.length} style={{ padding: 0, border: 0 }} />
              </tr>
            )}
            {visible.map((row) => {
              const k = rowKey(row);
              const cls = [onRowClick ? 'clickable' : '', selectedKey === k ? 'selected' : '', rowClassName?.(row) ?? '']
                .filter(Boolean)
                .join(' ');
              return (
                <tr
                  key={k}
                  data-row=""
                  className={cls || undefined}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  onKeyDown={
                    onRowClick
                      ? (e) => {
                          if (e.key === 'Enter' && e.target === e.currentTarget) onRowClick(row);
                        }
                      : undefined
                  }
                  tabIndex={onRowClick ? 0 : undefined}
                  aria-selected={selectedKey !== undefined ? selectedKey === k : undefined}
                >
                  {columns.map((c) => (
                    <td key={c.key} className={c.className}>
                      {c.render(row)}
                    </td>
                  ))}
                </tr>
              );
            })}
            {end < sorted.length && (
              <tr aria-hidden="true" style={{ height: (sorted.length - end) * rh }}>
                <td colSpan={columns.length} style={{ padding: 0, border: 0 }} />
              </tr>
            )}
            {sorted.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="center muted" style={{ padding: '2rem' }}>
                  {emptyText}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="table-footer">
        <span>{sorted.length} Einträge</span>
      </div>
    </div>
  );
}
