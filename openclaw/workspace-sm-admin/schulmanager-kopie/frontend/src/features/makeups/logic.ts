/**
 * Reine Hilfsfunktionen der Nachschreibtermine (ohne React, getestet in makeups.test.ts).
 */
import type { MakeupAppointment, MakeupAttestState, MakeupRow } from './api';

export const ATTEST_BADGE: Record<MakeupAttestState, string> = {
  fehlt: 'badge-danger',
  eingereicht: 'badge-info',
  genehmigt: 'badge-success',
  abgelehnt: 'badge-danger',
  nicht_noetig: '',
};

/** Offene und festgelegte zuerst (nach Klausurdatum), Erledigtes/Entfallenes unten. */
export function sortRows<T extends Pick<MakeupRow, 'status' | 'exam_date' | 'student_name'>>(rows: readonly T[]): T[] {
  const rank = (r: T) => (r.status === 'offen' ? 0 : r.status === 'angesetzt' ? 1 : 2);
  return [...rows].sort((a, b) => rank(a) - rank(b) || a.exam_date.localeCompare(b.exam_date) || a.student_name.localeCompare(b.student_name, 'de'));
}

export interface ExamGroup {
  exam_id: string;
  rows: MakeupRow[];
}

/** Zeilen je Klausur gruppieren (Reihenfolge der ersten Zeile bleibt erhalten). */
export function groupByExam(rows: readonly MakeupRow[]): ExamGroup[] {
  const out: ExamGroup[] = [];
  const by = new Map<string, ExamGroup>();
  for (const r of rows) {
    let g = by.get(r.exam_id);
    if (!g) {
      g = { exam_id: r.exam_id, rows: [] };
      by.set(r.exam_id, g);
      out.push(g);
    }
    g.rows.push(r);
  }
  return out;
}

/** „3.–4. Std.“ bzw. „3. Std.“ (0-basierter Beginn) */
export function periodSpan(start: number, length: number): string {
  return length > 1 ? `${start + 1}.–${start + length}. Std.` : `${start + 1}. Std.`;
}

export function appointmentText(a: Pick<MakeupAppointment, 'start' | 'length' | 'time' | 'room'>): string {
  return [periodSpan(a.start, a.length), a.time || null, a.room ? `Raum ${a.room}` : null].filter(Boolean).join(' · ');
}

/** Braucht die Familie noch etwas zu tun (Attest einreichen)? */
export function attestActionNeeded(r: Pick<MakeupRow, 'status' | 'attest' | 'level'>): boolean {
  return r.level !== 'teacher' && (r.status === 'offen' || r.status === 'angesetzt') && r.attest.missing;
}

/** Zeilen, für die die Lehrkraft einen Termin festlegen muss. */
export function needsDate(rows: readonly MakeupRow[]): MakeupRow[] {
  return rows.filter((r) => r.can_schedule && r.status === 'offen');
}

/** Zeilen, die ein Vorschlag abdeckt (bei „eigene Stunde“ nur die Kinder, die dort sitzen). */
export function rowsForSuggestion<T extends Pick<MakeupRow, 'student_id'>>(rows: readonly T[], s: { student_ids: readonly string[] }): T[] {
  return rows.filter((r) => s.student_ids.includes(r.student_id));
}

/** Kurzbeschriftung eines Vorschlags: „Eigene Stunde“, „Freistunde“ oder „Randstunde“. */
export function suggestionKind(s: { kind: 'unterricht' | 'frei'; slot?: 'luecke' | 'rand' }): string {
  return s.kind === 'unterricht' ? 'Eigene Stunde' : s.slot === 'luecke' ? 'Freistunde' : 'Randstunde';
}
