/**
 * Nachschreibtermine als Liste je Klausur – für die Seite `/nachschreiben`, die Startseite (Lehrkraft, Familie) und
 * die Klausurseite. Lehrkräfte der Klausur legen Termine fest, Klassenleitung/Sekretariat entscheiden über das Attest,
 * Familien sehen Termin und Attest-Status.
 */
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { examRoomLink } from '../channels/examRoom';
import { ApiError } from '../../api/client';
import { Abbr, AbbrNamesProvider, AbbrList, SubjectAbbr } from '../../components/Abbr';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useCollection, useSettings } from '../../hooks/useCollection';
import { formatDate, formatLong } from '../../lib/dates';
import { sortBy } from '../../lib/format';
import { abbrNamesOf, makeupsApi, type AppointmentInput, type MakeupAppointment, type MakeupRow, type MakeupSuggestion } from './api';
import { appointmentText, ATTEST_BADGE, attestActionNeeded, groupByExam, needsDate, rowsForSuggestion, sortRows, suggestionKind } from './logic';
import '../students/students.css';

const LIVE = ['makeups', 'exams', 'student_absences', 'student_documents'];

/** Vorschläge der Lehrkraft: eigene Stunden mit den Kindern und freie Zeiten (Rand-/Freistunden) – ein Klick legt den Termin fest. */
function Suggestions({ rows, onTake }: { rows: MakeupRow[]; onTake: (s: MakeupSuggestion, picked: MakeupRow[]) => Promise<void> }) {
  const q = useApi((signal) => makeupsApi.suggestions(rows.map((r) => r.id), signal), [rows.map((r) => r.id).join(',')]);
  const list = q.data?.suggestions ?? [];
  if (q.loading && !q.data) return <Loading />;
  if (q.error || !list.length) return <p className="small muted">Keine passenden Zeiten in den nächsten Wochen gefunden.</p>;
  return (
    <ul className="st-list" aria-label="Terminvorschläge">
      {list.map((s) => {
        const picked = rowsForSuggestion(rows, s);
        return (
          <li key={`${s.date}-${s.start}-${s.kind}-${s.room ?? ''}`} className="st-row">
            <div className="st-row-main">
              <strong>
                {formatLong(s.date)} · {appointmentText(s)}
              </strong>
              <span className="small muted">
                {suggestionKind(s)} · {s.reason}
                {!s.covers_all && ` · gilt für ${picked.map((r) => r.student_name).join(', ')}`}
              </span>
            </div>
            <div className="st-row-side">
              <AsyncButton className="btn btn-sm btn-primary" onClick={() => onTake(s, picked)}>
                Diesen Termin nehmen
              </AsyncButton>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function ScheduleDialog({ rows, existing, onClose, onSaved }: { rows: MakeupRow[]; existing?: MakeupAppointment | null; onClose: () => void; onSaved: () => void }) {
  const toast = useToast();
  const user = useUser();
  const { data: settings } = useSettings();
  const rooms = useCollection('rooms');
  const first = rows[0] as MakeupRow;
  const [a, setA] = useState<AppointmentInput>(() => ({
    date: existing?.date ?? '',
    start: existing?.start ?? Math.min(7, (settings?.periods ?? 10) - 1),
    length: existing?.length ?? Math.max(1, first.exam_length),
    room: existing?.room ?? first.exam_room ?? null,
    note: existing?.note ?? '',
  }));
  const [conflicts, setConflicts] = useState<string[] | null>(null);
  const ownOnly = user.role === 'lehrer';
  const periods = settings?.periods ?? 10;

  const save = async (force: boolean) => {
    if (!a.date) {
      toast.warning('Bitte ein Datum wählen.');
      return;
    }
    try {
      const body = { ...a, room: a.room || null, force };
      if (existing) await makeupsApi.reschedule(existing.id, body);
      else await makeupsApi.schedule(rows.map((r) => r.id), body);
      toast.success('Nachschreibtermin gespeichert');
      onSaved();
      onClose();
    } catch (e) {
      if (e instanceof ApiError && e.isConflict) setConflicts(e.conflicts);
      else toast.error(e, 'Speichern');
    }
  };

  const take = async (s: MakeupSuggestion, picked: MakeupRow[]) => {
    try {
      await makeupsApi.schedule(picked.map((r) => r.id), { date: s.date, start: s.start, length: s.length, room: s.room, note: a.note ?? '' });
      toast.success(`Nachschreibtermin am ${formatDate(s.date)} festgelegt${picked.length < rows.length ? ` (${picked.length} von ${rows.length} Kindern)` : ''}`);
      onSaved();
      onClose();
    } catch (e) {
      if (e instanceof ApiError && e.isConflict) setConflicts(e.conflicts);
      else toast.error(e, 'Speichern');
    }
  };

  return (
    <Modal
      title={existing ? 'Nachschreibtermin ändern' : 'Nachschreibtermin festlegen'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          {conflicts && !ownOnly && (
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
        <p className="small">
          <strong>{first.exam_title || first.label}</strong> vom {formatDate(first.exam_date)} · {rows.map((r) => r.student_name).join(', ')}
        </p>
        {!existing && (
          <section aria-label="Vorschläge">
            <h3 className="small">Vorschläge</h3>
            <Suggestions rows={rows} onTake={take} />
          </section>
        )}
        <div className="form-grid">
          <Field label="Datum" htmlFor="mk-date">
            <input id="mk-date" type="date" value={a.date} onChange={(e) => { setA({ ...a, date: e.target.value }); setConflicts(null); }} />
          </Field>
          <Field label="Beginn (Stunde)" htmlFor="mk-start">
            <select id="mk-start" value={a.start} onChange={(e) => { setA({ ...a, start: Number(e.target.value) }); setConflicts(null); }}>
              {Array.from({ length: periods }, (_, p) => (
                <option key={p} value={p}>
                  {p + 1}. Stunde {settings?.period_times[p] ? `(${settings.period_times[p]})` : ''}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Dauer (Stunden)" htmlFor="mk-len">
            <input id="mk-len" type="number" min={1} max={6} value={a.length} onChange={(e) => { setA({ ...a, length: Math.max(1, Number(e.target.value)) }); setConflicts(null); }} />
          </Field>
          <Field label="Raum" htmlFor="mk-room">
            <select id="mk-room" value={a.room ?? ''} onChange={(e) => { setA({ ...a, room: e.target.value || null }); setConflicts(null); }}>
              <option value="">noch offen</option>
              {sortBy(rooms.data ?? [], (r) => r.id).map((r) => (
                <option key={r.id} value={r.id}>
                  {r.id} {r.name && r.name !== r.id ? `(${r.name})` : ''}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Hinweis" htmlFor="mk-note" className="span-all">
            <input id="mk-note" type="text" value={a.note ?? ''} maxLength={300} onChange={(e) => setA({ ...a, note: e.target.value })} placeholder="z. B. Stift und Taschenrechner mitbringen" />
          </Field>
        </div>
        {conflicts && (
          <Alert kind="warning" title="Konflikte">
            <ul>
              {conflicts.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </Alert>
        )}
      </div>
    </Modal>
  );
}

function AttestBadge({ row }: { row: MakeupRow }) {
  return (
    <span className={`badge ${ATTEST_BADGE[row.attest.state]}`} title={row.source_label}>
      {row.attest.label}
    </span>
  );
}

export function MakeupPanel({ heading = 'Nachschreibtermine', hideWhenEmpty = false }: { heading?: string; hideWhenEmpty?: boolean }) {
  const toast = useToast();
  const q = useApi((signal) => makeupsApi.list({}, signal), [], { live: LIVE });
  const [pick, setPick] = useState<Set<number>>(new Set());
  const [dialog, setDialog] = useState<{ rows: MakeupRow[]; existing?: MakeupAppointment | null } | null>(null);
  const rows = useMemo(() => sortRows(q.data ?? []), [q.data]);
  const groups = useMemo(() => groupByExam(rows), [rows]);
  if (hideWhenEmpty && (q.error || (q.data && !q.data.length))) return null;

  const run = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      toast.success(ok);
      q.reload();
    } catch (e) {
      toast.error(e);
    }
  };
  const toggle = (id: number) =>
    setPick((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  return (
    <section className="card" aria-labelledby="mk-h">
      <div className="card-head">
        <h2 id="mk-h">{heading}</h2>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && !rows.length && <Empty icon="exam">Keine verpassten Klausuren.</Empty>}
      <AbbrNamesProvider names={abbrNamesOf(rows)}>
        {groups.map((g) => {
          const head = g.rows[0] as MakeupRow;
          const todo = needsDate(g.rows);
          const chosen = todo.filter((r) => pick.has(r.id));
          return (
            <div key={g.exam_id} className="stack-sm" style={{ marginTop: 12 }}>
              <div className="row-between">
                <strong>
                  {head.exam_kind === 'test' ? 'Test' : 'Klausur'}:{' '}
                  {head.channel_id ? (
                    <Link to={examRoomLink(head.channel_id, { id: head.exam_id, kind: head.exam_kind, date: head.exam_date })} title="Zum Kursraum">
                      {head.exam_title || head.label}
                    </Link>
                  ) : (
                    head.exam_title || head.label
                  )}{' '}
                  · <SubjectAbbr id={head.subject} />{' '}
                  <span className="small muted">
                    {formatLong(head.exam_date)} · <AbbrList kind="class" ids={head.classes} /> · <AbbrList kind="teacher" ids={head.teachers} />
                  </span>
                </strong>
                {todo.length > 0 && (
                  <button type="button" className="btn btn-sm btn-primary" onClick={() => setDialog({ rows: chosen.length ? chosen : todo })}>
                    <Icon name="plus" /> Termin festlegen{chosen.length ? ` (${chosen.length})` : todo.length > 1 ? ' (alle)' : ''}
                  </button>
                )}
              </div>
              <ul className="st-list">
                {g.rows.map((r) => (
                  <li key={r.id} className={`st-row${attestActionNeeded(r) ? ' st-row-alert' : ''}`}>
                    <div className="st-row-main">
                      {r.can_schedule && r.status === 'offen' && todo.length > 1 && (
                        <label className="check">
                          <input type="checkbox" checked={pick.has(r.id)} onChange={() => toggle(r.id)} /> <strong>{r.student_name}</strong>
                          {r.class_id ? ` (${r.class_id})` : ''}
                        </label>
                      )}
                      {!(r.can_schedule && r.status === 'offen' && todo.length > 1) && (
                        <strong>
                          {r.student_name}
                          {r.class_id ? ` (${r.class_id})` : ''}
                        </strong>
                      )}
                      <span className="small muted">
                        {r.source_label}
                        {' · '}
                        {r.appointment ? (
                          <>
                            Nachschreiben am {formatDate(r.appointment.date)}, {appointmentText(r.appointment)}
                            {r.appointment.students > 1 ? ` · ${r.appointment.students} Personen` : ''}
                            {r.appointment.note ? ` · ${r.appointment.note}` : ''}
                          </>
                        ) : (
                          <Abbr text={r.status_label} full={r.status === 'offen' ? 'Die Lehrkraft der Klausur legt den Nachschreibtermin fest.' : undefined} />
                        )}
                      </span>
                      {attestActionNeeded(r) && r.level === 'family' && (
                        <span className="small">
                          <Link to="/">Attest bei der Krankmeldung einreichen</Link>
                        </span>
                      )}
                    </div>
                    <div className="st-row-side">
                      <AttestBadge row={r} />
                      {r.status === 'erledigt' || r.status === 'entfallen' ? <span className="badge">{r.status_label}</span> : null}
                      {r.can_schedule && r.appointment && r.status === 'angesetzt' && (
                        <>
                          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setDialog({ rows: [r], existing: r.appointment })}>
                            <Icon name="edit" /> Ändern
                          </button>
                          <AsyncButton className="btn btn-ghost btn-sm" onClick={() => run(() => makeupsApi.unschedule((r.appointment as MakeupAppointment).id), 'Termin zurückgenommen')}>
                            Zurücknehmen
                          </AsyncButton>
                        </>
                      )}
                      {r.can_schedule && (r.status === 'offen' || r.status === 'angesetzt') && (
                        <>
                          <AsyncButton className="btn btn-ghost btn-sm" onClick={() => run(() => makeupsApi.patch(r.id, { status: 'erledigt' }), 'Als nachgeschrieben markiert')}>
                            Erledigt
                          </AsyncButton>
                          <AsyncButton className="btn btn-ghost btn-sm" confirm="Nachschreiben entfällt (z. B. Note wird anders ermittelt)?" onClick={() => run(() => makeupsApi.patch(r.id, { status: 'entfallen' }), 'Nachschreiben entfällt')}>
                            Entfällt
                          </AsyncButton>
                        </>
                      )}
                      {r.can_waive && r.status !== 'entfallen' && (
                        <AsyncButton className="btn btn-ghost btn-sm" onClick={() => run(() => makeupsApi.patch(r.id, { attest_waived: !r.attest_waived }), r.attest_waived ? 'Attest wieder erforderlich' : 'Attest nicht erforderlich')}>
                          {r.attest_waived ? 'Attest wieder verlangen' : 'Ohne Attest'}
                        </AsyncButton>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </AbbrNamesProvider>
      {dialog && <ScheduleDialog rows={dialog.rows} existing={dialog.existing} onClose={() => setDialog(null)} onSaved={() => { setPick(new Set()); q.reload(); }} />}
    </section>
  );
}
