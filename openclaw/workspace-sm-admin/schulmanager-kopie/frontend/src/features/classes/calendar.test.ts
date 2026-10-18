import { describe, expect, it } from 'vitest';
import { calendarCells, dayChips, type CalendarDay } from './CalendarWeek';
import { newAttached, overlayExams, withEvents, withExamNotes, withHomework } from './calendarOverlay';
import type { WeekCell } from './types';

const cell = (period: number, over: Partial<WeekCell> = {}): WeekCell => ({
  period,
  subject: 'M',
  teacher: 'FIS',
  room: 'R1',
  classes: ['5a'],
  status: 'normal',
  note: '',
  lesson_id: 'L1',
  part: 0,
  kind: null,
  course_id: '5a-M',
  ...over,
});

const day = (cells: WeekCell[]): CalendarDay =>
  ({ date: '2026-10-12', weekday: 0, holiday: null, cells, weekday_name: 'Montag', weekend: false, events: [], exams: [], homework: [], duty: false }) as CalendarDay;

describe('calendarCells', () => {
  it('fasst Doppelstunden zu einem Block zusammen', () => {
    const out = calendarCells([day([cell(0), cell(1), cell(3, { lesson_id: 'L2', subject: 'D' })])], () => undefined);
    expect(out.map((c) => [c.subject, c.start, c.length])).toEqual([
      ['M', 0, 2],
      ['D', 3, 1],
    ]);
  });

  it('trennt, wenn nur eine Stunde der Doppelstunde vertreten wird', () => {
    const out = calendarCells([day([cell(0), cell(1, { teacher: 'SA2', status: 'vertretung', kind: 'vertretung' })])], () => 'Mathematik');
    expect(out).toHaveLength(2);
    expect(out[0].status).toBeUndefined();
    expect(out[1].status?.label).toBe('Vertretung');
    expect(out[1].teachers).toEqual(['SA2']);
    expect(out[1].subject_name).toBe('Mathematik');
  });
});

describe('dayChips', () => {
  const att = { ha: new Set<number>(), exam: new Set<string>(), absent: new Set<number>() };
  it('lässt in der Stunde hängende Prüfungen, HA und Abwesenheit aus dem Kopf weg', () => {
    const d = {
      ...day([]),
      events: [{ id: 'e1', title: 'Elternabend', kind: 'termin', kind_label: 'Termin', time_from: '19:00', time_to: '', location: '', note: '' }],
      exams: [{ id: 'x1', kind: 'klausur', kind_label: 'Klausur', title: 'Mathe', label: 'M', subject: 'M', start: 1, length: 2, time: '', room: null }],
      homework: [{ item_id: 7, channel_id: 1, channel_title: 'M', title: 'S. 5', due_at: '', time: '08:00', subject: 'M', subject_name: 'Mathe' }],
    } as unknown as CalendarDay;
    expect(dayChips(d, att, false).map((c) => c.key)).toEqual(['ee1', 'xx1', 'h7']);
    const rest = dayChips(d, { ha: new Set([7]), exam: new Set(['x1']), absent: new Set() }, false);
    expect(rest.map((c) => c.key)).toEqual(['ee1']);
  });
});

describe('Prüfungen und Hausaufgaben in den Stunden', () => {
  const exam = (over: Record<string, unknown> = {}) => ({
    id: 'k1', kind: 'klausur', kind_label: 'Klausur/Arbeit', title: 'Klausur 1', label: 'M15', subject: 'M', start: 2, length: 2, time: '', room: 'R5', course_id: '5a-M', classes: ['5a'], teachers: ['FIS'], ...over,
  });
  const plan = (): CalendarDay =>
    day([cell(2, { subject: 'D', lesson_id: 'LD', course_id: '5a-D', teacher: 'KOL' }), cell(3, { subject: 'D', lesson_id: 'LD', course_id: '5a-D', teacher: 'KOL' }), cell(4, { subject: 'E', lesson_id: 'LE', course_id: '5a-E' })]);
  const names = (s: string) => ({ M: 'Mathematik', D: 'Deutsch' })[s];

  it('zeigt eine Klausur als eigenen Block in ihren Stunden und verdrängt das Fach des Regelplans', () => {
    const d = { ...plan(), exams: [exam()] } as unknown as CalendarDay;
    const att = newAttached();
    const { cells, targets } = overlayExams(calendarCells([d], names), [d], 'student', names, att);
    const block = cells.find((c) => c.exam);
    expect(block).toMatchObject({ subject: 'M', start: 2, length: 2, rooms: ['R5'], teachers: ['FIS'] });
    expect(block?.status).toMatchObject({ label: 'Klausur', note: expect.stringContaining('statt Deutsch') });
    expect(cells.filter((c) => !c.exam).map((c) => c.subject)).toEqual(['E']);
    expect(targets.get('k1')).toBe(block);
    expect(att.exam.has('k1')).toBe(true);
  });

  it('schneidet eine nur teilweise überdeckte Stunde zurecht', () => {
    const d = { ...plan(), exams: [exam({ start: 3, length: 1 })] } as unknown as CalendarDay;
    const { cells } = overlayExams(calendarCells([d], names), [d], 'student', names, newAttached());
    expect(cells.map((c) => [c.subject, c.start, c.length]).sort()).toEqual([
      ['D', 2, 1],
      ['E', 4, 1],
      ['M', 3, 1],
    ]);
  });

  it('hängt einen Test als Zeichen an die Stunde des Fachs, sonst Block', () => {
    const d = { ...day([cell(2), cell(3)]), exams: [exam({ id: 't1', kind: 'test', length: 1 })] } as unknown as CalendarDay;
    const { cells } = overlayExams(calendarCells([d], names), [d], 'student', names, newAttached());
    expect(cells).toHaveLength(1);
    expect(cells[0].links?.[0]).toMatchObject({ kind: 'exam', label: 'Test' });
    const d2 = { ...plan(), exams: [exam({ id: 't2', kind: 'test', length: 1 })] } as unknown as CalendarDay;
    const out = overlayExams(calendarCells([d2], names), [d2], 'student', names, newAttached()).cells;
    expect(out.find((c) => c.exam)?.status?.label).toBe('Test');
  });

  it('hängt Hausaufgaben an die vom Server genannte Stunde, auch ohne gleiches Fachkürzel', () => {
    const d = {
      ...plan(),
      homework: [{ item_id: 7, channel_id: 1, channel_title: 'D', title: 'Aufsatz', due_at: '', due_date: '2026-10-16', time: '16:00', subject: 'D', subject_name: 'Deutsch', course_id: '5a-D', slot: 3 }],
    } as unknown as CalendarDay;
    const att = newAttached();
    const cells = withHomework(calendarCells([d], names), [d], att);
    const target = cells.find((c) => c.links?.length);
    expect(target?.subject).toBe('D');
    expect(target?.links?.[0]).toMatchObject({ kind: 'ha', to: '/kursraeume/1?tab=aufgaben&aufgabe=7' });
    expect(target?.links?.[0].title).toContain('fällig 16.10.');
    expect(att.ha.has(7)).toBe(true);
  });

  it('hängt Termine mit Uhrzeit an die Stunde, ganztägige bleiben im Kopf', () => {
    const d = {
      ...plan(),
      events: [
        { id: 'a', title: 'Elternabend', kind: 'termin', kind_label: 'Termin', time_from: '09:50', time_to: '', location: '', note: '' },
        { id: 'b', title: 'Wandertag', kind: 'termin', kind_label: 'Termin', time_from: '', time_to: '', location: '', note: '' },
      ],
    } as unknown as CalendarDay;
    const att = newAttached();
    const cells = withEvents(calendarCells([d], names), [d], ['08:00', '08:50', '09:50', '10:40', '11:30'], att);
    expect(cells.find((c) => c.links?.length)?.start).toBe(2);
    expect(dayChips(d, att, false).map((c) => c.key)).toEqual(['eb']);
  });

  it('hängt Nachteilsausgleich und fehlende Kinder an den Klausurblock', () => {
    const d = { ...plan(), exams: [exam()] } as unknown as CalendarDay;
    const { targets } = overlayExams(calendarCells([d], names), [d], 'teacher', names, newAttached());
    withExamNotes(targets, { support: { k1: [{ name: 'Mia', summary: '+15 Min.' }] }, missing: { k1: ['Ben', 'Eva'] } });
    expect(targets.get('k1')?.links?.map((l) => l.kind)).toEqual(['support', 'missing', 'missing']);
  });
});
