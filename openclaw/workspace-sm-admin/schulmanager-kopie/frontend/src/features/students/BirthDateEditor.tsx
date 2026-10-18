/**
 * Geburtsdatum einer Schülerin/eines Schülers setzen (Recht „Geburtsdatum pflegen“, `PUT /students/{id}/birth-date`).
 * Daraus folgt die Volljährigkeit: Eltern-Freigaben, eigene Krankmeldung. Eingehängt in der Klassen-Schülerliste und im
 * Stammdaten-Dialog „Schüler/innen“.
 */
import { useId, useState } from 'react';
import { http } from '../../api/client';
import { AsyncButton } from '../../components/ui';
import { useToast } from '../../context/ToastContext';

export function ageOn(iso: string, today: Date = new Date()): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) return null;
  const y = Number(m[1]);
  const mo = Number(m[2]);
  const d = Number(m[3]);
  return today.getFullYear() - y - (today.getMonth() + 1 < mo || (today.getMonth() + 1 === mo && today.getDate() < d) ? 1 : 0);
}

export const birthDateApi = {
  save: (studentId: string, birthDate: string | null) =>
    http.put<{ student_id: string; birth_date: string | null; adult: boolean }>(`/students/${encodeURIComponent(studentId)}/birth-date`, { birth_date: birthDate }),
};

export function BirthDateEditor({ studentId, name, value, onSaved }: { studentId: string; name: string; value: string | null; onSaved?: (v: string | null) => void }) {
  const id = useId();
  const toast = useToast();
  const [saved, setSaved] = useState(value ?? '');
  const [draft, setDraft] = useState(value ?? '');
  const age = draft ? ageOn(draft) : null;
  const save = async () => {
    try {
      const res = await birthDateApi.save(studentId, draft || null);
      setSaved(res.birth_date ?? '');
      onSaved?.(res.birth_date);
      toast.success(res.birth_date ? `${name}: Geburtsdatum gespeichert${res.adult ? ' (volljährig)' : ''}` : `${name}: Geburtsdatum entfernt`);
    } catch (e) {
      toast.error(e);
    }
  };
  return (
    <span className="kl-row-side">
      <label htmlFor={id} className="small">
        Geburtsdatum
      </label>
      <input id={id} type="date" value={draft} max={new Date().toISOString().slice(0, 10)} onChange={(e) => setDraft(e.target.value)} />
      {age !== null && <span className={`badge${age >= 18 ? ' badge-info' : ''}`}>{age >= 18 ? 'volljährig' : 'minderjährig'}</span>}
      <AsyncButton className="btn btn-sm" disabled={draft === saved} onClick={save}>
        Speichern
      </AsyncButton>
    </span>
  );
}

export default BirthDateEditor;
