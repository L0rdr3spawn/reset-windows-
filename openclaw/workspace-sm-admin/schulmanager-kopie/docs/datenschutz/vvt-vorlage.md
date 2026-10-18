# Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO) – Vorlage für Schulpuls

> **Vorlage, keine Rechtsberatung.** Felder in `[eckigen Klammern]` füllt die Schule aus. Rechtsgrundlagen und Fristen mit dem Landesschulgesetz, der Landesdatenschutzbehörde und der bzw. dem Datenschutzbeauftragten abgleichen.

## 1. Allgemeine Angaben

| Feld | Eintrag |
|---|---|
| Verantwortlicher | [Name der Schule, Anschrift, Telefon, E-Mail], vertreten durch die Schulleitung [Name] |
| Schulträger | [Name, Anschrift] |
| Datenschutzbeauftragte/r | [Name, Kontakt] |
| Verfahren | Schulpuls – Stunden-, Vertretungs- und Schulverwaltung (Stundenplan, Vertretung, Klassenbuch/Anwesenheit, Krankmeldungen, Mitteilungen/Nachrichten, Kursräume, Notenbuch, Konten) |
| Einführung am | [Datum] |
| Betrieb | [Selbst betrieben durch … / Hoster … / Rechenzentrum, Standort Deutschland] |

## 2. Teilverfahren

### 2.1 Stunden-, Vertretungs- und Raumplanung

| Feld | Eintrag |
|---|---|
| Zweck | Erstellung des Stundenplans, Vertretungsplanung, Raum-, Aufsichts- und Klausurplanung, Information über Planänderungen |
| Rechtsgrundlage | Art. 6 Abs. 1 lit. e DSGVO i. V. m. [Landesschulgesetz §…]; für Lehrkräfte i. V. m. [Beamten-/Beschäftigtendatenschutz §…] |
| Betroffene | Schülerinnen und Schüler, Lehrkräfte und weiteres Personal |
| Datenkategorien | Name, Klasse, Kurszuordnung, Kürzel, Unterrichtsfächer, Deputat, Arbeits- und Sperrzeiten, Abwesenheiten (Grund knapp, nur für Berechtigte) |
| Empfänger | Schulleitung, Planung, Sekretariat; Lehrkräfte und Lernende im Umfang ihrer Rolle; Monitor im Foyer (ohne Gründe) |
| Drittland | keine Übermittlung |
| Löschfrist | Abwesenheiten und Vertretungsentscheidungen [Ende des folgenden Schuljahres]; Planversionen automatisch begrenzt (`SM_KEEP_VERSIONS`); Stammdaten ausgeschiedener Personen mit Abgang (siehe Löschkonzept) |

### 2.2 Konten und Anmeldung

| Feld | Eintrag |
|---|---|
| Zweck | Zugang zur Anwendung, Rechteverwaltung, Sicherheit |
| Rechtsgrundlage | Art. 6 Abs. 1 lit. e DSGVO [i. V. m. Landesrecht] |
| Betroffene | alle Nutzerinnen und Nutzer, Eltern |
| Datenkategorien | Benutzername, Name, Rolle, Passwort-Hash (scrypt), optional E-Mail und Telefonnummer, Zwei-Faktor-Geheimnis (verschlüsselt), Sitzungen, Anmeldeversuche, Zeitpunkt der letzten Anmeldung |
| Empfänger | Administration, Schulleitung, Sekretariat (Kontenverwaltung) |
| Löschfrist | Konten Ausgeschiedener: deaktivieren bei Austritt, löschen nach [3 Monaten]; Sitzungen und Anmeldeversuche automatisch (Wartungslauf, 30 Tage) |

### 2.3 Krankmeldungen, Atteste und Anwesenheit

| Feld | Eintrag |
|---|---|
| Zweck | Nachweis und Bearbeitung von Fehlzeiten, Entschuldigungsverfahren |
| Rechtsgrundlage | Art. 6 Abs. 1 lit. e DSGVO i. V. m. [Schulpflicht-/Schulgesetz §…]; Gesundheitsdaten: Art. 9 Abs. 2 lit. [g] DSGVO i. V. m. [Landesrecht] |
| Betroffene | Schülerinnen und Schüler, Eltern (Meldende) |
| Datenkategorien | Zeitraum, Stunden, Grund und Vermerk (verschlüsselt gespeichert), Status; Atteste (Datei, Titel und Vermerk verschlüsselt) |
| Empfänger | Meldende Person, Familie, Klassenleitung, Sekretariat, Schulleitung; Fachlehrkräfte sehen nur die Abwesenheit, nicht den Grund; die technische Administration sieht Atteste nicht |
| Löschfrist | Krankmeldungen [Ende des Schuljahres + Frist für Zeugnis-Fehlzeiten]; Atteste automatisch nach `SM_STUDENT_DOCS_RETENTION_DAYS` (Standard 400 Tage) |

### 2.4 Mitteilungen, Nachrichten und Kursräume

| Feld | Eintrag |
|---|---|
| Zweck | Schulische Kommunikation, Bereitstellung von Material und Aufgaben, Rückmeldungen |
| Rechtsgrundlage | Art. 6 Abs. 1 lit. e DSGVO; für freiwillige Funktionen (E-Mail-Benachrichtigung an private Adressen) Einwilligung nach Art. 6 Abs. 1 lit. a |
| Betroffene | Schülerinnen und Schüler, Eltern, Lehrkräfte |
| Datenkategorien | Nachrichtentexte, Anhänge und Abgaben (verschlüsselt gespeichert), Absender, Empfänger, Zeitpunkt, Lesestatus, gemeldete Nachrichten |
| Empfänger | Teilnehmende der Unterhaltung; bei gemeldeten Nachrichten berechtigte Prüfpersonen nur mit Zustimmung der Betroffenen bzw. nach Regelung der Schule |
| Löschfrist | Nachrichten nach `messaging_retention_days` der Schule (Standard 365 Tage); Kursraum-Papierkorb 30 Tage; Abgaben mit dem Kurs bzw. Schuljahr [festlegen] |

### 2.5 Leistungsdokumentation (Notenbuch, Kompetenzen, Lernstand)

| Feld | Eintrag |
|---|---|
| Zweck | Dokumentation und Bewertung von Leistungen, Information über den Lernstand |
| Rechtsgrundlage | Art. 6 Abs. 1 lit. e DSGVO i. V. m. [Schulgesetz / Leistungsbewertungsvorschriften §…] |
| Betroffene | Schülerinnen und Schüler |
| Datenkategorien | Noten, Punkte, Kommentare, Kompetenzeinschätzungen |
| Empfänger | unterrichtende Lehrkräfte, Klassenleitung, Schulleitung; Lernende und Eltern nach Freigabe |
| Löschfrist | [nach Aufbewahrungsvorschrift des Landes] |

### 2.6 Technische Protokolle

| Feld | Eintrag |
|---|---|
| Zweck | Sicherheit, Nachvollziehbarkeit, Fehleranalyse |
| Rechtsgrundlage | Art. 6 Abs. 1 lit. e bzw. f DSGVO, Art. 32 DSGVO |
| Datenkategorien | Audit-Protokoll (wer hat wann was geändert), Fehlerprotokoll (ohne Passwörter und Nachrichteninhalte), Server- und Zugriffsprotokolle mit gekürzter IP-Adresse |
| Empfänger | Administration, bei Vorfällen Schulleitung und DSB |
| Löschfrist | Fehlerprotokoll 30 Tage bzw. 1000 Einträge; Audit-Protokoll [1 Jahr]; Server-Logs [höchstens 14 Tage] |

## 3. Empfänger und Auftragsverarbeiter

| Stelle | Aufgabe | AV-Vertrag vom |
|---|---|---|
| [Hoster / Rechenzentrum] | Server, Speicher | [Datum] |
| [IT-Dienstleister] | Administration | [Datum] |
| [E-Mail-Anbieter] | Versand von Benachrichtigungen | [Datum] |
| [Backup-Speicher] | verschlüsselte Offsite-Sicherung | [Datum] |
| [SSO-Anbieter, falls genutzt] | Anmeldung | [Datum] |

## 4. Technische und organisatorische Maßnahmen

Siehe [`toms.md`](toms.md).

## 5. Datenschutz-Folgenabschätzung

Schwellwertanalyse durchgeführt am [Datum]; Ergebnis: [DSFA erforderlich / nicht erforderlich, Begründung]. Siehe [`README.md`](README.md).

## 6. Änderungsverlauf

| Datum | Änderung | Bearbeitet von |
|---|---|---|
| [Datum] | Ersterstellung | [Name] |
