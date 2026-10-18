/** Reine Logik der Benachrichtigungszentrale (testbar ohne DOM). */
import type { AppNotification, NotificationKind, NotificationMode, SchoolKind } from './api';

/** Zahl am Glockensymbol: ab 100 „99+“, 0 = nichts. */
export function bellText(n: number): string {
  if (!Number.isFinite(n) || n <= 0) return '';
  return n > 99 ? '99+' : String(n);
}

/** Beschriftung für Bildschirmleser. */
export function bellLabel(n: number): string {
  if (n <= 0) return 'Benachrichtigungen, keine neuen';
  return n === 1 ? 'Benachrichtigungen, 1 neue' : `Benachrichtigungen, ${n} neue`;
}

const MINUTE = 60_000;

/** „gerade eben“, „vor 5 Min.“, „vor 3 Std.“, sonst Datum (und Uhrzeit bis gestern). */
export function relativeTime(iso: string | null | undefined, now: Date = new Date()): string {
  if (!iso) return '';
  const t = new Date(iso);
  if (Number.isNaN(t.getTime())) return '';
  const diff = now.getTime() - t.getTime();
  if (diff < MINUTE) return 'gerade eben';
  if (diff < 60 * MINUTE) return `vor ${Math.floor(diff / MINUTE)} Min.`;
  if (diff < 24 * 60 * MINUTE && t.toDateString() === now.toDateString()) return `vor ${Math.floor(diff / (60 * MINUTE))} Std.`;
  const day = t.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: t.getFullYear() === now.getFullYear() ? undefined : 'numeric' });
  const time = t.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  return `${day}, ${time}`;
}

export type DayGroup = 'Heute' | 'Gestern' | 'Diese Woche' | 'Früher';

export function dayGroup(iso: string | null | undefined, now: Date = new Date()): DayGroup {
  if (!iso) return 'Früher';
  const t = new Date(iso);
  if (Number.isNaN(t.getTime())) return 'Früher';
  const start = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const days = Math.round((start(now) - start(t)) / 86_400_000);
  if (days <= 0) return 'Heute';
  if (days === 1) return 'Gestern';
  if (days < 7) return 'Diese Woche';
  return 'Früher';
}

/** Gruppiert (Reihenfolge der Liste bleibt) nach Heute/Gestern/…; leere Gruppen entfallen. */
export function groupByDay(items: AppNotification[], now: Date = new Date()): { label: DayGroup; items: AppNotification[] }[] {
  const order: DayGroup[] = ['Heute', 'Gestern', 'Diese Woche', 'Früher'];
  const map = new Map<DayGroup, AppNotification[]>();
  for (const n of items) {
    const g = dayGroup(n.created_at, now);
    map.set(g, [...(map.get(g) ?? []), n]);
  }
  return order.filter((g) => map.has(g)).map((g) => ({ label: g, items: map.get(g) ?? [] }));
}

/** Arten nach Gruppe (Reihenfolge des ersten Auftretens). */
export function groupKinds<T extends { group: string }>(kinds: T[]): { group: string; kinds: T[] }[] {
  const out: { group: string; kinds: T[] }[] = [];
  for (const k of kinds) {
    const g = out.find((x) => x.group === k.group);
    if (g) g.kinds.push(k);
    else out.push({ group: k.group, kinds: [k] });
  }
  return out;
}

/** Ziel einer Benachrichtigung: nur eigene, relative Pfade (keine fremden Adressen). */
export function safeLink(link: string | null | undefined): string | null {
  if (!link || !link.startsWith('/') || link.startsWith('//')) return null;
  return link;
}

/** Zeilen der Einstellung, die sich gegenüber dem gespeicherten Stand geändert haben. */
export function changedModes(kinds: NotificationKind[], edited: Record<string, NotificationMode>): Record<string, NotificationMode> {
  const out: Record<string, NotificationMode> = {};
  for (const k of kinds) {
    const m = edited[k.kind];
    if (m && !k.locked && m !== k.mode) out[k.kind] = m;
  }
  return out;
}

export function validTime(value: string): boolean {
  const m = /^(\d{2}):(\d{2})$/.exec(value);
  return !!m && Number(m[1]) <= 23 && Number(m[2]) <= 59;
}

/** Aufbewahrung in Tagen innerhalb der Grenzen? */
export function validRetention(value: string, min: number, max: number): boolean {
  if (!/^\d+$/.test(value.trim())) return false;
  const n = Number(value);
  return n >= min && n <= max;
}

/** Nur geänderte Schulvorgaben (für das Speichern). */
export function changedSchoolRules(kinds: SchoolKind[], edited: Record<string, { mode: NotificationMode; locked: boolean }>): Record<string, { mode: NotificationMode; locked: boolean }> {
  const out: Record<string, { mode: NotificationMode; locked: boolean }> = {};
  for (const k of kinds) {
    const e = edited[k.kind];
    if (e && (e.mode !== k.mode || e.locked !== k.locked)) out[k.kind] = e;
  }
  return out;
}
