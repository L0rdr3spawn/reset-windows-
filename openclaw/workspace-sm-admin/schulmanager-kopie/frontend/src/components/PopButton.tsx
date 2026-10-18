/**
 * Knopf mit kleiner Liste (Sprechblase): Antippen/Klick öffnet, Antippen daneben oder Escape schließt.
 * Die Liste hängt am `body` (position: fixed) und wird mit `placeHelp` im sichtbaren Bereich gehalten – so schneidet
 * sie weder der scrollende Stundenplan noch der Tageskopf ab.
 */
import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { placeHelp } from '../lib/help';

export function PopButton({ label, className, ariaLabel, children, popClassName }: { label: ReactNode; className?: string; ariaLabel: string; children: ReactNode; popClassName?: string }) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ left: number; top: number } | null>(null);
  const btn = useRef<HTMLButtonElement>(null);
  const pop = useRef<HTMLDivElement>(null);
  const id = useId();

  useLayoutEffect(() => {
    if (!open || !btn.current || !pop.current) return;
    const r = btn.current.getBoundingClientRect();
    const p = pop.current.getBoundingClientRect();
    const { left, top } = placeHelp(r, { width: p.width, height: p.height }, { width: window.innerWidth, height: window.innerHeight });
    setPos({ left, top });
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const away = (e: Event) => {
      const t = e.target as Node;
      if (!btn.current?.contains(t) && !pop.current?.contains(t)) setOpen(false);
    };
    const esc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false);
        btn.current?.focus();
      }
    };
    const close = () => setOpen(false);
    document.addEventListener('pointerdown', away);
    document.addEventListener('keydown', esc);
    window.addEventListener('scroll', close, true);
    window.addEventListener('resize', close);
    return () => {
      document.removeEventListener('pointerdown', away);
      document.removeEventListener('keydown', esc);
      window.removeEventListener('scroll', close, true);
      window.removeEventListener('resize', close);
    };
  }, [open]);

  return (
    <>
      <button
        ref={btn}
        type="button"
        className={className}
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        aria-label={ariaLabel}
        onClick={(e) => {
          e.stopPropagation();
          setPos(null);
          setOpen((o) => !o);
        }}
      >
        {label}
      </button>
      {open &&
        createPortal(
          <div
            ref={pop}
            id={id}
            role="dialog"
            aria-label={ariaLabel}
            className={`pop-list${popClassName ? ` ${popClassName}` : ''}`}
            style={{ left: pos?.left ?? 0, top: pos?.top ?? 0, visibility: pos ? 'visible' : 'hidden' }}
            onClick={(e) => e.stopPropagation()}
          >
            {children}
          </div>,
          document.body,
        )}
    </>
  );
}
