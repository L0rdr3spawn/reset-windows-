/**
 * Reiter „Wochenplan“: konkrete Kalenderwoche der Klasse inkl. Vertretungen (`GET /classes/{id}/week`).
 * * Wochennavigation (`components/WeekNav`): Woche 1 … Y, KW und Zeitraum (R3).
 * * Immer Mo–So (§16 E2): Tage ohne Unterricht der Klasse schmal und abgeblendet; „Nur Unterrichtstage“ blendet leere
 *   freie Tage aus (je Gerät gemerkt).
 * * Breit: Tabelle Tage (mit Datum) × Stunden (mit Uhrzeit); Handy: Liste je Tag (kein waagerechtes Scrollen).
 * * Gekoppelte Kursteile in einem Block, Änderungen als Text-Badge (Vertretung, Entfall, Verlegt, Raum,
 *   Klasse abwesend, Klausur), Ferien-/freie Tage, Sperrzeiten der Klasse gestreift.
 * * Mit `can_plan`: Stunde anklicken → „Findet nicht statt“, Knopf „Klasse ist nicht da“, Liste der Ausfälle mit
 *   „Zurücknehmen“.
 */
import { useMemo, useRef, useState, type CSSProperties, type ReactNode, type RefObject } from 'react';
import { Link } from 'react-router-dom';
import type { Cell, PlanState } from '../../api/types';
import { CalendarWeek, type CalendarDay } from './CalendarWeek';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { NoPlanNotice, PlanBadges } from '../../components/PlanNotice';
import { AsyncButton, ErrorBox, Loading, SegmentedControl, Spinner } from '../../components/ui';
import { useSchoolYear, WeekNav as YearWeekNav } from '../../components/WeekNav';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useIndex, useSettings } from '../../hooks/useCollection';
import { useMediaQuery, useStoredState } from '../../hooks/misc';
import { subjectColor, textOn } from '../../lib/colors';
import { currentSchoolDay, dateRangeLabel, formatLong, isValidISO, mondayOf, todayISO, WEEKDAYS, WEEKDAYS_SHORT } from '../../lib/dates';
import { NO_PLAN_SHORT, planMissing } from '../../lib/planPeriods';
import { isOffDay } from '../../lib/weeks';
import { classesApi } from './api';
import { StatusBadge } from './components';
import { DayPeriodGrid, type GridDay, type GridRow } from '../../components/grid/DayPeriodGrid';
import { ClassAbsentDialog, LessonDialog } from './dialogs';
import {
  absencePeriodsText,
  absenceTitle,
  cellBadges,
  escortsOf,
  inWeek,
  isCancelled,
  mergeCells,
  rowCount,
  shiftWeek,
  slotsByPeriod,
  slotText,
  sortAbsences,
  STATUS_INFO,
  weekTitle,
  type NameLookup,
  type SlotItem,
  type StatusKey,
} from './logic';
import type { ClassDetail, ClassWeek, ClassWeekDay, WeekAbsence, WeekCell } from './types';

const LIVE = ['substitutions', 'absences', 'overrides', 'timetable', 'classes', 'courses', 'holidays', 'exams'];

function dayHead(d: ClassWeekDay): { short: string; long: string; date: string } {
  const [, m, day] = d.date.split('-');
  return { short: WEEKDAYS_SHORT[d.weekday] ?? '', long: WEEKDAYS[d.weekday] ?? '', date: `${day}.${m}.` };
}

/** „Ferien“ bzw. „unterrichtsfrei“ (Feiertag, beweglicher Ferientag …); R3: aus `day_kind`, sonst aus dem Namen. */
export function holidayTag(name: string, kind?: ClassWeekDay['day_kind']): string {
  if (kind === 'ferien') return 'Ferien';
  if (kind === 'feiertag') return 'unterrichtsfrei';
  return /ferien/i.test(name) ? 'Ferien' : 'unterrichtsfrei';
}

/** Tag ohne Unterricht der Klasse und ohne Einträge (schmale Spalte bzw. ausgeblendet mit „Nur Unterrichtstage“). */
export function isEmptyOffDay(d: ClassWeekDay): boolean {
  return isOffDay(d) && !d.has_items && !d.cells.length;
}

/** Sichtbare Tage: Mo–So, mit `onlyTeaching` ohne leere Tage ohne Unterricht (§16 E2). */
export function visibleWeekDays(days: readonly ClassWeekDay[], onlyTeaching: boolean): ClassWeekDay[] {
  return onlyTeaching ? days.filter((d) => !isEmptyOffDay(d)) : [...days];
}

// ---------------------------------------------------------------------------------------------- Block

export interface BlockCtx {
  names: NameLookup;
  colorOf: (subject: string) => string;
  partLabel: (courseId: string | null | undefined, part: number | null | undefined) => string;
  times: readonly string[];
  onPick?: (item: SlotItem) => void;
}

function Changed({ now, before }: { now: string; before?: string | null }) {
  if (!before || before === now) return <>{now}</>;
  return (
    <>
      <strong>{now}</strong>{' '}
      <s className="kl-old">
        <span className="sr-only">(statt </span>
        {before}
        <span className="sr-only">)</span>
      </s>
    </>
  );
}

function CellLines({ c, names }: { c: WeekCell; names: NameLookup }) {
  const teacher = c.teacher ? names.teacher(c.teacher) : '';
  const room = c.room ? names.room(c.room) : '';
  return (
    <span className="kl-line">
      {teacher && <Changed now={teacher} before={c.original_teacher ? names.teacher(c.original_teacher) : null} />}
      {teacher && room && ' · '}
      {room && <Changed now={room} before={c.original_room ? names.room(c.original_room) : null} />}
    </span>
  );
}

export function SlotBlock({ item, ctx }: { item: SlotItem; ctx: BlockCtx }) {
  const { names } = ctx;
  const first = item.cells[0] as WeekCell;
  const subjects = [...new Set(item.cells.map((c) => names.subject(c.subject) || 'Unterricht'))];
  const title = subjects.length > 3 ? `${subjects.slice(0, 2).join(' / ')} +${subjects.length - 2}` : subjects.join(' / ');
  const notes = [...new Set(item.cells.map((c) => c.note).filter(Boolean))];
  const exams = [...new Set(item.cells.map((c) => c.exam).filter((x): x is string => !!x))];
  // gleiche Optik wie ein Block im Stundenplan (styles/timetable.css .tt-cell): Fachfarbe als Fläche, Änderung als
  // Rahmen in der Farbe der Vertretungsart, Entfall abgeblendet und durchgestrichen
  const cls = [
    'tt-cell',
    'kl-item',
    item.main ? `changed ${STATUS_INFO[item.main].cls}` : '',
    item.cancelled ? 'cancelled' : '',
    item.coupled ? 'multi' : '',
  ]
    .filter(Boolean)
    .join(' ');
  const color = ctx.colorOf(first.subject);
  const style = { ['--subj' as string]: color, ['--cell-bg' as string]: color, ['--cell-fg' as string]: textOn(color) } as CSSProperties;
  const text = slotText(item, names, ctx.times[item.period]);
  const content = (
    <>
      <span className="subj kl-item-title">{title}</span>
      {item.coupled ? (
        <span className="kl-parts">
          {item.cells.map((c) => (
            <span key={`${c.part ?? 0}-${c.entry_id ?? ''}`} className={`kl-part${isCancelled(c) ? ' cancelled' : ''}`}>
              <span className="kl-part-label">{ctx.partLabel(c.course_id, c.part) || names.subject(c.subject)}:</span> <CellLines c={c} names={names} />
              {cellBadges(c).map((k) => (
                <span key={k}>
                  {' '}
                  <StatusBadge status={k} compact />
                </span>
              ))}
            </span>
          ))}
        </span>
      ) : (
        <CellLines c={first} names={names} />
      )}
      {item.badges.length > 0 && (
        <span className="kl-badges">
          {item.badges.map((b: StatusKey) => (
            <StatusBadge key={b} status={b} />
          ))}
        </span>
      )}
      {exams.map((e) => (
        <span key={e} className="kl-note">
          {e}
        </span>
      ))}
      {notes.map((n) => (
        <span key={n} className="kl-note">
          {n}
        </span>
      ))}
    </>
  );
  if (ctx.onPick && item.markable) {
    return (
      <button type="button" className={`${cls} kl-pick`} style={style} onClick={() => ctx.onPick?.(item)}>
        {content}
        <span className="sr-only"> – „Findet nicht statt“ eintragen</span>
      </button>
    );
  }
  return (
    <div className={cls} style={style} title={text}>
      {content}
    </div>
  );
}

// ---------------------------------------------------------------------------------------------- Raster / Liste

export function WeekGrid({
  week,
  slots,
  rows,
  breaks,
  blocked,
  ctx,
  caption,
  dayInfo,
}: {
  week: ClassWeek;
  slots: SlotItem[][][];
  rows: number;
  breaks: Set<number>;
  blocked: (weekday: number, period: number) => string | null;
  ctx: BlockCtx;
  caption: string;
  /** Zusatzinfos im Tageskopf (Kalender: Termine, Tests, Hausaufgaben) */
  dayInfo?: (d: ClassWeekDay) => ReactNode;
}) {
  const today = todayISO();
  const noPlan = planMissing(week.week_info?.plan);
  const days: GridDay[] = week.days.map((d) => {
    const h = dayHead(d);
    const off = isEmptyOffDay(d);
    return {
      key: d.date,
      name: h.long,
      short: h.short,
      date: h.date,
      off,
      today: d.date === today,
      header: dayInfo?.(d),
      fill: off ? <span className="sr-only">kein Unterricht</span> : d.holiday ? (
        <>
          <span className="kl-holiday-tag">{holidayTag(d.holiday, d.day_kind)}</span>
          <span>{d.holiday}</span>
        </>
      ) : noPlan && !d.cells.length ? (
        <span>{NO_PLAN_SHORT}</span>
      ) : undefined,
    };
  });
  const gridRows: GridRow[] = Array.from({ length: rows }, (_, p) => ({ key: p, label: `${p + 1}.`, time: week.period_times[p] ?? '', breakAfter: breaks.has(p) }));
  return (
    <DayPeriodGrid
      days={days}
      rows={gridRows}
      label={caption}
      cell={(di, p) => {
        const d = week.days[di]!;
        const items = slots[di]?.[p] ?? [];
        const note = items.length ? null : blocked(d.weekday, p);
        return {
          blocked: !!note,
          title: note ?? undefined,
          content: (
            <>
              {items.map((it) => (
                <SlotBlock key={it.key} item={it} ctx={ctx} />
              ))}
              {note && <span className="sr-only">Klasse nicht anwesend: {note}</span>}
            </>
          ),
        };
      }}
    />
  );
}

export function WeekList({
  week,
  slots,
  ctx,
  dayInfo,
}: {
  week: ClassWeek;
  slots: SlotItem[][][];
  ctx: BlockCtx;
  dayInfo?: (d: ClassWeekDay) => ReactNode;
}) {
  const today = todayISO();
  const noPlan = planMissing(week.week_info?.plan);
  return (
    <div className="kl-daylist">
      {week.days.map((d, di) => {
        const items = (slots[di] ?? []).flat();
        const hid = `kl-day-${d.date}`;
        return (
          <section key={d.date} aria-labelledby={hid}>
            <h3 id={hid}>
              {formatLong(d.date)}
              {d.date === today && (
                <span className="badge badge-primary ml-2">Heute</span>
              )}
            </h3>
            {dayInfo?.(d)}
            {isEmptyOffDay(d) ? (
              <div className="day-free">Kein Unterricht</div>
            ) : d.holiday ? (
              <div className="day-free">
                <strong>{holidayTag(d.holiday, d.day_kind)}:</strong> {d.holiday}
              </div>
            ) : items.length === 0 ? (
              <div className="day-free">{noPlan ? NO_PLAN_SHORT : 'Kein Unterricht'}</div>
            ) : (
              <ul className="day-list">
                {items.map((it) => {
                  const first = it.cells[0] as WeekCell;
                  const status = it.cancelled ? 'changed k-entfall' : it.main ? `changed ${STATUS_INFO[it.main].cls}` : '';
                  return (
                    <li key={it.key} className={`day-item${status ? ` ${status}` : ''}`} style={{ ['--subj' as string]: ctx.colorOf(first.subject) } as CSSProperties}>
                      <div className="period">
                        {it.period + 1}.<small>{week.period_times[it.period] ?? ''}</small>
                      </div>
                      <SlotBlock item={it} ctx={ctx} />
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

// ---------------------------------------------------------------------------------------------- Navigation

export function WeekNav({
  date,
  onChange,
  kw,
  range,
  loading,
  schoolDays,
  plan,
}: {
  date: string;
  onChange: (d: string) => void;
  kw: number;
  range: string;
  loading: boolean;
  schoolDays: number;
  /** Planzeiträume: Zeitraum der Woche (Beginn/Ende, kein Stundenplan) */
  plan?: PlanState | null;
}) {
  const current = currentSchoolDay(new Date(), schoolDays);
  const isCurrent = inWeek(date, current);
  return (
    <div className="kl-weeknav" role="group" aria-label="Woche wählen">
      <button type="button" className="btn btn-icon" onClick={() => onChange(shiftWeek(date, -1))} aria-label="Vorherige Woche">
        <Icon name="chevronLeft" />
      </button>
      <button type="button" className="btn" onClick={() => onChange(current)} disabled={isCurrent}>
        Heute
      </button>
      <button type="button" className="btn btn-icon" onClick={() => onChange(shiftWeek(date, 1))} aria-label="Nächste Woche">
        <Icon name="chevronRight" />
      </button>
      <label htmlFor="kl-week-date" className="sr-only">
        Datum in der Woche
      </label>
      <input
        id="kl-week-date"
        type="date"
        value={date}
        onChange={(e) => {
          if (isValidISO(e.target.value)) onChange(e.target.value);
        }}
      />
      <span className="kl-week-label" aria-live="polite">
        <strong>KW {kw}</strong> <span>{range}</span>
        {isCurrent && <span className="badge badge-primary">aktuelle Woche</span>}
        <PlanBadges plan={plan} weekStart={mondayOf(date)} />
        {loading && <Spinner label="Woche wird geladen …" />}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------- Ausfälle

function AbsenceList({
  week,
  className,
  canPlan,
  onChanged,
  headingRef,
}: {
  week: ClassWeek;
  className: string;
  canPlan: boolean;
  onChanged: () => void;
  headingRef: RefObject<HTMLHeadingElement | null>;
}) {
  const toast = useToast();
  // Begleitungen stehen bei ihrer Klassen-Abwesenheit; übrige (z. B. Klassen-Abwesenheit schon gelöscht) einzeln
  const linked = new Set(week.absences.flatMap((a) => escortsOf(a, week.absences, className)).map((a) => a.id));
  const list = sortAbsences(week.absences.filter((a) => a.kind === 'class' || a.kind === 'lesson' || (a.kind === 'teacher' && !linked.has(a.id))));
  const withdraw = async (a: WeekAbsence, escorts: WeekAbsence[]) => {
    try {
      await classesApi.withdraw(a.id);
      for (const e of escorts) await classesApi.withdraw(e.id);
      toast.success('Zurückgenommen – der Plan wird automatisch neu berechnet.');
      onChanged();
    } catch (e) {
      toast.error(e, 'Zurücknehmen');
    }
  };
  return (
    <section className="card" aria-labelledby="kl-abs-h">
      <div className="card-head">
        <h2 id="kl-abs-h" ref={headingRef} tabIndex={-1}>
          Ausfälle dieser Woche
        </h2>
        {list.length > 0 && <span className="badge">{list.length}</span>}
      </div>
      {list.length === 0 ? (
        <p className="small muted" style={{ margin: 0 }}>
          Keine Ausfälle eingetragen.
        </p>
      ) : (
        <ul className="kl-rows">
          {list.map((a) => {
            const escorts = escortsOf(a, week.absences, className);
            const title = absenceTitle(a, className);
            return (
              <li key={a.id} className="kl-row">
                <span className="kl-row-main">
                  <strong>{title}</strong>
                  <span className="small muted">
                    {dateRangeLabel(a.date_from, a.date_to)} · {absencePeriodsText(a)}
                    {a.reason ? ` · ${a.reason}` : ''}
                    {escorts.length > 0 && ` · Begleitung: ${escorts.map((e) => e.ref_name || e.ref).join(', ')}`}
                  </span>
                </span>
                {canPlan && a.can_delete && (
                  <span className="kl-row-side">
                    <AsyncButton
                      className="btn btn-sm"
                      confirm={`„${title}“ (${dateRangeLabel(a.date_from, a.date_to)}) zurücknehmen?${escorts.length ? ' Die Begleitungen werden ebenfalls zurückgenommen.' : ''} Der Plan wird automatisch neu berechnet.`}
                      onClick={() => withdraw(a, escorts)}
                    >
                      <Icon name="undo" /> Zurücknehmen<span className="sr-only">: {title}</span>
                    </AsyncButton>
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------------------------- Reiter

export function WeekTab({ detail, names, date, onDate }: { detail: ClassDetail; names: NameLookup; date: string; onDate: (d: string) => void }) {
  const cls = detail.class;
  const { data: settings } = useSettings();
  const subjects = useIndex('subjects');
  const q = useApi((signal) => classesApi.week(cls.id, date, signal), [cls.id, date], { live: LIVE, keepPrevious: true });
  const { year } = useSchoolYear(date, { classId: cls.id });
  const [onlyTeaching, setOnlyTeaching] = useStoredState<boolean>('sm-kl-only-teaching', false);
  const narrow = useMediaQuery('(max-width: 700px)');
  const [mode, setMode] = useStoredState<'grid' | 'list'>('sm-kl-mode', 'grid');
  const effective = narrow ? 'list' : mode;
  const [lessonFor, setLessonFor] = useState<{ day: ClassWeekDay; item: SlotItem } | null>(null);
  const [classOpen, setClassOpen] = useState(false);
  const absHeading = useRef<HTMLHeadingElement>(null);
  // nach „Übernehmen“: Fokus auf die Liste der Ausfälle (dort steht der neue Eintrag mit „Zurücknehmen“)
  const afterApply = () => {
    q.reload();
    window.setTimeout(() => absHeading.current?.focus(), 50);
  };

  const raw = q.data && q.data.class_id === cls.id ? q.data : undefined;
  const week = useMemo(() => (raw ? { ...raw, days: visibleWeekDays(raw.days, onlyTeaching) } : undefined), [raw, onlyTeaching]);
  const stale = !!week && !inWeek(week.week_start, date);
  const canPlan = (week?.can_plan ?? detail.can_plan) && !stale;
  const title = weekTitle(week && !stale ? week.week_start : date, raw?.days.length || 7, week && !stale ? week.week_info?.week_text : null);

  const merged = useMemo(() => (week ? week.days.map((d) => mergeCells(d.cells)) : []), [week]);
  const rows = week ? rowCount(week.days, week.periods) : 0;
  const slots = useMemo(() => merged.map((items) => slotsByPeriod(items, rows)), [merged, rows]);
  const partLabels = useMemo(() => new Map(detail.subjects.map((s) => [`${s.course_id}#${s.part ?? 0}`, s.label])), [detail.subjects]);

  const ctx: BlockCtx = {
    names,
    colorOf: (s) => subjectColor(s, subjects.get(s)?.color),
    partLabel: (courseId, part) => (courseId ? partLabels.get(`${courseId}#${part ?? 0}`) ?? '' : ''),
    times: week?.period_times ?? [],
    onPick: canPlan
      ? (item) => {
          const day = week?.days[merged.findIndex((items) => items.includes(item))];
          if (day) setLessonFor({ day, item });
        }
      : undefined,
  };

  const today = todayISO();
  const defaultDate = week && week.days.some((d) => d.date === today && !d.holiday) ? today : week?.days.find((d) => !d.holiday)?.date ?? date;
  // Raster = dieselbe Kalenderwoche wie im Stundenplan (7 Tage); Klick → „findet nicht statt“ (Klassenleitung)
  const pickCell = (c: Cell, day: CalendarDay) => {
    if (!canPlan) return;
    const item = mergeCells(day.cells).find((it) => it.period === c.start && c.lesson_id.startsWith(`${it.lessonId ?? it.key}@`));
    if (item?.markable) setLessonFor({ day, item });
  };

  return (
    <div className="stack">
      <div className="kl-week-tools">
        {effective === 'list' ? (
          <div className="kl-weeknav">
            <YearWeekNav value={date} onChange={onDate} year={year} info={week && !stale ? week.week_info : null} label="Woche wählen" showText={false} />
            <span className="kl-week-label" aria-live="polite">
              {title.label}
              {q.loading && !!q.data && <Spinner label="Woche wird geladen …" />}
            </span>
          </div>
        ) : (
          <span />
        )}
        <div className="row">
          <label className="check">
            <input type="checkbox" checked={onlyTeaching} onChange={(e) => setOnlyTeaching(e.target.checked)} /> Nur Unterrichtstage
          </label>
          {!narrow && (
            <SegmentedControl
              label="Darstellung"
              value={mode}
              options={[
                { value: 'grid', label: 'Raster' },
                { value: 'list', label: 'Liste' },
              ]}
              onChange={setMode}
            />
          )}
          {canPlan && (
            <button type="button" className="btn btn-primary" onClick={() => setClassOpen(true)}>
              <Icon name="calendar" /> Klasse ist nicht da
            </button>
          )}
          <Link className="btn" to={`/stundenplan/class/${encodeURIComponent(cls.id)}`}>
            <Icon name="grid" /> Stundenplan
          </Link>
        </div>
      </div>

      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading label="Wochenplan wird geladen …" />}
      {week && (
        <div aria-busy={q.loading} className={stale ? 'kl-stale' : undefined}>
          {effective === 'grid' ? (
            <CalendarWeek
              kind="class"
              refId={cls.id}
              date={date}
              onDate={onDate}
              title={cls.name}
              onPick={pickCell}
              hint={
                <HelpTip>
                  Der Plan dieser Klasse für die gewählte Kalenderwoche, mit Vertretungen, Ausfällen, Terminen und Hausaufgaben.
                  {canPlan ? ' Stunde anklicken, um sie ausfallen zu lassen („findet nicht statt“).' : ''}
                </HelpTip>
              }
            />
          ) : (
            <>
              <NoPlanNotice plan={week.week_info?.plan} />
              <WeekList week={week} slots={slots} ctx={ctx} />
            </>
          )}
        </div>
      )}

      {week && <AbsenceList week={week} className={cls.name} canPlan={canPlan} onChanged={q.reload} headingRef={absHeading} />}

      {lessonFor && week && (
        <LessonDialog
          detail={detail}
          date={lessonFor.day.date}
          dayCells={lessonFor.day.cells}
          item={lessonFor.item}
          periodTimes={week.period_times}
          names={names}
          onClose={() => setLessonFor(null)}
          onApplied={() => {
            setLessonFor(null);
            afterApply();
          }}
        />
      )}
      {classOpen && week && (
        <ClassAbsentDialog
          detail={detail}
          defaultDate={defaultDate}
          periodsCount={week.periods || settings?.periods || 8}
          periodTimes={week.period_times}
          names={names}
          onClose={() => setClassOpen(false)}
          onApplied={() => {
            setClassOpen(false);
            afterApply();
          }}
        />
      )}
    </div>
  );
}
