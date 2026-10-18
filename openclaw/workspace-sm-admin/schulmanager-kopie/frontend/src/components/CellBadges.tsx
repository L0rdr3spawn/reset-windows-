/**
 * Kleine Abzeichen unten rechts in einer Stunde (Kalenderwoche): Hausaufgaben, Tests/Klausuren, Nachschreiben,
 * Nachteilsausgleich, Termine, Krankmeldung – je Art ein Abzeichen, übereinander gestapelt (Hausaufgaben zuerst). Mehrere Einträge derselben Art werden zu einem
 * Abzeichen mit Zähler („HA 2“), das beim Antippen eine kleine Liste mit je einem Link öffnet.
 */
import type { CSSProperties } from 'react';
import { Link } from 'react-router-dom';
import type { Cell } from '../api/types';
import { PopButton } from './PopButton';

export type CellLink = NonNullable<Cell['links']>[number];

const ORDER = ['ha', 'exam', 'makeup', 'support', 'missing', 'event', 'duty', 'absent'] as const;
const GROUP_LABEL = {
  ha: 'Hausaufgaben',
  exam: 'Prüfungen',
  makeup: 'Nachschreibtermin',
  support: 'Nachteilsausgleich',
  missing: 'Nachschreiben nötig',
  event: 'Termine',
  duty: 'Pflichttermine',
  absent: 'Abwesenheit',
} as const;
/** Listen mit Namen (Nachteilsausgleich, fehlt) zeigen auch bei einem Eintrag die Liste statt eines Links. */
const ALWAYS_LIST: ReadonlySet<string> = new Set(['support', 'missing']);

export function groupLinks(links: readonly CellLink[]): { kind: (typeof ORDER)[number]; items: CellLink[] }[] {
  return ORDER.map((kind) => ({ kind, items: links.filter((l) => (l.kind ?? 'ha') === kind) })).filter((g) => g.items.length);
}

/** Beschriftung des Sammel-Abzeichens: „HA 2“, „Test 2“, „Klausur 2“, „Prüfungen 2“ */
export function groupLabel(kind: (typeof ORDER)[number], items: readonly CellLink[]): string {
  if (kind === 'ha') return `HA ${items.length}`;
  if (kind === 'absent') return items[0]?.label ?? 'krank';
  if (ALWAYS_LIST.has(kind)) return `${items[0]?.label ?? ''} ${items.length}`;
  if (kind === 'event' || kind === 'duty') return items.length > 1 ? `${items[0]?.label} ${items.length}` : (items[0]?.label ?? '');
  const labels = [...new Set(items.map((i) => i.label))];
  return labels.length === 1 ? `${labels[0]} ${items.length}` : `Prüfungen ${items.length}`;
}

export function CellBadges({ links, className = 'tt-cell-links', style }: { links: readonly CellLink[]; className?: string; style?: CSSProperties }) {
  if (!links.length) return null;
  return (
    <div className={className} style={style} onClick={(e) => e.stopPropagation()}>
      {groupLinks(links).map(({ kind, items }) =>
        items.length === 1 && items[0].to && !ALWAYS_LIST.has(kind) ? (
          <Link key={kind} to={items[0].to} onClick={items[0].onClick} className={`tt-cell-link tt-link-${kind}${items[0].done ? ' done' : ''}`} title={items[0].title} aria-label={items[0].title ? `${items[0].label}: ${items[0].title}` : items[0].label}>
            {items[0].label}
          </Link>
        ) : (
          <PopButton key={kind} className={`tt-cell-link tt-link-${kind}`} label={`${groupLabel(kind, items)} ▾`} ariaLabel={`${GROUP_LABEL[kind]}: ${items.length}`}>
            <ul className="pop-items">
              {items.map((l) => (
                <li key={`${l.to}|${l.title ?? l.label}`} className={l.done ? 'done' : undefined}>
                  {l.to ? (
                    <Link to={l.to} onClick={l.onClick}>
                      {l.title ?? l.label}
                    </Link>
                  ) : (
                    <span>{l.title ?? l.label}</span>
                  )}
                </li>
              ))}
            </ul>
          </PopButton>
        ),
      )}
    </div>
  );
}
