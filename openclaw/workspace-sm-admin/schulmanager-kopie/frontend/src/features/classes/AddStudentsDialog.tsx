/**
 * „Schüler/in hinzufügen“ auf der Klassen-Seite (§11.3): gleiche Eingabe wie im Klassen-Assistenten, Konten optional,
 * Probelauf → Hinzufügen → Ergebnis mit Zugangsbriefen.
 */
import { useMemo, useState } from 'react';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { invalidate } from '../../hooks/useCollection';
import { can } from '../../lib/permissions';
import { accountBody, AccountOptionsForm, CreateResultView, defaultAccountOpts, PreviewTable, type AccountOpts } from './accountsUi';
import { classesApi } from './api';
import { StudentListEditor, studentListErrors } from './StudentListEditor';
import { toApiStudents, type StudentDraft } from './studentList';
import type { ClassDetail, CreateStudentsResult } from './types';

export function AddStudentsDialog({ detail, onClose, onAdded }: { detail: ClassDetail; onClose: () => void; onAdded: () => void }) {
  const me = useUser();
  const canManage = can(me, 'users.manage');
  const [rows, setRows] = useState<StudentDraft[]>([]);
  const [opts, setOpts] = useState<AccountOpts | null>(null);
  const [preview, setPreview] = useState<{ key: string; result: CreateStudentsResult } | null>(null);
  const [result, setResult] = useState<CreateStudentsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const existing = useMemo(() => (detail.students ?? []).map((s) => s.name), [detail.students]);
  const errors = studentListErrors(rows, existing);
  const options = opts ?? defaultAccountOpts(rows, canManage);
  const body = (dryRun: boolean) => ({ students: toApiStudents(rows), ...accountBody(options, dryRun) });
  const key = JSON.stringify(body(true));
  const ready = rows.length > 0 && errors === 0;

  const run = async (dryRun: boolean) => {
    setError(null);
    try {
      const r = await classesApi.addStudents(detail.class.id, body(dryRun));
      if (dryRun) setPreview({ key, result: r });
      else {
        setResult(r);
        invalidate('students');
        onAdded();
      }
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  return (
    <Modal
      size="lg"
      title={`Schüler/innen zur Klasse ${detail.class.name} hinzufügen`}
      onClose={onClose}
      footer={
        result ? (
          <button type="button" className="btn btn-primary" onClick={onClose}>
            Fertig
          </button>
        ) : (
          <>
            <button type="button" className="btn" onClick={onClose}>
              Abbrechen
            </button>
            <AsyncButton className={`btn${preview?.key === key ? '' : ' btn-primary'}`} disabled={!ready} onClick={() => run(true)}>
              <Icon name="eye" /> Probelauf
            </AsyncButton>
            <AsyncButton className="btn btn-primary" disabled={!ready || preview?.key !== key} onClick={() => run(false)}>
              <Icon name="plus" /> Hinzufügen
            </AsyncButton>
          </>
        )
      }
    >
      {result ? (
        <CreateResultView result={result} title={`${result.students.length === 1 ? '1 Schüler/in' : `${result.students.length} Schüler/innen`} hinzugefügt`} />
      ) : (
        <div className="stack">
          <StudentListEditor rows={rows} onChange={setRows} existing={existing} />
          {rows.length > 0 && <AccountOptionsForm value={options} onChange={setOpts} canManage={canManage} rows={rows} />}
          {error && (
            <Alert kind="error" title="Nicht möglich">
              {error}
            </Alert>
          )}
          {preview && preview.key !== key && (
            <Alert kind="warning" title="Eingaben geändert">
              Bitte den Probelauf wiederholen.
            </Alert>
          )}
          {preview && <PreviewTable result={preview.result} />}
        </div>
      )}
    </Modal>
  );
}
