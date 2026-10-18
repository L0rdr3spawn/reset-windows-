/**
 * Kürzel mit Sprechblase (components/Abbr.tsx) – reine Logik ohne DOM, damit sie mit vitest prüfbar ist.
 *
 * - Zustand: Hover, Fokus (Tastatur) und „angeheftet“ (Antippen, Enter, Langdruck) – offen, sobald eines davon gilt.
 * - Texte: aus den Stammdaten wird zum Kürzel die volle Bezeichnung gebaut
 *   („MÜL“ → „Frau Müller · Deutsch, Englisch“, „D“ → „Deutsch“, „R112“ → „Raum 112 (Hauptgebäude)“).
 */
import type { Room, SchoolClass, Site, Subject, Teacher } from '../api/types';

/** Verzögerung bis zur Blase beim Überfahren (damit sie beim Darüberwischen nicht flackert). */
export const ABBR_OPEN_MS = 120;
/** Nachlaufzeit nach Verlassen, damit der Zeiger in die Blase wandern kann. */
export const ABBR_CLOSE_MS = 150;
/** Langdruck am Touch-Gerät (wo ein Antippen etwas anderes tut, z. B. eine Stunde auswählt). */
export const ABBR_LONG_PRESS_MS = 450;
/** Bewegung (px), ab der ein Langdruck abgebrochen wird (Wischen/Scrollen). */
export const ABBR_MOVE_TOLERANCE = 10;

export interface AbbrState {
  hover: boolean;
  focus: boolean;
  pinned: boolean;
}

export type AbbrEvent =
  | { type: 'enter' }
  | { type: 'leave' }
  | { type: 'focus' }
  | { type: 'blur' }
  /** Antippen / Klick / Enter: angeheftet umschalten (eine per Hover offene Blase wird angeheftet) */
  | { type: 'toggle' }
  | { type: 'pin' }
  | { type: 'escape' }
  | { type: 'outside' };

export const INITIAL_ABBR: AbbrState = { hover: false, focus: false, pinned: false };

export const isAbbrOpen = (s: AbbrState): boolean => s.hover || s.focus || s.pinned;

export function abbrReduce(s: AbbrState, e: AbbrEvent): AbbrState {
  switch (e.type) {
    case 'enter':
      return s.hover ? s : { ...s, hover: true };
    case 'leave':
      return s.hover ? { ...s, hover: false } : s;
    case 'focus':
      return s.focus ? s : { ...s, focus: true };
    case 'blur':
      return s.focus || s.pinned ? { ...s, focus: false, pinned: false } : s;
    case 'toggle':
      // offen (egal wodurch) → zu; zu → angeheftet
      return isAbbrOpen(s) ? INITIAL_ABBR : { ...s, pinned: true };
    case 'pin':
      return s.pinned ? s : { ...s, pinned: true };
    case 'escape':
    case 'outside':
      return isAbbrOpen(s) ? INITIAL_ABBR : s;
    default:
      return s;
  }
}

// ---------------------------------------------------------------- Texte

export interface Directory {
  teachers?: ReadonlyMap<string, Teacher>;
  subjects?: ReadonlyMap<string, Subject>;
  rooms?: ReadonlyMap<string, Room>;
  classes?: ReadonlyMap<string, SchoolClass>;
  sites?: ReadonlyMap<string, Site>;
}

export type AbbrKind = 'teacher' | 'subject' | 'room' | 'class' | 'site';

const clean = (s: string | null | undefined): string => (s ?? '').trim();

export function subjectText(s: Subject | undefined, id: string): string {
  const name = clean(s?.name);
  return name && name !== id ? name : '';
}

export function teacherText(t: Teacher | undefined, id: string, subjects?: ReadonlyMap<string, Subject>): string {
  if (!t) return '';
  const name = clean(t.name);
  const fach = (t.subjects ?? []).map((sid) => clean(subjects?.get(sid)?.name) || sid).filter(Boolean);
  const head = name && name !== id ? name : '';
  return [head, fach.join(', ')].filter(Boolean).join(' · ');
}

export function roomText(r: Room | undefined, id: string, sites?: ReadonlyMap<string, Site>): string {
  if (!r) return '';
  let name = clean(r.name);
  if (!name || name === id) name = `Raum ${id}`;
  const site = clean(sites?.get(r.site)?.name);
  if (site) {
    // „Fachraum 3 (S1)“: das Standort-Kürzel in Klammern durch den Standortnamen ersetzen
    const tail = ` (${r.site})`;
    const stripped = name.endsWith(tail) ? name.slice(0, -tail.length) : name;
    name = stripped.includes(site) ? stripped : `${stripped} (${site})`;
  }
  return name;
}

export function classText(c: SchoolClass | undefined, id: string, teachers?: ReadonlyMap<string, Teacher>): string {
  if (!c) return '';
  const name = clean(c.name);
  const head = name && name !== id ? name : `Klasse ${id}`;
  const lead = c.class_teacher ? clean(teachers?.get(c.class_teacher)?.name) || c.class_teacher : '';
  return lead ? `${head} · Klassenleitung ${lead}` : head;
}

export function siteText(s: Site | undefined, id: string): string {
  const name = clean(s?.name);
  return name && name !== id ? name : '';
}

/** Volle Bezeichnung zu einem Kürzel (leer = unbekannt → keine Blase). */
export function describeAbbr(kind: AbbrKind, id: string, dir: Directory): string {
  switch (kind) {
    case 'teacher':
      return teacherText(dir.teachers?.get(id), id, dir.subjects);
    case 'subject':
      return subjectText(dir.subjects?.get(id), id);
    case 'room':
      return roomText(dir.rooms?.get(id), id, dir.sites);
    case 'class':
      return classText(dir.classes?.get(id), id, dir.teachers);
    case 'site':
      return siteText(dir.sites?.get(id), id);
    default:
      return '';
  }
}

/** Zerlegt eine Kürzelliste („MÜL, SCH“ bzw. „MÜL/SCH“) in einzelne Kürzel (Zellen mit mehreren Lehrkräften/Räumen). */
export function splitIds(text: string | readonly string[] | null | undefined): string[] {
  if (!text) return [];
  const list = Array.isArray(text) ? (text as readonly string[]) : String(text).split(/\s*[,;/]\s*/);
  return list.map((x) => x.trim()).filter((x) => x && x !== '–' && x !== '-');
}
