import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { absences as absApi, overrides as ovApi, substitutions as subApi } from '../api/endpoints';
import type { Absence, AbsenceKind, AbsencePreview, Candidate, DayPlan, Entry, Override, TeacherStat } from '../api/types';
import { AbsentTeachersCard } from '../components/AbsentTeachersCard';
import { EntryTable } from '../components/EntryTable';
import { DateNav } from '../components/DateNav';
import { HelpTip } from '../components/HelpTip';
import { Icon } from '../components/Icon';
import { Modal } from '../components/Modal';
import { SearchSelect, type SelectOption } from '../components/SearchSelect';
import { Alert, AsyncButton, Empty, ErrorBox, Field, KindBadge, Loading, SegmentedControl } from '../components/ui';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { useCollection, useIndex, useSettings } from '../hooks/useCollection';
import { useTitle } from '../hooks/misc';
import { currentSchoolDay, dateRangeLabel, isValidISO } from '../lib/dates';
import { sortBy } from '../lib/format';
import { can } from '../lib/permissions';
import {
  ABSENCE_REASON_FIELD,
  classAbsenceRows,
  filterClassRows,
  filterEntries,
  KIND_ORDER,
  kindInfo,
  statRows,
  statsWeek,
  withoutClassAbsences,
} from '../lib/substitution';
import { NoPlanNotice } from '../components/PlanNotice';
import { useAllowedRefs } from '../features/teacher/hooks';
import { allowedIds, filterAllowed } from '../features/teacher/scope';
import { isScopedTeacher } from '../features/teacher/windows';

const ABS_KIND_LABEL: Record<AbsenceKind, string> = { teacher: 'Lehrkraft', class: 'Klasse', room: 'Raum', lesson: 'Unterricht entfällt' };

/** Anzeigename: bei „Unterricht entfällt“ die Kursbezeichnung (`ref_name` vom Server) statt der Kurs-ID. */
function absenceName(a: Absence): string {
  return a.kind === 'lesson' ? (a as Absence & { ref_name?: string }).ref_name || a.ref : a.ref;
}

// ---------------------------------------------------------------- Abwesenheit erfassen

/** Vorschauzeile im Dialog: Ferien ohne Wirkung bzw. Zahl der betroffenen Stunden. */
function previewText(p: AbsencePreview): string {
  const free = p.free_names.length ? p.free_names.join(', ') : 'Ferien';
  if (p.school_days === 0) {
    return p.free_days > 0 ? `Der Zeitraum liegt in den ${free} – keine Stunden betroffen.` : 'Der Zeitraum liegt an unterrichtsfreien Tagen – keine Stunden betroffen.';
  }
  const days = `${p.school_days} ${p.school_days === 1 ? 'Schultag' : 'Schultage'}`;
  const skipped = p.free_days > 0 ? `, ${p.free_days} ${p.free_days === 1 ? 'Tag' : 'Tage'} unterrichtsfrei (${free})` : '';
  if (p.affected === null) return `${days}${skipped}.`;
  if (p.affected === 0) return `Keine Stunden betroffen (${days}${skipped}).`;
  return `${p.affected} ${p.affected === 1 ? 'Eintrag' : 'Einträge'} betroffen (${days}${skipped}).`;
}

export function AbsenceModal({ date, onClose, initial }: { date: string; onClose: () => void; initial?: Absence }) {
  const toast = useToast();
  const { data: settings } = useSettings();
  const teachers = useCollection('teachers');
  const classes = useCollection('classes');
  const rooms = useCollection('rooms');
  const [kind, setKind] = useState<AbsenceKind>(initial?.kind ?? 'teacher');
  const [ref, setRef] = useState<string | null>(initial?.ref ?? null);
  const [from, setFrom] = useState(initial?.date_from ?? date);
  const [to, setTo] = useState(initial?.date_to ?? date);
  const [periods, setPeriods] = useState<number[]>(initial?.periods ?? []);
  const [reason, setReason] = useState(initial?.reason ?? '');
  const [busy, setBusy] = useState(false);
  const nPeriods = settings?.periods ?? 10;
  const [preview, setPreview] = useState<AbsencePreview | null>(null);
  const periodsKey = periods.join(',');

  // Vorschau: Ferien bzw. betroffene Stunden vor dem Speichern (ohne Ergebnis bleibt der Dialog wie bisher)
  useEffect(() => {
    setPreview(null);
    if (!ref || !isValidISO(from) || !isValidISO(to) || to < from || kind === 'lesson') return;
    let alive = true;
    const timer = window.setTimeout(() => {
      absApi
        .preview({ kind, ref, date_from: from, date_to: to, periods, reason: '' }, initial?.id)
        .then((r) => alive && setPreview(r))
        .catch(() => undefined);
    }, 350);
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind, ref, from, to, periodsKey, initial?.id]);

  const options: SelectOption[] = useMemo(() => {
    if (kind === 'teacher') return sortBy(teachers.data ?? [], (t) => t.name).map((t) => ({ value: t.id, label: t.name, sub: t.id }));
    if (kind === 'class') return sortBy(classes.data ?? [], (c) => c.name).map((c) => ({ value: c.id, label: c.name, sub: c.site }));
    return sortBy(rooms.data ?? [], (r) => r.id).map((r) => ({ value: r.id, label: r.name || r.id, sub: r.type }));
  }, [kind, teachers.data, classes.data, rooms.data]);

  const save = async () => {
    if (!ref) return;
    setBusy(true);
    try {
      const body = { kind, ref, date_from: from, date_to: to < from ? from : to, periods, reason };
      if (initial) await absApi.update(initial.id, body);
      else await absApi.create(body);
      toast.success('Abwesenheit gespeichert – der Vertretungsplan wird neu berechnet.');
      onClose();
    } catch (e) {
      toast.error(e, 'Abwesenheit');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      title={initial ? 'Abwesenheit bearbeiten' : 'Abwesenheit erfassen'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <button type="button" className="btn btn-primary" disabled={!ref || busy || !isValidISO(from)} onClick={save}>
            {busy ? 'Speichern …' : 'Speichern'}
          </button>
        </>
      }
    >
      <div className="stack">
        <div className="field">
          <span className="field-label">Wer/was ist abwesend?</span>
          <SegmentedControl
            label="Art der Abwesenheit"
            value={kind}
            options={[
              { value: 'teacher', label: 'Lehrkraft' },
              { value: 'class', label: 'Klasse (Exkursion …)' },
              { value: 'room', label: 'Raum (Sperre)' },
            ]}
            onChange={(k) => {
              setKind(k);
              setRef(null);
            }}
          />
        </div>
        <SearchSelect label={ABS_KIND_LABEL[kind]} options={options} value={ref} onChange={setRef} />
        <div className="form-grid">
          <Field label="Von" htmlFor="abs-from">
            <input id="abs-from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
          </Field>
          <Field label="Bis" htmlFor="abs-to">
            <input id="abs-to" type="date" value={to} min={from} onChange={(e) => setTo(e.target.value)} />
          </Field>
        </div>
        <div role="group" aria-labelledby="abs-periods-label">
          <div className="field-label" id="abs-periods-label">
            Stunden <span className="muted small">(keine Auswahl = ganztägig)</span>
          </div>
          <div className="toggle-grid" style={{ marginTop: 4 }}>
            {Array.from({ length: nPeriods }, (_, p) => (
              <button
                key={p}
                type="button"
                className="toggle"
                aria-pressed={periods.includes(p)}
                onClick={() => setPeriods((s) => (s.includes(p) ? s.filter((x) => x !== p) : [...s, p].sort((a, b) => a - b)))}
              >
                {p + 1}.
              </button>
            ))}
          </div>
        </div>
        {preview && (
          <p className="small" role="status">
            {previewText(preview)}
          </p>
        )}
        <Field label={ABSENCE_REASON_FIELD[kind].label} htmlFor="abs-reason" help={ABSENCE_REASON_FIELD[kind].help}>
          <input id="abs-reason" type="text" value={reason} onChange={(e) => setReason(e.target.value)} placeholder={ABSENCE_REASON_FIELD[kind].placeholder} />
        </Field>
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------- Kandidaten / Overrides

function EntryPanel({ entry, date, onClose, overrides, onChanged }: { entry: Entry; date: string; onClose: () => void; overrides: Override[]; onChanged: () => void }) {
  const toast = useToast();
  const rooms = useCollection('rooms');
  const teachersIdx = useIndex('teachers');
  const [note, setNote] = useState('');
  const [room, setRoom] = useState<string | null>(null);
  const [allPeriods, setAllPeriods] = useState(false);
  const lessonBased = !!entry.lesson_id && entry.kind !== 'aufsicht' && entry.kind !== 'klausur';
  const cands = useApi<Candidate[]>(
    () => subApi.candidates({ date, lesson_id: entry.lesson_id as string, period: entry.period, part: entry.part ?? 0 }),
    [date, entry.lesson_id, entry.period, entry.part],
    { enabled: lessonBased },
  );
  const myOverrides = overrides.filter((o) => o.lesson_id === entry.lesson_id && o.period === entry.period && (o.part ?? 0) === (entry.part ?? 0));
  const length = Number((entry as Entry & { length?: number }).length ?? 1);

  const setOverride = async (action: Override['action'], extra: Partial<Override> = {}) => {
    try {
      await ovApi.create({
        date,
        lesson_id: entry.lesson_id as string,
        period: entry.period,
        part: entry.part ?? 0,
        action,
        teacher: extra.teacher ?? null,
        room: extra.room ?? null,
        note,
        all_periods: allPeriods,
      });
      toast.success('Entscheidung gespeichert');
      onChanged();
    } catch (e) {
      toast.error(e, 'Entscheidung');
    }
  };

  const roomOptions: SelectOption[] = useMemo(
    () => sortBy(rooms.data ?? [], (r) => r.id).map((r) => ({ value: r.id, label: r.name || r.id, sub: [r.type, r.site].filter(Boolean).join(' · ') })),
    [rooms.data],
  );

  return (
    <Modal title={`${entry.period_label || `${entry.period + 1}.`} Std. · ${entry.classes.join(', ')} · ${entry.subject}`} onClose={onClose} variant="drawer">
      <div className="stack">
        <div className="row">
          <KindBadge kind={entry.kind} />
          {entry.warning && <span className="badge badge-warning">bitte prüfen</span>}
          {entry.manual && <span className="badge badge-primary">manuell entschieden</span>}
          {entry.proposed && <span className="badge badge-info">Vorschlag</span>}
        </div>
        {entry.proposed && (
          <Alert
            kind="info"
            title="Automatischer Vorschlag"
            action={
              <AsyncButton
                className="btn btn-primary btn-sm"
                onClick={async () => {
                  try {
                    await subApi.release(date, [entry.id]);
                    toast.success('Vorschlag freigegeben');
                    onChanged();
                  } catch (e) {
                    toast.error(e, 'Freigeben');
                  }
                }}
              >
                <Icon name="check" /> Freigeben
              </AsyncButton>
            }
          />
        )}
        <dl className="kv small">
          <dt>Lehrkraft</dt>
          <dd>
            {entry.teacher ? `${teachersIdx.get(entry.teacher)?.name ?? entry.teacher} (${entry.teacher})` : '–'}
          </dd>
          {entry.substitute && (
            <>
              <dt>Vertretung</dt>
              <dd>
                {teachersIdx.get(entry.substitute)?.name ?? entry.substitute} ({entry.substitute})
              </dd>
            </>
          )}
          <dt>Raum</dt>
          <dd>
            {entry.room ?? '–'}
            {entry.new_room ? ` → ${entry.new_room}` : ''}
          </dd>
          {entry.note && (
            <>
              <dt>Hinweis</dt>
              <dd>{entry.note}</dd>
            </>
          )}
          <dt>Art</dt>
          <dd>{kindInfo(entry.kind).description || kindInfo(entry.kind).label}</dd>
        </dl>

        {myOverrides.length > 0 && (
          <Alert kind="info" title="Manuelle Entscheidung aktiv">
            {myOverrides.map((o) => (
              <div key={o.id} className="row-between">
                <span>
                  {o.action === 'substitute' ? `Vertretung durch ${o.teacher}` : o.action === 'cancel' ? 'Entfall' : o.action === 'keep' ? 'findet statt' : `Raum ${o.room}`}
                  {o.note ? ` – ${o.note}` : ''}
                </span>
                <AsyncButton
                  className="btn btn-sm"
                  onClick={async () => {
                    try {
                      await ovApi.remove(o.id);
                      toast.success('Entscheidung zurückgenommen – automatische Planung gilt wieder.');
                      onChanged();
                    } catch (e) {
                      toast.error(e);
                    }
                  }}
                >
                  <Icon name="undo" /> Zurücknehmen
                </AsyncButton>
              </div>
            ))}
          </Alert>
        )}

        {lessonBased ? (
          <>
            <Field label="Notiz zur Entscheidung (optional)" htmlFor="ov-note">
              <input id="ov-note" type="text" value={note} onChange={(e) => setNote(e.target.value)} placeholder="z. B. Aufgaben liegen im Fach" />
            </Field>
            {length > 1 && (
              <label className="check">
                <input type="checkbox" checked={allPeriods} onChange={(e) => setAllPeriods(e.target.checked)} /> für alle {length} Stunden des Blocks
              </label>
            )}
            <div className="row">
              <AsyncButton className="btn btn-danger btn-sm" onClick={() => setOverride('cancel')}>
                Entfallen lassen
              </AsyncButton>
              <AsyncButton className="btn btn-sm" onClick={() => setOverride('keep')} title="Unterricht findet wie geplant statt (z. B. Lehrkraft doch da)">
                Findet statt
              </AsyncButton>
            </div>
            <div className="row" style={{ alignItems: 'flex-end' }}>
              <div className="grow">
                <SearchSelect label="Raum ändern" options={roomOptions} value={room} onChange={setRoom} />
              </div>
              <AsyncButton className="btn btn-sm" disabled={!room} onClick={() => setOverride('room', { room })}>
                Raum setzen
              </AsyncButton>
            </div>

            <h3 style={{ marginTop: 8 }}>
              Vertretungskandidaten
              <HelpTip>Beste zuerst: frei, Fach, Klassenkenntnis, Springstunde, gleicher Standort, faire Verteilung.</HelpTip>
            </h3>
            {cands.error ? <ErrorBox error={cands.error} onRetry={cands.reload} /> : null}
            {cands.initialLoading && <Loading label="Kandidaten werden berechnet …" />}
            {cands.data && cands.data.length === 0 && <Empty>Keine freien Lehrkräfte gefunden.</Empty>}
            <div>
              {(cands.data ?? []).slice(0, 25).map((c, i) => (
                <div key={c.teacher} className={`candidate${i === 0 && c.free ? ' best' : ''}`}>
                  <div>
                    <div className="row">
                      <strong>{c.name}</strong> <span className="mono small">{c.teacher}</span>
                      {c.qualified && <span className="badge badge-success">Fach</span>}
                      {!c.free && <span className="badge badge-danger">nicht frei</span>}
                      {entry.substitute === c.teacher && <span className="badge badge-primary">aktuell</span>}
                    </div>
                    {c.reasons.length > 0 && (
                      <ul>
                        {c.reasons.map((r, j) => (
                          <li key={j}>{r}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div className="stack-sm" style={{ textAlign: 'right' }}>
                    <span className="score" title="Eignungswert">
                      {Math.round(c.score)}
                    </span>
                    <AsyncButton
                      className="btn btn-primary btn-sm"
                      disabled={!c.free || entry.substitute === c.teacher}
                      onClick={() => setOverride('substitute', { teacher: c.teacher })}
                    >
                      Einsetzen
                    </AsyncButton>
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <p className="muted small">Für diesen Eintrag gibt es keine Kandidatenliste.</p>
        )}
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------- Statistik (faire Verteilung)

function StatsCard({ date, days }: { date: string; days: number }) {
  const [open, setOpen] = useState(false);
  const { from, to } = statsWeek(date, days);
  const q = useApi<TeacherStat[]>(() => subApi.stats(from, to), [from, to], { enabled: open, live: ['substitutions', 'absences', 'overrides', 'duties'] });
  const rows = statRows(q.data ?? []);
  return (
    <section className="card">
      <details className="disclosure" open={open} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
        <summary>Verteilung der Vertretungen in dieser Woche ({dateRangeLabel(from, to)})</summary>
        {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
        {open && q.initialLoading && <Loading />}
        {q.data && rows.length === 0 && <p className="muted small">Keine Vertretungen und Aufsichten in dieser Woche.</p>}
        {rows.length > 0 && (
          <div className="table-wrap" style={{ maxHeight: 360 }}>
            <table className="table table-compact">
              <thead>
                <tr>
                  <th scope="col">Lehrkraft</th>
                  <th scope="col" className="num">
                    Vertretungen
                  </th>
                  <th scope="col" className="num">
                    eigener Unterricht entfallen
                  </th>
                  <th scope="col" className="num">
                    Aufsichten
                  </th>
                  <th scope="col" className="num">
                    Aufsichtsvertretungen
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.teacher}>
                    <td>
                      {r.name} <span className="mono small muted">{r.teacher}</span>
                    </td>
                    <td className="num">{r.substitutions}</td>
                    <td className="num">{r.cancelled_own}</td>
                    <td className="num">{r.duties}</td>
                    <td className="num">{r.supervisions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </details>
    </section>
  );
}

// ---------------------------------------------------------------- Seite

export default function SubstitutionsPage() {
  useTitle('Vertretungsplan');
  const user = useUser();
  const toast = useToast();
  const { data: settings } = useSettings();
  const [params, setParams] = useSearchParams();
  const schoolDays = settings?.days ?? 5;
  const date = isValidISO(params.get('datum')) ? (params.get('datum') as string) : currentSchoolDay(new Date(), schoolDays);
  const site = params.get('standort') ?? '';
  // Lehrkräfte (§9.3): nur eigene Klassen und eigene Einträge – fremde Filterwerte aus der URL ignorieren
  const scoped = isScopedTeacher(user);
  const { allowed } = useAllowedRefs(scoped);
  const ownClasses = allowedIds(allowed, 'class');
  const rawClass = params.get('klasse') ?? '';
  const classId = scoped && ownClasses && !ownClasses.has(rawClass) ? '' : rawClass;
  // Lehrkraft-Filter: der Server schränkt auch dann auf eigene Klassen/Einträge ein (Karte „Abwesende Lehrkräfte“)
  const teacher = params.get('lehrer') ?? '';
  const [text, setText] = useState('');
  const [kinds, setKinds] = useState<string[]>([]);
  const [grouping, setGrouping] = useState<'class' | 'period'>('class');
  const [selected, setSelected] = useState<Entry | null>(null);
  const [absenceModal, setAbsenceModal] = useState<{ initial?: Absence } | null>(null);
  const staff = can(user, 'plans.read_all');
  const editor = can(user, 'substitution.edit');

  const setParam = (key: string, value: string | null) => {
    const sp = new URLSearchParams(params);
    if (value) sp.set(key, value);
    else sp.delete(key);
    setParams(sp, { replace: true });
  };

  const sites = useCollection('sites');
  const classes = useCollection('classes', staff);
  const teachers = useCollection('teachers', staff && !scoped);

  const plan = useApi<DayPlan>(() => subApi.day({ date, site: site || undefined, class_id: classId || undefined, teacher: teacher || undefined }), [date, site, classId, teacher], {
    live: ['substitutions', 'absences', 'overrides', 'timetable', 'holidays', 'exams', 'duties', 'courses'],
    liveDates: [date],
  });
  const absQ = useApi<Absence[]>(() => absApi.list({ from: date, to: date }), [date], { enabled: editor, live: ['absences'] });
  const ovQ = useApi<Override[]>(() => ovApi.list({ date }), [date], { enabled: editor, live: ['overrides'] });

  // Auswahl nach Neuberechnung aktualisieren
  useEffect(() => {
    if (!selected || !plan.data) return;
    const fresh = plan.data.entries.find((e) => e.id === selected.id);
    if (fresh && fresh !== selected) setSelected(fresh);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plan.data]);

  // A-56: „Klasse abwesend“ nur als eine Zeile je gemeldeter Klasse, regulärer Rhythmus gar nicht
  const planEntries = useMemo(() => withoutClassAbsences(plan.data?.entries ?? []), [plan.data]);
  // beim Lehrkraft-Filter nur Klassen, in denen ihr Unterricht wegen der Abwesenheit entfällt (auch für die Zähler)
  const allClassRows = useMemo(
    () => filterClassRows(classAbsenceRows(plan.data?.absent_class_details), { teacher, entries: plan.data?.entries }),
    [plan.data, teacher],
  );
  const entries = useMemo(() => filterEntries(planEntries, { text, kinds }), [planEntries, text, kinds]);
  const classRows = useMemo(() => filterClassRows(allClassRows, { text, kinds }), [allClassRows, text, kinds]);
  const presentKinds = useMemo(
    () => KIND_ORDER.filter((k) => (k === 'klasse_abwesend' ? allClassRows.length > 0 : planEntries.some((e) => e.kind === k))),
    [planEntries, allClassRows],
  );
  const kindCount = (k: string) => (k === 'klasse_abwesend' ? allClassRows.length : planEntries.filter((e) => e.kind === k).length);
  const absentTeachers = plan.data?.absent_teacher_details ?? [];

  const classOptions: SelectOption[] = useMemo(() => {
    const all = sortBy(classes.data ?? [], (c) => c.name).map((c) => ({ value: c.id, label: c.name }));
    return scoped ? filterAllowed(all, allowed, 'class') : all;
  }, [classes.data, scoped, allowed]);
  const teacherOptions: SelectOption[] = useMemo(() => sortBy(teachers.data ?? [], (t) => t.name).map((t) => ({ value: t.id, label: t.name, sub: t.id })), [teachers.data]);

  const p = plan.data;
  const filtersActive = !!(site || classId || teacher);
  const printUrl = `/druck/vertretung?datum=${date}${site ? `&standort=${encodeURIComponent(site)}` : ''}${classId ? `&klasse=${encodeURIComponent(classId)}` : ''}`;

  return (
    <div className="page">
      <div className="page-head">
        <h1>Vertretungsplan</h1>
        <div className="actions">
          {editor && (
            <button type="button" className="btn btn-primary" onClick={() => setAbsenceModal({})}>
              <Icon name="plus" /> Abwesenheit erfassen
            </button>
          )}
          <Link className="btn" to={printUrl} target="_blank" rel="noopener">
            <Icon name="print" /> Drucken
          </Link>
        </div>
      </div>

      <div className="card stack" style={{ marginBottom: 16 }}>
        <DateNav value={date} onChange={(d) => setParam('datum', d)} schoolDays={schoolDays} classId={classId || undefined} weekText={p?.week_info?.week_text} />
        <div className="toolbar" style={{ marginBottom: 0 }}>
          <div className="field wide">
            <label htmlFor="f-text">Suche</label>
            <input id="f-text" type="search" value={text} onChange={(e) => setText(e.target.value)} placeholder="Klasse, Fach, Kürzel, Raum …" />
          </div>
        </div>
        <details className="disclosure" open={filtersActive}>
          <summary>
            Filter und Sortierung{filtersActive ? ' (aktiv)' : ''}{' '}
            {scoped && (
              <HelpTip label="Hilfe zur Ansicht">
                Sie sehen die Änderungen Ihrer Klassen sowie Ihre eigenen Einträge (Sie vertreten, werden vertreten oder haben Aufsicht).
              </HelpTip>
            )}
          </summary>
          <div className="toolbar" style={{ marginTop: 8, marginBottom: 0 }}>
            {(sites.data?.length ?? 0) > 1 && (
              <div className="field">
                <label htmlFor="f-site">Standort</label>
                <select id="f-site" value={site} onChange={(e) => setParam('standort', e.target.value || null)}>
                  <option value="">alle Standorte</option>
                  {(sites.data ?? []).map((st) => (
                    <option key={st.id} value={st.id}>
                      {st.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {staff && (
              <div className="field">
                <SearchSelect label="Klasse" options={classOptions} value={classId || null} onChange={(v) => setParam('klasse', v)} allowClear placeholder="alle Klassen" />
              </div>
            )}
            {staff && !scoped && (
              <div className="field">
                <SearchSelect label="Lehrkraft" options={teacherOptions} value={teacher || null} onChange={(v) => setParam('lehrer', v)} allowClear placeholder="alle Lehrkräfte" />
              </div>
            )}
            {scoped && user.teacher_id && (
              <div className="field">
                <span className="field-label">Einträge</span>
                <label className="check">
                  <input type="checkbox" checked={teacher === user.teacher_id} onChange={(e) => setParam('lehrer', e.target.checked ? (user.teacher_id ?? null) : null)} /> nur meine
                </label>
              </div>
            )}
            <div className="field">
              <span className="field-label">Sortierung</span>
              <SegmentedControl
                label="Sortierung"
                value={grouping}
                options={[
                  { value: 'class', label: 'nach Klasse' },
                  { value: 'period', label: 'nach Stunde' },
                ]}
                onChange={setGrouping}
              />
            </div>
          </div>
        </details>
        {presentKinds.length > 0 && (
          <div className="row" role="group" aria-label="Nach Art filtern">
            <span className="small muted">Arten:</span>
            {presentKinds.map((k) => {
              const on = kinds.includes(k);
              return (
                <button
                  key={k}
                  type="button"
                  className="btn btn-ghost btn-sm"
                  aria-pressed={on}
                  style={{ opacity: kinds.length && !on ? 0.5 : 1, padding: 2 }}
                  onClick={() => setKinds((s) => (on ? s.filter((x) => x !== k) : [...s, k]))}
                >
                  <KindBadge kind={k} /> <span className="small">{kindCount(k)}</span>
                </button>
              );
            })}
            {kinds.length > 0 && (
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setKinds([])}>
                Filter zurücksetzen
              </button>
            )}
          </div>
        )}
      </div>

      {plan.error ? <ErrorBox error={plan.error} onRetry={plan.reload} /> : null}
      {plan.initialLoading && <Loading label="Vertretungsplan wird berechnet …" />}

      {p && (
        <div className="stack">
          {p.holiday && (
            <Alert kind="info" title="Kein Unterricht">
              {p.holiday}
            </Alert>
          )}
          {!p.holiday && <NoPlanNotice plan={p.week_info?.plan} />}
          {editor && p.confirm_mode && (
            <Alert
              kind={(p.proposals ?? 0) > 0 ? 'warning' : 'info'}
              title={(p.proposals ?? 0) > 0 ? `${p.proposals} Vertretungsvorschläge warten auf Freigabe` : 'Bestätigungsmodus: keine offenen Vorschläge'}
              action={
                (p.proposals ?? 0) > 0 ? (
                  <AsyncButton
                    className="btn btn-primary btn-sm"
                    confirm={`Alle ${p.proposals} Vorschläge für ${date} freigeben? Danach sehen Lehrkräfte, Familien und Monitor sie.`}
                    onClick={async () => {
                      try {
                        const r = await subApi.release(date);
                        toast.success(`${r.released} Vorschläge freigegeben`);
                        plan.reload();
                      } catch (e) {
                        toast.error(e, 'Freigeben');
                      }
                    }}
                  >
                    <Icon name="check" /> Alle freigeben
                  </AsyncButton>
                ) : undefined
              }
            />
          )}
          <AbsentTeachersCard details={absentTeachers} selected={teacher} onSelect={(t) => setParam('lehrer', t)} date={date} />
          {p.warnings.length > 0 &&
            (p.warnings.length <= 3 ? (
              <Alert kind="warning" title={`${p.warnings.length} Warnung${p.warnings.length === 1 ? '' : 'en'}`}>
                <ul>
                  {p.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </Alert>
            ) : (
              <details className="disclosure">
                <summary>{p.warnings.length} Warnungen</summary>
                <ul className="warning-list small">
                  {p.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </details>
            ))}
          {!p.holiday && entries.length === 0 && classRows.length === 0 && (
            <Empty icon="checkCircle">Keine Änderungen{text || kinds.length || teacher ? ' für diesen Filter' : ''}.</Empty>
          )}
          {(entries.length > 0 || classRows.length > 0) && (
            <EntryTable
              entries={entries}
              classAbsences={classRows}
              grouped={grouping === 'class'}
              onSelect={editor ? setSelected : undefined}
              selectedId={selected?.id}
              caption={`Vertretungsplan ${date}`}
              showSite={!site && (sites.data?.length ?? 0) > 1}
              shortNotes
            />
          )}
          {editor && (
            <section className="card" aria-label="Abwesenheiten an diesem Tag">
              <details className="disclosure" open={(absQ.data?.length ?? 0) > 0 && (absQ.data?.length ?? 0) <= 6}>
              <summary>Abwesenheiten an diesem Tag ({absQ.data?.length ?? 0})</summary>
              {absQ.error ? <ErrorBox error={absQ.error} onRetry={absQ.reload} /> : null}
              {absQ.data && absQ.data.length === 0 && <p className="muted small">Keine Abwesenheiten erfasst.</p>}
              {absQ.data && absQ.data.length > 0 && (
                <div className="table-wrap">
                  <table className="table table-compact">
                    <thead>
                      <tr>
                        <th scope="col">Art</th>
                        <th scope="col">Wer/was</th>
                        <th scope="col">Zeitraum</th>
                        <th scope="col">Stunden</th>
                        <th scope="col">Grund</th>
                        <th scope="col">
                          <span className="sr-only">Aktionen</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {absQ.data.map((a) => (
                        <tr key={a.id}>
                          <td>{ABS_KIND_LABEL[a.kind] ?? a.kind}</td>
                          <td>
                            <strong>{absenceName(a)}</strong>
                          </td>
                          <td>{dateRangeLabel(a.date_from, a.date_to)}</td>
                          <td>{a.periods.length ? a.periods.map((x) => x + 1).join(', ') : a.kind === 'lesson' ? 'alle des Kurses' : 'ganztägig'}</td>
                          <td>{a.reason}</td>
                          <td className="actions">
                            {/* „Unterricht entfällt“ wird auf der Klassen-Seite angelegt – hier nur löschen */}
                            {a.kind !== 'lesson' && (
                              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setAbsenceModal({ initial: a })} aria-label={`Abwesenheit ${absenceName(a)} bearbeiten`}>
                                <Icon name="edit" />
                              </button>
                            )}
                            <AsyncButton
                              className="btn btn-ghost btn-sm"
                              confirm={a.kind === 'lesson' ? `„Unterricht entfällt“ für ${absenceName(a)} zurücknehmen?` : `Abwesenheit von ${absenceName(a)} löschen?`}
                              onClick={async () => {
                                try {
                                  await absApi.remove(a.id);
                                  toast.success('Abwesenheit gelöscht');
                                  absQ.reload();
                                } catch (e) {
                                  toast.error(e);
                                }
                              }}
                            >
                              <Icon name="trash" />
                              <span className="sr-only">Abwesenheit {absenceName(a)} löschen</span>
                            </AsyncButton>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              </details>
            </section>
          )}
          {editor && <StatsCard date={date} days={schoolDays} />}
        </div>
      )}

      {selected && (
        <EntryPanel
          entry={selected}
          date={date}
          overrides={ovQ.data ?? []}
          onClose={() => setSelected(null)}
          onChanged={() => {
            ovQ.reload();
            plan.reload();
          }}
        />
      )}
      {absenceModal && (
        <AbsenceModal
          date={date}
          initial={absenceModal.initial}
          onClose={() => {
            setAbsenceModal(null);
            absQ.reload();
          }}
        />
      )}
    </div>
  );
}
