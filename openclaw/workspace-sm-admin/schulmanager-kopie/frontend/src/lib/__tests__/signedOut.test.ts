/**
 * Ein Abmelden-Weg + Seite „Abgemeldet“: Quelltextprüfung (Layout/Profil/Benutzermenü brauchen ein DOM) und die
 * Zielwahl nach dem Abmelden.
 */
import { describe, expect, it } from 'vitest';
import { SIGNED_OUT_PATH, signedOutTarget } from '../../context/AuthContext';

const SRC = import.meta.glob(
  ['../../components/Layout.tsx', '../../components/AccountSwitcher.tsx', '../../pages/ProfilePage.tsx', '../../pages/SignedOutPage.tsx', '../../context/AuthContext.tsx', '../../App.tsx'],
  { query: '?raw', import: 'default', eager: true },
) as Record<string, string>;
const src = (name: string) => SRC[`../../${name}`] ?? '';

describe('Abmelden', () => {
  it('Ziel: Kontoauswahl nur, wenn weitere Konten angemeldet sind', () => {
    expect(signedOutTarget(0)).toBe('/login');
    expect(signedOutTarget(2)).toBe(SIGNED_OUT_PATH);
    expect(SIGNED_OUT_PATH).toBe('/abgemeldet');
  });

  it('„Abmelden“ unten in der Seitenleiste (außerhalb des scrollenden Menüs) und im Benutzermenü, beide mit Rückfrage', () => {
    const layout = src('components/Layout.tsx');
    const aside = layout.slice(layout.indexOf('<aside'), layout.indexOf('</aside>'));
    expect(aside).toContain('setConfirmLogout(true)');
    expect(aside).not.toContain('void logout()');
    expect(aside.indexOf('sidebar-logout')).toBeGreaterThan(aside.indexOf('</nav>'));
    const menu = layout.slice(layout.indexOf('function UserMenu'), layout.indexOf('function BottomNav'));
    expect(menu).toContain('onLogout={() => setLoggingOut(true)}');
    expect(menu).toContain('<LogoutConfirm');
    const sw = src('components/AccountSwitcher.tsx');
    expect(sw).toContain('Möchten Sie sich wirklich abmelden?');
    expect(sw).toContain('Ja, abmelden');
    expect(sw).not.toMatch(/logoutOther/);
  });

  it('Profil & Sicherheit: kein normales „Abmelden“, nur Sitzungen beenden', () => {
    const p = src('pages/ProfilePage.tsx');
    expect(p).not.toMatch(/>\s*Abmelden\s*</);
    expect(p).toContain('Alle anderen Sitzungen beenden');
  });

  it('nach dem Abmelden: kein Auto-Wechsel, Neuladen per replace', () => {
    const a = src('context/AuthContext.tsx');
    expect(a).not.toContain('switched');
    expect(a).toContain('window.location.replace(signedOutTarget(');
    expect(a).toContain("'pageshow'");
  });

  it('Seite „Abgemeldet“: Route, Konto wählen, Konto abmelden, anderes Konto anmelden', () => {
    expect(src('App.tsx')).toContain('path="/abgemeldet"');
    const s = src('pages/SignedOutPage.tsx');
    expect(s).toContain('Sie sind abgemeldet.');
    expect(s).toContain('switchAccount(');
    expect(s).toContain('logoutOther(');
    expect(s).toContain('to="/login"');
    expect(s).toContain('<Navigate to="/login"');
    expect(s).not.toContain('className="explain"');
  });
});
