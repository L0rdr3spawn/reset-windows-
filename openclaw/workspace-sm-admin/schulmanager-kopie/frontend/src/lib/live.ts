/**
 * Reine Hilfsfunktionen für Live-Ereignisse (testbar ohne Browser).
 */
import type { LiveChangeEvent } from '../api/types';

function norm(s: string): string {
  return s.trim().toLowerCase();
}

/**
 * Prüft, ob ein Änderungs-Ereignis für die gewünschten Bereiche relevant ist.
 * - Ereignis ohne Scope / mit "*" oder "all" → betrifft alles
 * - gewünschter Scope "*" → interessiert sich für alles
 * - sonst Präfix-Vergleich in beide Richtungen ("substitution" ~ "substitutions", "data" ~ "data.teachers")
 */
export function scopeMatches(eventScope: readonly string[] | string | null | undefined, wanted: readonly string[]): boolean {
  if (wanted.length === 0) return true;
  const ev = (Array.isArray(eventScope) ? eventScope : eventScope ? [eventScope] : []).map((x) => norm(String(x)));
  if (ev.length === 0) return true;
  if (ev.includes('*') || ev.includes('all')) return true;
  const w = wanted.map(norm);
  if (w.includes('*')) return true;
  return ev.some((e) => w.some((x) => e === x || e.startsWith(x) || x.startsWith(e)));
}

/** Prüft, ob ein Ereignis eines der gewünschten Daten betrifft (leere Liste = alle Daten). */
export function datesMatch(eventDates: readonly string[] | null | undefined, wanted: readonly string[] | undefined): boolean {
  if (!wanted || wanted.length === 0) return true;
  if (!eventDates || eventDates.length === 0) return true;
  return eventDates.some((d) => wanted.includes(d.slice(0, 10)));
}

export function eventRelevant(ev: LiveChangeEvent, scopes: readonly string[], dates?: readonly string[]): boolean {
  return scopeMatches(ev.scope, scopes) && datesMatch(ev.dates, dates);
}

/** Exponentielles Backoff mit Obergrenze (ms). */
export function backoffDelay(attempt: number, base = 1000, max = 30000): number {
  return Math.min(max, base * 2 ** Math.max(0, attempt));
}
