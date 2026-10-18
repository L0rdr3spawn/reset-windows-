import { describe, expect, it } from 'vitest';
import { addDays, currentSchoolDay, formatDate, formatDayMonth, formatLong, isoWeekNumber, isWeekend, relativeDayLabel, shiftSchoolDay, weekdayIndex } from '../dates';

describe('Datumshilfen', () => {
  it('rechnet Wochentage und Schultage', () => {
    expect(weekdayIndex('2026-10-05')).toBe(0); // Montag
    expect(weekdayIndex('2026-10-11')).toBe(6); // Sonntag
    expect(shiftSchoolDay('2026-10-09', 1)).toBe('2026-10-12'); // Fr → Mo
    expect(shiftSchoolDay('2026-10-12', -1)).toBe('2026-10-09'); // Mo → Fr
    expect(addDays('2026-12-31', 1)).toBe('2027-01-01');
    expect(currentSchoolDay(new Date(2026, 9, 10, 9))).toBe('2026-10-12'); // Samstag → Montag
  });

  it('formatiert deutsch', () => {
    expect(formatDate('2026-10-06')).toBe('06.10.2026');
    expect(formatLong('2026-10-06')).toBe('Dienstag, 6. Oktober 2026');
    expect(relativeDayLabel('2026-10-06', '2026-10-06')).toBe('Heute');
    expect(relativeDayLabel('2026-10-07', '2026-10-06')).toBe('Morgen');
  });

  it('Unterrichtstage als Zahl (erste n Tage) oder Liste (R3, V16); KW nach ISO', () => {
    expect(isWeekend('2026-10-10')).toBe(true); // Sa bei Mo–Fr
    expect(isWeekend('2026-10-10', 6)).toBe(false);
    expect(isWeekend('2026-10-10', [5])).toBe(false); // Samstagsklasse
    expect(isWeekend('2026-10-05', [5])).toBe(true); // Montag ohne Unterricht
    expect(isWeekend('2026-10-10', [])).toBe(true); // leer = Mo–Fr
    expect(shiftSchoolDay('2026-10-09', 1, [0, 1, 2, 3, 4, 5])).toBe('2026-10-10'); // Fr → Sa
    expect(shiftSchoolDay('2026-10-09', 1, [5])).toBe('2026-10-10');
    expect(currentSchoolDay(new Date(2026, 9, 11, 9), [5])).toBe('2026-10-17'); // So → nächster Sa
    expect(isoWeekNumber('2026-12-28')).toBe(53);
    expect(isoWeekNumber('2027-01-04')).toBe(1);
    expect(formatDayMonth('2026-10-05')).toBe('05.10.');
  });
});
