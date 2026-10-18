# Datenschutz: Löschkonzept und Auskunft

Grundlage für das Verzeichnis der Verarbeitungstätigkeiten (VVT) und die Datenschutz-Unterlagen der Schule. Die Fristen
sind Vorschläge der Software und **keine Rechtsberatung**; maßgeblich sind DSGVO, BDSG, Landesschulgesetz,
Schuldatenverordnung und Aktenordnung des Landes. Bitte mit der/dem Datenschutzbeauftragten abgleichen und in den
Einstellungen anpassen (Menü *Datenschutz*, Recht `privacy.manage`). Sicherheitsprüfung: Funde S-01, S-07, S-12.

## 1. Ablauf

1. **Austritt.** Wer nicht mehr im Planungsdokument steht (Löschen unter *Stammdaten*, Klasse löschen, Import/Wiederherstellung),
   kommt in die **Warteliste „ausgetreten“**. Das Konto wird sofort gesperrt. Steht die Person wieder im Dokument, wird der
   Eintrag automatisch entfernt und das Konto freigegeben (oder manuell *Zurücknehmen*). Ein leeres Schülerverzeichnis löst
   nie eine Massen-Austragung aus.
2. **Wartezeit** (`grace_days`, Standard 30 Tage): Mindestfrist für alle Datenarten – Zeit für Korrekturen, Übertritte, Rückfragen.
3. **Fristen je Datenart** (Tabelle unten, Tage ab Austritt, mindestens die Wartezeit). Der Wartungslauf
   (`maintenance.run_maintenance`, stündlich) löscht Fälliges. Das **Konto wird zuletzt** gelöscht, erst wenn alle anderen
   Datenarten der Person bereinigt sind. Schaltet die Schule „automatisch löschen“ aus, läuft nur der Abgleich; gelöscht wird
   dann per Knopf *Fälliges jetzt löschen*.
4. **Alters-Fristen** gelten unabhängig vom Austritt für laufende Schüler/innen (Krankmeldungen, Atteste, Formulare).
5. **Löschprotokoll** (`retention_log`): Datenart, Anzahl, Zeitpunkt, Anlass, ausführendes Konto, Personen-ID – **nie Inhalte**.
   Aufbewahrung einstellbar (Standard 3 Jahre, wegen der Nachweispflicht Art. 5 Abs. 2 DSGVO und der regelmäßigen Verjährung).
6. **Vorschau** *Was würde gelöscht*: Zahlen je Person und Datenart, ohne etwas zu ändern.
7. **Planverlauf**: Die Datenart „Planverlauf und Protokoll-Bezüge“ entfernt die Person aus **allen** gespeicherten
   Planversionen (Verlauf/Rückgängig), ersetzt ihren Namen in Versionsbeschreibungen und löst Audit-Einträge von der Person
   (`student:<ID>` → `student:gelöscht`, Details leer).
8. **Sofort-Löschen (Art. 17)**: *Datenschutz → Betroffene*, nur Recht `privacy.subject` (Schulleitung). Erst Vorschau,
   dann Bestätigung durch Eintippen der ID bzw. des Benutzernamens; die Person wird aus dem Planungsdokument entfernt und alle
   Datenarten werden ohne Wartefrist gelöscht. Audit-Eintrag `privacy.erase` (ohne Inhalte), Protokoll-Modus „Sofort“.
   Das eigene Konto und Administrations-Konten sind ausgenommen.

## 2. Datenarten, Fristen und Löschweg

„Nach Austritt“ = Tage ab Austritt (mindestens Wartezeit, Standard 30 Tage). „Alter“ = laufende Löschung ohne Austritt.

| Datenart | Frist (Voreinstellung) | Rechtsgrundlage (Hinweis) | Löschweg |
|---|---|---|---|
| Krankmeldungen und Fehlzeiten (inkl. Meldungsprotokoll, Nachschreibtermine) | 30 Tage nach Austritt; Alter: 31. Juli des Schuljahres + 365 Tage | Art. 9 Abs. 2 DSGVO i. V. m. Landesschulgesetz / Schuldatenverordnung | gelöscht |
| Atteste und Dokumente (Gesundheitsdaten, samt Datei) | 30 Tage nach Austritt; Alter: 400 Tage (`SM_STUDENT_DOCS_RETENTION_DAYS`, in den Einstellungen überschreibbar) | wie oben | gelöscht |
| Förder- und Unterstützungsdaten (Nachteilsausgleich, Förderpläne) | 30 Tage nach Austritt | wie oben | gelöscht |
| Formular-Einreichungen (Beurlaubung, Einwilligung …, samt Anhänge) | 90 Tage nach Austritt; Alter: 400 Tage | wie oben | gelöscht |
| Klausurergebnisse | 180 Tage nach Austritt | Art. 6 Abs. 1 lit. e DSGVO i. V. m. Landesschulgesetz | gelöscht |
| Notenbuch (Einzel-, Halbjahres-/Zeugnisnoten, Änderungsprotokoll) | 180 Tage nach Austritt | wie Klausurergebnisse | gelöscht |
| Lernstand und Kompetenzen (Stufen, Lernpläne, Abzeichen) | 180 Tage nach Austritt | wie Klausurergebnisse | gelöscht |
| Klassenbuch-Anwesenheit | 365 Tage nach Austritt | wie Klausurergebnisse; Aufbewahrung des Klassenbuchs nach Landesrecht prüfen | anonymisiert (Vermerk der Person entfällt, Thema/Hausaufgabe bleiben) |
| Abgaben und Rückmeldungen (samt Dateien, Versionen, Bewertungen) | 90 Tage nach Austritt | Art. 6 Abs. 1 lit. e DSGVO | gelöscht |
| Selbsttests, Abstimmungen, Umfragen | 90 Tage nach Austritt | Art. 6 Abs. 1 lit. e DSGVO | gelöscht (anonym gespeicherte Antworten sind nicht zuordenbar und bleiben) |
| Fortschritt und Kursraum-Nutzung (Erledigt-Markierungen, geöffnetes Material, Gruppen) | 90 Tage nach Austritt | Art. 6 Abs. 1 lit. e DSGVO | gelöscht |
| Benachrichtigungen (an die Person und über sie, z. B. an Eltern) | 30 Tage nach Austritt | Art. 6 Abs. 1 lit. e DSGVO | gelöscht |
| Postfach-Nachrichten (eigene gesendete, Entwürfe, Teilnahmen) | 30 Tage nach Austritt | Art. 6 Abs. 1 lit. e DSGVO | gelöscht; Nachrichten anderer an die Person bleiben bei den anderen bis zur Postfach-Aufbewahrung (`messaging_retention_days`) |
| Chats (Ende-zu-Ende-verschlüsselt: Mitgliedschaften, Geräte, Schlüssel-Backup, eigene Nachrichten, Anhänge) | 30 Tage nach Austritt | Art. 6 Abs. 1 lit. e DSGVO | gelöscht; Einzelchats ganz, Gruppenchats ohne Mitglieder ebenfalls |
| Hochgeladene Dateien (Eigentümer = Konto) | 30 Tage nach Austritt | Art. 6 Abs. 1 lit. e DSGVO | gelöscht (Inhalt und Eintrag) |
| Eltern-Verknüpfungen und Freigaben (`parent_links`, `parent_access`, Einstellungen) | 30 Tage nach Austritt | Art. 6 Abs. 1 lit. e DSGVO | gelöscht; Eltern-Konten ohne weiteres Kind werden samt ihren Daten gelöscht |
| Planverlauf und Protokoll-Bezüge | 30 Tage nach Austritt | Art. 5 Abs. 1 lit. c, e DSGVO | anonymisiert (Person aus allen Planversionen entfernt) |
| Schüler-Konten (Anmeldung, Sitzungen, Tokens, Kontakt, Verknüpfungen) | zuletzt, frühestens nach allen anderen Datenarten | Art. 6 Abs. 1 lit. e DSGVO | gelöscht; Audit/Protokolle pseudonymisiert |
| Audit-Protokoll | 365 Tage (`audit_days`; Umgebungsvariable `SM_AUDIT_RETENTION_DAYS` als Vorgabe; 0 = nie) | Art. 5 Abs. 1 lit. e, Art. 32 DSGVO | gelöscht |
| Löschprotokoll und erledigte Wartelisten-Einträge | 1095 Tage (`log_days`) | Art. 5 Abs. 2 DSGVO (Nachweis) | gelöscht |
| Anmeldeversuche, Sitzungen, abgelaufene Tokens, Briefstapel, Papierkorb der Kursräume | feste Fristen der Wartung (30 Tage bzw. Ablauf) | Art. 32 DSGVO | gelöscht |

**Begründung der Voreinstellungen.** Gesundheitsdaten (Art. 9) erhalten die kürzeste Frist: Krankmeldungen laufend bis zum Ende
des Schuljahres plus ein Jahr (Zeugnisfehlzeiten, Widerspruchs- und Klagefristen), nach Austritt nur die Wartezeit. Noten und
Lernstand bleiben ein halbes Jahr, damit Einsprüche und Nachfragen nach dem Abgang möglich sind; die amtlichen Zeugnisse und
Notenlisten gehören in die Schülerakte bzw. das Schulverwaltungsprogramm und werden dort nach Aktenordnung aufbewahrt
(nicht in dieser Software). Kommunikation und Nutzungsspuren sind nach dem Austritt nicht mehr erforderlich (30–90 Tage).
Audit-Protokoll: ein Jahr genügt für die Nachvollziehbarkeit von Änderungen und Sicherheitsvorfällen und erfüllt die
Speicherbegrenzung.

**Nicht erfasst (Grenzen).** Freitexte anderer Personen, die den Namen enthalten (z. B. Mitteilungen, Vermerke von Lehrkräften),
werden nicht automatisch durchsucht. Backups enthalten gelöschte Daten bis zum Ablauf der Rotation (höchstens 12 Monate) und
werden bei einer Wiederherstellung wieder eingespielt – nach einer Wiederherstellung den Löschlauf prüfen. Chats sind
Ende-zu-Ende-verschlüsselt: gelöscht werden die Daten auf dem Server, nicht Kopien auf Geräten anderer.

## 3. Auskunft (Art. 15, 20)

* **Selbstauskunft:** `GET /api/v1/me/export` (Profil → *Daten exportieren*), optional `?format=zip`. Enthält neben Konto,
  Sitzungen, Tokens, Anmeldeversuchen und Protokoll: Krankmeldungen, Dokumente, Formulare, Postfach (Nachrichten im Klartext),
  Chats (Mitgliedschaften, Geräte, eigene Nachrichten **nur verschlüsselt** mit Hinweis), Klausurergebnisse, Notenbuch,
  Lernstand, Abgaben samt Bewertungen, Selbsttests/Umfragen, Fortschritt, Klassenbuch-Anwesenheit, Benachrichtigungen,
  Förderdaten, Dateien, Eltern-Verknüpfungen.
* **Eltern** erhalten zusätzlich die Daten ihrer Kinder, soweit `parent_access` es erlaubt (minderjährig: alles; volljährig:
  je Bereich nur mit Freigabe des Kindes; Förderdaten nur bei Minderjährigen).
* **Auskunft durch die Schule:** `GET /api/v1/privacy/export?student_id=…` oder `?user_id=…` bzw. `GET /api/v1/users/{id}/export`
  (Recht `privacy.subject`, Audit `privacy.export`) als **ZIP** mit `daten.json` und `uebersicht.html` (lesbare Übersicht).
  Die Auskunft entspricht der Sicht der Person selbst. Personen ohne Konto: Auskunft manuell aus der Schülerakte.

## 4. Neue Module anbinden

Jedes Modul mit personenbezogenen Daten ruft einmal `retention.register` auf (siehe Modul-Doku in
`schulmanager/server/retention.py`; die mitgelieferten Datenarten stehen in `retention_kinds.py`):

```python
retention.register("meine_daten", purge_fn, export_fn, label="Meine Daten", category="leistung",
                   legal="Art. 6 Abs. 1 lit. e DSGVO …", default_days=180, ids_fn=lambda db: {...})
```

`purge_fn(db, ctx)` löscht bzw. anonymisiert (`ctx.student_ids`, `ctx.user_ids`; bei `ctx.dry_run` nur zählen),
`export_fn(db, subject)` liefert die Auskunftsabschnitte. Danach erscheinen Frist, Vorschau, Warteliste, Protokoll, Sofort-Löschen
und Auskunft automatisch. Regressionstest: `tests/test_retention.py::test_new_modules_register_and_take_part`.

## 5. Rechte

`privacy.manage` (Administration, Schulleitung): Fristen, Warteliste, Vorschau, Löschlauf, Protokoll.
`privacy.subject` (nur Schulleitung): Auskunft für eine Person und Sofort-Löschen – enthält Gesundheits- und Notendaten,
daher nie die technische Administration. Beide Rechte fehlen der Rolle Zuschauer.

## Schuljahreswechsel

Der Schuljahreswechsel-Assistent (`server/year_change.py`) entfernt Abgänger aus dem Planungsdokument und sperrt ihre Konten. Der nächste Wartungslauf (`retention.sync_leavers`) nimmt sie dann automatisch in die Warteliste „ausgetreten“ auf; ab dort gelten die Fristen oben. Wird der Wechsel rückgängig gemacht, stehen sie wieder im Dokument und werden beim nächsten Abgleich aus der Warteliste entfernt.
