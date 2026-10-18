/** Lehrkraft: Schüler/in wählen und Lernstand, Lernplan und Abzeichen bearbeiten. */
import { ErrorBox, Field, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { compApi, type Overview } from './api';
import { StudentPanel } from './StudentPanel';

export function StudentTab({ classId, studentId, onSelect }: { classId: string | null; studentId: string | null; onSelect: (classId: string | null, studentId: string | null) => void }) {
  const q = useApi<Overview>((signal) => compApi.overview({ class_id: classId ?? undefined }, signal), [classId], { live: ['competency'] });
  const data = q.data;
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!data) return <Loading />;
  if (!data.classes.length) return <p className="muted">Für Sie sind keine Klassen mit Schüler/innen sichtbar.</p>;
  const cls = data.class?.id ?? data.classes[0]?.id ?? null;
  const students = data.students;
  const current = students.find((s) => s.id === studentId) ?? null;
  return (
    <div className="stack">
      <div className="cp-filters">
        <Field label="Klasse" htmlFor="cp-st-class">
          <select id="cp-st-class" value={cls ?? ''} onChange={(e) => onSelect(e.target.value, null)}>
            {data.classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Schüler/in" htmlFor="cp-st-student">
          <select id="cp-st-student" value={current?.id ?? ''} onChange={(e) => onSelect(cls, e.target.value || null)}>
            <option value="">Auswählen …</option>
            {students.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
                {s.support ? ` (${s.support} Unterstützung)` : ''}
              </option>
            ))}
          </select>
        </Field>
      </div>
      {current ? <StudentPanel studentId={current.id} /> : <p className="muted">Bitte eine Schülerin oder einen Schüler wählen.</p>}
    </div>
  );
}
