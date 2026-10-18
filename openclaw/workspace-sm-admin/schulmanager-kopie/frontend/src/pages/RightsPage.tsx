/**
 * `/rechte` – Rollen & Rechte: Matrix (Recht × Rolle) gruppiert nach Bereichen, Zweige der Abteilungsleitung und
 * Zuordnungen (Zweige, begleitete Kinder). Bearbeiten mit `rights.manage`; feste Mindestregeln sind gesperrt.
 * Erklärungen stehen in den „i“-Hinweisen, nicht als Fließtext.
 */
import { Fragment, useMemo, useState } from 'react';
import { http } from '../api/client';
import { HelpTip } from '../components/HelpTip';
import { Icon } from '../components/Icon';
import { MultiSelect, type SelectOption } from '../components/SearchSelect';
import { AsyncButton, ErrorBox, Field, Loading, Tabs } from '../components/ui';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useCollection } from '../hooks/useCollection';
import { useApi } from '../hooks/useApi';
import { useTitle } from '../hooks/misc';
import { can } from '../lib/permissions';
import './rights.css';

interface ScopeOpt {
  id: string;
  label: string;
}
interface Cell {
  granted: boolean;
  scope: string | null;
  default_granted: boolean;
  default_scope: string | null;
  changed: boolean;
  locked: 'granted' | 'denied' | null;
  reason: string | null;
  scope_options: ScopeOpt[];
}
interface RightsData {
  areas: { id: string; label: string; permissions: string[] }[];
  permissions: { id: string; label: string; help: string; area: string; status: string }[];
  roles: { id: string; label: string; description: string; level: number; kind: string; link: string | null; editable: boolean }[];
  cells: Record<string, Record<string, Cell>>;
  derived_roles: { id: string; label: string; description: string }[];
  hierarchy: string[];
  locked_rules: string[];
}
interface Branch {
  id: number;
  name: string;
  sites: string[];
  grades: number[];
  class_ids: string[];
}
interface Assignment {
  id: number;
  username: string;
  display_name: string;
  role: string;
  role_label: string;
  active: boolean;
  branch_ids: number[];
  student_ids: string[];
}

type PermChange = { granted: boolean; scope?: string | null } | null;

function Matrix({ data, canEdit, onData }: { data: RightsData; canEdit: boolean; onData: (d: RightsData) => void }) {
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const labels = useMemo(() => {
    const m: Record<string, string> = {};
    for (const r of data.roles) m[r.id] = r.label;
    for (const d of data.derived_roles) m[d.id] = d.label;
    return m;
  }, [data]);
  const change = async (role: string, perm: string, value: PermChange) => {
    setBusy(true);
    try {
      onData(await http.put<RightsData>(`/rights/roles/${role}`, { permissions: { [perm]: value } }));
    } catch (e) {
      toast.error(e, 'Rechte');
    } finally {
      setBusy(false);
    }
  };
  const permById = new Map(data.permissions.map((p) => [p.id, p]));
  return (
    <div className="stack">
      <div className="row" style={{ flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
        <strong>Rangfolge</strong>
        {data.hierarchy.map((id, i) => (
          <Fragment key={id}>
            {i > 0 && <span aria-hidden="true">→</span>}
            <span className="badge">{labels[id] ?? id}</span>
          </Fragment>
        ))}
        <HelpTip label="Rangfolge">
          Höhere Stufen sehen mehr: Lehrkraft (eigener Unterricht) → Klassenleitung (ganze Klasse, ergibt sich aus den Stammdaten) → Abteilungsleitung (Zweig) →
          Sekretariat/Schulleitung. Hausmeister/in und Schulbegleitung stehen außerhalb dieser Reihe.
        </HelpTip>
        <span style={{ flex: 1 }} />
        <span className="muted small">
          <Icon name="lock" /> Feste Regeln
        </span>
        <HelpTip label="Feste Regeln">
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {data.locked_rules.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </HelpTip>
      </div>
      <div className="rights-wrap" role="region" aria-label="Rechtematrix" tabIndex={0}>
        <table className="rights-table">
          <thead>
            <tr>
              <th scope="col" className="rights-sticky">
                Recht
              </th>
              {data.roles.map((r) => (
                <th key={r.id} scope="col">
                  <div>{r.label}</div>
                  <HelpTip label={`Rolle ${r.label}`}>{r.description}</HelpTip>
                  {canEdit && r.editable && Object.values(data.cells[r.id]).some((c) => c.changed) && (
                    <div>
                      <AsyncButton
                        className="btn btn-sm"
                        confirm={`Alle Änderungen bei „${r.label}“ zurücksetzen?`}
                        title="Auf Standard zurücksetzen"
                        onClick={async () => {
                          try {
                            onData(await http.post<RightsData>(`/rights/roles/${r.id}/reset`));
                          } catch (e) {
                            toast.error(e, 'Rechte');
                          }
                        }}
                      >
                        Standard
                      </AsyncButton>
                    </div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.areas.map((area) => (
              <Fragment key={area.id}>
                <tr className="rights-area">
                  <th colSpan={data.roles.length + 1} scope="colgroup">
                    {area.label}
                  </th>
                </tr>
                {area.permissions.map((pid) => {
                  const p = permById.get(pid);
                  if (!p) return null;
                  return (
                    <tr key={pid}>
                      <th scope="row" className="rights-sticky">
                        {p.label}{' '}
                        <HelpTip label={p.label}>
                          {p.help}
                          {p.status === 'geplant' && ' (Einstellbar; die zugehörige Funktion prüft dieses Recht noch nicht.)'}
                        </HelpTip>
                        {p.status === 'geplant' && (
                          <span className="badge badge-info" style={{ marginLeft: 4 }}>
                            geplant
                          </span>
                        )}
                      </th>
                      {data.roles.map((r) => (
                        <CellView
                          key={r.id}
                          role={r.id}
                          perm={pid}
                          label={`${p.label} – ${r.label}`}
                          cell={data.cells[r.id][pid]}
                          editable={canEdit && r.editable && !busy}
                          onChange={(v) => change(r.id, pid, v)}
                        />
                      ))}
                    </tr>
                  );
                })}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CellView({ cell, label, editable, onChange }: { role: string; perm: string; label: string; cell: Cell; editable: boolean; onChange: (v: PermChange) => void }) {
  if (cell.locked) {
    return (
      <td className={`rights-cell locked ${cell.granted ? 'on' : 'off'}`} title={cell.reason ?? ''}>
        <span aria-label={`${label}: ${cell.granted ? 'ja' : 'nein'} (fest vorgegeben)`}>
          {cell.granted ? '✓' : '–'} <Icon name="lock" />
        </span>
      </td>
    );
  }
  const scopes = cell.scope_options;
  return (
    <td className={`rights-cell ${cell.granted ? 'on' : 'off'}${cell.changed ? ' changed' : ''}`}>
      <label className="check">
        <input type="checkbox" aria-label={label} checked={cell.granted} disabled={!editable} onChange={(e) => onChange({ granted: e.target.checked })} />
      </label>
      {cell.granted && scopes.length > 1 && (
        <select aria-label={`Umfang: ${label}`} value={cell.scope ?? 'all'} disabled={!editable} onChange={(e) => onChange({ granted: true, scope: e.target.value })}>
          {scopes.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
      )}
      {cell.granted && scopes.length === 1 && <span className="muted small">{scopes[0].label}</span>}
      {cell.changed && editable && (
        <button type="button" className="btn-link small" title="Auf Standard zurücksetzen" onClick={() => onChange(null)}>
          ↺
        </button>
      )}
    </td>
  );
}

function Branches({ canEdit }: { canEdit: boolean }) {
  const toast = useToast();
  const list = useApi((signal) => http.get<Branch[]>('/rights/branches', undefined, { signal }), []);
  const classes = useCollection('classes');
  const sites = useCollection('sites');
  const [draft, setDraft] = useState<Partial<Branch> | null>(null);
  const classOpts: SelectOption[] = (classes.data ?? []).map((c) => ({ value: c.id, label: c.name }));
  const siteOpts: SelectOption[] = (sites.data ?? []).map((s) => ({ value: s.id, label: s.name }));
  const gradeOpts: SelectOption[] = Array.from(new Set((classes.data ?? []).map((c) => c.grade)))
    .sort((a, b) => a - b)
    .map((g) => ({ value: String(g), label: `Klassenstufe ${g}` }));
  const save = async () => {
    if (!draft?.name?.trim()) return;
    const body = { name: draft.name.trim(), sites: draft.sites ?? [], grades: draft.grades ?? [], class_ids: draft.class_ids ?? [] };
    try {
      if (draft.id) await http.put(`/rights/branches/${draft.id}`, body);
      else await http.post('/rights/branches', body);
      setDraft(null);
      list.reload();
    } catch (e) {
      toast.error(e, 'Zweig');
    }
  };
  return (
    <div className="stack">
      <h2 style={{ margin: 0 }}>
        Zweige <HelpTip>Ein Zweig (Abteilung) fasst Klassen zusammen – nach Standort, Klassenstufe oder einzeln. Die Abteilungsleitung sieht die Klassen ihres Zweigs.</HelpTip>
      </h2>
      {list.error ? <ErrorBox error={list.error} onRetry={list.reload} /> : null}
      {list.initialLoading && <Loading />}
      <ul className="plain-list stack-sm">
        {(list.data ?? []).map((b) => (
          <li key={b.id} className="card row" style={{ gap: 8, alignItems: 'center' }}>
            <strong style={{ flex: 1 }}>{b.name}</strong>
            <span className="muted small">
              {[b.sites.length && `${b.sites.length} Standort(e)`, b.grades.length && `Stufe ${b.grades.join(', ')}`, b.class_ids.length && `${b.class_ids.length} Klasse(n)`]
                .filter(Boolean)
                .join(' · ') || 'leer'}
            </span>
            {canEdit && (
              <>
                <button type="button" className="btn btn-sm" onClick={() => setDraft(b)}>
                  Bearbeiten
                </button>
                <AsyncButton
                  className="btn btn-sm"
                  confirm={`Zweig „${b.name}“ löschen? Zuordnungen entfallen.`}
                  onClick={async () => {
                    try {
                      await http.del(`/rights/branches/${b.id}`);
                      list.reload();
                    } catch (e) {
                      toast.error(e, 'Zweig');
                    }
                  }}
                >
                  Löschen
                </AsyncButton>
              </>
            )}
          </li>
        ))}
      </ul>
      {canEdit && !draft && (
        <div>
          <button type="button" className="btn btn-primary" onClick={() => setDraft({ name: '', sites: [], grades: [], class_ids: [] })}>
            Zweig anlegen
          </button>
        </div>
      )}
      {draft && (
        <div className="card stack-sm">
          <Field label="Name des Zweigs" htmlFor="br-name">
            <input id="br-name" value={draft.name ?? ''} maxLength={80} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
          </Field>
          <MultiSelect label="Standorte" options={siteOpts} values={draft.sites ?? []} onChange={(v) => setDraft({ ...draft, sites: v })} />
          <MultiSelect label="Klassenstufen" options={gradeOpts} values={(draft.grades ?? []).map(String)} onChange={(v) => setDraft({ ...draft, grades: v.map(Number) })} />
          <MultiSelect label="Einzelne Klassen" options={classOpts} values={draft.class_ids ?? []} onChange={(v) => setDraft({ ...draft, class_ids: v })} />
          <div className="row" style={{ gap: 8 }}>
            <AsyncButton className="btn btn-primary" disabled={!draft.name?.trim()} onClick={save}>
              Speichern
            </AsyncButton>
            <button type="button" className="btn" onClick={() => setDraft(null)}>
              Abbrechen
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function Assignments({ canBranches }: { canBranches: boolean }) {
  const toast = useToast();
  const list = useApi((signal) => http.get<Assignment[]>('/rights/assignments', undefined, { signal }), []);
  const branches = useApi((signal) => http.get<Branch[]>('/rights/branches', undefined, { signal }), [], { enabled: canBranches });
  const students = useCollection('students');
  const studentOpts: SelectOption[] = (students.data ?? []).map((s) => ({ value: s.id, label: s.name, sub: s.class_id }));
  const branchOpts: SelectOption[] = (branches.data ?? []).map((b) => ({ value: String(b.id), label: b.name }));
  const save = async (id: number, body: { branch_ids?: number[]; student_ids?: string[] }) => {
    try {
      await http.put(`/rights/assignments/${id}`, body);
      toast.success('Zuordnung gespeichert');
      list.reload();
    } catch (e) {
      toast.error(e, 'Zuordnung');
    }
  };
  return (
    <div className="stack">
      <h2 style={{ margin: 0 }}>
        Zuordnungen <HelpTip>Abteilungsleitung: für welche Zweige. Schulbegleitung: welches Kind sie begleitet – nur dessen Plan, Kursräume und Material sind sichtbar.</HelpTip>
      </h2>
      {list.error ? <ErrorBox error={list.error} onRetry={list.reload} /> : null}
      {list.initialLoading && <Loading />}
      {list.data && list.data.length === 0 && <p className="muted">Noch keine Konten dieser Rollen. Anlegen unter „Benutzer“.</p>}
      {(list.data ?? []).map((a) => (
        <div key={a.id} className="card stack-sm">
          <div>
            <strong>{a.display_name || a.username}</strong> <span className="muted small">{a.role_label}</span>
          </div>
          {a.role === 'abteilungsleitung' ? (
            <MultiSelect
              label="Zweige"
              options={branchOpts}
              values={a.branch_ids.map(String)}
              onChange={(v) => save(a.id, { branch_ids: v.map(Number) })}
              placeholder="Zweig wählen …"
            />
          ) : (
            <MultiSelect label="Begleitete Kinder" options={studentOpts} values={a.student_ids} onChange={(v) => save(a.id, { student_ids: v })} placeholder="Kind suchen …" />
          )}
        </div>
      ))}
    </div>
  );
}

export default function RightsPage() {
  useTitle('Rollen & Rechte');
  const user = useUser();
  const canEdit = can(user, 'rights.manage');
  const [tab, setTab] = useState<'matrix' | 'zweige' | 'zuordnungen'>('matrix');
  const q = useApi((signal) => http.get<RightsData>('/rights', undefined, { signal }), []);
  return (
    <div className="page stack">
      <div className="page-head">
        <h1>
          Rollen & Rechte{' '}
          <HelpTip>
            Hier legt die Schule fest, was jede Rolle darf. Die Standardwerte sind bewährt; Änderungen gelten sofort bei der nächsten Anfrage der betroffenen Konten und werden im
            Protokoll festgehalten. Mit Schloss markierte Felder sind aus Datenschutzgründen fest vorgegeben.
          </HelpTip>
        </h1>
        {!canEdit && <span className="badge">nur Ansicht</span>}
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && (
        <>
          <Tabs
            label="Bereiche"
            active={tab}
            onChange={setTab}
            tabs={[
              { key: 'matrix', label: 'Rechte' },
              { key: 'zweige', label: 'Zweige', hidden: !canEdit },
              { key: 'zuordnungen', label: 'Zuordnungen' },
            ]}
          />
          {tab === 'matrix' && <Matrix data={q.data} canEdit={canEdit} onData={(d) => q.setData(d)} />}
          {tab === 'zweige' && <Branches canEdit={canEdit} />}
          {tab === 'zuordnungen' && <Assignments canBranches={canEdit} />}
        </>
      )}
    </div>
  );
}
