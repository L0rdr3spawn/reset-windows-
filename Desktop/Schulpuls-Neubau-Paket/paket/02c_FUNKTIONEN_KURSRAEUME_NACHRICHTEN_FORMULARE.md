# 02c – Funktionen: Kursräume, Nachrichten, Formulare

Kürzel: **KUR** Kursräume, Aufgaben, Lernaktivitäten, Lernfortschritt · **NAC** Nachrichten, Chats, Postfach, Rundschreiben · **FOR** Formulare, Briefe, Zugangsdaten.
Stand der Quellen: 2026-10-18. Spätere Entscheidungen überstimmen frühere. Wortlaut des Betreibers steht in „…“ (diktiert, sinngemäß wiedergegeben). Nummern laufen je Kürzel ab 001.

## 0 Lesehilfe, Begriffe, Rechte

| Zeichen | Bedeutung |
|---|---|
| P0 | Pflicht: Sicherheit, Datenschutz, Recht |
| P1 | Kernfunktion |
| P2 | wichtig |
| P3 | Wunsch |
| Status: Ist | im bisherigen System gebaut; der Neubau muss mindestens gleichwertig sein |
| Status: offen | gewünscht, geplant, Mangel des bisherigen Systems oder nicht bestätigt; im Neubau umzusetzen bzw. zu entscheiden |
| [unklar: …] | die Quellen treffen keine Aussage; mit dem Betreiber klären, nichts erfinden |

### 0.1 Begriffe in der Oberfläche

| Begriff | Bedeutung |
|---|---|
| Kursraum | digitaler Arbeitsraum für einen Kursteil, eine Klasse oder frei angelegt (nie „Kanal“) |
| Raum der Klasse | der physische Raum; der digitale Raum heißt „Kursraum der Klasse“ |
| Nachrichten | der EINE Menüeintrag für Chats, Gruppen, Briefe, Rundschreiben, E-Mails und Mitteilungen; das Wort „Postfach“ erscheint in Texten nicht mehr |
| Chat / Gruppe | Gespräch zwischen zwei Personen / mehreren Personen, Ende-zu-Ende verschlüsselt |
| Brief | E-Mail-artige Nachricht mit Betreff innerhalb der Schule; Rundschreiben = Brief an eine Gruppe |
| Mitteilung | Aushang / Schwarzes Brett mit Zielgruppe und Gültigkeit |
| Gerät | ein Browser mit eigenem Chat-Schlüssel |
| Zugangsbrief | PDF mit den Zugangsdaten eines Kontos |

### 0.2 Rechte dieser Datei

| Recht | Wirkung | Standard (Umfang) |
|---|---|---|
| channels.use | Kursräume öffnen, Material lesen, abgeben, Pinnwand | Administration, Schulleitung, Lehrkraft, Abteilungsleitung, Schüler/in, Schulbegleitung; Zuschauer/in nur lesen |
| channels.manage | Ordner, Material, Freigaben, Aufgaben, Mitglieder, Regeln, Übersicht aller Räume | Administration, Schulleitung; Lehrkraft/Abteilungsleitung (eigene Kurse) |
| channels.view_children | Räume der eigenen Kinder lesen | Eltern (eigene Kinder) |
| channels.trash | Papierkorb wiederherstellen oder endgültig löschen | Administration, Schulleitung; Lehrkraft/Abteilungsleitung (eigene Kurse) |
| messages.use | Nachrichten nutzen (Briefe, Chats, Mail-Konten) | alle Rollen außer Monitor und Schulbegleitung |
| messages.broadcast | Rundschreiben an Gruppen | Administration, Schulleitung, Sekretariat, Planung; Lehrkraft (eigene Klassen); Abteilungsleitung (eigener Zweig) |
| messages.moderate | gemeldete Nachrichten prüfen, Sperren, Aufbewahrungslauf | Schulleitung (Standard-Zuständigkeit), Administration |
| chats.review | gemeldete Chat-Auszüge nur mit Einwilligung lesen (Status: geplant) | Schulleitung |
| mail.custom_server | eigenen IMAP-/SMTP-Server eintragen | Administration, Schulleitung, Sekretariat; nie Schüler/Eltern |
| announcement.post | Mitteilungen veröffentlichen | Administration, Schulleitung, Sekretariat, Planung; Lehrkraft (eigene Klassen); Abteilungsleitung (eigener Zweig) |
| students.read | Schüler/innen als Empfänger suchen, Klassenoptionen | Verwaltung; Lehrkraft (eigene Klassen) |
| forms.submit | Formulare ausfüllen | Eltern, Schüler/in, Lehrkraft, Sekretariat, Schulleitung |
| forms.inbox | Eingang ansehen, entscheiden, exportieren | Schulleitung, Sekretariat; Lehrkraft/Abteilungsleitung nur als Klassenleitung der eigenen Klasse; nie technische Administration |
| forms.manage | Vorlagen gestalten, Ablauf und Aktionen festlegen, Bibliothek nutzen; ohne Einblick in Einreichungen | Administration, Schulleitung, Sekretariat |
| users.manage | Zugangsbrief-Stapel anlegen | Administration, Schulleitung, Sekretariat |
| passwords.reset | Zugangsbriefe ansehen, laden, versenden | Administration, Schulleitung, Sekretariat; Lehrkraft (eigene Klassenleitung, nur Schüler/Eltern) |
| settings.edit | Schulregeln der Nachrichten, Papierkorb-Frist | Administration, Planung |

Zuschauer/in: Allowlist, jede schreibende Anfrage liefert 403; Formular-Eingang, Zugangsbriefe, gemeldete Chats, Postausgang der Benachrichtigungen und Lernstände sind entzogen (Mitteilungen lesbar).

### 0.3 Querschnittsregeln (gelten für alle Anforderungen dieser Datei, Abnahme zentral in SIC/OBE/PRI)
Anrede „Sie“ für alle inkl. Schüler/innen · Erklärungen nur über Hilfe-Symbol/Hilfetext, keine Erklärabsätze · App-Dialoge statt Browser-Popups · fremde Daten liefern 404 · jede schreibende Aktion wird ohne Inhalte protokolliert (Ausnahmen stehen ausdrücklich als Anforderung) · Freitexte verschlüsselt · Produktname nur an einer Stelle konfigurierbar · ein gemeinsames Raster für alle Tage×Stunden-Ansichten · Farbe nie allein · 390 px ohne waagerechten Bildlauf.

---

## KUR – Kursräume, Aufgaben, Lernaktivitäten, Lernfortschritt

### KUR.1 Kursräume, Mitglieder, Rollen

**KUR-001** · P1 · Status: Ist — Kursraumarten: Kursteil (aus dem Stundenplan; ein Raum je Kursteil, weil gekoppelte Kursteile getrennte Lerngruppen mit eigener Lehrkraft sind), Klasse (Klassenraum) und eigener Kursraum (frei angelegt). Tabelle `channels` mit `kind` = course|class|custom und Bezug `ref`.
Abnahme: Kurs mit zwei gekoppelten Teilen → zwei getrennte Räume; Klasse „5a“ → ein Klassenraum; Lehrkraft legt „AG Robotik“ an → Raum nur für sie und eingetragene Mitglieder sichtbar.

**KUR-002** · P1 · Status: Ist — Seite `/kursraeume`: Kacheln, Suche nach Kurs, Klasse, Fach, Lehrkraft, Filter. Am Menüpunkt „Kursräume“ steht die Zahl neuer Inhalte (Material und Pinnwand-Beiträge); beim Öffnen des Raums gelten sie als gesehen. Menü sichtbar mit channels.use, channels.manage oder channels.view_children. Eltern wählen ein Kind (Auswahl nur bei mehreren Kindern; gilt für Startseite, Krankmeldungen, Noten, Kursräume).
Abnahme: neues Material in Raum A → Zähler der Schülerin +1; nach Öffnen von A → 0. Elternkonto mit zwei Kindern sieht die Kinderauswahl und je Kind nur dessen Räume.

**KUR-003** · P1 · Status: Ist — Mitgliedschaft wird aus Stundenplan und Konten berechnet, nicht von Hand gepflegt. Ausnahme: Zusatzeinträge (`channel_extra_members`, Rolle teacher|student, z. B. Referendar/in) durch Lehrkraft/Administration. Eine Lehrkraft ist in gekoppelten Kursen nur dort „Lehrende“, wo sie tatsächlich Schüler/innen unterrichtet.
Abnahme: Schüler wird im Plan aus dem Kurs genommen → Raum nicht mehr sichtbar, ohne Handarbeit. Lehrkraft, die in einem von fünf gekoppelten Tutorien unterrichtet, ist nur dort Lehrende.

**KUR-004** · P1 · Status: Ist — Mitglieder eintragen und austragen: Fach- und Klassenlehrkräfte suchen Schüler/innen und tragen sie ein bzw. aus; die Administration darf zusätzlich Lehrkräfte eintragen (Recht channels.manage + channels.use). Auch Lehrende eines eigenen Kursraums müssen Mitglieder per Suche eintragen können (Mangel des alten Systems: Dialog versprach es, Server verweigerte es). Austragen = Person landet unter „ausgetragene Schüler/innen“ und kann wieder aufgenommen werden.
Abnahme: Lehrkraft trägt Schüler X in eigenen Raum ein → X sieht den Raum; Austragen → Raum weg, Wiederaufnahme möglich; Schüler/in ohne Recht versucht Eintrag → abgewiesen.

**KUR-005** · P2 · Status: Ist — „Wer einen Kursraum erstellt hat, kann ihn nicht verlassen.“
Abnahme: Ersteller versucht Austritt → abgelehnt, Raum bleibt unverändert.

**KUR-006** · P0 · Status: Ist — Eltern lesen automatisch mit (nur Lesen; jede Anfrage trägt das Kind). Sie sehen freigegebenes Material und Aufgaben mit Frist und Status des eigenen Kindes, nie Daten anderer Kinder, nie die Teilnehmendenliste und nie die Pinnwand eines Fachraums. Im Tab „Klasse“ gelten die Klassen-Infos (KUR-054). Volljährige Schüler/innen: Eltern nur, wenn die Schülerin im Bereich „kursraeume“ selbst freigibt (Standard „nein“, jederzeit widerrufbar); minderjährig sieht die Familie alles, was das Kind sieht. Ob Eltern im Fachraum die Pinnwand sehen, wird im alten System nicht einheitlich geregelt [unklar: Sicherheitsvariante gewählt].
Abnahme: Elternkonto → Räume des Kindes lesbar, Schreibversuch → 403, fremdes Kind/fremder Raum → 404; Eltern eines Volljährigen ohne Freigabe sehen keinen Raum, nach Freigabe ja, nach Widerruf sofort wieder nicht.

**KUR-007** · P0 · Status: Ist — Rollen im Kursraum: Lehrende; Teilnehmende; Eltern (nur Lesen); Aufsicht = Schulleitung und Administration (nur Lesen, keine Abgabe-Inhalte, keine Noten; Eingriff nur nach Selbsteintrag als Lehrende/r, protokolliert); Klassenleitung und Kursraum-Verwaltung dürfen in Klassenräumen bearbeiten; Schulbegleitung (nur Lesen: Material und Abgaben des begleiteten Kindes, ohne Elternrechte). Schreibrechte hängen an Berechtigungen manage/post/submit, nicht an der Rolle allein. Material bearbeitet die Ersteller/in oder berechtigte Lehrkraft; Abgaben bewertet die für die Aufgabe verantwortliche Lehrkraft.
Abnahme: Schulleitung öffnet Raum → sieht Material, keine Abgabe-Inhalte/Noten; Selbsteintrag erzeugt Protokolleintrag; Fachlehrkraft B bewertet Abgabe zu Aufgabe von A → 403.

**KUR-008** · P2 · Status: Ist — Kursraum anlegen (Dialog), Einstellungen ändern, löschen (löscht zugehörige Daten inkl. Lernfortschritt). Einstellungen: Titel, Beschreibung, „Schüler dürfen Beiträge schreiben“ (Standard ja), „Schüler dürfen antworten“ (Standard ja), „Eltern sehen den Fortschritt ihres Kindes“ (Standard nein), Stundenzeiten. Kurs- und Klassenräume entstehen bei Bedarf.
Abnahme: „Schüler dürfen Beiträge schreiben“ = nein → kein Eingabefeld auf der Pinnwand, Server weist Beitrag mit 403 ab.

**KUR-009** · P2 · Status: Ist — Verwaiste Räume: wird ein Kurs umbenannt oder gelöscht, bleibt der Raum bestehen und trägt die Marke „verwaist“; Verwaltung (channels.manage) sieht alle Räume in einer Übersicht. [unklar: Bereinigung/Aufbewahrung verwaister Räume ist nicht beschrieben]
Abnahme: Kurs löschen → Raum bleibt mit Marke „verwaist“ und erscheint in der Übersicht.

**KUR-010** · P2 · Status: Ist — „Alles als ZIP“ und „Archivieren“ entfallen (Wunsch 10-11): kein Archivzustand, kein Gesamt-ZIP-Knopf im Kursraum; die Anfrage `archived=true` liefert 422. [unklar: das bisherige System enthält zusätzlich eine ZIP-Schnittstelle je Raum; im Neubau kein Knopf, Personen-Auskunft bleibt getrennt (DAT)]
Abnahme: in der Oberfläche keine Knöpfe „Alles als ZIP“/„Archivieren“; PATCH mit archived=true → 422.

### KUR.2 Material, Ordner, Sichtbarkeit

**KUR-011** · P1 · Status: Ist — Inhaltsarten: Datei, Link, Textseite (einfaches Markdown ohne HTML, Formeln, Links nur http/https/mailto in neuem Tab ohne Referrer), Aufgabe. Ordnerbaum bis Tiefe 6, Anzahl Ordner/Elemente begrenzt [unklar: Werte]. Ordner anlegen (auch ganze Struktur auf einmal), umbenennen, löschen (→ Papierkorb KUR-060). Material gilt zusätzlich als „Abgabe möglich“, wenn so gekennzeichnet.
Abnahme: Ordner-Upload mit zwei Ebenen → gleiche Struktur; Ebene 7 → verständliche Ablehnung; Textseite mit `<script>` → als Text, nicht ausgeführt.

**KUR-012** · P2 · Status: offen — Ordner und Material in der Oberfläche verschieben und umsortieren (Ziehen oder Auf/Ab); leere Unterordner werden beim Ordner-Upload angelegt. Das alte System konnte die Reihenfolge nur serverseitig und ließ leere Unterordner weg.
Abnahme: Element an neue Position ziehen → Reihenfolge bleibt nach Neuladen; Ordner-Upload mit leerem Unterordner → Ordner existiert.

**KUR-013** · P1 · Status: Ist — Hochladen in einem Schritt: eine Datei wird ohne zweiten Klick als Material mit gewählter Sichtbarkeit gespeichert; Schließen des Panels verwirft nichts; Ablegen funktioniert über der ganzen Materialliste; ganze Ordner (Auswahl oder Ziehen) mit Unterordnern in einer Transaktion; Betriebssystem-Systemdateien werden übersprungen [unklar: Liste]; ZIP-Import legt nichts außerhalb des Zielordners ab; Seitenwechsel während eines Uploads fragt per App-Dialog zurück (altes System brach ohne Rückfrage ab). Ein einziger Upload-Baustein (Ziehen, Fortschritt, Mehrfachauswahl) dient allen Zwecken (Kursraum-Material, Abgabe, Pinnwand, Nachricht, Formular-Scan).
Abnahme: Datei auf die Liste ziehen → sofort als Material sichtbar; ZIP mit Pfad „../x“ → nichts außerhalb des Ordners; Seitenwechsel bei laufendem Upload → Rückfrage.

**KUR-014** · P0 · Status: Ist — Dateisicherheit: Annahme nach Inhalt (Magic-Bytes) und Allowlist (PDF, Bilder, Office/OpenDocument, Text/CSV, Audio/Video, ZIP; zusätzlich Quelltext .py .java .c .cpp .sql nur als Text-Download, .rtf, .epub, .tif; .ggb, .notebook, .flipchart behalten ihre Endung). Gesperrt: ausführbare Dateien und aktive Inhalte (HTML, SVG mit Skript, Office-Makros, PDF mit Aktionen). Größe höchstens 25 MB je Datei (`SM_UPLOAD_MAX_MB`, zulässig 1–10240), Kontingent je Konto 2000 MB Personal / 200 MB Schüler/innen (`SM_QUOTA_MB_STAFF`, `SM_QUOTA_MB_STUDENT`). Optionale Virenprüfung (ClamAV); ohne Prüfung sichtbar „ungeprüft“. Dateien und Dateinamen verschlüsselt gespeichert; Auslieferung mit nosniff/sandbox; Zugriff nur über die Kursraum-Logik (Mitgliedschaft, Freigabe, Gruppen), kein Admin-Generalzugriff; nicht angehängte Uploads werden nach 24 Stunden gelöscht.
Abnahme: .exe → abgelehnt; als .pdf umbenannte .exe → abgelehnt; .py → angenommen, Download als Text; 26-MB-Datei → abgelehnt mit Meldung; Nicht-Mitglied ruft Datei-Adresse auf → 404.

**KUR-015** · P1 · Status: Ist — Anhang-Grenzen: höchstens 20 Anhänge je Material bzw. Abgabe, 10 je Pinnwand-Beitrag und je Rückmeldung. Die Zählung berücksichtigt bereits angehängte Dateien (das alte System zählte sie nicht mit).
Abnahme: Material mit 19 Anhängen + Hinzufügen von 2 → abgelehnt; Abgabe mit 21 Dateien → abgelehnt.

**KUR-016** · P1 · Status: Ist — Sichtbarkeit je Element und Ordner, fünf Werte: sofort sichtbar · verborgen · ab Zeitpunkt · zur nächsten Stunde · zur bestimmten Unterrichtsstunde (Stundenauswahl). Mehrere Elemente gleichzeitig änderbar. Ordnerfreigabe wirkt auf den Inhalt; es gilt die strengste Regel entlang des Ordnerpfads. Der Zustand wird immer berechnet, nie direkt gesetzt. Stundenfreigabe wirkt ab Stundenbeginn laut Stundenzeiten. Wunsch: Material verborgen speichern und zur Stunde manuell oder automatisch freigeben.
Abnahme: Element „zur Stunde 3 am Do“ → erst ab Beginn Stunde 3 für Schüler/Eltern sichtbar, davor auch per Direktaufruf nicht; Ordner verborgen + Inhalt „sofort“ → Inhalt unsichtbar.

**KUR-017** · P1 · Status: Ist — Entfall, Verlegung, Ferien: fällt die gebundene Stunde aus oder ist der Tag schulfrei, gilt die nächste stattfindende Stunde desselben Kurses; Verlegung auf einen anderen Tag wird beachtet. Die Vorausschau kommender Stunden steht für die Auswahl bereit [unklar: Standard und Maximum].
Abnahme: gebundene Stunde Mo entfällt → Material erscheint zur nächsten stattfindenden Stunde, nicht am Mo.

**KUR-018** · P2 · Status: offen — Fällt eine gebundene Stunde aus, bleibt das Material verborgen und die Lehrkraft wird benachrichtigt (Hinweis mit Link zum Kursraum, ohne Details).
Abnahme: Stunde entfällt → Lehrkraft erhält genau eine Benachrichtigung; Material bleibt unsichtbar.

**KUR-019** · P2 · Status: offen — Markierung „nur für Schüler/innen“ (z. B. Lösungen) und Eltern-Einsicht je Raum abschaltbar.
Abnahme: Material „nur für Schüler/innen“ → Elternkonto sieht es nicht; Raum mit abgeschalteter Eltern-Einsicht → Elternkonto sieht ihn nicht.

**KUR-020** · P2 · Status: Ist — „Neu“-Marker: Material, das ein Konto noch nicht geöffnet hat, trägt „neu“ (verschwindet nach dem Öffnen; Tabelle `channel_item_views`); im Tab „Unterricht“ steht ein Zähler wie „2 Materialien noch nicht angesehen · 1 Stunde verpasst“.
Abnahme: neues Material → „neu“; nach Öffnen weg; Marker eines anderen Kontos unverändert.

**KUR-021** · P1 · Status: Ist — Material bearbeiten (Titel, Inhalt, Kennzeichen: Ersteller/in oder berechtigte Lehrkraft) und in einen anderen eigenen Kursraum kopieren (Dialog). Kopien sind im Ziel zunächst verborgen. Abschlussbedingungen und Freigaberegeln werden derzeit nicht mitkopiert (offen: KUR-048).
Abnahme: Kopie in Raum B → verborgen; fremde Lehrkraft ohne Recht ändert Original → 403.

**KUR-022** · P1 · Status: Ist — Klassenräume: alle Lehrkräfte der Klasse lesen und legen eigenes Material an; fremdes Material ändern, löschen, freigeben und fremde Abgaben sehen nur Ersteller/in, Klassenleitung und Kursraum-Verwaltung.
Abnahme: Fachlehrkraft B ändert Material von A im Klassenraum → 403; Klassenleitung ändert → erlaubt.

**KUR-023** · P3 · Status: offen — Schalter „gemeinsam pflegen“ je Klassenraum (erlaubt allen Lehrkräften der Klasse, fremdes Material zu ändern); Klassenseite mit Knopf „Kursraum der Klasse“; Lehrerkonto ohne verknüpfte Lehrkraft sieht den Hinweis, sich an das Sekretariat zu wenden.
Abnahme: Schalter an → B darf Material von A ändern; Klassenseite zeigt den Knopf; Konto ohne Lehrkraft-Verknüpfung sieht den Hinweis.

**KUR-024** · P2 · Status: Ist — Startseiten-Kacheln: Schüler/in „neues Material und fällige Aufgaben“ aus allen Räumen; Lehrkraft „Heute: Material freigeben“ (Stunden des nächsten Unterrichtstags mit gebundenem Material und Freigabe-Knopf, auch Klassenräume) und „Aufgaben mit Abgaben, die eine Rückmeldung brauchen“. Gesperrte Elemente (KUR-045) erscheinen dort nicht.
Abnahme: Lehrkraft mit Material zu morgen → Kachel zeigt die Stunde mit Freigabe-Knopf; Klick gibt frei.

### KUR.3 Pinnwand

**KUR-025** · P2 · Status: Ist — Pinnwand je Raum: Beiträge mit Text (verschlüsselt, Markdown/Formeln) und Anhängen (höchstens 10), genau eine Antwortebene, Lehrende können anheften, Verfasser/in bearbeitet eigene Beiträge, weiches Löschen. Schreiben/Antworten durch Schüler/innen folgt der Raumeinstellung (KUR-008). Neue Beiträge, Bearbeiten und Löschen werden ohne Inhalt protokolliert. [unklar: Löschen/Bearbeiten fremder Beiträge im alten System nicht ausgewiesen; Vorschlag: Verfasser/in und Lehrende des Raums]
Abnahme: Antwort auf eine Antwort → nicht möglich; Schüler bearbeitet fremden Beitrag → 403; jeder neue Beitrag erzeugt einen Protokolleintrag ohne Text.

### KUR.4 Aufgaben, Abgaben, Bewertung

**KUR-026** · P1 · Status: Ist — Aufgabe anlegen: Beschreibung, Frist mit Datum und Uhrzeit, Anhänge, Sichtbarkeit (KUR-016), Gruppenzuordnung, späte Abgabe zulassen (Standard) oder sperren, Bewertungsart (KUR-031). Wunsch: „bis zum so und so vielten, um so und so viel Uhr“. Im Kursraum steht „gestellt am …“ neben „bis …“. Hausaufgaben hängen am Kurs (nicht am Fach-Kürzel), erscheinen auch in Stundenplan/Kalender (Zuordnung zur Stunde und Darstellung: STP) und tragen ihren Link nur bei Zugriffsrecht (KUR-053).
Abnahme: Aufgabe mit Frist 14.11. 18:00 → Schüler sieht „gestellt am … bis 14.11.2026 18:00“; Kalender zeigt den Eintrag.

**KUR-027** · P0 · Status: Ist — Anonyme Abgabe: „die Hausaufgabenabgabe muss anonym sein, also kein Schüler soll die Hausaufgaben von anderen sehen.“ Schüler/innen sehen nur die eigene Abgabe (bzw. die der eigenen Gruppe); die Abgabenliste sehen nur Lehrende; der Dateizugriff folgt derselben Regel.
Abnahme: Schüler A ruft Abgabe oder Datei von B auf → 404; Lehrkraft der Aufgabe sieht alle Abgaben.

**KUR-028** · P1 · Status: Ist — Abgabe: Text und/oder Dateien (höchstens 20); ersetzen bis zur effektiven Frist, danach nur wenn späte Abgabe zugelassen (Kennzeichnung „verspätet“); zurückziehen, solange die Abgabe offen ist (nicht nach Bewertung, nicht nach Überarbeitung); jede Version bleibt gespeichert; Abgabetext verschlüsselt; der Schüler sieht danach den Status. Status: abgegeben · verspätet · bewertet · zurückgegeben. Das Wort des Betreibers „Einsenden“ meint Abgabe.
Abnahme: Abgabe vor Frist → „abgegeben“; Zurückziehen → Abgabe weg; nach Bewertung Zurückziehen → nicht möglich; nach Frist bei gesperrter später Abgabe → verständliche Ablehnung.

**KUR-029** · P1 · Status: Ist — Verspätung: Abgabe nach der effektiven Frist (Frist plus persönliche bzw. Gruppen-Verlängerung) wird „verspätet“; die Kennzeichnung bleibt nach der Bewertung sichtbar und wird nur bewusst entfernt; bei Überarbeitung gilt deren eigene Frist.
Abnahme: Frist 10:00, Abgabe 10:05 → „verspätet“; mit Verlängerung bis 11:00 → „abgegeben“.

**KUR-030** · P1 · Status: Ist — Abgabe-Übersicht („Bewertungstabelle“, nur Lehrende): Zeile je Schüler/in mit Status (abgegeben, verspätet, fehlt, bewertet, Überarbeitung), Abgabezeit, Punkte/Note, geltender Frist, Gruppe und Hinweis „NTA“ (Nachteilsausgleich, nur Hinweis aus dem Förderbereich); Filter. Die Fachlehrkraft sieht in ihrer Stunde „x von y abgegeben“. „fehlt“ gilt nach Ablauf der effektiven Frist ohne Abgabe [unklar: Auslöser im alten System nicht beschrieben]. Schüler ohne Konto: „kein Konto“.
Abnahme: 28 Schüler, 25 abgegeben → „25 von 28 abgegeben“; Filter „fehlt“ zeigt nach Fristablauf die drei übrigen.

**KUR-031** · P1 · Status: Ist — Bewertungsart je Aufgabe, vier Werte: Freitext-Note (nur Text) · Punkte (mit Höchstpunkten) · Raster (Kriterien mit Stufen und Punkten) · Leitfaden (Kriterien mit Freitext und Höchstpunkten). Summe, Prozent und Note werden berechnet; die Note ist ein Vorschlag und überschreibbar. Keine Gewichtung einzelner Kriterien (Summe der Punkte bzw. Stufen).
Abnahme: Raster mit drei Kriterien (Stufen 0–4) → Summe/Prozent/Notenvorschlag; Lehrkraft überschreibt die Note → gespeichert wird die überschriebene.

**KUR-032** · P1 · Status: Ist — Notenschlüssel (kein schulweiter Schlüssel): je Aufgabe oder Raster-Vorlage wählbar. Voreinstellung „Noten 1–6“: Note 1 ab 92 %, 2 ab 81 %, 3 ab 67 %, 4 ab 50 %, 5 ab 30 %, darunter 6; alternativ „Punkte 15–0“ oder eigene Prozentgrenzen. Tendenznoten: „2+“ ergibt als Zahl 1,7. Auswertbare Notentexte: „80 %“, „12/15“, „9 von 12“, „2+“, „2,5“, „2-3“; „12 Punkte“ ohne Maximum ist nicht auswertbar. Noten werden verschlüsselt gespeichert.
Abnahme: 46 von 50 Punkten (92 %) → Vorschlag 1; 91 % → 2; „2+“ → Zahl 1,7.

**KUR-033** · P1 · Status: Ist — Raster-Vorlagen: privat je Lehrkraft, über alle ihre Kursräume nutzbar; beim Zuweisen wird eine Kopie übernommen (spätere Änderungen an der Vorlage ändern keine zugewiesene Aufgabe und keine ausgefüllte Bewertung); nach der ersten Bewertung mit dem Raster nicht mehr änderbar. Schüler/innen sehen die Kriterien vor der Abgabe und nach der Bewertung das ausgefüllte Raster; Eltern das Raster nur bei Freigabe; die Freitext-Note unabhängig davon.
Abnahme: Vorlage nach Zuweisung ändern → Aufgabe unverändert; Raster nach erster Bewertung ändern → abgelehnt; Elternkonto ohne Freigabe sieht das Raster nicht.

**KUR-034** · P1 · Status: Ist — Rückmeldung: Text und Anhänge (höchstens 10), Punkte bzw. Note, Zeitpunkt wird gespeichert; Rückmeldung und Note verschlüsselt; Benachrichtigung „Abgabe bewertet“ ohne Note und Rückmeldung im Text; nur die verantwortliche Lehrkraft bewertet.
Abnahme: Rückmeldung → Schüler erhält Benachrichtigung ohne Note; Mitschüler ruft Note ab → 404.

**KUR-035** · P1 · Status: Ist — „Überarbeitung anfordern“ (Status „zurückgegeben“, optional neue Frist): Abgabe samt Rückmeldung und Note wird als Version festgehalten, die nächste Version geöffnet. Rückmeldung und Note der letzten Version bleiben während der Überarbeitung sichtbar, werden bei erneuter Abgabe geleert und stehen weiter in der alten Version. Dateien früherer Versionen werden nie gelöscht. Danach kein Zurückziehen mehr; „zurückgegeben“ zählt nicht als bewertet. Einzelanpassungen einer Gruppenbewertung werden dabei mitversioniert (das alte System tat es nicht: Datenverlust-Gefahr).
Abnahme: Überarbeitung anfordern → Version 1 lesbar, Version 2 offen; erneute Abgabe → Version 1 behält Feedback; Dateien beider Versionen abrufbar.

**KUR-036** · P1 · Status: Ist — Fristverlängerung je Schüler/in oder je Gruppe (genau eines von beiden), neue Frist, Begründung verschlüsselt, löschbar. Der Dialog zeigt den Nachteilsausgleich-Hinweis mit Art und Minuten, ohne Diagnose.
Abnahme: Verlängerung für X bis 11:00 → Abgabe 10:50 von X „abgegeben“, andere um 10:50 „verspätet“; Hinweis enthält keine Diagnose.

**KUR-037** · P1 · Status: Ist — Noten im Kursraum: die Lehrkraft trägt ein; Schüler/innen und Eltern sehen ihre Noten (auch Hausaufgaben-Noten), Mitschüler und Fremde nicht. Bewertete Abgaben (aktuelle Version) stehen dem Notenbuch zur Übernahme bereit (Punkte, Höchstpunkte, Prozent, Note als Text und als Zahl, Zeitpunkt, Versuch, verspätet, Gruppe; eine Gruppenbewertung gilt je Person); die Lehrkraft übernimmt selbst (NOT). Eine endgültig gelöschte Aufgabe verschwindet auch im Notenbuch.
Abnahme: bewertete Abgabe erscheint in der Übernahmeliste des Notenbuchs; Aufgabe endgültig löschen → Eintrag weg.

**KUR-038** · P2 · Status: offen — „Hausaufgaben-Übersicht“ für Eltern und Schüler: eine Liste mit Fälligkeit aus Klassenbuch und Kursräumen (Zusammenführung vorhandener Daten). Zweck der Kästchen bei Material/Hausaufgabe im alten Dialog war unklar und entfällt; der Zweck „Abgabe möglich“ wird ausdrücklich beschriftet.
Abnahme: Schüler sieht alle fälligen Aufgaben aller Räume in einer Liste, sortiert nach Frist; fremde Aufgaben fehlen.

**KUR-039** · P3 · Status: offen — Aufgaben-Erweiterungen (Wettbewerbs-Lücken): anonym bewerten, Bewertung als Entwurf und Freigabe, Sammelaktionen, Notizen für Lehrkräfte, Abgaben als ZIP, PDF-Anmerkungen im Browser, automatischer Notenabzug bei Verspätung.
Abnahme: je Funktion eigener Test; bis dahin nicht vorhanden.

### KUR.5 Gruppen

**KUR-040** · P1 · Status: Ist — Gruppeneinteilungen im Reiter „Gruppen“ (nur Lehrende): Einteilung (z. B. „Projektgruppen“) mit beliebig vielen Gruppen; Mitglieder von Hand oder automatisch (zufällig oder alphabetisch, nach Gruppenzahl oder Gruppengröße, wahlweise alle neu oder nur Nicht-Eingeteilte); je Einteilung höchstens eine Gruppe je Person; nur Teilnehmende mit eigenem Konto. Hat eine Person mehrere Konten, entscheidet eine ausdrückliche Zuordnung, nicht „kleinste Kennung“ (Fehler des alten Systems).
Abnahme: Einteilung „zufällig, 4 Gruppen“ mit 28 Personen → 4 Gruppen à 7; Person in zwei Gruppen derselben Einteilung → abgelehnt; die Browser-Prüfung des Reiters „Gruppen“ (bisher nur Seitentext und Tests) ist Teil der Abnahme.

**KUR-041** · P1 · Status: Ist — Gruppenabgabe (Schalter an der Aufgabe): jedes Mitglied hat eine Abgabe-Zeile mit gleichem Inhalt; jede Änderung eines Mitglieds gilt für alle; eine Bewertung gilt für die Gruppe, „Nur diese Person“ legt eine Einzelanpassung an, die bei späteren Gruppenbewertungen erhalten bleibt, außer man wählt „überschreiben“. Nach der ersten Abgabe lässt sich die Gruppenabgabe nicht mehr umstellen. Wechselt ein Mitglied die Gruppe, fällt seine Zeile weg; die Dateien bleiben bei der Gruppe. Eltern anderer Gruppenmitglieder können Gruppendateien nicht öffnen.
Abnahme: Mitglied A ändert Text → B sieht ihn; Einzelanpassung für C bleibt nach neuer Gruppenbewertung; Umstellen nach erster Abgabe → abgelehnt.

**KUR-042** · P1 · Status: Ist — Sichtbarkeit nach Gruppe: Material, Aufgaben und Ordner lassen sich auf Gruppen beschränken („Nichts angekreuzt = für alle.“); Lehrende sehen immer alles; die Beschränkung wirkt in allen Teilnehmenden-Ansichten und beim Dateizugriff.
Abnahme: Material nur für Gruppe 2 → Mitglied von Gruppe 1 sieht es weder in der Liste noch per Direktaufruf; Lehrkraft sieht es.

### KUR.6 Lernfortschritt und bedingte Freigabe

**KUR-043** · P1 · Status: Ist — Abschlussbedingung je Element (Material oder Aufgabe), Dialog „Abschluss & Bedingungen“ (Häkchen-Symbol an der Zeile), nur für Lehrende (channels.manage). Modi: `manual` „Selbst abhaken“ · `viewed` „Angesehen“ · `submitted` „Abgegeben“ · `graded` „Bewertet“ · `passed` „Bestanden“ (Mindestprozent; ohne Prozentwert in der Bewertung gilt Note 4 oder besser). „Abgegeben“, „Bewertet“, „Bestanden“ gibt es nur für Aufgaben und Material mit „Abgabe möglich“; „zur Überarbeitung zurückgegeben“ zählt nicht als bewertet. Ein Element ohne Regel wird nicht verfolgt. Massenbearbeitung von Abschlüssen (Obergrenze je Aufruf [unklar: Wert]). Schüler/innen haken nur eigene „manual“-Elemente ab; Eltern und Aufsicht nichts.
Abnahme: „Bestanden ab 50 %“: Abgabe mit 60 % → erledigt, mit 40 % → offen; „Selbst abhaken“: Schülerin setzt Häkchen → erledigt; Elternkonto setzt Häkchen → 403.

**KUR-044** · P1 · Status: Ist — Anzeige: Häkchen „Erledigt“ bzw. Symbol am Material; im Kopf des Raums ein Fortschrittsbalken „x von y erledigt“ (nur wenn Elemente verfolgt werden); Reiter „Fortschritt“ für Lehrende als Tabelle Schüler/in × Elemente mit Filtern (Name, Klasse, „offen bei …“, „nur mit offenen Elementen“) und CSV-Export (Semikolon, UTF-8 mit BOM, Schutz vor Formeln in Zellen); „Mein Fortschritt“ für Lernende. In Klassenräumen sind Abgabe-Zellen fremder Aufgaben ausgeblendet (Schloss-Symbol). Schüler ohne Konto erscheinen als „kein Konto“.
Abnahme: 10 von 12 Elementen erledigt → Balken „10 von 12“; CSV beginnt für „=1+1“ im Namen mit entschärftem Zeichen; Fachlehrkraft B sieht im Klassenraum keine Abgabe-Zellen von Aufgaben der Lehrkraft A.

**KUR-045** · P1 · Status: Ist — Bedingte Freigabe (Verfügbarkeitsregel) je Element: Bedingungen „anderes Element erledigt oder bestanden“, „Punkte mindestens x %“, „Note x oder besser“, „Mitglied einer Gruppe“, „Datum ab/bis“, „Zeitfreigabe erreicht“; Verknüpfung UND/ODER, verschachtelbar (Untergruppen). Gesperrte Elemente zeigen nur Titel und „Verfügbar, sobald …“; Inhalt, Dateien, Link, Abgabe und „angesehen“ sowie der Dateizugriff sind serverseitig gesperrt (403), nicht nur ausgeblendet. Ohne Gruppen entfällt die Gruppen-Bedingung.
Abnahme: B frei erst, wenn A erledigt: vorher zeigt B „Verfügbar, sobald …“ und Direktabruf der Datei → 403; nach Erledigung von A → B frei; Regel „A erledigt ODER Datum erreicht“ → frei am Datum.

**KUR-046** · P0 · Status: Ist — Fortschritt für Eltern: nur wenn die Lehrkraft die Raumeinstellung „Eltern sehen den Fortschritt ihres Kindes“ einschaltet; dann nur „erledigt“ oder „offen“, nie Noten oder Abgaben; bei volljährigen Schüler/innen nur mit Freigabe im Bereich „kursraeume“.
Abnahme: Einstellung aus → Elternkonto sieht keinen Fortschritt; an → nur erledigt/offen; Volljähriger ohne Freigabe → nichts.

**KUR-047** · P2 · Status: Ist — Erweiterbarkeit: andere Bereiche (Selbsttest, Umfrage, Abstimmung, künftige) melden sich beim Fortschritt als Elementart an, ohne dass der Fortschrittsbereich geändert wird. Je Art: Typ und Bezeichnung, erlaubte Abschlussbedingungen, Liste der Elemente eines Raums (ohne gelöschte), Fakten je Konto (angesehen, abgegeben, bewertet, Punkteprozent, Note) und optional Ersteller sowie sichtbare Elemente je Konto. Danach erscheint das Element in Liste, Balken und Tabelle und ist als Voraussetzung in Freigaberegeln nutzbar (`completed`, `score`, `note`; für Lernaktivitäten `selftest_done`, `survey_done`, `poll_done`). Beim endgültigen Löschen eines Elements werden Regeln und Häkchen mit entfernt.
Abnahme: Selbsttest als Voraussetzung eines Materials → Material wird nach beendetem Versuch mit erreichter Grenze frei; Test endgültig löschen → Regel und Häkchen verschwinden.

**KUR-048** · P2 · Status: offen — (a) Beim Kopieren von Material oder Räumen werden Abschlussbedingungen und Freigaberegeln mitkopiert. (b) Benachrichtigung an Lernende, wenn ein Element durch eine Regel frei wird (bisher meldet nur sofort sichtbares Material etwas). (c) Verbindung zu Kompetenzen (Zuordnung im Kursraum, siehe NOT). (d) Die Fortschrittstabelle zeigt je Schüler/in „gesperrt“ oder „frei“.
Abnahme: (a) Kopie trägt Regel; (b) Element wird frei → Benachrichtigung einmal je Konto; (c) Kompetenz am Element wählbar; (d) Tabellenzelle zeigt „gesperrt“.

**KUR-049** · P3 · Status: offen — Abschluss- und Freigaberegeln für Abstimmungen und Umfragen sind über die normale Bedienung erreichbar (im alten System nur intern, ohne Schnittstelle).
Abnahme: Regel „Umfrage beantwortet“ an einem Material setzbar; Material bleibt bis zur Antwort gesperrt.

### KUR.7 Tab „Unterricht“

**KUR-050** · P1 · Status: Ist — Tab „Unterricht“, Liste: „Es sollen wirklich nur die Unterrichtsstunden dargestellt werden, die stattgefunden haben.“ Ausgefallene Stunden fehlen, verlegte stehen am Tag des echten Stattfindens. Klick auf eine Stunde führt zu Unterrichtsmaterial und Hausaufgaben dieses Tages („damit man alle Daten kriegen kann“); Material- und Hausaufgaben-Link stehen direkt an der Stunde. Unterrichtsmaterial mit Datum erscheint am Datum der Stunde (für Nachholende). Lehrende sehen zusätzlich Thema und Hausaufgabentext aus dem Klassenbuch. Die Stunden-Quelle ist das Klassenbuch/der Plan (KLB, STP).
Abnahme: Stunde am Fr entfällt → fehlt in der Liste; Mo-Stunde auf Mi verlegt → Eintrag unter Mi; Klick → Material und Hausaufgabe des Tages.

**KUR-051** · P1 · Status: Ist — Tab „Unterricht“ für Schüler/innen und Eltern: pro Stunde nur ein roter Hinweis bei „krank“, „beurlaubt“ oder „gefehlt“ (Text zusätzlich zur Farbe), Material klickbar, Hausaufgaben als Link (z. B. „HA 1“), versäumte Stunden öffnen sich automatisch; Klick auf eine rote Stunde führt zu den Fehlzeit-Details (Familie). Thema, Hausaufgabentext und Abwesenheitsgrund bekommen Schüler/innen und Eltern vom Server gar nicht (nicht nur ausgeblendet). Es wird nur die eigene Anwesenheit gezeigt.
Abnahme: Schülerin krank gemeldet → Stunde rot mit Text „krank“; API-Antwort enthält weder Thema noch Hausaufgabentext noch Grund; fremde Anwesenheit nicht abrufbar (404).

**KUR-052** · P2 · Status: offen — Orange-Markierung: Wunsch (10-12 15:35): „grün anwesend, orange zu spät oder früher gegangen, rot gefehlt“. Spätere Regel (10-12 17:18): zu spät/früher gegangen zählt im Kursraum nicht als Fehlen. [unklar: der Betreiber hat den Widerspruch nicht entschieden] Bis zur Klärung: keine Orange-Markierung im Kursraum, Hinweis nur bei Fehlen.
Abnahme: Schülerin kommt 10 Minuten zu spät → Stunde ohne roten Hinweis; Klärung des Betreibers wird als Entscheidung festgehalten.

**KUR-053** · P1 · Status: Ist — Hausaufgaben-Link (im Stundenplan/Kalender und im Tab „Unterricht“) erscheint nur, wenn der Betrachter den Kursraum öffnen darf (Sekretariat und fremde Lehrkräfte sahen früher einen toten Link); er führt direkt zur Aufgabe (Adressparameter `/kursraeume/:id?tab=&aufgabe=&ordner=`).
Abnahme: Sekretariatskonto sieht keinen Hausaufgaben-Link; Lehrkraft des Raums folgt dem Link → Aufgabe öffnet ohne Fehler.

### KUR.8 Tab „Klasse“ (Klassenräume)

**KUR-054** · P1 · Status: Ist — Erster Tab und Startansicht jedes Klassenraums: „Es soll einen Kursraum geben, wo klassenspezifische Sachen drin stehen … Informationen zu Elternabenden … regulären Stundenplan und anderen Plänen … allgemeine Informationen … die auch die Eltern gerne wissen würden.“ Inhalt: Regelplan, Termine/Elternabende, Infokarten, Kontakte (KUR-055 bis KUR-058) und „Fehlzeiten & Meldungen“. Sichtbarkeit: Schüler/innen und Eltern sehen nur die eigene Klasse, Eltern nur lesend; „Fehlzeiten & Meldungen“ nur Lehrkräfte und Schulleitung.
Abnahme: Schülerin der 5a ruft Klasse 5b auf → 404; Elternkonto sieht den Tab „Klasse“ ohne „Fehlzeiten & Meldungen“ und kann nichts ändern.

**KUR-055** · P1 · Status: Ist — Regelstundenplan der Klasse als Wochenraster mit Wochenauswahl, nur lesen, über das gemeinsame Tage×Stunden-Raster; Links zu „Stundenplan mit Änderungen“ und zum Klausurplan (nur Link).
Abnahme: Wochenwahl wechselt die Woche; Raster ist dasselbe wie im Stundenplan; kein Bearbeiten möglich.

**KUR-056** · P1 · Status: Ist — Termine und Elternabende der Klasse oder des Jahrgangs: die Klassenleitung legt einen Elternabend an (Titel vorbelegt, Datum, Zeit, Ort); er erscheint im Schulkalender (STA).
Abnahme: Elternabend anlegen → Eintrag im Klassen-Tab und im Schulkalender; Fachlehrkraft ohne Klassenleitung kann ihn nicht anlegen.

**KUR-057** · P1 · Status: Ist — Infokarten: angeheftet, sortierbar, mit Text, Links und Anhängen; jede Lehrkraft der Klasse legt an, bearbeiten dürfen nur Autor/in und Klassenleitung; Infokarten erscheinen nicht unter „Material“.
Abnahme: Fachlehrkraft B legt Karte an; Fachlehrkraft C bearbeitet sie → 403; Klassenleitung bearbeitet → erlaubt.

**KUR-058** · P1 · Status: Ist — Kontakte: Klassenleitung zuerst, dann Fachlehrkräfte mit Namens-Tooltip und Knopf „Nachricht schreiben“ (öffnet Nachrichten mit vorbelegtem Empfänger); keine E-Mail-Adressen.
Abnahme: Klick auf „Nachricht schreiben“ → Verfassen mit der Lehrkraft als Empfänger; die API liefert keine E-Mail-Adresse.

**KUR-059** · P3 · Status: offen — Anhänge an Infokarten auch nachträglich; Klausurplan als eigene Liste im Klassen-Tab (bisher nur Link).
Abnahme: Anhang zu bestehender Karte hinzufügbar; Klausurliste der Klasse im Tab sichtbar.

### KUR.9 Papierkorb

**KUR-060** · P1 · Status: Ist — Löschen von Material, Aufgaben und Ordnern legt sie in den Papierkorb (Dialog im Kopf des Raums). Wiederherstellen bringt Abgaben, Dateien und Regeln zurück; fehlt der Elternordner, landet der Eintrag oben im Baum; ein gleichnamiger Ordner bekommt „(2)“. Endgültig löschen einzeln und „Papierkorb leeren“. Gelöschte Elemente sind in allen normalen Abfragen unsichtbar. Zusammen gelöschte Elemente tragen eine gemeinsame Gruppe (`trash_group`).
Abnahme: Ordner mit Aufgabe löschen → beide im Papierkorb; Wiederherstellen → Abgaben und Regeln wieder da; Zielordner gleichnamig vorhanden → „(2)“.

**KUR-061** · P1 · Status: Ist — Frist und Rechte: Aufbewahrung 30 Tage, Schuleinstellung `trash_retention_days` (zulässig 1–365; erreichbar unter Planung → Einstellungen → „Kursräume“ und im Papierkorb mit settings.edit); der stündliche Wartungslauf löscht Abgelaufenes endgültig samt Abgaben, Dateien, Regeln und Häkchen. Wiederherstellen und endgültig löschen: Recht channels.trash und zusätzlich Bearbeitungsrecht am Material (Klassenräume: nur eigenes); Schulleitung und Aufsicht nur lesend. [unklar: die Routenliste nennt für die Papierkorb-Liste zusätzlich settings.edit]
Abnahme: Eintrag älter als 30 Tage → nach dem nächsten Lauf endgültig weg (inkl. Datei); Frist 0 oder 400 → abgelehnt; Schülerkonto → kein Papierkorb.

### KUR.10 Lernaktivitäten

**KUR-062** · P1 · Status: Ist — Tab „Tests & Umfragen“ (keine eigene Seite) mit Bereichen Abstimmungen, Umfragen, Selbsttests und – nur Lehrende – Fragensammlung; angelegt über „Neu“ (Material, Aufgabe, Test oder Umfrage). Anlegen, ändern, auswerten, löschen: Lehrende des Raums (channels.manage); Teilnehmende stimmen ab, antworten und testen; Eltern lesen nur Abstimmungen; Aufsicht liest Abstimmungen; in Klassenräumen ändern und werten nur Ersteller/in, Klassenleitung und Kursraum-Verwaltung. Ergebnisse anonymer Aktivitäten ohne Berechtigung: 404 statt 403.
Abnahme: Schüler öffnet Auswertung einer Umfrage ohne Freigabe → 404; Fachlehrkraft B ändert Umfrage von A im Klassenraum → 403.

**KUR-063** · P1 · Status: Ist — Abstimmung: Frage und Antwortoptionen (Standard 2; Mindest-/Höchstzahl [unklar: Werte]), eine oder mehrere Antworten (optional Höchstzahl), anonym oder namentlich; Ergebnissichtbarkeit sofort · nach der eigenen Stimme · nach dem Ende; Enddatum; vorzeitig beenden; Ergebnis als Balken. Namentlich: Stimme änderbar, Namen sehen alle, die das Ergebnis sehen; Eltern nie Namen. Anonym: Stimme nicht änderbar. Frage und Antworten im Kursraum serverseitig verschlüsselt. Im Chat dieselbe Darstellung (NAC-021).
Abnahme: anonyme Abstimmung → zweite Stimme/Änderung abgelehnt; namentliche → Änderung möglich; Elternkonto sieht Balken, keine Namen.

**KUR-064** · P0 · Status: Ist — Schutz der Anonymität bei Abstimmungen: Je Teilnahme wird nur eine Prüfnummer gespeichert (HMAC-SHA256 aus einem vom Server-Geheimnis `SM_SECRET_KEY` abgeleiteten Schlüssel über Abstimmung und Konto), das Konto bleibt leer, es entsteht keine Stimmzeile mit Konto; pro Antwort nur ein Zähler, atomar hochgezählt (nie lesen-und-schreiben). Teilnahme wird nie über das Konto geprüft. Protokoll `poll.vote` bei anonymen Abstimmungen ohne Konto und ohne IP, mit `anonymous: true` – Konto oder IP dürfen nie ergänzt werden. Wechsel von `SM_SECRET_KEY` macht Prüfnummern ungültig (erneutes Abstimmen offener anonymer Aktivitäten bewusst hingenommen). Der Hilfetext erklärt das ohne Versprechen wie „niemand kann …“.
Abnahme: Datenbankauszug einer anonymen Abstimmung enthält weder Konto noch Zuordnung Stimme↔Person; 50 gleichzeitige Stimmen → Zähler exakt 50; Protokolleintrag ohne Konto/IP.

**KUR-065** · P1 · Status: Ist — Umfrage (Feedback-Fragebogen) als Erweiterung des Formular-Baukastens (FOR-004), keine zweite Formularwelt. Fragetypen: Auswahl, Mehrfachauswahl, Ja/Nein, Skala 1–5 (mit Beschriftung der Enden), Freitext, kurzer Text, Zahl. Nicht übernommen: Einreichungen, Eingang, Genehmigung. Zielgruppe im Kursraum; anonym oder namentlich; Status `entwurf` → `offen` → `geschlossen`, optional Schlusszeit; Schalter „Ergebnisse für Schüler/innen sichtbar“. Fragen und Anonymität sind nach der ersten Antwort gesperrt. Auswertung je Frage (Balken, Mittelwert, Texte) und CSV (Semikolon, BOM, Formelschutz); Teilnehmende sehen die Auswertung nur nach dem Ende und bei Freigabe, sonst 404. Namentlich: eine Zeile je Person mit Name und Datum. Umfragen außerhalb eines Kursraums: KUR-073.
Abnahme: nach erster Antwort Frage ändern → abgelehnt; Auswertung vor Ende als Schülerin → 404; CSV-Zelle „=HYPERLINK(…)“ wird entschärft.

**KUR-066** · P0 · Status: Ist — Anonyme Umfragen sind wirklich anonym (Teilnehmer werden nicht mehr gespeichert): Antworten ohne Konto; Zeitstempel nur als Tagesdatum und nie ausgegeben; Teilnahme nur als Prüfnummer wie bei Abstimmungen; `survey.respond` ohne Konto und IP; Einzelantworten ohne Datum in zufälliger Reihenfolge; Freitexte je Frage getrennt gemischt, damit sich Texte verschiedener Fragen nicht über die Position einer Person zuordnen lassen; CSV nur gruppiert (`Frage;Antwort;Anzahl` je Frage mit Zählungen, Mittelwert, kleinstem/größtem Wert, Freitexten), keine Zeile je Person, kein Datum. In der Personen-Auskunft erscheint die Teilnahme als „(anonym gespeichert)“, die Antworten bleiben bei Löschung der Person erhalten. [unklar: Mindestteilnehmerzahl für eine Auswertung ist nicht festgelegt]
Abnahme: Auswertung/CSV/Datenbank enthalten keine Person und kein Datum; Reihenfolge der Freitexte ändert sich zwischen zwei Abrufen; Abruf der Personen-Auskunft zeigt „(anonym gespeichert)“.

**KUR-067** · P1 · Status: Ist — Fragensammlung je Kursraum (nur Lehrende): Frage samt Lösung verschlüsselt, Punkte je Frage, Kategorie; Fragetypen Einfachauswahl, Mehrfachauswahl, Wahr/Falsch, Lückentext (Platzhalter `___`), Zuordnung, Zahl mit Toleranz; Fragen in andere eigene Kursräume kopieren; Import und Export im GIFT-Format (Auswahl, Wahr/Falsch, Kurzantwort als Lückentext, Zuordnung, Zahl), Obergrenze je Import [unklar: Wert]. Nicht exportierbare Fragen (z. B. Lückentext mit mehreren Lücken) werden ausdrücklich gemeldet, nie still übersprungen. Moodle-XML ist nicht vorgesehen (KUR-073).
Abnahme: Export einer Sammlung mit Mehrlücken-Frage → Meldung nennt die Frage; Import einer GIFT-Datei mit Zahl-Frage → Toleranz übernommen.

**KUR-068** · P1 · Status: Ist — Selbsttest anlegen: Fragenauswahl aus der Sammlung (Obergrenze [unklar: Wert]), Anzahl Versuche, Zeitlimit in Minuten, Fragen mischen (Standard aus), Antworten mischen (Standard ein; fester Startwert je Versuch), Rückmeldung sofort je Frage (Standard aus; danach ist die Antwort gesperrt), Anzeige nach der Abgabe `none` · `score` · `full` (Standard `full`), Bestehensgrenze in Prozent, Beginn und Ende; Status `entwurf` → `offen` → `geschlossen`. Antworten werden beim Eingeben gespeichert. Lehrkräfte können probieren; diese Versuche zählen nicht in der Auswertung.
Abnahme: Test mit 2 Versuchen und 20 Minuten → dritter Start abgelehnt; Zeitablauf → Versuch endet mit gespeicherten Antworten; Lehrkraft-Probeversuch fehlt in der Auswertung.

**KUR-069** · P0 · Status: Ist — Selbsttest-Durchführung und Schutz: Bewertung nur auf dem Server mit dem Abbild der Fragen zum Start des Versuchs (spätere Änderungen an Fragen wirken nicht); die Lösung geht vor der Abgabe nie an den Browser. Mehrfachauswahl mit Teilpunkten (Treffer minus Fehler, geteilt durch Anzahl Richtiger, nie negativ); Lückentext: exakte Antwort, mehrere zulässige Antworten, Groß-/Kleinschreibung wählbar, Teilpunkte je Lücke; Zahl mit Toleranz (Komma erlaubt). Je Person und Test höchstens ein laufender Versuch, in der Datenbank abgesichert (Versuchsnummer je Test und Konto eindeutig); bei gleichzeitigem Start erhält der Verlierer den laufenden Versuch zurück, nie einen zweiten. Abgelaufene Versuche werden beim nächsten Zugriff (Start, Abruf, Auswertung, Notenliste) mit den gespeicherten Antworten abgeschlossen und dem Notenbuch angeboten. [unklar: Berechnung der Versuchsfrist bei gleichzeitiger Testschlusszeit]
Abnahme: Netzwerkprotokoll vor Abgabe enthält keine Lösung; zwei parallele Starts → ein Versuch; Fragenänderung während laufendem Versuch → Versuch unverändert bewertet.

**KUR-070** · P2 · Status: Ist — Ergebnisse: Übersicht je Schüler/in und Frage, Fragenstatistik, einzelne Versuche ansehen, Noten, CSV-Export. Ergebnisse werden dem Notenbuch gemeldet (bester Versuch, Punkte von Höchstpunkten; nur Kursraum eines Kursteils; Löschen nimmt zurück; Übernahme bleibt Entscheidung der Lehrkraft, NOT). Abstimmungen, Umfragen und Selbsttests melden Status je Element (erledigt, Punkte, Höchstpunkte, Prozent, bestanden) an den Fortschritt (KUR-047).
Abnahme: zwei Versuche (60 %, 80 %) → Notenbuch erhält 80 %; Test löschen → Meldung zurückgenommen.

**KUR-071** · P2 · Status: Ist — Mathe-Formeln: `$…$` (im Text) und `$$…$$` (Block) in Markdown-Ansichten (Material, Aufgaben, Selbsttest, Pinnwand, Klasseninfos). Formelsatz lokal gebündelt (kein externer Dienst, keine CDN), wird erst beim ersten Text mit Formel nachgeladen; Quelltext wird nie als HTML eingefügt; Größen- und Makro-Grenzen; Fehler erscheinen als Quelltext; „5 $ und 6 $“ bleibt Text, `\$` maskiert ein Dollarzeichen. Nachrichten und Chats zeigen keine Formeln (NAC-016).
Abnahme: „$x^2$“ wird gesetzt; „5 $ und 6 $“ bleibt unverändert; ungültige Formel → Quelltext sichtbar; Netzwerkprotokoll ohne Fremdhost.

**KUR-072** · P1 · Status: Ist — Bewusst NICHT nachbauen (Betreiber widersprach nicht): volles Quiz-System, SCORM, Plagiatsprüfung, Videokonferenz, Bezahlfunktionen, Plugin-Marktplatz, Blog/Notizen/Bewertung von Beiträgen, Gast- und Selbstregistrierung, KI-Assistenz; Quiz und H5P nur als Link. Eine Anbindung externer Werkzeuge (LTI) ist ein späterer Wunsch (KUR-081).
Abnahme: keine dieser Funktionen in Menü oder Schnittstelle; Link-Material auf eine Quiz-Adresse ist möglich.

**KUR-073** · P3 · Status: offen — Lücken der Lernaktivitäten: Moodle-XML-Import; Fragen mit Bildern oder Dateien; Umfragen außerhalb eines Kursraums (z. B. für einen Elternabend); Medienplayer; Forum mit Threads und Abo; Wiki/Glossar/mehrseitiges Buch mit Versionen; Open-Badges-Export; Umfragen im Chat über Abstimmungen hinaus; Selbsteinschreibung mit Schlüssel für AG/Wahlangebote.
Abnahme: je Funktion eigener Test; bis dahin nicht angeboten.

**KUR-074** · P0 · Status: offen — Elternfreigabe in den Lernaktivitäten vollständig prüfen: Eltern lesen nur Abstimmungen und nie Namen; Selbsttest-Ergebnisse und Umfrage-Auswertungen sind für Eltern nur nach demselben Bereichs-Freigabeschema wie Noten/Abgaben sichtbar (volljährige Kinder nur mit Freigabe). [unklar: der Umfang der Eltern-Leserechte ist im alten System nicht festgelegt]
Abnahme: Elternkonto volljähriges Kind ohne Freigabe → keine Lernaktivität; mit minderjährigem Kind → nur Abstimmungs-Balken ohne Namen; Selbsttest-Ergebnis des Kindes nach festgelegter Regel.

### KUR.11 Querschnitt: Sicherheit, Datenschutz, Betrieb

**KUR-075** · P0 · Status: Ist — Fremde Daten liefern 404 („nicht gefunden“, nicht „verboten“) in allen Kursraum-Routen (Räume, Elemente, Ordner, Gruppen, Abgaben, Dateien, Klassentermine, Lernaktivitäten, Papierkorb, Fortschritt); 403 nur bei fehlender Lehrkraft-Zuordnung oder rollenbedingt innerhalb des eigenen Raums. Jede neue Route mit Fremd-Kennung gehört in den Querschnittstest.
Abnahme: Test mit mindestens 40 Fällen aus Sicht fremder Schüler/innen, Lehrkräfte und Eltern; fremder, aber vorhandener Raum → 404 (nicht 403).

**KUR-076** · P0 · Status: Ist — Protokoll (ohne Inhalte): Ordner anlegen/umbenennen/verschieben/umsortieren, Elemente und Ordner löschen (`channel_item.delete`, `channel_folder.delete`), Papierkorb (`channel_trash.restore`, `.purge`, `.empty`), Abschlussregeln (`completion.rule`, `.bulk`, `.mark`), Freigaberegeln (`availability.rule`), Pinnwand-Beiträge, Lernaktivitäten (`poll.*`, `survey.*`, `question.*`, `selftest.*`, nie mit gewählten Antworten). Ausnahmen ohne Protokoll (Zustimmung des Betreibers steht aus): Zwischenspeichern von Selbsttest-Antworten.
Abnahme: jede schreibende Kursraum-Aktion erzeugt genau einen Eintrag ohne Text; Selbsttest-Zwischenspeichern erzeugt keinen.

**KUR-077** · P0 · Status: Ist — Verschlüsselung und Rollenschranken: Material-/Aufgabentext, Pinnwand, Abgaben, Rückmeldungen, Noten, Raster, Fristbegründungen, Fragen, Antworten, Versuche sind serverseitig verschlüsselt (`_enc`-Spalten, Bindung an Zeile und Feld). Die Zuschauer-Rolle hat keine Lernstände; Administration und Schulleitung sehen keine Abgaben-Inhalte und Noten (KUR-007).
Abnahme: Datenbankauszug zeigt nur Chiffrate; Zuschauerkonto ruft Fortschritt/Abgaben ab → 403/404 bzw. leer.

**KUR-078** · P0 · Status: Ist — Löschfristen nach Austritt einer Person (DAT): Abgaben/Rückmeldungen 90 Tage, Selbsttests/Abstimmungen/Umfragen 90 Tage (anonym gespeicherte Umfrage-Antworten bleiben), Fortschritt und Kursraum-Nutzung (Häkchen, Lesestände, Gruppen- und Zusatzmitgliedschaften, Fristverlängerungen) 90 Tage, hochgeladene Dateien 30 Tage. Kursraum-Inhalte (Material, Ordner, Beiträge) sind als Datenart nicht geführt und der Verbleib bei Kontolöschung ungeprüft [unklar]; Aufbewahrung von Abgaben und Räumen nach Ende des Kurses ist nicht beschrieben [unklar].
Abnahme: Person tritt aus → nach 90 Tagen sind Abgaben und Versuche gelöscht, anonyme Umfrage-Antworten bleiben; Löschprotokoll nennt Datenart und Anzahl ohne Inhalt.

**KUR-079** · P2 · Status: Ist — Bedienung: Live-Aktualisierung je Kursraum und für die Liste, Kennungen eindeutig (Raum 5 trifft nie Raum 50); Handy-Ansicht 390 px ohne waagerechten Bildlauf, Tabellen im eigenen Rahmen; Hilfe nur über Hilfe-Symbol; alle Texte „Sie“ (auch „Ihr Konto“, nie „dein“). Barrierefreiheit und Handy für Kursräume sind im alten System nicht beschrieben und werden in QUA/OBE geprüft [unklar].
Abnahme: Änderung in Raum 5 aktualisiert nur dessen Ansicht; Rundgang bei 390 px ohne seitlichen Bildlauf; Textprüfung findet kein „du/dein“.

**KUR-080** · P2 · Status: Ist — Benachrichtigungen aus Kursräumen (BEN): neue Aufgabe oder neues sofort sichtbares Material (`course_item`, an Lernende und Eltern, nicht an Lehrende); Abgabe bewertet oder zurückgegeben (`task_graded`, ohne Note und Rückmeldung); „Aufgabe ist morgen fällig“ (`task_due`, einmal je Aufgabe und Konto, nur ohne Abgabe); neue freigegebene Abstimmung/Umfrage/Selbsttest (`poll`, `selftest`, Text nennt nur den Kursraum, Link in den Raum). Zeitlich freigegebene und verborgene Inhalte lösen beim Freischalten nichts aus (offen: KUR-048).
Abnahme: neue Aufgabe → Benachrichtigung für Schüler und Eltern; Aufgabe fällig morgen ohne Abgabe → genau eine Erinnerung; verborgenes Material → keine.

**KUR-081** · P3 · Status: offen — Weitere Wünsche: Kursräume und Material teilen/kopieren (per Link, Export für Moodle, LTI-Anbindung); Kursvorlagen und Archiv-Kopie beim Schuljahreswechsel; Aktivitätsbericht je Raum (wer hat geöffnet/abgegeben) und Frühwarnung; Dateiablage über Fremdspeicher (Nextcloud/WebDAV); private Dateien je Person; Kursplanung Oberstufe (Kurswahl, Bänder; „groß, später“, Entscheidung offen).
Abnahme: je Funktion eigener Test; bis zur Entscheidung nicht vorhanden.

---

## NAC – Nachrichten, Chats, Postfach, Rundschreiben

### NAC.1 Ein Bereich „Nachrichten“: Struktur, Liste, Empfängerkreis

**NAC-001** · P1 · Status: Ist — Es gibt genau EINEN Menüeintrag „Nachrichten“ (Menügruppe „Kommunikation“) für Chats, Gruppen, Briefe, Rundschreiben, E-Mails und Mitteilungen. Wortlaut des Betreibers: „Ich sehe noch nicht so ganz wo du dir jetzt den Postfach und den Chats und Gruppen zusammengeführt hast“ – „das musst du jetzt sofort zusammenführen … nicht zwei, es muss jetzt eine werden“ – „Chats sind immer noch drin, das nervt.“ Chats und Gruppen sind ein Bereich („oben, kannst du auswählen … Chats oder Gruppen“). Seiten: `/nachrichten`, `/nachrichten/:art/:id`, `/nachrichten/neu` (Vorbelegung über Parameter `an`, `lehrkraft`, `eltern`, `schueler`, `betreff`, `entwurf`), `/nachrichten/einstellungen`, `/nachrichten/moderation` und `/nachrichten/moderation/chats` (nur messages.moderate). Alte Adressen `/postfach…`, `/chats…`, `/mitteilungen` und alle Verweise (Startseite, „Nachricht schreiben“ im Klassenraum, Dokumente) leiten dauerhaft um. Lehre: bei offener Frage keine eigene Variante bauen, sondern den Wunsch wörtlich umsetzen.
Abnahme: Menü zeigt genau einen Eintrag für alle Kommunikationsarten; `/postfach/12`, `/chats` und `/mitteilungen` landen unter `/nachrichten…`; Moderationspunkte nur mit messages.moderate sichtbar.

**NAC-002** · P1 · Status: Ist — Gemeinsame Liste, neueste zuerst: Eintrag mit Art-Kennzeichen, Profilkreis bzw. Person, Name oder Betreff, Vorschau, Zeit, Ungelesen-Markierung. Filter: Alle · Chats · Gruppen · Briefe · E-Mail · Mitteilungen · Archiv; „Entwürfe“ nur, wenn welche existieren; „Alle“ zeigt alles außer Archiviertem. Suchfeld: Briefe nach Inhalt, Chats nur nach Name (Inhalt ist verschlüsselt). Die Liste ist ohne harte Kappung seitenweise nachladbar (das alte System zeigte höchstens 100 Unterhaltungen ohne Seitenwechsel; Suche nur in einem begrenzten Ausschnitt [unklar: Werte]); die Chat-Liste fragt ohne N+1-Abfragen ab.
Abnahme: 150 Unterhaltungen → alle erreichbar; Suche nach einem Wort aus einem Brief findet ihn, nach einem Wort aus einer Chat-Nachricht nicht; Filter „Archiv“ zeigt nur Archiviertes.

**NAC-003** · P1 · Status: Ist — Zähler: am Menüpunkt EINE Zahl für ungelesene Chats/Gruppen und Briefe zusammen (gemeinsamer Zähler); Moderierende zusätzlich offener Meldungen. Startseiten-Kachel „Neue Nachrichten“: höchstens 5 ungelesene Unterhaltungen mit Absender, Betreff und Zeit. Lesestatus je Unterhaltung („gelesen bis“, wächst nur), „als ungelesen markieren“, „Alle als gelesen“.
Abnahme: 2 Chats + 1 Brief ungelesen → Zahl 3; „Alle als gelesen“ → 0; Kachel zeigt die letzten 5.

**NAC-004** · P1 · Status: Ist — Menü „Neu“: Chat (Einzelchat, Gruppe, Klassenchat), Brief (auch an mehrere Personen oder Klassen), E-Mail (nur mit verknüpftem Konto). Chats mit Suche und „+“-Knopf; die Suche findet alle erlaubten Personen einschließlich Eltern (Wunsch: „mit Suche nach allen Personen inklusive Eltern“; Einschränkung durch NAC-005). Die Senden-Funktion „Neue Nachricht an eine einzelne Person“ muss fehlerfrei laufen (im alten System als Fehler gemeldet, Behebung nicht bestätigt).
Abnahme: Lehrkraft schreibt neue Nachricht an eine einzelne Person → ankommt; Suche nach einem Elternteil liefert den Treffer.

**NAC-005** · P0 · Status: offen — Empfängerkreis datensparsam. Schüler/innen schreiben standardmäßig an Lehrkräfte ihrer Kurse, Klassenleitung und Sekretariat, an Mitschüler/innen nur, wenn die Schule es erlaubt (`messaging_students_to_students`) und dann nur innerhalb von Klasse und Kursen. Eltern schreiben an Personal (Lehrkräfte ihrer Kinder, Klassenleitung, Sekretariat, Schulleitung); andere Familien und Schüler/innen sind nicht auffindbar. Empfängerliste und Suche liefern nur Erlaubtes, nie Klassen fremder Kinder; eine schulweite Personensuche mit Klassenangabe für Schüler/Eltern ist ausgeschlossen (verhindert sonst jeden Verkauf). Gilt für Briefe UND Chats. Regeln stehen in den Einstellungen als drei Auswahlfelder; bestehende Unterhaltungen bleiben lesbar; neue Nachrichten an nicht mehr erlaubte Empfänger werden verständlich abgelehnt. Im alten System lag der Standard für Schüler↔Schüler auf „ja“. [unklar: Betreiber-Bestätigung für „aus“ steht aus; Neubau-Voreinstellung „aus“ (Datenschutz vor Komfort)]
Abnahme: Schülerkonto sucht Mitschüler „Theo“ → kein Treffer bei Standard; Elternkonto sucht „Lina“ aus fremder Familie → kein Treffer; Empfängerliste enthält keine Klasse eines fremden Kindes; Nachricht an Unzulässigen → Ablehnung mit Begründung.

**NAC-006** · P1 · Status: Ist — Layout: PC zwei Spalten (Liste links, Gespräch rechts); Handy: Liste und Gespräch nacheinander im Vollbild; getestet bei 360 und 390 px, ein echtes Handy ist noch nicht getestet. Alle Texte „Sie“; Hilfe nur über Hilfe-Symbol.
Abnahme: 390 px: Liste → Tippen öffnet Gespräch → Zurück zur Liste, ohne seitlichen Bildlauf; Rundgang auf einem echten Handy dokumentiert.

### NAC.2 Chats und Gruppen

**NAC-007** · P1 · Status: Ist — Chat-Arten: Einzelchat (zwei Personen, höchstens einer je Paar), Gruppe (selbst erstellt, Name, Mitglieder), Klassenchat (für eine Klasse, mit oder ohne Lehrkräfte), Elternchat (Eltern einer Klasse); Tabelle `chats` mit `kind` direct|group. Beim Anlegen eines Klassenchats wählt man die Klasse (Schülersuche braucht students.read). Der Chatname liegt serverseitig verschlüsselt, damit neue Geräte ihn anzeigen. Alle Chat-Routen erfordern messages.use. [unklar: welche Rolle in welcher Chat-Art teilnehmen darf (z. B. Eltern in Klassenchats) und ob Klassenänderungen Mitglieder automatisch ein-/austragen]
Abnahme: zweiter Einzelchat zwischen denselben Personen → vorhandener wird geöffnet; Klassenchat „5a ohne Lehrkräfte“ enthält nur Schüler/innen der 5a.

**NAC-008** · P1 · Status: Ist — Mitglieder: Chat-Admins fügen hinzu und entfernen und ernennen/entziehen weitere Admins; höchstens 400 Mitglieder je Chat; neue Mitglieder sehen nur Nachrichten ab ihrem Beitritt (Beitrittsgrenze, gilt auch beim Nachverpacken von Schlüsseln); Systemzeilen („X hat Y hinzugefügt“, Klartext ohne Nutzerinhalt) im Verlauf.
Abnahme: neues Mitglied sieht keine älteren Nachrichten; das 401. Mitglied wird abgelehnt; Nicht-Admin fügt hinzu → 403.

**NAC-009** · P1 · Status: Ist — Schreibrechte: Schreibmodus je Gruppe `all` (alle) · `admins` (nur Admins) · `selected` (Admins und Mitglieder mit „darf schreiben“); je Mitglied „darf schreiben“ oder „nur lesen“; lesende Mitglieder haben kein Eingabefeld und der Server erzwingt es. Wortlaut: „wenn Lehrer-Chats mit Schülern drin haben, können die quasi sagen, dass es ein only read oder ein read and write chat“; „manche dürfen schreiben, manche nur [lesen]“ (Diktat „reden“). „Nur schreiben ohne Lesen“ ist nicht vorgesehen [unklar: Betreiber klären].
Abnahme: Mitglied „nur lesen“ → kein Eingabefeld, POST → 403; Modus `admins` → normale Mitglieder lesen nur.

**NAC-010** · P1 · Status: Ist — Archiv und Stummschalten gelten pro Person: Archiv (Filter „Archiv“, Aktion „Zurückholen“), eine neue Nachricht holt einen archivierten Chat zurück, außer er ist stumm; Stummschalten (Symbol in der Liste). Alle Gesprächs-Einstellungen (Archiv, Stummschalten, Mitglieder und Rechte, Details, Geräte/Schlüssel) liegen hinter EINEM Zahnrad oben rechts; Wortlaut: „Das ist ein bisschen viel für so eine kleine Oberfläche.“ Chat-Archivierung ja, Entwürfe in Chats nein (spätere Aussage gilt: „Die Archivierfunktion kommt rein, die Entwurffunktion kommt raus“).
Abnahme: Chat archivieren, neue Nachricht → Chat wieder in der Liste; gleicher Test stumm → bleibt im Archiv; keine Knopfleiste im Gesprächsfenster, nur das Zahnrad.

**NAC-011** · P1 · Status: Ist — Eingabezeile wie WhatsApp: „eine Linie machen, die wirklich durchgehend ist“; „+“ links, Sende-Pfeil rechts in der Linie, Emoji-Knopf nur am PC (am Handy Emojis über die Tastatur). PC: Enter sendet, Umschalt+Enter macht eine neue Zeile. Handy: Enter macht eine neue Zeile, gesendet wird über den Pfeil. Keine Erklärtexte zu Tasten („das sind Sachen die musst du nicht erklären“). Die Zeile ist einzeilig und wächst bis zu einer Maximalhöhe. Nachrichten stehen untereinander (Sprechblasen), nicht übereinander. Dateien über „+“: [unklar: im alten System sind im Chat nur Bilder/GIFs belegt].
Abnahme: PC: Enter sendet, Umschalt+Enter Zeilenumbruch; 390 px: Enter Zeilenumbruch, nur Pfeil sendet; Zeile wächst bis zur Maximalhöhe; keine Tastaturhinweise sichtbar.

**NAC-012** · P1 · Status: Ist — Doppelsende-Schutz: der Client vergibt je Absendevorgang einen Schlüssel (UUID); Wiederholung mit gleichem Schlüssel liefert die bereits gespeicherte Nachricht (Erfolg, kein Duplikat), gleichzeitige Wiederholung wird abgefangen; gilt für Chat-Nachricht, neue Unterhaltung und Antwort (Bereiche Chat, bestehende Unterhaltung, neue Unterhaltung); gültig 24 Stunden; das Frontend hält den Schlüssel bis zum Erfolg. Es werden nur Schlüssel und Verweis gespeichert, keine Inhalte.
Abnahme: Doppelklick auf „Senden“ → genau eine Nachricht; zwei gleichzeitige Anfragen mit gleichem Schlüssel → eine Nachricht, beide Antworten gleich.

**NAC-013** · P2 · Status: Ist — Emoji-Auswahl in Chats und Briefen: Kategorien, deutsche Suche, zuletzt verwendet; reine Emoji-Nachrichten größer; zusammengesetzte Emoji (Familie) werden nicht zerlegt.
Abnahme: Familien-Emoji bleibt ein Zeichen; Suche „Herz“ findet Herz-Emoji; „zuletzt“ zeigt das gewählte.

**NAC-014** · P1 · Status: Ist — Bilder und GIFs in Chats: PNG, JPEG, GIF, WebP; höchstens 5 MB je Bild und 4 je Nachricht; auswählen, einfügen (Strg+V) oder ziehen, Vorschauleiste vor dem Senden; große Fotos werden im Browser vor dem Verschlüsseln verkleinert (maximale Kantenlänge [unklar: Ist-Wert fehlt; Vorschlag WebP, 2048 px]); GIFs bleiben animiert; Bildtyp wird am Inhalt geprüft; Ende-zu-Ende verschlüsselt (der Server kennt weder Inhalt noch Typ); Klick vergrößert; Bilder erscheinen auch in Briefen groß. Lose Uploads verfallen nach 24 Stunden.
Abnahme: 6-MB-Foto → verkleinert gesendet; .exe als .png → abgelehnt; 5 Bilder in einer Nachricht → abgelehnt; Server-Auszug enthält nur Chiffrat.

**NAC-015** · P1 · Status: Ist — Kontingente der Chat-Bilder: Personal 500 MB (`SM_CHAT_QUOTA_MB_STAFF`), Schüler/innen und Eltern 100 MB (`SM_CHAT_QUOTA_MB_STUDENT`), je Chat 1000 MB (`SM_CHAT_QUOTA_MB_CHAT`), jeweils 0 = unbegrenzt; höchstens 30 Uploads je 10 Minuten (`SM_CHAT_UPLOADS_PER_10MIN`); gesendete Anhänge zählen mit; Überschreiten liefert eine deutsche Fehlermeldung; negative Werte verhindern den Start.
Abnahme: Schülerkonto lädt 101 MB hoch → ab Überschreitung abgelehnt; 31. Upload in 10 Minuten → abgelehnt; `SM_CHAT_QUOTA_MB_STUDENT=-1` → Start bricht ab.

**NAC-016** · P1 · Status: Ist — Nachrichtenfunktionen: Antwort mit Zitat (Antwortleiste); eigene Nachricht löschen [unklar: wer sonst löschen darf]; Anzeige „…“ während der Entschlüsselung, „nicht lesbar“, wenn das Gerät keinen Schlüssel hat; Live-Aktualisierung neuer Nachrichten (Live-Ereignisse ohne Inhalt). Nachrichten sind Klartext (kein Markdown, keine Formeln), Anzeige ohne HTML; Chiffrat höchstens 120 000 Base64-Zeichen.
Abnahme: Antwort zeigt das zitierte Original; Nachricht ohne Schlüssel zeigt „nicht lesbar“, nicht „…“ auf Dauer; Nachricht mit `<b>` wird als Text gezeigt.

**NAC-017** · P2 · Status: offen — Stummschalten und Blockieren vereinfachen; 1:1-Chats löschen statt blockieren (spart Speicher). Betreiber (O-11): „Stummschalten und Blockieren vereinfachen; 1:1-Chats löschen statt blockieren“. [unklar: Löschen „nur für mich“ oder „für alle“]
Abnahme: Einzelchat löschen → verschwindet aus der Liste; Wirkung auf die Gegenseite ist festgelegt und dokumentiert.

**NAC-018** · P1 · Status: offen — Aufbewahrung von Chats: Betreiberwunsch „Aufbewahrung 1 Monat, außer mit Stern markiert“. Das alte System hat keine laufende Frist für Chats (nur manuelles Löschen und Entfernung 30 Tage nach Austritt der Person; aus dem Postfach übernommene Kopien folgen der Postfach-Frist, Standard 365 Tage). Neubau: laufende Frist für Chat-Nachrichten und -Bilder (Voreinstellung 1 Monat) mit Ausnahme sternmarkierter Nachrichten. [unklar: Stern je Person oder je Chat; „1 Monat“ = 30 Tage]
Abnahme: Nachricht ohne Stern, 31 Tage alt → nach dem Lauf gelöscht (inkl. Schlüsselzeilen, Bilder); mit Stern → bleibt.

**NAC-019** · P2 · Status: offen — Personenanzeige in Chats: Eltern mit vollem Namen, darunter klein „Kind: Name (Klasse)“; Suche nach dem Kindnamen schlägt die Eltern vor (unter Beachtung von NAC-005).
Abnahme: Lehrkraft sucht Kindnamen → Eltern erscheinen mit Zeile „Kind: … (5a)“; Schülerkonto sieht diese Zeile nicht.

**NAC-020** · P3 · Status: Ist — Bewusst nicht: GIF-Suche wie Giphy (Suchbegriffe und IP-Adressen gingen an Fremdfirmen; Betreiber nicht gefragt), Textkomprimierung der Chats (Nachrichten rund 110 Byte, Webserver-Kompression ist aktiv; Wunsch „automatisch komprimiert zum Server“ abgelehnt). Alternative: Bildverkleinerung im Browser (NAC-014).
Abnahme: keine Verbindung zu einem GIF-Dienst im Netzwerkprotokoll; Chat-Text wird nicht gesondert komprimiert.

**NAC-021** · P2 · Status: Ist — Abstimmung im Chat (siehe KUR-063/064): Anlage als Chat-Nachricht vom Typ Abstimmung; Frage und Antworten stehen nur im Ende-zu-Ende-Inhalt, der Server kennt nur Einstellungen, Anzahl der Antworten und Stimmen; abstimmen, schließen (wer im Chat schreiben darf); Löschen der Nachricht oder des Chats entfernt Abstimmung und Stimmen vollständig; Darstellung identisch zum Kursraum.
Abnahme: Server-Auszug enthält keine Frage im Klartext; Chat löschen → Abstimmung weg.

### NAC.3 Ende-zu-Ende-Verschlüsselung, Geräte, Schlüssel

**NAC-022** · P0 · Status: Ist — Ende-zu-Ende: jedes Gerät erzeugt ein eigenes Schlüsselpaar (X25519); der private Schlüssel verlässt das Gerät nie; jede Nachricht (Text und Bilder) wird mit einem zufälligen Nachrichtenschlüssel authentisiert verschlüsselt (NaCl/libsodium-kompatibel, XSalsa20-Poly1305, frische Nonces) und der Nachrichtenschlüssel für jedes Gerät aller Mitglieder (auch eigene) verpackt. Der Server speichert nur Chiffrat, Nonce, öffentliche Schlüssel, verpackte Schlüssel, Mitgliedschaften, Zeiten, Größen und Zähler; er sieht nie Texte, Bilder, Nachrichtenschlüssel, Geräteschlüssel, Code oder Passwort. Höchstens 10 Geräte je Person. Das Verfahren kann der Neubau mit gleichwertiger Stärke wählen, die Eigenschaften „Browser verschlüsselt, Server kennt keinen Klartext“ sind bindend. Speicherlast: je Nachricht eine Schlüsselzeile je Empfängergerät (≈ 99 KB je Nachricht in einem 400er-Chat) – Optimierung siehe NAC-057.
Abnahme: Datenbank, WAL, Dateiablage und Server-Log enthalten nach 100 Testnachrichten keinen Klartext; Nachricht an 3 Geräte → 3 verpackte Schlüssel; Server-API liefert nur Chiffrat.

**NAC-023** · P0 · Status: Ist — Geräteschlüssel im Browser: der geheime Schlüssel liegt im sicheren Schlüsselspeicher des Browsers und ist nicht auslesbar; Browser ohne native X25519-Unterstützung nutzen eine schwächere, aber verschlüsselte Ablage (AES-GCM-Hülle); fehlt der sichere Speicher ganz, erscheint eine verständliche Meldung statt einer lesbaren Ablage (kein unverschlüsselter Rückfall); bei defektem Speicher mit vorhandenem Altbestand wird ein Fehler gemeldet und KEIN neues Gerät angelegt. Chats funktionieren nur über HTTPS (oder localhost).
Abnahme: Browser-Speicher zeigt keinen exportierbaren Klartext-Schlüssel; Browser ohne Speicher → Meldung, kein Chat; Aufruf über HTTP (nicht localhost) → Chat gesperrt.

**NAC-024** · P0 · Status: offen — Beim Abmelden werden die Chat-Geräteschlüssel dieses Kontos aus dem Browser entfernt (Audit-Befund: sie blieben stehen; Widerspruch zur Beschreibung „nicht lesbar im Browser“). Folge: nach erneutem Anmelden ist eine Geräteeinrichtung nötig (NAC-025/027). [unklar: ob eine bewusste Option „Dieses Gerät merken“ für private Geräte zulässig ist; Betreiber entscheiden]
Abnahme: nach „Abmelden“ enthält der Browser-Speicher keinen Chat-Schlüssel des Kontos; Kontowechsel entfernt den Schlüssel des abgemeldeten Kontos.

**NAC-025** · P1 · Status: Ist — Neues Gerät einrichten („Gerät übertragen“): das neue Gerät erzeugt eine Verbindungsanfrage mit 8-stelligem Code (feste Zeichenmenge), QR-Code und Link, gültig 15 Minuten; das eingerichtete Gerät gibt den Code ein oder scannt den QR-Code; beide Geräte zeigen einen Fingerabdruck zum Vergleich; erst nach „Stimmt – übertragen“ gibt das alte Gerät frei (Freigabe befristet); die Schlüssel werden in Stapeln mit Fortschrittsbalken übertragen (abbrechbar, später fortsetzbar), das neue Gerät holt ausstehende Schlüssel und bestätigt den Empfang; danach ist der ganze Verlauf inkl. Bilder lesbar. Schutz: höchstens 10 Fehlversuche je 10 Minuten bei der Code-Suche, Verbindungsanfragen je Stunde begrenzt [unklar: Wert], Status pending|approved|cancelled. Ohne Übertragung sieht ein neues Gerät ältere Nachrichten nicht. Bekannte Grenze: ein kompromittierter Server könnte ein Gerät unterschieben; Gegenmaßnahme ist der Fingerabdruck-Vergleich. Wunsch: Schreiben am PC und am Handy mit demselben Chatpartner.
Abnahme: Test mit zwei echten, getrennten Browsern (steht im alten System aus): Code falsch → abgelehnt; nach zehn Fehlversuchen gesperrt; nach Freigabe liest das neue Gerät den alten Verlauf; Anfrage nach 15 Minuten ungültig.

**NAC-026** · P1 · Status: Ist — Geräte verwalten: Liste (Bezeichnung, zuletzt gesehen, Fingerabdruck), Gerät widerrufen/entfernen, „Gerät neu einrichten“ (ersetzt den Schlüssel eines Geräts), „Alle Geräte zurücksetzen“ (bei verlorenem Gerät; löscht fremde Geräteschlüssel). Banner auf den anderen eigenen Geräten, wenn ein neues Gerät wartet („Das war ich“ / „entfernen“). Chatpartner sehen „Sicherheitsschlüssel von X hat sich geändert“. [unklar: Folgen von „Alle Geräte zurücksetzen“ für bestehende Nachrichten]
Abnahme: Gerät C wird hinzugefügt → Gerät A zeigt Banner; „entfernen“ → C kann nichts mehr lesen; Zurücksetzen → Chatpartner sehen die Warnung.

**NAC-027** · P1 · Status: Ist — Wiederherstellung (optional, dringend empfohlen): empfohlen ein erzeugter Wiederherstellungscode (125 Bit), alternativ ein eigenes Passwort mit mindestens 12 Zeichen; Ableitung im Browser mit PBKDF2-SHA-256 und 1 000 000 Runden; der Server speichert nur einen undurchsichtigen Datenblock (Archivschlüssel), ersetzbar, abrufbar, löschbar. Ohne Code oder Passwort ist nichts wiederherstellbar; die Seite sagt das deutlich. Wunsch: Der Verlauf ist auf einem neuen Gerät lesbar.
Abnahme: Passwort mit 11 Zeichen → abgelehnt; Wiederherstellung mit Code auf neuem Gerät macht Verlauf lesbar; falscher Code → nichts lesbar, Server erfährt Code/Passwort nie.

**NAC-028** · P2 · Status: offen — Nutzerprüfung und Ergänzung: Wunsch „Hier fehlt die Option, neue End-zu-End-Verschlüsselungskeys zu generieren“ und „Das mit den Chatkeys muss gemacht werden“; Reiter „Neue Schlüssel“ und Geräteübersicht sind gebaut, die Prüfung durch den Betreiber (Gerät verknüpfen, Wiederherstellung, neue Schlüssel, Gerätebanner) steht aus; Geräteübersicht soll letzte Aktivität zeigen. [unklar: Wirkung neuer Schlüssel auf bestehende Nachrichten]
Abnahme: Betreiber spielt alle vier Abläufe auf zwei Geräten durch; Ergebnis wird dokumentiert.

### NAC.4 Melden, Moderation, Zugriffsschutz, Protokoll

**NAC-029** · P1 · Status: Ist — Melden: bei fremden Nachrichten „Melden“ (Grund optional, verschlüsselt); die meldende Person kann freiwillig den Klartext der Nachricht und Bilder mitschicken (serverseitig verschlüsselt, nur mit messages.moderate lesbar); nicht meldbar sind Nachrichten vor dem Beitritt und gelöschte; Doppelmeldungen werden verhindert; die meldende Person sieht „gemeldet“. Briefe: Meldekategorien belaestigung · beleidigung · bedrohung · spam · unangemessen · sonstiges. Status Chat `open|dismissed|removed`, Brief `offen|erledigt|abgelehnt`.
Abnahme: gemeldete Nachricht zweimal melden → Hinweis, keine zweite Meldung; Nachricht vor Beitritt melden → abgelehnt; Server speichert Klartext nur, wenn die meldende Person ihn schickt.

**NAC-030** · P1 · Status: Ist — Chat-Moderation unter `/nachrichten/moderation/chats` („Chat-Meldungen“): Liste ohne Inhalte, Detail mit freiwillig mitgeschicktem Text/Bildern; Entscheidung „Ablehnen“ oder „Nachricht entfernen“ (für alle, inkl. Bilder); Standardzuständigkeit Schulleitung (messages.moderate); Zugriffe auf Liste und Bilder werden protokolliert. Meldende und Gemeldete erfahren die Entscheidung nicht [unklar: ob so gewollt].
Abnahme: Moderator entfernt Nachricht → für alle Mitglieder weg (inkl. Bilder); Listenaufruf erzeugt Protokolleintrag; Lehrkraft ohne messages.moderate → 403.

**NAC-031** · P0 · Status: offen — Prüfung nur mit Einwilligung. Betreiberwunsch: gemeldete Nachrichten werden dauerhaft gesichert (Meldende wählen Nachricht oder Zeitraum), die Prüfung durch Berechtigte (Sekretariat, Administration, Schulleitung) erfolgt nur mit Zustimmung von Kind bzw. Eltern; ausdrücklich NICHT gewollt: Prüfung ohne Zustimmung. Dafür ist das Recht chats.review (geplant, nur Schulleitung) vorgesehen. [unklar: Ort und Form der dauerhaften Sicherung („extern“); wie Moderation und Administratorzugriff bei Ende-zu-Ende insgesamt wirken]
Abnahme: Prüfer öffnet gemeldeten Chat-Auszug ohne dokumentierte Einwilligung → verweigert; mit Einwilligung lesbar und protokolliert; Administration ohne chats.review → kein Zugriff.

**NAC-032** · P0 · Status: Ist — Chat-Protokoll: alle Verwaltungsaktionen (Geräte, Mitglieder, Moderation, Löschen, Meldungen, Gruppenänderungen) werden protokolliert (Muster `chat.<aktion>`), nur mit Kennungen und Zählungen, nie mit Titeln, Inhalten, Meldegründen oder Schlüsseln. Ausdrücklich NICHT protokolliert: einzelne gesendete Nachrichten und „gelesen“-Markierungen (sonst entstünde ein Protokoll, wer wann wem schreibt); das ist eine dokumentierte Ausnahme von „jede schreibende Aktion wird protokolliert“ (Zustimmung des Betreibers steht aus). Der Protokoll-Speicher der Chats ist begrenzt. [unklar: bei beobachteten Konten („jede Anfrage“) würden Chat-Anfragen erfasst; das hebt die Ausnahme auf – Datenschutz klären, DAT]
Abnahme: Nachricht senden/lesen → kein Eintrag; Mitglied hinzufügen, Gerät entfernen, Nachricht entfernen → je ein Eintrag mit Kennungen, ohne Text.

**NAC-033** · P0 · Status: Ist — Zugriffsschutz Chats: Zugriff nur für Mitglieder (mit Beitrittsgrenze) und mit eigenen Geräten; Nicht-Mitglieder erhalten 404; Anhänge nur zusammen mit einer für das Gerät lesbaren Nachricht; Zuschauer/in: gemeldete Chats und Postausgang gesperrt; kein Administrator-Generalzugriff auf Anhänge.
Abnahme: fremde Chat-Kennung → 404; Anhang eines Chats, in dem man nicht Mitglied ist → 404; Mitglied nach Beitritt ruft Anhang einer älteren Nachricht ab → abgelehnt.

### NAC.5 Briefe und Rundschreiben

**NAC-034** · P1 · Status: Ist — Brief verfassen (E-Mail-artig, schulintern): Empfänger in An, CC und BCC je als Person, Gruppe, Klasse oder freie E-Mail-Adresse (Auswahlfeld nach WAI-ARIA-Combobox); Betreff ist Pflicht (Briefe brauchen einen Betreff, Chats nicht); Text höchstens 20 000 Zeichen; höchstens 10 Anhänge je Nachricht (die Zählung zieht bereits angehängte Dateien ab, im Brief wie im Chat einheitlich); höchstens 20 000 Empfänger je Nachricht. Betreff und Text liegen serverseitig verschlüsselt (Bindung an Unterhaltung und Nachricht; die Absender-Kennung gehört nicht zur Bindung), Anhänge verschlüsselt in der Dateiablage. Der Brief erscheint im Chat-Stil; die Ansicht zeigt Rollen-Kennzeichen CC/BCC, externe Beteiligte und Versandstatus. Arten: direkt, Gruppe, Rundschreiben. Ratenlimits für neue Unterhaltungen und Nachrichten je Zeitraum und Betreff-/Empfängergrenzen sind im alten System konfiguriert [unklar: Werte].
Abnahme: Brief ohne Betreff → abgelehnt; 11. Anhang → abgelehnt; Text mit 20 001 Zeichen → abgelehnt; Datenbankauszug zeigt Betreff und Text nur als Chiffrat.

**NAC-035** · P1 · Status: Ist — Rundschreiben und Klassenansicht: Empfängergruppen sind alle Lehrkräfte · Lehrkräfte eines Standorts · alle Klassenleitungen · alle mit einer Rolle (Schulleitung, Sekretariat, Planung, Administration) · Klassenleitung einer Klasse · Klasse, Kurs, Kollegium, Jahrgang, alle. Rundschreiben nur mit messages.broadcast (Lehrkräfte nur eigene Klassen und Kurse, Abteilungsleitung eigener Zweig); ohne dieses Recht höchstens 25 Einzelempfänger. Antworten auf ein Rundschreiben gehen nur privat an den Absender, die Empfängerliste ist nicht sichtbar. Klassenansicht: Suche „5a“ → „Klasse 5a anzeigen“ mit Knöpfen Kinder · Eltern · Kinder und Eltern · Klassenleitung · alle Lehrkräfte; Einzelpersonen aus der Liste hinzufügen; Hinweis, wenn Eltern noch andere Kinder an der Schule haben. Kinder und Eltern sehen in der Klassenansicht nur die Lehrkräfte; die Liste „Kinder mit Eltern“ sehen nur Personen, die die Klasse ohnehin sehen dürfen (students.read). Beispielbezeichnungen: „Eltern der 5a“, „alle Lehrkräfte“.
Abnahme: Lehrkraft ohne messages.broadcast wählt 26 Einzelempfänger → abgelehnt; Rundschreiben an „Eltern der 5a“ → Antwort einer Mutter geht nur an die Lehrkraft; Schülerkonto sieht in der Klassenansicht keine Mitschüler.

**NAC-036** · P1 · Status: Ist — CC und BCC: Der BCC-Empfänger sieht nur den Absender und sich selbst; die anderen Empfänger sehen ihn nicht, auch nicht in der Auskunft; die Antwort aus BCC ist privat. Rollen-Kennzeichen to|cc|bcc je Teilnehmer.
Abnahme: A schreibt an B (An) und C (BCC): B sieht C nicht; C sieht nur A und sich; Antwort von C geht nur an A.

**NAC-037** · P1 · Status: offen — Zustellung an volljährige Schüler/innen: Sie entscheiden selbst, wohin Schulinformationen gehen: „mich / meine Eltern / beide“ (`delivery` self|parents|both; Standard self; minderjährig immer both; Hinweis auf die Volljährigkeit bleibt sichtbar, bis die Wahl bewusst gespeichert wurde). Offen ist, was ein Rundschreiben tut, solange noch keine Wahl getroffen wurde: bisher nur an den Schüler. [unklar: Betreiber entscheidet zwischen „nur Schüler“ und „beide bis zur Wahl“; Neubau-Vorgabe bis dahin „nur Schüler“]
Abnahme: Volljähriger ohne Wahl erhält Rundschreiben, Eltern nicht; nach Wahl „beide“ erhalten es beide.

**NAC-038** · P1 · Status: Ist — Antworten und Aktionen: Antwortmodus je Unterhaltung `all` · `sender` · `none`; Zahnrad-Menü: Archiv, stumm schalten, als ungelesen markieren, Person blockieren, Betreff ändern, Unterhaltung löschen („für mich“: ältere Nachrichten werden ausgeblendet, eine neue Nachricht holt die Unterhaltung zurück); „Alle als gelesen“; Nachricht melden (NAC-029).
Abnahme: Modus `none` → kein Antwortfeld, POST → 403; Unterhaltung „für mich“ löschen, neue Nachricht trifft ein → erscheint wieder ohne die alten.

**NAC-039** · P2 · Status: offen — Entwürfe: Briefe lassen sich als Entwurf speichern (Empfänger werden mitgespeichert, Inhalt verschlüsselt, Anhänge am Entwurf); eine ungespeicherte Nachricht wird automatisch als Entwurf gespeichert („Entwurf gespeichert“); Chats haben keine Entwürfe. Der Betreiber sagte erst „Die Entwurffunktion kannst du auch weglassen“; im alten System entfielen sie nur in Chats. [unklar: Betreiber bestätigt, ob Brief-Entwürfe bleiben]
Abnahme: Brief halb schreiben, Seite verlassen → Entwurf in der Liste (Filter „Entwürfe“ nur dann sichtbar); in Chats gibt es keinen Entwurf.

### NAC.6 E-Mail-Anbindung

**NAC-040** · P1 · Status: Ist — Externe E-Mail-Konten verbinden. Wunsch: „e-mailartige Mails in das Postfach kommen und alle E-Mails, die ich … mit meinem Account verknüpft habe und der eine Genehmigung gegeben habe“. Ausgehend nach außen, eingehend im Bereich Nachrichten (Art „E-Mail“), Antworten bleiben in derselben Unterhaltung (Zuordnung über die Message-ID). Anbieter: Google, Apple/iCloud, Microsoft/Outlook, GMX, WEB.DE, T-Online, Yahoo, eigener Server; Anbieter wird anhand der Adresse vorausgewählt. Anmeldung mit App-Passwort (mit Verweis auf die App-Passwort-Seite des Anbieters) oder über die Anmeldung beim Anbieter (nur Google, Microsoft); ob die Schule die Anbieter-Anmeldung zulässt, steuert eine Schuleinstellung. Konten auflisten, ändern, löschen, manuell synchronisieren, Standardkonto für den Versand; Verbindung trennen; „Von“-Auswahl beim Verfassen. Höchstzahl Konten je Person [unklar: Wert]. Verknüpfen kann nur die Inhaberin des Mail-Kontos (OAuth mit Zustandsparameter gegen Fälschung). Im alten System lokal gebaut, nie mit einem echten Konto getestet.
Abnahme: Testkonto mit App-Passwort verbinden → Abruf liefert Mails als „E-Mail“; Antwort bleibt in derselben Unterhaltung; Verbindung trennen → Konto und Zugangsdaten entfernt; E-Mail-Hinweis-Einstellung bleibt ausgegraut, solange kein Konto verbunden ist.

**NAC-041** · P0 · Status: Ist — Schutz der Anbindung: eigene Server nur mit mail.custom_server (Administration, Schulleitung, Sekretariat; Schüler/Eltern nie); Schüler/Eltern nur bekannte Anbieter mit festen Servern und Ports (IMAP 993; SMTP 587 mit starttls oder ssl); Zielprüfung bei Eintrag UND bei jeder Verbindung (nur öffentliche Adressen nach Auflösung aller DNS-Einträge; Loopback, link-lokale, private Bereiche, Multicast und interne Dienstnamen abgewiesen; keine Weiterleitungen; Verbindung an die geprüfte Adresse gebunden); einheitliche Fehlermeldung ohne Antwortinhalte; Ratenlimit 10 Versuche je Stunde und Konto; Zugangsdaten nur verschlüsselt und nie wieder angezeigt; bei OAuth werden Token-Inhalte erst nach Signaturprüfung gelesen (Prüfpunkt des alten Systems, offen). Alle automatisch erzeugten Mails tragen `Auto-Submitted: auto-generated`.
Abnahme: Schülerkonto trägt eigenen Server ein → 403; Eintrag mit privater oder Loopback-Adresse → abgelehnt; 11. Verbindungsversuch in einer Stunde → 429; Konto-Anzeige enthält kein Passwort.

**NAC-042** · P1 · Status: Ist — Abruf und Versand: Hintergrund-Abruf alle 5 Minuten (`SM_MAIL_SYNC_MINUTES` = 5.0, Schalter `SM_MAIL_SYNC`), zusätzlich „jetzt synchronisieren“; der erste Abruf holt die letzten Tage [unklar: Anzahl], je Abruf Mengengrenze [unklar: Wert], Mailanhang beim Abruf höchstens 10 MiB, Mailtext und Anzahl begrenzt. Versand über wählbares Absenderkonto; Versandstatus je Empfänger (sent · failed · pending) mit Fehler; letzter Fehler des Kontos sichtbar. Eingehende Mails sind Kopien auf dem Server und unterliegen den Aufbewahrungsregeln (NAC-046). [unklar: Verhalten bei ungültigen Zugangsdaten oder Abruffehlern]
Abnahme: Abruf nach 5 Minuten ohne Eingriff; Mail mit 11-MiB-Anhang wird ohne Anhang übernommen oder abgewiesen (dokumentiertes Verhalten); fehlgeschlagener Versand zeigt Status „failed“.

**NAC-043** · P2 · Status: offen — Inbetriebnahme durch den Betreiber: echter Test eines Mail-Kontos mit App-Passwort; Microsoft-App beim Anbieter registrieren und Google-Zugangsdaten für die Anbieter-Anmeldung hinterlegen (Betreiber gibt Passwörter selbst ein); weitere Anbieter-Vorlagen mit Servern und Link zur App-Passwort-Seite (IONOS, mailbox.org, Posteo, IServ).
Abnahme: Testprotokoll mit echtem Konto liegt vor (Verbinden, Abruf, Antwort, Trennen); neue Anbietervorlage ist wählbar.

### NAC.7 Mitteilungen, Blockieren, Moderation, Aufbewahrung, Einstellungen

**NAC-044** · P1 · Status: Ist — Mitteilungen (Schwarzes Brett/Aushang): Anlegen, Bearbeiten, Löschen durch Berechtigte (announcement.post, Umfang eigene Klassen/Zweig). Felder: Titel (höchstens 200 Zeichen), Text, Zielgruppe `all|staff|classes` (mit Rollen, Klassen, Standort), Gültigkeit von–bis (Datum), angeheftet, Priorität `normal|wichtig`, Kennzeichen „für den Monitor“. Sichtbar für die Zielgruppe, solange gültig: als Panel auf der Startseite und als Ordner „Mitteilungen“ in Nachrichten. Liste zwischengespeichert, jede Änderung leert den Speicher sofort. Verfasser wird bei Kontolöschung pseudonymisiert. Lesbar für Angemeldete im Rahmen der Zielgruppe (auch Zuschauer). [unklar: wer löschen darf, Lebensdauer des Zwischenspeichers, Sichtbarkeitsregel im Detail]
Abnahme: Mitteilung für „staff“ → Schülerkonto sieht sie nicht; nach Ablauf von „gültig bis“ verschwindet sie; Lehrkraft ohne announcement.post → 403.

**NAC-045** · P1 · Status: Ist — Blockieren und Sperren: Jede Person blockiert einzelne Personen, E-Mail-Adressen und Kontakte; die Blockliste in den Einstellungen erlaubt „Freigeben“; wer blockiert, erhält keine Nachrichten der blockierten Person. Moderation (messages.moderate, `/nachrichten/moderation`): Meldungsliste ohne Inhalte, Inhalt erst nach Klick (protokolliert), Entscheidung mit Status `offen|erledigt|abgelehnt`, Kategorie, verschlüsseltem Vermerk und Maßnahmen (Nachricht ausblenden – bleibt verschlüsselt als Beleg bis Fristablauf; Person sperren). Sperre vom Nachrichtenversand mit Ende, Grund (verschlüsselt) und Verursacher; Sende-Sperre → 403 `suspended`; Sperren auflisten und aufheben; gesperrte Konten bleiben lesend. [unklar: Wirkung des Blockierens auf Chats]
Abnahme: A blockiert B → Nachricht von B kommt bei A nicht an; Moderator sperrt B bis morgen → Senden liefert 403, Lesen geht; Listenaufruf zeigt keinen Text.

**NAC-046** · P0 · Status: offen — Aufbewahrung und Löschen: Nachrichten (Briefe, Rundschreiben, E-Mail-Kopien) samt Anhängen werden nach `messaging_retention_days` gelöscht (Standard 365 Tage), offen gemeldete ausgenommen; danach entfernt der Lauf leere Unterhaltungen, Entwürfe und abgeschlossene Meldungen älter als die Frist und beendet abgelaufene Sperren. Löschen einer Unterhaltung löscht alle Anhänge (auch an Entwürfen); neue Anhangsarten werden in Löschen und Lauf berücksichtigt. Der Lauf ist eine eigene Wartungsstufe mit festem Intervall (das alte System führte ihn nur als Notbehelf höchstens alle 6 Stunden beim Abruf des Ungelesen-Zählers aus – Mangel); Moderation kann ihn manuell auslösen (Protokoll `message.retention`). Nach Austritt einer Person: eigene gesendete Nachrichten nach 30 Tagen. Die Einstellung heißt im alten System „0 = nie“; das widerspricht der Regel „kein Wert schaltet die Löschung ab“. [unklar: Betreiber entscheidet, ob 0 zulässig bleibt]
Abnahme: Nachricht älter als 365 Tage → nach dem nächsten Lauf samt Anhang gelöscht; offen gemeldete bleibt; Lauf läuft ohne Aufruf des Zählers.

**NAC-047** · P2 · Status: Ist — Einstellungen `/nachrichten/einstellungen`: E-Mail-Hinweis „Neue Nachricht“ (Standard an, ohne Inhalt; ausgegraut, bis ein Mail-Konto verbunden ist, Klick führt zum Verbinden), Konto-Status („noch kein E-Mail-Konto verbunden“), E-Mail-Konten verwalten, blockierte Personen, Regeln der Schule (Aufbewahrung; Schüler↔Schüler; Empfängerregeln NAC-005). Offen: die Postfach-Regeln gehören in die zentralen Schuleinstellungen bzw. „Rollen & Rechte“ (Betreiber: verstreute Einzelregeln dorthin); heute liegt die Aufbewahrungsfrist noch in den Postfach-Einstellungen. Lange Texte nur über das Hilfe-Symbol.
Abnahme: Einstellungsseite enthält nur Blockliste, E-Mail-Konten, E-Mail-Hinweis und (mit settings.edit) die Schulregeln; keine Erklärabsätze.

**NAC-048** · P2 · Status: offen — Benachrichtigungen bei neuen Nachrichten: Die Benachrichtigungsart `message` ist standardmäßig aus und hat keine angebundene Quelle; die Glocke zeigt keine Chat-/Brief-Nachrichten (offen); der E-Mail-Hinweis „Neue Nachricht“ ist inhaltsfrei, dedupliziert und abschaltbar. Push folgt mit der App (BEN). Ruhezeiten für Nachrichten (Admin legt fest, Lehrkraft kann „Sofort zustellen“) sind nicht entschieden [unklar]. Automatische Nachrichten braucht ein Systemabsender (Nachschreib-Benachrichtigungen; fehlt).
Abnahme: Nutzerin schaltet `message` ein → neue Nachricht erscheint in der Glocke ohne Inhalt im Titel; E-Mail-Hinweis enthält nur Hinweis und Link.

### NAC.8 Datenschutz und Schutzmaßnahmen

**NAC-049** · P0 · Status: Ist — Keine Inhalte in Nebenkanälen: Nachrichteninhalte, Betreffe, Chat-Titel und Meldegründe stehen nie im Protokoll, in Logs, Live-Ereignissen oder Benachrichtigungs-E-Mails; erlaubt sind nur Kennungen und Zählungen. Live-Ereignisse („neue Nachricht“) tragen keinen Inhalt. Es gibt keine automatische Nachricht zu Krankmeldungen und keine Kopie von Gesundheitsangaben in Nachrichten. Test: Klartext einer Nachricht taucht in Datenbank, WAL, Dateiablage und Server-Log nicht auf.
Abnahme: Test sendet Nachricht mit Prüfwort und durchsucht alle genannten Speicher → kein Treffer; Ereignisstrom enthält nur Kennung.

**NAC-050** · P0 · Status: Ist — Auskunft (Art. 15/20) für Nachrichten: Briefe entschlüsselt (von der Moderation ausgeblendete Texte als „[von der Moderation ausgeblendet]“, BCC-Empfänger erscheinen nicht), Chat-Mitgliedschaften, Zeiten, eigene Chat-Nachrichten verschlüsselt mit Hinweis „Inhalte nur auf eigenen Geräten lesbar“, Geräte, Angabe ob ein Backup existiert, eigene Meldungen. Obergrenze der Auskunft für Benachrichtigungen 5000.
Abnahme: Auskunft eines Testkontos enthält Briefe lesbar, Chat-Nachrichten nur als Chiffrat und keine BCC-Empfänger Dritter.

**NAC-051** · P0 · Status: offen — Datenschutzgrundlagen der Chat-Funktion: Der Betreiber legt die Datenschutzrichtlinien für Chats noch fest („Sicherheitsstandards und die noch festzulegenden Datenschutzrichtlinien einhalten“). Einwilligungen bzw. Hinweise vor der ersten Nutzung von Schlüssel-Backup, Mail-Anbindung (Kopien liegen auf dem Server) und die Kenntnisnahme der Datenschutzhinweise sind im alten System nicht belegt [unklar]. Neubau: vor der ersten Nutzung von Backup und Mail-Anbindung ein kurzer Hinweis über das Hilfe-Symbol auf Datenverarbeitung und Fristen; Datenschutzseite `/datenschutz` für alle Rollen erreichbar.
Abnahme: erste Mail-Anbindung zeigt vor dem Verbinden den Hinweis; Betreiberbeschluss zur Chat-Richtlinie ist dokumentiert.

### NAC.9 Gewünschte, noch nicht gebaute Funktionen

**NAC-052** · P1 · Status: offen — Elternbriefe: Lesebestätigung und Lesestatus: Brief an Klasse, Jahrgang, Bildungsgang, Gruppe oder Schule, mit PDF-Anhang und Benachrichtigung; Volljährige erhalten Briefe selbst, Eltern nur mit Freigabe (NAC-037); Lesebestätigung mit einem Klick; Lesestand für Absender, Klassenleitung, Schulleitung („23 von 28 Familien“) mit Namensliste; Erinnerung an Nicht-Leser (kleine Funktion „Lese-Status“, Aufwand S, zuerst). Im alten System ist die Lesebestätigung (`read_at`) nur teilweise vorhanden. [unklar: Lesestatus je Familie oder je Elternteil]
Abnahme: Brief an 28 Familien, 23 bestätigen → Absender sieht „23 von 28“ und die fünf Namen; Erinnerung geht nur an diese fünf.

**NAC-053** · P1 · Status: offen — Elternbriefe: Rückmeldung und Einwilligung („groß, später“): Rückmeldung Ja/Nein, Auswahl, Freitext, Unterschrift auf dem Bildschirm, Frist, Auswertung als Liste und CSV; Umfrage mit Auswertung im Brief; Einwilligungen aus Vorlagen (versioniert, jederzeit widerrufbar, mit Nachweis nach Art. 7 DSGVO, Übersicht je Klasse „Wer darf fotografiert werden?“, ab einem einstellbaren Alter willigen Schüler/innen selbst ein [unklar: Alter]); Papier-Fallback (Liste der Familien ohne Konto, Serienbrief als PDF, Ausdruck für Eltern ohne Zugang); Archiv aller Briefe je Klasse und Schuljahr. Abgrenzung: die Formular-Vorlagen „Rückmeldung Elternabend“ u. a. liefert der Formular-Baukasten (FOR).
Abnahme: Rückmeldung bis Frist, Auswertung als CSV; Einwilligung widerrufen → Übersicht je Klasse zeigt sofort „nicht erlaubt“; Familie ohne Konto steht in der Papierliste.

**NAC-054** · P2 · Status: offen — Übersetzung von Elternbriefen per Klick: Eltern lesen Briefe in ihrer Sprache (mindestens TR, AR, UK, RU, PL, RO, EN, FR) mit Hinweis „maschinell übersetzt“ und Zugriff auf das Original; der Dienst ist in den Einstellungen wähl- und abschaltbar, ohne Dienst keine Übertragung; übertragen wird nur der Brieftext, möglichst ohne Namen von Kindern; nur Dienste mit Auftragsverarbeitungsvertrag und EU-Standort. [unklar: lokaler/datensparsamer Dienst oder Fremdanbieter – Betreiber entscheidet]
Abnahme: mit simuliertem Dienst: Brief in Türkisch lesbar, „maschinell übersetzt“ sichtbar, Original abrufbar; Dienst aus → keine Verbindung nach außen.

**NAC-055** · P3 · Status: offen — Kleine Funktionen: Nachrichtenvorlagen („Kind krank“, „Ausflug“; eigene Vorlagen je Person zuerst, Schulvorlagen optional); Abwesenheitsnotiz „abwesend bis …, Vertretung X“ als Hinweis im Chat, ausdrücklich KEINE automatische Antwort an Eltern (Datenschutz); Zitate, Erwähnungen und Favoriten; Suche in langen Verläufen.
Abnahme: je Funktion eigener Test; Abwesenheitsnotiz erzeugt keine automatische Nachricht.

**NAC-056** · P2 · Status: offen — Elternsprechtag und Sprechstunden: Sprechtag anlegen (Datum, Zeitfenster, Anmeldephase, Slotlänge 5 oder 10 Minuten, Puffer, Raum je Lehrkraft, vor Ort oder online per Link); Eltern sehen nur Lehrkräfte ihrer Kinder und buchen am Handy wie am PC, Doppelbuchungen ausgeschlossen (500 gleichzeitige Buchungen zur Freischaltung); Lehrkräfte laden gezielt ein und sperren Slots; Laufzettel als PDF und iCal; wöchentliche Sprechstunde mit Buchung, Bestätigung, Absage. Abgrenzung: Kalender und Räume in STA/STP.
Abnahme: 500 gleichzeitige Buchungsversuche auf 100 Slots → genau 100 Buchungen, keine Doppelung; Eltern sehen nur eigene Lehrkräfte.

**NAC-057** · P3 · Status: offen — Chat-Speicher entlasten (Entscheidung offen): Gruppenschlüssel statt eines verpackten Schlüssels je Nachricht und Gerät (Schlüsselzeilen ≈ 89 % des Chat-Textspeichers; Jahr 1: 2159 / 5397 / 10 794 MB für kleine/mittlere/große Schule), Chat-Bilder aus der Datenbank in die verschlüsselte Dateiablage (Chat-Bilder ≈ 57 MB je Schüler und Jahr; Sicherungen werden sonst unbetreibbar groß), kein doppelter Upload nach Gerätewechsel (`devices_changed`).
Abnahme: Vergleichsmessung mit 400er-Chat: Speicher je Nachricht deutlich unter 99 KB; Sicherung ohne Chat-Bild-Blobs in der Datenbank.

**NAC-058** · P3 · Status: offen — Weitere Wünsche und Ideen: Notfall-SMS und Notfallkommunikation mit Räumungsliste (später); Kanban-Boards; Dokumentenbereich fürs Kollegium (Kursraum „Kollegium“ mit Ordnerrechten); KI-Entwürfe nur ohne Klarnamen; Push und installierbare App (BEN); Umfragen im Chat über Abstimmungen hinaus.
Abnahme: je Funktion eigener Test; bis zur Entscheidung nicht vorhanden.

**NAC-059** · P2 · Status: offen — Begriffe: Hilfetexte und Dokumente sagen noch „Postfach“; im Neubau heißt alles „Nachrichten“ (Briefe, E-Mail, Chats).
Abnahme: Volltextsuche in Oberfläche, Hilfe und Handbuch findet kein „Postfach“.

**NAC-060** · P2 · Status: offen — Leistung: Nachrichtenversand dauerte im Lasttest 3 bis 5 Sekunden. Ziel: 95 % der Anfragen unter 500 ms bei 2500 Schüler/innen und 300 Lehrkräften (Spitze 7:30 bis 8:00 Uhr); Chat-Liste ohne N+1, Ungelesen-Zähler gespeichert, Index auf (Chat, Nachricht); PostgreSQL ab mittlerer Schulgröße. 150 gleichzeitige Nutzer liefen lokal fehlerfrei.
Abnahme: Lasttest gegen eine Wegwerf-Instanz mit Demo-Daten: Nachrichtenversand und Chat-Liste erreichen das Ziel.

**NAC-061** · P3 · Status: Ist — Nur bei Datenübernahme aus dem alten System: frühere Postfach-Gespräche werden einmalig in Chats übernommen, nichts wird gelöscht (Originale nur ausgeblendet), wiederholbar ohne Dubletten, rückgängig per Befehl. Mehrpersonen-Gespräch mit Betreff → Gruppenchat (Betreff = Gruppenname); Zweier-Gespräch ohne Betreff → Privatchat (mehrere zusammengeführt); Briefe mit Betreff, Rundbriefe, externe E-Mails und Nachrichten mit Anhang oder CC/BCC bleiben Briefe. Übernommene Nachrichten tragen „übernommen aus dem Postfach“, bleiben serverseitig verschlüsselt (nicht Ende-zu-Ende) und zeigen als Vorschau „Nachricht“ mit Schloss-Symbol; Lesestatus, Archiv und Stumm werden übernommen. Ein Neubau ohne Altbestand braucht das nicht.
Abnahme: Übernahme mit Musterdaten zweimal ausführen → keine Dubletten; Rückgängig stellt den Ausgangszustand her; Originale bleiben erhalten.

**NAC-062** · P3 · Status: Ist — Beispieldaten für Nachrichten in der Demo (BET): Wunsch „ein paar Beispiele für die Postfächer … zwischen Schüler eins, Lehrer eins, Eltern eins, Sekretariat eins und Admin eins“. Umgesetzt: neun Briefe mit Antworten (Krankmeldung und Attest, Hausaufgaben, Einverständniserklärung, Wartung, Lob u. a.), ein Gruppenchat mit allen fünf Testkonten und sechs Einzelchats; die Chats sind leer, weil Ende-zu-Ende-Inhalte nur auf den Geräten der Nutzer entstehen. Keine echten Personen, keine echten E-Mail-Adressen.
Abnahme: frische Demo enthält die Beispielbriefe; Chats sind angelegt, aber ohne Nachrichten; kein Beispielinhalt enthält echte Namen oder Adressen.

---

## FOR – Formulare, Briefe, Zugangsdaten

### FOR.1 Formular-Baukasten

**FOR-001** · P1 · Status: Ist — Schulen erstellen eigene Formulare und Anträge ohne Programmierung (Beurlaubung, Entschuldigung, Einverständnisse, Anträge, Rückmeldungen), legen fest, wer ausfüllt, wer prüft und was bei Genehmigung geschieht. Wunsch: „dass Schulen eigene Formulare eintragen können“ – „für eine Beurlaubung, Krankmeldung oder sonstiges erstellt werden können oder automatisiert werden können“. Familien füllen online (handytauglich) aus oder drucken ein PDF und laden den unterschriebenen Scan hoch. Ablauf: Vorlage → Version → Einreichung → Ereignisse (Verlauf) → Aktionen. Seite `/formulare` mit den Bereichen „Ausfüllen“, „Meine Formulare“, „Eingang“, „Vorlagen“, „Bibliothek“ (je nach Recht), Editor `/formulare/vorlage/:id` (Zahl oder „neu“, nur forms.manage), Startseiten-Kachel nur, wenn Einreichungen auf Entscheidung oder Rückmeldung warten. Die Browser-Prüfung des Baukastens durch den Betreiber steht aus.
Abnahme: Sekretariat legt „Ausflugs-Einverständnis“ an, aktiviert es, eine Mutter füllt es auf dem Handy aus, die Klassenleitung genehmigt → Einreichung „genehmigt“, Verlauf zeigt alle Schritte.

**FOR-002** · P1 · Status: Ist — Vorlage: Titel (höchstens 200 Zeichen), Beschreibung, Kategorie (Standard „sonstiges“ [unklar: weitere Werte]), Status `entwurf` → `aktiv` → `archiviert`, Kennzeichen „enthält geschützte Angaben“; anlegen, bearbeiten, duplizieren, löschen [unklar: Löschregel bei vorhandenen Einreichungen], Status setzen, aus der Bibliothek übernehmen, Vorschau auch als PDF einer noch nicht gespeicherten Vorlage.
Abnahme: Entwurf ist für Familien unsichtbar, aktiv sichtbar, archiviert nicht mehr ausfüllbar; Duplizieren erzeugt Entwurf mit gleichen Feldern.

**FOR-003** · P1 · Status: Ist — Versionierung: eine Änderung der Fassung erzeugt eine neue Version, sobald Einreichungen mit der aktuellen existieren, sonst wird direkt angepasst; neue Einreichungen nutzen die neueste Version, alte bleiben unverändert und zeigen ihre eigene Fassung (Tabellen `form_templates`, `form_versions`, `form_submissions`, `form_events`).
Abnahme: Feld hinzufügen nach einer Einreichung → neue Version; die alte Einreichung zeigt das Feld nicht.

**FOR-004** · P1 · Status: Ist — Feldarten: Text · langer Text · Zahl (mit Min/Max) · Datum · Zeitraum von–bis · Auswahl · Mehrfachauswahl · Ja/Nein · „Ich bestätige“ (Häkchen mit Text) · Unterschrift (Name; das Datum setzt der Server) · Datei-Upload (PDF oder Foto, höchstens 5) · Schüler/in (Kind) · Stundenauswahl · Skala 1–5 (Beschriftung der Enden; in Umfragen genutzt, KUR-065). Je Feld: Beschriftung, Hilfetext (Hilfe-Symbol), Pflicht, Reihenfolge. Obergrenzen für Felder, Schritte, Optionen, Dateien, Textlängen (kurz/lang) und Zeitraum in Tagen sind festgelegt [unklar: Werte]. Eingaben werden gesäubert.
Abnahme: Pflichtfeld leer → Fehler am Feld; Unterschrift ohne Namen → abgelehnt; Datei-Feld lehnt die 6. Datei ab.

**FOR-005** · P1 · Status: Ist — Zielgruppe: Rollen (Eltern, volljährige Schüler/innen, alle Schüler/innen, Lehrkräfte, Sekretariat, Schulleitung) kombiniert mit Klassen, Jahrgängen oder „alle“; die Klassenangabe gilt für die Klasse des Kindes. „Nur einmal je Kind“ verhindert Doppelabgaben (abgelehnte und zurückgezogene zählen nicht). Eltern volljähriger Kinder sehen und füllen nur mit Freigabe „Dokumente“ (`parent_access`). Wunsch: Formulare „pro Schule, Jahrgang oder Gruppe“ („die IT-Klassengruppen, die Fachabi für die Abi-Gruppen, für die Grundschüler, … für die Mittelstufe, für die Oberstufe, für Maler, Lackierer“), vorausgefüllt, „muss nur noch unterschrieben werden“.
Abnahme: Formular nur für Klasse 10a → Eltern der 10b sehen es nicht; „nur einmal je Kind“: zweite Einreichung → 409; nach Ablehnung ist neue Einreichung möglich.

**FOR-006** · P1 · Status: Ist — Prüfschritte (bis zu vier, nacheinander): Klassenleitung des Kindes (Klasse ohne Klassenleitung: Sekretariat) · Sekretariat · Schulleitung · bestimmte Person (nur Schulleitung, Sekretariat oder Lehrkräfte). Die Schulleitung kann jeden Schritt übernehmen. Ohne Prüfschritt landet die Einreichung im Eingang und wird dort „als erledigt“ abgeschlossen; „Sofort erledigt“ beendet sie ohne Prüfung (z. B. Rückmeldungen; Gefahr, weil Daten ungeprüft verarbeitet werden – nur bewusst einsetzen). Ablehnen verlangt eine Begründung, die die Familie sieht. Entscheidungen: genehmigen, ablehnen, erledigen, kommentieren.
Abnahme: Ablauf Klassenleitung → Schulleitung: Schritt 2 erst nach Schritt 1; Ablehnung ohne Begründung → abgelehnt; Fachlehrkraft kann nicht entscheiden.

**FOR-007** · P1 · Status: Ist — Fristen: „Ausfüllbar ab / bis“; „Bearbeitung innerhalb x Tagen“ (danach gilt die Einreichung als überfällig); „Erinnerung nach x Tagen“ (Hinweis an die Prüfenden, Wiederholung nach derselben Zeit, im Wartungslauf). Familien sehen für „Rückmeldung fehlt noch“ nur Zähler und Kachel, keine Einzelnachricht.
Abnahme: Erinnerung nach 3 Tagen → Prüfende erhalten Hinweis; nach weiteren 3 Tagen erneut; Familie erhält keine Einzelnachricht.

**FOR-008** · P1 · Status: Ist — Aktionen bei Genehmigung (bzw. sofort bei „Sofort erledigt“): (a) Beurlaubung bzw. Krankmeldung anlegen – über die vorhandene Abwesenheitsfunktion mit den Rechten der entscheidenden Person und allen Prüfungen (Schultage, Überschneidungen, Rückwirkung), Felder werden dem Formular zugeordnet (Kind, Zeitraum, Stunden, Anlass), Status „genehmigt/entschuldigt“ bzw. „gemeldet“; (b) Lehrkräfte informieren – Hinweis ohne Inhalt an die Lehrkräfte des Kindes, die Beurlaubung erscheint in „Fehlt heute in meiner Stunde“; (c) Termin eintragen – Klassentermin, Titel fest, keine persönlichen Angaben, keine Raumbuchung. Schlägt eine Aktion fehl (z. B. Wochenende, fehlendes Recht), bleibt die Genehmigung bestehen, die Meldung steht im Ergebnis, der Eingang kann „Aktionen erneut ausführen“. Für (a) muss die entscheidende Person für die Klasse melden dürfen (Klassenleitung, Sekretariat); die Schulleitung ohne dieses Recht lässt das Sekretariat wiederholen.
Abnahme: Beurlaubung für Samstag genehmigt → Genehmigung bleibt, Ergebnis nennt den Fehler, „Aktionen erneut ausführen“ mit korrigiertem Zeitraum legt die Abwesenheit an; Lehrkräfte sehen nur „fehlt“, keinen Grund.

**FOR-009** · P1 · Status: Ist — Ausfüllen: eine Spalte, große Berührflächen (mindestens 44 px), Handy-tauglich; online ausfüllen oder leeres PDF öffnen; Antworten werden vor dem Absenden geprüft (Fehlerliste mit Feldbezug, nie technische Namen); bei mehreren Kindern Kinderauswahl; es erscheinen nur Formulare, die die Person ausfüllen darf; bei übernommenen Beispielen der Link „Bisheriger Vordruck“.
Abnahme: 390 px ohne seitlichen Bildlauf; Familie mit zwei Kindern wählt das Kind; fremdes Formular nicht auffindbar (404).

**FOR-010** · P1 · Status: Ist — Einreichung: Status `eingereicht` → `in_pruefung` → `genehmigt` | `abgelehnt` | `erledigt` oder `zurueckgezogen`; zurückziehen nur, solange noch kein Schritt begonnen hat; Verlauf mit Prüfschritten (erledigt, aktuell, abgelehnt), Scans und Anhängen. Doppelklick-Schutz: gleiche Antworten derselben Person für dasselbe Formular und dasselbe Kind innerhalb von 5 Sekunden → 409 (ein Doppelklick auf „Absenden“ erzeugt keine zweite Einreichung); abgelehnte oder zurückgezogene Einreichungen zählen nicht, erneutes Einreichen ist möglich.
Abnahme: zwei Absende-Anfragen innerhalb 1 Sekunde → eine Einreichung; Zurückziehen nach Beginn von Schritt 1 → abgelehnt.

**FOR-011** · P1 · Status: Ist — Eingang: Berechtigte sehen die Einreichungen und entscheiden; Menü-Abzeichen = Zahl der Einreichungen, die auf die eigene Entscheidung warten (Familien: erwartete Einreichungen). Anzeige-Rollen ohne ausdrückliches Formular-Recht erhalten eine ausdrückliche Abweisung (Zusammenfassung → 403 „eingeschränkte Anzeige“; das Abzeichen ignoriert sie still). Zuschauer und Monitor werden bei der Formular-Übersicht abgewiesen (Monitor sieht keine Fehlermeldung, nur keinen Zähler); Formular-Eingang und Zugangsbriefe sind der Zuschauer-Rolle entzogen. Hinweis: eine ältere Beschreibung ließ Zuschauer den Eingang lesen – die spätere Entscheidung (10-16) gilt.
Abnahme: Zuschauerkonto ruft Eingang auf → 403; Monitor zeigt keinen Zähler; Klassenleitung sieht Zähler nur für die eigene Klasse.

**FOR-012** · P1 · Status: Ist — PDF und Scan: leeres Formular zum Ausdrucken (Wunsch: „direkt runterladen und direkt bei dem Ding reinschreiben können“ – Auslegung: herunterladen und direkt ausfüllen), ausgefülltes Archiv-PDF (mehrseitig A4, mit Verlauf), PDF einer einzelnen Einreichung, Sammel-PDF, Vorschau ungespeicherter Formulare; QR-Codes einbettbar. Scan: unterschriebenes Foto oder PDF an die Einreichung hängen (Büro oder Lehrkraft) und entfernen; Zugriff nur für Beteiligte über die Einreichungs-Zugriffsregel (falscher Zweck oder Pfad → 404/403). Die PDF-Schrift muss alle verwendeten Zeichen unterstützen (das alte System konnte „→“ nicht).
Abnahme: Archiv-PDF enthält alle Antworten und den Verlauf; Scan eines Fremden öffnen → 404; Sonderzeichen im Titel erscheinen korrekt.

**FOR-013** · P1 · Status: Ist — Export der Eingangsliste je Vorlage: CSV (Semikolon, UTF-8 mit BOM, Schutz vor Formeln in Zellen) und PDF aller sichtbaren Einreichungen; jeder Export wird protokolliert. Listen und PDF-Export dürfen nicht bei 300 Einträgen abgeschnitten werden (Fehler des alten Systems).
Abnahme: 301 Einreichungen → alle im Export; Zelle „=1+1“ wird entschärft; Exportaufruf erzeugt einen Protokolleintrag.

**FOR-014** · P2 · Status: Ist — Bibliothek mit sieben Vorlagen: Beurlaubungsantrag (legt Beurlaubung an, informiert Lehrkräfte), Schriftliche Entschuldigung (legt Fehlzeit als entschuldigt an), Einverständnis Klassenfahrt, Foto-/Medien-Einwilligung, Rückmeldung Elternabend, Antrag Nachteilsausgleich (Klassenleitung, dann Schulleitung), Schulbescheinigung anfordern. „Übernehmen“ legt eine Kopie als Entwurf an, die die Schule anpasst und veröffentlicht; die festen Vordrucke (Entschuldigungs- und Beurlaubungs-PDF) und der bisherige Ablauf bleiben unverändert.
Abnahme: „Übernehmen“ → Entwurf mit Feldern, Prüfschritten und Aktion; fester Vordruck weiterhin abrufbar.

**FOR-015** · P1 · Status: Ist — Entschuldigung und Beurlaubung digital oder auf Papier (Wunsch 10-12): fertige Formulare, digital ausfüllbar oder als PDF zum Unterschreiben und Hochladen; vorausgefüllt (Kind, Klasse). Die Wirkung auf Fehlzeiten (schriftliche Entschuldigung macht Stunden entschuldigt) beschreibt KLB.
Abnahme: digitale Entschuldigung genehmigt → Fehlzeit „entschuldigt“; PDF-Weg: Scan hochgeladen, vom Büro erfasst → gleiche Wirkung.

### FOR.2 Rechte, Schutz, Aufbewahrung

**FOR-016** · P0 · Status: Ist — Rechte: forms.submit (Eltern, Schüler/innen, Lehrkräfte, Sekretariat, Schulleitung), forms.inbox (Schulleitung, Sekretariat; Lehrkraft/Abteilungsleitung nur als Klassenleitung der eigenen Klasse), forms.manage (Administration, Schulleitung, Sekretariat; gestalten ohne Einblick in ausgefüllte Formulare). Die technische Administration hat forms.manage, aber nie forms.inbox oder forms.submit – fest, nicht freischaltbar. Seite und Menü sind sichtbar, wenn mindestens eines der drei Rechte vorliegt.
Abnahme: Administrationskonto öffnet Einreichung → 403/404; Sekretariat gestaltet und sieht Einreichungen; Lehrkraft sieht nur Einreichungen ihrer Klasse.

**FOR-017** · P0 · Status: Ist — Sichtbarkeit einer Einreichung: einreichende Person; Eltern des Kindes (volljährige nur mit Freigabe); das Kind selbst; Schulleitung und Sekretariat; Klassenleitung nur für die eigene Klasse; benannte Prüfperson im eigenen Schritt. Fachlehrkräfte, Planung, Hausmeister und technische Administration sehen keine Inhalte (404 bzw. 403).
Abnahme: Rechte-Matrix-Test über alle Rollen; Fachlehrkraft ruft Einreichung eines Schülers auf → 404.

**FOR-018** · P0 · Status: Ist — Schutz: Antworten, Vermerke, Verlaufsnotizen sind verschlüsselt und an die Einreichungs-ID gebunden (nicht vertauschbar); Scans und PDFs in der verschlüsselten Dateiablage, nur für Beteiligte; Protokoll bei Ansehen, PDF und Export von Formularen mit „geschützte Angaben“ (`form_submission.view`, `.pdf`, `.export`) und bei allen schreibenden Aktionen, ohne Inhalte; CSV mit Formelschutz.
Abnahme: Datenbankauszug zeigt Antworten nur als Chiffrat; Ansehen einer geschützten Einreichung erzeugt einen Eintrag.

**FOR-019** · P0 · Status: Ist — Aufbewahrung: abgeschlossene Einreichungen werden nach `SM_STUDENT_DOCS_RETENTION_DAYS` (Standard 400 Tage, 0 = aus) samt Dateien und Verlauf gelöscht (höchstens 5000 je Wartungslauf); nach Austritt der Person nach 90 Tagen; die Selbstauskunft enthält die eigenen Einreichungen. [unklar: Ablauf bei nicht gesetzter Frist; die Löschung darf nie über einen Sammelwert „0“ abgeschaltet werden, siehe DAT]
Abnahme: Einreichung abgeschlossen vor 401 Tagen → nach dem Lauf samt Scan gelöscht; Person tritt aus → nach 90 Tagen weg.

**FOR-020** · P0 · Status: offen — Zugriffsprüfung je Objekt im Neubau: Einreichungsliste, Eingang und Export sind ausdrücklich mit forms.inbox bzw. forms.manage-Regeln (Klasse, Schritt, Rolle) abgesichert, die Sichtbarkeit steckt in der Abfrage (nicht nachträgliches Filtern); das alte System wies diese Prüfung an den Routen nicht aus.
Abnahme: direkter API-Aufruf der Liste/des Exports mit Konto ohne Recht → 403/404; Konto mit Recht für Klasse A erhält nie Einreichungen der Klasse B.

**FOR-021** · P2 · Status: Ist — Benachrichtigungen: bei Entscheidung (`request_decided`) erhält die einreichende Person (plus Familie) einen Hinweis ohne Grund und Inhalt; Prüfende erhalten Erinnerungen; der Baukasten verschickt selbst keine Nachrichten in Nachrichten oder per E-Mail, nur Hinweise in der App und Zähler.
Abnahme: Genehmigung → Hinweis ohne Begründungstext; keine Brief-Nachricht entsteht.

**FOR-022** · P2 · Status: offen — Weitere Wünsche: Anträge von Schüler/innen und Eltern über die Lehrkraft an Vorgesetzte (zurückgestellt; bisher nur Formularlinks); öffentlicher Formularlink mit QR-Code und Export für Schulanmeldungen (nur auf Nachfrage); automatische Entschuldigung je Grund/Standardgrund der Schule (KLB); Formular-Baukasten-Ergebnisse als Kennzahl in Berichten.
Abnahme: je Funktion eigener Test; bis zur Entscheidung nicht vorhanden.

### FOR.3 Zugangsbriefe und Zugangsdaten

**FOR-023** · P1 · Status: Ist — Zugangsbriefe als PDF beim Anlegen neuer Konten oder Klassen: „PDFs mit den Startdaten … auch für alle Kinder und Eltern einer Klasse“ (die Klassenanlage allein erzeugt noch keine PDFs; Konten müssen angelegt werden). Ablauf: Konten wählen → Stapel erstellen → je Eintrag ein neues Startpasswort, verschlüsselt im Stapel → Downloads (Sammel-PDF, ZIP nur bei mehreren Briefen, Einzel-PDF) → Versand (FOR-027). Grenzen: 500 Konten je Stapel (Anlage über die Oberfläche), 5000 Einträge Speicherung, 2000 Briefe bei direkter PDF-Erzeugung ohne Speicherung, 5000 Konten in einer Auswahl. Klassen-Seite mit Zugang zu den Briefen der Klasse; „Passwort-Status“ je Konto (ob und wann ein Startpasswort gesetzt wurde, nie im Klartext).
Abnahme: Klasse mit 28 Kindern und 40 Eltern anlegen → 68 Briefe im Sammel-PDF, ZIP mit 68 Einzel-PDFs; Auswahl von 501 Konten für einen Stapel → abgelehnt.

**FOR-024** · P0 · Status: Ist — Stapel-Schutz: Lebensdauer 60 Minuten (`SM_LETTER_BATCH_MINUTES`, zulässig 1–1440); danach gelöscht (Wartung oder nächster Zugriff → 410 mit Hinweis); sichtbar nur für die anlegende Person und die Administration (anderen 404); ein Eintrag ist nur für Konten sichtbar, die der Betrachter zurücksetzen darf (Klassenleitung: nur Schüler/innen eigener Klassen). Rechte: Anlage users.manage; Ansehen, Laden, Versenden passwords.reset oder users.manage. Die Stapel-Seite `/zugangsdaten/:id` zeigt Ablauf-Countdown und Einträge, nie Passwörter (nur im PDF); der Stapel wird nur über den Seitenzustand übergeben, nie über Adresse oder lokalen Speicher; Antworten sind nicht zwischenspeicherbar (no-store); jeder Download und Versand wird ohne Passwort protokolliert (`letters.download`, `letters.send`). Die Zuschauer-Rolle hat keinen Zugriff.
Abnahme: Stapel nach 61 Minuten → 410; fremde Lehrkraft ruft Stapel auf → 404; Klassenleitung sieht keine Lehrkraft-Einträge; Protokoll enthält kein Passwort.

**FOR-025** · P1 · Status: Ist — Brief-Inhalt: eine Seite je Brief; Schulname und Produktname aus der Konfiguration, Logo, Datum, Titel, Zugangsdaten-Kasten (Benutzername, Startpasswort), Rolle als Text, QR-Code zur Anmeldeadresse (Basisadresse + `/login`), Anleitung, Hinweise; Anrede „Sie“ für alle Rollen. Das Startpasswort wird nur gedruckt, wenn Passwort-Anmeldung erlaubt ist oder eine Pflicht-Verknüpfung besteht; sonst Hinweis zum Anmeldeweg; bei Pflicht-Verknüpfung der Satz „Verbinden Sie nach dem ersten Anmelden …“. Hinweis zum Passwort: nur Kleinbuchstaben, Ziffern, Bindestriche; kein 0/o, 1/l/i. Titel für Eltern: „Zugangsdaten für die Eltern von …“. Sortierung: Klasse (natürlich), Nachname, Vorname, Schüler/innen vor Eltern, Personal zuletzt. Dateiname `Klasse_Nachname_Vorname.pdf` (Eltern mit `_Eltern`, ASCII, eindeutig); Namenszusätze („van“, „von“) werden beim Aufteilen beachtet.
Abnahme: Brief für eine Schülerin der 5a heißt `5a_Nachname_Vorname.pdf` (Platzhalter), enthält QR zur Anmeldeadresse, kein „du“; Brief für Eltern trägt den Zusatz im Titel und Dateinamen.

**FOR-026** · P0 · Status: Ist — Startpasswort: erzeugt aus 3 Gruppen zu je 4 Zeichen mit Bindestrich (z. B. `xxxx-xxxx-xxxx`, ≈ 59 Bit), Zeichenvorrat 31 Zeichen (Kleinbuchstaben ohne i, l, o; Ziffern 2 bis 9), kryptografisch zufällig; wird nur einmal angezeigt bzw. im Brief gedruckt, gespeichert werden nur der Hash und das Ablaufdatum; Pflicht-Wechsel beim ersten Anmelden; Frist 14 Tage ab Vergabe (Schuleinstellung `initial_password_days`, 1–90); abgelaufen → Anmeldung mit richtigem Passwort abgelehnt (403 `initial_password_expired`, zählt als Fehlversuch); die Marke erlischt bei Passwortwechsel oder Löschen des Kontos. „Passwort zurücksetzen“ durch die Verwaltung erzeugt IMMER ein neues Startpasswort (der Modus „altes Startpasswort wieder gültig“ entfällt); dazu das Angebot „Brief als PDF“ im selben Layout, das Einmalpasswort wird einmal angezeigt.
Abnahme: Startpasswort am Tag 15 → 403; nach Passwortwechsel keine Marke mehr; Datenbankauszug enthält keinen Klartext; Zurücksetzen erzeugt ein anderes Passwort.

**FOR-027** · P1 · Status: Ist — Versand per E-Mail: Ziel `student`, `parents` oder `both`; volljährige Schüler/innen nie über Eltern; eine Mail je Person und Adresse mit dem Brief als PDF-Anhang; Adressen dedupliziert; Personen ohne Adresse werden gesondert gemeldet; Vorschau und Zusammenfassung („wer ist erreichbar, wer nicht“) vor dem Senden; nur an aktive Elternkonten mit Adresse; Betreff für Schüler/innen „Ihre Zugangsdaten für …“, für Eltern „Zugangsdaten Ihres Kindes … für …“; der Mailtext enthält kein Passwort und weist auf das Löschen der Mail nach Festlegen des eigenen Passworts hin; nicht verfügbarer Versand liefert eine eigene Rückmeldung.
Abnahme: Versand für Volljährigen mit Ziel `both` → nur an ihn; Mailtext ohne Passwort; 3 Personen ohne Adresse erscheinen in der Zusammenfassung.

**FOR-028** · P1 · Status: Ist — Familien: ein Elternkonto für alle Kinder (Kinder werden dem Konto zugeordnet, Geschwister bekommen kein zweites Konto); je Kind und Elternteil ein Brief nur bei eigenem Konto; Eltern volljähriger Kinder erhalten keinen Brief mit den Zugangsdaten des Kindes. [unklar: zweite Zugangsdaten für einen zweiten Erziehungsberechtigten im selben Konto]
Abnahme: Eltern mit zwei Kindern erhalten einen Brief mit beiden Kindern; Eltern eines Volljährigen erhalten keinen Kindesbrief.

**FOR-029** · P1 · Status: offen — Einmal-Login statt Startpasswort. Wunsch (10-12): „Ich habe keine Beispiel für PDF gesehen für einen Einmallogin“ – Einmal-Login-PDFs für Lehrkräfte, Schüler/innen und alle weiteren Rollen; im Neubau nur Einmal-Login: Der Zugangsbrief enthält einen einmaligen, befristeten Zugang (Einmalcode oder QR-Code), der nach Gebrauch verfällt und zum Setzen des eigenen Passworts führt; kein wiederverwendbares Passwort im Brief. Das bisherige Startpasswort mit Pflicht-Wechsel (FOR-026) gilt nur als Übergang. QR-Login für Kinder (Klasse 1 bis 4) nur auf Nachfrage und erst nach Klärung von Einmal-Token, Ablauf, Anmelderichtlinie und Sicherheitsfragen. [unklar: Gültigkeitsdauer des Einmal-Zugangs und Verhalten bei Verlust]
Abnahme: Einmal-Zugang aus dem Brief funktioniert genau einmal; zweite Benutzung und Benutzung nach Ablauf → abgelehnt; Datenbank enthält nur Hash des Einmal-Zugangs.

**FOR-030** · P0 · Status: offen — Inhaber-Schutz und Sammelwege: Der Schutz des Inhaber-Kontos (nicht herabstufen, deaktivieren oder zurücksetzen) gilt zentral im Dienst für ALLE Wege, auch für Zugangsbrief-Stapel und Massen-Reset (im alten System umging der Stapel den Schutz); Massen- und Einzelaktionen nutzen dieselbe Prüfung je Objekt; das eigene Konto ist über einen Stapel nicht zurücksetzbar (sonst endet die eigene Sitzung).
Abnahme: Stapel mit dem Inhaber-Konto durch einen zweiten Administrator → abgelehnt; Stapel mit dem eigenen Konto → abgelehnt.

**FOR-031** · P2 · Status: offen — Konten beim Import optional mit anlegen, inklusive Zugangsbriefen (Personen ohne Konto werden bisher erst nach dem Anlegen der Konten ergänzt); Einzel-Zugangsbrief auch ohne Klasse (Mangel des alten Systems); die Kinderliste der Eltern wird in einem Aufruf übertragen (kein halber Stand).
Abnahme: Import mit Option „Konten anlegen“ erzeugt Stapel; Einzelbrief für Lehrkraft ohne Klasse möglich; Abbruch mittendrin lässt keinen halben Stand.

**FOR-032** · P2 · Status: Ist — Testzugänge und Beispielbriefe: Beispiel-Zugangsbriefe für zehn Rollen sind Muster ohne echte Passwörter; Testzugänge zum Ausprobieren aller Funktionen liegen in einer Datei des Betreibers, nie in Dokumenten des Pakets; Benutzernamen sind gut tippbar (klein, ASCII, ä→ae, ß→ss) und die Eingabe unterscheidet nicht nach Groß-/Kleinschreibung (Handys machen daraus gern Großbuchstaben); Änderungen an Testzugängen werden vorher angekündigt.
Abnahme: Anmeldung mit „MUSTER.A“ statt „muster.a“ gelingt; Beispielbrief enthält keinen echten Zugang.

**FOR-033** · P3 · Status: Ist — Druck: eigene Druckansicht der Zugangsbriefe (`/druck/zugangsbriefe`, Daten aus dem Seitenzustand, nie aus der Adresse); Drucke bleiben außerdem nur für Vertretungsplan-Aushang und schriftliche Entschuldigung vorgesehen. [unklar: Vollständigkeit der Druckansicht wurde in der Marktreife-Prüfung nur mehrdeutig gefunden]
Abnahme: Druckansicht eines Stapels zeigt dieselben Briefe wie das Sammel-PDF; Adresse enthält keine Zugangsdaten.

**FOR-034** · P2 · Status: Ist — Bedienung der Formulare und Briefe: alle Texte „Sie“ (auch in Briefen und für Schüler/innen), Erklärungen nur über das Hilfe-Symbol, App-Dialoge statt Browser-Popups, Fehlertexte für Menschen ohne Codes, Farbe nie allein, Tastaturbedienung; Handy-Ansicht des Ausfüllens ausdrücklich verlangt (FOR-009), für die Verwaltungsseiten gilt 390 px ohne seitlichen Bildlauf.
Abnahme: Textprüfung findet kein „du/dein“ in Formularen, Briefen und Mails; Rundgang bei 390 und 1280 px ohne Befund.

---

## Anhang A – Kennzahlen und Grenzen

| Wert | Einheit | Wirkung | Bezug |
|---|---|---|---|
| 30 (zulässig 1–365) | Tage | Papierkorb der Kursräume, danach endgültige Löschung | KUR-061 |
| 25 (zulässig 1–10 240) | MB | größte Datei je Upload (`SM_UPLOAD_MAX_MB`) | KUR-014 |
| 2000 / 200 | MB | Dateikontingent je Konto Personal / Schüler (`SM_QUOTA_MB_STAFF`, `_STUDENT`) | KUR-014 |
| 20 / 10 | Anhänge | je Material oder Abgabe / je Pinnwand-Beitrag, Rückmeldung, Nachricht | KUR-015, NAC-034 |
| 6 | Ebenen | Ordnertiefe im Kursraum | KUR-011 |
| 92 / 81 / 67 / 50 / 30 | Prozent | Notenschwellen 1 bis 5 des Standardschlüssels | KUR-032 |
| 90 / 30 | Tage | Löschung nach Austritt: Abgaben, Lernaktivitäten, Fortschritt / hochgeladene Dateien | KUR-078 |
| 5 MB, 4 | MB, Bilder | Chat-Bild je Datei, Bilder je Nachricht | NAC-014 |
| 500 / 100 / 1000, 30 | MB, Uploads | Chat-Bildkontingent Personal / Schüler,Eltern / je Chat; Uploads je 10 Minuten | NAC-015 |
| 400, 10 | Mitglieder, Geräte | höchstens je Chat, höchstens je Person | NAC-008, NAC-022 |
| 8 Zeichen, 15, 10 | –, Minuten, Versuche | Gerätecode, Gültigkeit der Anfrage, Fehlversuche je 10 Minuten | NAC-025 |
| ≥ 12, 125, 1 000 000 | Zeichen, Bit, Runden | Backup-Passwort, Wiederherstellungscode, Schlüsselableitung | NAC-027 |
| 24 | Stunden | Gültigkeit des Doppelsende-Schlüssels; Verfall loser Chat-Uploads | NAC-012, NAC-014 |
| 20 000, 10, 20 000 | Zeichen, Anhänge, Empfänger | Brieftext, Anhänge, Empfänger je Nachricht | NAC-034 |
| 25 | Empfänger | Einzelempfänger ohne messages.broadcast | NAC-035 |
| 365 | Tage | Aufbewahrung Briefe/E-Mail-Kopien (`messaging_retention_days`) | NAC-046 |
| 1 | Monat | gewünschte Chat-Aufbewahrung (außer Stern) | NAC-018 |
| 5,0 / 10 | Minuten / MiB | E-Mail-Abrufintervall / Mailanhang beim Abruf | NAC-042 |
| 993 / 587 | Port | IMAP / SMTP der Mail-Anbindung | NAC-041 |
| 10 | je Stunde | Verbindungsversuche je Mail-Konto | NAC-041 |
| 200 | Zeichen | Titel einer Mitteilung / einer Formularvorlage | NAC-044, FOR-002 |
| 5 | Sekunden | Doppelklick-Schutz bei Formular-Einreichungen | FOR-010 |
| 4 | Schritte | Prüfschritte je Formular | FOR-006 |
| 5 | Dateien | Datei-Upload je Formularfeld | FOR-004 |
| 400 / 90 | Tage | Aufbewahrung abgeschlossener Einreichungen / nach Austritt | FOR-019 |
| 5000 | je Lauf | höchstens gelöschte Einreichungen je Wartungslauf | FOR-019 |
| 60 (zulässig 1–1440) | Minuten | Lebensdauer eines Zugangsbrief-Stapels | FOR-024 |
| 500 / 5000 / 2000 / 5000 | Konten bzw. Briefe | je Stapel (Oberfläche) / Speicherung / direkte PDF-Erzeugung / Auswahl | FOR-023 |
| 14 (zulässig 1–90) | Tage | Frist des Startpassworts | FOR-026 |
| 3 × 4, 31 | Zeichen | Aufbau und Zeichenvorrat des Startpassworts | FOR-026 |
| 500 ms, 95 % | Millisekunden | Lastziel für Anfragen bei 2500 Schüler/innen, 300 Lehrkräften | NAC-060 |

## Anhang B – Offene Entscheidungen des Betreibers (Vorgabe bis zur Klärung)

| Frage | Vorgabe bis zur Klärung | Bezug |
|---|---|---|
| Orange-Markierung für „zu spät/früher gegangen“ im Kursraum | keine Orange-Markierung | KUR-052 |
| Eltern im Fachraum: Pinnwand und Teilnehmende sichtbar? | nein | KUR-006 |
| Schüler↔Schüler-Nachrichten: Voreinstellung | aus | NAC-005 |
| Rundschreiben an Volljährige ohne Wahl: nur Schüler oder beide | nur Schüler | NAC-037 |
| Brief-Entwürfe behalten | ja, nur im Brief, nie im Chat | NAC-039 |
| „Nur schreiben ohne Lesen“ als Gruppenrecht | nicht vorgesehen | NAC-009 |
| Meldende/Gemeldete über Moderationsentscheidung informieren | nein | NAC-030 |
| Prüfung gemeldeter Chat-Auszüge nur mit Einwilligung (chats.review) | Einwilligung Pflicht | NAC-031 |
| Chat-Schlüssel nach Abmeldung entfernen; Option „Gerät merken“ | entfernen, keine Option | NAC-024 |
| Aufbewahrung Chat (1 Monat, Stern) und Postfach-Wert „0 = nie“ | Chat 1 Monat; „0“ nicht zulässig | NAC-018, NAC-046 |
| Übersetzungsdienst (lokal oder Fremdanbieter) | kein Dienst | NAC-054 |
| Einwilligungsalter für eigenständige Einwilligungen | nicht festgelegt | NAC-053 |
| Audit-Ausnahmen (Chat-Senden/Lesestand, Selbsttest-Zwischenspeichern) | Ausnahmen gelten | NAC-032, KUR-076 |
| Mindestteilnehmerzahl für anonyme Umfragen | nicht festgelegt | KUR-066 |
| Wer fremde Pinnwand-Beiträge löschen darf | Verfasser/in und Lehrende des Raums | KUR-025 |
| Einmal-Login: Gültigkeitsdauer, Verlust | nicht festgelegt | FOR-029 |
| Statuswerte/Kategorien der Formulare, Löschregel von Vorlagen | nicht festgelegt | FOR-002 |

## Anhang C – Abgrenzung zu anderen Dateien

| Thema | Gehört nach | Hinweis |
|---|---|---|
| Hausaufgabe an der Stunde, Anzeige „HA 2“ im Stundenplan, Klassenraster | STP | hier nur Aufgabe, Frist und Link (KUR-026, KUR-053) |
| Anwesenheit, Thema, Hausaufgabentext, Fehlzeiten, Atteste, Schülerdokumente | KLB | Quelle des Tabs „Unterricht“ (KUR-050/051) |
| Notenbuch, Übernahme von Aufgaben-, Test- und Klausurnoten, Kompetenzen | NOT | Schnittstelle in KUR-037/070 |
| Schulkalender, Schuljahr, Klassenrollen, Einrichtung | STA | Elternabend (KUR-056) |
| Eltern-Freigabe für Volljährige, Schulbegleitung, Rollen und Umfang | SCH, REC | Rechte-Tabelle in 0.2 |
| Einmalcode/QR-Anmeldung, Zwei-Faktor, Startpasswort-Anmeldung | ANM | hier nur Brief und Frist (FOR-025 bis FOR-029) |
| Löschkonzept, Auskunft, Beobachtungsprotokoll, Verschlüsselung | DAT | hier nur Fristen der eigenen Daten |
| Glocke, E-Mail-Hinweise, Push, Ruhezeiten | BEN | hier nur Auslöser aus Kursräumen/Nachrichten/Formularen |
| Import (Moodle, Untis, CSV), LTI, API-Zugänge | INT | KUR-073/081, FOR-031 |
| Lizenz-Zugangsblatt und Rechnungen als PDF, Demo | BET | Anbieter-Portal |
| Hilfe-Symbol, Sie-Anrede, Raster, Dialoge, Barrierefreiheit | OBE, PRI | gelten hier ohne Wiederholung |

<!--ENDE-->
