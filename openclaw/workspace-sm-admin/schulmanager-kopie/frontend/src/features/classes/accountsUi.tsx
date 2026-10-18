/**
 * Konten-Bausteine des Klassen-Assistenten und von „Schüler/in hinzufügen“ (§11.3): Konto-Optionen (inkl. sofortigem
 * E-Mail-Versand), Vorschau des Probelaufs und Ergebnis mit PDF/ZIP/E-Mail.
 */
import { useId } from 'react';
import { Link } from 'react-router-dom';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert } from '../../components/ui';
import { lettersApi } from '../zugangsdaten/api';
import { LetterBatchActions } from '../zugangsdaten/components';
import { hasEmails, type StudentDraft } from './studentList';
import type { AccountOptionsBody, CreateStudentsResult, SendTo } from './types';

export interface AccountOpts {
  students: boolean;
  parents: boolean;
  send: boolean;
  sendTo: SendTo;
}

/** Vorbelegung: Schülerkonten an; Elternkonten an, sobald Elterndaten eingetragen sind; Versand an bei E-Mail-Adressen. */
export function defaultAccountOpts(rows: readonly StudentDraft[], canManage: boolean): AccountOpts {
  const mails = hasEmails(rows);
  const parentData = rows.some((r) => r.parents.some((p) => p.name.trim() || p.email.trim()));
  return {
    students: canManage,
    parents: canManage && parentData,
    send: canManage && mails.students + mails.parents > 0,
    sendTo: mails.students === 0 && mails.parents > 0 ? 'parents' : 'student',
  };
}

export function accountBody(o: AccountOpts, dryRun: boolean): AccountOptionsBody {
  const any = o.students || o.parents;
  return {
    create_student_accounts: o.students,
    create_parent_accounts: o.parents,
    send_email: any && o.send,
    send_to: o.sendTo,
    dry_run: dryRun,
  };
}

const SEND_TO: { value: SendTo; label: string }[] = [
  { value: 'student', label: 'an die Schüler/innen' },
  { value: 'parents', label: 'an die Eltern' },
  { value: 'both', label: 'an Schüler/innen und Eltern' },
];

export function AccountOptionsForm({
  value,
  onChange,
  canManage,
  rows,
}: {
  value: AccountOpts;
  onChange: (o: AccountOpts) => void;
  canManage: boolean;
  rows: readonly StudentDraft[];
}) {
  const name = useId();
  const mails = hasEmails(rows);
  const any = value.students || value.parents;
  const set = (patch: Partial<AccountOpts>) => onChange({ ...value, ...patch });
  return (
    <div className="stack">
      {!canManage && (
        <Alert kind="info" title="Konten legt die Benutzerverwaltung an">
          Ihr Konto darf keine Benutzerkonten anlegen. Zugangsdaten erzeugt danach das Sekretariat.
        </Alert>
      )}
      <fieldset className="kl-fieldset" disabled={!canManage}>
        <legend>
          Konten
          <HelpTip>
            Jedes Konto bekommt ein Startpasswort, beim ersten Anmelden wird ein eigenes Passwort verlangt. Eltern mit derselben E-Mail-Adresse bekommen ein gemeinsames Konto für alle Kinder; gibt es schon ein Elternkonto mit der Adresse, wird das Kind dort ergänzt. Ohne Elternangaben entsteht je Kind ein Konto „Eltern von …“.
          </HelpTip>
        </legend>
        <label className="check">
          <input type="checkbox" checked={value.students} onChange={(e) => set({ students: e.target.checked })} /> Schülerkonten anlegen
        </label>
        <label className="check">
          <input type="checkbox" checked={value.parents} onChange={(e) => set({ parents: e.target.checked })} /> Elternkonten anlegen
        </label>
      </fieldset>
      <fieldset className="kl-fieldset" disabled={!canManage || !any}>
        <legend>Zugangsdaten verschicken</legend>
        <label className="check">
          <input type="checkbox" checked={value.send && any} onChange={(e) => set({ send: e.target.checked })} /> Zugangsdaten sofort per E-Mail senden (je
          Person ihr PDF)
        </label>
        <p className="small muted" style={{ margin: 0 }}>
          {mails.students === 1 ? '1 Schüler/in' : `${mails.students} Schüler/innen`} und {mails.parents === 1 ? '1 Familie' : `${mails.parents} Familien`} mit
          E-Mail-Adresse.
          <HelpTip>Wer keine Adresse hat, bekommt den Brief ausgedruckt.</HelpTip>
        </p>
        {value.send && any && (
          <div role="radiogroup" aria-labelledby={`${name}-l`} className="stack-sm">
            <span id={`${name}-l`} className="field-label">
              Briefe Minderjähriger senden
            </span>
            {SEND_TO.map((o) => (
              <label key={o.value} className="check">
                <input type="radio" name={name} checked={value.sendTo === o.value} onChange={() => set({ sendTo: o.value })} /> {o.label}
              </label>
            ))}
            <span className="small muted">Volljährige bekommen ihren Brief selbst; Elternbriefe gehen an die Eltern.</span>
          </div>
        )}
        {value.send && any && (
          <Alert kind="warning" title="E-Mail ist weniger sicher als Papier">
            Startpasswörter per E-Mail können mitgelesen werden.
          </Alert>
        )}
      </fieldset>
    </div>
  );
}

export function PreviewTable({ result }: { result: CreateStudentsResult }) {
  return (
    <section className="kl-preview" aria-labelledby="kl-dry-h">
      <h3 id="kl-dry-h" tabIndex={-1}>
        Vorschau – noch nichts gespeichert
      </h3>
      {result.warnings.length > 0 && (
        <Alert kind="warning" title="Bitte prüfen">
          <ul>
            {result.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </Alert>
      )}
      <div className="table-wrap">
        <table className="table table-compact">
          <thead>
            <tr>
              <th scope="col">Name</th>
              <th scope="col">Benutzername</th>
              <th scope="col">Elternkonto</th>
            </tr>
          </thead>
          <tbody>
            {result.students.map((s) => (
              <tr key={s.index}>
                <td>
                  {s.name}
                  {s.adult && (
                    <span className="badge" style={{ marginLeft: 6 }}>
                      volljährig
                    </span>
                  )}
                </td>
                <td className="mono">{s.username ?? <span className="muted">kein Konto</span>}</td>
                <td className="small">
                  {s.parent_accounts.length
                    ? s.parent_accounts.map((p) => (
                        <div key={p.username}>
                          <span className="mono">{p.username}</span>{' '}
                          {p.existing ? <span className="badge badge-primary">vorhanden – Kind wird ergänzt</span> : null}
                        </div>
                      ))
                    : '–'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

const ROLE: Record<string, string> = { schueler: 'Schüler/in', eltern: 'Eltern' };

export function CreateResultView({ result, title }: { result: CreateStudentsResult; title: string }) {
  const batch = result.letter_batch;
  const students = result.accounts.filter((a) => a.role === 'schueler').length;
  const parents = result.accounts.length - students;
  const email = result.email;
  return (
    <div className="stack" aria-live="polite">
      <Alert kind="success" title={title}>
        {result.students.length === 1 ? '1 Schüler/in' : `${result.students.length} Schüler/innen`}
        {result.accounts.length
          ? ` · ${students} ${students === 1 ? 'Schülerkonto' : 'Schülerkonten'}, ${parents} ${parents === 1 ? 'Elternkonto' : 'Elternkonten'}`
          : ' · ohne Konten'}
        .{result.accounts.length > 0 && ' Beim ersten Anmelden muss jede Person ein eigenes Passwort festlegen.'}
      </Alert>
      {result.linked_parents.length > 0 && (
        <Alert kind="info" title="Vorhandene Elternkonten ergänzt">
          {result.linked_parents.map((p) => p.display_name || p.username).join(', ')} – das Kind wurde dem bestehenden Konto hinzugefügt (kein neuer Brief
          nötig).
        </Alert>
      )}
      {email && (
        <Alert kind={email.unavailable.length ? 'warning' : 'success'} title="E-Mail-Versand">
          {email.sent.length} {email.sent.length === 1 ? 'Brief' : 'Briefe'} verschickt
          {email.no_address.length ? ` · ${email.no_address.length} ohne E-Mail-Adresse (bitte ausdrucken)` : ''}
          {email.unavailable.length ? ` · ${email.unavailable.length} nicht zustellbar` : ''}.
          {email.no_address.length > 0 && <div className="small">Ohne Adresse: {email.no_address.map((r) => r.display_name).join(', ')}</div>}
        </Alert>
      )}
      {result.warnings.length > 0 && (
        <Alert kind="warning" title="Hinweise">
          <ul>
            {result.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </Alert>
      )}
      {batch && (
        <section className="card" aria-labelledby="kl-res-h">
          <div className="card-head">
            <h2 id="kl-res-h">
              Zugangsbriefe
              <HelpTip>Die Briefe sind aus Sicherheitsgründen nur kurze Zeit abrufbar; danach über „Auf Startpasswort zurücksetzen“ neu erzeugen.</HelpTip>
            </h2>
          </div>
          <div className="row">
            <LetterBatchActions batch={batch} page={false} small={false} />
            <Link className="btn" to={`/zugangsdaten/${encodeURIComponent(batch.id)}#senden`}>
              <Icon name="mail" /> Per E-Mail senden
            </Link>
          </div>
          <div className="table-wrap">
            <table className="table table-compact">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Rolle</th>
                  <th scope="col">Benutzername</th>
                  <th scope="col">
                    <span className="sr-only">Brief</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {result.accounts.map((a) => (
                  <tr key={a.user_id}>
                    <td>{a.display_name}</td>
                    <td>{ROLE[a.role] ?? a.role}</td>
                    <td className="mono">{a.username}</td>
                    <td>
                      <a
                        className="btn btn-ghost btn-sm"
                        href={lettersApi.entryUrl(batch.id, a.user_id)}
                        download
                        aria-label={`Brief für ${a.display_name} als PDF`}
                      >
                        <Icon name="download" /> PDF
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
