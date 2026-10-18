import { describe, expect, it } from 'vitest';
import type { AttestInfo } from '../../api/types';
import {
  attestBadgeClass,
  attestUploadWanted,
  badgeCount,
  docStatusBadgeClass,
  periodsLabel,
  pickChild,
  reportStart,
  shorten,
  showAttest,
  sortAbsences,
  sortInbox,
} from './logic';
import type { StudentDocument } from './types';

const attest = (state: AttestInfo['state']): AttestInfo => ({ required: state !== 'nicht_noetig', school_days: 3, due: null, state, label: state, missing: state === 'fehlt' });

const doc = (id: number, status: StudentDocument['status'], created: string, handled: string | null = null): StudentDocument => ({
  id,
  student_id: 'S1',
  student_name: 'Mia',
  class_id: '5a',
  absence_id: null,
  category: 'attest',
  category_label: 'Ärztliches Attest',
  title: `Dok ${id}`,
  file: null,
  paper: false,
  status,
  status_label: status,
  note: '',
  uploaded_by_name: 'Eltern',
  own: false,
  handled_by_name: '',
  handled_at: handled,
  created_at: created,
  can_handle: true,
  can_delete: false,
});

describe('Schüler-Selbstbedienung – Logik', () => {
  it('Attest-Badges und Upload-Bedarf', () => {
    expect(attestBadgeClass('fehlt')).toBe('badge-danger');
    expect(attestBadgeClass('geprueft')).toBe('badge-success');
    expect(attestBadgeClass(undefined)).toBe('');
    expect(docStatusBadgeClass('eingegangen')).toBe('badge-info');
    expect(showAttest({ attest: attest('nicht_noetig') })).toBe(false);
    expect(showAttest({ attest: attest('erforderlich') })).toBe(true);
    expect(attestUploadWanted({ attest: attest('fehlt') })).toBe(true);
    expect(attestUploadWanted({ attest: attest('abgelehnt') })).toBe(true);
    expect(attestUploadWanted({ attest: attest('eingereicht') })).toBe(false);
    expect(attestUploadWanted({})).toBe(false);
  });

  it('Stunden-Beschriftung', () => {
    expect(periodsLabel([])).toBe('ganztägig');
    expect(periodsLabel(undefined)).toBe('ganztägig');
    expect(periodsLabel([2, 0])).toBe('1., 3. Std.');
  });

  it('Sortierung: fehlende Atteste zuerst, Prüf-Eingang älteste offene zuerst', () => {
    const rows = [
      { id: 1, date_from: '2026-10-01', attest: attest('geprueft') },
      { id: 2, date_from: '2026-09-20', attest: attest('fehlt') },
      { id: 3, date_from: '2026-10-05', attest: attest('nicht_noetig') },
      { id: 4, date_from: '2026-09-25', attest: attest('abgelehnt') },
    ];
    expect(sortAbsences(rows).map((r) => r.id)).toEqual([2, 4, 3, 1]);
    const docs = [doc(1, 'geprueft', '2026-10-01', '2026-10-02'), doc(2, 'eingegangen', '2026-10-05'), doc(3, 'eingegangen', '2026-10-03'), doc(4, 'abgelehnt', '2026-10-01', '2026-10-06')];
    expect(sortInbox(docs).map((d) => d.id)).toEqual([3, 2, 4, 1]);
  });

  it('Kindauswahl, Meldestart, Badge, Kürzen', () => {
    expect(pickChild([{ id: 'A' }, { id: 'B' }], 'B')).toBe('B');
    expect(pickChild([{ id: 'A' }], 'X')).toBe('A');
    expect(pickChild([], null)).toBeNull();
    expect(reportStart('2026-10-10', false, '2026-10-12')).toBe('2026-10-12');
    expect(reportStart('2026-10-09', true, '2026-10-12')).toBe('2026-10-09');
    expect(badgeCount({ open: 2, attest_missing: 3 }, false)).toBe(5);
    expect(badgeCount({ open: 2, attest_missing: 3 }, true)).toBe(3);
    expect(badgeCount(undefined, false)).toBe(0);
    expect(shorten('kurz')).toBe('kurz');
    expect(shorten('Ein sehr langer Titel für ein Attest vom Kinderarzt mit vielen Wörtern darin', 40)).toBe('Ein sehr langer Titel für ein Attest…');
  });
});
