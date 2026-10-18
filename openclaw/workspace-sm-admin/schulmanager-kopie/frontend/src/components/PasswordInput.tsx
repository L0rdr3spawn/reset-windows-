/**
 * Passwortfeld mit Auge-Knopf zum Ein- und Ausblenden der Eingabe.
 *
 * Nimmt alle üblichen <input>-Eigenschaften (id, name, autoComplete, required …) – das Feld ist standardmäßig
 * type="password", Passwort-Manager der Browser erkennen es also weiter. Nach dem Absenden des Formulars wird die
 * Eingabe wieder verborgen.
 */
import { useEffect, useRef, useState, type InputHTMLAttributes, type Ref } from 'react';
import { Icon } from './Icon';

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & { ref?: Ref<HTMLInputElement> };

export function PasswordInput({ ref, className, disabled, ...props }: Props) {
  const [visible, setVisible] = useState(false);
  const own = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const form = own.current?.form;
    if (!form) return;
    const hide = () => setVisible(false);
    form.addEventListener('submit', hide);
    return () => form.removeEventListener('submit', hide);
  }, []);

  const setRef = (el: HTMLInputElement | null) => {
    own.current = el;
    if (typeof ref === 'function') ref(el);
    else if (ref) (ref as { current: HTMLInputElement | null }).current = el;
  };

  const label = visible ? 'Passwort verbergen' : 'Passwort anzeigen';
  return (
    <span className={`pw-input${className ? ` ${className}` : ''}`}>
      <input
        {...props}
        ref={setRef}
        type={visible ? 'text' : 'password'}
        disabled={disabled}
        autoCapitalize="none"
        autoCorrect="off"
        spellCheck={false}
      />
      <button
        type="button"
        className="pw-toggle"
        onClick={() => setVisible((v) => !v)}
        aria-pressed={visible}
        aria-label={label}
        title={label}
        disabled={disabled}
      >
        <Icon name={visible ? 'eyeOff' : 'eye'} />
      </button>
    </span>
  );
}
