/**
 * Krankmeldungen von Schüler/innen (B-06): was die Oberfläche je Konto zeigt. Das Backend entscheidet
 * (`server/absence_access.py`), diese Hilfen blenden nur passend ein/aus.
 */
import type { StudentAbsence, StudentAbsenceAccess } from '../api/types';
import { addDays, dateRangeLabel, formatDate } from './dates';

/** Wer Gründe sieht – Text für die Hilfe an „vertraulich“ (A-58). */
export const REASON_AUDIENCE =
  'Gründe sehen nur die Schülerin bzw. der Schüler, die Eltern (bei Volljährigen nur mit Freigabe), die meldende Person, die Klassenleitung, das Sekretariat und die Schulleitung.';

/** Hilfe zur Liste je Konto (Personenkreis der eigenen Sicht; Schüler/innen in Du-Form). */
export function listHelp(access: StudentAbsenceAccess | null | undefined, pupil = false): string {
  if (!access) return REASON_AUDIENCE;
  const presence = access.subject_view === 'presence';
  if (access.family) {
    return pupil
      ? `Ihre Krankmeldungen sehen außer Ihnen nur Ihre Eltern (sind Sie volljährig, nur mit Ihrer Freigabe), die Klassenleitung, das Sekretariat und die Schulleitung, den Grund auch die meldende Person.${presence ? ' Fachlehrkräfte sehen nur, dass Sie heute in ihrer Stunde fehlen.' : ''}`
      : `Diese Krankmeldungen sehen nur die Eltern (bei Volljährigen nur mit Freigabe), das Kind selbst, die Klassenleitung, das Sekretariat und die Schulleitung, den Grund auch die meldende Person.${presence ? ' Fachlehrkräfte sehen nur, wer heute in ihrer Stunde fehlt.' : ''}`;
  }
  const subject = presence ? ' Fachlehrkräfte sehen nur, wer heute in ihrer Stunde fehlt.' : '';
  if (access.all) return `${REASON_AUDIENCE} Die technische Administration sieht keine Krankmeldungen.${subject}`;
  if (access.class_ids.length) {
    const today = presence ? ', heute außerdem, wer in Ihren Stunden fehlt' : '';
    return `Sie sehen die Krankmeldungen Ihrer Klasse ${access.class_ids.join(', ')} und Ihre eigenen Meldungen${today}. ${REASON_AUDIENCE}`;
  }
  return presence
    ? 'Sie sehen Ihre eigenen Meldungen und heute, wer in Ihren Stunden fehlt – ohne Grund, Status und Attest.'
    : 'Sie sehen nur Ihre eigenen Meldungen. Gründe, Status und Atteste sieht die Klassenleitung.';
}

/** Eltern: nur Kinder, deren Krankmeldungen sie sehen und melden dürfen (volljährige nur mit Freigabe, U-103). */
export function reportableChildren<T extends { id: string }>(children: readonly T[], access: StudentAbsenceAccess | null | undefined): T[] {
  if (!access?.family || !access.student_ids) return [...children];
  const ids = new Set(access.student_ids);
  return children.filter((c) => ids.has(c.id));
}

/** Neu laden, wenn sich Schulschalter, Klassenleitungen oder Elternfreigaben ändern (wer meldet/sieht, U-103). */
export const ACCESS_LIVE_SCOPES = ['settings', 'classes', 'parent_access'] as const;

/** Melden erlaubt: Recht des Kontos oder laut Backend (volljährig nach Geburtsdatum ohne Konto-Merkmal). */
export function mayReport(hasPermission: boolean, access: StudentAbsenceAccess | null | undefined): boolean {
  return hasPermission || !!access?.can_report;
}

/** Status „entschuldigt/unentschuldigt“ nur mit Berechtigung (Klassenleitung, Sekretariat, Schulleitung, Familie). */
export function canSeeStatus(access: StudentAbsenceAccess | null | undefined): boolean {
  return !!access && (access.all || access.family || access.class_ids.length > 0);
}

/** Melden: beliebiger Zeitraum oder nur die eigene Stunde (Fachlehrkraft: ein Tag, nicht in der Zukunft). */
export function reportMode(access: StudentAbsenceAccess | null | undefined, classId: string | null | undefined): 'range' | 'lesson' {
  if (!access || access.all || access.family) return 'range';
  if (!classId) return access.class_ids.length ? 'range' : 'lesson';
  return access.class_ids.includes(classId) ? 'range' : 'lesson';
}

/** Startdatum der Liste: Familien sehen das ganze Jahr (U-89), das Personal die letzten zwei Wochen. */
export function defaultListFrom(today: string, family: boolean): string {
  return addDays(today, family ? -365 : -14);
}

/** Frühester Tag für eine Meldung (Backend: höchstens `max_backdate_days` rückwirkend). */
export function minReportDate(today: string, access: StudentAbsenceAccess | null | undefined): string {
  return addDays(today, -(access?.max_backdate_days ?? 30));
}

/** Zeile in der Sicht „fehlt heute in meiner Stunde“? */
export function isPresence(a: Pick<StudentAbsence, 'view'>): boolean {
  return a.view === 'presence';
}

/**
 * Spaltenbreiten der Liste in px: alle Spalten fest, damit die Tabelle auf dem Handy im eigenen Rahmen waagerecht
 * scrollt, statt Namen zusammenzudrücken; am PC verteilt der Browser übrigen Platz anteilig.
 */
export const COLUMN_WIDTHS = { name: 180, range: 160, reason: 100, by: 120, status: 132, attest: 120 } as const;

/** Breite der Aktionsspalte (so viele Knöpfe, wie eine Zeile höchstens hat); 0 = Spalte ausblenden. */
export function actionsWidth(rows: readonly Pick<StudentAbsence, 'can_manage' | 'can_delete'>[], coarse: boolean): number {
  const n = rows.reduce((m, a) => Math.max(m, (a.can_manage ? 2 : 0) + (a.can_delete ? 1 : 0)), 0);
  if (!n) return 0;
  const button = coarse ? 44 : 32; // .btn-sm.btn-icon, auf Touch-Geräten 44 px (A-61)
  return n * button + (n - 1) * 8 + 26;
}

/** Attest-Spalte nur, wenn eine Zeile ein Attest braucht. */
export function needsAttestColumn(rows: readonly Pick<StudentAbsence, 'attest'>[]): boolean {
  return rows.some((a) => !!a.attest && a.attest.state !== 'nicht_noetig');
}

/** Kurzer Zeitraum für die Liste: im laufenden Jahr ohne Jahreszahl („08.10.–09.10.“), sonst vollständig. */
export function shortRange(from: string, to: string, today: string): string {
  const year = today.slice(0, 4);
  const dm = (iso: string) => formatDate(iso).slice(0, 6);
  if (from.slice(0, 4) === year && to.slice(0, 4) === year) return from === to ? dm(from) : `${dm(from)}–${dm(to)}`;
  if (from.slice(0, 4) === to.slice(0, 4)) return from === to ? formatDate(from) : `${dm(from)}–${formatDate(to)}`;
  return dateRangeLabel(from, to);
}
