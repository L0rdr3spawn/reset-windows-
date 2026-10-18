/**
 * Planung → Regeln: Prioritäten und Regeln der Stundenplan-Optimierung als Bausteine.
 *
 * Ablauf: (1) Schulart/Vorlage wählen → passende Wichtigkeiten und nur die Bausteine, die diese Schule braucht;
 * (2) Bausteine je Gruppe mit Wichtigkeit Aus · Nett · Wichtig · Sehr wichtig · Muss, Wirkung und Ausnahmen
 * (Jahrgänge, Klassen, Fächer, Lehrkräfte, Wochen); „Erweitert“ zeigt alles – auch Bausteine ohne Datenbezug und
 * die Feinsteuerung mit Zahlen; (3) Wirkung vorab prüfen (Probelauf) und speichern. Vorlagen sind Daten:
 * exportieren, importieren, eigene Vorlage sichern. Konzept: docs/REGELN-UND-PRIORITAETEN.md.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage } from '../../../api/client';
import { HelpTip } from '../../../components/HelpTip';
import { Icon } from '../../../components/Icon';
import { Modal } from '../../../components/Modal';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../../../components/ui';
import { useToast } from '../../../context/ToastContext';
import { useApi } from '../../../hooks/useApi';
import { invalidate, useSettings } from '../../../hooks/useCollection';
import { rulesApi } from './api';
import { applyTemplate, exportPayload, parseImport, sameDraft, visibleRuleIds, type RuleItem, type RulesDraft, type RulesState, type RuleTemplate } from './model';
import { ProfilePicker } from './ProfilePicker';
import { RuleCard } from './RuleCard';
import { Simulation } from './Simulation';
import './rules.css';

function draftOf(s: RulesState): RulesDraft {
  return { profile: s.profile, advanced: s.advanced, items: structuredClone(s.items) };
}

export function RulesPanel({ canEdit, canGenerate }: { canEdit: boolean; canGenerate: boolean }) {
  const toast = useToast();
  const { data: settings } = useSettings();
  const q = useApi((signal) => rulesApi.get(signal), [], { live: ['settings', 'classes', 'teachers', 'subjects', 'courses', 'timetable', 'sites'] });
  const [draft, setDraft] = useState<RulesDraft | null>(null);
  const [saved, setSaved] = useState<RulesDraft | null>(null);
  const [chooseProfile, setChooseProfile] = useState(false);
  const [saveTemplate, setSaveTemplate] = useState<{ name: string; description: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Server-Stand übernehmen, solange nichts geändert wurde
  useEffect(() => {
    if (!q.data) return;
    const d = draftOf(q.data);
    setSaved(d);
    setDraft((cur) => (cur && saved && !sameDraft(cur, saved) ? cur : structuredClone(d)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q.data]);

  const state = q.data;
  const dirty = !!draft && !!saved && !sameDraft(draft, saved);
  const visible = useMemo(() => (state && draft ? visibleRuleIds({ ...state, items: draft.items, profile: draft.profile }, draft.advanced) : new Set<string>()), [state, draft]);

  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!state || !draft) return <Loading label="Regeln werden geladen …" />;

  const template = state.templates.find((t) => t.id === draft.profile);
  const firstTime = !state.profile && !chooseProfile;
  const update = (fn: (d: RulesDraft) => RulesDraft) => setDraft((d) => (d ? fn(d) : d));
  const setItem = (id: string, item: RuleItem) => update((d) => ({ ...d, items: { ...d.items, [id]: item } }));

  const pick = (t: RuleTemplate) => {
    update((d) => ({ ...d, profile: t.id, items: applyTemplate(d.items, t) }));
    setChooseProfile(false);
    toast.info(`Vorlage „${t.name}“ übernommen – noch nicht gespeichert`);
  };

  const save = async () => {
    try {
      const r = await rulesApi.put({ profile: draft.profile, advanced: draft.advanced, items: draft.items });
      toast.success('Regeln gespeichert – sie gelten beim nächsten Berechnen');
      const d = draftOf({ ...state, ...r });
      setSaved(d);
      setDraft(structuredClone(d));
      invalidate('settings');
      q.reload();
    } catch (e) {
      toast.error(e, 'Speichern');
    }
  };

  const exportFile = () => {
    const blob = new Blob([exportPayload({ ...state, profile: draft.profile, items: draft.items }, settings?.school_name ?? '')], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'regeln-und-prioritaeten.json';
    a.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const importFile = async (file: File) => {
    try {
      const parsed = parseImport(await file.text());
      update((d) => ({ ...d, profile: parsed.profile || d.profile, items: { ...d.items, ...Object.fromEntries(Object.entries(parsed.items).filter(([k]) => k in d.items)) } }));
      if (parsed.templates.length && canEdit) {
        const own = state.templates.filter((t) => !t.builtin).map(({ builtin: _b, ...t }) => t);
        await rulesApi.put({ templates: [...own, ...parsed.templates.map(({ builtin: _b, ...t }) => t)] });
        q.reload();
      }
      toast.success('Regeln aus Datei übernommen – prüfen und speichern');
    } catch (e) {
      toast.error(errorMessage(e), 'Import');
    }
  };

  const groups = state.groups.map((g) => ({ ...g, defs: state.catalog.filter((d) => d.group === g.id && visible.has(d.id)) })).filter((g) => g.defs.length > 0);
  const hiddenCount = state.catalog.length - visible.size;

  if (firstTime || chooseProfile) {
    return (
      <div className="stack">
        <section className="card">
          <h2 style={{ marginBottom: 12 }}>
            Welche Schulart passt am besten?{' '}
            <HelpTip label="Erklärung: Schulart">
              Die Vorlage bringt passende Wichtigkeiten mit und zeigt nur die Bausteine, die diese Schulart braucht. Alles bleibt danach frei änderbar; unter „Erweitert“ sind immer alle Bausteine erreichbar.
            </HelpTip>
          </h2>
          <ProfilePicker templates={state.templates} value={draft.profile} onPick={pick} disabled={!canEdit} />
          <div className="row" style={{ marginTop: 12 }}>
            {chooseProfile && (
              <button type="button" className="btn" onClick={() => setChooseProfile(false)}>
                Abbrechen
              </button>
            )}
            {firstTime && (
              <button type="button" className="btn" onClick={() => update((d) => ({ ...d, profile: 'standard' }))}>
                Ohne Auswahl weiter (bisherige Werte behalten)
              </button>
            )}
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="stack">
      <section className="card">
        <div className="row-between" style={{ flexWrap: 'wrap', gap: 8 }}>
          <div>
            <h2 style={{ margin: 0 }}>
              Regeln für den Stundenplan{' '}
              <HelpTip label="Hilfe zu Regeln und Prioritäten">
                Harte Regeln (keine Doppelbelegung, Sperrzeiten, Fachräume, Wegezeit) gelten immer. Die Bausteine hier sind die weichen Ziele: Je wichtiger ein
                Baustein, desto eher gibt der Generator anderswo nach. „Muss“ zählt zwanzigmal so stark wie „Wichtig“ und ist damit praktisch hart. Ausnahmen
                lassen einen Baustein für bestimmte Jahrgänge, Klassen, Fächer, Lehrkräfte oder Wochen anders gelten.
              </HelpTip>
            </h2>
            <p className="small muted" style={{ margin: '4px 0 0' }}>
              Vorlage: <strong>{template?.name ?? 'Eigene Einstellungen'}</strong>
              {hiddenCount > 0 && !draft.advanced ? ` · ${hiddenCount} Baustein${hiddenCount !== 1 ? 'e' : ''} ausgeblendet (ohne Datenbezug oder Feinsteuerung)` : ''}
            </p>
          </div>
          <div className="row" style={{ flexWrap: 'wrap', gap: 6 }}>
            <label className="check">
              <input type="checkbox" checked={draft.advanced} onChange={(e) => update((d) => ({ ...d, advanced: e.target.checked }))} /> Erweitert: alle Bausteine und Zahlenwerte
            </label>
            {canEdit && (
              <button type="button" className="btn btn-sm" onClick={() => setChooseProfile(true)}>
                <Icon name="grid" /> Vorlage wechseln
              </button>
            )}
            <button type="button" className="btn btn-sm" onClick={exportFile}>
              <Icon name="download" /> Exportieren
            </button>
            {canEdit && (
              <>
                <button type="button" className="btn btn-sm" onClick={() => fileRef.current?.click()}>
                  <Icon name="upload" /> Importieren
                </button>
                <input ref={fileRef} type="file" accept="application/json,.json" className="sr-only" aria-label="Regel-Datei wählen" onChange={(e) => { const f = e.target.files?.[0]; if (f) void importFile(f); e.target.value = ''; }} />
                <button type="button" className="btn btn-sm" onClick={() => setSaveTemplate({ name: '', description: '' })}>
                  <Icon name="plus" /> Als eigene Vorlage sichern
                </button>
              </>
            )}
          </div>
        </div>
      </section>

      {groups.map((g) => (
        <section key={g.id} className="card">
          <h2>
            {g.title} <HelpTip>{g.text}</HelpTip>
          </h2>
          <div style={{ marginTop: 8 }}>
            {g.defs.map((def) => (
              <RuleCard key={def.id} def={def} item={draft.items[def.id] as RuleItem} onChange={(it) => setItem(def.id, it)} options={state.options} disabled={!canEdit} advanced={draft.advanced} />
            ))}
          </div>
        </section>
      ))}

      <section className="card">
        <h2>
          Gilt immer (harte Regeln) <HelpTip>Diese Regeln verletzt der Generator nie. Sie werden nicht hier, sondern an den Daten selbst eingestellt – die Links führen dorthin.</HelpTip>
        </h2>
        <ul className="list-plain small" style={{ marginTop: 8 }}>
          {state.hard_rules.map((h) => (
            <li key={h.id} style={{ marginBottom: 4 }}>
              <strong>{h.title}</strong>
              {h.count !== null ? ` (${h.count} mit eigenen Angaben)` : ''} – {h.text} {h.link ? <Link to={h.link}>öffnen</Link> : null}
            </li>
          ))}
        </ul>
      </section>

      <Simulation draft={draft} dirty={dirty} canGenerate={canGenerate} />

      {canEdit && (
        <div className="row-end" style={{ position: 'sticky', bottom: 0, background: 'var(--bg)', padding: '8px 0', zIndex: 5 }}>
          {dirty && <span className="small muted">Ungespeicherte Änderungen</span>}
          <button type="button" className="btn" disabled={!dirty} onClick={() => saved && setDraft(structuredClone(saved))}>
            Verwerfen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save} disabled={!dirty}>
            Speichern
          </AsyncButton>
        </div>
      )}
      {!canEdit && <Alert kind="info">Ändern dürfen nur Konten mit dem Recht „Einstellungen bearbeiten“.</Alert>}

      {saveTemplate && (
        <Modal title="Als eigene Vorlage sichern" onClose={() => setSaveTemplate(null)}>
          <div className="stack-sm">
            <Field
              label="Name"
              htmlFor="tmpl-name"
              help="Die aktuellen Bausteine (mit Ausnahmen) werden als Vorlage gespeichert, z. B. für das nächste Schuljahr oder zum Export an eine andere Schule."
            >
              <input id="tmpl-name" type="text" maxLength={80} value={saveTemplate.name} onChange={(e) => setSaveTemplate({ ...saveTemplate, name: e.target.value })} />
            </Field>
            <Field label="Beschreibung (optional)" htmlFor="tmpl-desc">
              <input id="tmpl-desc" type="text" maxLength={300} value={saveTemplate.description} onChange={(e) => setSaveTemplate({ ...saveTemplate, description: e.target.value })} />
            </Field>
            <div className="row-end">
              <button type="button" className="btn" onClick={() => setSaveTemplate(null)}>
                Abbrechen
              </button>
              <AsyncButton
                className="btn btn-primary"
                disabled={!saveTemplate.name.trim()}
                onClick={async () => {
                  try {
                    const r = await rulesApi.saveTemplate({ name: saveTemplate.name.trim(), description: saveTemplate.description.trim(), items: draft.items, show: [...visible] });
                    toast.success('Vorlage gespeichert');
                    update((d) => ({ ...d, profile: r.id }));
                    setSaveTemplate(null);
                    q.reload();
                  } catch (e) {
                    toast.error(e, 'Vorlage');
                  }
                }}
              >
                Sichern
              </AsyncButton>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
