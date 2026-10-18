# 02e · Funktionen: Integrationen, Import/Export, API-Zugänge (Kürzel INT)

Stand der Quellen: 18.10.2026 (Gesprächsstand bis 17.10.2026). Sprache Deutsch. Alle Oberflächentexte in Sie-Form (auch für Schüler/innen). Erklärungen stehen nur im Hilfe-Symbol bzw. Hilfetext, nie als Absatz auf der Seite.

## 0. Lesehilfe

**Priorität:** P0 = Pflicht (Sicherheit, Recht, Datentrennung) · P1 = Kernfunktion · P2 = wichtig · P3 = Wunsch.
**Status:** `Status: Ist` = im Altbestand gebaut (muss im Neubau mindestens so vorhanden sein) · `Status: offen` = gewünscht, geplant oder als Lücke erkannt, nicht gebaut.
**Zeichen:** `[unklar: …]` = die Quellen belegen den Wert oder die Entscheidung nicht. Zitate des Betreibers stehen in „…“ mit Datum (MM-TT, Jahr 2026). Spätere Entscheidungen überstimmen frühere; die Überstimmungen stehen in Abschnitt 10.1, die offenen Punkte in 10.3.
**Rechte-Namen** wie im Rechte-Katalog (Datei 04): u. a. `api.own`, `api.manage`, `audit.read`, `masterdata.edit`, `masterdata.read`, `timetable.edit`, `plans.read_all`, `rooms.read`, `students.read`, `substitution.read`, `announcement.post`, `channels.manage`, `settings.edit`, `system.admin`, `gradebook.export`, `forms.inbox`, `mail.custom_server`, `users.manage`.

**Begriffe**

| Begriff | Bedeutung |
|---|---|
| Zugang (API-Zugang) | Maschinenzugang mit Umfang: Token mit Präfix `sma_`, gehört einem Konto, hat Bereiche, Filter, Art, Ablauf, optional IP-Freigabe und Ratenlimit |
| Persönliches Token | Token mit Präfix `smt_`; wirkt wie das Konto, ohne Umfang |
| Bereich | Datenart der offenen Schnittstelle (timetable, substitutions, calendar, rooms, announcements, directory) |
| Offene API | die Routen unter `/api/v1/open/…`, ausschließlich mit Token erreichbar |
| Lauf | ein Importvorgang eines Fremdsystems (Tabelle `import_runs`) |
| Trockenlauf / Vorschau | vollständige Berechnung eines Imports ohne Änderung der Daten |
| Outbox | Warteschlange ausgehender Nachrichten (Webhook, E-Mail, SMS) mit Wiederholungen |

**Abgrenzung zu anderen Dateien des Pakets** (hier nur Verweise, die Regeln stehen dort): Anmelde-Verhalten, Sitzungen, Zwei-Faktor, Anmelde-Richtlinien → ANM · Löschfristen, Verschlüsselung, Audit-Aufbewahrung, Auskunft Art. 15 → DAT · Benachrichtigungsarten, Glocke, Ruhezeiten → BEN · Notenbuch-Fachlogik → NOT · Fragen-GIFT, Fortschritt-Tabellen → KUR · Formular-Baukasten → FOR · Einrichtungsassistent, Jahreswechsel, Stammdaten-Fachregeln → STA · Lizenzserver, Updates, Zahlungs-Webhooks, Offsite-Sicherung, Konfigurations-Prüfungen beim Start → BET · Rate-Limit, Header, Härtung allgemein → SIC.

---

## 1. Leitplanken (Querschnitt für alle Integrationen)

**INT-001** · P1 · Status: Ist — **Import ist nie Pflicht.** „dass man quasi nicht importieren muss, sondern nur kann“ (10-16). Selbst anlegen ist der Hauptweg; an jeder Stelle, an der ein Import angeboten wird (Einrichtungsassistent, Stammdaten, Kursräume), ist er nur Alternative.
Abnahme: Neue, leere Instanz: Der Einrichtungsassistent lässt sich in allen Schritten ohne eine einzige Importdatei abschließen; kein Pflichtfeld und kein Schritt verlangt einen Import.

**INT-002** · P0 · Status: Ist — **Vorschau vor Übernahme.** Jeder schreibende Import (CSV, Untis, JSON, Konfigurations-ZIP, Fremdsysteme, Ferien) bietet eine Vorschau (Trockenlauf), die nichts ändert, und übernimmt erst nach ausdrücklicher Bestätigung. Fremdimport-Vorschau läuft vollständig und wird zurückgerollt. [Konfigurations-ZIP: siehe INT-063, Status offen.]
Abnahme: Datei hochladen, „Vorschau“ → Zählwerte und Probleme erscheinen, Zeilenzahl aller Fachtabellen vor und nach der Vorschau identisch; erst „Übernehmen“ ändert Daten.

**INT-003** · P0 · Status: Ist — **Rechte im Backend, fremde Ressourcen 404, Schreibaktionen im Audit.** Jede Integrationsfunktion prüft Rechte serverseitig. Unbekannte oder fremde Ressourcen (Zugang, Importlauf, Outbox-Eintrag, Mail-Konto) antworten 404, nie 403. Jede schreibende Aktion (Anlegen/Widerruf eines Zugangs, Schalter, Import, Rückgängig, Webhook-/SMTP-/SMS-Konfiguration) steht im Audit ohne Inhalte (nur IDs, Zählungen, Zugangskennung).
Abnahme: Konto ohne `api.manage` ruft den Zugang einer anderen Person ab → 404; nach Anlegen, Widerruf und Import je ein Audit-Eintrag mit Konto, Zeit und Zählwerten, ohne Dateiinhalt und ohne Klartext-Token.

**INT-004** · P0 · Status: Ist — **Datenminimierung nach außen.** Exporte und Schnittstellen geben nie Gesundheits-, Förder-, Fehlzeit- oder Nachrichtendaten und nie Abwesenheitsgründe von Lehrkräften aus (nicht in iCal, Monitor, API, Untis-Export; Untis-Export Standard ohne Abwesenheitsgründe, Schülerdaten wegschaltbar). Weitergabe an Dritte nur im jeweiligen Zweck (Untis, Schulmanager-Online-Paket, OneRoster, Kalender enthalten Personendaten).
Abnahme: Lehrkraft mit eingetragenem Abwesenheitsgrund „krank“: Untis-Export (Standard), iCal-Feed und offene API-Antwort enthalten den Grund an keiner Stelle (Volltextsuche im Ergebnis); Untis-Export mit Option „Schülerdaten weglassen“ enthält keine Schülerdatei.

**INT-005** · P0 · Status: Ist — **Demo-Sperre.** In der öffentlichen Demo sind gesperrt: alle Importe (JSON/CSV/Untis/Fremdsysteme), Kompetenz-Import und -Verwaltung, Webhooks, API-Zugänge, Mail-Konten, Ferien-Import, Briefversand per E-Mail, Benachrichtigungs-Einstellungen der Schule und Postausgang, Lizenz, Sicherheits-Einstellungen, Aufbewahrungsfristen, Anzeige abwesender Lehrkräfte. Jede schreibende Route ist standardmäßig gesperrt, außer sie steht ausdrücklich auf der Freigabeliste; ein Test prüft alle Routen und dass kein Eintrag veraltet ist.
Abnahme: In der Demo schreibender Aufruf auf eine neue, nicht freigegebene Route → 403; `POST /import/csv/students`, Webhook-Einstellung speichern, Zugang anlegen → je 403; der Routen-Test schlägt fehl, wenn eine neue Schreibroute weder gesperrt noch ausdrücklich freigegeben ist.

**INT-006** · P1 · Status: Ist — **Neue Import-/Export-Formate nach festem Muster.** Je Format ein eigenes Modul für Lesen und Schreiben; Route mit Rechteprüfung; Änderungen laufen über die gemeinsame Änderungsfunktion (Verlauf, Rückgängig, Audit); Oberfläche; Test. Die Feldliste einer Datenart wird **einmal** im Backend geführt; die Oberfläche lädt sie vom Server (`GET /import/csv/{what}/fields`) – keine zweite Handkopie (Fehlerquelle im Altbestand).
Abnahme: Ein neues Feld in der Backend-Feldbeschreibung erscheint ohne Änderung im Frontend im Zuordnungsdialog und im CSV-Export; ein Test schlägt fehl, wenn für ein registriertes Format Route, Rechteprüfung oder Rundlauf-Test fehlt.

**INT-007** · P2 · Status: offen — **Standards vor Einzelformaten.** Reihenfolge der Anbindungen: OneRoster als Standardweg ausbauen, danach Landes-Login (Schulconnex/VIDIS), LTI 1.3 und SCIM; Einzelformate nur, wenn eine echte Beispieldatei vorliegt (Details INT-101 und INT-102).
Abnahme: Für jede neue Anbindung liegt vor dem Bau die offizielle Formatbeschreibung oder eine echte, anonymisierte Beispieldatei vor und ist im Rundlauf-Test verwendet.

**INT-008** · P2 · Status: Ist — **Produktname nur zentral.** Sichtbare Namen in Exportdateien (LIESMICH, Briefe), ausgehenden Anfragen (z. B. Ferien-Abfrage) und Texten kommen aus der einen zentralen Namenskonfiguration. Technische Kennungen (Header-Präfix `X-<Technikname>-…`, Format-Kennung der JSON-Hülle, Metadaten-Kennung in Untis-Dateien) sind eine Konstante und ändern sich bei Umbenennung nicht (Rollback und Updates bleiben kompatibel). Ist: Technikname „schulmanager“.
Abnahme: Produktname in der zentralen Konfiguration ändern → LIESMICH, Ferien-Anfragekennung und Zugangstexte zeigen den neuen Namen; Header-Präfix und Format-Kennung bleiben unverändert; Quelltextsuche findet den sichtbaren Produktnamen nur an der einen Stelle.

---

## 2. API-Zugänge: Verwaltung

### 2.1 Zweck, Seite, Assistent

**INT-009** · P1 · Status: Ist — **Zweck.** Lehrkraft oder Administration gibt ausgewählte Daten für Anwendungen und KI-Werkzeuge frei: „für zum Beispiel jetzt einen Stundenplan, für den kompletten Stundenplan oder nur für bestimmte Schüler oder nur für bestimmte Lehrer oder bestimmte Umgebungen, Nachrichten oder so“ (10-12 18:20). „Nachrichten“ ist als Bereich **Mitteilungen** (Schwarzes Brett) umgesetzt; private Nachrichten und Chats sind nie freigebbar (INT-036).
Abnahme: Lehrkraft mit `api.own` legt einen Zugang mit Bereich Stundenplan und Filter Klasse 5a an; Aufruf mit dem Token liefert den Plan 5a (200), den Plan 5b (403).

**INT-010** · P1 · Status: Ist — **Seite „API-Zugänge“.** Menü Verwaltung, sichtbar bei `api.own` oder `api.manage` (eines genügt). Oberflächenpfade beginnen **nicht** mit `/api` (der Altbestand-Pfad `/api-zugaenge` kollidierte mit dem Schnittstellen-Präfix und lieferte beim Direktaufruf 404 des Backends). Reiter: Zugänge, Protokoll, Einstellungen (Einstellungen nur mit `api.manage`).
Abnahme: Konto ohne beide Rechte: Menüeintrag fehlt, Direktaufruf der Seite → keine Inhalte (403/Weiterleitung); Konto mit `api.own`: Seite lädt auch nach Neuladen der Adresse im Produktionsbetrieb ohne 404.

**INT-011** · P1 · Status: Ist — **Assistent „Neuer Zugang“ in vier Schritten:** (1) Name und Zweck (Freitext, z. B. „Vertretungsplan im Foyer“), (2) Bereiche, (3) Filter (Klassen, Lehrkräfte, Räume, Schüler/innen, Standorte), (4) Prüfung mit Art, Laufzeit, IP-Freigabe, Ratenlimit und Vorschau-Satz „Dieser Zugang darf: …“ sowie „Nie: …“ (gesperrte Datenarten). Die Vorschau ruft dieselbe Prüfung wie das Anlegen auf (`POST /api-access/preview`), ohne anzulegen. Bereiche und Filterwerte kommen aus `GET /api-access/meta` und enthalten nur, was das Konto selbst freigeben darf. [unklar: Zuordnung von Laufzeit/IP/Limit zu Schritt 1 oder 4.]
Abnahme: Schritt 4 zeigt „Dieser Zugang darf: Stundenplan der Klasse 5a“ und „Nie: …“; die Vorschau legt keinen Zugang an (Liste unverändert); ein Bereich, den das Konto nicht nutzen darf, ist nicht wählbar (Hilfe-Symbol erklärt warum).

**INT-012** · P1 · Status: Ist — **Eingabegrenzen.** Ablauf 1 bis 365 Tage, Standard 90, **kein unbefristeter Zugang**. Ratenlimit Anfragen je Minute: Standard 60, höchstens 600. Höchstens 25 aktive Zugänge je Konto. Höchstzahl der Werte je Filter und Länge von Name/Zweck: [unklar: Wert nicht belegt, im Neubau festlegen]. Zweck-Freitext höchstens 300 Zeichen, Name höchstens 100 Zeichen.
Abnahme: Ablauf 0 oder 366 → 422 mit deutschem Text; ohne Angabe → Ablauf in 90 Tagen; Limit 601 → 422; 26. aktiver Zugang → abgelehnt mit verständlicher Meldung; abgelaufene/widerrufene zählen nicht zu den 25.

**INT-013** · P1 · Status: Ist — **IP-Freigabe (optional).** Liste von Adressen oder Netzen in CIDR-Schreibweise; leer = keine Beschränkung. Anfrage von nicht freigegebener Adresse wird abgelehnt und mit Ergebnis `ip_denied` protokolliert. [unklar: HTTP-Status der Ablehnung.]
Abnahme: Zugang mit `192.0.2.0/24`; Aufruf von `198.51.100.7` → abgelehnt, Protokollzeile mit `ip_denied`; Aufruf von `192.0.2.15` → 200.

**INT-014** · P0 · Status: Ist — **Token-Erzeugung und -Speicherung.** Token mit Präfix `sma_` plus zufälligem Anteil [unklar: Länge in Byte; persönliches Token: 32 Byte]. Der Klartext erscheint genau einmal in der Antwort des Anlegens (Dialog mit Kopierfunktion und Beispielaufruf mit `curl`). Gespeichert wird nur ein nicht umkehrbarer, schlüsselgebundener Hash (HMAC mit dem Schul-Geheimschlüssel `SM_SECRET_KEY`), dazu Präfix zur Wiedererkennung. Bei Verlust: neuen Zugang anlegen.
Abnahme: Nach dem Anlegen enthält kein Datenbankfeld, kein Log und keine API-Antwort den Klartext (Suche nach dem Token → kein Treffer); erneutes Öffnen des Zugangs zeigt nur das Präfix; Token einer anderen Schule → 401.

**INT-015** · P0 · Status: Ist — **Anlegen nur mit Sitzung.** Zugänge werden nur nach Anmeldung in der Oberfläche (Sitzung und CSRF-Schutz) ausgestellt; ein Token (persönlich oder Zugang) stellt keine Zugänge aus.
Abnahme: `POST /api-access` mit Bearer-Token → 403; mit Sitzung ohne gültiges CSRF-Kopfzeilenfeld → 403 `csrf_failed`; mit Sitzung und CSRF → 201.

**INT-016** · P0 · Status: Ist — **Rechte der Verwaltung.** `api.own`: eigene Zugänge anlegen, ansehen, deren Nutzung einsehen, widerrufen. `api.manage`: alle Zugänge der Schule sehen, prüfen, widerrufen, Schuleinstellung ändern. `audit.read`: Protokoll aller Zugänge. Standardrollen: `api.own` Administration, Schulleitung, Sekretariat, Planung, Abteilungsleitung, Lehrkraft; `api.manage` Administration, Schulleitung. Schüler/innen, Eltern, Schulbegleitung, Hausmeister, Monitor, Zuschauer erhalten kein `api.own` (Ausstellung nur für berechtigte Rollen).
Abnahme: Schüler-Konto `POST /api-access` → 403; Lehrkraft sieht in der Liste nur eigene Zugänge, Schulleitung alle; Lehrkraft ruft `GET /api-access/{id}` eines fremden Zugangs → 404.

**INT-017** · P0 · Status: Ist — **Umfang höchstens wie das eigene Konto.** Der Anleger kann nur Bereiche und Filter wählen, die er selbst nutzen darf: Klassen nach Planzugriff (Lehrkräfte nur geleitete bzw. unterrichtete Klassen laut Planzugriff); fremde Lehrkräfte und Räume nur mit uneingeschränktem Planzugriff (`plans.read_all` ohne Beschränkung); Schüler/innen nur sichtbare. Gesundheits- und Förderdaten sind nie freigebbar.
Abnahme: Lehrkraft ohne Zugriff auf Klasse 7c wählt 7c im Filter → nicht wählbar, per direktem POST abgelehnt (422/403); `GET /api-access/meta` listet nur erlaubte Werte.

**INT-018** · P0 · Status: Ist — **Rechte werden bei jedem Aufruf neu ausgewertet; Lebenszyklus.** Ein Zugang handelt als sein Konto: Rechte und Datenumfang des Kontos gelten bei jeder Anfrage neu; der Umfang beschränkt zusätzlich. Wird das Konto gesperrt, deaktiviert oder gelöscht, ist der Zugang sofort tot (401). Wird die Schule gesperrt (Lizenz), werden alle Zugänge sofort ungültig. Ändert sich die Sichtbarkeit des Kontos (z. B. Klassenleitung entzogen), gilt die neue Sichtbarkeit sofort.
Abnahme: Konto deaktivieren → nächster Aufruf 401; Lehrkraft verliert Klassenleitung 5a → Aufruf Plan 5a mit dem Zugang → 403; Schule gesperrt → Aufruf eines gültigen Tokens 401/403 laut Sperrmeldung.

**INT-019** · P0 · Status: Ist — **Widerruf.** Wirkt sofort, ist endgültig (nicht rückgängig). Berechtigt: Eigentümer oder `api.manage`; sonst 404. Status danach „widerrufen“, Aufrufe 401.
Abnahme: Widerruf, danach Aufruf innerhalb 1 s → 401; Zugang erscheint als „widerrufen“; fremde Lehrkraft ruft `DELETE` des Zugangs → 404.

**INT-020** · P1 · Status: Ist — **Übersicht als Karten:** Name bzw. Zweck, Status (aktiv, abgelaufen, widerrufen), Umfang (Bereiche, Filter), Art, Ablaufdatum, letzte Nutzung, Nutzungszähler. Abgelaufene Zugänge bleiben 30 Tage sichtbar (samt Protokoll), danach räumt die Wartung auf (persönliche Tokens sofort nach Ablauf).
Abnahme: Zugang mit 3 Aufrufen zeigt Zähler 3 und Zeitpunkt der letzten Nutzung; 29 Tage nach Ablauf noch sichtbar, nach 31 Tagen und Wartungslauf gelöscht.

### 2.2 Schreibzugang

**INT-021** · P1 · Status: Ist — **Art „Nur lesen“ (Standard) oder „Lesen und schreiben“.** „Der soll noch Schreibzugang bekommen, also man soll Schreibzugang geben können.“ (10-16 22:12). Bei „Lesen und schreiben“ kann der Zugang optional auf bestimmte Rechte beschränkt werden; wirksam ist die Schnittmenge mit den Rechten des Kontos – ein Zugang hat nie mehr Rechte als sein Konto. Vorhandene Zugänge ohne Art bleiben „Nur lesen“. Ersetzt den Stand vom 10-12 („schreibgeschützt, einzige Schreibfunktion Mitteilungen“).
Abnahme: Zugang „Lesen und schreiben“ mit nur `announcement.post`: Mitteilung anlegen → 201; Änderung eines Stammdatensatzes (Recht nicht gewählt) → 403; Zugang „Nur lesen“: jede schreibende Anfrage → 403.

**INT-022** · P0 · Status: Ist — **Schulweiter Schalter „Schreibzugänge erlauben“** (Schuleinstellung `api_write_tokens`), Standard **aus**; nur mit `api.manage` änderbar; Änderung im Audit (`api_access.settings`). Ist er aus, können Schreibzugänge weder ausgestellt werden noch wirken (403).
Abnahme: Schalter aus: Anlegen mit „Lesen und schreiben“ → 403; vorhandener Schreibzugang `POST` → 403; Schalter ein → beide gelingen; Audit-Zeile mit Konto und Zeit; Lehrkraft ohne `api.manage` ändert Schalter → 403.

**INT-023** · P0 · Status: Ist — **Auch mit Schreibzugang immer gesperrt:** Passwort, Zwei-Faktor, Anmeldewege, Ausstellen von Zugängen/Tokens, Rechte und Rollen, Konten ändern, Lizenz, Sicherung und Wiederherstellung, Sicherheits- und Löscheinstellungen, Sitzungen. Passwort- und Zwei-Faktor-Änderungen gehen nur per Sitzung.
Abnahme: Schreibzugang mit allen Rechten des Kontos ruft je einen Endpunkt aus jeder Kategorie auf (Passwort ändern, 2FA zurücksetzen, Zugang anlegen, Rolle ändern, Lizenz setzen, Sicherung erstellen, Löscheinstellung ändern, Sitzung beenden) → jeweils 403.

**INT-024** · P0 · Status: Ist — **Audit mit Zugangskennung.** Jede Änderung über die Schnittstelle steht im normalen Protokoll mit Token-Bezug (ID und Präfix). Ereignisse: `api_access.create`, `api_access.revoke`, `api_access.announcement`, `api_access.settings`.
Abnahme: Mitteilung über einen Zugang anlegen → Audit-Zeile `api_access.announcement` mit Zugangs-ID und Präfix, ohne Mitteilungstext; Widerruf → `api_access.revoke`.

**INT-025** · P0 · Status: offen — **Entscheidung nötig: Reichweite eines Schreibzugangs.** Die Quellen widersprechen sich: (a) Zugänge mit Umfang dürfen nur unter `/api/v1/open/…`; (b) ein Schreibzugang nutzt die gesamte Schnittstelle als sein Konto. Festlegung für den Neubau: Zugänge „Nur lesen“ erreichen ausschließlich `/api/v1/open/…`; Zugänge „Lesen und schreiben“ erreichen zusätzlich die schreibenden Routen der gesamten Schnittstelle, soweit das gewählte Recht (INT-021) und die festen Sperren (INT-023) es zulassen; Bereiche/Filter gelten nur für die Lese-Routen unter `/open/`. [unklar: Betreiber hat die Reichweite nicht bestätigt.]
Abnahme: „Nur lesen“-Zugang ruft eine Route außerhalb `/open/` → 403; „Lesen und schreiben“ mit Recht `exam.edit` legt eine Klausur an → 201, ohne Recht → 403; Filter Klasse 5a begrenzt weiterhin nur die Lese-Antworten unter `/open/`.

### 2.3 Protokoll

**INT-026** · P1 · Status: Ist — **Protokoll-Reiter** („mir fehlen API-Logs“, 10-16 22:12). Je Aufruf: Zeit, Zugang, Konto, Aufruf (Methode und Pfad ohne Abfrageteil und ohne Token), Bereich, Ergebnis (`ok`, `error`, `ip_denied`, `rate_limited`, `blocked`), HTTP-Status, Dauer in ms, Adresse (IP). Filter: Zugang, Zeitraum, nur Fehler, nur Schreibzugriffe; Blättern; CSV-Export. Gilt für Zugänge und persönliche Tokens.
Abnahme: Zugang mit 3 Aufrufen (davon 1 Fehler, 1 POST): Reiter zeigt 3 Zeilen mit allen Spalten; „nur Fehler“ → 1 Zeile; „nur Schreibzugriffe“ → nur die POST-Zeile; CSV enthält dieselben Zeilen (Formelschutz INT-078); Abfrageteil der Adresse und Token kommen in keiner Zeile vor.

**INT-027** · P0 · Status: Ist — **Sichtbarkeit und Aufbewahrung des Protokolls.** Jede Person sieht die Aufrufe ihrer eigenen Zugänge; `api.manage` bzw. `audit.read` sehen alle. Aufbewahrung 90 Tage (Datenart `api_log`, Altersfrist einstellbar); Protokollzeilen der Tokens eines Kontos 30 Tage nach Austritt des Kontos gelöscht. Keine Antwortinhalte, keine Personendaten außer Konto und IP im Protokoll. Aufrufe unbekannter Adressen (nicht existierende Pfade) werden nicht protokolliert [unklar: Wortlaut „unbekannter Adressen“; vermutet nicht zuordenbare Pfade, damit Sondierungen das Protokoll nicht fluten]. Obergrenze der Zeilen je Zugang: [unklar].
Abnahme: Zeile älter als 90 Tage ist nach dem Wartungslauf gelöscht; Konto A sieht Zugang von B im Protokoll nicht (404 beim direkten Abruf); Aufruf eines nicht existierenden Pfades mit gültigem Token erzeugt keine Zeile.

**INT-028** · P1 · Status: Ist — **Ratenlimit je Zugang.** Anfragen je Minute (Standard 60, höchstens 600); bei Überschreitung 429 mit `Retry-After`, Ergebnis `rate_limited`. Ist: Zähler im Speicher des Serverprozesses (nur ein Worker); Neubau: Zähler gilt je Zugang und überlebt den Betrieb mehrerer Prozesse [unklar: Verhalten nach Neustart festlegen]. Zusätzlich gilt das allgemeine Limit je IP und Konto (SIC-095).
Abnahme: 61. Aufruf innerhalb einer Minute → 429 mit `Retry-After`; nach Ablauf der Wartezeit wieder 200; Protokollzeile `rate_limited`.

### 2.4 Mandantentrennung

**INT-029** · P0 · Status: Ist — **Mandantentrennung.** „wenn jetzt z.B. unterschiedliche Schulen das benutzen, können auch nur die Schulen ihre eigenen APIs gründen … linken die APIs wirklich nur auf deren eigenen Datenbanken nur deren eigenen space. Kannst du das bitte sicherstellen und alles was bis jetzt gebaut wurde applyn, dass ich das testen kann.“ (10-12 18:46). Jede Schule läuft als eigene Instanz mit eigener Datenbank, eigenem Dateispeicher/Datenvolumen und eigenem Geheimschlüssel (32 Byte zufällig, als Hex); Schlüssel und Datenvolumen werden nie geteilt. Zugangs-Tokens sind nur als HMAC mit dem Schlüssel der eigenen Schule gespeichert; ein Token einer anderen Schule ist wertlos (401), auch bei in die Datenbank kopierter Zeile. Beim Einrichten einer weiteren Schule entsteht automatisch ein neuer zufälliger Schlüssel.
Abnahme: Test `token_of_other_school_is_useless`: Token aus Instanz A gegen Instanz B → 401; Datenbankzeile des Zugangs aus A nach B kopiert → Token weiterhin 401; zwei Instanzen teilen weder Volumen noch Schlüssel (Prüfung der Konfiguration beim Anlegen einer Schule).

**INT-030** · P2 · Status: Ist — **API-Zugänge sind Standard für jede künftige Funktion** (10-12 18:20, 18:46): „bitte auch weiterhin in den Standard einbauen“; jede Schule nur auf ihren eigenen Daten. Verfahren: INT-041.
Abnahme: siehe INT-041 (Prüftest für neue Funktionen).

---

## 3. Offene API (`/api/v1/open/…`)

**INT-031** · P1 · Status: Ist — **Schnittstelle.** Versionierter Pfad `/api/v1/open/…`, ausschließlich mit Token (Kopfzeile `Authorization: Bearer …`). Kein Lesezugriff ohne Token, auch nicht für scheinbar öffentliche Daten (Klassen, Standorte, Kalender). Antworten JSON, Zeitzone Europe/Berlin.
Abnahme: Jede Route der Tabelle R-1 ohne Token → 401; mit gültigem Token und passendem Bereich → 200.

**R-1 Bereiche und Routen**

| Bereich | Routen (GET, wenn nicht anders) | Filter | Recht des Kontos (eines davon genügt) |
|---|---|---|---|
| timetable (Stundenplan) | `/open/timetable/{kind}/{ref}` – kind: Klasse, Lehrkraft, Schüler/in, Raum [unklar: Schreibweise der kind-Werte]; Raum zusätzlich Bereich rooms | classes, teachers, students, rooms, sites | `plans.read_all`, `timetable.edit` |
| substitutions (Vertretung) | `/open/substitutions` (ein Tag), `/open/substitutions/range` (Zeitraum) | classes, teachers, rooms, sites | `substitution.read` |
| calendar (Termine) | `/open/calendar/school-year`, `/open/calendar/week` | classes, teachers, students, rooms, sites | `plans.read_all`, `timetable.edit` |
| rooms (Räume) | `/open/rooms` | rooms, sites | `rooms.read`, `timetable.edit` |
| announcements (Mitteilungen) | `GET` und `POST /open/announcements` | classes, sites | lesen: kein zusätzliches Recht; schreiben: `announcement.post` |
| directory (Verzeichnis) | `/open/classes`, `/open/teachers` (nur Kürzel und Name), `/open/sites` | classes, sites | `plans.read_all`, `masterdata.read`, `timetable.edit` |

**INT-032** · P0 · Status: Ist — **Prüfreihenfolge je Aufruf:** (1) Token vorhanden, nicht widerrufen, nicht abgelaufen, Konto aktiv, Schule nicht gesperrt → sonst 401 `invalid_token`; (2) Herkunftsadresse freigegeben (falls gesetzt); (3) Ratenlimit; (4) Bereich liegt im Umfang des Tokens; (5) das Konto hat das Recht für den Bereich (R-1); (6) Filter werden auf die Daten angewendet. Antworten siehe R-2.
Abnahme: je ein Aufruf pro Fall der Tabelle R-2 liefert Statuscode und Ergebnis laut Tabelle (Test pro Zeile).

**R-2 Fehlerfälle der offenen API**

| Fall | Antwort | Protokoll-Ergebnis |
|---|---|---|
| Token fehlt, unbekannt, widerrufen, abgelaufen, Konto inaktiv, Token einer anderen Schule | 401 `invalid_token` | – / `blocked` |
| Adresse nicht freigegeben | [unklar: Status] | `ip_denied` |
| Ratenlimit überschritten | 429 mit `Retry-After`, Grund `rate_limited` | `rate_limited` |
| Bereich nicht im Zugang; Plan/Route außerhalb der Freigabe; Schreibzugang oder Schalter aus | 403 | `blocked` |
| Konto hat das Recht für den Bereich nicht | 403 | `blocked` |
| Unbekannte Ressource | 404 | `error` |

**INT-033** · P0 · Status: Ist — **Filter-Logik.** `classes`, `teachers`, `rooms`, `students` ergeben zusammen die erlaubte Menge, verknüpft mit ODER („Klasse 5a oder Lehrkraft MUS“). `sites` schränkt zusätzlich ein, verknüpft mit UND. Ohne Filter gilt alles, was das Konto sehen darf. Pläne außerhalb der Freigabe → 403.
Abnahme: Zugang Klasse 5a + Lehrkraft MUS: Plan 5a → 200, Plan MUS → 200, Plan 5b → 403; zusätzlich Standort „Nord“: Plan 5a an Standort „Süd“ → 403.

**INT-034** · P0 · Status: Ist — **Ausgabe wird bereinigt.** Die Antwort entfernt immer Schlüssel mit Gesundheits-, Förder- oder Fehlzeitenbezug (z. B. `reason`, `attendance`, `support`, `homework`, Nachschreibtermine). Das Lehrkräfte-Verzeichnis liefert nur Kürzel und Name.
Abnahme: Vertretung mit Abwesenheitsgrund und Hausaufgabe im Backend → die Antwort enthält keinen dieser Schlüssel (Schlüsselsuche über alle Bereiche in einem Test); `/open/teachers` enthält nur Kürzel und Name.

**INT-035** · P0 · Status: Ist — **Verzeichnis und Rechte nach Route.** Das Konto braucht für jede Route eines der in R-1 genannten Rechte; ohne Recht 403, auch wenn der Bereich im Zugang steht. (Die Kommanotation der Altquelle „rooms.read,timetable.edit“ bedeutet ODER.)
Abnahme: Zugang mit Bereich rooms, Konto ohne `rooms.read` und ohne `timetable.edit` → `/open/rooms` 403; Konto mit `rooms.read` → 200.

**INT-036** · P0 · Status: Ist — **Nie angeboten:** private Nachrichten und Chats, Krankmeldungen, Atteste, Nachteilsausgleich und Förderdaten, Fehlzeiten/Abwesenheiten, Gesundheitsdaten, Noten, Schülerlisten, Konten. Es gibt dafür weder Bereich noch Route; sie erscheinen nicht in Meta, OpenAPI und KI-Beschreibung.
Abnahme: `GET /api/v1/meta/scopes` und `openapi.json` enthalten keinen dieser Bereiche; im Assistenten ist keiner wählbar; eine Route `/open/…` ohne eingetragenen Bereich lässt den Prüftest (INT-041) scheitern.

**INT-037** · P1 · Status: Ist — **Mitteilung anlegen** (`POST /open/announcements`): nur mit Schreib-Zugang, eingeschaltetem Schul-Schalter (INT-022) und `announcement.post` des Kontos; sonst 403. Verfasser ist das Konto, Audit `api_access.announcement`. Schreibfelder und Sichtbarkeit: Felder wie in der Oberfläche (Titel, Text, Zielgruppe, Anzeigezeitraum) [unklar: Feldliste der offenen Schnittstelle nicht belegt]. Schreiben ist unter `/open/` der einzige Schreibzugriff.
Abnahme: Schreib-Zugang mit Schalter ein und `announcement.post` → 201, Mitteilung im Schwarzen Brett sichtbar für die Zielgruppe; Lese-Zugang → 403; Schalter aus → 403; Audit-Zeile ohne Text.

**INT-038** · P1 · Status: offen — **Zeitraum-Grenzen der offenen API.** Vertretungs- und Kalenderabfragen über einen Zeitraum haben eine festgelegte Höchstspanne; Überschreitung → 422 mit deutschem Text. [unklar: Wert im Altbestand nicht belegt; festlegen und in OpenAPI nennen.]
Abnahme: Anfrage über Höchstspanne + 1 Tag → 422; Anfrage genau über die Höchstspanne → 200; Wert steht in `GET /api/v1/meta/scopes`.

---

## 4. Auffindbarkeit für KI-Werkzeuge und Apps, Dokumentation

**INT-039** · P1 · Status: Ist — **Beschreibung für KIs und Apps** (Zitat 10-12 18:20: „dass du da Sachen hinterlegst in den Sachen, die die KI laden würde, damit die KI sich zurecht finden kann“). Ohne Anmeldung abrufbar: `/llms.txt` (kurz), `/llms-full.txt` (Begriffe, Filter, Fehler, Hinweise), `/.well-known/llms.txt`, `/.well-known/api-catalog` (RFC 9727, verweist auf OpenAPI und Beschreibungen), `/api/v1/meta/scopes` (Bereiche, Filter, Grenzen, Endpunkte als JSON), `/api/v1/meta/openapi.json` (OpenAPI **nur** der offenen Schnittstelle; unabhängig vom Dokumentations-Schalter), `/robots.txt` (alles gesperrt außer `/llms*.txt`, `/.well-known/…`, `/api/v1/meta/`). Die Endpunktliste wird aus den registrierten Routen erzeugt; Basisadresse aus `SM_BASE_URL`.
Abnahme: Ohne Anmeldung liefern alle sieben Adressen 200; `robots.txt` sperrt `/` und erlaubt nur die genannten Pfade; die Endpunktliste in `llms.txt` ist gleich der Menge der registrierten `/open/`-Routen.

**INT-040** · P0 · Status: Ist — **Keine Schul- oder Personendaten in der Beschreibung.** Die Beschreibungsdateien enthalten nur Struktur. Ein automatischer Test lädt eine Demo-Schule und prüft, dass kein Name aus den Daten in `llms.txt`, `llms-full.txt`, `scopes` und `openapi.json` vorkommt.
Abnahme: Test mit Demo-Daten (Namen von Lehrkräften, Klassen, Schule) → kein Treffer in den fünf Dokumenten.

**INT-041** · P1 · Status: Ist — **Standard für jede neue Funktion (Projektregel, verbindlich).** Jede neue Funktion, die Daten liefern oder ändern kann, legt fest: (1) Bereich (bestehend oder neu mit Name, Beschreibung, Filter, nötigen Rechten); (2) eine Route unter `/api/v1/open/…` mit Bereichsprüfung (Schreiben zusätzlich mit Schreib-Schalter), Wiederverwendung der vorhandenen Handler mit dem Konto, Ergebnis auf Filter beschnitten, Ausgabe bereinigt (INT-034); (3) OpenAPI-Beschreibung: Zusammenfassung, Beschreibung, Beispielantwort mit erfundenen Daten; (4) Eintrag in der Rechte-Dokumentation; (5) automatischen Test (Bereich verweigert, Filter erzwungen); (6) in der Oberfläche kommt die Bereichsliste aus dem Meta-Endpunkt. „Ein Test schlägt fehl, wenn eine geteilte Route keinen Bereich hat.“
Abnahme: Eine neue `/open/`-Route ohne Bereich, ohne OpenAPI-Beschreibung oder ohne Eintrag in der KI-Beschreibung lässt den Prüftest scheitern; mit allen Einträgen läuft er grün.

**INT-042** · P1 · Status: Ist — **API-Dokumentation für Administration** (`/api/docs`, OpenAPI der gesamten Schnittstelle unter `/api/openapi.json`). Schalter `SM_ENABLE_DOCS`: `off`, `admin` (nur angemeldete Administration), `public`; Standard: Produktion `off`, sonst `admin` („Die API-Doku ist standardmäßig aus; nur Admins schalten sie ein“, 10-16). Die Dokumentation wird lokal ausgeliefert, lädt nichts aus dem Internet und hat eine eigene strenge Inhaltsrichtlinie.
Abnahme: Produktion ohne Schalter: `/api/docs` → 404/403; Wert `admin`: Administration sieht die Seite, Lehrkraft nicht; Netzwerkaufzeichnung beim Öffnen zeigt keine externe Anfrage; `/api/v1/meta/openapi.json` bleibt in allen Modi erreichbar.

---

## 5. Persönliche Tokens (Details in Datei 04, Abschnitt ANM)

**INT-043** · P0 · Status: Ist — **Persönliches Token.** Präfix `smt_` plus 32 Zufalls-Byte; Speicherung als HMAC mit `SM_SECRET_KEY`; Klartext einmal bei Anlage; Name höchstens 100 Zeichen (Standard „API-Token“); Laufzeit optional 1 bis 3650 Tage (ohne Angabe unbefristet – siehe INT-044); wirkt wie das Konto ohne Umfang (für Dritte nur Zugänge mit Umfang ausgeben). Erzeugung nur per Sitzung oder mit eigenem Token und nur für das **eigene** Konto (fremdes Konto → 403); mit Token erzeugt: Laufzeit Pflicht und höchstens die Restlaufzeit des ausstellenden Tokens, Restlaufzeit unter 1 Tag → kein weiteres Token (422). Ungültig (abgelaufen, widerrufen, Konto inaktiv) → 401 `invalid_token`. Änderungen an Passwort und Zwei-Faktor nur per Sitzung; CSRF-Schutz entfällt bei Bearer. „Letzte Nutzung“ wird höchstens alle 60 Sekunden aktualisiert.
Abnahme: Token für fremdes Konto anfordern → 403; mit Token ein weiteres Token ohne Laufzeit → 422; Passwort ändern mit Token → 403; abgelaufenes Token → 401.

**INT-044** · P0 · Status: offen — **Härtung persönlicher Tokens** (Vorschlag 17.10., Freigabe nicht erfolgt): (a) Ablauf ist Pflichtangabe mit Höchstdauer [unklar: Standard und Höchstdauer]; (b) alle Tokens eines Kontos enden bei Passwortwechsel (heute überleben sie ihn); bei Kontosperre sind sie bereits wirkungslos; (c) Ausstellung nur für berechtigte Rollen – Schüler/innen und Eltern stellen keine Tokens aus.
Abnahme: Passwort ändern → vorhandenes Token → 401; Schüler-Konto fordert Token an → 403; Anforderung ohne Laufzeit → abgelehnt oder mit Standardlaufzeit ausgestellt (je nach Festlegung), nie unbefristet.

---

## 6. Importe

Betreiber-Zitate zum Thema: „dass man quasi nicht importieren muss, sondern nur kann“ (10-16); Schulen sollen ihren Bestand „einfach rüber kopieren“, „dass die richtig formatiert werden und richtig eingearbeitet werden“ (10-12 19:22). Hinweis zum Wort „Datenbank übernehmen“ (10-16 12:42): Der Betreiber kannte den Begriff nicht („Ich weiß nicht genau was du meinst mit der Datenbank einfach übernehmen.“); gemeint ist der Import aus anderen Systemen. In der Oberfläche heißt die Funktion „Import aus anderen Systemen“ (Erklärung nur im Hilfe-Symbol).

### 6.1 Gemeinsame Regeln für alle Importe

**INT-045** · P0 · Status: Ist — **Importrechte.** Jeder Import prüft serverseitig ein Recht; ohne Recht 403. Alle schreibenden Importrouten stehen in der Demo-Sperre (INT-005).

| Import | Recht (alle genannten nötig) | Hinweis |
|---|---|---|
| CSV je Datenart | `masterdata.edit` oder `timetable.edit`, je Datenart | [unklar: Zuordnung Datenart → Recht im Einzelnen; stundenplannahe Arten wie Unterricht vermutlich `timetable.edit`] |
| Untis-Dateien | `timetable.edit` | |
| JSON-Vollsicherung | `timetable.edit` und `masterdata.edit` | beide |
| Fremdsysteme (Moodle, OneRoster, WebUntis, Personenlisten) | `masterdata.edit` und `channels.manage`, jeweils ohne Einschränkung | Standardrollen: Administration, Schulleitung. Lehrkräfte, Sekretariat, Planung, Eltern, Schüler/innen → 403. Ansichts-/Zuschauer-Konten sind ausdrücklich ausgeschlossen, weil Importprotokolle Namen enthalten |
| Ferien und Feiertage | `masterdata.edit` | INT-075 |
| Kompetenzrahmen (JSON/CSV) | `competency.manage` | NOT-034 |
| Konfigurations-ZIP | [unklar: Recht nicht belegt] | INT-063 |

Abnahme: Je Tabellenzeile ein Test: Konto ohne das Recht → 403 und kein Importlauf; Lehrkraft ruft `POST /import/fremd/run` → 403; Zuschauer-Konto (Rechte auf dem Papier vorhanden) → 403 beim Fremdimport; Konto mit allen Rechten → Vorschau 200.

**INT-046** · P0 · Status: Ist — **Vorschau (Trockenlauf) und Bindung an die Ausführung.** Stammdaten-Importe (CSV, Untis, JSON, Konfigurations-ZIP): Die Vorschau liefert Zählwerte je Bereich (neu, geändert, unverändert, würde gelöscht, Fehler mit Zeilennummer) und eine Vorschau-Kennung, gebunden an Prüfsumme der Datei, Konto und Optionen; „Übernehmen“ geht nur mit dieser Kennung. Andere Datei, andere Optionen oder fremdes Konto → abgelehnt mit Text „Die Datei hat sich seit der Vorschau geändert. Bitte erstellen Sie die Vorschau erneut.“ [unklar: Statuscode und Gültigkeitsdauer der Kennung.] Fremdsystem-Importe: Die Vorschau läuft vollständig und wird zurückgerollt; der Lauf nutzt dieselben Eingaben; die Prüfsumme der Quelldatei wird im Lauf gespeichert. Vorschauen schreiben nichts und werden nicht im Lauf-Protokoll geführt.
Abnahme: Vorschau mit Datei A, „Übernehmen“ mit Datei B → abgelehnt, Daten unverändert; Zeilenzahl aller Fachtabellen vor und nach der Vorschau identisch; Vorschau-Kennung eines anderen Kontos → 404.

**INT-047** · P0 · Status: offen (Ist: CSV importiert die gültigen Zeilen und meldet Fehlerzeilen) — **Stammdaten-Importe gelten ganz oder gar nicht.** Jede importierte Zeile durchläuft dieselbe Prüfung wie die Eingabe in der Oberfläche und über die Schnittstelle (Pflichtfelder, Kennungen je Sammlung eindeutig ohne Beachtung der Groß-/Kleinschreibung, Verweise auf Klassen/Fächer/Lehrkräfte vorhanden, Jahrgang im Bereich, keine doppelten Fächer). Ein Fehler in einer Zeile verhindert die gesamte Übernahme; der Bericht nennt Datei, Zeilennummer und Grund. Gilt für CSV, Untis, JSON und Konfigurations-ZIP. Ausnahme: Fremdsystem-Importe (6.5) melden fehlerhafte Zeilen, ohne den Lauf abzubrechen (Teilimport mit Konfliktbericht ist dort der Zweck). Das Backlog-Ziel „Import und Stammdaten ohne Datenverlust“ (Priorität P0) überstimmt den Code-Stand vom 13.10. („Zeilenfehler werden gemeldet, die übrigen Zeilen importiert“). [unklar: Die Einrichtungsregel STA-073 führt „alles oder nichts“ bereits als Ist; maßgeblich für den Neubau ist „ganz oder gar nicht“.]
Abnahme: CSV mit 100 Zeilen, Zeile 57 mit Klasse „9z“ (nicht vorhanden) → Meldung „Zeile 57: Klasse 9z existiert nicht“, keine der 100 Zeilen gespeichert; nach Korrektur alle 100 gespeichert.

**INT-048** · P1 · Status: Ist — **Idempotenz und Schonung vorhandener Daten.** Ein erneuter Import derselben Datei ändert nichts („unverändert“ zählt im Bericht); unveränderte Elemente werden nicht neu geschrieben (Fingerabdruck je Element). Leere Zellen ändern vorhandene Werte nicht. Das Geburtsdatum wird nur ergänzt, nie überschrieben; ungültige Daten werden gemeldet, nicht gespeichert. Bei Fremdsystemen hält eine Verknüpfungstabelle (`import_links`: System, Instanz, Art, Quell-Schlüssel → Zielart, Ziel-ID, Fingerabdruck, anlegender und ändernder Lauf) die Zuordnung Quelle → Ziel; ein zweiter Lauf legt keine Dubletten an.
Abnahme: Dieselbe Schüler-CSV zweimal importieren → zweiter Bericht „0 neu, 0 geändert, n unverändert“; Import mit anderem Geburtsdatum bei vorhandenem Wert → Wert bleibt, Hinweis im Bericht; leere Zelle „E-Mail“ → vorhandene E-Mail bleibt.

**INT-049** · P1 · Status: Ist — **Verlauf und Rückgängig der Stammdaten-Importe.** Ein Import ist eine Version im Planverlauf (eine Änderungsfunktion für alle Wege, INT-006); „Rückgängig“ nimmt die letzte Änderung zurück, wer auch immer sie gemacht hat (Recht `history.restore`). Das Audit enthält Import-Art, Zählwerte und Konto, keine Inhalte. Im Demo-Betrieb gesperrt.
Abnahme: CSV-Import (3 neue Klassen) → Verlauf zeigt eine neue Version; Rückgängig → die 3 Klassen sind weg; Konto ohne `history.restore` → 403; Audit-Zeile ohne Dateiinhalt.

**INT-050** · P0 · Status: offen — **Ressourcengrenzen aller Importparser** (Sicherheitsregel SIC-071). Jeder Import (Untis, CSV, JSON, GIFT, Moodle-Abzug/-Sicherung, OneRoster, WebUntis, ZIP) hat Größen-, Zeit- und Entpackgrenzen. Bekannte Werte: Austausch-Import höchstens 50 MiB; Reverse-Proxy 50 MB je Anfrage; Zeitlimit des Browsers für Importe 5 Minuten; große Läufe (ab etwa 20.000 Abgaben) gehören in den Hintergrund (INT-072). Archive: keine Pfadausbrüche („Zip-Slip“, Ist ausgeschlossen); XML wird vollständig geprüft, nicht nur am Dateianfang (Altbestand: nur Anfang, Verdacht). [unklar: Höchstzahl Dateien im Archiv, Größe je Datei, entpackte Gesamtgröße, Kompressionsverhältnis, Verarbeitungszeit – im Neubau festlegen und per Test belegen.] Im Altbestand entpacken zwei Importe ohne Größengrenze.
Abnahme: Archiv über der festgelegten Entpackgrenze → Ablehnung mit Fehlertext, Prozess bleibt unter Speicher- und Zeitgrenze; Archiv mit Pfad `../x` → abgelehnt; Datei über 50 MiB → 413; Import ohne Importrecht → 403.

**INT-051** · P1 · Status: Ist (Frist offen) — **Importprotokoll.** Jeder echte Fremdsystem-Lauf steht in `import_runs`: System, Instanz (Standard „standard“), Name der Quelle, Prüfsumme der Quelldatei, ausführendes Konto (ID und Name), Start, Ende, Status (`ok`, `teilweise`, `fehler`, `zurueckgenommen`), Optionen, Zählwerte, Rücknahme (Zeitpunkt, Name), Bericht. Der Bericht (enthält Namen) ist verschlüsselt gespeichert. Einsicht nur Administration und Schulleitung (Namen). Von der Quelldatei wird nur die Prüfsumme gespeichert [unklar: Quelle sagt nichts zur Aufbewahrung der hochgeladenen Datei selbst; Neubau-Festlegung: Datei nicht aufbewahren]. Aufbewahrung der Läufe: im Altbestand nicht geführt; Neubau: Datenart im Löschkonzept (Datei DAT) mit Altersfrist [unklar: Wert]. Freitexte importierter Inhalte sind verschlüsselt (Verschlüsselung ist der Engpass der Laufzeit, INT-070).
Abnahme: Direkter Tabellenzugriff zeigt für `report_enc` nur Chiffrat; Lehrkraft ruft `GET /import/fremd/runs` → 403; Lauf-Eintrag enthält nur die Prüfsumme, keinen Dateiinhalt; Löschlauf entfernt Läufe älter als die eingestellte Frist.

### 6.2 CSV-Import (Stammdaten)

**INT-052** · P1 · Status: Ist — **Datenarten und Dateiformat.** Datenarten (`what`): `teachers`, `classes`, `rooms`, `subjects`, `students`, `lessons`, `curricula`. Export und Vorlage: Semikolon als Trennzeichen, UTF-8 mit führendem BOM (Excel zeigt Umlaute richtig), Zeilenende CRLF, deutsche Spaltennamen. Import: Trennzeichen wird automatisch erkannt (mindestens Semikolon, Komma, Tabulator), BOM wird gelesen, Kopfzeile Pflicht. [unklar: erlaubte Eingabekodierungen außer UTF-8.] Die Feldliste je Datenart kommt aus `GET /import/csv/{what}/fields` (INT-006).
Abnahme: Export `students` und Import in leere Instanz → gleicher Bestand; Datei mit Komma als Trennzeichen wird erkannt; Datei ohne Kopfzeile → abgelehnt mit deutscher Meldung; Excel öffnet den Export ohne Umlautfehler.

**INT-053** · P1 · Status: Ist — **Zuordnungsdialog in festen Schritten.** (1) Datei wählen, (2) Trennzeichen automatisch erkannt, (3) Kopfzeile gelesen, Spalten den Feldern vorgeschlagen und änderbar; Voreinstellungen (Presets) `schild-nrw`, `asv`, `lusd`, `magellan`, sonst „eigenes Zuordnen“, (4) Vorschau mit Anzahl betroffener Datensätze und Problemen (INT-046), (5) „Übernehmen“ und Ergebnisbericht mit Zählwerten, Fehlern, Hinweisen; technische Schlüssel sind im Bericht ausgeblendet. Die Zuordnung (Spalte → Feld) wird als Abbildung `{"Spalte": "feld"}` übergeben.
Abnahme: Schüler-Datei im SchILD-NRW-Format mit Preset `schild-nrw` → alle Pflichtfelder vorbelegt; Spalte manuell umordnen ändert die Vorschau; Bericht zeigt keine internen Schlüssel.

**INT-054** · P1 · Status: Ist — **Besondere Zellformate.** Listen in einer Zelle werden nur an `,`, `;` und `|` getrennt. Wochenangaben: „1,3“, „1-4,9“ (Schulwochen 1 bis 52); Rhythmus: „jede 2. Woche“, „jede 3. Woche ab Woche 10 bis Woche 30“ (auch in der Stundenliste). Lehrkräfte: Spalte „Wunschklassen“ (kommagetrennt) und „Zeitfenster“ im Format `Mo-Fr 10:00-18:30 | Woche 2: Mi 08:00-12:00`; der Wert `ganztägig` löscht das Zeitfenster. Das Arbeitszeit-Raster einer Lehrkraft kennt die CSV nicht. Alte Einträge `week_pattern {every, from, to}` werden zu Rhythmus umgewandelt; beide Angaben zugleich → 422.
Abnahme: Zelle „jede 3. Woche ab Woche 10 bis Woche 30“ wird als Rhythmus gespeichert und beim Export identisch ausgegeben; Wochenangabe „60“ → Fehler mit Zeilennummer; Zeitfenster „ganztägig“ entfernt die Einschränkung.

**INT-055** · P1 · Status: Ist — **Regeln für Lehrkräfte- und Schüler-CSV** (Einrichtung: STA-073). Lehrkräfte: Kürzel, Name, Fächer, Deputat, E-Mail. Schüler/innen: Pflicht Klasse (muss vorher existieren), Nachname, Vorname; die Kennung stammt aus der Schülernummer, fehlt sie aus Name und Klasse; das Geburtsdatum nur ergänzen (INT-048). Kennungen sind je Sammlung eindeutig ohne Beachtung der Groß-/Kleinschreibung („MUE“ ≠ „mue“ ist ein Fehler); neue Kürzel ohne Leerzeichen; bestehende Kürzel mit Leerzeichen überstehen den Rundlauf. Die Schülerzahl einer Klasse wird aus der Liste berechnet. Der Import legt keine Konten an.
Abnahme: Zweites Kürzel „mue“ neben „MUE“ → Fehler mit Zeilennummer; neues Kürzel „Mü 1“ mit Leerzeichen → abgelehnt; vorhandenes Kürzel mit Leerzeichen übersteht Export und Re-Import.

**INT-056** · P0 · Status: offen — **Konfession/Religionsunterricht in Import und Export.** Die Zuordnung zur Religionskategorie ist eine besondere Kategorie personenbezogener Daten (Art. 9 DSGVO). Die Spalte ordnet beim Import in die Religions-Kopplung ein. Neubau: Spalte im Export nur auf ausdrückliche Auswahl und nur mit dem Recht für Schülerdaten; Zweck und Empfängerkreis stehen im Verzeichnis der Verarbeitungen; jeder Export und Import ist im Audit. [unklar: eigenes Recht für die Spalte; Quelle nennt keine eigene Schutzregel.]
Abnahme: Schüler-Export ohne gewählte Konfessionsspalte enthält sie nicht; Konto ohne Schülerdaten-Recht → 403; Audit-Eintrag je Export mit Format und Anzahl, ohne Werte.

### 6.3 Untis (GPU-/DIF-Textdateien)

**INT-057** · P1 · Status: Ist — **Untis-Import.** Eingabe: ZIP oder einzelne Dateien GPU001 bis GPU015 (ausgewertet: 001 bis 006, 010, 014, 015); Datensätze mit Text in Anführungszeichen, Datum JJJJMMTT; Kodierung wird erkannt (BOM, UTF-8, Windows-1252), Trennzeichen `,`, `;` oder Tabulator. Ohne vorhandene Schule als Basis entsteht eine neue Schule, mit Basis wird eingearbeitet; Modus `merge` (einarbeiten) oder `replace` (Bestand ersetzen). Probelauf `dry_run` (INT-046). Wochenangaben im Untis-Text („Woche 1“, „Woche 1, 3“, Blöcke als eigene Unterrichtsnummer mit „(Woche 1)“) werden in ein Wochenmuster umgewandelt. GPU014 (Vertretungen) wird zu Abwesenheit und Überschreibung (Kennung `untis-…`; ein erneuter Import ersetzt sie). Untis-Unterrichte ohne Entsprechung erhalten die Kurs-Kennung `U<Untis-Nr>` mit Herkunft „untis“. Nicht übernommen und im Probelauf als Sammelwarnung gemeldet: Verlegungen, Aufsichten, Klausuren, Sperrzeiten, Arbeitszeiten, Pausen, Stundentafeln, Termine, Jahrgang. GPU010 Feld 13 liefert das Geburtsdatum, GPU003 die Abteilung. Neue Stunden setzen ihren Planzeitraum oder lassen ihn leer (überall gültig).
Abnahme: Beispiel-Paket mit GPU001–006 im Probelauf → Zählwerte und Sammelwarnung, Datenbestand unverändert; Übernehmen → Stundenplan sichtbar; GPU010 mit Geburtsdatum → gespeichert; Konto ohne `timetable.edit` → 403.

**INT-058** · P0 · Status: Ist (Warnung bei abweichenden Schüler-Kennungen: offen) — **Schutz beim Ersetzen.** Der Probelauf von `replace` (Untis) und des JSON-Imports zeigt eine Vorher-Nachher-Tabelle je Bereich (Beispiel: „löscht 12 Ferien-Einträge, 4 Aufsichtsbereiche, 30 Klausuren“); die Bestätigung nennt diese Zahlen. Ein JSON-Dokument, dem Bereiche fehlen, wird ohne ausdrückliches „alles ersetzen“ abgelehnt; der Probelauf zeigt `would_delete`. `replace` behält die Webhook-Einstellungen, wenn das Paket keine enthält. Abweichende Schüler-Kennungen, die Konten von ihren Daten trennen würden, stehen als Warnung mit Namen im Probelauf.
Abnahme: Untis-Paket ohne Ferien im Modus `replace` → Probelauf nennt die Anzahl zu löschender Ferien; Bestätigungsdialog zeigt dieselbe Zahl; Teil-JSON ohne „alles ersetzen“ → abgelehnt; Webhook-Ziele nach `replace` unverändert.

**INT-059** · P1 · Status: offen — **Untis-Rundlauf ohne Verlust, stabile Stunden-Kennungen.** Fehler im Altbestand: Export und Re-Import verlieren Sperrzeiten, Arbeitszeiten, Pausen, Stundentafeln, Termine, Aufsichten. Nach einem Massenimport ändern sich Stunden-Kennungen, manuelle Überschreibungen verwaisen. Neubau: Der Rundlauf erhält diese Daten verlustfrei (technische Lösung dem Neubau überlassen) oder der Probelauf weist sie ausdrücklich als „nicht übernommen“ aus; Stunden-Kennungen bleiben stabil, solange der Block gleich bleibt, sonst melden Überschreibungen „Stunde findet nicht statt“ (Datei 02a, STP) und der Dialog warnt vor verwaisten Überschreibungen. Die Metadaten-Kennung in den Untis-Dateien ist eine Konstante (INT-008).
Abnahme: Plan mit Sperrzeit „Lehrkraft MUS Mittwoch ab 12:00“ und Pausenregel → Export Untis, Import in leere Instanz → Sperrzeit und Pause vorhanden; Plan mit 3 Überschreibungen, Re-Import desselben Pakets → keine Überschreibung trifft die falsche Stunde.

**INT-060** · P1 · Status: offen — **Feldzuordnungen der Untis-Dateien bestätigen.** Die Quellen nennen „8 Feldzuordnungen“, die nur ein echter Untis-Export bestätigen kann; der Betreiber muss den Export liefern. Das Altmodul markiert folgende Stellen als unsicher (9 Stellen, Zählweise zur Zahl 8 [unklar]): GPU001 Feld 8 und 9; GPU002 Zeilentext 1 und 2 (Feld 13 und 39); GPU002 Text (Feld 18); GPU002 Doppelstunden Minimum/Maximum (Feld 28 und 29); GPU004 Deputat (Feld 15); GPU014 Art-Bits (Bit n entspricht 2^n); GPU014 Feld 22; GPU014 „Stunde“ bei Pausenaufsichten (nach-Stunde plus 2); GPU015 insgesamt. Referenz war die MIT-lizenzierte Bibliothek `enbrea.untis.gpu` (Lizenzhinweis beibehalten, wenn Code übernommen wird). Bis zur Bestätigung zeigt der Import den Hinweis „Zuordnung noch nicht mit einer echten Untis-Datei bestätigt“; der Import bleibt ein optionaler Alternativweg (INT-001).
Abnahme: Mit einer echten, anonymisierten Untis-Exportdatei des Betreibers läuft ein Rundlauf-Test; jede der 9 Stellen hat einen Testfall; Hinweis im Probelauf verschwindet erst nach dessen Erfolg.

**INT-061** · P2 · Status: offen — **Weitere GPU-Dateien.** Reihenfolge: zuerst 013 (Abwesenheiten), 011 (Zeitraster), 017 (Prüfungen), 016 (Zeitwünsche); danach 007 bis 009, 012, 018 bis 021 (Auswertungsexporte ohne Stammdatenwert bleiben zurückgestellt); XML `untis.xml` fehlt. Begründung der Quelle: „Umzug von Untis ohne Datenverlust ist das stärkste Wechselargument“. Zusätzlich offen: ein Untis-Wechsel-Assistent (Import mit Prüfbericht „das hat Untis gekannt, das fehlt bei uns“, Zuordnung von Abwesenheitsgründen) – [unklar: Betreiber-Entscheidung, ob gewünscht; die Quelle nennt als Zweck den Verkauf an Untis-Schulen]. Roadmap: Datei 10.
Abnahme: Je neu unterstützter GPU-Datei ein Rundlauf-Test mit Beispieldatei; der Probelauf listet jede nicht übernommene Datei mit Namen.

### 6.4 JSON-Vollsicherung und Konfigurations-ZIP

**INT-062** · P1 · Status: Ist — **JSON-Vollsicherung des Planungsstands.** Export: Hülle `{format, format_version, version, exported_at, school}` mit Format-Kennung als Konstante (INT-008). Import akzeptiert die Hülle oder ein nacktes Schul-Objekt; Integritätsprüfung vor dem Schreiben; Modus `replace` prüft vorab und fragt bei Teil-Dokumenten (INT-058). Ein JSON-Import ersetzt im Altbestand auch die Webhook-Einstellungen (Fallstrick); Neubau-Festlegung: Webhook-Ziele und -Geheimnisse werden nur ersetzt, wenn die Bestätigung sie ausdrücklich nennt; Zugangsdaten und Geheimnisse sind nie Teil der Datei. Export als Klartext-Sicherung nur mit Recht (`timetable.edit` und `masterdata.edit`), gekennzeichnet und im Audit (STA-010).
Abnahme: Export und Re-Import in eine leere Instanz liefert denselben Plan; Datei enthält kein Passwort, keinen Token, kein Webhook-Geheimnis; Konto ohne die beiden Rechte → 403 beim Export; Teil-Dokument ohne „alles ersetzen“ → abgelehnt.

**INT-063** · P2 · Status: offen — **Konfigurations-ZIP („Schulvorlage übertragen“)**; fachliche Regeln in STA-076, hier die Schnittstelle. `GET /config/export.zip?bereiche=…&personen=0|1`: ZIP mit `manifest.json`, `LIESMICH.txt`, je Bereich eine Excel-taugliche CSV (Standorte, Fächer, Räume, Bildungsgänge, Klassen, Klassengruppen, Abteilungen, Lehrkräfte [Verfügbarkeit als lesbarer Text], Schüler/innen mit Erziehungsberechtigten [nur mit Recht], Stundentafeln, Kopplungen, Ferien, Aufsichtsbereiche) und `einstellungen.json`. `personen=0` liefert eine Vorlage ohne Namen, E-Mail-Adressen und Geburtsdaten. `POST /config/import` (ZIP oder einzelne CSV): Probelauf je Bereich (neu, geändert, unverändert, würde gelöscht, Fehler mit Zeilennummer), feste Reihenfolge, ganz oder gar nicht, eine Version im Verlauf. `GET /config/template/{bereich}.csv` liefert die leere Vorlage mit Beispielzeile. Jeder Stammdaten-Reiter bietet „Als Datei“ und „Aus Datei“; Import/Export bietet „Konfiguration übertragen“ (Datei wählen, Unterschiede ansehen, Übernehmen). Alle Grenzen und Schutzregeln aus INT-050 gelten.
Abnahme: Rundlauf mit der Beispielschule Berufskolleg (Testdatei): Export, leere Instanz, Import → identischer Bestand; Export mit `personen=0`: Stichprobe auf Namen, E-Mails, Geburtsdaten findet nichts; Konto ohne Recht → 403; Archiv mit Pfad `../x` → abgelehnt.

### 6.5 Fremdsysteme (Import aus anderen Systemen)

**INT-064** · P1 · Status: Ist — **Ablauf und Schnittstelle.** Zweck: Bestand aus Moodle und gängigen Schulsystemen übernehmen (Personen, Klassen, Fächer, Räume, Stundenpläne, Kurse, Gruppen, Aufgaben, Abgaben, Noten, Fragen, Kompetenzen, Abzeichen, Forum, Dateien). Ablauf: System wählen oder automatisch erkennen lassen, Dateien hochladen (mehrteilig, `files[]`), Vorschau, Entscheidungen übernehmen, Lauf ausführen, optional Rückgängig. Schnittstellen: `GET /import/fremd/systems` (Systeme, Dateiendungen, Datenarten, Optionen), `POST /import/fremd/preview`, `POST /import/fremd/run`, `GET /import/fremd/runs`, `GET /import/fremd/runs/{run_id}`, `POST /import/fremd/runs/{run_id}/undo`. Systemkennungen: `auto`, `moodle-db`, `moodle-mbz`, `oneroster`, `webuntis`, `csv`. Empfohlene Reihenfolge der Einrichtung: (1) Stammdaten (OneRoster, WebUntis oder Liste), (2) Konten und Zugangsbriefe (außerhalb des Imports), (3) Moodle-Import, (4) Entscheidungen aus der Vorschau übernehmen und erneut importieren; jeder Lauf ist idempotent und ergänzt, was vorher mangels Konto fehlte.

| Option (alle optional) | Wirkung |
|---|---|
| `instance` | Name der Quellinstanz; trennt zwei Moodle-Systeme |
| `create_missing_students`, `create_missing_teachers` | Personen ohne Treffer neu anlegen (keine Konten) |
| `default_class` | Standardklasse; bei WebUntis nötig |
| `course_map` | je Quellkurs `KURS#TEIL` (Kurs und Teil), `neu` oder `ueberspringen` |
| `person_map` | Entscheidung für mehrdeutige Personen |
| `include_hidden_courses` | auch versteckte Kurse |
| `publish` | Standard aus: Aufgaben versteckt, Selbsttests als Entwurf |
| `parts` | Teilmenge aus `personen`, `kursraeume`, `gruppen`, `aufgaben`, `noten`, `fragen`, `kompetenzen`, `abzeichen`, `forum`, `dateien` |
| `only_courses` | nur ausgewählte Kurse |
| `update_existing` | bestehende Datensätze aktualisieren |
| `preset` | `schild-nrw`, `asv`, `lusd`, `magellan` (Personenlisten) |
| `prefix` | Präfix für Kennungen, Beispiel `mdl_` |

Abnahme: Vorschau mit der Moodle-Beispieldatei → Bericht mit Zählwerten, Bestand unverändert; Lauf → Bericht mit `run_id`; zweiter Lauf → alles „unverändert“; Systemkennung `auto` erkennt das Format; nicht erkennbares Format → verständliche Meldung statt Serverfehler; nur `parts=["personen"]` → keine Kursräume angelegt.

**INT-065** · P1 · Status: Ist — **Datenart-Matrix (ja = unterstützt und getestet, teil = eingeschränkt, – = nicht).** Neue Quellsysteme werden gegen diese Matrix ergänzt, nie stillschweigend.

| Datenart | Moodle-Datenbank | Moodle-Sicherung | OneRoster 1.2 | WebUntis | Personenliste | Untis-GPU |
|---|---|---|---|---|---|---|
| Personen (Zuordnung, Neuanlage) | ja | ja | ja | ja (ohne Klasse) | ja | ja |
| Klassen | nur Hinweis | nur Hinweis | ja (Stammklasse) | ja | ja (aus Spalte) | ja |
| Fächer, Räume | – | – | – | ja | – | ja |
| Stundenplan | – | – | – | – (Zeitraster ignoriert) | – | ja |
| Kurse zu Kursräumen | ja | ja | ja (`scheduled`) | – | – | – |
| Einschreibungen, Mitglieder | ja | ja | ja | – | – | teil (Kurswahlen) |
| Gruppen | ja | – | – | – | – | – |
| Aufgaben, Abgaben, Bewertung | ja | teil (nur Textabgaben) | – | – | – | – |
| Bewertungsraster | ja | – | – | – | – | – |
| Notenbuch-Einträge (manuell, Skala, Quiz, Aufgaben) | ja | – | ja (`lineItems`, `results`) | – | – | – |
| Fragen und Selbsttests (6 Typen) | ja | – | – | – | – | – |
| Kompetenzen, Abzeichen | ja | – | – | – | – | – |
| Forum → Pinnwand | ja | – | – | – | – | – |
| Dateien | nur Platzhalter (Metadaten) | ja, mit Inhalt | – | – | – | – |
| Trockenlauf, Idempotenz, Rückgängig, Protokoll | ja | ja | ja | ja | ja | nur Trockenlauf |

Abnahme: Je belegter Zelle „ja“ ein Rundlauf-Test mit der erfundenen Beispieldatei; Zelle „–“ → der Bericht nennt die Datenart unter „nicht übernommen“; Beispieldateien enthalten nur erfundene Personen.

**INT-066** · P0 · Status: Ist — **Personen-Zuordnung und Konfliktbericht.** Reihenfolge der Zuordnung: Kennung, E-Mail, Name mit Geburtsdatum. Namensvergleich normalisiert (Groß-/Kleinschreibung, Zeichen, Namensteile, Namenszusätze); Klassenstufe aus dem Klassennamen ableitbar. Namensvettern mit anderem Geburtsdatum werden nie zusammengelegt; unklare Fälle stehen im Konfliktbericht. Der Bericht (Vorschau und Lauf) enthält: `counts` (je Art `created`, `updated`, `unchanged`, `skipped`), `persons` (Zuordnungswege; Listen `unmatched`, `ambiguous`, `conflicts`, `unsure`), `courses` (Zuordnung je Quellkurs), `needs_decision` (Kurse ohne Zuordnung, mehrdeutige Personen; Antwort als `course_map` bzw. `person_map`), `waiting_for_accounts`, `problems` (höchstens 400, mit `problem_kinds`), `notes`, `lines` (fertige deutsche Zusammenfassung), `run_id`. Fehlerhafte Zeilen werden gemeldet, der Lauf bricht nicht ab.
Abnahme: Zwei Schüler/innen mit gleichem Vor- und Nachnamen, Geburtsdatum 01.02.2010 und 03.04.2011 → zwei Personen, kein Zusammenlegen; gleiche Namen ohne Geburtsdatum → Eintrag in `ambiguous` und `needs_decision`; Antwort per `person_map` → zweiter Lauf ordnet zu; Quelle mit 450 fehlerhaften Zeilen → Lauf läuft durch, `problems` enthält höchstens 400 Einträge.

**INT-067** · P1 · Status: Ist — **Konten und Sichtbarkeit.** Der Importer legt keine Konten an. Personen ohne Konto werden als „wartet auf Konto“ gezählt und beim nächsten Lauf ergänzt (Mitgliedschaften, Gruppen und Abgaben hängen an Konten). Alles Importierte ist zunächst versteckt bzw. Entwurf (`publish` aus), damit Lehrkräfte vor der Freigabe prüfen.
Abnahme: Import mit 10 Personen ohne Konto → Bericht „10 warten auf Konto“, keine Konten neu; nach Anlage der Konten zweiter Lauf → Mitgliedschaften und Abgaben vorhanden; importierte Aufgabe für Schüler/innen nicht sichtbar, bis die Lehrkraft sie freigibt.

**INT-068** · P2 · Status: Ist — **Bekannte Grenzen der Moodle-Übernahme** (im Bericht benannt; Erklärung im Hilfe-Symbol):

| Gegenstand | Verhalten |
|---|---|
| Abgaben | nur die jeweils letzte; Entwürfe übersprungen |
| Gruppen | überlappende Mitglieder innerhalb einer Einteilung nicht doppelt geführt |
| Notenbuch-Überschreibungen (`overridden`) | nicht gesondert behandelt |
| Mehrfachauswahl mit Strafpunkten (negative Brüche) | Strafpunkte gehen verloren |
| Fragetypen | unterstützt: Einfachauswahl, Mehrfachauswahl, Richtig/Falsch, Kurzantwort, Numerisch, Zuordnung; andere (Essay, Lückentext, berechnete Fragen) gemeldet und übersprungen |
| Kompetenzrahmen | nur beim ersten Lauf angelegt; später neue Kompetenzen kommen nicht nach |
| Notenbuch-Quellen | nur für Kurse, die einem Kursteil zugeordnet sind (eigene Kursräume haben kein Notenbuch) |
| Textinhalte | HTML wird in Markdown umgewandelt; Zeitangaben als Unix-Zeit und ISO gelesen; deutsche Notenwörter als Noten erkannt |
| Datenbank-Abzug | nur SQLite-Datei; MySQL-/PostgreSQL-Abzüge nicht direkt lesbar; Schema aus Entwicklungszweig, nicht gegen eine echte Sicherung geprüft |
| Kurssicherung | `.mbz` (gzip-TAR oder ZIP); Leser tolerant gebaut; nicht an einer echten Sicherung getestet |
| Beschädigte Datei | Bericht mit Problem, kein Serverfehler |

Abnahme: Beispiel mit Essay-Frage, Entwurf-Abgabe und Mehrfachauswahl mit negativem Bruch → Bericht listet die Frage als übersprungen, die Entwurf-Abgabe fehlt, Hinweis zu Strafpunkten; beschädigte SQLite-Datei → Bericht mit Problem „Datei nicht lesbar“, kein Serverfehler (kein 5xx).

**INT-069** · P1 · Status: Ist (Warnung bei aufeinander aufbauenden Läufen: offen) — **Rückgängig eines Fremdsystem-Laufs.** Entfernt nur das vom Lauf Neuangelegte (anhand der Verknüpfungen); Geändertes bleibt. Immer den jüngsten Lauf zuerst zurücknehmen; Status danach `zurueckgenommen`, mit Zeitpunkt und Name. Lücke im Altbestand: Wer einen älteren Lauf zurücknimmt, nachdem ein jüngerer darauf aufbaut, bekommt keine Warnung. Neubau: Rücknahme eines älteren Laufs wird mit Warnung und Bestätigung verlangt oder gesperrt, solange ein jüngerer Lauf darauf aufbaut.
Abnahme: Lauf 1 und Lauf 2 (baut auf 1 auf); Rückgängig von Lauf 1 → Warnung bzw. Sperre mit Verweis auf Lauf 2; Rückgängig von Lauf 2 → neu angelegte Objekte entfernt, geänderte unverändert; Audit-Eintrag ohne Inhalte; Lehrkraft → 403.

**INT-070** · P2 · Status: Ist — **Leistung und Tests.** Referenzlast: 1.500 Schüler/innen, 96 Kurse, 192 Aufgaben, 6.787 Abgaben, 198 Notenspalten. Messwerte des Altbestands (Laptop, SQLite, ein Prozess): Moodle-Abzug (3,4 MB) lesen 0,6 s; Vorschau (alles zurückgerollt) 6,2 s; echter Import mit Verschlüsselung 6,2 s; zweiter Lauf (alles unverändert) 2,0 s; OneRoster (1.505 Personen, 607 KB) lesen 0,04 s, zuordnen 0,2 s; Personenliste mit 1.500 Schüler/innen neu anlegen 0,3 s, zweiter Lauf 0,1 s. Engpass ist die Verschlüsselung der Freitexte, nicht die Datenbank. Automatische Tests (Altbestand 52): Rundlauf, Zuordnung, Umlaute, Idempotenz, Änderung, Fehler, Rückgängig, Konten-Reihenfolge, Entscheidungen, Stammdatenformate, Rechte und Schnittstelle, Großläufe; Testdaten nur mit erfundenen Personen.
Abnahme: Lauf mit der Referenzlast endet fehlerfrei; die Zeiten stehen im Prüfbericht neben den Altwerten (Abweichung wird begründet); alle genannten Testgruppen existieren und sind grün.

**INT-071** · P1 · Status: offen — **Oberfläche für Zuordnung und Entscheidungen.** Im Altbestand gibt es für Fremdsystem-Importe keine eigene Oberfläche; die Funktionen sind für den Einrichtungsassistenten gedacht. Neubau: Assistent für Systemwahl, Upload, Vorschau, Zuordnung von Spalten, Kursen und Personen, Konfliktlösung mit Gegenüberstellung, Namensvettern über das Geburtsdatum, Auswahl „immer so zuordnen“ (Entscheidung als Verknüpfung speichern; das Rückgrat dafür besteht), Lauf, Protokollliste mit Details und Rückgängig. Anrede „Sie“, Erklärungen nur im Hilfe-Symbol, Import bleibt nur Alternative (INT-001). Roadmap: Datei 10.
Abnahme: Ein mehrdeutiger Schüler erscheint im Assistenten mit beiden Kandidaten nebeneinander; Auswahl „immer so zuordnen“ wirkt beim nächsten Lauf ohne erneute Frage; ohne Importrecht ist der Assistent nicht erreichbar (403).

**INT-072** · P2 · Status: offen — **Hintergrundlauf für große Importe.** Große Schulen erreichen Uploads bis rund 50 MB und mehrere Minuten Laufzeit; ab etwa 20.000 Abgaben läuft der Import als Hintergrundjob mit Fortschrittsanzeige, die Datei wird zwischengespeichert (verschlüsselt, nach Lauf oder Frist gelöscht), Vorschau und Lauf nutzen einen Upload. Das Konto kann den Fortschritt ansehen und den Job abbrechen; Ergebnis steht im Importprotokoll.
Abnahme: Import mit 25.000 Abgaben → Antwort sofort mit Job-Kennung, Fortschritt sichtbar, Ergebnis im Protokoll; Abbruch lässt keinen halben Zustand zurück (Lauf `fehler` bzw. zurückgerollt); Job eines anderen Kontos → 404.

**INT-073** · P2 · Status: offen — **Moodle über den Webservice statt Datenbank-Abzug.** Empfohlener Hauptweg: Kurse, Abgaben, eingeschriebene Personen und Notenübersicht über die offizielle Schnittstelle, Dateien über den Dateiendpunkt; funktioniert bei MySQL, PostgreSQL und gehosteten Systemen. Die Leser für Abzüge bleiben. Das Zugangsgeheimnis des Moodle-Betreibers wird verschlüsselt gespeichert und nie wieder angezeigt, das Ziel läuft durch die Zielprüfung (Abschnitt 9). Später: Moodle-Sicherung als Weg für Lehrkräfte („Mein Kurs“) mit eigenem Rechtekonzept; Dateien aus dem Moodle-Datenordner über Pfad. [unklar: Betreiber-Freigabe.]
Abnahme: Import gegen eine Test-Moodle-Instanz auf PostgreSQL liefert denselben Bericht wie der Abzug-Weg; Ziel `127.0.0.1` → von der Zielprüfung abgelehnt; Geheimnis erscheint in keiner Antwort und keinem Protokoll.

**INT-074** · P3 · Status: offen — **Nicht belegte Quellsysteme.** IServ, Schulmanager Online (als Importquelle), SVWS-Datenbankauszug, itslearning und Google Classroom haben kein belegtes Importformat; für IServ und Schulmanager Online besteht nur eine tolerante Spaltenerkennung der Personenlisten; SchILD-/ASV-Voreinstellungen stammen aus dem bestehenden Bestand ohne öffentliche Spezifikation; WebUntis-Feldnamen stammen aus einer Drittbibliothek. Betreiber-Wunsch: „Mir fehlen noch ein paar so Niche Datenbanken.“ (10-16). Regel für den Neubau: Kein Importformat ohne Beleg (offizielle Beschreibung oder echte, anonymisierte Beispieldatei einer Schule, INT-007).
Abnahme: Für jedes neu aufgenommene Quellsystem liegt eine Beispieldatei im Repository und ein Rundlauf-Test; ohne Beleg erscheint das System in `GET /import/fremd/systems` nicht als „unterstützt“.

### 6.6 Ferien, Feiertage und Importe der Fachbereiche

**INT-075** · P1 · Status: Ist — **Ferien- und Feiertagsimport** (fachlich STA-057; hier die Anbindung). Rechte: alle Routen `masterdata.edit`. Schnittstellen: `GET`/`PUT /holiday-import` (Einstellungen: Land, Region, Sprache, automatische Übernahme), `GET /holiday-import/countries`, `GET /holiday-import/regions`, `POST /holiday-import/preview`, `POST /holiday-import/apply`. Quellen: OpenHolidays (Hauptquelle, Länder und Regionen), Nager.Date (Rückfall, nur gesetzliche Feiertage, ohne Regionen). Die Codes für Land, Region und Sprache werden formal geprüft. Die Anfrage enthält nur Land-, Regions- und Sprachcode und den Zeitraum, keine Personendaten; die Anfragekennung trägt den Produktnamen aus der zentralen Konfiguration (INT-008). Ablauf: Einstellungen speichern, Vorschau je Eintrag mit Aktion (neu, geändert, schon vorhanden, von Hand geändert), Übernehmen; danach automatische Aktualisierung täglich für das aktuelle und das nächste Schuljahr, nach einem Fehler früher erneute Versuche, erster Abruf nach dem Start verzögert, Antworten zwischengespeichert [unklar: Zahlenwerte von Verzögerung, Wiederholzeit und Zwischenspeicher]. Von Hand angelegte, geänderte oder gelöschte Einträge werden nie überschrieben oder zurückgeholt, nichts wird automatisch gelöscht. Importierte Einträge tragen Herkunft und Signatur. `SM_HOLIDAY_IMPORT` = 0 schaltet den Import schulweit ab (Standard an). Zielprüfung und Zeitlimit nach Abschnitt 9. Im Demo-Betrieb gesperrt.
Abnahme: Vorschau für NRW → Liste mit Aktionen, Daten unverändert; „Übernehmen“ legt Einträge an; Eintrag von Hand umbenennen, erneut übernehmen → Name bleibt; Hauptquelle ausgefallen → Rückfall liefert gesetzliche Feiertage; Konto ohne `masterdata.edit` → 403; mitgeschnittene Anfrage enthält keinen Personenbezug; `SM_HOLIDAY_IMPORT=0` → kein ausgehender Abruf.

**INT-076** · P2 · Status: Ist — **Importe der Fachbereiche (Verweisregister).** Diese Importe folgen den Regeln 6.1 (Rechte, Vorschau, Grenzen, Audit, Demo-Sperre), ihre Fachregeln stehen in den genannten Dateien.

| Import | Format | Recht | Fachregel |
|---|---|---|---|
| Kompetenzrahmen | JSON (Export = Import); CSV mit Kopf `Bereich;Kompetenz;Kürzel;Stufe 1;Stufe 2 …` und Trenner `;`, `,` oder Tabulator | `competency.manage` | NOT-034 |
| Fragen für Selbsttests | GIFT-Datei (Zahl-Fragen mit Toleranz) | Lehrende des Kursraums | KUR-067 |
| Moodle-Inhalte und -Notenbuch | Abschnitt 6.5 | Fremdimport-Recht | INT-064 |

Abnahme: Rahmen als JSON exportieren und in leere Instanz importieren → identische Struktur; CSV mit Zeile ohne Kompetenz → abgelehnt mit Zeilennummer; GIFT-Datei mit Zahl-Frage und Toleranz → Toleranz übernommen; der Kompetenz-Import ist in der Demo gesperrt (INT-005).

## 7. Exporte

### 7.1 Gemeinsame Regeln für alle Exporte

**INT-077** · P0 · Status: offen (Ist: JSON, Untis und Schulmanager-Online-Paket nur mit Anmeldung, Stammdaten-Exporte ohne Protokoll, Zuschauer-Konto hatte Zugriff) — **Exportrechte, Umfang und Audit.** Jeder Export (alle Formate) prüft serverseitig ein Recht, liefert nur den Umfang, den das Konto auch in der Oberfläche sehen darf (ein zentrales Feldregelwerk, SIC-027), schließt das Zuschauer-/Ansichtskonto aus und steht im Audit (Konto, Format, Umfang bzw. Anzahl, Filter; keine Inhalte; SIC-028). Ein Vollexport als Klartext-Sicherung ist gekennzeichnet (STA-010). Spannung zwischen Wunsch und Schutz (Hinweis 10-17): Der Wunsch „alle Rollen alle Rechte“ steht gegen die Lücke, dass das Zuschauer-Konto exportieren konnte; maßgeblich ist der Schutz (Zuschauer ausgeschlossen).

| Export | Route | Recht im Neubau | Altbestand |
|---|---|---|---|
| CSV je Datenart | `GET /export/csv/{what}` | Schüler-Daten `students.read`, sonst `masterdata.edit` oder `timetable.edit` je Datenart; Geburtsdatum nur mit `students.birth_date` | angemeldet plus Recht je Art |
| JSON-Vollsicherung | `GET /export/json` | `timetable.edit` und `masterdata.edit`; Schülerdaten zusätzlich `students.read` | nur angemeldet |
| Untis-ZIP | `GET /export/untis.zip` | wie JSON | nur angemeldet |
| Schulmanager-Online-Paket | `GET /export/schulmanager-online.zip` | wie JSON | nur angemeldet |
| OneRoster-ZIP | `GET /export/oneroster.zip` | `students.read` | `students.read` |
| Konfigurations-ZIP | `GET /config/export.zip` | [unklar: Recht] | nicht gebaut |

Abnahme: Zuschauer-Konto und Konto ohne `students.read` → 403 auf jeder Routenzeile der Tabelle; Lehrkraft ohne `timetable.edit` ruft `GET /export/untis.zip` → 403; je erfolgreichem Export genau ein Audit-Eintrag mit Format und Anzahl, ohne Dateiinhalt; CSV-Export `students` ohne `students.birth_date` enthält keine Geburtsdatums-Spalte.

**INT-078** · P0 · Status: offen (Ist: Schutzfunktion vorhanden, in fünf Exporten nicht genutzt: Beobachtungsprotokoll, API-Protokoll, Kompetenzen, Stammdaten-Export, OneRoster; geschützt sind Noten-, Formular- und Umfrage-Exporte) — **Entschärfung von Tabellenzellen (CSV-Formelschutz, SIC-069).** Eine zentrale Funktion wird von jedem CSV-/Tabellen-Export genutzt. Zellen in Text-, Namens- und Freitextspalten, die mit `=`, `+`, `-` oder `@` beginnen (auch nach Leerraum oder Tabulator), erhalten ein vorangestelltes Hochkomma; Zahlen- und Notenspalten (z. B. Note „2+“) werden als Zahl bzw. Note erzeugt und bleiben unverändert. [unklar: Behandlung von Werten wie „-2“ in Textspalten; der Sicherheitstest verlangt dort Neutralisierung.] Ein Registry-Test (SIC-005) scheitert, wenn ein Export die Funktion nicht nutzt.
Abnahme: Die Werte `=1+1`, `+SUMME(A1)`, `-2`, `@x` in Namens- und Freitextfeldern erscheinen in jedem CSV-Export als `'=1+1`, `'+SUMME(A1)`, `'-2`, `'@x`; ein neuer Export ohne die Funktion lässt den Registry-Test scheitern; Note „2+“ im Noten-Export bleibt „2+“.

**INT-079** · P1 · Status: Ist — **Einheitliche Dateiformate.** CSV: Semikolon als Trennzeichen, UTF-8 mit führendem BOM, Zeilenende CRLF, deutsche Spaltennamen; Datum `TT.MM.JJJJ`, Dezimalkomma in Noten; Listen in einer Zelle mit `,`, `;` oder `|`. ZIP-Exporte enthalten eine `LIESMICH.txt` (Produktname aus der zentralen Konfiguration, INT-008) und, wo ein Empfänger sie braucht, eine `manifest.json`. JSON: UTF-8, Format-Kennung als Konstante. Alle Exporte werden erzeugt und ausgeliefert, nicht gespeichert.
Abnahme: CSV-Export in Excel (deutsche Einstellung) öffnet ohne Umlautfehler und mit Spalten in getrennten Zellen; ZIP enthält `LIESMICH.txt` mit dem aktuell konfigurierten Produktnamen; nach dem Abruf liegt keine Exportdatei auf dem Server.

**INT-080** · P0 · Status: offen — **Exporte und Auskünfte nur ausdrücklich freigegeben für Zugänge und Tokens (Allowlist statt Sperrliste, SIC-004).** Zugänge „Lesen und schreiben“ und persönliche Tokens erreichen schreibende und exportierende Routen nur über eine ausdrückliche Freigabeliste; neue Routen sind gesperrt, bis sie freigegeben sind. Altbestand: Sperrliste (lückenhaft). Im Neubau steht keine Export- oder Auskunftsroute auf der Freigabeliste für Zugänge mit Umfang; für persönliche Tokens gelten die Rechte des Kontos, Export- und Auskunftswege verlangen zusätzlich die Sitzung [unklar: Quelle fordert „Allowlist für Export- und Auskunftswege“; Betreiber hat nicht entschieden, ob Exporte per persönlichem Token erlaubt sein sollen]. Gilt zusammen mit INT-023 und INT-025.
Abnahme: Zugang „Lesen und schreiben“ ruft `GET /export/json` → 403; Zugang ruft `GET /me/export` → 403; eine neu hinzugefügte, nicht freigegebene Schreibroute → 403 mit Token (der Registry-Test scheitert, wenn eine Route weder freigegeben noch ausdrücklich gesperrt ist); dieselben Routen mit Sitzung → laut Recht erlaubt.

### 7.2 Stundenplan-, Stammdaten- und Austauschpakete

**INT-081** · P1 · Status: Ist — **Stammdaten-CSV-Export.** Vor dem Export wählt die Person die Datenart(en): `teachers`, `classes`, `rooms`, `subjects`, `students`, `lessons`, `curricula`. Spaltenformate wie beim Import (INT-054), damit der Rundlauf gelingt: Wochenlisten, Regeln und Zeitfenster als Text je Zelle. Gesundheits- und Abwesenheitsgründe sind nie enthalten (INT-004). Geburtsdatum nur mit `students.birth_date`; die Religionsspalte nur nach INT-056. Rechte und Audit nach INT-077, Formelschutz nach INT-078.
Abnahme: Export `lessons` → Re-Import in leere Instanz ergibt dieselben Stunden samt Rhythmus „jede 3. Woche ab Woche 10“; Export `teachers` enthält keinen Abwesenheitsgrund; Export ohne gewählte Datenart → abgelehnt mit deutscher Meldung.

**INT-082** · P1 · Status: Ist — **Untis-Export (GPU-ZIP).** Enthält GPU001 (Stundenplan), GPU002 (Unterricht), GPU003 (Klassen), GPU004 (Lehrkräfte), GPU005 (Räume), GPU006 (Fächer), GPU010 (Schüler/innen) und GPU014 (Vertretungen; nur Export, mit übergebenen Tagesplänen). Kodierung Windows-1252 mit Umschrift nicht darstellbarer Zeichen (ğ→g, ı→i); Text in Anführungszeichen, Datum JJJJMMTT. Doppelstunden-Kennzeichen wird geschrieben. Eine Metadaten-Kennung in GPU002 Feld 39 (`sm1;c=…;p=…`) hilft dem Rundlauf und ist abschaltbar. Standard **ohne Abwesenheitsgründe**; Gründe nur auf ausdrückliches Verlangen; Option „Schülerdaten weglassen“ lässt GPU010 weg. Vorgangsarten der Vertretungen: Entfall, Betreuung, Sondereinsatz, Wegverlegung, Freisetzung, Plus, Teilvertretung, Hinverlegung, Raumvertretung, Pausenaufsicht, Unterrichtsfrei; die Zuordnung der Eintragsarten steht an genau einer Stelle (VER-037). [unklar: Inhalt der Symboltabelle.] Rechte nach INT-077.
Abnahme: Export enthält GPU001–006, 010, 014; mit Option „Schülerdaten weglassen“ fehlt GPU010; Standardexport mit Lehrkraft-Abwesenheit „krank“ enthält den Grund nirgends (Volltextsuche); Umlaute (ä, ö, ü, ß) kommen im Untis-Import korrekt an; bei abgeschalteter Metadaten-Kennung fehlt sie in GPU002.

**INT-083** · P2 · Status: Ist — **Schulmanager-Online-Paket (reiner Export).** ZIP mit `LIESMICH.txt` (Importanleitung für den Empfänger), `manifest.json`, `untis/GPU*.TXT` und `csv/{schueler,lehrer,klassen,raeume,faecher,unterricht}.csv`. Dateibasiert, keine öffentliche Schnittstelle des Empfängers. Das Importformat von Schulmanager Online selbst ist nicht belegt (INT-074); das Paket erhebt keinen Anspruch auf Importierbarkeit [unklar: Bestätigung durch den Empfänger]. Datenminimierung und Rechte wie Untis-Export.
Abnahme: Paket enthält genau die genannten Dateien; `LIESMICH.txt` nennt den konfigurierten Produktnamen; Konto ohne Recht → 403; Audit-Eintrag je Export.

**INT-084** · P1 · Status: Ist — **OneRoster-Export (Stammdaten, ohne Noten).** `GET /export/oneroster.zip` liefert Stammdaten als OneRoster-1.2-CSV-Bündel (Gegenrichtung zum Import) [unklar: genauer Dateiumfang; mindestens Organisationen, Benutzer, Klassen, Kurse, Einschreibungen, Schuljahre]. Recht `students.read` im Umfang der Sicht; Formelschutz INT-078; Audit INT-077. OneRoster ist der bevorzugte Standardweg (INT-007); Ausbau: Noten (`lineItems`, `results`) und REST-Lesezugriff (INT-101).
Abnahme: Export einer Schule mit 3 Klassen und 60 Schüler/innen → Bündel importierbar durch den eigenen OneRoster-Import in leere Instanz ohne Verlust (Rundlauf); Konto ohne `students.read` → 403; Zeile mit Namen „=1+1“ erscheint als `'=1+1`.

**INT-085** · P1 · Status: offen (Ist: Feed je Konto, Token nur als HMAC; offen: Feed je Kind, Elternzugriff nach Volljährigkeit, Entscheidung zum Token im Pfad) — **Kalender-Abo (iCal).** Fachregeln STP-097, ANM-123, SIC-063; hier die Schnittstelle. Persönlicher Feed `GET /ical/{token}.ics` (ohne Anmeldung, nur mit Token im Pfad, weil Kalenderprogramme keine Kopfzeilen senden), Parameter `student` (Kind wählen) und `days` (Zeitraum; Beispielwert der Quelle 21, Höchstwert 800 Tage). Zusätzlich Kalenderdatei je Art und Referenz (Klasse, Lehrkraft, Raum, Schüler/in) für einen Zeitraum. Inhalt: Stunden, Termine, Ferien (ganztägig), Vertretungen: ersetzte Stunde als `CANCELLED` mit „Vertreten“, die Vertretung als eigener Termin; Verlegung: alter Platz `CANCELLED`, neuer Termin „Verlegt“; Termine tragen „Woche n“. Format RFC 5545, Zeitzone Europe/Berlin, Text maskiert, lange Zeilen gefaltet. Nie enthalten: Abwesenheitsgründe, Gesundheits- oder Namensdaten Dritter (INT-004). Token: nur als HMAC gespeichert, Klartext einmalig bei Erzeugung, Neuerzeugung entwertet den alten Link (alter Link → 404), im Zugriffsprotokoll maskiert (`/ical/***`); Token mindestens 32 Zufallsbytes [unklar: Token im Pfad gegenüber Kopfzeile und Rotation – Prüfung offen, weil Kalenderprogramme keine Kopfzeilen senden]; das allgemeine Ratenlimit zählt `/ical/` (SIC-095). Neubau: je Kind ein Feed (Eltern mit zwei Kindern erhalten zwei), kein Feed für Eltern volljähriger Kinder ohne Freigabe, die Erzeugung des Links setzt die Einwilligung voraus (REH).
Abnahme: Vertretung → Feed zeigt die ersetzte Stunde als `CANCELLED` und die Vertretung als eigenen Termin; Feed enthält kein Wort des Abwesenheitsgrundes; `days=801` → auf 800 Tage begrenzt oder abgelehnt [unklar: Verhalten über dem Höchstwert]; Link neu erzeugen → alter Link 404; Elternkonto mit zwei Kindern → zwei Feeds; Kind wird 18, keine Freigabe → Eltern-Feed leer bzw. 404; Datenbank enthält nur den Hash.

### 7.3 Übergabe an Zielsoftware, Fachexporte, Auskunft

**INT-086** · P1 · Status: Ist (ENM/SVWS, Fehlzeiten-Export, weitere Länder: offen) — **Übergabe von Noten, Fehlzeiten und Zeugnisdaten.** Das System druckt keine Zeugnisse (NOT-028); es liefert Daten an die Zielsoftware der Schule. Betreiber-Linie: Zeugnisse bleiben in SchILD-NRW/SVWS bzw. ASV.

| Übergabe | Format und Weg | Recht | Verweis | Status |
|---|---|---|---|---|
| Endnoten Halbjahr | CSV für SchILD-NRW/SVWS (`schild`), ASV (`asv`), LUSD (`lusd`); `GET /gradebook/export` mit Halbjahr, Format, optional Klasse, `include_open` (Schulleitung); Semikolon, UTF-8 mit BOM, CRLF, Datum TT.MM.JJJJ, Dezimalkomma; nur festgelegte Endnoten aus gesperrten Notenbüchern | `gradebook.export` (Schulleitung, Sekretariat) oder `gradebook.manage` | NOT-026 | Ist |
| Noten, Fehlstunden, Bemerkungen im ENM-/SVWS-Format | Rundlauf-Test gegen die öffentliche Formatbeschreibung [unklar: Verfügbarkeit nicht belegt] | wie oben | NOT-030 | offen |
| Fehlzeiten je Halbjahr | CSV (entschuldigt, unentschuldigt, offen, Verspätungen je Kind) | [unklar: Recht; Umfang der Sicht der Klassenleitung bzw. Schulleitung, KLB-050] | KLB-050 | offen |
| Landes-Exporte weiterer Länder (ASV BY, LUSD HE, SchILD/LUPO NRW) inkl. Fehlzeiten | je Land | wie oben | NOT-030 | offen; Betreiberentscheidung, welche Länder zuerst |
| Kopfnoten | Übernahme in den Export nach Abstimmungs-Workflow | wie Noten | NOT-029 | offen |

Die Spalten der drei CSV-Formate sind im Altbestand nur gegen Importvorlagen, nicht gegen amtliche Spezifikationen geprüft; die Oberfläche weist darauf hin („Zuordnung in der Zielsoftware einmalig prüfen“). Jeder Export steht im Audit (Person, Zeit, Format, Halbjahr, Zeilenzahl; keine Noten).
Abnahme: Export Halbjahr `2026-1`, Format `schild`, nur gesperrte Bücher → Datei mit UTF-8-BOM, CRLF, Dezimalkomma; offenes Buch ohne `include_open` nicht enthalten; Lehrkraft ohne `gradebook.export` → 403; Audit-Eintrag ohne Noten; es gibt keine Route, die ein Zeugnis-PDF erzeugt.

**INT-087** · P1 · Status: Ist (Formelschutz: siehe INT-078) — **Register der übrigen Fachexporte.** Jeder Export ist im zentralen Register eingetragen (Recht, Audit, Formelschutz, Demo-Verhalten); der Registry-Test (SIC-005) scheitert, wenn eine Exportroute fehlt oder ein Merkmal nicht erfüllt ist.

| Export | Format | Recht | Verweis |
|---|---|---|---|
| Eingang eines Formulars | CSV (Semikolon, UTF-8 mit BOM) und PDF aller sichtbaren Einreichungen; Audit je Export | `forms.inbox` im Umfang (Klasse, Schritt, Rolle) | FOR-013 |
| Umfrage-Auswertung | CSV; anonyme Umfragen ohne Person und ohne Datum | Lehrende des Kursraums | KUR-065, KUR-066 |
| Kursraum-Ergebnisse und Fortschritt | CSV | Lehrende des Kursraums | KUR-044, KUR-070 |
| Kompetenzrahmen | JSON und CSV | `competency.manage` | NOT-034 |
| API-Protokoll | CSV (Zeit, Zugang, Konto, Aufruf ohne Abfrage und Token, Status, Dauer, Adresse) | `api.manage` bzw. eigene Zugänge, wie die Anzeige | INT-026 |
| Beobachtungsprotokoll | CSV | `watch.read` | Datei SIC |
| Zugangsbriefe | PDF-Sammeldatei, ZIP mit Einzelbriefen | Konten-Verwaltung; Stapel 60 Minuten gültig | STA-074 |
| Fehlzeiten-Übersicht (PDF und CSV: offen) | PDF/CSV | siehe Klassenbuch | KLB-050 |

Abnahme: Test über alle Zeilen der Tabelle: Konto ohne Recht → 403 bzw. 404; erfolgreicher Export → Audit-Eintrag; Zelle `=1+1` in Name/Freitext → entschärft; neuer Export ohne Registereintrag → Registry-Test schlägt fehl.

**INT-088** · P0 · Status: Ist (Obergrenzen und Lücken: offen) — **Auskunft und „Meine Daten exportieren“ als Exportart.** Die Wege, Rechte und der Inhalt stehen in DAT-053 und DAT-054 und KLB-064: `GET /me/export?format=json|zip` (eigenes Konto, Audit `user.export`), `GET /privacy/export?student_id=…|user_id=…` und `GET /users/{id}/export` (`privacy.subject`, Audit `privacy.export`). Auskunftsdateien sind keine API-Bereiche und für Zugänge nicht erreichbar (INT-080, INT-036). Grenzen im Altbestand: höchstens 1000 Anmeldeversuche, 5000 Audit-Einträge, 5000 Benachrichtigungen, 5000 Einträge des API-Protokolls; keine Geheimnisse (Zwei-Faktor nur ja/nein, kein Kalender-Link, API-Tokens ohne Wert, Verbindungen ohne Schlüssel); das Beobachtungsprotokoll ist nie Teil (die Auskunft darüber erteilt der Betreiber organisatorisch). Hinweise nennen Abschnitte, die nicht vollständig gelesen werden konnten; ein Einzelfehler bricht die Auskunft nicht ab.
Abnahme: Auskunft eines Elternkontos zu einem volljährigen Kind ohne Freigabe enthält weder Atteste noch Fehlzeiten; Datei enthält keinen Token-Wert und keinen Kalender-Link; Zugang „Lesen und schreiben“ ruft `GET /privacy/export` → 403; je Abruf ein Audit-Eintrag.

**INT-089** · P3 · Status: offen — **Austausch von Lerninhalten.** Teilen und Kopieren von Kursräumen und Material per Link; Export im Moodle-Format (Common Cartridge); Open-Badges-Datei für Abzeichen; Moodle-XML-Import für Fragen (nicht gebaut). Voraussetzung für jede Umsetzung: Betreiberfreigabe (Wunsch aus Marktvergleich, kein Betreiber-Wortlaut) und Beachtung von Datenschutz (keine Personendaten in Vorlagen).
Abnahme: Kursraum-Vorlage ohne Personen exportiert und in eine leere Instanz importiert → Struktur und Material vorhanden, keine Namen, Abgaben oder Noten; Abzeichen als Open-Badge-Datei prüfbar mit dem Validator der Spezifikation.

## 8. Externe Anbindungen

### 8.1 Register und gemeinsame Regeln

**INT-090** · P1 · Status: Ist — **Register der Anbindungen.** Jede Anbindung an ein anderes System steht in diesem Register; eine neue Anbindung wird zuerst hier eingetragen (Name, Richtung, Konfiguration durch wen, Schalter, Standard, Demo-Verhalten).

| Anbindung | Richtung | Eingerichtet durch | Ort und Schalter | Standard | Demo |
|---|---|---|---|---|---|
| E-Mail-Versand (Relay der Schule) | aus | Betreiber | `SM_SMTP_*` (INT-091) | aus | Test-Postausgang |
| Postfach der Person (IMAP/SMTP) | ein/aus | berechtigte Person | Profil/Postfach (INT-095) | aus | Mail-Konten gesperrt |
| SMS-Anbieter | aus | Betreiber | `SM_SMS_*` (INT-093) | aus | – |
| Webhooks (Vertretungsplan) | aus | Administration mit Bearbeitungsrecht | Einstellungen › Schnittstellen › „Erweitert“ (INT-096, INT-097) | keine Ziele | gesperrt |
| Ferien und Feiertage | aus | `masterdata.edit` | Stammdaten, `SM_HOLIDAY_IMPORT` (INT-075) | Funktion an, je Schule aktiv erst nach Einschalten | gesperrt |
| Anmeldedienste (Microsoft, Google, Apple, Schulkonto per OIDC) | aus | Betreiber/Administration | Datei 04 (ANM), `SM_SSO_*`, `SM_OIDC_*` (INT-099) | aus | gesperrt |
| Lizenzserver, Updates, Zahlungsanbieter-Eingang | aus/ein | Betreiber | Datei 08 (BET) | – | – |
| Passwort-Leak-Prüfung | aus | Betreiber | `SM_HIBP_CHECK` | 0 (aus) | – |
| Virenscanner | aus | Betreiber | `SM_CLAMAV_*` | aus | – |
| iCal-Abo | ein | jede Person | Profil (INT-085) | kein Link | – |
| Offene API | ein | Zugang mit Umfang | Abschnitt 3 | – | gesperrt |
| LTI, OneRoster-REST, Schulconnex, SCIM | ein/aus | Betreiber | INT-100, INT-101 | nicht gebaut | – |

Gemeinsame Regeln: (1) Geheimnisse (Passwörter, Token, Signaturschlüssel) sind nur per Umgebung oder verschlüsselt gespeichert, erscheinen nie wieder in Oberfläche, Antworten, Protokollen, Exporten oder Audit. (2) Jedes ausgehende Ziel läuft durch die Zielprüfung (Abschnitt 9). (3) Jede Einrichtung hat einen Testversand mit verständlicher Fehlermeldung. (4) Jede Konfigurationsänderung steht im Audit (Feldnamen, keine Werte). (5) Ein Ausfall der Anbindung verhindert nie den Fachvorgang (BEN-005); Verhalten bei Ausfall: INT-109. (6) Erklärungen nur im Hilfe-Symbol.
Abnahme: Für jede Zeile der Tabelle existiert ein Test mit Attrappe (kein Netz, QUA-025); Konfigurationsänderung → Audit-Eintrag ohne Werte; Passwort/Token erscheint in keiner Antwort von `GET`-Einstellungsrouten; Demo-Zeilen liefern 403 bei Änderung.

### 8.2 E-Mail, Postfach, SMS, Outbox

**INT-091** · P1 · Status: Ist — **E-Mail-Versand über das Relay der Schule (Betreiber-Konfiguration).** Variablen: `SM_SMTP_HOST` (leer), `SM_SMTP_PORT` (587), `SM_SMTP_USER`, `SM_SMTP_PASSWORD` (Geheimnis), `SM_SMTP_FROM` (Absender), `SM_SMTP_TLS` (`starttls` = Standard, `ssl`, `none`). Versand nur mit Host **und** Absender; fehlt eines, meldet der Start die Warnung „Kein E-Mail-Versand“ (Passwort-Zurücksetzen per E-Mail, Benachrichtigungen und Briefe per E-Mail funktionieren dann nicht), und die Wahl „In der App und per E-Mail“ sowie „Passwort vergessen“ per E-Mail bleiben ausgeblendet bzw. ausgegraut (BEN-010). `SM_NOTIFY_DISPATCHER` = 1; 0 schaltet den Versand ab. Test-Postausgang `SM_DEV_OUTBOX`: Standard 1 nur außerhalb der Produktion bei lokaler Basisadresse, sonst 0; in Produktion verboten (Startabbruch); zusammen mit SMTP oder SMS-Anbieter Warnung „Nachrichten werden nicht zugestellt, sondern angezeigt“; Test-Mails gehen nur an `example.org`; Inhalte des Test-Postausgangs werden nach 24 Stunden gelöscht (BEN-018). Alle Zustellungen laufen über die Outbox (INT-094). Jede automatische Mail ist als automatisch gekennzeichnet und trägt Abmeldelink und Abmelde-Kopfzeilen (BEN-017); Pflicht-Mails (Passwort-Zurücksetzen, Sicherheit, Zugangsbriefe) tragen weder Link noch Kopf. Eine versandte E-Mail ist höchstens 20 MB groß (SIC-075). Der Betreiber-Relay ist Betreiber-Konfiguration und läuft nicht durch die Zielprüfung (INT-107).
Abnahme: Start ohne Host → Warnung „Kein E-Mail-Versand“, Option „In der App und per E-Mail“ ausgegraut; mit Host und Absender → Testmail kommt automatisch gekennzeichnet an; `SM_ENV=production` mit `SM_DEV_OUTBOX=1` → Startabbruch; Relay nicht erreichbar → Outbox-Zeile `pending` mit steigendem `attempts`, Meldung in der App bleibt.

**INT-092** · P1 · Status: offen — **E-Mail und SMS ohne Serverzugang einrichten (Einstellungen › Schnittstellen).** Ziel: Eine Schule nimmt E-Mail-Versand und SMS ohne Zugriff auf den Server in Betrieb. Felder: Server, Port, Verschlüsselung, Absender, Benutzer, Passwort; SMS-Anbieter mit seinen Pflichtfeldern. Recht `settings.edit`. Passwörter und Token verschlüsselt gespeichert, nie wieder angezeigt; Umgebungsvariablen haben Vorrang und sind als „vom Server vorgegeben“ gekennzeichnet (Feld gesperrt); Testversand an eine Adresse bzw. Nummer mit verständlicher Fehlermeldung; Audit mit Feldnamen. Zugangsdaten trägt nur der Betreiber bzw. die Schule selbst ein, nie ein Entwicklungswerkzeug. **Widerspruch zu SIC-098** (dort: SMTP-Ziel ausschließlich per Umgebung, nie per Oberfläche): Entscheidung des Betreibers nötig [unklar]; gilt die Oberfläche, so ist der eingegebene Server eine Nutzereingabe und läuft vollständig durch die Zielprüfung mit den Ports 587, 465, 25 (Abschnitt 9).
Abnahme: Eingabe von Server und Zugang, „Testmail senden“ → „gesendet“ oder eine verständliche Meldung (Beispiel „Anmeldung am Mailserver abgelehnt“); Passwort erscheint nie wieder; mit gesetzter Umgebungsvariable ist das Feld gesperrt und gekennzeichnet; Server `127.0.0.1` → abgelehnt; Konto ohne `settings.edit` → 403.

**INT-093** · P1 · Status: Ist — **SMS-Anbieter.** `SM_SMS_PROVIDER`: leer (SMS aus), `log` (nur protokollieren), `webhook`, `twilio`, `seven`. Startprüfung: unbekannter Wert → Abbruch; `webhook` ohne http(s)-Adresse (`SM_SMS_URL`) → Abbruch; `twilio` ohne `SM_SMS_ACCOUNT_SID`, `SM_SMS_TOKEN` oder `SM_SMS_FROM` → Abbruch; `seven` ohne `SM_SMS_TOKEN` → Abbruch (`SM_SMS_FROM` optional); `SM_SMS_TIMEOUT` (Standard 10 Sekunden) muss größer 0 sein. Der Webhook-Anbieter erhält per POST Empfänger und Text mit Bearer-Token. `log` in Produktion → Warnung „SMS werden nur protokolliert“. Verwendung: vor allem Bestätigungscodes (ANM); Notfall-SMS ist ein offener Wunsch (BEN-032). Nummern werden zu E.164 normalisiert, verschlüsselt gespeichert, nur als HMAC durchsuchbar, nur maskiert angezeigt (BEN-020). Planungswert der Kosten (seven.io): etwa 7 bis 10 Cent je SMS. SMS nur mit Einwilligung der Person (Datei REH). Zustellung über die Outbox (Art `sms`); Ziele durch die Zielprüfung.
Abnahme: Anbieter `twilio` ohne SID → Startabbruch mit Hinweis auf die fehlende Variable; Anbieter `webhook` mit Attrappe empfängt Empfänger und Text per POST; Zeitlimit-Attrappe (11 s) → Versuch bricht nach 10 s ab und bleibt in der Outbox; ohne Konfiguration ist keine SMS-Option sichtbar.

**INT-094** · P1 · Status: Ist (Frist für Zeilen und Inhalte: offen) — **Outbox: Zustellung, Wiederholung, Aufräumen.** Tabelle `notifications_outbox`: `kind` (`email`, `webhook`, `secure_email`, `sms`), `target` (bis 500 Zeichen), `subject` (bis 300), `payload`, `status` (`pending`, `sending`, `sent`, `failed`), `attempts`, `next_attempt_at` (UTC), `last_error`, `dedupe_key` (bis 200), `created_at`, `sent_at`. Wiederholung (Webhook): Wartezeit 30 s · 2^(n−1) nach dem n-ten Fehlversuch (30 s, 60 s, 120 s …), höchstens 6 Stunden, nach 8 Versuchen `failed`; die Zustell-ID bleibt bei Wiederholung gleich, der Zeitstempel wird erneuert. [unklar: gleiche Werte für E-Mail und SMS; Quelle nennt nur „wachsende Wartezeit bis zu einer Obergrenze“.] Doppelsende-Schutz: Schlüssel und Nachrichten-ID werden 24 Stunden gespeichert. Klartext von Mail und SMS wird nach der Zustellung gelöscht; Neubau: auch Webhook-Nutzlasten verschlüsselt (Altbestand: Klartext-JSON, Zeilen nie gelöscht) und Zeilen nach Zustellung bzw. Frist gelöscht [unklar: Frist]. `last_error` enthält nie Antwortinhalte des Ziels. Der Hintergrunddienst startet und stoppt mit dem Server, sein Status ist abfragbar, er lässt sich anstoßen. Verwaltung: `GET /notifications/outbox`, `POST /notifications/outbox/{item_id}/retry` mit `settings.edit` oder `system.admin`; Zuschauer-Konto ausgeschlossen (Namen in Betreffzeilen); im Demo-Betrieb gesperrt.
Abnahme: Webhook-Ziel liefert Fehler → Zeile `pending`, Versuche 1, 2, 3 mit Abständen 30 s, 60 s, 120 s, nach dem 8. Versuch `failed` mit `last_error` ohne Antworttext; „Erneut versuchen“ setzt die Zeile auf `pending`; Zuschauer-Konto → 403/404; zugestellte Mail-Zeile enthält keinen Klartext mehr; zweimal derselbe `dedupe_key` innerhalb von 24 Stunden → eine Zustellung.

**INT-095** · P1 · Status: Ist — **Postfach der Person (IMAP/SMTP, Mail-OAuth).** Fachregeln in Datei 02c (NAC) und SIC-099; hier die Anbindung: bekannte Anbieter (Google, GMX, Web.de, T-Online, Yahoo, Apple, Microsoft) mit festen Servern, Host und Port aus dem Aufruf werden ignoriert; „Anderer Anbieter“ mit eigenem Server nur mit dem Recht `mail.custom_server` (Standard Administration, Schulleitung, Sekretariat; vergebbar an Personal, nie an Schüler/innen, Eltern, Hausmeister, Monitor). Ports IMAP 993, SMTP 465, 587, 25. Ratenlimit 10 Verbindungsversuche je Stunde und Konto; Zielprüfung bei Eintrag und bei jeder Verbindung; einheitliche Fehlermeldung. Abruf der Postfächer alle 5 Minuten (`SM_MAIL_SYNC_MINUTES`, `SM_MAIL_SYNC` = 1); Mailanhang beim Abruf höchstens 10 MiB. Mail-OAuth für Google und Microsoft (`SM_OAUTH_GOOGLE_*`, `SM_OAUTH_MICROSOFT_*`, Mandant `SM_OAUTH_MICROSOFT_TENANT` Standard `common`); Token-Antworten werden mit Signaturprüfung ausgewertet; Zugangsdaten verschlüsselt. Im Demo-Betrieb gesperrt.
Abnahme: Schüler-Konto verbindet Eigenserver → 403; Anbieter „Google“ mit Host `intern.example` → Host ignoriert, feste Server verwendet; 11. Verbindungsversuch binnen einer Stunde → 429; Konto ohne Recht sieht kein Eingabefeld für den Server; Passwort des Postfachs erscheint in keiner Antwort.

### 8.3 Webhooks (ausgehende Ereignisse)

**INT-096** · P1 · Status: Ist (signierter Zeitstempel: offen, SIC-073) — **Webhook-Zustellung und Nutzlast.** Zweck: Änderungen des Vertretungsplans für heute und morgen an externe Programme melden (Schul-App, Infoscreen, n8n, Zapier). Konfiguration: Liste von Zielen in den Schuleinstellungen (`webhooks`), nur Administration mit Bearbeitungsrecht; Adressen erscheinen in Antworten nur mit `settings.edit`; Ziel nur https (Port aus der Adresse). Ereignis im Bestand: `substitutions.changed`; Ereignisnamen folgen dem Schema `bereich.aktion`, `ping` ist erlaubt. Nutzlast (Schema-Version 1): `{schema, schema_version, id, event, sent_at, school, data:{date, dates, version, added, changed, removed}}`, zusätzlich `week_info`, `day_kind`, `week_no`. Kopfzeilen: `X-Schulmanager-Signature` (`sha256=<hex>`), `X-Schulmanager-Event`, `X-Schulmanager-Delivery` (eindeutige Zustell-ID), `X-Schulmanager-Timestamp` (Präfix als Konstante, INT-008). Signatur: HMAC-SHA256 über den kanonischen Körper mit `SM_WEBHOOK_SECRET`; Neubau: der Zeitstempel wird mitsigniert und der Empfänger prüft ihn mit einer Toleranz von 300 Sekunden gegen Wiedereinspielung (SIC-073); die Dokumentation für Empfänger nennt Prüfablauf und Beispiel. Zustellung über die Outbox (INT-094), Ziele durch die Zielprüfung, keine Weiterleitungen. Inhalt datensparsam: keine Abwesenheitsgründe, keine Gesundheitsdaten, keine Schülernamen (VER-036, BEN-007). Ein Geheimnis wird nie in Antworten oder Protokollen gezeigt; ein Wechsel von `SM_WEBHOOK_SECRET` verlangt, die Empfänger zu informieren. Im Demo-Betrieb sind die Webhook-Felder gesperrt.
Abnahme: Vertretung für morgen geändert → Webhook-Attrappe empfängt `substitutions.changed` binnen weniger Sekunden mit gültiger Signatur; Körper manipuliert oder Zeitstempel um 10 Minuten verschoben → Prüfung beim Empfänger schlägt fehl; Nutzlast enthält keinen Abwesenheitsgrund (Schlüsselsuche); Ziel `http://127.0.0.1/…` und Ziel mit `http://` → abgelehnt; Konto ohne `settings.edit` sieht die Zieladressen nicht.

**INT-097** · P1 · Status: offen — **Verständliche Verwaltung der Webhooks (Zielbild).** Betreiber-Zitat: „ich habe keinen Plan, was du mit dem Webhook hinzufügen meinst … Das ist irgendwie nicht so überdacht.“ (10-12 21:08). Der Altbestand versteckt die Funktion unter „Erweitert: Vertretungsplan an andere Programme senden (Webhook)“ (nur Administration mit Bearbeitungsrecht, 10-13); das ist eine Versteckung, keine Überarbeitung. Zielbild: Abschnitt unter „Erweitert“ in Einstellungen › Schnittstellen; Zweck und Beispiele (Schul-App, Infoscreen, n8n, Zapier) nur im Hilfe-Symbol; Auswahl fertiger Ziele als Vorlagen, die Adressformat und Nutzlast erklären [unklar: konkrete Vorlagen]; Knopf „Testnachricht senden“ (sendet `ping`, zeigt Statuscode und Dauer, nie den Antworttext); Zustellprotokoll der letzten Zustellungen mit Status und Fehler (Sicht auf die Outbox); eine Änderung steht im Audit ohne Adresse und Geheimnis; nichts wird ungefragt gelöscht.
Abnahme: Administration öffnet den Abschnitt, das Hilfe-Symbol erklärt Zweck und ein Beispiel in zwei Sätzen; „Testnachricht senden“ an die Attrappe → Anzeige „Zustellung erfolgreich (200, 120 ms)“ und eine Zustellung `ping` im Protokoll; Fehlerfall zeigt eine deutsche Meldung ohne Antworttext; Lehrkraft sieht den Abschnitt nicht (403 beim Direktaufruf); Demo: Felder gesperrt.

**INT-098** · P2 · Status: offen — **Ereigniskatalog der Webhooks.** Im Bestand existiert ein Ereignis (`substitutions.changed`); der vollständige Katalog ist nicht belegt [unklar]. Neubau: Katalog an einer Stelle (Name nach `bereich.aktion`, Auslöser, Nutzlast ohne Gesundheits-, Förder-, Fehlzeit- und Nachrichtendaten, Schema-Version); je Ziel wählbare Ereignisse (Liste aus Empfängern und Ereignissen); neue Ereignisse nur nach Eintrag im Katalog und Test.
Abnahme: Ereignis ohne Katalogeintrag → Test scheitert; Ziel mit nur `substitutions.changed` erhält kein anderes Ereignis; Nutzlast-Schlüsselsuche findet keinen Grund, keine Note, keine Fehlzeit.

### 8.4 Anmeldedienste, Push, Lernplattformen, Standards

**INT-099** · P1 · Status: Ist (Landes-Login: offen) — **Anmeldedienste (Verweis auf Datei 04, ANM).** Die Regeln für Anmeldung, Konten, Zuordnung und Zwei-Faktor stehen in Datei 04. Hier nur die Anbindung: Anbieter Microsoft, Google, Apple und ein allgemeines Schulkonto (OpenID Connect); Konfiguration durch Betreiber über `SM_SSO_*` und `SM_OIDC_*` (Schlüssel, Mandant, Domänenbeschränkung, Label der Schaltfläche, automatische Kontoanlage nur auf Wunsch, Standardrolle) oder durch die Administration; Discovery und Schlüsselabruf über 443 und 8443 durch die Zielprüfung; Testanbieter (`SM_SSO_DEV_MOCK`) nur in der Entwicklung, sonst Startabbruch; in der Demo gesperrt. Landes-Login (Schulconnex, VIDIS): bewusst „Groß, später“ (10-16); die OIDC-Grundlage besteht, die Aufnahme in den VIDIS-Katalog ist Vertrag und Zertifizierung (Entscheidung E-21 der Roadmap).
Abnahme: Anbieter mit Ziel `10.0.0.5` → Zielprüfung lehnt ab; `SM_SSO_DEV_MOCK=1` in Produktion → Startabbruch; Anbieter ohne Client-Kennung erscheint nicht auf der Anmeldeseite.

**INT-100** · P2 · Status: offen — **LTI 1.3 (Plattform für Lern-Apps).** Zweck: Verlagsprodukte und Lern-Apps (Beispiele der Quelle: Anton, bettermarks) einbinden, ohne sie nachzubauen; ebenso gemeinsames Whiteboard und gemeinsamer Text (nicht selbst bauen). Umfang: Start aus dem Kursraum, pseudonyme Schüler-ID je Tool, Rückgabe von Ergebnissen (Notenrückgabe, Assignment and Grade Services), Namen und Rollen (Names and Role Provisioning), Katalog dreistufig Instanz → Schule → Kursraum, Freigabe der Tools durch die Schule. Quiz und H5P bleiben bewusst nur Link oder LTI (Entscheidung E-23 der Roadmap, Bestätigung durch den Betreiber offen). Bibliotheken nur nach Lizenzprüfung (INT-102). Keine Klarnamen an Tools ohne ausdrückliche Einwilligung der Schule [unklar: Übernahmeregel der Ergebnisse ins Notenbuch].
Abnahme: Mit einem Referenz-Tool des Standards: Start aus einem Kursraum übergibt nur eine pseudonyme Kennung; Rückgabe eines Ergebnisses wird nur angenommen, wenn die Lehrkraft das Tool dem Kursraum zugeordnet hat, sonst abgewiesen; Tool ohne Freigabe der Schule → nicht startbar; Konto ohne Recht → 403.

**INT-101** · P2 · Status: offen — **Fahrplan der Standard-Anbindungen (Reihenfolge laut Betreiber-Linie 10-16: Standards vor Einzelformaten).** Aufwände der Quellen: S = bis 1 Tag, M = 2 bis 5 Tage, L = 1 bis 3 Wochen.

| Schritt | Inhalt | Aufwand | Stand |
|---|---|---|---|
| 1 OneRoster | CSV-Export (INT-084) → Notenexport (`lineItems`, `results`) → REST-Lesezugriff (`orgs`, `users`, `classes`, `courses`, `enrollments`, `academicSessions`) | CSV vorhanden; Noten M; REST L | CSV Ist, Rest offen |
| 2 Landes-Login | OIDC-Claims, Rollen-Zuordnung und Backchannel-Logout zuerst (S); Schulconnex-Login und Provisioning (M); Gruppen-Abgleich (L); Schulconnex-Quellsysteme-API liefernd (L) | S bis L | offen |
| 3 LTI 1.3 | INT-100 | M bis L | offen |
| 4 SCIM | Provisioning von Personen und Gruppen | M | offen |
| 5 Live-Abgleich | täglicher Abgleich von Personen und Klassen über einen Standard-Anschluss, Abgänge sperren | M | offen, erst nach Schritt 1 oder 2 |

Abnahme: Je Schritt liegt vor dem Bau die offizielle Formatbeschreibung vor und ein Konformitäts- oder Rundlauf-Test ist Teil der Abnahme; kein Schritt ändert die Rechte- oder Datentrennungsregeln (INT-029); ein Abgleich legt nie Konten mit Rechten über dem Standard an.

**INT-102** · P2 · Status: Ist (Regel) — **Lizenz- und Quellenregel für Standards und fremden Code.** Offene Standards werden selbst umgesetzt. Projekte unter AGPL (SchulCloud, SchulIT) liefern nur Ideen, kein Code; die Landes-Clouds laufen auf demselben Code wie SchulCloud. Ohne offenen Code: IServ, LernSax, aSc, Untis (nur Dateiformate nutzen). Bibliotheken unter Apache oder MIT (Beispiele der Quelle: ltijs, SCIM-SDK) sind nach Prüfung nutzbar; EUPL-1.2-Code nur nach Prüfung; Spezifikationen mit Lizenzvermerk „NOASSERTION“ (Schulconnex) nur zum Umsetzen, nicht zum Abschreiben; Hinweis der MIT-Bibliothek für die Untis-Dateien beibehalten (INT-060).
Abnahme: Die Abhängigkeitsliste nennt je Bibliothek die Lizenz; ein Lizenz-Scan findet keinen AGPL-Code im Quelltext; vor Einsatz einer neuen Bibliothek liegt ein Eintrag der Prüfung vor.

**INT-103** · P3 · Status: offen — **App-Option und Push.** Eine installierbare App und Web-Push sind vorerst nicht Teil des Umfangs („die app option mus noch nicht mit rein“, 10-13 20:14); Regeln und spätere Ausführung in BEN-026. Bis zur ausdrücklichen Freigabe enthält der Neubau weder Service Worker noch Push-Abonnement; Benachrichtigungen laufen über Glocke und E-Mail.
Abnahme: Der Neubau liefert kein Manifest, keinen Service Worker und keine Push-Abfrage; die Glocke funktioniert unabhängig davon.

## 9. Ausgehende Verbindungen und ihre Schutzregeln

Leitsatz: Das System darf nie als Weiterleitung in interne Netze missbraucht werden. Eine Verbindung, deren Ziel von einer Eingabe oder Einstellung abhängt, läuft durch **eine** zentrale Zielprüfung (Sicherheitsregeln SIC-097 bis SIC-099 in Datei 05; dort die vollständige Fassung).

**INT-104** · P0 · Status: Ist — **Zentrale Zielprüfung.** Der Hostname wird bei jeder Verbindung neu aufgelöst; alle aufgelösten Adressen müssen öffentlich sein: nicht Loopback, nicht privat, nicht link-local, keine Metadaten-Adressen, kein CGNAT, kein Multicast, keine eigenen Container-Namen; IPv6 einschließlich eingebetteter IPv4. Verbunden wird mit der geprüften Adresse (kein DNS-Rebinding), TLS prüft gegen den Namen. Keine Weiterleitungen. Antwortinhalte stehen nie in Fehlermeldungen; die Meldung unterscheidet die Fehlerart nicht (kein Port- oder Host-Orakel).
Abnahme: Test-Ziele `127.0.0.1`, `10.0.0.5`, `169.254.169.254`, `100.64.0.1`, `::1`, `::ffff:127.0.0.1` und ein Host, der erst öffentlich, dann privat auflöst → alle abgelehnt; Ziel mit HTTP-Weiterleitung auf ein internes Ziel → nicht gefolgt; Fehlermeldung enthält keinen Antworttext.

**INT-105** · P0 · Status: Ist — **Erlaubte Ziele und Ports (Allowlist je Dienst).** Nur diese Dienste dürfen ausgehend verbinden; jeder andere Weg ist gesperrt.

| Dienst | Ziel und Port | Wer legt das Ziel fest |
|---|---|---|
| Postfach-Server der Personen | IMAP 993; SMTP 465, 587, 25; bekannte Anbieter mit festen Servern | Person (bekannte Anbieter), `mail.custom_server` (eigener Server) |
| Anmeldedienste (Discovery, Schlüsselabruf, Token) | 443, 8443 | Betreiber/Administration |
| Webhooks, SMS-Webhook | die in der https-Adresse genannten Ziele | Administration bzw. Betreiber |
| SMS-Anbieter `twilio`, `seven` | [unklar: Ports nicht belegt; mindestens 443] | Betreiber |
| Ferien-Dienst, Lizenzserver, Update-Verteilung, Passwort-Leak-Prüfung | 443 | Betreiber (Lizenzdienst fest freigegeben) |
| Moodle-Webservice (offen, INT-073) | 443 | Administration |

Abnahme: Je Zeile ein Test mit erlaubtem und nicht erlaubtem Port (z. B. IMAP auf Port 22 → abgelehnt); ein Dienst außerhalb der Tabelle kann keine Verbindung aufbauen (Test: neues Ziel ohne Eintrag → abgelehnt).

**INT-106** · P1 · Status: Ist (Werte teils offen) — **Zeitlimits und Größenlimits.**

| Gegenstand | Wert | Wirkung |
|---|---|---|
| Browser-Anfrage | 30 s | Abbruch mit „Der Server antwortet nicht rechtzeitig“ |
| Upload, Sicherung, Import, Generator (Browser) | 5 Minuten | Abbruch |
| Virenprüfung (`SM_CLAMAV_TIMEOUT`) | 30 s (muss > 0 sein) | Zeitlimit der Prüfung [unklar: Wirkung bei Überschreitung; vermutlich wie Ausfall des Scanners, INT-109] |
| SMS (`SM_SMS_TIMEOUT`) | 10 s (muss > 0 sein) | Versuch bleibt in der Outbox |
| Passwort-Leak-Prüfung | 3 s | Passwort wird ohne Prüfung akzeptiert (INT-109) |
| Update-Download | 600 s | Zeitlimit |
| Webhook-Zustellung, Ferien-Dienst, Mail-Verbindung | [unklar: Zeitlimit nicht belegt, im Neubau festlegen und per Test belegen] | |
| Upload je Datei (`SM_UPLOAD_MAX_MB`) | 25 MB (größer 0, höchstens 10240) | 413, gezählt schon während der Übertragung |
| Anfragekörper am Reverse-Proxy | 50 MB | Austausch-Import höchstens 50 MiB |
| Mailanhang beim Abruf / versandte E-Mail insgesamt | 10 MiB / 20 MB | Grenze |
| Schülerdokument | 15 MB | Grenze (Zweckgrenze) |
| Antwort eines ausgehenden Abrufs, Webhook-Nutzlast | [unklar: Höchstgröße nicht belegt, im Neubau festlegen] | |

Abnahme: Künstlich verzögerte Route (35 s) endet mit der Meldung; Upload von 26 MB → 413 vor vollständigem Empfang; Start mit `SM_UPLOAD_MAX_MB=0` oder `SM_SMS_TIMEOUT=0` → Startabbruch; Webhook-Ziel, das 60 s schweigt, blockiert die Zustellung anderer Ziele nicht (Zeitlimit greift).

**INT-107** · P0 · Status: Ist (Befund niedrig: SMTP und Virenscanner nicht über die Zielprüfung) — **Ausnahmeliste und Betreiberziele.** Schulinterne Ziele (eigener Mailserver, Anmeldedienst, Test-Lizenzserver) erlaubt nur `SM_OUTBOUND_ALLOW` (kommagetrennt: Hostname, IP oder Netz, optional mit Port); sie hebt **nur** die Adressprüfung auf, die Port-Regeln des Dienstes bleiben; nur der Betreiber setzt sie (Umgebung, nie Oberfläche). Der Lizenzdienst ist fest freigegeben. Betreiber-Konfiguration, die nie aus einer Nutzereingabe stammt, läuft nicht durch die Zielprüfung: Relay (`SM_SMTP_*`), Datenbank, Virenscanner (`SM_CLAMAV_HOST`, `SM_CLAMAV_PORT`). Sobald ein solches Ziel aus der Oberfläche oder über die Schnittstelle gesetzt werden kann (INT-092), gilt es als Nutzereingabe und läuft durch die Zielprüfung.
Abnahme: `SM_OUTBOUND_ALLOW=mail.schule.example` erlaubt den Host mit Port 993, nicht Port 22; ohne Eintrag wird derselbe Host abgelehnt, wenn er intern auflöst; ein per Oberfläche gesetzter Server wird geprüft, der per Umgebung gesetzte Relay nicht.

**INT-108** · P0 · Status: Ist — **Datensparsamkeit der ausgehenden Anfragen.** Ferien-Dienst: nur Land-, Regions- und Sprachcode sowie Zeitraum. Passwort-Leak-Prüfung (optional, `SM_HIBP_CHECK` Standard 0): nur die ersten 5 Zeichen des SHA-1-Wertes verlassen den Server (k-Anonymität) mit angeforderter Auffüllung. Webhooks, E-Mail, SMS: keine Gesundheits-, Förder-, Fehlzeit-, Noten- oder Nachrichteninhalte, keine Abwesenheitsgründe. Lizenzserver, Update-Verteilung: nur was Datei 08 (BET) festlegt [unklar: Feldliste]. Kein ausgehender Abruf enthält Klartext-Passwörter oder Sitzungstoken.
Abnahme: Mitschnitt der Anfrage an den Ferien-Dienst zeigt nur Land, Region, Sprache, Zeitraum; Mitschnitt der Leak-Prüfung zeigt genau 5 Hex-Zeichen; Schlüsselsuche in Webhook- und Mail-Nutzlasten findet keinen Grund, keine Note, keine Fehlzeit.

**INT-109** · P1 · Status: Ist (Entscheidung zur Leak-Prüfung offen) — **Verhalten bei Ausfall einer Anbindung.** Ein Ausfall verhindert nie den Fachvorgang.

| Dienst | Verhalten |
|---|---|
| E-Mail-Relay | Outbox `pending` mit Wiederholung; Meldung in der App bleibt; nach der Höchstzahl `failed` |
| Webhook | Wiederholung 30 s · 2^(n−1), nach 8 Versuchen `failed` |
| SMS | Zeitlimit 10 s; Versuch bleibt in der Outbox [unklar: Meldung an die Person bei Bestätigungscodes] |
| Ferien-Dienst | Rückfall auf die zweite Quelle (nur gesetzliche Feiertage); früherer erneuter Versuch; vorhandene Einträge bleiben |
| Virenscanner | `SM_CLAMAV_REQUIRED` = 1: Uploads abgelehnt, solange der Scanner nicht erreichbar ist; sonst angenommen mit Warnung im Log und Kennzeichnung „nicht virengeprüft“ |
| Passwort-Leak-Prüfung | nicht erreichbar → Passwort wird ohne Prüfung akzeptiert (fail-open, Warnung im Log) [unklar: Betreiber-Entscheidung, ob das im Neubau so bleibt] |
| Anmeldedienst | Anmeldung über diesen Anbieter schlägt mit deutscher Meldung fehl; die Anmeldung mit Passwort bleibt möglich, das Inhaber-Konto bleibt erreichbar |
| Moodle-Webservice (offen) | Lauf bricht mit Bericht ab, nichts halb geschrieben |

Abnahme: Je Zeile ein Test mit abgeschalteter Attrappe: Krankmeldung wird trotz ausgefallenem Mailserver gespeichert; Upload mit `SM_CLAMAV_REQUIRED=1` und totem Scanner → abgelehnt, ohne `REQUIRED` → angenommen mit Kennzeichnung; Ferien-Hauptquelle tot → Rückfall liefert Feiertage.

**INT-110** · P1 · Status: offen (Ist: Attrappen im Altbestand teils) — **Tests ohne Netz.** Alle Tests laufen ohne ausgehendes Netz; Mail, SMS, Webhook, Anmeldedienst, Ferien-Dienst, Lizenzserver und Übersetzungsdienst sind Attrappen (QUA-025); Test-Mail-Adressen nur auf `example.org`. Ein Lasttest-Skript (nur gegen `localhost`) meldet Demo-Konten an, ruft Stundenplan, Vertretung und Nachrichten parallel auf und gibt Antwortzeiten und Fehlerquote aus; ein echter Lauf steht aus.
Abnahme: Testlauf mit blockiertem Netz besteht; der Lasttest verweigert ein Ziel außerhalb von `localhost`; ein Lauf gegen eine lokale Instanz liefert Antwortzeiten und Fehlerquote [unklar: Anzahl paralleler Konten und Zielwerte].

**INT-111** · P0 · Status: offen — **Jede Anbindung steht im Register der Drittdienste und Empfänger (REH-026).** Kein Datenfluss nach außen ohne Registereintrag: SMTP-Relay, SMS-Anbieter, Postfach-Anbieter der Personen, Ferien-Dienst, Lizenzserver, Update-Verteilung, Anmeldedienste, Passwort-Leak-Prüfung, Virenscanner, LTI-Tools, Moodle-Webservice sowie die Exportziele (Untis, SchILD, ASV, LUSD, Schulmanager-Online-Paket, OneRoster). Der Eintrag nennt Zweck, Datenkategorien, Empfänger, Rechtsgrundlage und Auftragsverarbeitung. Webhook-Empfänger und API-Zugänge sind vom Nutzer gewählte Empfänger; die Verantwortung liegt bei der freigebenden Person (Verzeichnis der Verarbeitungen, Zeile „Import, Export, Schnittstellen“). Bei Berichtigung, Löschung oder Einschränkung einer Person zeigt der Vorgang die Empfänger, an die ihre Daten gegangen sind (REH, Schalter „informiert am“; keine automatische Weitergabe).
Abnahme: Eine neue Anbindung ohne Registereintrag lässt die Release-Prüfliste scheitern; Löschvorgang einer Person, deren Daten über einen API-Zugang bezogen wurden → Liste nennt den Zugang, keine Inhalte; das Register enthält zu jeder Zeile von INT-090 einen Eintrag.

## 10. Überstimmungen, Fahrplan und offene Punkte

### 10.1 Überstimmungen (die spätere Entscheidung gilt)

| Nr | Früher | Später (gilt) | Anforderung |
|---|---|---|---|
| Ü-1 | API-Zugänge schreibgeschützt, einzige Schreibfunktion Mitteilungen (10-12 18:43) | Art „Nur lesen“ oder „Lesen und schreiben“, schulweiter Schalter, Standard aus (10-17 11:41) | INT-021, INT-022 |
| Ü-2 | Bereich „Nachrichten“ als Wunsch (10-12 18:20) | Bereich „Mitteilungen“ (Schwarzes Brett); private Nachrichten und Chats nie freigebbar | INT-009, INT-036 |
| Ü-3 | Oberflächenpfad `/api-zugaenge` | Pfad ohne Präfix `/api` | INT-010 |
| Ü-4 | Ratenlimit, IP-Freigabe, Ablauf „im Speicher des Prozesses“ (Doku) | persistent speichern; Verhalten nach Neustart festlegen | INT-028 |
| Ü-5 | Moodle-Kurse und Einschreibungen nicht importierbar (10-12) | Moodle-Importer mit Kursen, Einschreibungen, Gruppen, Aufgaben, Notenbuch (10-16) | INT-064, INT-065 |
| Ü-6 | Moodle nur über Datenbank-Abzug (10-16) | Webservice als empfohlener Hauptweg (offen) | INT-073 |
| Ü-7 | Webhook unter „Erweitert“ versteckt (10-13) | verständliche Verwaltung mit Erklärung und Testknopf | INT-097 |
| Ü-8 | CSV-Import übernimmt gültige Zeilen und meldet Fehler (13.10.) | ganz oder gar nicht | INT-047 |
| Ü-9 | Untis-Import „ersetzen“ ohne Vorher-Nachher-Vorschau (Befund) | Vorher-Nachher-Probelauf mit genannten Zahlen | INT-058 |
| Ü-10 | JSON-, Untis- und Schulmanager-Online-Export „nur angemeldet“ | Export nur mit Recht, im Audit, ohne Zuschauer | INT-077 |
| Ü-11 | Persönliche Tokens ohne Laufzeit | Ablauf Pflicht, Ende bei Passwortwechsel, Ausstellung nur für berechtigte Rollen | INT-043, INT-044 |
| Ü-12 | Wunsch „alle Rollen alle Rechte“ gegenüber Exporten | Schutz vor Wunsch: Zuschauer von Exporten ausgeschlossen | INT-077 |
| Ü-13 | Betreiber-Begriff „Datenbank übernehmen“ (10-16) | Klarstellung: Import aus anderen Systemen; Oberflächenname „Import aus anderen Systemen“ | Abschnitt 6 |

### 10.2 Fahrplan der Standards

Die Reihenfolge OneRoster, Landes-Login, LTI, SCIM, Live-Abgleich mit den Aufwänden steht in INT-101; die Lizenzregel in INT-102; der Grundsatz „Standards vor Einzelformaten“ in INT-007.

### 10.3 Offene Punkte

Alle Zeilen tragen `Status: offen`. Die Spalte „Roadmap“ nennt die Kennungen der Roadmap-Datei 10 laut deren Wellenplan (dort sind Inhalt, Aufwand und Abhängigkeiten maßgeblich; die Einzeleinträge sind dort teils noch nicht ausgeschrieben, die Zuordnung einzelner Zeilen zu einer Kennung innerhalb einer Spanne ist deshalb nicht verbindlich); „E-nn“ sind die Entscheidungen des Betreibers in Datei 10.

| Nr | Offener Punkt | Voraussetzung oder Entscheidung | Anforderung | Roadmap |
|---|---|---|---|---|
| O-1 | Reichweite eines Schreibzugangs (nur `/open/` oder gesamte Schnittstelle) | Betreiber-Entscheidung | INT-025 | – |
| O-2 | Persönliche Tokens: Pflichtablauf, Ende bei Passwortwechsel, Ausstellung nur für berechtigte Rollen | Freigabe der Sicherheitswelle (E-03) | INT-044 | INT-901 bis INT-903 (Schutz vor Datenabfluss) |
| O-3 | Stammdaten-Exporte nur mit Schülerdaten-Recht und mit Protokoll; Zuschauer ausgeschlossen | E-03 | INT-077 | INT-901 bis INT-903 |
| O-4 | CSV-Formelschutz in fünf Exporten | kleiner Fix | INT-078 | INT-901 bis INT-903 |
| O-5 | Import-Grenzen (Dateizahl, Größe, entpackte Größe, Verhältnis, Zeit) | Werte festlegen | INT-050 | INT-901 bis INT-903 |
| O-6 | Fehlerbilder der API-Zugänge: Statuscode bei IP-Sperre, Zeitraum-Höchstspanne, Obergrenzen der Filter und des Protokolls, Ratenlimit nach Neustart | Werte festlegen | INT-012, INT-013, INT-027, INT-028, INT-038 | INT-904 |
| O-7 | Untis: 8 Feldzuordnungen | echter, anonymisierter Untis-Export durch den Betreiber | INT-060 | INT-914 (Untis-Rundlauf) |
| O-8 | Untis-Rundlauf ohne Verlust, stabile Stunden-Kennungen | Neubau | INT-059 | INT-914 |
| O-9 | Weitere GPU-Dateien, Untis-Wechsel-Assistent | Entscheidung, ob gewünscht | INT-061 | INT-906 |
| O-10 | Oberfläche für Zuordnung und Entscheidungen beim Fremdimport | Neubau mit Einrichtungsassistent | INT-071 | INT-905 |
| O-11 | Hintergrundlauf, Konten beim Import optional mit Zugangsbriefen, Moodle-Webservice, Dateien aus dem Moodle-Datenordner | Betreiber-Freigabe | INT-072, INT-073, INT-067 | INT-915 bis INT-917 |
| O-12 | Moodle-Kurssicherung und Schema nur an erfundenen Daten geprüft; echte Systeme laufen auf MySQL oder PostgreSQL | echte, anonymisierte Sicherung einer Schule | INT-068 | – |
| O-13 | IServ, Schulmanager Online (Import), SVWS, itslearning, Google Classroom | echte, anonymisierte Beispieldateien | INT-074 | – |
| O-14 | Landes-Exporte weiterer Länder, ENM/SVWS-Format, Fehlzeiten-Export | Länderwahl (E-21); Verfügbarkeit der Formatbeschreibung | INT-086 | INT-918 |
| O-15 | Landes-Login (Schulconnex, VIDIS) | E-21 (NRW zuerst empfohlen) | INT-099, INT-101 | INT-910 |
| O-16 | LTI 1.3 | E-23 (Quiz/H5P nur per Link oder LTI) | INT-100 | INT-909 |
| O-17 | OneRoster-REST und Notenexport, SCIM, Live-Abgleich | nach Schritt 1 | INT-101 | INT-911, INT-912 |
| O-18 | Webhook-Verwaltung mit Erklärung und Testknopf; Ereigniskatalog; signierter Zeitstempel | Neubau | INT-097, INT-098, INT-096 | – |
| O-19 | E-Mail und SMS in der Oberfläche einrichten; Widerspruch zu SIC-098 | Betreiber-Entscheidung | INT-092 | – |
| O-20 | iCal: Feed je Kind, Elternzugriff nach Volljährigkeit, Token im Pfad | Prüfung | INT-085 | – |
| O-21 | Religionsdaten in Import und Export: eigenes Recht | Betreiber und Datenschutzbeauftragte | INT-056 | – |
| O-22 | Verhalten der Passwort-Leak-Prüfung bei Ausfall (fail-open) | Betreiber-Entscheidung | INT-109 | – |
| O-23 | Austausch von Lerninhalten (Moodle-Format, Common Cartridge, Open Badges) | Betreiberfreigabe | INT-089 | – |
| O-24 | Register der Drittdienste und Empfänger vollständig führen | Rechtsprüfung | INT-111 | – |
| O-25 | Nicht im Browser geprüft: CSV-Export des API-Protokolls, Lizenz-Schnittstellen; Lasttest echter Lauf | Prüflauf | INT-026, INT-110 | – |
| O-26 | Ferienimport-Ausbau (Zurücksetzen, deutsche Feiertagsnamen, Vorlagen je Bundesland, Import aus iCal/CSV) | Neubau | STA-058 | – |
| O-27 | Zahlungsanbieter (Stripe, GoCardless) vorbereitet, nicht aktiv; Konten fehlen | Betreiber | Datei 08 (BET) | – |
| O-28 | Kalender-Anbindung externer Systeme (CalDAV, Google, Microsoft) | nicht belegt, nicht im Umfang [unklar: Bedarf] | – | – |

### 10.4 Ideen aus Marktvergleichen ohne Betreiberwunsch (nicht Teil des Umfangs)

Repositories für Dateien (Nextcloud, WebDAV, OneDrive, Google Drive, S3); Videokonferenz nur als signierter Link (E-23); Plagiatsprüfung, Plugin-Markt, Bezahlfunktionen, volles Quiz-System und SCORM (bewusst nicht gebaut, Bestätigung durch den Betreiber steht aus); Import fremder Vertretungsformate (DSBmobile, Indiware, Untis-HTML) nur als Importweg, falls der Untis-Import fehlt. Aufnahme in den Umfang nur durch Betreiberentscheidung und mit eigener Anforderung (Muster INT-041).

<!--ENDE-->
