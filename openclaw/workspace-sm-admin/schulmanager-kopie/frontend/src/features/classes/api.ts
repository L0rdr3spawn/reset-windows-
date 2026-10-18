/**
 * Endpunkte der Klassen-Seite (§10.2). Zurücknehmen eines Ausfalls über das bestehende `DELETE /absences/{id}`.
 */
import { http } from '../../api/client';
import { absences as absencesApi } from '../../api/endpoints';
import type {
  ClassCurriculum,
  ClassCurriculumResult,
  ClassDetail,
  CurriculumRow,
  ClassListResponse,
  ClassPatch,
  ClassPatchResult,
  ClassWeek,
  AccountOptionsBody,
  ClassCreateBody,
  CreateStudentsResult,
  NewStudentBody,
  NotTakingPlaceBody,
  NotTakingPlaceResult,
} from './types';

const enc = encodeURIComponent;

/** Fehlende Listen robust auffüllen (Antwort des parallel entstandenen Backends). */
function normDetail(d: ClassDetail): ClassDetail {
  return {
    ...d,
    class: { ...d.class, unavailable: d.class.unavailable ?? [] },
    subjects: d.subjects ?? [],
    teachers: d.teachers ?? [],
    students: d.students ?? null,
  };
}

function normWeek(w: ClassWeek): ClassWeek {
  return {
    ...w,
    period_times: w.period_times ?? [],
    absences: w.absences ?? [],
    days: (w.days ?? []).map((d) => ({ ...d, holiday: d.holiday ?? null, cells: d.cells ?? [] })),
  };
}

export const classesApi = {
  /** Suche (Name/Klassenleitung/Raum) und Standortfilter; sortiert natürlich nach Klasse */
  list: (q: { q?: string; site?: string }, signal?: AbortSignal) =>
    http.get<ClassListResponse>('/classes', { q: q.q?.trim() || undefined, site: q.site || undefined }, { signal }),
  get: async (id: string, signal?: AbortSignal) => normDetail(await http.get<ClassDetail>(`/classes/${enc(id)}`, undefined, { signal })),
  /** Klassenraum/Klassenleitung setzen (`masterdata.edit`), Planungsfelder (`timetable.edit`, R3); `force` übernimmt 409 */
  patch: async (id: string, body: ClassPatch, opts: { force?: boolean } = {}): Promise<ClassPatchResult> => {
    const r = await http.patch<ClassPatchResult>(`/classes/${enc(id)}`, body, opts.force ? { query: { force: 1 } } : {});
    return { ...r, warnings: r?.warnings ?? [], skipped: r?.skipped ?? [], moved_lessons: r?.moved_lessons ?? 0 };
  },
  /** Wochenplan der Kalenderwoche, in der `date` liegt */
  week: async (id: string, date: string, signal?: AbortSignal) => normWeek(await http.get<ClassWeek>(`/classes/${enc(id)}/week`, { date }, { signal })),
  /** „Findet nicht statt“ bzw. „Klasse ist nicht da“ – mit `dry_run: true` nur Vorschau */
  notTakingPlace: async (id: string, body: NotTakingPlaceBody): Promise<NotTakingPlaceResult> => {
    const r = await http.post<NotTakingPlaceResult>(`/classes/${enc(id)}/not-taking-place`, body);
    return { ...r, summary: r?.summary ?? '', preview: (r?.preview ?? []).map((d) => ({ ...d, changes: d.changes ?? [] })) };
  },
  /** Stundentafel der Klasse (eigene oder die des Jahrgangs) */
  curriculum: (id: string, signal?: AbortSignal) => http.get<ClassCurriculum>(`/classes/${enc(id)}/curriculum`, undefined, { signal }),
  /** Eigene Stundentafel speichern (leer = Jahrgangs-Stundentafel verwenden) */
  putCurriculum: (id: string, rows: CurriculumRow[]) =>
    http.put<ClassCurriculumResult>(`/classes/${enc(id)}/curriculum`, {
      entries: rows.map((r) => ({ subject: r.subject, hours: r.hours, double: r.double })),
    }),
  /** Ausfall zurücknehmen */
  withdraw: (absenceId: string) => absencesApi.remove(absenceId),
  /** Klasse komplett anlegen (§11.3) – mit `dry_run: true` nur Vorschau */
  create: async (body: ClassCreateBody) => normCreate(await http.post<CreateStudentsResult>('/classes', body)),
  /** Schüler/innen nachlegen (gleiches Format) */
  addStudents: async (id: string, body: AccountOptionsBody & { students: NewStudentBody[] }) =>
    normCreate(await http.post<CreateStudentsResult>(`/classes/${enc(id)}/students`, body)),
};

function normCreate(r: CreateStudentsResult): CreateStudentsResult {
  return {
    ...r,
    warnings: r.warnings ?? [],
    accounts: r.accounts ?? [],
    linked_parents: r.linked_parents ?? [],
    students: (r.students ?? []).map((s) => ({ ...s, parent_accounts: s.parent_accounts ?? [] })),
    letter_batch: r.letter_batch ?? null,
    email: r.email ?? null,
  };
}
