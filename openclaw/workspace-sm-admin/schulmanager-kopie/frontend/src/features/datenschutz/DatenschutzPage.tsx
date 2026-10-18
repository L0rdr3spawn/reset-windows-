/**
 * `/datenschutz` – Löschkonzept (DSGVO Art. 5, 17) und Betroffenenrechte (Art. 15, 20).
 * Reiter: Fristen · Warteliste · Vorschau · Protokoll · Betroffene (Auskunft, Sofort-Löschen; Recht `privacy.subject`).
 * Daten: `/privacy/*`; Logik in `logic.ts`. Doku: `docs/DATENSCHUTZ-LOESCHKONZEPT.md`.
 */
import { useEffect, useState } from 'react';
import { http } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, Empty, ErrorBox, Field, Loading, Tabs } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { formatDate, formatDateTime } from '../../lib/dates';
import {
  ACTION_LABELS,
  MODE_LABELS,
  clampDays,
  confirmMatches,
  daysText,
  diffSettings,
  dueText,
  groupByCategory,
  previewSummary,
  type ErasePreview,
  type Leaver,
  type LogEntry,
  type Overview,
  type Preview,
  type PrivacySettings,
} from './logic';

type Area = 'fristen' | 'warteliste' | 'vorschau' | 'protokoll' | 'betroffene';

function Fristen({ data, reload }: { data: Overview; reload: () => void }) {
  const toast = useToast();
  const [draft, setDraft] = useState<PrivacySettings>(data.settings);
  useEffect(() => setDraft(data.settings), [data.settings]);
  const changes = diffSettings(data.settings, draft);
  const dirty = Object.keys(changes).length > 0;
  const setKind = (key: string, patch: Partial<{ days: number; age_days: number }>) =>
    setDraft((d) => ({ ...d, kinds: d.kinds.map((k) => (k.key === key ? { ...k, ...patch } : k)) }));

  return (
    <div className="stack">
      <section className="card stack-sm">
        <h2>
          Allgemein{' '}
          <HelpTip>
            Wer nicht mehr im Planungsdokument steht, kommt in die Warteliste „ausgetreten“; das Konto wird gesperrt. Frühestens nach der Wartezeit löscht die Wartung die Daten – je Datenart nach der dort eingestellten Frist. Die Fristen sind Vorschläge, keine Rechtsberatung; bitte mit Landesvorgaben und Datenschutzbeauftragten abgleichen.
          </HelpTip>
        </h2>
        <div className="form-grid">
          <Field label="Wartezeit nach Austritt (Tage)" htmlFor="ds-grace" help="Mindestfrist für alle Datenarten. Bis dahin lässt sich ein Austritt zurücknehmen.">
            <input id="ds-grace" type="number" min={0} max={3650} value={draft.grace_days} onChange={(e) => setDraft({ ...draft, grace_days: clampDays(e.target.value, draft.grace_days) })} />
          </Field>
          <Field label="Audit-Protokoll aufbewahren (Tage)" htmlFor="ds-audit" help={`0 = nie löschen. Vorschlag: ${data.settings.defaults.audit_days} Tage (1 Jahr) – genug für Nachvollziehbarkeit, kurz genug für die Speicherbegrenzung.`}>
            <input id="ds-audit" type="number" min={0} max={3650} value={draft.audit_days} onChange={(e) => setDraft({ ...draft, audit_days: clampDays(e.target.value, draft.audit_days) })} />
          </Field>
          <Field label="Löschprotokoll aufbewahren (Tage)" htmlFor="ds-log" help="Das Löschprotokoll enthält nur Datenart, Anzahl und Zeitpunkt, keine Inhalte. 0 = nie löschen.">
            <input id="ds-log" type="number" min={0} max={3650} value={draft.log_days} onChange={(e) => setDraft({ ...draft, log_days: clampDays(e.target.value, draft.log_days) })} />
          </Field>
        </div>
        <label className="check">
          <input type="checkbox" checked={draft.auto_purge} onChange={(e) => setDraft({ ...draft, auto_purge: e.target.checked })} /> Fälliges automatisch löschen (Wartungslauf){' '}
          <HelpTip>Aus: Die Wartung trägt Ausgetretene nur in die Warteliste ein; gelöscht wird erst, wenn Sie unter „Vorschau“ den Lauf selbst starten.</HelpTip>
        </label>
      </section>

      {groupByCategory(draft.kinds).map((g) => (
        <section className="card stack-sm" key={g.category}>
          <h2>{g.label}</h2>
          <div className="table-wrap">
            <table className="table table-compact">
              <caption className="sr-only">Aufbewahrungsfristen: {g.label}</caption>
              <thead>
                <tr>
                  <th scope="col">Datenart</th>
                  <th scope="col" className="num">Nach Austritt (Tage)</th>
                  <th scope="col" className="num">Nach Alter (Tage)</th>
                  <th scope="col">Löschweg</th>
                </tr>
              </thead>
              <tbody>
                {g.kinds.map((k) => (
                  <tr key={k.key}>
                    <th scope="row">
                      {k.label}{' '}
                      <HelpTip>
                        {k.description} Rechtsgrundlage (Hinweis): {k.legal || '–'}.{k.last ? ' Wird zuletzt gelöscht, wenn alle anderen Datenarten der Person bereinigt sind.' : ''}
                      </HelpTip>
                    </th>
                    <td className="num">
                      <input
                        aria-label={`${k.label}: Tage nach Austritt`}
                        type="number"
                        min={0}
                        max={3650}
                        value={k.days}
                        onChange={(e) => setKind(k.key, { days: clampDays(e.target.value, k.days) })}
                      />
                      {k.days < draft.grace_days && <div className="small muted">wirkt ab {draft.grace_days} (Wartezeit)</div>}
                    </td>
                    <td className="num">
                      {k.has_age ? (
                        <>
                          <input
                            aria-label={`${k.label}: Tage nach Alter`}
                            type="number"
                            min={0}
                            max={3650}
                            value={k.age_days ?? 0}
                            onChange={(e) => setKind(k.key, { age_days: clampDays(e.target.value, k.age_days ?? 0) })}
                          />
                          <div className="small muted">{daysText(k.age_days ?? 0)}</div>
                        </>
                      ) : (
                        <span className="muted">–</span>
                      )}
                    </td>
                    <td>{k.how}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}

      <div>
        <AsyncButton
          className="btn btn-primary"
          disabled={!dirty}
          onClick={async () => {
            await http.put('/privacy/settings', changes);
            toast.success('Fristen gespeichert');
            reload();
          }}
        >
          <Icon name="check" /> Speichern
        </AsyncButton>
      </div>
    </div>
  );
}

function Warteliste({ canEdit }: { canEdit: boolean }) {
  const toast = useToast();
  const list = useApi((signal) => http.get<{ leavers: Leaver[]; grace_days: number }>('/privacy/leavers', undefined, { signal }), []);
  if (list.error) return <ErrorBox error={list.error} onRetry={list.reload} />;
  if (!list.data) return <Loading />;
  const rows = list.data.leavers;
  if (rows.length === 0) return <Empty icon="check" title="Niemand ist als ausgetreten vermerkt" />;
  return (
    <section className="card stack-sm">
      <div className="table-wrap">
        <table className="table table-compact">
          <caption className="sr-only">Warteliste ausgetretener Personen</caption>
          <thead>
            <tr>
              <th scope="col">Person</th>
              <th scope="col">Klasse</th>
              <th scope="col">Ausgetreten</th>
              <th scope="col">Löschung vollständig</th>
              <th scope="col" className="num">Offene Datenarten</th>
              <th scope="col"><span className="sr-only">Aktionen</span></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.student_id}>
                <th scope="row">
                  {r.name || <span className="muted">(Name bereits gelöscht)</span>} <span className="mono small muted">{r.student_id}</span>
                </th>
                <td>{r.class_id || '–'}</td>
                <td>{formatDate(r.left_at)}</td>
                <td>{r.status === 'erledigt' ? `erledigt ${formatDate(r.done_at)}` : `${formatDate(r.last_due_at)} (${dueText(r.days_left, r.status)})`}</td>
                <td className="num">{r.status === 'erledigt' ? 0 : r.open}</td>
                <td className="actions">
                  {canEdit && r.status === 'wartend' && (
                    <AsyncButton
                      className="btn btn-sm"
                      title="Nur möglich, wenn die Person wieder unter Stammdaten steht"
                      onClick={async () => {
                        await http.post(`/privacy/leavers/${encodeURIComponent(r.student_id)}/cancel`);
                        toast.success('Austritt zurückgenommen, Konto wieder frei');
                        list.reload();
                      }}
                    >
                      <Icon name="undo" /> Zurücknehmen
                    </AsyncButton>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Vorschau() {
  const toast = useToast();
  const [data, setData] = useState<Preview | null>(null);
  const [error, setError] = useState<unknown>(null);
  const load = async () => {
    setError(null);
    try {
      setData(await http.get<Preview>('/privacy/preview'));
    } catch (e) {
      setError(e);
    }
  };
  useEffect(() => {
    void load();
  }, []);
  if (error) return <ErrorBox error={error} onRetry={load} />;
  if (!data) return <Loading />;
  return (
    <div className="stack">
      <section className="card stack-sm">
        <div className="card-head">
          <h2>
            Was würde gelöscht? <HelpTip>Die Vorschau zählt nur und ändert nichts. „Fällig“ heißt: Die Frist der Datenart ist abgelaufen – der nächste Wartungslauf löscht es.</HelpTip>
          </h2>
          <AsyncButton
            className="btn btn-danger"
            confirm="Alle fälligen Daten jetzt endgültig löschen? Das kann nicht rückgängig gemacht werden."
            onClick={async () => {
              const r = await http.post<Record<string, number>>('/privacy/run');
              toast.success(`Lauf beendet: ${r.rows_purged ?? 0} Einträge gelöscht, ${r.rows_expired ?? 0} nach Alter`);
              await load();
            }}
          >
            <Icon name="trash" /> Fälliges jetzt löschen
          </AsyncButton>
        </div>
        <p className="small" role="status">{previewSummary(data)}</p>
      </section>
      {data.people.map((p) => (
        <section className="card stack-sm" key={p.student_id}>
          <h3>
            {p.name || p.student_id} <span className="mono small muted">{p.student_id}</span> <span className="small muted">seit {formatDate(p.left_at)}</span>
          </h3>
          <div className="table-wrap">
            <table className="table table-compact">
              <caption className="sr-only">Betroffene Daten von {p.name || p.student_id}</caption>
              <thead>
                <tr>
                  <th scope="col">Datenart</th>
                  <th scope="col" className="num">Einträge</th>
                  <th scope="col">Fällig</th>
                </tr>
              </thead>
              <tbody>
                {p.items.map((i) => (
                  <tr key={i.kind}>
                    <th scope="row">{i.label}</th>
                    <td className="num">{i.count}</td>
                    <td>{i.due ? <span className="badge badge-danger">jetzt</span> : formatDate(i.due_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
      {data.expiry.length > 0 && (
        <section className="card stack-sm">
          <h3>Nach Alter fällig</h3>
          <ul>
            {data.expiry.map((e) => (
              <li key={e.kind}>{e.label}: {e.count}</li>
            ))}
          </ul>
        </section>
      )}
      {data.people.length === 0 && data.expiry.length === 0 && <Empty icon="check" title="Nichts zu löschen" />}
    </div>
  );
}

function Protokoll() {
  const list = useApi((signal) => http.get<{ entries: LogEntry[] }>('/privacy/log', { limit: 300 }, { signal }), []);
  if (list.error) return <ErrorBox error={list.error} onRetry={list.reload} />;
  if (!list.data) return <Loading />;
  if (list.data.entries.length === 0) return <Empty icon="list" title="Noch nichts gelöscht" />;
  return (
    <section className="card stack-sm">
      <p className="small muted">
        Protokoll der Löschungen
        <HelpTip>Das Protokoll hält fest, was wann gelöscht wurde, nie die Inhalte.</HelpTip>
      </p>
      <div className="table-wrap">
        <table className="table table-compact">
          <caption className="sr-only">Löschprotokoll</caption>
          <thead>
            <tr>
              <th scope="col">Zeitpunkt</th>
              <th scope="col">Datenart</th>
              <th scope="col" className="num">Anzahl</th>
              <th scope="col">Aktion</th>
              <th scope="col">Anlass</th>
              <th scope="col">Person</th>
              <th scope="col">Durch</th>
            </tr>
          </thead>
          <tbody>
            {list.data.entries.map((e) => (
              <tr key={e.id}>
                <td>{formatDateTime(e.at)}</td>
                <td>{e.label}</td>
                <td className="num">{e.count}</td>
                <td>{ACTION_LABELS[e.action] ?? e.action}</td>
                <td>{MODE_LABELS[e.mode] ?? e.mode}{e.note ? ` (${e.note})` : ''}</td>
                <td className="mono small">{e.subject || '–'}</td>
                <td>{e.actor}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Betroffene() {
  const toast = useToast();
  const [byUser, setByUser] = useState(false);
  const [value, setValue] = useState('');
  const [reason, setReason] = useState('');
  const [preview, setPreview] = useState<ErasePreview | null>(null);
  const [confirm, setConfirm] = useState('');
  const query: Record<string, string> = byUser ? { user_id: value.trim() } : { student_id: value.trim() };
  const exportHref = `/api/v1/privacy/export?${new URLSearchParams(query).toString()}`;

  return (
    <div className="stack">
      <section className="card stack-sm">
        <h2>
          Person wählen{' '}
          <HelpTip>
            Auskunft (Art. 15/20) liefert alle gespeicherten Daten als ZIP mit Datei „daten.json“ und einer lesbaren Übersicht. Sofort-Löschen (Art. 17) entfernt die Person aus dem Planungsdokument und löscht alle Datenarten ohne Wartefrist – unwiderruflich, mit Eintrag im Audit-Protokoll.
          </HelpTip>
        </h2>
        <label className="check">
          <input type="checkbox" checked={byUser} onChange={(e) => { setByUser(e.target.checked); setPreview(null); }} /> Konto-Nummer statt Schüler-ID verwenden (Eltern, Personal)
        </label>
        <Field label={byUser ? 'Konto-Nummer' : 'Schüler-ID (z. B. S00012)'} htmlFor="ds-person">
          <input id="ds-person" value={value} onChange={(e) => { setValue(e.target.value); setPreview(null); }} />
        </Field>
        <div className="row">
          <a className={`btn${value.trim() ? '' : ' disabled'}`} href={value.trim() ? exportHref : undefined} aria-disabled={!value.trim()} download>
            <Icon name="download" /> Auskunft erstellen (ZIP)
          </a>
          <AsyncButton
            className="btn"
            disabled={!value.trim()}
            onClick={async () => {
              setPreview(await http.get<ErasePreview>('/privacy/erase/preview', query));
              setConfirm('');
            }}
          >
            <Icon name="eye" /> Löschen vorbereiten
          </AsyncButton>
        </div>
      </section>
      {preview && (
        <section className="card stack-sm">
          <h2>Sofort-Löschen: {preview.name || preview.confirm_with}</h2>
          <Alert kind="warning" title="Nicht rückgängig zu machen">
            Es werden {preview.total} Einträge endgültig gelöscht.
          </Alert>
          <ul>
            {preview.items.filter((i) => i.count > 0).map((i) => (
              <li key={i.kind}>{i.label}: {i.count}</li>
            ))}
          </ul>
          <Field label="Anlass (kurz, ohne persönliche Angaben)" htmlFor="ds-reason">
            <input id="ds-reason" maxLength={200} value={reason} onChange={(e) => setReason(e.target.value)} />
          </Field>
          <Field label={`Zur Bestätigung „${preview.confirm_with}“ eintippen`} htmlFor="ds-confirm">
            <input id="ds-confirm" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="off" />
          </Field>
          <div>
            <AsyncButton
              className="btn btn-danger"
              disabled={!confirmMatches(confirm, preview.confirm_with)}
              onClick={async () => {
                await http.post('/privacy/erase', { ...(byUser ? { user_id: Number(value.trim()) } : { student_id: value.trim() }), confirm, reason });
                toast.success('Person gelöscht');
                setPreview(null);
                setValue('');
              }}
            >
              <Icon name="trash" /> Endgültig löschen
            </AsyncButton>
          </div>
        </section>
      )}
    </div>
  );
}

export default function DatenschutzPage() {
  useTitle('Datenschutz');
  const user = useUser();
  const canSubject = user.permissions.includes('privacy.subject');
  const [area, setArea] = useState<Area>('fristen');
  const overview = useApi((signal) => http.get<Overview>('/privacy/overview', undefined, { signal }), []);
  return (
    <div className="stack">
      <h1>Datenschutz und Löschkonzept</h1>
      {overview.error ? <ErrorBox error={overview.error} onRetry={overview.reload} /> : null}
      {!overview.data && !overview.error && <Loading />}
      {overview.data && (
        <>
          <Tabs<Area>
            label="Bereiche"
            active={area}
            onChange={setArea}
            tabs={[
              { key: 'fristen', label: 'Fristen' },
              { key: 'warteliste', label: `Warteliste${overview.data.waiting ? ` (${overview.data.waiting})` : ''}` },
              { key: 'vorschau', label: 'Vorschau' },
              { key: 'protokoll', label: 'Protokoll' },
              { key: 'betroffene', label: 'Betroffene', hidden: !canSubject },
            ]}
          />
          {area === 'fristen' && <Fristen data={overview.data} reload={overview.reload} />}
          {area === 'warteliste' && <Warteliste canEdit />}
          {area === 'vorschau' && <Vorschau />}
          {area === 'protokoll' && <Protokoll />}
          {area === 'betroffene' && canSubject && <Betroffene />}
        </>
      )}
    </div>
  );
}
