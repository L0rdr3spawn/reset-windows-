/**
 * Lernaktivitäten im Kursraum und im Chat: Abstimmung, Umfrage, Fragensammlung, Selbsttest
 * (`schulmanager/server/routes/features_learning_*.py`, Doku: docs/LERNAKTIVITAETEN.md).
 */
import { API_BASE, http } from '../../api/client';
import type { FormField } from '../formulare/api';

// ------------------------------------------------------------------------------------------ Abstimmung
export type PollResults = 'live' | 'after_vote' | 'after_end';

export interface PollState {
  id: number;
  option_count: number;
  multiple: boolean;
  max_choices: number | null;
  anonymous: boolean;
  results: PollResults;
  ends_at: string | null;
  closed: boolean;
  closed_at: string | null;
  voted: boolean;
  /** eigene Stimme (nur bei namentlichen Abstimmungen bekannt) */
  mine: number[];
  can_vote: boolean;
  show_results: boolean;
  counts: number[] | null;
  /** Zahl der Teilnehmenden, die abgestimmt haben */
  total: number | null;
  /** Namen je Antwort (nur namentliche Abstimmungen) */
  voters: Record<string, string[]> | null;
  created_by: number | null;
  created_at: string;
}

export interface ChannelPoll extends PollState {
  question: string;
  options: string[];
  editable: boolean;
}

export interface PollInput {
  question: string;
  options: string[];
  multiple: boolean;
  max_choices: number | null;
  anonymous: boolean;
  results: PollResults;
  ends_at: string | null;
}

/** Einstellungen einer Chat-Abstimmung – Frage und Antworten bleiben in der verschlüsselten Nachricht. */
export interface ChatPollMeta {
  option_count: number;
  multiple: boolean;
  max_choices: number | null;
  anonymous: boolean;
  results: PollResults;
  ends_at: string | null;
}

// ------------------------------------------------------------------------------------------ Umfrage
export type SurveyStatus = 'entwurf' | 'offen' | 'geschlossen';

export interface Survey {
  id: number;
  title: string;
  anonymous: boolean;
  status: SurveyStatus;
  state: SurveyStatus;
  closes_at: string | null;
  results_to_students: boolean;
  question_count: number;
  done: boolean;
  editable: boolean;
  response_count: number | null;
  results_visible: boolean;
  created_by: number | null;
  created_at: string;
  intro?: string;
  fields?: FormField[];
}

export interface SurveyInput {
  title: string;
  intro: string;
  fields: FormField[];
  anonymous: boolean;
  status: 'entwurf' | 'offen';
  closes_at: string | null;
  results_to_students: boolean;
}

export interface SurveyItemResult {
  id: string;
  type: string;
  label: string;
  answered: number;
  counts?: { option: string; count: number }[];
  mean?: number | null;
  min?: number | null;
  max?: number | null;
  texts?: string[];
}

export interface SurveyResults {
  survey: Survey;
  response_count: number;
  member_count: number | null;
  items: SurveyItemResult[];
  responses: { name: string; at: string; answers: Record<string, unknown> }[];
}

// ------------------------------------------------------------------------------------------ Fragen
export type QuestionType = 'single' | 'multi' | 'truefalse' | 'cloze' | 'matching' | 'numeric';

export interface QuestionOption {
  text: string;
  correct?: boolean;
  feedback?: string;
}

export interface QuestionData {
  type: QuestionType;
  text: string;
  points: number;
  feedback: string;
  category: string;
  options?: QuestionOption[];
  correct?: boolean;
  gaps?: string[][];
  case_sensitive?: boolean;
  pairs?: { left: string; right: string }[];
  value?: number;
  tolerance?: number;
  unit?: string;
}

/** Eingabe einer Frage: Zahlen dürfen als Text kommen (Dezimalkomma), der Server prüft. */
export type QuestionInput = Omit<QuestionData, 'value' | 'tolerance' | 'points'> & { value?: number | string; tolerance?: number | string; points: number | string };

export interface BankQuestion {
  id: number;
  type: QuestionType;
  category: string;
  title: string;
  points: number;
  data: QuestionData;
  used_in: { id: number; title: string }[];
  editable: boolean;
  created_at: string;
}

// ------------------------------------------------------------------------------------------ Selbsttest
export type TestStatus = 'entwurf' | 'offen' | 'geschlossen';
export type TestState = TestStatus | 'geplant';
export type ReviewMode = 'none' | 'score' | 'full';

export interface SelftestMine {
  attempts: number;
  running_attempt: number | null;
  best_attempt: number | null;
  last_attempt: number | null;
  best_points: number | null;
  best_percent: number | null;
  max_points: number | null;
  passed: boolean | null;
  done: boolean;
  attempts_left: number | null;
}

export interface Selftest {
  id: number;
  title: string;
  status: TestStatus;
  state: TestState;
  max_attempts: number | null;
  time_limit_min: number | null;
  shuffle_questions: boolean;
  shuffle_answers: boolean;
  immediate_feedback: boolean;
  review: ReviewMode;
  pass_percent: number | null;
  opens_at: string | null;
  closes_at: string | null;
  created_by: number | null;
  question_count: number;
  max_points: number;
  editable: boolean;
  description?: string;
  question_ids?: number[];
  attempt_count?: number;
  mine?: SelftestMine;
}

export interface SelftestInput {
  title: string;
  description: string;
  status: TestStatus;
  question_ids: number[];
  max_attempts: number | null;
  time_limit_min: number | null;
  shuffle_questions: boolean;
  shuffle_answers: boolean;
  immediate_feedback: boolean;
  review: ReviewMode;
  pass_percent: number | null;
  opens_at: string | null;
  closes_at: string | null;
}

export interface PublicQuestion {
  id: number;
  type: QuestionType;
  text: string;
  points: number;
  options?: { id: number; text: string }[];
  gaps?: number;
  lefts?: { id: number; text: string }[];
  rights?: { id: number; text: string }[];
  unit?: string;
}

export type Answer = number | number[] | boolean | string[] | Record<string, number> | string | null;

export interface CheckedView {
  fraction: number;
  correct: boolean;
  points: number;
  max: number;
  solution: { correct?: number[] | boolean; accepted?: string[][]; pairs?: { left: number; right: number }[]; value?: number; tolerance?: number; unit?: string };
  feedback: { general: string; options: Record<string, string> };
}

export interface Attempt {
  id: number;
  test_id: number;
  title: string;
  number: number;
  started_at: string;
  deadline_at: string | null;
  finished_at: string | null;
  state: 'running' | 'finished';
  immediate_feedback: boolean;
  time_left_s: number | null;
  answers: Record<string, Answer>;
  checked: Record<string, CheckedView>;
  running_points?: number;
  max_points: number;
  questions?: PublicQuestion[];
  result: null | {
    finished: boolean;
    points?: number;
    max_points?: number;
    percent?: number;
    passed?: boolean | null;
    rows?: { qid: number; points: number; max: number; fraction: number; answered: boolean; correct: boolean }[];
    details?: Record<string, CheckedView>;
  };
}

export interface TestResultRow {
  user_id: number;
  name: string;
  attempts: number;
  finished: number;
  running: boolean;
  best_points: number | null;
  best_percent: number | null;
  max_points: number | null;
  passed: boolean | null;
  last_at: string | null;
  per_question: Record<string, number>;
  attempt_ids: number[];
}

export interface TestResults {
  test: Omit<Selftest, 'max_points' | 'editable'>;
  max_points: number;
  students: TestResultRow[];
  questions: { qid: number; title: string; type: QuestionType; max: number; attempts: number; mean: number | null; correct_share: number | null }[];
}

const ch = (id: number) => `/channels/${id}`;

export const learnApi = {
  // Abstimmung
  polls: (cid: number, studentId?: string | null, signal?: AbortSignal) =>
    http.get<{ polls: ChannelPoll[]; can_create: boolean }>(`${ch(cid)}/polls`, { student_id: studentId ?? undefined }, { signal }),
  createPoll: (cid: number, body: PollInput) => http.post<ChannelPoll>(`${ch(cid)}/polls`, body),
  vote: (cid: number, pid: number, choices: number[]) => http.put<ChannelPoll>(`${ch(cid)}/polls/${pid}/vote`, { choices }),
  closePoll: (cid: number, pid: number) => http.post<ChannelPoll>(`${ch(cid)}/polls/${pid}/close`),
  deletePoll: (cid: number, pid: number) => http.del<unknown>(`${ch(cid)}/polls/${pid}`),
  chatVote: (chatId: number, messageId: number, choices: number[]) => http.put<PollState>(`/chats/${chatId}/messages/${messageId}/vote`, { choices }),
  chatClose: (chatId: number, messageId: number) => http.post<PollState>(`/chats/${chatId}/messages/${messageId}/poll/close`),
  // Umfrage
  surveys: (cid: number, signal?: AbortSignal) => http.get<{ surveys: Survey[]; can_create: boolean }>(`${ch(cid)}/surveys`, undefined, { signal }),
  survey: (cid: number, sid: number, signal?: AbortSignal) => http.get<Survey>(`${ch(cid)}/surveys/${sid}`, undefined, { signal }),
  createSurvey: (cid: number, body: SurveyInput) => http.post<Survey>(`${ch(cid)}/surveys`, body),
  patchSurvey: (cid: number, sid: number, body: Partial<Omit<SurveyInput, 'status'>> & { status?: SurveyStatus; clear_closes_at?: boolean }) => http.patch<Survey>(`${ch(cid)}/surveys/${sid}`, body),
  deleteSurvey: (cid: number, sid: number) => http.del<unknown>(`${ch(cid)}/surveys/${sid}`),
  respond: (cid: number, sid: number, answers: Record<string, unknown>) => http.post<{ done: boolean }>(`${ch(cid)}/surveys/${sid}/respond`, { answers }),
  surveyResults: (cid: number, sid: number, signal?: AbortSignal) => http.get<SurveyResults>(`${ch(cid)}/surveys/${sid}/results`, undefined, { signal }),
  surveyCsvUrl: (cid: number, sid: number) => `${API_BASE}${ch(cid)}/surveys/${sid}/export.csv`,
  // Fragensammlung
  questions: (cid: number, signal?: AbortSignal) => http.get<{ questions: BankQuestion[]; types: Record<string, string> }>(`${ch(cid)}/questions`, undefined, { signal }),
  createQuestion: (cid: number, body: QuestionInput) => http.post<BankQuestion>(`${ch(cid)}/questions`, body),
  updateQuestion: (cid: number, qid: number, body: QuestionInput) => http.put<BankQuestion>(`${ch(cid)}/questions/${qid}`, body),
  deleteQuestion: (cid: number, qid: number) => http.del<{ removed_from_tests: number }>(`${ch(cid)}/questions/${qid}`),
  importGift: (cid: number, gift: string) => http.post<{ created: number; errors: string[] }>(`${ch(cid)}/questions/import`, { gift }),
  exportGiftUrl: (cid: number, ids: number[] = []) => `${API_BASE}${ch(cid)}/questions/export.gift${ids.length ? `?ids=${ids.join(',')}` : ''}`,
  copyQuestions: (cid: number, fromChannelId: number, ids: number[]) => http.post<{ created: number }>(`${ch(cid)}/questions/copy`, { from_channel_id: fromChannelId, ids }),
  // Selbsttest
  tests: (cid: number, signal?: AbortSignal) => http.get<{ tests: Selftest[]; can_create: boolean }>(`${ch(cid)}/selftests`, undefined, { signal }),
  test: (cid: number, tid: number, signal?: AbortSignal) => http.get<Selftest>(`${ch(cid)}/selftests/${tid}`, undefined, { signal }),
  createTest: (cid: number, body: SelftestInput) => http.post<Selftest>(`${ch(cid)}/selftests`, body),
  patchTest: (cid: number, tid: number, body: Partial<SelftestInput> & { clear_max_attempts?: boolean; clear_time_limit?: boolean; clear_pass_percent?: boolean; clear_opens_at?: boolean; clear_closes_at?: boolean }) =>
    http.patch<Selftest>(`${ch(cid)}/selftests/${tid}`, body),
  deleteTest: (cid: number, tid: number) => http.del<unknown>(`${ch(cid)}/selftests/${tid}`),
  startAttempt: (cid: number, tid: number) => http.post<Attempt>(`${ch(cid)}/selftests/${tid}/attempts`),
  attempt: (cid: number, tid: number, aid: number, signal?: AbortSignal) => http.get<Attempt>(`${ch(cid)}/selftests/${tid}/attempts/${aid}`, undefined, { signal }),
  saveAnswer: (cid: number, tid: number, aid: number, questionId: number, answer: Answer) =>
    http.put<{ saved: boolean; checked?: CheckedView }>(`${ch(cid)}/selftests/${tid}/attempts/${aid}/answer`, { question_id: questionId, answer }),
  finishAttempt: (cid: number, tid: number, aid: number) => http.post<Attempt>(`${ch(cid)}/selftests/${tid}/attempts/${aid}/finish`),
  testResults: (cid: number, tid: number, signal?: AbortSignal) => http.get<TestResults>(`${ch(cid)}/selftests/${tid}/results`, undefined, { signal }),
  testCsvUrl: (cid: number, tid: number) => `${API_BASE}${ch(cid)}/selftests/${tid}/results.csv`,
};
