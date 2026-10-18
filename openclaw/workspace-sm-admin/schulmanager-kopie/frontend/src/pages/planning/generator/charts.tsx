/**
 * Eigene SVG-Diagramme der Generator-Auswertung (keine Bibliothek): waagerechte Balken, Säulen und Linien.
 * Farben ausschließlich über Design-Tokens (`generator.css`), hell und dunkel; jede Grafik hat Achsen, Werte an den
 * Marken, eine Legende (ab zwei Reihen) und die Werte als Tabelle. Breite folgt dem Behälter (Handy ab 320 px).
 */
import { useLayoutEffect, useRef, useState, type ReactNode, type RefObject } from 'react';
import { clip, compact, fmt, niceMax, niceRange, ticks } from './logic';
import './generator.css';

/** Farbrolle einer Reihe: `before` neutral, `after` Akzent, `good`/`bad` Status, `best`/`other` für Linien. */
export type Tone = 'before' | 'after' | 'good' | 'bad' | 'best' | 'other';

export interface Series {
  name: string;
  tone: Tone;
}

/** Breite des Behälters in Pixeln (folgt Größenänderungen). */
export function useWidth<T extends HTMLElement>(): [RefObject<T | null>, number] {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    setWidth(el.clientWidth);
    if (typeof ResizeObserver === 'undefined') return undefined;
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width;
      if (w) setWidth(Math.floor(w));
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, width];
}

export function Legend({ series }: { series: Series[] }) {
  if (series.length < 2) return null;
  return (
    <ul className="gc-legend" aria-label="Legende">
      {series.filter((s, i) => series.findIndex((x) => x.name === s.name) === i).map((s) => (
        <li key={s.name}>
          <span className={`gc-sw gc-fill-${s.tone}`} aria-hidden="true" />
          {s.name}
        </li>
      ))}
    </ul>
  );
}

export interface TableData {
  head: string[];
  rows: (string | number)[][];
}

/** Rahmen einer Grafik: Titel, Legende, Zeile für den Wert unter dem Zeiger, Wertetabelle nur für Screenreader. */
export function ChartCard({
  title,
  subtitle,
  series,
  readout,
  table,
  children,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  series: Series[];
  readout?: string;
  table: TableData;
  children: ReactNode;
}) {
  return (
    <figure className="gc-card">
      <figcaption>
        <strong>{title}</strong>
        {subtitle && <span className="gc-sub">{subtitle}</span>}
      </figcaption>
      <Legend series={series} />
      <div className="gc-plot">{children}</div>
      <p className="gc-readout" aria-hidden="true">
        {readout || ' '}
      </p>
      <table className="sr-only">
        <caption>{typeof title === 'string' ? title : 'Werte'}</caption>
        <thead>
          <tr>
            {table.head.map((h, i) => (
              <th key={i} scope="col">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((r, i) => (
            <tr key={i}>
              {r.map((c, j) => (
                <td key={j}>{c}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}

/** Balken mit abgerundetem Datenende, am Fußpunkt eckig. `dir`: right (waagerecht) oder up (Säule). */
export function barPath(x: number, y: number, w: number, h: number, dir: 'right' | 'up', radius = 4): string {
  if (w <= 0 || h <= 0) return '';
  if (dir === 'right') {
    const r = Math.min(radius, w, h / 2);
    return `M${x},${y}h${w - r}a${r},${r} 0 0 1 ${r},${r}v${h - 2 * r}a${r},${r} 0 0 1 ${-r},${r}h${-(w - r)}z`;
  }
  const r = Math.min(radius, h, w / 2);
  return `M${x},${y + h}v${-(h - r)}a${r},${r} 0 0 1 ${r},${-r}h${w - 2 * r}a${r},${r} 0 0 1 ${r},${r}v${h - r}z`;
}

// ------------------------------------------------------------------ waagerechte Balken
export interface BarRow {
  key: string;
  label: string;
  values: number[];
}

export function HBars({
  title,
  subtitle,
  rows,
  series,
  unit,
  format = fmt,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  rows: BarRow[];
  series: Series[];
  unit?: string;
  format?: (n: number) => string;
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState('');
  const W = Math.max(width, 240);
  const labelW = Math.round(Math.min(Math.max(W * 0.38, 96), 190));
  const padR = 54;
  const plotW = Math.max(60, W - labelW - padR);
  const barH = 12;
  const inner = 2;
  const rowH = series.length * barH + (series.length - 1) * inner + 12;
  const top = niceMax(Math.max(0, ...rows.flatMap((r) => r.values)));
  const tk = ticks(top, W < 420 ? 2 : 4);
  const H = rows.length * rowH + 22;
  const x = (v: number) => labelW + (v / top) * plotW;
  return (
    <ChartCard
      title={title}
      subtitle={subtitle}
      series={series}
      readout={hover}
      table={{ head: ['Eintrag', ...series.map((s) => `${s.name}${unit ? ` (${unit})` : ''}`)], rows: rows.map((r) => [r.label, ...r.values.map((v) => format(v))]) }}
    >
      <div ref={ref} className="gc-svgbox">
        {rows.length === 0 ? (
          <p className="muted small">Keine Einträge.</p>
        ) : (
          <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${typeof title === 'string' ? title : 'Balkendiagramm'}, ${rows.length} Einträge`}>
            {tk.map((t) => (
              <g key={t}>
                <line className="gc-grid" x1={x(t)} x2={x(t)} y1={0} y2={rows.length * rowH} />
                <text className="gc-text" x={x(t)} y={rows.length * rowH + 14} textAnchor="middle">
                  {compact(t)}
                </text>
              </g>
            ))}
            {rows.map((r, i) => {
              const y0 = i * rowH + 6;
              return (
                <g key={r.key} onMouseEnter={() => setHover(`${r.label}: ${series.map((s, k) => `${s.name} ${format(r.values[k] ?? 0)}`).join(' · ')}`)} onMouseLeave={() => setHover('')}>
                  <title>{`${r.label}: ${series.map((s, k) => `${s.name} ${format(r.values[k] ?? 0)}`).join(', ')}`}</title>
                  <text className="gc-label" x={labelW - 8} y={y0 + (series.length * (barH + inner)) / 2} textAnchor="end" dominantBaseline="middle">
                    {clip(r.label, Math.floor((labelW - 8) / 6.6))}
                  </text>
                  {series.map((s, k) => {
                    const v = r.values[k] ?? 0;
                    const y = y0 + k * (barH + inner);
                    const w = Math.max(0, x(v) - labelW);
                    return (
                      <g key={s.name}>
                        <path className={`gc-fill-${s.tone}`} d={barPath(labelW, y, w, barH, 'right')} />
                        <text className="gc-value" x={labelW + w + 5} y={y + barH / 2} dominantBaseline="middle">
                          {format(v)}
                        </text>
                      </g>
                    );
                  })}
                </g>
              );
            })}
            <line className="gc-axis" x1={labelW} x2={labelW} y1={0} y2={rows.length * rowH} />
          </svg>
        )}
      </div>
    </ChartCard>
  );
}

// ------------------------------------------------------------------ Säulen
export interface ColumnGroup {
  key: string;
  label: string;
  values: number[];
}

export function Columns({
  title,
  subtitle,
  groups,
  series,
  xTitle,
  unit,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  groups: ColumnGroup[];
  series: Series[];
  xTitle?: string;
  unit?: string;
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState('');
  const W = Math.max(width, 260);
  const padL = 38;
  const padR = 8;
  const padT = 18;
  const padB = xTitle ? 38 : 24;
  const H = 200;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;
  const top = niceMax(Math.max(0, ...groups.flatMap((g) => g.values)));
  const tk = ticks(top, 4);
  const band = plotW / Math.max(1, groups.length);
  const barW = Math.max(3, Math.min(24, (band - 8) / series.length - 2));
  const y = (v: number) => padT + plotH - (v / top) * plotH;
  const showValues = barW >= 12 || (groups.length <= 12 && band / series.length >= 24);
  return (
    <ChartCard
      title={title}
      subtitle={subtitle}
      series={series}
      readout={hover}
      table={{ head: [xTitle ?? 'Eintrag', ...series.map((s) => `${s.name}${unit ? ` (${unit})` : ''}`)], rows: groups.map((g) => [g.label, ...g.values.map((v) => fmt(v))]) }}
    >
      <div ref={ref} className="gc-svgbox">
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${typeof title === 'string' ? title : 'Säulendiagramm'}, ${groups.length} Gruppen`}>
          {tk.map((t) => (
            <g key={t}>
              <line className="gc-grid" x1={padL} x2={W - padR} y1={y(t)} y2={y(t)} />
              <text className="gc-text" x={padL - 6} y={y(t)} textAnchor="end" dominantBaseline="middle">
                {compact(t)}
              </text>
            </g>
          ))}
          {groups.map((g, i) => {
            const cx = padL + band * i + band / 2;
            const totalW = series.length * barW + (series.length - 1) * 2;
            return (
              <g key={g.key} onMouseEnter={() => setHover(`${g.label}: ${series.map((s, k) => `${s.name} ${fmt(g.values[k] ?? 0)}`).join(' · ')}`)} onMouseLeave={() => setHover('')}>
                <title>{`${g.label}: ${series.map((s, k) => `${s.name} ${fmt(g.values[k] ?? 0)}`).join(', ')}`}</title>
                <rect x={padL + band * i} y={padT} width={band} height={plotH} className="gc-hit" />
                {series.map((s, k) => {
                  const v = g.values[k] ?? 0;
                  const bx = cx - totalW / 2 + k * (barW + 2);
                  const h = plotH - (y(v) - padT);
                  return (
                    <g key={s.name}>
                      <path className={`gc-fill-${s.tone}`} d={barPath(bx, y(v), barW, h, 'up')} />
                      {showValues && (
                        <text className="gc-value" x={bx + barW / 2} y={y(v) - 4} textAnchor="middle">
                          {fmt(v)}
                        </text>
                      )}
                    </g>
                  );
                })}
                <text className="gc-text" x={cx} y={padT + plotH + 15} textAnchor="middle">
                  {g.label}
                </text>
              </g>
            );
          })}
          <line className="gc-axis" x1={padL} x2={W - padR} y1={padT + plotH} y2={padT + plotH} />
          {xTitle && (
            <text className="gc-text" x={padL + plotW / 2} y={H - 4} textAnchor="middle">
              {xTitle}
            </text>
          )}
        </svg>
      </div>
    </ChartCard>
  );
}

// ------------------------------------------------------------------ Linien
export interface LineSeries extends Series {
  points: [number, number][];
}

export function Lines({
  title,
  subtitle,
  lines,
  xTitle,
  yTitle,
  xUnit,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  lines: LineSeries[];
  xTitle: string;
  yTitle: string;
  xUnit: string;
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [cursor, setCursor] = useState<number | null>(null);
  const W = Math.max(width, 260);
  const padL = 46;
  const padR = 16;
  const padT = 24;
  const padB = 44;
  const H = 240;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;
  const all = lines.flatMap((l) => l.points);
  const xMax = Math.max(0.001, ...all.map((p) => p[0]));
  const yr = niceRange(Math.min(...all.map((p) => p[1])), Math.max(0, ...all.map((p) => p[1])), 4);
  const xTop = niceMax(xMax);
  const xs = (v: number) => padL + (v / xTop) * plotW;
  const ys = (v: number) => padT + plotH - ((v - yr.lo) / (yr.hi - yr.lo || 1)) * plotH;
  const yt = yr.ticks;
  const xt = ticks(xTop, W < 420 ? 2 : 4);
  const lead = lines.find((l) => l.tone === 'best') ?? lines[0];
  const valueAt = (l: LineSeries, x: number): number | null => {
    if (!l.points.length) return null;
    let best = l.points[0] as [number, number];
    for (const p of l.points) if (Math.abs(p[0] - x) < Math.abs(best[0] - x)) best = p;
    return best[1];
  };
  const onMove = (e: React.PointerEvent<SVGRectElement>) => {
    const box = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - box.left) / Math.max(1, box.width)) * plotW;
    setCursor(Math.max(0, Math.min(xMax, (px / plotW) * xTop)));
  };
  const readout =
    cursor === null || !lead
      ? ''
      : `Nach ${fmt(cursor)} ${xUnit}: ${lines
          .slice(0, 6)
          .map((l) => `${l.name} ${fmt(valueAt(l, cursor))}`)
          .join(' · ')}`;
  const rows = lead
    ? lead.points.map((p, i) => [fmt(p[0]), ...lines.map((l) => fmt(l.points[Math.min(i, l.points.length - 1)]?.[1] ?? null))])
    : [];
  return (
    <ChartCard
      title={title}
      subtitle={subtitle}
      series={lines}
      readout={readout}
      table={{ head: [`${xTitle} (${xUnit})`, ...lines.map((l) => l.name)], rows }}
    >
      <div ref={ref} className="gc-svgbox">
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${typeof title === 'string' ? title : 'Liniendiagramm'}, ${lines.length} Reihen`}>
          {yt.map((t) => (
            <g key={t}>
              <line className="gc-grid" x1={padL} x2={W - padR} y1={ys(t)} y2={ys(t)} />
              <text className="gc-text" x={padL - 6} y={ys(t)} textAnchor="end" dominantBaseline="middle">
                {compact(t)}
              </text>
            </g>
          ))}
          {xt.map((t) => (
            <text key={t} className="gc-text" x={xs(t)} y={padT + plotH + 15} textAnchor="middle">
              {fmt(t)}
            </text>
          ))}
          <line className="gc-axis" x1={padL} x2={W - padR} y1={padT + plotH} y2={padT + plotH} />
          <text className="gc-text" x={padL + plotW / 2} y={H - 6} textAnchor="middle">
            {xTitle} ({xUnit})
          </text>
          <text className="gc-text" x={4} y={10} textAnchor="start">
            {yTitle}
          </text>
          {[...lines].sort((a) => (a.tone === 'best' ? 1 : -1)).map((l) => {
            const d = l.points.map((p, i) => `${i ? 'L' : 'M'}${xs(p[0]).toFixed(1)},${ys(p[1]).toFixed(1)}`).join('');
            const last = l.points[l.points.length - 1];
            return (
              <g key={l.name}>
                <path className={`gc-line gc-line-${l.tone}`} d={d} />
                {last && <circle className={`gc-dot gc-fill-${l.tone}`} cx={xs(last[0])} cy={ys(last[1])} r={4} />}
              </g>
            );
          })}
          {cursor !== null && <line className="gc-cursor" x1={xs(cursor)} x2={xs(cursor)} y1={padT} y2={padT + plotH} />}
          <rect
            x={padL}
            y={padT}
            width={plotW}
            height={plotH}
            className="gc-hit"
            onPointerMove={onMove}
            onPointerLeave={() => setCursor(null)}
          />
        </svg>
      </div>
    </ChartCard>
  );
}
