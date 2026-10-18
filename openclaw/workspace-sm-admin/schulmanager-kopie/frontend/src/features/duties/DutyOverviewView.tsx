/**
 * Pausenaufsichten lesbar: Tag → Pause → Standort → Bereich → Namen. Dazu je Lehrkraft, wo sie an dem Tag unterrichtet
 * (Standort), ob die Aufsicht dazu passt, und – bei Abwesenheit oder Standortwechsel – der automatische Ersatz.
 * Handy: Tageslisten; PC: zusätzlich die Wochentabelle (Bereich × Tag, je Pause).
 */
import { useMemo } from 'react';
import type { DutyOverview, DutyOverviewBreak, DutyOverviewCell, DutyOverviewDay, DutyOverviewRow } from '../../api/types';
import { DayPeriodGrid, type GridDay, type GridRow } from '../../components/grid/DayPeriodGrid';
import { useIndex } from '../../hooks/useCollection';
import { todayISO, WEEKDAYS, WEEKDAYS_SHORT } from '../../lib/dates';
import { sortBy } from '../../lib/format';

export interface DutyPick {
  dutyId?: string;
  area: string;
  day: number;
  breakIndex: number;
  label: string;
}

interface Common {
  myId?: string | null;
  onlyMine: boolean;
  canEdit: boolean;
  site: string;
  onPick: (p: DutyPick) => void;
}

export const STATUS_TEXT: Record<DutyOverviewRow['status'], string> = {
  ok: 'passt',
  hinweis: 'Hinweis',
  vertreten: 'Ersatz gefunden',
  konflikt: 'Konflikt – kein Ersatz',
  offen: 'offen',
};
const STATUS_BADGE: Record<DutyOverviewRow['status'], string> = {
  ok: 'badge-success',
  hinweis: 'badge-info',
  vertreten: 'badge-warning',
  konflikt: 'badge-danger',
  offen: 'badge-danger',
};

function useSiteNames(): (id: string) => string {
  const sites = useIndex('sites');
  return (id) => sites.get(id)?.name ?? id;
}

function rowVisible(r: DutyOverviewRow, c: Common): boolean {
  return !c.onlyMine || r.teacher === c.myId || r.substitute === c.myId;
}

function dutyLabel(cell: DutyOverviewCell, day: DutyOverviewDay, brk: DutyOverviewBreak): string {
  return `${cell.area_name}, ${WEEKDAYS[day.weekday]}, ${brk.name}`;
}

function PersonLine({ row, cell, day, brk, c }: { row: DutyOverviewRow; cell: DutyOverviewCell; day: DutyOverviewDay; brk: DutyOverviewBreak; c: Common }) {
  const siteName = useSiteNames();
  const label = dutyLabel(cell, day, brk);
  const mine = !!c.myId && (row.teacher === c.myId || row.substitute === c.myId);
  const body = (
    <>
      <span className="duty-name">{row.teacher ? row.teacher_name : 'noch niemand eingeteilt'}</span>
      {row.teacher && row.sites_today.length > 0 && (
        <span className="duty-where small muted">
          heute {row.sites_today.map(siteName).join(' und ')}
          {row.sites_today.length > 1 ? ' (wechselt)' : ''}
        </span>
      )}
      {row.status !== 'ok' && <span className={`badge ${STATUS_BADGE[row.status]}`}>{STATUS_TEXT[row.status]}</span>}
    </>
  );
  return (
    <li className={`duty-person status-${row.status}${mine ? ' mine' : ''}`}>
      {c.canEdit ? (
        <button
          type="button"
          className="duty-person-btn"
          onClick={() => c.onPick({ dutyId: row.duty_id, area: cell.area, day: day.weekday, breakIndex: brk.index, label })}
          aria-label={`${label}: ${row.teacher_name || 'offen'} – ändern`}
        >
          {body}
        </button>
      ) : (
        <div className="duty-person-btn">{body}</div>
      )}
      {row.note && row.status !== 'ok' && <div className="small muted duty-note">{row.note}</div>}
      {row.substitute && (
        <div className="small duty-sub">
          Ersatz: <strong>{row.substitute_name}</strong>
          {row.substitute_reason ? <span className="muted"> ({row.substitute_reason})</span> : null}
        </div>
      )}
    </li>
  );
}

function CellBlock({ cell, day, brk, c }: { cell: DutyOverviewCell; day: DutyOverviewDay; brk: DutyOverviewBreak; c: Common }) {
  const rows = cell.duties.filter((r) => rowVisible(r, c));
  if (c.onlyMine && rows.length === 0) return null;
  return (
    <div className="duty-area">
      <div className="duty-area-head">
        <strong>{cell.area_name}</strong>
        <span className="small muted">{cell.needed} benötigt</span>
        {cell.missing > 0 && !c.onlyMine && <span className="badge badge-danger">{cell.missing} offen</span>}
      </div>
      <ul className="list-plain duty-people">
        {rows.map((r) => (
          <PersonLine key={r.duty_id} row={r} cell={cell} day={day} brk={brk} c={c} />
        ))}
      </ul>
      {c.canEdit && !c.onlyMine && cell.missing > cell.duties.filter((r) => !r.teacher).length && (
        <button type="button" className="btn btn-sm" onClick={() => c.onPick({ area: cell.area, day: day.weekday, breakIndex: brk.index, label: dutyLabel(cell, day, brk) })}>
          + Aufsicht hinzufügen
        </button>
      )}
    </div>
  );
}

function bySite(cells: DutyOverviewCell[], site: string): [string, DutyOverviewCell[]][] {
  const m = new Map<string, DutyOverviewCell[]>();
  for (const cell of cells) {
    if (site && cell.site !== site) continue;
    const l = m.get(cell.site) ?? [];
    l.push(cell);
    m.set(cell.site, l);
  }
  return [...m.entries()];
}

function DayList({ day, c }: { day: DutyOverviewDay; c: Common }) {
  const siteName = useSiteNames();
  if (!day.open) return <p className="muted">{day.reason ? `Kein Schultag: ${day.reason}` : 'Kein Schultag.'}</p>;
  if (day.breaks.length === 0) return <p className="muted">An diesem Tag gibt es keine Pausen mit Aufsichtsbedarf.</p>;
  return (
    <div className="stack">
      {day.breaks.map((brk) => {
        const groups = bySite(brk.cells, c.site);
        if (groups.length === 0) return null;
        return (
          <section key={brk.index} className="card duty-break" aria-label={brk.name}>
            <h3>
              {brk.name}
              {brk.time ? <span className="muted small"> · ab {brk.time} Uhr</span> : null}
              <span className="muted small"> · nach der {brk.after + 1}. Stunde</span>
            </h3>
            {groups.map(([site, cells]) => (
              <div key={site || '-'} className="duty-site">
                {(groups.length > 1 || site) && <h4>{site ? siteName(site) : 'ohne Standort'}</h4>}
                {cells.map((cell) => (
                  <CellBlock key={cell.area} cell={cell} day={day} brk={brk} c={c} />
                ))}
              </div>
            ))}
          </section>
        );
      })}
    </div>
  );
}

/** Wochentabelle (PC): Zeilen = Pause · Bereich, Spalten = Tage. */
function WeekTable({ ov, c }: { ov: DutyOverview; c: Common }) {
  const siteName = useSiteNames();
  const days = ov.days.filter((d) => d.open);
  const rows = useMemo(() => {
    const m = new Map<string, { brk: DutyOverviewBreak; cell: DutyOverviewCell }>();
    for (const d of days)
      for (const b of d.breaks)
        for (const cell of b.cells) {
          if (c.site && cell.site !== c.site) continue;
          const k = `${String(b.index).padStart(2, '0')}|${cell.site}|${cell.area}`;
          if (!m.has(k)) m.set(k, { brk: b, cell });
        }
    return sortBy([...m.entries()], ([k]) => k).map(([k, v]) => ({ key: k, ...v }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ov, c.site]);
  if (rows.length === 0) return <p className="muted">Keine Aufsichten in dieser Woche.</p>;
  const gridDays: GridDay[] = days.map((d) => ({
    key: d.date,
    name: WEEKDAYS[d.weekday] ?? String(d.weekday + 1),
    short: WEEKDAYS_SHORT[d.weekday] ?? String(d.weekday + 1),
    date: `${d.date.slice(8, 10)}.${d.date.slice(5, 7)}.`,
    today: d.date === todayISO(),
  }));
  const gridRows: GridRow[] = rows.map(({ key, brk, cell }, i) => ({
    key,
    label: cell.area_name,
    time: cell.site ? siteName(cell.site) : '',
    heading: i === 0 || rows[i - 1]!.brk.index !== brk.index ? `${brk.name}${brk.time ? ` · ab ${brk.time} Uhr` : ''}` : undefined,
  }));
  return (
    <DayPeriodGrid
      days={gridDays}
      rows={gridRows}
      label="Aufsichten der Woche"
      corner="Pause / Bereich"
      minCol="7rem"
      minWidth={150 + 112 * days.length}
      compact
      cell={(di, ri) => {
        const d = days[di]!;
        const { brk, cell } = rows[ri]!;
        const dBrk = d.breaks.find((b) => b.index === brk.index);
        const dc = dBrk?.cells.find((x) => x.area === cell.area);
        if (!dBrk || !dc) return { tone: 'muted', title: 'keine Pause', content: <span className="duty-none" aria-label="keine Pause">–</span> };
        const list = dc.duties.filter((r) => rowVisible(r, c));
        const label = dutyLabel(dc, d, dBrk);
        return {
          content: (
            <div className="duty-wcell">
              {list.map((r) => {
                const who = r.substitute ? r.substitute_name : r.teacher ? r.teacher_name : 'offen';
                const mine = !!c.myId && (r.teacher === c.myId || r.substitute === c.myId);
                const cls = `duty-chip status-${r.status}${mine ? ' mine' : ''}`;
                const inner = (
                  <>
                    {r.substitute ? <s className="muted">{r.teacher_name}</s> : null} {who}
                    {r.status !== 'ok' && r.status !== 'offen' && <span className="xsmall"> · {STATUS_TEXT[r.status]}</span>}
                    {r.note && r.status !== 'ok' ? <span className="xsmall muted"> ({r.note})</span> : null}
                  </>
                );
                return c.canEdit ? (
                  <button
                    key={r.duty_id}
                    type="button"
                    className={cls}
                    onClick={() => c.onPick({ dutyId: r.duty_id, area: cell.area, day: d.weekday, breakIndex: brk.index, label })}
                    aria-label={`${label}: ${who} – ändern`}
                  >
                    {inner}
                  </button>
                ) : (
                  <div key={r.duty_id} className={cls}>
                    {inner}
                  </div>
                );
              })}
              {c.canEdit && !c.onlyMine && dc.missing > dc.duties.filter((r) => !r.teacher).length && (
                <button type="button" className="duty-chip status-offen" onClick={() => c.onPick({ area: cell.area, day: d.weekday, breakIndex: brk.index, label })}>
                  + offen
                </button>
              )}
            </div>
          ),
        };
      }}
    />
  );
}

export function DutyOverviewView({ ov, mode, day, ...c }: Common & { ov: DutyOverview; mode: 'week' | 'day'; day: number }) {
  if (mode === 'week') return <WeekTable ov={ov} c={c} />;
  const d = ov.days.find((x) => x.weekday === day) ?? ov.days[0];
  if (!d) return <p className="muted">Keine Schultage in dieser Woche.</p>;
  return <DayList day={d} c={c} />;
}

/** Zähler der Woche: offene Plätze, Aufsichten mit gefundenem Ersatz, Konflikte ohne Ersatz. */
export function overviewCounts(ov: DutyOverview | undefined, site: string): { open: number; replaced: number; conflict: number } {
  let open = 0;
  let replaced = 0;
  let conflict = 0;
  for (const d of ov?.days ?? [])
    for (const b of d.breaks)
      for (const cell of b.cells) {
        if (site && cell.site !== site) continue;
        open += cell.missing;
        for (const r of cell.duties) {
          if (r.status === 'vertreten') replaced++;
          if (r.status === 'konflikt') conflict++;
        }
      }
  return { open, replaced, conflict };
}

