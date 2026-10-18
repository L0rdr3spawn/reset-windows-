---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/"
stand: 2026-10-12 22:53
generator: schulmanager-regen
---

# Frontend Übersicht

> Einstieg: [[Schulmanager Architektur]] · React 19, TypeScript strikt, Vite 7, react-router-dom 7

Die Oberfläche ist eine Single-Page-App, die als `frontend/dist` vom Backend ausgeliefert wird ([[Server app]]). Kernseiten liegen in `pages/`, abgeschlossene Funktionsbereiche als **Feature-Module** in `features/<x>/` (Registry-Muster, siehe [[Frontend App und Routing]]). Alle Daten kommen über die [[Frontend API-Schicht]]; Live-Aktualisierung über SSE ([[Server events]]).

## Grundbausteine

- [[Frontend App und Routing]]
- [[Frontend API-Schicht]]
- [[Frontend Basis]] (Kontexte, Hooks, `lib/`)
- [[Frontend Komponenten]]

## Seiten (`pages/`)

| Seite | Route | Aufgabe |
|---|---|---|
| [[Seite DashboardPage]] | `/` (HomeRoute) | Startseite je Rolle: heutiger Plan und Vertretungen („für Sie“), Krankmeldung der Lehrkraft, Karten für Schüler/Eltern,… |
| [[Seite LoginPage]] | `/login` | Anmeldung mit Benutzername und Passwort, 2FA-Code bei aktivierter Zwei-Faktor-Anmeldung, Anmeldedienste (SSO), Kontowec… |
| [[Seite TimetablePage]] | `/stundenplan`, `/stundenplan/:kind`, `/stundenplan/:kind/:ref` | Stundenplan-Ansichten für Klasse, Lehrkraft, Raum und Schüler/in mit Wochenwahl; Planende verschieben Stunden per Drag… |
| [[Seite SubstitutionsPage]] | `/vertretung` | Vertretungsplan eines Tages: Einträge nach Art, Abwesenheiten erfassen (Lehrkraft, Klasse, Raum, Einzelstunde), Kandida… |
| [[Seite PlanningPage]] | `/planung`, `/planung/:tab` | Planungs-Werkstatt mit Reitern: Stundentafeln, Kurse, Generator (Job-Fortschritt, Entwurf übernehmen), Auto-Planer, Zei… |
| [[Seite MasterDataPage]] | `/stammdaten`, `/stammdaten/:tab` | Generisches CRUD für alle Sammlungen des Planungsdokuments (Standorte, Fächer, Lehrkräfte, Räume, Klassen, Schüler, Fer… |
| [[Seite ExamsPage]] | `/klausuren` | Klassenarbeiten, Klausuren und Tests eintragen, Konflikte/Hinweise anzeigen. |
| [[Seite DutiesPage]] | `/aufsichten` | Pausenaufsichten: Bereiche, Raster je Tag und Pause, faire automatische Verteilung. |
| [[Seite AnnouncementsPage]] | `/mitteilungen` | Mitteilungen an Gruppen schreiben und verwalten (im Menü inzwischen als Postfach-Ordner geführt). |
| [[Seite StudentAbsencesPage]] | `/krankmeldungen` | Krankmeldungen und Fehlzeiten von Schüler/innen: Meldung, Status, Entschuldigung, Rechte je Rolle (Eltern, Volljährige,… |
| [[Seite UsersPage]] | `/benutzer` | Benutzerverwaltung: Konten anlegen/ändern, Startpasswörter, Eltern-Kind-Verknüpfung, Sitzungen, API-Tokens, Massenanlag… |
| [[Seite MonitorAdminPage]] | `/monitore` | Vertretungsmonitore einstellen: Tage, Überschrift, Laufband, Hinweise (mit Ablaufdatum) je Standort. |
| [[Seite MonitorPage]] | `/monitor/:site?` | Vollbild-Anzeige des Vertretungsplans für Monitore im Schulhaus (Rolle monitor, Standort-Filter). |
| [[Seite LicensePage]] | `/lizenz` | Lizenz der Schule: Stand, Laufzeit, Grenzen, letzte Online-Bestätigung; neue Lizenzdatei einspielen und jetzt prüfen. |
| [[Seite RightsPage]] | `/rechte` | Rollen & Rechte: Matrix Recht × Rolle, Schulzweige der Abteilungsleitung und Zuordnungen; feste Mindestregeln sind gesp… |
| [[Seite SetupPage]] | `/einrichtung` | Einrichtungs-Assistent für eine neue Schule: Lizenz → Schuldaten → Stammdaten (auch per Import) → Schüler → Unterricht… |
| [[Seite ImportExportPage]] | `/daten` | Import/Export: Untis GPU, Schulmanager-Online-Paket, CSV mit Spalten-Mapping und Probelauf, JSON, iCal-Links. |
| [[Seite HistoryPage]] | `/verlauf` | Verlauf des Planungsdokuments (Versionen ansehen, wiederherstellen, rückgängig) und Audit-Protokoll. |
| [[Seite ProfilePage]] | `/profil` | Eigenes Profil und Sicherheit: Passwort, Zwei-Faktor (TOTP), persönlicher iCal-Link, Datenexport. |
| [[Seite AdminPage]] | `/system` | Systemseite der Administration: Version/Status, Sicherungen, Demo-Daten laden, Wartung. |
| [[Seite ChangePasswordPage]] | `/passwort` | Pflichtseite bei Startpasswort bzw. Passwortwechsel-Zwang. |
| [[Seite TwoFactorSetupPage]] | `/zwei-faktor` | Pflichtseite, wenn die Rolle laut SM_REQUIRE_2FA_ROLES Zwei-Faktor-Anmeldung braucht. |
| [[Seite PrintTimetablePage]] | `/druck/stundenplan/:kind/:ref` | Druckansicht eines Stundenplans (eigenes Layout ohne Menü). |
| [[Seite PrintSubstitutionsPage]] | `/druck/vertretung` | Druckansicht des Vertretungsplans. |
| [[Seite AccessLettersPage]] | `/druck/zugangsbriefe` | Druckansicht der Zugangsbriefe (Startpasswörter) im Browser. |
| [[Seite SignedOutPage]] | (siehe `App.tsx`) | Seite nach dem Abmelden: „Sie sind abgemeldet.“ + die in diesem Browser noch angemeldeten weiteren Konten (Klick = weit… |

## Features (`features/`)

| Feature | Aufgabe |
|---|---|
| [[Feature channels]] | Kursräume (/kursraeume, /kursraeume/:id): Material in Ordnern, Aufgaben mit Abgabe und Rückmeldung (Hausaufgaben), Pinnwand, Unte… |
| [[Feature chats]] | Chats: Einzel-, Gruppen- und Klassenchats mit Ende-zu-Ende-Verschlüsselung (Gerätschlüssel im Browser, tweetnacl), Moderation gem… |
| [[Feature classes]] | Klassen-Seite (/klassen, /klassen/:id, /klassen/neu) mit Stundentafel, Woche, Personen, Schülerkonten-Assistent und das Klassenbu… |
| [[Feature messages]] | Postfach (/postfach): Unterhaltungen, Verfassen mit An/CC/BCC und externen Adressen, Rollengruppen, Moderation, Einstellungen und… |
| [[Feature students]] | Schüler-Selbstbedienung und Akten: Atteste & Dokumente, Fehlzeiten-Akte (/fehlzeiten/:studentId), Noten (/noten), Förderinformati… |
| [[Feature teacher]] | Lehrer-Selbstverwaltung: eigenes Profil mit Zeitfenstern (/lehrkraft/profil), Anträge prüfen (/planung/antraege), Neuplanungs-Pan… |
| [[Feature konto]] | Öffentliche Konto-Seiten (Passwort vergessen/zurücksetzen, Entwicklungs-Postausgang) und Kontakt-Bausteine (E-Mail/Handy bestätig… |
| [[Feature anmeldedienste]] | Anmeldedienste (/anmeldedienste, nur Administration): Microsoft, Apple, Google und Schulkonto einrichten und testen; Verbindungs-… |
| [[Feature anmelderichtlinien]] | Anmelde-Richtlinien (/anmelde-richtlinien): wer darf sich wie anmelden; Pflicht-Verknüpfungsseite /konten-verbinden. |
| [[Feature zugangsdaten]] | Stapel-Seite /zugangsdaten/:id: Zugangsbriefe als PDF/ZIP laden oder per E-Mail versenden; ohne Menüeintrag. |
| [[Feature elternzugriff]] | Baustein (kein eigenes Modul): Abschnitt, in dem volljährige Schüler/innen festlegen, welche Bereiche ihre Eltern sehen. |
| [[Feature api-zugaenge]] | Feature-Modul „API-Zugänge“ (docs/API-ZUGAENGE.md) für die Registry (features/registry.ts). /api-zugaenge – Zugänge für Apps/KI-W… |
| [[Feature formulare]] | Feature-Modul „Formulare“ (Formular-Baukasten) für die Registry (features/registry.ts). /formulare – ausfüllen (Eltern, Schüler,… |
| [[Feature makeups]] | Feature-Modul „Nachschreibtermine“ für die Registry (features/registry.ts). /nachschreiben – Lehrkräfte (Klausur), Klassenleitung… |
| [[Feature nachrichten]] | Neues Feature (noch nicht beschrieben). |

## Querschnitt

- [[Rollen und Rechte]] (Sichtbarkeit nach Recht) · [[Abläufe]] · [[Abhängigkeiten]]

<!-- eigene Notizen -->
