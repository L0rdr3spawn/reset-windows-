/**
 * Verwaltungsseite „Sicherheit“ (`/sicherheit`, Recht `login_policy.manage`): Zwei-Faktor-Vorgabe für das Personal,
 * Abmeldung bei Inaktivität, Gültigkeit von Startpasswörtern und die aktuellen Anmelde-Drosselungen (aufheben mit
 * `users.manage`).
 */
import { useEffect, useId, useState } from 'react';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Alert, AsyncButton, Empty, ErrorBox, Field, Loading, SegmentedControl } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useTitle } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { securityApi } from './api';
import { MODE_LABELS, formatMinutes, formatWait, lockTitle, toggleRole } from './logic';
import type { SecuritySettings, TwofaMode } from './types';

const IDLE_CHOICES = [30, 60, 120, 240, 480, 720, 1440, 4320];

function SettingsCard({ s, onSaved }: { s: SecuritySettings; onSaved: () => void }) {
  const toast = useToast();
  const ids = { idle: useId(), days: useId() };
  const [mode, setMode] = useState<TwofaMode>(s.twofa_mode);
  const [roles, setRoles] = useState<string[]>(s.twofa_roles);
  const [idle, setIdle] = useState(s.staff_idle_minutes);
  const [days, setDays] = useState(s.initial_password_days);
  useEffect(() => {
    setMode(s.twofa_mode);
    setRoles(s.twofa_roles);
    setIdle(s.staff_idle_minutes);
    setDays(s.initial_password_days);
  }, [s]);
  const order = s.role_choices.map((r) => r.id);
  const dirty = mode !== s.twofa_mode || idle !== s.staff_idle_minutes || days !== s.initial_password_days || roles.join() !== s.twofa_roles.join();
  const idleOptions = Array.from(new Set([...IDLE_CHOICES, s.staff_idle_minutes])).sort((a, b) => a - b);

  const save = async () => {
    try {
      await securityApi.save({ twofa_mode: mode, twofa_roles: roles, staff_idle_minutes: idle, initial_password_days: days });
      toast.success('Sicherheits-Einstellungen gespeichert');
      onSaved();
    } catch (e) {
      toast.error(errorMessage(e), 'Speichern');
    }
  };

  return (
    <section className="card stack" aria-labelledby="sec-set-h">
      <h2 id="sec-set-h">Anmeldung des Personals</h2>
      <Field
        label={
          <>
            Zwei-Faktor-Anmeldung{' '}
            <HelpTip>„Empfohlen“ zeigt den betroffenen Konten einen Hinweis auf der Startseite. „Pflicht“ sperrt die Anwendung, bis die Einrichtung (Authenticator-App) erledigt ist.</HelpTip>
          </>
        }
      >
        <SegmentedControl<TwofaMode>
          label="Zwei-Faktor-Anmeldung"
          value={mode}
          onChange={setMode}
          options={(Object.keys(MODE_LABELS) as TwofaMode[]).map((m) => ({ value: m, label: MODE_LABELS[m] }))}
        />
      </Field>
      {mode !== 'off' && (
        <fieldset className="stack-sm" style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className="small">Betroffene Rollen</legend>
          {s.role_choices.map((r) => (
            <label key={r.id} className="check">
              <input type="checkbox" checked={roles.includes(r.id)} onChange={() => setRoles(toggleRole(roles, r.id, order))} /> {r.label}
            </label>
          ))}
        </fieldset>
      )}
      {s.env_required_roles.length > 0 && (
        <Alert kind="info">Für {s.env_required_roles.join(', ')} ist die Pflicht fest in der Serverkonfiguration eingestellt.</Alert>
      )}
      <Field
        label="Abmeldung bei Inaktivität (Personal)"
        htmlFor={ids.idle}
        help={`Gilt für Administration, Schulleitung, Sekretariat, Lehrkräfte und weitere Mitarbeitende. Schüler/innen und Eltern: ${formatMinutes(s.student_idle_minutes)}.`}
      >
        <select id={ids.idle} value={idle} onChange={(e) => setIdle(Number(e.target.value))}>
          {idleOptions.map((m) => (
            <option key={m} value={m}>
              {formatMinutes(m)}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Startpasswort gilt" htmlFor={ids.days} help="Danach lässt sich das Startpasswort aus dem Zugangsbrief nicht mehr verwenden; ein neues wird in der Konten-Verwaltung erzeugt.">
        <span className="row">
          <input
            id={ids.days}
            type="number"
            min={s.password_days_range[0]}
            max={s.password_days_range[1]}
            value={days}
            onChange={(e) => setDays(Math.max(s.password_days_range[0], Math.min(s.password_days_range[1], Number(e.target.value) || s.password_days_range[0])))}
            style={{ maxWidth: '8rem' }}
          />
          Tage
        </span>
      </Field>
      <div>
        <AsyncButton className="btn btn-primary" onClick={save} disabled={!dirty}>
          Speichern
        </AsyncButton>
      </div>
    </section>
  );
}

function LocksCard({ s }: { s: SecuritySettings }) {
  const toast = useToast();
  const user = useUser();
  const canUnlock = user.permissions.includes('users.manage');
  const q = useApi((signal) => securityApi.locks(signal), [], { enabled: canUnlock });
  if (!canUnlock) return null;
  const locks = q.data?.locks ?? [];
  return (
    <section className="card stack" aria-labelledby="sec-lock-h">
      <div className="row-between">
        <h2 id="sec-lock-h">
          Gebremste Anmeldungen{' '}
          <HelpTip>
            Nach {s.lock.max_failures} falschen Eingaben je Konto und Anschluss wartet dieser Anschluss {formatWait(s.lock.base_delay_seconds)}, danach jeweils doppelt so lange (höchstens{' '}
            {formatWait(s.lock.max_delay_seconds)}). Andere Anschlüsse und „Passwort vergessen“ sind nicht betroffen – das Konto lässt sich also nicht gezielt aussperren.
          </HelpTip>
        </h2>
        <button type="button" className="btn btn-sm" onClick={q.reload}>
          Aktualisieren
        </button>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && locks.length === 0 && <Empty title="Zurzeit wird niemand gebremst" />}
      {locks.length > 0 && (
        <ul className="list">
          {locks.map((l) => (
            <li key={`${l.kind}-${l.username}-${l.ip}`} className="row-between">
              <span>
                <strong>{lockTitle(l)}</strong>
                {l.role_label ? <span className="muted"> · {l.role_label}</span> : null}
                <span className="small muted">
                  {' '}
                  · {l.failures} Fehlversuche, nächster Versuch in {formatWait(l.wait)}
                </span>
              </span>
              <AsyncButton
                className="btn btn-sm"
                onClick={async () => {
                  try {
                    if (l.kind === 'ip' && l.ip) await securityApi.unlockIp(l.ip);
                    else if (l.username) await securityApi.unlockUser(l.username);
                    toast.success('Bremse aufgehoben');
                    q.reload();
                  } catch (e) {
                    toast.error(errorMessage(e), 'Aufheben');
                  }
                }}
              >
                Aufheben
              </AsyncButton>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function SecurityPage() {
  useTitle('Sicherheit');
  const q = useApi((signal) => securityApi.settings(signal), []);
  return (
    <div className="stack">
      <h1>Sicherheit</h1>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && (
        <>
          <SettingsCard s={q.data} onSaved={q.reload} />
          <LocksCard s={q.data} />
        </>
      )}
    </div>
  );
}
