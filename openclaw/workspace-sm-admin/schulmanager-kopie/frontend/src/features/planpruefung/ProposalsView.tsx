import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AbbrList } from '../../components/Abbr';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, Empty, ErrorBox, Loading, ProgressBar } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDate, formatDateTime } from '../../lib/dates';
import { proposalsApi, type ProposalPackage, type ProposalVariant, type ProposalsResponse } from './api';
import { highlights, impactText, isActionable, metricDeltas, STATUS_LABELS, verdict } from './logic';
import './planpruefung.css';

const LIVE = ['proposals', 'timetable', 'teachers', 'rooms', 'classes', 'courses', 'curricula', 'settings'];

/** Lädt die Pakete (live, bei laufender Berechnung zusätzlich im Takt) – gemeinsam für Seite und Planungs-Tab. */
export function useProposals(enabled = true) {
  const q = useApi<ProposalsResponse>((signal) => proposalsApi.list(signal), [], { live: LIVE, enabled });
  const computing = (q.data?.summary.computing ?? 0) > 0;
  const { reload } = q;
  useEffect(() => {
    if (!computing) return undefined;
    const t = window.setInterval(reload, 3000);
    return () => window.clearInterval(t);
  }, [computing, reload]);
  return q;
}

function MetricTable({ v }: { v: ProposalVariant }) {
  const rows = metricDeltas(v.metrics_before, v.metrics_after);
  if (rows.length === 0) return null;
  return (
    <table className="pp-metrics" aria-label={`Kennzahlen vorher und nachher: ${v.title}`}>
      <tbody>
        {rows.map((r) => (
          <tr key={r.key}>
            <th scope="row">{r.label}</th>
            <td className={r.tone === 'good' ? 'pp-tone-good' : r.tone === 'bad' ? 'pp-tone-bad' : undefined}>
              {r.text}
              <span className="sr-only">{r.tone === 'good' ? ' (besser)' : r.tone === 'bad' ? ' (schlechter)' : ' (unverändert)'}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ChangeList({ v }: { v: ProposalVariant }) {
  if (v.changes.length === 0) return null;
  return (
    <details className="disclosure">
      <summary>
        {v.key === 'vertretung' ? 'Betroffene Stunden' : 'Änderungen'} ({v.changes.length})
      </summary>
      <ul className="pp-changes">
        {v.changes.slice(0, 60).map((c) => (
          <li key={c.course_id}>
            <strong>{c.label}</strong>
            {c.classes.length > 0 && (
              <>
                {' '}
                (<AbbrList kind="class" ids={c.classes} />)
              </>
            )}
            {c.cover ? `: ${c.cover}` : null}
            {!c.cover && (c.from.length > 0 || c.to.length > 0) ? `: ${c.from.join(', ') || '–'} → ${c.to.join(', ') || '–'}` : null}
            {c.rooms.map((r, i) => (
              <div key={i} className="xsmall muted">
                Raum {r.old.join(', ') || '–'} → {r.new.join(', ') || '–'} ({r.where})
              </div>
            ))}
          </li>
        ))}
        {v.changes.length > 60 && <li>… {v.changes.length - 60} weitere</li>}
      </ul>
    </details>
  );
}

function VariantCard({ pkg, v, hints, note, canDecide, onDone }: { pkg: ProposalPackage; v: ProposalVariant; hints: string[]; note: string; canDecide: boolean; onDone: () => void }) {
  const toast = useToast();
  const deltas = metricDeltas(v.metrics_before, v.metrics_after);
  const vd = verdict(deltas);
  return (
    <article className="pp-variant" aria-label={v.title}>
      <div>
        <h4>{v.title}</h4>
        {hints.length > 0 && (
          <div className="row" style={{ gap: 4, marginTop: 4 }}>
            {hints.map((h) => (
              <span key={h} className="badge badge-info">
                {h}
              </span>
            ))}
          </div>
        )}
      </div>
      <p className="small muted" style={{ margin: 0 }}>
        {v.description}
      </p>
      <MetricTable v={v} />
      <p className="small" style={{ margin: 0 }}>
        {impactText(v)}
        {v.key !== 'vertretung' && deltas.length > 0 ? ` · ${vd.better} besser, ${vd.worse} schlechter` : ''}
      </p>
      {v.remaining.length > 0 && (
        <Alert kind="warning" title={`Danach noch offen: ${v.remaining.length}`}>
          <ul className="small">
            {v.remaining.slice(0, 4).map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </Alert>
      )}
      {v.affected_teachers.length > 0 && (
        <p className="xsmall muted" style={{ margin: 0 }}>
          Lehrkräfte: <AbbrList kind="teacher" ids={v.affected_teachers.slice(0, 12)} />
          {v.affected_teachers.length > 12 ? ` … +${v.affected_teachers.length - 12}` : ''}
        </p>
      )}
      <ChangeList v={v} />
      <div className="pp-actions">
        {v.key !== 'vertretung' && (
          <Link to={`/planung/vorschlaege/${pkg.id}/${v.id}`} className="btn btn-sm">
            <Icon name="eye" /> Entwurf ansehen
          </Link>
        )}
        {canDecide && (
          <AsyncButton
            className="btn btn-primary"
            confirm={
              v.key === 'vertretung'
                ? 'Planänderung nicht durchführen und die betroffenen Stunden per Vertretung abdecken?'
                : `„${v.title}“ als neuen Stundenplan übernehmen? Betroffene Lehrkräfte werden informiert; Rückgängig über „Verlauf & Audit“.`
            }
            onClick={async () => {
              try {
                await proposalsApi.accept(pkg.id, v.id, note);
                toast.success(v.key === 'vertretung' ? 'Entschieden: Vertretung statt Planänderung' : 'Der Plan wurde übernommen');
              } catch (e) {
                toast.error(e, 'Plan übernehmen');
              } finally {
                onDone();
              }
            }}
          >
            <Icon name="check" /> Diesen Plan nehmen
          </AsyncButton>
        )}
      </div>
    </article>
  );
}

function PackageCard({ pkg, canDecide, onDone, progress }: { pkg: ProposalPackage; canDecide: boolean; onDone: () => void; progress?: { done: number; total: number } | null }) {
  const toast = useToast();
  const [note, setNote] = useState('');
  const variants = (pkg.variants ?? []).filter((v) => v.status === 'bereit');
  const hints = highlights(variants);
  const postponed = pkg.status === 'offen' && !isActionable(pkg);
  return (
    <section className={`card pp-package${postponed ? ' pp-postponed' : ''}`} aria-label={pkg.title}>
      <div className="row-between">
        <h3 style={{ margin: 0 }}>{pkg.title}</h3>
        <span className={`badge ${pkg.status === 'offen' ? (postponed ? 'badge-info' : 'badge-warning') : 'badge-info'}`}>
          {postponed ? 'zurückgestellt' : pkg.status === 'offen' ? 'wartet auf Entscheidung' : STATUS_LABELS[pkg.status]}
        </span>
      </div>
      <p className="small muted" style={{ margin: 0 }}>
        Berechnet {formatDateTime(pkg.created_at)}
        {pkg.valid_from ? ` · Anlass gilt ab ${formatDate(pkg.valid_from)}` : ''}
        {pkg.trigger_labels.length > 0 ? ` · ${pkg.trigger_labels.join(', ')}` : ''}
      </p>
      {pkg.reasons.length > 0 && (
        <details className="disclosure">
          <summary>
            {pkg.problem_count} Problem{pkg.problem_count === 1 ? '' : 'e'} im Plan
          </summary>
          <ul className="warning-list small">
            {pkg.reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </details>
      )}
      {pkg.status === 'berechnung' && (
        <ProgressBar value={progress && progress.total > 0 ? progress.done / progress.total : 0.05} label={progress ? `Lösungen werden berechnet … (${Math.min(progress.done + 1, progress.total)} von ${progress.total})` : 'Lösungen werden berechnet …'} />
      )}
      {pkg.status === 'offen' && (
        <>
          <div className="pp-variants">
            {variants.map((v) => (
              <VariantCard key={v.id} pkg={pkg} v={v} hints={hints.get(v.id) ?? []} note={note} canDecide={canDecide} onDone={onDone} />
            ))}
          </div>
          {canDecide && (
            <div className="pp-note">
              <input
                type="text"
                value={note}
                maxLength={500}
                onChange={(e) => setNote(e.target.value)}
                aria-label="Anmerkung oder Grund (optional)"
                placeholder="Anmerkung oder Grund (optional)"
              />
              {postponed ? (
                <AsyncButton
                  className="btn btn-sm"
                  onClick={async () => {
                    try {
                      await proposalsApi.wake(pkg.id);
                    } catch (e) {
                      toast.error(e);
                    } finally {
                      onDone();
                    }
                  }}
                >
                  Wieder anzeigen
                </AsyncButton>
              ) : (
                <AsyncButton
                  className="btn btn-sm"
                  title="Blendet den Vorschlag für 24 Stunden aus Zähler und Startseite aus"
                  onClick={async () => {
                    try {
                      await proposalsApi.postpone(pkg.id, 24);
                      toast.info('Zurückgestellt für 24 Stunden');
                    } catch (e) {
                      toast.error(e);
                    } finally {
                      onDone();
                    }
                  }}
                >
                  <Icon name="clock" /> Später
                </AsyncButton>
              )}
              <AsyncButton
                className="btn btn-sm"
                confirm="Alle Vorschläge dieses Pakets verwerfen? Die gleiche Problemlage wird erst nach der nächsten Änderung erneut vorgeschlagen."
                onClick={async () => {
                  try {
                    await proposalsApi.discard(pkg.id, note);
                    toast.info('Vorschlag verworfen');
                  } catch (e) {
                    toast.error(e);
                  } finally {
                    onDone();
                  }
                }}
              >
                <Icon name="x" /> Verwerfen
              </AsyncButton>
            </div>
          )}
        </>
      )}
    </section>
  );
}

function Recent({ items }: { items: ProposalPackage[] }) {
  if (items.length === 0) return null;
  return (
    <details className="disclosure">
      <summary>Zuletzt entschieden ({items.length})</summary>
      <ul className="small">
        {items.map((p) => (
          <li key={p.id}>
            <strong>{p.title}</strong> – {STATUS_LABELS[p.status]}
            {p.decided_by ? ` von ${p.decided_by}` : ''}
            {p.decided_at ? ` (${formatDateTime(p.decided_at)})` : p.updated_at ? ` (${formatDateTime(p.updated_at)})` : ''}
            {p.decision_note ? ` – ${p.decision_note}` : ''}
            {p.informed.length > 0 ? ` · informiert: ${p.informed.length} Lehrkraft/Lehrkräfte` : ''}
          </li>
        ))}
      </ul>
    </details>
  );
}

/** Offene Vorschlagspakete mit Variantenvergleich, Entscheidung und Verlauf. */
export function ProposalsList({ data, reload, canDecide }: { data: ProposalsResponse; reload: () => void; canDecide: boolean }) {
  const open = data.open;
  return (
    <div className="stack">
      <h2 style={{ margin: 0 }}>
        Offene Vorschläge{' '}
        <HelpTip label="Hilfe zu den Vorschlägen">
          Wenn sich am Plan etwas ändert (Lehrkraft, Raum, Kurs …) und dadurch Probleme entstehen, rechnet das System mehrere Lösungen aus. Nichts wird
          ohne Ihre Entscheidung geändert. Mit „Diesen Plan nehmen“ wird die gewählte Variante zum neuen Stundenplan; betroffene Lehrkräfte werden
          informiert. Rückgängig machen können Sie das unter „Verlauf &amp; Audit“. Ein Vorschlag ist veraltet, sobald sich der Plan danach geändert
          hat – er wird dann automatisch neu berechnet.
        </HelpTip>
      </h2>
      {open.length === 0 ? (
        <Empty icon="checkCircle" title="Keine offenen Vorschläge">
          {data.check.open_count > 0 ? 'Für die offenen Probleme liegt zurzeit kein Vorschlag vor.' : 'Der Stundenplan ist in Ordnung.'}
        </Empty>
      ) : (
        open.map((p) => <PackageCard key={p.id} pkg={p} canDecide={canDecide} onDone={reload} progress={data.summary.builder?.package_id === p.id ? data.summary.builder : null} />)
      )}
      <Recent items={data.recent} />
    </div>
  );
}

/** Eigenständige Ansicht (Seite „Planvorschläge“). */
export function ProposalsView({ canDecide }: { canDecide: boolean }) {
  const q = useProposals();
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  return <ProposalsList data={q.data} reload={q.reload} canDecide={canDecide} />;
}
