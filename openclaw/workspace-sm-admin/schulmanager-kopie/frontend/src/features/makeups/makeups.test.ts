import { describe, expect, it } from 'vitest';
import type { MakeupRow } from './api';
import { abbrNamesOf } from './api';
import { appointmentText, attestActionNeeded, groupByExam, needsDate, periodSpan, rowsForSuggestion, sortRows, suggestionKind } from './logic';

function row(p: Partial<MakeupRow>): MakeupRow {
  return {
    id: 1,
    exam_id: 'KA1',
    course_id: 'K1',
    student_id: 'S1',
    student_name: 'Mia B.',
    class_id: '7a',
    exam_title: 'Klassenarbeit',
    exam_kind: 'klausur',
    label: 'D 7a',
    subject: 'D',
    classes: ['7a'],
    teachers: ['MUE'],
    exam_date: '2026-11-03',
    exam_start: 1,
    exam_length: 1,
    exam_time: '08:45',
    exam_room: null,
    status: 'offen',
    status_label: 'Termin offen',
    source: 'abwesend',
    source_label: 'abwesend',
    attest: { state: 'fehlt', label: 'Attest fehlt', missing: true },
    attest_waived: false,
    level: 'teacher',
    appointment: null,
    can_schedule: true,
    can_waive: false,
    names: { teachers: { MUE: 'Frau Müller' }, subjects: { D: 'Deutsch' }, rooms: {}, classes: {} },
    ...p,
  };
}

describe('Nachschreibtermine', () => {
  it('sortiert Offenes zuerst, Erledigtes unten', () => {
    const rows = [row({ id: 1, status: 'erledigt' }), row({ id: 2, status: 'offen', exam_date: '2026-11-05' }), row({ id: 3, status: 'angesetzt' })];
    expect(sortRows(rows).map((r) => r.id)).toEqual([2, 3, 1]);
  });
  it('gruppiert je Klausur', () => {
    const g = groupByExam([row({ id: 1 }), row({ id: 2, exam_id: 'KA2' }), row({ id: 3 })]);
    expect(g.map((x) => [x.exam_id, x.rows.length])).toEqual([['KA1', 2], ['KA2', 1]]);
  });
  it('formatiert Stunden und Termin', () => {
    expect(periodSpan(2, 1)).toBe('3. Std.');
    expect(periodSpan(7, 2)).toBe('8.–9. Std.');
    expect(appointmentText({ start: 7, length: 2, time: '14:20', room: 'R12' })).toBe('8.–9. Std. · 14:20 · Raum R12');
  });
  it('Attest-Handlung nur für Betroffene und Klassenleitung, nicht für die Fachlehrkraft', () => {
    expect(attestActionNeeded(row({ level: 'family' }))).toBe(true);
    expect(attestActionNeeded(row({ level: 'teacher' }))).toBe(false);
    expect(attestActionNeeded(row({ level: 'full', status: 'erledigt' }))).toBe(false);
    expect(attestActionNeeded(row({ level: 'full', attest: { state: 'genehmigt', label: '', missing: false } }))).toBe(false);
  });
  it('Termin nötig nur bei offenen Zeilen mit Recht', () => {
    expect(needsDate([row({ id: 1 }), row({ id: 2, can_schedule: false }), row({ id: 3, status: 'angesetzt' })]).map((r) => r.id)).toEqual([1]);
  });
  it('liefert Namen für die Kürzel-Sprechblase', () => {
    expect(abbrNamesOf([row({})])?.teacher?.MUE).toBe('Frau Müller');
    expect(abbrNamesOf([])).toBeNull();
  });
});

describe('Terminvorschläge', () => {
  it('wählt nur die Zeilen, die der Vorschlag abdeckt', () => {
    const rows = [row({ id: 1, student_id: 'S1' }), row({ id: 2, student_id: 'S2' })];
    expect(rowsForSuggestion(rows, { student_ids: ['S2'] }).map((r) => r.id)).toEqual([2]);
  });
  it('benennt die Art des Vorschlags', () => {
    expect(suggestionKind({ kind: 'unterricht' })).toBe('Eigene Stunde');
    expect(suggestionKind({ kind: 'frei', slot: 'luecke' })).toBe('Freistunde');
    expect(suggestionKind({ kind: 'frei', slot: 'rand' })).toBe('Randstunde');
  });
});
