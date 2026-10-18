/** Reine Hilfsfunktionen der Jahrgänge-Ansicht (ohne React, getestet in logic.test.ts). */
import type { GradeProfile } from '../../api/types';
import { fallbackColor, isHexColor } from '../../lib/colors';
import { GRADE_MAX, GRADE_MIN } from '../../pages/planning/curricula';
import type { ProfileImpact } from './types';

export { GRADE_MAX, GRADE_MIN };

const LETTERS = 'abcdefghijklmnopqrstuvwxyz';

/** Vorschläge für neue Klassenkürzel einer Stufe: 5a, 5b, … – bereits vergebene Kürzel werden übersprungen. */
export function suggestClassNames(grade: number, existing: readonly string[], count: number): string[] {
  const taken = new Set(existing.map((x) => x.toLowerCase()));
  const out: string[] = [];
  for (let i = 0; i < 200 && out.length < count; i++) {
    const letter = i < LETTERS.length ? (LETTERS[i] as string) : `${LETTERS[Math.floor(i / LETTERS.length) - 1]}${LETTERS[i % LETTERS.length]}`;
    const name = `${grade}${letter}`;
    if (!taken.has(name.toLowerCase())) out.push(name);
  }
  return out;
}

export function gradeValid(g: number): boolean {
  return Number.isInteger(g) && g >= GRADE_MIN && g <= GRADE_MAX;
}

export interface ImpactLine {
  text: string;
  danger: boolean;
}

/** Folgen-Zeilen für den Löschdialog von Klassen (gefährliche zuerst). */
export function impactLines(t: { students: number; courses_deleted: number; courses_shared: number; lessons: number; absences: number }, studentsMoved: boolean): ImpactLine[] {
  const out: ImpactLine[] = [];
  if (t.students) out.push(studentsMoved ? { text: `${t.students} Schüler/in${t.students === 1 ? '' : 'nen'} werden in die andere Klasse verschoben`, danger: false } : { text: `${t.students} Schüler/in${t.students === 1 ? '' : 'nen'} werden mit gelöscht`, danger: true });
  if (t.courses_deleted) out.push({ text: `${t.courses_deleted} Kurs${t.courses_deleted === 1 ? '' : 'e'} werden gelöscht`, danger: true });
  if (t.lessons) out.push({ text: `${t.lessons} Stunde${t.lessons === 1 ? '' : 'n'} verschwinden aus dem Stundenplan`, danger: true });
  if (t.courses_shared) out.push({ text: `${t.courses_shared} klassenübergreifende${t.courses_shared === 1 ? 'r Kurs verliert' : ' Kurse verlieren'} diese Klasse (bleiben für die anderen bestehen)`, danger: false });
  if (t.absences) out.push({ text: `${t.absences} Abwesenheits-Eintrag/-Einträge der Klasse werden gelöscht`, danger: false });
  return out;
}

/** Löschen braucht eine ausdrückliche Bestätigung (Eintippen), sobald Daten mit verloren gehen. */
export function needsTypedConfirm(t: { students: number; courses_deleted: number; lessons: number }, studentsMoved: boolean): boolean {
  return (!studentsMoved && t.students > 0) || t.courses_deleted > 0 || t.lessons > 0;
}

/** Folgen-Zeilen für das Löschen eines Jahrgangs („betrifft 3 Klassen, 42 Kurse, 120 Stunden im Plan“). */
export function profileImpactLines(imp: ProfileImpact, moveTo: string | null, deleteCurriculum: boolean): ImpactLine[] {
  const out: ImpactLine[] = [];
  const n = imp.classes.length;
  if (n) {
    const target = moveTo ? imp.alternatives.find((a) => a.id === moveTo)?.name ?? moveTo : null;
    out.push(
      target
        ? { text: `${n} Klasse${n === 1 ? ' wechselt' : 'n wechseln'} zu „${target}“ (${imp.classes.map((c) => c.name).join(', ')})`, danger: false }
        : { text: `${n} Klasse${n === 1 ? '' : 'n'} ohne Jahrgang und ohne Stundentafel (${imp.classes.map((c) => c.name).join(', ')})`, danger: true },
    );
  }
  if (imp.courses) out.push({ text: `${imp.courses} Kurs${imp.courses === 1 ? '' : 'e'} aus der Stundentafel${imp.lessons ? ` mit ${imp.lessons} Stunde${imp.lessons === 1 ? '' : 'n'} im Plan` : ''} ändern sich beim nächsten „Kurse erzeugen“`, danger: !moveTo });
  if (imp.curriculum) {
    if (deleteCurriculum && !imp.curriculum.shared) {
      out.push({ text: `Stundentafel „${imp.curriculum.name}“ wird gelöscht${imp.curriculum.derived.length ? `; ${imp.curriculum.derived.length} abgeleitete Tafel${imp.curriculum.derived.length === 1 ? ' wird' : 'n werden'} eigenständig` : ''}`, danger: true });
    } else {
      out.push({ text: `Stundentafel „${imp.curriculum.name}“ bleibt erhalten`, danger: false });
    }
  }
  return out;
}

/** Anzeigefarbe eines Jahrgangs: eigene Farbe oder eine stabile aus dem Namen. */
export function profileColor(p: Pick<GradeProfile, 'id' | 'color'>): string {
  return isHexColor(p.color) ? p.color : fallbackColor(p.id);
}

/** Kurzname fürs Kärtchen: eigener Kurzname, sonst Klassenstufe, sonst Anfang des Namens. */
export function profileShort(p: Pick<GradeProfile, 'name' | 'short' | 'grade'>): string {
  if (p.short.trim()) return p.short.trim();
  if (p.grade !== null && p.grade !== undefined) return String(p.grade);
  return p.name.trim().slice(0, 4);
}

/** Vorschlag für eine Jahrgangs-ID aus dem Kurznamen bzw. Namen („5 IF“ → „5IF“). */
export function suggestProfileId(name: string, short: string, taken: readonly string[]): string {
  const base = (short || name).replace(/[^\p{L}\p{N}-]+/gu, '').slice(0, 20) || 'JG';
  let id = base;
  let n = 2;
  const low = new Set(taken.map((t) => t.toLowerCase()));
  while (low.has(id.toLowerCase())) id = `${base}${n++}`;
  return id;
}

/** Klassen gruppiert nach Jahrgang für Auswahllisten: „5a · Jahrgang 5“. */
export function classOptionSub(cls: { grade: number; profile?: string | null }, profiles: readonly GradeProfile[]): string {
  const p = cls.profile ? profiles.find((x) => x.id === cls.profile) : null;
  return p ? p.name : `Stufe ${cls.grade} · ohne Jahrgang`;
}
