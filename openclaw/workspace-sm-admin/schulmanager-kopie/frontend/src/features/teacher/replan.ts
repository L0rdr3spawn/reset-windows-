/**
 * Neuplanungs-Jobs (`kind: "replan_teacher"`) – reine Hilfsfunktionen (testbar, ohne React).
 */
import type { ReplanJob } from './types';

/** Status, in denen ein Job noch läuft. */
export const JOB_RUNNING: ReadonlySet<string> = new Set(['queued', 'pending', 'running', 'applying']);

export function jobTeacher(j: Pick<ReplanJob, 'replan' | 'params'>): string | undefined {
  const fromParams = j.params?.teacher_id;
  return j.replan?.teacher_id ?? (typeof fromParams === 'string' ? fromParams : undefined);
}

/** Letzter Neuplanungs-Job dieser Lehrkraft: laufend vor fertig (noch nicht übernommen), neuester zuerst. */
export function pickReplanJob(jobs: readonly ReplanJob[], teacherId: string): ReplanJob | null {
  const mine = jobs
    .filter((j) => j.kind === 'replan_teacher' && jobTeacher(j) === teacherId)
    .sort((a, b) => String(b.created_at ?? '').localeCompare(String(a.created_at ?? '')));
  return mine.find((j) => JOB_RUNNING.has(j.status)) ?? mine.find((j) => j.status === 'done') ?? null;
}
