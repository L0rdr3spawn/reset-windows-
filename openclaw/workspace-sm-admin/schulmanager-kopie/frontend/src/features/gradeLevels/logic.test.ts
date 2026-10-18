import { describe, expect, it } from 'vitest';
import { gradeValid, impactLines, needsTypedConfirm, profileColor, profileImpactLines, profileShort, suggestClassNames, suggestProfileId } from './logic';

describe('suggestClassNames', () => {
  it('beginnt bei a und überspringt vorhandene', () => {
    expect(suggestClassNames(5, [], 3)).toEqual(['5a', '5b', '5c']);
    expect(suggestClassNames(5, ['5a', '5B'], 2)).toEqual(['5c', '5d']);
  });
  it('geht nach z weiter', () => {
    const many = suggestClassNames(0, [], 28);
    expect(many[25]).toBe('0z');
    expect(new Set(many).size).toBe(28);
  });
});

describe('gradeValid', () => {
  it('0 bis 20', () => {
    expect([gradeValid(0), gradeValid(20), gradeValid(21), gradeValid(-1), gradeValid(5.5)]).toEqual([true, true, false, false, false]);
  });
});

describe('Löschfolgen', () => {
  const t = { students: 23, courses_deleted: 9, courses_shared: 1, lessons: 74, absences: 0 };
  it('Schüler gefährlich, solange sie nicht verschoben werden', () => {
    expect(impactLines(t, false)[0]).toEqual({ text: '23 Schüler/innen werden mit gelöscht', danger: true });
    expect(impactLines(t, true)[0]?.danger).toBe(false);
  });
  it('Eintippen nur bei Datenverlust', () => {
    expect(needsTypedConfirm({ students: 0, courses_deleted: 0, lessons: 0 }, false)).toBe(false);
    expect(needsTypedConfirm({ students: 3, courses_deleted: 0, lessons: 0 }, false)).toBe(true);
    expect(needsTypedConfirm({ students: 3, courses_deleted: 0, lessons: 0 }, true)).toBe(false);
    expect(needsTypedConfirm({ students: 0, courses_deleted: 2, lessons: 0 }, true)).toBe(true);
  });
});

describe('Jahrgänge', () => {
  it('Farbe, Kurzname und ID-Vorschlag', () => {
    expect(profileColor({ id: 'x', color: '#1d4ed8' })).toBe('#1d4ed8');
    expect(profileColor({ id: 'x', color: 'rot' })).toMatch(/^#[0-9a-f]{6}$/i);
    expect(profileShort({ name: 'Montessori', short: '', grade: null })).toBe('Mont');
    expect(profileShort({ name: 'Jahrgang 5', short: '', grade: 5 })).toBe('5');
    expect(profileShort({ name: 'Jahrgang 5', short: '5 IF', grade: 5 })).toBe('5 IF');
    expect(suggestProfileId('5 Informatik', '5 IF', ['5IF'])).toBe('5IF2');
    expect(suggestProfileId('GIF 26', '', [])).toBe('GIF26');
  });
  it('Löschfolgen eines Jahrgangs', () => {
    const imp = {
      id: 'JG5', name: 'Jahrgang 5',
      classes: [{ id: '5a', name: '5a' }, { id: '5b', name: '5b' }], courses: 18, lessons: 54,
      curriculum: { id: 'ST5', name: 'Stundentafel 5', shared: false, derived: ['ST5IF'] },
      alternatives: [{ id: '5IF', name: '5 Informatik', grade: 5, color: '' }],
    };
    const ohne = profileImpactLines(imp, null, false);
    expect(ohne[0]).toMatchObject({ danger: true });
    expect(ohne[0]?.text).toContain('2 Klassen ohne Jahrgang');
    expect(ohne[1]?.text).toContain('18 Kurse');
    expect(ohne[1]?.text).toContain('54 Stunden');
    expect(ohne[2]).toEqual({ text: 'Stundentafel „Stundentafel 5“ bleibt erhalten', danger: false });
    const umzug = profileImpactLines(imp, '5IF', true);
    expect(umzug[0]).toMatchObject({ danger: false });
    expect(umzug[0]?.text).toContain('„5 Informatik“');
    expect(umzug[2]?.text).toContain('1 abgeleitete Tafel wird eigenständig');
    expect(profileImpactLines({ ...imp, classes: [], courses: 0, curriculum: null }, null, false)).toEqual([]);
  });
});
