# 10 Roadmap: offene Punkte (Schulpuls-Neubau)

Stand der Quellen: 2026-10-18 09:10 (neueste Gesprächsquelle G6, Stand 17.10. abends). Diese Datei listet alles, was im Ist-Stand **nicht** gebaut ist, bereinigt um Doppelungen und um alles, was laut neuestem Stand (G6) inzwischen gebaut ist. Der Neubau muss den gebauten Stand ohnehin vollständig erreichen (siehe die übrigen Dateien des Pakets); diese Roadmap ordnet die **darüber hinaus offenen** Anforderungen nach Priorität und Reihenfolge.

## 0. Lesehilfe

**Kennungen.** Format `<KÜRZEL>-<nnn>`. Die Nummern dieser Datei liegen je Kürzel im Kreis **901 bis 999**, damit sie nie mit Anforderungen der Hauptdateien (Nummern ab 001) kollidieren. Jeder Eintrag trägt `Status: offen`.

**Priorität.**

| Stufe | Bedeutung |
|---|---|
| P0 | Pflicht: Sicherheit, Datenschutz, Recht, Betriebs-Pflichten vor jedem Einsatz bei einer echten Schule |
| P1 | Kernfunktion bzw. ausdrücklicher Betreiber-Wunsch mit hohem Alltagsnutzen; Lücken, ohne die die Schule nicht „wirklich damit arbeitet“ |
| P2 | wichtig: Wettbewerbs-Lücken mit hohem oder mittlerem Nutzen, Optimierungen, Qualitätsarbeit |
| P3 | Wunsch / später / nur auf Nachfrage / niedriger Nutzen |

**Aufwand** (Größenordnung für ein Bau-Team, Quellenangaben unverändert übernommen): S = bis 1 Tag, M = 2 bis 5 Tage, L = 1 bis 3 Wochen, XL = über 3 Wochen.

**Herkunft.** `Betreiber` = Wunsch oder Aussage des Betreibers (Zitate wörtlich, Datum 2026 als MM-TT); `Claude` = Vorschlag, Befund oder Prüfung des Assistenten/der Prüf-Agenten (Audit, Bewertung, Code-Durchsicht); `Wettbewerb` = Funktionslücke aus den Marktvergleichen. Kombinationen sind möglich.

**Abhängigkeiten** verweisen auf Kennungen dieser Datei oder auf Bereichs-Kürzel der Hauptdateien (z. B. „REC-Basis“ = Rechte-Grundmodell).

**Abnahme** = genau eine prüfbare Zeile (Zustand/Eingabe → erwartetes Ergebnis, mit Rechte- bzw. Fehlerfall, wo einschlägig).

**Gestaltungsregeln, die für jeden Eintrag mitgelten** (nicht je Eintrag wiederholt): Anrede „Sie“ für alle inkl. Schüler/innen; Erklärungen nur über Hilfe-Symbol (i), keine Erklär-Absätze; ein gemeinsames Raster für jede Tage×Stunden-Ansicht; App-Dialoge statt Browser-Popups; fremde Daten liefern 404; jede schreibende Aktion wird protokolliert (ohne Inhalte); Freitexte verschlüsselt; Produktname nur an einer Stelle konfigurierbar; Sicherheit und Datenschutz vor Komfort.

**Zeitangaben.** Protokoll-Zeiten sind UTC; Chat-Zeiten der Quellen wirken UTC-basiert (lokal +2 h).

## 1. Wellenplanung

Reihenfolge: erst Pflicht (Sicherheit/Recht/Betrieb), dann Kern-Alltag, dann Kommunikation mit Eltern, dann Anbindungen und Skalierung, zuletzt Ausbau. Innerhalb einer Welle zuerst die Einträge ohne Abhängigkeiten. Die Wellen 2 bis 4 setzen die Freigabe des Betreibers voraus (Entscheidung E-02), weil er die Wettbewerbs-Kleinfunktionen am 10-16 14:49 ausdrücklich nur als Liste wollte: „die Sachen noch nicht einbauen, erst mal mir sagen, es sind wirklich nur so kleine Sachen.“

### Welle 0: Pflicht vor jedem Einsatz bei einer echten Schule (alle P0)

| Block | Inhalt | Kennungen |
|---|---|---|
| 0.1 Betrieb | Produktivmodus für alle Kundeninstanzen; Lizenzprüfung nicht abschaltbar; Demo-Konten und Test-Postausgang; Schlüsselablage; HTTPS-only; SSH-Erreichbarkeit | BET-901 bis BET-905, BET-920 |
| 0.2 Konten und Zugriff | Inhaber-Schutz zentral; 2FA-Pflicht für Admins samt Wiederherstellungscodes; SSO mit 2FA; Client-IP hinter Proxy (IPv6/VPN); Vorfall-Nachbereitung | REC-901, REC-910, ANM-901, ANM-902, ANM-903, ANM-915 |
| 0.3 Schutz vor Datenabfluss | Default-Deny; Stammdaten-Exporte; API-Tokens; CSV-Formelschutz; Live-Ströme; Massenzugriffs-Alarm; Familienzugriff nach Volljährigkeit; Notenbuch-Scopes; Import-Grenzen; Mail-/Lizenzserver-Prüfung; Chat-Schlüssel nach Abmeldung entfernen; Hausaufgaben-Abgaben untereinander unsichtbar | SIC-901 bis SIC-908, INT-901 bis INT-903, NAC-908, KUR-901 |
| 0.4 Datenschutz und Recht | Auskunft, Löschfristen, Pseudonymisierung, IP-Speicherung, Datenpannen-Prozess, Beobachtungsfunktion; Datenschutztexte abgleichen; Barrierefreiheitserklärung; Rechtsprüfung; Namens-/Markenrecht | DAT-901 bis DAT-906, REH-901 bis REH-903, REH-905, REH-906 |
| 0.5 Nachweis | Pentest wiederholen und erweitern (nach 0.2 und 0.3) | SIC-909 |
| 0.6 Fachbereichs-Härtung | Pakete und Plan-Stände schützen; Druckansicht und Monitor schützen; Rechte der Aufsichten, Klausur-Datenweg, Protokoll (vor dem Re-Test 0.5) | STP-914, VER-909, VER-911 |

Abnahme der Welle 0: alle P0-Einträge bestanden; Re-Test (SIC-909) ohne offenen Fund der Stufen hoch oder kritisch; Betreiber hat die Entscheidungen E-03 bis E-10 getroffen.

### Welle 1: Kern-Alltag und Fehlerbehebung (P1)

| Block | Inhalt | Kennungen |
|---|---|---|
| 1.1 Fehlerbehebung (frühere „Welle 2“ des Altprojekts, 14 Pakete) | Plan-Übernahme, Vertretungs-Nebenläufigkeit, Notenbuch, Kompetenzen, Klausuren/Nachholtermine, Formulare, Schüler/Eltern, Rechte-Konsistenz, Regel-Vorlagen, API-Zugänge, Benachrichtigungen | STP-902, STP-920, VER-913, NOT-902, NOT-909, NOT-914, FOR-904, SCH-910, REC-904, INT-904, BEN-911 |
| 1.2 Klassenbuch und Fehlzeiten | Klassenbuch Stufe 2, Erinnerung an offene Stunden, Beurlaubungs-Entscheidung, Nachteilsausgleich | KLB-901, KLB-903, KLB-907, NOT-911 |
| 1.3 Benachrichtigungen | Systemabsender, Glocke für Nachrichten, Nachschreiben/Beurlaubung/Volljährigkeit, Neutral-Mail, Mail/SMS in der Oberfläche | BEN-901 bis BEN-905, BEN-908, BEN-909 |
| 1.4 Vertretung und Lehrkräfte | Qualifikation, Material bei Abwesenheit, Vertretungskonto, Deputat nur als Wunsch | VER-901, VER-903, VER-904, VER-910, LEH-906 |
| 1.5 Konten und Rechte | Passwortregeln, Spraying-Erkennung, Delegation Inhaber-Reset, nicht erzwungene Rechte, Schulbegleitung, Ausbilder-Rolle | ANM-904 bis ANM-906, ANM-914, REC-902, REC-903, REC-906, SCH-905, SCH-908 |
| 1.6 Bedienung und Barrierefreiheit | Raster per Tastatur/Touch, Barrieren beheben, Kopfleiste, Produktname konsistent | STP-901, OBE-901, OBE-902, OBE-909 |
| 1.7 Zugangsbriefe, Nachrichten | Einmal-Login, Lese-Status, Moderation, Rundschreiben | FOR-901, NAC-901, NAC-907, NAC-913 |
| 1.8 Import und Betrieb | Import-Oberfläche, Untis-Rundlauf, Update-Dienst, Restore-Test, Backups, DB-Rollen | INT-905, INT-914, BET-906 bis BET-909 |
| 1.9 Datenschutz-Werkzeuge | Zwei-Personen-Freigabe, Auskunftsfristen, VVT, Landesrecht, Minimierung | DAT-907 bis DAT-911, REH-904, REH-907 bis REH-909, SIC-910 |
| 1.10 Qualität | Browser-Rundgänge je Rolle, Gesamttest, Lasttest, Marktreife-Checkliste | QUA-901 bis QUA-907, QUA-912 |
| 1.11 Stammdaten | Ausbildungsbetriebe | STA-911 |

### Welle 2: Kommunikation mit Eltern, Komfort (P2, mit Freigabe E-02)

Reihenfolge laut Marktvergleich und Betreiber-Liste: 1. Lese-Status (NAC-901, schon in Welle 1), Stundenplan-PDF (STP-918), Hausaufgaben-Übersicht (SCH-903); 2. Elternbriefe (NAC-902) mit Push/PWA (BEN-907) und Übersetzung (NAC-903); 3. Elternsprechtag und Sprechstunden (SCH-901, SCH-902); 4. Schnellsuche, Tastenkürzel, Feedback-Knopf (OBE-903, OBE-904); 5. Nachrichtenvorlagen, Ruhezeiten, Terminumfrage (NAC-905, NAC-906, NAC-917); 6. Kalender-Abo je Rolle/Kind (SCH-904); 7. Klassenbuch-Ausbau, schnelle Anwesenheit, Entschuldigungs-Einstellungen (KLB-904 bis KLB-906); 8. Vertretungs-Ausbau (VER-905 bis VER-908); 9. Notenbuch- und Kompetenz-Ausbau (NOT-903, NOT-904, NOT-910, NOT-912, NOT-913).

### Welle 3: Anbindungen und Skalierung (P2)

Landes-Login und Schulconnex (ANM-910, INT-910), LTI (INT-909), OneRoster/SCIM (INT-911, INT-912), GPU-Dateien und Landes-Exporte (INT-906, INT-918), Import-Ausbau (INT-915 bis INT-917), Module ein/aus und Preismodell (STA-901, BET-919), Zahlungen (BET-911), Statusseite (BET-910), Skalierung (BET-914), Lizenzserver-Hosting (BET-912).

### Welle 4: Ausbau zum Komplettprodukt (überwiegend P3)

Raum-/Gerätebuchung (STP-926), Oberstufe, Epochen, Wahlfächer, Abteilungsplanung (STP-921 bis STP-924), Zeugnis-Module (NOT-905 bis NOT-908), Ganztag und Schülerakte (SCH-909, SCH-911), Wertrechnung (LEH-905), Moodle-Kleinteile und weitere Kursraum-Funktionen (KUR-907 bis KUR-919), mehrere Server/HA (BET-913), Mischaltersgruppen (STP-908, STA-907).

## 2. Offene Entscheidungen des Betreibers

Format: Frage · Optionen · Empfehlung (Empfehlungen sind Vorschläge, keine Beschlüsse) · betroffene Einträge. Kein Eintrag dieser Liste wurde in den Quellen vom Betreiber beantwortet.

**E-01 Produktname.** Der Arbeitstitel „Schulpuls“ wird im Bildungsbereich bereits von einem anderen Unternehmen genutzt (Website, Lern-App; Verwechslungsgefahr hoch; keine Rechtsberatung). Optionen: (a) behalten; (b) Schulhafen; (c) Schulfeld; (d) Schulfunke; (e) Schultor/Schulkern/Schulkreis; (f) Schulwelle (in einer Prüfung als aussichtsreichster genannt, in der Vorschlagsliste nicht geführt). Wunsch des Betreibers: Name mit „Schule“ oder Teilen davon. Empfehlung: intern „Schulpuls“ als Arbeitstitel, nach außen erst nach anwaltlicher Markenrecherche (DPMA, EUIPO, WIPO) einen freien Namen (Vorschlag Schulhafen), Domain beim Registrar sichern; ebenso Abstand zum Namen „Schulmanager Online“ klären. Betrifft REH-906, OBE-909.

**E-02 Freigabe der Ausbau-Pakete.** Die Wettbewerbs-Kleinfunktionen (10) und die früheren Wellen 2 bis 4 wurden vom Assistenten zur Umsetzung eingeplant, vom Betreiber aber nur als Liste gewünscht. Optionen: (a) alles freigeben; (b) einzeln freigeben; (c) nur Pflicht (Welle 0/1) jetzt. Empfehlung: (b), Reihenfolge laut Welle 2. Betrifft alle P2-Einträge der Bereiche NAC, SCH, OBE, KLB, VER.

**E-03 Sicherheitswelle freigeben.** Die drei live bestätigten hohen Lücken (Inhaber-Schutz auf allen Wegen, Stammdaten-Exporte, API-Tokens) wurden am 10-17 16:53 vorgeschlagen, ohne Freigabe. Optionen: ja / nein / teilweise. Empfehlung: ja, vollständig und sofort (Welle 0). Betrifft REC-901, INT-901, INT-902.

**E-04 Zwei-Faktor für Admins.** Heute nur empfohlen, Wiederherstellungscodes fehlen. Optionen: Pflicht für Administration; Pflicht für Administration, Schulleitung, Sekretariat, Planung; Pflicht für alle Personal-Rollen. Empfehlung: Pflicht für Administration, Schulleitung, Sekretariat, Planung (Lehrkräfte einstellbar). Betrifft ANM-901.

**E-05 Delegation des Inhaber-Passwort-Resets.** Wortlaut (10-17 18:02): „Dem Admin soll man grundsätzlich nicht seine Admin-Rechte nehmen können. … Es sei denn, es gibt einen zweiten Admin, dem der erste Admin den Zugang gegeben hat, seinen Password zurückzusetzen.“ Der Assistent fragte zweimal „Soll ich das bauen?“. Optionen: bauen; nicht bauen. Empfehlung: bauen, mit Zusatzschutz (nur ausdrückliche Vergabe durch den Inhaber, jederzeit widerrufbar, Benachrichtigung des Inhabers, Protokoll), erst nach REC-901. Betrifft REC-902.

**E-06 Passwortregeln.** Mindestlänge je Rolle (Code: 8; Quellen nennen für Lehrkräfte teils 10) und Prüfung auf geleakte Passwörter (eingebaut, aus; Online-Abfrage bei Dritten wurde bewusst nicht gewählt). Optionen: nur Offline-Liste (mindestens 3000 Einträge); Online-Prüfung mit Hash-Präfix, abschaltbar; keine. Empfehlung: Offline-Liste, Online-Prüfung nur als abschaltbare Option; Mindestlänge 10 für Personal, 8 für Schüler/innen und Eltern. Betrifft ANM-905.

**E-07 Beobachtete Konten.** Zweck, Rechtsgrundlage, Information der betroffenen Person, Speicherdauer (180 Tage) und Erkennbarkeit sind ungeklärt; ob bei beobachteten Konten auch Chat-Nachrichten erfasst würden, ist offen. Optionen: nur Test-/Demo-Konten mit schriftlicher Information; zusätzlich echte Personen mit Einwilligung; abschaffen. Empfehlung: nur Test-/Demo-Konten mit Information, Chat-Inhalte nie erfassen. Betrifft DAT-906.

**E-08 Vorfall vom 16.10. und Konten.** (a) Waren Sie die Anmeldung als Konto „monitor“ am 16.10. 21:49 von außerhalb des Netzes? (b) Soll das von Ihnen selbst angelegte, herabgestufte und deaktivierte Konto wieder aktiv und Admin sein? (c) Soll das Konto „betatester“ bleiben oder gelöscht werden? Empfehlung: (a) beantworten, bei „nein“ Passwörter von Administration und Monitor ändern und alle Sitzungen beenden; (b) nur mit 2FA reaktivieren; (c) nach Ende des Betatests löschen. Betrifft ANM-915.

**E-09 Betriebsmodus und Pilot.** Hauptserver, Demo und Test-Instanz laufen im Entwicklungsmodus. Optionen: sofort umstellen (Test-Instanz zuerst); Hauptinstanz bleibt Demo und die erste echte Schule bekommt eine eigene Instanz im Produktivmodus. Empfehlung: beides (Vorschlag aus der Produktreife-Prüfung). Betrifft BET-901.

**E-10 HTTP im Heimnetz.** Der Hauptserver erlaubt HTTP im Heimnetz (Cookies ohne Secure-Kennzeichen). Optionen: HTTP abschalten; Heimnetz-Adresse automatisch auf die Domain umleiten; so lassen. Empfehlung: abschalten bzw. umleiten (Sitzungen sind an die Adresse gebunden, Konten „verschwinden“ beim Wechsel). Betrifft BET-905.

**E-11 Notenbuch-Einsicht (Standard).** Vier Modi: gar nichts, alles sofort, erst nach Freigabe, nur Endnote. Die Quellen führen „nach Freigabe“ einmal als Entscheidung, einmal als offen. Empfehlung: Standard „nach Freigabe“, Wahl in der Einrichtung erzwingen. Betrifft NOT-901.

**E-12 Audit-Ausnahmen.** Dürfen ohne Audit bleiben: Löschen eigener Benachrichtigungen, Zwischenspeichern von Selbsttest-Antworten, einzelne gesendete Chat-Nachrichten und „gelesen“-Markierungen (datenschutzbedingt)? Empfehlung: ja, in der Datenschutzdokumentation ausdrücklich festhalten. Betrifft DAT-906, REH-903.

**E-13 Chat-Moderation und Ende-zu-Ende.** Gemeldete Nachrichten brauchen Klartext. Optionen: Melder gibt die gemeldete Nachricht frei (Klartext geht nur an die Moderation); Server-Schlüsselhinterlegung; keine Moderation. Dazu: Chat-Textkompression (vom Betreiber gewünscht, vom Assistenten als nicht lohnend abgelehnt) und weggelassene GIF-Suche bestätigen. Empfehlung: Freigabe durch den Melder; Kompression nicht bauen; keine Drittanbieter-GIF-Suche. Betrifft NAC-907.

**E-14 Monitor-Menü.** Der Menü-Knopf ist bewusst kaum sichtbar (Konflikt mit Auffindbarkeit/Tastatur/WCAG). Optionen: sichtbar lassen kaum erkennbar; erkennbar mit Fokusring und Tastaturzugang. Zusätzlich: Genügt „andere Schulansicht“ nur für Monitor-Konten ohne festen Standort? Empfehlung: erkennbar und per Tastatur erreichbar; Standortbindung beibehalten. Betrifft VER-910.

**E-15 Rechte-Fragen.** (a) Darf die Rolle Schulleitung den Generator starten (heute nur Planung)? (b) Darf das Sekretariat Anträge der Lehrkräfte genehmigen (heute Planung, Schulleitung, Admin)? (c) Regel „Elternkonten zurücksetzen nur Sekretariat/Schulleitung/Admin“ bestätigen. Empfehlung: (a) ja über Rechte-Schalter, Standard aus; (b) ja über Schalter, Standard aus; (c) bestätigen. Betrifft REC-908, LEH-902.

**E-16 Minderjährige.** (a) Altersgrenze 18 und „Schüler/innen unter 18 melden nicht selbst“ bestätigen. (b) Soll „Meine Fehlzeiten“ (nur lesen) für Minderjährige bleiben (Betreiber 10-12 19:08: „Sollte Ansichten sind komplett unnötig für die Kinder“)? (c) Sollen Klassenbuch-Thema und Hausaufgabentext für Schüler/innen/Eltern sichtbar sein (heute ausgeblendet)? Empfehlung: (a) bestätigen; (b) für Minderjährige ausblenden, Eltern sehen; (c) Hausaufgaben sichtbar (Kursraum), Thema sichtbar, Notizen nie. Betrifft SCH-910, KLB-901.

**E-17 Eltern volljähriger Kinder.** Rundschreiben an volljährige Schüler ohne Wahl: nur Schüler oder beide? Empfehlung: an beide, bis der Schüler entscheidet. Betrifft NAC-913.

**E-18 Anzeige und Zählung.** (a) Samstag/Sonntag im Raster immer oder nur bei Terminen (Betreiber: „wenn da auch Events sind“; gebaut: immer)? (b) Schuljahr-Zählung „ab Woche 1 des Kalenderjahrs“: genügt Anzeige in Kalenderwochen mit interner fortlaufender Zählung? Empfehlung: (a) Standard nur bei Terminen, Schalter „immer“; (b) bestätigen. Betrifft STP-919.

**E-19 Planung.** (a) Reihenfolge der Planungs-Reiter: „Plan prüfen“ vorn, Qualitätsbericht als zweiter, oder beides in einem Reiter. (b) Sollen Plan-Vorschläge eine Empfehlung tragen (bisher bewusst nicht)? (c) Bleibt der frühere Auto-Planer (Neuplanung ohne Auswahl, mit Abschaltschalter) im Neubau? Betreiber-Grundsatz (10-12 20:53): „Menschen mögen es lieber, eine Auswahl zu haben.“ Empfehlung: (a) ein Reiter mit Unterbereichen; (b) Empfehlung als Markierung mit Warnung bei Verschlechterung, Entscheidung beim Menschen; (c) nein, nur Vorschlagspakete. Betrifft STP-912, STP-913.

**E-20 Push und App.** Der Betreiber hat die App-Option 10-13 zurückgestellt („die app option mus noch nicht mit rein“), die Marktvergleiche reihen Push/PWA an erste Stelle. Optionen: PWA mit Web-Push (Opt-in); native App; weiter zurückgestellt. Empfehlung: installierbare PWA mit Web-Push nach Welle 1; „kein Drittanbieter“ für Browser-Push-Dienste klären. Betrifft BEN-907.

**E-21 Landes-Anbindung.** Landes-Login (Schulconnex/VIDIS) gilt nach Recherche (ungeprüft) als Voraussetzung für den Verkauf in NRW, Niedersachsen und Sachsen; Landes-Exporte: welche Länder zuerst (BY, NI, SN, ST, NRW, HE, BW)? Empfehlung: NRW zuerst (Zielmarkt), Landes-Login vor dem ersten Verkauf in NRW; OIDC-Claims und Backchannel-Logout zuerst (kleiner Aufwand). Betrifft ANM-910, INT-910, INT-918.

**E-22 Eltern-Kommunikation (groß).** Elternbriefe, Elternsprechtag (Schüler-Zugang für parallele Gespräche?), Briefübersetzung (Dienst: lokal, EU-Anbieter mit AV-Vertrag, aus), Einwilligungsalter. Empfehlung: Reihenfolge Briefe vor Sprechtag; Übersetzung als abschaltbares Modul mit lokalem oder EU-Dienst; Namen von Kindern nicht übertragen; Einwilligungsalter gesetzlich prüfen lassen. Betrifft NAC-902, NAC-903, SCH-901.

**E-23 Bewusst nicht gebaute Funktionen.** Quiz-System, SCORM, Videokonferenz, Plagiatsprüfung, KI-Assistenz, Bezahlfunktionen für Eltern, Plugin-Markt, Zeugnisdruck: bestätigen oder doch gewünscht? Empfehlung: bestätigen; Quiz/H5P nur per Link oder LTI, Videokonferenz nur als signierter Link (Schul-BBB), Zeugnisdruck bleibt in SchILD/ASV. Betrifft KUR-913, INT-909.

**E-24 Module und Preismodell.** Module einzeln ein/aus (Wettbewerber verkaufen Module) oder ein Preis ohne Modul-Staffel; Quellen widersprechen sich. Empfehlung: Module technisch vorsehen (STA-901), Preis zunächst ein Paket je Schule. Betrifft STA-901, BET-919.

**E-25 Update-Dienst.** Der Update-Dienst braucht Docker-Zugriff (praktisch Root). Optionen: Dienst mit Docker-Zugriff; Zeitplan direkt auf dem Server (Host-Job); nur manuelle Updates. Verteilung: Download vom Lizenzserver oder eigene Registry (ab rund 10 Schulen). Empfehlung: Host-Job ohne Container-Rechte, Download vom Lizenzserver. Betrifft BET-907.

**E-26 Lizenzserver und Mehrserver.** Hosting: Heimserver (Ausfallpuffer 7 Tage normal, danach 14 Tage nur lesen) oder externer Hoster. Mehrere Server je Schule: erst anbieten, wenn einmal echt durchgespielt. Empfehlung: externer Hoster ab dem ersten zahlenden Kunden; Mehrserver später. Betrifft BET-912, BET-913.

**E-27 Zahlungen.** Stripe (Karte) und GoCardless (SEPA) sind vorbereitet, aber nicht aktiv (Konten/Schlüssel legt der Betreiber an); automatische Pause bei Zahlungsverzug ist aus. Optionen: aktivieren / nur Rechnung und Überweisung / später. Empfehlung: zunächst Rechnung und Überweisung, Anbieter erst bei Bedarf; Pause-Frist vom Betreiber festlegen, Standard aus. Betrifft BET-911.

**E-28 Code-Schutz und Patent.** Wunsch: Schulen sollen den Code nicht entschlüsseln können, „patentiert“. Technisch nur Erschwernis möglich. Optionen: gehostetes Angebot statt Auslieferung; kompiliertes Python mit Nuitka für Kernteile; EULA mit Anwalt; Kunden-Wasserzeichen; Patentanwalt. Empfehlung: EULA durch Anwalt, nicht abschaltbare Lizenzprüfung, Wasserzeichen, Patentanwalt befragen (Software-Patente in der EU schwierig). Betrifft REH-907.

**E-29 Demo.** (a) Wer gibt Demo-Zugänge aus: nur der Inhaber (gebaut) oder auch Schulen (Wortlaut 10-12: „dass die Schule Demo-Accounts rausgeben können oder der, also ich, der Software-Inhaber“)? (b) Rollen-Knöpfe ohne Passwort auf der Demo-Anmeldeseite (Betreiber 10-12 14:16: „Totaler Quatsch“; später als Demo-Verhalten beschrieben): gelten lassen? (c) Demo-Hosting durch Schulen. Empfehlung: (a) nur Inhaber; (b) nur auf der Demo-Instanz, nie im Produktivmodus; (c) später. Betrifft BET-915.

**E-30 Klassenleitungen.** Mehrere Klassenleitungen je Klasse und weitere Klassenrollen (Stellvertretung, Klassensprecher, Verwalter, Abteilungsleitung) von Anfang an im Datenmodell? Empfehlung: ja (Betreiber-Anforderung A-42, A-43); sonst entstehen Folgeänderungen in Kursräumen, Selbstbereich, Klassenkonten, Rechten, Löschweitergabe. Betrifft STA-908.

**E-31 Produktumfang großer Module.** Entscheidung je Modul, ob und wann: Zeugnis-Module (nur Daten zuliefern oder Kopfnoten/Konferenz/LEG), Ganztag (Rechtsgrundlage für Verhaltens-/Beobachtungseinträge), Schülerakte-Kategorien, Mensa/Speiseplan, Notfallbenachrichtigung, Wahlfach-/AG-Zuteilung, Oberstufenplanung (Zielgruppe Oberstufe oder Berufskolleg), Wertrechnung/Deputat, Abteilungsplanung, Mehrarbeit nach KMBek (nur Bayern). Empfehlung: Fokus NRW; Zeugnis nur Daten zuliefern; die übrigen auf Nachfrage. Betrifft NOT-905 bis NOT-908, SCH-909 bis SCH-912, STP-921 bis STP-924, LEH-905.

**E-32 Lehrkräfte-Verwaltung.** (a) Lehrkraft-Arbeitstage/Einchecken/Mindeststunden verfolgen (Mitbestimmung, Personalrat prüfen)? (b) Fortbildungsanträge, Einzelprofil-Seite? (c) Höchststunden: aus dem Lehrkraft-Profil entfernen oder als genehmigungspflichtigen Wunsch behalten? Empfehlung: (a) nein bis rechtlich geprüft; (b) später; (c) als Wunsch mit Genehmigung. Betrifft LEH-901, LEH-903, LEH-906.

**E-33 Design-Richtung.** Referenzprodukte nennen (Vorschläge: Linear, WebUntis-App, Notion) und die Seite mit dem meisten „Text-Müll“ benennen; Phase 2 des Stylesheet-Umbaus (rund 310 Dateien) nur bei Nutzen. Das Mockup „Rehaul“ wurde abgelehnt („komplett grauenhaft“); Lehre: erst Referenzen, keine Spielzeug-Mockups. Empfehlung: Referenzen festlegen, bevor der Neubau die Oberfläche gestaltet. Betrifft OBE-908.

**E-34 Vertrieb und Markt.** Vertriebsweg und Freigabe der Anschreiben (Werbung nur mit Einwilligung oder persönlicher Einzelanfrage, § 7 UWG, rechtlich ungeprüft), Pilotschule, Ziel des Businessplans („um sich wo zu bewerben“ – wo?), Support-Modell, Hosting-Angebot. Empfehlung: persönliche Einzelanfrage und Schulträger; Pilotschule mit eigener Instanz. Betrifft REH-909, QUA-912.

**E-35 Aufbewahrungsfristen.** Voreinstellung (Gesundheitsdaten, Nachrichten, Benachrichtigungen 30 Tage; Abgaben und Formulare 90 Tage; Noten und Lernstand 180 Tage; Klassenbuch-Anwesenheit 1 Jahr; Audit-Log 1 Jahr; API-Protokoll 90 Tage; Beobachtungsprotokoll 180 Tage) bestätigen; Klassenbuch-Archiv-Frist (Backlog: 10 Jahre) gegen Landesrecht prüfen. Empfehlung: als änderbare Voreinstellung bestätigen, Landesrecht (VO-DV I NRW) prüfen lassen, „0“ verbieten. Betrifft DAT-902, DAT-908, KLB-901.

**E-36 Datenschutzrichtlinien und Rechtsprüfung.** Richtlinien für Chat und Gesundheitsdaten festlegen (Betreiber: „die du noch festlegen musst“); externe Prüfung von Datenschutz-Folgenabschätzung, Mustertexten, AV-Vertrag, Löschfristen durch Schule/Schulträger oder Datenschutz-Fachperson. Empfehlung: Fachperson beauftragen, Vorlagen bis dahin als „Entwurf“ kennzeichnen. Betrifft REH-901, REH-905.

**E-37 Anmeldedienste je Zielgruppe.** Google-/Apple-Anmeldung für Schüler/innen? (Empfehlung des Assistenten: nein, nur Personal und Erwachsene; Landes-Login bevorzugt.) Apple verlangt Entwicklerkonto (99 $ bzw. 99 € je Jahr) und Standardport 443. „Automatische Anmeldung“ standardmäßig aus bestätigen. Empfehlung: Google/Microsoft für Personal, Apple nur bei Bedarf. Betrifft ANM-913.

**E-38 Arbeitsweise (Altprojekt).** Auswahl der Skills, die in jedem Workflow aktiv sein sollen; Strix ausführbar machen (Docker und CLI oder Schlüssel); Plugin-Installationen selbst ausführen; weitere Anbieter-Schlüssel selbst anlegen. Empfehlung: Auswahl frontend-design, owasp-security, sentry-security-review, gdpr-dsgvo-expert; Strix erst mit festem Einsatzzweck. Betrifft PRI-901 bis PRI-903.

**E-39 Heimserver-Reste (nicht Produkt).** Minecraft-Live-Verzeichnis löschen? Sammel-Skript (jede Minute) beenden? Server-Reste (ungenutzte Schlüsseldatei, vier verwaiste Docker-Volumes, Test-Image, rund 1,5 GB Build-Cache) entfernen? Graph-Server/Klon-Server beenden? Empfehlung: Reste entfernen, Skript nach Auswertung der Beta-Rückmeldung beenden. Betrifft BET-917, PRI-904.

**E-40 Hosting großer Schulen und Domain.** Heimanschluss ist für rund 5.000 Schüler zu klein (Lastspitze rund 190 Anfragen/s, Upload mindestens 50 Mbit/s); eigene Domain ohne Portnummer (Tunnel) und Subdomain je Schule. Empfehlung: Hoster-Angebot ab mittlerer Schulgröße; Subdomain je Schule mit zentralem Anmeldepunkt erst bei der zweiten Schule. Betrifft BET-918, ANM-909.

## 3. Abgleich mit dem Ist-Stand: nicht aufgenommen (bereits gebaut, Stand G6)

Folgendes ist laut neuestem Stand gebaut und steht deshalb **nicht** in dieser Liste (Pflicht für den Neubau über die Hauptdateien): Planungsdokument/Versionen/JSON-Backup verschlüsselt; Monitor-Menü; 404-Regel für fremde Daten; Zuschauer-Rolle mit 26 Rechten; Anmelde-Härtung (gestaffelte Wartezeit, SSO-Cookie verschlüsselt, Zeitschutz bei unbekannten Namen); Chat-Geräteschlüssel im sicheren Browser-Speicher; Audit-Lücken (Chat-Verwaltung, Download, Wartung, Lizenzprüfung); Doppelklick-Schutz (Chat, Formulare); Einrichtung in 12 Schritten mit Tabelleneingabe; Impressum/Datenschutz-Seiten und Betreiber-Hilfe; Rechte frei vergebbar, eigene Rollen; Inhaber-Schutz auf direktem Weg; Demo-Konten für alle Rollen; beobachtete Konten; API-Zugänge mit Schreibzugang und API-Protokoll; Lizenzmodell mit Schlüsseln je Server, signierte Antworten, Anbieter-Portal, Tarife/Rechnungen, Update-Verwaltung (Server-Seite), Demo-Sperre im Produktivmodus; Passwortregeln (8 Zeichen, Name nicht enthalten, rund 120 verbotene Passwörter); Notenbuch, Kompetenzraster, Lernstand, Lernplan, Abzeichen; Kursraum-Aufgaben, Gruppen, bedingte Freigabe, Papierkorb; Formular-Baukasten; Schuljahreswechsel mit Vorschau und Rückgängig; Löschkonzept, Auskunft als ZIP; Import aus Moodle/OneRoster/WebUntis/SchILD/ASV; Nachrichten als ein Bereich; Glocke mit Einstellungen; Kontowechsel (bis 5 Konten); Passwort vergessen; Regelkatalog mit 11 Regeln und 9 Schultyp-Vorlagen; Plan prüfen mit Varianten; Klausur-Limits; Nachschreibtermine mit Vorschlägen; Fehlzeiten-Statistik mit Ampel; Beurlaubung; Vertretung automatisch aus Krankmeldungen mit Begründung und Fairness; Pausenaufsicht-Ansichten; Verfügbarkeit mit Rhythmus und Gilt-ab; Pendelregeln; Ferienimport; Kalenderwochen-Anzeige; Jahrgänge/Bildungsgänge frei anlegbar; Mandantentrennung; Browser-Zeitgrenze 30 s; Netzschutz für ausgehende Abrufe; Produktname als Konstante, Sie-Form, App-Dialoge, (i)-Hilfen.

Beim Aufbau von Abschnitt 4 zusätzlich als gebaut erkannt und deshalb nicht aufgenommen (Stand G6/G5): Ausführen und Rückgängig des Schuljahreswechsels laufen ganz oder gar nicht; Plan-Prüfen-Vorschlagspakete mit Varianten und Freigabemodus der Vertretung; Standortcheck und Wochen-/Tagesansicht der Pausenaufsichten; Kompetenzraster, Lernstand, Lernplan und Abzeichen; Klausur-Limits je Schule, Jahrgang und Klasse; Passwort-Reset durch die Klassenleitung; Chat-Archiv pro Person; Lizenzschlüssel im Anbieter-Portal anzeigbar (verschlüsselt gespeichert); Plan-Stände und Zeiträume (Halbjahre); Moodle-Importer (nur an Beispieldaten belegt, siehe INT-915); automatische Kennzeichnung der Mails als automatisch mit Abmeldelink; Hausaufgaben-Marken im Raster.

Nicht aufgenommen wurden außerdem bewusst abgelehnte oder zurückgenommene Dinge: harte Kontosperre je Benutzername (ersetzt durch gestaffelte Wartezeit), Lizenzdatei mit Ablaufdatum (verworfen), „altes Startpasswort wieder gültig“, Schnellauswahl in der Arbeitszeit-Maske, Stundenplan-Druck (vom Betreiber entfernt; siehe aber STP-918), Dunkelmodus-Zeitplan und Vertretungsansicht für Fernseher (Monitor existiert), automatische Antwort an Eltern bei Abwesenheit (datenschutzkritisch), Rollen-Knöpfe auf der Anmeldeseite außerhalb der Demo, Fable-Agenten (Arbeitsregel: Sonnet/Haiku), Online-Prüfung geleakter Passwörter bei Dritten als Standard.

Die Statusangaben der Altquellen vom 10.10.–11.10. (Produkt-Backlog, Mängelliste U-01 bis U-116) wurden nur dann übernommen, wenn spätere Quellen den Punkt nicht als gebaut belegen; solche Punkte tragen den Zusatz „[unklar: Status im Ist nicht belegt]“. Quellen: Gesprächsauszüge G1 bis G6, Notizen W2, W3, W5, W6, W7, W8.

## 4. Priorisierte Liste aller noch nicht umgesetzten Punkte

Aufbau: 19 Bereiche (4.1 bis 4.19, Namen wie in der Bereichsliste der Gesprächsauszüge). Je Bereich zuerst P0, dann P1, P2, P3, innerhalb einer Stufe nach Kennung. Eintragskopf: `Kennung · Titel · Priorität · Aufwand · Status: offen`; darunter Beschreibung, Herkunft, Abhängigkeiten und genau eine Zeile `Abnahme:`. Zusammengeführte Doppelungen sind in der Beschreibung genannt. Punkte, die laut G6 gebaut sind, stehen nicht hier (siehe Abschnitt 3). Die Kennungen sind je Kürzel fest (901 bis 999) und werden in den Abschnitten 1 und 2 referenziert.

### 4.1 Stundenplan und Generator

#### STP-914 · Pakete und Plan-Stände schützen, Planungs-Aktionen protokollieren · P0 · Aufwand M · Status: offen
- Vorschlagspakete („Plan prüfen“) und gespeicherte Plan-Stände (bis 50) enthalten Namen von Lehrkräften und Klassen und sind im Ist weder verschlüsselt noch an eine Aufbewahrungsfrist gebunden. Sie werden mit Datensatz-Bezug verschlüsselt, laufen ins Löschkonzept (Frist nicht abschaltbar); jede Regel-, Paket- und Plan-Stand-Aktion (Speichern, Übernehmen, Verwerfen, Zurückstellen, Wecken, Löschen, Import) wird ohne Inhalt protokolliert; Lesen und Export von Regeln und Paketen nur mit `settings.edit`, `timetable.edit` oder `timetable.generate`.
- Herkunft: Claude (Audit 10-17, Bewertung 10-16). Abhängigkeiten: SIC-901, DAT-902.
Abnahme: Ein Plan-Stand liegt in der Datenbank nicht lesbar; Schüler-Konto ruft Regeln oder Pakete auf → 403; jede Paketaktion erzeugt einen Protokolleintrag ohne Planinhalt; nach Fristablauf sind alte Stände gelöscht.

#### STP-901 · Raster per Tastatur, Touch und Screenreader bedienbar · P1 · Aufwand L · Status: offen
- Verschieben von Stunden per Pfeiltasten und Eingabetaste, Touch-Verschieben oder Optionsmenü, sichtbarer Fokusring, ARIA-Beschriftung (Tag, Stunde, Inhalt); ein Bedienkonzept für TimetableGrid und DayPeriodGrid, damit für alle Tage×Stunden-Ansichten.
- Herkunft: Claude (Bewertung 10-16, Paket W3-01); Betreiber-Regel „Ein Raster für alles“. Abhängigkeiten: OBE-902.
Abnahme: Ohne Maus lässt sich eine Stunde wählen, mit Pfeiltasten verschieben und mit Eingabetaste bestätigen; der Screenreader liest „Dienstag, 3. Stunde, Mathematik, Raum 101“; bei 390 px erscheint ein Optionsmenü; ohne `timetable.edit` bleibt das Raster nur lesbar.

#### STP-902 · Plan-Übernahme absichern · P1 · Aufwand M · Status: offen
- Die Übernahme eines Entwurfs prüft die Planversion zu Laufbeginn; bei Abweichung 409 „Der Plan hat sich seit Beginn des Laufs geändert“ mit Angebot, neu zu rechnen oder bewusst zu überschreiben (zweite Bestätigung, protokolliert). Protokoll in derselben Transaktion; Protokoll auch bei Zurückstellen und Wecken; Recht `settings.edit` klären.
- Herkunft: Claude (Bewertung 10-16, Paket W2-09; Datenverlustrisiko). Abhängigkeiten: STP-903.
Abnahme: Lauf starten, Stunde verschieben, Übernahme → 409 mit der Meldung; ausdrückliches Überschreiben gelingt und der Protokolleintrag nennt es; schlägt die Transaktion fehl, bleiben Plan und Protokoll unverändert.

#### STP-903 · Gleichzeitige Änderungen am Planungsdokument · P1 · Aufwand M · Status: offen
- Jedes Speichern prüft, dass die Basisversion die aktuelle ist; sonst Meldung „Der Plan wurde inzwischen geändert. Bitte erneut versuchen.“ (keine stille Überschreibung). Bei Mehrserver-Betrieb zusätzlich datenbankweite Schreibsperre bis zum Commit.
- Herkunft: Claude (Analyse). Abhängigkeiten: BET-913 (nur für Mehrserver).
Abnahme: Zwei Sitzungen speichern von derselben Basisversion → die zweite erhält die Meldung, nichts wird überschrieben.

#### STP-904 · Planungsdokument serverseitig validieren · P1 · Aufwand M · Status: offen
- Eindeutigkeit der Kennungen, Verweisprüfung (Kurs→Klasse/Fach/Lehrkraft/Raum, Stunde→Kurs, Abwesenheit→Lehrkraft/Klasse/Raum/Kurs, Aufsicht→Bereich/Lehrkraft), Löschregeln (Klasse löschen entfernt Kursteil-Teilnehmer), Wertebereiche; Kürzel ohne Unterschied bei Groß-/Kleinschreibung und ohne Leerzeichen; Abwesenheits-Kennungen werden nie wiederverwendet.
- Herkunft: Claude (Bestandsprüfung 10-10). Abhängigkeiten: STA-905.
Abnahme: Anlegen von „mue“ bei vorhandenem „MUE“ → 422; Löschen einer Klasse entfernt deren Kursteil-Verweise; eine neue Abwesenheit erhält nie eine bereits vergebene Kennung.

#### STP-905 · Zeitraster-Rechner und frei einstellbares Raster · P1 · Aufwand M · Status: offen
- Die Schule gibt Beginn (7:50, 7:55, 8:00 oder frei), Stundenlänge (45, 60 oder frei, optional je Stunde) und Pausen (Name, Minuten, „trennt Doppelstunden“) ein; das System berechnet die Uhrzeiten, zeigt eine Live-Vorschau, rechnet Lehrkraft-Zeitfenster neu, meldet überlappende Stunden und zu kurze Pausen und zeigt vor der Änderung die betroffenen Stunden. „Zeiten von Hand“ bleibt möglich.
- Herkunft: Betreiber (Wunsch „Zeitraster frei“, 10-10/11). Abhängigkeiten: STA-902.
Abnahme: Beginn 07:55, Länge 45 min, Pause 15 min nach Stunde 2 → Stunde 3 beginnt 09:40; eine Rasteränderung nennt vorab die betroffenen Stunden; eine Überlappung wird mit Meldung abgelehnt.

#### STP-907 · Hinweis bei nicht lesbarem Planstand · P1 · Aufwand S · Status: offen
- Beim Start wird die jüngste lesbare Version geladen (höchstens die 5 jüngsten geprüft). Greift der Rückfall auf eine ältere Version oder ein leeres Dokument, zeigt der Systembereich der Administration einen deutlichen Hinweis „Planungsdaten nicht lesbar“, nicht nur einen Protokolleintrag.
- Herkunft: Claude (Analyse). Abhängigkeiten: keine.
Abnahme: Bei beschädigter jüngster Version lädt das System die vorherige und meldet das im Systembereich; bei fünf unlesbaren Versionen erscheint der Hinweis vor dem Start mit leerem Dokument.

#### STP-915 · Handy- und Tablet-Ansichten des Plans · P1 · Aufwand M · Status: offen
- Der Stundenplan-Baustein schaltet am Handy automatisch auf Listen-/Tagesansicht; Filterleisten hinter einem Knopf „Filter“ mit aktiven Filtern als Chips; seltene Schalter (Regelplan bearbeiten, Raster/Liste) im „Mehr“-Menü; auf dem Tablet leere Sa/So-Spalten ausblenden; Hinweis-Spalte bei 800 px nicht abgeschnitten.
- Herkunft: Betreiber (Geräte-Tauglichkeit A-61); Claude (Vorschlag 10-12, Freigabe offen). Abhängigkeiten: STP-901.
Abnahme: Bei 390 px zeigt der Plan die Tagesliste ohne horizontalen Bildlauf; bei 800 px ist kein Hinweistext abgeschnitten.

#### STP-920 · Regel-Vorlagen reparieren · P1 · Aufwand S · Status: offen
- Vorlagen laufen vor dem Anwenden durch die Normalisierung (Ausnahmen mit gelöschten Klassen), stilles Kürzen auf 30 Einträge entfällt (Fehler oder ausdrückliche Grenze), Größenlimit für importierte Vorlagen, Operator-Reihenfolge der Bedingungen eindeutig.
- Herkunft: Claude (Bewertung 10-16, Paket W2-14). Abhängigkeiten: keine.
Abnahme: Vorlage mit Ausnahme für eine gelöschte Klasse wird mit Meldung abgewiesen; 31 Einträge werden nicht still auf 30 gekürzt; eine Vorlagendatei über dem Größenlimit wird abgelehnt.

#### STP-906 · Tageszeiten und Zeitraster je Klasse · P2 · Aufwand L · Status: offen
- Abendklassen ab 16:00 mit eigener erster Stunde; Lehrkräfte mit Früh- und Abendunterricht werden richtig behandelt; Konflikte nach Uhrzeit statt Stundennummer; mehrere Zeitraster je Klasse oder Abteilung und Vorlagen dafür; Lehrkraft- und Raumplan chronologisch.
- Herkunft: Betreiber (A-69); Wettbewerb (Untis, „Minuten-Stundenplan“). Abhängigkeiten: STP-905.
Abnahme: Klasse mit Raster ab 16:00 und Lehrkraft mit Unterricht um 08:00 und 17:00 → keine Doppelbelegung, Konflikte werden nach Uhrzeit gemeldet.

#### STP-909 · Pläne mit Gültigkeit „ab Datum“ · P2 · Aufwand L · Status: offen
- Ein neuer Plan oder ein Lehrkraftwechsel gilt ab einem Datum; vergangene Pläne, Vertretungen und Statistiken bleiben unverändert; Stunden mit Gültigkeitsbeginn, Hohl- und Springstunden samt Vertretung, Tagesplan einzeln neu erzeugen. Halbjahres-Zeiträume sind gebaut.
- Herkunft: Claude (Backlog B-46, Paket W4-08); Wettbewerb. Abhängigkeiten: STP-903.
Abnahme: Wechsel der Lehrkraft einer Stunde zum 01.02. ändert Auswertungen vor dem 01.02. nicht; der Plan danach zeigt die neue Lehrkraft.

#### STP-910 · Engpassanalyse, Tauschvorschläge, Szenarien · P2 · Aufwand M · Status: offen
- Vorab-Engpassanalyse vor dem Lauf (fehlende Lehrkräfte, Räume, Deputat), Tauschvorschläge im Raster beim manuellen Planen, Szenarien-Vergleich; „Unverplant“ nennt den Grund bereits.
- Herkunft: Wettbewerb (Untis); Claude (Vorschlag 10-12). Abhängigkeiten: STP-902.
Abnahme: Vor dem Lauf nennt die Analyse „Fach Physik: 4 Stunden ohne Lehrkraft“; ein Tauschvorschlag verschiebt zwei Stunden ohne Konflikt.

#### STP-911 · Regelabdeckung ergänzen · P2 · Aufwand M · Status: offen
- Muster „leere erste Stunde“ und „Doppelstunde plus Einzelstunde am selben Tag“ als Regeln bewerten; Pendelverstöße im Qualitätsbericht auf der Seite zählen; Strafpunkt-Gewichte (Springstunden 4 oder 5, Hohlstunden 100, gleichmäßige Tage 6) als Konfiguration führen.
- Herkunft: Betreiber (10-11 Wunsch Doppelstunden, nicht bestätigt gebaut); Claude. Abhängigkeiten: keine.
Abnahme: Der Bericht listet Pendelverstöße mit Tag und Lehrkraft; die Gewichte stehen in der Konfiguration; ein Plan hat 0 Kurse mit Doppel- und Einzelstunde am selben Tag, solange Tage frei sind.

#### STP-912 · Reihenfolge der Planungs-Reiter · P2 · Aufwand S · Status: offen
- Entscheidung E-19a: „Plan prüfen“ vorn und Qualitätsbericht als zweiter Reiter oder beides in einem Reiter mit Unterbereichen (Betreiber wollte den Qualitätsbericht als ersten, 10-12).
- Herkunft: Betreiber (10-12/13), offen. Abhängigkeiten: E-19.
Abnahme: Reiterreihenfolge und Unterbereiche entsprechen der Entscheidung; alte Links funktionieren.

#### STP-913 · Plan-Vorschläge mit Empfehlung, Auto-Planer-Frage · P2 · Aufwand M · Status: offen
- Varianten tragen eine Markierung „empfohlen“ mit Warnung bei Verschlechterung (Test: Variante „minimal“ machte Leerstunden von 20 auf 88); Entscheidung bleibt beim Menschen („Menschen mögen es lieber, eine Auswahl zu haben“, 10-12). Der frühere Auto-Planer (Neuplanung ohne Auswahl) entfällt im Neubau.
- Herkunft: Betreiber (10-12 20:53); Claude. Abhängigkeiten: E-19.
Abnahme: Jede Variante zeigt Vorher/Nachher-Zahlen und eine Empfehlungsmarke; die Annahme verlangt Bestätigung; es gibt keine automatische Planänderung.

#### STP-916 · Stunden-Details, Hausaufgaben eintragen, freie Räume · P2 · Aufwand M · Status: offen
- Antippen einer Stunde zeigt Lehrkraft, Raum, Thema, Hausaufgabe, Änderungen; Lehrkräfte tragen Hausaufgaben ein; Ansicht „freie Räume je Stunde“ aus dem Plan.
- Herkunft: Betreiber (A-54, A-55); Wettbewerb (Untis). Abhängigkeiten: STP-901, KLB-901.
Abnahme: Tipp auf eine Stunde öffnet die Details; eine eingetragene Hausaufgabe erscheint mit Frist in Plan und Hausaufgaben-Übersicht; „Freie Räume“ listet für Dienstag 3. Stunde alle freien Räume.

#### STP-918 · Stundenplan als PDF · P2 · Aufwand S · Status: offen
- PDF je Kind (Woche), Klasse, Lehrkraft für Eltern (Wettbewerbs-Kleinfunktion). Der Betreiber hat den Stundenplan-Druck entfernt (10-12); Neuaufnahme nur als PDF-Export, nicht als Druckseite.
- Herkunft: Wettbewerb; Betreiber-Entfernung 10-12 beachten. Abhängigkeiten: E-02.
Abnahme: „Als PDF“ erzeugt das PDF der gewählten Woche mit Pausen und Raum; ein fremdes Kind liefert 404.

#### STP-919 · Anzeige Sa/So und Wochenzählung · P2 · Aufwand S · Status: offen
- Entscheidung E-18: Sa/So im Raster standardmäßig nur bei Terminen (Betreiber 10-11: „wenn da auch Events sind“), Schalter „immer“; Anzeige in Kalenderwochen mit interner fortlaufender Schulwochen-Zählung bestätigen.
- Herkunft: Betreiber (10-11/13), offen. Abhängigkeiten: E-18.
Abnahme: Ohne Termin fehlen Sa/So; ein Samstagstermin zeigt die Spalte; der Schalter „immer“ zeigt sie dauerhaft.

#### STP-908 · Reformformen: Mischaltersgruppen, Tagesrahmen, Team-Teaching · P3 · Aufwand XL · Status: offen
- Mischaltersgruppen (Klasse mit mehreren Jahrgängen), Tagesrahmen/Zeitanker („Freiarbeit vormittags“), gleichberechtigtes Team-Teaching, Raumgruppen und teilbare Räume, Lerngruppen unabhängig von Klassen, Blocklängen beliebig; Montessori-Testschule zeigte 1.224 ungeplante Blöcke ohne diese Werkzeuge.
- Herkunft: Betreiber (10-12 Montessori-Auftrag); Claude (Werkzeugliste). Abhängigkeiten: STA-907, STP-922.
Abnahme: Die Testschule (12 Mischgruppen, 250 Kinder, 83 Kurse) wird ohne Behelfsräume vollständig verplant, Freiarbeit liegt vormittags.

#### STP-917 · Hitzefrei und abweichendes Tagesraster · P3 · Aufwand S · Status: offen
- Ein einzelner Tag erhält ein abweichendes Stundenraster (Hitzefrei, Projekttag) ohne den Dauerplan zu ändern.
- Herkunft: Wettbewerb. Abhängigkeiten: STP-905.
Abnahme: Hitzefrei-Raster für einen Tag kürzt die Stunden dieses Tages; der Folgetag ist unverändert.

#### STP-921 · Oberstufe: Kurswahl, Bänder, Kursplanung · P3 · Aufwand XL · Status: offen
- Kurswahl mit Prioritäten und Konfliktprüfung je Kind, Bänder bilden, Kursoptimierung, Soll-Ist-Rechnung; „groß, später“, Zielgruppe (Oberstufe oder Berufskolleg) offen.
- Herkunft: Betreiber („groß, später“, 10-16); Wettbewerb. Abhängigkeiten: E-31, STP-923.
Abnahme: 100 Schüler/innen wählen Kurse; die Planung bildet Bänder ohne Wahlkonflikt oder nennt je Kind den Konflikt.

#### STP-922 · Jahresstunden, Epochen, Blockphasen · P3 · Aufwand L · Status: offen
- Jahresstunden über das Jahr verteilen, Epochen- und Projektplaner, Blockphasen für Teilgruppen, mehrere Zeitraster.
- Herkunft: Wettbewerb (Untis); Claude (Montessori-Liste). Abhängigkeiten: STP-906.
Abnahme: Ein Fach mit 80 Jahresstunden wird als 4-Wochen-Epoche geplant und erscheint nur in diesen Wochen.

#### STP-923 · Wahlfächer, AG, Projekttage mit Zuteilung · P3 · Aufwand L · Status: offen
- Anmeldung mit Wünschen, faire Zuteilung im Solver, Los als Rückfall mit Begründung; Selbsteinschreibung mit Schlüssel.
- Herkunft: Wettbewerb; Claude. Abhängigkeiten: E-31.
Abnahme: 30 Wünsche auf 20 Plätze → Zuteilung nennt je Kind den Grund; Los ist nachvollziehbar protokolliert.

#### STP-924 · Abteilungsplanung, Unterrichtsmatrix · P3 · Aufwand L · Status: offen
- Plan aufteilen, dezentral planen und zusammenführen; Unterrichtsmatrix (Klasse×Fach) mit Lehrkraft per Klick.
- Herkunft: Wettbewerb (Untis); Betreiber (Abteilungsleitung, Rückmeldung 10-10). Abhängigkeiten: STA-908, E-31.
Abnahme: Abteilung A plant ihre Klassen, die Zusammenführung meldet Konflikte mit Abteilung B.

#### STP-925 · Weitere Planungslücken · P3 · Aufwand M · Status: offen
- Sitzpläne; Besprechungstermin mit Zeitfindung (Lehrkräfte, Klassen); Mindestanzahl freier Tage; Sperrzeiten je Fach; Plan-PDF je Klasse und Lehrkraft.
- Herkunft: Wettbewerb. Abhängigkeiten: keine.
Abnahme: Ein Besprechungstermin für fünf Lehrkräfte schlägt drei gemeinsame freie Zeiten vor.

#### STP-926 · Räume: Konzept, Leihe, Buchung · P3 · Aufwand L · Status: offen
- Räume mit Fach-/Ausstattungszuordnung, Raumleihe (Klasse aus Fachraum verdrängen), Raum- und Gerätebuchung mit Genehmigung, Rolle Ressourcenverwalter, Auslastungsbericht; Entfall gibt den Raum frei; Konfliktwarnung mit Klausuren.
- Herkunft: Betreiber („groß, später“, 10-16); Wettbewerb. Abhängigkeiten: STP-916, E-31.
Abnahme: Buchung des PC-Raums in einer belegten Stunde wird abgelehnt; ein Entfall macht den Raum buchbar.

### 4.2 Vertretung, Aufsichten, Monitore

#### VER-909 · Druckansicht und Monitor-Anzeige schützen · P0 · Aufwand S · Status: offen
- Die Druckansicht (Aushang) des Vertretungsplans ist nur angemeldet mit `substitution.read` oder `monitor.read` erreichbar und zeigt die öffentliche Sicht ohne Gründe; Monitor-Konten sind schreibgeschützt (Schreibversuch 403), erhalten für Abwesenheiten-Liste, Atteste, Förderkennzeichen, Eltern-Kontakte und Benachrichtigungs-Ausgang 403, und die Monitor-Antwort enthält weder Grund noch Gesundheitsdaten. Betreiberentscheidung zu anonymem Aushang-Zugang steht aus.
- Herkunft: Claude (Bestandsprüfung, Audit 10-17). Abhängigkeiten: SIC-901.
Abnahme: Druckansicht ohne Anmeldung → Weiterleitung zur Anmeldung; Monitor-Konto ruft Atteste auf → 403; Monitor-Konto legt eine Abwesenheit an → 403.

#### VER-911 · Rechte der Aufsichten, Klausur-Datenweg, Protokoll · P0 · Aufwand M · Status: offen
- Aufsichten erzeugen, Bereiche verwalten und bearbeiten nur mit `duties.manage` (oder `timetable.edit`), Lesen der eigenen Aufsichten für alle Lehrkräfte; der generische Datenweg für Klausuren läuft durch dieselbe Prüfung wie die Klausur-Schnittstelle (Schultag, Höchstzahlen, Kursunterricht, kein `force`); Verweise auf Raum, Fach, Klasse werden beim Löschen gepflegt; alle schreibenden Aktionen von Vertretung, Aufsicht, Nachschreiben und Klausur sind protokolliert; Outbox-Inhalte verschlüsselt und nach Zustellung bzw. Frist gelöscht.
- Herkunft: Claude (Audit 10-17, Bewertung 10-16). Abhängigkeiten: SIC-901, DAT-902.
Abnahme: Lehrkraft ohne `duties.manage` erzeugt keine Aufsichten (403); eine Klausur an einem Ferientag über den generischen Weg wird wie über die Klausur-Schnittstelle abgelehnt; Löschen eines Raums meldet die Klausuren, die ihn verwenden.

#### VER-901 · Qualifikation: wer vertreten darf · P1 · Aufwand M · Status: offen
- Betreiber: „das ist auch wirklich nur Lehrer unterrichten als Vertretung, die Qualifikation haben für die Klasse“ (11.10.). Zuerst die zuständige Lehrkraft der Klasse, danach nur qualifizierte; Einstellung „nur qualifizierte Lehrkräfte“ ohne fachfremden Rückfall (bleibt offen mit Warnung); Profilfeld „kann vertreten in“ (Klassen) wird bevorzugt. Der Standardwert ist nicht bestätigt.
- Herkunft: Betreiber (10-11/12). Abhängigkeiten: LEH-906.
Abnahme: Mit „nur qualifizierte“ wird Englisch nie fachfremd betreut, die Stunde bleibt offen mit Warnung; eine Lehrkraft mit „kann vertreten in 7b“ wird vor einer ohne Eintrag vorgeschlagen.

#### VER-903 · Material und Selbststudium bei Lehrerabwesenheit · P1 · Aufwand M · Status: offen
- Betreiber („Next up“, 10-12): bei Ausfall Eigenarbeit je Klassenstufe mit Material; Recht `substitution.self_study` (ab welcher Klassenstufe legt die Verwaltung fest, nicht die Lehrkraft); die Lehrkraft hinterlegt Material, es erscheint als Vorschlag im Eintragsdetail.
- Herkunft: Betreiber (10-12), Backlog Paket W4-02. Abhängigkeiten: KUR-902.
Abnahme: Ausfallstunde in zugelassener Klassenstufe zeigt „Eigenarbeit“ mit Material; in nicht zugelassener Klassenstufe fehlt der Vorschlag.

#### VER-904 · Vertretungskonto und Fairness über das Halbjahr · P1 · Aufwand L · Status: offen
- Vertretungen, Entfälle und Mitbetreuungen je Tag in einem Konto (nachträgliche Änderungen zählen); Auswahl bevorzugt Lehrkräfte unter ihrem Soll nach Deputat im Zeitraum (Standard Halbjahr); Höchstgrenzen (2 je Tag, 3 je Woche) bleiben als Schutz mit Warnung; Ist, Soll und Abweichung in Vertretungsseite und Lehrkraft-Detail; Monatsübersicht, Export zur Abrechnung. Befund: 17 von 57 Lehrkräften trugen alle Vertretungen.
- Herkunft: Betreiber (A-49); Wettbewerb (Untis, Schulmanager Online). Abhängigkeiten: LEH-906.
Abnahme: Vier-Wochen-Simulation mit drei Langzeitkranken: keine Lehrkraft über dem Doppelten ihres Solls, solange andere unter Soll verfügbar sind; die Seite zeigt „Ist 6, Soll 4,2, +1,8“.

#### VER-910 · Monitor-Menü auffindbar und per Tastatur erreichbar · P1 · Aufwand S · Status: offen
- Der Menü-Knopf (☰) ist bewusst kaum sichtbar; Entscheidung E-14: erkennbar mit Fokusring und Tastaturzugang; „Standort wechseln“ nur ohne festen Standort. Auf den Servern ist das Menü nicht bestätigt.
- Herkunft: Betreiber (Beschwerde 10-17: kein Ausgang); Claude. Abhängigkeiten: E-14, OBE-902.
Abnahme: Das Menü ist per Tab erreichbar mit sichtbarem Fokusring; Abmelden mit Bestätigung führt zur Anmeldeseite; ein Konto mit festem Standort sieht keinen Standortwechsel.

#### VER-912 · Monitor ruhig, mobil, geräte-fest, modular · P1 · Aufwand L · Status: offen
- Unter 48em oder bei Touch: nativer Bildlauf, eine Spalte, Umschalter „Heute · Morgen“, Karten je Klasse, `100dvh`; Uhr als eigene Komponente (kein Neuaufbau je Sekunde); `?tage=1..5`; „Stand: HH:MM“ und laufende Stunde hervorgehoben; widerrufbares Geräte-Token statt Abmeldung nach 30 Tagen; Monitor-Profile je Bildschirm mit frei gewählten Kacheln; nach Verbindungsabbruch bleibt der letzte Stand mit Stand-Angabe sichtbar.
- Herkunft: Betreiber (A-62); Claude (Backlog B-12, B-28, B-33). Abhängigkeiten: VER-910.
Abnahme: Bei 375 px keine abgeschnittenen Spalten; ein Gerät bleibt nach 45 Tagen angemeldet; nach Widerruf des Tokens liefert der nächste Abruf 401; nach Verbindungsverlust springt „Stand“ nach dem Wiederverbinden auf die neue Zeit.

#### VER-913 · Vertretung: Nebenläufigkeit und Leistung · P1 · Aufwand M · Status: offen
- Freigabe von Vorschlägen mit Versionsprüfung; Index-Fehler bei Ausnahme ohne Eintrag und Kurs ohne Teile beheben; Statistik beschleunigen; Last der Vertretungsplanung messen.
- Herkunft: Claude (Bewertung 10-16, Paket W2-10). Abhängigkeiten: STP-903.
Abnahme: Zwei gleichzeitige Freigaben derselben Vorschläge → die zweite erhält die Konfliktmeldung; die Statistik für 4 Wochen antwortet unter 2 Sekunden.

#### VER-902 · Schultag-Navigation und Ferien-Hinweise überall gleich · P2 · Aufwand S · Status: offen
- Die Kachel „Meine Tage“ und alle Datumsnavigationen überspringen Ferien (16.10. → 02.11.); die Ferien-Warnung im Krankmeldungsdialog im Dialog selbst prüfen.
- Herkunft: Claude (Test 10-16). Abhängigkeiten: keine.
Abnahme: Kachel „Meine Tage“ am 16.10. zeigt den 02.11.; im Dialog erscheint bei Krankmeldung in den Ferien die Warnung.

#### VER-905 · Aufsichten ausbauen · P2 · Aufwand M · Status: offen
- Soll-Anzahl Aufsichten je Lehrkraft und Ausnahmen; manueller Lehrkraft-Vorschlag je Platz mit Korrekturlauf; eigener Bereich für Pausenhöfe mit Hinweis beim Standortwechsel; Aufsichten online im Plan der Lehrkraft; Nacharbeit-Aufsichten.
- Herkunft: Betreiber (10-12 Pausenhöfe); Wettbewerb. Abhängigkeiten: VER-911.
Abnahme: Soll 1 je Woche für Lehrkraft X wird vom Generator eingehalten; der Vorschlag je Platz nennt die geeigneten Lehrkräfte.

#### VER-906 · Bereitschaft, Sondereinsatz, Methodenreihenfolge · P2 · Aufwand M · Status: offen
- Reserve vorab verplanen (bei Ausfall bevorzugt); wählbare Methodenreihenfolge der Automatik (Bereitschaft vor Freigesetzten, Verschiebung vor Vertretung, Aufsicht); Tagestext zum Plan; Zusatzrolle „Leseansicht Klassenbuch“ und Schalter „Kollegium sieht den ganzen Plan“.
- Herkunft: Wettbewerb (Untis, Schulmanager Online). Abhängigkeiten: VER-904.
Abnahme: Eine Bereitschaftsstunde wird bei Ausfall vor Freigesetzten gewählt; die Reihenfolge ist einstellbar.

#### VER-907 · Benachrichtigung und Webhook der Vertretung · P2 · Aufwand M · Status: offen
- Webhook-Testknopf und fertige Ziele; Signatur samt signiertem Zeitstempel; Schalter „Vertretungsmails“ in den Benachrichtigungen mit Hinweis in der Mail; Inhalte ohne Gründe, Gesundheitsdaten und fremde Namen; im Bestätigungsmodus erst nach Freigabe.
- Herkunft: Claude (Audit-Checkliste 10-17); Betreiber (Webhook 10-13). Abhängigkeiten: BEN-908.
Abnahme: Testknopf sendet einen signierten Testaufruf; eine neue Vertretung erzeugt Glocke und Mail ohne Grund; die Mail führt zum Abschalten.

#### VER-908 · Prüfungsfelder, Statistik, Kalender-Zielgruppen · P2 · Aufwand M · Status: offen
- Prüfungsfelder „zurückgegeben am / von / Ø-Note“ und Prüfungsstatistik; Schuljahreskalender mit Zielgruppen (Lehrkräfte, Schüler/innen, Eltern, Klasse), Anmeldepflicht und Rückmeldung am Termin, Listenansicht, öffentlicher Termin-Feed.
- Herkunft: Wettbewerb (Untis, Schulmanager Online). Abhängigkeiten: NOT-914.
Abnahme: Eine Klausur zeigt Rückgabedatum und Durchschnitt; ein Termin für „Eltern 7b“ erscheint nur dort.

### 4.3 Klassenbuch, Fehlzeiten, Atteste, Nachschreiben

#### KLB-901 · Klassenbuch Stufe 2: Thema, Kontrolle, Archiv, Sichtbarkeit · P1 · Aufwand L · Status: offen
- Das digitale Klassenbuch ersetzt das Papier-Klassenbuch: Thema optional aus einer Stoffverteilung, Eintrag je Stunde, Vertretungen und Termine fließen ein, Kontrollliste der Klassenleitung (Stunden ohne Eintrag), PDF je Woche und Halbjahr fürs Archiv (Archiv-Frist 10 Jahre gegen Landesrecht prüfen lassen), Erfassung ohne Netz mit späterem Abgleich. Entscheidung E-16(c): Thema und Hausaufgabentext sind für Schüler/innen und Eltern heute ausgeblendet (Hausaufgaben sichtbar, Thema sichtbar, Notizen nie).
- Herkunft: Wettbewerb (Schulmanager Online, Untis); Claude (Backlog B-53). Abhängigkeiten: DAT-902, SCH-910.
Abnahme: Das PDF der Woche enthält Stunden, Themen, Vertretungen und Termine; eine Stunde ohne Thema erscheint in der Kontrollliste; Schüler/innen sehen das Thema, nicht die Notiz.

#### KLB-903 · Erinnerung an offene Klassenbuch-Stunden · P1 · Aufwand S · Status: offen
- Push oder Mail an die Lehrkraft (statt nur Liste für die Klassenleitung) für Stunden ohne Anwesenheitseintrag; Kontrolle, ob alle Fachlehrkräfte eingetragen haben; „wie gestern“ als Ein-Klick-Anwesenheit.
- Herkunft: Wettbewerb (Untis, Kleinfunktion 10-16); Claude. Abhängigkeiten: BEN-901.
Abnahme: Um 16:00 erhält die Lehrkraft mit leerer Stunde eine Erinnerung, die zur Stunde führt; nach dem Eintragen entfällt sie.

#### KLB-907 · Beurlaubung: Entscheidungsansicht, Genehmigungswege, Befreiungen · P1 · Aufwand M · Status: offen
- Die Schulleitung sieht betroffene Stunden, bisherige Fehlquote und anstehende Klassenarbeiten im Zeitraum; Genehmigungsweg nach Dauer einstellbar (Beispiel: bis 2 Tage Klassenleitung, länger oder direkt vor/nach Ferien Schulleitung; Schwellen legt der Betreiber fest); bei Auszubildenden optionale Mitzeichnung des Betriebs; Postfach-Nachricht an die Klassenleitung bei neuem Antrag, Startkachel „offene Anträge“; Fachbefreiungen (z. B. Sport) mit Zeitraum und Wochentag.
- Herkunft: Claude (Vorschlag 10-13); Wettbewerb (Untis, Schulmanager Online). Abhängigkeiten: BEN-904, STA-911.
Abnahme: Beurlaubung während einer Klassenarbeit zeigt Stunden, Fehlquote in % und die Klassenarbeit; Befreiung Sport 01.–31.03. markiert die Person in den Sportstunden als „befreit“; ein neuer Antrag erhöht den Kachelzähler um 1.

#### KLB-902 · Fehlzeiten-Kleinteile klären · P2 · Aufwand S · Status: offen
- Wunsch „nach der Stunde gegangen“ als eigener Klassenbuch-Status (gebaut: Notizfeld, Krankmeldung kennt „früher gegangen“); Ampelregel der Fehlzeiten nach Zeit bestätigen; Dokument-Altversionen in der Oberfläche aufrufbar; gemerkte Kindauswahl je Konto statt je Gerät, bei Abmeldung verworfen; Tags der PDF-Formulare für Barrierefreiheit.
- Herkunft: Betreiber (10-11); Claude. Abhängigkeiten: OBE-901.
Abnahme: Status „nach der Stunde gegangen“ wählbar und in der Statistik getrennt; die Kindauswahl eines Kontos gilt auf einem zweiten Gerät und endet mit der Abmeldung.

#### KLB-904 · Klassenbuch-Ausbau: Eintragsarten, Lob/Tadel, Berichte · P2 · Aufwand L · Status: offen
- Freie Eintragsarten (Hausaufgabe vergessen, Störung, Material fehlt), Lob und Tadel je Person oder Klasse mit Elternsichtbarkeit je Kategorie, Mehrfacheinträge, Berichte und Listen (z. B. länger als N Tage unentschuldigt), Abwesenheitsübersicht als PDF und Export (bisher nur Drucken); Leistung: Auswertung für 2500 Schüler/innen und ein Halbjahr unter 1 s.
- Herkunft: Claude (Vorschlag 10-13); Wettbewerb. Abhängigkeiten: KLB-901.
Abnahme: Ein Eintrag „Störung“ erscheint nur für Berechtigte; die Liste „über 3 Tage unentschuldigt“ nennt die Personen; PDF und Halbjahresabfrage unter 1 s.

#### KLB-905 · Schnelle Anwesenheit · P2 · Aufwand M · Status: offen
- „Ist gekommen“ per Klick, Abwesenheit auf die nächste Stunde verlängern; Handy-Klassenbuch mit zwei großen Schaltern „anwesend / fehlt“ je Person (Notizfeld erst auf Antippen).
- Herkunft: Claude (Vorschlag 10-12/13). Abhängigkeiten: KLB-903.
Abnahme: Ein Klick auf „ist gekommen“ ändert „fehlt“ in „zu spät“ mit Minuten; bei 390 px sind alle Schalter ohne Zoom bedienbar.

#### KLB-906 · Entschuldigungs-Einstellungen je Schule · P2 · Aufwand M · Status: offen
- Standardgrund und Frist je Schule, Erinnerung bei offenen Abwesenheiten, Attest-Schwelle je Schule, Entschuldigungsvorlagen je Schule oder Schulgang (vorausgefüllt, nur unterschreiben), Entschuldigung vor Ort; Entscheidung, ob die Online-Meldung der Eltern als Entschuldigung gilt (ohne Standardwert).
- Herkunft: Betreiber (10-12 „Entschuldigung vor Ort mit vorgefertigtem Dokument“); Wettbewerb. Abhängigkeiten: FOR-904.
Abnahme: Mit Standardgrund „krank“ gilt die Eltern-Meldung sofort als entschuldigt; ohne Entscheidung bleibt sie „gemeldet“; die Vorlage des Bildungsgangs erscheint vorausgefüllt.

### 4.4 Noten, Kompetenzen, Klausuren

#### NOT-901 · Notenbuch-Einsicht: Standard festlegen · P1 · Aufwand S · Status: offen
- Vier Modi (gar nichts, alles sofort, erst nach Freigabe, nur Endnote); Standard „nach Freigabe“ (Claude-Entscheidung 10-16, Betreiber hat nicht bestätigt), Wahl in der Einrichtung erzwingen (E-11). Elterneinsicht Volljähriger folgt der Freigabe des Kindes.
- Herkunft: Claude; Betreiber-Bestätigung offen. Abhängigkeiten: E-11.
Abnahme: Neue Schule ohne Wahl kann die Einrichtung nicht abschließen; im Modus „nach Freigabe“ sehen Schüler/innen eine Note erst nach Freigabe durch die Lehrkraft.

#### NOT-902 · Notenbuch-Fehlerbehebung · P1 · Aufwand M · Status: offen
- Abdeckung bei fehlenden Leistungen anzeigen; Export-Spaltenköpfe gegen echte SchILD-, ASV- und LUSD-Vorlagen prüfen; stille Fehler protokollieren; Bewertung entschuldigt/unentschuldigt festlegen.
- Herkunft: Claude (Bewertung 10-16, Paket W2-07). Abhängigkeiten: NOT-901.
Abnahme: Ein Kurs mit 3 von 5 Leistungen zeigt „Abdeckung 60 %“; die Importdatei der Zielverwaltung nimmt den Export ohne Spaltenfehler an.

#### NOT-909 · Kompetenzen: Fehlerbehebung · P1 · Aufwand M · Status: offen
- Bestätigung idempotent (409 bei Wiederholung); Einträge für Kommentare und Verknüpfungen klären; Lernstände nach Austritt minimieren (180 Tage); Tests für alle Routen.
- Herkunft: Claude (Bewertung 10-16, Paket W2-06). Abhängigkeiten: DAT-902.
Abnahme: Zweite Bestätigung desselben Eintrags → 409; 180 Tage nach Austritt sind Lernstände des Kindes gelöscht.

#### NOT-911 · Nachteilsausgleich und Förderung vervollständigen · P1 · Aufwand M · Status: offen
- Bearbeiten-Dialog für Förder-Einträge (bisher nur Anlegen und Löschen); in der Klausurstunde erscheint „NTA n“ auch im Wochenplan der Lehrkraft; Antrag auf Nachteilsausgleich als Formular (Betreiber 10-12 21:08: „Sowas soll bitte auch die Kinder zu den Lehrern, sollen die Lehrer zu den höhergestellten da antworten.“); Schulbegleitung für mehrere Kinder gleichberechtigt; Begriff „Merkmale/sonstiges“ klären.
- Herkunft: Betreiber (10-12); Claude. Abhängigkeiten: FOR-904, SCH-905.
Abnahme: Ein Förder-Eintrag lässt sich ändern (Version im Protokoll, Dokument bleibt); der Antrag erzeugt einen Vorgang bei der Klassenleitung; Schulbegleitung mit drei Kindern sieht alle gleichwertig.

#### NOT-914 · Klausuren, Aufsichten, Nachholtermine: Regeln durchgängig · P1 · Aufwand M · Status: offen
- Sperrzeit-Logik (UND/ODER) korrigieren; Status der Nachholtermine prüfen; Protokoll bei Ausnahmen; Konfliktprüfung bündeln; „0“ bei Klassenarbeiten pro Woche/Tag bedeutet keine Grenze (Bestätigung offen); Klassenarbeiten je Halbjahr begrenzen; ein Prüfweg für alle Schreibwege; Klausurplan als Liste im Klassen-Kursraum.
- Herkunft: Betreiber (A-33); Claude (Paket W2-05). Abhängigkeiten: VER-911.
Abnahme: Eine vierte Klassenarbeit bei Grenze 3 je Halbjahr wird abgelehnt; Grenze 0 lässt unbegrenzt zu; jede Ausnahme steht im Protokoll.

#### NOT-903 · Notenübergabe im ENM-/SVWS-Format mit Rundlauf · P2 · Aufwand L · Status: offen
- Export und Import im offiziellen Format (Formatbeschreibung beschaffen), Rundlauf-Test gegen die Zielverwaltung; zuerst NRW; Spaltenzuordnung der bestehenden CSV-Exporte prüfen.
- Herkunft: Wettbewerb (Schulmanager Online); Claude. Abhängigkeiten: NOT-902, INT-918.
Abnahme: Export eines Kurses lässt sich fehlerfrei einlesen; der Rundlauf liefert dieselben Noten.

#### NOT-904 · Notenbuch-Erweiterungen · P2 · Aufwand M · Status: offen
- Notenabzug bei verspäteter Abgabe (Beispiel 10 % je Tag); Klausur-Detailfelder „zurückgegeben am“ und Durchschnitt; ein gemeinsamer Notenschlüssel für Aufgaben und Notenbuch (heute 92/81/67/50/30 % gegen 87/73/59/45/18 %); Löschregeln für Notenbücher; Benachrichtigung bei veröffentlichten Noten (ohne Noten im Text); Hauptfach-Kennzeichen und Zählweise der Versetzungswarnung.
- Herkunft: Wettbewerb (Moodle, Untis); Claude. Abhängigkeiten: NOT-901.
Abnahme: Aufgabe 3 Tage verspätet mit 10 % Abzug je Tag → die Vorschlagsnote zeigt den Abzug; Veröffentlichung erzeugt eine Glocke ohne Notenwert.

#### NOT-910 · Kompetenzen im Kursraum, Wochenplan-Kachel, Open Badges · P2 · Aufwand M · Status: offen
- Beim Anlegen eines Nachweises eine Aufgabe oder Material wählen (Zuordnungs-Chips); Schüler-Startseite mit Kachel „Mein Wochenplan“ und Hinweis bei offener Selbsteinschätzung; mehrere Kinder gleichzeitig einschätzen; Abzeichen als Open-Badge-Datei exportieren.
- Herkunft: Claude (Moodle-Vergleich); Wettbewerb. Abhängigkeiten: NOT-909.
Abnahme: Ein Nachweis verweist auf eine Kursraum-Aufgabe; Stufe 3 für 10 Kinder in einem Dialog; Abzeichen als Datei exportierbar.

#### NOT-912 · Individuelle Wochenpläne und Lerndokumentation · P2 · Aufwand L · Status: offen
- Wochenplan je Kind mit Wochenzielen, Darbietungsterminen (Lehrkraft, Raum, Zeitfenster), Pflichtanteilen, Wochenrückblick, Lerntagebuch; Beobachtungen und Gesprächsplanung; Berichtszeugnis aus Bausteinen als PDF.
- Herkunft: Betreiber (10-12 Montessori-Auftrag); Claude. Abhängigkeiten: STP-908.
Abnahme: Wochenplan mit einer Darbietung wird vom Kind bestätigt; das Berichtszeugnis ist als PDF erzeugbar.

#### NOT-913 · Auswertungen für Schulleitung und Förderung · P2 · Aufwand M · Status: offen
- Schulleitungs-Dashboard (Fehlquoten, Vertretungslast, Klausurdichte), eigene Stundenübersicht Soll/Ist, Frühwarnung für gefährdete Lernende (nur Hinweis), Aktivität je Kursraum.
- Herkunft: Wettbewerb (Moodle, Untis). Abhängigkeiten: KLB-904.
Abnahme: Das Dashboard zeigt Fehlquote je Klasse und Klausurdichte je Woche; die Frühwarnung nennt Kriterien, keine Prognose.

#### NOT-905 · Kopfnoten-Workflow · P3 · Aufwand M · Status: offen
- Abstimmung zwischen Fachlehrkraft und Klassenleitung, Übernahme in die Zeugnisverwaltung; Entscheidung E-31.
- Herkunft: Wettbewerb. Abhängigkeiten: NOT-903, E-31.
Abnahme: Kopfnote durchläuft Vorschlag, Abstimmung, Übernahme und erscheint im Export.

#### NOT-906 · Zeugniskonferenz-Ansicht · P3 · Aufwand L · Status: offen
- Leistungsübersicht mit Farbmarkierung, Notenschnitte, Gefährdungsmeldungen; Zeugnisdruck bleibt in SchILD/ASV.
- Herkunft: Wettbewerb. Abhängigkeiten: NOT-905.
Abnahme: Die Ansicht zeigt eine Klasse mit Schnitt und Farbmarkierung; kein Zeugnisdruck.

#### NOT-907 · Lernentwicklungsgespräch (LEG) · P3 · Aufwand L · Status: offen
- Kompetenzpool, Ich-/Du-Bögen (Anrede „Sie“ beachten), Symbolsets, PDF mit Schullogo.
- Herkunft: Wettbewerb (nur Grund- und Mittelschule BY). Abhängigkeiten: NOT-912, E-31.
Abnahme: Ein Bogen wird aus dem Kompetenzpool erzeugt und als PDF ausgegeben.

#### NOT-908 · Abschlussregeln je Bundesland, Abschlussprognose · P3 · Aufwand L · Status: offen
- Abschlussregeln als Daten (Vorbild SchILD), Prognose des Abschlusses.
- Herkunft: Claude (Recherche 10-16). Abhängigkeiten: NOT-906.
Abnahme: Für NRW wird die Versetzung nach hinterlegter Regel berechnet.

### 4.5 Kursräume, Aufgaben, Lernaktivitäten, Lernfortschritt

#### KUR-901 · Abgaben und Ergebnisse untereinander und gegenüber Eltern abschotten · P0 · Aufwand M · Status: offen
- Betreiber (10-11): „kein Schüler soll die Hausaufgaben von anderen sehen“; die Umsetzung wurde nie bestätigt. Abgaben, Gruppenabgaben (nur Mitglieder), Bewertungen, Abstimmungs- und Selbsttest-Ergebnisse sind nur für die Person selbst, die Lehrkraft und – nach Freigabe – für Eltern sichtbar; die Elternfreigabe in den Lernaktivitäten (Abstimmungen, Selbsttests) wird vollständig geprüft und für Volljährige an deren Freigabe gebunden.
- Herkunft: Betreiber (10-11); Claude (Audit 10-17, Anhang C). Abhängigkeiten: SIC-905, SIC-901.
Abnahme: Schüler A ruft die Abgabe von Schüler B (andere ID) auf → 404; Eltern eines Volljährigen ohne Freigabe sehen keine Selbsttest-Ergebnisse; die Auswertung einer Abstimmung nennt keine Teilnehmer.

#### KUR-902 · Material und Ordner in der Oberfläche verwalten · P2 · Aufwand S · Status: offen
- Ordner und Material verschieben und umsortieren (Ziehen oder Menü), nicht nur über die Schnittstelle; Zweck der Checkboxen bei Material und Hausaufgaben klären.
- Herkunft: Betreiber (10-11 Kursräume); Claude. Abhängigkeiten: keine.
Abnahme: Eine Datei lässt sich in einen anderen Ordner verschieben; die Reihenfolge bleibt nach Neuladen erhalten; ohne Lehrenden-Recht 404.

#### KUR-903 · Freigabe bei Entfall, „nur für Schüler/innen“, Eltern-Einsicht je Raum · P2 · Aufwand M · Status: offen
- Fällt eine gebundene Stunde aus, bleibt das Material verborgen und die Freigabe wandert zur nächsten Stunde; Markierung „nur für Schüler/innen“ (z. B. Lösungen); die Eltern-Einsicht je Raum abschaltbar (Wunsch, keine Anforderung).
- Herkunft: Betreiber (A-46, A-47); Claude (Backlog B-20). Abhängigkeiten: VER-902.
Abnahme: Entfall der Stunde 1 verschiebt die Freigabe auf die nächste Stunde; Eltern sehen als „nur Schüler/innen“ markiertes Material nicht.

#### KUR-904 · Benachrichtigung bei Freigabe, Regeln beim Kopieren · P2 · Aufwand S · Status: offen
- Benachrichtigung, wenn ein Element frei wird; beim Kopieren von Material oder Kursräumen werden Abschlussbedingungen und Freigaberegeln mitkopiert.
- Herkunft: Claude (Vorschlag 10-16). Abhängigkeiten: BEN-902.
Abnahme: Ein Element wird durch Erledigen eines anderen frei und löst eine Glocke aus; die Kopie behält die Bedingung.

#### KUR-905 · Unterricht-Tab: Markierung „zu spät / früher gegangen“ · P2 · Aufwand S · Status: offen
- Betreiber (10-12 15:35): grün anwesend, orange zu spät oder früher gegangen; 17:18 zählt es im Kursraum nicht als Fehlen und die Markierung ist möglicherweise entfallen; Entscheidung und Umsetzung nötig.
- Herkunft: Betreiber (10-12). Abhängigkeiten: KLB-902.
Abnahme: Ein Unterricht-Eintrag mit 5 Minuten Verspätung erscheint orange und nicht als „gefehlt“.

#### KUR-906 · Klassenraum-Tab: Klausurplan-Liste, Anhänge, gemeinsames Pflegen · P3 · Aufwand S · Status: offen
- Klausurplan als eigene Liste statt Link; nachträgliche Anhänge an Infokarten; Schalter „gemeinsam pflegen“ je Klassenraum.
- Herkunft: Betreiber/Claude (10-12). Abhängigkeiten: NOT-914.
Abnahme: Der Klassenraum listet die Klausuren der Woche; ein Anhang lässt sich später ergänzen.

#### KUR-907 · Aufgaben-Erweiterungen · P3 · Aufwand M · Status: offen
- Anonym bewerten, Entwurf und Freigabe von Bewertungen, Sammelaktionen, Notizen für Lehrkräfte, Abgaben-ZIP, private Dateien je Person.
- Herkunft: Wettbewerb (Moodle). Abhängigkeiten: KUR-901.
Abnahme: Anonymes Bewerten blendet Namen aus, bis die Bewertung freigegeben ist.

#### KUR-908 · Lernaktivitäten-Erweiterungen · P3 · Aufwand M · Status: offen
- Moodle-XML-Import, Fragen mit Bildern, weitere Fragetypen; Selbsttest bleibt einfach.
- Herkunft: Wettbewerb (Moodle). Abhängigkeiten: KUR-901.
Abnahme: Eine Moodle-XML-Datei mit 10 Fragen wird importiert; Bilder erscheinen in der Frage.

#### KUR-909 · Freigabe- und Abschlussregeln für Abstimmungen und Umfragen · P3 · Aufwand S · Status: offen
- Abschluss- und Freigaberegeln gelten bisher nicht für Abstimmungen und Umfragen.
- Herkunft: Claude. Abhängigkeiten: KUR-904.
Abnahme: Eine Umfrage lässt sich an eine Bedingung binden und wird erst danach angezeigt.

#### KUR-910 · Teilen und Kopieren, Common Cartridge · P3 · Aufwand M · Status: offen
- Kursräume und Material per Link mit Ablauf teilen (Dateien mitkopieren, Kontingent prüfen), Export und Import als Common Cartridge, Export für Moodle.
- Herkunft: Claude (Vorschlag 10-16); Wettbewerb. Abhängigkeiten: SIC-901.
Abnahme: Ein Teilen-Link zeigt den Raum read-only und läuft nach 7 Tagen ab; der Export lässt sich in eine Zielplattform einlesen.

#### KUR-911 · Forum mit Threads und Abo-Mail · P3 · Aufwand M · Status: offen
- Forum je Kursraum, Abo per Mail mit Abmeldelink; Moderation wie Pinnwand.
- Herkunft: Wettbewerb (Moodle). Abhängigkeiten: BEN-901.
Abnahme: Eine Antwort löst Abo-Mails nur für Abonnenten aus.

#### KUR-912 · Dateiablage über Repositories · P3 · Aufwand L · Status: offen
- Anbindung von Nextcloud und WebDAV (zuerst), später OneDrive, Google Drive, S3.
- Herkunft: Wettbewerb (Moodle). Abhängigkeiten: SIC-908.
Abnahme: Eine WebDAV-Datei wird als Material verlinkt; interne Ziele werden abgelehnt.

#### KUR-913 · Bewusst nicht gebaute Lernfunktionen bestätigen · P3 · Aufwand S · Status: offen
- Entscheidung E-23: Quiz-System, SCORM, Plagiatsprüfung, KI-Assistenz, Plugin-Markt bleiben ungebaut; Quiz/H5P nur per Link oder LTI.
- Herkunft: Claude (Empfehlung); Betreiber-Bestätigung offen. Abhängigkeiten: E-23, INT-909.
Abnahme: Die Entscheidung liegt schriftlich vor; ein H5P-Inhalt lässt sich als Link einbinden.

#### KUR-914 · PDF-Anmerkungen und Medienplayer · P3 · Aufwand L · Status: offen
- PDF im Browser anmerken; Medienplayer im Kursraum.
- Herkunft: Wettbewerb (Moodle). Abhängigkeiten: keine.
Abnahme: Eine Anmerkung bleibt nach Neuladen sichtbar und nur für Berechtigte lesbar.

#### KUR-915 · Kursvorlagen, Archiv-Kopie, Kohorten · P3 · Aufwand M · Status: offen
- Kursvorlagen und Archiv-Kopie beim Schuljahreswechsel, Kohorten (Klassengruppen).
- Herkunft: Wettbewerb. Abhängigkeiten: STA-901.
Abnahme: Beim Wechsel entsteht aus dem Kursraum eine Kopie ohne Abgaben.

#### KUR-916 · Wiki, Glossar, Buch, Boards, Präsentationsmodus · P3 · Aufwand M · Status: offen
- Mehrseitiges Buch mit Versionen, Glossar, Kanban-Board, Präsentations- und Abfragemodus.
- Herkunft: Wettbewerb. Abhängigkeiten: keine.
Abnahme: Ein Buch speichert Versionen; ein Board lässt Karten zwischen Spalten verschieben.

#### KUR-917 · Lernpfad-Editor und OER-Suche · P3 · Aufwand L · Status: offen
- Lernpfade mit Binnendifferenzierung, OER-Suche per Schnittstelle mit Verlinkung (Fach- und Stufenvokabular).
- Herkunft: Wettbewerb. Abhängigkeiten: NOT-910.
Abnahme: Ein Pfad zeigt nach Erfüllen der Bedingung die nächste Station.

#### KUR-918 · Videokonferenz-Link und Open Badges 3.0 · P3 · Aufwand M · Status: offen
- Signierter Link zu BigBlueButton oder Landesdienst je Kursraum (Schlüssel nur serverseitig); signierte Open Badges mit Verifikations-URL.
- Herkunft: Wettbewerb. Abhängigkeiten: NOT-910.
Abnahme: Der Link öffnet den Raum mit der Rolle der Person; ein Badge lässt sich per URL prüfen.

#### KUR-919 · Weitere Kleinfunktionen · P3 · Aufwand M · Status: offen
- Schüler-Bücherei und Ausleihe, Stoffverteilungsplan zum Klassenbuch, Sprachnachrichten, Eltern-Feed mit Fotos nur nach Einwilligung und Prüfung.
- Herkunft: Wettbewerb. Abhängigkeiten: KLB-901.
Abnahme: Ein Stoffverteilungsplan füllt das Thema im Klassenbuch vor.

### 4.6 Nachrichten, Chats, Postfach, Rundschreiben

#### NAC-908 · Chat-Geräteschlüssel beim Abmelden entfernen · P0 · Aufwand S · Status: offen
- Beim Abmelden werden die Chat-Geräteschlüssel dieses Kontos aus dem Browser-Speicher gelöscht (Audit-Befund 10-17: sie bleiben stehen, obwohl die Umstellung als „nicht lesbar“ gemeldet wurde); beim nächsten Anmelden auf demselben Gerät muss das Gerät wieder gekoppelt oder aus der Sicherung wiederhergestellt werden; auf geteilten Geräten bleibt nie ein Schlüssel eines anderen Kontos zurück.
- Herkunft: Claude (Audit 10-17). Abhängigkeiten: keine.
Abnahme: Nach Abmelden enthält der Browser-Speicher keinen Chat-Schlüssel mehr; ein zweites Konto auf demselben Gerät kann den Verlauf des ersten nicht lesen.

#### NAC-901 · Lese-Status mit Namensliste und Erinnerung · P1 · Aufwand M · Status: offen
- Lesebestätigung mit einem Klick bei Mitteilungen und Briefen, vollständiger Lese-Status (wer hat gelesen, wer nicht) für Absender, Klassenleitung und Schulleitung, Erinnerung an Nicht-Leser; Lesestatus je Elternteil, Zustellung nur nach Elternfreigabe; Empfänger sehen den Status anderer nicht. Heute ist die Lesebestätigung nur teilweise vorhanden.
- Herkunft: Wettbewerb (Kleinfunktion 10-16, Schulmanager Online, Sdui); Claude (Marktreife 10-13). Abhängigkeiten: E-02, SIC-905.
Abnahme: Ein Brief an 30 Eltern zeigt dem Absender „gelesen 12, offen 18“ mit Namen; „Erinnerung senden“ erreicht nur die 18; ein Elternteil sieht nicht, wer sonst gelesen hat.

#### NAC-904 · Aufbewahrung von Chats mit Sternmarkierung · P1 · Aufwand M · Status: offen
- Betreiberwunsch: „Aufbewahrung 1 Monat, außer mit Stern markiert“. Laufende Frist für Chat-Nachrichten und -Bilder (Voreinstellung 1 Monat, 30 Tage), sternmarkierte Nachrichten sind ausgenommen [unklar: Stern je Person oder je Chat]; Löschen 1:1-Chat statt Blockieren spart Speicher.
- Herkunft: Betreiber (10-12 Betreiberwunsch O-11). Abhängigkeiten: DAT-902.
Abnahme: Eine 31 Tage alte Nachricht ist gelöscht, eine sternmarkierte bleibt; die Frist ist einstellbar und nicht auf „0“ setzbar.

#### NAC-907 · Chat-Moderation mit Einwilligung bei Ende-zu-Ende · P1 · Aufwand M · Status: offen
- Entscheidung E-13: Gemeldete Nachrichten brauchen Klartext; Melder gibt die gemeldete Nachricht oder einen Zeitraum frei, der Klartext geht nur an die Moderation (standardmäßig Schulleitung); Prüfung durch Berechtigte nur mit Zustimmung von Kind bzw. Eltern („ausdrücklich NICHT gewollt: Prüfung ohne Zustimmung“); dauerhafte Sicherung gemeldeter Nachrichten (Ort und Form offen); Melder und Gemeldete erfahren das Ergebnis [unklar]. Chat-Textkompression (Nachrichten rund 110 Byte) nicht bauen; keine Drittanbieter-GIF-Suche.
- Herkunft: Betreiber (10-12); Claude. Abhängigkeiten: E-13, REH-901.
Abnahme: Eine Meldung ohne Freigabe zeigt der Moderation keinen Klartext; mit Freigabe sieht nur die Moderation die gewählte Nachricht; der Zugriff steht im Protokoll.

#### NAC-913 · Rundschreiben an volljährige Schüler/innen · P1 · Aufwand S · Status: offen
- Entscheidung E-17: Ein Rundschreiben an Volljährige ohne Zustellwahl geht heute nur an den Schüler; Vorschlag: an beide, bis der Schüler „mich / meine Eltern / beide“ bewusst wählt; Hinweis auf die Volljährigkeit bleibt sichtbar bis zur Wahl.
- Herkunft: Betreiber-Frage (10-12), offen. Abhängigkeiten: E-17, SIC-905.
Abnahme: Ohne Wahl erhalten Schüler und Eltern das Rundschreiben; mit Wahl „mich“ nur der Schüler; Minderjährige immer beide.

#### NAC-902 · Elternbriefe mit Rückmeldung, Unterschrift, Einwilligung · P2 · Aufwand XL · Status: offen
- Brief an Klasse, Jahrgang oder Gruppe per App und Mail; Rückmeldung je Kind (Abschnitt zum Abtrennen), digitale Unterschrift, Einwilligungen mit Nachweis, Ausdruck für Eltern ohne Zugang, Umfrage im Brief mit CSV/PDF-Auswertung; Einwilligungsalter rechtlich festlegen; Zustellung nach Elternfreigabe.
- Herkunft: Betreiber („groß, später“, 10-16); Wettbewerb (Kernmodul Schulmanager Online); Claude (Backlog B-47). Abhängigkeiten: NAC-901, BEN-907, E-22.
Abnahme: Ein Brief mit Einwilligung zeigt je Kind „zugestimmt / abgelehnt / offen“ mit Zeitpunkt; ein Ausdruck für Eltern ohne Konto ist erzeugbar; Zustimmung ist widerrufbar.

#### NAC-903 · Briefübersetzung per Klick · P2 · Aufwand M · Status: offen
- Eltern lesen Briefe und Nachrichten in der eigenen Sprache (Mitbewerber 26 bzw. 40 Sprachen); abschaltbares Modul mit lokalem oder EU-Dienst mit AV-Vertrag; Namen von Kindern werden nicht übertragen.
- Herkunft: Wettbewerb; Claude (Backlog B-55); Dienstwahl offen (E-22). Abhängigkeiten: NAC-902, E-22.
Abnahme: „Übersetzen“ zeigt den Brief in der Zielsprache; im Übersetzungsaufruf fehlt jeder Kindername; bei ausgeschaltetem Modul fehlt der Knopf.

#### NAC-905 · Nachrichtenvorlagen · P2 · Aufwand S · Status: offen
- Eigene Vorlagen je Nutzer („Kind krank“, „Ausflug“), Schulvorlagen optional.
- Herkunft: Wettbewerb (Kleinfunktion 10-16). Abhängigkeiten: E-02.
Abnahme: Eine gespeicherte Vorlage füllt eine neue Nachricht; Vorlagen anderer Nutzer sind unsichtbar.

#### NAC-906 · Ruhezeiten und Erreichbarkeit · P2 · Aufwand S · Status: offen
- Administration legt Ruhezeiten fest (keine Nachrichten/Push in dieser Zeit); Lehrkraft kann „Sofort zustellen“ wählen; gilt auch für Nachrichten und Push (Frage offen); gesperrte Konten bleiben lesbar.
- Herkunft: Wettbewerb (Schulmanager Online, Moodle). Abhängigkeiten: BEN-907.
Abnahme: Eine Nachricht um 22:00 bei Ruhezeit 20–7 Uhr wird erst um 07:00 zugestellt; „Sofort zustellen“ umgeht die Ruhezeit.

#### NAC-909 · Chat-Bedienung vereinfachen · P2 · Aufwand M · Status: offen
- Stummschalten und Blockieren vereinfachen; 1:1-Chats löschen („nur für mich“ oder „für alle“ klären); Eltern erscheinen mit vollem Namen und klein „Kind: Name (Klasse)“, Suche nach Kindnamen schlägt die Eltern vor; Reiter „Neue Schlüssel“ und Geräteübersicht (letzte Aktivität) von der Betreiberseite prüfen lassen.
- Herkunft: Betreiber (10-12). Abhängigkeiten: SIC-910.
Abnahme: Ein 1:1-Chat lässt sich löschen; die Suche nach „Lina“ schlägt nur Eltern vor, die das Kind laut Regeln erreichen darf; die Geräteübersicht nennt die letzte Aktivität.

#### NAC-911 · Begriffe und Entwürfe in Nachrichten · P2 · Aufwand S · Status: offen
- Hilfetexte und Dokumente sagen noch „Postfach“, im Bereich heißt es „Nachrichten“; Entscheidung, ob Brief-Entwürfe bleiben (Betreiber: „Die Entwurffunktion kannst du auch weglassen“), Entwürfe nur anzeigen, wenn vorhanden.
- Herkunft: Betreiber (10-12/13). Abhängigkeiten: OBE-901.
Abnahme: Kein Hilfetext nennt „Postfach“; ohne Entwürfe fehlt der Bereich Entwürfe.

#### NAC-912 · Leistung des Nachrichtenversands · P2 · Aufwand M · Status: offen
- Im Lasttest dauerte der Versand 3 bis 5 Sekunden; Ziel unter 1 Sekunde bei 2500 Schüler/innen und 300 Lehrkräften.
- Herkunft: Claude (Lasttest 10-12). Abhängigkeiten: QUA-905.
Abnahme: Lasttest 95. Perzentil des Versands unter 1 s.

#### NAC-914 · E-Mail-Anbindung in Betrieb nehmen · P2 · Aufwand M · Status: offen
- Echter Test eines Mail-Kontos mit App-Passwort (Betreiber gibt Passwörter selbst ein); Microsoft-App registrieren und Google-Zugangsdaten hinterlegen; Anbieter-Vorlagen mit Servern und Link zur App-Passwort-Seite (IONOS, mailbox, Posteo, IServ); Token-Claims der Mail-OAuth mit Signaturprüfung; echtes Mail-Konto statt Brücke.
- Herkunft: Betreiber (10-11); Claude (Audit Anhang C). Abhängigkeiten: SIC-908.
Abnahme: Ein Testkonto ruft Mails ab und beantwortet sie in derselben Unterhaltung; ein unsigniertes Token wird abgewiesen.

#### NAC-916 · Datenschutzhinweis vor Backup und Mail-Anbindung · P2 · Aufwand S · Status: offen
- Vor der ersten Nutzung von Schlüssel-Backup und Mail-Anbindung (Kopien liegen auf dem Server) erscheint ein Hinweis über das Hilfe-Symbol zu Datenverarbeitung und Fristen; Seite `/datenschutz` für alle Rollen.
- Herkunft: Claude (Audit); Betreiber (legt Richtlinien noch fest). Abhängigkeiten: REH-901.
Abnahme: Erstnutzung des Backups zeigt den Hinweis einmal; danach nicht mehr.

#### NAC-917 · Terminumfrage · P2 · Aufwand M · Status: offen
- Doodle-artige Terminumfrage für Konferenzen und Eltern.
- Herkunft: Wettbewerb (Kleinfunktion). Abhängigkeiten: E-02.
Abnahme: Eine Umfrage mit drei Terminen zeigt die Verfügbarkeit je Person und schlägt den besten Termin vor.

#### NAC-910 · Chat-Speicher entlasten · P3 · Aufwand M · Status: offen
- Gruppenschlüssel statt eines Schlüssels je Nachricht und Gerät (Schlüsselzeilen rund 89 % des Textspeichers, Jahr 1: 2159 / 5397 / 10 794 MB für kleine/mittlere/große Schule); Chat-Bilder in die verschlüsselte Dateiablage (rund 57 MB je Schüler und Jahr); Bildverkleinerung im Browser (WebP, höchstens 2048 px); Entscheidung offen.
- Herkunft: Claude (10-12, Audit S-13). Abhängigkeiten: BET-914.
Abnahme: Eine Gruppe mit 400 Mitgliedern speichert höchstens eine Schlüsselzeile je Mitglied und Gruppenwechsel; Sicherungen wachsen mit Bildern nicht proportional.

#### NAC-915 · Kleine Chat- und Nachrichtenfunktionen · P3 · Aufwand S · Status: offen
- Umfragen im Chat über Abstimmungen hinaus, Sprachnachrichten, Zitate/Erwähnung/Favoriten, Suche in Briefen, Checklisten für Eltern-Nachrichten, Gruppenrecht „nur schreiben ohne Lesen“ (unklar).
- Herkunft: Wettbewerb (Schoolfox, Untis). Abhängigkeiten: keine.
Abnahme: Eine Chat-Umfrage zeigt Zwischenstand ohne Namen; die Suche findet Briefe nach Inhalt.

### 4.7 Formulare, Briefe, Zugangsdaten

#### FOR-901 · Einmal-Login statt Startpasswort · P1 · Aufwand M · Status: offen
- Betreiber (10-12): „Ich habe keine Beispiel für PDF gesehen für einen Einmallogin“. Der Zugangsbrief enthält nur einen einmaligen, befristeten Zugang (Einmalcode oder QR), der nach Gebrauch verfällt und zum Setzen des eigenen Passworts führt; kein wiederverwendbares Passwort; für Lehrkräfte, Schüler/innen und alle Rollen; Gültigkeitsdauer und Verlust-Verhalten festlegen [unklar]; Inhaber-Schutz gilt auch für Sammelwege.
- Herkunft: Betreiber (10-12); Claude. Abhängigkeiten: REC-901, ANM-905.
Abnahme: Der Brief-Code funktioniert genau einmal und läuft nach der festgelegten Frist ab; nach dem Setzen des Passworts ist der Code wertlos; ein Brief für das Inhaber-Konto wird abgewiesen.

#### FOR-904 · Formulare: Fehlerbehebung und Objektrechte · P1 · Aufwand M · Status: offen
- Kappung bei Listen und PDF-Export (300) beheben; Sichtbarkeit in der Abfrage; 409 statt 403 bei Doppelung; Eindeutigkeit „einmal je Kind“; Kommentar an Schritt binden; Zugriffsprüfung je Objekt bei Einreichungsliste, Eingang und Export; Zugangsbriefe-Druck auf Vollständigkeit prüfen.
- Herkunft: Claude (Bewertung 10-16, Paket W2-08; Marktreife 10-13). Abhängigkeiten: SIC-901.
Abnahme: Ein Formular mit 450 Einreichungen listet alle 450; eine zweite Einreichung „einmal je Kind“ → 409; fremde Einreichung per ID → 404.

#### FOR-902 · Konten beim Import mit anlegen · P2 · Aufwand M · Status: offen
- Konten beim Import optional mit anlegen, inklusive Zugangsbriefen; Personen ohne Konto werden heute erst danach ergänzt.
- Herkunft: Claude (10-16). Abhängigkeiten: FOR-901, INT-905.
Abnahme: Ein Import mit gesetzter Option erzeugt Konten und einen Brief-Stapel; ohne Option entstehen keine Konten.

#### FOR-903 · Anträge von Schüler/innen und Eltern über die Lehrkraft · P2 · Aufwand M · Status: offen
- Betreiber (10-12): Anträge laufen vom Kind zur Lehrkraft und von dort zu den Höhergestellten; heute nur Formularlinks. Öffentlicher Formularlink mit QR-Code für Schulanmeldungen nur auf Nachfrage.
- Herkunft: Betreiber (10-12 21:08). Abhängigkeiten: FOR-904.
Abnahme: Ein Antrag des Kindes erzeugt einen Vorgang bei der Lehrkraft und nach deren Weiterleitung bei der Schulleitung; jede Stufe ist protokolliert.

### 4.8 Stammdaten, Klassen, Jahrgänge und Stundentafeln, Schuljahr, Ferien, Einrichtung, Jahreswechsel

#### STA-903 · Einstellungen an ihrem Ort · P1 · Aufwand M · Status: offen
- Eigene Seite „Einstellungen“ (`settings.edit`) mit den Abschnitten Schule · Schulwoche & Zeitraster · Vertretung · Lehrkräfte · Krankmeldungen & Atteste · Nachrichten · Schnittstellen; jede Einstellung genau einmal; jeder Abschnitt speichert für sich (nur geänderte Felder); ungespeicherte Änderungen lösen beim Reiter- oder Seitenwechsel eine Rückfrage aus; die Nachrichten-Regeln stehen in den zentralen Einstellungen.
- Herkunft: Betreiber (A-32, 10-10/11 „Einstellungen am Ort“); Claude (Backlog B-22). Abhängigkeiten: keine.
Abnahme: Jede Einstellung kommt in genau einem Abschnitt vor; Speichern eines Abschnitts lässt Felder anderer Abschnitte unverändert; Seitenwechsel mit offenen Änderungen fragt nach.

#### STA-904 · Löschen mit Folgenvorschau, Rückgängig mit Fremdänderungen · P1 · Aufwand M · Status: offen
- Folgenvorschau und Rückgängig auch beim Löschen von Lehrkräften, Räumen, Standorten, Kursen und Schüler/innen (heute nur Klassen, Jahrgänge, Stundentafeln, Fächer); Rückgängig und Wiederherstellen zeigen vorher, welche Änderungen anderer Personen mitgehen (Wer, Was, Wann); Löschen einer Person sperrt das verknüpfte Konto (laufende Sitzungen enden), die Benutzerverwaltung zeigt „ohne Datensatz“ mit „deaktivieren / löschen“, Eltern sehen kein Kind ohne Klasse.
- Herkunft: Claude (Bestandsprüfung 10-10, Review 10-13). Abhängigkeiten: STA-905.
Abnahme: Löschen einer Lehrkraft nennt die betroffenen Kurse; danach kann sich ihr Konto nicht mehr anmelden; Rückgängig mit fremder Änderung zeigt „Frau X, 3. Stunde, gestern“ und verlangt Bestätigung.

#### STA-905 · Stammdaten-Integrität auf allen Wegen · P1 · Aufwand L · Status: offen
- Löschen verlangt dasselbe Schreibrecht wie Ändern (im Ist nur „angemeldet“ geprüft); eine gemeinsame Prüfung für Oberfläche, API, CSV, JSON und Untis: Pflichtfelder, Kennungen eindeutig ohne Beachtung der Groß-/Kleinschreibung, Kürzel ohne Leerzeichen, Verweise (Raum→Standort, Klasse→Raum/Lehrkraft/Jahrgang, Kurs→Klasse/Fach), einheitliche Grenzen der Klassenstufe (Assistent 1–13, Datenschnittstelle 0–20), konkurrierende Änderungen erkannt; neue Felder mit Standardwert und CSV-Rundlauf.
- Herkunft: Claude (Audit 10-17, Bestandsprüfung). Abhängigkeiten: SIC-901.
Abnahme: Lehrkraft ohne `masterdata.edit` löscht eine Klasse → 403; Anlegen einer Klasse mit Raum, der nicht existiert → 422 mit Klartext; CSV-Rundlauf erhält alle Felder.

#### STA-909 · Jahreswechsel: Hochstufen-Regel und Aktionen je Klasse · P1 · Aufwand M · Status: offen
- Fortschreibung des Klassennamens aus dem Namensmuster („5a“ → „6a“, „11a IT“ → „12a IT“) mit passendem Folgejahrgang (heute wird die Klassenstufe angehoben, der Jahrgang bleibt stehen); Aktion je Klasse versetzen / wiederholen / abschließen / belassen; einzelne Wiederholer und Abgänger markieren; leere Eingangsklassen je Bildungsgang; Klassenleitungen übernehmen ja/nein; Kurse und Stundentafeln fortschreiben. Ausführen und Rückgängig laufen bereits ganz oder gar nicht.
- Herkunft: Betreiber (A-39); Claude (Backlog B-37). Abhängigkeiten: STA-908.
Abnahme: „11a IT“ wird „12a IT“ mit Jahrgang 12; ein Wiederholer bleibt in der Stufe; Vorschau und Rückgängig bleiben erhalten.

#### STA-911 · Ausbildungsbetriebe (Berufskolleg) · P1 · Aufwand L · Status: offen
- Betriebe als Stammdaten (Name, Ausbilder/in, Kontakt verschlüsselt), Zuordnung der Auszubildenden, Praxistage; Grundlage für den Ausbilder-Zugang (SCH-908). Ohne Betriebszugang ist der Berufskolleg-Zweig laut Marktvergleich nicht verkaufbar.
- Herkunft: Claude (Marktvergleich, Backlog B-39); Betreiber (A-00 Berufskolleg). Abhängigkeiten: STA-908.
Abnahme: Ein Azubi ist einem Betrieb zugeordnet; die Betriebsliste zeigt ihn; fremde Betriebe liefern 404.

#### STA-901 · Module ein- und ausschalten · P2 · Aufwand M · Status: offen
- Funktionsbereiche (Notenbuch, Klassenbuch, Raumbuchung u. a.) je Schule ein- und ausschalten; ausgeschaltete Module erscheinen weder im Menü noch in der Schnittstelle, die Daten bleiben erhalten; Preismodell als Paket je Schule (E-24).
- Herkunft: Claude (Marktreife 10-13, Backlog B-56). Abhängigkeiten: BET-919, E-24.
Abnahme: Modul „Notenbuch“ aus → Menüpunkt weg, Schnittstelle antwortet 404; wieder ein → Daten sind unverändert da.

#### STA-902 · Schuljahr, Ferienvorlagen, Schulkalender · P2 · Aufwand M · Status: offen
- Ferienvorlagen je Bundesland als Datei mit Quellenangabe (mindestens NRW 2026/27 und 2027/28) per Klick, Import aus iCal/CSV, „Zurücksetzen“ für von Hand gelöschte Ferien, Feiertagsnamen auf Deutsch; Schulkalender (Monat, Woche, Liste) je Rolle mit Zielgruppen (Schule, Klassen, Klassengruppen, Jahrgänge, Lehrkräfte; Art Pflicht, freiwillig, Info); Halbjahresgrenzen einstellbar (heute fest 31.01./01.02.).
- Herkunft: Claude (Backlog B-25, B-26); Betreiber (Wochen/Ferien A-28). Abhängigkeiten: keine.
Abnahme: Die NRW-Vorlage trägt alle Ferien mit einem Klick ein; ein von Hand gelöschter Eintrag lässt sich zurücksetzen; ein Elternabend für „5a“ erscheint nur dort.

#### STA-906 · Raumtypen, Kursassistent, Auswahl und Handy-Karten · P2 · Aufwand M · Status: offen
- Raumtyp-Verwaltung und Fachbindung (allgemeine Räume und Fachräume mit Ausstattung); Kursassistent mit Teilnehmerübersicht und Zuteilungsvorschau mit Rückgängig; Schülerlisten nach Klassen gruppiert und durchsuchbar; Fächer mit Schrägstrich („Mu/Ku“) erlaubt (Hinweis „Mugs“ unklar); Einrichtungs-Stepper am Handy; Karten statt Tabellen unter 600 px bei mehr als 5 Spalten; Entwürfe gehen beim Reiterwechsel nicht verloren.
- Herkunft: Betreiber (10-11/12); Claude (Review 10-13). Abhängigkeiten: STP-926.
Abnahme: Ein Fach mit Raumtyp „Informatik“ wird nur in Räumen dieses Typs geplant; die Klassenauswahl gruppiert Schüler/innen nach Klasse.

#### STA-908 · Klassenrollen im Datenmodell · P2 · Aufwand XL · Status: offen
- Mehrere Klassenleitungen (Reihenfolge = Hauptverantwortung), Stellvertretung, Abteilungsleitung (Rechte für die Klassen ihrer Abteilung), Klassensprecher/in (höchstens 2 Schüler/innen), Verwalter einer Klasse (pflegt Raum, Rollen, Schülerliste, erzeugt Zugangsdaten ohne globale Rechte). Entscheidung E-30: von Anfang an im Datenmodell, sonst Folgeänderungen in Kursräumen, Selbstbereich, Klassenkonten, Rechten und Löschweitergabe.
- Herkunft: Betreiber (A-41 bis A-43, Rückmeldung „Abteilungsleitung“, 10-10/11); Claude. Abhängigkeiten: E-30.
Abnahme: Bei zwei Klassenleitungen sehen beide Fehlzeiten und Klassenbuch; Klassensprecher sehen keine Fehlzeiten; die Abteilungsleitung sieht nur Klassen ihrer Abteilung; ein Verwalter erzeugt Zugangsbriefe ohne globale Rechte.

#### STA-910 · Einrichtung: Vorlagen, Startschulen, Konfigurationsdateien · P2 · Aufwand L · Status: offen
- Zeitraster-Vorlagen je Schulform, Stundentafel-Vorlagen je Bundesland und Schulform; Beispielschulen (Gymnasium, Gesamtschule, Berufskolleg NRW) als wählbare, wirklich importierbare Startvorlage; Konfigurationsdateien: Schulstruktur mit oder ohne Personen als ZIP mit Manifest und je Bereich einer CSV, Übernahme mit Probelauf; Durchlauf „Schule von Null“ durch den Betreiber (steht aus), Klärung ob 12 oder 13 Einrichtungsschritte; Browser-Prüfung der Fehleranzeige in der Einrichtungstabelle.
- Herkunft: Betreiber (10-16 „von null auf die Schule aufsetze“, A-37); Claude (Backlog B-17). Abhängigkeiten: STA-903.
Abnahme: Die Startschule „Berufskolleg NRW“ lässt sich importieren; die Struktur einer Schule lässt sich exportieren und in einer leeren Instanz mit Probelauf übernehmen; die Einrichtung weist die Schritte und ihre Zahl eindeutig aus.

#### STA-907 · Klassenprinzipien und Mischaltersgruppen als Option · P3 · Aufwand L · Status: offen
- Jahrgangsübergreifende Klassen (mehrere Jahrgangswerte statt Notbehelf Mittelwert), Sonderstunden für Einzelne, Förderstunden je Person, Lerngruppen aus mehreren Klassen; Betreiber 10-11: „soll garantiert nicht der Standard sein“.
- Herkunft: Betreiber (10-11/12). Abhängigkeiten: STP-908.
Abnahme: Eine Klasse mit Jahrgängen 1 bis 3 wird ohne Notbehelf angelegt; Standardschulen sehen die Option nicht.

### 4.9 Lehrkräfte (Profil, Verfügbarkeit, Anträge)

#### LEH-904 · Verfügbarkeit mit Wiederholungsregeln und Ausnahmen · P1 · Aufwand L · Status: offen
- Grundwochenplan (leer = immer verfügbar) plus Ausnahmen mit Wiederholung: wöchentlich (alle n Wochen ab Datum), monatlich (n-ter Wochentag), jährlich, mit Gültigkeitszeitraum; Satzbaukasten und Vorschau acht Wochen. Beispiele des Betreibers als Tests: „jeden 1. Mittwoch im Monat“, „jede 3. Woche nicht“, „alle 2 Wochen erst ab 10“, „mittwochs nie nach 12“, „erst ab 9“. Sonderfälle beim Schulwechsel (Wechsel nur in Pausen, nur einmal hin und her) prüfen. Rhythmus und „Gilt ab“ sind gebaut.
- Herkunft: Betreiber (A-50, A-51); Claude (Backlog B-35, B-42). Abhängigkeiten: STP-906.
Abnahme: „Jeden 1. Mittwoch im Monat nicht“ sperrt genau diese Mittwoche im Raster und für Generator und Vertretung; die Vorschau zeigt acht Wochen.

#### LEH-906 · Selbstverwaltung begrenzen, „kann vertreten in“ · P1 · Aufwand M · Status: offen
- Lehrkräfte bestimmen nicht selbst Höchststunden oder Vertretungsgrenzen; sie geben Tage/Verfügbarkeit und höchstens eine gewünschte Höchstzahl Wochenstunden als genehmigungspflichtigen Wunsch an (E-32c); Deputat und Grenzen setzt die Planung; „Wunschklassen“ entfallen, das Profil zeigt „Klassenleitung in“, „Ich unterrichte“ (nur lesen) und „Ich kann vertreten in“ (bearbeitbar), vorhandene Wunschklassen werden einmalig übernommen.
- Herkunft: Betreiber (A-48, A-49); Claude. Abhängigkeiten: E-32.
Abnahme: Eine Lehrkraft kann `max_hours` nicht direkt ändern, nur als Wunsch beantragen; „kann vertreten in 7b“ wirkt auf die Vertretung (VER-901).

#### LEH-902 · Anträge: Genehmigung durch Sekretariat, „Ich bin neu“ · P2 · Aufwand S · Status: offen
- Entscheidung E-15(b): Sekretariat darf Lehrkraft-Anträge genehmigen (heute Planung, Schulleitung, Admin) über einen Schalter der Rechte-Matrix, Standard aus; ein Lehrerkonto ohne verknüpfte Lehrkraft beantragt „Ich bin neu“ (die Planung legt an und verknüpft), neues Fach mit Option „auf vorhandenes Fach abbilden“.
- Herkunft: Claude/Betreiber-Frage (10-13), offen. Abhängigkeiten: REC-908, E-15.
Abnahme: Mit Schalter an genehmigt das Sekretariat einen Antrag; ohne Schalter 403; „Ich bin neu“ erzeugt einen Planer-Vorgang statt 409.

#### LEH-903 · Abwesend-bis-Hinweis, Fortbildungsanträge, Einzelprofil · P2 · Aufwand M · Status: offen
- „Abwesend bis …, Vertretung X“ nur als Hinweis im Profil und Chat, nie als Auto-Antwort an Eltern (Datenschutz); Fortbildungsanträge mit Genehmigung (Termine mit teilnehmenden Lehrkräften sind gebaut); Einzelprofil-Seite je Lehrkraft.
- Herkunft: Wettbewerb (Kleinfunktion 10-16); Betreiber (10-12). Abhängigkeiten: E-02, E-32.
Abnahme: Der Hinweis erscheint im Profil und im Chat mit der Lehrkraft; es geht keine Auto-Nachricht an Eltern; ein Fortbildungsantrag durchläuft die Genehmigung.

#### LEH-901 · Arbeitstage und Mindeststunden verfolgen (Entscheidung) · P3 · Aufwand S · Status: offen
- Betreiber (10-11): „dass die auch wirklich ihre Arbeitstage halten“; Einchecken beim Unterricht und Verfolgen von Arbeitstagen und Mindeststunden (modular). Mitbestimmung, Personalrat prüfen; Empfehlung E-32(a): nicht bauen, bis rechtlich geprüft.
- Herkunft: Betreiber (10-11/12). Abhängigkeiten: E-32.
Abnahme: Entscheidung liegt schriftlich vor; ohne Freigabe existiert keine Einchecken-Funktion.

#### LEH-905 · Wertrechnung und Deputat-Modell · P3 · Aufwand L · Status: offen
- Soll-/Ist-Werte, Fach-Faktoren, Anrechnungsstunden, Jahresmittel, Lehrer-Jahresarbeit; Mehrarbeit nach KMBek nur auf Nachfrage Bayern.
- Herkunft: Wettbewerb (Untis). Abhängigkeiten: E-31, STP-924.
Abnahme: Die Wertrechnung zeigt je Lehrkraft Soll, Ist und Abweichung im Jahresmittel.

### 4.10 Schüler/innen und Eltern (Familie, Selbstbedienung)

#### SCH-910 · Erziehungsberechtigte, Freigaben und Sichtbarkeit für Familien · P1 · Aufwand L · Status: offen
- Tabelle der Erziehungsberechtigten (Name, E-Mail, Telefon verschlüsselt, Beziehung, Sorgerecht, optional verknüpftes Konto), Geschwister teilen ein Elternkonto, Angaben aus Klassen-Assistent gehen nicht verloren; Kindauswahl je Konto; Vermerk (für Familie sichtbar) und interne Notiz getrennt, archivierte Dokumente nicht mehr prüfbar; Entscheidung E-16: Altersgrenze 18 bestätigen, „Meine Fehlzeiten“ für Minderjährige ausblenden (Betreiber 10-12: „Sollte Ansichten sind komplett unnötig für die Kinder“), Hausaufgaben und Thema sichtbar, Notizen nie; Hinweise zu Minderjährigen; Ursache der Meldung „Stundenplan bei Schülern nicht sichtbar“ klären.
- Herkunft: Betreiber (A-41, A-44, 10-12); Claude (Paket W2-11, Audit). Abhängigkeiten: E-16, SIC-905.
Abnahme: Zwei Kinder derselben Familie teilen ein Elternkonto; Eltern eines Minderjährigen sehen die Fehlzeiten, das Kind nicht; die interne Notiz ist für Familien nie sichtbar.

#### SCH-905 · Schulbegleitung für mehrere Kinder · P1 · Aufwand S · Status: offen
- Schulbegleitung als eigene Rolle mit allen zugewiesenen Kindern gleichberechtigt (heute erstes Kind als Hauptbezug, weitere nur in einer Liste), Auswahl wie bei Eltern.
- Herkunft: Betreiber (10-12 „funktioniert nur für ein Kind“). Abhängigkeiten: REC-906.
Abnahme: Schulbegleitung mit drei Kindern wechselt zwischen allen dreien; fremde Kinder liefern 404.

#### SCH-908 · Ausbilder-Rolle für Ausbildungsbetriebe · P1 · Aufwand L · Status: offen
- Betriebe sehen Plan und Fehlzeiten ihrer Azubis; Zugang gegen den Wunsch volljähriger Azubis je Bildungsgang festlegen und rechtlich prüfen; Mitzeichnung bei Beurlaubungen optional.
- Herkunft: Claude (Marktvergleich, Backlog B-39). Abhängigkeiten: STA-911, REC-906.
Abnahme: Ein Ausbilder sieht nur Azubis seines Betriebs; ein volljähriger Azubi kann den Zugang für seine Daten sperren.

#### SCH-901 · Elternsprechtag mit Terminvergabe · P2 · Aufwand L · Status: offen
- Sprechtag anlegen (Datum, Zeitfenster, Anmeldephase, Slotlänge 5 oder 10 Minuten, Puffer, Raum, vor Ort oder online mit Link); Eltern sehen nur Lehrkräfte ihrer Kinder und buchen am Handy; Geschwister im selben Block, Wunschlisten, Wegzeiten, Wartelisten; Terminliste als PDF ohne Namen; Optimierung „beste Reihenfolge“; Entscheidung, ob Schüler zu parallelen Gesprächen Zugang haben (E-22).
- Herkunft: Betreiber („groß, später“, 10-16); Wettbewerb. Abhängigkeiten: NAC-902, E-22.
Abnahme: Zwei Eltern buchen denselben Block → die zweite Buchung wird abgelehnt; Geschwister landen im selben Block; das PDF enthält keine Kindernamen.

#### SCH-902 · Sprechstunden und Elterngespräche · P2 · Aufwand M · Status: offen
- Buchung von Sprechstunden bei Fachlehrkräften; Terminvorschläge der Klassenleitung für Elterngespräche.
- Herkunft: Wettbewerb. Abhängigkeiten: SCH-901.
Abnahme: Eine Lehrkraft veröffentlicht 3 Slots; Eltern des Kindes buchen einen, fremde Eltern sehen sie nicht.

#### SCH-903 · Hausaufgaben-Übersicht · P2 · Aufwand S · Status: offen
- Eine Liste mit Fälligkeit aus Klassenbuch und Kursräumen für Eltern und Schüler/innen (Wettbewerbs-Kleinfunktion 10-16), nur Zusammenführung vorhandener Daten.
- Herkunft: Wettbewerb. Abhängigkeiten: E-02.
Abnahme: Die Liste zeigt alle offenen Aufgaben des Kindes mit Frist, sortiert nach Datum; Hausaufgaben anderer Kinder fehlen.

#### SCH-904 · Kalender-Abo je Rolle und Kind · P2 · Aufwand M · Status: offen
- Ausbau des persönlichen iCal-Feeds: Klausuren, Termine, Ferien, Hausaufgaben je Rolle und je Kind (heute nur das erste Kind); Eltern Volljähriger ohne Freigabe ausgeschlossen.
- Herkunft: Wettbewerb (Kleinfunktion 10-16); Claude (Audit P1-05). Abhängigkeiten: SIC-905.
Abnahme: Eltern mit zwei Kindern abonnieren je Kind einen Feed; der Feed eines volljährigen Kindes ohne Freigabe bleibt leer.

#### SCH-906 · Klassendienste und Geburtstagsliste · P3 · Aufwand S · Status: offen
- Tafel- und Ordnungsdienst mit Zeitraum und Rotation; Geburtstagsliste für die Klassenleitung (nur Tag und Monat, nur Klassenleitung, standardmäßig aus mit Schalter); „nur auf Nachfrage“.
- Herkunft: Wettbewerb (10-16). Abhängigkeiten: E-02.
Abnahme: Die Liste ist ohne Schalter leer; mit Schalter sieht nur die Klassenleitung Tag und Monat, kein Jahr.

#### SCH-907 · QR-Login für Kinder · P3 · Aufwand M · Status: offen
- Zugangsbrief mit QR für Klasse 1 bis 4; Einmal-Token, Ablauf, Anmelderichtlinie und Sicherheitsfragen vorher klären.
- Herkunft: Wettbewerb (10-16 „nur auf Nachfrage“). Abhängigkeiten: FOR-901.
Abnahme: Ein QR-Code funktioniert einmal und verfällt; nach Ablauf ist er wertlos.

#### SCH-909 · Ganztag-Modul · P3 · Aufwand L · Status: offen
- Externes Betreuungspersonal, digitale Anwesenheit, Abholzeiten, Verhaltens- und Beobachtungseinträge (sensibel, Rechtsgrundlage klären), Elternmitteilungen, Rolle Ganztagskraft; Entscheidung E-31.
- Herkunft: Wettbewerb (Schulmanager Online). Abhängigkeiten: E-31.
Abnahme: Eine Ganztagskraft sieht nur ihre Gruppe; Verhaltenseinträge sind nur für Berechtigte lesbar.

#### SCH-911 · Schülerakte mit Kategorien · P3 · Aufwand L · Status: offen
- Kategorien mit Feldern, Rechte je Kategorie, Vorlagen als PDF an Eltern, Export, Rolle „Schüleraktenverwalter“; Auskunft und Löschfristen mitdenken.
- Herkunft: Wettbewerb. Abhängigkeiten: SCH-910, E-31.
Abnahme: Eine Kategorie ist nur für die zugeordnete Rolle lesbar; der Export enthält nur erlaubte Kategorien.

#### SCH-912 · Mensa/Speiseplan und Notfallbenachrichtigung · P3 · Aufwand M · Status: offen
- Speiseplan als Anzeige oder Link (keine Bestellung); Notfallkommunikation (SMS, Räumungsliste) auf Basis von Anwesenheit und Push; später, Entscheidung E-31.
- Herkunft: Wettbewerb; Claude. Abhängigkeiten: BEN-907, E-31.
Abnahme: Der Speiseplan erscheint als Link ohne Bestellfunktion; die Notfallliste nennt nur anwesende Kinder.

### 4.11 Rechte und Rollen

#### REC-901 · Inhaber-Schutz zentral auf allen Wegen · P0 · Aufwand M · Status: offen
- Das Inhaber-Konto (oberster Account) ist nur vom Inhaber änderbar (Rolle, Sperre, Löschen, Passwort, 2FA-Reset, Sitzungen). Der Schutz liegt in der zentralen Konten-Änderungsstelle, die jeder Weg nutzt: direkt, Zugangsbriefe, Massen-Reset, Import, API-Zugang mit Schreibrecht, beobachtete Konten, zweite Administratoren. Heute gilt er nur auf dem direkten Weg; der Massen-Reset über Zugangsbriefe umging ihn (live bestätigt). Der Versuch wird abgewiesen und protokolliert.
- Herkunft: Betreiber (10-17 18:02, Grundsatz); Claude (Audit/Pentest 10-17, Vorfall 10-16). Abhängigkeiten: E-03.
Abnahme: Ein zweiter Admin startet einen Massen-Reset mit dem Inhaber-Konto in der Auswahl → das Konto wird abgelehnt und der Versuch protokolliert; direkter Weg und API-Zugang mit Schreibrecht → 403.

#### REC-910 · Admin-Konten überwachen, Rollenwechsel melden · P0 · Aufwand M · Status: offen
- Neue Admin-Konten, Rollenwechsel von oder zu Admin, Herabstufung und Löschung lösen sofort eine Benachrichtigung an den Inhaber und alle Admins aus; Admin-Konten legt nur der Inhaber an (oder wer das Recht ausdrücklich hat); jede Admin-Aktion und jeder Rollenwechsel ist vollständig nachvollziehbar protokolliert; Schreibzugriff auf Live-Daten nur mit Freigabe des Betreibers. Beobachtete Konten legen standardmäßig keine Admins an (gebaut).
- Herkunft: Claude (Lehre aus dem Vorfall 10-16/17). Abhängigkeiten: REC-901, BEN-901.
Abnahme: Das Anlegen eines Admin-Kontos erzeugt innerhalb 1 Minute eine Benachrichtigung an den Inhaber und einen Protokolleintrag mit Urheber; ein Rollenwechsel des Inhaber-Kontos wird abgewiesen.

#### REC-902 · Delegation des Inhaber-Passwort-Resets · P1 · Aufwand M · Status: offen
- Betreiber (10-17 18:02): „Dem Admin soll man grundsätzlich nicht seine Admin-Rechte nehmen können. … Es sei denn, es gibt einen zweiten Admin, dem der erste Admin den Zugang gegeben hat, seinen Password zurückzusetzen.“ Entscheidung E-05: nur ausdrückliche Vergabe durch den Inhaber, jederzeit widerrufbar, Benachrichtigung des Inhabers, Protokoll; erst nach REC-901.
- Herkunft: Betreiber (10-17); Claude fragte zweimal, keine Freigabe. Abhängigkeiten: REC-901, E-05.
Abnahme: Ohne Vergabe weist das System den Reset des Inhaber-Kontos ab; mit Vergabe gelingt er, der Inhaber wird benachrichtigt und kann die Vergabe widerrufen.

#### REC-903 · Alle Rechte serverseitig erzwingen · P1 · Aufwand M · Status: offen
- Acht Rechte stehen auf „geplant“ und werden nicht geprüft (u. a. Stammdaten lesen, Förderdaten, Pausenaufsichten verwalten, Eigenarbeit freigeben); die Lizenzseiten prüfen `system.admin` statt `license.manage`; ein Test ordnet jedem Recht mindestens eine Route zu und prüft sie je Rolle.
- Herkunft: Claude (Bestand 10-12). Abhängigkeiten: SIC-901.
Abnahme: Für jedes Recht des Katalogs gibt es eine Route, die ohne das Recht 403 oder 404 liefert; der Test schlägt bei einem ungeprüften Recht fehl.

#### REC-904 · Rechte-Konsistenz Frontend und Backend · P1 · Aufwand M · Status: offen
- Text der gesperrten Regeln aus der Quelle ableiten; Rollenlisten in Backend und Frontend aus einer Quelle; Selbstaussperrung der Schulleitung verhindern; Zurücksetzen einer Rolle auf Standardrechte.
- Herkunft: Claude (Bewertung 10-16, Paket W2-03). Abhängigkeiten: REC-903.
Abnahme: Die Rollenliste ist in beiden Schichten identisch; die Schulleitung kann sich das Recht für die Rechteseite nicht selbst entziehen; „Zurücksetzen“ stellt die Standardrechte her.

#### REC-906 · Schulbegleitung und Ausbilder im Rechtekatalog · P1 · Aufwand M · Status: offen
- Rollen Schulbegleitung und Ausbilder mit Scope: nur zugewiesene Kinder bzw. Auszubildende, Lesen von Plan und Fehlzeiten, keine Noten ohne Freigabe; Grundtyp Eltern bzw. Personal je nach Rolle festlegen.
- Herkunft: Betreiber (10-12 Schulbegleitung); Claude (Backlog B-39). Abhängigkeiten: SCH-905, SCH-908.
Abnahme: Ein Konto der Rolle Schulbegleitung sieht nur die zugewiesenen Kinder; fremde Kinder liefern 404.

#### REC-905 · Rechte-Vorschau „Sicht als Rolle“ · P2 · Aufwand L · Status: offen
- Änderungen an Rechten und Rollen vor dem Speichern als Vorschau der Sicht der Rolle testen.
- Herkunft: Claude (Paket W4-05). Abhängigkeiten: REC-903.
Abnahme: Die Vorschau zeigt Menü und Seiten der Rolle ohne Daten zu schreiben; Speichern übernimmt die Rechte erst nach Bestätigung.

#### REC-907 · Passwort-Reset-Rechte · P2 · Aufwand M · Status: offen
- Reset durch Klassenleitung für eigene Schüler mit Protokoll; „Operator mit Genehmigung“ (höhergestellt, bei Passwort-Reset) als Berechtigung; Regel „Elternkonten zurücksetzen nur Sekretariat, Schulleitung, Administration“ bestätigen (der Betreiber nannte Klassenlehrkräfte, Admins und höhergestellte Operatoren); Schüler/innen setzen nicht selbst zurück.
- Herkunft: Betreiber (10-12); Wettbewerb. Abhängigkeiten: E-15.
Abnahme: Klassenleitung setzt das Passwort eines Schülers ihrer Klasse zurück (Protokoll); für eine fremde Klasse 404.

#### REC-908 · Rechte-Fragen aus Tests · P2 · Aufwand S · Status: offen
- Entscheidung E-15: (a) Rolle Schulleitung darf den Generator starten (heute nur Planung) über einen Rechte-Schalter, Standard aus; (b) Sekretariat genehmigt Lehrkraft-Anträge (LEH-902); (c) Reset-Regel für Elternkonten bestätigen.
- Herkunft: Claude (Test 10-16); Betreiber offen. Abhängigkeiten: E-15.
Abnahme: Schulleitung ohne Schalter startet den Generator nicht (403); mit Schalter ja.

#### REC-909 · Demo-Administration und Verhalten von Monitor und Zuschauer · P2 · Aufwand S · Status: offen
- Demo-Admin-Zugänge ohne `system.admin` und `rights.manage` (eigene Rolle „Demo-Administration“); einheitliches Verhalten von Monitor und Zuschauer bei der Formular-Übersicht (abweisen statt leerer Zähler); „Vorführkonto sieht alles wie die Schulleitung“ gegen die Datenschutz-Mindestregeln abgleichen.
- Herkunft: Claude (Audit S-03, 10-17). Abhängigkeiten: BET-903.
Abnahme: Das Demo-Admin-Konto kann keine Rechte vergeben; Monitor und Zuschauer erhalten bei der Formular-Übersicht dieselbe Abweisung.

### 4.12 Anmeldung, SSO, Zwei-Faktor, Sitzungen, Konten

#### ANM-901 · Zwei-Faktor für Personal als Pflicht, Wiederherstellungscodes · P0 · Aufwand M · Status: offen
- Heute nur empfohlen, Wiederherstellungscodes fehlen. Entscheidung E-04: Pflicht für Administration, Schulleitung, Sekretariat und Planung (Lehrkräfte einstellbar); Einmal-Wiederherstellungscodes (gehasht, einmal anzeigbar); 2FA-Reset nur durch den Inhaber; ohne Einrichtung nach der Frist keine Anmeldung.
- Herkunft: Claude (Audit P3-04, Pentest 10-17); Betreiber-Entscheidung offen. Abhängigkeiten: E-04.
Abnahme: Ein Admin ohne 2FA wird nach der Frist zur Einrichtung gezwungen; ein Wiederherstellungscode funktioniert einmal; ein 2FA-Reset durch einen anderen Admin wird abgewiesen.

#### ANM-902 · Gleiche 2FA-Regel auf allen Anmeldewegen · P0 · Aufwand M · Status: offen
- SSO (Google, Microsoft, Apple, später Landes-Login) umgeht die lokale 2FA; alle Wege erzwingen dieselbe Regel; Kontoverknüpfung nur mit bestätigter Adresse; den Befund „nach Abmeldung bleiben weitere Konten ohne Passwort wählbar“ klären und abstellen.
- Herkunft: Claude (Audit P3). Abhängigkeiten: ANM-901.
Abnahme: Ein Admin mit Pflicht-2FA meldet sich per SSO nur nach dem zweiten Faktor an; ein Konto ohne bestätigte Adresse wird nicht verknüpft.

#### ANM-903 · Client-IP hinter Proxy für IPv4, IPv6 und VPN · P0 · Aufwand M · Status: offen
- Anfragen erscheinen mit einer internen Docker-Adresse statt der Client-IP (IPv6-Weiterleitung vermutet); Proxy-Header gelten nur von festen Proxy-Adressen; Lösungswege Docker-IPv6, Host-Proxy oder PROXY-Protokoll; Betriebsdoku ergänzen. Ohne Korrektur wirken alle IPv6-Nutzer wie eine Adresse (Protokoll, Anmelde-Drosselung). Betreiber (10-17): „Ja, aber er benutzt eine VPN um sich einzuloggen, also keine Ahnung, wie das das jetzt beeinflusst hat.“ VPN-Adressen sind nur Austrittsadressen.
- Herkunft: Betreiber (10-17); Claude. Abhängigkeiten: BET-905.
Abnahme: Eine Anfrage über IPv6 und eine über IPv4 erscheinen im Protokoll mit der jeweiligen gekürzten Client-Adresse; die Drosselung unterscheidet sie.

#### ANM-915 · Vorfall vom 16.10. nachbereiten · P0 · Aufwand S · Status: offen
- Entscheidung E-08: (a) Klärung der Anmeldung als „monitor“ am 16.10. 21:49 von außerhalb; bei „nein“ Passwörter von Administration und Monitor ändern und alle Sitzungen beenden (sechs offene Admin-Sitzungen); (b) das selbst angelegte, herabgestufte, deaktivierte Konto nur mit 2FA reaktivieren; (c) Konto „betatester“ nach Ende des Betatests löschen; Herkunft der vier Protokolleinträge „Attest erlassen“ klären; Admin-Passwort der Hauptinstanz stärken.
- Herkunft: Claude (Vorfall 10-16/17); Betreiber-Antwort offen. Abhängigkeiten: E-08.
Abnahme: Die Antwort des Betreibers liegt vor; bei „nein“ sind Passwörter geändert und alle Sitzungen der Konten beendet; das Ergebnis steht im Protokoll.

#### ANM-904 · Passwort-Spraying erkennen, Anmeldefehler protokollieren · P1 · Aufwand M · Status: offen
- Fehlversuche (Zeit, Konto-Kennung, gekürzte Adresse) ins Protokoll; Erkennung vieler Konten mit gleichem Passwort über IP-Grenzen mit Alarm an die Administration; progressive Verzögerung bleibt, nie harte Kontosperre.
- Herkunft: Claude (Audit P3). Abhängigkeiten: SIC-904.
Abnahme: 50 Anmeldeversuche auf 50 Konten mit demselben Passwort aus verschiedenen Adressen lösen einen Alarm aus; jeder Fehlversuch steht im Protokoll.

#### ANM-905 · Passwortregeln und Leak-Prüfung · P1 · Aufwand M · Status: offen
- Entscheidung E-06: Trivialliste mindestens 3000 Einträge (heute rund 120); Mindestlänge 10 für Personal, 8 für Schüler/innen und Eltern; Leak-Prüfung zuerst als Offline-Liste, Online-Prüfung mit Hash-Präfix nur als abschaltbare Option (heute eingebaut, aus); Hash-Parameter festlegen (scrypt; die Quellen nennen N ≥ 16384 bzw. N = 2^15 als Befund) [unklar: Zielwert].
- Herkunft: Claude (Audit, ASVS); Betreiber-Entscheidung offen. Abhängigkeiten: E-06.
Abnahme: Ein Passwort aus der 3000er-Liste wird abgelehnt; ein Personalkonto mit 8 Zeichen wird abgelehnt, ein Schülerkonto akzeptiert.

#### ANM-906 · Sitzungen und Token bei Ereignissen widerrufen · P1 · Aufwand M · Status: offen
- Sitzungen und Tokens enden bei Passwortwechsel, Reset, Sperre, 2FA-Reset, Herabstufung, Austritt und Volljährigkeit; „Alle anderen Sitzungen beenden“ je Konto mit Geräteliste; (API-Tokens: INT-902).
- Herkunft: Claude (Audit P3-02/03). Abhängigkeiten: INT-902.
Abnahme: Nach einem Passwortwechsel sind alle anderen Sitzungen ungültig; die Geräteliste zeigt Gerät und letzte Aktivität.

#### ANM-914 · Passkeys und Passwort-Manager-taugliche Anmeldung · P1 · Aufwand L · Status: offen
- Passkeys (WebAuthn, feste Bibliotheksversion), eindeutige Anmeldeformulare für Passwort-Manager, Geschwister und mehrere Erziehungsberechtigte in einem Konto (zweiter Zugangscode); 2FA zusätzlich per E-Mail oder SMS (BEN-909).
- Herkunft: Betreiber (A-26, A-27); Claude (Backlog B-21). Abhängigkeiten: ANM-901.
Abnahme: Ein Konto meldet sich mit Passkey an; ein Passwort-Manager erkennt Benutzername und Passwort-Feld.

#### ANM-907 · Anbieter-Anmeldung einrichten und prüfen · P2 · Aufwand S · Status: offen
- Google-OAuth-Client und Microsoft-Entra-App (kostenlos) und Apple (Entwicklerkonto 99 $ bzw. 99 € je Jahr, Standardport 443) legt der Betreiber selbst an; Anmeldeknöpfe nach Eintrag der IDs im Browser prüfen; Google-Test mit nicht standardmäßigem Port.
- Herkunft: Betreiber (10-12/16). Abhängigkeiten: ANM-913.
Abnahme: Die Knöpfe erscheinen nur bei eingetragener ID; eine Testanmeldung gelingt mit Google und Microsoft.

#### ANM-908 · Sitzungsdauer je Rolle · P2 · Aufwand S · Status: offen
- Pflichtlaufzeit: Personal 12 Stunden Inaktivität (gebaut), Schüler/innen und Eltern einstellbar, Höchstdauer für alle Rollen (Audit: 7 Tage Inaktivität / 30 Tage heute für alle).
- Herkunft: Claude (Audit S-17). Abhängigkeiten: ANM-906.
Abnahme: Eine Schüler-Sitzung endet nach der eingestellten Inaktivität; die Höchstdauer wird auch bei Aktivität durchgesetzt.

#### ANM-910 · Landes-Login Schulconnex/VIDIS · P2 · Aufwand L · Status: offen
- Login mit Rolle, Schulnummer und Gruppen beim Anmelden, Provisionierung, später Gruppen-Abgleich; laut Recherche (ungeprüft) Voraussetzung für Verkauf in NRW, Niedersachsen und Sachsen; Entscheidung E-21 (NRW zuerst).
- Herkunft: Betreiber („groß, später“, 10-16); Wettbewerb. Abhängigkeiten: ANM-912, INT-910, E-21.
Abnahme: Ein Testkonto des Landesdienstes meldet sich an, erhält die Rolle aus dem Claim und sieht nur Daten seiner Schule.

#### ANM-912 · OIDC-Verbesserungen · P2 · Aufwand S · Status: offen
- Gruppen-Claim und Rollen-Mapping je Anbieter, Backchannel-Logout, mehrere Anbieter je Schule.
- Herkunft: Claude (Recherche 10-13). Abhängigkeiten: ANM-902.
Abnahme: Ein Logout beim Anbieter beendet die lokale Sitzung; ein Gruppen-Claim ordnet die Rolle zu.

#### ANM-913 · Anmeldedienste je Zielgruppe · P2 · Aufwand S · Status: offen
- Entscheidung E-37: Google- und Apple-Anmeldung nur für Personal und Erwachsene, nicht für Schüler/innen; Landes-Login bevorzugt; Fremdskripte erst beim Klick laden und in der Datenschutzvorlage nennen; „automatische Anmeldung“ standardmäßig aus bestätigen; Passwort-Felder standardmäßig verdeckt (Auge-Symbol).
- Herkunft: Claude (Empfehlung 10-16); Betreiber offen. Abhängigkeiten: E-37, REH-902.
Abnahme: Ein Schülerkonto sieht keine Google- oder Apple-Anmeldung; die Seite lädt vor dem Klick keine Fremdskripte.

#### ANM-909 · Zentraler Anmeldepunkt und mehrere Schulen je Konto · P3 · Aufwand L · Status: offen
- Eltern mit Kindern an zwei Schulen wechseln die Schule im Konto: ein gemeinsamer Anmeldepunkt für viele Schul-Subdomains (Empfehlung: bei der zweiten Schule); Subdomain je Schule ohne Portnummer (E-40).
- Herkunft: Betreiber („später“, 10-12); Claude. Abhängigkeiten: BET-918, E-40.
Abnahme: Ein Konto wählt zwischen zwei Schulen, ohne sich neu anzumelden; Daten der Schulen bleiben getrennt.

#### ANM-911 · SAML und LDAP/AD für Träger · P3 · Aufwand L · Status: offen
- SAML 2.0 als Dienstanbieter und LDAP/AD-Anbindung für Träger.
- Herkunft: Wettbewerb (Moodle, Untis). Abhängigkeiten: ANM-912.
Abnahme: Ein Testkonto aus dem Verzeichnis meldet sich an und erhält die zugeordnete Rolle.

### 4.13 Datenschutz, Löschkonzept, Verschlüsselung, Protokolle, Beobachtung, Sicherheit, Recht

#### SIC-901 · Default-Deny und eine Prüfung je Objekt auf allen Wegen · P0 · Aufwand L · Status: offen
- Neue Routen, Funktionen, Token-Rechte, Exporte und Demo-Aktionen sind gesperrt, bis sie ausdrücklich freigegeben sind (Allowlist statt Blocklist); Schutz nur im Routen-Handler genügt nicht: Massen- und Einzelaktionen laufen durch dieselbe Prüfung je Objekt; ein Feldregelwerk für Einzelansicht, Liste, Export und Feed; Löschen verlangt dasselbe Recht wie Ändern; Lesen von Regeln, Plan-Prüfung und Paketen nur mit Recht; Dokument annehmen/ablehnen und Förder-Einträge nur mit Fachrecht; Zugriffsprüfung je Objekt bei Formular-Eingang und Export; Rechte werden je Anfrage neu berechnet.
- Herkunft: Claude (Audit 10-17, Pentest live bestätigt, Bestandsprüfung). Abhängigkeiten: keine.
Abnahme: Eine neue Testroute ohne Freigabeeintrag ist für Token und Demo gesperrt; ein Matrix-Test ruft jede Route je Rolle auf und erwartet die tabellierte Antwort (200, 403, 404); eine fremde ID liefert 404.

#### SIC-902 · CSV-Formelschutz in jedem Export · P0 · Aufwand S · Status: offen
- Zellen, die mit `=`, `@`, `+` oder `-` beginnen, werden zentral entschärft; betroffen sind die Exporte Beobachtungsprotokoll, API-Protokoll, Kompetenzen, Stammdaten und OneRoster sowie die Fortschritts-CSV; die Schutzfunktion existiert bereits, wird dort aber nicht genutzt.
- Herkunft: Claude (Audit P2-01). Abhängigkeiten: keine.
Abnahme: Ein Name `=1+1` erscheint in jedem Export als Text und nicht als Formel; ein Test erfasst alle CSV-Ausgaben.

#### SIC-903 · Live-Ströme: Rechte neu prüfen, Verbindungen schließen · P0 · Aufwand M · Status: offen
- Ereignisströme behalten Rechte nach Abmeldung, Sperre und Herabstufung; Rechte werden je Ereignis neu geprüft, Verbindungen werden bei Abmeldung, Sperre, Herabstufung und Passwortwechsel geschlossen.
- Herkunft: Claude (Audit P1-11). Abhängigkeiten: ANM-906.
Abnahme: Nach der Herabstufung eines Kontos liefert dessen offener Strom keine Ereignisse mehr und wird beendet.

#### SIC-904 · Massenzugriffs-Alarm und Protokollpflicht für Exporte · P0 · Aufwand M · Status: offen
- Alarm an die Administration bei vielen fremden IDs hintereinander (404-Serie), massenhaften Listen-/Export-Abrufen und gehäuften Anmeldefehlern; Export, Anmeldefehler, Fremdabrufe und Beobachtungs-Lesezugriffe sind protokollpflichtig.
- Herkunft: Claude (Audit P4). Abhängigkeiten: SIC-901.
Abnahme: 100 Abrufe fremder Schüler-IDs innerhalb einer Minute lösen einen Alarm aus; ein Export erzeugt einen Protokolleintrag mit Konto und Umfang.

#### SIC-905 · Familienzugriff endet mit der Volljährigkeit, überall · P0 · Aufwand M · Status: offen
- Ein zentraler Baustein entscheidet je Kind und Bereich, ob Eltern sehen dürfen (Krankmeldungen, Dokumente, Kursraum, Stundenplan-Route, Klausuren, Nachrichten, Lernaktivitäten, iCal-Feed); Eltern Volljähriger verlieren den Zugriff automatisch, solange das Kind nicht freigibt; der iCal-Plan und eigene Dokumente zählen mit.
- Herkunft: Claude (Audit P1-05, P1-12); Betreiber (A-44). Abhängigkeiten: SCH-910.
Abnahme: Am 18. Geburtstag liefern iCal-Feed, Dokumente und Plan-Route für die Eltern ohne Freigabe 404 oder leer; mit Freigabe nur der freigegebene Bereich.

#### SIC-906 · Notenbuch-Scopes und freie Rechtevergabe · P0 · Aufwand M · Status: offen
- Eltern und Schüler/innen mit dem Recht `gradebook.use` ohne Scope dürfen nicht alle Notenbücher bearbeiten; eine serverseitige Scope-Grenze je Grundtyp, die freie Rechtevergabe nie erweitert; das Notenbuch eines Kursverbands ist nicht über eine sichtbare Klasse lesbar.
- Herkunft: Claude (Audit P1-08, P1-09). Abhängigkeiten: REC-903.
Abnahme: Ein Elternkonto mit `gradebook.use` liest nur das eigene Kind (nach Freigabe) und schreibt nichts; ein Kursverbands-Notenbuch ist nur für den Kurs lesbar.

#### SIC-907 · Import-Grenzen · P0 · Aufwand M · Status: offen
- Untis, CSV, JSON, GIFT und ZIP-Importe haben Größen-, Zeit- und Entpackgrenzen (zwei Importe entpacken ohne Grenze); die XML-Prüfung prüft mehr als den Dateianfang (Verdacht, nicht belegt); Import nur mit Import-Recht.
- Herkunft: Claude (Audit Anhang C). Abhängigkeiten: SIC-901.
Abnahme: Eine 2-GB-ZIP-Bombe wird mit Meldung abgelehnt; ein überlanger Import bricht nach der Zeitgrenze ab.

#### SIC-908 · Netzschutz für Mail, Virenscanner, Lizenzserver · P0 · Aufwand S · Status: offen
- SMTP/IMAP, Virenscanner, Mail-OAuth und Lizenzserver-Aufrufe laufen über die zentrale Zielprüfung (nur Betreiber-Ziele); Fail-open-Schalter (Virenscan optional) nur mit sichtbarer Kennzeichnung „ungeprüft“; Container-Scan im Release-Ablauf.
- Herkunft: Claude (Audit Anhang B/C). Abhängigkeiten: BET-916.
Abnahme: Ein Mail-Ziel im internen Netz wird abgelehnt; ohne Virenscanner erscheint die Kennzeichnung „ungeprüft“.

#### SIC-909 · Pentest wiederholen und erweitern · P0 · Aufwand M · Status: offen
- Nach REC-901, INT-901 bis INT-903 und SIC-901: Re-Test der Welle-0-Punkte auf einer isolierten Wegwerf-Instanz im Produktivmodus; Erweiterung um Überlastung (bewusst begrenzt), weitere Schwachstellensuche („nach anderen Sachen, wo du noch nicht darüber nachgedacht hast“, 10-17 17:25, unterbrochen), Lizenzserver tiefer, dynamische Tests gegen eine Kopie; Cloud-Zweige der Git-Historie auf Schlüssel prüfen; Strix ausführbar machen (E-38).
- Herkunft: Betreiber (10-17 „alles durch probieren“); Claude. Abhängigkeiten: REC-901, INT-901, INT-902, SIC-901.
Abnahme: Der Re-Test ergibt keinen offenen Fund der Stufen hoch oder kritisch; der Bericht nennt jeden Punkt von Welle 0 als bestanden.

#### SIC-910 · Datenminimierung: Adressbuch und Empfängerkreis · P1 · Aufwand M · Status: offen
- Schüler/innen schreiben standardmäßig nur an Lehrkräfte ihrer Kurse, Klassenleitung und Sekretariat, an Mitschüler/innen nur mit Schulschalter; Eltern schreiben an Personal ihrer Kinder; eine schulweite Personensuche mit Klassenangabe für Schüler und Eltern entfällt („K.-o.-Kriterium“); Geburtsdatum nur mit Recht; Entscheidung zum schulweiten Adressbuch; Regeln gelten für Briefe und Chats.
- Herkunft: Claude (Bestandsprüfung 10-10, Audit P1-10). Abhängigkeiten: STA-905.
Abnahme: Ein Schülerkonto findet bei der Suche „Theo“ nur erlaubte Empfänger; ein Elternkonto findet keine fremden Familien.

#### DAT-901 · Auskunft nach Art. 15 vollständig · P0 · Aufwand M · Status: offen
- Die Auskunft als ZIP enthält auch Protokolleinträge zu Schüler/innen; Sitzungs- und Token-Angaben werden auf Zugehörigkeit geprüft; Eltern erhalten nur freigegebene Daten; Dokumente volljähriger Kinder nicht an Eltern.
- Herkunft: Claude (Audit P4, S-07). Abhängigkeiten: DAT-909.
Abnahme: Die Auskunft für eine Schülerin enthält Nachrichten, Noten, Klassenbuch und Protokolleinträge zu ihr; die Eltern-Auskunft eines Volljährigen ohne Freigabe ist leer.

#### DAT-902 · Verbindliche Löschfristen, Registry je Datenart · P0 · Aufwand M · Status: offen
- Keine Einstellung (auch nicht „0“) schaltet die Löschung ab; Voreinstellung bestätigen (E-35): Gesundheitsdaten, Nachrichten, Benachrichtigungen 30 Tage; Abgaben und Formulare 90 Tage; Noten und Lernstand 180 Tage; Klassenbuch-Anwesenheit 1 Jahr; Audit-Log 1 Jahr; API-Protokoll 90 Tage; Beobachtungsprotokoll 180 Tage; Chats 1 Monat (NAC-904); Pakete und Plan-Stände (STP-914); jedes neue Feature meldet seine Daten an.
- Herkunft: Claude (Audit P4, S-01); Betreiber-Bestätigung offen. Abhängigkeiten: DAT-908, E-35.
Abnahme: Der Wert „0“ wird abgelehnt; eine Nachricht, die älter ist als die Frist, ist nach dem Wartungslauf gelöscht; das Löschprotokoll nennt den Lauf ohne Inhalt.

#### DAT-903 · Pseudonymisierung in Protokollen · P0 · Aufwand S · Status: offen
- Der Benutzername bleibt im Protokoll stehen, nachdem das Konto gelöscht wurde; er wird pseudonymisiert; Protokollzeilen `student_absence.*` zeigen der Administration keine Schüler-Kennung und keinen Zeitraum.
- Herkunft: Claude (Audit P4, Prüfbefund KLB-008). Abhängigkeiten: keine.
Abnahme: Nach Löschung eines Kontos zeigt das Protokoll eine Pseudonym-Kennung statt des Namens; die Administration sieht bei Krankmeldungen keine Person.

#### DAT-904 · IP-Speicherung und Zusage in Einklang bringen · P0 · Aufwand S · Status: offen
- Die Datenschutzerklärung verspricht gekürzte IP-Adressen (IPv4 auf /24, IPv6 auf /48); das Protokoll speichert sie 365 Tage vollständig; entweder kürzen oder Frist senken, Erklärung und Verarbeitungsverzeichnis anpassen. Eine falsche Datenschutzinformation kann selbst abgemahnt werden.
- Herkunft: Claude (Audit P4-01). Abhängigkeiten: REH-902.
Abnahme: Das Protokoll enthält nur gekürzte Adressen oder löscht volle Adressen nach der erklärten Frist; Text und Verhalten stimmen überein.

#### DAT-905 · Datenpannen-Prozess nach Art. 33 · P0 · Aufwand M · Status: offen
- Erkennung (Alarme aus SIC-904), Dokumentation, Meldung an die Aufsichtsbehörde innerhalb 72 Stunden, Benachrichtigung Betroffener, Vorlage mit Zuständigen; Befunde zum Datenpannen-Ablauf stehen nur im Audit-Bericht.
- Herkunft: Claude (Audit, Recherche 10-17). Abhängigkeiten: SIC-904, REH-901.
Abnahme: Ein Probealarm erzeugt die Vorlage mit Zeitstempel und Zuständigen; die Schule kann die Meldung nach Vorlage absetzen.

#### DAT-906 · Beobachtete Konten rechtlich klären und begrenzen · P0 · Aufwand M · Status: offen
- Zweck, Rechtsgrundlage, Information der betroffenen Person, Speicherdauer (180 Tage) und Erkennbarkeit sind ungeklärt; Entscheidung E-07: nur Test- und Demo-Konten mit schriftlicher Information, Chat-Inhalte nie erfassen, Zugriffe auf Fachinhalte protokollieren; Audit-Ausnahmen (E-12) dokumentieren.
- Herkunft: Claude (Audit P1-06/07); Betreiber-Entscheidung offen. Abhängigkeiten: REH-901, REH-903, E-07.
Abnahme: Ein beobachtetes Konto erfasst keine Chat-Nachrichten; vor dem Einschalten liegt die Information der betroffenen Person vor; Lesezugriffe der Beobachtungsseite stehen im Protokoll.

#### DAT-907 · Zwei-Personen-Freigabe bei Sofort-Löschung · P1 · Aufwand M · Status: offen
- Sofort-Löschen (Art. 17) mit Vorschau und Freigabe durch eine zweite berechtigte Person.
- Herkunft: Claude (Paket W4-04). Abhängigkeiten: DAT-902.
Abnahme: Eine Sofort-Löschung wird erst nach Freigabe durch eine zweite Person ausgeführt; die Vorschau nennt den Umfang.

#### DAT-908 · Löschfristen nach Landesrecht als Vorlagen · P1 · Aufwand M · Status: offen
- Vorlagen je Land (zuerst NRW nach VO-DV I) für Fristen einschließlich Klassenbuch-Archiv (Backlog: 10 Jahre); Kennzeichnung als Entwurf bis zur Prüfung (REH-904).
- Herkunft: Claude (Backlog B-38). Abhängigkeiten: REH-904.
Abnahme: Die Vorlage NRW lässt sich übernehmen und zeigt je Datenart Frist und Rechtsquelle; eine Vorlage ohne Prüfvermerk trägt „Entwurf“.

#### DAT-909 · Auskunftsfristen nach Art. 12 · P1 · Aufwand S · Status: offen
- Eingang, Frist (1 Monat), Erinnerung und Nachweis der Bearbeitung eines Auskunftsersuchens.
- Herkunft: Claude (Paket W4-04). Abhängigkeiten: DAT-901.
Abnahme: Ein erfasstes Ersuchen zeigt die Restfrist und löst vor Ablauf eine Erinnerung aus.

#### DAT-910 · Verarbeitungsverzeichnis nach Art. 30 · P1 · Aufwand M · Status: offen
- Verzeichnis, das aus der tatsächlichen Konfiguration abgeleitet wird (Datenarten, Fristen, Empfänger, Lizenzserver); Aktualisierung bei Änderungen.
- Herkunft: Claude (Paket W4-04, Audit). Abhängigkeiten: REH-902.
Abnahme: Das Verzeichnis nennt für jede Datenart Zweck, Frist und Empfänger und ändert sich mit der Konfiguration.

#### DAT-911 · Datenregister, Richtlinien und Einwilligungen mit Versionen · P1 · Aufwand M · Status: offen
- Datenregister, Richtlinien und Einwilligungen mit Versionsstand und Zustimmungsbericht; ein Einwilligungsstand je Person statt je Funktion; Datenminimierung als Prüfung je neuem Feld.
- Herkunft: Wettbewerb (Moodle); Claude. Abhängigkeiten: SCH-910.
Abnahme: Der Zustimmungsbericht listet je Person Version und Datum; eine neue Richtlinienversion erfordert erneute Zustimmung.

#### REH-901 · Datenschutzrichtlinien und Pflichtdokumente festlegen · P0 · Aufwand M · Status: offen
- Betreiber: die Richtlinien für Chat und Gesundheitsdaten sind „noch festzulegen“; Pflichtdokumente DSFA, Verarbeitungsverzeichnis, TOM, AV-Vertrag und Datenpannen-Ablauf liegen als Entwurf vor und sind bis zur Prüfung als „Entwurf“ gekennzeichnet; Verantwortung für Impressum und Datenschutz zwischen Anbieter und Schule klären.
- Herkunft: Betreiber (10-11/12); Claude. Abhängigkeiten: E-36.
Abnahme: Alle Pflichtdokumente liegen vor und tragen Stand und Prüfvermerk oder „Entwurf“; die Richtlinien für Chat und Gesundheitsdaten sind beschlossen.

#### REH-902 · Datenschutztexte und Barrierefreiheitserklärung abgleichen · P0 · Aufwand M · Status: offen
- Die Datenschutzvorlage nennt den Lizenzserver als Empfänger, Fremdskripte bei Google- oder Apple-Anmeldung, die Fristen für API-Protokoll (90 Tage) und Beobachtung (180 Tage) und die tatsächliche IP-Speicherung; ein Test prüft Zusagen gegen die Konfiguration; die Erklärung zur Barrierefreiheit (BFSG/BITV) mit Rückmeldeweg fehlt.
- Herkunft: Claude (Audit P4, Checkliste 10-17). Abhängigkeiten: DAT-904, OBE-902.
Abnahme: Ein Test schlägt fehl, wenn eine Zusage des Textes nicht zum Verhalten passt; die Erklärung zur Barrierefreiheit ist ohne Anmeldung erreichbar und nennt den Rückmeldeweg.

#### REH-903 · Audit-Ausnahmen festhalten · P0 · Aufwand S · Status: offen
- Entscheidung E-12: Ohne Protokoll dürfen bleiben: Löschen eigener Benachrichtigungen, Zwischenspeichern von Selbsttest-Antworten, einzelne gesendete Chat-Nachrichten und „gelesen“-Markierungen (sonst entstünde ein Protokoll, wer wann wem schreibt); schriftlich in der Datenschutzdokumentation.
- Herkunft: Claude/Koordinator (10-16); Betreiber-Zustimmung offen. Abhängigkeiten: E-12.
Abnahme: Die Datenschutzdokumentation nennt die Ausnahmen ausdrücklich; sonst protokolliert jede schreibende Aktion.

#### REH-905 · Externe Rechtsprüfung beauftragen · P0 · Aufwand M · Status: offen
- Datenschutz-Folgenabschätzung, Mustertexte, AV-Vertrag und Löschfristen durch Schule/Schulträger oder Datenschutz-Fachperson prüfen lassen; Rechtsaussagen der Recherche (30 Punkte, 25 mit hohem Risiko) sind nicht rechtlich geprüft.
- Herkunft: Claude (Audit 10-17); Betreiber offen. Abhängigkeiten: REH-901, E-36.
Abnahme: Ein Prüfbericht der Fachperson liegt vor; offene Anmerkungen sind als Einträge dieser Liste erfasst.

#### REH-906 · Namens- und Markenrecht klären · P0 · Aufwand S · Status: offen
- Der Arbeitstitel „Schulpuls“ wird im Bildungsbereich bereits genutzt (Verwechslungsgefahr hoch; keine Rechtsberatung); Markenrecherche (DPMA, EUIPO, WIPO) durch einen Anwalt, Domain sichern, Abstand zu „Schulmanager Online“ klären; Namenswahl E-01 (Wunsch: Name mit „Schule“ oder Teilen davon).
- Herkunft: Betreiber (10-16 Namenswahl); Claude. Abhängigkeiten: E-01, OBE-909.
Abnahme: Eine Markenrecherche liegt vor; der Name ist entschieden und im Konstanten-Eintrag für den Produktnamen hinterlegt.

#### REH-904 · Löschfristen nach Landesrecht juristisch prüfen · P1 · Aufwand S · Status: offen
- Fristen gegen VO-DV I NRW und die Landesregeln weiterer Länder prüfen lassen, auch Klassenbuch-Archiv und Gesundheitsdaten.
- Herkunft: Claude (Audit P4). Abhängigkeiten: DAT-908, REH-905.
Abnahme: Ein Prüfvermerk je Frist liegt vor; die Vorlage trägt Rechtsquelle und Prüfdatum.

#### REH-907 · Code-Schutz, EULA, Patent · P1 · Aufwand M · Status: offen
- Betreiber: Schulen sollen den Code nicht entschlüsseln können, „patentiert“; technisch nur Erschwernis; Entscheidung E-28: EULA durch Anwalt, nicht abschaltbare Lizenzprüfung, Kunden-Wasserzeichen, Patentanwalt befragen (Software-Patente in der EU schwierig), gehostetes Angebot als Alternative.
- Herkunft: Betreiber (10-16); Claude. Abhängigkeiten: BET-902, E-28.
Abnahme: Eine anwaltlich geprüfte EULA liegt vor; die ausgelieferte Version trägt ein Kunden-Wasserzeichen.

#### REH-908 · Vertragswerk und Nachweise · P1 · Aufwand M · Status: offen
- Muster-AV-Vertrag, Unterauftragnehmerliste, TOM-Beschreibung, Support-Modell; Hinweis auf Hosting-Zertifizierung (Aufgabe des Betreibers).
- Herkunft: Claude (Backlog B-51). Abhängigkeiten: REH-905.
Abnahme: AV-Vertrag, Unterauftragnehmerliste und TOM liegen als geprüfte Fassung vor.

### 4.14 Benachrichtigungen

#### BEN-901 · Systemabsender für Nachrichten · P1 · Aufwand S · Status: offen
- Die Nachrichten-Ablage hat keinen Systemabsender; er ist Voraussetzung für automatische Nachrichten (Nachschreibtermine, Erinnerungen, Admin-Meldungen); Mails sind als automatisch gekennzeichnet (gebaut).
- Herkunft: Claude (Befund 10-12). Abhängigkeiten: keine.
Abnahme: Eine automatische Erinnerung erscheint in „Nachrichten“ mit Absender „System“; Antworten darauf sind nicht möglich.

#### BEN-902 · Glocke für Chat-/Nachrichten und Kursraum-Freischaltungen · P1 · Aufwand S · Status: offen
- Neue Chat- und Brief-Nachrichten sowie freigeschaltete Kursraum-Elemente erzeugen eine Benachrichtigung (Einstellung je Ereignis); die Liste ungelesener Benachrichtigungen vollständig prüfen; die Quelle für Nachrichten und Freigabe-Zeitpunkte festlegen.
- Herkunft: Betreiber (10-13 „Benachrichtigung bei neuen Nachrichten fehlt“); Claude. Abhängigkeiten: BEN-901.
Abnahme: Eine neue Chat-Nachricht erhöht den Glockenzähler des Empfängers; ohne Einstellung „Nachrichten“ bleibt er stumm; kein Nachrichteninhalt in der Mitteilung.

#### BEN-903 · Nachschreibtermine melden · P1 · Aufwand S · Status: offen
- Nachricht an die Lehrkraft bei Nachschreib-Bedarf und an Eltern und Schüler/innen bei festgelegtem Termin (Datum, Raum, ohne Gesundheitsangaben).
- Herkunft: Betreiber/Claude (10-12); Claude (Paket W4-06). Abhängigkeiten: BEN-901.
Abnahme: Ein festgelegter Nachschreibtermin erzeugt Benachrichtigungen für die betroffenen Kinder und Eltern und den Hinweis an die Lehrkraft; Mitschüler erhalten nichts.

#### BEN-904 · Beurlaubungsantrag melden · P1 · Aufwand S · Status: offen
- Postfach-Nachricht an die Klassenleitung bei neuem Beurlaubungsantrag und Rückmeldung an die Familie nach Entscheidung.
- Herkunft: Betreiber/Claude (10-12). Abhängigkeiten: BEN-901, KLB-907.
Abnahme: Ein neuer Antrag benachrichtigt die Klassenleitung; die Genehmigung benachrichtigt die Familie.

#### BEN-905 · Volljährigkeit melden · P1 · Aufwand S · Status: offen
- Am Tag der Volljährigkeit eine Mitteilung per Nachricht oder Mail (nicht nur In-App-Hinweis) an die Person mit Link zu den Freigabe-Schaltern; Anrede „Sie“.
- Herkunft: Betreiber (10-12); Claude. Abhängigkeiten: BEN-901, SCH-910.
Abnahme: Am 18. Geburtstag erhält die Person die Mitteilung mit „Sie“-Anrede und Link zu den Freigaben.

#### BEN-908 · Neutral-Mail als Schulvorgabe · P1 · Aufwand S · Status: offen
- Schule kann festlegen, dass Benachrichtigungs-Mails keinen Namen im Text tragen und Betreffs neutral sind; Mails enthalten nie Gründe, Noten oder Gesundheitsangaben.
- Herkunft: Claude (Paket W2-13). Abhängigkeiten: STA-903.
Abnahme: Mit Vorgabe „neutral“ enthält die Vertretungsmail keinen Personennamen und keinen Grund.

#### BEN-909 · Mail, SMS und Zwei-Faktor in der Oberfläche einrichten · P1 · Aufwand M · Status: offen
- Mailkonto (Server, Benutzer, Passwort, Absender), SMS-Anbieter (z. B. seven, Twilio oder Webhook; ca. 7–10 Cent je SMS) und 2FA-Pflicht ohne Serverzugang in der Oberfläche einrichten und testen (Passwörter trägt der Betreiber selbst ein); „Passwort vergessen“ erscheint erst bei eingerichtetem Versand; SMS-Anbieter festlegen.
- Herkunft: Betreiber (10-12); Claude (Backlog B-49). Abhängigkeiten: SIC-908.
Abnahme: Ein Administrator richtet Mail ohne Servereingriff ein und sendet eine Testmail; ohne Einrichtung zeigt „Passwort vergessen“ den Hinweis „Bitte wenden Sie sich an das Sekretariat“.

#### BEN-911 · Benachrichtigungen: Fehlerbehebung · P1 · Aufwand S · Status: offen
- Rechte für die Einstellungen; N+1-Abfragen beseitigen; stille Ausnahmen protokollieren; Ereigniszuordnung vollständig.
- Herkunft: Claude (Bewertung 10-16, Paket W2-13). Abhängigkeiten: VER-911.
Abnahme: Die Einstellungsseite verlangt das Recht; ein Fehler beim Zustellen steht im Protokoll.

#### BEN-906 · Ampel-Überschreitung der Fehlzeiten melden · P2 · Aufwand S · Status: offen
- Überschreitet ein Kind die Fehlzeitgrenze je Fach, erhalten Klassenleitung und Sekretariat eine Benachrichtigung (ohne Gründe).
- Herkunft: Claude (Paket W4-06). Abhängigkeiten: BEN-901.
Abnahme: Bei Überschreitung der Grenze erscheint genau eine Meldung für die Klassenleitung.

#### BEN-907 · Push und installierbare App (PWA) · P2 · Aufwand L · Status: offen
- Installierbare PWA mit Web-Push (Opt-in), Offline-Cache für den Plan, QR-Einrichtung, mehrere Schulkonten; Push ohne Namen, Noten und Gesundheitsdaten; Betreiber 10-13: „die app option mus noch nicht mit rein“; Marktvergleiche reihen Push an erste Stelle; Entscheidung E-20 und Klärung von „kein Drittanbieter“ bei Browser-Push-Diensten.
- Herkunft: Betreiber (zurückgestellt 10-13/16); Wettbewerb. Abhängigkeiten: E-20, BEN-902.
Abnahme: Eine installierte PWA erhält „Morgen Entfall 1.–2. Stunde“ ohne geöffnete Seite; Widerruf der Zustimmung beendet den Push.

#### BEN-910 · Benachrichtigungszentrale prüfen · P2 · Aufwand S · Status: offen
- Browser-Prüfung der Benachrichtigungsliste (Zähler, Seite, Live-Aktualisierung) und der Einstellungen je Rolle; Zusammenfassung und Ruhezeit (NAC-906) einbinden.
- Herkunft: Claude. Abhängigkeiten: BEN-902.
Abnahme: Die Prüfliste ist mit Gerät, Rolle und Ergebnis abgehakt.

### 4.15 Integrationen, Import/Export, API-Zugänge

#### INT-901 · Stammdaten-Exporte nur mit Recht und Protokoll · P0 · Aufwand M · Status: offen
- Exporte (JSON, CSV, Untis, SMO, OneRoster, ZIP) verlangen `students.read`; das Geburtsdatum nur mit eigenem Recht; jeder Export wird protokolliert; die Zuschauer-Rolle ist ausgeschlossen (sie hatte Zugriff, Exporte waren nicht protokolliert); ein Vollexport als Klartext-Sicherung nur für `system.admin`.
- Herkunft: Claude (Audit P1-04, Pentest live bestätigt). Abhängigkeiten: SIC-901, SIC-902, E-03.
Abnahme: Die Zuschauer-Rolle ruft den Stammdaten-Export auf → 403; ein erlaubter Export erzeugt einen Protokolleintrag mit Konto und Umfang; ohne Geburtsdatum-Recht fehlt die Spalte.

#### INT-902 · API-Tokens mit Ablauf und Widerruf · P0 · Aufwand M · Status: offen
- Pflichtablauf (Standard 90 Tage), Ende bei Passwortwechsel, Reset, Sperre, 2FA-Reset, Herabstufung und „Sitzungen beenden“; Ausstellung nur für berechtigte Rollen (Schüler-Konten nicht); Token rotieren; Umfang, Ablauf und IP nachträglich ändern; Tokens überleben heute Passwortwechsel und Sperre (live bestätigt).
- Herkunft: Claude (Audit P1-02, P3-02/03, Pentest); Paket W4-07. Abhängigkeiten: ANM-906, E-03.
Abnahme: Nach einem Passwortwechsel liefert ein altes Token 401; ein Schüler-Konto kann kein Token ausstellen; ein abgelaufenes Token wird abgewiesen.

#### INT-903 · Schreibzugang: Allowlist und Reichweite · P0 · Aufwand M · Status: offen
- Schreib-Tokens: nur ausdrücklich freigegebene Routen (Allowlist) statt Sperrliste, auch für Export- und Auskunftswege; Entscheidung zur Reichweite eines Schreibzugangs; auch mit Schreibzugang gesperrt: Passwort, Zwei-Faktor, neue Zugänge, Rechte, Lizenz, Sicherungen (gebaut).
- Herkunft: Claude (Audit P1-03). Abhängigkeiten: SIC-901.
Abnahme: Ein Schreib-Token ruft einen Auskunfts- oder Export-Weg auf → 403; eine ausdrücklich freigegebene Route funktioniert.

#### INT-904 · API-Zugänge und offene API: Fehlerbehebung · P1 · Aufwand M · Status: offen
- Rate-Limit in Datenbank oder gemeinsamem Speicher statt je Prozess; Zugangs-Grenze atomar; Last des Protokolls; Zeitraum-Grenzen der offenen API für Vertretungs- und Kalenderabfragen.
- Herkunft: Claude (Bewertung 10-16, Paket W2-12). Abhängigkeiten: BET-914.
Abnahme: Das Limit gilt über zwei Prozesse gemeinsam; eine Abfrage über mehr als den erlaubten Zeitraum wird begrenzt.

#### INT-905 · Import-Oberfläche mit Zuordnung und Hintergrundlauf · P1 · Aufwand L · Status: offen
- Oberfläche zum Zuordnen von Kursen und Personen und zum Lösen von Konflikten; große Importe laufen im Hintergrund mit Fortschritt; Vorschau, Ausführen, Rückgängig; Protokoll verschlüsselt; Konten optional (FOR-902).
- Herkunft: Betreiber („Nische-Datenbanken“, 10-16); Claude. Abhängigkeiten: SIC-907.
Abnahme: Ein Import mit 3000 Zeilen läuft im Hintergrund; ein Konflikt lässt sich in der Oberfläche lösen; Rückgängig stellt den Stand her.

#### INT-914 · Untis-Rundlauf vollständig · P1 · Aufwand M · Status: offen
- Export und Re-Import verlieren Sperrzeiten, Arbeitszeiten, Pausen und Termine; die acht Feldzuordnungen des Untis-Imports kann nur ein echter Untis-Export bestätigen (der Betreiber muss ihn liefern).
- Herkunft: Claude (Montessori-Test 10-12); Betreiber (Export offen). Abhängigkeiten: keine.
Abnahme: Ein Rundlauf Export → leere Instanz → Import liefert dieselben Sperrzeiten, Arbeitszeiten, Pausen und Termine.

#### INT-906 · Weitere GPU-Dateien · P2 · Aufwand M · Status: offen
- Zuerst 013 (Abwesenheiten), 011 (Zeitraster), 017 (Prüfungen), 016 (Zeitwünsche), danach 007–009, 012, 018–021; „stärkstes Wechselargument“ laut Marktvergleich.
- Herkunft: Wettbewerb (Untis). Abhängigkeiten: INT-914.
Abnahme: Je Datei lässt sich ein Beispiel einlesen und exportieren; der Probelauf zeigt Vorher-Nachher.

#### INT-907 · API-Härtung im Detail · P2 · Aufwand S · Status: offen
- Standortfilter bei der API prüfen; Kalender-Token nicht im URL-Pfad (Header oder Rotation); CSV-Export des API-Protokolls und Lizenz-Schnittstellen im Browser prüfen.
- Herkunft: Claude (Prüfung 10-16/17). Abhängigkeiten: INT-902.
Abnahme: Ein Token mit Standortfilter liefert nur diesen Standort; der Kalender-Abruf funktioniert ohne Token im Pfad.

#### INT-909 · LTI 1.3 Plattform · P2 · Aufwand L · Status: offen
- Lern-Apps und Verlage einbinden (OIDC-Start, Dienste für Noten zurück und Namen/Rollen); pseudonyme Schüler-IDs je Tool; Entscheidung E-23: Quiz/H5P nur per Link oder LTI.
- Herkunft: Claude (Recherche 10-16); Wettbewerb. Abhängigkeiten: SIC-908, E-23.
Abnahme: Ein Test-Tool startet mit pseudonymer Kennung und meldet eine Note zurück; keine Klarnamen.

#### INT-910 · Schulconnex-Anbindung · P2 · Aufwand L · Status: offen
- Dienste-API empfangend (Login-Provisioning mit Rolle, Schulnummer, Gruppen), später Gruppen-Abgleich; Quellsysteme-API liefernd für Moodle und Lern-Apps; Test-Knopf und Ablaufprotokoll; Lösch-Aktion einstellbar (nichts, deaktivieren, löschen).
- Herkunft: Claude (Recherche 10-13/16). Abhängigkeiten: ANM-910, E-21.
Abnahme: Ein Test-Login legt die Person mit Rolle und Gruppen an; der Abgleich-Job protokolliert Änderungen.

#### INT-911 · OneRoster 1.2 und WebUntis-REST · P2 · Aufwand M · Status: offen
- Zuerst CSV-Export, dann REST (orgs, users, classes, courses, enrollments, academicSessions); OneRoster als Standardweg ausbauen.
- Herkunft: Wettbewerb; Claude (Empfehlung 10-16). Abhängigkeiten: INT-901.
Abnahme: Der CSV-Export wird von einem Referenz-Import eingelesen; die REST-Abfrage liefert nur Daten mit Berechtigung.

#### INT-912 · SCIM 2.0 Server · P2 · Aufwand M · Status: offen
- /Users, /Groups, Filter und Patch zum Anlegen und Sperren aus Verzeichnisdiensten.
- Herkunft: Claude (Recherche 10-16). Abhängigkeiten: INT-902.
Abnahme: Ein Verzeichnisdienst legt einen Nutzer an und sperrt ihn; die Sperre beendet dessen Sitzungen.

#### INT-913 · Webhooks überarbeiten · P2 · Aufwand M · Status: offen
- Erklärung mit Zweck und Beispielen, Testknopf, fertige Ziele (Schul-App, Infoscreen, n8n, Zapier); der Betreiber hat die Versteckung unter „Erweitert“ kritisiert.
- Herkunft: Betreiber (10-13); Claude. Abhängigkeiten: SIC-908.
Abnahme: Ein Administrator wählt ein fertiges Ziel, sendet einen Test und sieht das Ergebnis; Aufrufe sind signiert.

#### INT-915 · Moodle-Import über Webservice · P2 · Aufwand M · Status: offen
- Anbindung über die offizielle Schnittstelle (Dateien inklusive) statt Datenbank-Abzug; Kurssicherung an einer echten Sicherung testen; MySQL/PostgreSQL-Moodle testen.
- Herkunft: Claude (10-16). Abhängigkeiten: INT-905.
Abnahme: Ein echtes Moodle-Backup wird mit Kursen, Dateien und Einschreibungen importiert.

#### INT-918 · Landes-Exporte · P2 · Aufwand M · Status: offen
- NRW-Vertretungsabrechnung, ASV, LUSD, SchILD/LUPO; Noten- und Fehlzeiten-Export je Land; Entscheidung E-21 (NRW zuerst).
- Herkunft: Wettbewerb. Abhängigkeiten: NOT-903, E-21.
Abnahme: Der NRW-Export wird von der Zielverwaltung angenommen.

#### INT-908 · Untis-Wechsel-Assistent und Zusatz-Schnittstellen · P3 · Aufwand M · Status: offen
- Geführter Wechsel aus Untis (Import, Prüfbericht, Rundlauf); Untis-kompatible JSON-RPC-Schicht und CalDAV-Lesezugriff nur bei Bedarf.
- Herkunft: Wettbewerb (Untis). Abhängigkeiten: INT-906.
Abnahme: Der Assistent importiert und weist Unterschiede aus.

#### INT-916 · IServ, Schulmanager Online und Nischen-Datenbanken · P3 · Aufwand M · Status: offen
- Betreiber (10-16): „Mir fehlen noch ein paar so Niche Datenbanken“; für IServ und Schulmanager Online fehlen echte, anonymisierte Exporte; weitere Stundenplan-Formate (Indiware, Willi, SPO-Office, DaVinci, Tabulex, svPlan, Turbo-Planer, aSc).
- Herkunft: Betreiber (10-16); Wettbewerb. Abhängigkeiten: INT-905.
Abnahme: Je Format wird ein anonymisierter Beispielexport eingelesen.

#### INT-917 · Direktimporte und Online-Schulanmeldung · P3 · Aufwand M · Status: offen
- LUSD, ASV, SchILD direkt; Vertretungsplan-Import fremder Formate (DSBmobile, Indiware, Untis-HTML) nur als Importweg; Schulanmeldung online (BY) mit öffentlichem Formularlink nur auf Nachfrage.
- Herkunft: Wettbewerb. Abhängigkeiten: INT-905.
Abnahme: Ein Direktimport liest die Zielstruktur; der öffentliche Link gibt keine Daten preis.

### 4.16 Betrieb, Lizenz, Updates, Zahlungen, Anbieter-Portal, Demo

#### BET-901 · Produktivmodus für alle Kundeninstanzen · P0 · Aufwand S · Status: offen
- Hauptserver, Demo und Test-Instanz laufen im Entwicklungsmodus (Demo-Konten ohne Passwortwechsel, Schutz einer Kundenschule greift nicht); Kundeninstanzen laufen nur mit `SM_MODE=production` (Verschlüsselungsschlüssel Pflicht, Docs aus, Demo-Laden gesperrt, Entwicklungs-Passwörter aus); der Start verweigert Entwicklungsschalter im Produktivbetrieb; die Demo-Sperre im Produktivmodus ist nicht geprüft. Entscheidung E-09: Test-Instanz zuerst umstellen; die Hauptinstanz bleibt Demo, die erste echte Schule erhält eine eigene Instanz.
- Herkunft: Claude (Audit P3-05/06/07, Produktreife); Betreiber-Entscheidung offen. Abhängigkeiten: E-09.
Abnahme: Eine Instanz im Produktivmodus startet ohne Verschlüsselungsschlüssel nicht; „Demo laden“ liefert dort 403; kein Konto mit Standardpasswort ist anmeldbar.

#### BET-902 · Lizenzprüfung im Echtbetrieb nicht abschaltbar · P0 · Aufwand S · Status: offen
- Die Prüfung lässt sich heute per Einstellung abschalten; im Echtbetrieb nicht; der öffentliche Prüfschlüssel ist fest im Programm (Status vor dem ersten Kunden prüfen); Live-Test auf der leeren Instanz (Lizenz eingeben, widerrufen, Sperre prüfen, wieder freigeben); Sofortsperre im Anbieter-Portal ausprobieren (innerhalb 15 Minuten gesperrt); die Testschule trägt den neuen Schlüssel einmal ein; Sperrseite „Die Lizenz dieser Schule ist abgelaufen – bitte wenden Sie sich an die Schulleitung“.
- Herkunft: Betreiber (10-16 Abo-Modell); Claude. Abhängigkeiten: BET-901.
Abnahme: Im Produktivmodus gibt es keinen Schalter, der die Prüfung deaktiviert; ein gesperrter Schlüssel sperrt die Schule innerhalb 15 Minuten; die Schnittstellen sind bei Sperre dicht.

#### BET-903 · Demo-Konten und Test-Postausgang absichern · P0 · Aufwand S · Status: offen
- Prüfen, ob Demo-Konten mit bekanntem Passwort auf dem Hauptserver aktiv sind (Ergebnis nicht gemeldet) und sie sperren; Standardwert des Test-Postausgangs im Code härten (nur Administration, nur lokal, Standard aus; live ausgeschaltet); Vorschau-Skript ohne festes Passwort; Demo-Konten nie öffentlich mit bekanntem Passwort.
- Herkunft: Claude (Audit Sofortpunkte, 10-16/17). Abhängigkeiten: BET-901.
Abnahme: Auf einer Produktivinstanz liefert der Test-Postausgang 404; kein Demo-Konto mit Standardpasswort ist anmeldbar.

#### BET-904 · Schlüsselablage und Schlüssel-Hygiene · P0 · Aufwand M · Status: offen
- Datenschlüssel nicht neben der Datenbank ablegen (Lage auf dem Live-System prüfen); ungenutzte Schlüsseldatei im Quellordner entfernen (Bericht uneindeutig); Schlüssel getrennt sichern; Schlüssel-Rotation dokumentieren (innere Tokens am alten Schlüssel); Lizenzserver-Schlüsselspeicher in die Sicherung aufnehmen; Gateway-Schlüssel aus dem Chat vom 10-13 rotieren; Repo-Hygiene (Demo-Logins, .env-Beispiele, Lizenzserver-Krypto vor Produktivbetrieb entfernen oder abschirmen).
- Herkunft: Claude (Audit Betrieb, 10-13/17). Abhängigkeiten: BET-901.
Abnahme: Ein Dateisystem-Abzug der Datenbank enthält keinen Schlüssel; eine Rotation lässt alte Daten lesbar; im Schul-Image liegen keine Entwicklungsskripte und kein Lizenzserver.

#### BET-905 · HTTPS-only, Heimnetz-Adresse · P0 · Aufwand S · Status: offen
- Der Hauptserver erlaubt HTTP im Heimnetz (Cookies ohne Secure-Kennzeichen, `SM_COOKIE_SECURE=0`); Entscheidung E-10: HTTP abschalten oder die Heimnetz-Adresse auf die Domain umleiten (Sitzungen sind an die Adresse gebunden, Konten „verschwinden“ beim Wechsel); Proxy-Adresse als vertrauenswürdig eintragen.
- Herkunft: Claude (10-12/13); Betreiber-Entscheidung offen. Abhängigkeiten: E-10, ANM-903.
Abnahme: Ein HTTP-Aufruf wird auf HTTPS umgeleitet oder abgelehnt; alle Cookies tragen `Secure`.

#### BET-920 · SSH-Erreichbarkeit und Fremdzugänge am Router · P0 · Aufwand S · Status: offen
- Ob Port 22 am Router nach außen offen ist, ist unbekannt; Fehlversuche konnten nicht geprüft werden; SSH nur mit Schlüsselanmeldung, ohne Passwort, mit Sperre nach Fehlversuchen; die Portfreigabe läuft über ein Skript für eine fremde Anwendung (Minecraft) und wird getrennt; der Anbieter erlaubt nur Ports 10476 bis 10495.
- Herkunft: Claude (Server-Prüfung 10-17). Abhängigkeiten: keine.
Abnahme: Von außen ist Port 22 nicht erreichbar oder nur mit Schlüssel; ein Port-Scan zeigt nur die Dienste des Lizenz- und Schulservers.

#### BET-906 · Sicherungen: inkrementell, extern, aufbewahrt · P1 · Aufwand M · Status: offen
- Jede Nacht volle Kopie mit 34 Kopien ist bei verschlüsselten Dateien unbetreibbar groß (1,4 bis 7 TB im ersten Jahr); inkrementelle Sicherung (rund −97 %), externe Kopie, E-Mail-Alarm und externe Sicherung auf der Statusseite, Aufbewahrungsregel; JSON-Backup bei PostgreSQL verschlüsselt (bei SQLite gebaut).
- Herkunft: Claude (Speicherkalkulation 10-12/16). Abhängigkeiten: BET-908.
Abnahme: Die Sicherung der zweiten Nacht ist höchstens 5 % der ersten; eine externe Kopie existiert und ist verschlüsselt.

#### BET-907 · Update-Dienst auf dem Schulserver · P1 · Aufwand L · Status: offen
- Der Update-Dienst (Signaturprüfung, Vorladen, Termin, Sicherung, Update, Gesundheitsprüfung, Rollback) ist nicht auf dem Schulserver eingespielt; der echte Container-Austausch wurde nie getestet; Entscheidung E-25: Host-Job ohne Container-Rechte statt Docker-Zugriff (praktisch Root), Download vom Lizenzserver, eigene Registry erst ab rund 10 Schulen; Schule kann ein Update einmal um 1 bis 7 Tage verschieben, außer dringend.
- Herkunft: Betreiber (10-16 „automatisch das Update machen“); Claude. Abhängigkeiten: BET-908, E-25.
Abnahme: Ein Update 1.1.0 läuft durch; ein absichtlich scheiterndes 1.2.0 wird zurückgerollt; der Dienst läuft ohne Container-Rechte.

#### BET-908 · Wiederherstellung einmal echt nachweisen · P1 · Aufwand S · Status: offen
- Vollständige Dateiprüfung mit einer echten Sicherung (bisher 5 Dateien); Betreiber-Vorgabe „einmal echt“; Ergebnis mit Datum in der Betriebsdoku, danach vierteljährlich.
- Herkunft: Betreiber (10-16/17); Claude (O-5). Abhängigkeiten: BET-906.
Abnahme: Die Sicherung wird in einem Testcontainer wiederhergestellt; alle Konten, der Plan und alle Dateien (Atteste, Kursraum-Dateien) sind lesbar; das Protokoll trägt Datum.

#### BET-909 · Datenbank-Rollen mit minimalen Rechten · P1 · Aufwand M · Status: offen
- Migrationen laufen mit einer Besitzer-Rolle nur im Update-Schritt, die Laufzeit mit reinen Daten-Rechten (`SM_MIGRATE_DATABASE_URL`); das Audit-Log ist nur anhängbar; bisher nur Doku, Aufwand rund 1 Tag; der Heimserver nutzt SQLite.
- Herkunft: Claude (Audit O-3). Abhängigkeiten: BET-907.
Abnahme: Das Laufzeit-Konto kann keine Tabellen ändern; ein Migrationslauf gelingt mit der Besitzer-Rolle.

#### BET-910 · Statusseite und Verfügbarkeit · P2 · Aufwand M · Status: offen
- Öffentliche oder interne Statusseite mit Verfügbarkeit, Selbsthilfe, E-Mail-Alarm bei Ausfall, Sicherheitsbericht; Lastspitzen 7:45 Uhr und Zeugnistag.
- Herkunft: Wettbewerb; Claude (Backlog B-58). Abhängigkeiten: BET-914.
Abnahme: Bei gestopptem Dienst wechselt die Seite binnen 5 Minuten auf „gestört“ und löst den Alarm aus.

#### BET-911 · Zahlungen aktivieren · P2 · Aufwand M · Status: offen
- Stripe (Karte) und GoCardless (SEPA) sind vorbereitet, aber nicht aktiv (Konten und Schlüssel legt der Betreiber an); automatische Pause bei Zahlungsverzug ist aus (Standard aus, Frist vom Betreiber); Entscheidung E-27 (zunächst Rechnung und Überweisung); die Reel-Checkliste hält Stripe-Abo-Punkte für nicht zutreffend, die Anbindung nutzt es aber.
- Herkunft: Betreiber (10-16); Claude. Abhängigkeiten: E-27.
Abnahme: Eine Testzahlung verlängert die Lizenz ab dem bisherigen Ablaufdatum; bei ausgeschalteter Pause wird nichts gesperrt.

#### BET-912 · Lizenzserver-Hosting · P2 · Aufwand M · Status: offen
- Heimserver (Ausfallpuffer 7 Tage normal, danach 14 Tage nur lesen) oder externer Hoster ab dem ersten zahlenden Kunden (E-26); Lizenzserver tiefer prüfen; Minecraft-Ressourcen und Angriffsfläche getrennt (Container gestoppt).
- Herkunft: Betreiber (10-16 offen); Claude. Abhängigkeiten: E-26.
Abnahme: Der Lizenzserver läuft beim externen Hoster; ein Ausfall von 3 Tagen sperrt keine Schule.

#### BET-914 · Skalierung und Lasttest · P2 · Aufwand L · Status: offen
- Echter Lauf des Lasttest-Werkzeugs (im Neubau zu erstellen) gegen eine Testinstanz (nicht die Entwicklungsdatenbank); Ziel Stoßzeit 7:30–8:00 mit 2500 Schüler/innen und 300 Lehrkräften, 95 % der Anfragen unter 500 ms; PostgreSQL für hohe Last; Speicher-Optimierungen (Bilder verkleinern, Caching, gestaffeltes Nachladen); Lastspitze 40 / 100 / 190 Anfragen je Sekunde für kleine / mittlere / große Schule.
- Herkunft: Betreiber (10-12 Tausende gleichzeitige Nutzer); Claude. Abhängigkeiten: QUA-905.
Abnahme: Der Lasttest läuft mit 2500 Konten; das 95. Perzentil liegt unter 500 ms; die Fehlerquote ist 0.

#### BET-915 · Demo-Zugänge und Simulation · P2 · Aufwand M · Status: offen
- Entscheidung E-29: Demo-Zugänge gibt nur der Inhaber aus (Betreiber 10-12: „dass die Schule Demo-Accounts rausgeben können oder der, also ich, der Software-Inhaber“); Rollen-Knöpfe ohne Passwort nur auf der Demo-Instanz, nie im Produktivmodus; Demo-Hosting durch Schulen später; Simulation aller Vorgänge je Kontoart (Klassenwechsel, Schüler gehen oder kommen, neue Klasse, Newsletter, Schülerchats) per Knopf.
- Herkunft: Betreiber (10-11/12); Claude. Abhängigkeiten: E-29.
Abnahme: Im Produktivmodus fehlen Demo-Knöpfe und Demo-Ausgabe; die Simulation „Schüler wechselt Klasse“ ändert nur Demo-Daten.

#### BET-916 · Release-Prozess und Lieferkette · P2 · Aufwand S · Status: offen
- Container-Scan im Release-Ablauf; drei direkt genutzte Python-Pakete (pydantic, starlette, anyio) in die Paketliste aufnehmen; Abhängigkeits-Updates (TypeScript, Vite, Vitest, Node) nur mit Tests und getrennt; Build nur mit Lock-Dateien; Zeilenenden der Skripte; zweiter vollständiger Gesamttest nach Klärung des Hängers.
- Herkunft: Claude (Code-Durchsicht 10-17). Abhängigkeiten: QUA-902.
Abnahme: Der Release bricht bei bekannter Schwachstelle ab; die Paketliste enthält alle direkt genutzten Pakete.

#### BET-919 · Preismodell und Module · P2 · Aufwand S · Status: offen
- Entscheidung E-24: Module technisch vorsehen (STA-901), Preis zunächst ein Paket je Schule; Quellen widersprechen sich (Wettbewerber 89 bis 239 Euro je Schuljahr und Modul, bis 30 % Rabatt).
- Herkunft: Claude; Betreiber offen (13.10. Preis- und Lizenzmodell nicht festgelegt). Abhängigkeiten: STA-901, E-24.
Abnahme: Die Entscheidung liegt vor; Tarife im Portal bilden sie ab.

#### BET-913 · Mehrere Server je Schule, Hochverfügbarkeit · P3 · Aufwand XL · Status: offen
- Modell gebaut, Hochverfügbarkeit nur Konzept (PostgreSQL, gemeinsame Dateiablage, Verteiler, Live-Anzeige über mehrere Server); erst anbieten, wenn einmal echt durchgespielt (E-26); nach einem Update wird jede Anmeldung einmal neu verteilt.
- Herkunft: Claude. Abhängigkeiten: BET-914, STP-903.
Abnahme: Ein Rolling-Update mit zwei Servern hält die Schule durchgehend online.

#### BET-917 · Heimserver-Reste aufräumen · P3 · Aufwand S · Status: offen
- Entscheidung E-39: ungenutzte Schlüsseldatei, vier verwaiste Docker-Volumes, Test-Image, rund 1,5 GB Build-Cache entfernen; Minecraft-Live-Verzeichnis (17,7 GB) löschen oder behalten; Sammel-Skript (jede Minute) nach der Beta-Auswertung beenden; Graph-Server beenden.
- Herkunft: Betreiber-Frage (10-17); Claude. Abhängigkeiten: E-39.
Abnahme: Die Reste sind entfernt oder bewusst behalten; das Sammel-Skript läuft nicht mehr.

#### BET-918 · Hosting großer Schulen und eigene Domain · P3 · Aufwand M · Status: offen
- Der Heimanschluss ist für rund 5.000 Schüler zu klein (Lastspitze rund 190 Anfragen/s, Upload mindestens 50 Mbit/s); Hoster-Angebot ab mittlerer Schulgröße; eigene Domain ohne Portnummer (Tunnel-Dienst), Subdomain je Schule (E-40).
- Herkunft: Claude (Empfehlung 10-12); Betreiber (Domain 10-11). Abhängigkeiten: ANM-909, E-40.
Abnahme: Eine Testschule mit 5000 Konten läuft beim Hoster; die Adresse enthält keine Portnummer.

### 4.17 Oberfläche, Design, Barrierefreiheit, Texte

#### OBE-901 · Kopfleiste: Live-Anzeige, Glocke, Hell/Dunkel · P1 · Aufwand S · Status: offen
- Betreiber (10-16 22:12, Satz abgebrochen): „Du kannst manche Dinge anklicken, zum Beispiel das Live-Ding oder die Glocke oder … Also ob es jetzt hell oder dunkles Layout sein soll“; der Fehler ist unbeschrieben, Claude fragte zweimal (10-16 22:15, 10-17 11:32) ohne Antwort. Zuerst Rückfrage an den Betreiber (was stimmt beim Anklicken nicht?), dann Behebung; Live-Anzeige, Glocke und Umschalter sind mit Maus, Touch und Tastatur bedienbar und zeigen eine Wirkung.
- Herkunft: Betreiber (10-16); Claude. Abhängigkeiten: BEN-902.
Abnahme: Die Antwort des Betreibers liegt vor; Live-Anzeige, Glocke und Hell/Dunkel-Umschalter sind per Maus, Touch und Tab bedienbar; der Umschalter wechselt das Design sofort.

#### OBE-902 · Barrierefreiheit prüfen und Barrieren beheben · P1 · Aufwand L · Status: offen
- Prüfung nach WCAG 2.2 AA/BITV: automatische Prüfung (axe-core über Playwright) für 20 Seiten je Rolle, Tastatur- und Screenreader-Prüfung, Kontrasttest, 200 % Zoom, 390 px; Barrieren beheben (Raster STP-901, Monitor-Menü VER-910, Hilfe-Symbole, PDF-Tags); Seite zur Barrierefreiheit mit Rückmeldeweg (REH-902). Schulen sind öffentliche Stellen.
- Herkunft: Claude (Backlog B-44, Audit); Wettbewerb. Abhängigkeiten: STP-901, VER-910.
Abnahme: Der automatische Lauf meldet keinen schweren Verstoß auf den 20 Seiten; ein Tastaturdurchlauf erreicht jede Funktion; bei 200 % Zoom entsteht kein waagerechter Bildlauf.

#### OBE-909 · Produktname konsistent und nur an einer Stelle · P1 · Aufwand M · Status: offen
- „Schulpuls“ steht noch fest im Seitentitel (index.html) und in der Wortmarke als Bild; drei Logo-Dateien liegen ungenutzt; Logo-Geometrie aus einer Quelle; Produktkennung in Kalender und User-Agent; Aufräumen bzw. bei echter Umbenennung mitziehen; bewusst alte technische Namen (Updater-Image, Manifest-Kennung, Lastverteilungs-Cookie, Pfade) brauchen einen Migrationsplan; Betreiber nannte „Schulplus“ (kommt im Code nicht vor); endgültiger Name offen (E-01).
- Herkunft: Betreiber (Produktname nur an einer Stelle); Claude (Code-Durchsicht 10-17). Abhängigkeiten: REH-906, E-01.
Abnahme: Ein Test findet den Produktnamen im sichtbaren Teil nur über die zentrale Konstante; Seitentitel und Wortmarke folgen einer Änderung der Konstante.

#### OBE-903 · Schnellsuche und Tastenkürzel · P2 · Aufwand M · Status: offen
- Schnellsuche (Strg+K) für Personen, Klassen, Kursräume, Seiten; Ergebnisse nach Rechten und Datenumfang gefiltert; Tastenkürzel (`?` für Hilfe, Navigation) nur zusammen mit der Suche; auf dem Handy keine Maus- oder Tastaturbegriffe.
- Herkunft: Wettbewerb (Kleinfunktion 10-16). Abhängigkeiten: E-02, SIC-901.
Abnahme: Strg+K öffnet die Suche; ein Schüler-Konto findet keine fremden Personen; `?` zeigt die Kürzel.

#### OBE-904 · Feedback-Knopf · P2 · Aufwand S · Status: offen
- „Fehler oder Idee melden“ in der Kopfleiste, übermittelt nur, was die Person abschickt (Seite und Version); nutzt die Kontaktfunktion; Demo-Wunschbox bleibt getrennt.
- Herkunft: Wettbewerb (Kleinfunktion 10-16). Abhängigkeiten: E-02.
Abnahme: Ein Absenden erzeugt einen Eintrag mit Seite und Version ohne weitere Daten.

#### OBE-905 · Textdurchgang: Erklärtexte, Sie-Form, Hilfen · P2 · Aufwand M · Status: offen
- Erklärtexte der Planungsseiten (Generator, Zeitraster, Regeln, Kurse, Einstellungen) kürzen; `title=` durch Hilfe-Symbol ersetzen; lange Hilfetexte kürzen; Hilfeseiten und Zugangsbriefe Seite für Seite in Sie-Form gegenlesen; Mehrzahl „1 Einträge“; Inline-Hilfe vollständig; Begriff „Postfach“ durch „Nachrichten“ ersetzen; Erklärungen nur über (i).
- Herkunft: Betreiber („Text-Müll raus“, Sie-Form 10-16); Claude (Paket W3-02). Abhängigkeiten: NAC-911.
Abnahme: Ein Test findet keinen neuen Erklärabsatz und kein „du“ in App-Texten; „1 Eintrag“ erscheint korrekt.

#### OBE-906 · Verständliche Fehlermeldungen · P2 · Aufwand S · Status: offen
- Validierungsfehler auf Deutsch mit Beschriftung des Feldes statt technischer Pfade; unerwartete Fehler zeigen „Das hat nicht geklappt“ mit Fehlernummer; nie englische Servertexte; Zeitüberschreitung „Der Server antwortet nicht rechtzeitig“ (30 s, gebaut).
- Herkunft: Betreiber (A-59); Claude (Backlog B-13). Abhängigkeiten: keine.
Abnahme: `POST /absences` ohne Datum zeigt „Bitte ein Startdatum angeben.“; ein 500 zeigt eine Fehlernummer.

#### OBE-907 · Design-Rest und vollständige Oberflächenprüfung · P2 · Aufwand L · Status: offen
- Rund 400 Stellen mit eigenen Abständen (vor allem Planung) auf zentrale Werte; 28 Inline-Styles in den Einstellungs-Panels; Startseiten-Kacheln gleich hoch; Prüfung aller Rollen auf Handy, Tablet, Breitbild, hell/dunkel, Monitor, Druck; Rechteseite mit einklappbaren Gruppen.
- Herkunft: Claude (Bewertung 10-16/13). Abhängigkeiten: QUA-901.
Abnahme: Ein Design-Test findet keine Inline-Abstände; ein Rundgang je Rolle zeigt gleich hohe Kacheln und keinen Seitenüberlauf bei 390 px.

#### OBE-908 · Design-Richtung festlegen · P2 · Aufwand M · Status: offen
- Entscheidung E-33: Der Betreiber nennt Referenzprodukte (Vorschläge: Linear, WebUntis-App, Notion) und die Seite mit dem meisten „Text-Müll“; das Mockup „Schulmanager Rehaul“ wurde abgelehnt („Jo das ist komplett grauenhaft“, 10-13 17:25); Lehre: erst Referenzen, keine Spielzeug-Mockups; Phase 2 des Stylesheet-Umbaus (rund 310 Dateien) nur bei Nutzen.
- Herkunft: Betreiber (10-13); Claude. Abhängigkeiten: E-33.
Abnahme: Die Referenzen und die Problemseite sind benannt; der Entwurf wird an der echten Oberfläche gezeigt.

### 4.18 Arbeitsweise, Vorlieben und Entscheidungen des Betreibers, Qualität

#### QUA-901 · Browser-Abnahme der nur per Test geprüften Funktionen · P1 · Aufwand L · Status: offen
- Im Browser (PC 1280 px und Handy 390 px, hell und dunkel, Tastatur) und als Eltern, Eltern mit mehreren Kindern und Volljährige prüfen: Notenbuch-Eingabe am Handy; Lernstand, Abzeichen, Lernplan, Elternansicht; Attest-Freigabe; Krankmeldung mit Dateien; Verlängern; Beurlaubung zurückgeben; Nachschreiben; Kursraum-Gruppen; Klausur-Link bei mehreren Kindern; gekoppelte Kurse; Regelplan-Editor mit Ziehen; Stundenplan hell; Impressum-/Datenschutz-Links; Fehleranzeige der Einrichtungstabelle; CSV-Export des API-Protokolls; Zeitleiste der beobachteten Konten; Monitor-Menü auf den Servern; Demo-Wunschbox.
- Herkunft: Claude (Prüfbefund 10-17); Betreiber („nicht lesen, sondern prüfen“). Abhängigkeiten: keine.
Abnahme: Eine Abnahmeliste enthält jeden Punkt mit Datum, Gerät, Rolle und Ergebnis; kein Punkt führt bei 390 px zu waagerechtem Bildlauf.

#### QUA-902 · Backend-Gesamttest auf dem Heimserver · P1 · Aufwand M · Status: offen
- Ein zweiter vollständiger Gesamtlauf nach den Fehlerbehebungen; Ursache des hängenden Gesamttests klären (Verdacht Lizenz-Prüfthread; Loopback unter Windows nicht belegt); vier rote Tests (Beurlaubung an den Herbstferien u. a.); Gesamttest nur einmal vor dem Aufspielen, nie auf dem PC.
- Herkunft: Betreiber (Regel „weniger Checks“, 10-12/16); Claude. Abhängigkeiten: keine.
Abnahme: Der Gesamtlauf auf dem Heimserver endet ohne Hänger und ohne roten Test und dauert höchstens 20 Minuten.

#### QUA-903 · Rundgang je Rolle und Rechte-Matrix · P1 · Aufwand M · Status: offen
- Rundgang aller Rollen (Administration bis Zuschauer, Monitor, Eltern mit mehreren Kindern, Volljährige) bei 390 und 1280 px; die Liste der 274 Lese-Adressen des Zuschauer-Rundgangs dokumentieren; Matrix-Test Rolle × Route mit Erwartung 200, 403 oder 404.
- Herkunft: Claude (Backlog Rundgang E1); Betreiber (Prüfpflicht Zugriff 10-13). Abhängigkeiten: SIC-901.
Abnahme: Die Matrix liegt vor; jede Abweichung ist ein Fehler; fremde Daten liefern 404.

#### QUA-904 · Echte Geräte und Screenreader · P1 · Aufwand M · Status: offen
- Nachrichten auf einem echten Handy; Koppeln zweier getrennter echter Browser im Chat; Prüfung mit Screenreader (NVDA, VoiceOver) für Anmeldung, Plan, Klassenbuch, Nachrichten.
- Herkunft: Claude (Prüfbefund 10-13/17). Abhängigkeiten: OBE-902.
Abnahme: Ein zweiter echter Browser liest den Chat nach Kopplung; ein Screenreader-Durchlauf der Kernseiten ist ohne Blocker.

#### QUA-905 · Lasttest echt ausführen · P1 · Aufwand M · Status: offen
- Echter Lauf des Lasttest-Werkzeugs (im Neubau zu erstellen) gegen eine Testinstanz mit Demo-Daten (nicht gegen die Entwicklungsdatenbank, nie gegen fremde Systeme); Ziele STA-089: 2500 Schüler/innen und 300 Lehrkräfte, 95 % unter 500 ms, Fehlerquote 0; Nachrichtenversand unter 1 s.
- Herkunft: Claude (Audit O-10); Betreiber (Skalierung 10-12). Abhängigkeiten: BET-914.
Abnahme: Der Lauf endet mit 95. Perzentil unter 500 ms und 0 Fehlern und liefert Antwortzeiten je Aufruf.

#### QUA-906 · Testlücken schließen · P1 · Aufwand L · Status: offen
- Neue Tests für Branding, Klassenbuch-Routen, Lernen-Routen, Datenschutz-Seite, Rechte-Matrix, 404-Pfade, Protokoll der Schreibrouten; zu jedem Fix ein Regressionstest, der den Fund nachstellt; Haiku-Befunde vor dem Bau am Code nachprüfen (76 Funde: 42 bestätigt, 11 falsch, 23 unklar).
- Herkunft: Claude (Bewertung 10-16, Paket W3-05). Abhängigkeiten: SIC-901.
Abnahme: Jede schreibende Route hat einen Protokolltest; die Testanzahl wird im Atlas nachgezogen.

#### QUA-907 · Leistung der Listen und Stabilität der Oberfläche · P1 · Aufwand M · Status: offen
- Monitor-Uhr in eigene Komponente; Listen paginieren; Formular-Summe in SQL; Vertretungs-Statistik; Anlegen von Zeilen nicht beim Lesen; Tests für den Anfrage-Client; Fokusfalle im Dialog; Schlüssel im Bestätigungsfenster.
- Herkunft: Claude (Paket W3-03, W3-08). Abhängigkeiten: BET-914.
Abnahme: Eine Liste mit 5000 Einträgen lädt seitenweise unter 500 ms; der Dialog fängt den Tastaturfokus.

#### QUA-908 · Aufräumen, Doku- und Atlas-Abgleich · P2 · Aufwand S · Status: offen
- Toten Code entfernen; Zeilen über 120 Zeichen; große Dateien aufteilen (z. B. Kursraum-Modul mit rund 3.400 Zeilen); veraltete Doku abgleichen (Rollen- und Rechtezahlen, Entwurf Kalender/Zeitraster); Testrouten in der Demo-Tabelle; fehlende Rechte nachtragen.
- Herkunft: Claude (Pakete W3-06, W3-07). Abhängigkeiten: QUA-906.
Abnahme: Ein Abgleichstest meldet keine Doku-Zahl, die vom Code abweicht.

#### QUA-909 · Betatest auswerten · P2 · Aufwand S · Status: offen
- Auswertung der Rückmeldungen des Beta-Testers (Wunschbox, Chat-Kanal) sobald der Betreiber die Nachricht einfügt oder das Lesen bestätigt; danach Konto „betatester“ löschen; Sammel-Skript beenden.
- Herkunft: Betreiber (10-17); Claude. Abhängigkeiten: ANM-915, BET-917.
Abnahme: Die Rückmeldungen sind als Einträge dieser Liste erfasst; das Konto ist gelöscht.

#### QUA-910 · Abnahmeliste für den Betreiber · P2 · Aufwand S · Status: offen
- Vom Betreiber selbst durchzuspielen: Testtag auf dem Hauptserver und danach mit einem Befehl entfernen; Mandantentrennung selbst testen; Sofortsperre im Portal; Durchlauf „Schule von Null“; Demo-Wartung (Klassenarbeit in den Herbstferien, Mittwoch-Leerstunde einer Demo-Lehrkraft: Absicht oder Test?).
- Herkunft: Betreiber (10-12/13/16). Abhängigkeiten: STA-910, BET-902.
Abnahme: Jeder Punkt trägt Datum und Ergebnis des Betreibers.

#### QUA-911 · Betreiber-Rückfragen beantworten · P2 · Aufwand S · Status: offen
- Unbeantwortete Fragen: Commit und Push der Änderungen, Branches (Spaßseite, Login-Knopf) löschen oder behalten, Merge-Stand auf die Server, unklare Diktatwörter („Anbildung“, „NLW“, „im“, „Mugs“), Klärung der Marktliste (digitales Klassenbuch fälschlich als Lücke).
- Herkunft: Claude (Rückfragen 10-11 bis 10-17). Abhängigkeiten: keine.
Abnahme: Zu jeder Frage liegt eine Antwort des Betreibers vor.

#### PRI-901 · Skills und Werkzeuge auswählen · P3 · Aufwand S · Status: offen
- Entscheidung E-38: Auswahl der Skills, die in jedem Workflow aktiv sein sollen (Empfehlung frontend-design, owasp-security, sentry-security-review, gdpr-dsgvo-expert); i-have-adhd nur auf Wunsch („nicht weniger Code, sondern einfach nur weniger Kontext“); Strix erst mit festem Einsatzzweck ausführbar machen (Docker und CLI oder Schlüssel).
- Herkunft: Betreiber (10-13); Claude. Abhängigkeiten: E-38.
Abnahme: Die Auswahl ist festgehalten; Strix läuft einmal gegen die Demo-Instanz.

#### PRI-902 · Arbeitsregeln des Betreibers festhalten · P3 · Aufwand S · Status: offen
- Verbindlich: Eingriffe in Konten und Sicherheitsaktionen nur nach Freigabe; Zugangsdaten nur in der Desktop-Datei, nie im Chat; weniger Prüfungen (nur geänderte Bereiche, Gesamttest einmal vor dem Aufspielen); Fortschritt kurz melden; Modelle: Sonnet für komplexe, Haiku für einfache Aufgaben, Fable nur auf ausdrückliche Bitte („fabel ist viel zu teuer“, 10-16 22:22); keine Server auf dem PC; Wortlaut des Betreibers geht Zusammenfassungen vor; vor der Umsetzung von Sicherheits-Fixes eine Auswahl einholen.
- Herkunft: Betreiber (10-12 bis 10-17). Abhängigkeiten: keine.
Abnahme: Die Regeln stehen in der Arbeitsanleitung des Projekts; kein Agent wird ohne ausdrückliche Bitte auf dem teuersten Modell gestartet.

#### PRI-903 · Gratis-LLM-Gateway und Plugins · P3 · Aufwand S · Status: offen
- Weitere Anbieter-Schlüssel legt der Betreiber selbst an (Reihenfolge Gemini, NVIDIA; optional Cloudflare, OpenRouter, Mistral, Cohere); Gateway als Anbieter einhängen (Stand unklar); Plugin-Installationen (insecure-defaults, CloudMEM) führt der Betreiber selbst aus; Gratis-Anbieter erhalten keinen Quellcode und keine Schlüssel; Cloud-Container-Setup zurückgestellt („Nee“).
- Herkunft: Betreiber (10-13). Abhängigkeiten: E-38.
Abnahme: Ein Aufruf über das Gateway liefert eine Antwort; an Gratis-Anbieter gehen nur freigegebene Dateien.

#### PRI-904 · Entwicklungsumgebung aufräumen · P3 · Aufwand S · Status: offen
- Klon-Server (lokal, Port 5180) und Graph-Server beenden; Obsidian-Dauerbetrieb als Windows-Aufgabe (Betreiber richtet ein); Branches entscheiden; Commit-Vorgabe: vor dem Commit prüfen, dass keine Daten, `.env`, `.venv` oder Build-Ordner enthalten sind; Cloud-Zweige auf Schlüssel prüfen; E-39.
- Herkunft: Betreiber-Fragen (10-13/17). Abhängigkeiten: E-39.
Abnahme: Die Hilfsserver laufen nicht mehr; ein Commit-Check findet keine Schlüssel.

### 4.19 Sonstiges

#### REH-909 · Vertriebsrecht und Anschreiben · P1 · Aufwand S · Status: offen
- Werbung nur mit Einwilligung oder persönlicher Einzelanfrage (§ 7 UWG, Abmahnrisiko, rechtlich ungeprüft); nur Institutionskontakte (Sekretariat, offizielle Adresse), keine Privatdaten von Lehrkräften; Anschreiben im Schreibstil des Betreibers (Entwurf bisher von Claude, nichts verschickt); Vertriebsweg und Freigabe (E-34): persönliche Einzelanfrage und Schulträger, Medienberatung NRW als Ansprechpartner; Käufer sind meist Schulträger (ungeprüft).
- Herkunft: Claude (10-13); Betreiber-Freigabe offen. Abhängigkeiten: E-34, REH-906.
Abnahme: Kein Anschreiben geht ohne Freigabe des Betreibers und ohne Rechtsprüfung hinaus; die Empfängerliste enthält nur Institutionskontakte.

#### QUA-912 · Marktreife-Checkliste und Pilotschule · P1 · Aufwand M · Status: offen
- Zielbild des Betreibers (10-13 20:01): „es ist kein amateurn Programm, das soll schon am Ende ein voll ausgewachsener Schulmanager sein“. Marktreife-Checkliste mit rund 50 Punkten in sechs Bereichen (Funktionen, Datenschutz, IT-Sicherheit, Barrierefreiheit, Firma und Verträge, Betrieb und Support), Status und Zeitpunkt je Punkt; Priorisierung nicht entschieden; Pilotschule mit eigener Instanz, Support-Modell, Hosting-Angebot; Ziel des Businessplans („um sich wo zu bewerben“ – wo?) klären; Web-Scan zur Kundengewinnung NRW nachholen (rund 20 % Fehlerquote durch Limits), Lead-Liste fehlt.
- Herkunft: Betreiber (10-13); Claude. Abhängigkeiten: E-34, BET-901.
Abnahme: Jeder Checklisten-Punkt trägt Status und Termin; die Pilotschule läuft im Produktivmodus mit eigener Instanz.

### 4.20 Wellen-Zuordnung der in Abschnitt 1 nicht einzeln genannten Einträge

Abschnitt 1 nennt nicht jede Kennung. Die übrigen Einträge sind so zugeordnet (Stufe = Priorität des Eintrags):

| Welle | Kennungen | Anmerkung |
|---|---|---|
| 0 (P0) | STP-914, VER-909, VER-911 | Ergänzung als Block 0.6 „Fachbereichs-Härtung“, gleiche Abnahme wie Welle 0 |
| 1 (P1) | LEH-904, NAC-904, NOT-901, STA-903, STA-904, STA-905, STA-909, STP-903, STP-904, STP-905, STP-907, STP-915, VER-912 | Kern-Alltag und Datenintegrität |
| 1, begleitend | BET-916, PRI-902, QUA-908, QUA-909, QUA-910, QUA-911 | Prozess, Aufräumen, Aufgaben des Betreibers |
| 2 (P2) | ANM-908, BEN-906, BEN-910, FOR-902, FOR-903, KLB-902, KUR-902, KUR-903, KUR-904, KUR-905, LEH-902, LEH-903, NAC-909, NAC-911, NAC-912, NAC-916, OBE-905, OBE-906, OBE-907, OBE-908, REC-905, REC-907, REC-908, REC-909, STA-902, STA-906, STA-908, STP-909, STP-910, STP-911, STP-912, STP-913, STP-916, STP-919, VER-902 | Freigabe E-02; STA-908 zuerst (Datenmodell, E-30) |
| 3 (P2) | ANM-907, ANM-912, ANM-913, BET-915, INT-907, INT-913, NAC-914, STA-910, STP-906 | Anbindungen, Einrichtung, Betrieb |
| 4 (P3) | ANM-909, ANM-911, BET-918, INT-908, KUR-906, LEH-901, NAC-910, NAC-915, SCH-906, SCH-907, SCH-912, STP-917, STP-925 | nur auf Nachfrage oder nach Entscheidung E-31 |
| jederzeit | BET-917, PRI-901, PRI-903, PRI-904 | Aufräumen und Arbeitsweise, nach Entscheidung des Betreibers |

Zählung der Liste: 258 Einträge, davon P0 40, P1 82, P2 88, P3 48.

<!--ENDE-->
