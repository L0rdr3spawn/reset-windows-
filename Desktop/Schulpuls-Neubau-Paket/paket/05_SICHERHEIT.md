# 05 SICHERHEIT – Pflichtenheft Sicherheit (SIC) und Datenschutz-Technik (DAT)

Paket „Schulpuls“ (Neubau). Dieses Dokument legt fest, **was** das System an Schutz leisten muss, mit welchen Werten und womit es geprüft wird. Es enthält keinen Code des Altsystems und keine Angriffsanleitungen. Alle Abnahme-Prüfungen sind **verteidigend**: Eine Prüfung belegt, dass ein Schutz greift, ein Protokolleintrag entsteht und keine Daten austreten.

## 0 Lesehinweise

- **Kennungen:** `SIC-nnn` = Sicherheit (quer), `DAT-nnn` = Datenschutz-Technik (Verschlüsselung, Schlüssel, Protokolle, Beobachtung, Löschkonzept, Auskunft, Wartung). Beide Zählungen laufen in dieser Datei ab 001.
- **Priorität:** P0 = Pflicht (Sicherheit/Recht). P1 nur dort, wo eine Anforderung einen Schutz bewusst lockert oder optional ist.
- **Status:** `Status: Ist` = im Altsystem gebaut, mindestens so zu übernehmen. `Status: offen` = gewünscht, in einer Prüfung gefordert oder im Altsystem nur teilweise gebaut (Teilstand steht in Klammern).
- **Abnahme:** genau eine Zeile je Anforderung. Alle Abnahmen laufen auf einer isolierten Wegwerf-Instanz (SIC-009). Kurzform „fremdes Objekt → 404“ meint: Status 404, gleicher Antworttext wie bei nicht vorhandener ID, keine Daten, Laufzeitunterschied zur nicht vorhandenen ID im Median unter 50 ms [Prüfwert].
- **Rollen:** `admin`, `schulleitung`, `abteilungsleitung`, `planer`, `sekretariat`, `lehrer`, `hausmeister`, `schulbegleitung`, `schueler`, `eltern`, `monitor`, `zuschauer` (12 eingebaute Rollen). Eigene Rollen haben einen Grundtyp (`personal`, `lehrkraft`, `schueler`, `eltern`, `ansicht`); **alle Schutzregeln hängen am Grundtyp**. Rechte-Namen und Umfänge (`all`, `own_classes`, `own_branch`, `class_teacher`, `own_courses`) stammen aus dem Rechte-Katalog (Datei REC).
- **Inhaber-Konto:** das Konto `SM_ADMIN_USER` (Standard `admin`), sonst das älteste Administrationskonto.
- **Zeit:** Protokollzeiten UTC; Fachzeiten Europe/Berlin.
- **Zitate des Betreibers** stehen wörtlich in Anführungszeichen. Unklares: `[unklar: …]`. Prüfwerte, die der Schreiber der Abnahme vorschlägt und die nicht aus den Quellen stammen: `[Prüfwert]`.

### Vorrang bei Widersprüchen (gilt für das ganze Dokument)

| Nr | Gegenstand | Es gilt | Überholt oder verworfen |
|---|---|---|---|
| 1 | 2FA für Administration | Pflicht (Prüfung 17.10.) | Standard „empfohlen“ (16.10.) |
| 2 | Anmeldesperre | gestaffelte Wartezeit (16.10.) | harte Kontosperre je Benutzername (S-04, verworfen) |
| 3 | Startpasswort | nur Hash + Ablaufdatum; „neues Startpasswort erzeugen“ | „altes Startpasswort wieder gültig“ (gestrichen); entschlüsselbare Speicherung |
| 4 | Anmeldung mit 2FA-Konto | zweistufig: Schritt 1 antwortet bei richtigem Passwort `totp_required` (Z2, I10; 16.10.) | einheitliche Antwort wie bei falschem Passwort (S-16, 13.10.). Die Notiz W8 „totp_required entfernt“ widerspricht Z2/I10; maßgeblich ist Z2 (Quelltext vom 18.10.) |
| 5 | Lizenz Offline-Frist | 7 Tage (Betreiber 16.10.) | 30 Tage |
| 6 | Löschfristen | Löschkonzept (Kap. 16) | Überblickstabellen in Sicherheitskonzept, Verzeichnis-Vorlage, Hinweisen („3 Monate“, „Ende Schuljahr plus Zeugnisfrist“) |
| 7 | Sitzungs-Leerlauf Personal | 12 Stunden, einstellbar 15 Minuten bis 7 Tage | Empfehlung „1 Tag“ |
| 8 | Rollen | 12 Rollen (Stand 17.10.) | Übersicht mit 8 Rollen |
| 9 | Passwort-Mindestlänge | Schüler/innen 8, übrige 10 | Hinweistext „10“ für Schüler/innen |
| 10 | Wiederherstellung einer Sicherung | nur per Konsolenbefehl | „Wiederherstellen per Klick“ (Backlog B-05) |
| 11 | API-Token-Laufzeit | Pflichtlaufzeit | „unbefristet möglich“ (Ist) |
| 12 | Löschfrist-Wert „0“ | verboten (keine Abschaltung der Löschung) | Ist: „0 = nie löschen“ |
| 13 | Freie Rechtevergabe | frei mit Warnhinweis, **innerhalb** der festen Mindestregeln (SIC-015 bis SIC-019) | uneingeschränkt „alle Rollen alle Berechtigungen“ (Spannung, siehe Kap. 29) |

---

## 1 Grundsätze (quer)

**SIC-001** · P0 · Status: Ist · **Sicherheit und Datenschutz vor Komfort**
- Bei Zielkonflikt gewinnt der Schutz. Eine Abweichung braucht eine ausdrückliche, dokumentierte Entscheidung des Betreibers (Beispiel: automatische Anmeldung per Anbieter-Dienst ist standardmäßig **aus**, weil Schul-PCs geteilt werden).
- Betreiber-Auftrag: „Du musst wirklich sicher sein … Kannst du doch nochmal bitte explizit drüber gehen.“ Sicherheit wird explizit geprüft, nie pauschal behauptet.
Abnahme: Jedes Funktionspaket enthält im Abnahmeprotokoll einen Abschnitt „Sicherheit“ mit Rechte-/Umfangsregel, Audit-Aktion, Verschlüsselungsfeldern, Löschart und 404-Verhalten; fehlt er, gilt das Paket als nicht abgenommen.

**SIC-002** · P0 · Status: Ist · **Definition of Done Sicherheit je Paket**
- Rechte und Datenumfang im Backend geprüft; bei jeder neuen Sichtbarkeitsregel ein Rechte-Matrix-Test.
- Jede schreibende Aktion im Audit (Ausnahmen nur DAT-031); personenbezogene Freitexte verschlüsselt; Codes und Token nur als Hash/HMAC.
- Zu jedem behobenen Fund ein Regressionstest, der den Fund nachstellt. Geprüft wird **je Objekt und Aktion**, nicht je Route (Lehre aus dem Umgehungsfund über Zugangsbriefe).
- Befunde (auch von Prüf-Agenten) werden vor dem Bau am Code nachgeprüft: In einer Prüfrunde waren von 76 Befunden 11 falsch und 23 unklar.
Abnahme: Die CI bricht ab, wenn (a) eine registrierte Route keine Rechte-/Bereichsdeklaration hat, (b) eine Sichtbarkeitsregel keinen Matrix-Test hat, (c) eine als behoben markierte Befundnummer keinen Test referenziert.

**SIC-003** · P0 · Status: offen (Ist: Selbstaussperr-Schutz im Dienst; Lücke: Inhaber-Schutz wirkte nur im Routen-Handler) · **Schutz im Dienst, nicht im Routen-Handler**
- Jede Schutzregel (Inhaber-Schutz, Selbstaussperr-Schutz, Scope, Eltern-Sicht) liegt in der Dienst-/Domänenschicht. Jeder Zugangsweg ruft denselben Dienst: Einzelroute, Massenroute, Zugangsbriefe, Import, Export, Konsolenbefehl (CLI), API-Zugang, Hintergrundjob.
- Massen- und Einzelaktionen nutzen dieselbe Prüfung je Objekt.
Abnahme: Für jede Schutzregel existiert ein Test je Zugangsweg (UI-Route, Massenroute, Stapel-Zugangsbriefe, Import, CLI, API-Token); alle verweigern mit identischem Ergebnis, und der Audit-Eintrag der Verweigerung entsteht auf jedem Weg.

**SIC-004** · P0 · Status: offen (Ist: Demo-Freigabeliste, Zuschauer-Allowlist; Lücke: Schreib-Token- und Export-Wege als Sperrliste) · **Default-Deny**
- Neue Routen und Funktionen sind für Zuschauer/Ansichtskonten, Demo-Betrieb, API-Schreibzugang und Export **gesperrt**, bis sie ausdrücklich freigegeben sind (Allowlist statt Blocklist).
Abnahme: Ein Test zählt alle registrierten Routen auf; jede Route ohne Freigabe-Eintrag antwortet in diesen vier Kontexten mit Sperre; ein künftiger, nicht freigegebener Eintrag lässt den Test scheitern; veraltete Freigabeeinträge lassen ihn ebenfalls scheitern.

**SIC-005** · P0 · Status: Ist · **Zentrale Registries**
- Jedes Modul mit personenbezogenen Daten meldet sich einmal an mit: Datenart (Bezeichnung, Kategorie, Rechtsgrundlage, Standardfrist, Löschfunktion mit Trockenlauf, Auskunftsfunktion, Betroffenen-Ermittlung), verschlüsselten Spalten (Rotation), Exportformat, Dateizugriffsprüfung je Verweistyp, Zielprüfung für ausgehende Verbindungen, Demo-Freigabe.
Abnahme: Regressionstest scheitert bei (a) einer `_enc`-Spalte ohne Rotations-Eintrag, (b) einer Tabelle mit Personenbezug ohne Datenart, (c) einem Verweistyp für Dateien ohne Zugriffsprüfung, (d) einem Export ohne Registrierung.

**SIC-006** · P0 · Status: Ist · **Keine Geheimnisse in Protokollen, Antworten, Frontend, Repository, Image**
- Nie ausgegeben: Passwörter, Startpasswörter, Token, Schlüssel, Codes, Cookies, `Authorization`-Werte, Datei-Inhalte. Das Einmalpasswort des Erst-Admins steht nie im Log (Datei, siehe SIC-046).
- Antworten mit Zugangsdaten tragen `Cache-Control: no-store`. Passwortfelder sind standardmäßig verdeckt; die Anzeige geschieht nur bewusst.
- Keine personenbezogenen Daten in URLs oder Abfrageparametern; Zugriffsprotokoll und Fehlerprotokoll speichern Pfade ohne Abfrage.
Abnahme: Ein vollständiger Erststart im Produktiv-, Demo- und Entwicklungsmodus erzeugt Logs, die keine der zuvor erzeugten Geheimniszeichenfolgen enthalten (Suche: 0 Treffer); ein Scan des gebauten Frontends und des Images findet keine Schlüssel/`.env`/Kennwörter; Antworten der Startpasswort-Routen haben `no-store`.

**SIC-007** · P0 · Status: Ist · **Keine Orakel**
- Bekannte und unbekannte Konten erhalten gleiche Antwort und gleiche Laufzeit (Scheinprüfung des Passworts; Reset-Anfrage mit Mindestlaufzeit, SIC-053). Fehlermeldungen unterscheiden die Fehlerart nur, wo es für die Person nötig ist und kein Konto verrät.
- Jeder Fehlversuch zählt, unabhängig vom Ergebnis der Prüfung (SIC-093).
Abnahme: 200 Anmeldeversuche mit unbekanntem und 200 mit bekanntem Benutzernamen (falsches Passwort) liefern identischen Statuscode und Text; Median der Laufzeiten unterscheidet sich um höchstens 40 ms [Prüfwert]; dasselbe für die Reset-Anfrage.

**SIC-008** · P0 · Status: offen · **Dokumentation entspricht dem Verhalten**
- Datenschutzerklärung, Verzeichnis (VVT), TOMs und Hinweise an Betroffene werden aus der Konfiguration abgeleitet oder per Test gegen das Verhalten geprüft: IP-Speicherung/-Kürzung, Fremdskripte (Anbieter-Anmeldung), Löschfristen, Empfänger (Hoster, E-Mail-Versand, SMS-Anbieter, Offsite-Backup, Monitoring, Anmeldedienste, Lizenzserver, optionale Passwort-Leak-Prüfung).
- Eine falsche Zusage („IP gekürzt“, tatsächlich voll gespeichert) ist selbst abmahnfähig.
Abnahme: Ein Test liest alle Fristen und Zusagen aus den Textvorlagen und vergleicht sie mit den Konfigurationswerten und dem Verhalten (Zugriffslog-IP gekürzt; Audit-IP wie in DAT-028 entschieden; Fremdskript nur bei aktivem Anbieter); Abweichung = Fehler.

**SIC-009** · P0 · Status: Ist · **Angriffssimulationen nur auf Wegwerf-Instanz**
- Sicherheits- und Lasttests laufen nur auf einer isolierten Instanz (eigene Datenbank, Demo-Daten, nur lokal erreichbar), die danach vollständig entfernt wird. Auf echten Instanzen nur lesende Konfigurationsprüfung. Keine Lastflut gegen gemeinsam genutzte Server; Schutz gegen Massenanfragen wird mit niedrig gesetzter Schwelle nachgewiesen.
- Sicherheitswerkzeuge nur gegen eigene Systeme. Kein Quellcode, keine Schlüssel an kostenlose Fremddienste.
Abnahme: Das Lasttest-Werkzeug verweigert jede Zieladresse außer `localhost`, außer ein ausdrücklicher Schalter (`--ich-darf`) ist gesetzt; das Prüfprotokoll nennt Instanz, Zeitraum und Entfernung der Instanz.

**SIC-010** · P0 · Status: offen · **Externer Penetrationstest vor breitem Einsatz**
- Vor der Auslieferung an die erste Schule: Penetrationstest durch Dritte (oder ein autonomes Prüfwerkzeug auf der Wegwerf-Instanz) und **Wiederholung** nach Behebung der Funde. Abdeckung vollständig: auch Überlastung (kontrolliert), Passwort-Angriffe, fortgeschrittene Fälle.
Abnahme: Ein Prüfbericht mit Datum und Version liegt vor; keine offenen Funde der Stufen „kritisch“ und „hoch“; der Wiederholungstest belegt jede Behebung.

**SIC-011** · P0 · Status: offen · **Prüfnachweis je Release**
- Je Release ein dokumentierter Sicherheitsprüfbericht. Maßstab: OWASP Top 10:2025, ASVS 5.0, DSGVO (Art. 5, 9, 13, 15, 17, 20, 32, 35), BDSG, BFSG/BITV. Der Bericht nennt, was von wem geprüft wurde, einschließlich des Einsatzes KI-gestützter Entwicklung und der menschlichen Prüfung (Haftungsnachweis).
- Ein Rechtsrat ersetzt der Bericht nicht; DSFA, Mustertexte und Löschfristen nach Landesrecht prüft die Schule/der Schulträger oder eine Datenschutz-Fachperson.
Abnahme: Das Release-Verfahren verlangt den Bericht als Anhang; ohne Bericht keine Freigabe.

---

## 2 Zugriffskontrolle, Rollen-Grenzen, 404-Regel

**SIC-012** · P0 · Status: Ist · **Prüfung bei jeder Anfrage**
- Rechte und Datenumfang werden serverseitig bei **jeder** Anfrage neu berechnet (Rollenabweichungen, Zuordnungen, Volljährigkeit, Zweige). Das Frontend blendet nur aus.
- Rechteänderungen wirken sofort, auch bei mehreren Serverprozessen (Abweichungen werden je Anfrage geladen).
Abnahme: Wird einer Rolle ein Recht entzogen, wird dieselbe Sitzung bei der nächsten Anfrage abgewiesen (ohne Neuanmeldung); dasselbe bei Herabstufung des Kontos und bei Wechsel von Klasse/Schuljahr (Umfang ändert sich).

**SIC-013** · P0 · Status: Ist · **404-Regel für fremde Daten**
- Fremde, unsichtbare oder unbekannte Objekte antworten **404** („nicht gefunden“) – gleich wie bei nicht vorhandener ID –, damit nicht erkennbar ist, dass es sie gibt. 403 nur, wo (a) die Person das Objekt sieht, aber die Aktion nicht darf und die Meldung hilft, (b) es kein Konto zu verbergen gibt (Anlegen/Umstellen auf eine nicht verwaltbare Rolle), (c) Inhaber-Konto (SIC-021), (d) Lehrkonto ohne Zuordnung (hilfreiche Meldung), (e) Schreibversuch eines Ansichtskontos (SIC-020), (f) Schreibversuch einer Elternrolle im Kursraum.
- Gilt für Konten, Noten, Notenbuch, Kompetenzen, Klassenbuch, Krankmeldungen, Atteste/Dokumente, Förderdaten, Formulare, Nachrichten, Chats, Kursräume (rund 40 Routen), Klassentermine, Selbstauskunft, Elternzugang, Löschen fremder Dateien, unbekannte Klassen, Benachrichtigungen („anderes: 404“).
- Fachlehrkraft bei Krankmeldung: ohne Unterricht bei der Person → 404; mit Unterricht, aber ohne Zuständigkeit für Status/Vermerk/Löschen → 403; Klassenleitung → 200.
Abnahme: Für **jeden** Endpunkt mit Objekt-ID (automatisch über alle Routen mit Pfadparameter) fragt Konto A (Rolle mit gültigem Recht, aber ohne Bezug zum Objekt) ein Objekt von Konto B ab → 404 und keine Daten; Altsystem-Referenz: 42 Fälle aus Sicht fremder Schüler, Neubau-Ziel: 100 % der ID-Routen.

**SIC-014** · P0 · Status: Ist · **Umfänge (Scopes) und Scope-Helfer je Fachbereich**
- Je Fachbereich ein zentraler Scope-Helfer. Umfänge: `all` (uneingeschränkt), `own_classes` (eigene Klassen/Kurse der Lehrkraft), `own_branch` (eigene Klassen plus Klassen der Zweige), `class_teacher` (nur die geleitete Klasse), `own_courses` (eigene Kurse/Kursteile), „eigene Kinder“ (Eltern, Schulbegleitung), „eigene Person“.
- Klassenleitung ist keine Kontorolle, sondern ergibt sich aus den Stammdaten (Klassenleitung einer Klasse); Zweige (Abteilungen) ergeben `own_branch`.
- Eine Lehrkraft sieht nur den eigenen Plan und die geführte Klasse (samt Schüler/innen); Raumpläne und fremde Lehrerpläne nur Planung, Verwaltung, Schulleitung.
Abnahme: Matrix-Test über (Rolle × Umfang × Fachbereich): je ein Positivfall (eigenes Objekt) und ein Negativfall (fremdes Objekt → 404) für Konten, Pläne, Klassenbuch, Krankmeldungen, Dokumente, Förderdaten, Noten, Kursräume, Nachrichten.

**SIC-015** · P0 · Status: Ist · **Feste Mindestregeln trotz freier Rechtevergabe**
- Jede Rolle kann jedes Recht erhalten (Wunsch des Betreibers 16./17.10.), mit Warnhinweis bei Rechten außerhalb des üblichen Zwecks. Die **festen Mindestregeln** (SIC-016 bis SIC-019) sind davon ausgenommen; sie sind in der Rechte-Oberfläche verschlossen („Schloss“) und werden serverseitig durchgesetzt.
- Overrides werden beim Laden erneut gegen die festen Grenzen gefiltert; unmögliche Abweichungen (Verstoß gegen Aussperr-Schutz, unbekannter Umfang) werden ignoriert.
Abnahme: Ein Versuch, die Administration mit `student_documents.read` auszustatten (Oberfläche und Schnittstelle), wird mit Fehler abgelehnt bzw. in der wirksamen Matrix ignoriert; der Schloss-Zustand der Zelle ist im Rechte-Katalog abrufbar.

**SIC-016** · P0 · Status: Ist · **Technische Administration ohne Gesundheits-, Noten-, Förderdaten**
- `admin` erhält nie `student_documents.read`, `support.read`, `support.manage`, `support.hints`, `chats.review`; keine Krankmeldungen (Gründe, Vermerke, Status) und keine Profile/Anträge von Lehrkräften. Kein automatischer Administrationszugriff auf Dateien.
- Die Administration behält `users.manage`, `settings.edit`, `rights.manage`, `system.admin` (Schutz vor Aussperrung).
Abnahme: Als `admin` (jede Rechtekonfiguration): Abruf von Attest, Förderdatum, Krankmeldungsgrund, gemeldetem Chat, Lehrkraft-Antrag → 404; die Datei-Download-Route fremder Dateien → 404; `users.manage` bleibt trotz Abweichungs-Eintrag wirksam.

**SIC-017** · P0 · Status: Ist · **Eingeschränkte Rollen: Positivliste**
- `schueler`, `eltern`, `schulbegleitung` erhalten ausschließlich eine kleine Positivliste zuweisbarer Rechte und sehen nur `own` bzw. „eigene Kinder“. Nie andere Kinder, nie Personalrechte.
- `schulbegleitung`: keine Elternrechte (`student_absence.report` und `student_documents.read` ausgeschlossen); begleitete Kinder über dieselbe Verknüpfung wie Eltern.
- Recht `gradebook.use` darf bei Eltern/Schüler/innen keinen Zugriff auf fremde Notenbücher geben (Scope-Grenze je Grundtyp serverseitig; Fund P1-08).
Abnahme: Wird `eltern` das Recht `gradebook.use` ohne Scope zugewiesen, kann das Elternkonto kein Notenbuch außer dem Einsichtsumfang der eigenen Kinder lesen oder ändern (jeder Schreibversuch → 403/404); Zuweisung eines Personalrechts an `schueler` wird abgelehnt.

**SIC-018** · P0 · Status: Ist · **Lehrkraft, Abteilungsleitung, Hausmeister, Monitor**
- `lehrer`: Pläne und Schülerdaten nur eigener Klassen (`own_classes`); Atteste und Förderdaten nur als Klassenleitung. `abteilungsleitung`: höchstens eigener Zweig; Atteste/Förderdaten nur als Klassenleitung.
- `hausmeister`: nur Raumpläne, Monitor, Postfach; keine Schülerdaten. `monitor`: nur `monitor.read` (Vertretungsplan eines Standorts, ohne Lehrkraft-Abwesenheiten und ohne Gründe).
Abnahme: Als `lehrer` ohne Klassenleitung: Attest/Förderdaten der eigenen Klasse → 404; als `hausmeister`: jede Schülerdaten-Route → 404; als `monitor`: Monitor-Route liefert keine Abwesenheitsgründe (Feldscan der Antwort).

**SIC-019** · P0 · Status: Ist · **Systemrechte nur für Administration und Schulleitung; Selbstaussperr-Schutz**
- Rechte-, Lizenz-, Anmelde- und Protokoll-Rechte (`rights.manage`, `license.manage`, `login_policy.manage`, `audit.read`) nur Administration und Schulleitung; `system.admin` nur Administration. Postfach-Eigenserver (`mail.custom_server`) vergebbar an Personal, **nie** an Schüler/innen, Eltern, Hausmeister, Monitor.
- Letzter aktiver Administrator: nicht deaktivierbar, nicht löschbar, nicht herabstufbar (409). Eigene Rolle ändern, eigenes Konto deaktivieren oder löschen: verboten (409).
- Betreiber: „Der einzige feste Schutz bei Rechten: der Admin kann sich nicht selbst aussperren.“ (zusätzlich zu SIC-015 bis SIC-018).
Abnahme: Versuch, die Rolle des einzigen aktiven Administrators zu ändern/zu deaktivieren/zu löschen → 409 und Audit-Eintrag; Versuch von `sekretariat`, `rights.manage` zu erhalten → abgelehnt.

**SIC-020** · P0 · Status: Ist · **Zuschauer- und Ansichtskonten sind schreibgeschützt**
- Grundtyp `ansicht` (Rollen `zuschauer`, `monitor`, Ansichtskonten): jede ändernde Anfrage (POST/PUT/PATCH/DELETE) wird serverseitig mit 403 abgewiesen, nicht nur in der Oberfläche; ausdrücklich erteilte Rechte dürfen ändern, nur diese.
- `zuschauer`: Allowlist von 26 Rechten (Pläne, Vertretung, Räume, Stammdaten, Klausuren, Mitteilungen, Einstellungen lesend). Entzogen: Protokoll, Krankmeldungen/Atteste, Förder-, Noten-, Lernstandsdaten, Formular-Eingang, Konten, Zugangsbriefe, Anmelderegeln, gemeldete Chats, Postausgang der Benachrichtigungen (Namen in Betreffzeilen), Schlüssel, Massen-Exporte; `privacy.manage` und `privacy.subject` fehlen.
Abnahme: Ein Rundgang ruft als `zuschauer` **alle** Lese-Adressen auf (Altsystem: 274): nur Allowlist-Adressen liefern Daten, alle anderen 403/404; jede ändernde Anfrage → 403; jede Stammdaten-Exportroute → 403.

**SIC-021** · P0 · Status: offen (Ist: Schutz auf dem direkten Weg; Lücke: Massen-Reset über Zugangsbriefe) · **Inhaber-Schutz auf allen Wegen**
- Betreiber: „Dem Admin soll man grundsätzlich nicht seine Admin-Rechte nehmen können. Das ist der einzige Account, den man nicht seine Rechte wegnehmen kann. Oder dessen Passwort man zurücksetzen kann.“
- Kein anderes Konto (auch keine Administration) darf das Inhaber-Konto herabstufen, deaktivieren, löschen, sein Passwort oder seine 2FA zurücksetzen, seine Sitzungen beenden, seine Rechte-Zuordnungen ändern, es beobachten (DAT-033). Der Inhaber ändert sein Konto selbst.
- Gilt zentral im Dienst für jeden Weg (SIC-003): Einzelroute, Passwort-Reset, Massen-Reset über Zugangsbriefe, Import, CLI-Fremdaufruf. Versuch: 403 und Audit `user.owner_protected`.
- Das Inhaber-Konto bleibt über „Passwort vergessen“ und SSO erreichbar.
Abnahme: Als zweiter Administrator: Herabstufen, Deaktivieren, Löschen, Passwort-Reset (direkt **und** als Eintrag in einem Zugangsbrief-Stapel/Massen-Reset), 2FA-Reset, Sitzungen beenden, Rollenzuordnung → jeweils 403 mit Audit `user.owner_protected`; Inhaber ändert eigenes Passwort → 200.

**SIC-022** · P1 · Status: offen · **Vertretung des Inhabers durch einen zweiten Administrator**
- Betreiber (17.10.): „Es sei denn, es gibt einen zweiten Admin, dem der erste Admin den Zugang gegeben hat, seinen Password zurückzusetzen.“ Ein zweiter Administrator darf das Inhaber-Passwort **nur** zurücksetzen, wenn der Inhaber ihm das ausdrücklich erlaubt hat. [unklar: Bau nicht freigegeben – der Betreiber hat die Rückfrage „Soll ich das bauen?“ nicht beantwortet.]
- Die Erlaubnis ist ein Inhaber-Recht, widerrufbar, im Audit; sie erweitert nur das Passwort-Reset, nichts anderes aus SIC-021.
Abnahme: Ohne Erlaubnis → 403; nach Erlaubnis durch den Inhaber → Reset durch genau diesen Administrator möglich und mit Audit-Eintrag; Widerruf → wieder 403; Herabstufen/Löschen bleibt dem Zweitadministrator weiter verwehrt.

**SIC-023** · P0 · Status: Ist · **Konten-Verwaltung: Umfang und Verbergen**
- `users.manage` hat den Umfang `all`, `no_admins` (alle außer Administration) oder `students_parents` (nur Schüler- und Elternkonten); gilt über die Grundrolle auch für eigene Rollen. Konten außerhalb des Verwaltungs-Umfangs fehlen in der Kontoliste und antworten 404.
- Administrationskonten dürfen nur von Administration geändert werden. Löschen eines Kontos: endgültig, Protokolle pseudonymisiert (DAT-052); Rollen-Löschung erst nach Umhängen aller Konten auf eine Rolle **desselben Grundtyps** (sonst 409).
- Rolle `admin` und eingebaute Rollen sind nicht löschbar; `admin` nicht ausblendbar.
Abnahme: Als `sekretariat` (Umfang `students_parents`): Abruf eines Lehrerkontos → 404 und Konto fehlt in der Liste; Rolle einer Lehrkraft auf `admin` setzen → 403; Löschen einer Rolle mit Konten ohne `move_to` → 409.

**SIC-024** · P0 · Status: Ist · **Administrations-Vergabe-Sperre**
- Konto-Einstellung `no_admin_grant`: das Konto darf keine Administrationskonten anlegen und keine Administrationsrechte vergeben. Für beobachtete Konten (Kap. 15) standardmäßig **an**; abschalten nur der Inhaber. Verstoß: 403 und Audit `user.admin_grant_denied`.
Abnahme: Ein beobachtetes Administrationskonto legt ein Administrationskonto an → 403 und Audit-Eintrag; der Inhaber schaltet die Sperre ab, danach gelingt es; ein anderer Administrator kann sie nicht abschalten (403).

**SIC-025** · P0 · Status: offen (Ist: Zugriffsmatrix gebaut; Lücke: Administration sieht `student_absence.*`-Einträge im Audit mit Schüler-ID und Zeitraum) · **Gesundheitsdaten nur für Zuständige**
- Gründe, Vermerke und Atteste (Art. 9 DSGVO) sehen nur: meldende Person, Familie (Eltern, bei Minderjährigen), volljährige Schüler/innen selbst, Klassenleitung, Sekretariat, Schulleitung. Nie: Fachlehrkräfte (Anzeige „vertraulich“), technische Administration, Zuschauer, Monitor, andere Schüler/Eltern.
- Fachlehrkräfte erhalten höchstens die Schul-Einstellung `subject_teacher_absence_view`: `none` (Standard) oder `presence` („fehlt heute in meiner Stunde“: Name und Stunde, ohne Status, Attest, Grund, meldende Person; berechnet über tatsächliche Kursteile).
- Gründe erscheinen nie in Exporten, iCal-Feed, Monitor, Benachrichtigungen (Mail/Glocke/Push), Protokollen. Untis-Export enthält Abwesenheitsgründe nur auf ausdrücklichen Wunsch. Das Audit führt Zugriffe auf Gesundheitsdaten **ohne** Schüler-ID/Zeitraum für Leser ohne Gesundheitsrecht (Maskierung).
Abnahme: Rollenmatrix für Krankmeldung: Fachlehrkraft ohne Unterricht bei der Person → 404; mit Unterricht, Status setzen → 403; Klassenleitung → 200; `admin` liest Grund → 404; Feldscan von Export, iCal, Monitor, Mails: kein Grundfeld; `admin` mit `audit.read` sieht für `student_absence.*` keine Schüler-ID/Zeitraum.

**SIC-026** · P0 · Status: offen (Ist: Krankmeldungen, Kursräume; offen: Stundenplan-Abruf, iCal, Dokumente) · **Volljährigkeit und Elternzugriff**
- Volljährig ist, wer laut Geburtsdatum 18 ist (Stichtag Europe/Berlin, Auswertung bei **jeder** Anfrage, Wechsel am Geburtstag ohne Zutun); nur ohne Geburtsdatum zählt das Konto-Flag „volljährig“. Minderjährige Schüler/innen melden sich nie selbst krank.
- Eltern minderjähriger Kinder sehen, was das Kind sieht. Bei Volljährigen gilt die Schulvorgabe `adult_parent_access_default` (Standard: keine Einsicht), bis die Person selbst je Bereich freigibt: Kursräume (inkl. Hausaufgaben), Stundenplan, Krankmeldungen und Fehlzeiten, Dokumente und Atteste, Mitteilungen und Noten; zusätzlich „Informationen der Schule gehen an: mich / meine Eltern / beide“ (Standard ab 18: nur die Person). Freigaben jederzeit widerrufbar, jede Änderung im Audit (ohne Inhalte). Förderdaten nur für Minderjährige.
- Der Elternzugriff endet mit der Volljährigkeit **für alle Ausgaben**: Pläne (`GET /timetable/student/{id}`), iCal-Feed, Dokumente, Krankmeldungen, Benachrichtigungen, Export/Auskunft, Kursräume.
Abnahme: Mit fester Uhr: Kind wird am Tag X 18 → ab 00:00 Europe/Berlin liefern Eltern-Abrufe von Plan, iCal-Feed, Dokumenten, Krankmeldungsgründen 404/leer, solange keine Freigabe besteht; Freigabe „Stundenplan“ → Plan sichtbar, Dokumente weiter 404; Widerruf → sofort wieder 404.

**SIC-027** · P0 · Status: offen (Ist: Geburtsdatum nur mit Recht; Lücke: Sammel-API und Export) · **Ein Feldregelwerk für alle Ausgaben**
- Für jedes sensible Feld gilt **ein** zentrales Regelwerk für Einzelansicht, Liste, Export, Feed (iCal), API-Zugang und Auskunft. Beispiele: Geburtsdatum nur mit Recht `students.birth_date` (Sekretariat, Schulleitung, Administration, Klassenleitung der eigenen Klasse) oder für die Person selbst; Kurswahl gestuft (vollständig nur Planung/Verwaltung und die Betroffenen; übrige Lehrkräfte nur echte Wahlen in mehrteiligen Kursen); Abwesenheitsgründe nie in Ausgaben außer der Gesundheits-Sicht.
Abnahme: Äquivalenztest: für Geburtsdatum, Kurswahl und Abwesenheitsgrund liefern alle Ausgabewege je Rolle dasselbe Ergebnis (Einzelabruf = Listenabruf = Export = API-Zugang = Auskunft).

**SIC-028** · P0 · Status: offen · **Exporte nur mit Schülerdaten-Recht, mit Protokoll**
- Stammdaten-Exporte (JSON, CSV, Untis, Schulmanager-Online-Paket, OneRoster, ZIP) verlangen `students.read` im Umfang der Sicht; Geburtsdatum nur mit eigenem Recht; `zuschauer` ausgeschlossen. Jeder Export ist im Audit (Konto, Format, Umfang/Anzahl, Filter; keine Inhalte). Auskunfts-Exporte siehe DAT-053.
Abnahme: `zuschauer` und ein Konto ohne `students.read` → 403 auf jeder Exportroute; je erfolgreichem Export genau ein Audit-Eintrag mit Format und Anzahl; Export mit Geburtsdatum ohne Recht enthält die Spalte nicht.

**SIC-029** · P0 · Status: offen · **Live-Verbindungen (Ereignisstrom)**
- Der Strom `GET /api/v1/events` prüft Rechte bei Änderung neu oder schließt die Verbindung bei Abmeldung, Sperre, Herabstufung, Austritt. Zielgerichtete Ereignisse gehen nur an die betroffenen Konten (`user_ids`) und enthalten **keine Inhalte** (Nachrichten, Gesundheitsangaben, Material werden nicht übertragen). Kein Strom bei Zwangszuständen (`password_change_required`, `totp_setup_required`, `link_required`). Der Strom wird nie vom allgemeinen Rate-Limit gebremst; Keep-alive `SM_SSE_PING_SECONDS` = 20 Sekunden.
Abnahme: Konto abmelden/sperren/herabstufen → der offene Strom endet spätestens beim nächsten Ping (20 s); ein Ereignis „neue Krankmeldung“ enthält keinen Grund/Namen; Strom mit Zwangszustand → 403.

**SIC-030** · P0 · Status: offen · **Zuordnungen nur passend zur Rolle**
- `teacher_id` und `student_id` eines Kontos nur passend zur Rolle (Fund U-26). Eltern-Kind-Verknüpfungen nur durch Berechtigte; keine Selbstzuordnung über Sequenz-IDs oder Raten von Kennungen; Verknüpfung mit Nachweis. Schulbegleitung: Verknüpfung über dieselbe Tabelle wie Eltern (alle Kinder in `student_ids`).
Abnahme: Konto mit Rolle `schueler` und gesetzter `teacher_id` → 422; Elternkonto versucht, ein beliebiges Kind per ID zu verknüpfen → 404/403 und kein Zugriff.

**SIC-031** · P0 · Status: Ist · **Verwaiste Konten, Austritt**
- Wird die Person aus den Stammdaten entfernt, endet die Anmeldung des Kontos sofort, laufende Sitzungen enden, das Konto wird gesperrt (Warteliste, DAT-049). Die Benutzerverwaltung zeigt „ohne Datensatz“ mit „deaktivieren/löschen“. Eltern sehen kein Kind ohne Klasse.
Abnahme: Schüler wird aus dem Planungsdokument entfernt → laufende Sitzung des Schüler- und der Elternkonten (sofern kein weiteres Kind) liefert bei der nächsten Anfrage 401; Anmeldung → 403 `account_disabled`.

**SIC-032** · P0 · Status: offen (Ist: Standards gesetzt; offen: Designentscheidung Adressbuch) · **Empfängerkreis datensparsam**
- Schüler/innen schreiben standardmäßig an Lehrkräfte ihrer Kurse, Klassenleitung und Sekretariat; an Mitschüler/innen nur, wenn die Schule es erlaubt (`messaging_students_to_students`, Standard aus) und nur innerhalb von Klasse und Kursen. Eltern schreiben an Personal (Lehrkräfte ihrer Kinder, Klassenleitung, Sekretariat, Schulleitung). Andere Familien und Schüler/innen sind nicht auffindbar; keine schulweite Personensuche für Schüler/Eltern. [unklar: Designentscheidung „schulweites Adressbuch für Eltern/Schüler“ (Fund P1-10) – Betreiber entscheidet; bis dahin gilt die Minimierung.]
Abnahme: `GET /messages/recipients` liefert für ein Schülerkonto bei Suche nach dem Vornamen eines Mitschülers nichts (Standard) und nie Klassen fremder Kinder; ein Elternkonto findet keine anderen Eltern; Senden an nicht erlaubte Empfänger → verständliche Ablehnung.

**SIC-033** · P0 · Status: Ist · **Demo-Betrieb: Freigabeliste und keine öffentlichen Standardzugänge**
- Im Demo-Betrieb ist jede schreibende Anfrage gesperrt, die nicht auf der Freigabeliste steht (Altsystem: 330 Schreib-Routen getestet); neue Routen sind automatisch gesperrt. Gesperrt bleiben: Anbieter-Anmeldung einrichten, Rechte, Anmelderegeln, alle Importe, Verlauf/Rückgängig, API-Zugänge, Mail-Konten, Lizenz, Sicherheits-/Benachrichtigungs-Einstellungen der Schule, Postausgang, Ferien-Import, Briefversand per E-Mail, Kontakt-/Anbieter-Verknüpfungen, Systemverwaltung, Webhooks und Aufbewahrungsfristen.
- Demo-Konten: eigenes Passwort und 2FA nicht änderbar, andere Konten dürfen sie nicht ändern; **nie öffentlich erreichbare Standardkonten mit bekanntem Passwort**; Demo-Zugänge gibt nur der Inhaber aus; „Demo laden“ und „Demo-Zugang ausgeben“ werden im Produktivbetrieb **serverseitig** verweigert (App, CLI, Start). Das Demo-Passwort steht nie im Log; beim ersten Demo-Start entsteht ein Einmalpasswort. [unklar: Anmeldeform der Demo (Rollen-Knöpfe ohne Passwort vs. Zugangsdaten je Rolle) – widersprüchlich, Betreiber entscheidet; der Betreiber nannte die Rollen-Knöpfe auf der Anmeldeseite „Totaler Quatsch“.]
Abnahme: Test über alle Routen im Demo-Modus: jede schreibende Route außerhalb der Freigabeliste → 403; im Produktivmodus: `POST /admin/demo` und CLI „Demo laden“ → verweigert, ohne Datenänderung; Demo-Konto ändert eigenes Passwort → 403.

---

## 3 Authentifizierung

**SIC-034** · P0 · Status: Ist · **Passwortregeln (alle Wege: Anlage, Setzen durch Verwaltung, Ändern, Zurücksetzen, CLI mit Passwort)**
- Mindestlänge `schueler` 8 Zeichen, alle übrigen Rollen (Personal, Eltern, Monitor, eigene Rollen nach Grundtyp) 10 Zeichen. Höchstlänge 256 Zeichen (Neubau: Eingabefeld und Regel gleich 256; im Altsystem akzeptierte das Feld 1024 – Fund U-72).
- Mindestens 4 verschiedene Zeichen. Der Benutzername (ab 3 Zeichen, Vergleich ohne Groß-/Kleinschreibung) darf nicht enthalten sein. Neues Passwort ≠ bisheriges (nur Passwortwechsel des eigenen Kontos).
- Keine Zeichenklassen-Pflicht, kein Passwortverlauf, kein Zwangswechsel nach Zeit.
- Die Regeln liefert der Server (öffentlich abrufbar: Standard 10, Schüler/innen 8); das Frontend hält keine eigene Kopie. Benutzernamen: a–z, 0–9, Punkt, Unterstrich, Bindestrich (Umlaute umgeschrieben), klein, höchstens 80 Zeichen.
Abnahme: Passwort mit 7 Zeichen (`schueler`) bzw. 9 Zeichen (übrige Rollen) → 422 mit Regelmeldung; „aaaaaaaaaa“ → 422; Passwort enthält den Benutzernamen → 422; neues = altes → 422; 257 Zeichen → 422; 256 gültige Zeichen → angenommen; derselbe Test über alle fünf Wege.

**SIC-035** · P0 · Status: offen (Ist: rund 120 Einträge) · **Sperrliste häufiger Passwörter**
- Die Liste häufiger/geleakter Passwörter umfasst mindestens **3000 Einträge** (ASVS); Vergleich nach Kleinschreibung; Ablehnung mit „zu leicht zu erraten“.
Abnahme: Die Liste hat ≥ 3000 verschiedene Einträge; 50 Stichproben aus der Liste werden bei Anlage und Wechsel abgelehnt.

**SIC-036** · P1 · Status: offen (Ist: gebaut, Standard aus; Betreiber hat das Einschalten nicht entschieden) · **Optionale Prüfung auf bekannte Datenlecks**
- Schalter `SM_HIBP_CHECK` oder Schul-Einstellung `hibp_check`, Standard **aus**. Geprüft werden nur selbst gewählte Passwörter (eigener Wechsel, Zurücksetzen per Code/Link), nicht Vergabe durch die Verwaltung oder Kontoanlage.
- Übertragen werden nur die ersten 5 Zeichen des SHA-1-Werts (k-Anonymität) mit Padding-Anforderung; Zeitlimit 3 Sekunden; Antwort höchstens 2 000 000 Byte. Dienst nicht erreichbar → Passwort wird akzeptiert (fail-open) und eine Warnung ins Protokoll geschrieben. Treffer → Ablehnung „aus bekannten Datenlecks“.
- Ist die Prüfung aktiv, nennen Datenschutzerklärung und Verzeichnis den Dienstleister (Drittland USA) und die übertragenen Daten (IP-Adresse des Servers, 5-stelliges Hash-Präfix). Zielverbindung über die Zielprüfung (SIC-097). Alternative ohne Drittland: Offline-Liste ausbauen (SIC-035).
Abnahme: Schalter aus → keine Netzverbindung beim Passwortwechsel; Schalter an, Dienst per Test-Attrappe: bekanntes Passwort → abgelehnt, nur 5 Hash-Zeichen im Request; Dienst nicht erreichbar → Passwort angenommen und Log-Warnung vorhanden.

**SIC-037** · P0 · Status: Ist · **Passwort-Hash**
- Verfahren scrypt; Format `scrypt$N$r$p$Salt$Hash` (Base64 ohne Auffüllung); N = 32768 (2^15) für selbst gewählte Passwörter (`SM_SCRYPT_N`, Zweierpotenz, Produktion mindestens 16384), r = 8, p = 1, Ausgabe 32 Byte, Salt 16 Byte zufällig je Hash, Speicherlimit mindestens 64 MiB. Vergleich in konstanter Zeit. Ungültiger Hash gilt als falsch.
- Neuhash bei erfolgreicher Anmeldung, wenn gespeichertes N kleiner als konfiguriert (nicht bei Pflicht-Passwortwechsel). Unbekannter Benutzername: Scheinprüfung gleicher Dauer.
- Startpasswörter (zufällig, ca. 59 Bit) nutzen N = 2048 (2^11) [Abwägung des Altsystems; Neubau darf höheres N wählen, nie niedrigeres].
Abnahme: Ein gespeicherter Hash hat die genannten Parameter; Start mit `SM_SCRYPT_N=8192` im Produktivmodus bricht ab; ein Hash mit N = 16384 wird bei der nächsten Anmeldung auf 32768 erneuert; Laufzeit unbekannter vs. bekannter Benutzer: SIC-007.

**SIC-038** · P0 · Status: Ist · **Startpasswörter**
- Standard: 3 Gruppen zu je 4 Zeichen mit Bindestrich (z. B. Schema xxxx-xxxx-xxxx, ca. 59 Bit); Erst-Admin und CLI `create-admin` ohne Passwort: 4 Gruppen (ca. 79 Bit). Zeichenvorrat 31 Zeichen: Kleinbuchstaben ohne i, l, o; Ziffern 2 bis 9. Zufallsquelle kryptografisch sicher.
- Anzeige **einmalig** in der Antwort (Feld `temp_password`), nie zwischengespeichert; in Briefen im Brief. Klartext wird nie gespeichert: nur Hash und Ablaufdatum (`account_initial_passwords`).
- Frist: 14 Tage (Schuleinstellung `initial_password_days`, 1 bis 90). Nach Ablauf lehnt die Anmeldung das richtige Startpasswort mit 403 `initial_password_expired` ab (zählt als Fehlversuch); neues Startpasswort erzeugen. Die Marke fällt beim Passwortwechsel und beim Zurücksetzen über „Passwort vergessen“. Der Modus „altes Startpasswort wieder gültig“ entfällt.
- Neues Startpasswort: Pflicht-Passwortwechsel, alle Sitzungen des Kontos enden, offene Reset-Codes werden entwertet. Pflichtwechsel gilt bei Anlage, Massenanlage, Verwaltungs-Reset; Ausnahme: Anmeldeweg „Passwort“ nicht erlaubt (kein Zwang). Bis zum Wechsel antworten alle Endpunkte außer den Anmelde-Pfaden mit 403 `password_change_required`.
- Der Brieftext nennt die Frist (Lücke im Altsystem, Hinweis 14).
Abnahme: Ein Datenbank-Dump enthält kein Startpasswort im Klartext oder entschlüsselbar; Frist + 1 Tag: richtiges Startpasswort → 403 `initial_password_expired`; nach Passwortwechsel existiert keine Marke mehr; neues Startpasswort beendet alle Sitzungen (nächste Anfrage 401).

**SIC-039** · P0 · Status: offen (Ist: Verschlüsselung/Lebensdauer/Sichtbarkeit; Lücken: Inhaber-Schutz und eigenes Konto im Stapel) · **Zugangsbrief-Stapel**
- Stapel enthalten Startzugangsdaten, **verschlüsselt** gespeichert (DAT-016), Lebensdauer `SM_LETTER_BATCH_MINUTES` = 60 (1 bis 1440), danach gelöscht (Zugriff 410 mit Hinweis). Sichtbar nur dem Ersteller oder der Administration; anderen: 404. Ein Eintrag ist nur sichtbar, wenn der Betrachter das Konto zurücksetzen darf (Klassenleitung: Schüler/innen der eigenen Klasse; Elternkonten nur Sekretariat, Schulleitung, Administration).
- Grenzen: 5000 Einträge je Stapel (Speicherung), 500 Konten je Anlage über die Route, 2000 Briefe je direkter PDF-Erzeugung, 5000 Konten je Auswahl. Rechte: Anlage `users.manage`; Lesen/Versand `users.manage` oder `passwords.reset`. Antworten `no-store`.
- Jeder Download und Versand im Audit (`letters.download`, `letters.send`), ohne Passwort. Mail-Versand: pro Person und Adresse eine Mail, Brief als PDF-Anhang, Mailtext **ohne** Passwort; volljährige Schüler/innen nie über Eltern.
- Der Stapel darf das eigene Konto nicht enthalten und das Inhaber-Konto nur für den Inhaber (SIC-021).
Abnahme: Stapel nach 61 Minuten → 410; Zugriff durch fremdes Konto → 404; Klassenleitung sieht nur eigene Klasse; Stapel mit dem eigenen Konto → abgelehnt; Stapel mit dem Inhaber-Konto durch Zweitadministrator → 403 `user.owner_protected`; DB-Dump: `data_enc` nicht lesbar; Audit-Einträge ohne Passwortzeichen.

**SIC-040** · P0 · Status: Ist · **Konten-Sperrung und Schutzregeln**
- Deaktiviertes Konto: alle Sitzungen enden, API-Token wirkungslos (401 `invalid_token`), Anmeldung nach richtigem Passwort 403 `account_disabled` (zählt als Fehlversuch). Eigenes Konto deaktivieren/löschen, eigene Rolle ändern: 409. Letzter aktiver Administrator: 409 (SIC-019).
- Löschen: endgültig; Sitzungen, API-Token, Anmeldeversuche, Eltern-Verknüpfungen gelöscht; Protokolle pseudonymisiert (DAT-052).
- Demo-Konten: eigenes Passwort und 2FA nicht änderbar; andere Konten dürfen sie nicht ändern (403). Ansichtskonten: nur lesend (SIC-020).
- Lizenz gesperrt: nur Anmelde-Pfade und Lizenz-Eingabe erreichbar (403 `license_locked`); Kulanzzeit: Lesen erlaubt, Ändern 403.
Abnahme: Je Zeile ein Test; Konto deaktivieren → vorhandenes API-Token des Kontos liefert sofort 401; Löschen → keine Zeile in `sessions`, `api_tokens`, `login_attempts` für das Konto.

**SIC-041** · P0 · Status: Ist · **Zwei-Faktor (TOTP)**
- RFC 6238, HMAC-SHA1, Periode 30 Sekunden, 6 Ziffern, Prüffenster ±1 Schritt (bis 90 Sekunden Abweichung). Geheimnis 20 Zufallsbytes, Base32 (32 Zeichen), verschlüsselt gespeichert und an die Konto-ID gebunden (`users.totp_secret:<Konto-ID>`).
- Ein Code gilt **nur einmal** in seinem Gültigkeitsfenster (Replay-Schutz); bei mehreren Knoten knotenübergreifend (SIC-120).
- Einrichtung: Geheimnis erzeugen (inaktiv) → Code bestätigen → aktiv; begonnene Einrichtung behält das Geheimnis (neues nur mit `neu=true`). Einrichten, Aktivieren, Abschalten nur mit **Sitzung**, nie mit API-Token. Abschalten: Sitzung + Passwort (Sperre gilt; falsches Passwort zählt), Audit `auth.2fa_disable`. Die Administration kann 2FA nicht einschalten (422), nur abschalten (Konto bearbeiten, Reset mit `disable_2fa`, CLI `disable-2fa`); ein 2FA-Reset beendet Sitzungen und API-Token des Kontos. Passwort-Reset lässt 2FA bestehen. Das Inhaber-Konto: SIC-021.
Abnahme: Code 31 s nach Ausstellung (innerhalb ±1) angenommen, 91 s → abgelehnt; derselbe Code ein zweites Mal → abgelehnt und als Fehlversuch gezählt; DB-Dump: Geheimnisspalte beginnt mit `SM1`; 2FA-Einrichtung mit API-Token → 403; Administration schaltet 2FA eines Kontos ein → 422.

**SIC-042** · P0 · Status: offen (Ist: Modus empfohlen für Administration; Pflicht für Administration ist neu) · **Zwei-Faktor-Pflicht**
- Schul-Einstellung `twofa_mode`: `off`, `recommended` (Standard; Hinweis auf der Startseite), `required`; betroffene Rollen `twofa_roles` (wählbar: `admin`, `schulleitung`, `planer`, `sekretariat`, `abteilungsleitung`, `lehrer`; Standard `admin`, `schulleitung`, `sekretariat`). `SM_REQUIRE_2FA_ROLES` erzwingt die Pflicht immer, unabhängig von der Schuleinstellung.
- **Neu:** Für `admin` ist 2FA **immer Pflicht** und nicht abschaltbar (Prüfung 17.10., Fund P3-04; Haftungsmuster fehlende MFA bei Schulsystemen).
- Pflicht ohne Einrichtung: Sitzung nur zur Einrichtung (`/zwei-faktor`), alle Endpunkte außer Anmelde-Pfaden 403 `totp_setup_required` (nur Sitzung, nicht API-Token). Ein Passkey (WebAuthn, Datei ANM) erfüllt die Pflicht.
- **Alle Anmeldewege** (Passwort, Microsoft, Google, Apple) unterliegen derselben 2FA-Regel; eine Anbieter-Anmeldung umgeht die lokale 2FA nicht (Fund P3, offen). Bekannter Zustand: Der Status „2FA für Administration/Schulleitung nicht erzwungen“ erscheint auf der Statusseite als Warnung (DAT-057).
Abnahme: Neu angelegtes `admin`-Konto ohne 2FA: nach der Anmeldung nur `/zwei-faktor` erreichbar, sonst 403 `totp_setup_required`; Versuch, die Pflicht für `admin` abzuschalten → abgelehnt; Anmeldung eines Pflicht-Kontos über den Anbieter-Weg verlangt dieselbe Einrichtung.

**SIC-043** · P0 · Status: offen · **Wiederherstellungscodes für 2FA**
- Bei Verlust des Geräts gibt es einen Notweg ohne Verwaltungseingriff: Wiederherstellungscodes, einmalig verwendbar, nur als Hash gespeichert, einmal angezeigt, Neuerzeugung entwertet alte, Verbrauch im Audit; falscher Code zählt wie ein falscher TOTP-Code als Fehlversuch (SIC-093). Pflicht für `admin`. [unklar: Anzahl und Form der Codes – im Altsystem nicht vorhanden; Notweg war nur Reset durch Administration/Konsole.]
Abnahme: Admin-Konto meldet sich mit Passwort + Wiederherstellungscode an; derselbe Code ein zweites Mal → abgelehnt; die Codes liegen in der Datenbank nur als Hash.

**SIC-044** · P0 · Status: Ist · **Zweistufige Anmeldung**
- Reihenfolge der Prüfungen: (1) Drosselung (429, `Retry-After`; zählt nicht als Fehlversuch), (2) Benutzername klein, höchstens 80 Zeichen, Konto suchen, (3) Passwort (Fehler 401 `invalid_credentials`, gleiche Antwort für unbekanntes Konto, zählt), (4) Konto aktiv (403 `account_disabled`, zählt), (5) 2FA aktiv und Code fehlt: **200 `totp_required: true` ohne Sitzung, zählt nicht** (5a) Code falsch/bereits benutzt: 401, zählt, (6) Startpasswort-Frist (403, zählt), (7) Anmeldeweg Passwort erlaubt (403 `method_not_allowed` + Kopf `X-Login-Methods`, zählt), (8) Erfolg: Erfolgseintrag, neue Sitzung, Cookie, Antwort mit Benutzer und CSRF-Token; Ersteinrichtung (Startpasswort oder fehlende Pflicht-Verknüpfung): Sitzung nur zum Verbinden (`password_setup`); `add=true`: bisheriges Konto bleibt als weiteres Konto angemeldet.
- Schritt 2 ist zustandslos (Passwort wird erneut geprüft, kein Zwischen-Token). Bewusster Preis: Wer das Passwort schon kennt, erfährt, dass 2FA aktiv ist; das Passwort allein reicht nicht.
- Anmeldung nur per JSON-Body (kein HTML-Formular, damit kein Login-CSRF); bei jedem Login eine **neue** Sitzung (keine Fixierung). Fehlermeldung: „Benutzername oder Passwort ist falsch.“; ein falscher Code erhält eine eigene Meldung. Ein gedrosseltes Konto mit richtigem Passwort erhält trotzdem 429 bis zum Ablauf.
Abnahme: Kontrakt-Test über jede Zeile; 2FA-Konto mit richtigem Passwort ohne Code → 200 `totp_required` und kein `Set-Cookie`; Anmeldung mit vor-bekannter Sitzungskennung ergibt eine neue Kennung; Form-POST → 415/422.

**SIC-045** · P0 · Status: Ist · **Fehlercodes der Zugangsschicht**
- Feste Codes: 401 `not_authenticated`, 401 `invalid_token`, 401 `invalid_credentials`, 403 `csrf_failed`, 403 `password_change_required`, 403 `totp_setup_required`, 403 `link_required`, 403 `account_disabled`, 403 `initial_password_expired`, 403 `method_not_allowed`, 403 `license_locked`, 403 Ansichtskonto, 409 Selbst-Aussperrung, 429 `too_many_attempts` und `rate_limited` (jeweils mit `Retry-After`). Fehlerantwort immer `{"detail": "..."}`.
Abnahme: Kontrakt-Test pro Code mit auslösender Bedingung und erwartetem Status/Text.

**SIC-046** · P0 · Status: offen (Ist: Datei mit Rechten 600; Lücken: Regelverstoß von `SM_ADMIN_PASSWORD` nur Warnung, Entwicklungs-Passwort bei fehlendem Modus) · **Erst-Admin**
- Nur wenn noch kein Konto existiert. Ohne `SM_ADMIN_PASSWORD` (Produktion/Demo): Startpasswort 4 × 4 Zeichen mit Pflichtwechsel in der Datei `ERST-ADMIN.txt` im Datenverzeichnis, Rechte 600, **nie** im Log; nach dem ersten Passwortwechsel des Administrators gelöscht (auch beim Start, wenn kein Administrator mehr Pflichtwechsel hat). Datei nicht schreibbar: Fehlermeldung ohne Passwort, Zurücksetzen über CLI.
- Mit `SM_ADMIN_PASSWORD`: dieses Passwort, kein Pflichtwechsel, **muss** die Passwortregeln erfüllen – Regelverstoß bricht den Start ab (Neubau; im Altsystem nur Warnung) und ein bekanntes Entwicklungs-Passwort ist in Produktion verboten.
- Entwicklungs-Passwörter nur im Entwicklungsmodus; selbst dort nie im Log. CLI: `create-admin` ohne Passwort → 4 × 4 Zeichen mit Pflichtwechsel; `reset-password` ohne Passwort → 3 × 4 Zeichen mit Pflichtwechsel, Sitzungen beendet; mit angegebenem Passwort Regelprüfung, kein Pflichtwechsel (CLI-Reset).
Abnahme: Produktiver Erststart ohne `SM_ADMIN_PASSWORD`: Log enthält keine Passwortzeichenfolge, Datei hat Rechte 600, nach dem ersten Wechsel existiert die Datei nicht mehr; Start mit `SM_ADMIN_PASSWORD=abc` im Produktivmodus bricht ab.

**SIC-047** · P0 · Status: Ist (atomarer Verbrauch: offen) · **Konto-Codes (E-Mail/Handy bestätigen, Passwort vergessen)**
- Code: 6 Ziffern, zufällig, nullgefüllt; gespeichert als HMAC über Zweck, Konto und Code; Gültigkeit `SM_AUTH_CODE_MINUTES` = 15 (1 bis 1440); 5 Fehlversuche je Code, danach verbraucht; ein neuer Code entwertet offene ältere gleichen Zwecks; ein Fehlversuch bei mehreren offenen Reset-Codes zählt auf alle offenen Reset-Codes des Kontos.
- Link (E-Mail): 32 Zufallsbytes, gleiche Gültigkeit, einmal. Reset-Token nach Prüfung: 32 Zufallsbytes, Gültigkeit 15 Minuten, einmal, Mindestlänge in der Anfrage 10 Zeichen. Ziel (Adresse/Nummer) verschlüsselt gespeichert. Bereinigung: Codes 1 Stunde nach Ablauf.
- **Atomarer Einmalverbrauch**: bei parallelen Anfragen gewinnt genau eine (Fund U-73, Altsystem verbrauchte nicht atomar).
Abnahme: 5 falsche Eingaben → Code verbraucht, 6. mit dem richtigen Code → abgelehnt; 20 parallele Einlösungen desselben Reset-Tokens → genau 1 Erfolg; Code 16 Minuten alt → abgelehnt; DB-Dump enthält keine Klartext-Codes.

**SIC-048** · P0 · Status: Ist · **Passwort vergessen: Zustellung und Wirkung**
- Optionen erscheinen nur, wenn der Versand wirklich eingerichtet ist (E-Mail: SMTP und Zustellung aktiv; SMS: Anbieter eingerichtet); sonst Hinweis „Bitte wenden Sie sich an das Sekretariat“. Zustellung nur an **bestätigte** Kontakte, nur über Kanäle der Anmelde-Richtlinie, nur bei aktivem Konto und erlaubter Passwort-Anmeldung; sonst gleiche Antwort ohne Versand. Kanal „auto“: E-Mail-Kennung → E-Mail, Handynummer → SMS, Benutzername → E-Mail, sonst SMS. Schüler/innen: Standard aus (Schulvorgabe „Passwort vergessen per“, je Rolle/Jahrgang/Klasse/Person; leer = nicht erlaubt).
- Reset-Codes gehen nie an eine öffentliche Seite (Test-Postausgang nur lokal, SIC-104).
- Erfolg: Passwort gesetzt, Pflichtwechsel aus, Startpasswort-Marke entfernt, **alle** Sitzungen beendet, offene Codes verbraucht, Erfolgseintrag hebt Paar-/Kontozähler auf (SIC-093), 2FA bleibt; Audit `auth.password_reset`. Neues Passwort nach den Passwortregeln (inkl. Leak-Prüfung, falls aktiv: 422 mit Meldungen).
- Verwaltungs-Versand von Link/Code: nur bei bestätigtem Kontakt, aktivem Konto, erlaubter Passwort-Anmeldung, eingerichtetem Versand (sonst 409 mit Grund).
Abnahme: Ohne SMTP zeigt die Seite keine E-Mail-Option; Anfrage für ein unbekanntes und ein bekanntes Konto liefert identische Antwort; nach Erfolg liefert eine vorher gültige Sitzung 401; Schülerkonto mit Standardrichtlinie erhält keinen Code (neutrale Antwort).

**SIC-049** · P0 · Status: Ist · **Eigene Kontakte bestätigen**
- E-Mail ändern: Code an die **neue** Adresse plus Link (Anmeldung nötig), 6 Ziffern, 15 Minuten; wirksam erst nach Bestätigung; die alte bestätigte Adresse bekommt einen Hinweis. E-Mail höchstens 254 Zeichen, eine Adresse, keine Kopfzeilen-Trennzeichen (Schutz vor Kopfzeilen-Einschleusung); sonst 422. Handynummer: Code per SMS. Änderung/Entfernen verlangt das aktuelle Passwort (Sperre gilt, falsches Passwort zählt); offene Codes werden entwertet. Verwaltung setzt Kontakte ohne Code (Recht `users.manage`; `sekretariat` nur Schüler/Eltern).
Abnahme: E-Mail-Adresse mit Zeilenumbruch → 422; Änderung ohne Passwort → 403; alte bestätigte Adresse erhält Hinweis (Postausgang); `sekretariat` ändert Lehrerkontakt → 404.

**SIC-050** · P0 · Status: Ist · **Anbieter-Anmeldung (OIDC): Ablauf und Prüfung**
- Authorization Code mit PKCE (außer Apple, siehe unten), `state` und `nonce` (24 Zufallsbytes). Status in verschlüsseltem Cookie `sm_sso_<Anbieter>` (600 Sekunden, einmal verwendbar, Pfad `/api/v1/auth`, HttpOnly, SameSite=Lax; Apple-Rückgabe per Formular: SameSite=None und Secure bei HTTPS).
- ID-Token: Signatur über die öffentlichen Schlüssel des Anbieters (RS256, `kid`; bei unbekannter `kid` Neuladen höchstens alle 30 Sekunden), `iss`, `aud`, `exp`, `nonce`, `sub`. Discovery und Schlüsselliste je 3600 Sekunden zwischengespeichert; Endpunkte nur https (Ausnahme: lokale Entwicklung).
- Rückleitungsziel `next` nur interner Pfad (SIC-070). Apple: kein PKCE (vom Anbieter nicht dokumentiert); Schutz über state, nonce und das Client-Geheimnis als ES256-JWT (10 Minuten gültig, höchstens 180 Tage). Anbieter-Geheimnisse und Apple-Schlüssel verschlüsselt (DAT-016); Konfigurationsänderungen im Audit nur mit Feldnamen (`sso_provider.update`).
Abnahme: Test-Attrappe des Anbieters: Token mit falscher Signatur/`aud`/`exp`/`nonce` → abgelehnt; zweiter Aufruf mit demselben `state` → abgelehnt; Callback mit `next=https://fremd.example` → Umleitung auf `/`; Cookie-Attribute wie angegeben.

**SIC-051** · P0 · Status: offen (Ist: Reihenfolge und E-Mail-Prüfung; Lücke: E-Mail-Zuordnung ohne bestätigte Adresse prüfen) · **Anbieter-Anmeldung: Kontozuordnung**
- Zuordnung in dieser Reihenfolge: (1) vorhandene Verknüpfung (Anbieter, Kennung); (2) Vormerkung mit gleicher **bestätigter** E-Mail (eindeutig); (3) nur wenn die Richtlinie `sso_create` erlaubt: eindeutiges Konto mit gleicher E-Mail; (4) nur Schulkonto: Zuordnung per Benutzername/bestätigter E-Mail und `SM_OIDC_AUTO_CREATE` (Standard 0). Danach Prüfung des Anmeldewegs (sonst 403 `method_not_allowed`, Audit `auth.login_denied`), dann Aktiv-Prüfung. Keine Kontoanlage durch Anbieter-Dienste, außer die Richtlinie erlaubt es.
- Microsoft: E-Mail gilt nur als bestätigt aus dem Benutzernamen (UPN) mit Kennzeichen `xms_edov` oder bei festem Mandanten; frei setzbares Mail-Attribut fremder Mandanten zählt nicht; Gastkonten (`#EXT#`) werden ignoriert. Google: Domain `hd` als Parameter und Prüfung. `allowed_domains` (alle Anbieter): nur bestätigte Adressen dieser Domains (`email_unverified`, `domain_not_allowed`). Kennungen: `sub`; Schulkonto `<Aussteller>|<sub>`. Eindeutig je (Anbieter, Kennung) und je (Konto, Anbieter).
- Verbinden/Trennen im Profil: Zustand an Sitzung gebunden; Trennen nur bei erlaubter Selbstverknüpfung, nicht bei Pflicht-Verknüpfung und nur wenn ein anderer erlaubter Anmeldeweg bleibt (409 `required`/`last_method`). Neue Zuordnungen im Audit mit Herkunft (`identity.link`: `reserved`, `email`, `legacy`, `created`, `profile`).
Abnahme: Anbieter meldet unbestätigte E-Mail eines bestehenden Kontos → keine Zuordnung (`email_unverified`); Gastkonto `#EXT#` → abgelehnt; Trennen des letzten Anmeldewegs → 409; Zuordnung ohne Richtlinie `sso_create` legt kein Konto an.

**SIC-052** · P0 · Status: Ist · **Anbieter-Anmeldung: Skripte, automatische Anmeldung, Test-Anbieter**
- Skripte der Anbieter (Google, Apple) werden erst geladen, wenn der Anbieter in den Schuleinstellungen aktiv ist; nach dem Betreiber-Auftrag „erst beim Klick“ (Fund P4-02). Sonst fließen keine Daten an Dritte. Nur offizielle Anbieter-Knöpfe; keine Test-Knöpfe in Produktion; „Schulkonto“-Knopf entfällt.
- Automatische/stille Anmeldung (One Tap, Microsoft stiller Versuch) ist standardmäßig **aus** (Schul-PCs); Antworten des stillen Versuchs: `login_required`, `interaction_required`, `consent_required`, `account_selection_required`. Microsoft und Google nutzen `prompt=select_account`. Nach dem Abmelden keine automatische Rück-Anmeldung. Cookies `sm_sso_hint` (nur Anbieter-Kennung) und `sm_sso_who` (verschlüsselte E-Mail, HttpOnly) werden beim Abmelden gelöscht.
- Test-Anbieter (`SM_SSO_DEV_MOCK`): nur wenn `SM_ENV=development`; in Produktion, Demo und öffentlicher Demo Startabbruch. Testcode 120 Sekunden, signiert, einmalig, PKCE-geprüft; Banner „Test-Anbieter – nur Entwicklung“.
Abnahme: Netzwerkmitschnitt der Anmeldeseite mit ungeaktiviertem Anbieter: 0 Fremd-Requests; Start mit `SM_SSO_DEV_MOCK=1` und `SM_ENV=production` bricht ab; nach Abmelden liefert der stille Versuch keine Sitzung.

**SIC-053** · P0 · Status: Ist · **Limits für Konto-Codes und Passwort-Zurücksetzen**

| Limit | Wert | Wirkt auf | Bei Überschreitung |
|---|---|---|---|
| Bestätigungscodes je Konto und Art (E-Mail/Handy) | 5 je Stunde | Konto | 429, `Retry-After` 3600 s |
| Bestätigungscodes je IP | 20 je Stunde | IP | 429 |
| Reset-Anfragen je Kennung (Benutzername, E-Mail, Handynummer; auch unbekannte) | 5 je Stunde | Kennung | 429 |
| Reset-Anfragen je IP | 20 je Stunde | IP | 429 |
| Reset-Codes je Konto (alle Kennungen) | 5 je Stunde | Konto | still verworfen, gleiche Antwort |
| Reset-Fehlversuche je IP | 30 je Stunde | IP | 429 |
| Admin: Link oder Code senden | 10 je Stunde | Zielkonto | 429 (zählt mit auf das Konto-Limit) |
| Konten je Kennung | höchstens 5 | gleiche Adresse (z. B. Eltern) | weitere nicht berücksichtigt |
| Mindestlaufzeit Reset-Anfrage | 0,35 s plus Zufall 0–39 ms | bekannt/unbekannt | gleiche Laufzeit |

- Antwort auf eine Reset-Anfrage immer: „Falls ein Konto dazu passt, ist ein Code unterwegs.“ Falscher Code: 400 „Der Code ist falsch oder abgelaufen.“ (Fehlversuch zählt auf die IP); ungültiger Link: 400 „Der Link ist ungültig oder abgelaufen.“; abgelaufenes Reset-Token: 400 „Die Zeit zum Zurücksetzen ist abgelaufen.“ Rate-Limit-Zeilen werden 1 Stunde nach ihrem Ablauf gelöscht.
Abnahme: Je Tabellenzeile ein Test mit Überschreitung (Schwelle + 1 → erwartete Reaktion); Reset-Anfrage für bekanntes und unbekanntes Konto dauert jeweils ≥ 0,35 s und liefert denselben Text.

**SIC-054** · P0 · Status: Ist · **Anmelde-Richtlinie: Schutzregeln**
- Rangfolge je Feld: Person, Klasse (Zielgruppe, dann alle), Jahrgang (Zielgruppe, dann alle), Rolle, Standard, Voreinstellung; Eltern mehrerer Kinder: Vereinigung (Wege, Kanäle, Pflicht-Verknüpfungen; Schalter wahr, wenn eine Regel wahr). Standard: alle Wege erlaubt.
- Administration: Passwort immer erlaubt, keine Pflicht-Verknüpfungen. Leere Wegeliste ist nicht erlaubt (422; Speicherung leerer Liste gilt als „erben“, nie aussperren). Eine Regel, die den eigenen Anmeldeweg entfernt, wird mit 409 abgelehnt. Regeln für Administrationskonten ändert nur die Administration. Änderungen wirken sofort (Zwischenspeicher 5 Sekunden, Änderung leert ihn). Audit `login_policy.set`/`.delete` mit Wert vorher/nachher; Recht `login_policy.manage` (Administration, Schulleitung).
- Fehlende Pflicht-Verknüpfung: 403 `link_required` (Ausnahme Anmelde-Pfade und Identitäten).
Abnahme: Schulleitung entfernt „Passwort“ und hat keinen verbundenen Anbieter → 409; Regel für `admin` mit „nur Microsoft“ gespeichert → Passwort bleibt für `admin` erlaubt; effektive Richtlinie (`/login-policies/effective`) nennt je Feld die Herkunft.

---

## 4 Sitzungen, Cookies, CSRF, Token

**SIC-055** · P0 · Status: Ist · **Sitzungs-Token**
- 32 Zufallsbytes (CSPRNG), URL-sicher, im Cookie; in der Datenbank nur HMAC-SHA256 mit `SM_SECRET_KEY`. Neue Sitzung bei jedem Login, Logout löscht Sitzung und Cookie serverseitig. Ablauf wird bei jeder Anfrage geprüft (abgelaufen = nicht angemeldet). Wechsel von `SM_SECRET_KEY` macht alle Sitzungen, API-Token und offenen Codes ungültig (bewusst; Vorfall-Maßnahme, SIC-135).
Abnahme: Ein Datenbank-Dump erlaubt keine Anmeldung (kein Klartext-Token); nach Logout liefert das alte Cookie 401; Schlüsselwechsel macht eine vorher gültige Sitzung ungültig.

**SIC-056** · P0 · Status: offen (Ist: Werte für Personal; Schüler/Eltern: Laufzeit zu prüfen) · **Sitzungsdauer**
- Absolut 30 Tage ab Anmeldung (`SM_SESSION_MAX_DAYS`; nicht verlängerbar; zugleich Cookie-Laufzeit).
- Leerlauf: `schueler`, `eltern`, `monitor` 10080 Minuten (7 Tage, `SM_SESSION_IDLE_MINUTES`); Personal (`admin`, `schulleitung`, `planer`, `sekretariat`, `abteilungsleitung`, `lehrer`, `schulbegleitung`, `hausmeister`, nach Grundtyp) = Minimum aus Schuleinstellung `staff_idle_minutes` (Standard 720 = 12 Stunden, Bereich 15 bis 10080) und `SM_SESSION_IDLE_MINUTES`. Gleitende Verlängerung bei Aktivität höchstens alle 60 Sekunden: neues Ablaufdatum = min(jetzt + Leerlauf, Anmeldung + 30 Tage). [unklar: ob die 7-Tage-Laufzeit für Schüler/innen und Eltern angemessen ist – Prüfung W8 „Laufzeiten prüfen“, Betreiber entscheidet; ein Leerlauf-Hinweis vor der Abmeldung ist im Altsystem nicht vorhanden.]
Abnahme: Personalkonto nach 12 Stunden + 1 Minute ohne Aktivität → 401; Aktivität nach 59 Minuten verlängert; Sitzung nach 30 Tagen + 1 Minute → 401 trotz Aktivität; `staff_idle_minutes=10` → abgelehnt (Minimum 15).

**SIC-057** · P0 · Status: Ist · **Cookies**

| Cookie | Inhalt | HttpOnly | SameSite | Secure | Pfad | Laufzeit |
|---|---|---|---|---|---|---|
| `sm_session` | Sitzungs-Token | ja | Lax | ja bei `SM_COOKIE_SECURE=1` oder HTTPS-Anfrage (Proxy: `X-Forwarded-Proto` nur bei vertrautem Proxy) | / | 30 Tage |
| `sm_sessions` | Tokens weiterer Konten, durch `~` getrennt, höchstens 4 | ja | Lax | wie `sm_session` | / | 30 Tage |
| `sm_sso_hint` | Kennung des zuletzt genutzten Anbieters | nein | Lax | `SM_COOKIE_SECURE` | / | 90 Tage |
| `sm_sso_who` | verschlüsselte E-Mail für stilles SSO | ja | Lax | `SM_COOKIE_SECURE` | / | 90 Tage |
| `sm_sso_<Anbieter>` | verschlüsselter Status (Zustand, Nonce) | ja | Lax (Apple-Formular: None) | bei Formular-Rückgabe und HTTPS ja, sonst `SM_COOKIE_SECURE` | `/api/v1/auth` | 600 s |

- `SM_COOKIE_SECURE` Standard 1 in Produktion. Keine Passwörter oder Klartext-Adressen in Cookies. Neubau: Secure-Regel der SSO-Hinweis-Cookies wie bei der Sitzung (HTTPS-abhängig, Hinweis 12 des Altsystems). Cookies gelten je Host und Port: Sitzungen sind an die Adresse gebunden, unter der man angemeldet ist; Betrieb nur unter **einer** Adresse (Weiterleitung weiterer Adressen auf die Hauptadresse).
Abnahme: Header-Test der Antwort nach Login mit allen Attributen der Tabelle; Cookie ohne `Secure` über HTTPS-Anfrage wird nie gesetzt; Anmeldung unter zweiter Adresse erzeugt keine Sitzung der ersten.

**SIC-058** · P0 · Status: offen (Ist: Passwortwechsel, Deaktivierung; Lücken: API-Token, Herabstufung) · **Widerruf von Sitzungen und Token**
- Automatisch beendet werden **alle** Sitzungen **und** persönlichen API-Token eines Kontos bei: Passwort gesetzt/geändert/zurückgesetzt (bei eigenem Wechsel außer der aktuellen Sitzung), Reset per Code/Link, Erzeugung eines Startpassworts, Deaktivierung, Löschung, Sperre, 2FA-Reset, Herabstufung der Rolle, Austritt, Eintritt der Volljährigkeit (für Elternzugriffe). „Alle anderen Sitzungen beenden“ ist eine eigene Aktion; Verwaltung beendet einzeln oder alle (nicht beim Inhaber-Konto).
- Sitzungsliste: nur aktive Sitzungen mit Anmeldezeit, letzter Aktivität, Ablauf, IP, Browser (höchstens 300 Zeichen); für das Konto selbst oder die Verwaltung mit Recht.
Abnahme: Je Auslöser: vorher erzeugte Sitzung und persönliches Token liefern danach 401 (Altsystem-Lücke: Token überlebten Passwortwechsel, Sperre, 2FA-Reset – Pflicht im Neubau).

**SIC-059** · P0 · Status: Ist · **Mehrfachanmeldung im Browser**
- Höchstens 5 Konten je Browser (1 aktives + 4 weitere, Cookie `sm_sessions`). Weiteres Konto: Anmeldung mit `add=true` (auch mit 2FA). Konto wechseln ohne Passwort nur mit gültiger weiterer Sitzung (neues Sitzungs-Cookie, Audit `auth.switch_account`). Kontoliste: aktives zuerst, ungültige Sitzungen werden entfernt, Doppelte nur einmal. Abmelden beendet nur das aktive Konto (Audit `auth.logout`); weitere Konten lassen sich auch ohne aktive Sitzung abmelden.
- Kontoliste ohne Sitzung („Abgemeldet“-Seite): Kopf `X-Requested-With: schulmanager` und passender `Origin` bei Schreibzugriffen. Nach Abmelden/Kontowechsel/401 werden alle Client-Zwischenspeicher zentral geleert; die Zurück-Taste zeigt keine Daten des alten Kontos (API-Antworten `no-store`). Daten zweier Konten vermischen sich nie: jeder Aufruf läuft mit dem aktiven Konto.
Abnahme: Mit Eltern- und Lehrerkonto parallel: nach Wechsel zeigt keine Seite Daten des anderen Kontos; Abmelden + Zurück-Taste → keine Kontodaten; ein sechstes Konto wird abgelehnt.

**SIC-060** · P0 · Status: Ist · **CSRF-Schutz**
- Pro Sitzung ein CSRF-Token (24 Zufallsbytes) im Header `X-CSRF-Token` bei POST/PUT/PATCH/DELETE mit Sitzungs-Cookie; fehlend oder falsch → 403 `csrf_failed`, durchgängig auf allen schreibenden Routen (Konto wechseln, abmelden, „alle anderen beenden“ eingeschlossen). Bearer-Token (API) braucht kein CSRF.
Abnahme: Test über **alle** schreibenden Routen: ohne Token → 403 `csrf_failed`, mit falschem Token → 403, mit richtigem → normaler Ablauf.

**SIC-061** · P0 · Status: offen (Ist: Vertrauenskonzept; Lücke: IPv6-Quelladresse hinter Container-Netz) · **Client-IP und Proxy-Vertrauen**
- Die App wertet Weiterleitungs-Köpfe nur aus, wenn `SM_TRUST_PROXY=1` **und** die direkte Gegenstelle in `SM_TRUSTED_PROXIES` steht (leer = nur Loopback); Position in `X-Forwarded-For` von rechts gemäß `SM_PROXY_COUNT` (min. 1), sonst `X-Real-IP`. Der Wert `*` nur, wenn die App garantiert nur hinter dem Proxy erreichbar ist (Startwarnung). Der Anwendungsserver läuft ohne eigenes Proxy-Header-Vertrauen (`--no-proxy-headers`); die App ist **nie direkt veröffentlicht**.
- Ohne Proxy-Vertrauen hinter Proxy sieht die Drosselung nur die Proxy-Adresse → Startwarnung. IPv6- und VPN-Anfragen müssen mit der echten Adresse ankommen (Docker/Proxy richtig konfigurieren); sonst wirken alle IPv6-Nutzer wie eine Adresse (Audit, Beobachtung, Drosselung unbrauchbar). Pflicht vor dem Schuleinsatz.
Abnahme: Anfrage mit gefälschtem `X-Forwarded-For` von nicht vertrauter Gegenstelle → Drosselung und Audit verwenden die Socket-Adresse; Anfrage über IPv6 durch den Proxy erscheint im Audit mit der echten IPv6-Adresse (gekürzt im Zugriffslog, DAT-026).

**SIC-062** · P0 · Status: offen (Ist: Eigenes-Konto-Regel, Laufzeit-Kette; Lücken: Pflichtlaufzeit, Widerruf, Rollenbeschränkung) · **Persönliche API-Token (Bearer `smt_`)**
- Format `smt_` + 32 Zufallsbytes, gespeichert als HMAC mit `SM_SECRET_KEY`, einmal im Klartext angezeigt. Erzeugung nur für das **eigene** Konto, nur per Sitzung oder eigenem Token (sonst 403). **Pflichtlaufzeit** 1 bis 3650 Tage (Altsystem: optional/unbefristet); ein per Token erzeugtes Token höchstens bis zur Restlaufzeit des ausstellenden Tokens, unter 1 Tag Restlaufzeit kein weiteres (422). Name höchstens 100 Zeichen (Standard „API-Token“).
- Ausstellung nur für berechtigte Rollen; **Schüler/innen-Konten dürfen keine Token ausstellen**. Ein Token ändert nie Passwort, 2FA, neue Zugänge, Rechte, Lizenz oder Sicherungen (nur per Sitzung). Ungültig (abgelaufen, widerrufen, Konto inaktiv) → 401 `invalid_token`. „Letzte Nutzung“ höchstens alle 60 Sekunden aktualisiert. Persönliche Token werden sofort nach Ablauf bereinigt. Widerruf: SIC-058.
Abnahme: Token ohne Laufzeit → 422; Token eines `schueler`-Kontos erzeugen → 403; Token für fremdes Konto → 403; Passwortwechsel → Token 401; Token ändert Passwort → 403.

**SIC-063** · P0 · Status: offen (Ist: HMAC, einmalige Anzeige; offen: Token nicht im Pfad, Elternzugriff nach Volljährigkeit) · **Kalender-Abo-Token (iCal)**
- Geheime URL `GET /ical/{token}.ics`; Token nur als HMAC gespeichert, Link nur beim Erzeugen angezeigt (`GET /me/ical-url` liefert nur `active`), Neuerzeugung im Profil entwertet den alten Link; im Protokoll ausgeblendet/maskiert. Der Feed enthält keine Abwesenheitsgründe. Eltern volljähriger Kinder erhalten ohne Freigabe keinen Feed (SIC-026). [unklar: Token im Pfad vs. Header/Rotation (Fund F48) – Betreiber/Prüfung offen; Mindestlänge ≥ 32 Zufallsbytes.]
Abnahme: Neuer Link → alter Link liefert 404; DB-Dump enthält keinen Token-Klartext; Feld-Scan des Feeds: kein Abwesenheitsgrund; Protokollzeile zeigt das Token maskiert.

**SIC-064** · P0 · Status: offen (Ist: Zugänge mit Umfang; Lücken: Allowlist für Schreibzugriffe, Pflichtablauf) · **API-Zugänge mit Umfang (`sma_`)**
- Nur für die öffentliche Schnittstelle `GET /open/…`. Bereiche: Stundenplan, Vertretung, Termine, Räume, Mitteilungen, Verzeichnis; Filter nach Klassen, Lehrkräften, Räumen, Schülern, Standorten; optionale IP-Liste; Ratenlimit Standard 60 Anfragen je Minute; Ablauf Standard 90 Tage; Schlüssel einmal sichtbar, nur als Hash gespeichert; jederzeit widerrufbar; abgelaufene Zugänge 30 Tage nach Ablauf bereinigt.
- **Nie** freigegeben: Gesundheitsdaten, Fördermerkmale, Fehlzeiten, private Nachrichten, Chats. Ein Zugang hat nie mehr Rechte als sein Konto; Lehrkräfte geben nie mehr frei, als sie selbst sehen. Art: „Nur lesen“ (Standard) oder „Lesen und schreiben“; Schreibzugang schulweit **aus**, die Administration schaltet ihn ein; Schreibzugang nur über eine **Allowlist** von Aktionen; auch mit Schreibzugang gesperrt: Passwort, 2FA, neue Zugänge, Rechte, Lizenz, Sicherungen, Exporte/Auskünfte.
- API-Protokoll (Reiter „Protokoll“): Zeit, Zugang, Konto, Aufruf (ohne Abfrage und Token), Status, Dauer, IP; Filter; CSV-Export (SIC-069); Aufbewahrung 90 Tage; Aufrufe unbekannter Adressen nicht protokolliert; jede Person sieht eigene Zugänge, Administration alle. Jede Änderung über die API steht zusätzlich im Audit mit Zugangskennung.
Abnahme: Zugang auf Bereich „Stundenplan“ ruft Fehlzeiten → 403/404; Zugang mit Schreibzugang ruft Passwort-/Rechte-/Sicherungs-Routen → 403; Zugang ohne Ablauf wird abgelehnt; Schlüssel einer anderen Schule (andere Instanz) → 401 (SIC-118).

---

## 5 Eingabe- und Ausgabeprüfung

**SIC-065** · P0 · Status: Ist · **Keine Injektion**
- Datenbankzugriff ausschließlich über parametrisierte Abfragen (ORM/Query-Builder); kein Roh-SQL mit Nutzereingaben (dynamische Bezeichner nur aus geprüften Listen). Kein Aufruf einer Shell oder eines Unterprozesses mit Nutzereingaben. Keine unsichere Deserialisierung (nur JSON, kein Pickle). Dateipfade nie aus Nutzereingaben (SIC-079).
Abnahme: Statische Analyse (CodeQL/Semgrep-Regeln für SQL-Injektion, Befehls-Injektion, Deserialisierung, Pfadzugriff) meldet 0 Treffer; ein Suchlauf im Code findet keinen Roh-SQL-Aufruf mit Zeichenketten-Verkettung.

**SIC-066** · P0 · Status: offen (Ist: an einzelnen Stellen `extra=forbid`) · **Strikte Eingabemodelle**
- Jedes Eingabemodell nennt alle erlaubten Felder ausdrücklich; unbekannte Felder werden abgelehnt (keine Massenzuweisung wie `role`, `adult`, `is_active`). Rollenänderung nur über die Konten-Route mit Rechteprüfung. Längengrenzen: Benutzername 80, E-Mail 254, Betreff 300, Passwort 256, Code-Eingaben fest; Listen und Mengen begrenzt (z. B. Klasse höchstens 500 Schüler/innen im Schema und in der Prüfung gleich – Fund U-71).
Abnahme: Ein Test erzwingt `extra=forbid` an allen Eingabemodellen (Registry-Test); POST mit zusätzlichem Feld `role` an die Profilroute → 422; 81-stelliger Benutzername → 422.

**SIC-067** · P0 · Status: Ist · **Ausgabe im Frontend**
- Kein `innerHTML`/`dangerouslySetInnerHTML` mit Nutzerinhalt. Markdown nur über React-Elemente. Links nur `http`, `https`, `mailto`, mit `rel="noopener noreferrer"`. Formelsatz (KaTeX) mit `trust: false` und Größenlimits. Texte der Schule (Impressum, Datenschutz) nur als reiner Text, kein HTML; Platzhalter in eckigen Klammern lösen eine Warnung aus. Passwortfelder verdeckt.
- Keine Drittquellen im Browser (Schriften lokal, kein CDN, keine Tracker, kein Session-Replay, keine Analyse); Telemetrie nur, was die Person selbst abschickt (z. B. Feedback-Knopf).
Abnahme: Lint-Regel verbietet `dangerouslySetInnerHTML`; Test mit `javascript:`-Link im Markdown → nicht klickbar; Netzwerkmitschnitt eines Rundgangs durch alle Seiten zeigt ausschließlich eigene Herkunft (0 Fremd-Requests ohne aktiven Anbieter).

**SIC-068** · P0 · Status: offen (Ist: Fehlertexte vereinheitlicht; Lücke: Request-ID fehlt bei 500) · **Fehlerbehandlung**
- Fehlerantwort `{"detail": "..."}`; unerwartete Fehler: generische Meldung „Das hat nicht geklappt“ mit **Request-ID** in Antwort und Log (auch bei Datei-Uploads); Stacktraces nur im Log. Fehlermeldungen enthalten nie Schlüsselmaterial, Passwörter, Empfänger, Antwortinhalte Dritter. Servertexte deutsch.
Abnahme: Ein erzwungener Fehler liefert 500 ohne Stacktrace, mit Request-ID; das Log enthält dieselbe ID; ein fehlgeschlagener Verbindungsversuch (SIC-097) enthält keinen Antwortinhalt des Ziels.

**SIC-069** · P0 · Status: offen (Ist: Schutzfunktion vorhanden, in fünf Exporten nicht genutzt) · **Entschärfung von Tabellenzellen (CSV-Formel-Einschleusung)**
- Eine zentrale Funktion entschärft Zellen, die mit `=`, `+`, `-` oder `@` beginnen (auch nach Leerraum/Tabulator), und wird von **jedem** CSV-/Tabellen-Export genutzt: Beobachtungsprotokoll, API-Protokoll, Kompetenzen, Stammdaten-Export, OneRoster, Notenbuch-CSV und alle weiteren.
Abnahme: Ein Test schreibt `=1+1`, `+SUMME(A1)`, `-2`, `@x` in Namens-/Freitextfelder und prüft in **jedem** Export, dass das führende Zeichen neutralisiert ist; der Registry-Test (SIC-005) scheitert, wenn ein Export die Funktion nicht nutzt.

**SIC-070** · P0 · Status: offen · **Weiterleitungsziele nur intern**
- Das Ziel `next` nach Anmeldung, Verbinden von Anbietern und Passwort-Zurücksetzen darf nur ein eigener, interner Pfad sein (kein Schema, kein Host, kein `//`); die Anbieter-URL beim Verbinden wird einheitlich geprüft; Reset-Parameter ohne Erzeuger entfallen (Fund U-91).
Abnahme: `next` ∈ {`https://fremd.example`, `//fremd.example`, `/\fremd.example`, `javascript:…`} → Umleitung auf `/`; `next=/profil` → wird übernommen.

**SIC-071** · P0 · Status: offen · **Import-Parser: Ressourcen-Grenzen**
- Alle Importe (Untis GPU, CSV, JSON, GIFT, Moodle-Abzug/Sicherung, OneRoster, WebUntis, ZIP) verlangen Importrecht und haben Größen-, Zeit- und Entpackgrenzen (entpackte Gesamtgröße, Dateianzahl, Kompressionsverhältnis, Verarbeitungszeit); Archive ohne Pfadausbruch („Zip-Slip“); XML wird vollständig, nicht nur am Dateianfang, geprüft. Obergrenze Austausch-Import 50 MiB. Vorschau ohne Änderung mit Token-Bindung, Ausführen, Rückgängig; fehlerhafte Zeilen werden gemeldet, nicht abgebrochen; Import-Protokoll verschlüsselt (DAT-016). [unklar: konkrete Entpackgrenzen (Gesamtgröße, Anzahl, Verhältnis) im Neubau festlegen und per Test belegen.]
Abnahme: Ein Archiv, das über der festgelegten Entpackgrenze liegt, wird mit Fehler abgelehnt, ohne dass der Prozess Speicher/Zeit über der Grenze verbraucht; ein Archiv mit Pfad `../x` wird abgelehnt; Import ohne Importrecht → 403.

**SIC-072** · P0 · Status: Ist · **Doppelsende-Schutz**
- Chat-Senden, Postfach-Neu und Postfach-Antwort nehmen optional `client_msg_id` (8 bis 64 Zeichen `A-Za-z0-9_-`, eine UUID je Absendevorgang); derselbe Schlüssel desselben Kontos im selben Chat/derselben Unterhaltung liefert die bereits gesendete Nachricht erneut (201, gleiche ID); Aufbewahrung des Schlüssels 24 Stunden; Inhalte werden nicht verglichen. Formular-Einreichung: doppelte Einreichung binnen 5 Sekunden → 409. Gleichzeitige Wiederholungen entscheidet der Primärschlüssel.
Abnahme: Zweimal gleiche `client_msg_id` → genau eine Nachricht, zweite Antwort 201 mit gleicher ID; 20 parallele Sendungen mit gleichem Schlüssel → eine Nachricht; zweite Formular-Einreichung nach 3 s → 409.

**SIC-073** · P0 · Status: offen (Ist: HMAC-Signatur; Lücke: Zeitstempel nicht signiert) · **Ausgehende Webhooks**
- Signatur HMAC-SHA256 mit `SM_WEBHOOK_SECRET` über Körper **und Zeitstempel** (Zeitstempel-Header mitsigniert, Empfänger kann Wiedereinspielung erkennen). Ziele nur über die Zielprüfung (Kap. 13). Einstellbar nur durch die Administration mit Bearbeitungsrecht; im Demo-Betrieb gesperrt (feldweise). Webhook-Ziele und Geheimnis gelten nie im Klartext in Antworten/Protokollen.
Abnahme: Ein Webhook-Empfänger prüft Signatur und Zeitstempel: manipulierter Körper oder um 10 Minuten verschobener Zeitstempel → Prüfung schlägt fehl; Webhook-Ziel `http://127.0.0.1/…` → abgelehnt.

**SIC-074** · P0 · Status: Ist · **Automatische E-Mails: Kennzeichnung und Abmeldung**
- Alle automatischen Mails tragen `Auto-Submitted: auto-generated`. Vertretungs-/Planänderungs-Rundmails, E-Mail-Hinweise des Postfachs und Mails der Benachrichtigungszentrale tragen einen signierten Abmeldelink (HMAC, gilt nur für diese Abmeldung) sowie `List-Unsubscribe` und `List-Unsubscribe-Post: List-Unsubscribe=One-Click`. GET zeigt nur eine Bestätigung (Mail-Scanner melden niemanden ab); POST setzt die Einstellung; Audit `notification.unsubscribe`. Hat die Schule eine Art fest vorgegeben, ändert die Abmeldung nichts und sagt das. Pflicht-Mails (Passwort zurücksetzen, Sicherheit, Zugangsbriefe) haben weder Link noch Köpfe.
- Mails enthalten keine Krankheitsgründe, Noten, Diagnosen; Namen in Betreff/Text nur nach Schulvorgabe („Neutralmodus“: nur Hinweis und Link). Test-Mails nur an `example.org`.
Abnahme: Rundmail-Header enthält die drei Kopfzeilen; GET auf den Abmeldelink ändert nichts, POST schaltet ab; manipulierter Token → 400; Passwort-Reset-Mail enthält keinen Abmeldelink.

---

## 6 Uploads und Dateien

**SIC-075** · P0 · Status: Ist · **Größen und Kontingente**
- `SM_UPLOAD_MAX_MB` = 25 (Bereich größer 0 bis 10240; Start bricht sonst ab); die Größe wird **schon während der Übertragung** gezählt (Abbruch → 413). Reverse-Proxy begrenzt Anfragen zusätzlich (50 MB; über ca. 49 MB muss das Proxy-Limit angehoben werden). Zweckgrenzen: Schülerdokument (PDF, Bilder) bis 15 MB; Austausch-Import 50 MiB; Mailanhang beim Mailabruf 10 MiB; versandte E-Mail insgesamt höchstens 20 MB.
- Kontingent je Konto: Personal 2000 MB (`SM_QUOTA_MB_STAFF`), Schüler/innen und Eltern 200 MB (`SM_QUOTA_MB_STUDENT`); 0 = unbegrenzt; Werte unter 0 → Startabbruch.
Abnahme: Upload mit 26 MB → 413 vor vollständigem Empfang; Konto über dem Kontingent → verständliche Ablehnung; Start mit `SM_UPLOAD_MAX_MB=0` bricht ab.

**SIC-076** · P0 · Status: Ist · **Chat-Bilder: Kontingent und Rate**
- Bis 4 Bilder je Nachricht, je Bild bis 5 MB (PNG, JPEG, GIF, WebP; im Browser verkleinert; Ende-zu-Ende verschlüsselt). Kontingent je Konto: Personal 500 MB (`SM_CHAT_QUOTA_MB_STAFF`), Schüler/innen und Eltern 100 MB (`SM_CHAT_QUOTA_MB_STUDENT`); je Chat 1000 MB (`SM_CHAT_QUOTA_MB_CHAT`); höchstens 30 Uploads je 10 Minuten (`SM_CHAT_UPLOADS_PER_10MIN`); 0 = unbegrenzt. Gesendete Anhänge zählen mit; Platz wird frei, wenn die Nachricht gelöscht wird. Verständliche Fehlermeldung. Ablage der Chat-Blobs in der Dateiablage statt in der Datenbank ist Ziel (zurückgestellt).
Abnahme: 31. Upload innerhalb von 10 Minuten → abgelehnt mit Meldung; das Kontingent-Limit wird auch für bereits gesendete Anhänge geprüft; nach Löschen der Nachricht ist der Platz wieder frei.

**SIC-077** · P0 · Status: Ist · **Inhaltsprüfung (Allowlist am Inhalt)**
- Prüfung am Inhalt (Magic Bytes); Dateiendung und Browser-Angabe zählen nicht. Erlaubt: PDF; Bilder PNG, JPEG, GIF, WebP, HEIC, TIFF (SVG nur als Download); DOCX, XLSX, PPTX, ODT, ODS, ODP, DOC, XLS, PPT; Text, CSV, Markdown, RTF, EPUB; Audio/Video MP3, M4A, WAV, OGG, MP4, MOV, WebM; ZIP; Fachformate (Quelltext `.py`, `.java`, `.c`, `.cpp`, `.sql` nur als Text-Download; `.ggb`, `.notebook`, `.flipchart`, Scratch, SMART behalten ihre Endung).
- Blockiert (Audit `file.blocked`): Programme (EXE, DLL, MSI, ELF, Mach-O, APK, JAR u. a.), Skripte (Shell, PowerShell, JavaScript, VBS u. a.), HTML, PHP, SVG mit Skripten, Office-Dateien mit Makros/ActiveX/eingebetteten Programmen, passwortgeschützte Office-Dateien, nicht prüfbare Archive, PDF mit Startbefehlen (`/Launch`), ZIP mit ausführbaren Dateien oder ungültigen Pfaden. Dateinamen werden bereinigt; die Endung passt immer zum erkannten Inhalt.
Abnahme: Je Blockkategorie eine harmlose Prüfdatei (z. B. Datei mit ausführbarem Kopfteil, HTML-Datei, makrobehaftete Office-Prüfdatei) → abgelehnt mit Audit `file.blocked`; eine PNG mit Endung `.txt` wird mit Endung `.png` gespeichert; `.py` wird nur als Download ausgeliefert.

**SIC-078** · P0 · Status: Ist (Kennzeichnung „ungeprüft“ sichtbar: offen) · **Virenprüfung**
- Optional ClamAV (`SM_CLAMAV_HOST`, Port 3310, Zeitlimit `SM_CLAMAV_TIMEOUT` = 30 Sekunden je Prüfung; leerer Host = aus): jede Datei wird **vor** dem Speichern geprüft; Fund → abgelehnt (Audit `file.virus`). `SM_CLAMAV_REQUIRED=1`: Uploads werden mit 503 abgelehnt, solange der Prüfdienst nicht erreichbar ist (verlangt einen Host, sonst Startabbruch). Ohne Pflicht: Annahme mit Warnung im Log **und sichtbarer Kennzeichnung „nicht virengeprüft“** (fail-open nur mit Kennzeichnung).
Abnahme: Prüfdienst per Attrappe meldet Fund → Upload abgelehnt, Audit `file.virus`; Dienst aus + `REQUIRED=1` → 503; Dienst aus + `REQUIRED=0` → angenommen, Datei trägt Kennzeichnung „nicht virengeprüft“.

**SIC-079** · P0 · Status: Ist (hartes Löschen robust gegen Rollback: offen) · **Speicherung von Dateien**
- Speicherpfad nur aus einer validierten UUID, nie aus Nutzereingaben; Dateien nie unter dem Web-Wurzelverzeichnis und nur über die Schnittstelle ausgeliefert; auf dem Datenträger **nur verschlüsselt** (DAT-004), Dateiname verschlüsselt in der Datenbank; SHA-256 des Klartexts wird gespeichert. Uploads ohne Anhang werden nach 24 Stunden gelöscht, Temp-Reste älter als 6 Stunden gelöscht; weich gelöschte Dateien nach 30 Tagen endgültig. Hartes Löschen entfernt den Inhalt erst **nach** erfolgreichem Abschluss der Transaktion (Fund U-63: späterer Rollback ließ den Blob gelöscht zurück).
Abnahme: Ein Dateisystem-Scan des Dateiverzeichnisses findet nur Dateien mit `SMS1`-Kopf; ein Upload mit Pfadtrennern im Namen landet unter einer UUID; Rollback nach „hart löschen“ lässt die Datei vorhanden.

**SIC-080** · P0 · Status: Ist · **Auslieferung von Dateien**
- Immer als Download (`Content-Disposition` mit `filename*`, RFC 5987); nur PDF und Bilder (außer SVG) dürfen im Browser angezeigt werden (`?inline=1`). Antwortköpfe: `X-Content-Type-Options: nosniff`, `Content-Security-Policy: sandbox`, `Cross-Origin-Resource-Policy: same-origin`, `Cache-Control: no-store`. Aktive Inhalte (HTML, SVG) nie inline; Anhänge nie im Kontext eingeloggter Administratoren ausführen oder anzeigen. Gilt auch für Anhänge des Test-Postausgangs. Dotfiles, Quellen und Source Maps werden nie ausgeliefert (SIC-090).
Abnahme: Header-Test jeder Datei-Route; SVG-Prüfdatei mit `?inline=1` → Download statt Anzeige; PDF inline → mit `sandbox`-CSP.

**SIC-081** · P0 · Status: Ist · **Zugriff auf Dateien und Audit der Fremdabrufe**
- Eigentümer immer; sonst nur über die für den **Verweistyp registrierte** Prüfung (Kursmitglieder für Material, Gesprächsteilnehmende für Anhänge, berechtigte Stellen für Atteste, Aufgabensteller für Abgaben, Formulare, Förderdaten). **Kein automatischer Administrator-Zugriff.** Anhängen nur eigener, noch nicht angehängter Dateien; Löschen nur durch den Eigentümer (fremde Datei → 404). Fremdabrufe werden im Audit (`file.download`, je Konto, Datei und Tag einmal) protokolliert; das Download-Protokoll überlebt Neustarts.
Abnahme: Konto A ruft Datei-ID von Konto B ab → 404; `admin` ruft Attest-Datei → 404; ein Abruf durch berechtigte Klassenleitung erzeugt genau einen Audit-Eintrag je Tag; nach Neustart bleibt der Eintrag.

---

## 7 Verschlüsselung im Ruhezustand: Verfahren, Bindung, Datenschlüssel je Datensatz

**DAT-001** · P0 · Status: Ist · **Verfahren: Umschlagverschlüsselung mit Datenschlüssel je Wert**
- AES-256-GCM (authentifiziert). Jeder verschlüsselte Wert (Feld, Nachricht, Planversion) und jede Datei bekommt einen **eigenen zufälligen 256-Bit-Datenschlüssel**; dieser wird mit dem aktiven Master-Schlüssel des Schlüsselrings „gewrappt“ und mit dem Chiffrat gespeichert. Nonce 96 Bit zufällig je Verschlüsselung.
- Formate (versioniert): Text `SM1.` + Base64-URL ohne Auffüllung (ASCII für Textspalten); Binärfeld Präfix `SM1`; Datei Präfix `SMS1`.
- Fehler: Manipulation, falsches Zusatzdatum (Bindung) oder falscher Schlüssel → „ungültig“; unbekannte Schlüssel-ID → „nicht lesbar“; **Klartext wird nie zurückgegeben**; Fehlermeldungen enthalten nie Schlüsselmaterial.
Abnahme: Ein geändertes Bit im Token → Lesefehler „ungültig“; ein in eine andere Zeile kopiertes Token → „ungültig“; Token mit unbekannter `kid` → „nicht lesbar“; 1 000 000 Verschlüsselungen desselben Klartexts ergeben paarweise verschiedene Nonces und Chiffrate.

**DAT-002** · P0 · Status: offen (Ist: alle Bindungen außer Löschgrund im Audit zeilengebunden) · **Bindung an den Bezugspunkt (zusätzliche authentifizierte Daten)**
- Ein Token ist an seine Zeile gebunden und lässt sich nicht in eine andere Zeile oder ein anderes Feld verschieben. **Ausnahmslos** zeilengebunden (der Löschgrund im Audit hatte im Altsystem ein festes, nicht zeilengebundenes Zusatzdatum).

| Objekt | Bindung |
|---|---|
| Textfelder (alle Tabellen) | `<Tabelle>.<Feld>:<Zeilen-ID>` |
| Planversion | `school_versions.data:<Version-ID>` |
| JSON-Sicherung des Planungsdokuments | `backup.school:<Version>` |
| Datei (Inhalt) | Datei-ID (zusätzlich Blockgröße) |
| Dateiname | `stored_files.filename:<Datei-ID>` |
| 2FA-Geheimnis | `users.totp_secret:<Konto-ID>` |
| Name in der Warteliste | `retention_leavers.name:<ID>` |
| Löschgrund im Audit (Neubau) | `audit_log.<Feld>:<Audit-ID>` |
| Chat-Titel / Meldebild | `chats.title:<ID>` / `chat_report_images.data:<ID>` |
| Nachrichten-Text | `messages.body:<ID>` |
| Beobachtungsprotokoll | `watch_log.<Feld>:<ID>` |

Abnahme: Für jede Zeile der Tabelle: das Token in eine andere Zeile derselben Spalte kopieren → Lesefehler; ein Löschgrund-Token in einen anderen Audit-Eintrag verschoben → „ungültig“.

**DAT-003** · P0 · Status: Ist · **Dateiformat `SMS1`**
- Blockweise authentifiziert verschlüsselt: Blockgröße 64 KiB (Standard; zulässig 1 KiB bis 16 MiB); 32-Bit-Blockzähler und Schlussblock-Kennzeichen verhindern Vertauschen, Weglassen, Abschneiden und Anhängen von Blöcken; 7 Byte zufälliges Präfix je Datei; konstanter Speicherverbrauch beim Lesen/Schreiben. Beim Lesen: Fehler statt stillem Datenmüll.
Abnahme: Datei in der Mitte abgeschnitten, zwei Blöcke vertauscht, Block angehängt → jeweils Lesefehler; 2-GB-Test-Datei wird mit höchstens 64 MiB zusätzlichem Speicher verarbeitet [Prüfwert].

**DAT-004** · P0 · Status: Ist · **Dateien und Dokumente: kein Klartext auf dem Datenträger**
- Inhalt (`SMS1`) und Dateiname (Token) verschlüsselt; bei Atteste/Dokumente zusätzlich Titel und Vermerk. Das gilt für Kursräume, Postfach, Chats, Atteste, Formulare, Förderdaten, Abgaben, Zugangsbriefe, Import-Anhänge. Zugriff: SIC-081.
Abnahme: Ein Scan aller Dateien im Dateiverzeichnis findet keine Datei ohne `SMS1`-Kopf und keinen Klartext-Dateinamen; in der Datenbank beginnt jeder `filename`-Wert mit `SM1.`.

**DAT-005** · P0 · Status: Ist · **Schutzziel und dokumentierte Grenzen**
- Schutz vor Lesen aus gestohlenen oder versehentlich veröffentlichten Datenbank-Dumps und Sicherungen, aus Festplatten-/Snapshot-Kopien beim Hoster und durch Datenbank-Administration ohne Schlüssel.
- **Keine** Wirkung gegen: Root-Zugriff auf den laufenden Server (der Schlüssel liegt in der Prozessumgebung) und Missbrauch berechtigter Konten (dafür Rechtekonzept, 2FA, Audit). Nachrichten im Postfach sind **nicht** Ende-zu-Ende verschlüsselt (Server entschlüsselt zur Anzeige und Moderation, `messages.moderate`). Diese Grenzen stehen in den TOMs und im Sicherheitskonzept.
Abnahme: TOMs/Sicherheitskonzept enthalten die drei Grenzen wörtlich (Dokumenten-Test, SIC-008).

**DAT-006** · P0 · Status: offen (Ist: Klartext-Altbestand beim Lesen übernommen; Entschlüsselungsfehler im Klassenbuch geschützt) · **Kein Klartext in registrierten Spalten; unlesbare Einträge nie still überschreiben**
- Der Neubau führt keinen Klartext in verschlüsselten Spalten: Datenübernahme aus dem Altsystem (Import/Migration) verschlüsselt beim Einlesen, Planungsdokument eingeschlossen. Ein Klartextwert in einer registrierten Spalte gilt beim Lesen als Fehler.
- Ein nicht lesbarer Eintrag (falscher/fehlender Schlüssel, Manipulation) wird **nie** still mit leeren Werten überschrieben: Speichern bricht ab (409), die Seite zeigt einen Hinweis (z. B. Klassenbuch-Notiz).
Abnahme: Test-Datensatz mit Klartext in einer `_enc`-Spalte → Lesefehler; Speichern eines Klassenbuch-Eintrags mit nicht lesbarer Notiz → 409 und die Notiz bleibt unverändert.

---

## 8 Schlüsselverwaltung und Rotation

**DAT-007** · P0 · Status: Ist · **Schlüsselring `SM_ENCRYPTION_KEYS`**
- Format `kid:Base64(32 Byte)`, Trenner Komma, Semikolon, Leerzeichen oder Zeilenumbruch; der **erste** Eintrag ist aktiv (verschlüsselt neue Daten), weitere nur zum Entschlüsseln. Schlüssel-ID 1 bis 32 Zeichen (A–Z, a–z, 0–9, `_`, `-`), Dubletten sind ein Fehler, `dev` ist reserviert; Standard-ID beim Erzeugen `k` + Datum (JJJJMMTT). Schlüsselgröße genau 32 Byte, sonst Konfigurationsfehler.
- Produktion: Pflicht – ohne gültigen Ring bricht der Start ab. Entwicklung ohne Ring: Schlüssel `dev` aus `SM_SECRET_KEY` per HKDF-SHA256 abgeleitet, Warnung im Log; solche Instanzen nie mit Echtdaten; mit Ring bleibt `dev` nur als Entschlüsselungs-Rückfall.
- Werkzeuge: `gen-key` erzeugt einen Schlüssel; `crypto-status` zeigt aktive Kennung und **Fingerabdrücke** (12 Hex-Zeichen, SHA-256 über Präfix und Schlüssel, nicht umkehrbar), nie Schlüsselmaterial; Anzeige auch in der Statusseite.
Abnahme: Start im Produktivmodus ohne Ring → Abbruch; Ring mit doppelter `kid`, 31-Byte-Schlüssel oder `dev` → Abbruch; `crypto-status` und Statusseite enthalten keine Schlüsselbytes (Suche nach dem Base64-Wert: 0 Treffer).

**DAT-008** · P0 · Status: offen (Ist: Rotation gebaut; Lücke: „innere Token“ des Plans bleiben am alten Schlüssel) · **Rotation ohne Ausfall**
- Ablauf: neuen Schlüssel **vorn** eintragen (`k2:…,k1:…`), neu starten, `rotate-keys`. Wirkung: alle Datenschlüssel werden neu gewrappt, Nutzdaten bleiben unverändert (schnell auch bei vielen Dateien). Dateien: nur der Kopf wird neu geschrieben, Blöcke werden kopiert, atomar ersetzt (Datei zuerst schließen, dann ersetzen). Die Rotation umfasst **alle** registrierten Spalten (SIC-005) einschließlich der inneren Token im Planungsdokument (z. B. Abwesenheitsgründe), des TOTP-Geheimnisses, des Beobachtungsprotokolls und des Namens in der Warteliste.
- Planversionen, deren Schlüssel nicht mehr im Ring steht, werden mit Warnung übersprungen; die Rotation bricht deshalb nicht ab. Anlässe: jährlich, Personalwechsel in der IT, Verdacht auf Offenlegung.
- Den alten Schlüssel erst entfernen, wenn **alle** Sicherungen, die ihn brauchen, abgelaufen sind (bis 12 Monate; Kalendereintrag, DAT-010).
Abnahme: Nach `rotate-keys` ist die Testdatenbank (ohne Backups) allein mit dem neuen Schlüssel vollständig lesbar, auch Dateien und die inneren Token des Plans; ein zweiter Aufruf ändert nichts (idempotent); während der Rotation bleibt die Anwendung erreichbar.

**DAT-009** · P0 · Status: offen (Aufrufweg im Altsystem unklar) · **Kompromittierung eines Master-Schlüssels**
- Vorgesehen ist eine vollständige Neuverschlüsselung (neuer Datenschlüssel je Wert) als eigener Befehl; Name und Ablauf legt der Neubau fest [unklar: Aufrufweg im Altsystem nicht belegt]. Nach Verdacht auf Offenlegung zusätzlich als Vorfall behandeln (SIC-135 bis SIC-137): alte Sicherungen bleiben mit dem alten Schlüssel lesbar, alle Geheimnisse rotieren.
Abnahme: Nach dem Neuverschlüsselungs-Befehl ist kein Datenschlüssel-Wert der Datenbank mehr mit dem alten Datenschlüssel identisch (Stichprobe über jede Registry-Spalte); Entschlüsselung mit nur dem neuen Schlüssel gelingt.

**DAT-010** · P0 · Status: Ist (Lagerort des Schlüssels auf Live-Instanzen: Prüfung offen) · **Aufbewahrung der Schlüssel**
- Produktion: Schlüssel nur aus Umgebung/Secret-Store; `.env` Rechte 600, Besitzer root. **Nicht neben der Datenbank**, nicht im Repository, nicht im Image, nicht im Speicher oder Bucket der Sicherungen, nie per E-Mail oder Chat. Zwei getrennte Aufbewahrungsorte: Passwort-Tresor der Schulleitung und versiegelter Ausdruck im Safe. Entwicklung: Schlüsseldatei mit Rechten 0600.
- Verlust des Schlüssels = Verlust der verschlüsselten Inhalte, auch aus allen Sicherungen. Es gibt **keine Hintertür** und keinen Generalschlüssel des Herstellers. Die Wiederherstellung einer Sicherung ohne den passenden Schlüssel bricht mit klarer Meldung ab.
Abnahme: Ein Scan jedes Sicherungsarchivs findet keinen Wert aus `SM_ENCRYPTION_KEYS`/`SM_SECRET_KEY`; Wiederherstellung auf einer Instanz ohne den Schlüssel → Abbruch mit Meldung „Schlüssel fehlt“ ohne Teilimport; der Betriebsnachweis nennt zwei Aufbewahrungsorte.

**DAT-011** · P0 · Status: Ist · **Geheimnis `SM_SECRET_KEY` (HMAC)**
- Mindestens 32 Zeichen, Platzhalter (Wert beginnt mit `BITTE_AENDERN` oder enthält `CHANGE_ME`) verboten; dient als HMAC-Schlüssel für Sitzungs-Hashes, API-Token, Codes, Kalender-Token, SSO-Status, Teilnahmekennungen im Lernbereich, OAuth-Status des Postfachs. Entwicklung ohne Wert: einmal erzeugt in `.secret_key` (Rechte 600), bei nicht schreibbarem Verzeichnis zufällig je Start. Wechsel macht Sitzungs-Hashes, API-Token und offene Codes ungültig (bewusste Folge, SIC-055).
Abnahme: Produktionsstart mit 31 Zeichen oder Platzhalter → Abbruch; Wechsel invalidiert eine bestehende Sitzung.

---

## 9 Katalog der verschlüsselten Felder (verbindlich; Registry SIC-005)

Spaltennamen mit Suffix `_enc` bzw. als `SM1`-Token gespeichert. Neubau: einheitliche Benennung (`_enc`), auch bei Krankmeldungen (Altsystem: `reason`, `note` ohne Suffix). Die Liste ist ein Mindeststand; die Registry macht sie vollständig [unklar: Altsystem ruft Verschlüsselung in über 30 Dateien auf, Vollständigkeit nicht belegt].

**DAT-012** · P0 · Status: Ist · **Gesundheit, Förderung, Formulare, Klassenbuch**

| Tabelle | Verschlüsselte Felder |
|---|---|
| `student_absences` | Grund, Vermerk (`reason`, `note`) |
| `student_documents` | `title_enc`, `note_enc` (Datei zusätzlich, DAT-004) |
| `student_support` | `title_enc`, `details_enc`, `aids_enc` (Nachweise als Dateien) |
| `form_submissions` / `form_events` | `answers_enc`, `decision_note_enc` / `note_enc` |
| `register_lessons` | `topic_enc`, `homework_enc`, `attendance_enc` (JSON, inkl. Anwesenheitsnotiz) |
| `teacher_change_requests` | `note_enc`, `review_comment_enc` (Anlass/Freitext der Lehrkraft) |

Abnahme: Datenbank-Dump-Scan: in allen aufgeführten Spalten beginnt jeder Wert mit `SM1`; Stichprobe 100 Zeilen je Tabelle ergibt 0 lesbare Zeichenfolgen.

**DAT-013** · P0 · Status: Ist · **Leistung, Aufgaben, Kompetenzen**

| Tabelle | Verschlüsselte Felder |
|---|---|
| `exam_results` | `grade_enc`, `note_enc` |
| `gb_entries`, `gb_finals` | `value_enc`, `note_enc` |
| `gb_log` | `detail_enc` |
| `comp_assessments` | `evidence_enc`, `comment_enc` |
| `comp_plans` | `title_enc`, `note_enc` |
| `comp_badge_awards` | `note_enc` |
| `grading_templates` / `assignment_settings` / `assignment_extensions` | `criteria_enc` / `rubric_enc` / `reason_enc` |
| `assignment_submissions`, `assignment_submission_versions` | `text_enc`, `feedback_enc`, `grade_enc`, `rubric_enc` |

Abnahme: wie DAT-012 für diese Tabellen.

**DAT-014** · P0 · Status: Ist · **Kursräume und Lernaktivitäten**

| Tabelle | Verschlüsselte Felder |
|---|---|
| `channel_items`, `channel_posts` | `body_enc` (Markdown-Inhalt) |
| `learning_polls` | `question_enc`, `options_enc` |
| `learning_surveys` / `learning_survey_responses` | `intro_enc` / `answers_enc` |
| `learning_questions` / `learning_selftests` | `data_enc` / `description_enc` |
| `learning_attempts` | `snapshot_enc`, `answers_enc`, `result_enc` |

Umfragen sind **wirklich anonym**: die Teilnahme wird nicht der Person zugeordnet gespeichert (Teilnahmekennung per HMAC ohne Rückbezug).
Abnahme: wie DAT-012; in einer anonymen Umfrage gibt es keine Zuordnung Antwort → Konto (Spaltenprüfung der Tabellen).

**DAT-015** · P0 · Status: Ist · **Kommunikation und Benachrichtigungen**

| Tabelle | Verschlüsselte Felder |
|---|---|
| `messages` / `conversations` | `body_enc` / `subject_enc` |
| `message_reports` | `reason_enc`, `resolution_enc` |
| `message_user_settings` / `message_drafts` | `suspension_reason_enc` / `data_enc` |
| `notifications` | `title_enc`, `body_enc` |
| Benachrichtigungs-Postausgang | Empfänger, Betreff, Text, Anhänge (bis zur Zustellung; danach geleert) |
| `chats` | `title_enc` |
| `chat_messages` | `legacy_body_enc` (aus dem Postfach übernommene Kopien); neue Nachrichten: Ende-zu-Ende, Server speichert nur Nonce und Chiffrat |
| `chat_reports` / `chat_report_images` | `reason_enc`, `content_enc` / `data_enc` (binär) |

Abnahme: wie DAT-012; Chat-Nachrichten bestehen in der Datenbank nur aus Nonce und Chiffrat (kein Klartextfeld).

**DAT-016** · P0 · Status: offen (Ist: Aufstellung unten; offen: SMTP-/SMS-Passwörter in der Oberfläche) · **Konto, Anmeldung, Zugangsdaten, Betrieb**

| Tabelle | Verschlüsselte Felder |
|---|---|
| `users` | `totp_secret_enc` (20 Byte Zufall, Base32) |
| `user_contacts` | `phone_enc` (Suche über HMAC-Index) |
| `auth_codes` | `target_enc` (Zieladresse) |
| `sso_providers` | `client_secret_enc`, `private_key_enc` (Apple) |
| `mail_accounts` | `secret_enc` (verschlüsseltes JSON) |
| `letter_batches` | `data_enc` (Startzugangsdaten, SIC-039) |
| `import_runs` | `report_enc` |
| SMTP-/SMS-Zugangsdaten (Neubau, in der Oberfläche einstellbar) | verschlüsselt gespeichert, nie wieder angezeigt (Testversand mit verständlicher Fehlermeldung); Umgebungsvariablen haben Vorrang und sind als „vom Server vorgegeben“ gekennzeichnet |
| Lizenzserver: Schulschlüssel | Hash zum Suchen, zusätzlich verschlüsselt zum Anzeigen |

Abnahme: wie DAT-012; Konfigurationsmaske zeigt gespeicherte Geheimnisse nie an (Antwort enthält kein Geheimnisfeld).

**DAT-017** · P0 · Status: Ist · **Protokolle, Planungsdokument, Warteliste**

| Gegenstand | Verschlüsselt |
|---|---|
| Planungsdokument (`school_versions.data`) | ganze Version, komprimiert und verschlüsselt, jede Version ein eigenes Token; enthält Stammdaten mit Geburtsdaten, Abwesenheitsgründe, Notizen zu Vertretungen, Monitor-Hinweise |
| JSON-Sicherung des Planungsdokuments | verschlüsselt (Bindung `backup.school:<Version>`), auch bei PostgreSQL |
| `retention_leavers` | `name_enc` (wird beim Abschluss geleert) |
| `watch_log` | `query_enc`, `body_enc`, `changes_enc` (geschwärzt und verschlüsselt, Kap. 15) |
| `audit_log` | Löschgrund (`details.grund_enc`); sonst nur Länge |
| `stored_files` | Dateiname; Inhalt in `SMS1` |
| SSO-Cookies | Status (`sm_sso_<Anbieter>`) und E-Mail (`sm_sso_who`) |

Abnahme: wie DAT-012; Löschen mit Grund „Test“ → im Audit nur Länge 4 und ein `SM1`-Token.

**DAT-018** · P0 · Status: Ist · **Bewusst nicht verschlüsselte Daten (mit Begründung)**
- Konten-Stammdaten (Benutzername, Anzeigename, Rolle), die E-Mail-Adresse des Kontos (für Versand und Suche), benannte Plan-Stände (`plan_snapshots`: nur Stundenzuordnungen, ohne Freitext), Metadaten der Chats (Mitglieder, Zeitpunkte, Größen, öffentliche Schlüssel, Gerätenamen), das Audit-Log (ohne Inhalte), das Löschprotokoll. Begründung: Diese Daten schützen Rechtekonzept, Transport- und Sicherungs-Verschlüsselung. [unklar: Ob die Konto-E-Mail im Neubau ebenfalls verschlüsselt mit HMAC-Suchindex gespeichert wird (wie die Telefonnummer), entscheidet der Betreiber.]
- Suche über verschlüsselte Inhalte: Chats nur nach Name; Briefe nach Inhalt (serverseitig entschlüsselt); Telefonnummer per HMAC-Index.
Abnahme: Die Liste dieser Datenarten stimmt mit der Registry überein (Test: jede Tabelle mit Freitext-Spalte ist entweder im Katalog oder hier aufgeführt).

---

## 10 Ende-zu-Ende-verschlüsselte Chats (Sicherheitsmodell)

**SIC-082** · P0 · Status: Ist · **Verfahren und Schlüsselablage**
- Je Nachricht ein zufälliger Inhaltsschlüssel K (secretbox); der Absender verpackt K für jedes Gerät **aller** Mitglieder und eigener Geräte (box, X25519; Bibliothek mit fester Version, tweetnacl 1.0.3). Jedes Gerät hat einen eigenen Schlüssel; der private Geräteschlüssel verlässt den Browser nie.
- Ablage: nicht exportierbarer WebCrypto-Schlüssel (X25519, `extractable=false`) in IndexedDB; Rückfallstufe `wrapped` (AES-GCM mit nicht exportierbarem AES-Schlüssel) für Browser ohne X25519. **Kein Klartext-Rückfall**: ohne IndexedDB/WebCrypto (z. B. kein HTTPS, bestimmte private Fenster) sind Chats nicht möglich, mit verständlicher Meldung. Chats funktionieren nur über HTTPS (oder localhost). Altbestände im lokalen Speicher werden beim nächsten Öffnen übernommen und gelöscht.
- Der Server sieht: Konten, Mitglieder, Zeitpunkte, Größen, öffentliche Schlüssel, Gerätenamen, verpackte Schlüssel, kurzlebige Verknüpfungs-Codes, das Archiv-Blob. Der Server sieht **nie**: Nachrichtentexte, Bilder, Inhaltsschlüssel, private Geräte-/Archivschlüssel, Passwort oder Wiederherstellungscode.
- Dokumentierte Grenzen: ein kompromittierter Server könnte beim Verknüpfen ein eigenes Gerät unterschieben (Gegenmaßnahme: Fingerabdruck-Vergleich); wer das Browserprofil lesen kann, liest IndexedDB (Gegenmaßnahme: Geräteverschlüsselung des Betriebssystems, gesperrtes Gerät).
Abnahme: Datenbank-Dump einer Test-Unterhaltung enthält weder Klartext noch Bildbytes noch einen Inhaltsschlüssel; im Browser ist der Geräteschlüssel nicht exportierbar (`exportKey` schlägt fehl); ohne WebCrypto zeigt die Seite die Meldung statt eines Klartext-Modus.

**SIC-083** · P0 · Status: Ist · **Geräte-Verknüpfung**
- Das neue Gerät zeigt Code (8 Zeichen), QR-Code und Fingerabdruck; ein bereits eingerichtetes Gerät gibt den Code ein, vergleicht den Fingerabdruck und bestätigt („Stimmt – übertragen“). Der Code ist 15 Minuten gültig, danach 2 Stunden Übertragungsfenster; höchstens 10 Fehlversuche je 10 Minuten; nur im eigenen Konto auffindbar.
- Das alte Gerät öffnet die Inhaltsschlüssel in Paketen zu 200 (fortsetzbar, abbrechbar) und verpackt sie für das neue Gerät (`POST /chat-keys`). Der Server prüft: beide Geräte gehören zum selben Konto, Freigabe liegt vor, die Person war Mitglied, die Nachricht liegt nach der Beitrittsgrenze. Nachrichten **vor** der Mitgliedschaft bleiben für die Person unlesbar (auch beim Nachverpacken). Bilder: ihr Schlüssel steht im verschlüsselten Inhalt.
Abnahme: Code nach 16 Minuten → abgelehnt; 11. Fehlversuch innerhalb von 10 Minuten → 429; Paket mit Schlüsseln für Nachrichten vor der Beitrittsgrenze → abgelehnt; Gerät eines fremden Kontos → abgelehnt.

**SIC-084** · P0 · Status: Ist · **Archiv und Wiederherstellung**
- Optional ein Archiv-Schlüsselpaar je Konto: der öffentliche Teil erscheint als „Gerät“ der Art `archive`; der private Teil liegt nur als Blob (`chat_key_backups`) auf dem Server, verschlüsselt mit einem Schlüssel aus Wiederherstellungscode oder Passwort (PBKDF2-SHA-256, 1 000 000 Runden, Salt im Blob). Empfohlen: erzeugter Code (125 Bit); eigenes Passwort mindestens 12 Zeichen. **Ohne Code/Passwort gibt es keine Wiederherstellung**, auch nicht durch Schule oder Betreiber – die Seite sagt das deutlich. Passwort ändern und Backup löschen möglich; Löschen entfernt den Archivschlüssel und alle für ihn verpackten Schlüssel. Grenze: wer die Datenbank hat, kann das Blob offline raten – nur ein starker Code/Passwort schützt.
Abnahme: Eigenes Passwort mit 11 Zeichen → abgelehnt; der Blob ist ohne Code nicht entschlüsselbar (Test mit falschem Code); nach „Backup löschen“ existiert weder Blob noch ein für `archive` verpackter Schlüssel.

**SIC-085** · P0 · Status: Ist · **Zurücksetzen und Sicherheitsmeldungen**
- „Dieses Gerät neu einrichten“ erzeugt ein neues Schlüsselpaar (Verlauf wandert auf Wunsch mit) und widerruft das alte. „Alle Geräte zurücksetzen“ widerruft alle Geräteschlüssel des Kontos (Backup wahlweise behalten); Gesprächspartner verwenden automatisch die neuen Schlüssel. Der Browser merkt sich je Person die Fingerabdrücke und meldet „Sicherheitsschlüssel von X hat sich geändert“ bzw. „weiteres Gerät“; neue eigene Geräte werden den anderen eigenen Geräten als „neu“ gemeldet (Live-Ereignis, Banner), bis ein anderes Gerät sie bestätigt oder entfernt.
Abnahme: Nach „Alle Geräte zurücksetzen“ kann ein widerrufenes Gerät keine neue Nachricht lesen; ein neuer Schlüssel einer Gegenstelle löst das Banner aus.

**SIC-086** · P0 · Status: offen · **Chat-Schlüssel beim Abmelden entfernen**
- Beim Abmelden werden die lokalen Chat-Schlüssel (Geräteschlüssel, Zwischenspeicher) aus dem Browser entfernt oder gesperrt; auf geteilten Schulrechnern darf nach dem Abmelden kein Zugriff auf Chats des vorherigen Kontos bleiben (Prüffund: Schlüssel blieben nach Abmeldung erhalten). [unklar: Betreiber-Entscheidung, ob „Abmelden“ das Gerät aus dem Konto löscht (erneute Verknüpfung nötig) oder die Ablage nur sperrt (PIN/Passwort-Hülle)].
Abnahme: Nach Logout liefert eine Inspektion der Browser-Speicher (IndexedDB, lokaler Speicher) keinen nutzbaren Geräteschlüssel des abgemeldeten Kontos; eine zweite Person auf demselben Gerät kann keinen Chat des ersten Kontos entschlüsseln.

**SIC-087** · P0 · Status: Ist · **Moderation und Audit bei verschlüsselten Chats**
- Meldeweg: Die meldende Person sendet freiwillig den Klartext der gemeldeten Nachricht (Server speichert ihn verschlüsselt, `content_enc`, Meldebilder `data_enc`); lesbar nur mit dem Recht `messages.moderate`/`chats.review` (nur mit Einwilligung der meldenden Person); nie durch technische Administration. Eine Chat-Moderation ohne Klartext-Zugriff auf Chats ist bewusst so entschieden.
- Chat-Audit: Verwaltungsaktionen (Geräte, Mitglieder, Moderation, Löschen, Meldungen) mit Kennungen, ohne Inhalte und Meldegründe; einzelne gesendete Nachrichten und „gelesen“-Markierungen werden **nicht** protokolliert (sonst entstünde ein Protokoll, wer wann wem schreibt). Gelöscht werden Server-Daten, nicht Kopien auf Geräten anderer. Aus dem Postfach übernommene Alt-Nachrichten sind nicht Ende-zu-Ende, sondern serverseitig verschlüsselt (`legacy_body_enc`) und erscheinen als „übernommen aus dem Postfach“.
Abnahme: `admin` ruft Meldungsinhalt → 404; Chat senden erzeugt keinen Audit-Eintrag, Mitglied entfernen erzeugt genau einen mit Kennungen; der Meldungsinhalt ist in der Datenbank `SM1`.

---

## 11 Transport, Sicherheits-Header, CSP, CORS

**SIC-088** · P0 · Status: Ist · **Transportverschlüsselung**
- TLS 1.2 oder 1.3 mit HSTS am Reverse-Proxy (Caddy oder nginx); Port 80 leitet auf HTTPS um; eingehend nur 80/tcp, 443/tcp, 443/udp (QUIC). Zertifikate automatisch (Let's Encrypt, DNS-Prüfung oder HTTP-Prüfung) mit automatischer Erneuerung; Ablauf-Warnung 14 Tage vorher im Monitoring. Let's Encrypt erhält nur Domainnamen und Kontakt-E-Mail.
- Im Echtbetrieb startet die App nur mit `SM_BASE_URL` als `https://`-Adresse (nicht lokal) und `SM_COOKIE_SECURE=1`. Kein HTTP-Zugang zur Anwendung im Echtbetrieb (die Hauptinstanz des Altsystems lief wegen eines Heimnetz-Zugangs mit `SM_COOKIE_SECURE=0` – im Neubau ausgeschlossen). [unklar: `max-age` der HSTS-Kopfzeile nicht belegt; Neubau legt einen Wert fest, mindestens 6 Monate.]
Abnahme: HTTP-Anfrage → Umleitung auf HTTPS; jede HTTPS-Antwort trägt `Strict-Transport-Security`; TLS-1.1-Handshake wird abgelehnt; Produktivstart mit `http://`-Basisadresse bricht ab.

**SIC-089** · P0 · Status: Ist · **Sicherheits-Kopfzeilen und Content-Security-Policy**
- Jede Antwort (App, Proxy): `Content-Security-Policy` mit `default-src 'self'`, `script-src 'self'` (kein `unsafe-inline` für Skripte), `frame-ancestors 'none'`, `object-src 'none'`; `X-Frame-Options: DENY`; `X-Content-Type-Options: nosniff`; `Referrer-Policy` (same-origin); `Permissions-Policy`; Cross-Origin-Opener-Policy; API-Antworten `Cache-Control: no-store`; HSTS (SIC-088). Dateiauslieferung: SIC-080.
- Jede Kopfzeile erscheint **genau einmal** (nicht doppelt durch App und Proxy; Fund U-100: doppelte Header blockierten die Swagger-Seite); die App-eigene CSP hat Vorrang vor dem Proxy-Fallback. Die Swagger-Oberfläche wird lokal ausgeliefert, die CSP braucht kein CDN. Keine Ressourcen von Dritten (Schriften lokal).
Abnahme: Header-Test auf Startseite, einer API-Route, einer Datei-Route und der API-Doku: alle genannten Köpfe vorhanden, jeder genau einmal; CSP-Bericht eines Rundgangs durch alle Seiten: 0 Verstöße.

**SIC-090** · P0 · Status: Ist · **CORS, Quellen, Betriebs- und Doku-Endpunkte**
- **CORS:** fremde Websites haben keinen Zugriff auf die API (keine Freigabe für fremde Ursprünge, keine Freigabe von Anmeldedaten).
- Ausgeliefert werden nur Build-Dateien erlaubter Typen: keine Source Maps, keine Quellen, **keine Dotfiles** (`.env`, `.git` u. ä., auch nicht aus dem Build-Ordner); die Single-Page-Auslieferung (Fallback unbekannter Pfade auf die Anwendung) liefert sie nicht.
- API-Dokumentation `/api/docs`, `/api/openapi.json` über `SM_ENABLE_DOCS`: `off` (Standard in Produktion), `admin` (sonst; nur angemeldete Administratoren), `public`. `/metrics` ohne `SM_METRICS_TOKEN` geschlossen (401), mit Bearer-Token; der Proxy sperrt `/metrics` zusätzlich von außen; `/healthz` liefert nur Status, keine Daten. `/llms.txt`, `/llms-full.txt`, `/robots.txt`, `/.well-known/api-catalog`, `/meta/openapi.json` sind öffentlich, enthalten aber keine Namen oder personenbezogenen Daten (Test).
Abnahme: Anfrage mit `Origin: https://fremd.example` erhält keinen `Access-Control-Allow-Origin`; GET auf `/.env`, `/.git/config`, `/assets/*.map` → 404; `/api/docs` in Produktion → 403/404; `/metrics` ohne Token → 401; Scan der öffentlichen Texte auf Eigennamen von Testpersonen → 0 Treffer.

---

## 12 Missbrauchsschutz: Drosselung und Rate-Limits

**SIC-091** · P0 · Status: Ist · **Anmelde-Drosselung: Zähler**
- Grundsatz: **keine harte Kontosperre** (schützt vor gezieltem Aussperren fremder Konten), sondern gestaffelte Wartezeit; ein Schulnetz hinter einer Adresse wird nie komplett ausgesperrt. Betreiber: „Die Login-IP-Drosselung arbeitet mit gestaffelter Wartezeit statt Sperre.“ Gedrosselte Anfragen zählen nicht als Fehlversuch.

| Zähler | Schwelle | Zählfenster | Wartezeit | Wirkt auf | Zurückgesetzt durch |
|---|---|---|---|---|---|
| Paar Benutzername + IP | 5 Fehlversuche (`SM_LOGIN_MAX_FAILURES`) | 15 Minuten (`SM_LOGIN_LOCK_MINUTES`), seit letztem Erfolg des Kontos | 30 s × 2^(Überschuss), Deckel 900 s (= `SM_LOGIN_LOCK_MINUTES` × 60, mindestens 30 s) | Anmeldung dieses Kontos von dieser IP | Erfolg des Kontos (auch SSO, Passwort-Reset); Verwaltung |
| IP insgesamt | 30 Fehlversuche (`SM_LOGIN_MAX_FAILURES_IP`) plus erfolgreiche Anmeldungen dieser IP im Fenster | 15 Minuten | 2 s × 2^(Überschuss ÷ 10 ganzzahlig), Deckel 60 s | alle Konten von dieser IP; greift nur, wenn das Paar mindestens 1 Fehlversuch hat (**erster Versuch eines Kontos von dieser IP ist immer frei**) | nur Fensterablauf oder Verwaltung (kein Reset durch Erfolg) |
| Konto insgesamt | 20 Fehlversuche (4 × `SM_LOGIN_MAX_FAILURES`) seit letztem Erfolg | 15 Minuten | 30 s × 2^(Überschuss), Deckel 900 s | nur IP **ohne Erfolg dieses Kontos in den letzten 60 Tagen** (bekannte IP ausgenommen) | Erfolg des Kontos; Verwaltung |

Abnahme: Test pro Zähler mit den Schwellen (Schwelle − 1 → frei, Schwelle → Wartezeit); Test „Schulnetz“: 300 Konten hinter einer IP, davon 75 mit einmaligem Tippfehler → alle 300 melden sich nach erneutem Versuch an; Konto A von bekannter IP nach 20 Fehlversuchen anderer IPs → weiterhin nur durch den Paarzähler gebremst.

**SIC-092** · P0 · Status: Ist · **Wartezeit-Stufen**

| Fehlversuche im Fenster (Paar und Konto) | Wartezeit ab letztem Fehlversuch |
|---|---|
| 1 bis 4 | keine |
| 5 / 6 / 7 / 8 / 9 | 30 s / 60 s / 120 s / 240 s / 480 s |
| 10 und mehr | 900 s (Deckel) |

| Fehlversuche über der IP-Schwelle | Wartezeit |
|---|---|
| 0 bis 9 / 10 bis 19 / 20 bis 29 | 2 s / 4 s / 8 s |
| 30 bis 39 / 40 bis 49 / 50 und mehr | 16 s / 32 s / 60 s (Deckel) |

- Antwort bei Drosselung: 429 `too_many_attempts`, Kopf `Retry-After` in Sekunden, **vor** der Passwortprüfung (auch bei richtigem Passwort und in Schritt 2 der 2FA-Anmeldung).
Abnahme: Je Tabellenzeile ein Test mit erwarteter Wartezeit (± 1 s); richtiges Passwort während der Wartezeit → 429.

**SIC-093** · P0 · Status: offen (Ist: Zählregeln gebaut; offen: Fehlversuche im Audit, Spraying-Erkennung) · **Zählregeln und Erkennung**
- Zählt als Fehlversuch: falsches Passwort (auch bei unbekanntem Konto), deaktiviertes Konto nach richtigem Passwort, falscher oder bereits benutzter 2FA-Code, abgelaufenes Startpasswort, nicht erlaubter Anmeldeweg, falsches Passwort bei sensiblen Konto-Aktionen in der Sitzung (Passwort ändern, 2FA abschalten, E-Mail/Handy ändern oder entfernen). **Jeder Fehlversuch zählt unabhängig vom Ergebnis der Prüfung.** Zählt nicht: gedrosselte Anfragen, 2FA-Schritt 1 (Passwort richtig, Code fehlt).
- Ein Erfolg löscht Paar- und Kontozähler (auch Passwort-Reset), nicht den IP-Zähler. Passwort-Reset und Anbieter-Anmeldung sind nicht gedrosselt (eigene Limits, SIC-053).
- **Fehlversuche stehen im Audit** (`auth.login_failed`, mit gekürzter IP und Konto-Kennung, ohne Passwort) und speisen die Erkennung von Passwort-Spraying (viele Konten, wenige Versuche je Konto, gleiche Quelle) und den Alarm (DAT-032) [unklar: Schwellen].
Abnahme: Falscher TOTP-Code erhöht alle drei Zähler; 2FA-Schritt 1 ändert keinen Zähler; 50 Fehlversuche gegen 50 verschiedene Konten von einer IP erzeugen 50 Audit-Einträge und einen Alarm-Eintrag.

**SIC-094** · P0 · Status: Ist · **Sperren sichtbar und aufhebbar**
- Aktive Bremsen erscheinen auf der Seite „Sicherheit“ mit Restzeit; die Verwaltung hebt sie auf (Konto: `users.manage` und Rolle verwaltbar; IP: `login_policy.manage`; Audit `login_lock.clear`); CLI `unlock`. Aufbewahrung der Anmeldeversuche 30 Tage; „bekannte IP“ = Erfolg von dieser IP in den letzten 60 Tagen. Das Inhaber-Konto bleibt über „Passwort vergessen“ und Anbieter-Anmeldung erreichbar.
Abnahme: Verwaltung hebt die Bremse auf → nächster Versuch ohne Wartezeit und Audit-Eintrag `login_lock.clear`; `sekretariat` hebt die Bremse eines Lehrerkontos auf → 404.

**SIC-095** · P0 · Status: Ist (knotenübergreifend: offen) · **Allgemeines Rate-Limit**
- Token-Eimer im Speicher, gezählt je IP **und** je Konto (beide Eimer müssen frei sein): `SM_RATE_IP_PER_MIN` = 6000, `SM_RATE_ACCOUNT_PER_MIN` = 1200 (zugleich Burst), abschaltbar mit `SM_RATE_LIMIT=0` (nicht im Echtbetrieb). Gezählt werden `/api/` und `/ical/`; nie gebremst: Ereignisstrom, `/healthz`, `/metrics`, statische Dateien. Überschreitung: 429, `Retry-After`, Grund `rate_limited`. Speicherbegrenzung: höchstens 50 000 IP-Schlüssel und 20 000 Zugangsdaten-Zuordnungen; Schlüssel sind gekürzte Hashes, nie der Wert.
- Ergänzend am Reverse-Proxy: Anmeldung höchstens 10 je Minute und IP; Anfragekörper höchstens 50 MB. Im Mehrknoten-Betrieb gilt das Limit knotenübergreifend (SIC-120).
Abnahme: Mit auf 10 gesenkter Schwelle liefert die 11. Anfrage eines Kontos binnen einer Minute 429 mit `Retry-After`; `/healthz` bleibt erreichbar; ein zweites Konto derselben IP wird durch den IP-Eimer begrenzt, nicht durch den Konto-Eimer des ersten.

**SIC-096** · P0 · Status: Ist · **Ressourcen- und Zeitgrenzen**
- Browser: Anfragen brechen nach 30 Sekunden mit der Meldung „Der Server antwortet nicht rechtzeitig“ ab; Uploads, Sicherungen, Importe und Stundenplan-Generator 5 Minuten. Server: Generator `SM_GENERATE_TIME_LIMIT` = 30 s, Auto-Planer 15 s, Virenprüfung 30 s, SMS 10 s, Leak-Prüfung 3 s, Update-Download 600 s; Thread-Pool 40 (`SM_THREADPOOL`, min. 8), Datenbank-Pool 20 (`SM_DB_POOL_SIZE`, min. 5; größer als die Threads). Listen werden paginiert (Verlauf höchstens 1000 Einträge je Abruf).
Abnahme: Eine künstlich verzögerte Route (35 s) endet im Client mit der Meldung; Start mit `SM_THREADPOOL=4` → auf 8 angehoben; Listenabruf mit 5000 Einträgen liefert die erste Seite und einen Folgeverweis.

---

## 13 Ausgehende Verbindungen (SSRF-Schutz)

**SIC-097** · P0 · Status: Ist · **Zentrale Zielprüfung**
- Jede Verbindung, deren Ziel von Nutzereingaben oder Einstellungen abhängt, läuft durch **eine** zentrale Zielprüfung. Der Hostname wird bei **jeder** Verbindung neu aufgelöst; **alle** aufgelösten Adressen müssen öffentlich sein: nicht Loopback, nicht privat, nicht link-local, keine Metadaten-Adressen, kein CGNAT, kein Multicast, auch eigene Container-Namen nicht; IPv6 einschließlich eingebetteter IPv4. Verbunden wird mit der geprüften Adresse (kein DNS-Rebinding), TLS prüft weiterhin gegen den Namen.
- **Keine Weiterleitungen** folgen. Antwortinhalte stehen nie in Fehlermeldungen; Fehlermeldungen unterscheiden die Fehlerart nicht (einheitliche Meldung, kein Port-/Hosts-Orakel).
Abnahme: Test-Ziele `127.0.0.1`, `10.0.0.5`, `169.254.169.254`, `100.64.0.1`, `::1`, `::ffff:127.0.0.1` und ein Host, der erst öffentlich, dann privat auflöst → alle abgelehnt; ein Ziel mit HTTP-Weiterleitung auf ein internes Ziel → nicht gefolgt; Fehlermeldung enthält keinen Antworttext.

**SIC-098** · P0 · Status: Ist · **Erfasste Ziele und Ports**

| Ziel | Ports |
|---|---|
| Postfach-Server (IMAP; SMTP) | 993; 465, 587, 25 |
| OIDC-/Anbieter-Anmeldung (Discovery, JWKS, Token) | 443, 8443 |
| Webhooks, SMS-Webhook | die in der Adresse genannten (https) |
| Ferien-Dienst, Lizenzserver, Update-Verteilung, optionale Passwort-Leak-Prüfung | 443 |

- Ausnahme für schulinterne Ziele (z. B. eigener Mailserver, Anmeldedienst): `SM_OUTBOUND_ALLOW` (kommagetrennt: Hostname, IP oder Netz, optional mit Port); sie hebt **nur** die Adressprüfung auf, die Port-Regeln des Dienstes bleiben. Betreiber-Konfiguration ist keine Nutzereingabe und läuft nicht durch die Prüfung: der Betreiber-SMTP-Relay (`SM_SMTP_*`), die Datenbank, der Virenscanner (ClamAV); sie sind ausschließlich per Umgebung festgelegt, nie per Oberfläche änderbar.
- SMS-Anbieter: leer, `log`, `webhook`, `twilio`, `seven` (unbekannter Wert → Startabbruch; Webhook ohne http(s)-URL, Twilio ohne SID/Token/Absender, seven ohne Token → Startabbruch; Zeitlimit `SM_SMS_TIMEOUT` = 10 s).
Abnahme: Je Zeile ein Test mit erlaubtem und nicht erlaubtem Port; `SM_OUTBOUND_ALLOW=mail.schule.example` erlaubt den Host mit Port 993, nicht Port 22; ein per Oberfläche gesetzter SMTP-Zielwert wird nicht akzeptiert (Betreiberwert).

**SIC-099** · P0 · Status: Ist · **Postfach-Anbindung (IMAP/SMTP) und Mail-OAuth**
- Bekannte Anbieter (Google, GMX, Web.de, T-Online, Yahoo, Apple, Microsoft) haben **feste Server**; Host und Port aus dem Aufruf werden ignoriert. „Anderer Anbieter“ mit eigenem IMAP-/SMTP-Server verlangt das Recht `mail.custom_server` (Standard Administration, Schulleitung, Sekretariat; vergebbar an Personal, nie an Schüler/Eltern/Hausmeister/Monitor). Ratenlimit 10 Verbindungsversuche je Stunde und Konto; Zielprüfung bei Eintrag **und** bei jeder Verbindung; feste Ports; Zugangsdaten verschlüsselt (DAT-016); Abrufintervall `SM_MAIL_SYNC_MINUTES` = 5.
- Mail-OAuth (Google, Microsoft): Zustand an die Sitzung gebunden; Token-Antworten werden **mit Signaturprüfung** ausgewertet (Altsystem las Token-Claims ohne Signaturprüfung – Prüfpunkt offen); Tauschadressen laufen durch die Zielprüfung.
Abnahme: Schüler ruft Verbindung mit Eigenserver → 403; Aufruf mit Anbieter „Google“ und Host `intern.example` → Host ignoriert, feste Server verwendet; 11. Verbindungsversuch binnen einer Stunde → 429; Token mit ungültiger Signatur → abgelehnt.

---

## 14 Protokollierung und Audit (ohne Inhalte)

**DAT-019** · P0 · Status: Ist · **Jede schreibende Aktion wird protokolliert**
- Der Audit erfasst: Konto-ID und Benutzername (bei Systemaktionen leer bzw. „system“), Aktion im Schema `Bereich.Verb` (z. B. `auth.login`, `user.create`, `plan.change`), Ziel (höchstens 200 Zeichen, z. B. `user:<ID>`, `student:<ID>`), Details (JSON, nur was der Aufrufer übergibt), IP, bei API-Token die Token-ID und das Präfix, Zeitpunkt in UTC. Auch automatische Änderungen ohne angemeldeten Benutzer (Auto-Planer, Wartung) stehen im Protokoll („Verlauf & Audit“, rückgängig machbar).
Abnahme: Ein Test ruft **jede** schreibende Route auf und erwartet genau einen neuen Audit-Eintrag mit Aktion und Ziel; Routen ohne Eintrag lassen die CI scheitern, außer sie stehen in der geschlossenen Ausnahmeliste (DAT-031).

**DAT-020** · P0 · Status: Ist · **Keine Inhalte im Audit**
- Nie im Audit: Passwörter, Startpasswörter, Codes, Token-Werte (nur Hashes werden gespeichert), Telefonnummern, Gründe, Diagnosen, private Notizen, Anfragekörper, Abfrageparameter, Vorher/Nachher-Werte (Ausnahme: beobachtete Konten, Kap. 15, und Richtlinienänderungen `login_policy.set`/`.delete` mit Wert vorher/nachher). Löschgründe: nur Länge, der Grund selbst verschlüsselt (DAT-017). Anbieter-Änderungen nur mit Feldnamen. Beschriftung `student_absence.*`: ohne Gründe.
Abnahme: Nach Passwortwechsel, Kontakt-Änderung, Löschung mit Grund und Anbieter-Konfiguration enthält die Audit-Tabelle keine der eingegebenen Klartextwerte (Volltextsuche: 0 Treffer).

**DAT-021** · P0 · Status: offen (Ist: Teile der Liste; offen: markierte Zeilen) · **Pflicht-Audit-Ereignisse**

| Gruppe | Aktionen (Beispiele) | Stand |
|---|---|---|
| Anmeldung | `auth.login`, `auth.login_failed`, `auth.login_denied`, `auth.logout`, `auth.switch_account`, `auth.password_change`, `auth.password_reset_request/_verify/_reset`, `auth.2fa_disable`, 2FA-Einrichtung | Fehlversuche, 2FA-Einrichtung: offen |
| Konten | `user.create/update/delete`, `user.export`, `user.send_reset`, `user.contact_update`, `user.owner_protected`, `user.admin_grant_denied`, `user.watch_update` | Ist |
| Rechte/Rollen | `role.create/update/delete/hide/show`, `rights.update/reset/assign`, `branch.*`, `login_policy.set/delete` | Ist |
| Identitäten | `identity.link/unlink/reserve/admin_unlink`, `sso_provider.update` | Ist |
| Datenschutz | `privacy.leaver`, `.leaver_cancel`, `.settings`, `.run`, `.erase`, `.erase_failed`, `.export`, `.purged` | Ist |
| Dateien | `file.blocked`, `file.virus`, `file.download` (Fremdabruf), Datei-Upload und -Löschen | Upload/Löschen: offen |
| Exporte und Auskünfte | jeder Export aller Formate, jede Auskunft | offen |
| System | `system.backup`, Sicherungs-Download, Test-Wiederherstellung, Wartungslauf, Lizenzprüfung, Wiederherstellung | Ist |
| Kursräume | Ordner anlegen/umbenennen/verschieben/umsortieren, Pinnwand-Beiträge | Ist |
| Chats | Verwaltungsaktionen (Geräte, Mitglieder, Moderation, Löschen, Meldungen) mit Kennungen | Ist |
| Briefe und Nachrichten | `letters.download`, `letters.send`, `notification.unsubscribe`, `message.retention`, `message.unsuspend` | Ist |
| Beobachtung | `watch.detail`, `watch.export` | Ist |
| Übrige | iCal-Link erzeugen, Outbox-Wiederholung, zurückgezogener Antrag, Postfach-Einstellungen, Wartungsaktionen | offen |

Abnahme: Je Zeile ein Test, der die Aktion auslöst und den Audit-Eintrag mit Aktion/Ziel prüft; Zeilen mit „offen“ sind im Neubau Pflicht (Prüffund U-67, P1-04, P3).

**DAT-022** · P0 · Status: Ist · **Lesezugriffe auf besonders geschützte Daten**
- Jeder Zugriff auf Förderdaten und auf Atteste/Dokumente (Anlegen, Prüfen, Ablehnen, Lesen, Löschen/Archivieren) wird protokolliert, ohne Inhalt; Fremdabrufe von Dateien: SIC-081. [unklar: ob Lesezugriffe auf Krankmeldungs-Gründe und Notenbuch ebenfalls je Abruf protokolliert werden – Empfehlung der Rechtsrecherche: Lesen, Ändern, Exportieren, Löschen von Schülerdaten mit Wer/Wann/Was/Quelle-IP; Betreiber entscheidet Umfang.] Massenzugriffe lösen den Alarm DAT-032 aus.
Abnahme: Klassenleitung öffnet ein Attest → Audit-Eintrag (Konto, Ziel, Zeit, IP) ohne Inhalt; Förderdaten-Abruf → Eintrag.

**DAT-023** · P0 · Status: Ist · **Nur ergänzbare Fachprotokolle**
- **Meldeprotokoll Krankmeldung/Fehlzeit:** nur ergänzbar, nie editierbar oder löschbar, auch bei Rücknahme der Meldung; Felder: wer (Eltern, volljährige/r Schüler/in, Sekretariat, Klassenleitung, Lehrkraft, Schulleitung), wann, wie (online, telefonisch, schriftlich, Formular, Klassenbuch), was (Stunden, Art krank/fehlt/Beurlaubung, Änderung vorher/nachher); nie Gründe, Diagnosen, private Notizen. Sichtbarkeit: Klassenleitung, Sekretariat, Schulleitung die volle Historie; Fachlehrkräfte nur „abwesend gemeldet“ mit Zeit und Kanal, ohne Person, Status, Grund oder Dokumente; Schüler/innen, Eltern, technische Administration kein Zugriff.
- **Notenbuch-Änderungsprotokoll** (`gb_log`): jede Änderung; Halbjahresnoten sperrt die Lehrkraft, nur die Schulleitung öffnet, jede Änderung protokolliert. **Dokumente:** Versionen, nie überschrieben, „Löschen“ archiviert nur, Ablehnung mit Begründung.
Abnahme: Ein Versuch, einen Eintrag des Meldeprotokolls zu ändern oder zu löschen (Anwendung und Datenbankbenutzer der Anwendung), scheitert; Rücknahme der Meldung lässt den Eintrag bestehen; Fachlehrkraft sieht keine Person im Protokoll.

**DAT-024** · P0 · Status: Ist · **Datensparsame Protokolle und Anzeigen**
- Keine personenbezogenen Daten im Klartext in Logs. Fehlerprotokoll: Pfad ohne Abfrage, Kennungen maskiert. Anzeige von Zieladressen in Protokollen/Postausgang: E-Mail maskiert (erster Buchstabe, dann •••, Domain), Handynummer nur letzte Ziffern. Klartext von Mails/SMS wird nach Zustellung oder endgültigem Fehlschlag geleert; Fehlermeldungen des Postausgangs enthalten keine Empfänger. Zugriff auf Gesundheitsdaten: keine Gründe/Diagnosen/Notizen in Protokollen.
Abnahme: Nach Zustellung ist das Textfeld der Postausgangs-Zeile leer; ein Fehlerprotokoll-Eintrag zeigt keine Abfrage-Parameter und keine volle ID-Kennung.

**DAT-025** · P0 · Status: Ist · **Aufbewahrung der Protokolle**

| Protokoll | Frist | Bemerkung |
|---|---|---|
| Audit | 365 Tage (`audit_days`; `SM_AUDIT_RETENTION_DAYS` als Startwert; 1 bis 3650; **„0“ nicht zulässig**) | Löschung nach Erstellungszeit; Löschprotokoll-Eintrag „audit“ mit Anzahl |
| API-Protokoll | 90 Tage (Alter); 30 Tage nach Austritt | Zeit, Methode, Pfad ohne Abfrage/Token, Status, Dauer, IP |
| Beobachtungsprotokoll | 180 Tage; bei Kontolöschung sofort | Kap. 15 |
| Löschprotokoll | 1095 Tage | DAT-049 |
| Fehlerprotokoll | 30 Tage, höchstens 1000 Zeilen | DAT-056 |
| Anmeldeversuche | 30 Tage | |
| Zugriffsprotokoll des Servers | höchstens 14 Tage | DAT-026 |
| Download-Protokoll (Fremdabruf) | wie Audit (365 Tage) | im Altsystem ohne Ablauf |
| Test-Postausgang | 24 Stunden | nur Entwicklung |

Abnahme: Einträge mit Alter Frist + 1 Tag werden im nächsten Wartungslauf gelöscht; Einstellung `audit_days=0` wird abgelehnt (422).

**DAT-026** · P0 · Status: Ist (Zugriffsprotokoll gekürzt; IP-Frage: DAT-028) · **Zugriffsprotokoll des Servers**
- Client-IP gekürzt: IPv4 auf /24, IPv6 auf /48 (App und Proxy-Vorlage); Pfad ohne Abfrage; Request-ID; Format JSON in Produktion (`SM_LOG_FORMAT`), Stufe `SM_LOG_LEVEL`; `SM_ACCESS_LOG=0` schaltet es ab. Rotation: Container-Log 10 MB × 5, journald `MaxRetentionSec=14d`; höchstens 14 Tage.
Abnahme: Zugriffslog-Zeile für Client `203.0.113.77` enthält `203.0.113.0` (IPv4 /24) bzw. einen /48-Präfix für IPv6; keine Abfrageparameter; Log-Rotation begrenzt auf 5 Dateien à 10 MB.

**DAT-027** · P0 · Status: offen (Ist: Audit nur durch Anwendungslogik; Lücke: Datenbankrechte) · **Manipulationsschutz des Audits**
- Das Audit ist **nur anhängbar**: weder Anwendung noch Konten ändern oder löschen Einträge außer die Frist-Löschung und die Pseudonymisierung (DAT-052) der Wartung. Die Laufzeit nutzt einen Datenbank-Benutzer mit minimalen Rechten (kein DDL; Migrationen mit einem Besitzer-Benutzer nur im Update-Schritt, z. B. `SM_MIGRATE_DATABASE_URL`); auf der Audit-Tabelle nur Einfügen und Lesen (Löschen nur über die Wartungsrolle). Die Audit-Tabelle liegt getrennt von Fachdaten oder ist anders geschützt (Prüfliste: „append-only, getrennt“).
Abnahme: Mit dem Laufzeit-Datenbankbenutzer scheitern `UPDATE` und `DELETE` auf der Audit-Tabelle; DDL-Befehle scheitern; die Wartungsrolle löscht nur Einträge älter als die Frist.

**DAT-028** · P0 · Status: offen · **IP-Adresse in Audit, Anmeldeversuchen und Hinweisen**
- Der Ist-Zustand speichert in Anmeldeversuchen (30 Tage) und im Audit (365 Tage) die **volle** IP (Zweck: Sperre und Nachvollziehbarkeit), in der Beobachtung ebenfalls; die Hinweise an Eltern und Schüler/innen sagen „IP-Adresse wird gekürzt“ (Widerspruch). [unklar: Betreiber-Entscheidung: (a) IP im Audit nach kurzer Frist kürzen oder (b) volle Speicherung mit Zweck/Frist begründen und die Texte anpassen.] Jede Wahl ist in Datenschutzerklärung und Verzeichnis abzubilden (SIC-008).
Abnahme: Der Textvergleichstest (SIC-008) findet keine Aussage, die dem gewählten Verhalten widerspricht; ein Stichprobenlauf zeigt IPs im Audit gemäß Entscheidung.

**DAT-029** · P0 · Status: offen (Ist: Abruf mit Recht; Lücken: Zeitzone, Maskierung) · **Audit-Abruf**
- `GET /api/v1/audit?limit=&user=&action=&since=&until=` mit Recht `audit.read` (Administration, Schulleitung); Zeitfilter mit Zeitzonen-Offset werden nach UTC umgerechnet (Fund U-65); Ziele von Gesundheitsdaten für Leser ohne Gesundheitsrecht maskiert (SIC-025); Benutzername nach Kontolöschung pseudonymisiert. Auskunft an Betroffene: DAT-053.
Abnahme: Abruf mit `since=2026-10-17T00:00:00+02:00` liefert dieselben Einträge wie `…T22:00:00Z` des Vortags; `admin` sieht für `student_absence.*` keine Schüler-ID.

**DAT-030** · P0 · Status: Ist · **Keine Chat-Inhalte im Audit**
- Siehe SIC-087 (Chat-Audit ohne Nachrichten und Lesestand). Das Audit enthält nie Chiffrate, Schlüssel oder Dateiinhalte.
Abnahme: Audit-Scan nach einem Chat-Austausch enthält keine Nonce/Chiffrat-Werte.

**DAT-031** · P0 · Status: Ist (Betreiber-Zustimmung: offen) · **Geschlossene Liste der Audit-Ausnahmen**
- Ohne Audit dürfen **nur** bleiben: (1) Löschen eigener Benachrichtigungen, (2) Zwischenspeichern von Selbsttest-Antworten, (3) einzelne gesendete Chat-Nachrichten und „gelesen“-Markierungen. Jede weitere Ausnahme braucht einen dokumentierten Beschluss. [unklar: Zustimmung des Betreibers zu (1) und (2) (F12/F13) ist in den Quellen nicht eindeutig; Chat-Ausnahme (3) ist entschieden.]
Abnahme: Die Registry-Prüfung (DAT-019) kennt genau diese drei Ausnahmen; eine vierte Route ohne Audit lässt den Test scheitern.

**DAT-032** · P0 · Status: offen · **Alarm bei Massenzugriffen und Auffälligkeiten**
- Auslöser: viele Abfragen fremder IDs (404-Serien) eines Kontos in kurzer Zeit, Massenexport, Administrations-Anmeldung von neuer Adresse, Passwort-Spraying (SIC-093), viele Konten-Abfragen. Wirkung: Alarm-Eintrag im Audit und Benachrichtigung der Administration/Schulleitung. [unklar: Schwellen und Zeitfenster; im Neubau festlegen. Logging ohne Alarmierung hat laut OWASP geringen Nutzen.]
Abnahme: 100 Abfragen mit fremden Objekt-IDs durch ein Konto binnen einer Minute [Prüfwert] erzeugen einen Alarm-Eintrag und eine Benachrichtigung; normale Nutzung (20 Abfragen/Minute) bleibt ohne Alarm.

---

## 15 Verstärkte Beobachtung einzelner Konten

Anlass: Ein neu angelegtes Administrationskonto stufte das ursprüngliche Inhaber-Konto herab und legte ein weiteres Administrationskonto an. Der Betreiber will Betatestern Administrationszugang geben und „alle actionen extrem stark“ protokollieren: „damit er quasi jede Änderung erhält … alles, was er abruft“.

**DAT-033** · P0 · Status: Ist · **Setzen und Ändern**
- Nur wer `users.manage` **und** `watch.read` hat, setzt das Kennzeichen „Beobachtet“ (`PUT /users/{id}/watch`): ein/aus, optionales Ablaufdatum, Administrations-Vergabe-Sperre (SIC-024). Das eigene Konto und das Inhaber-Konto lassen sich nicht beobachten. Audit `user.watch_update` (ohne Inhalte). In der Kontenliste erscheint das Kennzeichen; im Konto-Dialog der Reiter „Beobachtung“.
Abnahme: Ein Konto ohne `watch.read` → 403/404; Beobachten des eigenen Kontos und des Inhaber-Kontos → abgelehnt; Setzen erzeugt `user.watch_update`.

**DAT-034** · P0 · Status: Ist · **Wirkung auf das beobachtete Konto**
- Das Konto verliert `watch.read` wirksam (auch als Administration); es sieht weder das Menü „Beobachtete Konten“ noch sein Kennzeichen (`GET /auth/me` enthält es nie); auf allen `/watch/*`- und `/users/{id}/watch`-Aufrufen antwortet es mit 404; es kann die Beobachtung nicht abschalten und das Protokoll weder lesen noch löschen. Für beobachtete Konten ist `no_admin_grant` standardmäßig an.
Abnahme: Als beobachtetes Administrationskonto: `GET /auth/me` ohne Beobachtungsfeld; `/watch/*` → 404; Abschalten der Beobachtung → 404; `no_admin_grant` ist an.

**DAT-035** · P0 · Status: Ist · **Umfang der Protokollierung**
- Für beobachtete Konten wird **jede** Anfrage protokolliert, auch reine Lesezugriffe: Zeit, Methode, Pfad mit Route-Muster, Abfrageparameter, HTTP-Status, Dauer, volle IP, Browserkennung, gekürzter HMAC des Sitzungs-Cookies (nie das Token). Bei schreibenden Anfragen zusätzlich der Anfragekörper und die währenddessen entstandenen Audit-Einträge (Vorher/Nachher-Werte, soweit der Fachcode sie liefert). Ereignisse: Anmeldungen, Fehlversuche (`auth.login_failed`), Kontowechsel, Abmeldungen, 2FA-Änderungen. Normale Konten werden nicht anders protokolliert. Schreiben gebündelt im Hintergrund (die Anfrage wird nicht langsamer). Chat-Sendungen enthalten nur Chiffrat [abgeleitet]; ob Chat-Anfragen erfasst werden, ist zu klären [unklar: Datenschutz].
Abnahme: Ein beobachtetes Testkonto ruft 5 Lese- und 2 Schreibrouten auf → 7 Protokollzeilen mit den genannten Feldern, bei den Schreibzeilen Körper und Änderungen; ein nicht beobachtetes Konto erzeugt keine Zeilen im Beobachtungsprotokoll.

**DAT-036** · P0 · Status: Ist · **Schwärzung, Verschlüsselung, Grenzen**
- Passwörter, Codes, Token, Schlüssel, Cookies, `Authorization`-Werte und Datei-Inhalte werden mit `***` ersetzt; Datei-Uploads nur als Vermerk. Abfrage, Körper und Änderungen liegen verschlüsselt (Bindung an Feld und Datensatz, DAT-002); Schlüsselwechsel über `rotate-keys`. Obergrenzen: Körper 32 000 Byte, Abfrage 2000 Zeichen, einzelne Textwerte 4000 Zeichen, Listen 200 Einträge, mit Kürzungsvermerk bei Überschreitung. Dies ist die einzige dokumentierte Ausnahme von „Audit ohne Inhalte“ (und gehört in TOMs und Hinweise für Beschäftigte).
Abnahme: Anfrage mit Feld `password` und Datei-Upload → Protokoll zeigt `***` und „Datei“; Körper mit 40 000 Byte wird bei 32 000 gekürzt mit Vermerk; Spalten sind `SM1`-Token.

**DAT-037** · P0 · Status: Ist · **Einsicht, Export und deren Audit**
- Ansicht `/beobachtete-konten` (Recht `watch.read`): Zeitleiste je Konto, Filter „nur Schreibzugriffe“, Zeitraum, Art; Detailansicht mit entschlüsseltem, geschwärztem Körper; CSV-Export (mit Zell-Entschärfung, SIC-069). Jeder Detailabruf `watch.detail`, jeder Export `watch.export` im Audit. [unklar: Betreiber nennt „Einsicht nur für den Inhaber“, die Umsetzung vergibt `watch.read` (Standard nur Administration, der Schulleitung zuweisbar); Entscheidung des Betreibers einholen.]
Abnahme: Detailabruf und Export erzeugen je einen Audit-Eintrag; Konto ohne `watch.read` → 404.

**DAT-038** · P0 · Status: Ist · **Aufbewahrung, Löschung, Auskunft**
- Aufbewahrung 180 Tage (Datenart `watch_log`, Alters-Frist); bei Kontolöschung verschwinden Kennzeichen und Protokoll sofort; 30 Tage nach Austritt. Das Protokoll ist **nicht** Teil der Selbstauskunft (sie würde die Beobachtung verraten); die Auskunft an die betroffene Person (Art. 15) erteilt der Betreiber organisatorisch über den CSV-Export.
Abnahme: Einträge älter als 180 Tage sind nach dem Wartungslauf weg; Kontolöschung entfernt Kennzeichen und Zeilen; die Selbstauskunft des beobachteten Kontos enthält keinen Beobachtungsabschnitt.

**DAT-039** · P0 · Status: offen · **Zweck, Rechtsgrundlage und Abstimmung vor Aktivierung**
- Vor dem ersten Beobachten eines Kontos sind Zweck, Rechtsgrundlage, Information der betroffenen Person, Speicherdauer und die Abstimmung mit Personalrat und Datenschutzbeauftragten zu dokumentieren (Beschäftigtendatenschutz; Prüffund P1-06/P1-07); die Hinweise für Lehrkräfte/Beschäftigte nennen die Beobachtung (im Altsystem fehlt sie dort, TOMs sagen „Audit ohne Inhalte“). Die Aktivierung verlangt einen Vermerk (Zweck und Grundlage, verschlüsselt gespeichert) [Vorschlag]. [unklar: Erkennbarkeit für die betroffene Person – im Altsystem bewusst nicht erkennbar; Festlegung nach Rechtsprüfung.]
Abnahme: Aktivieren ohne Vermerk → abgelehnt; die Hinweise für Beschäftigte enthalten den Abschnitt „Verstärkte Protokollierung“ (Dokumententest SIC-008).

---

## 16 Löschkonzept (technische Umsetzung)

Die Fristen sind Vorschläge der Software und keine Rechtsberatung; maßgeblich sind DSGVO, BDSG, Landesschulgesetz, Schuldatenverordnung und Aktenordnung des Landes. Sie sind mit der/dem Datenschutzbeauftragten abzugleichen und im Menü *Datenschutz* (Recht `privacy.manage`: Administration, Schulleitung) anzupassen.

**DAT-040** · P0 · Status: offen (Ist: Werte gebaut; Lücke: „0“ schaltet ab) · **Grundwerte und Einstellungen**

| Name | Standard | Bereich | Wirkung |
|---|---|---|---|
| `grace_days` (Wartelisten-Frist) | 30 Tage | 0 bis 3650 | Mindestfrist nach Austritt für **jede** Datenart; wirksame Frist = Maximum aus eigener Frist und `grace_days` |
| `auto_purge` | an | an/aus | Fristlöschung nach Austritt; „Fälliges jetzt löschen“ wirkt auch bei „aus“ (Neubau); bei „aus“ und überfälliger Löschung warnt die Statusseite |
| `audit_days` | 365 Tage | 1 bis 3650 | Audit-Frist (Startwert `SM_AUDIT_RETENTION_DAYS`) |
| `log_days` | 1095 Tage | 1 bis 3650 | Löschprotokoll und erledigte Wartelisten-Einträge |
| `<datenart>.days` | je Datenart | 1 bis 3650 | Frist nach Austritt (mindestens `grace_days`) |
| `<datenart>.age_days` | je Datenart | 1 bis 3650 | Alters-Frist unabhängig vom Austritt |
| `SM_STUDENT_DOCS_RETENTION_DAYS` | 400 | Tage | Startwert für `documents.age_days` und `forms.age_days` |
| `SM_MAINTENANCE_INTERVAL` | 3600 s | min. 5 | Abstand der Wartungsläufe; erster Lauf sofort nach dem Start |

- **Kein Konfigurationswert darf die Löschung abschalten**: der Altwert „0 = nie löschen“ entfällt (Prüffund P4: „0 schaltet die Löschung ab“). Die Obergrenze 3650 Tage gilt für alle Fristen.
- [unklar: Landesrecht. Das Backlog nennt für NRW (VO-DV I) Klassenbuch, Kursbuch, Zeugnislisten 10 Jahre, Schülerstammblatt 20 Jahre, übrige Daten 5 Jahre; die Voreinstellungen sind kürzer. Amtliche Zeugnisse und Notenlisten gehören in Schülerakte/Schulverwaltungsprogramm, nicht in diese Software. Die Schule/der Schulträger prüft die Fristen; sie sind je Land konfigurierbar. Rechtliche Prüfung nicht belegt.]
Abnahme: `audit_days=0` und `<art>.days=0` → 422; `grace_days=3651` → 422; Datenart mit eigener Frist 10 und `grace_days` 30 → wirksam 30; `auto_purge=aus` und fällige Person → Warnung auf der Statusseite, „Fälliges jetzt löschen“ löscht trotzdem.

**DAT-041** · P0 · Status: Ist · **Datenarten Gesundheit und Förderung** (Art. 9 DSGVO i. V. m. Landesschulgesetz/Schuldatenverordnung)

| Datenart (Schlüssel) | Frist nach Austritt | Alters-Frist (laufend) | Verfahren |
|---|---|---|---|
| Krankmeldungen und Fehlzeiten (`absences`) | 30 Tage | 365 Tage (`absences.age_days`): abgelaufen, wenn das Enddatum vor dem letzten 31. Juli liegt, der vor (heute − 365 Tage) liegt | hart löschen: Meldungen, Meldungsprotokoll, Nachschreibtermine; Blöcke zu 500 |
| Atteste und Dokumente (`documents`) | 30 Tage | 400 Tage ab Erstellung (`documents.age_days`; durch die Wartung) | löschen Datensatz **und** Datei, auch vom Konto der Person hochgeladene; höchstens 5000 Datensätze je Lauf |
| Förder- und Unterstützungsdaten (`support`) | 30 Tage | keine | löschen samt aller Dateien |
| Formular-Einreichungen (`forms`) | 90 Tage | 400 Tage, nur abgeschlossene Einreichungen | löschen samt Dateien und Verlauf; höchstens 5000 je Lauf |

Abnahme: Je Zeile: Person mit Austritt vor Frist + 1 Tag → Daten weg; Vorschau (DAT-049) zählt vor der Löschung dieselben Zahlen; ein Dokument von 401 Tagen Alter ist nach dem nächsten Wartungslauf samt Datei gelöscht (Dateisystem-Prüfung).

**DAT-042** · P0 · Status: Ist · **Datenarten Leistung**

| Datenart | Frist nach Austritt | Verfahren |
|---|---|---|
| Klausurergebnisse (`exam_results`) | 180 Tage | löschen |
| Notenbuch (`gradebook`: Einträge, Halbjahres-/Zeugnisnoten, Änderungsprotokoll, Quellergebnisse) | 180 Tage | löschen |
| Lernstand und Kompetenzen (`competencies`: Stufen, Lernpläne, Abzeichen) | 180 Tage | löschen |
| Klassenbuch-Anwesenheit (`attendance`) | 365 Tage | **anonymisieren**: nur der Eintrag der Person im Anwesenheitsfeld wird entfernt; Thema und Hausaufgabe bleiben; Protokollart „anonymisiert“ |

Abnahme: Wie DAT-041; nach der Anonymisierung ist die Person im Klassenbuch-Eintrag nicht mehr auffindbar, Thema und Hausaufgabe sind unverändert.

**DAT-043** · P0 · Status: Ist · **Datenarten Unterricht**

| Datenart | Frist nach Austritt | Verfahren |
|---|---|---|
| Abgaben und Rückmeldungen (`submissions`) | 90 Tage | löschen samt Abgabe-, Rückmeldungs- und Versionsdateien |
| Selbsttests, Abstimmungen, Umfragen (`learning`) | 90 Tage | löschen (Versuche, Stimmen, Teilnehmer, Antworten); anonym gespeicherte Umfrage-Antworten bleiben |
| Fortschritt und Kursraum-Nutzung (`progress`) | 90 Tage | löschen: Erledigt-Markierungen, Lesestände, Ansichten, Gruppenmitgliedschaften, Fristverlängerungen |
| Hochgeladene Dateien (`files`) | 30 Tage | hart löschen (Inhalt und Eintrag) aller Dateien, deren Eigentümer das Konto ist |

Abnahme: Wie DAT-041; Stichprobe: nach Abschluss existiert keine Datei mit Eigentümer der Person im Dateiverzeichnis.

**DAT-044** · P0 · Status: offen (Ist: Fristen; offen: laufende Chat-Frist) · **Datenarten Kommunikation**

| Datenart | Frist nach Austritt | Alters-Frist | Verfahren |
|---|---|---|---|
| Benachrichtigungen (`notifications`) | 30 Tage | Aufbewahrung 90 Tage (Einstellung 7 bis 730) | löschen Benachrichtigungen der Person und über die Person (z. B. an Eltern), Einstellungen |
| Postfach-Nachrichten (`messages`) | 30 Tage | `messaging_retention_days` 365 Tage | löschen eigene gesendete Nachrichten samt Anhängen, Entwürfe, Sperrlisten, Teilnahmen, Einstellungen; leere Unterhaltungen entfernt; Nachrichten anderer bleiben bis zu deren Frist |
| Chats Ende-zu-Ende (`chats`) | 30 Tage | **[unklar: keine laufende Frist im Altsystem]** | löschen Mitgliedschaften, Geräte, Schlüssel-Backup, Nachrichtenschlüssel, eigene Nachrichten und Anhänge, Meldungen samt Meldebildern; **Einzelchats ganz**; Gruppen ohne Mitglieder; Server kann Inhalte nicht lesen; Kopien auf anderen Geräten bleiben |

- Die Postfach-Aufbewahrung läuft als **eigene Wartungsstufe** (nicht als Nebenwirkung eines Zählerabrufs, Hinweis 2 des Altsystems).
Abnahme: Wie DAT-041; Nachricht mit Alter 366 Tage ist nach dem Wartungslauf gelöscht (außer offen gemeldete); ein Einzelchat der Person verschwindet vollständig.

**DAT-045** · P0 · Status: Ist · **Datenarten Konten und Verknüpfungen**

| Datenart | Frist nach Austritt | Verfahren |
|---|---|---|
| Eltern-Verknüpfungen und Freigaben (`parents`) | 30 Tage | löschen Verknüpfungen, Freigaben, Einstellungen; ein Eltern-/Begleitungs-Konto **ohne weiteres Kind** wird samt Daten und Konto gelöscht |
| Schüler-Konten (`accounts`) | 30 Tage, läuft **zuletzt** (erst wenn alle anderen Datenarten der Person erledigt sind) | Konto löschen; Sitzungen, API-Token, Anmeldeversuche, Verknüpfungen entfallen; Protokollbezüge pseudonymisiert (DAT-052); Administrationskonten werden nie vom Löschkonzept gelöscht |

Abnahme: Das Konto wird erst gelöscht, nachdem alle anderen Datenarten `erledigt` sind; ein Eltern-Konto mit einem zweiten Kind bleibt bestehen, nur die Verknüpfung zum ausgetretenen Kind entfällt.

**DAT-046** · P0 · Status: Ist · **Datenarten System und Protokolle**

| Datenart | Frist nach Austritt | Alters-Frist | Verfahren |
|---|---|---|---|
| Planverlauf und Protokoll-Bezüge (`history`) | 30 Tage | – | **anonymisieren**: Person aus **allen** gespeicherten Planversionen entfernt, Namen im Versionstext durch „[gelöscht]“ ersetzt, Protokollziele `student:<ID>` → `student:gelöscht`, Details entfernt; nur bei Schüler/innen |
| API-Protokoll (`api_log`) | 30 Tage (Zeilen der Token des Kontos) | 90 Tage unabhängig vom Konto | löschen |
| Beobachtungsprotokoll (`watch_log`) | 30 Tage; bei Kontolöschung sofort | 180 Tage | löschen Protokoll und Kennzeichen; **nicht** in der Selbstauskunft |

Abnahme: Nach der Anonymisierung findet eine Suche in allen Planversionen (Volltext, Namen und ID) die Person nicht mehr; Wer wieder im Planungsdokument steht, bleibt unberührt.

**DAT-047** · P0 · Status: Ist · **Weitere Löschregeln**

| Gegenstand | Frist | Verfahren |
|---|---|---|
| Audit-Protokoll | 365 Tage | Löschen; Löschprotokoll „audit“ mit Anzahl |
| Löschprotokoll, erledigte Wartelisten-Einträge | 1095 Tage (nach Abschluss) | löschen |
| Fehlerprotokoll | 30 Tage, höchstens 1000 Zeilen | älteste zuerst |
| Anmeldeversuche | 30 Tage | Wartung |
| Anmelde-Sitzungen | bis zum Ablauf | Wartung |
| Persönliche API-Token | sofort nach Ablauf | Wartung |
| API-Zugänge mit Umfang | 30 Tage nach Ablauf | Wartung (Nutzungsprotokoll bleibt solange einsehbar) |
| Dateien ohne Anhang | 24 Stunden | Wartung |
| Dateien im Löschzustand | 30 Tage | endgültig entfernt |
| Kursraum-Papierkorb | 30 Tage (Einstellung 1 bis 365) | endgültig entfernt; Wiederherstellen inkl. Fallback „(2)“ bei gleichnamigen Ordnern |
| Zugangsbrief-Stapel | 60 Minuten | gelöscht |
| Startpasswort-Frist | 14 Tage | nur Hash und Ablauf |
| Kontakt-Codes | Ablauf + 1 Stunde | Wartung; höchstens 5 Fehlversuche je Code |
| Test-Postausgang | 24 Stunden | Wartung |
| Doppelsende-Schlüssel | 24 Stunden | Wartung |
| Kontosperre während der Wartefrist | Austritt bis Abschluss/Rückkehr | Konto gesperrt, Sitzungen beendet |

Abnahme: Je Zeile ein Test mit Eintrag älter als die Frist → nach dem Wartungslauf weg; jüngerer Eintrag bleibt.

**DAT-048** · P0 · Status: offen · **Vollständigkeit des Datenart-Katalogs**
- Im Altsystem sind folgende Daten **nicht** als Datenart geführt (Löschung nur über Fremdschlüssel am Konto, nicht geprüft): Kursraum-Inhalte (`channel_items`, `channel_posts`, `channel_folders`), Lehrkraft-Profilanträge, Kontaktdaten und Anbieter-Verknüpfungen (`user_contacts`, `user_identities`), Import-Protokolle (`import_runs`), Planvorschläge und Planschnappschüsse, Mailkonten (`mail_accounts`), Ankündigungen (Verfasser wird nur pseudonymisiert), Abwesenheiten und Vertretungsentscheidungen von Lehrkräften (Verzeichnis-Vorlage: bis Ende des folgenden Schuljahres), Planversionen (nur über `SM_KEEP_VERSIONS` = 300), laufende Frist der Chats.
- Neubau: **jede** Tabelle mit Personenbezug ist über die Registry (SIC-005) einer Datenart mit Frist, Löschfunktion (mit Trockenlauf), Auskunftsfunktion und Betroffenen-Ermittlung zugeordnet. Grenze: Freitexte anderer Personen mit Namen (z. B. Mitteilungen, Vermerke) werden nicht automatisch durchsucht – dies ist in den TOMs genannt.
Abnahme: Der Registry-Test (SIC-005) listet alle Tabellen mit Personenbezug; jede hat eine Datenart; die genannten Lücken sind geschlossen oder mit Beschluss ausgenommen.

**DAT-049** · P0 · Status: Ist · **Warteliste „ausgetreten“, Fristlauf, Löschprotokoll**
- **Abgleich** (jeder Wartungslauf, auch bei `auto_purge` = aus): Jede bekannte Person (Schüler-Konten, Eltern-Verknüpfungen, Datenarten mit Personenkennung), die nicht mehr im Planungsdokument steht, kommt in die Warteliste (`wartend`, Zeitpunkt = jetzt); alle ihre Konten werden gesperrt, Sitzungen beendet. Der Name wird verschlüsselt gespeichert, die Klasse im Klartext. **Ein leeres Schülerverzeichnis wird nie als „alle ausgetreten“ gewertet.** Quelle `abgleich` (automatisch) oder `planung` (Sofort-Löschung).
- **Fristlauf** (`auto_purge` an): fällig, wenn jetzt ≥ Austritt + wirksame Frist. Reihenfolge nach Ordnungszahl: Gesundheit 10–13, Leistung 20–23, Unterricht 30–32, Kommunikation 40–43, Eltern 50, Planverlauf 800, API-Protokoll 810, Beobachtung 820, Schüler-Konten 900 (zuletzt). Fehler einer Datenart: bleibt offen, wird wiederholt, die übrigen laufen weiter, die Person wird nicht abgeschlossen, Fehlerprotokoll. Abschluss: Status `erledigt`, Name geleert, Löschprotokoll „abgeschlossen“, Audit `privacy.purged`.
- **Rückkehr** ins Planungsdokument während der Wartefrist: Eintrag entfernt, Konten entsperrt (auch manuell „Austritt zurücknehmen“: 409 wenn die Person nicht im Planungsdokument steht, 404 ohne offenen Austritt); Planverlauf bleibt unberührt. Erneuter Austritt nach Abschluss: Eintrag wird zurückgesetzt, die Löschung beginnt von vorn.
- **Löschprotokoll**: Datenart, Anzahl, Zeitpunkt, Modus (`automatik`, `frist`, `sofort`), Aktion (`geloescht`, `anonymisiert`, `abgeschlossen`), Anlass (höchstens 200 Zeichen), ausführendes Konto, Bezug (`student:<ID>`/`user:<ID>`) – **nie Inhalte**. **Vorschau** „Was würde gelöscht“ zählt je Person und Datenart, ohne etwas zu ändern (auch nicht fällige; die Summe „fällig“ zählt nur Fälliges). Schuljahreswechsel: Abgänger werden entfernt, Konten gesperrt, der nächste Lauf nimmt sie in die Warteliste auf.
Abnahme: Test mit leerem Schülerverzeichnis → 0 neue Wartelisten-Einträge; Person aus dem Dokument entfernt → Konto gesperrt, Sitzung 401; Fehler in einer Datenart (erzwungen) → Person bleibt `wartend`, nächster Lauf beendet sie; Rückkehr → Konto entsperrt; Löschprotokoll enthält keine Namen/Inhalte (Spaltenscan).

**DAT-050** · P0 · Status: Ist · **Sofort-Löschung auf Antrag (Art. 17)**
- Recht `privacy.subject` (nur Schulleitung; enthält Gesundheits- und Notendaten, daher nie die technische Administration). Erst Vorschau, dann Bestätigung durch **exaktes Eintippen** der Personen-ID bzw. des Benutzernamens (sonst 422). Ablauf: Warteliste-Eintrag anlegen/zurücksetzen (Quelle `planung`, Name verschlüsselt) und **vorher bestätigt schreiben**, damit ein Fehler wiederholbar bleibt; Person aus dem Planungsdokument entfernen (eigene Planversion); alle Datenarten sofort (Modus `sofort`), Planverlauf vor den Konten. Scheitert ein Schritt: Audit `privacy.erase_failed`, ein erneuter Aufruf führt zu Ende. Audit `privacy.erase` mit Länge des Grundes, verschlüsseltem Grund (höchstens 200 Zeichen), Anzahl erledigter Datenarten, IP. **Unwiderruflich**, kein Papierkorb.
- Ausgenommen: das eigene Konto und Administrationskonten (409) [unklar: wie Administrationskonten gelöscht werden]. Konto ohne Schülerbezug (Eltern, Personal): alle Datenarten außer Planverlauf, danach das Konto, Modus `sofort`; Eltern-Konto mit weiterem Kind: nur die Verknüpfung.
Abnahme: Löschung mit falscher Bestätigung → 422; mit `lehrer`-Konto → 404; erzwungener Fehler im vierten Schritt → `privacy.erase_failed`, zweiter Aufruf schließt ab; nach Abschluss: keine Zeile der Person in den Datenart-Tabellen (Registry-Prüfung), Audit nur mit Länge des Grundes.

**DAT-051** · P0 · Status: Ist (Wiederholung nach Restore: offen) · **Wiederherstellbarkeit und Sicherungen**
- Austritt: bis zum Abschluss rücknehmbar. Fristlöschung und Sofort-Löschung: **nicht** wiederherstellbar. Dateien (weich gelöscht): endgültig nach 30 Tagen. Kursraum-Papierkorb: 30 Tage (1 bis 365). Das Löschkonzept wirkt **nicht** auf Sicherungen: gelöschte Personendaten bleiben bis zur Rotation der Sicherungen erhalten (höchstens 12 Monate; Rotation 14 Tage / 8 Wochen / 12 Monate, SIC-112) und sind in der Datenschutzerklärung/TOMs so dokumentiert.
- **Nach einer Wiederherstellung** wird der Löschlauf erneut angewandt: Das Löschprotokoll (Personen-IDs, Modus, Zeit) dient als Nachweis, welche Personen seit dem Sicherungszeitpunkt gelöscht wurden; deren Daten werden erneut gelöscht, bevor die Instanz für Nutzer freigegeben wird [Vorschlag; Altsystem: manuelle Prüfung]. Das Ergebnis steht im Audit.
Abnahme: Test: Person löschen, ältere Sicherung zurückspielen, Wiederherstellungsprotokoll läuft → die Person ist nach dem Wiederherstellungs-Schritt wieder gelöscht, vor der Freigabe der Instanz.

**DAT-052** · P0 · Status: Ist · **Pseudonymisierung und Anonymisierung**

| Ort | Vorgang |
|---|---|
| Audit bei Kontolöschung | `user_id` leer; `username` → `gelöscht#<Konto-ID>`; ebenso alle Einträge mit demselben Benutzernamen |
| Planversionen (Verfasser), Mitteilungen (Verfasser), Krankmeldungen (Melder) | Verweis leer |
| Abwesenheitsereignisse (Akteur) | `actor_id` leer, `actor_name` → `gelöscht#<Konto-ID>` |
| Anmeldeversuche des Kontos | gelöscht |
| Schüler/innen im Planverlauf | aus allen Planversionen entfernt, „[gelöscht]“ |
| Protokollziele `student:<ID>` / `students:<ID>` | `student:gelöscht`, Details entfernt |
| Klassenbuch | Eintrag der Person entfernt, Thema/Hausaufgabe bleiben |
| Anonyme Umfrage-Antworten | bleiben (nicht zuordenbar) |
| Auskunft | von der Moderation ausgeblendete Texte als „[von der Moderation ausgeblendet]“; Bcc-Empfänger erscheinen nicht |
| Warteliste | Name nach Abschluss geleert, Personen-ID bleibt 1095 Tage |
| Erledigungs-Audit `privacy.erase` | bleibt mit Personen-ID und IP bis zur Audit-Frist (365 Tage); Grund nur verschlüsselt |

Abnahme: Nach Kontolöschung enthält keine Audit-Zeile den Benutzernamen (Volltextsuche: 0 Treffer, `gelöscht#<ID>` vorhanden); Namen in Ankündigungen, Abwesenheiten, Dokumenten und Kanalbeiträgen sind pseudonymisiert (Fund U-27: im Altsystem unvollständig).

---

## 17 Auskunft und Übertragbarkeit (Art. 15 und 20)

**DAT-053** · P0 · Status: Ist · **Wege, Rechte, Audit**

| Weg | Recht | Format | Audit |
|---|---|---|---|
| `GET /api/v1/me/export?format=json` | eigenes Konto | JSON (`meine-daten-<Benutzername>.json`) | `user.export` |
| `GET /api/v1/me/export?format=zip` | eigenes Konto | ZIP mit `daten.json` und `uebersicht.html` (Titel „Meine Daten – <Name>“) | `user.export` |
| `GET /api/v1/privacy/export?student_id=…` oder `?user_id=…` | `privacy.subject` | ZIP (`auskunft-<Benutzername>.zip`, Titel „Auskunft nach Art. 15 DSGVO – <Name>“) | `privacy.export` |
| `GET /api/v1/users/{id}/export` | `privacy.subject` | wie oben | `privacy.export` |

- Person ohne Konto: 404 mit Hinweis, die Auskunft manuell aus der Schülerakte zu erstellen [Lücke: Neubau soll auch für Personen ohne Konto eine Auskunft erzeugen können, Prüffund P4].
- Eltern erhalten die Daten ihrer Kinder nur für die Bereiche, die die Freigabe (`parent_access`) erlaubt; Förderdaten nur bei minderjährigen Kindern; volljährige Schüler/innen steuern die Zustellung selbst (Standard: die Person selbst). Das Beobachtungsprotokoll ist nicht Teil der Selbstauskunft (DAT-038).
- Eine Auskunft enthält **keine Daten Dritter** (Namen anderer Kinder in Nachrichten geschwärzt) und **keine Geheimnisse** (nur Metadaten: kein Token-Wert, kein Link-Token, kein 2FA-Geheimnis).
Abnahme: Fremdes Konto ruft `/privacy/export?user_id=…` → 404; Elternkonto eines volljährigen Kindes ohne Freigabe erhält den Bereich nicht; die Auskunft enthält keinen Wert aus Token-Spalten (Scan); Antwort auf Konto ohne Eintrag ist 404.

**DAT-054** · P0 · Status: offen (Ist: Abschnittsliste; Lücken: Obergrenzen, Schülerprotokolle) · **Inhalt der Auskunft**

| Abschnitt | Inhalt | Grenze im Altsystem |
|---|---|---|
| `exported_at`, `account`, `permissions`, `two_factor_enabled`, `ical_link_active` | Konto, wirksame Rechte, Wert ja/nein | – |
| `sessions` | Erstellung, letzte Aktivität, Ablauf, IP, Browserkennung | – |
| `api_tokens` / `api_token_log` | Name, Präfix, Zeiten, Umfang ja/nein / Protokoll | Protokoll höchstens 5000 |
| `login_attempts` / `audit_log` | Zeit, IP, Erfolg / Einträge des Kontos oder mit Ziel `user:<ID>` | 1000 / 5000 |
| `students`, `teacher`, `teacher_change_requests`, `contact`, `identities` | Stammdaten, Anträge (entschlüsselt), E-Mail/Telefon, Anbieter-Konten (ohne Geheimnisse) | – |
| `absences`, `student_documents`, `support`, `forms` | Fachdaten | Förderdaten nur minderjährig |
| `exam_results`, `gradebook_*`, `competency_*`, `register_attendance` | Noten, Notenbuch, Kompetenzen, Anwesenheit | Eltern nur mit Freigabe des Bereichs |
| `assignment_submissions`, `selftest_attempts`, `poll_participation`, `survey_participation`, `progress_*`, `channel_*` | Abgaben mit Versionen, Antworten (entschlüsselt; anonyme Umfragen nur „(anonym gespeichert)“), Fortschritt, Gruppen | – |
| `notifications`, `notification_settings`, `mailbox_conversations` | Benachrichtigungen, Einstellungen, Unterhaltungen (Text entschlüsselt, Anhangsnamen) | Benachrichtigungen höchstens 5000 |
| `chats`, `chat_devices`, `chat_key_backup_exists`, `chat_reports_filed` | Mitgliedschaften, Zeiten, eigene Nachrichten **verschlüsselt** (Hinweis: lesbar nur auf eigenen Geräten), Geräte, ob Backup existiert, eigene Meldungen | – |
| `files`, `parent_accounts`, `parent_access_settings`, `linked_children`, `announcements_authored` | Dateimetadaten und Namen, Eltern-Konten und Freigaben, verknüpfte Kinder, verfasste Mitteilungen | – |
| `hinweise` | Abschnitte, die nicht vollständig ausgelesen werden konnten (die Auskunft bricht bei Einzelfehlern nicht ab) | – |

- **Neubau:** keine stille Kürzung durch Obergrenzen (1000/5000/5000/5000): die Auskunft ist vollständig (seitenweise Erzeugung); Protokolleinträge zu Schüler/innen sind enthalten (Prüffund P4); jeder Abschnitt, der nicht gelesen werden konnte, steht in `hinweise`.
Abnahme: Testperson mit 6000 Benachrichtigungen und 2000 Anmeldeversuchen: die Auskunft enthält alle; ein erzwungener Fehler in einem Abschnitt erscheint in `hinweise`, die übrigen Abschnitte bleiben vollständig; jede Datenart der Registry (SIC-005) erscheint in der Auskunft.

---

## 18 Wartung, Fehlerprotokoll, Statusseite

**DAT-055** · P0 · Status: offen (Ist: Läufe gebaut; offen: Postfach als eigene Stufe, eindeutige Bedeutung von Intervall 0) · **Wartungsläufe**
- Hauptlauf alle `SM_MAINTENANCE_INTERVAL` Sekunden (Standard 3600, mindestens 5), erster Lauf sofort nach dem Start. Jede Stufe hat eigene Fehlerbehandlung; ein Fehler stoppt die übrigen nicht. Reihenfolge: Sitzungen, Token, Anmeldeversuche, Dateiablage, Dokumente, Formulare, Kontakt-Codes, Zugangsbriefe, Benachrichtigungen, Kursraum-Papierkorb, Fehlerprotokoll, Löschkonzept. Bei Mehrknoten-Betrieb nur auf dem Führungsknoten (`SM_HA`, SIC-122). Intervall **0 = aus** eindeutig für alle Stufen (Altsystem: Schleife lief trotzdem alle 5 Sekunden, Postfach-Notbehelf war aus).

| Job | Wirkung |
|---|---|
| Abgelaufene Sitzungen / persönliche Token (ohne Umfang) | sofort löschen |
| API-Zugänge mit Umfang | 30 Tage nach Ablauf löschen |
| Anmeldeversuche | älter als 30 Tage löschen |
| Dateiablage | Abgleich Platte/Datenbank höchstens alle 12 Stunden; Temp-Reste älter als 6 Stunden; Uploads ohne Anhang älter als 24 Stunden; weich gelöschte älter als 30 Tage endgültig |
| Schüler-Dokumente / Formular-Aufbewahrung | Alters-Fristen (DAT-041), höchstens 5000 je Lauf |
| Formular-Erinnerungen | an Prüfende bei offenen Einreichungen (Erinnerungsfrist der Vorlage) |
| Kontakt-Codes / Zugangsbrief-Stapel / Test-Postausgang | 1 Stunde nach Ablauf / nach Ablauf (Standard 60 min) / älter als 24 Stunden |
| Benachrichtigungen | Erinnerungen, zurückgestellte Mails nach Ruhezeit, Tageszusammenfassung einmal täglich ab 7:00 Uhr Ortszeit, Aufräumen älter als Aufbewahrung (90 Tage, 7 bis 730) |
| Kursraum-Papierkorb | älter als `trash_retention_days` (30) endgültig |
| Postfach-Aufbewahrung (**eigene Stufe**) | Nachrichten älter als `messaging_retention_days` (365), außer offen gemeldete; danach leere Unterhaltungen, Entwürfe, abgeschlossene Meldungen älter als die Frist; Ende abgelaufener Postfach-Sperren |
| Fehlerprotokoll | älter als 30 Tage und alles über 1000 Zeilen; Vermerk im Zustandsspeicher |
| Löschkonzept | Abgleich, Fristen, Alters-Fristen, Audit, Löschprotokoll (DAT-049) |
| Automatische Sicherung | alle `SM_AUTO_BACKUP_HOURS` (Standard 0 = aus), Rotation `SM_BACKUP_KEEP` = 30 |

Abnahme: Je Job ein Test mit Eintrag knapp über/unter der Frist; Stufe 4 wirft einen erzwungenen Fehler → Stufen 5 bis 12 laufen trotzdem; `SM_MAINTENANCE_INTERVAL=0` → keine Läufe (kein Dauerlauf).

**DAT-056** · P0 · Status: Ist · **Fehlerprotokoll**
- Gespeichert werden nur die Stufen ERROR und CRITICAL; Aufbewahrung 30 Tage, höchstens 1000 Zeilen (älteste zuerst); Meldung höchstens 2000 Zeichen; Stacktrace höchstens 8000 Zeichen (Ende der Ausgabe); Request-ID; Anfragepfad ohne Abfrage, Kennungen maskiert; Schreiben asynchron über eine Warteschlange (500 Einträge) mit Hintergrund-Schreiber, blockiert nie die auslösende Anfrage, eigene Protokollierung wird nicht zurückgekoppelt. Keine Verschlüsselung (Längen begrenzt, keine Inhalte).
Abnahme: 1100 erzwungene Fehler → nach dem Wartungslauf 1000 Zeilen; Eintrag mit 3000-Zeichen-Meldung wird auf 2000 gekürzt; Fehler während eines Requests verzögert die Antwort nicht (> 100 ms Mehrlaufzeit ausgeschlossen [Prüfwert]).

**DAT-057** · P0 · Status: Ist · **Statusseite (Sicherheits- und Betriebsprüfungen)**

| Prüfung | Schwelle | Ergebnis |
|---|---|---|
| Speicherplatz frei | ≥ 15 % ok; 5 bis 15 % Warnung; < 5 % Fehler | |
| Sicherung (Alter der letzten) | ≤ 48 Stunden ok, sonst Warnung; keine Sicherung: Warnung in Produktion | |
| Fehlerprotokoll | 0 Fehler in 24 Stunden | sonst Warnung |
| E-Mail | nicht eingerichtet, Test-Postausgang aktiv oder nicht zustellbare Mails | Warnung |
| Verschlüsselung | Schlüssel aus Konfiguration ok; abgeleiteter Entwicklungsschlüssel Warnung | |
| Zwei-Faktor | Produktion und Pflicht für Administration/Schulleitung nicht erzwungen (`SM_REQUIRE_2FA_ROLES` bzw. Schuleinstellung) | Warnung |
| Administration | kein aktives Administrator-Konto | **Fehler** |
| HTTPS | Adresse `https` und sicheres Cookie ok; sonst | Warnung |
| Wartungslauf | letzter Lauf vorhanden | sonst Warnung |
| Lizenz, Impressum, Datenschutztexte, Datenbankstand | laut Status / Hinweis auf Migration | |
| Löschfristen | überfällige Löschungen bei `auto_purge` = aus | Warnung (Neubau) |
| Start-Warnungen (SIC-103) | Proxy-Vertrauen aus, keine automatische Sicherung u. a. | Warnung |

- Der Zustandsspeicher (Schlüssel `setup`, `school_profile`, `yearchange`, `maintenance`) enthält keine Freitexte über Personen. Die Statusseite zeigt nie Schlüsselmaterial (nur Kennung und Fingerabdruck, DAT-007).
Abnahme: Je Zeile ein Test mit Schwellenwert (z. B. 4,9 % frei → Fehler; letzte Sicherung 49 Stunden alt → Warnung); Instanz ohne Administrator → Fehler.

---

## 19 Geheimnisse, Konfiguration, Start mit Pflichtprüfung

**SIC-100** · P0 · Status: offen (Ist: Modi gebaut; Lücke: Standard „development“, abgeleiteter Modus) · **Betriebsmodi**

| Modus | Wirkung |
|---|---|
| `production` | Demo-Funktionen aus; Pflicht-Secrets werden beim Start geprüft; Lizenz-Durchsetzung immer an; API-Doku aus; Cookie-Secure Pflicht; Test-Postausgang und Test-Anmeldedienst verboten |
| `demo` | `SM_DEMO_PUBLIC` Standard 1; Demo-Konten und Systemfunktionen geschützt; Instanz wird regelmäßig neu aufgesetzt (03:30); niemals mit Echtdaten |
| `development` | Test-Postausgang an, wenn Basis-Adresse lokal; SSO-Testanbieter erlaubt; Entwicklungs-Erst-Admin; **nie auf öffentlich erreichbaren Instanzen** |

- `SM_MODE` ∈ {`production`, `demo`, `development`}, `SM_ENV` ∈ {`development`, `production`}; widersprüchliche Angaben (z. B. `SM_MODE=production` bei `SM_ENV≠production`) → Startabbruch. **Neubau:** `SM_MODE` ist Pflicht; ohne Angabe startet der Server nicht (Altsystem: Standard `development`, „abgeleiteter“ Modus mit nur Warnungen – Risiko Entwicklungs-Zugang auf Live-Instanzen, Prüffund P3-05/06/07). Live-Schulen und Test-Instanzen, die eine Kundenschule nachstellen, laufen im Produktivmodus.
Abnahme: Start ohne `SM_MODE` → Abbruch mit Meldung; Start `SM_MODE=production` und `SM_ENV=development` → Abbruch; in `production` sind Test-Postausgang, Test-Anmeldedienst, Demo-Laden verweigert.

**SIC-101** · P0 · Status: Ist · **Start-Pflichtprüfungen im Produktivmodus (hart: Startabbruch)**

| Prüfung | Bedingung → Abbruch |
|---|---|
| Geheimschlüssel | `SM_SECRET_KEY` leer, kürzer als 32 Zeichen, beginnt mit `BITTE_AENDERN` oder enthält `CHANGE_ME` |
| Verschlüsselung | `SM_ENCRYPTION_KEYS` leer oder fehlerhaft (DAT-007) |
| Adresse | `SM_BASE_URL` fehlt oder nicht `https` (außer lokal) |
| Cookie | `SM_COOKIE_SECURE=0` |
| Entwicklungsschalter | `SM_DEV_OUTBOX=1`; `SM_SSO_DEV_MOCK=1` (außerhalb `development`, in Demo und öffentlicher Demo); `SM_LOAD_DEMO=1`; `SM_DEMO_PUBLIC=1` |
| Erst-Admin | `SM_ADMIN_PASSWORD` gleich einem der 8 bekannten Entwicklungs-Passwörter oder Platzhalter, oder Regelverstoß (SIC-046) |
| Passwort-Hash | `SM_SCRYPT_N` keine Zweierpotenz, kleiner 2 oder (Produktion) kleiner 16384 |
| Lizenz | Durchsetzung nicht abschaltbar (`SM_LICENSE_ENFORCE` immer 1; Lizenzserver-Adresse und Prüfschlüssel fest) |
| Betriebsmodus | SIC-100 |

- Im Altsystem galten einzelne Prüfungen (Basisadresse, Cookie, Admin-Passwort, Demo) nur im „ausdrücklichen“ Produktivmodus; im Neubau gelten **alle** hart.
Abnahme: Je Zeile ein Startversuch mit der Verletzung → Prozess endet mit Fehlermeldung, die die Variable nennt (nicht den Wert); ein Start mit allen gültigen Werten gelingt.

**SIC-102** · P0 · Status: Ist · **Wertebereichs- und Syntaxprüfung der Konfiguration**
- Zahlenvariable nicht lesbar → Startabbruch mit Variablennamen. `SM_AUTH_CODE_MINUTES` 1 bis 1440; `SM_LETTER_BATCH_MINUTES` 1 bis 1440; `SM_UPLOAD_MAX_MB` größer 0 bis 10240; Kontingente (Datei, Chat) ≥ 0; Upload-Rate ≥ 0; `SM_CLAMAV_PORT` 1 bis 65535; `SM_CLAMAV_TIMEOUT` > 0; `SM_CLAMAV_REQUIRED` ohne Host; `SM_SMS_PROVIDER` ∈ {leer, `log`, `webhook`, `twilio`, `seven`}; SMS-Webhook ohne http(s)-Adresse; `twilio` ohne SID/Token/Absender; `seven` ohne Token; `SM_SMS_TIMEOUT` > 0; `SM_DEMO_CLASSES_PER_GRADE` 1 bis 23.
Abnahme: Je Variable ein Startversuch mit Wert außerhalb des Bereichs → Abbruch.

**SIC-103** · P0 · Status: Ist · **Start-Warnungen (auf Statusseite sichtbar)**
- Warnungen, die den Start nicht verhindern, aber im Log und auf der Statusseite (DAT-057) stehen: SQLite ab etwa 500 Konten (PostgreSQL empfohlen); kein E-Mail-Versand (`SM_SMTP_HOST`/`SM_SMTP_FROM` fehlt: Passwort-Zurücksetzen per E-Mail und Briefe per E-Mail funktionieren nicht); `SM_REQUIRE_2FA_ROLES` leer (Empfehlung `admin`, `schulleitung`, `sekretariat`); `SM_AUTO_BACKUP_HOURS` = 0; `SM_TRUST_PROXY` nicht gesetzt (hinter Proxy sieht die Drosselung nur die Proxy-Adresse); `SM_SMS_PROVIDER=log` in Produktion; Test-Postausgang parallel zu SMTP/SMS; Entwicklungsschlüssel `dev` statt Ring; fehlende Impressums-/Datenschutztexte. Hinweis: Eine fehlende Sicherung ist im Neubau in Produktion eine **Warnung der Statusseite** mit Pflichtbehandlung, nicht stumm.
Abnahme: Je Bedingung ein Start → Warnung im Log und als Zeile auf der Statusseite.

**SIC-104** · P0 · Status: offen (Ist: Test-Postausgang nur lokal; Lücke: Standardwert im Code) · **Entwicklungs- und Test-Schalter**
- Test-Postausgang (`SM_DEV_OUTBOX`): Standard **aus**; nur wenn Basis-Adresse lokal (`localhost`), nur für Administration/lokalen Zugriff; Nachrichten werden nie zugestellt, nur angezeigt; auf öffentlich erreichbaren Instanzen antwortet der Endpunkt 404; „Passwort vergessen“-Codes landen nie auf einer öffentlichen Testseite. Anhang-Download mit `nosniff`, Sandbox, `no-store`; Anzeige letzte 50 Nachrichten, Aufbewahrung 24 Stunden.
- Entwicklungs-Passwörter, Ersatz-Schlüssel und unsichere Verbindungen im Update-Dienst sind nur im Entwicklungsmodus; Entwicklungs-Skripte, Vorschau-Passwörter, persönliche Pfade und Beispielnamen gehören nicht ins Auslieferungs-Image (SIC-111).
Abnahme: Öffentlich erreichbare Instanz (nicht lokal): `GET /dev-outbox` → 404; Start in `development` ohne Variable: Test-Postausgang aus, wenn Basis-Adresse nicht lokal.

**SIC-105** · P0 · Status: Ist · **Konfigurationsdateien und Geheimnis-Handhabung**
- Konfiguration nur über `SM_*`-Umgebungsvariablen und Geheimnisse nur aus Umgebung/Secret-Store; `.env` Rechte 600, Besitzer root, nie im Repository oder Image; `.env.example` nur mit Platzhaltern und ohne Kommentare hinter Werten (Datei dient als systemd-`EnvironmentFile`); jede dokumentierte `SM_*`-Variable kommt im Container an (Test über die Compose-Vorlage); Installationsskript erzeugt `.env` mit Zufallsgeheimnissen (Pflichtwerte `SM_DOMAIN`, `ACME_EMAIL`, `SM_SECRET_KEY`, `POSTGRES_PASSWORD`; dringend `BACKUP_GPG_PASSPHRASE`; Schlüsselring Pflicht).
- Keine Schlüssel/Zugangsdaten im Frontend; Quellen, Tests und Source Maps nicht im Image.
Abnahme: Test vergleicht die Variablenliste der Dokumentation mit dem Compose-Environment (Differenz = 0); `.env` im Image-Scan: 0 Treffer; `.env.example` enthält kein `#` hinter einem Wert.

**SIC-106** · P0 · Status: Ist · **Geheimnisse und ihre Rotation**

| Geheimnis | Ablage | Rotation / Wirkung |
|---|---|---|
| `SM_SECRET_KEY` | `.env` | Wechsel meldet alle Sitzungen ab, API-Token ungültig |
| `SM_ENCRYPTION_KEYS` | `.env` und Tresor, getrennt von Sicherungen | Rotation ohne Ausfall; Verlust unwiederbringlich |
| `POSTGRES_PASSWORD` | `.env` | `ALTER USER`, `.env` anpassen, Neustart |
| `BACKUP_GPG_PASSPHRASE` | `.env` und Tresor | neue Sicherungen mit neuer Passphrase; alte Passphrase für ältere Sicherungen aufbewahren, bis diese rotiert sind |
| `SM_WEBHOOK_SECRET` | `.env` | Empfänger informieren |
| SMTP-, S3-, OIDC-, Anbieter-Zugangsdaten | `.env` | beim Anbieter neu erzeugen |
| Administrations-Passwörter und 2FA | Konto | regelmäßig prüfen; bei Personalwechsel sofort deaktivieren |

Abnahme: Jeder Eintrag hat im Betriebshandbuch einen Rotationsschritt und im Test (Wegwerf-Instanz) eine erfolgreiche Rotation ohne Datenverlust (außer dem dokumentierten Sitzungsverlust).

---

## 20 Lieferkette und Abhängigkeiten

**SIC-107** · P0 · Status: Ist (Deklaration direkter Pakete: offen) · **Gesperrte Abhängigkeiten**
- Python: Sperrdateien mit Hashes für Laufzeit und Entwicklung (`make lock`); Docker-Build und CI installieren **nur** daraus mit Hash-Prüfung (ohne Sperrdatei schlägt der Build fehl); keine Auswahl „neueste passende Version“ zur Bauzeit. Frontend: `package-lock.json` gepinnt, Installation mit `npm ci`. Alle direkt genutzten Pakete stehen in der Projektdatei (im Altsystem fehlten `pydantic`, `starlette`, `anyio`). Große Versionssprünge (z. B. TypeScript 5→7, Vite 7→8, Vitest 4→5, Node 22→25) nur getrennt und mit Tests. Frontend-Bibliotheken für Verschlüsselung/Formelsatz mit fester Version.
Abnahme: Build ohne Sperrdatei bricht ab; Hash-Abweichung eines Pakets bricht ab; ein Prüfwerkzeug (deptry/Äquivalent) findet 0 direkt genutzte, nicht deklarierte Pakete.

**SIC-108** · P0 · Status: offen (Ist: pip-audit, npm audit, CodeQL, Dependabot; offen: Container-Scan) · **Laufende Prüfung der Lieferkette**
- CI-Jobs: Abhängigkeits-Audit (`pip-audit` mit Hashes, `npm audit --omit=dev`; lokal `make audit`), CodeQL, Dependabot für Aktualisierungen, **Container-Scan (z. B. trivy) im Release-Workflow**, Prüfung auf tote Abhängigkeiten (knip/vulture als nicht blockierende Stufe), Syntaxprüfung der geänderten Dateien vor jedem Deploy. Stand Altsystem: 0 bekannte Schwachstellen in beiden Sperrdateien. Monatlicher Patchtag (Betriebssystem, Container, Anwendung), Sicherheitsupdates sofort; Images regelmäßig neu bauen (`docker compose build --pull`).
Abnahme: Die CI-Pipeline enthält die genannten Jobs; ein absichtlich eingefügtes Paket mit bekannter Schwachstelle lässt den Audit-Job scheitern.

**SIC-109** · P0 · Status: offen · **Geheimnisse im Quellbestand und Weitergabe von Code**
- Das Repository (alle Zweige, auch Cloud-Zweige) wird auf echte Schlüssel durchsucht (Altsystem: nur 108 lokale Commits geprüft); ein Secret-Scan läuft in der CI. Kein Quellcode, keine Schlüssel und keine Demo-Anmeldedaten an kostenlose Fremddienste (nur CSS-Dateien dürfen hinaus). Interne Dokumente (Sicherheitsberichte, Konkurrenzrecherchen, Namensprüfung) liegen außerhalb des Repositories und nie im Kunden-Image.
Abnahme: Secret-Scan über alle Zweige: 0 Treffer; das Repository enthält keine Datei aus der Liste der internen Dokumente.

**SIC-110** · P0 · Status: offen · **Herkunft der Release-Artefakte**
- Releases entstehen in einer signierten Release-Pipeline bzw. mit eigenen CI-Images (Build-Provenienz); die ausgelieferten Images und Update-Manifeste sind signiert (SIC-124). Bauumgebung ohne Zugriff auf Produktivgeheimnisse.
Abnahme: Ein Release ohne gültige Signatur wird vom Update-Dienst abgelehnt (SIC-124); das Build-Protokoll nennt Quelle (Commit), Sperrdateien-Hash und Image-Digest.

**SIC-111** · P0 · Status: Ist · **Inhalt des Auslieferungs-Images**
- Enthalten: Anwendungscode mit Migrationen, gebautes Frontend, Handbuch je Rolle, Betreiber-Paket (Installation, Betrieb, Sicherheit, Updates, Schule einrichten, Datenschutz-Vorlagen; nur für Zuständige verlinkt), notwendige Skripte/Deploy-Vorlagen. Nicht enthalten: Tests, interne Dokumente, Lizenzserver (nur beim Anbieter, eigene Ausschlussliste: Schlüssel und Datenbank nie im Image), Entwicklungs- und Vorschau-Skripte mit Standardpasswörtern, Entwicklungs-Updater, Quellen/Source Maps, `.env`, Datenbanken, Sicherungen, persönliche Links/Domains, große Beispieldaten. Build-Kontext per Whitelist (`.dockerignore`, ohne tote Einträge).
- Keine Betreiber-Daten (Heimserver, Domain, Personen) in Kundentexten; Platzhalter `example.org`/`schule.example.org`; ein Test prüft dies bei jedem Lauf. Die Anbieter-Domain steht nur an einer Stelle und ist per Umgebung überschreibbar.
Abnahme: Image-Inhaltsliste enthält keinen Pfad aus der „Nicht enthalten“-Liste; Textscan der Kunden-Doku findet keinen Betreiber-Eigennamen/keine echte Domain (0 Treffer).

---

## 21 Backups und Wiederherstellung

**SIC-112** · P0 · Status: Ist · **Sicherung: Umfang, Zeitplan, Rotation**
- Der Sicherungsdienst (eigener Container bzw. systemd-Timer) erzeugt täglich zu `BACKUP_TIMES` (Standard 02:30, mehrere Zeiten möglich) und beim Start: Datenbank (PostgreSQL-Dump bzw. SQLite-Online-Sicherung mit Integritätsprüfung) und Datei-Archiv (Datenverzeichnis ohne Datenbankdateien, ohne App-Sicherungen, ohne das Zielverzeichnis der Sicherung; vom selben Zeitpunkt), je Datei eine `.sha256`-Prüfsumme. Rotation: `daily` 14 Tage, `weekly` 8 Wochen (erstes Backup je ISO-Woche), `monthly` 12 Monate (erstes je Monat), `manual` (vor Updates und Restores) die letzten 10; Wochen-/Monatsstände sind Hardlinks.
- App-eigene Sicherung (Administration → System): JSON (PostgreSQL) bzw. SQLite-Datei, Ablage `SM_BACKUP_DIR`, Rotation `SM_BACKUP_KEEP` = 30, Automatik `SM_AUTO_BACKUP_HOURS` (Standard 0 = aus), nur Datenbank, dient dem Herunterladen und ersetzt nicht den Sicherungsdienst. Namensmuster `schulmanager-JJJJMMTT-HHMMSS.db` bzw. `.json.gz`; **nur** dieses Muster ist listbar/abrufbar (kein Pfadzugriff). Dateirechte 0600, `umask 077`. Herunterladen, Prüfen und Anlegen im Audit.
Abnahme: Nach 20 Tagen mit täglicher Sicherung existieren 14 daily-, 2–3 weekly-Stände; Datei mit Name `../etc/passwd` → 404; Dateirechte der Sicherungen 0600.

**SIC-113** · P0 · Status: Ist (Offsite-Nachweis: Betreiber) · **Verschlüsselung und Offsite-Kopie**
- Alle Sicherungsdateien GPG-verschlüsselt (AES-256, `BACKUP_GPG_PASSPHRASE`, Endung `.gpg`); ohne Passphrase kein Restore. Inhalte (Nachrichten, Dateien, Atteste) liegen zusätzlich nur als Token vor (Kap. 7). Das Schlüsselmaterial (`SM_ENCRYPTION_KEYS`, Passphrase) liegt **nicht** in den Sicherungen (DAT-010).
- Offsite (3-2-1-Regel): `BACKUP_RCLONE_REMOTE` (S3, SFTP, WebDAV/Nextcloud), nach jeder Sicherung gespiegelt; `BACKUP_RCLONE_MODE=copy` löscht am Ziel nie; Anbieter in DE/EU mit AV-Vertrag, Versionierung oder Object Lock am Bucket (Schutz vor Ransomware), eigener Zugang mit Schreibrecht nur auf diesen Bucket; der Speicheranbieter sieht nie Klartext.
Abnahme: Eine Sicherungsdatei lässt sich ohne Passphrase nicht öffnen (Test); die Offsite-Kopie ist nach einer Sicherung innerhalb von 15 Minuten vorhanden [Prüfwert]; ein Löschversuch mit dem Schreibzugang am Ziel scheitert (Object Lock/copy-Modus).

**SIC-114** · P0 · Status: offen (Ist: Healthcheck; offen: Alarm per E-Mail, Offsite auf der Statusseite) · **Überwachung der Sicherung**
- Der Sicherungsdienst meldet „unhealthy“, wenn die letzte erfolgreiche Sicherung älter ist als `BACKUP_MAX_AGE_HOURS` (26 Stunden); optional Ping `BACKUP_PING_URL` (Erfolg) und `BACKUP_PING_URL_FAIL`. Statusseite: Warnung bei letzter Sicherung älter als 48 Stunden (DAT-057). Neubau: Alarm per E-Mail bei fehlender Sicherung oder Fehlerhäufung und Anzeige der Offsite-Sicherung auf der Statusseite.
Abnahme: Sicherungsdienst 27 Stunden ohne Erfolg → Status „unhealthy“ und E-Mail-Alarm; Statusseite zeigt den Zeitpunkt der letzten Offsite-Kopie.

**SIC-115** · P0 · Status: Ist · **Wiederherstellung**
- **Nur per Konsolenbefehl** (bewusst keine Wiederherstellung per Klick in der Oberfläche; Oberfläche: Herunterladen und „Prüfen“). Der Restore ist eine einzige Transaktion (Abbruch lässt die Datenbank unverändert), die Anwendung wird dabei gestoppt, vorher entsteht eine Sicherheitssicherung (`manual`). Benötigt werden Datenbank-Sicherung, Datei-Archiv **vom selben Zeitpunkt** und der Verschlüsselungsschlüssel; fehlt der Schlüssel, bricht der Restore mit klarer Meldung ab. Wiederherstellung auf einem neuen Server: dieselbe `.env` (`SM_SECRET_KEY` muss gleich bleiben, sonst werden Sitzungen und API-Token ungültig), Sicherungen aus der Offsite-Kopie, danach DNS umstellen; nach dem Restore läuft der Löschlauf (DAT-051).
Abnahme: Restore mit beschädigter Datei → Abbruch, Datenbank unverändert; Restore auf frischer Instanz ohne Schlüssel → Abbruch mit Meldung; nach Restore: Konten anmeldbar, Atteste lesbar (Dateiprüfung).

**SIC-116** · P0 · Status: offen (Ist: Test-Restore der Datenbank; Lücke: Dateiprüfung nur 5 Dateien, vollständiger Probe-Restore nicht belegt) · **Restore-Tests**
- Monatlich Pflicht: Test-Restore einer Monatssicherung in eine Wegwerf-Datenbank (zählt Planversionen und Konten, Live-Daten unberührt); halbjährlich vollständiger Probe-Restore auf separater VM (Installation, Sicherung einspielen, Anmeldung und Vertretungsplan prüfen) mit Nachweis (Datum, Sicherungsdatei, Dauer, Ergebnis, Name); **vor dem Echtbetrieb** einmal auf dem Zielsystem. In der App: „Prüfen“ spielt eine App-Sicherung in eine Wegwerf-Kopie (SQLite: Integritätsprüfung „ok“, Zeilen je Tabelle, Konten > 0, Planversionen > 0 = bestanden; JSON: Format „schulmanager-backup“ und Planungsdokument vorhanden). `verify-files` entschlüsselt **alle** Dateien und vergleicht Prüfsummen (Exit-Code 1 bei fehlenden/beschädigten Dateien).
Abnahme: Der Restore-Test meldet die Zahl geprüfter Dateien gleich der Zahl in der Sicherung (nicht 5); das Nachweisprotokoll liegt vor dem ersten Echtbetrieb vor; ein Test mit einer entfernten Datei im Archiv schlägt fehl.

**SIC-117** · P0 · Status: Ist · **Wiederanlauf-Richtwerte**
- RPO = Abstand der Sicherungen (Standard 24 Stunden; mit zwei Zeiten ca. 12 Stunden); RTO ca. 1 Stunde mit vorbereitetem Server. Stufen: 0 (Standard: eine VM, nächtliche Sicherung plus Offsite; RTO 1–4 h, RPO ≤ 24 h), 1 (häufigere Sicherungen, z. B. 4 Zeiten; RTO ca. 1 h, RPO ≤ 4–5 h), 2 (Kaltreserve: zweite VM in anderem Rechenzentrum, RTO 15–30 min), 3 (Warmreserve mit Datenbank-Replikation, RTO 5–15 min, RPO Sekunden). Die Schule wählt die Stufe; jede höhere Stufe ist im Betriebshandbuch beschrieben.
Abnahme: Das Betriebshandbuch nennt für die gewählte Stufe RPO/RTO; der halbjährliche Probe-Restore (SIC-116) misst die Dauer und vergleicht sie mit dem RTO.

---

## 22 Mandantentrennung und Mehrinstanz-Betrieb

**SIC-118** · P0 · Status: Ist · **Eine Instanz je Schule (Mandantentrennung)**
- Jede Schule hat eine eigene Instanz: eigene Datenbank, eigener Dateispeicher (Volume), eigener `SM_SECRET_KEY`, eigener Verschlüsselungs-Schlüsselring, eigene Domain/Subdomain; keine gemeinsamen Daten oder Schlüssel zwischen Instanzen (auch nicht zwischen Haupt-, Demo- und Test-Instanz). API-Schlüssel und Sitzungen einer anderen Schule sind wirkungslos (eigener Test „Schlüssel einer anderen Schule ist wertlos“). Anmeldungen und Cookies gelten je Host und Port. [offen: Zentraler Anmeldepunkt für viele Schul-Subdomains erst bei der zweiten Schule, Entscheidung des Betreibers; „Mehrere Schulen auf einer Instanz“ ist ausdrücklich nicht im Umfang.]
Abnahme: Token/Sitzungs-Cookie von Instanz A gegen Instanz B → 401; die Schlüsselringe zweier Instanzen sind verschieden (Fingerabdrücke, `crypto-status`); ein Dump von A ist mit dem Ring von B nicht lesbar.

**SIC-119** · P0 · Status: offen (Betriebsmodell des Altsystems: eine Anwendungsinstanz) · **Zustand im Prozess und Entscheidung Einzel-/Mehrknoten-Betrieb**
- Im Altsystem liegt Zustand im Speicher eines Prozesses: Arbeitskopie des Planungsdokuments, Cache der Anmelde-Richtlinien (5 s) und Einstellungen (5 s), Discovery- und Schlüssel-Caches der Anbieter (3600 s; bei unbekannter Schlüssel-ID Neuladen höchstens alle 30 s), Rate-Limit-Zähler, Speicher des 2FA-Replay-Schutzes, Live-Ereignisse, Hintergrundaufträge. **Entscheidung für den Neubau:** Standard ist die **Einzelinstanz mit Sicherung und Wiederherstellung**; ein Betrieb mit mehreren Knoten (mehrere Server je Schule) wird erst angeboten, wenn er einmal vollständig durchgespielt ist, und verlangt PostgreSQL, gemeinsame Dateiablage und einen Verteiler (Proxy mit Lastverteilung).
- Sobald mehr als ein Knoten betrieben wird, gelten SIC-120 bis SIC-123; vorher sind sie als Prüfung der Konfiguration umzusetzen („mehr als ein Knoten ohne gemeinsamen Zustand → Start verweigert“).
Abnahme: Start mit `SM_HA=1` und SQLite oder ohne gemeinsame Dateiablage → Abbruch mit Meldung.

**SIC-120** · P0 · Status: offen · **Sicherheitszustand knotenübergreifend**
- 2FA-Replay-Schutz (benutzte Codes), Rate-Limit-Zähler (Konto/IP) und alle Drosselungszähler liegen in einem gemeinsamen Speicher (Datenbank bzw. Cache), nicht je Prozess; alternativ setzt der Verteiler das IP-Limit (Altsystem: Rate-Limit je Knoten, Replay-Schutz je Prozess). Sitzungen und Token liegen in der Datenbank; Rechte-Abweichungen werden je Anfrage geladen; Caches höchstens 5 Sekunden.
Abnahme: Mit zwei Knoten: derselbe TOTP-Code an Knoten A und danach an Knoten B → B lehnt ab; 6001 Anfragen derselben IP binnen einer Minute, verteilt auf beide Knoten → die 6001. Anfrage erhält 429; Sitzung wird auf A beendet → B antwortet 401.

**SIC-121** · P0 · Status: offen · **Gleichzeitige Änderungen**
- Schreibende Aktionen am Planungsdokument und an Freigaben (Plan-Übernahme, Vertretungs-Freigabe) prüfen die Version (optimistische Sperre, 409 bei Konflikt); Änderungen laufen auf einer Kopie, bei Fehler bleibt alles unverändert, danach neue Version, Audit-Eintrag und Ereignis in derselben Transaktion. Der Altbestand kennt keine Konfliktregel bei parallelen Schreibvorgängen.
Abnahme: Zwei parallele Änderungen auf derselben Version → eine erfolgreich, die andere 409; kein Zwischenzustand ohne Audit-Eintrag.

**SIC-122** · P0 · Status: Ist (Mehrknoten: offen) · **Führungsknoten, Wartung, Migrationen**
- `SM_NODE_ID` (höchstens 40 Zeichen, Standard `main`), `SM_HA` = 1: Hintergrundjobs und Wartung laufen nur auf dem Führungsknoten (Leader-Sperre, Drain). Migrationen beim Start (`SM_AUTO_MIGRATE` = 1) laufen nur auf **einem** Knoten (bei mehreren Instanzen sonst Konfliktpunkt) und vor jedem Update an einer Kopie der Datenbank getestet. Ein Knoten im Drain antwortet auf der Bereitschaftsprüfung mit 503.
Abnahme: Zwei Knoten starten gleichzeitig → genau einer migriert und führt die Wartung aus; der Drain-Knoten antwortet 503 und erhält keine neuen Anfragen.

**SIC-123** · P0 · Status: offen · **Live-Ereignisse über mehrere Knoten**
- Live-Ereignisse (Änderungs-, Auftrags-, Zielkonto-Ereignisse) werden über alle Knoten verteilt (gemeinsamer Bus); Rechteprüfung und Schließen von Verbindungen gilt knotenübergreifend (SIC-029). Wiederaufnahme nach Verbindungsabbruch und Ereignis-Reihenfolge sind festzulegen [unklar: im Altsystem nicht beschrieben].
Abnahme: Ereignis an Knoten A erreicht einen Strom an Knoten B; Sperre eines Kontos beendet den Strom an Knoten B innerhalb eines Pings.

---

## 23 Updates, Lizenz-Integrität, Anbieter-Dienste

**SIC-124** · P0 · Status: Ist · **Signierte Updates: Prüfung durch den Update-Dienst**
- Jedes Release-Manifest (kanonisches JSON: sortierte Schlüssel, ohne Leerzeichen, UTF-8) ist mit **Ed25519** vom Anbieter signiert; der Update-Dienst prüft mit dem eingebauten, gepinnten Anbieter-Schlüssel (Fingerabdruck = erste 16 Hex-Zeichen des SHA-256 des Prüfschlüssels; Änderung → Dienst hält an). Prüfregeln, jeweils Ablehnung bei Verstoß: Signatur gültig; Produkt-Kennung stimmt; Version `x.y.z`; **Downgrade-Schutz** (größer als die laufende und größer als die höchste je installierte Version); Mindestversion; Verteilung per Datei: SHA-256 (64 Hex), sicherer Dateiname, Größe > 0; per Registry: Abbild **nur per Digest** (`sha256`), nur Abbilder mit konfiguriertem Präfix; Adresse nur `https` (lokale Ausnahme nur in Entwicklung); Antwort des Anbieters: Signatur, Nonce, Instanz-ID und Knotenname stimmen (sonst ignoriert); Anbieter nicht erreichbar: Zeitlimit 20 s, keine Änderung. **Befehlsgrenze:** der Dienst führt ausschließlich „Version X installieren“ aus – keine Befehle, Skripte oder Adressen aus Antworten.
Abnahme: Manifest mit falscher Signatur, mit niedrigerer Version, mit Registry-Tag statt Digest, mit `http://`-Adresse, mit Fremdprodukt-Kennung → jeweils abgelehnt; Wechsel des Prüfschlüssels hält den Dienst an.

**SIC-125** · P0 · Status: Ist (Dienst auf dem Schulserver nicht eingespielt) · **Update-Ablauf mit Sicherung und Rückkehr**
- Vorbereiten: Platz mindestens max(2048 MB; 2 × Dateigröße), Download mit Zeitlimit 600 s, SHA-256 und Größe müssen stimmen. Last wegnehmen (Drain 20 s, Bereitschaftsprüfung 503), Sicherung (`vor-update-<Version>`; Fehler → Update nicht gestartet), neue Version starten (Migration beim Start), Gesundheitsprüfung: Status ok, Datenbank ok, Startseite erreichbar, Version = Zielversion, **3 gute Prüfungen hintereinander** (Abstand 5 s, Gesamtlimit 300 s). Fehler → Rückkehr auf die alte Version; war die Migration nicht abwärtskompatibel, Einspielen der Sicherung (nur bei Einzelserver oder Wartungsfenster); Meldung an den Anbieter; die gescheiterte Zielversion bleibt blockiert bis „Erneut versuchen“.
- Die Schule darf ein Update einmal um 1 bis 7 Tage verschieben, außer es ist als dringend (Sicherheit) markiert. Rollout: erst Test-Schulen, dann Prozentwellen; Termine als Datum und Uhrzeit in deutscher Zeit.
Abnahme: Ein absichtlich scheiterndes Release (Gesundheitsprüfung rot) führt zur Rückkehr auf die alte Version, Datenbank unverändert, Anbieter-Meldung; ein dringendes Update lässt sich nicht verschieben.

**SIC-126** · P0 · Status: offen · **Rechte des Update-Dienstes**
- Der Update-Dienst braucht Zugriff auf die Container-Verwaltung (praktisch Root-Zugriff). [unklar: Entscheidung offen; Alternativen: Zeitplan direkt auf dem Server oder nur manuelle Updates.] Bis zur Entscheidung gilt: Dienst läuft nur mit der Befehlsgrenze von SIC-124, lauscht auf keinem Netzwerkport, ist nicht aus der Anwendung heraus steuerbar, und seine Zustandsdatei ist nur für ihn schreibbar. „Jetzt installieren“ der Schule darf die vertragliche Regel „nur manuelle Updates“ nicht umgehen [Entscheidung offen, Hinweis 8].
Abnahme: Port-Scan der Instanz zeigt keinen Port des Update-Dienstes; die Anwendung (Konto `admin`) kann keine Update-Aktion auslösen, die der Dienst nicht aus dem Anbieter-Angebot ableitet.

**SIC-127** · P0 · Status: offen (Ist: Signatur, Nonce, Bindung, MAC; offen: ungeschützter Sperrzustand, ein gemeinsamer Signaturschlüssel) · **Lizenz-Integrität**
- Lizenzantworten: Ed25519-Signatur über kanonisches JSON, Prüfung auf der Schul-Instanz mit eingebautem Prüfschlüssel; Nonce (32 Hex-Zeichen je Anfrage, die Antwort muss ihn spiegeln), Instanz-ID und die letzten 4 Zeichen des Schlüssels müssen passen; falsche oder fehlende Signatur zählt wie „Anbieter nicht erreichbar“. Der Schlüssel ist an genau eine Instanz-ID gebunden; ein zweiter Server mit demselben Schlüssel wird abgelehnt. Ausführliche Prüfung beim Start und alle 24 Stunden (`SM_LICENSE_CHECK_HOURS`), kurze Statusabfrage alle 15 Minuten (`SM_LICENSE_PING_MINUTES`, damit eine Sperre zeitnah wirkt).
- Sperrbefehle: HMAC-SHA256 mit dem schulspezifischen Sperrgeheimnis (64 Hex) über Befehl, Text (höchstens 300 Zeichen), Zeitpunkt, Nonce der Anfrage, Instanz-ID und letzte 4 Zeichen; Vergleich in konstanter Zeit; ein Befehl für Schule A wirkt nicht bei Schule B und ist nicht wiederverwendbar. Das Sperrgeheimnis wird nur bei der Aktivierung einmal ausgeliefert. **Neubau:** Der Sperrzustand wird signiert oder an die Instanz gebunden gespeichert (nicht als ungeschützter Klartext in der lokalen Zustandsdatei); **getrennte Signaturschlüssel** für Lizenzantworten und Update-Manifeste.
- Lizenzprüfung im Echtbetrieb nicht abschaltbar; Lizenzserver-Adresse und öffentlicher Prüfschlüssel fest eingebaut **vor dem ersten Kunden** (sonst könnte sich eine Schule eigene Lizenzen ausstellen). Die Sperre wirkt auf alle Schnittstellen (Test über rund 500 Routen); Administration und Schulleitung erreichen trotz Sperre nur Anmeldung und `/lizenz`.
Abnahme: Antwort mit manipulierter Signatur/falscher Nonce → wie „nicht erreichbar“; Entfernen des Sperrbefehls aus der Zustandsdatei hebt die Sperre nicht auf (erneuter Kontakt höchstens nach 15 Minuten und Datei ist signiert); Sperrbefehl von Schule A bei Schule B → wirkungslos; Test über alle Routen: im Sperrzustand 403 `license_locked`, außer Anmeldung und `/lizenz`.

**SIC-128** · P0 · Status: Ist (Mehr-Rollen-Konten im Portal: offen) · **Anbieter-Dienste (Lizenzserver und Portal)**
- Schlüssel: Hash zum Suchen und zusätzlich verschlüsselt zum Anzeigen (jede Anzeige im Verlauf der Schule vermerkt); Neuausstellung entwertet den alten Schlüssel, Bindung und Sperrgeheimnis; der private Signaturschlüssel liegt nur auf dem Lizenzserver (Rechte 0600, nie im Image). Portal-Anmeldung: PBKDF2, Fehlversuchs-Sperre, CSRF, Herkunftsprüfung, Sitzung 8 Stunden (nur im Arbeitsspeicher), Cookie HttpOnly/SameSite=Strict/Secure; Anfragegrenzen 60 bzw. 120 je 10 Minuten je Adresse; Header wie SIC-089. **Neubau:** statt eines gemeinsamen Passworts Konten mit Rollen im Portal [Vorschlag aus Hinweis 16]. Gefährliche Aktionen (Kündigen, Sperren) verlangen die Eingabe des exakten Schulnamens.
- Zahlungs-Webhooks: Stripe `Stripe-Signature` (HMAC-SHA256 über „Zeit.Körper“, Zeitfenster 300 s), GoCardless `Webhook-Signature` (HMAC-SHA256 über den Rohtext, ohne Zeitfenster; Schutz nur über die eindeutige Anbieter-Kennung); ohne eingerichtetes Geheimnis 503. Zahlungen laufen nur im Lizenzserver, nie in der Schul-App.
Abnahme: Wiederholter Stripe-Webhook mit Zeitstempel +10 Minuten → abgelehnt; Kündigen ohne exakten Schulnamen → abgelehnt; Datenbank-Dump des Lizenzservers enthält keinen Schlüssel im Klartext.

---

## 24 Server-, Container- und Betriebshärtung (TOMs)

**SIC-129** · P0 · Status: Ist · **Container-Härtung**
- Die Anwendung läuft als unprivilegierter Benutzer (UID 10001); Root-Dateisystem schreibgeschützt, `/tmp` als tmpfs, Daten in einem Volume (`/app/data`); `cap_drop: ALL`, `no-new-privileges`; PID-, CPU- und RAM-Limits (`APP_MEMORY` Standard 3 GB). Der Proxy läuft mit minimalen Rechten (`NET_BIND_SERVICE`), schreibgeschützt. Mehrstufiger Build (erst Oberfläche, dann Laufzeit), Gesundheitsprüfung im Container, Neustart-Richtlinie `unless-stopped`.
Abnahme: Container-Inspektion zeigt UID 10001, `ReadonlyRootfs=true`, `CapDrop=ALL`, `no-new-privileges`; ein Schreibversuch außerhalb von `/tmp` und `/app/data` scheitert.

**SIC-130** · P0 · Status: Ist · **Netz, Ports, Host**
- Veröffentlicht sind nur 80/tcp, 443/tcp und 443/udp; Docker-veröffentlichte Ports umgehen die Host-Firewall, deshalb keine weiteren `ports:` (insbesondere nicht für PostgreSQL). Monitoring (Grafana, Prometheus, Uptime-Kuma) nur an Loopback, Zugang per SSH-Tunnel mit eigenen starken Passwörtern; Grafana sendet keine Nutzungsstatistiken. Host: minimales Betriebssystem, nur benötigte Dienste, automatische Sicherheitsupdates (`unattended-upgrades`), geplante Neustarts, NTP aktiv (TOTP, Zertifikate, Protokolle); SSH nur mit Schlüssel (`PasswordAuthentication no`, `PermitRootLogin prohibit-password` bzw. `no`), Zugriff nur aus Admin-Netzen oder VPN, optional `fail2ban`; Firewall eingehend 22 (eingeschränkt), 80, 443 (UDP 443 für QUIC). Dienste fremder Anwendungen (z. B. andere Container auf dem Server) teilen sich keine Angriffsfläche mit Lizenz- und Update-Server.
Abnahme: Externer Port-Scan der Instanz zeigt nur 80/443; `ss -tlnp` zeigt Grafana/Prometheus/Kuma nur auf `127.0.0.1`; SSH-Anmeldung mit Passwort scheitert.

**SIC-131** · P0 · Status: offen (Ist: Doku, kein Code) · **Datenbank**
- PostgreSQL nur im internen Netz `backend` (`internal: true`): weder aus dem Internet erreichbar noch mit Internetzugang, kein veröffentlichter Port. Zwei Datenbank-Benutzer: Migrationen mit einem Besitzer-Benutzer nur im Update-Schritt (`SM_MIGRATE_DATABASE_URL`), Laufzeit nur mit DML-Rechten (kein DDL); Audit-Rechte nach DAT-027. Wiederherstellung und `pg_dump` nutzen dieselbe Hauptversion (Wechsel der Hauptversion nie durch bloßes Ändern des Tags).
Abnahme: Verbindungsversuch von außerhalb des Compose-Netzes zur Datenbank scheitert; der Laufzeitbenutzer kann keine Tabelle anlegen oder löschen.

**SIC-132** · P0 · Status: offen (Ist: Vorlagen; Lücken: SMS-Anbieter und Lizenzserver als Empfänger im Verzeichnis) · **Auftragsverarbeitung, Hosting, Drittland**
- Die Schule ist Verantwortlicher (Art. 4 Nr. 7); Hoster, IT-Dienstleister und Betreiber sind Auftragsverarbeiter (Art. 28, AV-Vertrag, Unterauftragnehmer nur mit Zustimmung). Hosting im Rechenzentrum in Deutschland oder EU/EWR, bevorzugt ISO 27001; **kein Transfer in Drittländer**, auch nicht über US-Konzernmütter von Sicherungs-, Mail- oder CDN-Diensten, ohne geeignete Garantien. Im Verzeichnis (Art. 30) als Empfänger geführt: Hoster, IT-Dienstleister des Schulträgers, E-Mail-Versand (`SM_SMTP_*`), **SMS-Anbieter**, Offsite-Backup-Speicher, Monitoring-Dienst (falls genutzt), SSO-Identitätsanbieter, **Lizenzserver** (Lizenzkennung und Konten-Anzahl werden übertragen), optionaler Passwort-Leak-Dienst (SIC-036). Übersetzungsdienst nur als Unterauftragnehmer mit AV-Vertrag und EU-Standort (nur Brieftext, keine Namen von Kindern). Push-Inhalte ohne Gesundheitsdaten und ohne Namen anderer Kinder.
Abnahme: Das Verzeichnis-Muster der Auslieferung führt jeden ausgehenden Dienst der Konfiguration als Empfänger (Dokumententest: jede aktivierte `SM_*`-Integration hat einen Eintrag); Netzwerkmitschnitt zeigt keine Verbindung zu Zielen außerhalb der konfigurierten Liste.

**SIC-133** · P0 · Status: offen (Nachweisspalte im Altsystem leer) · **TOM-Nachweise und Kontrollrhythmus (Betrieb)**
- Die Betriebs-TOMs sind vom Betreiber/der Schule zu belegen (Maßnahme – Verantwortlich – Nachweis/Datum): Zutritt (zertifiziertes Rechenzentrum oder abgeschlossener Serverraum), Zugang Server (SSH nur mit Schlüssel, Admin-Netz/VPN), Zugriff Anwendung (Administrationskonten personengebunden, kein geteiltes Konto im Alltag, 2FA), Rechteprüfung (jährlich und zum Schuljahreswechsel: Konten und Rollen), Schlüssel (Tresor, getrennt von Sicherungen), Sicherung (Offsite, Test-Restore monatlich, Probe-Restore halbjährlich), Updates (monatlicher Patchtag), Netz (Firewall), Personal (Schulung: Rollen, Passwörter, 2FA, Zugangsbriefe, Gründe knapp halten, Exporte, Meldewege), Datenpanne (Meldeweg und Kontaktliste bekannt), Verträge (AV-Verträge), Endgeräte (Bildschirmsperre, aktuelle Browser, keine Passwörter im Browser auf Gemeinschaftsgeräten), Subunternehmer-Zugänge mit eigenen Konten, 2FA und minimalen Rechten. Kontrollrhythmus: monatlich Patchtag und Test-Restore; halbjährlich Probe-Restore; jährlich Rechte- und TOM-Prüfung.
Abnahme: Vor dem ersten Echtbetrieb ist jede Zeile des Betriebsnachweises mit Datum, Verantwortlichem und Nachweis ausgefüllt; die Statusseite zeigt „Rechteprüfung fällig“, wenn das Datum der letzten Rechteprüfung älter als 12 Monate ist [Vorschlag].

**SIC-134** · P0 · Status: Ist (Alarm-Versand: offen) · **Überwachung**
- `GET /healthz` (Status, Datenbank, ohne Daten), Metriken im Prometheus-Format nur mit `SM_METRICS_TOKEN`; empfohlene Monitore: HTTP-Keyword-Prüfung auf die Gesundheitsadresse (Intervall 60 s), Zertifikatsablauf mit Warnung 14 Tage vorher, Push-Monitor „Backup“ (Intervall 25 Stunden); Benachrichtigung an IT-Betreuung und Schulleitung (der Vertretungsplan ist morgens geschäftskritisch); möglichst auf einem anderen Server. Prometheus-Token in Compose und Vorlagen konfiguriert.
Abnahme: `/healthz` liefert `status: ok` ohne Personendaten; Ausfall der Instanz für 3 Minuten löst eine Benachrichtigung aus; `/metrics` ohne Token 401.

---

## 25 Vorfallbehandlung (technische Unterstützung)

Frist: Meldung an die Aufsichtsbehörde binnen **72 Stunden** ab Kenntnis (Art. 33), außer „voraussichtlich kein Risiko“ (Begründung dokumentieren); bei hohem Risiko Benachrichtigung der Betroffenen (Art. 34); **jede** Panne wird dokumentiert (Art. 33 Abs. 5), auch wenn nicht meldepflichtig. Verantwortlich ist die Schulleitung mit der/dem Datenschutzbeauftragten.

**SIC-135** · P0 · Status: Ist · **Werkzeuge zum Eindämmen**
- Die Software bietet: Konto deaktivieren; „alle Sitzungen beenden“ (Benutzer → Sitzungen); Passwort zurücksetzen (Oberfläche und CLI `reset-password --username`); `disable-2fa` und neue Einrichtung; Wechsel von `SM_SECRET_KEY` (meldet alle ab, API-Token ungültig) mit Neustart; Neuerzeugen der iCal-Links betroffener Nutzer; Dienst offline schalten (Reverse-Proxy stoppen); Aufheben von Anmelde-Bremsen (CLI `unlock`); Schlüssel-Rotation (DAT-008) und Neuverschlüsselung (DAT-009). Alle Geheimnisse werden rotiert (SIC-106).
Abnahme: Auf der Wegwerf-Instanz führt der Ablauf „Konto verdächtig“ in unter 10 Minuten [Prüfwert] zu: Konto deaktiviert, alle Sitzungen und Token beendet, Passwort neu, iCal-Link neu; das Audit hält jeden Schritt fest.

**SIC-136** · P0 · Status: Ist · **Beweise sichern, bewerten, melden**
- Vor Bereinigung: Container-Logs exportieren, Sicherung mit Kennzeichen (`make backup`), Audit-Export, Snapshot beim Hoster. Bewerten: `GET /api/v1/audit?since=…`, Zugriffslogs über Request-IDs, Kontenliste; Fragen: welche Daten, wie viele Personen, welches Risiko (Minderjährige, Art.-9-Daten). Meldung: Meldeformular der Landesbehörde; Schulaufsicht und Schulträger nach Landesvorgabe. Wiederherstellen: Ursache beseitigen (Update, Konfiguration, Passwort); ggf. System neu aufsetzen und Sicherung von vor dem Vorfall einspielen; alle Geheimnisse rotieren. Nachbereiten: Ursachenanalyse, Maßnahmen, TOMs anpassen, Vorfallsbericht. Alles mit Uhrzeit protokollieren; nichts vorschnell löschen.
Abnahme: Das Betriebshandbuch enthält die sieben Schritte mit den genannten Befehlen; ein Übungslauf auf der Wegwerf-Instanz erzeugt Audit-Export und Sicherung mit Kennzeichen, ohne dass Beweise überschrieben werden.

**SIC-137** · P0 · Status: Ist · **Sonderfälle**
- Ransomware oder kompromittierter Server: Server nicht weiterverwenden, neu aufsetzen (frisches Betriebssystem, neue Geheimnisse), Sicherung aus der versionierten Offsite-Kopie von vor dem Befall einspielen, vorher per Test-Restore prüfen. Zugangsbriefe falsch verteilt: betroffene Konten zurücksetzen (neue Briefe); in der Regel Dokumentation, Meldung nach Risikobewertung. Gerät mit aktiver Sitzung verloren: Sitzungen des Kontos beenden, Passwort ändern, ggf. 2FA neu einrichten.
Abnahme: Übungsfall „Zugangsbriefe falsch verteilt“: Stapel-Zurücksetzen erzeugt neue Startpasswörter, beendet alle Sitzungen der Konten, die alten Briefe sind unbrauchbar.

**SIC-138** · P0 · Status: offen (Ist: Vorlagen im Betreiber-Paket; Kontakte vom Betreiber auszufüllen) · **Vorlagen für den Ernstfall**
- Im Betreiber-Paket: Kontaktliste (Schulleitung als Verantwortlicher, IT-Betreuung, Datenschutzbeauftragte/r, Hoster mit Support und Vertragsnummer, Schulträger-IT, Aufsichtsbehörde; je mit Vertretung; ausdrucken, offline aufbewahren); Verzeichnis-Eintrag „Stunden- und Vertretungsplanung“ (Zwecke, Rechtsgrundlage Art. 6 Abs. 1 lit. e i. V. m. Landesschulgesetz, Betroffene, Datenkategorien, Empfänger, Drittlandübermittlung keine, Löschfristen, TOMs); Vorfallsbericht (Kurzform: Datum/Uhrzeit der Kenntnis, Meldung von, Beschreibung, betroffene Daten und Personen, Sofortmaßnahmen mit Uhrzeit, Risikobewertung gering/mittel/hoch mit Begründung, Meldung an Aufsicht ja/nein mit Aktenzeichen, Benachrichtigung Betroffener, Ursache, dauerhafte Maßnahmen, Abschluss mit Unterschrift). Vorlagen sind **Entwürfe** und keine Rechtsberatung; eine juristische Prüfung steht aus. Die DSFA-Schwellwertanalyse (mehr als 2500 Schüler/innen, Minderjährige, mittelbare Art.-9-Daten) ist zu dokumentieren.
Abnahme: Das Betreiber-Paket enthält die drei Vorlagen; offene eckige Platzhalter lösen eine Warnung aus und der Einrichtungsschritt gilt nicht als erledigt.

**SIC-139** · P0 · Status: offen [Vorschlag aus dem Vorfall vom 16./17.10.] · **Benachrichtigung bei Änderungen an Administrationskonten**
- Lehre aus dem Vorfall (neues Administrationskonto stufte das Inhaber-Konto herab und legte ein weiteres Administrationskonto an): Jede Anlage, Herabstufung, Deaktivierung, Löschung oder Rechte-Vergabe eines Administrationskontos benachrichtigt den Inhaber (Glocke, E-Mail) und steht im Audit. „Neue Administrationskonten sind nachvollziehbar.“ Schreibzugriff auf die Live-Datenbank durch Betreiber-Werkzeuge nur nach ausdrücklicher Freigabe.
Abnahme: Anlage eines Administrationskontos erzeugt eine Benachrichtigung an den Inhaber und genau einen Audit-Eintrag mit Anlegerkonto und Zeit.

---

## 26 Querschnitts-Prüfnetz (verteidigende Abnahme)

Die folgenden Prüfungen sind selbst Anforderungen; sie laufen in der CI bzw. auf der Wegwerf-Instanz und belegen die Schutzbereiche der Kapitel 2 bis 25.

**SIC-140** · P0 · Status: offen (Ist: Teile) · **Routen-Register-Prüfung**
- Ein Test liest die Liste **aller** registrierten Routen und prüft je Route: (1) Rechte-/Bereichsdeklaration vorhanden, (2) Audit-Aufruf bei schreibenden Routen oder Eintrag in der Ausnahmeliste (DAT-031), (3) CSRF-Pflicht bei Sitzungs-Cookie, (4) Verhalten im Demo-Betrieb (gesperrt oder freigegeben), (5) Verhalten für `zuschauer` (gesperrt oder Allowlist), (6) Verhalten für API-Schreib-Token (Allowlist), (7) 404-Verhalten bei fremder ID, (8) Eingabemodell mit `extra=forbid`.
Abnahme: Eine neu hinzugefügte Route ohne eine dieser Deklarationen lässt die CI scheitern; die Testausgabe nennt die Route.

**SIC-141** · P0 · Status: offen (Ist: 42 Fälle) · **Objekt- und Rollen-Matrix**
- Für **jeden** Endpunkt mit ID: Konto A fordert das Objekt von Konto B → 404 (SIC-013). Negativtests: Lehrkraft fremder Klasse, Elternteil fremdes Kind, Schüler anderer Klasse, abgelaufene oder entzogene Rolle, Fachlehrkraft ohne Zuständigkeit. Zusätzlich je Rolle (12 Rollen + eigene Rollen je Grundtyp) die Rechte-Matrix gegen die Architektur-Doku (Test `matrix == code`).
Abnahme: Testbericht: 100 % der Routen mit Pfadparameter getestet, 0 Abweichungen; die Rechte-Matrix in der Doku und im Code ist identisch.

**SIC-142** · P0 · Status: Ist (Rundgang je Rolle: Teile) · **Rollen-Rundgänge**
- Rundgang je Rolle: alle Lese-Adressen mit dem Konto aufrufen; Soll: nur die Daten des Umfangs, alle übrigen 403/404; Referenz: Zuschauer-Rundgang 274 Lese-Adressen; Live-Test mit 11 Rollen und rund 500 Aufrufen ohne Fehler, Ansichtskonto korrekt blockiert, Kontowechsel funktioniert. Dazu: 300 Konten hinter einer IP (SIC-091).
Abnahme: Je Rolle ein Bericht „Adresse → Status“ gegen die Soll-Tabelle (REC); Abweichung = Fehler.

**SIC-143** · P0 · Status: offen · **Datenbank-Dump-Scan**
- Ein Test erzeugt auf der Wegwerf-Instanz Beispieldaten in **allen** Bereichen und scannt den Datenbank-Dump und das Dateiverzeichnis: (a) keine lesbare Zeichenfolge in einer Katalogspalte (Kap. 9), (b) kein Passwort/Startpasswort/Token/Code im Klartext (nur Hash/HMAC), (c) keine Datei ohne `SMS1`-Kopf, (d) kein Schlüsselmaterial in Sicherungen.
Abnahme: 0 Treffer; der Test schlägt an, wenn eine Spalte versehentlich unverschlüsselt befüllt wird (Gegenprobe).

**SIC-144** · P0 · Status: offen (Ist: Teile) · **Konfigurations-, Header- und Browser-Prüfungen**
- Start-Tests für jede Zeile von SIC-101/SIC-102; Header-Test für Startseite, API-Route, Datei-Route, API-Doku (SIC-089); Cookie-Attribute (SIC-057); Browser-Rundgang mit Netzwerkmitschnitt (0 Fremd-Requests, SIC-067); keine Source Maps/Dotfiles (SIC-090); Zugriffs-/Fehlerlog-Scan auf Geheimnisse (SIC-006); Textvergleich Doku gegen Verhalten (SIC-008); Barrierefreiheit der Sicherheitsseiten (Datei OBE).
Abnahme: Alle genannten Tests laufen grün in der CI; ein absichtlich entfernter Header lässt den Header-Test scheitern.

**SIC-145** · P0 · Status: offen · **Regressions-, Last- und Wiederholungstests**
- Jeder behobene Fund hat einen Regressionstest (SIC-002); die Prüfungen der Kapitel 12 (Rate-Limit mit gesenkter Schwelle; Wirkung nachgewiesen bei 6000/min im Produktivbetrieb), 21 (Restore) und 23 (Update-Rückkehr) laufen vor jedem Release; ein Lasttest (7:30 bis 8:00 Uhr: 2500 Schüler/innen, 300 Lehrkräfte; 95 % der Anfragen unter 500 ms) auf der Wegwerf-Instanz; der Penetrationstest wird nach Behebung wiederholt (SIC-010). Gesamttests nur einmal vor dem Deploy, geänderte Bereiche laufen laufend.
Abnahme: Das Release-Protokoll enthält die Ergebnisse der genannten Läufe mit Datum, Version und 0 offenen Funden der Stufe „hoch“.

---

## 27 Typische Fehlerklassen aus den früheren Prüfungen (nur Art und verhindernde Regel)

Quellen: Code-Durchsicht 13.10., Haftungsaudit und dynamischer Test 17.10., Prüfliste „Reels“ (69 Punkte), Befundliste der Bestandsprüfung, Recherchen zu Klagen/Bußgeldern. Keine Angriffsdetails; die Regel in der dritten Spalte verhindert die Klasse und ist in der vierten Spalte verortet.

| Nr | Fehlerklasse (Art) | Verhindernde Regel | Anforderung |
|---|---|---|---|
| FK-01 | Schutz nur auf einem Weg (pfadbasiert; Massen-Reset über Zugangsbriefe umging den Inhaber-Schutz) | Schutzprüfung im zentralen Dienst; jeder Weg läuft durch denselben Dienst, nie nur im Routen-Handler | SIC-003, SIC-021 |
| FK-02 | Sperrliste statt Freigabeliste (Schreib-Token, Demo, Export) | Default-Deny: neue Routen sind gesperrt, bis ausdrücklich freigegeben | SIC-004, SIC-033, SIC-064 |
| FK-03 | Massen- und Sammelwege umgehen Einzelregeln (Zugangsbriefe, Exporte, Import) | Massen- und Einzelaktion nutzen dieselbe Prüfung je Objekt | SIC-003, SIC-028, SIC-039 |
| FK-04 | Dieselben Daten, zwei Regeln (Geburtsdatum in Klassenseite verborgen, in Sammel-API sichtbar) | Ein Feldregelwerk für Einzelansicht, Liste, Export, Feed, Auskunft | SIC-027 |
| FK-05 | Rechte eingefroren oder nicht neu geprüft (Live-Ströme, Token nach Herabstufung) | Rechte je Anfrage neu berechnen; Verbindungen bei Änderung schließen | SIC-012, SIC-029, SIC-058 |
| FK-06 | Lebensdauer ohne Widerruf (API-Token unbefristet, überleben Passwortwechsel/Sperre/2FA-Reset) | Pflichtlaufzeit; Widerruf bei Passwortwechsel, Reset, Sperre, 2FA-Reset, Herabstufung, Austritt, Volljährigkeit | SIC-058, SIC-062 |
| FK-07 | Nutzereingaben steuern Verbindungen (frei wählbare Ziele, interne Netze erreichbar) | Zentrale Zielprüfung für jede nutzerbeeinflusste Adresse; Antwortinhalte nie in Fehlermeldungen | SIC-097 bis SIC-099 |
| FK-08 | Klartext oder umkehrbare Speicherung (Startpasswörter, 2FA-Geheimnis, Kalender-Token) | Nur Hash (wo Vergleich genügt) oder Verschlüsselung mit Bindung; Rewrap bei Rotation | SIC-038, SIC-041, SIC-063, DAT-001 |
| FK-09 | Vertrauen in Proxy-Header von jedem Absender | Weiterleitungs-Köpfe nur von festen Proxy-Adressen; App nie direkt veröffentlicht | SIC-061 |
| FK-10 | Entwicklungs- und Testschalter im Live-Betrieb (Dev-Modus, Demo-Konten, Dev-Erst-Passwort im Log, Test-Postausgang öffentlich, Schlüssel neben der Datenbank) | Betriebsmodus Pflicht, harte Start-Prüfung, Dev-Schalter im Produktivstart verboten | SIC-046, SIC-100 bis SIC-104, DAT-010 |
| FK-11 | Antworten verraten Zustände (Orakel: 2FA-Konto ohne Fehlversuch, Verbindungsfehler-Art) | Einheitliche Antworten und Laufzeit; jeder Fehlversuch zählt | SIC-007, SIC-044, SIC-097 |
| FK-12 | Sperre als Angriffsvektor (harte Kontosperre sperrt Fremde, Schul-IP) | Progressive Wartezeit je Paar/IP/Konto (nur unbekannte IPs), nie harte Sperre; sichtbar und aufhebbar | SIC-091 bis SIC-094 |
| FK-13 | Schwache Passwortprüfung (kleine Trivialliste, Benutzername erlaubt) | Liste ≥ 3000, Benutzername im Passwort abweisen, Hash-Parameter prüfen | SIC-034 bis SIC-037 |
| FK-14 | Anmeldewege unterschiedlicher Stärke (SSO umgeht 2FA; Konto-Verknüpfung per unbestätigter E-Mail) | Alle Wege gleiche 2FA-Regel; Verknüpfung nur mit bestätigter Adresse | SIC-042, SIC-051 |
| FK-15 | Zweiter Faktor nur empfohlen, keine Wiederherstellungscodes | Pflicht für `admin`; Wiederherstellungscodes | SIC-042, SIC-043 |
| FK-16 | Fehlende Protokolle (Exporte, Anmeldefehler, Beobachtungs-Lesezugriffe) und kein Alarm | Audit-Pflicht-Liste; Alarm bei Massenzugriff | DAT-021, DAT-032 |
| FK-17 | Keine oder zu lange Löschfristen; Konfigurationswert „0“ schaltet Löschung ab | Registry je Datenart mit Frist; kein Wert, der Löschung abschaltet | DAT-040, DAT-048 |
| FK-18 | Zu viele Daten ausgegeben (Geburtsdatum in Sammelansicht, volle IP im Zugriffslog) | Jedes Feld gegen Rechte und Zweck prüfen; IP kürzen | SIC-027, DAT-026, DAT-028 |
| FK-19 | Doku und Verhalten weichen ab (IP-Kürzung zugesagt, nicht umgesetzt; „keine Fremdskripte“ trotz SSO) | Texte aus Konfiguration ableiten oder per Test gegen das Verhalten prüfen | SIC-008, DAT-028 |
| FK-20 | Fremdressourcen im Browser (Swagger-CDN, Anbieter-Skripte, Schriften) | Keine Drittquellen; Anbieter-Skripte erst beim Klick/aktivem Anbieter | SIC-052, SIC-067, SIC-089 |
| FK-21 | Freie Rechtevergabe ohne Grenze (Eltern/Schüler mit `gradebook.use` bearbeiten alle Notenbücher) | Serverseitige Scope-Grenze je Grundtyp; feste Mindestregeln | SIC-015, SIC-017 |
| FK-22 | Familienzugriff nach Volljährigkeit (iCal, Dokumente, Stundenplan) | Elternzugriff endet automatisch mit 18 für alle Ausgaben | SIC-026 |
| FK-23 | Formel-Einschleusung in Exporten | Eine zentrale Zellen-Entschärfung für jeden CSV-Export | SIC-069 |
| FK-24 | Ungeprüfte Ressourcen beim Import (Entpacken ohne Grenze) | Größen-, Zeit- und Entpackgrenzen, Test | SIC-071 |
| FK-25 | Fail-open-Schalter ohne Kennzeichnung (Virenscan, Leak-Prüfung) | Fail-open nur mit sichtbarer Kennzeichnung/Protokoll | SIC-036, SIC-078 |
| FK-26 | Doku-Endpunkte öffentlich (OpenAPI/Swagger) | In Produktion aus oder nur für angemeldete Administratoren | SIC-090 |
| FK-27 | Beobachtungsfunktion ohne geklärte Grundlage | Zweck und Rechtsgrundlage vor Aktivierung dokumentieren; Zugriffe protokollieren | DAT-037, DAT-039 |
| FK-28 | Lokale Schlüssel bleiben nach Abmeldung | Chat-Schlüssel beim Abmelden entfernen oder sperren | SIC-086 |
| FK-29 | Daten des vorigen Kontos im selben Tab sichtbar (Zwischenspeicher überleben Abmeldung/Kontowechsel) | Zentrale Rücksetzung aller Zwischenspeicher bei Abmeldung, Kontowechsel, 401 | SIC-059 |
| FK-30 | 403 statt 404 bei fremden vorhandenen Datensätzen (ID-Erkennung) | 404-Regel auf allen Routen mit Objekt-ID; automatischer Routen-Test | SIC-013, SIC-141 |
| FK-31 | Einmal-Token nicht atomar verbraucht | Atomarer Einmalverbrauch, Test mit parallelen Anfragen | SIC-047 |
| FK-32 | Offene Weiterleitung nach Anmeldung | Nur interne Pfade | SIC-070 |
| FK-33 | Unvollständige Pseudonymisierung/Auskunft (Namen im Audit nach Löschung, Protokolle zu Schüler/innen fehlen) | Registry-Vollständigkeit; Pseudonymisierung aller Protokollbezüge; Auskunft ohne stille Kürzung | DAT-048, DAT-052, DAT-054 |
| FK-34 | Entschlüsselungsfehler werden still mit leeren Werten überschrieben | Speichern bricht ab (409); Hinweis | DAT-006 |
| FK-35 | Rotation lässt Teilbestände am alten Schlüssel | Rotation über Registry, inklusive innerer Token; Testabdeckung | DAT-008 |
| FK-36 | Doppelte Sicherheits-Header / 500 ohne Request-ID | Jeder Header genau einmal; Request-ID in Antwort und Log | SIC-068, SIC-089 |
| FK-37 | Standardkonten mit bekanntem Passwort öffentlich erreichbar | Keine bekannten Standardzugänge auf öffentlichen Instanzen; im Produktivmodus gesperrt | SIC-033, SIC-046 |
| FK-38 | Sperrzustand der Lizenz ungeschützt lokal; ein Signaturschlüssel für alles | Sperrzustand signiert/gebunden; Schlüssel trennen | SIC-127 |
| FK-39 | Insider-Abfluss/Offboarding (Export ohne Protokoll, Konten nach Austritt aktiv) | Konten bei Austritt sofort sperren; Export protokolliert; Alarm | SIC-028, SIC-031, DAT-032 |
| FK-40 | Gesundheitsdaten an falscher Stelle (Administration, Audit, Mail, Push, Logs) | Nur Zuständige; Maskierung im Audit; keine Gründe in Mails/Push/Logs | SIC-016, SIC-025, SIC-074, DAT-024 |
| FK-41 | Geheimnisse im Quellbestand/Weitergabe von Code | Secret-Scan über alle Zweige; keine Code-Weitergabe an Fremddienste | SIC-109, SIC-111 |
| FK-42 | Ungeübte Wiederherstellung („funktioniert“ nur für Konten, nicht für Dateien) | Test-Restore monatlich, Dateiprüfung vollständig, Probe-Restore halbjährlich | SIC-116 |
| FK-43 | Tracker, Session-Replay, Analyse | Keine Tracker; Telemetrie nur, was die Person selbst abschickt | SIC-067 |
| FK-44 | Unsignierte Updates/Lizenzantworten | Ed25519-Signatur, Pinning, Downgrade-Schutz, Befehlsgrenze | SIC-124, SIC-127 |

---

## 28 Anhang A: sicherheitsrelevante Konfigurationsvariablen

Spalten: Name – Standard – Bereich/Einheit – Wirkung. (Geheimnisse sind nie Teil der Dokumentation; „Pflicht“ = Start bricht in Produktion ohne gültigen Wert ab.)

**Betrieb, Modus, Adresse**

| Name | Standard | Bereich | Wirkung |
|---|---|---|---|
| `SM_MODE` | Pflicht (Neubau) | `production`, `demo`, `development` | Betriebsmodus (SIC-100) |
| `SM_ENV` | – | `development`, `production` | muss zu `SM_MODE` passen |
| `SM_SECRET_KEY` | Pflicht | ≥ 32 Zeichen | HMAC-Schlüssel (DAT-011) |
| `SM_ENCRYPTION_KEYS` | Pflicht | Liste `kid:Base64(32 Byte)` | Schlüsselring (DAT-007) |
| `SM_BASE_URL` | – | `https://…` | öffentliche Adresse (Links, SSO-Rückkehr) |
| `SM_COOKIE_SECURE` | 1 in Produktion | 0/1 | Secure-Attribut |
| `SM_TRUST_PROXY` / `SM_PROXY_COUNT` / `SM_TRUSTED_PROXIES` | 0 / 1 (min. 1) / leer = Loopback | 0/1, Stufen, Adressen/Netze | Proxy-Vertrauen (SIC-061) |
| `SM_ENABLE_DOCS` | `off` in Produktion, sonst `admin` | `off`, `admin`, `public` | API-Doku (SIC-090) |
| `SM_METRICS_TOKEN` | leer = gesperrt | Text | Bearer für `/metrics` |
| `SM_OUTBOUND_ALLOW` | leer | Hosts, IPs, Netze (kommagetrennt, optional Port) | Ausnahmen der Zielprüfung (SIC-098) |
| `SM_DEV_OUTBOX` | 0 (Neubau) | 0/1 | Test-Postausgang; in Produktion verboten |
| `SM_SSO_DEV_MOCK` | 0 | 0/1 | Test-Anbieter; nur Entwicklung |
| `SM_LOAD_DEMO` / `SM_DEMO_PUBLIC` / `SM_DEMO_PASSWORD` / `SM_DEMO_ALL_ACCOUNTS` | 0 / 1 im Modus `demo` / – / 1 | 0/1 | Demo; in Produktion verboten |
| `SM_ADMIN_USER` / `SM_ADMIN_PASSWORD` | `admin` / leer | Name / Passwort nach Regeln | Erst-Admin (SIC-046) |
| `SM_DATA_DIR`, `SM_FILES_DIR`, `SM_BACKUP_DIR`, `SM_DATABASE_URL`, `SM_FRONTEND_DIST` | Datenverzeichnis, `files`, `backups`, SQLite, `frontend/dist` | Pfade/URL | Ablage |
| `SM_LOG_LEVEL` / `SM_LOG_FORMAT` / `SM_ACCESS_LOG` | `INFO` / `json` in Produktion / 1 | Stufe, `json`/`text`, 0/1 | Protokolle (DAT-026) |
| `SM_AUTO_MIGRATE` / `SM_MAINTENANCE_INTERVAL` | 1 / 3600 | 0/1 / Sekunden (min. 5) | Migration beim Start; Wartung |
| `SM_NODE_ID` / `SM_HA` / `SM_THREADPOOL` / `SM_DB_POOL_SIZE` | `main` (≤ 40 Zeichen) / 0 / 40 (min. 8) / 20 (min. 5) | | Mehrknoten und Pools |
| `SM_SSE_PING_SECONDS` | 20 | Sekunden | Keep-alive des Ereignisstroms |

**Anmeldung, Sitzung, Drosselung, Rate-Limit**

| Name | Standard | Bereich | Wirkung |
|---|---|---|---|
| `SM_SESSION_IDLE_MINUTES` | 10080 | Minuten | Leerlauf Schüler/Eltern/Monitor, Obergrenze Personal |
| `SM_SESSION_MAX_DAYS` | 30 | Tage | absolute Dauer; Cookie-Laufzeit |
| `SM_LOGIN_MAX_FAILURES` / `_IP` / `SM_LOGIN_LOCK_MINUTES` | 5 / 30 / 15 | Fehlversuche / Minuten | Drosselung (SIC-091) |
| `SM_REQUIRE_2FA_ROLES` | leer | Rollenliste | 2FA immer Pflicht für diese Rollen |
| `SM_AUTH_CODE_MINUTES` / `SM_LETTER_BATCH_MINUTES` | 15 / 60 | 1–1440 Minuten | Code-Gültigkeit / Brief-Stapel |
| `SM_HIBP_CHECK` | 0 | 0/1 | Leak-Prüfung (SIC-036) |
| `SM_SCRYPT_N` | 32768 | Zweierpotenz, Produktion ≥ 16384 | Hash-Kosten |
| `SM_RATE_LIMIT` / `SM_RATE_IP_PER_MIN` / `SM_RATE_ACCOUNT_PER_MIN` | 1 / 6000 / 1200 | 0/1 / Anfragen je Minute | allgemeines Limit (SIC-095) |
| `SM_OIDC_ISSUER`, `_CLIENT_ID`, `_SCOPES`, `_USERNAME_CLAIM`, `_AUTO_CREATE` (0), `_DEFAULT_ROLE` (`lehrer`), `_LABEL` | leer bzw. angegeben | | Schulkonto (OIDC); Geheimnis `_CLIENT_SECRET` nie dokumentiert |
| `SM_SSO_MICROSOFT_*`, `SM_SSO_GOOGLE_*` (`_HD`), `SM_SSO_APPLE_*`, `SM_OAUTH_GOOGLE_*`, `SM_OAUTH_MICROSOFT_*` | leer | Kennungen; Geheimnisse und Schlüssel nie dokumentiert | Anbieter-Anmeldung und Postfach-Verbindung |

**Dateien, Virenprüfung, Aufbewahrung, Versand, Sicherung**

| Name | Standard | Bereich | Wirkung |
|---|---|---|---|
| `SM_UPLOAD_MAX_MB` | 25 | > 0 bis 10240 MB | Dateigröße |
| `SM_QUOTA_MB_STAFF` / `_STUDENT` | 2000 / 200 | MB (0 = unbegrenzt) | Kontingent |
| `SM_CHAT_QUOTA_MB_STAFF` / `_STUDENT` / `_CHAT`, `SM_CHAT_UPLOADS_PER_10MIN` | 500 / 100 / 1000 / 30 | MB bzw. Uploads (0 = unbegrenzt) | Chat-Bilder |
| `SM_CLAMAV_HOST` / `_PORT` / `_REQUIRED` / `_TIMEOUT` | leer / 3310 / 0 / 30 | Host, 1–65535, 0/1, Sekunden | Virenprüfung (SIC-078) |
| `SM_STUDENT_DOCS_RETENTION_DAYS` / `SM_AUDIT_RETENTION_DAYS` / `SM_KEEP_VERSIONS` | 400 / 365 / 300 (min. 2) | Tage bzw. Versionen | Aufbewahrung (DAT-040) |
| `SM_SMTP_HOST`, `_PORT` (587), `_USER`, `_FROM`, `_TLS` (`starttls`; `ssl`, `none`) | leer | | Konto-Post; `SM_SMTP_PASSWORD` nie dokumentiert |
| `SM_SMS_PROVIDER` / `_URL` / `_ACCOUNT_SID` / `_FROM` / `_TIMEOUT` | leer / – / – / – / 10 | leer, `log`, `webhook`, `twilio`, `seven`; Sekunden | SMS; `SM_SMS_TOKEN` nie dokumentiert |
| `SM_NOTIFY_DISPATCHER` / `SM_MAIL_SYNC` / `SM_MAIL_SYNC_MINUTES` / `SM_WEBHOOK_SECRET` | 1 / 1 / 5 / leer | 0/1, Minuten | Zustellung, Postfach-Abruf, Webhook-Signatur |
| `SM_BACKUP_KEEP` / `SM_AUTO_BACKUP_HOURS` | 30 / 0 | Sicherungen / Stunden | App-Sicherung (SIC-112) |
| `BACKUP_TIMES` / `BACKUP_MAX_AGE_HOURS` / `BACKUP_GPG_PASSPHRASE` / `BACKUP_RCLONE_REMOTE` / `BACKUP_RCLONE_MODE` | `02:30` / 26 / – / – / `copy` | Uhrzeiten / Stunden | Sicherungsdienst |
| `SM_LICENSE_ENFORCE` / `_GRACE_DAYS` / `_CHECK_HOURS` / `_PING_MINUTES` | 0 (Produktion immer 1) / 14 / 24 / 15 | 0/1, Tage, Stunden (min. 1), Minuten (0 = aus) | Lizenz (SIC-127) |

---

## 29 Offene Entscheidungen und Widersprüche (für den Betreiber)

| Nr | Gegenstand | Stand und Vorschlag |
|---|---|---|
| E-01 | 2FA-Standard für Schulleitung, Sekretariat, Planung | Altsystem: Modus „empfohlen“ (Rollen `admin`, `schulleitung`, `sekretariat`); Backlog (10.10.): Pflicht für Administration, Schulleitung, Sekretariat, Planung. Entschieden nur: Administration = Pflicht (SIC-042). Übrige Rollen: Betreiber wählt. |
| E-02 | IP im Audit | Kürzen oder begründen (DAT-028). |
| E-03 | „Alle Rollen alle Rechte“ gegen feste Mindestregeln | Betreiber wünschte (16./17.10.) uneingeschränkte Vergabe; die Mindestregeln (Gesundheit/Administration, Positivliste Schüler/Eltern, Systemrechte) sind hier als Sicherheit vor Komfort fest (SIC-015 bis SIC-019). Der Betreiber bestätigt oder ändert. |
| E-04 | Beobachtung: Einsicht, Erkennbarkeit, Rechtsgrundlage | Einsicht „nur Inhaber“ gegen Recht `watch.read`; Erkennbarkeit für die betroffene Person; Abstimmung mit Personalrat und Datenschutzbeauftragten (DAT-037, DAT-039). |
| E-05 | Vertretung des Inhabers durch einen zweiten Administrator | Bau nicht freigegeben (SIC-022). |
| E-06 | Optionale Leak-Prüfung einschalten | Betreiber entscheidet; Datenschutztexte anpassen (SIC-036). |
| E-07 | Sitzungslaufzeit Schüler/innen und Eltern (7 Tage Leerlauf) | prüfen (SIC-056). |
| E-08 | Update-Dienst mit Container-Zugriff | Alternativen: Zeitplan auf dem Server oder manuell (SIC-126). |
| E-09 | Anmeldeform der Demo | Rollen-Knöpfe ohne Passwort gegen Zugangsdaten je Rolle; „Totaler Quatsch“ (Betreiber 12.10.) gegen Altsystem-Beschreibung 16.10. (SIC-033). |
| E-10 | Konto-E-Mail verschlüsseln | mit HMAC-Suchindex wie Telefonnummer? (DAT-018) |
| E-11 | Chat-Schlüssel beim Abmelden | Gerät entfernen oder Ablage sperren (SIC-086). |
| E-12 | Löschfristen und Landesrecht | Fristen konfigurierbar; Prüfung durch Schule/Schulträger/DSB; Konten-Frist „3 Monate“ (Hinweise/VVT) gegen „zuletzt, nach allen anderen Datenarten“ (Löschkonzept, maßgeblich); Klassenbuch-Aufbewahrung nach Landesrecht (DAT-040, DAT-041). |
| E-13 | Laufende Frist für Chats | im Altsystem keine (DAT-044). |
| E-14 | Zahlenwerte, die der Neubau festlegt | Entpackgrenzen (SIC-071), Alarm-Schwellen (DAT-032), Anzahl/Form der Wiederherstellungscodes (SIC-043), HSTS-`max-age` (SIC-088). |
| E-15 | Mehrere Schulen/zentraler Anmeldepunkt | erst bei der zweiten Schule (SIC-118). |
| E-16 | Schreibende Sicherheitsänderungen am Betrieb | Der Betreiber verlangt vor der Umsetzung von Sicherheits-Fixes eine Auswahl durch ihn (Lehre: 17 Fixe wurden ohne Auswahl umgesetzt); Eingriffe in Live-Konten und Live-Datenbanken nur nach seiner ausdrücklichen Freigabe. |
| E-17 | Widerspruch W8/Z2 zur zweistufigen Anmeldung | gilt Z2/I10 (SIC-044). |
| E-18 | Vorfall 16./17.10. | Ursache und Herkunft der Anmeldung vom 16.10. 21:49 sind in den Quellen nicht aufgeklärt; dieses Dokument verwendet ihn nur als Lehre (SIC-021, SIC-139). |
| E-19 | Rechtsprüfung | Alle Texte zu Datenschutz, DSFA, Verzeichnis, Löschfristen und Beobachtung sind Entwürfe; juristische Prüfung steht aus (SIC-011, SIC-138). |

Abgrenzung: Funktionen von Chat, Anmeldung, Rollenkatalog, Betrieb/Lizenz, Barrierefreiheitserklärung und Rechtsdokumenten stehen in den Dateien NAC, ANM, REC, BET, OBE, REH; diese Datei legt nur die Schutzwerte und Prüfungen fest.

---

## 30 Zählung

- Anforderungen: 202 (SIC-001 bis SIC-145 = 145; DAT-001 bis DAT-057 = 57). Priorität: P0 = 200, P1 = 2 (SIC-022, SIC-036).
- Stand: `Status: Ist` = 128, `Status: offen` = 74 (Teilstände stehen im Kopf der jeweiligen Anforderung). Jede Anforderung hat genau eine Abnahme-Zeile.

<!--ENDE-->
