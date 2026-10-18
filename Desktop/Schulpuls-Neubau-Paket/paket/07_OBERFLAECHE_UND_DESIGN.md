# 07 Oberfläche und Design (Kürzel OBE)

Stand: 18.10.2026. Geltung: Neubau des Schulverwaltungs- und Lernsystems (Arbeitstitel des Produkts: „Schulpuls“, technisch „schulmanager“). Diese Datei legt fest, wie die Oberfläche aussieht, sich verhält und klingt: Gestaltungsregeln des Betreibers, Design-Tokens, Bausteine, das gemeinsame Tage-×-Stunden-Raster, Seiteninventar und Menü je Rolle, Hilfe, Texte, Barrierefreiheit, Handy-Ansicht, Druck, Monitor und Marke. Sie beschreibt WAS gelten soll, nicht wie der alte Code gebaut war.

## 0. Lesehilfe

- **Kennung**: `OBE-nnn`, fortlaufend ab 001. Jede Anforderung hat genau eine Zeile `Abnahme:` (Eingabe oder Zustand, erwartetes Ergebnis, wo sinnvoll Rechte- oder Fehlerfall).
- **Priorität**: P0 = Pflicht (Betreiberregel, Sicherheit, Recht, Barrierefreiheit). P1 = Kernfunktion. P2 = wichtig. P3 = Wunsch.
- **Status**: `Status: Ist` = im bisherigen Produkt gebaut und im Neubau mindestens gleich zu liefern. `Status: offen` = gewünscht oder vorgesehen, aber noch nicht (vollständig) gebaut. Reste im Altbestand, die gegen die Regel verstoßen, sind im Neubau nicht zu übernehmen.
- **Rangfolge bei Widersprüchen**: spätere Entscheidung vor früherer (Datum beachten); Langfassung des Designhandbuchs vor der Kurzfassung; Wortlaut des Betreibers vor Zusammenfassungen. Alle Quellenwidersprüche, die hier entschieden oder offen gelassen wurden, stehen gesammelt in Kapitel 17.
- **Zitate** des Betreibers stehen in Anführungszeichen mit Datum. Das Original ist diktiert; Schreibweisen bleiben unverändert.
- `[unklar: …]` markiert Werte oder Entscheidungen, die in den Quellen fehlen. Dort ist nichts erfunden.
- **Querverweise** auf andere Dateien des Pakets nennen nur das Kürzel (REC Rechte, ANM Anmeldung, DAT Datenschutz, BEN Benachrichtigungen, STP Stundenplan, VER Vertretung/Monitore, KLB Klassenbuch, NOT Noten, KUR Kursräume, NAC Nachrichten, FOR Formulare/Briefe, STA Stammdaten, BET Betrieb, SIC Sicherheit, REH Recht, QUA Qualität).
- **Begriffe**: „Hilfe-Symbol“ ist der Oberbegriff für die Namenshilfe (Beschriftung mit gepunkteter Unterstreichung) und das Info-Zeichen (i) an Überschriften. „Raster“ ist das eine Tage-×-Stunden-Raster (Kapitel 4). „Flag“ ist ein Berechtigungskennzeichen in der Serverantwort (z. B. „darf bearbeiten“). „Eigener Datenumfang“ ist der Teil der Daten, den eine Person sehen darf; Zugriff darauf außerhalb ergibt 404.
- **Rollen** in diesem Dokument: Administration, Schulleitung, Sekretariat, Planung (Stundenplanung), Abteilungsleitung, Klassenleitung, Lehrkraft (inkl. Fachlehrkraft), Schüler/in, Eltern (Familie), Zuschauer (reiner Lesezugriff, Vorführ-Konto), Monitor (Anzeigekonto), eigene Rollen der Schule; geplant: Hausmeister, Schulbegleitung. Die Rechte-Namen (z. B. `timetable.edit`) sind im Rechte-Katalog (REC) festgelegt.

---

## 1. Gestaltungsprinzipien des Betreibers

- **OBE-001 · P0 · Status: Ist** — Ruhig, einheitlich, gut lesbar. Betreiber-Auftrag (13.10.2026): Das Design soll „einheitlicher, ruhiger, gut lesbar, auch auf dem Handy“ sein. Neutrale Flächen, genau eine Akzentfarbe (Blau) für Aktionen und Auswahl. Farbe trägt Bedeutung (Status, Vertretungsart), nie Dekoration. Keine Verläufe, keine Hero-Bereiche, keine Illustrationen, keine Emojis oder Textzeichen als Icons in den Oberflächentexten der Anwendung (Nutzerinhalte in Nachrichten sind ausgenommen).
  - Abnahme: Rundgang über alle Seiten in Hell und Dunkel zeigt außer Status- und Vertretungsfarben nur Neutraltöne und die Akzentfarbe; keine Verläufe, keine Illustrationen; eine automatische Suche nach Emoji-Zeichen in Oberflächentexten (ohne Nutzerinhalte) findet 0 Treffer.

- **OBE-002 · P0 · Status: Ist** — Dicht, aber klar. Viele Informationen je Bildschirm, sauber ausgerichtet. Gruppierung über Abstand und dünne Linien, nicht über Karten mit Schatten. Eine Karte ist ein Abschnitt mit 1-px-Rand ohne Schatten; Karten werden nicht ineinander geschachtelt; nicht jede Information steht in einer Karte. Kennzahlen stehen als eine Leiste mit Trennlinien, nicht als Einzelkarten. Ein Wert hat genau ein Steuerelement.
  - Abnahme: Automatische Stilprüfung findet keine Karte mit Schatten und keine Karte innerhalb einer Karte; jede Kennzahlengruppe ist eine einzige Leiste; für jeden einstellbaren Wert existiert genau ein Steuerelement.

- **OBE-003 · P0 · Status: Ist** — Hilfe statt Erklärtext. Betreiber (12.10.2026): „short labels, explanations behind a small i“. Beschriftungen sind kurz; Erklärungen stehen in der Hilfe an der Beschriftung (Kapitel 8). Es gibt keine erklärenden Absätze, auch keine kleinen grauen Erklärsätze unter Überschriften, keine dauerhaften Hinweisboxen als Erklärtext, keine Einleitungskarten. Dauerhaft sichtbar bleiben nur: Fehlertexte, Leerzustände (kurzer Titel), Formatangaben, ohne die ein Feld nicht ausfüllbar ist, Hinweise zu einem echten Zustand (z. B. „3 Schultage – Attest nötig“, Ferien-Warnung), rechtlich nötige Hinweise (Datenschutzerklärung, Attest-Hinweis). Der Altbestand hatte noch rund 65 solcher Restfälle und eine Ausnahmeliste; im Neubau gibt es keine Ausnahmeliste.
  - Abnahme: Eine automatische Prüfung zählt Textblöcke, die als Erklärtext gelten (Absatz mit mehr als 12 Wörtern außerhalb der erlaubten Textarten); Ergebnis 0. Die erlaubten Textarten sind als Komponenten markiert, nicht als freie Absätze.

- **OBE-004 · P0 · Status: Ist** — Alle Geräte gleichwertig. Jede Seite ist ab 360 px Breite ohne waagerechtes Scrollen der Seite nutzbar (Prüfbreiten 360, 390, 820, 1440 px); Bedienung mit Maus, Touch und Tastatur; Hell und Dunkel. Jede Funktion für Eltern, Schüler/innen und Lehrkräfte geht am Handy vollständig; Verwaltung und Planung zusätzlich gut am PC und Tablet. Betreiber (11.10.2026): „dass das auch alles mobile kompatibel ist“. Breite Inhalte (Tabellen, Raster) scrollen im eigenen Rahmen.
  - Abnahme: Je Rolle und Seite des Verzeichnisses (Kapitel 6) bei 360 px und 390 px: Breite des Dokuments gleich Breite des Fensters (kein Seitenscroll), alle Hauptaktionen erreichbar; Stichprobe 820 px und 1440 px; alles in Hell und Dunkel.

- **OBE-005 · P0 · Status: Ist** — Eine Gestaltungssprache für gleichartige Objekte. Betreiber (13.10.2026): „dass ähnliche Objekte, zum Beispiel wenn es unterschiedliche Stundenpläne gibt … dass es alles gleich aussieht, dass es die gleiche Design Language hat und nicht immer unterschiedlich ist“. Gleich sind: Knöpfe, Felder, Reiter, Karten, Dialoge, Navigation und Rasterzellen in Höhe, Abstand, Ecken und Farbe; Listen (Anträge, Meldungen, Regeln) in einer Grundform mit farbigem Statusbalken links; Status-Chips; alle Raster (Kopfzeile, Zeitspalte, Zellgröße, Schraffur, Heute-Markierung, Markierungen für Klausur, Hausaufgabe, krank, Entfall). Das Anbieter-Portal (BET) nutzt dieselbe Optik (Farben, Schrift, Karten, Tabellen, Hell und Dunkel, Handy); gefährliche Aktionen sind rot.
  - Abnahme: Bildschirmfoto-Vergleich der Stundenpläne (Klasse, Lehrkraft, Raum, Schüler/in, Eltern), der Kalenderwoche, der Fehlzeiten-Prozentansicht, der Aufsichten und der Verfügbarkeit: Kopfzeile, Zeitspalte, Zellhöhe, Schraffur, Heute-Markierung und Statusfarben sind identisch; die Listen von Anträgen, Meldungen und Regeln haben dieselbe Grundform; das Anbieter-Portal verwendet dieselben Tokens.

- **OBE-006 · P0 · Status: Ist** — Anrede „Sie“ für alle. Betreiber (16.10.2026): Die Anwendung „siezen“, auch Schüler/innen und Eltern. Gilt für Oberfläche, Servertexte, E-Mails, SMS, PDF (Zugangsbriefe, Elternbriefe), Hilfe und Handbuch, Fehlermeldungen und Tests. Frühere Fassungen im Du („Willst du dich wirklich abmelden?“, „Bitte wende dich an deine Klassenleitung“, „Dein Konto“) sind überholt. Der Betreiber selbst schreibt im Chat „du“; das gilt nicht für die Anwendung.
  - Abnahme: Eine Textprüfung über Oberfläche, Servertexte, Mailvorlagen, PDF-Vorlagen und Handbuch findet keine Formen von „du“, „dein/e/n/m/r“, „dich“, „dir“ (Ausnahme: Zitate in Nutzerinhalten); Zugangsbrief für ein minderjähriges Kind enthält Sie-Formulierungen.

- **OBE-007 · P0 · Status: Ist** — Keine Browser-Dialoge. Betreiber (16.10.2026): „kannst du das bitte nicht aufspringen lassen“ (gedeutet und umgesetzt als: keine Browser-Popups). Alle Bestätigungen und Texteingaben (auch Passwort- und Token-Felder) laufen über App-Dialoge (Kapitel 3, 3.1). Ausnahme: Die Browser-Rückfrage beim Schließen des Tabs, solange ein Datei-Upload läuft.
  - Abnahme: Ein Test sucht im Quelltext nach Aufrufen der nativen Dialoge (Bestätigen, Hinweis, Eingabe) und findet 0 Treffer; im Browser löst keine Aktion einen nativen Dialog aus; nur beim Tab-Schließen während eines Uploads erscheint die Browser-Frage.

- **OBE-008 · P0 · Status: Ist** — Ein Raster für alle Tage-×-Stunden-Ansichten. Betreiber (13.10.2026): „Du sollst immer dieses Stundplan Raster benutzen und dann halt custom für die bestimmten Use Cases benutzen.“ Es gibt genau einen Raster-Baustein; Ansichten passen nur den Zellinhalt oder eine Variante des Bausteins an (Kapitel 4). Kein eigenes Raster, keine eigene Tabelle für Tage × Stunden.
  - Abnahme: Eine automatische Prüfung schlägt fehl, sobald eine Ansicht mit Tagen als Spalten und Stunden als Zeilen ohne den Raster-Baustein gebaut ist; alle Verwendungen aus OBE-094 verwenden ihn nachweislich.

- **OBE-009 · P0 · Status: Ist** — Pop-over statt Schraffur für gekoppelte Inhalte. Schraffur im Raster bedeutet ausschließlich „gesperrt“ oder „gefehlt“. Gekoppelte Kurse zeigen sich als Knopf „N Kurse“, der ein Pop-over mit den Kursteilen und dem Knopf „Kurs bearbeiten“ öffnet. Betreiber (16.10.2026): „bei er ist das ist so gestrichelt ich weiß nicht warum“ und „kannst du dieses drei kurse ding anklickbar machen“.
  - Abnahme: Ein gekoppelter Kurs wird ohne Schraffur dargestellt; Klick/Tipp auf „3 Kurse“ öffnet ein Pop-over mit allen drei Kursteilen und „Kurs bearbeiten“; eine gesperrte Zelle ist durchgehend schraffiert, ebenso eine als „gefehlt“ markierte.

- **OBE-010 · P0 · Status: Ist** — Status nie nur über Farbe. Jeder Status (Vertretungsart, Anwesenheit, Fehler, Warnung, Erfolg, Notenfarbe, Heatmap) erscheint zusätzlich als Wort oder Kurzzeichen. Die Notenfarbe dient nur der Kennzeichnung; der Wert steht immer daneben.
  - Abnahme: In Graustufen-Darstellung und mit simulierter Farbfehlsichtigkeit bleibt jeder Status unterscheidbar; kein Statusabzeichen besteht nur aus einer Farbfläche.

- **OBE-011 · P0 · Status: Ist** — Server prüft, Oberfläche blendet nur aus. Rechte und Datenumfang werden immer auf dem Server geprüft. Elemente und Menüeinträge erscheinen nach Flags der Serverantwort, nie nach Rollennamen. Rechte-Namen in der Oberfläche stimmen mit dem Rechte-Katalog des Servers überein. Fremde Daten liefern 404, nicht 403.
  - Abnahme: Ein Konto einer eigenen Rolle mit frei gewählten Rechten sieht genau die Knöpfe, für die der Server Flags liefert; ein Test vergleicht alle in der Oberfläche verwendeten Rechte-Namen mit dem Katalog (Abweichung = Fehler); der direkte Aufruf eines fremden Datensatzes zeigt die 404-Seite.

- **OBE-012 · P0 · Status: Ist** — Menschen wählen, das System entscheidet nicht allein. Betreiber (12.10.2026): „Menschen mögen es lieber, eine Auswahl zu haben … Ne, ich muss jetzt genau das nehmen, weil das ist die KI.“ Wo das System Lösungen berechnet (Planvorschläge, Vertretungsvorschläge, Nachschreibtermine), zeigt die Oberfläche mehrere Varianten mit Zahlen vorher und nachher nebeneinander, nennt sachliche Hinweise („wenigste Änderungen“, „beste Qualität“), spricht keine Empfehlung aus und übernimmt nichts ohne ausdrückliche Auswahl mit Bestätigung. Automatische Übernahme ist standardmäßig aus.
  - Abnahme: Ein Variantenvergleich zeigt keine vorausgewählte Variante und kein Wort „empfohlen“; „Diesen Plan nehmen“ verlangt einen Bestätigungsdialog; ohne Klick bleibt der Plan unverändert.

- **OBE-013 · P0 · Status: Ist** — Keine Schieberegler; Technik unter „Erweitert“. Zahlen sind Zahlenfelder, Stufen sind Stufenauswahlen (2 bis 5 gleichrangige Optionen nebeneinander, z. B. egal · normal · wichtig · sehr wichtig), Zeitbudgets sind Auswahlen („Schnell · Normal · Gründlich“). Rohwerte, Startwerte und technische Parameter stehen unter „Erweitert“ (aufklappbar), mit genau einem Steuerelement je Wert. In der Oberfläche erscheinen keine IDs, Feldnamen, Schema-Revisionen, Konfigurationsschlüssel oder englischen Status („Job … Status“, „removed_lessons: 0“); Zahlen tragen deutsche Bezeichnungen („Klassen 33“).
  - Abnahme: Die Oberfläche enthält keine Elemente vom Typ Schieberegler; die Planungs-Optimierung zeigt höchstens sechs Ziele als Stufenauswahl; eine Textprüfung findet keine Rohschlüssel („assigned: 0 · open: 0“) und keine Job-IDs.

- **OBE-014 · P0 · Status: Ist** — Knöpfe. Genau eine Hauptaktion (primär) je Bereich; Nebenaktionen als Ghost-Knopf; Symbolknöpfe tragen eine Bezeichnung für Bildschirmleser; Beschriftung als Verb im Infinitiv mit klarem Ziel („Speichern“, „Krank melden“, „Neuen Link erzeugen“). Der Gefahr-Knopf (danger) ist nur für zerstörende oder nicht umkehrbare Aktionen (Löschen, Sperren, Kündigen, Sofort-Löschen); „Krank melden“ ist eine Hauptaktion, kein Gefahr-Knopf. Die Hauptaktion ist nur dann deaktiviert, wenn ein Grund erkennbar ist. Während einer Aktion zeigt der Knopf einen Ladezustand und ist deaktiviert (kein Doppelabsenden).
  - Abnahme: Je Dialog und Seitenbereich genau ein primärer Knopf; ein Doppelklick auf „Speichern“ erzeugt genau einen Speichervorgang; ein deaktivierter Hauptknopf nennt den Grund (Hilfe oder Hinweis); „Krank melden“ hat die Primärfarbe.

- **OBE-015 · P0 · Status: Ist** — Keine Fremdinhalte, kein Datenabfluss. Die Oberfläche lädt keine Fremdinhalte: Schriften lokal, keine Skripte, Tracker, Analyse- oder Replay-Werkzeuge, keine Telemetrie (nur was die Person selbst abschickt); Skripte der Anmeldedienste (Google, Microsoft, Apple) werden erst geladen, wenn der Anbieter aktiv ist; Emoji-Auswahl und Formelsatz sind lokal gebündelt; keine GIF-Suche über Dritte (Suchanfragen und IP-Adressen würden an Fremde gehen); SVG-Dateien von Nutzern werden nie im Browser angezeigt.
  - Abnahme: Ein Netzwerkprotokoll beim Rundgang zeigt nur Anfragen an die eigene Instanz (Ausnahme: aktivierte Anmeldedienste auf der Anmeldeseite); eine Inhaltssicherheitsrichtlinie verbietet fremde Quellen; ein hochgeladenes SVG wird nur als Download angeboten.

- **OBE-016 · P1 · Status: Ist** — Browser-Speicher nur für Komfort. Im Browser werden nur Komfortwerte gemerkt: Farbschema, Schalter „Hilfetexte immer anzeigen“, zuletzt verwendete Emoji, gewähltes Kind (Eltern). Sie sind nie die einzige Quelle und enthalten keine personenbezogenen Inhalte außer der Kind-Auswahl. Die Kind-Auswahl wird je Konto gemerkt (nicht gerätweit) und bei ungültigem Kind auf das erste erlaubte Kind zurückgesetzt. Beim Abmelden, beim Kontowechsel und bei 401 werden alle kontobezogenen Zwischenspeicher und offenen Meldungen geleert.
  - Abnahme: Elternkonto A wählt Kind 2, meldet sich ab, Elternkonto B meldet sich an: B sieht nicht die Auswahl von A, und ein gemerktes fremdes Kind führt nicht zu einem hängenden 403, sondern zur Auswahl des ersten Kindes; nach Abmelden zeigt „Zurück“ im Browser keine Daten des Vorkontos.

---

## 2. Design-Tokens

- **OBE-017 · P0 · Status: Ist** — Nur Tokens. Alle Farben, Abstände, Schriftgrößen, Radien, Schatten, Übergänge und Maße kommen aus benannten Tokens. Keine festen Farbcodes, keine Inline-Styles für Farbe oder Abstand, keine neuen Farben und keine Abstände außerhalb der Skala. Der Altbestand hatte rund 400 Stellen mit eigenen Abständen und 144 Inline-Styles; das ist nicht zu übernehmen.
  - Abnahme: Eine automatische Suche in Stilen und Komponenten findet keinen Farbcode außerhalb der Token-Definition und keinen Inline-Style mit Farbe oder Abstand; Abweichung = Fehler im Build.

- **OBE-018 · P0 · Status: Ist** — Farb-Tokens neutral. Jedes Token hat einen Wert für Hell und für Dunkel. Verbindliche Werte (Hell / Dunkel):

| Token | Zweck | Hell | Dunkel |
|---|---|---|---|
| bg | Seitenhintergrund | #f4f6fa | #0d1117 |
| surface | Flächen: Karten, Eingabefelder | #ffffff | #161b22 |
| surface-2 | Tabellenkopf, leichte Absetzung | #f8f9fb | #1b212a |
| surface-3 | Hover, Gruppen, Ablagen | #eef1f5 | #222a35 |
| border | Trennlinien, Kartenrand | #d8dde5 | #2f3a48 |
| border-strong | betonte Trennung, Knopfrand, Zellenrahmen | #9aa6b8 | #536074 |
| border-control | Rand von Eingabefeldern (mindestens 3:1) | #7d8898 | #6b778a |
| text | Haupttext | #111827 | #e6edf3 |
| text-muted | Nebentext | #4b5563 | #a9b4c2 |
| text-faint | Hilfs- und Hinweistext | #5f6877 | #8b97a6 |
| primary | Hauptaktion, Auswahl, Links, aktive Reiter und Menüpunkte | #1d4ed8 | #60a5fa |
| focus | Fokusrahmen (2 px) | #2563eb | #93c5fd |
| primary-hover, primary-soft, on-primary | Hover, Hintergrund ausgewählter Elemente, Text auf Primärfläche | [unklar: Werte nicht in den Quellen; Neubau legt fest] | [unklar] |
| overlay | Abdunkelung hinter Dialogen und ausgeklapptem Menü | [unklar: Wert] | [unklar] |
| shadow-sm, -md, -lg | nur für Menüs und Dialoge | [unklar: Werte] | [unklar] |

  Karten und Tabellen tragen keinen Schatten. `border` und `border-strong` sind Trennlinien; der Rand eines Eingabefelds ist stets `border-control`.
  - Abnahme: Die Token-Tabelle der Umsetzung enthält diese Namen und Werte; ein Test liest sie aus und rechnet die Kontraste aus OBE-020 nach.

- **OBE-019 · P0 · Status: Ist** — Hell und Dunkel gleichwertig. Das Farbschema ist wählbar in drei Stufen: hell, dunkel, System (folgt dem Gerät). Der Umschalter sitzt in der Kopfzeile (Kapitel 5); die Wahl wird je Browser gemerkt. Ein Zeitplan für den Dunkelmodus entfällt („System“ deckt das ab, 16.10.2026). Dunkle Werte werden an genau einer Stelle definiert; im Altbestand waren sie doppelt (Geräteeinstellung und manuelle Wahl) und mussten identisch gepflegt werden. Jede neue Farbe braucht Werte für beide Schemata.
  - Abnahme: Wahl „System“ mit Gerät auf dunkel und Wahl „dunkel“ ergeben pixelgleiche Darstellung; eine Prüfung findet jedes Token in beiden Schemata; ein Zeitplan-Schalter existiert nicht.

- **OBE-020 · P0 · Status: Ist** — Kontrast nach WCAG AA, in beiden Schemata. Text mindestens 4,5:1 (großer Text mindestens 3:1); Feldränder, Fokusrahmen und Bedienelement-Zeichen mindestens 3:1 zur Fläche; Schrift auf den weichen Statusflächen mindestens 4,5:1; Text auf der Primärfläche mindestens 4,5:1 (Hell und Dunkel). Fächerfarben: Serverfarbe, sonst eine stabile, aus dem Kürzel abgeleitete Farbe; die Schriftfarbe wird rechnerisch so gewählt, dass der Kontrast mindestens 4,5:1 beträgt.
  - Abnahme: Ein automatischer Token-Test prüft alle Paarungen (Text auf Flächen, Rand auf Fläche, Text auf Status, Text auf Primär, Fokus auf Fläche) in beiden Schemata und schlägt bei Unterschreitung fehl; für 50 zufällige Fächerkürzel ist der berechnete Textkontrast jeweils mindestens 4,5:1.

- **OBE-021 · P0 · Status: Ist** — Statusfarben. Vier Statusfamilien, je mit Farbe und weichem Hintergrund: success (Erfolg, OK), warning (Achtung, zu prüfen; der Text ist ein Braunton), danger (Fehler, Löschen, Abwesenheit), info (neutrale Meldung); dazu „Text auf Statusfarbe“ für voll gefärbte Flächen (Konflikt, wichtige Hinweise). Werte: [unklar: Hex-Werte stehen nicht in den Quellen; Neubau legt sie fest und erfüllt OBE-020]. Anwesenheit nutzt grün, gelb, rot (success, warning, danger) mit Prozentwert; „krank“ zählt 0 %.
  - Abnahme: Die Statusfamilien sind als Tokens beider Schemata vorhanden; ein Hinweis in jeder der vier Arten ist in Hell und Dunkel gerendert und erfüllt 4,5:1.

- **OBE-022 · P0 · Status: Ist** — Vertretungsarten mit eigener Farbfamilie. Jede Eintragsart hat Hintergrund, Text und Rand als Token in beiden Schemata sowie ein Kurzzeichen und ein Wort. Es gibt zehn Arten: Vertretung, Betreuung, Mitbetreuung, Entfall, Verlegung, Raumänderung, Lehrkraft abwesend, Aufsicht, Klausur, Sonstiges (die Liste im Designhandbuch kannte „Mitbetreuung“ nicht; die Token-Übersicht kennt sie; maßgeblich sind die zehn). Die Farben gelten nur für Einträge im Vertretungs- und Stundenplan. Vertretung und Entfall erscheinen im Stundenplan als farbiger Rahmen in der Farbe der Vertretungsart; Markierungen sind gedämpft mit gutem Kontrast. Eine neue Eintragsart braucht eine neue Farbfamilie in beiden Schemata. Reihenfolge in Listen: feste Reihenfolge nach Art [unklar: genaue Reihenfolge nicht in den Quellen; Vorschlag = Reihenfolge der Aufzählung oben]. Werte der Farben und Kurzzeichen: [unklar: nicht in den Quellen].
  - Abnahme: Für jede der zehn Arten existieren Tokens (Hintergrund, Text, Rand) in Hell und Dunkel, Wort und Kurzzeichen; ein Stundenplan mit je einer Stunde jeder Art zeigt zehn unterscheidbare Rahmen auch in Graustufen; das Hinzufügen einer elften Art ohne Farbfamilie lässt den Build fehlschlagen.

- **OBE-023 · P1 · Status: Ist** — Zustandsfarben im Raster. Zustandsklassen für Rasterzellen: frei, gut, mittel, schlecht, gedämpft, Konflikt, Wunsch; Zeitfenster: verfügbar (grün), gesperrt (rot) und gesperrt-Schraffur; Heatmap-Anteil von 0 bis 1 (Farbstufen aus Tokens). Werte: [unklar: nicht in den Quellen]. Farben nur aus diesen Klassen, Hell und Dunkel über Tokens.
  - Abnahme: Alle genannten Zustände sind in Hell und Dunkel als Tokens vorhanden und in der Raster-Legende (OBE-085) mit identischen Farbfeldern dargestellt.

- **OBE-024 · P0 · Status: Ist** — Typografie. Systemschrift (Segoe UI, Roboto, Helvetica, Arial, Noto Sans), Festbreitenschrift für Kürzel und Codes; keine nachgeladenen Fremdschriften.

| Stufe | Größe | Gewicht | Verwendung |
|---|---|---|---|
| Seitentitel (2xl) | 24 px | 600 | ein Titel (Ebene 1) je Seite |
| Abschnittsüberschrift (lg) | 18 px | 600 | Abschnitte, Dialogtitel |
| Unterabschnitt (md) | 16 px | 600 | Unterabschnitte |
| Fließtext, Eingabefelder (md) | 16 px, Zeilenhöhe 1,5 | 400 | Eingabefelder 16 px, damit iOS nicht zoomt |
| Beschriftung, kompakte Tabelle (sm) | 14 px | Feldnamen 600 | Tabellenköpfe, Metaangaben |
| Kleinst (xs) | 12 px | 500 bis 700 | nur Badges und Menügruppen, nie Fließtext |
| xl | 20 px | [unklar: Verwendung nicht benannt] | |

  Zeilenhöhen: eng 1,25, mittel 1,35, Standard 1,5. Gewichte: 500, 600, 700. Zahlen in Tabellen und Kennzahlen haben gleiche Ziffernbreite und stehen rechtsbündig. Fließtext ist höchstens 72 Zeichen breit.
  - Abnahme: Rechnen mit den Browserwerkzeugen: Seitentitel 24 px/600, Eingabefelder 16 px, Fließtextbreite höchstens 72 Zeichen bei 1440 px; eine Spalte mit Zahlen ist rechtsbündig und ausgerichtet; keine Fremdschrift in den Netzwerkanfragen.

- **OBE-025 · P0 · Status: Ist** — Abstände, Radien, Schatten, Bewegung. Abstandsskala 4, 8, 12, 16, 24, 32, 40, 48 px (häufigste: 8 und 12). Seitenrand 16 px am Handy, sonst 16 bis 32 px; in Formularen 12 oder 16 px; zwischen Abschnitten 16 bis 24 px; Rasterzellen-Abstand 2 px. Radien: xs 4 px (Raster, Zellen), sm 6 px (Knöpfe, Felder, Hinweise), normal 8 px (Karten, Tabellen), lg 12 px (Dialoge), Pille 999 px nur für Badges und Chips. [unklar: Die Token-Übersicht nennt 8 px auch für Felder, das Designhandbuch 6 px; Festlegung Neubau: Felder 6 px.] Schatten klein/normal/groß nur für Ebenen über dem Inhalt (Menüs, Dialoge). Übergänge 120 ms.
  - Abnahme: Ein Stiltest erlaubt nur Abstandswerte der Skala und nur die genannten Radien; Karten und Tabellen haben keinen Schatten, Dialoge und Menüs schon; ein Übergang dauert 120 ms.

- **OBE-026 · P1 · Status: Ist** — Layoutmaße. Kopfzeile 56 px; Seitenleiste 248 px; eingeklappte Symbolleiste 64 px; untere Leiste am Handy 60 px; Steuerelement-Höhe 40 px; kleine Nebenaktion 32 px; Mindestgröße eines Touch-Ziels 44 px; Rasterzeile 64 px, kompakt 46 px; Seitenbreite schmal 760 px (Formulare, Profil), Standard 1400 px, breit 1680 px (Listen, Tabellen ab 1440 px); Lesebreite 72 Zeichen.
  - Abnahme: Messung der genannten Elemente bei den passenden Fensterbreiten ergibt die genannten Maße; auf einem Gerät mit grobem Zeiger sind Knöpfe, Felder, Reiter und Menüeinträge mindestens 44 px hoch.

- **OBE-027 · P1 · Status: offen** — Eine Hauptfarbe zentral. Primärfarbe, Primär-Hover, Primär-weich, Text auf Primärfarbe und Fokusfarbe bilden zusammen die Hauptfarbe und werden an genau einer Stelle gepflegt. Die Browser-Leistenfarbe (theme-color), die Logos und die Markenkonfiguration lesen von dort. Im Altbestand war sie an mehreren Stellen zu pflegen. Der Kontrast der Hauptaktion auf Text beträgt mindestens 4,5:1 in beiden Schemata.
  - Abnahme: Eine Änderung der Primärfarbe an der zentralen Stelle ändert Knöpfe, Links, aktive Reiter, Fokus, Browser-Leistenfarbe und Logo-Akzent gemeinsam; der Token-Test bleibt grün oder schlägt bei Kontrastverlust fehl.

---

## 3. Bausteine-Katalog

Jeder Baustein ist einmal gebaut und überall wiederverwendet. Neue Seiten setzen sich aus diesen Bausteinen zusammen; ein zweiter Baustein für denselben Zweck ist nicht zulässig.

### 3.1 Dialoge und Bestätigungen

- **OBE-028 · P0 · Status: Ist** — Dialog-Grundgerüst. Modaler Dialog: Der Fokus bleibt im Dialog (Fokusfalle), Escape schließt (steht eine Hilfe offen, schließt Escape zuerst diese), beim Schließen kehrt der Fokus zum Auslöser zurück; der Hintergrund ist mit dem Overlay-Token abgedunkelt; der Dialog ist für Bildschirmleser als Dialog mit Titel gekennzeichnet. Kopfzeile (Titel 18 px/600) und Fuß bleiben sichtbar, nur der Inhalt scrollt. Fuß: rechts „Abbrechen“ und die Hauptaktion. Radius 12 px. Am Handy volle Breite und volle Höhe. Seitenpanels (Bearbeiten, Anlegen) folgen derselben Regel.
  - Abnahme: Mit der Tab-Taste verlässt der Fokus den Dialog nie; Escape schließt und der Fokus steht wieder auf dem auslösenden Knopf; bei 390 px füllt der Dialog das Fenster, bei langem Inhalt bleiben Kopf und Fuß sichtbar; ein Screenreader meldet „Dialog“ mit Titel.

- **OBE-029 · P0 · Status: Ist** — Bestätigungsdialog im App-Stil. Titel, Text, „Abbrechen“ und genau eine Hauptaktion, deren Beschriftung die Folge nennt („Klasse löschen“, nicht „OK“; keine Ja/Nein-Knöpfe). Gefahr-Variante (rot) für Löschen und nicht umkehrbare Aktionen. Mehrere Abfragen laufen nacheinander über einen zentralen Host, nie übereinander. Abmelden fragt „Möchten Sie sich abmelden?“ und meldet nur das aktive Konto ab.
  - Abnahme: „Klasse löschen“ öffnet einen Dialog mit rotem Hauptknopf „Klasse löschen“ und „Abbrechen“; zwei fast gleichzeitig ausgelöste Abfragen erscheinen nacheinander; „Abbrechen“ ändert nichts; der Abmelde-Dialog hat die Knöpfe „Abbrechen“ und „Abmelden“.

- **OBE-030 · P1 · Status: Ist** — Texteingabe-Dialog. Eingabe im App-Dialog statt Browser-Eingabe; Abbruch liefert keine Eingabe; Passwort- und Token-Eingaben nutzen das Passwortfeld (OBE-050).
  - Abnahme: Die Mail-Passwort-Eingabe erscheint als Dialog mit verdecktem Feld; „Abbrechen“ speichert nichts und liefert keinen Wert an den Aufrufer.

- **OBE-031 · P0 · Status: Ist** — Bestätigung durch Eintippen. Bei Löschen mit Datenverlust (Jahrgang mit Klassen, Klasse mit Stundenplan-Folgen) nennt der Dialog die Folgen als Liste und verlangt das Eintippen des Namens; beim sofortigen Löschen nach Datenschutz muss die Kennung oder der Benutzername exakt eingegeben werden; im Anbieter-Portal (BET) verlangen Kündigen und Sofortsperre den Schulnamen. Die Hauptaktion bleibt bis zur exakten Eingabe deaktiviert.
  - Abnahme: Bei „Jahrgang 7 löschen“ mit zwei Klassen zeigt der Dialog „Klassen: 7a, 7b“ und die Stundenplan-Folgen; mit abweichendem Text bleibt der Knopf deaktiviert; mit exaktem Namen wird er aktiv.

- **OBE-032 · P0 · Status: Ist** — Änderungsbestätigung bei Konflikt (409). Antwortet der Server mit 409, zeigt ein Dialog die Liste der betroffenen Änderungen (Beispiel: „Kurs M 5a: Woche 2 → entfällt“). Übernommen wird nur nach ausdrücklicher Bestätigung; ein stilles Wiederholen mit Erzwingen gibt es nicht. Das gilt für jede Bestätigungsabfrage der Vertretung und der Planung.
  - Abnahme: Eine Abwesenheit, die einen Konflikt erzeugt, öffnet den Dialog mit der Änderungsliste; erst „Übernehmen“ sendet die Bestätigung; „Abbrechen“ lässt den Plan unverändert.

- **OBE-033 · P0 · Status: Ist** — Ungespeicherte Änderungen. Eine Leiste „Ungespeicherte Änderungen · Speichern · Verwerfen“ erscheint, sobald Eingaben abweichen; beim Verlassen von Seite oder Reiter fragt ein App-Dialog (kein Browser-Popup). Nachrichten werden bei Seitenwechsel automatisch als Entwurf gespeichert (Hinweis „Entwurf gespeichert“; Chats haben keine Entwürfe). Entwürfe in Planung und Einstellungen gehen beim Reiterwechsel nicht verloren; jeder Abschnitt speichert für sich.
  - Abnahme: Feld ändern, Reiter wechseln → App-Dialog mit „Speichern“, „Verwerfen“, „Abbrechen“; eine angefangene Nachricht ist nach Seitenwechsel und Rückkehr als Entwurf vorhanden und die Meldung „Entwurf gespeichert“ erschien; in der Planung gehen Eingaben beim Reiterwechsel nicht verloren.

- **OBE-034 · P1 · Status: Ist** — Rückgängig-Leiste. Nach Aktionen mit Rückgängig-Möglichkeit erscheint 20 Sekunden lang eine Leiste über den Knöpfen; die Seite hält unten Platz frei, sodass kein Knopf verdeckt wird (Auslöser war ein Handy-Fehler, bei dem die Leiste „Einreichen“ verdeckte). Das Rückgängigmachen im Verlauf zeigt vorher, welche weiteren Änderungen mitgehen. [offen: Anzeige der mitgehenden Änderungen ist im Altbestand nicht umgesetzt.]
  - Abnahme: Nach „Plan leeren“ steht 20 s lang eine Rückgängig-Leiste; bei 390 px bleibt der unterste Knopf der Seite sichtbar und anklickbar; „Rückgängig“ im Verlauf listet vor Ausführung alle mitzurückgesetzten Änderungen.

- **OBE-035 · P0 · Status: Ist** — Konto- und Abmelde-Dialoge. Das Benutzermenü bietet Kontowechsel über alle in diesem Browser angemeldeten Konten, „Weiteres Konto anmelden“ (Fenster über der Seite mit Zurück/Abbrechen, kein Sprung zur Startseite) und „Abmelden“. Ein Abmelden-Knopf sitzt zusätzlich fixiert unten in der Seitenleiste und im Handy-Menü. Die Seite „Sie sind abgemeldet.“ zeigt noch gültige Konten („Weiter als …“, × je Konto, „Mit anderem Konto anmelden“); ohne weitere Konten geht es direkt zur Anmeldung; es gibt keinen automatischen Sprung in ein anderes Konto. Abgemeldete Konten zeigen keine Daten mehr, auch nicht über „Zurück“. Kontowechsel mischt keine Daten (siehe OBE-016).
  - Abnahme: Mit einem Eltern- und einem Lehrerkonto parallel angemeldet: Wechsel zeigt jeweils nur die Daten des aktiven Kontos; Abmelden des einen lässt das andere angemeldet; „Zurück“ nach dem Abmelden zeigt keine Fachdaten.

### 3.2 Meldungen, Zustände, Live-Aktualisierung

- **OBE-036 · P0 · Status: Ist** — Meldungen (Toasts). Kurzmeldungen mit Art (Erfolg, Hinweis, Fehler). Fehlermeldungen zeigen die Ursache. Am Handy erscheinen sie über der unteren Leiste. Sie sind für Bildschirmleser eine Live-Region. Bei Abmeldung und Kontowechsel werden alle offenen Meldungen geleert. 403-Meldungen enthalten „Keine Berechtigung“ nur einmal. Fehlermeldungen und Meldungen mit Handlungsbedarf verschwinden nicht von selbst, sondern bleiben bis zum Schließen (WCAG 2.2.1); Erfolgsmeldungen verschwinden von selbst [unklar: Anzeigedauer nicht in den Quellen].
  - Abnahme: Ein Fehler-Toast bleibt stehen, bis er geschlossen wird; ein Screenreader liest einen neuen Toast vor, ohne den Fokus zu verschieben; nach Kontowechsel ist kein Toast des Vorkontos sichtbar; ein 403 zeigt „Keine Berechtigung“ genau einmal.

- **OBE-037 · P1 · Status: Ist** — Hinweisleiste (Alert). Nur für echte Zustände: Fehler, Warnung, Erfolg, wichtige Information; kurzer Titel, optionaler Text; Statusfarben aus OBE-021 mit Wort oder Zeichen. Keine Hinweisbox als Dauer-Erklärtext (OBE-003).
  - Abnahme: Jede der vier Arten ist mit Titel dargestellt, erfüllt 4,5:1 und trägt ein Wort oder Zeichen; ein Hinweis ohne zugrunde liegenden Zustand wird im Review abgelehnt.

- **OBE-038 · P1 · Status: Ist** — Leerzustand. Kurzer Titel („Keine Vertretungen“), optional eine Aktion („Abwesenheit erfassen“). Kein Erklärabsatz, keine großen Illustrationen. Beispiele fester Texte: „Für diesen Zeitraum ist noch kein Stundenplan festgelegt.“ (mit Zeitraum), „Noch nicht hinterlegt“ (Impressum, Datenschutz).
  - Abnahme: Ein leerer Vertretungstag zeigt „Keine Vertretungen“ und, mit Recht `substitution.edit`, den Knopf „Abwesenheit erfassen“; ohne das Recht fehlt der Knopf; kein Absatz länger als der Titel.

- **OBE-039 · P1 · Status: Ist** — Ladezustand. Die Ladeanzeige erscheint im betroffenen Bereich, nicht seitenweit. Bei Aktionen zeigt der Knopf einen Ladezustand. Lange Vorgänge zeigen einen Fortschrittsbalken „x von y erledigt“. Bei „Bewegung reduzieren“ läuft der Spinner langsam bzw. statisch.
  - Abnahme: Beim Nachladen einer Kachel bleibt der Rest der Seite bedienbar; „Speichern“ zeigt während der Anfrage einen Ladezustand; ein Import zeigt „12 von 40 erledigt“.

- **OBE-040 · P0 · Status: Ist** — Fehlerzustand und Fehlergrenze. Ein Ladefehler zeigt die Ursache in einem Satz und den Knopf „Erneut versuchen“. Bei fehlender Berechtigung nennt die Meldung die fehlende Berechtigung mit ihrem Kurznamen aus dem Rechte-Katalog. Ein Fehler in einer Seite oder Kachel bricht nicht die Anwendung ab (Fehlergrenze je Bereich); „Keine Berechtigung“ erscheint im App-Rahmen mit Menü und Rückweg, nicht als leere Seite. Unbekannte Adressen zeigen die 404-Seite, nicht 403.
  - Abnahme: Ein erzwungener Fehler in einer Startseiten-Kachel lässt alle anderen Kacheln und das Menü funktionieren; ein Aufruf einer Seite ohne Recht zeigt „Keine Berechtigung“ im App-Rahmen; eine unbekannte Adresse zeigt „nicht gefunden“.

- **OBE-041 · P0 · Status: Ist** — Fehlermeldungen für Menschen. Alle bekannten Fehlercodes des Servers haben einen deutschen Klartext (Übersetzungstabelle; ein Test fordert einen Eintrag für jeden neuen Code). Validierungsfehler (fehlt, ungültiges Datum, zu lang, außerhalb des Bereichs, falscher Typ) werden auf die Beschriftung des Feldes abgebildet statt auf technische Pfade („body.date_from“). Technische oder englische Servertexte werden durch eine allgemeine Meldung ersetzt. Nie Codes, Pfade, interne IDs. Beispiel: `POST` ohne Datum zeigt „Bitte ein Startdatum angeben.“ am Feld.
  - Abnahme: Ein Test sendet die zehn häufigsten Fehlertypen und prüft deutschen Text am richtigen Feld; ein neuer Servercode ohne Übersetzung lässt den Test fehlschlagen; die Oberfläche zeigt nie „Field required“.

- **OBE-042 · P1 · Status: Ist** — Fehlernummer und Zeitgrenzen. Unerwartete Fehler zeigen „Das hat nicht geklappt“ mit einer Fehlernummer (die ersten 8 Zeichen der Anfrage-ID in Großbuchstaben) für den Support. Jede 500-Antwort trägt eine Anfrage-ID in Antwort und Protokoll, auch bei Datei-Uploads (im Altbestand fehlte sie dort). Zeitgrenze im Browser 30 Sekunden mit der Meldung „Der Server antwortet nicht rechtzeitig“; Uploads, Sicherungen, Importe und der Plan-Generator 5 Minuten.
  - Abnahme: Ein erzwungener 500-Fehler zeigt die achtstellige Fehlernummer, die im Serverprotokoll wiederzufinden ist (auch bei Upload); ein künstlich verzögerter normaler Aufruf meldet nach 30 s die Zeitüberschreitung, ein Upload erst nach 5 min.

- **OBE-043 · P1 · Status: Ist** — Statusabzeichen, Badge, Chip. Text und Kurzzeichen, nie nur Farbe; Pillenform (999 px) nur für Badges und Chips; sie enthalten Status oder Kürzel, keine Sätze. Entfernen-Kreuze an Chips haben eine Trefferfläche von mindestens 44 px (Handy), die Zeile wird dadurch nicht höher.
  - Abnahme: Auf einem Touch-Gerät lässt sich das Kreuz eines Chips in 44 × 44 px treffen; kein Badge enthält mehr als ein Kürzel oder ein Wort.

- **OBE-044 · P1 · Status: Ist** — Zähler. Zähler stehen am Menüeintrag und an der Glocke; ab 100 erscheint „99+“. Menüzähler sind klein und werden beim App-Start geladen. Zähler gibt es für: ungelesene Nachrichten, offene Formulare, offene Anträge, neue Kursraum-Inhalte, Planvorschläge, Nachschreibtermine, offene Dokumente und fehlende Atteste, Anmeldetätigkeiten (Beobachtete Konten). Ein gemeinsamer Zähler für Nachrichten umfasst Chats, Gruppen, Briefe, E-Mails und Mitteilungen.
  - Abnahme: 100 ungelesene Nachrichten zeigen „99+“; ein Zähler fehlt, wenn die Person das Recht der Seite nicht hat; ein neuer Planvorschlag erhöht den Zähler ohne Neuladen.

- **OBE-045 · P1 · Status: Ist** — Live-Aktualisierung. Listen und Zähler aktualisieren sich über eine Ereignisverbindung (Server-Sent Events, `/api/v1/events`) ohne Neuladen. Ein Ereignis nennt Bereiche und einen Datumsbereich; ein Ereignis ohne Bereich lädt alles neu. Die Verbindung baut sich bei Abbruch mit wachsender Wartezeit automatisch neu auf; eine Zeitgrenze ohne Ereignisse löst eine Neuverbindung aus [unklar: Zeitgrenze und Wartezeiten nicht in den Quellen]. Der Verbindungsstatus ist in der Kopfzeile als Live-Anzeige sichtbar. Ohne Verbindung fragt die Oberfläche periodisch ab (Glocke einmal pro Minute, Monitor alle 120 Sekunden). Die Live-Anzeige ist eine Anzeige mit definiertem Verhalten bei Klick (Kapitel 17, Punkt 4).
  - Abnahme: Verbindung unterbrechen: die Live-Anzeige wechselt auf „getrennt“ und die Glocke fragt nach 60 s selbst ab; Verbindung wiederherstellen: die Anzeige wechselt zurück; eine Vertretungsänderung durch ein anderes Konto erscheint ohne Neuladen.

- **OBE-046 · P1 · Status: Ist** — Lizenzhinweis und Sperrseite. Die Hinweisleiste zum Lizenzablauf erscheint nach der Kulanzzeit für alle, die Vorwarnung nur für Personen mit `license.manage`. Ist die Lizenz gesperrt, ersetzt eine Sperrseite die gesamte Anwendung; bei einer frischen Instanz ohne Lizenzschlüssel erscheint eine Begrüßung statt der Sperre (Details BET).
  - Abnahme: Mit gesperrter Lizenz zeigt jeder Aufruf nur die Sperrseite; eine frische Instanz ohne Schlüssel zeigt die Begrüßung; die Vorwarnung erscheint für ein Konto mit `license.manage`, nicht für eine Lehrkraft.

### 3.3 Formulare und Eingaben

- **OBE-047 · P0 · Status: Ist** — Beschriftetes Feld. Aufbau: Beschriftung (Substantiv, höchstens 3 Wörter, ohne Doppelpunkt; Zusatz „(optional)“ oder Pflicht „\*“), Steuerelement, Hilfe an der Beschriftung (Kapitel 8), Fehlertext darunter. Eine Fehlermeldung erscheint erst, nachdem die Person etwas getan hat. Nach dem Absenden erscheint der Fehler am Feld und zusätzlich als Meldung, wenn das Feld nicht im Blick ist; der Fokus springt auf das erste fehlerhafte Feld. Fehlertext und Feld sind programmatisch verknüpft (ungültig-Kennzeichen, beschreibende Verknüpfung).
  - Abnahme: Leeres Pflichtfeld unberührt: kein Fehler; nach „Speichern“: Fehlertext unter dem Feld, Fokus auf dem Feld, Screenreader liest Beschriftung und Fehler; ist das Feld außerhalb des sichtbaren Bereichs, erscheint zusätzlich eine Meldung.

- **OBE-048 · P1 · Status: Ist** — Formular-Layout. Pflichtfelder zuerst, Seltenes unter „Erweitert“ (aufklappbar). Zusammengehöriges steht in einer Gruppe mit Titel (Feldgruppe mit Legende). Spalten ab 220 px Breite, am Handy einspaltig. Seitencontainer für Formulare und Profil schmal (760 px). Hauptaktion rechts unten im Dialog bzw. am Formularende.
  - Abnahme: Bei 390 px stehen Felder einspaltig; bei 1440 px ist ein Formular nicht breiter als 760 px; die „Erweitert“-Gruppe ist zugeklappt und per Tastatur aufklappbar.

- **OBE-049 · P0 · Status: offen** — Fehler am richtigen Feld, überall. Serverfehler werden dem richtigen Feld in verständlichen Worten zugeordnet; Fehler, die kein Feld betreffen, stehen oben am Formular. Der Altbestand hatte den Baustein, setzte ihn aber in keinem Formular ein; im Neubau ist er Pflicht in jedem Formular und Dialog mit Eingaben.
  - Abnahme: Ein Test-Durchlauf je Formular mit absichtlich ungültigen Werten zeigt in 100 % der Formulare den Fehlertext am Feld; ein Formular ohne Fehlerzuordnung lässt die Prüfung scheitern.

- **OBE-050 · P0 · Status: offen** — Passwortfeld und Anmeldeformulare. Passwortfeld mit Knopf zum Ein- und Ausblenden (Ist, 19 Verwendungen). Zusätzlich Pflicht im Neubau: Anmeldeformulare sind für Passwort-Manager eindeutig (Benutzername- und Passwortfeld mit passenden Eingabe-Hinweisen für aktuelles Passwort, neues Passwort und Einmalcode); Einfügen in Passwort- und Codefelder ist erlaubt; das Benutzernamenfeld schaltet automatische Großschreibung und Autokorrektur aus (Handy macht sonst Großbuchstaben); die Passwortregeln (Mindestlänge usw.) kommen vom Server, nicht aus der Oberfläche.
  - Abnahme: Ein Passwort-Manager füllt die Anmeldeseite und die Seite „Neues Passwort“ korrekt; Einfügen per Tastatur und Kontextmenü funktioniert; auf einem Handy erscheint der Benutzername klein geschrieben; die angezeigte Mindestlänge entspricht der Serverantwort.

- **OBE-051 · P1 · Status: Ist** — Auswahl mit Suche. Combobox: Treffer sind auf höchstens 60 begrenzt; Mehrfachauswahl als Chips mit Suchfeld; Pfeiltasten und Escape; Beschriftung. „Fach hinzufügen“: ein Knopf, darunter eine durchsuchbare Liste, unten „Neues Fach anlegen …“ (Recht `masterdata.edit`) mit Kürzel-Vorschlag (Informatik → INF); ein neues Fach startet mit 2 Wochenstunden; Hauptfach und Farbe unter „Mehr Optionen“.
  - Abnahme: Mit 500 Einträgen zeigt die Liste höchstens 60 Treffer; „Informatik“ eintippen bietet „Neues Fach anlegen …“ mit Kürzel „INF“ an; ohne `masterdata.edit` fehlt dieser Eintrag.

- **OBE-052 · P1 · Status: Ist** — Kürzel mit Sprechblase. Überall, wo ein Kürzel steht (Lehrkraft, Fach, Raum, Klasse, Standort), zeigt eine Sprechblase den vollen Namen: bei Hover mit Verzögerung, bei Fokus/Tastatur, auf Touch bei Tippen oder Langdruck. In Listen wie „MÜL, SCH“ gilt sie je Kürzel. Schüler/innen und Eltern erhalten Namen nur aus ihrem eigenen Stundenplan. Keine Sprechblase im Monitor, in Auswahllisten und im Druck. Platzhalter für Personen sind neutral („Frau Muster“).
  - Abnahme: Hover auf „MÜL“ im Stundenplan zeigt den vollen Namen; Tipp auf Touch öffnet sie; für ein Schüler-Konto zeigt ein fremdes Kürzel keinen Namen; im Monitor und in der Druckansicht gibt es keine Sprechblasen.

- **OBE-053 · P1 · Status: Ist** — Empfängerwahl. Adressbuch nur mit erlaubten Personen (Rechte NAC), Gruppen nur mit Recht (Rundschreiben `messages.broadcast`), freie E-Mail-Adressen, Anzeige als Chips, Felder An, CC, BCC (BCC-Empfänger sieht nur der Absender).
  - Abnahme: Ein Schüler-Konto findet im Adressbuch keine Mitschüler, wenn die Schule es nicht erlaubt; ohne `messages.broadcast` bietet die Auswahl keine Gruppen an.

- **OBE-054 · P1 · Status: Ist** — Eingabezeile wie im Messenger. Betreiber (12.10.2026): „eine Linie machen, die wirklich durchgehend ist“, links ein Plus für Dateien, rechts ein Sende-Pfeil. Die Zeile wächst mit dem Text; Anhänge per Einfügen, Ziehen (nur am PC) oder Auswahl mit Vorschauleiste; der Emoji-Knopf nur am PC (am Handy über die Tastatur). Am PC sendet Enter, Umschalt+Enter macht eine neue Zeile; am Handy macht Enter eine neue Zeile und gesendet wird über den Pfeil. Es gibt keine Tastatur-Erklärungen. Einstellungen (Archiv, Stummschalten, Mitglieder und Rechte, Details, Geräte und Schlüssel) liegen hinter dem Zahnrad oben rechts („Das ist ein bisschen viel für so eine kleine Oberfläche“, 12.10.2026). Doppelsenden (Doppelklick, Wiederholung) liefert dieselbe Nachricht (Sendeschlüssel je Absendevorgang).
  - Abnahme: Bei 390 px besteht die Zeile aus einer durchgehenden Linie mit „+“ links und Pfeil rechts; Enter sendet am PC, am Handy erzeugt es eine neue Zeile; ein Doppelklick auf den Pfeil sendet genau eine Nachricht.

- **OBE-055 · P1 · Status: Ist** — Dateiablage. Ziehen und Ablegen (der Hinweis „hierher ziehen“ nur am PC) oder Auswahl; mehrere Dateien nacheinander; Fortschritt; Abbruch; Vorprüfung von Größe und Endung im Browser vor dem Hochladen; Anzeige des Kontingents; die erlaubten Dateiarten werden genannt. Ordner-Upload bewahrt Pfade und lässt versteckte und Systemdateien aus. Solange Uploads laufen, fragt ein App-Dialog beim Seitenwechsel und der Browser beim Tab-Schließen nach. Dateiliste: Name als Download, „Ansehen“ nur für PDF und Bilder, Größe, Art, Datum. Größenlimits und erlaubte Arten legen KUR/FOR fest.
  - Abnahme: Eine zu große Datei wird vor dem Hochladen mit Größe und Limit abgelehnt; ein laufender Upload wird beim Seitenwechsel mit App-Dialog bestätigt; ein hochgeladenes SVG hat nur „Herunterladen“, kein „Ansehen“.

- **OBE-056 · P1 · Status: Ist** — Zeit- und Codefelder. Zeitfelder nehmen Ortszeit (Zeitzone Europe/Berlin) an und speichern UTC; Fristvorschlag („in N Tagen um Uhrzeit“). Das 6-stellige Codefeld übernimmt beim Einfügen nur Ziffern und erlaubt am Handy den Vorschlag des SMS-Codes. Ein Kopierfeld zeigt Werte (Zugangsdaten, Codes) mit Kopierknopf.
  - Abnahme: Das Einfügen von „Code: 123 456“ ergibt „123456“; eine Frist um 23:30 Ortszeit wird als UTC gespeichert und wieder als 23:30 angezeigt (auch im Sommer); der Kopierknopf legt den Wert in die Zwischenablage.

- **OBE-057 · P2 · Status: Ist** — Emoji-Auswahl. Kategorien, Suche, zuletzt verwendet (im Gerät gespeichert), Einfügen an der Cursorposition; ein einzelnes Emoji wird größer dargestellt; zusammengesetzte Zeichen (Familien-Emoji) werden nicht auseinandergerissen. Nur Unicode-Zeichen, nichts wird nachgeladen.
  - Abnahme: Ein Familien-Emoji bleibt beim Einfügen und Löschen ein Zeichen; die Auswahl erzeugt keine Netzwerkanfrage.

- **OBE-058 · P1 · Status: Ist** — Umschalter, Reiter, Stufenauswahl, Chips. Segment-Umschalter und Reiter folgen WAI-ARIA mit Pfeiltasten; eine Reihe Chips (z. B. Wochen 1 bis n) ist eine Tab-Station mit Pfeiltasten; Tages-Chips Mo bis So tragen für Bildschirmleser die vollen Namen. Reiter: höchstens eine Reihe, am Handy waagerecht scrollbar innerhalb der Leiste. Stufenauswahl: 2 bis 5 gleichrangige Optionen nebeneinander.
  - Abnahme: Mit der Tab-Taste betritt man die Reiterleiste einmal und wechselt mit Pfeiltasten; ein Screenreader liest „Montag“ statt „Mo“; die Reiterleiste verbreitert bei 390 px die Seite nicht.

- **OBE-059 · P1 · Status: Ist** — Wochen- und Datumsbausteine. Wochennavigation: Pfeile, Heute-Knopf, Anzeige „Woche n · KW · Zeitraum“. Wochenangabe-Editor: „Jede Woche“, „Ausgewählte Wochen“ oder „Rhythmus“ (alle k Wochen ab Woche s bis Woche e); bei regelmäßigem Abstand schlägt er einen Rhythmus vor und übernimmt ihn nie automatisch. Datumsnavigation: vorheriger und nächster Schultag (Ferien werden übersprungen), Heute, Datumsfeld; „Heute“ ist am Wochenende sinnvoll belegt. Wochen erscheinen nur als Zahl, Liste oder Rhythmus, nie als Buchstabe. [unklar: Woche 1 bis 52 oder 1 bis 53 – der Altbestand nennt 52, der Entwurf des Kalenders 53.]
  - Abnahme: „Nächster Schultag“ vom 16.10.2026 springt auf den ersten Schultag nach den Ferien; eine Kurswoche 27 erscheint als „27“, nie als Zeichen; der Editor schlägt für 1, 3, 5, 7 den Rhythmus „alle 2 Wochen ab 1“ vor und übernimmt ihn erst nach Klick.

- **OBE-060 · P2 · Status: offen** — Editoren für Verfügbarkeit, Regeln und Zeitraster. Der Verfügbarkeitseditor ist ein Raster zum Antippen für Arbeitszeit, Sperrzeiten und Wünsche in einer Bedienung, mit Rhythmus und Schnellvorlagen für typische Arbeitszeiten. Der Regel-Editor (Sperr- und Rhythmusregeln) arbeitet mit Wochen, Tagen, Stunden und einem Satzbaukasten („Jeden [1.] [Mittwoch] im [Monat] → nicht verfügbar“, „Alle [2] Wochen ab [Datum] erst ab [10:00]“) mit Klartext-Zusammenfassung und einer Vorschau über acht Wochen. Der Zeitraster-Editor erfasst Stunden, Beginn, Länge, Pausen, mit Vorlagen und einem Rechner (Beginn 7:50, 7:55, 8:00 oder frei; Stundenlänge 45, 60 oder frei; Live-Tabelle der Uhrzeiten). Beispiele des Betreibers als Abnahmefälle: „jeden 1. Mittwoch im Monat“, „jede 3. Woche nicht“, „alle 2 Wochen erst ab 10“, „mittwochs nie nach 12“, „erst ab 9“. Fachregeln: STP, LEH.
  - Abnahme: Alle fünf Beispiele lassen sich im Satzbaukasten und im Raster ohne Formularfelder voller Umschalter eingeben, werden als Klartext zusammengefasst und zeigen in der Acht-Wochen-Vorschau die richtigen Wochen; das Raster ist per Tastatur und am Handy als Tagesliste bedienbar.

- **OBE-061 · P1 · Status: Ist** — Tabellen-Eingabe und CSV-Zuordnung. Einfügen aus Tabellenkalkulation, Word oder CSV (Trennzeichen wird erkannt; Listen-Trenner `,` `;` `|`), Serien („5a–5d“) werden ausgeschrieben, Enter erzeugt die nächste Zeile, Fehlerzeilen sind rot markiert und erklärt (lange Fehlertexte brechen um); bei einem Fehler wird nichts gespeichert. CSV-Spaltenzuordnung: Vorschlag aus der Kopfzeile (exakter Vergleich, kein Teilstring-Treffer: „Geburtsort“ wird nicht „Geburtsdatum“), Vorlagen für typische Schulverwaltungsprogramme.
  - Abnahme: Das Einfügen von „5a–5d“ erzeugt vier Zeilen; eine Datei mit Spalte „Geburtsort“ ordnet sie nicht dem Geburtsdatum zu; eine Zeile mit Fehler verhindert das Speichern aller Zeilen und ist rot markiert.

- **OBE-062 · P1 · Status: Ist** — Assistenten-Muster. Mehrschritt-Abläufe (Einrichtung, Klassen-Assistent, Schuljahreswechsel, Import) zeigen Fortschritt, erlauben das Überspringen von Schritten und das spätere Fortsetzen („Einrichtung fortsetzen“; der Fortschritt wird gespeichert), bieten vor dem Ausführen Vorschau oder Probelauf (es wird nichts geändert) und beim Schuljahreswechsel Ausführen nur nach Vorschau sowie Rückgängig, solange der Plan nicht weiter geändert wurde. Die Startseite zeigt offene Einrichtungsschritte.
  - Abnahme: „Ausführen“ des Schuljahreswechsels ist ohne vorherige Vorschau nicht klickbar; ein übersprungener Einrichtungsschritt bleibt auf der Startseite als offen sichtbar; ein Probelauf des Klassen-Assistenten legt keine Konten an.

### 3.4 Tabellen und Listen

- **OBE-063 · P0 · Status: Ist** — Tabellen. Eigener Rahmen mit eigenem waagerechtem Scroll; die Seite scrollt nie wegen einer Tabelle; Zahlen rechtsbündig; Aktionen rechts; die Kopfzeile klebt oben. Große Bildschirme dürfen volle Seitenbreite nutzen (Tabelle breit, Fließtext daneben bleibt lesbreit). Die Aktionsspalte ist so breit wie die meisten Knöpfe einer Zeile; 0 Knöpfe blenden sie aus. Sortierung natürlich (5a vor 10a); „Ohne Jahrgang“ steht zuletzt.
  - Abnahme: Eine Tabelle mit 12 Spalten bei 390 px scrollt nur in ihrem Rahmen; „5a“ steht vor „10a“; „Ohne Jahrgang“ steht am Ende der Jahrgangsliste.

- **OBE-064 · P1 · Status: offen** — Kartenliste am Handy. Unter 600 px (599,98 px) werden Tabellen mit mehr als 4 bis 5 Spalten zur Kartenliste: je Zeile eine Karte, der Spaltenname steht links an jedem Wert. Alternativ zeigt die Tabelle wenige Spalten und der Rest steht in einer Detailansicht. Im Altbestand war der Baustein vorbereitet, aber nirgends eingesetzt.
  - Abnahme: Die Schülerliste mit 8 Spalten zeigt bei 390 px Karten mit „Spaltenname: Wert“-Paaren; bei 800 px dieselbe Liste als Tabelle; kein waagerechter Seitenscroll.

- **OBE-065 · P1 · Status: Ist** — Virtualisierte Tabelle. Die Tabelle rendert nur sichtbare Zeilen und bleibt bei über 5.000 Zeilen flüssig (Richtwert Altbestand: 2.626 Schüler/innen, rund 5.000 Konten). Zähler verwenden die richtige Mehrzahl („1 Eintrag“, nicht „1 Einträge“).
  - Abnahme: Eine Liste mit 6.000 Konten scrollt ohne spürbares Ruckeln (Bildrate bleibt im Messprotokoll bei mindestens 30 Bildern/s); die Zeilenzahl im DOM bleibt unter 200; „1 Eintrag“ erscheint korrekt.

- **OBE-066 · P1 · Status: Ist** — Listen, Filter und Suche. Listen können nach Tag gruppiert sein (Heute, Gestern, Diese Woche, Früher bzw. Datum). Listenelemente tragen einen farbigen Statusbalken links. Filter-Chips und Volltextsuche: alle eingegebenen Wörter müssen vorkommen, Suche nach Wortteilen; der Filter „Alle“ zeigt alles außer Archiviertem. Briefe werden nach Inhalt durchsucht, Chats nur nach Name (verschlüsselt). Filterleisten werden am Handy hinter einem Knopf „Filter“ eingeklappt, aktive Filter erscheinen als Chips [offen: Vorschlag vom 12.10.2026, vom Betreiber nicht freigegeben].
  - Abnahme: Suche „anna mat“ findet nur Einträge mit beiden Wortteilen; „Alle“ blendet Archiviertes aus; die Benachrichtigungsliste gruppiert in Heute, Gestern, Diese Woche, Früher.

- **OBE-067 · P2 · Status: Ist** — Spezialtabellen. Notentabelle: Pfeiltasten bewegen die Zelle; Kürzel e, a, n, u setzen den Status bei Zahlenskalen; am Handy Schnellwahl-Knöpfe. Heatmap Klasse × Kompetenzen: Anteil in Prozent, Farbstufen 1 bis 4, „nicht eingeschätzt“ gesondert, Filter „braucht Unterstützung“. Bewertungstabelle: Schüler/in × Status (abgegeben, verspätet, fehlt, bewertet, Überarbeitung) mit Punkten oder Note im Text.
  - Abnahme: In der Notentabelle bewegt sich der Fokus mit Pfeiltasten und die Taste „e“ setzt den Status; die Heatmap zeigt „nicht eingeschätzt“ mit eigener Darstellung und Text, nicht als Stufe 0.

- **OBE-068 · P2 · Status: Ist** — CSV-Export und Papierkorb-Liste. CSV mit Semikolon als Trenner (deutsche Tabellenprogramme) und Schutz vor Formeln in Zellen (Zellen, die mit =, +, -, @ beginnen, werden entschärft). Die Papierkorb-Liste zeigt die verbleibenden Tage bis zum endgültigen Löschen (Altbestand: 30 Tage).
  - Abnahme: Ein Name „=1+1“ erscheint im Export als Text und nicht als Formel; die Papierkorb-Liste zeigt „noch 29 Tage“ für eine gestern gelöschte Datei.

### 3.5 Fachbausteine

- **OBE-069 · P1 · Status: Ist** — Markdown-Darstellung. Sicher und ohne HTML (Überschriften, Listen, Tabellen, Codeblöcke, Zitate, Trennlinien, Anker). Links nur für http, https und mailto, öffnen in neuem Tab ohne Referrer. Formelsatz ist lokal gebündelt und wird erst bei Bedarf geladen. Verweise auf Beispieldateien erscheinen als Text, nicht als Link.
  - Abnahme: Ein Beitrag mit eingebettetem Skript-Tag zeigt den Text unwirksam; ein Link mit `javascript:` wird als Text dargestellt; Formeln laden keine fremde Quelle.

- **OBE-070 · P1 · Status: Ist** — Kursraum: Material und Sichtbarkeit. Material-Ordnerbaum mit Position; Sichtbarkeitswahl: sofort, verborgen, ab Zeitpunkt, zur nächsten Stunde, zur Unterrichtsstunde; Gruppen-Freigabe (nichts angekreuzt = für alle); Kopieren in einen eigenen Kursraum; Papierkorb-Dialog; Abschluss-Bedingungen als verschachtelter UND-/ODER-Baum mit Fortschrittsbalken „x von y erledigt“. Neues Material ist „neu“ markiert, bis es geöffnet wird. Fachregeln KUR.
  - Abnahme: Ein Material „zur nächsten Stunde“ erscheint für Schüler/innen erst mit dieser Stunde; ein Abschluss-Baum „A UND (B ODER C)“ zeigt „2 von 3 erledigt“, wenn A und B erledigt sind.

- **OBE-071 · P1 · Status: Ist** — Kursraum: Aufgaben und Bewertung. Bewertungsraster (Editor, Bewerten, Ansicht, Vorschau; Stufen mit Punkten oder Freitext mit Höchstpunkten); Versionsliste der Abgaben; Gruppenaufteilung (zufällig, alphabetisch, von Hand); „Frist verlängern“ mit Hinweis auf Nachteilsausgleich; Einstellungen (Bewertungsart, Notenschlüssel). Fachregeln KUR/NOT.
  - Abnahme: Das Bewertungsraster lässt sich anlegen, in der Vorschau ansehen und beim Bewerten verwenden; „Frist verlängern“ nennt den Nachteilsausgleich als Grund-Auswahl.

- **OBE-072 · P2 · Status: Ist** — Abstimmung, Umfrage, Selbsttest. Die Abstimmungskarte mit Balken sieht in Kursraum und Chat gleich aus. Testdurchführung mit Zeitlimit und Speicherung je Antwort; Fragensammlung mit Import und Export im GIFT-Format. Anzeige ehrlich: Teilnahme über Pseudonym statt Klarname bei Umfragen.
  - Abnahme: Dieselbe Abstimmung erscheint in Kursraum und Chat mit identischer Balkendarstellung; ein Selbsttest speichert jede Antwort sofort (Seite neu laden behält sie).

- **OBE-073 · P1 · Status: Ist** — Chat-Bausteine. Bilder werden verschlüsselt geladen und im Browser entschlüsselt; Klick vergrößert; Vorschauleiste vor dem Senden; höchstens 5 MB pro Bild, größere Fotos werden verkleinert. Geräte und Schlüssel: Gerät mit Kopplungscode oder QR-Code einrichten, Fingerabdruck vergleichen, Verlauf übertragen, Wiederherstellung mit Passwort, Warnung „Sicherheitsschlüssel von … hat sich geändert“. Chats funktionieren nur über HTTPS (oder localhost). Kryptografische Regeln: NAC, SIC.
  - Abnahme: Ein 8-MB-Foto wird vor dem Senden verkleinert; die Kopplung eines zweiten Geräts zeigt Code, QR-Code und Fingerabdruck; über HTTP (außer localhost) zeigt die Chat-Seite die Meldung, dass HTTPS nötig ist.

- **OBE-074 · P1 · Status: Ist** — Kennzahlen und Diagramme. Kennzahlen-Kachel: Wert, Titel, Einheit, Erklärung per Hover oder Antippen (Hilfe-Symbol), Klick öffnet die Liste dahinter (zum Beispiel „Hohlstunden Klassen“ öffnet die Liste der betroffenen Klassen). Diagramme (Balken, Säulen, Linien) tragen die Zahlenwerte direkt am Balken oder beim Darüberfahren; es gibt keine Werte-Tabelle neben dem Diagramm (Betreiber, 16.10.2026: „Warum wird die Tabelle extra in Wert dann gezeigt? Ich interessiere mich nicht.“); eine Tabelle existiert nur für Bildschirmleser. Mehrere Kennzahlen stehen als eine Leiste (OBE-002). Generator-Auswertung: „Kosten“ heißt „Strafpunkte (niedriger = besser)“ mit Hilfe-Symbol und Zusammensetzung in Klartext; Anteile unter 2 % erscheinen als „Übrige“.
  - Abnahme: Ein Balkendiagramm zeigt die Zahl am Balken; kein sichtbares Wertetabellen-Element; ein Screenreader erhält die Werte als Tabelle; ein Klick auf „Hohlstunden Klassen: 3“ öffnet die zugehörige Liste.

- **OBE-075 · P1 · Status: Ist** — Planungs-Bausteine. Stundentafel-Matrix (Fächer × Stundentafeln, Eingabe direkt in der Tabelle, geerbte Werte mit Abweichung gekennzeichnet). Planungsregeln als Bausteine mit Wichtigkeit (Aus, Nett, Wichtig, Sehr wichtig, Muss) als Stufenauswahl, Ausnahmen mit Gültigkeit (Jahrgang, Woche, Fach), Probelauf mit Kennzahlen aktuell gegen Entwurf, Vergleichstabelle der Varianten mit markierten besten Werten. Plan-Stände: speichern (Name, Notiz, Umfang), ansehen, mit dem aktuellen Plan vergleichen, wiederherstellen, löschen; „Plan leeren“ mit Bestätigung (der bisherige Stand bleibt im Verlauf). Fachregeln STP.
  - Abnahme: Die Regelseite zeigt je Baustein die fünf Stufen und eine Ausnahme mit Jahrgang und Wochenangabe; der Variantenvergleich markiert je Kennzahl den besten Wert und spricht keine Empfehlung aus.

- **OBE-076 · P2 · Status: Ist** — Kompetenzen und Notenbuch in der Oberfläche. Stufenbalken mit vier Farbstufen; Lernplan gegliedert in „diese Woche“, „nächste Wochen“, „ohne Woche“, „frühere Wochen (offen)“, „erledigt“; Abzeichen mit eingebauten Zeichnungen (kein Bild-Upload). Notenbuch: Notenfarbe nur zur Kennzeichnung (der Wert steht daneben), Gewichtsanteile, Leistungsbaum mit Einrückung; Dialoge Leistung, Leistungsarten, Einstellungen, Übernahme aus Quellen, Protokoll, Einzelwert, Person. Fachregeln NOT.
  - Abnahme: Der Lernplan zeigt die fünf Gliederungen in dieser Reihenfolge; eine rot gefärbte Note trägt immer den Zahlenwert und im Graustufenbild unterscheidbare Information.

- **OBE-077 · P1 · Status: Ist** — Eltern- und Krankmeldungs-Bausteine. Kinderauswahl (nur sichtbar bei mehreren Kindern; die Wahl gilt für Startseite, Krankmeldungen, Noten und Kursräume). Krankmeldung: großer Knopf „Für heute krank melden“ (Bestätigung im Knopf), „Mehrere Tage / später“ (von bis, Zukunft, optional Einzelstunden), „Beurlaubung beantragen“; der Attest-Hinweis steht unter dem Zeitraum („3 Schultage – Attest nötig“; die Schwelle kommt aus der Schuleinstellung); Reihenfolge der Seite in einer Spalte: 1 Melden, 2 Offen (nur wenn etwas fehlt, jeweils mit Upload), 3 Bisherige Meldungen (mit „Zurücknehmen“, Fehlzeitenübersicht, Dokumente), 4 Statistik; zwei druckbare Formulare unten (Entschuldigung, Beurlaubung). „Einreichen“ bleibt unten sichtbar, Hinweis „Erst die Datei hochladen, dann einreichen“. Der Hinweis für Minderjährige („Krankmeldungen können nur Erziehungsberechtigte oder volljährige Schülerinnen und Schüler abgeben.“) steht nur im Krankmeldungs-Dialog. Warnung in den Ferien: „Im gewählten Zeitraum sind Ferien“ mit Anzahl betroffener Einträge (bei keinem: „keine Stunden betroffen“). Fachregeln KLB, SCH.
  - Abnahme: Ein Elternkonto mit einem Kind sieht keine Kinderauswahl, mit zwei Kindern schon; ein Zeitraum über 3 Schultage zeigt den Attest-Hinweis (bei Schwelle 3); ein Zeitraum in den Ferien zeigt die Ferien-Warnung; bei 390 px bleibt „Einreichen“ sichtbar und nicht verdeckt.

- **OBE-078 · P1 · Status: Ist** — Zugangsbriefe-Seite. Zeigt je Stapel einen Ablauf-Countdown (60 Minuten ab Erzeugung), die Einträge, Downloads (Sammel-PDF, ZIP nur bei mehreren Briefen, einzeln) und den Versand an Schüler/in oder Eltern mit Sicherheitshinweis; ein abgelaufener Stapel liefert „410“-Verhalten (Meldung „Der Stapel ist abgelaufen“). Zugriff nur für die erzeugende Person oder Administration, sonst 404 (ANM, FOR).
  - Abnahme: Der Countdown zählt von 60:00 herunter; nach Ablauf zeigt die Seite die Abgelaufen-Meldung statt Daten; ein anderes Konto erhält 404.

### 3.6 Erweiterbarkeit der Oberfläche

- **OBE-079 · P2 · Status: offen** — Module. Erweiterungsmodule bringen eigene Seiten, Menüeinträge, Startseiten-Kacheln, Hintergrunddienste und Zähler mit. Seiten werden erst bei Bedarf geladen (Richtwert Altbestand: Start-Paket rund 100 KB gzip, Seiten als eigene Pakete); ein Modul darf Kernpfade nicht belegen; ein Fehler in einem Modul bleibt auf dieses begrenzt. Nicht gebuchte oder ausgeschaltete Module verschwinden aus Menü, Startseite und Schnittstelle (404); Ausschalten löscht keine Daten, Wiedereinschalten stellt sie wieder her (BET, Paket „Module ein und aus“).
  - Abnahme: Ein ausgeschaltetes Modul „Elternbriefe“ hat keinen Menüeintrag, keine Kachel, und seine API antwortet 404; nach Wiedereinschalten sind die Daten vorhanden; ein Modul mit eigenem Pfad „/login“ wird beim Start abgelehnt.

---

## 4. Das Tage-×-Stunden-Raster

Betreiber (12.10.2026): das Wochenraster wie der Stundenplan wird wiederverwendet, „quasi dieses Sheet, was wir eh schon haben“. Es gibt einen einzigen Raster-Baustein (OBE-008). Sein Inhalt wird angepasst, seine Gestalt nicht.

- **OBE-080 · P0 · Status: Ist** — Spalten (Tage). Kopf mit Name, Kürzel und Datum (voller Wochentag und Datum). Markierungen: Ferien, frei, heute, Trennlinie. Spuren für parallele Lehrkräfte oder Räume. Der Kopf ist anklickbar („ganzen Tag markieren“) in Editoren. Bei Ferien oder frei ist die Spalte ganztägig gefüllt. Die Wochentage stehen exakt über ihren Feldern. Es sind bis zu 7 Schultage möglich; Samstag und Sonntag erscheinen im Wochenraster nur bei Terminen [offen: im Altbestand teilweise].
  - Abnahme: Ein Raster mit 5 Schultagen und einem Ferientag zeigt den Ferientag ganztägig gefüllt; „heute“ ist markiert; die Spalten fluchten exakt mit den Zellen (Messung: Spaltenmitte Kopf = Spaltenmitte Zelle ±1 px); ein Klick auf einen Tageskopf markiert im Editor alle Zellen des Tages.

- **OBE-081 · P0 · Status: Ist** — Zeilen (Stunden). Je Zeile die Stunde („3. Std.“), die Uhrzeit, eine Pausenlinie nach der jeweiligen Stunde (Pausen sind eigene Zeilen bzw. Linien), Gruppenüberschriften. Der Zeilenkopf ist anklickbar („ganze Stunde markieren“). Die Zeitspalte bleibt links stehen, wenn das Raster waagerecht scrollt.
  - Abnahme: Bei waagerechtem Scroll bleibt die Zeitspalte sichtbar; die Pausenzeile steht zwischen der betreffenden Stunde und der folgenden; ein Klick auf den Zeilenkopf markiert alle Zellen der Stunde.

- **OBE-082 · P0 · Status: Ist** — Zelle. Eine Zelle hat Inhalt, Titel, den Zustand „blockiert“ (durchgehend schraffiert), eine Tonalität (frei, gut, mittel, schlecht, gedämpft, Konflikt, Wunsch), optional einen Heatmap-Wert von 0 bis 1 (Anteil) und einen Auswahlrahmen. Die ganze Zelle ist ein Knopf mit zugänglichem Namen (zum Beispiel „Montag, 3. Std., Mathematik, Raum 101, Vertretung“). Zellabstand 2 px, Zellrundung 4 px, Zeilenhöhe 64 px, kompakt 46 px (Tokens).
  - Abnahme: Das Raster rendert alle sieben Tonalitäten und einen Heatmap-Wert 0,35 in Hell und Dunkel; die Zugänglichkeitsprüfung liest für jede Zelle einen vollständigen Namen; Zeilenhöhe 64 px (normal) bzw. 46 px (kompakt) gemessen.

- **OBE-083 · P0 · Status: Ist** — Zellinhalt im Stundenplan. Kürzel bleiben in der Zelle; der Status ist mit Farbe und Text erkennbar. Hausaufgaben, Tests, Klausuren, Nachschreiben, Krankmeldungen und Abwesenheiten folgen einem einheitlichen System (Betreiber, 12.10.2026: „das soll alles einheitlich sein“) als Stunden-Abzeichen: Hausaufgabe, Test oder Klausur, Nachschreiben, Abwesenheit, Aufsicht; mehrere gleichartige werden zum Sammel-Abzeichen mit Zähler („HA 2“, „Klausur 2“, „Prüfungen 2“). Über dem Tag stehen keine Text-Chips („Test“, „Klausur“, „HA“) mehr; der Tageskopf zeigt nur Feiertagsname, ganztägige Termine, Pflichttermine und nicht Zuordenbares. Klausuren und Tests stehen in der echten Stunde; der Klausur-Block ersetzt die reguläre Stunde („Klausur M · statt Deutsch“), parallele Wahlkurse bleiben sichtbar; ein Klick führt in den Kursraum. Hausaufgaben hängen am Kurs; Fälligkeit an einem Tag mit Kursstunde: erste Stunde dieses Tages, sonst die letzte Stunde des Kurses vor dem Fälligkeitstag mit Hinweis „fällig Fr 16.10.“. Mehrere Abzeichen überdecken einander nicht. Fachregeln STP, KLB.
  - Abnahme: Ein Tag mit zwei Hausaufgaben zeigt ein Abzeichen „HA 2“ in der Zelle; der Tageskopf enthält keine Text-Chips; eine Klausur „M“ am Donnerstag erscheint in der Mathematikstunde (nicht im Tageskopf) als „Klausur M · statt Deutsch“, wenn sie eine Deutschstunde ersetzt; drei Abzeichen in einer Zelle sind alle lesbar.

- **OBE-084 · P1 · Status: Ist** — Überlagerung und Kopplung. Blöcke über mehrere Stunden oder Spuren (Doppelstunden, gekoppelte Kurse) werden als Überlagerung gezeichnet und beim Verschieben zusammen bewegt. Gekoppelte Kurse zeigen das Pop-over aus OBE-009, nicht Schraffur. Vertretung und Entfall sind farbige Rahmen (OBE-022).
  - Abnahme: Beim Verschieben einer Doppelstunde bewegen sich beide Zellen gemeinsam; der Zielrahmen ist grün (zulässig) oder rot (unzulässig); ein gekoppelter Kurs wird nicht schraffiert.

- **OBE-085 · P1 · Status: Ist** — Legende. Unter jedem Raster steht eine Legende mit denselben Farbfeldern wie das Raster, aus den Zustandsklassen; Farben Hell und Dunkel über Tokens.
  - Abnahme: Für jede im Raster verwendete Tonalität und Vertretungsart existiert ein Legendeneintrag mit Wort und identischem Farbfeld; ein Raster ohne Legende fällt im Review durch.

- **OBE-086 · P0 · Status: Ist** — Wochen als Grundlage. Die angezeigte Woche ist die Grundlage für Raster, Liste und Dialoge; welche Stunden stattfinden, entscheiden die Wochenregeln (jede Woche, ausgewählte Wochen oder Rhythmus). Anzeige-Indizes der sichtbaren Woche werden nie mit Rohdaten vermischt. Die Wochenanzeige lautet „Woche n · KW · Zeitraum“.
  - Abnahme: Ein Kurs mit „alle 2 Wochen ab Woche 1“ erscheint in Woche 1 und 3, nicht in 2 und 4; ein Dialog zur Stunde in Woche 3 meldet Woche 3 (nicht einen Rohindex).

- **OBE-087 · P0 · Status: offen** — Bearbeiten im Raster ohne Maus. Editoren (Antippen, Ziehen) nutzen einen eigenen Bearbeitungsmodus mit Zeigerereignissen (Maus, Touch, Stift). Jede Funktion, die Ziehen verlangt, hat eine Alternative ohne Ziehen (WCAG 2.2, 2.5.7): Block antippen und Zielzelle antippen, oder der Knopf „Verschieben nach …“; per Tastatur Pfeiltasten und Enter. Der Altbestand ermöglichte Verschieben nur per Maus (Pflichtpunkt der Welle 3). Hinweise nennen auf Touch-Geräten nur „antippen“ und „gedrückt halten“.
  - Abnahme: Eine Stunde lässt sich allein per Tastatur (Pfeiltasten, Enter) und allein per Touch (Antippen von Quelle und Ziel) verschieben; „Verschieben nach …“ bietet alle zulässigen Ziele als Liste; auf einem Touch-Gerät erscheint kein Text mit „Maus“, „Rechtsklick“, „Strg“ oder „ziehen“.

- **OBE-088 · P0 · Status: offen** — Tastaturbedienung des Rasters. Das Raster ist eine einzige Tab-Station; innen bewegen Pfeiltasten den Fokus von Zelle zu Zelle, Enter öffnet die Details bzw. wählt, Leertaste markiert in Editoren, Escape verlässt den Bearbeitungsmodus. Der Fokusrahmen (2 px) ist an jeder Zelle sichtbar. Die Zellen tragen korrekte Rollen und Zustände (keine Auswahlmarkierung an Zeilen als Tabellenzeile).
  - Abnahme: Mit nur der Tastatur kann man in einem Wochenraster jede Zelle erreichen, Details öffnen und den Fokus wieder zum Seitenmenü verlassen; ein Screenreader liest Zeile, Spalte und Zellinhalt; die Barrierefreiheitsprüfung meldet keine Rollenverstöße.

- **OBE-089 · P0 · Status: Ist** — Raster am Handy. Am Handy wird das Raster zur Liste (Tage untereinander, Karten); die Umschaltung Raster/Liste bleibt bedienbar (Betreiber, 11.10.2026: Ansichten Raster und Liste wiederherstellen, Karte „Mein Tag“ entfernen). Auf größeren Breiten scrollt das Raster waagerecht, die Zeitspalte bleibt stehen. Grenze: unter 600 px (599,98 px) Liste [unklar: der Altbestand nutzte 700 px für das Raster; Vereinheitlichung auf 600 px siehe Kapitel 17]. Die Tagesansicht auf 390 px erlaubt Wischen zwischen den Tagen, am Tablet steht die Woche [offen].
  - Abnahme: Bei 390 px zeigt der Stundenplan standardmäßig die Liste mit Umschalter; bei 800 px das Raster mit festgehaltener Zeitspalte; ein Wisch nach links wechselt auf den nächsten Tag.

- **OBE-090 · P1 · Status: offen** — Stunden-Details auf Antippen. Antippen oder Klicken einer Stunde öffnet Details: am PC als Einblendung, am Handy als Blatt von unten. Inhalt: voller Name der Lehrkraft, Fach, Raum, Status, Hausaufgabe, Klausurhinweise (die Kürzel bleiben in der Zelle). Kein Popup mit nur Kürzeln (Betreiber, 11.10.2026: Lehrkürzel „FIS“ durch vollen Namen ersetzen). Details gibt es auch ohne Planungsrecht, für Schüler/innen nur zu eigenen Stunden.
  - Abnahme: Tippen auf eine Stunde zeigt bei 390 px ein Blatt von unten mit vollem Namen, Raum und Status; für ein Schüler-Konto fehlen Angaben zu fremden Klassen.

- **OBE-091 · P1 · Status: Ist** — Wochenraster Klasse und Schüler/in. Tage ohne Unterricht erscheinen schmal und abgeblendet; ein Umschalter „Nur Unterrichtstage“ blendet sie aus. Der Wochen-Stundenplan der Klasse zeigt „findet nicht statt“ und Begleitungen. Kalenderwoche: Termine, Klausuren, Hausaufgaben und Abwesenheit als Blöcke oder kleine Zeichen in der Stunde; die Startseitenkarte hat eine eigene KW-Auswahl.
  - Abnahme: Mit aktivem Schalter „Nur Unterrichtstage“ fehlen Ferien- und freie Tage; die Startseitenkarte lässt sich unabhängig vom Stundenplan auf eine andere KW stellen.

- **OBE-092 · P1 · Status: Ist** — Variante Klassenbuch (Anwesenheit). Standardansicht „Woche (je Stunde)“ mit KW-Navigation, Raster Tage × Stunden mit Datum und Uhrzeit; jedes Kästchen zeigt Fach und Anwesenheit in Prozent mit Farbe grün/gelb/rot (Beispiel: „89 % – 5 Min. zu spät, offen“; krank = 0 %); Tipp für Details; Ferien, Entfall und kommende Stunden sind markiert. Zweite Ansicht „Durchschnitt im Zeitraum“. Begriff einheitlich „Anwesenheit“. Auf dem Handy: eine Karte je Schüler/in (Name, Anwesenheit, Notiz), „fehlt“ farbig; größere Tippflächen. Fachregeln KLB.
  - Abnahme: Eine Stunde mit 5 Minuten Verspätung zeigt „89 %“ gelb mit Wort; eine Krankmeldung zeigt „0 %“ rot mit Wort „krank“; bei 390 px erscheint das Klassenbuch als Kartenliste.

- **OBE-093 · P1 · Status: Ist** — Variante Aufsichten. Wochenansicht: Pause und Bereich gegen Tage, Standort je Bereich, Namen ausgeschrieben, Vertretung mit durchgestrichener Person. Tagesansicht am Handy: Karten je Pause, nach Standort gruppiert (statt eines Rasters mit 110 Knöpfen). Badges („heute Hauptstandort“, „wechselt“, krank), Zähler (offene Plätze, Vertretungen, Konflikte), Filter nach Standort und „nur meine“; es erscheinen nur echte Pausen (Unterricht davor oder danach am selben Standort). Betreiber (12.10.2026): „Ich verstehe überhaupt nicht wer wann welche Pause hat und wie und wo“ – die Darstellung muss das ohne Erklärung zeigen. Fachregeln VER.
  - Abnahme: Auf der Wochenansicht lässt sich für jede Pause und jeden Standort ohne weitere Klicks ablesen, wer Aufsicht hat; die Tagesansicht bei 390 px zeigt Karten je Pause gruppiert nach Standort; eine durch Vertretung ersetzte Person erscheint durchgestrichen neben der Vertretung.

- **OBE-094 · P1 · Status: Ist** — Weitere Verwendungen. Der Raster-Baustein ist die Grundlage für: Stundenplan (Klasse, Lehrkraft, Raum, Schüler/in), Klassenbuch (OBE-092), Verfügbarkeit der Lehrkräfte (Arbeitszeit, Sperrzeiten, Wünsche; OBE-060), Aufsichten (OBE-093), Klassen-Wochenplan, Fehlzeiten in Prozent je Stunde, Kursraum-Regelplan, Vorschauen (Regel-Editor, Plan prüfen, Abwesenheit), Kennzahlen-Heatmaps der Planung, Vertretungsplan in Rasterform. Jede neue Ansicht mit Tagen und Stunden wird so gebaut.
  - Abnahme: Eine Liste aller Seiten mit Tage-×-Stunden-Darstellung (Kapitel 6) ist deckungsgleich mit den Verwendungen des Raster-Bausteins; die Prüfung aus OBE-008 bestätigt es.

---

## 5. App-Rahmen, Navigation und Breakpoints

- **OBE-095 · P0 · Status: Ist** — App-Rahmen. Kopfzeile (56 px) mit Seitentitel, Live-Anzeige, Glocke, Farbschema-Umschalter und Benutzermenü (Initialen); Seitenleiste mit Menügruppen; Seitenkörper mit Lesebreite (72 Zeichen) und Seitenbreite. Genau ein Seitentitel (Ebene 1) je Seite; Überschriften in logischer Reihenfolge; der Dokumenttitel entsteht aus der Route (Format `[unklar: Format nicht in den Quellen]`; Festlegung Neubau: „Seitenname – Produktname“, Produktname aus der zentralen Konfiguration). Eine Sprungmarke „Zum Inhalt springen“ ist der erste fokussierbare Punkt.
  - Abnahme: Jede Seite hat genau ein `h1`; die Tab-Taste führt als Erstes zur Sprungmarke, die zum Hauptinhalt springt; der Dokumenttitel ändert sich je Route und enthält den konfigurierten Produktnamen.

- **OBE-096 · P0 · Status: Ist** — Breakpoints. Handy unter 600 px: Kopfzeile, untere Leiste, einspaltig, Seitenrand 16 px, Platz für die untere Leiste. Tablet 600 bis 1023 px: einklappbare Seitenleiste, eingeklappt als Symbolleiste (64 px), der Menü-Knopf klappt sie mit Beschriftungen über dem Inhalt auf; Raster 1 bis 2 Spalten. Laptop 1024 bis 1439 px: feste Seitenleiste (248 px), Seite bis 1400 px. Desktop ab 1440 px: feste Seitenleiste, Seite bis 1680 px, Text bis 72 Zeichen. Grenzen genau: 599,98 px, 1023,98 px, 1440 px. Es gibt keine weiteren Seitenbreiten-Grenzen im Stil; die Ausnahmen des Altbestands (800 px für die geteilte Ansicht, 1200 px für das Stundenplan-Layout) entfallen oder sind mit Begründung dokumentiert [unklar: Betreiber hat die Vereinheitlichung nicht bestätigt, siehe Kapitel 17].
  - Abnahme: Bei 599 px erscheint die untere Leiste, bei 600 px die Symbolleiste; bei 1023 px die einklappbare, bei 1024 px die feste Seitenleiste (248 px); bei 1440 px darf die Seite 1680 px breit werden; eine Suche in den Stilen findet nur diese drei Grenzen (plus dokumentierte Ausnahmen).

- **OBE-097 · P0 · Status: Ist** — Untere Leiste am Handy. Bis zu 4 wichtigste Ziele je Rolle in fester Reihenfolge (typisch: Start, Stundenplan, Vertretung, Nachrichten; je Rolle konfigurierbar) und „Menü“, das die vollständige Navigation ausklappt. Nicht erlaubte Ziele entfallen. Höhe 60 px. Das Menü öffnet über den Menü-Knopf; beim Öffnen geht der Fokus ins Menü, beim Schließen (Escape, Klick auf den Hintergrund, Seitenwechsel) zurück zum Auslöser. Meldungen erscheinen über der Leiste. Jede Seite des Verzeichnisses ist am Handy über die Leiste oder „Menü“ erreichbar.
  - Abnahme: Für ein Schüler-Konto zeigt die Leiste kein „Vertretung“; „Menü“ öffnet die vollständige Navigation, Escape schließt sie und der Fokus steht wieder auf „Menü“; eine Prüfung ruft jede Seite des Verzeichnisses bei 390 px über Leiste oder Menü auf.

- **OBE-098 · P1 · Status: Ist** — Menügruppen und Einträge. Die Seitenleiste ordnet Einträge in Gruppen in fester Reihenfolge: Alltag, Kommunikation (Nachrichten, Kursräume), Planung, Verwaltung, Konto (Zuordnung der Einträge in Kapitel 6). Ein Eintrag erscheint nur, wenn die Person das Recht der Seite hat; Eintrag und Seite nutzen dieselbe Regel (im Altbestand blieb unklar, ob ein Eintrag bei fehlendem Seitenrecht verschwindet; im Neubau verschwindet er). Die aktuelle Seite ist über das längste passende Adresspräfix markiert. Menüs sind per Pfeiltasten bedienbar. Menügruppen-Überschriften nutzen 12 px.
  - Abnahme: Ein Konto ohne `timetable.edit`, `timetable.generate` und `settings.edit` sieht keinen Eintrag „Planvorschläge“; auf `/klassen/5a` ist „Klassen“ markiert; Pfeiltasten wechseln zwischen Menüeinträgen.

- **OBE-099 · P1 · Status: Ist** — Benutzermenü. Initialen als Auslöser. Inhalt: Kontowechsel, „Hilfetexte immer anzeigen“ (Schalter, je Browser, nicht im Konto), Abmelden (mit Bestätigung), „Weiteres Konto anmelden“. Tastenkürzel an/aus [offen, siehe OBE-175].
  - Abnahme: Das Menü öffnet per Klick und Tastatur; der Schalter „Hilfetexte immer anzeigen“ zeigt danach unter jedem Feld mit Hilfe den Hilfetext als Text; nach Abmelden eines anderen Browsers bleibt die Einstellung dort unverändert.

- **OBE-100 · P1 · Status: offen** — Kopfzeilen-Elemente mit definiertem Verhalten. Live-Anzeige, Glocke und Farbschema-Umschalter sind anklickbar mit genau definiertem Verhalten: Glocke mit Zähler (auch am Handy); Tippen zeigt die letzten 10 Benachrichtigungen mit „Alle als gelesen“ und „Alle anzeigen und einstellen“; die Live-Anzeige nennt den Verbindungsstatus (OBE-045); der Umschalter wechselt zwischen hell, dunkel, System. Alle drei sind per Tastatur bedienbar und tragen eine Bezeichnung. Betreiber (16.10.2026, abgebrochen): „Du kannst manche Dinge anklicken, zum Beispiel das Live-Ding oder die Glocke oder … Also ob es jetzt hell oder dunkles Layout sein soll“ – der gemeinte Fehler ist nicht benannt und blieb unbeantwortet [unklar: Beschwerde unbeantwortet; Klärung beim Betreiber erforderlich].
  - Abnahme: Klick, Enter und Leertaste auf Glocke, Live-Anzeige und Schema-Umschalter führen jeweils das in der Spezifikation genannte Verhalten aus; ein Screenreader liest für jedes Element Name und Zustand („Benachrichtigungen, 3 ungelesen“).

- **OBE-101 · P0 · Status: Ist** — Erreichbarkeit jeder Seite. Jede Seite ist über Menü, Startkachel oder einen Link erreichbar, auch am Handy; ein Menüeintrag ohne Ziel ist verboten. Betreiber (12.10.2026): „Kannst du bitte gucken, ob es weitere Übersichten gibt, wo einfach nur die Button fehlen oder die Zugänge, die Links“. Die Seite „Meine Übersicht“ gibt es nicht mehr; ihre Inhalte stehen in Start, Krankmeldungen, Kursräumen und Noten.
  - Abnahme: Ein automatischer Test durchläuft alle Routen des Seitenverzeichnisses und weist für jede mindestens einen Zugang (Menü, Kachel, Link) je berechtigter Rolle nach; ein Menüeintrag mit nicht vorhandener Route lässt den Test fehlschlagen.

- **OBE-102 · P0 · Status: Ist** — Pflichtweichen und Sitzungsende. Vor allen Seiten greifen (der Server nennt den Grund, die Oberfläche leitet um), in dieser Reihenfolge [Festlegung Neubau; im Altbestand nicht festgelegt]: Lizenz gesperrt (Sperrseite ersetzt die Anwendung) → Passwort ändern (`/passwort`, nach Erstanmeldung oder Zurücksetzen) → Konten verbinden (`/konten-verbinden`, laut Anmelde-Richtlinie) → Zwei-Faktor einrichten (`/zwei-faktor`, wenn die Rolle laut `SM_REQUIRE_2FA_ROLES` oder Einstellung verpflichtet ist). Bei Sitzungsende (401) leitet die Oberfläche zur Anmeldung um und leert kontobezogene Zwischenspeicher und Meldungen. Die Weiterleitung nach der Anmeldung geht nur auf eigene interne Pfade; Standard ist die Startseite (Monitor-Konten gehen zu ihrem Standort-Monitor).
  - Abnahme: Ein Konto mit gesetztem „Passwort ändern“ erreicht außer `/passwort` keine Seite (jeder Aufruf leitet dorthin); eine Anmeldung mit Rücksprungadresse auf eine fremde Domain führt zur Startseite; nach 401 zeigt die Oberfläche die Anmeldung und keine Fachdaten.

---

## 6. Seiteninventar und Menüstruktur nach Rolle

Das Seitenverzeichnis ist Teil der Anforderung: Der Neubau liefert mindestens diese Seiten. Rechte-Namen stammen aus dem Rechte-Katalog (REC). „Mindestens eines“ heißt: eines der genannten Rechte genügt. Ist kein Recht genannt, steht „Recht laut REC“ mit dem Stand des Altbestands.

- **OBE-103 · P0 · Status: Ist** — Zugriffsregel je Seite. Jede Seite hat eine ausdrückliche Zugriffsregel: öffentlich, angemeldet oder mindestens ein Recht. Im Altbestand fehlte sie bei vielen Seiten (z. B. Benutzer, Rechte, Stammdaten, Planung, Verlauf, Vertretung, Klausuren, Aufsichten, Krankmeldungen, System, Daten, Einrichtung, Schuljahreswechsel); das ist nicht zu übernehmen. Ohne das Recht zeigt die Seite „Keine Berechtigung“ im App-Rahmen ohne Fachdaten (Servermeldung 403); unbekannte Adressen zeigen die 404-Seite. Die Oberfläche blendet nur aus, der Server prüft jede Anfrage (OBE-011). Der Menüeintrag verschwindet bei fehlendem Recht (OBE-098).
  - Abnahme: Ein Test listet alle Routen und fordert je Route eine Regel; eine Route ohne Regel lässt den Build scheitern; ein Konto ohne das Recht sieht bei direktem Aufruf „Keine Berechtigung“ und keinen Fachinhalt, die Netzwerkantwort des Servers enthält keine Fachdaten.

### 6.1 Öffentliche Seiten (ohne Anmeldung)

- **OBE-104 · P0 · Status: Ist** — Öffentliche Seiten.

| Route | Seite | Inhalt und Verhalten |
|---|---|---|
| `/login` | Anmeldung | Kennung und Passwort; bei Bedarf Zwei-Faktor-Schritt; Knöpfe der aktiven Anmeldedienste (Google, Microsoft, Apple; die Anmeldung „Schulkonto“ entfällt seit 16.10.2026; die Anmeldedienste erscheinen nur bei echter Einrichtung und im offiziellen Design der Anbieter); Logo; unten Links zu Impressum, Datenschutz, Barrierefreiheit; kein Code-Feld, keine Test-Knöpfe in Produktion |
| `/abgemeldet` | Abgemeldet | „Sie sind abgemeldet.“; noch gültige Konten dieses Browsers (OBE-035) |
| `/impressum` | Impressum | Text der Schule als reiner Text (kein HTML), je Text oder externer Link; fehlt er: „Noch nicht hinterlegt“ |
| `/datenschutz` | Datenschutzerklärung | Text der Schule wie beim Impressum; auch für Angemeldete im App-Rahmen erreichbar (siehe OBE-105) |
| `/barrierefreiheit` | Erklärung zur Barrierefreiheit | Stand der Konformität, bekannte Mängel, Rückmeldeweg [offen, neue Seite; OBE-146] |
| `/passwort-vergessen` | Passwort vergessen | Kennung und Kanal (E-Mail oder SMS) → neutrale Bestätigung (gleiche Antwort für unbekannte Kennungen) → 6-stelliger Code → neues Passwort; Link und Felder erscheinen nur, wenn der Server versenden kann und die Rolle es selbst darf; sonst „Kein Versand eingerichtet“ bzw. „Bitte wenden Sie sich an das Sekretariat“ |
| `/passwort-zuruecksetzen` | Passwort zurücksetzen | Zurücksetzen über den Link aus der E-Mail, dann neues Passwort; der Link wird einmal beim Laden geprüft |
| `/monitor/:site?` | Vertretungsmonitor | Seite ohne Anmeldung ladbar; Daten nur für ein Monitor-Konto mit `monitor.read` (Kapitel 14) |
| `/druck/vertretung` | Aushang Vertretungsplan | Druckansicht in öffentlicher Sicht ohne Gründe (Kapitel 13) [unklar: Altbestand ohne Routenregel; Neubau: Datenabruf nur mit `substitution.read`] |
| `/test-postausgang` | Test-Postausgang | nur im Entwicklungsbetrieb (`SM_DEV_OUTBOX`); in Produktion verboten (404) |

  - Abnahme: Alle genannten Routen sind ohne Anmeldung erreichbar bzw. in Produktion (Test-Postausgang) mit 404 beantwortet; `/login` enthält die Links Impressum, Datenschutz, Barrierefreiheit; ohne hinterlegten Impressumstext zeigt `/impressum` „Noch nicht hinterlegt“ und die Verwaltung eine Warnung; Anmeldedienste ohne Einrichtung erscheinen nicht.

### 6.2 Kernseiten und Konto

- **OBE-105 · P0 · Status: Ist** — Kernseiten nach der Anmeldung. Gruppe „Konto“, soweit nicht anders vermerkt.

| Route | Menü | Zweck | Zugriff |
|---|---|---|---|
| `/` | Start | Startseite mit Kacheln je Recht und Rolle (Kapitel 7) | angemeldet |
| `/*` | – | 404-Seite für unbekannte Adressen | – |
| `/passwort` | – | Passwort ändern (auch Pflichtseite) | angemeldet |
| `/zwei-faktor` | – | Einrichtung der Zwei-Faktor-Anmeldung (Code, QR-Code); Pflicht je Rolle | angemeldet |
| `/konten-verbinden` | – | Pflicht-Anmeldekonten verbinden (laut Richtlinie) | angemeldet |
| `/profil` | Profil | Abschnitte: „E-Mail & Handynummer“ (Kontakt und Wiederherstellung), verbundene Konten, Sicherheit (Zwei-Faktor, „Sitzung beenden“, „Alle anderen Sitzungen beenden“, angemeldete Geräte), Freigaben für Eltern (nur Schüler/innen), Verweis auf Benachrichtigungen | angemeldet |
| `/benachrichtigungen` | Benachrichtigungen | Liste gruppiert nach Heute, Gestern, Diese Woche, Früher; Filter „Ungelesen“; gelesen/ungelesen setzen oder löschen; „Gelesene löschen“; Klick führt zum Ziel; Reiter „Einstellungen“ (je Art: Aus, In der App, In der App und per E-Mail; ausgegraut, wenn kein Versand), Reiter „Schulvorgaben“ nur mit `settings.edit` | angemeldet |
| `/hilfe` | Hilfe | Handbuch in der App (Kapitel 8) | angemeldet |
| `/datenschutz` | Datenschutz | für Angemeldete derselbe Text wie öffentlich, ergänzt um den Abschnitt „Meine Daten“ mit Auskunft über die gespeicherten Daten (bei Eltern je Kind) | alle Angemeldeten |
| `/zugangsdaten/:id` | – | Zugangsbriefe eines Stapels (OBE-078) | `users.manage` oder `passwords.reset` |
| `/druck/zugangsbriefe` | – | Druck der Zugangsbriefe; die Daten kommen aus dem Seitenzustand, nie aus der Adresse | `users.manage` oder `passwords.reset` |

  [unklar: Der Altbestand hatte zwei Definitionen unter `/datenschutz` – Verwaltung (Löschkonzept, Betroffenenrechte, `privacy.manage`) und Hinweise für alle ohne Recht. Festlegung Neubau: `/datenschutz` = Hinweise und Auskunft; die Verwaltung liegt unter `/datenschutz/verwaltung` (OBE-109). Abgleich mit DAT.]
  - Abnahme: Jede Zeile ist mit dem genannten Zugriff erreichbar; `/datenschutz` zeigt Schülern den Abschnitt „Meine Daten“; `/datenschutz/verwaltung` ist für sie nicht erreichbar (Menüeintrag fehlt, direkter Aufruf zeigt „Keine Berechtigung“).

### 6.3 Seiten des Schulalltags

- **OBE-106 · P0 · Status: Ist** — Alltagsseiten (Menügruppe „Alltag“).

| Route | Menü | Zweck | Zugriff |
|---|---|---|---|
| `/stundenplan`, `/stundenplan/:kind`, `/stundenplan/:kind/:ref` | Stundenplan | Stundenplan je Ansicht (Klasse, Lehrkraft, Raum, Schüler/in) und konkrete Person, Klasse oder Raum | angemeldet; Sichten nach Freigabe und Datenumfang (alle Pläne: `plans.read_all`); Schüler/innen und Eltern nur eigene |
| `/vertretung` | Vertretungsplan | Vertretungsplan für Tag oder Zeitraum, Abwesenheit melden, Wochenstatistik | `substitution.read` (nicht für Schüler/innen und Eltern; Betreiber 12.10.2026) |
| `/aufsichten` | Pausenaufsichten | Pausenaufsichten der Woche: offene Plätze, Ersatz, Konflikte | Recht laut REC [Altbestand ohne Routenregel] |
| `/klausuren` | Klausuren | Klausurplan: Termin, Raum, Lehrkraft, Sprung zu Stundenplan oder Kursraum; Bearbeiten mit `exam.edit` | angemeldet |
| `/nachschreiben` | Nachschreiben | Nachschreibtermine je Klausur; Familie sieht den Attest-Stand; Terminvorschläge (eigene Stunde, Freistunde, Randstunde) | `exam.edit` oder `student_absence.read` |
| `/klassenbuch` | Klassenbuch | Klasse und Tag wählen, Anwesenheit je Stunde (OBE-092) | `student_absence.read` |
| `/krankmeldungen` | Krankmeldungen | Familie meldet je Kind und sieht die Meldungen; Personal sieht Meldungen; Lehrkraft meldet sich selbst ab | Sicht je Rolle (`student_absence.read` für Personal) |
| `/fehlzeiten/:studentId` | – | Fehlzeiten eines Kindes im Schuljahr: Summen entschuldigt und unentschuldigt, Protokoll | `student_absence.read` |
| `/dokumente` | Atteste und Dokumente | Prüf-Eingang und Dokumentliste für Personal; Einreichen für Schüler/innen und Eltern | `student_documents.read` |
| `/noten` | Noten | „Meine Noten“: alle Noten je Fach, je Kind; erst nach Freigabe durch die Lehrkraft | Schüler/innen und Eltern |
| `/lernstand` | Lernstand | Schüler/innen schätzen sich selbst ein; Eltern sehen den Lernstand je Kind; nur wenn die Schule freigibt | angemeldet; Sicht je Rolle |
| `/kompetenzen` | Kompetenzen | Klassenübersicht Lernstand je Kind (Heatmap), Kompetenzrahmen, Abzeichen | `competency.read` oder `competency.manage` |
| `/notenbuch` | Notenbuch | Notenbücher eines Halbjahres (eigene Kurse, für die Schulleitung alle), neues Notenbuch | mindestens eines laut NOT |
| `/notenbuch/:bookId` | – | Notentabelle eines Kursteils (Schüler/in × Leistungen, Tastatureingabe) | Ansichtsrechte laut NOT |
| `/notenbuch/klasse/:classId` | – | Klassenübersicht Schüler/in × Fächer mit Halbjahres- oder Vorschlagsnoten, Warnungen | `gradebook.read_class` oder `gradebook.manage` |
| `/notenbuch/verwaltung` | – | Schuleinstellungen des Notenbuchs, u. a. Einsicht für Schüler/innen und Eltern | Verwaltungsrecht laut NOT (Schulleitung) |
| `/klassen` | Klassen | Klassenliste: Suche nach Klasse, Klassenleitung, Raum; Filter Standort; gruppiert nach Jahrgang | mindestens eines laut STA |
| `/klassen/:id` | – | Klasse im Detail: Kopf (Raum, Klassenleitung), Reiter Lehrkräfte, Schüler/innen mit Konten, Wochenplan, Stundentafel, Klassenbuch-Übersicht, Fehlzeiten-Statistik (Krankmeldungen mit Nachweisstatus [offen]) | wie `/klassen` |
| `/klassen/neu` | – | Klassen-Assistent: Klasse, Schülerliste einfügen, Konten (Probelauf), Anlegen | `masterdata.edit` |
| `/lehrkraft/profil` | Profil als Lehrkraft | Fächer, Wunschklassen bzw. künftig Rollen, Deputat (nur lesbar), Arbeitszeitfenster, Wünsche, Sperrzeiten, einmalige Ausnahmen beantragen, Pendeln (nur bei mehreren Standorten) | `profile.teacher_self` |
| `/formulare` | Formulare | Ausfüllen, „Meine Formulare“, Eingang der Entscheidungen, Vorlagen | `forms.submit`, `forms.inbox` oder `forms.manage` |
| `/formulare/vorlage/:id` | – | Vorlage bearbeiten (Felder, Zielgruppe, Ablauf, Fristen, Aktionen, Vorschau); `:id` = Zahl oder „neu“ | `forms.manage` |

  - Abnahme: Je Zeile wird mit einem Konto, das nur das genannte Recht hat, die Seite erreicht und mit einem Konto ohne das Recht „Keine Berechtigung“ gezeigt; ein Schüler-Konto hat weder Menüeintrag noch Zugriff auf `/vertretung`; ein Eltern-Konto sieht unter `/stundenplan` nur Pläne der eigenen Kinder; fremde Klassen-, Schüler- oder Buch-IDs ergeben 404.

### 6.4 Kommunikation

- **OBE-107 · P0 · Status: Ist** — Kommunikationsseiten (Menügruppe „Kommunikation“). Nachrichten sind ein Eintrag: Postfach, Chats/Gruppen, Rundschreiben, E-Mails und Mitteilungen erscheinen als ein Menüeintrag „Nachrichten“ mit gemischter Liste, Filter-Chips und einem Zähler. Betreiber (12.10.2026): „Chat und Gruppen und das Postfach sind immer noch zwei getrennte Sachen … das musst du jetzt sofort zusammenführen … nicht zwei, es muss jetzt eine werden“.

| Route | Menü | Zweck | Zugriff |
|---|---|---|---|
| `/nachrichten/:kind?/:id?` | Nachrichten | Eine Liste für alles: Einzelchats, Gruppen, Briefe und Rundschreiben, E-Mails, Mitteilungen; Verlauf, Antworten, Suche. Filter: Alle · Chats · Gruppen · Briefe · E-Mail · Mitteilungen · Archiv; „Entwürfe“ nur, wenn welche existieren. PC: Liste links, Gespräch rechts; Handy: Liste und Gespräch nacheinander. Zahnrad oben rechts: Archiv, Stummschalten, Mitglieder und Rechte, Details, Geräte und Schlüssel | Nachrichten-Nutzung laut NAC |
| `/nachrichten/neu` | – | Nachricht verfassen: An, CC, BCC; Personen, Gruppen, E-Mail-Adressen; „Neu“: Chat, Gruppe, Brief; E-Mail nur mit verknüpftem Konto | Nachrichten-Nutzung; Rundschreiben mit `messages.broadcast` |
| `/nachrichten/einstellungen` | – | E-Mail-Hinweis und E-Mail-Konten, blockierte Personen, Regeln der Schule (z. B. Aufbewahrung) | Nachrichten-Nutzung |
| `/nachrichten/moderation` | Moderation | Gemeldete Nachrichten prüfen; die Liste zeigt keine Inhalte | `messages.moderate` |
| `/nachrichten/moderation/chats` | Chat-Meldungen | Gemeldete Chat-Nachrichten prüfen (Ende-zu-Ende-verschlüsselt; Umfang NAC) | `messages.moderate` |
| `/kursraeume` | Kursräume | Eigene Kursräume (Kursteile, Klassen, eigene), Suche nach Kurs, Klasse, Fach, Lehrkraft; Zähler neuer Inhalte | `channels.use`, `channels.manage` oder `channels.view_children` |
| `/kursraeume/:id` | – | Ein Kursraum mit Bereichen: Klasse (Startansicht), Material, Aufgaben, Unterricht, Pinnwand, Tests und Umfragen, Teilnehmende, Fortschritt, Papierkorb | wie `/kursraeume` |

  - Abnahme: Für jede Rolle erscheint genau ein Eintrag „Nachrichten“ (kein „Postfach“, kein „Chats“); der Zähler summiert alle Arten; `/kursraeume/<fremde ID>` liefert 404; Schüler/innen sehen keinen Eintrag „Moderation“.

### 6.5 Planung, Stammdaten, Daten

- **OBE-108 · P0 · Status: Ist** — Planungs- und Stammdatenseiten (Menügruppe „Planung“).

| Route | Menü | Zweck | Zugriff |
|---|---|---|---|
| `/planung`, `/planung/:tab` | Planung | Reiter (Reihenfolge `[unklar]`, siehe Kapitel 17): Plan prüfen (`/planung/pruefung`), Qualitätsbericht (`/planung/bericht`), Optimierung, Regeln (`/planung/regeln`), Vertretung & Abwesenheit, Stundentafeln, Kurse und Kopplungen, Neuaufbau (Generator), Plan-Stände, Planzeiträume, Zeitraster und Schuljahr | Reiter mit eigenen Rechten (`timetable.generate`, `timetable.edit`, `settings.edit`) |
| `/planung/vorschlaege` | Planvorschläge | Plan prüfen: Status der Dauerprüfung, offene Vorschlagspakete mit Varianten, Entscheidung, Verlauf; Zähler | `timetable.generate`, `timetable.edit` oder `settings.edit` |
| `/planung/vorschlaege/:paket/:variante` | – | Stundenplan-Vorschau einer Variante (Klassen- oder Lehrkraftplan) im Vergleich zum aktuellen Plan | wie `/planung/vorschlaege` |
| `/planung/antraege` | Anträge | Anträge von Lehrkräften prüfen: Profiländerungen, Ausnahmen, neue Fächer; Zähler | `teacher_requests.review` |
| `/stammdaten`, `/stammdaten/:tab` | Stammdaten | Reiter Standorte, Schuljahr, Zeitraster, Fächer, Räume, Jahrgänge, Lehrkräfte, Klassen, Schüler/innen; Bearbeiten über Rechte | Lesen und Bearbeiten laut STA (`masterdata.edit`) |
| `/einstellungen` | Einstellungen | Abschnitte Schule · Schulwoche & Zeitraster · Vertretung · Lehrkräfte · Krankmeldungen & Atteste · Postfach · Schnittstellen; jede Einstellung genau einmal; jeder Abschnitt speichert für sich [offen: im Altbestand lagen die Einstellungen noch in der Planung; alte Adressen leiten weiter] | `settings.edit` |
| `/verlauf` | Verlauf | Änderungsprotokoll mit Rückgängig (z. B. Plan-Stände); Aktionen als Sätze („[Lehrkraft] hat die Krankmeldung von [Schüler/in] entschuldigt“), Filter als Auswahl, deutsche Datumsangaben, Kürzel mit Namen | Recht laut REC [Altbestand ohne Routenregel] |
| `/daten` | Daten | Import und Export (CSV mit Spalten-Zuordnung und Vorlagen; Untis, Schulmanager Online) mit Vorschau vor der Übernahme und Warnhinweis bei Stunden-Neunummerierung | `timetable.edit` bzw. `masterdata.edit` |

  - Abnahme: Ein Konto nur mit `settings.edit` sieht „Planvorschläge“ und „Einstellungen“, nicht „Anträge“; `/planung/vorschlaege/<Paket>/<Variante>` zeigt den Vergleich Entwurf gegen aktuell ohne zu speichern; `/daten` zeigt vor der Übernahme eine Vorher-Nachher-Vorschau.

### 6.6 Verwaltung, Sicherheit, Betrieb

- **OBE-109 · P0 · Status: Ist** — Verwaltungsseiten (Menügruppe „Verwaltung“).

| Route | Menü | Zweck | Zugriff |
|---|---|---|---|
| `/einrichtung` | Schule einrichten | Einrichtungs-Assistent Schritt für Schritt (Schuldaten, Schuljahr und Ferien, Zeitraster, Lehrkräfte, Klassen, Schüler/innen, Stundentafeln, Konten, Rechte, E-Mail-Versand, Impressum und Datenschutzerklärung); Fortschritt gespeichert, Schritte überspringbar | `settings.edit` |
| `/schuljahreswechsel` | Schuljahreswechsel | Assistent: Vorgaben, Vorschau, Ausführen, Rückgängig | Schulleitung und Administration (Recht laut REC) |
| `/benutzer` | Benutzer | Benutzerverwaltung; Konto-Dialog mit Reitern Kontakt, verbundene Konten, Beobachtung, Zugangsdaten | `users.manage` (Reiter mit eigenen Rechten) |
| `/rechte` | Rollen und Rechte | Matrix Recht × Rolle, gruppiert nach Bereichen; eigene Rollen (Name, Beschreibung, Grundtyp Personal/Lehrkraft/Schüler/in/Eltern/Ansicht, Vorlage für Startrechte); Warn-Dialog bei Rechten außerhalb des üblichen Zwecks (Warnung statt Verbot); Gruppen einklappbar | Recht laut REC (`rights.manage`) |
| `/anmeldedienste` | Anmeldedienste | Microsoft, Apple, Google einrichten (Felder je Anbieter, Prüfung) | nur Administration |
| `/anmelde-richtlinien` | Anmelde-Richtlinien | Anmeldewege je Zielgruppe (Schüler/innen, Eltern, Personal), Pflicht-Anbieter, Vererbung Schule → Jahrgang → Klasse → Person, Prüfbericht | `login_policy.manage` |
| `/sicherheit` | Sicherheit | Zwei-Faktor-Vorgabe je Rolle, Anmelde-Drosselung und Sperren mit Wartezeit | `login_policy.manage` |
| `/beobachtete-konten` | Beobachtete Konten | Verstärkte Protokollierung mit Ablauf, Zeitleiste der Anmeldungen und Aktionen, CSV-Export | `watch.read` |
| `/api-zugaenge` | API-Zugänge | API-Zugänge anlegen (Assistent: Name, Bereiche, Filter), verwalten, Protokoll der Zugriffe | `api.own` oder `api.manage` |
| `/datenschutz/verwaltung` | Datenschutz-Verwaltung | Löschkonzept (Fristen je Datenart, Vorschau, Warteliste, Sofort-Löschen mit Bestätigung durch Eintippen) und Betroffenenrechte (Auskunft, Übertragbarkeit) | `privacy.manage` |
| `/betrieb` | Betrieb | Betriebsstatus mit Prüfliste (Datenbank, Schema, Speicher, letzte Sicherung, E-Mail-Versand, Verschlüsselung, Lizenz, Wartungslauf), Sicherungen, Test-Restore, Fehlerprotokoll (30 Tage, mit Fehlernummer), Updates mit Zeitfenster; Hinweise gelb, Fehler rot, jeweils mit Text | `system.admin` |
| `/system` | System | Systemseite der Administration; Zahlen mit deutschen Bezeichnungen, Technik einklappbar | Administration (`system.admin` abgeleitet) |
| `/lizenz` | Lizenz | Lizenz der Schule: Status, Server, Hinweise (Schlüssel nur für `license.manage`) | `license.manage` |
| `/monitore` | Monitore | Vertretungsmonitore einstellen, je Standort (später je Profil, Kapitel 14) | `monitor.manage` |

  - Abnahme: Je Zeile erreicht ein Konto mit genau dem genannten Recht die Seite, ein Konto ohne es nicht (Menüeintrag fehlt; direkter Aufruf zeigt „Keine Berechtigung“); die Standardrolle Administration hat keinen Zugriff auf Gesundheits- und Notendaten (kein Eintrag „Krankmeldungen“, „Notenbuch“, „Atteste und Dokumente“); `/betrieb` zeigt Hinweise gelb und Fehler rot jeweils mit Text; `/rechte` fragt in einem App-Dialog nach, wenn einer Schüler-Rolle ein Verwaltungsrecht zugewiesen wird.

- **OBE-110 · P1 · Status: Ist** — Weiterleitungen alter Adressen. `/postfach…` und `/chats…` leiten nach `/nachrichten…`, `/mitteilungen` nach `/nachrichten` (Mitteilungen sind ein Ordner bzw. Filter der Nachrichten), `/chats/moderation` nach `/nachrichten/moderation/chats`, `/meine-uebersicht` nach `/` [abgeleitet: Zielseite im Altbestand nicht genannt; Start und Übersicht wurden zusammengeführt]. Weiterleitungen behalten die Rechteprüfung des Ziels. Startkacheln und „Nachricht schreiben“ im Klassenraum zeigen auf die neuen Adressen.
  - Abnahme: Aufruf von `/postfach/123`, `/chats/456` und `/mitteilungen` führt zu den Zielen; ein Schüler-Konto wird von `/chats/moderation` nicht zur Moderation, sondern zu „Keine Berechtigung“ geleitet.

- **OBE-111 · P2 · Status: Ist** — Anbieter-Portal (eigene Oberfläche des Betreibers, BET). Seitenleiste mit Start, Schulen, Zahlungen, Updates; Schul-Detailseite mit Reitern Überblick, Server, Zahlungen, Verlauf, Einstellungen; „Schule anlegen“ als Assistent in 4 Schritten mit Zugangsblatt (PDF) am Ende; Schlüssel anzeigen, kopieren, neu ausstellen; Sofortsperre und Kündigen mit Eingabe des Schulnamens (OBE-031); Anmeldung mit Passwort. Gestaltung wie die Schul-Oberfläche (Tokens, Hell und Dunkel, Handy); gefährliche Aktionen rot.
  - Abnahme: Das Portal verwendet dieselben Token-Dateien wie die Schul-Oberfläche; „Sofortsperre“ bleibt ohne exakten Schulnamen deaktiviert; der Assistent endet mit einem herunterladbaren Zugangsblatt.

### 6.7 Menü je Rolle

- **OBE-112 · P1 · Status: Ist** — Menü je Rolle. Das Menü folgt den Rechten (OBE-098); eigene Rollen der Schule sind möglich, ihre Bezeichnung kommt aus der Schule. Die folgende Zuordnung zeigt das Ergebnis der Standardrechte und ist abgeleitet, nicht verbindlich; Abweichungen entstehen allein durch geänderte Rechte. Gruppen: A = Alltag, K = Kommunikation, P = Planung, V = Verwaltung, C = Konto. Alle Rollen mit Anmeldung haben in C: Benachrichtigungen, Hilfe, Datenschutz, Profil (Profil als Menüpunkt und Abmelden im Benutzermenü).

| Rolle | A – Alltag | K – Kommunikation | P – Planung | V – Verwaltung |
|---|---|---|---|---|
| Schüler/in | Start, Stundenplan, Klausuren, Krankmeldungen (Volljährige melden selbst), Atteste und Dokumente (einreichen), Noten (nach Freigabe), Lernstand, Formulare | Nachrichten (Mitschüler nur, wenn die Schule es erlaubt), Kursräume | – | – |
| Eltern | Start, Stundenplan (Kind), Klausuren, Krankmeldungen, Atteste und Dokumente, Noten (nach Freigabe), Lernstand (nur ansehen), Formulare, Kinderauswahl (nur bei mehreren Kindern) | Nachrichten, Kursräume (lesend) | – | – |
| Lehrkraft (Fachlehrkraft) | Start, Stundenplan, Vertretungsplan, Pausenaufsichten, Klassenbuch und Krankmeldungen (je Recht), Klausuren, Nachschreiben, Atteste und Dokumente (je Recht), Notenbuch (eigene Kurse), Kompetenzen, Formulare, Profil als Lehrkraft | Nachrichten, Kursräume | – | – |
| Klassenleitung | wie Lehrkraft, zusätzlich Klassen (eigene Klasse), Klassenbuch ganz, Krankmeldungen der Klasse prüfen und entschuldigen, Atteste und Dokumente der eigenen Klasse | Nachrichten, Kursräume | – | – |
| Sekretariat | Start, Krankmeldungen, Atteste und Dokumente, Vertretungsplan, Klassen, Klausuren, Nachschreiben, Formulare (Eingang) | Nachrichten | Stammdaten (lesen) | Benutzer (mit Zugangsdaten), Monitore |
| Planung (Stundenplanung) | Start, Stundenplan, Vertretungsplan, Pausenaufsichten, Klausuren | Nachrichten | Planung (mit Reitern), Planvorschläge, Anträge, Stammdaten, Verlauf, Daten | – |
| Schulleitung | Start, Krankmeldungen, Vertretungsplan, Pausenaufsichten, Klausuren, Klassen, Notenbuch (Verwaltung), Kompetenzen | Nachrichten (mit Moderation) | Planung, Planvorschläge, Anträge | Benutzer, Rollen und Rechte, Schuljahreswechsel, Datenschutz-Verwaltung, Schule einrichten, Sicherheit, Anmelde-Richtlinien, Beobachtete Konten, Monitore, Lizenz |
| Administration | Start, Stundenplan, Vertretungsplan, Klassen (kein Zugang zu Gesundheits- und Notendaten) | – | Planung, Stammdaten, Verlauf, Daten | Betrieb, System, Anmeldedienste, API-Zugänge, Datenschutz-Verwaltung, Schuljahreswechsel, Lizenz, Monitore, Schule einrichten, Benutzer, Rollen und Rechte |
| Abteilungsleitung | wie Lehrkraft, zusätzlich Klassen der Abteilung | Nachrichten, Kursräume | – | – |
| Zuschauer (Vorführ-Konto) | Start, Stundenplan, Vertretungsplan, Klausuren (reiner Lesezugriff; ausdrückliche Rechte-Liste mit 26 Rechten) | – | – | – |
| Monitor | kein Menü; nur der Monitor (Kapitel 14) | – | – | – |
| eigene Rolle | Menü folgt den zugewiesenen Rechten | | | |

  Nicht in der Zuschauer-Rolle: Gesundheits-, Förder-, gemeldete Chat- und Audit-Daten; der Zuschauer sieht die Betreiber-Hilfe nie. Die Rollen Hausmeister und Schulbegleitung sind vorgesehen; ihr Menü ist [unklar: nicht beschrieben]. Das Menü der Abteilungsleitung ist [unklar: Rechte im Altbestand nicht im Einzelnen beschrieben; Klassenrollen B-15/B-19 offen].
  - Abnahme: Für jede Rolle mit Standardrechten (Demo-Konten) enthält das Menü mindestens die genannten Einträge und keinen der ausgeschlossenen (Schüler/Eltern ohne „Vertretungsplan“, Administration ohne „Krankmeldungen“ und „Notenbuch“, Zuschauer ohne Verwaltungseinträge); ein Konto einer eigenen Rolle mit nur `forms.submit` sieht genau „Start“, „Formulare“ und die Konto-Einträge.

- **OBE-113 · P1 · Status: Ist** — Untere Leiste je Rolle (Handy). Je Rolle bis zu 4 Ziele in fester Reihenfolge plus „Menü“. Typische Belegung (abgeleitet, je Rolle konfigurierbar; der Altbestand nennt als typisch: Start, Stundenplan, Vertretung, Postfach bzw. Mitteilungen):

| Rolle | Ziele der unteren Leiste |
|---|---|
| Schüler/in | Start, Stundenplan, Kursräume, Nachrichten |
| Eltern | Start, Stundenplan, Krankmeldungen, Nachrichten |
| Lehrkraft | Start, Stundenplan, Vertretung, Nachrichten |
| Klassenleitung | Start, Stundenplan, Klassenbuch, Nachrichten |
| Sekretariat | Start, Krankmeldungen, Vertretung, Nachrichten |
| Planung | Start, Planvorschläge, Vertretung, Stundenplan |
| Schulleitung | Start, Planvorschläge, Vertretung, Nachrichten |
| Administration | Start, Betrieb, Benutzer, Hilfe |

  - Abnahme: Bei 390 px zeigt jede Rolle höchstens 4 Ziele plus „Menü“ in dieser Reihenfolge; ein Ziel, für das die Person kein Recht hat, entfällt; die übrigen Ziele behalten ihre feste Reihenfolge.

---

## 7. Startseiten

Betreiber (11.10.2026): „der Start und meine Übersicht ... könntest du zusammenführen.“ Die frühere Karte „Mein Tag“ (ein Tag, Stunden untereinander) entfällt; Raster und Liste sind wiederhergestellt. „Meine Übersicht“ gibt es nicht mehr (OBE-101).

- **OBE-114 · P1 · Status: Ist** — Startseite. Nach der Anmeldung öffnet `/` die Startseite mit Kacheln, die je Recht und Anlass erscheinen. Eine Kachel wird nur geladen, wenn sie erscheint; Menüzähler sind klein und werden beim App-Start geladen. Jede Kachel steht in einer Fehlergrenze (OBE-040). Weitere Regeln: feste Kachel-Reihenfolge je Rolle [unklar: Reihenfolge im Altbestand nicht ausgeschrieben; Neubau legt sie je Rolle in der Konfiguration fest]; eine Spalte auf 390 px; alle Kacheln einer Zeile gleich hoch [offen: im Altbestand unterschiedlich hoch]; „Aktualisieren“ lädt nur die Daten, nicht die Seite; keine Erklärabsätze. „Heute“ ist am Wochenende sinnvoll belegt und überspringt Ferien.
  - Abnahme: Eine Lehrkraft sieht die Kacheln in der konfigurierten Reihenfolge; ein erzwungener Fehler in einer Kachel lässt die übrigen stehen; „Aktualisieren“ löst keinen Seitenneuaufbau aus (Fokus und Scrollposition bleiben); bei 390 px stehen alle Kacheln untereinander in gleicher Höhe.

- **OBE-115 · P1 · Status: Ist** — Kachelkatalog. Eine Kachel erscheint nur, wenn ihr Recht vorliegt oder ein Anlass besteht.

| Kachel | Inhalt | Bedingung |
|---|---|---|
| Nachrichten | ungelesene Unterhaltungen, höchstens 5, mit Absender, Betreff, Zeit | Nachrichten-Nutzung |
| Kursräume (Schüler/in) | neues Material und fällige Aufgaben aus allen Kursräumen | Schüler/in |
| Kursräume (Lehrkraft) | Stunden des (nächsten) Unterrichtstags mit gebundenem Material und Freigabe-Knopf; Aufgaben mit Abgaben, die Rückmeldung brauchen | Lehrkraft |
| Formulare | Einreichungen, die auf Entscheidung oder Rückmeldung warten | nur bei Anlass |
| Nachschreiben | anstehende Termine | nur bei Terminen |
| Planvorschläge | Vorschläge zur Entscheidung oder in Berechnung; Hinweis bei neuem Paket | `timetable.generate`, `timetable.edit` oder `settings.edit`, nur bei Anlass |
| Anträge | offene Anträge | Planung und Leitung (`teacher_requests.review`) |
| Profil als Lehrkraft | Zeitfenster, Deputat, Antragsstatus | `profile.teacher_self` |
| Atteste und Dokumente | offene Dokumente (Personal), fehlende Atteste; Klassenleitung für die eigene Klasse | `student_documents.read` |
| Familie je Kind | Wochenplan, Hinweis auf fehlende Angaben, Krankmeldung | Eltern, Schüler/in |
| Zwei-Faktor-Hinweis | Die Schule empfiehlt Zwei-Faktor für die Rolle, das Konto hat es noch nicht | nur bei Anlass |
| Abwesende Lehrkräfte | eine Zeile je Person: Kürzel, Name, Stunden, Fälle | `substitution.read` |
| Wochenplan / Klassenkarte | Wochenplan, bei Klassenleitung die eigene Klasse; eigene KW-Auswahl | Rolle |
| Planungskennzahlen | Hohlstunden, unverplante Stunden, Konflikte | nur Planung (nicht Sekretariat, nicht Schulleitung) [offen] |
| Einrichtung | Liste der nächsten Einrichtungsschritte statt Nullen bei leerer Schule | `settings.edit` [offen] |
| Betriebs-, Lizenz-, Sicherheitshinweise | Zustand der Instanz | Administration |

  Die Kennzahl „Klassen abwesend“ entfällt; „Lehrkräfte abwesend“ führt zur Karte auf `/vertretung` (nur gemeldete Klassenabwesenheiten zählen; ein Wandertag ist eine Zeile je Klasse).
  - Abnahme: Je Rolle zeigt die Startseite genau die Kacheln, deren Bedingung erfüllt ist; ein Sekretariats-Konto sieht keine Planungskennzahlen, ein Planungs-Konto schon; eine leere Schule zeigt die Einrichtungsliste und keine Nullen-Kacheln; die Kachel „Nachschreiben“ fehlt, solange kein Termin ansteht.

- **OBE-116 · P1 · Status: Ist** — Schnellmeldungen. Lehrkräfte melden sich auf der Startseite per Schnellwahl: „Ich bin krank“, „Mein Kind ist krank“, „Beurlaubung“; beim Krankmelden geben sie an, was die Klasse in den verpassten Stunden tun soll. Familien haben den großen Knopf „Für heute krank melden“. Eine Lehrkraft sieht ihre eigene Krankmeldung auf der Startseite und kann sie verkürzen oder zurückziehen („bin doch da“) [offen]; die Vertretungen werden neu berechnet.
  - Abnahme: Ein Klick auf „Ich bin krank“ öffnet den Dialog mit Feld für die Aufgabe der Klasse; nach dem Absenden erscheinen die Vertretungen im Vertretungsplan ohne Neuladen.

- **OBE-117 · P2 · Status: Ist** — Typische Startseite je Rolle (abgeleitet, folgt den Kacheln aus OBE-115): Administration: Betriebs-, Lizenz- und Sicherheitshinweise. Schulleitung: Anträge, Planvorschläge, Vertretungsübersicht. Sekretariat: Dokumente, Krankmeldungen, Monitor. Planung: Vorschläge, Anträge. Klassenleitung: Klassenkarte, Wochenplan, Dokumente. Lehrkraft: Heute (Stunden), Aufgaben mit Abgaben, Profilkarte. Schüler/in: Wochenplan, neues Material und fällige Aufgaben, Krankmeldung. Eltern: Kinderauswahl, Wochenplan, Krankmeldung, Nachschreib-Hinweis.
  - Abnahme: Die Demo-Konten der genannten Rollen zeigen jeweils mindestens die genannten Kacheln und keine der ausgeschlossenen.

---

## 8. Hilfe und Handbuch

### 8.1 Hilfe an der Beschriftung

- **OBE-118 · P0 · Status: Ist** — Auslösen der Hilfe mit Maus und Touch. Maus: Der Zeiger verweilt etwa 2 Sekunden auf dem Namen, dann erscheint die Hilfe; sie bleibt, solange der Zeiger auf Name oder Hilfe steht (WCAG 1.4.13). Rechtsklick auf den Namen: Hilfe sofort und angeheftet (nicht im Eingabefeld). Touch: Antippen des Namens öffnet oder schließt die Hilfe; das Feld erhält dabei keinen Fokus. Klick schaltet Hilfe-Knöpfe und eigenständige Namen um; ein Name innerhalb einer Beschriftung fokussiert dagegen das Feld. Betreiber (11.10.2026): Hilfe „nach 2 s, Rechtsklick, Antippen“.
  - Abnahme: Zeiger 2 s auf „Doppelstunden“ → Hilfe erscheint, bleibt beim Wandern des Zeigers auf die Hilfe; Rechtsklick → Hilfe sofort; Tipp auf dem Handy → Hilfe, zweiter Tipp schließt; das Feld hat danach keinen Fokus.

- **OBE-119 · P0 · Status: Ist** — Hilfe per Tastatur und Schließen. F1 im Feld öffnet oder schließt die Hilfe (auch Umschalt+? im fokussierten Feld); außerhalb von Texteingaben (Auswahl, Kästchen, Knopf) zusätzlich „?“. Hilfe-Knöpfe und eigenständige Namen mit Enter oder Leertaste. Escape schließt zuerst die Hilfe, nicht den Dialog darunter; alternativ Klick außerhalb. Höchstens eine Hilfe ist gleichzeitig offen. Position: unter dem Auslöser, sonst darüber, immer im sichtbaren Bereich. Die Hilfe ist mit dem Feld verknüpft und wird beim Fokussieren vorgelesen.
  - Abnahme: F1 im Feld öffnet die Hilfe, Escape schließt nur sie (der Dialog bleibt offen); eine zweite Hilfe schließt die erste; ein Screenreader liest die Hilfe beim Fokus des Feldes; am unteren Fensterrand erscheint sie oberhalb des Auslösers.

- **OBE-120 · P0 · Status: Ist** — Darstellung der Hilfe. Namen mit Hilfe tragen eine gepunktete Unterstreichung und den Mauszeiger „Hilfe“. Überschriften- und Seitenhilfe nutzen ein dezentes Info-Zeichen (i) neben dem Titel (24 × 24, Strichstil, für Bildschirmleser ausgeblendet; die Bedeutung steht als Text daneben bzw. als Bezeichnung des Knopfes). Auf Touch-Geräten haben Namen mit Hilfe eine unsichtbar vergrößerte Trefferfläche von mindestens 44 px bis an das Feld, ohne die Zeile zu erhöhen (Altbestand: 37 px, vorher 16 px; maßgeblich 44 px). Kennzahlen-Kacheln erklären sich über dieselbe Hilfe („?“).
  - Abnahme: Eine Beschriftung mit Hilfe ist gepunktet unterstrichen; auf einem Touch-Gerät misst die Trefferfläche mindestens 44 px und die Zeilenhöhe bleibt unverändert; das Info-Zeichen hat einen zugänglichen Namen („Hilfe zu …“).

- **OBE-121 · P0 · Status: Ist** — Inhalt der Hilfetexte. 1 bis 3 Sätze, reiner Text ohne Links und ohne Knöpfe; sie beschreiben Wirkung und Folgen, nicht die Bedienung des Feldes (Beispiel: „Jüngere Klassen werden immer vertreten.“); Sie-Form; keine Tastatur- oder Mausanweisungen (auf Touch sowieso nicht); Begriffe der Planung (Unverplant, Zu viel verplant, Konflikte, Hohlstunden, Springstunden, Standortwechsel, Hauptfächer spät, Wochenmuster, Strafpunkte) sind per Hilfe erklärt (Betreiber, 12.10.2026: „drauf drücken“). Fachlich nötige, vom Zustand abhängige Hinweise (z. B. Ferien-Warnung, Attest-Hinweis) bleiben als sichtbarer Hinweis stehen und wandern nicht in die Hilfe.
  - Abnahme: Eine Prüfung über alle Hilfetexte findet höchstens 3 Sätze, keine Links, keine Wörter wie „klicken“, „Maus“, „Rechtsklick“, „drücken Sie“; die Ferien-Warnung im Krankmeldungs-Dialog ist ohne Hilfe sichtbar.

- **OBE-122 · P2 · Status: Ist** — Hilfetexte immer anzeigen. Im Benutzermenü schaltet „Hilfetexte immer anzeigen“ die Feldhilfen zusätzlich als Text unter dem Feld ein (Einsteiger-Option). Die Einstellung gilt je Browser, nicht im Konto.
  - Abnahme: Mit eingeschaltetem Schalter erscheint unter einem Feld mit Hilfe deren Text; nach Abmeldung und Anmeldung mit einem anderen Konto im selben Browser bleibt der Schalter an; in einem anderen Browser ist er aus.

- **OBE-123 · P2 · Status: offen** — Seitenhilfe mit Weg ins Handbuch. Jede Seite hat neben dem Seitentitel ein Info-Zeichen mit einer Seitenhilfe. Als einzige Ausnahme von „reiner Text“ darf sie den Link „Im Handbuch öffnen“ tragen, der den Abschnitt des Handbuchs zur Seite öffnet (`/hilfe?doc=<id>`). [unklar: Das Backlog verlangt „mehr dazu“-Verweise an Feldhilfen; die Hilfetext-Regel verbietet Links. Festlegung Neubau: nur die Seitenhilfe trägt den Link.]
  - Abnahme: Die Seitenhilfe von `/vertretung` enthält den Link und öffnet den passenden Handbuchabschnitt; eine Feldhilfe enthält nie einen Link.

### 8.2 Handbuch in der App

- **OBE-124 · P1 · Status: Ist** — Handbuch `/hilfe`. Zeigt die Kurzanleitung(en) für die Rolle der angemeldeten Person (angemeldet genügt als Recht); Abruf über `GET /api/v1/manual`. Darstellung als Markdown (Überschriften, Listen, Tabellen, Codeblöcke, Zitate, Trennlinien, Anker) ohne HTML; Links zwischen Hilfeseiten werden zu Anwendungslinks (`/hilfe?doc=<id>`), Verweise auf Beispieldateien erscheinen als Text, externe Links nur http, https, mailto. Die Handbuch-Texte liegen als Dokumente im Programm, nicht in der Datenbank. Sprache: Sie-Form, einfache Sprache (geprüft gegen die Textregeln dieses Kapitels).
  - Abnahme: Ein Schüler-Konto sieht nur die Schüler-Anleitung; ein Link zu einer anderen Hilfeseite bleibt in der App; ein Markdown-Skript wird nicht ausgeführt.

- **OBE-125 · P1 · Status: Ist** — Gliederung der Kurzanleitungen je Rolle. Jede Anleitung nennt die Menüpunkte der Rolle mit ihren Namen aus Kapitel 6 und gliedert sich so:

| Rolle | Abschnitte |
|---|---|
| Administration | Erste Schritte (Anmeldung mit dem Erst-Administrator, eigenes Passwort, Zwei-Faktor im Profil, Einrichtungsassistent); Einrichtungsassistent; Menü „Betrieb“ (Status, Sicherung erstellen, Prüfen/Test-Restore mindestens monatlich, Fehlerprotokoll der letzten 30 Tage); Konten (Benutzer, Zurücksetzen, Entsperren); Notfallzugang über den Befehl `schulmanager-admin`; Updates (vorher Sicherung); Schuljahreswechsel |
| Schulleitung und Verwaltung (Schulleitung, Sekretariat, Planung, Abteilungsleitung) | Einrichtung; Start; Krankmeldungen; Vertretungsplan; Planung mit „Plan prüfen“; Klausuren; Mitteilungen und Nachrichten; Konten und Zugangsbriefe; Rollen und Rechte; Schuljahreswechsel (Vorgaben, Vorschau, Ausführen, Rückgängig; vorher Sicherung); Datenschutz |
| Lehrkräfte | Anmeldung und Profil; Stundenplan; Vertretungsplan; Krank melden; Pausenaufsichten; Klassenbuch; Krankmeldungen der Klasse; Nachschreiben und Klausuren; Kursräume; Notenbuch; Kompetenzen; Nachrichten; Datenschutz |
| Eltern | Anmeldung (Adresse öffnen, zum Startbildschirm hinzufügen, Zugangsbrief mit QR-Code, eigenes Passwort, Passwort vergessen); Stundenplan und Vertretung; Krankmeldung in vier Schritten; Nachrichten; Benachrichtigungen; Lernstand und Noten; Datenschutz-Seite; Zwei-Faktor |
| Schüler/innen | Anmeldung; Stundenplan; Kursräume (Abgabe, Status, Material „neu“); Nachrichten; Krankmeldung; Lernstand; Sicherheit (Abmelden, Passwort nicht weitergeben) |

  [unklar: Ein eigenes Kapitel für Sekretariat und Planung gab es im Altbestand nicht; die Rollen sind unter „Schulleitung und Verwaltung“ zusammengefasst. Die Rolle Ausbilder/innen kommt mit dem Ausbilderzugang (STA).]
  - Abnahme: Für jede Zeile existiert ein Abschnitt; die in den Abschnitten genannten Menüpunkte existieren in Kapitel 6 mit diesem Namen; kein Abschnitt verwendet „Postfach“ oder „du“.

- **OBE-126 · P0 · Status: Ist** — Betreiber-Hilfe. Zusätzlich gibt es ein Betreiber-Paket mit den Reitern „Betrieb und Einrichtung“ (Installation, Betrieb, Sicherheit, Updates; `system.admin`), „Schule einrichten“ (`settings.edit`) und „Datenschutz-Vorlagen“ (`privacy.manage`); jedes Dokument ist mit einem Recht verknüpft. Unberechtigte erhalten 404 (`GET /api/v1/manual/operator`), sodass die Existenz verborgen bleibt; der Zuschauer sieht das Paket nie; Lehrkräfte, Eltern, Schüler/innen, Hausmeister und Sekretariat ebenfalls nicht. Die Texte enthalten keine Betreiber-Domain, keinen Servernamen, keine Personennamen (ein automatischer Test prüft das bei jedem Lauf). Verweise auf nicht ausgelieferte Dokumente sind verboten („Hilfe → Administration“ statt Dateipfad).
  - Abnahme: Ein Lehrkraft-Konto erhält für das Betreiber-Paket 404 und sieht keinen Reiter; ein Konto mit nur `privacy.manage` sieht „Datenschutz-Vorlagen“, nicht „Betrieb und Einrichtung“; der Test schlägt an, wenn ein Hilfetext eine Domain enthält.

- **OBE-127 · P1 · Status: offen** — Werte im Handbuch aus der Konfiguration. Zahlenwerte, die konfigurierbar sind (Passwort-Mindestlänge, Attest-Schwelle in Schultagen, Lebensdauer von Zugangsbriefen, Fristen), stehen im Handbuch als Platzhalter und werden bei der Auslieferung aus der Konfiguration eingesetzt. Im Altbestand nannte das Schüler-Handbuch 10 Zeichen, der Code verlangte 8.
  - Abnahme: Ein Test vergleicht alle Zahlenwerte im Handbuch mit der Konfiguration und schlägt bei Abweichung fehl.

- **OBE-128 · P2 · Status: offen** — Hilfecenter ausbauen (Paket Handbuch je Rolle). Durchsuchbar; jede Seite verlinkt ihren Abschnitt (OBE-123); Kurzanleitungen als PDF je Rolle (eine bis zwei Seiten, Bildschirmfotos aus der Demo); Einführungspaket (Muster-Elternbrief, Aushang, FAQ, Pressetext-Vorlage); Datenschutzunterlagen als Vorlagen (Datenschutzinformationen nach Art. 13/14, Eintrag für das Verzeichnis der Verarbeitungstätigkeiten, Beschreibung der technischen und organisatorischen Maßnahmen, Nutzungsordnung, Muster-Auftragsverarbeitungsvertrag; Inhalte REH/DAT); Texte in einfacher Sprache; Hilfetexte nennen „Nachrichten“ statt „Postfach“.
  - Abnahme: Die Handbuchsuche findet „Krankmeldung“ in den Anleitungen von Eltern und Lehrkräften; das PDF der Eltern-Anleitung hat höchstens 2 Seiten; eine Volltextsuche nach „Postfach“ in Handbuch und Hilfetexten findet 0 Treffer.

---

## 9. Texte und Ton

Die Oberfläche spricht Deutsch in der Sie-Form (OBE-006), sachlich und knapp. Es gibt keinen Werbeton, keine Ausrufezeichen, keine Emojis und kein „Tipp:“. Die Oberfläche ist nur auf Deutsch (siehe Kapitel 18).

- **OBE-129 · P0 · Status: Ist** — Formate und zentrale Formatierung. Datum und Zeit entstehen nur über eine zentrale Formatierung. Datum `TT.MM.JJJJ`, Uhrzeit `HH:MM` (24 Stunden), Wochentage Mo bis So (für Bildschirmleser ausgeschrieben), Kalenderwoche „KW“, Zahlen mit Komma („5,5“), Stunden als „3. Std.“, Zahl und Einheit mit Leerzeichen („45 min“, „5 %“), Dateigrößen mit Komma („1,5 KB“, nicht „1.5 KB“). Zeiten in Ortszeit (Europe/Berlin), Speicherung in UTC. Sortierung nach deutscher Regel und natürlich (5a vor 10a; „Ohne Jahrgang“ zuletzt). Mehrzahlformen, Listen und Größen werden zentral gebildet („1 Hinweis“, „2 Hinweise“, „1 Kursraum“, „3 Kursräume“, „1 Eintrag“). Wochen erscheinen nur als Zahl, Liste oder Rhythmus („Woche 1 … N“), nie als Buchstabe. Datum und Zeit außerhalb der zentralen Formatierung sind verboten.
  - Abnahme: Ein Test sucht nach manueller Datumsformatierung außerhalb der zentralen Funktion und findet 0 Treffer; „1 Hinweise“ und „1 Einträge“ kommen nirgends vor; 1500 Bytes erscheinen als „1,5 KB“; eine Liste „5a, 10a, 5b“ wird als „5a, 5b, 10a“ sortiert; eine Wochenangabe mit Buchstaben besteht den Test nicht.

- **OBE-130 · P0 · Status: Ist** — Stilregeln für Beschriftungen, Knöpfe und Meldungen. Beschriftungen: Substantiv, höchstens drei Wörter, ohne Doppelpunkt („Grund“, nicht „Bitte geben Sie einen Grund ein:“); optionale Felder mit „(optional)“, Pflichtfelder mit „\*“. Knöpfe: Verb im Infinitiv mit klarem Ziel („Speichern“, „Krank melden“, „Neuen Link erzeugen“). Meldungen: was ist passiert und was ist zu tun („Keine Verbindung. Erneut versuchen.“). Kein Fachjargon, keine internen IDs, keine Feldnamen, kein Englisch. Keine Ausrufezeichen, keine Emojis, kein „Tipp:“. Hinweise nur bei echtem Zustand. Ein Begriff bedeutet überall dasselbe.
  - Abnahme: Eine Prüfung der Beschriftungen findet keine mit Doppelpunkt am Ende und keine mit mehr als drei Wörtern (Ausnahmen sind namentlich im Glossar erfasst); die Texte der Oberfläche enthalten kein „!“ und kein „Tipp:“; ein Knopf heißt nie „OK“ oder „Ja“.

- **OBE-131 · P0 · Status: Ist** — Glossar und verbotene Begriffe. Die Oberfläche verwendet die Begriffe der linken Spalte; die rechte Spalte ist in Oberflächentexten verboten (Test).

| Verwenden | Nicht verwenden |
|---|---|
| Kursraum; Raum der Klasse | Kanal, Channel |
| Woche 1 | Wochenbuchstabe (A/B) |
| Stunde, Doppelstunde | Block (als Planungsbegriff in Texten) |
| Planung | Planungsdokument |
| Nachrichten | Postfach, Chats und Gruppen als getrennte Einträge |
| Lehrkraft | Lehrende, Lehrer (als Sammelbegriff) |
| Strafpunkte (niedriger = besser) | Kosten |
| Wochenmuster | variants |
| Optimierung (mit Stufen) | Prioritäten, Gewichte |
| Rechenzeit „Schnell · Normal · Gründlich“ | Startwert (Seed), Optimierungsschritte, parallele Läufe (nur unter „Erweitert“) |
| Neuaufbau (Generator) | Automatische Neuplanung (Karte entfiel) |
| Anwesenheit | Präsenz, Fehlzeit-Prozent (uneinheitlich) |
| „Klassenleitung in“, „Ich unterrichte“, „Ich kann vertreten in“ | Wunschklassen |
| Doppelstunde geteilt | Block geteilt |
| Eigene Rolle, Rollen und Rechte | Berechtigungsgruppe, Rolle-ID |
| Erziehungsberechtigte; Eltern | Elternteil-Konto, Guardian |

  Weitere verbotene Elemente: Schema-Revisionen, Konfigurationsschlüssel, Job-IDs, englische Status („assigned“, „open“, „removed_lessons“), die Zeile „Nicht im Haus: …“ und „Abwesende Klassen“ (abwesende Lehrkräfte stehen getrennt; Klassenabwesenheit ist eine Zeile je Klasse).
  - Abnahme: Ein Test durchsucht Oberflächentexte, Hilfetexte und Handbuch nach den Wörtern der rechten Spalte (außerhalb des Bereichs „Erweitert“, wo er ausdrücklich zulässig ist) und findet 0 Treffer.

- **OBE-132 · P1 · Status: Ist** — Personenbezeichnungen und Platzhalter. „Lehrkraft“, „Schüler/in“ bzw. „Schüler/innen“, „Eltern“, „Erziehungsberechtigte“. Platzhalter und Beispiele in Feldern sind neutral („Frau Muster“, „schule.example.org“, Beispiel-Mailadressen nur auf `example.org`); echte oder realistische Personennamen stehen nie in Oberfläche, Demo, Tests oder Dokumentation. Datumsplatzhalter folgen `TT.MM.JJJJ`.
  - Abnahme: Eine Suche nach Personennamenlisten und Nicht-`example`-Domains in Platzhaltern findet 0 Treffer; das Namensfeld der Lehrkraft zeigt „Frau Muster“ als Platzhalter.

- **OBE-133 · P1 · Status: Ist** — Musterformulierungen für Fehler. Fehler nennen die Ursache in einem Satz und die nächste Handlung; sie stehen am Feld oder, bei Ladefehlern, in der Fehlerbox mit „Erneut versuchen“.

| Situation | Text (Muster) |
|---|---|
| keine Verbindung | „Keine Verbindung. Erneut versuchen.“ |
| Zeitüberschreitung | „Der Server antwortet nicht rechtzeitig. Erneut versuchen.“ |
| unerwarteter Fehler | „Das hat nicht geklappt. Fehlernummer: 3F9A12CD. Bitte nennen Sie diese Nummer dem Support.“ |
| fehlende Berechtigung | „Dafür fehlt Ihnen die Berechtigung „Stundenplan bearbeiten“.“ (Kurzname aus dem Rechte-Katalog) |
| Pflichtfeld | „Bitte ein Startdatum angeben.“ |
| ungültiges Datum | „Bitte ein gültiges Datum angeben.“ |
| zu lang | „Bitte höchstens {n} Zeichen eingeben.“ |
| Konflikt (409) | „Diese Änderung betrifft weitere Einträge. Bitte prüfen Sie die Liste und bestätigen Sie.“ |
| Sitzung abgelaufen | „Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.“ |
| Anmeldung fehlgeschlagen | „Anmeldung nicht möglich. Bitte prüfen Sie Benutzername und Passwort.“ (nennt nie, welcher Teil falsch ist) |
| Konto gedrosselt | „Zu viele Versuche. Bitte warten Sie einen Moment und versuchen Sie es erneut.“ [unklar: Wartezeit gestaffelt, Wert ANM] |
| Datei zu groß | „Die Datei ist zu groß. Erlaubt sind höchstens {n} MB.“ |
| kein Versand | „Kein Versand eingerichtet. Bitte wenden Sie sich an das Sekretariat.“ |
| abgelaufener Zugangsbrief-Stapel | „Dieser Stapel ist abgelaufen. Bitte erzeugen Sie die Zugangsbriefe neu.“ |
| Seite nicht gefunden | „Diese Seite wurde nicht gefunden.“ |

  - Abnahme: Jede Zeile ist in einer Textdatei als Meldung vorhanden und löst im Test bei der genannten Situation genau diesen Text (bei {n} mit dem konkreten Wert) aus; kein Text enthält Code, Pfad oder interne ID.

- **OBE-134 · P1 · Status: Ist** — Musterformulierungen für Leer-, Erfolgs-, Hinweis- und Bestätigungstexte.

| Art | Text (Muster) |
|---|---|
| Leerzustand | „Keine Vertretungen“ (Aktion „Abwesenheit erfassen“); „Keine Nachrichten“ (Aktion „Neue Nachricht“); „Keine offenen Dokumente“; „Keine Treffer für „{Suchbegriff}““; „Für diesen Zeitraum ist noch kein Stundenplan festgelegt.“; „Noch nicht hinterlegt“ |
| Erfolg | „Gespeichert.“; „Krankmeldung gesendet.“; „Passwort geändert.“; „Entwurf gespeichert“; „Link kopiert.“ |
| Zustandshinweis | „3 Schultage – Attest nötig“; „Im gewählten Zeitraum sind Ferien. Es sind keine Stunden betroffen.“; „Erst die Datei hochladen, dann einreichen“; „Plan in Ordnung“ bzw. „3 Probleme“; „Keine bessere Lösung“ |
| Bestätigung löschen | Titel „Klasse 5a löschen?“, Text „Die Klasse, ihre Stunden und Kurse werden entfernt. Das lässt sich nicht rückgängig machen.“, Knöpfe „Abbrechen“ und „Klasse löschen“ (rot) |
| Bestätigung abmelden | „Möchten Sie sich abmelden?“; „Abbrechen“, „Abmelden“ |
| ungespeicherte Änderungen | Leiste „Ungespeicherte Änderungen · Speichern · Verwerfen“ |
| Plan übernehmen | Titel „Plan übernehmen?“, Text „Der Plan wird für alle Wochen ersetzt. Sie können die Übernahme im Verlauf rückgängig machen.“, Knöpfe „Abbrechen“ und „Diesen Plan nehmen“ |
| Altersgrenze Krankmeldung | „Krankmeldungen können nur Erziehungsberechtigte oder volljährige Schülerinnen und Schüler abgeben.“ (nur im Krankmeldungs-Dialog) |
| Abschlussmeldung | „Sie sind abgemeldet.“ |

  - Abnahme: Alle Muster sind als Texte vorhanden; ein Rundgang zeigt sie in den genannten Situationen; keiner enthält „du“, „!“ oder „OK“.

- **OBE-135 · P0 · Status: Ist** — Ton in E-Mails, SMS und Benachrichtigungen. Gleiche Regeln wie die Oberfläche (Sie, sachlich, ohne Ausrufezeichen). Titel und Text einer Benachrichtigung enthalten nie Noten, Gründe, Diagnosen oder Kommentare („Neue Krankmeldung“ ohne Grund, „Abgabe bewertet“ ohne Note); Push-Inhalte nennen keine Gesundheitsdaten und keine Namen anderer Kinder. Alle automatischen Mails sind als automatisch gekennzeichnet und tragen einen Abmeldelink (bei Rundmails); in Zugangs- und Rücksetz-Mails steht nie ein Passwort im Text. Der Neutralmodus (nur Hinweis und Link, kein Name im Text) ist als Schulvorgabe möglich (BEN).
  - Abnahme: Eine Krankmeldung erzeugt „Neue Krankmeldung“ ohne Grund; die Prüfung aller Mailvorlagen findet kein „du“, kein „!“ und keinen Klartext-Passwort-Platzhalter; jede automatische Mail trägt die Kennzeichnung als automatisch erzeugt.

---

## 10. Barrierefreiheit (WCAG 2.2 AA)

Schulen sind öffentliche Stellen; ohne Nachweis der Barrierefreiheit scheitert die Vergabe. Maßstab des Neubaus: WCAG 2.2 Stufe AA (einschließlich der Kriterien 2.0 und 2.1), BITV 2.0 und EN 301 549. Der Altbestand zielte auf WCAG 2.1 AA ohne ausdrückliches Konformitätsziel und ohne Nachweis.

- **OBE-136 · P0 · Status: offen** — Konformitätsziel und Nachweis. Alle Seiten und Dokumente aus Kapitel 6 erfüllen WCAG 2.2 AA. Der Nachweis besteht aus automatischer Prüfung, manueller Prüfung mit Tastatur und Screenreader, Kontrasttest der Tokens, 200 % Zoom, 390 px ohne waagerechten Seitenscroll und einer veröffentlichten Erklärung (OBE-146).
  - Abnahme: Das Prüfprotokoll (OBE-145) liegt vor und enthält keine offenen Verstöße der Stufen A und AA; Abweichungen stehen in der Erklärung.

- **OBE-137 · P0 · Status: Ist** — Tastatur. Alles ist per Tastatur bedienbar; es gibt keine Tastaturfalle außer in Dialogen (dort bewusst, mit Escape zum Verlassen); die Tab-Reihenfolge folgt der Lesereihenfolge. Pfeiltasten gelten in Reitern, Chips, Auswahlfeldern, Menüs und im Raster (OBE-088). Einzeltasten-Kürzel („?“, Schnellsuche) sind abschaltbar oder nur aktiv, wenn die Komponente den Fokus hat (WCAG 2.1.4). Der Fokus wird nach dem Öffnen von Menü und Dialog in diese verschoben und beim Schließen zurückgegeben.
  - Abnahme: Ein Durchlauf der Anmeldung, der Krankmeldung, des Stundenplans, der Nachrichten und eines Kursraums gelingt allein mit Tastatur; in keinem Zustand bleibt der Fokus gefangen außer im offenen Dialog; die Einstellung „Tastenkürzel aus“ unterbindet „?“.

- **OBE-138 · P0 · Status: offen** — Fokus sichtbar und nicht verdeckt. Der Fokus ist an jedem bedienbaren Element mit einem 2-px-Rahmen in der Fokusfarbe sichtbar (mindestens 3:1 zur Umgebung, in beiden Schemata). Kopfzeile, untere Leiste, Meldungen und Rückgängig-Leiste verdecken das fokussierte Element nie (WCAG 2.4.11): der Scroll-Abstand berücksichtigt 56 px Kopfzeile und 60 px untere Leiste. Nach einem Seitenwechsel steht der Fokus am Seitentitel oder am Anfang des Inhalts, nicht in der Navigation.
  - Abnahme: Beim Durchtabben der Stundenplan-Seite bei 390 px liegt das fokussierte Element nie unter der unteren Leiste; nach Klick auf einen Menüeintrag steht der Fokus am neuen Seitentitel; Messung des Fokusrahmens ergibt 2 px und mindestens 3:1.

- **OBE-139 · P0 · Status: offen** — Darstellung bei Zoom, Textabstand und Reflow. 200 % Zoom ohne Verlust von Inhalt oder Funktion; Reflow ohne zweidimensionales Scrollen bei 320 CSS-Pixeln Breite (Ausnahme: Raster und Tabellen in ihrem eigenen Rahmen); veränderter Textabstand (Zeilenhöhe 1,5, Absatzabstand 2×, Buchstabenabstand 0,12 em, Wortabstand 0,16 em) lässt nichts abschneiden; Text lässt sich bis 200 % vergrößern. Die Betreiberregel (360/390 px ohne Seitenscroll) bleibt bestehen.
  - Abnahme: Bei 320 px Breite und 400 % Zoom ist kein Seitenscroll in zwei Richtungen nötig (Raster scrollen in ihrem Rahmen); mit dem Textabstand-Prüfskript ist kein Text abgeschnitten.

- **OBE-140 · P0 · Status: offen** — Zielgrößen und Zeigergesten. Zeigerziele sind mindestens 24 × 24 CSS-Pixel (WCAG 2.5.8) – maßgeblich bleibt die Betreiberregel: 44 px auf Touch-Geräten, 40 px Steuerelement-Höhe und 32 px kleine Nebenaktion auf dem Desktop. Jede Geste mit Weg oder Mehrfinger (Wischen im Stundenplan, Ziehen) hat eine Schaltflächen-Alternative (Tag vor/zurück, „Verschieben nach …“). Funktionen reagieren beim Loslassen, nicht beim Drücken, und sind abbrechbar.
  - Abnahme: Eine automatische Messung findet kein bedienbares Ziel unter 24 × 24 px und auf Touch keines unter 44 px Höhe (Ausnahme: Text im Fließtext); der Tag-Wechsel im Stundenplan funktioniert ohne Wischen über „Vorheriger Tag“/„Nächster Tag“.

- **OBE-141 · P0 · Status: Ist** — Struktur für Bildschirmleser. Dokumentsprache Deutsch; Seitenbereiche (Kopf, Navigation, Hauptinhalt) sind als solche ausgezeichnet; die Sprungmarke „Zum Inhalt springen“ führt zum Hauptinhalt; genau eine Überschrift der Ebene 1 je Seite, Überschriften in logischer Reihenfolge ohne Sprünge. Jedes Feld hat eine programmatische Beschriftung; Hilfe und Fehlertext sind per beschreibender Verknüpfung am Feld; Symbolknöpfe tragen eine Bezeichnung; Symbole sind dekorativ (ausgeblendet), ihre Bedeutung steht als Text daneben; Tabellen haben Kopfzellen; Diagramme haben Textalternativen (Tabelle für Bildschirmleser); Zähler sind lesbar („3 ungelesen“); Meldungen sind Live-Regionen; Dialoge sind als Dialog mit Titel ausgezeichnet; Statusabzeichen haben Text. Tabs sind mit korrekten Bezügen ausgezeichnet; Auswahlzustand liegt am richtigen Element (nicht an einer Tabellenzeile).
  - Abnahme: Die automatische Prüfung meldet 0 schwere Verstöße (fehlende Beschriftung, doppelte IDs, falsche Rollen); mit NVDA und VoiceOver liest die Krankmeldung Beschriftung, Pflicht, Hilfe und Fehler vollständig vor.

- **OBE-142 · P0 · Status: offen** — Eingabe, Fehler und Anmeldung (WCAG 3.3). Fehler werden benannt und beschrieben (3.3.1), Vorschläge zur Korrektur gegeben (3.3.3), Beschriftungen und Anweisungen stehen vor dem Feld (3.3.2); bei rechtlich oder datenrelevanten Eingaben gibt es Prüfen, Bestätigen oder Rückgängig (3.3.4: Krankmeldung zurücknehmen, Dialog vor Löschen, Vorschau vor Import); bereits Eingegebenes wird nicht erneut verlangt (3.3.7: Kind-Auswahl bleibt, Assistenten behalten Eingaben, Entwürfe); die Anmeldung kommt ohne kognitiven Funktionstest aus (3.3.8): Einfügen in Passwort- und Codefelder erlaubt, Passwort-Manager unterstützt (OBE-050), Zwei-Faktor-Code als 6-stelliges Feld mit Einfügen, keine Zeichen- oder Rätselaufgaben.
  - Abnahme: Ein Passwort lässt sich in die Anmeldung einfügen und per Passwort-Manager füllen; nach einem Validierungsfehler bleiben alle anderen Eingaben erhalten; die Rücknahme einer Krankmeldung ist ohne Datenverlust möglich.

- **OBE-143 · P1 · Status: offen** — Konsistente Navigation und Hilfe. Gleiche Bausteine heißen überall gleich und stehen an gleicher Stelle (3.2.3, 3.2.4); der Zugang zur Hilfe („Hilfe“ im Menü, Seitenhilfe neben dem Titel, Feedback-Knopf falls vorhanden) liegt auf jeder Seite an derselben relativen Stelle (3.2.6). Ein Kontextwechsel geschieht nie allein durch Fokus oder Eingabe.
  - Abnahme: Auf fünf zufälligen Seiten liegen Seitenhilfe und Menüeintrag „Hilfe“ an derselben Stelle; ein Fokuswechsel löst keine Navigation aus.

- **OBE-144 · P0 · Status: Ist** — Bewegung reduzieren. Bei der Systemeinstellung „Bewegung reduzieren“ entfällt jede Bewegung: Übergänge 0 s, Animationen laufen höchstens einmal, der Spinner läuft langsam bzw. statisch, das Monitor-Laufband wird als statische Liste gezeigt (Seiten blättern statt scrollen). Nichts blinkt mehr als dreimal pro Sekunde. Automatisch bewegte oder aktualisierte Inhalte, die länger als 5 Sekunden laufen (Monitor), lassen sich anhalten (WCAG 2.2.2).
  - Abnahme: Mit der Systemeinstellung bewegt sich auf keiner Seite etwas außer Nutzereingaben (Aufzeichnung); das Monitor-Laufband steht still als Liste; ein laufender Autoscroll hat ein Bedienelement „Anhalten“.

- **OBE-145 · P0 · Status: offen** — Prüfungen. Teil der Testsuite: automatische Prüfung der 20 wichtigsten Seiten je Rolle mit einem Barrierefreiheits-Prüfwerkzeug (z. B. axe-core über Playwright) ohne schwere Verstöße; Kontrast-Test der Tokens (OBE-020). Manuell und dokumentiert: Tastatur und Screenreader (NVDA, VoiceOver) für Anmeldung, Krankmeldung, Stundenplan, Nachrichten, Kursraum und Vertretungsplan; 200 % Zoom; 390 px ohne waagerechten Seitenscroll; Hell und Dunkel. Prüfung vor jedem Release (QUA).
  - Abnahme: Die Pipeline führt die automatische Prüfung aus und scheitert bei schweren Verstößen; das manuelle Protokoll mit Datum, Prüfgerät und Ergebnis liegt für alle sechs genannten Abläufe vor.

- **OBE-146 · P0 · Status: offen** — Erklärung zur Barrierefreiheit. Eine öffentliche Seite `/barrierefreiheit` nach der BITV-Vorlage nennt Konformitätsstand, bekannte Barrieren (z. B. das nur dezent sichtbare Monitor-Menü, Raster-Bedienung bis zur Fertigstellung) und einen Rückmeldeweg; sie ist in der Anmeldeseite und im Profilmenü verlinkt. Der Inhalt der Erklärung legt der Betreiber fest [unklar: Text und Rückmeldeweg stehen nicht in den Quellen; Audit-Befund „fehlt“].
  - Abnahme: `/barrierefreiheit` ist ohne Anmeldung erreichbar, enthält einen Rückmeldeweg und ist von `/login` aus verlinkt.

- **OBE-147 · P1 · Status: offen** — Zugängliche PDF-Dokumente. PDF-Zugangsbriefe und Handbuch-PDF tragen Struktur-Tags, Dokumenttitel, Dokumentsprache Deutsch und eine sinnvolle Lesereihenfolge; der QR-Code hat eine Textalternative mit der Adresse.
  - Abnahme: Ein PDF-Prüfwerkzeug meldet für einen Zugangsbrief keine Struktur- oder Sprachfehler; der Text neben dem QR-Code enthält die Anmeldeadresse als Text.

---

## 11. Handy-Ansicht und App-Verhalten

- **OBE-148 · P0 · Status: Ist** — Touch statt Maus. Auf Geräten mit grobem Zeiger gibt es keine Hinweise, die nur mit Maus oder Tastatur gehen („Enter“, „Rechtsklick“, „Maus darüber“, „Strg+…“, „Drag & Drop“); stattdessen gelten „antippen“ und „gedrückt halten“. Betreiber (12.10.2026): „… die du auf dem PC brauchst, aber auf Handys oder Mobilgeräten ohne Tastaturen oder Mäuse sind irrelevant oder müssen bearbeitet werden.“ Funktionen, die nur mit Maus gehen, haben eine Tipp-Alternative (Stundenplan-Editor: „Block antippen“; Knopf „Verschieben nach …“). „Hierher ziehen“ bei Datei-Uploads erscheint nur am PC; der Emoji-Knopf nur am PC; am Handy ist Enter in Chats ein Zeilenumbruch. Die Eingabeart wird über die Zeigerart des Geräts (grob oder fein) erkannt, nicht über die Gerätekennung.
  - Abnahme: Mit emuliertem Touch-Gerät (390 px, grober Zeiger) findet eine Textsuche über alle Seiten keines der Wörter „Maus“, „Rechtsklick“, „Strg“, „Enter“, „ziehen“, „Drag“; der Stundenplan-Editor lässt sich mit zwei Tipps bedienen.

- **OBE-149 · P1 · Status: Ist** — Handy-Layout. Einspaltig mit 16 px Seitenrand und Platz für die untere Leiste; Kopfzeile mit Titel, Live-Anzeige, Schema und Konto; Dialoge in voller Breite und Höhe; Datumsfelder in einer Zeile; Reiterleisten scrollen waagerecht in der Leiste; Tippflächen für kleine Links und Chip-Kreuze sind größer (OBE-043). Nachrichten: Liste und Gespräch nacheinander. Klassenbuch: eine Karte je Schüler/in. Aufsichten: Karten je Pause. Tabellen: Kartenliste (OBE-064). Raster: Liste (OBE-089). Stundenplan-Details: Blatt von unten (OBE-090). Eingabefelder 16 px, damit iOS nicht zoomt.
  - Abnahme: Rundgang bei 390 px über Start, Stundenplan, Nachrichten, Klassenbuch, Aufsichten und Krankmeldungen: Alle Muster dieser Anforderung sind erkennbar, es gibt keinen Seitenscroll, kein Eingabefeld löst Zoom aus.

- **OBE-150 · P1 · Status: offen** — Vollständige Geräteprüfung. Betreiber (12.10.2026): Die Oberfläche in allen Größen prüfen (Handy, Tablet, PC): zu große Texte, Verschiebungen, zu enge Stellen, zu schwere oder überladene Übersichten, unnötige Knöpfe (verstecken oder anders lösen). Der Altbestand prüfte nur eine Stichprobe (Handy 360 px für fünf Rollen, Tablet und PC nur Administration; Hell-Modus, Monitor und Druck nicht geprüft). Im Neubau wird die volle Matrix geprüft und der Prüfumfang im Protokoll ausdrücklich genannt.
  - Abnahme: Ein Prüfprotokoll enthält die Matrix aus allen Rollen aus Kapitel 6 × Breiten 360/390/820/1440 px × Hell/Dunkel, dazu Monitor und Druckansichten, und nennt je Zelle das Ergebnis; Lücken sind als „nicht geprüft“ ausgewiesen.

- **OBE-151 · P3 · Status: offen** — Entlastung kleiner Bildschirme (Vorschläge vom 12.10.2026, nicht freigegeben). Filterleisten (Stundenplan, Vertretung) hinter einem Knopf „Filter“ mit aktiven Filtern als Chips; seltene Schalter („Regelplan bearbeiten“, Raster/Liste) in einem „Mehr“-Menü; auf dem Tablet leere Sa/So-Spalten ausblenden; Klassenbuch am Handy mit zwei großen Schaltern „anwesend / fehlt“ je Schüler/in und Notizfeld erst auf Tipp; Rechte-Seite mit einklappbaren Gruppen.
  - Abnahme: Nach Freigabe: bei 390 px sind Filter hinter „Filter“, das „Mehr“-Menü enthält die seltenen Schalter und im Klassenbuch ist ein Schüler mit einem Tipp als „fehlt“ markierbar; ohne Freigabe bleibt der Stand von OBE-149.

- **OBE-152 · P2 · Status: Ist** — Zum Startbildschirm hinzufügen. Die Seite lässt sich am Handy wie eine App zum Startbildschirm hinzufügen (so beschreiben es die Anleitungen für Eltern und Schüler/innen). Die Verknüpfung trägt den konfigurierten Produktnamen und das Logo.
  - Abnahme: Auf Android und iOS lässt sich die Seite zum Startbildschirm hinzufügen; der Name der Verknüpfung entspricht dem konfigurierten Produktnamen.

- **OBE-153 · P2 · Status: offen** — Installierbare App (PWA). Manifest, Symbole und Service Worker: installierbar auf Android, iOS (ab 16.4) und Desktop; Offline-Seite; der zuletzt geladene Stundenplan ist ohne Netz lesbar. Offline gespeicherte Inhalte enthalten keine Gesundheitsdaten und werden beim Abmelden gelöscht. Entscheidung des Betreibers im Altbestand: Push und PWA „bewusst später“ (13.10.2026); der Neubau plant sie ein, liefert sie aber nach dem Pflichtumfang. Native Apps in den App-Stores sind ausgeschlossen (Kapitel 18).
  - Abnahme: Nach Installation öffnet die App ohne Adressleiste; im Flugmodus zeigt sie den zuletzt geladenen Stundenplan der Woche und eine Offline-Meldung; nach Abmelden ist der Offline-Speicher leer.

- **OBE-154 · P2 · Status: offen** — Push-Benachrichtigungen. Web Push mit Abo je Gerät, widerrufbar; Anlässe: Vertretung, Entfall oder Raumänderung in eigenen bzw. Kind-Stunden von heute und morgen, neue Nachricht, Krankmeldung in der eigenen Klasse (Klassenleitung). Je Person einstellbar, worüber benachrichtigt wird; Ruhezeiten (z. B. 20 bis 6 Uhr) außer für heutigen Unterricht. Inhalte ohne Gesundheitsdaten und ohne Namen anderer Kinder („Änderung im Plan für morgen“). Versand einer Planänderung an 2.500 Abos unter 30 Sekunden. [unklar: Der Altbestand nennt „kein Drittanbieter“, Web Push läuft technisch über Dienste der Browserhersteller; Klarstellung durch BEN/REH.]
  - Abnahme: Ein Eltern-Gerät mit Abo erhält bei Entfall einer Stunde des Kindes eine Push-Meldung ohne Namen und ohne Grund; nach Widerruf des Abos keine mehr; innerhalb der Ruhezeit kommt keine Meldung außer für heutigen Unterricht; Last-Messung: 2.500 Abos in unter 30 s.

---

## 12. Druckansichten und PDF

- **OBE-155 · P1 · Status: Ist** — Druckdarstellung allgemein. Druckansichten sind hell (Schwarz auf Weiß, unabhängig vom Farbschema), A4, ohne Navigation, Bedienleiste, Hilfe-Symbole, Meldungen und Sprechblasen; sie tragen eine Kopfzeile mit Titel und Stand; Hinweise erscheinen vollständig statt gekürzt; Statusfarben sind zusätzlich durch Kurzzeichen oder Wort unterscheidbar (Schwarz-Weiß-Druck). Produktname und Schulname kommen aus der Konfiguration.
  - Abnahme: Die Druckvorschau von `/druck/vertretung` zeigt keine Bedienleiste, keine Sprechblasen und hellen Hintergrund auch bei dunklem Schema; ein gekürzter Hinweis erscheint im Druck vollständig; in Graustufen sind Vertretung und Entfall unterscheidbar.

- **OBE-156 · P1 · Status: Ist** — Aushang des Vertretungsplans (`/druck/vertretung`). Öffentliche Sicht ohne Gründe: abwesende Lehrkräfte nur mit Kürzel und Stunden (Gründe nie), keine „Abwesende Klassen“ (Klassenabwesenheit eine Zeile je Klasse), Gruppierung nach Klasse, Sortierung nach Art in fester Reihenfolge, Option „eine Seite pro …“ [unklar: Einheit nicht in den Quellen]; der Standort steht mit Namen statt Kürzel („S1“) [offen]. Papier unterliegt keinem Zugriffsschutz; deshalb enthält der Aushang nur Angaben, die auch am Monitor stehen dürfen.
  - Abnahme: Der Aushang enthält zu keiner abwesenden Lehrkraft einen Grund; ein Vergleich mit der Monitor-Sicht zeigt dieselbe Datenmenge; die Standortangabe lautet ausgeschrieben.

- **OBE-157 · P3 · Status: offen** — Stundenplan als PDF oder Druck. Stundenplan je Kind (Woche), Klasse und Lehrkraft als PDF bzw. Druckansicht (`/druck/stundenplan/:kind/:ref`, A4); der Altbestand hatte den Druck entfernt; Wettbewerbs-Lücke „Stundenplan als PDF für Eltern“. Datenumfang wie die Stundenplanansicht (fremde Pläne 404).
  - Abnahme: Ein Eltern-Konto erhält das PDF der Woche seines Kindes mit allen Vertretungen und Entfällen; der Aufruf für ein fremdes Kind liefert 404.

- **OBE-158 · P0 · Status: Ist** — Zugangsbriefe als PDF. A4; Einzel-PDF je Person, Sammel-PDF (eine Seite je Brief), ZIP mit Einzel-PDFs (nur bei mehreren Briefen); Dateiname `<Klasse>_<Nachname>_<Vorname>.pdf`, Elternbriefe `…_Eltern.pdf`. Inhalt: Schulname (und Schul-Logo, OBE-173), Datum, Titel („Zugangsdaten für <Name> (Klasse 5a)“ bzw. „… für die Eltern von <Kind>“), Kasten mit Anmeldeadresse und QR-Code zur Anmeldeseite, Benutzername, Startpasswort in Festbreitenschrift, Schritte, Hinweise aus der Anmelde-Richtlinie (z. B. „Verbinden Sie danach …“). Anrede durchgehend Sie, auch für minderjährige Schüler/innen (der Altbestand duzte sie; überholt durch OBE-006). Ein Stapel ist 60 Minuten abrufbar, nur für die erzeugende Person oder Administration; danach 410. E-Mail-Versand: je Person eine Mail mit PDF-Anhang, kein Passwort im Text. Ablauf-Details: FOR, ANM.
  - Abnahme: Ein Brief für ein 11-jähriges Kind enthält „Sie“-Formulierungen, den QR-Code und das Startpasswort; der Dateiname folgt dem Muster; ein anderes Konto erhält 404, nach 60 min 410; die Begleit-Mail enthält kein Passwort.

- **OBE-159 · P1 · Status: Ist** — Formular-PDF. Leeres Formular (Ausfüllen auf Papier), ausgefülltes Archiv-PDF (mehrseitig, A4), PDF einer einzelnen Einreichung, Sammel-PDF; der PDF-Erzeuger bettet QR-Codes ein; unterschriebene Scans lassen sich hochladen. Die Krankmeldungsseite bietet zwei druckbare Formulare (Entschuldigung, Beurlaubung). Der Sammel-PDF-Export wird nicht stillschweigend gekappt (Altbestand: 300).
  - Abnahme: Ein Sammel-PDF mit 350 Einreichungen enthält alle 350; das leere Formular entspricht der Vorschau im Baukasten.

- **OBE-160 · P2 · Status: offen** — Weitere Ausgaben. Folgende Ausgaben haben eine PDF- oder Druckfassung nach den Regeln dieses Kapitels; ihre Inhalte legen die Fachdateien fest: PDF-Liste für die Notenkonferenz (NOT, Ist); Lernentwicklungsbericht (A4, mehrere Seiten, Fußzeile „Vertraulich – nur für Lehrkräfte und Eltern bestimmt“, ohne Beobachtungsnotizen; KUR, Ist); Klassenlisten drucken und als CSV exportieren (Wandertag, Klausuraufsicht, Elternabend; offen); Klassenbuch je Woche und Halbjahr (offen, KLB); Laufzettel des Elternsprechtags als PDF und iCal (offen, FOR); Rechnung und Quittung (eine Seite A4; BET, Ist).
  - Abnahme: Für jede genannte Ausgabe existiert eine Druck- oder PDF-Fassung mit hellem Hintergrund und Kopfzeile; die Fußzeile des Lernentwicklungsberichts lautet exakt wie angegeben.

- **OBE-161 · P1 · Status: Ist** — PDF-Zeichensatz und Metadaten. PDFs stellen alle deutschen Sonderzeichen und typografische Zeichen (Umlaute, ß, Anführungszeichen, Pfeile) korrekt dar; im Altbestand fehlte der Pfeil „→“ (Ersatz „›“). Unbekannte Zeichen erscheinen nie als Platzhalter. Produktname und Schulname in Inhalt und Metadaten kommen aus der Konfiguration, nicht aus festem Text; Dokumentsprache Deutsch.
  - Abnahme: Ein PDF mit „Kurs M 5a → Woche 2 entfällt, „zitiert“, Größe 1,5 KB“ zeigt alle Zeichen; die Metadaten nennen den konfigurierten Produktnamen; eine Namensänderung der Konfiguration verändert Inhalt und Metadaten ohne Codeänderung.

---

## 13. Monitor- und Kiosk-Ansicht

Der Vertretungsmonitor läuft auf Großbildschirmen (Aula, Flur, Lehrerzimmer, zweiter Standort), nach Wunsch auch am Tablet oder Handy. Er hat dieselben Tokens wie die übrige Oberfläche und eigene Zusatzregeln. Eine getrennte „Vertretungs-Ansicht für Fernseher“ ist gestrichen (16.10.2026): der Monitor deckt sie ab.

- **OBE-162 · P1 · Status: Ist** — Monitor-Ansicht. Route `/monitor/:standort?` (Standort optional). Vollbild mit: Uhr (eigener Baustein, damit nicht die ganze Seite jede Sekunde neu gezeichnet wird), heute und nächster Schultag in Tagesspalten (Anzahl der Tage per Adresse `?tage=1..5`, höchstens fünf; Ferien werden übersprungen), Einträge gruppiert nach Klasse, Mitteilungsband (Aushang oben, Laufband unten; wichtige Mitteilungen hervorgehoben), Block „Abwesende Lehrkräfte“, Leerzustand, Angabe „Stand: 07:42“ und Hervorhebung der laufenden Stunde. Automatisches seitenweises Scrollen ist nur auf großen Bildschirmen aktiv. Aktualisierung über die Live-Verbindung und zusätzlich alle 120 Sekunden per Abfrage. Fachregeln: VER.
  - Abnahme: Der Monitor zeigt „Stand: 07:42“ und die laufende Stunde hervorgehoben; ein gemessener Render-Zähler zeigt, dass beim Sekundentakt der Uhr nur der Uhr-Baustein neu gezeichnet wird; `?tage=3` zeigt drei Schultage; die Ferienwoche wird übersprungen.

- **OBE-163 · P1 · Status: offen** — Monitor mobil und ruhig. Unter 48 em Breite oder bei Touch-Bedienung gibt es nativen Bildlauf statt Autoscroll, eine Spalte, einen Umschalter „Heute · Morgen“ und Einträge als Karten je Klasse (Tabelle erst ab 48 em). Höhe `100dvh` (an die sichtbare Fläche angepasst, nicht an die Fensterhöhe); die Kopfzeile bricht um; der Vollbild-Knopf ist am Handy ausgeblendet. Bei 375 px sind keine Spalten abgeschnitten. Der Altbestand schnitt am Handy ab und zeichnete die Seite jede Sekunde neu.
  - Abnahme: Bei 375 px zeigt der Monitor eine Spalte mit dem Umschalter „Heute · Morgen“, nativem Scrollen und ohne abgeschnittene Inhalte (Bildschirmfoto-Test); der Vollbild-Knopf fehlt.

- **OBE-164 · P0 · Status: Ist** — Inhalte und Datenschutz am Monitor. Abwesende Lehrkräfte erscheinen standardmäßig nur mit Kürzel (Name und Stunden nach Einstellung), Gründe nie; die Schulleitung kann die Anzeige über die Einstellung „Anzeige abwesender Lehrkräfte“ abschalten (in der öffentlichen Demo gesperrt). Klassenabwesenheit erscheint als eine Zeile je Klasse (ein Wandertag eine Zeile), nicht je Stunde; „Abwesende Klassen“ und die Zeile „Nicht im Haus: …“ entfallen. Automatisch berechnete Vertretungen erscheinen im Bestätigungsmodus erst nach Freigabe. Keine Namens-Sprechblasen; Hinweistexte sind gekürzt (volle Fassung nur im Druck). Der Monitor sieht keine Formular-Übersicht.
  - Abnahme: Eine Lehrkraft mit Krankmeldung erscheint als Kürzel ohne Grund; mit abgeschalteter Einstellung fehlt der Block; im Bestätigungsmodus fehlt eine noch nicht freigegebene Vertretung; ein Wandertag der 6b ist eine Zeile.

- **OBE-165 · P0 · Status: offen** — Zugang und Geräte. Die Monitor-Seite lässt sich ohne Anmeldung laden; die Daten liefert der Server nur an ein Monitor-Konto mit `monitor.read` (Rolle Monitor, optional an einen festen Standort gebunden; ein Konto für Standort S2 sieht nur S2). Statt nach 30 Tagen abgemeldet zu werden, bleibt ein Monitor-Gerät über ein widerrufbares Geräte-Token angemeldet [offen, Paket Monitor-Profile]. Ein Aufruf ohne Konto zeigt eine Anmeldung bzw. die Meldung „Kein Zugriff“, keine Vertretungsdaten.
  - Abnahme: Ein Aufruf von `/monitor/S2` ohne Konto zeigt keine Vertretungsdaten; das Monitor-Konto von S1 erhält für S2 keine Daten; das Widerrufen des Geräte-Tokens meldet das Gerät beim nächsten Abruf ab.

- **OBE-166 · P0 · Status: Ist** — Verstecktes Menü im Monitor. Der Monitor hat einen Ausgang. Betreiber (17.10.2026): „ich habe keine option aus dem monitor ding heraus zu gehen ich kann mich nicht abmnelden andere schul ansich teistellen etc“. Ein Menü-Knopf (☰) sitzt oben rechts neben der Uhr, ist bewusst dezent und wird beim Darüberfahren deutlich. Menüpunkte: „Konto wechseln“, „Weiteres Konto anmelden“, „Abmelden“ (mit Bestätigung), „Standort wechseln“ (nur wenn dem Monitor-Konto kein fester Standort zugewiesen ist), „Zurück zur Startseite“ (nur wenn der Monitor mit einem normalen Konto geöffnet wurde). Ein Monitor-Konto mit festem Standort bleibt dort. Barrierefreiheit (Konflikt mit der „kaum sichtbaren“ Darstellung, vom Betreiber nicht bestätigt): Der Knopf ist per Tastatur erreichbar und wird bei Fokus voll sichtbar mit 2-px-Fokusrahmen, hat den zugänglichen Namen „Monitor-Menü“ und im Ruhezustand mindestens 3:1 Kontrast zum Hintergrund [unklar: Betreiber hat den „fast unsichtbaren“ Zustand nicht bestätigt; Festlegung Neubau: dezent, aber erkennbar mit 3:1]. Auf Touch öffnet ein Tipp in die Ecke das Menü.
  - Abnahme: Ein Monitor-Konto ohne festen Standort sieht im Menü „Standort wechseln“, eines mit festem Standort nicht; „Abmelden“ fragt nach und führt zur Anmeldung; per Tab erreicht man den Knopf und er wird voll sichtbar; der Kontrast im Ruhezustand beträgt mindestens 3:1.

- **OBE-167 · P1 · Status: Ist** — Monitor-Verwaltung `/monitore`. Je Monitor (Standort) gibt es eine Karte mit Einstellungen: Aushang oben (kurzer Hinweis), Laufband unten, Hervorhebung wichtiger Mitteilungen. Recht `monitor.manage` (Administration, Schulleitung, Sekretariat). Das Monitor-Konto eines Standorts ist an diesen gebunden. Die Einstellungen liegen im Schuldokument, nicht im Browser.
  - Abnahme: Ein Hinweis, der in der Verwaltung für Standort S2 gesetzt wird, erscheint am S2-Monitor ohne Neuladen und nicht am Monitor von S1; ein Konto ohne `monitor.manage` sieht die Seite nicht.

- **OBE-168 · P1 · Status: offen** — Modulare Monitor-Profile. Jeder Bildschirm bekommt ein Profil (Name, Standort, Kacheln, Optionen, zugeordnete Monitor-Konten). Kacheltypen (Positivliste): Tagesplan, abwesende Lehrkräfte, Mitteilungen, Uhr, laufende Stunde, Klausuren, Raumänderungen, Termine. „Monitor einrichten“: Kacheln hinzufügen, entfernen, anordnen, in der Größe ändern, Vorschau mit Beispieldaten; Optionen als Auswahlfelder (Bildlauf langsam/normal/schnell, Schriftgröße, Folgetag ab Uhrzeit), keine Schieberegler; Tagesplan-Kachel: heute oder morgen, gruppiert nach Klasse oder Stunde, Spaltenauswahl. Adressen `/monitor/p/:profil` und weiter `/monitor/:standort`. Kacheln passen sich der Breite an (Tabelle ab 48 em, darunter Karten). Zwei Monitore mit verschiedenen Profilen laufen gleichzeitig.
  - Abnahme: Ein Profil „Aula“ mit Tagesplan und Uhr und ein Profil „Lehrerzimmer“ mit abwesenden Lehrkräften und Klausuren laufen gleichzeitig und zeigen jeweils nur ihre Kacheln; ein Kacheltyp außerhalb der Liste wird abgelehnt.

---

## 14. Marke: Produktname, Logo, Schulname

- **OBE-169 · P0 · Status: Ist** — Produktname an einer einzigen Stelle. Der sichtbare Produktname ist ein einziger Konfigurationswert; Server und Oberfläche lesen denselben Wert. Er erscheint in: Kopfzeile, Anmeldeseite, Dokumenttitel (Browser-Tab), Verknüpfung zum Startbildschirm bzw. Manifest, PDF-Inhalt und -Metadaten, E-Mail- und SMS-Texten, Hilfe und Handbuch (als Platzhalter), Kalender-Feeds (Produktkennung), der Programmkennung ausgehender Anfragen und Rechnungen. Er steht nie fest in einem Text; die Wortmarke ist Text, kein Bild. Eine Änderung des Wertes und der Logo-Datei genügt, um das Produkt umzubenennen. Alle Texte des Handbuchs nennen den Namen über den Platzhalter.
  - Abnahme: Ein Test sucht im Quelltext (Oberfläche und Server) nach dem aktuellen Produktnamen und findet ihn nur in der Konfiguration; die Änderung des Wertes ändert Kopfzeile, Titel, PDF-Metadaten, Mailbetreff und Kalender-Produktkennung gleichzeitig.

- **OBE-170 · P1 · Status: Ist** — Technische Namen bleiben unabhängig vom Produktnamen. Paketname „schulmanager“, Präfix `SM_` der Umgebungsvariablen, Cookies (z. B. `sm_session`), Header `X-Schulmanager-*` und `X-CSRF-Token`, Schnittstellen-Basis `/api/v1`, Container-, Image-, Domain- und Pfadnamen ändern sich bei einem Produktnamenwechsel nicht. Sie sind technisch einheitlich „schulmanager“; Bestandsinstallationen behalten alte technische Namen lesbar (Rollback und Updates). Der Altbestand mischte `schulpuls-…`-Namen in Updater, Pfaden und einem Lastverteilungs-Cookie; im Neubau gibt es nur die einheitliche Fassung.
  - Abnahme: Eine Prüfung aller technischen Bezeichner (Cookies, Header, Variablen, Images) findet nur das einheitliche Präfix; die Änderung des Produktnamens verändert keinen von ihnen.

- **OBE-171 · P1 · Status: offen** — Produktname: Entscheidung offen. Betreiber (13.10.2026): „dass der Schulmanager zu Umgenannt wird zu einem schulspezifischen Namen, in dem Namen soll Schule oder zumindest Teile … vorkommen.“ Als Arbeitstitel dient „Schulpuls“ (Puls als Takt der Schule). Die Namensprüfung (16.10.2026) fand den Namen im Bildungsbereich bereits von einem anderen Unternehmen genutzt; Verwechslungsgefahr hoch; empfohlen: den Namen nicht nach außen verwenden, bevor Marken (DPMA, EUIPO, WIPO) selbst geprüft sind. Kandidaten: Schulhafen (Empfehlung), Schulfeld, Schulfunke, außerdem Schultor, Schulkern, Schulkreis. Der Betreiber nannte am 17.10.2026 „Schulplus“; diese Schreibweise gibt es im Altbestand nirgends. Der Neubau muss einen Namenswechsel allein durch Konfiguration und Logo-Datei ermöglichen (OBE-169).
  - Abnahme: Die endgültige Namensentscheidung des Betreibers liegt schriftlich vor und ist im Konfigurationswert eingetragen; bis dahin erscheint der Name nicht in öffentlichen Seiten und Briefen, die nach außen gehen [unklar: Entscheidung und rechtliche Prüfung des Betreibers ausstehend].

- **OBE-172 · P1 · Status: Ist** — Logo. Betreiber (13.10.2026): „Ich will auch, dass du mein Logo designst“. Aufbau: eine Kachel (Rechteck), eine Pulslinie und ein gelber „Live“-Punkt, mit festgelegter Strichstärke und festgelegtem Punktradius; die Geometrie kommt aus genau einer Quelle (Altbestand: abweichende Maße in mehreren Dateien). Varianten: farbig (blaue Kachel) für Anmeldeseite, Browser-Symbol, PDFs und Briefe; einfarbig in gleicher Form, in der aktuellen Textfarbe und ohne Kachel, für die Kopfzeile; beide in Hell und Dunkel mit mindestens 3:1 Kontrast. Das Logo ist dekorativ, wenn der Produktname daneben steht; sonst trägt es den Produktnamen als Alternativtext. Konkrete Maße: [unklar: Strichstärke, Punktradius, Kachelgröße nicht in den Quellen].
  - Abnahme: Alle Logo-Verwendungen (Kopfzeile, Anmeldeseite, Browser-Symbol, PDF, Mail) stammen aus derselben Geometrie (Vergleichstest der Pfade); die einfarbige Variante hat dieselbe Form wie die farbige; das Logo erreicht in Hell und Dunkel mindestens 3:1.

- **OBE-173 · P2 · Status: offen** — Schulname und Schul-Logo. In der Einrichtung hinterlegt die Schule Namen und optional ein Logo; beide erscheinen auf der Anmeldeseite, in Zugangsbriefen und Elternbriefen (OBE-158). Logos sind Rastergrafiken (PNG oder JPEG), keine SVG-Dateien; Alternativtext ist der Schulname. Fehlt das Logo, erscheint nur der Name. Der Altbestand hatte diese Anzeige nicht.
  - Abnahme: Nach dem Hochladen eines PNG-Logos erscheint es auf der Anmeldeseite und im Zugangsbrief-PDF; ein SVG wird abgelehnt; ohne Logo erscheint nur der Schulname.

---

## 15. Weitere Oberflächen-Wünsche (Wettbewerbs-Ideen, kleine Funktionen)

Diese Funktionen stammen aus der Wettbewerbsrecherche vom 16.10.2026. Der Betreiber sagte dazu: „die Sachen noch nicht einbauen, erst mal mir sagen, es sind wirklich nur so kleine Sachen.“ Eine spätere Freigabe liegt nicht vor; sie sind deshalb P3 und Status offen. Wo eine Datenhaltung betroffen ist, gelten die Regeln der Fachdateien.

- **OBE-174 · P3 · Status: offen** — Schnellsuche. Eine Suchzeile für Personen, Klassen, Kursräume und Seiten, geöffnet mit Strg+K (auf Apple-Geräten Cmd+K) und zusätzlich über einen Such-Knopf in der Kopfzeile (auch für Touch und für Menschen ohne Kürzel). Ergebnisse werden nach Rechten und Datenumfang gefiltert (fremde Daten sind nicht auffindbar; Schüler/innen finden Mitschüler nur, wenn die Schule Nachrichten zwischen ihnen erlaubt); Suche nach Wortteilen; Auswahl mit Pfeiltasten und Enter, Escape schließt; Ergebnisse tragen Typ und Name als Text. Chats sind nur nach Namen durchsuchbar.
  - Abnahme: Strg+K öffnet die Suche; „5a“ findet die Klasse und die Seite „Klassen“, aber für ein Schüler-Konto keine Lehrerkonten außerhalb seines Stundenplans; ein Suchergebnis für eine fremde Klasse erscheint nicht; die Suche ist mit Tastatur und mit dem Such-Knopf bedienbar.

- **OBE-175 · P3 · Status: offen** — Tastenkürzel. „?“ öffnet die Hilfe außerhalb von Texteingaben, Strg+K die Suche, weitere Kürzel für die Navigation; eine Übersicht der Kürzel ist über die Hilfe erreichbar. Alle Einzeltasten-Kürzel lassen sich im Benutzermenü ausschalten (WCAG 2.1.4) und kollidieren nicht mit Kürzeln des Browsers oder von Bildschirmlesern. Auf Touch-Geräten gibt es keine Hinweise auf Kürzel.
  - Abnahme: Mit abgeschaltetem Schalter bewirkt „?“ nichts; bei eingeschaltetem öffnet „?“ außerhalb eines Textfeldes die Hilfe, nicht aber in einem Textfeld; auf einem Touch-Gerät erscheint keine Kürzelübersicht.

- **OBE-176 · P3 · Status: offen** — Feedback-Knopf. Ein Knopf „Fehler oder Idee melden“ in der Kopfzeile öffnet einen Dialog mit Freitext; gesendet werden nur der eingegebene Text sowie die aktuelle Seite und die Programmversion, keine weiteren Daten und keine Telemetrie. Die Meldung geht über die Kontaktfunktion an die Schule bzw. den Support und wird als Freitext verschlüsselt gespeichert und protokolliert. Nach dem Senden erscheint „Ihre Meldung wurde gesendet.“
  - Abnahme: Das Netzwerkprotokoll zeigt beim Senden genau Text, Seite und Version; ohne Absenden fließen keine Daten; die Meldung ist im Audit-Protokoll ohne Inhalt vermerkt.

- **OBE-177 · P3 · Status: offen** — Nachrichtenvorlagen. Beim Verfassen können Vorlagen eingefügt werden („Kind krank“, „Ausflug“); zuerst eigene Vorlagen je Person, Schulvorlagen optional. Vorlagen enthalten keine Namen Dritter.
  - Abnahme: Eine Person legt die Vorlage „Kind krank“ an und fügt sie beim Verfassen ein; andere Personen sehen sie nicht.

- **OBE-178 · P3 · Status: offen** — Lese-Status mit Namensliste. Absender von Briefen und Rundschreiben sehen „23 von 28 Familien“, eine Namensliste der Lesenden und Nicht-Lesenden und können Nicht-Leser erinnern (die Daten liegen in den Teilnehmerzeilen vor). Details und Datenschutz: NAC, FOR.
  - Abnahme: Ein Rundschreiben an 28 Familien zeigt den Lesestand „23 von 28“; „Erinnern“ benachrichtigt nur die 5 übrigen.

- **OBE-179 · P3 · Status: offen** — Hausaufgaben-Übersicht. Eine Liste für Eltern und Schüler/innen mit Fälligkeit, zusammengeführt aus Klassenbuch und Kursräumen (nur Zusammenführung vorhandener Daten; Hausaufgaben hängen am Kurs, OBE-083).
  - Abnahme: Ein Schüler-Konto sieht alle offenen Hausaufgaben der nächsten sieben Tage sortiert nach Fälligkeit; ein Elternkonto sieht sie je Kind.

- **OBE-180 · P3 · Status: offen** — Kalender-Abo je Rolle und Kind. Ausbau des persönlichen Kalenderlinks (Klausuren, Termine, Ferien, Hausaufgaben) je Rolle und je Kind; der Umfang je Rolle wird vor dem Einbau geprüft; das Token steht nicht im Adresspfad [unklar: Maßnahme im Altbestand nur „prüfen“]. Details: INT.
  - Abnahme: Ein Elternkonto mit zwei Kindern erhält zwei getrennte Kalenderlinks; ein Link ohne gültiges Token liefert 404.

- **OBE-181 · P3 · Status: offen** — Rechte-Vorschau „Sicht als Rolle“. Auf `/rechte` zeigt eine Vorschau Menü und Startseite so, wie eine Rolle sie mit den geänderten Rechten sähe, bevor gespeichert wird; die Vorschau führt keine Aktion aus und zeigt keine Fachdaten.
  - Abnahme: Das Entfernen von `substitution.read` bei der Rolle Lehrkraft zeigt in der Vorschau das Menü ohne „Vertretungsplan“; nach Verwerfen ist nichts gespeichert.

---

## 16. Prüfungen der Gestaltungsregeln

Betreiber (12.10.2026): „fast 1400 Checks … Das ist ein bisschen viel“. Gemeint sind Prüfungen, die ungeändert bleibende Bereiche wiederholen; die folgenden Prüfungen sind dagegen kleine, schnelle Regelprüfungen, die als Teil der Testsuite laufen. Browser-Rundgänge nur für geänderte Bereiche (QUA).

- **OBE-182 · P0 · Status: Ist** — Regelprüfungen als Teil der Testsuite. Folgende automatische Prüfungen existieren und schlagen bei einem absichtlich eingebauten Verstoß fehl:

| Nr. | Prüfung | Regel |
|---|---|---|
| 1 | kein zweites Raster | OBE-008 |
| 2 | Erklärtexte nicht über der Grenze (Ziel 0) | OBE-003 |
| 3 | keine nativen Browser-Dialoge | OBE-007 |
| 4 | Wochen nie als Buchstaben | OBE-059, OBE-129 |
| 5 | Datum und Zeit nur über die zentrale Formatierung | OBE-129 |
| 6 | Token-Kontraste in Hell und Dunkel | OBE-020 |
| 7 | keine Farbcodes oder Inline-Styles außerhalb der Tokens | OBE-017 |
| 8 | neue Vertretungsart nur mit Farbfamilie | OBE-022 |
| 9 | jede Seite erreichbar, kein Menüeintrag ohne Ziel | OBE-101 |
| 10 | jede Route hat eine Zugriffsregel | OBE-103 |
| 11 | jeder Fehlercode hat deutschen Text | OBE-041 |
| 12 | Rechte-Namen der Oberfläche gleich dem Katalog | OBE-011 |
| 13 | verbotene Begriffe, Sie-Form | OBE-131, OBE-006 |
| 14 | Produktname nur in der Konfiguration | OBE-169 |
| 15 | Betreiber-Hilfe ohne Domains, Server- und Personennamen | OBE-126 |
| 16 | keine Fremdquellen im Netzwerkverkehr | OBE-015 |
| 17 | Hilfe-Zeit- und Zustandslogik als reine Funktion getestet | OBE-118 bis OBE-119 |
| 18 | Dialog-Fokusfalle, Bestätigungs-Host, Anfrage-Client (Zeitgrenze, Fehlerabbildung, Sicherheitskopf) getestet | OBE-028, OBE-029, OBE-041, OBE-042 |
| 19 | Fehler am Feld in jedem Formular | OBE-049 |
| 20 | nur drei Layout-Grenzen im Stil | OBE-096 |
| 21 | Modul-Pfade kollidieren nicht mit Kernpfaden | OBE-079 |

  - Abnahme: Für jede Zeile wurde einmal ein Verstoß eingebaut und die Prüfung hat den Build fehlschlagen lassen (Nachweisprotokoll); die Pipeline führt alle 21 Prüfungen aus.

- **OBE-183 · P0 · Status: Ist** — Seitenabnahme für jede neue oder geänderte Seite. Prüfliste: keine erklärenden Absätze (Hilfe nur über Feldhilfe oder Seitenhilfe); nur Tokens, keine neuen Farben, keine Schatten auf Karten; 390 px ohne waagerechtes Scrollen, Tablet 820 px, Desktop 1440 px; Hell und Dunkel geprüft; Fokus sichtbar und alles per Tastatur bedienbar; Status nicht nur über Farbe; Fehlertexte am Feld; genau ein Seitentitel; Begriffe nach Glossar; Sie-Form. Neue Texte folgen vom Paketbeginn an dieser Datei.
  - Abnahme: Zu jeder Änderung an einer Seite liegt die ausgefüllte Prüfliste vor; ein Review lehnt eine Änderung ohne sie ab.

---

## 17. Offene Punkte und entschiedene Quellenkonflikte

Dieses Kapitel enthält keine eigenen Anforderungen; es sammelt Entscheidungen, die der Betreiber noch treffen muss, und Konflikte der Quellen, die hier entschieden wurden.

### 17.1 Offene Entscheidungen des Betreibers

1. **Produktname** (OBE-171): Arbeitstitel „Schulpuls“ ist im Bildungsbereich bereits in Benutzung; endgültiger Name und rechtliche Prüfung stehen aus. Frage vom 16.10.2026, 10:51, unbeantwortet.
2. **Monitor-Menü-Knopf** (OBE-166): Der „bewusst kaum sichtbare“ Knopf ist eine Entscheidung des Altbestands, vom Betreiber nicht bestätigt; er widerspricht Auffindbarkeit und Barrierefreiheit (WCAG 1.4.11, Tastatur). Festlegung bis zur Entscheidung: dezent, aber mit 3:1 Kontrast und per Tastatur erreichbar. Ob für Monitor-Konten mit festem Standort „andere Schulansichten“ nötig sind, ist offen.
3. **Grenzen für Raster-Liste und Zusatzgrenzen** (OBE-089, OBE-096): Tabellen werden unter 600 px zur Kartenliste, das Raster im Altbestand erst unter 700 px zur Liste; zusätzlich gab es 800 px (geteilte Ansicht) und 1200 px (Stundenplan-Layout). Vorschlag: nur 599,98 / 1023,98 / 1440 px.
4. **Kopfzeile: Live-Anzeige, Glocke, Hell/Dunkel-Umschalter** (OBE-100, OBE-045): Beschwerde des Betreibers vom 16.10.2026, 22:12, abgebrochen mitten im Satz („Du kannst manche Dinge anklicken, zum Beispiel das Live-Ding oder die Glocke oder … Also ob es jetzt hell oder dunkles Layout sein soll“). Der Fehler ist nicht benannt; Rückfragen am 16.10. 22:15 und 17.10. 11:32 blieben unbeantwortet.
5. **Reihenfolge der Planungs-Reiter** (OBE-108): Betreiber (12.10.2026): „der Qualitätsbericht soll auf jeden Fall als ersten Tab in die Planungsliste reinkommen“. Umgesetzt wurde „Plan prüfen“ als erster und der Qualitätsbericht als zweiter Reiter; Zusammenlegung oder Reihenfolge offen.
6. **Wochen 1 bis 52 oder 1 bis 53** (OBE-059).
7. **Reihenfolge der Startseiten-Kacheln und Startseiten-Regel je Rolle** (OBE-114): im Altbestand nicht ausgeschrieben.
8. **Menüs der Rollen Abteilungsleitung, Hausmeister, Schulbegleitung** (OBE-112): Rechte nicht beschrieben.
9. **Zugriff auf Monitor und Druck-Aushang ohne Anmeldung** (OBE-104, OBE-165): Altbestand ohne Routenregel; Neubau verlangt Monitor-Konto bzw. Berechtigung für die Daten.
10. **Test-Postausgang** (OBE-104): Ob er im Neubau überhaupt bleibt oder nur für die Entwicklung gilt, ist offen; in Produktion ist er verboten.
11. **Fehlende Werte**: Hex-Werte von primary-hover, primary-soft, Text auf Primär, Overlay, Schatten, Statusfarben, Vertretungsarten, Zustandsklassen; Kurzzeichen der Vertretungsarten; Maße des Logos; Wartezeiten der Live-Verbindung; Anzeigedauer von Erfolgsmeldungen; Einheit der Druckoption „eine Seite pro …“; Format des Seitentitels (OBE-018, 021, 022, 023, 036, 045, 095, 156, 172).
12. **Barrierefreiheitserklärung**: Text und Rückmeldeweg legt der Betreiber fest (OBE-146).
13. **Freigabe der Wettbewerbs-Kleinfunktionen und der Layout-Vorschläge**: Betreiber (16.10.2026): „die Sachen noch nicht einbauen, erst mal mir sagen“; Claude kündigte später die Umsetzung an, eine Freigabe fehlt (OBE-151, OBE-174 bis OBE-181). Die Vorschläge vom 12.10.2026 zu Filter-Knopf, Mehr-Menü, Klassenbuch-Schaltern und einklappbaren Rechte-Gruppen warten ebenfalls auf Freigabe.
14. **Design-Referenzen**: Welche Produkte als Vorbild dienen sollen (Claudes Beispiele: Linear, WebUntis-App, Notion) und welche Seite textlich am meisten stört, hat der Betreiber nicht beantwortet.
15. **Zeitpunkt von PWA und Push** (OBE-153, OBE-154): „bewusst später“ laut Altbestand.
16. **Hilfetexte und Zugangsbriefe in Sie-Form**: Die Hilfetexte sind im Altbestand nicht Seite für Seite gegengelesen; der Neubau prüft sie vollständig (OBE-006, OBE-125).
17. **Reihenfolge der Pflichtweichen** (OBE-102): im Altbestand nicht festgelegt; Neubau-Festlegung Lizenz → Passwort → Konten verbinden → Zwei-Faktor.

### 17.2 Entschiedene Quellenkonflikte

| Konflikt | Quellen | Entscheidung im Neubau |
|---|---|---|
| Anrede Du/Sie | Schülerprofil und Zugangsbriefe im Du (Plan 11.10.2026) gegen „siezen“ (Betreiber 16.10.2026) | Sie für alle (OBE-006) |
| Gefahr-Knopf für „Löschen oder Krankmeldung“ | Langfassung des Designhandbuchs gegen Kurzfassung („nur Löschen“) | nur zerstörende Aktionen (OBE-014) |
| Hilfe-Symbol | gepunktete Unterstreichung des Namens (Designhandbuch) gegen Info-Zeichen neben dem Feldnamen (Token-Übersicht, Betreiber „kleines i“) | Namenshilfe bei Feldern, Info-Zeichen bei Seiten- und Abschnittstiteln (OBE-120) |
| Radius der Felder | 6 px (Designhandbuch) gegen 8 px (Token-Übersicht) | 6 px (OBE-025) |
| Abstandsskala | bis 32 px (Designhandbuch) gegen bis 48 px (Token-Übersicht) | 4 bis 48 px (OBE-025) |
| Vertretungsarten | neun ohne „Mitbetreuung“ (Designhandbuch) gegen zehn (Token-Übersicht) | zehn (OBE-022) |
| Doppelte Seite `/datenschutz` | Verwaltung mit `privacy.manage` gegen Hinweise ohne Recht | `/datenschutz` für alle, Verwaltung unter `/datenschutz/verwaltung` (OBE-105, OBE-109) |
| `/mitteilungen` | eigene Seite im Routenverzeichnis gegen Ordner im Postfach | Weiterleitung auf Nachrichten (OBE-110) |
| Postfach und Chats | getrennte Einträge gegen ein Eintrag (Betreiber 12.10.2026, 20:48) | ein Eintrag „Nachrichten“ (OBE-107) |
| Chat-Archiv und Entwürfe | Archiv und Entwürfe „weglassen“ gegen „Archiv rein, Entwurf raus“ (Betreiber 12.10.2026) | Archiv ja, Entwürfe in Chats nein (OBE-033, OBE-107) |
| Hilfetext „reiner Text“ gegen „mehr dazu“-Verweis | Designhandbuch gegen Backlog | Link nur in der Seitenhilfe (OBE-123) |
| Menüeintrag bei fehlendem Seitenrecht | im Altbestand unklar | Eintrag verschwindet (OBE-098) |
| Dunkles Schema | doppelt definiert gegen einmal | einmal (OBE-019) |
| Dunkelmodus-Zeitplan | Wunsch gegen gestrichen (16.10.2026) | entfällt |
| Fernseher-Ansicht | eigene Ansicht gegen Monitor | entfällt, Monitor (Kapitel 13) |
| Kind-Auswahl gerätweit | Altbestand gegen je Konto | je Konto (OBE-016) |
| Touch-Fläche der Hilfe | 37 px (Ist) gegen 44 px (Regel) | 44 px (OBE-120) |
| „Block geteilt“ | Hinweistext des Altbestands gegen Verbotsbegriff „Block“ | „Doppelstunde geteilt“ (OBE-131) |
| Monitor „ohne Anmeldung“ | Routenverzeichnis gegen Monitor-Rolle mit Konto | Seite ladbar, Daten nur mit Konto (OBE-165) |
| Logo „blaue Kachel“ gegen „ohne Kachel in der Textfarbe“ | Betreiberauftrag gegen Token-Übersicht | farbig mit Kachel für Anmeldung, Browser-Symbol, PDFs; einfarbig ohne Kachel in der Kopfzeile (OBE-172) |
| Bestätigungsknöpfe | „Ja/Nein“ im Altbestand gegen Verb mit klarem Ziel | Verb (OBE-029, OBE-130) |

### 17.3 Hinweis zum Vorgehen beim Design

Der Betreiber lehnte am 13.10.2026 ein von Claude gebautes Stil-Mockup („Schulmanager Rehaul“) ab: „Jo das ist komplett grauenhaft“. Gründe laut Claude (vom Betreiber nicht widersprochen): beliebig, nur eine Skizze mit Stundenplan und zwei Beispielen, die Hälfte der Funktionen fehlte. Ein reiner Stylesheet-Umbau durch kostenlose Sprachmodelle änderte kaum etwas (Schrift, neutralere Grautöne, minimal rundere Ecken). Folgerung für den Neubau: keine Spielzeug-Mockups; Gestaltung entsteht an den echten Seiten mit den Bausteinen dieser Datei, Struktur- und Textänderungen gehören dazu. Arbeitsregeln dazu: PRI.

---

## 18. Nicht im Umfang der Oberfläche

- Native Apps in den App-Stores (stattdessen installierbare Web-App, OBE-153).
- Mehrsprachige Oberfläche einschließlich Rechts-nach-links-Sprachen; die Oberfläche ist nur auf Deutsch. Die Übersetzung von Elternbriefen per Klick ist ein eigenes, abschaltbares Modul (FOR); Texte in einfacher Sprache gelten für das Handbuch (OBE-128).
- Videokonferenz in der App (nur Link-Anbindung), gemeinsames Bearbeiten von Dokumenten und Office im Browser, H5P und Lernpfade, Klassengeld und Online-Bezahlung, Mensa-Bestellung, Schulwebsite.
- Eigene Vertretungs-Ansicht für Fernseher und Zeitplan für den Dunkelmodus (gestrichen 16.10.2026).
- Eltern-Feed mit Fotos und Punkten (hohes Datenschutzrisiko; nur nach Einwilligungsklärung, derzeit nicht vorgesehen).
- Klassendienste, Geburtstagsliste, QR-Anmeldung für Kinder und Abwesenheitsnotiz als eigene Funktionen: nur auf Nachfrage des Betreibers (16.10.2026), nicht Teil dieses Pakets.
- GIF-Suche über Dritte (Datenschutz, OBE-015) und jede Nachladung von Fremdinhalten.
- Browser-Dialoge, Schieberegler, Emojis als Icons, Erklärabsätze auf Seiten.

<!--ENDE-->
