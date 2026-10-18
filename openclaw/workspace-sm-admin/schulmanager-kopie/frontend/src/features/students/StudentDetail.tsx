/** Stammdaten → Schüler/in: Eltern, Klassenleitung, Fachlehrkräfte sowie Merkmale & Nachweise (Nachteilsausgleich). */
import { HelpTip } from '../../components/HelpTip';
import { useState } from 'react';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { can } from '../../lib/permissions';
import { passwordsApi } from '../zugangsdaten/api';
import { PasswordDialog } from '../zugangsdaten/components';
import { SupportSection } from './SupportSection';
import { supportApi } from './supportApi';

/** Knopf „Passwort zurücksetzen“ für das Schülerkonto (Verwaltung bzw. Klassenleitung der Klasse). */
function AccountReset({ studentId, classId }: { studentId: string; classId: string }) {
  const me = useUser();
  const enabled = !!classId && (can(me, 'users.manage') || (can(me, 'passwords.reset') && !!me.teacher_id));
  const q = useApi((signal) => passwordsApi.classAccounts(classId, signal), [classId], { enabled, live: ['students'] });
  const [open, setOpen] = useState(false);
  const acc = q.data?.students.find((s) => s.student_id === studentId)?.account ?? null;
  if (!enabled || !acc?.can_reset) return null;
  return (
    <section className="stack-sm">
      <h3 style={{ margin: 0 }}>Konto</h3>
      <p className="small" style={{ margin: 0 }}>
        <span className="mono">{acc.username}</span>
        {acc.must_change_password ? <span className="badge badge-warning"> Passwortwechsel offen</span> : null}
      </p>
      <div>
        <button type="button" className="btn btn-sm" onClick={() => setOpen(true)}>
          Passwort zurücksetzen
        </button>
      </div>
      {open && <PasswordDialog userId={acc.user_id} name={acc.display_name} role={acc.role} onClose={() => setOpen(false)} onDone={() => q.reload()} />}
    </section>
  );
}

export function StudentDetail({ studentId, classId = '' }: { studentId: string; classId?: string }) {
  const q = useApi((signal) => supportApi.people(studentId, signal), [studentId], { live: ['students', 'courses', 'classes', 'users'] });
  const p = q.data;
  return (
    <div className="stack" style={{ gridColumn: '1 / -1' }}>
      <AccountReset studentId={studentId} classId={classId} />
      {p && (
        <section className="stack-sm" aria-labelledby={`sd-h-${studentId}`}>
          <h3 id={`sd-h-${studentId}`} style={{ margin: 0 }}>
            Eltern &amp; Lehrkräfte
            <HelpTip>Eltern sind die verknüpften Elternkonten. Kontaktdaten sehen Verwaltung und Klassenleitung.</HelpTip>
          </h3>
          <dl className="kv small" style={{ margin: 0 }}>
            <dt>Klassenleitung</dt>
            <dd>{p.class_teacher ? p.class_teacher.name : <span className="muted">nicht eingetragen</span>}</dd>
            <dt>Eltern</dt>
            <dd>
              {p.parents.length ? (
                <ul className="plain" style={{ margin: 0, paddingLeft: 0, listStyle: 'none' }}>
                  {p.parents.map((x) => (
                    <li key={x.id}>
                      {x.name}
                      {x.email && (
                        <>
                          {' '}
                          · <a href={`mailto:${x.email}`}>{x.email}</a>
                        </>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <span className="muted">kein Elternkonto verknüpft</span>
              )}
            </dd>
            <dt>Fachlehrkräfte</dt>
            <dd>
              {p.subject_teachers.length ? (
                <ul className="plain" style={{ margin: 0, paddingLeft: 0, listStyle: 'none' }}>
                  {p.subject_teachers.map((x) => (
                    <li key={x.subject}>
                      <strong>{x.subject_name}:</strong> {x.teachers.map((t) => t.name).join(', ') || '–'}
                    </li>
                  ))}
                </ul>
              ) : (
                <span className="muted">keine Kurse zugeordnet</span>
              )}
            </dd>
          </dl>
        </section>
      )}
      {(!p || p.can_see_support) && <SupportSection studentId={studentId} embedded />}
    </div>
  );
}
