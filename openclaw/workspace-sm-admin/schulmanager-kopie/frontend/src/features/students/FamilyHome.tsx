/**
 * Startseiten-Bereich für Schüler/innen und Eltern (je Kind): Wochenplan (Kalenderwoche), Hinweis auf fehlende Atteste
 * mit Weg zum Krankmelden, Klausuren, offene Aufgaben (Eltern; Schüler/innen sehen sie in der Kursraum-Kachel),
 * ungelesene Nachrichten. Krankmelden, Atteste und Dokumente liegen auf der Seite Krankmeldungen
 * (`FamilyAbsences.tsx`), Noten auf `/noten`. (Früher eigene Seite „Meine Übersicht“.)
 */
import { Link } from 'react-router-dom';
import { Icon } from '../../components/Icon';
import { CalendarWeekCard } from '../classes/CalendarWeek';
import { chatsApi } from '../chats/api';
import { messagesApi } from '../messages/api';
import { Alert, Empty, ErrorBox, KindBadge, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { formatDate, formatDateTime, relativeDayLabel } from '../../lib/dates';
import { can } from '../../lib/permissions';
import { studentSelfApi } from './api';
import { useStudentOverview } from './FamilyAbsences';
import './students.css';
import type { StudentOverview, TasksOverview } from './types';
import { ChildSelect } from './useChild';

function TasksCard({ childParam, enabled }: { childParam?: string; enabled: boolean }) {
  const q = useApi<TasksOverview>((signal) => studentSelfApi.tasks(childParam, signal), [childParam], { enabled, live: ['channels'] });
  if (!enabled || q.error) return null;
  const due = q.data?.student?.due ?? q.data?.due ?? [];
  return (
    <section className="card" aria-labelledby="st-tasks-h">
      <div className="card-head">
        <h2 id="st-tasks-h">Offene Aufgaben</h2>
        {q.data?.role !== 'parent' && (
          <Link to="/kursraeume" className="small">
            Kursräume
          </Link>
        )}
      </div>
      {q.initialLoading && <Loading />}
      {q.data?.restricted ? (
        <p className="small muted">Ihr Kind ist volljährig – Aufgaben sehen nur Schüler/in und Lehrkräfte.</p>
      ) : q.data && !due.length ? (
        <p className="small muted">Keine offenen Aufgaben.</p>
      ) : (
        <ul className="st-list">
          {due.slice(0, 8).map((t) => (
            <li key={`${t.channel_id}-${t.item_id}`} className={`st-row${t.overdue ? ' st-row-alert' : ''}`}>
              <div className="st-row-main">
                <strong className="st-title">{t.title}</strong>
                <span className="small muted">{t.channel_title}</span>
              </div>
              <div className="st-row-side">
                {t.due_at && <span className={`badge ${t.overdue ? 'badge-danger' : 'badge-warning'}`}>bis {formatDateTime(t.due_at)}</span>}
                {t.status_label && <span className="badge">{t.status_label}</span>}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function MessagesCard({ ov }: { ov: StudentOverview }) {
  const user = useUser();
  const enabled = can(user, 'messages.use');
  const inbox = useApi((signal) => messagesApi.list({ folder: 'inbox', unread: true, limit: 6 }, signal), [user.id], { enabled, live: ['messages'] });
  const chats = useApi((signal) => chatsApi.list(signal), [user.id], { enabled, live: ['chats'] });
  if (!enabled) return null;
  const items = inbox.data?.items ?? [];
  const newChats = (chats.data?.chats ?? []).filter((c) => c.unread > 0 && !c.muted);
  const loading = !inbox.data && !chats.data;
  return (
    <section className="card" aria-labelledby="st-msg-h">
      <div className="card-head">
        <h2 id="st-msg-h">Nachrichten</h2>
        <Link to="/nachrichten" className="small">
          Zu den Nachrichten
        </Link>
      </div>
      {loading && <Loading />}
      {!loading && !items.length && !newChats.length && <p className="small muted">Keine ungelesenen Nachrichten.</p>}
      {(items.length > 0 || newChats.length > 0) && (
        <ul className="st-list">
          {items.map((c) => (
            <li key={`p${c.id}`} className="st-row">
              <div className="st-row-main">
                <Link to={`/nachrichten/b/${c.id}`}>
                  <strong>{c.kind === 'direct' ? c.participants[0]?.name ?? c.title : c.title}</strong>
                </Link>
                <span className="small muted">{[c.subject, c.last_message?.preview].filter(Boolean).join(' – ')}</span>
              </div>
              <div className="st-row-side">
                <span className="badge badge-primary">{c.unread} neu</span>
              </div>
            </li>
          ))}
          {newChats.map((c) => (
            <li key={`c${c.id}`} className="st-row">
              <div className="st-row-main">
                <Link to={`/nachrichten/c/${c.id}`}>
                  <strong>{c.title}</strong>
                </Link>
                <span className="small muted">{c.kind === 'group' ? 'Gruppe' : 'Chat'} · {c.last?.sender_name ? `von ${c.last.sender_name}` : 'neue Nachricht'}</span>
              </div>
              <div className="st-row-side">
                <span className="badge badge-primary">{c.unread} neu</span>
              </div>
            </li>
          ))}
        </ul>
      )}
      {ov.class_teacher && (
        <div className="row" style={{ marginTop: 8 }}>
          <Link to={`/nachrichten/neu?lehrkraft=${encodeURIComponent(ov.class_teacher.id)}`} className="btn btn-sm">
            <Icon name="user" /> Klassenleitung ({ov.class_teacher.name}) schreiben
          </Link>
        </div>
      )}
    </section>
  );
}

/** Bereich für Schüler/innen und Eltern auf der Startseite. */
export default function FamilyHome() {
  const { q, parent, child, setChild, kids } = useStudentOverview();
  const ov = q.data;

  return (
    <div className="st-page">
      {parent && (
        <div className="row-between">
          <span />
          <ChildSelect kids={ov?.children ?? kids} value={ov?.student.id ?? child} onChange={setChild} />
        </div>
      )}
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {ov && (
        <div className="stack">
          <p className="small muted">
            {ov.student.name} · Klasse {ov.student.class_id}
            {ov.student.class_name && ov.student.class_name !== ov.student.class_id ? ` (${ov.student.class_name})` : ''}
            {ov.student.adult ? ' · volljährig' : ''}
            {ov.class_teacher ? ` · Klassenleitung: ${ov.class_teacher.name}` : ''}
          </p>
          {ov.attest_missing > 0 && (
            <Alert
              kind="warning"
              title={ov.attest_missing === 1 ? 'Ein Attest fehlt' : `${ov.attest_missing} Atteste fehlen`}
              action={
                <Link className="btn btn-sm" to="/krankmeldungen">
                  Zu den Krankmeldungen
                </Link>
              }
            >
              Ab {ov.sick_note_after_days} Schultagen Krankheit braucht die Schule ein ärztliches Attest.
            </Alert>
          )}
          <div className="grid grid-2 st-grid" style={{ gridAutoFlow: 'dense' }}>
            <div style={{ gridColumn: '1 / -1' }}>
              <CalendarWeekCard key={ov.student.id} kind="student" refId={ov.student.id} title={ov.student.name} />
            </div>
            <section className="card" aria-labelledby="st-exams-h">
              <div className="card-head">
                <h2 id="st-exams-h">Klausuren &amp; Arbeiten (3 Wochen)</h2>
                <Link to="/klausuren" className="small">
                  Alle Klausuren
                </Link>
              </div>
              {ov.exams.length ? (
                <ul className="st-list">
                  {ov.exams.map((e) => (
                    <li key={e.id} className="st-row">
                      <div className="st-row-main">
                        <strong>{e.title || 'Klassenarbeit'}</strong>
                        <span className="small muted">
                          {formatDate(e.date)} · {e.start + 1}.{e.length > 1 ? `–${e.start + e.length}.` : ''} Std.{e.subject ? ` · ${e.subject}` : ''}
                          {e.room ? ` · Raum ${e.room}` : ''}
                        </span>
                      </div>
                      <div className="st-row-side">
                        <KindBadge kind="klausur" compact />
                        <span className="badge">{relativeDayLabel(e.date, ov.today)}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <Empty icon="exam">Keine Klausuren in den nächsten drei Wochen.</Empty>
              )}
            </section>
            <TasksCard childParam={parent ? child : undefined} enabled={parent} />
            <MessagesCard ov={ov} />
          </div>
          <p className="small muted" style={{ margin: 0 }}>
            <Icon name="medical" /> Krank melden, Atteste &amp; Dokumente: <Link to="/krankmeldungen">Krankmeldungen</Link> · Noten: <Link to="/noten">Noten</Link>
          </p>
        </div>
      )}
    </div>
  );
}
