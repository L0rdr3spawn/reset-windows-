import { describe, expect, it } from 'vitest';
import { examDetailLink, examRoomLink, examTarget } from './examRoom';

describe('examTarget', () => {
  it('führt mit Kursraum-Zugang direkt in den Kursraum', () => {
    expect(examTarget({ id: 'KA1', kind: 'klausur', channel_id: 7 }, '2026-10-15')).toBe('/kursraeume/7?klausur=KA1&datum=2026-10-15&art=klausur');
    expect(examTarget({ id: 'KA1', kind: 'test', channel_id: 7 }, '2026-10-15', 's1')).toContain('&child=s1');
  });
  it('ohne Zugang bleibt das Klausur-Detail, Nachschreiben nutzt die Klausur-ID', () => {
    expect(examTarget({ id: 'KA1', kind: 'klausur' }, '2026-10-15')).toBe(examDetailLink('KA1', '2026-10-15'));
    expect(examTarget({ id: 'nm3', kind: 'nachschreiben' }, '2026-10-20')).toBeUndefined();
    expect(examTarget({ id: 'nm3', kind: 'nachschreiben', exam_id: 'KA1', channel_id: 7 }, '2026-10-20')).toBe(
      examRoomLink(7, { id: 'KA1', kind: 'nachschreiben', date: '2026-10-20' }),
    );
  });
});
