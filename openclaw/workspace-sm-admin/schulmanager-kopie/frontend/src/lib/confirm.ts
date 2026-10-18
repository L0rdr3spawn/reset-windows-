/**
 * Bestätigungen im App-Stil statt `window.confirm`/`alert`/`prompt` (Browser-Popups sind nicht gestaltbar und werden
 * in eingebetteten Browsern abgebrochen). `confirmAsk()` bzw. `useConfirm()` liefert ein Promise; gezeichnet wird
 * der Dialog einmal von `<ConfirmHost />` (`components/ConfirmHost.tsx`, in `App.tsx` eingehängt).
 */
import { useCallback } from 'react';

export interface ConfirmOptions {
  /** Überschrift; Standard „Bitte bestätigen“. */
  title?: string;
  /** Text; Zeilenumbrüche erzeugen Absätze. */
  message: string;
  /** Beschriftung der Hauptaktion (Verb), Standard „Bestätigen“. */
  confirmLabel?: string;
  /** Rote Hauptaktion, nur für Löschen/Leeren/Verwerfen. */
  danger?: boolean;
}

export interface PromptOptions {
  title?: string;
  message: string;
  confirmLabel?: string;
  initial?: string;
  /** Eingabe als Passwortfeld. */
  secret?: boolean;
}

export type DialogRequest =
  | { kind: 'confirm'; opts: ConfirmOptions; resolve: (v: boolean) => void }
  | { kind: 'prompt'; opts: PromptOptions; resolve: (v: string | null) => void };

type Listener = (queue: DialogRequest[]) => void;

let queue: DialogRequest[] = [];
const listeners = new Set<Listener>();

function emit() {
  for (const l of listeners) l(queue);
}

export function subscribeDialogs(l: Listener): () => void {
  listeners.add(l);
  l(queue);
  return () => {
    listeners.delete(l);
  };
}

export function settleDialog(req: DialogRequest, value: boolean | string | null): void {
  queue = queue.filter((r) => r !== req);
  if (req.kind === 'confirm') req.resolve(value === true);
  else req.resolve(typeof value === 'string' ? value : null);
  emit();
}

/** Ohne eingehängten `ConfirmHost` (z. B. in Tests ohne App) gilt die Abfrage als abgelehnt. */
function hostMounted(): boolean {
  return listeners.size > 0;
}

export function confirmAsk(opts: ConfirmOptions | string): Promise<boolean> {
  const o = typeof opts === 'string' ? { message: opts } : opts;
  if (!hostMounted()) return Promise.resolve(false);
  return new Promise<boolean>((resolve) => {
    queue = [...queue, { kind: 'confirm', opts: o, resolve }];
    emit();
  });
}

/** Texteingabe im App-Stil; `null` bei Abbruch. */
export function promptAsk(opts: PromptOptions): Promise<string | null> {
  if (!hostMounted()) return Promise.resolve(null);
  return new Promise<string | null>((resolve) => {
    queue = [...queue, { kind: 'prompt', opts, resolve }];
    emit();
  });
}

/** `const ask = useConfirm(); if (!(await ask({ message: '…', danger: true, confirmLabel: 'Löschen' }))) return;` */
export function useConfirm(): (opts: ConfirmOptions | string) => Promise<boolean> {
  return useCallback((opts) => confirmAsk(opts), []);
}

export function usePrompt(): (opts: PromptOptions) => Promise<string | null> {
  return useCallback((opts) => promptAsk(opts), []);
}
