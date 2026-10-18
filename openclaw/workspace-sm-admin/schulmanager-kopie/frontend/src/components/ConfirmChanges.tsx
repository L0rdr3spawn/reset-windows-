/**
 * Bestätigung einer 409-Antwort mit Änderungsliste (R3, Entwurf §15.3 „409 für alle Bestätigungen“, §15.5 Texte):
 * `detail = {message, code: 'plan_change' | 'grid_change' | 'time_grid_change', changes[]}`; übernommen wird mit
 * `?force=1`. `useConfirmChanges().run(fn)` ruft `fn(false)`, zeigt bei einer solchen 409 die Liste und ruft nach
 * „Trotzdem übernehmen“ `fn(true)`.
 */
import { useRef, useState, type ReactNode } from 'react';
import { ApiError } from '../api/client';
import type { ChangeItem, ConfirmDetail } from '../api/types';
import { Modal } from './Modal';
import { AsyncButton } from './ui';
import './weeks.css';

const CODES = new Set(['plan_change', 'grid_change', 'time_grid_change']);

/** 409-Bestätigung aus einem Fehler lesen (sonst `null`). */
export function confirmDetailOf(e: unknown): ConfirmDetail | null {
  if (!(e instanceof ApiError) || e.status !== 409) return null;
  const d = e.detail as Partial<ConfirmDetail> | null;
  if (!d || typeof d !== 'object' || typeof d.code !== 'string' || !CODES.has(d.code)) return null;
  return { message: typeof d.message === 'string' ? d.message : '', code: d.code, changes: Array.isArray(d.changes) ? d.changes : [] };
}

export function confirmTitle(code: ConfirmDetail['code']): string {
  return code === 'plan_change' ? 'Änderungen durch die neuen Unterrichtstage' : 'Änderungen durch das Zeitraster';
}

/** „Kurs M 5a: Woche 2 → entfällt“ */
export function changeLine(c: ChangeItem): string {
  return `${c.label || c.id}: ${c.before} → ${c.after}`;
}

export function ConfirmChangesDialog({ detail, onConfirm, onCancel }: { detail: ConfirmDetail; onConfirm: () => Promise<void>; onCancel: () => void }) {
  return (
    <Modal
      title={confirmTitle(detail.code)}
      onClose={onCancel}
      footer={
        <>
          <button type="button" className="btn" onClick={onCancel}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={onConfirm}>
            Trotzdem übernehmen
          </AsyncButton>
        </>
      }
    >
      {detail.message && <p>{detail.message}</p>}
      {detail.changes.length > 0 && (
        <ul className="change-list small">
          {detail.changes.map((c, i) => (
            <li key={`${c.kind}-${c.id}-${i}`}>{changeLine(c)}</li>
          ))}
        </ul>
      )}
    </Modal>
  );
}

export function useConfirmChanges(): { dialog: ReactNode; run: <T>(fn: (force: boolean) => Promise<T>) => Promise<T | undefined> } {
  const [pending, setPending] = useState<{ detail: ConfirmDetail; confirm: () => Promise<void>; cancel: () => void } | null>(null);
  const busy = useRef(false);
  const run = async <T,>(fn: (force: boolean) => Promise<T>): Promise<T | undefined> => {
    try {
      return await fn(false);
    } catch (e) {
      const detail = confirmDetailOf(e);
      if (!detail || busy.current) throw e;
      return new Promise<T | undefined>((resolve, reject) => {
        busy.current = true;
        const done = () => {
          busy.current = false;
          setPending(null);
        };
        setPending({
          detail,
          confirm: async () => {
            try {
              const r = await fn(true);
              done();
              resolve(r);
            } catch (e2) {
              done();
              reject(e2);
            }
          },
          cancel: () => {
            done();
            resolve(undefined);
          },
        });
      });
    }
  };
  const dialog = pending ? <ConfirmChangesDialog detail={pending.detail} onConfirm={pending.confirm} onCancel={pending.cancel} /> : null;
  return { dialog, run };
}
