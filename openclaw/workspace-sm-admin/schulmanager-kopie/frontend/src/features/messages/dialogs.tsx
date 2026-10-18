/** Dialoge des Postfachs: Nachricht melden. */
import { useId, useState } from 'react';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Modal } from '../../components/Modal';
import { AsyncButton } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { messagesApi } from './api';
import type { Message } from './types';

const FALLBACK_CATEGORIES = [
  { key: 'belaestigung', label: 'Belästigung' },
  { key: 'beleidigung', label: 'Beleidigung' },
  { key: 'bedrohung', label: 'Bedrohung' },
  { key: 'spam', label: 'Spam' },
  { key: 'unangemessen', label: 'Unangemessener Inhalt' },
  { key: 'sonstiges', label: 'Sonstiges' },
];

export function ReportDialog({
  conversationId,
  message,
  categories,
  onClose,
  onDone,
}: {
  conversationId: number;
  message: Message;
  categories?: { key: string; label: string }[];
  onClose: () => void;
  onDone: () => void;
}) {
  const cats = categories?.length ? categories : FALLBACK_CATEGORIES;
  const [category, setCategory] = useState(cats[0]?.key ?? 'sonstiges');
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const catId = useId();
  const reasonId = useId();
  const submit = async () => {
    setError(null);
    try {
      const res = await messagesApi.report(conversationId, message.id, { category, reason: reason.trim() });
      toast.success(res.duplicate ? 'Sie haben diese Nachricht bereits gemeldet.' : 'Danke – die Moderation prüft die Nachricht.');
      onDone();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title="Nachricht melden"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-danger" onClick={submit}>
            Melden
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        <p className="small" style={{ margin: 0 }}>
          Die Moderation der Schule sieht die gemeldete Nachricht von <strong>{message.sender.name}</strong>.
          <HelpTip>
            Die Moderation (Schulleitung) sieht außerdem Ihren Grund und, falls nötig, die Nachrichten direkt davor und danach. Jede Ansicht wird protokolliert. Die absendende Person erfährt nicht, wer gemeldet hat.
          </HelpTip>
        </p>
        <div className="field">
          <label htmlFor={catId}>Grund</label>
          <select id={catId} value={category} onChange={(e) => setCategory(e.target.value)}>
            {cats.map((c) => (
              <option key={c.key} value={c.key}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor={reasonId}>Beschreibung (optional)</label>
          <textarea id={reasonId} rows={4} maxLength={2000} value={reason} onChange={(e) => setReason(e.target.value)} />
          <span className="hint">Bei Gefahr bitte sofort eine Lehrkraft oder die Schulleitung ansprechen.</span>
        </div>
        {error && (
          <p className="pf-error-text" role="alert">
            {error}
          </p>
        )}
      </div>
    </Modal>
  );
}
