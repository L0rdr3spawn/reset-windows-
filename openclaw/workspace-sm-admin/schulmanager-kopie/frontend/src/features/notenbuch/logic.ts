/** Reine Hilfen des Notenbuchs (ohne React): Anzeige, Kürzel-Eingabe, Spaltenfolge, Tastaturbewegung. */
import type { Category, Entry, EntryStatus, Item, Scale, ScaleKind } from './types';

export type Tone = 'good' | 'ok' | 'bad' | 'none';

/** Zahl mit deutschem Komma; `–` ohne Wert. */
export function fmtNum(n: number | null | undefined, decimals = 2): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '–';
  return n.toFixed(Math.max(0, Math.min(3, decimals))).replace('.', ',');
}

/** Gewicht ohne überflüssige Nullen (`2`, `2,5`). */
export function fmtWeight(w: number): string {
  return String(Math.round(w * 100) / 100).replace('.', ',');
}

export function parseDecimal(text: string): number | null {
  const t = text.trim().replace(',', '.');
  if (!t) return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}

/** Farbton einer Note (nur für die Kennzeichnung, nie allein: der Wert steht immer als Text daneben). */
export function gradeTone(label: string, kind: ScaleKind): Tone {
  const t = (label || '').trim();
  if (!t) return 'none';
  if (kind === 'note6') {
    const base = Number(t[0]);
    if (!Number.isFinite(base)) return 'none';
    if (base <= 2) return 'good';
    return base <= 4 ? 'ok' : 'bad';
  }
  if (kind === 'punkte15') {
    const n = Number(t);
    if (!Number.isFinite(n)) return 'none';
    return n >= 10 ? 'good' : n >= 5 ? 'ok' : 'bad';
  }
  if (kind === 'prozent') {
    const n = Number(t.replace(',', '.'));
    if (!Number.isFinite(n)) return 'none';
    return n >= 75 ? 'good' : n >= 45 ? 'ok' : 'bad';
  }
  if (kind === 'bestanden') return t.startsWith('nicht') ? 'bad' : 'good';
  return 'none';
}

export const STATUS_SHORT: Record<EntryStatus, string> = {
  '': '',
  entschuldigt: 'entsch.',
  ausgelassen: 'ausgel.',
  nachschreiben: 'nachschr.',
  unentschuldigt: 'unentsch.',
};

export const STATUS_NAMES: Record<EntryStatus, string> = {
  '': 'zählt',
  entschuldigt: 'entschuldigt (zählt nicht)',
  ausgelassen: 'ausgelassen (zählt nicht)',
  nachschreiben: 'Nachschreiben (zählt noch nicht)',
  unentschuldigt: 'unentschuldigt gefehlt (ungenügend)',
};

const QUICK: Record<string, EntryStatus> = { e: 'entschuldigt', a: 'ausgelassen', n: 'nachschreiben', u: 'unentschuldigt' };

/** Kürzel-Eingabe in der Tabelle: `e`, `a`, `n`, `u` setzen den Status (nur bei Zahlenskalen, wo Buchstaben keine Note
 * sind); `-` oder leer löscht den Wert; alles andere ist der Wert selbst. */
export function parseQuick(raw: string, kind: ScaleKind | undefined): { value: string; status: EntryStatus } {
  const t = raw.trim();
  const letters = kind === 'note6' || kind === 'punkte15' || kind === 'prozent';
  if (letters && t.length === 1 && QUICK[t.toLowerCase()]) return { value: '', status: QUICK[t.toLowerCase()] };
  if (t === '-' || t === '–') return { value: '', status: '' };
  return { value: t, status: '' };
}

/** Text im Eingabefeld einer Zelle. */
export function cellText(e: Entry | undefined): string {
  if (!e) return '';
  if (e.status === 'entschuldigt') return 'e';
  if (e.status === 'ausgelassen') return 'a';
  if (e.status === 'nachschreiben') return 'n';
  if (e.status === 'unentschuldigt') return 'u';
  return e.value;
}

export interface Column {
  item: Item;
  /** Name der Leistungsart (mit Oberkategorien: „Sonstige Mitarbeit › Tests“) */
  path: string;
  category_id: number | null;
}

/** Leistungen in der Reihenfolge der Leistungsarten (Baumreihenfolge), darin nach Datum/Position. */
export function orderedColumns(categories: Category[], items: Item[]): Column[] {
  const byId = new Map(categories.map((c) => [c.id, c]));
  const order = new Map(categories.map((c, i) => [c.id, i]));
  const pathOf = (id: number | null): string => {
    const parts: string[] = [];
    let cur = id !== null ? byId.get(id) : undefined;
    let guard = 0;
    while (cur && guard++ < 8) {
      parts.unshift(cur.name);
      cur = cur.parent_id !== null ? byId.get(cur.parent_id) : undefined;
    }
    return parts.join(' › ');
  };
  const rank = (i: Item) => (i.category_id !== null && order.has(i.category_id) ? (order.get(i.category_id) as number) : -1);
  return [...items]
    .sort((a, b) => rank(a) - rank(b) || (a.date || '9999').localeCompare(b.date || '9999') || a.position - b.position || a.id - b.id)
    .map((item) => ({ item, path: pathOf(item.category_id), category_id: item.category_id }));
}

/** Auswahl der Leistungsarten mit Einrückung. */
export function categoryOptions(categories: Category[]): { id: number; label: string }[] {
  return categories.map((c) => ({ id: c.id, label: `${' '.repeat(c.depth)}${c.name}` }));
}

export function topCategories(categories: Category[]): Category[] {
  return categories.filter((c) => c.parent_id === null);
}

/** Welche Zelle erhält den Fokus? `ArrowDown`/`Enter` ↓, `ArrowUp` ↑ (am Rand bleibt die Zelle). */
export function moveTarget(row: number, col: number, key: string, rows: number, shift = false): [number, number] {
  if (key === 'ArrowDown' || (key === 'Enter' && !shift)) return [Math.min(rows - 1, row + 1), col];
  if (key === 'ArrowUp' || (key === 'Enter' && shift)) return [Math.max(0, row - 1), col];
  return [row, col];
}

/** Gewichte der Leistungsarten als Prozent unter den Geschwistern (nur zur Anzeige). */
export function weightShare(categories: Category[]): Record<number, number> {
  const sums = new Map<number | null, number>();
  for (const c of categories) sums.set(c.parent_id, (sums.get(c.parent_id) ?? 0) + c.weight);
  const out: Record<number, number> = {};
  for (const c of categories) {
    const s = sums.get(c.parent_id) ?? 0;
    out[c.id] = s > 0 ? Math.round((c.weight / s) * 100) : 0;
  }
  return out;
}

/** Schnellwahl-Noten für die Eingabe am Handy. */
export function quickLabels(scale: Scale | null | undefined): string[] {
  if (!scale) return [];
  if (scale.kind === 'note6') return ['1', '2', '3', '4', '5', '6', '1-', '2+', '2-', '3+', '3-', '4+', '4-', '5+', '5-'];
  if (scale.kind === 'punkte15') return Array.from({ length: 16 }, (_, i) => String(15 - i));
  if (scale.kind === 'bestanden') return ['bestanden', 'nicht bestanden'];
  if (scale.kind === 'custom') return scale.labels.map((l) => l.label);
  return [];
}

/** Datum `2026-10-05` → `05.10.` (kurz) für Spaltenköpfe. */
export function shortDate(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '');
  return m ? `${m[3]}.${m[2]}.` : '';
}

/** Dateiname/Anzeige des Halbjahres „2026-1“ → „2026/27, 1. Halbjahr“. */
export function termText(term: string): string {
  const m = /^(\d{4})-([12])$/.exec(term);
  return m ? `${m[1]}/${String(Number(m[1]) + 1).slice(2)}, ${m[2]}. Halbjahr` : term;
}
