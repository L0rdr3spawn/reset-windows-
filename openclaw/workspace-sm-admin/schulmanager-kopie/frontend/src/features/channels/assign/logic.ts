/**
 * Reine Hilfsfunktionen der Aufgaben-Erweiterungen (ohne React, mit vitest getestet): Status der Bewertungstabelle,
 * Summe/Note aus dem Raster (spiegelt `schulmanager/grading.py`), Eingabe-Entwürfe für Raster und Fristen.
 */
import type { SubmissionRow } from '../types';
import type { Rubric, RubricCriterion, RubricFill, RubricKind, ScaleStep } from './types';

// ------------------------------------------------------------------ Zahlen
/** Punkte ohne überflüssige Nachkommastellen: `4` statt `4.0`, `3,5` mit Komma */
export function fmtPoints(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '';
  return String(Math.round(value * 100) / 100).replace('.', ',');
}

/** Eingabe mit Komma oder Punkt → Zahl (`null` bei leerer/ungültiger Eingabe) */
export function parsePoints(text: string): number | null {
  const t = text.trim().replace(',', '.');
  if (!t || !/^\d+(\.\d+)?$/.test(t)) return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}

// ------------------------------------------------------------------ Summe und Note
export function criterionMax(kind: RubricKind, c: RubricCriterion): number {
  if (kind === 'guide') return c.max_points ?? 0;
  return Math.max(0, ...(c.levels ?? []).map((l) => l.points));
}

export function rubricMax(r: Rubric | null | undefined): number {
  if (!r) return 0;
  return Math.round(r.criteria.reduce((sum, c) => sum + criterionMax(r.kind, c), 0) * 100) / 100;
}

/** Summe der bisher bewerteten Kriterien; `complete` = alle Kriterien bewertet */
export function rubricTotal(r: Rubric, fill: RubricFill): { points: number; complete: boolean; done: number } {
  let points = 0;
  let done = 0;
  for (const c of r.criteria) {
    const f = fill[c.id];
    if (!f) continue;
    if (r.kind === 'rubric') {
      const lv = (c.levels ?? []).find((l) => l.id === f.level);
      if (lv) {
        points += lv.points;
        done += 1;
      }
    } else if (typeof f.points === 'number' && Number.isFinite(f.points)) {
      points += Math.min(f.points, c.max_points ?? f.points);
      done += 1;
    }
  }
  return { points: Math.round(points * 100) / 100, complete: done === r.criteria.length, done };
}

/** Note zu Punkten nach Notenschlüssel (absteigend sortierte Stufen, wie der Server) */
export function gradeFor(points: number | null | undefined, max: number | null | undefined, steps: readonly ScaleStep[]): string | null {
  if (points === null || points === undefined || !max || max <= 0 || !steps.length) return null;
  const pct = (100 * points) / max;
  const sorted = [...steps].sort((a, b) => b.min - a.min);
  for (const s of sorted) if (pct + 1e-9 >= s.min) return s.label;
  return sorted[sorted.length - 1].label;
}

export function percentText(points: number | null | undefined, max: number | null | undefined): string {
  if (points === null || points === undefined || !max) return '';
  return `${Math.round((100 * points) / max)} %`;
}

export function setLevel(fill: RubricFill, criterionId: string, levelId: string): RubricFill {
  return { ...fill, [criterionId]: { ...fill[criterionId], level: levelId } };
}

export function setCriterionPoints(fill: RubricFill, criterionId: string, text: string): RubricFill {
  const next = { ...fill };
  const n = parsePoints(text);
  const prev = { ...fill[criterionId] };
  if (n === null) delete prev.points;
  else prev.points = n;
  if (prev.points === undefined && prev.level === undefined && !prev.comment) delete next[criterionId];
  else next[criterionId] = prev;
  return next;
}

export function setComment(fill: RubricFill, criterionId: string, comment: string): RubricFill {
  const prev = { ...fill[criterionId] };
  if (comment) prev.comment = comment;
  else delete prev.comment;
  const next = { ...fill };
  if (prev.points === undefined && prev.level === undefined && !prev.comment) delete next[criterionId];
  else next[criterionId] = prev;
  return next;
}

// ------------------------------------------------------------------ Status der Bewertungstabelle
export type RowStatusKey = 'abgegeben' | 'verspaetet' | 'fehlt' | 'offen' | 'bewertet' | 'ueberarbeitung';
export type RowTone = 'success' | 'warning' | 'danger' | 'info' | 'primary' | 'muted';

/** Status einer Zeile: abgegeben, verspätet, fehlt, bewertet (+ „Überarbeitung“ nach Rückgabe) */
export function rowStatus(row: Pick<SubmissionRow, 'status' | 'late'>): { key: RowStatusKey; label: string; tone: RowTone } {
  switch (row.status) {
    case 'bewertet':
      return { key: 'bewertet', label: row.late ? 'bewertet · verspätet' : 'bewertet', tone: 'primary' };
    case 'zurueckgegeben':
      return { key: 'ueberarbeitung', label: 'Überarbeitung', tone: 'warning' };
    case 'abgegeben':
    case 'verspaetet':
      return row.late || row.status === 'verspaetet' ? { key: 'verspaetet', label: 'verspätet', tone: 'warning' } : { key: 'abgegeben', label: 'abgegeben', tone: 'success' };
    case 'ueberfaellig':
      return { key: 'fehlt', label: 'fehlt', tone: 'danger' };
    default:
      return { key: 'offen', label: 'offen', tone: 'muted' };
  }
}

export type TableFilter = 'alle' | 'zu_bewerten' | 'fehlt' | 'erledigt';

export function matchesFilter(row: Pick<SubmissionRow, 'status'>, filter: TableFilter): boolean {
  switch (filter) {
    case 'zu_bewerten':
      return row.status === 'abgegeben' || row.status === 'verspaetet';
    case 'fehlt':
      return row.status === 'offen' || row.status === 'ueberfaellig' || row.status === 'zurueckgegeben';
    case 'erledigt':
      return row.status === 'bewertet';
    default:
      return true;
  }
}

/** Punkte-/Notentext einer Zeile (`8 / 10 · 3`) */
export function resultText(row: Pick<SubmissionRow, 'submission'>): string {
  const s = row.submission;
  if (!s) return '';
  const parts: string[] = [];
  if (s.points !== null && s.points !== undefined) parts.push(s.max_points ? `${fmtPoints(s.points)} / ${fmtPoints(s.max_points)}` : fmtPoints(s.points));
  if (s.grade) parts.push(`Note ${s.grade}`);
  return parts.join(' · ');
}

// ------------------------------------------------------------------ Entwürfe für das Raster
export interface LevelDraft {
  id?: string;
  title: string;
  points: string;
  description: string;
}

export interface CriterionDraft {
  id?: string;
  title: string;
  description: string;
  levels: LevelDraft[];
  maxPoints: string;
}

export interface RubricDraft {
  kind: RubricKind;
  criteria: CriterionDraft[];
}

export function newLevels(): LevelDraft[] {
  return [
    { title: 'voll erfüllt', points: '3', description: '' },
    { title: 'teilweise', points: '2', description: '' },
    { title: 'kaum', points: '1', description: '' },
    { title: 'nicht erfüllt', points: '0', description: '' },
  ];
}

export function newCriterion(kind: RubricKind): CriterionDraft {
  return { title: '', description: '', levels: kind === 'rubric' ? newLevels() : [], maxPoints: kind === 'guide' ? '10' : '' };
}

export function newRubricDraft(kind: RubricKind): RubricDraft {
  return { kind, criteria: [newCriterion(kind)] };
}

export function rubricToDraft(r: Rubric): RubricDraft {
  return {
    kind: r.kind,
    criteria: r.criteria.map((c) => ({
      id: c.id,
      title: c.title,
      description: c.description,
      maxPoints: c.max_points !== undefined ? fmtPoints(c.max_points) : '',
      levels: (c.levels ?? []).map((l) => ({ id: l.id, title: l.title, description: l.description, points: fmtPoints(l.points) })),
    })),
  };
}

/** Wechsel zwischen Raster und Leitfaden: Kriterien bleiben, Stufen bzw. Höchstpunkte werden ergänzt */
export function switchKind(draft: RubricDraft, kind: RubricKind): RubricDraft {
  if (draft.kind === kind) return draft;
  return {
    kind,
    criteria: draft.criteria.map((c) => ({
      ...c,
      levels: kind === 'rubric' ? (c.levels.length ? c.levels : newLevels()) : c.levels,
      maxPoints: kind === 'guide' ? c.maxPoints || '10' : c.maxPoints,
    })),
  };
}

/** Entwurf → Raster für den Server oder Fehlertext (deutsch, wie die Servermeldungen) */
export function draftToRubric(draft: RubricDraft): { rubric: Rubric } | { error: string } {
  if (!draft.criteria.length) return { error: 'Mindestens ein Kriterium angeben.' };
  const criteria: RubricCriterion[] = [];
  for (const [i, c] of draft.criteria.entries()) {
    const title = c.title.trim();
    if (!title) return { error: `Kriterium ${i + 1}: bitte einen Namen angeben.` };
    const base = { id: c.id ?? '', title, description: c.description.trim() };
    if (draft.kind === 'guide') {
      const max = parsePoints(c.maxPoints);
      if (max === null || max <= 0) return { error: `„${title}“: Höchstpunkte müssen größer als 0 sein.` };
      criteria.push({ ...base, max_points: max });
      continue;
    }
    if (c.levels.length < 2) return { error: `„${title}“: mindestens zwei Stufen angeben.` };
    const levels = [];
    for (const [j, l] of c.levels.entries()) {
      const lt = l.title.trim();
      if (!lt) return { error: `„${title}“: Stufe ${j + 1} braucht einen Namen.` };
      const pts = parsePoints(l.points);
      if (pts === null) return { error: `„${title}“ / ${lt}: bitte Punkte angeben.` };
      levels.push({ id: l.id ?? '', title: lt, description: l.description.trim(), points: pts });
    }
    criteria.push({ ...base, levels });
  }
  const rubric: Rubric = { kind: draft.kind, criteria };
  if (rubricMax(rubric) <= 0) return { error: 'Die Gesamtpunktzahl muss größer als 0 sein.' };
  return { rubric };
}

// ------------------------------------------------------------------ Fristen
/** Neue Frist = alte Frist + `days` Tage (lokale Zeit, für `datetime-local`) */
export function extendedDue(dueIso: string | null | undefined, days: number): string {
  const base = dueIso ? new Date(dueIso) : new Date();
  const d = new Date(base.getTime() + days * 86_400_000);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
