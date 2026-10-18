# Vorschau: Schulmanager selbst ausprobieren

Die Vorschau startet die komplette App mit einer **Demo-Schule** (≈ 2600 Schüler/innen, ≈ 170 Lehrkräfte, 99 Klassen,
zwei Standorte, Rhythmus-Beispiele: jede 2. Woche). Alle Daten sind erfunden – bitte **keine echten Schülerdaten** eintragen.

## 1. Starten

### Im Browser mit GitHub Codespaces (empfohlen, auch am Tablet)

1. Diesen Link öffnen (bei GitHub angemeldet):
   **https://codespaces.new/L0rdr3spawn/Claude.Code/tree/claude/magical-newton-dcni3v?quickstart=1**
   → **„Create codespace“** klicken.
2. Der erste Start dauert **einige Minuten** (Programme werden installiert, die Oberfläche gebaut). Danach erzeugt die
   App die Demo-Schule (ca. 30–60 Sekunden) und öffnet sich **automatisch in einem neuen Tab**.
   Falls nicht: unten im Codespace auf **„Ports“** → Zeile **„Schulmanager (8000)“** → Globus-Symbol („Im Browser öffnen“).
3. Die Adresse (`https://…-8000.app.github.dev`) ist **privat**: Nur du kommst mit deinem GitHub-Konto hinein. In einem
   Inkognito-Fenster oder auf dem Handy fragt GitHub deshalb zuerst nach deiner GitHub-Anmeldung – danach erscheint die
   Anmeldung des Schulmanagers.
4. **Beenden:** Ohne Aktivität im Codespace stoppt er nach 30 Minuten (das Protokoll im Terminal-Fenster zählt als
   Aktivität – den Codespace-Tab also offen lassen). Unter https://github.com/codespaces kannst du ihn stoppen oder
   löschen; die Leerlaufzeit lässt sich unter https://github.com/settings/codespaces verlängern. Für private Konten ist ein
   monatliches Gratis-Kontingent enthalten.
5. **Von vorn anfangen** (Demo-Schule neu erzeugen): im Codespace unten das **Terminal** öffnen und
   `scripts/preview.sh --reset` eingeben.

### Auf dem eigenen Rechner

Voraussetzungen: Python 3.11+ und Node 22.

```bash
pip install -e .
npm --prefix frontend ci && npm --prefix frontend run build
scripts/preview.sh            # → http://localhost:8000  (Strg+C beendet)
```

## 2. Konten

Passwort für alle Demo-Konten: **`demo123456`**

| Konto | Wer | Besonderheit |
|---|---|---|
| `admin` | Technische Administration | Passwort **`Schulmanager-Vorschau-2026`**; sieht keine Atteste |
| `schulleitung` | Schulleitung | alles außer Systemverwaltung; dazu Postfach-Moderation |
| `planer` | Stundenplanung | Generator, Stammdaten, Anträge von Lehrkräften |
| `sekretariat` | Sekretariat | Krankmeldungen, Atteste & Dokumente, Schüler-/Elternkonten |
| `lehrer1` | Frau Ludwig (Kürzel **LUD**) | Klassenleitung **Q1-5** („Jg. 11 Tutorium 5“), Kurse in der Oberstufe sowie M/IF in 10e und 10l |
| `lehrer2`, `lehrer3` | Herr Keller (**KEL**), Herr Vogt (**VOG**) | Klassenleitung Q1-4 bzw. Q2-5; Herr Keller unterrichtet Theo (Q1-5) in Englisch |
| `schueler1` | Nora Kaiser, 5a | minderjährig – Krankmeldung nur über die Eltern |
| `schueler2` | Luis Schreiber, 9P | Praxisklasse (mittwochs im Betrieb) |
| `schueler3` | Theo Baumann, Q1-5 | **volljährig** – meldet sich selbst krank; Klasse von `lehrer1` |
| `schueler4` | Lina Stein, 10e | besucht die Kurse „M 10e“ und „IF 10e“ von `lehrer1` (Kursräume) |
| `eltern1` | Familie | Kinder Nora (5a) und Luis (9P) |
| `monitor` | Flur-Bildschirm | zeigt den Vertretungsplan des Hauptstandorts |

**Tipp:** Zwei Rollen gleichzeitig testen – eine im normalen Fenster, die andere in einem **privaten/Inkognito-Fenster**
(oder auf dem Handy). Änderungen erscheinen live, ohne neu zu laden. Bei Lehrkräften auf das **Kürzel** achten (z. B. LUD).
Am Wochenende zeigen die Seiten automatisch den **nächsten Schultag**.

## 3. Rundgang – was du ausprobieren kannst

### Stundenplan
- `planer` → **Stundenplan**: Klasse, Lehrkraft oder Raum wählen, die Woche wählen (Woche 1 … 52, KW). Klasse **9P** hat
  mittwochs keinen Unterricht (Praxistag).
- Eine Stunde per Ziehen verschieben: gültige Ziele sind grün, Konflikte rot (der Grund erscheint beim Darüberfahren).
  **Die Änderung gilt sofort** für den regulären Plan. Zurück: Stunde zurückziehen, oder anklicken →
  „Verschieben nach … (Tastatur)“, oder **Verlauf & Audit** → „Rückgängig“.
- `planer` → **Planung**: Reiter **Stundentafeln**, **Kurse & Kopplungen** (Spalte „Lehrkraft“, Filter „ohne Lehrkraft“)
  und **Generator** (unter „1. Vorbereitung“ die Knöpfe „Kurse erzeugen“ und „Lehrkräfte zuweisen“). Der Generator läuft
  als Hintergrund-Job mit Fortschritt; das Ergebnis wird erst mit **„Übernehmen“** aktiv.

### Klassen (Klasse suchen, Personen, Wochenplan, Ausfälle)
- `sekretariat` (oder `planer`, `schulleitung`, `admin`) → **Klassen** → z. B. „7b“ suchen → Klasse öffnen.
- Oben: Jahrgang, Standort, Schülerzahl, **Klassenraum** und **Klassenleitung** – beides direkt ändern; beim Raum auf
  Wunsch „auch im Stundenplan übernehmen“ (Stunden, in denen der neue Raum belegt ist, werden gemeldet).
- Reiter **Lehrkräfte**: alle Fächer mit Kurs/Kursteil und Lehrkraft, Klassenleitung markiert. Reiter **Schüler/innen**:
  Liste mit Kurswahl.
- Reiter **Wochenplan**: Woche wählen (Vor/Zurück/Heute/Datum, Woche, KW); Vertretungen, Entfall, Verlegungen,
  Raumänderungen und Klausuren sind markiert.
- Eine Stunde anklicken → **„Findet nicht statt“** → Grund → **„Vorschau anzeigen“**: zeigt, was das System automatisch
  umstellt (ältere Klassen: Randstunde vorziehen bzw. Klasse beginnt später/endet früher; jüngere Klassen: Betreuung; die
  frei gewordene Lehrkraft kann anderswo vertreten) → **„Übernehmen“**.
- **„Klasse ist nicht da“** (z. B. Ausflug): Zeitraum, Stunden, Begleitlehrkräfte → Vorschau → Übernehmen. Die Lehrkräfte
  der Klasse werden frei und vertreten anderswo; Begleitlehrkräfte gelten als abwesend.
- Unter „Ausfälle dieser Woche“ lässt sich jede Änderung mit **„Zurücknehmen“** rückgängig machen.
- `lehrer1` sieht unter **Klassen** nur die eigenen Klassen (ohne Bearbeiten).

### Live-Vertretung
- Fenster 1: `monitor` (Flur-Bildschirm, zeigt nur den **Hauptstandort**). Fenster 2: `sekretariat` →
  **Vertretungsplan** → **„Abwesenheit erfassen“** → Lehrkraft suchen, z. B. „Vogt“ → **„Herr Vogt (VOG)“** wählen →
  ohne Stundenauswahl gilt sie ganztägig → Grund z. B. „krank“ → **„Speichern“**.
- Der Plan wird sofort neu berechnet: Randstunden älterer Klassen entfallen, Lücken in der Tagesmitte werden verlegt
  oder vertreten. Der Monitor aktualisiert sich nach etwa einer Sekunde von selbst (bei Herrn Vogt z. B. Klasse 7l).
  Alle Standorte zeigt `sekretariat` → **Monitor-Ansicht** → „Alle Standorte“.
- `lehrer1` → **Start** → im Abschnitt **„Meine Tage“** auf **„Krankmeldung“** → Zeitraum prüfen → **„Krank melden“**.

### Lehrkräfte pflegen ihr Profil
- `lehrer1` → **Profil als Lehrkraft**: Fächer, Wunschklassen, Deputat und Arbeitszeiten ändern, z. B. mit der
  Schnellvorlage **„ab 10:00“** oder **„nur abends ab 16:00“**. Die Vorschau zeigt sofort die Konflikte mit dem aktuellen
  Plan → unten **„Änderung beantragen“**.
- `planer` → **Anträge von Lehrkräften**: Antrag ansehen (mit Konflikten) → **„Genehmigen“** → im Kasten „Stundenplan für
  diese Lehrkraft neu planen“ auf **„Neu planen“**. Der Entwurf wird erst mit **„Übernehmen“** aktiv.
- `lehrer1` sieht nur die eigenen Klassen und Kurse: unter **Stundenplan** fehlen fremde Lehrkräfte und Klassen.

### Kursräume (wie Moodle)
- `lehrer1` → **Kursräume** → **„M 10e“** öffnen (dort ist `schueler4` Teilnehmerin) → Ordner anlegen,
  **„Dateien hochladen“** → Datei wählen → **„1 Datei speichern“**, oder eine Textseite schreiben.
- Beim Material auf **„Zur Stunde“** klicken und eine Stunde wählen → **„Übernehmen“**: Das Material wird erst zu Beginn
  dieser Stunde sichtbar. Zum sofortigen Ausprobieren „Frühere Stunden anzeigen“ und eine schon begonnene Stunde wählen.
  Unter **Aufgaben** eine Aufgabe anlegen.
- `schueler4` → **Start** (Kachel „Neues Material & fällige Aufgaben“) bzw. **Kursräume** → „M 10e“: sieht sichtbares
  Material und die Aufgabe, gibt ab.
- `lehrer1` → Abgabe bewerten; `schueler4` sieht die Rückmeldung.

### Postfach
- `schueler1` → **Postfach** → **Neue Nachricht** an „Frau Ludwig“ (mit Anhang). `lehrer1` antwortet.
- `sekretariat` → **Postfach** → **Neue Nachricht** → bei „An“ „5a“ eingeben → Gruppe **„Klasse 5a – Eltern“** wählen
  (damit wird es ein Rundschreiben, Betreff ist Pflicht) → **Senden**. `eltern1` erhält es.
- Eine empfangene Nachricht **melden** (unter der Nachricht **„Melden“**, Grund wählen) → `schulleitung` →
  **Postfach-Moderation**.

### Krankmeldung & Atteste
- `eltern1` → **Start** oder **Meine Übersicht** → Karte „Krank melden“ → **„Nora heute krank melden“** (ein Klick; am
  Wochenende heißt der Knopf „Für <nächster Schultag> krank melden“).
- `eltern1` → **Meine Übersicht** → „Mehrere Tage / einzelne Stunden“ → z. B. die letzten 3 Schultage melden →
  Hinweis **„Attest fehlt“** → **„Attest hochladen“** (PDF oder Handyfoto).
- `schueler1` (minderjährig) sieht nur den Hinweis, dass die Eltern melden. `schueler3` (volljährig) meldet sich selbst
  krank und kann Atteste hochladen.
- `sekretariat` → **Atteste & Dokumente**: im Reiter **Eingang** Attest ansehen, **„Geprüft“** oder **„Ablehnen“** mit
  Begründung. Im Reiter **„Attest fehlt“** (Krankmeldungen ab 3 Schultagen ohne gültiges Attest, z. B. nach „Ablehnen“)
  → **„Papier-Attest vermerken“**. `eltern1` sieht das Ergebnis.
- `lehrer1` ist Klassenleitung von Q1-5: Die Startseite zeigt die Kachel „Meine Klasse Q1-5: Krankmeldungen“ (Zähler und
  die Meldungen für heute bzw. den nächsten Schultag). Alle Meldungen mit Grund stehen unter **Krankmeldungen**, die
  Atteste über **„Öffnen“** (dort auch „Geprüft“/„Ablehnen“).
- Gegenprobe: `lehrer2` (Herr Keller, unterrichtet Theo in Englisch) → **Krankmeldungen**: Theos Meldung erscheint
  **nicht** (Fachlehrkräfte sehen standardmäßig keine Krankmeldungen, B-06); er kann nur für die eigene Stunde eine
  Abwesenheit melden (ein Tag, nicht in der Zukunft) und diese Meldung löschen, solange sie „gemeldet“ ist. Mit
  `planer` → **Planung → Prioritäten & Regeln → Krankmeldungen & Atteste → „Fachlehrkräfte sehen“** = „wer heute in
  meiner Stunde fehlt“ steht Theo am Tag selbst mit Stunde in seiner Liste und auf der Startseite – ohne Grund, Status,
  Attest und meldende Person. `admin` sieht keine Krankmeldungen.
- `sekretariat` → **Benutzer** → ein Schülerkonto öffnen → „darf sich selbst krankmelden“ (volljährig) ein- oder
  ausschalten.

### Konten & Anmeldung
- **Test-Postausgang**: In der Vorschau werden E-Mails und SMS nicht verschickt, sondern unter
  **`/test-postausgang`** angezeigt (ohne Anmeldung, eigener Tab) – mit Codes, Links und PDF-Anhängen.
- **Passwort vergessen**: abmelden → „Passwort vergessen?“ → Benutzername z. B. `eltern1`, Kanal E-Mail → Code bzw. Link
  aus dem Test-Postausgang → neues Passwort (danach gilt für das Konto das neue Passwort, nicht mehr `demo123456`). Alle
  Demo-Konten haben eine bestätigte Adresse `<benutzer>@demo.schule`.
  **Profil → Kontakt & Wiederherstellung**: E-Mail/Handynummer ändern (Bestätigung per Code, mit aktuellem Passwort).
- **Neue Klasse mit Zugangsdaten**: `sekretariat` → **Klassen → „Neue Klasse“** → Bezeichnung (z. B. `5x`) → Schülerliste
  einfügen (z. B. aus Excel: `Nachname, Vorname, Geburtsdatum, E-Mail` oder mit Kopfzeile inkl. Spalte „E-Mail Eltern“ –
  gleiche Eltern-Adresse bei Geschwistern = ein gemeinsames Elternkonto) → „In die Liste übernehmen“ → **Weiter** →
  „Zugangsdaten sofort per E-Mail senden“ → **„Probelauf (Vorschau)“** → **„Klasse anlegen“** → Ergebnis mit Sammel-PDF,
  ZIP mit Einzel-PDFs und „Per E-Mail senden“ (Zugangsdaten-Seite); die Mails mit PDF stehen im Test-Postausgang. Mit
  Benutzername und Startpasswort aus dem PDF anmelden → das Konto verlangt zuerst ein eigenes Passwort.
- **Passwort zurücksetzen (Klassenseite)**: Klassenseite → Reiter Schüler/innen: „Schüler/in hinzufügen“, Auswahl →
  „Neue Zugangsdaten erzeugen“ (fehlende Konten werden angelegt), je Person „Passwort“: auf Startpasswort zurücksetzen
  oder selbst setzen. Das geht auch als Klassenleitung, z. B. `lehrer1` für Q1-5 – dort haben in der Demo nur wenige
  Schüler/innen ein Konto und noch kein Startpasswort; deshalb zuerst als `sekretariat` in Q1-5 Schüler/innen ohne Konto
  auswählen → „Neue Zugangsdaten erzeugen“. In fremden Klassen (z. B. 10e) sieht `lehrer1` keinen „Passwort“-Knopf.
- **Microsoft / Apple / Google**: Auf der Anmeldeseite stehen Test-Anbieter („(Test)“) – eine E-Mail-Adresse eingeben
  genügt, ein Passwort wird nicht geprüft. Zuerst verbinden: angemeldet **Profil → Verbundene Konten** → bei Microsoft
  „Verbinden“ → beliebige E-Mail (z. B. `nora@test.de`) → abmelden → „Mit Microsoft anmelden (Test)“ mit **derselben**
  E-Mail. Mit einer nicht verbundenen Adresse erscheint „Zu diesem Anbieter-Konto gibt es keinen Zugang“. Als `admin`
  unter **Anmeldedienste** echte Anbieter einrichten.
- **Anmelde-Richtlinien**: `admin` oder `schulleitung` → **Anmelde-Richtlinien** → oben **„Beispiel: Schüler/innen nur
  Microsoft + Apple, beide Pflicht“** → **Speichern** (gilt für alle Schüler/innen). Dann als `sekretariat` →
  **Benutzer** → `schueler2` öffnen → Reiter „Sicherheit & Sitzungen“ → **„Passwort zurücksetzen“** (Startpasswort wird
  angezeigt) → als `schueler2` mit dem Startpasswort anmelden: Ersteinrichtung **„Konten verbinden“** → Microsoft und
  Apple je „Jetzt verbinden“ (Test-Anbieter, E-Mail merken) → „Weiter zur Startseite“. Danach wird die Anmeldung mit
  Passwort abgelehnt (auch mit dem Startpasswort: „Für dieses Konto ist die Anmeldung mit Passwort nicht vorgesehen“);
  „Mit Apple anmelden (Test)“ mit derselben E-Mail funktioniert. Reiter **Vorschau** („Was gilt für …?“) und **Bericht**
  („Wer hat noch nicht verbunden?“) zeigen die Wirkung. Zurückstellen: Reiter Rollen → „Rolle Schüler/in“ →
  „Bearbeiten“ → **„Regel entfernen“**; das Passwort von `schueler2` setzt `sekretariat` unter „Sicherheit & Sitzungen“ →
  „Auf Startpasswort zurücksetzen / selbst setzen“ wieder auf `demo123456` (Haken „beim nächsten Anmelden ändern“
  entfernen).

### Verwaltung
- `admin` → **System**: **„Sicherung erstellen“**, **„Wartung jetzt ausführen“**. Achtung: „Demo laden“ und „Laden“ einer
  Sicherung ersetzen alle Daten.
- `admin` oder `planer` → **Verlauf & Audit**: Reiter „Versionen (Undo)“ zeigt, wer wann was geändert hat;
  **„Rückgängig“** nimmt die *jeweils letzte* Änderung zurück (egal von wem), „Wiederherstellen“ holt einen älteren Stand.
- `planer` → **Import / Export**: Export für Untis (GPU-ZIP), Schulmanager Online (Paket), JSON und CSV; Import aus Untis,
  CSV mit Vorlagen (SchILD-NRW, ASV, LUSD, Magellan) und JSON – zuerst **„Probelauf“**. `sekretariat` sieht Export und
  CSV-Import.
- **Profil**: 2-Faktor-Anmeldung einrichten, eigene Daten exportieren; mit einem Lehrer-, Schüler- oder Elternkonto auch
  das Kalender-Abo (iCal).

## 4. Grenzen der Vorschau
- E-Mails, SMS und Webhooks werden nicht verschickt (E-Mails/SMS stehen im Test-Postausgang).
- Entwicklungsmodus: Der Schlüssel für die Verschlüsselung wird aus einem zufälligen Geheimnis im Codespace abgeleitet –
  für echte Daten gilt die Anleitung in `docs/BETRIEB.md`.
- Läuft die Vorschau nicht (z. B. nach dem Neustart eines Codespaces), im Terminal `scripts/preview.sh --background`
  eingeben; Protokoll unter `data/preview/server.log`.
