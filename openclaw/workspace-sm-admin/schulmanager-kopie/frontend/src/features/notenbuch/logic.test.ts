import { describe, expect, it } from 'vitest';
import {
  categoryOptions,
  cellText,
  fmtNum,
  fmtWeight,
  gradeTone,
  moveTarget,
  orderedColumns,
  parseDecimal,
  parseQuick,
  quickLabels,
  shortDate,
  termText,
  weightShare,
} from './logic';
import type { Category, Item, Scale } from './types';

const cat = (id: number, parent: number | null, name: string, weight = 1, depth = 0): Category => ({ id, parent_id: parent, name, weight, position: id, depth });
const item = (id: number, category: number | null, date: string, title = `L${id}`): Item => ({
  id,
  category_id: category,
  title,
  date,
  weight: 1,
  max_points: null,
  key_id: '',
  position: id,
  released: false,
  makeup_date: '',
  source_type: '',
  source_id: '',
  source_label: '',
});

describe('Zahlen', () => {
  it('deutsches Komma, Platzhalter', () => {
    expect(fmtNum(2.333, 2)).toBe('2,33');
    expect(fmtNum(2, 0)).toBe('2');
    expect(fmtNum(null)).toBe('–');
    expect(fmtNum(Number.NaN)).toBe('–');
    expect(fmtWeight(2.5)).toBe('2,5');
    expect(fmtWeight(2)).toBe('2');
    expect(parseDecimal('17,5')).toBe(17.5);
    expect(parseDecimal('')).toBeNull();
    expect(parseDecimal('abc')).toBeNull();
  });
});

describe('Farbton', () => {
  it('Noten, Punkte, Prozent, Bestanden', () => {
    expect(gradeTone('2+', 'note6')).toBe('good');
    expect(gradeTone('4-', 'note6')).toBe('ok');
    expect(gradeTone('5', 'note6')).toBe('bad');
    expect(gradeTone('12', 'punkte15')).toBe('good');
    expect(gradeTone('4', 'punkte15')).toBe('bad');
    expect(gradeTone('50', 'prozent')).toBe('ok');
    expect(gradeTone('nicht bestanden', 'bestanden')).toBe('bad');
    expect(gradeTone('', 'note6')).toBe('none');
    expect(gradeTone('gut', 'verbal')).toBe('none');
  });
});

describe('Kürzel-Eingabe', () => {
  it('Status nur bei Zahlenskalen', () => {
    expect(parseQuick('e', 'note6')).toEqual({ value: '', status: 'entschuldigt' });
    expect(parseQuick('U', 'punkte15')).toEqual({ value: '', status: 'unentschuldigt' });
    expect(parseQuick('n', 'prozent')).toEqual({ value: '', status: 'nachschreiben' });
    expect(parseQuick('a', 'custom')).toEqual({ value: 'a', status: '' });        // „A“ kann eine Note sein
    expect(parseQuick('b', 'bestanden')).toEqual({ value: 'b', status: '' });
    expect(parseQuick(' 2+ ', 'note6')).toEqual({ value: '2+', status: '' });
    expect(parseQuick('-', 'note6')).toEqual({ value: '', status: '' });
    expect(parseQuick('', 'note6')).toEqual({ value: '', status: '' });
  });
  it('Zellentext zeigt Kürzel für Status', () => {
    const e = { value: '3', label: '3', status: '' as const, note: '', makeup_date: '', invalid: false };
    expect(cellText(e)).toBe('3');
    expect(cellText({ ...e, value: '', status: 'entschuldigt' })).toBe('e');
    expect(cellText({ ...e, value: '', status: 'nachschreiben' })).toBe('n');
    expect(cellText(undefined)).toBe('');
  });
});

describe('Spaltenfolge', () => {
  const cats = [cat(1, null, 'Schriftlich'), cat(2, null, 'Sonstige'), cat(3, 2, 'Tests', 1, 1)];
  it('nach Leistungsart (Baumfolge), dann Datum', () => {
    const cols = orderedColumns(cats, [item(5, 3, '2026-10-03'), item(6, 1, '2026-11-01'), item(7, 1, '2026-10-01'), item(8, null, '2026-09-01')]);
    expect(cols.map((c) => c.item.id)).toEqual([8, 7, 6, 5]);
    expect(cols[3].path).toBe('Sonstige › Tests');
    expect(cols[0].path).toBe('');
  });
  it('Auswahl mit Einrückung und Anteile', () => {
    expect(categoryOptions(cats).map((o) => o.label)).toEqual(['Schriftlich', 'Sonstige', ' Tests']);
    const share = weightShare([cat(1, null, 'a', 60), cat(2, null, 'b', 40), cat(3, 2, 'c', 5, 1)]);
    expect(share[1]).toBe(60);
    expect(share[2]).toBe(40);
    expect(share[3]).toBe(100);
  });
});

describe('Tastatur', () => {
  it('Enter und Pfeile bewegen in der Spalte', () => {
    expect(moveTarget(0, 2, 'Enter', 5)).toEqual([1, 2]);
    expect(moveTarget(4, 2, 'ArrowDown', 5)).toEqual([4, 2]);
    expect(moveTarget(2, 1, 'ArrowUp', 5)).toEqual([1, 1]);
    expect(moveTarget(0, 1, 'ArrowUp', 5)).toEqual([0, 1]);
    expect(moveTarget(2, 1, 'Enter', 5, true)).toEqual([1, 1]);
    expect(moveTarget(2, 1, 'a', 5)).toEqual([2, 1]);
  });
});

describe('Sonstiges', () => {
  const scale = (kind: Scale['kind'], labels: string[] = []): Scale => ({ id: kind, name: kind, kind, builtin: true, numeric: kind !== 'verbal', higher_better: false, labels: labels.map((label, i) => ({ label, value: i })) });
  it('Schnellwahl je Skala', () => {
    expect(quickLabels(scale('note6'))).toContain('2+');
    expect(quickLabels(scale('punkte15'))).toHaveLength(16);
    expect(quickLabels(scale('custom', ['A', 'B']))).toEqual(['A', 'B']);
    expect(quickLabels(scale('verbal'))).toEqual([]);
    expect(quickLabels(null)).toEqual([]);
  });
  it('Datum und Halbjahr', () => {
    expect(shortDate('2026-10-05')).toBe('05.10.');
    expect(shortDate('')).toBe('');
    expect(termText('2026-2')).toBe('2026/27, 2. Halbjahr');
    expect(termText('x')).toBe('x');
  });
});
