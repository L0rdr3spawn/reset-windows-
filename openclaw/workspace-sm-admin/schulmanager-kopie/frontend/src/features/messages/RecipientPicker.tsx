/**
 * Empfängerauswahl (Combobox nach WAI-ARIA): Suche im Adressbuch des Servers (nur erlaubte Personen und – mit
 * `messages.broadcast` – Gruppen), ohne Suchtext Vorschläge. Pfeiltasten wählen, Enter übernimmt, Escape schließt,
 * Rücktaste im leeren Feld entfernt den letzten Eintrag. Eine getippte E-Mail-Adresse wird als Empfänger übernommen
 * (Enter, Komma, Semikolon oder Verlassen des Feldes) – Schulkonto mit dieser Adresse oder extern. Passt der Suchtext
 * zu einer Klasse, öffnet „Klasse … anzeigen“ die Klassenansicht (Kinder, Eltern, Lehrkräfte).
 */
import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from 'react';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { useDebounced } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { messagesApi } from './api';
import { ClassRosterPanel } from './ClassRoster';
import { Avatar } from './components';
import { ClassAbbr } from '../../components/Abbr';
import { addRecipient, isEmail, personDetail, plural, recipientKey, recipientLabel, removeRecipient } from './logic';
import type { GroupOption, Person, Recipient, RecipientsResponse } from './types';

interface Option {
  key: string;
  item: Recipient | ClassItem;
}
interface ClassItem {
  type: 'class';
  id: string;
  name: string;
}

const chipLabel = recipientLabel;

export function RecipientPicker({
  value,
  onChange,
  inputId,
  describedBy,
  disabled,
  invalid,
  placeholder,
}: {
  value: Recipient[];
  onChange: (list: Recipient[]) => void;
  inputId: string;
  describedBy?: string;
  disabled?: boolean;
  invalid?: boolean;
  placeholder?: string;
}) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [roster, setRoster] = useState<string | null>(null);
  const debounced = useDebounced(query, 220);
  const listId = useId();
  const statusId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const q = useApi<RecipientsResponse>((signal) => messagesApi.recipients(debounced, signal), [debounced], { enabled: open && !disabled });

  const selected = useMemo(() => new Set(value.map(recipientKey)), [value]);
  const data = q.data;
  const fresh = data && data.query === debounced.trim();
  const groups: Option[] = useMemo(() => (data?.groups ?? []).map((g) => ({ key: recipientKey(g), item: g as Recipient })).filter((o) => !selected.has(o.key)), [data, selected]);
  const people: Option[] = useMemo(() => (data?.people ?? []).map((p) => ({ key: recipientKey(p), item: p as Recipient })).filter((o) => !selected.has(o.key)), [data, selected]);
  const typedEmail = isEmail(query) ? query.trim().toLowerCase() : '';
  const emailOption: Option[] = useMemo(
    () =>
      typedEmail && !selected.has(`email:${typedEmail}`)
        ? [
            {
              key: `email:${typedEmail}`,
              item: { type: 'email', email: typedEmail } as Recipient,
            },
          ]
        : [],
    [typedEmail, selected],
  );
  const classOpts: Option[] = useMemo(
    () =>
      (fresh ? (data?.classes ?? []) : []).map((c) => ({
        key: `class:${c.id}`,
        item: { type: 'class' as const, id: c.id, name: c.name },
      })),
    [data, fresh],
  );
  const options = useMemo(() => [...emailOption, ...classOpts, ...people, ...groups], [emailOption, classOpts, people, groups]);

  /** Getippte Adresse(n) übernehmen – auch mehrere, durch Komma/Semikolon getrennt. */
  const takeTyped = (text: string): boolean => {
    const parts = text
      .split(/[,;\s]+/)
      .map((x) => x.trim())
      .filter(Boolean);
    if (!parts.length || !parts.every(isEmail)) return false;
    let list = value;
    for (const addr of parts) list = addRecipient(list, { type: 'email', email: addr.toLowerCase() });
    onChange(list);
    setQuery('');
    return true;
  };

  useEffect(() => setActive(0), [debounced, open]);
  useEffect(() => {
    if (active >= options.length) setActive(Math.max(0, options.length - 1));
  }, [active, options.length]);

  const pick = (o: Option | undefined) => {
    if (!o) return;
    if (o.item.type === 'class') {
      setRoster(o.item.id);
      setQuery('');
      setOpen(false);
      return;
    }
    onChange(addRecipient(value, o.item));
    setQuery('');
    setOpen(false); // Vorschläge schließen, damit sie das Formular nicht verdecken (Tippen/Pfeil öffnet wieder)
    inputRef.current?.focus();
  };

  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!open) setOpen(true);
      else setActive((a) => (options.length ? (a + 1) % options.length : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((a) => (options.length ? (a - 1 + options.length) % options.length : 0));
    } else if (e.key === 'Enter') {
      if (open && options[active]) {
        e.preventDefault();
        pick(options[active]);
      } else if (takeTyped(query)) {
        e.preventDefault();
      }
    } else if ((e.key === ',' || e.key === ';') && isEmail(query)) {
      e.preventDefault();
      takeTyped(query);
    } else if (e.key === 'Escape') {
      if (open) {
        e.preventDefault();
        e.stopPropagation();
        setOpen(false);
      }
    } else if (e.key === 'Backspace' && !query && value.length) {
      onChange(value.slice(0, -1));
    }
  };

  const optionId = (i: number) => `${listId}-o${i}`;
  const showList = open && !disabled;
  const shortQuery = debounced.trim().length > 0 && debounced.trim().length < 2;
  let status = '';
  if (showList && fresh && !q.loading) {
    status = options.length ? plural(options.length, 'Vorschlag', 'Vorschläge') : 'Keine passenden Empfänger/innen';
  }

  const renderOption = (o: Option, i: number) => {
    const r = o.item;
    const isActive = i === active;
    if (r.type === 'class') {
      return (
        <li
          key={o.key}
          id={optionId(i)}
          role="option"
          aria-selected={isActive}
          className={`pf-opt${isActive ? ' pf-opt-active' : ''}`}
          onMouseDown={(e) => {
            e.preventDefault();
            pick(o);
          }}
          onMouseEnter={() => setActive(i)}
        >
          <Avatar name={r.name} size={30} group />
          <span className="pf-opt-main">
            <span className="pf-opt-title">
              Klasse{' '}
              <ClassAbbr id={r.id} passive>
                {r.name}
              </ClassAbbr>{' '}
              anzeigen
            </span>
            <span className="pf-opt-sub">Kinder, Eltern und Lehrkräfte einzeln oder gesammelt auswählen</span>
          </span>
        </li>
      );
    }
    return (
      <li
        key={o.key}
        id={optionId(i)}
        role="option"
        aria-selected={isActive}
        className={`pf-opt${isActive ? ' pf-opt-active' : ''}`}
        onMouseDown={(e) => {
          e.preventDefault();
          pick(o);
        }}
        onMouseEnter={() => setActive(i)}
      >
        {r.type === 'email' ? (
          <>
            <Avatar name={r.email} size={30} />
            <span className="pf-opt-main">
              <span className="pf-opt-title">E-Mail an {r.email}</span>
              <span className="pf-opt-sub">Konto der Schule mit dieser Adresse oder extern über Ihr E-Mail-Konto</span>
            </span>
          </>
        ) : r.type === 'user' ? (
          <>
            <Avatar name={r.name} role={r.role} size={30} />
            <span className="pf-opt-main">
              <span className="pf-opt-title">{r.name}</span>
              <span className="pf-opt-sub">{personDetail(r as Person)}</span>
            </span>
          </>
        ) : (
          <>
            <Avatar name={r.label} size={30} group />
            <span className="pf-opt-main">
              <span className="pf-opt-title">{r.label}</span>
              <span className="pf-opt-sub">
                {(r as GroupOption).category_label}
                {typeof (r as GroupOption).count === 'number' ? ` · ${plural((r as GroupOption).count ?? 0, 'Person', 'Personen')}` : ''}
              </span>
            </span>
          </>
        )}
      </li>
    );
  };

  return (
    <div className="pf-picker-wrap">
      <div className={`pf-picker${invalid ? ' pf-picker-invalid' : ''}${disabled ? ' pf-picker-disabled' : ''}`} onClick={() => inputRef.current?.focus()}>
        {value.length > 0 && (
          <ul className="pf-chips" aria-label="Ausgewählte Empfänger/innen">
            {value.map((r) => (
              <li key={recipientKey(r)} className={`pf-chip${r.type === 'group' ? ' pf-chip-group' : ''}`}>
                <span className="pf-chip-text">{chipLabel(r)}</span>
                <button
                  type="button"
                  className="pf-chip-x"
                  aria-label={`${chipLabel(r)} entfernen`}
                  disabled={disabled}
                  onClick={(e) => {
                    e.stopPropagation();
                    onChange(removeRecipient(value, recipientKey(r)));
                    inputRef.current?.focus();
                  }}
                >
                  <Icon name="x" />
                </button>
              </li>
            ))}
          </ul>
        )}
        <input
          ref={inputRef}
          id={inputId}
          type="text"
          role="combobox"
          className="pf-picker-input"
          autoComplete="off"
          spellCheck={false}
          aria-autocomplete="list"
          aria-expanded={showList}
          aria-controls={listId}
          aria-activedescendant={showList && options[active] ? optionId(active) : undefined}
          aria-describedby={[describedBy, statusId].filter(Boolean).join(' ') || undefined}
          aria-invalid={invalid || undefined}
          disabled={disabled}
          value={query}
          placeholder={value.length ? 'Weitere hinzufügen …' : (placeholder ?? 'Name, Gruppe oder E-Mail-Adresse')}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onClick={() => setOpen(true)}
          onBlur={() => {
            setOpen(false);
            takeTyped(query);
          }}
          onKeyDown={onKey}
        />
      </div>
      <span id={statusId} className="sr-only" aria-live="polite">
        {status}
      </span>
      {showList && (
        <div className="pf-popup">
          <ul id={listId} role="listbox" aria-label="Vorschläge für Empfänger/innen" className="pf-options">
            {emailOption.map((o, i) => renderOption(o, i))}
            {classOpts.length > 0 && (
              <li role="presentation" className="pf-opt-head">
                Klassen
              </li>
            )}
            {classOpts.map((o, i) => renderOption(o, emailOption.length + i))}
            {people.length > 0 && (
              <li role="presentation" className="pf-opt-head">
                {data?.suggestions ? 'Vorschläge' : 'Personen'}
              </li>
            )}
            {people.map((o, i) => renderOption(o, emailOption.length + classOpts.length + i))}
            {groups.length > 0 && (
              <li role="presentation" className="pf-opt-head">
                Gruppen
              </li>
            )}
            {groups.map((o, i) => renderOption(o, emailOption.length + classOpts.length + people.length + i))}
          </ul>
          {q.error ? <p className="pf-popup-note pf-error-text">{errorMessage(q.error)}</p> : null}
          {q.loading && !fresh && <p className="pf-popup-note">Suche läuft …</p>}
          {fresh && !q.loading && !options.length && !typedEmail && (
            <p className="pf-popup-note">
              {shortQuery
                ? 'Bitte mindestens 2 Buchstaben eingeben.'
                : debounced.trim()
                  ? 'Niemand gefunden. Personen, die keine Nachrichten empfangen können, erscheinen nicht.'
                  : 'Namen eingeben, um Personen zu finden.'}
            </p>
          )}
        </div>
      )}
      {roster && !disabled && <ClassRosterPanel classId={roster} value={value} onChange={onChange} onClose={() => setRoster(null)} />}
    </div>
  );
}
