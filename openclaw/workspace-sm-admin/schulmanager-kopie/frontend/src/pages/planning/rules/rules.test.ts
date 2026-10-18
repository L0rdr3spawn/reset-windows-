import { describe, expect, it } from 'vitest';
import {
  applyTemplate,
  compareStats,
  differsFromTemplate,
  exportPayload,
  levelForWeight,
  parseImport,
  rangesText,
  sameDraft,
  scopeText,
  visibleRuleIds,
  weightFor,
  type RuleDef,
  type RuleItem,
  type RulesState,
  type RuleTemplate,
} from './model';

const item = (level: RuleItem['level'] = 'wichtig', extra: Partial<RuleItem> = {}): RuleItem => ({ level, weight: null, params: {}, overrides: [], ...extra });

const def = (id: string, extra: Partial<RuleDef> = {}): RuleDef => ({
  id,
  group: 'klassen',
  title: id,
  text: '',
  control: 'level',
  weight_key: id,
  base: 10,
  scope: ['grades'],
  report: '',
  hard: false,
  hard_text: '',
  advanced: false,
  entity: 'class',
  params: [],
  relevant: true,
  requires_text: '',
  visible: true,
  weight: 10,
  affects: 1,
  affects_text: '',
  violations: null,
  ...extra,
});

describe('Stufen und Gewichte', () => {
  it('Stufe → Gewicht ist ein Vielfaches des Grundgewichts, eigener Wert gewinnt', () => {
    expect(weightFor(100, 'wichtig')).toBe(100);
    expect(weightFor(100, 'nett')).toBe(25);
    expect(weightFor(100, 'sehr_wichtig')).toBe(400);
    expect(weightFor(100, 'muss')).toBe(2000);
    expect(weightFor(100, 'aus')).toBe(0);
    expect(weightFor(100, 'aus', 7)).toBe(7);
  });
  it('Gewicht → Stufe: exakt oder nächste Stufe mit „eigener Wert“', () => {
    expect(levelForWeight(100, 0)).toEqual({ level: 'aus', exact: true });
    expect(levelForWeight(100, 400)).toEqual({ level: 'sehr_wichtig', exact: true });
    expect(levelForWeight(100, 300)).toEqual({ level: 'sehr_wichtig', exact: false });
    expect(levelForWeight(6, 150)).toEqual({ level: 'muss', exact: false });
    expect(levelForWeight(0.6, 0.6)).toEqual({ level: 'wichtig', exact: true });
  });
});

describe('Vorlagen', () => {
  const tmpl: RuleTemplate = {
    id: 'gym',
    name: 'Gymnasium',
    description: '',
    builtin: true,
    show: ['class_gap'],
    items: { class_gap: { level: 'sehr_wichtig', overrides: [{ level: 'nett', grades: [11, 12, 13] } as never] } },
  };
  it('übernimmt Stufen und Ausnahmen, behält Bausteine ohne Vorgabe', () => {
    const out = applyTemplate({ class_gap: item('wichtig'), teacher_gap: item('nett') }, tmpl);
    expect(out.class_gap?.level).toBe('sehr_wichtig');
    expect(out.class_gap?.overrides).toHaveLength(1);
    expect(out.class_gap?.overrides[0]).toMatchObject({ level: 'nett', grades: [11, 12, 13], classes: [], weeks: [], note: '' });
    expect(out.teacher_gap).toEqual(item('nett'));
  });
  it('erkennt Abweichungen von der Vorlage', () => {
    const fallback = item();
    expect(differsFromTemplate(item('sehr_wichtig', { overrides: [{ level: 'nett', grades: [11, 12, 13], classes: [], subjects: [], teachers: [], weeks: [], rhythm: null, note: '', params: {} }] }), tmpl.items.class_gap, fallback)).toBe(false);
    expect(differsFromTemplate(item('muss'), tmpl.items.class_gap, fallback)).toBe(true);
  });
  it('zeigt ohne „Erweitert“ nur relevante Bausteine der Vorlage plus Geändertes', () => {
    const state: Pick<RulesState, 'catalog' | 'items' | 'templates' | 'profile'> = {
      profile: 'gym',
      templates: [tmpl],
      catalog: [def('class_gap'), def('teacher_gap'), def('site_change', { relevant: false }), def('position', { advanced: true })],
      items: { class_gap: item('sehr_wichtig'), teacher_gap: item('wichtig'), site_change: item('muss'), position: item('wichtig') },
    };
    expect([...visibleRuleIds(state, false)]).toEqual(['class_gap']);
    expect([...visibleRuleIds({ ...state, items: { ...state.items, teacher_gap: item('nett') } }, false)]).toEqual(['class_gap', 'teacher_gap']);
    expect([...visibleRuleIds(state, true)]).toHaveLength(4);
  });
});

describe('Texte und Vergleich', () => {
  it('fasst Zahlen zu Bereichen zusammen', () => {
    expect(rangesText([5, 6, 7, 10])).toBe('5–7, 10');
    expect(scopeText({ grades: [11, 12, 13], classes: ['7a'], subjects: [], teachers: [] }, { classes: new Map([['7a', 'Klasse 7a']]) })).toBe('Jahrgang 11–13 · Klasse Klasse 7a');
    expect(scopeText({ grades: [], classes: [], subjects: [], teachers: [] })).toBe('alle');
  });
  it('vergleicht Entwürfe unabhängig von Reihenfolge', () => {
    const a = { profile: 'x', advanced: false, items: { b: item('nett'), a: item('muss') } };
    const b = { profile: 'x', advanced: false, items: { a: item('muss'), b: item('nett') } };
    expect(sameDraft(a, b)).toBe(true);
    expect(sameDraft(a, { ...b, items: { ...b.items, a: item('wichtig') } })).toBe(false);
  });
  it('rechnet Vorher/Nachher (negativ = besser)', () => {
    const rows = compareStats({ class_gaps: 5, unplaced_hours: 2, core_late: 1 }, { class_gaps: 3.5, unplaced: 0, core_late: 1 });
    const by = Object.fromEntries(rows.map((r) => [r.key, r]));
    expect(by.class_gaps?.delta).toBe(-1.5);
    expect(by.unplaced_hours).toMatchObject({ before: 2, after: 0, delta: -2 });
    expect(by.core_late?.delta).toBe(0);
    expect(by.site_changes?.delta).toBeNull();
  });
});

describe('Export und Import', () => {
  it('exportiert nur eigene Vorlagen und liest die Datei wieder ein', () => {
    const state = {
      profile: 'gym',
      items: { class_gap: item('muss') },
      templates: [
        { id: 'gym', name: 'G', description: '', builtin: true, show: [], items: {} },
        { id: 'eigene-1', name: 'Eigene', description: '', builtin: false, show: [], items: {} },
      ],
    };
    const text = exportPayload(state, 'Testschule');
    const parsed = parseImport(text);
    expect(parsed.profile).toBe('gym');
    expect(parsed.items.class_gap?.level).toBe('muss');
    expect(parsed.templates.map((t) => t.id)).toEqual(['eigene-1']);
  });
  it('lehnt fremde Dateien ab', () => {
    expect(() => parseImport('{')).toThrow(/JSON/);
    expect(() => parseImport('{"foo": 1}')).toThrow(/schulmanager-regeln/);
    expect(() => parseImport('{"format":"schulmanager-regeln"}')).toThrow(/items/);
  });
});
