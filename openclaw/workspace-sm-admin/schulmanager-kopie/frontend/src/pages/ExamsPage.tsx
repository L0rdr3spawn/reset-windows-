import { Fragment, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import { exams as examsApi } from '../api/endpoints';
import type { Exam } from '../api/types';
import { AbbrList, AbbrNamesProvider, RoomAbbr, SubjectAbbr } from '../components/Abbr';
import { HelpTip } from '../components/HelpTip';
import { Icon } from '../components/Icon';
import { Modal } from '../components/Modal';
import { SearchSelect, type SelectOption } from '../components/SearchSelect';
import { Alert, AsyncButton, Empty, ErrorBox, Field, Loading } from '../components/ui';
import { ExamLimitsDefaultsCard } from '../components/ExamLimits';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { useCollection, useSettings } from '../hooks/useCollection';
import { useTitle } from '../hooks/misc';
import { addDays, formatLong, isWeekend, todayISO } from '../lib/dates';
import { classDaysOf } from '../lib/weeks';
import { sortBy } from '../lib/format';
import { can, isFamily } from '../lib/permissions';
import { isScopedTeacher } from '../features/teacher/windows';
import { ExamGradesDialog } from '../features/students/GradesPage';
import { ExamHint, useExamHints } from '../features/students/ExamHints';
import { examRoomLink } from '../features/channels/examRoom';
import { MakeupPanel } from '../features/makeups/MakeupPanel';

/** `can_edit` liefert der Server je Klausur (Lehrkräfte: nur eigene Kurse). */
type ExamRow = Exam & { can_edit?: boolean };

/** Raum der Klausur: eigener Raum, sonst der Raum der Unterrichtsstunde, sonst „noch offen“. */
export function examRoom(e: Pick<Exam, 'room' | 'room_lesson'>): { room: string | null; own: boolean } {
  if (e.room) return { room: e.room, own: true };
  return { room: e.room_lesson ?? null, own: false };
}

/** Stundenplan der Klausurwoche: Familie → Plan des Kindes, Personal → Klassenplan, sonst eigener Lehrerplan. */
export function examTimetableLink(
  user: { role: string; teacher_id?: string | null; student_ids?: string[]; students?: { id: string; class_id?: string | null }[] },
  e: Pick<Exam, 'date' | 'classes' | 'teachers'>,
  readAll: boolean,
): string | null {
  const q = `?datum=${e.date}`;
  if (user.role === 'schueler' || user.role === 'eltern') {
    const kid = (user.students ?? []).find((s) => s.class_id && (e.classes ?? []).includes(s.class_id)) ?? user.students?.[0];
    const sid = kid?.id ?? user.student_ids?.[0];
    return sid ? `/stundenplan/student/${encodeURIComponent(sid)}${q}` : null;
  }
  const cls = e.classes?.[0];
  if (readAll && cls) return `/stundenplan/class/${encodeURIComponent(cls)}${q}`;
  if (user.teacher_id) return `/stundenplan/teacher/${encodeURIComponent(user.teacher_id)}${q}`;
  return null;
}

function ExamDetail({ exam, onClose }: { exam: ExamRow; onClose: () => void }) {
  const user = useUser();
  const { room, own } = examRoom(exam);
  const plan = examTimetableLink(user, exam, can(user, 'plans.read_all'));
  return (
    <AbbrNamesProvider names={exam.names ? { teacher: exam.names.teachers, subject: exam.names.subjects, room: exam.names.rooms, class: exam.names.classes } : null}>
      <Modal
        title={`${exam.kind === 'test' ? 'Test' : 'Klausur'}: ${exam.title || exam.label || ''}`}
        onClose={onClose}
        footer={
          <button type="button" className="btn" onClick={onClose}>
            Schließen
          </button>
        }
      >
        <dl className="kv small">
          <dt>Datum</dt>
          <dd>
            {formatLong(exam.date)}, {exam.start + 1}.{exam.length > 1 ? `–${exam.start + exam.length}.` : ''} Stunde{exam.time ? ` (${exam.time})` : ''}
          </dd>
          <dt>Fach</dt>
          <dd>
            {exam.subjects?.length ? exam.subjects.map((s, i) => <Fragment key={s}>{i > 0 && ', '}<SubjectAbbr id={s} /></Fragment>) : exam.label}
          </dd>
          <dt>Klassen</dt>
          <dd>
            <AbbrList kind="class" ids={exam.classes} empty="–" />
          </dd>
          <dt>Lehrkraft</dt>
          <dd>
            <AbbrList kind="teacher" ids={exam.teachers ?? exam.teacher} empty="–" />
          </dd>
          <dt>Raum</dt>
          <dd>{room ? <><RoomAbbr id={room} />{own ? '' : ' (Raum der Unterrichtsstunde)'}</> : 'Raum noch offen'}</dd>
        </dl>
        <div className="row" style={{ marginTop: 12 }}>
          {exam.channel_id ? (
            <Link className="btn" to={examRoomLink(exam.channel_id, { id: exam.id, kind: exam.kind, date: exam.date })} onClick={onClose}>
              <Icon name="folder" /> Zum Kursraum
            </Link>
          ) : null}
          {plan ? (
            <Link className="btn" to={plan} onClick={onClose}>
              <Icon name="grid" /> Im Stundenplan (Woche der Klausur)
            </Link>
          ) : null}
        </div>
      </Modal>
    </AbbrNamesProvider>
  );
}

/** Unterrichtstage der Klassen eines Kurses (R3: Sa/So möglich, wenn eine Klasse dort Unterricht hat). */
export function examDays(
  classIds: readonly string[],
  classes: readonly { id: string; school_days?: number[] }[] | undefined,
  settings: { days: number; school_days?: number[] } | null | undefined,
): number[] {
  const byId = new Map((classes ?? []).map((c) => [c.id, c]));
  const days = new Set<number>();
  for (const id of classIds) for (const d of classDaysOf(byId.get(id), settings)) days.add(d);
  return days.size ? [...days].sort((a, b) => a - b) : classDaysOf(null, settings);
}

function ExamModal({ initial, onClose }: { initial: Partial<Exam>; onClose: () => void }) {
  const toast = useToast();
  const user = useUser();
  const { data: settings } = useSettings();
  const courses = useCollection('courses');
  const rooms = useCollection('rooms');
  const classList = useCollection('classes');
  const [e, setE] = useState<Partial<Exam>>(() => ({ length: 1, start: 0, title: '', part: null, room: null, kind: 'klausur', ...initial }));
  const [warnings, setWarnings] = useState<string[] | null>(null);
  const [needForce, setNeedForce] = useState(false);
  const ownOnly = user.role === 'lehrer';
  const periods = settings?.periods ?? 10;

  const courseOptions: SelectOption[] = useMemo(() => {
    let list = courses.data ?? [];
    if (ownOnly && user.teacher_id) list = list.filter((c) => c.parts.some((p) => p.teacher === user.teacher_id));
    return sortBy(list, (c) => `${c.classes.join(',')} ${c.label}`).map((c) => ({
      value: c.id,
      label: `${c.classes.join(', ')} · ${c.parts.length > 1 ? c.label || c.id : c.parts[0]?.subject ?? c.id}`,
      sub: c.parts.map((p) => p.teacher).filter(Boolean).join(', '),
      keywords: `${c.label} ${c.parts.map((p) => p.subject).join(' ')}`,
    }));
  }, [courses.data, ownOnly, user.teacher_id]);
  const course = courses.data?.find((c) => c.id === e.course_id);

  const body = () => ({ ...e, id: e.id || undefined }) as Partial<Exam>;

  const check = async () => {
    try {
      setWarnings(await examsApi.check(body()));
    } catch (err) {
      toast.error(err, 'Prüfen');
    }
  };

  const save = async (force = false) => {
    if (!e.course_id || !e.date) {
      toast.warning('Bitte Kurs und Datum angeben.');
      return;
    }
    try {
      const res = e.id ? await examsApi.update(e.id, { ...body(), force }) : await examsApi.create({ ...body(), force });
      if (res.warnings?.length) toast.warning('Gespeichert – mit Hinweisen', res.warnings);
      else toast.success('Klausur gespeichert');
      onClose();
    } catch (err) {
      if (err instanceof ApiError && err.isConflict) {
        setWarnings(err.conflicts);
        setNeedForce(!ownOnly);
      }
      toast.error(err, 'Speichern');
    }
  };

  return (
    <Modal
      title={e.id ? (e.kind === 'test' ? 'Test bearbeiten' : 'Klausur bearbeiten') : 'Klausur oder Test eintragen'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn" onClick={check} disabled={!e.course_id || !e.date}>
            <Icon name="check" /> Konflikte prüfen
          </AsyncButton>
          {needForce && (
            <AsyncButton className="btn btn-danger" onClick={() => save(true)}>
              Trotzdem speichern
            </AsyncButton>
          )}
          <AsyncButton className="btn btn-primary" onClick={() => save(false)}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <SearchSelect
          label="Kurs"
          options={courseOptions}
          value={e.course_id ?? null}
          onChange={(v) => {
            setE({ ...e, course_id: v ?? undefined, part: null });
            setWarnings(null);
          }}
          placeholder="Klasse oder Fach suchen …"
        />
        {course && course.parts.length > 1 && (
          <Field label="Kursteil" htmlFor="ex-part">
            <select id="ex-part" value={e.part ?? ''} onChange={(ev) => setE({ ...e, part: ev.target.value === '' ? null : Number(ev.target.value) })}>
              <option value="">alle Teile</option>
              {course.parts.map((p, i) => (
                <option key={i} value={i}>
                  {p.label || p.subject} {p.teacher ? `(${p.teacher})` : ''}
                </option>
              ))}
            </select>
          </Field>
        )}
        <div className="form-grid">
          <Field label="Datum" htmlFor="ex-date">
            <input
              id="ex-date"
              type="date"
              value={e.date ?? ''}
              onChange={(ev) => {
                setE({ ...e, date: ev.target.value });
                setWarnings(null);
              }}
            />
          </Field>
          <Field label="Beginn (Stunde)" htmlFor="ex-start">
            <select id="ex-start" value={e.start ?? 0} onChange={(ev) => setE({ ...e, start: Number(ev.target.value) })}>
              {Array.from({ length: periods }, (_, p) => (
                <option key={p} value={p}>
                  {p + 1}. Stunde {settings?.period_times[p] ? `(${settings.period_times[p]})` : ''}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Dauer (Stunden)" htmlFor="ex-len">
            <input id="ex-len" type="number" min={1} max={6} value={e.length ?? 1} onChange={(ev) => setE({ ...e, length: Math.max(1, Number(ev.target.value)) })} />
          </Field>
          <Field label="Raum (optional)" htmlFor="ex-room">
            <select id="ex-room" value={e.room ?? ''} onChange={(ev) => setE({ ...e, room: ev.target.value || null })}>
              <option value="">wie Unterricht</option>
              {sortBy(rooms.data ?? [], (r) => r.id).map((r) => (
                <option key={r.id} value={r.id}>
                  {r.id} ({r.type})
                </option>
              ))}
            </select>
          </Field>
          <Field label="Art" htmlFor="ex-kind" hint="Tests zählen nicht zu den Höchstzahlen für Klassenarbeiten. Beides erscheint im Stundenplan.">
            <select id="ex-kind" value={e.kind ?? 'klausur'} onChange={(ev) => setE({ ...e, kind: ev.target.value as 'klausur' | 'test' })}>
              <option value="klausur">Klassenarbeit / Klausur</option>
              <option value="test">Test (angekündigt)</option>
            </select>
          </Field>
          <Field label="Titel" htmlFor="ex-title" className="span-all">
            <input id="ex-title" type="text" value={e.title ?? ''} onChange={(ev) => setE({ ...e, title: ev.target.value })} placeholder="z. B. 2. Klassenarbeit" />
          </Field>
        </div>
        {e.date && isWeekend(e.date, examDays(course?.classes ?? [], classList.data, settings)) && <Alert kind="warning">Kein Unterrichtstag der Klasse.</Alert>}
        {warnings &&
          (warnings.length ? (
            <Alert kind="warning" title="Konflikte / Hinweise">
              <ul>
                {warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </Alert>
          ) : (
            <Alert kind="success" title="Keine Konflikte gefunden." />
          ))}
      </div>
    </Modal>
  );
}

export default function ExamsPage() {
  useTitle('Klausuren');
  const user = useUser();
  const toast = useToast();
  const [from, setFrom] = useState(todayISO());
  const [to, setTo] = useState(addDays(todayISO(), 56));
  const [classId, setClassId] = useState<string | null>(null);
  const [edit, setEdit] = useState<Partial<Exam> | null>(null);
  const [gradesFor, setGradesFor] = useState<string | null>(null);
  const [detail, setDetail] = useState<ExamRow | null>(null);
  const [params, setParams] = useSearchParams();
  const wantedId = params.get('klausur');
  const wantedDate = params.get('datum');
  const staff = can(user, 'plans.read_all');
  const classes = useCollection('classes', staff);
  const editor = can(user, 'exam.edit');
  const q = useApi(() => examsApi.list({ from, to, class_id: classId ?? undefined }), [from, to, classId], { live: ['exams', 'courses'] });
  const hints = useExamHints(from, to);

  // Link von Startseite/Kalender: `?klausur=ID&datum=…` öffnet die Details (Zeitraum wird passend gesetzt)
  useEffect(() => {
    if (wantedDate && /^\d{4}-\d{2}-\d{2}$/.test(wantedDate) && (wantedDate < from || wantedDate > to)) {
      setFrom(wantedDate);
      setTo(addDays(wantedDate, 28));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wantedDate]);
  useEffect(() => {
    if (!wantedId || !q.data) return;
    const hit = (q.data as ExamRow[]).find((x) => x.id === wantedId);
    if (hit) {
      setDetail(hit);
      const sp = new URLSearchParams(params);
      sp.delete('klausur');
      sp.delete('datum');
      setParams(sp, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wantedId, q.data]);
  const examNames = (q.data?.[0] as ExamRow | undefined)?.names;

  const byDate = useMemo(() => {
    const m = new Map<string, Exam[]>();
    for (const e of q.data ?? []) {
      const list = m.get(e.date) ?? [];
      list.push(e);
      m.set(e.date, list);
    }
    return [...m.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [q.data]);

  const classOptions = useMemo(() => sortBy(classes.data ?? [], (c) => c.name).map((c) => ({ value: c.id, label: c.name })), [classes.data]);

  return (
    <div className="page">
      <div className="page-head">
        <h1>
          Klausuren & Klassenarbeiten
          {isFamily(user) && <HelpTip>Angezeigt werden die Klausuren Ihrer Kurse.</HelpTip>}
          {isScopedTeacher(user) && <HelpTip>Angezeigt werden die Klausuren Ihrer Klassen und Kurse. Eintragen und ändern können Sie Klausuren Ihrer eigenen Kurse.</HelpTip>}
        </h1>
        {editor && (
          <button type="button" className="btn btn-primary" onClick={() => setEdit({ date: todayISO() })}>
            <Icon name="plus" /> Klausur eintragen
          </button>
        )}
      </div>
      <div className="toolbar card" style={{ padding: 12 }}>
        <Field label="Von" htmlFor="ex-from">
          <input id="ex-from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        </Field>
        <Field label="Bis" htmlFor="ex-to">
          <input id="ex-to" type="date" value={to} min={from} onChange={(e) => setTo(e.target.value)} />
        </Field>
        {staff && (
          <div className="field">
            <SearchSelect label="Klasse" options={classOptions} value={classId} onChange={setClassId} allowClear placeholder="alle Klassen" />
          </div>
        )}
      </div>
      {staff && (can(user, 'settings.edit') || can(user, 'exam.edit')) && <ExamLimitsDefaultsCard canEdit={can(user, 'settings.edit')} />}
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && q.data.length === 0 && <Empty icon="exam">Keine Klausuren im Zeitraum.</Empty>}
      {byDate.length > 0 && (
        <AbbrNamesProvider names={examNames ? { teacher: examNames.teachers, subject: examNames.subjects, room: examNames.rooms, class: examNames.classes } : null}>
        <div className="table-wrap">
          <table className="table">
            <caption className="sr-only">Klausuren</caption>
            <thead>
              <tr>
                <th scope="col">Stunde</th>
                <th scope="col">Klassen</th>
                <th scope="col">Kurs / Fach</th>
                <th scope="col">Titel</th>
                <th scope="col">Lehrkraft</th>
                <th scope="col">Raum</th>
                {editor && (
                  <th scope="col">
                    <span className="sr-only">Aktionen</span>
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {byDate.map(([date, list]) => (
                <Fragment key={date}>
                  <tr>
                    <th colSpan={editor ? 7 : 6} scope="colgroup" style={{ position: 'static', background: 'var(--surface-3)', color: 'var(--text)' }}>
                      {formatLong(date)}
                    </th>
                  </tr>
                  {(list as ExamRow[]).map((e) => (
                    <tr
                      key={e.id}
                      onClick={(ev) => {
                        if ((ev.target as HTMLElement).closest('button, a, input, select, .abbr')) return;
                        setDetail(e);
                      }}
                    >
                      <td className="nowrap">
                        {e.start + 1}.{e.length > 1 ? `–${e.start + e.length}.` : ''} {e.time && <span className="xsmall muted">{e.time}</span>}
                      </td>
                      <td>
                        <AbbrList kind="class" ids={e.classes} />
                      </td>
                      <td>
                        {e.subjects?.length ? e.subjects.map((s, i) => <Fragment key={s}>{i > 0 && '/'}<SubjectAbbr id={s} /></Fragment>) : e.subject || ''}{' '}
                        <span className="small muted">{e.label}</span>
                      </td>
                      <td>
                        {e.kind === 'test' && <span className="badge">Test</span>}{' '}
                        {e.channel_id ? (
                          <>
                            <Link className="btn btn-ghost btn-sm" to={examRoomLink(e.channel_id, { id: e.id, kind: e.kind, date: e.date })} title="Zum Kursraum">
                              {e.title || e.label}
                            </Link>{' '}
                            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setDetail(e)} aria-label={`Details zu ${e.title || e.label}`}>
                              Details
                            </button>
                          </>
                        ) : (
                          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setDetail(e)} aria-label={`Details zu ${e.title || e.label}`}>
                            {e.title || e.label}
                          </button>
                        )}
                        <ExamHint students={hints[e.id]} />
                      </td>
                      <td>
                        <AbbrList kind="teacher" ids={e.teachers ?? e.teacher} />
                      </td>
                      <td>
                        {(() => {
                          const r = examRoom(e);
                          return r.room ? (
                            <span title={r.own ? undefined : 'Raum der Unterrichtsstunde'}>
                              <RoomAbbr id={r.room} />
                              {r.own ? '' : '*'}
                            </span>
                          ) : (
                            <span className="muted">Raum noch offen</span>
                          );
                        })()}
                      </td>
                      {editor && e.can_edit === false && <td />}
                      {editor && e.can_edit !== false && (
                        <td className="actions">
                          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setGradesFor(e.id)} title="Noten eintragen">
                            Noten
                          </button>
                          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEdit(e)} aria-label={`Klausur ${e.title} bearbeiten`}>
                            <Icon name="edit" />
                          </button>
                          <AsyncButton
                            className="btn btn-ghost btn-sm"
                            confirm="Klausur löschen?"
                            onClick={async () => {
                              try {
                                await examsApi.remove(e.id);
                                toast.success('Klausur gelöscht');
                                q.reload();
                              } catch (err) {
                                toast.error(err);
                              }
                            }}
                          >
                            <Icon name="trash" />
                            <span className="sr-only">löschen</span>
                          </AsyncButton>
                        </td>
                      )}
                    </tr>
                  ))}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
        </AbbrNamesProvider>
      )}
      {byDate.length > 0 && <p className="xsmall muted">* Raum der Stunde</p>}
      <MakeupPanel hideWhenEmpty heading="Nachschreibtermine" />
      {detail && <ExamDetail exam={detail} onClose={() => setDetail(null)} />}
      {edit && (
        <ExamModal
          initial={edit}
          onClose={() => {
            setEdit(null);
            q.reload();
          }}
        />
      )}
      {gradesFor && <ExamGradesDialog examId={gradesFor} onClose={() => setGradesFor(null)} />}
    </div>
  );
}
