/**
 * Lehrer-Scope im Frontend (ARCHITECTURE.md §9.3) – reine Hilfsfunktionen (testbar, ohne React).
 *
 * Lehrkräfte haben `plans.read_all` nur für die eigenen Klassen (Scope `own_classes`). Welche Pläne ein Konto
 * öffnen darf, liefert der Server über `GET /timetable/allowed` (`null` = alle der Sammlung). Das Frontend
 * zeigt in Auswahllisten und Filtern nur diese Einträge; die eigentliche Prüfung macht immer der Server.
 */
import type { AllowedRefs } from './types';

export type RefKind = 'class' | 'teacher' | 'room' | 'student';

const KEY: Record<RefKind, 'classes' | 'teachers' | 'rooms' | 'students'> = {
  class: 'classes',
  teacher: 'teachers',
  room: 'rooms',
  student: 'students',
};

/** Erlaubte IDs einer Art – `null` = keine Einschränkung (oder Freigaben noch nicht geladen). */
export function allowedIds(allowed: AllowedRefs | null | undefined, kind: RefKind): Set<string> | null {
  if (!allowed || allowed.all) return null;
  const list = allowed[KEY[kind]];
  return list === null || list === undefined ? null : new Set(list);
}

/** Darf `ref` der Art `kind` geöffnet werden? (ohne Freigabeliste: ja – der Server prüft ohnehin) */
export function isAllowed(allowed: AllowedRefs | null | undefined, kind: RefKind, ref: string): boolean {
  if (allowed && !allowed.all && !allowed.kinds.includes(kind)) return false;
  const ids = allowedIds(allowed, kind);
  return ids === null || ids.has(ref);
}

/** Auswahlliste auf erlaubte Einträge kürzen. */
export function filterAllowed<T extends { value: string }>(options: readonly T[], allowed: AllowedRefs | null | undefined, kind: RefKind): T[] {
  if (allowed && !allowed.all && !allowed.kinds.includes(kind)) return [];
  const ids = allowedIds(allowed, kind);
  return ids === null ? [...options] : options.filter((o) => ids.has(o.value));
}

/** Ansichten (Klasse/Lehrkraft/Raum/Schüler) in der Reihenfolge von `base`, gekürzt auf die Freigaben. */
export function allowedKinds(base: readonly RefKind[], allowed: AllowedRefs | null | undefined): RefKind[] {
  if (!allowed || allowed.all) return [...base];
  return base.filter((k) => allowed.kinds.includes(k));
}

const NOUN: Record<RefKind, string> = { class: 'Klassenplan', teacher: 'Lehrerplan', room: 'Raumplan', student: 'Schülerplan' };

/** Verständlicher Text für einen gesperrten Plan (403). */
export function forbiddenText(kind: RefKind, scoped: boolean): string {
  if (!scoped) return `Für diesen ${NOUN[kind]} fehlt Ihrem Konto die Berechtigung.`;
  switch (kind) {
    case 'teacher':
      return 'Lehrkräfte sehen nur ihren eigenen Stundenplan – Pläne von Kolleginnen und Kollegen sind nicht freigegeben.';
    case 'student':
      return 'Schülerpläne sind nur für Schülerinnen und Schüler Ihrer eigenen Klassen freigegeben.';
    case 'class':
      return 'Sie sehen nur die Pläne der Klassen, in denen Sie unterrichten oder die Sie leiten.';
    default:
      return 'Dieser Plan ist für Ihr Konto nicht freigegeben.';
  }
}
