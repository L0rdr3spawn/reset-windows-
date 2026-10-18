/** Papierkorb des Kursraums: gelöschtes Material, Aufgaben und Ordner wiederherstellen oder endgültig löschen. */
import { useEffect, useId, useState } from 'react';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, Empty, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatWhen } from './logic';
import { daysLeft, trashApi, trashContent, type TrashResponse } from './progress';

export default function TrashDialog({ channelId, onClose, onChanged }: { channelId: number; onClose: () => void; onChanged: () => void }) {
  const toast = useToast();
  const daysId = useId();
  const q = useApi<TrashResponse>((signal) => trashApi.list(channelId, signal), [channelId]);
  const [days, setDays] = useState('');
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (q.data) setDays(String(q.data.retention_days));
  }, [q.data]);

  const run = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      toast.success(ok);
      setError(null);
      q.reload();
      onChanged();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const d = q.data;
  const dayValue = Number(days);
  const daysValid = days.trim() !== '' && Number.isInteger(dayValue) && dayValue >= 1 && dayValue <= 365;
  return (
    <Modal
      title="Papierkorb"
      size="lg"
      onClose={onClose}
      footer={
        <>
          {d?.can_use && d.entries.length > 0 && (
            <AsyncButton
              className="btn btn-danger"
              confirm="Den ganzen Papierkorb endgültig leeren? Das lässt sich nicht rückgängig machen."
              onClick={() => run(() => trashApi.empty(channelId), 'Papierkorb geleert')}
            >
              <Icon name="trash" /> Papierkorb leeren
            </AsyncButton>
          )}
          <button type="button" className="btn" onClick={onClose}>
            Schließen
          </button>
        </>
      }
    >
      <div className="stack-sm">
        <p className="small muted">
          Gelöschtes bleibt {d?.retention_days ?? 30} Tage hier und wird danach automatisch endgültig entfernt.
          <HelpTip>Abgaben, Dateien sowie Abschluss- und Freigaberegeln bleiben beim Wiederherstellen erhalten. Fehlt der ursprüngliche Ordner, landet der Eintrag oben im Kursraum.</HelpTip>
        </p>
        {error && <Alert kind="error">{error}</Alert>}
        {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
        {q.initialLoading && <Loading />}
        {d && !d.can_use && <Alert kind="info">Dafür fehlt das Recht „Kursraum-Papierkorb nutzen“.</Alert>}
        {d && !d.entries.length && <Empty icon="trash">Der Papierkorb ist leer.</Empty>}
        {d && d.entries.length > 0 && (
          <ul className="kr-list" aria-label="Gelöschte Elemente">
            {d.entries.map((e) => {
              const left = daysLeft(e.purge_at);
              return (
                <li key={e.group} className="kr-item">
                  <span className="kr-item-icon" aria-hidden="true">
                    <Icon name={e.kind === 'folder' ? 'folder' : 'trash'} />
                  </span>
                  <div className="kr-item-main">
                    <div className="kr-item-title">{e.name}</div>
                    <div className="kr-item-meta">
                      {e.type_label}
                      {trashContent(e) ? ` · ${trashContent(e)}` : ''} · gelöscht {formatWhen(e.deleted_at)}
                      {e.deleted_by_name ? ` von ${e.deleted_by_name}` : ''}
                    </div>
                    <div className="xsmall muted">{left === null ? '' : left === 0 ? 'Wird heute endgültig entfernt' : left === 1 ? 'Noch 1 Tag' : `Noch ${left} Tage`}</div>
                  </div>
                  {d.can_use && (
                    <div className="kr-item-actions">
                      <AsyncButton className="btn btn-sm" disabled={!e.can_restore} onClick={() => run(() => trashApi.restore(channelId, e.group), `„${e.name}“ wiederhergestellt`)}>
                        <Icon name="undo" /> Wiederherstellen
                      </AsyncButton>
                      <AsyncButton
                        className="btn btn-sm btn-ghost"
                        disabled={!e.can_restore}
                        confirm={`„${e.name}“ endgültig löschen? Das lässt sich nicht rückgängig machen.`}
                        onClick={() => run(() => trashApi.purge(channelId, e.group), 'Endgültig gelöscht')}
                      >
                        <Icon name="trash" />
                        <span className="sr-only">{e.name} endgültig löschen</span>
                      </AsyncButton>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
        {d?.can_set_retention && (
          <div className="field">
            <label htmlFor={daysId}>Aufbewahrung in Tagen (gilt für die ganze Schule)</label>
            <div className="row">
              <input id={daysId} type="number" min={1} max={365} value={days} aria-invalid={!daysValid || undefined} onChange={(e) => setDays(e.target.value)} />
              <AsyncButton className="btn" disabled={!daysValid || dayValue === d.retention_days} onClick={() => run(() => trashApi.setRetention(dayValue), 'Frist gespeichert')}>
                Speichern
              </AsyncButton>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
