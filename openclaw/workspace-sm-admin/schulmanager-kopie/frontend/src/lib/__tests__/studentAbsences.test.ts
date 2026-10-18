import { describe, expect, it } from 'vitest';
import type { StudentAbsenceAccess } from '../../api/types';
import { ACCESS_LIVE_SCOPES, actionsWidth, canSeeStatus, COLUMN_WIDTHS, defaultListFrom, isPresence, listHelp, mayReport, minReportDate, needsAttestColumn, REASON_AUDIENCE, reportableChildren, reportMode, shortRange } from '../studentAbsences';

const base: StudentAbsenceAccess = { all: false, family: false, can_report: true, class_ids: [], subject_view: 'none', max_days: 60, max_backdate_days: 30 };
const staff = { ...base, all: true };
const classTeacher = { ...base, class_ids: ['5a'] };
const subject = { ...base };
const family = { ...base, family: true };

describe('Krankmeldungen: Sichtbarkeit in der Oberfläche (B-06)', () => {
  it('zeigt „entschuldigt/unentschuldigt“ nur mit Berechtigung', () => {
    expect(canSeeStatus(staff)).toBe(true);
    expect(canSeeStatus(classTeacher)).toBe(true);
    expect(canSeeStatus(family)).toBe(true);
    expect(canSeeStatus(subject)).toBe(false);
    expect(canSeeStatus({ ...subject, subject_view: 'presence' })).toBe(false);
    expect(canSeeStatus(null)).toBe(false);
  });

  it('nennt im Hinweis „vertraulich“ den richtigen Personenkreis', () => {
    expect(REASON_AUDIENCE).toContain('Klassenleitung');
    expect(REASON_AUDIENCE).toContain('Sekretariat');
    expect(REASON_AUDIENCE).toContain('Schulleitung');
    expect(REASON_AUDIENCE).toContain('nur mit Freigabe');
    expect(REASON_AUDIENCE).not.toMatch(/Administration|Fachlehrkr/);
    expect(listHelp(staff)).toContain('technische Administration sieht keine');
    expect(listHelp(classTeacher)).toContain('5a');
    expect(listHelp(subject)).toContain('nur Ihre eigenen Meldungen');
    expect(listHelp({ ...subject, subject_view: 'presence' })).toContain('ohne Grund, Status und Attest');
  });

  it('Hilfe der Familie nennt Eltern und Kind, Schüler/innen in Sie-Form (die App siezt alle)', () => {
    const pupil = listHelp(family, true);
    const parent = listHelp(family);
    expect(pupil).toMatch(/^Ihre Krankmeldungen/);
    expect(pupil).toContain('Ihre Eltern');
    expect(pupil).not.toMatch(/\b(du|dich|dir|deine?)\b/i);
    expect(parent).toContain('das Kind selbst');
    expect(parent).toContain('bei Volljährigen nur mit Freigabe');
    for (const text of [pupil, parent]) {
      expect(text).toContain('meldende Person');
      expect(text).not.toContain('Fachlehrkräfte');
    }
    expect(listHelp({ ...family, subject_view: 'presence' }, true)).toContain('dass Sie heute in ihrer Stunde fehlen');
    expect(listHelp({ ...family, subject_view: 'presence' })).toContain('wer heute in ihrer Stunde fehlt');
    expect(listHelp({ ...classTeacher, subject_view: 'presence' })).toContain('heute außerdem, wer in Ihren Stunden fehlt');
    expect(listHelp(classTeacher)).not.toContain('heute außerdem');
  });

  it('Eltern melden nur für Kinder mit Freigabe (U-103)', () => {
    const kids = [{ id: 'S1' }, { id: 'S2' }];
    expect(reportableChildren(kids, { ...family, student_ids: ['S2'] })).toEqual([{ id: 'S2' }]);
    expect(reportableChildren(kids, { ...family, student_ids: [] })).toEqual([]);
    expect(reportableChildren(kids, family)).toEqual(kids); // älteres Backend ohne Feld
    expect(reportableChildren(kids, null)).toEqual(kids);
    expect(reportableChildren(kids, staff)).toEqual(kids);
  });

  it('Fachlehrkräfte melden nur die eigene Stunde, Klassenleitung beliebig', () => {
    expect(reportMode(staff, '7b')).toBe('range');
    expect(reportMode(family, null)).toBe('range');
    expect(reportMode(classTeacher, '5a')).toBe('range');
    expect(reportMode(classTeacher, null)).toBe('range');
    expect(reportMode(classTeacher, '7b')).toBe('lesson');
    expect(reportMode(subject, '5a')).toBe('lesson');
    expect(reportMode(subject, null)).toBe('lesson');
  });

  it('Familien sehen auch ältere Meldungen (U-89)', () => {
    expect(defaultListFrom('2026-10-12', true)).toBe('2025-10-12');
    expect(defaultListFrom('2026-10-12', false)).toBe('2026-09-28');
    expect(minReportDate('2026-10-12', staff)).toBe('2026-09-12');
  });

  it('erkennt die Zeile „fehlt heute in meiner Stunde“', () => {
    expect(isPresence({ view: 'presence' })).toBe(true);
    expect(isPresence({ view: 'own' })).toBe(false);
  });

  it('Spalten: Aktionen nur so breit wie nötig, Attest nur bei Bedarf, Tabelle passt an den PC', () => {
    expect(actionsWidth([], false)).toBe(0);
    expect(actionsWidth([{ can_manage: false, can_delete: false }], false)).toBe(0);
    const own = actionsWidth([{ can_manage: false, can_delete: true }], false);
    const full = actionsWidth([{ can_manage: false, can_delete: true }, { can_manage: true, can_delete: true }], false);
    expect(own).toBe(58);
    expect(full).toBe(3 * 32 + 2 * 8 + 26);
    expect(actionsWidth([{ can_manage: true, can_delete: true }], true)).toBe(3 * 44 + 2 * 8 + 26);
    expect(needsAttestColumn([{ attest: null }, { attest: undefined }])).toBe(false);
    expect(needsAttestColumn([{ attest: { state: 'nicht_noetig' } as never }])).toBe(false);
    expect(needsAttestColumn([{ attest: { state: 'fehlt' } as never }])).toBe(true);
    // Sekretariat/Klassenleitung mit allen Spalten: höchstens so breit wie die Liste am PC (1280 px, ~950 px Platz)
    const sum = Object.values(COLUMN_WIDTHS).reduce((a, b) => a + b, 0) + full;
    expect(sum).toBeLessThanOrEqual(950);
  });

  it('kürzt Zeiträume im laufenden Jahr', () => {
    expect(shortRange('2026-10-08', '2026-10-09', '2026-10-11')).toBe('08.10.–09.10.');
    expect(shortRange('2026-10-09', '2026-10-09', '2026-10-11')).toBe('09.10.');
    expect(shortRange('2025-11-03', '2025-11-05', '2026-10-11')).toBe('03.11.–05.11.2025');
    expect(shortRange('2025-12-22', '2026-01-08', '2026-10-11')).toBe('22.12.2025 – 08.01.2026');
  });
});

describe('Krankmeldungen: Prüfung R2-B (2. Durchgang)', () => {
  it('Volljährige nach Geburtsdatum melden auch ohne Konto-Recht, wenn das Backend es erlaubt', () => {
    expect(mayReport(false, { ...family, can_report: true })).toBe(true);
    expect(mayReport(false, { ...family, can_report: false })).toBe(false);
    expect(mayReport(false, null)).toBe(false);
    expect(mayReport(true, null)).toBe(true);
  });

  it('lädt die Rechte neu, wenn ein volljähriges Kind die Freigabe ändert', () => {
    expect(ACCESS_LIVE_SCOPES).toContain('parent_access');
    expect(ACCESS_LIVE_SCOPES).toContain('settings');
  });
});
