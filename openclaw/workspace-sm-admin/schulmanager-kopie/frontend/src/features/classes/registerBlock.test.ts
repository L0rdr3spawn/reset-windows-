import { describe, expect, it } from 'vitest';
import { periodsLabel, rowFromBlock } from './RegisterPage';

describe('Doppelstunde im Klassenbuch', () => {
  it('beschriftet Stundenfolgen', () => {
    expect(periodsLabel([2])).toBe('3. Stunde');
    expect(periodsLabel([2, 3])).toBe('3.–4. Stunde');
  });
  it('noch nichts eingetragen', () => {
    expect(rowFromBlock([null, null], [2, 3]).status).toBeNull();
  });
  it('fehlt in beiden Stunden = ganz, sonst nur die genannte', () => {
    const a = { status: 'absent' as const };
    expect(rowFromBlock([a, a], [2, 3])).toMatchObject({ status: 'absent', partial: null });
    expect(rowFromBlock([{ status: 'present' }, a], [2, 3])).toMatchObject({ status: 'absent', partial: [3] });
  });
  it('zu spät zählt in der ersten Stunde, früher gegangen ab der zweiten', () => {
    expect(rowFromBlock([{ status: 'late', minutes: 7 }, { status: 'present' }], [2, 3])).toMatchObject({ status: 'present', late: true, minutes: 7, early: null });
    expect(rowFromBlock([{ status: 'left' }, { status: 'left', gone: true }], [2, 3])).toMatchObject({ status: 'present', late: false, early: 3 });
  });
});
