/**
 * Schnittstelle für andere Module (Kursräume, Aufgaben, Material): zeigt die Kompetenzen, die einem Element
 * zugeordnet sind, und lässt Lehrkräfte sie ändern. Einbindung::
 *
 *     <ItemCompetencies itemType="channel_item" itemId={String(item.id)} />
 *
 * `itemType` ist ein frei gewählter Elementtyp (Kleinbuchstaben und `_`), `itemId` die ID des Elements. Die Zuordnung
 * liegt in der Tabelle `comp_links` (Doku: docs/KOMPETENZEN.md, §6). Ohne Recht `competency.assess` bleibt es eine
 * reine Anzeige; ohne Zuordnung und ohne Recht wird nichts gezeigt.
 */
import './kompetenzen.css';
import { useState } from 'react';
import { Modal } from '../../components/Modal';
import { AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { can } from '../../lib/permissions';
import { compApi, type Framework } from './api';

export function ItemCompetencies({ itemType, itemId }: { itemType: string; itemId: string }) {
  const user = useUser();
  const canEdit = can(user, 'competency.assess');
  const q = useApi((signal) => compApi.links(itemType, itemId, signal), [itemType, itemId], { live: ['competency'] });
  const [open, setOpen] = useState(false);
  if (!q.data) return q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null;
  if (!q.data.length && !canEdit) return null;
  return (
    <div className="cp-item">
      <span className="xsmall muted">Kompetenzen:</span>
      <ul className="chips">
        {q.data.map((l) => (
          <li key={l.competency_id} className="chip" title={`${l.framework_name}: ${l.area_name}`}>
            {l.code ? `${l.code} ` : ''}
            {l.title}
          </li>
        ))}
      </ul>
      {canEdit && (
        <button type="button" className="btn btn-sm" onClick={() => setOpen(true)}>
          {q.data.length ? 'Ändern' : 'Kompetenz zuordnen'}
        </button>
      )}
      {open && <Picker itemType={itemType} itemId={itemId} selected={q.data.map((l) => l.competency_id)} onClose={() => setOpen(false)} onSaved={q.reload} />}
    </div>
  );
}

function Picker({ itemType, itemId, selected, onClose, onSaved }: { itemType: string; itemId: string; selected: number[]; onClose: () => void; onSaved: () => void }) {
  const [chosen, setChosen] = useState<number[]>(selected);
  const fws = useApi(async (signal) => {
    const list = await compApi.frameworks(false, signal);
    return Promise.all(list.map((f) => compApi.framework(f.id, signal)));
  }, []);
  const frameworks: Framework[] = fws.data ?? [];
  return (
    <Modal
      title="Kompetenzen zuordnen"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            onClick={async () => {
              await compApi.setLinks(itemType, itemId, chosen);
              onSaved();
              onClose();
            }}
          >
            Speichern
          </AsyncButton>
        </>
      }
    >
      {fws.error ? <ErrorBox error={fws.error} onRetry={fws.reload} /> : null}
      {!fws.data && !fws.error && <Loading />}
      {frameworks.map((f) => (
        <fieldset key={f.id} className="cp-comp-pick">
          <legend>{f.name}</legend>
          {f.areas.map((a) => (
            <div key={a.id}>
              <div className="small muted">{a.name}</div>
              {a.competencies.map((c) => (
                <label key={c.id} className="cp-check">
                  <input type="checkbox" checked={chosen.includes(c.id)} onChange={(e) => setChosen(e.target.checked ? [...chosen, c.id] : chosen.filter((x) => x !== c.id))} /> {c.title}
                </label>
              ))}
            </div>
          ))}
        </fieldset>
      ))}
    </Modal>
  );
}
