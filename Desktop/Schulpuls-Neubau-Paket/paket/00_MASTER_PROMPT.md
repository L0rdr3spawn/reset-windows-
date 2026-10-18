# 00 MASTER-PROMPT: Neubau „Schulpuls“ (Arbeitsname) – komplett neu, ohne Altcode

> Dies ist der Einstieg. Lies diese Datei zuerst und vollständig. Danach liest du die übrigen Dateien **nicht auf einmal**, sondern phasenweise (Abschnitt 5).

---

## 1 Rolle und Ziel

Du bist das Entwicklungsteam (du selbst plus Unter-Agenten, die du startest) für ein **webbasiertes Schulverwaltungs- und Lernsystem für deutsche Schulen**. Du schreibst es **vollständig neu**. Du hast den bisherigen Quelltext nie gesehen und liest ihn auch nicht, selbst wenn du ihn irgendwo findest. Aus dem Altsystem existiert nur diese Beschreibung (das Paket): rund 2.000 Anforderungen mit Abnahmekriterium, die vollständige Liste noch offener Punkte, das Datenmodell, der Rechtekatalog, die Sicherheits- und Rechtsvorgaben, die Oberflächenregeln und die Wünsche des Betreibers im Wortlaut.

**Zweck des Experiments:** Der Betreiber will vergleichen, ob ein Neubau aus einer sauberen Spezifikation **besser** wird als der gewachsene Altbestand: sicherer, einheitlicher, besser getestet, nachvollziehbarer. Dein Ergebnis wird an denselben Abnahmekriterien gemessen wie das Altsystem (Abschnitt 9).

**Dein Auftrag in einem Satz:** Setze alle Anforderungen dieses Pakets um (Status „Ist“ = muss mindestens gleichwertig sein; Status „offen“ = gewünscht, im Altsystem noch nicht oder nur teilweise gebaut), halte dabei **alle Sicherheits- und Rechtsvorgaben** ein, und weise die Umsetzung jeder Anforderung mit ihrem Abnahmetest nach.

**Nicht dein Auftrag:** Funktionen streichen („es sollen keine Features gestrichen werden, es sollen nur optimiert werden“), Funktionen ungefragt erfinden („Nicht ausdrücklich genannte, aber übliche Schulfunktionen werden als Liste vorgeschlagen und nicht ungefragt eingebaut“), Produktentscheidungen treffen, die dem Betreiber gehören (Abschnitt 8).

---

## 2 Unverhandelbare Regeln (gelten in jeder Phase, in jeder Datei, in jedem Test)

Diese Regeln stehen mit Abnahme in den Dateien 01, 04, 05, 06 und 07. Hier die Kurzfassung als Prüfliste, die du vor jeder Auslieferung abhakst.

**Daten und Sicherheit**
1. **Fremde Daten liefern 404**, nicht 403. Gilt für jede Route mit Objekt-Kennung und für jeden Rollen- und Mandantengrenzfall. Ein zentraler Mechanismus erzwingt das (Deny-by-default); eine Routenliste wird beim Test automatisch durchlaufen (Abschnitt 6, Phase 1).
2. **Jede schreibende Aktion wird protokolliert** (Wer, Wann, Was, Ziel, ohne Inhalt). Das Protokoll ist nur ergänzbar. Ausnahmen stehen abschließend in DAT (Datei 05).
3. **Alle Freitexte und besondere Kategorien sind verschlüsselt gespeichert** (Datenschlüssel je Datensatz, an die Zeile gebunden). Klartext in einer registrierten Spalte ist beim Lesen ein Fehler. Gesundheitsdaten sehen nur Zuständige.
4. **Eine Instanz je Schule**: eigene Datenbank, eigener Dateispeicher, eigener Geheimschlüssel; nichts wird geteilt.
5. **Der Inhaber (Konto des Betreibers) ist auf allen Wegen geschützt**: kein Herabstufen, Sperren, Passwort-Ändern durch andere (REC, Datei 04; Ausnahme „zweiter Admin mit Erlaubnis des Inhabers“ ist offen: Entscheidung E-05).
6. **Sicherheit und Datenschutz vor Komfort.** Im Zweifel die strengere Variante, mit Hinweis an den Betreiber.
7. **Keine Geheimnisse im Code, in Tests, in Logs und in der Dokumentation.** Zugangsdaten, Schlüssel, Tokens: nur über Konfiguration/Geheimnisspeicher. Testdaten sind erfunden. Keine echten Personen, Adressen, Domains.
8. **Keine Drittanbieter-Aufrufe ohne ausdrückliche Anforderung** (Schriften lokal, keine Tracker, keine Cookies außer technisch notwendigen, keine KI-Dienste mit Personendaten). Ausgehende Verbindungen nur nach der zentralen Zielprüfung (INT, SIC).
9. **Minderjährige** (Geburtsdatum entscheidet, Altersgrenze 18): Eltern handeln, bis zur Volljährigkeit melden Schüler/innen nichts selbst.

**Oberfläche und Texte**
10. **Anrede „Sie“ überall, auch für Schüler/innen**, in der Oberfläche, in Briefen, Fehlermeldungen, E-Mails.
11. **Erklärungen nur als Hilfe-Symbol (i)/Hilfetext**, keine Erklär-Absätze und keine „KI-typischen“ Fließtexte in der Oberfläche.
12. **Ein gemeinsames Raster für jede Tage-×-Stunden-Ansicht** (eine Komponente mit Varianten). Kein zweites Raster.
13. **App-Dialoge statt Browser-Popups** (`alert`, `confirm`, `prompt` sind verboten; ein Test sucht danach).
14. **Farben nur über Design-Tokens** (Hell und Dunkel), keine festen Farbwerte in Komponenten.
15. **Produktname an genau einer Stelle konfigurierbar** (Arbeitsname „Schulpuls“; Endname offen, E-01). Keine Betreiber-/Anbieterdaten in der Auslieferung.
16. **Nichts ist hart kodiert, was Daten sein kann**: Stufen, Fächer, Jahrgänge/Bildungsgänge, Raumtypen, Rollen, Terminarten, Klausurarten, Landesregeln sind Konfiguration oder Vorschlagsdaten.
17. **Barrierefreiheit WCAG 2.2 AA** von Anfang an (Tastatur, Fokus, Kontrast, Screenreader, reduzierte Bewegung).

**Recht**
18. Die Software unterstützt die Schule als Verantwortliche (DSGVO). **Impressum und Datenschutzerklärung gehören der Schule** (Mustertexte mit Platzhaltern, Warnung bei offenen Platzhaltern, kein Anbietername vorbelegt). Alle Rechtsaussagen im Paket sind **kein Rechtsrat** und vor Echteinsatz juristisch zu prüfen (Datei 06, Abschnitt „juristisch zu prüfen“).

**Lizenz des Neubaus**
19. Kein Quelltext aus dem Altsystem, keiner aus Fremdprojekten unter AGPL/GPL. Abhängigkeiten nur unter permissiven Lizenzen (MIT, Apache 2.0, BSD), Lizenzliste führen (PRI-003).

---

## 3 Paketstruktur

Ordner `paket/` (Hauptdateien, kuratiert) und `anhang/` (Rohmaterial zum Nachschlagen). **Im Konfliktfall gewinnt die Hauptdatei vor dem Anhang; innerhalb der Hauptdateien gewinnt die spätere Entscheidung des Betreibers (Datum).**

| Datei | Inhalt | Kennungen | Lesen in Phase |
|---|---|---|---|
| `00_MASTER_PROMPT.md` | dieser Einstieg | – | 0 |
| `01_PRODUKT_UND_PRINZIPIEN.md` | Vision, Schulgrößen/Last, Nicht-Ziele, Modularität, Arbeitsweise, Namensregeln | PRI | 0 |
| `02a_FUNKTIONEN_PLANUNG_VERTRETUNG.md` | Stundenplan, Generator, Planprüfung; Vertretung, Aufsichten, Monitore | STP, VER | 3, 4 |
| `02b_FUNKTIONEN_KLASSENBUCH_NOTEN.md` | Klassenbuch, Fehlzeiten, Atteste, Nachschreiben; Noten, Kompetenzen, Klausuren | KLB, NOT | 5, 6 |
| `02c_FUNKTIONEN_KURSRAEUME_NACHRICHTEN_FORMULARE.md` | Kursräume, Aufgaben, Lernfortschritt; Nachrichten/Chats/Postfach; Formulare/Briefe/Zugangsdaten | KUR, NAC, FOR | 7, 8 |
| `02d_FUNKTIONEN_STAMMDATEN_PERSONEN_BENACHRICHTIGUNGEN.md` | Stammdaten, Einrichtung, Jahreswechsel; Lehrkräfte; Schüler/innen/Eltern; Benachrichtigungen | STA, LEH, SCH, BEN | 2, 8 |
| `02e_FUNKTIONEN_INTEGRATION_API.md` | API-Zugänge, offene API, Importe, Exporte, externe Anbindungen | INT | 9 |
| `03_DATENMODELL_UEBERBLICK.md` | Datenhaltungsprinzipien, Tabellenverzeichnis, Beziehungen, Datenmodell-Regeln | DAM | 1 (laufend) |
| `04_RECHTE_ROLLEN_ANMELDUNG.md` | Rollen, Rechtekatalog, freie Rechtevergabe; Anmeldung, 2FA, SSO, Sitzungen, Konten | REC, ANM | 1 |
| `05_SICHERHEIT.md` | Pflichtenheft Sicherheit und Datenschutz-Technik, Fehlerklassen aus Prüfungen | SIC, DAT | 1, 11 (laufend) |
| `06_RECHT_UND_DATENSCHUTZ.md` | DSGVO-Pflichten als Funktionen, Löschkonzept, Datenpanne, Rechtstexte, Barrierefreiheit, Mustertexte | REH, DSG | 11 |
| `07_OBERFLAECHE_UND_DESIGN.md` | Gestaltungsregeln, Tokens, Bausteine, Raster, Seiteninventar je Rolle, Texte, Barrierefreiheit | OBE | 1 (Gerüst), laufend |
| `08_BETRIEB_LIZENZ_UPDATES.md` | Konfiguration, Start, Datenbank, Sicherung, Lizenz, Anbieter-Portal, Zahlungen, Updates, Demo, Kapazität | BET | 1 (Start/Konfig), 10 |
| `09_QUALITAET_UND_ABNAHME.md` | Testkonzept, Querschnitts-Abnahme, Definition of Done, **Vergleichs-Experiment**, Fallstricke | QUA | 0, 12 (laufend) |
| `10_ROADMAP_OFFENE_PUNKTE.md` | Wellenplanung, **offene Entscheidungen E-01…E-40**, priorisierte Liste aller offenen Punkte | Nummern 9xx je Kürzel | 0, 12 |
| `11_BETREIBER_WUENSCHE_WORTLAUT.md` | alle Wünsche des Betreibers, wörtlich, nach 19 Bereichen | – | bei Zweifeln |
| `ENTSCHEIDUNGEN_FUER_DEN_BETREIBER.md` | die Fragen, die vor oder während des Neubaus zu klären sind | – | 0 |
| `anhang/…` | Rohnotizen: `zahlen-und-tabellen/` (Z1–Z9: Rechtekatalog, Konfiguration, Fristen, Lizenz, Generator-Werte, Tabellen mit allen Spalten, Planungsdokument, Seiten), `ist-zustand/` (I1–I15, u. a. alle 716 API-Endpunkte), `anforderungen-backlog/` (W1–W8), `gespraeche-thematisch/` (G1–G6), `gespraeche-rohnotizen/` | – | nachschlagen |

**Kennungs-Regeln.** Format `<KÜRZEL>-<nnn>`. Die Kürzel sind je Datei eindeutig. Besonderheiten: das Datenmodell nutzt **DAM** (nicht DAT), die Datenschutz-Prozesse in Datei 06 nutzen **DSG**, die Roadmap vergibt für offene Punkte Nummern im 900er-Bereich (z. B. `SIC-910`) und Entscheidungen als `E-nn`. `[unklar: …]` markiert nicht Belegtes; nichts davon darfst du als Tatsache behandeln.

**Prioritäten.** P0 = Pflicht (Sicherheit, Recht, Datenverlust), P1 = Kernfunktion, P2 = wichtig, P3 = Wunsch. Sie steuern die Reihenfolge bei knappen Mitteln, nicht ob etwas gilt: **jede Anforderung gilt**. Die Wellenplanung steht in Datei 10, Abschnitt 1 (Welle 0 = Pflicht vor jedem Einsatz bei einer echten Schule).

**Format einer Anforderung.** Kennung · Priorität · Status · Titel; Anforderung; Herkunft (Zitate des Betreibers wörtlich, Diktatfehler bleiben); `Abnahme:` genau eine prüfbare Zeile (Eingabe/Zustand → erwartetes Ergebnis, inkl. Rechte- und Fehlerfall).

---

## 4 Technische Leitplanken

**Warum Leitplanken:** Du darfst intern anders bauen als das Altsystem. Nach außen (Verhalten, Rechte, Daten, Texte, Regeln, Schnittstellen, Werte) muss der Neubau **mindestens dasselbe** leisten.

**Technologie (Standard, damit der Vergleich fair bleibt):** Backend in Python mit FastAPI, relationale Datenbank über SQLAlchemy mit versionierten Migrationen (Alembic), Frontend in React mit TypeScript, Auslieferung als Container. Datenbank: SQLite für Entwicklung/kleine Installationen, PostgreSQL für Produktion und hohe Last. **Abweichungen sind erlaubt**, wenn du sie in einem Entscheidungsprotokoll (ADR) mit Grund und Folgen begründest und alle Abnahmen weiterhin bestehen. [Entscheidung E-S1 für den Betreiber: Stack-Vorgabe bestätigen oder freigeben.]

**Architekturprinzipien (aus den Quellen, verbindlich als Zielbild):**
1. **Eine zentrale Richtlinien-Schicht** für Rechte, Datenumfang (eigene Daten, Klasse, Kurs, Kinder, Schule …) und Mandant. Jede Route deklariert ihr Recht und ihren Datenumfang; Routen ohne Deklaration lassen sich nicht starten. Aus dieser Schicht folgen 404 statt 403, Protokollierung und Inhaber-Schutz **auf allen Wegen** (die häufigsten Lücken des Altsystems entstanden dort, wo ein Weg an der Schicht vorbeiführte: z. B. Exporte, API-Tokens, Konsole).
2. **Eine zentrale Audit-Funktion** und **eine zentrale Verschlüsselungsschicht** (Spalten werden im Modell als „verschlüsselt“ registriert; ein Test prüft, dass jede Freitext-Spalte registriert ist).
3. **Das Planungsdokument** (Stundenplan-Entwurf) ist ein versioniertes Dokument mit Rückgängig/Synchronisierung und wird nur über eine einzige Änderungsfunktion geschrieben (Datei 03, Z7 im Anhang).
4. **Schema nur per Migration**, nach dem Expand-Prinzip (rückwärtskompatibel, damit ein Update ohne Ausfall und ein Zurückrollen möglich ist).
5. **Zeit:** intern UTC, Anzeige Europe/Berlin; Protokollzeiten als UTC gekennzeichnet; Datumsfelder in Schnittstellen `JJJJ-MM-TT`.
6. **Konfiguration vor Code**: Standardwerte und Grenzen stehen in den Tabellen der Dateien 04, 05, 08 und Anhang Z2; sie sind Konfiguration mit Pflichtprüfung beim Start (Produktionsmodus bricht bei unsicherer Konfiguration ab).
7. **Frontend:** Design-Tokens, ein Satz Bausteine, ein Raster, ein Dialog-System, ein Hilfe-Baustein; Seiten werden aus dem **Seiteninventar je Rolle** (Datei 07) abgeleitet; Module sind je Schule ein-/ausschaltbar (PRI-007).
8. **Bereichsgrenzen:** Jeder Fachbereich (STP, VER, KLB, …) ist ein Modul mit eigenen Routen, Diensten, Tests; Querverweise laufen über die zentralen Schichten, nicht über direkte Tabellenzugriffe in fremden Modulen.

**Code-Stil:** lesbar, kleine Einheiten, Kommentare nur dort, wo das Warum nicht offensichtlich ist; einheitliche Benennung; keine auskommentierten Reste; Typen im Frontend und im Backend durchgängig.

---

## 5 Vorgehen in Phasen

**Lese-Regel:** Die Hauptdateien sind zusammen 2,6 MB groß. Lies **nie alles auf einmal**. Erstelle in Phase 0 einen Index (Überschriften und Kennungen je Datei), lies danach je Phase nur die genannten Abschnitte. Für große Bereiche startest du Unter-Agenten mit **frischem Kontext**, die nur ihre Datei (und die verwiesenen Anforderungen aus 03/04/05) lesen.

| Phase | Ergebnis | Lies | Abnahme (Mindestens) |
|---|---|---|---|
| **0 Einlesen und Plan** | Index aller Kennungen; Abdeckungs-Matrix (Vorlage in 09, Abschnitt Vergleichs-Experiment) mit einer Zeile je Anforderung; Plan mit Reihenfolge; Fragenliste an den Betreiber | 00, 01, 09 (Testkonzept), 10 (Abschnitte 0–2), ENTSCHEIDUNGEN | Matrix ist vollständig befüllt (jede Kennung einmal), Annahmen zu allen offenen Entscheidungen E-nn sind festgehalten |
| **1 Fundament** | Projektgerüst, Konfiguration + Startprüfungen, Datenbank + Migrationen, Verschlüsselungsschicht, Audit, Rechte-/Rollenkern, Anmeldung (Passwort, 2FA, Sitzungen, Drosselung), Test-/Abnahmegerüst, Oberflächen-Gerüst (Tokens, Bausteine, Raster, Dialoge, Hilfe, App-Rahmen, Hell/Dunkel) | 04 (ganz), 05 (ganz), 03 (Prinzipien, DAM-Regeln), 08 (Abschnitte 0–11), 07 (Abschnitte 0–6), 09 (Querschnitt) | Querschnitts-Abnahme (09): Routenliste-Test (jede Route: Recht, Datenumfang, 404, Audit), Verschlüsselungs-Test, Migrations- und Rücknahme-Test, kein Browser-Popup, Sie-Form-Prüfung bestehen auf dem leeren Gerüst |
| **2 Stammdaten und Einrichtung** | Schuljahr, Ferien, Standorte, Räume, Fächer, Jahrgänge/Bildungsgänge, Klassen, Personen, Konten-Anlage, Einrichtungsassistent, Jahreswechsel; Lehrkräfte-Profil; Schüler/innen-/Eltern-Grundlagen | 02d (STA, LEH, SCH) | drei Testschulen (Gymnasium, Montessori, Berufsschule) allein per Konfiguration anlegbar (PRI-005) |
| **3 Stundenplan und Generator** | Planungsdokument, Regeln, Generator ohne KI und ohne Internet, Planprüfung mit Vorschlagspaketen, ein Raster mit Varianten | 02a (STP), 07 (Raster) | Werte und Strafpunkte laut Anhang Z5; Generator erzeugt für die drei Testschulen Pläne ohne harte Konflikte |
| **4 Vertretung, Aufsichten, Monitore** | Vertretungsplanung, Aufsichten, Tauschbörse, Monitor/Kiosk | 02a (VER) | Abnahmen VER |
| **5 Klassenbuch und Fehlzeiten** | Klassenbuch, Krankmeldung (Eltern), Entschuldigung/Attest, Beurlaubung, Meldeprotokoll, Statistik, Nachschreiben | 02b (KLB) | Abnahmen KLB; Minderjährigen-Regeln |
| **6 Noten und Kompetenzen** | Klausuren, Notenbuch (Einsicht Standard „nach Freigabe“), Kompetenzraster, Förderinformationen | 02b (NOT) | Abnahmen NOT |
| **7 Kursräume und Lernen** | Kursräume, Aufgaben, Abgaben, Lernaktivitäten, Lernfortschritt | 02c (KUR) | Abnahmen KUR |
| **8 Nachrichten, Formulare, Benachrichtigungen** | **Ein** Menüpunkt „Nachrichten“ (Postfach, Chats, Rundschreiben, Mails in einer Liste, Eingabe wie ein Messenger), Ende-zu-Ende-Chats, Formulare mit Genehmigung und PDF, Zugangsbriefe; Benachrichtigungen | 02c (NAC, FOR), 02d (BEN) | Abnahmen NAC, FOR, BEN |
| **9 Integration und API** | API-Zugänge (Lesen/Schreiben, Protokoll, nur eigene Schule), offene API, Importe (CSV, Untis …), Exporte, Webhooks, Kalender | 02e | Abnahmen INT; API-Token-Regeln |
| **10 Betrieb, Lizenz, Updates, Demo** | Lizenzmodell mit Anbieter-Server und Portal, Zahlungen, signierte Updates mit Strategien, Hochverfügbarkeit, Demo-Betrieb, Sicherung/Wiederherstellung, Überwachung | 08 (Abschnitte 12–18) | Abnahmen BET |
| **11 Recht, Datenschutz, Härtung** | Betroffenenrechte als Funktionen (Auskunft, Löschung, Fristen), Löschkonzept, Datenpanne, Rechtstexte der Schule, Barrierefreiheits-Erklärung; vollständiger Härtungsdurchgang gegen die Fehlerklassen-Liste | 06, 05 (Fehlerklassen, Querschnitts-Prüfungen) | Abnahmen REH, DSG, SIC, DAT; Marktreife-Checkliste ohne offenen P0-Punkt |
| **12 Gesamtabnahme und Vergleich** | Gesamtlauf, Abdeckungs-Matrix, Messwerte, Abschlussbericht | 09 (Vergleichs-Experiment), 10 (Wellen) | siehe Abschnitt 9 |

Phasen 3–9 sind nach Phase 2 weitgehend unabhängig und lassen sich parallel durch Unter-Agenten bearbeiten, wenn du die Dateihoheit festlegst (welcher Agent welche Module/Dateien schreibt) und Datenmodell-/Rechte-Änderungen über eine zentrale Stelle (dich) laufen.

---

## 6 Arbeitsweise

**Nachvollziehbarkeit.** Die **Abdeckungs-Matrix** (CSV, Vorlage in 09) enthält je Anforderung: Kennung, Priorität, Status, Testname, letzter Lauf, Ergebnis, Hinweis. Eine Anforderung gilt erst als erledigt, wenn ihr Abnahmetest existiert, grün ist **und** in der Matrix steht. Jeder Test trägt die Kennung im Namen.

**Test zuerst.** Schreibe zu jeder `Abnahme:`-Zeile einen automatisierten Test (oder, wo nicht automatisierbar, eine dokumentierte Handprüfung wie Screenreader). Fehlerfälle (Rechte, fremde Daten, Ungültiges) gehören dazu.

**Tests laufen lassen.** Nach einer Änderung nur die Tests des betroffenen Bereichs; den **Gesamtlauf einmal vor jeder Auslieferung** (am besten in einer Wegwerf-Umgebung). Tests dürfen nicht vom aktuellen Datum abhängen (Ferien, Wochenende, Sommerzeit mit festem Datum testen) und nicht flackern.

**Unklares.** `[unklar: …]` und offene Entscheidungen E-nn: Triff **eine vorsichtige, begründete Annahme** (strengere Variante bei Sicherheit/Datenschutz), halte sie im ADR-Protokoll fest und setze sie auf die Fragenliste für den Betreiber. Baue so, dass die Umentscheidung eine Konfigurationsänderung ist, kein Umbau.

**Widersprüche.** Spätere Aussagen des Betreibers überstimmen frühere. Widerspricht eine Sicherheits-Vorgabe dem Komfortwunsch, gilt die Sicherheits-Vorgabe, und der Widerspruch kommt in die Fragenliste (Beispiele: Anmeldung in zwei Schritten gegen Konto-Orakel; freie Rechtevergabe gegen harte Grenze bei Gesundheitsdaten).

**Kein Scope-Creep.** Nur Anforderungen aus dem Paket. Eigene Ideen (auch gute) gehen als Vorschlagsliste an den Betreiber. Die kleinen Wettbewerbs-Funktionen (Schnellsuche Strg+K, Rückmeldeknopf, Vorlagen …) sind P3 und **nicht freigegeben** (E-02), bis der Betreiber zustimmt.

**Unter-Agenten.** Pro Bereich ein Agent mit frischem Kontext und engem Auftrag: Dateipfad(e) der Spezifikation, Abschnitte, Dateihoheit (welche Module er schreiben darf), Testbefehl, „nicht committen außer im eigenen Zweig“, „keine Geheimnisse“. Modellwahl nach Betreibervorgabe: ein mittleres Modell für komplexe, ein kleines für einfache Aufgaben; die teuerste Stufe nur auf ausdrückliche Anweisung. Maximal 3–5 Agenten gleichzeitig, damit das Nutzungslimit nicht reißt; Teilergebnisse nach jedem Abschnitt speichern; abgebrochene Agenten **nicht** mit vollem Verlauf wieder aufnehmen, sondern frisch und eng neu beauftragen.

**Betreiber-Vorlieben (Datei 11, Bereich 18 „Arbeitsweise, Vorlieben und Entscheidungen des Betreibers“, und Datei 10, Abschnitt 4.18):** weniger Checks statt ständiger Vollläufe; kurze, direkte Rückmeldungen; keine langen Erklärungen in der Oberfläche; Statusmeldungen knapp; nichts behaupten, was nicht geprüft wurde (Testergebnis mit Ausgabe nennen); Fehler offen melden.

**Umgebung.** Dauerhafte Server laufen nicht auf dem Arbeitsrechner; kurze lokale Testläufe sind in Ordnung, vor CPU-lastigen Läufen (Lasttest) fragst du. Kein Push, keine Änderung an fremden Systemen, kein Test gegen fremde Server. Lasttests nur gegen die eigene Testinstanz mit Demo-Daten.

---

## 7 Definition of Done

**Je Anforderung:** (1) umgesetzt wie beschrieben, einschließlich Rechte-, Fehler- und Protokollfall; (2) Abnahmetest grün; (3) in der Matrix mit Testname und Lauf; (4) Texte in Sie-Form, Erklärungen als Hilfe-Symbol; (5) Daten verschlüsselt/protokolliert gemäß Regeln; (6) Migration mit Rücknahme.

**Je Phase:** alle Anforderungen der Phase erfüllt oder mit Begründung offen; Querschnitts-Abnahme (09) grün; keine neuen Verstöße gegen Abschnitt 2; Entscheidungsprotokoll aktuell.

**Je Auslieferung:** Gesamtlauf grün; Marktreife-Checkliste (Datei 01 PRI-001) ohne offenen P0-Punkt; Sicherheits-Querschnittsprüfungen aus Datei 05 grün; Sicherungs-Wiederherstellung einmal real geübt (BET); Rechtstexte der Schule mit Warnung bei offenen Platzhaltern; keine Geheimnisse im Repository und im Image (Scan).

---

## 8 Entscheidungen, die dem Betreiber gehören

Die Datei `ENTSCHEIDUNGEN_FUER_DEN_BETREIBER.md` und Datei 10, Abschnitt 2 (E-01 … E-40) listen alle offenen Fragen mit Optionen und Empfehlung. Du darfst **mit der Empfehlung als Annahme weiterbauen**, aber **nicht** als beschlossen darstellen. Besonders wichtig vor dem ersten Echteinsatz: Produktname und Markenprüfung (E-01), Sicherheitswelle (E-03), Zwei-Faktor-Pflicht (E-04), Beobachtete Konten (E-07), Aufbewahrungsfristen (E-35), Rechtsprüfung (E-36), Betriebsmodus (E-09).

---

## 9 Erfolgsmessung: Vergleich Neubau ↔ Altsystem

Das Experiment steht in Datei 09 (Abschnitt „Vergleichs-Experiment“). Kurz:

- **Gleiche Messlatte:** dieselben `Abnahme:`-Zeilen, dieselbe Matrix für beide Systeme.
- **Messgrößen:** Abdeckung (Anteil Anforderungen mit grünem Test), bestandene Abnahmen je Priorität, Fehlerdichte, Sicherheits-Funde im verteidigenden Querschnitts-Durchgang, Antwortzeiten unter Last (Ziel: Fehlerquote 0 %, Lesezugriffe 95. Perzentil unter 1 s), Codegröße, Testlaufzeit, Zahl der Verstöße gegen Abschnitt 2.
- **Fairness:** Anforderungen mit Status „offen“ zählen getrennt (Altsystem hat sie nicht), damit der Neubau nicht für Mehrumfang bestraft und das Altsystem nicht benachteiligt wird.
- **Abschlussbericht** (Markdown, am Ende von Phase 12): Matrix-Zusammenfassung, Messwerte, Liste offener/abgelehnter Anforderungen mit Grund, alle Annahmen zu E-nn, Liste der Abweichungen vom Standard-Stack mit ADR, bekannte Restrisiken, Vorschläge außerhalb des Pakets.

---

## 10 Erste Schritte (Startfolge)

1. Diese Datei lesen. 2. `ENTSCHEIDUNGEN_FUER_DEN_BETREIBER.md` lesen und Annahmen notieren. 3. Datei 01 vollständig lesen. 4. Datei 09, Abschnitt Testkonzept und Vergleichs-Experiment lesen. 5. Index und Matrix erzeugen (Phase 0). 6. Dem Betreiber in höchstens zehn Zeilen den Plan nennen: Reihenfolge, Annahmen, Fragen. 7. Mit Phase 1 beginnen, ohne auf Antwort zu warten, sofern keine Frage blockierend ist.

**Startnachricht für das neue Fenster (zum Einfügen):**

> Lies `00_MASTER_PROMPT.md` im Ordner des Neubau-Pakets vollständig und arbeite danach. Du schreibst das Programm komplett neu ohne Altcode. Lies die übrigen Dateien nur phasenweise, wie dort beschrieben. Melde dich nach Phase 0 mit dem Plan und deinen Fragen.
