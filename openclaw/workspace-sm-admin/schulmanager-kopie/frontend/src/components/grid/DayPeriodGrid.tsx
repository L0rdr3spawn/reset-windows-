/**
 * DayPeriodGrid – DER Baustein für jede Ansicht „Tage × Stunden“ (docs/DESIGN.md §10a).
 *
 * Er ist das Stundenplan-Raster: Kopf mit Wochentag/Datum/Ferien, Zeitspalte mit Stunde und Uhrzeit, dicke Linien nach
 * Pausen, Trennlinie vor dem Wochenende, durchgehende Schraffur für gesperrte Felder, Heute-Markierung, Abblendung von
 * Tagen ohne Unterricht, waagerechtes Scrollen mit festgehaltener Zeitspalte und – auf Wunsch – die Listenansicht fürs
 * Handy. Jede Ansicht liefert nur Achsen (`days`, `rows`) und den Inhalt je Zelle (`cell`); Aussehen und Zellzustände
 * (frei, gesperrt, gut/mittel/schlecht, Heatmap, ausgewählt, Konflikt) kommen aus `styles/timetable.css`.
 *
 * Zeilen müssen keine Unterrichtsstunden sein: auch Pausen/Bereiche (Aufsichten) sind „Zeilen“ (`rows[i].heading`
 * setzt eine Gruppenüberschrift davor). Blöcke über mehrere Stunden oder Spuren (Stundenplan) kommen als `overlay`.
 * Neue Raster NIE von Hand bauen – der Gestaltungstest (`lib/__tests__/designRules.test.ts`) lehnt das ab.
 */
import { useMemo, type CSSProperties, type HTMLAttributes, type ReactNode } from 'react';
import { useMediaQuery } from '../../hooks/misc';

export interface GridDay {
  key: string | number;
  /** ausgeschriebener Name („Montag“) */
  name: string;
  /** Kürzel („Mo“) – bei Tagen ohne Unterricht statt des Namens */
  short?: string;
  /** Datum im Kopf („12.10.“) */
  date?: string;
  holiday?: string;
  /** Tag ohne Unterricht: schmal und abgeblendet */
  off?: boolean;
  today?: boolean;
  /** kräftige Trennlinie davor (Samstag nach Freitag) */
  divider?: boolean;
  /** Unterspalten (Stundenplan mit Parallelblöcken), Standard 1 */
  lanes?: number;
  /** Zusatzinfo im Kopf (Termine, Anteile …) */
  header?: ReactNode;
  /** Kopf antippbar (Editoren: ganzen Tag markieren) */
  onHeadClick?: () => void;
  headPressed?: boolean;
  headTitle?: string;
  headDisabled?: boolean;
  /** füllt den ganzen Tag statt der Zellen (Ferien, Feiertag, kein Unterricht) */
  fill?: ReactNode;
}

export interface GridRow {
  key: string | number;
  /** „1.“ oder „Hofpause“ */
  label: ReactNode;
  /** Uhrzeit o. ä. unter dem Namen */
  time?: ReactNode;
  /** dicke Linie nach dieser Zeile (Pause) */
  breakAfter?: boolean;
  /** Gruppenüberschrift über der Zeile (volle Breite) */
  heading?: ReactNode;
  onHeadClick?: () => void;
  headPressed?: boolean;
  headTitle?: string;
  headDisabled?: boolean;
}

export type GridTone = 'free' | 'good' | 'mid' | 'bad' | 'muted' | 'conflict' | 'wish';

export interface GridCell {
  content?: ReactNode;
  title?: string;
  /** gesperrt: schraffiert (durchsichtig) */
  blocked?: boolean;
  /** Statusfarbe */
  tone?: GridTone;
  /** Heatmap 0 … 1 (Anteil, z. B. versäumt) */
  heat?: number;
  selected?: boolean;
  /** weitere Klassen (Ziehen: ok / conflict / origin / dragover) */
  className?: string;
  /** Ereignisse der Zelle (Ziehen, Zeiger) */
  handlers?: HTMLAttributes<HTMLDivElement>;
}

export interface DayPeriodGridProps {
  days: readonly GridDay[];
  rows: readonly GridRow[];
  /** Beschriftung für Screenreader */
  label: string;
  /** Inhalt/Zustand je Feld; `null` = leeres Feld */
  cell?: (day: number, row: number) => GridCell | null | undefined;
  /** Blöcke, die selbst per `gridRow`/`gridColumn` platziert sind (siehe `rowLine`, `dayColumnStarts`) */
  overlay?: ReactNode;
  /** fester Spaltenverlauf (sonst aus `days` berechnet) */
  columnTemplate?: string;
  /** Mindestbreite einer Tagesspalte (z. B. '4rem') */
  minCol?: string;
  /** Mindestbreite des ganzen Rasters (Standard 680px, Zahl = px) */
  minWidth?: number | string;
  /** Mindesthöhe einer Zeile (Standard 64px, `compact` 46px) */
  rowHeight?: number | string;
  compact?: boolean;
  /** Ecke oben links (Standard: nur für Screenreader „Stunde“) */
  corner?: ReactNode;
  /** zusätzliche Klassen am Raster (z. B. `editing` für Ziehen/Antippen) */
  gridClassName?: string;
  className?: string;
  /** Listenansicht fürs Handy; ersetzt das Raster unterhalb von `mobileQuery` */
  mobileList?: ReactNode;
  mobileQuery?: string;
  legend?: ReactNode;
}

/** Grid-Zeile (1-basiert) der Zeile `r` (Zeile 1 = Kopf; Gruppenüberschriften zählen mit). */
export function rowLine(rows: readonly GridRow[], r: number): number {
  let line = 2;
  for (let i = 0; i < rows.length; i++) {
    if (rows[i]?.heading) line++;
    if (i === r) return line;
    line++;
  }
  return line;
}

/** Erste Grid-Spalte (1-basiert) je Tag; Spalte 1 = Zeitspalte. */
export function dayColumnStarts(days: readonly GridDay[]): number[] {
  const out: number[] = [];
  let col = 2;
  for (const d of days) {
    out.push(col);
    col += Math.max(1, d.lanes ?? 1);
  }
  return out;
}

function defaultTemplate(days: readonly GridDay[], minCol: string): string {
  const parts = ['minmax(3.6rem, max-content)'];
  for (const d of days) {
    const l = Math.max(1, d.lanes ?? 1);
    if (d.off && l === 1) {
      parts.push('minmax(2.5rem, 0.3fr)');
      continue;
    }
    const fr = +(1 / l).toFixed(4);
    for (let i = 0; i < l; i++) parts.push(`minmax(${minCol}, ${fr}fr)`);
  }
  return parts.join(' ');
}

/** Heatmap-Zellen: Anteil 0 … 1 als Stilwert (`--heat`). */
export function heatStyle(level: number): CSSProperties {
  return { ['--heat' as string]: Math.max(0, Math.min(1, level)) };
}

export function DayPeriodGrid({
  days,
  rows,
  label,
  cell,
  overlay,
  columnTemplate,
  minCol = '0px',
  minWidth,
  rowHeight,
  compact,
  corner,
  gridClassName,
  className,
  mobileList,
  mobileQuery = '(max-width: 700px)',
  legend,
}: DayPeriodGridProps) {
  const narrow = useMediaQuery(mobileQuery);
  const starts = useMemo(() => dayColumnStarts(days), [days]);
  const template = columnTemplate ?? defaultTemplate(days, minCol);
  const lines = useMemo(() => rows.map((_, r) => rowLine(rows, r)), [rows]);
  const totalRows = rows.length + rows.filter((r) => r.heading).length;
  if (narrow && mobileList !== undefined) {
    return (
      <>
        {mobileList}
        {legend}
      </>
    );
  }
  const style: Record<string, string | number> = {
    gridTemplateColumns: template,
    gridTemplateRows: `auto${rows.map((r) => `${r.heading ? ' auto' : ''} minmax(var(--tt-row, 64px), auto)`).join('')}`,
  };
  if (minWidth !== undefined) style['--tt-min'] = typeof minWidth === 'number' ? `${minWidth}px` : minWidth;
  if (rowHeight !== undefined) style['--tt-row'] = typeof rowHeight === 'number' ? `${rowHeight}px` : rowHeight;
  const colOf = (d: number) => `${starts[d] ?? 2} / span ${Math.max(1, days[d]?.lanes ?? 1)}`;

  return (
    <>
      <div className={`tt-scroll${className ? ` ${className}` : ''}`}>
        <div className={`tt-grid${compact ? ' compact' : ''}${gridClassName ? ` ${gridClassName}` : ''}`} style={style as CSSProperties} role="region" aria-label={label}>
          <div className="tt-head tt-corner" style={{ gridRow: 1, gridColumn: 1 }}>
            {corner ?? <span className="sr-only">Stunde</span>}
          </div>
          {days.map((d, di) => {
            const cls = `tt-head${d.today ? ' today' : ''}${d.off ? ' off-day' : ''}${d.divider ? ' day-divider' : ''}`;
            // langer Name; bei schmalen Spalten zeigt styles/timetable.css (Container-Abfrage) nur das Kürzel – so
            // sehen die Köpfe in jeder Ansicht gleich aus, egal was die Ansicht liefert
            const name = d.off ? (
              <span className="tt-day-name">
                <abbr title={`${d.name} – Kein Unterricht`}>{d.short ?? d.name}</abbr>
              </span>
            ) : d.short && d.short !== d.name ? (
              <span className="tt-day-name">
                <span className="tt-day-long">{d.name}</span>
                <span className="tt-day-short" aria-hidden="true">
                  {d.short}
                </span>
              </span>
            ) : (
              <span className="tt-day-name">{d.name}</span>
            );
            const inner = (
              <>
                {name}
                {d.date && <span className="tt-day-date">{d.date}</span>}
                {d.holiday && <span className="tt-day-holiday">{d.holiday}</span>}
                {d.off && <span className="sr-only">{d.name}: Kein Unterricht</span>}
              </>
            );
            return (
              <div
                key={`h${d.key}`}
                className={cls}
                style={{ gridRow: 1, gridColumn: colOf(di) }}
                aria-current={d.today ? 'date' : undefined}
                title={d.off ? 'Kein Unterricht' : d.holiday || undefined}
              >
                {d.onHeadClick ? (
                  <button type="button" className="tt-head-btn" aria-pressed={d.headPressed} disabled={d.headDisabled} title={d.headTitle} onClick={d.onHeadClick}>
                    {inner}
                  </button>
                ) : (
                  inner
                )}
                {d.header}
              </div>
            );
          })}
          {rows.map((row, r) => {
            const line = lines[r] ?? r + 2;
            const inner = (
              <>
                <strong>{row.label}</strong>
                {row.time !== undefined && row.time !== '' && <span>{row.time}</span>}
              </>
            );
            return [
              row.heading ? (
                <div key={`g${row.key}`} className="tt-group" style={{ gridRow: line - 1, gridColumn: '1 / -1' }}>
                  {row.heading}
                </div>
              ) : null,
              <div key={`t${row.key}`} className={`tt-time${row.breakAfter ? ' break-after' : ''}`} style={{ gridRow: line, gridColumn: 1 }}>
                {row.onHeadClick ? (
                  <button type="button" className="tt-head-btn tt-row-btn" aria-pressed={row.headPressed} disabled={row.headDisabled} title={row.headTitle} onClick={row.onHeadClick}>
                    {inner}
                  </button>
                ) : (
                  inner
                )}
              </div>,
            ];
          })}
          {days.map((d, di) =>
            d.fill !== undefined && d.fill !== null ? (
              <div
                key={`f${d.key}`}
                className={`tt-slot tt-day-fill${d.off ? ' off-day' : ''}${d.divider ? ' day-divider' : ''}`}
                style={{ gridRow: `2 / span ${totalRows}`, gridColumn: colOf(di) }}
              >
                {d.fill}
              </div>
            ) : (
              rows.map((row, r) => {
                const c = cell?.(di, r) ?? null;
                const cls = [
                  'tt-slot',
                  d.off ? 'off-day' : '',
                  d.today ? 'today' : '',
                  c?.blocked ? 'blocked' : '',
                  row.breakAfter ? 'break-after' : '',
                  d.divider ? 'day-divider' : '',
                  c?.tone ? `tone-${c.tone}` : '',
                  c?.heat !== undefined ? 'heat' : '',
                  c?.selected ? 'is-selected' : '',
                  c?.className ?? '',
                ]
                  .filter(Boolean)
                  .join(' ');
                const st: CSSProperties = { gridRow: lines[r] ?? r + 2, gridColumn: colOf(di) };
                if (c?.heat !== undefined) Object.assign(st, heatStyle(c.heat));
                return (
                  <div key={`s${d.key}:${row.key}`} {...c?.handlers} className={cls} style={st} title={c?.title}>
                    {c?.content}
                  </div>
                );
              })
            ),
          )}
          {overlay}
        </div>
      </div>
      {legend}
    </>
  );
}

export type LegendTone = GridTone | 'blocked' | 'ok' | 'bad' | 'heat' | 'selected' | 'changed' | 'cancelled' | 'absent' | 'exam' | 'today';

/**
 * Legende unter dem Raster: Farbfelder mit Text, gleiche Zustände wie im Raster (Klassen aus styles/timetable.css).
 * Statt eines Farbfelds geht auch ein Symbol (`icon`, z. B. Schloss für „fixiert“) oder nur Text.
 */
export function GridLegend({ items, hidden = true }: { items: { tone?: LegendTone; icon?: ReactNode; label: ReactNode }[]; hidden?: boolean }) {
  return (
    <div className="tt-legend" aria-hidden={hidden || undefined}>
      {items.map((it, i) => (
        <span key={i}>
          {it.tone ? <span className={`sw ${it.tone}`} /> : it.icon}
          {it.label}
        </span>
      ))}
    </div>
  );
}
