/** Formulare des Features „konto“: Passwort-Manager-taugliche Attribute (echte Formulare, autocomplete). */
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { AuthProvider } from '../../context/AuthContext';
import { ToastProvider } from '../../context/ToastContext';
import { CodeInput, NewPasswordForm } from './components';
import ForgotPasswordPage from './ForgotPasswordPage';
import { ForgotPasswordLink } from './slots';

const count = (html: string, re: RegExp) => html.match(re)?.length ?? 0;

const inRouter = (el: ReturnType<typeof createElement>, url = '/') =>
  renderToStaticMarkup(createElement(MemoryRouter, { initialEntries: [url] }, createElement(ToastProvider, null, createElement(AuthProvider, null, el))));

describe('konto: Formulare', () => {
  it('Neues Passwort: Benutzername + zweimal new-password in einem <form>', () => {
    const html = renderToStaticMarkup(createElement(NewPasswordForm, { username: 'anna.m', minLength: 8, onSubmit: async () => undefined }));
    expect(html.startsWith('<form')).toBe(true);
    expect(html).toMatch(/<input[^>]*autocomplete="username"[^>]*>/i);
    const user = html.match(/<input[^>]*autocomplete="username"[^>]*>/i)?.[0] ?? '';
    expect(user).toMatch(/name="username"/);
    expect(user).toMatch(/value="anna.m"/);
    expect(user).toMatch(/readonly/i);
    expect(count(html, /autocomplete="new-password"/gi)).toBe(2);
    expect(html).toContain('Mindestens 8 Zeichen');
  });

  it('Code-Feld: one-time-code, numerische Tastatur', () => {
    const html = renderToStaticMarkup(createElement(CodeInput, { id: 'c', value: '', onChange: () => undefined }));
    expect(html).toMatch(/autocomplete="one-time-code"/i);
    expect(html).toMatch(/inputmode="numeric"/i);
  });

  it('Passwort vergessen: ein Feld (username), kein Kanal-Auswahlfeld', () => {
    const html = inRouter(createElement(ForgotPasswordPage), '/passwort-vergessen');
    const form = html.match(/<form[\s\S]*?<\/form>/)?.[0] ?? '';
    expect(form).toMatch(/<input[^>]*autocomplete="username"[^>]*name="username"/i);
    expect(html).not.toContain('type="radio"');
    expect(form.match(/<input/g)?.length).toBe(1);
    expect(html).toContain('Code senden');
  });

  it('Login-Link mit Erfolgsmeldung nach dem Zurücksetzen', () => {
    expect(inRouter(createElement(ForgotPasswordLink), '/login')).not.toContain('Passwort geändert');
    const html = inRouter(createElement(ForgotPasswordLink), '/login?reset=ok');
    expect(html).toContain('Bitte melden Sie sich neu an.');
    expect(html).toContain('href="/passwort-vergessen"');
  });
});
