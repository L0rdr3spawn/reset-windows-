/**
 * Bereich „Klasse“ (Startansicht des Klassenraums): Regelplan der Klasse, Termine/Elternabende, angeheftete Infokarten
 * (gepflegt von der Klassenleitung und den Lehrkräften des Klassenraums) und Ansprechpersonen. Lesen dürfen alle
 * Mitglieder inkl. Eltern (nur lesend); die Infokarten sind gewöhnliche Textseiten (`info_card`) des Klassenraums.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { Abbr } from '../../components/Abbr';
import { FileList } from '../../components/FileList';
import { FileUpload } from '../../components/FileUpload';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { TimetableGrid } from '../../components/TimetableGrid';
import { useSchoolYear, WeekNav } from '../../components/WeekNav';
import { Alert, AsyncButton, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatShort, mondayOf, todayISO, weekdayIndex } from '../../lib/dates';
import { isCurrentWeek } from '../../lib/weeks';
import { can, isFamily } from '../../lib/permissions';
import { AbsenceHistory, reportLine } from '../students/AbsenceHistory';
import { channelsApi } from './api';
import { eventWhen, infoCards, messageLink, moveCard, splitContacts } from './classInfo';
import { Markdown } from './MarkdownView';
import type { ChannelDetail, ClassContact, ClassEvent, ClassOverview, Item } from './types';
import { confirmAsk } from '../../lib/confirm';

// ------------------------------------------------------------------ Regelplan

function PlanSection({ detail, overview }: { detail: ChannelDetail; overview: ClassOverview | undefined }) {
  const id = detail.channel.id;
  const [day, setDay] = useState(() => mondayOf(todayISO()));
  const { year } = useSchoolYear(day);
  const q = useApi((signal) => channelsApi.classPlan(id, day, signal), [id, day], { live: ['timetable', 'classes'] });
  const user = useUser();
  return (
    <section className="card" aria-labelledby="kl-plan-h">
      <div className="card-head">
        <h2 id="kl-plan-h" style={{ fontSize: 'var(--fs-lg)' }}>
          Regelplan der Klasse{' '}
          <HelpTip>
            Der reguläre Stundenplan der Klasse, nur zum Ansehen. Änderungen und Vertretungen stehen im Stundenplan mit Änderungen.
          </HelpTip>
        </h2>
        <WeekNav value={day} onChange={setDay} year={year} info={q.data?.week_info} />
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && (
        <TimetableGrid
          view={q.data}
          compact
          todayIndex={weekdayIndex(todayISO()) < q.data.days.length && isCurrentWeek(day, todayISO()) ? weekdayIndex(todayISO()) : null}
        />
      )}
      <div className="row" style={{ marginTop: 'var(--space-2)' }}>
        {overview?.plan_links.map((l) => (
          <Link key={l.to} className="btn btn-sm" to={l.to}>
            <Icon name="grid" /> {l.label}
          </Link>
        ))}
        {user.role !== 'monitor' && (
          <Link className="btn btn-sm" to="/klausuren">
            <Icon name="exam" /> Klausurplan
          </Link>
        )}
      </div>
    </section>
  );
}

// ------------------------------------------------------------------ Termine / Elternabende

function EventDialog({ channelId, defaultTitle, onClose, onDone }: { channelId: number; defaultTitle: string; onClose: () => void; onDone: () => void }) {
  const [title, setTitle] = useState(defaultTitle);
  const [date, setDate] = useState('');
  const [from, setFrom] = useState('19:00');
  const [to, setTo] = useState('');
  const [location, setLocation] = useState('');
  const [note, setNote] = useState('');
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const save = async () => {
    if (!date) {
      setError('Bitte ein Datum angeben');
      return;
    }
    try {
      await channelsApi.addClassEvent(channelId, { title, date_from: date, time_from: from, time_to: to, location, note });
      toast.success('Termin angelegt');
      onDone();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title="Termin der Klasse anlegen"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        {error && (
          <p role="alert" className="kr-error">
            {error}
          </p>
        )}
        <Field label="Titel" htmlFor="kl-ev-title">
          <input id="kl-ev-title" value={title} maxLength={120} onChange={(e) => setTitle(e.target.value)} />
        </Field>
        <div className="form-grid">
          <Field label="Datum" htmlFor="kl-ev-date">
            <input id="kl-ev-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </Field>
          <Field label="Von" htmlFor="kl-ev-from">
            <input id="kl-ev-from" type="time" value={from} onChange={(e) => setFrom(e.target.value)} />
          </Field>
          <Field label="Bis (optional)" htmlFor="kl-ev-to">
            <input id="kl-ev-to" type="time" value={to} onChange={(e) => setTo(e.target.value)} />
          </Field>
        </div>
        <Field label="Ort (optional)" htmlFor="kl-ev-loc">
          <input id="kl-ev-loc" value={location} maxLength={120} onChange={(e) => setLocation(e.target.value)} />
        </Field>
        <Field label="Hinweis (optional)" htmlFor="kl-ev-note">
          <textarea id="kl-ev-note" rows={3} value={note} maxLength={1000} onChange={(e) => setNote(e.target.value)} />
        </Field>
      </div>
    </Modal>
  );
}

function EventsSection({ channelId, overview, reload }: { channelId: number; overview: ClassOverview; reload: () => void }) {
  const [adding, setAdding] = useState(false);
  const toast = useToast();
  const remove = async (ev: ClassEvent) => {
    if (!(await confirmAsk({ title: 'Termin löschen', message: `Termin „${ev.title}“ löschen?`, confirmLabel: 'Löschen', danger: true }))) return;
    try {
      await channelsApi.deleteClassEvent(channelId, ev.id);
      toast.success('Termin gelöscht');
      reload();
    } catch (e) {
      toast.error(e, 'Termin löschen');
    }
  };
  return (
    <section className="card" aria-labelledby="kl-ev-h">
      <div className="card-head">
        <h2 id="kl-ev-h" style={{ fontSize: 'var(--fs-lg)' }}>
          Termine und Elternabende
        </h2>
        {overview.can_add_event && (
          <button type="button" className="btn btn-sm" onClick={() => setAdding(true)}>
            <Icon name="plus" /> Termin anlegen
          </button>
        )}
      </div>
      {overview.events.length === 0 ? (
        <p className="muted small">Keine kommenden Termine für diese Klasse.</p>
      ) : (
        <ul className="kl-list">
          {overview.events.map((ev) => (
            <li key={ev.id} className="kl-event">
              <div>
                <strong>{ev.title}</strong> {ev.parents_evening && <span className="badge badge-info">Eltern</span>}
                <div className="small">{eventWhen(ev)}</div>
                {ev.location && <div className="small muted">{ev.location}</div>}
                {ev.note && <div className="small muted">{ev.note}</div>}
              </div>
              {ev.can_delete && (
                <button type="button" className="btn btn-sm btn-ghost btn-icon" onClick={() => remove(ev)} aria-label={`Termin ${ev.title} löschen`}>
                  <Icon name="trash" />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {adding && <EventDialog channelId={channelId} defaultTitle={overview.default_event_title} onClose={() => setAdding(false)} onDone={reload} />}
    </section>
  );
}

// ------------------------------------------------------------------ Infokarten

function CardDialog({ detail, card, onClose, onDone }: { detail: ChannelDetail; card: Item | null; onClose: () => void; onDone: () => void }) {
  const ch = detail.channel;
  const full = useApi<Item>((signal) => channelsApi.item(ch.id, card?.id ?? 0, signal), [ch.id, card?.id], { enabled: !!card });
  const [title, setTitle] = useState(card?.title ?? '');
  const [body, setBody] = useState<string | null>(card ? null : '');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [preview, setPreview] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const text = body ?? full.data?.body ?? '';
  const save = async () => {
    try {
      if (card) {
        await channelsApi.patchItem(ch.id, card.id, { title, ...(body !== null ? { body } : {}) });
      } else {
        await channelsApi.createItem(ch.id, { type: 'text', title, body: text, attachment_ids: attachments, info_card: true });
      }
      toast.success('Gespeichert');
      onDone();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title={card ? 'Infokarte bearbeiten' : 'Infokarte hinzufügen'}
      size="lg"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save} disabled={!!card && full.loading && body === null}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        {error && (
          <p role="alert" className="kr-error">
            {error}
          </p>
        )}
        <Field label="Titel" htmlFor="kl-card-title" hint="z. B. Kontakt Klassenleitung, Sprechzeiten, Klassensprecher, Materialliste, Regeln">
          <input id="kl-card-title" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />
        </Field>
        <div className="field">
          <div className="row-between">
            <label htmlFor="kl-card-body">Text</label>
            <button type="button" className="btn btn-sm btn-ghost" aria-pressed={preview} onClick={() => setPreview((p) => !p)}>
              {preview ? 'Bearbeiten' : 'Vorschau'}
            </button>
          </div>
          {preview ? (
            <div className="kr-preview">{text.trim() ? <Markdown text={text} /> : <span className="muted small">Noch kein Text.</span>}</div>
          ) : (
            <textarea id="kl-card-body" rows={8} value={text} maxLength={detail.limits.max_body} onChange={(e) => setBody(e.target.value)} />
          )}
          <span className="hint">Formatierung: **fett**, *kursiv*, - Liste, [Linktext](https://…)</span>
        </div>
        {!card && <FileUpload purpose="channel_material" compact label="Anhänge hinzufügen" maxFiles={detail.limits.max_attachments} onChange={(f) => setAttachments(f.map((x) => x.id))} />}
      </div>
    </Modal>
  );
}

function InfoCard({
  detail,
  card,
  first,
  last,
  canEdit,
  onEdit,
  onDelete,
  onMove,
}: {
  detail: ChannelDetail;
  card: Item;
  first: boolean;
  last: boolean;
  canEdit: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onMove: (dir: -1 | 1) => void;
}) {
  const q = useApi<Item>((signal) => channelsApi.item(detail.channel.id, card.id, signal, detail.child?.id), [detail.channel.id, card.id, detail.child?.id, card.updated_at]);
  return (
    <article className="kl-card">
      <div className="row-between">
        <h3 style={{ margin: 0, fontSize: 'var(--fs-md)' }}>{card.title}</h3>
        {canEdit && (
          <span className="row">
            <button type="button" className="btn btn-sm btn-ghost btn-icon" disabled={first} onClick={() => onMove(-1)} aria-label={`${card.title} nach oben`}>
              <span aria-hidden="true">↑</span>
            </button>
            <button type="button" className="btn btn-sm btn-ghost btn-icon" disabled={last} onClick={() => onMove(1)} aria-label={`${card.title} nach unten`}>
              <span aria-hidden="true">↓</span>
            </button>
            <button type="button" className="btn btn-sm btn-ghost btn-icon" onClick={onEdit} aria-label={`${card.title} bearbeiten`}>
              <Icon name="edit" />
            </button>
            <button type="button" className="btn btn-sm btn-ghost btn-icon" onClick={onDelete} aria-label={`${card.title} löschen`}>
              <Icon name="trash" />
            </button>
          </span>
        )}
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.data?.body ? <Markdown text={q.data.body} /> : q.initialLoading ? <Loading /> : null}
      {q.data && q.data.attachments.length > 0 && <FileList files={q.data.attachments} label="Anhänge" />}
    </article>
  );
}

function InfoSection({ detail, reload }: { detail: ChannelDetail; reload: () => void }) {
  const cards = infoCards(detail.items);
  const [dialog, setDialog] = useState<{ card: Item | null } | null>(null);
  const toast = useToast();
  const canAdd = detail.permissions.manage;
  const guard = async (what: string, fn: () => Promise<unknown>) => {
    try {
      await fn();
      reload();
    } catch (e) {
      toast.error(e, what);
    }
  };
  return (
    <section className="card" aria-labelledby="kl-info-h">
      <div className="card-head">
        <h2 id="kl-info-h" style={{ fontSize: 'var(--fs-lg)' }}>
          Allgemeine Infos{' '}
          <HelpTip>Angeheftete Infokarten der Klassenleitung und der Lehrkräfte, z. B. Kontakt, Sprechzeiten, Klassensprecher, Materialliste und Regeln.</HelpTip>
        </h2>
        {canAdd && (
          <button type="button" className="btn btn-sm" onClick={() => setDialog({ card: null })}>
            <Icon name="plus" /> Infokarte hinzufügen
          </button>
        )}
      </div>
      {cards.length === 0 ? (
        <p className="muted small">{canAdd ? 'Noch keine Infokarten – legen Sie die erste an.' : 'Noch keine Infos eingetragen.'}</p>
      ) : (
        <div className="kl-cards">
          {cards.map((c, i) => (
            <InfoCard
              key={c.id}
              detail={detail}
              card={c}
              first={i === 0}
              last={i === cards.length - 1}
              canEdit={!!c.can_edit && detail.permissions.manage}
              onEdit={() => setDialog({ card: c })}
              onDelete={async () => {
                if (await confirmAsk({ title: 'Infokarte löschen', message: `Infokarte „${c.title}“ löschen?`, confirmLabel: 'Löschen', danger: true })) void guard('Löschen', () => channelsApi.deleteItem(detail.channel.id, c.id));
              }}
              onMove={(dir) =>
                void guard('Verschieben', () => Promise.all(moveCard(cards, c.id, dir).map((p) => channelsApi.patchItem(detail.channel.id, p.id, { position: p.position }))))
              }
            />
          ))}
        </div>
      )}
      {dialog && <CardDialog detail={detail} card={dialog.card} onClose={() => setDialog(null)} onDone={reload} />}
    </section>
  );
}

// ------------------------------------------------------------------ Ansprechpersonen

function ContactRow({ c, messaging }: { c: ClassContact; messaging: boolean }) {
  return (
    <li className="kl-contact">
      <div>
        <strong>
          <Abbr text={c.teacher_id} full={c.name} />
        </strong>{' '}
        <span>{c.name !== c.teacher_id ? c.name : ''}</span>
        {c.subjects.length > 0 && (
          <span className="small muted">
            {' · '}
            {c.subjects.map((s, i) => (
              <span key={s.id}>
                {i > 0 && ', '}
                <Abbr text={s.id} full={s.name} />
              </span>
            ))}
          </span>
        )}
      </div>
      {messaging && (
        <Link className="btn btn-sm" to={messageLink(c.teacher_id)}>
          <Icon name="mail" /> Nachricht schreiben
        </Link>
      )}
    </li>
  );
}

function ContactsSection({ overview }: { overview: ClassOverview }) {
  const user = useUser();
  const messaging = can(user, 'messages.use');
  const { lead, others } = splitContacts(overview.contacts);
  return (
    <section className="card" aria-labelledby="kl-contacts-h">
      <div className="card-head">
        <h2 id="kl-contacts-h" style={{ fontSize: 'var(--fs-lg)' }}>
          Ansprechpersonen
        </h2>
      </div>
      {overview.contacts.length === 0 ? (
        <Empty title="Keine Lehrkräfte eingetragen" />
      ) : (
        <>
          {lead.length > 0 && (
            <>
              <h3 className="kl-sub">Klassenleitung</h3>
              <ul className="kl-list">
                {lead.map((c) => (
                  <ContactRow key={c.teacher_id} c={c} messaging={messaging} />
                ))}
              </ul>
            </>
          )}
          {others.length > 0 && (
            <>
              <h3 className="kl-sub">Fachlehrkräfte</h3>
              <ul className="kl-list">
                {others.map((c) => (
                  <ContactRow key={c.teacher_id} c={c} messaging={messaging} />
                ))}
              </ul>
            </>
          )}
        </>
      )}
    </section>
  );
}

// ------------------------------------------------------------------ Fehlzeiten & Meldungen (nur Lehrkräfte)

/**
 * „Fehlzeiten & Meldungen“: je Schüler/in die aktuellen und letzten Meldungen mit Zeitpunkt und Kanal. Klassenleitung,
 * Sekretariat und Schulleitung sehen zusätzlich Person, Art, Status und den Verlauf; Fachlehrkräfte nur „abwesend
 * gemeldet“. Schüler/innen und Eltern bekommen den Bereich nie (der Server liefert ihnen 403).
 */
function AbsencesSection({ channelId }: { channelId: number }) {
  const q = useApi((signal) => channelsApi.classAbsences(channelId, signal), [channelId], { live: ['student_absences', 'register'] });
  if (q.error || !q.data) return q.initialLoading ? <Loading /> : null; // 403/404: Bereich entfällt
  const data = q.data;
  return (
    <section className="card" aria-labelledby="kl-abs-h">
      <div className="card-head">
        <h2 id="kl-abs-h" style={{ fontSize: 'var(--fs-lg)' }}>
          Fehlzeiten &amp; Meldungen{' '}
          <HelpTip>
            Meldungen der letzten 30 Tage und der nächsten 14 Tage. Nur für Lehrkräfte dieses Klassenraums – Schüler/innen und Eltern sehen diesen Bereich nicht.
            {data.full ? '' : ' Als Fachlehrkraft sehen Sie nur, dass jemand abwesend gemeldet ist, sowie Zeitpunkt und Kanal – keine Gründe.'}
          </HelpTip>
        </h2>
      </div>
      {data.students.length === 0 ? (
        <p className="muted small">Keine Meldungen in diesem Zeitraum.</p>
      ) : (
        <ul className="kl-list">
          {data.students.map((st) => (
            <li key={st.id}>
              <strong>{st.level === 'full' ? <Link to={`/fehlzeiten/${encodeURIComponent(st.id)}`}>{st.name}</Link> : st.name}</strong>
              {st.reports.map((r) => (
                <div key={r.absence_id}>
                  <span className="small">
                    {formatShort(r.date_from)}
                    {r.date_to !== r.date_from ? ` – ${formatShort(r.date_to)}` : ''}
                    {r.periods.length ? ` (${r.periods.map((p) => p + 1).join(', ')}. Std.)` : ''}: {reportLine(r)}
                    {r.status_label ? ` · ${r.status_label}` : ''}
                  </span>
                  <AbsenceHistory events={r.history} />
                </div>
              ))}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

// ------------------------------------------------------------------ Bereich

export default function ClassTab({ detail, reload }: { detail: ChannelDetail; reload: () => void }) {
  const id = detail.channel.id;
  const child = detail.child?.id;
  const user = useUser();
  const showAbsences = can(user, 'student_absence.read') && !isFamily(user) && (detail.channel.role === 'teacher' || detail.channel.role === 'supervisor');
  const q = useApi<ClassOverview>((signal) => channelsApi.classOverview(id, signal, child), [id, child], { live: ['events', 'holidays', 'classes', 'timetable'] });
  return (
    <div className="stack kl-tab">
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      <PlanSection detail={detail} overview={q.data} />
      {q.data && <EventsSection channelId={id} overview={q.data} reload={q.reload} />}
      <InfoSection detail={detail} reload={reload} />
      {q.data && <ContactsSection overview={q.data} />}
      {showAbsences && <AbsencesSection channelId={id} />}
      {!q.data && !q.error && !q.initialLoading && <Alert kind="info">Keine Angaben.</Alert>}
    </div>
  );
}
