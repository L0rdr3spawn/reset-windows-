# 01 Produkt und Prinzipien (PRI)

Neubau-Paket „Schulpuls“ (Arbeitsname). Kürzel dieser Datei: PRI. Stand der Quellen: 2026-10-18 09:10 (Gespräche des Betreibers 10-11 bis 10-18, Anforderungslisten A-00 bis A-70 vom 10-05 bis 10-12, Arbeitsnotizen der Vorgänger-Agenten, Prüf-, Bewertungs- und Rechercheberichte 10-13 bis 10-17).

## 0. Lesehinweise

**Begriffe**

| Begriff | Bedeutung in diesem Paket |
|---|---|
| Betreiber | Auftraggeber und Inhaber der Software. Gegenüber den Schulen der „Anbieter“. Er spricht und diktiert Deutsch per Spracheingabe; Transkriptionsfehler kommen vor (Abschnitt 6.5). |
| Schule | Kunde und datenschutzrechtlich verantwortliche Stelle; Käufer ist oft der Schulträger (Stadt, Kreis). |
| Admin | Technische Administration einer Schule (Konten, Einstellungen). Hat nicht automatisch Zugriff auf Gesundheitsdaten. |
| Inhaber-Konto | Das Admin-Konto des Betreibers in seinen eigenen Instanzen; besonders geschützt (REC). |
| Altsystem | Der bis 2026-10-18 gebaute Stand. Nur als Beschreibung dessen, was „Ist“ ist; der Neubau übernimmt keinen Code. |
| Neubau | Das neu zu schreibende System. |
| Arbeitsname | „Schulpuls“. Endgültiger Produktname offen (Abschnitt 2). |

**Konventionen**

- Kennung `PRI-nnn`, fortlaufend. Priorität: P0 Pflicht, Sicherheit, Recht; P1 Kernfunktion; P2 wichtig; P3 Wunsch. Alle PRI-Regeln sind verbindlich; die Priorität steuert nur die Reihenfolge bei knappen Mitteln.
- `Status: Ist` = im Altsystem umgesetzt (der Neubau muss mindestens gleichwertig sein). `Status: offen` = gewünscht, im Altsystem nicht oder nur teilweise gebaut. Unabhängig vom Status gilt jede Anforderung für den Neubau.
- Zitate des Betreibers stehen wörtlich in „…“ (Diktatfehler bleiben). Datumsangaben `MM-TT` im Jahr 2026. Eine spätere Aussage des Betreibers überstimmt eine frühere; wo beide genannt sind, ist die gültige markiert.
- Herkunftsmarken: [Betreiber] = Aussage des Betreibers; [Claude, bestätigt] / [Claude, unbestätigt] = Entscheidung eines Vorgänger-Agenten, die der Betreiber ausdrücklich übernommen bzw. nicht bestätigt hat; [Recherche] = Bericht ohne Betreiberäußerung. Unklares steht als `[unklar: …]`.
- Verweise auf andere Dateien nur über das Kürzel: STP Stundenplan/Generator, VER Vertretung, KLB Klassenbuch, NOT Noten, KUR Kursräume, NAC Nachrichten, FOR Formulare/Briefe, STA Stammdaten/Einrichtung, LEH Lehrkräfte, SCH Schüler/Eltern, REC Rechte, ANM Anmeldung, DAT Datenschutz, BEN Benachrichtigungen, INT Integrationen, BET Betrieb/Lizenz, OBE Oberfläche, SIC Sicherheit, REH Recht, QUA Qualität.
- Nicht in dieser Datei: Passwörter, Schlüssel, Tokens, Lizenzschlüssel, echte Adressen, Domains, IPs, Personennamen. Wo im Original Zugangsdaten standen, steht nichts.

---

## 1. Produkt

### 1.1 Vision

Schulpuls ist ein webbasiertes Schulverwaltungs- und Lernsystem aus einer Hand. Es umfasst: Stundenplan-Erzeugung mit eigenem Generator und dauerhafter Planprüfung (STP), Vertretung, Pausenaufsichten und Monitore (VER), Klassenbuch, Fehlzeiten, Atteste und Nachschreiben (KLB), Noten, Kompetenzen und Klausuren (NOT), Kursräume mit Aufgaben und Lernfortschritt (KUR), Nachrichten als Chat, Gruppe, Brief und E-Mail in einer Oberfläche (NAC), Formulare und Zugangsbriefe (FOR), Stammdaten, Einrichtung und Jahreswechsel (STA), Lehrkraft-Selbstverwaltung (LEH), Schüler/innen- und Elternbereich (SCH), Rechte und Rollen (REC), Anmeldung und Konten (ANM), Datenschutz und Protokolle (DAT), Benachrichtigungen (BEN), Import, Export und API (INT) sowie Betrieb, Lizenz, Updates und Anbieter-Portal (BET).

Leitsätze des Betreibers: Die Software wird „als volles Produkt an eine Schule verkauft“; die Schule soll „wirklich alles darüber machen“ können; „Denke an mehr, was ich jetzt nicht ausdrücklich gesagt habe.“ (A-00, 10-05).

**PRI-001 · P0 · Status: offen — Leitziel: verkaufsfähiges Gesamtprodukt**
Anforderung: Der Neubau ist ein vollständiges, verkaufsfähiges Schulverwaltungs- und Lernsystem. Es ist kein Amateurprogramm, hat keine KI-typische Oberfläche (keine Erklärprosa, keine „komischen Schieber oder Felder“) und ist für PC, Laptop, Tablet und Handy ausgelegt.
Herkunft: [Betreiber] 10-05 (A-00): „ein Schulmanager, den man als volles Produkt an eine Schule verkaufen kann“. [Betreiber] 10-13 20:01: „Also es ist kein amateurn Programm, das soll schon am Ende ein voll ausgewachsener Schulmanager sein.“ [Betreiber] 10-18: „alle Sicherheitsmaßnahmen beachten, alle gesetzlichen Sachen beachten, alle Oberflächen und Datenbanken und alles, was wir haben“.
Abnahme: Abnahmerundgang mit je einem Konto jeder Standardrolle (REC) durchläuft jeden Fachbereich dieses Pakets ohne Sackgasse; die Marktreife-Checkliste (rund 50 Punkte in sechs Gruppen: Funktionen, Datenschutz, IT-Sicherheit, Barrierefreiheit, Firma und Verträge, Betrieb und Support) hat keinen offenen P0-Punkt; Fehlerfall: ist ein P0-Punkt offen, wird die Version nicht an eine Schule ausgeliefert.

**PRI-002 · P0 · Status: offen — Funktionsumfang mindestens wie das Altsystem, nichts streichen**
Anforderung: Der Neubau erfüllt mindestens den Funktionsumfang des Altsystems und alle Wünsche dieses Pakets. Funktionen werden nicht gestrichen, sondern höchstens optimiert, zusammengelegt, umbenannt oder mit besseren Standardwerten versehen; bestehende Einstellungen und Daten werden verlustfrei übernommen. Nicht ausdrücklich genannte, aber übliche Schulfunktionen werden als Liste vorgeschlagen und nicht ungefragt eingebaut.
Herkunft: [Betreiber] 10-12 20:51: „Auf jeden Fall sollen keine Features gestrichen werden, es sollen nur optimiert werden.“ [Betreiber] 10-05: „Denke an mehr, was ich jetzt nicht ausdrücklich gesagt habe.“
Abnahme: Funktionsmatrix: Jede Anforderung dieses Pakets mit `Status: Ist` hat im Neubau einen bestandenen Abnahmetest (Anzahl bestandener Tests = Anzahl Ist-Anforderungen). Eine Funktion entfällt nur mit Eintrag im Entscheidungsprotokoll des Betreibers; ohne Eintrag gilt das Entfernen als Fehler.

**PRI-003 · P1 · Status: offen — Neubau ohne Altcode und ohne Fremdcode unter Copyleft**
Anforderung: Der Neubau wird vollständig neu geschrieben, ohne Übernahme von Quelltext des Altsystems. Aus Fremdprojekten werden nur Ideen übernommen, kein Quelltext; das gilt insbesondere für Projekte unter AGPL (SchulCloud, SchulIT). Eingesetzte Bibliotheken stehen unter permissiven Lizenzen (MIT, Apache 2.0, BSD) und sind in einer Lizenzliste erfasst.
Herkunft: [Betreiber] 10-18: „wenn du das ganze Programm komplett neu schreibst mit 0 % des alten Codes, also einem ganz neuen Fenster, ob es dann besser wird“. [Claude, unbestätigt] 10-13 20:26: „Von SchulCloud und SchulIT (AGPL) nur Ideen übernehmen, keinen Code.“
Abnahme: Lizenzscan der Abhängigkeiten (Python und Frontend) → keine AGPL/GPL-Pakete im Auslieferungsimage; Ähnlichkeitsprüfung gegen das Altrepository liefert keine übernommenen Dateien; Fehlerfall: Treffer → Paket entfernen oder neu schreiben.

**PRI-004 · P1 · Status: offen — Schulgrößen und Last**
Anforderung: Der Neubau trägt drei Schulgrößen: Klein bis 1.000 Schüler/innen (80 Lehrkräfte, rund 2.580 Konten, 40 Klassen), Mittel bis 2.500 (200 Lehrkräfte, rund 6.450 Konten, 100 Klassen), Groß bis 5.000 (400 Lehrkräfte, rund 12.900 Konten, 200 Klassen). Der Stundenplan-Generator erzeugt Pläne für rund 2.500 Schüler/innen und einige hundert Lehrkräfte (A-02). Lastziel nach Betreiberwunsch: „tausende gleichzeitige Nutzer“, die gleichzeitig schreiben, ohne dass das System „unglaublich langsam“ wird. Richtwerte aus der Rechnung: Spitze bei Unterrichtsbeginn rund 40 / 100 / 190 Anfragen je Sekunde und rund 600 / 1.500 / 3.000 gleichzeitige Live-Verbindungen (Klein / Mittel / Groß). Altsystem: lokal 150 gleichzeitige Nutzer ohne Fehler, Nachrichtenversand 3 bis 5 s; das Betreiberziel war damit nicht erreicht.
Herkunft: [Betreiber] 10-05 (A-02), 10-12 14:16 („guckt bitte mal über die infrastruktur“). Richtwerte [Recherche, Rechnung ohne Messung unter Last].
Abnahme: Lasttest gegen eine Instanz mit Demo-Daten (nur eigene Testinstanz) simuliert die Spitzenwerte der Größe Mittel (100 Anfragen/s, 1.500 Live-Verbindungen) und die der Größe Groß; Ergebnis: Fehlerquote 0 % [unklar: Zielwert für die Antwortzeit hat der Betreiber nicht genannt; Empfehlung 95. Perzentil unter 1 s bei Lesezugriffen, im Altsystem 1,2 s bei 60 Nutzern]. Nachrichtenversand im Lasttest unter 1 s [Empfehlung]. Details BET und QUA.

**PRI-005 · P1 · Status: offen — Modularität für alle Schulformen, keine festen Optionen**
Anforderung: Alles ist frei konfigurierbar und modular, damit möglichst viele Schulen, Schularten und Schultypen das System nutzen. Zu unterstützen sind mindestens: Grundschule, Gesamtschule, Gymnasium mit Oberstufe und Wahlkursen, Berufsschule mit Blockunterricht und Kooperationsklassen, Abendschule, Förderschule, Ganztag, Montessori- und Waldorfschule (gemischte Klassen, komplexe Unterrichtskonzepte). Es gibt keine „festen Optionen“; Sonderformen (jahrgangsübergreifende Mischgruppen, Sonderstunden für Einzelne, Förderung je Person, Lerngruppen aus mehreren Klassen) sind Optionen, nie Standard. Neue Anwendungsfälle müssen ohne Codeänderung abbildbar sein.
Herkunft: [Betreiber] 10-11 20:20: „es sollen jetzt keine festen optionen sein ich will dass es alles sehr modular und frei setzbar sind ... und dass wenn es noch andere use cases gibt, dass die auch noch funktionieren.“ [Betreiber] 10-12 19:19: „alles soll so modular … so customizable sein wie möglich, dass so viele Schulen, Schularten, Schultypen … benutzen wollen.“ [Betreiber] 10-11: Klassenprinzipien „garantiert nicht der Standard“.
Abnahme: Drei Testschulen werden allein durch Konfiguration eingerichtet: (a) Gymnasium mit Regelklassen und Wahlkursen, (b) Montessori-Schule mit gemischten Lerngruppen, Freiarbeitsblöcken und zwei Lehrkräften je Block (Vorbild Testschule: 12 Lerngruppen, 250 Kinder, 42 Lehrkräfte, 83 Kurse), (c) Berufsschule mit Abendklasse, Blockunterricht, Klassen mit „jede zweite Woche Mittwoch frei“ und Teilzeit-Lehrkräften. Der Generator erzeugt für jede einen Plan ohne harte Konflikte; es sind keine Codeänderungen nötig. Fehlerfall: Muss für einen Fall Code geändert werden, gilt die Anforderung als nicht erfüllt.

**PRI-006 · P1 · Status: Ist — Keine Festverdrahtung**
Anforderung: Stufen, Fächer, Jahrgänge und Bildungsgänge, Raumtypen, Rollen, Terminarten und Klausurarten sind Daten, nie Code. Es gibt keine feste Stufenliste (5 bis 13) und keine feste Fächerliste. Ein Jahrgang ist ein eigener Bildungsgang (z. B. „5“, „5 Informatik“, „Montessori“, „Schreiner“, „GIF 26“) mit eigener Stundentafel und frei zuweisbaren Klassen, auch nachträglich.
Herkunft: [Betreiber] 10-16 12:42: „Ich will dass der ganze das alles nicht hart gekodet ist.“ „es gibt kein fünf Informatik fünf und das es gibt keine Klassen die man für eigene Schuljahrgänge zuweisen kann“.
Abnahme: Es lassen sich die Jahrgänge „5 Informatik“, „Montessori“, „Schreiner“, „GIF 26“ sowie Stufe 0 und Stufe über 13 anlegen und Klassen zuweisen; eine statische Codeprüfung findet keine festen Fächer-, Stufen- oder Rollenlisten außerhalb von Vorschlagsdaten; Fehlerfall: Löschen eines Jahrgangs mit zugeordneten Klassen zeigt zuerst die Folgen.

**PRI-007 · P1 · Status: offen — Anzeige nur dessen, was die Schule braucht**
Anforderung: Die Oberfläche zeigt nur Funktionen und Einstellungen, die für die konkrete Schule gelten. Eine Schulform-Auswahl setzt passende Regeln und Voreinstellungen; „Erweitert“ zeigt alles. Beispiele: Pendeln und Standortwechsel erscheinen nur bei mehr als einem Standort; Module lassen sich je Schule ein- und ausschalten.
Herkunft: [Betreiber] 10-12 20:55: „dass auch immer nur das angezeigt wird, was die Schulen brauchen oder was sie nicht brauchen.“ [Betreiber] 10-12 21:08: Pendeln „quasi nur dargestellt wird, wenn das so ist“. Modul-Schalter: Marktreife-Punkt, im Altsystem nicht gebaut.
Abnahme: Instanz mit einem Standort → Seiten Lehrkraft-Verfügbarkeit, Planung und Qualitätsbericht enthalten keine Pendel- oder Standortwechsel-Elemente; zweiter Standort anlegen → Elemente erscheinen; Modul „Kompetenzen“ ausschalten → Menüpunkt, Route (404) und Startkachel entfallen; Schulform „Erweitert“ → alle Regeln sichtbar.

**PRI-008 · P0 · Status: Ist — Betriebsmodell: eine Instanz je Schule, strikte Mandantentrennung**
Anforderung: Jede Schule hat eine eigene Instanz mit eigener Datenbank, eigenem Dateispeicher und eigenem Geheimschlüssel. Schlüssel und Datenvolumen werden nie geteilt; es gibt kein gemeinsames Datenverzeichnis. Mehrere Schulen auf einer Instanz sind ein Nicht-Ziel (PRI-018). Der Anbieter betreibt getrennt davon Lizenzserver und Anbieter-Portal (BET). API-Zugänge einer Schule erreichen ausschließlich deren Daten.
Herkunft: [Betreiber] 10-12 18:46: „wenn jetzt z.B. unterschiedliche Schulen das benutzen, können auch nur die Schulen ihre eigenen APIs gründen … linken die APIs wirklich nur auf deren eigenen Datenbanken nur deren eigenen space. Kannst du das bitte sicherstellen“.
Abnahme: Zwei Instanzen A und B nebeneinander; ein API-Schlüssel von A gegen B → abgelehnt (401), ein Sitzungs-Cookie von A gegen B → abgelehnt; Dateisystem- und Datenbankprüfung: keine gemeinsamen Pfade oder Schlüssel; Test mit vertauschtem Geheimschlüssel → Daten unlesbar; Fehlerfall: API-Schlüssel anderer Schule wird nicht als „gültig, aber ohne Rechte“, sondern wie ein unbekannter Schlüssel behandelt.

**PRI-009 · P1 · Status: Ist — Plattform: Web-Oberfläche für alle Geräte**
Anforderung: Das Produkt ist eine Web-Oberfläche für PC, Laptop, Tablet und Handy. Es gibt keine native App; „App-Option“ und Push-Benachrichtigungen sind zurückgestellt (PRI-016). Die Oberfläche ist für Touch und Maus gleichermaßen bedienbar.
Herkunft: [Betreiber] 10-05 (A-61): optimiert für PC, Laptop, Tablet und Handy. [Betreiber] 10-11 20:20: „dass das auch alles mobile kompatibel ist“.
Abnahme: Die Kernabläufe jeder Rolle sind in einer Handy-Ansicht (390 px), einer Tablet-Ansicht (768 px) und am PC (1280 px und 1920 px) ohne Funktionsverlust ausführbar. [unklar: Eine Liste unterstützter Browser hat der Betreiber nicht festgelegt; Empfehlung: jeweils die aktuellen Versionen von Chrome, Firefox, Safari und Edge.]

**PRI-010 · P1 · Status: offen — Sprache, Region, Zeit**
Anforderung: Oberflächensprache ist Deutsch; Rechtsrahmen sind deutsches Schulrecht und DSGVO. Erste Zielregion ist [unklar: „NLW“ im Diktat, vermutlich Nordrhein-Westfalen; Datenquelle der Vertriebsplanung war das amtliche Schulverzeichnis NRW]. Zeiten werden intern in UTC gespeichert und in Ortszeit Europe/Berlin (mit Sommer- und Winterzeit) angezeigt; Protokollzeiten stehen in UTC und sind so gekennzeichnet. Datumsfelder in Schnittstellen sind ISO-Zeichenketten `JJJJ-MM-TT`. Länderspezifisches (Feiertage, Ferien, Löschfristen nach Landesrecht, Abschlussregeln) ist je Bundesland als Daten konfigurierbar. Mehrsprachigkeit für Eltern ist Vorschlag der Recherche, kein Betreiberwunsch (Abschnitt 6, E-09).
Herkunft: [Betreiber] 10-13 (Web-Scan „Kreis NLW“); [Claude, unbestätigt] Zeitkonventionen.
Abnahme: Instanz mit Zeitzone Europe/Berlin zeigt einen Eintrag vom 2026-10-24 22:30 UTC als 25.10. 00:30 (Sommerzeit) und einen Eintrag vom 2026-10-25 02:30 UTC als 03:30 (Winterzeit; Umstellung um 01:00 UTC); Protokolleintrag zeigt die Zeit mit Kennzeichnung „UTC“; Schulferien-Import für Nordrhein-Westfalen und Bayern liefert unterschiedliche Daten ohne Codeänderung.

**PRI-011 · P0 · Status: Ist — Kinderschutz und Altersgrenze 18**
Anforderung: Ein erheblicher Teil der Nutzer ist minderjährig. Für sie gilt die höchste Schutzstufe. Das Geburtsdatum entscheidet, ob jemand als minderjährig gilt; ein von Hand gesetztes Kennzeichen „volljährig“ reicht nicht. Unter 18 melden Schüler/innen nichts selbst (keine Krankmeldung, keine Beurlaubung, kein Upload von Attesten); Eltern oder Sorgeberechtigte handeln. Ab 18 entscheidet die Schülerin bzw. der Schüler selbst, was die Eltern sehen. Das echte Geburtsdatum darf nur berechtigte Personen ändern. Die Altersgrenze 18 muss der Betreiber noch ausdrücklich bestätigen (E-14). Details KLB und SCH.
Herkunft: [Betreiber] 10-11 und 10-12 19:08: „das sollen alles die Eltern regeln, wenn die Kinder dazu noch nicht berechtigt sind“; 10-12 18:11 „musst du Minderjährigen nicht anzeigen“; Alter: „dass das echte Alter von einem Schüler, von den Lehrern oder von einem Admin, also einem mit der Genehmigung, festlegen kann“.
Abnahme: Konto mit Geburtsdatum vor 17 Jahren und manuell gesetztem Kennzeichen „volljährig“ → Krankmeldung wird mit 403 abgewiesen; Geburtsdatum auf 18 Jahre geändert → Meldefunktion erscheint und der Elternzugriff wird ausgegraut bzw. zur Wahl; Schüler/in unter 18 sieht weder Knopf „Krank melden“ noch Beurlaubung; Fehlerfall: Änderung des Geburtsdatums durch Rolle ohne Recht → 403 und kein Protokolleintrag mit Inhalt.

**PRI-012 · P1 · Status: offen — Funktionsparität mit Untis und Schulmanager Online**
Anforderung: Der Funktionsumfang der Vergleichsprodukte Untis/WebUntis und Schulmanager Online soll abgedeckt werden. Dazu liegt eine Funktionsliste vor (214 Zeilen: Moodle M-01 bis M-62, Schulmanager Online S-01 bis S-43, Untis U-01 bis U-109, Status je Zeile ja / teil / fehlt / geplant / bewusst nicht). Jede Zeile mit Status „fehlt“ oder „geplant“ wird abgearbeitet; jede Zeile „bewusst nicht“ braucht die ausdrückliche Bestätigung des Betreibers (E-02).
Herkunft: [Betreiber] 10-13 20:14: „die funktion von den beiden will ich nämlich genau was die können soll auch genau … was sich hier gerade mudel schickt ab muss alles da rein“ ([unklar: Wortlaut „mudel schickt ab“ im Diktat]). [Betreiber] 10-13: „Das muss alles da rein.“
Abnahme: Paritätsmatrix liegt vor; jede der 214 Zeilen hat im Neubau den Status „ja“, „bewusst nicht (Betreiber bestätigt, Datum)“ oder einen Eintrag in der Planung mit Termin; Fehlerfall: Zeile ohne Entscheidung blockiert die Abnahme dieser Anforderung.

**PRI-013 · P1 · Status: Ist — Alleinstellungsmerkmale bleiben erhalten**
Anforderung: Die folgenden Stärken des Altsystems gelten als Produktkern und dürfen nicht abgeschwächt werden: (1) Planer und Betrieb in einem System (Generator, Regeln, Plan prüfen mit Vorschlagspaketen, Vertretung, Aufsichten, Tauschbörse, Nachholen); (2) Klassenbuch mit Fehlzeiten in Prozent; (3) Eltern-Rolle mit Freigaben nach Alter; (4) Ende-zu-Ende-verschlüsselte Chats; (5) Formulare mit Genehmigung und PDF; (6) Datenschutz als Verkaufsargument (fremde Daten 404, Gesundheitsdaten nur für Zuständige, Protokoll jeder Schreibaktion, verschlüsselte Freitexte); (7) Daten beim Träger (eine Instanz je Schule); (8) offene API mit API-Zugängen je Schule; (9) Import aus Untis, SchILD/SVWS, ASV, LUSD, OneRoster, Moodle und CSV.
Herkunft: [Recherche] Marktübersicht 10-13 (41 Produkte), Vergleich Moodle/Schulmanager Online/Untis.
Abnahme: Für jedes der neun Merkmale existiert ein Ende-zu-Ende-Abnahmetest in der jeweiligen Fachdatei (STP, KLB, SCH, NAC, FOR, DAT/SIC, BET, INT); alle bestanden.

### 1.2 Zielgruppen und Rollen (Überblick)

Zielgruppen: Schulen aller Formen und deren Träger als Kunden; Schüler/innen (teils minderjährig), Eltern, Lehrkräfte, Schulverwaltung und Schulleitung als Nutzer; der Betreiber als Anbieter. Die vollständige Rechtematrix steht in REC, die Anmeldung in ANM.

| Rolle | Zielgruppe / Grundtyp | Wesentliches |
|---|---|---|
| Admin (inkl. Inhaber-Konto) | Technische Administration | Konten, Einstellungen, Rechtevergabe; sieht nie ärztliche Atteste (Mindestregel, siehe E-15); Inhaber-Konto nur durch den Inhaber änderbar |
| Schulleitung | Personal | Voller Überblick; entsperrt Halbjahresnoten; Moderation von Chat-Meldungen (Standard); Rang höchste Stufe |
| Planung (Planer) | Personal | Erzeugt Pläne, startet den Generator, bearbeitet Vorschlagspakete |
| Sekretariat | Personal | Krankmeldungen und Beurlaubungen bearbeiten, „teilweise entschuldigt“ setzen, Passwort-Reset für alle Konten |
| Abteilungsleitung | Personal | Sieht nur den eigenen Schulzweig |
| Lehrkraft mit Klassenleitung | Lehrkraft | Klassenleitung ergibt sich automatisch aus der Klassenzuweisung; sieht alle Stunden der eigenen Klasse |
| Lehrkraft ohne Klassenleitung (Fachlehrkraft) | Lehrkraft | Sieht nur eigenen Plan und eigene Stunden; keine Gesundheits- und Förderdaten |
| Schüler/in minderjährig | Schüler/in | Liest eigene Daten; meldet nichts selbst |
| Schüler/in volljährig | Schüler/in | Meldet selbst; steuert Elternzugriff |
| Eltern | Eltern | Je Kind; lesend in Kursräumen; Zugriff auf volljährige Kinder nur mit Freigabe |
| Schulbegleitung | Eigener Typ | Zugang zu Plan, Kursräumen, Material und Abgaben des Kindes; ohne Elternrechte; im Altsystem nur für ein Kind (mehrere Kinder offen) |
| Hausmeister/in | Eigener Typ | Eingeschränkte Rolle (neu im Altsystem); [unklar: Standardrechte in den Quellen nicht beschrieben, siehe REC] |
| Monitor | Anzeige | Vertretungsbildschirm, optional mit festem Standort; zeigt keine Abwesenheitsgründe |
| Zuschauer (Ansichtskonto, Vorführkonto) | Ansicht | Nur lesen, Allowlist von 26 Rechten; jede Änderung → 403 |
| Eigene Rollen | Grundtyp Personal, Lehrkraft, Schüler/in, Eltern oder Ansicht | Name, Beschreibung, Vorlage für Startrechte; löschbar erst ohne zugeordnete Konten |
| Beobachtetes Konto (Betatester) | Kontoeigenschaft, keine Rolle | Alle Anfragen werden verschlüsselt protokolliert (DAT) |
| Anbieter (Betreiber) | Außerhalb der Schul-Instanz | Anbieter-Portal und Lizenzserver (BET) |

Rangfolge für Zuständigkeit: Lehrkraft < Klassenleitung < Abteilungsleitung < Sekretariat < Schulleitung; Hausmeister/in und Schulbegleitung stehen daneben.

### 1.3 Positionierung und Abgrenzung (grob)

Die Aussagen beruhen auf Recherche vom 10-13 (Suchauszüge und Herstellerseiten, nicht alles belegt). Der Betreiber hat die Funktionslisten der Vergleichsprodukte als Messlatte gesetzt (PRI-012).

| Produkt / Gruppe | Wofür im Markt | Verhältnis zu Schulpuls |
|---|---|---|
| Schulmanager Online | Cloud-Schulverwaltung mit Modul-Abos (Planung, Vertretung, Elternbriefe, Infoscreen, Zahlungen, Zeugnisse); einzelne Module laut Herstellerseite 89 bis 239 € je Schuljahr, bis 30 % Rabatt; keine öffentliche API | Funktionsreferenz. Abgrenzung: Planer und Betrieb in einem System, Daten beim Träger, offene API, E2E-Chats. Zahlungen, Zeugnisdruck und Videokonferenz „bewusst nicht“ (Bestätigung offen, E-02). Namensnähe zu „Schulmanager“ beachten (PRI-028) |
| Untis / WebUntis | Stundenplan-Planer (Textformat GPU001 bis GPU015), WebUntis mit Klassenbuch, Vertretung, Messenger; nicht quelloffen | Funktionsreferenz. Eigener Generator statt Untis; Untis-Import und -Export als Brücke; Schnittstelle bewusst nicht Untis-kompatibel (Kompatibilitätsschicht nur bei Bedarf) |
| Moodle | Lernplattform | Nur Vorbild für Kursräume (Ordner, Material, Aufgaben, Freigabe nach Vorgänger, Fortschritt, Kompetenzraster, Notenbuch, Abzeichen, Papierkorb, Selbsttest). Nicht nachgebaut: siehe PRI-014. Import aus einem Moodle-Datenbankabzug möglich |
| SchILD-NRW/SVWS, ASV (BW/Bayern), LUSD, Magellan, OneRoster | Schulverwaltung und Austauschformate | Zeugnisdruck bleibt dort; Schulpuls importiert, exportiert und liefert Noten und Fehlstunden zu |
| IServ, Sdui, schul.cloud, itslearning, Edupage, MS Teams, Google Classroom, Schoolfox, Logineo, LernSax, beste.schule u. a. | Kommunikation und Lernen | Abgrenzung über Planung plus Vertretung plus Datenschutztiefe. Landes-Logins (Schulconnex, VIDIS) sind laut Recherche in NRW, Niedersachsen und Sachsen praktisch Kaufvoraussetzung [ungeprüft] (E-17) |
| SchulCloud, SchulIT | Quelloffene Schulsoftware (AGPL) | Nur Ideen, kein Code (PRI-003) |

### 1.4 Was das Produkt nicht sein soll

**PRI-014 · P1 · Status: Ist — Nicht-Ziel: Moodle-Funktionen jenseits der Kursräume**
Anforderung: Nicht gebaut werden: volles Quiz-System mit Fragenbank und Lernpfaden, SCORM/IMS-CP, Workshop (Peer-Assessment), Portfolio-Dienste, Plagiatsprüfung, Videokonferenz, Bezahlfunktionen, Plugin-Marktplatz und Installation von Fremdcode, Blog/Notizen/Tags/Bewertungen/Social-Blöcke, Inhaltsbank als eigenes Modul. Quiz und H5P sind als Link einbindbar; ein einfacher Selbsttest mit Fragensammlung bleibt. Videokonferenzen: Link zur Schul-Lösung oder zum Landesdienst genügt.
Herkunft: [Claude, unbestätigt] 10-13 20:08; der Betreiber widersprach nicht. Ob er weitere Moodle-Teile will, ist offen (E-03).
Abnahme: Menü, Routen und Rechte enthalten keines der genannten Module; ein Link-Material mit URL zu einem Quiz öffnet das Ziel in neuem Tab; Selbsttest mit sechs Fragearten lässt sich anlegen und auswerten (KUR).

**PRI-015 · P1 · Status: Ist — Nicht-Ziel: Zeugnisdruck und Zahlungen innerhalb der Schule**
Anforderung: Zeugnisdruck, Kopfnoten-Druck, Klassengeld, Mensa-Bestellung und Bezahlschranken gehören nicht zum Umfang. Schulpuls liefert Noten und Fehlstunden an SchILD/ASV und Co. Zahlungen zwischen Schule und Anbieter (Abo, Rechnungen) sind davon getrennt und gehören zum Anbieter-Portal (BET). Der Betreiber hat „Untis und Schulmanager Online … muss alles da rein“ gesagt; dieser Widerspruch ist zu klären (E-02).
Herkunft: [Claude, unbestätigt] Backlog-Entscheidung „bewusst nicht“, Herkunft unklar.
Abnahme: Es gibt keine Funktion zum Erzeugen eines Zeugnis-PDF oder zum Einziehen von Schulgeldern; Notenexport (CSV, OneRoster) enthält Noten und Fehlstunden; Anbieter-Portal erzeugt Rechnungen als PDF ohne Zahlungsfunktion der Schule.

**PRI-016 · P1 · Status: Ist — Zurückgestellt: native App und Push**
Anforderung: App-Option und Push-Benachrichtigungen kommen vorerst nicht in den Umfang. Die In-App-Benachrichtigung (Glocke) und die E-Mail-Benachrichtigung sind davon getrennt und gehören dazu (BEN).
Herkunft: [Betreiber] 10-13 20:14: „die app option mus noch nicht mit rein“.
Abnahme: Es gibt keinen Push-Dienst, keinen Dienst-Worker für Push und keine App-Installationsaufforderung; die Glocke zeigt Benachrichtigungen innerhalb der geöffneten Anwendung.

**PRI-017 · P0 · Status: Ist — Nicht-Ziel: KI-Entscheidungen und Weitergabe von Schülerdaten an Fremd-KI**
Anforderung: Der Generator und die Planprüfung laufen ohne KI und ohne Internet (klassisches Optimierungsverfahren). Es gibt keine KI-Funktionen, die Daten von Schülerinnen und Schülern oder Lehrkräften an Dritte senden. Eine automatische Antwort („Abwesend bis …“) an Eltern wird nicht gebaut (datenschutzkritisch); höchstens ein Hinweis im Chat. KI-Entwürfe ohne Klarnamen sind nur ein Vorschlag der Recherche und brauchen eine Betreiber-Entscheidung (E-20). Entscheidungen im Betrieb trifft immer ein Mensch.
Herkunft: [Betreiber] 10-12 20:53 („Menschen mögen es lieber, eine Auswahl zu haben“); [Claude, unbestätigt] 10-16 (Autoantwort verworfen), Recherche M-50 „KI bewusst nicht (Datenschutz)“.
Abnahme: Netzwerkprüfung während Plan-Erzeugung und Vertretungsberechnung: keine ausgehenden Verbindungen; Statische Prüfung: keine KI-Dienstanbindung im Auslieferungsimage; Lehrkraft meldet sich bis Datum X abwesend → es wird keine automatische Nachricht an Eltern erzeugt.

**PRI-018 · P0 · Status: Ist — Nicht-Ziel: mehrere Schulen je Instanz, Selbstregistrierung, Gastzugang**
Anforderung: Konten entstehen ausschließlich durch die Schule (Anlage, Import, Klassen-Assistent); es gibt keine Selbstregistrierung, keinen Gast- oder öffentlichen Zugang. Ohne Anmeldung erreichbar sind nur: die Anmeldeseite mit dem Passwort-vergessen-Ablauf, Impressum, Datenschutzerklärung, die Gesundheitsprüfung der Instanz und das durch einen geheimen Schlüssel geschützte Kalender-Abo. Mehrere Schulen auf einer Instanz sind ausgeschlossen (PRI-008). Anmeldedienste (Google, Microsoft, Apple) erstellen keine Konten, sondern verbinden bestehende Schulkonten.
Herkunft: [Claude, unbestätigt] 10-12/10-13 (Kinderschutz); [Betreiber] 10-12 18:58 (nur bestehende Schulkonten).
Abnahme: Aufruf der Registrierung → nicht vorhanden (404); Anmeldung über Anbieter mit unbekannter E-Mail → keine Kontoanlage, neutrale Fehlermeldung; Nicht angemeldeter Aufruf jeder anderen Seite → Weiterleitung zur Anmeldung bzw. 401, keine Daten.

**PRI-019 · P1 · Status: Ist — Nicht-Ziel: bestimmte Oberflächenelemente**
Anforderung: Nicht gebaut werden: Stundenplan-Druck (Drucke bleiben: Vertretungsplan-Aushang, Zugangsbriefe, schriftliche Entschuldigung); Vertretungsplan als Seite für Schüler/innen und Eltern (Information über den eigenen Stundenplan); Legenden-Leiste unter dem Stundenplan; Text-Chips im Tageskopf; Karte „Mein Tag“ als Ersatz für Raster und Liste; Dunkelmodus-Zeitplan („System“ deckt es ab); eigene TV-Vertretungsansicht (der Monitor existiert); GIF-Suche über Fremddienste. Wunschlisten-Vorschlag „Stundenplan als PDF für Eltern“ nur auf Betreiber-Freigabe (E-19).
Herkunft: [Betreiber] 10-12 19:16: „Das mit dem Stundenplan drucken macht gar keinen Sinn, das kannst du weglassen.“; 10-12 18:03: „der Vertretungsplaner muss nicht für die Kinder angezeigt werden. Da ist ja auch nichts, was die sehen sollten.“; 10-11 20:20: Legende „Das soll bitte weg.“
Abnahme: Es gibt keinen Druckknopf am Stundenplan; Aufruf der Vertretungsseite als Schüler/in oder Eltern → 403 (Menüpunkt und Startkachel fehlen); Stundenplan zeigt Ausfall, Vertretung und Raumänderung trotzdem im eigenen Raster; keine Legende unter dem Raster.

**PRI-020 · P1 · Status: Ist — Nicht-Ziel: verworfene Planungsmodelle**
Anforderung: Nicht gebaut werden: Wochenbuchstaben (A/B-Wochen), Wochenzyklus, globaler Wochenrhythmus, „Gilt für Jahrgang“ als Bedingung, „Wunschklassen“ (ersetzt durch: Klassenleitung, Klassen in denen unterrichtet wird, Klassen in denen vertreten werden kann), starre Höchst- und Mindestwerte für Vertretungen, die eine Lehrkraft selbst setzt, und die Schnellauswahl bei Arbeitszeiten.
Herkunft: [Betreiber] 10-11 und 10-12 (A-40, A-48, A-49, A-67); 10-12 21:08: „Die habe ich dir gesagt, die Schnellauswahl kommt weg.“
Abnahme: Textscan über Oberfläche, Meldungen, Demo-Daten, ICS-Export und Dokumentation findet keinen der Begriffe „Woche A/B“, „Zyklus“, „Zykluswoche“, „Wochenzyklus“, „Wunschklassen“, „Gilt für Jahrgang“, „Schnellauswahl“; Datenmodell enthält kein Feld für globale Wochenzyklen.

**PRI-021 · P0 · Status: Ist — Nicht-Ziel: Fremdkomponenten und Datenabfluss**
Anforderung: Es gibt keine Tracker, keine Analyse- und Session-Replay-Skripte, keine Fremd-CDNs, keine Fremdschriften (Schriften liegen lokal), keine GIF-Suche über Dienste wie Giphy (Suchbegriffe und IP-Adressen würden an Dritte gehen), keine Online-Prüfung geleakter Passwörter bei Dritten (Offline-Liste statt dessen) und keine Telemetrie außer dem, was der Nutzer selbst abschickt (z. B. Feedback). Anmeldedienste laden ihre Skripte erst, wenn der Anbieter in den Schuleinstellungen aktiv ist. Grundlage: [Betreiber] Datenschutz vor Komfort; [Claude, unbestätigt] Giphy-Verzicht, Passwortprüfung offline.
Abnahme: Netzwerkmitschnitt beim Laden jeder Seite im Auslieferungszustand zeigt ausschließlich Anfragen an die eigene Herkunft; die Content-Security-Policy verbietet Fremdquellen; Anbieter „Google“ aktivieren → erst dann wird dessen Skript geladen; Chat bietet keine GIF-Suche über Fremddienst.

**PRI-022 · P3 · Status: Ist — Nicht-Ziel: übrige Bereiche**
Anforderung: Nicht gebaut werden: Netzwerk- und Geräteverwaltung (MDM), gemeinsames Bearbeiten von Dokumenten, Schulwebsite, Speiseplan-Bestellung, adaptive Übungen (nur Verlinkung), Laufbahnplanung Oberstufe und automatische Wahlfach-/AG-Zuteilung vorerst (zurückgestellt, nicht abgelehnt: „bewusst später“), VIDIS-Aufnahme als eigene Entwicklung (Anschluss ggf. über Schulconnex).
Herkunft: [Claude, unbestätigt] Backlog „bewusst nicht“ bzw. „später“, Herkunft unklar.
Abnahme: Keine entsprechenden Menüpunkte; Planungsliste enthält die Zurückgestellten mit Vermerk „später“ (E-17).

---

## 2. Namens- und Markenregel

Hintergrund: Am 10-13 verlangte der Betreiber einen neuen, schulspezifischen Namen („Ich will, dass der Schulmanager zu Umgenannt wird zu einem schulspezifischen Namen, in dem Namen soll Schule oder zumindest Teile … vorkommen“). Der Arbeitsname „Schulpuls“ wurde vergeben; der Betreiber hat ihn nie ausdrücklich bestätigt. Am 10-16 ergab die Prüfung, dass der Name bereits genutzt wird.

**PRI-023 · P1 · Status: offen — Arbeitsname „Schulpuls“, Endname offen**
Anforderung: Bis zur Entscheidung des Betreibers (E-01) heißt das Produkt intern „Schulpuls“. Der Name darf nicht in Außenmaterial (Website, Anschreiben, App-Stores, Verträge, Rechnungen an Dritte) stehen, bevor der Namensprüfstand (PRI-028) bestanden ist. Gewünschtes Namensmerkmal des Betreibers: „Schule“ oder Teile davon (Anlaute) im Namen.
Herkunft: [Betreiber] 10-13 20:48; [Betreiber] 10-16 12:58: Frage, ob „Schulpuls“ schon vergeben ist; [Betreiber] 10-17: „die Domain heißt jetzt Schulmanager und nicht Schulplus“ ([unklar: „Schulplus“ kommt im Altsystem nirgends vor; vermutlich Verhörer oder Verwechslung]).
Abnahme: Kein Dokument und keine Oberfläche, die den Betreiber verlassen (Kundenpaket, Anbieter-Portal, PDF-Vorlagen), enthält einen fest eingetippten Produktnamen (siehe PRI-024); Außenmaterial existiert erst nach schriftlicher Freigabe des Betreibers nach bestandenem Prüfstand.

**PRI-024 · P0 · Status: Ist — Produktname an genau einer Stelle konfigurierbar**
Anforderung: Der sichtbare Produktname steht in genau einer Konfigurationsstelle (Umgebungsvariable `SM_APP_NAME`, Standard = Produktname des Neubaus). Er wirkt auf: Kopfleiste, Anmeldeseite, Seitentitel und Browser-Tab, Wortmarke, PDF-Kopf und PDF-Metadaten, E-Mail-Absendername, Betreff und Kopfzeilen, ausgehende Anfragen (Kennung des Programms), Kalender-Abo-Texte, Hilfetexte, Kundendokumentation, Lizenz- und Rechnungs-PDFs und Ferien-Import. Die Wortmarke ist Text, kein Bild mit fest eingebautem Namen; auch der Seitentitel der Startdatei kommt aus der Konfiguration. Ob eine Schule den Namen für sich ersetzen darf (Weißlabel), ist eine Lizenzfrage (E-05).
Herkunft: [Claude, bestätigt] 10-16: „Der Anzeigename steht an einer Stelle im Code“ (vom Betreiber in die verbindlichen Gestaltungsregeln übernommen: „Produktname nur an einer Stelle konfigurierbar“); Anlass ist der Namenswunsch vom 10-13 (PRI-023). Fehler im Altsystem: Seitentitel und Wortmarke waren fest eingetragen; Zählung der Stellen widersprüchlich („an einer Stelle“ / „an zwei Stellen“).
Abnahme: `SM_APP_NAME=Testname` setzen und neu starten → eine Volltextsuche über die ausgelieferte Oberfläche, alle erzeugten PDFs (Zugangsbrief, Entschuldigung, Rechnung), alle Test-E-Mails (Kopf und Text), die ICS-Datei und die Seitenköpfe findet den bisherigen Produktnamen 0-mal; Fehlerfall: Ist die Variable leer, greift der Standardname; ein automatischer Test schlägt fehl, sobald der Name fest im Quelltext oder in einer Vorlage eingetippt ist.

**PRI-025 · P1 · Status: offen — Technische Namen neutral und einheitlich**
Anforderung: Technische Bezeichner (Paketname, Datenbankname, Cookie-Namen, Container- und Image-Namen, Installationspfade, Webhook-Kopfzeilen, Manifest-Kennung) tragen einen einzigen, einheitlichen und vom Anzeigenamen unabhängigen Namen. Eine Umbenennung des Produkts darf keine Datenmigration und keinen Rollback-Bruch verursachen. Im Altsystem waren die Namen gemischt („schulmanager“ und „schulpuls“, Lastverteilungs-Cookie, Updater-Image); das führte zu Sonderfällen.
Herkunft: [Claude, unbestätigt] 10-17 (Code-Durchsicht). Der Betreiber will die Namen „richtig umbenannt“ („ob die Files alle richtig umbenannt werden“).
Abnahme: Alle technischen Bezeichner stammen aus einer Namensliste; ein Test findet keinen technischen Bezeichner, der den Anzeigenamen enthält; Namenswechsel (`SM_APP_NAME` ändern) lässt Cookies, Pfade, Image und Datenbank unverändert; Fehlerfall: Test schlägt fehl, wenn ein Skript einen alten Namen erwartet.

**PRI-026 · P0 · Status: Ist — Keine Betreiber- oder Anbieterdaten in Auslieferung und Kundentexten**
Anforderung: Weder im ausgelieferten Code noch in Texten, Vorlagen, Demo-Daten oder Dokumentation stehen Firmendaten, Domains, Adressen, Zugangs-Links, Vorschau-Passwörter oder Personennamen des Betreibers. Die Domain des Anbieters ist nur an einer Stelle gesetzt und überschreibbar, standardmäßig `example.org`; Platzhalter sind `schule.example.org` und für Namen „Frau Muster“. Impressum und Datenschutzerklärung enthalten Platzhalter wie [Name der Schule], [Schulträger], [Datenschutzbeauftragte/r], [Aufsichtsbehörde]; der Anbieter erscheint nur neutral als „Auftragsverarbeiter (siehe AV-Vertrag)“.
Herkunft: [Betreiber] 10-17: „da ist jetzt die Firma von mir drin … sondern das sind dann Informationen, die sollten dann die Schulen anpassen“.
Abnahme: Ein Test prüft bei jedem Lauf alle Auslieferungsdateien, Vorlagen und Demo-Daten gegen eine Sperrliste (Betreiber-Domain, Firmenname, Heimserver-Angaben, Personennamen, Codespaces-Links, Vorschau-Passwörter) → 0 Treffer; Mustertext mit offenen eckigen Klammern → Warnung in der Verwaltung und der Einrichtungsschritt gilt nicht als erledigt.

**PRI-027 · P2 · Status: Ist — Logo und Wortmarke**
Anforderung: Das Produkt hat ein Logo, das der Betreiber hat gestalten lassen: blaue Kachel mit Pulslinie und gelbem „Live“-Punkt (Altsystem, passt zum Arbeitsnamen). Es existiert in Hell und Dunkel, als Browser-Symbol und einfarbig in gleicher Geometrie (für Druck und PDF). Alle Varianten stammen aus einer Quelle. Bei Namenswechsel wird das Logo neu entschieden (E-01).
Herkunft: [Betreiber] 10-13 20:48: „Ich will auch, dass du mein Logo designst“.
Abnahme: Das Logo erscheint in Kopfleiste (hell und dunkel), Anmeldeseite, Browser-Tab, PDF-Kopf; die einfarbige Variante hat dieselbe Form wie die farbige (Vergleich der Umrisse); es gibt keine ungenutzten Logo-Dateien.

**PRI-028 · P0 · Status: offen — Namensprüfstand vor jeder Außenwirkung**
Anforderung: Vor jeder Außenwirkung eines Namens (Website, Anschreiben, App-Store, Kennzeichnung auf Rechnungen, Domain) liegt ein datiertes Prüfprotokoll vor: Markenrecherche bei DPMA, EUIPO und WIPO (selbst abfragen, keine Rechtsberatung), Domain-Verfügbarkeit (.de, .eu, .app, .net, .org, .io), App Stores und Social-Kanäle, Verwechslung mit „Schulmanager Online“. Das Prüfprotokoll ist keine Rechtsberatung; eine anwaltliche Markenrecherche wird empfohlen.
Stand des Prüfstands (10-16, [Recherche], unvollständig):

| Name | Befund |
|---|---|
| „Schulpuls“ | Im Bildungsbereich bereits von einem Berliner Unternehmen genutzt (Website, Lern-App für Klasse 1 bis 7, Videokanal, Podcast; Domain 2026-09-08 registriert). Verwechslungsgefahr hoch. Die Namensprüfung vom Vortag hatte irrtümlich „keine Treffer“ gemeldet. Ob die Seite dem Betreiber gehört, ist offen (das Impressum nennt ein anderes Unternehmen). Die .de-Domain ist belegt; .eu, .app, .net, .org, .io vermutlich frei. Marken nicht abgefragt |
| „Schulmanager“ (technischer Name, Domains, Pfade) | Fast identisch mit dem Wettbewerber „Schulmanager Online“; Marken- und Verwechslungsrisiko ungeprüft |
| Schulhafen | Ampel grün, Empfehlung der Namensvorschläge („alles in einem Hafen“); Domains scheinbar frei, nicht beim Registrar bestätigt |
| Schulfeld | Grün; kurz, wenig Bildungsbezug |
| Schulfunke | Grün; freundlich; Nähe zu „Schulfunk“ prüfen |
| Schultor, Schulkern, Schulkreis | Weitere Kandidaten, nicht bewertet |
| Schulwelle | In der Namensprüfung „am aussichtsreichsten“, in der Vorschlagsliste nicht enthalten; widersprüchlich |
| Schulea, Schulico | Gelb (Aussprache, Nähe zu anderen Marken) |
| Schulanker | Rot (Konflikt mit einem Anbieter für Schulbegleitung) |

Weiteres: DPMA-Gebühr laut Recherche rund 290 € für bis zu drei Klassen [nicht verifiziert]. Der Betreiber soll selbst prüfen und eine Domain sichern.
Herkunft: [Betreiber] 10-16 12:58: Name prüfen („ob der Name Schulpuls … schon vergeben ist oder ob es die Website schon gibt oder die Firma“); [Claude, bestätigt] Befund.
Abnahme: Prüfprotokoll mit Datum, Namen, Quellen und Ergebnis je Register liegt vor und enthält die Betreiberfreigabe; bis dahin wird in keinem Außenmaterial ein Produktname außer „Arbeitsname“ verwendet; Fehlerfall: Außenmaterial mit ungeprüftem Namen → Rückzug.

<!--ENDE-->
