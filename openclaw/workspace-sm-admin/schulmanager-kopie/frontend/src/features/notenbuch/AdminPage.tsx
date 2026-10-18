/**
 * `/notenbuch/verwaltung` – Schuleinstellungen des Notenbuchs (Schulleitung): Einsicht für Schüler/innen und Eltern,
 * Notenskalen je Klassenstufe, Notenschlüssel, Versetzungswarnung, Vorlage der Leistungsarten; Export der Halbjahresnoten
 * für SchILD/ASV/LUSD (Schulleitung, Sekretariat).
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { HelpTip } from '../../components/HelpTip';
import { AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useTitle } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { gbApi } from './api';
import { fmtWeight, parseDecimal } from './logic';
import type { GradebookSettings, Meta, RiskSettings, TemplateNode, Visibility } from './types';
import './notenbuch.css';

type CustomScale = NonNullable<GradebookSettings['custom_scales']>[number];
type CustomKey = NonNullable<GradebookSettings['custom_keys']>[number];

export default function AdminPage() {
  useTitle('Notenbuch verwalten');
  const meta = useApi((signal) => gbApi.meta(signal), []);
  if (meta.error) return <div className="page"><ErrorBox error={meta.error} onRetry={meta.reload} /></div>;
  if (!meta.data) return <div className="page"><Loading /></div>;
  const m = meta.data;
  return (
    <div className="page stack">
      <div className="page-head">
        <div>
          <p className="small muted">
            <Link to="/notenbuch">Notenbuch</Link>
          </p>
          <h1>Notenbuch verwalten</h1>
        </div>
      </div>
      {m.can.manage && <SettingsForm meta={m} onSaved={meta.reload} />}
      {m.can.export && <ExportCard meta={m} />}
    </div>
  );
}

function SettingsForm({ meta, onSaved }: { meta: Meta; onSaved: () => void }) {
  const toast = useToast();
  const s = meta.settings;
  const [visibility, setVisibility] = useState<Visibility>(s.visibility);
  const [showAvg, setShowAvg] = useState(s.show_averages);
  const [defaultScale, setDefaultScale] = useState(s.default_scale ?? 'note6');
  const [byGrade, setByGrade] = useState<Record<string, string>>(s.scale_by_grade ?? {});
  const [keysDefault, setKeysDefault] = useState<Record<string, string>>(s.keys_default ?? {});
  const [rounding, setRounding] = useState<string>(s.rounding);
  const [decimals, setDecimals] = useState(String(s.decimals));
  const [scales, setScales] = useState<CustomScale[]>(s.custom_scales ?? []);
  const [keys, setKeys] = useState<CustomKey[]>(s.custom_keys ?? []);
  const [risk, setRisk] = useState<RiskSettings>(s.risk);
  const [split, setSplit] = useState(s.halfyear_split ?? '02-01');
  const [template, setTemplate] = useState<TemplateNode[]>((s.templates ?? {})['*'] ?? meta.default_template);
  const allScales = [...meta.scales.filter((x) => x.builtin), ...scales.filter((x) => x.id.length >= 2).map((x) => ({ id: x.id, name: x.name, builtin: false }))];
  const keyChoices = (scaleId: string) => [...meta.keys.filter((k) => k.builtin && k.scale_id === scaleId), ...keys.filter((k) => k.scale_id === scaleId)];

  const save = async () => {
    const templates = { ...(s.templates ?? {}), '*': template };
    const body: Partial<GradebookSettings> = {
      visibility,
      show_averages: showAvg,
      default_scale: defaultScale,
      scale_by_grade: Object.fromEntries(Object.entries(byGrade).filter(([, v]) => v)),
      keys_default: Object.fromEntries(Object.entries(keysDefault).filter(([, v]) => v)),
      rounding: rounding as GradebookSettings['rounding'],
      decimals: Number(decimals),
      custom_scales: scales,
      custom_keys: keys,
      risk,
      halfyear_split: split,
      templates,
    };
    try {
      await gbApi.saveSettings(body);
      toast.success('Einstellungen gespeichert');
      onSaved();
    } catch (e) {
      toast.error(e);
    }
  };

  return (
    <>
      <section className="card stack" aria-labelledby="gbk-a-vis">
        <h2 id="gbk-a-vis">Einsicht für Schüler/innen und Eltern</h2>
        <Field label="Wann sehen sie Noten?" htmlFor="gbk-vis" help="Eltern volljähriger Schüler/innen sehen Noten nur mit deren Freigabe im Profil, unabhängig von dieser Einstellung.">
          <select id="gbk-vis" value={visibility} onChange={(e) => setVisibility(e.target.value as Visibility)}>
            {meta.visibility_options.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
        </Field>
        <label className="check">
          <input type="checkbox" checked={showAvg} onChange={(e) => setShowAvg(e.target.checked)} /> Schnitte mit anzeigen
        </label>
      </section>

      <section className="card stack" aria-labelledby="gbk-a-scales">
        <h2 id="gbk-a-scales">Notenskalen</h2>
        <div className="grid grid-2">
          <Field label="Standardskala" htmlFor="gbk-def-scale">
            <select id="gbk-def-scale" value={defaultScale} onChange={(e) => setDefaultScale(e.target.value)}>
              {allScales.map((x) => (
                <option key={x.id} value={x.id}>
                  {x.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Vorschlagsnote runden" htmlFor="gbk-def-round" help="Gilt für neue Notenbücher; je Notenbuch änderbar.">
            <select id="gbk-def-round" value={rounding} onChange={(e) => setRounding(e.target.value)}>
              <option value="ganz">Ganze Note</option>
              <option value="tendenz">Mit Tendenz</option>
            </select>
          </Field>
          <Field label="Nachkommastellen im Schnitt" htmlFor="gbk-def-dec">
            <select id="gbk-def-dec" value={decimals} onChange={(e) => setDecimals(e.target.value)}>
              {[0, 1, 2, 3].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <h3>
          Skala je Klassenstufe <HelpTip>Neue Notenbücher einer Klassenstufe starten mit dieser Skala. Leer = Standardskala. Einzelne Kurse lassen sich im Notenbuch umstellen, solange noch keine Noten eingetragen sind.</HelpTip>
        </h3>
        <div className="chips">
          {meta.grades.map((g) => (
            <label key={g} className="field">
              <span>Stufe {g}</span>
              <select aria-label={`Skala Stufe ${g}`} value={byGrade[String(g)] ?? ''} onChange={(e) => setByGrade({ ...byGrade, [String(g)]: e.target.value })}>
                <option value="">Standard</option>
                {allScales.map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.name}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
        <ScaleEditor scales={scales} onChange={setScales} />
      </section>

      <section className="card stack" aria-labelledby="gbk-a-keys">
        <h2 id="gbk-a-keys">Notenschlüssel</h2>
        <div className="chips">
          {allScales
            .filter((x) => keyChoices(x.id).length > 0)
            .map((x) => (
              <label key={x.id} className="field">
                <span>Standard für {x.name}</span>
                <select aria-label={`Schlüssel ${x.name}`} value={keysDefault[x.id] ?? ''} onChange={(e) => setKeysDefault({ ...keysDefault, [x.id]: e.target.value })}>
                  <option value="">Eingebaut</option>
                  {keyChoices(x.id).map((k) => (
                    <option key={k.id} value={k.id}>
                      {k.name}
                    </option>
                  ))}
                </select>
              </label>
            ))}
        </div>
        <details>
          <summary>Eingebaute Schlüssel ansehen</summary>
          <ul className="gbk-list">
            {meta.keys
              .filter((k) => k.builtin)
              .map((k) => (
                <li key={k.id}>
                  <strong>{k.name}</strong>
                  <span className="small muted">{k.steps.map((st) => `${st.label} ab ${fmtWeight(st.min_percent)} %`).join(' · ')}</span>
                </li>
              ))}
          </ul>
        </details>
        <KeyEditor keys={keys} scales={allScales} onChange={setKeys} />
      </section>

      <section className="card stack" aria-labelledby="gbk-a-risk">
        <h2 id="gbk-a-risk">Versetzungswarnung</h2>
        <label className="check">
          <input type="checkbox" checked={risk.enabled} onChange={(e) => setRisk({ ...risk, enabled: e.target.checked })} /> Warnung in der Klassenübersicht anzeigen
        </label>
        <div className="grid grid-2">
          <Field label="Defizit ab Note" htmlFor="gbk-r-grade" help="Bei Noten 1–6: ab dieser Note zählt ein Fach als Defizit (5 = mangelhaft).">
            <select id="gbk-r-grade" value={risk.min_grade} disabled={!risk.enabled} onChange={(e) => setRisk({ ...risk, min_grade: Number(e.target.value) })}>
              {[3, 4, 5, 6].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Defizit bis Punkte" htmlFor="gbk-r-points" help="Bei Punkten 15–0: bis zu dieser Punktzahl zählt ein Fach als Defizit.">
            <input id="gbk-r-points" type="number" min={0} max={14} value={risk.max_points} disabled={!risk.enabled} onChange={(e) => setRisk({ ...risk, max_points: Number(e.target.value) })} />
          </Field>
          <Field label="Warnen bei Defiziten in Hauptfächern" htmlFor="gbk-r-core" help="Anzahl der Hauptfächer mit Defizit, ab der gewarnt wird. 0 = nie.">
            <input id="gbk-r-core" type="number" min={0} max={10} value={risk.core_count} disabled={!risk.enabled} onChange={(e) => setRisk({ ...risk, core_count: Number(e.target.value) })} />
          </Field>
          <Field label="Warnen bei Defiziten in allen Fächern" htmlFor="gbk-r-any" help="Anzahl der Fächer mit Defizit insgesamt, ab der gewarnt wird. 0 = nie.">
            <input id="gbk-r-any" type="number" min={0} max={20} value={risk.any_count} disabled={!risk.enabled} onChange={(e) => setRisk({ ...risk, any_count: Number(e.target.value) })} />
          </Field>
        </div>
      </section>

      <section className="card stack" aria-labelledby="gbk-a-tpl">
        <h2 id="gbk-a-tpl">
          Vorlage der Leistungsarten <HelpTip>Neue Notenbücher beginnen mit diesen Leistungsarten und Gewichten. Jedes Notenbuch lässt sich danach ändern.</HelpTip>
        </h2>
        <TemplateEditor nodes={template} onChange={setTemplate} />
        <Field label="Wechsel zum 2. Halbjahr" htmlFor="gbk-split" help="Ab diesem Tag (Monat-Tag) gilt das 2. Halbjahr, Standard 01.02.">
          <input id="gbk-split" value={split} pattern="\d\d-\d\d" placeholder="02-01" onChange={(e) => setSplit(e.target.value)} />
        </Field>
      </section>

      <div className="gbk-bar">
        <AsyncButton className="btn btn-primary" onClick={save}>
          Einstellungen speichern
        </AsyncButton>
      </div>
    </>
  );
}

function ScaleEditor({ scales, onChange }: { scales: CustomScale[]; onChange: (s: CustomScale[]) => void }) {
  const set = (i: number, patch: Partial<CustomScale>) => onChange(scales.map((x, j) => (j === i ? { ...x, ...patch } : x)));
  return (
    <div className="stack-sm">
      <h3>
        Eigene Skalen <HelpTip>Eigene Stufen mit Zahlenwert, z. B. „sicher / teilweise / noch nicht“. Der Zahlenwert bestimmt den Schnitt; „höher ist besser“ legt fest, welche Richtung gut ist.</HelpTip>
      </h3>
      {scales.map((sc, i) => (
        <div key={i} className="card stack-sm">
          <div className="gbk-bar">
            <input aria-label="Kennung" placeholder="kennung" pattern="[a-z0-9_-]+" value={sc.id} onChange={(e) => set(i, { id: e.target.value.toLowerCase() })} />
            <input aria-label="Name" placeholder="Name" value={sc.name} onChange={(e) => set(i, { name: e.target.value })} />
            <label className="check">
              <input type="checkbox" checked={sc.higher_better} onChange={(e) => set(i, { higher_better: e.target.checked })} /> höher ist besser
            </label>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange(scales.filter((_, j) => j !== i))}>
              Skala entfernen
            </button>
          </div>
          {sc.labels.map((l, k) => (
            <div key={k} className="gbk-bar">
              <input aria-label="Stufe" placeholder="Stufe" value={l.label} onChange={(e) => set(i, { labels: sc.labels.map((x, j) => (j === k ? { ...x, label: e.target.value } : x)) })} />
              <input aria-label="Zahlenwert" inputMode="decimal" value={String(l.value)} onChange={(e) => set(i, { labels: sc.labels.map((x, j) => (j === k ? { ...x, value: parseDecimal(e.target.value) ?? 0 } : x)) })} />
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => set(i, { labels: sc.labels.filter((_, j) => j !== k) })}>
                −
              </button>
            </div>
          ))}
          <button type="button" className="btn btn-sm" onClick={() => set(i, { labels: [...sc.labels, { label: '', value: sc.labels.length + 1 }] })}>
            Stufe hinzufügen
          </button>
        </div>
      ))}
      <button
        type="button"
        className="btn btn-sm"
        onClick={() => onChange([...scales, { id: `skala-${scales.length + 1}`, name: 'Neue Skala', higher_better: true, labels: [{ label: 'A', value: 3 }, { label: 'B', value: 2 }, { label: 'C', value: 1 }] }])}
      >
        Eigene Skala hinzufügen
      </button>
    </div>
  );
}

function KeyEditor({ keys, scales, onChange }: { keys: CustomKey[]; scales: { id: string; name: string }[]; onChange: (k: CustomKey[]) => void }) {
  const set = (i: number, patch: Partial<CustomKey>) => onChange(keys.map((x, j) => (j === i ? { ...x, ...patch } : x)));
  return (
    <div className="stack-sm">
      <h3>
        Eigene Notenschlüssel <HelpTip>Je Stufe die Mindestprozent der Höchstpunktzahl. Die unterste Stufe beginnt bei 0 %. Grenzen gelten „ab“: genau auf der Grenze zählt schon die bessere Note.</HelpTip>
      </h3>
      {keys.map((k, i) => (
        <div key={i} className="card stack-sm">
          <div className="gbk-bar">
            <input aria-label="Kennung" placeholder="kennung" pattern="[a-z0-9_-]+" value={k.id} onChange={(e) => set(i, { id: e.target.value.toLowerCase() })} />
            <input aria-label="Name" placeholder="Name" value={k.name} onChange={(e) => set(i, { name: e.target.value })} />
            <select aria-label="Skala" value={k.scale_id} onChange={(e) => set(i, { scale_id: e.target.value })}>
              {scales.map((x) => (
                <option key={x.id} value={x.id}>
                  {x.name}
                </option>
              ))}
            </select>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange(keys.filter((_, j) => j !== i))}>
              Schlüssel entfernen
            </button>
          </div>
          {k.steps.map((st, n) => (
            <div key={n} className="gbk-steps">
              <input aria-label="Ab Prozent" inputMode="decimal" value={String(st.min_percent)} onChange={(e) => set(i, { steps: k.steps.map((x, j) => (j === n ? { ...x, min_percent: parseDecimal(e.target.value) ?? 0 } : x)) })} />
              <input aria-label="Note" value={st.label} onChange={(e) => set(i, { steps: k.steps.map((x, j) => (j === n ? { ...x, label: e.target.value } : x)) })} />
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => set(i, { steps: k.steps.filter((_, j) => j !== n) })}>
                −
              </button>
            </div>
          ))}
          <button type="button" className="btn btn-sm" onClick={() => set(i, { steps: [...k.steps, { min_percent: 0, label: '' }] })}>
            Stufe hinzufügen
          </button>
        </div>
      ))}
      <button
        type="button"
        className="btn btn-sm"
        onClick={() => onChange([...keys, { id: `schluessel-${keys.length + 1}`, name: 'Neuer Schlüssel', scale_id: 'note6', steps: [{ min_percent: 50, label: '4' }, { min_percent: 0, label: '6' }] }])}
      >
        Eigenen Schlüssel hinzufügen
      </button>
    </div>
  );
}

function TemplateEditor({ nodes, onChange, depth = 0 }: { nodes: TemplateNode[]; onChange: (n: TemplateNode[]) => void; depth?: number }) {
  const set = (i: number, patch: Partial<TemplateNode>) => onChange(nodes.map((x, j) => (j === i ? { ...x, ...patch } : x)));
  return (
    <div className="stack-sm">
      {nodes.map((n, i) => (
        <div key={i}>
          <div className="gbk-cat-row">
            <div className={`gbk-ind-${Math.min(depth, 3)}`}>
              <input aria-label="Name der Leistungsart" value={n.name} maxLength={120} onChange={(e) => set(i, { name: e.target.value })} />
            </div>
            <input aria-label="Gewicht" inputMode="decimal" value={fmtWeight(n.weight)} onChange={(e) => set(i, { weight: parseDecimal(e.target.value) ?? 0 })} />
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange(nodes.filter((_, j) => j !== i))}>
              Entfernen
            </button>
          </div>
          {depth < 2 && (
            <>
              <TemplateEditor nodes={n.children ?? []} depth={depth + 1} onChange={(c) => set(i, { children: c })} />
              <div>
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => set(i, { children: [...(n.children ?? []), { name: 'Unterart', weight: 1 }] })}>
                  Unterart zu „{n.name || 'Leistungsart'}“
                </button>
              </div>
            </>
          )}
        </div>
      ))}
      {depth === 0 && (
        <button type="button" className="btn btn-sm" onClick={() => onChange([...nodes, { name: 'Neue Leistungsart', weight: 1 }])}>
          Leistungsart hinzufügen
        </button>
      )}
    </div>
  );
}

function ExportCard({ meta }: { meta: Meta }) {
  const [term, setTerm] = useState(meta.term);
  const [format, setFormat] = useState(meta.export_formats[0]?.id ?? 'schild');
  const [cls, setCls] = useState('');
  const [open, setOpen] = useState(false);
  return (
    <section className="card stack" aria-labelledby="gbk-a-exp">
      <h2 id="gbk-a-exp">
        Export der Halbjahresnoten <HelpTip>CSV für den Import in SchILD-NRW/SVWS, ASV oder LUSD. Enthalten sind die festgelegten Noten gesperrter Notenbücher. Zeugnisse druckt weiterhin die Verwaltungssoftware.</HelpTip>
      </h2>
      <div className="grid grid-2">
        <Field label="Halbjahr" htmlFor="gbk-x-term">
          <select id="gbk-x-term" value={term} onChange={(e) => setTerm(e.target.value)}>
            {meta.terms.map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Format" htmlFor="gbk-x-format">
          <select id="gbk-x-format" value={format} onChange={(e) => setFormat(e.target.value)}>
            {meta.export_formats.map((f) => (
              <option key={f.id} value={f.id}>
                {f.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Klasse" htmlFor="gbk-x-class">
          <select id="gbk-x-class" value={cls} onChange={(e) => setCls(e.target.value)}>
            <option value="">Alle Klassen</option>
            {(meta.classes.length ? meta.classes : []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
      </div>
      {meta.can.manage && (
        <label className="check">
          <input type="checkbox" checked={open} onChange={(e) => setOpen(e.target.checked)} /> Auch noch nicht gesperrte Notenbücher einschließen
        </label>
      )}
      <div>
        <a className="btn btn-primary" href={gbApi.exportUrl(term, format, cls || undefined, open)} download>
          CSV herunterladen
        </a>
      </div>
    </section>
  );
}
