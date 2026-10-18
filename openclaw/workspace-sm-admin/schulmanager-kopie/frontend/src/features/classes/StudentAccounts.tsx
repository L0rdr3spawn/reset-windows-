/**
 * Reiter „Schüler/innen“ mit Konten & Zugangsdaten (§11.3):
 * * „Schüler/in hinzufügen“ (masterdata.edit),
 * * Auswahl → „Neue Zugangsdaten erzeugen“ (users.manage; fehlende Konten optional anlegen, Eltern optional),
 * * je Schüler/in Konto-Status und „Passwort“ (auf Startpasswort zurücksetzen / selbst setzen) – Verwaltung sowie
 *   Klassenleitungen mit `passwords.reset` für die eigene Klasse.
 */
import { useId, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { can } from '../../lib/permissions';
import { lettersApi, passwordsApi } from '../zugangsdaten/api';
import { PasswordDialog } from '../zugangsdaten/components';
import type { ClassAccount } from '../zugangsdaten/types';
import { AddStudentsDialog } from './AddStudentsDialog';
import { StudentsTab } from './PeopleTabs';
import type { ClassDetail } from './types';

function NewCredentialsDialog({
  classId,
  studentIds,
  withoutAccount,
  onClose,
}: {
  classId: string;
  studentIds: string[];
  withoutAccount: number;
  onClose: () => void;
}) {
  const navigate = useNavigate();
  const [parents, setParents] = useState(false);
  const [createMissing, setCreateMissing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const n = studentIds.length;
  return (
    <Modal
      title="Neue Zugangsdaten erzeugen"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            onClick={async () => {
              setError(null);
              try {
                const r = await lettersApi.create({ student_ids: studentIds, parents, create_missing: createMissing });
                navigate(`/zugangsdaten/${encodeURIComponent(r.id)}`);
              } catch (e) {
                setError(errorMessage(e));
              }
            }}
          >
            <Icon name="key" /> Zugangsdaten erzeugen
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <p>
          Für {n === 1 ? '1 Schüler/in' : `${n} Schüler/innen`} der Klasse {classId} werden neue Startpasswörter erzeugt.{' '}
          <strong>Bisherige Passwörter werden ungültig.</strong>
          <HelpTip>
            Alle Sitzungen werden beendet; beim ersten Anmelden wird ein eigenes Passwort verlangt. Danach können die Briefe als PDF gedruckt oder per E-Mail verschickt werden.
          </HelpTip>
        </p>
        <label className="check">
          <input type="checkbox" checked={parents} onChange={(e) => setParents(e.target.checked)} /> auch für die Elternkonten
        </label>
        {withoutAccount > 0 && (
          <label className="check">
            <input type="checkbox" checked={createMissing} onChange={(e) => setCreateMissing(e.target.checked)} /> fehlende Konten anlegen ({withoutAccount}{' '}
            ohne Konto
            {parents ? ', Eltern ohne Konto ebenso' : ''})
          </label>
        )}
        {error && (
          <Alert kind="error" title="Nicht möglich">
            {error}
          </Alert>
        )}
      </div>
    </Modal>
  );
}

function AccountBadge({ acc }: { acc: ClassAccount | null }) {
  if (!acc) return <span className="badge">kein Konto</span>;
  return (
    <span className="kl-acc small">
      <span className="mono">{acc.username}</span>
      {!acc.active && <span className="badge badge-danger">inaktiv</span>}
      {acc.must_change_password && <span className="badge badge-warning">{acc.last_login ? 'Passwortwechsel offen' : 'noch nicht angemeldet'}</span>}
    </span>
  );
}

export function StudentsWithAccounts({ detail, onChanged }: { detail: ClassDetail; onChanged: () => void }) {
  const me = useUser();
  const canManage = can(me, 'users.manage');
  const isLead = !!me.teacher_id && detail.class.class_teacher?.id === me.teacher_id;
  const enabled = canManage || (can(me, 'passwords.reset') && isLead);
  const accounts = useApi((signal) => passwordsApi.classAccounts(detail.class.id, signal), [detail.class.id, detail.student_count], {
    enabled,
    live: ['students'],
  });
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [adding, setAdding] = useState(false);
  const [creds, setCreds] = useState(false);
  const [pwFor, setPwFor] = useState<ClassAccount | null>(null);
  const hint = useId();
  const byStudent = useMemo(() => new Map((accounts.data?.students ?? []).map((s) => [s.student_id, s])), [accounts.data]);
  const all = detail.students ?? [];
  const selectable = canManage && !!accounts.data?.can_manage;
  const withoutAccount = [...selected].filter((sid) => byStudent.has(sid) && !byStudent.get(sid)?.account).length;

  const toolbar =
    detail.can_edit || selectable ? (
      <div className="row kl-acc-bar">
        {detail.can_edit && (
          <button type="button" className="btn btn-sm" onClick={() => setAdding(true)}>
            <Icon name="plus" /> Schüler/in hinzufügen
          </button>
        )}
        {selectable && all.length > 0 && (
          <>
            <button
              type="button"
              className="btn btn-sm btn-ghost"
              onClick={() => setSelected(selected.size === all.length ? new Set() : new Set(all.map((s) => s.id)))}
            >
              {selected.size === all.length ? 'Auswahl aufheben' : 'Alle auswählen'}
            </button>
            <button type="button" className="btn btn-sm btn-primary" disabled={!selected.size} onClick={() => setCreds(true)} aria-describedby={hint}>
              <Icon name="key" /> Neue Zugangsdaten erzeugen{selected.size ? ` (${selected.size})` : ''}
            </button>
            <span id={hint} className="small muted">
              Schüler/innen auswählen – Briefe als PDF oder per E-Mail.
            </span>
          </>
        )}
      </div>
    ) : null;

  return (
    <>
      {accounts.error ? (
        <Alert kind="warning" title="Konten konnten nicht geladen werden">
          {errorMessage(accounts.error)}
        </Alert>
      ) : null}
      <StudentsTab
        detail={detail}
        extra={{
          toolbar,
          selected: selectable ? selected : undefined,
          onToggle: selectable
            ? (sid) => {
                const next = new Set(selected);
                if (next.has(sid)) next.delete(sid);
                else next.add(sid);
                setSelected(next);
              }
            : undefined,
          rowSide: enabled
            ? (s) => {
                const acc = byStudent.get(s.id)?.account ?? null;
                return accounts.data ? (
                  <>
                    <AccountBadge acc={acc} />
                    {acc?.can_reset && (
                      <button type="button" className="btn btn-ghost btn-sm" onClick={() => setPwFor(acc)} aria-label={`Passwort von ${s.name} zurücksetzen`}>
                        <Icon name="key" /> Passwort
                      </button>
                    )}
                  </>
                ) : null;
              }
            : undefined,
        }}
      />
      {adding && (
        <AddStudentsDialog
          detail={detail}
          onClose={() => setAdding(false)}
          onAdded={() => {
            onChanged();
            accounts.reload();
          }}
        />
      )}
      {creds && <NewCredentialsDialog classId={detail.class.id} studentIds={[...selected]} withoutAccount={withoutAccount} onClose={() => setCreds(false)} />}
      {pwFor && (
        <PasswordDialog userId={pwFor.user_id} name={pwFor.display_name} role={pwFor.role} onClose={() => setPwFor(null)} onDone={() => accounts.reload()} />
      )}
    </>
  );
}
