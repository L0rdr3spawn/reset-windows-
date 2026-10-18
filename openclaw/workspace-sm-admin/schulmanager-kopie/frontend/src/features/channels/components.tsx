/** Kleine Bausteine der Kursräume: Symbole, Status-Abzeichen, Rollen-Abzeichen. */
import type { ReactNode } from 'react';
import type { ChannelRole, ItemState, ItemType, LessonStatus, SubmissionStatus } from './types';
import { lessonTone, STATE_TEXT, stateTone, submissionTone, SUBMISSION_TEXT, toneClass } from './logic';

const GLYPHS: Record<ItemType | 'folder' | 'folderOpen' | 'board' | 'room', string> = {
  folder: 'M3 6a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z',
  folderOpen: 'M3 6a1 1 0 0 1 1-1h5l2 2h8a1 1 0 0 1 1 1v2H7l-4 9zM7 10h15l-3 9H3',
  file: 'M14 3H7a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V7zM14 3v4h4M9 13h6M9 17h6',
  link: 'M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7',
  text: 'M4 5h16M4 10h16M4 15h10M4 20h7',
  assignment: 'M9 3h6l1 2h3v16H5V5h3zM9 12l2 2 4-4',
  board: 'M4 4h16v12H8l-4 4zM8 9h8M8 12h5',
  room: 'M3 21V8l9-5 9 5v13M9 21v-6h6v6',
};

/** Symbol für Materialart/Ordner (dekorativ, Bedeutung steht immer auch als Text daneben). */
export function Glyph({ name, size = 20, className }: { name: keyof typeof GLYPHS; size?: number; className?: string }) {
  return (
    <svg
      className={`kr-glyph${className ? ` ${className}` : ''}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={GLYPHS[name]} />
    </svg>
  );
}

export function StateBadge({ state, label }: { state: ItemState | undefined; label?: ReactNode }) {
  if (!state) return null;
  return <span className={toneClass(stateTone(state))}>{label ?? STATE_TEXT[state]}</span>;
}

export function SubmissionBadge({ status, label }: { status: SubmissionStatus | undefined; label?: string }) {
  if (!status) return null;
  return <span className={toneClass(submissionTone(status))}>{label ?? SUBMISSION_TEXT[status]}</span>;
}

export function LessonStatusBadge({ status, changes }: { status: LessonStatus; changes: string[] }) {
  if (status === 'normal' && !changes.length) return null;
  const text = changes.length ? changes.join(' · ') : status;
  return <span className={toneClass(lessonTone(status))}>{text}</span>;
}

const ROLE_TEXT: Record<ChannelRole, string> = { teacher: 'Lehrende', student: 'Teilnehmende', supervisor: 'nur lesen', parent: 'Eltern – nur lesen' };

export function RoleBadge({ role }: { role: ChannelRole | null }) {
  if (!role) return null;
  const cls = role === 'teacher' ? 'badge badge-primary' : role === 'supervisor' ? 'badge badge-warning' : 'badge';
  return <span className={cls}>{ROLE_TEXT[role]}</span>;
}

export function NewBadge({ n, label = 'neu' }: { n?: number; label?: string }) {
  if (n === 0) return null;
  return (
    <span className="badge badge-info">
      {n !== undefined && n > 1 ? `${n} ` : ''}
      {label}
    </span>
  );
}
