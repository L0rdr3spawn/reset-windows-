import { useEffect, useState } from 'react';
import { settleDialog, subscribeDialogs, type DialogRequest } from '../lib/confirm';
import { Modal } from './Modal';

/** Zeichnet die Abfragen aus `lib/confirm.ts` (eine nach der anderen). Einmal in `App.tsx` einhängen. */
export function ConfirmHost() {
  const [queue, setQueue] = useState<DialogRequest[]>([]);
  useEffect(() => subscribeDialogs(setQueue), []);
  const req = queue[0];
  if (!req) return null;
  return req.kind === 'confirm' ? <ConfirmView key={queue.length + req.opts.message} req={req} /> : <PromptView key={queue.length + req.opts.message} req={req} />;
}

function ConfirmView({ req }: { req: Extract<DialogRequest, { kind: 'confirm' }> }) {
  const { title = 'Bitte bestätigen', message, confirmLabel = 'Bestätigen', danger } = req.opts;
  return (
    <Modal
      title={title}
      onClose={() => settleDialog(req, false)}
      footer={
        <>
          <button type="button" className="btn" onClick={() => settleDialog(req, false)}>
            Abbrechen
          </button>
          <button type="button" className={danger ? 'btn btn-danger' : 'btn btn-primary'} onClick={() => settleDialog(req, true)}>
            {confirmLabel}
          </button>
        </>
      }
    >
      <div className="stack">
        {message.split('\n').filter((l) => l.trim()).map((l, i) => (
          <p key={i}>{l}</p>
        ))}
      </div>
    </Modal>
  );
}

function PromptView({ req }: { req: Extract<DialogRequest, { kind: 'prompt' }> }) {
  const { title = 'Eingabe', message, confirmLabel = 'Übernehmen', initial = '', secret } = req.opts;
  const [value, setValue] = useState(initial);
  const submit = () => settleDialog(req, value);
  return (
    <Modal
      title={title}
      onClose={() => settleDialog(req, null)}
      footer={
        <>
          <button type="button" className="btn" onClick={() => settleDialog(req, null)}>
            Abbrechen
          </button>
          <button type="button" className="btn btn-primary" onClick={submit}>
            {confirmLabel}
          </button>
        </>
      }
    >
      <form
        className="field"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <label>
          {message}
          <input type={secret ? 'password' : 'text'} value={value} autoComplete="off" onChange={(e) => setValue(e.target.value)} />
        </label>
      </form>
    </Modal>
  );
}
