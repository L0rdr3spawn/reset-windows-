# Beta-Test Schulmanager mit OpenClaw

Drei lokale OpenClaw-Agenten prüfen den Schulmanager Bereich für Bereich. Sie laufen mit Gemma auf der RTX 5070, nichts verlässt den PC.

| Agent | Aufgabe |
|---|---|
| sm-admin | hält die aktuelle Server-Kopie (Code, ohne Datenbank und Passwörter), teilt Aufträge zu, schreibt den Update-Patch |
| sm-tester-a | prüft Bedienung und Aussehen in der Demo-Instanz |
| sm-tester-b | prüft den Code (Aufbau, Modularität, Projektregeln) |

## Ablauf je Bereich

1. Kopie vom Server holen (immer der Stand, der auf dem Server läuft).
2. Admin teilt den Bereich in Auftrag A und Auftrag B.
3. Tester A und Tester B arbeiten gleichzeitig und schreiben je einen Bericht.
4. Gegenprüfung über Kreuz: B prüft den Bericht von A, A prüft den Bericht von B.
5. Admin schreibt aus allem einen Update-Patch.

Die Bereiche kommen aus dem Code-Atlas (24 Stück). `status.json` merkt sich, welche fertig sind.

## Ordner

- `patches/` – Update-Patches (Markdown mit Begründung und Diffs gegen die Kopie). Nichts davon wird automatisch eingespielt.
- `berichte/` – Berichte und Gegenprüfungen der Tester.
- `verlauf.log` – was wann lief.
- `skripte/` – Ablauf (`betatest-runde.ps1`), Kopie holen, Demo-Zugänge eintragen.

## Bedienung

1. Desktop: **OpenClaw starten**.
2. Einmalig: **Betatest Zugaenge eintragen** (zwei Demo-Zugänge, verdeckte Eingabe). Ohne Zugänge prüfen die Tester nur öffentliche Seiten und den Code.
3. Desktop: **Betatest naechster Bereich** (ein Bereich) oder **Betatest alles durcharbeiten** (alle offenen Bereiche nacheinander, dauert Stunden).
4. Danach: **OpenClaw stoppen**.

Neu von vorn: `skripte\betatest-runde.ps1 -Neu -Alle`. Einzelner Bereich: `-Bereich nachrichten`.

## Grenzen

Gemma E4B ist schnell, aber ein kleines Modell. Befunde und besonders Diffs vor dem Übernehmen prüfen; Claude kann das mit dem Skill `schulpuls-nutzercheck` übernehmen.
