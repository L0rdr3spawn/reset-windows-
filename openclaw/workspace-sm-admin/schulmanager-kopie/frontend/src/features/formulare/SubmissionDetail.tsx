/**
 * Einreichung ansehen: Antworten, Ablauf, Verlauf, Scans/Anhänge, Entscheidung (Genehmigen/Ablehnen/Erledigt) und PDF.
 */
import { useState } from 'react';
import { errorMessage } from '../../api/client';
import { FileList } from '../../components/FileList';
import { FileUpload } from '../../components/FileUpload';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDate, formatDateTime } from '../../lib/dates';
import { formsApi, type DecideAction, type Submission } from './api';
import { StatusBadge } from './components';
import { EVENT_LABEL, isOpen } from './logic';
import './formulare.css';

function Steps({ s }: { s: Submission }) {
  if (!s.steps.length) return null;
  return (
    <ol className="fm-steps" aria-label="Ablauf">
      {s.steps.map((st, i) => {
        const done = s.status === 'genehmigt' || s.status === 'erledigt' ? true : i < s.step;
        const current = isOpen(s) && i === s.step;
        const rejected = s.status === 'abgelehnt' && i === s.step;
        return (
          <li key={i} className={`fm-step${done ? ' is-done' : ''}${current ? ' is-current' : ''}${rejected ? ' is-rejected' : ''}`} aria-current={current ? 'step' : undefined}>
            <span className="fm-step-dot" aria-hidden="true">
              {done ? '✓' : rejected ? '✕' : i + 1}
            </span>
            <span>{st.label}</span>
          </li>
        );
      })}
    </ol>
  );
}

export function SubmissionDetail({ id, onClose, onChanged }: { id: number; onClose: () => void; onChanged: () => void }) {
  const toast = useToast();
  const q = useApi((signal) => formsApi.submission(id, signal), [id], { live: ['forms'] });
  const [note, setNote] = useState('');
  const [scanKey, setScanKey] = useState(0);
  const s = q.data;

  const run = async (fn: () => Promise<Submission>, ok: string) => {
    try {
      const next = await fn();
      q.setData(next);
      setNote('');
      toast.success(ok);
      onChanged();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const decide = (action: DecideAction, ok: string) => run(() => formsApi.decide(id, action, note.trim()), ok);

  return (
    <Modal title={s ? s.template_title : 'Formular'} onClose={onClose} size="lg">
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {s && (
        <div className="stack fm-detail">
          <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
            <StatusBadge status={s.status} label={s.status_label} />
            {s.overdue && <span className="badge badge-danger">überfällig</span>}
            {s.sensitive && (
              <span className="badge badge-warning">
                geschützt <HelpTip>Enthält Angaben, die besonders geschützt sind (z. B. Gesundheit oder Förderung). Nur berechtigte Personen sehen sie; jedes Ansehen wird protokolliert.</HelpTip>
              </span>
            )}
          </div>
          <p className="small muted" style={{ margin: 0 }}>
            {s.student_name ? `${s.student_name}${s.class_id ? ` (${s.class_id})` : ''} · ` : ''}eingereicht von {s.submitted_by_name} am {formatDateTime(s.created_at)} · Version {s.version}
            {s.due_on ? ` · Bearbeitung bis ${formatDate(s.due_on)}` : ''}
          </p>
          <Steps s={s} />
          <dl className="fm-answers">
            {(s.answers ?? []).map((a) => (
              <div key={a.id} className="fm-answer">
                <dt>{a.label}</dt>
                <dd>{a.display || <span className="muted">–</span>}</dd>
              </div>
            ))}
          </dl>
          {(s.attachments?.length ?? 0) > 0 && <FileList files={s.attachments ?? []} label="Anlagen" compact />}
          {s.decision_note && (
            <div className="alert alert-info">
              <strong>Vermerk:</strong> {s.decision_note}
            </div>
          )}
          {s.result?.actions?.length ? (
            <ul className="fm-actions-result" aria-label="Ausgeführte Aktionen">
              {s.result.actions.map((a, i) => (
                <li key={i} className={a.ok ? 'is-ok' : 'is-fail'}>
                  <Icon name={a.ok ? 'check' : 'alert'} /> {a.message}
                </li>
              ))}
            </ul>
          ) : null}
          {s.result?.actions?.some((a) => !a.ok) && s.staff && (
            <AsyncButton className="btn btn-sm" onClick={() => run(() => formsApi.retry(id), 'Aktionen erneut ausgeführt')}>
              <Icon name="refresh" /> Aktionen erneut ausführen
            </AsyncButton>
          )}

          <section aria-labelledby="fm-scan-h">
            <h3 id="fm-scan-h" style={{ margin: '4px 0' }}>
              Unterschriebener Scan{' '}
              <HelpTip>Ausgedruckt, unterschrieben und fotografiert oder gescannt: hier hochladen. Die Datei liegt verschlüsselt und ist nur für die Beteiligten sichtbar.</HelpTip>
            </h3>
            <FileList
              files={s.scans ?? []}
              emptyText="Noch kein Scan hochgeladen."
              compact
              onDelete={s.can_scan ? async (f) => run(() => formsApi.removeScan(id, f.id), 'Datei entfernt') : undefined}
              canDelete={() => s.can_scan}
            />
            {s.can_scan && (
              <FileUpload
                key={scanKey}
                purpose="form_file"
                compact
                multiple={false}
                accept=".pdf,.jpg,.jpeg,.png,.heic"
                label="Scan oder Foto hochladen"
                showList={false}
                deleteOnRemove={false}
                onUploaded={(f) => {
                  void run(() => formsApi.addScan(id, f.id), 'Scan gespeichert').then(() => setScanKey((k) => k + 1));
                }}
              />
            )}
          </section>

          <section aria-labelledby="fm-hist-h">
            <h3 id="fm-hist-h" style={{ margin: '4px 0' }}>
              Verlauf
            </h3>
            <ul className="fm-history">
              {(s.events ?? []).map((e) => (
                <li key={e.id}>
                  <span className="small muted">{formatDateTime(e.at)}</span> · <strong>{EVENT_LABEL[e.action] ?? e.action}</strong>
                  {e.actor_name ? ` · ${e.actor_name}` : ''}
                  {e.note ? <span className="fm-note"> – {e.note}</span> : null}
                </li>
              ))}
            </ul>
          </section>

          {(s.can_decide || s.can_complete || s.staff) && s.status !== 'zurueckgezogen' && (
            <section aria-labelledby="fm-dec-h" className="fm-decide">
              <h3 id="fm-dec-h" style={{ margin: '4px 0' }}>
                Entscheidung
              </h3>
              <Field label="Vermerk" htmlFor="fm-note" help="Bei „Ablehnen“ Pflicht – die Familie sieht den Text. Sonst freiwillig.">
                <textarea id="fm-note" rows={2} value={note} maxLength={1000} onChange={(e) => setNote(e.target.value)} />
              </Field>
              <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
                {s.can_decide && (
                  <>
                    <AsyncButton className="btn btn-primary" onClick={() => decide('approve', s.step + 1 >= s.steps.length ? 'Genehmigt' : 'Schritt freigegeben')}>
                      <Icon name="check" /> {s.step + 1 >= s.steps.length ? 'Genehmigen' : 'Freigeben & weiter'}
                    </AsyncButton>
                    <AsyncButton className="btn btn-danger" disabled={!note.trim()} title={note.trim() ? undefined : 'Bitte einen Vermerk eingeben'} onClick={() => decide('reject', 'Abgelehnt')}>
                      <Icon name="x" /> Ablehnen
                    </AsyncButton>
                  </>
                )}
                {s.can_complete && (
                  <AsyncButton className="btn" onClick={() => decide('complete', 'Als erledigt markiert')}>
                    <Icon name="check" /> Als erledigt abschließen
                  </AsyncButton>
                )}
                {s.staff && (
                  <AsyncButton className="btn btn-ghost" disabled={!note.trim()} onClick={() => decide('comment', 'Vermerk gespeichert')}>
                    Nur Vermerk speichern
                  </AsyncButton>
                )}
              </div>
            </section>
          )}

          <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
            <a className="btn btn-sm" href={formsApi.submissionPdfUrl(id)} target="_blank" rel="noopener">
              <Icon name="download" /> PDF (Archiv)
            </a>
            {s.can_withdraw && (
              <AsyncButton className="btn btn-sm btn-ghost" confirm="Einreichung wirklich zurückziehen?" onClick={() => run(() => formsApi.withdraw(id), 'Zurückgezogen')}>
                Zurückziehen
              </AsyncButton>
            )}
          </div>
        </div>
      )}
    </Modal>
  );
}
