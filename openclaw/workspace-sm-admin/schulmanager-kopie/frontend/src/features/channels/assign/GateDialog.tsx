/** Material, Aufgabe oder Ordner nur für bestimmte Gruppen sichtbar machen (nichts angekreuzt = für alle). */
import { useState } from 'react';
import { errorMessage } from '../../../api/client';
import { Modal } from '../../../components/Modal';
import { AsyncButton, ErrorBox, Loading } from '../../../components/ui';
import { useToast } from '../../../context/ToastContext';
import { useApi } from '../../../hooks/useApi';
import { assignApi } from './api';
import type { GroupsResponse } from './types';
import './aufgaben.css';

export type GateTarget = { kind: 'item' | 'folder'; id: number; title: string };

export function currentGate(data: GroupsResponse | undefined, target: GateTarget): number[] {
  const map = target.kind === 'item' ? data?.gates?.items : data?.gates?.folders;
  return map?.[String(target.id)] ?? [];
}

export function GateDialog({ channelId, target, onClose, onDone }: { channelId: number; target: GateTarget; onClose: () => void; onDone?: () => void }) {
  const toast = useToast();
  const q = useApi((signal) => assignApi.groups(channelId, signal), [channelId]);
  const [picked, setPicked] = useState<number[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const selected = picked ?? currentGate(q.data, target);
  const toggle = (id: number) => setPicked(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  const save = async () => {
    try {
      if (target.kind === 'item') await assignApi.itemGate(channelId, target.id, selected);
      else await assignApi.folderGate(channelId, target.id, selected);
      toast.success(selected.length ? 'Nur für die gewählten Gruppen sichtbar' : 'Für alle sichtbar');
      onDone?.();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  const sets = q.data?.sets ?? [];
  return (
    <Modal
      title={`Sichtbar für Gruppen – ${target.title}`}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save} disabled={!q.data}>
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
        {q.initialLoading && <Loading />}
        {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
        {q.data && !sets.length && <p className="small muted">Noch keine Gruppen im Kursraum.</p>}
        {sets.map((s) => (
          <fieldset key={s.id} className="au-scope">
            <legend className="small">{s.name}</legend>
            {s.groups.map((g) => (
              <label key={g.id} className="check">
                <input type="checkbox" checked={selected.includes(g.id)} onChange={() => toggle(g.id)} /> {g.name} <span className="xsmall muted">({g.members.length})</span>
              </label>
            ))}
          </fieldset>
        ))}
        {sets.length > 0 && <p className="xsmall muted">Nichts angekreuzt: für alle Teilnehmenden sichtbar. Lehrende sehen immer alles.</p>}
      </div>
    </Modal>
  );
}
