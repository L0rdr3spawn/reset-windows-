import { describe, expect, it } from 'vitest';
import type { PollInput, PublicQuestion } from './api';
import {
  answerFilled,
  barPercent,
  cleanQuestion,
  emptyPoll,
  emptyQuestion,
  formatTimeLeft,
  gapCount,
  gapParts,
  moveId,
  openQuestions,
  pollError,
  pollFacts,
  questionError,
  solutionText,
  syncGaps,
  testRules,
  toggleChoice,
  verdict,
} from './logic';

const poll = (patch: Partial<PollInput> = {}): PollInput => ({ ...emptyPoll(), question: 'Wohin?', options: ['Zoo', 'Park'], ...patch });

describe('Abstimmung', () => {
  it('Balken: Anteil der Abstimmenden', () => {
    expect(barPercent(0, 0)).toBe(0);
    expect(barPercent(1, 3)).toBe(33);
    expect(barPercent(3, 3)).toBe(100);
    expect(barPercent(5, 3)).toBe(100);
  });

  it('Auswahl: Einzelwahl ersetzt, Mehrfachwahl schaltet um und beachtet die Höchstzahl', () => {
    expect(toggleChoice([0], 2, false, null)).toEqual([2]);
    expect(toggleChoice([0], 2, true, null)).toEqual([0, 2]);
    expect(toggleChoice([0, 2], 2, true, null)).toEqual([0]);
    expect(toggleChoice([0, 1], 2, true, 2)).toEqual([0, 1]);
  });

  it('Vorabprüfung', () => {
    expect(pollError(poll())).toBeNull();
    expect(pollError(poll({ question: ' ' }))).toMatch(/Frage/);
    expect(pollError(poll({ options: ['Zoo', ''] }))).toMatch(/zwei Antworten/);
    expect(pollError(poll({ options: ['Zoo', 'zoo'] }))).toMatch(/unterscheiden/);
    expect(pollError(poll({ multiple: true, max_choices: 5 }))).toMatch(/Höchstzahl/);
    expect(pollError(poll({ ends_at: new Date(Date.now() - 1000).toISOString() }))).toMatch(/Zukunft/);
  });

  it('Eigenschaften in der Kopfzeile', () => {
    const base = { anonymous: true, multiple: true, max_choices: 2, results: 'after_end' as const, closed: false, ends_at: null };
    expect(pollFacts(base, () => 'x')).toEqual(['anonym', 'bis zu 2 Antworten', 'Ergebnis nach dem Ende']);
    expect(pollFacts({ ...base, anonymous: false, multiple: false, results: 'live', closed: true }, () => 'x')).toEqual(['mit Namen', 'beendet']);
    expect(pollFacts({ ...base, anonymous: false, multiple: false, results: 'live', ends_at: '2026-10-20T10:00:00Z' }, () => 'am 20.10.')).toContain('endet am 20.10.');
  });
});

describe('Fragen', () => {
  it('Lücken im Text', () => {
    expect(gapCount('a ___ b ___ c')).toBe(2);
    expect(gapParts('a ___ b')).toEqual(['a ', ' b']);
    expect(gapCount('keine')).toBe(0);
    expect(syncGaps('a ___ b ___', [['x', 'y']])).toEqual([['x', 'y'], ['']]);
    expect(syncGaps('nur ___', [['x'], ['y']])).toEqual([['x']]);
  });

  it('Vorabprüfung je Art', () => {
    const single = { ...emptyQuestion('single'), text: 'Frage?', options: [{ text: 'a', correct: true }, { text: 'b', correct: false }] };
    expect(questionError(single)).toBeNull();
    expect(questionError({ ...single, options: [{ text: 'a', correct: true }, { text: 'b', correct: true }] })).toMatch(/Genau eine/);
    expect(questionError({ ...single, text: ' ' })).toMatch(/Fragetext/);
    const multi = { ...single, type: 'multi' as const, options: [{ text: 'a' }, { text: 'b' }] };
    expect(questionError(multi)).toMatch(/Mindestens eine/);
    const cloze = { ...emptyQuestion('cloze'), gaps: [['']] };
    expect(questionError(cloze)).toMatch(/Lücke/);
    expect(questionError({ ...cloze, gaps: [['Osten']] })).toBeNull();
    expect(questionError({ ...cloze, text: 'ohne' })).toMatch(/mindestens eine Lücke/);
    const num = { ...emptyQuestion('numeric'), text: 'n?', value: '3,5', tolerance: '0,1' };
    expect(questionError(num)).toBeNull();
    expect(questionError({ ...num, value: '' })).toMatch(/Zahl/);
    expect(questionError({ ...num, tolerance: '-1' })).toMatch(/Toleranz/);
    const match = { ...emptyQuestion('matching'), text: 'z', pairs: [{ left: 'a', right: 'b' }, { left: 'c', right: '' }] };
    expect(questionError(match)).toMatch(/zwei Teile/);
  });

  it('Bereinigen entfernt leere Einträge', () => {
    const q = cleanQuestion({ ...emptyQuestion('single'), text: ' F ', options: [{ text: ' a ', correct: true }, { text: '' }, { text: 'b' }] });
    expect(q.text).toBe('F');
    expect(q.options).toEqual([{ text: 'a', correct: true }, { text: 'b', correct: false }]);
  });
});

describe('Selbsttest', () => {
  const qs: PublicQuestion[] = [
    { id: 1, type: 'single', text: 'a', points: 1, options: [{ id: 0, text: 'x' }] },
    { id: 2, type: 'multi', text: 'b', points: 1, options: [] },
    { id: 3, type: 'cloze', text: 'c ___', points: 1, gaps: 1 },
    { id: 4, type: 'truefalse', text: 'd', points: 1 },
    { id: 5, type: 'matching', text: 'e', points: 1 },
    { id: 6, type: 'numeric', text: 'f', points: 1 },
  ];

  it('beantwortet oder offen', () => {
    expect(answerFilled(qs[0]!, 0)).toBe(true);
    expect(answerFilled(qs[0]!, undefined)).toBe(false);
    expect(answerFilled(qs[1]!, [])).toBe(false);
    expect(answerFilled(qs[1]!, [1])).toBe(true);
    expect(answerFilled(qs[2]!, ['', ' '])).toBe(false);
    expect(answerFilled(qs[2]!, ['Osten'])).toBe(true);
    expect(answerFilled(qs[3]!, false)).toBe(true);
    expect(answerFilled(qs[4]!, {})).toBe(false);
    expect(answerFilled(qs[4]!, { '0': 1 })).toBe(true);
    expect(answerFilled(qs[5]!, '0')).toBe(true);
    expect(openQuestions(qs, { '1': 0, '4': true }).map((q) => q.id)).toEqual([2, 3, 5, 6]);
  });

  it('Restzeit', () => {
    expect(formatTimeLeft(65)).toBe('1:05');
    expect(formatTimeLeft(3725)).toBe('1:02:05');
    expect(formatTimeLeft(-3)).toBe('0:00');
  });

  it('Regeln als Text', () => {
    expect(testRules({ max_attempts: 2, time_limit_min: 20, pass_percent: 60, immediate_feedback: true, question_count: 5, max_points: 10 })).toEqual([
      '5 Fragen',
      '10 Punkte',
      '2 Versuche',
      '20 Min.',
      'bestanden ab 60 %',
      'Rückmeldung sofort',
    ]);
    expect(testRules({ max_attempts: null, time_limit_min: null, pass_percent: null, immediate_feedback: false, question_count: 1, max_points: 1.5 })).toEqual(['1 Frage', '1,5 Punkte', 'beliebig oft']);
  });

  it('Lösung als Text und Urteil', () => {
    expect(solutionText(qs[0]!, { correct: [0] })).toBe('x');
    expect(solutionText(qs[3]!, { correct: false })).toBe('Falsch');
    expect(solutionText(qs[2]!, { accepted: [['Osten', 'Ost']] })).toBe('1: Osten / Ost');
    expect(solutionText(qs[5]!, { value: 3.14, tolerance: 0.01, unit: 'cm' })).toBe('3,14 cm (± 0,01)');
    expect(verdict(1).label).toBe('Richtig');
    expect(verdict(0.5).tone).toBe('warning');
    expect(verdict(0).label).toBe('Falsch');
  });

  it('Reihenfolge ändern', () => {
    expect(moveId([1, 2, 3], 2, -1)).toEqual([2, 1, 3]);
    expect(moveId([1, 2, 3], 1, -1)).toEqual([1, 2, 3]);
    expect(moveId([1, 2, 3], 3, 1)).toEqual([1, 2, 3]);
  });
});
