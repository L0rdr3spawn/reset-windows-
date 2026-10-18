/**
 * Hilfe an Beschriftungen (A-60) – reine Zustandslogik ohne DOM, damit sie mit vitest prüfbar ist.
 *
 * Verhalten (siehe docs/DESIGN.md, Abschnitt „Hilfe“):
 * - Maus/Stift: Zeiger ~2 s auf der Beschriftung → Hilfe öffnet („hover“). Verlassen vorher bricht ab.
 *   Offen bleibt sie, solange der Zeiger auf Beschriftung oder Hilfe steht (WCAG 1.4.13), danach kurze Nachlaufzeit.
 * - Rechtsklick auf die Beschriftung → sofort offen und angeheftet („pinned“).
 * - Touch: Antippen der Beschriftung öffnet/schließt (angeheftet); das Feld wird dabei nicht fokussiert.
 * - Tastatur: F1 im beschriebenen Feld bzw. Enter/Leertaste auf einem Hilfe-Knopf → angeheftet; erneut → zu.
 * - Escape oder Klick außerhalb schließt; es ist immer höchstens eine Hilfe offen.
 */

/** Verzögerung bis zur Hover-Hilfe (A-60: „nach ein paar Sekunden (2)“). */
export const HELP_DELAY_MS = 2000;
/** Nachlaufzeit nach Verlassen, damit der Zeiger in die Hilfe wandern kann. */
export const HELP_GRACE_MS = 300;

export type HelpMode = 'closed' | 'pending' | 'hover' | 'pinned';
export type PointerKind = 'mouse' | 'pen' | 'touch' | string;

export interface HelpState {
  mode: HelpMode;
  overTrigger: boolean;
  overPopover: boolean;
}

export type HelpEvent =
  | { type: 'pointerEnter'; pointer: PointerKind }
  | { type: 'pointerLeave' }
  | { type: 'popoverEnter' }
  | { type: 'popoverLeave' }
  | { type: 'delayElapsed' }
  | { type: 'graceElapsed' }
  | { type: 'contextMenu' }
  /** Klick/Tippen: `pointer` aus dem vorangehenden pointerdown */
  | { type: 'activate'; pointer: PointerKind }
  | { type: 'key' }
  | { type: 'escape' }
  | { type: 'outside' }
  | { type: 'close' };

export type TimerCommand = 'startDelay' | 'startGrace' | 'clear' | null;

export interface HelpOptions {
  /**
   * Trigger ist ein Knopf (Hilfe-Knopf): ein Mausklick schaltet um. Bei Beschriftungen (false) bleibt der Mausklick
   * beim Feld (Fokus), er bricht nur eine laufende Wartezeit ab.
   */
  button?: boolean;
}

export const INITIAL_HELP: HelpState = { mode: 'closed', overTrigger: false, overPopover: false };

/**
 * Optionen für einen Namen mit Hilfe (`HelpText`): In einem <label> mit Steuerelement bleibt er Beschriftung (Mausklick
 * fokussiert das Feld). Eigenständig (Überschrift, Kennzahl, Tabellenkopf; role="button") schaltet er wie ein
 * Hilfe-Knopf um – auch beim Klick per Maus, Bildschirmleser oder Tastatur.
 */
export const helpTriggerOptions = (labelsControl: boolean): HelpOptions => ({ button: !labelsControl });

export const isHelpOpen = (mode: HelpMode): boolean => mode === 'hover' || mode === 'pinned';

/** Übergang: neuer Zustand + Timer-Befehl. */
export function helpTransition(s: HelpState, e: HelpEvent, opts: HelpOptions = {}): [HelpState, TimerCommand] {
  switch (e.type) {
    case 'pointerEnter': {
      if (e.pointer === 'touch') return [s, null];
      const next = { ...s, overTrigger: true };
      if (s.mode === 'closed') return [{ ...next, mode: 'pending' }, 'startDelay'];
      if (s.mode === 'hover') return [next, 'clear'];
      return [next, null];
    }
    case 'pointerLeave': {
      const next = { ...s, overTrigger: false };
      if (s.mode === 'pending') return [{ ...next, mode: 'closed' }, 'clear'];
      if (s.mode === 'hover' && !s.overPopover) return [next, 'startGrace'];
      return [next, null];
    }
    case 'popoverEnter': {
      const next = { ...s, overPopover: true };
      return [next, s.mode === 'hover' ? 'clear' : null];
    }
    case 'popoverLeave': {
      const next = { ...s, overPopover: false };
      if (s.mode === 'hover' && !s.overTrigger) return [next, 'startGrace'];
      return [next, null];
    }
    case 'delayElapsed':
      return s.mode === 'pending' ? [{ ...s, mode: 'hover' }, null] : [s, null];
    case 'graceElapsed':
      return s.mode === 'hover' && !s.overTrigger && !s.overPopover ? [{ ...s, mode: 'closed' }, null] : [s, null];
    case 'contextMenu':
      return [{ ...s, mode: 'pinned' }, 'clear'];
    case 'activate': {
      const touch = e.pointer === 'touch';
      if (touch || opts.button) {
        // Antippen bzw. Hilfe-Knopf: angeheftet ↔ zu (eine per Hover offene Hilfe wird angeheftet)
        if (s.mode === 'pinned') return [{ ...s, mode: 'closed' }, 'clear'];
        return [{ ...s, mode: 'pinned' }, 'clear'];
      }
      // Mausklick auf eine Beschriftung: Fokus ins Feld, nur die Wartezeit abbrechen
      if (s.mode === 'pending') return [{ ...s, mode: 'closed' }, 'clear'];
      return [s, null];
    }
    case 'key':
      return s.mode === 'pinned' ? [{ ...s, mode: 'closed' }, 'clear'] : [{ ...s, mode: 'pinned' }, 'clear'];
    case 'escape':
    case 'close':
      return s.mode === 'closed' ? [s, null] : [{ ...s, mode: 'closed' }, 'clear'];
    case 'outside':
      return isHelpOpen(s.mode) ? [{ ...s, mode: 'closed' }, 'clear'] : [s, null];
    default:
      return [s, null];
  }
}

export interface TimerApi {
  set: (fn: () => void, ms: number) => unknown;
  clear: (handle: unknown) => void;
}

const defaultTimers: TimerApi = {
  set: (fn, ms) => setTimeout(fn, ms),
  clear: (h) => clearTimeout(h as ReturnType<typeof setTimeout>),
};

export interface HelpController {
  send: (e: HelpEvent) => void;
  readonly state: HelpState;
  dispose: () => void;
}

/** Steuert Zustand und Timer; `onChange` meldet jeden Moduswechsel. */
export function createHelpController(
  onChange: (mode: HelpMode) => void,
  opts: HelpOptions & { delay?: number; grace?: number; timers?: TimerApi } = {},
): HelpController {
  const timers = opts.timers ?? defaultTimers;
  const delay = opts.delay ?? HELP_DELAY_MS;
  const grace = opts.grace ?? HELP_GRACE_MS;
  let state = INITIAL_HELP;
  let handle: unknown = null;
  const clear = () => {
    if (handle !== null) timers.clear(handle);
    handle = null;
  };
  const send = (e: HelpEvent) => {
    const [next, cmd] = helpTransition(state, e, opts);
    if (cmd === 'clear' || cmd === 'startDelay' || cmd === 'startGrace') clear();
    if (cmd === 'startDelay') handle = timers.set(() => ((handle = null), send({ type: 'delayElapsed' })), delay);
    if (cmd === 'startGrace') handle = timers.set(() => ((handle = null), send({ type: 'graceElapsed' })), grace);
    const changed = next.mode !== state.mode;
    state = next;
    if (changed) {
      if (isHelpOpen(next.mode)) claimActive(controller);
      else releaseActive(controller);
      onChange(next.mode);
    }
  };
  const controller: HelpController = {
    send,
    get state() {
      return state;
    },
    dispose: () => {
      clear();
      releaseActive(controller);
    },
  };
  return controller;
}

// ------------------------------------------------------------ höchstens eine offene Hilfe

let active: HelpController | null = null;

function claimActive(c: HelpController): void {
  if (active && active !== c) {
    const prev = active;
    active = c;
    prev.send({ type: 'close' });
  }
  active = c;
}

function releaseActive(c: HelpController): void {
  if (active === c) active = null;
}

/** Nur für Tests: offene Hilfe vergessen. */
export function resetActiveHelp(): void {
  active = null;
}

// ------------------------------------------------------------ Tastatur (F1 im beschriebenen Feld)

const keyTargets = new Map<string, () => void>();

/** Registriert eine Hilfe unter der id ihres Beschreibungstexts (aria-describedby). */
export function registerHelpKey(descId: string, open: () => void): () => void {
  keyTargets.set(descId, open);
  return () => {
    if (keyTargets.get(descId) === open) keyTargets.delete(descId);
  };
}

/**
 * Taste, die die Hilfe zum fokussierten Element öffnet: F1 immer, „?“ (Umschalt+ß) nur außerhalb von Texteingaben
 * (`typing` = Fokus in Textfeld/Textbereich, dort bleibt „?“ ein Zeichen).
 */
export const isHelpKey = (e: { key: string; altKey?: boolean; ctrlKey?: boolean; metaKey?: boolean }, typing = false): boolean => {
  if (e.altKey || e.ctrlKey || e.metaKey) return false;
  return e.key === 'F1' || (e.key === '?' && !typing);
};

const TEXT_TYPES = new Set(['', 'text', 'search', 'password', 'email', 'number', 'url', 'tel', 'date', 'time', 'datetime-local', 'month', 'week']);

/** Fokus liegt in einer Texteingabe (dort ist „?“ ein Zeichen, keine Hilfetaste). */
export function isTypingTarget(el: { tagName?: string; type?: string; isContentEditable?: boolean } | null | undefined): boolean {
  if (!el) return false;
  const tag = (el.tagName ?? '').toUpperCase();
  if (tag === 'TEXTAREA' || el.isContentEditable) return true;
  return tag === 'INPUT' && TEXT_TYPES.has((el.type ?? '').toLowerCase());
}

// ------------------------------------------------------------ Einstellung „Hilfetexte immer anzeigen“ (Benutzermenü)

const INLINE_KEY = 'sm-help-inline';
let inlineHelp: boolean | null = null;
const inlineListeners = new Set<() => void>();

export function getHelpInline(): boolean {
  if (inlineHelp === null) {
    try {
      inlineHelp = typeof localStorage !== 'undefined' && localStorage.getItem(INLINE_KEY) === '1';
    } catch {
      inlineHelp = false;
    }
  }
  return inlineHelp;
}

export function setHelpInline(on: boolean): void {
  inlineHelp = on;
  try {
    if (typeof localStorage !== 'undefined') {
      if (on) localStorage.setItem(INLINE_KEY, '1');
      else localStorage.removeItem(INLINE_KEY);
    }
  } catch {
    /* Speicher nicht verfügbar – gilt dann nur für diese Sitzung */
  }
  inlineListeners.forEach((fn) => fn());
}

export function subscribeHelpInline(fn: () => void): () => void {
  inlineListeners.add(fn);
  return () => inlineListeners.delete(fn);
}

/** Öffnet die Hilfe, auf die `aria-describedby` des Elements zeigt; true, wenn eine gefunden wurde. */
export function openHelpFor(describedBy: string | null | undefined): boolean {
  for (const id of (describedBy ?? '').split(/\s+/)) {
    const open = id ? keyTargets.get(id) : undefined;
    if (open) {
      open();
      return true;
    }
  }
  return false;
}

/** Fügt ids zu einer aria-describedby-Liste hinzu (ohne Doppelte). */
export function addTokens(list: string | null, ids: readonly string[]): string {
  const have = (list ?? '').split(/\s+/).filter(Boolean);
  for (const id of ids) if (id && !have.includes(id)) have.push(id);
  return have.join(' ');
}

/** Entfernt ids aus einer aria-describedby-Liste. */
export function removeTokens(list: string | null, ids: readonly string[]): string {
  return (list ?? '')
    .split(/\s+/)
    .filter((t) => t && !ids.includes(t))
    .join(' ');
}

/** Position der Hilfe: unter dem Auslöser, sonst darüber; immer im sichtbaren Bereich. */
export function placeHelp(
  trigger: { left: number; top: number; bottom: number },
  pop: { width: number; height: number },
  view: { width: number; height: number },
  gap = 6,
  margin = 8,
): { left: number; top: number; above: boolean } {
  const left = Math.max(margin, Math.min(trigger.left, view.width - pop.width - margin));
  const below = trigger.bottom + gap;
  if (below + pop.height <= view.height - margin || trigger.top - gap - pop.height < margin) {
    return { left, top: Math.max(margin, Math.min(below, view.height - pop.height - margin)), above: false };
  }
  return { left, top: trigger.top - gap - pop.height, above: true };
}
