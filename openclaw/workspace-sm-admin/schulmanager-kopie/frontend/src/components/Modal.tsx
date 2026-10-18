import { useEffect, useId, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { Icon } from './Icon';

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Barrierearmer Dialog: Fokusfalle, Escape schließt, Fokus kehrt zurück, aria-modal.
 * `variant="drawer"` öffnet als Seitenleiste rechts.
 */
export function Modal({
  title,
  onClose,
  children,
  footer,
  size,
  variant = 'modal',
}: {
  title: ReactNode;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  size?: 'lg';
  variant?: 'modal' | 'drawer';
}) {
  const ref = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  useEffect(() => {
    const prev = document.activeElement as HTMLElement | null;
    const el = ref.current;
    const first = el?.querySelector<HTMLElement>('[autofocus], input:not([type="hidden"]), select, textarea') ?? el?.querySelector<HTMLElement>(FOCUSABLE);
    (first ?? el)?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        closeRef.current();
      } else if (e.key === 'Tab' && el) {
        const items = Array.from(el.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((x) => x.offsetParent !== null);
        if (!items.length) return;
        const firstEl = items[0] as HTMLElement;
        const lastEl = items[items.length - 1] as HTMLElement;
        if (e.shiftKey && document.activeElement === firstEl) {
          e.preventDefault();
          lastEl.focus();
        } else if (!e.shiftKey && document.activeElement === lastEl) {
          e.preventDefault();
          firstEl.focus();
        }
      }
    };
    document.addEventListener('keydown', onKey);
    const overflow = document.body.style.overflow;
    if (variant === 'modal') document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = overflow;
      prev?.focus?.();
    };
  }, [variant]);

  const content = (
    <div
      ref={ref}
      className={variant === 'drawer' ? 'drawer' : `modal${size === 'lg' ? ' modal-lg' : ''}`}
      role="dialog"
      aria-modal={variant === 'modal'}
      aria-labelledby={titleId}
      tabIndex={-1}
      onMouseDown={(e) => e.stopPropagation()}
    >
      <div className="modal-head">
        <h2 id={titleId}>{title}</h2>
        <button type="button" className="btn btn-ghost btn-icon" onClick={onClose} aria-label="Schließen">
          <Icon name="close" />
        </button>
      </div>
      <div className="modal-body">{children}</div>
      {footer && <div className="modal-foot">{footer}</div>}
    </div>
  );

  if (variant === 'drawer') return createPortal(content, document.body);
  return createPortal(
    <div className="modal-backdrop" onMouseDown={onClose}>
      {content}
    </div>,
    document.body,
  );
}
