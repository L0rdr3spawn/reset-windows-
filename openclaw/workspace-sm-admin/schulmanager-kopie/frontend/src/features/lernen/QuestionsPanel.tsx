/**
 * Fragensammlung eines Kursraums (nur Lehrende): Fragen anlegen, wiederverwenden, aus GIFT importieren, als GIFT
 * exportieren und aus einem anderen eigenen Kursraum übernehmen. Texte unterstützen Markdown und Formeln (`$x^2$`).
 */
import { useState } from 'react';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { channelsApi } from '../channels/api';
import { Markdown } from '../channels/MarkdownView';
import { learnApi, type BankQuestion, type QuestionInput, type QuestionOption, type QuestionType } from './api';
import { cleanQuestion, emptyQuestion, gapCount, MAX_QUESTION_OPTIONS, numberText, QUESTION_TYPE_LABELS, questionError, syncGaps } from './logic';
import './lernen.css';

const TYPES = Object.keys(QUESTION_TYPE_LABELS) as QuestionType[];

function toInput(q: BankQuestion): QuestionInput {
  const d = q.data;
  return {
    ...emptyQuestion(d.type),
    ...d,
    options: d.options?.map((o) => ({ ...o })),
    pairs: d.pairs?.map((p) => ({ ...p })),
    gaps: d.gaps?.map((g) => [...g]),
  };
}

// ------------------------------------------------------------------------------------------ Bearbeiten
function QuestionEditor({ channelId, question, onClose, onSaved }: { channelId: number; question: BankQuestion | null; onClose: () => void; onSaved: () => void }) {
  const [q, setQ] = useState<QuestionInput>(() => (question ? toInput(question) : emptyQuestion('single')));
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const set = (patch: Partial<QuestionInput>) => setQ((x) => ({ ...x, ...patch }));
  const options = q.options ?? [];
  const setOption = (i: number, patch: Partial<QuestionOption>) =>
    set({ options: options.map((o, k) => (k === i ? { ...o, ...patch } : patch.correct && q.type === 'single' ? { ...o, correct: false } : o)) });
  const pairs = q.pairs ?? [];
  const gaps = q.gaps ?? [];

  const save = async () => {
    const clean = cleanQuestion(q);
    const problem = questionError(clean);
    if (problem) return setError(problem);
    try {
      if (question) await learnApi.updateQuestion(channelId, question.id, clean);
      else await learnApi.createQuestion(channelId, clean);
      toast.success('Frage gespeichert');
      onSaved();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  return (
    <Modal
      title={question ? 'Frage bearbeiten' : 'Neue Frage'}
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
        {question && question.used_in.length > 0 && <Alert kind="info">
            Die Frage steht in {question.used_in.map((t) => `„${t.title}“`).join(', ')}.
            <HelpTip>Laufende und beendete Versuche behalten den alten Wortlaut.</HelpTip>
          </Alert>}
        <div className="ln-two">
          <Field label="Art der Frage" htmlFor="qe-type">
            <select id="qe-type" value={q.type} disabled={!!question} onChange={(e) => setQ({ ...emptyQuestion(e.target.value as QuestionType), text: q.text && q.type !== 'cloze' ? q.text : emptyQuestion(e.target.value as QuestionType).text, points: q.points, feedback: q.feedback, category: q.category })}>
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {QUESTION_TYPE_LABELS[t]}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Punkte" htmlFor="qe-points">
            <input id="qe-points" type="text" inputMode="decimal" value={String(q.points)} onChange={(e) => set({ points: e.target.value })} />
          </Field>
        </div>
        <Field
          label={
            <>
              Fragetext <HelpTip>Markdown ist möglich. Formeln schreiben Sie mit Dollarzeichen: $x^2+1$ im Text oder $$\frac{'{a}{b}'}$$ als eigene Zeile.{q.type === 'cloze' ? ' Eine Lücke markieren Sie mit drei Unterstrichen: ___' : ''}</HelpTip>
            </>
          }
          htmlFor="qe-text"
        >
          <textarea id="qe-text" rows={4} maxLength={4000} value={q.text} onChange={(e) => set(q.type === 'cloze' ? { text: e.target.value, gaps: syncGaps(e.target.value, gaps) } : { text: e.target.value })} />
        </Field>
        {q.text.includes('$') && (
          <div className="ln-preview" aria-label="Vorschau">
            <Markdown text={q.text} />
          </div>
        )}

        {(q.type === 'single' || q.type === 'multi') && (
          <fieldset className="ln-fieldset">
            <legend>Antworten (richtige markieren)</legend>
            <ul className="ln-edit-list">
              {options.map((o, i) => (
                <li key={i} className="ln-edit-row ln-edit-wide">
                  <input type={q.type === 'single' ? 'radio' : 'checkbox'} name="qe-correct" aria-label={`Antwort ${i + 1} ist richtig`} checked={!!o.correct} onChange={(e) => setOption(i, { correct: q.type === 'single' ? true : e.target.checked })} />
                  <input type="text" aria-label={`Antwort ${i + 1}`} maxLength={300} value={o.text} onChange={(e) => setOption(i, { text: e.target.value })} />
                  <input type="text" aria-label={`Hinweis zu Antwort ${i + 1}`} placeholder="Hinweis (optional)" maxLength={300} value={o.feedback ?? ''} onChange={(e) => setOption(i, { feedback: e.target.value })} />
                  <button type="button" className="btn btn-sm btn-ghost" aria-label={`Antwort ${i + 1} entfernen`} disabled={options.length <= 2} onClick={() => set({ options: options.filter((_, k) => k !== i) })}>
                    <Icon name="trash" />
                  </button>
                </li>
              ))}
            </ul>
            <button type="button" className="btn btn-sm" disabled={options.length >= MAX_QUESTION_OPTIONS} onClick={() => set({ options: [...options, { text: '', correct: false }] })}>
              <Icon name="plus" /> Antwort hinzufügen
            </button>
          </fieldset>
        )}

        {q.type === 'truefalse' && (
          <fieldset className="ln-fieldset">
            <legend>Richtig ist</legend>
            <div className="ln-two">
              <label className="check">
                <input type="radio" name="qe-tf" checked={q.correct === true} onChange={() => set({ correct: true })} /> Wahr
              </label>
              <label className="check">
                <input type="radio" name="qe-tf" checked={q.correct === false} onChange={() => set({ correct: false })} /> Falsch
              </label>
            </div>
          </fieldset>
        )}

        {q.type === 'cloze' && (
          <fieldset className="ln-fieldset">
            <legend>Richtige Antworten je Lücke ({gapCount(q.text)})</legend>
            <ul className="ln-edit-list">
              {syncGaps(q.text, gaps).map((g, i) => (
                <li key={i} className="ln-edit-row">
                  <span className="ln-gap-no">{i + 1}.</span>
                  <input type="text" aria-label={`Richtige Antworten Lücke ${i + 1}, getrennt durch |`} placeholder="Antwort (mehrere mit | trennen)" value={g.join(' | ')} onChange={(e) => set({ gaps: syncGaps(q.text, gaps).map((x, k) => (k === i ? e.target.value.split('|').map((a) => a.trim()) : x)) })} />
                </li>
              ))}
            </ul>
            <label className="check">
              <input type="checkbox" checked={!!q.case_sensitive} onChange={(e) => set({ case_sensitive: e.target.checked })} /> Groß-/Kleinschreibung beachten
            </label>
          </fieldset>
        )}

        {q.type === 'matching' && (
          <fieldset className="ln-fieldset">
            <legend>Paare (links – rechts)</legend>
            <ul className="ln-edit-list">
              {pairs.map((p, i) => (
                <li key={i} className="ln-edit-row">
                  <input type="text" aria-label={`Paar ${i + 1} links`} maxLength={200} value={p.left} onChange={(e) => set({ pairs: pairs.map((x, k) => (k === i ? { ...x, left: e.target.value } : x)) })} />
                  <input type="text" aria-label={`Paar ${i + 1} rechts`} maxLength={200} value={p.right} onChange={(e) => set({ pairs: pairs.map((x, k) => (k === i ? { ...x, right: e.target.value } : x)) })} />
                  <button type="button" className="btn btn-sm btn-ghost" aria-label={`Paar ${i + 1} entfernen`} disabled={pairs.length <= 2} onClick={() => set({ pairs: pairs.filter((_, k) => k !== i) })}>
                    <Icon name="trash" />
                  </button>
                </li>
              ))}
            </ul>
            <button type="button" className="btn btn-sm" disabled={pairs.length >= MAX_QUESTION_OPTIONS} onClick={() => set({ pairs: [...pairs, { left: '', right: '' }] })}>
              <Icon name="plus" /> Paar hinzufügen
            </button>
          </fieldset>
        )}

        {q.type === 'numeric' && (
          <div className="ln-three">
            <Field label="Richtige Zahl" htmlFor="qe-value">
              <input id="qe-value" type="text" inputMode="decimal" value={String(q.value ?? '')} onChange={(e) => set({ value: e.target.value })} />
            </Field>
            <Field label="Toleranz (±)" htmlFor="qe-tol" help="Abweichung, die noch als richtig gilt. 0 = genau.">
              <input id="qe-tol" type="text" inputMode="decimal" value={String(q.tolerance ?? '')} onChange={(e) => set({ tolerance: e.target.value })} />
            </Field>
            <Field label="Einheit (Anzeige)" htmlFor="qe-unit">
              <input id="qe-unit" type="text" maxLength={20} value={q.unit ?? ''} onChange={(e) => set({ unit: e.target.value })} />
            </Field>
          </div>
        )}

        <Field label="Rückmeldung zur Frage (optional)" htmlFor="qe-fb">
          <textarea id="qe-fb" rows={2} maxLength={1000} value={q.feedback} onChange={(e) => set({ feedback: e.target.value })} />
        </Field>
        <Field label="Gruppe (optional)" htmlFor="qe-cat" help="Zum Sortieren und für den GIFT-Export, z. B. „Bruchrechnen“.">
          <input id="qe-cat" type="text" maxLength={60} value={q.category} onChange={(e) => set({ category: e.target.value })} />
        </Field>
      </div>
    </Modal>
  );
}

// ------------------------------------------------------------------------------------------ GIFT-Import
function ImportDialog({ channelId, onClose, onDone }: { channelId: number; onClose: () => void; onDone: () => void }) {
  const [text, setText] = useState('');
  const [result, setResult] = useState<{ created: number; errors: string[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  return (
    <Modal
      title="Fragen aus GIFT importieren"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            {result ? 'Schließen' : 'Abbrechen'}
          </button>
          {!result && (
            <AsyncButton
              className="btn btn-primary"
              disabled={!text.trim()}
              onClick={async () => {
                try {
                  const r = await learnApi.importGift(channelId, text);
                  setResult(r);
                  onDone();
                } catch (e) {
                  setError(errorMessage(e));
                }
              }}
            >
              Importieren
            </AsyncButton>
          )}
        </>
      }
    >
      <div className="stack-sm">
        {error && <Alert kind="error">{error}</Alert>}
        {result ? (
          <>
            <Alert kind={result.created ? 'success' : 'warning'}>{result.created} {result.created === 1 ? 'Frage' : 'Fragen'} übernommen.</Alert>
            {result.errors.length > 0 && (
              <ul className="ln-texts">
                {result.errors.map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <>
            <Field label={<>GIFT-Datei <HelpTip>Austauschformat der Moodle-Fragensammlung. Unterstützt: Auswahl, Wahr/Falsch, Kurzantwort (als Lückentext), Zuordnung und Zahl. Aufsätze und Beschreibungstexte werden übersprungen.</HelpTip></>} htmlFor="gift-file">
              <input
                id="gift-file"
                type="file"
                accept=".gift,.txt,text/plain"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (file && file.size < 400_000) setText(await file.text());
                }}
              />
            </Field>
            <Field label="oder Text einfügen" htmlFor="gift-text">
              <textarea id="gift-text" rows={10} className="mono" value={text} onChange={(e) => setText(e.target.value)} />
            </Field>
          </>
        )}
      </div>
    </Modal>
  );
}

// ------------------------------------------------------------------------------------------ Aus anderem Kursraum
function CopyDialog({ channelId, onClose, onDone }: { channelId: number; onClose: () => void; onDone: () => void }) {
  const rooms = useApi(async (signal) => (await channelsApi.list({}, signal)).channels.filter((c) => c.role === 'teacher' && c.id !== channelId), [channelId]);
  const [source, setSource] = useState<number | ''>('');
  const bank = useApi((signal) => learnApi.questions(source as number, signal), [source], { enabled: source !== '' });
  const [picked, setPicked] = useState<number[]>([]);
  const toast = useToast();
  return (
    <Modal
      title="Fragen aus einem anderen Kursraum"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            disabled={!picked.length || source === ''}
            onClick={async () => {
              const r = await learnApi.copyQuestions(channelId, source as number, picked);
              toast.success(`${r.created} ${r.created === 1 ? 'Frage' : 'Fragen'} übernommen`);
              onDone();
              onClose();
            }}
          >
            Übernehmen
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        <Field label="Kursraum" htmlFor="cp-room">
          <select id="cp-room" value={source} onChange={(e) => { setSource(e.target.value ? Number(e.target.value) : ''); setPicked([]); }}>
            <option value="">Bitte wählen …</option>
            {(rooms.data ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.title}
              </option>
            ))}
          </select>
        </Field>
        {bank.loading && source !== '' && <Loading />}
        {bank.data && (bank.data.questions.length === 0 ? <p className="muted">Dort gibt es keine Fragen.</p> : (
          <ul className="ln-pick-list">
            {bank.data.questions.map((qq) => (
              <li key={qq.id}>
                <label className="check">
                  <input type="checkbox" checked={picked.includes(qq.id)} onChange={(e) => setPicked((p) => (e.target.checked ? [...p, qq.id] : p.filter((i) => i !== qq.id)))} />
                  <span>{qq.title}</span> <span className="badge badge-info">{QUESTION_TYPE_LABELS[qq.type]}</span>
                </label>
              </li>
            ))}
          </ul>
        ))}
      </div>
    </Modal>
  );
}

// ------------------------------------------------------------------------------------------ Liste
export default function QuestionsPanel({ channelId }: { channelId: number }) {
  const q = useApi((signal) => learnApi.questions(channelId, signal), [channelId]);
  const [editing, setEditing] = useState<BankQuestion | 'new' | null>(null);
  const [importing, setImporting] = useState(false);
  const [copying, setCopying] = useState(false);
  const [type, setType] = useState<QuestionType | ''>('');
  const [search, setSearch] = useState('');
  const [picked, setPicked] = useState<number[]>([]);
  const toast = useToast();
  if (q.error && !q.data) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  const all = q.data.questions;
  const rows = all.filter((x) => (!type || x.type === type) && (!search.trim() || `${x.title} ${x.category}`.toLowerCase().includes(search.trim().toLowerCase())));

  return (
    <section className="stack" aria-label="Fragensammlung">
      <div className="ln-toolbar">
        <button type="button" className="btn btn-primary" onClick={() => setEditing('new')}>
          <Icon name="plus" /> Neue Frage
        </button>
        <button type="button" className="btn" onClick={() => setImporting(true)}>
          <Icon name="upload" /> GIFT importieren
        </button>
        <button type="button" className="btn" onClick={() => setCopying(true)}>
          <Icon name="copy" /> Aus anderem Kursraum
        </button>
        {all.length > 0 && (
          <a className="btn" href={learnApi.exportGiftUrl(channelId, picked)} download>
            <Icon name="download" /> GIFT exportieren{picked.length ? ` (${picked.length})` : ''}
          </a>
        )}
      </div>
      {all.length > 0 && (
        <div className="ln-filters">
          <Field label="Suche" htmlFor="qb-search">
            <input id="qb-search" type="search" value={search} onChange={(e) => setSearch(e.target.value)} />
          </Field>
          <Field label="Art" htmlFor="qb-type">
            <select id="qb-type" value={type} onChange={(e) => setType(e.target.value as QuestionType | '')}>
              <option value="">Alle</option>
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {QUESTION_TYPE_LABELS[t]}
                </option>
              ))}
            </select>
          </Field>
        </div>
      )}
      {all.length === 0 ? (
        <Empty icon="list" title="Die Fragensammlung ist leer">
          Fragen gehören zum Kursraum und lassen sich in mehreren Selbsttests verwenden.
        </Empty>
      ) : rows.length === 0 ? (
        <p className="muted">Keine Frage passt zum Filter.</p>
      ) : (
        <ul className="ln-bank">
          {rows.map((x) => (
            <li key={x.id} className="ln-bank-row">
              <label className="ln-bank-pick">
                <input type="checkbox" aria-label={`Frage „${x.title}“ zum Exportieren wählen`} checked={picked.includes(x.id)} onChange={(e) => setPicked((p) => (e.target.checked ? [...p, x.id] : p.filter((i) => i !== x.id)))} />
              </label>
              <div className="ln-bank-main">
                <span className="ln-bank-title">{x.title}</span>
                <span className="small muted">
                  {QUESTION_TYPE_LABELS[x.type]} · {numberText(x.points, 2)} {x.points === 1 ? 'Punkt' : 'Punkte'}
                  {x.category ? ` · ${x.category}` : ''}
                  {x.used_in.length ? ` · in ${x.used_in.length} ${x.used_in.length === 1 ? 'Test' : 'Tests'}` : ''}
                </span>
              </div>
              <div className="ln-bank-actions">
                {x.editable && (
                  <>
                    <button type="button" className="btn btn-sm" onClick={() => setEditing(x)}>
                      <Icon name="edit" /> Bearbeiten
                    </button>
                    <AsyncButton
                      className="btn btn-sm btn-ghost"
                      confirm={x.used_in.length ? `Die Frage wird auch aus ${x.used_in.length} Test(s) entfernt. Löschen?` : 'Frage löschen?'}
                      onClick={async () => {
                        await learnApi.deleteQuestion(channelId, x.id);
                        toast.success('Frage gelöscht');
                        q.reload();
                      }}
                    >
                      <Icon name="trash" />
                      <span className="sr-only">Löschen</span>
                    </AsyncButton>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
      {editing && <QuestionEditor channelId={channelId} question={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={q.reload} />}
      {importing && <ImportDialog channelId={channelId} onClose={() => setImporting(false)} onDone={q.reload} />}
      {copying && <CopyDialog channelId={channelId} onClose={() => setCopying(false)} onDone={q.reload} />}
    </section>
  );
}
