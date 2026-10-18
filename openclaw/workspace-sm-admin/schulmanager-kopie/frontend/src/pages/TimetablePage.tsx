import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import { timetable as ttApi } from '../api/endpoints';
import type { Cell, MoveOption, TimetableKind, TimetableView } from '../api/types';
import { Icon } from '../components/Icon';
import { NoPlanNotice } from '../components/PlanNotice';
import { SearchSelect, type SelectOption } from '../components/SearchSelect';
import { cellWeeksText, TimetableGrid, TimetableList } from '../components/TimetableGrid';
import { GridLegend } from '../components/grid/DayPeriodGrid';
import { useSchoolYear, WeekNav } from '../components/WeekNav';
import { CalendarWeek } from '../features/classes/CalendarWeek';
import { Alert, AsyncButton, ErrorBox, Loading, SegmentedControl } from '../components/ui';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { useCollection, useSettings } from '../hooks/useCollection';
import { useMediaQuery, useStoredState, useTitle } from '../hooks/misc';
import { useInputMode } from '../hooks/useInputMode';
import { currentSchoolDay, isValidISO, mondayOf, todayISO, weekdayIndex } from '../lib/dates';
import { sortBy } from '../lib/format';
import { periodRangeLabel } from '../lib/grid';
import { noPlanBlocked, planMissing } from '../lib/planPeriods';
import { can, isFamily } from '../lib/permissions';
import { isCurrentWeek, weekQueryFromSearch } from '../lib/weeks';
import { AbbrList, RoomAbbr, SubjectAbbr, TeacherAbbr } from '../components/Abbr';
import { useAllowedRefs } from '../features/teacher/hooks';
import { allowedKinds as scopeKinds, filterAllowed, forbiddenText } from '../features/teacher/scope';
import { isScopedTeacher } from '../features/teacher/windows';

const KIND_LABELS: Record<TimetableKind, string> = { class: 'Klasse', teacher: 'Lehrkraft', room: 'Raum', student: 'Schüler/in' };
const KIND_PICK: Record<TimetableKind, string> = { class: 'eine Klasse', teacher: 'eine Lehrkraft', room: 'einen Raum', student: 'eine Schülerin bzw. einen Schüler' };
const KINDS: TimetableKind[] = ['class', 'teacher', 'room', 'student'];

function isKind(k: string | undefined): k is TimetableKind {
  return !!k && (KINDS as string[]).includes(k);
}

/** Auswahllisten für Klasse/Lehrkraft/Raum/Schüler */
function useRefOptions(kind: TimetableKind, enabled: boolean): SelectOption[] {
  const classes = useCollection('classes', enabled && kind === 'class');
  const teachers = useCollection('teachers', enabled && kind === 'teacher');
  const rooms = useCollection('rooms', enabled && kind === 'room');
  const students = useCollection('students', enabled && kind === 'student');
  return useMemo(() => {
    switch (kind) {
      case 'class':
        return sortBy(classes.data ?? [], (c) => c.name).map((c) => ({ value: c.id, label: c.name, sub: c.site || undefined }));
      case 'teacher':
        return sortBy(teachers.data ?? [], (t) => t.name).map((t) => ({ value: t.id, label: `${t.name}`, sub: t.id, keywords: t.subjects?.join(' ') }));
      case 'room':
        return sortBy(rooms.data ?? [], (r) => r.id).map((r) => ({ value: r.id, label: r.name || r.id, sub: [r.type, r.site].filter(Boolean).join(' · ') }));
      case 'student':
        return sortBy(students.data ?? [], (s) => s.name).map((s) => ({ value: s.id, label: s.name, sub: s.class_id }));
      default:
        return [];
    }
  }, [kind, classes.data, teachers.data, rooms.data, students.data]);
}

function CellDetails({
  cell,
  view,
  editable,
  onClose,
  onChanged,
  lastConflicts,
  onMove,
}: {
  cell: Cell;
  view: TimetableView;
  editable: boolean;
  onClose: () => void;
  onChanged: () => void;
  lastConflicts: string[];
  onMove: (c: Cell, day: number, start: number, option?: MoveOption) => void;
}) {
  const toast = useToast();
  const { fine } = useInputMode();
  const [options, setOptions] = useState<MoveOption[] | null>(null);
  const [loadingOpts, setLoadingOpts] = useState(false);
  useEffect(() => setOptions(null), [cell.lesson_id]);
  const okOptions = (options ?? []).filter((o) => o.ok && !(o.day === cell.day && o.start === cell.start));
  return (
    <aside className="card tt-side" aria-label="Details zur Stunde">
      <div className="card-head">
        <h2 style={{ fontSize: 'var(--fs-lg)' }}>
          {cell.subject_name || cell.subject}{' '}
          <span className="muted small">
            <SubjectAbbr id={cell.subject} fallback={cell.subject_name} />
          </span>
        </h2>
        <button type="button" className="btn btn-ghost btn-icon btn-sm" onClick={onClose} aria-label="Details schließen">
          <Icon name="close" />
        </button>
      </div>
      <dl className="kv small">
        <dt>Zeit</dt>
        <dd>
          {view.days[cell.day]}, {periodRangeLabel(cell.start, cell.length)} Stunde
          {cell.length > 1 ? ' (Doppelstunde)' : ''}
        </dd>
        {cellWeeksText(cell) && (
          <>
            <dt>Wochen</dt>
            <dd>{cellWeeksText(cell)}</dd>
          </>
        )}
        <dt>Klassen</dt>
        <dd>
          <AbbrList kind="class" ids={cell.classes} empty="–" />
        </dd>
        <dt>Lehrkraft</dt>
        <dd>
          <AbbrList kind="teacher" ids={cell.teachers} empty="–" />
        </dd>
        <dt>Raum</dt>
        <dd>
          <AbbrList kind="room" ids={cell.rooms} empty="–" />
        </dd>
        <dt>Kurs</dt>
        <dd className="mono">{cell.label || cell.course_id}</dd>
        <dt>Status</dt>
        <dd>{cell.locked ? 'fixiert' : 'frei verschiebbar'}</dd>
      </dl>
      {cell.parts.length > 1 && (
        <details open style={{ marginTop: 12 }}>
          <summary>
            <strong>Kopplung: {cell.parts.length} parallele Kurse</strong>
          </summary>
          <ul className="tt-parts">
            {cell.parts.map((p, i) => (
              <li key={i}>
                <span>{p.label || p.subject}</span>
                <span>{p.teacher ? <TeacherAbbr id={p.teacher} /> : '–'}</span>
                <span>{p.room ? <RoomAbbr id={p.room} /> : '–'}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
      {lastConflicts.length > 0 && (
        <Alert kind="error" title="Verschieben nicht möglich">
          <ul>
            {lastConflicts.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </Alert>
      )}
      {editable && (
        <div className="stack-sm" style={{ marginTop: 12 }}>
          <AsyncButton
            className="btn w-100"
            onClick={async () => {
              try {
                await ttApi.lock(cell.lesson_id, !cell.locked);
                toast.success(cell.locked ? 'Stunde freigegeben' : 'Stunde fixiert');
                onChanged();
              } catch (e) {
                toast.error(e);
              }
            }}
          >
            <Icon name={cell.locked ? 'unlock' : 'lock'} /> {cell.locked ? 'Fixierung lösen' : 'Fixieren'}
          </AsyncButton>
          {!cell.locked && (
            <div>
              {options === null ? (
                <button
                  type="button"
                  className="btn w-100"
                  disabled={loadingOpts}
                  onClick={async () => {
                    setLoadingOpts(true);
                    try {
                      setOptions(await ttApi.options(cell.lesson_id));
                    } catch (e) {
                      toast.error(e);
                    } finally {
                      setLoadingOpts(false);
                    }
                  }}
                >
                  <Icon name="swap" /> {loadingOpts ? 'Lade Ziele …' : 'Verschieben nach …'}
                </button>
              ) : (
                <div className="field">
                  <label htmlFor="move-target">Gültiges Ziel wählen ({okOptions.length})</label>
                  <select
                    id="move-target"
                    defaultValue=""
                    onChange={(e) => {
                      const [d, s] = e.target.value.split(':').map(Number);
                      if (d === undefined || s === undefined || Number.isNaN(d)) return;
                      onMove(cell, d, s, okOptions.find((o) => o.day === d && o.start === s));
                    }}
                  >
                    <option value="" disabled>
                      – Ziel auswählen –
                    </option>
                    {okOptions.map((o) => (
                      <option key={`${o.day}:${o.start}`} value={`${o.day}:${o.start}`}>
                        {view.days[o.day]}, {periodRangeLabel(o.start, cell.length)} Stunde
                      </option>
                    ))}
                  </select>
                </div>
              )}
              {fine && (
                <p className="xsmall muted" style={{ marginTop: 6 }}>
                  Oder den Block ziehen: Grün = frei, Rot = Konflikt.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </aside>
  );
}

export default function TimetablePage() {
  const user = useUser();
  const toast = useToast();
  const navigate = useNavigate();
  const params = useParams<{ kind: string; ref: string }>();
  const [search, setSearch] = useSearchParams();
  const { data: settings } = useSettings();
  const isMobile = useMediaQuery('(max-width: 700px)');
  const { fine } = useInputMode();
  const [mode, setMode] = useStoredState<'grid' | 'list' | 'auto'>('sm-tt-mode', 'auto');
  const effectiveMode = mode === 'auto' ? (isMobile ? 'list' : 'grid') : mode;
  const family = isFamily(user);
  const readAll = can(user, 'plans.read_all');
  const canEditPlan = can(user, 'timetable.edit');
  // Kalenderwoche (Standard, mit Datum, Vertretungen, Terminen) bzw. Regelplan (nur Stundenplanung: bearbeiten)
  const [planMode, setPlanMode] = useStoredState<'kalender' | 'regelplan'>('sm-tt-plan', 'kalender');
  const regel = canEditPlan && planMode === 'regelplan';
  const editable = regel;
  const rawDate = search.get('datum');
  const calDate = isValidISO(rawDate) ? (rawDate as string) : currentSchoolDay(new Date(), settings?.days ?? 5);
  const setCalDate = (d: string) => {
    const sp = new URLSearchParams(search);
    sp.set('datum', d);
    setSearch(sp, { replace: true });
  };
  // Lehrkräfte (§9.3): nur eigene Klassen, eigener Plan, Räume – Freigaben vom Server
  const scoped = isScopedTeacher(user);
  const { allowed } = useAllowedRefs(scoped);

  // Kinder/eigene Schüler (Eltern/Schüler)
  const ownStudents = useCollection('students', family && !user.students?.length);
  const ownOptions: SelectOption[] = useMemo(() => {
    if (user.students?.length) return user.students.map((s) => ({ value: s.id, label: s.name, sub: s.class_id }));
    const ids = user.student_ids ?? [];
    const byId = new Map((ownStudents.data ?? []).map((s) => [s.id, s]));
    return ids.map((id) => ({ value: id, label: byId.get(id)?.name ?? id, sub: byId.get(id)?.class_id }));
  }, [user.students, user.student_ids, ownStudents.data]);

  // Standardansicht
  const defaultSel = (): { kind: TimetableKind; ref: string } | null => {
    if (family && user.student_ids?.length) return { kind: 'student', ref: user.student_ids[0] as string };
    if (user.teacher_id) return { kind: 'teacher', ref: user.teacher_id };
    return null;
  };
  const def = defaultSel();
  const kind: TimetableKind = isKind(params.kind) ? params.kind : (def?.kind ?? 'class');
  // Standard-Plan nur für die passende Ansicht (sonst z. B. Lehrerkürzel als Raum angefragt)
  const ref = params.ref ? decodeURIComponent(params.ref) : def && def.kind === kind ? def.ref : '';

  const baseKinds = KINDS.filter((k) => {
    if (family) return k === 'student';
    if (k === 'student') return can(user, 'students.read');
    return readAll || (k === 'teacher' && !!user.teacher_id);
  });
  const allowedKinds = scoped ? scopeKinds(baseKinds, allowed) : baseKinds;

  const rawOptions = useRefOptions(kind, !family && readAll);
  const options = useMemo(() => (scoped ? filterAllowed(rawOptions, allowed, kind) : rawOptions), [scoped, rawOptions, allowed, kind]);
  // Lehrkräfte sehen nur den eigenen Lehrerplan – keine Auswahl nötig
  const fixedTeacher = scoped && kind === 'teacher';
  // Woche (R3): ?datum= (Montag) kanonisch, ?woche=L laufende Woche; ohne Angabe die Woche von heute
  const today = todayISO();
  const weekQuery = weekQueryFromSearch(search);
  const [onlyTeaching, setOnlyTeaching] = useStoredState<boolean>('sm-tt-only-teaching', false);
  const query = { date: weekQuery.date ?? (weekQuery.week_no ? undefined : mondayOf(today)), week_no: weekQuery.week_no, all_days: !onlyTeaching };

  const select = (k: TimetableKind, r: string | null) => {
    if (!r) {
      navigate(`/stundenplan`, { replace: false });
      return;
    }
    navigate({ pathname: `/stundenplan/${k}/${encodeURIComponent(r)}`, search: search.toString() });
  };

  // Ohne Auswahl: erste Klasse vorwählen
  useEffect(() => {
    if (!ref && !family && kind === 'class' && options.length) select('class', options[0]?.value ?? null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ref, options.length]);

  const viewQ = useApi<TimetableView>(() => ttApi.view(kind, ref, query), [kind, ref, query.date, query.week_no, query.all_days], {
    enabled: !!ref && regel,
    live: ['timetable', 'courses', 'classes', 'teachers', 'rooms', 'subjects', 'settings'],
  });
  const forbidden = viewQ.error instanceof ApiError && viewQ.error.status === 403;
  // Ohne Auswahl (z. B. nach Wechsel der Ansicht auf „Lehrkraft“) keinen alten Plan mehr zeigen
  const rawView = forbidden || !ref ? undefined : viewQ.data;
  // Woche ohne gültigen Plan (Planzeiträume): Unterrichtsfelder schraffiert statt leer
  const view = useMemo(() => {
    if (!rawView || !planMissing(rawView.week_info?.plan)) return rawView;
    const teaching = (rawView.day_info ?? []).filter((d) => d.teaching).map((d) => d.index);
    return { ...rawView, blocked: [...(rawView.blocked ?? []), ...noPlanBlocked(teaching, rawView.periods.length)] };
  }, [rawView]);
  const monday = view?.week_info?.week_start ?? query.date ?? mondayOf(today);
  const { year } = useSchoolYear(monday, { enabled: !!settings });
  const setWeek = (m: string) => {
    const sp = new URLSearchParams(search);
    sp.set('datum', m);
    sp.delete('woche');
    setSearch(sp, { replace: true });
  };
  const [selected, setSelected] = useState<Cell | null>(null);
  const [conflicts, setConflicts] = useState<string[]>([]);
  const [dragInfo, setDragInfo] = useState<string | null>(null);
  const refLabel = view?.title ?? [...ownOptions, ...options].find((o) => o.value === ref)?.label ?? ref;
  useTitle(ref ? `Stundenplan ${refLabel}` : 'Stundenplan');

  // Auswahl nach Neuladen aktualisieren
  useEffect(() => {
    if (!selected || !view) return;
    const fresh = view.cells.find((c) => c.lesson_id === selected.lesson_id);
    setSelected(fresh ?? null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view]);

  const doMove = async (c: Cell, day: number, start: number, option?: MoveOption) => {
    if (option && !option.ok) {
      setConflicts(option.conflicts);
      setSelected(c);
      toast.warning('Ziel hat Konflikte', option.conflicts);
      return;
    }
    try {
      await ttApi.move(c.lesson_id, day, start);
      setConflicts([]);
      toast.success(`${c.subject} verschoben nach ${view?.days[day] ?? ''}, ${start + 1}. Stunde`);
      viewQ.reload();
    } catch (e) {
      if (e instanceof ApiError && e.isConflict) {
        setConflicts(e.conflicts);
        setSelected(c);
      }
      toast.error(e, 'Verschieben');
    }
  };

  const todayIdx = view && weekdayIndex(today) < view.days.length && isCurrentWeek(monday, today) ? weekdayIndex(today) : null;

  return (
    <div className="page">
      <div className="page-head">
        <h1>Stundenplan{ref ? `: ${refLabel}` : ''}</h1>
      </div>

      <div className="toolbar card">
        {allowedKinds.length > 1 && (
          <div className="field" style={{ minWidth: 0 }}>
            <span className="field-label" id="kind-label">
              Ansicht
            </span>
            <SegmentedControl
              label="Ansicht"
              value={kind}
              options={allowedKinds.map((k) => ({ value: k, label: KIND_LABELS[k] }))}
              onChange={(k) => {
                setSelected(null);
                if (k === 'teacher' && user.teacher_id && !readAll) select(k, user.teacher_id);
                else navigate(`/stundenplan/${k}/`, { replace: false });
              }}
            />
          </div>
        )}
        <div className="field wide">
          {family ? (
            ownOptions.length > 1 ? (
              <SearchSelect label="Kind" options={ownOptions} value={ref} onChange={(v) => select('student', v)} />
            ) : (
              <>
                <span className="field-label">Plan</span>
                <span>{ownOptions[0]?.label ?? view?.title ?? '–'}</span>
              </>
            )
          ) : (readAll || kind === 'student') && !fixedTeacher ? (
            <SearchSelect
              label={KIND_LABELS[kind]}
              options={options}
              value={ref}
              onChange={(v) => {
                setSelected(null);
                select(kind, v);
              }}
              placeholder={`${KIND_LABELS[kind]} suchen …`}
            />
          ) : (
            <>
              <span className="field-label">{KIND_LABELS[kind]}</span>
              <span>{view?.title ?? ref}</span>
            </>
          )}
        </div>
        {canEditPlan && (
          <div className="field" style={{ minWidth: 0 }}>
            <span className="field-label">Plan</span>
            <SegmentedControl
              label="Plan"
              value={planMode}
              options={[
                { value: 'kalender', label: 'Kalenderwoche' },
                { value: 'regelplan', label: 'Regelplan bearbeiten' },
              ]}
              onChange={(m) => setPlanMode(m)}
            />
          </div>
        )}
        {regel && (
        <div className="field" style={{ minWidth: 0 }}>
          <span className="field-label">Woche</span>
          <WeekNav value={monday} onChange={setWeek} year={year} info={view?.week_info} today={today} />
        </div>
        )}
        {regel && (
        <label className="check" style={{ alignSelf: 'flex-end' }}>
          <input type="checkbox" checked={onlyTeaching} onChange={(e) => setOnlyTeaching(e.target.checked)} /> Nur Unterrichtstage
        </label>
        )}
        <div className="field" style={{ minWidth: 0 }}>
          <span className="field-label">Darstellung</span>
          <SegmentedControl
            label="Darstellung"
            value={effectiveMode}
            options={[
              { value: 'grid', label: 'Raster' },
              { value: 'list', label: 'Liste' },
            ]}
            onChange={(m) => setMode(m)}
          />
        </div>
      </div>

      {!ref && !family && <Alert kind="info">Bitte {KIND_PICK[kind]} auswählen.</Alert>}
      {forbidden ? (
        <Alert kind="warning" title="Dieser Plan ist für Ihr Konto nicht freigegeben">
          <p style={{ margin: '0 0 8px' }}>{forbiddenText(kind, scoped)}</p>
          <div className="row">
            {user.teacher_id && (
              <Link className="btn btn-sm" to={`/stundenplan/teacher/${encodeURIComponent(user.teacher_id)}`}>
                <Icon name="grid" /> Mein Stundenplan
              </Link>
            )}
            {family && user.student_ids?.[0] && (
              <Link className="btn btn-sm" to={`/stundenplan/student/${encodeURIComponent(user.student_ids[0])}`}>
                <Icon name="grid" /> Eigener Plan
              </Link>
            )}
            {scoped &&
              (allowed?.classes ?? []).slice(0, 16).map((c) => (
                <Link key={c} className="btn btn-sm" to={`/stundenplan/class/${encodeURIComponent(c)}`}>
                  Klasse {c}
                </Link>
              ))}
          </div>
        </Alert>
      ) : viewQ.error ? (
        <ErrorBox error={viewQ.error} onRetry={viewQ.reload} />
      ) : null}
      {!regel && ref && !forbidden && <CalendarWeek kind={kind} refId={ref} date={calDate} onDate={setCalDate} title={refLabel} mode={effectiveMode} />}
      {regel && viewQ.initialLoading && ref && <Loading />}
      {regel && view && <NoPlanNotice plan={view.week_info?.plan} />}
      {editable && effectiveMode === 'grid' && (
        <p className="small muted no-print" aria-live="polite">
          {dragInfo ?? fine
            ? 'Bearbeiten: Block ziehen oder anklicken (Details, Fixieren, Verschieben).'
            : 'Bearbeiten: Block antippen (Details, Fixieren, Verschieben).'}
        </p>
      )}
      {regel && view && (
        <div className={`tt-layout${selected ? '' : ' no-side'}`}>
          <div>
            {effectiveMode === 'grid' ? (
              <TimetableGrid
                view={view}
                editable={editable}
                selectedId={selected?.lesson_id ?? null}
                onSelect={(c) => {
                  setSelected(c);
                  setConflicts([]);
                }}
                onMove={doMove}
                loadOptions={editable ? ttApi.options : undefined}
                todayIndex={todayIdx}
                onDragInfo={setDragInfo}
              />
            ) : (
              <TimetableList view={view} onSelect={setSelected} selectedId={selected?.lesson_id ?? null} />
            )}
            <GridLegend
              hidden={false}
              items={[
                ...((view.blocked?.length ?? 0) > 0 ? [{ tone: 'blocked' as const, label: 'nicht anwesend / gesperrt (Rhythmus)' }] : []),
                ...(editable
                  ? [
                      { tone: 'ok' as const, label: 'gültiges Ziel' },
                      { tone: 'bad' as const, label: 'Konflikt' },
                      { icon: <Icon name="lock" className="icon" />, label: 'fixiert' },
                    ]
                  : []),
                { label: `${view.cells.length} Blöcke` },
              ]}
            />
          </div>
          {selected && (
            <CellDetails
              cell={selected}
              view={view}
              editable={editable}
              onClose={() => setSelected(null)}
              onChanged={viewQ.reload}
              lastConflicts={conflicts}
              onMove={doMove}
            />
          )}
        </div>
      )}
    </div>
  );
}
