/**
 * Seite „API-Zugänge“ (`/api-zugaenge`, Recht `api.own` bzw. `api.manage`; docs/API-ZUGAENGE.md):
 * Liste der Zugänge (eigene, mit `api.manage` alle), Assistent zum Anlegen (Name → Bereiche → Filter → Prüfen) mit
 * Vorschau „Dieser Zugang darf: …“, einmalige Token-Anzeige mit curl-Beispiel, Nutzungsprotokoll und Widerruf.
 */
import { useEffect, useId, useMemo, useState } from 'react';
import { Icon } from '../../components/Icon';
import { HelpTip } from '../../components/HelpTip';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, CopyField, Empty, ErrorBox, Field, FormErrors, Loading, SegmentedControl } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { formatDateTime } from '../../lib/dates';
import { accessApi } from './api';
import { OUTCOME_LABELS, STATUS_LABELS, cleanFilters, emptyDraft, parseList, relevantFilters, searchOptions, stepValid, toggle } from './logic';
import type { AccessDetail, AccessDraft, AccessItem, AccessMeta, CreatedAccess, FilterKind, Preview, ValueOption } from './types';
import './api-zugaenge.css';

const STEPS = ['Name', 'Bereiche', 'Filter', 'Prüfen'];

// =================================================================== Auswahl mit Suche
function ValuePicker({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: ValueOption[];
  value: string[];
  onChange: (v: string[]) => void;
}) {
  const [query, setQuery] = useState('');
  const id = useId();
  const shown = useMemo(() => searchOptions(options, query), [options, query]);
  return (
    <fieldset className="aa-picker">
      <legend>
        {label}
        {value.length > 0 && <span className="badge badge-primary">{value.length} gewählt</span>}
      </legend>
      {options.length === 0 ? (
        <p className="small muted">Für dieses Konto sind hier keine Werte freigebbar.</p>
      ) : (
        <>
          {options.length > 8 && (
            <input id={id} type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Suchen …" aria-label={`${label} suchen`} />
          )}
          <ul className="aa-options">
            {shown.map((o) => (
              <li key={o.id}>
                <label>
                  <input type="checkbox" checked={value.includes(o.id)} onChange={() => onChange(toggle(value, o.id))} />
                  <span>
                    {o.name && o.name !== o.id ? `${o.name} ` : ''}
                    <span className="muted">({o.id})</span>
                  </span>
                </label>
              </li>
            ))}
          </ul>
          {shown.length < options.length && <p className="small muted">Weitere Einträge über die Suche.</p>}
        </>
      )}
    </fieldset>
  );
}

// =================================================================== Assistent
function Wizard({ meta, onClose, onCreated }: { meta: AccessMeta; onClose: () => void; onCreated: (c: CreatedAccess) => void }) {
  const [step, setStep] = useState(0);
  const [draft, setDraft] = useState<AccessDraft>(() => emptyDraft({ expires: meta.limits.default_expires_days, rate: meta.limits.default_rate }));
  const [ipText, setIpText] = useState('');
  const [preview, setPreview] = useState<Preview | null>(null);
  const [error, setError] = useState<unknown>(null);
  const filterKinds = useMemo(() => relevantFilters(meta.areas, draft.areas), [meta.areas, draft.areas]);
  const filterLabel = (k: FilterKind) => meta.filters.find((f) => f.id === k)?.label ?? k;
  const nameId = useId();
  const purposeId = useId();
  const daysId = useId();
  const rateId = useId();
  const ipId = useId();

  const body = (): AccessDraft => ({
    ...draft,
    name: draft.name.trim(),
    purpose: draft.purpose.trim(),
    filters: cleanFilters(draft.filters, filterKinds),
    write: draft.write.filter((w) => draft.areas.includes(w)),
    ip_allow: parseList(ipText),
  });

  useEffect(() => {
    if (step !== 3) return;
    let alive = true;
    setPreview(null);
    setError(null);
    accessApi
      .preview(body())
      .then((p) => alive && setPreview(p))
      .catch((e) => alive && setError(e));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  const next = () => setStep((s) => Math.min(3, s + 1));
  const back = () => setStep((s) => Math.max(0, s - 1));

  return (
    <Modal
      title="Neuer API-Zugang"
      onClose={onClose}
      size="lg"
      footer={
        <>
          <button type="button" className="btn" onClick={step === 0 ? onClose : back}>
            {step === 0 ? 'Abbrechen' : 'Zurück'}
          </button>
          {step < 3 ? (
            <button type="button" className="btn btn-primary" disabled={!stepValid(step, draft)} onClick={next}>
              Weiter
            </button>
          ) : (
            <AsyncButton
              className="btn btn-primary"
              disabled={!preview}
              onClick={async () => {
                try {
                  onCreated(await accessApi.create(body()));
                } catch (e) {
                  setError(e);
                }
              }}
            >
              <Icon name="key" /> Zugang anlegen
            </AsyncButton>
          )}
        </>
      }
    >
      <ol className="aa-steps" aria-label="Schritte">
        {STEPS.map((s, i) => (
          <li key={s} aria-current={i === step ? 'step' : undefined} className={i < step ? 'done' : undefined}>
            {i + 1}. {s}
          </li>
        ))}
      </ol>
      <FormErrors error={error}>
        {step === 0 && (
          <div className="stack">
            <Field label="Name" htmlFor={nameId} help="Wofür oder für wen der Zugang ist, z. B. „Foyer-Monitor“. Erscheint in der Liste und im Protokoll.">
              <input id={nameId} value={draft.name} maxLength={100} onChange={(e) => setDraft({ ...draft, name: e.target.value })} autoFocus />
            </Field>
            <Field label="Zweck (optional)" htmlFor={purposeId} help="Freier Vermerk für spätere Prüfungen, z. B. wer die Anwendung betreibt.">
              <input id={purposeId} value={draft.purpose} maxLength={300} onChange={(e) => setDraft({ ...draft, purpose: e.target.value })} />
            </Field>
            <Field label="Gültig für (Tage)" htmlFor={daysId} help={`Danach läuft der Zugang ab. Höchstens ${meta.limits.max_expires_days} Tage; unbefristete Zugänge gibt es nicht.`}>
              <input
                id={daysId}
                type="number"
                min={1}
                max={meta.limits.max_expires_days}
                value={draft.expires_days}
                onChange={(e) => setDraft({ ...draft, expires_days: Math.max(1, Math.min(meta.limits.max_expires_days, Number(e.target.value) || 1)) })}
              />
            </Field>
          </div>
        )}
        {step === 1 && (
          <div className="stack">
            <p className="small muted">
              Nur lesen ist Standard.
              <HelpTip>Ein Zugang sieht nie mehr als Ihr Konto. Gesundheits- und Förderdaten, private Nachrichten und Schülerlisten lassen sich nicht freigeben.</HelpTip>
            </p>
            <ul className="aa-areas">
              {meta.areas.map((a) => (
                <li key={a.id} className={a.available ? undefined : 'disabled'}>
                  <label>
                    <input
                      type="checkbox"
                      disabled={!a.available}
                      checked={draft.areas.includes(a.id)}
                      onChange={() => setDraft({ ...draft, areas: toggle(draft.areas, a.id), write: draft.write.filter((w) => w !== a.id) })}
                    />
                    <span>
                      <strong>{a.label}</strong>
                      <span className="small muted"> {a.available ? a.description : 'Mit diesem Konto nicht freigebbar.'}</span>
                    </span>
                  </label>
                  {a.write && a.write_available && draft.areas.includes(a.id) && (
                    <label className="aa-write">
                      <input type="checkbox" checked={draft.write.includes(a.id)} onChange={() => setDraft({ ...draft, write: toggle(draft.write, a.id) })} />
                      <span>Auch schreiben (neue Einträge anlegen)</span>
                    </label>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
        {step === 2 && (
          <div className="stack">
            {filterKinds.length === 0 ? (
              <Empty icon="info" title="Keine Filter nötig" />
            ) : (
              <>
                <p className="small muted">
                  Ohne Auswahl sieht der Zugang alles, was Ihr Konto sieht.
                  <HelpTip>Klassen, Lehrkräfte, Räume und Schüler/innen gelten zusammen („oder“); Standorte schränken zusätzlich ein.</HelpTip>
                </p>
                <div className="aa-pickers">
                  {filterKinds.map((k) => (
                    <ValuePicker
                      key={k}
                      label={filterLabel(k)}
                      options={meta.values[k] ?? []}
                      value={draft.filters[k] ?? []}
                      onChange={(v) => setDraft({ ...draft, filters: { ...draft.filters, [k]: v } })}
                    />
                  ))}
                </div>
              </>
            )}
            <details className="aa-more">
              <summary>Weitere Einstellungen</summary>
              <div className="stack">
                <Field label="Erlaubte Adressen" htmlFor={ipId} help="IP-Adressen oder Netze (z. B. 192.168.0.0/24), getrennt durch Komma oder Zeilenumbruch. Leer = von überall.">
                  <textarea id={ipId} rows={2} value={ipText} onChange={(e) => setIpText(e.target.value)} />
                </Field>
                <Field label="Anfragen pro Minute" htmlFor={rateId} help={`Darüber antwortet der Server mit 429. Höchstens ${meta.limits.max_rate}.`}>
                  <input
                    id={rateId}
                    type="number"
                    min={1}
                    max={meta.limits.max_rate}
                    value={draft.rate_limit}
                    onChange={(e) => setDraft({ ...draft, rate_limit: Math.max(1, Math.min(meta.limits.max_rate, Number(e.target.value) || 1)) })}
                  />
                </Field>
              </div>
            </details>
          </div>
        )}
        {step === 3 && (
          <div className="stack">
            {!preview && !error && <Loading />}
            {preview && (
              <>
                <section aria-labelledby="aa-can">
                  <h3 id="aa-can">Dieser Zugang darf</h3>
                  <ul className="aa-list aa-can">
                    {preview.can.map((l) => (
                      <li key={l}>
                        <Icon name="check" /> {l}
                      </li>
                    ))}
                  </ul>
                </section>
                <section aria-labelledby="aa-cannot">
                  <h3 id="aa-cannot">Nie</h3>
                  <ul className="aa-list aa-cannot">
                    {preview.cannot.map((l) => (
                      <li key={l}>{l}</li>
                    ))}
                  </ul>
                </section>
                {preview.warnings.map((w) => (
                  <Alert key={w} kind="warning">
                    {w}
                  </Alert>
                ))}
                <p className="small muted">
                  Gültig {draft.expires_days} Tage, höchstens {draft.rate_limit} Anfragen pro Minute
                  {parseList(ipText).length > 0 ? `, nur von ${parseList(ipText).join(', ')}` : ''}.
                </p>
              </>
            )}
          </div>
        )}
      </FormErrors>
    </Modal>
  );
}

// =================================================================== Token einmalig anzeigen
function TokenDialog({ created, meta, onClose }: { created: CreatedAccess; meta: AccessMeta; onClose: () => void }) {
  return (
    <Modal title="Zugang angelegt" onClose={onClose} footer={<button type="button" className="btn btn-primary" onClick={onClose}>Fertig</button>}>
      <div className="stack">
        <Alert kind="warning" title="Token jetzt kopieren">
          Es wird nur dieses eine Mal angezeigt und ist danach nicht mehr abrufbar.
        </Alert>
        <CopyField value={created.token} label="Token" />
        {created.examples.map((e, i) => (
          <CopyField key={i} value={e} label={i === 0 ? 'Beispielaufruf' : `Beispielaufruf ${i + 1}`} />
        ))}
        <p className="small">
          <a href={meta.docs.llms} target="_blank" rel="noreferrer">
            Beschreibung für KI-Werkzeuge (llms.txt)
          </a>
          {' · '}
          <a href={meta.docs.openapi} target="_blank" rel="noreferrer">
            OpenAPI
          </a>
        </p>
      </div>
    </Modal>
  );
}

// =================================================================== Details / Protokoll
function DetailDialog({ id, onClose }: { id: number; onClose: () => void }) {
  const { data, error, loading } = useApi<AccessDetail>((s) => accessApi.detail(id, s), [id]);
  return (
    <Modal title={data?.name ?? 'API-Zugang'} onClose={onClose} size="lg" footer={<button type="button" className="btn" onClick={onClose}>Schließen</button>}>
      {loading && !data && <Loading />}
      {error != null && !data && <ErrorBox error={error} />}
      {data && (
        <div className="stack">
          {data.summary && (
            <ul className="aa-list aa-can">
              {data.summary.map((l) => (
                <li key={l}>
                  <Icon name="check" /> {l}
                </li>
              ))}
            </ul>
          )}
          <p className="small muted">
            Token beginnt mit {data.prefix}… · {data.use_count} Abrufe · Limit {data.rate_limit}/Minute
            {data.ip_allow.length > 0 ? ` · nur von ${data.ip_allow.join(', ')}` : ''}
          </p>
          <h3>Letzte Aufrufe{data.log_total > data.log.length ? ` (${data.log.length} von ${data.log_total})` : ''}</h3>
          {data.log.length === 0 ? (
            <p className="small muted">Noch nicht benutzt.</p>
          ) : (
            <div className="table-wrap">
              <table className="aa-log">
                <thead>
                  <tr>
                    <th>Zeit</th>
                    <th>Aufruf</th>
                    <th>Ergebnis</th>
                    <th>Adresse</th>
                  </tr>
                </thead>
                <tbody>
                  {data.log.map((l, i) => (
                    <tr key={i}>
                      <td>{formatDateTime(l.at)}</td>
                      <td>
                        {l.method} {l.path}
                      </td>
                      <td>{OUTCOME_LABELS[l.outcome] ?? l.outcome}</td>
                      <td>{l.ip ?? ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}

// =================================================================== Seite
function AccessCard({ item, meta, showOwner, onDetail, onRevoke }: { item: AccessItem; meta: AccessMeta; showOwner: boolean; onDetail: () => void; onRevoke: () => Promise<unknown> }) {
  const areaLabel = (id: string) => meta.areas.find((a) => a.id === id)?.label ?? id;
  const kind = item.status === 'active' ? 'badge-success' : item.status === 'expired' ? 'badge-warning' : 'badge-danger';
  return (
    <li className="card aa-card">
      <div className="aa-card-main">
        <div className="aa-card-title">
          <strong>{item.name}</strong>
          <span className={`badge ${kind}`}>{STATUS_LABELS[item.status]}</span>
          {showOwner && <span className="badge">{item.owner.name}</span>}
        </div>
        {item.purpose && <p className="small muted">{item.purpose}</p>}
        <p className="aa-chips">
          {item.areas.map((a) => (
            <span key={a} className="badge badge-info">
              {areaLabel(a)}
              {item.write.includes(a) ? ' (schreiben)' : ''}
            </span>
          ))}
        </p>
        {item.summary && (
          <ul className="aa-summary small">
            {item.summary.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        )}
        <p className="small muted">
          Läuft ab {formatDateTime(item.expires_at)} · zuletzt benutzt {item.last_used ? formatDateTime(item.last_used) : 'nie'} · {item.use_count} Abrufe
        </p>
      </div>
      <div className="aa-card-actions">
        <button type="button" className="btn btn-sm" onClick={onDetail}>
          <Icon name="list" /> Protokoll
        </button>
        {item.status === 'active' && (
          <AsyncButton className="btn btn-sm btn-danger" confirm={`Zugang „${item.name}“ widerrufen? Anwendungen damit verlieren sofort den Zugriff.`} onClick={onRevoke}>
            <Icon name="trash" /> Widerrufen
          </AsyncButton>
        )}
      </div>
    </li>
  );
}

export default function ApiAccessPage() {
  useTitle('API-Zugänge');
  const toast = useToast();
  const meta = useApi<AccessMeta>((s) => accessApi.meta(s), []);
  const [scope, setScope] = useState<'own' | 'all'>('own');
  const list = useApi<AccessItem[]>((s) => accessApi.list(scope === 'all', s), [scope], { keepPrevious: true });
  const [wizard, setWizard] = useState(false);
  const [created, setCreated] = useState<CreatedAccess | null>(null);
  const [detail, setDetail] = useState<number | null>(null);

  if (meta.error != null && !meta.data) return <ErrorBox error={meta.error} onRetry={meta.reload} />;
  if (!meta.data) return <Loading />;
  const m = meta.data;
  return (
    <div className="aa-page stack">
      <div className="page-head">
        <h1>
          API-Zugänge
          <HelpTip>
            Zugänge für Apps oder KI-Werkzeuge: nur lesen (Standard), nur ausgewählte Bereiche und Filter, befristet und jederzeit widerrufbar. Sie sehen nie mehr als Ihr eigenes Konto.
          </HelpTip>
        </h1>
        <div className="actions">
          {m.can_manage_all && (
            <SegmentedControl
              label="Anzeige"
              value={scope}
              onChange={setScope}
              options={[
                { value: 'own', label: 'Meine' },
                { value: 'all', label: 'Alle' },
              ]}
            />
          )}
          <a className="btn btn-sm" href={m.docs.llms} target="_blank" rel="noreferrer">
            <Icon name="link" /> Beschreibung für KIs
          </a>
          {m.can_create && (
            <button type="button" className="btn btn-primary" onClick={() => setWizard(true)}>
              <Icon name="plus" /> Neuer Zugang
            </button>
          )}
        </div>
      </div>
      {list.error != null && <ErrorBox error={list.error} onRetry={list.reload} />}
      {list.loading && !list.data && <Loading />}
      {list.data && list.data.length === 0 && <Empty icon="key" title="Noch keine API-Zugänge" />}
      {list.data && list.data.length > 0 && (
        <ul className="aa-cards">
          {list.data.map((it) => (
            <AccessCard
              key={it.id}
              item={it}
              meta={m}
              showOwner={scope === 'all'}
              onDetail={() => setDetail(it.id)}
              onRevoke={async () => {
                await accessApi.revoke(it.id);
                toast.success('Zugang widerrufen');
                list.reload();
              }}
            />
          ))}
        </ul>
      )}
      {wizard && (
        <Wizard
          meta={m}
          onClose={() => setWizard(false)}
          onCreated={(c) => {
            setWizard(false);
            setCreated(c);
            list.reload();
          }}
        />
      )}
      {created && <TokenDialog created={created} meta={m} onClose={() => setCreated(null)} />}
      {detail != null && <DetailDialog id={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}
