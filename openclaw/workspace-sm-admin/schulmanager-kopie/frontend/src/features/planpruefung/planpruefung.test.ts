import { describe, expect, it } from 'vitest';
import { impactText, isActionable, metricDeltas, verdict } from './logic';

describe('metricDeltas', () => {
  it('zeigt vorher → nachher und bewertet weniger als besser', () => {
    const d = metricDeltas({ problems: 5, conflicts: 0, unplaced_hours: 2, class_gaps: 1.5, teacher_gaps: 2 }, { problems: 1, conflicts: 0, unplaced_hours: 0, class_gaps: 2, teacher_gaps: 2 });
    expect(d.find((x) => x.key === 'problems')).toMatchObject({ tone: 'good', text: '5 → 1' });
    expect(d.find((x) => x.key === 'class_gaps')?.tone).toBe('bad');
    expect(d.find((x) => x.key === 'teacher_gaps')).toMatchObject({ tone: 'same', text: '2' });
    expect(verdict(d)).toEqual({ better: 2, worse: 1 });
  });

  it('blendet unwichtige Nullzeilen und unbekannte Werte aus', () => {
    const d = metricDeltas({ problems: 1, site_changes: 0, core_late: null }, { problems: 0, site_changes: 0, core_late: null });
    expect(d.map((x) => x.key)).toEqual(['problems']);
  });
});

describe('impactText', () => {
  it('beschreibt Verschiebungen, Räume und Betroffene', () => {
    const t = impactText({
      key: 'minimal',
      moved_lessons: 3,
      changes: [{ course_id: 'K1', label: 'M 7a', classes: ['7a'], teachers: ['ABC'], from: ['Mi 3.'], to: ['Do 2.'], rooms: [{ where: 'Do 2.', old: ['R1'], new: ['R2'] }] }],
      affected_classes: ['7a'],
      affected_teachers: ['ABC', 'DEF'],
    });
    expect(t).toBe('3 Stunden verschoben · 1 Raumwechsel · 1 Klasse · 2 Lehrkräfte');
  });

  it('Vertretung ändert den Plan nicht', () => {
    expect(impactText({ key: 'vertretung', moved_lessons: 0, changes: [], affected_classes: [], affected_teachers: [] })).toBe('Keine Änderung am Stundenplan');
  });
});

describe('isActionable', () => {
  it('berücksichtigt Zurückstellung und Status', () => {
    const now = Date.parse('2026-10-13T12:00:00Z');
    expect(isActionable({ status: 'offen', postponed_until: null }, now)).toBe(true);
    expect(isActionable({ status: 'offen', postponed_until: '2026-10-13T18:00:00Z' }, now)).toBe(false);
    expect(isActionable({ status: 'offen', postponed_until: '2026-10-13T08:00:00Z' }, now)).toBe(true);
    expect(isActionable({ status: 'angenommen', postponed_until: null }, now)).toBe(false);
  });
});
