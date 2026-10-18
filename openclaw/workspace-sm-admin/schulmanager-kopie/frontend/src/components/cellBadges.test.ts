import { describe, expect, it } from 'vitest';
import { groupLabel, groupLinks, type CellLink } from './CellBadges';

const ha = (n: number): CellLink => ({ kind: 'ha', label: 'HA', to: `/kursraeume/1?aufgabe=${n}` });

describe('CellBadges', () => {
  it('ordnet Hausaufgaben vor Prüfungen vor Abwesenheit', () => {
    const links: CellLink[] = [
      { kind: 'absent', label: 'krank', to: '/krankmeldungen' },
      { kind: 'exam', label: 'Test', to: '/klausuren?klausur=1' },
      ha(1),
      ha(2),
    ];
    const g = groupLinks(links);
    expect(g.map((x) => x.kind)).toEqual(['ha', 'exam', 'absent']);
    expect(g[0].items).toHaveLength(2);
  });
  it('ordnet alle Arten in fester Reihenfolge', () => {
    const l = (kind: CellLink['kind']): CellLink => ({ kind, label: 'x', to: '' });
    const g = groupLinks([l('absent'), l('duty'), l('event'), l('missing'), l('support'), l('makeup'), l('exam'), l('ha')]);
    expect(g.map((x) => x.kind)).toEqual(['ha', 'exam', 'makeup', 'support', 'missing', 'event', 'duty', 'absent']);
  });
  it('beschriftet Nachteilsausgleich und fehlende Kinder mit Zähler', () => {
    expect(groupLabel('support', [{ kind: 'support', label: 'NTA', to: '' }])).toBe('NTA 1');
    expect(groupLabel('missing', [{ kind: 'missing', label: 'fehlt', to: '' }, { kind: 'missing', label: 'fehlt', to: '' }])).toBe('fehlt 2');
  });
  it('zählt mehrere Einträge einer Art', () => {
    expect(groupLabel('ha', [ha(1), ha(2)])).toBe('HA 2');
    const t: CellLink = { kind: 'exam', label: 'Test', to: 'a' };
    const k: CellLink = { kind: 'exam', label: 'Klausur', to: 'b' };
    expect(groupLabel('exam', [t, t])).toBe('Test 2');
    expect(groupLabel('exam', [t, k])).toBe('Prüfungen 2');
  });
});
