/** Katalog der Merkmale/Nachteilsausgleiche der Schule (Zeitzuschlag, Duden, ADHS …) – Stammdaten → Schüler/innen. */
import { useState } from 'react';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { supportApi, type CatalogBody, type CatalogItem, type SupportKind } from './supportApi';

const blank = (): CatalogBody => ({ label: '', kind: 'nachteilsausgleich', uses_minutes: false, default_minutes: null, teacher_visible: true, active: true });
const bodyOf = (c: CatalogItem): CatalogBody => ({
  label: c.label,
  kind: c.kind,
  uses_minutes: c.uses_minutes,
  default_minutes: c.default_minutes,
  teacher_visible: c.teacher_visible,
  active: c.active,
  sort: c.sort,
});

export function SupportCatalogDialog({ onClose }: { onClose: () => void }) {
  const toast = useToast();
  const q = useApi((signal) => supportApi.catalog(signal), [], { live: ['support_catalog'] });
  const [edit, setEdit] = useState<{ id: number | null; body: CatalogBody } | null>(null);
  const data = q.data;
  const set = <K extends keyof CatalogBody>(k: K, v: CatalogBody[K]) => setEdit((e) => (e ? { ...e, body: { ...e.body, [k]: v } } : e));
  const save = async () => {
    if (!edit) return;
    try {
      if (edit.id === null) await supportApi.createCatalog(edit.body);
      else await supportApi.updateCatalog(edit.id, edit.body);
      toast.success('Gespeichert');
      setEdit(null);
      q.reload();
    } catch (e) {
      toast.error(e);
    }
  };
  return (
    <Modal size="lg" title="Katalog der Merkmale" onClose={onClose}>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!data && !q.error && <Loading />}
      {data && (
        <div className="stack-sm">
          <p className="small" style={{ margin: 0 }}>
            Arten von Nachteilsausgleich und Förderung dieser Schule
            <HelpTip>
              „Für Lehrkräfte sichtbar“: Fachlehrkräfte sehen die Art (z. B. Zeitzuschlag, Duden) bei ihren Klausuren. Ausgeschaltet bleibt sie (z. B. Diagnose wie ADHS) nur für Klassenleitung, Verwaltung und Familie sichtbar.
            </HelpTip>
          </p>
          <ul className="st-list">
            {data.items.map((c) => (
              <li key={c.id} className="st-row">
                <div className="st-row-main">
                  <strong>
                    {c.label} {!c.active && <span className="badge">inaktiv</span>}
                  </strong>
                  <span className="xsmall muted">
                    {c.kind_label}
                    {c.uses_minutes ? ` · Zeitzuschlag${c.default_minutes ? ` (Standard ${c.default_minutes} Min.)` : ''}` : ''}
                    {c.teacher_visible ? ' · für Lehrkräfte sichtbar' : ' · nur Berechtigte'}
                  </span>
                </div>
                {data.can_manage && (
                  <div className="st-row-side">
                    <button type="button" className="btn btn-sm" onClick={() => setEdit({ id: c.id, body: bodyOf(c) })}>
                      <Icon name="edit" /> Bearbeiten
                    </button>
                    <AsyncButton
                      className="btn btn-sm btn-ghost"
                      confirm={`„${c.label}“ löschen?`}
                      onClick={async () => {
                        try {
                          await supportApi.removeCatalog(c.id);
                          q.reload();
                        } catch (err) {
                          toast.error(err);
                        }
                      }}
                    >
                      <Icon name="trash" />
                      <span className="sr-only">löschen</span>
                    </AsyncButton>
                  </div>
                )}
              </li>
            ))}
          </ul>
          {data.can_manage && !edit && (
            <button type="button" className="btn btn-primary" onClick={() => setEdit({ id: null, body: blank() })}>
              <Icon name="plus" /> Neue Art
            </button>
          )}
          {edit && (
            <div className="card stack-sm">
              <div className="form-grid">
                <Field label="Bezeichnung" htmlFor="sc-label">
                  <input id="sc-label" value={edit.body.label} maxLength={120} onChange={(e) => set('label', e.target.value)} />
                </Field>
                <Field label="Gruppe" htmlFor="sc-kind">
                  <select id="sc-kind" value={edit.body.kind} onChange={(e) => set('kind', e.target.value as SupportKind)}>
                    {(Object.keys(data.kinds) as SupportKind[]).map((k) => (
                      <option key={k} value={k}>
                        {data.kinds[k]}
                      </option>
                    ))}
                  </select>
                </Field>
                <label className="check">
                  <input type="checkbox" checked={edit.body.uses_minutes} onChange={(e) => set('uses_minutes', e.target.checked)} /> mit Zeitzuschlag (Minuten)
                </label>
                {edit.body.uses_minutes && (
                  <Field label="Standard-Minuten" htmlFor="sc-min">
                    <input id="sc-min" type="number" min={0} max={600} value={edit.body.default_minutes ?? ''} onChange={(e) => set('default_minutes', e.target.value ? Number(e.target.value) : null)} />
                  </Field>
                )}
                <label className="check">
                  <input type="checkbox" checked={edit.body.teacher_visible} onChange={(e) => set('teacher_visible', e.target.checked)} /> für Lehrkräfte sichtbar
                </label>
                <label className="check">
                  <input type="checkbox" checked={edit.body.active} onChange={(e) => set('active', e.target.checked)} /> aktiv (auswählbar)
                </label>
              </div>
              <div className="row">
                <AsyncButton className="btn btn-primary" disabled={!edit.body.label.trim()} onClick={save}>
                  Speichern
                </AsyncButton>
                <button type="button" className="btn" onClick={() => setEdit(null)}>
                  Abbrechen
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
