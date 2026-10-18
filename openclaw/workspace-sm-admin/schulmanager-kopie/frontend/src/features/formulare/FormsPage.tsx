/**
 * `/formulare` – Formular-Baukasten: Familien/Schüler/Lehrkräfte füllen aus („Ausfüllen“, „Meine Formulare“), Klassenleitung,
 * Sekretariat und Schulleitung prüfen („Eingang“), Verwaltung gestaltet („Vorlagen“, „Bibliothek“).
 */
import { useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { PageHelp } from '../../components/Help';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { AsyncButton, Empty, ErrorBox, Field, Loading, Tabs } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useTitle } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { formatDate } from '../../lib/dates';
import { formsApi, type AvailableForm, type FormsMeta, type FormTemplate } from './api';
import { SubmissionList } from './components';
import { FillDialog } from './FillDialog';
import { audienceText, TEMPLATE_LABEL, TEMPLATE_TONE, workflowText } from './logic';
import { SubmissionDetail } from './SubmissionDetail';
import './formulare.css';

const LIVE = ['forms'];

// ---------------------------------------------------------------------------------------------- Ausfüllen
function AvailablePanel({ onFill }: { onFill: (templateId: number, studentId?: string) => void }) {
  const q = useApi((signal) => formsApi.available(signal), [], { live: LIVE });
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (q.initialLoading) return <Loading />;
  const rows: AvailableForm[] = q.data ?? [];
  if (!rows.length) return <Empty icon="list" title="Zurzeit gibt es keine offenen Formulare für Sie." />;
  return (
    <ul className="fm-cards">
      {rows.map((f) => (
        <li key={f.id} className="card fm-card">
          <div className="card-head">
            <h2>{f.title}</h2>
            <span className="badge badge-info">{f.category_label}</span>
          </div>
          {f.description && <p style={{ margin: '0 0 8px' }}>{f.description}</p>}
          <p className="small muted" style={{ margin: '0 0 8px' }}>
            {f.open_until ? `Bis ${formatDate(f.open_until)} · ` : ''}
            {f.fields} Felder{f.sensitive ? ' · enthält geschützte Angaben' : ''}
          </p>
          <div className="stack" style={{ gap: 6 }}>
            {f.needs_student && f.students.length > 0 ? (
              f.students.map((s) => (
                <div key={s.id} className="row row-between fm-who">
                  <span>
                    {s.name}
                    {s.class_id ? <span className="muted"> ({s.class_id})</span> : null}
                  </span>
                  {f.once && s.submission_id ? (
                    <span className="badge badge-success">abgegeben</span>
                  ) : (
                    <button type="button" className="btn btn-primary btn-sm" onClick={() => onFill(f.id, s.id)}>
                      Ausfüllen
                    </button>
                  )}
                </div>
              ))
            ) : (
              <div>
                <button type="button" className="btn btn-primary" onClick={() => onFill(f.id)}>
                  Ausfüllen
                </button>
              </div>
            )}
          </div>
          <div className="row" style={{ gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
            <a className="btn btn-sm btn-ghost" href={formsApi.blankPdfUrl(f.id)} target="_blank" rel="noopener">
              <Icon name="print" /> Leer ausdrucken
            </a>
            {f.legacy_pdf && (
              <a className="btn btn-sm btn-ghost" href={formsApi.legacyPdfUrl(f.legacy_pdf, f.students[0]?.id)} target="_blank" rel="noopener">
                <Icon name="download" /> Bisheriger Vordruck
              </a>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

function MinePanel({ onOpen }: { onOpen: (id: number) => void }) {
  const q = useApi((signal) => formsApi.submissions({ scope: 'mine' }, signal), [], { live: LIVE });
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (q.initialLoading) return <Loading />;
  return <SubmissionList rows={q.data ?? []} onOpen={onOpen} empty="Sie haben noch kein Formular abgegeben." />;
}

// ---------------------------------------------------------------------------------------------- Eingang
function InboxPanel({ onOpen }: { onOpen: (id: number) => void }) {
  const [view, setView] = useState<'mine' | 'open' | 'all'>('mine');
  const [templateId, setTemplateId] = useState<string>('');
  const [classId, setClassId] = useState('');
  const [search, setSearch] = useState('');
  const q = useApi(
    (signal) =>
      formsApi.submissions(
        {
          scope: view === 'mine' ? 'inbox' : 'all',
          open_only: view === 'open' || undefined,
          template_id: templateId ? Number(templateId) : undefined,
          class_id: classId || undefined,
          q: search.trim() || undefined,
        },
        signal,
      ),
    [view, templateId, classId, search],
    { live: LIVE },
  );
  const all = useApi((signal) => formsApi.submissions({}, signal), [], { live: LIVE });
  const options = useMemo(() => {
    const t = new Map<number, string>();
    const c = new Set<string>();
    for (const s of all.data ?? []) {
      t.set(s.template_id, s.template_title);
      if (s.class_id) c.add(s.class_id);
    }
    return { templates: [...t.entries()].sort((a, b) => a[1].localeCompare(b[1], 'de')), classes: [...c].sort((a, b) => a.localeCompare(b, 'de', { numeric: true })) };
  }, [all.data]);
  return (
    <div className="stack">
      <div className="toolbar fm-filters">
        <Field label="Anzeige" htmlFor="fm-view">
          <select id="fm-view" value={view} onChange={(e) => setView(e.target.value as 'mine' | 'open' | 'all')}>
            <option value="mine">Wartet auf meine Entscheidung</option>
            <option value="open">Alle offenen</option>
            <option value="all">Alle Einreichungen</option>
          </select>
        </Field>
        <Field label="Formular" htmlFor="fm-tpl">
          <select id="fm-tpl" value={templateId} onChange={(e) => setTemplateId(e.target.value)}>
            <option value="">Alle</option>
            {options.templates.map(([id, title]) => (
              <option key={id} value={id}>
                {title}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Klasse" htmlFor="fm-cls">
          <select id="fm-cls" value={classId} onChange={(e) => setClassId(e.target.value)}>
            <option value="">Alle</option>
            {options.classes.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Suche" htmlFor="fm-q">
          <input id="fm-q" type="search" value={search} placeholder="Name oder Titel" onChange={(e) => setSearch(e.target.value)} />
        </Field>
      </div>
      {templateId && (
        <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
          <a className="btn btn-sm" href={formsApi.exportCsvUrl(Number(templateId))} download>
            <Icon name="download" /> CSV-Export
          </a>
          <a className="btn btn-sm" href={formsApi.exportPdfUrl(Number(templateId))} target="_blank" rel="noopener">
            <Icon name="download" /> PDF-Archiv
          </a>
          <HelpTip>Exportiert alle Einreichungen dieses Formulars, die Sie sehen dürfen. Jeder Export wird protokolliert.</HelpTip>
        </div>
      )}
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading ? <Loading /> : <SubmissionList rows={q.data ?? []} onOpen={onOpen} showSubmitter empty={view === 'mine' ? 'Nichts wartet auf Ihre Entscheidung.' : 'Keine Einreichungen gefunden.'} />}
    </div>
  );
}

// ---------------------------------------------------------------------------------------------- Vorlagen
function TemplateRow({ t, meta, onChanged }: { t: FormTemplate; meta: FormsMeta; onChanged: () => void }) {
  const toast = useToast();
  const nav = useNavigate();
  const run = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      toast.success(ok);
      onChanged();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return (
    <li className="card fm-card">
      <div className="card-head">
        <h2>
          <Link to={`/formulare/vorlage/${t.id}`}>{t.title}</Link>
        </h2>
        <span className={`badge badge-${TEMPLATE_TONE[t.status]}`}>{TEMPLATE_LABEL[t.status]}</span>
      </div>
      <p className="small muted" style={{ margin: '0 0 6px' }}>
        {t.category_label} · Version {t.version} · {t.definition.fields.length} Felder
        {t.sensitive ? ' · geschützt' : ''}
      </p>
      <p className="small" style={{ margin: '0 0 2px' }}>
        <strong>Ausfüllen:</strong> {audienceText(t.definition, meta.audience_roles)}
      </p>
      <p className="small" style={{ margin: '0 0 8px' }}>
        <strong>Prüfung:</strong> {workflowText(t.definition.workflow.steps, t.definition.workflow.auto_complete, meta.approvers)}
        {t.definition.actions.length ? ` · ${t.definition.actions.length} Aktion(en)` : ''}
      </p>
      <p className="small muted" style={{ margin: '0 0 8px' }}>
        {t.counts?.total ?? 0} Einreichungen, {t.counts?.open ?? 0} offen
      </p>
      <div className="row" style={{ gap: 6, flexWrap: 'wrap' }}>
        <Link className="btn btn-sm btn-primary" to={`/formulare/vorlage/${t.id}`}>
          <Icon name="edit" /> Bearbeiten
        </Link>
        {t.status !== 'aktiv' && (
          <AsyncButton className="btn btn-sm" onClick={() => run(() => formsApi.setStatus(t.id, 'aktiv'), 'Veröffentlicht')}>
            Veröffentlichen
          </AsyncButton>
        )}
        {t.status === 'aktiv' && (
          <AsyncButton className="btn btn-sm" onClick={() => run(() => formsApi.setStatus(t.id, 'archiviert'), 'Archiviert')}>
            Archivieren
          </AsyncButton>
        )}
        <a className="btn btn-sm btn-ghost" href={formsApi.blankPdfUrl(t.id)} target="_blank" rel="noopener">
          <Icon name="print" /> PDF
        </a>
        <AsyncButton
          className="btn btn-sm btn-ghost"
          onClick={async () => {
            const copy = await formsApi.duplicate(t.id);
            nav(`/formulare/vorlage/${copy.id}`);
          }}
        >
          <Icon name="copy" /> Kopieren
        </AsyncButton>
        {(t.counts?.total ?? 0) === 0 && (
          <AsyncButton className="btn btn-sm btn-ghost" confirm={`„${t.title}“ wirklich löschen?`} onClick={() => run(() => formsApi.remove(t.id), 'Gelöscht')}>
            <Icon name="trash" /> Löschen
          </AsyncButton>
        )}
      </div>
    </li>
  );
}

function TemplatesPanel({ meta }: { meta: FormsMeta }) {
  const q = useApi((signal) => formsApi.templates(signal), [], { live: LIVE });
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (q.initialLoading) return <Loading />;
  const rows = q.data ?? [];
  return (
    <div className="stack">
      <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
        <Link className="btn btn-primary" to="/formulare/vorlage/neu">
          <Icon name="plus" /> Neues Formular
        </Link>
        <Link className="btn" to="/formulare?tab=bibliothek">
          <Icon name="copy" /> Aus der Bibliothek
        </Link>
      </div>
      {rows.length === 0 ? <Empty icon="list" title="Noch keine Formulare – starten Sie mit einem Beispiel aus der Bibliothek." /> : (
        <ul className="fm-cards">
          {rows.map((t) => (
            <TemplateRow key={t.id} t={t} meta={meta} onChanged={q.reload} />
          ))}
        </ul>
      )}
    </div>
  );
}

function LibraryPanel({ meta }: { meta: FormsMeta }) {
  const nav = useNavigate();
  const q = useApi((signal) => formsApi.library(signal), []);
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (q.initialLoading) return <Loading />;
  return (
    <ul className="fm-cards">
      {(q.data ?? []).map((e) => (
        <li key={e.key} className="card fm-card">
          <div className="card-head">
            <h2>{e.title}</h2>
            <span className="badge badge-info">{e.category_label}</span>
          </div>
          <p style={{ margin: '0 0 8px' }}>{e.description}</p>
          <p className="small muted" style={{ margin: '0 0 8px' }}>
            {e.definition.fields.length} Felder · {audienceText(e.definition, meta.audience_roles)} · {workflowText(e.definition.workflow.steps, e.definition.workflow.auto_complete, meta.approvers)}
            {e.definition.actions.some((a) => a.type === 'create_absence') ? ' · legt die Beurlaubung/Fehlzeit an' : ''}
          </p>
          <AsyncButton
            className="btn btn-primary btn-sm"
            onClick={async () => {
              const created = await formsApi.adopt(e.key);
              nav(`/formulare/vorlage/${created.id}`);
            }}
          >
            <Icon name="copy" /> Übernehmen und anpassen
          </AsyncButton>
        </li>
      ))}
    </ul>
  );
}

// ---------------------------------------------------------------------------------------------- Seite
type Tab = 'ausfuellen' | 'meine' | 'eingang' | 'vorlagen' | 'bibliothek';

export default function FormsPage() {
  useTitle('Formulare');
  const meta = useApi((signal) => formsApi.meta(signal), []);
  const summary = useApi((signal) => formsApi.summary(signal), [], { live: LIVE });
  const [params, setParams] = useSearchParams();
  const [fill, setFill] = useState<{ id: number; student?: string } | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const m = meta.data;
  const tabs = useMemo(() => {
    if (!m) return [];
    const s = summary.data;
    return [
      { key: 'ausfuellen' as Tab, label: `Ausfüllen${s?.to_fill ? ` (${s.to_fill})` : ''}`, hidden: !m.submit },
      { key: 'meine' as Tab, label: `Meine Formulare${s?.mine_open ? ` (${s.mine_open})` : ''}`, hidden: !m.submit },
      { key: 'eingang' as Tab, label: `Eingang${s?.to_decide ? ` (${s.to_decide})` : ''}`, hidden: !m.inbox },
      { key: 'vorlagen' as Tab, label: 'Vorlagen', hidden: !m.manage },
      { key: 'bibliothek' as Tab, label: 'Bibliothek', hidden: !m.manage },
    ];
  }, [m, summary.data]);
  if (meta.error) return <ErrorBox error={meta.error} onRetry={meta.reload} />;
  if (!m) return <Loading />;
  const visible = tabs.filter((t) => !t.hidden);
  const wanted = params.get('tab') as Tab | null;
  const first: Tab = m.inbox && (summary.data?.to_decide ?? 0) > 0 ? 'eingang' : (visible[0]?.key ?? 'ausfuellen');
  const tab: Tab = wanted && visible.some((t) => t.key === wanted) ? wanted : first;
  const reloadAll = () => {
    summary.reload();
  };
  return (
    <div className="page fm-page">
      <div className="page-head">
        <h1>
          Formulare{' '}
          <PageHelp label="Hilfe zu Formularen">
            Anträge, Einverständnisse und Rückmeldungen der Schule – online ausfüllen oder als PDF ausdrucken. Eingereichte Formulare liegen verschlüsselt und sind nur für die Beteiligten sichtbar.
          </PageHelp>
        </h1>
      </div>
      <Tabs label="Formulare" tabs={tabs} active={tab} onChange={(k) => setParams(k === first ? {} : { tab: k })} />
      <div className="fm-body">
        {tab === 'ausfuellen' && <AvailablePanel onFill={(id, student) => setFill({ id, student })} />}
        {tab === 'meine' && <MinePanel onOpen={setOpen} />}
        {tab === 'eingang' && <InboxPanel onOpen={setOpen} />}
        {tab === 'vorlagen' && <TemplatesPanel meta={m} />}
        {tab === 'bibliothek' && <LibraryPanel meta={m} />}
      </div>
      {fill && (
        <FillDialog
          templateId={fill.id}
          studentId={fill.student}
          onClose={() => setFill(null)}
          onDone={(s) => {
            setFill(null);
            setOpen(s.id);
            reloadAll();
          }}
        />
      )}
      {open !== null && <SubmissionDetail id={open} onClose={() => setOpen(null)} onChanged={reloadAll} />}
    </div>
  );
}
