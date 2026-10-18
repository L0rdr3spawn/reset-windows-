import { describe, expect, it } from 'vitest';
import { pickReplanJob } from './replan';
import { allowedIds, allowedKinds, filterAllowed, forbiddenText, isAllowed } from './scope';
import type { AllowedRefs, ReplanJob, TeacherProfile } from './types';
import { availablePeriods, describeWindows, isScopedTeacher, profileEqual, splitRules, toMinutes, WINDOW_TEMPLATES, windowError } from './windows';

// Demo-Raster: 12 Stunden inkl. Abendstunden 16:00/16:50/17:40, 45 Minuten
const TIMES = ['07:55', '08:45', '09:50', '10:40', '11:45', '12:35', '13:30', '14:20', '15:10', '16:00', '16:50', '17:40'];

describe('Zeitfenster → verfügbare Stunden', () => {
  it('leere Liste = ganztägig verfügbar', () => {
    expect([...availablePeriods([], TIMES, 45, 0)]).toHaveLength(12);
  });

  it('„ab 10:00“ sperrt die ersten drei Stunden (Stunde zählt nur ganz im Fenster)', () => {
    const w = [{ days: [0, 1, 2, 3, 4], start: '10:00', end: '18:30', weeks: [] }];
    const set = availablePeriods(w, TIMES, 45, 2);
    expect([...set].sort((a, b) => a - b)).toEqual([3, 4, 5, 6, 7, 8, 9, 10, 11]);
    // 17:40 + 45 = 18:25 ≤ 18:30 → letzte Abendstunde gehört dazu; Ende 18:20 nicht
    expect(availablePeriods([{ ...w[0]!, end: '18:20' }], TIMES, 45, 2).has(11)).toBe(false);
  });

  it('„nur abends ab 16:00“ und Tage ohne Fenster sind gesperrt', () => {
    const w = [{ days: [0, 1, 2, 3], start: '16:00', end: '21:00', weeks: [] }];
    expect([...availablePeriods(w, TIMES, 45, 0)]).toEqual([9, 10, 11]);
    expect(availablePeriods(w, TIMES, 45, 4).size).toBe(0); // Freitag: kein Fenster
  });

  it('Ausgewählte Wochen: Fenster nur in Woche 2; Rhythmus alle k Wochen', () => {
    const w = [
      { days: [0], start: '07:00', end: '13:00', weeks: [1] },
      { days: [0], start: '12:00', end: '18:30', weeks: [2] },
    ];
    expect(availablePeriods(w, TIMES, 45, 0, 1).has(0)).toBe(true);
    expect(availablePeriods(w, TIMES, 45, 0, 2).has(0)).toBe(false);
    expect(availablePeriods(w, TIMES, 45, 0, 2).has(11)).toBe(true);
    const r = [{ days: [0], start: '07:00', end: '13:00', weeks: [], rhythm: { every: 2, from_week: 10 } }];
    expect(availablePeriods(r, TIMES, 45, 0, 10).has(0)).toBe(true);
    expect(availablePeriods(r, TIMES, 45, 0, 11).size).toBe(0);
    expect(availablePeriods(r, TIMES, 45, 0, 12).has(0)).toBe(true);
    expect(describeWindows(r)).toBe('jede 2. Woche ab Woche 10: Mo 07:00–13:00');
  });

  it('Vorlagen, Prüfung und Beschreibung', () => {
    const ab10 = WINDOW_TEMPLATES.find((t) => t.key === 'ab10')!.windows(5);
    expect(describeWindows(ab10)).toBe('Mo–Fr 10:00–18:30');
    expect(describeWindows([{ days: [2], start: '08:00', end: '12:00', weeks: [2] }])).toBe('Woche 2: Mi 08:00–12:00');
    expect(describeWindows([{ days: [0, 1, 2, 3, 4], start: '10:00', end: '17:00', weeks: [1] }])).toBe('Woche 1: Mo–Fr 10:00–17:00');
    expect(windowError({ days: [], start: '08:00', end: '12:00', weeks: [] }, 5)).toMatch(/Wochentag/);
    expect(windowError({ days: [0], start: '12:00', end: '08:00', weeks: [] }, 5)).toMatch(/Ende/);
    expect(windowError({ days: [5], start: '08:00', end: '12:00', weeks: [] }, 5)).toMatch(/außerhalb/);
    expect(windowError({ days: [0], start: '08:00', end: '24:00', weeks: [2] }, 5)).toBeNull();
    expect(windowError({ days: [0], start: '08:00', end: '12:00', weeks: [54] }, 5)).toMatch(/Wochen/);
    expect(windowError({ days: [0], start: '08:00', end: '12:00', weeks: [1], rhythm: { every: 2, from_week: 1 } }, 5)).toMatch(/entweder/);
    expect(toMinutes('24:00')).toBeNull();
    expect(toMinutes('7:05')).toBe(425);
  });

  it('erzeugte Sperrzeiten werden von manuellen getrennt; Profilvergleich ignoriert Reihenfolge', () => {
    const r = splitRules([
      { weeks: [], days: [4], periods: [6, 7], note: 'Freitag frei' },
      { weeks: [], days: [0], periods: [0, 1], note: 'Zeitfenster: verfügbar 10:00–18:30' },
    ]);
    expect(r.manual.map((x) => x.note)).toEqual(['Freitag frei']);
    expect(r.generated).toHaveLength(1);
    const a: TeacherProfile = { subjects: ['M', 'D'], preferred_classes: ['5a'], max_hours: 20, time_windows: [{ days: [1, 0], start: '10:00', end: '18:30', weeks: [] }], wishes: [] };
    const b: TeacherProfile = { ...a, subjects: ['D', 'M'], time_windows: [{ days: [0, 1], start: '10:00', end: '18:30', weeks: [] }] };
    expect(profileEqual(a, b)).toBe(true);
    expect(profileEqual(a, { ...b, max_hours: 21 })).toBe(false);
  });
});

describe('Lehrer-Scope (Auswahllisten)', () => {
  const scoped: AllowedRefs = { all: false, kinds: ['class', 'teacher', 'room'], classes: ['5a', '7b'], teachers: ['MUE'], rooms: null, students: [] };
  const opts = [{ value: '5a' }, { value: '5b' }, { value: '7b' }];

  it('filtert Klassen/Lehrkräfte, Räume bleiben frei', () => {
    expect(filterAllowed(opts, scoped, 'class').map((o) => o.value)).toEqual(['5a', '7b']);
    expect(filterAllowed([{ value: 'MUE' }, { value: 'SCH' }], scoped, 'teacher').map((o) => o.value)).toEqual(['MUE']);
    expect(filterAllowed([{ value: 'R1' }], scoped, 'room')).toHaveLength(1);
    expect(filterAllowed([{ value: 'S1' }], scoped, 'student')).toHaveLength(0);
    expect(allowedIds(scoped, 'room')).toBeNull();
  });

  it('ohne Einschränkung bzw. vor dem Laden: alles', () => {
    expect(filterAllowed(opts, null, 'class')).toHaveLength(3);
    expect(filterAllowed(opts, { ...scoped, all: true }, 'class')).toHaveLength(3);
    expect(isAllowed(undefined, 'teacher', 'SCH')).toBe(true);
  });

  it('Ansichten und 403-Texte', () => {
    expect(allowedKinds(['class', 'teacher', 'room', 'student'], scoped)).toEqual(['class', 'teacher', 'room']);
    expect(isAllowed(scoped, 'teacher', 'SCH')).toBe(false);
    expect(isAllowed(scoped, 'class', '7b')).toBe(true);
    expect(isAllowed(scoped, 'student', 'S1')).toBe(false);
    expect(forbiddenText('teacher', true)).toMatch(/eigenen Stundenplan/);
    expect(forbiddenText('class', false)).toMatch(/Klassenplan/);
  });

  it('erkennt eingeschränkte Lehrkräfte', () => {
    expect(isScopedTeacher({ role: 'lehrer', permissions: ['plans.read_all', 'profile.teacher_self'] })).toBe(true);
    expect(isScopedTeacher({ role: 'planer', permissions: ['plans.read_all', 'timetable.edit'] })).toBe(false);
    expect(isScopedTeacher({ role: 'schueler', permissions: [] })).toBe(false);
    expect(isScopedTeacher(null)).toBe(false);
  });
});

describe('Neuplanungs-Jobs', () => {
  const job = (id: string, status: string, teacher: string, created: string, kind = 'replan_teacher'): ReplanJob =>
    ({ id, kind, status, progress: 0, message: '', created_at: created, params: { teacher_id: teacher } }) as ReplanJob;

  it('laufender Job vor fertigem, fremde Lehrkräfte und Generator-Läufe ignoriert', () => {
    const jobs = [
      job('a', 'done', 'MUE', '2026-10-06T08:00:00Z'),
      job('b', 'running', 'MUE', '2026-10-06T07:00:00Z'),
      job('c', 'running', 'SCH', '2026-10-06T09:00:00Z'),
      job('d', 'running', 'MUE', '2026-10-06T10:00:00Z', 'generate'),
    ];
    expect(pickReplanJob(jobs, 'MUE')?.id).toBe('b');
    expect(pickReplanJob(jobs.filter((j) => j.id !== 'b'), 'MUE')?.id).toBe('a');
    expect(pickReplanJob([job('x', 'applied', 'MUE', '2026-10-06T08:00:00Z')], 'MUE')).toBeNull();
  });
});
