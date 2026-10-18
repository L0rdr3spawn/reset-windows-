/** Frist für eine Schülerin/einen Schüler oder eine Gruppe verlängern (mit Hinweis auf Nachteilsausgleich). */
import { useState } from 'react';
import { errorMessage } from '../../../api/client';
import { Modal } from '../../../components/Modal';
import { AsyncButton, Field } from '../../../components/ui';
import { useToast } from '../../../context/ToastContext';
import { formatWhen, fromLocalInput, toLocalInput } from '../logic';
import type { Item } from '../types';
import { assignApi } from './api';
import { extendedDue } from './logic';
import type { ExtensionInfo } from './types';
import './aufgaben.css';

export type ExtensionTarget = { kind: 'user'; userId: number; name: string } | { kind: 'group'; groupId: number; name: string };

export function ExtensionDialog({ channelId, item, target, existing, support, onClose, onDone }: { channelId: number; item: Item; target: ExtensionTarget; existing: ExtensionInfo | null; support: string[]; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const [due, setDue] = useState(existing?.due_at ? toLocalInput(existing.due_at) : extendedDue(item.due_at, 2));
  const [reason, setReason] = useState(existing?.reason ?? (support.length ? `Nachteilsausgleich: ${support.join(', ')}` : ''));
  const [error, setError] = useState<string | null>(null);
  const save = async () => {
    const iso = fromLocalInput(due);
    if (!iso) {
      setError('Bitte eine gültige Frist angeben.');
      return;
    }
    try {
      await assignApi.putExtension(channelId, item.id, { ...(target.kind === 'user' ? { user_id: target.userId } : { group_id: target.groupId }), due_at: iso, reason });
      toast.success(`Frist für ${target.name} verlängert`);
      onDone();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  const remove = async () => {
    if (!existing?.id) return;
    try {
      await assignApi.deleteExtension(channelId, item.id, existing.id);
      toast.success('Verlängerung entfernt');
      onDone();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title={`Frist verlängern – ${target.name}`}
      onClose={onClose}
      footer={
        <>
          {existing?.id && (
            <AsyncButton className="btn btn-ghost" onClick={remove}>
              Verlängerung entfernen
            </AsyncButton>
          )}
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        {error && (
          <p role="alert" className="kr-error">
            {error}
          </p>
        )}
        <p className="small">Allgemeine Frist: {item.due_at ? formatWhen(item.due_at) : 'keine'}</p>
        {support.length > 0 && (
          <p className="au-nta" role="note">
            <strong>Nachteilsausgleich:</strong> {support.join(', ')}
          </p>
        )}
        <Field label="Neue Frist" htmlFor="au-ext-due">
          <input id="au-ext-due" type="datetime-local" value={due} onChange={(e) => setDue(e.target.value)} />
        </Field>
        <div className="row">
          {[1, 3, 7].map((d) => (
            <button key={d} type="button" className="btn btn-sm" onClick={() => setDue(extendedDue(item.due_at, d))}>
              {d === 7 ? '+ 1 Woche' : `+ ${d} ${d === 1 ? 'Tag' : 'Tage'}`}
            </button>
          ))}
        </div>
        <Field label="Begründung (optional)" htmlFor="au-ext-reason">
          <input id="au-ext-reason" value={reason} maxLength={500} onChange={(e) => setReason(e.target.value)} />
        </Field>
      </div>
    </Modal>
  );
}
