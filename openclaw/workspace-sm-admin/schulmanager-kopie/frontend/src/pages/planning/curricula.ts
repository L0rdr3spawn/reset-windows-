/**
 * Zuordnung Stundentafel → Klasse (gleiche Regel wie `schulmanager/planning.py::resolve_curricula`):
 * 1. eine Tafel, die die Klasse unter „Klassen“ nennt (eigene Klassen-Tafel);
 * 2. die Tafel des Jahrgangs der Klasse (`SchoolClass.profile` → `GradeProfile.curriculum`);
 * 3. Altbestand: eine Tafel **ohne** Klassen, deren `grades` die Klassenstufen-Nummer enthält.
 * Mehrere Tafeln auf derselben Stufe = Konflikt. Abgeleitete Tafeln (`base` + `deltas`) löst `effectiveEntries` auf
 * (wie `planning.effective_entries`).
 */
import type { Curriculum, CurriculumEntry, GradeProfile, SchoolClass } from '../../api/types';

export interface Resolution {
  curriculum: string | null;
  source: 'class' | 'profile' | 'grade' | null;
  candidates: string[];
  conflict: boolean;
}

export function resolveCurricula(curricula: readonly Curriculum[], classes: readonly SchoolClass[], profiles: readonly GradeProfile[] = []): Record<string, Resolution> {
  const out: Record<string, Resolution> = {};
  const byId = new Map(curricula.map((c) => [c.id, c]));
  const profById = new Map(profiles.map((p) => [p.id, p]));
  for (const cls of classes) {
    const byClass = curricula.filter((c) => c.classes.includes(cls.id));
    let found = byClass;
    let source: Resolution['source'] = byClass.length ? 'class' : null;
    if (!found.length && cls.profile) {
      const cur = byId.get(profById.get(cls.profile)?.curriculum ?? '');
      if (cur) {
        found = [cur];
        source = 'profile';
      }
    }
    if (!found.length) {
      found = curricula.filter((c) => !c.classes.length && c.grades.includes(cls.grade));
      source = found.length ? 'grade' : null;
    }
    const ids = found.map((c) => c.id);
    out[cls.id] = { curriculum: ids.length === 1 ? (ids[0] ?? null) : null, source, candidates: ids, conflict: ids.length > 1 };
  }
  return out;
}

export interface CurriculumScope {
  /** Klassen, für die die Tafel gilt */
  classes: string[];
  /** Klassen, für die außerdem eine andere gleichrangige Tafel gilt */
  conflicts: { classId: string; others: string[] }[];
  /** Jahrgangs-/Stufen-Treffer, die wegen einer Klassen-Tafel nicht gelten */
  shadowed: string[];
}

export function curriculumScope(id: string, curricula: readonly Curriculum[], classes: readonly SchoolClass[], profiles: readonly GradeProfile[] = []): CurriculumScope {
  const res = resolveCurricula(curricula, classes, profiles);
  const cur = curricula.find((c) => c.id === id);
  const profById = new Map(profiles.map((p) => [p.id, p]));
  const out: CurriculumScope = { classes: [], conflicts: [], shadowed: [] };
  for (const cls of classes) {
    const r = res[cls.id];
    if (!r) continue;
    if (r.candidates.includes(id)) {
      if (r.conflict) out.conflicts.push({ classId: cls.id, others: r.candidates.filter((x) => x !== id) });
      else out.classes.push(cls.id);
    } else if (cur && r.source === 'class' && ((cls.profile && profById.get(cls.profile)?.curriculum === id) || (!cur.classes.length && cur.grades.includes(cls.grade)))) {
      out.shadowed.push(cls.id);
    }
  }
  return out;
}

/** Suchtext einer Tafel: Name, Jahrgänge, Klassenstufen und alle Klassen, für die sie gilt oder im Konflikt steht. */
export function curriculumSearchText(cur: Curriculum, res: Record<string, Resolution>, classes: readonly SchoolClass[], profiles: readonly GradeProfile[] = []): string {
  const names = classes.filter((c) => cur.classes.includes(c.id) || res[c.id]?.candidates.includes(cur.id)).map((c) => c.name);
  const profs = profiles.filter((p) => p.curriculum === cur.id).map((p) => `${p.name} ${p.short}`);
  return `${cur.name} ${cur.grades.join(' ')} ${profs.join(' ')} ${names.join(' ')}`.toLowerCase();
}

/** Fächer, die in einer Tafel mehrfach vorkommen. */
export function duplicateSubjects(entries: readonly CurriculumEntry[]): Set<string> {
  const seen = new Set<string>();
  const dup = new Set<string>();
  for (const e of entries) {
    if (!e.subject) continue;
    if (seen.has(e.subject)) dup.add(e.subject);
    seen.add(e.subject);
  }
  return dup;
}

/** Klassenstufen zur Auswahl: alle Stufen vorhandener Klassen plus bereits gewählte (z. B. nur in einer Tafel genannte). */
export function gradeOptions(classes: readonly SchoolClass[], selected: readonly number[] = []): number[] {
  return [...new Set([...classes.map((c) => c.grade), ...selected])].sort((a, b) => a - b);
}

export const GRADE_MIN = 0;
export const GRADE_MAX = 20;

/** Wochenstunden, die das Zeitraster hergibt (Stunden pro Tag × Unterrichtstage); 0 = unbekannt. */
export function weeklyCapacity(periodsPerDay: number, schoolDays: number): number {
  return periodsPerDay > 0 && schoolDays > 0 ? periodsPerDay * schoolDays : 0;
}

// ---------------------------------------------------------------- Ableitung (Basis + Abweichungen)

/** Wirksame Zeilen: eigene `entries` oder – mit `base` – Basis plus `deltas` (Stunden addiert, ≤ 0 fällt weg). */
export function effectiveEntries(all: readonly Curriculum[], cur: Curriculum | null | undefined, seen: ReadonlySet<string> = new Set()): CurriculumEntry[] {
  if (!cur) return [];
  if (!cur.base || seen.has(cur.id)) return cur.entries.map((e) => ({ ...e }));
  const base = all.find((c) => c.id === cur.base);
  if (!base) return cur.entries.map((e) => ({ ...e }));
  const merged = new Map<string, CurriculumEntry>();
  for (const e of effectiveEntries(all, base, new Set([...seen, cur.id]))) if (e.subject) merged.set(e.subject, { ...e });
  for (const d of cur.deltas ?? []) {
    if (!d.subject) continue;
    const hours = (merged.get(d.subject)?.hours ?? 0) + d.hours;
    if (hours <= 0) merged.delete(d.subject);
    else merged.set(d.subject, { subject: d.subject, hours, double: d.double });
  }
  return [...merged.values()];
}

/** Abweichungen, die aus `base` genau `target` machen (Zielwerte → `deltas`, wie `planning.deltas_for`). */
export function deltasFor(base: readonly CurriculumEntry[], target: readonly CurriculumEntry[]): CurriculumEntry[] {
  const b = new Map(base.filter((e) => e.subject).map((e) => [e.subject, e]));
  const out: CurriculumEntry[] = [];
  for (const t of target) {
    if (!t.subject) continue;
    const e = b.get(t.subject);
    if (!e) out.push({ subject: t.subject, hours: t.hours, double: t.double });
    else if (e.hours !== t.hours || !!e.double !== !!t.double) out.push({ subject: t.subject, hours: t.hours - e.hours, double: t.double });
  }
  const wanted = new Set(target.map((t) => t.subject));
  for (const [subj, e] of b) if (!wanted.has(subj)) out.push({ subject: subj, hours: -e.hours, double: e.double });
  return out;
}

/** Wert einer Zelle (Fach × Tafel) setzen: bei eigenen Tafeln die Zeile, bei abgeleiteten die Abweichung. 0 = Fach raus. */
export function setEffectiveHours(all: readonly Curriculum[], cur: Curriculum, subject: string, hours: number, double?: boolean): Curriculum {
  const current = effectiveEntries(all, cur);
  const old = current.find((e) => e.subject === subject);
  const next = current.filter((e) => e.subject !== subject);
  if (hours > 0) next.push({ subject, hours, double: double ?? old?.double ?? false });
  if (cur.base && all.some((c) => c.id === cur.base)) {
    const base = all.find((c) => c.id === cur.base);
    return { ...cur, deltas: deltasFor(effectiveEntries(all, base), next) };
  }
  // Reihenfolge der eigenen Zeilen behalten
  const kept = cur.entries.filter((e) => e.subject !== subject || hours > 0).map((e) => (e.subject === subject ? { ...e, hours, double: double ?? e.double } : e));
  if (hours > 0 && !kept.some((e) => e.subject === subject)) kept.push({ subject, hours, double: double ?? false });
  return { ...cur, entries: kept };
}

/** Abweichung einer Zelle zur Basis: `null` = keine Basis oder gleich. */
export function deviation(all: readonly Curriculum[], cur: Curriculum, subject: string): { base: number; delta: number } | null {
  if (!cur.base) return null;
  const base = all.find((c) => c.id === cur.base);
  if (!base) return null;
  const b = effectiveEntries(all, base).find((e) => e.subject === subject)?.hours ?? 0;
  const v = effectiveEntries(all, cur).find((e) => e.subject === subject)?.hours ?? 0;
  return b === v ? null : { base: b, delta: v - b };
}

/** Reihenfolge der Spalten: nach kleinster Klassenstufe ihrer Jahrgänge, dann Name. */
export function curriculumOrder(curricula: readonly Curriculum[], profiles: readonly GradeProfile[]): Curriculum[] {
  const rank = (c: Curriculum): number => {
    const grades = [...profiles.filter((p) => p.curriculum === c.id && p.grade !== null).map((p) => p.grade as number), ...c.grades];
    return grades.length ? Math.min(...grades) : c.classes.length ? 500 : 900;
  };
  return [...curricula].sort((a, b) => rank(a) - rank(b) || a.name.localeCompare(b.name, 'de', { numeric: true }));
}

/** Fächer der Matrix: Vereinigung aller wirksamen Zeilen, in der Reihenfolge der Fächerliste (unbekannte zuletzt). */
export function matrixSubjects(all: readonly Curriculum[], subjects: readonly { id: string }[]): string[] {
  const used = new Set<string>();
  for (const c of all) for (const e of effectiveEntries(all, c)) if (e.subject) used.add(e.subject);
  const known = subjects.map((s) => s.id).filter((id) => used.has(id));
  const unknown = [...used].filter((id) => !subjects.some((s) => s.id === id)).sort();
  return [...known, ...unknown];
}
