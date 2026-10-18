/**
 * Einhängepunkte des Features „anmeldedienste“ (§11.4) in geteilten Seiten.
 * LoginPage: <SsoButtons next hidden /> + SSO_ERROR_MESSAGES, ProfilePage: <IdentitiesSection /> (nach
 * „Zwei-Faktor-Anmeldung“), UsersPage/UserModal: <UserIdentitiesPanel userId /> (Reiter „Verbundene Konten“).
 */
import { useEffect, useState } from 'react';
import { HelpTip } from '../../components/HelpTip';
import { Alert } from '../../components/ui';
import { ssoApi } from './api';
import IdentitiesSectionImpl from './IdentitiesSection';
import { flowOf, privacyText, readHint, silentTarget, SSO_ERROR_MESSAGES as MESSAGES, ssoLoginUrl } from './logic';
import { AppleButton, GoogleButton, MicrosoftButton, RedirectButton } from './OfficialButtons';
import type { SsoProvider } from './types';
import UserIdentitiesPanelImpl from './UserIdentitiesPanel';
import './anmeldedienste.css';

/** Zusätzliche/überschreibende Texte für `/login?sso_error=<code>`. */
export const SSO_ERROR_MESSAGES: Record<string, string> = MESSAGES;

const SILENT_FLAG = 'sm_sso_silent';

function silentAlreadyTried(): boolean {
  try {
    return sessionStorage.getItem(SILENT_FLAG) === '1';
  } catch {
    return true; // ohne Speicher kein stiller Versuch (sonst könnte er sich wiederholen)
  }
}

/**
 * Knöpfe unter dem Formular: je eingeschaltetem Anbieter der offizielle Knopf (Google, Apple, Microsoft) bzw. „Mit … anmelden“
 * (Schulkonto). Ohne eingeschalteten Anbieter erscheint nichts und es wird nichts von Dritten geladen. `add`: weiteres Konto
 * anmelden. Das stille Microsoft-SSO läuft nur auf der Anmeldeseite (nicht bei `add`) und nur einmal je Tab.
 */
export function SsoButtons({ next, hidden, add = false }: { next: string | null; hidden?: boolean; add?: boolean }) {
  const [providers, setProviders] = useState<SsoProvider[] | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  useEffect(() => {
    const ctrl = new AbortController();
    ssoApi
      .providers(ctrl.signal)
      .then((list) => {
        // Nur Google, Apple, Microsoft auf der Anmeldeseite – „Schulkonto“ (OIDC) bewusst nicht (Wunsch Betreiber)
        if (!ctrl.signal.aborted) setProviders(list.filter((p) => p.id !== 'oidc'));
      })
      .catch(() => {
        if (!ctrl.signal.aborted) setProviders([]);
      });
    return () => ctrl.abort();
  }, []);
  const [silent, setSilent] = useState(false);
  useEffect(() => {
    if (!providers || hidden || add) return;
    const q = new URLSearchParams(window.location.search);
    const target = silentTarget(providers, readHint(document.cookie), {
      alreadyTried: silentAlreadyTried(),
      hasMessage: q.has('sso_error') || q.has('sso_silent'),
      add,
    });
    if (!target) return;
    try {
      sessionStorage.setItem(SILENT_FLAG, '1');
    } catch {
      return;
    }
    setSilent(true);
    window.location.replace(ssoLoginUrl(target.provider.id, next, { silent: true }));
  }, [providers, hidden, add, next]);
  if (hidden || !providers?.length || silent) return null;
  const anyMock = providers.some((p) => p.mock);
  const common = { next, add, onError: setMessage };
  return (
    <div className="ad-sso" role="group" aria-labelledby="ad-sso-or">
      <div className="ad-divider" id="ad-sso-or">
        <span>oder</span>
        <HelpTip label="Datenschutz bei der Anmeldung mit Anbietern">{privacyText(providers)}</HelpTip>
      </div>
      {message && (
        <Alert kind="error" title="Anmeldung nicht möglich">
          {message}
        </Alert>
      )}
      <div className="stack-sm">
        {providers.map((p) => {
          const flow = flowOf(p);
          if (flow === 'gis') return <GoogleButton key={p.id} p={p} {...common} />;
          if (flow === 'apple_js') return <AppleButton key={p.id} p={p} {...common} />;
          if (flow === 'microsoft') return <MicrosoftButton key={p.id} p={p} next={next} add={add} />;
          return <RedirectButton key={p.id} p={p} next={next} add={add} />;
        })}
      </div>
      {anyMock && <p className="small faint ad-sso-hint">„(Test)“: Die Anmeldung wird nur simuliert.</p>}
    </div>
  );
}

/** Profil: Abschnitt „Verbundene Konten“ (bringt seine eigene `card` mit). */
export function IdentitiesSection() {
  return <IdentitiesSectionImpl />;
}

/** Benutzerverwaltung: verbundene Anbieter-Konten eines Kontos. */
export function UserIdentitiesPanel({ userId }: { userId: number }) {
  return <UserIdentitiesPanelImpl userId={userId} />;
}
