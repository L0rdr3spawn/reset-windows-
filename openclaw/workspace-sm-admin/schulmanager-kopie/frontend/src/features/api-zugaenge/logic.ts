/** Reine Logik der Seite „API-Zugänge“ (ohne React). */
import type { AccessDraft, AccessStatus, AreaInfo, FilterKind, ValueOption } from './types';

export const STATUS_LABELS: Record<AccessStatus, string> = { active: 'Aktiv', expired: 'Abgelaufen', revoked: 'Widerrufen' };

export const OUTCOME_LABELS: Record<string, string> = {
  ok: 'abgerufen',
  area_denied: 'Bereich nicht freigegeben',
  write_denied: 'Schreiben nicht erlaubt',
  ip_denied: 'Adresse nicht freigegeben',
  rate_limited: 'Limit erreicht',
  not_open_api: 'Pfad nicht erlaubt',
};

export function emptyDraft(defaults: { expires: number; rate: number }): AccessDraft {
  return { name: '', purpose: '', expires_days: defaults.expires, areas: [], write: [], filters: {}, ip_allow: [], rate_limit: defaults.rate };
}

/** Filterarten, die in mindestens einem der gewählten Bereiche wirken (in fester Reihenfolge). */
export function relevantFilters(areas: AreaInfo[], selected: string[]): FilterKind[] {
  const order: FilterKind[] = ['classes', 'teachers', 'students', 'rooms', 'sites'];
  const used = new Set<FilterKind>();
  for (const a of areas) if (selected.includes(a.id)) a.filters.forEach((f) => used.add(f));
  return order.filter((f) => used.has(f));
}

/** Auswahl umschalten (stabil, ohne Doppelte). */
export function toggle(list: string[], value: string): string[] {
  return list.includes(value) ? list.filter((x) => x !== value) : [...list, value];
}

/** Filter ohne Einträge und ohne unpassende Arten entfernen (für das Senden). */
export function cleanFilters(filters: AccessDraft['filters'], allowed: FilterKind[]): AccessDraft['filters'] {
  const out: AccessDraft['filters'] = {};
  for (const k of allowed) if (filters[k]?.length) out[k] = filters[k];
  return out;
}

/** Eingabe „a, b\nc“ → Liste ohne Leerwerte und Doppelte. */
export function parseList(text: string): string[] {
  return Array.from(new Set(text.split(/[\s,;]+/).map((s) => s.trim()).filter(Boolean)));
}

/** Auswahlliste durchsuchen (Name oder Kürzel), höchstens `limit` Treffer. */
export function searchOptions(options: ValueOption[], query: string, limit = 200): ValueOption[] {
  const q = query.trim().toLowerCase();
  const hits = q ? options.filter((o) => o.id.toLowerCase().includes(q) || o.name.toLowerCase().includes(q)) : options;
  return hits.slice(0, limit);
}

/** Kann der Assistent von Schritt `step` weiter? (0 Name, 1 Bereiche) */
export function stepValid(step: number, d: AccessDraft): boolean {
  if (step === 0) return d.name.trim().length > 0 && d.expires_days >= 1;
  if (step === 1) return d.areas.length > 0;
  return true;
}
