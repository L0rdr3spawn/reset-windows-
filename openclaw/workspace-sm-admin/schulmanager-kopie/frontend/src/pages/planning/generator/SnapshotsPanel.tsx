import { useState } from 'react';
import { calendar } from '../../../api/endpoints';
import type { PlanPeriod } from '../../../api/types';
import { Alert, AsyncButton, Empty, ErrorBox, Field, Loading } from '../../../components/ui';
import { ConfirmDialog } from '../../../components/ConfirmDialog';
import { HelpTip } from '../../../components/HelpTip';
import { Icon } from '../../../components/Icon';
import { Modal } from '../../../components/Modal';
import { useToast } from '../../../context/ToastContext';
import { useApi } from '../../../hooks/useApi';
import { formatDateTime } from '../../../lib/dates';
import { periodSpan } from '../../../lib/planPeriods';
import { genApi } from './api';
import { PlanPreviewDialog } from './PlanPreviewDialog';
import { ResultTiles } from './ResultTiles';
import { plural } from './logic';
import type { ApplyResult, SnapshotMeta } from './types';
import './generator.css';

/** Text zur Übernahme/Wiederherstellung inklusive Aufsichten. */
export function applyResultText(r: ApplyResult): string {
  const base = `${plural(r.lessons, 'Block', 'Blöcke')} im neuen Stundenplan.`;
  if (r.duties === null || r.duties === undefined) return base;
  const open = r.duties_open ? `, davon ${r.duties_open} noch ohne Lehrkraft` : '';
  return `${base} Pausenaufsichten neu berechnet: ${plural(r.duties, 'Aufsicht', 'Aufsichten')}${open}.`;
}

/** Namen, Notiz und Umfang (ein Zeitraum oder ausdrücklich der ganze Plan) für einen neuen Plan-Stand erfragen. */
export function SaveSnapshotDialog({
  jobId,
  variant,
  defaultName,
  period: periodHint,
  onSaved,
  onClose,
}: {
  jobId?: string;
  variant?: number;
  defaultName?: string;
  /** Zeitraum des Entwurfs bzw. der Generator-Auswahl (Voreinstellung) */
  period?: string;
  onSaved: (s: SnapshotMeta) => void;
  onClose: () => void;
}) {
  const toast = useToast();
  const [name, setName] = useState(defaultName ?? '');
  const [note, setNote] = useState('');
  const pq = useApi((signal) => calendar.planPeriods(signal), []);
  const periods: PlanPeriod[] = pq.data?.active ? pq.data.periods : [];
  const [scope, setScope] = useState('');
  const chosen = scope || (periods.some((p) => p.id === periodHint) ? (periodHint ?? '') : (pq.data?.target ?? periods[0]?.id ?? ''));
  const whole = periods.length > 0 && chosen === '__all';
  const options = jobId && periodHint ? periods.filter((p) => p.id === periodHint) : periods;
  return (
    <Modal
      title={jobId ? 'Entwurf als Plan-Stand speichern' : 'Aktuellen Plan speichern'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            disabled={!name.trim() || (periods.length > 0 && !chosen)}
            onClick={async () => {
              const s = await genApi.saveSnapshot({
                name: name.trim(),
                note: note.trim(),
                job_id: jobId,
                variant,
                ...(periods.length ? (whole ? { whole: true } : { period: chosen }) : {}),
              });
              toast.success('Plan-Stand gespeichert');
              onSaved(s);
              onClose();
            }}
          >
            <Icon name="check" /> Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <Field label="Name" htmlFor="snap-name">
          <input id="snap-name" type="text" maxLength={120} value={name} placeholder="Stand Herbst A" onChange={(e) => setName(e.target.value)} autoFocus />
        </Field>
        {periods.length > 0 && (
          <Field
            label="Umfang"
            htmlFor="snap-scope"
            help="Ein Plan-Stand enthält standardmäßig nur den Stundenplan eines Zeitraums. Beim Wiederherstellen wird dann nur dieser Zeitraum ersetzt. „Ganzer Plan“ speichert alle Zeiträume zusammen."
          >
            <select id="snap-scope" value={chosen} onChange={(e) => setScope(e.target.value)}>
              {options.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({periodSpan(p)})
                </option>
              ))}
              <option value="__all">Ganzer Plan (alle Zeiträume)</option>
            </select>
          </Field>
        )}
        <Field label="Notiz" htmlFor="snap-note">
          <input id="snap-note" type="text" maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} />
        </Field>
      </div>
    </Modal>
  );
}

function CompareDialog({ snap, onClose }: { snap: SnapshotMeta; onClose: () => void }) {
  const q = useApi((signal) => genApi.snapshot(snap.id, signal), [snap.id]);
  return (
    <Modal title={`Vergleich: ${snap.name}`} onClose={onClose} size="lg">
      <div className="stack">
        {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
        {!q.data && !q.error && <Loading />}
        {q.data && <ResultTiles ev={q.data.evaluation} ctx={{ beforeLabel: 'Aktuell', afterLabel: 'Stand', trace: [], runs: [], unplaced: [] }} />}
      </div>
    </Modal>
  );
}

/**
 * „Plan leeren“ mit Bestätigung; der bisherige Stand bleibt im Verlauf (Rückgängig). Mit Planzeiträumen wählen Sie den
 * Zeitraum (Voreinstellung: der im Generator gewählte); den ganzen Plan leeren Sie nur über die eigene Auswahl.
 */
export function ClearPlanButton({ disabled, period }: { disabled?: boolean; period?: string }) {
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [pick, setPick] = useState('');
  const pq = useApi((signal) => calendar.planPeriods(signal), [], { live: ['settings', 'timetable'] });
  const periods: PlanPeriod[] = pq.data?.active ? pq.data.periods : [];
  const chosen = pick || (periods.some((p) => p.id === period) ? (period ?? '') : '');
  const all = chosen === '__all';
  const current = periods.find((p) => p.id === chosen);
  const needsChoice = periods.length > 0 && !chosen;
  return (
    <>
      <button type="button" className="btn btn-danger" disabled={disabled} onClick={() => setOpen(true)}>
        <Icon name="trash" /> Plan leeren
      </button>
      {open && (
        <ConfirmDialog
          title={periods.length ? 'Welchen Plan leeren?' : 'Plan leeren?'}
          confirmLabel={all ? 'Ganzen Plan leeren' : current ? `${current.name} leeren` : 'Plan leeren'}
          confirmDisabled={needsChoice}
          danger
          onCancel={() => setOpen(false)}
          onConfirm={async () => {
            const r = await genApi.clear(periods.length ? (all ? { all: true } : { period: chosen }) : {});
            toast.success(`Plan geleert (${plural(r.lessons, 'Block', 'Blöcke')} entfernt)`);
          }}
        >
          {periods.length > 0 && (
            <Field label="Zeitraum" htmlFor="clear-period">
              <select id="clear-period" value={chosen} onChange={(e) => setPick(e.target.value)}>
                <option value="" disabled>
                  Bitte wählen
                </option>
                {periods.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({periodSpan(p)}) – {plural(p.lessons, 'Block', 'Blöcke')}
                  </option>
                ))}
                <option value="__all">Ganzer Plan (alle Zeiträume)</option>
              </select>
            </Field>
          )}
          <p>
            {all
              ? 'Alle Unterrichtsblöcke aller Zeiträume und die zugehörigen Tagesentscheidungen werden entfernt.'
              : periods.length
                ? 'Die Unterrichtsblöcke dieses Zeitraums und die zugehörigen Tagesentscheidungen werden entfernt. Die übrigen Zeiträume bleiben unverändert.'
                : 'Alle Unterrichtsblöcke und die zugehörigen Tagesentscheidungen werden entfernt.'}{' '}
            Kurse, Lehrkräfte und Räume bleiben.
          </p>
          <p className="small muted">Der bisherige Stand bleibt im Verlauf und lässt sich dort rückgängig machen.</p>
        </ConfirmDialog>
      )}
    </>
  );
}

/** Gespeicherte Plan-Stände: speichern, ansehen, mit dem aktuellen Plan vergleichen, wiederherstellen, löschen. */
export function SnapshotsPanel() {
  const toast = useToast();
  const q = useApi((signal) => genApi.snapshots(signal), [], { live: ['timetable'] });
  const [saving, setSaving] = useState(false);
  const [view, setView] = useState<SnapshotMeta | null>(null);
  const [compare, setCompare] = useState<SnapshotMeta | null>(null);
  const [restore, setRestore] = useState<SnapshotMeta | null>(null);
  const [remove, setRemove] = useState<SnapshotMeta | null>(null);
  const [duties, setDuties] = useState(true);
  const [result, setResult] = useState<string | null>(null);
  return (
    <section className="card">
      <div className="row" style={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <h2>
          3. Plan-Stände <HelpTip label="Erklärung: Plan-Stände">Ein Plan-Stand speichert den Stundenplan unter einem Namen. Er bleibt erhalten, auch wenn der Verlauf gekürzt wird. Wiederherstellen legt eine neue Version an und lässt sich über den Verlauf rückgängig machen.</HelpTip>
        </h2>
        <button type="button" className="btn" onClick={() => setSaving(true)}>
          <Icon name="plus" /> Aktuellen Plan speichern
        </button>
      </div>
      {result && (
        <div style={{ marginTop: 12 }}>
          <Alert kind="success" title="Plan-Stand wiederhergestellt">
            {result}
          </Alert>
        </div>
      )}
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!q.data && !q.error && <Loading />}
      {q.data && q.data.length === 0 && <Empty title="Noch keine Plan-Stände" />}
      {q.data && q.data.length > 0 && (
        <ul className="gs-list" style={{ marginTop: 12 }}>
          {q.data.map((s) => (
            <li key={s.id} className="gs-item">
              <div>
                <strong>{s.name}</strong>{' '}
                <span className="gv-badge">{s.period ? s.period_name : 'Ganzer Plan'}</span>
                <div className="gs-meta">
                  {s.created_at ? formatDateTime(s.created_at) : ''} · {s.user} · {plural(s.lessons_count, 'Block', 'Blöcke')} · {s.source === 'entwurf' ? 'aus Entwurf' : 'aus aktuellem Plan'}
                </div>
                {s.note && <div className="gs-meta">{s.note}</div>}
              </div>
              <div className="row" style={{ flexWrap: 'wrap' }}>
                <button type="button" className="btn btn-sm" onClick={() => setView(s)}>
                  Ansehen
                </button>
                <button type="button" className="btn btn-sm" onClick={() => setCompare(s)}>
                  Vergleichen
                </button>
                <button type="button" className="btn btn-sm" onClick={() => setRestore(s)}>
                  Wiederherstellen
                </button>
                <button type="button" className="btn btn-sm btn-danger" onClick={() => setRemove(s)}>
                  Löschen
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {saving && <SaveSnapshotDialog onSaved={() => q.reload()} onClose={() => setSaving(false)} />}
      {view && <PlanPreviewDialog title={`Plan-Stand: ${view.name}`} draftLabel="Stand" load={(k, r, d) => genApi.snapshotView(view.id, k, r, d)} onClose={() => setView(null)} />}
      {compare && <CompareDialog snap={compare} onClose={() => setCompare(null)} />}
      {restore && (
        <ConfirmDialog
          title={`„${restore.name}“ wiederherstellen?`}
          confirmLabel="Wiederherstellen"
          onCancel={() => setRestore(null)}
          onConfirm={async () => {
            const r = await genApi.restoreSnapshot(restore.id, duties);
            setResult(applyResultText(r));
            toast.success('Plan-Stand wiederhergestellt');
          }}
        >
          <p>
            {restore.period
              ? `Nur der Stundenplan von ${restore.period_name} wird durch diesen Stand ersetzt. Die übrigen Zeiträume bleiben unverändert.`
              : 'Der gesamte Stundenplan wird durch diesen Stand ersetzt.'}{' '}
            Der bisherige Plan bleibt im Verlauf und lässt sich rückgängig machen.
          </p>
          <label className="check">
            <input type="checkbox" checked={duties} onChange={(e) => setDuties(e.target.checked)} /> Pausenaufsichten neu berechnen
          </label>
        </ConfirmDialog>
      )}
      {remove && (
        <ConfirmDialog
          title={`„${remove.name}“ löschen?`}
          confirmLabel="Löschen"
          danger
          onCancel={() => setRemove(null)}
          onConfirm={async () => {
            await genApi.deleteSnapshot(remove.id);
            toast.success('Plan-Stand gelöscht');
            q.reload();
          }}
        >
          <p>Dieser Plan-Stand wird endgültig gelöscht. Der aktuelle Stundenplan bleibt unverändert.</p>
        </ConfirmDialog>
      )}
    </section>
  );
}
