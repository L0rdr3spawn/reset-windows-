/**
 * Offizielle Anmelde-Knöpfe der Anbieter (§11.4), nur für Anbieter, die in den Anmeldediensten eingeschaltet sind:
 * - Google: „Sign in with Google“ (Google Identity Services, Skript erst jetzt von accounts.google.com), optional One Tap
 *   mit automatischer Auswahl. Das ID-Token geht an `POST /auth/sso/google/token` (Prüfung auf dem Server).
 * - Apple: „Sign in with Apple“ (JS, Popup) – Skript erst jetzt von appleid.cdn-apple.com.
 * - Microsoft: Knopf nach den Branding-Richtlinien (Logo + „Mit Microsoft anmelden“), reine Weiterleitung, kein Skript.
 * Lässt sich ein Skript nicht laden (Werbeblocker, Netzwerk), erscheint der gewöhnliche Knopf mit Weiterleitung.
 */
import { useEffect, useRef, useState } from 'react';
import { ApiError } from '../../api/client';
import { Icon } from '../../components/Icon';
import { ssoApi } from './api';
import { APPLE_SCRIPT, GOOGLE_SCRIPT, readHint, ssoLoginUrl, tokenErrorMessage } from './logic';
import type { SsoProvider } from './types';

const scripts = new Map<string, Promise<void>>();

/** Lädt ein Skript genau einmal; schlägt das Laden fehl, kann es später erneut versucht werden. */
export function loadScript(src: string): Promise<void> {
  const known = scripts.get(src);
  if (known) return known;
  const p = new Promise<void>((resolve, reject) => {
    const el = document.createElement('script');
    el.src = src;
    el.async = true;
    el.referrerPolicy = 'no-referrer';
    el.onload = () => resolve();
    el.onerror = () => {
      scripts.delete(src);
      el.remove();
      reject(new Error('script'));
    };
    document.head.appendChild(el);
  });
  scripts.set(src, p);
  return p;
}

interface GoogleId {
  initialize(cfg: Record<string, unknown>): void;
  renderButton(el: HTMLElement, opts: Record<string, unknown>): void;
  prompt(): void;
  cancel(): void;
}
interface AppleAuth {
  init(cfg: Record<string, unknown>): void;
}
type Win = { google?: { accounts?: { id?: GoogleId } }; AppleID?: { auth?: AppleAuth } };

interface Common {
  next: string | null;
  add: boolean;
  onError: (message: string) => void;
}

function codeOf(err: unknown): string | undefined {
  if (err instanceof ApiError && err.detail && typeof err.detail === 'object') return (err.detail as { code?: string }).code;
  return undefined;
}

/** Gewöhnlicher Knopf mit Weiterleitung (Test-Anbieter, Schulkonto, Rückfall). */
export function RedirectButton({ p, next, add }: { p: SsoProvider; next: string | null; add: boolean }) {
  return (
    <a className="btn w-100 ad-sso-btn" href={ssoLoginUrl(p.id, next, { add })} aria-label={`Mit ${p.label} anmelden${p.mock ? ' (Test)' : ''}`}>
      <Icon name="key" />
      <span className="ad-sso-text">
        Mit {p.label} anmelden{p.mock && <span className="ad-test"> (Test)</span>}
      </span>
    </a>
  );
}

/** Microsoft-Logo (vier Quadrate) – unverändert nach den Branding-Richtlinien von Microsoft. */
function MicrosoftLogo() {
  return (
    <svg className="ad-ms-logo" width="21" height="21" viewBox="0 0 21 21" aria-hidden="true" focusable="false">
      <rect x="1" y="1" width="9" height="9" fill="#f25022" />
      <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
      <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
      <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
    </svg>
  );
}

export function MicrosoftButton({ p, next, add }: { p: SsoProvider; next: string | null; add: boolean }) {
  return (
    <a className="ad-ms" href={ssoLoginUrl(p.id, next, { add })} aria-label="Mit Microsoft anmelden (Arbeits- oder Schulkonto)">
      <MicrosoftLogo />
      <span>Mit Microsoft anmelden</span>
    </a>
  );
}

export function GoogleButton({ p, next, add, onError }: Common & { p: SsoProvider }) {
  const box = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);
  const [round, setRound] = useState(0);
  useEffect(() => {
    let alive = true;
    let id: GoogleId | undefined;
    void (async () => {
      try {
        await loadScript(GOOGLE_SCRIPT);
        const { nonce } = await ssoApi.nonce(p.id);
        id = (window as unknown as Win).google?.accounts?.id;
        if (!alive || !id || !box.current) return;
        const hint = readHint(document.cookie);
        const auto = !!p.auto && !add;
        id.initialize({
          client_id: p.client_id,
          nonce,
          callback: async (resp: { credential?: string }) => {
            if (!resp.credential) return;
            try {
              const done = await ssoApi.token(p.id, resp.credential, next, add);
              window.location.assign(done.next || '/');
            } catch (e) {
              const code = codeOf(e);
              onError(tokenErrorMessage(code));
              if (code === 'state' || code === 'provider') setRound((r) => r + 1);
            }
          },
          auto_select: auto && hint?.provider === p.id,
          cancel_on_tap_outside: false,
          use_fedcm_for_button: true,
          itp_support: true,
          context: 'signin',
        });
        id.renderButton(box.current, {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          text: 'signin_with',
          shape: 'rectangular',
          logo_alignment: 'left',
          locale: 'de',
          width: Math.max(200, Math.min(400, box.current.offsetWidth || 300)),
        });
        if (auto) id.prompt();
      } catch {
        if (alive) setFailed(true);
      }
    })();
    return () => {
      alive = false;
      try {
        id?.cancel();
      } catch {
        /* nichts anzuzeigen */
      }
    };
  }, [p.id, p.client_id, p.auto, next, add, onError, round]);
  if (failed) return <RedirectButton p={p} next={next} add={add} />;
  return <div ref={box} className="ad-gis" aria-label="Mit Google anmelden" />;
}

export function AppleButton({ p, next, add, onError }: Common & { p: SsoProvider }) {
  const [failed, setFailed] = useState(false);
  const [round, setRound] = useState(0);
  useEffect(() => {
    let alive = true;
    const onOk = async (ev: Event) => {
      const idToken = (ev as CustomEvent<{ authorization?: { id_token?: string } }>).detail?.authorization?.id_token;
      if (!idToken) return;
      try {
        const done = await ssoApi.token(p.id, idToken, next, add);
        window.location.assign(done.next || '/');
      } catch (e) {
        const code = codeOf(e);
        onError(tokenErrorMessage(code));
        if (code === 'state' || code === 'provider') setRound((r) => r + 1);
      }
    };
    const onFail = (ev: Event) => {
      const err = (ev as CustomEvent<{ error?: string }>).detail?.error;
      if (err && err !== 'popup_closed_by_user' && err !== 'user_cancelled_authorize') onError(tokenErrorMessage('provider'));
    };
    document.addEventListener('AppleIDSignInOnSuccess', onOk);
    document.addEventListener('AppleIDSignInOnFailure', onFail);
    void (async () => {
      try {
        await loadScript(APPLE_SCRIPT);
        const { nonce } = await ssoApi.nonce(p.id);
        const auth = (window as unknown as Win).AppleID?.auth;
        if (!alive || !auth) return;
        auth.init({ clientId: p.client_id, scope: 'name email', redirectURI: p.redirect_uri, state: 'sm', nonce, usePopup: true });
      } catch {
        if (alive) setFailed(true);
      }
    })();
    return () => {
      alive = false;
      document.removeEventListener('AppleIDSignInOnSuccess', onOk);
      document.removeEventListener('AppleIDSignInOnFailure', onFail);
    };
  }, [p.id, p.client_id, p.redirect_uri, next, add, onError, round]);
  if (failed) return <RedirectButton p={p} next={next} add={add} />;
  return (
    <div className="ad-apple">
      <div id="appleid-signin" data-color="black" data-border="true" data-type="sign in" data-width="280" data-height="44" data-border-radius="4" />
    </div>
  );
}
