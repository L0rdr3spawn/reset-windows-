/** Editor für einen Kompetenzrahmen: Niveaustufen, Bereiche, Kompetenzen (mit optionalen Beschreibungen je Stufe). */
import { useState } from 'react';
import { ApiError } from '../../api/client';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, Field } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { compApi } from './api';
import { draftError, emptyDraft, MAX_LEVELS, MIN_LEVELS, setLevelCount, toInput, type Draft } from './logic';

export function FrameworkEditor({ frameworkId, initial, onClose, onSaved }: { frameworkId: number | null; initial: Draft | null; onClose: () => void; onSaved: () => void }) {
  const toast = useToast();
  const [d, setD] = useState<Draft>(() => initial ?? emptyDraft());
  const [confirm, setConfirm] = useState<string | null>(null);
  const err = draftError(d);

  const setArea = (i: number, patch: Partial<Draft['areas'][number]>) => setD((x) => ({ ...x, areas: x.areas.map((a, j) => (j === i ? { ...a, ...patch } : a)) }));
  const setComp = (i: number, k: number, patch: Partial<Draft['areas'][number]['competencies'][number]>) =>
    setD((x) => ({ ...x, areas: x.areas.map((a, j) => (j === i ? { ...a, competencies: a.competencies.map((c, m) => (m === k ? { ...c, ...patch } : c)) } : a)) }));

  const save = async (force: boolean) => {
    try {
      if (frameworkId === null) await compApi.createFramework(toInput(d));
      else await compApi.saveFramework(frameworkId, toInput(d), force);
      toast.success('Kompetenzrahmen gespeichert');
      onSaved();
      onClose();
    } catch (e) {
      if (e instanceof ApiError && e.status === 409 && frameworkId !== null && !force) {
        setConfirm(e.message);
        return;
      }
      throw e;
    }
  };

  return (
    <Modal
      size="lg"
      title={frameworkId === null ? 'Neuer Kompetenzrahmen' : 'Kompetenzrahmen bearbeiten'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" disabled={!!err} title={err ?? undefined} onClick={() => save(false)}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        {confirm && (
          <Alert kind="warning" action={<AsyncButton className="btn btn-danger" onClick={() => save(true)}>Trotzdem entfernen</AsyncButton>}>
            {confirm}
          </Alert>
        )}
        <div className="cp-filters">
          <Field label="Name" htmlFor="cp-fw-name">
            <input id="cp-fw-name" value={d.name} maxLength={200} onChange={(e) => setD({ ...d, name: e.target.value })} />
          </Field>
          <Field label="Fach" htmlFor="cp-fw-subject" help="Optional, z. B. Mathematik. Leer lassen für fächerübergreifende Rahmen.">
            <input id="cp-fw-subject" value={d.subject} maxLength={40} onChange={(e) => setD({ ...d, subject: e.target.value })} />
          </Field>
        </div>
        <Field label="Beschreibung" htmlFor="cp-fw-desc">
          <input id="cp-fw-desc" value={d.description} maxLength={500} onChange={(e) => setD({ ...d, description: e.target.value })} />
        </Field>
        <fieldset className="cp-levels-edit">
          <legend>Niveaustufen</legend>
          {d.levels.map((l, i) => (
            <div key={i} className="row">
              <span className="mono">{i + 1}</span>
              <input aria-label={`Beschriftung Stufe ${i + 1}`} value={l} maxLength={80} onChange={(e) => setD({ ...d, levels: d.levels.map((x, j) => (j === i ? e.target.value : x)) })} />
            </div>
          ))}
          <div className="row">
            <button type="button" className="btn btn-sm" disabled={d.levels.length >= MAX_LEVELS} onClick={() => setD(setLevelCount(d, d.levels.length + 1))}>
              Stufe hinzufügen
            </button>
            <button type="button" className="btn btn-sm" disabled={d.levels.length <= MIN_LEVELS} onClick={() => setD(setLevelCount(d, d.levels.length - 1))}>
              Letzte Stufe entfernen
            </button>
          </div>
          <Field label="Unterstützung bis Stufe" htmlFor="cp-fw-support" help="Bis zu dieser Stufe zählt eine Kompetenz als „braucht Unterstützung“. 0 schaltet die Markierung aus.">
            <select id="cp-fw-support" value={d.support_level} onChange={(e) => setD({ ...d, support_level: Number(e.target.value) })}>
              {d.levels.map((_, i) => (
                <option key={i} value={i}>
                  {i === 0 ? 'Keine Markierung' : `Stufe ${i}`}
                </option>
              ))}
            </select>
          </Field>
        </fieldset>
        {d.areas.map((a, i) => (
          <section key={a.id ?? `n${i}`} className="card cp-edit-area">
            <div className="row">
              <input aria-label={`Name des Bereichs ${i + 1}`} placeholder="Bereich" value={a.name} maxLength={200} onChange={(e) => setArea(i, { name: e.target.value })} />
              <button type="button" className="btn btn-sm" onClick={() => setD((x) => ({ ...x, areas: x.areas.filter((_, j) => j !== i) }))}>
                Bereich entfernen
              </button>
            </div>
            <ul className="cp-edit-comps">
              {a.competencies.map((c, k) => (
                <li key={c.id ?? `n${k}`}>
                  <div className="row">
                    <input className="cp-code-in" aria-label="Kürzel" placeholder="Kürzel" value={c.code} maxLength={20} onChange={(e) => setComp(i, k, { code: e.target.value })} />
                    <input className="cp-title-in" aria-label={`Kompetenz ${k + 1} in ${a.name || 'Bereich'}`} placeholder="Ich kann …" value={c.title} maxLength={300} onChange={(e) => setComp(i, k, { title: e.target.value })} />
                    <button type="button" className="btn btn-sm" aria-label="Kompetenz entfernen" onClick={() => setArea(i, { competencies: a.competencies.filter((_, m) => m !== k) })}>
                      Entfernen
                    </button>
                  </div>
                  <details>
                    <summary className="small">Beschreibung je Stufe</summary>
                    {d.levels.map((l, s) => (
                      <div key={s} className="row">
                        <span className="small cp-desc-label">{s + 1}</span>
                        <input
                          aria-label={`${l}: Beschreibung`}
                          value={c.descriptors[s] ?? ''}
                          maxLength={300}
                          onChange={(e) => {
                            const next = d.levels.map((_, t) => (t === s ? e.target.value : (c.descriptors[t] ?? '')));
                            setComp(i, k, { descriptors: next });
                          }}
                        />
                      </div>
                    ))}
                  </details>
                </li>
              ))}
            </ul>
            <button type="button" className="btn btn-sm" onClick={() => setArea(i, { competencies: [...a.competencies, { code: '', title: '', descriptors: [] }] })}>
              Kompetenz hinzufügen
            </button>
          </section>
        ))}
        <div>
          <button type="button" className="btn" onClick={() => setD((x) => ({ ...x, areas: [...x.areas, { name: '', competencies: [{ code: '', title: '', descriptors: [] }] }] }))}>
            Bereich hinzufügen
          </button>
        </div>
        {err && <p className="small muted">{err}</p>}
      </div>
    </Modal>
  );
}
