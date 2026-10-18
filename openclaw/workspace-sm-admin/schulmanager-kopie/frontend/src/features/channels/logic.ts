/**
 * Reine Hilfsfunktionen der Kursräume (ohne React, mit vitest getestet): Ordnerbaum, Sortierung, Texte zu
 * Sichtbarkeit/Fristen/Status, Zeitumrechnung für Formularfelder, Suche, Badge-Zahl.
 */
import type { Channel, Folder, Item, ItemState, LessonBinding, LessonStatus, SubmissionStatus, UpcomingLesson, VisibilityChoice, VisibilityInput } from './types';

const pad = (n: number) => String(n).padStart(2, '0');
const WD = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];

// ------------------------------------------------------------------ Ordner
export interface FolderNode extends Folder {
  children: FolderNode[];
  depth: number;
}

export function byPosition<T extends { position: number; id: number }>(a: T, b: T): number {
  return a.position - b.position || a.id - b.id;
}

/** Ordnerbaum (sortiert nach Position); Ordner mit unbekanntem Elternordner landen oben. */
export function buildFolderTree(folders: readonly Folder[]): FolderNode[] {
  const ids = new Set(folders.map((f) => f.id));
  const kids = new Map<number | null, Folder[]>();
  for (const f of folders) {
    const parent = f.parent_id !== null && ids.has(f.parent_id) ? f.parent_id : null;
    const list = kids.get(parent) ?? [];
    list.push(f);
    kids.set(parent, list);
  }
  const seen = new Set<number>();
  const build = (parent: number | null, depth: number): FolderNode[] =>
    [...(kids.get(parent) ?? [])].sort(byPosition).flatMap((f) => {
      if (seen.has(f.id) || depth > 32) return [];
      seen.add(f.id);
      return [{ ...f, depth, children: build(f.id, depth + 1) }];
    });
  return build(null, 0);
}

/** Baum in Anzeige-Reihenfolge abflachen (für Auswahllisten mit Einrückung). */
export function flattenTree(nodes: readonly FolderNode[]): FolderNode[] {
  return nodes.flatMap((n) => [n, ...flattenTree(n.children)]);
}

/** Pfad Wurzel → Ordner (leer für die oberste Ebene/unbekannte Ordner). */
export function folderPath(folders: readonly Folder[], folderId: number | null): Folder[] {
  const byId = new Map(folders.map((f) => [f.id, f]));
  const out: Folder[] = [];
  let cur = folderId;
  while (cur !== null && byId.has(cur) && out.length < 64) {
    const f = byId.get(cur)!;
    if (out.includes(f)) break;
    out.unshift(f);
    cur = f.parent_id;
  }
  return out;
}

/** IDs aller Unterordner (ohne den Ordner selbst). */
export function descendantIds(folders: readonly Folder[], folderId: number): Set<number> {
  const out = new Set<number>();
  const stack = [folderId];
  while (stack.length) {
    const cur = stack.pop()!;
    for (const f of folders) {
      if (f.parent_id === cur && !out.has(f.id) && f.id !== folderId) {
        out.add(f.id);
        stack.push(f.id);
      }
    }
  }
  return out;
}

export function childFolders(folders: readonly Folder[], parentId: number | null): Folder[] {
  return folders.filter((f) => f.parent_id === parentId).sort(byPosition);
}

export function itemsIn(items: readonly Item[], folderId: number | null): Item[] {
  return items.filter((i) => i.folder_id === folderId).sort(byPosition);
}

/** Anzahl Materialien in einem Ordner inkl. Unterordnern. */
export function countInFolder(folders: readonly Folder[], items: readonly Item[], folderId: number): number {
  const ids = descendantIds(folders, folderId);
  ids.add(folderId);
  return items.filter((i) => i.folder_id !== null && ids.has(i.folder_id)).length;
}

// ------------------------------------------------------------------ Zeiten
/** ISO (UTC) → „Di, 13.10.2026, 08:00“ in Ortszeit des Browsers. */
export function formatWhen(iso: string | null | undefined, withYear = true): string {
  if (!iso) return '–';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const date = `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${withYear ? d.getFullYear() : ''}`;
  return `${WD[d.getDay()]}, ${date}, ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** ISO-Zeitpunkt → Wert für `<input type="datetime-local">` (Ortszeit). */
export function toLocalInput(iso: string | null | undefined): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Wert eines `datetime-local`-Felds (Ortszeit) → ISO in UTC mit `Z` (`null` = leer/ungültig). */
export function fromLocalInput(value: string): string | null {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}

/** Vorschlag für eine Frist: in `days` Tagen um `hour` Uhr (Ortszeit). */
export function defaultDue(now: Date = new Date(), days = 7, hour = 18): string {
  const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + days, hour, 0, 0);
  return toLocalInput(d.toISOString());
}

/** Frist-Text: „bis Mo, 12.10., 18:00“ bzw. „Frist abgelaufen (…)“. */
export function dueText(dueAt: string | null | undefined, now: Date = new Date()): string {
  if (!dueAt) return 'ohne Frist';
  const d = new Date(dueAt);
  if (Number.isNaN(d.getTime())) return dueAt;
  const when = formatWhen(dueAt, d.getFullYear() !== now.getFullYear());
  return d.getTime() < now.getTime() ? `Frist abgelaufen (${when})` : `bis ${when}`;
}

/** Restzeit bis zur Frist, z. B. „noch 2 Tage“, „noch 5 Std.“ (leer ohne/abgelaufene Frist). */
export function remainingText(dueAt: string | null | undefined, now: Date = new Date()): string {
  if (!dueAt) return '';
  const ms = new Date(dueAt).getTime() - now.getTime();
  if (!Number.isFinite(ms) || ms <= 0) return '';
  const hours = Math.floor(ms / 3_600_000);
  if (hours >= 48) return `noch ${Math.floor(hours / 24)} Tage`;
  if (hours >= 1) return `noch ${hours} Std.`;
  return `noch ${Math.max(1, Math.round(ms / 60_000))} Min.`;
}

// ------------------------------------------------------------------ Status-Texte
export type Tone = 'success' | 'warning' | 'danger' | 'info' | 'primary' | 'muted';

export const STATE_TEXT: Record<ItemState, string> = {
  visible: 'sichtbar',
  hidden: 'verborgen',
  scheduled: 'geplant',
  lesson: 'zur Stunde',
  folder_hidden: 'Ordner nicht freigegeben',
};

export function stateTone(state: ItemState | undefined): Tone {
  switch (state) {
    case 'visible':
      return 'success';
    case 'scheduled':
    case 'lesson':
      return 'info';
    case 'hidden':
    case 'folder_hidden':
      return 'warning';
    default:
      return 'muted';
  }
}

/** Hinweis bei Entfall/Verlegung einer gebundenen Stunde, z. B. „Entfall → Di, 13.10. · 3. Std.“. */
export function shiftText(lesson: Pick<LessonBinding, 'shift'> | null | undefined): string {
  const sh = lesson?.shift;
  if (!sh) return '';
  if (sh.status === 'verlegt') return `verlegt (${formatWhen(sh.release_at)})`;
  return sh.to_label ? `${sh.reason} → ${sh.to_label}` : `${sh.reason} – keine weitere Stunde in 8 Wochen`;
}

/** Freigabe-Beschreibung für Lehrende, z. B. „zur Stunde Di, 13.10. · 1. Std. · 07:55“. */
export function visibilityText(item: Pick<Item, 'visibility' | 'state' | 'lesson' | 'visible_from' | 'release_at'>): string {
  if (item.state === 'folder_hidden') {
    return item.release_at ? `Ordner wird freigegeben ${formatWhen(item.release_at)}` : 'Ordner nicht freigegeben';
  }
  switch (item.visibility) {
    case 'hidden':
      return 'verborgen';
    case 'scheduled':
      return item.state === 'visible' ? `sichtbar seit ${formatWhen(item.release_at ?? item.visible_from)}` : `geplant ab ${formatWhen(item.release_at ?? item.visible_from)}`;
    case 'lesson': {
      const label = item.lesson?.label ?? formatWhen(item.release_at);
      const shift = shiftText(item.lesson);
      if (item.state === 'visible') return `sichtbar seit Stundenbeginn (${shift || label})`;
      return shift ? `zur Stunde ${label} · ${shift}` : `zur Stunde ${label}`;
    }
    default:
      return 'sichtbar';
  }
}

/** Freigabe-Beschreibung eines Ordners (wie {@link visibilityText}). */
export function folderVisibilityText(f: Pick<Folder, 'visibility' | 'state' | 'lesson' | 'visible_from' | 'release_at'>): string {
  return visibilityText({ visibility: f.visibility ?? 'visible', state: f.state, lesson: f.lesson ?? null, visible_from: f.visible_from, release_at: f.release_at });
}

/** Darf die Lehrkraft das Material/den Ordner ändern? (ältere Antworten ohne `can_edit`: wie `manage`) */
export function canEdit(entry: { can_edit?: boolean }, manage: boolean): boolean {
  return manage && entry.can_edit !== false;
}

export const SUBMISSION_TEXT: Record<SubmissionStatus, string> = {
  offen: 'offen',
  ueberfaellig: 'Frist verpasst',
  abgegeben: 'abgegeben',
  verspaetet: 'verspätet abgegeben',
  bewertet: 'bewertet',
  zurueckgegeben: 'zur Überarbeitung',
};

export function submissionTone(status: SubmissionStatus | undefined): Tone {
  switch (status) {
    case 'abgegeben':
      return 'success';
    case 'verspaetet':
      return 'warning';
    case 'bewertet':
      return 'primary';
    case 'zurueckgegeben':
      return 'info';
    case 'ueberfaellig':
      return 'danger';
    default:
      return 'muted';
  }
}

/** Offen für Schüler/innen (Hinweis „zu erledigen“)? */
export function isOpenForStudent(status: SubmissionStatus | undefined): boolean {
  return status === 'offen' || status === 'ueberfaellig' || status === 'zurueckgegeben';
}

export function lessonTone(status: LessonStatus): Tone {
  switch (status) {
    case 'entfall':
      return 'danger';
    case 'verlegt':
    case 'geaendert':
      return 'warning';
    default:
      return 'muted';
  }
}

export function toneClass(tone: Tone): string {
  return tone === 'muted' ? 'badge' : `badge badge-${tone}`;
}

// ------------------------------------------------------------------ Stunden
/** Kommende Stunden nach Datum gruppiert (Reihenfolge bleibt erhalten). */
export function groupByDate<T extends Pick<UpcomingLesson, 'date'>>(lessons: readonly T[]): { date: string; lessons: T[] }[] {
  const out: { date: string; lessons: T[] }[] = [];
  for (const l of lessons) {
    const last = out[out.length - 1];
    if (last && last.date === l.date) last.lessons.push(l);
    else out.push({ date: l.date, lessons: [l] });
  }
  return out;
}

/** Kurzbeschreibung einer Stunde für Listen: „1. Std. · 07:55–08:40“ (+ Hinweise). */
export function lessonLine(l: Pick<UpcomingLesson, 'period_label' | 'time' | 'end_time' | 'rooms'>): string {
  const time = l.time ? ` · ${l.time}${l.end_time ? `–${l.end_time}` : ''}` : '';
  const rooms = l.rooms.length ? ` · Raum ${l.rooms.join(', ')}` : '';
  return `${l.period_label} Std.${time}${rooms}`;
}

// ------------------------------------------------------------------ Kanäle
/** Suche in Titel, Untertitel, Klassen, Fach, Lehrkräften (alle Wörter müssen vorkommen). */
export function matchChannel(ch: Pick<Channel, 'title' | 'subtitle' | 'classes' | 'subject_name' | 'teachers' | 'ref'>, query: string): boolean {
  const words = query.trim().toLocaleLowerCase('de').split(/\s+/).filter(Boolean);
  if (!words.length) return true;
  const hay = [ch.title, ch.subtitle, ch.ref ?? '', ch.classes.join(' '), ch.subject_name ?? '', ch.teachers.join(' ')]
    .join(' ')
    .toLocaleLowerCase('de');
  return words.every((w) => hay.includes(w));
}

/** Zahl am Menüeintrag: neues Material + neue Beiträge (archivierte Kursräume zählen nicht). */
export function badgeCount(channels: readonly Pick<Channel, 'new_items' | 'new_posts' | 'archived'>[]): number {
  return channels.reduce((n, c) => n + (c.archived ? 0 : (c.new_items ?? 0) + (c.new_posts ?? 0)), 0);
}

export const KIND_ORDER: Record<string, number> = { course: 0, class: 1, custom: 2 };

/** Sicherer Link (nur http/https/mailto) – sonst `null`. */
export function safeHref(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const u = new URL(url);
    return ['http:', 'https:', 'mailto:'].includes(u.protocol) ? u.href : null;
  } catch {
    return null;
  }
}

/** Dateiendung für die Anzeige („PDF“) oder Typbezeichnung. */
export function itemKindLabel(item: Pick<Item, 'type' | 'type_label' | 'file'>): string {
  if (item.type === 'file' && item.file) return item.file.kind_label || item.file.kind.toUpperCase();
  return item.type_label;
}

// ------------------------------------------------------------------ Sichtbarkeit (Formular)
export interface VisibilityDraft {
  mode: VisibilityChoice;
  /** `datetime-local` (Ortszeit) für „ab Zeitpunkt“ */
  from: string;
  lesson: Pick<UpcomingLesson, 'key' | 'date' | 'lesson_id' | 'period' | 'label'> | null;
}

export const DEFAULT_DRAFT: VisibilityDraft = { mode: 'visible', from: '', lesson: null };

/** Entwurf → Eingabe für das Backend oder Fehlermeldung (Text). */
export function draftToInput(d: VisibilityDraft): VisibilityInput | string {
  if (d.mode === 'scheduled') {
    const iso = fromLocalInput(d.from);
    return iso ? { visibility: 'scheduled', visible_from: iso } : 'Bitte Datum und Uhrzeit der Freigabe angeben.';
  }
  if (d.mode === 'lesson') {
    return d.lesson
      ? { visibility: 'lesson', lesson: { date: d.lesson.date, lesson_id: d.lesson.lesson_id, period: d.lesson.period } }
      : 'Bitte die Unterrichtsstunde wählen.';
  }
  return { visibility: d.mode };
}

/** Erste noch nicht begonnene, stattfindende Stunde (für „Zur nächsten Stunde“). */
export function nextHeldLesson<T extends Pick<UpcomingLesson, 'status' | 'started'>>(lessons: readonly T[]): T | null {
  return lessons.find((l) => l.status !== 'entfall' && !l.started) ?? null;
}

// ------------------------------------------------------------------ Ordner-Upload
export interface PathFile {
  file: File;
  /** relativer Ordnerpfad ohne Dateiname, z. B. „Projekt/Bilder“ (leer = lose Datei) */
  dir: string;
}

/** Ordnerpfad einer Datei aus `webkitRelativePath` bzw. dem Pfad beim Ablegen („Projekt/Bilder/a.png“ → „Projekt/Bilder“). */
export function dirOf(relativePath: string): string {
  const parts = relativePath.replace(/\\/g, '/').split('/').filter((p) => p && p !== '.' && p !== '..');
  return parts.slice(0, -1).join('/');
}

/** Alle Ordnerpfade (inkl. übergeordneter) einer Dateiliste, sortiert. */
export function folderPaths(files: readonly Pick<PathFile, 'dir'>[]): string[] {
  const out = new Set<string>();
  for (const f of files) {
    const parts = f.dir.split('/').filter(Boolean);
    for (let i = 1; i <= parts.length; i += 1) out.add(parts.slice(0, i).join('/'));
  }
  return [...out].sort((a, b) => a.split('/').length - b.split('/').length || a.localeCompare(b, 'de'));
}
