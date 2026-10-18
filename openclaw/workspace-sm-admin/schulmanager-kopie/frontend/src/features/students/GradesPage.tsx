/**
 * „Meine Noten“ (`/noten`) für Schüler/innen und Eltern (je Kind): alle Noten nach Fach – Klausuren/Tests und
 * bewertete Hausaufgaben der Kursräume. Außerdem der Dialog zum Eintragen der Noten einer Klausur/eines Tests.
 */
import { useEffect, useState } from 'react';
import { useFamilyChild } from './useChild';
import { http } from '../../api/client';
import { Modal } from '../../components/Modal';
import { AsyncButton, Empty, ErrorBox, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { formatDate } from '../../lib/dates';
import MyGradebook from '../notenbuch/MyGradebook';

interface GradeEntry {
  kind: 'klausur' | 'test' | 'hausaufgabe';
  title: string;
  date: string;
  grade: string;
  note: string;
  by: string;
}
interface GradesResponse {
  student: { id: string; name: string; class_id: string };
  subjects: { subject: string; subject_name: string; entries: GradeEntry[] }[];
}
interface ResultsResponse {
  exam_id: string;
  title: string;
  kind: string;
  date: string;
  students: { student_id: string; name: string; class_id: string | null; grade: string; note: string }[];
}

export const gradesApi = {
  mine: (studentId?: string, signal?: AbortSignal) => http.get<GradesResponse>('/grades', { student_id: studentId }, { signal }),
  results: (examId: string, signal?: AbortSignal) => http.get<ResultsResponse>(`/exams/${encodeURIComponent(examId)}/results`, undefined, { signal }),
  save: (examId: string, results: { student_id: string; grade: string; note: string }[]) =>
    http.put<ResultsResponse & { changed: number }>(`/exams/${encodeURIComponent(examId)}/results`, { results }),
};

const KIND: Record<GradeEntry['kind'], string> = { klausur: 'Klausur/Arbeit', test: 'Test', hausaufgabe: 'Hausaufgabe' };

export default function GradesPage() {
  useTitle('Meine Noten');
  const user = useUser();
  const { child, setChild, kids } = useFamilyChild();
  const q = useApi((signal) => gradesApi.mine(child, signal), [child], { live: ['grades', 'channels'] });
  const data = q.data;
  return (
    <div className="page stack">
      <div className="page-head">
        <h1>{user.role === 'eltern' ? 'Noten' : 'Meine Noten'}</h1>
        {user.role === 'eltern' && kids.length > 1 && (
          <select aria-label="Kind" value={child} onChange={(e) => setChild(e.target.value)}>
            {kids.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name}
              </option>
            ))}
          </select>
        )}
      </div>
      {user.role === 'eltern' && !child ? null : <MyGradebook studentId={child} />}
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!data && q.loading && <Loading />}
      {data && !data.subjects.length && <Empty icon="exam">Noch keine Noten eingetragen.</Empty>}
      {data &&
        data.subjects.map((s) => (
          <section key={s.subject || 'x'} className="card" aria-labelledby={`gr-${s.subject}`}>
            <h2 id={`gr-${s.subject}`} style={{ marginTop: 0 }}>
              {s.subject_name}
            </h2>
            <table className="table">
              <thead>
                <tr>
                  <th>Datum</th>
                  <th>Art</th>
                  <th>Titel</th>
                  <th className="num">Note</th>
                  <th>Bemerkung</th>
                </tr>
              </thead>
              <tbody>
                {s.entries.map((e, i) => (
                  <tr key={`${e.title}-${i}`}>
                    <td>{e.date ? formatDate(e.date) : '–'}</td>
                    <td>{KIND[e.kind]}</td>
                    <td>{e.title}</td>
                    <td className="num">
                      <strong>{e.grade || '–'}</strong>
                    </td>
                    <td className="small">{e.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ))}
    </div>
  );
}

/** Noten einer Klausur bzw. eines Tests eintragen (Lehrkraft des Kurses). */
export function ExamGradesDialog({ examId, onClose }: { examId: string; onClose: () => void }) {
  const toast = useToast();
  const q = useApi((signal) => gradesApi.results(examId, signal), [examId]);
  const [rows, setRows] = useState<ResultsResponse['students']>([]);
  useEffect(() => {
    if (q.data) setRows(q.data.students);
  }, [q.data]);
  const set = (i: number, patch: Partial<ResultsResponse['students'][number]>) => setRows((r) => r.map((x, j) => (j === i ? { ...x, ...patch } : x)));
  return (
    <Modal
      size="lg"
      title={q.data ? `Noten: ${q.data.title || (q.data.kind === 'test' ? 'Test' : 'Klausur')} (${formatDate(q.data.date)})` : 'Noten'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            onClick={async () => {
              try {
                const r = await gradesApi.save(examId, rows.map((x) => ({ student_id: x.student_id, grade: x.grade, note: x.note })));
                toast.success(r.changed ? `${r.changed} Note(n) gespeichert – die Schüler/innen sehen sie unter „Meine Noten“` : 'Keine Änderungen');
                onClose();
              } catch (e) {
                toast.error(e, 'Noten');
              }
            }}
          >
            Speichern
          </AsyncButton>
        </>
      }
    >
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!q.data && <Loading />}
      {q.data && (
        <table className="table">
          <thead>
            <tr>
              <th>Schüler/in</th>
              <th style={{ width: 110 }}>Note</th>
              <th>Bemerkung (sieht nur die Schülerin/der Schüler bzw. die Eltern)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.student_id}>
                <td>
                  {r.name} <span className="xsmall muted">{r.class_id}</span>
                </td>
                <td>
                  <input aria-label={`Note ${r.name}`} value={r.grade} maxLength={20} style={{ width: 90 }} onChange={(e) => set(i, { grade: e.target.value })} />
                </td>
                <td>
                  <input aria-label={`Bemerkung ${r.name}`} value={r.note} maxLength={500} style={{ width: '100%' }} onChange={(e) => set(i, { note: e.target.value })} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Modal>
  );
}
