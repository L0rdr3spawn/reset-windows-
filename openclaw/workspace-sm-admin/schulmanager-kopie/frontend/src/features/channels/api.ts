/**
 * Endpunkte der Kursräume (§9.4). Dateien werden vorher über `uploadFile` (`src/api/files.ts`) hochgeladen –
 * Zwecke `channel_material` (Material, Aufgaben-Anhänge, Rückmeldungen), `submission` (Abgaben), `channel_post`.
 */
import { buildQuery, http } from '../../api/client';
import type { TimetableView } from '../../api/types';
import { onSessionReset } from '../../lib/session';
import type { RubricFill } from './assign/types';
import type {
  Channel,
  ChannelDetail,
  ClassAbsences,
  ClassEvent,
  ClassEventInput,
  ClassOverview,
  ChannelKind,
  ChannelListResponse,
  Folder,
  Item,
  ItemType,
  LessonsResponse,
  MemberCandidate,
  MembersResponse,
  MySubmissionResponse,
  OverviewResponse,
  Post,
  PostsResponse,
  Submission,
  SubmissionsResponse,
  VisibilityInput,
} from './types';

export interface ItemInput extends Partial<VisibilityInput> {
  type: ItemType;
  title?: string;
  folder_id?: number | null;
  body?: string;
  url?: string | null;
  file_id?: string | null;
  attachment_ids?: string[];
  due_at?: string | null;
  allow_late?: boolean;
  lesson_material?: boolean;
  material_date?: string | null;
  submittable?: boolean;
  /** Klassenraum: als angeheftete Infokarte (Textseite) anlegen */
  info_card?: boolean;
}

export interface LessonLogEntry {
  date: string;
  period: number;
  length: number;
  period_label: string | null;
  time: string | null;
  subject: string | null;
  subject_name: string | null;
  teachers: string[];
  status: string | null;
  changes: string[];
  /** Thema/Hausaufgabe aus dem Klassenbuch – nur für Lehrende/Schulleitung (sonst leer) */
  topic: string;
  homework: string;
  materials: (Item & { viewed?: boolean })[];
  /** an diesem Tag gestellte Aufgaben (Link zur Hausaufgabe) */
  assignments?: (Item & { viewed?: boolean })[];
  /** Schüler/innen, Eltern: nur wenn gefehlt (Label krank / beurlaubt / gefehlt), sonst nichts */
  attendance?: 'absent' | null;
  attendance_label?: string;
  /** Material dieses Tages, das noch nicht geöffnet wurde */
  unviewed?: number;
}

export interface LessonLog {
  from: string;
  to: string;
  lessons: LessonLogEntry[];
  other_materials: (Item & { viewed?: boolean })[];
  student_id?: string | null;
  /** Klassenbuch-Inhalte sichtbar (Lehrende, Schulleitung) */
  register?: boolean;
  unviewed?: number;
}

export interface FeedbackInput {
  feedback: string;
  grade: string;
  status: 'bewertet' | 'zurueckgegeben';
  file_ids?: string[];
  points?: number | null;
  rubric?: RubricFill | null;
  /** Gruppenabgabe: `self` = Einzelanpassung nur für diese Person */
  scope?: 'group' | 'self';
  overwrite_individual?: boolean;
  /** Überarbeitung anfordern: neue Frist */
  revision_due_at?: string | null;
}

export type ItemPatch = Partial<Omit<ItemInput, 'type'>> & { position?: number };

const base = (id: number) => `/channels/${id}`;

export const channelsApi = {
  list: (q: { q?: string; kind?: ChannelKind | ''; all?: boolean; archived?: boolean; studentId?: string | null } = {}, signal?: AbortSignal) =>
    http.get<ChannelListResponse>(
      '/channels',
      { q: q.q, kind: q.kind || undefined, all: q.all ? 1 : undefined, archived: q.archived ? 1 : undefined, student_id: q.studentId || undefined },
      { signal },
    ),
  overview: (signal?: AbortSignal) => http.get<OverviewResponse>('/channels/overview', undefined, { signal }),
  create: (body: { title: string; description?: string; students_can_post?: boolean; students_can_reply?: boolean }) =>
    http.post<Channel>('/channels', body),
  get: (id: number, signal?: AbortSignal, studentId?: string | null) =>
    http.get<ChannelDetail>(base(id), { student_id: studentId || undefined }, { signal }),
  patch: (id: number, body: Partial<{ title: string; description: string; students_can_post: boolean; students_can_reply: boolean; progress_parents: boolean; archived: boolean }>) =>
    http.patch<Channel>(base(id), body),
  remove: (id: number, force = false) => http.del<{ deleted: number }>(base(id), { query: { force: force ? 1 : undefined } }),
  seen: (id: number, studentId?: string | null) =>
    http.post<{ last_seen_at: string }>(`${base(id)}/seen${buildQuery({ student_id: studentId || undefined })}`, {}),

  members: (id: number, signal?: AbortSignal) => http.get<MembersResponse>(`${base(id)}/members`, undefined, { signal }),
  addMembers: (id: number, userIds: number[], role: 'teacher' | 'student') =>
    http.post<{ added: number[]; updated: number[] }>(`${base(id)}/members`, { user_ids: userIds, role }),
  removeMember: (id: number, userId: number) => http.del<{ removed: number }>(`${base(id)}/members/${userId}`),
  readmit: (id: number, userId: number) => http.del<{ readmitted: number }>(`${base(id)}/excluded/${userId}`),
  candidates: (id: number, q: string, role: 'teacher' | 'student' = 'student', signal?: AbortSignal) =>
    http.get<{ candidates: MemberCandidate[] }>(`${base(id)}/member-candidates`, { q, role }, { signal }),

  createFolder: (id: number, body: { name: string; parent_id?: number | null; hidden?: boolean } & Partial<VisibilityInput>) =>
    http.post<Folder>(`${base(id)}/folders`, body),
  /** Ordner-Upload: Struktur anlegen → `{pfad: ordner_id}` (oberste Ordner tragen die Sichtbarkeit) */
  createFolderTree: (id: number, body: { parent_id?: number | null; paths: string[] } & Partial<VisibilityInput>) =>
    http.post<{ folders: Record<string, number>; roots: Folder[] }>(`${base(id)}/folders/tree`, body),
  patchFolder: (id: number, folderId: number, body: Partial<{ name: string; parent_id: number | null; position: number; hidden: boolean }> & Partial<VisibilityInput>) =>
    http.patch<Folder>(`${base(id)}/folders/${folderId}`, body),
  deleteFolder: (id: number, folderId: number, force = false) =>
    http.del<{ deleted: number; folders: number; items: number }>(`${base(id)}/folders/${folderId}`, { query: { force: force ? 1 : undefined } }),

  /** Bereich „Klasse“ (nur Klassenräume): Ansprechpersonen, Termine, Pläne */
  classOverview: (id: number, signal?: AbortSignal, studentId?: string | null) =>
    http.get<ClassOverview>(`${base(id)}/klasse`, { student_id: studentId || undefined }, { signal }),
  classAbsences: (id: number, signal?: AbortSignal) => http.get<ClassAbsences>(`${base(id)}/klasse/absences`, undefined, { signal }),
  classPlan: (id: number, date: string, signal?: AbortSignal) => http.get<TimetableView>(`${base(id)}/klasse/plan`, { date }, { signal }),
  addClassEvent: (id: number, body: ClassEventInput) => http.post<ClassEvent>(`${base(id)}/klasse/termine`, body),
  deleteClassEvent: (id: number, eventId: string) => http.del<{ deleted: string }>(`${base(id)}/klasse/termine/${encodeURIComponent(eventId)}`),

  createItem: (id: number, body: ItemInput) => http.post<Item>(`${base(id)}/items`, body),
  lessonLog: (id: number, q: { from?: string; days?: number } = {}, signal?: AbortSignal) =>
    http.get<LessonLog>(`${base(id)}/unterricht`, q, { signal }),
  markViewed: (id: number, itemId: number) => http.post<{ ok: boolean }>(`${base(id)}/items/${itemId}/viewed`, {}),
  createFileItems: (id: number, body: { folder_id?: number | null; file_ids: string[] } & Partial<VisibilityInput>) =>
    http.post<{ items: Item[] }>(`${base(id)}/items/files`, body),
  item: (id: number, itemId: number, signal?: AbortSignal, studentId?: string | null) =>
    http.get<Item>(`${base(id)}/items/${itemId}`, { student_id: studentId || undefined }, { signal }),
  patchItem: (id: number, itemId: number, body: ItemPatch) => http.patch<Item>(`${base(id)}/items/${itemId}`, body),
  deleteItem: (id: number, itemId: number, force = false) =>
    http.del<{ deleted: number; trashed?: boolean }>(`${base(id)}/items/${itemId}`, { query: { force: force ? 1 : undefined } }),
  setVisibility: (id: number, itemIds: number[], vis: VisibilityInput, folderIds: number[] = []) =>
    http.post<{ items: Item[]; folders: Folder[]; changed: number[]; changed_folders: number[] }>(`${base(id)}/items/visibility`, {
      item_ids: itemIds,
      folder_ids: folderIds,
      ...vis,
    }),
  copy: (id: number, body: { target_channel_id: number; target_folder_id?: number | null; item_ids?: number[]; folder_ids?: number[]; keep_visibility?: boolean }) =>
    http.post<{ target_channel_id: number; items: number; folders: number }>(`${base(id)}/copy`, body),
  lessons: (id: number, q: { from?: string; days?: number; all?: boolean } = {}, signal?: AbortSignal) =>
    http.get<LessonsResponse>(`${base(id)}/lessons`, { from: q.from, days: q.days, all: q.all ? 1 : undefined }, { signal }),

  mySubmission: (id: number, itemId: number, signal?: AbortSignal, studentId?: string | null) =>
    http.get<MySubmissionResponse>(`${base(id)}/items/${itemId}/submission`, { student_id: studentId || undefined }, { signal }),
  submit: (id: number, itemId: number, body: { text: string; file_ids: string[] }) =>
    http.put<Submission>(`${base(id)}/items/${itemId}/submission`, body),
  withdraw: (id: number, itemId: number) => http.del<{ deleted: boolean }>(`${base(id)}/items/${itemId}/submission`),
  submissions: (id: number, itemId: number, signal?: AbortSignal) =>
    http.get<SubmissionsResponse>(`${base(id)}/items/${itemId}/submissions`, undefined, { signal }),
  feedback: (id: number, submissionId: number, body: FeedbackInput) =>
    http.put<Submission>(`${base(id)}/submissions/${submissionId}/feedback`, body),

  posts: (id: number, before?: number | null, signal?: AbortSignal, studentId?: string | null) =>
    http.get<PostsResponse>(`${base(id)}/posts`, { before: before ?? undefined, student_id: studentId || undefined }, { signal }),
  createPost: (id: number, body: { body: string; parent_id?: number | null; attachment_ids?: string[] }) =>
    http.post<Post>(`${base(id)}/posts`, body),
  patchPost: (id: number, postId: number, body: { body?: string; pinned?: boolean }) =>
    http.patch<Post>(`${base(id)}/posts/${postId}`, body),
  deletePost: (id: number, postId: number) => http.del<{ deleted: number; count: number }>(`${base(id)}/posts/${postId}`),
};


let overviewCache: { at: number; promise: Promise<OverviewResponse> } | null = null;
onSessionReset(() => { overviewCache = null; }); // Übersicht gehört zum Konto (U-01)

/** Übersicht für mehrere Kacheln derselben Startseite nur einmal laden (kurz zwischengespeichert). */
export function overviewShared(force = false): Promise<OverviewResponse> {
  const now = Date.now();
  if (!force && overviewCache && now - overviewCache.at < 800) return overviewCache.promise;
  const promise = channelsApi.overview();
  overviewCache = { at: now, promise };
  promise.catch(() => {
    if (overviewCache?.promise === promise) overviewCache = null;
  });
  return promise;
}
