import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { StatusBadge } from './components';
import { PreviewView } from './dialogs';
import { StudentsTab, TeachersTab } from './PeopleTabs';
import {
  absencePeriodsText,
  absenceTitle,
  blockPeriods,
  canMarkCell,
  cellBadges,
  classBody,
  countsText,
  coursePeriods,
  describeChanges,
  escortsOf,
  filterClasses,
  filterStudents,
  groupByGrade,
  groupSubjects,
  inWeek,
  isoWeekNumber,
  lessonBody,
  makeNames,
  mergeCells,
  movedFrom,
  parseNote,
  partnerClasses,
  previewStats,
  previewStatsText,
  rangeError,
  roomHints,
  rowCount,
  shiftWeek,
  slotsByPeriod,
  slotText,
  sortAbsences,
  sortTeachers,
  teacherHint,
  weekDates,
  weekTitle,
} from './logic';
import type { ClassDetail, ClassListItem, ClassSubject, ClassWeek, PreviewChange, WeekAbsence, WeekCell } from './types';
import { WeekGrid, WeekList, type BlockCtx } from './WeekTab';

const cell = (over: Partial<WeekCell>): WeekCell => ({
  period: 0,
  subject: 'M',
  teacher: 'MUE',
  room: 'R101',
  classes: ['5a'],
  status: 'normal',
  note: '',
  lesson_id: 'L1',
  part: 0,
  kind: 'unterricht',
  course_id: 'C-M',
  original_teacher: null,
  original_room: null,
  entry_id: null,
  exam: null,
  ...over,
});

const cls = (id: string, grade: number, over: Partial<ClassListItem> = {}): ClassListItem => ({
  id,
  name: id,
  grade,
  site: 'H',
  site_name: 'Hauptgebäude',
  home_room: null,
  class_teacher: null,
  student_count: 25,
  course_count: 10,
  teacher_count: 8,
  ...over,
});

const change = (over: Partial<PreviewChange>): PreviewChange => ({
  kind: 'entfall',
  classes: ['5a'],
  period: 0,
  subject: 'M',
  teacher: 'MUE',
  substitute: null,
  room: null,
  note: '',
  ...over,
});

const names = makeNames({
  subjects: new Map([
    ['M', 'Mathe'],
    ['D', 'Deutsch'],
    ['E', 'Englisch'],
  ]),
  teachers: new Map([
    ['MUE', 'Frau Müller'],
    ['SCH', 'Herr Schmidt'],
  ]),
  rooms: new Map([['R101', 'Raum 101']]),
});

describe('Kalenderwoche', () => {
  it('ISO-Kalenderwoche auch an Jahresgrenzen', () => {
    expect(isoWeekNumber('2026-10-05')).toBe(41);
    expect(isoWeekNumber('2026-10-10')).toBe(41);
    expect(isoWeekNumber('2026-10-11')).toBe(41);
    expect(isoWeekNumber('2026-10-12')).toBe(42);
    expect(isoWeekNumber('2021-01-01')).toBe(53);
    expect(isoWeekNumber('2024-12-30')).toBe(1);
    expect(isoWeekNumber('2026-01-01')).toBe(1);
    expect(isoWeekNumber('2027-01-04')).toBe(1);
    expect(isoWeekNumber('2026-12-28')).toBe(53);
  });

  it('Wochen blättern, Tage, Titel', () => {
    expect(shiftWeek('2026-10-08', 0)).toBe('2026-10-05');
    expect(shiftWeek('2026-10-08', 1)).toBe('2026-10-12');
    expect(shiftWeek('2026-10-05', -1)).toBe('2026-09-28');
    expect(shiftWeek('2026-12-31', 1)).toBe('2027-01-04');
    expect(weekDates('2026-10-05', 5)).toEqual(['2026-10-05', '2026-10-06', '2026-10-07', '2026-10-08', '2026-10-09']);
    expect(inWeek('2026-10-05', '2026-10-11')).toBe(true);
    expect(inWeek('2026-10-05', '2026-10-12')).toBe(false);
    const t = weekTitle('2026-10-07', 5);
    expect(t.kw).toBe(41);
    expect(t.range).toBe('05.10.–09.10.2026');
    expect(t.label).toBe('KW 41 · 05.10.–09.10.2026');
    // R3: Text des Servers, Zeitraum Mo–So hinter der KW (§15.5)
    expect(weekTitle('2026-10-07', 7, 'Woche 6 · KW 41').label).toBe('Woche 6 · KW 41 · 05.10.–11.10.2026');
  });
});

describe('Klassenliste', () => {
  const list = [
    cls('10a', 10),
    cls('5b', 5, { class_teacher: { id: 'MUE', name: 'Frau Müller' } }),
    cls('5a', 5, { home_room: { id: 'R101', name: 'Raum 101' } }),
    cls('Q1', 0, { site: 'N', site_name: 'Nebenstelle' }),
  ];

  it('Suche über Name, Klassenleitung und Raum; Standortfilter', () => {
    expect(filterClasses(list, 'müller').map((c) => c.id)).toEqual(['5b']);
    expect(filterClasses(list, '101').map((c) => c.id)).toEqual(['5a']);
    expect(filterClasses(list, '', 'N').map((c) => c.id)).toEqual(['Q1']);
    expect(filterClasses(list, '').length).toBe(4);
  });

  it('nach Jahrgang gruppiert, natürlich sortiert, ohne Jahrgang zuletzt', () => {
    const g = groupByGrade(list);
    expect(g.map((x) => x.label)).toEqual(['Klassenstufe 5', 'Klassenstufe 10', 'Ohne Klassenstufe']);
    expect(g[0]?.classes.map((c) => c.id)).toEqual(['5a', '5b']);
    expect(countsText({ student_count: 1, course_count: 12, teacher_count: 1 })).toBe('1 Schüler/in · 12 Kurse · 1 Lehrkraft');
  });
});

describe('Wochenplan: Status und Zusammenführen', () => {
  it('Text-Badges je Änderung', () => {
    expect(cellBadges(cell({}))).toEqual([]);
    expect(cellBadges(cell({ kind: 'vertretung', status: 'geaendert', teacher: 'SCH', original_teacher: 'MUE' }))).toEqual(['vertretung']);
    expect(cellBadges(cell({ kind: 'entfall', status: 'entfall' }))).toEqual(['entfall']);
    expect(cellBadges(cell({ kind: 'verlegung', status: 'entfall', note: 'verlegt in die 5. Stunde' }))).toEqual(['verlegt']);
    expect(cellBadges(cell({ kind: 'verlegung', status: 'neu' }))).toEqual(['verlegt']);
    expect(cellBadges(cell({ kind: 'raumaenderung', status: 'geaendert', room: 'R2', original_room: 'R101' }))).toEqual(['raum']);
    expect(cellBadges(cell({ kind: 'klasse_abwesend', status: 'entfall' }))).toEqual(['klasse_abwesend']);
    expect(cellBadges(cell({ exam: 'Klassenarbeit 1' }))).toEqual(['klausur']);
    expect(cellBadges(cell({ kind: 'vertretung', status: 'geaendert', teacher: 'SCH', original_teacher: 'MUE', room: 'R2', original_room: 'R101' }))).toEqual([
      'vertretung',
      'raum',
    ]);
    expect(cellBadges(cell({ status: 'geaendert', kind: 'irgendwas' }))).toEqual(['geaendert']);
  });

  it('nur stattfindender Unterricht eines Kurses ist markierbar', () => {
    expect(canMarkCell(cell({}))).toBe(true);
    expect(canMarkCell(cell({ kind: 'vertretung', status: 'geaendert' }))).toBe(true);
    expect(canMarkCell(cell({ kind: 'entfall', status: 'entfall' }))).toBe(false);
    expect(canMarkCell(cell({ kind: 'verlegung', status: 'neu' }))).toBe(false);
    expect(canMarkCell(cell({ course_id: null }))).toBe(false);
  });

  it('gekoppelte Kursteile werden zu einem Block, Entfall nach hinten', () => {
    const cells = [
      cell({ period: 1, lesson_id: 'L2', course_id: 'C-REL', subject: 'ER', part: 1, teacher: 'SCH' }),
      cell({ period: 1, lesson_id: 'L2', course_id: 'C-REL', subject: 'KR', part: 0, teacher: 'MUE', kind: 'vertretung', status: 'geaendert', original_teacher: 'X' }),
      cell({ period: 2, lesson_id: 'L3', kind: 'entfall', status: 'entfall', note: 'Entfall – dafür D (Herr Schmidt) aus der 6. Stunde vorgezogen' }),
      cell({ period: 2, lesson_id: 'L9', subject: 'D', kind: 'verlegung', status: 'neu', course_id: 'C-D' }),
      cell({ period: 0 }),
    ];
    const items = mergeCells(cells);
    expect(items.map((i) => [i.period, i.lessonId, i.cells.length])).toEqual([
      [0, 'L1', 1],
      [1, 'L2', 2],
      [2, 'L9', 1],
      [2, 'L3', 1],
    ]);
    const rel = items[1];
    expect(rel?.coupled).toBe(true);
    expect(rel?.cells.map((c) => c.subject)).toEqual(['KR', 'ER']);
    expect(rel?.badges).toEqual(['vertretung']);
    expect(rel?.main).toBe('vertretung');
    expect(rel?.markable).toBe(true);
    expect(items[3]?.cancelled).toBe(true);
    expect(items[3]?.markable).toBe(false);
    const slots = slotsByPeriod(items, 4);
    expect(slots.map((s) => s.length)).toEqual([1, 1, 2, 0]);
    expect(slotText(items[0]!, names, '08:00–08:45')).toBe('1. Std. (08:00–08:45): Mathe, Lehrkraft Frau Müller, Raum Raum 101');
    expect(slotText(rel!, names)).toMatch(/^2\. Std\.: 2 Kursteile – KR, Lehrkraft Frau Müller statt X/);
  });

  it('„Unterricht entfällt“ wird erkannt, Zeilen bis zur letzten Stunde', () => {
    const [it1] = mergeCells([cell({ kind: 'entfall', status: 'entfall', note: 'Unterricht entfällt – Exkursion' })]);
    expect(it1?.dropped).toBe(true);
    expect(mergeCells([cell({ dropped: true, status: 'entfall', kind: 'entfall' })])[0]?.dropped).toBe(true);
    expect(rowCount([{ cells: [{ period: 5 }] }, { cells: [{ period: 2 }] }], 10)).toBe(6);
    expect(rowCount([{ cells: [] }], 8)).toBe(8);
  });

  it('Stunden des Kurses am Tag und Vorauswahl des Blocks', () => {
    const day = [
      cell({ period: 1, lesson_id: 'A', course_id: 'C-M' }),
      cell({ period: 2, lesson_id: 'A', course_id: 'C-M' }),
      cell({ period: 4, lesson_id: 'B', course_id: 'C-M' }),
      cell({ period: 5, lesson_id: 'C', course_id: 'C-M', kind: 'entfall', status: 'entfall' }),
      cell({ period: 3, lesson_id: 'D', course_id: 'C-D' }),
    ];
    expect(coursePeriods(day, 'C-M')).toEqual([1, 2, 4]);
    expect(blockPeriods(day, 'A', 2)).toEqual([1, 2]);
    expect(blockPeriods(day, null, 3)).toEqual([3]);
  });
});

describe('Vorschau-Texte', () => {
  it('Entfall + Verlegung in dieselbe Stunde → ein Satz', () => {
    const lines = describeChanges(
      [
        change({ kind: 'verlegung', period: 2, subject: 'D', teacher: 'SCH', note: 'D (Herr Schmidt) aus der 6. Stunde vorgezogen' }),
        change({ kind: 'entfall', period: 2, subject: 'M', note: 'Entfall – dafür D (Herr Schmidt) aus der 6. Stunde vorgezogen' }),
      ],
      names,
      '5a',
    );
    expect(lines.map((l) => l.text)).toEqual(['Mathe 3. Std. entfällt – dafür wird Deutsch aus der 6. Std. vorgezogen']);
  });

  it('nach hinten verlegt, Feld moved_from, ohne Partner', () => {
    expect(movedFrom({ moved_from: 0, note: '' })).toBe(0);
    expect(movedFrom({ note: 'M (X) aus der 2. Stunde nach hinten verlegt' })).toBe(1);
    expect(movedFrom({ note: '' })).toBeNull();
    const lines = describeChanges(
      [change({ kind: 'entfall', period: 4 }), change({ kind: 'verlegung', period: 4, subject: 'E', moved_from: 1 })],
      names,
      '5a',
    );
    expect(lines[0]?.text).toBe('Mathe 5. Std. entfällt – dafür wird Englisch aus der 2. Std. nach hinten verlegt');
    expect(describeChanges([change({ kind: 'verlegung', period: 1, subject: 'D', moved_from: 5 })], names, '5a')[0]?.text).toBe(
      'Deutsch wird aus der 6. Std. in die 2. Std. vorgezogen',
    );
  });

  it('andere Klassen, Vertretung, Betreuung, Notiz ohne Dopplung', () => {
    const lines = describeChanges(
      [
        change({ kind: 'vertretung', classes: ['7b'], period: 1, subject: 'E', teacher: 'SCH', substitute: 'MUE' }),
        change({ kind: 'betreuung', period: 3, substitute: null }),
        change({ kind: 'entfall', period: 5, note: 'Unterricht entfällt – Exkursion' }),
        change({ kind: 'entfall', period: 6, note: 'Unterricht entfällt' }),
        change({ kind: 'raumaenderung', period: 0, room: 'R101' }),
        change({ kind: 'klasse_abwesend', period: 7 }),
        change({ kind: 'mitbetreuung', period: 8, substitute: 'SCH' }),
      ],
      names,
      '5a',
    );
    expect(lines.map((l) => l.text)).toEqual([
      'Mathe 1. Std.: anderer Raum – Raum 101',
      '7b: Englisch 2. Std.: Vertretung durch Frau Müller (statt Herr Schmidt)',
      'Mathe 4. Std.: Betreuung noch offen',
      'Mathe 6. Std. entfällt (Exkursion)',
      'Mathe 7. Std. entfällt',
      'Mathe 8. Std.: Klasse nicht da',
      'Mathe 9. Std.: wird von Herr Schmidt mitbetreut',
    ]);
    expect(lines[1]?.kind).toBe('vertretung');
    expect(lines.every((l) => !l.warning)).toBe(true);
    expect(describeChanges([change({ kind: 'betreuung', warning: true })], names, '5a')[0]?.warning).toBe(true);
  });

  it('nicht gepaarte Entfall-Notiz „dafür …“ wird übernommen, entfernte Einträge markiert', () => {
    expect(describeChanges([change({ period: 2, note: 'Entfall – dafür D (Schmidt) aus der 6. Stunde vorgezogen' })], names, '5a')[0]?.text).toBe(
      'Mathe 3. Std. entfällt – dafür D (Schmidt) aus der 6. Stunde vorgezogen',
    );
    expect(describeChanges([change({ kind: 'vertretung', substitute: 'SCH', op: 'removed' })], names, '5a')[0]?.text).toBe(
      'wieder wie geplant: Mathe 1. Std.: Vertretung durch Herrn Schmidt (statt Frau Müller)',
    );
  });

  it('Notizen der Engine für entfallenden Unterricht (§10.1)', () => {
    expect(parseNote('Unterricht entfällt (Exkursion) – Unterricht endet früher')).toEqual({ dropped: true, reason: 'Exkursion', rest: 'Unterricht endet früher' });
    expect(parseNote('Entfall – dafür D (MUE) aus der 6. Stunde vorgezogen')).toEqual({ dropped: false, reason: '', rest: 'dafür D (MUE) aus der 6. Stunde vorgezogen' });
    expect(parseNote('Unterricht entfällt')).toEqual({ dropped: true, reason: '', rest: '' });
    expect(parseNote('Vertretung für Frau Müller')).toEqual({ dropped: false, reason: '', rest: 'Vertretung für Frau Müller' });
    const lines = describeChanges(
      [
        change({ kind: 'entfall', period: 2, note: 'Unterricht entfällt (Exkursion) – dafür D (MUE) aus der 6. Stunde vorgezogen', dropped: true }),
        change({ kind: 'verlegung', period: 2, subject: 'D', note: 'D (Frau Müller) aus der 6. Stunde vorgezogen' }),
        change({ kind: 'betreuung', period: 1, substitute: 'SCH', note: 'Unterricht entfällt (Projekttag) – Betreuung (fachfremd)' }),
        change({ kind: 'entfall', period: 5, note: 'Unterricht entfällt (Exkursion) – Unterricht endet früher' }),
        change({ kind: 'vertretung', period: 4, substitute: 'SCH', dropped: true, note: 'Unterricht entfällt – Vertretung' }),
      ],
      names,
      '5a',
    );
    expect(lines.map((l) => l.text)).toEqual([
      'Mathe 2. Std. entfällt (Projekttag) – Betreuung durch Herrn Schmidt',
      'Mathe 3. Std. entfällt (Exkursion) – dafür wird Deutsch aus der 6. Std. vorgezogen',
      'Mathe 5. Std. entfällt – Vertretung durch Herrn Schmidt',
      'Mathe 6. Std. entfällt (Exkursion – Unterricht endet früher)',
    ]);
  });

  it('Kennzahlen der Vorschau', () => {
    const s = previewStats(
      [
        { date: '2026-10-05', changes: [change({}), change({ classes: ['7b', '7a'] })] },
        { date: '2026-10-06', changes: [] },
        { date: '2026-10-07', changes: [change({ classes: ['10a'] })] },
      ],
      '5a',
    );
    expect(s).toEqual({ changes: 3, days: 2, otherClasses: ['7a', '7b', '10a'] });
    expect(previewStatsText(s)).toBe('3 Änderungen an 2 Tagen · auch betroffen: 7a, 7b, 10a');
    expect(previewStatsText({ changes: 1, days: 1, otherClasses: [] })).toBe('1 Änderung an 1 Tag');
    expect(previewStatsText({ changes: 0, days: 0, otherClasses: [] })).toBe('Keine Änderungen am Vertretungsplan.');
  });
});

describe('Dialoge und Ausfälle', () => {
  it('Zeitraum prüfen (höchstens 14 Tage)', () => {
    expect(rangeError('2026-10-05', '2026-10-05')).toBeNull();
    expect(rangeError('2026-10-05', '2026-10-18')).toBeNull();
    expect(rangeError('2026-10-05', '2026-10-19')).toMatch(/Höchstens 14 Tage/);
    expect(rangeError('2026-10-05', '2026-10-04')).toMatch(/vor dem Startdatum/);
    expect(rangeError('', '2026-10-04')).toMatch(/Startdatum/);
  });

  it('Anfragekörper nach Vertrag', () => {
    expect(lessonBody({ date: '2026-10-05', periods: [3, 2, 3], courseId: 'C-M', part: null, reason: ' Exkursion ' }, true)).toEqual({
      mode: 'lesson',
      date_from: '2026-10-05',
      date_to: '2026-10-05',
      periods: [2, 3],
      course_id: 'C-M',
      part: null,
      reason: 'Exkursion',
      dry_run: true,
    });
    expect(classBody({ from: '2026-10-06', to: '2026-10-05', periods: [], reason: 'Wandertag', escorts: ['MUE', 'MUE', 'SCH'] }, false)).toEqual({
      mode: 'class',
      date_from: '2026-10-06',
      date_to: '2026-10-06',
      periods: [],
      reason: 'Wandertag',
      escort_teachers: ['MUE', 'SCH'],
      dry_run: false,
    });
  });

  const abs = (over: Partial<WeekAbsence>): WeekAbsence => ({
    id: 'A1',
    kind: 'class',
    ref: '5a',
    ref_name: '5a',
    date_from: '2026-10-05',
    date_to: '2026-10-05',
    periods: [],
    reason: 'Wandertag',
    can_delete: true,
    ...over,
  });

  it('Titel, Stunden, Begleitungen, Sortierung', () => {
    expect(absenceTitle(abs({ kind: 'lesson', ref: 'C-M', ref_name: 'Mathematik 5a' }))).toBe('Unterricht entfällt: Mathematik 5a');
    expect(absenceTitle(abs({}), '5a')).toBe('Klasse 5a ist nicht da');
    expect(absenceTitle(abs({ kind: 'teacher', ref: 'MUE', ref_name: '', reason: 'krank' }))).toBe('Lehrkraft abwesend: MUE');
    expect(absenceTitle(abs({ kind: 'teacher', ref: 'MUE', ref_name: 'Frau Müller', reason: 'Begleitung 5a' }))).toBe('Begleitung: Frau Müller');
    expect(absencePeriodsText(abs({ kind: 'lesson', periods: [] }))).toBe('alle Stunden des Kurses');
    expect(absencePeriodsText(abs({ periods: [3, 1] }))).toBe('2., 4. Std.');
    const classAbs = abs({});
    const escort = abs({ id: 'A2', kind: 'teacher', ref: 'MUE', reason: 'Begleitung 5a' });
    const other = abs({ id: 'A3', kind: 'teacher', ref: 'SCH', reason: 'Begleitung 5ab' });
    const hyphen = abs({ id: 'A5', kind: 'teacher', ref: 'SCH', reason: 'Begleitung 5a-Fahrt' });
    const otherDay = abs({ id: 'A4', kind: 'teacher', ref: 'SCH', reason: 'Begleitung 5a', date_to: '2026-10-06' });
    expect(escortsOf(classAbs, [classAbs, escort, other, otherDay, hyphen], '5a').map((a) => a.id)).toEqual(['A2']);
    expect(escortsOf(escort, [escort], '5a')).toEqual([]);
    const sorted = sortAbsences([
      abs({ id: 'x', kind: 'lesson', date_from: '2026-10-05', periods: [3] }),
      abs({ id: 'y', kind: 'class', date_from: '2026-10-05' }),
      abs({ id: 'z', kind: 'lesson', date_from: '2026-10-04', periods: [5] }),
    ]);
    expect(sorted.map((a) => a.id)).toEqual(['z', 'y', 'x']);
  });
});

describe('Kopf, Lehrkräfte, Schüler/innen', () => {
  it('Hinweise zu Raum und Klassenleitung', () => {
    const room = { id: 'R2', name: 'Raum 2', type: 'Fachraum', site: 'N', capacity: 20, home_of: ['5a', '6b'] };
    expect(roomHints(room, { id: '5a', site: 'H' }, 25)).toEqual([
      'ist schon Klassenraum von 6b',
      'liegt an einem anderen Standort',
      'nur 20 Plätze für 25 Schüler/innen',
      'Raumtyp „Fachraum“ – kein Klassenraum',
    ]);
    expect(roomHints({ ...room, type: 'Klassenraum', site: 'H', capacity: 30, home_of: ['5a'] }, { id: '5a', site: 'H' }, 25)).toEqual([]);
    expect(roomHints(undefined, { id: '5a', site: 'H' }, 25)).toEqual([]);
    expect(teacherHint('MUE', [{ id: 'MUE' }])).toBeNull();
    expect(teacherHint('SCH', [{ id: 'MUE' }])).toBe('unterrichtet die Klasse bisher nicht');
    expect(teacherHint(null, [])).toBeNull();
  });

  it('Lehrkräfte sortiert, Fächer gruppiert, Kopplung, Schülersuche', () => {
    expect(
      sortTeachers([
        { name: 'Zander', is_class_teacher: false },
        { name: 'Albers', is_class_teacher: false },
        { name: 'Müller', is_class_teacher: true },
      ]).map((t) => t.name),
    ).toEqual(['Müller', 'Albers', 'Zander']);
    const row = (over: Partial<ClassSubject>): ClassSubject => ({
      course_id: 'C',
      part: null,
      label: 'M 5a',
      subject: 'M',
      subject_name: 'Mathematik',
      teacher: null,
      hours: 4,
      classes: ['5a'],
      coupled: false,
      ...over,
    });
    const groups = groupSubjects([
      row({ subject: 'REL', subject_name: 'Religion', label: 'Religion kath.', part: 1, classes: ['5a', '5b'], coupled: true }),
      row({}),
      row({ subject: 'REL', subject_name: 'Religion', label: 'Ethik', part: 2, classes: ['5a', '5b'], coupled: true }),
    ]);
    expect(groups.map((g) => g.name)).toEqual(['Mathematik', 'Religion']);
    expect(groups[1]?.rows.map((r) => r.label)).toEqual(['Ethik', 'Religion kath.']);
    expect(partnerClasses({ classes: ['5a', '5b'] }, '5a')).toEqual(['5b']);
    const students = [
      { id: 'S2', name: 'Zoe Berg', courses: [{ course_id: 'C', part: 1, label: 'Ethik' }] },
      { id: 'S1', name: 'Anna Adler', courses: [] },
    ];
    expect(filterStudents(students, '').map((s) => s.id)).toEqual(['S1', 'S2']);
    expect(filterStudents(students, 'ethik').map((s) => s.id)).toEqual(['S2']);
  });
});

describe('Darstellung (statisches Markup)', () => {
  const week: ClassWeek = {
    class_id: '5a',
    week_start: '2026-10-05',
    periods: 8,
    period_times: ['08:00–08:45', '08:50–09:35', '09:55–10:40'],
    days: [
      {
        date: '2026-10-05',
        weekday: 0,
        holiday: null,
        cells: [
          cell({ period: 0 }),
          cell({ period: 1, lesson_id: 'L2', course_id: 'C-REL', subject: 'KR', part: 0 }),
          cell({ period: 1, lesson_id: 'L2', course_id: 'C-REL', subject: 'ER', part: 1, teacher: 'SCH' }),
          cell({ period: 2, lesson_id: 'L3', kind: 'entfall', status: 'entfall', note: 'Unterricht entfällt' }),
        ],
      },
      { date: '2026-10-06', weekday: 1, holiday: 'Herbstferien', cells: [] },
    ],
    absences: [],
    can_plan: true,
  };
  const items = week.days.map((d) => mergeCells(d.cells));
  const slots = items.map((x) => slotsByPeriod(x, 3));
  const ctx = (pick: boolean): BlockCtx => ({
    names,
    colorOf: () => '#336699',
    partLabel: (courseId, part) => (courseId === 'C-REL' ? (part === 0 ? 'kath. Religion' : 'ev. Religion') : ''),
    times: week.period_times,
    onPick: pick ? () => undefined : undefined,
  });

  it('Raster: Tage mit Datum, Kopplung in einem Block, Ferien, Text-Badge, Klick nur mit can_plan', () => {
    const html = renderToStaticMarkup(createElement(WeekGrid, { week, slots, rows: 3, breaks: new Set([1]), blocked: () => null, ctx: ctx(true), caption: 'Plan' }));
    expect(html).toContain('tt-grid');
    expect(html).not.toContain('<table');
    expect(html).toContain('05.10.');
    expect(html).toContain('08:50–09:35');
    expect(html).toContain('Herbstferien');
    expect(html).toContain('tt-day-fill');
    expect(html).toContain('kath. Religion:');
    expect(html).toContain('ev. Religion:');
    expect(html.match(/kl-item-title/g)?.length).toBe(3);
    expect(html).toContain('>Entfall<');
    expect(html.match(/<button/g)?.length).toBe(2);
    const readOnly = renderToStaticMarkup(createElement(WeekGrid, { week, slots, rows: 3, breaks: new Set<number>(), blocked: () => null, ctx: ctx(false), caption: 'Plan' }));
    expect(readOnly).not.toContain('<button');
  });

  it('Liste je Tag ohne Tabelle (Handy)', () => {
    const html = renderToStaticMarkup(createElement(WeekList, { week, slots, ctx: ctx(false) }));
    expect(html).not.toContain('<table');
    expect(html).toContain('Montag, 5. Oktober 2026');
    expect(html).toContain('Ferien:</strong> Herbstferien');
  });

  it('Badge mit Text, Vorschau mit Sätzen', () => {
    expect(renderToStaticMarkup(createElement(StatusBadge, { status: 'verlegt' }))).toContain('Verlegt');
    const html = renderToStaticMarkup(
      createElement(PreviewView, {
        result: {
          summary: 'Mathe fällt aus.',
          preview: [
            {
              date: '2026-10-05',
              changes: [
                change({ kind: 'entfall', period: 2, subject: 'M' }),
                change({ kind: 'verlegung', period: 2, subject: 'D', moved_from: 5 }),
              ],
            },
          ],
        },
        names,
        ownClass: '5a',
      }),
    );
    expect(html).toContain('Mathe fällt aus.');
    expect(html).toContain('Mathe 3. Std. entfällt – dafür wird Deutsch aus der 6. Std. vorgezogen');
    // Kennzahlen nur, wenn der Server keine Zusammenfassung liefert
    expect(html).not.toContain('2 Änderungen an 1 Tag');
    const own = renderToStaticMarkup(
      createElement(PreviewView, {
        result: { summary: '', preview: [{ date: '2026-10-05', changes: [change({}), change({ period: 1 })], warnings: ['Keine Vertretung für 7b'] }] },
        names,
        ownClass: '5a',
      }),
    );
    expect(own).toContain('2 Änderungen an 1 Tag');
    expect(own).toContain('Keine Vertretung für 7b');
  });
});

describe('Reiter Lehrkräfte und Schüler/innen (statisches Markup)', () => {
  const detail: ClassDetail = {
    class: {
      id: '5a',
      name: '5a',
      grade: 5,
      site: 'H',
      site_name: 'Hauptgebäude',
      max_periods_per_day: 7,
      unavailable: [],
      home_room: { id: 'R101', name: 'Raum 101', type: 'Klassenraum', capacity: 30, site: 'H' },
      class_teacher: { id: 'MUE', name: 'Frau Müller' },
    },
    subjects: [
      { course_id: 'C-M', part: null, label: 'Mathematik 5a', subject: 'M', subject_name: 'Mathematik', teacher: { id: 'MUE', name: 'Frau Müller' }, hours: 4, classes: ['5a'], coupled: false },
      { course_id: 'C-REL', part: 1, label: 'Ethik', subject: 'ETH', subject_name: 'Ethik', teacher: { id: 'SCH', name: 'Herr Schmidt' }, hours: 2, classes: ['5a', '5b'], coupled: true },
    ],
    teachers: [
      { id: 'SCH', name: 'Herr Schmidt', is_class_teacher: false, subjects: ['ETH'], hours: 2 },
      { id: 'MUE', name: 'Frau Müller', is_class_teacher: true, subjects: ['M'], hours: 4 },
    ],
    students: [{ id: 'S1', name: 'Anna Adler', courses: [{ course_id: 'C-REL', part: 1, label: 'Ethik' }] }],
    student_count: 1,
    can_edit: false,
    can_plan: false,
  };

  it('Fach → Kurs → Lehrkraft, Klassenleitung markiert, Kopplung genannt', () => {
    const html = renderToStaticMarkup(createElement(MemoryRouter, null, createElement(TeachersTab, { detail, names })));
    expect(html).toContain('Mathematik');
    expect(html).toContain('gekoppelt mit 5b');
    expect(html).toContain('Klassenleitung');
    expect(html.indexOf('Frau Müller')).toBeLessThan(html.lastIndexOf('Herr Schmidt'));
    expect(html).toContain('/stundenplan/teacher/SCH');
  });

  it('Schülerliste mit Kurswahl, ohne Recht ein Hinweis', () => {
    const html = renderToStaticMarkup(createElement(MemoryRouter, null, createElement(StudentsTab, { detail })));
    expect(html).toContain('Anna Adler');
    expect(html).toContain('Ethik');
    expect(renderToStaticMarkup(createElement(MemoryRouter, null, createElement(StudentsTab, { detail: { ...detail, students: null } })))).toContain('nicht freigegeben');
  });
});

describe('accusative', () => {
  it('setzt „Herrn“ nach „durch“', async () => {
    const { accusative } = await import('./logic');
    expect(accusative('Herr Sommer')).toBe('Herrn Sommer');
    expect(accusative('Frau Ludwig')).toBe('Frau Ludwig');
    expect(accusative('LUD')).toBe('LUD');
  });
});
