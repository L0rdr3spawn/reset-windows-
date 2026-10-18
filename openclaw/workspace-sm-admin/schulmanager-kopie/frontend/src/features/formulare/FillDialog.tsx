/**
 * Formular online ausfüllen (Handy-tauglich) – oder leer als PDF zum Ausdrucken öffnen.
 */
import { useMemo, useState } from 'react';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { AsyncButton, ErrorBox, Field, FormErrors, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDate } from '../../lib/dates';
import { formsApi, type Answers, type FillInfo, type Submission } from './api';
import { FormFields } from './FormFields';
import { answerErrors, initialAnswers } from './logic';
import './formulare.css';

function Form({ info, studentId: studentIn, onClose, onDone }: { info: FillInfo; studentId?: string; onClose: () => void; onDone: (s: Submission) => void }) {
  const toast = useToast();
  const defn = info.definition;
  const hasStudentField = defn.fields.some((f) => f.type === 'student');
  const [answers, setAnswers] = useState<Answers>(() => initialAnswers(defn));
  const [student, setStudent] = useState<string>(() => studentIn ?? (info.students.length === 1 ? (info.students[0]?.id ?? '') : ''));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saveError, setSaveError] = useState<unknown>(null);
  const studentRow = info.students.find((s) => s.id === student);
  const alreadyDone = info.once && studentRow?.submission_id != null;

  const submit = async () => {
    setSaveError(null);
    const found = answerErrors(defn, answers, student || null, info.needs_student);
    setErrors(found);
    if (Object.keys(found).length) {
      toast.error(new Error('Bitte die markierten Felder prüfen.'));
      return;
    }
    try {
      const result = await formsApi.submit(info.id, { student_id: student || null, answers });
      toast.success('Formular abgesendet');
      onDone(result);
    } catch (e) {
      setSaveError(e);
    }
  };

  return (
    <Modal
      title={info.title}
      size="lg"
      onClose={onClose}
      footer={
        <>
          <a className="btn btn-ghost" href={formsApi.blankPdfUrl(info.id)} target="_blank" rel="noopener">
            <Icon name="print" /> Leer ausdrucken
          </a>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" disabled={alreadyDone} onClick={submit}>
            <Icon name="check" /> Absenden
          </AsyncButton>
        </>
      }
    >
      <FormErrors error={saveError}>
        <div className="stack">
          {info.description && <p className="muted" style={{ margin: 0 }}>{info.description}</p>}
          {info.open_until && <p className="small muted" style={{ margin: 0 }}>Bis {formatDate(info.open_until)} auszufüllen.</p>}
          {info.needs_student && !hasStudentField && info.students.length !== 1 && (
            <Field label="Für wen?" htmlFor="fm-student" error={errors.__student}>
              <select id="fm-student" value={student} onChange={(e) => setStudent(e.target.value)}>
                <option value="">Bitte wählen …</option>
                {info.students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                    {s.class_id ? ` (${s.class_id})` : ''}
                    {info.once && s.submission_id ? ' – bereits abgegeben' : ''}
                  </option>
                ))}
              </select>
            </Field>
          )}
          {info.needs_student && !hasStudentField && info.students.length === 1 && (
            <p className="small" style={{ margin: 0 }}>
              Für: <strong>{info.students[0]?.name}</strong>
              {info.students[0]?.class_id ? ` (${info.students[0].class_id})` : ''}
            </p>
          )}
          {alreadyDone && <div className="alert alert-info">Für {studentRow?.name} liegt dieses Formular bereits vor.</div>}
          <FormFields
            definition={defn}
            answers={answers}
            onChange={(id, v) => setAnswers((a) => ({ ...a, [id]: v }))}
            errors={errors}
            students={info.students}
            studentId={student}
            onStudent={setStudent}
            periods={info.periods}
            signer={info.signer}
          />
          {info.sensitive && <p className="small muted" style={{ margin: 0 }}>Besonders geschützte Angaben, sichtbar nur für berechtigte Personen.</p>}
        </div>
      </FormErrors>
    </Modal>
  );
}

export function FillDialog({ templateId, studentId, onClose, onDone }: { templateId: number; studentId?: string; onClose: () => void; onDone: (s: Submission) => void }) {
  const q = useApi((signal) => formsApi.fillInfo(templateId, signal), [templateId]);
  const body = useMemo(() => q.data, [q.data]);
  if (q.error || q.initialLoading || !body) {
    return (
      <Modal title="Formular" onClose={onClose}>
        {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : <Loading />}
      </Modal>
    );
  }
  return <Form info={body} studentId={studentId} onClose={onClose} onDone={onDone} />;
}
