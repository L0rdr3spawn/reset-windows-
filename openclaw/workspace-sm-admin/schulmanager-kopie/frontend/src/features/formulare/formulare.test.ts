import { describe, expect, it } from 'vitest';
import type { FormAction, FormDefinition, FormField } from './api';
import { formsApi } from './api';
import {
  answerErrors,
  audienceText,
  dropFieldRefs,
  emptyDefinition,
  initialAnswers,
  isOpen,
  moveItem,
  newField,
  nextFieldId,
  publishBlocker,
  workflowText,
} from './logic';

function defn(fields: FormField[], extra: Partial<FormDefinition> = {}): FormDefinition {
  return { ...emptyDefinition(), fields, ...extra };
}

const FIELDS: FormField[] = [
  { id: 'kind', type: 'student', label: 'Kind', required: true },
  { id: 'zeit', type: 'daterange', label: 'Zeitraum', required: true },
  { id: 'grund', type: 'textarea', label: 'Grund', required: true },
  { id: 'zahl', type: 'number', label: 'Anzahl', min: 1, max: 5 },
  { id: 'ok', type: 'confirm', label: 'Bestätigung', required: true },
  { id: 'sig', type: 'signature', label: 'Unterschrift', required: true },
];

describe('Formular-Baukasten – Felder', () => {
  it('vergibt freie Kennungen und passende Voreinstellungen', () => {
    expect(nextFieldId([])).toBe('f1');
    expect(nextFieldId([{ id: 'f1', type: 'text', label: 'a' }])).toBe('f2');
    expect(nextFieldId([{ id: 'f2', type: 'text', label: 'a' }])).toBe('f3'); // f2 belegt, Länge 1 → f2 wäre doppelt
    const sel = newField('select', []);
    expect(sel.options?.length).toBe(2);
    expect(newField('signature', []).required).toBe(true);
    expect(newField('text', []).required).toBe(false);
  });

  it('verschiebt Elemente nur innerhalb der Grenzen', () => {
    expect(moveItem(['a', 'b', 'c'], 1, -1)).toEqual(['b', 'a', 'c']);
    expect(moveItem(['a', 'b', 'c'], 1, 1)).toEqual(['a', 'c', 'b']);
    expect(moveItem(['a', 'b'], 0, -1)).toEqual(['a', 'b']);
    expect(moveItem(['a', 'b'], 1, 1)).toEqual(['a', 'b']);
  });

  it('bereinigt Aktionen, deren Feld gelöscht wird', () => {
    const actions: FormAction[] = [
      { type: 'create_absence', kind: 'beurlaubung', student: 'kind', range: 'zeit', periods: 'std', reason: 'grund' },
      { type: 'calendar_entry', title: 'T', date: 'tag' },
      { type: 'inform_teachers' },
    ];
    const withoutReason = dropFieldRefs(actions, 'grund');
    expect(withoutReason[0]?.reason).toBeNull();
    expect(withoutReason).toHaveLength(3);
    const withoutRange = dropFieldRefs(actions, 'zeit');
    expect(withoutRange.map((a) => a.type)).toEqual(['calendar_entry', 'inform_teachers']); // Aktion ohne Zeitraum entfällt
    expect(dropFieldRefs(actions, 'tag').map((a) => a.type)).toEqual(['create_absence', 'inform_teachers']);
  });
});

describe('Formular-Baukasten – Antworten', () => {
  const d = defn(FIELDS);

  it('bereitet leere Antworten je Feldart vor', () => {
    const a = initialAnswers(d);
    expect(a.zeit).toEqual({ from: '', to: '' });
    expect(a.ok).toBe(false);
    expect(a.sig).toEqual({ name: '' });
    expect(a.grund).toBe('');
  });

  it('meldet fehlende Pflichtangaben vor dem Absenden', () => {
    const e = answerErrors(d, initialAnswers(d), null, true);
    expect(Object.keys(e).sort()).toEqual(['grund', 'kind', 'ok', 'sig', 'zeit']);
    expect(e.ok).toBe('Bitte bestätigen.');
    expect(e.sig).toContain('unterschreiben');
  });

  it('akzeptiert vollständige Antworten und prüft Zahl und Zeitraum', () => {
    const a = { ...initialAnswers(d), zeit: { from: '2030-01-07', to: '2030-01-08' }, grund: 'Arzt', ok: true, sig: { name: 'Erika Muster' } };
    expect(answerErrors(d, a, 'S1', true)).toEqual({});
    expect(answerErrors(d, { ...a, zahl: '9' }, 'S1', true).zahl).toContain('Erlaubt');
    expect(answerErrors(d, { ...a, zahl: 'x' }, 'S1', true).zahl).toContain('Zahl');
    expect(answerErrors(d, { ...a, zahl: '2,5' }, 'S1', true).zahl).toBeUndefined();
    expect(answerErrors(d, { ...a, zeit: { from: '2030-01-09', to: '2030-01-08' } }, 'S1', true).zeit).toContain('vor dem Beginn');
  });

  it('verlangt die Kind-Auswahl auch ohne Feld „Schüler/in“', () => {
    const plain = defn([{ id: 'a', type: 'text', label: 'A' }]);
    expect(answerErrors(plain, { a: '' }, null, true).__student).toBeTruthy();
    expect(answerErrors(plain, { a: '' }, 'S1', true)).toEqual({});
    expect(answerErrors(plain, { a: '' }, null, false)).toEqual({});
  });
});

describe('Formular-Baukasten – Vorlage', () => {
  it('blockiert das Veröffentlichen mit verständlichem Grund', () => {
    expect(publishBlocker(defn([]), 'Titel')).toContain('Feld');
    expect(publishBlocker(defn([{ id: 'a', type: 'text', label: 'A' }]), ' ')).toContain('Titel');
    expect(publishBlocker(defn([{ id: 'a', type: 'text', label: '' }]), 'T')).toContain('Beschriftung');
    expect(publishBlocker(defn([{ id: 'a', type: 'select', label: 'S', options: [' '] }]), 'T')).toContain('Möglichkeit');
    const noRoles = defn([{ id: 'a', type: 'text', label: 'A' }], { audience: { roles: [], scope: 'all', classes: [], grades: [] } });
    expect(publishBlocker(noRoles, 'T')).toContain('ausfüllen');
    expect(publishBlocker(defn([{ id: 'a', type: 'text', label: 'A' }]), 'T')).toBeNull();
  });

  it('beschreibt Ablauf und Zielgruppe in Worten', () => {
    const labels = { class_teacher: 'Klassenleitung des Kindes', schulleitung: 'Schulleitung' };
    expect(workflowText([{ approver: 'class_teacher' }, { approver: 'schulleitung' }], false, labels)).toBe('Klassenleitung des Kindes → Schulleitung');
    expect(workflowText([], true, labels)).toBe('Sofort erledigt');
    expect(workflowText([], false, labels)).toContain('Eingang');
    const d = defn([], { audience: { roles: ['eltern', 'schueler_adult'], scope: 'grades', classes: [], grades: [9, 10] } });
    expect(audienceText(d, { eltern: 'Eltern', schueler_adult: 'Volljährige' })).toBe('Eltern, Volljährige · Jahrgänge 9, 10');
  });

  it('erkennt offene Einreichungen', () => {
    expect(isOpen({ status: 'eingereicht' })).toBe(true);
    expect(isOpen({ status: 'in_pruefung' })).toBe(true);
    expect(isOpen({ status: 'genehmigt' })).toBe(false);
  });
});

describe('Formular-Baukasten – Adressen', () => {
  it('baut Download-Adressen mit Parametern', () => {
    expect(formsApi.blankPdfUrl(3)).toBe('/api/v1/forms/templates/3/blank.pdf');
    expect(formsApi.submissionPdfUrl(7)).toBe('/api/v1/forms/submissions/7/pdf');
    expect(formsApi.exportCsvUrl(3)).toBe('/api/v1/forms/export.csv?template_id=3');
    expect(formsApi.exportCsvUrl(3, 'genehmigt')).toBe('/api/v1/forms/export.csv?template_id=3&status=genehmigt');
    expect(formsApi.legacyPdfUrl('leave-form', 'S1')).toBe('/api/v1/student-absences/leave-form.pdf?student_id=S1');
    expect(formsApi.legacyPdfUrl('excuse-form')).toBe('/api/v1/student-absences/form.pdf');
  });
});
