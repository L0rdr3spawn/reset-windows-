/**
 * Fehlzeiten-Übersicht mit Anteilen: wie viele Unterrichtsstunden gab es, wie viele davon gefehlt (Anzahl, Prozent),
 * je Fach mit Ampel zur Schul-Grenze, Häufung nach Wochentag/Stunde. Backend: `GET /absence-stats` (features_absence_stats.py).
 * Eingehängt auf der Seite „Krankmeldungen & Fehlzeiten“ (Familie je Kind, Klassenleitung je Klasse) und in der
 * Fehlzeiten-Übersicht einer Person.
 */
import { useState } from 'react';
import { Icon } from '../../components/Icon';
import { todayISO } from '../../lib/dates';
import { Link } from 'react-router-dom';
import { http } from '../../api/client';
import { DayPeriodGrid, GridLegend, type GridDay, type GridRow, type GridTone } from '../../components/grid/DayPeriodGrid';
import { HelpTip } from '../../components/HelpTip';
import { ErrorBox, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';

export type LimitState = 'none' | 'ok' | 'warn' | 'over';
export interface Counts {
  held: number;
  excused: number;
  unexcused: number;
  open: number;
  absent: number;
  percent: number;
  /** Versäumte Unterrichtszeit (Minuten, inkl. zu spät/früher gegangen) und Anteil an den Unterrichtsminuten */
  held_minutes: number;
  missed_minutes: number;
  missed_excused: number;
  missed_unexcused: number;
  missed_open: number;
  missed_percent: number;
  /** Stunden mit versäumter Zeit */
  affected: number;
  late_count: number;
  late_minutes: number;
  early_count: number;
  early_minutes: number;
}
export interface SubjectStat extends Counts {
  subject: string | null;
  name: string;
  limit_state: LimitState;
  hours_left: number | null;
}
export interface SlotStat extends Counts {
  weekday: number;
  weekday_label: string;
  period: number;
  period_label: string;
}
export interface AbsenceStatsData {
  student: { id: string; name: string; class_id: string };
  period: { key: string; label: string; from: string; to: string; counted_to: string };
  totals: Counts & { limit_state: LimitState; hours_left: number | null };
  subjects: SubjectStat[];
  slots: SlotStat[];
  weekdays: (Counts & { weekday: number; weekday_label: string })[];
  late: { count: number; minutes: number; excused: number; unexcused: number; open: number };
  early: { count: number; excused: number; unexcused: number; open: number };
  limits: { total: number; unexcused: number };
  worst_state: LimitState;
  top_subject: string | null;
  top_subject_name: string | null;
  period_minutes: number;
  hot_slots: { weekday_label: string; period_label: string; held: number; absent: number; percent: number; missed_percent: number; missed_minutes: number }[];
  notes: string[];
}
export interface ClassStatsData {
  class_id: string;
  period: { key: string; label: string; from: string; to: string };
  limits: { total: number; unexcused: number };
  students: { student_id: string; name: string; held: number; absent: number; percent: number; missed_percent: number; unexcused: number; state: LimitState; worst_subject: string | null; worst_percent: number }[];
}

export interface WeekCell {
  date: string;
  period: number;
  period_label: string;
  subject: string | null;
  subject_name: string;
  length: number;
  status: 'held' | 'cancelled' | 'upcoming';
  state: 'present' | 'partial' | 'absent' | 'none';
  /** Anwesenheit in Prozent der Stunde (100 = ganz da, 0 = gefehlt); null bei Entfall/noch nicht gehalten */
  present_percent: number | null;
  missed_minutes: number;
  labels: string[];
  bucket: 'excused' | 'unexcused' | 'open' | null;
  bucket_label: string;
}
export interface WeekData {
  student: { id: string; name: string; class_id: string };
  monday: string;
  sunday: string;
  iso_week: number;
  iso_year: number;
  prev: string;
  next: string;
  is_current: boolean;
  today: string;
  days: { date: string; weekday: number; weekday_label: string; school_day: boolean; reason: string }[];
  periods: { period: number; label: string; time: string }[];
  cells: WeekCell[];
  period_minutes: number;
}

export type PeriodKey = 'year' | 'half1' | 'half2' | 'custom';
interface PeriodQuery {
  period: PeriodKey;
  from?: string;
  to?: string;
}

export const absenceStatsApi = {
  student: (studentId: string, p: PeriodQuery, signal?: AbortSignal) =>
    http.get<AbsenceStatsData>('/absence-stats', { student_id: studentId, period: p.period, from: p.period === 'custom' ? p.from : undefined, to: p.period === 'custom' ? p.to : undefined }, { signal }),
  week: (studentId: string, week: string | undefined, signal?: AbortSignal) => http.get<WeekData>('/absence-stats/week', { student_id: studentId, week }, { signal }),
  klass: (classId: string, p: PeriodQuery, signal?: AbortSignal) =>
    http.get<ClassStatsData>('/absence-stats/class', { class_id: classId, period: p.period, from: p.period === 'custom' ? p.from : undefined, to: p.period === 'custom' ? p.to : undefined }, { signal }),
};

export const STATE_LABEL: Record<LimitState, string> = { none: '', ok: 'unter der Grenze', warn: 'nahe an der Grenze', over: 'Grenze überschritten' };
const STATE_BADGE: Record<LimitState, string> = { none: '', ok: 'badge-success', warn: 'badge-warning', over: 'badge-danger' };

export function pct(n: number): string {
  return `${n.toLocaleString('de-DE', { maximumFractionDigits: 1 })} %`;
}

/** Text „noch 2 Std. bis zur Grenze“ bzw. „3 Std. über der Grenze“ */
export function leftText(state: LimitState, left: number | null): string {
  if (state === 'none' || left === null) return '';
  if (left < 0) return `${-left} Std. über der Grenze`;
  return left === 0 ? 'Grenze erreicht' : `noch ${left} Std. bis zur Grenze`;
}

export function LimitBadge({ state, left }: { state: LimitState; left: number | null }) {
  if (state === 'none') return <span className="muted small">–</span>;
  const extra = leftText(state, left);
  return (
    <span className={`badge ${STATE_BADGE[state]}`} title={STATE_LABEL[state]}>
      <span aria-hidden="true">{state === 'ok' ? '●' : state === 'warn' ? '▲' : '■'}</span> {STATE_LABEL[state]}
      {extra ? ` – ${extra}` : ''}
    </span>
  );
}

function PeriodPicker({ value, onChange }: { value: PeriodQuery; onChange: (p: PeriodQuery) => void }) {
  return (
    <div className="toolbar">
      <div className="field">
        <label htmlFor="as-period">Zeitraum</label>
        <select id="as-period" value={value.period} onChange={(e) => onChange({ ...value, period: e.target.value as PeriodKey })}>
          <option value="year">Schuljahr</option>
          <option value="half1">1. Halbjahr (bis 31.01.)</option>
          <option value="half2">2. Halbjahr (ab 01.02.)</option>
          <option value="custom">Eigener Zeitraum</option>
        </select>
      </div>
      {value.period === 'custom' && (
        <>
          <div className="field">
            <label htmlFor="as-from">von</label>
            <input id="as-from" type="date" value={value.from ?? ''} onChange={(e) => onChange({ ...value, from: e.target.value || undefined })} />
          </div>
          <div className="field">
            <label htmlFor="as-to">bis</label>
            <input id="as-to" type="date" value={value.to ?? ''} onChange={(e) => onChange({ ...value, to: e.target.value || undefined })} />
          </div>
        </>
      )}
    </div>
  );
}

function minutesText(n: number): string {
  return `${n.toLocaleString('de-DE')} Min.`;
}

/** Tooltip einer Zelle/Gruppe: betroffene Stunden, versäumte Minuten, Aufschlüsselung und entschuldigt/unentschuldigt */
export function slotTitle(s: Counts, head: string): string {
  const parts: string[] = [];
  if (s.late_count) parts.push(`${s.late_count}× zu spät ${minutesText(s.late_minutes)}`);
  if (s.early_count) parts.push(`${s.early_count}× früher gegangen ${minutesText(s.early_minutes)}`);
  if (s.absent) parts.push(`${s.absent}× gefehlt`);
  const split = s.missed_minutes ? `; entschuldigt ${minutesText(s.missed_excused)}, unentschuldigt ${minutesText(s.missed_unexcused)}${s.missed_open ? `, offen ${minutesText(s.missed_open)}` : ''}` : '';
  return `${head}: ${s.affected} von ${s.held} Stunden betroffen · ${minutesText(s.missed_minutes)} versäumt (${pct(s.missed_percent)} der Unterrichtszeit)${parts.length ? ` (${parts.join(', ')})` : ''}${split}`;
}

const GRID_LABEL_W = 56;
const GRID_CELL_W = 64;

/** Durchschnitts-Raster: je Wochentag und Stunde die durchschnittliche **Anwesenheit** über den Zeitraum (100 % minus versäumter Anteil). */
function SlotGrid({ slots }: { slots: SlotStat[] }) {
  const dayNos = [...new Set(slots.map((s) => s.weekday))].sort();
  const periodNos = [...new Set(slots.map((s) => s.period))].sort((a, b) => a - b);
  const by = new Map(slots.map((s) => [`${s.weekday}-${s.period}`, s]));
  if (!dayNos.length) return null;
  const days: GridDay[] = dayNos.map((d) => {
    const full = slots.find((s) => s.weekday === d)?.weekday_label ?? String(d);
    return { key: d, name: full, short: full.slice(0, 2) };
  });
  const rows: GridRow[] = periodNos.map((p) => ({ key: p, label: `${p + 1}.` }));
  return (
    <DayPeriodGrid
      days={days}
      rows={rows}
      label="Durchschnittliche Anwesenheit nach Wochentag und Stunde"
      minWidth={GRID_LABEL_W + GRID_CELL_W * dayNos.length}
      minCol={`${GRID_CELL_W}px`}
      compact
      cell={(di, ri) => {
        const s = by.get(`${dayNos[di]}-${periodNos[ri]}`);
        if (!s) return { tone: 'muted' };
        const present = Math.round((100 - s.missed_percent) * 10) / 10;
        const title = `${s.weekday_label}, ${s.period_label} Stunde: durchschnittlich ${pct(present)} anwesend. ${slotTitle(s, 'Einzelheiten')}`;
        return {
          tone: s.missed_minutes ? undefined : 'free',
          heat: s.missed_minutes ? Math.min(1, s.missed_percent / 30) : undefined,
          title,
          content: (
            <span className="tt-fill" tabIndex={0} aria-label={title}>
              {s.missed_minutes ? pct(present) : <span className="muted">100 %</span>}
            </span>
          ),
        };
      }}
      legend={
        <GridLegend
          items={[
            { tone: 'free', label: '100 % anwesend' },
            { tone: 'heat', label: 'je dunkler, desto mehr versäumt' },
            { tone: 'muted', label: 'kein Unterricht' },
          ]}
        />
      }
    />
  );
}

const WEEK_CELL_W = 82;

function weekCellTone(c: WeekCell): GridTone {
  if (c.status === 'cancelled' || c.status === 'upcoming') return 'muted';
  if (c.state === 'absent') return 'bad';
  if (c.state === 'partial') return 'mid';
  return 'good';
}

/** Beschreibung einer Wochen-Zelle („Mathematik: 89 % anwesend – 5 Min. zu spät, offen“). */
export function weekCellText(c: WeekCell): string {
  if (c.status === 'cancelled') return `${c.subject_name}: Entfall (zählt nicht)`;
  if (c.status === 'upcoming') return `${c.subject_name}: noch nicht gehalten`;
  const extra = [...c.labels, ...(c.bucket_label ? [c.bucket_label] : [])].join(', ');
  return `${c.subject_name}: ${c.present_percent ?? 100} % anwesend${extra ? ` – ${extra}` : ''}`;
}

function shortDate(iso: string): string {
  return new Date(`${iso}T12:00:00`).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
}

/** Wochenansicht: je tatsächlicher Stunde Anwesenheit in % (Standard: aktuelle Woche), Antippen zeigt die Einzelheiten. */
function WeekView({ studentId }: { studentId: string }) {
  const [week, setWeek] = useState<string | undefined>(undefined);
  const [picked, setPicked] = useState<string | null>(null);
  const q = useApi((signal) => absenceStatsApi.week(studentId, week, signal), [studentId, week], {
    enabled: !!studentId,
    live: ['student_absences', 'parent_access', 'timetable'],
    keepPrevious: true,
  });
  const d = q.data;
  const go = (iso: string | undefined) => {
    setPicked(null);
    setWeek(iso);
  };
  const by = new Map((d?.cells ?? []).map((c) => [`${c.date}-${c.period}`, c]));
  const weekDays: GridDay[] = (d?.days ?? []).map((day) => ({
    key: day.date,
    name: day.weekday_label,
    short: day.weekday_label.slice(0, 2),
    date: shortDate(day.date),
    today: day.date === todayISO(),
    fill: !day.school_day && !(d?.cells ?? []).some((c) => c.date === day.date) ? <span className="xsmall">{day.reason}</span> : undefined,
  }));
  const weekRows: GridRow[] = (d?.periods ?? []).map((p) => ({ key: p.period, label: p.label, time: p.time }));
  const sel = picked && d ? by.get(picked) : undefined;
  const selDay = sel && d ? d.days.find((x) => x.date === sel.date) : undefined;
  const selTime = sel && d ? d.periods.find((x) => x.period === sel.period)?.time : '';
  return (
    <div className="stack-sm">
      <div className="date-nav" role="group" aria-label="Woche wählen">
        <button type="button" className="btn btn-icon" aria-label="Vorherige Woche" onClick={() => go(d?.prev)}>
          <Icon name="chevronLeft" />
        </button>
        <span className="date-label" aria-live="polite">{d ? `KW ${d.iso_week}: ${shortDate(d.monday)} – ${new Date(`${d.sunday}T12:00:00`).toLocaleDateString('de-DE')}` : '…'}</span>
        <button type="button" className="btn btn-icon" aria-label="Nächste Woche" onClick={() => go(d?.next)}>
          <Icon name="chevronRight" />
        </button>
        <button type="button" className="btn btn-sm" disabled={!week || !!d?.is_current} onClick={() => go(undefined)}>
          Diese Woche
        </button>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!d && q.loading && <Loading />}
      {d && (
        <>
          <DayPeriodGrid
            days={weekDays}
            rows={weekRows}
            label={`Anwesenheit je Stunde, Woche ab ${shortDate(d.monday)}`}
            minWidth={GRID_LABEL_W + WEEK_CELL_W * d.days.length}
            minCol={`${WEEK_CELL_W}px`}
            cell={(di, ri) => {
              const day = d.days[di]!;
              const p = d.periods[ri]!;
              const c = by.get(`${day.date}-${p.period}`);
              if (!c) return { tone: 'muted' };
              const text = weekCellText(c);
              const first = c.labels[0] ?? '';
              const id = `${c.date}-${c.period}`;
              return {
                tone: weekCellTone(c),
                selected: picked === id,
                content: (
                  <button
                    type="button"
                    className="tt-fill"
                    aria-pressed={picked === id}
                    title={text}
                    aria-label={`${day.weekday_label} ${shortDate(day.date)}, ${p.label} Stunde, ${text}`}
                    onClick={() => setPicked(picked === id ? null : id)}
                  >
                    <span className="xsmall muted clip">{c.subject_name}</span>
                    <strong>{c.present_percent === null ? (c.status === 'cancelled' ? 'Entfall' : '–') : `${c.present_percent} %`}</strong>
                    {first && c.status === 'held' && <span className="xsmall clip">{first}</span>}
                  </button>
                ),
              };
            }}
            legend={
              <GridLegend
                items={[
                  { tone: 'good', label: 'ganz da' },
                  { tone: 'mid', label: 'teilweise (zu spät, früher gegangen)' },
                  { tone: 'bad', label: 'gefehlt' },
                  { tone: 'muted', label: 'kein Unterricht, Entfall, noch nicht gehalten' },
                ]}
              />
            }
          />
          {!d.periods.length && <p className="muted small">In dieser Woche gibt es keinen Unterricht.</p>}
          {sel ? (
            <p className="small" role="status">
              <strong>
                {selDay?.weekday_label}, {new Date(`${sel.date}T12:00:00`).toLocaleDateString('de-DE')} · {sel.period_label} Stunde{selTime ? ` (${selTime})` : ''}
              </strong>
              <br />
              {weekCellText(sel)}
              {sel.status === 'held' && sel.missed_minutes > 0 ? ` · ${minutesText(sel.missed_minutes)} von ${minutesText(sel.length)} versäumt` : ''}
            </p>
          ) : null}
          {d.days.filter((x) => !x.school_day && x.reason).length > 0 && (
            <p className="xsmall muted">{d.days.filter((x) => !x.school_day && x.reason).map((x) => `${x.weekday_label.slice(0, 2)} ${shortDate(x.date)}: ${x.reason}`).join(' · ')}</p>
          )}
        </>
      )}
    </div>
  );
}

export function AbsenceStats({ studentId, showName }: { studentId: string; showName?: boolean }) {
  const [p, setP] = useState<PeriodQuery>({ period: 'year' });
  const [view, setView] = useState<'week' | 'avg'>('week');
  const q = useApi((signal) => absenceStatsApi.student(studentId, p, signal), [studentId, p.period, p.from, p.to], {
    enabled: !!studentId && (p.period !== 'custom' || !!p.from),
    live: ['student_absences', 'parent_access', 'timetable'],
  });
  const d = q.data;
  const limited = !!d && (d.limits.total > 0 || d.limits.unexcused > 0);
  return (
    <section className="card absence-stats" aria-labelledby="as-h">
      <div className="card-head">
        <h2 id="as-h" className="with-help">
          Fehlzeiten im Überblick{showName && d ? ` – ${d.student.name}` : ''}
          <HelpTip>
            Gezählt werden die Unterrichtsstunden, die laut Plan bis heute stattgefunden haben (ohne Ferien und Entfall, mit Vertretungen), und die Stunden, in denen laut Krankmeldung oder Klassenbuch gefehlt wurde. Zu spät kommen und früher gehen zählen nicht als ganze Fehlstunde, aber mit den versäumten Minuten in die „versäumte Zeit“ (Anteil an den Unterrichtsminuten). Die Grenzen-Ampel richtet sich nach dieser Zeit. Das Raster zeigt die Anwesenheit: je tatsächlicher Stunde einer Woche, wie viel Prozent der Stunde da waren (100 % ganz da, 0 % gefehlt, dazwischen z. B. bei „5 Min. zu spät“), oder als Durchschnitt über den Zeitraum je Wochentag und Stunde. Antippen zeigt die Einzelheiten. Grau: kein Unterricht, Entfall oder noch nicht gehalten.
          </HelpTip>
        </h2>
        <button type="button" className="btn btn-sm no-print" onClick={() => window.print()}>
          Drucken
        </button>
      </div>
      <PeriodPicker value={p} onChange={setP} />
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {d && (
        <div className="stack">
          <p>
            <strong>
              {d.totals.absent} von {d.totals.held} Stunden gefehlt ({pct(d.totals.percent)})
            </strong>{' '}
            <span className="muted small">
              versäumte Zeit {minutesText(d.totals.missed_minutes)} von {minutesText(d.totals.held_minutes)} ({pct(d.totals.missed_percent)}) · {d.period.label}, bis {new Date(d.period.counted_to).toLocaleDateString('de-DE')} – davon entschuldigt {d.totals.excused}, unentschuldigt {d.totals.unexcused}, offen {d.totals.open}
            </span>
          </p>
          {(d.late.count > 0 || d.early.count > 0) && (
            <p className="small">
              Zu spät: {d.late.count}× ({d.late.minutes} Min.) · Früher gegangen: {d.early.count}×
            </p>
          )}
          {limited && (
            <p className="small">
              Zulässige Fehlzeit je Fach: {pct(d.limits.total)}
              {d.limits.unexcused > 0 ? `, unentschuldigt ${pct(d.limits.unexcused)}` : ''}. Gesamt: <LimitBadge state={d.totals.limit_state} left={d.totals.hours_left} />
            </p>
          )}
          {d.top_subject_name && (
            <p className="small">
              Höchster Anteil: <strong>{d.top_subject_name}</strong> ({pct(d.subjects.find((s) => s.subject === d.top_subject)?.missed_percent ?? 0)} der Unterrichtszeit).
              {d.hot_slots.length > 0 &&
                ` Besonders viele Fehlzeiten: ${d.hot_slots.map((h) => `${h.weekday_label}, ${h.period_label} Stunde (${pct(h.missed_percent)})`).join('; ')}.`}
            </p>
          )}
          <div style={{ overflowX: 'auto' }}>
            <table className="table" aria-label="Fehlzeiten je Fach">
              <thead>
                <tr>
                  <th scope="col">Fach</th>
                  <th scope="col" className="num">
                    Stunden
                  </th>
                  <th scope="col" className="num">
                    Std. gefehlt
                  </th>
                  <th scope="col" className="num">
                    Anteil gefehlt
                  </th>
                  <th scope="col" className="num">
                    Zeit versäumt
                  </th>
                  <th scope="col" className="num">
                    entsch. / unentsch. / offen
                  </th>
                  {limited ? <th scope="col">Grenze</th> : null}
                </tr>
              </thead>
              <tbody>
                {d.subjects.map((s) => (
                  <tr key={s.subject ?? '-'}>
                    <th scope="row">
                      {s.name}
                      {s.subject === d.top_subject ? ' ★' : ''}
                    </th>
                    <td className="num">{s.held}</td>
                    <td className="num">{s.absent}</td>
                    <td className="num">{pct(s.percent)}</td>
                    <td className="num" title={slotTitle(s, s.name)}>
                      {pct(s.missed_percent)}
                    </td>
                    <td className="num">
                      {s.excused} / {s.unexcused} / {s.open}
                    </td>
                    {limited ? (
                      <td>
                        <LimitBadge state={s.limit_state} left={s.hours_left} />
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h3>Anwesenheit nach Stunden</h3>
          <div className="row" role="group" aria-label="Ansicht der Anwesenheit">
            <button type="button" className={`btn btn-sm${view === 'week' ? ' btn-primary' : ''}`} aria-pressed={view === 'week'} onClick={() => setView('week')}>
              Woche (je Stunde)
            </button>
            <button type="button" className={`btn btn-sm${view === 'avg' ? ' btn-primary' : ''}`} aria-pressed={view === 'avg'} onClick={() => setView('avg')}>
              Durchschnitt im Zeitraum
            </button>
          </div>
          {view === 'week' ? (
            <WeekView studentId={studentId} />
          ) : (
            <>
              <p className="xsmall muted">Durchschnittliche Anwesenheit im Zeitraum ({d.period.label}).</p>
              <SlotGrid slots={d.slots} />
            </>
          )}
        </div>
      )}
    </section>
  );
}

/** Klassenleitung/Verwaltung: wer ist nahe an oder über der Grenze (sortiert nach Ampel, dann Anteil). */
export function ClassAbsenceStats({ classId }: { classId: string }) {
  const [p, setP] = useState<PeriodQuery>({ period: 'year' });
  const q = useApi((signal) => absenceStatsApi.klass(classId, p, signal), [classId, p.period, p.from, p.to], {
    enabled: !!classId && (p.period !== 'custom' || !!p.from),
    live: ['student_absences'],
  });
  const d = q.data;
  const limited = !!d && (d.limits.total > 0 || d.limits.unexcused > 0);
  return (
    <section className="card" aria-labelledby="cas-h">
      <h2 id="cas-h" className="with-help">
        Fehlzeiten der Klasse {classId}
        <HelpTip>Anteil der gefehlten an den stattgefundenen Stunden je Person; „Zeit“ ist der Anteil der versäumten Unterrichtsminuten (mit Verspätungen). Die Ampel richtet sich nach der Schul-Grenze (Einstellungen, Krankmeldungen), gerechnet in Zeit, und dem Fach mit dem schlechtesten Wert.</HelpTip>
      </h2>
      <PeriodPicker value={p} onChange={setP} />
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {d && (
        <div style={{ overflowX: 'auto' }}>
          <table className="table" aria-label="Fehlzeiten der Klasse">
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col" className="num">
                  gefehlt
                </th>
                <th scope="col" className="num">
                  Anteil
                </th>
                <th scope="col" className="num">
                  Zeit
                </th>
                <th scope="col" className="num">
                  unentsch.
                </th>
                <th scope="col">Auffälligstes Fach</th>
                {limited ? <th scope="col">Grenze</th> : null}
              </tr>
            </thead>
            <tbody>
              {d.students.map((s) => (
                <tr key={s.student_id}>
                  <th scope="row">
                    <Link to={`/fehlzeiten/${encodeURIComponent(s.student_id)}`}>{s.name}</Link>
                  </th>
                  <td className="num">
                    {s.absent}/{s.held}
                  </td>
                  <td className="num">{pct(s.percent)}</td>
                  <td className="num">{pct(s.missed_percent)}</td>
                  <td className="num">{s.unexcused}</td>
                  <td>{s.worst_subject ? `${s.worst_subject} (${pct(s.worst_percent)})` : '–'}</td>
                  {limited ? (
                    <td>
                      <LimitBadge state={s.state} left={null} />
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
