import { describe, expect, it } from 'vitest';
import {
  addGroup,
  addLeaf,
  cellText,
  csvField,
  csvFileName,
  daysLeft,
  emptyTree,
  filterStudents,
  isoToLocal,
  leafCount,
  localToIso,
  newLeaf,
  noFilter,
  removeAt,
  replaceLeaf,
  setOp,
  toCsv,
  trashContent,
  treeProblem,
  type ProgressTable,
  type TableStudent,
  type TrashEntry,
} from './progress';

const student = (name: string, cls: string, cells: Record<string, boolean | null>, extra: Partial<TableStudent> = {}): TableStudent => {
  const vals = Object.values(cells).filter((v) => v !== null);
  const done = vals.filter(Boolean).length;
  return { student_id: name, user_id: 1, name, class_id: cls, has_account: true, cells, done, total: vals.length, percent: vals.length ? Math.round((done * 100) / vals.length) : 0, ...extra };
};

const table: ProgressTable = {
  elements: [
    { element_type: 'item', element_id: 1, key: 'item:1', title: 'Lesen', kind_label: 'Textseite', folder_id: null, mode: 'manual', mode_label: 'Selbst abhaken', done: 1, of: 3, restricted: false },
    { element_type: 'item', element_id: 2, key: 'item:2', title: '=Aufgabe;1', kind_label: 'Aufgabe', folder_id: null, mode: 'submitted', mode_label: 'Abgegeben', done: 1, of: 3, restricted: false },
  ],
  students: [
    student('Anna Alt', '5a', { 'item:1': true, 'item:2': true }),
    student('Ben Bunt', '5a', { 'item:1': false, 'item:2': true }),
    student('Cem Test', '5b', { 'item:1': false, 'item:2': false }),
  ],
  classes: ['5a', '5b'],
  progress_parents: false,
  generated_at: '2026-10-13T08:00:00Z',
};

describe('Bedingungsbaum bearbeiten', () => {
  it('fügt Bedingungen und Untergruppen hinzu, ohne das Original zu ändern', () => {
    const root = emptyTree();
    const a = addLeaf(root, [], newLeaf('completed', { element_type: 'item', element_id: 5 }));
    const b = addGroup(a, []);
    const c = addLeaf(b, [1], { type: 'release' });
    expect(root.items).toHaveLength(0);
    expect(leafCount(c)).toBe(2);
    expect(c.items[1]).toEqual({ op: 'or', items: [{ type: 'release' }] });
  });

  it('ändert Verknüpfung, ersetzt und entfernt Blätter', () => {
    let t = addLeaf(emptyTree(), [], newLeaf('score', { element_type: 'item', element_id: 2 }));
    t = setOp(t, [], 'or');
    expect(t.op).toBe('or');
    t = replaceLeaf(t, [0], { type: 'score', element_type: 'item', element_id: 2, min_percent: 80 });
    expect(t.items[0]).toMatchObject({ min_percent: 80 });
    t = removeAt(t, [0]);
    expect(t.items).toEqual([]);
  });

  it('meldet unvollständige Bedingungen', () => {
    expect(treeProblem(emptyTree())).toBeNull();
    expect(treeProblem(addLeaf(emptyTree(), [], newLeaf('completed')))).toMatch(/Element/);
    expect(treeProblem(addLeaf(emptyTree(), [], newLeaf('group')))).toMatch(/Gruppe/);
    expect(treeProblem(addLeaf(emptyTree(), [], newLeaf('date')))).toMatch(/Datum/);
    expect(treeProblem(addLeaf(emptyTree(), [], { type: 'score', element_type: 'item', element_id: 1, min_percent: 120 }))).toMatch(/Prozent/);
    expect(treeProblem(addLeaf(emptyTree(), [], { type: 'note', element_type: 'item', element_id: 1, max_note: 7 }))).toMatch(/Noten/);
    const nested = addLeaf(addGroup(emptyTree(), []), [0], newLeaf('group'));
    expect(treeProblem(nested)).toMatch(/Gruppe/);
    expect(treeProblem(addLeaf(emptyTree(), [], { type: 'release' }))).toBeNull();
  });

  it('wandelt lokale Zeit und ISO ineinander um', () => {
    expect(localToIso('')).toBeNull();
    expect(localToIso('kaputt')).toBeNull();
    const iso = localToIso('2026-10-14T08:30');
    expect(iso).toMatch(/Z$/);
    expect(isoToLocal(iso)).toBe('2026-10-14T08:30');
    expect(isoToLocal('2026-10-14T06:30:00')).toMatch(/^2026-10-14T/);
    expect(isoToLocal(null)).toBe('');
  });
});

describe('Fortschrittstabelle', () => {
  it('filtert nach Name, Klasse und offenen Elementen', () => {
    expect(filterStudents(table.students, noFilter)).toHaveLength(3);
    expect(filterStudents(table.students, { ...noFilter, q: ' ben ' }).map((s) => s.name)).toEqual(['Ben Bunt']);
    expect(filterStudents(table.students, { ...noFilter, classId: '5b' }).map((s) => s.name)).toEqual(['Cem Test']);
    expect(filterStudents(table.students, { ...noFilter, onlyOpen: true }).map((s) => s.name)).toEqual(['Ben Bunt', 'Cem Test']);
    expect(filterStudents(table.students, { ...noFilter, openKey: 'item:1' }).map((s) => s.name)).toEqual(['Ben Bunt', 'Cem Test']);
    expect(filterStudents(table.students, { ...noFilter, openKey: 'item:2', classId: '5a' })).toEqual([]);
  });

  it('nicht einsehbare Zellen zählen weder als offen noch als erledigt', () => {
    const s = student('Dora', '5a', { 'item:1': null, 'item:2': true }, { has_account: false });
    expect(filterStudents([s], { ...noFilter, openKey: 'item:1' })).toEqual([]);
    expect(cellText(null)).toBe('');
    expect(cellText(true)).toBe('erledigt');
    expect(cellText(false)).toBe('offen');
  });
});

describe('CSV', () => {
  it('schützt Zellen vor Formeln und maskiert Trennzeichen', () => {
    expect(csvField('Anna')).toBe('Anna');
    expect(csvField('=1+1')).toBe("'=1+1");
    expect(csvField('@SUMME')).toBe("'@SUMME");
    expect(csvField('-5')).toBe("'-5");
    expect(csvField('a;b')).toBe('"a;b"');
    expect(csvField('sagt "hi"')).toBe('"sagt ""hi"""');
    expect(csvField(42)).toBe('42');
  });

  it('exportiert die gefilterte Tabelle mit Kopfzeile und BOM', () => {
    const csv = toCsv(table, filterStudents(table.students, { ...noFilter, classId: '5a' }));
    const lines = csv.replace('﻿', '').trimEnd().split('\r\n');
    expect(csv.startsWith('﻿')).toBe(true);
    expect(lines[0]).toBe(`Name;Klasse;Lesen;"'=Aufgabe;1";Erledigt;Gesamt;Fortschritt %`);
    expect(lines).toHaveLength(3);
    expect(lines[1]).toBe('Anna Alt;5a;erledigt;erledigt;2;2;100');
    expect(lines[2]).toBe('Ben Bunt;5a;offen;erledigt;1;2;50');
  });

  it('bildet einen harmlosen Dateinamen', () => {
    expect(csvFileName('Mathe 7a – Gruppe/1', new Date('2026-10-13T10:00:00Z'))).toBe('fortschritt-Mathe-7a-Gruppe-1-2026-10-13.csv');
    expect(csvFileName('###', new Date('2026-10-13T10:00:00Z'))).toBe('fortschritt-kursraum-2026-10-13.csv');
  });
});

describe('Papierkorb', () => {
  const entry = (over: Partial<TrashEntry>): TrashEntry => ({
    group: 'g',
    kind: 'item',
    name: 'Blatt',
    type: 'file',
    type_label: 'Datei',
    folders: 0,
    items: 1,
    submissions: 0,
    deleted_at: '2026-10-13T08:00:00Z',
    deleted_by_name: '',
    purge_at: '2026-11-12T08:00:00Z',
    can_restore: true,
    ...over,
  });

  it('beschreibt den Inhalt', () => {
    expect(trashContent(entry({}))).toBe('');
    expect(trashContent(entry({ submissions: 1 }))).toBe('1 Abgabe');
    expect(trashContent(entry({ kind: 'folder', folders: 3, items: 4, submissions: 7 }))).toBe('2 Unterordner · 4 Materialien · 7 Abgaben');
    expect(trashContent(entry({ kind: 'folder', folders: 2, items: 1 }))).toBe('1 Unterordner · 1 Material');
  });

  it('zählt die Resttage', () => {
    const now = new Date('2026-10-13T08:00:00Z').getTime();
    expect(daysLeft('2026-11-12T08:00:00Z', now)).toBe(30);
    expect(daysLeft('2026-10-13T20:00:00Z', now)).toBe(1);
    expect(daysLeft('2026-10-01T08:00:00Z', now)).toBe(0);
    expect(daysLeft(null, now)).toBeNull();
    expect(daysLeft('kaputt', now)).toBeNull();
  });
});
