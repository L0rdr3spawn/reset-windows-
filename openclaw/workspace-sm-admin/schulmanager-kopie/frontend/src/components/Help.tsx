/**
 * Hilfe an Beschriftungen (A-59/A-60) – ersetzt dauerhaft sichtbare Erklärtexte.
 *
 * - `useHelp(inhalt)`: Grundbaustein (Auslöser-Props, versteckter Beschreibungstext für aria-describedby, Popover).
 * Überall dasselbe Zeichen: ein kleines (i) im Kreis neben der Sache; Klick/Antippen zeigt die Erklärung.
 * - `<HelpText help="…">Name</HelpText>`: Name mit (i); in einem <label> wird das zugehörige Feld
 *   automatisch per aria-describedby verknüpft, sonst ist der Name selbst per Tab erreichbar.
 * - `<PageHelp label="Hilfe zu …">…</PageHelp>` (bzw. `HelpTip`): (i)-Knopf für Seiten- und Abschnittsüberschriften,
 *   Knöpfe und Kennzahlen (statt erklärender Absätze).
 * - `Field` (components/ui.tsx) zeigt für `help` bzw. `hint` ein (i)-Knopf (`HelpButton`) neben der Beschriftung.
 *
 * Bedienung: Klick/Antippen auf das (i) (Tastatur: Enter/Leertaste), Maus ~2 s auf dem Namen, Rechtsklick, F1 im Feld;
 * Escape oder Klick außerhalb schließt. Logik und Tests: lib/help.ts, lib/__tests__/help.test.ts.
 */
import {
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';
import {
  addTokens,
  createHelpController,
  getHelpInline,
  helpTriggerOptions,
  isHelpKey,
  isHelpOpen,
  isTypingTarget,
  openHelpFor,
  placeHelp,
  registerHelpKey,
  removeTokens,
  subscribeHelpInline,
  type HelpMode,
} from '../lib/help';
import { Icon } from './Icon';

let keyListenerInstalled = false;

/** Ein globaler Tastatur-Listener: F1 (bzw. „?“ außerhalb von Texteingaben) öffnet die Hilfe des fokussierten Elements. */
function ensureKeyListener(): void {
  if (keyListenerInstalled || typeof window === 'undefined') return;
  keyListenerInstalled = true;
  window.addEventListener('keydown', (e) => {
    const el = document.activeElement;
    if (!(el instanceof HTMLElement) || !isHelpKey(e, isTypingTarget(el))) return;
    if (openHelpFor(el.getAttribute('aria-describedby'))) e.preventDefault();
  });
}

/** Einstellung „Hilfetexte immer anzeigen“ (Benutzermenü; lib/help.ts setHelpInline). */
export function useHelpInline(): boolean {
  return useSyncExternalStore(subscribeHelpInline, getHelpInline, () => false);
}

const hasContent = (c: ReactNode): boolean => c !== undefined && c !== null && c !== false && c !== '';

export interface HelpHandle {
  /** Hilfe vorhanden (Inhalt nicht leer) */
  enabled: boolean;
  open: boolean;
  mode: HelpMode;
  /** id des versteckten Beschreibungstexts – für aria-describedby */
  descId: string;
  ref: (el: HTMLElement | null) => void;
  /** Props für den Auslöser (Name bzw. Knopf) */
  triggerProps: {
    onPointerEnter: (e: ReactPointerEvent<HTMLElement>) => void;
    onPointerLeave: () => void;
    onPointerDown: (e: ReactPointerEvent<HTMLElement>) => void;
    onContextMenu: (e: ReactMouseEvent<HTMLElement>) => void;
    onClick: (e: ReactMouseEvent<HTMLElement>) => void;
  };
  /** per Tastatur umschalten (Enter/Leertaste auf einem fokussierbaren Auslöser) */
  toggle: () => void;
  /** Versteckter Beschreibungstext (immer rendern, nicht in einem Knopf) */
  description: ReactNode;
  /** Popover (Portal, nur wenn offen) */
  popover: ReactNode;
}

export function useHelp(content: ReactNode, opts: { button?: boolean } = {}): HelpHandle {
  const enabled = hasContent(content);
  const button = !!opts.button;
  const uid = useId();
  const descId = `${uid}help`;
  const popId = `${uid}pop`;
  const triggerEl = useRef<HTMLElement | null>(null);
  const popEl = useRef<HTMLDivElement | null>(null);
  const lastPointer = useRef<string>('');
  const [mode, setMode] = useState<HelpMode>('closed');
  const ctrl = useMemo(() => createHelpController(setMode, { button }), [button]);
  const open = enabled && isHelpOpen(mode);

  useEffect(() => () => ctrl.dispose(), [ctrl]);

  useEffect(() => {
    if (!enabled) return undefined;
    ensureKeyListener();
    return registerHelpKey(descId, () => ctrl.send({ type: 'key' }));
  }, [enabled, descId, ctrl]);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      // erst die Hilfe schließen, nicht zugleich einen Dialog darunter
      e.stopPropagation();
      ctrl.send({ type: 'escape' });
    };
    const onDown = (e: PointerEvent) => {
      const t = e.target as Node | null;
      if (t && (triggerEl.current?.contains(t) || popEl.current?.contains(t))) return;
      ctrl.send({ type: 'outside' });
    };
    window.addEventListener('keydown', onKey, true);
    document.addEventListener('pointerdown', onDown, true);
    return () => {
      window.removeEventListener('keydown', onKey, true);
      document.removeEventListener('pointerdown', onDown, true);
    };
  }, [open, ctrl]);

  const triggerProps: HelpHandle['triggerProps'] = {
    onPointerEnter: (e) => {
      if (enabled) ctrl.send({ type: 'pointerEnter', pointer: e.pointerType });
    },
    onPointerLeave: () => {
      if (enabled) ctrl.send({ type: 'pointerLeave' });
    },
    onPointerDown: (e) => {
      lastPointer.current = e.pointerType;
    },
    onContextMenu: (e) => {
      if (!enabled) return;
      e.preventDefault();
      ctrl.send({ type: 'contextMenu' });
    },
    onClick: (e) => {
      if (!enabled) return;
      const pointer = lastPointer.current;
      lastPointer.current = '';
      // Antippen des Namens zeigt die Hilfe – das Feld wird dabei nicht fokussiert (keine Bildschirmtastatur)
      if (pointer === 'touch' && !button) e.preventDefault();
      ctrl.send({ type: 'activate', pointer });
    },
  };

  return {
    enabled,
    open,
    mode,
    descId,
    ref: (el) => {
      triggerEl.current = el;
    },
    triggerProps,
    toggle: () => ctrl.send({ type: 'key' }),
    description: enabled ? (
      <span id={descId} hidden>
        {content}
      </span>
    ) : null,
    popover: open ? (
      <HelpPopover
        id={popId}
        anchor={triggerEl}
        popRef={popEl}
        pinned={mode === 'pinned'}
        onEnter={() => ctrl.send({ type: 'popoverEnter' })}
        onLeave={() => ctrl.send({ type: 'popoverLeave' })}
      >
        {content}
      </HelpPopover>
    ) : null,
  };
}

function HelpPopover({
  id,
  anchor,
  popRef,
  pinned,
  onEnter,
  onLeave,
  children,
}: {
  id: string;
  anchor: { current: HTMLElement | null };
  popRef: { current: HTMLDivElement | null };
  pinned: boolean;
  onEnter: () => void;
  onLeave: () => void;
  children: ReactNode;
}) {
  const [pos, setPos] = useState<{ left: number; top: number } | null>(null);
  useLayoutEffect(() => {
    const update = () => {
      const a = anchor.current;
      const p = popRef.current;
      if (!a || !p) return;
      const r = a.getBoundingClientRect();
      const { width, height } = p.getBoundingClientRect();
      const next = placeHelp(r, { width, height }, { width: document.documentElement.clientWidth, height: window.innerHeight });
      setPos((prev) => (prev && prev.left === next.left && prev.top === next.top ? prev : { left: next.left, top: next.top }));
    };
    update();
    window.addEventListener('scroll', update, true);
    window.addEventListener('resize', update);
    return () => {
      window.removeEventListener('scroll', update, true);
      window.removeEventListener('resize', update);
    };
  }, [anchor, popRef]);
  return createPortal(
    <div
      ref={popRef}
      id={id}
      role="tooltip"
      className={`help-pop${pinned ? ' pinned' : ''}`}
      style={{ left: pos?.left ?? 0, top: pos?.top ?? 0, visibility: pos ? undefined : 'hidden' }}
      onPointerEnter={onEnter}
      onPointerLeave={onLeave}
    >
      {children}
    </div>,
    document.body,
  );
}

/** Verknüpft ids per aria-describedby mit einem Element (das Element liefert `target` nach dem Rendern). */
export function useDescribedBy(target: () => Element | null | undefined, ids: readonly (string | false | null | undefined)[]): void {
  const list = ids.filter((x): x is string => !!x);
  const key = list.join(' ');
  // ohne Abhängigkeiten: das Feld kann neu gerendert oder ausgetauscht werden, die Verknüpfung bleibt aktuell
  useLayoutEffect(() => {
    const el = target();
    if (!el || !key) return undefined;
    const ids2 = key.split(' ');
    el.setAttribute('aria-describedby', addTokens(el.getAttribute('aria-describedby'), ids2));
    return () => {
      const rest = removeTokens(el.getAttribute('aria-describedby'), ids2);
      if (rest) el.setAttribute('aria-describedby', rest);
      else el.removeAttribute('aria-describedby');
    };
  });
}

/**
 * Name mit Hilfe (gepunktet unterstrichen). In einem <label> beschreibt die Hilfe das zugehörige Feld; außerhalb
 * (Überschrift, Tabellenkopf) ist der Name selbst fokussierbar (Enter/F1 öffnet).
 */
export function HelpText({ help, children, className }: { help?: ReactNode; children: ReactNode; className?: string }) {
  const el = useRef<HTMLElement | null>(null);
  const [standalone, setStandalone] = useState(false);
  // eigenständig = Knopf: Klick (Maus, Bildschirmleser) schaltet um; im <label> bleibt der Klick beim Feld
  const h = useHelp(help, helpTriggerOptions(!standalone));
  useDescribedBy(() => (el.current?.closest('label') as HTMLLabelElement | null)?.control ?? null, [h.enabled && h.descId]);
  useLayoutEffect(() => {
    if (!h.enabled) return;
    const own = !(el.current?.closest('label') as HTMLLabelElement | null)?.control;
    if (own !== standalone) setStandalone(own);
  });
  if (!h.enabled) return <>{children}</>;
  const onKeyDown = (e: ReactKeyboardEvent<HTMLElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      h.toggle();
    }
  };
  return (
    <>
      <span
        ref={(node) => {
          el.current = node;
          h.ref(node);
        }}
        className={`help-trigger${className ? ` ${className}` : ''}`}
        tabIndex={standalone ? 0 : undefined}
        role={standalone ? 'button' : undefined}
        aria-expanded={standalone ? h.open : undefined}
        aria-describedby={standalone ? h.descId : undefined}
        onKeyDown={standalone ? onKeyDown : undefined}
        {...h.triggerProps}
      >
        {children}
        {/* das (i): auch im <label> per Mausklick bedienbar, ohne das Feld zu fokussieren */}
        <span
          className="help-i"
          aria-hidden="true"
          onClick={
            standalone
              ? undefined
              : (e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  h.toggle();
                }
          }
        >
          <Icon name="info" />
        </span>
      </span>
      {h.description}
      {h.popover}
    </>
  );
}

/** Das (i) als Knopf – Auslöser einer Hilfe (`useHelp(…, { button: true })`); gerendert wird nur bei vorhandenem Inhalt. */
export function HelpButton({ h, label = 'Hilfe' }: { h: HelpHandle; label?: string }) {
  if (!h.enabled) return null;
  return (
    <>
      <button type="button" ref={h.ref} className="help-btn" aria-label={label} aria-expanded={h.open} aria-describedby={h.descId} {...h.triggerProps}>
        <Icon name="info" />
      </button>
      {h.description}
      {h.popover}
    </>
  );
}

/** Dezenter Hilfe-Knopf (Info-Zeichen) für Seiten- und Abschnittsüberschriften – statt erklärender Absätze. */
export function PageHelp({ children, label = 'Hilfe' }: { children: ReactNode; label?: string }) {
  const h = useHelp(children, { button: true });
  return <HelpButton h={h} label={label} />;
}
