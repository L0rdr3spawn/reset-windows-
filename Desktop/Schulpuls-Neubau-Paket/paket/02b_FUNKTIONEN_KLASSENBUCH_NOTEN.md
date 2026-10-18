# 02b · Funktionen: Klassenbuch, Fehlzeiten, Atteste, Nachschreiben (KLB) · Noten, Kompetenzen, Klausuren (NOT)

Quellenstand: bis 2026-10-18. Gilt für den Neubau des Schulverwaltungs- und Lernsystems („das System“; der Produktname steht nur in der zentralen Konfiguration). Sprache der Oberfläche: Deutsch, Anrede „Sie“ für alle Rollen einschließlich Schülerinnen und Schüler.

---

## 0. Lesehilfe

### 0.1 Geltung und Abgrenzung

- Teil A (KLB): Klassenbuch und Anwesenheit, Fehlzeiten (Krankmeldung durch Eltern bzw. Volljährige, Beurlaubung, Entschuldigung, Attestpflicht), Meldeprotokoll, Fehlzeitenstatistik, Atteste und Schüler-Dokumente, Nachschreibtermine.
- Teil B (NOT): Klausuren und Tests (Regeln, Höchstzahlen, Sprung in den Kursraum), Notenbuch (Skalen, Berechnung, Sperre, Export), Kompetenzraster und Lernstand, Förderinformationen und Nachteilsausgleich.
- Nicht hier geregelt (nur Verweis): Stundenplan-Generator, Vertretung, Aufsichten (STP/VER); Kursräume, Aufgaben, Bewertungsraster, Lernaktivitäten (KUR); Postfach und Chats (NAC); Benachrichtigungszentrale (BEN); Formular-Baukasten (FOR); Stammdaten, Geburtsdatum-Pflege, Schuljahreswechsel (STA/SCH); Rechtekatalog und Rollenverwaltung (REC); Löschkonzept im Ganzen, Protokoll-Technik (DAT); Importformate (INT).
- Jede Anforderung hat eine feste Kennung (`KLB-nnn`, `NOT-nnn`, je Kürzel ab 001), eine Priorität (P0 Pflicht/Sicherheit/Recht · P1 Kernfunktion · P2 wichtig · P3 Wunsch), einen Status (`Status: Ist` = im Vorgängerbestand gebaut und vom Neubau mindestens zu erreichen; `Status: offen` = gewünscht oder entschieden, aber noch nicht gebaut) und genau eine Zeile `Abnahme:`.
- `[unklar: …]` kennzeichnet Werte oder Wirkungen, die die Quellen nicht eindeutig belegen; nichts wurde ergänzt. Wortlaut des Betreibers steht als Zitat in „…“ mit Datum (2026-MM-TT, ggf. Uhrzeit des Gesprächs). Spätere Entscheidungen überstimmen frühere; Überstimmungen sind vermerkt.

### 0.2 Begriffe

| Begriff | Bedeutung |
|---|---|
| Stunde | Unterrichtsstunde im Zeitraster; Standardlänge 45 min (`period_minutes`). Eine Doppelstunde zählt als zwei Stunden |
| Schultag | Unterrichtstag der Klasse, der weder Ferien noch Feiertag ist |
| Fehlzeit | Datensatz in `student_absences`: Krankmeldung, Fehlen, Beurlaubung, Verspätung oder frühes Gehen eines Kindes. Eine einzige Datenquelle speist Klassenbuch, Krankmeldungsseite, Statistik, Nachschreiben und Kalender |
| offene Fehlzeit | Fehlzeit im Status `gemeldet` oder `teilweise`, die noch nicht entschuldigt ist |
| Familie | Eltern bzw. Sorgeberechtigte (je Kind) und Personen mit Genehmigung; bei Volljährigen die Schülerin bzw. der Schüler selbst |
| volljährig | ab dem 18. Geburtstag, berechnet aus dem Geburtsdatum (Stichtag Europe/Berlin) |
| Klassenleitung | Klassenlehrkräfte einer Klasse einschließlich Stellvertretung; die Abteilungsleitung hat dieselben Rechte für die Klassen ihrer Abteilung |
| Fachlehrkraft | Lehrkraft ohne Klassenleitung der betreffenden Klasse |
| technische Administration | Rolle `admin` (Betrieb und Konfiguration). Sie sieht nie Gesundheits-, Noten-, Lernstands- oder Förderdaten |
| Halbjahr | Notenbuch-Kennung `JJJJ-1` (1. Halbjahr) bzw. `JJJJ-2`; JJJJ = Jahr des Schuljahresbeginns. Stichtag des Wechsels 1. Februar (Standard) |
| Kursteil | Parallelgruppe eines Kurses mit eigener Lehrkraft, Raum und Schülerliste; Notenbücher gehören zu Kursteilen |

### 0.3 Gemeinsame Konventionen dieser Datei

- Fremde oder unbekannte Datensätze antworten mit 404 (nicht 403); 403 nur, wenn der Datensatz sichtbar ist, aber nicht geändert werden darf, oder die Rolle das Recht grundsätzlich nicht hat. Die Oberfläche zeigt 403 als Seite im App-Rahmen mit Rückweg, nie als leere Seite.
- Notation in Abnahmezeilen: `a+b` = beide Rechte, `a|b` = eines davon; „als X“ = angemeldet als Konto der Rolle X.
- Zahlen mit Einheit: Minuten „45 min“, Prozent „5 %“, Tage „14 Tage“, Schultage „3 Schultage“.
- Zeitstempel werden in UTC gespeichert und in Europe/Berlin angezeigt.

---

# Teil A · Klassenbuch, Fehlzeiten, Atteste, Nachschreiben (KLB)

## A1. Grundlagen: Querschnitt, Datenmodell, Einstellungen

#### KLB-001 · Querschnittsregeln des Bereichs
`P0` · `Status: Ist`

- Alle Endpunkte und Ansichten dieses Teils prüfen Rolle, Zuständigkeit (Klasse, Kurs, Kind) und Freigaben serverseitig; das Frontend ist nur Komfort. Fremde Klassen, Kinder, Meldungen, Dokumente und Nachschreib-Zeilen liefern 404 und verraten ihre Existenz nicht (kein Fehlertext mit Zeitraum, Status oder „bereits vorhanden“ für Unberechtigte).
- Jede schreibende Aktion (Anlegen, Ändern, Status, Rücknahme, Upload, Prüfung, Sperre) steht im Audit-Protokoll ohne Inhalte (Person, Zeit, Aktion, Datensatz-Kennung, Zählwerte). Lesezugriffe auf Dokumente, Atteste und Förderdaten werden ebenfalls protokolliert (siehe KLB-065).
- Freitexte mit Personenbezug sind in der Datenbank nur verschlüsselt gespeichert: Gründe und Vermerke der Fehlzeit, Klassenbuch-Thema, Hausaufgabe, Anwesenheit samt Notiz, Titel und Vermerke der Dokumente, Begründungen. Verschlüsselung gebunden an Tabelle, Feld und Datensatz-Kennung (Zusatzdaten `<tabelle>.<feld>:<id>`, Präfix `SM1`); die Kennung steht vor dem Verschlüsseln fest. Ein nicht entschlüsselbarer Wert erscheint als „[nicht lesbar]“, wird protokolliert und darf nie still mit leeren Werten überschrieben werden (Speichern wird mit Konflikt abgewiesen).
- Gesundheitsdaten (Krankmeldungen mit Grund, Atteste, Förderdaten) erscheinen nie in Benachrichtigungstexten, URLs, Dateinamen, Fehlermeldungen, Protokolltexten, Push-Nachrichten oder Client-Caches über Abmeldung und Kontowechsel hinaus.
- Oberfläche: Anrede „Sie“; Erklärungen nur als Hilfe an der Beschriftung (Verweilen 2 s, Rechtsklick, Antippen), keine Erklärabsätze; Bestätigungen und Eingaben als App-Dialoge, nie als Browser-Popups; jede Ansicht „Tage × Stunden“ nutzt das eine gemeinsame Raster; Zustände sind immer mit Text oder Zeichen gekennzeichnet, nie nur durch Farbe; 390 px Breite ohne waagerechten Bildlauf der Seite.
- Abnahme: Als Eltern-Konto Meldung, Dokument und Fehlzeitenseite eines fremden Kindes per Kennung abrufen und ändern → jeweils 404 ohne Hinweis auf Existenz; Datenbankauszug zeigt für `reason`, `note`, `topic_enc`, `homework_enc`, `attendance_enc`, Dokumenttitel nur Chiffrat mit Präfix `SM1`; im gesamten Bereich tritt kein `alert/confirm/prompt` des Browsers auf; Stichprobe der Texte enthält nur „Sie“-Formen.

#### KLB-002 · Fehlzeit: Datenmodell, Arten und Status
`P1` · `Status: Ist`

- Tabelle `student_absences` (eine Fehlzeit je Zeile):

| Feld | Bedeutung / Werte |
|---|---|
| `id` | Primärschlüssel, wird nicht wiederverwendet |
| `student_id` | Schüler-Kennung (Text, max. 40 Zeichen), indiziert |
| `date_from`, `date_to` | erster und letzter Fehltag (`JJJJ-MM-TT`) |
| `periods` | Liste der betroffenen Stundennummern; leer = ganztägig (alle Stunden der Tage) |
| `kind` | Art: `krank` (krank gemeldet; Standard), `fehlt` (im Klassenbuch ohne Meldung gefehlt), `beurlaubung`, `verspaetung` (zu spät), `frueh` (früher gegangen) |
| `status` | `gemeldet` (offen; Standard), `teilweise` (telefonisch gemeldet, schriftliche Entschuldigung fehlt), `entschuldigt`, `unentschuldigt` |
| `minutes` | Minuten bei `verspaetung` bzw. `frueh` |
| `source` | Herkunft: `online` (Standard), `telefon`, `schriftlich`, `lehrkraft` |
| `reason`, `note` | Grund und Vermerk, verschlüsselt (Gesundheitsdaten) |
| `excused_by`, `excused_by_name`, `excused_at` | wer wann entschuldigt hat |
| `register_id` | Klassenbuch-Eintrag, aus dem die Fehlzeit stammt; wird beim erneuten Speichern der Stunde angepasst |
| `reported_by`, `reported_by_name` | meldende Person |
| `created_at`, `updated_at` | `updated_at` setzt die Anwendung bei jeder Änderung selbst |

- Beurlaubung: Anzeige „beantragt“ = `gemeldet`, „genehmigt“ = `entschuldigt`, „abgelehnt“ = `unentschuldigt`; in der Statistik zählt eine Beurlaubung nur, wenn genehmigt oder abgelehnt (KLB-046).
- Ein ärztliches Attest (Dokumentkategorie `attest`) ist nur an Fehlzeiten der Art `krank` zulässig; an anderen Arten wird die Angabe abgelehnt.
- Eine zurückgenommene Meldung zählt nicht mehr in Statistik, Attestpflicht und Nachschreiben; ihr Protokoll bleibt bestehen (KLB-043). [unklar: ob die Zeile technisch gelöscht oder als zurückgenommen markiert wird]
- Abnahme: Neue Krankmeldung ohne weitere Angaben → `kind=krank`, `status=gemeldet`, `source=online`; Attest-Upload an eine Fehlzeit der Art `fehlt` oder `beurlaubung` → abgelehnt (422); Beurlaubung `beantragt` zählt in der Statistik nicht, nach Genehmigung als entschuldigt, nach Ablehnung als unentschuldigt.

#### KLB-003 · Schuleinstellungen des Bereichs
`P1` · `Status: Ist` (Teile offen, ausgewiesen)

| Einstellung | Standard | Bereich / Einheit | Wirkung |
|---|---|---|---|
| `sick_note_after_days` | 3 | 0–60 Schultage; 0 = keine Attestpflicht | ab so vielen Fehltagen in Folge ist ein ärztliches Attest nötig (KLB-031). Oberfläche und Server verwenden dieselbe Obergrenze 60 |
| `period_minutes` | 45 | Minuten | Stundenlänge für versäumte Unterrichtszeit |
| `absence_limit_percent` | 0 (keine Grenze) | 0–100 % der Unterrichtszeit | zulässige Fehlzeit je Fach (Ampel, KLB-047); Beschriftung „zulässige Fehlzeit je Fach in %“ |
| `absence_limit_unexcused_percent` | 0 (keine Grenze) | 0–100 % | zulässige unentschuldigte Fehlzeit je Fach |
| Warnschwelle der Ampel | 80 | % der Grenze | ab hier „nahe dran“ |
| `subject_teacher_absence_view` | `none` | `none` · `presence` | Sicht der Fachlehrkräfte auf Meldungen (KLB-009) |
| `adult_parent_access_default` | nein | ja · nein | Elterneinsicht bei Volljährigen, bis die Person selbst freigibt (KLB-005) |
| Telefonnummer und Anrufzeiten der Schule | leer | Text | erscheinen bei der Krankmeldung und auf dem Entschuldigungsformular (KLB-028) |
| Halbjahreswechsel | 1. Februar | Monat-Tag | trennt 1. und 2. Halbjahr in Fehlzeitenstatistik (31.01./01.02.) und Notenbuch. [unklar: kein Zeugnisdatum vorhanden, Annahme der Quellen] |
| Nachweisfrist (offen) | 14 | Tage nach Rückkehr | „Nachweis überfällig“ (KLB-037) |
| Online-Meldung gilt als Entschuldigung (offen) | [unklar: Standard nicht festgelegt] | ja · nein | KLB-037 |

- Feste Konstanten (nicht einstellbar): Rückgängig-Fenster 20 s, Vorschläge Nachschreiben 28 Tage / 12 gesamt / 3 je Tag, Auswertungszeitraum der Statistik höchstens 400 Tage, Mindeststunden für „Auffälligkeit“ 3.
- Ort der Einstellungen: Seite „Einstellungen“, Abschnitt „Krankmeldungen & Atteste“ (jede Einstellung genau einmal; Speichern je Abschnitt; Fehler am Feld; Rückfrage bei ungespeicherten Änderungen).
- Abnahme: `sick_note_after_days` auf 5 → Meldung über 4 Schultage zeigt „Unterschriebene Entschuldigung reicht“, über 5 Schultage „Attest nötig“; Wert 61 → 422 mit deutschem Text am Feld; `absence_limit_percent` auf 10 → Ampel je Fach rechnet gegen 10 %.

#### KLB-004 · Volljährigkeit und Geburtsdatum
`P0` · `Status: Ist` (Benachrichtigung offen, siehe KLB-066)

- Volljährig ist, wer am Stichtag (Europe/Berlin) mindestens 18 Jahre alt ist. Das Geburtsdatum entscheidet; ein bloßes Konto-Merkmal „volljährig“ gilt nur, solange kein Geburtsdatum vorliegt. Die Rechte wechseln bei jeder Anfrage am Geburtstag automatisch, ohne Zutun. Ursache der Korrektur 2026-10-12: Ein fälschlich als volljährig markiertes Konto konnte sich als Minderjähriger krankmelden.
- Alle Wege der Kontoanlage (Klassen-Assistent, „Schüler/in hinzufügen“, fehlende Konten anlegen, Massenanlage, Import) behandeln Volljährige gleich: kein automatisches Elternkonto, Selbstmeldung möglich.
- Geburtsdatum ändern dürfen: technische Administration, Schulleitung, Sekretariat und die Klassenleitung der eigenen Klasse (Recht `students.birth_date`). Der Betreiber wünschte „dass das echte Alter von einem Schüler, von den Lehrern oder von einem Admin, also einem mit der Genehmigung, festlegen kann“ (2026-10-12 18:11); Änderung durch die Schülerin bzw. den Schüler selbst ist nicht gebaut. [unklar: ob Schüler/innen selbst ändern dürfen sollen]
- Das Geburtsdatum wird in Importen übernommen (CSV, Untis) und auf Plausibilität geprüft (INT/STA).
- Abnahme: Mit fester Uhr: Schüler/in wird am Tag X 18 → am Tag davor `POST` Krankmeldung als Schüler/in → 403 und kein Meldeknopf; am Tag X → Meldung möglich; Konto mit gesetztem Merkmal „volljährig“, aber Geburtsdatum unter 18 Jahren → weiterhin 403; Änderung des Geburtsdatums als Fachlehrkraft → 403.

#### KLB-005 · Eltern-Sicht und Freigaben (Bereich Fehlzeiten, Dokumente, Noten, Lernstand)
`P0` · `Status: Ist`

- Minderjährige: Eltern und Sorgeberechtigte sehen alles, was das Kind in diesen Bereichen sieht, und melden für das Kind. Förder- und Unterstützungsdaten sehen Eltern nur bei minderjährigen Kindern.
- Volljährige: Eltern sehen nur Bereiche, die die Person selbst freigegeben hat. Standard ohne Freigabe: keine Einsicht (Schulvorgabe `adult_parent_access_default` = nein); fehlender Eintrag = nein. Die Freigabe ist je Bereich einstellbar, jederzeit widerrufbar und wird ohne Inhalte protokolliert. Bereiche (sieben): Kanäle/Kursräume (inkl. Hausaufgaben), Krankmeldungen, Dokumente/Atteste, Stundenplan, Noten, Mitteilungen, Kompetenzen. Der Bereich „Krankmeldungen“ umfasst Ansehen (mit Gründen) und Melden.
- Zustellung von Schulinformationen: „mich / meine Eltern / beide“; Standard „nur die Person selbst“, bei Minderjährigen immer „beide“. Unter 18 sind die Schalter ausgegraut mit „ab 18“.
- Jeder Elternzugriff in diesem Teil läuft über dieselbe zentrale Freigabe-Prüfung; neue Bereiche müssen sie verwenden.
- Offen und im Bereich SCH zu klären: Freigabe „Postfach“ fehlte in der Liste (Betreiber nannte „Postfach“), ob nach Volljährigkeit „alles automatisch“ oder „nur auf Wunsch“ weitergeleitet wird, Rundschreiben an Volljährige. [unklar: Entscheidung des Betreibers]
- Abnahme: Eltern-Konto zu einem 17-Jährigen sieht Krankmeldungen, Dokumente, Noten; nach dem 18. Geburtstag liefern dieselben Abrufe ohne Freigabe 404; nach Freigabe „Krankmeldungen“ durch das Kind sind Meldungen sichtbar und Melden durch Eltern möglich, „Noten“ bleiben 404; Widerruf wirkt sofort; jede Änderung der Freigabe steht im Audit ohne Inhalt.

## A2. Rechte und Sichtbarkeit

#### KLB-006 · Rechte und Standardrollen
`P0` · `Status: Ist`

| Recht | Wirkung | Standardrollen (Datenumfang) |
|---|---|---|
| `student_absence.read` | Klassenbuch ansehen; Krankmeldungen, Fehlzeiten, Statistik lesen (Gesundheitsdaten) | Schulleitung (alle), Sekretariat (alle), Lehrkraft (eigene Klassenleitung), Abteilungsleitung (eigener Zweig), Schüler/in (nur selbst), Eltern (eigene Kinder), Schulbegleitung (zugewiesene Kinder, ohne Klassenbuch-Inhalte). Technische Administration: nie |
| `student_absence.report` | Anwesenheit und Thema im Klassenbuch eintragen; Krankmeldung und Beurlaubung erfassen | Eltern (eigene Kinder), Sekretariat (alle), Lehrkraft (eigene Stunden), Abteilungsleitung (eigener Zweig), volljährige Schüler/innen (nur selbst). Schulleitung: nicht im Standard (meldet bei Bedarf über Rechtevergabe) |
| `register.read_all` | Klassenbuch einer Klasse vollständig lesen | Schulleitung, Sekretariat, Abteilungsleitung (eigener Zweig); Klassenleitung für die eigene Klasse |
| `student_documents.read` | Atteste und Dokumente einsehen, einreichen, prüfen (Gesundheitsdaten) | Schulleitung, Sekretariat, Lehrkraft (eigene Klassenleitung), Abteilungsleitung, volljährige Schüler/innen (nur selbst, Einreichen), Eltern (Kinder). Technische Administration: nie |
| `exam.edit` | Klausur- und Testtermine eintragen; Seite „Nachschreiben“ | Lehrkraft und Abteilungsleitung (eigene Kurse), Schulleitung, Planung, Administration |
| `students.birth_date` | Geburtsdatum pflegen | Administration, Schulleitung, Sekretariat, Lehrkraft (Klassenleitung der eigenen Klasse) |

- Grundrolle Schüler/in erhält `student_absence.read` (nur selbst), `student_absence.report` und `student_documents.read` nur als volljährige Person. Mit ausdrücklich erteiltem Recht dürfen auch Minderjährige melden; die Rechteverwaltung warnt dann („Standard ist nur die Selbstmeldung volljähriger Schüler/innen“).
- Schulbegleitung hat keine Elternrechte: keine Krankmeldung, keine Atteste.
- Zuschauer/in (Ansichtskonto): Krankmeldungen und Atteste sind gesperrt (403), die Klassenbuch-Übersicht bleibt lesbar; schreibende Anfragen werden mit 403 abgewiesen („Ansichtskonto: Änderungen sind mit diesem Zugang nicht möglich.“), außer ausdrücklich erteilte Rechte.
- Abnahme: Rechte-Matrix-Test über alle Rollen × die sechs Rechte × je eine eigene und eine fremde Klasse bzw. ein eigenes und ein fremdes Kind; erwartet gemäß Tabelle (eigener Umfang 200, fremd 404, Rolle ohne Recht 403); Zuschauer-Konto ruft Krankmeldungen auf → 403, Klassenbuch-Übersicht → 200.

#### KLB-007 · Sichtbarkeitsmatrix
`P0` · `Status: Ist`

Kürzel: FL = Fachlehrkraft, KL = Klassenleitung der eigenen Klasse, Sek = Sekretariat, SL = Schulleitung, S<18 / S≥18 = Schüler/in minderjährig / volljährig, Adm = technische Administration.

| Datum | FL | KL | Sek | SL | S<18 | S≥18 | Eltern | Adm |
|---|---|---|---|---|---|---|---|---|
| Klassenbuch-Inhalt (Thema, Hausaufgabentext, Anwesenheits-Notiz) | nur eigene Stunden | alle Stunden der Klasse | lesend [unklar: Entscheidung 2026-10-12 nennt nur Lehrkräfte und Schulleitung] | alle Klassen | nein | nein | nein | nein |
| Fehlzeit mit Art, Zeitraum, Stunden, Status | nur „abwesend gemeldet“ in eigener Stunde | ja | ja | ja | eigene lesen | eigene | Kinder (Volljährige nur mit Freigabe) | nein |
| Grund und Vermerk der Meldung | nein | ja | ja | ja | [unklar] | eigene | Kinder (wie oben) | nein |
| Atteste und Dokumente | nie | ja (eigene Klasse) | ja | ja | nein | eigene | ja (Sperre je Dokument möglich) | nie |
| Attest-Status (fehlt / eingereicht / genehmigt / abgelehnt / nicht nötig) | nur zur eigenen Klausur | ja | ja | ja | eigene Zeile | eigene | Kinder | nein |
| Meldeprotokoll | nur „abwesend gemeldet“ + Uhrzeit + Kanal | volle Historie | volle Historie | volle Historie | nein | nein | nein | nein |
| Fehlzeitenübersicht und Statistik | nein | ja (inkl. Klassenübersicht) | ja | ja | lesen | ja | ja | nein |
| Beurlaubung (Antrag, Grund, Unterlagen) | 14 Tage nach Genehmigung: Name, Datum, eigene Stunden, ohne Grund | ja, entscheidet | ja, entscheidet | ja, entscheidet | nein | eigene | ja | nein |

- Das Klassenraum-Tab „Klasse“ mit Fehlzeiten und Meldungen ist nur für Lehrkräfte und Schulleitung sichtbar, nie für Schüler/innen und Eltern.
- [unklar: Quellen widersprechen sich, ob Familie das Meldeprotokoll mit Personen und Kanälen sieht. Entscheidung 2026-10-12 20:31: „Schüler, Eltern und technische Administration sehen das Protokoll nicht“; die bisherige Oberfläche zeigt Familien einen Verlauf je Meldung. Neubau: Familie sieht je eigener Meldung nur Status, Dokumentstatus und Zeitpunkte, nie Person oder Rolle der Bearbeitenden.]
- Abnahme: Je Zelle der Matrix ein automatischer Test mit Konto der Rolle: erlaubte Zellen liefern Daten im beschriebenen Umfang, nicht erlaubte 404 bzw. 403; Fachlehrkraft sieht in der Antwort weder `kind`, `reason`, `note` noch Dokumentverweise.

#### KLB-008 · Technische Administration und Ansichtskonten ohne Gesundheitsdaten
`P0` · `Status: Ist` (Audit-Sicht offen)

- Die technische Administration hat standardmäßig keines der Rechte `student_absence.read|report`, `student_documents.read`, `support.read|manage|hints`, `competency.*`, `gradebook.*`. Wird eines davon über die Rechteverwaltung erteilt, erscheint die Warnung „Gesundheits- und Personaldaten sieht die technische Administration üblicherweise nie“.
- Mindestregel der Quellen: Administratoren sehen keine ärztlichen Atteste (Entscheidung 2026-10-12). Eine spätere Linie („alle Rechte an alle Rollen vergebbar, mit Warnung“) lässt offen, ob diese Mindestregel dadurch fällt. [unklar: Betreiber-Entscheidung, ob `student_documents.read` für `admin` unabdingbar gesperrt bleibt]
- Die Dateiablage kennt keinen automatischen Administrator-Zugriff auf Atteste, Förderdokumente und Nachrichtenanhänge.
- Offen (Status: offen, Prüfbefund): Das Audit-Protokoll (`audit.read`) zeigt der Administration Einträge `student_absence.*` mit Schüler-Kennung und Zeitraum; im Neubau dürfen Protokollzeilen zu Krankmeldungen für die Administration nur Aktion und Zähler zeigen, nie Schüler-Kennung oder Zeitraum.
- Abnahme: Als Administration alle Routen der Matrix (KLB-007) aufrufen → 403 bzw. leer; Audit-Ansicht als Administration zeigt zu `student_absence.*` weder Schüler-Kennung noch Zeitraum; Rechtevergabe `student_documents.read` an Administration erzeugt die genannte Warnung.

#### KLB-009 · Fachlehrkräfte: nur „Abwesenheit“, keine Gründe, keine Atteste
`P0` · `Status: Ist`

- Korrektur 2026-10-12 (Befund der Testagenten): Fachlehrkräfte sahen Art und Grund einer Krankmeldung. Regel seitdem: In der Stunde eines gemeldeten Kindes sieht die Fachlehrkraft nur „Abwesenheit“ (bzw. „abwesend gemeldet“ mit Uhrzeit und Kanal); Art (krank/beurlaubt), Grund, Diagnose, Entschuldigungsstatus und Dokumente bleiben verborgen („Gesundheitsdaten nie an Fachlehrkräfte“).
- Schalter `subject_teacher_absence_view`: `none` (Standard) – keine Meldungslisten; `presence` – Anzeige „fehlt heute in meiner Stunde“ (Name und Stunde, ohne Status, Attest, Grund, meldende Person), berechnet über die tatsächlichen Kursteile der Lehrkraft, nicht über Klassen.
- Fachlehrkräfte dürfen Status nicht setzen, Vermerke nicht ändern und Meldungen nicht löschen (403; ohne Unterricht bei der Person 404). Sie dürfen eine Abwesenheit für die eigene Stunde melden und die eigene Meldung löschen, solange sie `gemeldet` ist.
- Der Attest-Status (fehlt / eingereicht / genehmigt / abgelehnt / nicht nötig) ist für die Lehrkraft einer Klausur im Nachschreib-Kontext sichtbar (KLB-053), nie das Dokument.
- Fehlermeldungen verraten nicht, ob für ein Kind bereits eine Meldung vorliegt (Prüfbefund: Fachlehrkraft erkannte dies über einen Konflikt-Code).
- [unklar: Nutzerwunsch 2026-10-11 „Fachlehrkräfte dürfen ‚entschuldigt‘ setzen, sehen aber keine Atteste“ steht gegen die Rechte-Matrix (Fachlehrkraft 403). Neubau: Entschuldigen nur Klassenleitung, Sekretariat, Schulleitung; Betreiber bestätigt oder erteilt ein eigenes Recht.]
- Abnahme: Als Fachlehrkraft Klassenbuch einer eigenen Stunde mit krank gemeldetem Kind → Anzeige „abwesend gemeldet“ ohne Art/Grund; `PATCH` Status → 403; Fachlehrkraft ohne Unterricht bei der Person → 404; bei `presence` zeigt „fehlt heute in meiner Stunde“ nur Name und Stunde; Antwort bei bereits bestehender Meldung gleicht der Antwort ohne Meldung.

## A3. Klassenbuch

#### KLB-010 · Seite „Klassenbuch“: Auswahl und Ansicht
`P1` · `Status: Ist`

- Route `/klassenbuch`, Menüeintrag „Klassenbuch“ (Recht `student_absence.read`). Auswahl: Klasse und Tag (Datumsnavigation: vorheriger/nächster Schultag, „Heute“, Datumsfeld). Angezeigt werden nur gehaltene Stunden laut Stundenplan einschließlich Vertretungen; Entfall, Ferien und Feiertage erscheinen als Markierung, nicht als Eintragsfeld.
- Schnellzugriff „aktuelle Stunde“: die laufende Stunde wird direkt mit Anwesenheit angezeigt. Die Startseite der Lehrkraft hat die Karte „Jetzt“ (in der 2. Stunde einer Doppelstunde die ganze Doppelstunde).
- Klassenliste: Klassen, für die das Konto Klassenbuch-Recht hat. Fachlehrkräfte sehen nur eigene Klassen und Kurse und nur eigene Stunden; Klassenleitung alle Stunden der eigenen Klasse; Schulleitung (`register.read_all`) alle Klassen. Fremde und unbekannte Klassen → 404. Schüler/innen und Eltern: kein Zugriff (403).
- Die Tagesansicht nutzt das gemeinsame Raster der Tagesansichten (kein eigenes Raster); die aktuelle Stunde ist hervorgehoben; Markierungen je Kind mit Text.
- Abnahme: Als Fachlehrkraft Klasse und Tag wählen → nur eigene Stunden mit Eintragsfeldern; fremde Klasse per Kennung → 404; als Klassenleitung alle Stunden; Feiertag gewählt → keine Eintragsfelder, Hinweis mit Feiertagsname; Schüler-Konto ruft `/klassenbuch` → 403-Seite im App-Rahmen.

#### KLB-011 · Eintrag je Stunde: Thema, Hausaufgabe, Anwesenheit
`P1` · `Status: Ist`

- Zitat: „Es fehlt noch eine Klassenbuchfunktion.“ (2026-10-11 17:55) – „Pro Stunde die Anwesenheit abhaken.“
- Je gehaltener Stunde (eindeutig je Datum, Unterrichtseinheit, Stunde, Kursteil; Tabelle `register_lessons`): Thema (Freitext), Hausaufgabe (Freitext, verknüpfbar mit einer Aufgabe des Kursraums), Anwesenheit je Kind, Zeitpunkt und Name der prüfenden Person.
- Anwesenheit je Kind: `anwesend`, `fehlt`, `zu spät` (mit Minuten, setzt zugleich „anwesend“), dazu Notiz (Freitext, verschlüsselt). Startzustand: „noch nicht eingetragen“ – die Erfassung muss aktiv erfolgen, niemand ist vorbelegt (außer Krankgemeldete, KLB-012).
- Speichern erfolgt je Stunde in einem Schritt (Thema, Hausaufgabe, Anwesenheit zusammen). Doppelklick oder Wiederholung speichern nicht doppelt.
- Datenhaltung: Thema, Hausaufgabe und Anwesenheit (JSON `{Schüler-Kennung: {status, minutes}}`) verschlüsselt (KLB-017).
- Abnahme: Neue Stunde öffnen → kein Kind vorbelegt, Status „noch nicht eingetragen“; Thema, Hausaufgabe, 3 × anwesend, 1 × zu spät (5 Min.), 1 × fehlt in einem Schritt speichern → ein Datensatz, erneutes Speichern ändert ihn; Doppelklick auf „Speichern“ → ein Datensatz.

#### KLB-012 · Klassenbuch und Fehlzeit: Vorausfüllung und offene Fehlzeit
`P1` · `Status: Ist`

- Zitat: „dass da schon drin steht, dass die krank sind und wer krank ist“ (2026-10-11): Für Kinder mit gemeldeter Abwesenheit in dieser Stunde ist der Eintrag mit „krank“ vorausgefüllt; je Kind ist „krank / nicht krank“ ankreuzbar.
- „fehlt“ und „zu spät“ legen eine Fehlzeit an oder passen die bestehende an (`kind` `fehlt` bzw. `verspaetung`, `status` `gemeldet`, `source` `lehrkraft`, `register_id` gesetzt). Erneutes Speichern derselben Stunde ändert dieselbe Fehlzeit, erzeugt kein Duplikat. Die Anwesenheits-Notiz wird verschlüsselt in die offene Fehlzeit übernommen („krank nach Hause“ u. Ä.).
- Zitat: „Alles buchen. Auch geringe Verspätung eintragbar und entschuldigungspflichtig.“ Jede Fehlstunde und jede Verspätung, auch von wenigen Minuten, ist entschuldigungspflichtig; entschuldigen dürfen nur Familie (Eltern bzw. Volljährige selbst) mit anschließender Prüfung durch die Schule (KLB-030).
- Fehlt jemand zu einer Klausur oder einem Test (Klassenbuch „fehlt“ oder Krankmeldung), entsteht eine Nachschreib-Zeile (KLB-051).
- [unklar: Verhalten, wenn eine Lehrkraft „anwesend“ einträgt, obwohl eine Krankmeldung vorliegt, und wenn „fehlt“ später auf „anwesend“ zurückgesetzt wird; die Quellen nennen nur „anlegen oder anpassen“.]
- Abnahme: Kind mit Meldung für Stunde 3 → im Klassenbuch Stunde 3 vorausgefüllt „krank“; Lehrkraft setzt anderes Kind auf „fehlt“ mit Notiz → Fehlzeit `fehlt`/`gemeldet` mit `register_id`, Notiz im Datenbankauszug nur als Chiffrat; Stunde erneut speichern → keine zweite Fehlzeit; „5 Min. zu spät“ → Fehlzeit `verspaetung` mit `minutes=5`.

#### KLB-013 · Doppelstunde im Klassenbuch
`P1` · `Status: Ist`

- Zitat: „dann müssen die nicht jede Schulstunde das eintragen, sondern quasi nur einmal eintragen und dann wird das für beide Stunden gezählt.“ (2026-10-13 14:17)
- Eine Karte „1.–2. Stunde (Doppelstunde)“: Anwesenheit, Thema und Hausaufgabe werden einmal erfasst und gelten für beide Stunden.
- „fehlt“ gilt für beide Stunden; Ausnahme-Auswahl „nur 1. Stunde“ bzw. „nur 2. Stunde“. „X Min. zu spät“ zählt in der 1. Stunde. „früher gegangen ab 2. Std.“ zählt ab der 2. Stunde.
- Alte Einträge (je Stunde einzeln erfasst) bleiben gültig; Statistik und Meldeprotokoll zählen korrekt zwei Stunden. Bei längeren Blöcken (3-Stunden-Zyklus, W-02 des Plans) gilt ein Eintrag je zusammenhängendem Block. [unklar: Blocklängen über 2 sind im Bestand nicht gebaut]
- Abnahme: Doppelstunde 3./4.: „fehlt“ → Fehlzeit mit `periods` [3, 4]; „5 Min. zu spät“ → nur Stunde 3 mit `minutes=5`; „früher gegangen ab 4. Std.“ → nur Stunde 4; „fehlt, nur 1. Stunde“ → `periods` [3]; Statistik zählt in allen Fällen die richtige Stundenzahl.

#### KLB-014 · Status „nach der Stunde gegangen“ im Klassenbuch
`P2` · `Status: offen`

- Zitat: „Status ‚nach der Stunde gegangen‘, ‚abwesend‘, ‚zu spät‘. Alles buchen.“ (2026-10-11 17:55)
- Wunsch: eigener Status je Kind und Stunde „früher gegangen“ (ab welcher Stunde bzw. nach wie vielen Minuten). Gebaut wurde stattdessen ein Notizfeld; die Fehlzeitart `frueh` existiert nur über die Krankmeldung („Ich komme früher zurück“ gehört zu `krank`) und im Klassenbuch nur als „früher gegangen ab 2. Std.“ in Doppelstunden. [unklar: Abweichung vom Wunsch, vom Betreiber zu bestätigen]
- Anforderung: Klassenbuch bietet je Kind zusätzlich „früher gegangen“ mit Stunde oder Minuten; erzeugt Fehlzeit `frueh` (entschuldigungspflichtig) und fließt mit der Restzeit in die Anwesenheit (KLB-018).
- Abnahme: Kind in Stunde 5 auf „früher gegangen nach 20 Min.“ setzen → Fehlzeit `frueh` mit `minutes=25` (versäumte Zeit), Anwesenheit der Stunde 44 %; Eintrag erscheint in Statistik unter „früher gegangen“.

#### KLB-015 · Klassenbuch-Übersicht der Klassenleitung und Handy-Ansicht
`P1` · `Status: Ist` (Handy-Vorschlag offen)

- Reiter „Klassenbuch“ auf der Klassenseite (nur Klassenleitung; ohne Klassenleitung 404): Schüler/innen untereinander, Stunden als Spalten; je Feld Haken (anwesend), Kreuz (fehlt), „zu spät“, „krank“ – mit Zeichen und Text. Zusätzlich Abschnitt „Meldungen & Verlauf“ je Kind (KLB-044). Spalten bleiben fest und gleich breit; Wochentage und Zahlen stehen nicht versetzt.
- Handy: eine Karte je Kind (Name, Anwesenheit, Notiz), „fehlt“ farbig und mit Text.
- Vorschlag (Status: offen, P3): zwei große Schalter „anwesend / fehlt“ je Kind; Notizfeld erst auf Antippen.
- Abnahme: Als Klassenleitung Reiter öffnen → Schüler × Stunden mit Zeichen und Text je Feld; als Fachlehrkraft derselben Klasse → 404; bei 390 px erscheint eine Karte je Kind ohne waagerechten Bildlauf.

#### KLB-016 · Sichtbarkeit der Klassenbuch-Inhalte
`P0` · `Status: Ist`

- Zitat: „Die Informationen zum Klassenbuch sollen nur die Lehrer sehen. Schüler, Eltern, Begleiter und so sollen das nicht sehen.“ (2026-10-12 17:18)
- Thema, Hausaufgabentext und Notizen sind nur für Lehrkräfte (Umfang laut KLB-010) und Schulleitung lesbar. Der Server liefert sie an Schüler/innen, Eltern, Schulbegleitung und Ansichtskonten gar nicht aus (nicht nur ausgeblendet). Schüler/innen und Eltern sehen im Unterricht-Bereich ausschließlich: krank / nicht da (nichts, wenn anwesend), Material vorhanden (anklickbar), verlinkte Hausaufgaben.
- Hintergrund: Klassenbuch-Leck 2026-10-12 (Schüler und Eltern sahen Inhalte im Unterricht-Tab); ein Test prüft seitdem, dass die Antwort die Felder nicht enthält.
- Abnahme: Antwort der Unterricht-Ansicht für ein Schüler- und ein Eltern-Konto enthält weder Thema, Hausaufgabentext noch Notiz (JSON-Prüfung); Ansichtskonto und Schulbegleitung ebenso; Lehrkraft derselben Stunde erhält die Felder.

#### KLB-017 · Schutz der Klassenbuch-Daten
`P0` · `Status: Ist`

- Thema, Hausaufgabe, Anwesenheit und Notizen sind verschlüsselt (KLB-001); Klassenbuch-Inhalte sind nie Teil der öffentlichen Schnittstelle oder der API-Zugänge.
- Nicht lesbare Einträge werden als „[nicht lesbar]“ angezeigt; Speichern einer Stunde mit nicht lesbaren Notizen wird mit Konflikt (409) abgewiesen, damit nichts überschrieben wird.
- Altbestand im Klartext wird mit dem CLI-Befehl `encrypt-register-notes` nachverschlüsselt (Befehl idempotent, Ausgabe nur Zählwerte).
- Fremde oder unbekannte Klassen liefern 404 (Paket „Klassenbuch absichern“ 2026-10-16: 28 Tests statt 3, u. a. Verschlüsselung der Notizen, unlesbare Einträge, fremde Klassen).
- Abnahme: Klassenbuch-Eintrag mit manipuliertem Chiffrat → Anzeige „[nicht lesbar]“ und `PUT` der Stunde → 409 ohne Datenänderung; Befehl `encrypt-register-notes` auf Testdaten mit Klartext → danach nur Chiffrate, zweiter Lauf ohne Änderung; Klasse einer anderen Schule/Abteilung → 404.

#### KLB-018 · Anwesenheit in Prozent je Stunde (Berechnung)
`P1` · `Status: Ist`

- Zitat: „fehlt = 0 %, anwesend = 100 %“ – ausdrücklich pro Stunde, nicht als Tages- oder Durchschnittswert (2026-10-13 14:17); die Prozent-Anzeige über den Gesamtzeitraum „ist falsch“.

| Fall (Stunde zu 45 min) | Anwesenheit der Stunde |
|---|---|
| anwesend | 100 % |
| gefehlt, krank gemeldet | 0 % |
| ganze Stunde gefehlt | 0 % |
| m Minuten zu spät | (45 − m) / 45, auf ganze % gerundet (5 Min. → 89 %) |
| früher gegangen, r Minuten Restzeit | r / 45 |

- Anzeige „89 % – 5 Min. zu spät, offen“; Farbe grün (100 %), gelb (Teil), rot (0 %) jeweils mit Text; Tooltip mit Aufschlüsselung. Fehlzeit = Anteil versäumter Unterrichtszeit in Prozent, nicht „x von y“.
- Abnahme: Stunde mit 5 Min. zu spät → „89 %“; 12 Min. Rest bei früherem Gehen → „27 %“; krank gemeldet → „0 %“; Tooltip nennt Minuten und Status (offen/entschuldigt).

#### KLB-019 · Anwesenheitsansichten (Woche je Stunde, Durchschnitt im Zeitraum)
`P1` · `Status: Ist`

- Ort: Abschnitt „Statistik“ der Seite „Krankmeldungen“ (Schüler/Eltern) und Klassenübersicht der Klassenleitung.
- Standardansicht „Woche (je Stunde)“: Kalenderwochen-Auswahl (zurück, vor, „Diese Woche“); Raster Tage × Stunden mit Datum und Uhrzeit im gemeinsamen Raster; jedes Kästchen zeigt Fach und Anwesenheit in %; Details per Tipp; Ferien, Entfall und kommende Stunden sind markiert. Begriff einheitlich „Anwesenheit“.
- Zweite Ansicht „Durchschnitt im Zeitraum“: Raster Wochentag × Stunde als echte Tabelle mit festen, gleich breiten Spalten und links fixierter Stundenspalte; je Kasten Prozent versäumter Unterrichtszeit, farbig nach Stufe mit Text; Tooltip z. B. „3 von 6 Stunden betroffen · 45 Min. versäumt (2× zu spät, 1× gefehlt)“, entschuldigt und unentschuldigt getrennt; Wochenende nur bei Unterricht; leere Kästen grau. Nenner einer Zelle = Zahl der Wochen mit dieser Stunde im Zeitraum.
- Zitat: „eins von sieben und es sind nur sechs Stunden … da sollte dann stehen wie viel Prozent der Stunde man fehlt“ (2026-10-12 20:32). Hintergrund: „1 von 7“ bezog sich auf sieben Montage, kein Zählfehler; Anzeige trotzdem auf Prozent umgestellt.
- Abnahme: Woche mit 1 Stunde „5 Min. zu spät“ → Kästchen „89 %“, Wochenwechsel zeigt Vorwoche; Durchschnittsansicht bei 3 betroffenen von 6 Stunden zeigt Prozent versäumter Zeit statt „3 von 6“ als Hauptwert; Spalten bleiben bei 390 px gleich breit und im eigenen Rahmen waagerecht scrollbar.

#### KLB-020 · Unterricht-Ansicht für Schüler/innen und Eltern
`P2` · `Status: Ist` (Teil [unklar])

- Farben je Tag/Stunde: grün = anwesend, orange = früher gegangen oder zu spät, rot = gefehlt (auch bei Krankmeldung); rot und orange sind klickbar (Zeitraum und Status). Zusätzlich immer Text oder Zeichen. Schüler/Eltern sehen nur „krank / nicht da“; bei „nicht krank“ wird nichts eingetragen.
- [unklar: Konflikt – Betreiber 2026-10-12 15:35 wollte Orange für „zu spät/früher gegangen“; Entscheidung 17:18 „zu spät oder früher gegangen zählt im Kursraum nicht als Fehlen, bleibt aber im Klassenbuch“. Neubau: Orange bleibt in der Unterricht-Ansicht sichtbar, ohne als „Fehlen“ zu zählen.]
- Abnahme: Kind mit „zu spät“ → Tag orange mit Text „zu spät“; „gefehlt“ → rot; Klick öffnet Detail ohne Klassenbuch-Inhalte; anwesendes Kind → grün ohne Zusatzeintrag.

#### KLB-021 · Kalender-Markierung von Krankmeldung und Verspätung
`P2` · `Status: Ist`

- Im Kalender und Wochenplan erscheinen Tage mit Krankmeldung oder Zuspätkommen unten rechts in Rot mit „für den Tag krank gemeldet“; bei unter 18-Jährigen zusätzlich der Hinweis, dass die Elternmeldung noch fehlt. Stunden tragen das Abzeichen „Abwesenheit“. Für Eltern ist das richtige Kind vorausgewählt (Krankensymbol im Eltern-Plan).
- Abnahme: Meldung für Mittwoch → Mittwoch im Wochenplan mit Text „für den Tag krank gemeldet“ unten rechts; Schüler-Konto unter 18 mit Klassenbuch-„fehlt“ ohne Elternmeldung → Zusatzhinweis „Elternmeldung fehlt“.

## A4. Krankmeldung

#### KLB-022 · Wer melden darf
`P0` · `Status: Ist`

- Zitat: „alles nur von Schülern über 18 oder von Eltern, also gesetzlich Berechtigten oder die, die dazu noch die Genehmigung haben, durchführbar gemacht.“ (2026-10-12 19:08)
- Melden dürfen: Eltern bzw. Sorgeberechtigte für ihre Kinder; volljährige Schüler/innen für sich selbst; Personen mit Genehmigung; Sekretariat (auch telefonisch eingehende Meldungen); Lehrkräfte für die eigene Stunde; Klassenleitung. Schulleitung nur mit erteiltem Recht. Gilt für Krankmeldung, Beurlaubung und Dokumente.
- Minderjährige melden nicht selbst (Entscheidung 2026-10-11 18:27: „unter 18 nur über Eltern“; die zwischenzeitliche Umsetzung 17:59 „alle Schüler dürfen sich selbst krankmelden“ wurde zurückgenommen). Das Geburtsdatum entscheidet (KLB-004).
- Abnahme: Als Schüler/in 17 Jahre `POST` Krankmeldung → 403; als Eltern-Konto desselben Kindes → 201; als volljähriges Kind → 201; als Eltern eines Volljährigen ohne Freigabe → 404; als Fachlehrkraft für ein Kind außerhalb der eigenen Stunden → 403.

#### KLB-023 · Minderjährige: keine Meldefunktion, Hinweis nur im Krankmeldungsbereich
`P0` · `Status: Ist` (Hinweis-Text [unklar])

- Zitate: „Der Hinweis für unter 18-Jährige … dass der keine Krankmeldungen machen darf, weil er kein Erziehungsberechtigter oder über 18 ist“ – nur im Krankmeldungsbereich (2026-10-11 20:20); „Sollte Ansichten sind komplett unnötig für die Kinder, das sollen alles die Eltern regeln, wenn die Kinder dazu noch nicht berechtigt sind.“ (2026-10-12 19:08); „musst du Minderjährigen nicht anzeigen“ (18:11).
- Für Minderjährige gibt es keinen Krank-melden-Knopf, keine Beurlaubung, keinen Upload und keinen Infokasten auf der Startseite. Erreicht eine minderjährige Person den Krankmeldungsbereich, steht dort nur der Hinweis „Das machen Ihre Erziehungsberechtigten über ihr Eltern-Konto.“
- Lesen bleibt: „Meine Fehlzeiten“ (nur lesen) und die Statistik. [unklar: Widerspruch – Betreiber 18:11 wollte eine Fehlzeiten-Übersicht für Schüler, 19:08 nannte Ansichten für Kinder „komplett unnötig“; umgesetzt blieb das Lesen. Entscheidung des Betreibers offen.]
- Der Server lehnt Melde-, Beurlaubungs- und Upload-Anfragen von Minderjährigen unabhängig vom Frontend ab (403).
- Abnahme: Als Schüler-Konto 16 Jahre → Startseite und Menü ohne Krank-melden-Knopf und ohne Infokasten, `/krankmeldungen` zeigt nur den Hinweistext und die Lese-Ansichten; direkter `POST` auf Meldung, Beurlaubung und Dokument → 403.

#### KLB-024 · Melden: heute, mehrere Tage, später, einzelne Stunden
`P1` · `Status: Ist`

- Zitat: „für heute krankmelden und dann … von bis … die und die Tage“; „in der Zukunft krank zu melden“ (2026-10-12 19:08). Optional einzelne Stunden.
- Großer Knopf „Für heute krank melden“ mit Bestätigung im Knopf (zweiter Klick bzw. Bestätigungs-Zustand, kein Browser-Popup). „Mehrere Tage / später“: Zeitraum von–bis, auch künftige Tage, optional Auswahl einzelner Stunden.
- Vorschau vor dem Absenden (betroffene Schultage, Anzahl, Attest-Hinweis, Klausur im Zeitraum, siehe KLB-031).
- Meldungen nur für Tage mit Unterricht der Klasse; Wochenende und Ferien werden mit verständlicher Meldung abgelehnt. Überlappt eine neue Meldung eine bestehende derselben Person, wird zusammengeführt (Protokollereignis `zusammengefuehrt`) oder verständlich abgelehnt.
- Rückdatierung: Familie bis zu einer begrenzten Zahl von Tagen zurück, Lehrkräfte und Büro weiter zurück; maximale Dauer einer Meldung begrenzt. [unklar: die Zahlenwerte sind in den Quellen nicht genannt; Neubau legt sie als Schuleinstellungen fest]
- Optional Grund (Freitext, verschlüsselt). Die Meldung steht sofort im Klassenbuch der betroffenen Stunden (KLB-012).
- Abnahme: „Für heute krank melden“ → Fehlzeit für heute, Tagesplan der Klasse zeigt Abwesenheit; Zeitraum Freitag–Montag → nur Freitag und Montag zählen, Wochenende nicht; Meldung für Ferientag → abgelehnt mit Text; zweite Meldung mit Überlappung → zusammengeführt, Protokoll `zusammengefuehrt`.

#### KLB-025 · Rückgängig, Zurücknehmen, Rücknahme anfragen
`P1` · `Status: Ist`

- Zitat: „Wenn man aus Versehen auf Für den Tag krank melden drückt, will ich, dass es eine Funktion gibt, das rückgängig zu machen.“ (2026-10-11 20:20); „man will sich natürlich nicht aus Versehen krank melden und dann geht man zur Schule“.
- Direkt nach „Für heute krank melden“ erscheint 20 s lang eine Rückgängig-Leiste. Danach steht „Zurücknehmen“ zur Verfügung, solange die Schule die Meldung nicht bearbeitet hat (Status noch `gemeldet`, kein Dokument geprüft). Danach nur noch „Rücknahme anfragen“ an die Klassenleitung (Ereignis `ruecknahme_angefragt`).
- Die zurückgenommene Meldung bleibt im Protokoll; Attestpflicht und Nachschreib-Bedarf passen sich automatisch an. Die Rückgängig-Leiste verdeckt keine Knöpfe (Platz unten, solange sie sichtbar ist).
- Abnahme: Meldung → Leiste 20 s; „Rückgängig“ in der Zeit → Fehlzeit entfällt; nach 21 s kein „Rückgängig“, aber „Zurücknehmen“; nachdem die Klassenleitung ein Dokument geprüft hat → nur „Rücknahme anfragen“; Protokoll enthält in allen Fällen die ursprüngliche Meldung.

#### KLB-026 · Weitere Fälle: früher zurück, verlängern, Unterlagen nachreichen
`P2` · `Status: Ist` (Verlängern nur per Test geprüft)

- Zitat: „dass man auch sagen kann, ich komme jetzt früher“; „ich würde das gerne verlängern“; „mehr Variationen“ (2026-10-12 20:34).
- „Ich komme früher zurück“ (verkürzen): „ab morgen wieder da“ oder „ab der 3. Stunde wieder da“ (Ereignis `verkuerzt`). „Verlängern“: erweitert den Zeitraum; die Oberfläche zeigt sofort „Attest nötig“, wenn dadurch die Schwelle erreicht wird (Ereignis `verlaengert`). Unterlagen nachreichen: Entschuldigung oder Attest später hochladen („Dokument später einsenden“, Zitat 2026-10-12 19:08: „eine Unterschrift, quasi ein Dokument … später einsenden … das ein fertiges Formular dazu gibt“).
- Attestpflicht, Nachschreib-Pflicht und Statistik passen sich bei Verkürzen, Verlängern und Zurücknehmen automatisch an.
- Abnahme: Meldung Mo–Mi, „ab Mittwoch 3. Stunde wieder da“ → Zeitraum bis Mittwoch 2. Stunde, Attestzustand neu berechnet; Verlängerung auf Do → Hinweis „Attest nötig“ und Zustand `erforderlich`; Browserabnahme beider Aktionen als Eltern (PC und Handy), da bisher nur durch Tests belegt.

#### KLB-027 · Seite „Krankmeldungen“: Aufbau
`P1` · `Status: Ist`

- Route `/krankmeldungen`. Eine Spalte, feste Reihenfolge: 1 Melden · 2 Offen (nur wenn etwas fehlt, jeweils mit Upload-Knopf) · 3 Bisherige Meldungen (mit „Zurücknehmen“, Fehlzeitenübersicht, Dokumente) · 4 Statistik. Zwei druckbare Formulare (Entschuldigung, Beurlaubung) am Ende. „Offen“ und „Bisherige Meldungen“ sind eine Liste (offene oben, Upload am Eintrag), Raster mit festen Tabellenspalten; nichts steht doppelt oder versetzt.
- Zitat: „Und hier ist vor allem bei den Krankmeldungen und Fehlzeiten ist komplett zu viel. Es ist doppelt, es muss da nicht hin“ (2026-10-12 19:08; Ursache: zwei Boxen mit demselben internen Schlüssel); „offene dinger und sind eigentlich das gleiche und kannst du das bitte wirklich untereinander packen“ (20:34).
- Es gibt keinen „Krank melden“-Knopf in der oberen Leiste oder auf anderen Seiten: „Der Button oben in der Ecke … soll bitte weg und einfach in das Krankmeldungsding rein.“ (2026-10-12 20:34, überstimmt die Festlegung vom selben Tag „Knopf in der oberen Leiste für alle Rollen“). Die Startseite hat nur einen Link zur Seite.
- Eltern mit mehreren Kindern wählen ein Kind (Auswahl nur sichtbar bei mehreren Kindern); die Auswahl gilt für Start, Krankmeldungen, Noten und Kursräume. Die Familie sieht die ganze Liste der Meldungen (nicht nur 14 Tage).
- Status-Abzeichen je Meldung mit Text, Attest-Spalte, Dokumentenliste mit Download, Verlauf.
- Offen (P2, Status: offen, Prüfbefund): Die gemerkte Kindauswahl gilt im Altsystem je Gerät statt je Konto; im Neubau gilt sie je Konto, wird bei Abmeldung und Kontowechsel verworfen und fällt bei einem nicht mehr zugeordneten Kind auf das erste zulässige zurück (kein Hängen in 403).
- Abnahme: Seite als Eltern-Konto (PC und 390 px) → Reihenfolge 1–4 ohne doppelte Abschnitte und ohne Zusatzknopf in der Kopfleiste; offene Meldung erscheint oben mit Upload-Knopf, abgeschlossene darunter in derselben Liste; Eltern mit zwei Kindern: Kindauswahl sichtbar, bei einem Kind unsichtbar.

#### KLB-028 · Kontaktdaten der Schule im Krankmeldungsbereich
`P2` · `Status: Ist`

- Schuleinstellungen: Telefonnummer des Sekretariats und Anrufzeiten (Zitat 2026-10-11: „Telefonnummer mit Anrufzeiten in den Einstellungen (erscheint bei Krankmeldung und auf dem Formular)“). Beide erscheinen auf der Krankmeldungsseite und auf dem Entschuldigungsformular (PDF).
- Abnahme: Einstellung „Telefon 0123, Anrufzeiten Mo–Fr 7:30–9:00“ → beide Texte stehen auf der Krankmeldungsseite und im erzeugten PDF.

#### KLB-029 · Meldekanäle und telefonische Meldung
`P1` · `Status: Ist`

- Kanal (`source` bzw. Protokollkanal): online (Eltern, volljährige Schüler), telefonisch (Sekretariat nimmt Meldung auf), schriftlich, über ein Formular, im Klassenbuch, von einer Lehrkraft erfasst, Import, automatisch (System). Das Sekretariat erfasst telefonische Meldungen mit Status `teilweise` („teilweise entschuldigt“: angerufen, schriftliche Entschuldigung fehlt noch).
- Der Kanal wird im Meldeprotokoll festgehalten (KLB-043) und in „krank gemeldet am … von … (Eltern) · telefonisch“ angezeigt.
- Abnahme: Sekretariat legt telefonisch eine Meldung an → `source=telefon`, `status=teilweise`, Protokoll mit Kanal `telefon`; Anzeige im Klassenbuch „… von … (Sekretariat) · telefonisch“.

## A5. Entschuldigung, Attest, Dokumente

#### KLB-030 · Entschuldigungsverfahren (Statuslogik)
`P0` · `Status: Ist`

- Zitat: „Krank gemeldet heißt unentschuldigt. ... der ist krank gemeldet unentschuldigt“ (2026-10-11 20:20). Eine Meldung allein ist keine Entschuldigung; Anzeige „gemeldet – noch nicht entschuldigt“ (der frühere Text „krank gemeldet“ wurde als „entschuldigt“ missverstanden).

| Ereignis | Status danach |
|---|---|
| Meldung durch Familie (online) | `gemeldet` – „gemeldet – noch nicht entschuldigt“; darunter Option „Entschuldigung einreichen“ |
| telefonische Meldung durch das Sekretariat, Schriftliches fehlt | `teilweise` – „teilweise entschuldigt“ (nur Sekretariat setzt dies) |
| Klassenbuch „fehlt“ oder „zu spät“ ohne Meldung | `gemeldet` (offene Fehlzeit, `source=lehrkraft`) |
| schriftliche Entschuldigung hochgeladen | Status unverändert; Dokument `eingegangen` („eingereicht – wird geprüft“) |
| Dokument durch die Schule „geprüft“ („genehmigt“) | `entschuldigt` automatisch, `excused_by` und `excused_at` gesetzt |
| Dokument abgelehnt (Grund Pflicht) | Status unverändert; Handlungsbedarf „neues Dokument“ |
| Schule setzt manuell | `entschuldigt` oder `unentschuldigt` |
| Beurlaubung genehmigt / abgelehnt | `entschuldigt` / `unentschuldigt` |

- Entscheiden (Status setzen, Vermerk ändern, löschen) dürfen Klassenleitung (Stellvertretung, Abteilungsleitung für ihren Zweig), Sekretariat und Schulleitung; Löschen durch Lehrkräfte nur eigener, noch `gemeldeter` Meldungen. Technische Administration nie.
- Anerkennen in einem Schritt: „Nachweis geprüft und Meldung entschuldigt“ mit Name und Zeit; Ablehnen mit Begründung (Pflicht).
- Entschuldigen müssen Familie bzw. Volljährige; die Schule prüft. Ob schon die Online-Meldung der Eltern als Entschuldigung gilt, ist eine Schuleinstellung (KLB-037).
- Abnahme: Eltern melden → Anzeige „gemeldet – noch nicht entschuldigt“, Statistik zählt „offen“; Eltern laden Entschuldigung hoch, Klassenleitung genehmigt → Status `entschuldigt`, Statistik zählt „entschuldigt“, `excused_by_name` gesetzt; Genehmigung durch Fachlehrkraft → 403; Ablehnung ohne Begründung → 422.

#### KLB-031 · Attestpflicht und Fälligkeit
`P1` · `Status: Ist`

- Zitat: „ab wieviel Tagen man einen ärztlichen Attest braucht, wenn man in Folge krank ist … die die Schule festlegen“ (2026-10-12 19:08). Einstellung `sick_note_after_days` (Standard 3 Schultage, 0–60; 0 = keine Attestpflicht).
- Zählung: nur Schultage der Klasse im Zeitraum der Krankmeldung; Ferien und unterrichtsfreie Tage zählen nicht. Pflicht, wenn die Zahl der Schultage ≥ Grenze. Fälligkeit am N-ten Schultag der Abwesenheit (N = Grenze); davor „erforderlich“, danach „fehlt“, wenn heute ≥ Fälligkeitstag.
- Anzeige bei der Meldung: „Attest nötig (ab 3 Schultagen / Klausur am …)“ oder „Unterschriebene Entschuldigung reicht“. Liegt im Zeitraum eine Klausur oder ein Test, erscheint zusätzlich eine Warnung. Ohne Attest genügt eine unterschriebene Entschuldigung.
- Zustände (Reihenfolge der Prüfung):

| Nr | Bedingung | Zustand | Anzeige (Schüler-/Elternsicht) | Handlungsbedarf |
|---|---|---|---|---|
| 1 | Attest „geprüft“ vorhanden | `geprueft` | Attest genehmigt | nein |
| 2 | Attest „eingegangen“ vorhanden | `eingereicht` | Attest eingereicht | nein |
| 3 | keine Pflicht | `nicht_noetig` | kein Attest nötig | nein |
| 4 | Attest „abgelehnt“ vorhanden | `abgelehnt` | Attest abgelehnt | ja (neues Attest) |
| 5 | fällig | `fehlt` | Attest fehlt | ja |
| 6 | noch nicht fällig | `erforderlich` | Attest erforderlich | nein |

- Handlungsbedarf („missing“) = Zustand `fehlt` oder (Pflicht und `abgelehnt`). Die Pflicht passt sich automatisch an, wenn die Meldung verlängert, verkürzt oder zurückgenommen wird. Zurückgezogene (archivierte) Dokumente zählen nicht.
- Abnahme: Schwelle 3: Meldung Mo–Mi → „Attest nötig“, Fälligkeit Mittwoch; Donnerstag ohne Dokument → `fehlt`; Meldung Mo–Di → „Unterschriebene Entschuldigung reicht“; Ferientag im Zeitraum zählt nicht; Verkürzen von Mi auf Di → Zustand wechselt auf `nicht_noetig`; Klausur am Mittwoch → Warnung bei der Meldung.

#### KLB-032 · Schüler-Dokumente: Kategorien, Status, Speicherung
`P0` · `Status: Ist`

- Zitat: „Die Dokumente sollen bitte alle gespeichert werden, wirklich alle.“ (2026-10-12 18:11). Tabelle `student_documents`:

| Feld | Bedeutung |
|---|---|
| `student_id`, `absence_id` (optional) | Kind; Verknüpfung mit einer Fehlzeit |
| `category` | `attest` (Ärztliches Attest), `entschuldigung` (Entschuldigung), `beurlaubung` (Antrag auf Beurlaubung unterschrieben), `einverstaendnis` (Einverständniserklärung), `sonstiges` (Sonstiges Dokument) |
| Titel (verschlüsselt) | freie Bezeichnung höchstens 200 Zeichen, sonst Kategoriename |
| Datei | verschlüsselte Ablage (Inhalt und Dateiname); leer = nur Papier-Attest als Vermerk |
| `status` | `eingegangen` (Anzeige „eingereicht“; Standard) → `geprueft` („genehmigt“) oder `abgelehnt` |
| Einreichende/Bearbeitende | Konto und Name, `handled_at`; Vermerk/Ablehnungsgrund verschlüsselt |
| `withdrawn_at`, `withdrawn_by_name` | archiviert (nicht gelöscht) |

- Dokumente werden nie überschrieben und nie gelöscht: Neue Fassungen erzeugen Versionen, auch abgelehnte Dokumente bleiben erhalten. „Löschen“ bedeutet Archivieren (Eintrag und Datei bleiben, erscheinen in keiner Liste). Endgültiges Entfernen nur über die Aufbewahrungsregel (KLB-063). Jeder Zugriff und jeder Download wird protokolliert (KLB-065).
- Statuswechsel nur `eingegangen` → `geprueft` | `abgelehnt`; Ablehnung nur mit Begründung. [unklar: weitere erlaubte Übergänge, z. B. erneutes Prüfen]
- Dokumentversionen als eigene Ansicht (Status: offen, P3): Altfassungen sind gespeichert, aber in der Oberfläche nicht einzeln aufrufbar.
- Abnahme: Attest hochladen, ablehnen (mit Grund), neues Attest hochladen → beide Versionen in der Datenbank, nur die neue wirksam für den Attestzustand; „Löschen“ → `withdrawn_at` gesetzt, Datei weiterhin vorhanden, nicht in Listen; Download als Berechtigter → Audit-Eintrag; Datenbankauszug zeigt Titel/Vermerk nur als Chiffrat.

#### KLB-033 · Prüfung durch die Schule: „Atteste & Dokumente“
`P1` · `Status: Ist`

- Route `/dokumente` (Recht `student_documents.read`), Menüeintrag „Dokumente“ mit Abzeichen (offene Dokumente und fehlende Atteste). Prüf-Eingang für Klassenleitung (eigene Klasse), Sekretariat, Schulleitung und Lehrkräfte mit Leitungsrolle; Dokumente sortiert nach Eingang, offene zuerst. Startseiten-Kachel „Atteste & Dokumente“: für Klassenleitungen die eigene Klasse einschließlich der heute Erkrankten.
- Zitat: Die Lehrkraft sieht das Dokument und klickt „Genehmigen“ oder „Ablehnen“ (2026-10-12 18:11). Ablehnen öffnet einen App-Dialog mit Pflicht-Begründungsfeld. Das Ergebnis wirkt auf Attestzustand und Entschuldigungsstatus (KLB-030, KLB-031) und löst eine Benachrichtigung ohne Inhalt an die einreichende Person aus.
- Schülerinnen und Schüler (volljährig) und Eltern sehen auf derselben Route ihre Dokumente, Status und können einreichen (Formular: Kategorie wählen, Datei hochladen, absenden).
- Fachlehrkräfte erreichen die Seite nicht (403).
- Abnahme: Als Klassenleitung Dokument öffnen und genehmigen → Status `geprueft`, Abzeichen sinkt um 1, Meldung `entschuldigt`; Ablehnen ohne Begründung nicht abschließbar; als Fachlehrkraft `/dokumente` → 403; als Eltern-Konto nur Dokumente des eigenen Kindes (fremdes → 404).

#### KLB-034 · Zugriffsschutz der Dokumente
`P0` · `Status: Ist`

- Atteste und Dokumente sehen: Klassenleitung (eigene Klasse), Sekretariat, Schulleitung, die Person selbst (Volljährige) und Eltern (Kinder; bei Volljährigen nur mit Freigabe „Dokumente“). Fachlehrkräfte nie, technische Administration nie, Schulbegleitung nie, Ansichtskonten nie (403). Die Schule kann einzelne Dokumente für Eltern sperren. [unklar: Kategorien, für die die Sperre gilt]
- Auskünfte und Datenexporte enthalten Dokumente nur im Umfang der Einsicht der anfragenden Person (Befund 2026-10-11: Export enthielt Atteste volljähriger Kinder für Eltern; behoben).
- Upload-Schutz: erlaubte Dateitypen und Größen nach Allowlist der Dateiablage, Inhaltsprüfung (`scan_status` `clean|unscanned|error`), keine ausführbaren Dateien; Dateien werden nie im Kontext eingeloggter Administratoren ausgeführt oder angezeigt. [unklar: konkrete Größen- und Typ-Grenzen für Atteste]
- Abnahme: Fachlehrkraft ruft Dokument per Kennung ab → 403/404 gemäß Matrix; Eltern eines Volljährigen ohne Freigabe → 404; Auskunft für Eltern eines Volljährigen enthält keine Dokumente; Upload einer ausführbaren Datei → abgelehnt.

#### KLB-035 · „Attest einreichen“ bleibt immer bedienbar (Regressionsschutz)
`P0` · `Status: Ist` (Wirksamkeit am Originalfehler unbestätigt)

- Zitat: „Wenn ich auf Attest bei der Krankenhaltung einreiche, kann ich nicht draufklicken, das geht nicht.“ (2026-10-13 15:38). Drei vermutete Ursachen wurden behoben, der Originalfehler ließ sich lokal nicht nachstellen.
- Anforderungen: Der Knopf „Einreichen“ ist im Dialog immer sichtbar und bedienbar (PC und Handy, 390 px). Der Hinweis „Bitte zuerst eine Datei hochladen“ darf Knöpfe nicht überdecken oder Antippen abfangen; sichtbar bleibt „Erst die Datei hochladen, dann einreichen“; Hinweise bei offenem Fenster erscheinen oben. Die Rückgängig-Leiste lässt unten Platz und verdeckt keine Knöpfe. Das Formular existiert pro Seite genau einmal. Ein Antippen einer Beschriftung fokussiert das zugehörige Feld.
- Offen für den Betreiber: „Attest einreichen“ auf der produktiven Domain prüfen; bei Fehler Konto und Krankmeldung nennen; ggf. Dokumentenrecht der Rolle prüfen.
- Abnahme: Automatischer Browser-Test (Touch-Emulation 390 px und PC) öffnet „Attest einreichen“, lädt eine Datei hoch, klickt „Einreichen“ → Dokument gespeichert; Test mit sichtbarer Rückgängig-Leiste: Knopf bleibt klickbar; Antippen der Beschriftung „Datei“ setzt den Fokus auf das Dateifeld.

#### KLB-036 · Formulare als PDF: Entschuldigung und Beurlaubung
`P2` · `Status: Ist`

- Zwei druckbare Formulare: Entschuldigung („Schriftliche Entschuldigung“) und „Antrag auf Beurlaubung“. Das Entschuldigungsformular lässt sich auf Wunsch vorausgefüllt erzeugen (Kind, Klasse, Zeitraum, Schule, Telefon und Anrufzeiten); Schule, Briefkopf und Produktname kommen aus der zentralen Konfiguration. Unterschriftsfeld vorhanden.
- Jedes Zeichen im Formular muss mit der PDF-Schrift darstellbar sein (Befund: Pfeil „→“ fehlte in der Schrift und wurde durch „›“ ersetzt).
- Eine vollständige PDF-Struktur (Tags) für Barrierefreiheit ist offen (Status: offen, P3; BITV).
- Abnahme: „Entschuldigung als PDF“ vorausgefüllt → alle Felder gefüllt, kein fehlendes Zeichen, Telefon und Anrufzeiten sichtbar; „Beurlaubung als PDF“ → Felder Zeitraum, Grund, Unterschrift.

#### KLB-037 · Entschuldigungsfrist, Erinnerung, Standardgrund
`P1` · `Status: offen`

- Nachweisfrist je Schule (Standard 14 Tage nach Rückkehr, einstellbar). Danach „Nachweis überfällig“ bei der Klassenleitung. Automatisch „unentschuldigt“ wird nur gesetzt, wenn die Schule es einschaltet. Erinnerung an offene Abwesenheiten und Fristen an Familie und Klassenleitung (Push/E-Mail ohne Gesundheitsdaten, KLB-066).
- Eltern-Meldung mit Standardgrund der Schule („Krankheit, durch Eltern gemeldet“), der sofort als entschuldigt gilt – wählbar durch die Schule; Schuleinstellung „Online-Meldung der Eltern gilt als Entschuldigung“. [unklar: Standardwert nicht festgelegt – Betreiber entscheidet]
- Klassenleitung, Abteilungsleitung oder Schulleitung können einzelnen Lehrkräften Einsicht in Krankmeldungen geben (Stufe „anwesend/abwesend“ oder „vollständig“, befristbar); die Klasse zeigt je Meldung „eingesehen von/am“ und „anerkannt von/am“.
- Abnahme: Frist 14 Tage: Rückkehr am Tag X ohne Nachweis → am Tag X+15 erscheint bei der Klassenleitung „Nachweis überfällig“, Status unverändert; Schalter „automatisch unentschuldigt“ ein → Status wechselt `unentschuldigt`; Schalter „Online-Meldung gilt als Entschuldigung“ ein → neue Meldung sofort `entschuldigt`.

#### KLB-038 · Entschuldigungsvorlagen je Schule oder Schulgang
`P2` · `Status: offen`

- Zitat: Die Schule legt eigene Vorlagen an, pro Schule oder Jahrgang bzw. Schulgang („IT-Klassen, Fachabi, Grundschule, Mittelstufe, Oberstufe, Maler/Lackierer, whatever“), vorausgefüllt, „nur noch unterschreiben“ (2026-10-11/12). Eltern bzw. Volljährige laden das unterschriebene Dokument hoch oder unterschreiben am Gerät.
- Umsetzung über den Formular-Baukasten (FOR) mit Zuordnung der Vorlage zu Schule, Jahrgang, Bildungsgang oder Klasse; die Auswahl erfolgt automatisch nach Klasse des Kindes.
- Abnahme: Vorlage „Fachabi“ der Klasse 12F zugeordnet → Eltern eines Kindes der Klasse 12F erhalten beim Erzeugen das Fachabi-Formular vorausgefüllt; Kind einer anderen Klasse die Schulvorlage.

#### KLB-039 · Entschuldigung vor Ort
`P3` · `Status: offen`

- Zitat: Eltern oder volljährige Schüler können die Entschuldigung vor Ort abgeben bzw. abnehmen lassen, mit vorgefertigtem Dokument (2026-10-11 20:20).
- Das Sekretariat bzw. die Klassenleitung erfasst die persönlich übergebene Entschuldigung (Kanal „schriftlich“, Dokumentkategorie `entschuldigung`, Papier-Vermerk ohne Datei möglich) und prüft sie; Protokoll mit Person und Kanal.
- Abnahme: Sekretariat erfasst übergebene Entschuldigung zu offener Meldung → Dokument `geprueft`, Meldung `entschuldigt`, Protokoll mit Kanal `schriftlich` und erfassender Rolle.

## A6. Beurlaubung

#### KLB-040 · Beurlaubungsantrag und Entscheidung
`P1` · `Status: Ist`

- Zitat: „eine Funktion, um beurlaubt zu werden, z. B. für einen Termin an einem Schultag oder in einer Stunde“ (2026-10-11 20:20); „Da soll es auch ein Formular geben … von bis und dass das auch an die Lehrer in den Klassen geht.“ (2026-10-12 19:08).
- Antragstellung durch Eltern bzw. Volljährige: Zeitraum von–bis (Tage oder einzelne Stunden), Grund (verschlüsselt), Unterlagen. Art `beurlaubung`; Status beantragt → genehmigt | abgelehnt (Ablehnung mit Begründung); kein Attest nötig. Das Formular „Antrag auf Beurlaubung“ gibt es als PDF.
- Entscheiden: Klassenlehrkraft, Sekretariat oder Schulleitung (Abteilungsleitung für Klassen ihrer Abteilung). Nach Genehmigung sehen die Fachlehrkräfte der betroffenen Stunden 14 Tage lang Name, Datum und ihre Stunden, ohne Grund. Die Klassenleitung wird bei jeder Aktion (Antrag, Rückzug, Rückgabe, Verlängerung) in der Benachrichtigungszentrale benachrichtigt (ohne Grund).
- Minderjährige: nur über Eltern. Eine genehmigte Beurlaubung gilt in Anwesenheit und Statistik als entschuldigt, eine abgelehnte als unentschuldigt.
- Abnahme: Eltern beantragen Beurlaubung Do 3.–4. Stunde → Status beantragt, Klassenlehrkraft erhält Benachrichtigung; Klassenleitung genehmigt → Fachlehrkraft der 3. Stunde sieht 14 Tage lang Name, Datum, Stunde ohne Grund; danach nicht mehr; Fachlehrkraft versucht zu genehmigen → 403; Ablehnung ohne Begründung → 422.

#### KLB-041 · Varianten nach dem Antrag
`P2` · `Status: Ist` (Verlängern und Rückgabe nur per Test geprüft)

- Antrag zurückziehen, solange offen. „Zurückgeben“ nach der Genehmigung (Klassenlehrkraft wird informiert; Ereignis `beurlaubung_zurueckgegeben`). Verlängerung anfragen (Ereignis `verlaengerung_beantragt`). Unterlagen später einreichen mit Status „Unterlagen eingereicht – wird geprüft“. Zitat: „beurlaubung zurücknehmen“; „Unterlagen nachreichen“ (2026-10-12 20:34).
- Abnahme: Genehmigte Beurlaubung → „Zurückgeben“ → Protokoll `beurlaubung_zurueckgegeben`, Stunden zählen wieder als Unterricht; Browserabnahme als Eltern (PC und Handy).

#### KLB-042 · Beurlaubung: Weiterentwicklung
`P2` · `Status: offen`

- Entscheidungsansicht für die Schulleitung: betroffene Stunden, bisherige Fehlquote des Kindes, anstehende Klassenarbeiten im Zeitraum (Daten sind vorhanden).
- Genehmigungsweg nach Dauer einstellbar (Beispiel des Backlogs: bis zwei Tage Klassenleitung, länger oder direkt vor/nach Ferien Schulleitung). [unklar: Schwellen nicht festgelegt – Betreiber entscheidet]. Bei Auszubildenden Mitzeichnung durch den Ausbildungsbetrieb, wenn eingeschaltet.
- Benachrichtigung an die Klassenlehrkraft per Postfach bei neuem Antrag und Startseiten-Kachel „offene Anträge“ (Schulleitung, Sekretariat, Klassenleitung).
- Fachbefreiungen (z. B. Sport mit Attest) mit Zeitraum, Wochentag, Fachgruppe und Grund markieren die Person in den betroffenen Stunden.
- Abnahme: Beurlaubung während einer Klassenarbeit → Entscheidungsansicht zeigt Stunden, Fehlquote in % und die Klassenarbeit; Befreiung Sport 01.–31.03. → Person im Klassenbuch der Sportstunden als „befreit“ markiert; neuer Antrag → Postfach-Nachricht und Kachelzähler +1.

## A7. Meldeprotokoll

#### KLB-043 · Meldeprotokoll: Inhalt und Unveränderlichkeit
`P0` · `Status: Ist`

- Zitate: „alle Krankmeldungen und Meldungen müssen gelockt werden“ (Diktat; gemeint: protokolliert); „Wann die krank gemeldet wurden, wie die krank gemeldet wurden, das muss auch alles buchgeführt werden im Klassenbuch.“ (2026-10-12 20:20). Der Betreiber wusste nicht, ob es gebaut war; es fehlte und wurde nachgebaut.
- Tabelle `student_absence_events`, nur anhängend; Ändern und Löschen einzelner Zeilen ist technisch ausgeschlossen. Felder: `absence_id` (ID-Verweis ohne Fremdschlüssel, bleibt nach Löschen der Meldung erhalten), `student_id`, `at` (UTC), `event`, `actor_id`, `actor_name`, `actor_role`, `channel`, `detail` (nur Zeiträume, Stunden, Status, Art, Kanal; Änderungen als „vorher → nachher“). Index (`absence_id`, `at`).
- Ereignisse: `angelegt`, `zusammengefuehrt`, `aenderung`, `zurueckgenommen`, `dokument_eingereicht`, `dokument_geprueft`, `dokument_abgelehnt`, `dokument_zurueckgezogen`, `verkuerzt`, `verlaengert`, `verlaengerung_beantragt`, `ruecknahme_angefragt`, `beurlaubung_zurueckgegeben`.
- Kanäle: `online`, `telefon`, `schriftlich`, `formular`, `klassenbuch`, `lehrkraft`, `import`, `system`.
- Rollenbezeichnungen: Eltern, Schüler/in (volljährig), Sekretariat, Schulleitung, Abteilungsleitung, Lehrkraft, Klassenleitung (bei Lehrkraft mit Klassenleitung), Administration, Planung, Schulbegleitung.
- Nie im Protokoll: Gründe, Vermerke, Diagnosen, private Notizen. Das Protokoll bleibt auch bei Rücknahme der Meldung bestehen. Altmeldungen erhalten den Startpunkt „angelegt“.
- Abnahme: Meldung anlegen, verlängern, Dokument einreichen, zurücknehmen → fünf Zeilen mit den passenden Ereignissen, Akteur, Rolle, Kanal; `UPDATE`/`DELETE` auf eine Protokollzeile durch Anwendung und Datenbank-Konto → verweigert; Datenbankauszug enthält kein Wort aus `reason`/`note`.

#### KLB-044 · Meldeprotokoll: Sichtbarkeit und Anzeigeorte
`P0` · `Status: Ist` (Familien-Sicht [unklar], siehe KLB-007)

- Stufen: Klassenleitung, Sekretariat, Schulleitung sehen die volle Historie (Person, Rolle, Kanal, jede Änderung). Fachlehrkräfte sehen nur „abwesend gemeldet“ mit Zeit und Kanal, ohne Person, Status, Grund, Dokumente. Schüler/innen, Eltern und technische Administration sehen das Protokoll nicht.
- Anzeigeorte (eine gemeinsame Datenbasis): (1) Klassenbuch je Kind und Stunde: „krank gemeldet am … von … (Eltern) · telefonisch“, bei Vollzugriff mit aufklappbarer Historie; (2) Klassenbuch-Übersicht, Abschnitt „Meldungen & Verlauf“; (3) Klassenraum-Reiter „Klasse“, Abschnitt „Fehlzeiten & Meldungen“ (letzte 30 Tage und nächste 14 Tage; nur Lehrkräfte und Schulleitung); (4) Fehlzeitenseite des Kindes mit Verlauf je Meldung und „Zurückgenommene Meldungen“.
- Zitat: Lehrkräfte sollen in den „Klassenchats“ (Begriff unklar) einsehen können, wann und wie krank gemeldet wurde; umgesetzt als Einsicht in Klassenbuch, Klassenraum-Reiter und Fehlzeitenseite. [unklar: ob der Betreiber damit die Orte (1)–(4) meinte]
- Abnahme: Meldung telefonisch erfassen → Klassenleitung sieht im Klassenbuch „krank gemeldet am … von … (Sekretariat) · telefonisch“ und aufklappbar jede Änderung; Fachlehrkraft sieht dieselbe Stelle nur als „abwesend gemeldet“ mit Uhrzeit und Kanal; Schüler-Konto → keine Protokollansicht.

#### KLB-045 · Pseudonymisierung bei Kontolöschung
`P0` · `Status: offen` (Protokollteil Ist)

- Ist: Wird ein Konto gelöscht, wird im Meldeprotokoll `actor_id` geleert und `actor_name` zu „gelöscht#<Konto-ID>“; `reported_by` der Fehlzeit wird geleert.
- Offen (Befund): Die Namensfelder `reported_by_name`, `excused_by_name`, `uploaded_by_name`, `handled_by_name`, `withdrawn_by_name` bleiben im Klartext stehen; im Neubau werden auch sie bei Kontolöschung auf „gelöscht#<Konto-ID>“ gesetzt (Konflikt mit der DSGVO-Löschung im Altsystem).
- Abnahme: Konto einer Lehrkraft, die Meldungen und Dokumente bearbeitet hat, löschen → in `student_absence_events`, `student_absences` und `student_documents` steht der Name nirgends mehr, stattdessen „gelöscht#<Konto-ID>“; Meldungen und Dokumente selbst bleiben erhalten.

## A8. Fehlzeitenstatistik

#### KLB-046 · Berechnung der Fehlzeit je Fach
`P1` · `Status: Ist`

- Zitat: „Fehlstunden je Fach in Prozent (250 Stunden, davon drei gefehlt = zehn Prozent; darin zwei Stunden Mathe = fünf Prozent, Deutsch vier Prozent)“ (sinngemäß 2026-10-12 18:11); „in welchen fächern du fehlst, in welchen fächern du wie viel fehlst, ob du fehlst, wie viele Stunden du fehlst, wie viel Prozent du fehlst, wie viel du fehlen darfst, wenn das definiert ist“ (18:17).
- Nenner: stattgefundene Stunden laut Plan bis heute. Ferien und unterrichtsfreie Tage fallen weg; Entfall und „Unterricht findet nicht statt“ zählen nicht; Vertretungen und Verlegungen zählen. Eine Doppelstunde zählt als zwei Stunden.
- Zähler: Stunden mit Fehlzeit der Arten `krank`, `fehlt` und `beurlaubung` (nur genehmigt oder abgelehnt); ohne Stundenangabe = alle Stunden des Tages. Zuordnung bei Überschneidung: entschuldigt vor offen (`gemeldet`/`teilweise`) vor unentschuldigt; eine Stunde zählt nur einmal. Verspätung und frühes Gehen werden getrennt geführt (Anzahl; Verspätung in Minuten).
- Versäumte Unterrichtszeit: volle Stunde = Stundenlänge (`period_minutes`, 45 min); Verspätung = gemeldete Minuten in der ersten betroffenen Stunde; früher gegangen = gemeldete Stunden ganz (ohne Stundenangabe: Minuten in der letzten Stunde des Tages); je Stunde höchstens die Stundenlänge. Anteil `missed_percent` = versäumte Minuten / Unterrichtsminuten der Gruppe.
- Zeitraum: Schuljahr (Standard), Halbjahr 1/2 (Grenze 31.01./01.02.) oder frei, höchstens 400 Tage. Keine Gründe und keine Vermerke in der Statistik, nur Zahlen. Nicht entschuldigte, offene und entschuldigte Stunden werden getrennt ausgewiesen.
- Abnahme: Testdaten: 10 Mathe-Stunden stattgefunden (450 min), davon 1 krank entschuldigt, 1 unentschuldigt gefehlt, 1 × 10 Min. zu spät → versäumte Zeit (45 + 45 + 10) / 450 = 22,2 % (entschuldigt 10 %, unentschuldigt 10 %, Verspätung 2,2 %); eine Ferienwoche ändert den Nenner nicht; eine abgesagte Stunde zählt nicht; eine Vertretungsstunde zählt.

#### KLB-047 · Grenzen, Ampel, „noch X Stunden“
`P1` · `Status: Ist`

- Grenzen der Schule: `absence_limit_percent` (gesamt) und `absence_limit_unexcused_percent`; 0 = keine Grenze. Zitat: „Das ist eine Option, die die Schule in allgemeinen Konfigstern in dem Admin-Ding einstellen kann.“ (2026-10-12 18:17).
- Ampel je Fach auf Basis der versäumten Zeit (nicht der Stundenzahl): `over` (überschritten) bei Anteil > Grenze; `warn` („nahe dran“) bei Anteil ≥ 80 % der Grenze; sonst `ok`. Gesamtzustand = schlechtester Zustand über alle Fächer (ok < warn < over). Mit Verspätungen schaltet die Ampel früher auf „nahe dran“ (Claude-Entscheidung 2026-10-12, vom Betreiber nicht bestätigt).
- „Noch X Stunden bis zur Grenze“: Rest in Minuten / Stundenlänge, abgerundet; bei Überschreitung negativ aufgerundet („X Std. über der Grenze“). Es gilt der kleinste Wert über die Grenzen.
- Auffälligkeit: je Fach mindestens 3 gehaltene Stunden und Fehlzeit > 0, höchster Anteil; je Zelle (Wochentag × Stunde) mindestens 3 Unterrichtsstunden im Zeitraum.
- Abnahme: Grenze 10 %, Fach mit 8 % versäumter Zeit → `warn` (80 % der Grenze), mit 11 % → `over`, mit 5 % → `ok`; Gesamtzustand = schlechtester Fach-Zustand; Grenze 0 → keine Ampel; „noch 2 Std.“ bei 90 min Rest und 45 min Stundenlänge.

#### KLB-048 · Fehlzeitenübersicht: Darstellung und Sichtbarkeit
`P1` · `Status: Ist`

- Inhalt: gehalten gegen versäumt insgesamt und je Fach in Stunden und in Prozent (Spalte „versäumte Zeit %“ einschließlich Verspätung); Raster Wochentag × Stunde mit den drei auffälligsten Stunden; Aufteilung entschuldigt / unentschuldigt / offen; zu spät und früher gegangen gesondert; Zeitraum Schuljahr, Halbjahr oder eigener Bereich; Ampel und „noch X Std.“.
- Sichtbar für Schüler/in (auch minderjährig, lesend), Eltern, Klassenleitung (zusätzlich Klassenübersicht, sortiert nach Ampel), Sekretariat, Schulleitung. Nicht für Fachlehrkräfte und nicht für die technische Administration. Es gibt kein PDF der Übersicht, nur Drucken (siehe KLB-050).
- Seite `/fehlzeiten/:schuelerId` (Recht `student_absence.read`): Fehlzeiten eines Kindes im Schuljahr mit Summen in Tagen und Stunden, entschuldigt und unentschuldigt, Verlauf je Meldung und „Zurückgenommene Meldungen“; Verlinkung aus der Schülerliste der Klassenseite; Fehlzeiten-Statistik als Reiter der Klassenseite.
- Abnahme: Als Klassenleitung Klassenübersicht → Kinder nach Ampel sortiert (`over` zuerst); als Eltern nur das eigene Kind; als Fachlehrkraft → 403; `/fehlzeiten/<fremde Kennung>` → 404.

#### KLB-049 · Beurlaubung und Statistik
`P2` · `Status: Ist`

- Eine Beurlaubung zählt in der Statistik nur, wenn sie genehmigt (als entschuldigt) oder abgelehnt (als unentschuldigt) ist; „beantragt“ zählt nicht. Zurückgegebene Beurlaubungen zählen nicht.
- Abnahme: Beurlaubung beantragt → Mathe-Fehlanteil unverändert; genehmigt → +Stunden entschuldigt; abgelehnt → +Stunden unentschuldigt.

#### KLB-050 · Auswertungen und Exporte (offen)
`P2` · `Status: offen`

- PDF der Fehlzeitenübersicht (bisher nur „Drucken“).
- Klassenübersicht mit einstellbaren Warnschwellen (die 80 % der Ampel einstellbar) und CSV-Export der Fehlzeiten je Halbjahr für Zeugnis bzw. Schulverwaltung; Listen und Berichte („länger als N Tage unentschuldigt“) mit Druck.
- Schulleitungs-Dashboard mit Fehlquoten (Vertretungslast und Klausurdichte gehören zu VER/NOT). Klassenleitung und Schulleitung sehen Stunden ohne Anwesenheitskontrolle und können erinnern (KLB-060).
- CSV-Ausgabe schützt Zellen, die mit `=`, `@`, `+` oder `-` (nicht gefolgt von einer Ziffer) beginnen, durch ein vorangestelltes Hochkomma.
- Abnahme: CSV-Export Halbjahr 1 enthält je Kind entschuldigte, unentschuldigte, offene Stunden und Verspätungen; Zelle „=1+1“ erscheint als `'=1+1`; Warnschwelle auf 70 % → Ampel wechselt bei 70 % der Grenze auf „nahe dran“.

## A9. Nachschreibtermine

#### KLB-051 · Nachschreib-Zeilen: Entstehung und Abgleich
`P1` · `Status: Ist`

- Zitat: „Wer an einem Klausurtag fehlt“ muss „ein ärztliches Attest abgeben und bekommt einen Nachschreibtermin“; „Da müssen die Lehrer, die den Test gehalten haben in dem Unterrichtsfach, müssen eine Benachrichtigung kriegen“; der Termin soll im Stundenplan stehen (2026-10-12 18:03).
- Je versäumter Klausur oder Test und Person entsteht automatisch eine Zeile (Tabelle `exam_makeups`: `exam_id`, `student_id`, `course_id`, `exam_date`, `source` `krank|fehlt`, `absence_id`, `status`, `date_id`, `attest_waived`). Voraussetzung: Fehlzeit der Art `krank` oder `fehlt`, deren Datum und Stunden die Klausur überschneiden (leere Stundenliste = ganztägig), und die Person schreibt die Klausur (Kursteil berücksichtigt).
- Der Abgleich läuft automatisch nach jeder Änderung an Fehlzeiten, nach Klausuränderungen und beim Lesen; manuell neu abgleichbar. Eine Zeile wird entfernt, wenn die Klausur gelöscht ist; ist die Fehlzeit nicht mehr zutreffend und die Zeile noch `offen`, wird sie ebenfalls entfernt. Festgelegte (`angesetzt`) und erledigte Zeilen bleiben bestehen, solange ihre Klausur besteht. Eine bestehende offene Zeile erhält bei neuer Fehlzeit deren Kennung.
- Abnahme: Klausur Dienstag 3.–4. Stunde, Kind am Dienstag krank gemeldet → Zeile `offen`, Herkunft `krank`; Meldung zurücknehmen → Zeile verschwindet; Klassenbuch „fehlt“ in der Klausurstunde → Zeile mit Herkunft `fehlt`; bereits `angesetzte` Zeile bleibt nach Rücknahme der Meldung bestehen; Klausur gelöscht → alle Zeilen weg.

#### KLB-052 · Nachschreib-Status und Attestzustand
`P1` · `Status: Ist`

- Status einer Zeile: `offen` („Termin offen“) → `angesetzt` („Termin festgelegt“) → `erledigt` („nachgeschrieben“) oder `entfallen` („entfällt“); in Verwaltungstexten der Termine `offen · erledigt · abgesagt`. Herkunft: `krank` („krank gemeldet“), `fehlt` („im Klassenbuch als gefehlt eingetragen“).
- Attestzustand (abgeleitet aus den Dokumenten der Kategorie `attest` zu den Fehlzeiten, die den Klausurtag abdecken; nicht gespeichert). Prüfreihenfolge:

| Nr | Bedingung | Zustand | Anzeige | fehlt? |
|---|---|---|---|---|
| 1 | Attest-Verzicht gesetzt | `nicht_noetig` | Attest nicht erforderlich | nein |
| 2 | mindestens ein Attest „geprüft“ | `genehmigt` | Attest genehmigt | nein |
| 3 | mindestens ein Attest „eingegangen“ | `eingereicht` | Attest eingereicht (wird geprüft) | nein |
| 4 | mindestens ein Attest „abgelehnt“ | `abgelehnt` | Attest abgelehnt – neues Attest nötig | ja |
| 5 | sonst | `fehlt` | Attest fehlt | ja |

- Der automatische Eintrag „Attest fehlt“ entsteht, sobald jemand eine Klausur versäumt; er verschwindet bei Wegfall.
- Abnahme: Zeile ohne Dokument → „Attest fehlt“; Attest hochladen → „Attest eingereicht (wird geprüft)“; Klassenleitung genehmigt → „Attest genehmigt“; Verzicht gesetzt → „Attest nicht erforderlich“ (überschreibt alles); Ablehnung → „Attest abgelehnt – neues Attest nötig“.

#### KLB-053 · Nachschreib-Zeilen: Sichtbarkeit
`P0` · `Status: Ist`

| Stufe | Wer | Sichtbar |
|---|---|---|
| voll | Klassenleitung, Sekretariat, Schulleitung | alles: Quelle der Fehlzeit, Attest verwalten, Verzicht setzen |
| Familie | Person selbst bzw. Eltern (Volljährige nur mit Freigabe) | eigene Zeile, Termin und Attest-Status |
| Lehrkraft | Lehrkraft der Klausur mit Recht `exam.edit` (nur eigene Kurse) | nur „abwesend“, Termin und Attest-Status – nie Grund oder Dokument |
| Administration | technische Administration | kein Zugriff |

- Lehrkräfte sehen in der Klausurstunde „fehlt n“ (Anzahl Kinder mit Nachschreibbedarf) und „NTA n“ (Nachteilsausgleich, ohne Diagnose, siehe NOT-007). Familien sehen „Nachschreiben“ mit Datum und dem Attest-Hinweis.
- Abnahme: Je Stufe ein Konto: Lehrkraft der Klausur sieht „abwesend“ + Termin + Attest-Status ohne Grund; fremde Lehrkraft → 404; Familie sieht nur die eigene Zeile; Administration → 403.

#### KLB-054 · Nachschreibtermin festlegen und Konfliktprüfung
`P1` · `Status: Ist`

- Die Lehrkraft, die die Klausur gestellt hat, legt Tag, Stunde(n), Dauer (Standard 1 Stunde, Beginn Stunde 0) und Raum fest, auch für mehrere Kinder gleichzeitig; ein Termin kann von mehreren Personen geteilt werden, Termine ohne Teilnehmende werden gelöscht. Ändern und Löschen des Termins möglich. Dialog „Termin festlegen“.
- Prüfung: Warnungen (Liste leer = frei) bei: Ferien/Feiertag („ist kein Schultag (<Name>)“); kein Unterrichtstag der Klasse; außerhalb des Zeitrasters (Start < 0 oder Start + Länge > Stunden je Tag); Raum durch eine Klausur, einen anderen Nachschreibtermin oder laut Stundenplan belegt; Lehrkraft schreibt zur Zeit eine andere Klausur, hat einen anderen Nachschreibtermin oder laut Stundenplan Unterricht. Ausnahme: Eigene Stunden der Lehrkraft, in denen die betroffenen Kinder ohnehin sitzen, zählen nicht als Konflikt (gemeinsames Schreiben im Unterricht). Gleiche Meldungen erscheinen nur einmal.
- Termin-Notiz ist ein Freitext und wird verschlüsselt gespeichert (im Altsystem Klartext – nicht übernehmen).
- Abnahme: Termin Samstag ohne Unterricht → Warnung „Kein Unterrichtstag der Klasse“; Termin im belegten Raum → Warnung mit Raumname; Lehrkraft mit Unterricht zur Zeit → Warnung; Termin in der eigenen Stunde mit allen betroffenen Kindern → keine Warnung; Termin mit zwei Kindern, eines wird entfernt → Termin bleibt, ohne Teilnehmende → Termin gelöscht.

#### KLB-055 · Terminvorschläge
`P1` · `Status: Ist`

- Zitat: „ich würde gerne mit den Kindern, die krank waren, den Test schreiben. Man kann das machen und dann wird das ausgewählt.“ (2026-10-12 20:23); Optionen: im eigenen Unterricht (dort sitzen die Kinder ohnehin) oder außerhalb des Unterrichts (freie Zeit).
- Im Dialog „Termin festlegen“: höchstens 12 Vorschläge, höchstens 3 je Tag, im Zeitraum von höchstens 28 Tagen ab dem Tag nach der Klausur bzw. ab morgen. Schulfrei (Ferien, Feiertag, Wochentag ohne Unterricht einer Klasse der Kinder): kein Vorschlag.
- Art „unterricht“: Stunde, die eine Lehrkraft der Klausur ohnehin hält und in der betroffene Kinder sitzen, mit Raum der Stunde; Bewertung = Nähe zu heute (Tage nach heute) − 5, wenn alle Kinder sitzen, sonst − 3. Art „frei“: Zeit, in der Lehrkraft, alle Kinder und ein Raum frei sind (Raum der Klausur hat Vorrang, sonst irgendein freier Raum); Lage „luecke“ (Freistunde der Kinder zwischen zwei Stunden, Bewertung Nähe + 0) oder „rand“ (direkt vor der ersten oder nach der letzten Stunde, Nähe + 1); ganz freie Stunden ohne Bezug zum Unterricht werden nicht vorgeschlagen.
- Sortierung: Bewertung, dann Datum, dann Startstunde; Ausgabe mit Uhrzeit. „Diesen Termin nehmen“ wendet den Vorschlag auf alle oder ausgewählte Kinder an, mit Konfliktprüfung (KLB-054). Ferien, Konflikte und Rhythmen (Wochenmuster) werden berücksichtigt.
- Abnahme: Klausur Montag, Kind krank → Vorschläge enthalten Unterrichtsstunden der Lehrkraft mit dem Kind (Art `unterricht`) vor freien Randstunden; höchstens 12 Einträge, höchstens 3 je Tag, keiner in den Ferien; „Diesen Termin nehmen“ → Zeile `angesetzt`, Familie sieht den Termin.

#### KLB-056 · Anzeige der Nachschreibtermine und Hinweise
`P1` · `Status: Ist`

- Seite `/nachschreiben` (Recht `exam.edit` oder `student_absence.read`): Liste je Klausur (Zeilen je Kind mit Attest-Abzeichen und Termintext), Dialog „Termin festlegen“. Menüpunkt „Nachschreiben“ mit Zähler offener Punkte je Rolle (Lehrkräfte: noch festzulegende Termine; Klassenleitung und Sekretariat: Übersicht), Startseiten-Kachel für die Lehrkraft der Klausur und für Familien („Nachschreib-Hinweis“ je Kind).
- Schüler/innen und Eltern sehen den Termin im Wochenkalender/Stundenplan, auf der Startseite und auf der Klausuren-Seite; der Termin erscheint als Kalendereintrag mit Abzeichen „Nachschreiben“.
- Abnahme: Termin festgelegt → Wochenplan des Kindes zeigt den Termin mit Abzeichen; Startseite der Eltern zeigt „Nachschreiben“ mit Datum und Attest-Hinweis; Menüzähler der Lehrkraft sinkt um 1; ohne Recht → Seite 403.

#### KLB-057 · Benachrichtigung der Lehrkraft beim Nachschreib-Bedarf
`P2` · `Status: offen`

- Postfach- oder E-Mail-Nachricht an die Lehrkraft der Klausur, sobald eine Nachschreib-Zeile entsteht (bisher nur Startkachel, Zähler, Live-Aktualisierung; das Postfach hatte keinen Systemabsender). Text ohne Grund und ohne Gesundheitsdaten („Für die Klausur … gibt es 1 Nachschreibbedarf“).
- Abnahme: Kind meldet sich für den Klausurtag krank → Lehrkraft erhält eine Benachrichtigung ohne Namen des Grundes; Nachricht enthält kein Wort aus Grund/Attest.

#### KLB-058 · Attest-Verzicht
`P2` · `Status: Ist`

- Die Klassenleitung oder das Sekretariat (Schulleitung) setzt je Nachschreib-Zeile den Verzicht auf das Attest (`attest_waived`, Name der verzichtenden Person gespeichert); nicht die Person selbst. Der Verzicht setzt den Attestzustand auf `nicht_noetig`.
- Abnahme: Verzicht als Sekretariat → „Attest nicht erforderlich“; als Eltern oder Fachlehrkraft → 403.

## A10. Klassenbuch-Ausbau und weitere offene Funktionen

#### KLB-059 · Klassenbuch-Ausbau
`P2` · `Status: offen`

- Freie Eintragsarten je Kind oder Klasse (vergessene Hausaufgabe, Störung, fehlendes Material, Lob, Tadel) mit Sichtbarkeit je Kategorie für Eltern; Mehrfacheinträge; Nachweis des Lehrstoffs; Berichte je Klasse, Unterricht und Schüler; Klassen-Wochenansicht; Listen (z. B. „länger als N Tage unentschuldigt“); Klassendienste (nur auf Nachfrage); Befreiungen (siehe KLB-042). Verhaltens- und Beobachtungseinträge gelten als sensibel (Rechtsgrundlage vor Bau klären).
- Zusatzrolle „Leseansicht Klassenbuch“ (nur lesen) für Personal ohne Lehrbefugnis.
- Abnahme: Eintrag „Hausaufgabe vergessen“ für ein Kind → erscheint im Klassenbuch mit Datum und Lehrkraft; Eltern sehen nur Kategorien, die die Schule für Eltern freigegeben hat; Bericht „Eintragsarten je Klasse“ druckbar.

#### KLB-060 · Schnelle Anwesenheit, Erinnerung, Offline
`P2` · `Status: offen`

- „alle da“ mit einem Klick; Ein-Klick-Anwesenheit „wie gestern“; „ist gekommen“ per Klick (Eintreffzeit); Abwesenheit auf die nächste Stunde verlängern; bei schlechtem Netz zwischengespeichert, am Handy bedienbar.
- Erinnerung an offene Klassenbuch-Stunden an die Lehrkraft per Push oder Mail (statt Liste für die Klassenleitung); Klassen- und Schulleitung sehen Stunden ohne Anwesenheitskontrolle und Quote und können erinnern (Aufwand S bis M).
- Änderungen nach Stundenende stehen im Audit.
- Abnahme: Stunde ohne Eintrag 30 min nach Ende → Lehrkraft erhält Erinnerung; „alle da“ → alle Kinder anwesend außer Krankgemeldete; Offline-Eintrag am Tablet wird nach Verbindung synchronisiert, Konflikte werden angezeigt; Änderung nach Stundenende erzeugt Audit-Eintrag.

#### KLB-061 · Klassenbuch Stufe 2: Thema, Kontrolle, Archiv
`P2` · `Status: offen`

- Thema optional aus einer Stoffverteilung; Klassenbucheintrag bzw. Bemerkung je Stunde; Vertretungen und Termine fließen automatisch ein; Druck bzw. PDF des Klassenbuchs je Woche und Halbjahr für das Archiv (Löschfrist laut Landesrecht, KLB-063).
- Abnahme: PDF der Woche enthält Stunden, Themen, Vertretungen und Termine; Stunde ohne Thema erscheint in der Kontrollliste der Klassenleitung.

#### KLB-062 · Ausbilderzugang zu Fehlzeiten
`P3` · `Status: offen`

- Rolle „Ausbilder/in“ (Berufskolleg) sieht nur die eigenen Auszubildenden: Fehlzeiten mit Stunden, Krankmeldungen ohne Grund, zeichnet Beurlaubungen mit. Ob der Zugang auch gegen den Willen volljähriger Auszubildender besteht, legt die Schule je Bildungsgang fest und nennt die Datenschutzinformation. [unklar: rechtlich zu prüfen]
- Abnahme: Ausbilder-Konto sieht Fehlzeiten eigener Auszubildender ohne Grund; fremde Auszubildende → 404.

## A11. Datenschutz, Aufbewahrung, Betrieb

#### KLB-063 · Aufbewahrung und Löschung
`P0` · `Status: Ist` (Rechtsprüfung offen)

| Datenart | Frist | Verfahren |
|---|---|---|
| Krankmeldungen und Fehlzeiten (`student_absences`, Protokoll, Nachschreib-Zeilen) | 30 Tage nach Austritt; laufend 365 Tage (abgelaufen, wenn das Enddatum vor dem letzten 31. Juli liegt, der vor „heute minus 365 Tage“ liegt) | löschen, in Blöcken zu 500 |
| Atteste und Dokumente | 30 Tage nach Austritt; laufend 400 Tage ab Erstellung (`SM_STUDENT_DOCS_RETENTION_DAYS`, 0 = aus) | Datensatz und Datei löschen, höchstens 5000 je Lauf |
| Klassenbuch-Anwesenheit | 365 Tage nach Austritt | anonymisieren: nur der Eintrag der Person entfällt, Thema und Hausaufgabe bleiben |
| Förder- und Unterstützungsdaten | 30 Tage nach Austritt | löschen samt Dateien |

- Wirksame Frist je Datenart = Maximum aus eigener Frist und Wartelisten-Frist (30 Tage); Löschprotokoll ohne Inhalte, nur Art, Anzahl, Zeitpunkt, Bezug. Dokumente werden nie manuell hart gelöscht, sondern nur archiviert (KLB-032).
- [unklar: Rechtsprüfung offen – das Backlog nennt eine NRW-Vorlage nach VO-DV I (Klassenbuch, Kursbuch, Zeugnislisten 10 Jahre; Schülerstammblatt 20 Jahre; übrige Daten 5 Jahre) mit täglichem Löschlauf und Vorschau „wird in den nächsten 30 Tagen gelöscht“, die im Widerspruch zu 365 Tagen Anonymisierung des Klassenbuchs steht. Entscheidung und Landesvorlage: DAT/REH.]
- Abnahme: Mit fester Uhr Person austreten lassen → nach 30 Tagen sind Fehlzeiten, Dokumente und Förderdaten gelöscht, Klassenbuch-Anwesenheit nach 365 Tagen anonymisiert (Thema bleibt); Löschprotokoll enthält Datenart und Anzahl, keine Namen; Sicherungen werden vom Löschlauf nicht erfasst (Rotation).

#### KLB-064 · Auskunft und Datenexport
`P0` · `Status: Ist`

- Die Auskunft nach Art. 15/20 enthält Fehlzeiten, Dokumente, Förderdaten (nur minderjährige Kinder), Noten, Kompetenzen, Klassenbuch-Anwesenheit mit Status und Minuten, jeweils im Umfang der Einsicht der anfragenden Person; Eltern erhalten Daten ihrer Kinder nur für freigegebene Bereiche (bei Volljährigen: Krankmeldungen für Anwesenheit, Noten/Lernstand je Bereich). Daten Dritter (Mitschüler, Notizen anderer) sind nicht enthalten. Freigabe-Zeilen (`parent_access`) gehören in den Export.
- Abnahme: Auskunft für Eltern eines Volljährigen ohne Freigabe enthält weder Atteste noch Fehlzeiten; mit Freigabe „Krankmeldungen“ enthält sie die Fehlzeiten, nicht die Dokumente; Auskunft enthält keine Daten von Mitschülern.

#### KLB-065 · Audit und Zugriffsprotokoll
`P0` · `Status: Ist` (Teil offen)

- Jeder Zugriff auf Förderdaten und Dokumente wird im Audit-Log protokolliert (wer, wann, welcher Datensatz); schreibende Aktionen aller Funktionen dieses Teils ebenfalls, ohne Inhalte (Gesundheitsdaten und Noten stehen nie im Audit-Text). Änderungen am Klassenbuch nach Stundenende stehen im Audit.
- Offen: Audit-Lücken des Altsystems (Datei-Upload und -Löschen, still zurückgezogener Antrag) sind im Neubau zu schließen; „schreibende Aktionen ohne Protokoll“ darf es nicht geben.
- Vier Protokolleinträge „Attest erlassen“ (nur Demo-Schüler, Protokollzeit 22:23 UTC, ohne Herkunfts-Adresse) wurden 2026-10-17 gefunden; die Herkunft ist nicht prüfbar, der Betreiber hat nicht bestätigt, sie ausgelöst zu haben. [unklar: Ursache offen; Neubau protokolliert jede Attest-Aktion mit Herkunfts-Adresse]
- Abnahme: Dokument ansehen, genehmigen, herunterladen → drei Audit-Einträge mit Konto, Zeit, Datensatz-Kennung; keine Zeile enthält Dateiname, Titel oder Grund; jede schreibende Anfrage der Funktionen dieses Teils erzeugt einen Eintrag (Testlauf über alle Routen).

#### KLB-066 · Benachrichtigungen, Push und Volljährigkeits-Hinweis
`P1` · `Status: Ist` (Postfach/E-Mail offen)

- Benachrichtigungen in diesem Bereich (Glocke): Eingang einer Meldung bei der Klassenleitung, Statusänderung, Dokument geprüft/abgelehnt, Beurlaubung genehmigt/abgelehnt, Nachschreibtermin festgelegt, Sperre des Notenbuchs. Texte ohne sensible Einzelheiten (Beispiel „Neue Krankmeldung“ statt Diagnose), ohne Namen anderer Kinder, ohne Noten. Automatische E-Mails sind als automatisch gekennzeichnet (kein Abwesenheitsnotiz-Rücklauf).
- Push-Nachrichten (PWA, offen) enthalten keine Gesundheitsdaten und keine Namen anderer Kinder („Änderung im Plan für morgen“); Krankmeldung in der eigenen Klasse für die Klassenleitung nur in dieser neutralen Form.
- Offen (Status: offen, P2): Hinweis bei Eintritt der Volljährigkeit per Postfach oder E-Mail (bisher nur In-App-Hinweis am Tag: „Sie sind jetzt volljährig …“ mit Link zu den Schaltern; Sie-Form statt „du“).
- Abnahme: Neue Krankmeldung → Klassenleitung erhält „Neue Krankmeldung“ ohne Grund; Text enthält keinen Kindernamen anderer Kinder; E-Mail trägt den Kopf `Auto-Submitted`; Volljährigkeit am Geburtstag → In-App-Hinweis mit „Sie“.

#### KLB-067 · Leistung und Verlässlichkeit
`P2` · `Status: offen`

- Die Fehlzeitenauswertung für 2500 Schüler/innen und ein Halbjahr liegt unter 1 s; Krankmeldungen und Planabrufe zwischen 7:30 und 8:00 Uhr werden zu 95 % unter 500 ms beantwortet (Lasttest 2500 Schüler/innen, 300 Lehrkräfte; Teil der Qualitätsabnahme).
- Abnahme: Lasttest mit 2500 Konten und 300 Lehrkräften: Krankmeldungen und Planabrufe 95. Perzentil < 500 ms; Statistikabfrage Halbjahr < 1 s.

#### KLB-068 · Demo- und Testdaten
`P2` · `Status: Ist`

- Demo-Konten (Schüler/in minderjährig, Schüler/in volljährig, Eltern) enthalten erfundene Daten; die Demo ist beobachtet (verstärkte Protokollierung). In der Demo sind Kompetenz-Import und -Verwaltung gesperrt; Notenbücher der Demoklassen enthalten erfundene Werte. Produktivbetrieb: Demo-Funktionen gesperrt.
- Abnahme: Im Produktionsmodus liefern Demo-Funktionen 403; Demo-Daten enthalten keine realen Personen.

---

## A12. Offene Entscheidungen (Teil A, keine Anforderungen)

| Nr | Frage | Stand der Quellen |
|---|---|---|
| E-A1 | Sollen Minderjährige „Meine Fehlzeiten“ und Statistik lesen (KLB-023)? | Betreiber 18:11 dafür, 19:08 „komplett unnötig“; Ist: lesend sichtbar |
| E-A2 | Dürfen Fachlehrkräfte „entschuldigt“ setzen (KLB-009)? | Wunsch 2026-10-11 ja, Rechte-Matrix 403 |
| E-A3 | Gilt die Online-Meldung der Eltern als Entschuldigung (KLB-037)? | kein Standardwert |
| E-A4 | Orange für „zu spät/früher gegangen“ in der Unterricht-Ansicht (KLB-020)? | Konflikt 15:35 gegen 17:18 |
| E-A5 | Schüler/in darf Geburtsdatum selbst ändern (KLB-004)? | Wunsch nannte Schüler; nicht gebaut |
| E-A6 | Backlog-Vorschlag „Krankmeldungen, die mehr als einen Tag in der Zukunft beginnen, werden auf Beurlaubung umgeleitet“ | widerspricht dem Betreiberwunsch 2026-10-12 19:08 („in der Zukunft krank zu melden“, gebaut); nicht umsetzen ohne Betreiber-Entscheidung |
| E-A7 | Familie sieht Meldeprotokoll-Details (KLB-007/044)? | Entscheidung „nicht“, Oberfläche zeigt Verlauf |
| E-A8 | Löschfrist Klassenbuch: 365 Tage Anonymisierung oder 10 Jahre (KLB-063)? | Rechtsprüfung offen |
| E-A9 | Begriff „Klassenchats“ (KLB-044) | Herkunft unklar |
| E-A10 | Sekretariat sieht Klassenbuch-Inhalte (KLB-007)? | Recht `register.read_all` vorhanden, Entscheidung nennt nur Lehrkräfte und Schulleitung |

---

# Teil B · Noten, Kompetenzen, Klausuren (NOT)

Gliederung: B1 Klausuren und Tests · B2 Notenbuch: Aufbau und Berechnung · B3 Notenbuch: Sperre, Einsicht, Rechte, Export, Datenschutz, Zeugnisse · B4 Kompetenzraster und Lernstand · B5 Förderinformationen und Nachteilsausgleich · B6 Qualität, offene Entscheidungen, Referenz-Routen.

Zusatz zu den gemeinsamen Konventionen (0.3): Noten, Punkte, Bemerkungen, Lernstände und Förderdaten gehören zu den besonders geschützten Daten: Rechte und Datenumfang werden serverseitig geprüft, Werte sind verschlüsselt gespeichert, die technische Administration hat nie Zugriff, fremde Datensätze liefern 404 (KLB-001).

## B1. Klausuren und Tests

#### NOT-001 · Klausur und Test: Grundregeln
`P1` · `Status: Ist`

- Eine Klausur ist ein Termin eines Kurses an einem Datum mit Start (Stunde; Anzeige 1-basiert), Länge (Stunden, Standard 1, mindestens 1), optional Kursteil (nur ein Teil des Kurses), Raum, Titel (Standard „Klausur“) und Art `klausur` (Klausur/Arbeit) oder `test` (angekündigter Test). Sie wird in den verknüpften Klassenkanälen (Kursräume) angezeigt.
- Klausuren finden in regulären Unterrichtsstunden des Kurses statt. Im Vertretungsplan erscheinen sie als Info-Einträge (Art „klausur“); fällt die Lehrkraft aus, wird zwingend eine Aufsicht eingeplant (VER).
- Zitat: „dass Lehrer sagen können, wir schreiben einen Test und dass das auch im Stundenplan steht, genauso wie die Hausaufgaben“ (2026-10-11 17:55). Tests und Klausuren erscheinen im Stundenplan und Kalender als Abzeichen in der Stunde („Klausur“, „Test“, Sammelzähler „Klausur 2“, „Prüfungen 2“).
- Eintragen, ändern, löschen und „prüfen“ (ohne zu speichern) darf, wer `exam.edit` hat (Lehrkräfte und Abteilungsleitung für eigene Kurse; Schulleitung, Planung, Administration alle Kurse); Lehrkräfte tragen Klausuren und Tests für ihre eigenen Kurse selbst ein.
- Lesen dürfen alle angemeldeten Rollen im Umfang ihrer Rolle: Lehrkraft ihre Kurse, Schüler/in und Eltern die Klasse und die gewählten Kursteile, Raum- und Klassenansichten. [unklar: Elterneinsicht bei Volljährigen folgt der Freigabe „Stundenplan“; ein eigener Bereich „Klausuren“ wird im Backlog erwähnt, in der Freigabeliste nicht geführt]
- Abfragen im Zeitraum nach Klasse, Lehrkraft (Kursteil mit dieser Lehrkraft), Raum, Schüler/in (Klasse plus gewählte Kursteile), Kurs oder alle; Ausgabe je Klausur: Kennung, Kurs, Datum, Wochentag, Woche (Anzeigetext), Start, Länge, Stundenbezeichnung, Beginn, Titel, Kursteil, Raum, Klassen, Fächer, Lehrkräfte, Bezeichnung; Sortierung Datum, Start, Kennung.
- Abnahme: Lehrkraft trägt für den eigenen Kurs einen Test ein → erscheint im Wochenplan der Klasse als Abzeichen „Test“; derselbe Versuch für einen fremden Kurs → 403 bzw. 404; Schüler-Konto sieht nur Klausuren der eigenen Klasse und Kursteile; Abfrage nach Raum liefert alle Klausuren des Raums sortiert nach Datum, Start, Kennung.

#### NOT-002 · Regelprüfung beim Anlegen und Ändern
`P1` · `Status: Ist`

- Eine Klausur wird mit einer Liste verständlicher Gründe abgelehnt, wenn: (1) der Kurs nicht existiert, (2) der Kursteil nicht existiert, (3) das Datum ungültig ist, (4) der Tag kein Unterrichtstag der Klassen des Kurses ist („Kein Unterrichtstag der Klasse.“; Samstag und Sonntag sind erlaubt, wenn sie Unterrichtstag einer Klasse des Kurses sind), (5) Ferien oder Feiertag („ist kein Schultag (<Name>)“), (6) außerhalb des Zeitrasters (Start < 0 oder Start + Länge > Stunden je Tag), (7) der Kurs an dem Tag in einer Stunde der Klausur laut Stundenplan keinen Unterricht hat („<Kurs> hat am <Wochentag>, <Datum> in der <n>. Stunde laut Stundenplan keinen Unterricht“; alle Stunden der Klausur werden geprüft), (8) die Klasse in der Stunde nicht da ist (Abwesenheit oder Rhythmus; Grund wird genannt), (9) die Höchstzahl je Klasse und Tag überschritten wird, (10) die Höchstzahl je Klasse und Woche überschritten wird (NOT-003), (11) der Raum durch eine andere Klausur mit überlappenden Stunden am selben Tag belegt ist („Raum <Raum> ist bereits durch Klausur <Titel> belegt“).
- Der Raum wird aus der Stunde des Kurses übernommen. Angekündigte Tests (Art `test`) werden nicht gegen die Höchstzahlen geprüft und nicht in sie eingerechnet.
- Die Oberfläche zeigt Konflikte und Regelverletzungen vor dem Speichern (Schnittstelle „prüfen“); ein Überspringen der Prüfung (`force`) ist für Klausuren ausgeschlossen.
- Abnahme: Klausur auf einen Feiertag → abgelehnt mit „ist kein Schultag (Tag der Deutschen Einheit)“; Klausur in einer Stunde ohne Unterricht des Kurses → Grund (7) mit Wochentag und Datum; Test an einem Tag, an dem die Klasse schon die Tageshöchstzahl erreicht hat → gespeichert; zweite Klausur im selben Raum, überlappende Stunde → Grund (11).

#### NOT-003 · Höchstzahlen Klassenarbeiten (Schule → Jahrgang → Klasse)
`P1` · `Status: Ist`

- Vorgabe der Schule: höchstens 3 Klausuren je Klasse und Woche (`max_exams_per_week`), höchstens 1 je Klasse und Tag (`max_exams_per_day`). Je Jahrgang (1–14) überschreibbar: je Woche 0–20, je Tag 0–5 (`exam_limits_by_grade`; leerer Wert = Schulvorgabe). Je Klasse überschreibbar (leerer Wert = Jahrgang bzw. Schule). Es gilt die erste gesetzte Angabe in der Reihenfolge Klasse → Jahrgang → Schule.
- Zitat: „Es gibt einfach Konfig, die sind klassen-based und nicht hergang-based, die müssen einfach in die Klassen-Dinger rein.“ (2026-10-12 21:08; Diktat „jahrgangs-based“). Die Klassenwerte stehen in der Klassen-Konfiguration (nicht in der allgemeinen Konfiguration), werden in der Klassenkopfzeile und auf der Klausurseite angezeigt, und die Klausurplanung nutzt sie.
- Prüfung: Zahl der anderen Klausuren derselben Klasse am selben Tag ≥ Tageshöchstzahl → abgelehnt; in derselben Woche (Montag–Sonntag) ≥ Wochenhöchstzahl → abgelehnt. Ein anderer Kursteil desselben Kurses am selben Tag zählt als dieselbe Klausur.
- Anzeige: „max. <Woche> je Woche, <Tag> je Tag (<Quelle>)“ mit Quelle „Schule“, „Jahrgang“ oder „Klasse“ (gemischt: „Woche: <Quelle>, Tag: <Quelle>“).
- Abnahme: Schule 3/1, Klasse 5a Wochenwert 2 → dritte Klausur der Woche in 5a abgelehnt mit „max. 2 je Woche, 1 je Tag (Klasse)“, in 5b erlaubt; zweite Klausur am selben Tag in 5a abgelehnt; Jahrgang 6 mit Tageswert 2 und Klasse ohne Wert → zwei Klausuren am Tag erlaubt, Quelle „Jahrgang“.

#### NOT-004 · Grenze „0“ und Halbjahresgrenze der Klassenarbeiten
`P1` · `Status: offen`

- `0` bedeutet „keine Grenze“ (Backlog B-02; Bestätigung durch den Betreiber steht aus). Das Altsystem behandelte 0 wie 1 (Fehler); der Neubau wertet 0 als „unbegrenzt“ und erklärt das in der Hilfe an der Beschriftung.
- Höchstzahlen je Halbjahr für Jahrgang, Bildungsgang, Klasse oder Kurs, optional je Fach, mit Standardwerten je Jahrgang; Vererbung wie NOT-003. Beim Eintragen prüft das System zusätzlich die Halbjahresgrenze und nennt Klasse, Halbjahr und Stand („5a, 2. Halbjahr: bereits 4 von 4 Arbeiten in Mathematik“). Die Klausurseite zeigt je Klasse und Halbjahr eine Übersicht „Fach · erlaubt · eingetragen“; die Klassenseite verlinkt dorthin. Tages- und Wochengrenzen bleiben.
- Abnahme: Wochenwert 0 → beliebig viele Klausuren pro Woche möglich; Halbjahresgrenze Mathematik 4, vier eingetragen → fünfte abgelehnt mit „bereits 4 von 4 Arbeiten in Mathematik“; Übersicht zeigt 4 erlaubt / 4 eingetragen.

#### NOT-005 · Ein Prüfweg für alle Schreibwege
`P1` · `Status: offen`

- Jeder Weg, der Klausuren anlegt oder ändert (Klausurformular, generischer Stammdatenzugriff, Importe wie Untis und JSON), durchläuft dieselbe Regelprüfung (NOT-002/003); ein zweiter Weg mit nur Formprüfung ist nicht zulässig (Prüfbefund: der generische Datenweg umging Schultag, Höchstzahlen und Kursunterricht). Neue Regeln gelten automatisch für alle Wege.
- Verweise (Stunden, Klassen, Lehrkräfte, Räume, Kanäle) werden beim Löschen von Fach, Klasse oder Raum gepflegt; Frontend-Rollenvergleiche sind nur Komfort, der Server entscheidet.
- Abnahme: Klausur auf Sonntag ohne Unterricht über den generischen Datenweg → abgelehnt wie über das Klausurformular; Untis-Import mit Klausur am Feiertag → Zeile abgelehnt mit Zeilennummer; `force`-Parameter ändert nichts.

#### NOT-006 · Klausuren-Seite und Sprung in den Kursraum
`P1` · `Status: Ist` (Elternkonto mit mehreren Kindern ungeprüft)

- Route `/klausuren`: Liste nach Tagen (Klausur- und Testtermine mit Raum, Lehrkraft); Klick auf eine Klausur öffnet Details: Raum (Raum der regulären Stunde mit „*“, sonst „Raum noch offen“), Zeit, Kanäle, Nachteilsausgleich-Hinweis (NOT-007), Links zum Kursraum und zum Wochenstundenplan. Dialog Anlegen und Ändern mit Prüfung (NOT-002).
- Zitate: „wenn ich auch im Klausuren- und Klassenarbeiten-Ding auch auf eine Klassenarbeit klicke, dass ich dann auch direkt in den Raum reinkomme“ (2026-10-11 20:20); „Ich will auch auf die Klausuren und Tests drauf klicken können und dann zu den entsprechenden Klassenräumen geleitet werden, also für die der Test ist.“ (2026-10-13 14:13).
- Ein Klick auf Klausur, Test oder Nachholblock führt in den Kursraum des Kurses bzw. der Kursgruppe – im Stundenplan, an Markierungen, auf der Klausurenseite, der Startseite und bei Nachholterminen. Im Kursraum steht oben der Hinweis „Klausur am <Wochentag, Datum>“ mit Link „Details zur Klausur“, auch nach Wechsel des Reiters; ein Knopf „Details“ zeigt Raum, Zeit und Nachteilsausgleich. Ohne Kursraumzugriff erscheint das Klausurdetail wie bisher. Eltern landen im Kursraum des richtigen Kindes.
- Offen (P3, Status: offen): Der Klausurplan im Klassen-Kursraum ist nur ein Link, keine eigene Liste.
- Abnahme: Als Schüler/in auf eine Klausur im Wochenplan klicken → Kursraum des Kurses mit Hinweis „Klausur am Donnerstag, 15. Oktober 2026“ und Link „Details zur Klausur“; Reiterwechsel hält den Hinweis; als Eltern mit zwei Kindern wird der Raum des Kindes geöffnet, dem die Klausur gehört (Browserabnahme); Konto ohne Kursraumzugriff sieht nur das Detailblatt.

#### NOT-007 · Nachteilsausgleich-Hinweis bei Klausuren
`P0` · `Status: Ist` (Erinnerung im Wochenkalender: NOT-053)

- Zitate: „Erinnerung Prüfung: Die Lehrkraft sieht bei anstehenden Klausuren den Nachteilsausgleich ihrer Kurse/Klassen.“ (2026-10-12 17:55); „dass die Lehrer angezeigt bekommen, dass die Kinder … einen Nachteilsausgleich haben … dass das Kind einen Nachschreibetermin haben soll“ (20:23).
- Lehrkräfte mit Recht `support.hints` (eigene Kurse) sehen in Klausurübersicht, Klausurdetail und Startseite für ihre Kurse und Klassen: „NTA n“ (n = Zahl der Kinder mit Nachteilsausgleich) mit Art, Zeitzuschlag in Minuten, betroffenen Fächern und Hilfsmitteln (z. B. „+15 Min. (Deutsch), Duden“); zusätzlich „fehlt n“ (Zahl der Kinder mit Nachschreibbedarf, KLB-053). Nie Diagnose, Merkmalsnamen von Förderbedarfen oder Nachweis-Dokumente; nur Katalogeinträge mit `teacher_visible` = ja (NOT-049). Jeder Zugriff wird protokolliert.
- Abnahme: Kind mit Katalogeintrag „Zeitzuschlag 15 min“ (Deutsch) und „Duden“ → Lehrkraft des Kurses sieht „NTA 1: +15 Min. (Deutsch), Duden“; Kind mit Merkmal „ADHS“ erscheint nicht; Lehrkraft eines fremden Kurses sieht nichts; Administration → 403.

#### NOT-008 · Klausurnoten
`P1` · `Status: Ist`

- Tabelle `exam_results` (eindeutig je `exam_id` und `student_id`): Kurs, Note (verschlüsselt), Bemerkung (verschlüsselt, optional), bewertende Person (Konto und Name), Zeitpunkt. Knopf „Noten“ an jeder Klausur und jedem Test. Ergebnisse einer Klausur werden gemeinsam abgerufen und gespeichert; die Note wird gegen die Maximalnote der Skala geprüft.
- Eintragen darf die Lehrkraft des Kursteils (`gradebook.use`, Umfang eigene Kurse) und die Schulleitung; lesen die Genannten, die Klassenleitung der Klasse (`gradebook.read_class`) und – nach der Einsichtsregel – Schüler/innen und Eltern (NOT-024). [Festlegung des Neubaus: Die Quelle weist die Routen nur als „angemeldet“ aus und verlangt eine ausdrückliche Regel.]
- Klausurnoten fließen als Quelle in das Notenbuch ein (NOT-019); das Speichern gleicht übernommene Leistungen ab. Bei Austritt einer Person werden die Ergebnisse nach der Aufbewahrungsfrist gelöscht (KLB-063: 180 Tage nach Austritt).
- Abnahme: Lehrkraft des Kurses speichert Noten für drei Kinder in einem Vorgang → drei Zeilen, Note im Datenbankauszug nur als Chiffrat; Note „7“ bei Skala 1–6 → abgelehnt; Lehrkraft eines fremden Kurses `PUT` → 404; Schüler-Konto `PUT` → 403.

## B2. Notenbuch: Aufbau und Berechnung

#### NOT-009 · Notenbuch: Aufbau, Halbjahr, Anlegen
`P1` · `Status: Ist`

- Ein Notenbuch gehört zu einem Kursteil in einem Halbjahr (eindeutig je Kurs, Kursteil, Halbjahr; Tabelle `gb_books`) mit Skala (Standard `note6`), Schlüssel, Rundungsart (Standard `ganz`), Nachkommastellen (Standard 2), Sperrzeitpunkt und sperrender Person. Halbjahr-Kennung `JJJJ-1` bzw. `JJJJ-2`, `JJJJ` = Jahr des Schuljahresbeginns.
- Halbjahreszuordnung: Datum vor dem Stichtag (Standard 1. Februar des Folgejahres) = 1. Halbjahr, ab dem Stichtag = 2. Halbjahr. Auswahl: zwei Schuljahre zurück bis zum nächsten Halbjahr; zu benachbarten Halbjahren wechseln.
- Route `/notenbuch`: Liste der Notenbücher des gewählten Halbjahres (Lehrkräfte eigene Kurse, Schulleitung alle) und „Neues Notenbuch“ (Kurs aus einer Auswahl, Leistungsstruktur nach Vorlage NOT-010). Route `/notenbuch/:bookId` zeigt die Notentabelle. Menüpunkt „Notenbuch“ bei einem der Rechte `gradebook.use|read_class|manage`.
- Löschen von Notenbüchern, Leistungen und Leistungsarten ist erlaubt, solange nicht gesperrt; mit Bestätigung und Protokolleintrag. [unklar: Löschregeln sind in den Quellen nicht belegt; Aufbewahrungs- und Löschfristen siehe NOT-027]
- Abnahme: Notenbuch für Kursteil Deutsch 5a, Halbjahr 2026-1 anlegen → ein zweites für dieselbe Kombination wird abgelehnt (409); Datum 2027-01-31 gehört zu `2026-1`, 2027-02-01 zu `2026-2`; Lehrkraft sieht in der Liste nur eigene Kurse, Schulleitung alle; fremdes Notenbuch per Kennung → 404.

#### NOT-010 · Leistungsarten und Leistungen
`P1` · `Status: Ist`

- Leistungsart (Kategorie, Tabelle `gb_categories`): Name (höchstens 120 Zeichen), Gewicht (Faktor ≥ 0, Standard 1; Gewichte ≤ 0 zählen nicht), Reihenfolge, Verschachtelung bis zu 4 Ebenen; höchstens 40 Leistungsarten und 120 Leistungen je Notenbuch. Anlegen, ändern (Name, Gewicht), löschen.
- Leistung (Spalte der Notentabelle, `gb_items`): Titel (höchstens 120 Zeichen), Datum, Gewicht (≥ 0, Standard 1), Höchstpunktzahl (optional), Schlüssel (optional), Leistungsart, Nachschreibdatum, Quelle (Typ, Kennung), `released` (Freigabe an Schüler/Eltern, NOT-024), Reihenfolge.
- Standardvorlage, wenn die Schule für das Fach keine eigene hat: „Schriftlich / Klausuren“ Gewicht 50; „Sonstige Mitarbeit“ Gewicht 50 mit Unterarten „Tests“, „Mündlich“, „Hausaufgaben“, „Referate“ je Gewicht 1 (Zitat-Kern: „Standard 50 % schriftlich, 50 % sonstige Mitarbeit“). Einzelnoten sind zusätzlich gewichtbar. Die Schulleitung pflegt die Vorlage in der Verwaltung (NOT-023).
- Abnahme: Neues Notenbuch ohne Fachvorlage → Struktur mit 50/50 und vier Unterarten; fünfte Verschachtelungsebene → abgelehnt; 121. Leistung → abgelehnt mit deutscher Meldung; Gewicht −1 → abgelehnt (422).

#### NOT-011 · Notenskalen
`P1` · `Status: Ist`

| Skala (`scale_id`) | Eingabe | Zahlenwert | Anzeige / Stufen | Höher ist besser |
|---|---|---|---|---|
| `note6` „Noten 1–6 (mit Tendenz)“ | 1, 1+, 1-, 2+, 2, 2-, … 5+, 5, 5-, 6 (6- gibt es nicht) | 1 bis 6; Tendenz ±0,3 (2+ = 1,7; 2- = 2,3); 1+ zählt wie 1,0 | Stufen 1, 1-, 2+, 2, 2-, … 5-, 6 (1+ wird nie vorgeschlagen) | nein |
| `punkte15` „Punkte 15–0 (Oberstufe)“ | ganze Zahl 0 bis 15 | 0 bis 15 | 15 bis 0 | ja |
| `prozent` | Zahl 0 bis 100 (optional „%“) | 0 bis 100 | ganzzahlig | ja |
| `verbal` | beliebiger Text (höchstens 500 Zeichen) | keiner (nicht rechenbar) | – | nein |
| `bestanden` | bestanden / b / ja / 1 bzw. nichtbestanden / nb / nein / 0 | 1 bzw. 0 | „bestanden“ / „nicht bestanden“ | ja |
| `custom` (eigene Skala) | eigene Stufen mit Zahlenwert | frei | eigene Stufen | frei (Schalter) |

- Die Schulstandardskala ist einstellbar; überschreibbar je Jahrgang (Klassenstufe) und je Kurs (höchste Priorität). Notensystem je Schulform bzw. Bildungsgang (1–6, 0–15 Punkte, Lernfelder am Berufskolleg als eigene Skala/verbal).
- Schlechtester Wert (für „unentschuldigt“, NOT-013): `note6` = 6; `punkte15`, `prozent`, `bestanden` = 0; `custom` = kleinster bzw. größter Wert je nach Richtung. Werte werden auf Gültigkeit gegen die Skala geprüft (z. B. „2+“ bei `note6`, 0–15 bei `punkte15`).
- Abnahme: Eingabe „6-“ bei `note6` → ungültig; „2+“ zählt 1,7; „1+“ zählt 1,0; `punkte15` Eingabe 16 → ungültig; Skala je Jahrgang 11 auf `punkte15` → neue Notenbücher des Jahrgangs 11 starten mit `punkte15`, Kurs-Einstellung überschreibt sie.

#### NOT-012 · Notenschlüssel
`P1` · `Status: Ist`

- Ein Notenschlüssel rechnet Punkte über Prozentgrenzen in Noten um. Grenzen gelten „ab“: Erreicht die Prozentzahl genau die Grenze, zählt schon die bessere Note; unter der letzten Grenze gilt die letzte Note. Ein Schlüssel passt nur zur eigenen Skala. Eigene Schlüssel: Stufen mit Mindestprozent 0 bis 100, absteigend sortiert.

| Schlüssel | Skala | Grenzen (mindestens % → Note) |
|---|---|---|
| `standard6` „Standard 1–6, ganze Noten“ | `note6` | 87 → 1 · 73 → 2 · 59 → 3 · 45 → 4 · 18 → 5 · 0 → 6 |
| `tendenz6` „Standard 1–6 mit Tendenz“ | `note6` | 95 → 1 · 90 → 1- · 85 → 2+ · 80 → 2 · 75 → 2- · 70 → 3+ · 65 → 3 · 60 → 3- · 55 → 4+ · 50 → 4 · 45 → 4- · 39 → 5+ · 33 → 5 · 27 → 5- · 0 → 6 |
| `oberstufe15` „Oberstufe 15–0 Punkte“ | `punkte15` | 95 → 15 · 90 → 14 · 85 → 13 · 80 → 12 · 75 → 11 · 70 → 10 · 65 → 9 · 60 → 8 · 55 → 7 · 50 → 6 · 45 → 5 · 39 → 4 · 33 → 3 · 27 → 2 · 20 → 1 · 0 → 0 |
| `bestanden50` „Bestanden ab 50 %“ | `bestanden` | 50 → bestanden · 0 → nicht bestanden |

- Standardschlüssel je Skala: `note6` → `standard6`, `punkte15` → `oberstufe15`, `bestanden` → `bestanden50`. Auswahl: ausdrücklich gewählter Schlüssel (Notenbuch oder Leistung) → Schulstandard für die Skala → eingebauter Standard.
- Für Aufgaben im Kursraum gilt ein eigener Schlüssel (Voreinstellung Note 1 ab 92 %, 2 ab 81 %, 3 ab 67 %, 4 ab 50 %, 5 ab 30 %, darunter 6; KUR). [unklar: Vereinheitlichung mit `standard6`, Betreiber entscheidet] Notenerkennung aus Text (Bewertungstext, Import) und Umrechnung in der Oberfläche verwenden im Neubau genau eine Regel.
- Abnahme: 87 % bei `standard6` → Note 1; 86,9 % → 2; 0 % → 6; 95 % bei `tendenz6` → 1, 90 % → 1-; `oberstufe15` 20 % → 1 Punkt, 19 % → 0; eine Skala `punkte15` mit Schlüssel `standard6` zugewiesen → abgelehnt.

#### NOT-013 · Eintragung, Status, Eingabegrenzen
`P1` · `Status: Ist`

- Je Leistung und Person (eindeutig, Tabelle `gb_entries`): Wert (verschlüsselt), Bemerkung (verschlüsselt), Status, Nachschreibdatum, Herkunft (aus anderem Bereich übernommen), eintragende Person und Zeitpunkt. Leere Eingabe = keine Note (zählt nicht, wird nicht als 0 gerechnet).
- Status: leer = normal gewertet; `entschuldigt` und `ausgelassen` zählen nicht; `nachschreiben` zählt noch nicht (Nachschreibtermin je Leistung und Person wird angezeigt); `unentschuldigt` zählt als schlechteste Note der Skala. Kürzel der Tabelleneingabe bei Zahlenskalen: e, a, n, u setzen den Status (e entschuldigt, a ausgelassen, n nachschreiben, u unentschuldigt; [unklar: Zuordnung aus den Statusnamen abgeleitet]).
- Punkte: bei Leistungen mit Höchstpunktzahl Punkte von 0 bis 100 000 (Dezimalzahl erlaubt, negative Werte ungültig). Prozent = Punkte × 100 / Höchstpunktzahl; Note = Schlüssel auf Prozent angewendet (Prozentskala: Wert, höchstens 100). Ohne Höchstpunktzahl wird direkt die Note eingegeben. Angezeigte Note bei `unentschuldigt`: „6“ (`note6`), „0“ (`punkte15`, `prozent`), „nicht bestanden“ (`bestanden`).
- Ungültige Werte (nicht passend zur Skala) werden als ungültig markiert und zählen nicht – außer bei den vier Status. Dezimalwerte werden mit Komma eingegeben und angezeigt; ein Punkt wird akzeptiert und als Komma übernommen.
- Abnahme: Leistung mit 40 Höchstpunkten, 30 erreicht → 75 % → Note 3 (`standard6`) bzw. 2- (`tendenz6`); Status `u` → Anzeige „6“ und zählt als 6; Status `e` → Note zählt nicht und erscheint nicht als Null; Eingabe „2,5“ bei `note6` ohne Tendenz → ungültig markiert.

#### NOT-014 · Gewichteter Schnitt
`P1` · `Status: Ist`

- Rechnung mit Dezimalzahlen (keine Gleitkomma-Ungenauigkeit); Runden kaufmännisch (0,5 wird aufgerundet, betragsmäßig symmetrisch bei negativen Werten). Eine Note zählt nur mit Zahlenwert und Gewicht > 0.
- Schnitt einer Leistungsart = Σ(Wert × Gewicht) / Σ(Gewicht) über ihre zählenden Noten und ihre Unterarten (Unterart mit Schnitt, Gewicht > 0). Gesamtschnitt = dieselbe Rechnung über die obersten Noten und Leistungsarten. Eine Leistungsart ohne zählende Note hat keinen Schnitt (leer, nicht 0); die Gewichte der übrigen verteilen sich neu. Die Zahl der zählenden Noten wird angezeigt. Standardgewicht je Note und Leistungsart: 1.
- Anzeige gerundet nach Einstellung (Nachkommastellen 0–3, Standard 2); gerechnet wird mit dem ungerundeten Wert. [unklar: Zeitpunkt der Rundung in der Quelle nicht vollständig beschrieben; Gewichtung bei Punktelisten und Rundung der Punkte nicht beschrieben]
- Abnahme: „Schriftlich“ (50) mit Klausur 2; „Sonstige Mitarbeit“ (50) mit Tests 4 und Mündlich 2 (je Gewicht 1), Hausaufgaben und Referate ohne Note → Sonstige 3,00, Gesamt (2 × 50 + 3 × 50) / 100 = 2,50; Hausaufgaben zählen nicht als 0; Schnitt 2,675 bei 2 Nachkommastellen → 2,68; Gewicht 0 → Note zählt nicht.

#### NOT-015 · Vorschlagsnote, Endnote, Übernahme der Vorschläge
`P1` · `Status: Ist`

- Vorschlagsnote je Person aus dem Gesamtschnitt (auf `decimals` gerundet). Rundungsart `ganz` (Standard): kaufmännisch auf die nächste ganze Note (3,5 → 4), begrenzt auf 1–6, 0–15 bzw. 0–100. Rundungsart `tendenz`: nächstgelegene Tendenzstufe; bei Gleichstand die schlechtere Stufe. Textskala `verbal`: kein Vorschlag. Der Vorschlag wird immer neu berechnet und nie gespeichert; Vorschläge sind keine Noten.
- Die Lehrkraft legt die Halbjahres- bzw. Zeugnisnote (Endnote) fest: je Person Wert (verschlüsselt), Bemerkung (verschlüsselt), festsetzende Person, Zeitpunkt (Tabelle `gb_finals`). „Vorschläge gesammelt übernehmen“ setzt die Endnoten aus den Vorschlägen; manuelles Setzen und Überschreiben ist jederzeit möglich, solange nicht gesperrt. Weicht die Endnote vom Vorschlag ab (Vergleich ohne Leerzeichen und Groß-/Kleinschreibung), wird „überschrieben“ vermerkt.
- Abnahme: Schnitt 2,50 mit `ganz` → Vorschlag 3; mit `tendenz` → 3+ (2,3 und 2,7 gleich weit entfernt, schlechtere Stufe); Schnitt 3,5 → 4; Endnote 2 gesetzt bei Vorschlag 3 → Anzeige „überschrieben“; „Vorschläge übernehmen“ ersetzt keine bereits festgelegten Endnoten ohne Rückfrage [unklar: Verhalten bei vorhandenen Endnoten nicht beschrieben].

#### NOT-016 · Versetzungswarnung
`P2` · `Status: Ist`

| Wert | Standard | Einheit | Wirkung |
|---|---|---|---|
| `enabled` | ja | – | Warnung an/aus |
| `min_grade` | 5 | Note (1–6) | Note 5 oder 6 (einschließlich 5+, 5-) gilt als Defizit |
| `max_points` | 4 | Punkte (15–0) | 4 Punkte oder weniger gelten als Defizit |
| `core_count` | 1 | Fächer | Warnung ab so vielen Defiziten in Hauptfächern (0 = aus) |
| `any_count` | 2 | Fächer | Warnung ab so vielen Defiziten in allen Fächern (0 = aus) |

- Defizit gibt es nur in den Skalen `note6` (ab `min_grade`) und `punkte15` (≤ `max_points`); `prozent`, `bestanden`, `verbal` nie. Die Warnung erscheint als Kennzeichen in der Notentabelle und in der Klassenübersicht für die Klassenleitung („gefährdete Versetzung“); Gründe als Text: „1 Hauptfach mit Defizit“ bzw. „N Hauptfächer mit Defizit“, „N Fächer mit Defizit“; leere Liste = keine Warnung. Eltern und Schüler/innen sehen die Warnung nicht. [unklar: Kennzeichnung der Hauptfächer in den Stammdaten und genaue Zählweise der beiden Schwellen sind in den Quellen nicht beschrieben]
- Abnahme: Standard: eine 5 in Mathematik (Hauptfach) → Klassenleitung sieht „1 Hauptfach mit Defizit“; zwei Defizite in Nebenfächern → „2 Fächer mit Defizit“; `core_count` 0 und `any_count` 0 → keine Warnung; `prozent`-Notenbuch mit 20 % → kein Defizit; Schüler-Konto sieht keine Warnung.

#### NOT-017 · Sperre und Entsperren der Halbjahresnoten
`P0` · `Status: Ist`

- Die Fachlehrkraft des Kursteils (Schulleitung für alle Notenbücher) sperrt das Notenbuch. Danach sind Einträge, Leistungen, Leistungsarten und Endnoten nicht mehr änderbar (Fehler 409 mit dem festen Text „Das Notenbuch ist gesperrt. Die Schulleitung kann es wieder öffnen.“). Entsperren darf nur die Schulleitung (`gradebook.manage`). Zitat der Entscheidung (Claude-Entwurf 2026-10-16, vom Betreiber nicht widersprochen): „Halbjahresnoten sperrt die Lehrkraft, nur die Schulleitung öffnet; jede Änderung wird protokolliert.“
- Sperrzeitpunkt, sperrende Person (Konto und Name) werden gespeichert; Sperren und Entsperren stehen im Änderungsprotokoll (NOT-018) und im Audit ohne Notenwerte.
- Gesperrte Notenbücher werden vom Nachziehen übernommener Quellen ausgenommen (NOT-019). Endnoten werden Schülern und Eltern erst nach dem Sperren sichtbar (NOT-024); der Export umfasst nur gesperrte Notenbücher (NOT-026). Eine Benachrichtigung der Art `gradebook` beim Sperren enthält keine Noten. [unklar: Empfängerkreis der Benachrichtigung nicht belegt]
- Abnahme: Lehrkraft sperrt → `PUT` eines Eintrags → 409 mit dem festen Text; Lehrkraft versucht zu entsperren → 403; Schulleitung entsperrt → Änderung wieder möglich, Protokoll enthält „gesperrt“ und „entsperrt“ mit Person und Zeit; Benachrichtigung enthält keinen Notenwert.

#### NOT-018 · Änderungsprotokoll des Notenbuchs
`P0` · `Status: Ist`

- Jede Änderung eines Notenbuchs wird protokolliert (Tabelle `gb_log`, nur anhängend): Zeitpunkt, handelnde Person (Konto, Name), Aktion, betroffene Leistung, betroffene Person, Einzelheiten „alter Wert → neuer Wert“ verschlüsselt. Das Protokoll bleibt beim Löschen des Notenbuchs erhalten (bis zur Aufbewahrungsfrist). Dialog „Protokoll“ im Notenbuch für die Lehrkraft des Notenbuchs und die Schulleitung.
- Aufgezeichnet werden mindestens: Notenbuch angelegt/geändert/gelöscht, Leistungsart und Leistung angelegt/geändert/gelöscht, Eintrag gesetzt/geändert, Endnote gesetzt, Sperre, Entsperrung, Übernahme/Abwahl/Rückzug von Quellen. [unklar: Liste der Aktionswerte in der Quelle nicht vollständig]
- Zusätzlich schreibt das Audit-Protokoll `gradebook.*` ohne Notenwerte.
- Abnahme: Note von 3 auf 2 ändern → Protokollzeile mit Person, Zeit, Aktion und verschlüsseltem Wert „3 → 2“ (Datenbankauszug nur Chiffrat), Protokolldialog zeigt „3 → 2“ für Berechtigte; Audit-Zeile enthält keinen Notenwert; Notenbuch löschen → Protokoll bleibt.

#### NOT-019 · Übernahme von Ergebnissen aus anderen Bereichen
`P1` · `Status: Ist`

- Ablauf: (1) Ein anderer Bereich meldet eine Quelle an (Quelltyp bis 30 Zeichen, Bezeichnung, Abrufmöglichkeit) und veröffentlicht Ergebnisse je Schüler/in und Leistung: Elementtyp, Kennung, Punkte mit Höchstpunktzahl oder Note, Datum. (2) Das Notenbuch zeigt die Ergebnisse unter „Übernehmen“ als Vorschlag. (3) Die Lehrkraft übernimmt (`adopted`), wählt ab (`dismissed`), stellt Abgewähltes wieder her (`restore`) oder synchronisiert (`sync`); die Bezeichnung der Quelle ist änderbar. (4) Nichts wird automatisch übernommen; eine Quelle kann ihre Ergebnisse zurückziehen (`withdraw`).
- Angeschlossene Quellen: Klausur- und Testnoten (`exam_results`), bewertete Aufgaben im Kursraum (je bewerteter Abgabe in der aktuellen Version: Punkte, Höchstpunkte, Prozent, Note als Text, Note als Zahl wenn eindeutig, Zeitpunkt, Versuch, verspätet, Gruppe; eine Gruppenbewertung gilt je Person), Selbsttests (Punkte = bester Versuch; Meldung beim Abgeben und Ändern, Rücknahme beim Löschen). Aus Bewertungstext ohne Punkte werden Formate wie „80 %“, „12/15“, „9 von 12“, „2+“, „2,5“, „2-3“ ausgewertet; „12 Punkte“ ohne Maximum ist nicht auswertbar.
- Erneutes Veröffentlichen zieht in bereits übernommene Leistungen nach; von Hand geänderte Noten bleiben erhalten; gesperrte Notenbücher werden nicht nachgezogen. Wird eine Quelle zurückgezogen, verschwinden ihre Ergebnisse, bereits übernommene Leistungen bleiben mit ihren Noten. Gelöschte Aufgaben verschwinden aus dem Notenbuch. Ergebnisse (Tabellen `gb_source_results`, `gb_source_links`) sind wie Noten verschlüsselt (Altsystem: Klartext – nicht übernehmen).
- Abnahme: Aufgabe bewertet (12 von 15) → erscheint unter „Übernehmen“, nicht in der Tabelle; „Übernehmen“ → neue Leistung mit Note; Quelle erneut veröffentlicht (13 von 15) → Leistung zieht nach, von Hand geändertes Kind bleibt; Quelle zurückgezogen → Vorschlag weg, Leistung bleibt; gesperrtes Notenbuch → kein Nachziehen.

#### NOT-020 · Notentabelle und Eingabe (PC und Handy)
`P1` · `Status: Ist` (Handy-Eingabe nur per Test belegt)

- Zeilen: Schüler/innen (gruppiert); Spalten: Leistungen je Leistungsart mit Kopf (Gewicht, Durchschnitt), Spalte Durchschnitt, Spalte Halbjahresnote; Warnkennzeichen (NOT-016); Status in Kurz- oder Langform; Leistungsbaum mit Einrückung und Gewichtsanteilen. Notenfarbe (gut/ok/schlecht) dient nur der Kennzeichnung – der Wert steht immer daneben.
- PC: tabellenartige Eingabe mit Pfeiltasten und Enter zum Weitergehen, Kürzel für Status und Noten; Einzeldialog für einen Wert. Handy: Antippen einer Zelle mit Schnellwahl-Knöpfen. Speichern je Leistung gebündelt. Schnelle Eingabe darf dieselbe Note nicht doppelt speichern (behobener Fehler 2026-10-16).
- Dialoge: Leistung (anlegen/ändern), Leistungsarten, Einstellungen, Übernahme (Quellen), Protokoll, Einzelwert, Person (Schülerdetail). Anrede „Sie“; Tastaturbedienung der Tabelle.
- Abnahme: Browser-Test PC: Pfeil rechts/unten und Enter bewegen die Eingabe, Kürzel `u` setzt `unentschuldigt`; Handy 390 px: Antippen der Zelle öffnet die Schnellwahl und speichert; zehnmal schnelle Eingabe derselben Note → ein Eintrag und eine Protokollzeile; Farbstufe ist ohne Farbe erkennbar (Wert sichtbar).

#### NOT-021 · Fehlzeiten und Noten: Bewertungsregel
`P2` · `Status: Ist`

- Entscheidung (Claude-Entwurf 2026-10-16, vom Betreiber nicht widersprochen): Eine entschuldigt fehlende oder nachgeschriebene Leistung zählt nicht; eine unentschuldigt fehlende Leistung zählt als ungenügend (schlechteste Note der Skala). Im Notenbuch entspricht dies den Status `entschuldigt`, `nachschreiben` (zählen nicht) und `unentschuldigt` (schlechteste Note); die Lehrkraft setzt den Status. Der Nachschreibtermin je Leistung und Person (Feld `makeup_date`) wird in der Tabelle angezeigt und stammt aus dem Nachschreibtermin (KLB-054). [unklar: eine automatische Vorbelegung des Status aus der Nachschreib-Zeile ist in den Quellen nicht beschrieben]
- Abnahme: Kind fehlt entschuldigt zur Klausur → Status `entschuldigt`, Schnitt unverändert; unentschuldigt → Schnitt rechnet mit 6; nach Nachschreiben Note eintragen und Status leeren → Note zählt; Nachschreibdatum erscheint in der Zelle.

#### NOT-022 · Klassenübersicht und Notenkonferenz-Liste
`P1` · `Status: Ist`

- Route `/notenbuch/klasse/:classId` (Recht `gradebook.read_class` oder `gradebook.manage`): Tabelle Schüler/in × Fächer; je Zelle die festgelegte Endnote oder der Vorschlag (vorläufig gekennzeichnet); Warnungen bei Defiziten und gefährdeter Versetzung. Klassenleitung sieht alle Fächer ihrer Klasse lesend (Abteilungsleitung für ihren Zweig).
- Notenkonferenz-PDF je Klasse: Schüler/innen × Fächer, Defizite markiert, Warnungen am Ende.
- Abnahme: Klassenleitung 7a öffnet die Übersicht → alle Fächer, Endnoten und Vorschläge unterscheidbar; Fachlehrkraft ohne Klassenleitung → 404; PDF enthält markierte Defizite und am Ende die Liste der Warnungen.

#### NOT-023 · Notenbuch-Einstellungen der Schule (Verwaltung)
`P1` · `Status: Ist` (Standard Einsicht geändert)

- Route `/notenbuch/verwaltung` (Schulleitung, `gradebook.manage`) mit Abschnitten Einsicht, Skalen, Notenschlüssel, Vorlage, Versetzungswarnung, Export. Skalen-Editor und Notenschlüssel-Editor. Alle Werte sind einstellbar und werden auf Gültigkeit geprüft.

| Einstellung | Standard | Einheit / Optionen | Wirkung |
|---|---|---|---|
| Standardskala | `note6` | `note6` · `punkte15` · `prozent` · `verbal` · `bestanden` · eigene | Skala neuer Notenbücher |
| Skala je Jahrgang | leer | Jahrgang → Skala | überschreibt Standard |
| Skala je Kurs | leer | Kurs → Skala | höchste Priorität |
| Schulstandard-Schlüssel je Skala | leer | Skala → Schlüssel | überschreibt den eingebauten Standard |
| Einsicht Schüler/Eltern | `freigabe` | `aus` · `sofort` · `freigabe` · `endnote` | NOT-024. [unklar: das Altsystem lieferte `sofort`; Entscheidung 2026-10-16 17:28 verlangt `freigabe`] |
| Durchschnitte anzeigen | ja | ja · nein | Schnitte in der Schülersicht |
| Rundungsart Vorschlag | `ganz` | `ganz` · `tendenz` | NOT-015 |
| Nachkommastellen Schnitt | 2 | 0 bis 3 | Rundung des Schnitts |
| Halbjahreswechsel | 1. Februar | Monat-Tag | NOT-009 |
| Versetzungswarnung | siehe NOT-016 | – | Gefährdungshinweise |
| Vorlage Leistungsstruktur | 50/50 (NOT-010) | Baum aus Leistungsarten | neue Notenbücher ohne Fachvorlage |

- Grenzen: höchstens 40 Leistungsarten und 120 Leistungen je Notenbuch, 4 Ebenen, Name höchstens 120 Zeichen, Gewicht ≥ 0. Jede Einstellung steht genau einmal; Speichern je Abschnitt.
- Abnahme: Einsicht auf `endnote` stellen → Schüler sehen nur Endnoten gesperrter Notenbücher; Standardskala auf `punkte15` → neue Notenbücher starten mit 15–0; Nachkommastellen 4 → abgelehnt; Lehrkraft ruft `/notenbuch/verwaltung` auf → 403.

## B3. Notenbuch: Einsicht, Rechte, Export, Datenschutz, Zeugnisse

#### NOT-024 · Einsicht für Schüler/innen und Eltern („Meine Noten“)
`P0` · `Status: Ist` (Standard „nach Freigabe“ ist Neubau-Vorgabe)

- Zitat (Sinn): Schüler sollen sehen, „in welchen Fächern sie benotet wurden“ (2026-10-11 17:55); Schüler/innen und Eltern sehen nur, was die Schule freigibt (Entscheidung 2026-10-16, vom Betreiber nicht bestätigt, nicht widersprochen): gar nichts · alles sofort · erst nach Freigabe · nur die Endnote.
- Einsichtsmodus der Schule (`gradebook`-Einstellung): `aus` – keine Einsicht; `sofort` – alle eingetragenen Noten; **`freigabe` (Standard)** – nur Leistungen, die die Lehrkraft einzeln freigegeben hat (`released`); `endnote` – nur die festgelegte Endnote. Die Endnote erscheint in jedem Modus erst nach dem Sperren des Notenbuchs. Schnitte sind ein- oder ausblendbar. Schüler/innen und Eltern sehen nur festgelegte Noten, nie Vorschlagsnoten oder Protokolle. [Festlegung des Neubaus: die Quelle belegt die Regel für Vorschlagsnoten nicht]
- Route `/noten` („Meine Noten“): Karte je Fach („in welchen Fächern sie benotet wurden“), Dialog für Klausuren und Tests, keine Eingabe, nur Einsicht. Eltern sehen die Noten je Kind (Kindauswahl); minderjährige Kinder: immer; volljährige: nur mit Freigabe des Bereichs „Noten“ (KLB-005). Mitschüler/innen und Fremde sehen Noten nie; ein Schüler-Konto kann über andere Kennungen keine fremden Noten abrufen (bestätigt durch Audit und Penetrationstest 2026-10-17).
- Nachteilsausgleich erscheint nur als Hinweis „NTA“ (mit `support.hints` bzw. `support.read`). Benachrichtigungen enthalten keine Noten.
- Abnahme: Modus `freigabe`: Lehrkraft gibt Test 1 frei → Schüler sieht nur Test 1, nicht Test 2 und nicht den Vorschlag; Modus `endnote`, Notenbuch nicht gesperrt → leere Ansicht; nach Sperren → Endnote sichtbar; Eltern eines Volljährigen ohne Freigabe „Noten“ → 404; Schüler A ruft Noten von Schüler B per Kennung → 404; Moduswechsel auf `aus` → „Meine Noten“ leer mit Hinweis.

#### NOT-025 · Rechte im Notenbuch
`P0` · `Status: Ist`

| Recht | Wirkung | Standardrollen (Datenumfang) |
|---|---|---|
| `gradebook.use` | Noten, Leistungsarten, Gewichtung eigener Notenbücher führen; Halbjahresnoten festlegen und sperren | Lehrkraft und Abteilungsleitung (eigene Kurse), Schulleitung (alle) |
| `gradebook.read_class` | Notenübersicht, Notenkonferenz-Liste und Versetzungswarnung der Klasse lesen | Lehrkraft und Abteilungsleitung (eigene Klassenleitung), Schulleitung |
| `gradebook.manage` | Skalen, Schlüssel, Einsicht, Versetzungswarnung festlegen; gesperrte Notenbücher öffnen; sieht alle Notenbücher | Schulleitung |
| `gradebook.export` | gesperrte Halbjahres- und Zeugnisnoten als CSV ausgeben | Schulleitung, Sekretariat |

- Die technische Administration hat nie Zugriff auf Noten. Schüler/innen und Eltern haben kein Recht, sondern sehen ihre Noten über `/noten` (NOT-024). Zuschauer/Ansichtskonten sind vom Notenbuch ausgeschlossen (entzogen). Fremde Notenbücher ohne Recht liefern 404.
- Jede Lese- und Schreibroute (Sperren, Einträge, Endnoten, Klausurergebnisse, Quellenaktionen) prüft fachlich: eigener Kurs, Klassenleitung, Sperre – nicht nur „angemeldet“. [Festlegung des Neubaus: In der Quelle weisen mehrere Routen nur „angemeldet“ aus.] Rechte-Matrix-Test bei jeder neuen Sichtbarkeitsregel.
- Abnahme: Je Rolle × Recht × (eigenes, fremdes Notenbuch) automatischer Test: Lehrkraft eigenes Notenbuch 200, fremdes 404; Klassenleitung schreibt → 403; Sekretariat `GET /export` ohne offene Bücher 200, Entsperren 403; Administration alle Routen 403; Zuschauer-Konto 403.

#### NOT-026 · Export für SchILD-NRW/SVWS, ASV und LUSD
`P1` · `Status: Ist` (Rundlauf-Prüfung offen, NOT-030)

- Recht `gradebook.export` oder `gradebook.manage`. Parameter: Halbjahr, Format (`schild`, `asv`, `lusd`), optional Klasse; die Schulleitung kann offene (nicht gesperrte) Notenbücher einschließen (`include_open`). Exportiert werden nur festgelegte Endnoten, nur aus gesperrten Notenbüchern.
- Spalten (gemeinsamer Kern): Kennung, Nachname, Vorname, Geburtsdatum, Klasse, Schuljahr („JJJJ/JJ“), Halbjahr (1 oder 2), Fach-Kennung, Fachname, Kurs, Lehrkraft, Note, Bemerkung (nur SchILD; leer). Je Format eigene Spaltenköpfe nach den Importvorlagen der Zielsoftware (SchILD-NRW/SVWS „Leistungsdaten“, ASV BW/BY, LUSD Hessen). Sortierung Klasse, Nachname, Vorname, Fach.
- Dateiformat: Trennzeichen „;“, UTF-8 mit Byte-Order-Mark, Zeilenende CRLF, Datum TT.MM.JJJJ, Noten mit Dezimalkomma. Excel-Schutz: Zellen, die mit „=“, „@“ oder „+“/„-“ (nicht gefolgt von einer Ziffer) beginnen, erhalten ein vorangestelltes Hochkomma; Noten wie „2+“ bleiben unverändert.
- Die Zuordnung der Spalten ist in der Zielsoftware einmalig zu prüfen (Hinweis in der Oberfläche, Export-Karte in der Verwaltung). Jeder Export wird protokolliert (Person, Zeit, Format, Halbjahr, Zahl der Zeilen; keine Noten). [Festlegung des Neubaus: Protokollierung des Exports ist im Altsystem nicht belegt]
- Abnahme: Export Halbjahr `2026-1`, Format `schild`, nur gesperrte Bücher → Zeilen mit allen Spalten, UTF-8-BOM, CRLF, „2,3“ als Dezimalkomma; offenes Buch ohne `include_open` nicht enthalten; Bemerkung „=SUMME(A1)“ erscheint als `'=SUMME(A1)`; Lehrkraft ohne `gradebook.export` → 403; Export erzeugt einen Audit-Eintrag ohne Notenwerte.

#### NOT-027 · Datenschutz der Noten
`P0` · `Status: Ist` (Klartext-Altlasten nicht übernehmen)

- Notenwerte, Punkte, Bemerkungen, Endnoten, Protokolleinzelheiten und Übernahme-Ergebnisse sind verschlüsselt gespeichert (Tabellen `exam_results`, `gb_entries`, `gb_finals`, `gb_log`, `gb_source_results`), gebunden an Tabelle, Feld und Datensatz (KLB-001). Im Altsystem standen Punkte und Note der Quellenergebnisse im Klartext und die Verschlüsselung der Endnoten war nicht eindeutig belegt – der Neubau verschlüsselt alle. Schüler-Kennungen bleiben als Schlüssel Klartext, enthalten aber keine Namen.
- Noten gehören nie zur öffentlichen Schnittstelle oder zu API-Zugängen. Keine Noten in Benachrichtigungen, Push, URLs, Logs, Fehlermeldungen; Client-Caches enden mit Abmeldung und Kontowechsel. Das Audit zeichnet jede Notenbuch-Aktion (`gradebook.*`) ohne Notenwerte auf.
- Schlüsselwechsel (CLI `rotate-keys`) schreibt alle Notenspalten neu. Auskunft und Export nur im Umfang der Einsicht (KLB-064).
- Aufbewahrung: Klausurergebnisse, Notenbuch (Einträge, Endnoten, Protokoll, Quellenergebnisse) und Lernstände werden 180 Tage nach Austritt gelöscht (Wartelistenfrist mindestens 30 Tage; Löschprotokoll ohne Inhalte). [unklar: Aufbewahrungsfristen für Zeugnislisten nach Landesrecht – Backlog nennt 10 Jahre; Entscheidung DAT/REH]
- Für Noten, Fehlzeiten, Gesundheits- und Verhaltensdaten liegt eine Datenschutz-Folgenabschätzung vor (REH).
- Abnahme: Datenbankauszug von `gb_entries`, `gb_finals`, `gb_source_results`, `exam_results`: Werte nur als Chiffrat; Audit-Zeilen und Benachrichtigungen enthalten keine Notenwerte; API-Zugang mit allen Bereichen liefert keine Noten; nach 180 Tagen Austritt (feste Uhr) sind die Noten der Person gelöscht, Löschprotokoll zeigt nur Art und Anzahl.

#### NOT-028 · Zeugnisse und Abschlüsse: kein Zeugnisdruck
`P1` · `Status: Ist` (bewusste Nicht-Funktion)

- Das System druckt keine amtlichen Zeugnisse und keine Zeugnisformulare. Zeugnisse werden weiter in SchILD-NRW/SVWS bzw. ASV erstellt; das System liefert Endnoten (NOT-026) und Fehlstunden (KLB-050) zu. Grund: hohes Rechtsrisiko je Land und Schulform.
- Der Lernentwicklungsbericht (NOT-042) ist kein Zeugnis, sondern Grundlage für Zeugnisbemerkungen und Gespräche.
- Abnahme: Es gibt weder eine Route noch einen Menüpunkt, die Zeugnis-PDF erzeugen; die Hilfe beim Export nennt die Zielsoftware.

#### NOT-029 · Kopfnoten, Zeugniskonferenz, Abschlussregeln
`P2` · `Status: offen`

- Kopfnoten (Arbeits- und Sozialverhalten; frei bei Noten/Zeugnis in BY, NI, SN, ST): Abstimmungs-Workflow im Notenbuch – Fachlehrkräfte geben Einschätzungen, die Klassenleitung schlägt die Kopfnote vor, Fachlehrkräfte bestätigen oder kommentieren, Übernahme in den Export. Hängt am Notenbuch („jetzt, da das Notenbuch existiert, sinnvoll“, Planungsstand 2026-10-13).
- Zeugniskonferenz: Leistungsübersicht mit Farbmarkierung (gefährdet/stark), Notenschnitte, Detail je Schüler/in mit Fehltagen, automatische Gefährdungsbriefe (im Marktvergleich nur BY Real/Gym).
- Abschlussregeln je Bundesland als Daten (Vorbild SchILD), z. B. Versetzungs- und Abschlussbedingungen. [unklar: welche Länder zuerst]
- Abnahme: Kopfnote durchläuft Vorschlag → Bestätigung → Export mit Protokoll; Konferenzansicht markiert gefährdete Kinder und zeigt Fehltage aus KLB-046; Abschlussregel für NRW als Datensatz ändert die Warnung der Versetzung ohne Programmänderung.

#### NOT-030 · Notenübergabe im ENM-/SVWS-Format und Rundlauf
`P2` · `Status: offen`

- Export der Noten, Fehlstunden (aus KLB-046) und Bemerkungen im ENM- bzw. SVWS-Format; Rundlauf-Test (Export, Import in die Zielsoftware, Vergleich) mit der öffentlichen Formatbeschreibung. [unklar: Verfügbarkeit der Formatbeschreibung nicht belegt] Die Spalten der drei CSV-Formate sind gegen die aktuellen amtlichen Spezifikationen zu testen (Altsystem: nur gegen Importvorlagen, keine Rundlauf-Tests).
- Landes-Exporte weiterer Länder (ASV BY, LUSD HE, SchILD/LUPO NRW) einschließlich Fehlzeiten-Export; Nachbarland nach Betreiberentscheidung.
- Abnahme: Rundlauf-Test: Export → Import in eine Testinstanz der Zielsoftware → gleiche Noten, Fächer, Halbjahre und Fehlstunden; Abweichung bricht den Test.

#### NOT-031 · Weitere offene Notenbuch-Funktionen
`P3` · `Status: offen`

- Notenabzug bei verspäteter Abgabe (Moodle-Vergleich, niedrig). Klausur-Detailfelder „zurückgegeben am“ und Durchschnittsnote, Klausurstatistik und Prüfungskalender-Statistik (Untis-Vergleich). Schulleitungs-Dashboard mit Klausurdichte und Fehlquoten (Fehlquoten: KLB-050).
- Entscheidung des Betreibers offen: Aufbewahrungs- und Löschregeln für Notenbücher, Leistungen und Leistungsarten; Wirkung eines Rückzugs einer Quelle auf übernommene Werte (Ist: Werte bleiben); Benachrichtigung bei veröffentlichten Noten (Ist: keine).
- Abnahme: Aufgabe 3 Tage verspätet mit Abzug 10 % je Tag → Vorschlagsnote berücksichtigt den Abzug nachvollziehbar; Klausur-Detail zeigt Durchschnittsnote und „zurückgegeben am“.

## B4. Kompetenzraster und Lernstand

Zweck: Kompetenzraster je Fach und Jahrgang, Lernstand je Kind und Kompetenz, Selbsteinschätzung, Lernplan, Abzeichen und Lernentwicklungsbericht (PDF). Trägt Grundschule, Montessori und Lernentwicklungsgespräche. Herkunft: Claude-Bau nach Marktvergleich (2026-10-13 bis 2026-10-16); der Betreiber hat den Moodle-/Marktvergleich gewollt, die Funktionen selbst nicht ausdrücklich beschrieben.

Begriffe: **Rahmen** = Kompetenzraster eines Faches oder Jahrgangs mit Name, 2 bis 6 Niveaustufen und Bereichen (mehrere Rahmen nebeneinander); **Bereich** = Gliederung im Rahmen (z. B. „Zahlen und Rechnen“); **Kompetenz** = „Ich kann …“-Aussage mit optionalem Kürzel und optionaler Beschreibung je Stufe; **Stufe** = 1 bis n, „nicht eingeschätzt“ ist kein Wert, sondern ein fehlender Eintrag; **Lernstand** = Stufe je Kind und Kompetenz mit Datum, Nachweis und Kommentar.

#### NOT-032 · Kompetenzrahmen: Aufbau und Grenzen
`P1` · `Status: Ist`

| Wert | Standard / Grenze | Wirkung |
|---|---|---|
| Stufen je Rahmen | 2 bis 6 (Standard 4); weniger Stufen als vorhandene Lernstände sind nicht möglich | Anzahl Niveaustufen |
| Standard-Stufenbeschriftung | „Ich fange an“ · „Ich kann es mit Hilfe“ · „Ich kann es allein“ · „Ich kann es erklären“ | wenn keine Stufen angegeben |
| Beispiel-Stufen Montessori | „Eingeführt“ · „Übt mit dem Material“ · „Arbeitet sicher“ · „Kann es weitergeben“ | Beispielrahmen (Dreierschritt) |
| Stufe „braucht Unterstützung“ (`support_level`) | 1; 0 bis (Stufenzahl − 1); 0 = Markierung aus | bis zu dieser Stufe gilt Unterstützungsbedarf |
| Bereiche je Rahmen | höchstens 40 | Obergrenze |
| Kompetenzen je Rahmen | mindestens 1, höchstens 600 | Obergrenze |
| Beschriftung einer Stufe | 1 bis 80 Zeichen, nicht leer | Stufentext |
| Name Rahmen / Bereich | höchstens 200 Zeichen, Pflicht | Name |
| Fach (Rahmen) | höchstens 40 Zeichen | Zuordnung |
| Beschreibung Rahmen | höchstens 500 Zeichen | Text |
| Kompetenz (Text) | 1 bis 300 Zeichen, Pflicht | „Ich kann …“-Aussage |
| Kürzel Kompetenz | höchstens 20 Zeichen | Code |
| Beschreibung je Stufe | höchstens 300 Zeichen; höchstens so viele wie Stufen | Stufenbeschreibung |

- Tabellen `comp_frameworks` (Name, Fach, Beschreibung, `levels`, `support_level`, `archived`), `comp_areas`, `comp_competencies` (Kürzel, Titel, Stufentexte). Rahmen und Bereiche tragen keine Personendaten.
- Abnahme: Rahmen mit 7 Stufen → 422; Rahmen mit 3 Stufen speichern, nachdem Lernstand der Stufe 4 existiert → abgelehnt; `support_level` 4 bei 4 Stufen → abgelehnt; 601. Kompetenz → abgelehnt; Stufenbeschriftung mit 81 Zeichen → abgelehnt mit deutscher Meldung am Feld.

#### NOT-033 · Rahmen verwalten: Vorlagen, Archiv, Löschen
`P1` · `Status: Ist`

- Recht `competency.manage`: Rahmen anlegen (leer, aus eingebauter Vorlage als eigene Kopie, per Import), bearbeiten (der Editor speichert den ganzen Rahmen; Einträge mit Kennung bleiben erhalten, die Stufenzahl wird geprüft), exportieren, archivieren, löschen. Archivieren: der Rahmen wird für neue Einschätzungen nicht mehr angeboten, die Historie bleibt (`?archived=1` zeigt archivierte).
- Ein Rahmen mit Lernständen lässt sich nur archivieren, nicht löschen (409). Eine Kompetenz mit Lernständen wird beim Bearbeiten nur mit ausdrücklicher Bestätigung (`force`) entfernt; die Oberfläche fragt vorher in einem App-Dialog nach.
- Eingebaute Beispielrahmen: „Grundschule Mathe und Deutsch“ (5 Bereiche, 21 Kompetenzen; Bereiche: Mathe Zahlen und Rechnen, Mathe Formen und Größen, Deutsch Sprechen und Zuhören, Deutsch Lesen, Deutsch Schreiben; Standardstufen; Unterstützungsstufe 1) und „Montessori-Materialien“ (5 Bereiche, 20 Kompetenzen; Bereiche: Übungen des täglichen Lebens, Sinnesmaterial, Sprache, Mathematik, Kosmische Erziehung; Montessori-Stufen). Zuschreibung: Lehrkräfte und Leitung pflegen Rahmen und Abzeichen der Schule ohne Einblick in Lernstände.
- Abnahme: Vorlage „Montessori-Materialien“ übernehmen → eigener Rahmen mit 5 Bereichen und 20 Kompetenzen, Änderungen daran verändern die Vorlage nicht; Rahmen mit einem Lernstand löschen → 409, archivieren → 200 und aus der Auswahl für neue Einschätzungen entfernt, Verlauf bleibt; Kompetenz mit Lernstand entfernen ohne Bestätigung → abgelehnt.

#### NOT-034 · Import und Export von Rahmen
`P2` · `Status: Ist` (Formelschutz im CSV-Export offen)

- Import im JSON-Format (Export = Import): Name, Fach, Beschreibung, Stufenbeschriftungen (`levels`), `support_level`, Bereiche mit Kompetenzen (`code`, `title`, `descriptors`). Import als CSV mit Trenner `;`, `,` oder Tabulator; erste Zeile ist Kopf: `Bereich;Kompetenz;Kürzel;Stufe 1;Stufe 2 …`; eine leere Bereichszelle heißt „wie darüber“; jede Zeile braucht Bereich und Kompetenz; Stufenbeschriftungen kommen aus dem Import-Formular (Standard „Ich fange an / mit Hilfe / allein / erklären“). Grenzen: 40 Bereiche, 600 Kompetenzen, 2 bis 6 Stufen; Fehler ergeben 422 mit deutschem Text je Zeile.
- Export als CSV: Bereich; Kompetenz; Kürzel; Beschreibung je Stufe („Stufe n: Beschriftung“); Export als JSON. Moodle-Importe übertragen Bewertungsraster, Notenbuch, Kompetenzen und Abzeichen (INT).
- Offen (Prüfbefund 2026-10-17, P2, Status: offen): Der CSV-Export „Kompetenzen“ schützt nicht vor Excel-Formeln; der Neubau stellt Zellen, die mit `=`, `@`, `+` oder `-` (nicht gefolgt von einer Ziffer) beginnen, ein Hochkomma voran.
- Abnahme: Export eines Rahmens und Import in eine leere Instanz → identische Struktur (Rundlauf); CSV mit Zeile ohne Kompetenz → 422 mit Zeilennummer; Stufen im CSV nach 7 Spalten → 422; Kompetenztext „=1+1“ im CSV-Export → `'=1+1`.

#### NOT-035 · Einschätzung durch Lehrkräfte
`P1` · `Status: Ist` (Mehrfach-Oberfläche offen)

- Recht `competency.assess`: Stufe je Kompetenz und Schüler/in setzen mit Datum, Nachweis (Art leer · `note` · `link` · `assignment` · `material`; optional Verweis auf ein Element im Format `Typ:ID`, z. B. `channel:12`) und Kommentar bzw. Beobachtung (Nachweistext und Kommentar verschlüsselt). Die Schnittstelle nimmt mehrere Kinder und Kompetenzen in einem Vorgang an; die Oberfläche arbeitet bisher je Kind und Kompetenz (Mehrfach: NOT-047).
- Jede Einschätzung ist unveränderlich (nur anhängend): Eine neue Einschätzung ergibt einen neuen Verlaufseintrag; ein falsch gesetzter Wert bleibt im Verlauf. Eine gleiche Stufe ohne Nachweis und ohne Kommentar wird beim Setzen übersprungen. Verlauf je Kompetenz einsehbar (neueste zuerst). Nach jeder Lehrkraft-Einschätzung oder Bestätigung werden automatische Abzeichen geprüft (NOT-041).
- Abnahme: Stufe 2 setzen, später Stufe 3 → zwei Verlaufseinträge, aktueller Stand 3; Stufe 3 erneut ohne Nachweis → kein neuer Eintrag; Stufe 5 bei 4-stufigem Rahmen → 422; Fremdes Kind (keine Zuständigkeit) → 404; Kommentar im Datenbankauszug nur Chiffrat.

#### NOT-036 · Selbsteinschätzung und Bestätigung
`P1` · `Status: Ist`

- Schüler/innen setzen die eigene Stufe je Kompetenz (Art `self`). Die Lehrkraft bestätigt die Selbsteinschätzung, auch mit anderer Stufe; dabei entsteht ein Lehrkraft-Eintrag, und der Selbsteintrag gilt als bestätigt (`confirmed_at`, `confirmed_by`). Beide Werte stehen nebeneinander. Selbsteinschätzungen lösen keine automatische Abzeichenvergabe aus.
- Schülerinnen und Schüler pflegen nur eigene Einträge; Eltern nur lesend.
- Abnahme: Schüler/in setzt Stufe 3; Lehrkraft bestätigt mit Stufe 2 → zwei Einträge (Selbst 3 bestätigt, Lehrkraft 2); Klassenübersicht zeigt keine „offene Bestätigung“ mehr; Eltern-Konto setzt Selbsteinschätzung → 403.

#### NOT-037 · Aktueller Stand, Fortschritt, „braucht Unterstützung“
`P1` · `Status: Ist`

- Aktueller Stand je Kompetenz = jüngster Eintrag (Datum, bei Gleichstand höhere Kennung) je Art; Lehrkraft und Selbsteinschätzung getrennt.
- Fortschritt je Rahmen oder Bereich = Σ min(Stufe, Höchststufe) / (Höchststufe × Anzahl Kompetenzen); fehlende Einschätzung zählt 0; Anzeige in Prozent (gerundet). „Eingeschätzt“ = Anzahl Kompetenzen mit Lehrkrafteintrag.
- „Braucht Unterstützung“ (nur Lehrkraft-Sicht): Lehrkraft-Stufe ≤ Unterstützungsstufe des Rahmens; fehlt die Lehrkraft-Einschätzung, zählt die Selbsteinschätzung; Unterstützungsstufe < 1 = nie. Schüler/innen und Eltern sehen die Markierung nicht.
- Abnahme: Rahmen mit 4 Stufen und 5 Kompetenzen, Lehrkraft-Stufen 4, 3, 2, 1 und eine fehlende → Fortschritt (4+3+2+1+0) / 20 = 50 %; Kompetenz auf Stufe 1 bei `support_level` 1 → „braucht Unterstützung“; bei `support_level` 0 nie; Antwort an das Schüler-Konto enthält die Markierung nicht.

#### NOT-038 · Beobachtungsnotizen
`P0` · `Status: Ist`

- Beobachtungen (Nachweisart `note`) sind verschlüsselt und nur für Lehrpersonal (Sichtstufe `staff`) sichtbar; Schüler/innen und Eltern sehen sie nie und sie erscheinen nie im Lernentwicklungsbericht (NOT-042). Förderbezug und Unterstützungsmarkierung sind nie Teil der öffentlichen Schnittstelle.
- Abnahme: Lehrkraft legt Beobachtung an → Schüler-Antwort und Eltern-Antwort enthalten weder Text noch Eintrag mit `evidence_type=note`; PDF-Bericht enthält sie nicht; Datenbankauszug zeigt Chiffrat.

#### NOT-039 · Klassenübersicht (Heatmap) und Lernstand je Kind
`P1` · `Status: Ist`

- Reiter „Klassenübersicht“ (`competency.read`): Tabelle Klasse × Kompetenzen, je Zelle Lehrkraft-Stufe, Selbsteinschätzung und offene Bestätigung; Anteil in Prozent, Farbstufen 1 bis 4 und „nicht eingeschätzt“ gesondert; Filter nach Rahmen, Bereich und „braucht Unterstützung“; Legende; Stufen immer mit Beschriftung, nie nur Farbe. Je Kind Zähler für Unterstützung, offene Bestätigungen und Fortschritt in Prozent.
- Lernstand eines Kindes: Fortschritt je Bereich in Prozent, je Kompetenz Stufenbalken (vier Farbstufen) mit aktueller Stufe und Verlauf, Lehrkraft- und Selbsteinschätzung nebeneinander, zugeordnete Elemente mit Titel. Lehrkraft nur eigene Klassen, Abteilungsleitung nur eigener Zweig.
- Abnahme: Klasse mit 25 Kindern und 20 Kompetenzen → Tabelle mit Prozent und Farbstufe plus Text je Zelle; Filter „braucht Unterstützung“ zeigt nur Kinder und Kompetenzen mit Markierung; Lehrkraft einer fremden Klasse → 404; Ansicht bei 390 px ohne waagerechten Seitenbildlauf (Tabelle im eigenen Rahmen scrollbar).

#### NOT-040 · Lernplan und Wochenplan
`P1` · `Status: Ist` (Klassenweise Anlage in der Oberfläche offen)

- Lernplan-Ziel je Kind (Tabelle `comp_plans`): Titel (verschlüsselt), Notiz (verschlüsselt), Woche (Montag der Woche), Fälligkeitsdatum, Status `offen` → `in_arbeit` → `erledigt` (Klick schaltet zum nächsten weiter), Quelle `lehrkraft` oder `schueler`, optional Kompetenz oder Material/Aufgabe. Lehrkraft und Kind tragen Ziele ein, das Kind hakt ab; Schüler/innen pflegen eigene Ziele und den Status aller Ziele; Eltern sehen lesend.
- Anzeige gruppiert nach „diese Woche“, „nächste Wochen“, „ohne Woche“, „frühere Wochen (offen)“, „erledigt“. Ziele für mehrere Kinder gleichzeitig kann die Schnittstelle (Lernpläne für ganze Klassen: NOT-047). Höchstzahl der Pläne je Kind ist begrenzt. [unklar: Zahlenwert nicht in der Quelle]
- Abnahme: Ziel für Woche 42 anlegen → erscheint unter „diese Woche“, Klick auf Status → „in Arbeit“, erneut → „erledigt“ und in „erledigt“; Kind legt eigenes Ziel an (`schueler`); Eltern-Konto ändert Status → 403; Titel im Datenbankauszug nur Chiffrat.

#### NOT-041 · Abzeichen
`P2` · `Status: Ist` (Open-Badges-Export offen)

- Abzeichen (Tabelle `comp_badges`): Name (höchstens 100 Zeichen), Beschreibung (höchstens 300), Symbol aus 12 eingebauten Zeichnungen (`star` Standard, `medal`, `trophy`, `flag`, `book`, `calculator`, `pencil`, `puzzle`, `bulb`, `heart`, `leaf`, `rocket`), Farbe (`gold` Standard, `silver`, `bronze`, `blue`, `green`, `red`, `purple`), Kriterien (leer = nur manuell), aktiv ja/nein. Kein Bild-Upload.
- Vergabe-Kriterien (Mindeststufe 1 bis 6): `competencies` – alle gewählten Kompetenzen (1 bis 100) mit Stufe ≥ Mindeststufe; `area` – Anteil der Kompetenzen des Bereichs mit Stufe ≥ Mindeststufe (1–100 %, Standard 100); `framework` – Anteil der Kompetenzen des Rahmens (1–100 %, Standard 100). Kriterien werden als Text beschrieben („Stufe n in k Kompetenz(en): …“, „Stufe n bei p % der Kompetenzen im Bereich/Rahmen „…““).
- Manuell vergeben oder entziehen (`competency.assess`); Definition und automatische Prüfung auf Abruf „Automatische Abzeichen prüfen“ (`competency.manage`). Automatisch wird nur nach Lehrkraft-Einschätzung oder Bestätigung geprüft (nie nach Selbsteinschätzung), nur aktive Abzeichen mit Kriterien, die die Person noch nicht hat; Vergabe mit Datum des Tages, Kennzeichen „automatisch“, ohne Notiz. Je Abzeichen und Schüler/in höchstens eine Vergabe (Tabelle `comp_badge_awards`, Notiz verschlüsselt). Vergebene Abzeichen bleiben, bis eine Lehrkraft sie zurücknimmt. Anzeige im Panel der Schülerin bzw. des Schülers (Schüler- und Elternseite).
- Abnahme: Kriterium „Bereich 100 % Stufe 3“: letzte Kompetenz des Bereichs wird von der Lehrkraft auf 3 gesetzt → Abzeichen automatisch vergeben, Datum heute, Kennzeichen automatisch; Selbsteinschätzung 4 → keine Vergabe; manuelles Abzeichen ohne Kriterien → nie automatisch; Zurücknehmen → Abzeichen weg und wird nicht erneut automatisch vergeben, solange keine neue Einschätzung folgt [unklar: Verhalten bei erneuter Prüfung nach Rücknahme nicht beschrieben].

#### NOT-042 · Lernentwicklungsbericht (PDF)
`P1` · `Status: Ist`

- A4, mehrseitig, je Schüler/in; Grundlage für Zeugnisbemerkungen und Lernentwicklungsgespräche, kein Zeugnis (NOT-028). Inhalt: Kopf (Name, Klasse, Datum); je Rahmen Stufenlegende und Fortschritt in Prozent; je Bereich Fortschritt; je Kompetenz Stufenkästchen (Lehrkraft), Selbsteinschätzung „Ich: <Stufe>“ mit Datum und der letzte Kommentar (höchstens 240 Zeichen); Abzeichen; Lernplan (offene Ziele, höchstens 12); Platz für 5 Bemerkungslinien zum Gespräch. Beobachtungsnotizen werden nie aufgenommen. Fußzeile „Vertraulich – nur für Lehrkräfte und Eltern bestimmt“. Layout: Kastengröße 9 pt, Zeilenhöhe 11 pt, Titelbreite 300 pt.
- Erzeugen darf die Lehrkraft mit `competency.read` (Umfang eigene Klassen); Schüler/innen und Eltern erhalten 404. Jede Erzeugung steht im Audit (`competency.report`). Alle Zeichen müssen in der PDF-Schrift darstellbar sein.
- Abnahme: Bericht für ein Kind mit zwei Rahmen → mehrere A4-Seiten mit allen genannten Teilen; enthält keine Beobachtungsnotiz; als Eltern-Konto → 404; Audit-Zeile `competency.report` ohne Inhalte.

#### NOT-043 · Verknüpfung mit Kursraum-Elementen
`P2` · `Status: Ist` (Oberfläche im Kursraum offen, NOT-047)

- Beliebige Elemente (Aufgaben, Material, Beiträge anderer Bereiche) werden mit Kompetenzen verknüpft über Elementtyp (frei wählbar `[a-z][a-z_]{0,29}`, vereinbart `channel_item`) und Elementkennung (Tabelle `comp_links`, eindeutig je Kompetenz, Typ, Kennung). Setzen mit `competency.assess` (ersetzt die Zuordnung des Elements); lesen dürfen alle Angemeldeten der genannten Gruppen (Titel, Rahmen, Bereich). Andere Bereiche wählen eigene Typen ohne Eingriff in fremde Tabellen.
- Ein Lernstand-Nachweis kann ein Element sein: Nachweisart `assignment` oder `material` mit Verweis `channel:<Kanal-Kennung>` (führt in den Kursraum).
- Abnahme: Aufgabe einer Kompetenz zuordnen → `GET` der Verknüpfungen liefert Titel, Rahmen und Bereich; Lernstand mit Nachweis `assignment`/`channel:12` → Link führt in den Kursraum; Schüler-Konto setzt Zuordnung → 403.

#### NOT-044 · Rechte und Sichtstufen der Kompetenzen
`P0` · `Status: Ist`

| Recht | Wirkung | Standardrollen (Datenumfang) |
|---|---|---|
| `competency.read` | Klassenübersicht, Lernstand, Lernpläne, Abzeichen, Bericht lesen | Schulleitung, Lehrkraft (eigene Klassen), Abteilungsleitung (eigener Zweig) |
| `competency.assess` | Stufen setzen, Selbsteinschätzungen bestätigen, Lernpläne führen, Abzeichen vergeben, Zuordnungen setzen | wie `read`, gleicher Umfang |
| `competency.manage` | Rahmen, Vorlagen, Schul-Abzeichen verwalten, automatische Prüfung; ohne Einblick in Lernstände | Schulleitung, Lehrkraft, Abteilungsleitung |

- Sichtstufen eines Lernstands: `staff` (Lehrpersonal: alles, auch Beobachtungsnotizen und Unterstützungsmarkierung), `self` (Schüler/in: eigene Daten; darf Selbsteinschätzung und eigene Lernplan-Ziele pflegen), `family` (Eltern je Kind: nur lesen, wie Schülersicht). Schüler/innen und Eltern haben kein Recht, sondern sehen ihr Kind; Eltern volljähriger Kinder nur mit Freigabe im Bereich „Kompetenzen“ (KLB-005); fremde Kinder 404.
- Die technische Administration hat keines der drei Rechte; Zuschauer/Ansichtskonten sind ausgeschlossen. Rahmen, Abzeichen-Katalog und Zuordnungen zum Lehrstoff sehen alle Angemeldeten der genannten Gruppen.
- Abnahme: Matrix-Test Rolle × Recht × (eigene, fremde Klasse): Lehrkraft eigene Klasse 200, fremde 404; Administration 403; Eltern minderjähriges Kind lesen 200, Schreiben 403, Eltern Volljähriger ohne Freigabe 404; Antwort für `self` und `family` enthält weder `note`-Nachweise noch die Unterstützungsmarkierung.

#### NOT-045 · Seiten und Oberfläche der Kompetenzen
`P2` · `Status: Ist`

- `/kompetenzen` (Recht `competency.read` oder `competency.manage`), Menüeintrag „Kompetenzen“: Reiter Klassenübersicht, Lernstand je Kind, Rahmen (Anlegen, aus Vorlage, Import mit Vorlagen- und Import-Dialog, Bearbeiten, Export, Archivieren), Abzeichen (Definition mit Symbol, Farbe und Kriterien, manuelle Vergabe, automatische Prüfung). Dialog „Stufe setzen“ (Datum, Nachweis, Kommentar) bzw. Selbsteinschätzung bestätigen.
- `/lernstand` (Menüeintrag „Lernstand“, ohne Recht): Schüler/innen schätzen sich selbst ein (kindgerecht, einfache Sprache, Anrede „Sie“ gemäß Projektregel – der Altbestand verwendet „du“ im Schülerprofil und ist anzupassen); Eltern sehen den Lernstand je Kind nur lesend; volljährige Kinder geben für Eltern frei. Lernplan nach Wochen gegliedert, Abzeichen mit eingebauten Zeichnungen.
- Barrierefreiheit: Stufen sind nicht nur über Farbe unterscheidbar (Legende mit Beschriftung); Tastaturbedienung; 390 px ohne waagerechten Seitenbildlauf.
- Abnahme: Schüler-Konto öffnet `/lernstand` → eigene Kompetenzen, Selbsteinschätzung setzbar, keine Unterstützungsmarkierung; Eltern-Konto → lesend; Lehrkraft `/kompetenzen` → vier Reiter; Texte enthalten kein „du“; Browserabnahme von Abzeichen, Lernplan und Elternansicht auf PC und 390 px (bisher nur Tests).

#### NOT-046 · Datenschutz der Kompetenzen
`P0` · `Status: Ist` (Bereinigung offen)

- Verschlüsselt (gebunden an Tabelle, Feld, Datensatz): Nachweis (Beobachtungsnotiz bzw. Link), Kommentar, Lernplan-Titel und -Notiz, Notiz zur Abzeichen-Vergabe. Lernstände sind Schülerdaten und werden nie über die offene API freigegeben.
- Audit jeder Schreibaktion ohne Inhalte, nur Zählungen und Kennungen: `competency.framework.create|update|archive|delete|import`, `competency.assess`, `competency.self`, `competency.confirm`, `competency.plan.create|update|delete`, `competency.badge.create|update|delete|award|revoke|evaluate`, `competency.links`, `competency.report`.
- Aufbewahrung: Lernstände, Lernpläne und Abzeichen-Vergaben werden 180 Tage nach Austritt gelöscht (KLB-063/NOT-027). Offen (P1, Status: offen): Wird ein Kind aus den Stammdaten entfernt, bleiben seine Lernstände bestehen; der Neubau bereinigt sie automatisch (wie Klausurnoten).
- In der Demo sind Kompetenz-Import und -Verwaltung gesperrt (Demo-Schutz); Demo-Werte sind erfunden.
- Abnahme: Datenbankauszug der Spalten Nachweis/Kommentar/Titel/Notiz nur als Chiffrat; jede der genannten Aktionen erzeugt genau eine Audit-Zeile ohne Text; Kind aus Stammdaten entfernen → nach der Frist sind Lernstände, Pläne, Vergaben weg; Demo: Kompetenz-Import → 403.

#### NOT-047 · Offene Kompetenz-Funktionen
`P2` · `Status: offen`

- Zuordnungs-Chips in der Kursraum-Oberfläche (Aufgaben und Material): beim Anlegen eines Nachweises eine Aufgabe oder ein Material auswählen; Verbindung Kursraum ↔ Kompetenzen.
- Schüler-Startseite mit Kachel „Mein Wochenplan“ und Benachrichtigung bei offener Selbsteinschätzung.
- Mehrere Kinder gleichzeitig einschätzen und Lernplan-Ziele für ganze Klassen in der Oberfläche (die Schnittstelle kann es).
- Open-Badges-Export der Abzeichen.
- Abnahme: Beim Anlegen eines Nachweises ist eine Kursraum-Aufgabe wählbar und führt später in den Kursraum; Schüler-Startseite zeigt „Mein Wochenplan“; Lehrkraft setzt Stufe 3 für 10 Kinder in einem Dialog; Abzeichen als Open-Badge-Datei exportierbar.

#### NOT-048 · Reformpädagogik: individuelle Wochenpläne, Beobachtung, Berichtszeugnis
`P2` · `Status: offen` (Kern teilweise gebaut)

- Individuelle Wochenpläne je Kind (Werkzeug W-09 des Montessori-Testlaufs, Priorität B): Lernbegleitung öffnet Kind → Wochenplan mit Wochenzielen, Darbietungsterminen (mit Lehrkraft und Raum, im Lernzeit-Block eingebettet), Pflichtanteilen; Kind und Eltern sehen und bestätigen; Wochenrückblick; Lerntagebuch. Gebaut ist der Lernplan (NOT-040) ohne Darbietungstermine und Pflichtanteile.
- Lernentwicklung und Dokumentation (W-23, Priorität C): je Kind Raster und Beobachtungen pflegen (Ist: Kompetenzraster und Lernstand), Gespräche planen (Termine im Kalender), Berichtszeugnis aus Bausteinen erzeugen (nicht gebaut), Wortzeugnis; Lernentwicklungsgespräch mit Kompetenzpool, Ich-/Du-Bögen (Anrede „Sie“ beachten), Symbolsets und PDF mit Schullogo (nur GS/MS BY; Marktvergleich).
- Abnahme: Lernbegleitung legt für ein Kind einen Wochenplan mit einer Darbietung (Lehrkraft, Raum, Zeitfenster) an → Kind und Eltern sehen sie und bestätigen; Berichtszeugnis aus Bausteinen als PDF erzeugbar; Gesprächstermin erscheint im Kalender.

## B5. Förderinformationen und Nachteilsausgleich

#### NOT-049 · Förderkatalog der Schule
`P1` · `Status: Ist`

- Die Schule pflegt einen Katalog der Merkmale und Nachteilsausgleiche (Tabelle `support_catalog`; Dialog „Katalog“ unter Stammdaten → Schüler/innen; Recht `support.catalog`: Administration, Schulleitung, Sekretariat – ohne Einblick in Schülerdaten). Felder: Bezeichnung (höchstens 120 Zeichen), Art (`nachteilsausgleich`, `schulbegleitung`, `foerderplan`, `sonstiges`), „mit Minuten“ (`uses_minutes`), Standardminuten, „für Lehrkräfte sichtbar“ (`teacher_visible`, Standard ja), aktiv (Standard ja), Sortierwert. Anlegen, ändern, löschen. Beim ersten Aufruf wird sichergestellt, dass ein Katalog mit Standardeinträgen existiert.
- Standardbestand (11 Einträge, alle aktiv):

| Bezeichnung | Art | mit Minuten | Standardminuten | für Lehrkräfte sichtbar |
|---|---|---|---|---|
| Zeitzuschlag | nachteilsausgleich | ja | 15 min | ja |
| Wörterbuch/Duden erlaubt | nachteilsausgleich | nein | – | ja |
| Eigener Raum | nachteilsausgleich | nein | – | ja |
| Pausen/Bewegungspausen | nachteilsausgleich | nein | – | ja |
| Vergrößerte Schrift/Lesehilfe | nachteilsausgleich | nein | – | ja |
| Laptop/Tablet erlaubt | nachteilsausgleich | nein | – | ja |
| ADHS | sonstiges | nein | – | nein |
| Körperliche Behinderung (k) | sonstiges | nein | – | nein |
| Geistige Behinderung (g) | sonstiges | nein | – | nein |
| Förderbedarf Lernen | foerderplan | nein | – | nein |
| Schulbegleitung | schulbegleitung | nein | – | nein |

- Regel Sichtbarkeit: `teacher_visible` = ja – Lehrkräfte sehen Art, Minuten, Fächer und Hilfsmittel (Ausgleichsart); `teacher_visible` = nein (Diagnose- oder Förderbedarfsmerkmal) – nur Klassenleitung, Verwaltung und Familie sehen den Eintrag. Die Bezeichnungen sind kein erzwungen eindeutiger Schlüssel. [unklar: Wirkung von `active` im Auswahl-Ablauf]
- Abnahme: Neue Schule → Katalog mit 11 Standardeinträgen; Eintrag „Eigenes Hilfsmittel“ anlegen → in der Auswahl der Förder-Einträge verfügbar; Lehrkraft ruft Katalog-Änderung auf → 403; Sekretariat ändert Katalog → 200, sieht aber keine Förder-Einträge von Kindern ohne `support.read`.

#### NOT-050 · Förder-Einträge je Schüler/in
`P1` · `Status: Ist` (Bearbeiten-Dialog: NOT-053)

- Zitat: Nachteilsausgleich und Schulbegleitung pro Schüler eintragen, z. B. „eine PDF … wo dann drin steht, was für einen Nachteilsausgleich der kriegt“; Dokumente für Schüler hinterlegen (2026-10-11 17:55).
- Schülerdetail (Stammdaten → Schüler/innen, Abschnitt „Förderung & Nachteilsausgleich“): Merkmale aus dem Schulkatalog auswählen, Einträge anlegen (Art `nachteilsausgleich` Standard, `schulbegleitung`, `foerderplan`, `sonstiges`), Text erfassen, Dokumente (PDF/Dateien) anhängen, löschen. Zusätzlich im Schülerdetail: Eltern, Klassenleitung und Fachlehrkräfte je Fach; in der Schülerliste eine Spalte „Merkmale“ (Förder-Kennzeichen für Personal mit `support.read|hints`).
- Tabelle `student_support`: Schüler-Kennung; Art; Titel, Details und Hilfsmittel (verschlüsselt); Gültig ab/bis (`JJJJ-MM-TT`; leer = unbefristet [unklar: Quelle schweigt]); angehängte Dokumente (verschlüsselte Ablage, Verweistyp `student_support`); Katalogeintrag; Zeitzuschlag in Minuten (übernimmt den Standard des Katalogs [unklar: Übernahme beim Anlegen nicht belegt]); Fächer (leer = alle Fächer); anlegende Person; Zeitpunkte.
- Schulbegleitung: Das Konto der Schulbegleitung sieht die zugewiesenen Schüler/innen; mehrere Kinder sind gleichberechtigt (Altsystem: nur ein Hauptbezug, offen, NOT-053).
- Abnahme: Klassenleitung legt für ein Kind „Zeitzuschlag 15 min, Deutsch, Duden“ mit PDF an → Eintrag in der Schülerliste als Merkmal sichtbar, PDF im Datenbankauszug und in der Ablage verschlüsselt; Eintrag mit Gültig bis gestern wird in der Klausuranzeige nicht berücksichtigt [unklar: Auswertung von Gültigkeit nicht belegt – Test festlegen]; Titel nur als Chiffrat.

#### NOT-051 · Sichtbarkeit und Schutz der Förderdaten
`P0` · `Status: Ist`

- Korrektur 2026-10-12 (Betreiber-Hinweis): Vorher sahen alle Fachlehrkräfte Förder- und Dokumentdaten, und die Verwaltung konnte sie bearbeiten. Jetzt gilt: Vollansicht (Details, Diagnose, Dokumente) haben Schulleitung, Sekretariat, die Klassenleitung der eigenen Klasse sowie Schüler/in (volljährig) und Eltern (nur bei minderjährigen Kindern; Förder- und Unterstützungsdaten gehören nicht zur Elternfreigabe Volljähriger). Fachlehrkräfte sehen ausschließlich unterrichtsrelevante Hinweise (Art, Zeitzuschlag, Fächer, Hilfsmittel) aus Katalogeinträgen mit `teacher_visible` = ja; ADHS, Behinderung, Förderbedarf und Schulbegleitung nie. Die technische Administration hat keinen Zugriff (auch nicht ändern). Zuschauer-Konten sind abgewiesen. Gesundheitsdaten nie an Fachlehrkräfte; Dokumente werden nie gelöscht, nur archiviert; Entfernen nur über die Aufbewahrungsregel.
- Rechte: `support.read` (Förderbedarf, Nachteilsausgleich, Nachweise lesen: Schulleitung, Sekretariat, Lehrkraft und Abteilungsleitung mit Umfang „eigene Klassenleitung“), `support.manage` (Einträge und Nachweise anlegen/löschen: Schulleitung, Sekretariat, Klassenleitung), `support.hints` (Hinweis bei Klausuren, eigene Kurse), `support.catalog` (NOT-049). Jeder Zugriff auf Förderdaten und Dokumente wird im Audit protokolliert; fremde Schüler-Kennungen liefern 404 (Paket „404 für fremde Daten“, 42 Testfälle 2026-10-16).
- Aufbewahrung: 30 Tage nach Austritt, keine laufende Frist; Löschen von Einträgen und aller zugehörigen Dateien; Auskunft: Förderdaten nur für minderjährige Kinder an die Eltern (KLB-064).
- Abnahme: Fachlehrkraft ruft Förder-Einträge eines Kindes ab → 403 bzw. 404; sie sieht in der Klausuranzeige nur „+15 Min., Duden“; Eintrag „ADHS“ nie; Administration → 403; Klassenleitung eigener Klasse 200, fremde Klasse 404; jeder Abruf erzeugt eine Audit-Zeile; Eltern eines Volljährigen sehen keine Förderdaten.

#### NOT-052 · Nachteilsausgleich in Aufgaben, Notenbuch und Nachschreiben
`P2` · `Status: Ist`

- Wo Zeitzuschläge wirken, erscheint der Nachteilsausgleich ausschließlich als Hinweis „NTA“ ohne Diagnose: im Klausurdetail und in der Klausurübersicht (NOT-007), im Dialog „Frist verlängern“ einer Aufgabe im Kursraum (KUR), in der Notenbuch-Einsicht (NOT-024) und bei der Terminfestlegung des Nachschreibens (KLB-054: „NTA n“ und „fehlt n“ in der Klausurstunde).
- Abnahme: Aufgabe mit Frist, Kind mit Zeitzuschlag → der Dialog „Frist verlängern“ zeigt „NTA +15 Min.“; Notenbuch-Ansicht der Lehrkraft zeigt „NTA“ am Namen; keiner der Texte nennt eine Diagnose.

#### NOT-053 · Offene Förderfunktionen
`P2` · `Status: offen`

- Dialog zum Bearbeiten bestehender Förder-Einträge (bisher nur Anlegen und Löschen).
- Erinnerung im Wochenkalender: In der Stunde mit Klausur erscheint für die Lehrkraft der Nachteilsausgleich-Hinweis (NOT-007), auch im Wochenplan.
- Antrag auf Nachteilsausgleich als Formularvorlage (FOR), Weg Schüler/Eltern → Lehrkraft → Vorgesetzte (Zitat 2026-10-12 21:08: „Sowas soll bitte auch die Kinder zu den Lehrern, sollen die Lehrer zu den höhergestellten da antworten.“).
- Schulbegleitung für mehrere Kinder gleichberechtigt (heute erstes Kind als Hauptbezug, weitere nur in einer Liste).
- Begriff klären: Förderart `sonstiges` im Datenmodell, „Merkmale (mit Nachweisen)“ in Oberfläche und Routen. [unklar: gleiche Sache?]
- Abnahme: Förder-Eintrag nachträglich ändern → Version im Audit, Dokument bleibt; Wochenplan der Lehrkraft zeigt am Klausurtag „NTA 2“ in der Stunde; Antrag über Formular erzeugt Vorgang bei der Klassenleitung; Schulbegleitung mit drei Kindern sieht alle drei gleichwertig.

## B6. Qualität, offene Entscheidungen, Referenz

#### NOT-054 · Prüfbarkeit der Bereiche Noten, Kompetenzen, Klausuren
`P1` · `Status: Ist` (Testumfang laut Vorgängerbestand)

- Automatische Tests decken ab: Berechnungen (Skalen, Schlüssel „ab“-Regel, gewichteter Schnitt, Vorschlag, Versetzungswarnung, Fortschritt), Rechte-Matrix je Rolle und Datenumfang (Notenbuch, Klausurergebnisse, Kompetenzen, Förderdaten), Klausur-Regelprüfung und Höchstzahlen, Nachschreib-Abgleich und Terminvorschläge, Verschlüsselung (Chiffrat, nicht lesbar → Konflikt), Rundlauf Import/Export der Rahmen, Export-Format (BOM, CRLF, Dezimalkomma, Formelschutz) und Frontend-Logik (Anzeige, Kürzel, Spaltenfolge, Tastaturbewegung). Vorgängerbestand: 107 Notenbuch-Tests, 59 Klausur-Ergebnis-Tests, 28 Klassenbuch-Tests, 42 Förder-Tests.
- Tests dürfen nicht vom echten Kalenderdatum abhängen (Prüfbefund: ein Beurlaubungstest scheiterte an den Herbstferien); alle datumsabhängigen Tests laufen mit fester Uhr (Europe/Berlin).
- Demo: Notenbücher der Demoklassen mit vollständigen erfundenen Werten; Demo-Tests prüfen, dass keine realen Personen enthalten sind.
- Abnahme: Die Testsuite enthält je Anforderung dieses Teils mindestens einen Test mit der Abnahmezeile; ein Lauf mit verschobener Systemuhr ändert kein Ergebnis; die Demo-Instanz enthält keine echten Namen.

#### NOT-055 · Browserabnahme der nur per Test geprüften Funktionen
`P1` · `Status: offen`

- Folgende Funktionen sind im Vorgängerbestand nur durch Tests, nicht im Browser geprüft; der Neubau nimmt sie vor der Freigabe im Browser (PC 1280 px und Handy 390 px, hell und dunkel, Tastatur) und – bei Familienfunktionen – als Eltern, Eltern mit mehreren Kindern und Volljährige ab: Notenbuch-Eingabe am Handy; Lernstand, Abzeichen, Lernplan, Elternansicht der Kompetenzen; Attest-Freigabe; Krankmeldung mit Dateien; Verlängern einer Krankmeldung; Verlängern und Rückgabe einer Beurlaubung; Nachschreib-Termine; Klausur → Kursraum bei Eltern mit mehreren Kindern; „Attest einreichen“ auf der produktiven Domain.
- Abnahme: Eine Abnahmeliste mit allen genannten Punkten liegt vor; jeder Punkt ist mit Datum, Gerät, Rolle und Ergebnis abgehakt; kein Punkt führt zu waagerechtem Seitenbildlauf bei 390 px.

### B6.1 Offene Entscheidungen (Teil B, keine Anforderungen)

| Nr | Frage | Stand der Quellen |
|---|---|---|
| E-B1 | Standard der Notenbuch-Einsicht (NOT-023/024) | Entscheidung 2026-10-16 „nach Freigabe“ (vom Betreiber nicht bestätigt), Altsystem `sofort` |
| E-B2 | Bewertung entschuldigt/unentschuldigt im Notenbuch (NOT-021) | Claude-Entwurf 2026-10-16, Betreiber widersprach nicht |
| E-B3 | Ein Notenschlüssel für Aufgaben und Notenbuch (NOT-012)? | Aufgaben 92/81/67/50/30 %, Notenbuch 87/73/59/45/18 % |
| E-B4 | `0` bei Klausur-Höchstzahlen = „keine Grenze“ (NOT-004) | Bestätigung steht aus |
| E-B5 | Kopfnoten, Zeugniskonferenz, Lernentwicklungsgespräch bauen oder nur Daten an SchILD/ASV liefern (NOT-029) | nicht ausdrücklich abgelehnt; Quellen empfehlen Prüfung nach dem Notenbuch |
| E-B6 | Verfügbarkeit der ENM-/SVWS-Formatbeschreibung; welche Länder zuerst (NOT-030) | offen |
| E-B7 | Hauptfach-Kennzeichen und genaue Zählweise der Versetzungswarnung (NOT-016) | nicht beschrieben |
| E-B8 | Löschregeln für Notenbücher; Fristen für Zeugnislisten nach Landesrecht (NOT-009/027/031) | nicht belegt |
| E-B9 | Empfänger der Benachrichtigung beim Sperren (NOT-017) | nicht belegt |
| E-B10 | Elterneinsicht in Klausuren Volljähriger: Bereich „Stundenplan“ oder eigener Bereich (NOT-001) | Backlog nennt eigenen Bereich, Freigabeliste nicht |
| E-B11 | Wirkung von `active`, Gültigkeit und Standardminuten der Förder-Einträge (NOT-049/050) | nicht belegt |
| E-B12 | Mindestregel „Administration sieht keine Atteste“ unabdingbar (KLB-008) | Betreiber-Entscheidung offen |

### B6.2 Referenz: Routen und Schnittstellen des Vorgängerbestands (nicht bindend; Präfix `/api/v1`)

| Bereich | Routen (Methode Pfad) |
|---|---|
| Fehlzeiten | `GET|POST /student-absences` · `GET /student-absences/access|preview|record|form.pdf|leave-form.pdf` · `PATCH|DELETE /student-absences/{id}` · `POST /student-absences/{id}/shorten|extend|request-withdrawal|return-leave` · `GET /student-absences/{id}/history` · `GET /channels/{kanal}/klasse/absences` |
| Statistik | `GET /absence-stats` (`student_absence.read` oder `report`) · `GET /absence-stats/class` (`read`) · `GET /absence-stats/week` |
| Dokumente | `GET|POST /student-documents` · `GET /student-documents/summary` · `PATCH|DELETE /student-documents/{id}` (Seite `/dokumente`) |
| Klassenbuch | `GET /register/classes|day|now|overview` · `PUT /register/lesson` (Seite `/klassenbuch`) |
| Klausuren | `GET|POST /exams` · `POST /exams/check` · `PUT|DELETE /exams/{id}` · `GET|PUT /exams/{id}/results` · `GET /exams/support-hints` |
| Nachschreiben | `GET /exam-makeups`, `/summary`, `/suggestions` · `POST /exam-makeups/dates` · `PUT|DELETE /exam-makeups/dates/{id}` · `PATCH /exam-makeups/{id}` (Seite `/nachschreiben`) |
| Notenbuch | `GET|POST /gradebook/books` · `GET|PATCH|DELETE /gradebook/books/{id}` · `POST …/lock|unlock` · `GET …/log` · `PUT …/finals` · `POST …/finals/apply-proposals` · `POST|PATCH|DELETE …/categories` · `POST|PATCH|DELETE …/items` · `PUT …/items/{id}/entries` · `GET …/sources` · `POST …/sources/adopt|dismiss|restore|sync` · `GET /gradebook/class/{id}` · `GET …/conference.pdf` · `GET /gradebook/courses|meta|export|my` · `PUT /gradebook/settings` · `GET /grades` (Seiten `/notenbuch`, `/notenbuch/:bookId`, `/notenbuch/klasse/:classId`, `/notenbuch/verwaltung`, `/noten`) |
| Kompetenzen | `GET|POST /competency/frameworks` · `GET|PUT|DELETE /competency/frameworks/{id}` · `POST …/archive` · `GET …/export` · `POST /competency/frameworks/import` · `GET /competency/templates` · `POST /competency/templates/{key}/use` · `POST /competency/assessments` · `POST /competency/self` · `POST /competency/self/{id}/confirm` · `GET /competency/overview` · `GET /competency/students/{id}` · `GET …/report.pdf` · `GET|PUT /competency/links` · `GET|POST|PATCH|DELETE /competency/plans` · `GET|POST|PUT|DELETE /competency/badges` · `POST …/award` · `DELETE …/award/{sid}` · `POST /competency/badges/evaluate` (Seiten `/kompetenzen`, `/lernstand`) |
| Förderung | `GET|POST|PUT|DELETE /students/{id}/support` · `GET /students/support-flags` · `GET|POST|PUT|DELETE /support/catalog` |

<!--ENDE-->
