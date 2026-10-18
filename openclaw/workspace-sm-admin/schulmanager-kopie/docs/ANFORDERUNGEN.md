# Anforderungen des Auftraggebers (vollständig aus dem Chatverlauf)

Quelle: alle Nachrichten des Auftraggebers seit dem 05.10.2026, sinngemäß geordnet (Rechtschreibung der Zitate
geglättet). Jede Anforderung hat eine ID. **Status und Nachweise stehen in `docs/OFFENE-PUNKTE.md`** – diese Datei
hier ändert sich nur, wenn der Auftraggeber Neues verlangt.

Leitziel (A-00): Ein Schulmanager, den man „als volles Produkt an eine Schule verkaufen kann“ und mit dem die Schule
„wirklich alles darüber machen kann“ – ohne KI-typische Oberfläche, für PC, Laptop, Tablet und Handy. „Denke an mehr,
was ich jetzt nicht ausdrücklich gesagt habe.“

## 1. Grundsystem (05.10.)
- **A-01** Zusammenarbeit mit vorhandenen Schulmanager-Systemen (Import/Export, z. B. Untis, Schulmanager Online, SchILD/ASV).
- **A-02** Stundenpläne für ~2500 Schüler/innen und einige hundert Lehrkräfte erzeugen.
- **A-03** Pläne ändern sich jederzeit dynamisch; bei kranken Lehrkräften wird live umgeplant.
- **A-04** Festlegen, welche Fächer mit wie vielen Wochenstunden je Klasse stattfinden (Stundentafel).
- **A-05** Priorisieren, dass Ausfälle am Anfang und Ende des Schultags liegen.

## 2. Lehrkräfte, Kursräume, Schüler/Eltern, Postfach (06.10.)
- **A-06** Web-Oberfläche für alle Rollen.
- **A-07** Lehrkräfte und Schüler/innen melden sich über die Seite krank.
- **A-08** Jede Lehrkraft hat ein eigenes Konto und pflegt: welche Klassen sie hauptsächlich unterrichtet, Fächer,
  Wochenstunden, Tagesbeginn (z. B. erst ab 10 Uhr, nur Abendunterricht ab 16 Uhr) → fließt in die Planung.
- **A-09** Lehrkräfte haben keinen Vollzugriff, nur auf ihre Fächer und die zugehörigen Klassen/Gruppen.
- **A-10** Klassen-/Kursräume mit Ordnern; Lehrkräfte legen Unterrichtsmaterial ab und geben es zu einer
  Unterrichtsstunde für die angemeldeten Schüler/innen frei (nach Vorbild Moodle).
- **A-11** Schülerübersicht mit Stundenplan und Krankmeldung für den Tag – selbst nur, wenn als volljährig (18)
  eingetragen von einer autorisierten Person; sonst über die Eltern-Konten.
- **A-12** Eltern bzw. volljährige Schüler/innen reichen Krankschreibungen/Atteste und andere Dokumente ein.
- **A-13** Internes Postfach für alle; Nachrichten an alle im System möglich; verschlüsselt gespeichert.

## 3. Vorschau und Klassen-Seite (10.10.)
- **A-14** Eine Vorschau zum Selbsttesten (Codespaces) mit Demo-Konten.
- **A-15** Klassenraum je Klasse setzen.
- **A-16** Nach einer Klasse suchen; dort Schüler/innen, zuständige Lehrkräfte (Klassen- und Fachlehrkräfte) sehen.
- **A-17** Den Wochenstundenplan der Klasse einsehen und angeben, dass etwas nicht stattfindet → automatische Umplanung.

## 4. Konten und Anmeldung (10.10.)
- **A-18** E-Mail und Handynummer mit dem Konto verbinden und darüber das Passwort zurücksetzen; der Admin darf das auch.
- **A-19** Ganze Klassen hinzufügen; für jeden neuen Schüler Zugangsdaten erzeugen; PDFs, die man einzeln verschicken kann.
- **A-20** Beim ersten Anmelden muss ein neues Passwort gesetzt werden.
- **A-21** Microsoft-, Apple- oder Google-Konto verbinden.
- **A-22** Admin legt fest, dass sich z. B. Schüler/innen nur mit bestimmten Anbietern anmelden (Schule gibt allen
  Apple- und Microsoft-Konten) – je Person, Klasse, Gruppe in der Klasse (nur Schüler/innen oder nur Eltern); wer darf
  sich über alles anmelden, wer darf ein Konto erstellen.
- **A-23** Konten werden beim Anlegen neuer Klassen vorgefertigt; die Kinder bekommen ein PDF an die eingetragene
  E-Mail mit Name, Benutzername und Einmal-Passwort und setzen sofort ein eigenes Passwort.
- **A-24** Admin und Lehrkräfte können das Passwort auf das erste Passwort zurücksetzen oder selbst ein neues setzen.
- **A-25** Passwortfeld mit Auge-Symbol zum Anzeigen.
- **A-26** Mehrere Konten speichern und ohne Probleme wechseln.
- **A-27** Passwort-Logins im Browser speichern (gängige Browser/Passwort-Manager: Google, Apple, Microsoft), automatische
  Anmeldung, Geräteerkennung – aber nicht fälschbar (niemand kann sich als jemand anderes ausgeben).

## 5. Zeitraster, Rhythmus, Planung (10.10.)
- **A-28** Wochen 1 … 52 (bis zur letzten Woche), Feiertage setzbar; in der Planungsoberfläche einfach angeben, ob etwas
  jede Woche, in ausgewählten Wochen oder im Rhythmus („alle k Wochen ab Woche s“) gilt.
- **A-29** Es gibt keinen globalen Wochenrhythmus der Schule: Wochenangaben hängen an dem, was sie betrifft (Kurs,
  Sperrzeit, Wunsch, Zeitfenster, Aufsicht).
- **A-67** (11.10., Präzisierung zu A-28/A-29, Vorrang) Wochenbuchstaben gibt es **nirgends** mehr. Wochenangaben sind
  jede Woche, ausgewählte Wochen (1 … 52) oder ein Rhythmus mit beliebigem Abstand k (1 … 52) – skalierbar, ohne feste
  Zahl unterschiedlicher Wochen. Ältere Daten werden verlustfrei umgerechnet.
- **A-68** (11.10.) Wirklich **alle Wochen** anzeigen, Woche 1 bis Woche 52 – auch Ferienwochen zählen und werden nicht
  übersprungen. **Jede Woche hat 7 Tage** (Montag bis Sonntag).
- **A-69** (11.10.) **Tageszeiten je Klasse**: Beginn und Länge des Tages ergeben sich aus den Stunden der Klasse und sind
  pro Klasse einstellbar – z. B. beginnt der Tag einer Abendklasse erst um 16 Uhr, eine normale Klasse hat morgens ihre
  erste Stunde; jede Klasse hat ihre eigene „1. Stunde“. Hat eine Lehrkraft früh Unterricht und später Abendklassen, wird
  das in ihrem Plan (und überall sonst) zeitlich richtig angezeigt.
- **A-30** Doppelstunden in den Stunden zwischen den Pausen planen – nicht immer möglich (z. B. 3 Wochenstunden).
- **A-31** Zeitraster frei einstellbar: Schulbeginn (7:50, 7:55, 8:00 …), Stundenlänge (45 min, 60 min, frei), Pausen.
- **A-32** Einstellungen bei ihrer eigenen Sache; Tage pro Woche allgemein; Samstag/Sonntag im Plan anzeigen, wenn dort
  Termine sind (Schüler können/müssen kommen).
- **A-33** Max. Klassenarbeiten pro Klasse pro Schulhalbjahr festlegbar.
- **A-34** Der Prioritäten-Tab der Planung ist unverständlich → überarbeiten.

## 6. Stammdaten und Schulstruktur (10.10.)
- **A-35** Stundentafel (wie viele Stunden je Fach) funktioniert nicht → reparieren.
- **A-36** Eigene Fächer hinzufügen – auch neue Fächer bei der Lehrer-Anmeldung/-Selbstverwaltung.
- **A-37** Allgemeine Konfig-Dateien je Klasse, Lehrkraft, Schüler/in usw. (inkl. wann welche Lehrkraft kann), damit
  eine andere Schule alles übernehmen kann.
- **A-38** Klassentypen hinzufügen und löschen; unterschiedliche Bildungsgänge an einer Schule (z. B. Informatik,
  Maurer) mit jeweils eigener Klasse 11; eigene Namen.
- **A-39** Klassen rücken zum Ende des Schuljahres automatisch eine Stufe höher.
- **A-40** „Gilt für Jahrgang“ ist irrelevant → allgemeine Option für eigene Klassen.
- **A-41** Im Klassen-Anlegen: Klassenleitung(en), Klassensprecher/in, Verwalter, Eltern je Schüler/in.
- **A-42** Mehrere Klassenleitungen je Klasse.
- **A-43** Gruppen von Klassen anlegen (IT-Zweig Klassen 1–13 oder 11–13, Abi-Klassen, Fach-Abi, Nachhilfe …).
- **A-44** Eltern-Kind-Zuordnung (ein Elternteil zu einem oder mehreren Kindern); Eltern sehen alles, was das Kind sieht,
  solange es unter 18 ist – automatisch aus dem Geburtsdatum (Schule trägt Geburtsdaten ein); volljährige Schüler/innen
  stellen ein, worauf ihre Eltern zugreifen dürfen.

## 7. Kursräume (10.10.)
- **A-45** Lehrkräfte können Ordner und einzelne Dateien in Klassen-/Kursräume einfügen (funktioniert laut Auftraggeber nicht).
- **A-46** Gespeichertes Material verbergen und zur Stunde manuell oder automatisch freigeben, sodass Schüler/innen und
  Eltern es sehen.
- **A-47** Eltern sind (lesend) in den Unterrichtsräumen ihrer Kinder.

## 8. Lehrkräfte-Verfügbarkeit und Vertretung (10.10.)
- **A-48** „Wunschklassen“ ersetzen durch: Klassenleitung (welche), in welchen Klassen man unterrichtet, in welchen man
  vertreten kann (Vertretung durch Lehrkräfte, die dieselben Klassen unterrichten).
- **A-49** Lehrkräfte bestimmen nicht selbst max. Stunden/Vertretungen, nur Tage und maximale Wochenstunden; Vertretungen
  fair verteilen (nicht ein Lehrer viel, ein anderer nichts) – ohne starre Max/Min-Vorgaben.
- **A-50** Arbeitszeitfenster dynamisch ohne Vorgaben: ein Wochenplan in frei wählbaren Zyklen mit Ausnahmen (jeden
  ersten Mittwoch im Monat/Jahr, jede 3. Woche nicht, alle 2 Wochen erst ab 10, mittwochs nie nach 12, erst ab 9 …).
- **A-51** Sperrzeiten ohne viele Vorgaben, frei einstellbar bis zu einzelnen Stunden an bestimmten Tagen.

## 9. Fehlzeiten, Krankmeldungen, Unterricht (10.10.)
- **A-52** Schriftliche Entschuldigung an die Schule als Krankmeldung → die Stunden gelten als entschuldigt statt unentschuldigt.
- **A-53** Schüler/innen, Eltern und Lehrkräfte sehen, wie viele entschuldigte, unentschuldigte und verspätete Stunden
  es gibt und in welchen Fächern wie viele Fehlstunden.
- **A-54** Im Stundenplan auf Namen/Abkürzungen tippen → Details: voller Name der Lehrkraft, genauer Fachname, Raum/Ort,
  ob die Stunde stattfindet, ob es Hausaufgaben gibt.
- **A-55** Lehrkräfte tragen Hausaufgaben ein.
- **A-56** Vertretungsplan: fehlende Lehrkräfte getrennt aufführen; die Anzeige „fehlende Klassen“ entfällt.
- **A-57** In der Klassenansicht: wer krank ist, wie viele, ob eine Bescheinigung eingeschickt, eingesehen und von der
  zuständigen Klassen- oder Abteilungsleitung anerkannt wurde (dass die Entschuldigung gilt).
- **A-58** Krankheitsdaten nur für Klassenleitungen und genehmigte Lehrkräfte, Eltern mit Genehmigung und den Schüler selbst.

## 10. Darstellung und Bedienung (10.10.)
- **A-59** Professionelle Designsprache; keine KI-typischen Erklärtexte und komischen Schieber/Felder.
- **A-60** Hilfe zu einer Option erst nach ~2 s Hover oder per Rechtsklick auf den Namen; am Handy Antippen des Namens.
- **A-61** Optimiert für PC, Laptop, Tablet und Handy (Benutzererlebnis).
- **A-62** Monitor-Ansicht modular und auf Mobilgeräten nutzbar.

## 11. Arbeitsweise und Qualität (10.10.)
- **A-63** Feature-Analyst ermittelt wichtige Funktionen gängiger Systeme, was wir haben, was nicht richtig funktioniert
  und was dringend fehlt (`docs/PRODUKT-BACKLOG.md`); Design/UX-Agent; zwei Umsetzungs-Agenten arbeiten den Plan ab.
- **A-64** Beispielschulen als Beispiel-Konfiguration (aus öffentlichen, nicht personenbezogenen Rahmendaten,
  `docs/beispielschulen/`) und eine Testliste aller Funktionen, deren Ergebnisse direkt zurückfließen.
- **A-65** Code-Dokumentation für Agenten (`docs/code/`), damit nicht immer der ganze Code gelesen werden muss –
  als feste Routine; aktive Prüfung auf Unstimmigkeiten; Abgleich mit allen Anforderungen → `docs/OFFENE-PUNKTE.md`
  → umsetzen.
- **A-66** Keine Hintergrundarbeit ohne Wissen des Auftraggebers; transparent und sparsam mit Tokens/Kosten.

## 12. Nachschreibtermine, Vertretungsplan, Dokumentstatus (12.10.)
- **A-67** Vertretungsplan nur für Personal: Schüler/innen und Eltern haben kein Recht `substitution.read` (Menü, Seite,
  Startkachel, `GET /substitutions*` → 403); sie sehen Entfall, Vertretung und Raumänderung im eigenen Stundenplan/Kalender.
- **A-68** Nachschreibtermine: Fehlt eine Person am Tag einer Klausur/eines Tests (Krankmeldung oder Klassenbuch), entsteht
  eine Aufgabe für die Lehrkraft der Klausur (Startseite, Menü-Zähler, Live-Ereignis `makeups`); sie legt Datum, Stunden,
  Raum fest (mehrere Personen gemeinsam, Konfliktprüfung gegen Klausuren, Termine, Stundenplan). Schüler/innen und Eltern
  sehen Termin und Attest-Status in Startseite, Klausurliste und Kalender. Fachlehrkräfte sehen nur „abwesend“, Termin
  und Attest-Status – nie Grund oder Dokument.
- **A-69** Dokumentstatus „eingereicht → genehmigt/abgelehnt“ überall sichtbar; Ablehnen nur mit Grund; Dokumente werden
  nie sofort vernichtet (Zurückziehen = Archivieren, endgültig nur per Aufbewahrungsfrist).
- **A-70** Klausurseite: Klick auf eine Klausur öffnet Details mit Links in Kursraum und Stundenplan (Woche der Klausur);
  Raum der Klausur bzw. der Unterrichtsstunde bzw. „Raum noch offen“; Kürzel mit Sprechblase.
