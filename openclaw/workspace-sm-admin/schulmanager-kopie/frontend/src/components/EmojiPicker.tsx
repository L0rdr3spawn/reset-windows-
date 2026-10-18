/**
 * Emoji-Auswahl (Chats, Postfach): Knopf mit kleinem Auswahlfenster – Kategorien und Suche, alles lokal
 * (Unicode-Zeichen, keine externen Server). `onPick` bekommt das gewählte Emoji; Einfügen übernimmt der Aufrufer
 * (siehe {@link useEmojiInsert}).
 *
 *   <EmojiButton onPick={insertEmoji} />
 */
import { useCallback, useEffect, useId, useMemo, useRef, useState, type RefObject } from 'react';
import { EMOJI_CATEGORIES, searchEmoji } from '../lib/emojiData';
import { insertAt } from '../lib/emoji';
import './emoji.css';

const RECENT_KEY = 'sm-emoji-recent';

function loadRecent(): string[] {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    const list: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(list) ? list.filter((x): x is string => typeof x === 'string').slice(0, 16) : [];
  } catch {
    return [];
  }
}

function saveRecent(list: string[]): void {
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(list));
  } catch {
    /* egal */
  }
}

export function EmojiPicker({ onPick, onClose }: { onPick: (emoji: string) => void; onClose: () => void }) {
  const [cat, setCat] = useState(EMOJI_CATEGORIES[0].id);
  const [query, setQuery] = useState('');
  const [recent, setRecent] = useState<string[]>(loadRecent);
  const searchId = useId();
  const found = useMemo(() => searchEmoji(query), [query]);
  const searching = query.trim().length > 0;
  const category = EMOJI_CATEGORIES.find((c) => c.id === cat) ?? EMOJI_CATEGORIES[0];
  const shown = searching ? found : category.items;

  const pick = (e: string) => {
    const next = [e, ...recent.filter((x) => x !== e)].slice(0, 16);
    setRecent(next);
    saveRecent(next);
    onPick(e);
  };

  return (
    <div className="emoji-pop" role="dialog" aria-label="Emoji auswählen">
      <label htmlFor={searchId} className="sr-only">
        Emoji suchen
      </label>
      <input
        id={searchId}
        type="search"
        className="emoji-search"
        placeholder="Suchen (z. B. herz, lachen) …"
        value={query}
        autoComplete="off"
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            e.stopPropagation();
            onClose();
          }
        }}
      />
      {!searching && (
        <div className="emoji-tabs" role="tablist" aria-label="Kategorien">
          {EMOJI_CATEGORIES.map((c) => (
            <button
              key={c.id}
              type="button"
              role="tab"
              aria-selected={c.id === cat}
              aria-label={c.label}
              title={c.label}
              className={`emoji-tab${c.id === cat ? ' active' : ''}`}
              onClick={() => setCat(c.id)}
            >
              {c.icon}
            </button>
          ))}
        </div>
      )}
      <div className="emoji-grid" role="group" aria-label={searching ? 'Suchergebnisse' : category.label}>
        {!searching && recent.length > 0 && (
          <>
            <div className="emoji-head">Zuletzt benutzt</div>
            {recent.map((e) => (
              <button key={`r${e}`} type="button" className="emoji-btn" onClick={() => pick(e)}>
                {e}
              </button>
            ))}
            <div className="emoji-head">{category.label}</div>
          </>
        )}
        {shown.map((it) => (
          <button key={it.e} type="button" className="emoji-btn" title={it.k.split(' ').slice(0, 3).join(', ')} onClick={() => pick(it.e)}>
            {it.e}
          </button>
        ))}
        {searching && !found.length && <p className="small muted emoji-none">Kein Emoji gefunden.</p>}
      </div>
    </div>
  );
}

/** Knopf „😊“, der die Auswahl ein- und ausblendet (schließt bei Klick daneben bzw. Escape). */
export function EmojiButton({
  onPick,
  className = 'btn btn-icon',
  label = 'Emoji einfügen',
}: {
  onPick: (emoji: string) => void;
  className?: string;
  label?: string;
}) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (!open) return;
    const away = (e: MouseEvent | TouchEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false);
    };
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', away);
    document.addEventListener('touchstart', away);
    document.addEventListener('keydown', key);
    return () => {
      document.removeEventListener('mousedown', away);
      document.removeEventListener('touchstart', away);
      document.removeEventListener('keydown', key);
    };
  }, [open]);
  return (
    <span className="emoji-wrap" ref={box}>
      <button type="button" className={className} aria-label={label} title={label} aria-haspopup="dialog" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <span aria-hidden="true">😊</span>
      </button>
      {open && <EmojiPicker onPick={onPick} onClose={() => setOpen(false)} />}
    </span>
  );
}

/** Fügt Emoji an der Cursorposition eines Textfelds ein (Fokus und Cursor bleiben erhalten). */
export function useEmojiInsert(
  ref: RefObject<HTMLTextAreaElement | HTMLInputElement | null>,
  value: string,
  setValue: (v: string) => void,
  maxLength?: number,
): (emoji: string) => void {
  return useCallback(
    (emoji: string) => {
      const el = ref.current;
      const r = insertAt(value, el?.selectionStart, el?.selectionEnd, emoji, maxLength);
      setValue(r.value);
      if (el) {
        requestAnimationFrame(() => {
          el.focus();
          el.setSelectionRange(r.caret, r.caret);
        });
      }
    },
    [ref, value, setValue, maxLength],
  );
}
