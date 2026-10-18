/**
 * Kalenderwoche (Stundenplan mit Datum) für Klasse, Lehrkraft, Raum oder Schüler/in – `GET /calendar/week`.
 * KW-Navigation (Vor/Zurück/Heute/Datum, aktuelle Woche vorausgewählt), Raster Tage × Stunden mit Vertretungen,
 * Entfall, Verlegungen, Ferien/Feiertagen. Klausuren und Nachschreibtermine stehen als eigener Block in ihren Stunden
 * („Klausur M statt D“); Hausaufgaben, Tests, Termine, Nachteilsausgleich und Krankmeldungen hängen als gestapelte
 * Abzeichen in der Stunde (`calendarOverlay.ts`). Im Kopf jedes Tages bleiben nur Ferienname, ganztägige Termine und
 * was sich keiner Stunde zuordnen lässt. Samstag und Sonntag werden immer angezeigt.
 */
import { useMemo, useState, type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { http } from '../../api/client';
import type { BlockedSlot, Cell, PlanState, TimetableKind, TimetableView } from '../../api/types';
import { AbbrNamesProvider } from '../../components/Abbr';
import { Icon, type IconName } from '../../components/Icon';
import { NoPlanNotice } from '../../components/PlanNotice';
import { PopButton } from '../../components/PopButton';
import { TimetableGrid, TimetableList } from '../../components/TimetableGrid';
import { ErrorBox, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { makeupsApi } from '../makeups/api';
import { useExamHints } from '../students/ExamHints';
import { examDetailLink, examTarget } from '../channels/examRoom';
import { newAttached, overlayExams, withAbsence, withEvents, withExamNotes, withHomework } from './calendarOverlay';
import { useApi } from '../../hooks/useApi';
import { useIndex, useSettings } from '../../hooks/useCollection';
import { currentSchoolDay, formatDate, todayISO, WEEKDAYS_SHORT } from '../../lib/dates';
import { NO_PLAN_SHORT, planMissing } from '../../lib/planPeriods';
import { mergeCells, STATUS_INFO, weekTitle, type SlotItem } from './logic';
import type { ClassWeekDay } from './types';
import { useFamilyChild } from '../students/useChild';
import { WeekNav } from './WeekTab';
import './classes.css';

export interface CalendarEvent {
  id: string;
  title: string;
  kind: 'termin' | 'pflicht';
  kind_label: string;
  time_from: string;
  time_to: string;
  location: string;
  note: string;
}
export interface CalendarExam {
  id: string;
  kind: 'klausur' | 'test' | 'nachschreiben';
  kind_label: string;
  title: string;
  label: string;
  subject: string;
  start: number;
  length: number;
  time: string;
  room: string | null;
  course_id?: string;
  part?: number | null;
  classes?: string[];
  teachers?: string[];
  /** nur Nachschreibtermine: die zugehörige Klausur */
  exam_id?: string;
  /** Kursraum des Kurses/Kursteils, nur wenn das Konto ihn öffnen darf */
  channel_id?: number | null;
  can_open?: boolean;
}
export interface CalendarHomework {
  item_id: number;
  channel_id: number;
  channel_title: string;
  title: string;
  due_at: string;
  time: string;
  subject: string | null;
  subject_name: string | null;
  status?: string;
  status_label?: string;
  /** Betrachter darf den Kursraum öffnen (sonst kein Link) */
  can_open?: boolean;
  created_at?: string;
  course_id?: string | null;
  part?: number | null;
  /** Fälligkeitstag (die Aufgabe liegt in der Stunde des Kurses am Fälligkeitstag bzw. davor) */
  due_date?: string;
  /** Stunde (0-basiert), an der die Aufgabe hängt; leer = keine Stunde des Kurses gefunden (Tageskopf) */
  slot?: number | null;
  /** nur für Lehrende des Kursraums: Abgaben / erwartete Abgaben */
  submitted?: number;
  expected?: number;
}
export interface CalendarAttendance {
  id: number;
  kind: string;
  kind_label: string;
  status: string;
  status_label: string;
  minutes: number | null;
  periods: number[];
  excused: boolean;
}
export interface CalendarDay extends ClassWeekDay {
  weekday_name: string;
  weekend: boolean;
  events: CalendarEvent[];
  exams: CalendarExam[];
  homework: CalendarHomework[];
  attendance?: CalendarAttendance[];
  duty: boolean;
}
export interface CalendarWeekData {
  kind: string;
  ref: string;
  week_start: string;
  week_end: string;
  iso_week: number;
  iso_year: number;
  periods: number;
  period_times: string[];
  breaks: { after: number; name: string; minutes: number }[];
  days: CalendarDay[];
  show_days: string[];
  /** nur mit Planzeiträumen: Zustand des Stundenplans dieser Woche */
  plan?: PlanState;
  names?: { teachers: Record<string, string>; rooms: Record<string, string>; classes: Record<string, string> };
}

export const calendarApi = {
  week: (kind: string, ref: string, date: string, signal?: AbortSignal) =>
    http.get<CalendarWeekData>('/calendar/week', { kind, ref, date }, { signal }),
};

const LIVE = ['substitutions', 'absences', 'overrides', 'timetable', 'classes', 'courses', 'holidays', 'events', 'exams', 'channels', 'makeups'];

type ChipKind = 'ev' | 'duty' | 'exam' | 'test' | 'hw' | 'absent';
interface Chip {
  key: string;
  kind: ChipKind;
  icon: IconName;
  /** kurze Beschriftung im Chip */
  short: string;
  /** ausführliche Zeile in der Liste („+N“) und als Tooltip */
  text: string;
  to?: string;
  done?: boolean;
}

const MAX_CHIPS = 2;

/** Alles im Tageskopf, was keiner Stunde zugeordnet ist: ganztägige Termine/Pflichttermine, HA ohne Stunde des Kurses,
 * Abwesenheiten ohne Stunde (z. B. Verspätung). */
export function dayChips(d: CalendarDay, attached: { ha: ReadonlySet<number>; exam: ReadonlySet<string>; absent: ReadonlySet<number>; event?: ReadonlySet<string> }, family: boolean, child?: string): Chip[] {
  const out: Chip[] = [];
  for (const e of d.events) {
    if (attached.event?.has(e.id)) continue;
    const time = e.time_from ? ` ${e.time_from}${e.time_to ? `–${e.time_to}` : ''}` : '';
    out.push({
      key: `e${e.id}`,
      kind: e.kind === 'pflicht' ? 'duty' : 'ev',
      icon: e.kind === 'pflicht' ? 'alert' : 'calendar',
      short: e.title,
      text: `${e.kind === 'pflicht' ? 'Pflichttermin: ' : ''}${e.title}${time}${e.location ? ` · ${e.location}` : ''}${e.note ? ` · ${e.note}` : ''}`,
    });
  }
  for (const x of d.exams) {
    if (attached.exam.has(x.id)) continue;
    const when = `${x.start + 1}.${x.length > 1 ? `–${x.start + x.length}.` : ''} Std.${x.room ? `, Raum ${x.room}` : ''}`;
    const nach = x.kind === 'nachschreiben';
    const name = nach ? x.title || 'Nachschreibtermin' : `${x.kind === 'test' ? 'Test' : 'Klausur'}: ${x.title || x.label}`;
    out.push({
      key: `x${x.id}`,
      kind: x.kind === 'test' ? 'test' : 'exam',
      icon: x.kind === 'test' ? 'edit' : 'exam',
      short: nach ? name : `${x.kind === 'test' ? 'Test' : 'Klausur'} ${x.label || x.title}`.trim(),
      text: `${name} (${when})`,
      to: examTarget(x, d.date, child),
    });
  }
  for (const h of d.homework) {
    if (attached.ha.has(h.item_id)) continue;
    const done = h.status === 'abgegeben' || h.status === 'bewertet';
    out.push({
      key: `h${h.item_id}`,
      kind: 'hw',
      icon: 'board',
      short: `HA ${h.subject_name ?? h.channel_title}`,
      text: `HA ${h.subject_name ?? h.channel_title} bis ${h.time}: ${h.title}${h.status_label ? ` – ${h.status_label}` : ''}${
        typeof h.submitted === 'number' ? ` – ${h.submitted}/${h.expected ?? '?'} abgegeben` : ''
      }`,
      to: h.can_open === false ? undefined : `/kursraeume/${h.channel_id}?tab=aufgaben&aufgabe=${h.item_id}`,
      done,
    });
  }
  for (const a of d.attendance ?? []) {
    if (attached.absent.has(a.id)) continue;
    out.push({
      key: `a${a.id}`,
      kind: 'absent',
      icon: 'medical',
      short: a.kind === 'krank' ? 'krank gemeldet' : a.kind_label,
      text: `${a.kind === 'krank' ? 'krank gemeldet' : a.kind_label}${a.kind === 'verspaetung' && a.minutes ? ` (${a.minutes} Min.)` : ''}${
        a.excused ? ' – entschuldigt' : ' – nicht entschuldigt'
      }`,
      to: !a.excused && family ? '/krankmeldungen' : undefined,
    });
  }
  return out;
}

function ChipBody({ c }: { c: Chip }) {
  return (
    <>
      <Icon name={c.icon} className="icon cal-chip-icon" />
      <span className="cal-chip-text">{c.short}</span>
    </>
  );
}

/** Tageskopf: farbige Chips mit Symbol, höchstens MAX_CHIPS sichtbar, der Rest hinter „+N“ (Antippen öffnet die Liste). */
function DayChips({ chips }: { chips: Chip[] }) {
  if (!chips.length) return null;
  const shown = chips.length > MAX_CHIPS + 1 ? chips.slice(0, MAX_CHIPS) : chips;
  const rest = chips.slice(shown.length);
  const cls = (c: Chip) => `cal-chip2 kind-${c.kind}${c.done ? ' done' : ''}`;
  return (
    <div className="cal-chips">
      {shown.map((c) =>
        c.to ? (
          <Link key={c.key} to={c.to} className={cls(c)} title={c.text}>
            <ChipBody c={c} />
          </Link>
        ) : (
          <span key={c.key} className={cls(c)} title={c.text}>
            <ChipBody c={c} />
          </span>
        ),
      )}
      {rest.length > 0 && (
        <PopButton className="cal-chip2 cal-more" label={`+${rest.length}`} ariaLabel={`Weitere Einträge des Tages: ${rest.length}`}>
          <ul className="pop-items">
            {rest.map((c) => (
              <li key={c.key} className={`kind-${c.kind}${c.done ? ' done' : ''}`}>
                <Icon name={c.icon} className="icon cal-chip-icon" />
                {c.to ? <Link to={c.to}>{c.text}</Link> : <span>{c.text}</span>}
              </li>
            ))}
          </ul>
        </PopButton>
      )}
    </div>
  );
}

/** Tag → Blöcke für das Raster: aufeinanderfolgende Stunden derselben Unterrichtsstunde (gleicher Zustand) werden
 * zu einem Block zusammengefasst (Doppelstunde). */
export function calendarCells(days: ClassWeekDay[], subjectName: (s: string) => string | undefined): Cell[] {
  const out: Cell[] = [];
  days.forEach((day, di) => {
    const items = mergeCells(day.cells).sort((a, b) => a.period - b.period);
    let prev: { cell: Cell; key: string; end: number } | null = null;
    for (const it of items) {
      const cell = toCell(it, di, day.date, subjectName);
      const key = `${it.lessonId ?? it.key}|${cell.status?.label ?? ''}|${cell.teachers.join()}|${cell.rooms.join()}`;
      if (prev && it.lessonId && prev.key === key && prev.end === it.period) {
        prev.cell.length += 1;
        prev.end += 1;
        continue;
      }
      out.push(cell);
      prev = { cell, key, end: it.period + 1 };
    }
  });
  return out;
}

function toCell(it: SlotItem, day: number, date: string, subjectName: (s: string) => string | undefined): Cell {
  const parts = it.cells;
  const first = parts[0];
  const uniq = (xs: (string | null | undefined)[]) => [...new Set(xs.filter((x): x is string => !!x))];
  const status = it.cancelled
    ? { label: it.main && it.main !== 'entfall' ? STATUS_INFO[it.main].label : 'Entfall', cancelled: true }
    : it.main
      ? { label: STATUS_INFO[it.main].label, cancelled: false }
      : undefined;
  const note = uniq(parts.map((c) => c.note)).join(' · ');
  return {
    lesson_id: `${it.lessonId ?? it.key}@${date}#${it.period}`,
    course_id: it.courseId ?? '',
    day,
    start: it.period,
    length: 1,
    weeks: [],
    subject: first.subject || (first.kind === 'aufsicht' ? 'Aufsicht' : ''),
    subject_name: subjectName(first.subject) ?? first.subject,
    color: '',
    teachers: uniq(parts.map((c) => c.teacher)),
    rooms: uniq(parts.map((c) => c.room)),
    classes: uniq(parts.flatMap((c) => c.classes)),
    label: first.subject,
    locked: false,
    parts: it.coupled ? parts.map((c, i) => ({ index: i, subject: c.subject, teacher: c.teacher, room: c.room, label: c.subject })) : [],
    status: status ? { ...status, note: note || undefined } : undefined,
  };
}

const DETAIL_PREFIX: Record<string, string> = {
  ha: 'Hausaufgabe: ',
  exam: 'Test: ',
  makeup: 'Nachschreiben: ',
  support: 'Nachteilsausgleich: ',
  missing: 'Nachschreiben nötig: ',
  event: 'Termin: ',
  duty: '',
  absent: 'Abwesenheit: ',
};

export function CalendarWeek({
  kind,
  refId,
  date,
  onDate,
  title,
  mode = 'grid',
  onPick,
  hint,
}: {
  kind: string;
  refId: string;
  date: string;
  onDate: (d: string) => void;
  title: string;
  /** Raster (Tage × Stunden) oder Liste (Tage untereinander) */
  mode?: 'grid' | 'list';
  /** zusätzlich zum Detail: Block angeklickt (z. B. Klassenleitung „findet nicht statt“) */
  onPick?: (cell: Cell, day: CalendarDay) => void;
  /** Hinweiszeile über dem Raster */
  hint?: ReactNode;
}) {
  const { data: settings } = useSettings();
  const subjects = useIndex('subjects');
  const q = useApi((signal) => calendarApi.week(kind, refId, date, signal), [kind, refId, date], { live: LIVE, keepPrevious: true });
  const data = q.data && q.data.kind === kind && q.data.ref === refId ? q.data : undefined;
  const [selected, setSelectedState] = useState<Cell | null>(null);
  const navigate = useNavigate();
  const setSelected = (c: Cell | null) => {
    // Klausur-/Test-/Nachschreib-Block: direkt in den Kursraum (ohne Zugang: Klausur-Detail), kein Detailfeld
    if (c?.exam?.to) {
      navigate(c.exam.to);
      return;
    }
    setSelectedState(c);
    const day = c ? shown[c.day] : undefined;
    if (c && day && onPick) onPick(c, day);
  };

  const shown = useMemo(() => (data ? data.days.filter((d) => data.show_days.includes(d.date)) : []), [data]);
  const fam = useFamilyChild();
  const setChild = fam.setChild;
  const user = useUser();
  const childId = kind === 'student' && user.role === 'eltern' ? refId : undefined;
  const hasExams = !!data?.days.some((d) => d.exams.length);
  const hints = useExamHints(data?.week_start ?? date, data?.week_end ?? date, kind !== 'student' && hasExams);
  const makeups = useApi((signal) => makeupsApi.list({ from: data?.week_start, to: data?.week_end }, signal), [data?.week_start, data?.week_end], {
    live: ['makeups', 'exams', 'student_absences'],
    enabled: hasExams && !!data && user.role !== 'admin',
  });
  const mkRows = makeups.data;
  const built = useMemo(() => {
    if (!data) return undefined;
    const attached = newAttached();
    const noPlan = planMissing(data.plan);
    const periods = Math.max(data.periods, ...shown.flatMap((d) => [...d.cells.map((c) => c.period + 1), ...d.exams.map((x) => x.start + Math.max(1, x.length))]));
    const blocked: BlockedSlot[] = [];
    shown.forEach((d, di) => {
      const free = !d.cells.length && !d.events.length && !d.exams.length;
      if (d.holiday && !d.cells.length) for (let p = 0; p < periods; p++) blocked.push({ day: di, period: p, note: d.holiday });
      else if (d.weekend && free) for (let p = 0; p < periods; p++) blocked.push({ day: di, period: p, note: 'Wochenende' });
      // Woche ohne gültigen Plan: Unterrichtsfelder schraffiert; Termine und Klausuren bleiben sichtbar
      else if (noPlan && !d.cells.length) for (let p = 0; p < periods; p++) blocked.push({ day: di, period: p, note: NO_PLAN_SHORT });
    });
    const subjectName = (s: string) => subjects.get(s)?.name;
    const over = overlayExams(calendarCells(shown, subjectName), shown, kind, subjectName, attached, childId);
    const support: Record<string, { name: string; summary: string }[]> = {};
    for (const [id, list] of Object.entries(hints)) support[id] = list.map((h) => ({ name: h.name, summary: h.summary }));
    const missing: Record<string, string[]> = {};
    const own: Record<string, string> = {};
    for (const r of mkRows ?? []) {
      if (r.status !== 'offen' && r.status !== 'angesetzt') continue;
      if (kind === 'student') {
        if (r.student_id !== refId) continue;
        const term = r.appointment ? `Nachschreibtermin am ${formatDate(r.appointment.date)}` : 'Nachschreiben nötig, Termin noch offen';
        own[r.exam_id] = `${term}${r.attest.missing ? ' – Attest fehlt' : ''}`;
      } else if (r.can_schedule && r.status === 'offen') (missing[r.exam_id] ??= []).push(r.student_name);
    }
    withExamNotes(over.targets, { support, missing, own });
    withHomework(over.cells, shown, attached);
    withEvents(over.cells, shown, data.period_times, attached);
    withAbsence(over.cells, shown, attached, () => {
      if (kind === 'student') setChild(refId);
    });
    const view: TimetableView = {
      kind: kind as TimetableKind,
      ref: refId,
      title,
      week_no: null,
      days: shown.map((d) => `${WEEKDAYS_SHORT[(new Date(`${d.date}T12:00:00`).getDay() + 6) % 7]} ${formatDate(d.date).slice(0, 6)}`),
      periods: Array.from({ length: periods }, (_, i) => data.period_times[i] ?? ''),
      breaks: data.breaks,
      blocked,
      cells: over.cells,
    };
    return { view, attached };
  }, [data, shown, kind, refId, title, subjects, setChild, hints, mkRows]);
  const view: TimetableView | undefined = built?.view;
  const todayIdx = shown.findIndex((d) => d.date === todayISO());
  const family = user.role === 'eltern' || user.role === 'schueler';
  const abbrNames = useMemo(() => (data?.names ? { teacher: data.names.teachers, room: data.names.rooms, class: data.names.classes } : null), [data?.names]);
  const tName = (id: string) => data?.names?.teachers[id] ?? id;
  const rName = (id: string) => data?.names?.rooms[id] ?? id;
  const wt = weekTitle(data?.week_start ?? date, 7, '');
  const header = (di: number) => {
    const d = shown[di];
    if (!d || !built) return null;
    return (
      <>
        {d.holiday && <span className="cal-holiday">{d.holiday}</span>}
        <DayChips chips={dayChips(d, built.attached, family, childId)} />
      </>
    );
  };

  return (
    <div className="stack">
      <WeekNav date={date} onChange={onDate} kw={data?.iso_week ?? wt.kw} range={wt.range} loading={q.loading} schoolDays={settings?.days ?? 5} plan={data?.plan} />
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      <NoPlanNotice plan={data?.plan} />
      {!data && q.loading && <Loading />}
      {hint}
      {view && mode === 'grid' && (
        <AbbrNamesProvider names={abbrNames}>
          <TimetableGrid
            view={view}
            week={0}
            selectedId={selected?.lesson_id ?? null}
            onSelect={setSelected}
            todayIndex={todayIdx >= 0 ? todayIdx : null}
            dayHeader={header}
            dayDividers={shown.flatMap((d, i) => (d.weekend && i > 0 && !shown[i - 1].weekend ? [i] : []))}
          />
        </AbbrNamesProvider>
      )}
      {view && mode === 'list' && (
        <AbbrNamesProvider names={abbrNames}>
          <TimetableList view={view} week={0} selectedId={selected?.lesson_id ?? null} onSelect={setSelected} dayHeader={header} />
        </AbbrNamesProvider>
      )}
      {selected && (
        <div className="card small cal-detail" role="status">
          <strong>
            {view?.days[selected.day]} · {selected.start + 1}.{selected.length > 1 ? `–${selected.start + selected.length}.` : ''} Stunde: {selected.subject_name || selected.subject}
          </strong>
          <span>
            {[
              selected.teachers.length ? `${selected.teachers.length > 1 ? 'Lehrkräfte' : 'Lehrkraft'}: ${selected.teachers.map(tName).join(', ')}` : '',
              selected.rooms.length ? `Raum: ${selected.rooms.map(rName).join(', ')}` : '',
              kind === 'teacher' || kind === 'room' ? `Klasse: ${selected.classes.map((c) => data?.names?.classes[c] ?? c).join(', ')}` : '',
            ]
              .filter(Boolean)
              .join(' · ')}
          </span>
          {(selected.links ?? []).map((l) => (
            <span key={`${l.to}|${l.kind}|${l.title ?? l.label}`}>
              {DETAIL_PREFIX[l.kind ?? 'ha']}
              {l.to ? (
                <Link to={l.to} onClick={l.onClick}>
                  {l.kind === 'absent' ? `${l.label} – ${l.title ?? 'öffnen'}` : l.title ?? 'öffnen'}
                </Link>
              ) : (
                (l.title ?? l.label)
              )}
            </span>
          ))}
          {selected.exam && selected.exam.kind !== 'nachschreiben' && (
            <span>
              <Link to={examDetailLink(selected.exam.id, shown[selected.day]?.date)}>{selected.exam.kind === 'test' ? 'Test' : 'Klausur'} – Details</Link>
            </span>
          )}
          {selected.status && (
            <span>
              <span className={`badge ${selected.status.cancelled ? 'badge-danger' : 'badge-warning'}`}>{selected.status.label}</span> {selected.status.note}
            </span>
          )}
        </div>
      )}
      {data && !planMissing(data.plan) && shown.every((d) => !d.cells.length && !d.holiday) && <p className="muted small">In dieser Woche kein Unterricht.</p>}
    </div>
  );
}

/** Wochenplan als Karte (Startseite der Schüler/innen und Eltern) mit eigener KW-Auswahl – aktuelle Woche vorausgewählt. */
export function CalendarWeekCard({ kind, refId, title, heading = 'Stundenplan' }: { kind: string; refId: string; title: string; heading?: string }) {
  const { data: settings } = useSettings();
  const [date, setDate] = useState(() => currentSchoolDay(new Date(), settings?.days ?? 5));
  return (
    <section className="card" aria-label={heading}>
      <div className="card-head">
        <h2>{heading}</h2>
      </div>
      <CalendarWeek kind={kind} refId={refId} date={date} onDate={setDate} title={title} />
    </section>
  );
}
