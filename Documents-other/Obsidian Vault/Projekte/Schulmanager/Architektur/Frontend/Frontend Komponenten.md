---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/components/"
stand: 2026-10-12 22:56
generator: schulmanager-regen
---

# Frontend Komponenten

> Gemeinsame UI-Bausteine, die mehrere Seiten und Features teilen. Einstieg: [[Frontend Übersicht]]

## Zweck

Wiederverwendbare React-Komponenten ohne eigene Fachlogik: Rahmen/Navigation, Formular- und Dialogbausteine, Tabellen, Datei-Upload, Wochen-/Datumsnavigation, Hilfe an Beschriftungen (A-60) und der Stundenplan-Raster. Fachliche Regeln stehen in [[Frontend Basis]] (`lib/`), Daten kommen aus [[Frontend API-Schicht]] über `useApi`/`useCollection`.

Gestaltungsregeln (aus `docs/DESIGN.md`): Farben nur über Tokens, keine Inline-Styles, nur vorhandene Icons, Erklärtexte nur als Hilfe an der Beschriftung, 390 px ohne waagerechtes Scrollen, helles und dunkles Schema.

## Komponenten

| Datei | Zeilen | Aufgabe | Genutzt von |
|---|---|---|---|
| `Abbr.tsx` | 419 | Kürzel mit Sprechblase – überall, wo ein Kürzel steht (Lehrkraft, Fach, Raum, Klasse, Standort …). - `<Abbr text="MÜL"… | [[Feature channels]], [[Feature classes]], [[Feature makeups]], [[Feature messages]], [[Feature teacher]] +9 |
| `AbsentTeachersCard.tsx` | 67 | – | [[Seite SubstitutionsPage]] |
| `AccountSwitcher.tsx` | 154 | Kontowechsel im Benutzermenü: alle in diesem Browser angemeldeten Konten, mit einem Klick wechseln, weiteres Konto anme… | – |
| `CellBadges.tsx` | 71 | Kleine Abzeichen unten rechts in einer Stunde (Kalenderwoche): Hausaufgaben, Tests/Klausuren, Nachschreiben, Nachteilsa… | – |
| `ClassPlanningFields.tsx` | 60 | Planungsfeld einer Klasse (Entwurf §3, §15.2 V12, Texte §15.5): Unterrichtstage („Wie Schule (Mo–Fr)“ oder Chips). Ände… | [[Feature classes]], [[Seite MasterDataPage]] |
| `ConfirmChanges.tsx` | 99 | Bestätigung einer 409-Antwort mit Änderungsliste (R3, Entwurf §15.3 „409 für alle Bestätigungen“, §15.5 Texte): `detail… | [[Feature classes]], [[Seite MasterDataPage]], [[Seite PlanningPage]] |
| `DateNav.tsx` | 56 | – | [[Seite SubstitutionsPage]] |
| `EmojiPicker.tsx` | 172 | Emoji-Auswahl (Chats, Postfach): Knopf mit kleinem Auswahlfenster – Kategorien und Suche, alles lokal (Unicode-Zeichen,… | [[Feature messages]], [[Feature nachrichten]] |
| `EntryTable.tsx` | 208 | Tabelle der Vertretungseinträge (Arten, Filter, Zeilenaktionen). | [[Seite DashboardPage]], [[Seite PrintSubstitutionsPage]], [[Seite SubstitutionsPage]] |
| `FileList.tsx` | 205 | Liste gespeicherter Dateien (Basisdienst §9.2): Name als Download-Link, „Ansehen“ für PDF/Bilder, Größe, Art, Datum, op… | [[Feature channels]], [[Feature formulare]], [[Feature messages]] |
| `FileUpload.tsx` | 483 | Datei-Upload (Basisdienst §9.2): Ablagefläche für Drag & Drop + Auswahlknopf, mehrere Dateien nacheinander mit Fortschr… | [[Feature channels]], [[Feature formulare]], [[Feature messages]], [[Feature students]] |
| `Help.tsx` | 315 | Hilfe an Beschriftungen (A-59/A-60) – ersetzt dauerhaft sichtbare Erklärtexte. - `useHelp(inhalt)`: Grundbaustein (Ausl… | [[Feature channels]], [[Feature elternzugriff]], [[Feature formulare]], [[Seite DashboardPage]], [[Seite PlanningPage]] +2 |
| `HelpTip.tsx` | 11 | Kleines Hilfe-Symbol neben einer Beschriftung oder Überschrift – dünne Hülle um `PageHelp` (components/Help.tsx), damit… | [[Feature anmeldedienste]], [[Feature api-zugaenge]], [[Feature channels]], [[Feature chats]], [[Feature classes]] +10 |
| `Icon.tsx` | 86 | Inline-SVG-Icons (nur vorhandene Icons verwenden). | [[Feature anmeldedienste]], [[Feature anmelderichtlinien]], [[Feature api-zugaenge]], [[Feature channels]], [[Feature chats]] +34 |
| `Layout.tsx` | 379 | App-Rahmen: Kopfzeile, Seitenmenü aus `NAV_ITEMS` + Feature-Menüs, untere Leiste am Handy, `FeatureBoundary`. | [[Feature channels]], [[Feature classes]], [[Frontend App und Routing]], [[Seite DashboardPage]] |
| `Modal.tsx` | 94 | – | [[Feature anmelderichtlinien]], [[Feature api-zugaenge]], [[Feature channels]], [[Feature chats]], [[Feature classes]] +14 |
| `PasswordInput.tsx` | 57 | Passwortfeld mit Auge-Knopf zum Ein- und Ausblenden der Eingabe. Nimmt alle üblichen <input>-Eigenschaften (id, name, a… | [[Feature konto]], [[Feature zugangsdaten]], [[Seite ChangePasswordPage]], [[Seite LoginPage]], [[Seite ProfilePage]] +1 |
| `PopButton.tsx` | 85 | Knopf mit kleiner Liste (Sprechblase): Antippen/Klick öffnet, Antippen daneben oder Escape schließt. Die Liste hängt am… | [[Feature classes]] |
| `QrCode.tsx` | 28 | – | [[Feature chats]], [[Seite ProfilePage]] |
| `RuleEditor.tsx` | 110 | Editor für Sperr-/Rhythmusregeln (`TimeRule`) an Lehrkräften, Klassen und Räumen. | [[Feature teacher]], [[Seite MasterDataPage]] |
| `SearchSelect.tsx` | 221 | – | [[Feature classes]], [[Feature students]], [[Feature teacher]], [[Seite AnnouncementsPage]], [[Seite DutiesPage]] +8 |
| `TimetableGrid.tsx` | 399 | Stundenplan-Raster (Zellen, Fächerfarben, Drag & Drop, Wochenbezug). | [[Feature channels]], [[Feature classes]], [[Seite TimetablePage]] |
| `VirtualTable.tsx` | 179 | – | [[Seite HistoryPage]], [[Seite MasterDataPage]], [[Seite PlanningPage]], [[Seite StudentAbsencesPage]], [[Seite UsersPage]] |
| `WeekNav.tsx` | 115 | Wochenwahl (R3, Entwurf §8, §15.5): „‹ [Woche 12 · KW 45 · 02.11.–08.11.] › Heute“ und `week_text` des Servers. Ersetzt… | [[Feature channels]], [[Feature classes]], [[Seite DutiesPage]], [[Seite PlanningPage]], [[Seite TimetablePage]] |
| `WeekPatternInput.tsx` | 254 | Wochenangabe-Editor: „Jede Woche“ · „Ausgewählte Wochen“ (Chips 1 … Schuljahreswochen) · „Rhythmus“. Gilt überall, wo e… | [[Feature teacher]], [[Seite DutiesPage]], [[Seite PlanningPage]] |
| `emoji.css` | 91 | Stylesheet (Wochen-Chips) | – |
| `ui.tsx` | 387 | Basisbausteine: `Field`, `Alert`, `Loading`, `Empty`, `ErrorBox`, `FormErrors`, Tabs, Badges … | [[Feature anmeldedienste]], [[Feature anmelderichtlinien]], [[Feature api-zugaenge]], [[Feature channels]], [[Feature chats]] +36 |
| `weeks.css` | 131 | Stylesheet (Wochen-Chips) | – |

## Nutzt (Frontend)

- [[Feature anmeldedienste]] – `slots`
- [[Feature elternzugriff]] – `ParentAccessSection`
- [[Frontend API-Schicht]] – `client`, `endpoints`, `errors`, `files`, `types`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `ThemeContext`, `ToastContext`, `abbr`, `colors` …

## Siehe auch

- [[Frontend Übersicht]] · [[Abhängigkeiten]]

<!-- eigene Notizen -->
