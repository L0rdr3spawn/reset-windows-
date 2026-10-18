/**
 * Produktmarke – einzige Stelle für den sichtbaren Produktnamen im Frontend.
 *
 * Technische Namen bleiben unverändert: Python-Paket `schulmanager`, Cookies `sm_*`, Umgebungsvariablen `SM_*`,
 * Docker-Namen, Routen. Hier ändert sich nur, was Menschen sehen. Backend-Gegenstück: `schulmanager/branding.py`.
 * Der Schulname aus den Einstellungen ist zusätzlich („Schulpuls · Gesamtschule Musterstadt“), siehe {@link withSchool}.
 */
import logoUrl from './assets/logo.svg';
import logoMonoUrl from './assets/logo-mono.svg';
import wordmarkUrl from './assets/logo-wordmark.svg';
import wordmarkDarkUrl from './assets/logo-wordmark-dark.svg';

/** Produktname, wie er überall sichtbar steht (Kopfleiste, Titel, Login, Briefe). Grammatik: der Schulpuls. */
export const APP_NAME = 'Schulpuls';
/** Kurzform für sehr enge Stellen (eingeklappte Leiste, Platzhalter-Kacheln). */
export const APP_SHORT_NAME = 'Puls';
/** Slogan für Login, Über-Seite und Druck. */
export const APP_TAGLINE = 'Stundenplan, Klassenbuch und Nachrichten – im Takt der Schule.';

/** Bildmarke farbig (Kachel + Pulslinie), z. B. für <img>, Favicon, App-Icon. */
export const LOGO_URL: string = logoUrl;
/** Bildmarke einfarbig (currentColor), ohne Kachel. */
export const LOGO_MONO_URL: string = logoMonoUrl;
/** Wortmarke für helle Flächen. */
export const WORDMARK_URL: string = wordmarkUrl;
/** Wortmarke für dunkle Flächen. */
export const WORDMARK_DARK_URL: string = wordmarkDarkUrl;

/** Dokumenttitel: „Seite · Schulpuls“ bzw. nur der Produktname. */
export function pageTitle(title?: string | null): string {
  return title ? `${title} · ${APP_NAME}` : APP_NAME;
}

/** „Schulpuls · Schulname“ – der eigene Schulname aus den Einstellungen bleibt unberührt und kommt dazu. */
export function withSchool(schoolName?: string | null): string {
  const s = (schoolName ?? '').trim();
  return s && s !== APP_NAME ? `${APP_NAME} · ${s}` : APP_NAME;
}
