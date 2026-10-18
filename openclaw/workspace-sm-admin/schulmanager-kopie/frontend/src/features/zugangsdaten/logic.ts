/**
 * Reine Logik der Zugangsdaten-Seite (§11.3): Ablauf-Countdown, Versand-Vorschau, Texte.
 */
import type { BatchEntry, SendResult, SendTarget } from './types';

/** Sekunden bis `expiresAt` (ISO) – nie negativ. */
export function secondsLeft(expiresAt: string, now: Date = new Date()): number {
  const t = Date.parse(expiresAt);
  if (Number.isNaN(t)) return 0;
  return Math.max(0, Math.floor((t - now.getTime()) / 1000));
}

/** „54:07“ bzw. „1:02:03“ */
export function formatClock(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const mm = String(m).padStart(h ? 2 : 1, '0');
  return `${h ? `${h}:` : ''}${mm}:${String(sec).padStart(2, '0')}`;
}

/** Text für Bildschirmleser/Hinweise: „noch 54 Minuten“, „noch 40 Sekunden“, „abgelaufen“. */
export function remainingLabel(seconds: number): string {
  if (seconds <= 0) return 'abgelaufen';
  if (seconds < 60) return `noch ${seconds} ${seconds === 1 ? 'Sekunde' : 'Sekunden'}`;
  const m = Math.ceil(seconds / 60);
  return `noch ${m} ${m === 1 ? 'Minute' : 'Minuten'}`;
}

export const ROLE_TEXT: Record<string, string> = {
  schueler: 'Schüler/in',
  eltern: 'Eltern',
  lehrer: 'Lehrkraft',
  sekretariat: 'Sekretariat',
  schulleitung: 'Schulleitung',
  planer: 'Stundenplanung',
  admin: 'Administration',
  monitor: 'Monitor',
};

export const TARGET_TEXT: Record<SendTarget, string> = {
  student: 'an die Person selbst',
  parents: 'an die Eltern',
  both: 'an beide',
};

/** Bekommt ein Eintrag beim Versand mit `to` mindestens eine E-Mail (Stand der Stapel-Übersicht)? */
export function reachable(e: BatchEntry, to: SendTarget): boolean {
  // Elternbriefe und Volljährige: immer an die eigene Adresse (Volljährige nie über die Eltern)
  const own = e.has_email && (to !== 'parents' || e.role === 'eltern' || e.adult === true);
  const parents = to !== 'student' && e.role === 'schueler' && e.parents_with_email > 0;
  return own || parents;
}

export function sendPreview(entries: readonly BatchEntry[], to: SendTarget): { reachable: number; missing: number } {
  const n = entries.filter((e) => reachable(e, to)).length;
  return { reachable: n, missing: entries.length - n };
}

/** „3 Briefe verschickt · 2 ohne E-Mail-Adresse · 1 nicht zustellbar“ */
export function sendSummary(r: SendResult): string {
  const parts = [`${r.sent.length} ${r.sent.length === 1 ? 'Brief' : 'Briefe'} verschickt`];
  if (r.no_address.length) parts.push(`${r.no_address.length} ohne E-Mail-Adresse`);
  if (r.unavailable.length) parts.push(`${r.unavailable.length} nicht zustellbar`);
  return parts.join(' · ');
}

/** Anmeldehinweis eines Eintrags (für die Tabelle) */
export function loginHint(e: BatchEntry): string {
  const parts: string[] = [];
  if (!e.password_printed && e.login_methods.length) parts.push(`nur ${e.login_methods.join(' / ')}`);
  else parts.push('Startpasswort');
  if (e.required_links.length) parts.push(`muss ${e.required_links.join(', ')} verbinden`);
  return parts.join(' · ');
}
