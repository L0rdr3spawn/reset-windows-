import type { LoginLock, TwofaMode } from './types';

export const MODE_LABELS: Record<TwofaMode, string> = {
  off: 'Aus',
  recommended: 'Empfohlen',
  required: 'Pflicht',
};

/** Minuten als lesbare Dauer: „12 Stunden“, „30 Minuten“, „2 Tage“. */
export function formatMinutes(min: number): string {
  if (min % 1440 === 0) {
    const d = min / 1440;
    return `${d} ${d === 1 ? 'Tag' : 'Tage'}`;
  }
  if (min % 60 === 0) {
    const h = min / 60;
    return `${h} ${h === 1 ? 'Stunde' : 'Stunden'}`;
  }
  return `${min} Minuten`;
}

/** Wartezeit einer Drosselung: „45 Sekunden“, „3 Minuten“. */
export function formatWait(seconds: number): string {
  if (seconds < 90) return `${Math.max(1, Math.round(seconds))} Sekunden`;
  return `${Math.round(seconds / 60)} Minuten`;
}

/** Beschreibung einer Drosselung für die Verwaltung. */
export function lockTitle(l: LoginLock): string {
  if (l.kind === 'ip') return `Anschluss ${l.ip}`;
  if (l.kind === 'account') return `${l.username} (viele Anschlüsse)`;
  return `${l.username}${l.ip ? ` von ${l.ip}` : ''}`;
}

/** Auswahl der Rollen ein-/ausschalten, Reihenfolge der Auswahlliste bleibt erhalten. */
export function toggleRole(current: string[], role: string, order: string[]): string[] {
  const set = new Set(current);
  if (set.has(role)) set.delete(role);
  else set.add(role);
  return order.filter((r) => set.has(r));
}
