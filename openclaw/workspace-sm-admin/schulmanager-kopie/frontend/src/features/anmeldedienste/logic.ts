/** Reine Logik der Anmeldedienste (§11.4) – ohne React, mit vitest getestet. */
import { APP_NAME } from '../../brand';
import { formatDateTime } from '../../lib/dates';
import type { ConfigField, MyProvider, ProviderSetup, ProviderStatus, ProviderUpdate, SsoFlow, SsoProvider } from './types';

/** Texte für `?sso_error=<code>` (Login-Seite, Profil, „Konten verbinden“). */
export const SSO_ERROR_MESSAGES: Record<string, string> = {
  not_configured: 'Die Anmeldung über das Schulkonto ist nicht eingerichtet.',
  state: 'Die Anmeldung ist abgelaufen oder wurde in einem anderen Fenster gestartet – bitte erneut versuchen.',
  provider: 'Der Anmeldedienst hat einen Fehler gemeldet. Bitte später erneut versuchen.',
  cancelled: 'Die Anmeldung beim Anbieter wurde abgebrochen.',
  provider_disabled: 'Dieser Anmeldedienst ist nicht (mehr) eingerichtet.',
  unknown_user:
    `Zu diesem Anbieter-Konto gibt es keinen Zugang im ${APP_NAME}. Konto erst im Profil verbinden (mit Benutzername und Passwort anmelden → Profil → „Verbundene Konten“) oder Sekretariat fragen.`,
  account_disabled: 'Dieses Konto ist deaktiviert. Bitte wenden Sie sich an das Sekretariat.',
  method_not_allowed:
    'Diese Art der Anmeldung ist für Ihr Konto nicht freigegeben. Bitte melden Sie sich auf einem der erlaubten Wege an – welche das sind, erfahren Sie im Sekretariat.',
  email_unverified: 'Der Anbieter hat die E-Mail-Adresse dieses Kontos nicht bestätigt.',
  domain_not_allowed: 'Mit diesem Anbieter-Konto ist keine Anmeldung möglich – bitte das Konto der Schule verwenden.',
  already_linked: `Dieses Anbieter-Konto ist bereits mit einem anderen ${APP_NAME}-Konto verbunden.`,
  already_connected: 'Ihr Konto ist bereits mit einem anderen Konto dieses Anbieters verbunden. Bitte zuerst trennen.',
  link_not_allowed: 'Verbundene Konten werden von Ihrer Schule verwaltet – selbst verbinden ist nicht möglich.',
  link_expired: 'Das Verbinden ist abgelaufen, weil die Sitzung beendet oder gewechselt wurde. Bitte anmelden und erneut versuchen.',
};

export interface LoginUrlOptions {
  /** weiteres Konto anmelden (bisherige bleiben angemeldet) */
  add?: boolean;
  /** stilles SSO (`prompt=none`) – scheitert ohne Anbieter-Sitzung ohne Rückfrage */
  silent?: boolean;
  /** E-Mail-Adresse des zuletzt verwendeten Anbieter-Kontos (nur mit `silent`) */
  hint?: string | null;
}

/** Adresse zum Starten der Anmeldung (nur interne `next`-Pfade). */
export function ssoLoginUrl(provider: string, next?: string | null, opts: LoginUrlOptions = {}): string {
  const base = `/api/v1/auth/sso/${encodeURIComponent(provider)}/login`;
  const safe = next && next.startsWith('/') && !next.startsWith('//') && !next.includes('\\') ? next : null;
  const q: string[] = [];
  if (safe) q.push(`next=${encodeURIComponent(safe)}`);
  if (opts.add) q.push('add=true');
  if (opts.silent) {
    q.push('silent=true');
    if (opts.hint) q.push(`hint=${encodeURIComponent(opts.hint)}`);
  }
  return q.length ? `${base}?${q.join('&')}` : base;
}

/** Art der Anmeldung eines Anbieters (Test-Anbieter und unbekannte Werte: gewöhnliche Weiterleitung). */
export function flowOf(p: SsoProvider): SsoFlow {
  if (p.mock) return 'redirect';
  return p.flow === 'gis' || p.flow === 'apple_js' || p.flow === 'microsoft' ? p.flow : 'redirect';
}

/** Skripte Dritter – werden erst geladen, wenn der Anbieter in den Anmeldediensten eingeschaltet ist. */
export const GOOGLE_SCRIPT = 'https://accounts.google.com/gsi/client';
export const APPLE_SCRIPT = 'https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/de_DE/appleid.auth.js';

/** Welche Skripte Dritter eine Anbieterliste nach sich zieht (leer = die Anmeldeseite lädt nichts nach). */
export function externalScripts(providers: SsoProvider[]): string[] {
  const out: string[] = [];
  for (const p of providers) {
    const flow = flowOf(p);
    if (flow === 'gis' && p.client_id) out.push(GOOGLE_SCRIPT);
    if (flow === 'apple_js' && p.client_id && p.redirect_uri) out.push(APPLE_SCRIPT);
  }
  return out;
}

export const HINT_COOKIE = 'sm_sso_hint';

/**
 * Zuletzt verwendeter Anbieter aus dem Cookie `sm_sso_hint` (nur die Kennung, z. B. `microsoft`); Abmelden löscht ihn.
 * Die E-Mail-Adresse für die stille Anmeldung liegt verschlüsselt in einem httponly-Cookie, das nur der Server liest.
 */
export function readHint(cookie: string): { provider: string } | null {
  for (const part of cookie.split(';')) {
    const [name, ...rest] = part.trim().split('=');
    if (name !== HINT_COOKIE) continue;
    let value = '';
    try {
      value = decodeURIComponent(rest.join('='));
    } catch {
      return null;
    }
    const provider = value.split('|')[0] ?? '';
    return /^[a-z]+$/.test(provider) ? { provider } : null;
  }
  return null;
}

/**
 * Soll beim Öffnen der Anmeldeseite still angemeldet werden (Microsoft)? Nur wenn der Anbieter aktiv ist, die
 * automatische Anmeldung eingeschaltet ist, hier zuletzt dieser Anbieter benutzt wurde, noch kein Versuch lief und
 * die Seite nicht gerade mit einer Meldung (Fehler, Abbruch, Kontowechsel) aufgerufen wurde.
 */
export function silentTarget(
  providers: SsoProvider[],
  hint: { provider: string } | null,
  opts: { alreadyTried: boolean; hasMessage: boolean; add: boolean },
): { provider: SsoProvider } | null {
  if (!hint || opts.alreadyTried || opts.hasMessage || opts.add) return null;
  const p = providers.find((x) => x.id === hint.provider);
  if (!p || p.mock || flowOf(p) !== 'microsoft' || !p.auto) return null;
  return { provider: p };
}

/** Fehlertext zu einem Fehler von `POST /auth/sso/{id}/token` (Antwort-Code des Servers). */
export function tokenErrorMessage(code: string | undefined): string {
  return (code && SSO_ERROR_MESSAGES[code]) || SSO_ERROR_MESSAGES.provider;
}

/** Kurzer Datenschutzhinweis zu den Anmeldediensten (HelpTip auf der Anmeldeseite). */
export function privacyText(providers: SsoProvider[]): string {
  const real = providers.filter((p) => !p.mock);
  if (!real.length) return 'Die Anmeldung über Anbieter ist hier nur eine Simulation – es wird nichts an Dritte gesendet.';
  const names = real.map((p) => p.label).join(', ');
  const scripts = externalScripts(real).length > 0;
  return (
    `Erst wenn Sie einen Knopf benutzen, geht es zu ${names}. ` +
    (scripts ? 'Für Google bzw. Apple lädt diese Seite deren Anmelde-Skript von deren Servern; dabei sieht der Anbieter Ihre IP-Adresse und Ihren Browser. ' : '') +
    `${APP_NAME} erhält nur Kennung, Name und E-Mail-Adresse des Kontos, kein Passwort. ` +
    'Die automatische Anmeldung (wenn eingeschaltet) wirkt nur, wenn Sie beim Anbieter in diesem Browser schon angemeldet sind; nach dem Abmelden ist sie bis zur nächsten Anmeldung aus.'
  );
}

export function buttonLabel(p: SsoProvider): string {
  return `Mit ${p.label} anmelden${p.mock ? ' (Test)' : ''}`;
}

/** Datum eines Zeitstempels („06.10.2026“). */
export function dayOf(ts: string | null | undefined): string {
  return formatDateTime(ts).split(',')[0] ?? '–';
}

/** Zeile unter dem Anbieter im Profil. */
export function statusLine(p: MyProvider): string {
  const ident = p.identity;
  if (p.linked && ident) {
    const who = ident.email ? `Verbunden als ${ident.email}` : 'Verbunden';
    const since = ident.created_at ? ` · seit ${dayOf(ident.created_at)}` : '';
    const last = ident.last_login_at ? ` · zuletzt angemeldet ${formatDateTime(ident.last_login_at)}` : '';
    return `${who}${since}${last}`;
  }
  if (ident?.pending) {
    return `Von der Schule vorgemerkt${ident.email ? ` für ${ident.email}` : ''} – wird bei der ersten Anmeldung mit ${p.label} verbunden.`;
  }
  if (!p.available) return 'Dieser Anbieter ist an der Schule noch nicht eingerichtet.';
  return p.required ? 'Noch nicht verbunden – bitte verbinden (Pflicht).' : 'Nicht verbunden';
}

export type Notice = { kind: 'success' | 'error'; text: string };

/** Meldung nach der Rückkehr vom Anbieter (`?verbunden=` bzw. `?sso_error=`). */
export function returnNotice(params: URLSearchParams, labelOf: (id: string) => string): Notice | null {
  const error = params.get('sso_error');
  if (error) return { kind: 'error', text: SSO_ERROR_MESSAGES[error] ?? 'Das Verbinden ist fehlgeschlagen.' };
  const ok = params.get('verbunden');
  if (ok) return { kind: 'success', text: `${labelOf(ok)} ist jetzt mit Ihrem Konto verbunden.` };
  return null;
}

export const STATUS_LABELS: Record<ProviderStatus, string> = {
  active: 'Aktiv',
  mock: 'Test-Anbieter aktiv',
  disabled: 'Eingerichtet, ausgeschaltet',
  missing: 'Nicht eingerichtet',
};

export const STATUS_BADGE: Record<ProviderStatus, string> = {
  active: 'badge-success',
  mock: 'badge-warning',
  disabled: 'badge-info',
  missing: '',
};

/** „schule.de, @appleid.schule.de\nx.de“ → `["appleid.schule.de", "schule.de", "x.de"]` */
export function parseDomains(text: string): string[] {
  const out = new Set<string>();
  for (const part of text.split(/[\s,;]+/)) {
    const d = part.trim().toLowerCase().replace(/^@+/, '');
    if (d) out.add(d);
  }
  return [...out].sort();
}

export const SECRET_FIELDS: ReadonlySet<ConfigField> = new Set<ConfigField>(['client_secret', 'private_key']);

export type SetupForm = Partial<Record<ConfigField, string>> & { enabled: boolean; auto_signin: boolean };

export function initialForm(p: ProviderSetup): SetupForm {
  const form: SetupForm = { enabled: p.db_enabled, auto_signin: p.auto_signin };
  for (const f of p.field_names) {
    if (SECRET_FIELDS.has(f)) form[f] = '';
    else {
      const v = p.fields[f];
      form[f] = Array.isArray(v) ? v.join(', ') : (v ?? '');
    }
  }
  return form;
}

/** Formular → `PUT /sso/providers/{id}`: Geheimnisse nur, wenn eingegeben; Felder aus Umgebungsvariablen nie. */
export function buildUpdate(p: ProviderSetup, form: SetupForm): ProviderUpdate {
  const body: ProviderUpdate = { enabled: form.enabled };
  if (p.auto_kind) body.auto_signin = form.auto_signin;
  const target = body as Record<string, unknown>;
  for (const f of p.field_names) {
    if (p.env_fields.includes(f)) continue;
    const value = form[f] ?? '';
    if (f === 'allowed_domains') target[f] = parseDomains(value);
    else if (SECRET_FIELDS.has(f)) {
      if (value.trim()) target[f] = value.trim();
    } else target[f] = value.trim();
  }
  return body;
}
