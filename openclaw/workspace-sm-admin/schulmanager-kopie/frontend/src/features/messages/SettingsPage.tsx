/**
 * `/nachrichten/einstellungen` – E-Mail-Hinweis, blockierte Personen, Regeln der Schule (Aufbewahrung, Schüler-Austausch);
 * mit `settings.edit` zusätzlich die schulweiten Postfach-Regeln (`PUT /settings`, nur diese beiden Felder).
 */
import { useEffect, useId, useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage, http } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useTitle } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { can } from '../../lib/permissions';
import { messagesApi } from './api';
import { MailAccounts } from './MailAccounts';
import { Glyph, PersonLine } from './components';
import { folderPath, fullTime, retentionText, suspendedText } from './logic';
import type { BlockEntry, MessageSettings } from './types';
import './messages.css';

interface SchoolMessagingRules {
  messaging_students_to_students?: boolean;
  messaging_retention_days?: number;
}

/** Schulweite Regeln (nur mit `settings.edit`): Schüler-Austausch und Aufbewahrungsfrist. */
function SchoolRules({ onSaved }: { onSaved: () => void }) {
  const toast = useToast();
  const daysId = useId();
  const q = useApi<SchoolMessagingRules>((signal) => http.get<SchoolMessagingRules>('/settings', undefined, { signal }), []);
  const [days, setDays] = useState('');
  useEffect(() => {
    if (q.data) setDays(String(q.data.messaging_retention_days ?? 365));
  }, [q.data]);
  const save = async (body: SchoolMessagingRules) => {
    const before = q.data;
    q.setData((d) => ({ ...(d ?? {}), ...body })); // sofort anzeigen, bei Fehler zurück
    try {
      q.setData(await http.put<SchoolMessagingRules>('/settings', body));
      toast.success('Regeln gespeichert');
      onSaved();
    } catch (e) {
      if (before) q.setData(before);
      toast.error(errorMessage(e));
    }
  };
  const dayValue = Number(days);
  const daysValid = days.trim() !== '' && Number.isInteger(dayValue) && dayValue >= 0 && dayValue <= 3650;
  return (
    <section className="card stack-sm" aria-labelledby="pf-set-school">
      <h2 id="pf-set-school">Regeln für die ganze Schule</h2>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.data && (
        <>
          <label className="check">
            <input
              type="checkbox"
              checked={q.data.messaging_students_to_students !== false}
              onChange={(e) => void save({ messaging_students_to_students: e.target.checked })}
            />{' '}
            Schülerinnen und Schüler dürfen sich gegenseitig schreiben
          </label>
          <Field
            label="Aufbewahrungsfrist in Tagen (0 = nie automatisch löschen)"
            htmlFor={daysId}
            help="Ältere Nachrichten samt Anhängen löscht die Wartung endgültig; offen gemeldete erst nach der Prüfung."
          >
            <div className="pf-days">
              <input id={daysId} type="number" min={0} max={3650} value={days} aria-invalid={!daysValid || undefined} onChange={(e) => setDays(e.target.value)} />
              <AsyncButton className="btn" disabled={!daysValid || dayValue === q.data.messaging_retention_days} onClick={() => save({ messaging_retention_days: dayValue })}>
                Speichern
              </AsyncButton>
            </div>
          </Field>
        </>
      )}
    </section>
  );
}

export default function SettingsPage() {
  useTitle('Nachrichten-Einstellungen');
  const toast = useToast();
  const user = useUser();
  const s = useApi<MessageSettings>((signal) => messagesApi.settings(signal), []);
  const blocks = useApi<BlockEntry[]>((signal) => messagesApi.blocks(signal), [], { live: ['messages'] });
  const settings = s.data;
  const [needMail, setNeedMail] = useState(false);

  const toggleMail = async (on: boolean) => {
    if (on && settings && !settings.has_email) {
      setNeedMail(true); // ohne Adresse/verbundenes Konto: erst einrichten
      return;
    }
    const before = s.data;
    if (before) s.setData({ ...before, email_notify: on }); // sofort anzeigen, bei Fehler zurück
    try {
      s.setData(await messagesApi.saveSettings({ email_notify: on }));
      toast.success(on ? 'E-Mail-Hinweis eingeschaltet' : 'E-Mail-Hinweis ausgeschaltet');
    } catch (e) {
      if (before) s.setData(before);
      toast.error(errorMessage(e));
    }
  };
  const unblock = async (b: BlockEntry) => {
    try {
      await messagesApi.unblock(b.user_id);
      toast.success(`${b.user.name} ist nicht mehr blockiert`);
      blocks.reload();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  return (
    <div className="page page-narrow stack">
      <div className="page-head">
        <h1>Nachrichten-Einstellungen</h1>
        <Link to={folderPath('alle')} className="btn btn-ghost">
          <Glyph name="back" size={16} /> Zu den Nachrichten
        </Link>
      </div>
      {s.error ? <ErrorBox error={s.error} onRetry={s.reload} /> : null}
      {s.initialLoading && <Loading />}
      {settings?.suspended_until && (
        <Alert kind="warning" title="Senden gesperrt">
          {suspendedText(settings.suspended_until)}
          {settings.suspension_reason ? ` Grund: ${settings.suspension_reason}` : ''}
        </Alert>
      )}
      {settings && (
        <section className="card stack-sm" aria-labelledby="pf-set-mail">
          <h2 id="pf-set-mail">E-Mail-Hinweis</h2>
          <label className="check">
            <input
              type="checkbox"
              checked={settings.email_notify && settings.email_available && settings.has_email}
              disabled={settings.has_email && !settings.email_available}
              onChange={(e) => void toggleMail(e.target.checked)}
            />{' '}
            Bei neuen Nachrichten eine E-Mail schicken
          </label>
          {needMail && !settings.has_email && (
            <Alert kind="warning" title="Zuerst eine E-Mail-Adresse einrichten">
              Dafür braucht Ihr Konto eine E-Mail-Adresse: im <Link to="/profil">Profil</Link> eintragen oder unten unter{' '}
              <a href="#pf-set-accounts">E-Mail-Konten</a> ein Postfach verbinden.
            </Alert>
          )}
          <p className="small muted" style={{ margin: 0 }}>
            {!settings.has_email
              ? 'Für Ihr Konto ist keine E-Mail-Adresse hinterlegt (Profil bzw. Schulverwaltung).'
              : !settings.email_available
                ? 'Der E-Mail-Versand ist an dieser Schule nicht eingerichtet.'
                : 'Die E-Mail enthält weder Absender noch Betreff oder Text – nur den Hinweis, dass etwas Neues im Postfach liegt (höchstens eine je Unterhaltung, bis Sie sie gelesen haben).'}
          </p>
        </section>
      )}
      <MailAccounts />
      <section className="card stack-sm" aria-labelledby="pf-set-blocks">
        <h2 id="pf-set-blocks">
          Blockierte Personen
          <HelpTip>
            Blockierte Personen können Ihnen nicht mehr schreiben; ihre Beiträge in Gruppen werden für Sie ausgeblendet. Schulpersonal kann nicht blockiert werden, melden Sie problematische Nachrichten bitte.
          </HelpTip>
        </h2>
        {blocks.error ? <ErrorBox error={blocks.error} onRetry={blocks.reload} /> : null}
        {blocks.data && !blocks.data.length && <p className="small">Sie haben niemanden blockiert.</p>}
        {blocks.data && blocks.data.length > 0 && (
          <ul className="pf-people pf-block-list">
            {blocks.data.map((b) => (
              <li key={b.user_id}>
                <PersonLine person={b.user} extra={<span className="xsmall muted">seit {fullTime(b.created_at)}</span>} />
                <AsyncButton className="btn btn-sm" onClick={() => unblock(b)}>
                  Blockierung aufheben
                </AsyncButton>
              </li>
            ))}
          </ul>
        )}
      </section>
      {settings && (
        <section className="card stack-sm" aria-labelledby="pf-set-rules">
          <h2 id="pf-set-rules">
            Datenschutz und Regeln
            <HelpTip>
              <ul className="pf-rules">
                <li>
                  Betreff, Text, Anhänge und Entwürfe werden verschlüsselt gespeichert. Lesen können sie nur die Teilnehmenden, die Moderation nur gemeldete Nachrichten, und jede Ansicht wird protokolliert.
                </li>
                <li>{retentionText(settings.retention_days)}</li>
                <li>
                  {settings.students_to_students
                    ? 'Schülerinnen und Schüler können sich gegenseitig schreiben.'
                    : 'Nachrichten zwischen Schülerinnen und Schülern sind an dieser Schule abgeschaltet.'}
                </li>
                {settings.can_broadcast && (
                  <li>
                    {settings.broadcast_scope === 'own_classes'
                      ? 'Sie können Rundschreiben an Ihre eigenen Klassen, deren Eltern und Ihre Kurse senden.'
                      : 'Sie können Rundschreiben an Klassen, Eltern, Kurse, Jahrgänge, das Kollegium und die ganze Schule senden.'}
                  </li>
                )}
              </ul>
            </HelpTip>
          </h2>
        </section>
      )}
      {can(user, 'settings.edit') && <SchoolRules onSaved={s.reload} />}
    </div>
  );
}
