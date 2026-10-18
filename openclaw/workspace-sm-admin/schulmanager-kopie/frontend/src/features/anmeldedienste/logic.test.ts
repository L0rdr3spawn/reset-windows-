import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  APPLE_SCRIPT,
  buildUpdate,
  buttonLabel,
  externalScripts,
  flowOf,
  GOOGLE_SCRIPT,
  initialForm,
  parseDomains,
  privacyText,
  readHint,
  returnNotice,
  silentTarget,
  SSO_ERROR_MESSAGES,
  ssoLoginUrl,
  statusLine,
  tokenErrorMessage,
} from './logic';
import { loadScript } from './OfficialButtons';
import { SsoButtons } from './slots';
import type { MyProvider, ProviderSetup } from './types';

describe('ssoLoginUrl', () => {
  it('gibt nur interne Rücksprungziele weiter', () => {
    expect(ssoLoginUrl('microsoft', '/stundenplan?woche=2')).toBe('/api/v1/auth/sso/microsoft/login?next=%2Fstundenplan%3Fwoche%3D2');
    expect(ssoLoginUrl('google', '//evil.example')).toBe('/api/v1/auth/sso/google/login');
    expect(ssoLoginUrl('apple', 'https://evil.example')).toBe('/api/v1/auth/sso/apple/login');
    expect(ssoLoginUrl('oidc', null)).toBe('/api/v1/auth/sso/oidc/login');
  });
  it('kennzeichnet Test-Anbieter', () => {
    expect(buttonLabel({ id: 'apple', label: 'Apple', mock: true })).toBe('Mit Apple anmelden (Test)');
    expect(buttonLabel({ id: 'apple', label: 'Apple', mock: false })).toBe('Mit Apple anmelden');
  });
});

describe('Fehlertexte und Rückkehr', () => {
  it('hat Texte für alle Codes des Backends', () => {
    for (const code of ['method_not_allowed', 'already_linked', 'link_not_allowed', 'link_expired', 'email_unverified', 'provider_disabled', 'unknown_user']) {
      expect(SSO_ERROR_MESSAGES[code]).toBeTruthy();
    }
    expect(SSO_ERROR_MESSAGES.unknown_user).toMatch(/Profil verbinden.*Sekretariat/);
  });
  it('liest ?verbunden= und ?sso_error=', () => {
    const label = (id: string) => (id === 'google' ? 'Google' : id);
    expect(returnNotice(new URLSearchParams('verbunden=google'), label)).toEqual({ kind: 'success', text: 'Google ist jetzt mit Ihrem Konto verbunden.' });
    expect(returnNotice(new URLSearchParams('sso_error=already_linked'), label)?.kind).toBe('error');
    expect(returnNotice(new URLSearchParams('sso_error=xyz'), label)?.text).toBe('Das Verbinden ist fehlgeschlagen.');
    expect(returnNotice(new URLSearchParams(''), label)).toBeNull();
  });
});

describe('statusLine', () => {
  const base: MyProvider = {
    id: 'microsoft', label: 'Microsoft', mock: false, available: true, required: false, linked: false, identity: null,
    can_link: true, can_unlink: false, unlink_block: null,
  };
  it('beschreibt verbunden, vorgemerkt, nicht eingerichtet', () => {
    const identity = { provider: 'microsoft', label: 'Microsoft', email: 'a@schule.de', email_verified: true, linked: true, pending: false, mock: false, managed: false, created_at: '2026-10-01T08:00:00Z', last_login_at: null };
    expect(statusLine({ ...base, linked: true, identity })).toMatch(/^Verbunden als a@schule\.de · seit \d\d\.10\.2026$/);
    expect(statusLine({ ...base, identity: { ...identity, linked: false, pending: true } })).toMatch(/vorgemerkt für a@schule\.de/);
    expect(statusLine({ ...base, available: false })).toMatch(/nicht eingerichtet/);
    expect(statusLine({ ...base, required: true })).toMatch(/Pflicht/);
  });
});

describe('Einrichtungsformular', () => {
  const setup: ProviderSetup = {
    id: 'microsoft', label: 'Microsoft', default_label: 'Microsoft', status: 'disabled', enabled: false, configured: true, db_enabled: false,
    mock: false, auto_signin: false, auto_kind: 'silent', origin: 'https://s.example:10489', js_origins: [], warnings: [], script_hosts: [],
    fields: { client_id: 'abc', tenant: '', label: '', allowed_domains: ['schule.de'] },
    field_names: ['client_id', 'client_secret', 'tenant', 'label', 'allowed_domains'], required: ['client_id', 'client_secret'], missing: [],
    secrets: { client_secret: true }, env_fields: ['tenant'], env_vars: { tenant: 'SM_SSO_MICROSOFT_TENANT' }, redirect_uri: 'x', updated_at: null,
  };
  it('lässt leere Geheimnisse und Umgebungsfelder weg', () => {
    const form = initialForm(setup);
    expect(form.client_secret).toBe('');
    expect(form.allowed_domains).toBe('schule.de');
    const body = buildUpdate(setup, { ...form, enabled: true, allowed_domains: '@Schule.de, appleid.schule.de\nschule.de' });
    expect(body).toEqual({ enabled: true, auto_signin: false, client_id: 'abc', label: '', allowed_domains: ['appleid.schule.de', 'schule.de'] });
    expect(buildUpdate(setup, { ...form, client_secret: ' neu ' }).client_secret).toBe('neu');
  });
  it('parseDomains', () => {
    expect(parseDomains(' A.de;b.de  @c.de ')).toEqual(['a.de', 'b.de', 'c.de']);
  });
});

describe('SsoButtons', () => {
  it('zeigt vor dem Laden nichts an', () => {
    expect(renderToStaticMarkup(createElement(SsoButtons, { next: null }))).toBe('');
    expect(renderToStaticMarkup(createElement(SsoButtons, { next: '/x', hidden: true }))).toBe('');
  });
});

describe('ssoLoginUrl mit Optionen', () => {
  it('hängt add/silent/hint an', () => {
    expect(ssoLoginUrl('microsoft', '/x', { add: true })).toBe('/api/v1/auth/sso/microsoft/login?next=%2Fx&add=true');
    expect(ssoLoginUrl('microsoft', null, { silent: true, hint: 'a@schule.de' })).toBe('/api/v1/auth/sso/microsoft/login?silent=true&hint=a%40schule.de');
    expect(ssoLoginUrl('microsoft', null, { hint: 'a@schule.de' })).toBe('/api/v1/auth/sso/microsoft/login');
  });
});

describe('Anbieter-Skripte nur bei eingeschaltetem Anbieter', () => {
  const google = { id: 'google', label: 'Google', mock: false, flow: 'gis' as const, client_id: 'cid', auto: false };
  const apple = { id: 'apple', label: 'Apple', mock: false, flow: 'apple_js' as const, client_id: 'de.x', redirect_uri: 'https://s.example/api/v1/auth/sso/apple/callback' };
  const ms = { id: 'microsoft', label: 'Microsoft', mock: false, flow: 'microsoft' as const };
  it('lädt ohne Anbieter oder bei Test-Anbietern nichts', () => {
    expect(externalScripts([])).toEqual([]);
    expect(externalScripts([{ ...google, mock: true }, { id: 'apple', label: 'Apple', mock: true }])).toEqual([]);
    expect(externalScripts([ms, { id: 'oidc', label: 'Schulkonto', mock: false }])).toEqual([]);
  });
  it('nennt Google/Apple-Skripte erst bei aktivem Anbieter (mit Client-ID)', () => {
    expect(externalScripts([google, ms])).toEqual([GOOGLE_SCRIPT]);
    expect(externalScripts([google, apple])).toEqual([GOOGLE_SCRIPT, APPLE_SCRIPT]);
    expect(externalScripts([{ ...google, client_id: undefined }])).toEqual([]);
  });
  it('flowOf: Test-Anbieter und Unbekanntes sind Weiterleitung', () => {
    expect(flowOf(google)).toBe('gis');
    expect(flowOf({ ...google, mock: true })).toBe('redirect');
    expect(flowOf({ id: 'oidc', label: 'x', mock: false })).toBe('redirect');
    expect(flowOf({ id: 'x', label: 'x', mock: false, flow: 'bogus' as never })).toBe('redirect');
  });
  it('Datenschutztext nennt Skripte nur, wenn welche geladen werden', () => {
    expect(privacyText([ms])).not.toMatch(/Skript/);
    expect(privacyText([google])).toMatch(/Skript/);
    expect(privacyText([{ ...google, mock: true }])).toMatch(/Simulation/);
  });
});

describe('loadScript', () => {
  const appended: { src: string; onload?: () => void; onerror?: () => void }[] = [];
  const fakeDocument = {
    createElement: () => ({ remove() {} }) as Record<string, unknown>,
    head: { appendChild: (el: { src: string }) => appended.push(el) },
  };
  afterEach(() => {
    vi.unstubAllGlobals();
    appended.length = 0;
  });
  it('fügt das Skript genau einmal ein; Fehler erlaubt neuen Versuch', async () => {
    vi.stubGlobal('document', fakeDocument);
    const a = loadScript('https://a.example/x.js');
    const b = loadScript('https://a.example/x.js');
    expect(appended).toHaveLength(1);
    appended[0].onload?.();
    await Promise.all([a, b]);
    const c = loadScript('https://b.example/y.js');
    appended[1].onerror?.();
    await expect(c).rejects.toThrow();
    void loadScript('https://b.example/y.js');
    expect(appended).toHaveLength(3);
  });
});

describe('Hinweis-Cookie und stilles SSO', () => {
  const ms = { id: 'microsoft', label: 'Microsoft', mock: false, flow: 'microsoft' as const, auto: true };
  const hint = { provider: 'microsoft' };
  const none = { alreadyTried: false, hasMessage: false, add: false };
  it('liest sm_sso_hint', () => {
    expect(readHint('a=1; sm_sso_hint=microsoft; b=2')).toEqual(hint);
    expect(readHint('sm_sso_hint=microsoft%7Ca%40schule.de')).toEqual(hint); // alter Cookie mit E-Mail: nur die Kennung zählt
    expect(readHint('a=1')).toBeNull();
    expect(readHint('sm_sso_hint=%E0%A4%A')).toBeNull();
    expect(readHint('sm_sso_hint=Micro%20soft')).toBeNull();
  });
  it('stilles SSO nur bei aktivem Microsoft mit Auto-Anmeldung und Hinweis', () => {
    expect(silentTarget([ms], hint, none)?.provider.id).toBe('microsoft');
    expect(silentTarget([ms], null, none)).toBeNull();
    expect(silentTarget([{ ...ms, auto: false }], hint, none)).toBeNull();
    expect(silentTarget([{ ...ms, mock: true }], hint, none)).toBeNull();
    expect(silentTarget([ms], { provider: 'google' }, none)).toBeNull();
    expect(silentTarget([ms], hint, { ...none, alreadyTried: true })).toBeNull();
    expect(silentTarget([ms], hint, { ...none, hasMessage: true })).toBeNull();
    expect(silentTarget([ms], hint, { ...none, add: true })).toBeNull();
  });
  it('Token-Fehlertexte', () => {
    expect(tokenErrorMessage('unknown_user')).toBe(SSO_ERROR_MESSAGES.unknown_user);
    expect(tokenErrorMessage(undefined)).toBe(SSO_ERROR_MESSAGES.provider);
    expect(tokenErrorMessage('method_not_allowed')).toBe(SSO_ERROR_MESSAGES.method_not_allowed);
  });
});
