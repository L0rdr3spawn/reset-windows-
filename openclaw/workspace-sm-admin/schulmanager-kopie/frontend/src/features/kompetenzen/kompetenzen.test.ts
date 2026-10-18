import { describe, expect, it } from 'vitest';
import type { BadgeCriteria, Framework, OverviewStudent, Plan } from './api';
import {
  criteriaDraft,
  criteriaError,
  criteriaOf,
  draftError,
  draftOf,
  emptyDraft,
  evidenceHref,
  filterStudents,
  groupPlans,
  levelBucket,
  levelLabel,
  levelSummary,
  nextStatus,
  percent,
  planProgress,
  setLevelCount,
  toInput,
  trimTail,
  weekRangeText,
} from './logic';

const LEVELS = ['Ich fange an', 'Mit Hilfe', 'Allein', 'Erklären'];

function student(over: Partial<OverviewStudent>): OverviewStudent {
  return { id: 's', name: 'Ada', cells: {}, support: 0, pending: 0, progress: 0, ...over };
}

function plan(over: Partial<Plan>): Plan {
  return {
    id: 1, student_id: 's', competency_id: null, competency_title: '', framework_name: '', area_name: '', title: 'Ziel', note: '', week_start: null,
    due_date: null, status: 'offen', source: 'lehrkraft', item_type: '', item_id: '', overdue: false, done_at: null, can_edit: true, can_status: true, ...over,
  };
}

describe('Stufen und Farben', () => {
  it('ordnet jede Stufe einer von vier Farbstufen zu', () => {
    expect([1, 2, 3, 4].map((l) => levelBucket(l, 4))).toEqual([1, 2, 3, 4]);
    expect([1, 2, 3].map((l) => levelBucket(l, 3))).toEqual([2, 3, 4]);
    expect([1, 6].map((l) => levelBucket(l, 6))).toEqual([1, 4]);
    expect(levelBucket(null, 4)).toBe(0);
    expect(levelBucket(0, 4)).toBe(0);
    expect(levelBucket(9, 4)).toBe(4);
  });
  it('beschreibt Stufen für Bildschirmleser', () => {
    expect(levelLabel(LEVELS, 2)).toBe('Mit Hilfe');
    expect(levelLabel(LEVELS, null)).toBe('Noch nicht eingeschätzt');
    expect(levelSummary(LEVELS, 3)).toBe('Stufe 3 von 4: Allein');
    expect(percent(0.456)).toBe('46 %');
    expect(percent(2)).toBe('100 %');
  });
});

describe('Klassenübersicht filtern', () => {
  const list = [student({ id: 'a', name: 'Anna', support: 2 }), student({ id: 'b', name: 'Ben', pending: 1 }), student({ id: 'c', name: 'Cem' })];
  it('zeigt, wer Unterstützung braucht', () => {
    expect(filterStudents(list, 'unterstuetzung').map((s) => s.id)).toEqual(['a']);
    expect(filterStudents(list, 'offen').map((s) => s.id)).toEqual(['b']);
    expect(filterStudents(list, 'alle')).toHaveLength(3);
    expect(filterStudents(list, 'alle', ' be ').map((s) => s.id)).toEqual(['b']);
  });
});

describe('Nachweise', () => {
  it('erlaubt nur sichere Links', () => {
    expect(evidenceHref('link', '', 'https://example.org/x')).toBe('https://example.org/x');
    expect(evidenceHref('link', '', '/kursraeume/4')).toBe('/kursraeume/4');
    expect(evidenceHref('link', '', 'javascript:alert(1)')).toBeNull();
    expect(evidenceHref('link', '', '//evil.example')).toBeNull();
    expect(evidenceHref('assignment', 'channel:12', '')).toBe('/kursraeume/12');
    expect(evidenceHref('material', 'channel_item:7', '')).toBe('/kursraeume/7');
    expect(evidenceHref('material', 'other:7', '')).toBeNull();
    expect(evidenceHref('note', '', 'Beobachtung')).toBeNull();
  });
});

describe('Lernplan', () => {
  const week = '2026-10-12';
  it('gliedert nach Wochen', () => {
    const plans = [
      plan({ id: 1, week_start: week, due_date: '2026-10-16' }),
      plan({ id: 2, week_start: week, due_date: '2026-10-14' }),
      plan({ id: 3, week_start: '2026-10-05' }),
      plan({ id: 4, week_start: '2026-10-19' }),
      plan({ id: 5 }),
      plan({ id: 6, week_start: week, status: 'erledigt', done_at: '2026-10-13T10:00:00Z' }),
    ];
    const groups = groupPlans(plans, '2026-10-14');
    expect(groups.map((g) => [g.key, g.plans.map((p) => p.id)])).toEqual([
      ['diese', [2, 1]],
      ['frueher', [3]],
      ['spaeter', [4]],
      ['ohne', [5]],
      ['erledigt', [6]],
    ]);
    expect(groupPlans([], week)).toEqual([]);
    expect(planProgress(plans)).toEqual({ done: 1, total: 6 });
  });
  it('wechselt den Status der Reihe nach', () => {
    expect(nextStatus('offen')).toBe('in_arbeit');
    expect(nextStatus('in_arbeit')).toBe('erledigt');
    expect(nextStatus('erledigt')).toBe('offen');
    expect(weekRangeText('2026-10-12')).toBe('12.10. – 16.10.');
  });
});

describe('Rahmen-Editor', () => {
  const fw: Framework = {
    id: 3, name: 'Mathe', subject: '', description: '', levels: LEVELS, support_level: 1, archived: false,
    areas: [{ id: 5, name: 'Zahlen', competencies: [{ id: 9, code: 'Z1', title: 'Ich kann zählen', descriptors: ['a', '', 'c'] }] }],
  };
  it('prüft den Entwurf', () => {
    expect(draftError(emptyDraft())).toMatch(/Namen/);
    const d = { ...emptyDraft(), name: 'X' };
    expect(draftError(d)).toMatch(/Mindestens ein Bereich/);
    const ok = { ...d, areas: [{ name: 'A', competencies: [{ code: '', title: 'Ich kann x', descriptors: [] }] }] };
    expect(draftError(ok)).toBeNull();
    expect(draftError({ ...ok, levels: ['a'] })).toMatch(/2 bis 6/);
    expect(draftError({ ...ok, levels: ['a', ' '] })).toMatch(/Beschriftung/);
    expect(draftError({ ...ok, support_level: 4 })).toMatch(/Unterstützung/);
    expect(draftError({ ...ok, areas: [{ name: '', competencies: [{ code: '', title: 'x', descriptors: [] }] }] })).toMatch(/Namen/);
    expect(draftError({ ...ok, areas: [{ name: 'B', competencies: [{ code: '', title: ' ', descriptors: [] }] }] })).toMatch(/Mindestens ein Bereich|keine Kompetenz/);
  });
  it('übernimmt IDs und verwirft Leeres', () => {
    const d = draftOf(fw);
    d.areas.push({ name: '', competencies: [{ code: '', title: '', descriptors: [] }] });
    d.areas[0]!.competencies.push({ code: '', title: '  ', descriptors: [] });
    const input = toInput(d);
    expect(input.areas).toHaveLength(1);
    expect(input.areas[0]).toMatchObject({ id: 5, name: 'Zahlen' });
    expect(input.areas[0]!.competencies).toEqual([{ id: 9, code: 'Z1', title: 'Ich kann zählen', descriptors: ['a', '', 'c'] }]);
    expect(trimTail(['a', '', ''])).toEqual(['a']);
  });
  it('ändert die Zahl der Stufen und kürzt Abhängiges', () => {
    const d = draftOf(fw);
    const fewer = setLevelCount({ ...d, support_level: 3 }, 2);
    expect(fewer.levels).toHaveLength(2);
    expect(fewer.support_level).toBe(1);
    expect(fewer.areas[0]!.competencies[0]!.descriptors).toEqual(['a', '']);
    expect(setLevelCount(d, 1).levels).toHaveLength(2);
    expect(setLevelCount(d, 9).levels).toHaveLength(6);
    expect(setLevelCount(d, 5).levels[4]).toBe('Stufe 5');
  });
});

describe('Abzeichen-Kriterien', () => {
  it('wandelt zwischen Formular und API', () => {
    expect(criteriaOf(criteriaDraft(null))).toBeNull();
    const area: BadgeCriteria = { type: 'area', area_id: 4, min_level: 3, share: 0.8 };
    expect(criteriaOf(criteriaDraft(area))).toEqual(area);
    const comps: BadgeCriteria = { type: 'competencies', competency_ids: [1, 2], min_level: 2 };
    expect(criteriaOf(criteriaDraft(comps))).toEqual(comps);
    const fwc: BadgeCriteria = { type: 'framework', framework_id: 7, min_level: 4, share: 1 };
    expect(criteriaDraft(fwc).kind).toBe('framework');
    expect(criteriaOf({ ...criteriaDraft(null), kind: 'area' })).toBeNull();
  });
  it('meldet fehlende Angaben', () => {
    expect(criteriaError(criteriaDraft(null))).toBeNull();
    expect(criteriaError({ ...criteriaDraft(null), kind: 'competencies' })).toMatch(/Kompetenz/);
    expect(criteriaError({ ...criteriaDraft(null), kind: 'area' })).toMatch(/Bereich/);
    expect(criteriaError({ ...criteriaDraft(null), kind: 'framework' })).toMatch(/Rahmen/);
  });
});
