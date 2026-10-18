---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/context, hooks, lib, styles"
stand: 2026-10-12 22:53
generator: schulmanager-regen
---

# Frontend Basis

> Kontexte, Hooks, reine Logik und Styles. Einstieg: [[Frontend Übersicht]]

## Zweck

Unterbau der Oberfläche: **`context/`** hält Anmeldezustand ([[Frontend API-Schicht]] `auth.me`), Farbschema und Toasts; **`hooks/`** kapselt Datenladen (`useApi` mit Live-Scopes, `useCollection` als gemeinsamer Cache der Stammdaten-Sammlungen, `useLive` für SSE-Ereignisse); **`lib/`** enthält reine, testbare Logik (Rechteprüfung `permissions.ts`, Stundenplan-Raster `grid.ts`, Wochen `weeks.ts`, Vertretungsdarstellung `substitution.ts`, Hilfe-Zustand `help.ts`, Sitzungs-Reset `session.ts`); **`styles/`** die Design-Tokens und Seiten-CSS.

Wichtig: `lib/permissions.ts` blendet Menüs und Routen nur **aus** (`can`, `canAccessPath`, `homePath`); die eigentliche Prüfung geschieht im Backend ([[Server deps]], [[Rollen und Rechte]]). Kontobezogene Zwischenspeicher melden sich bei `onSessionReset` an, sonst sähe das nächste Konto im selben Tab fremde Daten.

## context/

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/context/AuthContext.tsx` | 175 |  |
| `frontend/src/context/ThemeContext.tsx` | 55 |  |
| `frontend/src/context/ToastContext.tsx` | 122 |  |

## hooks/

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/hooks/misc.ts` | 67 |  |
| `frontend/src/hooks/useApi.ts` | 72 |  |
| `frontend/src/hooks/useCollection.ts` | 199 | Gemeinsamer Cache für Stammdaten-Sammlungen und Einstellungen. Mehrere Komponenten teilen sich eine Anfrage; bei Live-Änderungen… |
| `frontend/src/hooks/useInputMode.ts` | 18 |  |
| `frontend/src/hooks/useLive.ts` | 83 |  |

## lib/

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/lib/abbr.ts` | 141 | Kürzel mit Sprechblase (components/Abbr.tsx) – reine Logik ohne DOM, damit sie mit vitest prüfbar ist. - Zustand: Hover, Fokus (T… |
| `frontend/src/lib/colors.ts` | 64 | Fächerfarben: Server-Farbe verwenden, sonst stabile Farbe aus dem Kürzel ableiten. Textfarbe wird nach Kontrast (WCAG) gewählt. |
| `frontend/src/lib/csv.ts` | 78 | Minimaler CSV-Kopfzeilen-Parser für das Spalten-Mapping beim Import (rein, testbar). Erkennt Trennzeichen ; , oder Tab, berücksic… |
| `frontend/src/lib/csvFields.ts` | 88 |  |
| `frontend/src/lib/dates.ts` | 129 | Datumshilfen (lokale Zeit, ISO-Format YYYY-MM-DD). |
| `frontend/src/lib/emoji.ts` | 40 | Hilfen für Emoji in Texten (Unicode, mit Zeichenfolgen wie 👨‍👩‍👧 oder 🇩🇪 als *ein* Zeichen). |
| `frontend/src/lib/emojiData.ts` | 550 | Emoji für die Auswahl (Chats, Postfach): reine Unicode-Zeichen, nichts wird nachgeladen. Je Zeile „Emoji Suchwörter …“ (deutsch,… |
| `frontend/src/lib/format.ts` | 63 | Kleine Formatierungs- und Listenhelfer. |
| `frontend/src/lib/grid.ts` | 192 | Rasteraufbau für den Stundenplan (rein, testbar). Jeder Tag bekommt so viele „Spuren“ (Unterspalten), wie gleichzeitig liegende B… |
| `frontend/src/lib/help.ts` | 303 | Hilfe an Beschriftungen (A-60) – reine Zustandslogik ohne DOM, damit sie mit vitest prüfbar ist. Verhalten (siehe docs/DESIGN.md,… |
| `frontend/src/lib/layout.ts` | 49 | App-Rahmen (A-61): Auswahl der Einträge für die untere Leiste am Handy (< 600 px). Breakpoints und Navigationsmuster: docs/DESIGN… |
| `frontend/src/lib/live.ts` | 41 | Reine Hilfsfunktionen für Live-Ereignisse (testbar ohne Browser). |
| `frontend/src/lib/permissions.ts` | 299 | Rechteprüfung, rechtebasiertes Menü und Routing-Schutz (rein, testbar). |
| `frontend/src/lib/reportTiles.ts` | 214 | Kennzahlen des Qualitätsberichts: deutsche Titel, Einheiten, Erklärungen und die Darstellung der Werte. Hohl-/Springstunden und S… |
| `frontend/src/lib/rules.ts` | 84 | Rhythmus-/Sperrregeln (TimeRule): Beschreibung & Auswertung (rein, testbar). |
| `frontend/src/lib/session.ts` | 54 | Zentrale Sitzungs-Rücksetzung (U-01, A-09, Vorarbeit A-26). Alles, was zum angemeldeten Konto gehört und modulweit zwischengespei… |
| `frontend/src/lib/studentAbsences.ts` | 101 | Krankmeldungen von Schüler/innen (B-06): was die Oberfläche je Konto zeigt. Das Backend entscheidet (`server/absence_access.py`),… |
| `frontend/src/lib/substitution.ts` | 247 | Darstellung & Filter für Vertretungsplan-Einträge (rein, testbar). |
| `frontend/src/lib/weeks.ts` | 318 | Wochen und Unterrichtstage im 52-Wochen-System – rein, testbar. Alles, was nicht jede Woche gilt, hat eine Wochenangabe: **jede W… |

## styles/

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/styles/app.css` | 2193 | Stylesheet |
| `frontend/src/styles/monitor.css` | 147 | Stylesheet |
| `frontend/src/styles/print.css` | 155 | Stylesheet |
| `frontend/src/styles/timetable.css` | 474 | Stylesheet |
| `frontend/src/styles/tokens.css` | 200 | Stylesheet |

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`, `endpoints`, `errors`, `events`, `types`

## Wird genutzt von

- [[Feature anmeldedienste]]
- [[Feature anmelderichtlinien]]
- [[Feature api-zugaenge]]
- [[Feature channels]]
- [[Feature chats]]
- [[Feature classes]]
- [[Feature elternzugriff]]
- [[Feature formulare]]
- [[Feature konto]]
- [[Feature makeups]]
- [[Feature messages]]
- [[Feature nachrichten]]
- [[Feature students]]
- [[Feature teacher]]
- [[Feature zugangsdaten]]
- [[Frontend API-Schicht]]
- [[Frontend App und Routing]]
- [[Frontend Komponenten]]
- [[Seite AccessLettersPage]]
- [[Seite AdminPage]]
- [[Seite AnnouncementsPage]]
- [[Seite ChangePasswordPage]]
- [[Seite DashboardPage]]
- [[Seite DutiesPage]]
- [[Seite ExamsPage]]
- [[Seite HistoryPage]]
- [[Seite ImportExportPage]]
- [[Seite LicensePage]]
- [[Seite LoginPage]]
- [[Seite MasterDataPage]]
- [[Seite MonitorAdminPage]]
- [[Seite MonitorPage]]
- [[Seite PlanningPage]]
- [[Seite PrintSubstitutionsPage]]
- [[Seite ProfilePage]]
- [[Seite RightsPage]]
- [[Seite SetupPage]]
- [[Seite SignedOutPage]]
- [[Seite StudentAbsencesPage]]
- [[Seite SubstitutionsPage]]
- [[Seite TimetablePage]]
- [[Seite TwoFactorSetupPage]]
- [[Seite UsersPage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Frontend Komponenten]] · [[Abhängigkeiten]]

<!-- eigene Notizen -->
