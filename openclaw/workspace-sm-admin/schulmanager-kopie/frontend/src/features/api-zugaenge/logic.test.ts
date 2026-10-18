import { describe, expect, it } from 'vitest';
import { cleanFilters, emptyDraft, parseList, relevantFilters, searchOptions, stepValid, toggle } from './logic';
import type { AreaInfo } from './types';

const area = (id: string, filters: AreaInfo['filters']): AreaInfo => ({
  id,
  label: id,
  description: '',
  filters,
  available: true,
  write: false,
  write_available: false,
});

describe('api-zugaenge logic', () => {
  it('relevantFilters nutzt nur Filter der gewählten Bereiche', () => {
    const areas = [area('timetable', ['classes', 'teachers', 'sites']), area('rooms', ['rooms', 'sites'])];
    expect(relevantFilters(areas, ['rooms'])).toEqual(['rooms', 'sites']);
    expect(relevantFilters(areas, ['timetable', 'rooms'])).toEqual(['classes', 'teachers', 'rooms', 'sites']);
    expect(relevantFilters(areas, [])).toEqual([]);
  });
  it('toggle und cleanFilters', () => {
    expect(toggle(['a'], 'b')).toEqual(['a', 'b']);
    expect(toggle(['a', 'b'], 'a')).toEqual(['b']);
    expect(cleanFilters({ classes: ['5a'], rooms: [], teachers: ['X'] }, ['classes', 'rooms'])).toEqual({ classes: ['5a'] });
  });
  it('parseList entfernt Leerwerte und Doppelte', () => {
    expect(parseList('10.0.0.1, 10.0.0.1\n192.168.0.0/16;;')).toEqual(['10.0.0.1', '192.168.0.0/16']);
  });
  it('searchOptions sucht in Kürzel und Name', () => {
    const opts = [
      { id: '5a', name: 'Klasse 5a' },
      { id: 'MUS', name: 'Frau Muster' },
    ];
    expect(searchOptions(opts, 'mus').map((o) => o.id)).toEqual(['MUS']);
    expect(searchOptions(opts, '', 1)).toHaveLength(1);
  });
  it('stepValid', () => {
    const d = emptyDraft({ expires: 90, rate: 60 });
    expect(stepValid(0, d)).toBe(false);
    expect(stepValid(0, { ...d, name: 'App' })).toBe(true);
    expect(stepValid(1, d)).toBe(false);
    expect(stepValid(1, { ...d, areas: ['timetable'] })).toBe(true);
  });
});
