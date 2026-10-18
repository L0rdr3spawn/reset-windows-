# 09 · Qualität und Abnahme (QUA)

Stand: 2026-10-18 · Kürzel: QUA · Geltung: gesamtes Paket („Schulpuls“, Neubau ohne Altcode)

Diese Datei legt fest, **wie geprüft wird**, **wann etwas fertig ist** und **wie Neubau und heutiger Stand fair verglichen werden**. Sie enthält keine Fachfunktion. Jede Fachanforderung der anderen Paketdateien (STP, VER, KLB, NOT, KUR, NAC, FOR, STA, LEH, SCH, REC, ANM, DAT, BEN, INT, BET, OBE, SIC, REH, PRI) wird hier über ihre Kennung und ihre Abnahme-Zeile geprüft.

## Lesehilfe

- Kennung `QUA-nnn`, Priorität `P0` (Pflicht/Sicherheit/Recht) bis `P3` (Wunsch). Sicherheit und Recht sind immer P0.
- `Status: Ist` = im heutigen Stand (Alt) so gebaut bzw. so praktiziert. `Status: offen` = gewünscht, im Alt nicht vorhanden oder nicht belegt.
- **„Alt“** = heutiger Stand der Software (Bestand). **„Neubau“** = Neuentwicklung nach diesem Paket.
- **[Festlegung]** = Wert, den diese Spezifikation setzt (nicht aus dem Bestand). Er wird vor Messbeginn eingefroren und danach nur mit Datum und Begründung geändert.
- **[unklar: …]** = Quelle nennt keinen Wert; nichts erfunden.
- Bestandszahlen (Teststände, Funde, Messwerte) stammen aus Arbeitsdokumenten und Gesprächen vom 10.–17.10.2026. Testzahlen verschiedener Läufe sind **nicht vergleichbar** (Zählweise und Umfang wechselten); sie dienen nur als Orientierung.
- Wunsch-Wortlaut des Betreibers steht als Zitat. Bei Widerspruch gilt die spätere Entscheidung.

## 0. Begriffe

| Begriff | Bedeutung |
|---|---|
| Abnahmetest | Automatisierter (oder mit Datum, Prüfer, Beleg protokollierter) Test, der genau eine Abnahme-Zeile einer Anforderung belegt. |
| Querschnitts-Abnahmetest | Test, der über **alle** Routen bzw. Funktionen derselben Art läuft (Abschnitt 2). |
| Routen-Register | Maschinenlesbare Liste aller Endpunkte mit Bereich, Recht, Schutzart, Audit-Einstufung, verschlüsselten Feldern, Demo-Freigabe, Modul. Alt: 716 Endpunkte in 24 API-Bereichen. |
| Rollenfeld | Feste Menge von Testpersonen (Abschnitt 2.1), gegen die jede Route geprüft wird. |
| Beispielschule | Synthetische Schule mit festem Startwert (Abschnitt 1.5). |
| Wegwerf-Instanz | Isolierte, nur lokal erreichbare Instanz mit eigener Datenbank, eigenem Schlüssel und Beispielschule; wird nach der Prüfung entfernt. |
| Feste Uhr | Von außen gesetzte Uhrzeit/Datum in Tests; kein Test liest die echte Systemuhr. |
| Gate | Abnahme-Tor am Ende einer Phase (Abschnitt 6). Ohne bestandenes Gate beginnt die Folgephase nicht. |
| Defekt / Fund | Reproduzierbare Abweichung von einer Abnahme-Zeile oder einem Querschnittstest. Schwere: kritisch (Zugriff auf fremde Daten, Rechteumgehung, Datenverlust), hoch (Kernfunktion falsch oder Schutzmaßnahme umgehbar), mittel, niedrig. |
| Abdeckungs-Matrix | Tabelle aller Anforderungs-Kennungen mit Status in Alt und Neubau (Abschnitt 4). |

---

## 1. Testkonzept

### 1.1 Grundsätze und Testebenen

- **QUA-001** · P0 · Status: Ist — **Nachweisregel.** Eine Anforderung gilt erst als erfüllt, wenn ihre Abnahme-Zeile durch einen **ausgeführten** Test belegt ist. Code lesen, Behauptung oder „lokal geprüft“ belegen nichts. Hintergrund: Der Betreiber meldete „ich habe viel fehler gefunden die ich schon gemeldet hatte die du noch nciht umgesetzt hast“; seitdem gilt: kein Punkt ist erledigt, der nicht im Code **und** in einem Test belegt ist.
  - Abnahme: Prüfskript über die Abdeckungs-Matrix: Jede Kennung mit Status „erfüllt“ nennt mindestens eine Test-Kennung und ein Lauf-Datum; Kennung ohne Test-Kennung → Skript meldet „nicht belegt“ und setzt den Status auf „fehlt“.

- **QUA-002** · P1 · Status: Ist — **Ebenen 1–4 (ohne Browser, ohne Netz).** Der Neubau führt die Ebenen E1 bis E8 (Tabelle). E1 bis E4 laufen ohne Browser, ohne Netzzugang und ohne Fremddienste.
  - Abnahme: Testbericht listet je Ebene Anzahl, Dauer, Ergebnis; Lauf von E1–E4 in einem Container ohne Netzzugang ist grün.

| Ebene | Name | Prüft | Typischer Auslöser |
|---|---|---|---|
| E1 | Logik | reine Fachlogik ohne Server und Datenbank: Planung/Generator, Vertretung, Wochen/Kalender, Noten, Kompetenzen, Lernaktivitäten, Formulare, Regeln; Oberfläche: Hilfe-Zustände, Fehlerübersetzung, Raster, Rechte-Navigation | Änderung im Bereich |
| E2 | Schnittstelle | jede Route gegen frische Datenbank und kleine Beispielschule: Positiv-, Negativ-, Rechte-, Fehlerfall | Änderung im Bereich |
| E3 | Querschnitt | generische Tests über das Routen-Register (Abschnitt 2) | Gate, Änderung am Register/Schutzdienst |
| E4 | Daten | Migrationen, Altdokumente, Export/Import-Rundläufe, Verschlüsselungs-Marker-Suche, Datenübernahme | Schemaänderung, Gate |
| E5 | Browser | Rundgang je Rolle (1280 und 390 px, hell/dunkel, Tastatur, Touch), Dialoge, Hilfe, Barrierefreiheit | Oberflächenänderung, Gate |
| E6 | Last | Antwortzeiten, Durchsatz, Spitzen (1.6) | Gate, Änderung am Kernpfad |
| E7 | Sicherheit | defensive Abnahme auf Wegwerf-Instanz im Produktivmodus (1.8) | Gate, Release |
| E8 | Betrieb | Update/Rollback, Wiederherstellung mit Dateien, Probelauf an Datenbank-Kopie, Alarm-Auslösung | Release, vierteljährlich |

- **QUA-003** · P1 · Status: offen — **Ebenen 5–8 sind Pflicht.** Im Alt fehlten automatisierte Browser-Tests (Browser-Prüfungen liefen von Hand oder ad hoc; „keine E2E-Tests“), ein echter Lauf des Lastskripts stand aus, die Wiederherstellung war nur an 5 Dateien geprüft.
  - Abnahme: Vor Gate G5 (Abschnitt 6) liegt je Ebene E5–E8 mindestens ein Lauf mit Datum, Umgebung und Ergebnis im Messprotokoll vor.

- **QUA-004** · P2 · Status: offen — **Niedrigste mögliche Ebene.** Verhalten, das auf Ebene E1/E2 prüfbar ist, wird dort geprüft. Browser-Tests nur für Verhalten, das nur im Browser sichtbar ist (Layout, Tastatur, Touch, Dialoge, Hilfe-Zeitgeber, Zoom, Fokus).
  - Abnahme: Stichprobe von 10 Browser-Tests im Review; keiner ist als API- oder Logik-Test ersetzbar.

- **QUA-005** · P1 · Status: Ist — **Nur geänderte Bereiche testen; Gesamtlauf einmal vor dem Deploy.** Der Betreiber: „du hast jetzt fast 1400 Checks gemacht. Das ist ein bisschen viel.“ und „alles, was schon gecheckt wurde und nicht mehr gecheckt werden muss, nicht geändert wurde, musst du fürs erste nicht mehr checken.“ Entwicklungsschleife = Tests der geänderten Bereiche plus Basis-Querschnitt; Gesamtlauf nur im Gate (Abschnitt 6) und vor dem Aufspielen.
  - Abnahme: Das Lauf-Protokoll nennt zu jeder Änderung die betroffenen Bereiche und die ausgeführten Tests; ein Entwicklungslauf führt nur diese aus; der Gesamtlauf erscheint genau einmal je Auslieferung.

- **QUA-006** · P2 · Status: Ist — **Bereichs-Testkarte.** Eine automatisch erzeugte Karte ordnet jeder Testdatei einen Bereich zu und nennt je Bereich den Aufruf für Backend- und Oberflächen-Tests (Alt: 25 Bereiche mit Aufrufen). Eine Selbstprüfung der Karte meldet Tests ohne Bereich und Bereiche ohne Tests.
  - Abnahme: Karten-Prüfung gibt 0 Tests ohne Bereich und 0 Bereiche ohne Test aus; Änderungsliste → Karte liefert die Testbefehle.

- **QUA-007** · P2 · Status: offen — **Ein einziger Aufrufweg.** Backend- und Oberflächentests laufen mit je **einem** dokumentierten Befehl aus dem Projektwurzelverzeichnis (Alt: uneinheitliche Importpfade, nur ein Aufrufweg funktionierte).
  - Abnahme: Frisches Klonen + zwei dokumentierte Befehle (Backend, Oberfläche) starten alle Tests ohne Vorarbeit.

- **QUA-008** · P1 · Status: offen — **Mindestumfang.** Jede Route hat mindestens einen Positiv- und einen Negativtest (Rechte oder Eingabe); jeder Bereich hat mindestens einen Logik-Test. Hintergrund (Alt): Tests waren die schwächste Dimension (Ø 63,7 von 100); Bereich Branding hatte 0 Tests, Klassenbuch 13, bei Chats waren 15 von 27 Routen im Test.
  - Abnahme: Auswertung Register × Test-Kennzeichnung: „Routen ohne Test“ = 0 für alle P0- und P1-Bereiche.

- **QUA-009** · P0 · Status: Ist — **Regressionstest je Fix.** Zu jeder Fehlerbehebung gehört ein Test, der den Fund nachstellt.
  - Abnahme: Im Fund-Register (QUA-011) steht je behobenem Fund eine Test-Kennung und der Nachweis „vor der Behebung rot, danach grün“.

- **QUA-010** · P1 · Status: Ist — **Rückmeldungen der Anwender sind Prüfquelle.** Rückmeldungen des Betreibers und der Testlisten haben Vorrang vor dem Backlog. Jede Rückmeldung erhält eine Fund- oder Anforderungs-Kennung, einen Status und einen Test.
  - Abnahme: Rückmeldeliste: jede Zeile hat Kennung, Datum, Status (offen/behoben/abgelehnt mit Begründung) und Test-Kennung; keine Zeile „behoben“ ohne Test.

- **QUA-011** · P1 · Status: Ist — **Fund-Register.** Jeder Fund hat Kennung, Schwere, Entdeckungsweg (Abnahme, Prüfrunde, Anwender-Meldung, Sicherheitsabnahme), Status (bestätigt/falsch/unklar → behoben/offen) und wird **vor** der Behebung am Code oder per Test nachgeprüft. Hintergrund (Alt): Von 76 Funden einer reinen Lese-Bewertung waren 42 bestätigt, 11 falsch, 23 unklar; Bewerter behaupteten fälschlich „Tests laufen nicht“.
  - Abnahme: Register-Datei (CSV) mit allen Spalten; Änderung am Code nur zu Funden mit Status „bestätigt“; Stichprobe 5 Funde: Nachstellung vorhanden.

### 1.2 Pflichtinhalt je Bereich

Die Tabelle nennt je Bereich das **Verhalten**, das Tests belegen müssen (aus der Testlandkarte des Bestands; Dateinamen bewusst weggelassen). Kürzel verweisen auf die Fachdateien. Spalte „Zusatz“ nennt Ebenen außer E1–E3.

| Bereich (Kürzel) | Pflicht-Verhalten | Zusatz |
|---|---|---|
| planung (STP) | Stundentafel: Klasse vor Gruppe/Bildungsgang/Jahrgang; gleichrangige Überschneidung → 409 mit Klassenliste, mit Bestätigung speicherbar; Fach doppelt → 422; leere Tafel und Klasse ohne Tafel werden gemeldet; „zu viel verplant“ im Bericht. Generator-Auswertung = Qualitätsbericht-Kennzahlen; Verschiebungen. Dauerprüfung → Varianten → Entscheidung (Vorschlagspakete). Planzeiträume (Halbjahr = eigener Plan). Doppelstunden nur zwischen Pausen. Bericht in Klartext, Spannen je Woche, Wochenmuster. | E6 (Generator), E5 (Editor), Datum |
| regeln (STP) | Regeln und Prioritäten als Bausteine; Klausur-Höchstgrenzen (0 = keine Grenze); Vorlagen mit gelöschten Klassen; keine stille Kürzung. | – |
| stundenplan (STP) | Kalenderwoche mit Datum, Feiertagen und Terminen (auch Samstag/Sonntag); Wochenangaben jede Woche/ausgewählte Wochen/Rhythmus; Schulwoche und Kalenderwoche; Schuljahresbeginn aus den Sommerferien; Altdokument mit Wochenzyklus verlustfrei; Generator mit Wochenvarianten; iCal je Kind. | Datum-Matrix, E5 (Raster, Tastatur, Touch) |
| vertretung (VER) | Engine mit handgebauten Kleinstschulen (exakte Erwartung) und generierten Plänen (Invarianten: keine Doppelbelegung, kein Entfall in der Tagesmitte, solange Ersatz existiert); abwesende Lehrkräfte getrennt, keine „fehlenden Klassen“; öffentliche Sicht ohne Gründe; Bestätigungsmodus; Schultag-Navigation ohne Ferien; Vorschau vor dem Speichern; gesperrter oder durch Klausur belegter Fachraum ohne Ersatz; Monitor-Einstellungen je Standort; faire Verteilung. | E6 (Tagesplan), E5 (Monitor 375 px) |
| klausuren-aufsichten (VER, NOT) | Klausurprüfung (Schultag, Grenzen je Tag/Woche/Halbjahr, Kursunterricht, Bestätigungs-Verbot für Lehrkräfte); Pausenaufsichten (Besetzung, Ersatz schließt Sperren aus, Standort-Konflikte, Aufsichten mit Terminen); Nachschreibtermine; Vertretungsplan nur für Personal. | Datum |
| klassenbuch (KLB) | Anwesenheit je Stunde; vorausgefüllte Krankmeldungen; Notiz verschlüsselt; nicht lesbare Notiz → „nicht lesbar“ und Speichern 409 (nie still überschreiben); fremde Klassen 404; telefonisch/teilweise entschuldigt; zu spät/früher gegangen; Übersicht. | Datum, E4 (Verschlüsselung) |
| klassen (STA) | Suche, Filter, Detail; Stundentafel direkt an der Klasse; Infokarten; Jahrgangs- und Profil-Verwaltung (eigene Jahrgänge); Folgen-Vorschau; Klassenrollen (mehrere Leitungen, Abteilung). | CSV-Rundlauf |
| fehlzeiten (KLB) | Meldungsprotokoll lückenlos und nur anhängend, abgestufte Sicht; Statistik (Anteil je Fach, Grenzwert, Verspätung); Volljährigkeit nach Geburtsdatum; Abwesenheitsart „Unterricht findet nicht statt“; Rechte-Matrix Krankmeldungen (Fachlehrkraft 403 bzw. 404, Klassenleitung 200, Admin ohne Zugriff); nachträglich ändern/zurücknehmen. | Datum (Ferien, Wochenende), E6 (2.500 Schüler/innen) |
| nachrichten (NAC) | Postfach: Einzel, Gruppe, Rundschreiben, BCC-Regeln, Moderation (Liste ohne Inhalt, Ansicht erst nach Klick plus Audit), Sende-Sperre, datensparsamer Empfängerkreis, verschlüsselt. Chats Ende-zu-Ende (Server sieht nur Chiffrat), Geräte verknüpfen, Passwort-Backup, neue Schlüssel, Beitrittsgrenze, Audit-Umfang. Verbundene Mail-Konten. | E4 (Marker-Suche), E5 (zwei Browser koppeln) |
| kursraeume (KUR) | Mitgliedschaft je Kursteil (Lehrende nur dort, wo sie unterrichten); Lehrer-Scope; Aufsicht nur lesend; Material verborgen/ab Zeitpunkt/zur Stunde, Entfall und Ferien verschieben; Klassenräume schützen fremdes Material; Eltern lesend; Aufgaben (Raster, Notenschlüssel, Fristverlängerung); Lernfortschritt (Abschlussbedingungen, „Erledigt“). | Upload (Ordner, Fachformate), Datum |
| notenbuch (NOT) | Rechte je Rolle; Notentabelle, Schnitte, Vorschlag und Überschreiben; Skalen, Tendenzen, Rundung; Einsicht-Standard „nach Freigabe“; Export im Zielformat; Audit jeder Änderung. | Rundlauf [unklar: Formatbeschreibung verfügbar] |
| kompetenzen (NOT) | Raster, Import, Lernstand mit Verlauf, Selbsteinschätzung, Abzeichen, Lernplan, Elternbereich, idempotente Bestätigung (Wiederholung → 409). | E5 (Elternansicht) |
| lernaktivitaeten (KUR) | Abstimmung, Umfrage (Pseudonym statt Klarname), Fragensammlung, Selbsttest, Ergebnisse; atomare Zähler, eindeutiger Versuchsindex. | Nebenläufigkeit |
| benachrichtigungen (BEN) | Auslöser (Kursraum, Formular, Vertretung), Einstellungen je Person, Schulvorgaben, Rechte, Neutral-Mail (kein Name im Text), Abmeldung, Kennzeichnung automatischer Mails. | Mail-Attrappe |
| formulare (FOR) | Felder, Antworten, Bibliothek, Genehmigungsweg, Doppeleinreichung binnen 5 s → 409, Eingabesäuberung, PDF-Export und Listen ohne Kappung, Eindeutigkeit „einmal je Kind“. | E5 |
| lehrkraefte (LEH) | Verfügbarkeit als Regeln (Wiederholung, Ausnahmen), Sperrzeiten, Anträge und Genehmigung, Scope (nur eigene Klassen/Kurse), Deputat nicht selbst setzbar. | Datum (Beispiele des Auftraggebers) |
| schueler-eltern (SCH) | Selbstbedienung (Krankmeldung nur volljährig), Dokumente, Förderinformationen (Rechte, Admin gesperrt), Kinderwahl je Konto, Elternfreigabe je Bereich. | Matrix Volljährigkeit |
| rechte-rollen (REC) | Katalog, schulspezifische Abweichungen, feste Mindestregeln (Abweichungen dürfen sie nicht unterschreiten), freie Vergabe und eigene Rollen mit Scope-Grenze je Grundtyp, Zuschauer-Allowlist, beobachtete Konten, Inhaber-Schutz. | Rundgang je Rolle |
| login-sso (ANM) | Kontakt bestätigen, „Passwort vergessen“ (neutrale Antwort), Zugangsbriefe als PDF, Anmelde-Richtlinien, progressive Drosselung, mehrere Konten, Selbst-Reset, Anmeldedienste (Test-Anbieter), SSO aus dem Browser, Zwei-Faktor, Passkeys. | E5 (Passwort-Manager), E7 |
| datenschutz (DAT) | Dateiverschlüsselung; Löschkonzept (Fristen, Vorschau, Protokoll, Sofort-Löschen); Auskunft vollständig und ohne Daten Dritter; Impressum und Datenschutzerklärung; Betreiber-Paket; Datensparsamkeit in Sammelansichten. | feste Uhr |
| integrationen (INT) | API-Zugänge (Bereiche und Filter serverseitig, Ablauf, Schreibzugang mit Protokoll); Ferienimport; Fremdsystem-Importe (Probelauf, ganz oder gar nicht); Untis/CSV/iCal/Webhook (Signatur); 1.500 Schüler/innen mit Zeitmessung. | E6, Rundlauf |
| demo (BET) | Allowlist-Sperre aller schreibenden Routen; öffentliche Demo (Rollen, Konten, Systemfunktionen); Reset. | alle Schreibrouten |
| betrieb (BET) | Sicherheits-Checkliste (Header, Cookies, CORS, Source Maps); Lizenz (Prüfung, Sperrstufen, Offline-Stufen); Metriken-Schutz; Migrationen; Zielprüfung ausgehender Verbindungen; Einrichtungsassistent; Betriebsmodus; Update/Mehr-Knoten; Jahreswechsel; Sicherung und Wiederherstellung. | E8 |
| stammdaten-kern (STA) | Feature-Endpunkte, Rollen-Sicht, Live-Umplanung, Import-Hilfen, Planungsdokument verschlüsselt (Format, Altbestand, Bezug). | E4 |
| ui-basis (OBE) | Anfrage-Client (Zeitlimit, Fehlerübersetzung, CSRF, 401-Behandlung), Feature-Registry, Eingabemodus, App-Rahmen, Designregeln (Erklärabsätze), Hilfe-Logik, Plan-Perioden-Logik, Kennzahl-Kacheln, App-Dialoge. | E5 (Fokusfalle) |
| branding (OBE) | Produktname nur an einer Stelle; Logo-Geometrie aus einer Quelle; Varianten hell/dunkel/einfarbig. | – (Alt: 0 Tests) |

- **QUA-012** · P1 · Status: offen — **Pflichtinhalt.** Jedes in der Tabelle genannte Verhalten hat mindestens einen Abnahmetest mit Kennung der zugehörigen Fachanforderung.
  - Abnahme: Review Tabelle × Matrix: Zu jeder Zeile existiert pro genanntem Verhalten ein Test; fehlende Verhalten werden als Fund (Schwere mittel) geführt.

- **QUA-013** · P1 · Status: Ist — **Logik der Oberfläche getrennt testbar.** Reine Oberflächenlogik (Hilfe-Zeitgeber und Zustände, Übersetzung der zehn häufigsten Validierungsfehler, Wochen- und Datumshelfer, Raster, Rechte-Navigation, Kürzel/Namen, Formular-Fehler, Plan-Perioden, Kennzahl-Kacheln) liegt in Funktionen ohne Browser und wird auf E1 getestet.
  - Abnahme: Für jede genannte Logik existiert ein Oberflächen-Logiktest ohne Browser; der Hilfe-Zeitgeber ist mit gesteuerter Uhr prüfbar (2 s Verweilen öffnet, Rechtsklick sofort, Esc schließt).

- **QUA-014** · P1 · Status: offen — **Branding ist getestet.** Der Produktname ist nur an **einer** Stelle konfigurierbar; Logo-Geometrie kommt aus **einer** Quelle (Alt: Abweichungen zwischen Dateien, 0 Tests).
  - Abnahme: Test ändert den Namen in der einen Konfiguration → alle sichtbaren Ausgaben (Kopfzeile, Anmeldeseite, Browser-Tab, PDFs, Mails, Hilfe, Kalender-Feed, Rechnungen, Mail-Kopfzeilen, Benutzeragent) tragen den neuen Namen; Suche nach dem alten Namen in Ausgaben und Quelltext (außerhalb der Konfiguration) = 0 Treffer; Logo-Varianten stimmen geometrisch überein (Vergleich der Pfaddaten).

### 1.3 Datumsunabhängige Tests

Hintergrund (Alt): Tests scheiterten am Wochenende und in den Herbstferien (Beurlaubungstest, Notenbuch-Test, Klassenbuch-Tests); die Demo konnte keine Klassenarbeit in den Herbstferien anlegen; ein festes Schuljahresdatum stand an drei Stellen im Code. Sieben Testdateien wurden auf „echte Schultage inklusive Ferien“ umgestellt.

- **QUA-015** · P1 · Status: offen — **Feste Uhr.** Kein Test liest die echte Systemuhr. Die Uhr ist von außen setzbar (Produktivcode und Tests nutzen dieselbe Uhr-Schnittstelle).
  - Abnahme: Statische Suche in Testcode und Produktivcode: kein direkter Systemuhr-Zugriff außerhalb der Uhr-Schnittstelle; Gesamtlauf mit auf +400 Tage verschobener Systemuhr liefert dasselbe Ergebnis.

- **QUA-016** · P1 · Status: offen — **Datums-Matrix-Lauf.** Alle datenabhängigen Tests (Kalender, Vertretung, Fehlzeiten, Klassenbuch, Beurlaubung, Notenbuch, Kursraum-Freigaben, Löschfristen, Volljährigkeit, Termine) laufen mit zehn festen Uhren: (1) Montag der Schulwoche 1, (2) Mittwoch mitten im Halbjahr, (3) letzter Schultag vor Ferien, (4) Samstag, (5) Sonntag, (6) Tag mitten in den Herbstferien, (7) gesetzlicher Feiertag auf einem Wochentag, (8) 29. Februar eines Schaltjahres, (9) Tag des Halbjahreswechsels, (10) Tag der Sommerzeit-Umstellung.
  - Abnahme: Alle zehn Läufe sind grün; ein Lauf, der nur an einem Referenzdatum scheitert, gilt als Fund „datumsabhängiger Test“ (Schwere mittel).

- **QUA-017** · P1 · Status: Ist — **Beispiel- und Testtermine nur an Schultagen.** Beispieldaten und Test-Termine (Klassenarbeit, Beurlaubung, Hausaufgabe mit Frist) fallen nie auf Wochenende, Ferien oder Feiertage; der Beispieldaten-Erzeuger weicht auf den nächsten Schultag aus.
  - Abnahme: Beispieldaten-Erzeugung mit den zehn Uhren aus QUA-016 → 0 Beispieltermine auf Nicht-Schultagen.

- **QUA-018** · P1 · Status: offen — **Schuljahr, Halbjahre, Ferien aus Datum ableiten.** Es gibt keine festen Schuljahres-Datumsliterale in Produktivcode und Tests (Alt: festes Datum an drei Stellen). Ausnahme: Ferienvorlagen je Bundesland als Daten mit Quellenangabe.
  - Abnahme: Suche nach Datumsliteralen eines Schuljahres im Quelltext außerhalb der Vorlagendateien = 0 Treffer; Lauf mit zwei verschiedenen Uhren (Schuljahr 2026/27 und 2027/28) besteht unverändert.

- **QUA-019** · P0 · Status: Ist — **Zeitzone und Stichtage.** Intern wird in UTC gespeichert (ISO-Zeitstempel mit `Z`), Datumsfelder als `YYYY-MM-DD`; Stichtage (Volljährigkeit, Fristen, Terminzeiten) gelten in Ortszeit Europe/Berlin.
  - Abnahme: Mit fester Uhr 1 s vor und 1 s nach Mitternacht (Europe/Berlin) am 18. Geburtstag wechseln Rechte exakt; ein Termin „am 21.05. um 0 Uhr“ läuft über die Sommerzeit-Umstellung korrekt; alle Antwort-Zeitstempel enden auf `Z`.

- **QUA-020** · P1 · Status: offen — **Wochen- und Kalenderlogik tabellengetrieben.** Wochen 1…52 (Schulwoche über Ferien, Rhythmus über das Schuljahr, Altdokument ohne Schuljahr, Samstag/Sonntag nur bei Terminen) werden mit einer Eingabe-/Erwartungs-Tabelle geprüft, die als Datei vorliegt und für Alt und Neubau identisch ist. [unklar: 52 oder 53 Wochen; Festlegung in STP]
  - Abnahme: Die Tabelle (mindestens 30 Fälle) läuft gegen beide Systeme; jede Abweichung wird als Fund geführt.

- **QUA-021** · P1 · Status: offen — **Volljährigkeit an Grenzen.** Tests decken den 18. Geburtstag (Tag davor, Tag selbst), Geburtsdatum 29.02. [unklar: Regel für Nicht-Schaltjahre; Festlegung in REC/SCH] und fehlendes Geburtsdatum (Ersatzfeld `users.adult`) ab.
  - Abnahme: Für die drei Fälle sind erwartete Rechte je Rolle (Schüler/in, Eltern, Krankmeldung) festgelegt und grün; Änderung am Geburtstag wirkt in der nächsten Anfrage ohne Zutun.

### 1.4 Test-Isolation

- **QUA-022** · P1 · Status: Ist — **Frische Datenbank je Test.** Jeder Test (E2) startet mit eigener frischer Datenbank und kleiner Beispielschule (2 Klassen je Jahrgang); ein leerer Client steht für Leer-Zustände bereit.
  - Abnahme: Zwei Tests, die denselben Datensatz anlegen, sind in beliebiger Reihenfolge und parallel grün.

- **QUA-023** · P1 · Status: offen — **Kein gemeinsamer Zustand.** Prozessweite Zustände (Zwischenspeicher, Ratenbegrenzer, Anmelde-Drosselung, Singletons) werden zwischen Tests zurückgesetzt. Hintergrund (Alt): ein Test sah „429“ aus einem anderen Test; ein Löschkonzept-Test scheiterte nur im parallelen Lauf.
  - Abnahme: Gesamtsuite dreimal in zufälliger Reihenfolge und einmal parallel → identisches Ergebnis (0 Abweichungen).

- **QUA-024** · P1 · Status: Ist — **Hintergrunddienste in Tests aus.** Benachrichtigungs-Versand (`SM_NOTIFY_DISPATCHER=0`), Wartungslauf (`SM_MAINTENANCE_INTERVAL=0`), Auto-Planer (`SM_AUTOPLAN=0`), Lizenzprüfung, Update-Dienst und Job-Prozesse laufen in Tests nicht von selbst; Tests schalten sie gezielt ein. Passwort-Hash-Kosten sind gesenkt (`SM_SCRYPT_N=1024`), das ausgelieferte Oberflächenverzeichnis ist leer (`SM_FRONTEND_DIST`).
  - Abnahme: Test-Start protokolliert die Schalter; ein Test ohne gezielten Schalter startet keinen Hintergrundthread (Thread-Liste leer).

- **QUA-025** · P0 · Status: offen — **Kein Netz in Tests.** Ausgehende Verbindungen sind in E1–E4 blockiert; Mail, SMS, Webhook, Anmeldedienst, Ferien-Dienst, Lizenzserver und Übersetzungsdienst sind Attrappen; Mail-Adressen nur auf `example.org`.
  - Abnahme: Lauf in einem Container ohne Netzzugang ist grün; Scan der Testdaten: 0 E-Mail-Adressen außerhalb `example.org`.

- **QUA-026** · P1 · Status: offen — **Attrappen folgen der Schnittstelle.** Attrappen werden aus derselben Schnittstellenbeschreibung abgeleitet oder durch einen Vertragstest geprüft. Hintergrund (Alt, 17.10.): drei Backend-Tests schlugen fehl, weil Attrappen einen neuen Parameter nicht kannten.
  - Abnahme: Änderung einer Schnittstellen-Signatur bricht den Vertragstest der Attrappe, nicht Fachtests; Review-Stichprobe von 5 Attrappen.

- **QUA-027** · P1 · Status: Ist — **Eigene Ports, Datenbank und Hostname je Prüfer.** Jeder Browser-Check nutzt eine eigene Kopie des Vorschau-Starters, eigene Ports, eigene Datenbank und den Hostnamen `<paket>.localhost`; der Server wird danach gestoppt.
  - Abnahme: Zwei Prüfer starten gleichzeitig Browser-Checks ohne Portkonflikt; nach dem Lauf lauscht kein Prozess mehr.

- **QUA-028** · P0 · Status: offen — **Nie gegen Produktiv- oder Fremddaten.** Tests laufen nie gegen die Datenbank oder Dateiablage einer Produktivinstanz. Kopien echter Datenbanken dienen nur dem Migrations-Probelauf (Abschnitt 2.7) und werden danach gelöscht.
  - Abnahme: Test-Start bricht ab, wenn die Datenbank keine Test-Schutzmarke trägt; Probelauf-Kopie liegt nach dem Lauf nicht mehr vor.

- **QUA-029** · P1 · Status: Ist — **Zielplattform Linux.** Der Gesamtlauf läuft in der Linux-Zielumgebung. Plattformabweichungen (Dateisperren beim Ersetzen offener Dateien, Zeilenenden von Shell-Skripten, Groß-/Kleinschreibung von Importen, Betriebssystem-spezifische Kennzahlen) werden **mit Ursache und Lösung** als Fund geführt. Der Betreiber: „Was genau für ein Windows-Failure … und gibt es mir keinen Kontext und gar nichts. Was ist da?“ — „bekannte Fehler“ ohne Ursache sind unzulässig.
  - Abnahme: Gesamtlauf Linux: 0 fehlgeschlagen; Liste „bekannte Abweichungen“ ist leer oder jeder Eintrag nennt Ursache, Lösung, Fund-Kennung; Shell-Skripte haben Linux-Zeilenenden (Prüfung im Gate).

- **QUA-030** · P2 · Status: Ist — **Schalter für langsame/optionale Tests.** Langsame Solver-Tests (`SM_SLOW=1`) und PostgreSQL-Tests (`SM_TEST_POSTGRES_URL`) laufen nur bei gesetztem Schalter und werden im Bericht als „übersprungen: Grund“ geführt; vor jedem Release laufen sie.
  - Abnahme: Standardlauf nennt Anzahl und Grund übersprungener Tests; Release-Lauf: 0 übersprungen ohne Grund.

- **QUA-031** · P2 · Status: offen — **Skip-Disziplin.** Jeder übersprungene Test hat einen dokumentierten Grund; im Gate zählen ungeklärte Skips als Fehler.
  - Abnahme: Gate-Bericht: Anzahl Skips mit Grund = Anzahl Skips gesamt.

- **QUA-032** · P1 · Status: offen — **Eine Schnittstelle zwischen Alt und Neu bei Abnahmetests.** Abnahmetests formulieren Aktion und Erwartung; ein Adapter bildet sie auf Pfad und Format des jeweiligen Systems ab, damit dieselben Tests beide Systeme prüfen (Abschnitt 4).
  - Abnahme: Adapter für Alt und Neubau liegen vor; ein Probe-Test (Anmeldung + Stundenplan lesen) läuft gegen beide.

### 1.5 Testdaten ohne echte Personen

- **QUA-033** · P0 · Status: Ist — **Nur synthetische Daten.** Alle Testdaten sind erfunden: Namen aus einem Namensgenerator, Adressen und Telefonnummern fiktiv, Geburtsdaten zufällig, E-Mail nur auf `example.org`, Atteste als Platzhalter-Dateien. Keine echten Personen, Schulen oder Betriebe.
  - Abnahme: Scan der Beispielschulen, Fixtures und Seeds: 0 E-Mail-Adressen außerhalb `example.org`, 0 echte Domains; Stichprobe 20 Namen: aus Generatorliste.

- **QUA-034** · P1 · Status: Ist — **Vier Größenstufen.** (a) Handgebaute Kleinstschule mit **exakt** erwarteten Ergebnissen (Vertretung, Fairness); (b) kleine Demo (2 Klassen je Jahrgang) für E2; (c) volle Demo: rund 99 Klassen, 2.600 Schüler/innen, rund 170 Lehrkräfte, 2 Standorte, vier Rhythmusklassen (Praxis- bzw. Berufsschultag), Oberstufe mit Schienen, Abendunterricht, Wegezeiten; (d) Lastschule: 2.500 Schüler/innen, 300 Lehrkräfte. Dazu Beispielschulen Gymnasium, Gesamtschule, Berufskolleg NRW und Montessori als JSON.
  - Abnahme: Seeds der Stufen (a) bis (d) und der Beispielschulen liegen im Repository; jede Stufe lässt sich mit einem Befehl erzeugen; Größen stimmen mit der Beschreibung (±5 %).

- **QUA-035** · P1 · Status: Ist — **Deterministische Erzeugung.** Gleicher Startwert → gleiche Daten (Hash-Vergleich). Tests nageln keine Kürzel, IDs oder Namen der Demo fest, sondern wählen dynamisch (Hintergrund: die Demo-Zufallsfolge änderte sich durch neue Lehrkraft-Felder und brach Tests).
  - Abnahme: Zweimaliger Seed-Lauf → identischer Hash; Suche in Tests nach Demo-Kürzel-Literalen = 0 Treffer; Hinzufügen eines Lehrkraft-Feldes zum Erzeuger bricht keinen Fachtest.

- **QUA-036** · P2 · Status: Ist — **Testtag-Szenario.** Ein Szenario mit **allem gleichzeitig** zum Durchklicken (Hausaufgaben, Test, Klausur in echter Stunde, Krankmeldungen inkl. mehrtägig mit Attest, Eltern-Konto meldet das Kind am Klausurtag krank → Nachschreiben nötig, Nachteilsausgleich, „gefehlt“ im Klassenbuch). Alle Einträge sind mit „[Testtag]“ markiert; ein Befehl legt an, ein zweiter Lauf legt nichts doppelt an, ein Befehl entfernt alles.
  - Abnahme: anlegen → zweiter Lauf → entfernen: Zeilenzahlen aller Tabellen sind danach gleich dem Ausgangszustand; die Abnahme „durchgeklickt“ durch den Betreiber ist mit Datum protokolliert (Status im Alt: Abnahme steht aus).

- **QUA-037** · P0 · Status: Ist — **Testzugänge und Geheimnisse.** Testzugänge werden je Lauf erzeugt; Passwörter erscheinen nie in Chat, Logs, Berichten oder Screenshots (Passwortfelder verdeckt; Auge-Symbol aus). Entwicklungs-Passwörter existieren nur im Entwicklungsmodus; im Produktivmodus verweigert der Start sie.
  - Abnahme: Scan von Testlogs, Berichten und Screenshot-Beschriftungen auf Passwortmuster = 0; Produktivstart mit Entwicklungs-Passwort-Konto → Start verweigert (Meldung ohne Wert). Hintergrund (Alt): Ein Klartext-Passwort war auf einem Screenshot sichtbar.

- **QUA-038** · P1 · Status: offen — **Rundlauf der Beispielschulen.** Jede Beispielschule wird exportiert, in eine leere Instanz importiert und ist danach identisch (Zeilen, Beziehungen, Einstellungen). Bei jeder Schemaänderung wird geprüft, dass **ältere** Beispiel-JSON weiterhin lädt.
  - Abnahme: Rundlauf-Test je Beispielschule grün; Archiv älterer Beispiel-JSON (je Format-Epoche eine Datei) lädt ohne Fehler.

- **QUA-039** · P1 · Status: Ist — **Mandantentrennung in Testdaten.** Zwei Instanzen mit verschiedenen Schlüsseln: Token und Chiffretexte der einen sind in der anderen wertlos.
  - Abnahme: Token aus Instanz A an Instanz B → 401; Chiffretext aus A in B nicht lesbar (kontrollierter Fehler).

### 1.6 Lasttests (Ebene E6)

Hintergrund (Alt): Es gab nur einen früheren lokalen Lauf mit 150 gleichzeitigen Nutzern ohne Fehler und eine Messung von 1,2 s (95. Perzentil) bei 60 Nutzern; Nachrichtenversand dauerte 3 bis 5 s. Ein Lastskript (nur `localhost`, fremde Ziele nur mit `--ich-darf`, Aufruf `make lasttest`) wurde am 17.10. geschrieben; **ein echter Lauf stand aus**. Die Verkehrszahlen unten stammen aus einer Rechnung (Annahmen, keine Messung unter Last). Betreiber-Ziel: „tausende gleichzeitige Nutzer“, die gleichzeitig schreiben, ohne dass das System „unglaublich langsam“ wird (PRI-004).

- **QUA-040** · P1 · Status: offen — **Lastprofile und Zielwerte.** Der Neubau besteht die Szenarien S1 bis S9 (Tabelle; S10 erst nach Festlegung durch den Betreiber) auf der Wegwerf-Instanz mit Demo-Daten der Stufe (d) (QUA-034); für die Größen Klein und Groß wird die Lastschule auf 1.000 bzw. 5.000 Schüler/innen skaliert (Konten, Lehrkräfte, Eltern nach den Verhältnissen der Schulgrößen in PRI-004). Gemeinsame Zielwerte: **Fehlerquote 0 %** (keine 5xx, keine Zeitüberschreitung, keine verlorene Schreibaktion); **95. Perzentil ≤ 500 ms** für Lese- und Schreibabrufe der Szenarien (Ziel aus dem Backlog, in STP, KLB, NAC wiederholt); **Grenzwert 1.000 ms** (95. Perzentil): zwischen 500 und 1.000 ms gilt „bestanden mit Auflage“ (Fund mittel), darüber „nicht bestanden“ [Festlegung].
  - Abnahme: Lastbericht je Szenario mit Anzahl Anfragen, Fehlerzahl, 50./95./99. Perzentil, höchster Wert, Dauer der Plateau-Phase; Gate G5 verlangt für S1 bis S4 „bestanden“; ein Szenario ohne Bericht gilt als „nicht bestanden“.

| Nr | Szenario | Last | Zusatzprüfung |
|---|---|---|---|
| S1 | Unterrichtsbeginn, Größe Mittel | Spitze 100 Anfragen/s über 10 Minuten (07:30–07:40), 1.500 gleichzeitige Live-Verbindungen; Mischung: Startseite, Plan Klasse/Lehrkraft, Vertretungsplan, Krankmeldung (Eltern), Nachrichten-Zähler | 0 % Fehler; Live-Verbindungen bleiben offen |
| S2 | Unterrichtsbeginn, Größe Groß | 190 Anfragen/s, 3.000 Live-Verbindungen | wie S1; Speicherbedarf der Verbindungen notieren (Rechnung: 25–240 MB) |
| S3 | Unterrichtsbeginn, Größe Klein | 40 Anfragen/s, 600 Live-Verbindungen | wie S1 |
| S4 | Planänderung in der Spitze | eine Planänderung zwischen 07:00 und 08:00 löst Ereignisse an alle Verbindungen aus; alle Clients laden neu (600 / 1.500 / 3.000 Anfragen binnen Sekunden) | alle Neuladungen binnen 10 s abgeschlossen, 0 % Fehler [Festlegung] |
| S5 | Verkehrsprofil | aktive Nutzer je Schultag: Schüler/innen 80 %, Lehrkräfte 95 %, Eltern 25 %; je aktivem Nutzer Schüler/in 35 Anfragen, Lehrkraft 180, Eltern 12 | Gesamtanfragen je Schultag innerhalb ±20 % der Rechnung (46.000 / 115.000 / 231.000) |
| S6 | Elternsprechtag-Freischaltung | 500 gleichzeitige Buchungsversuche auf 100 Termine | genau 100 Buchungen, keine Doppelbuchung (Fachabnahme in den Fachdateien) |
| S7 | Nachrichten | Einzel- und Gruppenversand, Rundschreiben an 1.500 Empfänger, in der Spitze S1 | Versand einer Nachricht unter 1 s; 95. Perzentil ≤ 500 ms (Alt: 3 bis 5 s) |
| S8 | Chat im Größtfall | Chat mit 400 Mitgliedern und 10 Geräten je Person (Höchstwerte), 50 Nachrichten | Speicher je Nachricht deutlich unter 99 KB (Alt); Gerätewechsel führt nicht zu doppeltem Upload |
| S9 | Datei-Spitze | Abgaben mit Fotos von 2,5 MB (Annahme der Rechnung) in der Frist-Stunde, gleichzeitig [Festlegung: 500 Uploads] | 0 % Fehler; Kontingente und Virenprüfung greifen; Ablage verschlüsselt |
| S10 | Zeugnistag | [unklar: Lastprofil im Backlog nicht beschrieben; Betreiber festlegen] | – |

- **QUA-041** · P1 · Status: offen — **Messregeln.** Jeder Lastlauf läuft auf einer dokumentierten Plattform (CPU, Kerne, Arbeitsspeicher, Datenträger, Datenbank-Art); Mindestplattformen sind die Betriebs-Richtwerte: Klein 2 Kerne und 4 GB, Mittel 4 Kerne und 8 GB (PostgreSQL), Groß 6 bis 8 Kerne und 16 GB (PostgreSQL). Aufbau: Hochlauf 2 Minuten, Plateau mindestens 10 Minuten, drei Läufe, ausgewiesen wird der **Median der drei Läufe** und der schlechteste Lauf. Der Lastgenerator läuft nicht auf derselben Maschine wie der Prüfling, wenn dessen Kerne dadurch knapp werden [Festlegung]. Die Messung geschieht nicht in einem im Hintergrund laufenden Browser-Fenster (Zeitgeber gedrosselt, Werte unzuverlässig).
  - Abnahme: Der Bericht nennt Plattform, Version, Datenstand (Seed-Hash, QUA-035), Datum, drei Einzelergebnisse und den Median; fehlt eine Angabe, gilt der Lauf als nicht gewertet.

- **QUA-042** · P1 · Status: offen — **Last des Planungs-Generators.** Der Generator plant die Referenzschule mit 2.500 Schüler/innen, 300 Lehrkräften, 99 und mehr Klassen und 2 Standorten (QUA-034 c/d) innerhalb des konfigurierten Zeitlimits (Standard 30 s, `SM_GENERATE_TIME_LIMIT`); der Bericht nennt Laufzeit, Anzahl harter Konflikte (Soll 0), Kennzahlen des Qualitätsberichts und die Zahl der Teilläufe. Speichern und Laden des verschlüsselten Planungsstands bleiben ohne spürbare Verzögerung (Verschlüsselung unter 1 ms je Wert). Eine Dauerprüfung eines sauberen Plans dauert Millisekunden. Hinweis (Alt): längere Rechenzeit (2 Minuten statt 10 Sekunden) liefert bessere Pläne; das Zeitlimit ist einstellbar.
  - Abnahme: Generator-Lauf der Lastschule: 0 harte Konflikte, innerhalb Zeitlimit oder (bei Limit) mit ausgewiesener Güte; Dauerprüfung < 1 s; Laden des Plans mit 300 Versionen < 1 s [Festlegung]; Ergebnis im Lastbericht.

- **QUA-043** · P1 · Status: offen — **Nebenläufigkeitstests (Race-Tests).** Für jeden Ablauf, der nach den Fachdateien atomar sein muss, existiert ein Test mit gleichzeitigen Anfragen: Terminbuchung (500 Versuche auf 100 Termine → genau 100), Doppeleinreichung eines Formulars (binnen 5 s → 409), Vertretungs-Freigabe mit Versionsprüfung, Übernahme von Plan-Vorschlägen (Versionsprüfung), Zähler und Versuchs-Index der Lernaktivitäten (atomar, eindeutig), einmaliger Verbrauch von Reset-Token und Codes, Kontingent- und Zugangs-Grenzen (atomar), Nachrichten-/Chat-Wiederholung (Idempotenz-Schlüssel je Absendevorgang), parallele Planänderungen (Versionskonflikt → 409 statt stilles Überschreiben).
  - Abnahme: Je Ablauf ein Test mit mindestens 20 gleichzeitigen Aufrufern, wiederholt 10-mal; Ergebnis stets identisch und fachlich korrekt (keine Doppelung, keine verlorene Änderung); Fehlerfall: ein Lauf mit abweichendem Ergebnis → Fund hoch.

- **QUA-044** · P2 · Status: offen — **Speicher- und Wachstumsmessung.** Die Annahmen der Speicher-Rechnung (Dateien rund 47,6 MB und Datenbank rund 2,9 MB je Schüler/in und Jahr, Variante ohne Chat-Bilder; Chat-Bilder zusätzlich rund 57 MB; Planversion Ø 66 KB; Audit 220 B je Zeile) werden mit einem simulierten Schuljahr der Lastschule gegengemessen und nach 4 bis 6 Wochen Echtbetrieb aus der Datenbank nachgemessen. Abweichungen über ±25 % [Festlegung] werden als Fund (niedrig) geführt und in die Betriebsempfehlung übernommen.
  - Abnahme: Messbericht stellt Annahme und Messwert je Größe nebeneinander; die Nachmessung nach 4 bis 6 Wochen ist terminiert und im Betreiberpaket als Aufgabe geführt.

- **QUA-045** · P1 · Status: offen — **Dokumentation und Vergleich.** Die Ergebnisse stehen in der Betriebsdokumentation (Kapitel Lasttests) mit Empfehlung je Schulgröße; dieselben Szenarien laufen über den Adapter (QUA-032) gegen den Alt-Stand, soweit die Abrufe dort existieren (Vergleich in Abschnitt 4, Messgröße M5). Die Auswertung nennt auch den Grenzbereich: Groß (190 Anfragen/s) liegt für einen einzelnen Prozess im Grenzbereich; ein Betrieb auf dem Heimanschluss ohne Dienstgütevereinbarung wird für Mittel und Groß als Betriebsrisiko ausgewiesen.
  - Abnahme: Betriebsdokumentation enthält je Szenario einen Absatz „Ergebnis, Plattform, Empfehlung“; die Vergleichstabelle M5 enthält Alt- und Neubauwerte oder den Vermerk „nicht messbar: Abruf fehlt im Alt“.

### 1.7 Browser-Rundgänge (Ebene E5)

Hintergrund (Alt): Rundgänge liefen je Paket von Hand oder per Skript (Playwright, 1280 und 390 px, hell und dunkel; Ergebnis „keine unerwarteten JS-, 4xx- oder 5xx-Fehler außer den beabsichtigten 401/403“); zusätzlich ein Zuschauer-Rundgang über 274 Lese-Adressen. Für mehrere neue Funktionen fehlte die Browser-Prüfung (nur automatische Tests): Impressum-Links, Fehleranzeige der Einrichtungstabelle, CSV-Export des API-Protokolls, Zeitleiste beobachteter Konten, Koppeln zweier Browser im Chat. Aussagen „grün“ galten nur für die jeweils geänderten Bereiche.

- **QUA-046** · P1 · Status: offen (Ist: Rundgänge je Paket, nicht wiederholbar) — **Rundgang je Rolle.** Je Standardrolle des Rollenfelds (Abschnitt 2.1, mindestens die 12 eingebauten Rollen plus Klassenleitung, volljährige/r Schüler/in, Eltern mit zwei Kindern) durchläuft ein Skript **alle** Menüeinträge, Startkacheln und die Hauptaktion jeder Seite (Seiten-Register, QUA-068). Prüfpunkte je Seite: keine Konsolenfehler, keine unerwarteten Antwortcodes (erwartet nur 401/403/404 an absichtlichen Stellen), kein waagerechter Bildlauf der Seite, genau eine Hauptüberschrift, kein Fremdinhalt, keine Rohschlüssel oder technischen Begriffe, kein nativer Browser-Dialog.
  - Abnahme: Rundgangsbericht je Rolle mit Seitenzahl, Fehlerliste (Soll leer), Datum, Version; Gate G5 verlangt Berichte für alle Rollen; ein im Menü sichtbarer, aber ins Leere führender Eintrag ist ein Fund (mittel).

- **QUA-047** · P1 · Status: offen — **Geräte- und Darstellungsmatrix.** Jeder Rundgang läuft in diesen Darstellungen: Handy 390 px (Pflicht, kein waagerechter Bildlauf) und 360 px (Mindestbreite, OBE-004), 375 px (Monitor-Ansicht), Tablet 820 px, Desktop 1440 px (Prüfbreiten nach OBE-004) sowie 1280 px (Referenzbreite des Altsystems, für den Vergleich in Abschnitt 4); Farbschema hell, dunkel und System; „Bewegung reduzieren“ an und aus; Zoom 200 % ohne Verlust von Funktion oder Inhalt. Die Matrix wird nicht vollständig für jede Seite wiederholt, sondern gestaffelt: Pflichtseiten (20 je Rolle) in allen Zeilen, übrige Seiten in 390 px hell, 1280 px dunkel [Festlegung].
  - Abnahme: Bericht zeigt die Matrix mit Häkchen je Zeile und Seitenzahl; Verstöße (abgeschnittene Spalten bei 375 px, überlaufende Knöpfe bei 390 px, Zoom-Verlust) sind Funde mit Bildbeleg.

- **QUA-048** · P1 · Status: offen (Ist: Angaben widersprüchlich — eine Barrierefreiheits-Prüfdatei wird genannt, die Prüfung nannte „keine E2E-Tests“; [unklar: Stand]) — **Barrierefreiheit automatisiert.** Automatische Prüfung (Barrierefreiheits-Engine im Browser) der 20 wichtigsten Seiten je Rolle ohne schwere Verstöße; Kontraste nach WCAG 2.1 AA in hell und dunkel als Token-Test (Text 4,5:1, großer Text 3:1, Bedienelemente 3:1, OBE-020); Fokus sichtbar; Status nie nur über Farbe (OBE-010); Ziele mindestens 44 px; Tabs, Menüs und Auswahllisten mit korrekten Rollen und Pfeiltasten.
  - Abnahme: Bericht mit 0 Verstößen der Stufen „schwer“ und „kritisch“ auf 20 Seiten je Rolle; Verstöße „mittel“ sind Funde; der Token-Test scheitert, sobald ein Farbpaar unter dem Mindestkontrast liegt.

- **QUA-049** · P1 · Status: offen — **Tastatur und Touch.** Alle Abläufe sind ohne Maus erreichbar: Raster (eine Tab-Station, Pfeiltasten innen, Verschieben mit Enter/Pfeiltasten, OBE-087/088), Dialoge (Fokusfalle, Esc, Rückgabe des Fokus), Hilfe (2 s Verweilen, Rechtsklick, Antippen, F1, Esc, OBE-118/119), Menüs, Tabellen. Touch wird mit echter Touch-Emulation geprüft (Antippen, langes Drücken, Ziehen), nicht mit Mausklicks, die als Touch ausgegeben werden.
  - Abnahme: Skript verschiebt eine Stunde im Raster nur mit Tastatur und nur per Touch-Menü; Hilfe öffnet nach 2 s mit gesteuerter Uhr (QUA-013) und schließt mit Esc; Fehlerfall: Element nur per Maus bedienbar → Fund hoch.

- **QUA-050** · P2 · Status: offen (Ist: ausstehend) — **Screenreader-Prüfung dokumentiert.** Die Abläufe Anmeldung, Krankmeldung, Stundenplan, Postfach/Nachrichten, Kursraum und Vertretungsplan werden mit mindestens einem Windows-Screenreader und einem Apple-Screenreader von Hand geprüft und mit Datum, Prüfer, Version und Ergebnis protokolliert; Grundlage der Erklärung zur Barrierefreiheit (BITV 2.0, WCAG 2.1 AA).
  - Abnahme: Protokoll mit 6 Abläufen × 2 Screenreadern; offene Mängel stehen in der Erklärung zur Barrierefreiheit mit Rückmeldeweg.

- **QUA-051** · P1 · Status: offen — **Mehrbrowser- und Mehrkonten-Szenarien.** Folgende Abläufe laufen mit zwei Browsern bzw. Profilen: Chat-Geräte koppeln (Verlauf übertragen, Passwort-Backup, neue Schlüssel), Live-Aktualisierung (Änderung in Browser A erscheint in B ohne Neuladen), Kontowechsel Eltern-/Lehrerkonto parallel (jeder Aufruf mit dem aktiven Konto, keine Vermischung), Abmelden und Konto wechseln leeren alle Zwischenspeicher (Alt-Fund U-01: Daten des vorigen Kontos im selben Tab sichtbar), gemerktes Kind gilt je Konto, nicht je Gerät.
  - Abnahme: Je Szenario ein Skript; nach Kontowechsel enthält der Seitenspeicher keine Daten des Vorkontos (Suche nach Markerwerten, QUA-081: 0 Treffer); Fehlerfall: sichtbare Fremddaten → Fund kritisch.

- **QUA-052** · P1 · Status: offen — **Formulare, Passwort-Manager, Eingabeerhalt.** Anmelde- und Passwortformulare sind für Passwort-Manager eindeutig (Felder `username`, `current-password`, `new-password`, stabile Namen, eigene Seite für das neue Passwort); nach einem Validierungsfehler bleiben alle anderen Eingaben erhalten; Entwürfe gehen beim Reiterwechsel nicht verloren; Seitenwechsel während eines Uploads fragt zurück; Fehler erscheinen am richtigen Feld (OBE-049).
  - Abnahme: Test mit dem Passwortspeicher des Prüf-Browsers (Speichern, Füllen); Formular mit absichtlich ungültigem Feld → Fehlertext am Feld, übrige Felder unverändert.

- **QUA-053** · P2 · Status: offen — **Beweismittel und Schutz der Prüfdaten.** Jeder Browser-Check erzeugt ein Protokoll: Rolle, Seite, Darstellung, Konsole, Netzwerkfehler und Bildschirmfoto; Bildschirmfotos zeigen nie ein Passwort (verdeckte Felder, Auge-Symbol aus), keine Produktivdaten und keine echten Personen. Der Server des Prüfers läuft mit eigenen Ports und eigener Datenbank (QUA-027) und wird nach dem Lauf gestoppt.
  - Abnahme: Stichprobe von 10 Bildschirmfotos: kein lesbares Passwort, nur synthetische Namen; Prozessliste nach dem Lauf ohne Prüf-Server.

### 1.8 Sicherheitsabnahme (Ebene E7)

Die Sicherheitsabnahme ergänzt die Querschnittstests (Abschnitt 2) um Prüfungen, die nur auf einer Wegwerf-Instanz im Produktivmodus sinnvoll sind (SIC-009). Sie ist **verteidigend**: Eine Prüfung belegt, dass ein Schutz greift, ein Protokolleintrag entsteht und keine Daten austreten. Angriffsanleitungen enthält dieses Paket nicht.

- **QUA-054** · P0 · Status: offen (Ist: Checkliste mit 69 Punkten gegen den Code geprüft: 48 erfüllt, 13 teilweise, 1 fehlt, 7 nicht zutreffend) — **Umfang und Maßstab.** Geprüft wird nach OWASP Top 10:2025, ASVS 5.0, OWASP API Security Top 10 (2023), DSGVO-Technik (SIC-011) und der Sicherheits-Checkliste des Betreibers (rund 69 Punkte, übernommen in die Prüfliste). Im Neubau sind alle zutreffenden Punkte „erfüllt“; „teilweise“ ist nur mit Beschluss des Betreibers zulässig.
  - Abnahme: Prüfliste mit Punkt, Quelle, Nachweis (Test-Kennung oder Bericht), Ergebnis; Gate G5: 0 Punkte „fehlt“, 0 Punkte „teilweise“ ohne Beschluss.

- **QUA-055** · P0 · Status: offen (Ist: pip-audit und npm audit ohne bekannte Schwachstellen am 17.10.; CodeQL und Abhängigkeitsprüfung in der CI; Prüfung „ungenutzte Pakete“ ohne CI-Stufe) — **Automatische Prüfungen im Build.** Jeder Build führt aus: statische Analyse (Sicherheitsregeln), Abhängigkeits-Audit für Backend und Oberfläche (Sperrdateien mit Prüfsummen), Geheimnis-Suche im Repository und im Image, Lizenzscan (keine AGPL/GPL im Image, PRI-003), Prüfung des Image-Inhalts (keine Testdateien, keine internen Dokumente, keine Entwicklungs-Skripte, keine Source Maps, keine Dotfiles, keine Datenbank, keine `.env`), Syntaxprüfung aller geänderten Dateien (Lehre 17.10.: ein Syntaxfehler im Startmodul war kurz vorhanden), nicht blockierende Stufe für ungenutzten Code.
  - Abnahme: Die CI bricht ab bei: bekannter Schwachstelle der Stufe hoch oder kritisch, gefundenem Geheimnis, GPL/AGPL-Paket, verbotener Datei im Image, Syntaxfehler; Gegenprobe (QUA-069) je Prüfung mit absichtlich verletzender Testdatei.

- **QUA-056** · P0 · Status: offen — **Wegwerf-Instanz im Produktivmodus.** Eine isolierte Instanz startet im Produktivmodus (SIC-100/101) mit Demo-Daten der Stufe (b) oder (c); geprüft werden: Start verweigert bei unsicherer Konfiguration (je Pflichtprüfung ein Fall), Sicherheits-Kopfzeilen und Content-Security-Policy, Cookie-Flags (HttpOnly, Secure, SameSite), CORS, keine Source Maps und keine Dotfiles, Dokumentations-Schnittstelle aus bzw. nur für Administration, Metriken nur mit Token, Datenbank und interne Dashboards nicht von außen erreichbar, `Cache-Control: no-store` bei Zugangsdaten, kein Entwicklungs-Postausgang, Demo-Funktionen serverseitig verweigert, kein Entwicklungs-Passwort-Konto. Nur lesende Konfigurationsprüfung gegen echte Instanzen.
  - Abnahme: Prüfskript mit je einer Zeile je Punkt und Erwartungswert; 0 Abweichungen; ein Start mit Platzhalter-Geheimnis wird abgelehnt (Meldung ohne Wert).

- **QUA-057** · P0 · Status: offen (Ist: externer Penetrationstest steht aus; Prüfwerkzeuge für autonomes Testen installiert, aber nicht lauffähig) — **Penetrationstest und Wiederholung.** Vor der ersten Auslieferung an eine Schule: Test durch Dritte oder ein autonomes Prüfwerkzeug auf der Wegwerf-Instanz mit den Bereichen: Anmeldung und Sitzungen, Zugriffskontrolle (alle Rollen des Rollenfelds), Eingabeverarbeitung und Datei-Upload, Schnittstellen und API-Zugänge, Ausgehende Verbindungen, Überlastschutz (kontrolliert, mit niedriger Schwelle), Geschäftslogik. Nach Behebung wird jeder Fund der Stufen kritisch und hoch **wiederholt geprüft**.
  - Abnahme: Prüfbericht mit Datum, Version, Umfang, Funden und Wiederholungsbeleg; keine offenen Funde der Stufen kritisch und hoch (SIC-010); der Bericht ist Anhang des Release (SIC-011).

- **QUA-058** · P0 · Status: offen — **Fundkatalog des Altsystems als Regressionssatz.** Jeder dokumentierte Befund des Altsystems, der **Verhalten** betrifft (Rechte, Datenumfang, Verschlüsselung, Protokoll, Planungsregeln, Texte, Betrieb), erhält im Neubau einen Negativtest, auch wenn er im Alt behoben wurde. Quellen: die Befundlisten U-01 bis U-116 (davon 10 hoch), die 76 Funde der Bereichsbewertung (42 bestätigt, 11 falsch, 23 unklar), die 169 Funde der Code-Durchsicht (13 hoch), die 17 Funde der Sicherheitsprüfung vom 13.10., die Prüfrunden R0 bis R2 (20, 16, 14 Befunde) und die Checkliste. Befunde zu Code-Stil und toten Codeteilen sind ausgenommen.
  - Abnahme: Tabelle „Altfund → Test-Kennung → Status“ ist vollständig; Stichprobe von 20 Funden: der Test stellt den Fund nach und scheitert gegen eine absichtlich fehlerhafte Variante; „falsch“ markierte Funde bleiben mit Begründung in der Tabelle (nicht stillschweigend gestrichen).

- **QUA-059** · P0 · Status: offen — **Fristen für Funde.** Funde der Stufen kritisch und hoch sind vor Gate G5 behoben und im Re-Test bestätigt; mittlere Funde vor Gate G6 oder mit dokumentiertem Beschluss des Betreibers; niedrige Funde im Backlog mit Frist [Festlegung]. Jeder Fund wird **vor** der Behebung am Code oder per Test nachgeprüft (QUA-011); als „falsch“ bewertete Funde werden begründet geschlossen.
  - Abnahme: Fund-Register (QUA-011) zeigt keine offenen Funde kritisch/hoch beim Gate G5 und keinen mittleren ohne Beschluss beim Gate G6; Stichprobe 5 Funde: Nachstellung und Behebungstest vorhanden.

### 1.9 Betriebsabnahme (Ebene E8)

- **QUA-060** · P0 · Status: Ist (Ist: Update 1.1.0 ging durch, 1.2.0 scheiterte absichtlich und wurde zurückgerollt; Verträglichkeits-Prüfskript: von 51 Änderungen eine nicht verträglich) — **Update und Rollback.** Drei Szenarien auf Wegwerf-Instanz mit gefüllter Datenbank: (a) Update auf Folgeversion erfolgreich (Sicherung `vor-update`, Migration, Gesundheitsprüfung, Unterbrechung 10 bis 30 s, Anmeldungen und Sitzungen bleiben); (b) Update mit absichtlich fehlschlagender Migration → App startet nicht, Fehler im Protokoll, Rollback auf altes Image und Sicherung stellt den alten Stand her; (c) Update mit fehlschlagender Gesundheitsprüfung → automatischer Rückweg mit Meldung. Dazu Zweiknoten-Betrieb: Version n und n+1 laufen gleichzeitig auf demselben Schema.
  - Abnahme: Je Szenario Zeilenzahlen und Prüfsummen der Nutzerdaten vor und nach dem Lauf identisch; Dauer der Unterbrechung gemessen; Rollback dauert höchstens 15 Minuten [Festlegung].

- **QUA-061** · P0 · Status: offen (Ist: Test-Wiederherstellung am 17.10. in einem Container ohne Netz: Datenbank gesund, Plan im richtigen Stand, alle 5.464 Konten lesbar; **Dateiprüfung nur an 5 Dateien**) — **Vollständiger Wiederherstellungs-Rundlauf.** Sicherung der Wegwerf-Instanz (Datenbank und Dateiablage: Atteste, Kursraum-Dateien, Anhänge, Briefe) → leere Instanz ohne Netzzugang → Wiederherstellen mit dem passenden Schlüsselring → Prüfung: alle Konten lesbar, Planungsstand korrekt, **jede** Datei lesbar und entschlüsselbar (Prüfsummenvergleich über alle Dateien); ohne passenden Schlüssel bricht die Wiederherstellung mit klarer Meldung ab, eine beschädigte Sicherung lässt die Datenbank unverändert (Sicherheits-Sicherung „vor-restore“). Wiederholung vierteljährlich auf dem Zielsystem, mit Datum im Betriebshandbuch.
  - Abnahme: Prüfbericht nennt Anzahl Konten, Anzahl Dateien, Anzahl lesbarer Dateien (= Anzahl Dateien), Dauer; Lauf mit falschem Schlüssel → Abbruch mit Meldung; Lauf mit beschädigtem Archiv → Datenbank unverändert.

- **QUA-062** · P1 · Status: Ist (Ist: Probelauf an Kopien der echten Datenbanken am 17.10. ohne Fehler) — **Probelauf an Datenbank-Kopie.** Vor jedem Aufspielen auf eine echte Instanz läuft das Update an einer **Kopie** deren Datenbank (und ggf. Dateiablage): Migration, Start, Gesundheitsprüfung, Stichproben, Rücksetzweg (Image-Tag plus Datenbank-Kopie). Die Kopie wird nach dem Lauf gelöscht (QUA-028); der Probelauf nennt Zeilenzahlen aller Tabellen vor und nach (Abschnitt 2.7).
  - Abnahme: Probelauf-Protokoll mit Datum, Versionen, Dauer, Zeilenzahlen; Kopie nach dem Lauf nicht mehr vorhanden.

- **QUA-063** · P1 · Status: offen (Ist: Statusseite und Fehlerprotokoll gebaut; Alarmregeln als Vorlage; E-Mail-Alarm aus der App offen) — **Alarme und Statusseite.** Jede Alarmregel und jeder Prüfpunkt der Statusseite wird mit gesenkter Schwelle oder künstlichem Zustand ausgelöst: Datenbank nicht erreichbar (Gesundheitsprüfung 503), Sicherung zu alt oder fehlgeschlagen, Datenträger fast voll, Lizenzstufe, Wartungslauf überfällig, Fehlerrate, Zertifikat bald abgelaufen, Massenzugriffs-Alarm (DAT-032).
  - Abnahme: Je Regel ein Test „Zustand erzeugen → Alarm bzw. Statusfarbe innerhalb der Frist → Zustand beheben → Alarm endet“; Regel ohne Test gilt als nicht abgenommen.

- **QUA-064** · P1 · Status: offen — **Einrichtung einer neuen Schule ohne Entwicklerwissen.** Eine Person ohne Entwicklerwissen richtet mit Betreiberpaket und Einrichtungsassistent die Beispielschule „Berufskolleg“ ein (Stammdaten, Zeitraster, Stundentafeln, Konten, Zugangsbriefe, erster Stundenplan) in **höchstens 60 Minuten**; der Ablauf ist protokolliert (Schritte, Zeit, Stolpersteine).
  - Abnahme: Protokollierter Rundgang mit Stoppuhr; jede Hilfe, die der Prüfer geben musste, ist ein Fund (mittel); Ergebnis: eingerichtete Schule besteht den Rundgang QUA-046 für Administration und Sekretariat.

- **QUA-065** · P0 · Status: offen (Ist: Rotation gebaut; innere Token des Plans blieben am alten Schlüssel) — **Schlüsselverwaltung.** Schlüsselrotation ohne Ausfall (neuer Schlüssel vorn, alter im Ring): danach ist **kein** Datenschlüssel einer registrierten Spalte mehr mit dem alten Hauptschlüssel verhüllt (Stichprobe über jede Registerspalte, inklusive innerer Token des Planungsdokuments), Entschlüsselung mit nur dem neuen Schlüssel gelingt; fehlender Schlüssel → Start mit klarer Meldung (ohne Wert); Schlüssel werden nicht im Klartext gesichert.
  - Abnahme: Test rotiert auf einer Wegwerf-Instanz und prüft jede Registerspalte (SIC-005); ein Lauf ohne alten Schlüssel liest alles; ein Lauf ohne Schlüssel startet nicht.

---

## 2. Querschnitts-Abnahmetests

Ein Querschnitts-Abnahmetest prüft **eine Eigenschaft über alle Routen bzw. Seiten** und wird aus dem Routen-Register erzeugt, nicht von Hand je Route geschrieben. Dadurch lässt sich keine neue Route „vergessen“: Wird eine Route ohne Registereintrag angelegt oder trägt sie eine Eigenschaft nicht, scheitert der Test (Default-Deny, SIC-004). Die Querschnittstests laufen auf Ebene E3 (Rechte, 404, Audit, Texte, Drosselung, weitere Register-Prüfungen) bzw. E4 (Verschlüsselung, Migration); Fachverhalten prüfen die Fachdateien. Alle Läufe geschehen auf einer Wegwerf-Instanz (SIC-009) mit frischer Datenbank, der Beispielschule (QUA-034 b) und fester Uhr.

Bestand (Alt): 716 Endpunkte in 24 Bereichen; einzelne Querschnittstests existierten (404-Regel über rund 40 Kursraum-Routen und 42 Fälle aus Sicht fremder Schüler/innen, Zuschauer-Rundgang über 274 Lese-Adressen, Rechte-Matrix gegen die Architekturtabelle, „freigegebene Route braucht Bereich“, Registry-Prüfungen für Verschlüsselung und Datenarten). **Lücken (Alt):** keine Prüfung „jede Schreibroute erzeugt genau einen Audit-Eintrag“, keine Marker-Suche über Datenbank, Dateien, Protokolle und Sicherungen, keine Sie-Form-Prüfung der Server-Texte, keine Prüfung von Rücknahme und Atomarität über alle Abläufe.

### 2.1 Register, Rollenfeld und Gegenprobe

**Spalten des Routen-Registers** (maschinenlesbar, eine Zeile je Pfad und Methode):

| Spalte | Inhalt |
|---|---|
| Pfad, Methode, Modul, Fachbereich | Adresse, HTTP-Methode, zugehöriges Modul, Fachbereich (Kürzel der Fachdateien) |
| Schutzart | `öffentlich`, `angemeldet`, `Recht` (mit Rechte-Name und Umfang), `nur Administration`, `nur Inhaber`, `nur Betrieb (Token)` |
| Objekt-Verweise | Pfadparameter und Körperfelder, die ein fremdes Objekt benennen können (Konto, Schüler/in, Klasse, Kurs, Datei, Chat …) |
| schreibend | ja / nein; GET ändert nie Zustand (Ausnahme: ausdrücklich gelistete Lesemarkierungen) |
| Audit | Aktion im Schema `Bereich.Verb`, Granularität (je Aufruf / je Objekt) oder Ausnahme-Kennung A1 bis A3 (DAT-031) |
| Verschlüsselte Felder | Liste der Freitext-Felder der Anfrage, die gespeichert verschlüsselt sein müssen |
| Freigaben | Demo, Ansichtskonto, API-Schreibzugang, Export: je `ja` / `nein` (Standard `nein`) |
| Drosselklasse | `Anmeldung`, `Konto-Code`, `Upload`, `Chat`, `Standard`, `frei` (Ereignisstrom, Gesundheit, Metriken, statische Dateien) |
| Rücknehmbar | Gegenroute oder `unwiderruflich` mit Begründung (Löschkonzept) |
| Beispielanfrage | gültiger Körper und gültige Parameter für die Positivprüfung |
| Eingabemodell | strikt (unbekannte Felder → 422, SIC-066) |

**Rollenfeld** (feste Testpersonen, je Instanz A und eine zweite Instanz „B“ mit fremden Objekten; Konto A hat Objekte in Klasse K1, Konto B in Klasse K2):

| Kennung | Person | Zweck |
|---|---|---|
| R01 | `admin` (technische Administration, nicht Inhaber) | Rechte ohne Gesundheits-, Noten-, Förderdaten (SIC-016) |
| R02 | Inhaber-Konto (`SM_ADMIN_USER`) | Inhaber-Schutz (SIC-021) |
| R03 bis R06 | `schulleitung`, `abteilungsleitung` (eigener Zweig), `planer`, `sekretariat` | Personalrechte, Zweig-Umfang |
| R07 | `lehrer`, Fachunterricht in K1, keine Klassenleitung | Umfang `own_classes`, `own_courses` |
| R08 | `lehrer`, Klassenleitung von K1 | Umfang `class_teacher` (Atteste, Krankmeldungen) |
| R09 | `lehrer` ohne Bezug zu K1 | fremde Klasse |
| R10, R11 | `hausmeister`, `schulbegleitung` (begleitet ein Kind) | eingeschränkte Positivlisten (SIC-017/018) |
| R12 | `schueler` minderjährig in K1 | Selbstbedienung, eigene Daten |
| R13 | `schueler` volljährig in K1 | Selbstmeldung, Entscheidung über Elternsicht |
| R14 | `schueler` in K2 (Konto B) | fremde Schülerdaten |
| R15 | `eltern` eines minderjährigen Kindes in K1 | Elternsicht |
| R16, R17 | `eltern` eines volljährigen Kindes ohne bzw. mit Freigabe je Bereich | Volljährigkeit und Elternfreigabe |
| R18 | `eltern` mit zwei Kindern in zwei Klassen | Kinderwahl je Konto |
| R19 | `eltern` eines Kindes in K2 (Konto B) | fremdes Kind |
| R20, R21 | `monitor` (Standort 1), `zuschauer` | Ansichtskonten, Allowlist (SIC-020) |
| R22 bis R26 | je eine **eigene Rolle** der Grundtypen `personal`, `lehrkraft`, `schueler`, `eltern`, `ansicht` mit **allen** Rechten vergeben | Scope-Grenze je Grundtyp, feste Mindestregeln (SIC-015, SIC-017) |
| R27 | persönliches API-Token (Rechte des Kontos) | Token-Wege |
| R28, R29 | API-Zugang lesend mit Umfang; API-Zugang schreibend mit Pflichtlaufzeit | Umfang und Allowlist (SIC-064) |
| R30 | nicht angemeldet | 401 und öffentliche Routen |
| R31, R32 | Konto mit Pflicht-Passwortwechsel; Konto mit offener Pflicht-Zwei-Faktor-Einrichtung | Sperre aller Wege außer Anmeldung (403 `password_change_required`, `totp_setup_required`) |
| R33 | deaktiviertes bzw. ausgetretenes Konto | Sitzung und Token ungültig |

- **QUA-066** · P0 · Status: offen (Ist: „freigegebene Route braucht Bereich“-Test; Register nur teilweise) — **Routen-Register ist vollständig.** Jede im Anwendungsrahmen registrierte Route (auch öffentliche, Ereignisstrom, Gesundheit, Metriken, Dateiauslieferung, Kalender-Feeds, Anbieter-Portal) hat genau einen Registereintrag mit allen Pflichtspalten; jeder Registereintrag hat eine Route.
  - Abnahme: Test A zieht die Routentabelle aus dem Rahmen und vergleicht mit dem Register: 0 Routen ohne Eintrag, 0 Einträge ohne Route, 0 Einträge mit leerer Pflichtspalte; eine absichtlich neu angelegte Route ohne Eintrag lässt den Test scheitern (Gegenprobe, QUA-069).

- **QUA-067** · P0 · Status: offen — **Rollenfeld ist deterministisch und vollständig.** Ein Befehl erzeugt das Rollenfeld R01 bis R33 mit je einem eigenen und einem fremden Objekt je Fachbereich (Krankmeldung, Attest, Förderdatum, Note, Notenbuch-Eintrag, Klassenbuch-Notiz, Nachricht, Chat, Kursraum-Material, Aufgabe, Formular-Antwort, Datei, Klassentermin, Benachrichtigung, Zugangsbrief). Zugangsdaten werden je Lauf erzeugt und erscheinen nie in Berichten (QUA-037).
  - Abnahme: Zweimaliger Lauf mit gleichem Startwert → identischer Hash der Fachdaten; Zählung: je Person mindestens ein eigenes und ein fremdes Objekt je Objektart; fehlt eine Person oder Objektart, scheitert die Selbstprüfung des Rollenfelds.

- **QUA-068** · P1 · Status: offen (Ist: Registry der Oberflächen-Module mit Test, Seitenregeln im Code) — **Seiten-Register der Oberfläche.** Jede Seite hat einen Eintrag: Adresse, Zugriffsregel (öffentlich / angemeldet / Recht / Rolle, OBE-103), Erreichbarkeit (Menüeintrag, Startkachel oder Link, OBE-101), Hauptüberschrift, Zählung im Menü je Rolle (OBE-112). Kernpfade sind selbst gesperrt, Unterpfade erlaubt.
  - Abnahme: Test vergleicht Seitenmenge und Register: 0 Seiten ohne Eintrag, 0 Seiten ohne Weg, 0 Seiten ohne Hauptüberschrift (Alt-Fund U-43); ein Konto ohne Recht sieht den Menüeintrag nicht und erhält beim direkten Aufruf die Seite „Kein Zugriff“ **im App-Rahmen** mit Weg zurück (Alt-Fund U-38).

- **QUA-069** · P1 · Status: offen — **Gegenprobe: Querschnittstests sind selbst geprüft.** Zu jedem Querschnittstest gehört eine absichtlich verletzende Testroute bzw. Testseite in einer Testanwendung (ohne Audit, mit 403 statt 404, mit Klartext-Feld, in Du-Form, mit nativem Dialog, ohne Drosselklasse, ohne Rücknahme, ohne Eintrag im Register), an der der Test **scheitern muss**.
  - Abnahme: Je Querschnittstest ein Gegenprobe-Fall in der Testanwendung; Lauf der Gegenproben: alle erwarteten Fehlschläge treten ein; ein Querschnittstest ohne scheiternde Gegenprobe wird im Bericht als „unwirksam“ geführt und blockiert das Gate.

### 2.2 Rechte (Ebene E3)

- **QUA-070** · P0 · Status: offen (Ist: Rechte-Matrix je Fachbereich und Rollen-Rundgänge; keine vollständige Route × Person-Matrix) — **Rechte-Matrix über alle Routen.** Eine Soll-Matrix (Datei: Route × Person → `erlaubt` / `401` / `403` / `404`) wird von der Abnahme **unabhängig vom Register** aus den Fachdateien REC und SIC abgeleitet. Der Test ruft jede Route mit jeder Person R01 bis R33 mit der Beispielanfrage auf. `erlaubt` bedeutet: keine Abweisung aus Rechtegründen (Antwort 2xx oder fachlicher Fehler wie 409/422). Nicht angemeldet → 401, angemeldet ohne Recht → 403 bzw. 404 nach SIC-013, Ansichtskonto bei Schreibzugriff → 403, Pflichtwechsel und Pflicht-Zwei-Faktor → 403 mit Code.
  - Abnahme: 0 Abweichungen zur Soll-Matrix; Abweichung „mehr Zugriff als Soll“ ist Fund hoch (bei Gesundheits-, Noten-, Förder-, Konten-, Schlüsseldaten kritisch), „weniger Zugriff“ Fund mittel; die Soll-Matrix enthält pro Route und Person eine Zeile und wird mit Datum versioniert; eigene Rollen R22 bis R26 erhalten auch bei Vergabe **aller** Rechte nie mehr, als die festen Mindestregeln erlauben (SIC-015 bis SIC-019).

- **QUA-071** · P0 · Status: offen (Ist: Teilmaßnahmen, Lücken bei API-Token und Herabstufung) — **Rechteänderungen und Widerruf wirken sofort.** Entzug eines Rechts, Herabstufung, Deaktivierung, Passwortwechsel, Austritt, Klassenwechsel, Änderung der Zweig-Zuordnung, Ablauf eines API-Tokens und der 18. Geburtstag wirken **ab der nächsten Anfrage** derselben Sitzung bzw. desselben Tokens, auch bei mehreren Prozessen oder Knoten; Zwischenspeicher dürfen Rechte nicht länger halten.
  - Abnahme: Je Ereignis ein Test mit zwei Sitzungen (vor und nach der Änderung): nächste Anfrage → 401/403/404 bzw. neuer Umfang; Zweiknoten-Lauf: Änderung auf Knoten 1, nächste Anfrage an Knoten 2 → neuer Stand; Volljährigkeit mit fester Uhr 1 s vor und nach Mitternacht (QUA-019).

- **QUA-072** · P0 · Status: offen (Ist: Demo-Freigabeliste, Zuschauer-Allowlist; Lücke: Schreib-Token- und Export-Wege als Sperrliste) — **Default-Deny in vier Kontexten.** In den Kontexten Ansichtskonto/Zuschauer, Demo-Betrieb, API-Schreibzugang und Export ist jede Route ohne ausdrückliche Freigabe im Register gesperrt; veraltete Freigabeeinträge (Route existiert nicht mehr) sind ein Fehler.
  - Abnahme: Test zählt alle Routen und ruft sie in den vier Kontexten ab: nur Allowlist-Routen antworten; Zuschauer-Rundgang über **alle** Lese-Adressen (Alt: 274) → nur Allowlist liefert Daten, jede ändernde Anfrage und jede Stammdaten-Exportroute → 403; im Demo-Betrieb verändert keine nicht freigegebene Schreibroute Daten (Zeilenzählung aller Tabellen vor und nach); eine neu hinzugefügte, nicht freigegebene Route lässt den Test grün (gesperrt), ein veralteter Freigabeeintrag lässt ihn scheitern.

- **QUA-073** · P0 · Status: offen (Ist: Selbstaussperr-Schutz im Dienst; Inhaber-Schutz nur auf dem direkten Weg) — **Schutzregeln gelten auf jedem Zugangsweg.** Inhaber-Schutz, Selbstaussperr-Schutz, Rollen-Grenzen, Eltern-Sicht und Umfang liegen im Dienst und werden über **jeden** Weg geprüft: Einzelroute, Massenroute, Stapel-Zugangsbriefe, Import, Export, Befehlszeile, API-Zugang, Hintergrundjob.
  - Abnahme: Je Schutzregel ein Test je Weg (Matrix Schutzregel × Weg); alle Wege verweigern mit identischem Ergebnis, und der Audit-Eintrag der Verweigerung (z. B. `user.owner_protected`) entsteht auf jedem Weg; ein fehlender Weg in der Matrix ist ein Fehler im Test (Vollständigkeitsprüfung der Matrix).

### 2.3 404 für fremde Daten (Ebene E3)

Betreiberregel (16.10.): „Fremde Daten liefern 404, nicht 403.“ Spätere Regel überstimmt frühere Alt-Praxis (unbekannte oder fremde Schüler-ID → 403, Kürzel „nicht geheim“); im Neubau gilt 404 für alle fremden, unsichtbaren und unbekannten Objekte nach SIC-013.

- **QUA-074** · P0 · Status: offen (Ist: 42 Fälle aus Sicht fremder Schüler/innen und rund 40 Kursraum-Routen; Klassenbuch, Kursräume und Schüler-Selbstbedienung nachgezogen; Ziel 100 %) — **Fremdes Objekt → 404 an jeder ID-Route.** Für jede Route mit Objekt-Verweis fragt eine Person mit gültigem Recht, aber ohne Bezug zum Objekt (z. B. R12 gegen Objekt von R14, R07 gegen K2, R15 gegen R19-Kind, R09 gegen K1) das Objekt von Konto B ab.
  - Abnahme: Status 404; Antworttext gleich dem Text bei nicht vorhandener ID (Vergleich nach Entfernen von Fehlernummer und Zeitstempel); Median der Laufzeiten unterscheidet sich um höchstens 50 ms [Prüfwert, SIC-Lesehinweis] über 50 Wiederholungen; keine Daten im Körper; Abdeckung **100 %** der Routen mit Objekt-Verweis (Ausweis: Anzahl geprüfter / Anzahl Routen); Objektarten mindestens: Konten, Noten, Notenbuch, Kompetenzen, Klassenbuch, Krankmeldungen, Atteste/Dokumente, Förderdaten, Formulare, Nachrichten, Chats, Kursräume, Klassentermine, Selbstauskunft, Elternzugang, Dateien, Klassen, Benachrichtigungen.

- **QUA-075** · P0 · Status: offen — **Listen, Suche und Zusammenfassungen verraten nichts.** Objekte der Instanz B tragen Marker (QUA-081). Person A ruft **alle** Lese-Routen ab, auch Listen, Suche, Empfängerauswahl, Zähler, Statistik, Exporte (soweit erlaubt), Ereignisstrom, Kalender-Feeds und Selbstauskunft.
  - Abnahme: Keine Antwort enthält einen Marker von B; Gesamtzahlen, Seitenzahlen, Zähler und Summen zählen Objekte von B nicht mit; die Empfängersuche von Schüler/innen liefert keine Mitschüler/innen und keine Klassen fremder Kinder (SIC-032); Eltern sehen nur eigene Kinder.

- **QUA-076** · P0 · Status: offen — **Schreibversuche auf fremde Objekte ändern nichts.** POST, PUT, PATCH und DELETE auf fremde Objekte, auf Kindobjekte fremder Objekte, mit fremder ID im Körper und in Massenaktionen mit gemischter Liste (eigene und fremde Objekte) → 404; Massenaktionen mit auch nur einem fremden Objekt wirken **als Ganzes nicht** (keine Teilwirkung) [Festlegung].
  - Abnahme: Zeilen-Hash der betroffenen Tabellen vor und nach dem Versuch identisch; Audit enthält keinen Erfolgseintrag; Löschen fremder Dateien → 404 und Datei bleibt lesbar für den Besitzer.

- **QUA-077** · P0 · Status: offen — **Ausnahmen vom 404 sind eine geschlossene, datierte Liste.** Ein Status 403 an einer Route für eine Person des Rollenfelds ist nur zulässig für die Fälle (a) bis (f) der Regel (SIC-013): Objekt sichtbar, aber Aktion nicht erlaubt und die Meldung hilft; kein Konto zu verbergen; Inhaber-Konto; Lehrkonto ohne Zuordnung; Schreibversuch eines Ansichtskontos; Schreibversuch einer Elternrolle im Kursraum.
  - Abnahme: Die Ausnahmeliste (Route, Person, Fall a bis f, Begründung, Datum) liegt als Datei vor; der Test meldet jede 403-Antwort außerhalb der Liste als Fehler und jeden Listeneintrag ohne 403 als veraltet; die Liste wird bei jeder Änderung begründet und datiert (kein stilles Wachsen).

### 2.4 Protokollierung (Ebene E3)

- **QUA-078** · P0 · Status: offen (Ist: Audit auf den meisten Schreibwegen; Lücken Wartung, Upload/Löschen, iCal-Link, Postfach-Einstellungen, Ordner; Test „jede Schreibroute“ fehlte) — **Jede schreibende Route erzeugt genau einen Audit-Eintrag.** Der Test ruft **jede** schreibende Route als erlaubte Person auf und zählt die Audit-Zeilen vorher und nachher: genau so viele neue Zeilen wie im Register angegeben (Standard 1), mit Aktion `Bereich.Verb`, Ziel (höchstens 200 Zeichen), Konto, Zeit in UTC (`Z`), IP und bei Token-Zugriff Token-ID. Automatische Änderungen (Auto-Planer, Wartungslauf, Lizenzprüfung, Sicherung, Jahreswechsel) erzeugen Eintrag „system“. Ohne Audit dürfen nur die drei Ausnahmen A1 bis A3 bleiben (Löschen eigener Benachrichtigungen, Zwischenspeichern von Selbsttest-Antworten, einzelne gesendete Chat-Nachrichten und Lesemarkierungen; DAT-031). GET-Routen ändern nie Zustand.
  - Abnahme: 0 schreibende Routen ohne Eintrag außerhalb A1 bis A3; eine vierte Ausnahme lässt den Test scheitern; nach Aufruf **aller** GET-Routen sind die Fachtabellen unverändert (Zeilen-Hash; Alt-Lehre: Anlegen von Zeilen beim Lesen); Gegenprobe mit Testroute ohne Audit.

- **QUA-079** · P0 · Status: offen — **Audit enthält keine Inhalte.** Alle in QUA-081 eingesetzten Marker und Passwort-, Code- und Token-Werte tauchen im Audit nicht auf; Löschgründe nur als Länge (Grund verschlüsselt); Anfragekörper und Abfrageparameter nie; `student_absence.*`-Einträge ohne Gründe und für die technische Administration nicht mit Schüler-ID und Zeitraum sichtbar (SIC-025).
  - Abnahme: Nach Passwortwechsel, Kontakt-Änderung, Löschung mit Grund, Anbieter-Konfiguration und einem Lauf von QUA-081 liefert die Volltextsuche im Audit **0 Treffer** für Klartextwerte; Audit-Abruf als `admin` (R01) zeigt keine `student_absence.*`-Zeilen mit Schüler-ID.

- **QUA-080** · P0 · Status: offen — **Verweigerungen, Lesezugriffe und Unveränderbarkeit.** Protokolliert werden außerdem: Verweigerungen von Schutzregeln (z. B. `user.owner_protected`), Fehlversuche der Anmeldung (`auth.login_failed`), Lesezugriffe auf Förderdaten und Atteste (ohne Inhalt), Fremdabrufe von Dateien, jeder Export und jede Auskunft (DAT-021, DAT-022). Das Audit und die Fachprotokolle (Meldeprotokoll, Notenbuch-Änderungsprotokoll) sind **nur ergänzbar**.
  - Abnahme: Je Zeile der Pflicht-Ereignisliste (DAT-021) ein Test mit Aktion und Ziel; Versuch, einen Audit- oder Meldeprotokoll-Eintrag über Anwendung oder Datenbankbenutzer der Anwendung zu ändern oder zu löschen → scheitert; Rücknahme einer Krankmeldung lässt den Protokolleintrag bestehen.

### 2.5 Verschlüsselung der Freitexte (Ebene E4)

- **QUA-081** · P0 · Status: offen (Ist: Verschlüsselung in über 30 Dateien; Planungsdokument erst am 17.10. nachgezogen; Vollständigkeit nicht belegt) — **Marker-Suche über alle Speicherorte.** Der Test füllt **jedes** verschlüsselt zu speichernde Feld jeder schreibenden Route (Spalte „Verschlüsselte Felder“ des Registers) mit einem eindeutigen Marker `QUA-MARKER-<Routen-Nr>-<Feld>-<Zufall>`, liest ihn über die Schnittstelle als berechtigte Person zurück (Marker erscheint) und durchsucht danach: alle Tabellen und Spalten der Datenbank einschließlich Binärfeldern und Journal-/Protokolldateien der Datenbank, die Dateiablage einschließlich Dateinamen und Inhalten, Planversionen, Anwendungs-, Zugriffs- und Fehlerprotokoll, Audit, Postausgang nach Zustellung, Sicherungsarchive (Datenbank und Dateien), temporäre Verzeichnisse, Zwischenspeicher und Job-Warteschlangen. Gesucht wird in den Kodierungen UTF-8, UTF-16, URL-kodiert und Base64 [Festlegung].
  - Abnahme: **0 Klartext-Treffer** außerhalb der geschlossenen Liste bewusst unverschlüsselter Daten (DAT-018); die Dateiablage enthält nur Dateien mit dem Kopf `SMS1`; Marker in Dateiname und Dateiinhalt eines Uploads werden nicht gefunden; Gegenprobe mit einem Klartext-Testfeld schlägt an.

- **QUA-082** · P0 · Status: offen — **Bindung und Fehlerverhalten.** Jedes verschlüsselte Token ist an seine Zeile gebunden (DAT-002); Klartext in einer registrierten Spalte ist beim Lesen ein Fehler (DAT-006); ein nicht lesbarer Eintrag wird nie still überschrieben.
  - Abnahme: Für jede Bindungszeile der Tabelle in DAT-002: Token in eine andere Zeile derselben Spalte kopiert → Lesefehler; Klartext in einer `_enc`-Spalte → Lesefehler; Speichern eines Klassenbuch-Eintrags mit nicht lesbarer Notiz → 409 und die Notiz bleibt unverändert, die Seite zeigt „nicht lesbar“; Chiffretext aus Instanz A in Instanz B → kontrollierter Fehler (QUA-039).

- **QUA-083** · P0 · Status: offen (Ist: Registry-Prüfungen für Rotation, Datenart, Dateizugriff, Export) — **Register der verschlüsselten und der bewusst unverschlüsselten Spalten ist vollständig.** Per Schema-Abfrage werden alle Text- und Binärspalten aller Tabellen gelesen: jede ist entweder im Verschlüsselungs-Register (mit Rotations-Eintrag) oder im Katalog bewusst unverschlüsselter Daten mit Begründung (DAT-018); jede Tabelle mit Personenbezug hat eine Datenart (Frist, Löschfunktion mit Trockenlauf, Auskunft, Betroffenen-Ermittlung); jeder Verweistyp für Dateien hat eine Zugriffsprüfung; jeder Export ist registriert (SIC-005).
  - Abnahme: Eine neue Text-Spalte ohne Eintrag, eine `_enc`-Spalte ohne Rotations-Eintrag, eine Tabelle mit Personenbezug ohne Datenart und ein unregistrierter Export lassen den Test scheitern (vier Gegenproben); Schlüsselrotation verschlüsselt jede Registerspalte neu (QUA-065).

### 2.6 Texte und Oberfläche über alle Routen und Seiten (Ebene E3, ergänzt durch E5)

- **QUA-084** · P0 · Status: offen (Ist: Sie-Form seit 16.10. umgesetzt und in der Code-Durchsicht als „überall“ befunden; Prüfung von Hand, ältere Fassungen im Du) — **Sie-Form-Prüfung.** Betreiber (16.10.): „Alle Texte in Sie-Form, auch für Schüler/innen.“ Geprüft werden **alle** Texte, die eine Person erreichen: Oberflächentexte (Textkatalog), Antworttexte und Fehlermeldungen **jeder Route** (der Test löst je Route einen Validierungsfehler mit leerem Körper und einen Rechtefehler aus und liest den Text), E-Mail- und SMS-Vorlagen, PDF-Vorlagen (Zugangsbriefe, Elternbriefe, Berichte), Hilfetexte, Handbuch, Betreiber-Hilfe, Benachrichtigungstexte, Anbieter-Portal, sichtbare Texte der Beispielschulen.
  - Abnahme: Textprüfung findet **0** Formen von „du, dich, dir, dein/e/n/m/r/s, euch, euer/e/n/m/r/s“ (Groß- und Kleinschreibung; Ausnahme nur Zitate in Nutzerinhalten, Liste leer); Zugangsbrief für ein minderjähriges Kind und Fehlermeldung an eine Schülerin enthalten Sie-Formulierungen; Stichprobe von 20 Texten je Rolle (Schüler/in, Eltern, Lehrkraft) wird von einer Person gelesen (Imperativ-Formen wie „Gib ein“ sind maschinell nicht findbar): 0 Du-Anreden; Gegenprobe: der Text „Willst du dich wirklich abmelden?“ wird gefunden.

- **QUA-085** · P0 · Status: offen (Ist: Test erfasste nur die Klasse „explain“; rund 65 Restfälle mit Ausnahmeliste) — **Erklärungen nur über die Hilfe.** Es gibt keine erklärenden Absätze, keine grauen Erklärsätze unter Überschriften, keine dauerhaften Hinweisboxen als Erklärtext (OBE-003). Erlaubt bleiben nur Fehlertexte, Leerzustände, Formatangaben, Hinweise zu einem echten Zustand und rechtlich nötige Hinweise – als markierte Komponenten, nicht als freie Absätze. Native Tooltips (`title`) ersetzen die Hilfe nicht. Interne Begriffe (Kennungen, Feldnamen, „Block“, „Planungsdokument“, Wochenbuchstabe, „Wunschklassen“, englische Job-Status) erscheinen nie.
  - Abnahme: Der Seitenlauf (E5) zählt alle statischen Textblöcke mit mehr als 12 Wörtern außerhalb der erlaubten Komponenten: Ergebnis **0** bei **leerer** Ausnahmeliste; Suche nach `title`-Attributen mit Erklärtext: 0; Verbotsliste interner Begriffe: 0 Treffer in Oberfläche und Servertexten; Hilfetexte haben 1 bis 3 Sätze, reinen Text, keine Links (OBE-121); Gegenprobe mit einem 30-Wörter-Absatz scheitert.

- **QUA-086** · P0 · Status: Ist (Ist: Browser-Dialoge durch App-Dialoge ersetzt, Testregel gegen neue) — **Keine Browser-Dialoge.** Weder native Bestätigen-, Hinweis- noch Eingabe-Dialoge (auch nicht für Passwort- und Token-Felder). Einzige Ausnahme (OBE-007): die Browser-Rückfrage beim Schließen des Tabs, solange ein Datei-Upload läuft.
  - Abnahme: Statische Suche im Quelltext der Oberfläche findet 0 Aufrufe der nativen Dialoge; im Seitenlauf (E5) registriert das Prüfskript Dialog-Ereignisse des Browsers und meldet **jedes** als Fehler (außer Tab-Schließen während eines Uploads); jede destruktive Aktion des Seiten-Registers öffnet einen App-Dialog mit Fokusfalle, Esc und genau einer Hauptaktion (OBE-028/029).

- **QUA-087** · P1 · Status: offen (Ist: Fehlerübersetzung für bekannte Codes; Altfunde „Field required“ in Englisch, Rohschlüssel, Fehler ohne Nummer) — **Fehlermeldungen für Menschen, je Route.** Alle Fehlercodes des Servers haben einen deutschen Satz in Sie-Form ohne Technikbegriffe (OBE-041); unbekannte Codes zeigen „Das hat nicht geklappt“ mit Fehlernummer (OBE-042); ein 500 trägt Fehlernummer in Antwort und Protokoll (SIC-068); der Fehler erscheint am richtigen Feld (OBE-049).
  - Abnahme: Je Route mit Eingabemodell: Aufruf mit leerem Körper, mit zu langem Wert und mit falschem Typ → 422 mit deutschem Satz je Feld, keine englischen Wörter, keine Feldnamen des Servers; Katalogtest: jeder Fehlercode im Server-Katalog hat eine Übersetzung (0 ohne); künstlicher 500 → Fehlernummer in Antwort und Protokoll gleich; Stichprobe „Datum fehlt“ zeigt „Bitte ein Startdatum angeben.“.

- **QUA-088** · P0 · Status: offen (Ist: gemeinsamer Raster-Baustein, zweiter Baustein für Tag-×-Stunde-Ansichten im Altbestand) — **Ein Raster für alle Tag-×-Stunde-Ansichten.** Betreiber (13.10.): „Du sollst immer dieses Stundplan Raster benutzen und dann halt custom für die bestimmten Use Cases benutzen.“ Jede Ansicht des Seiten-Registers mit Tagen als Spalten und Stunden als Zeilen (Klasse, Lehrkraft, Raum, Schüler/in, Eltern, Klassenbuch, Aufsichten, Verfügbarkeit, Monitor, Wochenplan) verwendet den einen Baustein; Abweichungen betreffen nur Zellinhalt oder Variante (OBE-008, OBE-094).
  - Abnahme: Der Seiten-Test schlägt fehl, sobald eine Ansicht mit Tagen × Stunden ohne den Raster-Baustein gebaut ist; Bildschirmfoto-Vergleich der Ansichten: Kopfzeile, Zeitspalte, Zellhöhe, Schraffur („gesperrt“/„gefehlt“), Heute-Markierung und Statusfarben identisch; Gegenprobe: Testseite mit eigener Tabelle für Tage × Stunden scheitert.

- **QUA-089** · P2 · Status: offen (Ist: Altfunde „1 Einträge“, „1 Hinweise“, „Lehrkraft“ neben „Lehrende“, Emojis als Icons) — **Begriffe, Mehrzahl und Schreibweise.** Eine Glossar-Datei legt Begriffe fest (z. B. „Kursraum“, „Woche 1“, „Stunde/Doppelstunde“, „Planung“, „Lehrkraft“); eine Mehrzahl-Funktion erzeugt „1 Eintrag“ / „3 Einträge“; Zahlen und Daten folgen der deutschen Schreibweise (Komma als Dezimaltrennzeichen, Datum TT.MM.JJJJ); keine Emojis oder Glyphen als Symbole (nur Symbolsatz).
  - Abnahme: Test sucht verbotene Begriffe und feste Mehrzahlmuster („1 Einträge“, „1 Kursräume“, „3 Attest fehlt“) in Oberfläche und Servertexten: 0 Treffer; Suche nach Emoji-Zeichen im Quelltext der Seiten (außer Emoji-Auswahl und Nutzerinhalten): 0 Treffer.

### 2.7 Migrationstest (Ebene E4)

- **QUA-090** · P0 · Status: Ist (Ist: Migrationen mit SQLite und PostgreSQL 16 getestet; Prüfung Modell gegen Schema) — **Frische Datenbank, zweiter Start, Schema-Abgleich.** Alle Migrationen laufen auf frischer Datenbank ohne Fehler; ein zweiter Start ändert nichts; der Abgleich Modelle gegen Schema findet keine Differenz; es gibt genau **einen** Migrationskopf (Mehrfach-Köpfe werden vor dem Release zusammengeführt); jede Schemaänderung ist genau eine Revision; eine absichtlich fehlerhafte Migration verhindert den Start mit Nennung der Revision. Tests prüfen den Kopf über die Funktion des Migrationswerkzeugs, nie gegen eine feste Revisionsnummer (Alt-Lehre: Test mit fester Revision brach bei jeder neuen Migration).
  - Abnahme: Lauf auf SQLite **und** PostgreSQL 16; Modelländerung ohne Migration → Abgleichstest scheitert; zweiter Start: keine Änderung (Zeilen-Hash); zwei Köpfe → Test scheitert.

- **QUA-091** · P0 · Status: offen (Ist: gespeicherte Altversionen für einzelne Formate; Archiv je Epoche nicht vollständig) — **Aufwärtsmigration aus gespeicherten Altversionen mit Daten.** Je Release und je Format-Epoche liegt eine gefüllte Datenbank (Rollenfeld R01 bis R33, Beispielschule, verschlüsselte Felder, Dateien, Planversionen, Altdokumente des Planungsdokuments) im Archiv. Jede wird auf den aktuellen Kopf migriert.
  - Abnahme: Je Archivstand: Migration ohne Fehler; Zeilenzahlen aller Tabellen und Prüfsummen der Fachdaten gleich dem Erwartungswert (Datei); alle verschlüsselten Felder lesbar; alte Planungsdokumente laden verlustfrei (Wochenzyklus, Rhythmus, Zeitfenster); Beispielschulen älterer Formate laden (QUA-038); abwärts nur dort geprüft, wo die Revision eine Rückrichtung erklärt.

- **QUA-092** · P0 · Status: Ist (Ist: Prüfskript für die Expand-Regel; Regressionstest gegen verlorene Kind-Zeilen bei Tabellen mit kaskadierenden Fremdschlüsseln; ein Fund aus 51 Änderungen) — **Expand-Regel und kaskadierende Tabellen.** Die Verträglichkeitsprüfung (BET-034/035) meldet Löschen, Umbenennen, Typänderung und NOT NULL ohne Standardwert; Tabellenumbauten an Tabellen mit kaskadierenden Fremdschlüsseln (Konten, Kursraum-Ordner) behalten alle Kind-Zeilen (BET-036).
  - Abnahme: Testmigrationen „Spalte löschen“ und „Typ ändern“ werden als Verstoß gemeldet, „neue Spalte mit Standardwert“ nicht; Migrationstest auf gefüllter Datenbank (Konten mit Kursraum-Ordnern und Material): Zeilenzahlen **aller** abhängigen Tabellen vor und nach gleich; Version n und n+1 laufen gleichzeitig auf einem Schema (Zweiknoten-Test).

- **QUA-093** · P0 · Status: offen — **Datenübernahme aus dem Altsystem und Trockenlauf.** Die Übernahme eines Alt-Bestands (Konten mit Rollen, Verknüpfungen, Stammdaten, Planungsdokument samt Versionen, Kursräume mit Material und Dateien, Klassenbuch, Fehlzeiten, Noten, Nachrichten, Formulare, Einstellungen, Schlüsselring) in den Neubau ist verlustfrei (PRI-002, DAM-102): Es gibt zuerst einen **Trockenlauf** ohne Änderung mit Bericht (Zeilenzahlen je Tabelle, Warnungen, Fehler), danach die Übernahme ganz oder gar nicht. Klartext-Altbestand wird beim Einlesen verschlüsselt (DAT-006); nach der Übernahme gibt es keine Planversion ohne Präfix `SM1`.
  - Abnahme: Mit dem Alt-Stand einer Wegwerf-Instanz: Zeilenzahlen je Quell- und Zieltabelle in einer Abgleichstabelle (0 unerklärte Differenzen); Stichprobe von 50 Datensätzen je Fachbereich inhaltlich gleich; Marker-Suche (QUA-081) nach der Übernahme: 0 Klartext-Treffer; Fehler im Trockenlauf bricht die Übernahme ab, ohne dass die Zielinstanz verändert wurde; [unklar: Übernahme der Passwort-Hashes – Neubau muss das Alt-Format lesen oder Pflicht-Passwortwechsel auslösen; Entscheidung vor Gate G4].

### 2.8 Rücknahme-Test (Ebene E3/E4)

„Rücknahme“ umfasst hier das fachliche Rückgängigmachen, die Atomarität mehrstufiger Aktionen und die Rücknahme von Updates (dort E8, QUA-060/061).

- **QUA-094** · P1 · Status: offen (Ist: Rückgängig für Plan, Jahreswechsel, Klasse, Krankmeldung, Import; kein gemeinsamer Test) — **Rücknahme-Rundlauf je Route.** Jede Route, die im Register `Rücknehmbar` trägt, hat eine Gegenroute oder einen Rückgängig-Weg; der Test führt Aktion und Rücknahme aus.
  - Abnahme: Zeilen-Hash der Fachtabellen vor der Aktion gleich dem Hash nach der Rücknahme (ohne Protokolle, die bestehen bleiben); Rücknahme einer Krankmeldung nach 20 s („Rückgängig“-Leiste) und danach („Zurücknehmen“, solange die Schule die Meldung nicht bearbeitet hat) lässt den Eintrag im Meldeprotokoll bestehen; jede Route mit `unwiderruflich` nennt im Register die Begründung (Löschkonzept) und hat Vorschau oder Bestätigung (QUA-096).

- **QUA-095** · P1 · Status: offen (Ist: Plan-Rückgängig stellt die Vorgängerversion als neue Version her und lässt Konten und Mitteilungen unberührt; Fund „zeigt nicht, welche fremden Änderungen mitgehen“) — **Rücknahme zeigt, was mitgeht.** Vor einer Rücknahme, die das Planungsdokument oder mehrere Objekte betrifft, zeigt der Dialog, welche **fremden** Änderungen seit dem Zielstand mitgehen (Person, Zeit, Art); die Rücknahme ändert nur das Fachdokument, nie Konten oder Mitteilungen; sie wird protokolliert.
  - Abnahme: Zwei Personen ändern den Plan nacheinander; die erste nimmt zurück → Vorschau nennt die Änderung der zweiten; nach Bestätigung entsteht eine **neue** Version, Konten und Nachrichten sind unverändert, ein Audit-Eintrag besteht.

- **QUA-096** · P1 · Status: offen (Ist: Jahrgänge, Löschen mit Datenverlust per Eintippen; Altfund „Aufsicht entfernen ohne Rückfrage“) — **Destruktive Aktionen mit Vorschau oder Bestätigung.** Jede Route mit Kennzeichen „löscht oder überschreibt“ hat entweder einen Trockenlauf (Import, Löschkonzept, Jahreswechsel, Rechte-Vorschau), eine Bestätigung im App-Dialog oder – bei Datenverlust (Jahrgang mit Klassen, Konto-Löschung, Sofort-Löschung) – eine Bestätigung durch Eintippen (OBE-029/031); Konflikte (409) bieten „Trotzdem übernehmen“ erst nach Anzeige der Liste (OBE-032).
  - Abnahme: Seitenlauf (E5): jede destruktive Aktion des Seiten-Registers öffnet den passenden Dialog; Route ohne Kennzeichen, aber mit löschender Wirkung (Gegenprobe) wird gefunden, weil Zeilenzahlen vor und nach dem Aufruf sinken, ohne dass das Register es erklärt.

- **QUA-097** · P1 · Status: offen (Ist: Jahreswechsel mit Vorschau und Rückgängig; Abgänger-Verarbeitung; Fund „Zurücknehmen mit Begleitungen nicht atomar“) — **Atomarität mehrstufiger Aktionen.** Für jede mehrstufige Aktion (Jahreswechsel Ausführen und Rückgängig, Abgänger-Verarbeitung, Klasse anlegen und zurücknehmen mit Begleitungen, Sammel-Import, Massenanlage von Konten, Löschkonzept-Lauf, Auskunft, Plan-Übernahme, Stapel-Zugangsbriefe) läuft ein Test mit **erzwungenem Fehler** im k-ten Schritt für jedes k. Ergebnis: entweder vollständiger Rollback (Zustand wie vorher) oder ausdrücklich fortsetzbar (Wiederaufruf schließt ab, Meldung `…erase_failed` o. ä.); nie ein halber Zustand ohne Hinweis. Das Protokoll entsteht in derselben Transaktion.
  - Abnahme: Je Aktion und je Schritt: Zeilen-Hash gleich dem Ausgangszustand oder Wiederaufruf liefert den Endzustand; Audit-Eintrag nur bei Erfolg bzw. mit Fehlerkennung; Kinderliste der Eltern wird nicht in zwei Aufrufen halb gesendet (Alt-Fund U-90).

### 2.9 Drosselung und Missbrauchsschutz (Ebene E3, Last-Anteile auf der Wegwerf-Instanz)

Werte, Schwellen und Wartezeiten stehen in SIC-053 und SIC-091 bis SIC-096; hier steht, **wie sie über alle Wege geprüft werden**. Schwellen werden für den Test gesenkt, nie wird eine echte Instanz geflutet (SIC-009). Betreiberregel (16.10.): „Ein Schulnetz hinter NAT darf nie komplett ausgesperrt werden; je Konto bleibt die Drosselung.“

- **QUA-098** · P0 · Status: Ist (Ist: 17 Tests zur Anmelde-Härtung; Fehlversuche im Audit und Erkennung von Passwort-Spraying offen) — **Anmelde-Drosselung.** Je Zähler (Paar Benutzername + IP, IP insgesamt, Konto insgesamt) und je Stufe der Wartezeit-Tabelle (SIC-092): Schwelle − 1 → frei, Schwelle → Wartezeit; Antwort 429 `too_many_attempts` mit `Retry-After`, **vor** der Passwortprüfung (auch bei richtigem Passwort und in Schritt 2 der Zwei-Faktor-Anmeldung); gedrosselte Anfragen zählen nicht als Fehlversuch; ein falscher Zwei-Faktor-Code zählt auf alle drei Zähler, Schritt 1 auf keinen; Aufheben durch die Verwaltung mit Audit `login_lock.clear` (Sekretariat → 404 bei Lehrerkonto).
  - Abnahme: Je Tabellenzeile ein Test mit erwarteter Wartezeit (± 1 s); **Schulnetz-Test**: 300 Konten hinter einer IP, 75 davon mit einmaligem Tippfehler → alle 300 melden sich nach erneutem Versuch an, keine 429 für Konten ohne Fehlversuch; 50 Fehlversuche gegen 50 Konten von einer IP → 50 Audit-Einträge und ein Alarm-Eintrag (DAT-032); eine harte Kontosperre ist an keiner Stelle auslösbar.

- **QUA-099** · P0 · Status: Ist (Ist: Eimer je IP und Konto; knotenübergreifend offen) — **Allgemeines Rate-Limit je Drosselklasse.** Für jede im Register vorkommende Drosselklasse wird mit auf 10 gesenkter Schwelle geprüft: die 11. Anfrage binnen einer Minute → 429 mit `Retry-After` und Grund `rate_limited`; ausgenommen bleiben nur die Klasse `frei` (Ereignisstrom, Gesundheit, Metriken, statische Dateien). IP-Eimer und Konto-Eimer sind getrennt: ein zweites Konto derselben IP wird durch den IP-Eimer begrenzt, nicht durch den Konto-Eimer des ersten.
  - Abnahme: Test je Klasse; `/healthz` bleibt erreichbar; im Zweiknoten-Betrieb zählt das Limit knotenübergreifend (SIC-120); Betrieb mit `SM_RATE_LIMIT=0` im Produktivmodus → Start verweigert.

- **QUA-100** · P0 · Status: Ist — **Konto-Codes, Zurücksetzen, Uploads, Chat-Bilder.** Jede Zeile der Limit-Tabelle (SIC-053: Bestätigungscodes 5 je Stunde und Konto, 20 je Stunde und IP; Reset-Anfragen 5 je Stunde und Kennung, 20 je Stunde und IP; Reset-Fehlversuche 30 je Stunde und IP; Administration 10 je Stunde und Zielkonto; höchstens 5 Konten je Adresse) sowie die Größen- und Raten-Grenzen (SIC-075/076: Upload > 25 MB → 413 schon während der Übertragung; Kontingent je Konto; 31. Chat-Upload binnen 10 Minuten abgelehnt) ist geprüft.
  - Abnahme: Je Zeile ein Test „Schwelle + 1 → erwartete Reaktion“; Reset-Anfrage für bekanntes und unbekanntes Konto dauert je mindestens 0,35 s und liefert denselben Text; nach Löschen einer Nachricht ist das Kontingent wieder frei.

- **QUA-101** · P0 · Status: Ist — **Keine Orakel.** Bekannte und unbekannte Konten erhalten gleiche Antwort und gleiche Laufzeit bei Anmeldung, „Passwort vergessen“, Kontakt-Bestätigung und Anbieter-Anmeldung; Fehlermeldungen verraten nicht, ob ein Objekt, ein Konto oder ein Host existiert (SIC-007, SIC-097).
  - Abnahme: 200 Anmeldeversuche mit unbekanntem und 200 mit bekanntem Benutzernamen (falsches Passwort): identischer Statuscode und Text, Median der Laufzeiten höchstens 40 ms Unterschied [Prüfwert]; dasselbe für Reset-Anfragen; Zugriff auf 100 fremde und 100 nicht vorhandene Objekt-IDs: identische Antworten (QUA-074).

- **QUA-102** · P1 · Status: offen (Ist: Eingabe- und Zeitgrenzen einzeln; Obergrenzen uneinheitlich, Altfunde U-71/U-72) — **Eingabe-, Größen- und Zeitgrenzen über alle Routen.** Jedes Eingabemodell hat Längen- und Mengengrenzen, die in Schema und Prüfung gleich sind; Listen sind paginiert; Importe haben Größen-, Zeit- und Entpackgrenzen; Browser-Anfragen brechen nach 30 s ab (5 Minuten für Upload, Sicherung, Import, Generator); Server-Zeitlimits gelten (SIC-096).
  - Abnahme: Aus dem Register: jedes Textfeld mit Maximallänge + 1 → 422; Liste mit 5.000 Einträgen liefert erste Seite und Folgeverweis; Archiv über der Entpackgrenze und Archiv mit Pfad `../x` → abgelehnt ohne Speicher-/Zeitüberschreitung; künstlich verzögerte Route (35 s) endet im Client mit „Der Server antwortet nicht rechtzeitig“; Start mit `SM_THREADPOOL=4` hebt auf 8 an.

### 2.10 Weitere Register-Prüfungen (Ebene E3)

- **QUA-103** · P0 · Status: offen (Ist: einzelne Prüfungen; CSRF-Regel an allen schreibenden Methoden; Kopfzeilen-Test) — **Transport, Kopfzeilen, Zeit und Fehlerhygiene.** Für alle Routen gilt: (a) Sicherheits-Kopfzeilen und Content-Security-Policy, `Cache-Control: no-store` bei API-Antworten und bei Zugangsdaten (SIC-089); (b) Cookies HttpOnly, SameSite, Secure bei HTTPS (SIC-057) und CORS nur für erlaubte Quellen (SIC-090); (c) CSRF-Kopf bei allen schreibenden Methoden mit Sitzung (SIC-060); (d) jeder Zeitstempel einer Antwort in UTC mit `Z`, Datumsfelder `YYYY-MM-DD` (QUA-019); (e) ein 500 liefert nur Fehlernummer, nie Stapelspuren, SQL oder Pfade (SIC-068); (f) Zugriffsprotokoll ohne Abfrageparameter, Token in Kalender-Adressen maskiert (DAT-026).
  - Abnahme: Je Buchstabe ein Test über alle Routen des Registers; POST ohne CSRF-Kopf mit Sitzung → 403 an jeder schreibenden Route (Token-Zugang ausgenommen); künstlicher 500 enthält weder „Traceback“ noch SQL noch Dateipfad; Zugriffsprotokoll nach 100 Aufrufen mit Abfrage enthält 0 Abfrageparameter.

- **QUA-104** · P0 · Status: offen (Ist: `extra=forbid` an einzelnen Stellen; Schutzfunktion gegen Tabellenzellen-Formeln in fünf Exporten nicht genutzt) — **Eingabe- und Ausgabe-Neutralisierung.** (a) Jedes Eingabemodell lehnt unbekannte Felder ab (keine Massenzuweisung von `role`, `adult`, `is_active`; SIC-066); (b) in **jedem** Export und jeder CSV-Ausgabe sind führende Formelzeichen (`=`, `+`, `-`, `@`) neutralisiert (SIC-069); (c) Weiterleitungsziele nach Anmeldung und Abmeldung nur auf interne Pfade (SIC-070); (d) Antworten enthalten keine Geheimnisse: Feldscan nach Hashes, Token, Schlüssel- und Code-Feldnamen (SIC-006); (e) Markdown und Nutzertext werden nie als HTML eingefügt (SIC-067).
  - Abnahme: POST mit zusätzlichem Feld `role` an jede schreibende Route mit Körper → 422 (Registry-Test erzwingt `extra=forbid`); Namens- und Freitextfelder mit `=1+1`, `+SUMME(A1)`, `-2`, `@x` erscheinen in jedem Export mit neutralisiertem Anfang; Weiterleitung auf eine Adresse außerhalb der Instanz → abgelehnt; Feldscan aller Antworten: 0 Treffer; Skript-Text in einem Nachrichtenfeld wird als Text dargestellt (Browserlauf).

- **QUA-105** · P0 · Status: offen (Ist: zentrale Zielprüfung, Dateizugriffsprüfung, Ereignisse ohne Inhalt; Lücke: Ereignisstrom bei Pflicht-Weichen) — **Dateien, ausgehende Verbindungen, Live-Ereignisse.** (a) Dateien: Auslieferung nur über die Schnittstelle, Zugriffsprüfung je Verweistyp, fremde Datei → 404, `nosniff` und sichere Anzeige (SVG nie inline), Pfade nur über validierte Kennung (SIC-079/080/081); (b) jede ausgehende Verbindung läuft durch die eine Zielprüfung: Ziele `127.0.0.1`, `10.0.0.5`, `169.254.169.254`, `100.64.0.1`, `::1`, `::ffff:127.0.0.1`, ein erst öffentlich, dann privat auflösender Host und eine Weiterleitung auf ein internes Ziel werden abgelehnt (SIC-097); (c) der Ereignisstrom nennt nur Bereichsnamen und Datumsbezug, nie Inhalte, und wird bei Pflicht-Passwortwechsel und Pflicht-Zwei-Faktor nicht geliefert (SIC-029).
  - Abnahme: Je Verweistyp der Datei-Registry ein Fremdabruf-Test (404); statische Prüfung: kein direkter Aufruf eines HTTP-Clients außerhalb des Dienstes mit der Zielprüfung (0 Treffer); die genannten Testziele werden je Dienst (Webhook, Postfach-Server, Anbieter-Anmeldung, Ferien-Dienst, SMS) abgelehnt, die Fehlermeldung enthält keinen Antworttext; R31 und R32 erhalten vom Ereignisstrom 403; Ereignis-Nutzlast enthält keinen Marker (QUA-081).

### 2.11 Berichtswesen der Querschnittstests

- **QUA-106** · P1 · Status: offen — **Ausnahmelisten sind geschlossen, datiert und werden gezählt.** Jede Ausnahme eines Querschnittstests steht in einer Datei mit Route/Spalte, Grund, Beschluss und Datum: 403 statt 404 (QUA-077), Audit-Ausnahmen A1 bis A3 (QUA-078), bewusst unverschlüsselte Daten (DAT-018), Freigaben für Demo, Ansichtskonto, API-Schreibzugang, Export (QUA-072), Lesemarkierungen (Register), Rücknehmbarkeit `unwiderruflich` (QUA-094).
  - Abnahme: Der Querschnittsbericht nennt je Liste Anzahl und Veränderung seit dem letzten Gate; eine Liste wächst nur mit Beschluss des Betreibers oder der Abnahme (Eintrag im Entscheidungsprotokoll); veraltete Einträge (Route entfernt) lassen den Test scheitern.

- **QUA-107** · P2 · Status: offen — **Laufzeitbudget und Berichtsform.** Der Gesamtlauf der Querschnittstests E3 (rund 33 Personen × alle Routen) dauert höchstens 10 Minuten bei paralleler Ausführung auf 4 Kernen [Festlegung]; E4-Anteile (Marker-Suche, Migrationsarchiv) höchstens 15 Minuten [Festlegung]. Der Bericht listet je Test: geprüfte Routen bzw. Seiten, geprüfte Personen, Treffer, Abweichungen nach Schwere, Ausnahmen, Dauer, Datum, Version.
  - Abnahme: Bericht liegt je Gate vor; überschreitet ein Teil das Budget, wird er in Teile je Fachbereich zerlegt, nicht gekürzt; die Summe der geprüften Routen im Bericht gleicht der Registergröße (QUA-066).

---

## 3. Definition of Done

Eine Sache ist **fertig**, wenn ihre Nachweise vorliegen – nicht, wenn der Code geschrieben ist (QUA-001). Betreiber: „ich habe viel fehler gefunden die ich schon gemeldet hatte die du noch nciht umgesetzt hast“; seitdem gilt: Kein Punkt ist erledigt, der nicht im Code **und** in einem Test belegt ist. Die Definition gilt auf drei Ebenen: je Anforderung (3.1), je Fehlerbehebung bzw. Änderung (3.2), je Auslieferung (3.3).

**Statuswerte in der Abdeckungs-Matrix:** `erfüllt` (Abnahmetest grün, mit Test-Kennung, Lauf-Datum und Version), `handgeprüft` (Protokoll mit Datum, Prüfer, Beleg; nur für Dinge, die sich nicht automatisieren lassen, z. B. Screenreader), `teilweise` (Test grün für einen Teil; Rest benannt), `fehlt` (Funktion nicht vorhanden oder Test rot), `nicht belegt` (Behauptung ohne Test), `entfällt` (Beschluss des Betreibers im Entscheidungsprotokoll mit Datum).

### 3.1 Definition of Done je Anforderung

| Nr | Kriterium | Beleg |
|---|---|---|
| D1 | Die Abnahme-Zeile ist als **ausgeführter**, automatisierter Test umgesetzt (Positiv-, Negativ-, Rechte- und Fehlerfall) | Test-Kennung und Lauf in der Matrix (QUA-001, QUA-008) |
| D2 | Rechte und Datenumfang werden im Dienst (nicht nur in der Oberfläche) geprüft; bei jeder neuen Sichtbarkeitsregel gibt es einen Rechte-Matrix-Test; die Route steht im Register mit allen Spalten | QUA-066, QUA-070, SIC-002 |
| D3 | Fremde Objekte → 404 (Lese- und Schreibwege, Listen, Suche, Exporte) | QUA-074 bis QUA-076 grün für die neuen Routen |
| D4 | Jede schreibende Aktion steht im Audit ohne Inhalte; Ausnahmen nur A1 bis A3 | QUA-078, QUA-079 |
| D5 | Personenbezogene Freitexte sind verschlüsselt und im Register eingetragen; Datenart mit Frist, Löschfunktion, Auskunft; Codes und Token nur als Hash/HMAC | QUA-081, QUA-083 |
| D6 | Schemaänderung: nur erweiternd, Migrationstest, Archivstand ergänzt | QUA-090 bis QUA-092 |
| D7 | Oberfläche: Seite im Seiten-Register; Rundgang bei 390 px und 1440 px (und 360 px), hell und dunkel, nur mit Tastatur bedienbar; Sie-Form; keine Erklärabsätze (Hilfe-Symbol); kein Browser-Dialog; ein Raster; Fehler am Feld | QUA-046 bis QUA-049, QUA-084 bis QUA-088 |
| D8 | Konfiguration: neue Einstellung steht in der Variablentabelle, hat Standardwert und Startprüfung; Betreiberpaket und Handbuch sind angepasst | BET-015, QUA-029 |
| D9 | Drosselklasse und Eingabegrenzen sind festgelegt und getestet | QUA-099, QUA-102 |
| D10 | Nebenläufigkeit und Atomarität sind geprüft, wo zutreffend (Buchung, Zähler, Verbrauch von Codes, mehrstufige Aktionen) | QUA-043, QUA-097 |
| D11 | Datumsabhängiges Verhalten ist mit den zehn festen Uhren grün | QUA-016 |
| D12 | Der Status in der Abdeckungs-Matrix und im Fund-Register ist aktualisiert; die zugehörige Rückmeldung ist mit Test geschlossen | QUA-010, QUA-011 |
| D13 | Nach einem Paket folgt eine Prüfrunde: Fehler suchen, nachstellen, beheben, Regressionstest | QUA-009, QUA-011 |

- **QUA-108** · P0 · Status: Ist (Ist: sieben Punkte der Definition im Backlog – Tests je Abnahmepunkt, Rechte und Datenumfang, Audit/Verschlüsselung/Hash, Browser-Rundgang, Dokumentation, Notiz, Prüfrunde; Anwendung ungleichmäßig) — **Anforderung gilt nur als erfüllt, wenn D1 bis D13 zutreffend belegt sind.** Nicht zutreffende Kriterien werden mit Grund als „entfällt“ vermerkt (z. B. D6 ohne Schemaänderung).
  - Abnahme: Das Prüfskript über die Abdeckungs-Matrix (QUA-001) verlangt je Anforderung mit Status `erfüllt` für jedes zutreffende Kriterium einen Verweis; fehlt einer, setzt es den Status auf `teilweise`; Stichprobe von 10 Anforderungen mit Status `erfüllt`: alle Verweise führen zu vorhandenen, grünen Läufen.

### 3.2 Definition of Done je Fehlerbehebung bzw. Änderung

- **QUA-109** · P1 · Status: Ist (Ist: Regressionstest je Fix, nur Tests der eigenen Bereiche, Gesamtlauf nur durch die Koordination) — **Fertig ist eine Behebung, wenn:** (1) der Fund vor der Behebung nachgeprüft ist (QUA-011); (2) ein Test den Fund nachstellt und vor der Behebung **rot** war; (3) nach der Behebung der Test, die Tests des betroffenen Bereichs und der Basis-Querschnitt grün sind (QUA-005); (4) ein bestehender Test nur geändert wurde, wenn sich das Verhalten **bewusst** ändert, und die Änderung mit Begründung und Datum im Fund-Register steht (Lehre: Verhaltensänderung des Lehrer-Scopes brach alte Prüfungen; Entscheidung gilt als Vorgabe); (5) kein bestehender Test gelöscht oder übersprungen wurde, um grün zu werden; (6) die Bereichskarte (QUA-006) und die Dokumentation des Bereichs aktualisiert sind.
  - Abnahme: Prüfung der Änderungsliste: je Behebung Test-Kennung, Nachweis „rot vor, grün nach“, Liste ausgeführter Tests; Prüfskript meldet gelöschte oder neu übersprungene Tests (Skip-Zähler, QUA-031) als Verstoß; Stichprobe 5 Behebungen.

### 3.3 Definition of Done je Auslieferung (Release)

| Nr | Kriterium | Grenzwert / Beleg |
|---|---|---|
| L1 | **Gesamtlauf E1 bis E4** in der Linux-Zielumgebung | 0 fehlgeschlagen, 0 Skips ohne Grund; dreimal zufällige Reihenfolge und einmal parallel mit identischem Ergebnis (QUA-023, QUA-029, QUA-031); Lauf endet ohne Hänger |
| L2 | **Querschnittstests** (Abschnitt 2) | alle grün; Gegenproben scheitern wie erwartet (QUA-069); Ausnahmelisten geprüft (QUA-106) |
| L3 | **Abdeckungs-Matrix** (Abschnitt 4) | alle `P0`: 100 % `erfüllt`; alle Anforderungen mit `Status: Ist`: 100 % (PRI-002); `P1`: mindestens 95 % `erfüllt`, der Rest mit Beschluss [Festlegung]; P2/P3 nach Roadmap |
| L4 | **Fund-Register** | 0 offene Funde kritisch/hoch; mittlere nur mit Beschluss; Altfund-Regressionssatz grün (QUA-058) |
| L5 | **Browser-Rundgang E5** | Berichte für alle Rollen (QUA-046); Barrierefreiheit 0 schwere Verstöße (QUA-048); vor Einsatz bei einer Schule: Screenreader-Protokoll (QUA-050) |
| L6 | **Lasttest E6** | Szenarien S1 bis S4 bestanden (QUA-040) |
| L7 | **Sicherheitsabnahme E7** | Prüfliste ohne „fehlt“ (QUA-054); Build-Prüfungen grün (QUA-055); Penetrationstest mit Wiederholung (QUA-057); Prüfbericht als Anhang (SIC-011) |
| L8 | **Betriebsabnahme E8** | Update und Rollback mit dieser Version (QUA-060); Wiederherstellungs-Rundlauf (QUA-061); Probelauf an Kopie (QUA-062); Alarme (QUA-063) |
| L9 | **Image und Auslieferung** | Inhalt geprüft (QUA-055); Betreiberpaket enthalten; Lizenzscan ohne GPL/AGPL (PRI-003); Release-Manifest mit Kennzeichen „abwärtskompatibel“ (BET-035) |
| L10 | **Datenübernahme** (nur wenn Alt-Bestand übernommen wird) | Trockenlauf und Abgleichstabelle ohne unerklärte Differenz (QUA-093) |
| L11 | **Dokumentation entspricht dem Verhalten** | Datenschutz-Texte, Verzeichnis, Löschfristen und Zusagen per Test gegen Konfiguration und Verhalten geprüft (SIC-008); Handbuch und Betreiberpaket aktuell; Werte aus der Konfiguration (OBE-127) |
| L12 | **Marktreife-Checkliste** (PRI-001) | rund 50 Punkte in sechs Gruppen; kein offener P0-Punkt |
| L13 | **Name und Marke** | Produktname nur an einer Stelle (QUA-014); Namensprüfstand vor jeder Außenwirkung (PRI-028) |
| L14 | **Testtag-Szenario** | vor der ersten Schule vom Betreiber durchgeklickt und mit Datum protokolliert (QUA-036) |
| L15 | **Release-Notiz** | Version, Datum, Änderungen, bekannte Abweichungen mit Ursache, Lösung und Fund-Kennung (QUA-029), Rückfallweg, Prüfberichte als Anhang |

- **QUA-110** · P0 · Status: offen (Ist: Gesamtlauf auf dem Heimserver unter Linux mit 1.736 bestandenen Backend-Tests und 3 Fehlschlägen durch veraltete Attrappen; zweiter vollständiger Lauf fehlte; Penetrationstest, Lastlauf, vollständige Wiederherstellung standen aus) — **Eine Version wird nur ausgeliefert, wenn L1 bis L15 erfüllt sind.** Kriterien, die für die Auslieferungsart nicht zutreffen (z. B. L10 ohne Altbestand), sind mit Grund vermerkt.
  - Abnahme: Das Release-Werkzeug verweigert die Freigabe ohne Abnahmeprotokoll (QUA-112) mit Verweisen auf L1 bis L15; Probe: Freigabe mit fehlendem Lastbericht wird verweigert.

- **QUA-111** · P0 · Status: offen — **Offener P0-Punkt sperrt die Auslieferung.** Betreiberziel: kein Amateurprogramm, sondern ein „voll ausgewachsener Schulmanager“. Ist ein P0-Punkt offen (Anforderung, Fund der Stufen kritisch/hoch, Marktreife-Punkt), wird die Version nicht an eine Schule ausgeliefert (PRI-001). Eine begründete Ausnahme setzt einen schriftlichen Beschluss des Betreibers mit Datum und Frist voraus und wird im Release-Bericht genannt.
  - Abnahme: Probe: Matrix mit einem P0-Eintrag `fehlt` → Release-Werkzeug verweigert; Matrix mit demselben Eintrag und Beschluss → Freigabe mit Vermerk im Bericht; Stichprobe: kein ausgelieferter Stand ohne Abnahmeprotokoll.

- **QUA-112** · P1 · Status: offen — **Abnahmeprotokoll.** Je Gate und je Auslieferung entsteht ein Protokoll: Version (Commit/Image-Kennung), Datum und Zeit (UTC), Umgebung (Plattform, Datenbank, Uhr), Prüfer (Rolle, nicht Person) und Bau-Team getrennt, Liste der ausgeführten Läufe mit Ergebnis (E1 bis E8, Querschnitt), Matrix-Zusammenfassung (Zahlen nach Priorität und Kürzel), Fund-Register-Zusammenfassung (nach Schwere und Status), Ausnahmen und Beschlüsse, bekannte Abweichungen, Entscheidung (freigegeben / nicht freigegeben / mit Auflagen) und Auflagen.
  - Abnahme: Protokollvorlage liegt vor; ein Protokoll ohne Zahlenteil oder ohne Entscheidungsvermerk gilt als nicht ausgestellt; Stichprobe: Zahlen des Protokolls stimmen mit der Matrix überein.

- **QUA-113** · P1 · Status: offen — **Unabhängigkeit der Abnahme.** Abnahmetests werden **aus der Spezifikation** (Abnahme-Zeilen, Soll-Matrix, Rollenfeld) geschrieben, nicht aus dem Code des Neubaus; sie prüfen über Schnittstelle und Oberfläche (Black-Box). Das Bau-Team ändert Abnahmetests nicht; Änderungen laufen über die Abnahme mit Begründung (Verhaltensänderung bewusst, Spezifikation geändert, Testfehler). Ein Teil der Abnahmetests (mindestens 20 %, Varianten und zusätzliche Fälle zu den veröffentlichten Abnahme-Zeilen) wird dem Bau-Team nicht vorab gegeben [Festlegung].
  - Abnahme: Änderungsverlauf der Abnahmetests zeigt keine Änderung durch das Bau-Team ohne Freigabe; Bericht nennt Anzahl verdeckter Testfälle und deren Ergebnis; Stichprobe 5 Tests: Ursprung ist eine Abnahme-Zeile der Spezifikation.

---

## 4. Vergleichs-Experiment: Neubau gegen heutigen Stand

Betreiber (18.10.): „wenn du das ganze Programm komplett neu schreibst mit 0 % des alten Codes, also einem ganz neuen Fenster, ob es dann besser wird“. Dieser Abschnitt legt fest, **woran** „besser“ gemessen wird, **wie** gemessen wird und **wie fair** ausgewertet wird. Alle Festlegungen werden **vor Messbeginn eingefroren** (Datum im Protokoll) und danach nur mit Begründung geändert.

### 4.1 Gegenstand, Hypothesen und Referenzstände

- **QUA-114** · P1 · Status: offen — **Gegenstand und Hypothesen.** Verglichen werden zwei Arme: **Alt** (heutiger Stand, eingefroren) und **Neubau** (Auslieferung nach diesem Paket). Hypothesen (vorab festgelegt):
  - H1 *Parität*: Der Neubau besteht 100 % der Abnahmen von Anforderungen mit `Status: Ist` (PRI-002: „Auf jeden Fall sollen keine Features gestrichen werden, es sollen nur optimiert werden.“).
  - H2 *Fortschritt*: Der Neubau erfüllt mehr Anforderungen mit `Status: offen` als der Alt.
  - H3 *Qualität*: Bei gleicher Prüfung hat der Neubau weniger gewichtete Funde je 100 Anforderungen.
  - H4 *Sicherheit*: Der Neubau hat in den Querschnittstests (Abschnitt 2) weniger Abweichungen und keinen offenen Fund der Stufen kritisch/hoch.
  - H5 *Leistung*: Der Neubau ist bei den Lastszenarien nicht langsamer (Toleranz 10 %) und erreicht die Zielwerte (QUA-040).
  - H6 *Wartbarkeit*: Der Neubau erreicht dieselbe Abdeckung mit höchstens gleicher Codemenge (Informationsgröße).
  - Abnahme: Das Experiment-Protokoll nennt die Hypothesen wörtlich, das Einfrierdatum und die Auswertungsregel (QUA-129); später hinzugefügte Hypothesen sind als „nachträglich“ gekennzeichnet und fließen nicht in das Gesamturteil ein.

- **QUA-115** · P1 · Status: offen — **Referenzstände einfrieren.** Der Alt-Stand wird als Image-Kennung und Datenbank-Seed festgehalten (letzter Quellenstand: 17.10.2026, abends); [unklar: Image-Kennung des Alt-Stands beim Start des Experiments nennen]. Beide Arme laufen auf identischer Plattform (Linux-Zielumgebung, gleiche Kerne, gleicher Arbeitsspeicher, gleiche Datenbank-Art, feste Uhr), mit denselben Seeds der vier Größenstufen (QUA-034) und demselben Rollenfeld, soweit der Alt es abbilden kann. Der Alt wird während der Messung **nicht verbessert**; Korrekturen am Alt nach dem Einfrieren zählen nicht.
  - Abnahme: Protokoll nennt Kennung, Einfrierdatum, Plattform und Seed-Hash je Arm; die Plattformangaben beider Arme sind identisch; ein Lauf mit abweichender Plattform wird nicht gewertet.

### 4.2 Abdeckungs-Matrix

Die Matrix ist die zentrale Tabelle des Experiments und zugleich der Nachweis nach QUA-001. **Eine Zeile je Anforderungs-Kennung** aller Fachdateien (STP, VER, KLB, NOT, KUR, NAC, FOR, STA, LEH, SCH, REC, ANM, DAT, BEN, INT, BET, OBE, SIC, REH, QUA, PRI sowie die Roadmap-Kennungen der Nummernkreise 901 bis 999) und eine Zeile je Querschnittstest-Abweichung (Anhang der Matrix).

**Vorlage (CSV, Semikolon, UTF-8); die drei Zeilen sind erfundene Beispielwerte zur Form, keine Messergebnisse:**

```
kennung;kuerzel;prio;status_soll;titel_kurz;alt_ergebnis;alt_test;alt_lauf;alt_hinweis;neu_ergebnis;neu_test;neu_lauf;neu_hinweis;abweichung_schwere;beschluss;bemerkung
SIC-013;SIC;P0;Ist;404-Regel fremde Daten;bestanden;QT-404-allRoutes;2026-11-02;42 Faelle;nicht bestanden;QT-404-allRoutes;2026-11-20;3 Routen mit 403;hoch;;
STP-001;STP;P1;Ist;(Kurztitel);bestanden;T-STP-001;2026-11-02;;bestanden;T-STP-001;2026-11-20;;;;
QUA-050;QUA;P2;offen;Screenreader-Pruefung;nicht pruefbar;;;Handpruefung offen;handgeprueft;HP-2026-11-30-01;2026-11-30;NVDA/VoiceOver;;;
```

Spalten: `kennung` (z. B. `SIC-013`), `kuerzel`, `prio` (P0 bis P3), `status_soll` (`Ist` / `offen` laut Fachdatei), `titel_kurz`, je Arm `*_ergebnis` (Werte unten), `*_test` (Test-Kennung bzw. Protokoll-Kennung), `*_lauf` (Datum UTC), `*_hinweis`, `abweichung_schwere` (kritisch / hoch / mittel / niedrig / leer), `beschluss` (Verweis ins Entscheidungsprotokoll), `bemerkung`.

**Ergebniswerte je Arm:**

| Wert | Bedeutung | Zählt als |
|---|---|---|
| `bestanden` | Abnahmetest lief und war grün | erfüllt |
| `handgeprüft` | Protokoll mit Datum, Prüfer, Beleg (nur für nicht automatisierbare Dinge) | erfüllt, getrennt ausgewiesen |
| `nicht bestanden` | Test lief und scheiterte, Funktion vorhanden | nicht erfüllt |
| `fehlt` | Funktion nachweislich nicht vorhanden (Prüfer bestätigt) | nicht erfüllt |
| `nicht prüfbar` | Abruf bzw. Oberfläche existiert im System nicht oder ist nicht ansprechbar (Adapter-Grenze) | nicht erfüllt, getrennt ausgewiesen |
| `entfällt` | Beschluss des Betreibers mit Datum | aus dem Nenner genommen |

- **QUA-116** · P1 · Status: offen — **Aufbau und Pflege der Matrix.** Die Matrix wird aus den Fachdateien erzeugt (alle Kennungen, Priorität, Status, erste Abnahme-Zeile als Kurztitel) und von den Testläufen befüllt; sie ist maschinenlesbar, versioniert und je Gate abgelegt. Jede Kennung kommt genau einmal vor; Kennungen ohne Abnahmetest haben `nicht prüfbar` oder `fehlt`, nie eine leere Zelle. Die Matrix enthält die Summenzeile je Priorität und Kürzel.
  - Abnahme: Erzeugungsbefehl listet die Anzahl der Kennungen je Fachdatei und vergleicht mit der Zählung in den Dateien (0 Differenz); doppelte Kennung → Fehler; Zelle leer → Fehler; Stichprobe 20 Zeilen: Test-Kennung verweist auf einen vorhandenen Test mit der passenden Abnahme-Zeile.

- **QUA-117** · P1 · Status: offen — **Berechnungsvorschriften.** Mit b = Anzahl `bestanden`, g = Anzahl `handgeprüft`, e = Anzahl `entfällt`, N = Anzahl Kennungen: **Abdeckung A = (b + g) / (N − e)**, ausgewiesen gesamt, je Priorität (P0 bis P3), je Kürzel, getrennt nach `Status: Ist` (**Parität**, A_Ist) und `Status: offen` (**Fortschritt**, A_offen); Differenz Δ = A_Neubau − A_Alt in Prozentpunkten. Gewichtete Fehlerdichte **D = (10·F_krit + 5·F_hoch + 2·F_mittel + 1·F_niedrig) / (N / 100)** mit F = Anzahl bestätigter Funde der jeweiligen Schwere [Festlegung der Gewichte]. Nur Funde mit Status „bestätigt“ zählen (QUA-011); „falsch“ und „unklar“ werden getrennt ausgewiesen.
  - Abnahme: Rechenskript liefert die Kennzahlen aus der Matrix und dem Fund-Register; Beispielrechnung mit 10 Zeilen und 3 Funden (1 hoch, 1 mittel, 1 niedrig) liefert D = 8 / (10/100) = 80 [Rechenprobe]; das Skript stimmt mit der Handrechnung überein.

### 4.3 Messgrößen

Referenzwerte des Alt-Stands (Orientierung aus Arbeitsdokumenten 10. bis 17.10.2026; **nicht vergleichbar** mit späteren Läufen, weil Zählweise und Umfang wechselten; im Experiment werden beide Arme neu gemessen):

| Größe | Alt (Orientierung) | Quelle/Stand |
|---|---|---|
| Endpunkte; Tabellen | 716 in 24 Bereichen; rund 120 | Register; Datenmodell 16.10. |
| Codemenge | Backend rund 48.000 Zeilen in 164 Dateien, Oberfläche rund 35.000 Zeilen in 172 Dateien (rund 84.000 Zeilen, 336 Dateien); größte Datei 3.355 Zeilen | 13.10. bzw. Durchsicht 17.10. |
| Erstladung Oberfläche | rund 400 KB (gzip), größtes Bündel 364 KB | Messung 12.10. |
| Tests (Linux-Lauf Heimserver) | Backend 1.736 bestanden, 3 fehlgeschlagen (veraltete Attrappen); Oberfläche 704 | 17.10. |
| Gesamtlauf | 15 bis 20 Minuten CPU-Last auf dem PC; ein Lauf 18 Minuten ohne Fortschritt abgebrochen | 16./17.10. |
| Sicherheits-Checkliste | 69 Punkte: 48 erfüllt, 13 teilweise, 1 fehlt, 7 nicht zutreffend | 17.10. |
| Code-Durchsicht | 169 Funde, davon 13 hoch | 17.10. |
| Bereichsbewertung (Prüf-Agenten) | Schnitt 72,2 von 100 (Funktion 81,9; Qualität 73,2; Bedienung 70,3; Sicherheit 72,0; Tests 63,7); 76 Funde: 42 bestätigt, 11 falsch, 23 unklar | 16.10. |
| Last | 150 gleichzeitige Nutzer lokal ohne Fehler; 95. Perzentil 1,2 s bei 60 Nutzern; Nachrichtenversand 3 bis 5 s | früher |
| Wiederherstellung | 5.464 Konten lesbar; Dateiprüfung nur 5 Dateien | 17.10. |
| Erklärtext-Restfälle | rund 65 | 16.10. |

- **QUA-118** · P1 · Status: offen — **M1 Abdeckung.** Definition und Vorschrift: QUA-117 (A gesamt, je Priorität, je Kürzel; A_Ist als Parität, A_offen als Fortschritt). Ausgewiesen werden außerdem die Zahlen `nicht prüfbar` und `fehlt` getrennt, damit eine fehlende Testbarkeit des Alt nicht als „fehlende Funktion“ gewertet wird.
  - Abnahme: Tabelle M1 mit 4 Zeilen je Arm (gesamt, P0, Ist-Parität, offen-Fortschritt) und Spalten b, g, Nenner, A; Summe der Kürzel-Zeilen gleich der Gesamtzeile.

- **QUA-119** · P1 · Status: offen — **M2 Bestandene Abnahmen.** Anzahl und Quote bestandener **Abnahmeprüfungen**, getrennt nach Ebene: Anforderungsebene (Abnahme-Zeilen), Querschnittsebene (geprüfte Route-Person-Paare und Routen je Querschnittstest aus Abschnitt 2), Browser-Rundgänge (Seiten ohne Fehler / Seiten), Last (bestandene Szenarien), Sicherheit (bestandene Prüflistenpunkte), Betrieb (bestandene Szenarien). Die Zahl der Testfunktionen ist **keine** Vergleichsgröße (Zählweise wechselt); nur Abnahme-Zeilen und Querschnittspaare zählen.
  - Abnahme: Tabelle M2 je Ebene mit Anzahl geprüft, bestanden, Quote, für beide Arme; die Spalte „Testfunktionen“ ist als Information gekennzeichnet und fließt nicht in das Urteil ein.

- **QUA-120** · P1 · Status: offen — **M3 Fehlerdichte.** Beide Arme erhalten dieselbe Prüfung: (a) alle Querschnittstests über den Adapter (QUA-032), (b) eine Fachprüfrunde je Fachbereich durch eine Prüfperson bzw. einen Prüf-Agenten mit demselben Auftragstext und demselben Zeitbudget (60 Minuten je Bereich [Festlegung]), nur über Schnittstelle und Oberfläche, ohne Quellcode (Black-Box), (c) Rundgang je Rolle. Funde werden vor der Zählung nachgeprüft (QUA-011); gezählt werden nur **bestätigte**, **zum Einfrierdatum offene** Funde. Auswertung: D nach QUA-117, zusätzlich Funde je 1.000 Zeilen Code (Informationsgröße) und Falsch-Quote (falsche Funde / alle gemeldeten) je Arm (Alt-Erfahrung: 11 von 76 falsch, 23 unklar).
  - Abnahme: Fund-Register enthält je Fund den Arm, den Entdeckungsweg und das Nachprüfungsergebnis; Tabelle M3 zeigt Funde nach Schwere je Arm, D, Falsch-Quote; beide Arme hatten gleichen Auftragstext und gleiches Zeitbudget (Protokoll).

- **QUA-121** · P0 · Status: offen — **M4 Sicherheits-Funde.** Ausgewiesen werden: (a) Funde der Sicherheitsabnahme E7 nach Schwere und Maßstab (QUA-054), (b) Querschnitts-Quoten: 404-Quote (geprüfte ID-Routen mit 404 / alle ID-Routen), Audit-Quote (Schreibrouten mit genau einem Eintrag / alle), Treffer der Marker-Suche (Klartext-Fundstellen), Default-Deny-Verstöße, Routen ohne Registereintrag, Abweichungen der Rechte-Matrix (mehr Zugriff als Soll) und der Texte (Du-Formen, native Dialoge), (c) Ergebnis des Penetrationstests mit demselben Werkzeug, derselben Laufzeit und derselben Konfiguration auf Wegwerf-Instanzen beider Arme (SIC-009). Alt-Referenz: 404-Prüfung 42 Fälle, Zuschauer-Rundgang 274 Adressen, Checkliste 48/13/1/7.
  - Abnahme: Tabelle M4 mit allen genannten Quoten für beide Arme; „mehr Zugriff als Soll“ und Klartext-Treffer sind einzeln ausgewiesen (nicht in Durchschnitten versteckt); der Penetrationstest beider Arme läuft nur auf Wegwerf-Instanzen (SIC-009).

- **QUA-122** · P1 · Status: offen — **M5 Antwortzeiten.** Gemessen werden: Szenarien S1 bis S4 und S7 (QUA-040) mit 50./95./99. Perzentil und Fehlerquote; 20 Kernabrufe (Startseite, Plan Klasse, Plan Lehrkraft, Vertretungsplan, Krankmeldung anlegen, Nachricht senden, Notenbuch, Kursraum, Suche u. a.) einzeln ohne Last (kalt und warm); Erstladung der Oberfläche (übertragene Bytes, Zeit bis zur Bedienbarkeit auf der Referenzplattform). Abrufe, die der Alt nicht kennt, erhalten `nicht messbar`. Die Messung läuft nicht in einem im Hintergrund laufenden Browser-Fenster.
  - Abnahme: Tabelle M5 mit Messwerten beider Arme je Szenario/Abruf, drei Läufe (Median, schlechtester Lauf); Differenz in Prozent; Plattform identisch (QUA-115).

- **QUA-123** · P2 · Status: offen — **M6 Codegröße (Informationsgröße).** Gemessen mit demselben Zählwerkzeug und denselben Regeln (ohne Leerzeilen und Kommentare): Zeilen und Dateien getrennt für Backend, Oberfläche und Tests; Anzahl direkter Abhängigkeiten; Tabellen; Endpunkte; Konfigurationsvariablen; größte Datei und Anzahl Dateien über 1.000 Zeilen; Erstladung (KB gzip); Image-Größe. Normierung: **Zeilen je erfüllter Anforderung** (Zeilen / (b + g)).
  - Abnahme: Tabelle M6 für beide Arme mit Zählwerkzeug und Version; die Normierung ist gerechnet; die Größe allein führt nie zu „besser“ oder „schlechter“ (nur Information, H6).

- **QUA-124** · P1 · Status: offen — **M7 Testlaufzeit und Stabilität.** Gemessen in der Linux-Zielumgebung (4 Kerne [Festlegung]): Entwicklungslauf eines Bereichs, Gesamtlauf E1 bis E4, Querschnittslauf; Anzahl übersprungener Tests mit Grund; **Flackerquote** (Anteil Tests mit abweichendem Ergebnis in 5 Läufen mit gleicher und mit anderer Reihenfolge); **Hänger** (Läufe, die länger als 5 Minuten ohne Fortschritt blieben). Alt-Referenz: 15 bis 20 Minuten Gesamtlauf; ein Hänger von 18 Minuten.
  - Abnahme: Tabelle M7 mit Wanduhrzeiten (Median von 3 Läufen), Flackerquote (Soll 0), Hänger (Soll 0); Gesamtlauf E1 bis E4 des Neubaus höchstens 20 Minuten [Festlegung]; ein Test, der in 5 Läufen unterschiedlich ausgeht, wird als Fund „flackernder Test“ geführt.

- **QUA-125** · P1 · Status: offen — **M8 Oberfläche, Barrierefreiheit, Texte.** Gemessen: Rundgang-Fehler (Konsole, unerwartete 4xx/5xx) je Seite; Seiten mit waagerechtem Seiten-Bildlauf bei 360 und 390 px; Verstöße der Barrierefreiheits-Engine nach Schwere; Kontrastverstöße; Seiten ohne Hauptüberschrift; Bedienelemente nur mit Maus; Erklärtext-Blöcke (OBE-003; Alt rund 65); Du-Formen; native Dialoge; Seiten ohne Weg im Menü; Elemente mit Farbe als einziger Statusanzeige.
  - Abnahme: Tabelle M8 für beide Arme (Anzahl je Zeile, Seiten geprüft, Quote); Befunde mit Bildbeleg; Soll für den Neubau: 0 in jeder Zeile außer „mittel“-Verstößen mit Fund.

- **QUA-126** · P1 · Status: offen — **M9 Betrieb.** Gemessen: Zeit bis zur eingerichteten Beispielschule durch eine Person ohne Entwicklerwissen (QUA-064; Soll höchstens 60 Minuten), Unterbrechung beim Update (Alt: 10 bis 30 s) und Rollback-Dauer (QUA-060), Wiederherstellungsdauer und Vollständigkeit (QUA-061), Startzeit, Arbeitsspeicher im Leerlauf und unter Last, Anzahl bestandener Start-Pflichtprüfungen (SIC-101), Anzahl Konfigurationsvariablen mit Standardwert, Dauer von Probelauf und Migration auf der Lastschule.
  - Abnahme: Tabelle M9 für beide Arme; Werte, die der Alt nicht liefern kann (z. B. vollständige Dateiprüfung), sind `nicht messbar` und gekennzeichnet.

- **QUA-127** · P3 · Status: offen — **M10 Aufwand (reine Information).** Erfasst werden Bauzeit (Wanduhr), Zahl der Agentenläufe und Unterbrechungen durch Nutzungsgrenzen, Verbrauch (Rechenaufwand/Kosten laut Konto des Betreibers), Zahl der Nachbesserungsschleifen je Gate. Der Betreiber hat Kosten ausdrücklich beschränkt („fabel ist viel zu teuer“, Unteragenten nur Sonnet oder Haiku); die Werte dienen der Planung, **nicht** dem Urteil.
  - Abnahme: Tabelle M10 liegt dem Bericht bei und ist als „nicht Teil des Urteils“ gekennzeichnet.

### 4.4 Faire Auswertung

- **QUA-128** · P0 · Status: offen — **Fairness-Regeln.** Das Experiment hält ein:
  - F1 **Dieselben Tests für beide Arme** über den Adapter (QUA-032); der Adapter bildet Aktion und Erwartung auf Pfad und Format ab und enthält keine Sonderlogik für einen Arm.
  - F2 **Tests aus der Spezifikation**, nicht aus dem Code eines Arms (QUA-113); Abnahme-Zeilen sind neutral formuliert (Zustand/Eingabe → Ergebnis).
  - F3 **Gleiche Bedingungen**: Plattform, Daten (Seeds), Uhr, Rollenfeld, Anzahl Läufe (3, Median), Prüfbudget (QUA-115, QUA-120).
  - F4 **Eingefrorener Alt**: keine Korrekturen während der Messung; Funde zählen nur, wenn sie zum Einfrierdatum offen waren (bereits behobene Funde des Alt werden nicht gegen den Alt gezählt).
  - F5 **Spätere Entscheidungen**: Anforderungen, die auf einer späteren Betreiber-Entscheidung beruhen (z. B. Pflicht-Zwei-Faktor für Administration, Sie-Form, Löschfrist-Wert „0“ verboten), werden als `Status: offen` geführt; der Alt wird daran nur im Fortschritt (A_offen) gemessen, **nicht** in der Parität.
  - F6 **Parität getrennt von Fortschritt**: A_Ist prüft, ob der Neubau nichts verliert (PRI-002); A_offen zeigt Mehrwert. Besteht der Alt eine `Status: Ist`-Zeile nicht, wird geprüft: Testfehler (Test korrigieren, beide neu laufen lassen), Rückschritt des Alt (zählt) oder Spezifikationsfehler (Zeile korrigieren).
  - F7 **`nicht prüfbar` ist nicht `fehlt`**: Fehlende Testbarkeit eines Arms wird getrennt ausgewiesen (QUA-117).
  - F8 **Blindauswertung**: Die Ergebnisdateien beider Arme erhalten neutrale Kennungen (A/B); die Zuordnung ist der Auswertung bekannt, den Prüfenden bei der Fund-Nachprüfung nicht [Festlegung].
  - F9 **Verdeckte Fälle** (QUA-113) laufen gegen beide Arme.
  - F10 **Fund-Nachprüfung** nach QUA-011 mit gleicher Strenge; Falsch-Quote je Arm ausgewiesen.
  - F11 **Keine Mittelwertbildung über Schweren**: kritische und hohe Funde sowie „mehr Zugriff als Soll“ stehen einzeln in der Tabelle.
  - F12 **Wiederholbarkeit**: Skripte, Seeds, Matrix, Rohdaten und Kommandos liegen dem Bericht bei.
  - Abnahme: Prüfliste F1 bis F12 im Bericht mit Ja/Nein und Beleg; ein „Nein“ ohne Begründung macht das Gesamturteil ungültig; Stichprobe: Adapter-Code enthält keine arm-spezifische Auswertung.

- **QUA-129** · P1 · Status: offen — **Entscheidungsregel (vorab eingefroren).** Je Messgröße gilt das Urteil `Neubau besser` (Δ A ≥ +5 Prozentpunkte bzw. Kennzahl um mindestens 10 % günstiger), `gleichwertig` (innerhalb ±5 Prozentpunkte bzw. ±10 %), `Neubau schlechter` [Festlegung]. Das Gesamturteil „Neubau besser“ verlangt: (1) H1 erfüllt (A_Ist des Neubaus = 100 %, A der P0-Anforderungen = 100 %); (2) M4 (Sicherheit) bei keinem Einzelwert `schlechter`, 0 Funde kritisch/hoch; (3) von M3, M5, M7, M8, M9 mindestens drei `besser` und keine mehr als doppelt so ungünstig wie der Alt; (4) A_offen des Neubaus höher als die des Alt. Sonst lautet das Urteil `gleichwertig`, `uneinheitlich` (mit Nennung der Messgrößen) oder `schlechter`.
  - Abnahme: Die Regel steht vor Messbeginn im eingefrorenen Protokoll; das Rechenskript wendet sie auf die Tabellen M1 bis M9 an und gibt das Urteil samt Begründung je Bedingung aus; nachträgliche Änderung der Schwellen ist nur mit Vermerk „nachträglich“ möglich und macht das Urteil kenntlich.

- **QUA-130** · P1 · Status: offen — **Berichtsvorlage.** Gliederung: (1) Kopf (Datum, Versionen, Einfrierdaten, Plattform, Prüfer-Rollen); (2) Hypothesen und Regeln; (3) Matrix-Zusammenfassung (M1, M2); (4) Funde (M3, M4) mit Zahlen nach Schwere und den zehn schwersten im Wortlaut; (5) Leistung (M5), Größe (M6), Testlauf (M7); (6) Oberfläche (M8), Betrieb (M9); (7) Aufwand (M10, nicht im Urteil); (8) Fairness-Prüfliste F1 bis F12; (9) Gesamturteil mit Begründung; (10) Grenzen (QUA-131); (11) Anhang: Matrix (CSV), Fund-Register, Rohdaten, Skripte.
  - Abnahme: Bericht enthält alle elf Teile; fehlt Teil 8 oder 10, ist er nicht gültig; jede Zahl im Text stammt aus einer Tabelle des Anhangs (Stichprobe 10 Zahlen).

- **QUA-131** · P2 · Status: offen — **Grenzen der Aussage.** Der Bericht nennt: (a) je Arm **ein** Durchlauf – die Aussage ist beschreibend, nicht statistisch belegt; kleine Unterschiede zählen nicht; (b) der Alt wurde nicht gegen diese Spezifikation gebaut, der Neubau schon: Die Ergebnisse zu `Status: offen` sind deshalb kein Beleg für bessere Handwerkskunst, sondern für den Umfang, den die Spezifikation fordert (Regel F6); (c) Abnahmetests stammen aus derselben Spezifikation, die das Bau-Team kennt (Gegenmaßnahme: verdeckte Fälle, QUA-113); (d) KI-gestützte Entwicklung ist nicht deterministisch: wiederholter Bau könnte abweichen; (e) Prüfende können irren (Alt: 11 von 76 Funden falsch); (f) Bereichsbewertungen durch Prüf-Agenten (Skala 1 bis 100) sind **kein** Messwert des Urteils; (g) die Rechnungen zu Verkehr und Speicher sind Annahmen bis zur Messung im Echtbetrieb.
  - Abnahme: Teil 10 des Berichts enthält die Punkte (a) bis (g) und gegebenenfalls weitere; der Bericht formuliert das Gesamturteil mit Bezug auf diese Grenzen.

---

## 5. Fallstricke und Lehren

Dieser Abschnitt sammelt, was im Altsystem und im Arbeitsprozess (10. bis 17.10.2026) schiefging, und leitet daraus Regeln ab. Er ist Lehrmaterial für das Neubau-Team und die Abnahme; verbindlich sind die Zeilen `QUA-nnn`, auf die die Tabelle verweist.

### 5.1 Fallstricke aus Tests, Läufen und Prüfungen

| Nr | Fallstrick (Befund) | Beleg | Regel |
|---|---|---|---|
| A1 | Tests scheitern am Wochenende und in den Herbstferien (Beurlaubungs-, Notenbuch-, Klassenbuch-Tests); die Demo konnte keine Klassenarbeit in den Herbstferien anlegen; sieben Testdateien wurden auf „echte Schultage inklusive Ferien“ umgestellt | 16./17.10. | QUA-015 bis QUA-017 |
| A2 | Ein festes Schuljahresdatum steht an drei Stellen im Code; Tests hängen davon ab | 17.10. | QUA-018 |
| A3 | „Heute“ ist am Wochenende aktiv und wirkungslos; die Woche wird nur bei der Initialisierung aus dem Tagesdatum berechnet; die Wochenstatistik rechnete fest Montag bis Freitag | Prüfbefunde U-35, U-59, U-78 | QUA-016 (Uhren 4, 5 und 6), QUA-020 |
| A4 | Zeitzonen: Audit-Abfrage mit Offset wurde nicht nach UTC umgerechnet; Stichtage (Volljährigkeit, Terminzeiten) gelten in Ortszeit | U-65 | QUA-019 |
| B1 | Ein Test sieht „429“ eines anderen Tests; ein Löschkonzept-Test ist nur im parallelen Lauf rot, einzeln grün | Gesamtlauf 1 | QUA-023 |
| B2 | Hintergrunddienste (Versand, Wartung, Auto-Planer) starten in Tests und stören | Testgerüst | QUA-024 |
| B3 | Drei Backend-Tests scheitern, weil Attrappen einen neuen Parameter nicht kannten | 17.10. | QUA-026 |
| B4 | Die Zufallsfolge der Demo änderte sich durch neue Lehrkraft-Felder; Tests mit festen Kürzeln brachen | 10. bis 13.10. | QUA-035 |
| B5 | Uneinheitliche Importpfade der Tests: nur ein Aufrufweg funktionierte | Prüfbefund U-101 | QUA-007 |
| B6 | Eine Ignorierregel der Versionsverwaltung schloss das Testdaten-Verzeichnis (gemeinsame Falltabelle) aus | 10. bis 13.10. | QUA-137 |
| B7 | Ein Migrationstest prüfte eine feste Revisionsnummer und brach bei jeder neuen Migration | 10. bis 13.10. | QUA-090 |
| C1 | Der Gesamttest auf dem PC lief 18 Minuten ohne Fortschritt (13:23 bis 13:55) und wurde abgebrochen; die Ursache blieb ungeklärt. Betreiber: „Ich glaube, du hängst irgendwo. Du hast die ganze Zeit noch keinen Progress gemacht und das läuft schon ewig lange.“ | 17.10. | QUA-132, QUA-133 |
| C2 | Der erste Gesamtlauf brach bei rund 35 % ab; offene Fehler in sechs Testdateien; ein Teilstand wurde nicht als Ergebnis ausgegeben | Stand 17.10. | QUA-133 |
| C3 | Nutzungsgrenzen brachen Agenten ab (Runde 2; mehrfach am 12. und 13.10.; Wochengrenze bis 16.10.); halbfertige Arbeit blieb liegen; die Recherche startete jedes Mal neu. Lehre: Pause bis zur Rückkehr der Grenze, **nie** Umweg über andere Konten oder Schlüssel | 12. bis 16.10. | QUA-134 |
| C4 | Ein Syntaxfehler im Startmodul war am 17.10. für eine Minute im Stand (14:42, behoben 14:43) | 17.10. | QUA-055 |
| C5 | Ein Prüf-Agent meldete „Tests laufen nicht“ – falsch, die Tests liefen mit der richtigen Umgebung | 16.10. | QUA-011, QUA-135 |
| D1 | Windows-Abweichungen: Ersetzen offener Dateien (Dateisperre), Betriebssystem-Kennzahlen, Zeilenenden von Shell-Skripten (Fehler im Linux-Lauf), Groß-/Kleinschreibung von Importen. Die „bekannten Windows-Fehler“ waren teils echte Fehler. Betreiber: „Was genau für ein Windows-Failure … und gibt es mir keinen Kontext und gar nichts. Was ist da?“ | 11./12.10. | QUA-029 |
| D2 | Der Gesamtlauf belastete den PC des Betreibers 15 bis 20 Minuten; „keine Server auf dem PC“ wurde nicht erneut abgefragt | 16.10. | QUA-140 |
| E1 | Ein Tabellenumbau an einer Tabelle mit kaskadierenden Fremdschlüsseln löscht abhängige Zeilen; eine Migration konnte beim Upgrade Material in Bestandsordnern löschen | 11./12.10. | QUA-092 |
| E2 | Mehrere Migrationsköpfe und kollidierende Nummern nach Zusammenführung zweier Zweige | 11./12.10. | QUA-090 |
| E3 | Klartext-Altbestand und ein erst am 16.10. entdecktes unverschlüsseltes Planungsdokument; ein Entschlüsselungsfehler konnte Klassenbuch-Notizen still überschreiben | 16./17.10. | QUA-081, QUA-082 |
| F1 | Von 76 Funden einer reinen Lese-Bewertung waren 42 bestätigt, 11 falsch, 23 unklar | 16.10. | QUA-011, QUA-135 |
| F2 | Mehrfach gemeldete Fehler des Betreibers waren nicht umgesetzt; Aussagen „erledigt“ ohne Test | 12.10. | QUA-001, QUA-010 |
| F3 | Eine Marktliste nannte das digitale Klassenbuch als Lücke, obwohl es vorhanden ist (der Agent hatte nur das Backlog gelesen) | 13.10. | `fehlt` nur nach Bestätigung durch die Prüfung (QUA-117) |
| G1 | Parallele Agenten teilten sich ein Browserfenster: Tabs sprangen (12:42 bis 12:50) | 16.10. | QUA-136 |
| G2 | Für mehrere neue Funktionen fehlte die Browser-Prüfung; „grün“ galt nur für geänderte Bereiche | 16./17.10. | QUA-046 |
| G3 | Das Laden des Prüf-Browsers war in einzelnen Umgebungen blockiert; ein mitgelieferter Browser wurde verwendet | 10. bis 13.10. | QUA-136 |
| G4 | Eine Anmeldung auf der echten Instanz mit allen Konten wurde abgelehnt; Passwörter nur auf lokalen Testservern; der Betreiber meldet sich dort selbst an | 16.10. | QUA-136, QUA-037 |
| G5 | Ein Klartext-Passwort war auf einem Bildschirmfoto sichtbar | Alt (Datum nicht belegt) | QUA-037, QUA-053 |
| H1 | Der Designregel-Test erfasste nur eine Stilklasse „explain“; Erklärtexte in anderer Form (rund 65 Restfälle) blieben unentdeckt | 11. bis 16.10. | QUA-085 |
| H2 | Dokumente veralteten (Sicherheits- und Architekturbeschreibung: Datei-Allowlist, Rechtetabelle, Datenkategorien, Rollenzahl) | 11.10. | QUA-138 |
| I1 | Kostenlose Fremddienste dürfen Daten speichern oder zum Training nutzen; eine Sperre „Data Exfiltration“ verhinderte die Weitergabe von Quellcode; ein Zugangsschlüssel wurde in den Chat gepostet | 13.10. | QUA-139 |
| J1 | Zu viele Prüfungen: „du hast jetzt fast 1400 Checks gemacht. Das ist ein bisschen viel.“ | 12.10. | QUA-005 |
| J2 | Testzahlen (196 bis 1.736) sind nicht vergleichbar: Umfang und Zählweise wechselten | 13./17.10. | Abschnitt 4, Messgröße M2 |

- **QUA-132** · P1 · Status: offen (Ist: Überwachung nach dem Hänger vom 17.10. eingeführt, Ursache ungeklärt) — **Zeitlimits und Hänger-Überwachung.** Jeder Test hat ein Zeitlimit (60 Sekunden [Festlegung]); jeder Lauf gibt mindestens alle 60 Sekunden Fortschritt aus (Zähler erledigt / gesamt); ein Wächter bricht einen Lauf nach 5 Minuten ohne Fortschritt ab und meldet „hängend“ mit dem letzten Test; der Zustand des Laufs ist maschinenlesbar (`läuft` / `fertig` / `hängend` / `abgebrochen`).
  - Abnahme: Ein absichtlich endloser Test wird nach dem Zeitlimit abgebrochen und mit Namen gemeldet; ein künstlich eingefrorener Lauf wird nach 5 Minuten beendet; der Statusbericht enthält die Zähler; Gesamtlauf E1 bis E4 ohne Hänger (Messgröße M7).

- **QUA-133** · P1 · Status: Ist (Ist: Regel seit 17.10. — Gesamttest nicht als gelöst melden, solange Teilergebnisse ausstehen; kurzer maschinenlesbarer Fortschritt) — **Ehrliche Statusmeldung.** Eine Meldung „grün“ nennt Umfang (Ebenen, Bereiche), Anzahl, Datum und Version; ein Gesamtlauf gilt erst als bestanden, wenn alle Teile vorliegen; Teilstände werden als solche gekennzeichnet. Bei Unterbrechung hält die Arbeit an und fragt nach, statt ungefragt weiterzulaufen.
  - Abnahme: Das Statusformat enthält die Pflichtfelder (Umfang, Zähler erledigt/gesamt, Datum, Version, Ergebnis); ein Bericht „grün“ ohne Umfangsangabe wird zurückgewiesen; Stichprobe 5 Meldungen.

- **QUA-134** · P1 · Status: offen (Ist: Zwischenstände gingen bei Abbrüchen verloren; Fortsetzung nur von Hand) — **Fortsetzbar nach Abbruch.** Abnahme- und Prüfarbeiten sind in kleine, einzeln speicherbare Schritte geschnitten; Zwischenergebnisse (Lauf-Berichte, Teil-Matrix, Funde) werden sofort in Dateien geschrieben und beim Neustart wiederverwendet; ein Abbruch durch Nutzungsgrenze, Sitzungsende oder Systemfehler führt zu einer Pause bis zur Rückkehr der Grenze – **nie** zu einem Umweg über fremde Schlüssel oder zusätzliche Kosten; Dateien mit gemeinsamen Notizen werden nur angehängt.
  - Abnahme: Das Prüfskript wird nach künstlichem Abbruch in Schritt k neu gestartet und liefert dasselbe Endergebnis ohne Doppelzählung; das Protokoll nennt den Fortsetzungspunkt; kein Zwischenstand liegt nur im Arbeitsspeicher.

- **QUA-135** · P1 · Status: Ist — **Prüf-Agenten: Beleg, Nachprüfung, Einfachheit.** Prüfaufträge sind lesend; jeder Fund trägt einen Beleg (Anfrage und Antwort bzw. Schritte zur Nachstellung); bevor ein Prüfer meldet, „Tests laufen nicht“ oder „Funktion fehlt“, führt er die Tests mit der dokumentierten Umgebung aus bzw. probiert die Funktion; einfache Durchsichten übernehmen kleine Modelle, komplexe Bauaufgaben mittlere, ein teures Modell nur auf ausdrückliche Bitte des Betreibers; Befunde werden vor dem Bau am Code oder per Test bestätigt (QUA-011).
  - Abnahme: Stichprobe von 10 Funden: Beleg vorhanden, Nachprüfung dokumentiert; Falsch-Quote je Prüfauftrag steht im Bericht (Alt: 11 von 76); ein Fund ohne Beleg wird nicht gezählt.

- **QUA-136** · P2 · Status: Ist (Ist: eigene Ports und Hostnamen je Prüfer; Regeln für den Prüf-Browser nicht schriftlich) — **Regeln für den Prüf-Browser (Abschnitt 5.2).** Prüfskripte halten die Regeln R1 bis R9 ein; Anmeldung nur an lokalen Testinstanzen mit je Lauf erzeugten Testkonten; kein Prüf-Server dauerhaft auf dem Rechner des Betreibers.
  - Abnahme: Selbsttest der Prüfskripte: Darstellung (Größe, Farbschema) wird zu Beginn jedes Checks gesetzt und am Ende auf Desktop zurückgesetzt; zwei Prüfer laufen gleichzeitig ohne Tab-Konflikt; Prozess- und Portliste nach dem Lauf ohne Prüf-Server; Anmeldeversuch an einem Ziel außerhalb `*.localhost` bricht das Skript ab.

- **QUA-137** · P2 · Status: offen — **Testdaten liegen im Repository und werden nicht ignoriert.** Falltabellen (Wochen- und Kalenderfälle, QUA-020), Archiv älterer Beispiel-JSON (QUA-038), Datenbank-Archive je Epoche (QUA-091), Seeds und Soll-Matrizen liegen im Repository; keine Ignorierregel erfasst sie.
  - Abnahme: Frischer Klon + Standardbefehle (QUA-007): 0 fehlende Testdateien; die Prüfung „ist Datei ignoriert?“ meldet für alle Dateien im Testdaten-Verzeichnis „nein“.

- **QUA-138** · P1 · Status: offen (Ist: Test gleicht die Rechtetabelle der Architekturbeschreibung mit dem Katalog ab; weitere Dokumente veraltet) — **Dokumentation, Katalog und Verhalten stimmen überein.** Rechte, Rollen, Fristen, Variablen und Grenzwerte in Handbuch, Betreiberpaket und Hilfe werden aus dem Katalog bzw. der Konfiguration erzeugt oder per Test abgeglichen; jede dokumentierte `SM_*`-Variable kommt im Container an (Alt-Fund U-09: 2FA-Pflicht und SMS waren im Container wirkungslos); Beispiel-Umgebungsdatei ohne Kommentare hinter Werten, wenn sie als Umgebungsdatei dient (U-44).
  - Abnahme: Abgleichstest über Rechte-Katalog ↔ Dokumentation (0 Abweichungen), Variablentabelle ↔ Containerumgebung (jede dokumentierte Variable wirkt), Fristen ↔ Textvorlagen (SIC-008); Gegenprobe mit absichtlich veralteter Tabelle scheitert.

- **QUA-139** · P0 · Status: Ist (Ist: Regel seit 13.10.: kein Quellcode, keine Schlüssel, keine Kundendaten an kostenlose Fremddienste) — **Keine Weitergabe an Fremddienste bei Prüfung und Bau.** Prüf- und Hilfswerkzeuge außerhalb der eigenen Umgebung (kostenlose Modelle, Recherche-Dienste, Online-Prüfer) erhalten **nie** Quellcode, Schlüssel, Zugangsdaten, `.env`-Inhalte, Kundendaten, Diktate/Aufnahmen oder Personenbezug; erlaubt sind öffentliche Texte, Fragen ohne Daten und rein synthetische Beispiele. Schlüssel werden nie in Befehle, Chat oder Berichte kopiert.
  - Abnahme: Das Prüfprotokoll nennt je externem Dienst die übergebenen Dateiarten; ein Scan der übergebenen Dateien auf Geheimnisse und Personenbezug liefert 0 Treffer; Probe: Übergabe einer Datei mit Schlüsselmuster wird vom Übergabewerkzeug verweigert.

- **QUA-140** · P1 · Status: Ist (Ist: Gesamtlauf auf dem Heimserver unter Linux; lokale Läufe sollen den PC nicht 15 bis 20 Minuten belasten) — **Ort und Budget der Läufe.** Gesamtlauf, Last-, Sicherheits- und Betriebsläufe laufen in der Linux-Zielumgebung (Server oder Container), nicht auf dem Arbeitsrechner des Betreibers; lange Läufe (über 5 Minuten) und Prüf-Server auf dem Arbeitsrechner nur nach Rückfrage und mit Stopp danach. Ein Entwicklungslauf (geänderter Bereich plus Basis-Querschnitt, QUA-005) dauert höchstens 3 Minuten [Festlegung].
  - Abnahme: Das Lauf-Protokoll nennt den Ausführungsort; Läufe E6 bis E8 auf dem Arbeitsrechner → Verstoß; gemessene Dauer eines Entwicklungslaufs ≤ 3 Minuten (Median von 5 Läufen).

- **QUA-141** · P2 · Status: Ist (Ist: Dateihoheit je Paket, Nachträge nur anhängend, eigene Ports je Agent, Obergrenze gleichzeitiger Agenten wegen Nutzungsgrenze) — **Arbeitsteilung und Dateihoheit bei paralleler Arbeit.** Bau- und Prüfaufträge, die gleichzeitig laufen, ändern nur Dateien ihres Pakets; gemeinsam genutzte Bausteine (Rechtekatalog, Konfiguration, Anwendungsrahmen, Speicher des Planungsstands, Oberflächen-Rahmen, Designregel-Test, Architekturbeschreibung) werden nur gezielt, in kleinen Blöcken und nach frischem Lesen geändert; gemeinsame Notizdateien werden nur angehängt; Versionsverwaltung, Server und Datenbanken fasst ein Auftrag nur an, wenn der Auftrag es ausdrücklich sagt; die Zahl gleichzeitiger Aufträge bleibt unter der vereinbarten Obergrenze (Alt: höchstens drei Umsetzungs- und Design-Agenten gleichzeitig; Obergrenze 20 gleichzeitige Agenten insgesamt).
  - Abnahme: Prüfskript über die Änderungsliste eines Auftrags: jede geänderte Datei liegt im zugeordneten Bereich oder steht auf der Liste der gemeinsamen Bausteine mit Vermerk im Auftragsprotokoll; Änderungen an Notizdateien sind reine Anhänge (kein gelöschter oder geänderter Altinhalt); Stichprobe 5 Aufträge.

### 5.2 Eigenheiten des Prüf-Browsers

Herkunft: Beobachtung vom 16.10. (gemeinsames Fenster) und Beschreibung des im Bau eingesetzten Prüf-Browsers (Stand 18.10.). Die Regeln gelten für jedes Prüfwerkzeug mit ähnlichen Eigenschaften.

| Nr | Eigenheit | Folge | Regel |
|---|---|---|---|
| R1 | Ein Prüf-Browser, ein vorderster Tab: parallele Prüfer wechseln sich die Fenster weg | Tabs springen; Klicks treffen die falsche Seite | je Prüfer ein eigener Tab, kein gemeinsames Fenster; parallele Prüfer nur mit getrennten Prüf-Browsern |
| R2 | Eine emulierte Fenstergröße bleibt je Tab über Neuladen und Seitenwechsel bestehen; Voreinstellungen werden am Ende eines Auftrags unter Umständen zurückgesetzt | Folgeprüfungen laufen unbemerkt im falschen Format | Größe zu Beginn **jedes** Checks ausdrücklich setzen, am Ende auf Desktop zurücksetzen; im Bericht die Größe nennen |
| R3 | Handy-Voreinstellung (und jede Breite unter 768 px) schaltet zusätzlich Handy-Kennung und Touch-Punkte; Klicks bleiben Mausklicks | Touch-Verhalten ist so nicht geprüft; geräteabhängige Weichen laufen beim Laden | nach dem Wechsel die Seite neu laden; Touch-Gesten (langes Drücken, Ziehen) mit Touch-Emulation prüfen (QUA-049) |
| R4 | Farbschema (hell/dunkel) lässt sich emulieren und bleibt über Neuladen; der Prüf-Browser gleicht es bei einem Wechsel des Anwendungs-Themas wieder an; lokal geöffnete oder statische Vorschauen werden stets hell dargestellt | falsches Schema im Bericht; Dunkelmodus ungeprüft | Schema vor jedem Check setzen und nennen; Prüfung immer über die laufende Instanz (`<paket>.localhost`), nicht über Datei-Vorschau |
| R5 | Ein verdecktes Prüf-Fenster läuft als Hintergrundseite: Zeitgeber werden gedrosselt | Zeit- und Leistungswerte sind unzuverlässig; Hilfe-Zeitgeber (2 s) kann abweichen | Leistung nur mit dem Lastwerkzeug messen (QUA-041); Zeitgeber-Logik mit gesteuerter Uhr testen (QUA-013); Browser-Check im sichtbaren Fenster |
| R6 | Bildschirmfoto-Koordinaten gelten nur für das letzte (ggf. skalierte) Bild | Klicks daneben | Elemente über Referenz oder Suche ansprechen; Seitenstruktur und -text statt Bildern lesen, wo möglich |
| R7 | Neue Websites brauchen Freigabe; Fremdseiten und Anmeldungen auf echten Instanzen gehören nicht in den Prüf-Ablauf | Prüfung hängt an einer Rückfrage; Risiko für Zugangsdaten | nur lokale Testinstanzen; Testkonten je Lauf erzeugt; Passwort nie in Berichte, Chat oder Bildschirmfotos (QUA-037, QUA-053) |
| R8 | Das Herunterladen von Prüf-Browsern ist in manchen Umgebungen blockiert | Skript startet nicht | mitgelieferten Browser der Umgebung verwenden; Voraussetzung im Betreiberpaket der Entwicklung nennen |
| R9 | Chats und verschlüsselte Funktionen laufen nur über HTTPS oder `localhost`; sichere Cookies fordern HTTPS | Funktion scheint „kaputt“ | Prüf-Host `<paket>.localhost` (zählt als lokal); die Sicherheitsabnahme (E7) läuft zusätzlich mit HTTPS |

---

## 6. Reihenfolge der Abnahme in Phasen

Die Abnahme folgt dem Bau in **Phasen mit Toren (Gates)**. Ein Gate ist ein Abnahmeprotokoll (QUA-112) mit Zahlen und Entscheidung; ohne bestandenes Gate beginnt die Folgephase nicht (Begriffe, Abschnitt 0). Die Phasen ordnen sich nach Abhängigkeiten: Erst Fundament und Sicherheit (alles Spätere erbt Rechte, Verschlüsselung, Protokoll), dann Stammdaten und Planung, dann Alltag, dann Leistung/Integration/Betrieb, zuletzt Gesamtabnahme und Freigabe. Die Roadmap (Datei 10) ordnet die darüber hinaus offenen Punkte in Wellen; Welle 0 (Pflicht vor jedem Einsatz bei einer echten Schule) fällt in Phase 6, die Wellen 2 bis 4 in Phase 7. Die noch offenen Qualitätsarbeiten der Roadmap (Browser-Rundgänge je Rolle, Gesamttest, Lasttest, Marktreife-Checkliste) tragen dort die Kennungen QUA-901 ff.; dieses Dokument legt Verfahren und Werte fest.

### 6.1 Phasenplan

| Phase | Inhalt (Fachdateien) | Gate |
|---|---|---|
| 0 Fundament | PRI; Testgerüst (Uhr, Seeds, Register, Adapter, Gegenproben, Bereichskarte, CI) nach Abschnitt 1; Konfiguration und Betriebsmodi (BET); Datenmodell-Grundgerüst; Verfahren der Verschlüsselung und Schlüsselverwaltung (DAT-001 bis DAT-011); Migrationsgerüst | G0 |
| 1 Konten, Rechte, Sicherheit | ANM, REC; SIC (Zugriffskontrolle, Sitzungen, Drosselung, Eingabe, Dateien, Transport); DAT (Protokolle, Audit, Beobachtung); Oberflächen-Grundlagen (Tokens, Dialoge, Hilfe, App-Rahmen, Raster-Baustein); Demo-Sperre | G1 |
| 2 Stammdaten und Planung | STA, LEH, STP (Regeln, Kalender, Generator); INT-Grundlagen (CSV, Untis, Ferien, iCal); Planungsbausteine der Oberfläche | G2 |
| 3 Alltag | VER, KLB, SCH, KUR, NAC, FOR, BEN | G3 |
| 4 Leistung, Integration, Betrieb | NOT (Noten, Kompetenzen), Lernaktivitäten; DAT (Löschkonzept, Auskunft, Pseudonymisierung); INT (API-Zugänge, Fremdsysteme, Webhooks); BET (Sicherung, Updates, Lizenz, Zahlungen, Anbieter-Portal, Einrichtung, Jahreswechsel); technische Teile von REH | G4 |
| 5 Gesamtabnahme | alle Ebenen E1 bis E8, Vergleichsmessung (Abschnitt 4), Marktreife-Checkliste | G5 |
| 6 Freigabe für die erste echte Schule | Testtag-Szenario durch den Betreiber, Wiederholung des Penetrationstests, Rechts- und Datenschutz-Prüfungen (Welle 0 der Roadmap), Pilotinstanz im Produktivmodus | G6 |
| 7 Ausbau | Wellen 2 bis 4 der Roadmap, nur mit Freigabe des Betreibers (Entscheidung E-02) | G7.n je Welle |

- **QUA-142** · P0 · Status: offen — **Gate-Prinzip.** Jede Phase endet mit einem Gate; die Folgephase beginnt erst nach dem Beschluss „freigegeben“ oder „mit Auflagen“ (Auflagen mit Frist). Gates werden nicht übersprungen; eine Ausnahme braucht einen schriftlichen Beschluss des Betreibers. Parallel gearbeitet wird **innerhalb** einer Phase (getrennte Fachbereiche, getrennte Dateien), nicht über Gates hinweg. Das Bau-Team stellt den Antrag, die Abnahme prüft und empfiehlt, den Beschluss fasst bei G5 und G6 der Betreiber, bei G0 bis G4 die Abnahme.
  - Abnahme: Zu jeder Phase liegt ein Abnahmeprotokoll vor, bevor der erste Auftrag der Folgephase beginnt (Zeitstempel des Protokolls früher als der erste Änderungsnachweis der Folgephase); Auflagen sind mit Frist im Fund-Register geführt.

- **QUA-143** · P1 · Status: offen — **Phasenplan mit Zuordnung der Kennungen.** Jede Anforderungs-Kennung der Fachdateien ist genau einer Phase zugeordnet (Spalte `phase` in der Abdeckungs-Matrix, QUA-116); Querschnittsanforderungen (SIC, DAT, OBE, REH) sind der Phase zugeordnet, in der ihre erste Route bzw. Seite entsteht, und gelten ab dann für alle weiteren.
  - Abnahme: Matrix ohne leere Phasenzelle; die Summe der Kennungen je Phase gleicht der Gesamtzahl; ein Querschnittstest wird ab der Phase gefahren, in der die erste betroffene Route entsteht.

### 6.2 Kriterien der Gates

| Gate | Pflichtprüfungen | Bestehen, wenn |
|---|---|---|
| **G0** Fundament | Aufrufweg und frischer Klon (QUA-007, QUA-137); Uhr-Schnittstelle (QUA-015); Isolation und Hintergrunddienste (QUA-022 bis QUA-024); Adapter-Probe (QUA-032); Seeds und Hash (QUA-033 bis QUA-035); Register, Rollenfeld, Gegenproben (QUA-066, QUA-067, QUA-069); Migration frisch (QUA-090); Build-Prüfungen (QUA-055); Hänger-Überwachung (QUA-132); Verschlüsselungsverfahren mit Marker-Test an einer Beispiel-Spalte (QUA-081); Start-Pflichtprüfungen im Produktivmodus (BET-008) | alle genannten Prüfungen grün; Gegenprobe jedes vorhandenen Querschnittstests scheitert wie erwartet; E1/E2 des Gerüsts grün; Gesamtlauf läuft in der Linux-Zielumgebung ohne Hänger |
| **G1** Konten, Rechte, Sicherheit | Querschnitt 2.2 bis 2.5, 2.9 und 2.10 für **alle** Routen der Phasen 0 und 1; Rollenfeld R01 bis R33 vollständig; Marker-Suche über alle Speicherorte; Anmelde-Drosselung mit Schulnetz-Test (QUA-098); Default-Deny in vier Kontexten (QUA-072); Schutzregeln auf jedem Weg (QUA-073); Wegwerf-Instanz im Produktivmodus (QUA-056); Vorlauf eines autonomen Sicherheitswerkzeugs auf Phase-1-Funktionen; Rundgang Anmeldung, Konto, Rechte (QUA-046 erste Fassung) | 0 Abweichungen in den Querschnittstests; 0 offene Funde kritisch/hoch; Sicherheits-Prüfliste (QUA-054) für Zugriffskontrolle, Anmeldung, Sitzungen ohne „fehlt“ |
| **G2** Stammdaten und Planung | Fachabnahmen STA, LEH, STP, INT-Grundlagen; Datums-Matrix mit zehn Uhren für Kalender und Planung (QUA-016); Wochen-Falltabelle für Alt und Neubau (QUA-020); Rundlauf der Beispielschulen (QUA-038); Generator-Last, erster Lauf (QUA-042); ein Raster (QUA-088); Querschnitt für neue Routen; Rundgang Planer, Lehrkraft, Administration, Sekretariat | alle `P0` und `P1` der drei Kürzel `erfüllt` oder mit Beschluss; Datums-Matrix 10 von 10 grün; Generator-Lauf der Lastschule ohne harte Konflikte |
| **G3** Alltag | Fachabnahmen VER, KLB, SCH, KUR, NAC, FOR, BEN; Volljährigkeit an den Grenzen (QUA-021); Race-Tests (QUA-043); Rechte-Matrix der Krankmeldungen; Zwei-Browser-Szenarien (QUA-051); Rundgang aller Rollen, erste Fassung (QUA-046); Barrierefreiheit, erster Lauf (QUA-048); Lastvorlauf S1 und S3 (QUA-040) | alle `P0`/`P1` der sieben Kürzel `erfüllt` oder mit Beschluss; Querschnitt für neue Routen grün; Rundgang ohne Fund kritisch/hoch; Lastvorlauf: 0 % Fehler |
| **G4** Leistung, Integration, Betrieb | Fachabnahmen NOT, INT, DAT, BET; Datenübernahme-Trockenlauf (QUA-093); Update und Rollback (QUA-060); Wiederherstellungs-Rundlauf (QUA-061); Probelauf an Kopie (QUA-062); Löschkonzept, Auskunft und Lizenzstufen mit fester Uhr; Marker-Suche über **alle** Bereiche; API-Zugänge im Default-Deny (QUA-072) | alle genannten Prüfungen grün; Wiederherstellung: Anzahl lesbarer Dateien gleich Anzahl Dateien; Update-Rollback ohne Datenverlust |
| **G5** Gesamtabnahme (Release-Kandidat) | L1 bis L15 (QUA-110); alle Ebenen E1 bis E8 mindestens einmal gelaufen (QUA-003); Vergleichsmessung nach Abschnitt 4 durchgeführt und berichtet; Abnahmeprotokoll (QUA-112) | alle Kriterien L1 bis L15 erfüllt; Funde kritisch/hoch: 0 (QUA-059); Matrix: P0 100 %, `Status: Ist` 100 %, P1 mindestens 95 % |
| **G6** Freigabe für die erste Schule | Testtag-Szenario vom Betreiber durchgeklickt (QUA-036); Wiederholung des Penetrationstests (QUA-057); Marktreife-Checkliste ohne offenen P0-Punkt (PRI-001); Rechts- und Datenschutz-Prüfungen der Roadmap-Welle 0 (Auskunft, Löschfristen, Datenpannen-Prozess, Barrierefreiheitserklärung, Namens- und Markenprüfung); Screenreader-Protokoll (QUA-050); Einrichtung ohne Entwicklerwissen (QUA-064); Pilotinstanz im Produktivmodus | alle P0-Einträge der Welle 0 bestanden; Wiederholungstest ohne offenen Fund kritisch/hoch; mittlere Funde behoben oder per Beschluss zurückgestellt; Entscheidungen E-03 bis E-10 des Betreibers getroffen |
| **G7.n** Ausbau-Welle | Definition of Done je Anforderung (QUA-108) für jede Kennung der Welle; Regressionslauf der betroffenen Bereiche und des Basis-Querschnitts; Querschnitt für neue Routen; Rundgang der betroffenen Seiten; Gesamtlauf E1 bis E4 vor dem Aufspielen | alle Kennungen der Welle `erfüllt`; Release-Kriterien L1, L2, L4, L8, L9 erfüllt |

- **QUA-144** · P1 · Status: offen — **Gate G0 (Fundament).** Die Prüfungen und Bestehensbedingungen der Zeile G0 sind erfüllt, bevor Fachfunktionen gebaut werden.
  - Abnahme: Protokoll G0 mit Verweisen auf die genannten QUA-Kennungen; ein Fachbereich, dessen erster Auftrag vor dem Protokoll G0 beginnt, wird im Protokoll als Verstoß geführt.

- **QUA-145** · P0 · Status: offen — **Gate G1 (Konten, Rechte, Sicherheit).** Die Zeile G1 ist erfüllt; das gilt auch für jede später hinzukommende Route, deren Querschnittstests ab sofort automatisch laufen.
  - Abnahme: Protokoll G1 mit den Querschnittsberichten (Abschnitt 2.11) und der Liste der Ausnahmelisten; der Querschnittsbericht weist 0 Abweichungen aus; die Prüfliste QUA-054 ist für die genannten Punkte ohne „fehlt“.

- **QUA-146** · P1 · Status: offen — **Gate G2 (Stammdaten und Planung).** Die Zeile G2 ist erfüllt.
  - Abnahme: Protokoll G2 mit Datums-Matrix (zehn Läufe), Wochen-Falltabelle (mindestens 30 Fälle) für Alt und Neubau, Generator-Bericht; Rundgangsberichte der genannten Rollen.

- **QUA-147** · P1 · Status: offen — **Gate G3 (Alltag).** Die Zeile G3 ist erfüllt.
  - Abnahme: Protokoll G3 mit Rechte-Matrix der Krankmeldungen (Fachlehrkraft 403 bzw. 404, Klassenleitung 200, Administration ohne Zugriff), Volljährigkeits-Matrix, Race-Test-Ergebnissen, Rundgangsberichten aller Rollen und Lastvorlauf.

- **QUA-148** · P0 · Status: offen — **Gate G4 (Leistung, Integration, Betrieb).** Die Zeile G4 ist erfüllt.
  - Abnahme: Protokoll G4 mit Abgleichstabelle der Datenübernahme, Update-/Rollback-Protokoll, Wiederherstellungsbericht (Konten, Dateien, lesbare Dateien), Probelauf-Protokoll und Marker-Suche über alle Bereiche (0 Klartext-Treffer).

- **QUA-149** · P0 · Status: offen — **Gate G5 (Gesamtabnahme).** Die Zeile G5 ist erfüllt; alle Ebenen E1 bis E8 sind mindestens einmal mit Datum, Umgebung und Ergebnis gelaufen (QUA-003); das Vergleichs-Experiment (Abschnitt 4) ist durchgeführt, die Berichtsteile 1 bis 11 liegen vor.
  - Abnahme: Protokoll G5 enthält die Prüfliste L1 bis L15 mit Beleg je Zeile, die Matrix-Zusammenfassung nach Priorität und Kürzel und den Experiment-Bericht; Probe: fehlt ein Lastbericht oder ein Penetrationstest-Bericht, verweigert das Release-Werkzeug die Freigabe.

- **QUA-150** · P0 · Status: offen — **Gate G6 (Freigabe für die erste echte Schule).** Die Zeile G6 ist erfüllt; die Auslieferung an eine Schule erfolgt zuerst als Pilot mit eigener Instanz im Produktivmodus (BET-003, BET-006).
  - Abnahme: Protokoll G6 mit dem Testtag-Protokoll (Datum, durchführende Person, Ergebnis), dem Wiederholungs-Prüfbericht, der ausgefüllten Marktreife-Checkliste (rund 50 Punkte in sechs Gruppen, 0 offene P0-Punkte) und den Entscheidungen des Betreibers; ohne Protokoll G6 wird keine Instanz für eine echte Schule bereitgestellt.

### 6.3 Reihenfolge der Prüfungen innerhalb eines Gates

| Schritt | Inhalt | Kosten |
|---|---|---|
| S1 | statische Prüfungen: Syntax, Lint, Typen, Geheimnis-Suche, Lizenzscan, Abhängigkeits-Audit, Image-Inhalt (QUA-055) | niedrig |
| S2 | Register-Prüfungen (QUA-066, QUA-068, QUA-069) | niedrig |
| S3 | E1 Logik und E2 Schnittstelle (im Gate: Gesamtlauf; in der Entwicklung: betroffene Bereiche) | mittel |
| S4 | E3 Querschnitt (Abschnitt 2.2 bis 2.4, 2.6, 2.9, 2.10) | mittel |
| S5 | E4 Daten: Migration, Marker-Suche, Archive, Datenübernahme-Trockenlauf | mittel |
| S6 | Datums-Matrix (QUA-016), Zufalls- und Parallel-Läufe (QUA-023), Vertrags-Test der Attrappen (QUA-026) | mittel |
| S7 | E5 Browser-Rundgänge und Barrierefreiheit | hoch |
| S8 | E6 Last | hoch |
| S9 | E7 Sicherheitsabnahme auf Wegwerf-Instanz | hoch |
| S10 | E8 Betrieb: Update, Rollback, Wiederherstellung, Alarme | hoch |
| S11 | Matrix, Fund-Register, Protokoll, Entscheidung (QUA-112) | niedrig |

- **QUA-151** · P1 · Status: offen — **Reihenfolge innerhalb eines Gates.** Die Prüfungen eines Gates laufen in der Reihenfolge S1 bis S11; ein Schritt beginnt erst, wenn der vorige ohne kritische Fehler endete (die teuren Ebenen E5 bis E8 laufen nicht auf einem Stand, der die billigen Prüfungen nicht besteht).
  - Abnahme: Das Gate-Protokoll listet die Schritte mit Zeitstempel in dieser Reihenfolge; ein Schritt S7 bis S10 mit Zeitstempel vor dem Ende von S1 bis S6 oder auf einem Stand mit rotem Schritt S1 bis S6 wird als Verstoß vermerkt; in der Entwicklungsschleife gilt QUA-005 (nur geänderte Bereiche, Gesamtlauf einmal je Gate).

- **QUA-152** · P1 · Status: offen — **Nachbesserung nach einem Gate.** Nach der Behebung von Funden wird das Gate **nicht vollständig** wiederholt, sondern: (1) die fehlgeschlagenen Prüfungen, (2) die Prüfungen der geänderten Bereiche, (3) der Basis-Querschnitt (Register, Rechte, 404, Audit, Verschlüsselung), (4) der Gesamtlauf E1 bis E4 einmal vor der Freigabe, wenn gemeinsam genutzte Bausteine, das Schema oder das Register geändert wurden [Festlegung]; jede Behebung folgt QUA-109.
  - Abnahme: Das Nachprüfungs-Protokoll nennt je Behebung die ausgeführten Prüfungen und begründet, warum der Gesamtlauf nötig war oder nicht; Stichprobe 3 Nachbesserungen.

- **QUA-153** · P2 · Status: offen — **Abnahme der Ausbau-Wellen.** Jede Welle 2 bis 4 der Roadmap erhält ein Teil-Gate G7.n (Zeile G7.n) und beginnt erst mit der Freigabe des Betreibers (Entscheidung E-02: Wettbewerbs-Kleinfunktionen nur als Liste, bis er entscheidet); der Betreiber hat am 16.10. ausdrücklich gesagt, die Vorschläge nicht einzubauen, bevor er sie gesehen hat.
  - Abnahme: Je Welle ein Protokoll mit Freigabevermerk des Betreibers vor Baubeginn und mit DoD-Nachweisen je Kennung; eine Kennung der Wellen 2 bis 4 mit Änderungsnachweis vor dem Freigabevermerk wird als Verstoß geführt.

<!--ENDE-->
