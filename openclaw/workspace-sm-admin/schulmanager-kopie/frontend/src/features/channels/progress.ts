/**
 * Lernfortschritt im Kursraum (`schulmanager/server/routes/features_progress.py`, `features_channel_trash.py`):
 * Abschlussbedingungen, „Erledigt“-Häkchen, Fortschrittsübersicht, bedingte Freigabe, Papierkorb.
 * Reine Logik (Bedingungsbaum bearbeiten, Tabelle filtern, CSV) steht hier und ist getestet (`progress.test.ts`).
 */
import { http } from '../../api/client';

export type CompletionMode = 'manual' | 'viewed' | 'submitted' | 'graded' | 'passed';

export const MODE_LABELS: Record<CompletionMode, string> = {
  manual: 'Selbst abhaken',
  viewed: 'Angesehen',
  submitted: 'Abgegeben',
  graded: 'Bewertet',
  passed: 'Bestanden',
};

export const MODE_HINTS: Record<CompletionMode, string> = {
  manual: 'Die Schülerin/der Schüler setzt das Häkchen selbst.',
  viewed: 'Erledigt, sobald das Material geöffnet wurde.',
  submitted: 'Erledigt, sobald etwas abgegeben wurde.',
  graded: 'Erledigt, sobald die Abgabe bewertet ist (nicht bei „zur Überarbeitung zurückgegeben“).',
  passed: 'Erledigt, wenn die Bewertung die Mindestpunktzahl erreicht (Prozent, z. B. 12/15) oder Note 4 oder besser ist.',
};

export interface CompletionRule {
  mode: CompletionMode;
  mode_label: string;
  pass_percent: number | null;
}

// ---------------------------------------------------------------------------------------------- Bedingungen
export type Leaf =
  | { type: 'completed'; element_type: string; element_id: number }
  | { type: 'score'; element_type: string; element_id: number; min_percent: number }
  | { type: 'note'; element_type: string; element_id: number; max_note: number }
  | { type: 'group'; group_id: number }
  | { type: 'date'; from: string | null; until: string | null }
  | { type: 'release' };
export type LeafType = Leaf['type'];
export interface Node {
  op: 'and' | 'or';
  items: (Node | Leaf)[];
}
export const isLeaf = (n: Node | Leaf): n is Leaf => 'type' in n;

export const LEAF_LABELS: Record<LeafType, string> = {
  completed: 'Anderes Element erledigt',
  score: 'Punkte mindestens …',
  note: 'Note mindestens …',
  group: 'Mitglied einer Gruppe',
  date: 'Datum',
  release: 'Zeitfreigabe erreicht (Datum / zur Stunde)',
};

export interface Availability {
  tree: Node;
  text: string;
}

export interface ElementRow {
  element_type: string;
  element_id: number;
  title: string;
  kind_label: string;
  folder_id: number | null;
  modes: { mode: CompletionMode; label: string }[];
  completion: CompletionRule | null;
  availability: Availability | null;
}

export interface ElementsResponse {
  elements: ElementRow[];
  groups: { id: number; name: string }[];
  groups_available: boolean;
  types: Record<string, string>;
  progress_parents: boolean;
}

export const emptyTree = (): Node => ({ op: 'and', items: [] });

export function cloneTree(node: Node): Node {
  return { op: node.op, items: node.items.map((n) => (isLeaf(n) ? { ...n } : cloneTree(n))) };
}

/** Ersetzt den Knoten unter `path` (Indexliste ab Wurzel) – gibt eine neue Kopie zurück. */
export function updateAt(root: Node, path: number[], fn: (parent: Node, index: number) => void): Node {
  const copy = cloneTree(root);
  let cur = copy;
  for (const i of path.slice(0, -1)) cur = cur.items[i] as Node;
  fn(cur, path[path.length - 1] ?? 0);
  return copy;
}

export function addLeaf(root: Node, groupPath: number[], leaf: Leaf): Node {
  const copy = cloneTree(root);
  let cur = copy;
  for (const i of groupPath) cur = cur.items[i] as Node;
  cur.items.push(leaf);
  return copy;
}

export function addGroup(root: Node, groupPath: number[]): Node {
  const copy = cloneTree(root);
  let cur = copy;
  for (const i of groupPath) cur = cur.items[i] as Node;
  cur.items.push({ op: 'or', items: [] });
  return copy;
}

export function removeAt(root: Node, path: number[]): Node {
  return updateAt(root, path, (parent, i) => {
    parent.items.splice(i, 1);
  });
}

export function setOp(root: Node, groupPath: number[], op: 'and' | 'or'): Node {
  const copy = cloneTree(root);
  let cur = copy;
  for (const i of groupPath) cur = cur.items[i] as Node;
  cur.op = op;
  return copy;
}

export function replaceLeaf(root: Node, path: number[], leaf: Leaf): Node {
  return updateAt(root, path, (parent, i) => {
    parent.items[i] = leaf;
  });
}

export function leafCount(node: Node): number {
  return node.items.reduce((n, x) => n + (isLeaf(x) ? 1 : leafCount(x)), 0);
}

/** Neues Blatt eines Typs mit sinnvollen Vorgaben. */
export function newLeaf(type: LeafType, first?: { element_type: string; element_id: number }, groupId?: number): Leaf {
  switch (type) {
    case 'completed':
      return { type, element_type: first?.element_type ?? 'item', element_id: first?.element_id ?? 0 };
    case 'score':
      return { type, element_type: first?.element_type ?? 'item', element_id: first?.element_id ?? 0, min_percent: 50 };
    case 'note':
      return { type, element_type: first?.element_type ?? 'item', element_id: first?.element_id ?? 0, max_note: 3 };
    case 'group':
      return { type, group_id: groupId ?? 0 };
    case 'date':
      return { type, from: null, until: null };
    default:
      return { type: 'release' };
  }
}

/** Fehlertext für unvollständige Bedingungen (vor dem Speichern); `null` = in Ordnung. */
export function treeProblem(node: Node): string | null {
  for (const n of node.items) {
    if (!isLeaf(n)) {
      const p = treeProblem(n);
      if (p) return p;
      continue;
    }
    if ((n.type === 'completed' || n.type === 'score' || n.type === 'note') && !n.element_id) return 'Bitte bei jeder Bedingung ein Element wählen.';
    if (n.type === 'group' && !n.group_id) return 'Bitte bei jeder Gruppen-Bedingung eine Gruppe wählen.';
    if (n.type === 'date' && !n.from && !n.until) return 'Bitte bei jeder Datums-Bedingung „Ab“ oder „Bis“ ausfüllen.';
    if (n.type === 'score' && !(n.min_percent >= 0 && n.min_percent <= 100)) return 'Die Mindestpunktzahl liegt zwischen 0 und 100 Prozent.';
    if (n.type === 'note' && !(n.max_note >= 1 && n.max_note <= 6)) return 'Noten liegen zwischen 1 und 6.';
  }
  return null;
}

/** Wert eines `datetime-local`-Felds (lokale Zeit) ⇄ ISO-UTC für den Server. */
export function localToIso(value: string): string | null {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}
export function isoToLocal(value: string | null): string {
  if (!value) return '';
  const d = new Date(value.endsWith('Z') ? value : `${value}Z`);
  if (Number.isNaN(d.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ---------------------------------------------------------------------------------------------- Fortschritt
export interface MyElement {
  element_type: string;
  element_id: number;
  title: string;
  kind_label: string;
  folder_id: number | null;
  mode: CompletionMode;
  mode_label: string;
  done: boolean;
  locked: boolean;
  locked_text: string;
  can_toggle: boolean;
}

export interface MyProgress {
  enabled: boolean;
  elements: MyElement[];
  done: number;
  total: number;
  percent: number;
}

export interface TableElement {
  element_type: string;
  element_id: number;
  key: string;
  title: string;
  kind_label: string;
  folder_id: number | null;
  mode: CompletionMode;
  mode_label: string;
  done: number;
  of: number;
  /** Abgaben/Bewertungen einer anderen Lehrkraft: nicht einsehbar */
  restricted: boolean;
}

export interface TableStudent {
  student_id: string | null;
  user_id: number | null;
  name: string;
  class_id: string | null;
  has_account: boolean;
  /** `key` → erledigt / offen / `null` (nicht einsehbar oder kein Konto) */
  cells: Record<string, boolean | null>;
  done: number;
  total: number;
  percent: number;
}

export interface ProgressTable {
  elements: TableElement[];
  students: TableStudent[];
  classes: string[];
  progress_parents: boolean;
  generated_at: string;
}

export interface TableFilter {
  /** Namensteil */
  q: string;
  /** Klasse ('' = alle) */
  classId: string;
  /** nur Schüler/innen mit offenen Elementen */
  onlyOpen: boolean;
  /** nur Schüler/innen, bei denen dieses Element (`key`) offen ist ('' = egal) */
  openKey: string;
}

export const noFilter: TableFilter = { q: '', classId: '', onlyOpen: false, openKey: '' };

export function filterStudents(students: TableStudent[], f: TableFilter): TableStudent[] {
  const q = f.q.trim().toLocaleLowerCase('de');
  return students.filter((s) => {
    if (q && !s.name.toLocaleLowerCase('de').includes(q)) return false;
    if (f.classId && s.class_id !== f.classId) return false;
    if (f.onlyOpen && !(s.total > s.done)) return false;
    if (f.openKey && s.cells[f.openKey] !== false) return false;
    return true;
  });
}

/** Zelle für CSV/Anzeige: ✓ erledigt, – offen, leer = nicht einsehbar. */
export function cellText(v: boolean | null | undefined): string {
  return v === true ? 'erledigt' : v === false ? 'offen' : '';
}

/** Schützt vor Formeln in Tabellenprogrammen (Zelle beginnt mit = + - @ Tab Zeilenumbruch). */
export function csvField(value: string | number): string {
  let s = String(value);
  if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`;
  return /[";\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/** CSV (Semikolon, für deutsches Excel) der gefilterten Tabelle. */
export function toCsv(table: ProgressTable, students: TableStudent[]): string {
  const head = ['Name', 'Klasse', ...table.elements.map((e) => e.title), 'Erledigt', 'Gesamt', 'Fortschritt %'];
  const lines = [head.map(csvField).join(';')];
  for (const s of students) {
    const row: (string | number)[] = [s.name, s.class_id ?? '', ...table.elements.map((e) => cellText(s.cells[e.key])), s.done, s.total, s.percent];
    lines.push(row.map(csvField).join(';'));
  }
  return `﻿${lines.join('\r\n')}\r\n`;
}

export function csvFileName(channelTitle: string, date = new Date()): string {
  const slug = channelTitle
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^A-Za-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40);
  return `fortschritt-${slug || 'kursraum'}-${date.toISOString().slice(0, 10)}.csv`;
}

// ---------------------------------------------------------------------------------------------- Papierkorb
export interface TrashEntry {
  group: string;
  kind: 'item' | 'folder';
  name: string;
  type: string | null;
  type_label: string;
  folders: number;
  items: number;
  submissions: number;
  deleted_at: string | null;
  deleted_by_name: string;
  purge_at: string | null;
  can_restore: boolean;
}

export interface TrashResponse {
  entries: TrashEntry[];
  retention_days: number;
  can_use: boolean;
  can_set_retention: boolean;
}

/** „3 Einträge“, „Ordner mit 2 Unterordnern und 5 Materialien“ … */
export function trashContent(e: TrashEntry): string {
  const parts: string[] = [];
  if (e.kind === 'folder') {
    const sub = e.folders - 1;
    if (sub > 0) parts.push(sub === 1 ? '1 Unterordner' : `${sub} Unterordner`);
    if (e.items > 0) parts.push(e.items === 1 ? '1 Material' : `${e.items} Materialien`);
  }
  if (e.submissions > 0) parts.push(e.submissions === 1 ? '1 Abgabe' : `${e.submissions} Abgaben`);
  return parts.join(' · ');
}

/** Verbleibende Tage bis zum endgültigen Löschen (aufgerundet, mindestens 0). */
export function daysLeft(purgeAt: string | null, now = Date.now()): number | null {
  if (!purgeAt) return null;
  const t = new Date(purgeAt).getTime();
  return Number.isNaN(t) ? null : Math.max(0, Math.ceil((t - now) / 86_400_000));
}

// ---------------------------------------------------------------------------------------------- API
const base = (id: number) => `/channels/${id}`;

export const progressApi = {
  elements: (id: number, signal?: AbortSignal) => http.get<ElementsResponse>(`${base(id)}/elements`, undefined, { signal }),
  setCompletion: (id: number, type: string, elementId: number, body: { mode: CompletionMode; pass_percent?: number | null }) =>
    http.put<{ completion: CompletionRule | null }>(`${base(id)}/elements/${type}/${elementId}/completion`, body),
  removeCompletion: (id: number, type: string, elementId: number) =>
    http.del<{ completion: null }>(`${base(id)}/elements/${type}/${elementId}/completion`),
  bulkCompletion: (id: number, elements: { element_type: string; element_id: number }[], mode: CompletionMode | null, passPercent?: number | null) =>
    http.post<{ changed: number; skipped: number }>(`${base(id)}/completion/bulk`, { elements, mode, pass_percent: passPercent ?? null }),
  setAvailability: (id: number, type: string, elementId: number, tree: Node | null) =>
    http.put<{ availability: Availability | null }>(`${base(id)}/elements/${type}/${elementId}/availability`, { tree }),
  markDone: (id: number, type: string, elementId: number, done: boolean) =>
    http.post<{ done: boolean }>(`${base(id)}/elements/${type}/${elementId}/done`, { done }),
  mine: (id: number, signal?: AbortSignal, studentId?: string | null) =>
    http.get<MyProgress>(`${base(id)}/progress/me`, { student_id: studentId || undefined }, { signal }),
  table: (id: number, signal?: AbortSignal) => http.get<ProgressTable>(`${base(id)}/progress`, undefined, { signal }),
};

export const trashApi = {
  list: (id: number, signal?: AbortSignal) => http.get<TrashResponse>(`${base(id)}/trash`, undefined, { signal }),
  restore: (id: number, group: string) => http.post<{ restored: string; items: number; folders: number }>(`${base(id)}/trash/${group}/restore`, {}),
  purge: (id: number, group: string) => http.del<{ purged: string; items: number }>(`${base(id)}/trash/${group}`),
  empty: (id: number) => http.del<{ items: number; folders: number; skipped: number }>(`${base(id)}/trash`),
  setRetention: (days: number) => http.put<unknown>('/settings', { trash_retention_days: days }),
};
