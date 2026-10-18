/** Hinweis bei Klausuren/Tests: Schüler/innen mit Nachteilsausgleich (nur Art, Minuten, Fächer, Hilfsmittel). */
import { useApi } from '../../hooks/useApi';
import { can } from '../../lib/permissions';
import { useUser } from '../../context/AuthContext';
import { supportApi, type ExamHintStudent } from './supportApi';

/** Lädt die Hinweise für den Zeitraum; Personen ohne Recht `support.hints` bekommen eine leere Liste (ohne Anfrage). */
export function useExamHints(from: string, to: string, wanted = true): Record<string, ExamHintStudent[]> {
  const user = useUser();
  const enabled = wanted && can(user, 'support.hints');
  const q = useApi((signal) => supportApi.examHints(from, to, signal), [from, to], { live: ['student_support', 'support_catalog', 'exams', 'courses'], enabled });
  return enabled ? (q.data?.hints ?? {}) : {};
}

export function ExamHint({ students }: { students: ExamHintStudent[] | undefined }) {
  if (!students?.length) return null;
  return (
    <div className="small exam-hint" role="note">
      <strong>Nachteilsausgleich ({students.length}):</strong>{' '}
      {students.map((s, i) => (
        <span key={s.student_id}>
          {i > 0 && '; '}
          {s.name}: {s.summary}
        </span>
      ))}
    </div>
  );
}
