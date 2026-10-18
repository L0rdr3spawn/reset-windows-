import { describe, expect, it } from 'vitest';
import { reportLine } from './AbsenceHistory';
import { APP_NAME } from '../../brand';

describe('reportLine', () => {
  it('nennt Zeitpunkt, Person, Rolle und Kanal (volle Sicht)', () => {
    const t = reportLine({ kind_label: 'krank', reported_at: '2026-10-12T05:41:00Z', reported_by_name: 'Frau Müller', reported_by_role: 'Eltern', channel_label: `online im ${APP_NAME}` });
    expect(t).toContain('krank gemeldet am');
    expect(t).toContain('von Frau Müller (Eltern)');
    expect(t).toContain(`online im ${APP_NAME}`);
  });
  it('Fachlehrkraft: nur Zeitpunkt und Kanal, keine Person', () => {
    const t = reportLine({ kind_label: 'abwesend', reported_at: '2026-10-12T05:41:00Z', channel_label: 'telefonisch' });
    expect(t).toContain('abwesend gemeldet am');
    expect(t).not.toContain(' von ');
    expect(t).toContain('telefonisch');
  });
});
