/**
 * `/schuljahreswechsel` – Assistent für den Jahreswechsel: Vorgaben → Vorschau → Ausführen → Rückgängig.
 * Daten: `POST /year-change/preview|execute|undo`, `GET /year-change/runs` (docs/PRODUKTREIFE.md).
 * Die Vorschau ändert nichts und liefert ein Token; ausgeführt wird nur genau diese Vorschau.
 */
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { http } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { invalidateAll, useCollection } from '../../hooks/useCollection';
import { useTitle } from '../../hooks/misc';
import { formatDateTime } from '../../lib/dates';
import {
  ACTION_LABELS,
  defaultPlan,
  runText,
  setRule,
  toRequest,
  type ClassAction,
  type PlanForm,
  type Preview,
  type Run,
} from './logic';

function Toggle({ checked, onChange, children }: { checked: boolean; onChange: (v: boolean) => void; children: React.ReactNode }) {
  return (
    <label className="check">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} /> {children}
    </label>
  );
}

function Leavers({ plan, onChange }: { plan: PlanForm; onChange: (ids: string[]) => void }) {
  const students = useCollection('students');
  const [term, setTerm] = useState('');
  const byId = useMemo(() => new Map((students.data ?? []).map((s) => [s.id, s])), [students.data]);
  const hits = useMemo(() => {
    const t = term.trim().toLowerCase();
    if (t.length < 2) return [];
    return (students.data ?? []).filter((s) => s.name.toLowerCase().includes(t) && !plan.extra_leavers.includes(s.id)).slice(0, 8);
  }, [students.data, term, plan.extra_leavers]);
  return (
    <div className="stack-sm">
      <Field label="Einzelne Abgänger/innen" htmlFor="yc-leaver" help="Schüler/innen, die die Schule unabhängig vom Klassenwechsel verlassen (Schulwechsel, Abbruch). Sie werden wie Abgänger behandelt.">
        <input id="yc-leaver" value={term} placeholder="Name suchen (ab 2 Buchstaben)" onChange={(e) => setTerm(e.target.value)} />
      </Field>
      {hits.length > 0 && (
        <ul className="list-plain" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {hits.map((s) => (
            <li key={s.id}>
              <button type="button" className="btn btn-sm" onClick={() => { onChange([...plan.extra_leavers, s.id]); setTerm(''); }}>
                <Icon name="plus" /> {s.name} ({s.class_id})
              </button>
            </li>
          ))}
        </ul>
      )}
      {plan.extra_leavers.length > 0 && (
        <ul className="row" style={{ listStyle: 'none', padding: 0, margin: 0, gap: 6, flexWrap: 'wrap' }} aria-label="Ausgewählte Abgänger/innen">
          {plan.extra_leavers.map((id) => (
            <li key={id} className="badge">
              {byId.get(id)?.name ?? id}{' '}
              <button type="button" className="btn-link" aria-label={`${byId.get(id)?.name ?? id} entfernen`} onClick={() => onChange(plan.extra_leavers.filter((x) => x !== id))}>
                <Icon name="x" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function NewClasses({ plan, onChange }: { plan: PlanForm; onChange: (c: PlanForm['new_classes']) => void }) {
  const upd = (i: number, patch: Partial<PlanForm['new_classes'][number]>) =>
    onChange(plan.new_classes.map((c, k) => (k === i ? { ...c, ...patch } : c)));
  return (
    <div className="stack-sm">
      {plan.new_classes.map((c, i) => (
        <div key={i} className="row" style={{ gap: 8, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <Field label="Name" htmlFor={`yc-nc-name-${i}`}>
            <input id={`yc-nc-name-${i}`} value={c.name} maxLength={40} placeholder="5a" onChange={(e) => upd(i, { name: e.target.value })} />
          </Field>
          <Field label="Jahrgang" htmlFor={`yc-nc-grade-${i}`}>
            <input id={`yc-nc-grade-${i}`} type="number" min={1} max={13} value={c.grade} onChange={(e) => upd(i, { grade: Number(e.target.value) })} style={{ width: 90 }} />
          </Field>
          <Field label="Plätze" htmlFor={`yc-nc-count-${i}`}>
            <input id={`yc-nc-count-${i}`} type="number" min={0} max={60} value={c.count} onChange={(e) => upd(i, { count: Number(e.target.value) })} style={{ width: 90 }} />
          </Field>
          <button type="button" className="btn btn-ghost btn-sm" aria-label={`Neue Klasse ${c.name || i + 1} entfernen`} onClick={() => onChange(plan.new_classes.filter((_, k) => k !== i))}>
            <Icon name="trash" />
          </button>
        </div>
      ))}
      <div>
        <button type="button" className="btn btn-sm" onClick={() => onChange([...plan.new_classes, { name: '', grade: 5, site: '', count: 25 }])}>
          <Icon name="plus" /> Neue Klasse (Schulanfänger/innen)
        </button>
      </div>
    </div>
  );
}

function PreviewView({ p, onRule }: { p: Preview; onRule: (id: string, a: ClassAction, auto: ClassAction) => void }) {
  const auto = (c: Preview['classes'][number]): ClassAction => (p.final_grade && c.grade >= p.final_grade ? 'graduate' : 'promote');
  return (
    <div className="stack">
      {p.conflicts.length > 0 && (
        <Alert kind="error" title="Das lässt sich so nicht ausführen">
          <ul>{p.conflicts.map((c) => <li key={c}>{c}</li>)}</ul>
        </Alert>
      )}
      <section className="card stack-sm" aria-label="Klassen">
        <h3>
          Klassen {p.old_year ? `${p.old_year} → ` : ''}{p.new_year}{' '}
          <HelpTip>Jede Klasse kann abweichend behandelt werden, z. B. jahrgangsgemischte Gruppen „Unverändert“. Die interne Klassen-Kennung bleibt immer gleich, damit alle Verknüpfungen erhalten bleiben.</HelpTip>
        </h3>
        <div className="table-wrap">
          <table className="table table-compact">
            <thead>
              <tr>
                <th scope="col">Klasse</th>
                <th scope="col" className="num">Schüler/innen</th>
                <th scope="col">Aktion</th>
                <th scope="col">Danach</th>
              </tr>
            </thead>
            <tbody>
              {p.classes.map((c) => (
                <tr key={c.id}>
                  <td>{c.name} <span className="muted small">(Jg. {c.grade})</span></td>
                  <td className="num">{c.students}</td>
                  <td>
                    <select aria-label={`Aktion für Klasse ${c.name}`} value={c.action} onChange={(e) => onRule(c.id, e.target.value as ClassAction, auto(c))}>
                      {(Object.keys(ACTION_LABELS) as ClassAction[]).map((a) => (
                        <option key={a} value={a}>{ACTION_LABELS[a]}</option>
                      ))}
                    </select>
                  </td>
                  <td>{c.action === 'graduate' ? 'verlässt die Schule' : `${c.new_name} (Jg. ${c.new_grade})`}</td>
                </tr>
              ))}
              {p.new_classes.map((c) => (
                <tr key={`new-${c.name}`}>
                  <td>{c.name} <span className="badge badge-info">neu</span></td>
                  <td className="num">{c.count}</td>
                  <td>Anlegen</td>
                  <td>Jg. {c.grade}, danach Schüler/innen importieren</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="card stack-sm" aria-label="Folgen">
        <h3>Folgen</h3>
        <ul>
          <li>{p.leavers.count} Abgänger/innen verlassen die Schule{p.leavers.sample.length ? ` (u. a. ${p.leavers.sample.slice(0, 3).map((s) => s.name).join(', ')})` : ''}.</li>
          <li>{p.accounts.students} Schüler- und {p.accounts.parents} Eltern-Konten werden gesperrt (nicht gelöscht).</li>
          <li>{p.courses_removed} Kurse mit {p.lessons_removed} Stunden entfallen mit den Abgangsklassen.</li>
          <li>{p.rooms} Kursräume werden archiviert, {p.gradebooks} Notenbücher abgeschlossen.</li>
        </ul>
        {p.warnings.length > 0 && (
          <Alert kind="warning" title="Zu beachten">
            <ul>{p.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
          </Alert>
        )}
      </section>
    </div>
  );
}

export default function WechselPage() {
  useTitle('Schuljahreswechsel');
  const toast = useToast();
  const runs = useApi((signal) => http.get<Run[]>('/year-change/runs', undefined, { signal }), []);
  const [plan, setPlan] = useState<PlanForm>(() => defaultPlan());
  const [preview, setPreview] = useState<Preview | null>(null);
  const [done, setDone] = useState<Run | null>(null);
  const set = (patch: Partial<PlanForm>) => {
    setPlan((p) => ({ ...p, ...patch }));
    setPreview(null);
  };
  const lastRun = runs.data?.find((r) => !r.undone_at);

  const makePreview = async (p: PlanForm = plan) => {
    const r = await http.post<Preview>('/year-change/preview', toRequest(p));
    setPreview(r);
    setDone(null);
  };

  return (
    <div className="page page-narrow stack">
      <div className="page-head">
        <h1>
          Schuljahreswechsel{' '}
          <HelpTip>Stuft die Klassen hoch, trägt Abgänger aus, legt neue Klassen an, archiviert Kursräume und schließt Notenbücher ab. Zuerst sehen Sie eine Vorschau; erst „Ausführen“ ändert etwas. Danach lässt sich der Wechsel rückgängig machen, solange der Plan nicht weiter verändert wurde. Empfehlung: vorher eine Sicherung erstellen.</HelpTip>
        </h1>
      </div>
      {runs.error ? <ErrorBox error={runs.error} onRetry={runs.reload} /> : null}
      {runs.initialLoading && <Loading />}

      {lastRun && (
        <Alert kind="info" title={`Letzter Wechsel: ${lastRun.old_year} → ${lastRun.new_year}`}
          action={
            <AsyncButton
              className="btn btn-sm"
              confirm="Den letzten Schuljahreswechsel rückgängig machen?"
              onClick={async () => {
                await http.post('/year-change/undo');
                toast.success('Schuljahreswechsel rückgängig gemacht');
                invalidateAll();
                setPreview(null);
                setDone(null);
                runs.reload();
              }}
            >
              <Icon name="undo" /> Rückgängig
            </AsyncButton>
          }
        >
          {formatDateTime(lastRun.at)} – {runText(lastRun)}. {lastRun.notes.join(' ')}
        </Alert>
      )}

      {done && (
        <Alert kind="success" title={`Schuljahr ${done.new_year} angelegt`}>
          {runText(done)}. Nächste Schritte:{' '}
          <Link to="/daten">neue Schüler/innen importieren</Link>, <Link to="/planung/kurse">Kurse prüfen</Link>,{' '}
          <Link to="/planung/generator">Stundenplan erzeugen</Link>.
        </Alert>
      )}

      <section className="card stack-sm">
        <h2>1. Vorgaben</h2>
        <div className="form-grid">
          <Field label="Beginn des neuen Schuljahres" htmlFor="yc-start" help="Montag der ersten Schulwoche. Der bisherige Beginn bleibt im Verlauf.">
            <input id="yc-start" type="date" value={plan.new_year_start} onChange={(e) => set({ new_year_start: e.target.value })} />
          </Field>
          <Field label="Abschlussjahrgang" htmlFor="yc-final" help="Klassen ab diesem Jahrgang verlassen die Schule. Leer = höchster vorhandener Jahrgang. Einzelne Klassen können Sie in der Vorschau abweichend behandeln.">
            <input id="yc-final" type="number" min={1} max={13} value={plan.final_grade ?? ''} placeholder="automatisch" onChange={(e) => set({ final_grade: e.target.value ? Number(e.target.value) : null })} />
          </Field>
          <Field label="Kursräume" htmlFor="yc-rooms" help="Archivierte Kursräume bleiben lesbar, sind aber geschlossen. „Nur gelöschte“: Räume von Kursen und Klassen, die entfallen.">
            <select id="yc-rooms" value={plan.archive_rooms} onChange={(e) => set({ archive_rooms: e.target.value as PlanForm['archive_rooms'] })}>
              <option value="removed">nur Räume entfallener Kurse und Klassen archivieren</option>
              <option value="all">alle Kursräume archivieren</option>
              <option value="none">nicht archivieren</option>
            </select>
          </Field>
        </div>
        <div className="stack-sm">
          <Toggle checked={plan.rename_classes} onChange={(v) => set({ rename_classes: v })}>Klassennamen hochzählen (5a → 6a)</Toggle>
          <Toggle checked={plan.deactivate_accounts} onChange={(v) => set({ deactivate_accounts: v })}>Konten der Abgänger/innen sperren</Toggle>
          <Toggle checked={plan.lock_gradebooks} onChange={(v) => set({ lock_gradebooks: v })}>Notenbücher abschließen</Toggle>
          <Toggle checked={plan.clear_lessons} onChange={(v) => set({ clear_lessons: v })}>Stundenplan leeren (neuer Plan wird danach erzeugt)</Toggle>
        </div>
        <Leavers plan={plan} onChange={(ids) => set({ extra_leavers: ids })} />
        <h3>Neue Klassen</h3>
        <NewClasses plan={plan} onChange={(c) => set({ new_classes: c })} />
        <div>
          <AsyncButton className="btn btn-primary" onClick={() => makePreview()}>
            <Icon name="eye" /> Vorschau erstellen
          </AsyncButton>
        </div>
      </section>

      {preview && (
        <section className="stack" aria-label="Vorschau">
          <h2>2. Vorschau</h2>
          <PreviewView
            p={preview}
            onRule={async (id, a, auto) => {
              const next = setRule(plan, id, a, auto);
              setPlan(next);
              try {
                await makePreview(next);
              } catch (e) {
                toast.error(e, 'Vorschau');
              }
            }}
          />
          <section className="card stack-sm">
            <h2>3. Ausführen</h2>
            <p className="small" style={{ margin: 0 }}>
              Das ändert Klassen, Schülerlisten und Konten der ganzen Schule. Erstellen Sie vorher eine Sicherung unter <Link to="/betrieb">Betrieb</Link>.
            </p>
            <div>
              <AsyncButton
                className="btn btn-danger"
                disabled={!preview.can_execute}
                confirm={`Schuljahr ${preview.new_year} jetzt anlegen? ${preview.leavers.count} Abgänger/innen werden ausgetragen.`}
                onClick={async () => {
                  const r = await http.post<Run>('/year-change/execute', { plan: toRequest(plan), token: preview.token });
                  invalidateAll();
                  setPreview(null);
                  setDone(r);
                  setPlan(defaultPlan());
                  runs.reload();
                  toast.success('Schuljahreswechsel ausgeführt');
                }}
              >
                <Icon name="play" /> Schuljahreswechsel ausführen
              </AsyncButton>
            </div>
          </section>
        </section>
      )}
    </div>
  );
}
