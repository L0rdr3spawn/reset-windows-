/**
 * Bausteine und Seitenlogik für Wochen 1 … 53, Wochen-Editor (jede Woche / ausgewählte Wochen / Rhythmus),
 * 7-Tage-Woche (Entwurf KALENDER-ZEITRASTER §8, §15.5, §16 E2). Komponenten werden in `node` per `renderToStaticMarkup` geprüft; Bedienung über die reinen
 * Hilfsfunktionen bzw. den Element-Baum (Komponenten ohne Hooks).
 */
import { createElement, isValidElement, type ReactElement, type ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { ApiError } from '../../api/client';
import type { Cell, SchoolYear, Settings, TimetableView } from '../../api/types';
import { ClassPlanningFields, classPlanningOf, samePlanning } from '../../components/ClassPlanningFields';
import { changeLine, confirmDetailOf, confirmTitle } from '../../components/ConfirmChanges';
import { cellAriaLabel, cellWeeksText, dayHead, TimetableGrid } from '../../components/TimetableGrid';
import { WeekNav } from '../../components/WeekNav';
import {
  DayChips,
  initialWeekMode,
  selectionForMode,
  selectionForPattern,
  suggestRhythm,
  toggleWeekChip,
  WEEK_MODES,
  WeekPatternInput,
} from '../../components/WeekPatternInput';
import { profileDays } from '../../features/teacher/windows';
import { holidayTag, isEmptyOffDay, visibleWeekDays } from '../../features/classes/WeekTab';
import type { ClassWeekDay } from '../../features/classes/types';
import { dutyActive, dutyWeeksText } from '../../pages/DutiesPage';
import { examDays } from '../../pages/ExamsPage';
import { calendarErrors, previewBody, settingsBody } from '../../pages/planning/CalendarPanel';
import { layoutTimetable, weekCells } from '../grid';
import { ruleWeekGroups } from '../rules';
import { statsWeek } from '../substitution';
import { schoolYearSpan, weeksSortValue } from '../weeks';

/** Alle Elemente eines Baums (ohne Rendern von Funktionskomponenten). */
function walk(node: ReactNode, out: ReactElement[] = []): ReactElement[] {
  if (Array.isArray(node)) node.forEach((n) => walk(n, out));
  else if (isValidElement(node)) {
    out.push(node);
    walk((node.props as { children?: ReactNode }).children, out);
  }
  return out;
}

const html = (el: ReactElement) => renderToStaticMarkup(el);

// ============================================================================================== Muster-Editor

describe('WeekPatternInput (Wochen-Editor)', () => {
  it('Modi: Jede Woche · Ausgewählte Wochen · Rhythmus', () => {
    expect(WEEK_MODES).toEqual(['all', 'specific', 'rhythm']);
    expect(initialWeekMode({ weeks: [] })).toBe('all');
    expect(initialWeekMode({ weeks: [1, 3] })).toBe('specific');
    expect(initialWeekMode({ weeks: [], rhythm: { every: 2, from_week: 10 } })).toBe('rhythm');
  });

  it('Ergebnis je Modus (alle drei Modi)', () => {
    const p = { every: 3, from: 2, to: 0 };
    expect(selectionForMode('all', { weeks: [1] }, p)).toEqual({ weeks: [], rhythm: null });
    expect(selectionForMode('specific', { weeks: [3, 1, 1] }, p)).toEqual({ weeks: [1, 3], rhythm: null });
    expect(selectionForMode('rhythm', { weeks: [] }, p)).toEqual({ weeks: [], rhythm: { every: 3, from_week: 2 } });
    // vom Rhythmus zu ausgewählten Wochen: die Wochen des Rhythmus werden zur Liste
    expect(selectionForMode('specific', { weeks: [], rhythm: { every: 20, from_week: 5 } }, p)).toEqual({ weeks: [5, 25, 45], rhythm: null });
    expect(selectionForPattern({ every: 2, from: 10, to: 30 })).toEqual({ weeks: [], rhythm: { every: 2, from_week: 10, to_week: 30 } });
    // k beliebig bis 52
    expect(selectionForPattern({ every: 52, from: 1, to: 0 })).toEqual({ weeks: [], rhythm: { every: 52, from_week: 1 } });
    // fehlerhafte Eingabe ändert nichts
    expect(selectionForPattern({ every: 0, from: 1, to: 0 })).toBeNull();
    expect(selectionForPattern({ every: 2, from: 5, to: 3 })).toBeNull();
    expect(suggestRhythm([1, 3, 5, 7, 9])).toEqual({ every: 2, from_week: 1, to_week: 9 });
    expect(suggestRhythm([1, 2])).toBeNull();
  });

  it('Chips: An-/Abwählen, alle Wochen = [], letzte Woche bleibt', () => {
    expect(toggleWeekChip({ weeks: [] }, 1, 4)).toEqual({ weeks: [2, 3, 4], rhythm: null });
    expect(toggleWeekChip({ weeks: [2, 3] }, 1, 3)).toEqual({ weeks: [], rhythm: null });
    expect(toggleWeekChip({ weeks: [3] }, 3, 4)).toBeNull();
  });

  it('52 Chips mit aria-label und aria-pressed, eine Tab-Station', () => {
    const out = html(createElement(WeekPatternInput, { value: { weeks: [1, 27] }, onChange: () => {} }));
    expect(out).toContain('Ausgewählte Wochen');
    const chips = out.match(/aria-label="Woche \d+"/g) ?? [];
    expect(chips).toHaveLength(52);
    expect(out).toMatch(/aria-pressed="true"[^>]*aria-label="Woche 1"/);
    expect(out).toMatch(/aria-pressed="true"[^>]*aria-label="Woche 27"/);
    expect(out).toMatch(/aria-pressed="false"[^>]*aria-label="Woche 2"/);
    expect((out.match(/tabindex="0"/g) ?? []).length).toBe(1);
    expect(out).not.toMatch(/Woche [A-Z]\b/);
  });

  it('Schuljahr mit 53 Wochen zeigt 53 Chips', () => {
    const out = html(createElement(WeekPatternInput, { value: { weeks: [1] }, onChange: () => {}, yearWeeks: 53 }));
    expect(out.match(/aria-label="Woche \d+"/g) ?? []).toHaveLength(53);
  });

  it('Rhythmus mit Vorschau über das Schuljahr', () => {
    const out = html(createElement(WeekPatternInput, { value: { weeks: [], rhythm: { every: 2, from_week: 10 } }, onChange: () => {}, yearWeeks: 52 }));
    expect(out).toContain('Abstand (Wochen)');
    expect(out).toContain('Ab Woche');
    expect(out).toContain('Bis Woche (optional)');
    expect(out).toContain('Woche 10, 12, 14 … (22 von 52)');
  });

  it('jede Woche: keine Chips und keine Felder, aber der Umschalter bleibt', () => {
    const out = html(createElement(WeekPatternInput, { value: { weeks: [] }, onChange: () => {} }));
    expect(out).toContain('Jede Woche');
    expect(out).not.toContain('aria-label="Woche 1"');
    expect(out).not.toContain('Abstand (Wochen)');
  });

  it('Tages-Chips Mo–So mit vollem Namen; Antippen schaltet um, der letzte Tag bleibt', () => {
    const calls: number[][] = [];
    const el = DayChips({ value: [0, 1, 2, 3, 4], onChange: (d) => calls.push(d), label: 'Unterrichtstage' });
    const buttons = walk(el).filter((e) => e.type === 'button');
    expect(buttons.map((b) => (b.props as { 'aria-label': string })['aria-label'])).toEqual(['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']);
    (buttons[5]!.props as { onClick: () => void }).onClick();
    (buttons[0]!.props as { onClick: () => void }).onClick();
    expect(calls).toEqual([
      [0, 1, 2, 3, 4, 5],
      [1, 2, 3, 4],
    ]);
    const single = walk(DayChips({ value: [5], onChange: (d) => calls.push(d), label: 'x' })).filter((e) => e.type === 'button');
    (single[5]!.props as { onClick: () => void }).onClick();
    expect(calls).toHaveLength(2);
  });
});

// ============================================================================================== Wochenwahl

const YEAR: SchoolYear = {
  start: '2026-08-31',
  end: '2027-08-29',
  numbering: 'school_year',
  weeks_in_year: 52,
  open_days: [0, 1, 2, 3, 4],
  warnings: [],
  weeks: Array.from({ length: 52 }, (_, i) => {
    const start = new Date(2026, 7, 31 + 7 * i, 12);
    const end = new Date(2026, 7, 31 + 7 * i + 6, 12);
    const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    return {
      week_no: i + 1,
      iso_week: ((35 + i) % 53) + 1,
      week_start: iso(start),
      week_end: iso(end),
      holiday_week: i === 7 || i === 8,
      holidays: i === 7 || i === 8 ? ['Herbstferien (Beispiel)'] : [],
    };
  }),
};

describe('WeekNav (Woche 1 … Y statt Buchstaben-Umschalter)', () => {
  it('Auswahl 1 … 52 mit Datum und „Ferien“, Knöpfe, week_text', () => {
    const info = {
      week_no: 6,
      iso_week: 41,
      iso_year: 2026,
      week_start: '2026-10-05',
      week_end: '2026-10-11',
      week_text: 'Woche 6 · KW 41',
      holiday_week: false,
      holiday_name: null,
      in_school_year: true,
    };
    const out = html(createElement(WeekNav, { value: '2026-10-07', onChange: () => {}, year: YEAR, info, today: '2026-10-07' }));
    expect((out.match(/<option /g) ?? []).length).toBe(52);
    expect(out).toContain('Woche 6 · KW 41 · 05.10.–11.10.</option>');
    expect(out).toContain('Woche 8 · KW 43 · 19.10.–25.10. · Ferien</option>');
    expect(out).toMatch(/<option value="2026-10-05" selected="">/);
    expect(out).toContain('aria-label="Vorherige Woche"');
    expect(out).toContain('aria-label="Nächste Woche"');
    expect(out).toMatch(/<button[^>]*disabled=""[^>]*>Heute<\/button>/);
    expect(out).toContain('Woche 6 · KW 41');
    expect(out).toContain('Diese Woche');
  });

  it('Ferienwoche mit Badge; ohne Schuljahresdaten nur KW und Zeitraum', () => {
    const out = html(createElement(WeekNav, { value: '2026-10-21', onChange: () => {}, year: YEAR, today: '2026-10-07' }));
    expect(out).toContain('Herbstferien (Beispiel)');
    expect(out).not.toMatch(/<button[^>]*disabled=""[^>]*>Heute/);
    const bare = html(createElement(WeekNav, { value: '2026-10-07', onChange: () => {}, today: '2026-10-07' }));
    expect(bare).not.toContain('<select');
    expect(bare).toContain('KW 41 · 05.10.–11.10.');
  });
});

// ============================================================================================== 7-Tage-Woche

function cell(id: string, day: number, start: number, extra: Partial<Cell> = {}): Cell {
  return {
    lesson_id: id,
    course_id: `K${id}`,
    day,
    start,
    length: 1,
    weeks: [],
    subject: 'M',
    subject_name: 'Mathematik',
    color: '',
    teachers: ['MUE'],
    rooms: ['R1'],
    classes: ['5a'],
    label: '',
    locked: false,
    parts: [],
    ...extra,
  };
}

const DAYS = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];

function view7(cells: Cell[]): TimetableView {
  return {
    kind: 'class',
    ref: '5a',
    title: '5a',
    week_no: 6,
    days: DAYS,
    periods: ['07:55', '08:45'],
    cells,
    week_info: {
      week_no: 6,
      iso_week: 41,
      iso_year: 2026,
      week_start: '2026-10-05',
      week_end: '2026-10-11',
      week_text: 'Woche 6 · KW 41',
      holiday_week: false,
      holiday_name: null,
      in_school_year: true,
    },
    day_info: DAYS.map((name, i) => ({
      index: i,
      name,
      date: `2026-10-${String(5 + i).padStart(2, '0')}`,
      teaching: i < 5,
      day_kind: i < 5 ? ('unterricht' as const) : ('kein_unterrichtstag' as const),
      holiday: null,
    })),
  };
}

describe('Stundenplan: Mo–So, freie Tage schmal und abgeblendet (§16 E2)', () => {
  it('Raster mit 7 Spalten, Sa/So schmal; Zelle zeigt weeks_text statt Buchstaben', () => {
    const v = view7([cell('a', 0, 0, { weeks: [1], weeks_text: 'Woche 1' }), cell('b', 2, 1)]);
    const out = html(createElement(TimetableGrid, { view: v }));
    for (const d of DAYS.slice(0, 5)) expect(out).toContain(`>${d}</span>`);
    expect(out).toContain('<abbr title="Samstag – Kein Unterricht">Sa</abbr>');
    expect(out).toContain('Sonntag: Kein Unterricht');
    expect((out.match(/tt-head[^"]*off-day/g) ?? []).length).toBe(2);
    expect(out).toContain('Kein Unterricht');
    expect(out).toContain('minmax(2.5rem, 0.3fr)');
    expect(out).toContain('<span class="tag">Woche 1</span>');
    expect(out).toContain('05.10.');
    expect(out).not.toMatch(/Woche [A-Z]\b/);
  });

  it('Zellen: Server filtert die Woche (week_info), ältere Antworten filtert der Client', () => {
    const v = view7([cell('a', 0, 0, { weeks: [5] }), cell('b', 0, 1, { weeks: [6] }), cell('c', 0, 2, { weeks: [], rhythm: { every: 2, from_week: 2 } })]);
    expect(weekCells(v).map((c) => c.lesson_id)).toEqual(['a', 'b', 'c']);
    const old = { ...v, week_info: undefined };
    expect(weekCells(old).map((c) => c.lesson_id)).toEqual(['b', 'c']);
  });

  it('Spaltenbreite: schmale Spalte nur ohne Zellen', () => {
    const l = layoutTimetable([cell('s', 5, 0)], 7, 2, { narrowDays: [5, 6] });
    expect(l.columnTemplate.split(' minmax').length).toBe(8);
    expect(l.columnTemplate.endsWith('minmax(2.5rem, 0.3fr)')).toBe(true);
    expect(l.columnTemplate).not.toMatch(/minmax\(2\.5rem, 0\.3fr\) minmax\(2\.5rem/);
  });

  it('Texte der Zelle und des Tageskopfs', () => {
    expect(cellWeeksText(cell('a', 0, 0, { weeks: [1] }))).toBe('Woche 1');
    expect(cellWeeksText(cell('a', 0, 0, { weeks: [], weeks_text: 'jede Woche' }))).toBe('');
    expect(cellWeeksText(cell('a', 0, 0, { weeks: [], rhythm: { every: 2, from_week: 3 } }))).toBe('jede 2. Woche ab Woche 3');
    expect(cellAriaLabel(cell('a', 1, 0, { weeks: [2] }), DAYS)).toContain('Dienstag, 1. Stunde: Mathematik (Woche 2)');
    expect(dayHead(6, view7([]))).toEqual({ name: 'Sonntag', short: 'So', date: '11.10.', holiday: '', off: true });
  });

  it('Klassen-Wochenplan: Mo–So, „Nur Unterrichtstage“ blendet leere freie Tage aus', () => {
    const day = (date: string, weekday: number, extra: Partial<ClassWeekDay> = {}): ClassWeekDay => ({ date, weekday, holiday: null, cells: [], ...extra });
    const days = [
      day('2026-10-05', 0, { day_kind: 'unterricht' }),
      day('2026-10-10', 5, { day_kind: 'kein_unterrichtstag' }),
      day('2026-10-11', 6, { day_kind: 'kein_unterrichtstag', has_items: true }),
    ];
    expect(visibleWeekDays(days, false)).toHaveLength(3);
    expect(visibleWeekDays(days, true).map((d) => d.weekday)).toEqual([0, 6]);
    expect(isEmptyOffDay(days[1]!)).toBe(true);
    expect(holidayTag('Tag der Deutschen Einheit', 'feiertag')).toBe('unterrichtsfrei');
    expect(holidayTag('Brückentag', 'ferien')).toBe('Ferien');
    expect(holidayTag('Herbstferien (Beispiel)')).toBe('Ferien');
  });

  it('Klausur am Samstag: Unterrichtstag der Klasse statt „Wochenende“', () => {
    const st = { days: 5, school_days: [] };
    expect(examDays(['SA'], [{ id: 'SA', school_days: [5] }], st)).toEqual([5]);
    expect(examDays(['5a', 'SA'], [{ id: '5a' }, { id: 'SA', school_days: [5] }], st)).toEqual([0, 1, 2, 3, 4, 5]);
    expect(examDays([], [], st)).toEqual([0, 1, 2, 3, 4]);
  });

  it('Wochenstatistik mit Unterrichtstagen, Lehrkraft-Tage bis Sa/So', () => {
    expect(statsWeek('2026-10-07', [0, 1, 2, 3, 4, 5])).toEqual({ from: '2026-10-05', to: '2026-10-10' });
    expect(statsWeek('2026-10-07', 5)).toEqual({ from: '2026-10-05', to: '2026-10-09' });
    expect(profileDays({ days: 5, school_days: [0, 1, 2, 3, 4, 5] })).toBe(6);
    expect(profileDays({ days: 5 })).toBe(5);
  });
});

// ============================================================================================== Aufsichten, Kurse, Regeln

describe('Aufsichten, Kurse, Regeln ohne Buchstaben', () => {
  it('Aufsicht in der Woche aktiv (ausgewählte Wochen bzw. Rhythmus) und Wochentext', () => {
    expect(dutyActive({ weeks: [6] }, { weekNo: 6 })).toBe(true);
    expect(dutyActive({ weeks: [6] }, { weekNo: 5 })).toBe(false);
    expect(dutyActive({ weeks: [6] }, {})).toBe(true);
    expect(dutyActive({ weeks: [], rhythm: { every: 2, from_week: 10 } }, { weekNo: 11 })).toBe(false);
    expect(dutyActive({ weeks: [], rhythm: { every: 2, from_week: 10 } }, { weekNo: 12 })).toBe(true);
    expect(dutyWeeksText({ weeks: [2] })).toBe('Woche 2');
    expect(dutyWeeksText({ weeks: [] })).toBe('');
    expect(dutyWeeksText({ weeks: [], rhythm: { every: 3, from_week: 1 } })).toBe('jede 3. Woche ab Woche 1');
  });

  it('numerische Sortierung der Spalte „Wochen“ (U-84)', () => {
    const sel = (weeks: number[]) => ({ weeks });
    const sorted = [[9], [], [1], [10], [1, 3]].map(sel).sort((a, b) => weeksSortValue(a) - weeksSortValue(b));
    expect(sorted.map((x) => x.weeks)).toEqual([[], [1], [1, 3], [9], [10]]);
    expect(weeksSortValue({ weeks: [], rhythm: { every: 2, from_week: 4 } })).toBeGreaterThan(weeksSortValue({ weeks: [3] }));
  });

  it('Regel-Vorschau zeigt nur unterschiedliche Wochen', () => {
    const g = ruleWeekGroups([{ weeks: [1], days: [2], periods: [], note: '' }], 7, 2, 6);
    expect(g.map((x) => x.label)).toEqual(['Woche 1', 'Woche 2–6']);
    expect(ruleWeekGroups([{ weeks: [], days: [2], periods: [], note: '' }], 7, 2, 52).map((x) => x.label)).toEqual(['jede Woche']);
    const r = ruleWeekGroups([{ weeks: [], days: [0], periods: [], note: '', rhythm: { every: 2, from_week: 10, to_week: 14 } }], 7, 2, 52);
    expect(r.map((x) => x.label)).toEqual(['Woche 1–9, 11, 13, 15–52', 'jede 2. Woche ab Woche 10 bis Woche 14']);
  });
});

// ============================================================================================== Einstellungen, Klasse, 409

describe('Einstellungen „Zeitraster & Schuljahr“', () => {
  const base = { school_days: [], days: 5, cycle_start: '2026-08-31' } as unknown as Settings;

  it('Grenzen wie im Backend (Unterrichtstage)', () => {
    expect(calendarErrors(base)).toEqual([]);
    expect(calendarErrors({ ...base, days: 0, school_days: [] })).toEqual([]);     // Standard: die ersten Tage
  });

  it('Körper für PUT und Vorschau', () => {
    const body = settingsBody({ ...base, school_days: [0, 1, 2, 3, 4, 5], school_year_end: '2027-08-29' } as unknown as Settings);
    expect(body.days).toBe(6);
    expect('school_year_end' in body).toBe(false);
    expect(previewBody({ ...base, school_year_start: '2026-08-01' })).toEqual({
      week_numbering: 'iso',
      year_start_mode: 'auto',
      school_year_start: '2026-08-01',
      school_days: [],
    });
  });

  it('Ende des Schuljahres: Sonntag vor der Woche des nächsten Beginns (W3)', () => {
    expect(schoolYearSpan('2026-08-01')).toEqual({ end: '2027-07-25', weeks: 52 });
    expect(schoolYearSpan('2026-08-31')).toEqual({ end: '2027-08-29', weeks: 52 });
    expect(schoolYearSpan('2027-08-01')).toEqual({ end: '2028-07-30', weeks: 53 });
    expect(schoolYearSpan('')).toBeNull();
  });

  it('409 plan_change: Liste „{label}: {before} → {after}“, Titel, nur bekannte Codes', () => {
    const detail = { message: 'Die Änderung betrifft 1 Eintrag', code: 'plan_change', changes: [{ kind: 'lesson', id: 'L6', label: 'Stunde Mi 1. Std. M 7a', before: 'Mi', after: 'kein Unterrichtstag' }] };
    const d = confirmDetailOf(new ApiError(409, 'x', detail));
    expect(d?.changes.map(changeLine)).toEqual(['Stunde Mi 1. Std. M 7a: Mi → kein Unterrichtstag']);
    expect(confirmTitle('plan_change')).toBe('Änderungen durch die neuen Unterrichtstage');
    expect(confirmTitle('grid_change')).toBe('Änderungen durch das Zeitraster');
    expect(confirmDetailOf(new ApiError(409, 'x', { conflicts: [] }))).toBeNull();
    expect(confirmDetailOf(new ApiError(409, 'x', { ...detail, code: 'cycle_change' }))).toBeNull();
    expect(confirmDetailOf(new ApiError(422, 'x', detail))).toBeNull();
  });
});

describe('Planungsfeld der Klasse (V12)', () => {
  const st = { days: 5, school_days: [] };
  it('Standardwerte, Vergleich, Anzeige „Wie Schule“ bzw. eigene Tage', () => {
    expect(classPlanningOf({})).toEqual({ school_days: [], profile: null });
    expect(classPlanningOf({ profile: { id: 'JG5' } }).profile).toBe('JG5');
    expect(samePlanning(classPlanningOf({}), { school_days: [], profile: null })).toBe(true);
    expect(samePlanning(classPlanningOf({}), { school_days: [5], profile: null })).toBe(false);
    expect(samePlanning(classPlanningOf({}), { school_days: [], profile: 'JG5' })).toBe(false);
    const school = html(createElement(ClassPlanningFields, { value: classPlanningOf({}), onChange: () => {}, settings: st }));
    expect(school).toContain('Wie Schule (Mo–Fr)');
    expect(school).not.toMatch(/Zyklus|Wochen\)/);
    const own = html(createElement(ClassPlanningFields, { value: { school_days: [5], profile: null }, onChange: () => {}, settings: st }));
    expect(own).toContain('aria-label="Samstag"');
  });
});
