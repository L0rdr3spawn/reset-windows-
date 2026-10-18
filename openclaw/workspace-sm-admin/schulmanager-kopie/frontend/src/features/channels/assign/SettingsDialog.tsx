/**
 * Einstellungen einer Aufgabe: Bewertungsart (Note als Text, Punkte, Raster, Leitfaden), Notenschlüssel, Raster-Vorlagen,
 * Gruppenabgabe und Freigabe des ausgefüllten Rasters für Eltern.
 */
import { useMemo, useState } from 'react';
import { errorMessage } from '../../../api/client';
import { Modal } from '../../../components/Modal';
import { AsyncButton, Field, Loading, SegmentedControl } from '../../../components/ui';
import { useToast } from '../../../context/ToastContext';
import { useApi } from '../../../hooks/useApi';
import type { Item } from '../types';
import { assignApi, type SettingsInput } from './api';
import { draftToRubric, fmtPoints, newRubricDraft, parsePoints, rubricMax, rubricToDraft, switchKind, type RubricDraft } from './logic';
import { RubricEditor } from './RubricEditor';
import type { AssignSettings, GradeScale, ScaleStep } from './types';
import './aufgaben.css';

type Mode = 'none' | 'points' | 'rubric' | 'guide';
type ScaleChoice = 'noten' | 'punkte' | 'custom';

const MODE_OPTIONS: { value: Mode; label: string }[] = [
  { value: 'none', label: 'Nur Note/Rückmeldung' },
  { value: 'points', label: 'Punkte' },
  { value: 'rubric', label: 'Raster' },
  { value: 'guide', label: 'Leitfaden' },
];

function scaleChoice(scale: GradeScale | undefined): ScaleChoice {
  if (scale && 'preset' in scale) return scale.preset;
  return scale && 'steps' in scale ? 'custom' : 'noten';
}

function stepsToRows(steps: ScaleStep[]): { min: string; label: string }[] {
  return steps.map((s) => ({ min: fmtPoints(s.min), label: s.label }));
}

export function SettingsDialog({ channelId, item, settings, onClose, onDone }: { channelId: number; item: Item; settings: AssignSettings; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const initialMode: Mode = settings.rubric ? settings.rubric.kind : settings.free_max_points ? 'points' : 'none';
  const [mode, setMode] = useState<Mode>(initialMode);
  const [draft, setDraft] = useState<RubricDraft>(settings.rubric ? rubricToDraft(settings.rubric) : newRubricDraft('rubric'));
  const [title, setTitle] = useState(settings.rubric_title);
  const [maxPoints, setMaxPoints] = useState(settings.free_max_points ? fmtPoints(settings.free_max_points) : '');
  const [scale, setScale] = useState<ScaleChoice>(scaleChoice(settings.grade_scale));
  const [rows, setRows] = useState(stepsToRows(settings.scale_steps));
  const [groupMode, setGroupMode] = useState(settings.group_mode);
  const [setId, setSetId] = useState<number | null>(settings.group_set_id);
  const [parents, setParents] = useState(settings.show_parents);
  const [tplName, setTplName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const templates = useApi((signal) => assignApi.templates(signal), []);
  const groups = useApi((signal) => assignApi.groups(channelId, signal), [channelId]);
  const locked = !!settings.has_rubric_grades;
  const groupsLocked = (settings.submission_count ?? 0) > 0;
  const withRubric = mode === 'rubric' || mode === 'guide';

  const setKind = (m: Mode) => {
    setMode(m);
    if (m === 'rubric' || m === 'guide') setDraft((d) => switchKind(d, m));
  };
  const parsedRubric = useMemo(() => (withRubric ? draftToRubric({ ...draft, kind: mode === 'guide' ? 'guide' : 'rubric' }) : null), [withRubric, draft, mode]);
  const max = withRubric ? (parsedRubric && 'rubric' in parsedRubric ? rubricMax(parsedRubric.rubric) : 0) : parsePoints(maxPoints) ?? 0;

  const scaleBody = (): GradeScale | { error: string } => {
    if (scale !== 'custom') return { preset: scale };
    const steps: ScaleStep[] = [];
    for (const r of rows) {
      const min = parsePoints(r.min);
      if (min === null || min > 100 || !r.label.trim()) return { error: 'Im Notenschlüssel braucht jede Stufe eine Grenze (0–100 %) und eine Note.' };
      steps.push({ min, label: r.label.trim() });
    }
    if (steps.length < 2) return { error: 'Der Notenschlüssel braucht mindestens zwei Stufen.' };
    return { steps };
  };

  const save = async () => {
    const body: SettingsInput = {};
    const sc = scaleBody();
    if ('error' in sc) {
      setError(sc.error);
      return;
    }
    body.grade_scale = sc;
    if (!locked) {
      if (withRubric) {
        if (!parsedRubric || 'error' in parsedRubric) {
          setError(parsedRubric && 'error' in parsedRubric ? parsedRubric.error : 'Bitte das Raster ausfüllen.');
          return;
        }
        body.rubric = parsedRubric.rubric;
        body.rubric_title = title;
      } else {
        if (settings.rubric) body.clear_rubric = true;
        if (mode === 'points') {
          const m = parsePoints(maxPoints);
          if (m === null || m <= 0) {
            setError('Bitte die Höchstpunktzahl angeben.');
            return;
          }
          body.max_points = m;
        } else {
          body.max_points = null;
        }
      }
    } else {
      body.rubric_title = title;
    }
    if (!groupsLocked) {
      body.group_mode = groupMode;
      body.group_set_id = groupMode ? setId : null;
      if (groupMode && !setId) {
        setError('Bitte eine Gruppeneinteilung wählen.');
        return;
      }
    }
    body.show_parents = parents;
    try {
      await assignApi.saveSettings(channelId, item.id, body);
      toast.success('Einstellungen gespeichert');
      onDone();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const saveTemplate = async () => {
    if (!parsedRubric || 'error' in parsedRubric) {
      setError(parsedRubric && 'error' in parsedRubric ? parsedRubric.error : 'Kein Raster zum Speichern.');
      return;
    }
    const name = tplName.trim() || title.trim();
    if (!name) {
      setError('Bitte einen Namen für die Vorlage angeben.');
      return;
    }
    const sc = scaleBody();
    try {
      await assignApi.saveTemplate({ title: name, rubric: parsedRubric.rubric, grade_scale: 'error' in sc ? null : sc });
      toast.success('Als Vorlage gespeichert');
      setTplName('');
      templates.reload();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const loadTemplate = (id: number) => {
    const tpl = templates.data?.templates.find((t) => t.id === id);
    if (!tpl?.rubric) return;
    setMode(tpl.rubric.kind);
    setDraft(rubricToDraft(tpl.rubric));
    setTitle(tpl.title);
    if (tpl.grade_scale) {
      setScale(scaleChoice(tpl.grade_scale));
      if ('steps' in tpl.grade_scale) setRows(stepsToRows(tpl.grade_scale.steps));
    }
  };

  const sets = groups.data?.sets ?? [];
  return (
    <Modal
      title="Bewertung und Gruppen"
      size="lg"
      onClose={onClose}
      footer={
        <>
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
        <section className="stack-sm" aria-label="Bewertungsart">
          <Field label="Bewertungsart" help="Raster: Kriterien mit Stufen, die beim Bewerten angeklickt werden. Leitfaden: Kriterien mit Freitext und Höchstpunkten. Aus den Punkten ergibt sich die Note nach dem Notenschlüssel.">
            <SegmentedControl<Mode> label="Bewertungsart" value={mode} onChange={(m) => !locked && setKind(m)} options={MODE_OPTIONS} />
          </Field>
          {locked && <p className="small muted">Raster gesperrt, da Bewertungen vorliegen.</p>}
          {mode === 'points' && (
            <Field label="Höchstpunktzahl" htmlFor="au-max">
              <input id="au-max" inputMode="decimal" value={maxPoints} disabled={locked} onChange={(e) => setMaxPoints(e.target.value)} />
            </Field>
          )}
          {withRubric && (
            <>
              <Field label="Name des Rasters" htmlFor="au-title">
                <input id="au-title" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />
              </Field>
              <RubricEditor value={{ ...draft, kind: mode === 'guide' ? 'guide' : 'rubric' }} onChange={setDraft} disabled={locked} />
              <div className="au-tpl">
                {templates.initialLoading ? (
                  <Loading />
                ) : (
                  <>
                    {!locked && (templates.data?.templates.length ?? 0) > 0 && (
                      <Field label="Vorlage laden" htmlFor="au-tpl">
                        <select id="au-tpl" value="" onChange={(e) => e.target.value && loadTemplate(Number(e.target.value))}>
                          <option value="">– wählen –</option>
                          {templates.data!.templates.map((t) => (
                            <option key={t.id} value={t.id}>
                              {t.title} ({t.kind_label}, {fmtPoints(t.max_points)} P.)
                            </option>
                          ))}
                        </select>
                      </Field>
                    )}
                    <Field label="Als Vorlage speichern" htmlFor="au-tpl-name">
                      <div className="row">
                        <input id="au-tpl-name" value={tplName} maxLength={200} placeholder={title || 'Name der Vorlage'} onChange={(e) => setTplName(e.target.value)} />
                        <AsyncButton className="btn" onClick={saveTemplate}>
                          Speichern
                        </AsyncButton>
                      </div>
                    </Field>
                  </>
                )}
              </div>
            </>
          )}
        </section>

        {mode !== 'none' && (
          <section className="stack-sm" aria-label="Notenschlüssel">
            <Field label="Notenschlüssel" help="Aus der erreichten Prozentzahl wird die Note vorgeschlagen; Sie können sie beim Bewerten überschreiben. Der Schlüssel gilt für Bewertungen ab jetzt.">
              <select value={scale} onChange={(e) => setScale(e.target.value as ScaleChoice)} aria-label="Notenschlüssel">
                <option value="noten">Noten 1–6 (ab 92/81/67/50/30 %)</option>
                <option value="punkte">Punkte 15–0 (Oberstufe)</option>
                <option value="custom">Eigene Prozentgrenzen</option>
              </select>
            </Field>
            {scale === 'custom' && (
              <div className="au-scale">
                {rows.map((r, i) => (
                  <div key={i} className="au-scale-row">
                    <label>
                      <span className="xsmall muted">ab %</span>
                      <input inputMode="decimal" value={r.min} onChange={(e) => setRows(rows.map((x, k) => (k === i ? { ...x, min: e.target.value } : x)))} />
                    </label>
                    <label>
                      <span className="xsmall muted">Note</span>
                      <input value={r.label} maxLength={20} onChange={(e) => setRows(rows.map((x, k) => (k === i ? { ...x, label: e.target.value } : x)))} />
                    </label>
                    <button type="button" className="btn btn-sm btn-ghost" disabled={rows.length <= 2} onClick={() => setRows(rows.filter((_, k) => k !== i))} aria-label={`Stufe ${i + 1} entfernen`}>
                      ×
                    </button>
                  </div>
                ))}
                <button type="button" className="btn btn-sm" onClick={() => setRows([...rows, { min: '0', label: '' }])} disabled={rows.length >= 20}>
                  Stufe hinzufügen
                </button>
              </div>
            )}
            {max > 0 && <p className="xsmall muted">Höchstpunktzahl: {fmtPoints(max)}</p>}
          </section>
        )}

        <section className="stack-sm" aria-label="Gruppenabgabe">
          <label className="check">
            <input type="checkbox" checked={groupMode} disabled={groupsLocked} onChange={(e) => setGroupMode(e.target.checked)} /> Gruppenabgabe (eine Abgabe gilt für alle Mitglieder der Gruppe)
          </label>
          {groupsLocked && <p className="small muted">Gruppenabgabe gesperrt, da Abgaben vorliegen.</p>}
          {groupMode && !groupsLocked && (
            <Field label="Gruppeneinteilung" htmlFor="au-set">
              {groups.initialLoading ? (
                <Loading />
              ) : sets.length ? (
                <select id="au-set" value={setId ?? ''} onChange={(e) => setSetId(e.target.value ? Number(e.target.value) : null)}>
                  <option value="">– wählen –</option>
                  {sets.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.groups.length} Gruppen)
                    </option>
                  ))}
                </select>
              ) : (
                <p className="small muted">Noch keine Gruppeneinteilung.</p>
              )}
            </Field>
          )}
        </section>

        {mode !== 'none' && (
          <label className="check">
            <input type="checkbox" checked={parents} onChange={(e) => setParents(e.target.checked)} /> Eltern sehen das ausgefüllte Raster und die Punkte
          </label>
        )}
      </div>
    </Modal>
  );
}
