/**
 * Kleines Hilfe-Symbol neben einer Beschriftung oder Überschrift – dünne Hülle um `PageHelp` (components/Help.tsx),
 * damit überall dieselbe Hilfe-Bedienung gilt (Maus, Rechtsklick, Antippen, F1, Escape). Statt langer Erklärtexte.
 */
import type { ReactNode } from 'react';
import { PageHelp } from './Help';

export function HelpTip({ children, label = 'Erklärung' }: { children: ReactNode; label?: string }) {
  return <PageHelp label={label}>{children}</PageHelp>;
}
