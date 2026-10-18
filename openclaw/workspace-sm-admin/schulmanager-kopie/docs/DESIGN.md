# Designsprache Schulmanager

Verbindlich für alle Oberflächen (A-59, A-60, A-61; Grundlage für A-62). Technische Quelle der Werte:
`frontend/src/styles/tokens.css` (Tokens) und `frontend/src/styles/app.css` (Bausteine). Komponenten:
`frontend/src/components/ui.tsx`, `components/Help.tsx`, `components/Layout.tsx`.

## 1. Grundsätze

1. **Ruhig.** Neutrale Flächen, eine Akzentfarbe (Blau) für Aktionen und Auswahl. Farbe trägt Bedeutung (Status,
   Vertretungsart), nie Dekoration. Keine Verläufe, keine Hero-Bereiche, keine Illustrationen, keine Emojis.
2. **Professionell.** Sachliche Sprache in der Sie-Form (Schüler-Ansichten wie im Bestand), kurze Beschriftungen,
   einheitliche Begriffe. Kein „Tipp:“, kein Marketington, keine Ausrufezeichen.
3. **Dicht, aber klar.** Viele Informationen pro Bildschirm, sauber ausgerichtet; Gruppierung über Abstand und dünne
   Linien statt über Karten mit Schatten. Ein Wert – ein Steuerelement.
4. **Hilfe an der Beschriftung, nicht auf der Seite.** Keine erklärenden Absätze. Erklärungen liegen in der Hilfe-Funktion
   (Abschnitt 6) und sind für Bildschirmleser verknüpft.
5. **Für alle Geräte.** Jede Seite funktioniert ab 360 px Breite ohne waagerechtes Scrollen der Seite, mit Maus, Touch
   und Tastatur, im hellen und dunklen Schema (WCAG 2.1 AA).

## 2. Typografie

Systemschrift (`--font-sans`), Zahlen tabellarisch (`font-variant-numeric: tabular-nums`) in Tabellen und Kennzahlen,
Kürzel/Codes in `--font-mono`.

| Stufe | Token | Größe | Verwendung |
|---|---|---|---|
| Seitentitel | `--fs-2xl` | 24 px, 600 | genau ein `h1` je Seite (`.page-head`) |
| Abschnitt | `--fs-lg` | 18 px, 600 | `h2` in Karten/Abschnitten, Dialogtitel |
| Unterabschnitt | `--fs-md` | 16 px, 600 | `h3` |
| Fließtext | `--fs-md` | 16 px, Zeilenhöhe 1,5 | Inhalte, Eingabefelder (16 px verhindert Zoom auf iOS) |
| Beschriftung, Tabelle kompakt | `--fs-sm` | 14 px | Feldnamen (600), Tabellenköpfe, Meta-Angaben |
| Kleinst | `--fs-xs` | 12 px | Badges, Gruppen im Menü – nie für Fließtext |

Fließtext höchstens `--measure` (72 Zeichen) breit (`.measure`, automatisch für `.page-head p`).

## 3. Farben

Alle Farben nur über Tokens. Jede Kombination erfüllt WCAG AA (Text ≥ 4,5:1, Ränder von Eingabefeldern und
Fokusrahmen ≥ 3:1) – geprüft für hell **und** dunkel.

| Token | Hell | Dunkel | Verwendung |
|---|---|---|---|
| `--bg` | #f4f6fa | #0d1117 | Seitenhintergrund |
| `--surface` / `-2` / `-3` | #fff / #f8f9fb / #eef1f5 | #161b22 / #1b212a / #222a35 | Flächen, Tabellenkopf, Hover |
| `--border` | #d8dde5 | #2f3a48 | Trennlinien, Kartenrand |
| `--border-strong` | #9aa6b8 | #536074 | Knopfrand |
| `--border-control` | #7d8898 | #6b778a | Rand von Eingabefeldern (≥ 3:1) |
| `--text` / `-muted` / `-faint` | #111827 / #4b5563 / #5f6877 | #e6edf3 / #a9b4c2 / #8b97a6 | Text, Nebeninfo, Hinweis |
| `--primary` (+ `-hover`, `-soft`) | #1d4ed8 | #60a5fa | Hauptaktion, Auswahl, Links |
| `--focus` | #2563eb | #93c5fd | Fokusrahmen 2 px |

**Status** (Text auf `*-soft` ≥ 4,5:1): `--success` Erfolg/OK, `--warning` Achtung/zu prüfen, `--danger` Fehler, Löschen,
Abwesenheit; `--info` neutrale Meldung. Status nie nur über Farbe: immer mit Wort oder Symbol.

**Vertretungsarten** `--k-<art>-bg/-fg/-bd` (Vertretung, Betreuung, Entfall, Verlegung, Raum, Abwesend, Aufsicht,
Klausur, Sonstiges) – ausschließlich für Einträge des Vertretungs- und Stundenplans (`KindBadge`, `tr.kind-row`).

## 4. Abstände, Radien, Schatten

- Abstände nur aus der Skala `--space-1…6` (4, 8, 12, 16, 24, 32 px). Seitenrand am Handy 16 px, sonst 16–32 px.
  Innerhalb von Formularen 12/16 px, zwischen Abschnitten 16–24 px. Keine Inline-Styles für Abstände und Farben.
- Radien: `--radius-sm` 6 px (Knöpfe, Felder, Hinweise), `--radius` 8 px (Karten, Tabellen), `--radius-lg` 12 px
  (Dialoge). Pillen (999 px) nur für Badges/Chips.
- **Schatten sparsam:** nur für Ebenen über dem Inhalt (Menü, Dropdown, Hilfe, Dialog, Toast, aufgeklappte
  Seitenleiste). Karten haben einen 1-px-Rand und keinen Schatten.

## 5. Komponenten-Katalog

| Baustein | Regeln |
|---|---|
| `.page` / `.page-narrow` | Seitencontainer; `.page-narrow` (760 px) für Formulare/Profil, `.page` für Listen/Tabellen (ab 1440 px bis 1680 px breit). |
| `.page-head` | `h1` links, Aktionen rechts (`.actions`), umbrechend. Hilfe zur Seite: `<PageHelp>` neben dem Titel. |
| `.card` | Abschnitt mit Rand, ohne Schatten. Nicht jede Information in eine Karte; Karten nicht schachteln. |
| `.stats` + `.kpi` | Kennzahlen als **eine** Leiste mit Trennlinien, nicht als Einzelkarten. |
| Knöpfe `.btn` | Genau eine Hauptaktion (`.btn-primary`) je Bereich; `.btn-danger` nur für Löschen/Krankmeldung; `.btn-ghost` für Nebenaktionen; Symbolknöpfe `.btn-icon` mit `aria-label`. Beschriftung = Verb („Speichern“, „Krank melden“). |
| `Field` | Beschriftung (≤ 3 Wörter), Steuerelement, Hilfe an der Beschriftung, Fehlertext darunter. |
| `SegmentedControl` | 2–5 gleichrangige Optionen. Statt Schiebereglern für Stufen (z. B. aus/niedrig/mittel/hoch). |
| `Tabs` | Bereiche einer Seite; höchstens eine Reihe, am Handy waagerecht scrollbar innerhalb der Leiste. |
| `Alert` | Nur für echte Zustände (Fehler, Warnung, Erfolg, wichtige Info) – nie als Dauer-Erklärtext. Titel kurz, Text optional. |
| `ErrorBox` | Ladefehler mit „Erneut versuchen“. |
| `Empty` | Leerer Zustand (Abschnitt 9). |
| `KindBadge`, `.badge`, `.chip` | Kurzinformation, Status; keine Sätze. |
| `Modal` / `.drawer` | Für Bearbeiten/Anlegen; Fuß rechts: Abbrechen, Hauptaktion. Am Handy volle Breite. |
| `HelpText`, `PageHelp` | Hilfe-Funktion (Abschnitt 6). |
| Schieberegler | Nicht verwenden. Zahlen als Zahlenfeld, Stufen als `SegmentedControl`, Zeitbudgets als Auswahl („Schnell/Normal/Gründlich“). |

## 6. Hilfe-Funktion (A-60)

Erklärungen erscheinen nur auf Wunsch an der Beschriftung der Option:

- **Maus:** Zeiger ca. 2 s (`HELP_DELAY_MS`) auf dem Namen → Hilfe erscheint; sie bleibt, solange der Zeiger auf Name oder
  Hilfe steht.
- **Rechtsklick** auf den Namen → sofort (angeheftet).
- **Touch:** Antippen des Namens öffnet/schließt (das Feld bekommt dabei keinen Fokus).
- **Tastatur:** F1 im Feld öffnet/schließt, außerhalb von Texteingaben (Auswahl, Kästchen, Knopf) auch „?“;
  Hilfe-Knöpfe (`PageHelp`) und eigenständige Namen (`HelpText` außerhalb eines Labels) mit Enter/Leertaste; beide
  schalten auch per Klick um (Namen in einem Label nicht – dort fokussiert der Klick das Feld).
- **Schließen:** Escape (schließt zuerst die Hilfe, nicht den Dialog darunter) oder Klick außerhalb; höchstens eine
  Hilfe ist offen.
- **Bildschirmleser:** Der Hilfetext ist per `aria-describedby` mit dem Feld verknüpft und wird beim Fokussieren vorgelesen.
- **Erkennbar** an der gepunkteten Unterstreichung des Namens (Cursor „Hilfe“); Überschriften-Hilfe am dezenten
  Info-Zeichen.
- **Für Einsteiger:** Benutzermenü → „Hilfetexte immer anzeigen“ zeigt die Feldhilfen zusätzlich als Text unter dem Feld
  (je Browser gespeichert, `lib/help.ts` `setHelpInline`).

Verwendung:

```tsx
<Field label="Beginn" htmlFor="st-ystart" help="Woche 1 ist die Woche mit diesem Tag. Ferienwochen zählen mit.">…</Field>
<Field label="Benutzername" hint="klein, ohne Leerzeichen">…</Field>         // hint → Hilfe (abwärtskompatibel)
<Field label="Code" hint="6 Ziffern" hintInline>…</Field>                    // sichtbarer Kurzhinweis (Ausnahme)
<label className="check"><input type="checkbox" /> <HelpText help="…">Ganztägig</HelpText></label>
<h2 className="with-help">Kalender-Abo <PageHelp label="Hilfe zu Kalender-Abo">…</PageHelp></h2>
```

Regeln für Hilfetexte: 1–3 Sätze, reiner Text (keine Links/Knöpfe), beschreibt Wirkung und Folgen („Jüngere Klassen
werden immer vertreten“), nicht die Bedienung des Felds. Sichtbar bleiben nur Validierungsfehler und – als Ausnahme –
eine Formatangabe, ohne die das Feld nicht ausfüllbar ist (`hintInline`).

Technik: Zustandslogik `lib/help.ts` (reine Funktionen, Tests `lib/__tests__/help.test.ts`), Komponenten
`components/Help.tsx` (`useHelp`, `HelpText`, `PageHelp`, `useDescribedBy`, `useHelpInline`), `Field` in `ui.tsx`.

## 7. Texte

- Keine erklärenden Absätze (`<p className="explain">`, `small muted`-Sätze) auf Seiten. Stattdessen `PageHelp` an der
  Überschrift bzw. `help` am Feld. `lib/__tests__/designRules.test.ts` schlägt an, wenn eine Datei mehr
  `className="explain"` enthält als im Bestand erfasst (Bestandsliste nur senken).
- Beschriftungen: Substantiv, höchstens drei Wörter, ohne Doppelpunkt („Grund“, nicht „Bitte geben Sie einen Grund ein:“).
  Optionalität als „(optional)“, Pflicht als „*“.
- Knöpfe: Verb im Infinitiv, Aktionsziel klar („Krank melden“, „Neuen Link erzeugen“).
- Meldungen: Was ist passiert + was tun („Keine Verbindung. Erneut versuchen.“); kein Fachjargon, keine IDs.
- Datum und Zeit nur über `lib/dates.ts` (`formatDate`, `formatLong`, …), Stunden „3. Std.“, Zahlen mit Leerzeichen
  vor Einheiten („45 min“, „5 %“).

## 8. Formulare

- Raster `.form-grid` (Spalten ab 220 px, am Handy einspaltig). Zusammengehöriges in `fieldset`/`legend`.
- Reihenfolge: Pflichtfelder zuerst, Seltenes unter „Erweitert“ (`details.disclosure`).
- Fehler am Feld (`Field error=`), rot, sichtbar, verknüpft; nach dem Absenden zusätzlich als Toast/Alert, wenn das
  Feld nicht im Blick ist. Keine Fehler, bevor der Nutzer etwas getan hat.
- Hauptaktion rechts unten (Dialog) bzw. am Formularende; deaktiviert nur mit erkennbarem Grund.

## 9. Leere Zustände, Fehler, Laden

- **Leer:** `Empty` mit kurzem Titel („Keine Vertretungen“), optional eine Aktion („Abwesenheit erfassen“). Kein
  Erklär-Absatz, keine großen Illustrationen.
- **Laden:** `Loading` im Bereich, nicht seitenweit; bei Aktionen Spinner im Knopf (`AsyncButton`).
- **Fehler:** `ErrorBox` mit Ursache in einem Satz und „Erneut versuchen“; 403 nennt die fehlende Berechtigung.

## 10. Tabellen

- `.table` in `.table-wrap` (Rand, eigener waagerechter Scroll – nie die Seite). Zahlen rechtsbündig (`.num`),
  Aktionen rechts (`td.actions`), Kopf klebt oben.
- Große Bildschirme: Tabellen dürfen die volle Seitenbreite nutzen; Text daneben bleibt bei der Lesebreite.
- **Handy (< 600 px):** Tabellen mit mehr als 4–5 Spalten werden zur Kartenliste: `<table className="table table-cards">`
  mit `<td data-label="Spalte">` (eine Karte je Zeile, Spaltenname links). Alternativ wenige Spalten zeigen und den
  Rest in einer Detailansicht.

## 10a. Tage × Stunden-Raster (immer DayPeriodGrid)

**Jede Ansicht „Tage × Stunden“ (oder Tage × Pausen/Bereiche) benutzt `components/grid/DayPeriodGrid`** – das Stundenplan-Raster
(`TimetableGrid` ist nur dessen Stundenplan-Variante). Nie ein neues Raster bauen; nur den Inhalt anpassen.

- **Achsen:** `days` (Name, Kürzel, Datum, Ferien, `off`, `today`, `divider`, `lanes`, `header`, `fill` für ganztägig
  Ferien/frei, `onHeadClick` für „ganzen Tag markieren“) und `rows` (Stunde, Uhrzeit, `breakAfter` für Pausenlinien,
  `heading` für Gruppenüberschriften, `onHeadClick`).
- **Zelle:** `cell(day, row)` liefert `{ content, title, blocked, tone, heat, selected, className, handlers }`.
  `blocked` = durchgehend schraffiert; `tone` = `free | good | mid | bad | muted | conflict | wish`; `heat` = 0 … 1
  (Heatmap, Anteil); `selected` = Auswahlrahmen. Ganze Zelle als Knopf: `<button className="tt-fill">`. Editoren (Antippen,
  Ziehen): `gridClassName="editing"` plus Zeiger-Ereignisse in `handlers` bzw. am Knopf.
- **Blöcke über mehrere Stunden/Spuren** (Stundenplan): `overlay` mit `rowLine()` / `dayColumnStarts()`.
- **Handy:** `mobileList` ersetzt das Raster unter 700 px durch eine Liste; sonst scrollt das Raster waagerecht, die
  Zeitspalte bleibt stehen.
- **Legende:** `GridLegend` (gleiche Farbfelder wie im Raster). Farben nur aus den Zustandsklassen in
  `styles/timetable.css` (hell/dunkel über die Farb-Tokens).
- **Schutz:** `lib/__tests__/designRules.test.ts` („Tage×Stunden-Raster nur über DayPeriodGrid“) schlägt bei eigenen
  Rastern fehl (Tagesspalten per `grid-template-columns`, Wochentage im Tabellenkopf, `tt-*`-Klassen von Hand, alte
  Raster-Stylesheets). Ausnahmen nur in `GRID_EXCEPTIONS` und mit Begründung.

## 11. Breakpoints und Navigation (A-61)

| Gerät | Breite | Navigation | Inhalt |
|---|---|---|---|
| Handy | < 600 px | Kopfzeile (Titel, Live, Schema, Konto) + **untere Leiste** mit bis zu 4 wichtigsten Zielen (Start, Stundenplan, Vertretung, Postfach bzw. Mitteilungen – je Rolle) und „Menü“, das die vollständige Navigation ausklappt | einspaltig, Rand 16 px, Platz für die untere Leiste |
| Tablet | 600–1023 px | **einklappbare Seitenleiste**: Symbolleiste (64 px), Menü-Knopf klappt sie mit Beschriftungen über dem Inhalt auf | Raster 1–2 Spalten |
| Laptop | 1024–1439 px | feste Seitenleiste (248 px) | `.page` bis 1400 px |
| Desktop | ≥ 1440 px | feste Seitenleiste | `.page` bis 1680 px, Text bis 72 Zeichen |

- Touch-Geräte (`pointer: coarse`): Knöpfe, Felder, Reiter, Menüeinträge mind. 44 px hoch (`--touch`). Namen mit
  Hilfe bekommen eine unsichtbar vergrößerte Trefferfläche (bis an das Feld, ohne die Zeile zu erhöhen).
- Kein waagerechtes Scrollen der Seite bei 360/390 px; breite Inhalte scrollen in ihrem eigenen Container.
- Das ausgeklappte Menü schließt mit Escape, Klick auf den Hintergrund oder Seitenwechsel. Beim Öffnen geht der Fokus
  ins Menü, beim Schließen zurück zum Auslöser. Meldungen (Toasts) erscheinen am Handy über der unteren Leiste.
- Media-Queries nutzen genau diese Grenzen (`max-width: 599.98px`, `max-width: 1023.98px`, `min-width: 1440px`).

## 12. Groß- und Monitoranzeigen (Vorbereitung A-62)

Die Monitor-Ansicht (`/monitor`) folgt denselben Tokens, mit eigenen Regeln: Höhe `100dvh` statt `100vh`; unter 600 px
natürliches Scrollen statt Auto-Scroll und Einträge als Karten je Klasse; Uhr als eigene Komponente (kein
Neuzeichnen der ganzen Seite pro Sekunde); bei „Bewegung reduzieren“ Laufband als statische Liste. Umsetzung im
Paket zur Monitor-Ansicht.

## 13. Prüfliste für neue oder geänderte Seiten

- [ ] Keine erklärenden Absätze; Hilfe über `help`/`PageHelp`.
- [ ] Nur Tokens, keine neuen Farben, keine Inline-Styles für Abstand/Farbe, keine Schatten auf Karten.
- [ ] 390 px ohne waagerechtes Scrollen; Tablet 820 px; Desktop 1440 px.
- [ ] Hell und dunkel geprüft; Fokus sichtbar; alles per Tastatur bedienbar.
- [ ] Status nicht nur über Farbe; Fehlertexte am Feld.
