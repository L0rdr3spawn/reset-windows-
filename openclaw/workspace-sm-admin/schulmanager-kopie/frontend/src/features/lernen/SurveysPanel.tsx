/**
 * Umfragen (Feedback-Fragebögen) eines Kursraums. Fragen und Eingabefelder kommen aus dem Formular-Baukasten
 * (`features/formulare`): gleiche Feldarten, dazu die Skala 1–5. Anonym möglich, Auswertung mit Balken und CSV.
 */
import { useMemo, useState } from 'react';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../lib/dates';
import { fromLocalInput, toLocalInput } from '../channels/logic';
import type { Answers, FormDefinition, FormField } from '../formulare/api';
import { FormFields } from '../formulare/FormFields';
import { answerErrors, emptyDefinition, initialAnswers, moveItem, newField } from '../formulare/logic';
import { FieldEditor } from '../formulare/TemplateEditor';
import { learnApi, type Survey, type SurveyItemResult, type SurveyResults } from './api';
import { Bar } from './PollCard';
import { barPercent, numberText, SURVEY_FIELD_TYPES, SURVEY_STATE_LABELS, SURVEY_TYPE_LABELS } from './logic';
import './lernen.css';

const TONE = { entwurf: 'badge-warning', offen: 'badge-success', geschlossen: 'badge-primary' } as const;

function asDefinition(fields: FormField[], intro: string): FormDefinition {
  return { ...emptyDefinition(), fields, intro };
}

// ------------------------------------------------------------------------------------------ Bearbeiten
function SurveyEditor({ channelId, survey, locked, onClose, onSaved }: { channelId: number; survey: Survey | null; locked: boolean; onClose: () => void; onSaved: () => void }) {
  const [title, setTitle] = useState(survey?.title ?? '');
  const [intro, setIntro] = useState(survey?.intro ?? '');
  const [fields, setFields] = useState<FormField[]>(survey?.fields ?? []);
  const [anonymous, setAnonymous] = useState(survey?.anonymous ?? false);
  const [publish, setPublish] = useState(survey ? survey.status !== 'entwurf' : true);
  const [closes, setCloses] = useState(toLocalInput(survey?.closes_at));
  const [share, setShare] = useState(survey?.results_to_students ?? false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const typeMeta = useMemo(() => ({ field_types: SURVEY_TYPE_LABELS }), []);

  const save = async () => {
    setError(null);
    if (!title.trim()) return setError('Bitte einen Titel eingeben.');
    if (!fields.length) return setError('Bitte mindestens eine Frage hinzufügen.');
    if (fields.some((f) => !f.label.trim())) return setError('Jede Frage braucht eine Beschriftung.');
    const clean = fields.map((f) => (f.options ? { ...f, options: f.options.map((o) => o.trim()).filter(Boolean) } : f));
    try {
      if (survey) {
        await learnApi.patchSurvey(channelId, survey.id, {
          title,
          intro,
          ...(locked ? {} : { fields: clean, anonymous }),
          closes_at: fromLocalInput(closes),
          clear_closes_at: !closes,
          results_to_students: share,
          status: survey.status === 'geschlossen' ? 'geschlossen' : publish ? 'offen' : 'entwurf',
        });
      } else {
        await learnApi.createSurvey(channelId, { title, intro, fields: clean, anonymous, status: publish ? 'offen' : 'entwurf', closes_at: fromLocalInput(closes), results_to_students: share });
      }
      toast.success('Umfrage gespeichert');
      onSaved();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  return (
    <Modal
      title={survey ? 'Umfrage bearbeiten' : 'Neue Umfrage'}
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
        {error && <Alert kind="error">{error}</Alert>}
        {locked && <Alert kind="info">Antworten liegen vor: Fragen und Anonymität sind gesperrt.</Alert>}
        <Field label="Titel" htmlFor="sv-title">
          <input id="sv-title" type="text" maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} />
        </Field>
        <Field label="Einleitung (optional)" htmlFor="sv-intro">
          <textarea id="sv-intro" rows={2} maxLength={1500} value={intro} onChange={(e) => setIntro(e.target.value)} />
        </Field>
        <fieldset className="ln-fieldset" disabled={locked}>
          <legend>Fragen</legend>
          <ol className="fm-field-list">
            {fields.map((f, i) => (
              <FieldEditor
                key={f.id}
                f={f}
                index={i}
                count={fields.length}
                meta={typeMeta}
                onChange={(next) => setFields((all) => all.map((x) => (x.id === f.id ? next : x)))}
                onMove={(dir) => setFields((all) => moveItem(all, i, dir))}
                onRemove={() => setFields((all) => all.filter((x) => x.id !== f.id))}
              />
            ))}
          </ol>
          <div className="ln-add-row">
            {SURVEY_FIELD_TYPES.map((t) => (
              <button key={t} type="button" className="btn btn-sm" onClick={() => setFields((all) => [...all, newField(t, all)])}>
                <Icon name="plus" /> {SURVEY_TYPE_LABELS[t]}
              </button>
            ))}
          </div>
        </fieldset>
        <div className="ln-two">
          <label className="check">
            <input type="checkbox" checked={anonymous} disabled={locked} onChange={(e) => setAnonymous(e.target.checked)} /> Anonym
          </label>
          <label className="check">
            <input type="checkbox" checked={publish} disabled={survey?.status === 'geschlossen'} onChange={(e) => setPublish(e.target.checked)} /> Für Teilnehmende freigeben
          </label>
          <label className="check">
            <input type="checkbox" checked={share} onChange={(e) => setShare(e.target.checked)} /> Auswertung nach dem Ende zeigen
          </label>
        </div>
        <Field label="Ende (optional)" htmlFor="sv-end">
          <input id="sv-end" type="datetime-local" value={closes} onChange={(e) => setCloses(e.target.value)} />
        </Field>
      </div>
    </Modal>
  );
}

// ------------------------------------------------------------------------------------------ Ausfüllen
function RespondDialog({ channelId, survey, onClose, onDone }: { channelId: number; survey: Survey; onClose: () => void; onDone: () => void }) {
  const detail = useApi((signal) => learnApi.survey(channelId, survey.id, signal), [channelId, survey.id]);
  const defn = useMemo(() => asDefinition(detail.data?.fields ?? [], detail.data?.intro ?? ''), [detail.data]);
  const [answers, setAnswers] = useState<Answers>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const current = detail.data ? { ...initialAnswers(defn), ...answers } : {};
  return (
    <Modal
      title={survey.title}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            disabled={!detail.data}
            onClick={async () => {
              const problems = answerErrors(defn, current, null, false);
              setErrors(problems);
              if (Object.keys(problems).length) return;
              try {
                await learnApi.respond(channelId, survey.id, current);
                toast.success('Danke für Ihre Antwort');
                onDone();
                onClose();
              } catch (e) {
                setError(errorMessage(e));
              }
            }}
          >
            Absenden
          </AsyncButton>
        </>
      }
    >
      {detail.error && !detail.data ? (
        <ErrorBox error={detail.error} onRetry={detail.reload} />
      ) : !detail.data ? (
        <Loading />
      ) : (
        <div className="stack-sm">
          {survey.anonymous && <span className="badge badge-info">Anonym</span>}
          {error && <Alert kind="error">{error}</Alert>}
          <FormFields definition={defn} answers={current} errors={errors} onChange={(id, v) => setAnswers((a) => ({ ...a, [id]: v }))} />
        </div>
      )}
    </Modal>
  );
}

// ------------------------------------------------------------------------------------------ Auswertung
function ItemResult({ item, total }: { item: SurveyItemResult; total: number }) {
  return (
    <li className="ln-result">
      <h4 className="ln-result-title">{item.label}</h4>
      <p className="small muted">
        {item.answered} von {total} haben geantwortet
        {item.mean !== undefined && item.mean !== null ? ` · Mittelwert ${numberText(item.mean, 2)}` : ''}
        {item.min !== undefined && item.min !== null && item.type === 'number' ? ` · kleinster Wert ${numberText(item.min, 2)}, größter ${numberText(item.max, 2)}` : ''}
      </p>
      {item.counts && (
        <ul className="ln-bars">
          {item.counts.map((c) => {
            const pct = barPercent(c.count, item.answered);
            return (
              <li key={c.option} className="ln-option">
                <div className="ln-option-head">
                  <span className="ln-option-text">{c.option}</span>
                  <span className="ln-option-count mono">
                    {c.count} · {pct} %
                  </span>
                </div>
                <Bar percent={pct} label={`${c.option}: ${c.count} (${pct} %)`} />
              </li>
            );
          })}
        </ul>
      )}
      {item.texts && (item.texts.length ? (
        <ul className="ln-texts">
          {item.texts.map((t, i) => (
            <li key={i}>{t}</li>
          ))}
        </ul>
      ) : (
        <p className="muted small">Keine Antworten.</p>
      ))}
    </li>
  );
}

function ResultsDialog({ channelId, survey, onClose }: { channelId: number; survey: Survey; onClose: () => void }) {
  const q = useApi<SurveyResults>((signal) => learnApi.surveyResults(channelId, survey.id, signal), [channelId, survey.id]);
  const data = q.data;
  return (
    <Modal
      title={`Auswertung: ${survey.title}`}
      size="lg"
      onClose={onClose}
      footer={
        <>
          {data && survey.editable && (
            <a className="btn" href={learnApi.surveyCsvUrl(channelId, survey.id)} download>
              <Icon name="download" /> CSV
            </a>
          )}
          <button type="button" className="btn btn-primary" onClick={onClose}>
            Schließen
          </button>
        </>
      }
    >
      {q.error && !data ? (
        <ErrorBox error={q.error} onRetry={q.reload} />
      ) : !data ? (
        <Loading />
      ) : (
        <div className="stack-sm">
          <p>
            <strong>{data.response_count}</strong> {data.response_count === 1 ? 'Antwort' : 'Antworten'}
            {data.member_count ? ` von ${data.member_count} Teilnehmenden` : ''}
            {data.survey.anonymous ? ' · anonym' : ''}
          </p>
          <ul className="ln-results">
            {data.items.map((item) => (
              <ItemResult key={item.id} item={item} total={data.response_count} />
            ))}
          </ul>
          {data.responses.length > 0 && !data.survey.anonymous && (
            <details>
              <summary>Einzelne Antworten ({data.responses.length})</summary>
              <ul className="ln-texts">
                {data.responses.map((r, i) => (
                  <li key={i}>
                    <strong>{r.name}</strong> <span className="muted small">{formatDateTime(r.at)}</span>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </Modal>
  );
}

// ------------------------------------------------------------------------------------------ Liste
export default function SurveysPanel({ channelId, student }: { channelId: number; student: boolean }) {
  const q = useApi((signal) => learnApi.surveys(channelId, signal), [channelId], { live: [`channel:${channelId}:`] });
  const [editing, setEditing] = useState<Survey | 'new' | null>(null);
  const [responding, setResponding] = useState<Survey | null>(null);
  const [viewing, setViewing] = useState<Survey | null>(null);
  const toast = useToast();
  if (q.error && !q.data) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  const { surveys, can_create } = q.data;
  const act = async (fn: () => Promise<unknown>, message: string) => {
    await fn();
    toast.success(message);
    q.reload();
  };
  const openEditor = async (s: Survey) => setEditing(await learnApi.survey(channelId, s.id));

  return (
    <section className="stack" aria-label="Umfragen">
      {can_create && (
        <div>
          <button type="button" className="btn btn-primary" onClick={() => setEditing('new')}>
            <Icon name="plus" /> Neue Umfrage
          </button>
        </div>
      )}
      {surveys.length === 0 ? (
        <Empty icon="list" title="Noch keine Umfrage">
          {can_create ? 'Legen Sie einen Fragebogen an, z. B. ein Feedback zum Unterricht.' : 'Sobald eine Umfrage freigegeben ist, erscheint sie hier.'}
        </Empty>
      ) : (
        <ul className="ln-cards">
          {surveys.map((s) => (
            <li key={s.id} className="card ln-card">
              <div className="ln-card-head">
                <h3 className="ln-card-title">{s.title}</h3>
                <span className={`badge ${TONE[s.state]}`}>{SURVEY_STATE_LABELS[s.state]}</span>
              </div>
              <p className="small muted">
                {s.question_count} {s.question_count === 1 ? 'Frage' : 'Fragen'}
                {s.anonymous ? ' · anonym' : ''}
                {s.closes_at && s.state === 'offen' ? ` · bis ${formatDateTime(s.closes_at)}` : ''}
                {s.response_count !== null ? ` · ${s.response_count} ${s.response_count === 1 ? 'Antwort' : 'Antworten'}` : ''}
              </p>
              <div className="ln-card-actions">
                {student && s.state === 'offen' && !s.done && (
                  <button type="button" className="btn btn-primary btn-sm" onClick={() => setResponding(s)}>
                    Ausfüllen
                  </button>
                )}
                {student && s.done && <span className="badge badge-success">Beantwortet</span>}
                {s.results_visible && (
                  <button type="button" className="btn btn-sm" onClick={() => setViewing(s)}>
                    Auswertung
                  </button>
                )}
                {s.editable && (
                  <>
                    <button type="button" className="btn btn-sm" onClick={() => openEditor(s)}>
                      <Icon name="edit" /> Bearbeiten
                    </button>
                    {s.status === 'entwurf' && (
                      <AsyncButton className="btn btn-sm" onClick={() => act(() => learnApi.patchSurvey(channelId, s.id, { status: 'offen' }), 'Umfrage freigegeben')}>
                        Freigeben
                      </AsyncButton>
                    )}
                    {s.state === 'offen' && (
                      <AsyncButton className="btn btn-sm" confirm="Umfrage jetzt beenden?" onClick={() => act(() => learnApi.patchSurvey(channelId, s.id, { status: 'geschlossen' }), 'Umfrage beendet')}>
                        Beenden
                      </AsyncButton>
                    )}
                    {s.state === 'geschlossen' && (
                      <AsyncButton className="btn btn-sm" onClick={() => act(() => learnApi.patchSurvey(channelId, s.id, { status: 'offen', clear_closes_at: true }), 'Umfrage wieder geöffnet')}>
                        Wieder öffnen
                      </AsyncButton>
                    )}
                    <AsyncButton className="btn btn-sm btn-ghost" confirm="Umfrage samt allen Antworten löschen?" onClick={() => act(() => learnApi.deleteSurvey(channelId, s.id), 'Umfrage gelöscht')}>
                      <Icon name="trash" /> Löschen
                    </AsyncButton>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
      {editing && (
        <SurveyEditor
          channelId={channelId}
          survey={editing === 'new' ? null : editing}
          locked={editing !== 'new' && (editing.response_count ?? 0) > 0}
          onClose={() => setEditing(null)}
          onSaved={q.reload}
        />
      )}
      {responding && <RespondDialog channelId={channelId} survey={responding} onClose={() => setResponding(null)} onDone={q.reload} />}
      {viewing && <ResultsDialog channelId={channelId} survey={viewing} onClose={() => setViewing(null)} />}
    </section>
  );
}
