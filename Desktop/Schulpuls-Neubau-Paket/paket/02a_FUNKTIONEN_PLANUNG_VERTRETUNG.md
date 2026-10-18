# 02a · Funktionen: Stundenplan und Generator (STP) · Vertretung, Aufsichten, Monitore (VER)

Quellenstand: bis 2026-10-18. Gilt für den Neubau des Schulverwaltungs- und Lernsystems („das System“; der Produktname steht nur in der zentralen Konfiguration). Sprache der Oberfläche: Deutsch, Anrede „Sie“ für alle Rollen einschließlich Schülerinnen und Schüler.

---

## 0. Lesehilfe

### 0.1 Geltung und Abgrenzung

- Diese Datei beschreibt WAS das System leisten muss und mit welchen Werten: Planungsdokument, Zeit- und Wochenmodell, Stundentafel, Kurse, Generator („Neuaufbau“), Regeln und Prioritäten, Qualitätsbericht, Planzeiträume, Plan-Stände, Dauerprüfung „Plan prüfen“, Stundenplan-Ansichten, gemeinsames Tage-×-Stunden-Raster (STP); Tagesvertretung, Abwesenheiten, Pausenaufsichten, Klausurprüfung und Nachschreibtermine, Monitore und Aushang (VER).
- Nicht hier geregelt (nur Verweis): Fehlzeiten, Atteste und Entschuldigungsverfahren (KLB); Noten (NOT); Stammdaten-Pflege, Jahrgänge, Schuljahreswechsel (STA); Lehrkraft-Profil, Verfügbarkeitseditor, Anträge (LEH); Rechtekatalog und Rollen (REC); Löschkonzept (DAT); Benachrichtigungszentrale (BEN); Import/Export-Formate und API (INT); Gestaltungssystem (OBE).
- Jede Anforderung hat eine feste Kennung (`STP-nnn`, `VER-nnn`, je Kürzel ab 001), eine Priorität (P0 Pflicht/Sicherheit/Recht · P1 Kernfunktion · P2 wichtig · P3 Wunsch), einen Status (`Status: Ist` = im Vorgängerbestand vorhanden und beizubehalten, `Status: offen` = gewünscht oder entschieden, aber noch nicht gebaut) und genau eine Zeile `Abnahme:`.
- `[unklar: …]` kennzeichnet Werte oder Wirkungen, die die Quellen nicht eindeutig belegen. Nichts wurde ergänzt.

### 0.2 Begriffe

| Begriff | Bedeutung | Hinweis zur Oberfläche |
|---|---|---|
| Stunde | Unterrichtsstunde im Zeitraster. Einzelstunde = 1 Stunde, Doppelstunde = 2 Stunden | Doppelstunden zählen überall als zwei Schulstunden |
| Block (intern) | zusammenhängend gelegte Einzel- oder Doppelstunde eines Kurses | In Oberflächentexten verboten; dort „Stunde“ bzw. „Doppelstunde“ |
| Kurs | Unterricht, der `hours`-mal je Woche stattfindet; kann mehrere Klassen und mehrere Kursteile haben | – |
| Kursteil / Kopplung | parallele Gruppe eines Kurses mit Fach, Lehrkraft, Raum, Schülerliste; alle Teile liegen in derselben Stunde | Sprechblase „N Kurse“ |
| Wochenmuster | Gruppe realer Wochen mit identischen Bedingungen (Rechenersparnis des Generators) | nie „Variante“ oder „variants“ |
| Strafpunkte | Kostenmaß des Generators, niedriger = besser | nie „Kosten“ |
| Neuaufbau (Generator) | vollständige Neuerzeugung eines Plans zum Schuljahr oder Zeitraum | – |
| Plan prüfen | Dauerprüfung des regulären Plans mit Planvorschlägen | Menüpunkt „Planvorschläge“ |
| Planzeitraum | Teil des Schuljahres mit eigenem Plan (Standard: Halbjahre) | – |
| Plan-Stand | benannte Sicherung der Unterrichtsstunden | – |
| Tagesplan | für einen Schultag berechneter wirksamer Plan aus regulärem Plan, Abwesenheiten, Terminen, manuellen Entscheidungen | wird berechnet, nicht gespeichert |
| Eintragsart | Art eines Eintrags im Tagesplan (Vertretung, Betreuung, Mitbetreuung, Entfall, Verlegung, Raumänderung, Klasse abwesend, Aufsicht, Klausur) | je Art eigene Farbfamilie |

### 0.3 Zählweisen und Formate

- Intern: Wochentag 0 = Montag … 6 = Sonntag; Stunde 0 = 1. Stunde. Anzeige: „1. Std.“; Wochen 1-basiert („Woche 12“). Datum TT.MM.JJJJ, Zahlen mit Dezimalkomma, Zahl und Einheit mit Leerzeichen („45 min“, „5 %“). Zahlen ganzzahlig, wenn ganzzahlig, sonst eine Nachkommastelle.
- Wochenangaben nur als Zahl, Liste oder Rhythmus. Wochenbuchstaben (A/B) und „Zyklus“ gibt es nicht; ein automatischer Test schlägt an, wenn sie wieder auftauchen.

### 0.4 Rechte in diesen Bereichen (Namen wie im Rechtekatalog; Standardrollen laut Standardrechten)

| Recht | Wirkung hier | Standardrollen |
|---|---|---|
| `timetable.generate` | Generator starten/abbrechen/löschen/übernehmen, Plan leeren, Teilneuplanung, Plan-Stände anlegen/wiederherstellen/löschen, Dauerprüfung starten und entscheiden, Zeiträume kopieren/löschen | Administration, Planer |
| `timetable.edit` | Stundentafeln, Kurse, Lehrkraft-Zuweisung, Stunden verschieben/fixieren, Aufsichten erzeugen, Qualitätsbericht und alle Pläne lesen | Administration, Planer |
| `settings.edit` | Einstellungen, Planzeiträume speichern, Regeln bearbeiten, Klausur-Vorgaben (Schule/Jahrgang), Plan prüfen lesen/entscheiden | Administration, Schulleitung, Planer |
| `masterdata.edit` | Fächer, Klassenwerte der Klausurgrenzen, Ferien-Import | Administration, Schulleitung, Sekretariat, Planer |
| `plans.read_all` | Klassen-, Lehrkraft-, Schülerpläne lesen (Umfang: eigene Klassen bzw. eigener Zweig) | Administration, Schulleitung, Sekretariat, Planer, Lehrkraft, Abteilungsleitung |
| `rooms.read` | Raumpläne und Raumbelegung | Administration, Schulleitung, Sekretariat, Planer, Hausmeister |
| `substitution.read` | Vertretungsplan lesen (nicht Schüler/innen, nicht Eltern) | Administration, Schulleitung, Sekretariat, Planer, Lehrkraft, Abteilungsleitung, Schulbegleitung |
| `substitution.edit` | Abwesenheiten erfassen, Vertretungen planen, manuell entscheiden, freigeben, Statistik | Administration, Schulleitung, Sekretariat, Planer |
| `absence.report_self` | Lehrkraft meldet sich selbst ab (Administration ausgeschlossen) | Lehrkraft, Abteilungsleitung |
| `substitution.self_study` | Eigenarbeit bei Ausfall freigeben (Status: geplant) | Administration, Schulleitung, Planer, Abteilungsleitung |
| `duties.manage` | Pausenbereiche, Verfügbarkeit, faire Verteilung der Aufsichten (Status: geplant) | Administration, Schulleitung, Planer |
| `monitor.read` | Vertretungsmonitor und Aushang anzeigen | Administration, Schulleitung, Sekretariat, Planer, Hausmeister, Monitor |
| `monitor.manage` | Monitore einstellen (Anzeigetage, Laufband, Hinweise) | Administration, Schulleitung, Sekretariat |
| `exam.edit` | Klausurtermine eintragen, prüfen, ändern, löschen (Umfang: eigene Kurse) | Administration, Schulleitung, Planer, Lehrkraft, Abteilungsleitung |
| `history.restore` | Planverlauf lesen, Version wiederherstellen, Rückgängig | Administration, Schulleitung, Planer |
| `audit.read` | Audit-Protokoll lesen | Administration, Schulleitung |

Notation in Abnahmezeilen: `a+b` = beide Rechte, `a|b` = eines davon. Fehlt einer Route das Recht: 403 mit Nennung des fehlenden Rechts, in der Oberfläche als Seite im App-Rahmen (nie als Serverfehler). Objekte außerhalb des Datenumfangs liefern 404.

### 0.5 Entschiedene Widersprüche der Quellen (spätere Entscheidung überstimmt frühere)

| Thema | Entscheidung für den Neubau | Grundlage |
|---|---|---|
| Automatik oder Auswahl bei Planproblemen | Keine automatische Planänderung. „Plan prüfen“ legt 2 bis 5 Lösungen zur Wahl vor; Menschen entscheiden. Einzige Ausnahme: Schulschalter `plan_auto_apply` = „raeume“ (Standard aus) | Betreiber 12.10. 20:53 überstimmt 11.10. („immer automatisch“) |
| Doppelstunde über Pause | Nie (harte Regel); Einstellung `double_alignment` Standard „bloecke“. Der Backlog-Schalter „doubles_across_breaks“ entfällt | Betreiber 11.10. 19:14; Pflichtanforderung A-30 |
| Krankmeldung ändert den Stundenplan | Nein, nur den Tagesplan. Strukturelle Folgen (Sperrzeiten, Raumausfall, Kursänderung) erzeugen Planvorschläge | 11.10. Entscheidung, ab 13.10. durch „Plan prüfen“ ergänzt |
| Vertretungsplan für Schüler/innen und Eltern | Nur Personal (`substitution.read`). Kinder und Eltern sehen Entfall, Vertretung, Raumänderung im eigenen Stundenplan | Betreiber 12.10. 18:03 |
| Anrede | „Sie“ überall, auch für Schüler/innen (Plan R3-B „du“ im Schülerprofil ist verworfen) | Projektregel |
| Wochen 52 oder 53 | Schuljahr hat 52 oder 53 Wochen; Wochenlisten erlauben 1 bis 53; Liste mit allen 53 gilt als „jede Woche“ | Quellen Z-Werte |
| Rhythmus je Klasse (Backlog B-45) | Entfällt. Wochenangaben gelten je Objekt (Kurs, Stunde, Sperrzeit, Aufsicht). Zeitraster/Tageszeiten je Klasse bleiben Wunsch (offen) | Betreiber-Änderung 11.10. |
| Legende | Die Textleiste der Terminarten (Pflichttermin, Termin, Klausur, Test, Hausaufgaben) entfällt. Die Farblegende des gemeinsamen Rasters bleibt | Betreiber 11.10. und Raster-Baustein 16.10. |
| Stundenplan drucken | Entfällt. Es bleiben: Vertretungs-Aushang (öffentliche Sicht), Zugangsbriefe, schriftliche Entschuldigung | Betreiber 12.10. 19:16 |
| Klausur-Grenze „0“ | 0 bedeutet „keine Grenze“ (Bestätigung durch den Betreiber steht aus) | Backlog B-02, Standardwert zur Bestätigung |
| Strafpunkt-Gewichte | Grundgewichte laut STP-034 sind Konfiguration (Quellen nannten für Springstunden 4 und 5) | Z-Werte: 4 |
| Rolle Schulleitung und Generator | Standard: Schulleitung hat `timetable.generate` nicht, Planer und Administration schon. Ob gewollt, hat der Betreiber nicht bestätigt (offen) | Standardrechte |
| Fremde Daten | 404; fehlende Rolle/Recht an der Route 403 | Projektregel |

---

## 1. Teil STP: Stundenplan und Generator

### 1.1 Zeit- und Kalendermodell

### STP-001 · Schuljahr und Schulwochen · P1 · Status: Ist
- Woche 1 ist die Mo–So-Woche, die den Schuljahresbeginn enthält. Laufende Woche = (Montag der Woche − Montag der Woche 1) / 7 + 1. Vor dem Schuljahr 0 oder negativ („keine Schulwoche“). Ferien zählen mit.
- Das Schuljahr endet am Sonntag vor dem Montag des nächsten Beginns, sonst Beginn + 1 Jahr; Anzahl Wochen Y = 52 oder 53. Heute > Y Wochen ohne eingetragenen neuen Beginn: Hinweis „Schuljahr abgelaufen. Tragen Sie den Beginn des neuen Schuljahres ein.“
- Einstellung `week_numbering`: „iso“ (Standard, nur Kalenderwoche) oder „school_year“ (Anzeige „Woche n · KW k“). Wochenkopf: „‹ Woche 12 · KW 45 · 02.11.–08.11. › Heute“, gruppiert nach Planzeitraum, mit Zeitraum-Badge und „Kein Stundenplan“.
- Betreiberwunsch (Wortlaut): „Woche 1, Woche 2 … bis Woche 52, dass man da durchgehen kann“; die aktuelle Woche ist vorausgewählt (aus dem angezeigten Schultag abgeleitet, nicht aus dem heutigen Datum). Der Wunsch „ab Woche 1 des Kalenderjahrs“ ist als KW-Anzeige mit fortlaufender interner Zählung und Option „Wochen ab Schuljahresbeginn“ umgesetzt; Bestätigung offen.
- Wochenbuchstaben und „Zyklus“ gibt es nirgends (Oberfläche, Eingabe, Export, Testdaten).
Abnahme: Schuljahresbeginn Mo 03.08.2026 → Mo 02.11.2026 ist Woche 14 (KW 45) und das Wochenkopf-Format zeigt „Woche 14 · KW 45 · 02.11.–08.11.“ bei `week_numbering` = „school_year“; ein Datum vor dem Beginn liefert Woche ≤ 0 und wird als „keine Schulwoche“ bezeichnet; ein Test schlägt fehl, sobald „Woche A“, „Woche B“ oder „Zyklus“ in Oberfläche, API-Antworten oder Exporten erscheint.

### STP-002 · Schuljahresbeginn automatisch oder eigener Wert · P1 · Status: Ist
- Einstellung `year_start_mode`: „auto“ (Standard) = Ende der Sommerferien, „own“ = Wert in `school_year_start`. Standard für neue Schulen (`cycle_start`): 1. August des Schuljahres, das heute enthält (ab 1.8. dieses Jahres, sonst 1.8. des Vorjahres).
- Erkennung (nur „auto“): Ferien der Art „ferien“ mit (a) Name enthält „Sommer“ und Ende in Monat 6–9, oder (b) Dauer ≥ 20 Tage und Ende zwischen 15.06. und 15.09. Beginn = erster Werktag (Mo–Fr) nach dem Ende. Je Kalenderjahr zählt das späteste Ende einer benannten Sommerferien-Angabe, ohne solche das späteste Ende einer erkannten Ferienangabe. Der letzte erkannte Beginn ≤ heute gilt.
- Neuer Beginn weniger als 300 Tage vom alten entfernt (Korrektur desselben Schuljahres, z. B. 31.08. → 24.08.): gespeicherte Wochenangaben werden um die Differenz in Wochen verschoben, damit Kalenderwochen gleich bleiben. 300 Tage oder mehr (neues Schuljahr): alter Beginn kommt in den Verlauf (`school_year_history`, höchstens 20 Einträge; Lücken über 400 Tage werden mit „Beginn + 1 Jahr“ gefüllt), Zählung beginnt mit Woche 1, Planzeiträume werden verschoben. Der nächste erkannte Beginn (≥ 300 Tage später, höchstens 53 Wochen) wird ebenfalls in den Verlauf übernommen.
- Änderung nur mit `settings.edit`, mit Vorschau des Kalenders und Rückfrage im App-Dialog; Vorschau nennt betroffene Stunden und Kurse.
Abnahme: Ferien „Sommerferien“ enden am 01.09. (Dienstag) → Beginn 02.09. und Woche 1 ist die Woche mit dem 02.09.; Korrektur des Beginns um 7 Tage verschiebt eine Wochenliste „Woche 5“ auf „Woche 6“, die Kalenderwoche bleibt; ohne `settings.edit` liefert das Speichern 403.

### STP-003 · Wochenangabe: jede Woche, ausgewählte Wochen, Rhythmus · P1 · Status: Ist
- Was nicht in jeder Woche gilt, hat entweder `weeks` (Liste laufender Wochen, 1-basiert) oder `rhythm`; beides leer = jede Woche. Gilt für Zeitregeln (Sperren/Wünsche), Kurse, Stunden, Pausenaufsichten, Zeitfenster. Ist ein Rhythmus gesetzt, werden `weeks` ignoriert.
- Rhythmus `{every, from_week, to_week}`: Woche w ist aktiv, wenn from_week ≤ w, (to_week = 0 oder w ≤ to_week) und (w − from_week) durch every teilbar ist. Standards bei fehlenden/ungültigen Werten: every = 1 (auch unter 1), from_week = 1 (auch 0), to_week = 0 (offen); nicht lesbare Werte: Regel gilt als aktiv. Intern kehrt `invert` das Ergebnis um (nur aus Zeitfenstern). Wertebereich: every 1–52 (Validierung bis 53), from_week 1–53, Wochenliste 1–53; Oberfläche und Server verwenden dieselben Grenzen (Befund: Oberfläche 1–4 gegen Server 8).
- Unbekannte laufende Woche (kein Datum zugeordnet): Regel gilt vorsichtshalber in jeder Woche.
- Editor: drei Modi „Jede Woche“, „Ausgewählte Wochen“ (Chips 1 bis N, mit Pfeiltasten, eine Tab-Station), „Rhythmus“ („jede 3. Woche ab Woche 10 bis Woche 30“); Textvorschau („Woche 1–2“); Tag-Chips Mo–So mit vollen Namen für Bildschirmleser. Bei regelmäßigem Abstand schlägt der Editor einen Rhythmus vor, übernimmt ihn nie automatisch.
- Altdaten mit A/B-Wochen werden verlustfrei umgewandelt (A → „jede 2. Woche ab Woche 1“, B → „ab Woche 2“).
Abnahme: Rhythmus every 2, from_week 2, to_week 0 ist aktiv in den Wochen 2, 4, 6 …, nicht in 1, 3; every = 0 wird zu 1 normalisiert; eine Regel mit `weeks` = alle 53 Wochen gilt als „jede Woche“; Eingabe every = 60 wird mit Meldung abgelehnt; Import eines Altdokuments mit Woche „A“ liefert „jede 2. Woche ab Woche 1“.

### STP-004 · Zeitregeln: Sperrzeiten und Wünsche · P1 · Status: Ist
- Zeitregel = Tage (0–6, leer = jeder Tag), Stunden (0-basiert, leer = ganzer Tag), Wochen oder Rhythmus, Notiz, optional `valid_from` (ISO-Datum; beim Speichern wird `valid_week` = Montag der Woche des Datums berechnet; die Regel wirkt erst ab dieser Woche, bei unbekannter Woche ignoriert).
- Verwendung: harte Sperrzeit einer Lehrkraft oder Klasse („nicht verfügbar“, auch nicht als Vertretung); weicher Wunsch einer Lehrkraft („möglichst nicht“, Gewicht `teacher_wish`).
- Eine Zeitregel trifft genau zu, wenn Gültigkeit, Wochenangabe, Tag und Stunde passen.
- Eine Regel ohne Auswahl (keine Tage, Stunden, Wochen) wird abgelehnt (422); der Editor speichert erst nach einer Auswahl oder dem ausdrücklichen „ganze Woche“. (Befund im Bestand: leere Regel sperrte die ganze Woche, der Bericht meldete nichts.)
- Zeitfenster/Arbeitszeitraster der Lehrkräfte werden in harte Sperrzeiten umgerechnet; deren Notiz beginnt mit „Zeitfenster“, eigene Sperren dürfen nicht damit beginnen.
Abnahme: Sperrzeit Lehrkraft Mi, Stunden 1–2, Wochen 2 und 4 trifft Mi 1. Std. in Woche 2 und nicht in Woche 3; eine Sperrzeit mit `valid_from` 14.10.2026 wirkt nicht in der Woche davor; POST einer Regel ohne Tage/Stunden/Wochen und ohne „ganze Woche“ liefert 422; eine eigene Sperre mit Notiz „Zeitfenster …“ wird abgelehnt.

### STP-005 · Unterrichtstage, Tagesarten, Ferien und Feiertage · P1 · Status: Ist
- Schulvorgabe `school_days` (Tage 0–6), leer = die ersten `days` Tage ab Montag (Standard `days` = 5, Mo–Fr). Je Klasse eigene Unterrichtstage (z. B. Berufsschultag, Samstag); leer = Schulvorgabe. Schultage nur über die Unterrichtstage der Klasse prüfen, nie über „Wochentag < Anzahl Tage“. Schulöffnungstag = Unterrichtstag mindestens einer Klasse.
- Ferien/Feiertage (`holidays`): Name, Zeitraum (inklusiv), Art ferien · feiertag · beweglich · schulfrei (Fehlt/unbekannt: „ferien“ im Namen → ferien, sonst feiertag), Herkunft/Signatur für Wiedererkennung beim Import. Ferien schlagen Unterrichtstag.
- Tagesart: unterricht · kein_unterrichtstag · ferien · feiertag. Grund bei Nicht-Schultag: Sa/So „Wochenende“, sonst „Kein Unterrichtstag“, Ferien/Feiertag mit Name (Standard „Ferien“). Ferienwoche = alle Unterrichtstage der Woche frei.
- „Nächster Schultag“ und Datumsnavigation springen über Ferien und freie Tage (z. B. 16.10. → 02.11.); die Kachel „Meine Tage“ muss Ferien ebenfalls überspringen (Befund: noch nicht).
- Änderung der Unterrichtstage zeigt zuerst eine Vorschau der Stunden und gekoppelten Kurse, deren Bedeutung sich ändert, und wird erst nach Bestätigung übernommen.
Abnahme: Klasse mit Unterrichtstag Samstag hat Samstag als Schultag, andere Klassen nicht; Datum in Ferien liefert Tagesart „ferien“ mit Namen; „Nächster Schultag“ ab Fr 16.10. liefert bei Herbstferien bis 31.10. den 02.11.; Änderung von `days` von 5 auf 4 zeigt vorab die betroffenen Stunden und speichert erst nach Bestätigung.

### STP-006 · Ferien- und Feiertags-Import · P2 · Status: Ist
- Länder/Regionen aus einer öffentlichen Quelle (SM_HOLIDAY_IMPORT, Standard 1 = an) auswählen; Vorschau der Änderungen mit Aktionen und Zusammenfassung; erst danach Übernahme. Recht `masterdata.edit`. Erneuter Import erkennt frühere Importeinträge über die Signatur und überschreibt keine von Hand angelegten Einträge.
- Ferienvorlagen je Bundesland (mindestens NRW 2026/27 und 2027/28 als Datei mit Quellenangabe) sind per Klick übernehmbar [Status: offen laut Backlog B-25]; Import aus iCal/CSV [offen]. Ohne eingetragene Ferien bietet das Anlegen eines Schuljahres die Vorlage an; der Qualitätsbericht warnt.
- Welche Daten an die Quelle gesendet werden (nur Land/Region/Jahr), ist zu dokumentieren.
Abnahme: Import-Vorschau für ein Bundesland listet neue/geänderte/unveränderte Einträge, ohne etwas zu speichern; erst „Übernehmen“ schreibt; ein von Hand angelegter Eintrag bleibt beim zweiten Import unverändert; ohne `masterdata.edit` 403. [unklar: Quelle und Format der öffentlichen Feiertags-Schnittstelle]

### STP-007 · Zeitraster und Pausen · P1 · Status: Ist
- Standardwerte: 10 Stunden je Tag (`periods`), Beginn 07:55, 08:45, 09:50, 10:40, 11:45, 12:35, 13:30, 14:20, 15:10, 16:00 (`period_times`), Stundendauer 45 min (`period_minutes`). Pausen (`breaks`: nach Stunde, Name, Minuten): nach Stunde 2 „Pause 1“ 20 min, nach Stunde 4 „Pause 2“ 20 min, nach Stunde 6 „Pause 3“ 45 min. Pausenbeginn = Beginn der Folgestunde − Pausendauer. Stundenbezeichnung „1.“, „2.“ … Pausen sind dicke Linien im Raster, auch am Nachmittag.
- [unklar: Standard-Pause 3 (45 min) passt nicht zu den Standardzeiten; zwischen Ende Stunde 6 (13:20) und Beginn Stunde 7 (13:30) liegen nur 10 min.] Die Zeitraster-Prüfung muss solche Widersprüche melden.
- Prüfung des Zeitrasters: Stunden dürfen sich nicht überlappen (Beginn + Stundenlänge ≤ nächster Beginn), Pausen dürfen nicht kürzer sein als die Lücke erlaubt, `period_times` hat genau `periods` Einträge, „Pause nach Stunde“ darf bis zur letzten Stunde reichen (Oberfläche und Server gleich; Befund: Server nur bis `periods` − 1), Schultage und Wochentagsnamen haben dieselbe Obergrenze (7). `core_latest_period` blockiert das Senken der Stundenzahl nicht, sondern wird angepasst (Hinweis).
- Die Pausen bilden die Blockgrenzen für Doppelstunden (STP-032).
- Änderungen am Zeitraster mit Auswirkung auf bestehende Stunden zeigen vorab eine Vorschau (Stunden, die nicht mehr ins Raster passen) und verlangen Bestätigung.
Abnahme: Raster mit Stunde 1 07:55 und Stundenlänge 45 min bei Beginn Stunde 2 08:30 wird mit Meldung „überlappt“ abgelehnt; Pause nach Stunde 10 (letzte) ist speicherbar; `periods` = 8 bei `core_latest_period` = 9 speichert und setzt den Wert auf 7 mit Hinweis; Zeitraster-Änderung nennt vorab betroffene Stunden.

### STP-008 · Zeitraster-Rechner und frei einstellbares Raster · P1 · Status: offen
- Die Schule stellt Beginn (7:50, 7:55, 8:00 oder frei), Stundenlänge (45, 60 oder frei, optional je Stunde) und Pausen (Name, Minuten, „trennt Doppelstunden“) ein; das System berechnet `period_times`. „Zeiten von Hand“ bleibt möglich; Altdokumente gelten als „von Hand“.
- Live-Vorschau der berechneten Zeiten (Endpunkt `POST /settings/period-times/preview`); nach einer Änderung werden Lehrkraft-Zeitfenster neu berechnet; der Qualitätsbericht meldet Stunden, die nicht mehr ins Raster passen.
- Mehrere Zeitraster/„Minuten-Stundenplan“ je Klasse oder Abteilung und Hitzefrei-Raster (abweichendes Stundenraster) sind Wünsche (siehe STP-103, STP-105).
Abnahme: Beginn 07:50, 45 min, Pausen 15 und 20 min nach Stunde 2 und 4 liefern lückenlose, überlappungsfreie Zeiten; 08:00 mit 60 min; unterschiedliche Längen je Stunde; Handeingabe bleibt möglich; ein Altdokument wird als „von Hand“ geladen.

### STP-009 · Schulkalender-Termine im Plan, Wochenende · P1 · Status: Ist
- Termine (`events`): Titel, Datum von/bis (Ende leer = Beginn), Uhrzeit von/bis (leer = ganztägig), Art „termin“ (Information) oder „pflicht“ (Anwesenheit Pflicht), Klassen/Klassenstufen (leer + leer = ganze Schule), Ort, Notiz, teilnehmende Lehrkräfte (fehlen im Unterricht, siehe VER-007). Termin betrifft eine Klasse, wenn Klassen und Klassenstufen leer sind oder die Klasse/Klassenstufe enthalten ist. Termine erscheinen im Plan der Betroffenen, auch am Wochenende.
- Der Plan zeigt 7 Tage (Mo–So). Tage ohne Unterricht sind schmal, abgeblendet bzw. schraffiert; Umschalter „Nur Unterrichtstage“. Betreiberwortlaut 11.10.: „dass Freitag, äh, Samstag und Sonntag im Plan drin stehen ... dass wenn da auch Events sind“; umgesetzt wurde „Sa/So immer sichtbar“. [unklar: Betreiber hat nicht bestätigt, ob Sa/So nur bei Terminen erscheinen sollen; Backlog B-32 verlangt „nur bei Terminen“.]
- Schüler/innen sehen Ferien, Tests, Klassenarbeiten, Hausaufgaben im Stundenplan und ob sie am Wochenende irgendwohin müssen. Der Tageskopf zeigt nur Feiertagsname, ganztägige Termine, Pflichttermine und nicht zuordenbare Reste, keine Text-Chips für Klausur/Test/Hausaufgabe (dafür Symbole in den Stundenfeldern).
- Samstagstermine (z. B. Tag der offenen Tür mit Art „pflicht“) sind planbar; Rechte zum Anlegen: Sekretariat/Schulleitung (alle), Lehrkräfte für eigene Klassen [offen laut B-26].
Abnahme: Termin „Tag der offenen Tür“ am Samstag, Art pflicht, Klasse 5a erscheint im Wochenplan von 5a am Samstag; ein Termin mit zwei teilnehmenden Lehrkräften 10:00–12:00 zeigt diese in den überschneidenden Stunden als abwesend (VER-007); der Tageskopf enthält keine Text-Chips „Test“/„Klausur“/„HA“.

### STP-010 · Tageszeiten und Zeitraster je Klasse · P2 · Status: offen
- Wunsch A-69: Abendklassen ab 16:00 mit eigener erster Stunde; Lehrkräfte, die früh und abends unterrichten, werden richtig behandelt; Konflikte nach Uhrzeit statt nach Stundennummer; Lehrkraft- und Raumplan chronologisch. Bestand: nur globales `period_times`.
- Zeitraster-Vorlagen je Klasse/Abteilung.
Abnahme: Klasse „Abend“ mit eigenem Raster 16:00–21:15 und Klasse „Tag“ mit 07:55-Raster teilen sich eine Lehrkraft; der Generator und die Konfliktprüfung erkennen eine echte Zeitüberschneidung nach Uhrzeit und erlauben unterschiedliche Stundennummern in überlappungsfreien Zeiten.

### 1.2 Planungsdokument, Versionen, Speicherung

### STP-011 · Planungsdokument · P0 · Status: Ist
- Ein Dokument je Schule enthält genau einen Einstellungsblock und diese Sammlungen: Standorte, Fächer, Lehrkräfte, Räume, Klassen, Schüler/innen, Stundentafeln, Jahrgangsprofile, Kurse, Stunden (Blöcke), Abwesenheiten, manuelle Entscheidungen (Overrides), Ferien/Feiertage, Aufsichtsbereiche, Pausenaufsichten, Klausuren, Termine, optional Monitoreinstellungen und Ferien-Import-Einstellungen. Alle Sammlungen werden immer gespeichert (auch leer).
- Konto- und Personenbezüge (Benutzer ↔ Lehrkraft/Schüler/Eltern) liegen nicht im Dokument, sondern in der Datenbank; die Verbindung läuft nur über Kennungen.
- Schreiben nur über den kontrollierten, versionierten Schreibweg (Recht prüfen → Eingabe prüfen → neue Version → Audit `plan.change` → Live-Ereignis `change` mit Bereich und betroffenen Daten). Lesen aus einer unveränderlichen Momentaufnahme. Fehler (4xx) werden vor dem Speichern geworfen; es entsteht keine Version, kein Ereignis.
- Neue Felder brauchen Standardwert, Prüfung, Verweisprüfung und Löschregel (Kaskade). Unbekannte Felder und Sammlungen werden beim Lesen verworfen (Vorwärtskompatibilität ist nicht gegeben; siehe STP-017).
Abnahme: ein Schreibversuch ohne passendes Recht liefert 403 und erzeugt keine Version; eine gültige Änderung erzeugt genau eine Version, einen Audit-Eintrag `plan.change` und ein Ereignis `change`; ein Dokument mit allen 17 Sammlungen wird verlustfrei serialisiert und wieder geladen.

### STP-012 · Versionierung und Aufbewahrung · P0 · Status: Ist
- Jede erfolgreiche Änderung erzeugt genau eine neue Version mit fortlaufender, nie wiederverwendeter Nummer. Ergibt die Änderung denselben Stand (Prüfsumme SHA-256 des JSON), entsteht keine Version, kein Audit-Eintrag, kein Ereignis.
- Je Version: Benutzer (leer = System), Nachricht (höchstens 500 Zeichen, längere werden gekürzt), Bereich (Liste, Standard „all“; feste Werte „init“, „restore“, „undo“), Ursprungsversion (nur bei Wiederherstellen/Rückgängig), Zeitpunkt (UTC).
- Jede Änderung arbeitet auf einer vollständigen Kopie; Leser sehen nie einen halben Zustand.
- Aufbewahrung `SM_KEEP_VERSIONS`: Standard 300, Minimum 2; nach jedem Speichern werden die ältesten darüber endgültig gelöscht. Verlauf: neueste zuerst, 50 Einträge je Seite, höchstens 1000 je Abfrage; geltende Version „aktuell“; Anzeigename = Benutzer-Anzeigename, sonst Benutzername, ohne Benutzer „System“.
- Audit-Aktionen je Version: `plan.init`, `plan.change`, `plan.replace` (Import/Demo), `plan.restore`, `plan.undo`, ferner `plan.generator_apply`, `plan.clear`, `plan.snapshot_restore`, `plan.proposal_accept`, `plan.proposal_discard`. Einträge enthalten Nachricht und Bereich, nie Inhalte personenbezogener Daten. Standardnachrichten: „Leeres Planungsdokument angelegt“; „Version N wiederhergestellt“; „Rückgängig: zurück auf Version N (Nachricht der Version N)“.
Abnahme: zwei identische Speicherungen nacheinander erzeugen eine Version; bei `SM_KEEP_VERSIONS` = 3 und 5 Änderungen bleiben die letzten 3 Versionen; Nachricht mit 600 Zeichen wird auf 500 gekürzt; Verlauf ohne Parameter liefert 50 Einträge, `limit` = 5000 höchstens 1000.

### STP-013 · Rückgängig und Wiederherstellen · P0 · Status: Ist
- Rückgängig erzeugt eine neue Version (Bereich „all“ + „undo“, Aktion `plan.undo`, Ursprung = Zielversion); nichts wird gelöscht. Wiederholtes Rückgängig geht Schritt für Schritt zurück.
- Zielversion: normale Änderung → jüngste Version mit kleinerer Nummer als die Basis; Rückgängig-Schritt (Ursprung N) → jüngste Version kleiner als N; Wiederherstellung → Stand vor der Wiederherstellung; Ersetzen ohne Ursprung → jüngste kleinere. Fehler „Kein aktueller Stand vorhanden“ bzw. „Es gibt keine ältere Version, die wiederhergestellt werden kann“.
- Wiederherstellen einer Version N lädt N; fehlt/gelöscht: „Version N existiert nicht (mehr)“; sonst neue Version (Bereich „restore“, Ursprung N).
- Rückgängig/Wiederherstellen laufen unter derselben Sperre wie Änderungen; sie lösen keine neue Dauerprüfung aus.
- Rückgängig ist global (unabhängig vom Benutzer). Neubau: vor dem Rückgängig zeigt eine Vorschau, welche fremden Änderungen mitgehen, mit Bestätigung; Recht `history.restore`.
Abnahme: Änderung A, Änderung B, zweimal Rückgängig stellt den Stand vor A her und erzeugt zwei neue Versionen; Wiederherstellen von Version 3 bei vorhandener Aufbewahrungsgrenze nach Löschung von Version 3 liefert „Version 3 existiert nicht (mehr)“; ohne `history.restore` 403; Rückgängig-Dialog listet fremde Änderungen (Status der Vorschau: offen).

### STP-014 · Gleichzeitige Änderungen und Synchronisation · P1 · Status: offen
- Ist: Änderungen laufen im Prozess strikt nacheinander; Leser prüfen höchstens alle 2 s, ob eine neuere Version existiert; empfohlen genau ein Arbeitsprozess. Ohne Mehrserver-Betrieb wird beim Speichern nicht geprüft, ob zwischenzeitlich eine andere Version entstand (Lost Update möglich).
- Neubau: Jedes Speichern prüft, dass die Basisversion noch die aktuelle ist; sonst Fehler „Der Plan wurde inzwischen geändert. Bitte erneut versuchen.“ (keine stille Überschreibung). Mehrserver-Betrieb: zusätzlich datenbankweite Schreibsperre bis zum Commit.
- Ereignis `change` nach jeder erfolgreichen Änderung (auch Wiederherstellen, Rückgängig, Ersetzen) mit Versionsnummer, Bereich, Datumsliste (bei Ersetzen leer); Clients laden nur betroffene Listen neu, ohne Bereich alles.
Abnahme: zwei parallele Schreibvorgänge auf derselben Basisversion führen zu genau einem Erfolg und einem Fehler mit der genannten Meldung; nach einem Schreibvorgang sehen andere verbundene Clients die Änderung innerhalb von 15 s (Mehrprozess) bzw. sofort über das Ereignis.

### STP-015 · Speicherformat und Verschlüsselung des Planungsdokuments · P0 · Status: Ist
- Nutzlast je Version: JSON (UTF-8, Schlüssel sortiert, ohne Leerzeichen) → zlib (Stufe 6) → Verschlüsselung mit eigenem Datenschlüssel je Version; die Versionsnummer ist als Zusatzkontext gebunden (Kopieren in eine andere Zeile erzeugt einen Entschlüsselungsfehler). Verschlüsselungskopf mit Kennung; Prüfsumme über das JSON vor der Verschlüsselung.
- Schlüsselrotation per CLI `rotate-keys` (Bereich `school_versions.data`): alle Versionen werden mit dem aktiven Schlüssel neu verschlüsselt, verlustfrei; Versionen mit entferntem Schlüssel bleiben unverändert (Warnung im Protokoll). Altbestand (nur komprimiert) wird weiter gelesen und beim Start verschlüsselt umgeschrieben; Fehler dabei blockieren den Start nicht.
- Produktivmodus startet nicht ohne Verschlüsselungsschlüssel (`SM_ENCRYPTION_KEYS`). Backups enthalten das Planungsdokument verschlüsselt; Plan-Stände und Plan-Pakete sind ebenfalls verschlüsselt zu speichern (siehe STP-067, STP-081).
- Ist: Speichern/Laden praktisch unverändert (Verschlüsselung < 1 ms bei der Referenzschule mit 99 Klassen, rund 68 KB).
Abnahme: die Versionstabelle enthält keinen Klartext von Namen oder Abwesenheitsgründen; ein Austausch der Nutzlast zweier Versionen führt zu einem Entschlüsselungsfehler; Start im Produktivmodus ohne Schlüssel bricht ab; nach `rotate-keys` sind alle Versionen mit dem aktiven Schlüssel lesbar.

### STP-016 · Start und Laden · P1 · Status: Ist
- Beim Start wird die jüngste lesbare Version geladen; geprüft werden höchstens die 5 jüngsten, unlesbare werden übersprungen (Protokolleintrag). Ist die Tabelle leer: leeres Dokument als Version „Leeres Planungsdokument angelegt“ (Bereich „init“, `plan.init`). Sind die 5 jüngsten unlesbar, startet das System mit leerem Dokument als neue Version (Risiko: Datenverlust ohne Hinweis).
- Neubau: Ist der Fallback auf ältere Versionen oder ein leeres Dokument nötig, erscheint ein deutlicher Hinweis im Systembereich für Administration (Status offen).
Abnahme: bei beschädigter jüngster Version lädt das System die vorherige und meldet dies im Systembereich; bei fünf unlesbaren Versionen erscheint ein Hinweis „Planungsdaten nicht lesbar“, nicht nur ein Protokolleintrag.

### STP-017 · Validierung des Planungsdokuments · P1 · Status: offen
- Ist: Pflichtfelder werden geprüft (fehlt eines, schlägt das Laden des Datensatzes fehl); doppelte Kennungen, verwaiste Verweise, Wertebereiche und Auswahlwerte werden im Modell nicht erzwungen; Fachregeln (Konflikte, Deputat, Qualifikation) prüfen Plan-Prüfung und Qualitätsbericht.
- Neubau: Eindeutigkeit der Kennungen, Verweisprüfung (Kurs → Klasse/Fach/Lehrkraft/Raum, Stunde → Kurs, Abwesenheit → Lehrkraft/Klasse/Raum/Kurs, Aufsicht → Bereich/Lehrkraft, Lehrkraft → Fach/Standort), Löschregeln (Klasse löschen entfernt Kursteil-Teilnehmer und Verweise), Wertebereiche und Auswahllisten werden serverseitig erzwungen. Kürzel unterscheiden nicht nach Groß-/Kleinschreibung („MUE“ = „mue“); Abwesenheits-Kennungen werden nicht wiederverwendet; Kürzel mit Leerzeichen werden abgelehnt.
- Datumsfelder im Format JJJJ-MM-TT; Ende vor Beginn wird abgelehnt (Ist: Eintrag wirkt nie).
Abnahme: Anlegen einer zweiten Lehrkraft „MUE“ neben „mue“ liefert 422; Löschen einer Klasse mit Kursteil-Teilnehmern hinterlässt keine verwaisten Verweise und lässt spätere Speichervorgänge nicht mit 422 scheitern; Abwesenheit mit Ende vor Beginn liefert 422.

### STP-018 · Planungseinstellungen und Standardwerte · P1 · Status: Ist
Einstellungen der Schule, soweit für Plan und Vertretung wirksam (Einheit, Wirkung):

| Einstellung | Standard | Wirkung |
|---|---|---|
| `days` | 5 | Anzahl Wochentage im Raster (bis 7) |
| `periods` | 10 | Stunden je Tag |
| `period_times` / `period_minutes` | siehe STP-007 / 45 min | Uhrzeiten, Stundenlänge |
| `breaks` | siehe STP-007 | Pausen |
| `school_days` | leer (= `days` Tage) | Unterrichtstage der Schule |
| `site_travel_periods` | 1 freie Stunde | Wegezeit zwischen Standorten ohne Eintrag für das Paar |
| `site_travel` | leer | Wegezeit je Standortpaar in Minuten, beide Richtungen |
| `core_latest_period` | 5 (0-basiert, Anzeige 6. Std.), Bereich 0–15 | späteste Hauptfachstunde |
| `prefer_doubles` | ja | Fächer ab 2 Wochenstunden als Doppelstunden planen |
| `double_alignment` | „bloecke“ | Lage der Doppelstunden: bloecke / pausen / frei |
| `auto_replan` | ja | Dauerprüfung „Plan prüfen“ an/aus |
| `plan_auto_apply` | „aus“ | „aus“ oder „raeume“ |
| `substitution_confirm` | nein | Vertretungen erst nach Freigabe sichtbar |
| `public_absent_teachers` | „short“ | off · short (Kürzel) · name (Kürzel + Name) |
| `max_exams_per_week` / `max_exams_per_day` | 3 / 1 | Klassenarbeiten je Klasse (Schulvorgabe) |
| `exam_limits_by_grade` | leer | Vorgabe je Jahrgang (je Woche 0–20, je Tag 0–5) |
| `teacher_self_service` | „approval“ | approval · direct (Lehrkraft-Angaben) |
| `teacher_times_self` | nein | Lehrkräfte legen Arbeitszeiten selbst fest |
| `subject_teacher_absence_view` | „none“ | none · presence |
| `week_numbering` / `year_start_mode` | iso / auto | siehe STP-001, STP-002 |
| `plan_periods` | leer | Planzeiträume (max. 12) |
| `rules` | {} | Regel-Bausteine (STP-053 ff.) |
| `policy` | siehe VER-012 | Vertretungsregeln |
| `webhooks` | leer | Ziele für Ereignis-Benachrichtigungen |
| `weights` | siehe STP-034 | Altfeld der Gewichte; ältere Clients bleiben unterstützt |

Das Speichern lehnt unbekannte Felder ab (422); Rasterfelder haben eine eigene Feldliste. Änderungen an `days`, `periods` oder dem Schuljahresbeginn zeigen vorab, welche Stunden/Kurse betroffen sind (U-13 Befund: bisher keine Prüfung gegen den Bestand). Schreiben nur mit `settings.edit`.
Abnahme: PUT Einstellungen mit unbekanntem Feld → 422; Senken von `periods` von 10 auf 6 bei vorhandenen Stunden in Stunde 8 liefert eine Vorschau mit diesen Stunden statt stiller Speicherung; Standardwerte eines neuen Dokuments entsprechen der Tabelle.

### STP-019 · Planungsstammdaten: Felder und Standardwerte · P1 · Status: Ist
Felder, die Plan, Generator und Vertretung benötigen (Pflichtfelder mit *; weitere Felder siehe STA/LEH):

| Objekt | Feld | Standard | Einheit/Bereich | Wirkung |
|---|---|---|---|---|
| Fach | Kennung*, Name* | – | – | – |
| Fach | `room_type` | leer = Klassenraum | Raumtyp | Raumwahl |
| Fach | `core` | nein | – | Hauptfach (früh am Tag) |
| Fach | `max_per_day` | 1 | Blöcke je Klasse und Tag | harte Regel |
| Fach | `color` | leer (automatisch) | #rrggbb [unklar] | Anzeige |
| Lehrkraft | Kürzel*, Name* | – | – | Kürzel = Kennung |
| Lehrkraft | `subjects` | leer | Fach-Kennungen | Qualifikation |
| Lehrkraft | `max_hours` | 25 | Wochenstunden (Deputat) | Zuweisung, Generator, Vertretung (Fairness-Bezug) |
| Lehrkraft | `max_per_day` | 7 | Stunden je Tag | Generator, Vertretung |
| Lehrkraft | `max_subs_per_week` | 3 | Vertretungen je Woche | Vertretung |
| Lehrkraft | `unavailable`, `wishes` | leer | Zeitregeln | harte Sperren, weiche Wünsche |
| Lehrkraft | `sites` | leer = alle | Standort-Kennungen | Einsatzbeschränkung |
| Lehrkraft | `commute_mode` | leer = beliebig | never · once · free | siehe STP-051 |
| Lehrkraft | `commute_gap` | 0 | Minuten | Mindestpause bei Standortwechsel |
| Lehrkraft | `time_windows`, `work_grid` | leer | Tage/Zeiten/Wochen bzw. Raster Wochen 1–52 | werden in harte Sperrzeiten umgerechnet |
| Lehrkraft | `times_self` | nein | – | Arbeitszeiten selbst festlegen (je Lehrkraft) |
| Raum | Kennung*, Name* | – | – | – |
| Raum | `type` | „Klassenraum“ | Raumtyp (Klassenraum, Kursraum, Fachraum u. a.) | Raumwahl |
| Raum | `site`, `capacity` | leer / 30 | Standort / Plätze | Standort-Logik / Anzeige |
| Klasse | Kennung*, Name*, Klassenstufe* | – | Klassenstufe | Klausurregeln, Vertretung |
| Klasse | `students` | 25 | Richtwert; wird aus der Schülerliste berechnet, sobald jemand zugeordnet ist | Anzeige |
| Klasse | `home_room`, `site` | leer | – | Stammraum, Standort |
| Klasse | `max_periods_per_day` | 8 | Stunden (Index-Grenze) | harte Regel |
| Klasse | `unavailable`, `school_days` | leer | Zeitregeln; Tage 0–6 | Sperren; Unterrichtstage (Änderung nur mit `timetable.edit`) |
| Klasse | `max_exams_per_week` / `max_exams_per_day` | leer = erbt | Klassenarbeiten | siehe STP-061 |
| Klasse | `profile` | leer | Jahrgang | bestimmt Stundentafel |
| Standort | Kennung*, Name* | – | – | – |
| Aufsichtsbereich | `needed` | 1 | Lehrkräfte je Pause | VER-043 |

Deputat (`max_hours`) setzt die Lehrkraft nicht selbst; sie gibt nur Verfügbarkeit und eine gewünschte Höchstzahl an Wochenstunden als Wunsch an (Abgrenzung: LEH).
Abnahme: ein neu angelegtes Fach hat max. 1 Block je Tag, kein Hauptfach, Raumtyp Klassenraum; eine neue Lehrkraft hat Deputat 25, 7 Stunden je Tag, 3 Vertretungen je Woche; eine Lehrkraft ohne `sites` ist an allen Standorten einsetzbar; die Schülerzahl einer Klasse folgt der Schülerliste.

### STP-020 · Kurs, Kursteil und Stunde (Datenmodell) · P1 · Status: Ist
- Kurs: Kennung*, Klassen*, Kursteile*, Wochenstunden `hours`*, `double` (Standard nein), Bezeichnung, Wochen oder Rhythmus (leer = alle), Herkunft `origin` (manual · curriculum), Liste fixierter Felder `pinned`.
- Kursteil: Fach*, Lehrkraft (leer = automatische Zuweisung), fester Raum (leer = keiner), Raumtyp (überschreibt Fach), Bezeichnung, Schülerliste (leer = alle Schüler/innen der Klassen des Kurses).
- Stunde: Kennung (`L1` … `Ln`)*, Kurs*, Tag*, Start*, Länge (Standard 1; 2 = Doppelstunde), Wochen oder Rhythmus, Räume je Kursteil (gleiche Länge wie die Kursteile), fixiert (Standard nein), Planzeitraum (leer = überall), `from_week`/`to_week` (aus dem Zeitraum berechnet, 0 = offen). Ausnahmen (Overrides) und Klausuren hängen an der Stunden-Kennung.
- Kursteile ändern zieht mit: Räume der Stunde, Kurszuordnung der Schüler/innen („Kurs#Teil“), Ausnahmen, Klausuren.
- Stunden-Kennungen bleiben bei Neuplanung und Untis-Import stabil, soweit der Block gleich bleibt; sonst melden Overrides „Stunde findet nicht statt“ statt eine falsche Stunde zu treffen (Befund: IDs wurden neu vergeben, Overrides verwaisten).
Abnahme: Kurs mit zwei Kursteilen, Stunde mit Räumen [R1, R2]; Löschen von Kursteil 2 entfernt R2 und die Zuordnungen „Kurs#1“ der Schüler/innen; Neuplanung eines unveränderten Blocks behält die Kennung und die daran hängende Ausnahme.

### 1.3 Stundentafeln, Kurse, Zuweisung

### STP-021 · Stundentafel: Modell und Ableitung · P1 · Status: Ist
- Stundentafel: Kennung*, Name*, Zeilen (Fach*, Wochenstunden*, `double` Standard nein), optional Basistafel `base` mit Abweichungen `deltas` (Stunden = Differenz, auch negativ; `double` = Zielwert), Klassen (nur für diese, Vorrang), Klassenstufen (Altbestand).
- Wirksame Zeilen einer abgeleiteten Tafel = Basis + Abweichungen; Fach mit 0 oder weniger Stunden entfällt; neue Fächer werden ergänzt. Eine Ableitung darf nicht auf sich selbst oder einen Kreis zeigen (Fehler „Die Ableitung bildet einen Kreis“).
- Dasselbe Fach zweimal in einer Tafel wird mit 422 abgelehnt (Kurs-Kennungen dürfen nie doppelt entstehen).
- Jahrgang (Jahrgangsprofil): frei benennbar (Name*, höchstens 120 Zeichen; Kurzname höchstens 20; Klassenstufe optional; Farbe #rrggbb; Beschreibung höchstens 500; Schulform/Abteilung höchstens 80; Stundentafel optional). Klassen gehören zu genau einem Jahrgang; der Jahrgang verweist auf eine Stundentafel. Löschen eines Jahrgangs: Auswirkungsvorschau (Klassen, Stundentafel-Kurse und Stunden, Stundentafel geteilt/abgeleitet, Alternativ-Jahrgänge), Klassen wandern in einen anderen Jahrgang, Kurse bleiben bis „Kurse erzeugen“; abgeleitete Tafeln werden eigenständig (Pflege der Jahrgänge: STA).
Abnahme: Tafel B mit Basis A und Abweichung Mathematik +1 liefert Mathematik = A + 1; eine Ableitung A → B → A wird mit „Die Ableitung bildet einen Kreis“ abgelehnt; zwei Zeilen „Mathematik“ in einer Tafel → 422.

### STP-022 · Zuordnung Stundentafel zu Klasse · P1 · Status: Ist
- Vorrang: (1) eigene Tafel mit der Klasse in ihrer Klassenliste (Kennung „KL-<Klassenkennung>“, Name „Stundentafel <Klassenname>“; setzt die Klasse aus anderen Tafeln heraus), (2) Tafel des Jahrgangs der Klasse, (3) Altbestand: Tafel ohne Klassenliste, deren Stufenliste die Klassenstufe enthält.
- Gelten auf derselben Stufe mehrere Tafeln: Konflikt. Speichern liefert 409 mit den betroffenen Klassen; mit Bestätigung wird erzwungen gespeichert; „Kurse erzeugen“ ändert die Kurse dieser Klassen nicht und meldet „Konflikt: für <Klassen> gelten mehrere Stundentafeln (<Namen>) – Kurse dieser Klassen wurden nicht geändert“. Der Server liefert je Klasse die gültige Tafel, ihre Herkunft (Klasse/Jahrgang) und die Konflikte (`GET /planning/curricula/effective`; zusätzlich Übersicht `/planning/curricula/overview`).
- Hat eine Klasse keine Tafel oder eine Tafel ohne Fächer, meldet „Kurse erzeugen“ dies mit dem Klassennamen (nie stilles Schlucken). Ein Jahrgangswechsel, der still eine Überschneidung erzeugt, wird beim Speichern erkannt.
- Dieselbe Zuordnungslogik gilt auf Server und Oberfläche.
Abnahme: zwei Tafeln über denselben Jahrgang → 409 mit Klassenliste, nach Bestätigung gespeichert, „Kurse erzeugen“ meldet den Konflikt und ändert die Kurse nicht; neue Klasse 11 mit leerer Tafel erzeugt die Meldung „Klasse 11a hat keine Stundentafel mit Fächern“; Klasse mit eigener Tafel und Jahrgangstafel nutzt die eigene.

### STP-023 · Stundentafel-Editor · P1 · Status: Ist
- Matrix Fächer × Stundentafeln (Spalten sortiert nach der kleinsten Jahrgangsstufe); Zellen direkt editierbar (Wochenstunden); Abweichung einer Klasse von der Basis wird mit Vorzeichen-Marke angezeigt; Zeilen- und Spaltensummen; Fußzeile Soll (Tafel) gegen Ist (Mittel der Kursstunden je Klasse, nur Kurse mit Herkunft „Stundentafel“) und Anzahl Klassen.
- Spaltenkopf öffnet Dialog: Name, Basis, Jahrgänge, Einzelklassen („Gilt für“ zeigt die tatsächlich betroffenen Klassen; Jahrgänge kommen aus den vorhandenen Klassen statt fest 5–13; ungültige Jahrgänge lehnt die API ab). „Neue Stundentafel“ zeigt ein leeres Formular ohne markierten Fremdeintrag; jede Tafel lässt sich direkt öffnen; Link aus der Jahrgangsübersicht öffnet die Matrix mit hervorgehobener Tafel (einmaliges Scrollen).
- Löschen: vorher Auswirkungsübersicht (betroffene Jahrgänge, Klassen, Kurse), dann Bestätigung im App-Dialog.
- Entwurf bleibt beim Reiterwechsel erhalten (Zwischenspeicher der Browser-Sitzung); Leiste „ungespeicherte Änderungen“ mit Speichern/Verwerfen; Hinweis beim Verlassen ohne Browser-Popup. Unter 700 px Breite Liste statt Matrix. Neues Fach direkt aus der Fach-Auswahl anlegen („Neues Fach …“, Recht `masterdata.edit`). Lesende ohne Schreibrecht sehen den Grund statt stumm gesperrter Felder.
- Nach dem Speichern führt „Kurse der betroffenen Klassen aktualisieren“ mit Vorschau direkt zum Ergebnis, ohne Umweg über den Generator.
- Recht: Schreiben `timetable.edit`; Sekretariat nur lesen (mit Grund).
Abnahme: Änderung einer Zelle zeigt Summen sofort neu; Reiterwechsel und Rückkehr behalten den Entwurf; Löschen einer Tafel zeigt zuerst „betroffen: 3 Jahrgänge, 7 Klassen, 42 Kurse“; Sekretariat sieht die Matrix ohne Schreibfelder und mit Begründung; bei 600 px zeigt die Seite Listen statt Matrix.

### STP-024 · Kurse aus Stundentafeln erzeugen · P1 · Status: Ist
- Je Klasse und Fach eine Kurs-Kennung „<Klasse>-<Fach>“ (bei Kollision mit einem manuellen Kurs „-2“, „-3“ …), Bezeichnung „<Fach> <Klassenname>“, Herkunft „curriculum“. Wochenstunden = Stunden der Tafel − bereits abgedeckte Stunden derselben Klasse/desselben Fachs aus manuellen Kursen; Kurse nur in einigen Wochen zählen anteilig (Wochen des Kurses / Schulwochen); kaufmännisch gerundet (ab 0,5 auf); Kurse mit ≤ 0 Stunden werden nicht erzeugt. Doppelstunden-Flag aus der Tafel.
- Fach existiert nicht: übersprungen mit Warnung „Fach <Kürzel> existiert nicht (übersprungen)“. Gleiches Fach mehrfach: Stunden zusammengefasst mit Warnung „mehrfach eingetragen“ (die Eingabe wird jedoch bereits mit 422 abgelehnt, STP-021).
- Bestehende Lehrkraft (Kursteil 0) bleibt erhalten. Eigene Anpassungen (Wochenstunden, Doppelstunde, Wochen, Bezeichnung, Kursteile/Räume) bleiben erhalten, wenn der Kurs neu erzeugt wird (Pins), außer bei „manuell zurücksetzen“; der Bestätigungstext sagt das genau so.
- Ergebnisansicht: angelegt, entfernt, geändert (Felder: Stunden, Doppelstunde, Wochen, Rhythmus, Bezeichnung, Kursteile), beibehalten („kept“), Warnungen; entfernte Kurse mit Klartext-Bezeichnung statt Kennung. „Neuplanung nötig“, wenn Kurse angelegt/entfernt werden oder sich außer der Bezeichnung etwas ändert. Entfernte Kurse nehmen ihre Stunden mit.
- Werden Stunden gesenkt, meldet der Qualitätsbericht „X Stunden zu viel verplant“ je Kurs; „Kurse aktualisieren“ bietet an, überzählige nicht fixierte Stunden zu entfernen (Vorschau, dann Übernehmen).
- Manuelle Kurse mit Wochen zählen anteilig gegen die Stundentafel (Befund: zählten voll). Kurs-Editor erlaubt bis zu den Wochenstunden der Tafel (Befund: Editor-Grenze 20 gegen Tafel 40).
- Recht `timetable.edit`.
Abnahme: Tafel „Mathematik 4“ bei manuellem Kurs „Mathematik 5a“ mit 1 Stunde erzeugt „5a-MA“ mit 3 Stunden; ein Kurs mit Pin auf Raum behält ihn nach erneutem Erzeugen; Senken von 4 auf 3 Stunden zeigt im Bericht „1 Stunde zu viel“ und bietet die Entfernung mit Vorschau an; fehlendes Fach erzeugt die genannte Warnung.

### STP-025 · Kurs-Editor und fixierte Felder · P2 · Status: Ist
- Felder eines aus der Tafel erzeugten Kurses lassen sich einzeln fixieren („Pin“; feste Auswahlliste fixierbarer Felder); fixierte Felder überstehen „Kurse erzeugen“.
- Konflikte bei Stundentafeln werden als Liste angezeigt; Klick auf Kursziele in der Planung öffnet den Kurs-Editor.
- Für manuelle Kurse: Klassen auswählen (auch klassenübergreifend, z. B. 5a + 5b), Kursteile je Parallelgruppe (Fach, Lehrkraft, Raum, Schüler/innen), Filter „nur Kopplungen“.
Abnahme: Änderung der Wochenstunden eines Stundentafel-Kurses im Editor, danach „Kurse erzeugen“ lässt den Wert bestehen; Auswahl „5a + 5b“ legt einen Kurs mit zwei Klassen an.

### STP-026 · Gekoppelte Kurse (Kursteile) · P1 · Status: Ist
- Mehrere Klassen und/oder mehrere Kursteile bilden eine Kopplung: Der Generator setzt alle Teile in dieselbe Stunde; alle Beteiligten (Lehrkräfte, Räume, Schüler/innen) müssen frei sein.
- Anzeige im Stundenplan: Knopf „N Kurse“ (z. B. „3 Kurse“) unten links im Feld öffnet eine Sprechblase mit den Kursteilen (Lehrkraft, Raum); mit Planungsrecht zusätzlich „Kurs bearbeiten“ (springt in Planung → Kurse). Gekoppelte Kurse sind nie schraffiert dargestellt (Schraffur bedeutet nur „gesperrt“ oder „gefehlt“).
- Betreiberzitat (16.10.): „bei er ist das ist so gestrichelt ich weiß nicht warum ein design choices oder was auch immer“ → Schraffur entfernt.
- Bei gekoppelten Kursen ist eine Lehrkraft nur dort „Lehrende“, wo sie tatsächlich Schüler/innen unterrichtet.
Abnahme: Kopplung ER/KR/PL liegt in derselben Stunde; „3 Kurse“ öffnet die Sprechblase mit drei Zeilen (Lehrkraft, Raum); das Feld ist nicht schraffiert; ohne Planungsrecht fehlt „Kurs bearbeiten“.

### STP-027 · Lehrkraft-Zuweisung zu Kursteilen · P1 · Status: Ist
- Nur Kursteile ohne Lehrkraft. Reihenfolge: knappe Fächer zuerst (wenige qualifizierte Lehrkräfte), dann große Kurse (mehr Stunden zuerst). Qualifiziert = Fach steht im Fächerprofil der Lehrkraft.
- Harte Ausschlüsse: (a) Lehrkraft unterrichtet schon einen anderen Teil desselben Kurses; (b) Deputat: bisherige Stunden + Stunden des Kurses > `max_hours` (25 Wochenstunden); (c) Standorte der Lehrkraft passen nicht zum Standort der Klassen (wenn beide gesetzt); (d) gemeinsame freie Stunden von Klassen und Lehrkraft < Stunden des Kurses (je Wochenmuster das Minimum).
- Bewertung (niedrigster Wert gewinnt): Auslastung (bisherige Stunden / Deputat) × 10; kennt die Klassen −4 je gemeinsamem Kursteil; Wunschklasse −6; knappe Verfügbarkeit (Kapazität < 2 × Stunden) +4 × Stunden / Kapazität; Standorttreue +8 × Stunden an anderen Standorten / Deputat.
- Meldungen unterscheiden: „Keine Lehrkraft mit dem Fach <Fach> – <Kurs> bleibt offen (Fach bei Lehrkräften eintragen oder Lehrkraft im Kurs wählen)“ und „Keine freie Lehrkraft für <Fach> in <Kurs> (Deputat ausgeschöpft: n; Zeitfenster/Sperrzeiten passen nicht: n; anderer Standort: n; unterrichtet schon einen Parallelteil: n)“.
- Recht `timetable.edit`. Wunschklassen entfallen als Begriff; stattdessen „Klassenleitung in“, „Ich unterrichte“, „Ich kann vertreten in“ (LEH).
Abnahme: Kurs Chemie 5a/2 Std., nur Lehrkraft X (Chemie, 25/25 Stunden) → Meldung „Deputat ausgeschöpft: 1“; Lehrkraft ohne Fach Chemie → Meldung „Keine Lehrkraft mit dem Fach Chemie“; bei zwei Kandidaten gewinnt die Lehrkraft mit niedrigerer Auslastung, bei Gleichstand die kleinere Kennung.

### STP-028 · Klassenleitung zuweisen · P3 · Status: Ist
- Nur Klassen ohne Klassenleitung; jede Lehrkraft leitet höchstens eine Klasse. Bevorzugte Lehrkräfte zuerst (ihrer stärksten Klasse); danach je Klasse die Lehrkraft mit den meisten Stunden in dieser Klasse (Gleichstand: Kennung). Die Lehrkraft muss die Klasse ohnehin unterrichten.
- Mehrere Klassenleitungen je Klasse sind Wunsch (A-42, Status offen; STA/REC).
Abnahme: Klasse 5a ohne Leitung, Lehrkraft Y mit 10 Stunden in 5a und noch ohne Klasse → Y wird Klassenleitung; Lehrkraft, die bereits eine Klasse leitet, wird nicht ein zweites Mal gewählt.

### STP-029 · Kapazitätsprüfung der Klassen · P2 · Status: Ist
- Je Klasse und Wochenmuster: Wochenstunden aller Kurse > verfügbare Stunden (Unterrichtstage der Klasse × min(Stunden je Tag, Höchststunden der Klasse), abzüglich Sperrzeiten) → Warnung „Klasse <Name> (<Wochen>): <n> Wochenstunden, aber nur <m> verfügbare Stunden“.
Abnahme: Klasse mit 5 Tagen × 6 Höchststunden = 30 verfügbaren Stunden und Kursen über 32 Wochenstunden liefert die Warnung mit n = 32, m = 30.

### STP-030 · Zählregel Doppelstunde · P1 · Status: Ist
- Eine Doppelstunde zählt immer als zwei Schulstunden: in Stundentafel, Generator, Wochenstunden der Lehrkräfte, Planungsbericht, Fehlzeitenstatistik. (Beispiel: Englisch 5 Stunden = 2+2+1.) Die Anzeige macht die Stundenzahl erkennbar (die Betreiberin sah „drei Kästchen“ und wusste nicht, in welcher Stunde die Klausur liegt).
- Kennzahlen ohne halbe Stunden: unterscheiden sich Wochenmuster, wird ein Bereich angezeigt („5–6, Ø 5,5 je nach Woche“), sonst die ganze Zahl.
Abnahme: Kurs Englisch 5 Std. mit Doppelstunde + Doppelstunde + Einzelstunde meldet in Planungsbericht, Lehrkraft-Wochenstunden und Statistik je 5 Stunden; bei Wochenmustern mit 5 und 6 Hohlstunden steht „5–6, Ø 5,5“, nicht „5,5“.

---
### 1.4 Generator („Neuaufbau“)

### STP-031 · Ziel, Rangfolge und Grundsätze des Generators · P0 · Status: Ist
- Eingabe: Klassen, Lehrkräfte, Räume, Standorte, Fächer, Kurse mit Stunden je Woche, Stundentafel, Sperrzeiten, Wünsche, Wochenangaben, fixierte Stunden. Ergebnis: je platzierter Stunde Tag, Anfangsstunde, Länge (1 oder 2), Wochenangabe (leer = alle Wochen des Kurses), Räume und Standort, Kennung `L<n>`, Kennzeichen „fixiert“; dazu eine Liste unverplanter Stunden (Kurs, Länge, Wochen, Rhythmus, Klartext der Wochen).
- Rangfolge: (1) keine harte Regel verletzt, (2) möglichst wenige unverplante Stunden (1000 Strafpunkte je unverplante Stunde und Woche), (3) geringste Strafpunktesumme. Bei mehreren Varianten gewinnt die mit den wenigsten Konflikten, dann wenigsten unverplanten Stunden, dann niedrigsten Gesamtkosten.
- Grundsätze: klassisches Optimierungsverfahren (lokale Suche), keine KI, kein Internetzugriff; reproduzierbar mit Startwert; der Generator arbeitet ausschließlich auf dem Planungsdokument; nur der Neuaufbau erzeugt einen Plan, immer als Entwurf, der bestätigt werden muss. „Kennzahlen aktualisieren“ ändert nie den Plan.
- Der Generator dient dem Neuaufbau zum Schuljahr oder Zeitraum; die laufende Anpassung nach Änderungen leistet „Plan prüfen“ (STP-069 ff.).
Abnahme: Ein Lauf mit der Referenzschule (STP-098) ohne Netzwerkzugriff liefert einen Entwurf; der Qualitätsbericht des Entwurfs zeigt 0 Konflikte; solange nicht übernommen wird, ist der geltende Plan unverändert; die Rangfolge entscheidet zwischen zwei Varianten mit gleichen Konflikten nach unverplanten Stunden, dann nach Strafpunkten.

### STP-032 · Harte Regeln · P0 · Status: Ist
Harte Regeln werden nie verletzt; je Platz werden alle Sperrgründe ermittelt. Sie sind im System fest verdrahtet und nicht über die Regel-Bausteine abschaltbar.

| Regel | Standard / Wert | Wirkung |
|---|---|---|
| Keine Doppelbelegung | 1 Stunde je Klasse, Lehrkraft, Raum und Zeitpunkt | gilt für alle Wochen der Stunde |
| Sperrzeit Klasse | nach Tag, Stunde, Woche/Rhythmus | Stunde gesperrt |
| Sperrzeit Lehrkraft | nach Tag, Stunde, Woche/Rhythmus | Stunde gesperrt; Wünsche der Lehrkraft sind NICHT hart |
| Unterrichtstage Klasse | Schultage der Schule (Mo–Fr), je Klasse eigene | kein Block an Nicht-Unterrichtstagen; ein Kurs nutzt nur Tage, an denen alle seine Klassen Unterricht haben |
| Max. Stunden je Tag Klasse | `max_periods_per_day` = 8 | Stunden mit Index ≥ Wert gesperrt (bei 8: nur Stunden 1–8) |
| Max. Stunden je Tag Lehrkraft | `max_per_day` = 7 Stunden | bestehende Stunden des Tages + Länge der neuen Stunde ≤ Wert |
| Max. Blöcke eines Fachs je Tag | Fach-`max_per_day` = 1 | wirksam je Kurs = max(1; Fach-Wert; aufgerundet(benötigte Blöcke / verfügbare Tage)); letzter Ausweg +1 je Kurs mit Warnung „<Kurs>: musste <n>× an einem Tag gelegt werden“ |
| Lehrkraft nur an eigenen Standorten | Standortliste der Lehrkraft | Block nur an einem Standort der Lehrkraft |
| Wegezeit zwischen Standorten | `site_travel_periods` = 1 freie Stunde | zwischen Blöcken an verschiedenen Standorten mindestens so viele freie Stunden für Klasse und Lehrkraft; Sonderregeln siehe STP-051 |
| Doppelstunde: Lage | `double_alignment` = „bloecke“ | „bloecke“: Start nur 1.–2., 3.–4., 5.–6. Stunde usw. (Startindex 0, 2, 4 … innerhalb des Pausenabschnitts), nie über eine Pause; „pausen“: nie über eine Pause, sonst frei; „frei“: keine Einschränkung |
| Hauptfach-Grenze | `core_latest_period` = 5 (0-basiert, Anzeige 6. Std.) | nur hart, wenn der Baustein „Hauptfächer früh“ auf „Muss“ steht: kein Hauptfachblock endet nach der spätesten Hauptfachstunde |
| Fixierte Stunden | `keep_locked` = ja | bleiben erhalten und werden zuerst gesetzt; kollidiert eine mit einer harten Regel, wird sie verworfen mit Warnung „Fixierte Stunde <Kennung> (<Kurs>) kollidiert und wurde verworfen“ |
| Kurs ohne Woche im Schuljahr | – | nicht geplant; Warnung „<Kurs>: liegt in keiner Woche dieses Schuljahres“ |
| Kurs mit 0 Stunden oder ohne gültige Klasse | – | übersprungen (kein Absturz) |

Doppelstunden liegen nie über einer Pause (Pflichtanforderung des Betreibers). Betreiberzitat: „Doppelstunden sollen bitte nur ausschließlich in Gruppen sein, also nicht in Pausen sein.“ Die Bevorzugung von Doppelstunden allein genügt nicht; Pausen sind eine harte Grenze.
Abnahme: Referenzlauf mit 93 Doppelstunden → 0 liegen über einer Pause (Bestandsfehler: 30 von 93); eine Doppelstunde auf Start Stunde 2 (Index 1) wird bei „bloecke“ nicht gelegt; Fach mit `max_per_day` 1 hat pro Klasse und Tag höchstens einen Block, außer bei ausgewiesener Warnung; eine fixierte, kollidierende Stunde erzeugt exakt die genannte Warnung.

### STP-033 · Raumwahl · P1 · Status: Ist
- Reihenfolge der Kandidaten: fester Raum des Kursteils → Raumtyp (Kursteil, sonst Fach) → (nur ein Kursteil und eine Klasse) Heimatraum der Klasse → Pool aus Heimaträumen der Klassen und Räumen vom Typ „Kursraum“. Der Raum muss zur Stunde frei sein; Räume am Standort der Klasse zuerst; bereits fixierte Räume bleiben.
- Fächer ohne Raumtyp nutzen Klassenräume; Fächer mit Raumtyp (z. B. Sporthalle, Chemie) nur passende Räume. Ist kein Raum vom benötigten Typ frei, bleibt die Stunde unverplant mit Grund.
Abnahme: Fach mit Raumtyp „Chemie“ wird nur in Räume vom Typ „Chemie“ gelegt; sind alle belegt, erscheint die Stunde in der Liste unverplanter Stunden mit Grund „kein freier Raum vom Typ Chemie“; Kurs mit festem Raum bekommt diesen Raum.

### STP-034 · Gewichte der weichen Regeln (Strafpunkte) · P1 · Status: Ist
Wirksames Gewicht = Grundgewicht × Stufenfaktor. Stufenfaktoren: Aus 0; Nett 0,25; Wichtig 1; Sehr wichtig 4; Muss 20. Eigener Zahlenwert ≥ 0 ist erlaubt (verlustfrei für Altwerte, die keiner Stufe entsprechen). Grundgewichte sind Konfiguration (nicht im Code verteilt):

| Baustein (Schlüssel) | Titel | Grundgewicht | Bezug | Strafpunkte je … | Ausnahmen nach | Kennzahl |
|---|---|---|---|---|---|---|
| `class_gap` | Keine Hohlstunden für Klassen | 100 | Klasse, je Tag | Freistunde zwischen erster und letzter Stunde einer Klasse am Tag | Jahrgang, Klasse | class_gaps |
| `late_start` | Unterricht beginnt zur ersten Stunde | 40 | Klasse, je Tag | Stunde, um die die erste Stunde später liegt als die erste verfügbare | Jahrgang, Klasse | late_start |
| `day_balance` | Gleichmäßig lange Schultage | 6 | Klasse, je Tag | 0,5 × (Stunden am Tag − Zielstunden)² | Jahrgang, Klasse | – |
| `core_late` | Hauptfächer früh am Tag | 6 | Kurs, je Block | Stunde, die ein Hauptfachblock über die späteste Hauptfachstunde hinausragt | Jahrgang, Klasse, Fach | core_late |
| `spread` | Fächer über die Woche verteilen | 5 | Kurs (nur bis 3 Wochenstunden) | Paar aufeinanderfolgender Tage mit Unterricht desselben Kurses | Jahrgang, Klasse, Fach | – |
| `double_split` | Doppelstunde bekommen | 3 | Kurs, je Block | Einzelstunde eines Kurses mit Doppelstunden und ≥ 2 Wochenstunden | Jahrgang, Klasse, Fach | – |
| `position` | Früh am Tag (Feinsteuerung, nur „Erweitert“) | 0,6 | Kurs, je Block | Mittelpunkt-Stunde des Blocks (0-basiert) | Jahrgang, Klasse, Fach | – |
| `teacher_gap` | Wenige Springstunden | 4 | Lehrkraft, je Tag | Freistunde zwischen erster und letzter Stunde der Lehrkraft am Tag | Lehrkraft | teacher_gaps |
| `teacher_wish` | Wünsche der Lehrkraft | 5 | Lehrkraft, je Stunde | Stunde in einem Wunsch-frei-Slot | Lehrkraft | – |
| `site_change` | Standortwechsel vermeiden | 15 | Lehrkraft, je Tag | Wechsel des Standorts zwischen aufeinanderfolgenden Stunden (bei „nie pendeln“ × 40) | Lehrkraft | site_changes |
| `auto_replan` | Automatisch neu planen | Schalter, Standard an | – | nicht Teil der Kosten | – | – |

- Unverplante Stunde: 1000 Strafpunkte × Länge × Summe der Gewichte ihrer Wochenmuster (wichtigste Strafe).
- Stufentexte der Oberfläche: Aus „wird nicht beachtet“; Nett „zählt wenig – andere Ziele gehen vor“; Wichtig „normales Gewicht (Standard)“; Sehr wichtig „zählt viermal so stark wie Wichtig“; Muss „zählt zwanzigmal so stark – praktisch eine harte Regel“.
- Bei „Hauptfächer früh am Tag“ ist „Muss“ eine echte harte Regel im Generator.
Abnahme: Das Gewicht für Hohlstunden bei Stufe „Sehr wichtig“ beträgt 400, bei „Nett“ 25, bei „Aus“ 0; Gewicht 150 (keiner Stufe entsprechend) bleibt als eigener Zahlenwert erhalten und wird beim Export wieder ausgegeben; eine unverplante Doppelstunde in einem Wochenmuster mit Gewicht 1 kostet 2000 Strafpunkte.

### STP-035 · Kostenfunktion (Formeln) · P1 · Status: Ist
Alle Anteile werden mit dem Gewicht `nv` des Wochenmusters v multipliziert.
- Klasse, je Tag (nur Tage mit mindestens einer verfügbaren Stunde): Zielstunden = Stunden der Klasse in der Woche / Anzahl Tage mit verfügbarer Stunde. n = belegte Stunden am Tag; Lücken = freie, nicht gesperrte Stunden zwischen erster und letzter belegter Stunde. Kosten = w_balance × 0,5 × (n − Zielstunden)² + (falls n > 0) w_gap × Lücken + w_late × max(0; erste belegte − erste verfügbare Stunde).
- Lehrkraft, je Tag: Lücken = (letzte − erste + 1) − belegte Stunden. Standortwechsel = Anzahl Wechsel des Standorts zwischen aufeinanderfolgenden belegten Stunden; Wechselgewicht = w_site × 40, wenn die Lehrkraft „nie pendeln“; Modus „höchstens 1× am Tag“: jeder weitere Wechsel über den ersten hinaus zählt als 40 (Wechselzahl wird um (Wechsel − 1) × 39 erhöht). Kosten = w_gap × Lücken + Wechselgewicht × Wechsel + w_wish × Wunschstunden.
- Kurs (nur Kurse mit höchstens 3 Wochenstunden): je Paar aufeinanderfolgender Tage mit Unterricht w_spread.
- Block: Position = w_pos × Mitte (Mitte = Anfangsstunde + (Länge − 1) / 2, 0-basiert); Hauptfach: wenn Ende > späteste Hauptfachstunde w_core × (Ende − späteste) [unklar: „Ende“ = letzte belegte Stunde des Blocks]; geteilte Doppelstunde: wenn der Kurs Doppelstunden hat, ≥ 2 Wochenstunden und der Block eine Einzelstunde ist, w_split.
- Gesamtkosten = Summe aller Anteile + 1000 × Länge × Summe der Gewichte für unverplante Blöcke.
Abnahme: Klasse mit 5 Wochentagen, 25 Wochenstunden, Tag mit 8 belegten Stunden: Zielstunden 5, Anteil day_balance = 6 × 0,5 × 9 = 27 Strafpunkte; eine Klasse mit einer Freistunde zwischen Stunde 2 und 4 kostet 100 (Gewicht Wichtig); Lehrkraft „nie pendeln“ mit einem Standortwechsel kostet 15 × 40 = 600.

### STP-036 · Wochenmuster (Rechenersparnis) · P1 · Status: Ist
- Planungshorizont: die Schulwochen 1 … Y. Ein Wochenmuster = Menge realer Wochen mit identischer Signatur (gleiche Sperren, Wünsche, Kurs- und Stundenwochen, Ausnahmen-Wochen und -Rhythmen).
- Gewicht je Muster = (Anzahl Wochen des Musters) × V / H (V = Anzahl Muster, H = Anzahl realer Wochen); die Summe der Gewichte ist V [unklar: die Quelle nennt „Summe = Zahl der Wochen“, das widerspricht der Formel]. Beispiel: Regeln nur in den Wochen 1 und 2 → 3 Muster statt 52 Wochen.
- Warnung ab mehr als 8 Mustern: „Viele unterschiedliche Wochen (V). Erhöhen Sie die Rechenzeit oder tragen Sie Blockphasen als Abwesenheit ein.“
- Eine Stunde gilt zunächst für alle Muster ihres Kurses (gleicher Platz in jeder Woche); nur wenn sie nicht passt, wird je Muster aufgeteilt. Ausgabe der Wochenangabe: leer, wenn alle Wochen des Kurses; sonst die Wochen der Muster oder, bei regelmäßigem Abstand, ein Rhythmus (`every`, `from_week`, `to_week`; Beispiel: jede 2. Woche ab Woche 2 am Dienstag).
- Kennzahlen (Hohl-, Springstunden, Standortwechsel) sind Durchschnitte je Schulwoche (gewichtete Summe geteilt durch die Zahl der Muster).
Abnahme: Ein Kurs mit „jede 2. Woche ab Woche 2“ erzeugt zwei Muster; bei 9 Mustern erscheint die Warnung mit „(9)“; ein Kurs ohne Wochenangabe wird mit leerer Wochenangabe ausgegeben.

### STP-037 · Ablauf der Planung · P1 · Status: Ist
1. Fixierte Stunden setzen (Restbedarf je Kurs und Woche = Stunden − abgedeckte Stunden).
2. Blöcke erzeugen: Doppelstunden, wenn der Kurs `double` hat oder (`prefer_doubles` und Stunden ≥ 2); Blockanzahl = ⌈Stunden / 2⌉; Rest Einzelstunden.
3. Konstruktion (gierig): Blöcke nach Schwierigkeit absteigend. Schwierigkeit = 30 × (Klassen − 1) + 10 × (Lehrkräfte − 1) + 15 × Raumanforderungen ohne festen Raum + 20 × Länge + 20 × Anteil gesperrter Lehrkraft-Stunden + 40 × Anteil gesperrter Klassen-Stunden + 5 × (Anzahl aller Muster − Muster des Blocks) + Zufall (0 bis 1). Jeder Block nimmt die Lage mit der kleinsten Kostenänderung (plus Zufall bis 0,01).
4. Reparatur (bis 4 Runden): nicht platzierbarer Block → beste Lage; sonst Verdrängen von höchstens 2 nicht fixierten Blöcken, die anderswo neu platziert werden (höchstens 60 Versuche je Block; Rückverlegung als Zwischenschritt höchstens 10 Versuche); sonst aufteilen (je Muster ein Block bzw. Doppelstunde in Einzelstunden).
5. Letzter Ausweg: Höchstzahl Blöcke je Tag des Kurses um 1 erhöhen, mit Warnung (STP-032).
6. Optimierung (STP-038). 7. Ausgabe: Stunden, unverplante Blöcke, Kennzahlen, Warnungen, Verlauf.
Fortschrittsanteile: Konstruktion 0 bis 0,4; Reparatur 0,4 bis 0,5; Optimierung 0,5 bis 1,0.
Abnahme: Fester Startwert und feste Schrittzahl liefern bei zwei Läufen denselben Plan; ein Block mit Schwierigkeit 120 wird vor einem mit 60 gelegt; nach Reparatur sind alle Blöcke platziert oder in der Liste unverplanter Stunden.

### STP-038 · Optimierung (Simulated Annealing) · P1 · Status: Ist
- Temperatur T = 3,0 × (1 − f) + 0,01, linear fallend; f = verstrichene Zeit / Zeitlimit oder Schritte / feste Schrittzahl; Aktualisierung alle 200 Schritte.
- Zugarten: gibt es Lücken in Klassentagen, mit 40 % Wahrscheinlichkeit eine Lückenkorrektur (Stunde aus dem Rand oder eine Klassenstunde in die Lücke); sonst 75 % Verschiebezug (zufälliger Tag und Anfangsstunde desselben Kurses), 25 % Tausch (zwei Blöcke derselben Klasse mit gleicher Länge und gleichen Wochen).
- Annahme: Verbesserung (Δ ≤ 0) immer; Verschlechterung mit Wahrscheinlichkeit e^(−Δ/T). Die Liste der Lücken-Tage wird alle 2000 Schritte neu berechnet. Verlauf: höchstens 60 Stützpunkte (Sekunden, Schritte, Kosten).
Abnahme: Der Verlauf eines Laufs enthält höchstens 60 Punkte; die Gesamtkosten des Ergebnisses sind nicht höher als die der Konstruktion; bei f = 1 beträgt T = 0,01.

### STP-039 · Rechenzeit, Mehrläufe, Reproduzierbarkeit · P1 · Status: Ist
| Wert | Standard | Einheit | Wirkung |
|---|---|---|---|
| Zeitlimit Einzellauf | 20 [unklar: Konfiguration `SM_GENERATE_TIME_LIMIT` nennt 30] | Sekunden | Optimierung endet |
| Zeitlimit Mehrlauf | 30 | Sekunden | parallele Läufe |
| Parallele Läufe | min(4; Anzahl Kerne) | Läufe | je Lauf eigener Startwert |
| Startwert | 1 | Zahl | erster Lauf; weitere +1, +2 … |
| Starttemperatur | 3,0 → 0,01 | Punkte | linear fallend |
| Zeitgrenze einer Generator-Anfrage | 5 | Minuten | wie Uploads, Sicherungen, Importe (normale Anfragen 30 s) |

- Bester Lauf = wenigste unverplante Stunden, danach geringste Kosten; ausgegeben werden Startwert, bester Startwert, Läufe mit Kosten, unverplanten Stunden, Schritten und Verlauf. Mit fester Schrittzahl (`iterations`) und gleichem Startwert entsteht derselbe Plan.
- Oberfläche: Rechenzeit „Schnell · Normal · Gründlich“ (konkrete Sekunden je Stufe [unklar]); Startwert und parallele Läufe nur unter „Erweitert“. Messwerte des Bestands (Demo-Daten): 10 Sekunden lieferten ein schlechteres Ergebnis als der aktuelle Plan (Strafpunkte +2.689); 2 Minuten (rund 876.000 Varianten, 4 parallele Läufe, 557.600 Schritte je Lauf-Gruppe) verplanten alle 1.554 Stunden. Ist der Entwurf schlechter als der aktuelle Plan, steht dabei „Nicht übernehmen – aktueller Plan ist besser“ bzw. „Mehr Rechenzeit wählen“.
Abnahme: Mit `iterations` = 100000 und Startwert 1 liefern zwei Läufe identische Pläne; bei 4 Kernen laufen 4 Läufe mit Startwerten 1–4 und der beste wird gewählt; eine Anfrage über 5 Minuten wird abgebrochen mit verständlicher Meldung.

### STP-040 · Läufe: Start, Ablauf, Abbruch · P1 · Status: Ist
- Start `POST /api/v1/planning/generate` (Recht `timetable.generate`). Parameter: Anzahl Varianten 1 bis 5; Startwert (Variante i rechnet mit Startwert + i × 1000); Planzeitraum (optional, sonst ganzes Schuljahr); Startplan aus anderem Zeitraum kopieren (optional; dient als Ausgangsplan, wird nicht neu berechnet); Probelauf-Kennzeichen (rechnet den Entwurf der Regeln, ändert keine Einstellungen; STP-058).
- Läufe werden nacheinander abgearbeitet, immer nur einer gleichzeitig. Ein manuell gestarteter Lauf blockiert die Berechnung der Planvorschläge für bis zu 3 Minuten. Laufende Läufe sind abbrechbar, Läufe löschbar (`timetable.generate`). Lesen von Läufen und Varianten: angemeldet plus `timetable.generate` oder `timetable.edit`.
- Läufe leben im Speicher des laufenden Prozesses und gehen bei Neustart verloren; die Oberfläche zeigt dann „Lauf verloren“ statt eines hängenden Laufs. Status in Klartext (wartend · läuft · fertig · abgebrochen · fehlgeschlagen) ohne Kennung oder englische Wörter [unklar: vollständige Statusliste des Bestands].
- Die Oberfläche zeigt zuverlässig, ob ein Lauf (auch eines anderen Kontos) läuft; der Startknopf nennt den Grund, wenn er gesperrt ist (Befund: Hinweis „neuer Lauf erst danach“ widersprach dem Knopf).
Abnahme: Zweiter Start während ein Lauf läuft wird eingereiht oder mit Grund abgelehnt, nie parallel gerechnet; Abbrechen beendet den Lauf innerhalb weniger Sekunden; Varianten = 6 → 422; ohne `timetable.generate` 403; Startwert 10 ergibt für Variante 2 den Startwert 2010.

### STP-041 · Auswertung Vorher/Nachher · P1 · Status: Ist
- Nur beim Generatorlauf (nicht bei Teilneuplanung und Plan prüfen). Vergleichsbasis „Vorher“: bei Planzeitraum der Plan dieses Zeitraums, sonst Startplan bzw. ganzer Plan; nie gegen den ganzen Plan, wenn ein Zeitraum gewählt ist.
- Kennzahlen als Kacheln mit Vorher, Nachher, Differenz und Gesamturteil, aus derselben Prüfung wie der Qualitätsbericht (kein Doppelwert; Hohl-, Springstunden, Standortwechsel als Durchschnitt je Woche, nur regulärer Plan, nicht Tagesvertretungen). Kacheln öffnen Diagramme (Säulen, waagerechte Balken, Linien mit Legende; Farben für Vorher, Nachher, beste Variante, gut, schlecht, übrige); Werte stehen an den Balken bzw. erscheinen beim Darüberfahren oder Antippen. Keine zusätzliche Werte-Tabelle neben den Diagrammen (Betreiber: „Warum wird die Tabelle extra in Wert dann gezeigt? Ich interessiere mich nicht.“).
- Inhalte: Klassen und Lehrkräfte, die besser/schlechter wurden (gruppiert); Verschiebungen (Liste der geänderten Stunden, gezählt je Art, Filter nach Art: verschoben am Tag · verschoben in der Stunde · nur Raum · unverändert · neu · entfernt; Darstellungsgrenze 400 Änderungen); Verteilung je Wochentag und Stundenlage (Vorher gegen Nachher); Tabelle je Regel-Baustein (Vorher, Nachher, besser/schlechter); Hinweise und bereinigte Warnungen; Liste unverplanter Stunden; Kostenkurve über die Schritte (Linien für Ausgangszustand, beste Variante, übrige).
- Gesamturteil: ist der Entwurf schlechter, nennt die Auswertung welche Werte schlechter wurden und gibt eine Empfehlung (STP-039). [unklar: Abstufungen des Urteils]
- Beispiel Bestand (Demo, 2 Minuten): Hohlstunden Klassen 20 → 5,5; Springstunden Lehrkräfte 514 → 311; Standortwechsel 80 → 51; Hauptfächer spät 95 → 71; alle 1.554 Stunden verplant.
Abnahme: Auswertung eines Laufs mit Zeitraum „2. Halbjahr“ vergleicht gegen den Plan dieses Zeitraums; kein Dialog zeigt dieselbe Kennzahl mit zwei verschiedenen Werten; ein schlechterer Entwurf zeigt Empfehlung und Liste der verschlechterten Werte; Diagramm-Werte sind per Maus, Touch und Tastatur erreichbar.

### STP-042 · Aufschlüsselung der Strafpunkte · P2 · Status: Ist
- Die Summe der Bausteine ist exakt die Gesamtkosten (automatischer Test). Je Baustein: Titel, Anzahl (gewichtet), Punkte, wirksames Gewicht, Mittelwert je Verstoß, größte Verursacher (Klasse, Lehrkraft oder Kurs; Generator-Ausgabe Top 5, Vorher-Nachher-Vergleich höchstens 8 mit Wert > 0).
- Kleinstbeträge werden als „Übrige“ zusammengefasst, die kleinsten zuerst, solange die Summe höchstens 2 % der größeren Gesamtsumme (vorher/nachher) beträgt; „Unverplante Stunden“ (Einheit „Stunden“) bleiben immer einzeln. Darstellung mit Zusammensetzung („Hohlstunden Klassen 32 × 100 = 3.215“, „Springstunden Lehrkräfte 936 × 4 = 3.743“, „Gleichmäßig lange Schultage 1.317 × 6 = 7.903“). Begriff „Strafpunkte (niedriger = besser)“ mit (i), nicht „Kosten“.
- Jede Änderung an einer Kostenfunktion verlangt dieselbe Änderung der Aufschlüsselung.
Abnahme: Summe aller Zeilen + „Übrige“ = Gesamtkosten (Test); „Übrige“ ≤ 2 % der Gesamtkosten; Klick auf einen Baustein nennt die Top-Verursacher.

### STP-043 · Varianten (1 bis 5) und Vorschau · P1 · Status: Ist
- Ein Durchgang kann 1 bis 5 Varianten berechnen; die beste (Rangfolge STP-031) wird Hauptergebnis. Vergleichstabelle mit allen Varianten und Kennzahlen, beste markiert, wählbar. Je Variante mehrere Teilläufe (Best-of); alle Teilläufe sind ausgewiesen.
- Vorschau: Der Stundenplan der gewählten Variante ist vor der Übernahme in den Ansichten Klasse, Lehrkraft, Raum im gemeinsamen Raster ansehbar (`GET /planning/jobs/{id}/variants/{index}/timetable/{kind}/{ref}`).
Abnahme: Lauf mit 3 Varianten zeigt 3 Zeilen, die mit den wenigsten Konflikten ist markiert; Auswahl einer anderen Variante ändert die Vorschau; Vorschau verändert den geltenden Plan nicht.

### STP-044 · Übernahme eines Entwurfs · P0 · Status: Ist
- `POST /planning/jobs/{id}/apply` mit gewählter Variante und Schalter „Aufsichten neu berechnen“ (Standard ja); Stunden und Aufsichten werden im selben Schritt geschrieben. Mit Planzeitraum ersetzt die Übernahme nur die Stunden dieses Zeitraums, sonst alle Stunden. Version mit Aktion `plan.generator_apply` (rückgängig machbar). Bestätigung im App-Dialog.
- Vollgenerierung vergibt neue Stunden-Kennungen (L1 … Ln); Ausnahmen (Overrides) und Klausur-Verweise, die an Kennungen hängen, verwaisen. Der Bestätigungsdialog nennt Anzahl betroffener Ausnahmen; Teilneuplanung einer Lehrkraft behält die Kennungen gleicher Blöcke.
- Recht `timetable.generate`.
Abnahme: Übernahme mit Zeitraum „1. Halbjahr“ lässt die Stunden des 2. Halbjahres unverändert; Übernahme mit abgewähltem Schalter lässt die Aufsichten unverändert; der Verlauf enthält eine Version `plan.generator_apply`, Rückgängig stellt den alten Plan her; ohne `timetable.generate` 403.

### STP-045 · Übernahme erkennt veralteten Planstand · P1 · Status: offen
- Ist-Verhalten (Fallstrick): Die Vollübernahme ersetzt alle Stunden, auch wenn der Plan seit Laufbeginn geändert wurde; nur die Abfrage des Laufs zeigt „veraltet“. Entscheidung für den Neubau (Datenverlustrisiko): Die Übernahme prüft die Planversion zu Laufbeginn und lehnt bei Abweichung ab (409, Meldung „Der Plan hat sich seit Beginn des Laufs geändert“), mit Angebot, neu zu rechnen oder bewusst zu überschreiben (zweite Bestätigung, auditiert).
Abnahme: Lauf starten, Stunde verschieben, Übernahme → 409 mit genannter Meldung; mit ausdrücklicher Überschreibung gelingt die Übernahme und der Audit-Eintrag nennt die Überschreibung.

### STP-046 · Plan leeren · P1 · Status: Ist
- `POST /planning/clear` mit `{period}` oder `{all: true}`; bei vorhandenen Planzeiträumen und ohne Angabe 422. Version mit Aktion `plan.clear` bleibt erhalten (rückgängig). Oberfläche: Auswahl eines Zeitraums oder „Ganzer Plan“ mit Bestätigung im App-Dialog; der bisherige Stand bleibt im Verlauf. Recht `timetable.generate`.
- [unklar: Bedingung, unter der die Bestätigung deaktiviert sein kann]; Neubau: die Bestätigung ist nie abschaltbar.
Abnahme: Leeren ohne Angabe bei zwei Zeiträumen → 422; Leeren von „2. Halbjahr“ lässt das 1. Halbjahr unverändert; Rückgängig stellt den Plan wieder her.

### STP-047 · Teilneuplanung einer Lehrkraft · P2 · Status: Ist
- `POST /planning/replan-teacher/{teacher_id}` rechnet den Plan dieser Lehrkraft neu; Blöcke gleicher Gestalt behalten ihre Kennung. Mit Planzeiträumen: 409 „nicht unterstützt“. Recht `timetable.generate`.
Abnahme: Teilneuplanung einer Lehrkraft ändert nur deren Kurse; bei eingerichteten Planzeiträumen 409.

### STP-048 · Oberfläche des Generators · P1 · Status: Ist
- Reiter „Neuaufbau (Generator)“ (früher „Automatische Neuplanung“ entfällt dort). Startformular: Anzahl Varianten, Rechenzeit „Schnell · Normal · Gründlich“, Zeitraum, Startplan kopieren, Probelauf; Startwert und parallele Läufe nur unter „Erweitert“. Laufliste mit Status in Klartext. Ergebnis in Klartext („3 Hohlstunden, 0 Konflikte, 12 Kurse verplant“), nicht „Kosten 42.6“, „Optimierungsschritte“, „removed_lessons: 0“, keine Auftragskennung. „Wochenmuster“ statt „variants“; „1 Hinweis“ (Einzahl); Startwert zeigt den eingestellten Wert. Erklärungen nur hinter (i) an der Beschriftung, keine Erklärabsätze; keine Schieberegler.
- Auswertung (STP-041), Plan-Stände (STP-067), Plan leeren (STP-046) im selben Bereich; Übernahme über App-Dialog; ungespeicherte Eingaben lösen beim Reiter- oder Seitenwechsel eine Rückfrage aus.
- Betreiberzitat: „Dieses Generator Ding ist auch irgendwie komisch.“ und „Das ist irgendwie ein bisschen schlecht erklärt.“ → Begriffe verständlich: „Strafpunkte (niedriger = besser)“, „Wochenmuster“, „Kennzahlen aktualisieren“.
Abnahme: Kein Text der Seite enthält „Seed“, „Job“, „variants“, „Kosten“ oder interne Feldnamen; das Ergebnis nennt Anzahl Hohlstunden, Konflikte und verplante Kurse in einem Satz; Reiterwechsel mit geänderten Eingaben fragt im App-Dialog nach.

### STP-049 · Gründe für unverplante Stunden · P1 · Status: Ist
- Die Kachel „Unverplante Stunden“ nennt je Eintrag den Grund („kein Lehrer“, „erst 3 von 5 gelegt“, „kein freier Raum vom Typ …“) und verlinkt auf den Kurs. Der Qualitätsbericht trennt „Unverplant“ und „Zu viel verplant“. Die Vorab-Engpassanalyse („Warum nicht verplant?“ vor dem Lauf) ist Wunsch (STP-104).
Abnahme: Kurs mit 5 Stunden, von denen 3 gelegt werden konnten, erscheint mit Grund „erst 3 von 5 gelegt“ und Link zum Kurs-Editor.

### 1.5 Qualitätsbericht und Konflikte

### STP-050 · Qualitätsbericht: Kennzahlen und Kacheln · P1 · Status: Ist
- Der Bericht prüft den Gesamtplan; Recht `timetable.edit` oder `timetable.generate`. Kennzahlen (kleiner = besser, Zahl ganzzahlig wenn alle Wochen gleich, sonst Bereich „5–6, Ø 5,5 je nach Woche“):

| Kennzahl | Berechnung | Einheit |
|---|---|---|
| Einzel- und Doppelstunden (Bestand: „Unterrichtsblöcke“) | Anzahl platzierter Blöcke | Blöcke |
| Unverplante Stunden | Anzahl unverplanter Blöcke | Blöcke |
| Zu viel verplant | überzählige Wochenstunden je Kurs | Stunden |
| Lehrkräfte über Deputat | Lehrkräfte mit Stunden > `max_hours` | Lehrkräfte |
| Konflikte | siehe STP-052 | Anzahl |
| Hohlstunden (Klassen) | Freistunden aller Klassen, gewichtet, geteilt durch Anzahl Muster | Stunden je Schulwoche |
| Springstunden (Lehrkräfte) | Freistunden aller Lehrkräfte, gewichtet | Stunden je Schulwoche |
| Standortwechsel | Wechsel aller Lehrkräfte, gewichtet | Wechsel je Schulwoche |
| Hauptfächer spät | Blöcke von Hauptfächern, die nach der spätesten Hauptfachstunde enden (je Kurs gültige Stunde) | Blöcke |
| Wochenmuster | Anzahl Muster (nur bei mehr als einem) | Muster |
| Stunden je Woche | Σ(Länge × Wochen des Musters) / reale Wochen | Stunden je Woche |

- Jede Kachel hat ein „?“ (Bedeutung, Warum, Was tun) und ist klickbar: Kurse → Kurs-Editor; Klassen/Schüler → Listen; Lehrkräfte → Soll und Ist; Hohlstunden/Springstunden → Liste mit Tag, Stunde, Wochen und Link (`/planung/bericht?detail=class_gaps`); Konflikte → Stundenplan; Unverplant → Grund und Kurslink. Der Knopf „Kennzahlen aktualisieren“ ändert nie den Plan.
- Positionen im Klartext (z. B. „Dienstag, 1. Stunde: Lehrkraft doppelt belegt, Klassen 5a und 5b“), nicht „Woche 0, Tag 2, L1, L36“. Eine Kursänderung, die eine Doppelbelegung erzeugt, liefert Warnungen; der Vertretungsplan des Tages zeigt sie. Hohl- und Springstunden berücksichtigen nur den regulären Plan.
- Wochen ohne Plan (Planzeitraum) werden mit Gewicht 0 ausgelassen.
Abnahme: Die Kachel „Hohlstunden“ öffnet die Liste mit Klasse, Tag, Stunde und Wochen; die Kennzahl „Unverplante Stunden“ nennt je Eintrag den Grund; zwei Wochenmuster mit 5 und 6 Hohlstunden zeigen „5–6, Ø 5,5“; „Kennzahlen aktualisieren“ erzeugt keine neue Planversion.

### STP-051 · Pendelregeln und Wegezeit · P1 · Status: Ist
| Pendelart (je Lehrkraft) | Bedeutung | Wirkung |
|---|---|---|
| nie pendeln (`never`) | nie am selben Tag an zwei Standorten | Vertretung: hart; Generator: weich mit Faktor 40 |
| höchstens 1× am Tag (`once`) | höchstens ein Standortwechsel je Tag | jeder weitere Wechsel mit Faktor 40 |
| beliebig (`free`, Standard) | keine Einschränkung | Wechsel nur über Wegezeit bzw. Pause |

- Ist keine Pendelart gewählt, gilt das alte Ja/Nein-Feld („nein“ = nie pendeln, „ja“ = beliebig).
- Wegezeit je Standortpaar (Minuten, beide Richtungen, `site_travel`); ohne Eintrag `site_travel_periods` = 1 freie Stunde. Mindestpause der Lehrkraft `commute_gap` (Standard 0 min); wirksam ist der größere Wert aus Wegezeit und Mindestpause. Pause zwischen zwei Stunden = Beginn der späteren − (Beginn der früheren + Stundenlänge 45 min). Wechsel zulässig: gleicher oder unbekannter Standort immer; „nie pendeln“ nein; sonst Pause ≥ max(Wegezeit des Paars; Mindestpause); ohne Wegezeit des Paars mindestens so viele freie Stunden wie `site_travel_periods`; ohne Uhrzeiten nur nach freien Stunden.
- Verstoßtexte: „pendelt nicht, wechselt aber den Standort“; „<n> Standortwechsel an einem Tag (erlaubt: 1)“; „zu kurze Pause beim Wechsel <A> → <B> (<p>. → <q>. Stunde, <min> Min.)“. Die Pendelverstöße erscheinen auf der Seite des Qualitätsberichts (Bestand: nur gezählt, nicht sichtbar) [Status der Sichtbarkeit: offen].
- Die Wegezeit je Standortpaar gehört fachlich zum Baustein „Standortwechsel vermeiden“ (derzeit noch im Tab „Vertretung & Abwesenheit“) [offen].
Abnahme: Lehrkraft „nie pendeln“ wird vom Generator nicht an zwei Standorte am selben Tag gelegt, außer als Strafpunkt-Ausnahme; Wegezeit 20 min zwischen A und B bei 5 min Pause zwischen den Stunden verbietet den Wechsel; Qualitätsbericht listet Pendelverstöße mit Text.

### STP-052 · Konflikte im Stundenplan · P0 · Status: Ist
- Konflikt = harte Verletzung in der Gesamtprüfung; zählt in der Kennzahl „Konflikte“ und darf bei „Plan prüfen“ nicht steigen: Klasse (mehr Stunden am Tag als erlaubt, Sperrzeit, gleichzeitig anderer Unterricht); Lehrkraft (nicht verfügbar, gleichzeitig Unterricht); Kurs (mehr Blöcke an einem Tag als das Fach-Limit zulässt, je Wochenmuster); Raum (kein freier Raum des benötigten Typs); Standortwechsel ohne ausreichende Pause (Lehrkraft) bzw. ohne Wegezeit (Lehrkraft oder Klasse).
- Die Gesamtprüfung listet höchstens 200 Konflikte; die Detailauswertung begrenzt jede Liste. Stunden, die in kein Wochenmuster passen oder nach Zeitrasteränderung außerhalb liegen, werden gemeldet.
Abnahme: Zwei Stunden derselben Lehrkraft zur selben Zeit erzeugen genau einen Konflikt mit beiden Klassen im Text; eine Liste mit über 200 Konflikten zeigt 200 und den Hinweis auf weitere.

---
### 1.6 Regeln und Prioritäten der Optimierung

### STP-053 · Bausteine und Wichtigkeitsstufen statt Zahlen · P0 · Status: Ist
- Jede weiche Regel ist ein Baustein mit Titel, Hilfe (Erklärung hinter dem Hilfe-Symbol an der Beschriftung), Wichtigkeitsstufe, Voraussetzung (Datenbezug) und Geltungsbereich, optional einem Parameter. Die Regeln gelten je Schule; Ausnahmen je Jahrgang, Klasse, Fach, Lehrkraft und Woche (STP-057).
- Fünf Stufen in Wortform, nie als nackte Zahlen: Aus (Faktor 0), Nett (0,25), Wichtig (1, entspricht dem Standardwert), Sehr wichtig (4), Muss (20, praktisch hart; bei „Hauptfächer früh am Tag“ eine echte harte Regel). Ein Zahlenwert wird auf die nächste Stufe abgebildet; unter „Erweitert“ bleibt je Baustein ein eigener Zahlenwert möglich. Schalter-Bausteine (z. B. „Automatisch neu planen“) haben eine eingeschränkte Stufenliste [unklar: Einzelheiten].
- Reiter „Regeln“ in der Planung (früher „Prioritäten“; Seite `/planung/regeln`); der Reiter „Vertretung & Abwesenheit“ trägt die Vertretungsregeln (VER-012). Die Gewichte für Generator und Vertretung bleiben abgeglichen.
- Betreiberzitat (12.10.): „Dieses Prioritäten und Regelding ist kompletter Müll … wie das modularer sein kann, wie das mehr Schulen unterschiedlich nutzen können … dass auch immer nur das angezeigt wird, was die Schulen brauchen oder was sie nicht brauchen.“ Ausgangsprobleme, die nicht wieder entstehen dürfen: zehn nackte Zahlen mit Schiebereglern und willkürlichen Höchstwerten; alle Regeln pauschal für die ganze Schule (Hohlstunden Oberstufe wie Klasse 5; Grundschulen sahen Standortwechsel und Lehrerwünsche); vier fremde Themen auf einer Seite; keine Rückmeldung zur Wirkung, keine Vorschau, kein Export; Klausur-Höchstzahlen an der falschen Stelle.
- Keine Schieberegler; Zahlen als Zahlenfeld, Stufen als Stufenauswahl (2 bis 5 gleichrangige Optionen nebeneinander).
Abnahme: Die Seite zeigt je Baustein die Stufen „Aus · Nett · Wichtig · Sehr wichtig · Muss“ als Auswahl und keine Zahlen oder Schieberegler; Wechsel auf „Sehr wichtig“ speichert Faktor 4; die Hilfe eines Bausteins erscheint nach 2 s Verweilen am Namen; ohne `settings.edit` sind die Auswahlfelder gesperrt und nennen den Grund.

### STP-054 · Bausteinkatalog und Parameter · P1 · Status: Ist
Katalog, gruppiert (Schlüssel und Grundgewichte siehe STP-034):
- Für Schülerinnen und Schüler: Keine Hohlstunden für Klassen · Unterricht beginnt zur ersten Stunde · Gleichmäßig lange Schultage · Hauptfächer früh am Tag (Parameter „spätestens bis Stunde“; nur wirksam, wenn ein Fach als Hauptfach markiert ist).
- Unterricht und Fächer: Fächer über die Woche verteilen · Doppelstunden als Block (Parameter: alle Fächer ab 2 Wochenstunden; Lage in Pausenblöcken) · Unterricht möglichst früh am Tag (nur unter „Erweitert“).
- Für Lehrkräfte: Wenige Springstunden · Wünsche der Lehrkräfte berücksichtigen (nur wenn Wünsche vorliegen) · Standortwechsel vermeiden (Parameter Wegezeit; nur bei mehr als einem Standort).
- Automatik: nach Änderungen automatisch neu planen (Schalter).

| Parameter | Standard | Bereich | Einheit | Wirkung |
|---|---|---|---|---|
| `core_latest_period` | 5 (gespeichert 0-basiert; Anzeige „6. Stunde“) | 0 bis 15 | Stunde | späteste Hauptfachstunde; muss kleiner als die Zahl der Stunden sein (Fehler „Späteste Hauptfachstunde liegt außerhalb des Zeitrasters“) |
| `site_travel_periods` | 1 | 0 bis 5 | freie Stunden | Wegezeit zwischen Standorten ohne Tabelle |
| `prefer_doubles` | ja | ja/nein | – | alle Fächer ab 2 Wochenstunden als Doppelstunden |
| `double_alignment` | „bloecke“ | bloecke / pausen / frei | – | Lage der Doppelstunden (STP-032) |

- Karte „Gilt immer (harte Regeln)“: Verweise auf die Daten Sperrzeiten, Unterrichtstage und Höchststunden je Klasse; Sperrzeiten, Arbeitszeiten und Deputat je Lehrkraft; Fachräume; Blöcke eines Fachs pro Tag; Wegezeit; zeigt die Zahl der Einträge mit eigenen Angaben. Harte Regeln sind nicht über Bausteine einstellbar.
Abnahme: Parameter „spätestens bis Stunde“ = 20 bei 10 Stunden je Tag wird mit der genannten Fehlermeldung abgelehnt; `site_travel_periods` = 6 → 422; die Karte „Gilt immer“ zeigt z. B. „3 Klassen mit eigenen Sperrzeiten“ mit Link.

### STP-055 · Vorlagen nach Schulart · P1 · Status: Ist
Beim ersten Öffnen wählt die Schule eine Vorlage; ohne Wahl gilt „standard“ (Allgemein). Eine Vorlage bringt Stufen, Parameter, Ausnahmen und die Liste der sichtbaren Bausteine mit; `auto_replan` ist in allen Vorlagen „an“. Neun Vorlagen (Stufe je Baustein; Standard-Parameter in Klammern):

| Vorlage | Keine Hohlstd. | Früher Beginn | Gleich lange Tage | Hauptfächer bis (Stufe) | Fächer verteilen | Doppelstunden (Stufe; Lage) | Springstd. | Wünsche | Standortwechsel (Stufe; Wegezeit) | Position |
|---|---|---|---|---|---|---|---|---|---|---|
| standard (Allgemein) | Wichtig | Wichtig | Wichtig | 5 (Wichtig) | Wichtig | Wichtig; an; bloecke | Wichtig | Wichtig | Wichtig; 1 | Wichtig |
| grundschule | Muss | Sehr wichtig | Sehr wichtig | 3 (Wichtig) | Wichtig | Nett; aus; frei | Nett | Wichtig | Wichtig; 1 | Wichtig |
| gymnasium | Sehr wichtig; Ausnahme Jg. 11–13: Nett | Wichtig; Ausnahme Jg. 11–13: Nett | Wichtig | 5 (Wichtig) | Wichtig | Wichtig; an; bloecke | Wichtig | Wichtig | Wichtig; 1 | Wichtig |
| gesamtschule | Sehr wichtig; Ausnahme Jg. 11–13: Nett | Wichtig | Sehr wichtig | 5 (Wichtig) | Wichtig | Sehr wichtig; an; bloecke | Wichtig | Wichtig | Wichtig; 1 | Nett |
| berufsschule | Wichtig | Nett | Nett | aus (7) | Nett | Sehr wichtig; an; pausen | Wichtig | Wichtig | Sehr wichtig; 1 | Nett |
| foerderschule | Muss | Sehr wichtig | Sehr wichtig | 3 (Wichtig) | Sehr wichtig | Nett; aus; frei | Nett | Wichtig | Wichtig; 1 | Wichtig |
| montessori | Sehr wichtig | Wichtig | Wichtig | aus (5) | Nett | Sehr wichtig; an; frei | Nett | Wichtig | Wichtig; 1 | Nett |
| abendschule | Sehr wichtig | aus | Wichtig | aus (7) | Wichtig | Wichtig; an; pausen | Wichtig | Sehr wichtig | Wichtig; 1 | aus |
| ganztag | Sehr wichtig | Wichtig | Sehr wichtig | 5 (Wichtig) | Wichtig | Wichtig; an; bloecke | Wichtig | Wichtig | Wichtig; 1 | Nett |

- Grund- und Förderschule setzen Doppelstunden bewusst aus („Einzelstunden statt langer Blöcke“). Bei Berufsschule, Montessori und Abendschule ist die Hauptfach-Grenze wirkungslos (Stufe aus, Parameter bleibt gespeichert). Beispiele aus dem Betreiberwunsch: Gymnasium Hohlstunden „Sehr wichtig“ mit Ausnahme Jahrgang 11–13 „Nett“; Berufsschule ohne Regel „erste Stunde“; Abendschule ohne „früh am Tag“.
- [unklar: Ob das Anwenden einer Vorlage die aktuellen Regeln ersetzt und ob die Schule später eine andere Vorlage wählen kann.] Neubau: Anwenden zeigt zuerst die Änderungen (Vorher/Nachher je Baustein) und ersetzt erst nach Bestätigung im App-Dialog; Recht `settings.edit`.
Abnahme: Anwenden von „grundschule“ setzt „Keine Hohlstunden“ auf Muss, Doppelstunden-Stufe Nett, Lage „frei“ und `core_latest_period` 3; „gymnasium“ liefert die Ausnahme „Jahrgang 11–13: Nett“ bei Hohlstunden; „berufsschule“ blendet „Hauptfächer früh“ ohne Wirkung aus.

### STP-056 · Sichtbarkeit der Bausteine und „Erweitert“ · P1 · Status: Ist
- Ein Baustein erscheint, wenn (a) er Datenbezug hat (Standorte > 1, Hauptfächer markiert, Wünsche vorliegen) und (b) die Vorlage ihn zeigt oder die Schule ihn gegenüber der Vorlage verändert hat. „Erweitert“ zeigt alles, auch Bausteine ohne Datenbezug (mit Begründung) und die Zahlenwerte. Kein Feature fällt durch die Vorlage weg.
- Planung zeigt nur, was die Schule braucht (Betreiber: „dass auch immer nur das angezeigt wird, was die Schulen brauchen“); Beispiel: „Standortwechsel“ nur bei mehr als einem Standort.
Abnahme: Schule mit einem Standort sieht „Standortwechsel vermeiden“ nur unter „Erweitert“ mit der Begründung „nur bei mehr als einem Standort“; ohne markierte Hauptfächer erscheint „Hauptfächer früh“ nicht in der Grundansicht; „Erweitert“ zeigt alle 11 Bausteine.

### STP-057 · Ausnahmen je Gültigkeitsbereich · P1 · Status: Ist
- Ein Baustein kann je Gültigkeitsbereich eine andere Stufe haben (und bei „Hauptfächer früh“ einen anderen Parameter, z. B. Grundschule bis 4. Stunde, Oberstufe bis 8. Stunde). Felder: Stufe, Jahrgänge (Ganzzahlen), Klassen, Fächer, Lehrkräfte, Wochen (Liste) oder Rhythmus, Parameter, Notiz. Die erlaubten Dimensionen richten sich nach dem Baustein (Klassenregeln: Jahrgang/Klasse; Kursregeln zusätzlich Fach; Lehrkraftregeln: Lehrkraft).
- Mehrere Ausnahmen gelten der Reihe nach; die letzte passende gewinnt (eindeutige Vorrangregel für den Neubau). Ausnahmen mit Wochenbezug bilden eigene Wochenmengen und wirken anteilig: Gewicht = Gewicht × (1 − Anteil) + Gewicht der Ausnahme × Anteil je Wochenmuster. Eine Parameter-Ausnahme wirkt nur bei voller Abdeckung (Anteil ≥ 99,9 %).
- Fehler ohne jede Gültigkeit: „Eine Ausnahme braucht eine Gültigkeit (Jahrgang, Klasse, Fach, Lehrkraft oder Wochen).“
- Grenzen: höchstens 50 Ausnahmen je Baustein, Notiz je Ausnahme höchstens 120 Zeichen.
- Anzeige als Sätze: „Für Jahrgang 11–13: Nett“, „In Woche 1–2: Aus“.
Abnahme: Ausnahme „Jahrgang 11–13: Nett“ senkt das Gewicht für Hohlstunden dieser Klassen von 400 auf 25; zwei Ausnahmen für dieselbe Klasse: die spätere gewinnt; Ausnahme nur für Woche 1–2 wirkt anteilig (2 von 52 Wochen); die 51. Ausnahme wird abgelehnt; Ausnahme ohne Gültigkeit liefert die genannte Fehlermeldung.

### STP-058 · Wirkung anzeigen und Probelauf · P1 · Status: Ist
- Wirkungsanzeige je Baustein: „betrifft N Klassen · aktuell M Verstöße → Bericht“; die Verstöße stammen aus dem Qualitätsbericht (Hohlstunden, Springstunden, Standortwechsel, späte Hauptfächer, später Beginn, Fach an Folgetagen, zerlegte Doppelstunden, Treffer in Wunschzeiten) und verlinken dorthin. „Gleichmäßig lange Schultage“ und „früh am Tag“ haben bewusst keinen Zählwert, weil sie Kosten und keine Verstöße sind.
- Probelauf („Simulation“): Aus einem Entwurf der Regeln wird ein Generatorlauf gerechnet, ohne die Einstellungen zu ändern; der Reiter zeigt Kennzahlen aktuell gegen Entwurf (unverplante Stunden, Hohl- und Springstunden, späte Hauptfächer, Standortwechsel) mit „besser/schlechter“ je Baustein. Nichts wird automatisch übernommen. Der Entwurf liegt als Lauf im Generator-Reiter mit Hinweis auf den Probelauf. Der Probelauf läuft über den Generator-Start (Recht `timetable.generate`) und wird nicht mit einem Testlauf verwechselt.
Abnahme: Ein Probelauf mit geändertem Hohlstunden-Gewicht verändert `GET /settings/rules` nicht; er erscheint in der Laufliste als „Probelauf“ und im Reiter als Vergleich; ohne `timetable.generate` 403.

### STP-059 · Eigene Vorlagen, Export und Import · P2 · Status: Ist
- Eigene Vorlagen: speichern (Name höchstens 80 Zeichen, Beschreibung höchstens 300), anwenden, löschen; höchstens 30 je Schule; gespeichert in den Schuleinstellungen. Export als JSON (im Frontend auch ohne Serverantwort), Import durch Hochladen des Inhalts. Das Format muss exakt dem Vorlagenformat entsprechen, sonst meldet der Import, welche Bausteine nicht erkannt wurden. Recht `settings.edit` (anwenden, speichern, löschen).
Abnahme: Export einer Vorlage und Import in eine zweite Schule liefern gleiche Stufen, Parameter und Ausnahmen; die 31. Vorlage wird abgelehnt; ein JSON mit unbekanntem Baustein-Schlüssel wird mit Nennung des Schlüssels abgelehnt.

### STP-060 · Übernahme älterer Regelstände · P2 · Status: Ist
- Keine Datenbankmigration. Fehlende Bausteine werden aus den bisherigen Zahlen abgeleitet: Gewicht 0 → Aus; exaktes Vielfaches → Stufe; sonst nächste Stufe plus eigener Zahlenwert. Dokumente ohne Bausteine gelten als Vorlage „standard“. Ältere Oberflächen, die nur Zahlen senden, funktionieren weiter (Bausteine folgen; Ausnahmen bleiben). Änderungen über Bausteine oder Zahlen werden gegenseitig übernommen, sodass die Anzeige konsistent bleibt.
Abnahme: Ein Dokument mit `weights.class_gap` = 100 ergibt „Wichtig“, 400 „Sehr wichtig“, 0 „Aus“, 150 „Wichtig“ mit eigenem Wert 150; ein Dokument ohne Bausteine lädt als „standard“.

### STP-061 · Grenzen für Klassenarbeiten (Vorgaben und Vererbung) · P1 · Status: Ist
- Höchstzahl Klassenarbeiten/Klausuren je Klasse und Woche sowie je Tag. Ebenen: Schulvorgabe (`max_exams_per_week` Standard 3, `max_exams_per_day` Standard 1); Vorgabe je Jahrgang (`exam_limits_by_grade`, Jahrgang 1–14, je Woche 0–20, je Tag 0–5, jeder Wert einzeln optional); eigener Wert der Klasse (leer = erbt). Auflösung Klasse → Jahrgang → Schule, die Quelle wird angezeigt („max. 2 je Woche, 1 je Tag (Jahrgang)“, gemischt: „Woche: Klasse, Tag: Schule“). Tests (Art „test“) zählen nicht in die Höchstzahlen.
- Oberfläche: Vorgaben (Schule; je Jahrgang eine Tabelle aller vorhandenen Jahrgänge mit Spalte „Klassen mit eigenen Werten“) auf der Seite Klausuren, Recht `settings.edit`. Klassen-Editor: Feld „Klassenarbeiten / Klausuren“ mit Text „Wie Vorgabe (Jahrgang 7: 2 je Woche, 1 je Tag)“ oder eigenen Werten; Kopf der Klassenseite mit Zeile „Klassenarbeiten“ (wirksame Werte und Quelle), Ändern mit Recht `masterdata.edit`. Unter „Zeitraster & Schuljahr“ steht nur ein Verweis. Die Klausurprüfung (VER-063) nutzt die Klassenwerte.
- Wert 0 bedeutet „keine Grenze“ (Hilfe-Text); ein leeres Feld erbt und führt zu keinem Fehler. Der Bestand rechnet 0 wie 1 (`max(1; …)`); Neubau-Festlegung: 0 = keine Grenze, Bestätigung durch den Betreiber steht aus.
Abnahme: Jahrgang 7 mit 2 je Woche und Klasse 7a ohne eigenen Wert zeigt „Jahrgang“ als Quelle; Klasse 7b mit eigenem Wert 3 zeigt „Klasse“; Wert 0 je Tag erlaubt beliebig viele Klausuren am Tag; Schulvorgabe ändern ohne `settings.edit` → 403; Klassenwert ändern ohne `masterdata.edit` → 403.

### STP-062 · Sperrregeln nach Rhythmus (Zeitsperren) · P2 · Status: Ist
- Sperrregeln werden in Text und Auswertung beschrieben (welche Plätze gesperrt sind); blockierte Plätze erscheinen im Raster durchgehend schraffiert. Ein Editor-Element (Umschalter) bedient die Sperrregeln; Regeln werten die laufende Woche aus (Woche, Tag, Stunde). Zeitfenster-Sperren der Lehrkräfte erkennt man am Notiz-Präfix „Zeitfenster“ (STP-004).
- [unklar: Zusammenspiel der Sperrregeln mit den Lehrkraft-Zeitfenstern im Raster.]
Abnahme: Eine Sperre „Mi, Stunde 5–8, jede 2. Woche ab Woche 2“ erscheint in Woche 2 schraffiert im Raster der Klasse, in Woche 3 nicht.

### STP-063 · Rechte, Audit und Lesezugriff der Regeln · P0 · Status: offen
- Schreiben der Regeln und Vorlagenaktionen: `settings.edit`; Probelauf: `timetable.generate`; Wirkungsanzeige: Rechte des Qualitätsberichts (`timetable.edit` | `timetable.generate`).
- Der Bestand erlaubt Lesen und Export für alle Angemeldeten [prüfen]. Neubau: Lesen und Export nur mit `settings.edit`, `timetable.edit` oder `timetable.generate`; Schüler/innen und Eltern erhalten 403.
- Jede schreibende Regelaktion (Speichern, Vorlage anwenden/speichern/löschen, Import) wird im Audit-Protokoll festgehalten, ohne Regelinhalt. Die Regeln enthalten keine personenbezogenen Daten außer Klassen-, Lehrkraft- und Fachbezug in Ausnahmen.
Abnahme: GET Regeln als Schüler/in → 403; Speichern einer Regel erzeugt einen Audit-Eintrag „Regeln geändert“ ohne Inhalte; Vorlage löschen erzeugt einen Audit-Eintrag.

### STP-064 · Regeln, die noch nicht bewertet werden · P2 · Status: offen
- Im Katalog vorbereitet, aber im Generator ohne Bewertung: Tageszeit-Anker („Freiarbeit immer vormittags“), Blocklänge 3, „Fach X nie nach Fach Y“, Stundensoll je Zyklus.
- Doppel- und Einzelstunde desselben Kurses nicht am selben Tag, solange genug Tage frei sind (Bestandsfehler: 14 Fälle in der Demo; Betreiberbeanstandung 11.10.: „zweimal eine Doppelstunde Englisch und dann eine Einzelstunde“); keine leere erste Stunde (Betreiber: „die erste Stunde nichts. Das ist irgendwie doof“; der Baustein „Unterricht beginnt zur ersten Stunde“ ist die weiche Form).
- Für „Gleichmäßig lange Schultage“ und „früh am Tag“ fehlen Verstoßzahlen (nur Kosten). Wegezeit je Standortpaar gehört in den Baustein „Standortwechsel vermeiden“. Entfall erlaubt ab Klassenstufe ist nicht jahrgangsbezogen; eine Klassenausnahme gehört zur Vertretung (VER-012).
Abnahme: Ein Kurs mit Doppelstunde und Einzelstunde liegt bei ≥ 5 freien Tagen nie am selben Tag; der Katalog führt „Fach X nie nach Fach Y“ mit Bewertung im Generator.

### 1.7 Planzeiträume, Planzustand, Plan-Stände

### STP-065 · Planzeiträume (Halbjahre) · P1 · Status: Ist
- Je Zeitraum: Kennung, Name, Beginn, Ende, erste und letzte Schulwoche (aus den Daten berechnet); ein Zeitraum umfasst ganze Wochen und liegt im selben Schuljahr; höchstens 12 Zeiträume je Schule. Leere Liste = ein Plan für das ganze Schuljahr (Stunden ohne Zeitraum gelten überall).
- Standardvorgabe: „1. Halbjahr“ (Kennung „hj1“) vom Schuljahresbeginn bis zur Woche des 31. Januars (auf 1 bis Y − 1 begrenzt), „2. Halbjahr“ („hj2“) danach bis Schuljahresende; bei Y ≤ 1 ein einziger Zeitraum. Verwaltung unter Planung → Zeitraster & Schuljahr; Speichern `settings.edit`.
- Jeder Zeitraum hat seinen eigenen, wochenbasierten Plan. Aktionen: Plan aus anderem Zeitraum kopieren (`POST /calendar/plan-periods/{id}/copy/{source}`; Neubau: bei vorhandenem Zielplan Rückfrage, überschrieben wird erst nach Bestätigung), Plan eines Zeitraums löschen (`DELETE …/plan`), Generatorlauf je Zeitraum (nur dessen Stunden werden neu gerechnet), Plan-Stände und Varianten je Zeitraum. Kopieren/Löschen: `timetable.generate`.
- Bericht und Plan prüfen lassen Wochen ohne Plan aus (Gewicht 0). Plan prüfen repariert im Zeitraummodus nur Räume und verwaiste Stunden (freie Kurse bleiben leer); Teilneuplanung einer Lehrkraft ist gesperrt (409). Der Schuljahreswechsel verschiebt bzw. berechnet die Zeiträume neu. Neue Stunden aus Import, Plan leeren oder Untis-Import setzen ihren Zeitraum oder lassen ihn leer (= überall gültig).
Abnahme: Standardvorgabe bei Schuljahr mit 52 Wochen und 31. Januar in Woche 26 ergibt hj1 = Wochen 1–26, hj2 = 27–52; ein Zeitraum von Mi bis Mi wird abgelehnt (keine ganzen Wochen); die 13. Zeitraum-Eintragung wird abgelehnt; Generatorlauf für hj2 ändert hj1-Stunden nicht.

### STP-066 · Planzustand einer Woche und Hinweis „kein Stundenplan“ · P1 · Status: Ist
- Zustand je Woche: „ok“ (Zeitraum hat einen Plan), „missing“ (Zeitraum ohne Plan), „none“ (Woche in keinem Zeitraum). Ohne Plan zeigen Stundenplan, Vertretungsplan, Monitor, Druck und Startseite „Für diesen Zeitraum ist noch kein Stundenplan festgelegt“ (mit Zeitraum); der Knopf „Zum Generator“ nur mit `timetable.generate`. Termine und Ferien bleiben sichtbar. Schüler/innen und Eltern sehen den Hinweis nur bei Planzeiträumen und ohne Plan, ohne Knopf. Wochen ohne Plan sind im Wochenraster des Kalenders schraffiert.
Abnahme: Woche in hj2 ohne Plan zeigt den Hinweis im Stundenplan und Monitor; als Schülerkonto fehlt der Knopf; ein eingetragener Feiertag in dieser Woche bleibt sichtbar.

### STP-067 · Plan-Stände (Sicherungen) · P1 · Status: Ist
- Speichern des aktuellen Plans oder eines Generator-Entwurfs unter einem Namen (Name höchstens 120 Zeichen, Notiz höchstens 500; Beispiel „Stand Herbst A“); gespeichert werden nur die Unterrichtsstunden und die Kennzahlen zum Speicherzeitpunkt, Quelle „aktuell“ oder „entwurf“. Höchstens 50 Stände [unklar: je Schule oder insgesamt; Neubau: je Schule]. Mit Planzeiträumen gilt standardmäßig nur der Zeitraum; „ganzer Plan“ nur mit ausdrücklicher Option.
- Ansehen (Kennzahlen, Vergleich gegen den aktuellen Plan desselben Zeitraums, Stundenplan je Art und Bezug), Wiederherstellen (ersetzt die Stunden des Zeitraums bzw. den ganzen Plan; Tagesentscheidungen zu geänderten Stunden werden verworfen; Version `plan.snapshot_restore`; existiert der Zeitraum nicht mehr: 409), Löschen. Lesen: `timetable.generate` | `timetable.edit`; Anlegen, Wiederherstellen, Löschen: `timetable.generate`. Speichern, Wiederherstellen und Löschen laufen über App-Dialoge.
Abnahme: Stand „Herbst A“ speichern, Plan ändern, wiederherstellen → Stundenliste identisch zum Stand, Version `plan.snapshot_restore` im Verlauf; der 51. Stand wird abgelehnt; Wiederherstellen ohne `timetable.generate` 403.

### STP-068 · Pläne mit Gültigkeit „ab Datum“ · P1 · Status: offen
- Wunsch (Backlog B-46, XL): Der Stundenplan hat Gültigkeitszeiträume. „Übernehmen“ aus Generator, Untis-Import und Verschieben fragt „gültig ab“ (Standard: nächster Montag). Vertretungsplan, Klassenwoche, iCal und Statistiken nutzen je Datum den gültigen Plan; die Vergangenheit ändert sich nicht. Lehrkräfte und Schüler/innen sehen den künftigen Plan ab Freigabe als Vorschau. Kursräume („zur Stunde“) und Konfliktprüfungen nutzen die gültige Periode. Alte Dokumente gelten als eine Periode ab Schuljahresbeginn.
- Bestand: Stunden mit eigenem Gültigkeitsbeginn kennt das Planungsdokument nicht; Planvorschläge tragen nur den Hinweis „gilt ab“, die Übernahme ersetzt den Plan für alle Wochen; Übergangszeiten laufen über „Vertretung statt Planänderung“. Sperrzeiten haben bereits „gilt ab“ (STP-004).
Abnahme: Übernahme mit „gültig ab 02.02.2027“ lässt den Vertretungsplan vom 26.01.2027 unverändert und nutzt ab 02.02. den neuen Plan; die Statistik der Vorwochen bleibt gleich.

---
### 1.8 Plan prüfen (Dauerprüfung und Planvorschläge)

### STP-069 · Plan prüfen: Prinzip, Auslöser, Ablauf · P0 · Status: Ist
- Der reguläre Plan wird dauernd und automatisch auf Probleme geprüft. Bei Änderungen (Lehrkraft ändert Sperrzeiten, Raum fällt aus, Kurs oder Stundentafel ändern sich) berechnet das System mehrere Lösungen und legt sie den Zuständigen zur Auswahl vor. Menschen entscheiden; es gibt keine automatische Entscheidung durch das System (Ausnahme: STP-076). Betreiberzitate (12.10.): „Das soll aber eigentlich permanent die ganze Zeit automatisch gemacht werden, sobald jegliche Updates im Stundenplan passieren“; „Menschen mögen es lieber, eine Auswahl zu haben … Ne, ich muss jetzt genau das nehmen, weil das ist die KI.“ Der Generator bleibt für den Neuaufbau zum Schuljahr.
- Auslöser (Änderungsbereiche): Lehrkräfte, Räume, Klassen, Kurse, Stundentafeln, Fächer, Einstellungen, Standorte, Stunden, Stundenplan, Import, Initialisierung. Ignoriert werden eigene Änderungen der Planung (Übernahmen) sowie Rückgängig/Wiederherstellen (sie merken sich den Stand, ohne sofort neu zu prüfen). Krankmeldungen, Raumsperren und Klassenfahrten ändern den regulären Plan nicht (Tagesplan der Vertretung). „Lehrkraft meldet: ab nächster Woche mittwochs nicht“ ist eine Sperrzeit mit Gültigkeitsbeginn; nach Genehmigung entsteht daraus ein Paket.
- Entprellung: Ruhezeit nach der letzten Änderung `SM_AUTOPLAN_DELAY` (Standard 3,0 s); mehrere schnelle Änderungen ergeben eine Prüfung; die Prüfung läuft in eigener Verarbeitung und blockiert keine Anfrage. Abschaltbar je Schule (`auto_replan` aus → Status „ausgeschaltet“) und global (`SM_AUTOPLAN` = 0).
- Ablauf: Keine Probleme → offene Pakete werden „erledigt“, Status „Plan in Ordnung“. Derselbe Planstand wurde schon vorgeschlagen → nichts geschieht. Sonst werden ältere offene Pakete „ersetzt“ und ein neues Paket mit Status „Berechnung“ angelegt (je Variante eine Berechnung, nacheinander). Ist das Paket offen, erscheinen Zähler, Hinweis (Toast) und Startseiten-Kachel.
- Manueller Start: Knopf „Jetzt prüfen“ (`POST /api/v1/planning/autoplan/run`, `timetable.generate`); Status `GET /api/v1/planning/autoplan`.
Abnahme: Eine neue Sperrzeit einer Lehrkraft löst nach ca. 3 s genau eine Prüfung aus (drei Änderungen innerhalb von 2 s ergeben ebenfalls eine); eine Krankmeldung erzeugt kein Paket; Rückgängig löst keine Prüfung aus; mit `auto_replan` aus zeigt der Status „ausgeschaltet“; kein Plan wird ohne Zustimmung geändert.

### STP-070 · Prüfungen des regulären Plans · P0 · Status: Ist
Harte Verstöße je Stunde (Meldungen in Klartext, Kurzform):

| Nr. | Prüfung | Meldung |
|---|---|---|
| 1 | Stunde außerhalb des Zeitrasters (Tag ≥ Schultage, Stunde < 0, Stunde + Länge > Stunden je Tag) | „liegt außerhalb des Zeitrasters“ |
| 2 | Klasse: Stunde ≥ Höchststunden je Tag | „Klasse <Name> hat höchstens <n> Stunden am Tag“ |
| 3 | Klasse: Sperrzeit (Regel, Woche, Rhythmus) | „Klasse <Name> ist <Tag> <n>. Std. nicht da (<Grund>)“ |
| 4 | Lehrkraft: Sperrzeit | „Lehrkraft <Kürzel> ist … gesperrt (<Grund>)“ |
| 5 | Lehrkraft: Standort nicht eingesetzt | „Lehrkraft <Kürzel> unterrichtet nicht am Standort <Standort>“ |
| 6 | Raum: fester Raum des Kursteils nicht genutzt | „<Fach> gehört in den festen Raum <Raum>“ |
| 7 | Raum existiert nicht mehr | „Raum <Id> gibt es nicht mehr“ |
| 8 | Raumtyp falsch | „<Fach> braucht einen Raum vom Typ <Typ> (Raum <Id> ist <Typ>)“ |
| 9 | Kein Raum, obwohl Raumtyp nötig | „<Fach> braucht einen Raum vom Typ <Typ>“ |
| 10 | Doppelbelegung Klasse/Lehrkraft/Raum | „… hat … schon Unterricht (<andere Stunde>)“ bzw. „doppelt belegt“ |
| 11 | Stunde ohne Kurs (verwaist) | „<n> Stunde(n) ohne Kurs“ |
| 12 | Fehlende Wochenstunden eines Kurses | „<Kurs>: <n> Stunde(n) nicht verplant“ |
| 13 | Überzählige Wochenstunden | „<Kurs>: <n> Stunde(n) zu viel“ |

- Raumverstöße gelten als „nur Raum“, wenn keine anderen Gründe vorliegen. Fixierte Stunden werden zuerst gesetzt; bei Doppelbelegung bleibt die fixierte, die andere gilt als Problem. Wochenangaben werden über alle Wochen eines Kurses geprüft (je Wochengruppe nur Wochen, in denen der Plan gilt).
- Zählmaß für „besser/schlechter“: Stunden mit Verstoß + verwaiste + fehlende + überzählige Stunden. Problemlage-Kennung (Signatur) = Fingerabdruck der sortierten Verstöße; gleiche Lage → kein neuer Versuch. Kurzfassung für den Verlauf: höchstens 12 Gründe, dann „… und <n> weitere“.
Abnahme: Eine Stunde in der 11. Stunde bei 10 Stunden je Tag erzeugt Meldung 1; zwei Stunden derselben Lehrkraft zur selben Zeit erzeugen Meldung 10 und die fixierte bleibt unverändert; 15 Verstöße werden als 12 Gründe plus „… und 3 weitere“ zusammengefasst.

### STP-071 · Reparatur ohne Verschieben · P1 · Status: Ist
1. Stunden ohne Kurs werden entfernt.
2. Raumwahl zur selben Zeit; Kandidaten: fester Raum des Kursteils → bisheriger Raum (wenn passend und frei) → Klassenraum der (einzigen) Klasse, nur ohne besonderen Raumtyp → übrige Räume des Typs (Klassen-/Kursraum, wenn kein Typ nötig), gleicher Standort zuerst, Heimatraum einer anderen Klasse zuletzt.
3. Frei = Raum zu dieser Zeit (alle Wochen der Stunde) weder belegt noch von einem Kursteil dieser Stunde genutzt.
4. Ist keine Lösung möglich, bleibt die Stunde im Problemsatz; Raumänderungen dieser Stunde werden verworfen.
- Was übrig bleibt, sind die „freien Kurse“ für den Generator: nur deren Stunden werden neu gelegt, alle anderen bleiben samt Räumen fixiert. Mit Planzeiträumen bleibt die Liste freier Kurse leer.
Abnahme: Eine Stunde im gesperrten Chemieraum erhält zur selben Zeit einen freien Chemieraum; gibt es keinen, bleibt sie unverändert und erscheint als Problem; verwaiste Stunden werden entfernt.

### STP-072 · Vorschlagspakete und Varianten · P0 · Status: Ist
| Variante (Schlüssel) | Umfang | Rechenzeit-Faktor | Startwert |
|---|---|---|---|
| minimal | nur Kurse mit Problemen werden neu gelegt, alles andere bleibt (Räume inklusive) | 1,0 | 1 |
| lokal | zusätzlich alle Kurse der beteiligten Klassen und Lehrkräfte | 1,5 | 2 |
| gruendlich | größerer Teilbereich (zweite Erweiterung); nur wenn höchstens doppelt so groß wie „lokal“ bzw. +25 Kurse, sonst gleicher Umfang wie „lokal“ | 3,0 | 3 |
| vertretung | Plan bleibt, betroffene Stunden werden vertreten; nur wenn alle Probleme fehlende Lehrkräfte sind (Sperrzeit oder Standort) und keine verwaisten, fehlenden oder überzähligen Stunden vorliegen | – | – |
| raeume | nur Raumwechsel und Entfernen verwaister Stunden; keine Berechnung, sofort fertig | – | – |

- Kennzahlen je Variante vorher/nachher (kleiner = besser): Probleme, Konflikte, unverplante Stunden, Hohlstunden Klassen, Springstunden Lehrkräfte, Standortwechsel, späte Hauptfächer, später Beginn, Verteilung der Fächer, Doppelstunden, Lehrkraft-Wünsche. Die Kennzahlen „Ø je Woche“ sind Summen über alle Klassen und Lehrkräfte; kleine Änderungen an gekoppelten Kursen (Oberstufen-Schienen) bewegen sie stark, deshalb stehen vorher und nachher nebeneinander.
- Inhalt je Variante: Änderungsliste je Kurs (von → nach, mit Raumwechsel; Kurse mit Klartext-Namen), Zahl verschobener Stunden, betroffene Klassen und Lehrkräfte, verbleibende Probleme, Hinweis „gilt ab“ (kleinstes Datum der beteiligten Sperrzeiten), Vertretungsabdeckung, Stundenplan-Entwurf für Klasse, Lehrkraft oder Raum (Entwurf gegen aktuell, nichts wird gespeichert; `GET /planning/proposals/{id}/variants/{vid}/timetable/{kind}/{ref}`). Obergrenze der Änderungen je Vorschlag 200 [unklar: Verhalten bei Überschreitung].
Abnahme: Bei zwei gesperrten Lehrkräfte-Stunden entstehen Pakete mit den Varianten minimal, lokal, gruendlich und vertretung; bei einem Raumproblem nur raeume; jede Variante zeigt elf Kennzahlen vorher/nachher; Hohl- und Springstunden sind getrennt ausgewiesen.

### STP-073 · Berechnung der Varianten und Auswahl · P1 · Status: Ist
- Rechenzeit: Basis 15 s je Variante (`SM_AUTOPLAN_TIME_LIMIT`, Standard 15,0) mit Faktoren 1, 1,5 und 3, also ein Paket in rund 15 + 22 + 45 Sekunden (im Betrieb 1 bis 2 Minuten); die Berechnungen laufen nacheinander. Startet jemand den Generator von Hand, wartet die Berechnung bis etwa 3 Minuten.
- Varianten ohne Verbesserung (nicht weniger Probleme oder mehr Konflikte) und doppelte Ergebnisse werden verworfen. Bleibt keine übrig, ist das Paket „fehlgeschlagen“ mit Status „Keine bessere Lösung“ („Keine bessere Lösung gefunden – bitte von Hand nachbessern“).
- Wiederholung: nach Annahme oder veraltetem Paket neue Prüfung nach 1 s; nach Versionswechsel während der Berechnung nach 0,5 s. Die Oberfläche nennt sachliche Hinweise („wenigste Änderungen“, „beste Qualität“) und spricht keine Empfehlung aus (Entscheidung offen, STP-082); Beobachtung des Bestands: Variante „minimal“ verschlechterte die Leerstunden von 20 auf 88.
Abnahme: Ein Paket, dessen Varianten alle mehr Konflikte erzeugen, wird „fehlgeschlagen“ mit dem Text „Keine bessere Lösung gefunden …“; zwei identische Ergebnisse erscheinen nur einmal.

### STP-074 · Entscheidung: Annehmen, Verwerfen, Später, Zurückholen · P0 · Status: Ist
- „Diesen Plan nehmen“ (mit Bestätigung im App-Dialog, optionale Notiz höchstens 500 Zeichen): nur wenn sich der Planstand nicht verändert hat, sonst Status „veraltet“ und Neuberechnung; bei veraltetem oder bereits entschiedenem Paket Antwort 409.
- „Verwerfen“ (mit Grund): die Problemlage wird erst nach der nächsten Änderung wieder vorgeschlagen.
- „Später“: das Paket wird 24 Stunden (wählbar 1 bis 336) aus Zähler und Kachel ausgeblendet, bleibt offen; „Zurückholen“ macht es sofort wieder sichtbar.
- „Vertretung statt Planänderung“: der Plan bleibt unverändert, die Entscheidung wird im Paket festgehalten; dieselbe Problemlage wird danach nicht mehr vorgeschlagen (Prüfstatus „abgedeckt“), bis sie sich ändert. Für Übergangszeiten (kein „gilt ab“ im Plan) ist das der vorgesehene Weg.
- Rechte: `timetable.generate` | `timetable.edit` | `settings.edit` (Annehmen, Verwerfen, Später, Zurückholen). Entscheiden ist auditiert (`plan.proposal_accept`, `plan.proposal_discard`).
Abnahme: Annehmen bei geändertem Plan → 409 und Status „veraltet“; Verwerfen ohne Grund → 422; „Später“ mit 400 Stunden → 422; ein ausgeblendetes Paket erscheint nach „Zurückholen“ sofort im Zähler; ohne eines der drei Rechte 403.

### STP-075 · Übernahme eines Vorschlags · P0 · Status: Ist
- Vor dem Schreiben wird der Planfingerabdruck erneut innerhalb der Transaktion geprüft; die Annahme bricht ab, wenn die Übernahme neue Konflikte oder mehr Probleme als berechnet erzeugen würde. Übernommen werden ausschließlich die im Änderungsplan enthaltenen Stunden (ersetzt oder entfernt). Tagesentscheidungen (Vertretungen, Überschreibungen) zu verlegten Stunden werden gelöscht. Andere Varianten desselben Pakets verlieren ihren Änderungsplan; nach der Annahme werden alle anderen offenen Pakete „ersetzt“ und die Prüfung läuft erneut (Rest-Probleme ergeben ein neues Paket).
- Planfingerabdruck: Hash über die Stunden (Kennung, Kurs, Lage, Wochen, Räume, Fixierung) und die Problemlage. Er ändert sich bei jeder Planänderung und bei Änderungen, die Probleme verschieben (Sperrzeit, Raum, Kurs); er ändert sich nicht bei Krankmeldungen, Raumsperren, Vertretungsentscheidungen oder Texten.
- Die Übernahme ist eine normale Planversion mit Meldung „Plan-Vorschlag angenommen: …“ (Aktion `plan.proposal_accept`), über „Verlauf & Audit“ rückgängig zu machen.
Abnahme: Zwischen Anzeige und Annahme verschiebt jemand eine Stunde → Annahme abgelehnt (409); eine Variante, die einen neuen Konflikt erzeugte, wird nicht übernommen; nach Annahme verschwinden andere offene Pakete aus der Liste.

### STP-076 · Automatische Übernahme „Räume“ · P2 · Status: Ist
- Einstellung `plan_auto_apply`: „aus“ (Standard) = nichts ohne Zustimmung; „raeume“ = reine Raumänderungen und das Entfernen verwaister Stunden werden sofort übernommen, als Planversion mit Vermerk und rückgängig machbar. Alles andere bleibt Entscheidung. Meldung: „<n> Problem(e) automatisch behoben“, ergänzt um „, <m> offen“. Ein Ergebnis wird nur übernommen, wenn die Zahl der Verstöße sinkt und die Zahl der Konflikte nicht steigt, sonst Status „unsolved“ („Keine bessere Lösung gefunden – bitte von Hand nachbessern“); hat sich der Plan inzwischen geändert (Versionsprüfung), folgt eine neue Prüfung nach 0,5 s. Recht zum Einstellen: `settings.edit`.
- Betreiberhaltung: Nichts wird automatisch angewendet, außer die Schule erlaubt es für klar definierte Kleinigkeiten (z. B. Raumwechsel). Der Schalter ist ein Vorschlag des Entwicklers, vom Betreiber nicht verlangt.
Abnahme: Mit „raeume“ wird ein Raumwechsel ohne Rückfrage übernommen und erscheint als Version im Verlauf; ein Eingriff in die Lage einer Stunde bleibt Vorschlag; mit „aus“ wird nie automatisch geschrieben.

### STP-077 · Zustände und Lebenszyklus · P1 · Status: Ist
| Objekt | Zustände |
|---|---|
| Paket | berechnung → offen → angenommen · verworfen · ersetzt · erledigt · veraltet; berechnung → fehlgeschlagen |
| Variante | berechnung · bereit · keine_loesung · fehlgeschlagen · entfernt |
| Prüfstatus (Dauerprüfung) | off (Schule aus) · ok · waiting (Änderung rückgängig oder Generator läuft) · covered (per Vertretung abgedeckt) · proposal · running · unsolved · applied · partial · error |
| Protokollereignisse | erzeugt, bereit, später, zurückgeholt, angenommen, verworfen, ersetzt, erledigt, veraltet, informiert, keine_loesung |

- Ein neues Paket ersetzt alle offenen Pakete mit anderem Planstand; laufende Berechnungen werden abgebrochen. Ein Paket mit Status „abgedeckt“ blockiert neue Vorschläge für dieselbe Signatur, bis sich die Problemlage ändert. Beim Systemstart werden halb berechnete Pakete (Berechnung) auf „fehlgeschlagen“ gesetzt; die nächste Prüfung legt sie bei Bedarf neu an. Statustexte erscheinen in Deutsch.
Abnahme: Neustart während einer Berechnung → das Paket steht danach auf „fehlgeschlagen“ und die Prüfung erzeugt bei Bedarf ein neues; ein abgedecktes Paket verhindert ein zweites Paket derselben Signatur.

### STP-078 · Benachrichtigung der Betroffenen · P1 · Status: Ist
- Nach der Annahme erhalten betroffene Lehrkräfte eine E-Mail (nur wenn der Versand eingerichtet und eine Adresse hinterlegt ist) und einen Live-Hinweis an ihr Konto (Ereignis „Plan-Vorschlag angenommen“); die Namen der Informierten stehen im Paket. Lehrkräfte werden informiert, nicht vorher beteiligt; ein Einspruchsverfahren ist nicht vorgesehen.
- Für neue Pakete gibt es Live-Hinweis, Zähler und Startseiten-Kachel; keine Postfach-Nachricht und keine E-Mail an Berechtigte (STP-082).
Abnahme: Nach Annahme enthält das Paket die Liste der informierten Lehrkräfte; Lehrkräfte ohne hinterlegte Adresse erhalten nur den Live-Hinweis; ein Paketzähler erscheint bei Berechtigten sofort nach Erzeugung.

### STP-079 · Oberfläche: Plan prüfen und Planvorschläge · P1 · Status: Ist
- Reiter „Plan prüfen“ in der Planung (`/planung/pruefung`, erster Reiter): Status „Plan in Ordnung“ oder „N Probleme“, Knopf „Jetzt prüfen“, offene Vorschläge mit Variantenvergleich, zuletzt Entschiedenes, Einstellungen (`auto_replan`, `plan_auto_apply`, `substitution_confirm`).
- Menüpunkt „Planvorschläge“ (`/planung/vorschlaege`) mit Zähler offener Pakete (beim App-Start geladen, bewusst klein), Startseiten-Kachel nur bei offenen oder laufenden Paketen, Live-Hinweis bei neuem Paket. Paketkarten mit Variantenkarten (Kennzahlen vorher/nachher mit Ton gut/schlecht, nie nur Farbe; Wirkungstext; Änderungsliste; Aktionen annehmen, verwerfen, zurückstellen); zurückgestellte Pakete getrennt; Liste „Zuletzt“ für erledigte Pakete.
- Vorschau je Variante (`/planung/vorschlaege/:paket/:variante`): Kennzahlen-Tabelle, Änderungsliste, Stundenplan-Entwurf im gemeinsamen Raster gegen den aktuellen Plan (Klasse, Lehrkraft, Raum).
- Reihenfolge der Reiter: „Plan prüfen“ vor dem Qualitätsbericht. Der Betreiber wünschte den Qualitätsbericht als ersten Reiter („der Qualitätsbericht soll auf jeden Fall als ersten Tab in die Planungsliste reinkommen“); Entscheidung (Bericht zweiter oder Zusammenlegung) steht aus [offen].
- Alle Erklärungen hinter dem Hilfe-Symbol; Anrede „Sie“.
Abnahme: Ein offenes Paket zeigt im Menü den Zähler „1“, auf der Startseite die Kachel und beim Eintreffen den Hinweis; die Variantenkarte zeigt „Hohlstunden Klassen 20 → 18“ mit Ton „gut“ und Text; die Entwurfsansicht zeigt geänderte Stunden im Raster markiert.

### STP-080 · Rechte für Plan prüfen · P0 · Status: offen
- Seiten, Menüpunkt, Zähler, Liste, Zusammenfassung, Detail, Variantenansicht, Annehmen, Verwerfen, Zurückstellen und Zurückholen: nur mit `timetable.generate`, `timetable.edit` oder `settings.edit`. Der Bestand weist die Lese- und Entscheidungs-Schnittstellen nur als „angemeldet“ aus (Widerspruch zur Projektdokumentation, Risiko für Lesen und Annahme); Neubau: serverseitige Prüfung auf allen Pfaden, Schüler/innen und Eltern 403.
- Vertretungsvorschläge sehen und freigeben: `substitution.edit` (Freigabe-Recht wird nicht gesondert benannt; Neubau: ausdrücklich `substitution.edit`).
Abnahme: GET der Paketliste als Lehrkraft ohne eines der drei Rechte → 403; Annehmen als Sekretariat (ohne die Rechte) → 403; Administration, Planer: 200.

### STP-081 · Daten, Verschlüsselung und Aufbewahrung von Paketen und Plan-Ständen · P0 · Status: offen
- Tabellen: `plan_proposals` (Status, Planversion, Planfingerabdruck als Hash, Signatur, Titel ≤ 300 Zeichen, Gründe, Auslöser, Zahl der Probleme, Gilt-ab, Zurückstellung bis/durch, Entscheidung mit Zeitpunkt/Person/Notiz ≤ 500, gewählte Variante, angewendete Planversion, informierte Personen); `plan_proposal_variants` (Paket mit Kaskade, Schlüssel, Position, Titel ≤ 200, Beschreibung, Status, Kennzahlen vorher/nachher, Änderungsliste, betroffene Klassen/Lehrkräfte, Zahl verschobener Stunden, verbleibende Probleme, Gilt-ab, Änderungsdiff, Rechendauer; der Diff wird bei Abschluss gelöscht, außer bei der gewählten Variante); `plan_proposal_log` (nur anhängen; Paket ohne Fremdschlüssel, Verlauf bleibt erhalten; Zeitpunkt, Aktion ≤ 30, Person, Variante, Notiz ≤ 500, Einzelheiten); `plan_snapshots` (Name ≤ 120, Notiz ≤ 500, Zeitpunkt, Person, Quelle, Planversion, Zahl der Stunden, Zeitraum, Stunden, Kennzahlen).
- Neubau-Vorgaben: Klartext-Personenbezüge (Name der entscheidenden Person, Akteursname, Name der speichernden Person) und Freitexte (Entscheidungsnotiz, Plan-Stand-Notiz) sowie die Stundendaten der Plan-Stände und der Änderungsdiffs werden verschlüsselt gespeichert (Bestand: Stände nur komprimiert, Namen im Klartext). Planvorschläge, Protokoll und Plan-Stände werden als Datenarten in das Löschkonzept aufgenommen (Bestand: nicht als Datenart geführt). Aufbewahrungsfristen [unklar]; Vorschlag zur Entscheidung durch den Betreiber.
Abnahme: In der Datenbank steht kein Klartext von Namen oder Notizen dieser Tabellen; ein Plan-Stand lässt sich nach Schlüsselrotation lesen; das Löschkonzept führt „Planvorschläge“ und „Plan-Stände“ mit Frist (Prüfung nach Festlegung der Frist).

### STP-082 · Offene Punkte zu Plan prüfen · P2 · Status: offen
- Empfehlung: Ob die Oberfläche eine Variante empfiehlt, ist ungeklärt (bisher bewusst keine Empfehlung). 
- Benachrichtigung der Berechtigten per Postfach oder E-Mail bei neuem Paket fehlt (das Briefsystem hat keinen Systemabsender); bisher nur Zähler, Kachel, Live-Hinweis.
- Gültigkeit „ab Datum“ nur als Hinweis (STP-068).
- Beteiligung der Lehrkräfte vor der Annahme und ein Einspruchsverfahren sind nicht vorgesehen; der Betreiber hat nichts anderes gewünscht.
- Pendelverstöße erscheinen nicht auf der Seite des Qualitätsberichts (STP-051).
Abnahme: Entscheidung des Betreibers zu den genannten Punkten liegt vor und ist in dieser Datei nachgetragen; bis dahin bleibt der Ist-Zustand.

---
### 1.9 Stundenplan-Ansichten

### STP-083 · Ansichten und Zugriff · P0 · Status: Ist
- Ansichten: Klasse, Lehrkraft, Raum, Schüler/in (`GET /api/v1/timetable/{kind}/{ref}`); `GET /timetable/allowed` liefert die Bezüge, die die angemeldete Person sehen darf. Die Liste der Stunden (`/timetable/lessons`) braucht zusätzlich `timetable.edit` oder `plans.read_all`.
- Zugriff: Schüler/innen und Eltern sehen nur den eigenen Bezug (Eltern: ihre Kinder; Eltern volljähriger Kinder nur mit Freigabe für den Bereich „Stundenplan“; Befund des Bestands: Eltern volljähriger Kinder sahen den Plan weiter). Lehrkräfte sehen den eigenen Plan und den Plan ihrer geführten Klasse (`plans.read_all` im Umfang eigene Klassen/eigener Zweig); Raumpläne `rooms.read`; fremde Lehrkraft- und Schülerpläne nur mit `timetable.edit`, `plans.read_all` bzw. `students.read` (Planung, Verwaltung, Schulleitung). Kinder sehen ihren Stundenplan immer (Regressionstest). Fremde oder unbekannte Bezugs-Kennung → 404; fehlendes Recht → 403 mit Hinweis auf das fehlende Recht.
- Der Vertretungsplan ist nicht Teil der Kinder-Ansicht (VER-030); Entfall, Vertretung und Raumänderung erscheinen im eigenen Stundenplan.
Abnahme: Schülerkonto ruft den Plan einer fremden Klasse ab → 404; Lehrkraft ohne `plans.read_all` ruft einen fremden Lehrkraftplan ab → 403 mit Hinweis; Elternkonto eines volljährigen Kindes ohne Freigabe sieht den Stundenplan des Kindes nicht; Kind sieht seinen Plan nach Einführung neuer Sichtregeln weiterhin.

### STP-084 · Darstellung der Zellen und Statusmarker · P1 · Status: Ist
- Zellen zeigen Fach-Kürzel, Lehrkraft, Raum, Klasse, Kursteile (Mehrteil-Kurse mit Sprechblase, STP-026). Doppelstunden erscheinen als ein zusammengeführtes Feld über zwei Zeilen; die Stundenzahl bleibt erkennbar.
- Statusmarker: geändert, entfällt, Klassenarbeit, abwesend, gesperrt, Konflikt, OK, Ursprung (Verlegung), ausgewählt. Vertretung und Entfall als farbiger Rahmen in der Farbe der Eintragsart, Markierungen gedämpft mit gutem Kontrast; Status nie nur über Farbe (Text oder Zeichen dazu). Gesperrte/gefehlte Felder sind schraffiert; Schraffur bedeutet nie etwas anderes.
- Pausen als dicke Linie (auch nachmittags) mit „Pause 1/2/3“; Trennlinie vor dem Wochenende; Wochentage groß (Kurz- und Langname, Datum).
- Details zur Zelle: breite Bildschirme Seitenleiste/Einblendung; Zellen haben einen Text für Bildschirmleser (Fach, Lehrkraft, Raum, Zeit, Status).
Abnahme: Eine vertretene Stunde hat Rahmen in der Farbe „Vertretung“ und den Text „Vertretung“; ein Bildschirmleser liest „Mathematik, Frau X, Raum 204, 3. Stunde, Vertretung“; ein gekoppelter Kurs ist nicht schraffiert.

### STP-085 · Markierungen in der Stundenbox (Abzeichen) · P1 · Status: Ist
- Unten rechts in der Stundenbox gestapelt in fester Reihenfolge: Hausaufgabe (HA; Link zur Aufgabe im Kursraum, Lehrkräfte sehen die Zahl der Abgaben) → Test/Klausur (klickbar zum Klausur-Detail bzw. Kursraum) → krank/fehlt/beurlaubt (rotes Zeichen, klickbar zu den Krankmeldungen, bei Eltern mit vorausgewähltem Kind) → Nachschreiben. Mehrere gleicher Art als „HA 2 ▾“, „Test 2“, „Klausur 2“ mit kleiner Liste (Link und Status je Aufgabe; erledigte Abgaben grün durchgestrichen). Die Listenansicht am Handy zeigt dieselben Markierungen.
- Links erscheinen nur, wenn die betrachtende Person den Kursraum öffnen darf (Befund: Schüler, Sekretariat und andere Lehrkräfte sahen Links ohne Zugriff).
- Lehrkräfte sehen in der Klausurstunde „NTA n“ (Nachteilsausgleich, ohne Diagnose) und „fehlt n“; Familien sehen „Nachschreiben“ mit Datum und Attest-Hinweis.
- Betreiberzitat: „wenn der Lehrer zwei mal Hausaufgaben aufgegeben hat, dass dann einfach zweimal das Hausaufgabenzeichen übereinander steht“; „unten rechts in der Ecke sollen immer priorisiert die Hausaufgaben stehen“; „Das soll dann nicht oben unter dem Wochentag stehen.“ Hausaufgaben, Tests, Klausuren, Krankmeldungen und Nachschreiben folgen einem einheitlichen System. Noch zu prüfen: Überdeckung des Fachtextes bei drei Markierungen [offen].
Abnahme: Zwei Hausaufgaben im selben Feld erscheinen als „HA 2 ▾“ mit zwei Links; ein Schüler ohne Zugriff auf den Kursraum sieht kein HA-Zeichen mit Link; Klick auf das rote Zeichen öffnet die Krankmeldungen mit dem richtigen Kind; die Reihenfolge ist HA, Test/Klausur, krank, Nachschreiben.

### STP-086 · Klausur, Test und Nachschreibtermin in der echten Stunde · P1 · Status: Ist
- Klausuren, Tests und Nachschreibtermine stehen in der konkreten Stunde, nicht im Tageskopf, als eigener Block mit Raum („Klausur M · statt Deutsch“), der die reguläre Stunde ersetzt; parallele Wahlkurse bleiben sichtbar. Gilt in Schüler-, Eltern-, Klassen-, Lehrkraft- und Raumansicht. Die Zuordnung erfolgt über den echten Kurs, nicht über das Fach-Kürzel (Befund: „Klausur M15“ stand am Donnerstag ohne Mathe-Stunde). Hat der Kurs an dem Tag keine Stunde, erscheint ein eigener Block. Klick führt in den Kursraum des Kurses bzw. der Kursgruppe („zu den entsprechenden Klassenräumen … für die der Test ist“).
- Der Tageskopf zeigt keine Text-Chips für Klausur, Test oder Hausaufgabe; nichts doppelt im Kopf und in der Stunde.
Abnahme: Klausur M am Donnerstag in der 3. Stunde erscheint dort als Block „Klausur M · statt …“ in allen fünf Ansichten und nicht im Tageskopf; Klick öffnet den Kursraum; ein Wahlkurs parallel bleibt sichtbar.

### STP-087 · Hausaufgaben im Plan · P2 · Status: Ist
- Hausaufgaben hängen am Kurs, nicht am Fach-Kürzel. Fällig an einem Tag mit Kursstunde: erste Stunde dieses Tages. Sonst: letzte Stunde des Kurses vor dem Fälligkeitstag mit Hinweis „fällig Fr 16.10.“. Hausaufgaben aus Klassenräumen ohne Fach liegen in der ersten Stunde des Tages, bevorzugt bei der Klassenlehrkraft. Grenze: Eine Montags-Aufgabe erscheint dann nur in der Vorwoche.
- Mehrere Hausaufgaben derselben Stunde: „HA 2 ▾“ (STP-085). Betreiber: „Mittwochs steht so ein HA-Logo und sonst steht das nur am Dienstag … das muss auf jeden Fall noch geändert werden.“
Abnahme: Aufgabe für Mathe fällig Freitag, Kursstunden Mo/Mi → Markierung in der Mittwochs-Stunde mit „fällig Fr 16.10.“; fällig am Mittwoch → erste Stunde des Mittwochs.

### STP-088 · Verpasste Stunden im Plan · P1 · Status: Ist
- Verpasste Stunden (krank, beurlaubt, gefehlt) erscheinen rot schraffiert wie Feiertage mit kleiner Beschriftung; eine Krankmeldung ohne Stunden deckt den ganzen Tag. Die Schraffur wird einmal über das ganze Raster gezeichnet (durchgehende Streifen, in jeder Darstellungsgröße; blockierte Felder durchsichtig); Ferien im Klassenbuch gleich. Sichtbar für Schüler/innen, Eltern und berechtigtes Personal.
- Betreiber: „rot gestrichelt, wie die Feiertage über den Stunden“, damit klar ist „ab wann oder wo man fehlt“; „das sind keine durchgehende Linien … dass das so durchgehende sein können und dass es auch modular funktioniert mit jeder Größe von Darstellung.“
Abnahme: Krankmeldung für Mo–Mi ohne Stunden schraffiert alle Stunden dieser Tage in einem durchgehenden Muster; die Schraffur eines Kindes erscheint nicht bei anderen Kindern.

### STP-089 · Wochenansicht, Navigation, Druck · P1 · Status: Ist
- Wochennavigation (vor, zurück, Heute) und Datum-Navigation; Tageskopf mit Datum, Feiertags- und Ferienkennzeichen, heutiger Tag hervorgehoben. Zwei Darstellungen: Raster (Tage × Stunden) und Liste; die Wahl wird pro Gerät gespeichert, nicht pro Konto. Die angezeigte Woche leitet sich aus dem angezeigten Schultag ab. „Heute“ funktioniert auch am Wochenende (Befund: aktiv und wirkungslos). Plan-Kennungen mit Sonderzeichen (z. B. „%“) funktionieren; Links werden korrekt kodiert.
- Nicht gedruckt wird der Stundenplan (Betreiber: „Das mit dem Stundenplan drucken macht gar keinen Sinn, das kannst du weglassen.“). Es bleiben Vertretungs-Aushang, Zugangsbriefe und schriftliche Entschuldigung.
Abnahme: Am Sonntag springt „Heute“ auf die laufende Woche; eine Klasse mit Kennung „5%a“ lässt sich öffnen; es gibt keinen Knopf und keine Seite „Stundenplan drucken“.

### STP-090 · Handy und Tablet: Listenansicht, Tagesansicht · P1 · Status: offen
- Unter 700 px Breite wird das Raster automatisch zur Liste (Tage untereinander) (Bestand: schaltet nicht automatisch um); ab 700 px waagerechter Scroll im Rahmen, Zeitspalte bleibt stehen. Auf 390 px eine Tagesansicht mit Wischen zwischen den Tagen; am Tablet die Woche; leere Sa/So-Spalten am Tablet ausblendbar. Filter hinter „Filter“-Knopf mit Chips für aktive Filter; seltene Schalter („Regelplan bearbeiten“, Raster/Liste) im „Mehr“-Menü (Vorschlag, wartet auf Freigabe).
- 390 px ohne waagerechten Seitenbildlauf; Trefferflächen mindestens 44 px.
Abnahme: Bei 390 px zeigt der Stundenplan die Listen-/Tagesansicht ohne Seitenbildlauf; bei 800 px die Woche; die Liste zeigt dieselben Markierungen wie das Raster.

### STP-091 · Namen zu Kürzeln (Sprechblasen) · P2 · Status: Ist
- Kürzel für Lehrkraft, Fach, Raum, Klasse und Standort zeigen beim Verweilen (Maus), Antippen, langen Drücken und per Tastatur eine Sprechblase mit dem ausgeschriebenen Namen — überall, wo Kürzel stehen (Stundenplan, Vertretung, Stammdaten, Aufsichten, Startseite, Planung, Klassen, Postfach-Auswahl, Lehrkraft-Profil, Benutzerverwaltung, Klausuren). Nicht auf dem Monitor (er scrollt selbst), in Auswahllisten und im Druck. [unklar: Dauer des langen Drückens.]
- Betreiber (11.10.): Anzeige mit „vollem Lehrernamen und Raum“ statt Kürzel und Raumcode; „Information war nicht hilfreich“.
Abnahme: Antippen von „MUE“ am Handy zeigt „Frau Müller“ (Beispiel); die Sprechblase ist per Tastatur (Fokus) erreichbar; auf dem Monitor erscheint keine Sprechblase.

### STP-092 · Stunden-Details, Hausaufgaben eintragen, Hinweise im Plan · P1 · Status: offen
- Wunsch A-54/A-55 (Backlog B-30/B-32): Antippen oder Klicken auf eine Stunde öffnet Details (PC: Einblendung, Handy: Blatt von unten) mit vollem Namen der Lehrkraft (bzw. Vertretung), vollem Fachnamen, Raum mit Standort, Status (findet statt, Vertretung, Raumänderung, entfällt, verlegt) und Hausaufgabe — im Datenumfang der Rolle und auch ohne Planrecht. Betreiber: Popup mit Tag, Stunde, Fach, vollem Lehrernamen und Raum; „Klassenname und Klassenraum müssen nicht angezeigt werden“.
- Lehrkräfte tragen Hausaufgaben (Fälligkeit, optional Thema) in eigenen Stunden, auch Vertretungen, am PC und am Handy ein; Schüler/innen und Eltern sehen sie nach Fälligkeit („bis morgen“, „diese Woche“); Schüler/innen haken „erledigt“ ab; Aufgaben aus Kursräumen erscheinen in derselben Liste mit Verweis. `GET /me/week?date=` liefert für Schüler/innen und Eltern (je Kind) die konkrete Kalenderwoche mit Vertretungen, Entfall und Raumänderungen.
- Kalender-Hinweis (Betreiber 11.10.): beim Durchgehen unten rechts in Rot „zu spät“ bzw. für den Tag „krank gemeldet“; bei unter 18-Jährigen Hinweis, dass die Krankmeldung noch nicht vorliegt und nachgeholt werden muss [Umsetzung nicht bestätigt].
Abnahme: Antippen einer vertretenen Stunde zeigt „Vertretung durch Herrn Y“, Raum mit Standort und die Hausaufgabe; eine Lehrkraft trägt in einer Vertretungsstunde eine Hausaufgabe bis Freitag ein, die Familie sieht sie als „bis Freitag“; ein Elternkonto sieht sie nur für das eigene Kind.

### STP-093 · Stunden verschieben und fixieren · P1 · Status: Ist
- Eine Stunde auf einen anderen Platz ziehen (Drag and Drop). Mögliche Plätze liefert `GET /timetable/lessons/{id}/options`; vor dem Ablegen prüft das System das Ziel, Zielfelder werden als „OK“ (grün) oder „Konflikt“ (rot) markiert; `POST …/move` mit Zielplatz; `POST …/lock` fixiert die Stunde. Fixierte Stunden bleiben bei Generator und Plan prüfen erhalten und gewinnen bei Doppelbelegung.
- Die Zielprüfung nutzt dieselben harten Regeln wie der Generator (STP-032), insbesondere „Doppelstunde nie über eine Pause“ und die verfügbaren Tage (Befund: manuelles Verschieben beachtete Pausen nicht und nutzte eine andere Tage-Formel). Verschieben über Planzeiträume hinweg findet nicht statt. Bei Konflikt Rückfrage mit Liste der betroffenen Änderungen (409), Überschreiben nur mit Bestätigung. [unklar: vollständige Liste der Prüfungen des Bestands.]
- Recht `timetable.edit`; Version rückgängig machbar. Verschieben und Fixieren sind auch ohne Maus (Tastatur) möglich (STP-095, offen).
Abnahme: Eine Doppelstunde auf eine Position über der Pause gezogen wird als Konflikt markiert und nicht gespeichert; eine fixierte Stunde bleibt nach einem Generatorlauf an ihrem Platz; ohne `timetable.edit` 403.

### STP-094 · Das eine Tage-×-Stunden-Raster · P0 · Status: Ist
- Jede Ansicht „Tage × Stunden“ (oder Tage × Pausen/Bereiche) nutzt dasselbe Raster; der Stundenplan ist nur eine Variante. Es wird nie ein zweites Raster gebaut, nur der Zellinhalt wird angepasst (Ausnahmen nur mit ausdrücklicher Begründung); ein automatischer Test schlägt fehl, wenn ein eigenes Raster entsteht. Verwendung: Stundenplan (Klasse, Lehrkraft, Raum), Klassenbuch (Anwesenheit je Stunde), Verfügbarkeit/Sperrzeiten der Lehrkräfte (Editor), Pausenaufsichten, Klassen-Wochenplan, Kennzahlen-Heatmaps der Planung, Vorschau im Regel-Editor, Kursraum-Regelplan, Fehlzeiten je Stunde. Betreiber (12.10.): das Arbeitszeiten-Raster „dieses Sheet“ ist wiederzuverwenden.
- Spalten (Tage): Name, Kürzel, Datum; Markierungen für Ferien, frei, heute, Trennlinie, Spuren für parallele Lehrkräfte/Räume; Kopf anklickbar („ganzen Tag markieren“). Zeilen: Stunde, Uhrzeit, Pausenlinie, Gruppenüberschrift; Kopf anklickbar. Zelle: Inhalt, Titel, „blockiert“ (durchgehend schraffiert), Tonalität (frei, gut, mittel, schlecht, gedämpft, Konflikt, Wunsch), Heatmap-Wert 0 bis 1 (Anteil), Auswahlrahmen; die ganze Zelle ist ein Knopf mit Bezeichnung. Editoren (Antippen/Ziehen) mit eigenem Bearbeitungsmodus. Blöcke über mehrere Stunden oder Spuren als Überlagerung.
- Farben nur aus den Zustandsklassen, hell und dunkel über Tokens; Zeilenhöhe normal/kompakt, Zellabstand und -rundung als Tokens; Legende (Farbfeldern wie im Raster) unter dem Raster. Wochen: die angezeigte Woche ist Grundlage für Raster, Liste und Dialoge; Anzeige-Indizes werden nie mit Rohdaten vermischt. Spalten/Zeilen ohne Unterricht schmal und abgeblendet, Umschalter „Nur Unterrichtstage“.
- Handy: unter 700 px Liste statt Raster; ab 700 px waagerechter Scroll mit stehender Zeitspalte. [unklar: Tabellen werden unter 600 px zur Kartenliste, das Raster erst unter 700 px zur Liste; vereinheitlichen oder bestätigen.]
Abnahme: Ein Test findet im Quelltext der Oberfläche genau eine Raster-Komponente für alle genannten Ansichten; die Aufsichts-Wochenansicht und der Verfügbarkeitseditor zeigen dieselben Tageskopf-Markierungen wie der Stundenplan; ein Klick auf den Tageskopf im Editor markiert den ganzen Tag.

### STP-095 · Tastatur, Touch und Screenreader in den Planansichten · P1 · Status: offen
- Stundenplan-Raster per Tastatur (Pfeiltasten, Enter öffnet die Details) und Touch (Welle 3 der Fehlerbehebung noch offen); Listenansicht des Stundenplans bisher nur per Maus; Reiter mit ARIA-Bezügen; Auswahlzustand nicht an Tabellenzeilen; Menü mit Pfeiltasten; Verschieben per Tastatur [Lücke im Bestand]; Schraffur und Statusfarben mit Textäquivalent; Fokusrahmen 2 px sichtbar; Ziel WCAG 2.1 AA.
Abnahme: Mit Tastatur lässt sich im Raster eine Zelle erreichen, öffnen und eine Stunde zu einem Zielplatz verschieben; axe-core meldet für den Stundenplan keine schweren Verstöße.

### 1.10 Schnittstellen, Referenzdaten, Leistung

### STP-096 · Import und Export des Plans · P1 · Status: offen
- Ist: Import Untis (GPU-Format als Zip, Probelauf mit Vorher-Nachher), Export Untis als Zip, Schulmanager-Online-Paket, CSV je Datenart mit Feldzuordnung, JSON-Vollsicherung mit Integritätsprüfung (Format und Tabellen: INT). Rechte: Import Untis `timetable.edit`; CSV `timetable.edit` | `masterdata.edit` je Datenart; JSON `timetable.edit`+`masterdata.edit`; Export CSV je Datenart `students.read` | `masterdata.edit` | `timetable.edit`. Neue Stunden aus dem Import setzen ihren Planzeitraum oder lassen ihn leer. Nach Massenimport ändern sich Stunden-Kennungen, Überschreibungen können verwaisen; der Dialog warnt.
- Neubau-Festlegung: Export JSON, Untis und Schulmanager-Online nicht mehr „nur angemeldet“, sondern mit Recht (`timetable.edit`+`masterdata.edit`); Upload-Größen und Zahl der Zip-Dateien begrenzt [unklar: Werte].
- Offen: Der Untis-Rundlauf verliert Sperrzeiten, Arbeitszeiten, Pausen und Termine; GPU-Dateien 013 (Abwesenheiten), 011 (Zeitraster), 017 (Prüfungen), 016 (Zeitwünsche) zuerst, danach 007–009, 012, 018–021.
Abnahme: Export und Reimport eines Plans (JSON) in eine leere Instanz liefert denselben Plan; Export Untis als Konto ohne `timetable.edit` → 403; Untis-Rundlauf erhält Sperrzeiten und Pausen.

### STP-097 · Kalender-Abo (iCal) · P1 · Status: offen
- Ist: Feed über eine URL mit geheimem Token, ohne Login; enthält Stunden, Termine, Ferien und Vertretungseinträge mit Art-Bezeichnung. Bestand: Eltern erhielten nur den Feed des ersten Kindes.
- Neubau: Feed je Kind; Token nur als Hash bzw. HMAC gespeichert, nie im Klartext; Token erneuern und widerrufen; keine Gründe, Gesundheits- oder Namensdaten Dritter im Feed (Feed enthält personenbezogene Plandaten); Zugriff protokolliert nicht inhaltlich. [unklar: Schutz gegen Weitergabe der URL, Aktualisierungsintervall.]
Abnahme: Ein Elternkonto mit zwei Kindern erhält zwei Feeds; nach „Token erneuern“ liefert die alte URL 404; der Feed enthält keine Krankheitsgründe.

### STP-098 · Test- und Demo-Pläne, Referenzdaten · P1 · Status: Ist
- Stundenpläne für Demo und Tests entstehen ausschließlich über Regeln und Generator, nicht durch Handplatzierung (Betreiber 12.10.: „Ich will, dass du die Stundenpläne nur mit dem Tool designs, was du gemacht hast, nicht selber nur das Tool bedienen.“). Gewünscht: ein wirklich komplexer Plan mit sehr vielen, durcheinandergehenden Klassen.
- Referenzschule (Demo): 99 Klassen, 169 Lehrkräfte, 2.644 Schüler/innen, 1.554 Stunden, rund 2.300 Stunden in der großen Demo; lädt fehlerfrei, rund 68 KB Dokumentgröße. Fiktive Montessori-Testschule (eigene leere Instanz, bestehende Konfigurationen unverändert): 12 Mischaltersgruppen (Grundstufe 1–3, Mittelstufe 4–6, Sekundarstufe 7–10 am Standort Bauernhof) plus 2 Abendgruppen, 250 Kinder, 42 Lehrkräfte, 39 Räume, 2 Standorte, 83 Kurse; Ergebnis 363 Blöcke ohne Konflikt (einschließlich „jede 2. Woche Mittwoch frei“, Projektphasen, Abendklassen, Teilzeit, gemeinsame Stunden, Freiarbeitsblöcke); Export und Reimport identisch.
- Szenario „Testtag“: ein Datensatz mit Hausaufgaben, Test, Klausur, Krankmeldungen und Nachteilsausgleich gleichzeitig zum Durchklicken [Abnahme durch den Betreiber steht aus].
Abnahme: Der Generator verplant mit 2 Minuten Rechenzeit auf der Referenzschule alle 1.554 Stunden ohne Konflikt; die Montessori-Testschule ergibt 363 Stunden ohne Konflikt und überlebt Export/Reimport unverändert.

### STP-099 · Leistung und Skalierung der Planung · P2 · Status: offen
- Zielgröße: 2.500 Schüler/innen, einige hundert Lehrkräfte, zwei Standorte. Planabrufe zwischen 7:30 und 8:00 Uhr (2.500 Schüler/innen, 300 Lehrkräfte, Krankmeldungen und Planabrufe): 95 % unter 500 ms; Speichern und Laden des Planungsdokuments ohne spürbare Verzögerung durch Verschlüsselung; eine Dauerprüfung eines sauberen Plans der Referenzschule dauert Millisekunden. Lasttest im Repository (Bestand: Generator bisher nur mit kleiner Demo getestet, Lasttest fehlt).
Abnahme: Lasttest mit 2.500 Schüler/innen und 300 Lehrkräften hält die 95-%-Marke unter 500 ms; das Ergebnis steht in der Betriebsdokumentation.

---
### 1.11 Gewünschte, noch nicht gebaute Planungsthemen

### STP-100 · Räume: Konzept, Leihe, Buchung · P2 · Status: offen
- Betreiberwunsch (11.10.): Räume mit Fach-/Typ-Zuordnung. Allgemeine Räume für Stunden ohne Spezialbedarf (Mathe, Deutsch, Sprachen); Fachräume mit Ausstattung (z. B. Fachinformatik, Schweißen, Lackieren, Malen). Die Schule legt Räume und Zuordnungen fest. Raumleihe: Eine Klasse kann aus einem Fachraum für einige Stunden verdrängt werden, damit eine Klasse mit Bedarf (z. B. Informatik) den Raum bekommt. Später auch Raumgruppen und teilbare Räume.
- Ist: Raumtypen und Raumwahl (STP-033); Auto-Tausch einer Stunde bei gesperrtem Fachraum; „Räume anpassen“ als Variante der Planvorschläge. Es fehlen Verdrängung/Raumleihe und eine Fach-Ausstattungszuordnung.
- Raum- und Gerätebuchung (Backlog B-54, „groß, später“): buchbare Räume und Geräte je Standort (PC-Raum, Aula, Tablet-Koffer); belegte Räume laut Plan sind nicht buchbar; „Freien Raum finden“ für Datum und Stunde; Raumwechsel durch Lehrkräfte selbst (wenn freigeschaltet), sichtbar im Vertretungsplan; Genehmigung bei Fachräumen; Auslastungsbericht; Übersicht für Hausmeister/IT; Entfall gibt den Raum frei; Konfliktwarnung mit Klausuren und Vertretungstausch.
Abnahme: Ein Fachraum „Informatik“ wird für drei Stunden einer anderen Klasse zugewiesen; die verdrängte Klasse erhält einen Ersatzraum gleichen Typs oder die Stunde wird getauscht, der Vorgang erscheint als Planvorschlag; „Freien Raum finden“ liefert für Di 3. Std. alle freien Räume mit Kapazität.

### STP-101 · Werkzeuge für Reform- und Sonderformen (Montessori u. a.) · P3 · Status: offen
- Betreiberwunsch (12.10.): „alles soll so modular, also so customizable sein wie möglich, dass so viele Schulen, Schularten, Schultypen … benutzen wollen.“ Aus dem Test mit der fiktiven Montessori-Schule (STP-098) ergeben sich 24 fehlende Werkzeuge; die zehn wichtigsten: Tagesrahmen und Zeitanker (z. B. „Freiarbeit immer vormittags“; Bestand: Freiarbeit/Morgenkreis landen am Nachmittag); Team-Teaching als gleichberechtigtes Feature („1 von 2“; Bestand: Freiarbeit mit zwei Lehrkräften nur mit eigenem Raum, sonst 1.224 Blöcke unplatziert); Raumgruppen und teilbare Räume; Generator-Diagnose „Warum nicht verplant?“ (STP-104); Lerngruppen unabhängig von Klassen mit Jahrgangsbereich (Bestand: Mischaltersgruppen nur als Notbehelf, eine Klasse hat nur einen Jahrgangswert); Blocklängen beliebig und mehrere Raster (Bestand: nur Einzel- und Doppelstunden); Kurswahl mit Konfliktprüfung je Kind; Epochen- und Projektplaner; Einmal-Login; Formularbaukasten (gebaut). Danach Lernzeitblöcke, Import-Assistent; Vorlagen je Schulart und Moodle-Import sind gebaut.
- Weitere Lücken: keine individuellen Wochenpläne je Kind, keine Lernfortschrittsdokumentation je Kind (KUR), kein Aufsteigen in Mischgruppen.
- Vorschlag des Entwicklers: zuerst Generator-Diagnose und Team-Teaching; die Frage „Top-Werkzeuge bauen?“ blieb unbeantwortet.
Abnahme: Eine Lerngruppe mit Jahrgangsbereich 1–3 wird ohne Workaround angelegt; ein Kurs mit zwei gleichberechtigten Lehrkräften belegt einen Raum; eine Regel „Freiarbeit nur vormittags“ wird vom Generator eingehalten.

### STP-102 · Oberstufe: Kurswahl, Bänder, Kursplanung · P3 · Status: offen
- Kurswahlen erfassen mit Wahlkonflikten je Kind (Prioritäten 1 bis 3, Überschneidungsanzeige), Bänder/Schienen bilden (Kurse bandweise parallel legen), Kurs-Optimierung (Total- und Teilbereich), Klausurplanung Oberstufe, automatische Zuteilung bei Überbuchung (Losverfahren als Fallback mit sichtbarer Begründung). Bestand: Kopplungen/Schienen manuell; Import der Kurswahl (Untis GPU 015) vorhanden; Erfassung fehlt.
- Wahlfächer, AG und Projekttage mit Anmeldephase und fairer Zuteilung im Generator sowie Selbsteinschreibung mit Schlüssel sind zurückgestellt („später“). Laufbahnplanung der Oberstufe ist ausdrücklich nicht im Umfang (frühestens nach dem Ausbau zum Komplettprodukt).
Abnahme: Eine Kurswahl mit zwei Kursen derselben Schiene wird als Konflikt je Kind angezeigt; die Zuteilung bei Überbuchung nennt die Begründung.

### STP-103 · Jahresstunden, Epochen, Blockphasen, mehrere Zeitraster · P3 · Status: offen
- Jahresstunden verteilen (Wochenkontingent über einen Zeitraum, mit Sperrungen, Blockung und Kalenderfolgen), Epochen- und Phasenplaner, Blockphasen für Teilgruppen (Praktikum, Fahrten; Bestand: Klassen-Sperren), mehrere Zeitraster und „Minuten-Stundenplan“ je Klasse oder Abteilung (siehe STP-008, STP-010), Unterrichtsrhythmen der Berufsschule.
- Das Erfassen längerer Abwesenheit einer Klasse (z. B. dreiwöchiges Betriebspraktikum) hat auf der Klassenseite und im Vertretungsplan dieselbe Höchstdauer (bis Schuljahresende).
Abnahme: Ein dreiwöchiges Betriebspraktikum einer Klasse lässt sich auf der Klassenseite erfassen und erscheint im Vertretungsplan; eine Klasse mit eigenem Zeitraster liefert korrekte Konfliktprüfung nach Uhrzeit.

### STP-104 · Engpassanalyse, Tauschvorschläge, Szenarien · P2 · Status: offen
- Vorab-Engpassanalyse („Warum nicht verplant?“ vor dem Lauf: Lehrkräfte-Kapazität, Räume, Sperrzeiten) — nur die Gründe je unverplanter Stunde sind gebaut (STP-049). Tauschvorschläge im Raster beim manuellen Planen (bisher nur in der Vertretung). Szenarien-Vergleich allgemein (bisher Plan-Stände und Planvorschläge). Der Betreiber ließ eine Aufstellung priorisierter Planungsverbesserungen (Reviews vom 12.10.) anfertigen; die Freigabe zur Umsetzung steht aus.
Abnahme: Vor dem Lauf nennt eine Analyse, dass für Chemie nur 12 Raumstunden bei 18 Wochenstunden Bedarf vorhanden sind; im Raster zeigt „Tauschen“ passende Tauschpartner.

### STP-105 · Hitzefrei und abweichendes Stundenraster einzelner Tage · P3 · Status: offen
- Ein Tag kann ein abweichendes Stundenraster erhalten (z. B. Hitzefrei, verkürzte Stunden); Plan, Vertretung, Monitor und Kalender nutzen für diesen Tag das abweichende Raster.
Abnahme: Für einen Hitzefrei-Tag mit Unterrichtsende 11:30 zeigen Plan und Monitor nur die Stunden bis dahin; Stunden danach gelten als entfallen.

### STP-106 · Wertrechnung, Unterrichtsmatrix, Abteilungsplanung · P3 · Status: offen
- Soll-/Ist-Wertrechnung (Fach-Faktoren, Anrechnungsstunden, Wochen- und Jahresmittel, Lehrer-Jahresarbeit, Vergleich mit dem Vorjahr); bearbeitbare Unterrichtsmatrix (Klasse × Fach, Lehrkraft per Klick; Bestand: nur Übersicht); Abteilungsplanung für große Schulen (Gesamtplan aufteilen, dezentral planen, zusammenführen; Bestand: ein gemeinsames Planungsdokument, Abteilungen als Rollenzuschnitt). Zielgruppe und Bedarf sind unbeantwortet (offene Fragen des Vergleichs).
Abnahme: Die Unterrichtsmatrix erlaubt das Zuordnen einer Lehrkraft per Klick; eine Abteilung plant ihre Klassen und führt sie in den Gesamtplan zusammen.

### STP-107 · Schulformen, Sonderfälle, Standortwechsel · P3 · Status: offen
- Optionen, „garantiert nicht der Standard“: gemischte/jahrgangsübergreifende Klassen, Sonderstunden für Einzelne, Förderstunden pro Person, Förderunterricht, Lerngruppen aus mehreren Klassen; weitere Schulprinzipien sind zu recherchieren, ein Konzept liegt nicht vor.
- Sonderfälle beim Standortwechsel im Plan: Wechsel in Pausen, nur einmal hin und her, erste Stunden an Schule A nicht/an Schule B ja (teilweise über Standort, Rhythmus, Pendelregeln abbildbar, nicht geprüft).
- Eigenarbeit/Selbststudium bei Lehrkraft-Ausfall je Klassenstufe mit Material (VER-076).
Abnahme: Eine Lerngruppe aus 5a und 5b für Förderunterricht wird als Kurs mit zwei Klassen geplant; der Standortwechsel „in den Pausen erlaubt“ lässt sich als Pendelregel einer Lehrkraft einstellen.

### STP-108 · Weitere Wettbewerbs-Lücken der Planung · P3 · Status: offen
- Mindestanzahl freier Tage (Lehrkraft/Klasse), Sperrzeiten je Fach, Untis-Wechsel-Assistent (Import mit Prüfbericht „das hat Untis gekannt, das fehlt bei uns“ und Zuordnung von Abwesenheitsgründen), Stundenplan als PDF für Eltern (vom Betreiber nur zur Ansicht gewünscht, nicht eingebaut; Stundenplan-Druck bleibt entfallen, STP-089), PDF je Klasse/Lehrkraft für die Verwaltung [Entscheidung offen].
Abnahme: Eine Regel „Sport nie in Stunde 1“ lässt sich je Fach als Sperrzeit anlegen; der Untis-Import liefert einen Prüfbericht mit nicht übernommenen Elementen.

### 1.12 Querschnitt der Planung

### STP-109 · Rechte der Planung im Überblick · P0 · Status: Ist
| Aktion | Recht |
|---|---|
| Generator starten/abbrechen/löschen/übernehmen, Plan leeren, Teilneuplanung, Plan-Stände anlegen/wiederherstellen/löschen, Dauerprüfung manuell starten, Planvorschläge entscheiden, Zeitraum-Plan kopieren/löschen | `timetable.generate` (Entscheiden auch `timetable.edit` | `settings.edit`) |
| Stundentafeln, Kurse, Zuweisung, Kurse aus Stundentafeln, Aufsichten erzeugen, Stunden verschieben/fixieren/Optionen, Plan-Stände und Läufe lesen | `timetable.edit` |
| Qualitätsbericht lesen | `timetable.edit` | `timetable.generate` |
| Einstellungen, Zeiträume speichern, Regeln, Vorlagen, Klausur-Vorgaben Schule/Jahrgang | `settings.edit` |
| Fächer schreiben, Feiertags-Import, Klassenwerte der Klausurgrenzen | `masterdata.edit` |
| Planverlauf lesen, Wiederherstellen, Rückgängig | `history.restore` |
| Audit-Protokoll lesen | `audit.read` |
| Planungsseite, Reiter | sichtbar nur mit passendem Recht; Reiter ohne Recht ausgeblendet |

- Standard: Administration und Planer besitzen `timetable.generate`/`timetable.edit`; Schulleitung nicht (Test mit Demo-Konto: Schulleitung darf den Generator nicht starten; ob gewollt, ist nicht bestätigt). Sekretariat darf Stundentafeln nur lesen (mit Grund). Fehlende Rechte werden in der Oberfläche genannt, nicht stumm ausgeblendet.
Abnahme: Als Schulleitung (Standardrolle) liefert `POST /planning/generate` 403 mit Nennung von `timetable.generate`; als Planer 200; ein Reiter ohne Recht erscheint nicht im Menü, die Direktadresse liefert eine Seite „Kein Zugriff“ im App-Rahmen.

### STP-110 · Audit und Live-Ereignisse der Planung · P0 · Status: offen
- Jede schreibende Aktion der Planung wird im Audit-Protokoll festgehalten (Aktion, Person, Zeitpunkt, Ziel), ohne Inhalte: Planänderung, Rückgängig, Wiederherstellen, Übernahme, Leeren, Plan-Stand wiederherstellen, Annahme/Verwerfen von Vorschlägen, Regeländerungen, Verschieben, Fixieren, Import, Export, Kursänderungen, Stundentafeln. Bestand: Audit für Verschieben, Fixieren, Import und Export, Kurs- und Stundentafeländerungen nicht belegt.
- Live-Ereignisse: `change` (Bereich, betroffene Daten) nach jeder Planänderung; Ereignisse für Pakete, Läufe und Stunden; „plan_proposal_applied“ an die Konten der Informierten. Die Zeitzone im Audit ist UTC; Abfragen mit Zeitzonen-Offset werden nach UTC umgerechnet.
Abnahme: Verschieben einer Stunde, Fixieren und ein Untis-Import erzeugen je einen Audit-Eintrag ohne Stundeninhalt; ein Abruf mit `since=2026-10-18T10:00:00+02:00` entspricht 08:00 UTC.

### STP-111 · Datenschutz und Löschkonzept der Planung · P0 · Status: offen
- Das Planungsdokument enthält Namen und Abwesenheitsgründe; es ist verschlüsselt (STP-015). Beim Austritt einer Person wird sie nach 30 Tagen aus allen gespeicherten Planversionen entfernt (Namen im Versionstext „[gelöscht]“, Protokollziele „student:gelöscht“); wer wieder im Planungsdokument steht, bleibt unberührt (Bestand, Löschkonzept DAT).
- Offen: Aufbewahrung und Löschung von Abwesenheiten (Lehrkräfte), manuellen Entscheidungen, Planvorschlägen, Protokoll, Plan-Ständen und Läufen; Pseudonymisierung unvollständig (Benutzername im Protokoll, Namen in Abwesenheiten); diese Datenarten werden mit Frist und Anonymisierung ins Löschkonzept aufgenommen. Gründe von Lehrkraft-Abwesenheiten sind intern und erscheinen nie in öffentlichen Ansichten.
Abnahme: Nach Ablauf der Frist sind Name und Kürzel einer ausgetretenen Person in keiner Planversion und keinem Plan-Stand mehr auffindbar; das Löschkonzept enthält „Abwesenheiten“, „Planvorschläge“ und „Plan-Stände“ mit Frist.

### STP-112 · Oberflächenregeln der Planung · P1 · Status: offen
- Anrede „Sie“; Erklärungen nur hinter dem Hilfe-Symbol an der Beschriftung (Hilfe nach 2 s Verweilen, per Rechtsklick auf den Namen, Antippen auf Touch, F1 bzw. Umschalt+? im Feld; Esc schließt; 1 bis 3 Sätze, reiner Text); keine Erklärabsätze; keine Schieberegler (Zahlenfeld oder Stufenauswahl); App-Dialoge statt Browser-Popups (kein Browser-Bestätigungsdialog, kein Browser-Abfragedialog beim Verlassen); verständliche deutsche Fehlermeldungen mit Feldbezug, Servertexte ohne Feldnamen; unerwartete Fehler „Das hat nicht geklappt“ mit Fehlernummer.
- Glossar: „Kursraum“, „Woche 1“, „Stunde/Doppelstunde“ (nie „Block“), „Planung“ (nie „Planungsdokument“), „Strafpunkte“, „Wochenmuster“; keine Emojis oder Zeichen als Icons; Beschriftungen höchstens drei Wörter; Produktname nur zentral. Entwürfe der Reiter in Planung und Einstellungen gehen beim Reiterwechsel nicht verloren (Bestand: nur Stundentafeln; Speichern sendet das ganze Einstellungsobjekt) und lösen bei Verlassen eine Rückfrage im App-Dialog aus.
Abnahme: Ein Test findet in den Planungsseiten keinen Erklärabsatz, kein „du“, kein „Block“ und kein Browser-Dialog; Reiterwechsel mit ungespeicherter Regeländerung fragt im App-Dialog nach; ein Entwurf in „Regeln“ bleibt beim Wechsel zu „Generator“ erhalten.

---

# Teil VER · Vertretung, Aufsichten, Monitore

Dieser Teil beschreibt die Tagesvertretung (Live-Umplanung), Abwesenheiten, den Vertretungsplan mit Druck/Aushang, Pausenaufsichten, Monitore, die Klausurprüfung und die Nachschreibtermine. Der reguläre Plan und seine Dauerprüfung stehen in Teil STP.

### 2.1 Grundmodell und Abwesenheiten

### VER-001 · Der Tagesplan wird berechnet, nicht gespeichert · P0 · Status: Ist
- Aus dem regulären Stundenplan, den Abwesenheiten (Lehrkräfte, Klassen, Räume, Kursentfälle), Terminen mit Lehrkräften, Klausuren, Raumsperren und manuellen Entscheidungen wird je Schultag ein wirksamer Tagesplan berechnet (Live-Umplanung). Das Ergebnis hängt nur von den Eingaben ab (Schule, Datum, Historie der Vertretungsfälle). Tagesplan und Lehrkraft-Statistik stammen aus demselben Stand des Planungsdokuments.
- Krankmeldungen, Abwesenheiten, Raumsperren und Klassenfahrten ändern den regulären Stundenplan nicht (Entscheidung: „Das ist Absicht“). Strukturelle Folgen (Sperrzeit mit Gültigkeitsbeginn, Raumausfall, Kurs/Stundentafel) behandelt „Plan prüfen“ (STP-069).
- Der Tag wird in Einheiten (Block, Stunde, Kursteil) zerlegt; Doppelstunden werden stundenweise behandelt (eine Stunde kann betroffen sein, die andere nicht). Status je Einheit: normal (findet statt, ggf. Raumwechsel) · affected (Lehrkraft fehlt, noch offen) · sub (vertreten, betreut oder mitbetreut) · cancelled (entfällt) · class_absent (alle Klassen abwesend) · moved (alte Position einer Verlegung) · shifted (neue Position einer Verlegung). Der Raum ist belegt bei normal, sub, shifted, affected; die Klasse hat nichts bei class_absent, cancelled, moved.
- Kein Schultag (Ferien, Feiertag, schulfrei, Wochenende, kein Unterrichtstag der Klasse): Tagesplan ohne Einträge mit Grund. Zeitraumabfragen sind auf höchstens 400 Tage begrenzt; die Wochenhistorie startet je Woche (ab Montag) neu; die Wochenstatistik ist nicht auf Montag bis Freitag festgelegt.
Abnahme: Nach einer Krankmeldung ist `GET /timetable/class/5a` für den Folgetag unverändert, `GET /substitutions?date=…` zeigt die Einträge; dieselbe Anfrage zweimal liefert dasselbe Ergebnis; für einen Ferientag liefert der Tagesplan keine Einträge und den Ferientitel als Grund.

### VER-002 · Abwesenheiten: Arten, Felder, Sichtbarkeit des Grundes · P0 · Status: Ist
| Feld | Bedeutung |
|---|---|
| `kind` | teacher · class · room · lesson |
| `ref` | Kürzel der Lehrkraft, Kennung der Klasse bzw. des Raums; bei lesson „<Kurs>“ (ganzer Kurs) oder „<Kurs>#<Kursteil>“ (0-basiert) |
| `date_from`, `date_to` | erster und letzter Tag, inklusiv |
| `periods` | betroffene Stunden (0-basiert); leer = ganzer Tag; bei lesson leer = alle Stunden des Kurses an diesem Tag |
| `reason` | Grund (Freitext, intern); verschlüsselt gespeichert |
| `self_reported` | von der Lehrkraft selbst gemeldet |

- Eine Abwesenheit deckt eine Stunde, wenn das Datum im Bereich liegt und (`periods` leer oder die Stunde enthalten). Abwesenheitsarten (krank, Fortbildung, Dienstreise, Klassenfahrt, Sonstiges) werden getrennt gezählt (Backlog B-36) [unklar: vollständige Bezeichnungen des Bestands].
- Der Grund erscheint in keiner öffentlichen Ansicht (Monitor, Aushang, Druck, Kinder-Ansicht) und nie in Benachrichtigungen. Er ist sichtbar für Personen mit `substitution.edit`; der Feldtext sagt das richtig („nur für Personen mit Vertretungsrecht sichtbar“; Befund: „nur für die Schulleitung“ war falsch). Die Administration sieht keine Krankheitsgründe.
Abnahme: Anlegen einer Abwesenheit mit Grund „Grippe“ → der Grund erscheint nur in der Bearbeitungsansicht von Konten mit `substitution.edit`, nicht auf Monitor, Druck oder in der E-Mail; die Datenbank enthält den Grund nur verschlüsselt.

### VER-003 · Abwesenheit anlegen, ändern, löschen, Vorschau · P1 · Status: Ist
- Rechte: Lesen (`GET /absences`): angemeldet, Umfang nach `substitution.edit` | `plans.read_all` | `absence.report_self` (Letzteres nur eigene). Anlegen (`POST /absences`), Ändern (`PUT /absences/{id}`), Vorschau (`POST /absences/preview`): `substitution.edit`. Löschen: `substitution.edit`, oder `absence.report_self` für eigene Meldungen. Alles auditiert; ein fremder Eintrag liefert 404.
- Vorschau vor dem Anlegen: betroffene Einträge, Ferien-Einträge und der Unterschied der Planung vor und nach der Abwesenheit; höchstens 31 Schultage. Liegt der Zeitraum in den Ferien, zeigt der Dialog „keine Stunden betroffen“ bzw. die Anzahl betroffener Einträge und warnt. Hinweis: „Klasse ist nicht da“ hat auf der Klassenseite und im Vertretungsplan dieselbe Höchstdauer (bis Schuljahresende).
- Eingabeprüfung: Beginn, Ende und Bezug sind Pflicht (Meldung „Bitte ein Startdatum angeben.“); Ende vor Beginn → 422; Kennungen werden nicht wiederverwendet.
Abnahme: `POST /absences` ohne Datum → 422 mit „Bitte ein Startdatum angeben.“; Vorschau einer 40-tägigen Abwesenheit begrenzt sich auf 31 Schultage; Lehrkraft versucht eine Abwesenheit des Sekretariats zu löschen → 403/404.

### VER-004 · Selbstmeldung der Lehrkraft · P1 · Status: Ist
- Lehrkräfte melden sich selbst ab (`POST /absences/report-self`, Recht `absence.report_self`; Knopf „Krank melden“; Schnellwahl auf der Startseite „Ich bin krank“ / „Mein Kind ist krank“ / „Beurlaubung“). Dabei geben sie an, was die Klasse in den verpassten Stunden tun soll; die Vertretungsplanung sieht das. Eigene Meldung löschen: nur selbst gemeldete (`self_reported`); Meldungen des Sekretariats nicht. Höchstzahl Tage der Selbstmeldung [unklar: Wert].
- Die Meldung wirkt sofort: Vertretungen werden verteilt (VER-028). Das Recht liegt nicht bei der Administration.
Abnahme: Lehrkraft meldet sich für Mo–Di ab → Tagesplan Mo und Di enthält Vertretungen/Entfälle; sie kann die Meldung löschen, nicht aber eine vom Sekretariat angelegte; Administration erhält beim Aufruf 403.

### VER-005 · Klassenabwesenheit („Klasse ist nicht da“) · P0 · Status: Ist
- Klassenabwesenheit (Wandertag, Betriebspraktikum, Klassenfahrt) gilt nur an Unterrichtstagen der Klasse und ganztägig, wenn die Sperre (laut Rhythmus oder Gesamt-Sperre) mindestens `max_periods_per_day` Stunden (Standard 8) trifft; Teilsperren („erst ab 16:00“) zählen nicht als abwesend. Herkunft: „absence“ (gemeldet) oder „rhythm“ (regulärer Ganztag laut Rhythmus).
- Klassen mit regulärem Praxis- oder Berufsschultag erscheinen nirgends als abwesend; die Karte „Abwesende Klassen“ entfällt in Vertretungsplan, Druck, Monitor und Startseiten-Kennzahl (Betreiber-Pflichtanforderung A-56). Eine gemeldete Klassenabwesenheit erscheint als eine Zeile je Klasse („5a · ganztägig nicht im Haus · Wandertag“), nicht als Zeile je Stunde. In der Klassenansicht wird jede Zelle (außer Aufsicht/Entfall) zu „Klasse abwesend: <Grund>“, auch Kopplungsstunden anderer Klassen. Lehrkräfte, deren Stunde dadurch entfällt, gelten als „freigesetzt“ (nicht abwesend).
- Dialog „Klasse ist nicht da“ mit Zeitraum und Begleitung.
Abnahme: Klasse mit regulärem Mittwoch-Berufsschultag fehlt in „Abwesende Klassen“ (Karte existiert nicht); ein Wandertag von 5a erzeugt genau eine Zeile; die Lehrkraft der entfallenden Stunde ist als Vertretung einsetzbar.

### VER-006 · „Unterricht findet nicht statt“ und Raumsperren · P1 · Status: Ist
- Abwesenheit der Art lesson verweist auf Kurs (ganz) oder Kursteil; leere Stundenliste = alle Stunden des Tages. Die betroffenen Einheiten werden wie fehlende Lehrkräfte entschieden (Rand → Entfall, Mitte → Verlegung, jüngere Klassen → Betreuung); die Lehrkraft ist dabei frei (nicht abwesend) und kann anderswo vertreten. Einträge tragen `dropped` = wahr (zählen nicht als Vertretungsfall). Hinweis: „Unterricht entfällt (Grund) – …“ bzw. „Unterricht entfällt“; der Text „Vertretung für …“ entfällt dann.
- Raumsperren (gesperrte Stunden je Raum) und Klausurbelegung machen einen Raum unbenutzbar: „Raum <Id> gesperrt“, „Raum <Id> durch Klausur belegt“ (VER-021).
Abnahme: Kursentfall für „M-5a#1“ am Montag entfällt nur Kursteil 1; die Lehrkraft erscheint in der Kandidatenliste als „freigesetzt“; ein gesperrter Raum erzeugt einen Raumeintrag statt eines Entfalls.

### VER-007 · Termine mit Lehrkräften als Abwesenheit · P1 · Status: Ist
- Termine mit teilnehmenden Lehrkräften (Fortbildung, Exkursion, Klassenfahrt), außer Art „pflicht“: Die Lehrkräfte fehlen in allen Stunden, die sich mit der Zeitspanne des Termins überschneiden; ohne Uhrzeit gilt der ganze Tag; bei mehrtägigen Terminen an Folgetagen ganztägig bis Tagesende. Grund „Termin: <Titel>“ (intern). Art „pflicht“ (Anwesenheit Pflicht, z. B. Tag der offenen Tür am Samstag) löst keine Vertretung aus.
- [unklar: Ob Klassentermine automatisch als „Klasse nicht im Haus“ gelten; Backlog B-26 verlangt es.]
Abnahme: Fortbildung 10:00–12:00 mit Lehrkraft X macht X in den überschneidenden Stunden abwesend und erzeugt Vertretungen; derselbe Termin als „pflicht“ erzeugt keine.

### VER-008 · Automatische Quellen und Schnellmeldung · P1 · Status: Ist
- Der Vertretungsplan füllt sich selbst aus Krankmeldungen, Beurlaubungen, Meldungen der Lehrkräfte und Terminen (Betreiber 12.10.: „Krankmeldungen, Entschuldigungen und Termine gehen automatisch in den Plan“; er „darf bleiben, soll aber ein bisschen updaten“, „sehr sehr viel Text“ wurde gekürzt). Krankheit des eigenen Kindes der Lehrkraft und Beurlaubung sind Schnellmeldungen der Startseite.
- Termine haben das Feld „Teilnehmende Lehrkräfte“. Änderungen laufen über das Ereignis `change` zu allen Clients.
Abnahme: Eine genehmigte Beurlaubung einer Lehrkraft erscheint ohne weitere Eingabe im Tagesplan; ein neu angelegter Termin mit teilnehmender Lehrkraft verändert den Plan innerhalb von Sekunden bei geöffneten Clients.

### 2.2 Entscheidungslogik der Vertretung

### VER-009 · Ablauf eines Tages (feste Reihenfolge) · P1 · Status: Ist
1. Schultag prüfen (kein Schultag → leerer Plan mit Grund).
2. Einheiten aufbauen: nur Blöcke, die an diesem Wochentag laufen (Wochenangabe und Unterrichtstage der Klassen); Blöcke an Nicht-Unterrichtstagen der Klasse entfallen.
3. Klassen-Abwesenheiten, Lehrkraft-Abwesenheiten, Termine, Kursentfälle, Raumsperren, Klausuren einlesen.
4. Manuelle Entscheidungen anwenden (VER-020).
5. Phase A: Randstunden älterer Klassen (ab `cancel_min_grade`) entfallen lassen bzw. Lücken verlegen (ohne Verbrauch an Vertretungen).
6. Phase B: Klausuren und jüngere Klassen — immer Vertretung oder Betreuung, mit Lockerung der Limits als letztem Ausweg. Findet sich keine Lehrkraft: Entfall mit Warnung „Keine Lehrkraft frei – Klausur ohne Aufsicht, bitte manuell regeln“ bzw. „Unterstufe ohne Betreuung, bitte manuell regeln“. Danach Blocktreue (VER-015).
7. Phase C: Rest der älteren Klassen (Mitte: Verlegung oder Vertretung; Rand: Entfall).
8. Raumänderungen (VER-021).
9. Aufsichten der abwesenden Lehrkräfte (VER-047).
10. Klausureinträge, Warnungen, Statistik, Abwesenheitsübersicht.
Abnahme: Ein Tag mit fehlender Lehrkraft, einer Klausur und gesperrtem Raum wird in genau dieser Reihenfolge bearbeitet; das Ergebnis ist bei identischen Eingaben identisch.

### VER-010 · Entscheidungsreihenfolge und Phasen · P0 · Status: Ist
1. Manuelle Entscheidungen haben immer Vorrang.
2. Klausuren werden markiert; sie dürfen nie still entfallen.
3. Klassenstufe ≥ `cancel_min_grade` (Standard 7): betroffene Randstunden entfallen iterativ von außen nach innen. Lücken in der Mitte schließt `middle_strategy` = „shift_first“ (Standard) durch Verlegung einer nicht betroffenen Rand-Einzelstunde der Klasse (der Ausfall wandert an den Rand); bei „substitute_first“ wird zuerst vertreten.
4. Klausuren und Klassen unter `cancel_min_grade`: immer Vertretung oder Betreuung, kein Entfall.
5. Die übrigen Einheiten folgen der Mittelreihenfolge (VER-011).
6. Pausenaufsichten abwesender Lehrkräfte sowie Raumsperren und durch Klausuren belegte Räume werden anschließend behandelt (VER-021, VER-047).
- Betreiberwunsch (12.10.): Ersatz durch Lehrkräfte, die „nicht hin und her reisen müssen“ (VER-017); Lehrkräfte, die ohnehin springen (Freistunden). Hilfetext: „Jüngere Klassen werden immer vertreten.“
Abnahme: Klasse 9 (≥ 7), Lehrkraft fehlt in der 1. Stunde → Entfall am Rand ohne Vertretung; Klasse 5 → Vertretung oder Betreuung; Klasse 8, Lehrkraft fehlt in der 3. von 6 Stunden → Verlegung einer Rand-Einzelstunde in die Lücke; Klausur → nie Entfall ohne Warnung.

### VER-011 · Mittelreihenfolge und Strategien · P1 · Status: Ist
- Reihenfolge für übrige Einheiten: (1) Vertretung durch qualifizierte Lehrkraft (Fach im Fächerprofil), (2) Mitbetreuung (Kopplung, nur bei Kursteilen; Vorrang gleiches Fach: Rang 0, sonst 1), (3) Betreuung (fachfremd; nur wenn `allow_unqualified` = ja), (4) Entfall (am Rand ohne Warnung; in der Mitte mit Warnung „Entfall in der Tagesmitte – keine Vertretung gefunden“). Ist keine Vertretung möglich, fällt Unterricht am Tagesende aus („Entfall am Tagesende“).
- `edge_strategy`: „cancel“ (Standard: Randstunde entfällt), „substitute_if_qualified“ (am Rand nur vertreten, wenn qualifiziert und im Haus, sonst Entfall), „substitute“ (am Rand wie Mitte). `middle_strategy`: „shift_first“ (Standard) oder „substitute_first“.
- Betreuung (fachfremd): Hinweis „Betreuung (fachfremd)“; im Fachraum (z. B. Sporthalle) wird die Betreuung in den Heimatraum der einzigen Klasse verlegt, sofern dort frei und am selben Standort.
Abnahme: Mit `allow_unqualified` = nein bleibt eine Stunde ohne Fachlehrkraft offen bzw. entfällt statt fachfremd betreut zu werden; mit „substitute_if_qualified“ entfällt eine Randstunde, wenn keine qualifizierte Lehrkraft im Haus ist.

### VER-012 · Vertretungsregeln (Policy) und ihre Standardwerte · P1 · Status: Ist
| Wert | Standard | Einheit | Wirkung |
|---|---|---|---|
| `cancel_min_grade` | 7 | Klassenstufe | ab dieser Stufe darf Unterricht entfallen |
| `edge_strategy` | cancel | – | cancel · substitute_if_qualified · substitute |
| `middle_strategy` | shift_first | – | shift_first · substitute_first |
| `allow_unqualified` | ja | – | fachfremde Betreuung erlaubt |
| `max_subs_per_day` | 2 | Vertretungen je Lehrkraft und Tag | Tageslimit |
| `max_subs_per_week` (Lehrkraft) | 3 | Vertretungen je Lehrkraft und Woche | Wochenlimit |
| `max_per_day` (Lehrkraft) | 7 | Stunden | Tageshöchstbelastung |
| `max_hours` (Lehrkraft) | 25 | Stunden je Woche | Deputat, Bezug der Fairness-Strafe |
| `substitution_confirm` | nein | – | Vorschläge gelten sofort |

- Einstellbar im Planungs-Reiter „Vertretung & Abwesenheit“ (Recht `settings.edit`); Oberfläche und Server verwenden dieselben Grenzen (Befund: Entfall ab Stufe 13 gegen 14). Eine Ausnahme der Entfall-Grenze je Klasse wäre sinnvoll, ist aber nicht umgesetzt [offen]. Der Hilfetext beschreibt die Wirkung („Jüngere Klassen werden immer vertreten“), nicht die Bedienung.
- Die starren Grenzen `max_subs_per_day/week` werden durch Fairness über das Halbjahr ergänzt bzw. ersetzt (VER-018).
Abnahme: Wert `cancel_min_grade` = 5 lässt Entfall in Stufe 5 zu; der Reiter speichert nur mit `settings.edit`; Standardwerte eines neuen Dokuments entsprechen der Tabelle.

### VER-013 · Kandidatenprüfung (harte Ausschlüsse) · P0 · Status: Ist
Eine Lehrkraft scheidet aus, wenn — geprüft in dieser Reihenfolge, alle Gründe werden gesammelt —:
- abwesend in dieser Stunde; Sperrzeit (harte Sperre); belegt (anderer Unterricht, Vertretung oder Verlegung in dieser Stunde);
- nicht am Standort der Einheit eingesetzt (Standortliste); Pendelart „nie pendeln“: ein anderer Standort ist am Tag belegt; „höchstens 1×“: mehr als ein Standortwechsel entstünde; Wegezeit zwischen Standorten (freie Stunden, Wegezeit-Tabelle, Mindestpause; Pausenaufsicht eines anderen Standorts in den Pausen nahe der Stunde zählt);
- nur ohne Lockerung (`relax` = falsch): Tageslimit Vertretungen (2), Wochenlimit (3; Woche = Historie + heute), Tageshöchststunden (`max_per_day` 7).
- Mit Lockerung entfallen die drei Limits; Stundenbelegung und Sperren gelten weiter. Optionen: nur qualifizierte Lehrkräfte; nur Lehrkräfte, die ohnehin im Haus sind. Eine Pausenaufsicht zählt für eine Lehrkraft nur dann als Bindung, wenn sie in der Stunde vor und nach der Pause nicht abwesend ist.
Abnahme: Eine Lehrkraft mit Sperrzeit in der Stunde wird nie vorgeschlagen, auch nicht mit Lockerung; die Lehrkraft mit bereits 2 Vertretungen heute wird ohne Lockerung ausgeschlossen, mit Lockerung (Klausur/Unterstufe) zugelassen.

### VER-014 · Bewertung der Kandidaten (Punkte) · P1 · Status: Ist
Höchster Wert gewinnt; Gleichstand: erste Lehrkraft nach Kennung.

| Merkmal | Punkte | Bedingung |
|---|---|---|
| Fach-Qualifikation | +40 | Fach im Fächerprofil |
| Kennt die Klasse | +15 | unterrichtet schon eine der Klassen |
| Klassenleitung | +5 | Klassenleitung einer Klasse der Stunde |
| Freigesetzt | +30 | ohnehin frei, weil anderer Unterricht entfällt |
| Müsste extra kommen | −40 | heute keine Stunde im Haus |
| Springstunde (ohnehin im Haus) | +20 | Stunde liegt zwischen erster und letzter Stunde der Lehrkraft (nicht freigesetzt) |
| Müsste früher kommen | −(4 + 6 × (erste Stunde der Lehrkraft − Stunde − 1)) | vor der ersten Stunde |
| Müsste länger bleiben | −(4 + 6 × (Stunde − letzte Stunde − 1)) | nach der letzten Stunde |
| Gleicher Standort | +5 | heute schon am selben Standort |
| Anderer Standort | −10 | heute an einem anderen (und nicht am selben) |
| Vertretungen diese Woche | −6 × Anzahl × 25 / max(5; Deputat) | Deputat `max_hours` (25) |
| Vertretungen heute | −8 je Vertretung | – |
| Wunsch „frei“ in dieser Stunde | −8 | weicher Wunsch |
| Block-Bonus: übernimmt Nachbarstunde | +40 | gleicher Block, Nachbarstunde bereits von dieser Lehrkraft vertreten |
| Block-Bonus: wäre in Nachbarstunde frei | +30 | Nachbarstunde offen, Lehrkraft dort frei (nicht unter Fairness-Grenze) |

- Der Block-Bonus wird bei der Nachbarprüfung nicht erneut berechnet. Jede Auswahl wird mit Begründung angezeigt (Merkmale wie „Fachlehrkraft“, „kennt die Klasse“, „ohnehin im Haus“, „unter Soll“ statt einer nackten Punktzahl, VER-026).
- Betreiberwunsch: Vertretung „nur Lehrer unterrichten als Vertretung, die Qualifikation haben für die Klasse“; die zuständige Fachlehrkraft zuerst (VER-016).
Abnahme: Zwei Kandidaten: A mit Fach (+40), Springstunde (+20), Vertretungen heute 1 (−8) = 52; B ohne Fach (0), extra kommen (−40) = −40; A gewinnt. Bei Gleichstand gewinnt die kleinere Kennung.

---
### VER-015 · Doppelstunden und Blocktreue · P1 · Status: Ist
- Übernimmt eine Lehrkraft eine Stunde, die immer gedeckt werden muss (Klausur oder Klasse unter `cancel_min_grade`), bekommt sie die offene Nachbarstunde desselben Blocks mit, wenn sie dort frei ist (sonst würde eine andere Klasse die Nachbarstunde dazwischen belegen). Eine bereits vertretene Nachbarstunde gibt den Block-Bonus (+40; +30, wenn die Nachbarstunde offen und die Lehrkraft dort frei ist). Eine Doppelstunde zählt bei Limits als zwei Stunden.
- Ist eine Teilung nicht vermeidbar, steht im Plan „Block geteilt: keine Lehrkraft für beide Stunden frei“.
- Messwert des Bestands: Von 7 Doppelstunden waren vorher 3 geteilt, nachher keine.
Abnahme: Fällt die Lehrkraft einer Doppelstunde in Klasse 6 aus und ist eine Kandidatin für beide Stunden frei, übernimmt sie beide; ist sie nur für eine frei, erscheint der Hinweis „Block geteilt: …“ an beiden Einträgen.

### VER-016 · Qualifikation: wer vertreten darf · P1 · Status: offen
- Betreiberwunsch (11.10.): „das ist auch wirklich nur Lehrer unterrichten als Vertretung, die Qualifikation haben für die Klasse“; zuerst die zuständige Lehrkraft der Klasse (z. B. Englisch, Deutsch); wenn die nicht kann, nur qualifizierte Lehrkräfte.
- Ist: Qualifikation (+40) und Klassenkenntnis (+15) in der Bewertung; Option „nur qualifizierte Lehrkräfte“; `allow_unqualified` Standard ja führt zur fachfremden „Betreuung“ als Rückfall. Der Betreiber hat nicht bestätigt, ob der Standard „nur qualifiziert“ sein soll; die Umsetzung des Wunsches ist nicht bestätigt (13.10. im Wesentlichen durch die Ersatzauswahl nach Fach, Freistunde und Klassenkenntnis abgedeckt).
- Profil „kann vertreten in“ (Lehrkraft gibt Klassen an, in denen sie vertreten kann, vorgeschlagen die unterrichteten Klassen; Wunschklassen entfallen als Begriff, LEH): Die Vertretung bevorzugt Lehrkräfte mit „kann vertreten in“ für die Klasse.
Abnahme: Mit der Einstellung „nur qualifizierte“ wird eine Stunde Englisch nie fachfremd betreut; sie bleibt offen mit Warnung; eine Lehrkraft mit „kann vertreten in 7b“ wird vor einer ohne den Eintrag vorgeschlagen.

### VER-017 · Standort, Pendeln und Wegezeit in der Vertretung · P1 · Status: Ist
- Lehrkräfte, die nicht pendeln, werden nicht am anderen Standort eingesetzt. Ersatz bevorzugt Lehrkräfte, die „nicht hin und her reisen müssen“ (Betreiber 12.10.): gleicher Standort heute +5, anderer Standort −10; harte Ausschlüsse nach Pendelart, Standortliste, Wegezeit (VER-013). Der Standort einer Pausenaufsicht wird bei der Wegezeit berücksichtigt.
- Standort-Verfolgung: Startstandort der Lehrkraft am Tag, ob sie am Standort der Aufsicht ist, ob sie reisen muss oder krank ist (Abzeichen „heute Hauptstandort“, „wechselt“, krank; Betreiber: „Das muss auch getrackt werden an welchem Standort die sind“).
Abnahme: Lehrkraft „nie pendeln“ mit Unterricht an Standort A erscheint nicht als Kandidatin für eine Stunde an Standort B; zwei Kandidaten, einer am selben Standort: der am selben Standort steht oben (Differenz 15 Punkte).

### VER-018 · Fairness, Limits und Vertretungskonto · P1 · Status: offen
- Ist: Limits `max_subs_per_day` 2 und `max_subs_per_week` 3 (ohne Lockerung), Fairness-Abzug −6 × Anzahl der Vertretungen der Woche × 25 / max(5; Deputat) und −8 je Vertretung heute; Wochenhistorie von Montag bis zum Vortag (Zählung vertretung + betreuung, nicht mitbetreuung). Mehrtägige Krankmeldung: jeder Tag wird geplant, die Fairness-Tabelle zählt je Lehrkraft. Befund: Die Historie beginnt jeden Montag neu; in einer Vier-Wochen-Simulation (drei Langzeitkranke) trugen 17 von 57 Lehrkräften alles.
- Wunsch (A-49, Backlog B-36): Vertretungen verteilen sich über das Halbjahr gleichmäßig nach Deputat. Vertretungen, Entfälle und Mitbetreuungen werden je Tag in einem Vertretungskonto gespeichert (nachträgliche Änderungen zählen mit); die Auswahl bevorzugt Lehrkräfte unter ihrem Soll (Anteil nach Deputat) im eingestellten Zeitraum (Standard Halbjahr). Keine starren Mindestzahlen; Höchstgrenzen bleiben als Schutz mit Warnung. Vertretungsseite und Lehrkraft-Detail zeigen Ist, Soll und Abweichung im Halbjahr; jede Lehrkraft sieht ihr eigenes Konto. Abwesenheitsarten werden getrennt gezählt; Monatsübersicht Mehrarbeit je Lehrkraft als CSV. Weitere Ausbaustufen (Saldo, Monatszähler, Schwellenwert nach Beschäftigungsumfang × 3 / Regelmaß, Abrechnung, Vertretungsreserve, Bereitschaft) sind Vergleichslücken mit Bedarfsfrage an den Betreiber.
Abnahme: Simulation über vier Wochen mit drei Langzeitkranken: Keine Lehrkraft liegt über dem Doppelten ihres Solls, solange andere unter Soll verfügbar sind; die Vertretungsseite zeigt für Lehrkraft X „Ist 6, Soll 4,2, +1,8“.

### VER-019 · Klausuren im Vertretungsplan · P0 · Status: Ist
- Eine Klausur ist eine Einheit mit Stunden (Start, Länge, optional Kursteil und Raum); ihr Raum ist für diese Stunden belegt. Fällt die Lehrkraft aus, wird zwingend eine Aufsicht eingeplant (Vertretung ohne Entfallmöglichkeit); die Einheit erhält den Vermerk „– Klausuraufsicht“. Aufsichten werden genannt („Aufsicht: <Kürzel>“).
- Klausur-Eintrag (Art „klausur“) mit Notiz „<Titel> (<Länge> Std.)“ und Hinweisen (je Hinweis eine Warnung): „Kurs hat zu dieser Zeit laut Plan keinen Unterricht“; „Unterricht zur Klausurzeit entfällt – bitte klären“ (Entfall oder Verlegung); „Klasse abwesend – Klausur verschieben“. Eine manuelle Entscheidung „entfällt“ erzeugt „Klausur entfällt durch manuelle Entscheidung“.
- Die Art „test“ (angekündigter Test) erscheint im Stundenplan; die Vertretungslogik unterscheidet beide Arten nicht [unklar: ob Tests anders behandelt werden sollen].
Abnahme: Fällt die Klausurlehrkraft aus und gibt es keine freie Lehrkraft, erscheint die Warnung „Keine Lehrkraft frei – Klausur ohne Aufsicht, bitte manuell regeln“; eine Klausur wird nie ohne Warnung zum Entfall.

### VER-020 · Manuelle Entscheidungen (Overrides) · P0 · Status: Ist
- Je Datum und Einheit (Stunde, Kursteil) gilt die zuletzt gespeicherte Entscheidung. Aktionen: `cancel` (Entfall, manuell), `keep` (Unterricht findet statt, Lehrkraft nicht mehr frei; optional Raum), `room` (nur Raumänderung), `substitute` (Lehrkraft eintragen; fehlt sie, wird automatisch geplant mit Warnung; ist es die eigene Lehrkraft, wie `keep`).
- Bei `substitute` wird auch eine abwesende oder belegte Lehrkraft eingetragen, aber mit Warnung „manuell eingeteilte Lehrkraft <Kürzel> ist abwesend“ bzw. „… ist bereits belegt (<Beschreibung>)“. Art: Vertretung bei qualifizierter, sonst Betreuung; Hinweis „Vertretung (manuell)“ bzw. „Betreuung (manuell)“; eine eigene Notiz hat Vorrang. Manuelle Einträge zählen bei Limits und Vertretungsfall wie automatische und sind von der automatischen Umplanung ausgenommen (Kennzeichen „manual“). Existiert die Einheit nicht, Warnung „Manuelle Änderung <Kennung>: Stunde <Stunde> (<n>. Std., Teil <k>) findet an diesem Tag nicht statt“. Entscheidungen zu Aufsichten werden gesondert gespeichert (VER-047).
- `GET/POST/DELETE /overrides`, Recht `substitution.edit`; auditiert. Overrides hängen an Stunden-Kennungen (STP-020, STP-044).
Abnahme: Manuelles `substitute` mit abwesender Lehrkraft Y trägt Y ein und zeigt die Warnung; Löschen der Entscheidung stellt das automatische Ergebnis wieder her; ohne `substitution.edit` 403.

### VER-021 · Räume bei Vertretung: Ersatzraum, Tausch, Ausweichraum · P1 · Status: Ist
- Ein Raum ist unbenutzbar bei Sperre („Raum <Id> gesperrt“) oder Belegung durch die Klausur eines anderen Kurses („Raum <Id> durch Klausur belegt“). Reihenfolge: (1) Ersatzraum gleichen Typs am Standort (Klassenraum: zuerst Heimatraum der Klasse; Räume, die nicht Heimatraum einer anderen Klasse sind, vorn); Hinweis „<Grund> – Ersatzraum <Id>“. (2) Gibt es keinen, Tausch mit einer anderen Einzelstunde der Klasse am selben Tag. (3) Sonst Ausweichraum (Heimatraum der Klasse oder freier Klassen-/Kursraum) mit Warnung „… kein gleichwertiger Raum frei, Ausweichraum <Id> (bitte prüfen)“; ohne Ausweichraum „… kein Ersatzraum frei“. Raumwechsel ohne Ersatz führen nicht zum Entfall. Eintrag „Raumänderung“ für Stunden, die nur den Raum wechseln. Ausweich-Klassenräume gelten nicht für Klassen-/Kursräume selbst.
- Tausch (nur Einzelstunden, eine Klasse, keine Klausur, nicht manuell): Der Raum muss Typ „Fachraum“ sein; Stunden des gleichen Typs am Standort; Kandidaten nach Abstand zur gestörten Stunde (näher zuerst, bei gleichem Abstand die frühere); Tausch nur, wenn der Raum zur neuen Zeit frei ist, beide Lehrkräfte zur neuen Zeit einsetzbar sind und die andere Stunde einen passenden Raum zur alten Zeit findet. Beide Einträge Art „verlegung“, Hinweise „getauscht in die <n>. Stunde (<Grund>)“ bzw. „… getauscht mit <Fach>, weil <Grund>“.
Abnahme: Ist der einzige IT-Raum gesperrt, wird die Informatikstunde mit einer anderen Stunde der Klasse getauscht, beide Einträge „Verlegung“; ohne Tauschmöglichkeit erscheint der Ausweichraum mit Warnung; eine Raumsperre führt nie zu einem Entfall.

### VER-022 · Eintragsarten · P1 · Status: Ist
| Art | Bedeutung | zählt als Vertretung (Limits, Fairness) | zählt als Vertretungsfall der ursprünglichen Lehrkraft |
|---|---|---|---|
| vertretung | qualifizierte Vertretung | ja | ja |
| betreuung | fachfremde Betreuung | ja | ja |
| mitbetreuung | Mitbetreuung (Kopplung) | nein | ja |
| entfall | Unterricht entfällt | nein | ja |
| verlegung | Verlegung/Tausch (alte Position „moved“, neue „shifted“) | nein | nein |
| raumaenderung | nur Raumwechsel | nein | nein |
| klasse_abwesend | Klasse nicht da (Herkunft absence oder rhythm) | nein | nein |
| aufsicht | Pausenaufsicht (Ersatz) | nein | ja |
| klausur | Info-Eintrag zur Klausur | nein | nein |

- Einträge mit `dropped` zählen nicht. Ein „Vorschlag“ ist eine automatisch berechnete Vertretung/Betreuung ohne Handentscheidung (VER-027). Darstellung: je Art eine Farbfamilie (Vertretung, Betreuung, Entfall, Verlegung, Raum, Abwesend, Aufsicht, Klausur, Sonstiges), Hintergrund, Text und Rand in beiden Farbschemata, Art zusätzlich als Text (nie nur Farbe). „Mitbetreuung“ hat im Bestand keine Farbfamilie; der Neubau legt eine fest.
Abnahme: Ein Entfall zählt nicht gegen das Tageslimit der Vertretung, aber für den Vertretungsfall der ausgefallenen Lehrkraft; jede Art ist im Vertretungsplan farblich und per Text unterscheidbar, auch im dunklen Schema.

### VER-023 · Hinweistexte und Warnungen · P1 · Status: Ist
- Hinweise stehen in Klartext, gekürzt in der Tabelle (z. B. „für [Name] · Standortwechsel“; volle Fassung beim Darüberfahren/Antippen und im Druck). Wichtige feste Texte: „Entfall in der Tagesmitte – keine Vertretung gefunden“; „Keine Lehrkraft frei – Klausur ohne Aufsicht, bitte manuell regeln“; „Unterstufe ohne Betreuung, bitte manuell regeln“; „Block geteilt: keine Lehrkraft für beide Stunden frei“; „Betreuung (fachfremd)“; „Vertretung (manuell)“; „Unterricht entfällt (Grund) – …“; „Klasse abwesend: <Grund>“; „übernimmt <Kürzel>“; „verlegt in die <n>. Stunde“; „Raumänderung → <Raum>“; „Aufsicht für <Name> (<Grund der Wahl>)“; „Keine Lehrkraft für die Aufsicht frei – bitte manuell regeln“; „– Klausuraufsicht“.
- Warnungen ab vier Stück und Abwesenheiten sind auf der Seite eingeklappt; Warnungen werden pro Tag gezählt (Statistik `warnungen`). Auf schmalen Bildschirmen (800 px) bricht der Hinweis um und wird nicht abgeschnitten [offen im Bestand]. Singular/Plural stimmen („1 Hinweis“).
Abnahme: Der Hinweistext einer Vertretung zeigt in der Tabelle die Kurzfassung und beim Darüberfahren den vollen Text; im Druck steht der volle Text; bei 800 px ist nichts abgeschnitten.

### VER-024 · Statistik, Vertretungsfälle und Wochenhistorie · P1 · Status: Ist
- Statistik je Tag: Zähler je Eintragsart, `entfall_mitte` (Entfall mit Warnung), `warnungen`. Statistik je Lehrkraft im Zeitraum: Vertretungen (vertretung + betreuung + mitbetreuung), Vertretung je Art, Entfall eigener Stunden, Aufsichten gehalten (reguläre Pausenaufsichten), übernommene Aufsichten, „freigesetzt“ (Stunde entfällt durch abwesende Klasse oder `dropped`, Lehrkraft nicht abwesend — zählt nicht als Abwesenheit), verlegte Stunden, abwesende Stunden; Sortierung: meiste Vertretungen, dann meiste Aufsichten, dann Kennung.
- Vertretungshistorie für das Wochenlimit: Zählung je Lehrkraft für vertretung + betreuung (mitbetreuung zählt nicht) von Montag bis zum Vortag der laufenden Woche (nur Schultage). Ganztägige Abwesenheit: alle Stunden des Tages; Ausgabe ohne Grund (Name, Kürzel, Stunden oder ganztägig, Zahl der Vertretungsfälle).
- Rechte: `GET /substitutions/stats` für Personen mit `substitution.edit` vollständig; eine Lehrkraft sieht nur das eigene Konto. Anzeige als Statistikkarte auf der Vertretungsseite.
Abnahme: Lehrkraft mit 2 Vertretungen, 1 Mitbetreuung und 1 Entfall eigener Stunde zeigt Vertretungen = 3 und Entfall eigener Stunden = 1; Sortierung stimmt; das Wochenlimit zählt die Mitbetreuung nicht.

### VER-025 · Tagesübersicht je Ansicht · P1 · Status: Ist
- Je Ansicht (Klasse, Lehrkraft, Raum, Schüler/in) hat jede Zelle den Status normal · geaendert · entfall · neu. Verlegte Stunde: alte Position entfall „verlegt in die <n>. Stunde“, neue Position neu. Vertretung in der Ansicht der abwesenden Lehrkraft: entfall „übernimmt <Kürzel>“; in der Ansicht der Vertretungslehrkraft: neu. Raum-Ansicht: Zelle wird entfall mit „Raumänderung → <Raum>“, wenn der Raum wechselt. Klassen-Ansicht: ist die Klasse abwesend, wird jede Zelle (außer Aufsicht/Entfall) zu entfall mit „Klasse abwesend: <Grund>“.
- Kinder und Eltern sehen Ausfall, Vertretung und Raumänderung im eigenen Stundenplan (Test: Ausfall, Vertretung, Raumänderung erscheinen im Plan des Kindes), ohne Vertretungsplan; Vertretung im Stundenplan an derselben Stelle wie Klausuren: Rahmen in der Farbe der Eintragsart (Umsetzung im Raster nicht ausdrücklich bestätigt).
Abnahme: Fällt Lehrkraft X aus und Y übernimmt, zeigt X' Plan „übernimmt Y“ (entfall) und Y' Plan die Stunde als „neu“; ein Elternkonto sieht die Änderung im Kinderplan, aber nicht den Vertretungsplan.

### VER-026 · Kandidatenliste und Eintragsdetail · P1 · Status: Ist
- Im Eintragsdetail (Seitenpanel) werden alle Lehrkräfte für eine Einheit gerankt: frei zuerst, dann Punktzahl absteigend, dann Kennung; eine bisherige Vertretung wird vorher freigegeben und mitgezählt. Jeder Kandidat zeigt Punktzahl und Begründung (Fach, Springstunde, kennt die Klasse, gleicher Standort, Fairness); Ausgeschlossene nennen alle Gründe (VER-013). Auswahl erzeugt eine manuelle Entscheidung (VER-020). `GET /substitutions/candidates`, Recht `substitution.edit`.
- Neubau: Gründe erscheinen als Merkmale („Fachlehrkraft“, „kennt die Klasse“, „ohnehin im Haus“, „unter Soll“) statt einer nackten Punktzahl; die datumsgenaue Verfügbarkeit (LEH) wird beachtet.
Abnahme: Das Detail einer offenen Stunde listet freie Lehrkräfte zuerst; eine abwesende Lehrkraft steht mit Grund „abwesend“ unten; Auswahl einer Lehrkraft erzeugt eine Entscheidung „Vertretung (manuell)“.

### VER-027 · Bestätigungsmodus: Vorschläge freigeben · P1 · Status: Ist
- Schalter `substitution_confirm` (Standard aus; Planungs-Reiter „Vertretung & Abwesenheit“): Automatisch berechnete Vertretungen und Betreuungen gelten als Vorschlag; sie sind für Lehrkräfte, Schüler/innen, Eltern, Monitor, Kalender, Benachrichtigungen und offene Schnittstelle unsichtbar. Personen mit `substitution.edit` sehen sie mit der Markierung „Vorschlag“. „Freigeben“ bzw. „Alle freigeben“ (`POST /substitutions/release` mit Datum und optional Eintrags-Kennungen) macht sie zu manuellen Entscheidungen (Override `substitute` mit der vorgeschlagenen Lehrkraft); danach sind sie für alle sichtbar und lösen die üblichen Benachrichtigungen aus. Freigaben werden als Entscheidungen gespeichert und sind auditiert.
- Nicht betroffen: Entfall, Verlegung, Raumänderung, Mitbetreuung (Nachtrag 13.10.; ob Entfall/Verlegung ebenfalls freigabepflichtig sein sollen, ist offen). Das Freigabe-Recht ist `substitution.edit`.
Abnahme: Mit aktivem Modus sieht eine Lehrkraft eine neu berechnete Vertretung erst nach „Freigeben“; der Monitor zeigt sie vorher nicht; ein Planer sieht sie mit „Vorschlag“; ohne `substitution.edit` liefert `release` 403.

### VER-028 · Sofortige Umplanung, Mehrtägigkeit, Live-Aktualisierung · P1 · Status: Ist
- Eine Krankmeldung löst sofort die Verteilung der Vertretungen aus (Test: 4 Fälle bei einer Lehrkraft). Wird eine Vertretungslehrkraft ebenfalls krank, wird neu verteilt. Ist keine Vertretung möglich: „Entfall am Tagesende“. Mehrtägige Meldung: jeder Tag wird geplant. Pausenaufsichten werden bei Vertretung automatisch ersetzt.
- Änderungen laufen über das Ereignis `change` mit Bereich und betroffenen Daten an alle offenen Clients, die nur betroffene Tage/Listen neu laden. Vertretungspläne werden nur bei geänderter Grundlage neu berechnet (Befund: wegen eines Fehlers alle 5 s).
Abnahme: Nach der Krankmeldung einer Lehrkraft mit 4 Stunden zeigt ein zweiter offener Browser die 4 Einträge innerhalb weniger Sekunden ohne Neuladen; der zweite Krankheitsfall der Vertretung führt zu neuen Einträgen und keine Stunde bleibt der kranken Vertretung zugeordnet.

---
### 2.3 Darstellung, Sichtbarkeit, Benachrichtigung

### VER-029 · Seite „Vertretungsplan“ · P1 · Status: Ist
- Seite `/vertretung` für einen Tag oder Zeitraum: Tagesnavigation vor/zurück über Schultage (Ferien werden übersprungen), Datumsfeld, Suche. Oben nur Datum und Suche; Standort, Klasse, Lehrkraft und Sortierung stehen unter „Filter und Sortierung“ (eingeklappt, aktive Filter als Chips). Gruppierung nach Klasse (die Klassenzeile steht vorn), Sortierung nach Art in fester Reihenfolge.
- Tabelle farbig nach Eintragsart mit Art-Abzeichen und Hinweis-Spalte (gekürzt, VER-023); unter 600 px Kartenliste je Klasse. Warnungen (ab vier Stück) und Abwesenheiten sind eingeklappt; Karte „Abwesende Lehrkräfte“ (VER-032); Statistikkarte (VER-024); Eintragsdetail mit Kandidaten (VER-026); Abwesenheitsdialog mit Vorschau (VER-003). Leerzustand: „Keine Vertretungen“ mit Aktion „Abwesenheit erfassen“, kein Erklärabsatz. Der Hinweis für Lehrkräfte steht im Hilfe-Symbol. Texte sind kurz (Betreiber: „sehr sehr viel Text“).
- Tagesplan mit Vorschlägen (Bestätigungsmodus) zeigt für Personen mit `substitution.edit` die Markierung „Vorschlag“ (VER-027).
Abnahme: Die Seite zeigt beim Öffnen nur Datum und Suche; Filter sind eingeklappt; bei 390 px erscheinen Einträge als Karten je Klasse; ein Eintrag der Art „Entfall“ hat eine andere Farbfamilie und den Text „Entfall“ als Art-Abzeichen.

### VER-030 · Sichtbarkeit und Rechte der Vertretung · P0 · Status: Ist
| Aktion | Recht |
|---|---|
| Vertretungsplan lesen (Tag, Zeitraum) | `substitution.read` (Vorschläge zusätzlich `substitution.edit`) |
| Abwesenheiten lesen | `substitution.edit` | `plans.read_all` | `absence.report_self` (nur eigene) |
| Abwesenheit anlegen/ändern, Vorschau | `substitution.edit` |
| Selbstmeldung, eigene Meldung löschen | `absence.report_self` |
| Manuelle Entscheidungen, Kandidaten, Freigabe, Statistik | `substitution.edit` |
| Eigene Vertretungen heute/Woche | angemeldet |
| Monitordaten | `monitor.read` |
| Monitor-Konfiguration | `monitor.manage` |

- Der Vertretungsplan ist nur für Personal. Schüler/innen und Eltern haben weder Menüpunkt noch Startkachel noch Zugriff; ein direkter Aufruf liefert 403 mit einer Seite „Kein Zugriff“ im App-Rahmen (Befund: Serverfehler). Ihre Informationen kommen über den eigenen Stundenplan (STP-083, VER-025). Betreiber (12.10.): „der Vertretungsplaner muss nicht für die Kinder angezeigt werden. Da ist ja auch nichts, was die sehen sollten.“
- Fachlehrkräfte sehen Krankmeldungen von Schüler/innen nur nach Schulschalter `subject_teacher_absence_view` („none“ Standard; „presence“ = „fehlt heute in meiner Stunde“, ohne Grund). Fremde, vorhandene Datensätze liefern 404 (nicht 403).
- Die Rolle Schulbegleitung besitzt im Standard `substitution.read`; das ist auffällig und vom Betreiber zu bestätigen [offen]. Das Anzeigekonto „Zuschauer/in“ darf Vertretung, Räume, Pläne und Klausuren sehen.
Abnahme: Schülerkonto ruft `/vertretung` und die API auf → 403 und die Seite „Kein Zugriff“ mit Menü; Elternkonto: dasselbe; Lehrkraft sieht den Plan, aber nicht die Kandidatenliste (403); fremde Abwesenheits-Kennung → 404.

### VER-031 · Öffentliche Sicht auf abwesende Lehrkräfte (Datenminimierung) · P0 · Status: Ist
- Einstellung `public_absent_teachers`: „off“ (keine Lehrkräfte genannt), „short“ (Standard, nur Kürzel), „name“ (Kürzel und Name). Wirkt auf Monitor, Aushang, Druck und alle öffentlichen/Anzeige-Sichten. Gründe, Stunden und Fallzahlen werden dort nie angezeigt; die Schulleitung kann die Anzeige abschalten. Die Einstellung ist außenwirksam und in der Demo gesperrt.
- Rollen-, Standort- und öffentliche Sicht gelten auch für neu hinzukommende Felder: ein Test stellt sicher, dass Schüler/innen und Monitor keine Lehrkraft-Details ohne Freigabe erhalten.
- Datenminimierung: Die Anzeige am Standort listet abwesende Lehrkräfte öffentlich; Art und Umfang sind auf Kürzel (ggf. Name) begrenzt; kein Grund, keine Dauer außer „ganztägig/Stunden“ für Personal.
Abnahme: Mit „short“ zeigt der Monitor „MUE“, mit „name“ „MUE · Müller“, mit „off“ nichts; nie erscheint ein Grund; Test mit Monitor-Konto: die API-Antwort enthält die Felder Grund und Fallzahl nicht.

### VER-032 · Abwesende Lehrkräfte getrennt, keine „fehlenden Klassen“ · P0 · Status: Ist
- Der Tagesplan liefert `absent_teacher_details` (Kürzel, Name, Stunden oder „ganztägig“, Zahl der Vertretungsfälle, ohne Grund) und `absent_class_details` mit Herkunft `absence` | `rhythm`. Auf der Vertretungsseite zeigt eine eigene Karte „Abwesende Lehrkräfte“ eine Zeile je Person (Kürzel · Name · Stunden · Fälle); Klick filtert den Plan auf diese Lehrkraft. „Abwesende Klassen“ entfällt in Vertretungsplan und Druck (VER-005). Der Druck nutzt die öffentliche Sicht wie der Monitor.
- Betreiber-Pflichtanforderung A-56: abwesende Lehrkräfte getrennt, keine irreführende Liste „fehlender Klassen“.
Abnahme: Bei zwei kranken Lehrkräften zeigt die Karte zwei Zeilen mit Stunden und Fallzahl; die Seite enthält keine Karte „Abwesende Klassen“; die Druckansicht zeigt dieselbe Lehrkräfteliste ohne Grund.

### VER-033 · Druck und Aushang des Vertretungsplans · P0 · Status: offen
- Druckansicht (Aushang) des Vertretungsplans: öffentliche Sicht ohne Gründe; Bedienleiste wird nicht gedruckt; Kopfzeile; Option „eine Seite pro …“ [unklar: Einheit]; der volle Hinweistext erscheint im Druck; der Standort steht mit Namen statt Kürzel („S1“) [offen]. Der Aushang bleibt erhalten, obwohl der Stundenplan-Druck entfallen ist.
- Bestand: Die Druckansicht ist ohne Anmeldung erreichbar und der Papierausdruck unterliegt keinem Zugriffsschutz. Neubau: Aufruf der Druckansicht nur angemeldet mit `substitution.read` oder `monitor.read`; Inhalt wie öffentliche Sicht (VER-031). Betreiberentscheidung für anonymen Aushang-Zugang steht aus.
Abnahme: Aufruf der Druckansicht ohne Anmeldung → Weiterleitung zur Anmeldung; mit `substitution.read` erscheint die Druckansicht mit Kopfzeile, ohne Bedienleiste und ohne Gründe.

### VER-034 · Persönliche Sicht der Lehrkräfte und Familien · P1 · Status: Ist
- Lehrkräfte sehen eigene Vertretungen heute (`GET /me/today`) und in der Woche (`GET /me/week`, angemeldet); die Lehrkräfte-Startseite zeigt sie als Kachel. Wer eingeteilt wird, erhält eine Benachrichtigung (VER-036). `me/today` listet Nachschreibtermine noch nicht [offen]. Familien sehen die Woche je Kind mit Entfall, Vertretung und Raumänderung (STP-092).
Abnahme: Lehrkraft Y, die morgen zwei Stunden vertritt, sieht beide in „Heute“ bzw. „Woche“; Y erhält eine Benachrichtigung; eine andere Lehrkraft sieht Y's Einsätze nicht über diese Schnittstelle.

### VER-035 · Schultag-Navigation überall gleich · P2 · Status: offen
- Die Klassen-/Vertretungsansicht springt vor und zurück über Schultage und überspringt Ferien (16.10. → 02.11.). Die Kachel „Meine Tage“ der Lehrkräfte-Startseite springt nur über Wochentage (Abweichung): angleichen, sodass überall Ferien und freie Tage übersprungen werden. „Heute“ am Wochenende ist wirksam.
Abnahme: In allen Ansichten springt „nächster Schultag“ vom 16.10.2026 auf den 02.11.2026 (Herbstferien bis 31.10.).

### VER-036 · Benachrichtigung bei Änderungen · P1 · Status: offen
- Ziel: Wer eingeteilt wird oder betroffen ist, erfährt es. Kanäle: Glocke/Live-Hinweis in der App (Benachrichtigungszentrale, BEN), E-Mail (Vertretungs-Rundmail mit Abmeldelink, als automatische Mail gekennzeichnet) und Webhook. Webhook meldet Änderungen des Vertretungsplans an externe Programme (Schul-App, Infoscreen, Automatisierungsdienste); Einrichtung nur für Administration mit Bearbeitungsrecht, unter „Erweitert“ (Einstellung `webhooks`, Liste der Ziele); Zeitstempel im Kopf signiert; ein Testknopf mit fertigen Zielen fehlt [offen].
- Inhalt datensparsam: keine Gründe, keine Gesundheitsdaten, keine Namen anderer Personen; Push-Inhalte ohne Gesundheitsdaten (BEN). Im Bestand liegen Mail/Webhook im Klartext und die Outbox-Zeilen werden nie gelöscht; Neubau: Outbox-Inhalte verschlüsselt, Zeilen nach Zustellung/Frist gelöscht [unklar: Frist], Entscheidung zur Absicherung des Kanals durch den Betreiber. Im Bestätigungsmodus entstehen Benachrichtigungen erst nach der Freigabe (VER-027). [unklar: Auslöser und Empfänger im Bestand im Einzelnen.]
Abnahme: Eine neue Vertretung erzeugt für die eingeteilte Lehrkraft Glocke und (bei Einrichtung) E-Mail ohne Grund der Abwesenheit; die E-Mail enthält einen Abmeldelink und ist als automatisch gekennzeichnet; Webhook-Aufruf trägt eine Signatur und einen signierten Zeitstempel; nach der Frist ist die Outbox-Zeile gelöscht.

### VER-037 · Ausgabe der Vertretungen: iCal, Untis, Kanäle · P2 · Status: Ist
- iCal: Vertretungseinträge mit Art-Bezeichnung im persönlichen Kalender-Abo (STP-097). Untis (GPU-Export, Vertretungen nur Export): Zuordnung der Eintragsarten [unklar: Zuordnungswerte]. Nachrichten-Kanäle: Entfall- und Vertretungsarten werden in Kanälen unterschieden. Im Bestätigungsmodus erscheinen Vorschläge in keiner dieser Ausgaben.
- Nicht vorhanden: Landes-Exporte (NRW-Vertretungsabrechnung u. a.), siehe VER-076.
Abnahme: Eine freigegebene Vertretung erscheint im iCal-Feed der eingeteilten Lehrkraft mit der Bezeichnung der Eintragsart; eine nicht freigegebene nicht.

### VER-038 · Eintragsarten zentral definieren · P2 · Status: offen
- Der Neubau definiert jede Eintragsart an genau einer Stelle: Bezeichnung, Farbfamilie (hell/dunkel, Hintergrund/Text/Rand), Statistik-Zähler, Statusabbildung, iCal-Bezeichnung, Untis-Zuordnung, Kanal-Zuordnung und Abzeichen. Der Bestand pflegt eine neue Art an sechs Stellen. „Mitbetreuung“ erhält eine eigene Farbfamilie.
Abnahme: Das Hinzufügen einer Art „Aufsichtsersatz“ im zentralen Katalog erscheint ohne weitere Änderung in Statistik, Farbe, iCal und Abzeichen.

### VER-039 · Startseite: Kennzahlen und Kacheln der Vertretung · P1 · Status: offen
- Die Startseite zeigt die Kennzahl „Lehrkräfte abwesend“ (führt zur Karte auf der Vertretungsseite). Die Kennzahl „Klassen abwesend“ entfällt bzw. zählt nur gemeldete Klassenabwesenheiten; Start und Monitor nutzen den Wochentext und die 7-Tage-Hilfen wie der Vertretungsplan; abwesende Lehrkräfte wie dort. Befund: Start-Kennzahl und Monitor führen noch „Abwesende Klassen“ (Rest von A-56).
- Lehrkräfte-Startseite: eigene Vertretungen und Schnellmeldung (VER-004); Schulleitung: Vertretungsübersicht, Planvorschläge (STP-079).
Abnahme: Die Startseite der Schulleitung zeigt „Lehrkräfte abwesend: 3“ und keine Klassenzahl für Rhythmus-Klassen; Klick öffnet die Karte „Abwesende Lehrkräfte“.

### 2.4 Pausenaufsichten

### VER-040 · Aufsichtsplan: Grundsätze und Ablauf · P1 · Status: Ist
- Pausenaufsichten werden automatisch fair auf die Lehrkräfte verteilt; das Ergebnis ist ein fairer Plan, keine freie Wahl. Aufsichtsposten: Tag, Pause, Bereich (mit Standort); Varianten je Pause und Standort. Die Belastung je Lehrkraft fließt in die Verteilung ein; Aufsicht und eigener Unterricht dürfen sich nicht überschneiden. Der Aufsichtsplan wird bei jeder Plan-Übernahme neu berechnet (Schalter „Aufsichten neu berechnen“, Standard an, abwählbar) und kann gesondert erzeugt werden (`POST /duties/generate`).
- Betreiber (12.10.): „Ich verstehe überhaupt nicht wer wann welche Pause hat und wie und wo, welche Person, welcher Lehrer und ob die überhaupt an dem Standort sind.“ → Darstellung VER-049/VER-050.
Abnahme: Nach Übernahme eines Plans mit gesetztem Schalter liegen die Aufsichten neu vor; mit abgewähltem Schalter bleiben sie unverändert.

### VER-041 · Pausen und „echte“ Pausen · P1 · Status: Ist
- Pausen stammen aus dem Zeitraster (nach Stunde, Name, Minuten; STP-007). Nur relevante Pausen werden berücksichtigt: Pausen mit Unterricht in der Stunde davor oder danach am Standort des Bereichs. Pausen ohne Bezug (z. B. nach Abendunterricht ohne Unterricht am Standort davor/danach) bekommen keine Aufsicht. Der Pausenindex wird gegen die Zahl der Pausen geprüft.
Abnahme: Eine Pause, vor und nach der am Standort kein Unterricht stattfindet, erhält keine Aufsicht und erscheint nicht in der Übersicht.

### VER-042 · Datenmodell: Aufsicht (Dienst) · P1 · Status: Ist
- Aufsicht: Kennung „AU-<Bereich>-<Datum>-<Pause>-<Nummer>“, Bereich*, Tag*, Pause (Index)*, Lehrkraft (leer = offen), Wochen oder Rhythmus der Wochenmuster. Ist die Zuteilung über alle Wochenmuster gleich, gilt sie ohne Wochenangabe, sonst mit der Wochenangabe des Musters. Wochenmuster der Aufsichten = Gruppen realer Wochen mit gleichen Sperrzeiten der Lehrkräfte und gleichen Unterrichtsstunden. Pausenindex ungültig → Fehler.
Abnahme: Eine Aufsicht mit Pausenindex 9 bei 3 Pausen wird abgelehnt; gleiche Zuteilung in allen Mustern erzeugt eine Aufsicht ohne Wochenangabe.

### VER-043 · Aufsichtsbereiche · P1 · Status: Ist
- Bereich (Aufsichtsbereich): Kennung*, Name* (z. B. Schulhof, Mensa, Foyer Nord), Standort, Bedarf „benötigte Aufsichten je Pause“ `needed` (Standard 1 Lehrkraft; höhere Bedarfe werden zuerst besetzt, bei Gleichstand nach Kennung). Verwaltung der Bereiche (Pausenhöfe) mit Recht `duties.manage` bzw. `timetable.edit` [Rechte siehe VER-051].
Abnahme: Bereich „Schulhof“ mit `needed` 2 erzeugt je Pause zwei Aufsichten; ohne Angabe gilt 1.

### VER-044 · Erzeugung: Reihenfolge und Ausschlüsse · P1 · Status: Ist
- Reihenfolge: je Wochenmuster, je Schulöffnungstag, je Pause, je Bereich (höherer Bedarf zuerst, dann Kennung); je benötigter Aufsicht wird die beste Lehrkraft gewählt.
- Harte Ausschlüsse: Lehrkraft in dieser Pause schon eingeteilt; Standort nicht in ihren Standorten; Sperrzeit direkt vor oder nach der Pause; an dem Tag nicht im Haus; direkt vor oder nach der Pause Unterricht an einem anderen Standort als dem Bereich. Ist niemand frei, bleibt die Aufsicht unbesetzt (Lehrkraft leer).
Abnahme: Eine Lehrkraft mit Unterricht an Standort B in der Stunde vor der Pause wird für einen Bereich an Standort A nicht eingeteilt; ohne freie Lehrkraft bleibt die Aufsicht offen.

### VER-045 · Bewertung der Lehrkräfte für Aufsichten · P2 · Status: Ist
Niedrigster Wert gewinnt; Gleichstand: Kennung.

| Merkmal | Punkte |
|---|---|
| Bereits eine Aufsicht an diesem Tag (je Aufsicht) | +40 |
| Auslastung relativ zum Deputat (je bereits zugeteilter Aufsicht) | +10 × Auslastung / (Deputat / 25) [unklar: Einheit der Auslastung] |
| Lage zum Unterricht: direkt vor/nach der Pause = 0; zwischen erster und letzter Stunde im Haus = 1; sonst 2 | +4 × Lage |
| Gleiche Lehrkraft wie in der Vorvariante | −3 |
| Überschreitung der Richtlinie von höchstens 3 Aufsichten je Lehrkraft und Woche | +1000 (nur wenn sonst niemand kann) |

- Deputat-Gewicht je Lehrkraft = max(1; Deputat) / 25 (Standard-Deputat 25 Stunden je Woche).
Abnahme: Zwei Kandidaten: A hat Unterricht direkt vor der Pause und keine Aufsicht heute (Wert 0), B ist im Haus (4) und hat heute schon eine Aufsicht (40 + 4); A wird gewählt.

### VER-046 · Last je Lehrkraft und Obergrenze · P2 · Status: Ist
- Richtwert: höchstens 3 Pausenaufsichten je Lehrkraft und Woche (weich; Überschreitung nur, wenn sonst niemand kann). Last je Lehrkraft = Anzahl Aufsichten je Woche, über die Wochen des Schuljahres gemittelt (Aufsicht mit Wochen- oder Rhythmusangabe: Anteil der Schulwochen; sonst 1 je Woche); die Lastobergrenze nutzt die Wochenmuster-Gewichte. Soll-Werte je Lehrkraft und Ausnahmen (einzelne Lehrkräfte ausnehmen) sind nicht umgesetzt [VER-052].
Abnahme: Eine Lehrkraft mit Aufsichten nur in jeder zweiten Woche zählt 0,5 je Woche für diese Aufsicht; die 4. Aufsicht in einer Woche wird nur vergeben, wenn niemand sonst frei ist.

### VER-047 · Konflikt, Vertretung und manuelle Entscheidung bei Aufsichten · P0 · Status: Ist
- Konflikt der eingeteilten Lehrkraft (Grund steht im Eintrag): (1) „abwesend“ — fehlt in der Stunde vor oder nach der Pause; (2) „wechselt direkt vor/nach der Pause den Standort“; (3) „an dem Tag nicht am Standort der Aufsicht“. Eine Lehrkraft ohne Unterricht an dem Tag gilt NICHT als Konflikt; sie kommt eigens (Hinweis „kommt eigens“, keine automatische Ersatzsuche). Die Aufsicht wird vertreten, wenn die Lehrkraft fehlt (nicht eingetragen oder unbekannt) oder ein Konflikt besteht; Ausnahme: manuelle Entscheidung.
- Kandidaten werden ausgeschlossen: die ursprüngliche Lehrkraft; schon Aufsicht in dieser Pause; abwesend in der Stunde vor oder nach der Pause; dort gesperrt; Standort nicht eingesetzt; Standortwechsel direkt davor/danach. Rang (× 10 Punkte): 0 Unterricht direkt vor/nach der Pause, 1 ohnehin im Haus (zwischen erster und letzter Stunde), 3 müsste früher kommen oder länger bleiben, 6 müsste extra kommen. Bewertung = Rang × 10 + 25 × Aufsichtsersätze dieser Lehrkraft heute + 4 × Vertretungen heute + 6 × Auslastung × 25 / max(5; Deputat); niedrigster Wert gewinnt, Gleichstand Kennung. Der Aufsichtsersatz schließt gesperrte Nachbarstunden aus.
- Eintrag: Art „aufsicht“, Hinweis „Aufsicht für <Name> (<Grund der Wahl>)“ und ggf. Konflikt; Felder Kennung, Bereich, Pause, Standort, Zeit. Keine Lehrkraft frei: Warnung „Keine Lehrkraft für die Aufsicht frei – bitte manuell regeln“ (+ Grund). Manuelle Entscheidungen: `keep` (nur wenn kein Konflikt), `cancel` („Aufsicht entfällt (manuell)“), `substitute` („Aufsichtsvertretung (manuell)“).
- Eine Pausenaufsicht abwesender Lehrkräfte wird bei der Krankmeldung automatisch ersetzt (VER-028).
Abnahme: Wird die eingeteilte Lehrkraft krank, steht in der Aufsicht „abwesend“ und ein Ersatz mit Begründung; bei Standortwechsel direkt vor der Pause ebenso; Lehrkraft ohne Unterricht erhält „kommt eigens“ ohne Ersatzsuche; ein `cancel` ergibt „Aufsicht entfällt (manuell)“.

### VER-048 · Standortcheck der Aufsichten · P1 · Status: Ist
- Markiert Lehrkräfte, die krank sind, direkt vor/nach der Pause den Standort wechseln oder nicht am Standort sind, und sucht automatisch eine Vertretung (VER-047). Badges: „heute Hauptstandort“, „wechselt“, krank; Zähler für offene Plätze, Vertretungen, Konflikte. Betreiber (12.10.): „Das muss auch getrackt werden an welchem Standort die sind.“
Abnahme: Die Übersicht zeigt für eine Lehrkraft, die zwischen den Standorten wechselt, das Abzeichen „wechselt“; der Zähler „Konflikte“ entspricht der Zahl markierter Aufsichten.

### VER-049 · Aufsichts-Übersicht (Wochenansicht) und Status · P1 · Status: Ist
- Je Schultag der Woche, je Pause (nur Pausen mit Aufsicht oder mit Unterrichtsbezug am Standort), je Bereich: Liste der Aufsichten mit Status ok · konflikt · vertreten · offen · hinweis (kein Unterricht an dem Tag, kommt eigens). Fehlend = max(0; Bedarf − besetzte Aufsichten (ok oder vertreten)). Bestehende Einteilungen in anderen Pausen bleiben sichtbar. Status mit Text und Abzeichen, nie nur Farbe.
- Darstellung im gemeinsamen Raster (STP-094): Pause × Bereich gegen Tage, Standort je Bereich, Namen ausgeschrieben, Vertretung mit durchgestrichener Person. Handy: Tagesansicht als Karten je Pause, nach Standort gruppiert (statt Raster mit rund 110 Knöpfen). Filter nach Standort und „nur meine“. `GET /duties/overview` (angemeldet; Details `timetable.edit` | `substitution.edit`).
Abnahme: Die Wochenansicht zeigt für Mensa, Schulhof, Foyer Nord je Pause die Namen; eine vertretene Aufsicht zeigt die ursprüngliche Person durchgestrichen und die Vertretung; am Handy erscheinen Karten je Pause.

### VER-050 · Aufsichten: Oberfläche und „Meine Aufsichten“ · P1 · Status: Ist
- Seite `/aufsichten`: Wochenansicht, Tagesansicht, Übersicht Tag → Pause → Standort → Bereich → Namen, zusätzlich je Lehrkraft die Aufsichten des Tages, Zählwerte je Status. „Meine Aufsichten“ für Lehrkräfte. Dialog zum Bearbeiten einer Aufsicht. Das Entfernen einer Aufsicht verlangt eine Rückfrage im App-Dialog (Befund: ohne Rückfrage). Namens-Sprechblasen für Kürzel (STP-091).
- Betreiber (12.10.): Pausenaufsicht als Raster wie der Stundenplan; Pausenhöfe mit Rasteransicht und Standortwechsel-Hinweis.
Abnahme: Entfernen einer Aufsicht fragt nach; „Meine Aufsichten“ listet nur eigene; die Seite zeigt Zähler „offene Plätze“, „Vertretungen“, „Konflikte“.

### VER-051 · Rechte der Aufsichten · P0 · Status: offen
- Ist: Erzeugen (`POST /duties/generate`) mit `timetable.edit`; Übersicht für Angemeldete; Details mit `timetable.edit` | `substitution.edit`; die Rechte der Aufsichtsseiten sind im Bestand nicht einheitlich belegt. Das Recht `duties.manage` (Pausenbereiche, Verfügbarkeit der Lehrkräfte, faire Verteilung) ist im Katalog als „geplant“ geführt.
- Neubau: Aufsichten erzeugen, Bereiche verwalten und Aufsichten bearbeiten mit `duties.manage` (oder `timetable.edit`); Lesen der eigenen Aufsichten für alle Lehrkräfte; Aufsichtspläne und Belastung sind personenbezogen, Sichtbarkeit nach Rolle (Lehrkraft: eigene und Gesamtübersicht ohne Gründe).
Abnahme: Lehrkraft ohne `duties.manage` kann Aufsichten ansehen, aber nicht erzeugen (403); Planer kann erzeugen und Bereiche pflegen.

### VER-052 · Aufsichten: noch nicht gebaute Wünsche · P3 · Status: offen
- Soll-Anzahl Aufsichten je Lehrkraft und Ausnahmen einzelner Lehrkräfte; manueller Lehrervorschlag je Platz mit Korrekturlauf und Löschen aller Aufsichten; Verwaltung der Pausenhöfe und Hinweis beim Standortwechsel als eigener Bereich; Pausenaufsicht online im Plan der Lehrkraft; Nacharbeit-Aufsichten (zentrale Termine, Aufsicht erfasst Fehlen) [Vergleichsfunktion]. GPU-Dateien 008/009 (Lehrerqualifikation, Pausenaufsicht) fehlen.
Abnahme: Für Lehrkraft X lässt sich eine Soll-Anzahl 1 je Woche festlegen und der Generator hält sie ein; ein Lehrervorschlag je Platz zeigt die geeigneten Lehrkräfte.

---
### 2.5 Monitore und Bildschirmanzeige

### VER-053 · Monitor-Anzeige (Vollbild, je Standort) · P1 · Status: Ist
- Route `/monitor/:standort?` zeigt den Vertretungsplan im Vollbild, optional nur für einen Standort. Bestandteile: Uhr (aktualisiert jede Sekunde, als eigener Baustein, damit die Seite nicht jede Sekunde neu gezeichnet wird); Tagesspalten mit automatischem Scrollen [unklar: Geschwindigkeit/Intervall]; Aushang-Hinweis oben und Mitteilungsband (Laufband) unten, wichtige Mitteilungen hervorgehoben; Liste der abwesenden Lehrkräfte nach VER-031; Standortwahl und Menü (VER-058); Leerzustand, wenn nichts anzuzeigen ist; Angabe „Stand: 07:42“ und Hervorhebung der laufenden Stunde; Anzahl der Tage per Adresse `?tage=1..5`.
- Der Monitor zeigt keine Namens-Sprechblasen (er scrollt selbst). Es erscheint keine Zeile „Nicht im Haus: …“ (VER-005). Vertretungen im Bestätigungsmodus erscheinen erst nach Freigabe (VER-027).
Abnahme: `/monitor/Hauptgebäude?tage=2` zeigt zwei Tagesspalten, die laufende Stunde hervorgehoben und „Stand: HH:MM“; ohne Einträge erscheint ein Leerzustand; eine neu freigegebene Vertretung erscheint ohne Neuladen.

### VER-054 · Datenumfang und Schutz der Anzeige · P0 · Status: offen
- Die Monitor-Seite lässt sich im Frontend ohne Anmeldung aufrufen; die Daten liefert nur ein Konto der Rolle Monitor (Anzeigerolle, `monitor.read`) bzw. ein Konto mit `monitor.read`. Die Anzeige sieht ausschließlich öffentliche Sicht (VER-031), Mitteilungen mit Monitor-Kennzeichen, Uhr und Vertretungsplan; Routen mit Atteste, Förderkennzeichen, Eltern-Kontakten und Benachrichtigungs-Ausgang bleiben für Anzeigerollen mit 403 gesperrt, solange nicht ausdrücklich ein Recht erteilt wird. Bei der Formular-Übersicht wird der Monitor abgewiesen (sieht keinen Zähler, keine Fehlermeldung).
- Im Bestand ist die Anzeigerolle „Monitor“ nicht schreibgeschützt; Neubau: Monitor-Konten haben ausschließlich Lesezugriff (zusätzlich Abmelden, Konto-/Standortwechsel im Menü, VER-058). Wie sich ein Monitor-Gerät ohne Konto authentifiziert, ist im Bestand nicht beschrieben (VER-059).
Abnahme: Ein Monitor-Konto, das die Abwesenheiten-Liste oder Atteste aufruft, erhält 403; ein Schreibversuch (z. B. neue Abwesenheit) als Monitor-Konto liefert 403; die Antwort der Monitor-Daten enthält weder Grund noch Gesundheitsdaten.

### VER-055 · Monitor ruhig und mobil · P1 · Status: offen
- Unter 48 em Breite oder bei Touch: nativer Bildlauf statt Auto-Scroll, eine Spalte, Tage als Umschalter „Heute · Morgen“, Einträge als Karten je Klasse; bei 375 px keine abgeschnittenen Spalten; `100dvh`, umbrechende Kopfzeile, Vollbild-Knopf am Handy ausgeblendet. Die Höhe passt sich der sichtbaren Fläche an (nicht der Fensterhöhe). Das Laufband ist bei „Bewegung reduzieren“ eine statische Liste; Animationen laufen höchstens einmal. Der Hinweistext bricht bei schmalen Bildschirmen um und wird nicht abgeschnitten.
- Betreiberwunsch A-62: Monitor modular und mobil. Bestand: am Handy abgeschnitten, ganze Seite zeichnet jede Sekunde neu.
Abnahme: Bei 375 px zeigt der Monitor eine Spalte mit „Heute · Morgen“ ohne waagerechten Bildlauf; bei „Bewegung reduzieren“ steht das Laufband als Liste; die Tagesspalten werden nicht jede Sekunde neu gerendert.

### VER-056 · Monitor-Verwaltung („Monitore einstellen“) · P1 · Status: Ist
- Seite `/monitore` (Recht `monitor.manage`: Administration, Schulleitung, Sekretariat): je Monitor/Standort eine Karte mit Einstellungen — Aushang-Hinweis oben, Laufband (Ticker) unten, Anzeigetage, Darstellung [unklar: vollständige Feldliste]. Schlüssel leer = alle Standorte. Die Einstellungen liegen im Planungsdokument (`monitors`). `GET /monitor/config` (alle Standorte) und `PUT /monitor/config/{standort}`; jede Änderung wird auditiert. Ein Monitor-Konto kann an einen Standort gebunden werden (dann zeigt es nur diesen).
Abnahme: Speichern des Laufbands für Standort „S2“ ändert nur dessen Anzeige; ohne `monitor.manage` 403; ein an S2 gebundenes Konto sieht nur S2.

### VER-057 · Monitor-Konto und Standortbindung · P1 · Status: Ist
- Monitor-Konto: Rolle Monitor (`monitor.read`), optional mit festem Standort. Mit festem Standort bleibt das Konto dort; ohne festen Standort darf der Standort in der Anzeige gewechselt werden (Betreiber: „andere Schul ansich“; für Monitor-Konten mit festem Standort gibt es keine andere Schulansicht; ob das genügt, ist offen). Sitzung: Leerlauf 10080 min (7 Tage), absolute Dauer 30 Tage (danach Neuanmeldung, siehe VER-059). Demo-Konto „Monitor“ nur außerhalb der Produktion.
Abnahme: Ein Konto mit festem Standort S1 kann im Menü keinen anderen Standort wählen; ein Konto ohne festen Standort schon.

### VER-058 · Monitor-Menü: Ausgang, Kontowechsel, Abmelden · P1 · Status: offen
- Betreiberbefund (17.10.): „ich habe keine option aus dem monitor ding heraus zu gehen ich kann mich nicht abmelden andere schul ansichten etc“. Umgesetzt: Menü-Knopf (☰) oben rechts neben der Uhr; Inhalt: Konto wechseln, weiteres Konto anmelden, Abmelden (mit Bestätigung im App-Dialog), Standort wechseln (nur ohne festen Standort), Zurück zur Startseite (nur wenn mit einem normalen Konto geöffnet). Lokal getestet (Menü öffnet sich, Abmelden führt zur Anmeldeseite), auf den Servern seit 15:59.
- Der Knopf ist im Bestand bewusst kaum sichtbar und wird erst beim Darüberfahren deutlich; das ist eine Entscheidung des Entwicklers, vom Betreiber nicht bestätigt und widerspricht Auffindbarkeit und Barrierefreiheit. Neubau-Mindestanforderung bis zur Entscheidung: per Tastatur erreichbar, bei Fokus und Berührung deutlich sichtbar (Fokusrahmen 2 px, Kontrast des Bedienelements mindestens 3:1), Name für Bildschirmleser („Menü“).
Abnahme: Mit Tab ist der Menü-Knopf erreichbar und zeigt einen sichtbaren Fokusrahmen; „Abmelden“ fragt nach und führt zur Anmeldeseite; der Betreiber bestätigt die endgültige Gestaltung des Knopfes (Eintrag in dieser Datei).

### VER-059 · Monitor-Geräte dauerhaft angemeldet (Geräte-Token) · P1 · Status: offen
- Monitor-Geräte bleiben über ein widerrufbares Geräte-Token angemeldet, statt nach 30 Tagen abgemeldet zu werden (Backlog B-28). Das Token wird nur gehasht gespeichert (Cookie HttpOnly, Secure, SameSite=Strict), ist unter „Meine Geräte“ bzw. in der Monitor-Verwaltung einsehbar und widerrufbar; kein Fingerprinting. Ein widerrufenes Gerät zeigt die Anmeldeseite.
Abnahme: Ein Monitor-Gerät bleibt nach 45 Tagen angemeldet; nach Widerruf des Tokens liefert der nächste Abruf 401 und die Anzeige wechselt zur Anmeldung.

### VER-060 · Monitor-Profile und Kacheln (modular) · P2 · Status: offen
- Jeder Bildschirm (Aula, Lehrerzimmer, zweiter Standort) bekommt sein eigenes Layout (Backlog B-28/B-33): Tabelle `monitor_profiles` (Name, Standort, Kacheln, Optionen, zugeordnete Monitor-Konten), `GET/POST/PUT/DELETE /monitor/profiles` mit `monitor.manage`; Kacheltypen per Positivliste: Tagesplan, abwesende Lehrkräfte, Mitteilungen, Uhr, laufende Stunde, Klausuren, Raumänderungen, Termine. `GET /monitor?profile=` liefert die zu den Kacheln passenden Daten (Tage aus dem größten Versatz, höchstens fünf); ohne Profil bleibt die Antwort wie heute. `/monitor/p/:profil` zeigt ein Profil; `/monitor/:standort` funktioniert weiter.
- „Monitor einrichten“: Kacheln hinzufügen, entfernen, anordnen, in der Größe ändern; Vorschau mit Beispieldaten; Auswahlfelder statt Schieberegler (Bildlauf langsam/normal/schnell, Schriftgröße, Folgetag ab Uhrzeit). Tagesplan-Kachel: heute oder morgen, gruppiert nach Klasse oder Stunde, Spaltenauswahl; Kacheln passen sich der Breite an (Tabelle ab 48 em, darunter Karten). Vergleichswunsch: eigene Texte, Dateien, eingebettete Webseiten, Tabellen-/Kachelansicht.
Abnahme: Zwei Monitore (Aula, Lehrerzimmer) mit verschiedenen Profilen zeigen gleichzeitig ihre Kacheln; eine Kachel mit unbekanntem Typ wird abgelehnt (422); ohne `monitor.manage` 403.

### VER-061 · Mitteilungen auf dem Monitor (Aushang und Laufband) · P2 · Status: Ist
- Der Monitor zeigt oben einen kurzen Hinweis (Aushang) und unten das Laufband mit Mitteilungen; Mitteilungen aus dem Schwarzen Brett mit Zielgruppe, Rollen, Standort und Kennzeichen „Monitor“; wichtige Mitteilungen sind hervorgehoben. Gepflegt werden Hinweis und Laufband in der Monitor-Verwaltung (VER-056). [unklar: Zeitraum/Priorität im Einzelnen.]
Abnahme: Eine Mitteilung mit Kennzeichen „Monitor“ und Standort S1 erscheint im Laufband von S1, nicht auf S2; eine als wichtig markierte ist hervorgehoben.

### VER-062 · Aktualisierung und Fehlerzustände der Anzeige · P2 · Status: offen
- Änderungen erreichen die Anzeige live über den Ereignisstrom (VER-028); die Anzeige lädt nur die betroffenen Tage nach. Bricht die Verbindung ab, bleibt der letzte Stand sichtbar und die Angabe „Stand: HH:MM“ macht das Alter erkennbar (Neubau-Festlegung zur Verlässlichkeit); nach Wiederverbindung wird automatisch neu geladen. [unklar: Aktualisierungsintervall des Bestands.]
Abnahme: Nach Trennen und Wiederherstellen der Verbindung zeigt der Monitor wieder den aktuellen Stand und die Stand-Angabe springt auf die neue Zeit.

### 2.6 Klausuren, Klassenarbeiten und Nachschreibtermine

### VER-063 · Klausuren: Grundregeln und Prüfung beim Speichern · P0 · Status: Ist
- Klausur = Termin eines Kurses an einem Datum mit Start (Stunde, 0-basiert), Länge (Stunden, Standard 1, mindestens 1), optional Kursteil, Raum (wird aus der Stunde übernommen), Titel (Standard „Klausur“), Art `klausur` oder `test` (angekündigter Test). Klausuren finden in regulären Unterrichtsstunden des Kurses statt. Vor dem Speichern eine eigene Prüfung (`POST /exams/check`, Recht `exam.edit`); Anlegen, Ändern, Löschen: `exam.edit` (Umfang: eigene Kurse); Liste: angemeldet.
- Eine Klausur wird abgelehnt (Liste der Gründe), wenn: (1) Kurs existiert nicht („Kurs <Id> existiert nicht“); (2) Kursteil existiert nicht („Kursteil <n> existiert in <Kurs> nicht“); (3) Datum ungültig; (4) kein Unterrichtstag der Klassen des Kurses („Kein Unterrichtstag der Klasse.“; Samstag/Sonntag erlaubt, wenn Unterrichtstag einer Klasse); (5) Ferien oder Feiertag („ist kein Schultag (<Name>)“); (6) außerhalb des Zeitrasters (Start < 0 oder Start + Länge > Stunden je Tag); (7) der Kurs hat in dieser Stunde laut Stundenplan keinen Unterricht („<Kurs> hat am <Wochentag>, <Datum> in der <n>. Stunde laut Stundenplan keinen Unterricht“; alle Stunden der Klausur werden geprüft); (8) Klasse ist in der Stunde nicht da (Abwesenheit oder Rhythmus, Grund genannt); (9) Höchstzahl je Klasse und Tag überschritten; (10) Höchstzahl je Klasse und Woche überschritten (VER-064); (11) Raum durch eine andere Klausur am selben Tag mit überlappenden Stunden belegt („Raum <Raum> ist bereits durch Klausur <Titel> belegt“).
- Konflikte und Regelverletzungen werden vor dem Speichern angezeigt. Lehrkräfte dürfen Regelverletzungen nicht erzwingen (`force`-Verbot).
Abnahme: Klausur am Samstag für eine Klasse ohne Samstagsunterricht → Grund 4; zwei Klausuren im selben Raum mit überlappenden Stunden → Grund 11; Klausur in einer Stunde ohne Kursunterricht → Grund 7 mit dem genannten Text; Lehrkraft versucht `force` → 403.

### VER-064 · Prüfung gegen Höchstzahlen · P1 · Status: Ist
- Höchstzahlen und Vererbung (Schule → Jahrgang → Klasse) siehe STP-061. Prüfung: Anzahl anderer Klausuren derselben Klasse am selben Tag ≥ Tageshöchstzahl → abgelehnt; Anzahl anderer Klausuren derselben Klasse in derselben Woche (Montag–Sonntag) ≥ Wochenhöchstzahl → abgelehnt; die Höchstzahl entspricht der Zahl der Klausuren einschließlich der neuen. Ein anderer Kursteil desselben Kurses am selben Tag zählt als dieselbe Klausur. Angekündigte Tests (Art `test`) zählen nicht und werden nicht gegen die Höchstzahlen geprüft.
- Anzeige: „max. <Woche> je Woche, <Tag> je Tag (<Quelle>)“, Quelle „Schule“, „Jahrgang“, „Klasse“ (gemischt: „Woche: <Quelle>, Tag: <Quelle>“). Neubau: der Wert 0 bedeutet „keine Grenze“ (STP-061).
Abnahme: Klasse mit Höchstzahl 1 je Tag und bereits einer Klausur am Dienstag: die zweite wird mit der Quelle der Grenze abgelehnt; ein Test am selben Tag wird zugelassen; mit Tageshöchstzahl 0 werden beliebig viele Klausuren zugelassen.

### VER-065 · Klausuren in Ansichten, Kalender und Kanälen · P1 · Status: Ist
- Abfragen im Zeitraum für Ansicht Klasse, Lehrkraft (Kursteil mit dieser Lehrkraft), Raum, Schüler/in (Klasse + gewählte Kursteile), Kurs oder alle. Ausgabefelder je Klausur: Kennung, Kurs, Datum, Wochentag, Woche (Anzeigetext), Start, Länge, Stundenbezeichnung, Beginn, Titel, Kursteil, Raum, Klassen, Fächer, Lehrkräfte, Bezeichnung; Sortierung nach Datum, Start, Kennung. Klausur-Hinweise erscheinen in der Kalenderwoche und als Markierungen im Kalender; die Klausur wird in den verknüpften Klassenkanälen angezeigt.
- Seite „Klausuren“: Liste nach Tagen mit Link zum Stundenplan; Dialog anlegen/ändern mit Prüfung; Detailansicht mit Raum, Zeit, Kanälen; Vorgaben der Höchstzahlen (STP-061). Darstellung im Stundenplan siehe STP-086.
Abnahme: Die Lehrkraft-Ansicht listet nur Klausuren ihrer Kursteile; die Schüler-Ansicht nur der eigenen Klasse und gewählten Kursteile; der Kalender zeigt die Klausur als Markierung.

### VER-066 · Klausuren: Datenwege, Referenzen, Rechte · P0 · Status: offen
- Die Klausurregeln gelten auf jedem Datenweg: Der generische Datenweg für Klausuren läuft durch dieselbe Prüfung wie die Klausur-Schnittstelle (Schultag, Höchstzahlen, Kursunterricht) und hat dasselbe `force`-Verbot (Befund: er prüfte nur Formfehler und umging die Regeln). Rollenvergleiche im Frontend sind nur Komfort; der Server entscheidet.
- Referenzen: Klausuren verweisen auf Stunden, Klassen, Lehrkräfte, Räume und Kanäle; beim Löschen von Fach, Klasse oder Raum werden diese Verweise gepflegt. Die Sichtbarkeit der Klausur-Kanäle für Eltern und Schüler/innen ist zu klären [unklar]. Nachteilsausgleich wird in der Klausurstunde ohne Diagnose angezeigt („NTA n“). Schreibende Aktionen sind auditiert.
Abnahme: Eine Klausur über den generischen Datenweg an einem Ferientag wird mit denselben Gründen abgelehnt wie über die Klausur-Schnittstelle; Löschen eines Raums entfernt oder meldet Klausuren, die ihn verwenden.

---
### VER-067 · Nachschreib-Fälle: Entstehen, Abgleich, Status · P1 · Status: Ist
- Auslöser: Eine Schülerin oder ein Schüler hat eine Klausur oder einen Test wegen Krankheit oder Fehlens verpasst. Je verpasster Klausur und Person entsteht eine Zeile (eindeutig je Klausur und Person) mit Klausur, Person, Kurs, Klausurdatum, Herkunft, Verweis auf die Fehlzeit, Status, Termin, Attest-Verzicht (ja/nein) mit Name, Bearbeiter (Name). Voraussetzung: Fehlzeit der Art „krank“ oder „fehlt“, das Klausurdatum liegt in der Fehlzeit, die Stunden der Fehlzeit überschneiden die Klausurstunden (leere Stundenliste = ganztägig) und die Person schreibt die Klausur (Kursteil berücksichtigt).
- Status: `offen` („Termin offen“) → `angesetzt` („Termin festgelegt“) → `erledigt` („nachgeschrieben“) oder `entfallen` („entfällt“). Herkunft: `krank` („krank gemeldet“), `fehlt` („im Klassenbuch als gefehlt eingetragen“).
- Der Abgleich läuft automatisch nach jeder Änderung an Fehlzeiten, nach Klausuränderungen und beim Lesen und lässt sich manuell neu auslösen. Eine Zeile wird entfernt, wenn die Klausur gelöscht ist (unabhängig vom Status) oder wenn die Fehlzeit nicht mehr zutrifft und die Zeile noch „offen“ ist; festgelegte oder erledigte Zeilen bleiben, solange die Klausur besteht. Eine bestehende offene Zeile erhält bei neuer Fehlzeit deren Kennung.
- Tabellen: `exam_makeup_dates` (Klausur-Kennung, Datum, Startstunde, Länge in Stunden, Standard 1, Raum, Notiz, Anleger) und `exam_makeups` (Zeile je Person). Der Fall kann als erledigt markiert und ein Attest-Verzicht gesetzt werden (`PATCH /exam-makeups/{id}`).
Abnahme: Eine krank gemeldete Schülerin, die am Klausurtag fehlt, erhält automatisch die Zeile „Termin offen“ mit Herkunft „krank gemeldet“; wird die Krankmeldung zurückgenommen, verschwindet die offene Zeile; eine bereits „festgelegte“ Zeile bleibt; Löschen der Klausur entfernt alle ihre Zeilen.

### VER-068 · Attest-Zustand der Nachschreibfälle (abgeleitet) · P1 · Status: Ist
Der Zustand wird nicht gespeichert, sondern aus den Dokumenten der Kategorie „Attest“ (nicht zurückgezogen) zu den Fehlzeiten abgeleitet, die den Klausurtag abdecken. Vorrang (erste zutreffende Regel):

| Nr. | Bedingung | Zustand | Anzeige | Fehlt? |
|---|---|---|---|---|
| 1 | Attest-Verzicht gesetzt | nicht_noetig | Attest nicht erforderlich | nein |
| 2 | mindestens ein Attest „geprüft“ | genehmigt | Attest genehmigt | nein |
| 3 | mindestens ein Attest „eingegangen“ | eingereicht | Attest eingereicht (wird geprüft) | nein |
| 4 | mindestens ein Attest „abgelehnt“ | abgelehnt | Attest abgelehnt – neues Attest nötig | ja |
| 5 | sonst | fehlt | Attest fehlt | ja |

- Den Verzicht setzen Klassenleitung, Sekretariat oder Schulleitung, nicht die Person selbst. Die Attestpflicht allgemein (ab `sick_note_after_days` Fehltagen, Standard 3 Schultage, Bereich 0–60) ist Teil von KLB.
Abnahme: Ein Fall mit einem Attest „eingegangen“ und einem „abgelehnt“ zeigt „Attest eingereicht (wird geprüft)“; mit gesetztem Verzicht „Attest nicht erforderlich“; ohne Dokument „Attest fehlt“.

### VER-069 · Sichtbarkeit und Datenschutz der Nachschreibfälle · P0 · Status: Ist
| Stufe | Wer | Sichtbar |
|---|---|---|
| voll | Klassenleitung, Sekretariat, Schulleitung | alles: Quelle der Fehlzeit, Attest verwalten, Verzicht setzen |
| Familie | Person selbst bzw. Eltern (Volljährige nur mit Freigabe) | eigene Zeile, Termin und Attest-Stand |
| Lehrkraft | Lehrkraft der Klausur mit `exam.edit` (nur eigene Kurse) | nur „abwesend“, Termin und Attest-Stand; nie Grund oder Dokument |
| Administration | technische Administration | kein Zugriff |

- Verpasste Klausur wegen Krankheit und Attest haben Gesundheitsbezug (besondere Kategorie): Zugriff nur für zuständige Rollen, nie in der öffentlichen Schnittstelle. Seite `/nachschreiben`: `exam.edit` | `student_absence.read`. Nachschreibtermine sind für Angemeldete nach Rolle sichtbar; Schüler/innen-Sicht [unklar]. Ob der Attest-Stand im Familien-Widget sichtbar ist, ist offen [unklar].
- Neubau: Klartext-Personenbezüge (Namen von Anleger, Bearbeiter, Verzichtenden) und Notizen (Notiz zum Termin) werden verschlüsselt gespeichert; Aufbewahrung und Auditierung festlegen [unklar].
Abnahme: Eine Fachlehrkraft sieht bei einem Fall „abwesend“, Termin und Attest-Stand, aber keinen Grund und kein Dokument; die Administration erhält 403; Eltern sehen nur die Zeilen ihres Kindes (fremdes Kind: 404).

### VER-070 · Nachschreibtermine anlegen, ändern, prüfen · P1 · Status: Ist
- Termine anlegen, ändern, löschen (`POST/PUT/DELETE /exam-makeups/dates`); das Datum wird geprüft. Ein Termin wird mit Warnungen abgelehnt (Liste leer = frei), wenn: Ferien/Feiertag („ist kein Schultag (<Name>)“) bzw. kein Unterrichtstag der Klasse („Kein Unterrichtstag der Klasse.“); außerhalb des Zeitrasters („Der Termin liegt außerhalb des Zeitrasters“); Raum durch eine Klausur, einen anderen Nachschreibtermin oder laut Stundenplan belegt; die Lehrkraft schreibt zu der Zeit eine andere Klausur, hat einen anderen Nachschreibtermin oder laut Stundenplan Unterricht. Ausnahme: eigene Stunden der Lehrkraft, in denen die betroffenen Kinder ohnehin sitzen (gemeinsames Schreiben im Unterricht). Gleiche Meldungen erscheinen nur einmal.
- Mehrere Schüler/innen teilen einen Termin; Termine ohne Teilnehmende werden gelöscht. Nachschreibtermine erscheinen als Kalendereinträge und im Plan (STP-086).
Abnahme: Ein Termin an einem Feiertag wird mit „ist kein Schultag (<Name>)“ abgelehnt; ein Termin in der Stunde, in der die Lehrkraft eine andere Klasse unterrichtet, zeigt den Konflikt; derselbe Termin in einer Stunde, in der die betroffenen Kinder in ihrer Stunde sitzen, ist ohne Konflikt.

### VER-071 · Terminvorschläge für Nachschreiben · P2 · Status: Ist
- `GET /exam-makeups/suggestions`: Suchzeitraum höchstens 28 Tage ab dem Tag nach der Klausur bzw. ab morgen; höchstens 12 Vorschläge gesamt und 3 je Tag; Stunden der Lehrkraft werden berücksichtigt. Kein Vorschlag an schulfreien Tagen (Ferien, Feiertag, Wochentag ohne Unterricht einer Klasse der Kinder).
- Art „unterricht“: Stunde, die eine Lehrkraft der Klausur ohnehin hält und in der betroffene Kinder sitzen, mit dem Raum der Stunde; Bewertung = Nähe zu heute (Tage nach heute) − 5, wenn alle Kinder sitzen, sonst − 3. Art „frei“: Zeit, in der Lehrkraft, alle Kinder und ein Raum frei sind (Raum der Klausur hat Vorrang); Lage „luecke“ (Freistunde der Kinder zwischen zwei Stunden; Bewertung Nähe + 0) oder „rand“ (direkt vor der ersten oder nach der letzten Stunde der Kinder; Nähe + 1); ganz freie Stunden ohne Bezug zum Unterricht und Tage ohne Unterricht der Kinder werden nicht vorgeschlagen. Sortierung nach Bewertung, dann Datum, dann Startstunde; Ausgabe mit Uhrzeit.
Abnahme: Nach einer Klausur am 12.10. liegen alle Vorschläge zwischen 13.10. und 09.11.; je Tag höchstens 3, gesamt höchstens 12; an einem Ferientag erscheint keiner; ein Vorschlag „unterricht“ mit allen Kindern in der Stunde steht vor einem mit Lage „rand“ am selben Tag.

### VER-072 · Oberfläche: Nachschreiben, Badge, Kalender · P2 · Status: Ist
- Seite `/nachschreiben`: Liste je Klausur (gruppiert und sortiert), Zeilen je Schüler/in mit Attest-Badge und Termintext, Dialog „Termin festlegen“, Vorschläge je Art; Status als Text und Abzeichen, nie nur Farbe. Menü-Badge mit der Zahl offener Punkte je Rolle (Lehrkräfte: noch festzulegende Termine; Klassenleitung und Sekretariat: Übersicht). Startseiten-Widget für Lehrkräfte und Familien (Familie: Widget für das eigene Kind). Nachschreibtermine erscheinen als Kalendereinträge. Menüeintrag mit klarer Bezeichnung „Nachschreiben“ (im Bestand ohne Bezeichnung) [offen]. Handy-Ansicht [unklar].
Abnahme: Das Menü zeigt „Nachschreiben“ mit dem Zähler offener Fälle; die Liste zeigt je Schülerin „Termin offen“/„Termin festgelegt“ und den Attest-Badge als Text; ein Termin erscheint im Kalender.

### VER-073 · Benachrichtigung zu Nachschreibterminen · P2 · Status: offen
- Bestand: kein Postfach- oder E-Mail-Hinweis, nur Startkachel, Zähler und Live-Hinweis; der Nachteilsausgleich-Hinweis in der Klausurstunde nennt das Nachschreiben nicht; `me/today` listet keine Nachschreibtermine.
- Gewünscht (Nachtrag 12.10.): Betroffene (Familie, Lehrkraft) erfahren vom festgelegten Termin über die Benachrichtigungszentrale (ohne Gesundheitsdaten im Text), und `me/today` führt Nachschreibtermine.
Abnahme: Das Festlegen eines Termins erzeugt eine Benachrichtigung „Nachschreibtermin am 20.10., 3. Stunde“ für die Familie ohne Angabe des Grundes; `me/today` listet den Termin am Tag.

### VER-074 · Prüfungsfelder, Statistik, Kalender-Zielgruppen · P3 · Status: offen
- Prüfungsfelder nach Durchführung („zurückgegeben am“, „von“, Durchschnittsnote) und eine Prüfungsstatistik fehlen (Vergleichslücke); der Klausurplan im Klassen-Kursraum ist nur ein Link; Termine ohne Zielgruppe je Termin und Listenansicht fehlen.
Abnahme: Eine Klausur lässt sich mit „zurückgegeben am“ und Durchschnittsnote ergänzen; die Statistik zeigt Klausuren je Klasse und Zeitraum.

### VER-075 · Klassenarbeiten je Halbjahr begrenzen · P2 · Status: offen
- Wunsch A-33 (Backlog B-27): Höchstzahlen je Halbjahr für Jahrgang, Bildungsgang, Klasse oder Kurs, optional je Fach; Standardwerte je Jahrgang. Beim Eintragen prüft das System zusätzlich die Halbjahresgrenze und nennt Klasse, Halbjahr und Stand („5a, 2. Halbjahr: bereits 4 von 4 Arbeiten in Mathematik“). Die Seite „Klausuren“ zeigt je Klasse und Halbjahr eine Übersicht Fach · erlaubt · eingetragen; die Klassenseite verlinkt dorthin. Tages- und Wochengrenzen bleiben; 0 = keine Grenze.
Abnahme: Bei Halbjahresgrenze 4 für Mathematik in 5a wird die 5. Arbeit mit „bereits 4 von 4 Arbeiten in Mathematik“ abgelehnt; die Übersicht zeigt 4 von 4.

### 2.7 Offene Wünsche und Querschnitt der Vertretung

### VER-076 · Offene Wünsche und Vergleichslücken der Vertretung · P3 · Status: offen
- Eigenarbeit/Selbststudium bei Ausfall je Klassenstufe mit Material (Betreiber „Next up“ 12.10.; Recht `substitution.self_study`, ab welcher Klassenstufe die Verwaltung festlegt, nicht die Lehrkraft selbst; im Bestand nicht durchgesetzt).
- Bereitschaft und Sondereinsatz (Reserve vorab verplant, bei Ausfall bevorzugt eingesetzt; eigener Sondereinsatz-Typ; Doppelstunden-Modell); Vertretungsautomatik mit wählbarer Methodenreihenfolge (Bereitschaft vor Freigesetzten, Verschiebung vor Vertretung, Pausenaufsicht); Tagestext zum Vertretungsplan; Zusatzrolle „Leseansicht“ und Schalter „Kollegium sieht den ganzen Vertretungsplan“ (Lehrerzimmer-Ansicht); Vertretung im Stundenplan an derselben Stelle wie Klausuren (Betreiber 11.10.: Umsetzung nicht ausdrücklich bestätigt); Landes-Exporte (NRW-Vertretungsabrechnung, ASV, LUSD) und Mehrarbeit nach KMBek (nur Bayern, auf Nachfrage); Push bei Vertretung (BEN/B-41).
- Gestrichen: Vertretungs-Ansicht für Fernseher (der Monitor existiert).
Abnahme: Entscheidung des Betreibers je Punkt liegt vor und ist nachgetragen; „Eigenarbeit“ erscheint als Vorschlag im Eintragsdetail nur für die vom Recht `substitution.self_study` zugelassenen Klassenstufen.

### VER-077 · Audit und Rechte-Querschnitt der Vertretung · P0 · Status: offen
- Jede schreibende Aktion wird im Audit-Protokoll festgehalten (ohne Inhalte): Abwesenheit anlegen/ändern/löschen, Selbstmeldung, manuelle Entscheidung, Freigabe, Monitor-Konfiguration, Aufsicht bearbeiten/erzeugen, Klausur, Nachschreibtermin, Fall erledigt, Attest-Verzicht. Bestand: nicht für alle belegt. Audit-Zeiten in UTC. Die Administration sieht im Protokoll keine Einträge zu Krankmeldungen von Schüler/innen mit Schüler-Kennung und Zeitraum (Befund: sichtbar). Änderungen am Planungsdokument sind auditiert (`plan.change`).
- Verknüpfung von Konten mit `teacher_id`/`student_id` ist an die Rolle gebunden (Befund: ungeprüft).
Abnahme: Anlegen einer Abwesenheit erzeugt einen Audit-Eintrag ohne Grund; die Administration sieht in der Protokollliste keinen Eintrag zu Schüler-Krankmeldungen; jede in diesem Teil genannte schreibende Aktion hat einen Eintrag.

### VER-078 · Datenschutz, Aufbewahrung, Verschlüsselung (Vertretung, Aufsichten, Nachschreiben) · P0 · Status: offen
- Abwesenheiten von Lehrkräften sind personenbezogen: Gründe verschlüsselt, nie öffentlich, nie in Benachrichtigungen; Namen in Abwesenheiten, Dokumenten und Kanalbeiträgen werden bei Kontolöschung vollständig pseudonymisiert (Befund: unvollständig). Aufsichtspläne und Belastung sind personenbezogen; Sichtbarkeit nach Rolle.
- Aufbewahrung und Löschung von Abwesenheiten, manuellen Entscheidungen, Aufsichtsplänen, Nachschreibfällen und -terminen sowie der Outbox-Einträge sind festzulegen [unklar: Fristen] und ins Löschkonzept aufzunehmen. Nachschreibtermin-Notizen und Namen werden verschlüsselt (VER-069). Die Druckansicht erfordert Anmeldung (VER-033).
Abnahme: Nach Löschung des Kontos einer Lehrkraft enthalten Abwesenheiten, Vertretungshistorie und Kanalbeiträge keinen Namen mehr (Kürzel/Name ersetzt durch „gelöscht#<Nummer>“); das Löschkonzept führt die genannten Datenarten mit Frist.

### VER-079 · Oberflächenregeln für Vertretung, Aufsichten, Monitor · P1 · Status: offen
- Anrede „Sie“; Erklärungen nur hinter dem Hilfe-Symbol (Beispiel Hilfetext: „Jüngere Klassen werden immer vertreten.“); keine Erklärabsätze (Befund: sichtbarer Erklärsatz für Lehrkräfte auf der Vertretungsseite); keine Emojis oder Zeichen als Icons (Befund: „● live“, Stecknadel); Statusfarben nie ohne Text; Singular/Plural stimmen („1 Kursraum“, „1 Hinweis“); App-Dialoge statt Browser-Popups (Abmelden am Monitor mit Bestätigung im App-Dialog); jede Ansicht bei 390 px ohne waagerechten Bildlauf; Tage-×-Stunden-Ansichten (Aufsichten, Vertretung nach Stunden) nutzen das gemeinsame Raster (STP-094); Namens-Sprechblasen für Kürzel außer auf dem Monitor, in Auswahllisten und im Druck.
- Die Vertretungsfarben (Vertretung, Betreuung, Entfall, Verlegung, Raum, Abwesend, Aufsicht, Klausur, Sonstiges) haben in beiden Schemata gleichwertige Werte; Schrift auf Statusflächen mindestens 4,5:1.
Abnahme: Ein Test findet auf Vertretungs-, Aufsichts- und Monitorseiten keinen Erklärabsatz, kein „du“, kein Emoji; die Vertretungstabelle erfüllt im dunklen Schema Kontrast 4,5:1.

### VER-080 · Leistung und Last der Vertretung · P2 · Status: offen
- Spitzenlast zwischen 7:30 und 8:00 Uhr mit 2.500 Schüler/innen und 300 Lehrkräften: Abrufe des Vertretungsplans und der persönlichen Sicht bei 95 % unter 500 ms; eine Krankmeldung wird für alle offenen Clients sichtbar, ohne alle Tage aller Klassen neu zu berechnen; die Tagesplan-Berechnung der Referenzschule (99 Klassen, 169 Lehrkräfte) bleibt interaktiv [unklar: Messwert]. Versand einer Planänderung an 2.500 Abonnements unter 30 s (BEN).
Abnahme: Lasttest mit den genannten Zahlen hält die 95-%-Marke von 500 ms; das Ergebnis steht in der Betriebsdokumentation.

---

## 3. Offene Fragen an den Betreiber (zusammengefasst)

1. Samstag/Sonntag im Stundenplan: immer sichtbar (Ist) oder nur bei Terminen (Wortlaut 11.10.; Backlog B-32)? (STP-009)
2. Reihenfolge der Planungs-Reiter: „Plan prüfen“ vor Qualitätsbericht (Ist) oder Bericht zuerst (Wunsch 12.10.)? (STP-079)
3. Klausur-Grenze 0 = „keine Grenze“ bestätigen. (STP-061)
4. Schulleitung ohne Generator-Recht: so gewollt? (STP-109)
5. Soll „Plan prüfen“ eine Variante empfehlen? Soll bei neuem Paket eine Nachricht an die Berechtigten gehen? (STP-082)
6. Standard „nur qualifizierte Lehrkräfte vertreten“ statt Rückfall auf fachfremde Betreuung? (VER-016)
7. Monitor-Menü-Knopf: Gestaltung/Sichtbarkeit; anonymer Aushang-Zugang? (VER-058, VER-033)
8. Gelten Entfall und Verlegung ebenfalls als freigabepflichtig im Bestätigungsmodus? (VER-027)
9. Schulbegleitung mit `substitution.read`: gewollt? (VER-030)
10. Aufbewahrungsfristen für Abwesenheiten, Planvorschläge, Plan-Stände, Aufsichten, Nachschreibfälle, Outbox. (STP-081, STP-111, VER-078)
11. Bedarf der Vergleichsfunktionen: Bereitschaft/Sondereinsatz, Vertretungskonto-Ausbau, Landes-Exporte, Oberstufenplanung, Wertrechnung, Abteilungsplanung, Untis-Wechsel-Assistent. (STP-102, STP-106, STP-108, VER-018, VER-076)

<!--ENDE-->
