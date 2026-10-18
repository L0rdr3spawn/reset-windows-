import { useState } from 'react';
import { ApiError, errorMessage, http } from '../api/client';
import { auth } from '../api/endpoints';
import { TeacherAbbr } from '../components/Abbr';
import { HelpTip } from '../components/HelpTip';
import type { SessionInfo } from '../api/types';
import { users as usersApi } from '../api/endpoints';
import { PageHelp } from '../components/Help';
import { Icon } from '../components/Icon';
import { QrCode } from '../components/QrCode';
import { Alert, AsyncButton, CopyField, ErrorBox, Field } from '../components/ui';
import { useAuth, useUser } from '../context/AuthContext';
import { useTheme, type ThemeMode } from '../context/ThemeContext';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { useTitle } from '../hooks/misc';
import { formatDateTime } from '../lib/dates';
import { ROLE_LABELS } from '../lib/permissions';
import { PasswordForm } from './ChangePasswordPage';
import { IdentitiesSection } from '../features/anmeldedienste/slots';
import { ContactSection } from '../features/konto/slots';
import { ParentAccessSection } from '../features/elternzugriff/ParentAccessSection';
import { PasswordInput } from '../components/PasswordInput';

/** „Ihre Rolle“: Rollenname plus abgeleitete Titel (Klassenleitung, Zweig, begleitete Kinder). */
function RoleTitles({ role }: { role: keyof typeof ROLE_LABELS }) {
  const q = useApi((signal) => http.get<{ titles: string[]; children: string[] }>('/rights/me', undefined, { signal }), []);
  const titles = q.data?.titles?.length ? q.data.titles : [ROLE_LABELS[role] ?? role];
  const kids = q.data?.children?.length ? ` (${q.data.children.join(', ')})` : '';
  return <>{titles.join(' · ') + (role === 'schulbegleitung' ? kids : '')}</>;
}

export function TwoFactor() {
  const user = useUser();
  const { refresh } = useAuth();
  const toast = useToast();
  const [setup, setSetup] = useState<{ secret: string; otpauth_url: string } | null>(null);
  const [code, setCode] = useState('');
  const [codeError, setCodeError] = useState('');
  const [pw, setPw] = useState('');
  if (user.totp_enabled) {
    return (
      <div className="stack">
        <Alert kind="success" title="Zwei-Faktor-Anmeldung ist aktiv" />
        <div className="row" style={{ alignItems: 'flex-end' }}>
          <Field label="Passwort zur Bestätigung" htmlFor="tfa-pw">
            <PasswordInput id="tfa-pw" autoComplete="current-password" value={pw} onChange={(e) => setPw(e.target.value)} />
          </Field>
          <AsyncButton
            className="btn"
            disabled={!pw}
            onClick={async () => {
              try {
                await auth.disable2fa(pw);
                setPw('');
                toast.success('Zwei-Faktor-Anmeldung deaktiviert');
                await refresh();
              } catch (e) {
                toast.error(e);
              }
            }}
          >
            2FA deaktivieren
          </AsyncButton>
        </div>
      </div>
    );
  }
  if (!setup) {
    return (
      <div className="stack">
        <div>
          <AsyncButton
            className="btn btn-primary"
            onClick={async () => {
              try {
                setSetup(await auth.setup2fa());
              } catch (e) {
                toast.error(e);
              }
            }}
          >
            <Icon name="shield" /> 2FA einrichten
          </AsyncButton>
        </div>
      </div>
    );
  }
  return (
    <div className="stack">
      <ol className="small" style={{ paddingLeft: 20, margin: 0 }}>
        <li>Authenticator-App öffnen und diesen QR-Code scannen (oder den Schlüssel manuell eingeben).</li>
        <li>Den angezeigten 6-stelligen Code unten eintragen und bestätigen.</li>
      </ol>
      <div className="row" style={{ alignItems: 'flex-start', gap: 24 }}>
        <QrCode text={setup.otpauth_url} label="QR-Code für die Authenticator-App" />
        <div className="stack grow" style={{ minWidth: 240 }}>
          <CopyField label="Schlüssel (manuelle Eingabe)" value={setup.secret} />
          <CopyField label="otpauth-Adresse" value={setup.otpauth_url} />
        </div>
      </div>
      <form
        className="row"
        style={{ alignItems: 'flex-end' }}
        onSubmit={async (e) => {
          e.preventDefault();
          try {
            await auth.enable2fa(code.trim());
            toast.success('Zwei-Faktor-Anmeldung aktiviert – ab jetzt wird bei der Anmeldung der Code abgefragt');
            setSetup(null);
            setCode('');
            setCodeError('');
            await refresh();
          } catch (err) {
            setCodeError(
              err instanceof ApiError && err.status === 400
                ? 'Der Code passt nicht. Bitte den aktuell angezeigten Code nehmen. Am Handy sollte die Uhrzeit automatisch gestellt sein.'
                : errorMessage(err),
            );
          }
        }}
      >
        <Field label="Code aus der App" htmlFor="tfa-code">
          <input id="tfa-code" type="text" inputMode="numeric" autoComplete="one-time-code" maxLength={8} value={code} onChange={(e) => setCode(e.target.value.replace(/\s/g, ''))} />
        </Field>
        <button type="submit" className="btn btn-primary" disabled={code.length < 6}>
          Bestätigen
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => setSetup(null)}>
          Abbrechen
        </button>
      </form>
      {codeError && <Alert kind="error">{codeError}</Alert>}
      <div>
        <AsyncButton
          className="btn btn-ghost btn-sm"
          onClick={async () => {
            try {
              setSetup(await auth.setup2fa(true));
              setCode('');
              setCodeError('');
            } catch (e) {
              toast.error(e);
            }
          }}
        >
          Neuen QR-Code erzeugen
        </AsyncButton>{' '}
        <HelpTip>Nur nötig, wenn der Eintrag in der Authenticator-App verloren ist. Danach den alten Eintrag in der App löschen.</HelpTip>
      </div>
    </div>
  );
}

function Ical() {
  const toast = useToast();
  const q = useApi(() => auth.icalUrl(), []);
  const [url, setUrl] = useState<string | null>(null);
  const shown = url;   // der Link wird nur beim Erzeugen angezeigt (Server speichert nur einen Hash)
  const active = shown !== null || !!q.data?.active;
  return (
    <div className="stack">
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {shown && <CopyField label="Kalender-Abo (iCal)" value={shown} />}
      {!shown && active && (
        <p className="small">
          Ein Kalender-Link ist aktiv. Aus Sicherheitsgründen wird er nur beim Erzeugen angezeigt.{' '}
          <HelpTip>Auf dem Server liegt nur eine Prüfsumme des Links. Wer ihn verloren hat, erzeugt einen neuen; der alte funktioniert dann nicht mehr.</HelpTip>
        </p>
      )}
      <div className="row">
        {shown && (
          <a className="btn btn-sm" href={shown.replace(/^https?:/, 'webcal:')}>
            <Icon name="calendar" /> In Kalender-App öffnen
          </a>
        )}
        <AsyncButton
          className="btn btn-sm"
          confirm={active ? 'Neuen Link erzeugen? Der bisherige Link funktioniert dann nicht mehr.' : undefined}
          onClick={async () => {
            try {
              setUrl((await auth.icalReset()).url);
              toast.success('Kalender-Link erzeugt');
            } catch (e) {
              toast.error(e);
            }
          }}
        >
          <Icon name="refresh" /> {active ? 'Neuen Link erzeugen' : 'Kalender-Link erzeugen'}
        </AsyncButton>
      </div>
    </div>
  );
}

function MySessions() {
  const user = useUser();
  const toast = useToast();
  const q = useApi<SessionInfo[]>(() => usersApi.sessions(user.id), [user.id]);
  return (
    <div className="stack">
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      <ul className="list-plain small">
        {(q.data ?? []).map((s) => (
          <li key={s.id} className="row-between">
            <span>
              {s.current && <span className="badge badge-primary">dieses Gerät</span>} {s.user_agent?.slice(0, 90) ?? 'Gerät'} · zuletzt {formatDateTime(s.last_seen)}
            </span>
            {!s.current && (
              <AsyncButton
                className="btn btn-ghost btn-sm"
                onClick={async () => {
                  try {
                    await usersApi.deleteSession(s.id);
                    q.reload();
                  } catch (e) {
                    toast.error(e);
                  }
                }}
              >
                Sitzung beenden
              </AsyncButton>
            )}
          </li>
        ))}
      </ul>
      <div>
        <AsyncButton
          className="btn btn-sm"
          onClick={async () => {
            try {
              const r = await usersApi.revokeAllSessions(user.id);
              toast.success(`${r.revoked} andere Sitzung(en) beendet`);
              q.reload();
            } catch (e) {
              toast.error(e);
            }
          }}
        >
          Alle anderen Sitzungen beenden
        </AsyncButton>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  useTitle('Profil');
  const user = useUser();
  const toast = useToast();
  const { mode, setMode } = useTheme();
  return (
    <div className="page-narrow stack">
      <div className="page-head">
        <h1>Profil & Sicherheit</h1>
      </div>
      <section className="card">
        <h2>Konto</h2>
        <dl className="kv">
          <dt>Name</dt>
          <dd>{user.display_name}</dd>
          <dt>Benutzername</dt>
          <dd className="mono">{user.username}</dd>
          <dt>Rolle</dt>
          <dd>
            <RoleTitles role={user.role} />
          </dd>
          {user.teacher_id && (
            <>
              <dt>Lehrkraft</dt>
              <dd>
                <TeacherAbbr id={user.teacher_id} />
              </dd>
            </>
          )}
        </dl>
        <div className="row" style={{ marginTop: 12 }}>
          <Field label="Farbschema" htmlFor="pf-theme">
            <select id="pf-theme" value={mode} onChange={(e) => setMode(e.target.value as ThemeMode)}>
              <option value="system">wie Gerät</option>
              <option value="light">hell</option>
              <option value="dark">dunkel</option>
            </select>
          </Field>
        </div>
      </section>
      <ContactSection />
      <ParentAccessSection />
      <section className="card">
        <h2>Passwort ändern</h2>
        <PasswordForm onDone={() => toast.success('Passwort geändert. Andere Sitzungen wurden abgemeldet.')} />
      </section>
      <section className="card">
        <h2 className="with-help">
          Zwei-Faktor-Anmeldung
          <PageHelp label="Hilfe zu Zwei-Faktor-Anmeldung">
            Schützt Ihr Konto zusätzlich mit einem Code aus einer Authenticator-App (z. B. FreeOTP, Aegis, Google oder Microsoft Authenticator). Bei
            jeder Anmeldung wird dann zusätzlich der Code abgefragt. Empfohlen für alle Konten mit Zugriff auf Schülerdaten.
          </PageHelp>
        </h2>
        <TwoFactor />
      </section>
      <IdentitiesSection />
      {/* Kalender-Abo nur mit persönlichem Stundenplan (Lehrkraft, Schüler/in, Eltern) – der Feed liefert sonst 404 */}
      {(user.teacher_id || user.student_id || (user.student_ids?.length ?? 0) > 0 || (user.students?.length ?? 0) > 0) && (
        <section className="card">
          <h2 className="with-help">
            Kalender-Abo
            <PageHelp label="Hilfe zu Kalender-Abo">
              Ihr persönlicher Stunden- und Vertretungsplan in einer Kalender-App (z. B. Outlook, Apple-Kalender, Google Kalender, Thunderbird).
              Änderungen erscheinen automatisch. Der Link ist geheim – bitte nicht weitergeben; „Neuen Link erzeugen“ macht den bisherigen ungültig.
            </PageHelp>
          </h2>
          <Ical />
        </section>
      )}
      <section className="card">
        <h2 className="with-help">
          Angemeldete Geräte
          <PageHelp label="Hilfe zu angemeldeten Geräten">
            Browser und Geräte, auf denen Ihr Konto angemeldet ist. Unbekannte Sitzungen können Sie hier beenden.
          </PageHelp>
        </h2>
        <MySessions />
      </section>
      <section className="card">
        <h2 className="with-help">
          Datenauskunft (DSGVO)
          <PageHelp label="Hilfe zur Datenauskunft">Alle zu Ihrem Konto gespeicherten Daten als Datei herunterladen (Auskunft nach Art. 15 DSGVO).</PageHelp>
        </h2>
        <a className="btn btn-sm" href={auth.exportUrl()} download>
          <Icon name="download" /> Meine Daten exportieren
        </a>
      </section>
    </div>
  );
}
