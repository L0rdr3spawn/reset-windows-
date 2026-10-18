/**
 * Reine Hilfsfunktionen der Schüler-Selbstbedienung (ohne React, getestet in students.test.ts).
 */
import type { AttestState, StudentAbsence } from '../../api/types';
import type { ChildRef, DocCategory, DocStatus, StudentDocument } from './types';

export const CATEGORY_LABELS: Record<DocCategory, string> = {
  attest: 'Ärztliches Attest',
  entschuldigung: 'Entschuldigung',
  beurlaubung: 'Antrag auf Beurlaubung (unterschrieben)',
  einverstaendnis: 'Einverständniserklärung',
  sonstiges: 'Sonstiges Dokument',
};

export const STATUS_LABELS: Record<DocStatus, string> = { eingegangen: 'eingereicht', geprueft: 'genehmigt', abgelehnt: 'abgelehnt' };

const ATTEST_BADGE: Record<AttestState, string> = {
  nicht_noetig: '',
  erforderlich: 'badge-warning',
  fehlt: 'badge-danger',
  eingereicht: 'badge-info',
  geprueft: 'badge-success',
  abgelehnt: 'badge-danger',
};

const STATUS_BADGE: Record<DocStatus, string> = { eingegangen: 'badge-info', geprueft: 'badge-success', abgelehnt: 'badge-danger' };

export function attestBadgeClass(state: AttestState | undefined): string {
  return state ? ATTEST_BADGE[state] ?? '' : '';
}

export function docStatusBadgeClass(status: DocStatus): string {
  return STATUS_BADGE[status] ?? '';
}

/** Attest-Hinweis anzeigen? (nicht bei „kein Attest nötig“) */
export function showAttest(a: Pick<StudentAbsence, 'attest'>): boolean {
  return !!a.attest && a.attest.state !== 'nicht_noetig';
}

/** Darf zu dieser Krankmeldung ein Attest hochgeladen werden (fällig, fehlt oder abgelehnt)? */
export function attestUploadWanted(a: Pick<StudentAbsence, 'attest'>): boolean {
  const s = a.attest?.state;
  return s === 'erforderlich' || s === 'fehlt' || s === 'abgelehnt';
}

/** „1., 2. Std.“ bzw. „ganztägig“ */
export function periodsLabel(periods: number[] | undefined): string {
  if (!periods?.length) return 'ganztägig';
  return `${[...periods].sort((a, b) => a - b).map((p) => `${p + 1}.`).join(', ')} Std.`;
}

/** Krankmeldungen: fehlende Atteste zuerst, dann neueste. */
export function sortAbsences<T extends Pick<StudentAbsence, 'date_from' | 'attest'> & { id: number | string }>(rows: T[]): T[] {
  const rank = (a: T) => (a.attest?.state === 'fehlt' ? 0 : a.attest?.state === 'abgelehnt' ? 1 : 2);
  return [...rows].sort((a, b) => rank(a) - rank(b) || b.date_from.localeCompare(a.date_from) || String(b.id).localeCompare(String(a.id)));
}

/** Prüf-Eingang: eingegangene zuerst (älteste oben = zuerst bearbeiten), danach bearbeitete (neueste oben). */
export function sortInbox(docs: StudentDocument[]): StudentDocument[] {
  const open = docs.filter((d) => d.status === 'eingegangen').sort((a, b) => (a.created_at ?? '').localeCompare(b.created_at ?? ''));
  const done = docs.filter((d) => d.status !== 'eingegangen').sort((a, b) => (b.handled_at ?? b.created_at ?? '').localeCompare(a.handled_at ?? a.created_at ?? ''));
  return [...open, ...done];
}

/** Auswahl des Kindes: gespeicherte Wahl, wenn noch gültig, sonst das erste Kind. */
export function pickChild(children: Pick<ChildRef, 'id'>[], stored: string | null | undefined): string | null {
  if (stored && children.some((c) => c.id === stored)) return stored;
  return children[0]?.id ?? null;
}

/** Zeitraum für „Krank melden“: heute (bzw. nächster Schultag, wenn heute kein Unterricht ist) bis `days` Schultage. */
export function reportStart(today: string, todayIsSchoolDay: boolean, nextSchoolDay: string | null): string {
  return todayIsSchoolDay || !nextSchoolDay ? today : nextSchoolDay;
}

/** Zähler für den Menü-Badge: Personal offene Dokumente + fehlende Atteste, Familien fehlende Atteste. */
export function badgeCount(summary: { open: number; attest_missing: number } | undefined, family: boolean): number {
  if (!summary) return 0;
  return family ? summary.attest_missing : summary.open + summary.attest_missing;
}

/** Dateiname/Titel kürzen (Handy) ohne Wörter zu zerreißen. */
export function shorten(text: string, max = 60): string {
  if (text.length <= max) return text;
  const cut = text.slice(0, max - 1);
  const space = cut.lastIndexOf(' ');
  return `${(space > max * 0.6 ? cut.slice(0, space) : cut).trimEnd()}…`;
}
