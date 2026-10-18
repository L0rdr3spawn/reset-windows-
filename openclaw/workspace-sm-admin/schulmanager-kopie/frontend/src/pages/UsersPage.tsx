import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { users as usersApi } from '../api/endpoints';
import type { ApiTokenInfo, BulkCreated, ManagedUser, Role, SessionInfo } from '../api/types';
import { ClassAbbr, TeacherAbbr } from '../components/Abbr';
import { HelpTip } from '../components/HelpTip';
import { Icon } from '../components/Icon';
import { Modal } from '../components/Modal';
import { MultiSelect, SearchSelect, type SelectOption } from '../components/SearchSelect';
import { VirtualTable, type Column } from '../components/VirtualTable';
import { Alert, AsyncButton, CopyField, ErrorBox, Field, Loading, Tabs } from '../components/ui';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { useCollection } from '../hooks/useCollection';
import { useDebounced, useTitle } from '../hooks/misc';
import { formatDateTime } from '../lib/dates';
import { matchesQuery, sortBy } from '../lib/format';
import { ALL_ROLES, ROLE_LABELS } from '../lib/permissions';
import { UserIdentitiesPanel } from '../features/anmeldedienste/slots';
import { UserContactPanel } from '../features/konto/slots';
import { LetterBatchActions, PasswordPanel } from '../features/zugangsdaten/components';
import type { LetterBatchRef } from '../features/zugangsdaten/types';
import { PasswordInput } from '../components/PasswordInput';
import { promptAsk } from '../lib/confirm';

/** Brief-Stapel aus der Antwort (§11.3: `letter_batch` bei Anlegen/Zurücksetzen/Massenanlage) */
const batchOf = (r: unknown): LetterBatchRef | null => (r as { letter_batch?: LetterBatchRef | null } | null)?.letter_batch ?? null;

/** Rollen, die der Benutzer verwalten darf (laut Rechtematrix). */
function manageableRoles(role: Role): Role[] {
  if (role === 'admin') return ALL_ROLES;
  if (role === 'schulleitung') return ALL_ROLES.filter((r) => r !== 'admin');
  if (role === 'sekretariat') return ['schueler', 'eltern', 'schulbegleitung'];
  return [];
}

export interface LetterData {
  username: string;
  display_name: string;
  temp_password: string;
  class?: string | null;
  role?: Role | string;
}

function useStudentOptions(enabled: boolean): SelectOption[] {
  const students = useCollection('students', enabled);
  return useMemo(() => sortBy(students.data ?? [], (s) => s.name).map((s) => ({ value: s.id, label: s.name, sub: s.class_id })), [students.data]);
}

function UserModal({ initial, onClose, onLetters }: { initial: Partial<ManagedUser>; onClose: () => void; onLetters: (l: LetterData[]) => void }) {
  const me = useUser();
  const toast = useToast();
  const isNew = initial.id === undefined;
  const roles = manageableRoles(me.role);
  const [u, setU] = useState<Partial<ManagedUser> & { password?: string }>(() => ({ role: roles.includes('lehrer') ? 'lehrer' : roles[0], active: true, must_change_password: true, ...initial }));
  const [tab, setTab] = useState<'konto' | 'kontakt' | 'anbieter' | 'sicherheit'>('konto');
  const [temp, setTemp] = useState<string | null>(null);
  const [letterBatch, setLetterBatch] = useState<LetterBatchRef | null>(null);
  const [pwDialog, setPwDialog] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const teachers = useCollection('teachers');
  const sites = useCollection('sites');
  const needsStudents = u.role === 'schueler' || u.role === 'eltern';
  const studentOptions = useStudentOptions(needsStudents);
  const teacherOptions: SelectOption[] = useMemo(() => sortBy(teachers.data ?? [], (t) => t.name).map((t) => ({ value: t.id, label: t.name, sub: t.id })), [teachers.data]);
  const sessions = useApi<SessionInfo[]>(() => usersApi.sessions(initial.id as number), [initial.id, tab], { enabled: !isNew && tab === 'sicherheit' });
  const tokens = useApi<ApiTokenInfo[]>(() => usersApi.apiTokens(initial.id as number), [initial.id, tab], { enabled: !isNew && tab === 'sicherheit' });

  const save = async () => {
    if (!u.username?.trim()) {
      toast.warning('Bitte Benutzernamen angeben.');
      return;
    }
    const body: Partial<ManagedUser> & { password?: string } = {
      username: u.username.trim(),
      display_name: u.display_name ?? '',
      role: u.role,
      email: u.email || null,
      teacher_id: u.role === 'lehrer' || u.role === 'abteilungsleitung' || u.role === 'planer' || u.role === 'schulleitung' || u.role === 'admin' ? u.teacher_id || null : null,
      student_id: u.role === 'schueler' ? u.student_id || null : null,
      student_ids: u.role === 'eltern' ? u.student_ids ?? [] : undefined,
      site: u.role === 'monitor' ? u.site || null : u.site ?? null,
      adult: u.role === 'schueler' ? !!u.adult : false,
      must_change_password: u.must_change_password,
    };
    try {
      if (isNew) {
        if (u.password) body.password = u.password;
        const res = await usersApi.create(body);
        toast.success('Konto angelegt');
        if (res.temp_password) {
          setTemp(res.temp_password);
          setLetterBatch(batchOf(res));
          setU({ ...u, id: res.id });
          return;
        }
      } else {
        const { username: _u, ...patch } = body;
        void _u;
        await usersApi.update(initial.id as number, { ...patch, active: u.active });
        if (u.role === 'eltern') await usersApi.setChildren(initial.id as number, u.student_ids ?? []);
        toast.success('Konto gespeichert');
      }
      onClose();
    } catch (e) {
      toast.error(e, 'Speichern');
    }
  };

  return (
    <Modal
      size="lg"
      title={isNew ? 'Konto anlegen' : `Konto: ${initial.username}`}
      onClose={onClose}
      footer={
        <>
          {!isNew && initial.id !== me.id && (
            <AsyncButton
              className="btn btn-ghost"
              confirm={`Konto „${initial.username}“ endgültig löschen? Protokolle werden pseudonymisiert.`}
              onClick={async () => {
                try {
                  await usersApi.remove(initial.id as number);
                  toast.success('Konto gelöscht');
                  onClose();
                } catch (e) {
                  toast.error(e);
                }
              }}
            >
              <Icon name="trash" /> Löschen
            </AsyncButton>
          )}
          <button type="button" className="btn" onClick={onClose}>
            {temp ? 'Schließen' : 'Abbrechen'}
          </button>
          {!temp && (
            <AsyncButton className="btn btn-primary" onClick={save}>
              Speichern
            </AsyncButton>
          )}
        </>
      }
    >
      {temp && (
        <Alert kind="success" title="Startpasswort (nur jetzt sichtbar)">
          <CopyField label="Startpasswort" value={temp} />
          <button
            type="button"
            className="btn btn-sm"
            style={{ marginTop: 8 }}
            onClick={() => onLetters([{ username: u.username ?? '', display_name: u.display_name ?? '', temp_password: temp, role: u.role }])}
          >
            <Icon name="print" /> Zugangsbrief drucken
          </button>
          {letterBatch && (
            <div style={{ marginTop: 8 }}>
              <LetterBatchActions batch={letterBatch} />
            </div>
          )}
        </Alert>
      )}
      {!isNew && (
        <Tabs
          label="Kontobereiche"
          tabs={[
            { key: 'konto', label: 'Konto' },
            { key: 'kontakt', label: 'Kontakt' },
            { key: 'anbieter', label: 'Verbundene Konten' },
            { key: 'sicherheit', label: 'Sicherheit & Sitzungen' },
          ]}
          active={tab}
          onChange={setTab}
        />
      )}
      {!isNew && tab === 'kontakt' && <UserContactPanel userId={initial.id as number} onEmailChange={(email) => setU((prev) => ({ ...prev, email }))} />}
      {!isNew && tab === 'anbieter' && <UserIdentitiesPanel userId={initial.id as number} />}
      {tab === 'konto' && (
        <div className="form-grid">
          <Field label="Benutzername *" htmlFor="u-name" hint={isNew ? 'klein, ohne Leerzeichen' : 'nicht änderbar'}>
            <input id="u-name" type="text" value={u.username ?? ''} disabled={!isNew} autoCapitalize="none" onChange={(e) => setU({ ...u, username: e.target.value.toLowerCase() })} />
          </Field>
          <Field label="Anzeigename" htmlFor="u-dn">
            <input id="u-dn" type="text" value={u.display_name ?? ''} onChange={(e) => setU({ ...u, display_name: e.target.value })} />
          </Field>
          <Field label="Rolle" htmlFor="u-role">
            <select id="u-role" value={u.role} onChange={(e) => setU({ ...u, role: e.target.value as Role })}>
              {roles.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABELS[r]}
                </option>
              ))}
            </select>
          </Field>
          <Field label="E-Mail" htmlFor="u-mail">
            <input id="u-mail" type="email" value={u.email ?? ''} onChange={(e) => setU({ ...u, email: e.target.value })} />
          </Field>
          {(u.role === 'lehrer' || u.role === 'abteilungsleitung' || u.role === 'planer' || u.role === 'schulleitung' || u.role === 'admin') && (
            <SearchSelect label="Verknüpfte Lehrkraft (Kürzel)" options={teacherOptions} value={u.teacher_id ?? null} onChange={(v) => setU({ ...u, teacher_id: v })} allowClear />
          )}
          {u.role === 'schueler' && (
            <>
              <SearchSelect label="Verknüpfte/r Schüler/in" options={studentOptions} value={u.student_id ?? null} onChange={(v) => setU({ ...u, student_id: v })} allowClear />
              <div className="field">
                <span className="field-label">Volljährig</span>
                <label className="check">
                  <input type="checkbox" checked={!!u.adult} onChange={(e) => setU({ ...u, adult: e.target.checked })} /> darf sich selbst krankmelden
                </label>
              </div>
            </>
          )}
          {u.role === 'eltern' && (
            <div className="span-all">
              <MultiSelect label="Kinder" options={studentOptions} values={u.student_ids ?? []} onChange={(v) => setU({ ...u, student_ids: v })} placeholder="Kind suchen …" />
            </div>
          )}
          {(u.role === 'abteilungsleitung' || u.role === 'schulbegleitung') && (
            <p className="muted small span-all">
              {u.role === 'abteilungsleitung' ? 'Zweig' : 'Begleitetes Kind'} nach dem Speichern unter „Rollen & Rechte“ zuordnen.{' '}
              <Link to="/rechte">Zur Zuordnung</Link>
            </p>
          )}
          {u.role === 'monitor' && (
            <Field label="Standort des Monitors" htmlFor="u-site">
              <select id="u-site" value={u.site ?? ''} onChange={(e) => setU({ ...u, site: e.target.value || null })}>
                <option value="">alle Standorte</option>
                {(sites.data ?? []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </Field>
          )}
          {isNew && (
            <Field label="Passwort (optional)" htmlFor="u-pw" hint="leer = Startpasswort wird erzeugt">
              <PasswordInput id="u-pw" autoComplete="new-password" value={u.password ?? ''} onChange={(e) => setU({ ...u, password: e.target.value })} />
            </Field>
          )}
          <div className="field span-all">
            <div className="row">
              {!isNew && (
                <label className="check">
                  <input type="checkbox" checked={u.active !== false} onChange={(e) => setU({ ...u, active: e.target.checked })} disabled={initial.id === me.id} /> Konto aktiv
                </label>
              )}
              <label className="check">
                <input type="checkbox" checked={!!u.must_change_password} onChange={(e) => setU({ ...u, must_change_password: e.target.checked })} /> Passwortwechsel bei nächster Anmeldung
              </label>
            </div>
          </div>
        </div>
      )}
      {tab === 'sicherheit' && !isNew && (
        <div className="stack">
          <section>
            <h3>
              Passwort
              <HelpTip>Erzeugt ein neues Startpasswort. Alle Sitzungen des Kontos werden beendet, beim nächsten Login ist ein Wechsel nötig.</HelpTip>
            </h3>
            <div className="row" style={{ marginTop: 8 }}>
              <AsyncButton
                className="btn"
                confirm="Neues Startpasswort erzeugen?"
                onClick={async () => {
                  try {
                    const r = await usersApi.resetPassword(initial.id as number);
                    setTemp(r.temp_password);
                    setLetterBatch(batchOf(r));
                  } catch (e) {
                    toast.error(e);
                  }
                }}
              >
                <Icon name="key" /> Passwort zurücksetzen
              </AsyncButton>
              {initial.totp_enabled && (
                <AsyncButton
                  className="btn"
                  confirm="Passwort zurücksetzen UND Zwei-Faktor-Anmeldung abschalten (z. B. Handy verloren)?"
                  onClick={async () => {
                    try {
                      const r = await usersApi.resetPassword(initial.id as number, true);
                      setTemp(r.temp_password);
                      setLetterBatch(batchOf(r));
                    } catch (e) {
                      toast.error(e);
                    }
                  }}
                >
                  <Icon name="shield" /> … und 2FA abschalten
                </AsyncButton>
              )}
              <button type="button" className="btn" aria-expanded={pwDialog} onClick={() => setPwDialog(!pwDialog)}>
                <Icon name="undo" /> Auf Startpasswort zurücksetzen / selbst setzen
              </button>
            </div>
            {pwDialog && (
              <div className="card" style={{ marginTop: 8 }}>
                <PasswordPanel userId={initial.id as number} name={initial.display_name || initial.username || ''} role={initial.role} />
              </div>
            )}
          </section>
          <section>
            <div className="row-between">
              <h3>Aktive Sitzungen</h3>
              <AsyncButton
                className="btn btn-sm"
                onClick={async () => {
                  try {
                    const r = await usersApi.revokeAllSessions(initial.id as number);
                    toast.success(`${r.revoked} Sitzung(en) beendet`);
                    sessions.reload();
                  } catch (e) {
                    toast.error(e);
                  }
                }}
              >
                Alle beenden
              </AsyncButton>
            </div>
            {sessions.error ? <ErrorBox error={sessions.error} onRetry={sessions.reload} /> : null}
            {sessions.data && sessions.data.length === 0 && <p className="small muted">Keine aktiven Sitzungen.</p>}
            <ul className="list-plain small">
              {(sessions.data ?? []).map((s) => (
                <li key={s.id} className="row-between">
                  <span>
                    {s.current && <span className="badge badge-primary">diese Sitzung</span>} {s.user_agent?.slice(0, 80) ?? 'unbekanntes Gerät'} · {s.ip ?? ''} · zuletzt {formatDateTime(s.last_seen)}
                  </span>
                  <AsyncButton
                    className="btn btn-ghost btn-sm"
                    onClick={async () => {
                      try {
                        await usersApi.deleteSession(s.id);
                        sessions.reload();
                      } catch (e) {
                        toast.error(e);
                      }
                    }}
                  >
                    Beenden
                  </AsyncButton>
                </li>
              ))}
            </ul>
          </section>
          <section>
            <div className="row-between">
              <h3>API-Tokens</h3>
              {/* Tokens nur für das eigene Konto (A-27/U-02) – fremde lassen sich nur ansehen und widerrufen */}
              {initial.id === me.id && (
                <AsyncButton
                  className="btn btn-sm"
                  onClick={async () => {
                    const name = await promptAsk({ title: 'API-Token erzeugen', message: 'Name für das Token (z. B. „Schul-App“)', initial: 'API-Token', confirmLabel: 'Erzeugen' });
                    if (name === null) return;
                    try {
                      const r = await usersApi.apiToken(initial.id as number, name);
                      setToken(r.token);
                      tokens.reload();
                    } catch (e) {
                      toast.error(e);
                    }
                  }}
                >
                  <Icon name="plus" /> Token erzeugen
                </AsyncButton>
              )}
            </div>
            {token && (
              <Alert kind="warning" title="Token nur jetzt sichtbar – sicher aufbewahren">
                <CopyField label="API-Token (Header: Authorization: Bearer …)" value={token} />
              </Alert>
            )}
            <ul className="list-plain small">
              {(tokens.data ?? []).map((t) => (
                <li key={t.id} className="row-between">
                  <span>
                    <strong>{t.name}</strong> <span className="mono">{t.prefix}…</span> · erstellt {formatDateTime(t.created_at)} · zuletzt {formatDateTime(t.last_used)}
                  </span>
                  <AsyncButton
                    className="btn btn-ghost btn-sm"
                    confirm="Token widerrufen?"
                    onClick={async () => {
                      try {
                        await usersApi.deleteApiToken(t.id);
                        tokens.reload();
                      } catch (e) {
                        toast.error(e);
                      }
                    }}
                  >
                    Widerrufen
                  </AsyncButton>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </Modal>
  );
}

function BulkModal({ onClose, onLetters }: { onClose: () => void; onLetters: (l: LetterData[]) => void }) {
  const me = useUser();
  const toast = useToast();
  const allowed = (['schueler', 'eltern', 'lehrer'] as const).filter((r) => manageableRoles(me.role).includes(r));
  const [role, setRole] = useState<(typeof allowed)[number]>(allowed[0] ?? 'schueler');
  const [classIds, setClassIds] = useState<string[]>([]);
  const [result, setResult] = useState<{ created: BulkCreated[]; skipped?: unknown; letter_batch?: LetterBatchRef | null } | null>(null);
  const classes = useCollection('classes');
  const classOptions = useMemo(() => sortBy(classes.data ?? [], (c) => c.name).map((c) => ({ value: c.id, label: c.name })), [classes.data]);
  return (
    <Modal
      size="lg"
      title="Konten in Massen anlegen"
      onClose={onClose}
      footer={
        result ? (
          <>
            <button type="button" className="btn" onClick={onClose}>
              Schließen
            </button>
            <button type="button" className="btn btn-primary" disabled={!result.created.length} onClick={() => onLetters(result.created.map((c) => ({ ...c, role: c.role ?? role })))}>
              <Icon name="print" /> Zugangsbriefe drucken ({result.created.length})
            </button>
          </>
        ) : (
          <>
            <button type="button" className="btn" onClick={onClose}>
              Abbrechen
            </button>
            <AsyncButton
              className="btn btn-primary"
              onClick={async () => {
                try {
                  const r = await usersApi.bulk(role, role === 'lehrer' ? undefined : classIds);
                  setResult({ ...r, letter_batch: batchOf(r) });
                  toast.success(`${r.created.length} Konten angelegt`);
                } catch (e) {
                  toast.error(e, 'Massenanlage');
                }
              }}
            >
              Konten anlegen
            </AsyncButton>
          </>
        )
      }
    >
      {!result ? (
        <div className="stack">
          <Field
            label="Rolle"
            htmlFor="bulk-role"
            help="Legt für alle Personen ohne Konto ein Konto mit Startpasswort an. Die Passwörter werden nur einmal angezeigt, drucken Sie daher direkt die Zugangsbriefe."
          >
            <select id="bulk-role" value={role} onChange={(e) => setRole(e.target.value as typeof role)}>
              {allowed.map((r) => (
                <option key={r} value={r}>
                  {r === 'schueler' ? 'Schüler/innen' : r === 'eltern' ? 'Eltern (je Kind ein Konto)' : 'Lehrkräfte'}
                </option>
              ))}
            </select>
          </Field>
          {role !== 'lehrer' && <MultiSelect label="Nur für Klassen (leer = alle)" options={classOptions} values={classIds} onChange={setClassIds} />}
        </div>
      ) : (
        <div className="stack">
          <Alert kind="success" title={`${result.created.length} Konten angelegt`}>
            {typeof result.skipped === 'number' && result.skipped > 0 ? `${result.skipped} übersprungen (Konto vorhanden).` : null}
            {result.letter_batch && (
              <div style={{ marginTop: 8 }}>
                <LetterBatchActions batch={result.letter_batch} />
              </div>
            )}
          </Alert>
          <div className="table-wrap" style={{ maxHeight: 360 }}>
            <table className="table table-compact">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Klasse</th>
                  <th scope="col">Benutzername</th>
                  <th scope="col">Startpasswort</th>
                </tr>
              </thead>
              <tbody>
                {result.created.map((c) => (
                  <tr key={c.username}>
                    <td>{c.display_name}</td>
                    <td>{c.class ?? ''}</td>
                    <td className="mono">{c.username}</td>
                    <td className="mono">{c.temp_password}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Modal>
  );
}

/** Vorführ-Instanz: Demo-Zugang ausgeben (je Art ein Konto mit simulierten Daten) – nur der Inhaber. */
function DemoAccessModal({ onClose, onLetters }: { onClose: () => void; onLetters: (l: LetterData[]) => void }) {
  const toast = useToast();
  const info = useApi((signal) => usersApi.demoAccessInfo(signal), []);
  const [name, setName] = useState('');
  const [kinds, setKinds] = useState<string[]>(['schulleitung', 'lehrer', 'schueler', 'eltern']);
  const toggle = (k: string) => setKinds((cur) => (cur.includes(k) ? cur.filter((x) => x !== k) : [...cur, k]));
  return (
    <Modal
      size="lg"
      title="Demo-Zugang ausgeben"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            disabled={!name.trim() || !kinds.length}
            onClick={async () => {
              try {
                const r = await usersApi.demoAccess(name.trim(), kinds);
                toast.success(`${r.letters.length} Demo-Konten angelegt`);
                onLetters(r.letters);
              } catch (e) {
                toast.error(e, 'Demo-Zugang');
              }
            }}
          >
            <Icon name="print" /> Anlegen und Zugangsbriefe
          </AsyncButton>
        </>
      }
    >
      {info.error ? <ErrorBox error={info.error} onRetry={info.reload} /> : null}
      {!info.data && !info.error && <Loading />}
      {info.data && (
        <div className="stack">
          <Field label="Für wen?" htmlFor="da-name">
            <input id="da-name" value={name} maxLength={60} onChange={(e) => setName(e.target.value)} placeholder="z. B. Gesamtschule Musterstadt" />
          </Field>
          <fieldset className="stack-sm">
            <legend className="small">Konten</legend>
            <div className="row" style={{ flexWrap: 'wrap', gap: 12 }}>
              {info.data.kinds.map((k) => (
                <label key={k.kind} className="check">
                  <input type="checkbox" checked={kinds.includes(k.kind)} onChange={() => toggle(k.kind)} /> {k.label}
                </label>
              ))}
            </div>
          </fieldset>
          {info.data.issued.length > 0 && (
            <details>
              <summary className="small">Bisher ausgegeben ({info.data.issued.length})</summary>
              <ul className="small">
                {info.data.issued.map((u) => (
                  <li key={u.id}>
                    <span className="mono">{u.username}</span> – {u.display_name}
                    {!u.active ? ' (inaktiv)' : ''} · {u.last_login ? `zuletzt ${formatDateTime(u.last_login)}` : 'noch nie angemeldet'}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </Modal>
  );
}

export default function UsersPage() {
  useTitle('Benutzer');
  const me = useUser();
  const navigate = useNavigate();
  const [role, setRole] = useState('');
  const [q, setQ] = useState('');
  const query = useDebounced(q, 150);
  const [edit, setEdit] = useState<Partial<ManagedUser> | null>(null);
  const [bulk, setBulk] = useState(false);
  const [demoAccess, setDemoAccess] = useState(false);
  const list = useApi(() => usersApi.list(role ? { role } : undefined), [role]);
  const rows = useMemo(
    () => (list.data ?? []).filter((u) => !query || matchesQuery(`${u.username} ${u.display_name} ${u.teacher_id ?? ''} ${u.student_id ?? ''} ${u.class ?? ''} ${u.email ?? ''}`, query)),
    [list.data, query],
  );
  const counts = useMemo(() => {
    const m: Record<string, number> = {};
    for (const u of list.data ?? []) m[u.role] = (m[u.role] ?? 0) + 1;
    return m;
  }, [list.data]);

  const openLetters = (letters: LetterData[]) => navigate('/druck/zugangsbriefe', { state: { letters } });

  const columns: Column<ManagedUser>[] = [
    { key: 'username', header: 'Benutzername', render: (u) => <span className="mono">{u.username}</span>, sortValue: (u) => u.username, width: '200px' },
    { key: 'name', header: 'Name', render: (u) => u.display_name, sortValue: (u) => u.display_name },
    { key: 'role', header: 'Rolle', render: (u) => ROLE_LABELS[u.role] ?? u.role, sortValue: (u) => u.role, width: '170px' },
    {
      key: 'link',
      header: 'Verknüpfung',
      render: (u) =>
        u.teacher_id ? (
          <>
            Lehrkraft <TeacherAbbr id={u.teacher_id} />
          </>
        ) : u.student_id ? (
          <>
            Schüler/in {u.student_id}
            {u.class ? (
              <>
                {' ('}
                <ClassAbbr id={u.class} />)
              </>
            ) : null}
          </>
        ) : u.student_ids?.length
              ? `${u.student_ids.length} Kind(er)`
              : u.site
                ? `Standort ${u.site}`
                : '',
    },
    {
      key: 'status',
      header: 'Status',
      width: '230px',
      render: (u) => (
        <span className="row" style={{ gap: 4, flexWrap: 'nowrap' }}>
          {u.active === false && <span className="badge badge-danger">inaktiv</span>}
          {u.totp_enabled && <span className="badge badge-success">2FA</span>}
          {u.must_change_password && <span className="badge badge-warning">Startpasswort</span>}
        </span>
      ),
    },
    { key: 'last', header: 'Letzter Login', render: (u) => <span className="small">{u.last_login ? formatDateTime(u.last_login) : 'nie'}</span>, sortValue: (u) => u.last_login ?? '', width: '170px' },
  ];

  return (
    <div className="page">
      <div className="page-head">
        <h1>Benutzerkonten</h1>
        <div className="actions">
          {me.demo && me.role === 'admin' && (
            <button type="button" className="btn" onClick={() => setDemoAccess(true)}>
              <Icon name="eye" /> Demo-Zugang ausgeben
            </button>
          )}
          <button type="button" className="btn" onClick={() => setBulk(true)}>
            <Icon name="users" /> Massenanlage & Zugangsbriefe
          </button>
          <button type="button" className="btn btn-primary" onClick={() => setEdit({})}>
            <Icon name="plus" /> Konto anlegen
          </button>
        </div>
      </div>
      <div className="toolbar">
        <div className="field wide">
          <label htmlFor="u-q">Suche</label>
          <input id="u-q" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Name, Benutzername, Klasse, Kürzel …" />
        </div>
        <Field label="Rolle" htmlFor="u-rolefilter">
          <select id="u-rolefilter" value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="">alle Rollen</option>
            {manageableRoles(me.role).map((r) => (
              <option key={r} value={r}>
                {ROLE_LABELS[r]} {counts[r] !== undefined && !role ? `(${counts[r]})` : ''}
              </option>
            ))}
          </select>
        </Field>
      </div>
      {list.error ? <ErrorBox error={list.error} onRetry={list.reload} /> : null}
      {list.initialLoading && <Loading />}
      {list.data && <VirtualTable rows={rows} columns={columns} rowKey={(u) => String(u.id)} onRowClick={(u) => setEdit(u)} caption="Benutzerkonten" height="64vh" />}
      {edit && (
        <UserModal
          initial={edit}
          onClose={() => {
            setEdit(null);
            list.reload();
          }}
          onLetters={openLetters}
        />
      )}
      {demoAccess && <DemoAccessModal onClose={() => setDemoAccess(false)} onLetters={openLetters} />}
      {bulk && (
        <BulkModal
          onClose={() => {
            setBulk(false);
            list.reload();
          }}
          onLetters={openLetters}
        />
      )}
    </div>
  );
}
