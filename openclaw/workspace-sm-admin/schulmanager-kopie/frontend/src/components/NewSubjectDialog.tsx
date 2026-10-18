import { useMemo, useState } from 'react';
import { data as dataApi } from '../api/endpoints';
import type { Subject } from '../api/types';
import { useToast } from '../context/ToastContext';
import { invalidate, useCollection } from '../hooks/useCollection';
import { suggestSubjectCode } from '../lib/subjectCode';
import { Modal } from './Modal';
import { AsyncButton, Field } from './ui';

const ID_BAD = /[/#?\\,;|]/;

/**
 * Neues Fach direkt anlegen (Name, Fachraum-Typ; das Kürzel wird vorgeschlagen) – ohne die Seite zu wechseln.
 * Hauptfach, Farbe und Blöcke pro Tag stehen unter „Mehr Optionen“.
 */
export function NewSubjectDialog({ onClose, onCreated, initialName = '' }: { onClose: () => void; onCreated: (s: Subject) => void; initialName?: string }) {
  const toast = useToast();
  const subjects = useCollection('subjects');
  const rooms = useCollection('rooms');
  const [name, setName] = useState(initialName);
  const [idEdited, setIdEdited] = useState<string | null>(null);
  const takenIds = useMemo(() => (subjects.data ?? []).map((x) => x.id), [subjects.data]);
  const id = idEdited ?? suggestSubjectCode(name, takenIds);
  const [roomType, setRoomType] = useState('');
  const [core, setCore] = useState(false);
  const [maxPerDay, setMaxPerDay] = useState(1);
  const [color, setColor] = useState('');
  const roomTypes = useMemo(
    () => [...new Set([...(rooms.data ?? []).map((r) => r.type), ...(subjects.data ?? []).map((s) => s.room_type ?? '')].filter((t) => t && t !== 'Klassenraum'))].sort(),
    [rooms.data, subjects.data],
  );
  const code = id.trim();
  const idError = !code
    ? null
    : ID_BAD.test(code)
      ? 'Keine Zeichen / # ? \\ , ; |'
      : (subjects.data ?? []).some((s) => s.id.toLowerCase() === code.toLowerCase())
        ? 'Dieses Kürzel gibt es schon'
        : null;
  const ok = !!code && !!name.trim() && !idError;

  const save = async () => {
    if (!ok) return;
    try {
      const created = await dataApi.create('subjects', { id: code, name: name.trim(), room_type: roomType.trim() || null, core, max_per_day: maxPerDay, color });
      invalidate('subjects');
      toast.success(`Fach ${created.id} angelegt`);
      onCreated(created);
      onClose();
    } catch (e) {
      toast.error(e, 'Fach anlegen');
    }
  };

  return (
    <Modal
      title="Neues Fach anlegen"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save} disabled={!ok}>
            Anlegen
          </AsyncButton>
        </>
      }
    >
      <form
        className="form-grid"
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <Field label="Name" htmlFor="ns-name">
          <input id="ns-name" type="text" maxLength={80} value={name} onChange={(e) => setName(e.target.value)} autoFocus required />
        </Field>
        <Field label="Kürzel" htmlFor="ns-id" error={idError} hint="Wird aus dem Namen vorgeschlagen; kurz und eindeutig, z. B. „INF“ oder „LF3“; nicht mehr änderbar">
          <input id="ns-id" type="text" maxLength={20} value={id} onChange={(e) => setIdEdited(e.target.value)} required />
        </Field>
        <Field label="Fachraum-Typ" htmlFor="ns-room" hint="Leer = Unterricht im Klassenraum; sonst ein Raumtyp, z. B. „Sporthalle“ oder „Informatik“">
          <input id="ns-room" type="text" list="ns-room-types" maxLength={40} value={roomType} onChange={(e) => setRoomType(e.target.value)} placeholder="Klassenraum" />
          <datalist id="ns-room-types">
            {roomTypes.map((t) => (
              <option key={t} value={t} />
            ))}
          </datalist>
        </Field>
        <details className="disclosure span-all">
          <summary>Mehr Optionen</summary>
          <div className="form-grid" style={{ marginTop: 8 }}>
            <div className="field span-all">
              <label className="check">
                <input type="checkbox" checked={core} onChange={(e) => setCore(e.target.checked)} /> Hauptfach (möglichst früh am Tag)
              </label>
            </div>
            <Field label="max. Blöcke pro Tag" htmlFor="ns-mpd">
              <input id="ns-mpd" type="number" min={1} max={4} value={maxPerDay} onChange={(e) => setMaxPerDay(Math.max(1, Math.min(4, Number(e.target.value) || 1)))} />
            </Field>
            <Field label="Farbe im Stundenplan" htmlFor="ns-color">
              <div className="row">
                <input id="ns-color" type="color" value={color || '#4f7cac'} onChange={(e) => setColor(e.target.value)} />
                <button type="button" className="btn btn-sm btn-ghost" onClick={() => setColor('')}>
                  automatisch
                </button>
              </div>
            </Field>
          </div>
        </details>
      </form>
    </Modal>
  );
}
