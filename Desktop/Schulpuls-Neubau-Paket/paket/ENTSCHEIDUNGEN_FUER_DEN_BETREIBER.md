# Entscheidungen für den Betreiber

Diese Liste ist für **Sie**, nicht für das Neubau-Team. Das Team baut bis zu Ihrer Antwort mit der **Empfehlung als Annahme** weiter (Master-Prompt, Abschnitt 6) und stellt sie nie als beschlossen dar. Antworten Sie knapp mit der Nummer und „ja“, „nein“ oder der gewählten Option. Die vollständige Liste (E-01 bis E-40, mit allen Optionen und betroffenen Anforderungen) steht in `10_ROADMAP_OFFENE_PUNKTE.md`, Abschnitt 2.

## A Vor dem Start des Neubaus (damit nichts Grundsätzliches später umgebaut werden muss)

| Nr. | Frage | Empfehlung |
|---|---|---|
| E-S1 | **Technik des Neubaus:** gleicher Stack wie heute (Python/FastAPI, SQLAlchemy mit Alembic, React/TypeScript, SQLite/PostgreSQL, Container) oder freie Wahl? | Gleicher Stack. Dann vergleicht der Test das Vorgehen, nicht die Technik. Abweichungen nur mit schriftlicher Begründung. |
| E-30 | Mehrere Klassenleitungen je Klasse und weitere Klassenrollen (Stellvertretung, Klassensprecher, Abteilungsleitung) von Anfang an im Datenmodell? | Ja. Später sind es viele Folgeänderungen (Kursräume, Selbstbereich, Rechte, Löschweitergabe). |
| E-24 | Module einzeln ein/aus verkaufen oder ein Paket je Schule? | Module technisch vorsehen, Preis zunächst ein Paket je Schule. |
| E-31 | Welche großen Module wann: Zeugnis (nur Daten zuliefern oder Kopfnoten/Konferenz), Ganztag, Schülerakte, Mensa, Notfallbenachrichtigung, AG-Zuteilung, Oberstufenplanung, Deputat? | Fokus NRW; Zeugnis nur Daten zuliefern; der Rest auf Nachfrage. |
| E-23 | Bewusst nicht gebaut: Quiz, SCORM, Videokonferenz, Plagiatsprüfung, KI-Assistenz, Bezahlfunktion für Eltern, Plugin-Markt, Zeugnisdruck. Bestätigen? | Bestätigen. Quiz/H5P nur per Link oder LTI, Videokonferenz nur als signierter Link. |
| E-01 | **Produktname:** „Schulpuls“ ist im Bildungsbereich schon von einem anderen Unternehmen in Benutzung. | Intern Arbeitstitel behalten; nach außen erst nach anwaltlicher Markenrecherche (DPMA, EUIPO, WIPO) einen freien Namen. |

## B Sicherheit und Konten (wirken auf das heutige System und den Neubau)

| Nr. | Frage | Empfehlung |
|---|---|---|
| E-03 | **Sicherheitswelle freigeben:** die drei live bestätigten hohen Lücken (Inhaber-Schutz auf allen Wegen, Stammdaten-Exporte, API-Tokens) wurden am 17.10. vorgeschlagen, aber nicht freigegeben. | Ja, vollständig und sofort. |
| E-05 | **Vertretung für das Inhaber-Passwort:** ein zweiter Admin, dem der Inhaber ausdrücklich das Zurücksetzen erlaubt. Bauen? | Bauen, mit Zusatzschutz: nur ausdrückliche Vergabe durch den Inhaber, jederzeit widerrufbar, Benachrichtigung, Protokoll. |
| E-04 | Zwei-Faktor-Pflicht für wen? | Administration, Schulleitung, Sekretariat, Planung; Lehrkräfte einstellbar. |
| ANM-001 | **Anmeldung in zwei Schritten** (Benutzername, dann Passwort/Code) gegen das Sicherheitsaudit (verrät, ob ein Konto Zwei-Faktor hat). | Beim Neubau Ihre Entscheidung vom 16.10. beibehalten, das Risiko dokumentieren. Bitte bestätigen oder umentscheiden. |
| REC-060 | **Admin und Gesundheitsdaten:** freie Rechtevergabe (Ihr Wunsch) oder harte Grenze (Audit)? | Freie Vergabe mit deutlicher Warnung und Protokoll (heutiger Stand). Bitte bestätigen. |
| REC-059 | Schüler- und Elternrollen sehen auch bei frei vergebenen Rechten nur eigene Daten bzw. die ihrer Kinder. | Ja, als harte Obergrenze. |
| ANM-047 | Zwei-Faktor auch bei Anmeldung über Google/Microsoft usw.? | Ja, auf allen Anmeldewegen. |
| E-07 | **Beobachtete Konten:** Zweck, Rechtsgrundlage, Information der Betroffenen, Speicherdauer 180 Tage sind ungeklärt. | Nur Test-/Demo-Konten mit schriftlicher Information; Chat-Inhalte nie erfassen. |
| E-06 | Passwortregeln: Mindestlänge, Prüfung auf geleakte Passwörter. | Mindestlänge 10 für Personal, 8 für Schüler/innen und Eltern; nur Offline-Liste, Online-Prüfung als abschaltbare Option. |
| E-37 | Google-/Apple-Anmeldung für Schüler/innen? | Nein; nur Personal und Erwachsene, Landes-Login bevorzugt. |
| INT-092 | E-Mail und SMS in der Oberfläche einstellbar (Backlog-Wunsch) gegen die Sicherheitsregel, dass das SMTP-Ziel nur per Umgebung gesetzt werden darf. | Sicherheitsregel gilt; Einstellung nur für Zugangsdaten, nicht für das Ziel. |

## C Daten, Recht, Schule

| Nr. | Frage | Empfehlung |
|---|---|---|
| E-35 | Voreingestellte Aufbewahrungsfristen bestätigen (Gesundheitsdaten, Nachrichten, Benachrichtigungen 30 Tage; Abgaben und Formulare 90 Tage; Noten und Lernstand 180 Tage; Klassenbuch-Anwesenheit 1 Jahr; Audit-Log 1 Jahr; API-Protokoll 90 Tage). | Als änderbare Voreinstellung bestätigen, Landesrecht prüfen lassen, „0“ verbieten. |
| E-36 | Datenschutzrichtlinien (Chat, Gesundheitsdaten) und externe Rechtsprüfung (DSFA, Mustertexte, AV-Vertrag, Löschfristen). | Fachperson beauftragen; Vorlagen bis dahin als „Entwurf“ kennzeichnen. |
| E-11 | Notenbuch-Einsicht Standard. | „Nach Freigabe“, Wahl in der Einrichtung erzwingen. |
| E-16 | Minderjährige: Altersgrenze 18 bestätigen; „Meine Fehlzeiten“ für Minderjährige ausblenden (Eltern sehen sie); Klassenbuch-Thema für Schüler/innen und Eltern sichtbar, Notizen nie. | Wie vorgeschlagen. |
| E-17 | Rundschreiben an Eltern volljähriger Schüler ohne deren Wahl. | An beide, bis die Schülerin bzw. der Schüler entscheidet. |
| E-12 | Audit-Ausnahmen (eigene Benachrichtigungen löschen, Zwischenspeichern von Selbsttests, einzelne Chat-Nachrichten, Lesemarkierungen). | Erlaubt, in der Datenschutzdokumentation ausdrücklich festhalten. |
| E-13 | Chat-Moderation bei Ende-zu-Ende-Verschlüsselung; Chat-Kompression; GIF-Suche. | Melder gibt die gemeldete Nachricht frei; Kompression nicht bauen; keine Drittanbieter-GIF-Suche. |
| E-22 | Elternbriefe, Elternsprechtag, Briefübersetzung. | Briefe vor Sprechtag; Übersetzung nur als abschaltbares Modul mit lokalem oder EU-Dienst. |

## D Oberfläche und Planung

| Nr. | Frage | Empfehlung |
|---|---|---|
| E-14 | Menü-Knopf im Monitor: „kaum sichtbar“ gegen Auffindbarkeit/Tastatur/Kontrast. | Erkennbar (Kontrast mindestens 3:1) und per Tastatur erreichbar. |
| E-33 | Design-Richtung: Referenzprodukte nennen (Vorschläge: Linear, WebUntis-App, Notion) und die Seite mit dem meisten „Text-Müll“ benennen. | Referenzen festlegen, bevor der Neubau die Oberfläche gestaltet. |
| E-18 | Samstag/Sonntag im Raster immer oder nur bei Terminen; Wochenzählung ab Woche 1 des Kalenderjahrs. | Standard nur bei Terminen, Schalter „immer“; Zählung wie vorgeschlagen. |
| E-19 | Planungs-Reiter, Empfehlung in Plan-Vorschlägen, Auto-Planer. | Ein Reiter mit Unterbereichen; Empfehlung als Markierung mit Warnung; kein Auto-Planer, nur Vorschlagspakete. |
| E-15 | Rechte: Schulleitung darf den Generator starten? Sekretariat darf Anträge genehmigen? | Ja, jeweils über einen Rechte-Schalter, Standard aus. |
| E-02 | Wettbewerbs-Kleinfunktionen (Schnellsuche Strg+K, Rückmeldeknopf, Vorlagen) und Ausbau-Wellen 2 bis 4. | Einzeln freigeben, Reihenfolge laut Welle 2. |
| E-20 | Push und App. | Installierbare PWA mit Web-Push nach Welle 1. |

## E Betrieb und Vertrieb

| Nr. | Frage | Empfehlung |
|---|---|---|
| E-09 | Hauptserver, Demo und Test laufen im Entwicklungsmodus. | Test-Instanz zuerst auf Produktionsmodus; die erste echte Schule bekommt eine eigene Instanz im Produktionsmodus. |
| E-10 | HTTP im Heimnetz erlaubt (Cookies ohne Secure-Kennzeichen). | Abschalten bzw. auf die Domain umleiten. |
| E-25, E-26 | Update-Dienst ohne Container-Rechte; Hosting des Lizenzservers. | Host-Job statt Docker-Zugriff; externer Hoster ab dem ersten zahlenden Kunden. |
| E-27 | Zahlungen. | Zunächst Rechnung und Überweisung; Stripe/GoCardless erst bei Bedarf. |
| E-29, BET-177/178 | Wer gibt Demo-Zugänge aus; Rollen-Knöpfe ohne Passwort auf der Demo-Seite. | Nur der Inhaber; Rollen-Knöpfe nur auf der Demo-Instanz. |
| E-28 | Code-Schutz und Patent. | EULA durch Anwalt, nicht abschaltbare Lizenzprüfung, Wasserzeichen; Patentanwalt befragen. |
| E-34 | Vertriebsweg, Pilotschule. | Persönliche Einzelanfrage und Schulträger; Pilotschule mit eigener Instanz. |
| E-40 | Heimanschluss für große Schulen zu klein; Domain je Schule. | Hoster-Angebot ab mittlerer Schulgröße. |
| E-21 | Landes-Login und Landes-Exporte: welche Länder zuerst? | NRW zuerst, Landes-Login vor dem ersten Verkauf in NRW. |

## F Kleinere Festlegungen der Schreiber (bitte kurz durchsehen)

- Vertretungsarten: zehn statt neun (mit „Mitbetreuung“). Der Gefahr-Knopf ist nur für zerstörende Aktionen, nicht für „Krank melden“.
- Die Seite `/datenschutz` ist aufgeteilt: öffentliche Hinweise und Auskunft unter `/datenschutz`, Verwaltung unter `/datenschutz/verwaltung`.
- Untis-Import: Die Quellen nennen „8 Feldzuordnungen“, der alte Code markiert aber 9 unsichere Stellen. Der Neubau braucht einen **echten Untis-Export** als Testdatei von Ihnen.
- CSV-Import ist „ganz oder gar nicht“ (der Altstand importierte die gültigen Zeilen).
- Offline-Frist der Lizenz: 7 Tage Bestätigung plus 14 Tage Kulanz (nicht die früher genannten 30).
- Ihre Beschwerde vom 16.10. (22:12) zu Live-Anzeige, Glocke und Hell/Dunkel-Umschalter blieb unbeantwortet: Was genau war gemeint?
- Die Hex-Werte der Statusfarben, die Raster-Grenze (600 oder 700 px) und Woche 1–52/53 sind noch festzulegen; bis dahin gelten Vorschläge im Paket.
