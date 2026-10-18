/**
 * Reine Hilfen der Lernaktivitäten (ohne React): Abstimmung, Fragen, Selbsttest. Der Server prüft und wertet immer
 * erneut – hier steht nur, was die Oberfläche zum Anzeigen und zur Vorabprüfung braucht.
 */
import type { FieldType } from '../formulare/api';
import type { Answer, CheckedView, PollInput, PollResults, PollState, PublicQuestion, QuestionInput, QuestionType, Selftest, SurveyStatus, TestState } from './api';

export const MAX_POLL_OPTIONS = 20;
export const MAX_QUESTION_OPTIONS = 10;

export const POLL_RESULT_LABELS: Record<PollResults, string> = {
  live: 'Sofort sichtbar',
  after_vote: 'Nach der eigenen Stimme',
  after_end: 'Erst nach dem Ende',
};

export const QUESTION_TYPE_LABELS: Record<QuestionType, string> = {
  single: 'Einfachauswahl',
  multi: 'Mehrfachauswahl',
  truefalse: 'Wahr / Falsch',
  cloze: 'Lückentext',
  matching: 'Zuordnung',
  numeric: 'Zahl mit Toleranz',
};

export const TEST_STATE_LABELS: Record<TestState, string> = { entwurf: 'Entwurf', offen: 'Offen', geschlossen: 'Beendet', geplant: 'Geplant' };
export const SURVEY_STATE_LABELS: Record<SurveyStatus, string> = { entwurf: 'Entwurf', offen: 'Offen', geschlossen: 'Beendet' };
export const REVIEW_LABELS = { none: 'Nichts anzeigen', score: 'Nur den Punktestand', full: 'Punktestand und Lösungen' } as const;

/** Feldarten einer Umfrage (Teilmenge des Formular-Baukastens) mit ihren Namen. */
export const SURVEY_FIELD_TYPES: FieldType[] = ['select', 'multiselect', 'scale', 'yesno', 'textarea', 'text', 'number'];
export const SURVEY_TYPE_LABELS: Partial<Record<FieldType, string>> = {
  select: 'Auswahl (eine Antwort)',
  multiselect: 'Mehrfachauswahl',
  scale: 'Skala 1–5',
  yesno: 'Ja / Nein',
  textarea: 'Freitext',
  text: 'Kurzer Text',
  number: 'Zahl',
};

// ---------------------------------------------------------------------------------------------- Abstimmung
/** Anteil der Abstimmenden (0–100, ganze Zahl); bei Mehrfachauswahl ergibt die Summe mehr als 100. */
export function barPercent(count: number, total: number): number {
  if (!total || count <= 0) return 0;
  return Math.min(100, Math.round((100 * count) / total));
}

/** Auswahl umschalten: Einzelauswahl ersetzt, Mehrfachauswahl fügt hinzu/entfernt (bis zur Höchstzahl). */
export function toggleChoice(current: readonly number[], index: number, multiple: boolean, max: number | null): number[] {
  if (!multiple) return [index];
  if (current.includes(index)) return current.filter((i) => i !== index);
  if (max && current.length >= max) return [...current];
  return [...current, index].sort((a, b) => a - b);
}

export const emptyPoll = (): PollInput => ({ question: '', options: ['', ''], multiple: false, max_choices: null, anonymous: false, results: 'live', ends_at: null });

export const cleanOptions = (options: readonly string[]): string[] => options.map((o) => o.trim()).filter(Boolean);

/** Vorabprüfung einer neuen Abstimmung (`null` = in Ordnung). */
export function pollError(p: PollInput): string | null {
  if (!p.question.trim()) return 'Bitte eine Frage eingeben.';
  const opts = cleanOptions(p.options);
  if (opts.length < 2) return 'Bitte mindestens zwei Antworten angeben.';
  if (new Set(opts.map((o) => o.toLowerCase())).size !== opts.length) return 'Die Antworten müssen sich unterscheiden.';
  if (p.multiple && p.max_choices !== null && (p.max_choices < 1 || p.max_choices > opts.length)) return `Höchstzahl: 1 bis ${opts.length}.`;
  if (p.ends_at && new Date(p.ends_at).getTime() <= Date.now()) return 'Das Ende muss in der Zukunft liegen.';
  return null;
}

/** Kurze Eigenschaften einer Abstimmung für die Kopfzeile. */
export function pollFacts(p: Pick<PollState, 'anonymous' | 'multiple' | 'max_choices' | 'results' | 'closed' | 'ends_at'>, formatWhen: (iso: string) => string): string[] {
  const out: string[] = [];
  out.push(p.anonymous ? 'anonym' : 'mit Namen');
  if (p.multiple) out.push(p.max_choices ? `bis zu ${p.max_choices} Antworten` : 'mehrere Antworten');
  if (p.results === 'after_vote') out.push('Ergebnis nach der Stimme');
  if (p.results === 'after_end') out.push('Ergebnis nach dem Ende');
  if (p.closed) out.push('beendet');
  else if (p.ends_at) out.push(`endet ${formatWhen(p.ends_at)}`);
  return out;
}

// ---------------------------------------------------------------------------------------------- Fragen
export const GAP_RE = /_{3,}/g;

/** Text zwischen den Lücken (`___`): n Lücken ergeben n + 1 Teile. */
export const gapParts = (text: string): string[] => text.split(/_{3,}/);
export const gapCount = (text: string): number => Math.max(0, gapParts(text).length - 1);

/** Antwortlisten an die Zahl der Lücken im Text anpassen (vorhandene bleiben). */
export function syncGaps(text: string, gaps: readonly (readonly string[])[]): string[][] {
  const n = gapCount(text);
  return Array.from({ length: n }, (_, i) => [...(gaps[i] ?? [''])]);
}

export function emptyQuestion(type: QuestionType): QuestionInput {
  const base = { type, text: '', points: 1, feedback: '', category: '' };
  switch (type) {
    case 'single':
    case 'multi':
      return { ...base, options: [{ text: '', correct: true }, { text: '', correct: false }] };
    case 'truefalse':
      return { ...base, correct: true };
    case 'cloze':
      return { ...base, text: 'Die ___ geht im Osten auf.', gaps: [['']], case_sensitive: false };
    case 'matching':
      return { ...base, pairs: [{ left: '', right: '' }, { left: '', right: '' }] };
    default:
      return { ...base, value: '', tolerance: 0, unit: '' };
  }
}

/** Vorabprüfung einer Frage (`null` = in Ordnung). */
export function questionError(q: QuestionInput): string | null {
  if (!q.text.trim()) return 'Bitte den Fragetext eingeben.';
  if (q.type === 'single' || q.type === 'multi') {
    const opts = (q.options ?? []).filter((o) => o.text.trim());
    if (opts.length < 2) return 'Bitte mindestens zwei Antworten angeben.';
    const right = opts.filter((o) => o.correct).length;
    if (q.type === 'single' && right !== 1) return 'Genau eine Antwort muss richtig sein.';
    if (q.type === 'multi' && right < 1) return 'Mindestens eine Antwort muss richtig sein.';
  }
  if (q.type === 'cloze') {
    if (gapCount(q.text) < 1) return 'Der Text braucht mindestens eine Lücke (___).';
    if ((q.gaps ?? []).some((g) => !g.some((a) => a.trim()))) return 'Zu jeder Lücke gehört eine richtige Antwort.';
  }
  if (q.type === 'matching') {
    const pairs = (q.pairs ?? []).filter((p) => p.left.trim() || p.right.trim());
    if (pairs.length < 2) return 'Bitte mindestens zwei Paare angeben.';
    if (pairs.some((p) => !p.left.trim() || !p.right.trim())) return 'Zu jedem Eintrag gehören zwei Teile.';
  }
  if (q.type === 'numeric') {
    if (Number.isNaN(Number(String(q.value ?? '').replace(',', '.'))) || String(q.value ?? '').trim() === '') return 'Bitte die richtige Zahl angeben.';
    const tol = String(q.tolerance ?? '').trim();
    if (tol !== '' && (Number.isNaN(Number(tol.replace(',', '.'))) || Number(tol.replace(',', '.')) < 0)) return 'Die Toleranz muss eine Zahl ab 0 sein.';
  }
  return null;
}

/** Leere Einträge entfernen, bevor die Frage gespeichert wird. */
export function cleanQuestion(q: QuestionInput): QuestionInput {
  const out: QuestionInput = { ...q, text: q.text.trim() };
  if (out.options) out.options = out.options.filter((o) => o.text.trim()).map((o) => ({ ...o, text: o.text.trim(), correct: !!o.correct }));
  if (out.pairs) out.pairs = out.pairs.filter((p) => p.left.trim() || p.right.trim());
  if (out.gaps) out.gaps = out.gaps.map((g) => g.map((a) => a.trim()).filter(Boolean));
  return out;
}

// ---------------------------------------------------------------------------------------------- Selbsttest
/** Ist die Frage beantwortet (für den Hinweis „noch offen“ beim Abgeben)? */
export function answerFilled(q: Pick<PublicQuestion, 'type'>, a: Answer | undefined): boolean {
  if (a === null || a === undefined) return false;
  switch (q.type) {
    case 'single':
      return typeof a === 'number';
    case 'multi':
      return Array.isArray(a) && a.length > 0;
    case 'truefalse':
      return typeof a === 'boolean';
    case 'cloze':
      return Array.isArray(a) && (a as string[]).some((x) => String(x).trim() !== '');
    case 'matching':
      return typeof a === 'object' && !Array.isArray(a) && Object.keys(a).length > 0;
    default:
      return String(a).trim() !== '';
  }
}

export function openQuestions(questions: readonly PublicQuestion[], answers: Record<string, Answer>): PublicQuestion[] {
  return questions.filter((q) => !answerFilled(q, answers[String(q.id)]));
}

/** Restzeit als „4:05“ bzw. „1:02:09“. */
export function formatTimeLeft(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = String(s % 60).padStart(2, '0');
  return h ? `${h}:${String(m).padStart(2, '0')}:${sec}` : `${m}:${sec}`;
}

export const numberText = (n: number | null | undefined, digits = 1): string => (n === null || n === undefined ? '–' : n.toLocaleString('de-DE', { maximumFractionDigits: digits }));
export const percentText = (n: number | null | undefined): string => (n === null || n === undefined ? '–' : `${numberText(n)} %`);
export const pointsText = (points: number | null | undefined, max: number | null | undefined): string => `${numberText(points, 2)} von ${numberText(max, 2)} Punkten`;

/** Kurzbeschreibung der Regeln eines Tests („2 Versuche · 20 Min. · Bestehen ab 60 %“). */
export function testRules(t: Pick<Selftest, 'max_attempts' | 'time_limit_min' | 'pass_percent' | 'immediate_feedback' | 'question_count' | 'max_points'>): string[] {
  const out = [`${t.question_count} ${t.question_count === 1 ? 'Frage' : 'Fragen'}`, `${numberText(t.max_points, 2)} Punkte`];
  out.push(t.max_attempts ? `${t.max_attempts} ${t.max_attempts === 1 ? 'Versuch' : 'Versuche'}` : 'beliebig oft');
  if (t.time_limit_min) out.push(`${t.time_limit_min} Min.`);
  if (t.pass_percent !== null && t.pass_percent !== undefined) out.push(`bestanden ab ${numberText(t.pass_percent)} %`);
  if (t.immediate_feedback) out.push('Rückmeldung sofort');
  return out;
}

/** Farbton für ein Ergebnis: Anteil richtig (0–1). */
export function fractionTone(fraction: number | undefined): 'success' | 'warning' | 'danger' | 'muted' {
  if (fraction === undefined) return 'muted';
  if (fraction >= 0.999) return 'success';
  if (fraction > 0) return 'warning';
  return 'danger';
}

/** Elemente nach `ids` ordnen und Verschieben um eine Stelle. */
export function moveId(list: readonly number[], id: number, dir: -1 | 1): number[] {
  const i = list.indexOf(id);
  const j = i + dir;
  if (i < 0 || j < 0 || j >= list.length) return [...list];
  const copy = [...list];
  [copy[i], copy[j]] = [copy[j] as number, copy[i] as number];
  return copy;
}

// ---------------------------------------------------------------------------------------------- Lösungen anzeigen
/** Richtige Lösung als Text (für die Rückmeldung nach der Antwort bzw. nach dem Test). */
export function solutionText(q: PublicQuestion, solution: CheckedView['solution']): string {
  switch (q.type) {
    case 'single':
    case 'multi': {
      const ids = (solution.correct as number[] | undefined) ?? [];
      return (q.options ?? []).filter((o) => ids.includes(o.id)).map((o) => o.text).join('; ');
    }
    case 'truefalse':
      return solution.correct ? 'Wahr' : 'Falsch';
    case 'cloze':
      return (solution.accepted ?? []).map((g, i) => `${i + 1}: ${g.join(' / ')}`).join('; ');
    case 'matching': {
      const lefts = new Map((q.lefts ?? []).map((l) => [l.id, l.text]));
      const rights = new Map((q.rights ?? []).map((r) => [r.id, r.text]));
      return (solution.pairs ?? []).map((p) => `${lefts.get(p.left) ?? '?'} → ${rights.get(p.right) ?? '?'}`).join('; ');
    }
    default: {
      const tol = solution.tolerance ? ` (± ${numberText(solution.tolerance, 6)})` : '';
      return `${numberText(solution.value, 6)}${solution.unit ? ` ${solution.unit}` : ''}${tol}`;
    }
  }
}

export function verdict(fraction: number): { label: string; tone: 'success' | 'warning' | 'danger' } {
  if (fraction >= 0.999) return { label: 'Richtig', tone: 'success' };
  if (fraction > 0) return { label: 'Teilweise richtig', tone: 'warning' };
  return { label: 'Falsch', tone: 'danger' };
}
