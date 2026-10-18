import { useMediaQuery } from './misc';

/** Media-Query: Gerät hat eine echte Maus/Touchpad (feiner Zeiger, Hover möglich). */
export const FINE_POINTER_QUERY = '(hover: hover) and (pointer: fine)';

/**
 * Eingabeart des Geräts. `fine` = Maus/Touchpad (und meist Tastatur) vorhanden,
 * `touch` = Handy/Tablet ohne Maus. Hinweise zu Tastatur, Maus oder Drag & Drop nur bei `fine` zeigen.
 */
export function inputModeFor(fine: boolean): 'fine' | 'touch' {
  return fine ? 'fine' : 'touch';
}

export function useInputMode(): { mode: 'fine' | 'touch'; fine: boolean; touch: boolean } {
  const fine = useMediaQuery(FINE_POINTER_QUERY);
  return { mode: inputModeFor(fine), fine, touch: !fine };
}
