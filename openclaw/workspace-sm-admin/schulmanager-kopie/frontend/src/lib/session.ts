/**
 * Zentrale Sitzungs-Rücksetzung (U-01, A-09, Vorarbeit A-26).
 *
 * Alles, was zum angemeldeten Konto gehört und modulweit zwischengespeichert ist (Sammlungs-Cache, Datei-Limits,
 * Kursraum-Übersicht, Badges …), meldet hier eine Rücksetz-Funktion an. `AuthContext` ruft {@link resetSession} bei
 * Abmeldung, bei jedem 401 (Sitzung abgelaufen) und beim Wechsel auf ein anderes Konto auf. So sieht das nächste
 * Konto im selben Tab nie Daten im Umfang des vorigen.
 *
 * Bewusst ohne Abhängigkeiten: Module melden sich beim Laden an (`onSessionReset(fn)` auf oberster Ebene), auch
 * Feature-Module, die per `import.meta.glob` vor dem Rest der App ausgewertet werden.
 */

type Reset = () => void;

const resets = new Set<Reset>();
let currentAccount: string | null = null;
let resetCount = 0;

/** Rücksetz-Funktion anmelden; Rückgabe meldet sie wieder ab. */
export function onSessionReset(fn: Reset): () => void {
  resets.add(fn);
  return () => {
    resets.delete(fn);
  };
}

/** Alle kontobezogenen Zwischenspeicher leeren. Fehler einzelner Funktionen halten die übrigen nicht auf. */
export function resetSession(): void {
  currentAccount = null;
  resetCount += 1;
  resets.forEach((fn) => {
    try {
      fn();
    } catch (e) {
      if (typeof console !== 'undefined') console.error('[session] Rücksetzen fehlgeschlagen', e);
    }
  });
}

/**
 * Angemeldetes Konto mitteilen (`null` = abgemeldet). Wechselt das Konto ohne vorherige Abmeldung (z. B. Anmeldung
 * über die Login-Seite, während noch ein anderes Konto aktiv war), wird vorher zurückgesetzt.
 */
export function setSessionAccount(key: string | null): void {
  if (key === currentAccount) return;
  if (currentAccount !== null) resetSession();
  currentAccount = key;
}

/** Für Tests und Diagnose: wie oft wurde zurückgesetzt, welches Konto ist aktiv? */
export function sessionState(): { account: string | null; resets: number; listeners: number } {
  return { account: currentAccount, resets: resetCount, listeners: resets.size };
}
