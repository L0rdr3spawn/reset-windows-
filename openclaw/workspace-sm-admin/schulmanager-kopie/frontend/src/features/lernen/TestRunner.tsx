/**
 * Selbsttest durchführen und Ergebnis ansehen. Antworten werden beim Eingeben auf dem Server gespeichert
 * (bei „Rückmeldung sofort“ erst mit „Prüfen“, danach ist die Antwort gesperrt); gewertet wird nur auf dem Server.
 * Dieselbe Ansicht zeigt beendete Versuche (Schüler/in) und – für Lehrende – einen Versuch aus der Auswertung.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { errorMessage } from '../../api/client';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { Markdown } from '../channels/MarkdownView';
import { learnApi, type Answer, type Attempt, type CheckedView, type PublicQuestion } from './api';
import { answerFilled, formatTimeLeft, gapParts, numberText, openQuestions, percentText, pointsText, solutionText, verdict } from './logic';
import './lernen.css';

// ------------------------------------------------------------------------------------------ Eingabe je Fragenart
function QuestionBody({ q, answer, onChange, disabled }: { q: PublicQuestion; answer: Answer | undefined; onChange: (a: Answer) => void; disabled: boolean }) {
  const name = `q${q.id}`;
  switch (q.type) {
    case 'single':
      return (
        <div className="ln-choices" role="radiogroup" aria-label="Antworten">
          {(q.options ?? []).map((o) => (
            <label key={o.id} className="ln-choice">
              <input type="radio" name={name} disabled={disabled} checked={answer === o.id} onChange={() => onChange(o.id)} />
              <span className="ln-seg">
                <Markdown text={o.text} />
              </span>
            </label>
          ))}
        </div>
      );
    case 'multi': {
      const chosen = Array.isArray(answer) ? (answer as number[]) : [];
      return (
        <div className="ln-choices" role="group" aria-label="Antworten">
          {(q.options ?? []).map((o) => (
            <label key={o.id} className="ln-choice">
              <input type="checkbox" disabled={disabled} checked={chosen.includes(o.id)} onChange={(e) => onChange(e.target.checked ? [...chosen, o.id].sort((a, b) => a - b) : chosen.filter((i) => i !== o.id))} />
              <span className="ln-seg">
                <Markdown text={o.text} />
              </span>
            </label>
          ))}
        </div>
      );
    }
    case 'truefalse':
      return (
        <div className="ln-choices ln-inline" role="radiogroup" aria-label="Wahr oder falsch">
          {[
            ['Wahr', true],
            ['Falsch', false],
          ].map(([label, v]) => (
            <label key={String(label)} className="ln-choice">
              <input type="radio" name={name} disabled={disabled} checked={answer === v} onChange={() => onChange(v as boolean)} />
              <span>{label as string}</span>
            </label>
          ))}
        </div>
      );
    case 'cloze': {
      const parts = gapParts(q.text);
      const values = Array.isArray(answer) ? (answer as string[]) : [];
      const set = (i: number, v: string) => onChange(Array.from({ length: q.gaps ?? parts.length - 1 }, (_, k) => (k === i ? v : values[k] ?? '')));
      return (
        <div className="ln-cloze">
          {parts.map((p, i) => (
            <span key={i} className="ln-seg">
              <Markdown text={p} />
              {i < parts.length - 1 && <input type="text" className="ln-gap" aria-label={`Lücke ${i + 1}`} maxLength={200} disabled={disabled} value={values[i] ?? ''} onChange={(e) => set(i, e.target.value)} />}
            </span>
          ))}
        </div>
      );
    }
    case 'matching': {
      const map = answer && typeof answer === 'object' && !Array.isArray(answer) ? (answer as Record<string, number>) : {};
      return (
        <ul className="ln-match">
          {(q.lefts ?? []).map((l) => (
            <li key={l.id} className="ln-match-row">
              <span className="ln-match-left">{l.text}</span>
              <select aria-label={`Zuordnung zu „${l.text}“`} disabled={disabled} value={map[String(l.id)] ?? ''} onChange={(e) => {
                const next = { ...map };
                if (e.target.value === '') delete next[String(l.id)];
                else next[String(l.id)] = Number(e.target.value);
                onChange(next);
              }}>
                <option value="">– wählen –</option>
                {(q.rights ?? []).map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.text}
                  </option>
                ))}
              </select>
            </li>
          ))}
        </ul>
      );
    }
    default:
      return (
        <div className="ln-numeric">
          <input type="text" inputMode="decimal" aria-label="Antwort (Zahl)" maxLength={40} disabled={disabled} value={typeof answer === 'string' || typeof answer === 'number' ? String(answer) : ''} onChange={(e) => onChange(e.target.value)} />
          {q.unit ? <span className="muted">{q.unit}</span> : null}
        </div>
      );
  }
}

function Feedback({ q, view }: { q: PublicQuestion; view: CheckedView }) {
  const v = verdict(view.fraction);
  const hints = Object.values(view.feedback.options);
  return (
    <div className={`ln-feedback ln-${v.tone}`} role="status">
      <p>
        <span className={`badge badge-${v.tone}`}>{v.label}</span> <span className="small">{pointsText(view.points, view.max)}</span>
      </p>
      {view.fraction < 0.999 && <p className="small">Richtig wäre: {solutionText(q, view.solution) || '–'}</p>}
      {hints.map((h, i) => (
        <p key={i} className="small">
          {h}
        </p>
      ))}
      {view.feedback.general && <p className="small">{view.feedback.general}</p>}
    </div>
  );
}

// ------------------------------------------------------------------------------------------ Versuch
export function TestRunner({ channelId, testId, attemptId, onClose, onChanged }: {
  channelId: number;
  testId: number;
  /** vorhandener Versuch (ansehen); ohne Angabe wird ein Versuch gestartet bzw. fortgesetzt */
  attemptId?: number;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [checked, setChecked] = useState<Record<string, CheckedView>>({});
  const [left, setLeft] = useState<number | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const timers = useRef(new Map<number, number>());
  const latest = useRef<Record<string, Answer>>({});
  const attemptRef = useRef<Attempt | null>(null);
  attemptRef.current = attempt;
  latest.current = answers;
  const changedRef = useRef(onChanged);
  changedRef.current = onChanged;

  const load = useCallback(async () => {
    try {
      const a = attemptId ? await learnApi.attempt(channelId, testId, attemptId) : await learnApi.startAttempt(channelId, testId);
      setAttempt(a);
      setAnswers(a.answers);
      setChecked(a.checked);
      setLeft(a.time_left_s);
      changedRef.current();
    } catch (e) {
      setError(e);
    }
  }, [channelId, testId, attemptId]);

  useEffect(() => {
    load();
    const t = timers.current;
    return () => t.forEach((id) => window.clearTimeout(id));
  }, [load]);

  const running = attempt?.state === 'running';

  const saveNow = useCallback(async (qid: number) => {
    const a = attemptRef.current;
    if (!a) return;
    timers.current.delete(qid);
    try {
      await learnApi.saveAnswer(channelId, testId, a.id, qid, (latest.current[String(qid)] ?? null) as Answer);
      setProblem(null);
    } catch (e) {
      setProblem(errorMessage(e));
    }
  }, [channelId, testId]);

  const flush = useCallback(async () => {
    const pending = [...timers.current.entries()];
    pending.forEach(([, id]) => window.clearTimeout(id));
    await Promise.all(pending.map(([qid]) => saveNow(qid)));
  }, [saveNow]);

  const finish = useCallback(async () => {
    const a = attemptRef.current;
    if (!a) return;
    await flush();
    try {
      const done = await learnApi.finishAttempt(channelId, testId, a.id);
      setAttempt(done);
      setAnswers(done.answers);
      setLeft(null);
      changedRef.current();
    } catch (e) {
      setProblem(errorMessage(e));
    }
  }, [channelId, testId, flush]);

  // Uhr: läuft sie ab, wird der Versuch abgegeben
  useEffect(() => {
    if (!running || left === null) return undefined;
    if (left <= 0) {
      finish();
      return undefined;
    }
    const id = window.setTimeout(() => setLeft((s) => (s === null ? s : s - 1)), 1000);
    return () => window.clearTimeout(id);
  }, [running, left, finish]);

  const change = (q: PublicQuestion, value: Answer) => {
    setAnswers((a) => ({ ...a, [String(q.id)]: value }));
    latest.current = { ...latest.current, [String(q.id)]: value };
    if (attempt?.immediate_feedback) return; // dort zählt erst „Prüfen“
    const prev = timers.current.get(q.id);
    if (prev) window.clearTimeout(prev);
    timers.current.set(q.id, window.setTimeout(() => saveNow(q.id), 600));
  };

  const check = async (q: PublicQuestion) => {
    if (!attempt) return;
    try {
      const r = await learnApi.saveAnswer(channelId, testId, attempt.id, q.id, (answers[String(q.id)] ?? null) as Answer);
      if (r.checked) setChecked((c) => ({ ...c, [String(q.id)]: r.checked as CheckedView }));
      setProblem(null);
    } catch (e) {
      setProblem(errorMessage(e));
    }
  };

  const close = async () => {
    await flush();
    onClose();
  };

  const questions = attempt?.questions ?? [];
  const open = useMemo(() => openQuestions(questions, answers), [questions, answers]);
  const result = attempt?.result;
  const details = result?.details ?? {};
  const view = (q: PublicQuestion): CheckedView | undefined => checked[String(q.id)] ?? details[String(q.id)];
  const runningPoints = useMemo(() => Object.values(checked).reduce((s, v) => s + v.points, 0), [checked]);

  return (
    <Modal
      title={attempt?.title ?? 'Selbsttest'}
      size="lg"
      onClose={close}
      footer={
        running ? (
          <>
            <button type="button" className="btn" onClick={close}>
              Später fortsetzen
            </button>
            <AsyncButton className="btn btn-primary" confirm={open.length ? `${open.length} ${open.length === 1 ? 'Frage ist' : 'Fragen sind'} noch offen. Trotzdem abgeben?` : 'Versuch abgeben?'} onClick={finish}>
              Abgeben
            </AsyncButton>
          </>
        ) : (
          <button type="button" className="btn btn-primary" onClick={close}>
            Schließen
          </button>
        )
      }
    >
      {error && !attempt ? (
        <ErrorBox error={error} onRetry={load} />
      ) : !attempt ? (
        <Loading />
      ) : (
        <div className="stack">
          <div className="ln-run-head">
            <span className="small muted">Versuch {attempt.number}</span>
            {running && left !== null && (
              <span className={`badge ${left < 60 ? 'badge-danger' : 'badge-info'}`} role="timer" aria-label={`Restzeit ${formatTimeLeft(left)}`}>
                Noch {formatTimeLeft(left)}
              </span>
            )}
            {running && attempt.immediate_feedback && <span className="badge badge-primary">{pointsText(runningPoints, attempt.max_points)} bisher</span>}
          </div>
          {problem && <Alert kind="error">{problem}</Alert>}
          {!running && result && (
            <div className="ln-score" role="status">
              {result.points !== undefined ? (
                <>
                  <strong className="ln-score-main">{pointsText(result.points, result.max_points)}</strong>
                  <span>{percentText(result.percent)}</span>
                  {result.passed === true && <span className="badge badge-success">Bestanden</span>}
                  {result.passed === false && <span className="badge badge-warning">Noch nicht bestanden</span>}
                </>
              ) : (
                <strong>Der Versuch ist abgegeben.</strong>
              )}
            </div>
          )}
          <ol className="ln-questions">
            {questions.map((q, i) => {
              const fv = view(q);
              const locked = !running || !!checked[String(q.id)];
              return (
                <li key={q.id} className="card ln-question">
                  <div className="ln-question-head">
                    <span className="ln-question-no">Frage {i + 1}</span>
                    <span className="small muted">
                      {numberText(q.points, 2)} {q.points === 1 ? 'Punkt' : 'Punkte'}
                    </span>
                  </div>
                  {q.type !== 'cloze' && <Markdown text={q.text} />}
                  <QuestionBody q={q} answer={answers[String(q.id)]} onChange={(v) => change(q, v)} disabled={locked} />
                  {running && attempt.immediate_feedback && !checked[String(q.id)] && (
                    <div>
                      <AsyncButton className="btn btn-sm" disabled={!answerFilled(q, answers[String(q.id)])} onClick={() => check(q)}>
                        Prüfen
                      </AsyncButton>
                    </div>
                  )}
                  {fv && <Feedback q={q} view={fv} />}
                </li>
              );
            })}
          </ol>
        </div>
      )}
    </Modal>
  );
}

export default TestRunner;
