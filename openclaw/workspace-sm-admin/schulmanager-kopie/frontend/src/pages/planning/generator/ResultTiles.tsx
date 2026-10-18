import { useMemo, useState } from 'react';
import { HelpTip } from '../../../components/HelpTip';
import { Modal } from '../../../components/Modal';
import { SegmentedControl } from '../../../components/ui';
import { WEEKDAYS_SHORT } from '../../../lib/dates';
import { Columns, HBars, Lines, type BarRow, type LineSeries, type Series } from './charts';
import {
  MOVE_LABELS,
  beforeAfter,
  costPartRows,
  deltaText,
  penaltyParts,
  recommendation,
  filterMoves,
  fmt,
  moveClasses,
  movedTotal,
  plural,
  verdict,
  type MoveFilter,
  type PenaltyPart,
} from './logic';
import type { EntityGroup, EntityRow, Evaluation, Kpi, MoveSpot, RunInfo, TracePoint } from './types';

/** Zusatzdaten zur Auswertung (nicht Teil von `Evaluation`). */
export interface ResultContext {
  beforeLabel: string;
  afterLabel: string;
  trace: TracePoint[];
  runs: RunInfo[];
  unplaced: Record<string, unknown>[];
}

type TileKey = string;

const KPI_HELP: Record<string, string> = {
  class_gaps: 'Freie Stunden zwischen Unterricht einer Klasse, im Durchschnitt je Schulwoche. Dieselbe Rechnung wie im Qualitätsbericht.',
  teacher_gaps: 'Freie Stunden zwischen Unterricht einer Lehrkraft, im Durchschnitt je Schulwoche. Dieselbe Rechnung wie im Qualitätsbericht.',
  site_changes: 'Wechsel einer Lehrkraft zwischen Standorten am selben Tag, im Durchschnitt je Schulwoche.',
  core_late: 'Unterrichtsblöcke von Hauptfächern, die nach der eingestellten letzten Stunde liegen.',
  unplaced_hours: 'Wochenstunden der Kurse, die noch keinen Platz im Plan haben.',
  conflicts: 'Doppelbelegungen von Klassen, Lehrkräften oder Räumen. Der Generator vermeidet sie; hier sehen Sie, ob welche bleiben.',
  cost: 'Summe der gewichteten Regelverstöße aus „Prioritäten & Regeln“. Niedriger ist besser.',
};
const EXTRA_HELP: Record<string, string> = {
  moves: 'Blöcke, die sich gegenüber dem aktuellen Plan geändert haben: anderer Tag, andere Stunde oder anderer Raum.',
  distribution: 'Unterrichtsstunden je Wochentag und je Stunde des Tages.',
  rules: 'Weiche Ziele aus „Prioritäten & Regeln“ mit Gewicht und den Verstößen vorher und nachher.',
  progress: 'Strafpunkte der Optimierung über die Rechenzeit, je paralleler Lauf.',
  hints: 'Meldungen des Generators, zum Beispiel Fächer, die an einem Tag mehrfach liegen mussten.',
};

const day = (d: number) => WEEKDAYS_SHORT[d] ?? String(d);

function seriesBA(ctx: ResultContext, afterTone: Series['tone'] = 'after'): Series[] {
  return [
    { name: ctx.beforeLabel, tone: 'before' },
    { name: ctx.afterLabel, tone: afterTone },
  ];
}

function Verdict({ delta, unit }: { delta: number | null; unit?: string }) {
  const v = verdict(delta);
  return (
    <span className={`gr-verdict${v === 'besser' ? ' good' : v === 'schlechter' ? ' bad' : ''}`}>
      {deltaText(delta)}
      {unit && delta ? ` ${unit}` : ''}
    </span>
  );
}

function Summary({ k, ctx }: { k: Kpi; ctx: ResultContext }) {
  return (
    <div className="gr-summary">
      <span>
        {ctx.beforeLabel}: <span className="gr-big">{fmt(k.before)}</span>
      </span>
      <span>
        {ctx.afterLabel}: <span className="gr-big">{fmt(k.after)}</span>
      </span>
      <Verdict delta={k.delta} />
    </div>
  );
}

function entityRows(rows: EntityRow[]): BarRow[] {
  return rows.map((r) => ({ key: r.id, label: r.name, values: [r.before, r.after] }));
}

function EntitySection({ group, noun, nouns, ctx }: { group: EntityGroup; noun: string; nouns: string; ctx: ResultContext }) {
  return (
    <>
      <p className="small" style={{ margin: 0 }}>
        {group.better_count} {group.better_count === 1 ? noun : nouns} verbessert, {group.worse_count} verschlechtert, {group.total - group.changed} unverändert.
      </p>
      <div className="gr-grid">
        <HBars title="Größte Verbesserungen" subtitle="weniger ist besser" rows={entityRows(group.better)} series={seriesBA(ctx, 'good')} />
        <HBars title="Größte Verschlechterungen" subtitle="weniger ist besser" rows={entityRows(group.worse)} series={seriesBA(ctx, 'bad')} />
      </div>
      <HBars title="Am stärksten betroffen im Entwurf" subtitle="höchste Werte nachher" rows={entityRows(group.highest)} series={seriesBA(ctx)} />
    </>
  );
}

function DistributionCharts({ ev, ctx, core }: { ev: Evaluation; ctx: ResultContext; core?: boolean }) {
  const s = seriesBA(ctx);
  return (
    <div className="gr-grid">
      {!core && (
        <Columns
          title="Stunden je Wochentag"
          groups={ev.distribution.days.map((d) => ({ key: String(d.day), label: d.label, values: [d.before, d.after] }))}
          series={s}
          xTitle="Wochentag"
          unit="Stunden"
        />
      )}
      <Columns
        title={core ? 'Hauptfach-Stunden je Stunde des Tages' : 'Stunden je Stunde des Tages'}
        subtitle={core ? 'nach der eingestellten letzten Stunde zählen sie als spät' : undefined}
        groups={(core ? ev.distribution.core_periods : ev.distribution.periods).map((p) => ({ key: String(p.period), label: String(p.period), values: [p.before, p.after] }))}
        series={s}
        xTitle="Stunde"
        unit="Stunden"
      />
    </div>
  );
}

function spot(s: MoveSpot | null): string {
  if (!s) return '–';
  const span = s.length > 1 ? `${s.start}.–${s.start + s.length - 1}.` : `${s.start}.`;
  return `${day(s.day)} ${span}${s.rooms.length ? ` · ${s.rooms.join(', ')}` : ''}`;
}

function MovesSection({ ev, ctx }: { ev: Evaluation; ctx: ResultContext }) {
  const c = ev.moves.counts;
  const [filter, setFilter] = useState<MoveFilter>({ kind: 'all', change: '', classId: '' });
  const classes = useMemo(() => moveClasses(ev.moves.items), [ev.moves.items]);
  const rows = useMemo(() => filterMoves(ev.moves.items, filter), [ev.moves.items, filter]);
  const one: Series[] = [{ name: 'Blöcke', tone: 'after' }];
  const shown = rows.slice(0, 200);
  return (
    <>
      <p className="small" style={{ margin: 0 }}>
        {plural(movedTotal(c), 'Block', 'Blöcke')} von {c.total_before} im {ctx.beforeLabel.toLowerCase()} unterscheiden sich; im Entwurf gibt es {c.total_after} Blöcke.
      </p>
      <div className="gr-grid">
        <HBars
          title="Was sich geändert hat"
          rows={[
            { key: 'u', label: 'Unverändert', values: [c.unchanged] },
            { key: 'r', label: 'Nur Raum anders', values: [c.room] },
            { key: 'm', label: 'Verschoben', values: [c.moved] },
            { key: 'a', label: 'Neu', values: [c.added] },
            { key: 'e', label: 'Entfallen', values: [c.removed] },
          ]}
          series={one}
          unit="Blöcke"
        />
        <HBars
          title="Bei verschobenen Blöcken"
          subtitle="ein Block kann mehreres ändern"
          rows={[
            { key: 'd', label: 'Anderer Tag', values: [c.day] },
            { key: 'p', label: 'Andere Stunde', values: [c.period] },
          ]}
          series={one}
          unit="Blöcke"
        />
      </div>
      <div className="gr-filters">
        <div className="field" style={{ minWidth: 0 }}>
          <span className="field-label">Art</span>
          <SegmentedControl
            label="Art der Änderung"
            value={filter.kind}
            onChange={(kind) => setFilter({ ...filter, kind })}
            options={(['all', 'moved', 'room', 'added', 'removed'] as const).map((k) => ({ value: k, label: MOVE_LABELS[k] }))}
          />
        </div>
        <div className="field" style={{ minWidth: 0 }}>
          <label htmlFor="gr-change">Geändert</label>
          <select id="gr-change" value={filter.change} onChange={(e) => setFilter({ ...filter, change: e.target.value as MoveFilter['change'] })}>
            <option value="">Alles</option>
            <option value="Tag">Tag</option>
            <option value="Stunde">Stunde</option>
            <option value="Raum">Raum</option>
          </select>
        </div>
        <div className="field" style={{ minWidth: 0 }}>
          <label htmlFor="gr-class">Klasse</label>
          <select id="gr-class" value={filter.classId} onChange={(e) => setFilter({ ...filter, classId: e.target.value })}>
            <option value="">Alle</option>
            {classes.map((cl) => (
              <option key={cl} value={cl}>
                {cl}
              </option>
            ))}
          </select>
        </div>
      </div>
      <p className="small muted" style={{ margin: 0 }}>
        {plural(rows.length, 'Eintrag', 'Einträge')}
        {rows.length > shown.length ? `, die ersten ${shown.length} sind aufgeführt` : ''}
        {ev.moves.truncated ? '. Die Liste ist auf 400 Einträge begrenzt.' : ''}
      </p>
      <div className="table-wrap" style={{ maxHeight: '40vh' }}>
        <table className="table table-compact">
          <thead>
            <tr>
              <th scope="col">Kurs</th>
              <th scope="col">Klassen</th>
              <th scope="col">Art</th>
              <th scope="col">Vorher</th>
              <th scope="col">Nachher</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((m, i) => (
              <tr key={`${m.course}-${i}`}>
                <td>{m.label}</td>
                <td>{m.classes.join(', ')}</td>
                <td>{m.changes.length ? `${MOVE_LABELS[m.kind]} (${m.changes.join(', ')})` : MOVE_LABELS[m.kind]}</td>
                <td>{spot(m.from)}</td>
                <td>{spot(m.to)}</td>
              </tr>
            ))}
            {shown.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  Keine Einträge.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

function RulesSection({ ev, ctx }: { ev: Evaluation; ctx: ResultContext }) {
  const rows = ev.rules;
  const top = rows.filter((r) => r.before !== null && r.after !== null).slice(0, 8);
  return (
    <>
      <HBars
        title="Verstöße je Ziel"
        subtitle="die wichtigsten Ziele zuerst"
        rows={top.map((r) => ({ key: r.id, label: r.title, values: [r.before ?? 0, r.after ?? 0] }))}
        series={seriesBA(ctx)}
      />
      <div className="table-wrap">
        <table className="table table-compact">
          <thead>
            <tr>
              <th scope="col">Ziel</th>
              <th scope="col">Wichtigkeit</th>
              <th scope="col" className="gr-numeric">
                Gewicht
              </th>
              <th scope="col" className="gr-numeric">
                {ctx.beforeLabel}
              </th>
              <th scope="col" className="gr-numeric">
                {ctx.afterLabel}
              </th>
              <th scope="col">Veränderung</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.title}</td>
                <td>{r.level_label}</td>
                <td className="gr-numeric">{fmt(r.weight)}</td>
                <td className="gr-numeric">{fmt(r.before)}</td>
                <td className="gr-numeric">{fmt(r.after)}</td>
                <td>{r.delta === null ? 'nicht zählbar' : deltaText(r.delta)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function ProgressSection({ ctx }: { ctx: ResultContext }) {
  const runs = ctx.runs.filter((r) => r.trace.length > 1);
  const many = runs.length > 3;
  const lines: LineSeries[] = runs.length
    ? runs.map((r) => ({
        name: r.best ? `Bester Lauf (Startwert ${r.seed})` : many ? 'Weitere Läufe' : `Lauf ${r.index + 1} (Startwert ${r.seed})`,
        tone: r.best ? 'best' : 'other',
        points: r.trace.map((p) => [p[0], p[2]] as [number, number]),
      }))
    : ctx.trace.length > 1
      ? [{ name: 'Lauf', tone: 'best', points: ctx.trace.map((p) => [p[0], p[2]] as [number, number]) }]
      : [];
  return (
    <>
      {lines.length === 0 ? (
        <p className="muted">Für diesen Lauf liegt kein Verlauf vor.</p>
      ) : (
        <Lines title="Strafpunkte über die Rechenzeit" subtitle="niedriger ist besser" lines={lines} xTitle="Rechenzeit" yTitle="Strafpunkte" xUnit="s" />
      )}
      {ctx.runs.length > 0 && (
        <>
          <HBars
            title="Strafpunkte je Lauf"
            subtitle="niedriger ist besser"
            rows={ctx.runs.map((r) => ({ key: String(r.index), label: `Lauf ${r.index + 1}${r.best ? ' (bester)' : ''}`, values: [r.cost ?? 0] }))}
            series={[{ name: 'Strafpunkte', tone: 'after' }]}
          />
          <p className="small muted" style={{ margin: 0 }}>
            {plural(ctx.runs.length, 'Lauf', 'Läufe')} · {ctx.runs.reduce((n, r) => n + r.iterations, 0).toLocaleString('de-DE')} Schritte
          </p>
        </>
      )}
    </>
  );
}

function CostSection({ ev, ctx, k }: { ev: Evaluation; ctx: ResultContext; k: Kpi }) {
  const rec = recommendation(ev.kpis);
  const unplaced = ev.kpis.find((x) => x.key === 'unplaced_hours');
  const exact = (ev.cost_parts?.length ?? 0) > 0;
  const parts: (PenaltyPart & { top?: { name: string; points: number }[] })[] = exact
    ? costPartRows(ev)
    : penaltyParts(ev.rules, unplaced?.before ?? 0, unplaced?.after ?? 0);
  const sumAfter = parts.reduce((n, p) => n + p.afterPoints, 0);
  const rest = exact ? 0 : (k.after ?? 0) - sumAfter;
  const pts = (n: number) => Math.round(n).toLocaleString('de-DE');
  return (
    <>
      <Summary k={k} ctx={ctx} />
      <div className={`alert alert-${rec.tone === 'bad' ? 'warning' : rec.tone === 'good' ? 'success' : 'info'}`}>
        <div className="alert-body">
          <strong>{rec.title}</strong>
          {rec.worse.length > 0 && (
            <div>
              Schlechter geworden: {rec.worse.join('; ')}.
            </div>
          )}
          {rec.better.length > 0 && <div>Besser geworden: {rec.better.join('; ')}.</div>}
          {rec.advice && <div>{rec.advice}</div>}
        </div>
      </div>
      <HBars
        title="Woraus sich die Strafpunkte zusammensetzen"
        subtitle="Verstöße × Gewicht"
        rows={parts.slice(0, 10).map((p) => ({ key: p.id, label: p.title, values: [p.beforePoints, p.afterPoints] }))}
        series={seriesBA(ctx)}
        unit="Punkte"
        format={(n) => Math.round(n).toLocaleString('de-DE')}
      />
      <ul className="small" style={{ margin: 0, paddingLeft: 'var(--space-5)' }}>
        {parts.map((p) => (
          <li key={p.id}>
            {p.id === 'rest' ? `${p.title}: ${pts(p.afterPoints)}` : `${p.title}: ${fmt(p.after)} × Gewicht ${fmt(p.weight)} = ${pts(p.afterPoints)}`}
            {Math.round(p.beforePoints) !== Math.round(p.afterPoints) ? ` (vorher ${pts(p.beforePoints)})` : ''}
            {p.top && p.top.length > 0 && (
              <span className="muted">
                {' '}
                – am meisten: {p.top.slice(0, 3).map((t) => `${t.name} ${pts(t.points)}`).join(', ')}
              </span>
            )}
          </li>
        ))}
        {exact && (
          <li>
            <strong>Zusammen: {pts(sumAfter)} Strafpunkte</strong>
          </li>
        )}
        {rest > 0.5 && <li>Übrige Feinregeln: {Math.round(rest).toLocaleString('de-DE')}</li>}
      </ul>
      <ProgressSection ctx={ctx} />
    </>
  );
}

function UnplacedList({ ctx }: { ctx: ResultContext }) {
  if (!ctx.unplaced.length) return <p className="muted">Alle Stunden sind verplant.</p>;
  return (
    <div className="table-wrap" style={{ maxHeight: '35vh' }}>
      <table className="table table-compact">
        <thead>
          <tr>
            <th scope="col">Kurs</th>
            <th scope="col">Länge</th>
            <th scope="col">Wochen</th>
          </tr>
        </thead>
        <tbody>
          {ctx.unplaced.slice(0, 200).map((u, i) => (
            <tr key={i}>
              <td>{String(u.label ?? u.course ?? u.course_id ?? '–')}</td>
              <td>{u.length ? `${String(u.length)} Std.` : u.missing ? `${String(u.missing)} Std.` : '–'}</td>
              <td>{String(u.weeks_text ?? u.reason ?? '')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SectionBody({ tile, ev, ctx }: { tile: TileKey; ev: Evaluation; ctx: ResultContext }) {
  const k = ev.kpis.find((x) => x.key === tile);
  if (k) {
    return (
      <>
        {tile === 'cost' ? <CostSection ev={ev} ctx={ctx} k={k} /> : <Summary k={k} ctx={ctx} />}
        {tile === 'class_gaps' && <EntitySection group={ev.entities.classes} noun="Klasse" nouns="Klassen" ctx={ctx} />}
        {tile === 'teacher_gaps' && <EntitySection group={ev.entities.teachers} noun="Lehrkraft" nouns="Lehrkräfte" ctx={ctx} />}
        {tile === 'site_changes' && <EntitySection group={ev.entities.teachers_sites} noun="Lehrkraft" nouns="Lehrkräfte" ctx={ctx} />}
        {tile === 'core_late' && <DistributionCharts ev={ev} ctx={ctx} core />}
        {tile === 'unplaced_hours' && <UnplacedList ctx={ctx} />}
        {(tile === 'conflicts' || tile === 'unplaced_hours' || tile === 'core_late') && (
          <HBars title={k.label} rows={[{ key: k.key, label: k.label, values: [k.before ?? 0, k.after ?? 0] }]} series={seriesBA(ctx)} unit={k.unit} />
        )}
      </>
    );
  }
  if (tile === 'moves') return <MovesSection ev={ev} ctx={ctx} />;
  if (tile === 'distribution') return <DistributionCharts ev={ev} ctx={ctx} />;
  if (tile === 'rules') return <RulesSection ev={ev} ctx={ctx} />;
  if (tile === 'progress') return <ProgressSection ctx={ctx} />;
  if (tile === 'hints')
    return ev.hints.length ? (
      <ul className="warning-list small">
        {ev.hints.map((h, i) => (
          <li key={i}>{h.text}</li>
        ))}
      </ul>
    ) : (
      <p className="muted">Keine Hinweise.</p>
    );
  return null;
}

function Tile({ id, value, label, note, tone, help, onOpen }: { id: string; value: string; label: string; note?: string; tone?: 'good' | 'bad'; help: string; onOpen: () => void }) {
  return (
    <div className={`kpi report-tile${tone ? ` ${tone}` : ''}`}>
      <button type="button" className="report-tile-open" aria-label={`${label}: ${value}${note ? `, ${note}` : ''} – Grafiken öffnen`} onClick={onOpen} data-tile={id}>
        <span className="kpi-value">{value}</span>
        <span className="kpi-label">{label}</span>
        {note && <span className="kpi-unit">{note}</span>}
      </button>
      <span className="report-tile-help">
        <HelpTip label={`Erklärung: ${label}`}>{help}</HelpTip>
      </span>
    </div>
  );
}

/** Kacheln der Auswertung; ein Klick öffnet die Grafiken dahinter. */
export function ResultTiles({ ev, ctx, initialOpen }: { ev: Evaluation; ctx: ResultContext; initialOpen?: string }) {
  const [open, setOpen] = useState<TileKey | null>(initialOpen ?? null);
  const c = ev.moves.counts;
  const hasProgress = ctx.runs.length > 0 || ctx.trace.length > 1;
  const title = (key: string): string => ev.kpis.find((k) => k.key === key)?.label ?? { moves: 'Verschobene Blöcke', distribution: 'Verteilung', rules: 'Ziele und Regeln', progress: 'Verlauf der Optimierung', hints: 'Hinweise' }[key] ?? key;
  const extras: { id: string; value: string; label: string; note?: string }[] = [
    { id: 'moves', value: String(movedTotal(c)), label: 'Verschobene Blöcke', note: `von ${c.total_before}` },
    { id: 'distribution', value: `${ev.distribution.days.length} Tage`, label: 'Verteilung', note: 'je Tag und Stunde' },
    { id: 'rules', value: String(ev.rules.length), label: 'Ziele und Regeln', note: 'mit Gewicht' },
    ...(hasProgress ? [{ id: 'progress', value: ctx.runs.length ? plural(ctx.runs.length, 'Lauf', 'Läufe') : 'Verlauf', label: 'Verlauf der Optimierung', note: 'Strafpunkte über die Zeit' }] : []),
    { id: 'hints', value: String(ev.hints.length), label: ev.hints.length === 1 ? 'Hinweis' : 'Hinweise' },
  ];
  return (
    <>
      <div className="stats gr-tiles">
        {ev.kpis.map((k) => {
          const v = verdict(k.delta);
          return (
            <Tile
              key={k.key}
              id={k.key}
              value={beforeAfter(k)}
              label={k.label}
              note={v === 'gleich' ? `${k.unit}, unverändert` : `${k.unit}, ${v}`}
              tone={v === 'besser' ? 'good' : v === 'schlechter' ? 'bad' : undefined}
              help={KPI_HELP[k.key] ?? ''}
              onOpen={() => setOpen(k.key)}
            />
          );
        })}
        {extras.map((x) => (
          <Tile key={x.id} id={x.id} value={x.value} label={x.label} note={x.note} help={EXTRA_HELP[x.id] ?? ''} onOpen={() => setOpen(x.id)} />
        ))}
      </div>
      {open && (
        <Modal
          title={
            open === 'cost' ? (
              <>
                Strafpunkte (niedriger = besser) <HelpTip label="Erklärung: Strafpunkte">Summe der gewichteten Regelverstöße aus „Prioritäten & Regeln“.</HelpTip>
              </>
            ) : (
              title(open)
            )
          }
          onClose={() => setOpen(null)}
          size="lg"
        >
          <div className="stack">
            <SectionBody tile={open} ev={ev} ctx={ctx} />
          </div>
        </Modal>
      )}
    </>
  );
}

