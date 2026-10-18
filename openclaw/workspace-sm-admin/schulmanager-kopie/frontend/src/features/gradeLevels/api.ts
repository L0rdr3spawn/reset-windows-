import { http } from '../../api/client';
import type { GradeProfile } from '../../api/types';
import type {
  CreateClassesResult,
  CurriculumImpact,
  DeleteClassesResult,
  ImpactResponse,
  MatrixResponse,
  MigrationPreview,
  ProfileImpact,
  ProfileInput,
  ProfilesResponse,
  SubjectImpact,
} from './types';

const enc = encodeURIComponent;

export const gradeLevelsApi = {
  // Jahrgänge
  profiles: (signal?: AbortSignal) => http.get<ProfilesResponse>('/grade-profiles', undefined, { signal }),
  matrix: (signal?: AbortSignal) => http.get<MatrixResponse>('/grade-profiles/matrix', undefined, { signal }),
  createProfile: (body: ProfileInput) => http.post<GradeProfile & { classes: string[] }>('/grade-profiles', body),
  updateProfile: (id: string, body: ProfileInput) => http.put<GradeProfile>(`/grade-profiles/${enc(id)}`, body),
  assign: (classIds: string[], profileId: string | null) => http.post<{ changed: string[] }>('/grade-profiles/assign', { class_ids: classIds, profile_id: profileId }),
  profileImpact: (id: string, signal?: AbortSignal) => http.get<ProfileImpact>(`/grade-profiles/${enc(id)}/impact`, undefined, { signal }),
  deleteProfile: (id: string, opts: { moveTo?: string | null; deleteCurriculum?: boolean }) =>
    http.del<{ deleted: string; moved_classes: string[]; removed_curriculum: string | null }>(`/grade-profiles/${enc(id)}`, {
      query: { move_to: opts.moveTo || undefined, delete_curriculum: opts.deleteCurriculum ? 1 : undefined },
    }),
  migrationPreview: (signal?: AbortSignal) => http.get<MigrationPreview>('/grade-profiles/migration', undefined, { signal }),
  migrate: () => http.post<MigrationPreview>('/grade-profiles/migration', {}),
  // Stundentafeln und Fächer
  curriculumImpact: (id: string, signal?: AbortSignal) => http.get<CurriculumImpact>(`/curricula/${enc(id)}/impact`, undefined, { signal }),
  subjectImpact: (id: string, signal?: AbortSignal) => http.get<SubjectImpact>(`/subjects/${enc(id)}/impact`, undefined, { signal }),
  derive: (body: { base: string; name: string; entries?: { subject: string; hours: number; double?: boolean }[] | null; profile_id?: string | null }) =>
    http.post<import('../../api/types').Curriculum>('/curricula/derive', body),
  // Klassenstufen (Klassen anlegen/löschen)
  impact: (classIds: string[], signal?: AbortSignal) => http.get<ImpactResponse>('/grade-levels/impact', { classes: classIds.join(',') }, { signal }),
  createClasses: (grade: number, body: { names: string[]; copy_from?: string | null; create_courses?: boolean; profile?: string | null }) =>
    http.post<CreateClassesResult>(`/grade-levels/${grade}/classes`, body),
  deleteClasses: (classIds: string[], moveStudentsTo: string | null) =>
    http.post<DeleteClassesResult>('/grade-levels/delete-classes', { class_ids: classIds, move_students_to: moveStudentsTo }),
};
