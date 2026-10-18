/**
 * Kürzel mit Sprechblase – überall, wo ein Kürzel steht (Lehrkraft, Fach, Raum, Klasse, Standort …).
 *
 * - `<Abbr text="MÜL" full="Frau Müller · Deutsch">`: Grundbaustein. Blase bei Maus-Hover, Tastaturfokus und Antippen.
 * - `<TeacherAbbr id>`, `<SubjectAbbr id>`, `<RoomAbbr id>`, `<ClassAbbr id>`, `<SiteAbbr id>`: lösen die volle
 *   Bezeichnung aus den Stammdaten auf (hooks/useCollection.ts, lib/abbr.ts). Unbekannt oder nicht lesbar → Kürzel ohne Blase.
 * - `<AbbrList kind ids>`: mehrere Kürzel mit Komma, z. B. die Lehrkräfte einer Stunde.
 * - `<AbbrNamesProvider names>`: Seiten ohne Zugriff auf die Stammdaten (Schüler/Eltern) liefern die Namen selbst
 *   (z. B. `names` der Kalenderwoche); sie haben Vorrang vor den Stammdaten.
 *
 * Bedienung: Maus – Darüberfahren; Tastatur – Tab (fokussierbar), Enter heftet an, Escape schließt; Touch – Antippen
 * öffnet, Antippen daneben oder Escape schließt. `passive` (Kürzel in einem Knopf/Link/Rasterfeld, dessen Antippen etwas
 * anderes tut): kein eigener Tabstopp, Touch öffnet per Langdruck; ein normales Antippen geht an das Feld durch.
 * Es ist höchstens eine Blase offen. Logik und Tests: lib/abbr.ts, lib/__tests__/abbr.test.ts.
 */
import {
  Fragment,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';
import { useIndex } from '../hooks/useCollection';
import {
  ABBR_CLOSE_MS,
  ABBR_LONG_PRESS_MS,
  ABBR_MOVE_TOLERANCE,
  ABBR_OPEN_MS,
  INITIAL_ABBR,
  abbrReduce,
  classText,
  isAbbrOpen,
  roomText,
  siteText,
  splitIds,
  subjectText,
  teacherText,
  type AbbrKind,
} from '../lib/abbr';
import { placeHelp } from '../lib/help';

// ---------------------------------------------------------------- Namen von der Seite

export type AbbrNames = Partial<Record<AbbrKind, Record<string, string>>>;

const NamesContext = createContext<AbbrNames | null>(null);

export function AbbrNamesProvider({ names, children }: { names: AbbrNames | null | undefined; children: ReactNode }) {
  const parent = useContext(NamesContext);
  const merged = useMemo(() => {
    if (!names) return parent;
    if (!parent) return names;
    const out: AbbrNames = { ...parent };
    for (const k of Object.keys(names) as AbbrKind[]) out[k] = { ...parent[k], ...names[k] };
    return out;
  }, [names, parent]);
  return <NamesContext.Provider value={merged}>{children}</NamesContext.Provider>;
}

// ---------------------------------------------------------------- Grundbaustein

/** Schließt die zuvor geöffnete Blase, sobald eine andere aufgeht (höchstens eine offen). */
let closeActive: (() => void) | null = null;

export interface AbbrProps {
  /** angezeigtes Kürzel (Standard: Inhalt) */
  text?: ReactNode;
  /** volle Bezeichnung; leer = keine Blase */
  full?: ReactNode;
  /** Kürzel in Knopf/Link/Rasterfeld: nicht fokussierbar, Touch nur per Langdruck */
  passive?: boolean;
  className?: string;
  children?: ReactNode;
}

export function Abbr({ text, full, passive, className, children }: AbbrProps) {
  const enabled = full !== undefined && full !== null && full !== false && full !== '';
  const shown = children ?? text;
  if (!enabled) return className ? <span className={className}>{shown}</span> : <>{shown}</>;
  return (
    <AbbrBubble full={full} passive={!!passive} className={className}>
      {shown}
    </AbbrBubble>
  );
}

function AbbrBubble({ full, passive, className, children }: { full: ReactNode; passive: boolean; className?: string; children: ReactNode }) {
  const uid = useId();
  const popId = `${uid}abbr`;
  const [state, send] = useReducer(abbrReduce, INITIAL_ABBR);
  const open = isAbbrOpen(state);
  const triggerEl = useRef<HTMLSpanElement | null>(null);
  const popEl = useRef<HTMLDivElement | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const press = useRef<{ timer: ReturnType<typeof setTimeout>; x: number; y: number } | null>(null);
  const lastPointer = useRef('');
  const suppressClick = useRef(false);

  const clearTimer = () => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
  };
  const clearPress = () => {
    if (press.current) clearTimeout(press.current.timer);
    press.current = null;
  };
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
      if (press.current) clearTimeout(press.current.timer);
    },
    [],
  );

  const close = useCallback(() => send({ type: 'outside' }), []);
  useEffect(() => {
    if (!open) return undefined;
    if (closeActive && closeActive !== close) closeActive();
    closeActive = close;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      e.stopPropagation(); // erst die Blase schließen, nicht zugleich einen Dialog darunter
      send({ type: 'escape' });
    };
    const onDown = (e: PointerEvent) => {
      const t = e.target as Node | null;
      if (t && (triggerEl.current?.contains(t) || popEl.current?.contains(t))) return;
      send({ type: 'outside' });
    };
    window.addEventListener('keydown', onKey, true);
    document.addEventListener('pointerdown', onDown, true);
    return () => {
      window.removeEventListener('keydown', onKey, true);
      document.removeEventListener('pointerdown', onDown, true);
      if (closeActive === close) closeActive = null;
    };
  }, [open, close]);

  const enter = (e: ReactPointerEvent) => {
    if (e.pointerType === 'touch') return;
    clearTimer();
    if (state.hover) return;
    timer.current = setTimeout(() => send({ type: 'enter' }), ABBR_OPEN_MS);
  };
  const leave = () => {
    clearTimer();
    if (!state.hover) return;
    timer.current = setTimeout(() => send({ type: 'leave' }), ABBR_CLOSE_MS);
  };
  const pinNow = () => {
    clearTimer();
    send({ type: 'pin' });
  };

  return (
    <>
      <span
        ref={triggerEl}
        className={`abbr${passive ? ' abbr-passive' : ''}${className ? ` ${className}` : ''}`}
        tabIndex={passive ? undefined : 0}
        aria-describedby={passive ? undefined : popId}
        onPointerEnter={enter}
        onPointerLeave={leave}
        onPointerDown={(e) => {
          lastPointer.current = e.pointerType;
          if (passive && e.pointerType === 'touch') {
            clearPress();
            press.current = {
              x: e.clientX,
              y: e.clientY,
              timer: setTimeout(() => {
                press.current = null;
                suppressClick.current = true;
                pinNow();
              }, ABBR_LONG_PRESS_MS),
            };
          }
        }}
        onPointerMove={(e) => {
          const p = press.current;
          if (p && Math.hypot(e.clientX - p.x, e.clientY - p.y) > ABBR_MOVE_TOLERANCE) clearPress();
        }}
        onPointerUp={clearPress}
        onPointerCancel={clearPress}
        onContextMenu={(e: ReactMouseEvent) => {
          // Langdruck am Touch-Gerät löst oft das Kontextmenü aus: stattdessen die Blase zeigen
          if (lastPointer.current !== 'touch') return;
          e.preventDefault();
          if (passive) {
            clearPress();
            suppressClick.current = true;
            pinNow();
          }
        }}
        onClickCapture={(e: ReactMouseEvent) => {
          // der Klick nach einem Langdruck soll nicht zusätzlich das Rasterfeld auswählen
          if (suppressClick.current) {
            suppressClick.current = false;
            e.preventDefault();
            e.stopPropagation();
          }
        }}
        onClick={(e: ReactMouseEvent) => {
          if (passive) return;
          // Antippen (Touch) öffnet bzw. schließt, ohne eine Zeile/Karte dahinter auszulösen; Mausklick heftet an
          if (lastPointer.current === 'touch') e.stopPropagation();
          clearTimer();
          send({ type: 'toggle' });
        }}
        onKeyDown={(e: ReactKeyboardEvent) => {
          if (passive) return;
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            send({ type: 'toggle' });
          }
        }}
        onFocus={() => {
          if (!passive) send({ type: 'focus' });
        }}
        onBlur={() => {
          if (!passive) send({ type: 'blur' });
        }}
      >
        {children}
      </span>
      {passive ? null : (
        <span id={popId} hidden>
          {full}
        </span>
      )}
      {open ? (
        <AbbrPopover
          anchor={triggerEl}
          popRef={popEl}
          pinned={state.pinned}
          onEnter={() => {
            clearTimer();
            send({ type: 'enter' });
          }}
          onLeave={leave}
        >
          {full}
        </AbbrPopover>
      ) : null}
    </>
  );
}

function AbbrPopover({
  anchor,
  popRef,
  pinned,
  onEnter,
  onLeave,
  children,
}: {
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
      // bevorzugt oberhalb des Kürzels (der Finger verdeckt sonst die Blase), sonst darunter
      const view = { width: document.documentElement.clientWidth, height: window.innerHeight };
      const above = r.top - 6 - height >= 8;
      const next = above ? { left: Math.max(8, Math.min(r.left, view.width - width - 8)), top: r.top - 6 - height } : placeHelp(r, { width, height }, view);
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
      role="tooltip"
      className={`help-pop abbr-pop${pinned ? ' pinned' : ''}`}
      style={{ left: pos?.left ?? 0, top: pos?.top ?? 0, visibility: pos ? undefined : 'hidden' }}
      onPointerEnter={onEnter}
      onPointerLeave={onLeave}
    >
      {children}
    </div>,
    document.body,
  );
}

// ---------------------------------------------------------------- aufgelöste Kürzel

interface KindProps {
  id: string | null | undefined;
  /** angezeigter Text, wenn er vom Kürzel abweicht (Standard: die id) */
  children?: ReactNode;
  passive?: boolean;
  className?: string;
  /** Rückfall, wenn die Stammdaten nichts liefern (z. B. Fachname aus der Stundenplanzelle) */
  fallback?: string;
}

function useOverride(kind: AbbrKind, id: string | null | undefined): string {
  const names = useContext(NamesContext);
  return (id && names?.[kind]?.[id]) || '';
}

function Resolved({ id, children, passive, className, full }: KindProps & { full: string }) {
  if (!id) return children ? <>{children}</> : null;
  return (
    <Abbr full={full || undefined} passive={passive} className={className}>
      {children ?? id}
    </Abbr>
  );
}

export function TeacherAbbr(props: KindProps) {
  const teachers = useIndex('teachers');
  const subjects = useIndex('subjects');
  const over = useOverride('teacher', props.id);
  const full = over || (props.id ? teacherText(teachers.get(props.id), props.id, subjects) : '') || props.fallback || '';
  return <Resolved {...props} full={full} />;
}

export function SubjectAbbr(props: KindProps) {
  const subjects = useIndex('subjects');
  const over = useOverride('subject', props.id);
  const full = over || (props.id ? subjectText(subjects.get(props.id), props.id) : '') || props.fallback || '';
  return <Resolved {...props} full={full} />;
}

export function RoomAbbr(props: KindProps) {
  const rooms = useIndex('rooms');
  const sites = useIndex('sites');
  const over = useOverride('room', props.id);
  const full = over || (props.id ? roomText(rooms.get(props.id), props.id, sites) : '') || props.fallback || '';
  return <Resolved {...props} full={full} />;
}

export function ClassAbbr(props: KindProps) {
  const classes = useIndex('classes');
  const teachers = useIndex('teachers');
  const over = useOverride('class', props.id);
  const full = over || (props.id ? classText(classes.get(props.id), props.id, teachers) : '') || props.fallback || '';
  return <Resolved {...props} full={full} />;
}

export function SiteAbbr(props: KindProps) {
  const sites = useIndex('sites');
  const over = useOverride('site', props.id);
  const full = over || (props.id ? siteText(sites.get(props.id), props.id) : '') || props.fallback || '';
  return <Resolved {...props} full={full} />;
}

/** Generisch: `<EntityAbbr kind="room" id="R112" />`. */
export function EntityAbbr({ kind, ...rest }: KindProps & { kind: AbbrKind }) {
  switch (kind) {
    case 'teacher':
      return <TeacherAbbr {...rest} />;
    case 'subject':
      return <SubjectAbbr {...rest} />;
    case 'room':
      return <RoomAbbr {...rest} />;
    case 'class':
      return <ClassAbbr {...rest} />;
    default:
      return <SiteAbbr {...rest} />;
  }
}

/** Mehrere Kürzel mit Trennzeichen („MÜL, SCH“); Text oder Liste von ids. `empty` steht, wenn nichts da ist. */
export function AbbrList({
  kind,
  ids,
  passive,
  separator = ', ',
  empty = null,
}: {
  kind: AbbrKind;
  ids: string | readonly string[] | null | undefined;
  passive?: boolean;
  separator?: string;
  empty?: ReactNode;
}) {
  const list = splitIds(ids);
  if (!list.length) return <>{empty}</>;
  return (
    <>
      {list.map((id, i) => (
        <Fragment key={`${id}-${i}`}>
          {i > 0 ? separator : null}
          <EntityAbbr kind={kind} id={id} passive={passive} />
        </Fragment>
      ))}
    </>
  );
}
