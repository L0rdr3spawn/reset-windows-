# 06 Recht und Datenschutz (Einsatz in deutschen Schulen)

Kürzel dieser Datei: **REH** (Recht, Compliance, Verträge, Rechtstexte, Barrierefreiheit) und **DSG** (Datenschutz-Prozesse: Betroffenenrechte, Löschung, Auskunft, Datenpanne; bewusst nicht „DAT“, das gehört zu Datei 05). Stand der Quellenlesung: 18.10.2026.

**Geltung und Haftungsausschluss.** Diese Datei ist eine fachliche Spezifikation für den Neubau. Sie ist **keine Rechtsberatung**. Jede Rechtsnorm, jede Frist, jeder Mustertext und jede Vertragsklausel in dieser Datei ist vor dem Echteinsatz durch eine Anwältin bzw. einen Anwalt mit Schulrecht oder durch die bzw. den Datenschutzbeauftragten zu prüfen. Die Rechtsrecherchen, auf die sich die Datei stützt (Klagen- und Haftungsrecherche vom 17.10.2026), stammen aus Sekundärquellen und sind nicht rechtlich geprüft; Aktenzeichen, Beträge und Daten sind vor jeder Verwendung gegen das Primärdokument zu prüfen.

## 0. Legende

| Zeichen | Bedeutung |
|---|---|
| `[JP]` | **Juristisch zu prüfen** (kein Rechtsrat). Alle so markierten Aussagen, Werte und Texte gelten bis zur Prüfung nur als Entwurf. |
| `[unsicher]` | Aussage ist nicht gesichert (Sekundärquelle, Quellen widersprechen sich, oder Eigenwissen des Schreibers). |
| `[unklar: …]` | Wert oder Regel ist aus den Quellen nicht ableitbar; nichts erfunden. |
| `[Entscheidung Neubau]` | Quellen widersprechen sich oder schweigen; hier wurde für den Neubau festgelegt. Spätere Betreiberentscheidungen überstimmen frühere. |
| `[Eigenwissen]` | Rechtsaussage des Schreibers, die nicht aus den Quellen stammt. Immer zusätzlich `[JP]`. |
| `[…]` in Mustertexten | Platzhalter, den die **Schule** ausfüllt. Offene eckige Klammern lösen die Warnung nach REH-044 aus. |
| `{{…}}` in Mustertexten | Wert, den das **System** aus der Konfiguration einsetzt (kein Platzhalter der Schule, keine Warnung). |
| Status: Ist | Im heutigen System vorhanden; im Neubau mindestens gleichwertig herzustellen. |
| Status: offen | Gefordert oder gewünscht, aber nicht gebaut, oder im Neubau gegenüber dem Ist zu ändern (der Teil, der schon Ist ist, steht im Text). |
| P0 / P1 / P2 / P3 | P0 Pflicht, Recht, Sicherheit; P1 Kernfunktion zur Erfüllung der Pflicht; P2 wichtig; P3 Wunsch. Recht und Sicherheit sind immer P0; P1 bis P3 tragen hier nur Hilfsfunktionen und Wünsche. |

**Nummerierung.** REH-001 ff. und DSG-001 ff. (Betroffenenrechte, Fristen und Datenschutzprozesse; bewusst nicht „DAT“, das gehört zu Datei 05) laufen in dieser Datei fortlaufend in der Reihenfolge des Dokuments. Querverweise auf andere Dateien des Pakets nennen nur deren Kürzel (z. B. ANM, SIC, REC, KLB, NOT, NAC, STA, BET, OBE).

**Quellenvorrang.** Das Löschkonzept (Oktober 2026) gilt vor den Überblickstabellen im Sicherheitskonzept und vor den Platzhalterfristen in Verzeichnis und Hinweistexten. Das Haftungsaudit vom 17.10.2026 gilt vor der Sicherheitsprüfung vom 13.10.2026. Spätere Betreiberentscheidungen überstimmen frühere. Der Betreiber ist der Auftraggeber der Software (Anbieter); die Schule ist die Kundin.

**Wortlaut des Betreibers (bleibt erhalten).**
- „dass … alles bitte auch den Sicherheitsstandards entspricht und den Datenschutzrichtlinien, die du noch festlegen musst entspricht“ (11.10.2026; Datenschutzrichtlinien selbst waren offen und werden hier festgelegt).
- „das Impressum sollte ja vielleicht nicht an mich gehen, sondern dann über die Schule gehen“ (17.10.2026).
- „da ist jetzt die Firma von mir drin … sondern das sind dann Informationen, die sollten dann die Schulen anpassen“ (17.10.2026).
- „mach mir eine betatester account der admin zugang hat aber alle actionen extrem stark geloget werden“ (16.10.2026); „das soll alles gelockt werden, falls er Mist baut“ (17.10.2026).
- „Die Dokumente sollen bitte alle gespeichert werden, wirklich alle.“ (12.10.2026; durch die Löschfristen vom 16.10.2026 überholt, siehe Abschnitt 17).

---

## 1. Verantwortlichkeit, Rollen, Mandantentrennung

| Rolle | Wer | Aufgabe in Bezug auf die Software |
|---|---|---|
| Verantwortliche Stelle (Art. 4 Nr. 7 DSGVO) | die Schule, vertreten durch die Schulleitung; je Landesrecht auch Schulträger oder Land `[JP]` | Zwecke und Mittel festlegen, Rechte vergeben, Verzeichnis führen (Art. 30), Betroffene informieren (Art. 13/14), Rollen- und Löschkonzept, Pannen melden (Art. 33/34), DSFA (Art. 35), Verträge nach Art. 28 schließen |
| Auftragsverarbeiter (Art. 28) | Hoster; IT-Dienstleister des Schulträgers; E-Mail-Dienst; SMS-Dienst; Offsite-Backup-Speicher; Anmeldedienst; **Softwareanbieter nur bei gehostetem Betrieb, Fernwartung oder Support mit Datenzugriff** | Verarbeitung nur auf Weisung, TOMs, Unterauftragnehmer nur mit Zustimmung, Pannenmeldung an die Schule |
| Datenschutzbeauftragte/r (Art. 37–39) | benannt von der Schule bzw. dem Land | Beratung, DSFA-Prüfung, Schulung, Ansprechpartner für Betroffene und Aufsicht |
| IT-Betreuung | Administration der Schule oder des Schulträgers | Konten, Updates, Backups, Monitoring, Vorfallsbearbeitung |
| Aufsichtsbehörde | Landesdatenschutzbehörde des Bundeslandes der Schule | Meldeempfängerin (Art. 33), Beschwerdestelle |
| Schulaufsicht / Schulträger | nach Landesrecht | Informationsempfänger bei Vorfällen nach Landesvorgabe |

**REH-001 · Rollenverteilung Schule und Anbieter** — P0 · Status: Ist · `[JP]`
- Die Schule ist Verantwortliche. Der Softwareanbieter erhält ohne weitere Vereinbarung **keinen** Zugriff auf personenbezogene Daten; ein AV-Vertrag mit ihm ist nur nötig, wenn er im Auftrag der Schule Daten verarbeitet oder darauf zugreifen kann (gehosteter Betrieb, Fernwartung, Support mit Datenzugriff). Schulträger: Auftragsverarbeiter oder gemeinsam Verantwortlicher (Art. 26) je Land `[JP]`.
- Alle Mustertexte, Hilfetexte und Verträge bezeichnen die Schule als „Verantwortliche“ und den Anbieter nur als „Auftragsverarbeiter (siehe AV-Vertrag)“.
Abnahme: Suchlauf über alle ausgelieferten Mustertexte und Hilfetexte nach der Bezeichnung des Anbieters (Firmenname, Domain, Kontaktdaten) → 0 Treffer; jeder Text, der den Anbieter erwähnt, enthält ausschließlich die Formulierung „Auftragsverarbeiter (siehe AV-Vertrag)“; ein Test schlägt fehl, sobald ein Anbieterbezeichner in einem Mustertext steht.

**REH-002 · Stammdaten der verantwortlichen Stelle** — P0 · Status: offen · `[JP]`
- Ein Einrichtungsschritt „Verantwortliche Stelle“ erfasst einmal: Name der Schule, Anschrift, Vertretung (Schulleitung), Schulträger, Kontakt (Telefon, E-Mail), Datenschutzbeauftragte/r (Name, Kontakt, Vertretung), Aufsichtsbehörde (Name, Anschrift, Meldeweg/Formular-Link), Schulaufsicht, Hoster/IT-Dienstleister (Name, Vertragsnummer, Support), Kontaktliste für Vorfälle (je Person Vertretung). Alle Mustertexte, das Verzeichnis (REH-034), die Meldevorlage (REH-040) und die Hinweistexte (REH-047) ziehen diese Werte als `{{…}}`.
- Der Schritt gilt erst als erledigt, wenn alle Pflichtfelder gefüllt sind; Datenschutzbeauftragte/r ist Pflicht für öffentliche Schulen (Art. 37 Abs. 1 lit. a `[Eigenwissen]` `[JP]`).
Abnahme: Leere Pflichtfelder → Schritt „nicht erledigt“, Warnpunkt auf der Betriebsseite; Wert in einem Feld ändern → alle Mustertexte zeigen den neuen Wert ohne weiteren Eingriff; Berechtigung nur mit `settings.edit`, ohne Recht 403; jede Änderung im Audit (`setup.legal`, ohne Inhalte).

**REH-003 · Mandantentrennung (Trennungsgebot)** — P0 · Status: Ist
- Jede Schule hat eine eigene Instanz: eigene Datenbank, eigene Dateiablage, eigenen zufälligen Geheimschlüssel (`SM_SECRET_KEY`), eigene Verschlüsselungsschlüssel (`SM_ENCRYPTION_KEYS`), eigene Domain. Keine gemeinsamen Daten, Schlüssel oder Datenverzeichnisse zwischen Instanzen. API-Schlüssel sind nur mit dem Geheimschlüssel der jeweiligen Schule gültig.
- Der Betreiber will die Datentrennung selbst testen können („Kannst du das bitte sicherstellen …, dass ich das testen kann“).
Abnahme: Zwei Instanzen A und B; ein API-Zugangsschlüssel von A gegen B → 401, ein Sitzungs-Cookie von A gegen B → nicht angemeldet; Start von B mit dem Datenverzeichnis oder dem Geheimschlüssel von A ist durch die Betriebsprüfung ausgeschlossen bzw. wird im Preflight als Fehler gemeldet; Test „Zugang einer fremden Schule ist wirkungslos“ ist Teil der Testsuite.

**REH-004 · Zugriff des Anbieters, Fernwartung, Support** — P0 · Status: offen · `[JP]`
- Anbieterzugriff auf eine Schul-Instanz nur über einen **Support-Zugang**, den die Schule freigibt: personengebunden, befristet (Standard höchstens 24 Stunden `[Entscheidung Neubau]`), widerrufbar, jede Handlung im Audit. Auch ein Support-Zugang sieht nie Atteste, Förder-, Krankmeldungs-, Noten- oder Chat-Inhalte (feste Mindestregeln der technischen Administration, siehe REC).
- Lizenz- und Update-Verkehr (REH-030) ist kein Datenzugriff und braucht keinen Support-Zugang.
Abnahme: Support-Zugang ohne Freigabe der Schule → nicht erzeugbar; Zugang nach Ablauf → 401; Support-Konto ruft Attest, Förderdaten, Noten → 404; Audit enthält Erzeugung, Nutzung und Ablauf des Zugangs mit Konto-ID und Zeit, ohne Inhalte.

**REH-005 · Rechtsrahmen-Profil (Bundesland, Trägerart)** — P0 · Status: offen · `[JP]`
- Das Recht ist je Bundesland verschieden (Schulgesetz, Schuldatenverordnung, Aktenordnung, Landesdatenschutzgesetz, Einwilligungsalter, Meldeformular). Daher ein **Rechtsrahmen-Profil** als **Daten**, nicht als Code (wie die Ferienvorlagen je Bundesland). Felder: `bundesland` (alle 16), `traegerart` (`oeffentlich`, `ersatzschule`, `kirchlich`), `verantwortliche_stelle_typ` (Schule, Schulträger, Land), `schulgesetz_verweis`, `schuldatenverordnung_verweis`, `fristenprofil` (Schlüssel, siehe DSG-019), `einwilligungsalter` (Jahre), `aufsichtsbehoerde` (Name, Anschrift, Meldeweg), `personalvertretung_beteiligung` (ja/nein/unklar). Jeder Wert trägt `quelle`, `stand` (Datum) und `juristisch_geprueft` (nein/ja, durch wen, am).
- Ausgeliefert werden alle 16 Länder als Hüllen; befüllt ist nur, was aus den Quellen belegt ist (Fristenprofil NRW, siehe DSG-019). Alles andere bleibt leer und wird von der Schule eingetragen. Keine Aufsichtsbehörden-Adressen vorbelegen.
- Trägerart ≠ `oeffentlich`: sichtbarer Hinweis „Rechtsgrundlagen und Aufsicht weichen ab (z. B. Vertrag, berechtigtes Interesse, kirchliches Datenschutzrecht); die Mustertexte sind für öffentliche Schulen vorbereitet“ `[JP]` `[unsicher]`.
Abnahme: Profil „Nordrhein-Westfalen“ wählen → Fristen- und Altersvorschläge erscheinen mit Quelle, Stand und Kennzeichen „nicht rechtlich geprüft“; Profil „Baden-Württemberg“ ohne Eintrag → Felder leer, kein erfundener Wert; Trägerart `kirchlich` → Hinweisbanner sichtbar; Änderung nur mit `privacy.manage`, sonst 403; Änderung im Audit.

**REH-006 · Kennzeichnung „nicht rechtlich geprüft“** — P0 · Status: Ist
- Alle Rechtstexte, Vorlagen, Fristenprofile und Verträge tragen bis zur Prüfung die Kennzeichnung „Entwurf – keine Rechtsberatung – juristische Prüfung durch Schule/Datenschutzbeauftragte nötig“. Die Schule bestätigt die Prüfung je Dokument (Name, Datum); erst dann entfällt die Kennzeichnung.
Abnahme: Neu eingefügter Mustertext enthält die Hinweiszeile als erste Zeile (selbst ein offener Platzhalter); Hinweiszeile nicht gelöscht → Warnung; Bestätigung „geprüft durch [Name] am [Datum]“ ohne Namen → nicht speicherbar (422).

**REH-007 · Pflicht-Rechtsprüfung vor dem ersten Einsatz (Anbieterseite)** — P0 · Status: offen · `[JP]`
- Vor dem ersten Kunden lässt der Anbieter prüfen und dokumentiert Datum und Prüfer: Muster-AV-Vertrag mit Unterauftragnehmerliste (REH-024), Mustertexte und Hinweise (REH-044, REH-047), Fristenprofil NRW (DSG-019), Erklärung zur Barrierefreiheit (REH-066), Nutzungsordnung (REH-049), Lizenzvertrag/EULA (REH-079), Produktname und Marke (REH-078), DSFA-Hilfe (REH-038).
Abnahme: Release-Checkliste „Recht“ (REH-082) enthält je Dokument die Zeile „geprüft am / durch“; ein Release mit leerer Zeile wird als „nicht freigegeben für Kunden“ markiert (nur Demo erlaubt).

**REH-008 · Verpflichtung auf Vertraulichkeit (Personal und Externe)** — P1 · Status: offen · `[JP]` `[Eigenwissen]`
- Beim ersten Anmelden eines Personal-, Schulbegleitungs-, Hausmeister- oder Ausbilder-Kontos erscheint der App-Dialog „Pflichten im Alltag“ (Passwort nicht weitergeben, Zwei-Faktor einrichten, an gemeinsam genutzten Geräten abmelden, Abwesenheitsgründe knapp halten, Gesundheitsdaten nur im Bereich Atteste und Dokumente weitergeben, Exporte nur auf dienstlichen Geräten und nach Gebrauch löschen, Datenpannen sofort melden). Bestätigung mit Datum wird gespeichert (Audit, ohne Inhalt). Grundlage: Art. 29, 32 Abs. 4 DSGVO.
Abnahme: Erstanmeldung eines neuen Lehrerkontos → Dialog erscheint vor jeder anderen Seite; ohne Bestätigung keine weitere Nutzung; zweite Anmeldung → kein Dialog; Textänderung durch die Schule erhöht die Textversion → Dialog erscheint erneut.

---

## 2. Rechtsgrundlagen, Einwilligung, Minderjährige, besondere Kategorien

**REH-009 · Rechtsgrundlagen-Register** — P0 · Status: offen · `[JP]`
- Jede Verarbeitungstätigkeit (Zeilen in REH-035) hat ein Feld `rechtsgrundlage` mit Standardtext und Platzhaltern. Die Schule trägt die Normen ihres Landes ein. Das Register speist Verzeichnis, Datenschutzerklärung und Hinweistexte. Standardtexte (Platzhalter in `[…]`):

| Verarbeitung | Rechtsgrundlage (Standardtext) |
|---|---|
| Stunden-, Vertretungs-, Raum-, Aufsichts-, Klausurplanung (Schüler/innen) | Art. 6 Abs. 1 lit. e DSGVO i. V. m. [Schulgesetz §…] |
| dieselben für Lehrkräfte und weiteres Personal | Art. 6 Abs. 1 lit. e DSGVO i. V. m. [Landesdatenschutzgesetz / Beschäftigtendatenschutz §…] (§ 26 BDSG nur, wo anwendbar `[Eigenwissen]`) |
| Konten, Anmeldung, Sicherheit | Art. 6 Abs. 1 lit. e DSGVO [i. V. m. Landesrecht]; Art. 32 DSGVO |
| Krankmeldungen, Fehlzeiten, Entschuldigungsverfahren | Art. 6 Abs. 1 lit. e i. V. m. [Schulpflicht-/Schulgesetz §…]; Gesundheitsdaten Art. 9 Abs. 2 lit. [g] i. V. m. [Landesrecht] |
| Atteste, Förder- und Nachteilsausgleichsdaten | Art. 9 Abs. 2 lit. [g] i. V. m. [Landesrecht]; wo freiwillig: lit. [a] (ausdrückliche Einwilligung) `[JP]` |
| Klassenbuch, Notenbuch, Kompetenzen | Art. 6 Abs. 1 lit. e i. V. m. [Schulgesetz / Leistungsbewertungsvorschriften §…]; Aufbewahrung Art. 6 Abs. 1 lit. c i. V. m. [Aktenordnung / Schuldatenverordnung §…] |
| Nachrichten, Mitteilungen, Kursräume, Aufgaben | Art. 6 Abs. 1 lit. e DSGVO i. V. m. [Schulgesetz §…] |
| Chats (Ende-zu-Ende) | Art. 6 Abs. 1 lit. e `[JP]`; Zulässigkeit schulischer Chats nach Landesrecht `[JP]` |
| Freiwillige Zusatzfunktionen (E-Mail an private Adresse, SMS, iCal-Abo auf privaten Geräten, Fotos) | Art. 6 Abs. 1 lit. a DSGVO (Einwilligung), jederzeit widerrufbar |
| Technische Protokolle (Audit, Zugriffsprotokoll, Anmeldeversuche) | Art. 6 Abs. 1 lit. e DSGVO; Art. 32 DSGVO; lit. f steht öffentlichen Stellen in Erfüllung ihrer Aufgaben nicht zur Verfügung `[Eigenwissen]` `[JP]` |
| Verstärkte Protokollierung beobachteter Konten | `[unklar: Rechtsgrundlage und Zweck in den Quellen nicht geklärt]`, siehe REH-020 |
| Lizenzprüfung und Update-Verkehr (Anbieter) | Vertragserfüllung des Anbieters mit der Schule; Anbieter ist für diese Vertragsdaten eigener Verantwortlicher `[JP]`; übermittelt keine Personendaten (REH-030) |

Abnahme: Verzeichnis-Export (REH-034) enthält je Teilverfahren die Rechtsgrundlage; ein Teilverfahren ohne Eintrag → Warnung „Rechtsgrundlage offen“ und Einrichtungsschritt „Datenschutz“ nicht erledigt; Standardtexte enthalten ausschließlich Platzhalter in eckigen Klammern, nie eine erfundene Paragrafennummer.

**REH-010 · Konten legt die Schule an (keine Selbstregistrierung)** — P0 · Status: Ist
- Konten für Schüler/innen, Eltern, Lehrkräfte und Personal legt ausschließlich die Schule an (Schulrecht, keine Einwilligung des Kindes). Es gibt keine öffentliche Registrierung. Eltern- und Schulbegleitungs-Verknüpfungen mit Kindern legt die Schule an (Sekretariat/Schulleitung) oder löst per Einladungs-/Zugangsbrief aus; keine Selbstzuordnung über Kennungen oder Zahlenfolgen.
Abnahme: Aufruf einer Registrierungsroute ohne Anmeldung → 404; Elternkonto versucht, sich per Eingabe einer Schüler-ID zu verknüpfen → 404/422 ohne Information, ob die ID existiert; Verknüpfung nur durch Konto mit `users.manage` (Sekretariat: nur Schüler-, Eltern-, Begleitungskonten) → Audit-Eintrag.

**REH-011 · Einwilligung nur, wo sie nötig ist** — P0 · Status: Ist (Teil offen: Chat-Auszüge) · `[JP]`
- Einwilligung (Art. 6 Abs. 1 lit. a / Art. 9 Abs. 2 lit. a) nur für **freiwillige** Funktionen: (a) E-Mail-Benachrichtigungen an private Adressen und SMS; (b) iCal-Abo auf privaten Geräten (Lehrkräfte); (c) Fotos und Videos von Personen (REH-075); (d) Weitergabe gemeldeter Chat-Auszüge an Prüfende (`chats.review`) nur mit Einwilligung von Kind bzw. Eltern; (e) Freigaben volljähriger Schüler/innen an ihre Eltern je Bereich (REH-014); (f) freiwillige Kontaktangaben (E-Mail, Telefon).
- **Keine** Einwilligung als Rechtsgrundlage für Konten, Stundenplan, Vertretung, Krankmeldung, Klassenbuch, Noten, Kursräume (Schulrecht, REH-009). Eine Einwilligung darf nie zur Bedingung für den Zugang zur Pflichtfunktion gemacht werden (Freiwilligkeit).
Abnahme: Neues Konto ohne Opt-in → keine Mail an eine private Adresse, kein SMS-Versand, kein ausgegebener iCal-Link; Opt-in im Profil → Versand beginnt; Widerruf im Profil → Versand endet sofort, Eintrag im Audit; Pflichtfunktionen (Stundenplan, Krankmeldung) bleiben ohne Opt-in nutzbar.

**REH-012 · Einwilligungsverwaltung (Art. 7)** — P0 · Status: offen · `[JP]`
- Einwilligungen werden aus Vorlagen erteilt, **versioniert** (Textversion, Zweck, Datum, erteilende Person, betroffene Person, Weg), **jederzeit widerrufbar** (Widerruf ebenso einfach wie Erteilung, Wirkung für die Zukunft), mit Nachweis (Art. 7 Abs. 1). Übersicht je Klasse und Zweck („Wer darf fotografiert werden?“). Ab dem **Einwilligungsalter** (REH-013) willigen Schüler/innen selbst ein, darunter die Eltern. Abstufung: Teilschritte (a) Brief und Lesebestätigung, (b) Rückmeldung, (c) Einwilligungen (Quelle: Backlog B-47, dort P0, XL).
Abnahme: Einwilligung „Fotos Klasse 5a“ Version 1 erteilt → Übersicht zeigt „erteilt am …, Version 1“; Textänderung → Version 2, bestehende Einwilligungen bleiben an Version 1 gebunden und erscheinen als „neu einzuholen“; Widerruf → Status „widerrufen am …“, betroffene Funktion sofort gesperrt; Zugriff auf die Übersicht nur mit Recht `forms.inbox` bzw. Klassenleitung der eigenen Klasse, fremde Klasse → 404.

**REH-013 · Minderjährige: Volljährigkeit und Einwilligungsalter** — P0 · Status: Ist (Einwilligungsalter offen) · `[JP]`
- **Volljährigkeit** gilt ab 18 Jahren nach Geburtsdatum, Stichtag Zeitzone Europe/Berlin; nur ohne Geburtsdatum zählt das Konto-Flag „volljährig“. Die Rechte wechseln am Geburtstag bei jeder Anfrage automatisch (Details KLB, SCH, REC). Der Betreiber hat die Altersgrenze 18 noch **ausdrücklich zu bestätigen** `[unklar: Bestätigung steht aus]`.
- **Einwilligungsalter** für selbstständige Einwilligungen: Schulvorgabe `einwilligungsalter` (Jahre). Art. 8 DSGVO (16 Jahre) betrifft nur Dienste der Informationsgesellschaft mit Einwilligung; für die Schulverwaltung gibt es keine klare Grenze; Baden-Württemberg setzt Einsichtsfähigkeit in der Regel ab 16 an `[unsicher]` `[JP]`. Standardwert `[unklar: nicht festgelegt; Vorschlag 16, bis zur Prüfung nur als Vorschlag]` `[Entscheidung Neubau: Feld muss in der Einrichtung gesetzt werden; ohne Wert gilt „Eltern willigen ein“ für alle Minderjährigen]`.
- Informationen an Kinder in klarer, einfacher Sprache (Art. 12 Abs. 1, ErwG 38); in der App durchgehend „Sie“ (REH-047).
Abnahme: Schüler mit Geburtsdatum, der heute 18 wird → bei der ersten Anfrage nach 00:00 Uhr Europe/Berlin hat das Elternkonto keinen Zugriff auf Bereiche ohne Freigabe (Test mit fester Uhr); Konto-Flag „volljährig“ wird bei vorhandenem Geburtsdatum ignoriert; `einwilligungsalter` leer → Einwilligungsfunktionen für Schüler/innen sind gesperrt, Eltern willigen ein.

**REH-014 · Elternzugriff und Volljährige: alle Ausgabewege** — P0 · Status: Ist (Lücken aus dem Audit 17.10. offen)
- Minderjährige: Eltern sehen, was das Kind sieht (Förderdaten nur bei Minderjährigen). Volljährige: Standard **keine** Einsicht der Eltern (`adult_parent_access_default`), bis die Person je Bereich freigibt (Kursräume, Stundenplan, Krankmeldungen/Fehlzeiten, Dokumente/Atteste, Mitteilungen, Noten); Standard der Zustellung von Schulinformationen ab 18: nur an die Person (`self`), wählbar `parents`/`both`. Jede Änderung im Audit, jederzeit widerrufbar.
- **Dieselbe Regel gilt für jeden Ausgabeweg:** Einzelansicht, Liste, Export, Auskunft, iCal-Feed, Benachrichtigung, API, Live-Strom. Elternzugriff endet mit der Volljährigkeit automatisch, auch für iCal-Feed und eigene Dokumente (offene Funde P1-05, P1-12 im Audit).
Abnahme: Elternkonto eines volljährigen Kindes ohne Freigabe ruft Plan-Feed, Dokumente, Krankmeldungen, Export und Benachrichtigungen ab → jeweils 404 bzw. leere Liste; mit Freigabe „Krankmeldungen“ → nur dieser Bereich liefert Daten; Widerruf → sofort wieder 404; Test je Ausgabeweg und je Bereich (Rechte-Matrix-Test).

**REH-015 · Gesundheitsdaten (Art. 9): Schutzpaket** — P0 · Status: Ist · `[JP]`
- Besondere Kategorien: Gesundheitsdaten (Gründe und Vermerke von Krankmeldungen, Atteste und Dokumente, Förder- und Nachteilsausgleichsdaten), mittelbar Religion (Kurswahl Religion/Ethik), alle Daten Minderjähriger sind besonders schutzbedürftig. Schutzpaket: eigene Zugriffsregeln (Gründe nur meldende Person, Familie, Klassenleitung, Sekretariat, Schulleitung; Fachlehrkräfte sehen „vertraulich“; Atteste nie für Fachlehrkräfte und technische Administration), Verschlüsselung im Ruhezustand (Datei, Dateiname, Titel, Vermerk), Zugriffsprotokoll ohne Inhalte, kürzeste Löschfristen (DSG-018), Freitexte knapp (keine Diagnosen), Rechtsgrundlage Art. 9 Abs. 2 lit. [g] i. V. m. [Landesrecht] (REH-009).
- Diagnosetexte sind nicht vorgesehen: Hinweis ohne Diagnose; Nachteilsausgleich nur Art und Minuten.
Abnahme: Technische Administration, Fachlehrkraft, Lehrkraft einer fremden Klasse rufen ein Attest → 404; Klassenleitung der eigenen Klasse → 200; Datenbank-Dump enthält Gründe, Vermerke, Titel, Dateinamen nur als Chiffrat; Abruf fremder Atteste erzeugt Audit `file.download` (je Konto, Datei, Tag einmal); Fachlehrkraft sieht statt des Grundes den Text „vertraulich“.

**REH-016 · Keine Gesundheitsdaten, Noten oder Namen in Nachrichten nach außen** — P0 · Status: Ist
- Benachrichtigungstexte, Mails, SMS, (künftige) Push-Nachrichten, Betreffzeilen, Fehlermeldungen, URLs, Logs und Server-Antworten enthalten **keine** Krankheitsgründe, keine Noten, keine Diagnosen und keine Namen anderer Kinder. Schulvorgabe „Neutralmodus“ für Mails: nur Hinweis und Link, kein Name im Text (W2-13, offen). Alle automatischen Mails tragen `Auto-Submitted: auto-generated`; Pflicht-Mails (Passwort zurücksetzen, Sicherheit, Zugangsbriefe) haben weder Abmeldelink noch List-Unsubscribe-Kopf.
Abnahme: Krankmeldung mit Grund „Fieber“ erfasst → Benachrichtigung an die Klassenleitung enthält das Wort nicht; Test über alle Benachrichtigungsarten sucht nach Feldern `reason`, `note`, `grade`; Neutralmodus an → Mail-Text enthält weder Vor- noch Nachnamen noch Fachbezeichnung, nur Hinweis und Link; Mail-Kopf `Auto-Submitted` vorhanden.

**REH-017 · Datenkategorien-Katalog und Datensparsamkeit** — P0 · Status: offen (Teil Ist) · `[JP]`
- Ein **Datenkategorien-Katalog** beschreibt vollständig, was gespeichert wird; er ist Quelle für Verzeichnis, Datenschutzerklärung und Hinweistexte (REH-046). Gegenüber den Altdokumenten **korrigiert**: Geburtsdaten werden gespeichert (Stammdaten, Volljährigkeit), nur mit Recht „Geburtsdatum pflegen“ (`students.birth_date`) bzw. für die Person selbst sichtbar; Kategorien Kontakt, Postfach, Kursräume, SSO-Verknüpfung, Elternfreigaben, Briefe, Chats, Beobachtungsprotokoll sind aufzunehmen.
- Kategorien (Mindestumfang): Schüler/innen (Name, Klasse, Kurse/Kursteile, Geburtsdatum, Konto, Fehlzeiten, Krankmeldungen, Atteste, Förderdaten, Abgaben, Noten, Kompetenzen, Nachrichten), Eltern (Name, Konto, Zuordnung, optional E-Mail/Telefon, eigene Meldungen), Lehrkräfte/Personal (Name, Kürzel, Fächer, Deputat, Standort, E-Mail, Sperrzeiten und Wünsche nur für Planung und Schulleitung, Abwesenheiten mit knappem Grund, eigene Einträge), Technik (Sitzungen, Anmeldeversuche, Audit, Zugriffsprotokoll, API-Protokoll, Fehlerprotokoll).
- Ein Feldregelwerk gilt für **alle** Ausgaben (Einzelansicht, Liste, Export, Feed, API): ein Feld ist entweder überall sichtbar oder nirgends (Fund S-08/P1-04: Geburtsdatum war in der Sammel-API sichtbar, in der Klassenseite ausgeblendet).
Abnahme: Katalog enthält die Kategorie „Geburtsdatum“; Test vergleicht den Katalog mit den tatsächlich gespeicherten Feldern (Schema) und schlägt fehl bei einem gespeicherten personenbezogenen Feld ohne Katalogeintrag; Konto ohne `students.birth_date` ruft Schülerliste (Einzel, Sammel, Export) → Geburtsdatum in keinem Weg enthalten.

**REH-018 · Beschäftigtendaten (Lehrkräfte), Personalrat** — P0 · Status: Ist (Mitbestimmung offen) · `[JP]`
- Wünsche, Sperrzeiten, Deputat und Abwesenheitsgründe von Lehrkräften sind Beschäftigtendaten: nur Planung und Schulleitung. Abwesenheitsgründe minimal („krank“, „Fortbildung“), nie Diagnosen; sichtbar nur mit `substitution.edit`, nie für Schüler/innen, Eltern, Monitor, Exporte (Ausnahme: Untis-Export auf ausdrücklichen Wunsch), iCal.
- **Es findet keine Leistungs- oder Verhaltenskontrolle von Lehrkräften durch die Software statt.** Das Audit-Protokoll dient Sicherheit und Nachvollziehbarkeit; seine Nutzung für andere Zwecke bedarf einer Regelung mit dem Personalrat. Die Einführung einer Software, die Verhalten oder Leistung auswerten kann, ist nach Landespersonalvertretungsrecht beteiligungspflichtig `[Eigenwissen]` `[JP]`. Nationale Beschäftigtendatenschutzregeln müssen den Anforderungen von Art. 88 DSGVO genügen (EuGH 30.03.2023, Rs. C-34/21, Schulbezug Hessen) `[Eigenwissen]` `[unsicher]` `[JP]`.
Abnahme: Es existiert keine Auswertung, Rangliste oder Statistik, die Lehrkräfte nach Leistung oder Verhalten vergleicht (Funktionsliste-Prüfung bei Release); Schüler-, Eltern- und Monitor-Konto sehen den Abwesenheitsgrund einer Lehrkraft nie (Test über Plan, Monitor, iCal, Export); Hinweistext für Lehrkräfte (REH-047) nennt Audit und Zweckbindung.

**REH-019 · Keine ausschließlich automatisierten Entscheidungen (Art. 22)** — P0 · Status: Ist · `[JP]`
- Stundenplan-Generator, Vertretungsvorschläge, Plan-Prüfung, Notenvorschläge und Versetzungswarnungen sind **Vorschläge oder Hinweise**; die Entscheidung trifft stets eine Person (Plan übernehmen, Vertretung freigeben, Halbjahresnote festlegen). Kein Scoring, kein Profiling von Schüler/innen, keine Verhaltensbewertung, keine Werbung, keine Profilbildung.
Abnahme: Es gibt keinen Pfad, auf dem eine Note, Versetzung, Sanktion oder Vertretung ohne Aktion einer berechtigten Person wirksam wird (Test: Generatorlauf ohne „Übernehmen“ ändert den gültigen Plan nicht); Datenschutzerklärung enthält den Satz „Automatisierte Entscheidungsfindung einschließlich Profiling findet nicht statt“ nur, solange diese Abnahme besteht.

**REH-020 · Beobachtete Konten (verstärkte Protokollierung): rechtliche Voraussetzungen** — P0 · Status: offen · `[JP]`
- Technik (Ist): Schalter „Beobachtet“ je Konto (optional Ablaufdatum), jede Anfrage inklusive Lesezugriffen wird protokolliert (Zeit, Pfad, Status, Dauer, volle IP, Gerät, Sitzungs-Hash; bei Schreibzugriffen Body und Vorher/Nachher verschlüsselt; Passwörter, Codes, Dateiinhalte geschwärzt), Aufbewahrung 180 Tage, Einsicht nur mit `watch.read`, die beobachtete Person sieht die Beobachtung nicht. Anlass: Betatester mit Admin-Zugang, „aber alle actionen extrem stark geloget“.
- **Rechtliche Voraussetzungen vor dem Einschalten, je Konto** `[Entscheidung Neubau]`: (1) schriftlich dokumentierter Zweck und Rechtsgrundlage; (2) **Information der betroffenen Person vor Beginn** (Art. 13), auch wenn sie das Protokoll nicht einsehen kann – verdeckte Beobachtung wird nicht umgesetzt; (3) für Beschäftigte Abstimmung mit Personalrat und Datenschutzbeauftragten; (4) Speicherdauer höchstens 180 Tage; (5) **keine Beobachtung echter Schüler- oder Elternkonten**; erlaubt sind Demo-/Testkonten mit fiktiven Personen und Konten von Beschäftigten bzw. Testern mit Information; (6) Auskunft an die betroffene Person (Art. 15) organisatorisch über den CSV-Export, nicht über die Selbstauskunft; (7) jeder Detailabruf und Export des Beobachtungsprotokolls steht im Audit (`watch.detail`, `watch.export`, `user.watch_update`); (8) Information in den Hinweisen für Lehrkräfte (REH-047) und im Verzeichnis (V15).
- Der Satz „Audit ohne Inhalte“ gilt für beobachtete Konten nicht; diese Ausnahme steht in den TOMs (REH-036) und in den Hinweisen.
Abnahme: Beobachtung für ein Konto einschalten ohne ausgefüllte Felder „Zweck“, „Rechtsgrundlage“, „betroffene Person informiert am“ → 422; Einschalten für ein Schüler- oder Elternkonto einer Produktivinstanz → 422 mit Hinweis; beobachtete Person ruft `/beobachtete-konten` oder `/watch/*` → 404; Detailabruf und CSV-Export erzeugen Audit-Einträge; nach 180 Tagen sind Protokollzeilen gelöscht (Wartungslauf); beim Löschen des Kontos verschwinden Kennzeichen und Protokoll sofort.

**REH-021 · Chat-Moderation nur mit Einwilligung, kein Mitlesen** — P0 · Status: Ist (`chats.review` geplant) · `[JP]`
- Chats sind Ende-zu-Ende verschlüsselt; Server, Schule und Anbieter können Inhalte nicht lesen und haben keinen Generalschlüssel. Meldeweg: Inhalte erreichen Prüfende nur, wenn Teilnehmende sie freiwillig als Klartext mitsenden (serverseitig verschlüsselt, nur mit `messages.moderate`). Das Recht `chats.review` (gemeldete Chat-Auszüge) wirkt nur mit Einwilligung von Kind bzw. Eltern. Ohne Wiederherstellungscode oder Passwort gibt es keine Wiederherstellung, auch nicht durch Schule oder Betreiber; die Hinweistexte sagen das ausdrücklich (in den Altdokumenten fehlte es).
Abnahme: Datenbank-Dump der Chat-Tabellen enthält keine lesbaren Nachrichtentexte; Meldung ohne mitgesendeten Klartext → Prüfende sehen nur Metadaten; `chats.review` ohne Einwilligungsnachweis → Auszug nicht abrufbar (403); Hinweistexte Eltern/Schüler/Lehrkräfte enthalten den Satz zur fehlenden Wiederherstellung.

**REH-022 · Keine automatische Antwort an Eltern (Abwesenheitsnotiz)** — P1 · Status: Ist
- Eine „abwesend bis …“-Funktion mit automatischer Antwort an Eltern wird nicht umgesetzt (datenschutzkritisch); Abwesenheit nur als Hinweis im Chat.
Abnahme: Es gibt keine Funktion, die ohne manuelle Aktion Nachrichten an Eltern auslöst, die Abwesenheit, Grund oder Vertretung nennen; Funktionsliste-Prüfung bei Release.

**REH-023 · Zugang von Ausbildungsbetrieben zu Daten volljähriger Auszubildender** — P2 · Status: offen · `[JP]` `[unklar: rechtlich offen]`
- Der Ausbilderzugang (Plan mit Änderungen, Fehlzeiten mit Stunden, Klassenarbeiten; Krankmeldungen ohne Grund) gegen den Willen volljähriger Auszubildender ist rechtlich offen. Die Schule legt je Bildungsgang fest, ob der Zugang auch ohne Freigabe besteht; die Datenschutzinformation nennt es. Bis zur Prüfung gilt: **Volljährige geben den Betrieben je Bereich frei**.
Abnahme: Ausbilderkonto eines Betriebs für einen volljährigen Azubi ohne Freigabe → 404; mit Freigabe nur die freigegebenen Bereiche; fremder Azubi → 404.

---

## 3. Auftragsverarbeitung (Art. 28), Unterauftragnehmer, Drittland

**REH-024 · Muster-AV-Vertrag im Betreiber-Paket** — P0 · Status: offen · `[JP]`
- Das Betreiber-Paket (Hilfe, nur für Administration und Datenschutz-Zuständige sichtbar) enthält einen **Muster-Auftragsverarbeitungsvertrag** mit Anlagen (Datenkategorien, TOMs, Unterauftragnehmerliste). Der Vertrag wird zwischen Schule (Verantwortliche) und Anbieter bzw. Hoster geschlossen; ohne Vertrag ist der gehostete Betrieb nicht freigegeben. Muster stellen oft Landesdatenschutzbehörden, Kultusministerien oder Schulträger bereit; Schule darf deren Muster stattdessen verwenden. **Vor dem ersten Kunden juristisch prüfen** (Backlog B-51, Entscheidung 15 der offenen Fragen).
- Pflichtinhalte des Musters (Art. 28 Abs. 3 lit. a–h und Abs. 4, 9 `[Eigenwissen]`):

| Nr. | Klausel | Inhalt |
|---|---|---|
| 1 | Parteien, Gegenstand, Dauer | Schule = Verantwortliche; Anbieter/Hoster = Auftragsverarbeiter; Laufzeit an das Abo bzw. den Betriebsvertrag gekoppelt |
| 2 | Art und Zweck, Daten, Betroffene | Betrieb der Schulverwaltungssoftware (Stundenplan, Vertretung, Klassenbuch, Krankmeldungen, Nachrichten, Kursräume, Notenbuch, Konten); **Anlage 1 wird aus dem Datenkategorien-Katalog (REH-017) und dem Verzeichnis (REH-035) erzeugt**; Betroffene: Schüler/innen, Eltern, Lehrkräfte, Personal |
| 3 | Weisungen | nur auf dokumentierte Weisung (Textform); Konfiguration der Schule gilt als Weisung (REH-025); Hinweispflicht bei rechtswidriger Weisung |
| 4 | Vertraulichkeit | Verpflichtung aller Beschäftigten des Auftragsverarbeiters auf Vertraulichkeit |
| 5 | TOMs | Anlage 2 = TOM-Dokument (REH-036), Art. 32 |
| 6 | Unterauftragnehmer | nur mit vorheriger Zustimmung (allgemein oder im Einzelfall); Anlage 3 = Register (REH-026); Information über Änderungen mit Frist `[x Tage]` (Vorschlag 30 Tage) und Widerspruchsrecht; Weitergabe derselben Pflichten |
| 7 | Betroffenenrechte | Unterstützung der Schule (Art. 15–22); Weiterleitung von Anfragen unverzüglich, spätestens `[x Werktage]` |
| 8 | Unterstützung Art. 32–36 | Pannenmeldung an die Schule unverzüglich, Vorschlag **höchstens 24 Stunden** ab Kenntnis (REH-028); Hilfe bei DSFA und Vorabkonsultation |
| 9 | Löschung und Rückgabe | nach Vertragsende (REH-029) |
| 10 | Nachweise und Kontrollen | Nachweise (z. B. ISO 27001, BSI-Grundschutz des Rechenzentrums, Test-Restore-Protokoll), Vor-Ort- oder Remote-Prüfung durch die Schule |
| 11 | Drittland | keine Übermittlung ohne Zustimmung und Garantien (Art. 44 ff.); Standort Rechenzentrum Deutschland oder EU/EWR |
| 12 | Fernwartung/Support | nur über den befristeten Support-Zugang (REH-004) |
| 13 | Verzeichnis | der Auftragsverarbeiter führt ein eigenes Verzeichnis nach Art. 30 Abs. 2 |
| 14 | Betroffenenrechte bei Sperre | Lizenzsperre darf Datenschutz-Funktionen nicht blockieren (REH-031) |
| 15 | Form, Haftung | schriftlich oder elektronisch (Art. 28 Abs. 9); Haftungsverteilung `[JP]` |

Abnahme: Im Betreiber-Paket liegt das Muster mit allen 15 Klauseln; Anlage 1 lässt sich als Datei erzeugen und enthält exakt die Kategorien aus REH-017; das Muster trägt die Kennzeichnung nach REH-006 und die Zeile „geprüft am/durch“ ist leer, bis die Prüfung eingetragen ist; Suchlauf nach Anbieterbezeichnern im Muster → nur Platzhalter `[Auftragsverarbeiter]`.

**REH-025 · Weisungen: Konfiguration der Schule ist die dokumentierte Weisung** — P0 · Status: offen · `[JP]`
- Alle datenschutzrelevanten Einstellungen (Fristen, Rechte, Rollen, Zwei-Faktor-Modus, Drittdienste, Beobachtung, Löschautomatik) sind Weisungen der Schule an den Auftragsverarbeiter. Jede Änderung steht im Audit (wer, wann, was, ohne Inhalte). Die Seite „Datenschutz“ bietet einen Export „Weisungsstand“ (alle Einstellungen mit Datum der letzten Änderung).
Abnahme: Änderung einer Frist, eines Drittdienstes und des Zwei-Faktor-Modus → je ein Audit-Eintrag mit Konto-ID und Zeit; Export „Weisungsstand“ enthält diese drei Werte mit Änderungsdatum; Aufruf ohne `privacy.manage` → 403.

**REH-026 · Register der Auftragsverarbeiter und Drittdienste** — P0 · Status: offen · `[JP]`
- Ein Register führt jeden Dienst, der Daten der Schule empfängt oder verarbeiten kann: Dienst, Zweck, Datenkategorien, Sitz und Land, Drittlandübermittlung (ja/nein, Garantie), AV-Vertrag (ja/nein, Datum), Rechtsgrundlage, Schalter aktiv. Das Register speist Verzeichnis (REH-035), Datenschutzerklärung (REH-046) und Unterauftragnehmerliste. **Das Aktivieren einer Funktion, die einen Dienst anspricht (SMTP einrichten, SMS-Anbieter, SSO-Anbieter, Offsite-Backup, Monitoring, Passwort-Online-Prüfung, Übersetzungsdienst), legt den Registereintrag an**; ohne AV-Datum (wo nötig) Warnung auf der Betriebsseite.
- Vorbelegte Zeilen (alle Felder der Schule offen, kein Anbietername):

| Stelle | AV nötig | Anmerkung |
|---|---|---|
| Hoster / Rechenzentrum | ja | Deutschland oder EU bevorzugen; Zertifizierung (ISO 27001) erfragen |
| IT-Dienstleister des Schulträgers | ja | Zugriff auf die Instanz regeln; Administrationskonten personengebunden |
| Softwareanbieter bei Fernwartung/gehostetem Betrieb | ja, nur dann | Muster des Anbieters verwenden und prüfen |
| E-Mail-Versand (SMTP) | ja | übertragen werden Namen, Betreffzeilen, Texte |
| SMS-Anbieter (falls genutzt) | ja | übertragen werden Telefonnummern und Codes |
| Offsite-Backup-Speicher | ja | Backups mit Passphrase verschlüsselt; Anbieter sieht keinen Klartext |
| Anmeldedienste Microsoft, Google, Apple (falls genutzt) | prüfen | eigene Verantwortlichkeit oder AV je Vertrag; Datenschutzbeauftragte/n einbinden |
| Externer Monitoring-Dienst (falls genutzt) | ja | Altdokumente nennen ihn nur im Sicherheitskonzept |
| Lizenzserver des Anbieters | prüfen | überträgt nur die Felder aus REH-030 |
| Passwort-Prüfdienst (optional, USA) | prüfen | REH-033 |
| Ferien-Dienst (Import) | prüfen | `[unklar: ob Personendaten übertragen werden; Annahme: keine, REH-061]` |
| Übersetzungsdienst (optional) | ja | EU-Standort, REH-060 |
| Zertifizierungsstelle für HTTPS (z. B. Let’s Encrypt) | nein | erhält nur Domainname und Kontakt-E-Mail |

Abnahme: SMTP-Konto einrichten → Registerzeile „E-Mail-Versand“ entsteht automatisch mit Warnung „AV-Vertrag fehlt“; AV-Datum eintragen → Warnung entfällt; SSO-Anbieter Google aktivieren → Zeile entsteht mit Drittland-Kennzeichen; Export des Registers listet nur aktive Dienste; Bearbeiten nur mit `privacy.manage`.

**REH-027 · Drittland: Standard „keine Übermittlung“** — P0 · Status: offen (Teil Ist) · `[JP]`
- Standard: **keine Übermittlung in Drittländer**; Hosting im Rechenzentrum in Deutschland oder EU/EWR; kein Transfer auch nicht über US-Konzernmütter von Backup-, Mail- oder CDN-Diensten ohne geeignete Garantien (Art. 44 ff.). Dienste mit Drittlandbezug (Google-, Microsoft-, Apple-Anmeldung, SMS-Anbieter, Passwort-Online-Prüfung) sind **nur über den Schalter im Register** aktivierbar, mit Hinweis „Drittlandbezug“; Datenschutzerklärung und Verzeichnis ergänzen den Satz automatisch (Widerspruch der Altdokumente: „Drittland: keine“ trotz optionaler Passwort-Prüfung). Angemessenheit/Garantien (z. B. EU-US-Datenschutzrahmen) und deren Bestand sind vor Aktivierung zu prüfen `[Eigenwissen]` `[unsicher]` `[JP]`.
Abnahme: Neue Instanz → Drittland-Satz in der Datenschutzerklärung lautet „Eine Übermittlung in Länder außerhalb der EU/des EWR findet nicht statt“; Google-Anmeldung aktivieren → derselbe Absatz wird durch eine Liste der Dienste mit Land ersetzt und das Verzeichnis zeigt „Drittland: ja“; Dienst deaktivieren → Satz kehrt zurück; Test vergleicht Register und Text.

**REH-028 · Pannenmeldung Anbieter an Schule (Art. 33 Abs. 2)** — P0 · Status: offen · `[JP]`
- Der Auftragsverarbeiter meldet jede Verletzung unverzüglich an die Schule; der Vertrag nennt eine Höchstfrist (Vorschlag 24 Stunden ab Kenntnis `[JP]`). Die Frist der Schule (72 Stunden, DSG-033) beginnt mit deren Kenntnis; die Vorfallsakte hält „Meldung des Auftragsverarbeiters am …“ als Kenntniszeitpunkt fest `[JP]`.
Abnahme: Vorfallsakte mit Feld „gemeldet durch Auftragsverarbeiter am/um“ → Countdown beginnt ab diesem Zeitpunkt; Vertragsmuster enthält die Meldefrist als Pflichtplatzhalter; Test: Akte ohne Kenntniszeitpunkt ist nicht speicherbar (422).

**REH-029 · Vertragsende: Rückgabe und Löschung** — P0 · Status: offen · `[JP]`
- Bei Vertragsende kann die Schule alle Daten maschinenlesbar exportieren (Datenbank-Export, Dateien, Konfiguration, Verzeichnis, Löschprotokoll); danach löscht der Auftragsverarbeiter die Instanz einschließlich Backups nach einer vertraglichen Frist `[x Tage]` und bestätigt dies schriftlich. Die Bestätigung nennt Datum und Umfang. Die Abo-Stufen der Lizenz (14 Tage nur Lesen, dann Sperre) gelten für diese Phase; Export und Datenschutz-Funktionen bleiben erreichbar (REH-031).
Abnahme: Instanz mit gekündigter Lizenz: Administration und Schulleitung können den Gesamtexport erzeugen (200), alle anderen Konten 403 bzw. Sperrseite; nach der Löschung existiert weder Datenbank noch Dateiablage noch Backup der Instanz (Prüfliste im Betriebshandbuch); Löschbestätigung liegt als Dokument vor.

**REH-030 · Lizenz- und Update-Verkehr: Datenminimierung** — P0 · Status: Ist
- Die Lizenzprüfung (täglich und alle 15 Minuten Status) und der Update-Dienst übertragen **ausschließlich**: Lizenzschlüssel, Instanz-ID, eigene Adresse der Instanz (höchstens 300 Zeichen), Version (höchstens 40 Zeichen), Anzahl Schüler/innen und Anzahl aktiver Konten, Nonce; beim Update zusätzlich Zustand, Zielversion, Fehlerliste, Schlüssel-Fingerabdruck. **Keine Personendaten, keine Namen, keine Inhalte.** Antworten sind signiert; der Update-Agent führt nur „Version X installieren“ aus.
Abnahme: Mitschnitt aller ausgehenden Anfragen einer Schul-Instanz an den Anbieter über einen Tag enthält nur die genannten Felder (Feldlisten-Test gegen Allowlist); ein zusätzliches Feld lässt den Test fehlschlagen; Verzeichnis und Datenschutzerklärung nennen den Lizenzserver als Empfänger mit genau diesen Kategorien (Lücke der Altvorlagen).

**REH-031 · Datenschutz-Funktionen bei Lizenzsperre erreichbar** — P0 · Status: offen · `[JP]` `[Entscheidung Neubau]`
- Die Lizenzsperre (Zahlungsverzug, Kündigung, Sofortsperre) lässt die Sperrseite die Anwendung ersetzen; Administration und Schulleitung können sich anmelden und `/lizenz` nutzen. Ergänzend bleiben für Schulleitung (`privacy.subject`, `privacy.manage`) und Administration erreichbar: Betroffenenanfragen (Register, Auskunft, Export, Sofort-Löschen, Einschränkung), Vorfallsakte und Meldevorlagen, Gesamtexport, öffentliche Seiten Impressum, Datenschutzerklärung, Barrierefreiheit. Die Schule bleibt für Fristen nach Art. 12 und 33 verantwortlich, auch wenn die Zahlung ruht.
Abnahme: Gesperrte Lizenz: Schulleitung ruft Auskunft für eine Person ab → 200; Lehrkraft ruft Stundenplan → Sperrseite; Besucher ruft `/impressum` → 200; Fristenwächter (DSG-002) und Vorfallsakte (DSG-033) funktionieren weiter.

**REH-032 · Externe Mailkonten (Postfach-Anbindung)** — P2 · Status: Ist (rechtlich offen) · `[JP]` `[unklar: Telekommunikationsrecht bei privater Nutzung]`
- Die Anbindung externer Postfächer (IMAP/SMTP bekannter Anbieter oder eigener Server mit Recht `mail.custom_server`) speichert Zugangsdaten verschlüsselt, nur für das eigene Konto, löscht sie bei Kontolöschung und führt den Anbieter im Register (REH-026). Ob eine private Nutzung des Postfachs zusätzliche Pflichten auslöst (Fernmeldegeheimnis), ist zu prüfen; bis dahin Hinweis „dienstliche Nutzung“. Ausgehende Verbindungen laufen über die zentrale Zielprüfung (SIC).
Abnahme: Mailkonto eines Nutzers ist für andere Konten (auch Administration) weder lesbar noch auflistbar (404); Zugangsdaten sind in der Datenbank nur als Chiffrat; Kontolöschung entfernt das Mailkonto; Anbieter „Eigener Server“ ohne Recht → 403.

**REH-033 · Passwort-Prüfung gegen bekannte Datenlecks** — P1 · Status: Ist · `[JP]`
- Standard: **Offline-Liste** (mindestens 3000 Einträge, SIC/ANM), **keine** Online-Prüfung (Dritte, USA, DSGVO; Betreiberentscheidung O-12). Die Online-Prüfung (k-Anonymität, nur die ersten 5 Zeichen des SHA-1-Werts, fail-open) ist optional, standardmäßig aus (`SM_HIBP_CHECK=0`) und nur über das Register aktivierbar; Aktivierung ergänzt Datenschutzerklärung und Verzeichnis automatisch (Drittland USA, Übermittlung: IP-Adresse des Servers und Hash-Präfix).
Abnahme: `SM_HIBP_CHECK` nicht gesetzt → beim Passwortwechsel keine ausgehende Verbindung; Einschalten → Registerzeile „Passwort-Prüfdienst“ mit Drittland-Kennzeichen und Hinweis in der Datenschutzerklärung; Dienst nicht erreichbar → Passwort wird akzeptiert, Warnung im Fehlerprotokoll (fail-open, dokumentiert in den TOMs).

---

## 4. Betroffenenrechte (Art. 12–22) als Funktionen und Fristen

**Grundfrist (Art. 12 Abs. 3 `[Eigenwissen]` `[JP]`):** Antwort unverzüglich, spätestens **einen Monat** nach Eingang; Verlängerung um bis zu **zwei weitere Monate** nur bei Komplexität oder Anzahl der Anträge, mit Mitteilung samt Gründen **innerhalb des ersten Monats**. Auskunft und Maßnahmen sind unentgeltlich; bei offenkundig unbegründeten oder exzessiven Anträgen sind Entgelt oder Ablehnung mit Begründung möglich `[JP]`. Wird nicht oder nur teilweise entsprochen, enthält die Antwort Gründe, den Hinweis auf das Beschwerderecht bei der Aufsichtsbehörde und den Rechtsweg. Das Haftungsrisiko bei verfehlter Auskunft ist real: Schadensersatz nach Art. 82 DSGVO ist ohne Erheblichkeitsschwelle möglich (EuGH C-300/21, C-340/21, C-200/23; Gegenpol C-687/21; weitere Entscheidung zur Auskunft nur in einer Quelle `[unsicher]`).

| Recht | Norm | Funktion im Produkt | Auslöser | Frist | Recht/Rolle |
|---|---|---|---|---|---|
| Information | Art. 13/14 | Hinweistexte, Datenschutzerklärung (REH-041 ff.) | Einführung, jede Änderung | vor Beginn der Verarbeitung | `settings.edit` |
| Auskunft, Kopie | Art. 15 | Selbstauskunft (DSG-004), Schulauskunft (DSG-005) | Antrag oder Selbstbedienung | 1 Monat (+2) | eigenes Konto; `privacy.subject` |
| Berichtigung | Art. 16 | Stammdaten/Benutzer, Verknüpfung aus der Auskunft (DSG-007) | Antrag | 1 Monat (+2) | `masterdata.edit`, `users.manage` |
| Löschung | Art. 17 | Fristlöschung, Sofort-Löschen (DSG-009, DSG-010) | Antrag oder Frist | 1 Monat (+2) | `privacy.subject` |
| Einschränkung | Art. 18 | Sperrvermerk (DSG-008) | Antrag, Streit um Richtigkeit | 1 Monat (+2) | `privacy.subject` |
| Mitteilung an Empfänger | Art. 19 | Empfängerliste (DSG-014) | nach Berichtigung/Löschung/Einschränkung | unverzüglich | `privacy.subject` |
| Übertragbarkeit | Art. 20 | maschinenlesbarer Export (DSG-013) | Antrag | 1 Monat (+2) | eigenes Konto; `privacy.subject` |
| Widerspruch | Art. 21 | Widerspruchs-Vorgang (DSG-012) | Antrag | 1 Monat (+2) | `privacy.subject` |
| Automatisierte Entscheidung | Art. 22 | nicht vorhanden (REH-019) | – | – | – |
| Widerruf einer Einwilligung | Art. 7 Abs. 3 | Profil, Einwilligungsübersicht (REH-012) | Selbstbedienung | sofort | eigenes Konto; Eltern |

**DSG-001 · Register der Betroffenenanfragen** — P0 · Status: offen (Quelle: Backlog W4-04 „Auskunftsfristen Art. 12“)
- Jeder Antrag wird als Vorgang erfasst: `art` (`auskunft`, `berichtigung`, `loeschung`, `einschraenkung`, `widerspruch`, `uebertragbarkeit`, `widerruf`, `sonstige`), `eingang_am`, `kanal` (`app`, `mail`, `schriftlich`, `muendlich`), Antragsteller (Person oder Vertretung), betroffene Person (ID), `identitaet_geprueft` (am, durch), `frist_ende` (Eingang + 1 Kalendermonat; fehlt der Tag im Zielmonat, letzter Tag des Monats), `verlaengert_bis` (höchstens Eingang + 3 Monate) mit `verlaengerung_begruendung` und Datum der Mitteilung, `status` (`neu`, `in_pruefung`, `beantwortet`, `teilweise_abgelehnt`, `abgelehnt`, `zurueckgezogen`), Bearbeiter, `antwort_am`. **Keine Inhalte der Daten** im Register. Aufbewahrung 1095 Tage nach Abschluss (Nachweis Art. 5 Abs. 2, wie das Löschprotokoll) `[Entscheidung Neubau]`. Sichtbar für `privacy.manage` (Zahlen und Status); Bearbeiten und Antworten für `privacy.subject`.
Abnahme: Antrag am 31.01. erfasst → `frist_ende` 28.02. (bzw. 29.02. im Schaltjahr); Verlängerung ohne Begründung → 422; Verlängerung über Eingang + 3 Monate → 422; Mitteilung der Verlängerung nach Ablauf des ersten Monats → Warnung „Mitteilungsfrist verstrichen“; Konto ohne `privacy.manage` ruft das Register → 403; Eintrag enthält kein Feld mit Inhalt der Personendaten.

**DSG-002 · Fristenwächter** — P1 · Status: offen
- Der stündliche Wartungslauf prüft offene Vorgänge: am **21. Tag** Hinweis „bald fällig“, am **28. Tag** „dringend“, ab dem Fristtag „überfällig“ (Benachrichtigung und Startkachel an Schulleitung und Konten mit `privacy.manage`; Werte 21 und 28 `[Entscheidung Neubau]`). Ein überfälliger Vorgang ohne Verlängerungsmitteilung wird in der Statusseite als Warnung geführt. Läuft auch bei Lizenzsperre (REH-031).
Abnahme: Vorgang mit Eingang vor 21 Tagen → eine Benachrichtigung „bald fällig“ (nicht mehrfach pro Lauf); vor 29 Tagen → „dringend“; nach Fristablauf → Statusseite zeigt Warnung; Benachrichtigung enthält keinen Namen und keinen Inhalt der Anfrage; Konto ohne Recht erhält keine Benachrichtigung.

**DSG-003 · Identitätsprüfung und Antragsberechtigung** — P0 · Status: offen · `[JP]`
- Anträge über das angemeldete Konto gelten als authentifiziert; Anträge auf anderem Weg brauchen einen Identitätsnachweis nach Verfahren der Schule (Art. 12 Abs. 6 bei begründeten Zweifeln). Berechtigt sind: die Person selbst; **Eltern für minderjährige Kinder**; das Kind selbst ab Einsichtsfähigkeit (Orientierung Schulvorgabe `einwilligungsalter`, REH-013 `[unsicher]`); **volljährige Schüler/innen nur selbst**, Eltern nur mit Freigabe bzw. Vollmacht; Schulbegleitung hat keine Elternrechte. Eltern erhalten Daten ihrer Kinder nur im Umfang von `parent_access`; Förderdaten nur bei minderjährigen Kindern. Auskunft an Eltern volljähriger Kinder nur auf deren Wunsch.
Abnahme: Elternkonto beantragt Auskunft über ein minderjähriges Kind → Vorgang zulässig; über ein volljähriges Kind ohne Freigabe → 404; Antrag einer Schulbegleitung → abgewiesen mit Hinweis; Vorgang ohne vermerkte Identitätsprüfung lässt sich nicht auf „beantwortet“ setzen.

**DSG-004 · Selbstauskunft (Art. 15, 20)** — P0 · Status: Ist (Ergänzungen offen)
- Jedes angemeldete Konto kann unter *Profil → Daten exportieren* alle eigenen personenbezogenen Daten abrufen: `GET /api/v1/me/export` (JSON, Dateiname `meine-daten-<Benutzername>.json`) oder `?format=zip` (`daten.json` und `uebersicht.html`, Titel „Meine Daten – <Name>“). Jeder Abruf im Audit (`user.export`).
- Abschnitte: `exported_at`, `account`, `permissions`, `two_factor_enabled` (nur ja/nein), `ical_link_active` (kein Token), `sessions` (Erstellung, letzte Aktivität, Ablauf, IP, Browserkennung), `api_tokens` (Name, Präfix, Zeiten; kein Wert), `login_attempts`, `audit_log`, `announcements_authored`, `students`, `teacher`/`teacher_change_requests` (Freitexte entschlüsselt), `contact` (E-Mail, Bestätigung, Telefon entschlüsselt), `identities`, `absences`, `student_documents`, `support`, `forms`, `exam_results`, `gradebook_*`, `competency_*`, `register_attendance`, `assignment_submissions`, `selftest_attempts`, `poll_participation`, `survey_participation` (anonyme nur „anonym gespeichert“), `progress_*`, `channel_groups`, `notifications`, `notification_settings`, `mailbox_conversations` (Text entschlüsselt), `chats`/`chat_devices`/`chat_key_backup_exists`/`chat_reports_filed` (eigene Chat-Nachrichten nur verschlüsselt, mit Hinweis „Inhalte nur auf eigenen Geräten lesbar“), `files`, `api_token_log`, `parent_accounts`/`parent_access_settings` (für Schüler/innen), `linked_children` (für Eltern), `hinweise` (Abschnitte, die nicht vollständig ausgelesen werden konnten; die Auskunft bricht bei Einzelfehlern nicht ab). **Nicht enthalten:** Beobachtungsprotokoll (REH-020), Verwaltungsseiten, die dem Konto nicht zustehen, Geheimnisse (Token-Werte, Hashes, Schlüssel).
- **Änderung im Neubau `[Entscheidung Neubau]`:** keine stille Kappung. Die Altgrenzen (1000 Anmeldeversuche, 5000 Audit-/Benachrichtigungs-/Token-Protokolleinträge) entfallen; große Abschnitte werden als eigene Datei im ZIP (JSON Lines) geliefert, damit die Auskunft vollständig ist.
Abnahme: Konto ruft `/me/export?format=zip` → ZIP mit `daten.json` und `uebersicht.html`, Audit `user.export`; Test legt 6000 Benachrichtigungen an → alle 6000 sind im ZIP enthalten; Datei enthält keinen Token-Wert, kein Passwort-Hash, kein TOTP-Geheimnis; Elternkonto erhält zusätzlich nur Bereiche der Kinder, die `parent_access` erlaubt, und keine Förderdaten volljähriger Kinder; Export eines anderen Kontos über diese Route ist nicht möglich (404).

**DSG-005 · Schulauskunft zu einer Person** — P0 · Status: Ist (Ergänzungen offen)
- `GET /api/v1/privacy/export?student_id=…` oder `?user_id=…` bzw. `GET /api/v1/users/{id}/export`; Recht `privacy.subject` (Standard nur Schulleitung; **nie technische Administration**, weil Gesundheits- und Notendaten enthalten sind; der Backlog nannte Sekretariat, die jüngere Rechteentscheidung vom 17.10. überstimmt das). Ergebnis ZIP `auskunft-<Benutzername>.zip` mit `daten.json` und `uebersicht.html` (Titel „Auskunft nach Art. 15 DSGVO – <Name>“); zusätzlich **PDF** der Übersicht (Backlog B-57). Audit `privacy.export` bei jedem Abruf.
- **Daten Dritter geschwärzt** (Namen anderer Kinder in Nachrichten; von der Moderation ausgeblendete Texte als „[von der Moderation ausgeblendet]“; Bcc-Empfänger nicht genannt). Freitexte anderer Personen mit Namen werden nicht automatisch durchsucht (Grenze, siehe DSG-031).
- **Personen ohne Konto:** Das Altsystem lieferte 404 mit dem Hinweis, die Auskunft manuell aus der Schülerakte zu erstellen. Im Neubau liefert die Auskunft **auch für Schüler/innen ohne Konto** (aus Stammdaten, Klassenbuch, Noten, Krankmeldungen über die Schüler-ID) `[Entscheidung Neubau]`.
Abnahme: Schulleitung ruft Auskunft für Schüler-ID ohne Konto → 200 mit ZIP; Administration ruft dieselbe Route → 403/404 ohne Daten; Nachrichten anderer Kinder erscheinen mit geschwärzten Namen; Audit `privacy.export` mit Ziel `student:<ID>`, ohne Inhalt; Abruf ohne Bestätigung der Identitätsprüfung (DSG-003) eines offenen Vorgangs ist möglich, erzeugt aber Warnhinweis „kein Vorgang verknüpft“.

**DSG-006 · Vollständigkeit der Auskunft: Begleitblatt und Protokolleinträge** — P0 · Status: offen · `[JP]`
- Die Auskunft enthält zusätzlich die **Pflichtinformationen des Art. 15 Abs. 1** als Begleitblatt `{{…}}` aus Konfiguration: Zwecke, Kategorien, Empfänger (Register REH-026), Speicherdauer je Datenart (DSG-018), Herkunft der Daten, Rechte (Berichtigung, Löschung, Einschränkung, Widerspruch), Beschwerderecht, Hinweis auf fehlende automatisierte Entscheidung (REH-019).
- **Protokolleinträge zur Person** (Audit-Einträge mit Ziel `student:<ID>`/`user:<ID>`, Zugriffe auf Gesundheits- und Förderdaten) sind enthalten, soweit sie Daten der Person betreffen; die Namen handelnder Beschäftigter nur, soweit rechtlich erforderlich `[JP]` (Audit-Fund: Auskunft enthielt keine Protokolleinträge zu Schüler/innen). Rechte Dritter (Art. 15 Abs. 4) bleiben gewahrt.
Abnahme: Auskunft enthält den Abschnitt „Informationen nach Art. 15 Abs. 1“ mit Speicherdauern, die den eingestellten Fristen entsprechen (Test: Frist ändern → Begleitblatt ändert sich); ein Audit-Eintrag mit Ziel der Person erscheint in der Auskunft; Namen von Beschäftigten sind je nach Einstellung `audit_namen_in_auskunft` (`nein` Standard) durch Rollenbezeichnung ersetzt.

**DSG-007 · Berichtigung (Art. 16)** — P0 · Status: Ist (Verknüpfung offen)
- Berichtigung über *Stammdaten* bzw. *Benutzer*; aus der Auskunft (DSG-005) und dem Vorgang (DSG-001) führt ein Link direkt zum betroffenen Datensatz (Backlog B-57 Kriterium 2). Jede Änderung im Audit mit geänderten Feldern (ohne Freitext). Nach der Berichtigung zeigt der Vorgang die Liste der Empfänger/Systeme für Art. 19 (DSG-014).
Abnahme: Falscher Name in Stammdaten, Berichtigung gespeichert → Audit-Eintrag mit Feldnamen und Konto-ID; Link aus der Auskunft öffnet den Datensatz; Konto ohne `masterdata.edit` → 403; fremder Datensatz → 404.

**DSG-008 · Einschränkung der Verarbeitung (Art. 18)** — P0 · Status: offen (Teil Ist: Konto deaktivieren) · `[JP]`
- Sperrvermerk je Person: `eingeschraenkt_seit`, `grund` (`richtigkeit_bestritten`, `unrechtmaessig_loeschung_abgelehnt`, `rechtsanspruch`, `widerspruch_anhaengig`), gesetzt durch. Wirkung: Konto gesperrt und Sitzungen beendet; die Person erscheint nicht in Listen, Exporten, Benachrichtigungen, Vertretung und Suchen außer für Schulleitung (lesend); Daten werden nur gespeichert. Bei den Gründen `richtigkeit_bestritten` und `rechtsanspruch` pausiert die Fristlöschung dieser Person; Wiedervorlage nach 180 Tagen `[Vorschlag Schreiber]`. Aufheben nur durch Schulleitung **nach vorheriger Unterrichtung der Person** (Art. 18 Abs. 3).
Abnahme: Sperrvermerk setzen → Person fehlt in Klassenliste, Vertretungsplan, Benachrichtigungsempfängern und CSV-Export; Schulleitung sieht sie weiterhin; Aufheben ohne vermerkte Unterrichtung → 422; Wartungslauf löscht bei Grund `rechtsanspruch` nichts dieser Person; Audit `privacy.restrict` ohne Inhalte.

**DSG-009 · Löschverlangen: Sofort-Löschen (Art. 17)** — P0 · Status: Ist
- Unter *Datenschutz → Betroffene*, nur mit `privacy.subject`: zuerst **Vorschau** (Zahlen je Datenart), dann **Bestätigung durch exaktes Eintippen** der Personen-ID bzw. des Benutzernamens (sonst 422). Ablauf: Eintrag in der Warteliste (Quelle `planung`, Name verschlüsselt) → Entfernen aus dem Planungsdokument (eigene Planversion) → alle Datenarten ohne Wartefrist (Modus `sofort`), Planverlauf vor den Konten → Audit `privacy.erase` mit Länge und verschlüsseltem Grund (höchstens 200 Zeichen) und Anzahl erledigter Datenarten. Scheitert ein Schritt: Audit `privacy.erase_failed`, Status bleibt `wartend`, erneuter Aufruf führt zu Ende. **Unwiderruflich**, kein Papierkorb. Ausgenommen: das eigene Konto und Administrationskonten (siehe DSG-021 für deren Löschung).
Abnahme: Vorschau → keine Datenänderung (Zählvergleich vorher/nachher gleich); falsch getippte ID → 422 und nichts gelöscht; richtige ID → alle Datenarten der Person weg, Löschprotokoll mit Modus `sofort` und Anzahl, Audit ohne Inhalte; Fehler in Datenart 5 (erzwungen) → `privacy.erase_failed`, zweiter Aufruf löscht den Rest; Konto ohne `privacy.subject` → 403; Administrationskonto als Ziel → 409.

**DSG-010 · Prüfung der Ausnahmen (Art. 17 Abs. 3) und Teilablehnung** — P0 · Status: offen · `[JP]`
- Vor dem Sofort-Löschen zeigt die Vorschau je Datenart, ob eine **gesetzliche Aufbewahrungspflicht** nach dem aktiven Fristenprofil besteht (z. B. amtliches Klassenbuch, Zeugnislisten, REH-070 ff.) oder ein Rechtsanspruch geltend gemacht wird. Betroffene Datenarten werden **nicht gelöscht, sondern eingeschränkt** (DSG-008); die Antwort an die Person nennt die Teilablehnung mit Begründung und Beschwerderecht (DSG-015). Der Vorgang erhält Status `teilweise_abgelehnt`.
Abnahme: Fristenprofil mit Aufbewahrung Klassenbuch 10 Jahre; Sofort-Löschen einer Schülerin → Klassenbuch-Anwesenheit bleibt (eingeschränkt), Krankmeldungen und Nachrichten werden gelöscht; Vorgang zeigt `teilweise_abgelehnt` mit Liste der verbliebenen Datenarten; ohne aktives Profil → Warnung „Aufbewahrungspflichten nicht geprüft“ vor der Bestätigung.

**DSG-011 · Zwei-Personen-Freigabe für Sofort-Löschen** — P1 · Status: offen (Quelle: Backlog W4-04)
- Sofort-Löschen verlangt zusätzlich die Freigabe durch eine **zweite Person** mit `privacy.subject` (nicht die auslösende) in eigener Sitzung nach Ansicht derselben Vorschau. Die Anfrage verfällt nach einer einstellbaren Frist (Standard 7 Tage `[Vorschlag Schreiber]`). Schulen mit nur einem Konto mit diesem Recht können die Regel abschalten; die Abschaltung steht im Audit.
Abnahme: Schulleitung A löst aus → Löschung läuft nicht; Schulleitung A bestätigt selbst → 409; Schulleitung B bestätigt → Löschung läuft; nach 8 Tagen ohne Freigabe → Anfrage `verfallen`, nichts gelöscht.

**DSG-012 · Widerspruch (Art. 21)** — P1 · Status: offen · `[JP]`
- Vorgang `widerspruch` mit Begründung der besonderen Situation; Entscheidung der Schulleitung mit dokumentierten Gründen (Beenden/Einschränken der Verarbeitung der betroffenen Datenart oder Darlegung zwingender schutzwürdiger Gründe, z. B. Schulpflicht, gesetzliche Pflicht); bis zur Entscheidung optional Einschränkung (Art. 18 Abs. 1 lit. d, DSG-008). Gegen gesetzlich vorgeschriebene Verarbeitungen läuft der Widerspruch regelmäßig ins Leere `[Eigenwissen]` `[JP]`.
Abnahme: Widerspruch erfasst → Vorgang mit Frist; Entscheidung ohne Begründung → 422; Entscheidung „stattgegeben“ für Datenart „Benachrichtigungen per E-Mail“ → Versand endet sofort; Antwortbaustein enthält Beschwerderecht.

**DSG-013 · Datenübertragbarkeit (Art. 20)** — P2 · Status: Ist (rechtlicher Rahmen offen) · `[JP]` `[Eigenwissen]`
- Art. 20 gilt nur für Daten, die auf Einwilligung oder Vertrag beruhen und automatisiert verarbeitet werden; für die schulrechtliche Verarbeitung (Art. 6 Abs. 1 lit. e) ist er in der Regel nicht anwendbar. Das Produkt bietet den maschinenlesbaren Export (JSON/CSV in der Auskunft) trotzdem an.
Abnahme: Selbstauskunft liefert `daten.json` als gültiges JSON mit festem Schlüsselset; CSV-Spalten sind gegen Formel-Einschleusung entschärft (SIC).

**DSG-014 · Mitteilung an Empfänger (Art. 19)** — P2 · Status: offen
- Nach Berichtigung, Löschung oder Einschränkung zeigt der Vorgang die Empfänger/Systeme, an die Daten der Person weitergegeben wurden (Register REH-026, Exportziele wie Untis, SchILD, ASV, LUSD, Webhooks, API-Zugänge) mit Schalter „informiert am“; keine automatische Weitergabe.
Abnahme: Löschvorgang einer Person, deren Daten über einen Webhook-Zugang bezogen wurden → Liste enthält den Zugang; Schalter „informiert“ speichert Datum und Konto; Liste enthält keine Inhalte.

**DSG-015 · Antwortbausteine** — P1 · Status: offen · `[JP]`
- Textbausteine für Antworten (Sie-Form, einfache Sprache): Eingangsbestätigung, Fristverlängerung mit Gründen, Antwort mit Auskunft, Teilablehnung mit Begründung, Ablehnung, jeweils mit Hinweis auf das Beschwerderecht bei der Aufsichtsbehörde (`{{aufsichtsbehoerde}}`) und Kontakt der bzw. des Datenschutzbeauftragten. Die Bausteine tragen die Kennzeichnung nach REH-006.
Abnahme: Antwortbaustein „Teilablehnung“ enthält Beschwerderecht und Aufsichtsbehörde aus den Stammdaten (REH-002); leere Aufsichtsbehörde → Platzhalter bleibt als `[Aufsichtsbehörde]` und löst die Warnung nach REH-044 aus.

---

## 5. Löschkonzept (Art. 5 Abs. 1 lit. e, Art. 17)

Grundsatz: Die Fristen sind **Vorschläge der Software, keine Rechtsberatung**. Maßgeblich sind DSGVO, BDSG, Landesschulgesetz, Schuldatenverordnung und Aktenordnung des jeweiligen Landes `[JP]`. Amtliche Zeugnisse, Zeugnislisten und Schülerstammblätter gehören in die Schülerakte bzw. das Schulverwaltungsprogramm und werden dort nach Aktenordnung aufbewahrt, **nicht in dieser Software** (Löschkonzept, Begründung der Voreinstellungen).

**DSG-016 · Registrierungspflicht je Datenart** — P0 · Status: Ist
- Jedes Modul mit personenbezogenen Daten registriert **seine Datenart einmal**: Bezeichnung, Kategorie (Gesundheit, Leistung, Unterricht, Kommunikation, Konten, System), Rechtsgrundlage, Standardfrist, Löschfunktion mit Trockenlauf (zählt nur), Auskunftsfunktion, Ermittlung der betroffenen Personen. Danach erscheinen Frist, Vorschau, Warteliste, Protokoll, Sofort-Löschen und Auskunft automatisch. Die Löschfunktionen sind wiederholbar (idempotent).
Abnahme: Regressionstest scannt das Datenbankschema: jede Tabelle mit Verweis auf eine Person (Schüler-ID, Konto-ID, Eltern-ID) ist einer registrierten Datenart zugeordnet oder steht mit Begründung auf einer Ausnahmeliste; eine neue Tabelle ohne Zuordnung lässt den Test fehlschlagen; eine neue Datenart erscheint ohne weiteren Code in Fristenseite, Vorschau und Auskunft.

**DSG-017 · Fristenmodell und Wertebereiche** — P0 · Status: Ist (Änderung: „0“ entfällt)
- `grace_days` (Wartelisten-Frist): Standard **30 Tage**, Bereich 0–3650; Mindestfrist nach Austritt für **jede** Datenart. Wirksame Frist je Datenart = größerer Wert aus eigener Frist und `grace_days`. Einstellungen je Datenart: `<datenart>.days` (Tage nach Austritt) und, wo vorhanden, `<datenart>.age_days` (Alters-Frist, laufend unabhängig vom Austritt). `audit_days` 365 (Startwert `SM_AUDIT_RETENTION_DAYS`), `log_days` 1095. **Obergrenze aller Fristen: 3650 Tage.**
- **Neu gegenüber dem Altsystem `[Entscheidung Neubau]`:** Kein Konfigurationswert „0“ schaltet eine Löschung ab (Altsystem: 0 = nie/aus bei `audit_days`, `log_days`, `age_days`, `messaging_retention_days`, `SM_STUDENT_DOCS_RETENTION_DAYS`; Audit-Fund „0 schaltet die Löschung ganz ab“). Zulässig sind ganze Zahlen von 1 bis 3650; 0 und größere Werte werden mit 422 abgewiesen, Umgebungsvariablen mit ungültigem Wert verhindern den Start.
- Alters-Fristen und die Fristen der technischen Protokolle laufen **immer**. Der Schalter `auto_purge` (Standard an) steuert nur die **automatische** Fristlöschung nach Austritt; ist er aus, löscht der Knopf *Fälliges jetzt löschen* trotzdem (Altsystem: auch der Knopf blieb wirkungslos, Hinweis 4 der Wertequelle).
Abnahme: `audit_days=0` per Oberfläche → 422; `SM_STUDENT_DOCS_RETENTION_DAYS=0` in der Umgebung → Start bricht ab mit Meldung; `age_days=5000` → 422; `auto_purge` aus → Wartungslauf löscht nichts nach Austritt, *Fälliges jetzt löschen* löscht fällige Datenarten, Statusseite zeigt Warnung „Automatische Löschung aus“; Wirksame Frist: Datenart mit 10 Tagen und `grace_days` 30 → 30.

**DSG-018 · Standardfristen je Datenart** — P0 · Status: Ist (Ergänzungen in DSG-021 bis DSG-023)
- Alle Löschungen sind **hart** (endgültig), außer wo „anonymisiert“ steht. Auslöser „Austritt“ = Eintrag in die Warteliste (DSG-020). Die Standardwerte sind änderbar (Bereich 1–3650) und je Land durch ein Fristenprofil überschreibbar (DSG-019).

| Datenart (Schlüssel) | Kategorie | Frist nach Austritt | Laufende Alters-Frist | Verfahren |
|---|---|---|---|---|
| Krankmeldungen und Fehlzeiten (`absences`) | Gesundheit | 30 Tage | 365 Tage; eine Meldung ist abgelaufen, wenn ihr Enddatum vor dem letzten 31. Juli liegt, der vor (heute − 365 Tage) liegt (`absences.age_days`) | löschen: Meldungen, Meldungsprotokoll, Nachschreibtermine; Blöcke zu 500 |
| Atteste und Dokumente (`documents`) | Gesundheit | 30 Tage | 400 Tage ab Erstellung (`documents.age_days`, Startwert `SM_STUDENT_DOCS_RETENTION_DAYS`) | löschen: Datensatz und Datei; höchstens 5000 je Lauf; erfasst auch vom Konto der Person hochgeladene Dokumente |
| Förder- und Unterstützungsdaten (`support`) | Gesundheit | 30 Tage | keine | löschen: Datensatz und alle zugehörigen Dateien |
| Formular-Einreichungen (`forms`) | Gesundheit/Unterricht | 90 Tage | 400 Tage ab Erstellung, nur abgeschlossene (`forms.age_days`) | löschen: Einreichung, Dateien, Verlauf; höchstens 5000 je Lauf |
| Klausurergebnisse (`exam_results`) | Leistung | 180 Tage | keine | löschen |
| Notenbuch (`gradebook`: Einzel-, Halbjahres-, Zeugnisnoten, Änderungsprotokoll, Quellergebnisse) | Leistung | 180 Tage | keine | löschen |
| Lernstand und Kompetenzen (`competencies`) | Leistung | 180 Tage | keine | löschen |
| Klassenbuch-Anwesenheit (`attendance`) | Leistung | 365 Tage | keine | **anonymisieren**: nur der Eintrag der Person im Anwesenheitsfeld; Thema und Hausaufgabe bleiben (Fristenprofil und Schalter „amtliches Klassenbuch“: REH-071) |
| Abgaben und Rückmeldungen (`submissions`) | Unterricht | 90 Tage | keine | löschen: Abgaben, Versionen, Dateien, Bewertungen |
| Selbsttests, Abstimmungen, Umfragen (`learning`) | Unterricht | 90 Tage | keine | löschen; anonym gespeicherte Umfrage-Antworten sind nicht zuordenbar und bleiben |
| Fortschritt und Kursraum-Nutzung (`progress`) | Unterricht | 90 Tage | keine | löschen: Erledigt-Markierungen, geöffnetes Material, Gruppen, Fristverlängerungen |
| Hochgeladene Dateien (`files`) | Unterricht | 30 Tage | keine | löschen (Inhalt und Eintrag) |
| Benachrichtigungen (`notifications`) | Kommunikation | 30 Tage | 90 Tage (Einstellung der Schule 7–730 Tage) | löschen: an die Person und über sie (z. B. an Eltern), Einstellungen |
| Postfach-Nachrichten (`messages`) | Kommunikation | 30 Tage (eigene gesendete, Entwürfe, Sperrlisten, Teilnahmen, Einstellungen) | 365 Tage (`messaging_retention_days`), außer offen gemeldete | löschen; leere Unterhaltungen entfernt; Nachrichten anderer bleiben bis zu deren Frist |
| Chats Ende-zu-Ende (`chats`) | Kommunikation | 30 Tage | `[unklar: Altsystem ohne laufende Frist]` Vorschlag 365 Tage, siehe DSG-027 | löschen: Mitgliedschaften, Geräte, Schlüssel-Backup, Nachrichtenschlüssel, eigene Nachrichten und Anhänge, Meldungen; Einzelchats ganz; Gruppen ohne Mitglieder |
| Eltern-Verknüpfungen und Freigaben (`parents`) | Konten | 30 Tage | keine | löschen: `parent_links`, `parent_access`, `student_prefs`; Eltern-Konto (Rolle Eltern/Schulbegleitung) ohne weiteres Kind wird mit Konto gelöscht |
| Schüler-Konten (`accounts`) | Konten | 30 Tage, **läuft zuletzt** | keine | löschen; Sitzungen, Tokens, Anmeldeversuche, Verknüpfungen entfallen; Audit pseudonymisiert; Administrationskonten nie automatisch |
| Planverlauf und Protokoll-Bezüge (`history`) | System | 30 Tage | keine | **anonymisieren**: Person aus allen gespeicherten Planversionen entfernt, Namen in Versionstexten durch „[gelöscht]“ ersetzt, Protokollziele `student:<ID>` → `student:gelöscht`, Details entfernt |
| API-Protokoll (`api_log`) | System | 30 Tage | 90 Tage (`api_log.age_days`) | löschen |
| Beobachtungsprotokoll (`watch_log`, `account_watch`) | System | 30 Tage; bei Kontolöschung sofort | 180 Tage (`watch_log.age_days`) | löschen |

Reihenfolge im Lauf (aufsteigend): Gesundheit, Leistung, Unterricht, Kommunikation, Eltern, Planverlauf, API-Protokoll, Beobachtung, **Schüler-Konten zuletzt**.

Abnahme: Test legt je Datenart einen Datensatz an, setzt die Uhr auf Austritt + Frist − 1 Tag → Datensatz vorhanden, auf + 1 Tag → gelöscht bzw. anonymisiert; Werte der Tabelle sind als Standard im Test hinterlegt; Krankmeldung mit Enddatum 15.06. wird nach dem 31.07. des Folgejahres (Stichtag-Regel) gelöscht, nicht früher; anonymisierte Klassenbuch-Zeile enthält Thema und Hausaufgabe, aber keinen Eintrag der Person; Schülerkonto wird erst gelöscht, wenn alle anderen Datenarten `erledigt` sind.

**DSG-019 · Fristenprofile je Bundesland (konfigurierbar)** — P0 · Status: offen · `[JP]`
- Ein **Fristenprofil** (Daten, nicht Code) ordnet jeder Datenart `days` bzw. `age_days`, `basis` (`austritt`, `schuljahresende`, `erstellung`, `abgang`) und `quelle` zu. Die Schule wählt unter *Datenschutz → Fristen* ein Profil; die Oberfläche zeigt die **Differenz** zu den aktuellen Einstellungen und übernimmt erst nach Bestätigung (Audit `privacy.settings`). Einzelwerte bleiben danach änderbar; abweichende Werte sind gekennzeichnet („weicht vom Profil ab“). Jedes Profil trägt `stand`, `quelle`, `juristisch_geprueft` (REH-005).
- Ausgeliefert wird das **Profil „Nordrhein-Westfalen“** als Vorlage nach dem Backlog (Verordnung über die zur Verarbeitung zugelassenen Daten der Schülerinnen und Schüler, „VO-DV I“): Klassenbuch, Kursbuch, Zeugnislisten **10 Jahre**; Schülerstammblatt **20 Jahre**; übrige Daten **5 Jahre**. `[unsicher]` `[JP]` `[unklar: Fristbeginn nicht in den Quellen]`. Umsetzung: Klassenbuch-Anwesenheit 3650 Tage (amtliches Klassenbuch, REH-071); „übrige Daten 5 Jahre“ gilt als **Höchstwert** (1825 Tage), den keine Standardfrist dieser Software überschreiten darf (alle Standardwerte liegen darunter); Schülerstammblatt (20 Jahre = 7300 Tage > Obergrenze 3650) und Zeugnislisten liegen im Schulverwaltungsprogramm, **nicht in dieser Software**.
- Weitere Länder: als eigene Vorlagen später; Hinweise der Recherche (Berlin: Schuldatenverordnung vom 07.08.2023 mit Löschfristen in § 16; Bayern: Schulordnung § 40 mit u. a. Schülerstammblatt 50 Jahre, Leistungsnachweise 2 Jahre, übrige Unterlagen 1 Jahr; Hessen: Schuldatenschutzverordnung in der Fassung vom 01.12.2023) sind **unsicher** (Sekundärquellen, nicht gegen den Gesetzestext geprüft) und werden nicht als Profilwerte ausgeliefert.
Abnahme: Profil „Nordrhein-Westfalen“ wählen → Vorschau zeigt die Differenz (z. B. `attendance` 365 → 3650); vor Bestätigung ändert sich nichts; nach Bestätigung zeigt die Fristenseite „Profil NRW, Stand [Datum], nicht rechtlich geprüft“; Profil „Bayern“ → leer, keine Werte; Wert größer als 3650 im Profil → Profil wird beim Laden abgelehnt; Audit enthält Profilwechsel mit Konto-ID.

**DSG-020 · Austritt, Warteliste, Kontosperre, Konto zuletzt** — P0 · Status: Ist
- Wer nicht mehr im Planungsdokument steht (Löschen unter *Stammdaten*, Löschen einer Klasse, Import, Wiederherstellung, Schuljahreswechsel-Assistent), kommt auf die **Warteliste „ausgetreten“** (Status `wartend`/`erledigt`, Quelle `abgleich`/`planung`; Name verschlüsselt, Klasse im Klartext). Alle Konten der Person (auch Eltern-Verknüpfungen) werden sofort gesperrt, Sitzungen beendet. Rückkehr ins Planungsdokument entfernt den Eintrag und gibt die Konten frei; manuell *Austritt zurücknehmen* (409, wenn die Person nicht im Planungsdokument steht; 404, wenn kein offener Austritt). Ein **leeres Schülerverzeichnis** löst nie eine Massen-Austragung aus. Verschwindet eine bereits abgeschlossene Person erneut, beginnt die Löschung von vorn. Fehler einer Datenart: Datenart bleibt offen und wird im nächsten Lauf wiederholt, die übrigen laufen weiter; Abschluss (`erledigt`, Name geleert, Löschprotokoll `abgeschlossen`, Audit `privacy.purged`) erst, wenn alle Datenarten erledigt sind. Erledigte Wartelisten-Einträge werden nach `log_days` (1095) gelöscht.
Abnahme: Schüler aus dem Planungsdokument entfernen → Eintrag `wartend`, Konto sofort gesperrt; wieder hinzufügen → Eintrag weg, Konto frei; Import mit leerem Schülerverzeichnis → keine Warteliste-Einträge; erzwungener Fehler in einer Datenart → Person bleibt `wartend`, andere Datenarten gelöscht, nächster Lauf wiederholt; `erledigt` setzt `name_enc` auf leer.

**DSG-021 · Austritt von Beschäftigten und Lehrkräften** — P0 · Status: offen · `[Entscheidung Neubau]`
- Das Altsystem kennt die Warteliste nur für Schüler/innen; die Hinweise für Lehrkräfte versprachen „Konten ausgeschiedener Beschäftigter werden bei Ausscheiden gesperrt und nach [3 Monaten] gelöscht“ (nicht im Löschkonzept abgebildet). Im Neubau: **Austritt von Personal** (Datum, Grund) sperrt das Konto zum Stichtag, beendet Sitzungen und API-Tokens und führt die Person auf die Warteliste mit denselben Regeln wie Schüler/innen (`grace_days` 30). Kursräume werden an andere Lehrende übergeben (Pflicht vor Löschung, Warnung im Assistenten). Datenarten des Personals: Konto, Profil und Profilanträge, Sperrzeiten und Wünsche, eigene Nachrichten und Dateien, eigene Notenbuch-/Klassenbuch-Einträge (**Inhalte bleiben, Verfasser wird pseudonymisiert**, Aufbewahrung nach REH-070 ff.), Abwesenheiten (DSG-022). **Administrationskonten** werden nie automatisch gelöscht; die Löschung durch den Inhaber ist über die Benutzerverwaltung möglich (Inhaber-Konto bleibt geschützt, siehe REC); der Altbestand ließ das offen.
Abnahme: Lehrkraft mit Austritt zum Stichtag → Konto gesperrt, Eintrag `wartend`; nach `grace_days` Konto gelöscht, ihre Klassenbuch-Einträge bleiben mit `author = gelöscht#<ID>`; Austritt einer Lehrkraft mit eigenem Kursraum ohne Übergabe → Warnung im Assistenten; Administrationskonto → Löschlauf überspringt es.

**DSG-022 · Abwesenheiten und Vertretungsentscheidungen von Lehrkräften** — P0 · Status: offen
- Eigene Datenart `staff_absences`: Zeitraum, knapper Grund, Vertretungsentscheidungen. Frist: **Ende des folgenden Schuljahres** (Stichtag 31. Juli des auf das Schuljahr der Abwesenheit folgenden Schuljahres; Zweck Nachweis Unterrichtsausfall und Vertretungsabrechnung). Das Verzeichnis nannte die Frist, das Löschkonzept bildete sie nicht ab `[JP]`. Verfahren löschen; Grund ist verschlüsselt (Freitext).
Abnahme: Abwesenheit im Schuljahr 2026/27 → am 01.08.2028 gelöscht, am 31.07.2028 noch vorhanden; Grund liegt in der Datenbank als Chiffrat; Registrierung erscheint in Fristenseite und Vorschau.

**DSG-023 · Weitere Datenarten schließen** — P0 · Status: offen
- Im Altsystem nicht als Datenart geführt (Löschwirkung bei Kontolöschung nur über Fremdschlüssel, ungeprüft): Kursraum-Inhalte (Material, Ordner, Beiträge), Lehrkraft-Profilanträge, Kontaktdaten (Telefon, E-Mail) und Anbieter-Verknüpfungen, Import-Protokolle (verschlüsselter Bericht), Planvorschläge und Planschnappschüsse, Mailkonten, Ankündigungen (Verfasser nur pseudonymisiert). Im Neubau ist **jede** dieser Gruppen eine registrierte Datenart (DSG-016) mit Frist und Löschverfahren; Vorschlag: Kontaktdaten, Verknüpfungen und Mailkonten 30 Tage nach Austritt (gleich Konto), Profilanträge 90 Tage nach Abschluss, Import-Protokolle 90 Tage, Planvorschläge/Schnappschüsse nach der Planversionen-Grenze (`SM_KEEP_VERSIONS`, Standard 300), Kursraum-Inhalte Verfasser pseudonymisiert und Inhalte nach Kursende nach Schulvorgabe `[unklar: Frist nicht in den Quellen]` `[JP]`.
Abnahme: Schema-Test (DSG-016) findet keine unregistrierte personenbezogene Tabelle; Löschung einer Lehrkraft entfernt Kontaktdaten und Mailkonto; Ankündigung eines gelöschten Verfassers zeigt „gelöscht#<ID>“.

**DSG-024 · Anonymisieren und Pseudonymisieren** — P0 · Status: Ist (Ergänzung: Benutzername im Audit)
- Regeln: Audit bei Kontolöschung: `user_id` leer, `username` → `gelöscht#<Konto-ID>`, ebenso alle Einträge mit demselben Benutzernamen (Audit-Fund „Benutzername bleibt im Protokoll“ ist damit behoben und im Neubau zu prüfen). Planversionen (Verfasser leer), Mitteilungen (`author_id` leer), Krankmeldungen (`reported_by` leer), Abwesenheitsereignisse (`actor_id` leer, `actor_name` → `gelöscht#<Konto-ID>`), Anmeldeversuche des Kontos gelöscht, Klassenbuch (Eintrag der Person entfernt), anonyme Umfrage-Antworten bleiben. Das Audit `privacy.erase` bleibt mit Personen-ID und IP bis `audit_days`; der Löschgrund steht nur verschlüsselt (Bindung an die Audit-Zeile, nicht fest; Fund der Wertequelle).
Abnahme: Konto löschen → Suche nach dem Benutzernamen in Audit und Planversionen liefert 0 Treffer, `gelöscht#<ID>` an dessen Stelle; Löschgrund-Chiffrat eines Audit-Eintrags in einen anderen kopiert → nicht entschlüsselbar.

**DSG-025 · Abgang statt Löschen: Archiv-Zustand für Aufbewahrungspflichtiges** — P1 · Status: offen (Quelle: Backlog B-38) · `[JP]`
- Datenarten, für die das aktive Fristenprofil eine Aufbewahrungspflicht kennt (z. B. amtliches Klassenbuch), gehen nach dem Abgang in einen **Archiv-Zustand**: nur Sekretariat und Schulleitung lesend, jeder Zugriff im Audit, Bereinigung erst nach der Profilfrist. Das ersetzt die Altaussage „Dokumente werden nie gelöscht, nur archiviert“ (12.10.), die durch die Fristen vom 16.10. überholt ist.
Abnahme: Abgang einer Schülerin → Klassenbuch-Einträge nur für Sekretariat/Schulleitung lesbar, Lehrkraft der Klasse → 404; Zugriff erzeugt Audit-Eintrag; nach Profilfrist gelöscht.

**DSG-026 · Backups und Wiederherstellung** — P0 · Status: offen (Teil Ist)
- Das Löschkonzept wirkt **nicht** in Sicherungen. Gelöschte Daten verschwinden spätestens mit Ablauf der letzten Sicherung: Betriebsrotation 14 Tage täglich, 8 Wochen wöchentlich, 12 Monate monatlich (**höchstens 12 Monate**); App-interne Sicherung `SM_BACKUP_KEEP` 30 Dateien, automatisch nur bei `SM_AUTO_BACKUP_HOURS` > 0. Beides ist in Datenschutzerklärung und Verzeichnis zu nennen.
- **Neu `[Entscheidung Neubau]`:** Das Löschprotokoll (Personen-ID, Datenart, Zeit) wird **außerhalb der Datenbanksicherung** gesichert. Nach einer Wiederherstellung läuft automatisch ein **Nach-Löschlauf** anhand dieses Protokolls; erst danach nimmt das System Benutzer an. Altsystem: manuelle Prüfung nach Restore.
Abnahme: Person löschen, Sicherung vom Vortag einspielen → Person ist nach dem Nach-Löschlauf wieder entfernt (Test); Restore ohne vorhandenes Lösch-Ledger → Warnung „Löschprotokoll fehlt, Löschlauf manuell prüfen“ und Statusseite rot; Datenschutzerklärung nennt „höchstens 12 Monate“.

**DSG-027 · Chats: Grenzen der Löschung und Frist** — P1 · Status: offen · `[unklar]` `[Entscheidung Neubau]`
- Beim Löschen entfernt der Server seine Daten; **Kopien auf Geräten anderer Teilnehmer bleiben**, was in den Hinweistexten steht (REH-047). Das Altsystem kannte keine laufende Alters-Frist für Chats; Vorschlag: `chats.age_days` Standard 365 Tage (analog Postfach), weil unbegrenzte Speicherung der Speicherbegrenzung widerspricht `[JP]`. Löschung nach Zeitstempel erfordert keine Entschlüsselung.
Abnahme: Chat-Nachricht älter als `chats.age_days` → serverseitig gelöscht, ohne dass der Server Klartext sieht (Datenbankprüfung); Gruppenchat ohne Mitglieder → entfernt; Hinweistext Eltern enthält den Satz zu Kopien auf Geräten.

**DSG-028 · Löschprotokoll (Nachweis, Art. 5 Abs. 2)** — P0 · Status: Ist
- Tabelle `retention_log`: Datenart, Anzahl, Zeitpunkt, Modus (`automatik`, `frist`, `sofort`), Aktion (`geloescht`, `anonymisiert`, `abgeschlossen`), ausführendes Konto, Bezug (`student:<ID>` oder `user:<ID>`), Anlass (höchstens 200 Zeichen). **Nie Inhalte.** Aufbewahrung 1095 Tage (`log_days`), angezeigt als Löschprotokoll (nur Zahlen).
Abnahme: Löschlauf → je Datenart ein Protokolleintrag mit Anzahl; Test sucht in `retention_log` nach Namen oder Textinhalten gelöschter Datensätze → 0 Treffer; Eintrag älter als 1095 Tage wird gelöscht.

**DSG-029 · Vorschau und stündlicher Wartungslauf** — P0 · Status: Ist
- Vorschau *Was würde gelöscht*: Zahlen je Person und Datenart, ändert nichts, zeigt auch noch nicht fällige Datenarten; die Summe „fällig“ zählt nur Fälliges. Wartungslauf stündlich (`SM_MAINTENANCE_INTERVAL` 3600 Sekunden; Wert 0 = Wartung aus ist im Neubau eindeutig festgelegt und von der Löschung nicht betroffen; der erste Lauf beginnt sofort nach dem Start). Jede Stufe hat eigene Fehlerbehandlung; ein Fehler stoppt die übrigen Stufen nicht; die Postfach-Aufbewahrung ist eine eigene Wartungsstufe (Altsystem: Notbehelf höchstens alle 6 Stunden). Sicherungen und Löschlauf-Ergebnis stehen in der Statusseite.
Abnahme: Vorschau vor und nach Aufruf → Zähler unverändert; Lauf mit erzwungenem Fehler in der Stufe „Formulare“ → Stufe „Benachrichtigungen“ läuft trotzdem; Postfach-Nachricht älter als 365 Tage wird im regulären Lauf gelöscht (nicht erst beim Abruf eines Zählers).

**DSG-030 · Technische Protokolle: Fristen und IP-Adressen** — P0 · Status: Ist (Änderung beim Audit-IP) · `[JP]`

| Protokoll | Frist | IP-Adresse | Zweck |
|---|---|---|---|
| Zugriffsprotokoll (Proxy/App) | höchstens 14 Tage (Rotation `LOG_MAX_SIZE`, `LOG_MAX_FILES`; journald `MaxRetentionSec=14d`); `SM_ACCESS_LOG=0` schaltet ab | gekürzt: IPv4 auf /24, IPv6 auf /48 | Betrieb |
| Anmeldeversuche | 30 Tage | volle Adresse (Drosselung, Sperre) | Sicherheit |
| Audit-Protokoll | 365 Tage (`audit_days`) | je Schulvorgabe `audit_ip_mode`: **`gekuerzt` (Standard)** oder `voll` (nur mit Begründung im Verzeichnis) | Nachvollziehbarkeit |
| API-Protokoll | 90 Tage | Adresse des Aufrufers | Kontrolle der API-Zugänge |
| Beobachtungsprotokoll | 180 Tage | volle Adresse | REH-020 |
| Fehlerprotokoll | 30 Tage, höchstens 1000 Zeilen | keine | Betrieb |
| Sitzungen | bis zum Ablauf | Adresse und Browserkennung | Sicherheit |
| Download-Protokoll | wie Audit (`audit_days`; Altsystem ohne Ablauf) | gekürzt | Nachvollziehbarkeit |
| Idempotenz-Schlüssel (Doppelsende-Schutz) | 24 Stunden | keine | Betrieb |
| Löschprotokoll und erledigte Wartelisten-Einträge | 1095 Tage | keine | Nachweis |

- **Auflösung des Widerspruchs `[Entscheidung Neubau]`:** Die Altdokumente versprachen „IP-Adressen werden gekürzt gespeichert“, während Anmeldeversuche, Audit und Beobachtung volle Adressen speicherten (Audit-Fund P4-01: falsche Datenschutzinformation kann selbst abgemahnt werden). Im Neubau speichert das Audit standardmäßig gekürzte Adressen; die Datenschutzerklärung wird aus dieser Tabelle erzeugt (REH-046).
Abnahme: Anfrage von 192.0.2.77 → Zugriffsprotokoll enthält `192.0.2.0/24`, Audit-Eintrag (Standard) ebenfalls gekürzt, Anmeldeversuch die volle Adresse; `audit_ip_mode=voll` → Datenschutzerklärung ändert den Satz zu „vollständig gespeichert, 365 Tage“; Test vergleicht Text und Konfiguration; Einträge älter als die Frist sind nach dem Wartungslauf weg.

**DSG-031 · Freitexte anderer Personen mit Namen** — P3 · Status: offen · `[Vorschlag Schreiber]`
- Grenze des Altsystems: Freitexte anderer Personen mit dem Namen der Betroffenen (Mitteilungen, Vermerke von Lehrkräften) werden bei Auskunft und Löschung nicht durchsucht oder geändert. Wunsch: Werkzeug *Name in Freitexten finden* (nur Trefferliste ohne Auto-Änderung) für `privacy.subject`; bis dahin wird die Grenze in der Auskunft als Hinweis genannt.
Abnahme: Auskunft enthält den Hinweis auf die nicht durchsuchten Freitexte; (bei Umsetzung) Suche nach einem Namen liefert Treffer nur mit Datensatz-Art und -ID, ohne Textauszug, nur für `privacy.subject`.

**DSG-032 · Überwachung des Löschlaufs** — P1 · Status: offen
- Statusseite und Betriebsseite warnen, wenn (a) die automatische Löschung aus ist, (b) Fälliges länger als 7 Tage nicht gelöscht wurde (Wert `[Vorschlag Schreiber]`), (c) eine Datenart wiederholt Fehler meldet, (d) das Lösch-Ledger fehlt (DSG-026), (e) Fristen vom Profil abweichen.
Abnahme: Löschlauf aus und fälliger Datensatz älter als 8 Tage → Warnung „Löschung überfällig“ auf der Statusseite; Fehler in einer Datenart an drei Läufen → Warnung mit Datenart (ohne Personenbezug).

---

## 6. Verzeichnis der Verarbeitungstätigkeiten, TOMs, DSFA, Datenschutzpaket

**REH-034 · Verzeichnis der Verarbeitungstätigkeiten (Art. 30) aus der Konfiguration** — P0 · Status: offen (Quelle: Backlog W4-04; Altsystem nur Vorlagentext) · `[JP]`
- Seite *Datenschutz → Verzeichnis* erzeugt das Verzeichnis **aus der tatsächlichen Konfiguration** (aktive Module, Register REH-026, Fristen DSG-018, Rechtsgrundlagen REH-009, Stammdaten REH-002), nicht aus einem festen Text. Aufbau: 1 Allgemeine Angaben (Verantwortliche, Schulträger, Datenschutzbeauftragte/r, Verfahrensbezeichnung, Einführungsdatum, Betriebsform), 2 Teilverfahren (REH-035), 3 Empfänger und Auftragsverarbeiter, 4 TOMs (Verweis), 5 DSFA (Datum, Ergebnis), 6 Änderungsverlauf (Datum, Änderung, Bearbeiter). Export als PDF, CSV und JSON. Offene Pflichtfelder lösen die Warnung nach REH-044 aus. Der **Auftragsverarbeiter** führt sein eigenes Verzeichnis (Art. 30 Abs. 2); das Produkt liefert die Angaben dafür.
Abnahme: Modul „Chats“ ausschalten → Teilverfahren V6 verschwindet aus dem Export; Drittdienst aktivieren → Empfängerliste wächst; Frist ändern → Löschfrist in V-Zeile ändert sich; Export ohne eingetragene Datenschutzbeauftragte/n → Warnung „Pflichtangabe offen“; Aufruf ohne `privacy.manage` → 403.

**REH-035 · Inhalte des Verzeichnisses (Teilverfahren)** — P0 · Status: offen (Ergänzungen gegenüber der Altvorlage) · `[JP]`
- Pflichtzeilen (Löschfristen als `{{…}}` aus DSG-018; Spalten gekürzt). **Gegenüber der Altvorlage ergänzt:** Geburtsdaten, Monitor-Hinweise und Notizen (V1), Chats (V6), Beobachtungsprotokoll (V15), volle IP in Anmeldeversuchen (V11), Lizenzserver, SMS-Anbieter, Passwort-Prüfdienst, Ferien-Dienst (V14, Empfänger), Drittland nicht pauschal „keine“.

| Nr. | Tätigkeit | Betroffene | Datenkategorien | Empfänger / Besonderheit |
|---|---|---|---|---|
| V1 | Stunden-, Vertretungs-, Raum-, Aufsichts-, Klausurplanung | Schüler/innen, Lehrkräfte, Personal | Name, Klasse, Kurse, **Geburtsdatum**, Kürzel, Fächer, Deputat, Sperrzeiten/Wünsche, Abwesenheiten (Grund knapp), Vertretungsnotizen, Monitor-Hinweise | Schulleitung, Planung, Sekretariat; Lehrkräfte und Lernende im Umfang der Rolle; Monitor ohne Gründe |
| V2 | Konten und Anmeldung | alle Nutzer, Eltern | Benutzername, Name, Rolle, Passwort-Hash, optional E-Mail/Telefon, Zwei-Faktor-Geheimnis (verschlüsselt), Sitzungen, Anmeldeversuche (volle IP), SSO-Verknüpfung | Administration, Schulleitung, Sekretariat (Kontenverwaltung); SSO-Anbieter (Drittland möglich) |
| V3 | Krankmeldungen, Atteste, Fehlzeiten, Beurlaubung, Klassenbuch-Anwesenheit | Schüler/innen, Eltern | Zeitraum, Stunden, Grund/Vermerk (verschlüsselt), Status, Atteste (Datei verschlüsselt), Anwesenheit | meldende Person, Familie, Klassenleitung, Sekretariat, Schulleitung; **Art. 9** |
| V4 | Förder- und Nachteilsausgleichsdaten | Schüler/innen | Merkmal, Art, Minuten, Nachweise (verschlüsselt) | Schulleitung, Sekretariat, Klassenleitung; Fachlehrkräfte nur Art und Minuten; **Art. 9** |
| V5 | Nachrichten, Postfach, Mitteilungen, Benachrichtigungen | Schüler/innen, Eltern, Lehrkräfte | Texte (verschlüsselt), Anhänge, Absender/Empfänger, Lesestatus, gemeldete Nachrichten | Teilnehmende; Prüfende nur bei Meldung; E-Mail-/SMS-Dienst (AV) |
| V6 | Chats (Ende-zu-Ende) | Schüler/innen, Eltern, Lehrkräfte | Metadaten (Mitglieder, Zeiten, Größen), öffentliche Schlüssel, Chiffrate, Schlüssel-Backup-Blob | Teilnehmende; Server sieht keine Inhalte |
| V7 | Kursräume, Aufgaben, Abgaben, Lernaktivitäten, Fortschritt | Schüler/innen, Lehrkräfte | Material, Abgaben (Text/Datei verschlüsselt), Bewertungen, Selbsttests, Umfragen (anonym ohne Teilnehmer), Erledigt-Markierungen | Lehrende des Kursraums, Teilnehmende; Eltern nach Freigabe |
| V8 | Leistungsdokumentation: Notenbuch, Klausuren, Kompetenzen | Schüler/innen | Noten, Punkte, Kommentare, Kompetenzstufen, Abzeichen | unterrichtende Lehrkräfte, Klassenleitung, Schulleitung; Lernende/Eltern nach Freigabe; Export an Schulverwaltungsprogramm |
| V9 | Formulare, Briefe, Einwilligungen, Zugangsbriefe | Schüler/innen, Eltern, Personal | Antworten (verschlüsselt), Entscheidungen, Zugangsdaten (Brief höchstens 60 Minuten abrufbar), Einwilligungsnachweise | prüfende Stellen; Druck |
| V10 | Elternzugang und Freigaben | Eltern, volljährige Schüler/innen | Verknüpfungen, Freigaben je Bereich, Zustellweg | Familie, Schule |
| V11 | Technische Protokolle | alle | Audit, Zugriffsprotokoll (IP gekürzt), Anmeldeversuche (volle IP), API-Protokoll, Fehlerprotokoll | Administration; bei Vorfällen Schulleitung und DSB |
| V12 | Sicherung und Betrieb | alle | verschlüsselte Datenbank- und Dateisicherungen | Hoster, Offsite-Backup-Anbieter (AV); Aufbewahrung höchstens 12 Monate |
| V13 | Import, Export, Schnittstellen | Schüler/innen, Lehrkräfte | Untis, CSV, SchILD/ASV/LUSD, OneRoster, API-Zugänge, Webhooks, iCal | Schulverwaltungsprogramm, vom Nutzer gewählte Empfänger (Verantwortung der freigebenden Person) |
| V14 | Lizenzprüfung und Updates (Anbieter) | – | nur Felder aus REH-030 | Anbieter, Ferien-Dienst, ggf. SMS-/Passwort-Prüfdienst (Register) |
| V15 | Verstärkte Protokollierung beobachteter Konten | beobachtete Beschäftigte/Tester | jede Anfrage inkl. volle IP, Body/Änderungen verschlüsselt | Inhaber/`watch.read`; 180 Tage; Voraussetzungen REH-020 |

Abnahme: Jede Zeile hat Rechtsgrundlage (REH-009) und Löschfrist (DSG-018); Test: Datenkategorie-Katalog (REH-017) und V-Zeilen sind deckungsgleich (jede Kategorie in mindestens einer Zeile); die Zeile V15 erscheint nur, wenn mindestens ein Konto je beobachtet war oder das Modul aktiv ist.

**REH-036 · TOM-Dokument (Art. 32) und Betriebs-Nachweise** — P0 · Status: Ist (Entwurf; Nachweise offen) · `[JP]`
- Das TOM-Dokument beschreibt, **was die Software tatsächlich tut** (kein Marketing), und enthält die Schutzziele Vertraulichkeit, Integrität, Verfügbarkeit/Belastbarkeit, Überprüfung/Löschung. Software-Maßnahmen (Details in SIC, ANM, REC):

| Schutzziel | Maßnahmen der Software (Kurzfassung) |
|---|---|
| Vertraulichkeit | Rollen- und Rechtekonzept (Need-to-know), Rechte je Anfrage im Backend, fremde Daten 404; Passwort-Hash (scrypt), Zwei-Faktor (TOTP) je Rolle einstellbar, Anmelde-Drosselung (gestaffelt, Konto+IP, IP, Konto), App-Ratenlimit; Sitzungen mit Ablauf, HttpOnly/SameSite/Secure-Cookies, CSRF-Token; Inhaltsverschlüsselung AES-256-GCM mit Datenschlüssel je Objekt und Bindung an Tabelle/Feld/Datensatz; Chats Ende-zu-Ende; Transport TLS 1.2/1.3 mit HSTS; Schutz vor Schadinhalten (CSP ohne externe Ressourcen, Upload-Prüfung, optional Virenscan); Zielprüfung ausgehender Verbindungen; geheime Links und Zugänge nur als Hash, einmalig angezeigt; Datensparsamkeit; Trennung je Schule; Produktivmodus verbietet Demo und Entwicklungs-Passwörter |
| Integrität | Audit-Protokoll jeder schreibenden Aktion (**ohne Inhalte, Ausnahme beobachtete Konten**), Planversionen mit Verlauf und Rückgängig, authentifizierte Verschlüsselung erkennt Manipulation, Vorschau vor Massenänderungen, signierte Webhooks, signierte Lizenzantworten und Updates |
| Verfügbarkeit, Belastbarkeit | tägliche Sicherung (Datenbank und Dateien), Rotation, GPG-Verschlüsselung, Offsite, Test-Restore in Wegwerf-Kopie, Statusseite, `/healthz`, Metriken nur mit Token, Wartungslauf, gehärtete Container (unprivilegiert, schreibgeschütztes Dateisystem, Datenbank nur im internen Netz) |
| Überprüfung, Löschung | Fristlöschung, Schuljahreswechsel mit Abgängern, Auskunft als Export, Löschprotokoll, Abhängigkeits-Audit in der CI |

- **Grenzen werden ehrlich genannt** (Doku = Verhalten): keine Schutzwirkung der Inhaltsverschlüsselung gegen Root-Zugriff auf den laufenden Server (Schlüssel liegt in der Prozessumgebung) und gegen Missbrauch berechtigter Konten; Verlust des Verschlüsselungsschlüssels = Verlust der Inhalte auch in allen Backups, kein Generalschlüssel des Herstellers; Virenscan ohne Scanner nimmt Dateien „ungeprüft“ an (gekennzeichnet) `[Entscheidung Neubau: Kennzeichnung sichtbar]`; Passwortprüfung fail-open; Chat: kompromittierter Server könnte beim Verknüpfen ein Gerät unterschieben (Gegenmaßnahme Fingerabdruck-Vergleich).
- **Betriebsteil (von Schule und Hoster zu belegen), Spalten Maßnahme | Verantwortlich | Nachweis/Datum | Rhythmus**, alle Felder anfangs offen: Zutritt (zertifiziertes Rechenzentrum oder abgeschlossener Serverraum); Zugang Server (SSH nur mit Schlüssel, kein Root-Passwort-Login, nur aus Admin-Netz oder VPN); Zugriff Anwendung (Administrationskonten personengebunden, Zwei-Faktor); Rechteprüfung (jährlich und zum Schuljahreswechsel); Schlüssel (`SM_ENCRYPTION_KEYS` und Sicherungs-Passphrase getrennt von Sicherungen, Tresor); Sicherung (Offsite, Test-Restore); Updates (monatlicher Patchtag); Netz (Firewall eingehend 22 eingeschränkt, 80/tcp, 443/tcp, 443/udp; Altdokumente widersprachen sich bei 443/udp); Personal (Schulung); Datenpanne (Meldeweg bekannt); Verträge (AV vorhanden); Endgeräte (Bildschirmsperre, aktuelle Browser, keine Passwörter im Browser auf Gemeinschaftsgeräten).
Abnahme: Test vergleicht die Maßnahmenliste mit der Konfiguration (z. B. Maßnahme „Zwei-Faktor je Rolle“ nur, wenn `SM_REQUIRE_2FA_ROLES` bzw. Schulmodus existiert); TOM-Export enthält den Abschnitt „Grenzen“ und die Beobachtungs-Ausnahme von „Audit ohne Inhalte“; Betriebstabelle hat leere Nachweisfelder, bis sie gefüllt werden, und die Statusseite zeigt die Anzahl offener Nachweise.

**REH-037 · Prüfrhythmen und Nachweise** — P1 · Status: offen · `[Entscheidung Neubau]`
- Die Statusseite führt Fälligkeiten: monatlich Patchtag und Test-Restore (Wegwerf-Kopie); **vollständiger Probe-Restore mindestens vierteljährlich** (Quellen widersprechen sich: TOM-Betriebsteil „halbjährlich“, Betriebsnachweis O-5 „vierteljährlich“; die strengere Fassung gilt) mit protokolliertem Ergebnis und Datum, einschließlich **Dateiprüfung** (der Restore-Test vom 17.10. prüfte nur 5 Dateien); jährlich Rechte-, TOM- und DSFA-Überprüfung; zum Schuljahreswechsel Konten- und Rollenprüfung. Die Software erzwingt die Durchführung nicht; sie zeigt Fälligkeit und letzten Nachweis.
Abnahme: Kein Probe-Restore-Nachweis älter als 3 Monate → Statusseite „Warnung: Probe-Restore überfällig“; Nachweis mit Datum und Ergebnis eintragen → Warnung entfällt; Restore-Prüfung meldet die Zahl geprüfter Dateien und die Gesamtzahl.

**REH-038 · Datenschutz-Folgenabschätzung (Art. 35): Hilfe und Schwellwertanalyse** — P0 · Status: offen · `[JP]`
- Die DSFA liegt in der Verantwortung der Schule bzw. des Schulträgers. Das Produkt liefert (a) einen **Assistenten „Schwellwertanalyse“** (Fragenkatalog in Abschnitt 15.11), der Datum, Antworten, Ergebnis („DSFA erforderlich/nicht erforderlich“), Begründung und Stellungnahme der bzw. des Datenschutzbeauftragten speichert und im Verzeichnis (REH-034) anzeigt; (b) die Bausteine: Rollen- und Rechtekonzept, Verschlüsselung (TOM), Löschkonzept, Audit-Protokoll; (c) den Hinweis auf die Muss-Liste der Landesdatenschutzbehörde und die Vorabkonsultation (Art. 36) bei hohem Restrisiko. Auslöser laut Quellen: Daten Minderjähriger in großer Zahl (mehr als 2500 Schüler/innen), Gesundheitsbezug (Krankmeldungen, Atteste) und mittelbare besondere Kategorien (Religionskurse, Förderbedarf), Kommunikationsfunktionen mit Meldeverfahren (Chats), Auswertung von Leistungs- und Fehlzeitdaten; Bewertung von Leistungen (Noten, Fehlzeiten) gilt in Merkblättern von Aufsichtsbehörden als hohes Risiko `[unsicher]`. **Das Ergebnis wird auch dokumentiert, wenn keine DSFA nötig ist.** Wiederholung bei wesentlichen Änderungen (z. B. Aktivierung der Beobachtung, Push, Übersetzungsdienst).
Abnahme: Assistent ohne Abschluss → Einrichtungsschritt „Datenschutz“ nicht erledigt; Abschluss speichert Ergebnis mit Datum und Konto; Aktivierung eines Moduls aus der Liste „DSFA-relevant“ nach dem Abschluss → Hinweis „Schwellwertanalyse prüfen“; Zugriff nur mit `privacy.manage`.

**REH-039 · Datenschutzpaket im Betreiber-Paket** — P0 · Status: Ist (Entwürfe; juristische Prüfung offen) · `[JP]`
- Inhalt (Hilfe → „Datenschutz-Vorlagen“, nur für Datenschutz-Zuständige; „Betrieb und Einrichtung“ nur Administration; „Schule einrichten“ für Inhaber des Rechts `settings.edit`; **nicht** sichtbar für Lehrkräfte, Eltern, Schüler/innen, Zuschauer, Hausmeister, Sekretariat): Verzeichnis-Eintrag, TOM-Beschreibung, Hinweise Eltern/Schüler/Lehrkräfte, Datenschutzerklärung, Impressum, Erklärung zur Barrierefreiheit, Nutzungsordnung, Muster-AV-Vertrag mit Unterauftragnehmerliste, Löschkonzept (aus der Konfiguration), Schwellwertanalyse, Meldevorlagen, Kontaktliste. **Reihenfolge für die Schule:** (1) Datenschutzbeauftragte/n einbinden, (2) Verzeichnis ausfüllen und übernehmen, (3) AV-Verträge abschließen, (4) DSFA-Schwellwertanalyse durchführen und ablegen, (5) TOMs mit der tatsächlichen Installation abgleichen, (6) Hinweise anpassen, verteilen und den Erhalt nachweisen, soweit Landesrecht es verlangt, (7) Personal schulen (Passwörter, Zwei-Faktor, Zugangsbriefe, Exporte), (8) jährlich zum Schuljahreswechsel prüfen. Die Texte enthalten keine Heimserver-, Domain- oder Personenangaben (Test bei jedem Lauf).
Abnahme: Lehrkraft, Schüler, Eltern, Sekretariat öffnen die Betreiber-Hilfe → 404/Menüpunkt fehlt; Administration sieht „Betrieb und Einrichtung“; Datenschutz-Zuständige (`privacy.manage`) sehen „Datenschutz-Vorlagen“; Test sucht in allen Paket-Texten nach Domain-, IP-, Personen- und Firmenangaben → 0 Treffer; die acht Schritte sind im Einrichtungsassistenten als Checkliste abhakbar.

---

## 7. Datenpanne (Art. 33, 34): Prozess, Fristen, Vorlagen

**Grundfrist:** Meldung an die Aufsichtsbehörde **unverzüglich, möglichst binnen 72 Stunden ab Kenntnis**; Verspätung nur mit Begründung; Meldung entfällt nur bei voraussichtlich fehlendem Risiko (mit dokumentierter Begründung); bei hohem Risiko zusätzlich Benachrichtigung der Betroffenen; **jede** Panne wird dokumentiert, auch wenn nicht meldepflichtig (Art. 33 Abs. 5). Konkrete Schul-Bußgelder wurden nicht gefunden; öffentliche Schulen werden in Deutschland nach Quellenlage kaum mit Geldbußen belegt, Schadensersatz (Art. 82) und Aufsichtsmaßnahmen bleiben `[unsicher]` `[JP]`.

**DSG-033 · Vorfallsakte mit 72-Stunden-Uhr** — P0 · Status: offen (Altsystem: Vorlage im Sicherheitskonzept, keine Funktion)
- Tabelle `incidents` (nur für `privacy.manage`): `kenntnis_am` (Pflicht, Datum/Uhrzeit), `kenntnis_quelle` (`eigene_feststellung`, `meldung_auftragsverarbeiter`, `meldung_dritter`, `betroffene`), `vorfall_am` (geschätzt), `art` (`vertraulichkeit`, `integritaet`, `verfuegbarkeit`), `beschreibung` (verschlüsselt, **ohne Personendaten**), `betroffene_kategorien` (Schüler/innen, Minderjährige, Eltern, Beschäftigte), `anzahl_personen` (ca.), `datenkategorien` (inkl. Art. 9), `anzahl_datensaetze` (ca.), `risiko` (`gering`, `mittel`, `hoch`) mit Begründung, `meldung_aufsicht` (`ja`, `nein_kein_risiko`) mit Begründung, `gemeldet_am`, `aktenzeichen`, `betroffene_benachrichtigt` (ja/nein, am, Weg), `massnahmen` (Liste mit Uhrzeit), `ursache`, `dauerhafte_massnahmen`, `abgeschlossen_am`, `abgeschlossen_durch`. **Countdown:** `frist_ende = kenntnis_am + 72 Stunden`, Anzeige in Stunden und Minuten; nach Ablauf ist `verspaetung_begruendung` Pflicht; Meldungen in Stufen (Art. 33 Abs. 4) sind als Nachträge erlaubt. Aufbewahrung 1095 Tage nach Abschluss `[Vorschlag Schreiber]`. Läuft auch bei Lizenzsperre (REH-031).
Abnahme: Akte ohne `kenntnis_am` → 422; Akte mit Kenntnis vor 71 Stunden zeigt „noch 1 Stunde“ und löst eine Benachrichtigung an Schulleitung und Administration aus; nach 73 Stunden ohne `gemeldet_am` und ohne Entscheidung „kein Risiko“ → Akte rot, Abschluss nur mit Verspätungsbegründung; `beschreibung` ist in der Datenbank ein Chiffrat; Konto ohne `privacy.manage` → 403.

**DSG-034 · Eindämmung und Beweissicherung (Funktionen)** — P0 · Status: Ist
- Vorhanden und in der Vorfallsakte verlinkt: Konto deaktivieren bzw. *alle Sitzungen beenden* (*Benutzer → Sitzungen*); Passwort zurücksetzen (Oberfläche, `POST /users/{id}/reset-password`, CLI `reset-password --username`); CLI `disable-2fa` und `unlock`; bei breitem Verdacht `SM_SECRET_KEY` neu setzen (meldet alle ab, macht API-Tokens ungültig); iCal-Links betroffener Nutzer neu erzeugen; Dienst offline schalten (Reverse-Proxy stoppen); Beweise sichern **vor** Bereinigung: Container-Logs exportieren, Sicherung mit Label (`make backup`), Audit-Export (`GET /api/v1/audit?since=…`), Snapshot des Hosters; Grundsatz: Ruhe bewahren, nichts vorschnell löschen, alles mit Uhrzeit protokollieren; alle Geheimnisse rotieren (`rotate-keys`; alte Backups bleiben mit altem Schlüssel lesbar).
Abnahme: Konto mit Verdacht → „Sitzungen beenden“ beendet alle Sitzungen und macht persönliche API-Tokens des Kontos ungültig (Pentest-Befund P3-02/P3-03 gilt als Pflicht); Audit-Export mit `since` liefert nur Einträge ab dem Zeitpunkt; Sicherung mit Label `vorfall-<Datum>` wird angelegt und in der Akte vermerkt.

**DSG-035 · Risikobewertung und Meldeentscheidung** — P0 · Status: offen · `[JP]`
- Die Akte führt durch drei Fragen: (1) Sind personenbezogene Daten betroffen und gelangten sie an Unbefugte, gingen verloren oder wurden verändert? (2) Risiko für Rechte und Freiheiten: Minderjährige, Art.-9-Daten (Gesundheit, Förderung, Religion mittelbar), Menge, Identifizierbarkeit, Verschlüsselungszustand (Chiffrat **ohne** kompromittierten Schlüssel mindert das Risiko; „verschlüsselt“ allein ersetzt die Prüfung nicht). (3) Folge: kein Risiko → Dokumentation mit Begründung; Risiko → Meldung binnen 72 Stunden an die Aufsichtsbehörde (Meldeformular der Landesbehörde ist maßgeblich; die Vorlage REH-040 bereitet die Angaben vor); hohes Risiko → zusätzlich Betroffene unverzüglich (Art. 34; Ausnahmen Abs. 3 `[Eigenwissen]`); Schulaufsicht und Schulträger nach Landesvorgabe. Verantwortlich: Schulleitung mit Datenschutzbeauftragter/m.
Abnahme: Risiko „hoch“ gewählt → Akte verlangt Eintrag zur Benachrichtigung der Betroffenen oder Begründung der Ausnahme; Risiko „gering“ ohne Begründung → 422; Aufsichtsbehörde fehlt in den Stammdaten → Akte zeigt Warnung „Aufsichtsbehörde nicht hinterlegt“.

**DSG-036 · Benachrichtigung der Betroffenen (Art. 34)** — P0 · Status: offen
- Funktion *Betroffene benachrichtigen* aus der Akte: Auswahl betroffener Konten/Klassen/Eltern, Mitteilung über Postfach bzw. E-Mail mit der Vorlage aus REH-040 (Sie-Form, klare einfache Sprache, ohne Gesundheitsdaten, ohne Namen Dritter), Nachweis (Anzahl, Zeitpunkt, Weg) in der Akte; für Familien ohne Konto ein **Serienbrief als PDF** (barrierefrei, REH-068); bei Ausfall des Mailsystems alternative Kanäle (Aushang, öffentliche Bekanntmachung nach Art. 34 Abs. 3 lit. c `[Eigenwissen]`). Pflicht-Mails tragen weder Abmeldelink noch List-Unsubscribe-Kopf.
Abnahme: Versand an 30 Konten → Akte zeigt „30 benachrichtigt am …“; Mailtext enthält kein Wort aus Krankheits- oder Notenfeldern; Serienbrief-PDF für Familien ohne Konto wird erzeugt; Nachricht an ein Konto, das die Zustellung an die Person selbst eingestellt hat (volljährig, `self`), geht nicht an die Eltern.

**DSG-037 · Erkennung und Alarm bei Massenzugriffen** — P1 · Status: offen (Audit-Funde P4 mittel, P1-04, P3)
- Auffälligkeiten erzeugen eine Benachrichtigung an Administration und Schulleitung und einen Vorschlag für eine Vorfallsakte: viele Abrufe fremder IDs durch ein Konto (404-Zähler), Massen-Export oder -Abruf von Schülerdaten, Anmeldung eines Administrationskontos von neuer Adresse, Fehlversuche über viele Konten von einer Adresse (Passwort-Spraying), Wellen von Passwort-Reset-Anforderungen. **Pflicht-Audit** für Exporte aller Formate, Anmeldefehler, Fremdabrufe von Dateien, Beobachtungs-Lesezugriffe und Erzeugung von Auskünften. Schwellenwerte einstellbar `[unklar: Standardwerte nicht in den Quellen]`; Alarme enthalten keine Personendaten.
Abnahme: Konto ruft 200 fremde Schüler-IDs ab (Testschwelle 50) → Alarm an Administration; Export der Schülerliste → Audit-Eintrag mit Konto, Zeit, Zeilenzahl, ohne Inhalt; Alarmtext enthält nur Konto-ID und Zähler.

**DSG-038 · Sonderfälle als Handlungsanleitung** — P1 · Status: Ist (Hilfeseiten)
- Hilfeseiten im Betreiber-Paket mit Kontaktliste (ausfüllbar, druckbar, offline aufzubewahren) und Playbooks: **Ransomware/kompromittierter Server** (Server nicht weiterverwenden, frisches System, neue Geheimnisse, Backup aus der versionierten Offsite-Kopie von vor dem Befall nach Test-Restore); **Zugangsbriefe falsch verteilt** (betroffene Konten zurücksetzen, neue Briefe ausgeben, Dokumentation, Meldung nach Risikobewertung); **Gerät mit aktiver Sitzung verloren** (Sitzungen beenden, Passwort ändern, ggf. Zwei-Faktor neu); **Schlüsselkompromittierung** (Rotation, Vorfall, alte Backups); **Fehlversand von Mails/Dateien**; **Ausscheiden von Beschäftigten mit Datenzugang** (Offboarding sofort, Export-Protokoll prüfen; Insider-Abfluss ist ein belegtes Muster).
Abnahme: Hilfeseite „Datenpanne“ ist für Administration und Datenschutz-Zuständige erreichbar; Kontaktliste lässt sich als druckbare Seite ausgeben; jeder Playbook-Schritt nennt die zugehörige Funktion (z. B. „Sitzungen beenden“) mit Link in die Oberfläche.

**REH-040 · Vorlagen für Meldung, Benachrichtigung und Vorfallsbericht** — P0 · Status: offen (Vorfallsbericht und Kontaktliste Ist) · `[JP]`
- Die Vorlagen stehen in Abschnitt 15.8 bis 15.10: Meldung an die Aufsichtsbehörde mit den Angaben des Art. 33 Abs. 3, Mitteilung an Betroffene nach Art. 34, Vorfallsbericht (Kurzform mit Unterschrift der Schulleitung), Kontaktliste. Aus einer Vorfallsakte lassen sich Meldung und Bericht als Text/PDF vorbefüllen; das **Meldeformular der Landesbehörde bleibt maßgeblich** (die Software liefert die Angaben zum Übertragen).
Abnahme: Akte „Zugangsbriefe falsch verteilt“ → Export „Meldung vorbereiten“ enthält alle Felder der Vorlage (Verantwortlicher, Datenschutzbeauftragte/r, Zeitpunkte, Art, Kategorien und Zahl der Betroffenen und Datensätze, Folgen, Maßnahmen); fehlendes Feld → Platzhalter `[…]` und Warnung nach REH-044; Vorlagen tragen die Kennzeichnung nach REH-006.

---

## 8. Impressum, Datenschutzerklärung und Hinweistexte: Sache der Schule

**Betreiberentscheidung (17.10.2026):** Impressum und Datenschutzerklärung gehören der **Schule**, nicht dem Anbieter; die Schule trägt sie beim Einrichten selbst ein; keine Firmendaten des Anbieters in den Texten; Mustertexte mit Platzhaltern; der Anbieter steht nur neutral als „Auftragsverarbeiter (siehe AV-Vertrag)“. Ungeklärt blieb im Altbestand, wie die **Verantwortung** zwischen Anbieter und Schule im Einzelnen verteilt ist `[unklar]` `[JP]`; die Spezifikation legt fest: Verantwortlich für Inhalt und Aktualität ist die Schule, der Anbieter schuldet Mustertexte, technische Bereitstellung und Konsistenz mit dem Verhalten der Software (REH-046).

**REH-041 · Rechtstexte werden von der Schule gepflegt** — P0 · Status: Ist · `[JP]`
- Die Schule trägt Impressum und Datenschutzerklärung selbst ein: in *Einstellungen* (Recht `settings.edit`) oder im Einrichtungsschritt „Rechtstexte“. Je Text entweder **eigener Text** oder **externer Link** (nur `http`/`https`). Textlänge: `[unklar: Altsystem ohne dokumentierte Grenze]` Vorschlag 50 000 Zeichen `[Entscheidung Neubau]`. Änderungen im Audit `setup.legal` (ohne Inhalte). Der Einrichtungsschritt „Rechtstexte“ ist optional im Assistenten, gilt aber als nicht erledigt, solange ein Pflichttext fehlt oder Platzhalter offen sind.
Abnahme: Konto ohne `settings.edit` speichert einen Rechtstext → 403; Text mit 60 000 Zeichen → 422; Link `javascript:alert(1)` → 422; Änderung → Audit `setup.legal` mit Konto und Zeit, ohne Textinhalt; Wechsel von Text zu Link → öffentliche Seite leitet nicht um, sondern zeigt den Link als Verweis.

**REH-042 · Öffentliche Seiten und Verlinkung** — P0 · Status: Ist (Routen im Neubau getrennt)
- Seiten **ohne Anmeldung**: `/impressum`, `/datenschutz` (Datenschutzerklärung), `/barrierefreiheit` (Erklärung, REH-066). Links unten auf der Anmeldeseite und im Profilmenü (zusätzlich in der Fußzeile jeder Seite `[Entscheidung Neubau]`). Fehlt ein Text: Anzeige **„Noch nicht hinterlegt“**, in der Verwaltung eine Warnung und ein Warnpunkt auf der Betriebsseite („Lizenz, Impressum, Datenschutztexte“ in der Statusseite).
- **Routenkonflikt im Altbestand:** `/datenschutz` war dreifach belegt (öffentliche Erklärung, Verwaltungsseite mit `privacy.manage`, Hinweise ohne Recht). Neubau `[Entscheidung Neubau]`: öffentlich `/datenschutz`; Verwaltung `/datenschutz-verwaltung` (Menü *Datenschutz*, `privacy.manage`); Hinweistexte für Angemeldete `/hilfe/datenschutz`. Alte Adressen leiten um.
Abnahme: Ohne Anmeldung `/impressum` → 200 mit Text oder „Noch nicht hinterlegt“; Anmeldeseite enthält beide Links, Profilmenü ebenfalls; Statusseite zeigt Warnung bei fehlendem Text; `/datenschutz` ohne Anmeldung liefert nie die Verwaltungsseite; `/datenschutz-verwaltung` ohne `privacy.manage` → 403.

**REH-043 · Anzeige nur als reiner Text** — P0 · Status: Ist
- Eingetragene Rechtstexte werden **nie als HTML** eingefügt, nur als Absätze und Links; Links nur mit `http`/`https`, `rel="noopener noreferrer"`. Keine Skripte, kein Einbetten.
Abnahme: Text `<script>x()</script><b>fett</b>` gespeichert → öffentliche Seite zeigt die Zeichen wörtlich, DOM enthält weder `script` noch `b`; Link mit Schema `data:` → nicht klickbar.

**REH-044 · Mustertexte mit Platzhaltern und Warnung bei offenen Platzhaltern** — P0 · Status: Ist
- Der Knopf *Mustertext einfügen* (Recht `settings.edit`) liefert den Mustertext aus Abschnitt 15 mit **Platzhaltern in eckigen Klammern** `[…]`. Solange irgendeine eckige Klammer mit Inhalt im Text steht: **Warnung im Editor** (Anzahl und Liste der offenen Platzhalter), **Warnpunkt auf der Betriebsseite**, Einrichtungsschritt „Rechtstexte“ **nicht erledigt**. Die **Hinweiszeile am Textanfang** („Entwurf … diese Zeile löschen, sobald geprüft“) ist selbst ein Platzhalter und bleibt als Warnung, bis die Schule sie löscht. Der öffentliche Text bleibt sichtbar (die Schule entscheidet über die Veröffentlichung); die Warnung erscheint nur in der Verwaltung. `{{…}}` sind keine Platzhalter der Schule.
Abnahme: Mustertext einfügen → Editor zeigt „Offene Platzhalter: N“ mit Liste; alle `[…]` ausfüllen und Hinweiszeile löschen → Warnung entfällt, Schritt „erledigt“; Betriebsseite zeigt Warnpunkt, solange ein Platzhalter existiert; ein Text mit nur einem `[Datum]` → Warnung (1); Test zählt `[…]` im Mustertext und stellt sicher, dass kein `{{…}}` als Warnung gezählt wird.

**REH-045 · Kein Anbietername, keine Anbieterdaten; Produktname nur über eine Variable** — P0 · Status: Ist
- Mustertexte enthalten **keine** Firmendaten, keine Kontaktdaten, keine Domain des Anbieters (Betreiber: „da ist jetzt die Firma von mir drin … sondern das sind dann Informationen, die sollten dann die Schulen anpassen“). Der Produktname erscheint nur als `{{produktname}}` aus einer einzigen Konfigurationsstelle (Seitentitel, Wortmarke, PDF-Metadaten, Mail-Köpfe, User-Agents, Kalender, Rechnungen holen ihn von dort; Altfehler: fest eingetippte Namen). Beispielpersonen in sichtbaren Platzhaltern sind neutral („Frau Muster“).
Abnahme: Produktname in der Konfiguration ändern → Mustertexte, PDF-Metadaten, Mail-Köpfe und Seitentitel zeigen den neuen Namen; Suchlauf nach dem alten Namen in ausgelieferten Texten → 0 Treffer; Suchlauf nach Anbieterbezeichnern in Mustertexten → 0 Treffer (REH-001).

**REH-046 · Rechtstexte aus der Konfiguration ableiten, Konsistenz-Test** — P0 · Status: offen (Audit P4-01, P4-02) · `[JP]`
- Datenschutzerklärung, Verzeichnis und Hinweistexte müssen das **tatsächliche Verhalten** beschreiben. Der Generator setzt Werte ein: `{{produktname}}`, `{{loeschfristen_tabelle}}` (aus DSG-018), `{{protokoll_fristen}}` (Audit 365, API 90, Beobachtung 180 Tage u. a., DSG-030), `{{ip_text}}` (gekürzt/voll gemäß `audit_ip_mode`), `{{av_liste}}`, `{{drittland_text}}` (REH-027), `{{sso_text}}` (nur wenn ein Anmeldedienst aktiv ist, REH-058), `{{cookie_tabelle}}` (REH-053), `{{passwort_mindestlaenge_schueler}}`/`{{…_personal}}`, `{{backup_text}}` (höchstens 12 Monate), `{{aufsichtsbehoerde}}`, `{{dsb}}`. Ein **Konsistenz-Test** vergleicht Text und Konfiguration; eine falsche Datenschutzinformation kann selbst abgemahnt werden (Audit). Bekannte Altabweichungen, die der Neubau nicht wiederholen darf: Passwortlänge für Schüler/innen 10 im Hinweis, 8 in der App; „IP-Adresse wird gekürzt“ bei voller Speicherung; Konto-Löschfrist „3 Monate“ gegen „zuletzt, nach 30 Tagen“; Nachrichten-Frist „365 Tage“ gegen „30 Tage nach Austritt“; Drittland „keine“ trotz optionaler Passwort-Prüfung; „keine fremden Skripte“ trotz Anmeldedienst-Skripten.
Abnahme: Test A: `audit_ip_mode=voll` → Text sagt „vollständig“; `gekuerzt` → „gekürzt (IPv4 /24, IPv6 /48)“. Test B: Mindestlänge Schüler in der Konfiguration 8 → Hinweis nennt 8. Test C: kein Anmeldedienst aktiv → Text enthält keinen SSO-Absatz. Test D: `messaging_retention_days` 200 → Text nennt 200. Jede Abweichung lässt den Test fehlschlagen.

**REH-047 · Hinweise nach Art. 13/14 für Eltern, Schüler/innen, Lehrkräfte** — P0 · Status: Ist (Entwürfe, Lücken) · `[JP]`
- Drei Hinweistexte (Muster in 15.3 bis 15.5), durchgehend **Sie** (auch Schüler/innen), Schülertext in **einfacher Sprache** mit Fragen als Überschriften (Art. 12 Abs. 1, ErwG 38). Pflichtinhalt: Verantwortliche/r, Datenschutzbeauftragte/r, Zwecke, Daten, besonders geschützte Daten (Gesundheitsdaten verschlüsselt, Sichtbarkeit), Rechtsgrundlagen, Empfänger und Auftragsverarbeiter, Drittland, Speicherdauer (aus DSG-018), Rechte (Art. 15–21) und Ausübung, Beschwerderecht, Bereitstellung (Pflicht/freiwillig), Mithilfe (Passwort, Zwei-Faktor, Abmelden). **Gegenüber den Altentwürfen zu ergänzen:** Chats (Ende-zu-Ende, Kopien auf Geräten bleiben, keine Wiederherstellung ohne Code oder Passwort), Elternfreigabe ab 18 (Bereiche, Zustellweg), Beobachtungs-Ausnahme von „Audit ohne Inhalte“ und Information über verstärkte Protokollierung (Lehrkräfte), Sicht der Klassenleitung auf Atteste und Gründe, Profilanträge (Lehrkräfte), Kursraum-Papierkorb (30 Tage), Telefonnummer/SMS-Dienst als Empfänger, optionale Passwort-Prüfung (Drittland), Lizenzserver.
Abnahme: Die drei Texte liegen als Mustertext vor und enthalten jeden Pflichtinhalt (Checkliste im Test: Schlüsselwörter/Abschnitte vorhanden); der Schülertext hat keinen Satz mit mehr als 25 Wörtern `[Vorschlag Schreiber]`; Text enthält keine „du“-Formen (Test); Chat-Absatz nennt „keine Wiederherstellung ohne Code oder Passwort“.

**REH-048 · Bereitstellung und Nachweis der Kenntnisnahme** — P1 · Status: offen · `[JP]`
- Die Hinweise sind für Angemeldete unter `/hilfe/datenschutz` erreichbar; bei der ersten Anmeldung und nach jeder Textänderung (Textversion) erscheint ein Banner „Datenschutzhinweise“; eine **Lesebestätigung** (Datum, Textversion) wird nur gespeichert, **soweit Landesrecht den Nachweis verlangt** (Schulschalter `hinweis_nachweis`, Standard aus). Für Familien ohne Konto: Serienbrief als PDF (barrierefrei).
Abnahme: Textversion 2 veröffentlicht → Banner erscheint erneut; Schalter an → Bestätigung speichert Datum und Version; Schalter aus → es wird nichts gespeichert; Serienbrief-PDF für Familien ohne Konto verfügbar.

**REH-049 · Nutzungsordnung (Vorlage)** — P1 · Status: offen (Quelle: Backlog B-51) · `[JP]`
- Vorlage (Gliederung in 15.12) für Schüler/innen und Lehrkräfte: Zugang und Passwort, Zwei-Faktor, gemeinsam genutzte Geräte, Verbot der Weitergabe, Umgang mit Exporten und Namenslisten, Nachrichten und Chats (Melden), Uploads (Rechte Dritter, REH-074), Gesundheitsdaten nur im vorgesehenen Bereich, Meldung von Datenpannen, Folgen von Verstößen. Für Beschäftigte ist die Beteiligung des Personalrats zu prüfen (REH-018).
Abnahme: Vorlage liegt im Betreiber-Paket mit Kennzeichnung nach REH-006; Gliederung enthält alle neun Punkte; Test auf „du“-Formen negativ.

**REH-050 · Änderungsverlauf der Rechtstexte** — P1 · Status: Ist (Versionierung offen)
- Jede Änderung im Audit (`setup.legal`); jede Rechtsseite zeigt `Stand: [Datum]` (Pflichtfeld der Schule); die Software führt eine Textversion, die bei Änderung steigt (für REH-048); frühere Fassungen bleiben für Auskunftsfälle 3 Jahre abrufbar (Verwaltung) `[Vorschlag Schreiber]`.
Abnahme: Zweimal ändern → Audit enthält zwei Einträge, Textversion 3; frühere Fassung 2 ist in der Verwaltung lesbar; Seite ohne Stand-Datum → Warnung.

**REH-051 · Erreichbarkeit der Rechtsseiten** — P1 · Status: offen
- Die öffentlichen Rechtsseiten setzen **keine Cookies**, laden **keine** externen Ressourcen, bleiben bei Lizenzsperre und im Demo-Betrieb erreichbar, sind barrierefrei (REH-063) und druckbar (Druckstil), haben stabile Adressen.
Abnahme: Aufruf von `/impressum` ohne Cookies liefert keinen `Set-Cookie`-Kopf; Lizenz gesperrt → 200; Browser-Test mit Netzwerkprotokoll: alle Anfragen same-origin; Druckansicht ohne Navigation.

**REH-052 · Anbieter-eigene Seiten** — P2 · Status: offen · `[JP]`
- Anbieter-Portal und Lizenzserver-Seiten sind Angebote des Anbieters und brauchen ein **eigenes** Impressum und eine eigene Datenschutzerklärung des Anbieters; sie sind nicht Teil der Schul-App und werden nicht mit Schuldaten vermischt (Zahlungsdaten der Schule: Anbieter ist Verantwortlicher für Vertragsdaten, Zahlungsdienste Stripe/GoCardless vorbereitet, inaktiv).
Abnahme: Portal-Fußzeile verlinkt Impressum/Datenschutz des Anbieters; die Schul-App enthält keinen dieser Links zum Anbieter; Test: Mustertexte der Schule nennen den Anbieter nicht.

---

## 9. Cookies, Endgerätezugriff, Schriften, Drittanbieter

Rechtsrahmen: Speichern und Auslesen auf dem Endgerät braucht Einwilligung, außer die Maßnahme ist technisch erforderlich oder **unbedingt erforderlich, damit ein vom Nutzer ausdrücklich gewünschter Dienst bereitgestellt werden kann** (§ 25 TDDDG, früher TTDSG `[Eigenwissen]` `[JP]`). Grundsatz des Produkts: **nur technisch notwendige Mittel, keine Tracker, kein Einwilligungsbanner nötig**.

**REH-053 · Cookie-Inventar: nur technisch notwendige Cookies** — P0 · Status: Ist · `[JP]`
- Zulässige Cookies (Inventar wird in der Datenschutzerklärung erzeugt, REH-046); keine Passwörter oder Klartext-Adressen in Cookies:

| Cookie | Inhalt | HttpOnly | SameSite | Secure | Laufzeit | Zweck |
|---|---|---|---|---|---|---|
| `sm_session` | Sitzungs-Token (nur als HMAC in der Datenbank) | ja | Lax | ja bei HTTPS bzw. `SM_COOKIE_SECURE=1` | höchstens 30 Tage (`SM_SESSION_MAX_DAYS`), Leerlauf Schüler/Eltern 7 Tage, Personal 12 Stunden (einstellbar 15 Minuten bis 7 Tage) | Anmeldung |
| `sm_sessions` | Tokens weiterer Konten (höchstens 4) | ja | Lax | wie oben | 30 Tage | Kontowechsel im selben Browser |
| `sm_sso_hint` | Kennung des zuletzt genutzten Anbieters | nein | Lax | wie `SM_COOKIE_SECURE` | 90 Tage | Komfort, nur mit REH-057 |
| `sm_sso_who` | verschlüsselte E-Mail für stilles SSO | ja | Lax | wie `SM_COOKIE_SECURE` | 90 Tage | Komfort, nur mit REH-057 |
| `sm_sso_<Anbieter>` | verschlüsselter Zustand (state, nonce) | ja | Lax (Apple per Formular: None) | ja | 600 Sekunden, einmal verwendbar | Anmeldung über Anbieter |
| Lastverteiler-Cookie | Bindung an einen Server | nach Proxy | – | ja | Sitzung | nur bei mehreren Servern je Schule |

Abnahme: Browser-Test: Anmeldung, 20 Seiten je Rolle, Abmeldung → es entstehen nur Cookies der Tabelle; jeder trägt die Attribute der Tabelle; Abmelden löscht `sm_session`, `sm_sso_hint`, `sm_sso_who`; kein Cookie-Banner wird gezeigt; Datenschutzerklärung enthält exakt diese Cookies (Konsistenz-Test REH-046).

**REH-054 · Keine Tracker, Analyse, Session-Replay, Werbung, Telemetrie** — P0 · Status: Ist · `[JP]`
- Verboten: Analyse- und Werbe-Tracker, Session-Replay (auch in Fehlerberichts-Diensten), Social-Plugins, Fremd-Chat-Widgets, Marketing-Mails. Keine Telemetrie; gesendet wird nur, was die Person selbst abschickt (Feedback-Knopf mit Seite und Version). Hintergrund: Abmahn-, Klage- und Vergleichsmuster gegen Schulplattformen und Webangebote (REH-082, Abschnitt 14). **Freigabeprozess für Drittcode:** Registereintrag (REH-026) + CSP-Änderung + Datenschutzerklärung + Schwellwertanalyse (REH-038) vor jeder Aufnahme.
Abnahme: Browser-Test mit Netzwerkprotokoll über 20 Seiten je Rolle → 0 Anfragen an fremde Hosts; Quelltext-Scan nach bekannten Tracker-Bezeichnern → 0 Treffer; Build schlägt fehl bei neuer externer Abhängigkeit zur Laufzeit ohne Registereintrag.

**REH-055 · Schriften und alle Ressourcen lokal** — P0 · Status: Ist · `[JP]`
- Schriften, Symbole, Skripte, Stylesheets, Bilder, Karten, Videos und die API-Dokumentation (Swagger-UI) werden **lokal** ausgeliefert; Content-Security-Policy `default-src 'self'`, `script-src 'self'`, `object-src 'none'`, `frame-ancestors 'none'` (App, Proxy). Hintergrund: Dynamisch geladene Google Fonts führten zu Abmahnwellen (LG München I, 20.01.2022, Az. 3 O 17493/20, 100 EUR Schadensersatz plus Unterlassung `[unsicher]`, Aktenzeichen vor Verwendung prüfen). Externe Links öffnen nur auf Klick.
Abnahme: Build-Test: CSS und HTML enthalten keine URL mit fremdem Host; Browser-Test: alle Anfragen same-origin; Antwortkopf enthält die CSP mit den vier Direktiven.

**REH-056 · Lokale Speicher (Local-/Session-Storage, IndexedDB)** — P1 · Status: Ist (Chat-Schlüssel offen) · `[JP]`
- Erlaubt: Darstellung (hell/dunkel/System), „Hilfetexte immer anzeigen“, zuletzt gewählter Reiter/Filter, ungesendete Entwürfe, Chat-Geräteschlüssel (nicht exportierbarer Schlüssel in IndexedDB). Alle Zugriffe fangen Fehler ab (privater Modus). Bei Abmeldung, 401 und Kontowechsel werden kontobezogene Zwischenspeicher geleert. **Chat-Schlüssel nach Abmeldung (Audit-Fund) `[Entscheidung Neubau]`:** Die Anmeldeseite bietet „Dies ist mein privates Gerät“ (Standard aus); aus → Chat-Schlüssel und lokaler Cache werden beim Abmelden entfernt (Wiederherstellung per Code/Passwort, NAC/SIC).
Abnahme: Abmelden ohne Haken → IndexedDB-Eintrag des Chat-Schlüssels ist weg; mit Haken → bleibt; Kontowechsel → Listen des vorigen Kontos nicht sichtbar; im privaten Fenster ohne Speicher → App startet ohne Fehler.

**REH-057 · Anmelde-Komfort-Cookies nur auf ausdrücklichen Wunsch** — P1 · Status: offen · `[JP]`
- `sm_sso_hint` und `sm_sso_who` (90 Tage) sind kein „unbedingt erforderliches“ Cookie im engen Sinn `[Eigenwissen]`. Sie werden **nur** gesetzt, wenn die Person bei der Anmeldung „Auf diesem Gerät merken“ wählt; Abmelden löscht sie.
Abnahme: Anmeldung über Anbieter ohne Haken → keines der beiden Cookies; mit Haken → beide gesetzt; Abmeldung löscht beide.

**REH-058 · Anmeldedienste (SSO): keine Fremd-Skripte vor dem Klick, Hinweis, DSE-Absatz** — P0 · Status: offen (Audit P4-02) · `[JP]`
- Google-/Microsoft-/Apple-Anmeldung lädt **keine** Fremdskripte beim Seitenaufruf; die Weiterleitung nutzt den Autorisierungs-Code-Fluss mit PKCE und `nonce` ohne Anbieter-Skript, soweit der Anbieter es zulässt `[Entscheidung Neubau]`; wo ein Anbieter-Skript unvermeidbar ist, wird es erst nach Klick geladen. Vor der Weiterleitung steht ein Hinweis „Sie verlassen [Produktname] und melden sich bei [Anbieter] an. Dabei werden Daten an den Anbieter übertragen.“ Die Datenschutzerklärung enthält den Absatz nur bei aktivem Anbieter (REH-046); der Anbieter steht im Register mit Drittland-Kennzeichen (REH-027).
Abnahme: Anmeldeseite mit aktivem Google-Knopf, Netzwerkprotokoll vor dem Klick → keine Anfrage an Google; nach dem Klick → Hinweisdialog, erst nach Bestätigung Weiterleitung; Datenschutzerklärung enthält den SSO-Absatz genau dann, wenn ein Anbieter aktiv ist.

**REH-059 · Mail und SMS: Datensparsamkeit und Abmeldung** — P0 · Status: Ist (Neutralmodus offen)
- Jede automatische Mail trägt `Auto-Submitted: auto-generated`. Rundmails, Postfach-Hinweise und Benachrichtigungs-Mails tragen einen **signierten Abmeldelink** (HMAC, nur für diese Abmeldung) und die Köpfe `List-Unsubscribe`, `List-Unsubscribe-Post: List-Unsubscribe=One-Click`; GET zeigt nur die Bestätigung (Mail-Scanner melden niemanden ab), POST setzt (Audit `notification.unsubscribe`); hat die Schule die Art fest vorgegeben, sagt die Seite das. **Neutralmodus** als Schulvorgabe: Betreff und Text ohne Namen, nur Hinweis und Link. SMS: nur Telefonnummern und Codes, Anbieter im Register, Telefonnummer verschlüsselt. Test-Mails nur an `example.org`; der Test-Postausgang nur auf `localhost` und nie im Produktivmodus.
Abnahme: Rundmail enthält Abmeldelink und beide Köpfe; GET auf den Link ändert nichts, POST schaltet die Art ab; Pflicht-Mails (Passwort zurücksetzen, Sicherheit, Zugangsbrief) ohne Link und ohne Köpfe; Neutralmodus an → Test findet weder Vor- noch Nachnamen im Mailtext; Produktivmodus mit gesetztem Test-Postausgang → Start verweigert.

**REH-060 · Push/App, Übersetzungsdienst, externes Monitoring** — P3 · Status: offen (zurückgestellt) · `[JP]`
- Push-Benachrichtigungen und installierbare App sind vom Betreiber **zurückgestellt** („die app option mus noch nicht mit rein“, 13.10.2026). Falls später: Push-Inhalte ohne Gesundheitsdaten und ohne Namen („Änderung im Plan für morgen“); Web-Push läuft technisch über Dienste der Browserhersteller → Registereintrag (Klärung der Formulierung „kein Drittanbieter“). Übersetzung von Elternbriefen (Backlog B-55) nur als **abschaltbares Modul** mit Dienst als Unterauftragnehmer, EU-Standort, AV-Vertrag, nur Brieftext, keine Namen von Kindern, Hinweis „maschinell übersetzt“. Externes Monitoring nur mit AV-Vertrag.
Abnahme: Standardinstallation enthält weder Push-Abonnement noch Service Worker noch Übersetzungsdienst; Modul „Übersetzung“ ausgeschaltet → keine ausgehende Verbindung; eingeschaltet ohne Registereintrag/AV → Warnung; Push-Testnachricht enthält keinen Namen.

**REH-061 · Ferien-Dienst und weitere ausgehende Abrufe** — P2 · Status: Ist
- Der Ferien-Import ruft öffentliche Ferientermine ab (Quellen OpenHolidays, Nager.Date); die Anfrage enthält nur Land, Region, Jahr und Sprache sowie den Produktnamen (User-Agent), **keine Personendaten** `[unklar: im Altsystem nicht ausdrücklich dokumentiert; Annahme]`. Alle ausgehenden Verbindungen laufen über die zentrale Zielprüfung (SIC) und stehen im Register.
Abnahme: Mitschnitt eines Ferien-Imports enthält keine Konto-, Schüler- oder Lehrerdaten; Dienst steht im Register; Import in der Demo-Instanz gesperrt.

**REH-062 · API-Zugänge und Freigaben an Apps/KIs** — P1 · Status: Ist
- Beim Anlegen eines Zugangs zeigt die Vorschau „Dieser Zugang darf … / Nie …“; **nie freigegeben** werden Gesundheits-, Förder- und Fehlzeitdaten sowie private Nachrichten und Chats. Ein Zugang hat nie mehr Rechte als sein Konto; Standard „Nur lesen“; Schreibzugang schulweit zunächst aus; Ablauf standardmäßig 90 Tage; jeder Aufruf im API-Protokoll (90 Tage); Aufrufe unbekannter Adressen nicht protokolliert. Hinweis im Dialog: Die Weitergabe an Dritte (z. B. KI-Dienste, Drittland) braucht Rechtsgrundlage und gegebenenfalls AV-Vertrag der Schule. `/llms.txt`, `/llms-full.txt`, API-Beschreibung und `robots.txt` enthalten keine Namen oder personenbezogenen Daten.
Abnahme: Zugang mit Bereich „Verzeichnis“ liefert keine Krankmeldungen und keine Chats (404/leer); `/llms.txt` enthält keinen Personennamen (Test); Zugang einer fremden Schule → 401.

---

## 10. Barrierefreiheit (BFSG, BITV 2.0, WCAG 2.2 AA, EN 301 549)

**REH-063 · Geltungsbereich und Konformitätsziel** — P0 · Status: offen (Altsystem: WCAG 2.1 AA) · `[JP]` `[unklar: Geltung]`
- **Ziel: WCAG 2.2 Stufe AA** (EN 301 549, die in der Quelle mit WCAG 2.1 AA geführt wird; WCAG 2.2 ist rückwärtskompatibel und erfüllt 2.1 AA mit `[Eigenwissen]`) für **alle Oberflächen aller Rollen** (Anmeldung, Stundenplan, Vertretung, Monitor, Nachrichten, Kursräume, Verwaltung, Hilfe, Rechtsseiten) sowie für **Dokumente** (REH-068) und Mails. Schulen sind öffentliche Stellen; Barrierefreiheit gilt als Vergabevoraussetzung (Backlog B-44, Marktvergleich). Rechtsgrundlagen: BITV 2.0 bzw. Landesrecht für öffentliche Stellen der Länder; BFSG seit 28.06.2025 für Produkte und Dienstleistungen für Verbraucher, Ausnahme für Kleinstunternehmen bei Dienstleistungen, Bußgeld bis 100 000 EUR (§ 37 BFSG, Sekundärquelle `[unsicher]`). **Ob und in welchem Umfang BFSG, BITV oder Landesgesetz für die Schule als Betreiberin und für den Anbieter gelten, ist offen und je Land zu prüfen** `[unklar]` `[JP]`; die Spezifikation fordert das strengere Ziel unabhängig davon.
Abnahme: Die Prüfmatrix (REH-065) ist auf WCAG 2.2 AA ausgelegt (Kriterienliste enthält 2.4.11, 2.5.7, 2.5.8, 3.3.8); das Rechtsrahmen-Profil (REH-005) hat ein Feld `barrierefreiheit_rechtsgrundlage` (Freitext, leer bis zur Eintragung); die Erklärung (REH-066) nennt das Ziel.

**REH-064 · WCAG-2.2-Kriterien und ihre Umsetzung im Produkt** — P0 · Status: offen (Teil Ist) · `[Eigenwissen]`
- Konkrete Folgen für das Produkt (Kriterium: Umsetzung): **2.4.11 Fokus nicht vollständig verdeckt**: feststehende Kopfzeile, Dialoge und Banner verdecken den Fokus nicht; **2.5.7 Ziehbewegungen**: jede Funktion mit Ziehen hat eine Alternative mit einzelnem Zeigen/Tippen oder Tastatur (Stunden im Raster verschieben per Pfeiltasten und Enter und per Menü „Verschieben nach …“ auf Touch; Datei-Upload mit Auswahlknopf; Regel-Editor), **ein gemeinsames Raster** für alle Tage×Stunden-Ansichten (OBE); **2.5.8 Zielgröße (Minimum)**: mindestens 24×24 CSS-Pixel, Produktvorgabe bleibt 44 px (Hilfe-Beschriftung 37 px); **3.3.8 Barrierefreie Authentifizierung**: Passwort-, Code- und Zwei-Faktor-Felder erlauben Einfügen und Passwortmanager, keine Abtipp-Rätsel; **3.2.6 Konsistente Hilfe**: Hilfe an gleicher Stelle; **3.3.7 Redundante Eingabe**: bereits eingegebene Angaben (z. B. Kind-Auswahl, Formularfelder) werden nicht erneut abgefragt. Aus Version 2.1 bleiben: Kontrast Text 4,5:1, Feldränder und Fokusrahmen 3:1 (Fokusrahmen 2 px), Hilfe bei Hover/Fokus bleibt offen, bis der Zeiger sie verlässt (1.4.13), Status nie nur über Farbe, Fehlertexte am Feld, genau ein Seitentitel und logische Überschriften, 200 % Zoom ohne Verlust, 390 px ohne waagerechtes Scrollen, Bedienung mit Maus, Touch und Tastatur, hell und dunkel, bei „Bewegung reduzieren“ keine Bewegung (Laufband des Monitors als statische Liste).
- Offene Altbefunde, die behoben sein müssen: Stundenplan-Liste nur per Maus, Reiter ohne `aria`-Bezüge, `aria-selected` an Tabellenzeilen, Menü ohne Pfeiltasten (U-79), Modal ohne Fokusfalle.
Abnahme: Raster: Stunde nur mit Tastatur (Pfeiltasten, Enter) verschiebbar; Touch: Menü „Verschieben nach …“; Passwortfeld akzeptiert Einfügen (`paste` nicht unterdrückt); Fokus bleibt bei sticky Kopfzeile sichtbar (Browser-Test mit Tabulator durch jede Seite); Klickziele < 24 px → Test schlägt fehl; Dialog hält den Fokus innen und gibt ihn beim Schließen zurück.

**REH-065 · Prüfnachweis: automatisch und manuell** — P0 · Status: offen (Backlog B-44, R7-D)
- (a) Automatische Prüfung mit axe-core über Playwright für die **20 wichtigsten Seiten je Rolle** ohne schwere Verstöße, Teil der Testsuite und der CI; (b) dokumentierte Prüfung mit **Tastatur und Screenreader** (NVDA, VoiceOver) für Anmeldung, Krankmeldung, Stundenplan, Postfach, Kursraum, Vertretungsplan; (c) Kontraste nach Token-Test in hell und dunkel; (d) 200 % Zoom; (e) 390 px ohne waagerechten Bildlauf. Ergebnis: **Prüfbericht** mit Datum, Version, Prüfer/in, Kriterienliste und Befunden; er ist Grundlage der Erklärung (REH-066). Vollprüfung mindestens jährlich und vor einem Release mit geänderten Oberflächen (für diese Bereiche).
Abnahme: CI-Lauf mit absichtlich eingebauter Verletzung (Bild ohne Alternativtext) → Job rot; Prüfbericht enthält die sechs Abläufe mit Ergebnis je Screenreader; Bericht ohne Datum oder Version ist nicht als Grundlage der Erklärung auswählbar.

**REH-066 · Erklärung zur Barrierefreiheit** — P0 · Status: offen (Audit „mittel“: fehlt)
- Seite `/barrierefreiheit` ohne Anmeldung (REH-042) mit der **Erklärung der Schule** nach dem Muster in 15.6: Geltungsbereich, Stand der Vereinbarkeit (vollständig / teilweise / nicht vereinbar), nicht barrierefreie Bereiche mit Begründung und Alternativen, Datum der Erstellung und der letzten Prüfung, Methode, Rückmeldeweg (REH-067), Hinweis auf das Durchsetzungs- bzw. Schlichtungsverfahren nach Landesrecht `[JP]` `[Eigenwissen]` (Muster nach Durchführungsbeschluss (EU) 2018/1523 `[unsicher]`). Gleiche Platzhalter-Regeln wie REH-044 (Warnung, Einrichtungsschritt). Der Anbieter liefert die Konformitätsangaben aus dem Prüfbericht (REH-065) als `{{konformitaet}}` und `{{nicht_barrierefrei_liste}}`; die Schule trägt Kontakt und Schlichtungsstelle ein.
Abnahme: `/barrierefreiheit` ohne Anmeldung → 200; Mustertext hat offene Platzhalter → Warnung in der Verwaltung; Prüfbericht ausgewählt → `{{konformitaet}}` zeigt das Ergebnis; Link in Anmeldeseite, Profilmenü, Fußzeile.

**REH-067 · Rückmeldeweg für Barrieren** — P0 · Status: offen · `[JP]`
- Öffentliches Formular „Barriere melden“ (Seite, Beschreibung, optional E-Mail) ohne Anmeldung, mit Ratenlimit; die Meldung geht an das hinterlegte Postfach der Zuständigen (Stammdaten REH-002) und erscheint in der Verwaltung; die Antwortfrist wird angezeigt (Vorschlag **30 Tage** `[JP]` `[Vorschlag Schreiber]`); eigene kurze Datenschutzinformation am Formular; Aufbewahrung nach Abschluss 365 Tage `[Vorschlag Schreiber]`. Alternativ steht ein Kontakt per Telefon/Post in der Erklärung.
Abnahme: Meldung ohne Anmeldung → 201, Eintrag in der Verwaltung mit Fristanzeige; mehr als 5 Meldungen in 10 Minuten von einer Adresse → 429; Formular enthält Datenschutzhinweis; Meldung nach 365 Tagen gelöscht.

**REH-068 · Barrierefreie Dokumente und Briefe** — P1 · Status: offen (Backlog B-44 Kriterium 5)
- PDF-Zugangsbriefe, Elternbriefe, Serienbriefe, Auskunfts-PDF, Formular-PDF und Druckansichten werden mit **Struktur-Tags**, Dokumentsprache (Deutsch), Titel, sinnvoller Lesereihenfolge, Alternativtexten und ausreichendem Kontrast erzeugt (Orientierung PDF/UA `[Eigenwissen]`); QR-Codes haben eine Klartext-Alternative. Die HTML-Übersicht der Auskunft ist barrierefrei.
Abnahme: Test prüft erzeugtes PDF auf Dokumenttitel, Sprache `de` und Tag-Struktur (Prüfwerkzeug im CI); Zugangsbrief mit QR-Code enthält den Klartext-Code; HTML-Übersicht besteht den axe-Lauf (REH-065).

**REH-069 · Release-Gate Barrierefreiheit** — P1 · Status: offen · `[Entscheidung Neubau]`
- Kein Release mit schwerem axe-Verstoß (critical/serious) auf den 20 Seiten je Rolle und mit fehlgeschlagenem Kontrast-Token-Test. Die Bedienelemente dürfen nicht „bewusst kaum sichtbar“ sein (Altbefund: Menü-Knopf der Monitor-Ansicht, Entscheidung des Betreibers offen): im Neubau sichtbar, ausreichend kontrastreich, per Tastatur erreichbar, Fokus sichtbar.
Abnahme: Release-Pipeline bricht bei einem „serious“-Befund ab; Monitor-Menü-Knopf hat Kontrast ≥ 3:1 und ist mit Tab erreichbar (Test).

---

## 11. Aufbewahrung von Klassenbuch, Noten, Fehlzeiten (nach Landesrecht konfigurierbar)

**REH-070 · Aufbewahrungsfristen als Profil des Landes** — P0 · Status: offen · `[JP]`
- Fristen für Klassenbuch, Notenbuch, Klausuren, Fehlzeiten und Krankmeldungen kommen aus dem **Fristenprofil des Landes** (DSG-019) und sind je Schule überschreibbar; Wertebereich 1–3650 Tage; jedes Profil nennt Quelle, Stand und Prüfstatus. Einrichtungsfeld `amtliche_unterlagen_ort`: Wo liegen Zeugnislisten, Schülerstammblatt und Zeugnisse (Schulverwaltungsprogramm/Schülerakte)? Leer → Warnung im Schritt „Datenschutz“. Die Software ist **nicht** Aufbewahrungsort für Zeugnislisten und Stammblätter.
Abnahme: Profil NRW → Klassenbuch-Anwesenheit 3650 Tage; Wert 4000 → 422; `amtliche_unterlagen_ort` leer → Warnung; Fristenprofil ohne Quelle/Stand wird beim Laden abgelehnt.

**REH-071 · Schalter „amtliches Klassenbuch“** — P0 · Status: offen · `[JP]`
- Schulvorgabe `klassenbuch_amtlich` (ja/nein, Standard **nein**). **Ja:** das digitale Klassenbuch gilt als amtliches Klassenbuch; die Frist kommt aus dem Profil (NRW-Vorlage 10 Jahre `[unsicher]`); die Anonymisierung der Anwesenheit nach Austritt (365 Tage) entfällt, Datenart geht in den Archiv-Zustand (DSG-025); Änderungen am Klassenbuch sind im Audit nachvollziehbar; Druck/PDF je Woche und Halbjahr für das Archiv (Backlog B-53, offen). **Nein:** Standard 365 Tage nach Austritt anonymisieren. Ob ein digitales Klassenbuch das amtliche Papierklassenbuch ersetzen darf, regelt das Landesrecht `[unklar]` `[JP]`; die Einstellung ist nur durch Schulleitung (`privacy.manage`) änderbar, Audit `privacy.settings`.
Abnahme: Schalter ja + Profil NRW → Test: Anwesenheit einer ausgetretenen Schülerin bleibt nach 400 Tagen, Zugriff nur Sekretariat/Schulleitung; Schalter nein → nach 365 Tagen anonymisiert; Wechsel nein→ja im Audit; Konto ohne Recht → 403.

**REH-072 · Noten, Zeugnisse und Übergabe an das Schulverwaltungsprogramm** — P0 · Status: Ist (Teil offen) · `[JP]`
- Die Software erstellt **keine amtlichen Zeugnisse**. Halbjahres- und Zeugnisnoten werden festgelegt (durch die Lehrkraft, Vorschlag der Software), gesperrt und über den Export (`gradebook.export`: CSV für SchILD, ASV, LUSD; nur bei gesperrten Halbjahresnoten; Schulleitung, Sekretariat) übergeben; die Notenbuch-Standardfrist (180 Tage nach Austritt) dient Einsprüchen und Nachfragen. Noten sind für Schüler/innen und Eltern nach Freigabe sichtbar (Standard „nach Freigabe“, Betreiberentscheidung, fachliche Wahl in NOT); keine Noten in Benachrichtigungen (REH-016).
Abnahme: Export mit nicht gesperrter Halbjahresnote → 409; Export durch Konto ohne `gradebook.export` → 403; Notenbuch einer ausgetretenen Person nach 181 Tagen gelöscht; Schüler sieht eigene Noten erst nach Freigabe.

**REH-073 · Fehlzeiten und Krankmeldungen: Stichtag und Zeugnisbezug** — P0 · Status: Ist (Zeugnisfrist offen) · `[JP]`
- Standard: eine Meldung wird 365 Tage nach dem 31. Juli des Schuljahres gelöscht, in dem sie endet (DSG-018). Das Profil enthält das Feld `zeugnis_fehlzeiten_frist` (Landesrecht, Beginn und Dauer) `[unklar: in den Quellen nicht berücksichtigt]`; die wirksame Frist ist der **größere** Wert aus Standard und Profil. Fehlzeiten, die in ein Zeugnis eingehen, bleiben bis zum Ende dieser Frist erhalten.
Abnahme: Profil mit `zeugnis_fehlzeiten_frist` 800 Tage → Meldung bleibt 800 Tage, Standard 365 wird übertrumpft; ohne Profilwert gilt 365; Test mit fester Uhr.

---

## 12. Urheberrecht, Uploads, Marke und Schutzrechte

**REH-074 · Rechte an hochgeladenen Inhalten** — P1 · Status: offen · `[JP]`
- Jeder Upload-Dialog (Kursraum, Postfach, Abgabe, Formular) trägt einen kurzen Hinweis über die Hilfe-Funktion: „Laden Sie nur Material hoch, für das Sie die Rechte haben.“ Die Nutzungsordnung (REH-049) nennt Urheberrecht und Recht am eigenen Bild. Die Software erwirbt keine Rechte an Inhalten; Abgaben bleiben Inhalte der Schülerin bzw. des Schülers und werden nur zur Bewertung genutzt; Lehrmaterial bleibt beim Verfasser und wird bei Austritt nach Datenart (DSG-023) behandelt. Ob Material nach den Schranken für Unterricht und Lehre (§ 60a UrhG) genutzt werden darf, prüft die Software nicht `[Eigenwissen]` `[JP]`. **Inhalte werden nicht zum Training von KI-Modellen genutzt oder an KI-Dienste übergeben**, außer über einen von einer Person bewusst angelegten API-Zugang (REH-062).
Abnahme: Upload-Dialog zeigt den Hinweis; Test: kein ausgehender Request enthält Inhalte (REH-054); Austritt einer Lehrkraft ändert den Verfasser, nicht den Inhalt (DSG-021).

**REH-075 · Aufnahmen von Personen (Foto, Video, Audio)** — P1 · Status: offen · `[JP]`
- Bild-, Video- und Audio-Uploads in Kurs- und Klassenräumen zeigen den Hinweis „Aufnahmen von Personen nur mit Einwilligung“ (Recht am eigenen Bild, DSGVO). Ist die Einwilligungsverwaltung aktiv (REH-012), zeigt der Dialog zusätzlich die Zahl „Foto-Einwilligungen: N von M erteilt“ (nur Zahlen, keine Namen). Profilbilder sind nicht vorgesehen (Datenkategorie Schüler/innen enthält keine Fotos). Bilder in Chats unterliegen Kontingenten (SIC).
Abnahme: Foto-Upload in Klassenraum → Hinweis sichtbar; mit aktiver Einwilligungsübersicht erscheint die Zahl, ohne Namen; Profil bietet kein Foto-Feld.

**REH-076 · Meldeweg für rechtswidrige oder unzulässige Inhalte** — P2 · Status: offen (Teil Ist: Nachrichten) · `[JP]` `[unsicher]`
- Nachrichten können gemeldet und von berechtigten Personen geprüft werden (Ist, `messages.moderate`). Im Neubau auch Kursraum-Material und Beiträge: Funktion *Melden* an Lehrende bzw. Schulleitung, Ansicht verbergen, Protokoll ohne Inhalt. Ob DSA- oder Plattformpflichten für eine geschlossene Schulplattform gelten, ist nicht anzunehmen, aber zu prüfen `[Eigenwissen]` `[JP]`.
Abnahme: Beitrag melden → Lehrende sehen Meldung; Beitrag lässt sich verbergen und wiederherstellen; Meldegrund im Audit nur als Länge, Inhalt verschlüsselt.

**REH-077 · Lizenzen von Drittcode, Schriften und Beispieldaten** — P1 · Status: offen · `[JP]`
- Abhängigkeiten sind mit Hashes gesperrt (Lock-Dateien); eine **Lizenzliste** (Name, Version, Lizenz) liegt im Betreiber-Paket; die CI meldet Copyleft-Lizenzen (AGPL/GPL) in der ausgelieferten Software zur Freigabe. Von AGPL-Projekten (SchulCloud, SchulIT) werden **nur Ideen, kein Code** übernommen. Schriften, Symbole und Logo haben geklärte Nutzungsrechte; Beispieldaten sind fiktiv.
Abnahme: Lizenzliste wird beim Build erzeugt und enthält jede installierte Abhängigkeit; neue AGPL-Abhängigkeit → CI rot bis zur Freigabe im Register; Suchlauf in den Beispieldaten nach realen Personennamen → keine Treffer (Liste fiktiver Namen).

**REH-078 · Produktname und Marke** — P1 · Status: offen · `[JP]`
- Der Arbeitsname „Schulpuls“ ist **nicht für die Außenwirkung freigegeben**: Die Namensprüfung vom 16.10.2026 fand denselben Namen im Bildungsbereich bei einem anderen Unternehmen (Website, Lern-App, Video-Kanal, Podcast); Verwechslungsgefahr hoch, Abmahnung möglich; Markenregister (DPMA, EUIPO, WIPO) wurden nicht automatisch abgefragt; endgültiger Name offen (Kandidaten laut Prüfung: Schulhafen, Schulfeld, Schulfunke; Schulwelle laut erster Prüfung am aussichtsreichsten; Ausweichnamen nur auf Domains und Websuche geprüft). Der technische Name „schulmanager“ ist dem Namen eines Wettbewerbers sehr ähnlich (Marktreife-Befund) und nicht als sichtbarer Name zu verwenden. Vor externer Nutzung: anwaltliche Markenrecherche, Domain sichern, App-Stores und soziale Netzwerke prüfen. Technisch: sichtbarer Name nur über `{{produktname}}` (REH-045), Austausch ohne Codeänderung.
Abnahme: Release-Checkliste enthält „Namensrecherche geprüft am/durch“; Kundenfreigabe (REH-007) setzt sie voraus; Namenswechsel in der Konfiguration ändert alle sichtbaren Stellen (Test REH-045).

**REH-079 · Eigene Schutzrechte und Lizenzvertrag** — P3 · Status: offen · `[JP]`
- Lizenzvertrag/EULA, Urheberrecht, Kunden-Wasserzeichen und Code-Schutz (kompilierte Bestandteile, gehostetes Angebot) sind Entscheidungen des Anbieters mit Anwalt; Patentierung von Software ist in der EU kaum möglich (Patentanwalt) `[Eigenwissen]`. Die Spezifikation fordert nur: Lizenzprüfung im Echtbetrieb nicht abschaltbar (BET), Lizenzvertrag liegt dem Kunden vor, Prüfdatum nach REH-007.
Abnahme: Lizenzvertrag liegt im Release-Paket mit Prüfdatum; Lizenzprüfung lässt sich im Produktivmodus nicht per Einstellung abschalten (BET-Test).

---

## 13. Demo, Test und Entwicklungsnachweis

**REH-080 · Demo und Test nur mit fiktiven Daten** — P0 · Status: Ist
- Demo- und Testinstanzen enthalten **ausschließlich fiktive Personen** (Beispielschulen); keine echten Namen, Adressen, E-Mail-Adressen, Telefonnummern (nur `example.org`); keine Echtdaten in Code, Tests, Demo oder Dokumentation. Demo-Instanzen sperren schreibende Funktionen außer ausdrücklich freigegebenen (Import, Kompetenz-Import, Webhooks, Aufbewahrungsfristen, Anzeige abwesender Lehrkräfte, Lizenz, Sicherheits- und Benachrichtigungs-Einstellungen). **Demo-Zugänge mit bekannten Passwörtern gibt es nie auf einer Produktivinstanz oder öffentlich erreichbaren Echtinstanz**; im Produktivmodus verweigert der Server „Demo laden“ und „Demo-Zugang ausgeben“ (App, Kommandozeile, Start), und Konten mit Demo-Passwort werden beim Start gesperrt und gemeldet. Testinstanzen laufen nur im Heimnetz/ohne Echtdaten und werden nicht ins Internet freigegeben. Das Demo-Passwort steht nicht im Log.
Abnahme: Produktivmodus mit `SM_LOAD_DEMO=1` → Start bricht ab; „Demo laden“ im Produktivmodus → 403, Daten unverändert; Suchlauf über Demo-Daten nach E-Mail-Adressen außerhalb `example.org` → 0 Treffer; Demo-Instanz: Import → 403.

**REH-081 · Entwicklungsnachweis (Prüfung auch von KI-erzeugtem Code)** — P1 · Status: offen · `[JP]`
- Für jedes Release liegt ein **Prüfbericht** vor (Haftungsnachweis, Organisationspflicht Art. 24, 25, 32 `[Eigenwissen]`): statische Analyse, Abhängigkeits-Audit (`pip-audit`, `npm audit`), Rechte-Matrix- und 404-Tests, dynamischer Test auf einer **isolierten Wegwerf-Instanz** mit Demo-Daten (nie gegen Echtsysteme oder fremde Server; Lastflut nur mit niedrig gesetzter Schwelle), Befundliste mit Status. Befunde von Hilfsmodellen werden am Code nachgeprüft (im Audit vom 17.10. waren 11 von 76 Funden falsch). Dokumentation, dass KI-erzeugter Code geprüft wurde (kein Urteil zu KI-erzeugter Software gefunden; Haftung bleibt bei Anbieter/Betreiber `[unsicher]`). Aufbewahrung `[unklar: Frist]`.
Abnahme: Release-Checkliste hat die Zeile „Prüfbericht vom [Datum]“ mit Anhang; ein Bericht ohne Rechte-Matrix-Test gilt als unvollständig; dynamischer Test gegen eine Adresse außerhalb der Wegwerf-Instanz ist im Testskript nicht möglich (nur `localhost`, sonst Parameter `--ich-darf`).

**REH-082 · Release-Gate Recht (Haftungs-Prüfliste)** — P0 · Status: offen
- Vor jedem Release geht die Freigebende die **Prüfliste „Haftungsmuster“ (Abschnitt 14)** durch; je Zeile ein Nachweis (Testname/Datum) oder eine begründete Ausnahme. Ein Release für Kunden verlangt: alle P0-Zeilen mit Nachweis, Rechtsprüfungs-Zeilen (REH-007) ausgefüllt, keine offenen Platzhalter in ausgelieferten Mustertexten, alle Konsistenz-Tests (REH-046) grün.
Abnahme: Release-Skript bricht ab, wenn eine P0-Zeile der Prüfliste keinen Nachweis hat; Beispiel: fehlender Test „fremde Daten → 404“ blockiert das Release.

---

## 14. Haftungsmuster aus den Recherchen als Prüfpunkte (Release-Gate REH-082)

Quelle: Klagen- und Haftungsrecherche vom 17.10.2026 (zwei Berichte). **Alle Fundstellen sind Sekundärquellen, nicht rechtlich geprüft; Aktenzeichen, Beträge und Daten vor Verwendung gegen das Primärdokument prüfen. Keine Rechtsberatung.** Für Schulen in öffentlicher Trägerschaft wurden in Deutschland keine Geldbußen gefunden; das Risiko liegt bei Schadensersatz (Art. 82), Aufsichtsmaßnahmen, Rufschaden und Regress `[unsicher]`; Privatschulen und Anbieter tragen höheres Risiko `[unsicher]`. Die Relevanz „hoch“ stammt aus der Einschätzung der Recherche, nicht aus einer Rechtsprüfung.

| Nr. | Muster (technisch) | Norm | Referenz der Recherche (ungeprüft) | Prüfpunkt im Produkt |
|---|---|---|---|---|
| H1 | Fremde Ressourcen/Schriften dynamisch geladen, IP ohne Einwilligung übertragen | Art. 6, 82 DSGVO; § 823 BGB | LG München I, 20.01.2022, Az. 3 O 17493/20: 100 EUR plus Unterlassung; danach Abmahnwelle (100–500 EUR); Vorlage an den EuGH nur in einer Quelle `[unsicher]` | REH-055, REH-054 |
| H2 | Session-Replay, Analyse- und Werbe-Tracker vor Einwilligung | § 25 TDDDG; Art. 6, 7 DSGVO; USA: CIPA | US-Klagen uneinheitlich (Berufungsgericht 2022 und 2025 für Zulassung, andere Gerichte abgewiesen); typische Forderung 5000 USD je Verstoß; deutscher Ausgang nicht gefunden | REH-054, REH-053 |
| H3 | Tracking von Schülerkommunikation auf Schulplattform | USA ECPA/CIPA; DE Art. 6, 32, 82 | Vergleich 17,25 Mio. USD; Auflage: zwei Jahre kein Drittanbieter-Code ohne Freigabe | REH-054 (Freigabeprozess) |
| H4 | Massenabfluss aus Schul-Informationssystem über Zugangsdaten eines Subunternehmers, kein Mehrfaktor | Art. 28, 32, 33/34, 82 | PowerSchool, Dezember 2024; Sammelklage laufend, Mehrfaktor-Vorwurf nur Klägerangabe `[unsicher]` | ANM/SIC Zwei-Faktor, REH-004, REH-024, DSG-033 |
| H5 | Ransomware auf Landes-Schulverwaltung, gleiches schwaches Passwort bei über 600 Konten | Art. 32, 33, 34 | Rheinland-Pfalz, Januar 2025; Zahlen widersprechen sich | ANM Passwort-Policy und Zwei-Faktor, DSG-033, DSG-038 |
| H6 | Insider-Abfluss nach Ausscheiden | Art. 32, 5 Abs. 1 lit. f | München, Ermittlungen seit Juni 2026 `[unsicher]` | DSG-021 (Offboarding), DSG-037 (Export-Alarm), REH-008 |
| H7 | Fremde Datensätze per ID abrufbar (fehlende Besitzprüfung) | Art. 25, 32; OWASP A01 | Ravenna Hub (Februar 2026), Zyosoft CVE-2026-7491, Classroomio CVE-2025-65670, EduplusCampus CVE-2025-61148, Lovable (April 2026) | REC/SIC „fremde Daten 404“, REH-014, DSG-004/005 (Export fremder Daten ausgeschlossen) |
| H8 | KI-erzeugte Software ohne Sicherheitsprüfung | Art. 24, 25, 32 | kein Urteil gefunden `[unsicher]` | REH-081 |
| H9 | Authentifizierungsumgehung, offene Datenbank bei KI-Apps | Art. 32, 33 | nur Blogquellen `[unsicher]` | SIC (Auth auf jeder Route), REH-081 |
| H10 | Daten Minderjähriger ohne Einwilligung/Zweckbindung, Werbenutzung | Art. 8, Art. 5 Abs. 1 lit. b; USA: COPPA | FTC 2023: 6 Mio. USD, ausgesetzt; Beträge widersprüchlich | REH-011, REH-013, REH-054 (keine Werbung, kein Profiling) |
| H11 | Schadensersatz ohne Bagatellgrenze, Beweislast beim Verantwortlichen | Art. 82 | EuGH C-300/21 (04.05.2023), C-340/21 (14.12.2023), C-200/23 (04.10.2024); Gegenpol C-687/21 (25.01.2024) | DSG-001 bis DSG-006, REH-036 (TOM-Nachweis) |
| H12 | Panne nicht rechtzeitig gemeldet oder dokumentiert | Art. 33, 34, 83 Abs. 4 | Meldeverstöße Teil des Bußgelds gegen einen Plattformbetreiber (2024, rund 91 Mio. EUR) | DSG-033 bis DSG-036, REH-040 |
| H13 | Öffentliche Schule als Verantwortliche | Art. 83 Abs. 7; Landesdatenschutzgesetze | keine Geldbußen belegt (Forum, ältere Quelle) `[unsicher]` | REH-005 (Trägerart), REH-001 |
| H14 | Website/App nicht barrierefrei | BFSG, BITV 2.0, Landesrecht | Abmahnung, Marktaufsicht; Gerichtsentscheidungen zu § 3a UWG offen | REH-063 bis REH-069 |
| H15 | Klartext-Passwörter, ungesalzene Hashes | Art. 32, 5 Abs. 1 lit. f | ein Chat-Dienst 2018 (Landesbehörde Baden-Württemberg): 20 000 EUR; Niedersachsen 2021: 65 000 EUR `[unsicher]`; Plattformbetreiber 2024 | ANM/SIC (scrypt, kein Klartext im Log), REH-036 |
| H16 | Stored XSS in Nutzerinhalten, Admin-Sitzung übernommen | OWASP A05; Art. 32 | Canvas/Instructure 2026, Zahlen widersprüchlich `[unsicher]` | SIC (CSP, kein `innerHTML`), REH-043, REH-055 |
| H17 | Verschlüsselung und TOMs nicht „Stand der Technik“ | Art. 32 Abs. 1 lit. a; Art. 83 Abs. 4 lit. a | Rahmen bis 10 Mio. EUR bzw. 2 % des Umsatzes; Beweislast Art. 5 Abs. 2, 24 | REH-036 |
| H18 | Keine/zu lange Löschfristen, Landesrecht ignoriert | Art. 5 Abs. 1 lit. e, 17; Schuldatenverordnungen | Berlin 07.08.2023 (§ 16), Bayern (Schulordnung § 40), Hessen (Fassung 01.12.2023) `[unsicher]` | DSG-016 bis DSG-032, REH-070 bis REH-073 |
| H19 | Fehlende Protokollierung/Alarm | Art. 32 Abs. 1 lit. b, d; OWASP A09 | keine generelle Pflicht belegt `[unsicher]` | DSG-037, REH-036 |
| H20 | DSFA fehlt bei Gesundheits- und Leistungsdaten | Art. 35 | Merkblatt Rheinland-Pfalz: Bewertung von Leistungen = hohes Risiko `[unsicher]` | REH-038 |
| H21 | Kein AV-Vertrag mit Dienstleistern | Art. 28, 44 ff. | Bayerische Vollzugsbekanntmachung für Schulen, Nr. 7 `[unsicher]` | REH-024 bis REH-027 |
| H22 | Information für Kinder nicht in einfacher Sprache | Art. 8, 12 Abs. 1; ErwG 38 | Einsichtsfähigkeit Baden-Württemberg ab 16 `[unsicher]` | REH-013, REH-047 |
| H23 | Datenschutzinformation passt nicht zum Verhalten (z. B. „IP gekürzt“, tatsächlich voll) | Art. 13, 5 Abs. 1 lit. a | Abmahnrisiko laut Audit | REH-046, DSG-030 |
| H24 | Auskunft/Löschung funktionieren nicht oder unvollständig | Art. 15, 17, 82 | weitere EuGH-Entscheidung zur Auskunft nur in einer Quelle `[unsicher]` | DSG-004 bis DSG-010 |
| H25 | Fremdskripte bei Anmeldedienst, unbenannt | Art. 13; § 25 TDDDG | Audit P4-02 | REH-058 |
| H26 | Beobachtung von Konten ohne Zweck, Grundlage, Information | Art. 5, 6, 13; Personalvertretungsrecht | Audit P1-06 | REH-020 |
| H27 | Formel-Einschleusung in CSV-Exporten | OWASP; Art. 32 | Audit P2-01 | DSG-013, SIC (zentrale Entschärfung) |

Abnahme (gilt für alle Zeilen): Die Prüfliste ist im Release-Skript (REH-082) hinterlegt; jede Zeile verweist auf mindestens einen Test oder Nachweis; eine Zeile ohne Nachweis blockiert das Kunden-Release.

---

## 15. Mustertexte und Vorlagen

Alle Texte tragen als erste Zeile die Hinweiszeile nach REH-006 und gelten als **Entwurf, nicht rechtlich geprüft, keine Rechtsberatung**. `[…]` füllt die Schule aus, `{{…}}` setzt das System ein. Die Anrede ist durchgehend „Sie“. Kein Text nennt den Anbieter außer als „Auftragsverarbeiter (siehe AV-Vertrag)“.

### 15.1 Muster Impressum

```
[HINWEIS – Entwurf eines Mustertexts, nicht rechtlich geprüft. Diese Zeile löschen, sobald die Schule den Text geprüft hat.]
Impressum
Angaben nach [§ 5 DDG bzw. nach Landesrecht]
Betreiberin dieses Angebots ({{produktname}}):
[Name der Schule]
[Straße und Hausnummer]
[Postleitzahl und Ort]
Schulträger: [Name und Anschrift des Schulträgers]
Vertreten durch: [Name und Funktion der Schulleitung]
Kontakt: Telefon [Telefonnummer], E-Mail [E-Mail-Adresse der Schule]
Zuständige Schulaufsicht: [Name und Anschrift]
Datenschutzbeauftragte/r: [Name und Kontakt]
Inhaltlich verantwortlich: [Name und Funktion]
Umsatzsteuer-Identifikationsnummer: [nur falls vorhanden, sonst diese Zeile löschen]
Technischer Betrieb: Der Betrieb erfolgt im Auftrag der Schule durch einen Auftragsverarbeiter (siehe AV-Vertrag).
Barrierefreiheit: Die Erklärung zur Barrierefreiheit finden Sie unter /barrierefreiheit.
Stand: [Datum]
```

### 15.2 Muster Datenschutzerklärung (öffentlich, `/datenschutz`)

```
[HINWEIS – Entwurf eines Mustertexts, nicht rechtlich geprüft. Diese Zeile löschen, sobald die Schule den Text geprüft hat.]
Datenschutzerklärung zur Nutzung von {{produktname}} an [Name der Schule]

1. Verantwortliche Stelle
[Name der Schule, Anschrift], vertreten durch [Name und Funktion der Schulleitung]. Telefon [Telefonnummer], E-Mail [E-Mail-Adresse].
2. Datenschutzbeauftragte/r
[Name, Anschrift, E-Mail, Telefon]
3. Wozu wir Daten verarbeiten
Stunden- und Vertretungsplanung, Information über Planänderungen, Krankmeldungen und Entschuldigungen, Anwesenheit, Mitteilungen und Nachrichten, Kursräume mit Material und Aufgaben, Dokumentation von Leistungen, Zugang und Sicherheit der Anwendung.
4. Welche Daten verarbeitet werden
Schüler/innen: Name, Klasse, Kurse, Geburtsdatum, Stundenplan, Fehlzeiten und Krankmeldungen, Atteste, Aufgabenabgaben, Noten und Rückmeldungen, Nachrichten.
Eltern: Name, Benutzername, Zuordnung zu Kindern, auf Wunsch E-Mail-Adresse und Telefonnummer, eigene Meldungen und Nachrichten.
Lehrkräfte und Personal: Name, Kürzel, Fächer, Deputat, Standort, E-Mail, Planungswünsche und Sperrzeiten, Abwesenheiten mit knapp gehaltenem Grund, eigene Einträge.
Technische Daten: Anmeldezeitpunkte, Sitzungen, Protokoll von Änderungen. {{ip_text}}
5. Rechtsgrundlagen
{{rechtsgrundlagen_liste}}
Freiwillige Funktionen (z. B. Benachrichtigungen an eine private E-Mail-Adresse) nur mit Ihrer Einwilligung (Art. 6 Abs. 1 lit. a DSGVO). Sie können sie jederzeit mit Wirkung für die Zukunft widerrufen (Profil → Benachrichtigungen).
6. Besonders geschützte Daten
Gründe von Krankmeldungen, Atteste und Förderdaten sind Gesundheitsdaten (Art. 9 DSGVO). Sie sind verschlüsselt gespeichert und nur für die dafür zuständigen Personen sichtbar.
7. Empfänger und Auftragsverarbeiter
Lehrkräfte, Schulleitung und Sekretariat im Umfang ihrer Aufgaben. Im Auftrag der Schule arbeiten: {{av_liste}}
8. Übermittlung in Länder außerhalb der EU/des EWR
{{drittland_text}}
9. Speicherdauer
{{loeschfristen_tabelle}}
Protokolle: {{protokoll_fristen}} {{backup_text}}
10. Cookies und lokale Speicherung
Wir setzen nur technisch notwendige Cookies ein. Es gibt keine Analyse-, Werbe- oder Tracking-Dienste und keine Fremdschriften. {{cookie_tabelle}}
11. Anmeldung über externe Dienste
{{sso_text}}
12. Ihre Rechte
Auskunft (Art. 15), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung (Art. 18), Datenübertragbarkeit (Art. 20), Widerspruch (Art. 21). Wir antworten spätestens innerhalb eines Monats. Kontodaten können Sie unter Profil → Daten exportieren abrufen; weitere Auskünfte erteilt die Schulleitung. Sie haben das Recht, sich bei der Aufsichtsbehörde zu beschweren: {{aufsichtsbehoerde}}
13. Pflicht zur Bereitstellung
Ohne die erforderlichen Daten ist die Nutzung der digitalen Angebote nicht möglich. Freiwillige Angaben sind gekennzeichnet.
14. Automatisierte Entscheidungen
Automatisierte Entscheidungsfindung einschließlich Profiling findet nicht statt. Vorschläge des Systems (z. B. Stundenplan) prüft und entscheidet eine Person.
15. Sicherheit
Verschlüsselte Übertragung, Rollen- und Rechtekonzept, Verschlüsselung sensibler Inhalte, Protokollierung von Änderungen.
Stand: [Datum]
```

### 15.3 Muster Hinweise für Eltern (Art. 13/14)

```
[HINWEIS – Entwurf eines Mustertexts, nicht rechtlich geprüft. Diese Zeile löschen, sobald die Schule den Text geprüft hat.]
Information nach Art. 13 und 14 DSGVO zur Nutzung von {{produktname}} an [Name der Schule]
Verantwortlich ist [Name der Schule, Anschrift], vertreten durch [Name der Schulleitung]. Datenschutzbeauftragte/r: [Name, Kontakt].
Wozu: Stunden- und Vertretungsplanung; Information über Änderungen; Krankmeldungen und Entschuldigungen; Anwesenheit; Mitteilungen und Nachrichten; Kursräume mit Material und Aufgaben; Dokumentation von Leistungen.
Welche Daten: Ihr Kind: Name, Klasse, Kurse, Stundenplan, Fehlzeiten und Krankmeldungen, Aufgabenabgaben, Noten und Rückmeldungen, Nachrichten. Sie: Name, Benutzername, Zuordnung zu Ihren Kindern, auf Wunsch E-Mail-Adresse und Telefonnummer, Ihre Krankmeldungen, Atteste und Nachrichten. Technik: Anmeldezeitpunkte, Sitzungen, Protokoll von Änderungen; {{ip_text}}
Besonders geschützt: Gründe von Krankmeldungen und Atteste sind verschlüsselt. Sichtbar nur für die meldende Person, die Familie, die Klassenleitung, das Sekretariat und die Schulleitung. Fachlehrkräfte sehen nur, dass ein Kind fehlt. Förderdaten sehen nur Schulleitung, Sekretariat und Klassenleitung; Fachlehrkräfte sehen nur die Art des Ausgleichs.
Volljährige Kinder: Ab dem 18. Geburtstag entscheidet Ihr Kind selbst, welche Bereiche (Kursräume, Stundenplan, Krankmeldungen und Fehlzeiten, Dokumente, Mitteilungen, Noten) Sie sehen und ob Schulinformationen an Sie gehen. Ohne Freigabe sehen Sie nichts.
Chats: Chats sind Ende-zu-Ende verschlüsselt. Die Schule und der Betreiber können Nachrichten nicht lesen. Ohne Wiederherstellungscode oder Passwort kann ein Chatverlauf nicht wiederhergestellt werden. Beim Löschen entfernt der Server seine Daten; Kopien auf Geräten anderer Teilnehmer bleiben.
Rechtsgrundlage: {{rechtsgrundlagen_liste}} Freiwillige Funktionen nur mit Einwilligung; Widerruf jederzeit mit Wirkung für die Zukunft (Profil).
Empfänger: Lehrkräfte, Schulleitung und Sekretariat im Umfang ihrer Aufgaben; im Auftrag der Schule: {{av_liste}}. {{drittland_text}}
Speicherdauer: {{loeschfristen_tabelle}}
Ihre Rechte: Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit, Widerspruch (Art. 15 bis 21). Kontodaten in der App unter Profil → Daten exportieren; weitere Auskünfte durch die Schulleitung, Antwort binnen eines Monats. Beschwerde bei {{aufsichtsbehoerde}}.
Bereitstellung: Ohne die Daten kein Zugang zu den digitalen Angeboten für Ihr Kind; gesetzlich erforderliche Angaben müssen gemacht werden, freiwillige sind gekennzeichnet.
Mithilfe: Geben Sie Ihr Passwort nicht weiter, richten Sie die Zwei-Faktor-Anmeldung ein, melden Sie sich auf gemeinsam genutzten Geräten ab.
Stand: [Datum]
```

### 15.4 Muster Hinweise für Schüler/innen (einfache Sprache, Sie-Form)

```
[HINWEIS – Entwurf eines Mustertexts, nicht rechtlich geprüft. Diese Zeile löschen, sobald die Schule den Text geprüft hat.]
Was passiert mit Ihren Daten in {{produktname}}?
Kurz gesagt: Die Schule nutzt {{produktname}}. So sehen Sie Ihren Stundenplan, geben Aufgaben ab, lesen Nachrichten und melden Fehlzeiten.
Welche Daten gibt es? Ihr Name, Ihre Klasse und Ihre Kurse. Ihr Stundenplan und Änderungen. Ihre Fehlzeiten und Krankmeldungen. Ihre Abgaben, Noten und Rückmeldungen. Nachrichten, die Sie schreiben oder bekommen. Der Zeitpunkt Ihrer Anmeldung. {{ip_text}}
Wer darf was sehen? Lehrkräfte sehen, was sie für ihren Unterricht brauchen. Die Klassenleitung, das Sekretariat und die Schulleitung sehen mehr, zum Beispiel Krankmeldungen. Andere Schüler/innen sehen Ihre Noten und Fehlzeiten nicht. Gesundheitsdaten, zum Beispiel Atteste, sind verschlüsselt und nur wenigen Personen zugänglich. Ihre Eltern sehen Daten, solange Sie unter 18 sind. Ab 18 entscheiden Sie selbst.
Wie lange werden Daten gespeichert? Die Schule löscht Daten, wenn sie nicht mehr gebraucht werden. Wenn Sie die Schule verlassen, wird Ihr Konto gesperrt und später gelöscht. {{loeschfristen_kurz}}
Chats: Ihre Chats sind verschlüsselt. Niemand in der Schule kann sie mitlesen. Wenn Sie Ihr Gerät verlieren und keinen Wiederherstellungscode oder kein Passwort für den Chat haben, sind alte Nachrichten verloren.
Ihre Rechte: Sie können erfahren, welche Daten über Sie gespeichert sind. Sie können falsche Daten berichtigen lassen. Unter bestimmten Bedingungen können Sie Löschung verlangen. Ansprechpartner: [Sekretariat oder Datenschutzbeauftragte/r, Name und Kontakt]. Beschwerde bei {{aufsichtsbehoerde}}.
So schützen Sie Ihre Daten: Ihr Passwort hat mindestens {{passwort_mindestlaenge_schueler}} Zeichen. Geben Sie es niemandem weiter, auch nicht Lehrkräften. Melden Sie sich an fremden Geräten ab. Schreiben Sie höflich: Nachrichten können bei Problemen gemeldet und von berechtigten Personen geprüft werden. Wenn jemand Ihr Passwort kennt, ändern Sie es sofort und sagen Sie dem Sekretariat Bescheid.
Stand: [Datum]
```

### 15.5 Muster Hinweise für Lehrkräfte und weiteres Personal

```
[HINWEIS – Entwurf eines Mustertexts, nicht rechtlich geprüft. Diese Zeile löschen, sobald die Schule den Text geprüft hat; Beteiligung der Personalvertretung prüfen.]
Information nach Art. 13 DSGVO für Lehrkräfte und weiteres Personal zur Nutzung von {{produktname}}
Verantwortlich: [Name der Schule, Anschrift], vertreten durch [Name der Schulleitung]. Datenschutzbeauftragte/r: [Name, Kontakt].
Zwecke: Stunden- und Vertretungsplanung; Aufsichtsplanung; Information über Planänderungen; Klassenbuch und Anwesenheit; Kursräume; Notenbuch; Kommunikation.
Rechtsgrundlage: Art. 6 Abs. 1 lit. e DSGVO i. V. m. [Landesdatenschutzgesetz / Beschäftigtendatenschutz §…]. Freiwillige Funktionen (iCal-Abo auf privaten Geräten, Benachrichtigungen an private E-Mail-Adressen) nur mit Ihrer Einwilligung.
Daten über Sie: Name, Kürzel, Fächer, Deputat, Standort, E-Mail; Arbeitszeiten, Sperrzeiten und Wünsche für die Planung (nur Planung und Schulleitung sehen sie); Abwesenheiten mit knapp gehaltenem Grund (nur Berechtigte sehen den Grund); Ihre Einträge in Klassenbuch, Noten, Nachrichten und Kursräumen; Anträge auf Änderung Ihres Profils (Prüfung durch Schulleitung bzw. Planung); Technikdaten: Anmeldungen, Sitzungen, Protokoll aller Änderungen (wer, wann, was, ohne Inhalte).
Keine Leistungs- oder Verhaltenskontrolle: Die Software wertet Ihre Leistung oder Ihr Verhalten nicht aus. Das Protokoll dient Sicherheit und Nachvollziehbarkeit; seine Nutzung für andere Zwecke bedarf einer Regelung mit der Personalvertretung.
Verstärkte Protokollierung: [Nur ausfüllen oder Absatz löschen: Für einzelne Konten (z. B. Testkonten) kann die Schule nach vorheriger Information jede Anfrage protokollieren; Aufbewahrung höchstens 180 Tage.]
Sichtbarkeit: Kolleginnen und Kollegen sehen Stundenplan und Vertretungen. Die Klassenleitung sieht Gründe von Krankmeldungen und Atteste der eigenen Klasse. Fachlehrkräfte sehen „vertraulich“ statt eines Grundes.
Empfänger: Schulleitung, Planung und Sekretariat im Umfang ihrer Aufgaben; im Auftrag der Schule: {{av_liste}}. {{drittland_text}}
Speicherdauer: {{loeschfristen_tabelle}} Konten ausgeschiedener Beschäftigter werden gesperrt und nach Ablauf der Wartezeit gelöscht. Kursraum-Papierkorb: {{papierkorb_tage}} Tage.
Ihre Rechte: Auskunft, Berichtigung, Löschung, Einschränkung, Widerspruch, Datenübertragbarkeit (Art. 15 bis 21); Kontodaten unter Profil → Daten exportieren. Beschwerde bei {{aufsichtsbehoerde}}.
Pflichten im Alltag: Passwort nicht weitergeben; Zwei-Faktor-Anmeldung einrichten; an gemeinsam genutzten Geräten abmelden; Abwesenheitsgründe knapp halten (keine Diagnosen); Gesundheitsdaten nur im Bereich „Atteste und Dokumente“, nicht in Kursräumen oder Nachrichten; Exporte und Namenslisten nur auf dienstlichen Geräten und nach Gebrauch löschen; Datenpannen (falsch versandte Briefe, verlorene Geräte mit angemeldeter Sitzung) sofort der Schulleitung und der IT melden.
Stand: [Datum]
```

### 15.6 Muster Erklärung zur Barrierefreiheit (`/barrierefreiheit`)

```
[HINWEIS – Entwurf eines Mustertexts, nicht rechtlich geprüft. Diese Zeile löschen, sobald die Schule den Text geprüft hat.]
Erklärung zur Barrierefreiheit für {{produktname}} an [Name der Schule]
[Name der Schule] ist bemüht, diese Anwendung im Sinne von [BITV 2.0 bzw. Landesrecht] barrierefrei zugänglich zu machen. Maßstab ist WCAG 2.2 Stufe AA (EN 301 549).
Stand der Vereinbarkeit: {{konformitaet}}
Nicht barrierefreie Bereiche: {{nicht_barrierefrei_liste}} [Begründung und Alternativen ergänzen]
Erstellung dieser Erklärung: erstellt am [Datum]; letzte Prüfung am {{pruefdatum}} (Methode: {{pruefmethode}}).
Barrieren melden: Wenn Sie auf Barrieren stoßen oder Inhalte in einer anderen Form benötigen, nutzen Sie das Formular unter /barrierefreiheit oder wenden Sie sich an [Name, Telefon, E-Mail]. Wir antworten innerhalb von [30 Tagen].
Durchsetzungsverfahren: Wenn Sie keine zufriedenstellende Antwort erhalten, können Sie sich an [Schlichtungsstelle / zuständige Stelle nach Landesrecht, Anschrift] wenden.
```

### 15.7 Muster-Auftragsverarbeitungsvertrag

Pflichtklauseln und Anlagen: Tabelle in REH-024. Das Muster ist ein vollständig ausformulierter Vertragstext mit diesen 15 Klauseln; Anlage 1 (Datenkategorien, aus REH-017/REH-035), Anlage 2 (TOMs, REH-036), Anlage 3 (Unterauftragnehmer, REH-026). Platzhalter: `[Auftragsverarbeiter]`, `[Vertragsnummer]`, `[Meldefrist in Stunden]`, `[Frist Unterauftragnehmer in Tagen]`, `[Löschfrist nach Vertragsende in Tagen]`.

### 15.8 Muster Meldung an die Aufsichtsbehörde (Art. 33 Abs. 3)

```
[HINWEIS – Entwurf eines Mustertextes, nicht rechtlich geprüft; das Meldeformular der Landesbehörde ist maßgeblich. Diese Zeile löschen, sobald geprüft.]
Meldung einer Verletzung des Schutzes personenbezogener Daten
1. Meldende Stelle: {{schule}}, vertreten durch {{schulleitung}}; Datenschutzbeauftragte/r {{dsb}}; Ansprechperson für Rückfragen: [Name, Telefon, E-Mail]
2. Zeitpunkte: Vorfall (geschätzt) {{vorfall_am}}; Kenntnis der Schule {{kenntnis_am}}; Meldung {{gemeldet_am}}. Bei Meldung nach mehr als 72 Stunden: Gründe der Verzögerung {{verspaetung_begruendung}}
3. Art der Verletzung: {{art}} (Vertraulichkeit / Integrität / Verfügbarkeit)
4. Beschreibung des Vorfalls: {{beschreibung}}
5. Betroffene Personen: Kategorien {{betroffene_kategorien}} (Schüler/innen, Minderjährige, Eltern, Beschäftigte); ungefähre Zahl {{anzahl_personen}}
6. Betroffene Daten: Kategorien {{datenkategorien}} (insbesondere Gesundheitsdaten nach Art. 9: ja/nein); ungefähre Zahl der Datensätze {{anzahl_datensaetze}}
7. Wahrscheinliche Folgen: {{folgen}}
8. Ergriffene und vorgeschlagene Maßnahmen: {{massnahmen}} (Eindämmung, Beweissicherung, Wiederherstellung, Vorbeugung)
9. Benachrichtigung der Betroffenen (Art. 34): {{betroffene_benachrichtigt}} (ja / nein, Gründe, Datum, Weg)
10. Beteiligte Auftragsverarbeiter und grenzüberschreitender Bezug: {{av_beteiligt}}
11. Weitere Meldungen (Schulaufsicht, Schulträger): [ja/nein, Datum]
Anlagen: [Liste]
```

### 15.9 Muster Mitteilung an Betroffene (Art. 34)

```
[HINWEIS – Entwurf eines Mustertextes, nicht rechtlich geprüft. Diese Zeile löschen, sobald geprüft.]
Betreff: Wichtige Information zum Schutz Ihrer Daten
Sehr geehrte Damen und Herren,
am {{vorfall_datum}} wurde festgestellt, dass {{kurzbeschreibung}}. Betroffen sind folgende Angaben: {{datenkategorien_klartext}}.
Mögliche Folgen für Sie: {{folgen_klartext}}.
Was wir getan haben: {{massnahmen_klartext}}.
Was Sie tun können: [Empfehlungen, z. B. Passwort ändern, auf auffällige Nachrichten achten].
Ihre Ansprechperson: {{dsb}}, [Telefon, E-Mail]. Sie können sich außerdem an {{aufsichtsbehoerde}} wenden.
Mit freundlichen Grüßen
[Name der Schulleitung]
```
Der Text nennt keine Gesundheitsdaten im Einzelnen und keine Namen Dritter; er geht an Eltern und Schüler/innen in einfacher Sprache, bei Volljährigen an die Person selbst.

### 15.10 Vorfallsbericht (Kurzform) und Kontaktliste

Vorfallsbericht: Datum und Uhrzeit der Kenntnis; Meldung von; Beschreibung; betroffene Daten und Personen (Anzahl, Kategorien); Sofortmaßnahmen mit Uhrzeit; Risikobewertung (gering/mittel/hoch, mit Begründung); Meldung an die Aufsichtsbehörde (ja/nein, am, Aktenzeichen); Benachrichtigung der Betroffenen (ja/nein, am); Ursache; dauerhafte Maßnahmen; Abschluss mit Unterschrift der Schulleitung.

Kontaktliste (ausfüllen, ausdrucken, offline aufbewahren; je Eintrag mit Vertretung): Schulleitung (Verantwortliche), IT-Betreuung, Datenschutzbeauftragte/r, Hoster (Support, Vertragsnummer), IT des Schulträgers, Aufsichtsbehörde (Landesdatenschutz), Softwareanbieter (Auftragsverarbeiter, Meldeweg).

### 15.11 DSFA-Schwellwertanalyse (Fragenkatalog)

1. Anzahl der Schüler/innen und Beschäftigten: [Zahl] (Quelle: mehr als 2500 Schüler/innen sprechen für eine DSFA).
2. Werden Daten Minderjähriger in großer Zahl verarbeitet? [ja/nein]
3. Besondere Kategorien (Krankmeldungsgründe, Atteste, Förderdaten, Religion über Kurswahl)? [ja/nein, welche]
4. Bewertung oder Einstufung von Personen (Noten, Fehlzeiten, Kompetenzen, Lernstand)? [ja/nein]
5. Systematische Überwachung (z. B. verstärkte Protokollierung einzelner Konten)? [ja/nein, REH-020]
6. Neue Technologien (Ende-zu-Ende-Chats, Planungsgenerator, API-Zugänge für Apps/KIs)? [ja/nein]
7. Kommunikationsfunktionen mit Meldeverfahren (Chats, Postfach)? [ja/nein]
8. Verknüpfung oder Abgleich von Datenbeständen (Import aus Untis, SchILD, ASV, Moodle, OneRoster)? [ja/nein]
9. Schutzbedürftige Betroffene (Kinder, Beschäftigte)? [ja]
10. Drittdienste oder Drittland (Register REH-026)? [ja/nein, welche]
11. Muss-Liste der Landesdatenschutzbehörde geprüft am [Datum], Ergebnis [Text]
12. Restrisiko nach den Maßnahmen (TOM): [gering/mittel/hoch]; Vorabkonsultation (Art. 36) erforderlich? [ja/nein]
Ergebnis: [DSFA erforderlich / nicht erforderlich], Begründung [Text], Stellungnahme der/des Datenschutzbeauftragten [Text], Datum [Datum], Wiedervorlage [Datum].

### 15.12 Nutzungsordnung (Gliederung)

(1) Geltungsbereich und Zugang; (2) Passwort und Zwei-Faktor-Anmeldung, keine Weitergabe; (3) gemeinsam genutzte Geräte und Abmelden; (4) Umgang mit Exporten und Namenslisten; (5) Nachrichten und Chats (höflicher Umgang, Melden, Wiederherstellungscode); (6) Uploads (Rechte Dritter, Aufnahmen von Personen, Verbot aktiver Inhalte); (7) Gesundheitsdaten nur im vorgesehenen Bereich; (8) Meldung von Datenpannen und Auffälligkeiten; (9) Folgen von Verstößen. Anrede „Sie“; für Beschäftigte Beteiligung der Personalvertretung prüfen.

### 15.13 Verzeichnis der Textvariablen `{{…}}`

| Variable | Quelle |
|---|---|
| `{{produktname}}` | eine Konfigurationsstelle (REH-045) |
| `{{schule}}`, `{{schulleitung}}`, `{{dsb}}`, `{{aufsichtsbehoerde}}` | Stammdaten der verantwortlichen Stelle (REH-002) |
| `{{rechtsgrundlagen_liste}}` | Rechtsgrundlagen-Register (REH-009) |
| `{{av_liste}}`, `{{drittland_text}}`, `{{sso_text}}` | Register der Dienste (REH-026, REH-027, REH-058) |
| `{{loeschfristen_tabelle}}`, `{{loeschfristen_kurz}}`, `{{protokoll_fristen}}`, `{{backup_text}}`, `{{papierkorb_tage}}`, `{{ip_text}}` | Fristen und Protokolle (DSG-018, DSG-026, DSG-030) |
| `{{cookie_tabelle}}` | Cookie-Inventar (REH-053) |
| `{{passwort_mindestlaenge_schueler}}`, `{{passwort_mindestlaenge_personal}}` | Konfiguration Passwortregeln (ANM) |
| `{{konformitaet}}`, `{{nicht_barrierefrei_liste}}`, `{{pruefdatum}}`, `{{pruefmethode}}` | Prüfbericht Barrierefreiheit (REH-065) |
| `{{kenntnis_am}}`, `{{vorfall_am}}`, `{{gemeldet_am}}`, `{{art}}`, `{{beschreibung}}`, `{{massnahmen}}`, `{{betroffene_kategorien}}`, `{{anzahl_personen}}`, `{{datenkategorien}}`, `{{anzahl_datensaetze}}`, `{{folgen}}`, `{{betroffene_benachrichtigt}}`, `{{av_beteiligt}}`, `{{verspaetung_begruendung}}` | Vorfallsakte (DSG-033) |

Abnahme (gilt für alle Mustertexte 15.1 bis 15.12): Jeder Text ist als Datei im Betreiber-Paket abrufbar und über *Mustertext einfügen* (nur Rechtstexte 15.1, 15.2, 15.6) bzw. als Download (übrige) verfügbar; ein Test ersetzt alle `{{…}}` aus einer Beispielkonfiguration und findet danach keine unaufgelöste Variable; ein Test zählt die `[…]`-Platzhalter und erwartet die Warnung nach REH-044; Suche nach „du“, „dein“, „dir“ (als Anrede) → 0 Treffer; Suche nach Anbieterbezeichnern → 0 Treffer.

---

## 16. Liste „juristisch zu prüfen“ (kein Rechtsrat)

Diese Liste fasst alle mit `[JP]` markierten Gegenstände zusammen. Die Prüfung erfolgt durch Anwältin/Anwalt mit Schulrecht, die Datenschutzbeauftragte bzw. den Datenschutzbeauftragten der Schule oder die Landesdatenschutzbehörde; der Anbieter dokumentiert Prüfer und Datum (REH-007).

| Nr. | Gegenstand | Verweis |
|---|---|---|
| J1 | Verantwortlicher je Land (Schule/Schulträger/Land), Schulträger als AV oder gemeinsam Verantwortlicher | REH-001 |
| J2 | Rechtsrahmen-Profile, Trägerarten (öffentlich, Ersatzschule, kirchlich) | REH-005 |
| J3 | Standardtexte der Rechtsgrundlagen, Art. 9 Abs. 2 lit. g, Landesnormen | REH-009, REH-015 |
| J4 | Einwilligungsalter, Art. 8 DSGVO, Einsichtsfähigkeit, Altersgrenze 18 | REH-013 |
| J5 | Zulässigkeit schulischer Chats, Moderation nur mit Einwilligung | REH-021 |
| J6 | Beschäftigtendaten, Art. 88 DSGVO, Personalrat, keine Leistungskontrolle | REH-018 |
| J7 | Beobachtete Konten: Zweck, Rechtsgrundlage, Information, Personalrat | REH-020 |
| J8 | Muster-AV-Vertrag, Unterauftragnehmer, Meldefrist (Vorschlag 24 Stunden), Haftung | REH-024, REH-028 |
| J9 | Drittland, Angemessenheit/Garantien (EU-US-Datenschutzrahmen) | REH-027 |
| J10 | Anbieter als eigener Verantwortlicher für Vertragsdaten, Lizenzverkehr | REH-009, REH-030 |
| J11 | Datenschutz-Funktionen bei Lizenzsperre, Vertragsende, Rückgabe | REH-029, REH-031 |
| J12 | Externe Mailkonten, Fernmeldegeheimnis bei privater Nutzung | REH-032 |
| J13 | Online-Passwortprüfung (Drittland) | REH-033 |
| J14 | Fristen Art. 12, Entgelt/Ablehnung, Identitätsprüfung | DSG-001, DSG-003 |
| J15 | Inhalt der Auskunft (Protokolleinträge, Beschäftigtennamen), Art. 15 Abs. 4 | DSG-006 |
| J16 | Anwendbarkeit Art. 20 | DSG-013 |
| J17 | Fristenprofile (NRW-Vorlage VO-DV I, weitere Länder), Obergrenze 3650 Tage | DSG-019, REH-070 |
| J18 | Digitales Klassenbuch als amtliches Klassenbuch | REH-071 |
| J19 | Zeugnis-Fehlzeiten-Frist | REH-073 |
| J20 | Backups, Nach-Löschlauf, 12 Monate | DSG-026 |
| J21 | Chat-Frist (Vorschlag 365 Tage) | DSG-027 |
| J22 | IP-Speicherung im Audit | DSG-030 |
| J23 | Inhalt des Verzeichnisses | REH-034, REH-035 |
| J24 | DSFA-Pflicht und -Ergebnis | REH-038 |
| J25 | Kenntnis, 72-Stunden-Frist, Risikoeinstufung, Meldeinhalt | REH-028, DSG-033, DSG-035, REH-040 |
| J26 | Impressum (§ 5 DDG), Datenschutzerklärung | REH-041, 15.1, 15.2 |
| J27 | Hinweise nach Art. 13/14, Nachweis der Kenntnisnahme | REH-047, REH-048 |
| J28 | Nutzungsordnung, Beteiligung Personalvertretung | REH-049 |
| J29 | Cookies/Endgerätezugriff (§ 25 TDDDG), Komfort-Cookies | REH-053, REH-057 |
| J30 | Geltung von BFSG/BITV/Landesrecht, Erklärung, Rückmeldefrist | REH-063, REH-066, REH-067 |
| J31 | Urheberrecht (§ 60a UrhG), Aufnahmen von Personen | REH-074, REH-075 |
| J32 | Plattformpflichten (DSA) für geschlossene Schulplattform | REH-076 |
| J33 | Lizenzen von Drittcode (AGPL/GPL) | REH-077 |
| J34 | Produktname und Marke | REH-078 |
| J35 | Lizenzvertrag/EULA, Code-Schutz, Patent | REH-079 |
| J36 | Ausbilderzugang bei Volljährigen | REH-023 |
| J37 | Quellenlage der Haftungsmuster (Sekundärquellen) | Abschnitt 14 |

---

## 17. Entscheidungen im Neubau und Widersprüche der Quellen

| Nr. | Gegenstand | Quellenlage | Festlegung im Neubau | Verweis |
|---|---|---|---|---|
| E1 | IP-Adressen | Hinweise: „gekürzt gespeichert“; tatsächlich volle IP in Anmeldeversuchen (30 Tage), Audit (365 Tage), Beobachtung (180 Tage); Audit vom 17.10. fordert Anpassung | Zugriffsprotokoll gekürzt; Audit standardmäßig gekürzt (`audit_ip_mode`); Text aus Konfiguration | DSG-030, REH-046 |
| E2 | Konto-Löschfrist | Hinweise/Verzeichnis „3 Monate“; Löschkonzept: Konto zuletzt, Wartezeit 30 Tage | Löschkonzept gilt | DSG-020 |
| E3 | Krankmeldungs-Frist | Überblick: „Schuljahresende + Zeugnisfrist“; Löschkonzept: 30 Tage nach Austritt bzw. 31. Juli + 365 Tage | Löschkonzept; Zeugnisfrist als Profilfeld, größerer Wert gilt | DSG-018, REH-073 |
| E4 | Nachrichten-Frist | Verzeichnis 365 Tage; Löschkonzept 30 Tage nach Austritt (eigene Nachrichten) | beide gelten nebeneinander (laufend 365, nach Austritt 30) | DSG-018 |
| E5 | „Audit ohne Inhalte“ | TOMs/Hinweise; Beobachtungsprotokoll mit verschlüsselten Inhalten | Ausnahme in TOMs und Hinweisen benannt | REH-020, REH-036 |
| E6 | „0“ schaltet Löschung ab | Altsystem: 0 = nie/aus; Audit-Fund | verboten, Bereich 1–3650 | DSG-017 |
| E7 | Dokumente „nie löschen“ | 12.10.: alle Dokumente speichern; 16.10.: Fristen je Datenart | Fristen gelten; Archiv-Zustand nur für Aufbewahrungspflichtiges | DSG-018, DSG-025 |
| E8 | Drittland | Verzeichnis „keine“; Passwort-Online-Prüfung (USA) optional | Standard keine, Dienste über Register mit Text-Anpassung | REH-027, REH-033 |
| E9 | Passwortlänge Schüler/innen | App 8; Hinweis 10 | Zahl aus Konfiguration | REH-046 |
| E10 | Geburtsdaten | „nicht nötig“ (Datenkategorien); tatsächlich gespeichert | Katalog führt sie | REH-017 |
| E11 | Auskunft ohne Konto | Altsystem 404 und manuell | Auskunft auch ohne Konto | DSG-005 |
| E12 | Einwilligungsalter | nicht festgelegt | Schulfeld, ohne Wert Eltern willigen ein | REH-013 |
| E13 | Route `/datenschutz` | dreifach belegt | öffentlich `/datenschutz`, Verwaltung `/datenschutz-verwaltung`, Hinweise `/hilfe/datenschutz` | REH-042 |
| E14 | Verantwortung Impressum/Datenschutz | Betreiber: Schule trägt ein; Teilung unklar | Schule verantwortlich, Anbieter liefert Muster und Konsistenz | Abschnitt 8 |
| E15 | Auskunft: Sekretariat oder Schulleitung | Backlog B-57 beide; Rechtekatalog `privacy.subject` nur Schulleitung (17.10.) | Schulleitung; Recht vergebbar, nie an technische Administration | DSG-005 |
| E16 | Probe-Restore-Rhythmus | TOM halbjährlich; Betriebsnachweis vierteljährlich | vierteljährlich | REH-037 |
| E17 | Netzport 443/udp | Sicherheitskonzept nennt, TOM-Checkliste nicht | beide genannt (22 eingeschränkt, 80/tcp, 443/tcp, 443/udp) | REH-036 |
| E18 | Chats ohne Frist | Löschkonzept: nur 30 Tage nach Austritt | Vorschlag 365 Tage laufend | DSG-027 |
| E19 | Altersgrenze 18 | Betreiber soll sie ausdrücklich bestätigen | als Standard gesetzt, Bestätigung offen | REH-013 |
| E20 | Beobachtungsprotokoll in der Selbstauskunft | bewusst keine Selbstauskunft (würde Beobachtung verraten) | Auskunft organisatorisch über den CSV-Export; Information vorab | REH-020, DSG-004 |
| E21 | Chat-Schlüssel nach Abmeldung | Audit: bleiben im Browser | Auswahl „privates Gerät“ | REH-056 |
| E22 | Sitzungsdauer Personal | Empfehlung „1 Tag“ vs. Standard 12 Stunden | 12 Stunden (einstellbar 15 Minuten bis 7 Tage) | REH-053 |
| E23 | Anrede in Schülertexten | frühere Entwürfe „du“; Betreiberentscheidung 16.10.2026 „siezen“ | Sie überall | REH-047 |
| E24 | Beobachtung echter Schüler-/Elternkonten | im Altbestand technisch möglich | unzulässig | REH-020 |

<!--ENDE-->
