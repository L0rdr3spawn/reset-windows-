import { describe, expect, it } from 'vitest';
import { TILES, TILE_BY_KEY, courseLink, formatNumber, tileTone, tileValue, tileVisible, timetableLink } from '../reportTiles';

const def = (k: string) => TILE_BY_KEY[k]!;

describe('Kennzahlen des Qualitätsberichts', () => {
  it('halbe Werte werden als Spanne je Woche gezeigt, nicht als 5,5', () => {
    const v = tileValue(def('class_gaps'), { class_gaps: 5.5 }, { class_gaps: { min: 5, max: 6, avg: 5.5 } });
    expect(v.value).toBe('5–6');
    expect(v.note).toBe('je nach Woche, Ø 5,5');
  });

  it('gleiche Werte in allen Wochen: ganze Zahl ohne Nebenzeile', () => {
    expect(tileValue(def('teacher_gaps'), { teacher_gaps: 42 }, { teacher_gaps: { min: 42, max: 42, avg: 42 } })).toEqual({ value: '42' });
  });

  it('ältere Server ohne Spanne: gerundet mit Durchschnitt in der Nebenzeile', () => {
    expect(tileValue(def('teacher_gaps'), { teacher_gaps: 42.5 })).toEqual({ value: '≈ 43', note: 'Ø 42,5 je Woche' });
  });

  it('Zählwerte bleiben unverändert, fehlende Werte werden zu „–“', () => {
    expect(tileValue(def('courses'), { courses: 12 })).toEqual({ value: '12' });
    expect(tileValue(def('courses'), {})).toEqual({ value: '–' });
  });

  it('Färbung: grün bei 0, rot/gelb bei > 0, neutral ohne Regel', () => {
    expect(tileTone(def('conflicts'), { conflicts: 0 })).toBe('good');
    expect(tileTone(def('conflicts'), { conflicts: 2 })).toBe('bad');
    expect(tileTone(def('class_gaps'), { class_gaps: 1 })).toBe('warn');
    expect(tileTone(def('courses'), { courses: 3 })).toBeUndefined();
  });

  it('„Wochenmuster“ nur bei mehr als einem Muster; unbekannte Kennzahlen nie', () => {
    expect(tileVisible(def('week_variants'), { week_variants: 1 })).toBe(false);
    expect(tileVisible(def('week_variants'), { week_variants: 2 })).toBe(true);
    expect(tileVisible(def('conflicts'), { courses: 1 })).toBe(false);
  });

  it('jede kachel hat deutschen Titel, Einheit, Erklärung und ein Ziel; kein „Week-Variants“', () => {
    for (const t of TILES) {
      expect(t.title.length).toBeGreaterThan(2);
      expect(t.unit.length).toBeGreaterThan(2);
      expect(t.help.length).toBeGreaterThan(30);
      expect(Boolean(t.nav) !== Boolean(t.detail)).toBe(true);
      expect(`${t.title} ${t.unit}`).not.toMatch(/variant/i);
    }
  });

  it('Zahlen deutsch und Links kodiert', () => {
    expect(formatNumber(5.5)).toBe('5,5');
    expect(formatNumber(7)).toBe('7');
    expect(timetableLink('class', '5 a')).toBe('/stundenplan/class/5%20a');
    expect(courseLink('5a-D')).toBe('/planung/kurse?kurs=5a-D');
  });
});
