/** Kompetenzrahmen verwalten: anlegen, aus Vorlage, importieren (JSON/CSV), bearbeiten, exportieren, archivieren. */
import { useState } from 'react';
import { Modal } from '../../components/Modal';
import { AsyncButton, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { compApi, type FrameworkSummary } from './api';
import { FrameworkEditor } from './FrameworkEditor';
import { DEFAULT_LEVELS, draftOf, type Draft } from './logic';

export function FrameworksTab({ canManage }: { canManage: boolean }) {
  const toast = useToast();
  const q = useApi((signal) => compApi.frameworks(canManage, signal), [canManage], { live: ['competency'] });
  const [editor, setEditor] = useState<{ id: number | null; draft: Draft | null } | null>(null);
  const [templates, setTemplates] = useState(false);
  const [importing, setImporting] = useState(false);
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;

  const edit = async (f: FrameworkSummary) => {
    const full = await compApi.framework(f.id);
    setEditor({ id: f.id, draft: draftOf(full) });
  };

  return (
    <div className="stack">
      {canManage && (
        <div className="row">
          <button type="button" className="btn btn-primary" onClick={() => setEditor({ id: null, draft: null })}>
            Neuer Rahmen
          </button>
          <button type="button" className="btn" onClick={() => setTemplates(true)}>
            Aus Vorlage
          </button>
          <button type="button" className="btn" onClick={() => setImporting(true)}>
            Importieren
          </button>
        </div>
      )}
      {!q.data.length && <Empty icon="list">Noch kein Kompetenzrahmen.</Empty>}
      <ul className="cp-fw-list">
        {q.data.map((f) => (
          <li key={f.id} className={`card cp-fw${f.archived ? ' cp-archived' : ''}`}>
            <div className="row-between">
              <strong>{f.name}</strong>
              {f.archived && <span className="badge">Archiviert</span>}
            </div>
            <div className="small muted">
              {f.areas} Bereiche · {f.competencies} Kompetenzen · {f.levels.length} Niveaustufen{f.subject ? ` · ${f.subject}` : ''}
            </div>
            {f.description && <div className="small">{f.description}</div>}
            <div className="small muted">Stufen: {f.levels.join(' → ')}</div>
            <div className="row cp-fw-actions">
              <a className="btn btn-sm" href={compApi.exportUrl(f.id, 'json')}>
                Export JSON
              </a>
              <a className="btn btn-sm" href={compApi.exportUrl(f.id, 'csv')}>
                Export CSV
              </a>
              {canManage && (
                <>
                  <AsyncButton className="btn btn-sm" onClick={() => edit(f)}>
                    Bearbeiten
                  </AsyncButton>
                  <AsyncButton
                    className="btn btn-sm"
                    onClick={async () => {
                      await compApi.archiveFramework(f.id, !f.archived);
                      q.reload();
                    }}
                  >
                    {f.archived ? 'Wiederherstellen' : 'Archivieren'}
                  </AsyncButton>
                  <AsyncButton
                    className="btn btn-sm btn-danger"
                    confirm={`Rahmen „${f.name}“ löschen? Das geht nur, wenn noch keine Lernstände vorliegen.`}
                    onClick={async () => {
                      try {
                        await compApi.deleteFramework(f.id);
                        q.reload();
                      } catch (e) {
                        toast.error(e, 'Rahmen löschen');
                      }
                    }}
                  >
                    Löschen
                  </AsyncButton>
                </>
              )}
            </div>
          </li>
        ))}
      </ul>
      {editor && <FrameworkEditor frameworkId={editor.id} initial={editor.draft} onClose={() => setEditor(null)} onSaved={q.reload} />}
      {templates && <TemplateDialog onClose={() => setTemplates(false)} onDone={q.reload} />}
      {importing && <ImportDialog onClose={() => setImporting(false)} onDone={q.reload} />}
    </div>
  );
}

function TemplateDialog({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const q = useApi((signal) => compApi.templates(signal), []);
  return (
    <Modal title="Vorlage übernehmen" onClose={onClose} footer={<button type="button" className="btn" onClick={onClose}>Schließen</button>}>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!q.data && !q.error && <Loading />}
      <ul className="cp-fw-list">
        {(q.data ?? []).map((t) => (
          <li key={t.key} className="card cp-fw">
            <strong>{t.name}</strong>
            <div className="small">{t.description}</div>
            <div className="small muted">
              {t.areas} Bereiche · {t.competencies} Kompetenzen · Stufen: {t.levels.join(' → ')}
            </div>
            <AsyncButton
              className="btn btn-primary btn-sm"
              onClick={async () => {
                await compApi.useTemplate(t.key);
                toast.success('Rahmen angelegt – er lässt sich jetzt anpassen');
                onDone();
                onClose();
              }}
            >
              Übernehmen
            </AsyncButton>
          </li>
        ))}
      </ul>
    </Modal>
  );
}

function ImportDialog({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const [format, setFormat] = useState<'json' | 'csv'>('json');
  const [content, setContent] = useState('');
  const [name, setName] = useState('');
  const [levels, setLevels] = useState(DEFAULT_LEVELS.join('; '));
  const read = async (file: File | undefined) => {
    if (!file) return;
    setContent(await file.text());
    setFormat(file.name.toLowerCase().endsWith('.csv') ? 'csv' : 'json');
    if (!name) setName(file.name.replace(/\.[^.]+$/, ''));
  };
  return (
    <Modal
      title="Rahmen importieren"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            disabled={!content.trim()}
            onClick={async () => {
              await compApi.importFramework({
                format,
                content,
                name: name.trim() || undefined,
                levels: format === 'csv' ? levels.split(/[;,]/).map((x) => x.trim()).filter(Boolean) : undefined,
              });
              toast.success('Rahmen importiert');
              onDone();
              onClose();
            }}
          >
            Importieren
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <Field label="Datei" htmlFor="cp-imp-file" help="JSON wie beim Export, oder CSV mit den Spalten Bereich; Kompetenz; Kürzel (optional); Beschreibung je Stufe (optional).">
          <input id="cp-imp-file" type="file" accept=".json,.csv,text/csv,application/json" onChange={(e) => void read(e.target.files?.[0])} />
        </Field>
        <Field label="Format" htmlFor="cp-imp-format">
          <select id="cp-imp-format" value={format} onChange={(e) => setFormat(e.target.value as 'json' | 'csv')}>
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
          </select>
        </Field>
        <Field label="Name" htmlFor="cp-imp-name" help="Bei CSV Pflicht; bei JSON überschreibt er den Namen aus der Datei.">
          <input id="cp-imp-name" value={name} maxLength={200} onChange={(e) => setName(e.target.value)} />
        </Field>
        {format === 'csv' && (
          <Field label="Niveaustufen" htmlFor="cp-imp-levels" help="Beschriftungen der Stufen, getrennt durch Semikolon (2 bis 6).">
            <input id="cp-imp-levels" value={levels} onChange={(e) => setLevels(e.target.value)} />
          </Field>
        )}
        <Field label="Inhalt" htmlFor="cp-imp-content" help="Wird aus der Datei gefüllt; lässt sich auch hier einfügen.">
          <textarea id="cp-imp-content" rows={8} value={content} onChange={(e) => setContent(e.target.value)} />
        </Field>
      </div>
    </Modal>
  );
}
