import { useMemo, useState, type ReactNode } from 'react';
import { Icon } from '../../../components/Icon';
import { ConfirmDialog } from '../../../components/ConfirmDialog';
import { HelpTip } from '../../../components/HelpTip';
import { Alert, ErrorBox, Loading } from '../../../components/ui';
import { useToast } from '../../../context/ToastContext';
import { useApi } from '../../../hooks/useApi';
import type { PlanPeriod } from '../../../api/types';
import { periodSpan } from '../../../lib/planPeriods';
import { genApi } from './api';
import { PlanPreviewDialog } from './PlanPreviewDialog';
import { ResultTiles, type ResultContext } from './ResultTiles';
import { SaveSnapshotDialog, applyResultText } from './SnapshotsPanel';
import { VariantsTable } from './VariantsTable';
import { fmt, plural, recommendation } from './logic';
import type { ApplyResult, VariantSummary } from './types';
import './generator.css';

/** Job-Felder, die der Generator ergänzt (Varianten, Parameter). */
export interface GenJob {
  id: string;
  status: string;
  params?: { time_limit?: number; seed?: number; workers?: number; variants?: number; rules_preview?: boolean; period?: string; copy_from?: string };
  stats?: Record<string, number | string>;
  unplaced?: Record<string, unknown>[];
  lessons_count?: number;
  outdated?: boolean;
  variants?: VariantSummary[];
  best_variant?: number;
  applied_variant?: number | null;
}

function runLine(job: GenJob): string {
  const s = job.stats ?? {};
  const parts: string[] = [];
  if (job.params?.time_limit) parts.push(`Rechenzeit ${fmt(job.params.time_limit)} s je Variante`);
  if (typeof s.runs === 'number') parts.push(plural(s.runs, 'paralleler Lauf', 'parallele Läufe'));
  if (s.seed !== undefined) parts.push(`Startwert ${String(s.seed)}${s.best_seed !== undefined && s.best_seed !== s.seed ? ` (bester Lauf: ${String(s.best_seed)})` : ''}`);
  if (typeof s.iterations === 'number') parts.push(`${s.iterations.toLocaleString('de-DE')} Optimierungsschritte`);
  if (typeof s.variants === 'number') parts.push(plural(s.variants, 'Wochenmuster', 'Wochenmuster'));
  return parts.join(' · ');
}

/**
 * Ergebnis eines Generator-Laufs: anklickbare Kacheln mit Grafiken, Vergleich der Varianten, Vorschau im Raster,
 * Übernehmen mit Bestätigung (Pausenaufsichten werden auf Wunsch gleich neu berechnet) und Speichern als Plan-Stand.
 * `legacy` wird für ältere Läufe ohne Auswertung angezeigt.
 */
export function GeneratorResult({ job, onApplied, legacy, periods = [] }: { job: GenJob; onApplied: () => void; legacy: ReactNode; periods?: PlanPeriod[] }) {
  const toast = useToast();
  const variants = job.variants ?? [];
  const best = job.best_variant ?? 0;
  const [picked, setPicked] = useState<number | null>(null);
  const sel = picked ?? job.applied_variant ?? best;
  const [preview, setPreview] = useState<number | null>(null);
  const [applying, setApplying] = useState<number | null>(null);
  const [saving, setSaving] = useState<number | null>(null);
  const [duties, setDuties] = useState(true);
  const [backup, setBackup] = useState(false);
  const [applied, setApplied] = useState<ApplyResult | null>(null);
  const detail = useApi((signal) => genApi.variant(job.id, sel, signal), [job.id, sel], { enabled: variants.length > 0 });
  const ctx: ResultContext | null = useMemo(
    () =>
      detail.data
        ? {
            beforeLabel: 'Aktuell',
            afterLabel: 'Entwurf',
            trace: detail.data.trace,
            runs: detail.data.runs,
            unplaced: detail.data.unplaced,
          }
        : null,
    [detail.data],
  );
  const done = job.status === 'done';
  const rec = detail.data ? recommendation(detail.data.evaluation.kpis) : null;
  if (variants.length === 0) return <>{legacy}</>;
  const unplaced = detail.data?.unplaced.length ?? job.unplaced?.length ?? 0;
  const jobPeriod = periods.find((p) => p.id === job.params?.period);
  const periodLabel = jobPeriod ? `${jobPeriod.name} (${periodSpan(jobPeriod)})` : job.params?.period ? 'nicht mehr vorhanden' : undefined;
  const label = (i: number) => (variants.length > 1 ? `Variante ${i + 1}` : 'Entwurf');
  return (
    <div className="stack">
      {variants.length > 1 && (
        <VariantsTable
          variants={variants}
          best={best}
          selected={sel}
          done={done}
          onSelect={setPicked}
          onPreview={setPreview}
          onApply={setApplying}
          periodLabel={periodLabel}
        />
      )}
      {detail.error ? <ErrorBox error={detail.error} onRetry={detail.reload} /> : null}
      {!detail.data && !detail.error && <Loading />}
      {detail.data && ctx && (
        <>
          <p className="gr-run">
            {variants.length > 1 ? `${label(sel)} · ` : ''}
            {variants.length === 1 && periodLabel ? `Zeitraum ${periodLabel} · ` : ''}
            {runLine({ ...job, stats: { ...(job.stats ?? {}), ...detail.data.stats } })}
          </p>
          {done && (
            <Alert kind={rec?.tone === 'bad' ? 'warning' : rec?.tone === 'good' ? 'success' : 'info'} title={rec?.title}>
              {rec?.worse.length ? `Schlechter geworden: ${rec.worse.join('; ')}. ` : ''}
              {rec?.advice}
            </Alert>
          )}
          <ResultTiles key={`${job.id}-${sel}`} ev={detail.data.evaluation} ctx={ctx} />
          {unplaced > 0 ? (
            <Alert kind="warning" title={`${plural(unplaced, 'Unterrichtseinheit konnte', 'Unterrichtseinheiten konnten')} nicht verplant werden`}>
              Die Liste steht hinter der Kachel „Unverplante Stunden“.
            </Alert>
          ) : (
            <Alert kind="success" title="Alle Stunden wurden verplant." />
          )}
        </>
      )}
      {applied && (
        <Alert kind="success" title="Stundenplan übernommen">
          {applyResultText(applied)}
        </Alert>
      )}
      {done && (
        <div className="row" style={{ flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-primary" onClick={() => setApplying(sel)}>
            <Icon name="check" /> {variants.length > 1 ? `${label(sel)} übernehmen` : 'Übernehmen'}
          </button>
          <button type="button" className="btn" onClick={() => setPreview(sel)}>
            <Icon name="calendar" /> Im Stundenplan ansehen
          </button>
          <button type="button" className="btn" onClick={() => setSaving(sel)}>
            <Icon name="download" /> Als Plan-Stand speichern
          </button>
          <span className="small muted">{job.lessons_count ? `${job.lessons_count} Blöcke im Entwurf` : ''}</span>
        </div>
      )}
      {job.status === 'applied' && !applied && <Alert kind="success">Dieser Entwurf wurde übernommen.</Alert>}
      {preview !== null && (
        <PlanPreviewDialog
          title={`${label(preview)} im Stundenplan`}
          draftLabel="Entwurf"
          load={(k, r, d) => genApi.variantView(job.id, preview, k, r, d)}
          onClose={() => setPreview(null)}
        />
      )}
      {saving !== null && <SaveSnapshotDialog jobId={job.id} variant={saving} period={job.params?.period} defaultName={variants.length > 1 ? `Variante ${saving + 1}` : 'Entwurf'} onSaved={() => undefined} onClose={() => setSaving(null)} />}
      {applying !== null && (
        <ConfirmDialog
          title={`${label(applying)} als neuen Stundenplan übernehmen?`}
          confirmLabel="Übernehmen"
          onCancel={() => setApplying(null)}
          onConfirm={async () => {
            if (backup) {
              await genApi.saveSnapshot({ name: `Vor Übernahme ${new Date().toLocaleString('de-DE')}`, ...(job.params?.period ? { period: job.params.period } : {}) });
            }
            const r = await genApi.apply(job.id, { variant: applying, regenerate_duties: duties });
            setApplied(r);
            toast.success('Neuer Stundenplan übernommen');
            onApplied();
          }}
        >
          <p>
            {periodLabel ? `Der Stundenplan von ${jobPeriod?.name ?? 'diesem Zeitraum'} wird durch den Entwurf ersetzt, die übrigen Zeiträume bleiben.` : 'Der aktuelle Stundenplan wird durch den Entwurf ersetzt.'}{' '}
            Der bisherige Plan bleibt im Verlauf und lässt sich rückgängig machen.
          </p>
          {job.outdated && <Alert kind="warning" title="Planungsdaten wurden inzwischen geändert">Zwischenzeitliche Stundenplan-Änderungen gehen verloren.</Alert>}
          <label className="check">
            <input type="checkbox" checked={duties} onChange={(e) => setDuties(e.target.checked)} /> Pausenaufsichten neu berechnen{' '}
            <HelpTip label="Erklärung: Pausenaufsichten">Die Aufsichten hängen an den Standorten der Stunden. Ohne Neuberechnung passen sie nach einem neuen Plan oft nicht mehr.</HelpTip>
          </label>
          <label className="check">
            <input type="checkbox" checked={backup} onChange={(e) => setBackup(e.target.checked)} /> Aktuellen Plan vorher als Plan-Stand speichern
          </label>
        </ConfirmDialog>
      )}
    </div>
  );
}
