/**
 * Lizenz der Schule (`/lizenz`, Sperrseite, Hinweis-Balken): Beschriftungen und Entscheidungen ohne Oberfläche –
 * damit testbar. Die Stufen berechnet der Server (`licensing.evaluate`): gültig (ggf. Vorwarnung) → Kulanzzeit
 * (nur lesen) → gesperrt.
 */
import type { LicenseBrief } from '../api/types';

export type LicenseState = 'valid' | 'grace' | 'locked';

export const STATE_LABEL: Record<LicenseState, [string, string]> = {
  valid: ['gültig', 'badge-success'],
  grace: ['Kulanzzeit – nur Lesen', 'badge-warning'],
  locked: ['gesperrt', 'badge-danger'],
};

/** Status beim Anbieter (Antwort des Lizenzservers). */
export const PROVIDER_STATUS: Record<string, string> = {
  active: 'aktiv',
  expired: 'Abo abgelaufen',
  paused: 'pausiert',
  cancelled: 'gekündigt',
  unknown: 'dem Anbieter unbekannt',
  unbound: 'nicht gebunden',
  bound_elsewhere: 'an anderen Server gebunden',
};

/** Zustand eines Servers der Schule (`servers` der Prüf-Antwort). */
export const SERVER_STATE: Record<string, [string, string]> = {
  active: ['aktiv', 'badge-success'],
  blocked: ['gesperrt', 'badge-danger'],
  unbound: ['nicht aktiviert', 'badge-info'],
  paused: ['pausiert', 'badge-warning'],
  cancelled: ['gekündigt', 'badge-danger'],
  expired: ['Abo abgelaufen', 'badge-warning'],
  silent: ['ohne Kontakt', 'badge-warning'],
};

export function stateLabel(state: string | undefined): [string, string] {
  return STATE_LABEL[state as LicenseState] ?? [state ?? '–', 'badge'];
}

/** Frische Instanz ohne Lizenzschlüssel (Auslieferung): Begrüßung statt Sperre. */
export function isWelcome(reason: string | undefined): boolean {
  return reason === 'missing';
}

/** Überschrift der Sperrseite je nach Grund. */
export function lockedTitle(reason: string | undefined): string {
  if (isWelcome(reason)) return 'Willkommen – bitte Lizenz eingeben';
  if (reason === 'paused') return 'Die Lizenz dieser Schule ist pausiert';
  if (reason === 'offline' || reason === 'unconfirmed') return 'Die Lizenz konnte nicht bestätigt werden';
  if (reason === 'expired') return 'Die Lizenz dieser Schule ist abgelaufen';
  return 'Die Lizenz dieser Schule wurde gesperrt';
}

/** Darf diese Person die Lizenz eingeben (Recht `license.manage`)? */
export function canManageLicense(user: { permissions?: readonly string[] } | null | undefined): boolean {
  return !!user?.permissions?.includes('license.manage');
}

/** Zeigt der App-Rahmen einen Lizenz-Hinweis? Kulanzzeit für alle, Vorwarnung nur für Personen mit `license.manage`. */
export function licenseBanner(
  lic: LicenseBrief | null | undefined,
  manager: boolean,
): { kind: 'error' | 'warning'; text: string; link: boolean } | null {
  if (!lic || !lic.enforced) return null;
  if (lic.read_only) return { kind: 'error', text: `Nur Lesen: ${lic.message}`, link: manager };
  if (manager && (lic.message || lic.warning)) return { kind: 'warning', text: lic.message || lic.warning, link: true };
  return null;
}
