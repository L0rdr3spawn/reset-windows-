/**
 * Eingabezeile wie im Messenger (Chats und Antworten auf Briefe): eine durchgehende, mit dem Text wachsende Zeile;
 * links „+“ (Bilder/Dateien anhängen), rechts in der Zeile der Senden-Pfeil. Der Emoji-Knopf erscheint nur mit Maus
 * und Tastatur (`(pointer: fine)`) – auf dem Handy gibt es Emojis über die Tastatur. Mit Maus/Tastatur sendet Enter
 * (Umschalt + Enter = neue Zeile), auf dem Handy macht Enter eine neue Zeile und gesendet wird mit dem Pfeil.
 */
import { useEffect, useRef, useState, type ClipboardEvent, type KeyboardEvent, type RefObject } from 'react';
import { EmojiButton, useEmojiInsert } from '../../components/EmojiPicker';
import { useMediaQuery } from '../../hooks/misc';
import { Glyph } from '../messages/components';

const MAX_HEIGHT = 168;

export function Composer({
  id,
  value,
  onChange,
  onSend,
  canSend,
  placeholder,
  label,
  maxLength,
  onAttach,
  attachLabel = 'Datei anhängen',
  onPaste,
  describedBy,
  textRef,
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  /** darf auch asynchron sein; Fehler zeigt der Aufrufer selbst an */
  onSend: () => Promise<unknown> | void;
  /** Senden möglich (Text oder Anhang vorhanden) */
  canSend: boolean;
  placeholder: string;
  /** Beschriftung für Bildschirmleser */
  label: string;
  maxLength: number;
  /** ohne Angabe gibt es kein „+“ */
  onAttach?: () => void;
  attachLabel?: string;
  onPaste?: (e: ClipboardEvent<HTMLTextAreaElement>) => void;
  describedBy?: string;
  textRef?: RefObject<HTMLTextAreaElement | null>;
}) {
  const own = useRef<HTMLTextAreaElement>(null);
  const ref = textRef ?? own;
  const mouse = useMediaQuery('(pointer: fine)');
  const [busy, setBusy] = useState(false);
  const insertEmoji = useEmojiInsert(ref, value, onChange, maxLength);

  // Feld wächst mit dem Text (bis etwa sieben Zeilen), danach scrollt es; bei neuer Breite neu messen
  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const fit = () => {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
    };
    fit();
    if (typeof ResizeObserver === 'undefined') return undefined;
    let width = el.clientWidth;
    const ro = new ResizeObserver(() => {
      if (el.clientWidth !== width) {
        width = el.clientWidth;
        fit();
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [value, ref]);

  const send = async () => {
    if (!canSend || busy) return;
    setBusy(true);
    try {
      await onSend();
    } finally {
      setBusy(false);
    }
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== 'Enter' || e.nativeEvent.isComposing) return;
    if (mouse && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  };

  return (
    <div className="cmp">
      {onAttach && (
        <button type="button" className="cmp-btn cmp-plus" aria-label={attachLabel} title={attachLabel} onClick={onAttach}>
          <Glyph name="plus" size={22} />
        </button>
      )}
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <textarea
        ref={ref}
        id={id}
        className="cmp-text"
        rows={1}
        value={value}
        maxLength={maxLength}
        placeholder={placeholder}
        aria-describedby={describedBy}
        enterKeyHint="enter"
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKey}
        onPaste={onPaste}
      />
      {mouse && <EmojiButton onPick={insertEmoji} className="cmp-btn" />}
      <button type="button" className="cmp-send" disabled={!canSend || busy} aria-busy={busy} aria-label="Senden" title="Senden" onClick={() => void send()}>
        <Glyph name="arrowUp" size={20} />
      </button>
    </div>
  );
}
