/**
 * Kleine gemeinsame Bausteine des Formular-Baukastens: Status-Abzeichen und Liste von Einreichungen.
 */
import { Icon } from '../../components/Icon';
import { formatDate } from '../../lib/dates';
import type { FormStatus, Submission } from './api';
import { STATUS_TONE } from './logic';
import './formulare.css';

export function StatusBadge({ status, label }: { status: FormStatus; label: string }) {
  return <span className={`badge badge-${STATUS_TONE[status]}`}>{label}</span>;
}

export function SubmissionList({ rows, onOpen, empty, showSubmitter = false }: { rows: Submission[]; onOpen: (id: number) => void; empty: string; showSubmitter?: boolean }) {
  if (!rows.length) return <p className="muted small" style={{ margin: 0 }}>{empty}</p>;
  return (
    <ul className="fm-list" aria-label="Einreichungen">
      {rows.map((s) => (
        <li key={s.id}>
          <button type="button" className={`fm-row${s.overdue ? ' is-overdue' : ''}`} onClick={() => onOpen(s.id)}>
            <span className="fm-row-main">
              <strong>{s.template_title}</strong>
              <span className="small muted">
                {s.student_name ? `${s.student_name}${s.class_id ? ` (${s.class_id})` : ''} · ` : ''}
                {showSubmitter ? `${s.submitted_by_name} · ` : ''}
                {formatDate((s.created_at ?? '').slice(0, 10))}
                {s.current_step ? ` · wartet auf: ${s.current_step}` : ''}
              </span>
            </span>
            <span className="fm-row-side">
              {s.can_decide && <span className="badge badge-primary">Ihre Entscheidung</span>}
              {s.overdue && <span className="badge badge-danger">überfällig</span>}
              <StatusBadge status={s.status} label={s.status_label} />
              <Icon name="eye" />
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
