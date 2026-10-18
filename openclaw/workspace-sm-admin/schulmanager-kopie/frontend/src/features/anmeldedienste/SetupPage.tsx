/**
 * `/anmeldedienste` (nur Administration): Microsoft, Apple, Google und Schulkonto (OIDC) einrichten – Felder je
 * Anbieter, Weiterleitungs-URI zum Kopieren, „Verbindung testen“, Hinweis zum Test-Anbieter. Geheimnisse zeigt der
 * Server nie an (nur „gesetzt“); leere Felder lassen sie unverändert. Werte aus Umgebungsvariablen sind gesperrt.
 */
import { useId, useState, type ReactNode } from 'react';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { HelpTip } from '../../components/HelpTip';
import { Alert, AsyncButton, CopyField, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useTitle } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../lib/dates';
import { ssoApi } from './api';
import { buildUpdate, initialForm, SECRET_FIELDS, STATUS_BADGE, STATUS_LABELS, type SetupForm } from './logic';
import type { ConfigField, ProviderSetup, TestResult } from './types';
import './anmeldedienste.css';
import { APP_NAME } from '../../brand';

const HINTS: Record<string, Partial<Record<ConfigField, ReactNode>>> = {
  microsoft: {
    client_id: 'Anwendungs-ID (Client-ID) der App-Registrierung in Microsoft Entra ID.',
    client_secret: 'Geheimer Clientschlüssel (Wert, nicht die ID) der App-Registrierung.',
    tenant: 'Verzeichnis-ID (Tenant-ID) der Schule. Leer = „organizations“ (alle Schul-/Geschäftskonten). Mit fester Tenant-ID gelten die E-Mail-Adressen als bestätigt.',
  },
  google: {
    client_id: 'OAuth-Client vom Typ „Webanwendung“ aus der Google Cloud Console.',
    client_secret: 'Clientschlüssel des OAuth-Clients.',
    hosted_domain: 'Optional: nur Konten dieser Google-Workspace-Domain zulassen (z. B. schule.de).',
  },
  apple: {
    client_id: 'Services-ID aus dem Apple-Developer-Konto (z. B. de.schule.anmeldung).',
    team_id: '10-stellige Team-ID des Apple-Developer-Kontos.',
    key_id: 'Schlüssel-ID des „Sign in with Apple“-Schlüssels.',
    private_key: 'Inhalt der heruntergeladenen .p8-Datei (beginnt mit „-----BEGIN PRIVATE KEY-----“).',
  },
  oidc: {
    issuer: 'Adresse des Identity Providers der Schule, z. B. https://idp.schule.de/realms/schule.',
    client_id: `Client-ID, die beim Identity Provider für ${APP_NAME} angelegt wurde.`,
    client_secret: 'Nur bei vertraulichen Clients nötig.',
  },
};
/** Kurzanleitung je Anbieter (ausführlich: docs/ANMELDEDIENSTE.md). */
const STEPS: Record<string, string[]> = {
  microsoft: [
    'Microsoft Entra Admin Center → App-Registrierungen → Neue Registrierung.',
    'Plattform „Web“ mit der Weiterleitungs-URI von unten (genau so, mit Port).',
    'Zertifikate & Geheimnisse → Neuer geheimer Clientschlüssel; den Wert hier eintragen.',
    'Anwendungs-ID (Client-ID) und – für nur ein Verzeichnis – die Verzeichnis-ID (Mandant) hier eintragen.',
  ],
  google: [
    'Google Cloud Console → APIs & Dienste → Anmeldedaten → OAuth-Client-ID, Typ „Webanwendung“.',
    '„Autorisierte JavaScript-Quellen“: die Quelle von unten; „Autorisierte Weiterleitungs-URIs“: die URI von unten.',
    'Client-ID und Clientschlüssel hier eintragen; OAuth-Zustimmungsbildschirm einrichten.',
  ],
  apple: [
    'Apple-Developer-Konto (kostenpflichtig, Developer Program) → Identifiers → Services ID anlegen.',
    '„Sign in with Apple“ aktivieren; Domain (ohne Port) und Return-URL von unten eintragen.',
    'Keys → neuer Schlüssel mit „Sign in with Apple“; .p8-Datei, Schlüssel-ID und Team-ID hier eintragen.',
  ],
  oidc: ['Beim Identity Provider der Schule einen Client anlegen und die Weiterleitungs-URI von unten eintragen.'],
};
const AUTO_TEXT: Record<string, { label: string; help: string }> = {
  one_tap: {
    label: 'Automatisch anmelden (Google One Tap)',
    help: 'Beim Öffnen der Anmeldeseite blendet Google „Weiter als …“ ein; wer in diesem Browser schon bei Google angemeldet ist und sich hier zuletzt mit Google angemeldet hat, wird ohne Klick angemeldet. Nach dem Abmelden ist das aus. Auf gemeinsam genutzten Rechnern besser ausgeschaltet lassen. Dafür lädt die Anmeldeseite das Skript von Google.',
  },
  silent: {
    label: 'Automatisch anmelden (stilles Microsoft-SSO)',
    help: 'Wer in diesem Browser schon bei Microsoft angemeldet ist und sich hier zuletzt mit Microsoft angemeldet hat, wird beim Öffnen der Anmeldeseite ohne Klick angemeldet (einmal je Tab). Klappt es nicht, erscheint die gewohnte Anmeldeseite. Nach dem Abmelden ist das aus. Auf gemeinsam genutzten Rechnern besser ausgeschaltet lassen.',
  },
};
const COMMON_HINTS: Partial<Record<ConfigField, ReactNode>> = {
  label: 'Text auf dem Knopf „Mit … anmelden“ – leer = Standard.',
  allowed_domains: 'Optional: nur Konten mit bestätigter E-Mail-Adresse dieser Domains (Komma oder Zeilenumbruch), z. B. schule.de, appleid.schule.de.',
};

function ProviderCard({ setup, labels, onSaved }: { setup: ProviderSetup; labels: Record<string, string>; onSaved: (p: ProviderSetup) => void }) {
  const toast = useToast();
  const id = useId();
  const [form, setForm] = useState<SetupForm>(() => initialForm(setup));
  const [test, setTest] = useState<TestResult | null>(null);
  const set = (f: ConfigField, v: string) => setForm((prev) => ({ ...prev, [f]: v }));
  const envOnly = setup.env_fields.some((f) => setup.required.includes(f as ConfigField));

  const save = async () => {
    try {
      const saved = await ssoApi.update(setup.id, buildUpdate(setup, form));
      onSaved(saved);
      setForm(initialForm(saved));
      setTest(null);
      toast.success(`${saved.label}: gespeichert`);
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const clearSecret = async (f: 'client_secret' | 'private_key') => {
    try {
      const saved = await ssoApi.update(setup.id, f === 'client_secret' ? { clear_client_secret: true } : { clear_private_key: true });
      onSaved(saved);
      toast.success('Geheimnis entfernt');
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const runTest = async () => {
    try {
      setTest(await ssoApi.test(setup.id));
    } catch (e) {
      setTest({ ok: false, message: errorMessage(e) });
    }
  };

  return (
    <section className="card stack-sm" aria-labelledby={`${id}-h`}>
      <div className="row-between ad-card-head">
        <h2 id={`${id}-h`} className="ad-card-title">
          {setup.label}
          {setup.label !== setup.default_label && <span className="small muted"> ({setup.default_label})</span>}
        </h2>
        <span>
          <span className={`badge ${STATUS_BADGE[setup.status]}`}>{STATUS_LABELS[setup.status]}</span>
          {setup.status === 'mock' && (
            <HelpTip>Solange der Anbieter nicht eingerichtet ist, erscheint er in dieser Umgebung als Test-Anbieter „{setup.label} (Test)“.</HelpTip>
          )}
        </span>
      </div>
      {setup.missing.length > 0 && setup.status !== 'mock' && (
        <p className="small muted">Es fehlen noch: {setup.missing.map((f) => labels[f] ?? f).join(', ')}.</p>
      )}
      {setup.warnings.map((w) => (
        <Alert key={w} kind="warning" title="Hinweis zur Adresse">
          {w}
        </Alert>
      ))}
      <div className="row ad-urls">
        <HelpTip label={`Einrichtung bei ${setup.default_label}`}>
          <ol>
            {(STEPS[setup.id] ?? []).map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ol>
          {setup.script_hosts.length > 0 && <p>Ist der Anbieter eingeschaltet, lädt die Anmeldeseite Skripte von: {setup.script_hosts.join(', ')}. Sonst wird nichts von Dritten geladen.</p>}
        </HelpTip>
      </div>
      <CopyField label={setup.id === 'apple' ? 'Return-URL (bei Apple eintragen)' : 'Weiterleitungs-URI (beim Anbieter eintragen)'} value={setup.redirect_uri} />
      {setup.js_origins.map((o) => (
        <CopyField key={o} label={setup.id === 'apple' ? 'Domain (bei Apple eintragen, ohne https:// und ohne Port)' : 'Autorisierte JavaScript-Quelle (bei Google eintragen)'} value={setup.id === 'apple' ? new URL(o).hostname : o} />
      ))}
      <div className="ad-setup-grid">
        {setup.field_names.map((f) => {
          const fid = `${id}-${f}`;
          const fromEnv = setup.env_fields.includes(f);
          const secret = SECRET_FIELDS.has(f);
          const isSet = secret && setup.secrets[f as 'client_secret' | 'private_key'];
          const envHint = fromEnv ? <> · festgelegt über <code>{setup.env_vars[f]}</code></> : null;
          const hint = (
            <>
              {HINTS[setup.id]?.[f] ?? COMMON_HINTS[f]}
              {envHint}
            </>
          );
          const label = `${labels[f] ?? f}${setup.required.includes(f) ? ' *' : ''}`;
          const wide = f === 'private_key' || f === 'allowed_domains' || f === 'issuer';
          return (
            <div key={f} className={wide ? 'ad-wide' : undefined}>
              <Field label={label} htmlFor={fid} hint={hint}>
                {f === 'private_key' ? (
                  <textarea
                    id={fid}
                    className="ad-key"
                    value={form[f] ?? ''}
                    disabled={fromEnv}
                    spellCheck={false}
                    autoComplete="off"
                    placeholder={fromEnv ? 'aus der Umgebung' : isSet ? 'gesetzt – leer lassen = unverändert' : '-----BEGIN PRIVATE KEY-----'}
                    onChange={(e) => set(f, e.target.value)}
                  />
                ) : f === 'allowed_domains' ? (
                  <textarea id={fid} rows={2} value={form[f] ?? ''} disabled={fromEnv} spellCheck={false} onChange={(e) => set(f, e.target.value)} />
                ) : (
                  <input
                    id={fid}
                    type={secret ? 'password' : 'text'}
                    value={form[f] ?? ''}
                    disabled={fromEnv}
                    autoComplete={secret ? 'new-password' : 'off'}
                    spellCheck={false}
                    autoCapitalize="none"
                    placeholder={fromEnv ? 'aus der Umgebung' : isSet ? 'gesetzt – leer lassen = unverändert' : f === 'tenant' ? 'organizations' : ''}
                    onChange={(e) => set(f, e.target.value)}
                  />
                )}
              </Field>
              {secret && isSet && !fromEnv && (
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => void clearSecret(f as 'client_secret' | 'private_key')}>
                  <Icon name="trash" /> Gespeichertes Geheimnis entfernen
                </button>
              )}
            </div>
          );
        })}
      </div>
      <label className="check">
        <input type="checkbox" checked={envOnly || form.enabled} disabled={envOnly} onChange={(e) => setForm((prev) => ({ ...prev, enabled: e.target.checked }))} /> Anmeldung mit{' '}
        {setup.label} einschalten
        {envOnly && <span className="small muted"> (über Umgebungsvariablen eingerichtet – immer eingeschaltet)</span>}
      </label>
      {setup.auto_kind && !setup.mock && (
        <label className="check">
          <input type="checkbox" checked={form.auto_signin} onChange={(e) => setForm((prev) => ({ ...prev, auto_signin: e.target.checked }))} /> {AUTO_TEXT[setup.auto_kind].label}{' '}
          <HelpTip label="Hilfe zur automatischen Anmeldung">{AUTO_TEXT[setup.auto_kind].help}</HelpTip>
        </label>
      )}
      <div className="row ad-actions">
        <AsyncButton className="btn btn-primary" onClick={save}>
          <Icon name="check" /> Speichern
        </AsyncButton>
        <AsyncButton className="btn" onClick={runTest} disabled={!setup.configured} title={setup.configured ? undefined : 'Erst vollständig einrichten und speichern'}>
          <Icon name="refresh" /> Verbindung testen
        </AsyncButton>
        {setup.updated_at && <span className="small faint">zuletzt geändert {formatDateTime(setup.updated_at)}</span>}
      </div>
      <div aria-live="polite">
        {test && (
          <Alert kind={test.ok ? 'success' : 'error'} title={test.ok ? 'Verbindung erfolgreich' : 'Test fehlgeschlagen'}>
            <span>{test.message}</span>
            {test.ok && test.jwks_ok && <div className="small">Signaturschlüssel des Anbieters sind abrufbar.</div>}
            {test.issuer && <div className="small ad-break">Aussteller: {test.issuer}</div>}
            {test.note && <div className="small">{test.note}</div>}
          </Alert>
        )}
      </div>
    </section>
  );
}

export default function SetupPage() {
  useTitle('Anmeldedienste');
  const q = useApi((signal) => ssoApi.setup(signal), []);
  if (q.initialLoading) return <Loading />;
  if (q.error && !q.data) return <ErrorBox error={q.error} onRetry={q.reload} />;
  const data = q.data;
  if (!data) return null;
  const replaceProvider = (p: ProviderSetup) =>
    q.setData((prev) => {
      const base = prev ?? data;
      return { ...base, providers: base.providers.map((x) => (x.id === p.id ? p : x)) };
    });
  return (
    <div className="stack">
      <section className="card stack-sm">
        <h2>
          Anmelden mit Microsoft, Apple, Google oder dem Schulkonto
          <HelpTip>
            Richten Sie hier die Anbieter ein. Alle Personen können ihr Konto danach im Profil unter „Verbundene Konten“ verbinden; in der Benutzerverwaltung lassen sich Adressen vormerken (z. B. die Apple-IDs und Microsoft-Konten, die die Schule
            ausgibt). Wer sich wie anmelden darf oder verbinden muss, legen die Anmelde-Richtlinien fest. Umgebungsvariablen (<code>SM_SSO_*</code>, <code>SM_OIDC_*</code>) haben Vorrang vor den Angaben hier.
          </HelpTip>
        </h2>
        {data.mock_enabled ? (
          <Alert kind="warning" title="Test-Anbieter aktiv (nur Entwicklung)">
            Nicht eingerichtete Anbieter erscheinen auf der Anmeldeseite als „… (Test)“.
            <HelpTip>Eine interne Seite simuliert die Anmeldung: Es genügt eine E-Mail-Adresse, ein Passwort wird nicht geprüft. In Produktion ist das ausgeschlossen (<code>SM_SSO_DEV_MOCK</code>).</HelpTip>
          </Alert>
        ) : (
          !data.production && <p className="small muted">Test-Anbieter sind abgeschaltet (<code>SM_SSO_DEV_MOCK=0</code>).</p>
        )}
        {!data.base_url.startsWith('https://') && (
          <p className="small muted">
            Weiterleitungs-URIs ohne https.
            <HelpTip>Die Weiterleitungs-URIs basieren auf <code>SM_BASE_URL</code> ({data.base_url}). Echte Anbieter verlangen https.</HelpTip>
          </p>
        )}
      </section>
      {data.providers.map((p) => (
        <ProviderCard key={p.id} setup={p} labels={data.field_labels} onSaved={replaceProvider} />
      ))}
    </div>
  );
}
