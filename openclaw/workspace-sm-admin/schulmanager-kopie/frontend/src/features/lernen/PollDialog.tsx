/** Neue Abstimmung anlegen (Kursraum und Chat): Frage, Antworten, Einstellungen. */
import { useState } from 'react';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, Field } from '../../components/ui';
import { fromLocalInput, toLocalInput } from '../channels/logic';
import type { PollInput, PollResults } from './api';
import { cleanOptions, emptyPoll, MAX_POLL_OPTIONS, POLL_RESULT_LABELS, pollError } from './logic';
import './lernen.css';

export function PollDialog({ title = 'Neue Abstimmung', onClose, onSubmit, submitLabel = 'Abstimmung starten' }: {
  title?: string;
  onClose: () => void;
  onSubmit: (poll: PollInput) => Promise<unknown>;
  submitLabel?: string;
}) {
  const [poll, setPoll] = useState<PollInput>(emptyPoll);
  const [ends, setEnds] = useState('');
  const [error, setError] = useState<string | null>(null);
  const set = (patch: Partial<PollInput>) => setPoll((p) => ({ ...p, ...patch }));
  const options = poll.options;
  const filled = cleanOptions(options).length;

  const build = (): PollInput => ({
    ...poll,
    question: poll.question.trim(),
    options: cleanOptions(options),
    max_choices: poll.multiple && poll.max_choices && poll.max_choices < filled ? poll.max_choices : null,
    ends_at: fromLocalInput(ends),
  });

  return (
    <Modal
      title={title}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            onClick={async () => {
              const input = build();
              const problem = pollError(input);
              if (problem) {
                setError(problem);
                return;
              }
              try {
                await onSubmit(input);
                onClose();
              } catch (e) {
                setError(errorMessage(e));
              }
            }}
          >
            {submitLabel}
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        {error && <Alert kind="error">{error}</Alert>}
        <Field label="Frage" htmlFor="ln-poll-q">
          <input id="ln-poll-q" type="text" maxLength={300} value={poll.question} onChange={(e) => set({ question: e.target.value })} />
        </Field>
        <fieldset className="ln-fieldset">
          <legend>Antworten</legend>
          <ul className="ln-edit-list">
            {options.map((o, i) => (
              <li key={i} className="ln-edit-row">
                <input type="text" aria-label={`Antwort ${i + 1}`} maxLength={200} value={o} onChange={(e) => set({ options: options.map((x, k) => (k === i ? e.target.value : x)) })} />
                <button type="button" className="btn btn-sm btn-ghost" aria-label={`Antwort ${i + 1} entfernen`} disabled={options.length <= 2} onClick={() => set({ options: options.filter((_, k) => k !== i) })}>
                  <Icon name="trash" />
                </button>
              </li>
            ))}
          </ul>
          <button type="button" className="btn btn-sm" disabled={options.length >= MAX_POLL_OPTIONS} onClick={() => set({ options: [...options, ''] })}>
            <Icon name="plus" /> Antwort hinzufügen
          </button>
        </fieldset>
        <div className="ln-two">
          <label className="check">
            <input type="checkbox" checked={poll.multiple} onChange={(e) => set({ multiple: e.target.checked, max_choices: null })} /> Mehrere Antworten erlaubt
          </label>
          <label className="check">
            <input type="checkbox" checked={poll.anonymous} onChange={(e) => set({ anonymous: e.target.checked })} /> Anonym abstimmen
            <HelpTip>Es wird nur gespeichert, dass jemand abgestimmt hat – nicht, wer was gewählt hat. Anonyme Stimmen lassen sich nicht ändern.</HelpTip>
          </label>
        </div>
        {poll.multiple && (
          <Field label="Höchstens so viele Antworten (leer = alle)" htmlFor="ln-poll-max">
            <input id="ln-poll-max" type="number" min={1} max={Math.max(filled, 1)} value={poll.max_choices ?? ''} onChange={(e) => set({ max_choices: e.target.value === '' ? null : Number(e.target.value) })} />
          </Field>
        )}
        <Field label="Ergebnis sichtbar" htmlFor="ln-poll-res" help="Wer das Ergebnis wann sehen darf. Wer die Abstimmung gestellt hat, sieht es immer.">
          <select id="ln-poll-res" value={poll.results} onChange={(e) => set({ results: e.target.value as PollResults })}>
            {(Object.keys(POLL_RESULT_LABELS) as PollResults[]).map((k) => (
              <option key={k} value={k}>
                {POLL_RESULT_LABELS[k]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Ende (optional)" htmlFor="ln-poll-end">
          <input id="ln-poll-end" type="datetime-local" value={ends} min={toLocalInput(new Date().toISOString())} onChange={(e) => setEnds(e.target.value)} />
        </Field>
      </div>
    </Modal>
  );
}

export default PollDialog;
