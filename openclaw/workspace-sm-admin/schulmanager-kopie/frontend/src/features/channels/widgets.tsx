/**
 * Startseiten-Kacheln der Kursräume (werden erst bei Bedarf geladen, siehe module.tsx):
 * * Schüler/innen: „Neues Material & fällige Aufgaben“
 * * Lehrkräfte: „Heute: Stunden & Material freigeben“ (Stunden des Tages mit gebundenem Material; Material direkt
 *   zur Stunde freigeben) und „Abgaben zu bewerten“.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatShort, todayISO } from '../../lib/dates';
import { channelsApi, overviewShared } from './api';
import { LessonStatusBadge, StateBadge, SubmissionBadge } from './components';
import { dueText, formatWhen, lessonLine, visibilityText } from './logic';
import type { ChannelDetail, OverviewResponse, TeacherLesson } from './types';
import './channels.css';

function useOverview() {
  return useApi<OverviewResponse>(() => overviewShared(), [], { live: ['channels'] });
}

/** Schüler/innen: neues Material und fällige Aufgaben aus allen Kursräumen. */
export function StudentWidget() {
  const q = useOverview();
  const s = q.data?.student;
  return (
    <section className="card" aria-labelledby="krw-s-h">
      <div className="card-head">
        <h2 id="krw-s-h">Neues Material &amp; fällige Aufgaben</h2>
        <Link to="/kursraeume" className="small">
          Alle Kursräume
        </Link>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && !s && <p className="small muted">Ihr Konto ist keiner Schülerin/keinem Schüler zugeordnet.</p>}
      {s && (
        <div className="stack-sm">
          <div>
            <h3 className="krw-sub">Fällige Aufgaben{s.open_assignments ? ` (${s.open_assignments} offen)` : ''}</h3>
            {s.due.length ? (
              <ul className="krw-list">
                {s.due.map((e) => (
                  <li key={e.item_id}>
                    <Link to={`/kursraeume/${e.channel_id}?tab=aufgaben&aufgabe=${e.item_id}`} className="krw-title">
                      {e.title}
                    </Link>
                    <span className="xsmall muted">
                      {e.channel_title} · <span className={e.overdue ? 'kr-overdue' : ''}>{dueText(e.due_at)}</span>
                    </span>
                    {e.status && <SubmissionBadge status={e.status} label={e.status_label} />}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="small muted" style={{ margin: 0 }}>
                Keine fälligen Aufgaben.
              </p>
            )}
          </div>
          <div>
            <h3 className="krw-sub">Neues Material</h3>
            {s.new_items.length ? (
              <ul className="krw-list">
                {s.new_items.map((e) => (
                  <li key={e.item_id}>
                    <Link to={e.type === 'assignment' ? `/kursraeume/${e.channel_id}?tab=aufgaben&aufgabe=${e.item_id}` : `/kursraeume/${e.channel_id}`} className="krw-title">
                      {e.title}
                    </Link>
                    <span className="xsmall muted">
                      {e.type_label} · {e.channel_title} · {formatWhen(e.available_at, false)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="small muted" style={{ margin: 0 }}>
                Nichts Neues seit deinem letzten Besuch.
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

/** Material eines Kursraums auswählen und zur gegebenen Stunde freigeben (Stunde zuerst gewählt). */
function ReleaseForLessonDialog({ lesson, onClose, onDone }: { lesson: TeacherLesson; onClose: () => void; onDone: () => void }) {
  const q = useApi<ChannelDetail>((signal) => channelsApi.get(lesson.channel_id, signal), [lesson.channel_id]);
  const [chosen, setChosen] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const bound = new Set(lesson.items.map((i) => i.id));
  const candidates = (q.data?.items ?? []).filter((i) => !bound.has(i.id) && i.state !== 'visible');
  const release = async () => {
    if (!chosen.size) {
      setError('Bitte Material auswählen.');
      return;
    }
    try {
      await channelsApi.setVisibility(lesson.channel_id, [...chosen], {
        visibility: 'lesson',
        lesson: { date: lesson.date, lesson_id: lesson.lesson_id, period: lesson.period },
      });
      toast.success(`${chosen.size === 1 ? 'Material' : `${chosen.size} Materialien`} zur Stunde ${lesson.label} freigegeben`);
      onDone();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title="Material zur Stunde freigeben"
      size="lg"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={release} disabled={!chosen.size}>
            Freigeben
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        <p className="small" style={{ margin: 0 }}>
          <strong>{lesson.channel_title}</strong> · {lesson.label}
          {lesson.started ? ' – die Stunde hat begonnen, freigegebenes Material ist sofort sichtbar.' : ' – sichtbar ab Stundenbeginn.'}
        </p>
        {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
        {q.initialLoading && <Loading />}
        {q.data && !candidates.length && (
          <p className="small muted">
            Kein verborgenes oder geplantes Material vorhanden. Legen Sie Material im <Link to={`/kursraeume/${lesson.channel_id}`}>Kursraum</Link> an.
          </p>
        )}
        {candidates.length > 0 && (
          <fieldset className="kr-fieldset">
            <legend>Noch nicht sichtbares Material</legend>
            <ul className="krw-pick">
              {candidates.map((i) => (
                <li key={i.id}>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={chosen.has(i.id)}
                      onChange={(e) =>
                        setChosen((s) => {
                          const next = new Set(s);
                          if (e.target.checked) next.add(i.id);
                          else next.delete(i.id);
                          return next;
                        })
                      }
                    />
                    <span>
                      <strong>{i.title}</strong> <span className="xsmall muted">· {i.type_label}</span>
                      <br />
                      <StateBadge state={i.state} label={i.state_label} /> <span className="xsmall muted">{visibilityText(i)}</span>
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          </fieldset>
        )}
        {error && (
          <p role="alert" className="kr-error">
            {error}
          </p>
        )}
      </div>
    </Modal>
  );
}

/** Lehrkräfte: Stunden des (nächsten) Unterrichtstags mit gebundenem Material und Freigabe-Knopf. */
export function TeacherTodayWidget() {
  const q = useOverview();
  const [release, setRelease] = useState<TeacherLesson | null>(null);
  const t = q.data?.teacher;
  if (q.data?.no_teacher_link) {
    return (
      <section className="card" aria-labelledby="krw-t-h">
        <h2 id="krw-t-h">Kursräume</h2>
        <p className="small" role="status" style={{ margin: 0 }}>
          <Icon name="alert" /> Ihr Konto ist keiner Lehrkraft zugeordnet – bitte wenden Sie sich an das Sekretariat oder die Schulleitung.
        </p>
      </section>
    );
  }
  if (q.data && !t) return null;
  const dayLabel = t?.day ? (t.is_today ? 'Heute' : formatShort(t.day)) : 'Heute';
  return (
    <section className="card" aria-labelledby="krw-t-h">
      <div className="card-head">
        <h2 id="krw-t-h">{dayLabel}: Stunden &amp; Material freigeben</h2>
        <Link to="/kursraeume" className="small">
          Kursräume
        </Link>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {t && !t.lessons.length && <p className="small muted">In den nächsten Tagen haben Sie keinen Unterricht in Ihren Kursen.</p>}
      {t && t.lessons.length > 0 && (
        <>
          {!t.is_today && t.day && t.day !== todayISO() && (
            <p className="xsmall muted" style={{ marginTop: 0 }}>
              Heute keine Stunden mehr – nächster Unterrichtstag.
            </p>
          )}
          <ul className="krw-lessons">
            {t.lessons.map((l) => (
              <li key={`${l.channel_id}-${l.key}`} className={l.ended ? 'ended' : ''}>
                <div className="krw-lesson-main">
                  <span className="krw-time">{l.time || l.period_label}</span>
                  <div style={{ minWidth: 0 }}>
                    <Link to={`/kursraeume/${l.channel_id}`} className="krw-title">
                      {l.channel_title}
                    </Link>
                    <span className="xsmall muted">
                      {lessonLine(l)}
                      {l.ended ? ' · vorbei' : l.started ? ' · läuft' : ''}
                    </span>
                    <LessonStatusBadge status={l.status} changes={l.changes} />
                    {l.items.length > 0 && (
                      <span className="xsmall">
                        <Icon name="check" /> {l.items.map((i) => i.title).join(', ')}
                      </span>
                    )}
                  </div>
                </div>
                {l.status !== 'entfall' && (
                  <button type="button" className="btn btn-sm" onClick={() => setRelease(l)}>
                    <Icon name="calendar" /> Freigeben<span className="sr-only">: Material für {l.channel_title}, {l.label}</span>
                  </button>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
      {release && <ReleaseForLessonDialog lesson={release} onClose={() => setRelease(null)} onDone={() => void overviewShared(true).then(q.reload)} />}
    </section>
  );
}

/** Lehrkräfte: Aufgaben mit Abgaben, die noch eine Rückmeldung brauchen. */
export function TeacherGradeWidget() {
  const q = useOverview();
  const t = q.data?.teacher;
  if (q.data && !t) return null;
  return (
    <section className="card" aria-labelledby="krw-g-h">
      <div className="card-head">
        <h2 id="krw-g-h">Abgaben zu bewerten{t?.to_grade_total ? ` (${t.to_grade_total})` : ''}</h2>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {t && !t.to_grade.length && <p className="small muted">Alle Abgaben sind bewertet.</p>}
      {t && t.to_grade.length > 0 && (
        <ul className="krw-list">
          {t.to_grade.map((e) => (
            <li key={e.item_id}>
              <Link to={`/kursraeume/${e.channel_id}?tab=aufgaben&aufgabe=${e.item_id}`} className="krw-title">
                {e.title}
              </Link>
              <span className="xsmall muted">
                {e.channel_title} · {dueText(e.due_at)}
              </span>
              <span className="badge badge-warning">
                {e.count} {e.count === 1 ? 'Abgabe' : 'Abgaben'}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
