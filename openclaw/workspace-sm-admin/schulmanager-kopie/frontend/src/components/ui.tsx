import { createContext, useContext, useId, useMemo, useRef, useState, type ReactNode } from 'react';
import { ApiError, errorMessage, formErrors } from '../api/client';
import type { FieldLabels } from '../api/errors';
import type { EntryKind } from '../api/types';
import { useOptionalToast } from '../context/ToastContext';
import { confirmAsk } from '../lib/confirm';
import { kindInfo } from '../lib/substitution';
import { HelpButton, useDescribedBy, useHelp, useHelpInline } from './Help';
import { Icon } from './Icon';

export function Spinner({ large, label = 'Wird geladen …' }: { large?: boolean; label?: string }) {
  return (
    <span role="status" aria-live="polite">
      <span className={`spinner${large ? ' spinner-lg' : ''}`} aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </span>
  );
}

export function Loading({ label = 'Wird geladen …' }: { label?: string }) {
  return (
    <div className="loading-block" role="status" aria-live="polite">
      <span className="spinner spinner-lg" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

type AlertKind = 'error' | 'warning' | 'success' | 'info';
const ALERT_ICON: Record<AlertKind, string> = { error: 'alert', warning: 'alert', success: 'checkCircle', info: 'info' };

export function Alert({ kind = 'info', title, children, action }: { kind?: AlertKind; title?: ReactNode; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className={`alert alert-${kind}`} role={kind === 'error' ? 'alert' : undefined}>
      <Icon name={ALERT_ICON[kind]} />
      <div className="alert-body">
        {title && <strong>{title}</strong>}
        {children && <div>{children}</div>}
      </div>
      {action}
    </div>
  );
}

/** Fehleranzeige inkl. Hinweisen für 403/409/Netzwerk. */
export function ErrorBox({ error, onRetry, title }: { error: unknown; onRetry?: () => void; title?: string }) {
  if (!error) return null;
  let heading = title ?? 'Fehler beim Laden';
  let text = errorMessage(error);
  let details: string[] = [];
  if (error instanceof ApiError) {
    if (error.status === 403) {
      heading = 'Keine Berechtigung';
      // Konkrete Begründung des Servers (z. B. „nur eigene Klassen“) mit anzeigen, allgemeine Texte nicht doppeln
      const reason = /berechtigung|^forbidden|^not_authenticated/i.test(text.trim()) ? '' : ` (${text.trim().replace(/\.$/, '')})`;
      text = `Für diese Ansicht fehlt Ihrem Konto die nötige Berechtigung${reason}. Bitte wenden Sie sich an die Schulverwaltung.`;
    } else if (error.status === 0) {
      heading = 'Keine Verbindung';
    } else if (error.status === 404) {
      heading = 'Nicht gefunden';
    }
    details = error.conflicts.length ? error.conflicts : error.issues.length > 1 ? error.issues.map((i) => i.summary) : [];
    if (details.length && !error.conflicts.length) text = 'Bitte die Eingaben prüfen.';
  }
  return (
    <Alert
      kind="error"
      title={heading}
      action={
        onRetry && (
          <button type="button" className="btn btn-sm" onClick={onRetry}>
            <Icon name="refresh" /> Erneut versuchen
          </button>
        )
      }
    >
      <span>{text}</span>
      {details.length > 0 && (
        <ul>
          {details.map((d, i) => (
            <li key={i}>{d}</li>
          ))}
        </ul>
      )}
    </Alert>
  );
}

/** Leerer Zustand: kurzer Satz, optional Titel und eine Aktion (docs/DESIGN.md „Leere Zustände“). */
export function Empty({ icon = 'info', title, action, children }: { icon?: string; title?: ReactNode; action?: ReactNode; children?: ReactNode }) {
  return (
    <div className="empty">
      <Icon name={icon} />
      {title && <div className="empty-title">{title}</div>}
      {children && <div>{children}</div>}
      {action && <div className="empty-action">{action}</div>}
    </div>
  );
}

export function KindBadge({ kind, compact }: { kind: EntryKind | string; compact?: boolean }) {
  const info = kindInfo(kind);
  return (
    <span className={`kind ${info.cls}`} title={info.description || info.label}>
      <span className="kind-short" aria-hidden="true">
        {info.short}
      </span>
      {compact ? <span className="sr-only">{info.label}</span> : info.label}
    </span>
  );
}

interface FormErrorState {
  fields: Record<string, string>;
}
const FormErrorsCtx = createContext<FormErrorState | null>(null);

/**
 * Fehler eines Formulars am Feld anzeigen (B-13): `<FormErrors error={saveError} labels={{ ref: 'Lehrkraft' }}>` um
 * das Formular, `Field name="date_from"` am Feld. Validierungsfehler des Servers (422) erscheinen dann am Feld mit
 * Beschriftung statt Feldcode; Felder, die das Formular nicht kennt, landen in der Meldung (Toast/`ErrorBox`).
 * `error` beim Ändern/erneuten Absenden selbst zurücksetzen.
 */
export function FormErrors({ error, labels, children }: { error: unknown; labels?: FieldLabels; children: ReactNode }) {
  const value = useMemo<FormErrorState>(() => ({ fields: error ? formErrors(error, labels).fields : {} }), [error, labels]);
  return <FormErrorsCtx.Provider value={value}>{children}</FormErrorsCtx.Provider>;
}

/** Fehlertext des Servers für ein Feld (`name` = Feldcode der API) innerhalb von {@link FormErrors}. */
export function useFieldError(name?: string): string | null {
  const ctx = useContext(FormErrorsCtx);
  if (!name || !ctx) return null;
  return ctx.fields[name] ?? null;
}

/** Steuerelement in einem Feld ohne `htmlFor` (für die Verknüpfung von Hilfe/Fehler per aria-describedby). */
const FIELD_CONTROL = 'input:not([type="hidden"]), select, textarea, [role="combobox"], [role="group"], [role="radiogroup"]';

/**
 * Beschriftetes Feld. `help` (bzw. – abwärtskompatibel – `hint`) erscheint nicht als Dauertext, sondern als (i) neben
 * der Beschriftung (Klick/Antippen, Enter, F1 im Feld; components/Help.tsx) und ist per aria-describedby
 * mit dem Feld verknüpft. Sichtbar bleibt nur ein kurzer `hint`, wenn zusätzlich `help` gesetzt ist oder `hintInline`.
 * Validierungsfehler (`error`) sind immer sichtbar und ebenfalls verknüpft. Mit `name` (Feldcode der API, z. B.
 * `date_from`) zeigt das Feld innerhalb von {@link FormErrors} auch den Fehler des Servers.
 */
export function Field({
  label,
  hint,
  help,
  hintInline,
  error: ownError,
  name,
  children,
  className,
  htmlFor,
}: {
  label: ReactNode;
  /** Hinweis zum Feld; ohne `help`/`hintInline` wird er zur Hilfe an der Beschriftung */
  hint?: ReactNode;
  /** Hilfe an der Beschriftung (statt erklärender Texte auf der Seite) */
  help?: ReactNode;
  /** `hint` als sichtbaren Kurzhinweis unter dem Feld zeigen (z. B. Formatangabe) */
  hintInline?: boolean;
  error?: string | null;
  /** Feldcode der API (z. B. `date_from`, `items.name`) für Serverfehler aus {@link FormErrors} */
  name?: string;
  children: ReactNode;
  className?: string;
  htmlFor?: string;
}) {
  const serverError = useFieldError(name);
  const error = ownError || serverError;
  const helpContent = help ?? (hintInline ? undefined : hint);
  const visibleHint = help != null || hintInline ? hint : undefined;
  const h = useHelp(helpContent, { button: true });
  const inlineHelp = useHelpInline();
  const uid = useId();
  const box = useRef<HTMLDivElement>(null);
  const hintId = `${uid}hint`;
  const errId = `${uid}err`;
  useDescribedBy(
    () => (htmlFor ? document.getElementById(htmlFor) : box.current?.querySelector(FIELD_CONTROL)),
    [h.enabled && h.descId, !!visibleHint && hintId, !!error && errId],
  );
  return (
    <div ref={box} className={`field${className ? ` ${className}` : ''}`}>
      {h.enabled ? (
        <div className="field-head">
          <label htmlFor={htmlFor}>{label}</label>
          <HelpButton h={h} label={typeof label === 'string' ? `Erklärung zu ${label}` : 'Erklärung'} />
        </div>
      ) : (
        <label htmlFor={htmlFor}>{label}</label>
      )}
      {children}
      {/* Einstellung „Hilfetexte immer anzeigen“: sichtbare Kopie (Bildschirmleser lesen die verknüpfte Beschreibung) */}
      {inlineHelp && h.enabled && (
        <span className="hint" aria-hidden="true">
          {helpContent}
        </span>
      )}
      {visibleHint && (
        <span className="hint" id={hintId}>
          {visibleHint}
        </span>
      )}
      {error && (
        <span className="error-text" id={errId} role={serverError && !ownError ? 'alert' : undefined}>
          {error}
        </span>
      )}
    </div>
  );
}

export interface TabDef<K extends string> {
  key: K;
  label: ReactNode;
  hidden?: boolean;
}

/** Tabs nach WAI-ARIA (Pfeiltasten wechseln). */
export function Tabs<K extends string>({ tabs, active, onChange, label }: { tabs: TabDef<K>[]; active: K; onChange: (k: K) => void; label: string }) {
  const visible = tabs.filter((t) => !t.hidden);
  const id = useId();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const onKey = (e: React.KeyboardEvent, i: number) => {
    let n = -1;
    if (e.key === 'ArrowRight') n = (i + 1) % visible.length;
    if (e.key === 'ArrowLeft') n = (i - 1 + visible.length) % visible.length;
    if (e.key === 'Home') n = 0;
    if (e.key === 'End') n = visible.length - 1;
    if (n >= 0) {
      e.preventDefault();
      const t = visible[n];
      if (t) onChange(t.key);
      refs.current[n]?.focus();
    }
  };
  return (
    <div className="tabs" role="tablist" aria-label={label}>
      {visible.map((t, i) => (
        <button
          key={t.key}
          ref={(el) => {
            refs.current[i] = el;
          }}
          type="button"
          role="tab"
          id={`${id}-${t.key}`}
          className="tab"
          aria-selected={t.key === active}
          tabIndex={t.key === active ? 0 : -1}
          onClick={() => onChange(t.key)}
          onKeyDown={(e) => onKey(e, i)}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function ProgressBar({ value, label }: { value: number; label: string }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div>
      <div className="row-between small">
        <span>{label}</span>
        <span className="mono">{pct} %</span>
      </div>
      <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-label={label}>
        <div className="progress-bar" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

/**
 * Button, der während einer async-Aktion deaktiviert ist. Fehler, die `onClick` nicht selbst abfängt, erscheinen als
 * Toast (deutsch, mit Fehlernummer bei Unerwartetem); ohne Toast-Provider landen sie in der Konsole.
 */
export function AsyncButton({
  onClick,
  children,
  className = 'btn',
  confirm,
  confirmLabel,
  disabled,
  title,
  type = 'button',
}: {
  onClick: () => Promise<unknown> | void;
  children: ReactNode;
  className?: string;
  /** Rückfrage im App-Dialog vor der Aktion. */
  confirm?: string;
  /** Beschriftung der Hauptaktion im Dialog (Standard: Text des Knopfs, sonst „Bestätigen“). */
  confirmLabel?: string;
  disabled?: boolean;
  title?: string;
  type?: 'button' | 'submit';
}) {
  const [busy, setBusy] = useState(false);
  const toast = useOptionalToast();
  return (
    <button
      type={type}
      className={className}
      disabled={disabled || busy}
      aria-busy={busy}
      title={title}
      onClick={async () => {
        if (confirm && !(await confirmAsk({ message: confirm, confirmLabel: confirmLabel ?? (typeof children === 'string' && children.trim() ? children.trim() : undefined), danger: className.includes('btn-danger') || /löschen|leeren|widerrufen/i.test(confirm) }))) return;
        setBusy(true);
        try {
          await onClick();
        } catch (e) {
          if (e instanceof DOMException && e.name === 'AbortError') return;
          if (toast) toast.error(e);
          else console.error(e);
        } finally {
          setBusy(false);
        }
      }}
    >
      {busy && <span className="spinner spinner-sm" aria-hidden="true" />}
      {children}
    </button>
  );
}

export function CopyField({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false);
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className="copy-field">
        <input id={id} type="text" readOnly value={value} onFocus={(e) => e.currentTarget.select()} />
        <button
          type="button"
          className="btn"
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(value);
              setCopied(true);
              window.setTimeout(() => setCopied(false), 2000);
            } catch {
              /* Zwischenablage nicht verfügbar */
            }
          }}
        >
          <Icon name={copied ? 'check' : 'copy'} /> {copied ? 'Kopiert' : 'Kopieren'}
        </button>
      </div>
    </div>
  );
}

export function SegmentedControl<T extends string | number>({
  options,
  value,
  onChange,
  label,
}: {
  options: { value: T; label: ReactNode; title?: string }[];
  value: T;
  onChange: (v: T) => void;
  label: string;
}) {
  return (
    <div className="btn-group" role="group" aria-label={label}>
      {options.map((o) => (
        <button
          key={String(o.value)}
          type="button"
          className="btn btn-sm"
          aria-pressed={o.value === value}
          title={o.title}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
