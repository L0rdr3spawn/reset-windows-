/** Reine Hilfen der Datenschutz-Seite (Löschkonzept) – ohne React, damit sie testbar bleiben. */

export interface KindSetting {
  key: string;
  label: string;
  category: string;
  category_label: string;
  legal: string;
  how: string;
  description: string;
  last: boolean;
  days: number;
  default_days: number;
  effective_days: number;
  age_days: number | null;
  age_default: number | null;
  has_age: boolean;
}

export interface PrivacySettings {
  grace_days: number;
  auto_purge: boolean;
  audit_days: number;
  log_days: number;
  defaults: { grace_days: number; audit_days: number; log_days: number };
  kinds: KindSetting[];
}

export interface Overview {
  settings: PrivacySettings;
  categories: Record<string, string>;
  waiting: number;
  last_log_at: string | null;
  can_subject: boolean;
}

export interface Leaver {
  student_id: string;
  name: string;
  class_id: string;
  status: 'wartend' | 'erledigt';
  left_at: string;
  done_at: string | null;
  purged: string[];
  open: number;
  last_due_at: string | null;
  days_left: number | null;
}

export interface PreviewItem {
  kind: string;
  label: string;
  count: number;
  due_at: string;
  due: boolean;
  done: boolean;
}

export interface PreviewPerson {
  student_id: string;
  name: string;
  class_id: string;
  left_at: string;
  items: PreviewItem[];
  total: number;
  due_total: number;
}

export interface Preview {
  people: PreviewPerson[];
  expiry: { kind: string; label: string; count: number }[];
}

export interface LogEntry {
  id: number;
  at: string;
  kind: string;
  label: string;
  action: string;
  mode: string;
  subject: string;
  count: number;
  actor: string;
  note: string;
}

export interface ErasePreview {
  student_id: string | null;
  user_id: number | null;
  name: string;
  confirm_with: string;
  items: { kind: string; label: string; count: number; how: string }[];
  total: number;
}

export const MODE_LABELS: Record<string, string> = { automatik: 'Automatik', frist: 'Frist abgelaufen', sofort: 'Sofort (Art. 17)' };
export const ACTION_LABELS: Record<string, string> = { geloescht: 'gelöscht', anonymisiert: 'anonymisiert', abgeschlossen: 'abgeschlossen' };

/** Datenarten nach Kategorie gruppiert (Reihenfolge der Kategorien bleibt wie geliefert). */
export function groupByCategory(kinds: KindSetting[]): { category: string; label: string; kinds: KindSetting[] }[] {
  const out: { category: string; label: string; kinds: KindSetting[] }[] = [];
  for (const k of kinds) {
    let g = out.find((x) => x.category === k.category);
    if (!g) {
      g = { category: k.category, label: k.category_label, kinds: [] };
      out.push(g);
    }
    g.kinds.push(k);
  }
  return out;
}

/** „in 12 Tagen“, „fällig“ für die Warteliste. */
export function dueText(daysLeft: number | null, status: string): string {
  if (status === 'erledigt') return 'erledigt';
  if (daysLeft === null) return '–';
  if (daysLeft <= 0) return 'fällig';
  return daysLeft === 1 ? 'in 1 Tag' : `in ${daysLeft} Tagen`;
}

/** Fristangabe in Tagen lesbar: 0 = „aus“/„sofort“, volle Jahre in Jahren. */
export function daysText(days: number | null, zero = 'aus'): string {
  if (days === null || days === undefined) return '–';
  if (days === 0) return zero;
  if (days % 365 === 0) return days === 365 ? '1 Jahr' : `${days / 365} Jahre`;
  return days === 1 ? '1 Tag' : `${days} Tage`;
}

/** Bestätigung beim Sofort-Löschen: ID bzw. Benutzername muss exakt (ohne Rand-Leerzeichen) stimmen. */
export function confirmMatches(input: string, expected: string): boolean {
  return expected !== '' && input.trim() === expected;
}

/** Zahlenfeld: leer/ungültig → Rückfall, sonst auf 0…3650 begrenzt. */
export function clampDays(raw: string, fallback: number): number {
  const n = parseInt(raw, 10);
  if (Number.isNaN(n)) return fallback;
  return Math.min(3650, Math.max(0, n));
}

/** Nur die geänderten Fristen an den Server schicken. */
export function diffSettings(base: PrivacySettings, draft: PrivacySettings): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const key of ['grace_days', 'audit_days', 'log_days', 'auto_purge'] as const) {
    if (base[key] !== draft[key]) out[key] = draft[key];
  }
  const kinds: Record<string, { days?: number; age_days?: number }> = {};
  for (const k of draft.kinds) {
    const old = base.kinds.find((x) => x.key === k.key);
    if (!old) continue;
    const change: { days?: number; age_days?: number } = {};
    if (old.days !== k.days) change.days = k.days;
    if (k.has_age && old.age_days !== k.age_days && k.age_days !== null) change.age_days = k.age_days;
    if (Object.keys(change).length) kinds[k.key] = change;
  }
  if (Object.keys(kinds).length) out.kinds = kinds;
  return out;
}

/** Einzeiler zur Vorschau: „1 Person, 5 Einträge, davon 2 jetzt fällig“. */
export function previewSummary(p: Preview): string {
  const people = p.people.length;
  const total = p.people.reduce((n, x) => n + x.total, 0);
  const due = p.people.reduce((n, x) => n + x.due_total, 0);
  const exp = p.expiry.reduce((n, x) => n + x.count, 0);
  const parts = [`${people} ${people === 1 ? 'Person' : 'Personen'}, ${total} ${total === 1 ? 'Eintrag' : 'Einträge'}`];
  if (people) parts.push(`davon ${due} jetzt fällig`);
  if (exp) parts.push(`${exp} ${exp === 1 ? 'Eintrag' : 'Einträge'} nach Alter`);
  return parts.join(', ');
}
