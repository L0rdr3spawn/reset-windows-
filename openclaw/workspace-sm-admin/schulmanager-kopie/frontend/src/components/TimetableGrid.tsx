import { useMemo, useState, type CSSProperties, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import type { Cell, DayInfo, MoveOption, TimetableKind, TimetableView } from '../api/types';
import { useOptionalUser } from '../context/AuthContext';
import { can } from '../lib/permissions';
import { subjectColor, textOn } from '../lib/colors';
import { formatDayMonth, WEEKDAYS, WEEKDAYS_SHORT } from '../lib/dates';
import { blockedMap, cellsByDay, findOption, isCoupled, layoutTimetable, normalizePeriods, periodRangeLabel, slotState, weekCells } from '../lib/grid';
import { describeSelection, isOffDay } from '../lib/weeks';
import { AbbrList, RoomAbbr, SubjectAbbr, TeacherAbbr } from './Abbr';
import { CellBadges } from './CellBadges';
import { DayPeriodGrid, type GridCell, type GridDay, type GridRow } from './grid/DayPeriodGrid';
import { Icon } from './Icon';
import { PopButton } from './PopButton';
import './weeks.css';

export interface DragState {
  cell: Cell;
  options: MoveOption[] | null;
}

/** Nebenzeilen je nach Ansicht (Kürzel mit Sprechblase; im Rasterfeld „passiv“: Antippen wählt die Stunde, Langdruck zeigt die Namen). */
function cellLines(c: Cell, kind: TimetableKind): ReactNode[] {
  const classes = <AbbrList kind="class" ids={c.classes} passive />;
  const teachers = <AbbrList kind="teacher" ids={c.teachers} passive />;
  const rooms = <AbbrList kind="room" ids={c.rooms} passive />;
  const has = { classes: c.classes.length > 0, teachers: c.teachers.length > 0, rooms: c.rooms.length > 0 };
  const pick = (a: boolean, node: ReactNode) => (a ? node : null);
  if (kind === 'teacher') return [pick(has.classes, classes), pick(has.rooms, rooms)];
  if (kind === 'room') return [pick(has.classes, classes), pick(has.teachers, teachers)];
  return [pick(has.teachers, teachers), pick(has.rooms, rooms)];
}

/** Farbklasse (.k-*) einer Statusbeschriftung – Rahmen und Abzeichen eines geänderten Blocks nutzen dieselbe Palette wie der Vertretungsplan. */
export function statusKindClass(label: string | undefined, cancelled?: boolean): string {
  const l = (label ?? '').toLowerCase();
  if (cancelled || l.startsWith('entf')) return 'k-entfall';
  if (l.startsWith('mitbetreu')) return 'k-mitbetreuung';
  if (l.startsWith('betreu')) return 'k-betreuung';
  if (l.startsWith('vertret')) return 'k-vertretung';
  if (l.startsWith('verleg')) return 'k-verlegung';
  if (l.startsWith('raum')) return 'k-raum';
  if (l.includes('abwesend')) return 'k-abwesend';
  if (l.startsWith('klausur')) return 'k-klausur';
  if (l.startsWith('aufsicht')) return 'k-aufsicht';
  return 'k-sonst';
}

/** Wochen einer Zelle („Woche 1, 3“, „jede 3. Woche ab Woche 2“) oder leer bei „jede Woche“. */
export function cellWeeksText(c: Pick<Cell, 'weeks' | 'weeks_text' | 'rhythm'>): string {
  const text = c.weeks_text ?? describeSelection({ weeks: c.weeks, rhythm: c.rhythm });
  return text === 'jede Woche' ? '' : text;
}

/**
 * Kopf einer Tagesspalte: Name (lang + Kürzel), Datum, Feiertag/Ferien; Tage ohne Unterricht abgeblendet.
 * Liefert der Server den Tag schon mit Datum („Mo 12.10.“), wird er zerlegt – so sieht der Kopf in jeder Ansicht gleich aus.
 */
export function dayHead(d: number, view: Pick<TimetableView, 'days' | 'day_info'>): { name: string; short: string; date: string; holiday: string; off: boolean } {
  const info: DayInfo | undefined = view.day_info?.[d];
  const raw = view.days[d] ?? info?.name ?? `Tag ${d + 1}`;
  const m = /^(\S+?)\.?\s+(\d{1,2}\.\d{1,2}\.?)$/.exec(raw);
  const word = m?.[1] ?? raw;
  const idx = WEEKDAYS_SHORT.indexOf(word);
  const name = idx >= 0 ? (WEEKDAYS[idx] ?? word) : word;
  const short = idx >= 0 ? word : (WEEKDAYS_SHORT[WEEKDAYS.indexOf(word)] ?? WEEKDAYS_SHORT[d] ?? word);
  return { name, short, date: info?.date ? formatDayMonth(info.date) : (m?.[2] ?? ''), holiday: info?.holiday ?? '', off: isOffDay(info) };
}

export function cellAriaLabel(c: Cell, days: string[]): string {
  const day = days[c.day] ?? `Tag ${c.day + 1}`;
  const wt = cellWeeksText(c);
  const weeks = wt ? ` (${wt})` : '';
  const parts = isCoupled(c) ? `, Kopplung mit ${c.parts.length} Kursen` : '';
  const status = c.status ? `; ${c.status.label}${c.status.note ? ` (${c.status.note})` : ''}` : '';
  return `${day}, ${periodRangeLabel(c.start, c.length)} Stunde: ${c.subject_name || c.subject}${weeks}; Lehrkraft ${c.teachers.join(', ') || '–'}; Raum ${
    c.rooms.join(', ') || '–'
  }; Klassen ${c.classes.join(', ')}${parts}${c.locked ? ', fixiert' : ''}${status}`;
}

/** Nach welchen Stunden eine Pause liegt: eingestellte Pausen plus jede echte Lücke zwischen zwei Stundenbeginnen
 * (länger als der übliche Abstand) – so stehen die dicken Linien an allen Pausen, auch am Nachmittag. */
export function breakSlots(breaks: readonly { after: number }[] | null | undefined, periods: readonly { time: string }[]): Set<number> {
  const out = new Set((breaks ?? []).map((b) => b.after));
  const mins = periods.map((p) => {
    const m = /^(\d{1,2}):(\d{2})/.exec(p.time ?? '');
    return m ? Number(m[1]) * 60 + Number(m[2]) : null;
  });
  const diffs: number[] = [];
  for (let i = 0; i + 1 < mins.length; i++) {
    const a = mins[i];
    const b = mins[i + 1];
    if (a !== null && b !== null && b > a) diffs.push(b - a);
  }
  if (!diffs.length) return out;
  const usual = Math.min(...diffs);
  for (let i = 0; i + 1 < mins.length; i++) {
    const a = mins[i];
    const b = mins[i + 1];
    if (a !== null && b !== null && b - a > usual + 4) out.add(i);
  }
  return out;
}

export function TimetableGrid({
  view,
  editable,
  selectedId,
  onSelect,
  onMove,
  loadOptions,
  compact,
  todayIndex,
  onDragInfo,
  dayHeader,
  dayDividers,
}: {
  view: TimetableView;
  /** wird nicht mehr gebraucht: die Woche steht in `view` (ältere Server: `view.week`) */
  week?: number;
  editable?: boolean;
  selectedId?: string | null;
  onSelect?: (c: Cell | null) => void;
  onMove?: (c: Cell, day: number, start: number, option: MoveOption | undefined) => void;
  loadOptions?: (lessonId: string) => Promise<MoveOption[]>;
  compact?: boolean;
  todayIndex?: number | null;
  onDragInfo?: (text: string | null) => void;
  /** Zusatzinfos im Tageskopf (Kalenderwoche: Termine, Tests, Hausaufgaben) */
  dayHeader?: (day: number) => ReactNode;
  /** Tage mit kräftiger Trennlinie davor (z. B. Samstag nach Freitag) */
  dayDividers?: readonly number[];
}) {
  const periods = useMemo(() => normalizePeriods(view.periods), [view.periods]);
  const divider = useMemo(() => new Set(dayDividers ?? []), [dayDividers]);
  const cells = useMemo(() => weekCells(view), [view]);
  const offDays = useMemo(() => (view.day_info ?? []).filter((d) => isOffDay(d)).map((d) => d.index), [view.day_info]);
  const layout = useMemo(() => layoutTimetable(cells, view.days.length, periods.length, { narrowDays: offDays }), [cells, view.days.length, periods.length, offDays]);
  const blocked = useMemo(() => blockedMap(view.blocked), [view.blocked]);
  const breakAfter = useMemo(() => breakSlots(view.breaks, periods), [view.breaks, periods]);

  const [drag, setDrag] = useState<DragState | null>(null);
  const [over, setOver] = useState<string | null>(null);

  const startDrag = (c: Cell, e: React.DragEvent) => {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', c.lesson_id);
    setDrag({ cell: c, options: null });
    onDragInfo?.('Gültige Ziele werden geladen …');
    if (loadOptions) {
      loadOptions(c.lesson_id)
        .then((opts) => {
          setDrag((d) => (d && d.cell.lesson_id === c.lesson_id ? { ...d, options: opts } : d));
          // Ausgangsposition zählt nicht als Ziel
          const ok = opts.filter((o) => o.ok && !(o.day === c.day && o.start === c.start)).length;
          onDragInfo?.(`${ok === 1 ? '1 gültiges Ziel' : `${ok} gültige Ziele`} (grün). Rot = Konflikt. Ablegen verschiebt sofort.`);
        })
        .catch(() => onDragInfo?.('Ziele konnten nicht geladen werden – Prüfung beim Ablegen.'));
    }
  };
  const endDrag = () => {
    setDrag(null);
    setOver(null);
    onDragInfo?.(null);
  };

  // beim Ziehen alle Felder des Zielbereichs (Doppelstunde) markieren
  const overSpan = useMemo(() => {
    const set = new Set<string>();
    if (!drag || !over) return set;
    const [d, p] = over.split(':').map(Number);
    for (let k = 0; k < Math.max(1, drag.cell.length); k++) set.add(`${d}:${(p ?? 0) + k}`);
    return set;
  }, [drag, over]);

  const gridDays: GridDay[] = useMemo(
    () =>
      Array.from({ length: layout.days }, (_, d) => {
        const h = dayHead(d, view);
        return {
          key: d,
          name: h.name,
          short: h.short,
          date: h.date,
          holiday: h.holiday,
          off: h.off,
          today: todayIndex === d,
          divider: divider.has(d),
          lanes: layout.dayLanes[d],
          header: dayHeader?.(d),
        };
      }),
    [layout, view, todayIndex, divider, dayHeader],
  );
  const gridRows: GridRow[] = useMemo(
    () => Array.from({ length: layout.periods }, (_, p) => ({ key: p, label: periods[p]?.label ?? `${p + 1}.`, time: periods[p]?.time, breakAfter: breakAfter.has(p) })),
    [layout.periods, periods, breakAfter],
  );

  const cell = (d: number, p: number): GridCell => {
    const key = `${d}:${p}`;
    const st = drag ? slotState(drag.options, d, p, { day: drag.cell.day, start: drag.cell.start }) : 'unknown';
    const opt = drag ? findOption(drag.options, d, p) : undefined;
    const cls = [drag && st === 'ok' ? 'ok' : '', drag && st === 'conflict' ? 'conflict' : '', drag && st === 'origin' ? 'origin' : '', drag && overSpan.has(key) ? 'dragover' : '']
      .filter(Boolean)
      .join(' ');
    return {
      blocked: blocked.has(key),
      className: cls,
      title: blocked.get(key) ?? (opt && !opt.ok ? opt.conflicts.join('\n') : undefined),
      handlers: {
        onDragOver:
          editable && drag
            ? (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = st === 'conflict' ? 'none' : 'move';
                if (over !== key) {
                  setOver(key);
                  if (opt && !opt.ok) onDragInfo?.(`Konflikt: ${opt.conflicts.join('; ')}`);
                  else if (opt?.ok) onDragInfo?.(`${view.days[d]}, ${p + 1}. Stunde: frei`);
                }
              }
            : undefined,
        onDragLeave: editable && drag ? () => setOver((o) => (o === key ? null : o)) : undefined,
        onDrop:
          editable && drag
            ? (e) => {
                e.preventDefault();
                const c = drag.cell;
                endDrag();
                if (c.day === d && c.start === p) return;
                onMove?.(c, d, p, opt);
              }
            : undefined,
      },
    };
  };

  const overlay = layout.placed.map((pc) => {
    const c = pc.cell;
    const bg = subjectColor(c.subject, c.color);
    const fg = textOn(bg);
    const lines = cellLines(c, view.kind);
    const style: CSSProperties = {
      gridRow: pc.gridRow,
      gridColumn: pc.gridColumn,
      ['--cell-bg' as string]: bg,
      ['--cell-fg' as string]: fg,
    };
    const coupled = isCoupled(c);
    const canDrag = !!editable && !c.locked;
    return [
      <button
        key={`${c.lesson_id}-${pc.day}-${pc.start}`}
        type="button"
        className={[
          'tt-cell',
          selectedId === c.lesson_id ? 'selected' : '',
          drag?.cell.lesson_id === c.lesson_id ? 'dragging' : '',
          coupled ? 'multi' : '',
          c.status ? `changed ${statusKindClass(c.status.label, c.status.cancelled)}` : '',
          c.status?.cancelled ? 'cancelled' : '',
          c.absent ? 'absent' : '',
          c.exam ? 'exam-block' : '',
        ]
          .filter(Boolean)
          .join(' ')}
        style={style}
        draggable={canDrag}
        onDragStart={canDrag ? (e) => startDrag(c, e) : undefined}
        onDragEnd={canDrag ? endDrag : undefined}
        onClick={() => onSelect?.(selectedId === c.lesson_id ? null : c)}
        aria-pressed={selectedId === c.lesson_id}
        aria-label={cellAriaLabel(c, view.days)}
      >
        <span className="subj">
          <SubjectAbbr id={c.subject} fallback={c.subject_name} passive />
        </span>
        {lines.map((l, i) => (l ? <span key={i} className="line">{l}</span> : null))}
        <span className="tags">
          {cellWeeksText(c) && <span className="tag">{cellWeeksText(c)}</span>}
          {c.status && <span className="tag tag-status">{c.status.label}</span>}
        </span>
        {c.locked && <Icon name="lock" className="lock" />}
      </button>,
      coupled ? (
        <CoursePartsPop key={`${c.lesson_id}-${pc.day}-${pc.start}-parts`} cell={c} style={{ gridRow: pc.gridRow, gridColumn: pc.gridColumn }} />
      ) : null,
      c.links?.length ? (
        <CellBadges key={`${c.lesson_id}-${pc.day}-${pc.start}-links`} links={c.links} className="tt-cell-links" style={{ gridRow: pc.gridRow, gridColumn: pc.gridColumn }} />
      ) : null,
    ];
  });

  return <DayPeriodGrid days={gridDays} rows={gridRows} label={`Stundenplan ${view.title}`} cell={cell} overlay={overlay} columnTemplate={layout.columnTemplate} compact={compact} />;
}

/** „3 Kurse“ im Block: Sprechblase mit den parallelen Kursteilen (Fach, Lehrkraft, Raum) und – mit Planungsrecht –
 *  Sprung in Planung → Kurse, wo die Kopplung festgelegt wird. */
function CoursePartsPop({ cell, style }: { cell: Cell; style?: CSSProperties }) {
  const user = useOptionalUser();
  const canPlan = !!user && can(user, ['plans.read_all', 'timetable.edit', 'timetable.generate']);
  return (
    <span className="tt-cell-parts" style={style}>
      <PopButton
        className="tag tt-parts-btn"
        ariaLabel={`${cell.parts.length} parallele Kurse von ${cell.subject_name || cell.subject}`}
        label={<>{cell.parts.length} Kurse ▾</>}
      >
        <p className="small muted mt-0">Gleichzeitig, jeweils mit eigener Gruppe:</p>
        <ul className="pop-items tt-parts">
          {cell.parts.map((p, i) => (
            <li key={i}>
              <strong>{p.label || p.subject}</strong>
              <span>{p.teacher ? <TeacherAbbr id={p.teacher} /> : 'ohne Lehrkraft'}</span>
              <span>{p.room ? <RoomAbbr id={p.room} /> : 'ohne Raum'}</span>
            </li>
          ))}
        </ul>
        {canPlan && cell.course_id ? (
          <Link className="btn btn-sm mt-2" to={`/planung/kurse?kurs=${encodeURIComponent(cell.course_id)}`}>
            <Icon name="edit" /> Kurs bearbeiten
          </Link>
        ) : null}
      </PopButton>
    </span>
  );
}

/** Kompakte Listenansicht (Handy): Tage untereinander. */
export function TimetableList({
  view,
  onSelect,
  selectedId,
  dayHeader,
}: {
  view: TimetableView;
  week?: number;
  onSelect?: (c: Cell | null) => void;
  selectedId?: string | null;
  dayHeader?: (day: number) => ReactNode;
}) {
  const periods = normalizePeriods(view.periods);
  const byDay = cellsByDay(weekCells(view), view.days.length);
  return (
    <div className="tt-daylist">
      {byDay.map((cells, d) => {
        const h = dayHead(d, view);
        return (
        <section key={d} aria-labelledby={`tt-day-${d}`} className={h.off ? 'off-day' : undefined}>
          <h3 id={`tt-day-${d}`}>
            {h.name}
            {h.date && <span className="muted small"> · {h.date}</span>}
            {h.holiday && <span className="badge badge-warning">{h.holiday}</span>}
          </h3>
          {dayHeader?.(d)}
          {cells.length === 0 ? (
            <div className="day-free">Kein Unterricht</div>
          ) : (
            <ul className="day-list">
              {cells.map((c) => {
                const color = subjectColor(c.subject, c.color);
                return (
                  <li
                    key={c.lesson_id}
                    className={`day-item${selectedId === c.lesson_id ? ' selected' : ''}${c.status ? ` changed ${statusKindClass(c.status.label, c.status.cancelled)}` : ''}${onSelect ? ' clickable' : ''}`}
                    style={{ ['--subj' as string]: color }}
                    onClick={() => onSelect?.(c)}
                  >
                    <div className="period">
                      {periodRangeLabel(c.start, c.length)}
                      <small>{periods[c.start]?.time}</small>
                    </div>
                    <div>
                      <div className="subject">
                        <SubjectAbbr id={c.subject} fallback={c.subject_name}>
                          {c.subject_name || c.subject}
                        </SubjectAbbr>
                        {c.status && <span className="tag tag-status ml-2">{c.status.label}</span>}
                      </div>
                      <div className="meta">
                        {[
                          c.teachers.length ? <AbbrList key="t" kind="teacher" ids={c.teachers} /> : null,
                          c.rooms.length ? <AbbrList key="r" kind="room" ids={c.rooms} /> : null,
                          view.kind !== 'class' && c.classes.length ? <AbbrList key="c" kind="class" ids={c.classes} /> : null,
                        ]
                          .filter(Boolean)
                          .map((node, i) => (
                            <span key={i}>
                              {i > 0 ? ' · ' : null}
                              {node}
                            </span>
                          ))}
                      </div>
                      {isCoupled(c) && (
                        <details>
                          <summary className="small">{c.parts.length} parallele Kurse</summary>
                          <ul className="tt-parts">
                            {c.parts.map((p, i) => (
                              <li key={i}>
                                <span>{p.label || p.subject}</span>
                                <span>{p.teacher ? <TeacherAbbr id={p.teacher} /> : '–'}</span>
                                <span>{p.room ? <RoomAbbr id={p.room} /> : '–'}</span>
                              </li>
                            ))}
                          </ul>
                        </details>
                      )}
                    </div>
                    <div>
                      {cellWeeksText(c) && <span className="badge">{cellWeeksText(c)}</span>}
                      {c.links?.length ? <CellBadges links={c.links} className="tt-cell-links tt-cell-links-list" /> : null}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
        );
      })}
    </div>
  );
}
