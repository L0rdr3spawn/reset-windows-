/**
 * `/klassenbuch` – Klassenbuch: Klasse und Tag wählen, je Stunde die Anwesenheit eintragen (zuerst niemand eingetragen;
 * anwesend / fehlt, „zu spät“ mit Minuten, Notiz je Kind), Thema und Hausaufgabe. Krankmeldungen stehen als Hinweis
 * am Namen. Fehlen und Verspätung landen als offene Fehlzeiten beim Kind und müssen dort entschuldigt werden.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { http } from '../../api/client';
import type { AbsenceLogEvent } from '../../api/types';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useSettings } from '../../hooks/useCollection';
import { useTitle } from '../../hooks/misc';
import { addDays, currentSchoolDay, formatDateTime, formatLong, isValidISO } from '../../lib/dates';
import { HelpTip } from '../../components/HelpTip';
import { AbsenceHistory } from '../students/AbsenceHistory';
import './classes.css';

type Status = 'present' | 'absent' | 'late' | 'left';
type Att = { status: Status; minutes?: number; note?: string; gone?: boolean };
interface RegStudent {
  id: string;
  name: string;
  reported: {
    kind: string;
    kind_label: string;
    status: string;
    status_label: string;
    from_register: boolean;
    /** Meldungsprotokoll: wann/wie (alle Lehrkräfte), wer + Verlauf nur Klassenleitung/Verwaltung */
    absence_id?: number;
    reported_at?: string | null;
    channel_label?: string;
    reported_by_name?: string;
    reported_by_role?: string;
    history?: AbsenceLogEvent[];
  } | null;
  attendance: Att | null;
  /** gültige Förderinformationen (z. B. „Nachteilsausgleich“) */
  support?: string[];
}
interface RegLesson {
  period: number;
  time: string;
  lesson_id: string;
  part: number;
  course_id: string | null;
  subject: string | null;
  subject_name: string | null;
  teacher: string | null;
  teacher_name: string | null;
  kind: string | null;
  note: string;
  cancelled: boolean;
  entry: {
    topic: string;
    homework: string;
    attendance: Record<string, Att>;
    checked_by_name: string;
    checked_at: string | null;
  } | null;
  students: RegStudent[];
  can_edit: boolean;
  /** Stunden des Blocks (Doppelstunde: beide), die gemeinsam erfasst werden */
  block?: number[];
}
interface RegDay {
  class: { id: string; name: string };
  date: string;
  lessons: RegLesson[];
  /** ganzes Klassenbuch (Klassenleitung/Verwaltung); sonst nur eigene Stunden */
  full?: boolean;
}

export const registerApi = {
  day: (classId: string, date: string, signal?: AbortSignal) => http.get<RegDay>('/register/day', { class_id: classId, date }, { signal }),
  classes: (signal?: AbortSignal) => http.get<{ classes: { id: string; name: string; full: boolean }[] }>('/register/classes', undefined, { signal }),
  save: (classId: string, body: unknown) => http.put<RegDay>(`/register/lesson?class_id=${encodeURIComponent(classId)}`, body),
  now: (signal?: AbortSignal) =>
    http.get<{
      date: string | null;
      period?: number;
      lessons: {
        class_id: string;
        lesson_id: string;
        period: number;
        part: number;
        subject: string | null;
        time: string | null;
      }[];
    }>('/register/now', undefined, { signal }),
};

/** Stand einer Zeile: zuerst niemand eingetragen (`status: null`); „zu spät“ heißt anwesend mit Minuten. Bei Doppelstunden:
 * `partial` = nur diese Stunden gefehlt (null = alle), `early` = ab dieser Stunde früher gegangen (null = nein). */
interface Row {
  status: 'present' | 'absent' | null;
  late: boolean;
  minutes: number;
  note: string;
  partial: number[] | null;
  early: number | null;
}

/** Eine Zeile aus den (je Stunde gespeicherten) Eintragungen des Blocks zusammensetzen. */
export function rowFromBlock(atts: (Att | null)[], periods: number[]): Row {
  const have = atts.map((a, i) => (a ? { a, p: periods[i] } : null)).filter((x): x is { a: Att; p: number } => !!x);
  if (!have.length) return { status: null, late: false, minutes: 5, note: '', partial: null, early: null };
  const note = have.find((x) => x.a.note)?.a.note ?? '';
  const absent = have.filter((x) => x.a.status === 'absent').map((x) => x.p);
  const late = have.find((x) => x.a.status === 'late');
  const base = { late: false, minutes: late?.a.minutes ?? 5, note, partial: null, early: null };
  if (absent.length) return { ...base, status: 'absent', partial: absent.length === periods.length ? null : absent };
  const gone = have.find((x) => x.a.status === 'left' && x.a.gone);
  const left = have.find((x) => x.a.status === 'left');
  const next = left ? periods[periods.indexOf(left.p) + 1] : undefined;
  return { ...base, status: 'present', late: !!late, early: gone ? gone.p : next ?? null };
}

/** Beschriftung einer Stundenfolge: „3. Stunde“ bzw. „3.–4. Stunde“ */
export function periodsLabel(periods: number[]): string {
  return periods.length > 1 ? `${periods[0] + 1}.–${periods[periods.length - 1] + 1}. Stunde` : `${periods[0] + 1}. Stunde`;
}

/** Alle Stunden des Blocks (Doppelstunde) einer Stunde, aufsteigend; sonst nur sie selbst. */
export function blockOf(lessons: RegLesson[], lesson: RegLesson): RegLesson[] {
  const periods = lesson.block ?? [lesson.period];
  return periods.map((p) => lessons.find((l) => l.lesson_id === lesson.lesson_id && l.part === lesson.part && l.period === p)).filter((l): l is RegLesson => !!l);
}

export function LessonCard({ classId, date, lesson, blockLessons, onSaved }: { classId: string; date: string; lesson: RegLesson; blockLessons?: RegLesson[]; onSaved: (d: RegDay) => void }) {
  const toast = useToast();
  const lessons = blockLessons?.length ? blockLessons : [lesson];
  const periods = lessons.map((l) => l.period);
  const multi = periods.length > 1;
  const lessonsKey = lessons.map((l) => l.entry?.checked_at ?? '').join('|');
  const initial = useMemo(
    () =>
      Object.fromEntries(
        lesson.students.map((s) => [
          s.id,
          rowFromBlock(
            lessons.map((l) => l.students.find((x) => x.id === s.id)?.attendance ?? null),
            periods,
          ),
        ]),
      ) as Record<string, Row>,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [lesson, lessonsKey],
  );
  const [att, setAtt] = useState(initial);
  const [topic, setTopic] = useState(lesson.entry?.topic ?? '');
  const [homework, setHomework] = useState(lesson.entry?.homework ?? '');
  useEffect(() => {
    setAtt(initial);
    setTopic(lesson.entry?.topic ?? '');
    setHomework(lesson.entry?.homework ?? '');
  }, [initial, lesson.entry]);
  const rows = Object.values(att);
  const missing = rows.filter((a) => a.status === 'absent').length;
  const open = rows.filter((a) => a.status === null).length;
  const set = (id: string, patch: Partial<Row>) => setAtt((a) => ({ ...a, [id]: { ...a[id], ...patch } }));

  const save = async () => {
    try {
      const d = await registerApi.save(classId, {
        date,
        lesson_id: lesson.lesson_id,
        period: lesson.period,
        part: lesson.part,
        ...(multi ? { block: periods } : {}),
        topic,
        homework,
        attendance: Object.entries(att)
          .filter(([, a]) => a.status !== null)
          .map(([student_id, a]) => {
            const early = multi && a.status === 'present' && !a.late && a.early !== null;
            const status: Status = a.status === 'absent' ? 'absent' : early ? 'left' : a.late ? 'late' : 'present';
            return {
              student_id,
              status,
              ...(status === 'late' ? { minutes: a.minutes } : {}),
              ...(status === 'absent' && a.partial?.length ? { missing: a.partial } : {}),
              ...(status === 'left' ? { left_from: a.early } : {}),
              ...(a.note.trim() ? { note: a.note.trim() } : {}),
            };
          }),
      });
      toast.success(`${periodsLabel(periods)} gespeichert`);
      onSaved(d);
    } catch (e) {
      toast.error(e, 'Klassenbuch');
    }
  };

  return (
    <section className={`card stack-sm${lesson.cancelled ? ' kb-cancelled' : ''}`} aria-labelledby={`kb-${lesson.period}-${lesson.part}`}>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h2 id={`kb-${lesson.period}-${lesson.part}`} style={{ margin: 0 }}>
          {periodsLabel(periods)}
          {multi ? ' (Doppelstunde)' : ''} <span className="muted small">{lesson.time}</span> · {lesson.subject_name ?? lesson.subject} · {lesson.teacher_name ?? lesson.teacher}
        </h2>
        <span className="row">
          {lesson.cancelled && <span className="badge badge-warning">entfällt</span>}
          {lesson.kind === 'vertretung' && <span className="badge badge-info">Vertretung</span>}
          {lesson.entry ? (
            <span className="badge badge-success" title={lesson.entry.checked_at ?? ''}>
              eingetragen von {lesson.entry.checked_by_name}
            </span>
          ) : (
            !lesson.cancelled && <span className="badge">noch nicht eingetragen</span>
          )}
        </span>
      </div>
      {lesson.note && (
        <p className="small muted" style={{ margin: 0 }}>
          {lesson.note}
        </p>
      )}
      {!lesson.cancelled && (
        <>
          <p className="xsmall muted" style={{ margin: 0 }}>
            {lesson.students.length} Schüler/innen
            {open ? ` · ${open} noch nicht eingetragen` : ''}
            {missing ? ` · ${missing} fehlen` : ''}
          </p>
          <table className="table kb-table">
            <thead>
              <tr>
                <th>Schüler/in</th>
                <th>Anwesenheit</th>
                <th>Notiz</th>
              </tr>
            </thead>
            <tbody>
              {lesson.students.map((s) => {
                const a = att[s.id];
                const radio = `kb-${lesson.lesson_id}-${lesson.period}-${lesson.part}-${s.id}`;
                return (
                  <tr key={s.id} className={a?.status === 'absent' ? 'kb-away' : undefined}>
                    <td>
                      <Link to={`/fehlzeiten/${encodeURIComponent(s.id)}`}>{s.name}</Link>
                      {(s.support ?? []).map((x) => (
                        <span key={x} className="badge badge-info" style={{ marginLeft: 6 }} title="Details auf der Seite des Kindes">
                          {x}
                        </span>
                      ))}
                      {s.reported && !s.reported.from_register && (
                        <span className="badge badge-warning" style={{ marginLeft: 6 }} title={s.reported.status_label}>
                          {s.reported.kind_label} gemeldet
                        </span>
                      )}
                      {s.reported?.reported_at && (
                        <div className="xsmall muted">
                          {s.reported.from_register ? 'Im Klassenbuch erfasst' : s.reported.kind === 'abwesend' ? 'Abwesend gemeldet' : `${s.reported.kind_label} gemeldet`} am{' '}
                          {formatDateTime(s.reported.reported_at)}
                          {s.reported.reported_by_name ? ` von ${s.reported.reported_by_name}${s.reported.reported_by_role ? ` (${s.reported.reported_by_role})` : ''}` : ''}
                          {s.reported.channel_label ? ` · ${s.reported.channel_label}` : ''}
                        </div>
                      )}
                      <AbsenceHistory events={s.reported?.history} />
                    </td>
                    <td>
                      <span className="row kb-att">
                        <span className="row" role="radiogroup" aria-label={`Anwesenheit ${s.name}`}>
                          <label className="check small">
                            <input type="radio" name={radio} checked={a?.status === 'present'} disabled={!lesson.can_edit} onChange={() => set(s.id, { status: 'present', partial: null })} />{' '}
                            anwesend
                          </label>
                          <label className="check small">
                            <input
                              type="radio"
                              name={radio}
                              checked={a?.status === 'absent'}
                              disabled={!lesson.can_edit}
                              onChange={() => set(s.id, { status: 'absent', late: false, early: null })}
                            />{' '}
                            fehlt
                          </label>
                        </span>
                        <label className="check small">
                          <input
                            type="checkbox"
                            checked={!!a?.late}
                            disabled={!lesson.can_edit || a?.status === 'absent'}
                            onChange={(e) => set(s.id, e.target.checked ? { late: true, status: 'present', early: null } : { late: false })}
                          />{' '}
                          zu spät
                        </label>
                        {a?.late && (
                          <label className="small">
                            <input
                              type="number"
                              min={1}
                              max={600}
                              value={a.minutes}
                              disabled={!lesson.can_edit}
                              aria-label={`Minuten zu spät ${s.name}`}
                              style={{ width: 64 }}
                              onChange={(e) =>
                                set(s.id, {
                                  minutes: Math.max(1, Number(e.target.value) || 1),
                                })
                              }
                            />{' '}
                            Min.
                          </label>
                        )}
                        {multi && a?.status === 'absent' && (
                          <select
                            aria-label={`Gefehlt in ${s.name}`}
                            style={{ width: 'auto' }}
                            value={a.partial?.length === 1 ? String(a.partial[0]) : 'all'}
                            disabled={!lesson.can_edit}
                            onChange={(e) => set(s.id, { partial: e.target.value === 'all' ? null : [Number(e.target.value)] })}
                          >
                            <option value="all">ganze Doppelstunde</option>
                            {periods.map((p) => (
                              <option key={p} value={p}>
                                nur {p + 1}. Stunde
                              </option>
                            ))}
                          </select>
                        )}
                        {multi && a?.status === 'present' && !a.late && (
                          <>
                            <label className="check small">
                              <input
                                type="checkbox"
                                checked={a.early !== null}
                                disabled={!lesson.can_edit}
                                onChange={(e) => set(s.id, { early: e.target.checked ? periods[periods.length - 1] : null })}
                              />{' '}
                              früher gegangen
                            </label>
                            {a.early !== null && (
                              <select
                                aria-label={`Früher gegangen ab ${s.name}`}
                                style={{ width: 'auto' }}
                                value={a.early}
                                disabled={!lesson.can_edit}
                                onChange={(e) => set(s.id, { early: Number(e.target.value) })}
                              >
                                {periods.slice(1).map((p) => (
                                  <option key={p} value={p}>
                                    ab der {p + 1}. Stunde
                                  </option>
                                ))}
                              </select>
                            )}
                          </>
                        )}
                      </span>
                    </td>
                    <td>
                      <input
                        className="kb-note"
                        value={a?.note ?? ''}
                        maxLength={500}
                        disabled={!lesson.can_edit}
                        aria-label={`Notiz ${s.name}`}
                        onChange={(e) => set(s.id, { note: e.target.value })}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="form-grid">
            <div className="field">
              <label htmlFor={`kb-t-${lesson.period}-${lesson.part}`}>Thema der Stunde</label>
              <input id={`kb-t-${lesson.period}-${lesson.part}`} value={topic} disabled={!lesson.can_edit} maxLength={2000} onChange={(e) => setTopic(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor={`kb-h-${lesson.period}-${lesson.part}`}>Hausaufgabe</label>
              <input id={`kb-h-${lesson.period}-${lesson.part}`} value={homework} disabled={!lesson.can_edit} maxLength={2000} onChange={(e) => setHomework(e.target.value)} />
            </div>
          </div>
          {lesson.can_edit ? (
            <div className="row">
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                disabled={!open}
                onClick={() => setAtt((cur) => Object.fromEntries(Object.entries(cur).map(([id, r]) => [id, r.status === null ? { ...r, status: 'present' as const } : r])))}
              >
                Übrige anwesend
              </button>
              <AsyncButton className="btn btn-primary" onClick={save}>
                <Icon name="check" /> Speichern
                {missing ? ` (${missing} fehlen)` : ''}
              </AsyncButton>
            </div>
          ) : (
            <p className="xsmall muted">Eintragen nur durch Lehrkraft und Klassenleitung.</p>
          )}
        </>
      )}
    </section>
  );
}

/** Startseite der Lehrkraft: Anwesenheit der laufenden Stunde direkt erfassen. */
function CurrentClassLesson({ classId, date, lessonId, period, part }: { classId: string; date: string; lessonId: string; period: number; part: number }) {
  const q = useApi((signal) => registerApi.day(classId, date, signal), [classId, date], { live: ['register', 'student_absences'], keepPrevious: true });
  const lesson = q.data?.lessons.find((l) => l.lesson_id === lessonId && l.period === period && l.part === part);
  const blockLessons = lesson ? blockOf(q.data?.lessons ?? [], lesson) : [];
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  if (!lesson) return null;
  return (
    <div className="stack-sm">
      <strong>Klasse {q.data.class.name}</strong>
      <LessonCard classId={classId} date={date} lesson={blockLessons[0] ?? lesson} blockLessons={blockLessons} onSaved={(d) => q.setData(d)} />
    </div>
  );
}

export function CurrentLessonAttendance() {
  const q = useApi((signal) => registerApi.now(signal), [], {
    live: ['timetable', 'substitutions'],
  });
  useEffect(() => {
    const t = window.setInterval(q.reload, 5 * 60 * 1000);
    return () => window.clearInterval(t);
  }, [q.reload]);
  const data = q.data;
  if (!data || !data.date || !data.lessons.length) return null;
  return (
    <section className="card stack-sm" aria-labelledby="kb-now-h">
      <div className="card-head">
        <h2 id="kb-now-h">
          Jetzt: {(data.period ?? 0) + 1}. Stunde – wer ist da?
          <HelpTip>„Fehlt“ und „zu spät“ landen als offene Fehlzeit beim Kind.</HelpTip>
        </h2>
        <Link to="/klassenbuch" className="small">
          Klassenbuch
        </Link>
      </div>
      {data.lessons.map((l) => (
        <CurrentClassLesson key={`${l.class_id}-${l.lesson_id}-${l.part}`} classId={l.class_id} date={data.date as string} lessonId={l.lesson_id} period={l.period} part={l.part} />
      ))}
    </section>
  );
}

export default function RegisterPage() {
  useTitle('Klassenbuch');
  const user = useUser();
  const [params, setParams] = useSearchParams();
  const { data: settings } = useSettings();
  const list = useApi((signal) => registerApi.classes(signal), []);
  const classes = list.data?.classes ?? [];
  const own = classes.find((c) => c.full && user.teacher_id);
  const classId = params.get('klasse') ?? own?.id ?? classes[0]?.id ?? '';
  const rawDate = params.get('datum');
  const date = isValidISO(rawDate) ? (rawDate as string) : currentSchoolDay(new Date(), settings?.days ?? 5);
  const setParam = (k: string, v: string) => {
    const sp = new URLSearchParams(params);
    sp.set(k, v);
    setParams(sp, { replace: true });
  };
  const q = useApi((signal) => (classId ? registerApi.day(classId, date, signal) : Promise.resolve(null)), [classId, date], {
    live: ['register', 'student_absences'],
    keepPrevious: true,
  });
  const data = q.data;

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>
          Klassenbuch{data ? ` ${data.class.name}` : ''}
          <HelpTip>
            „Fehlt“ und „zu spät“ erscheinen als offene Einträge in den Fehlzeiten des Kindes. Entschuldigt sind sie erst, wenn die schriftliche Entschuldigung eingereicht und von der Klassenleitung bestätigt wurde.
          </HelpTip>
        </h1>
      </div>
      <div className="card toolbar">
        <div className="field">
          <label htmlFor="kb-class">Klasse</label>
          <select id="kb-class" value={classId} onChange={(e) => setParam('klasse', e.target.value)}>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <div className="row" role="group" aria-label="Tag wählen">
          <button type="button" className="btn btn-icon" aria-label="Vorheriger Tag" onClick={() => setParam('datum', addDays(date, -1))}>
            <Icon name="chevronLeft" />
          </button>
          <input type="date" aria-label="Datum" value={date} onChange={(e) => isValidISO(e.target.value) && setParam('datum', e.target.value)} />
          <button type="button" className="btn btn-icon" aria-label="Nächster Tag" onClick={() => setParam('datum', addDays(date, 1))}>
            <Icon name="chevronRight" />
          </button>
          <button type="button" className="btn" onClick={() => setParam('datum', currentSchoolDay(new Date(), settings?.days ?? 5))}>
            Heute
          </button>
          <strong>{formatLong(date)}</strong>
        </div>
      </div>
      {list.error ? <ErrorBox error={list.error} onRetry={list.reload} /> : null}
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!data && q.loading && <Loading />}
      {data && data.full === false && (
        <p className="small muted" style={{ margin: 0 }}>
          Nur Ihre eigenen Stunden in dieser Klasse. <HelpTip>Das ganze Klassenbuch und die Übersicht sieht die Klassenleitung.</HelpTip>
        </p>
      )}
      {data && !data.lessons.length && <Alert kind="info">{data.full === false ? 'An diesem Tag haben Sie keinen Unterricht in der Klasse.' : 'An diesem Tag hat die Klasse keinen Unterricht.'}</Alert>}
      {data &&
        data.lessons
          .filter((l) => !l.block || l.block[0] === l.period)
          .map((l) => <LessonCard key={`${l.lesson_id}-${l.period}-${l.part}`} classId={classId} date={date} lesson={l} blockLessons={blockOf(data.lessons, l)} onSaved={(d) => q.setData(d)} />)}
    </div>
  );
}
