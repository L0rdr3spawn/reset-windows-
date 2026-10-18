# 04 – Rechte, Rollen, Anmeldung, Konten (REC, ANM)

**Geltung:** Spezifikation für den Neubau „Schulpuls“ (Produktname nur an einer Stelle konfigurierbar: `SM_APP_NAME`). Stand der Quellen: Altbestand bis 18.10.2026; spätere Entscheidungen überstimmen frühere.

**Kennungen und Format**
- `REC-nnn` = Rechte und Rollen. `ANM-nnn` = Anmeldung, SSO, Zwei-Faktor, Sitzungen, Konten. Nummern je Kürzel fortlaufend ab 001.
- Jede Anforderung hat Priorität (P0 Pflicht/Sicherheit/Recht, P1 Kernfunktion, P2 wichtig, P3 Wunsch), Status (`Status: Ist` = im Altbestand gebaut, mindestens zu übernehmen; `Status: offen` = gewünscht oder gefordert, noch nicht gebaut) und genau eine `Abnahme:`-Zeile.
- `[unklar: …]` = Quelle widersprüchlich oder lückenhaft; bis zur Entscheidung gilt der genannte Standard.
- Tabellen sind Referenzdaten (Katalog, Werte); verbindlich sind sie über die Anforderung, die auf sie verweist.

**Gestaltungsregeln, die in beiden Bereichen gelten**
- Anrede „Sie“ für alle Rollen, auch Schüler/innen. Erklärungen nur über Hilfe-Symbol („?“) bzw. Hilfetext, keine Erklär-Absätze. App-Dialoge statt Browser-Popups.
- Fremde Daten liefern 404 (Regel in Abschnitt R10). Jede schreibende Aktion wird protokolliert, ohne Inhalte. Freitexte werden verschlüsselt gespeichert. Sicherheit und Datenschutz gehen vor Komfort.
- Der Server entscheidet jede Berechtigung; die Oberfläche blendet nur aus.

**Rollenkürzel in den Tabellen**
ADM = Administration (`admin`) · SL = Schulleitung (`schulleitung`) · SEK = Sekretariat (`sekretariat`) · PLA = Stundenplanung (`planer`) · AL = Abteilungsleitung (`abteilungsleitung`) · LEH = Lehrkraft (`lehrer`) · HM = Hausmeister/in (`hausmeister`) · SB = Schulbegleitung (`schulbegleitung`) · SCH = Schüler/in (`schueler`) · ELT = Eltern (`eltern`) · MON = Monitor (`monitor`) · ZUS = Zuschauer/in (`zuschauer`).

## Kennzahlen (Abnahmegrundlage)

| Größe | Wert |
|---|---|
| Rechte im Katalog | 61 in 6 Gruppen (Pläne & Stammdaten 6, Vertretung & Aufsicht 7, Schüler/Klassenbuch/Prüfungen 19, Kommunikation & Kursräume 13, Konten & Profile 4, Verwaltung & System 12); davon 6 mit Status „geplant“ |
| Umfänge | 11 (Alle plus 10 Einschränkungen) |
| Eingebaute Rollen / Grundtypen / abgeleiteter Titel | 12 / 5 / 1 (Klassenleitung) |
| Standardrechte je Rolle | ADM 41 · SL 53 · SEK 29 · PLA 21 · AL 30 · LEH 28 · HM 3 · SB 2 · SCH 4 (+2 bei Volljährigkeit) · ELT 6 · MON 1 · ZUS 26 |
| Umfangs-Einschränkungen im Standard | LEH 20 · AL 22 · SCH 3 · ELT 4 · SL 1 · SEK 1 · PLA 1 |
| Selbstaussperr-Schutz | 4 Rechte (`rights.manage`, `users.manage`, `license.manage`, `watch.read`) |
| Heikle Rechte mit Hinweis | 26; Zweck-Listen für 6 Grundrollen; Verboten-Hinweise: Administration 20, Schüler/in 2 |
| Protokollaktionen Rechte/Rollen/Konten | 16 (Abschnitt R8, REC-056) |

---

# TEIL A – RECHTE UND ROLLEN (REC)

## R1 Rollenmodell

### R1.1 Eingebaute Rollen (12)

| Kennung | Bezeichnung | Grundtyp | Anzeige-Gruppe | Rangstufe | Zuordnung | Zweck | Standardrechte |
|---|---|---|---|---|---|---|---|
| `admin` | Administration | Personal/Verwaltung | Technik | 6 | – | Technischer Betrieb: Konten, Einstellungen, Sicherungen. Sieht keine Gesundheitsdaten | 41 |
| `schulleitung` | Schulleitung | Personal/Verwaltung | Personal | 5 | – | Leitet die Schule. Sieht und verwaltet nahezu alles, vergibt Rollen und Rechte | 53 |
| `sekretariat` | Sekretariat | Personal/Verwaltung | Personal | 4 | – | Verwaltung: Stammdaten, Krankmeldungen, Mitteilungen, Konten von Schüler/innen und Eltern | 29 |
| `planer` | Stundenplanung | Personal/Verwaltung | Personal | 4 | – | Stundenplan erstellen und ändern, Vertretungen, Klausuren | 21 |
| `abteilungsleitung` | Abteilungsleitung | Lehrkraft | Personal | 3 | Zweige (mehrere je Konto) | Leitet einen Schulzweig: wie Lehrkraft, mit Blick auf alle Klassen des eigenen Zweigs | 30 |
| `lehrer` | Lehrkraft | Lehrkraft | Personal | 1 | Lehrkraft-Kürzel | Unterricht: eigener Plan, eigene Kurse und Klassen; als Klassenleitung zusätzlich die geleitete Klasse | 28 |
| `hausmeister` | Hausmeister/in | Personal/Verwaltung | eingeschränkt | 1 | – | Haustechnik: Raumpläne und Anzeige, keine Schülerdaten | 3 |
| `schulbegleitung` | Schulbegleitung | Eltern | Kind | 0 | Kinder (mehrere je Konto) | Begleitet ein Kind: dessen Stundenplan, Kursräume und Material; ohne Elternrechte (keine Krankmeldung) | 2 |
| `schueler` | Schüler/in | Schüler/in | Kind | 0 | Schüler-Verknüpfung (ein/e Schüler/in) | Eigener Plan, Kursräume, Postfach | 4 (+2 bei Volljährigkeit) |
| `eltern` | Eltern | Eltern | Kind | 0 | Kinder (mehrere je Konto) | Pläne und Krankmeldung der eigenen Kinder | 6 |
| `monitor` | Monitor (Anzeige) | Ansicht | Anzeige | 0 | – (optional fester Standort) | Anzeigegerät (Vertretungsplan im Foyer) | 1 |
| `zuschauer` | Zuschauer/in (nur lesen) | Ansicht | Anzeige | 0 | – | Vorführ- und Prüfzugang: sieht Pläne, Stammdaten, Vertretung und Kursräume wie Leitung, Planung und Sekretariat, ändert nichts. Ohne Gesundheits-, Förder-, Noten-, Kontodaten, Protokolle und Schlüssel | 26 |

Hinweis: „Anzeige-Gruppe“ (Technik, Personal, eingeschränkt, Kind, Anzeige) ist reine Darstellungsordnung der Rollenliste und nicht identisch mit dem Grundtyp. Rangstufe sortiert die Anzeige [unklar: weitere Wirkung der Rangstufe nicht belegt].

### R1.2 Grundtypen (5)

| Grundtyp | Bezeichnung | Grundrolle im Konto | Eingebaute Rollen | Bedeutung |
|---|---|---|---|---|
| `personal` | Personal/Verwaltung | `sekretariat` | admin, schulleitung, planer, sekretariat, hausmeister | Verwaltung ohne eigene Klassen; sieht, was die Rechte erlauben, ohne Lehrkraft- oder Kind-Bezug |
| `lehrkraft` | Lehrkraft | `lehrer` | lehrer, abteilungsleitung | Mit Lehrkraft-Kürzel: eigene Kurse, eigene Klassen, Klassenleitung aus den Stammdaten |
| `schueler` | Schüler/in | `schueler` | schueler | Mit Schüler-Verknüpfung: eigener Plan, eigene Klasse, eigene Daten |
| `eltern` | Eltern | `eltern` | eltern, schulbegleitung | Mit verknüpften Kindern: Pläne und Daten der eigenen Kinder |
| `ansicht` | Ansicht | `zuschauer` | monitor, zuschauer | Liest, ändert nichts, außer mit ausdrücklich erteilten Rechten |

Die Grundrolle steht im Konto (`users.role`) und bestimmt das Verhalten (Lehrkraft-Kürzel, Kinder der Eltern, eigene Klasse, Schreibschutz der Ansichtskonten). Rollenvergleiche im Code laufen immer über die Grundrolle, Anzeige und Rechte über die eigene Rolle (`users.custom_role`).

### R1.3 Anforderungen Rollenmodell

- **REC-001** (P0, Status: Ist) Drei strikt getrennte Ebenen: **Rolle** (Konto-Eigenschaft), **Recht** (Erlaubnis aus dem zentralen Katalog) und **Umfang** (Datenreichweite des Rechts). Jede Zugriffsentscheidung kombiniert alle drei und wird serverseitig bei jeder Anfrage neu berechnet; Änderungen an Rollen/Rechten wirken bei der nächsten Anfrage ohne Neustart, auch bei mehreren Serverprozessen. Die Oberfläche blendet nur aus.
  Abnahme: Konto mit Recht R und Umfang U ruft einen Datensatz außerhalb U direkt per Schnittstelle auf → 404; ruft es eine Funktion ohne R auf → 403; wird R der Rolle entzogen, antwortet die nächste Anfrage desselben Kontos ohne Neustart mit 403 (auch gegen zwei parallel laufende Serverprozesse); ein in der Oberfläche ausgeblendetes Element, direkt per Schnittstelle aufgerufen, liefert dieselbe Ablehnung.

- **REC-002** (P0, Status: Ist) Es gibt genau 12 eingebaute Rollen mit den Kennungen und Standardrechten aus Tabelle R1.1; die Standardrechte je Rolle stehen im Katalog (Abschnitt R7) und ergeben die Anzahlen der Tabelle.
  Abnahme: Frische Installation, Rollenliste abrufen: 12 Rollen mit den Kennungen der Tabelle; Zahl der wirksamen Standardrechte je Rolle exakt ADM 41, SL 53, SEK 29, PLA 21, AL 30, LEH 28, HM 3, SB 2, SCH 4, ELT 6, MON 1, ZUS 26; ein Schüler-Konto mit Geburtsdatum ≥ 18 Jahre hat 6 Rechte.

- **REC-003** (P1, Status: Ist) Eingebaute Rollen sind nicht löschbar und ihre Kennungen unveränderlich; sie tragen Grundtyp, Anzeige-Gruppe und Rangstufe wie in R1.1. Eigene Rollen haben Rangstufe 0.
  Abnahme: Löschversuch einer eingebauten Rolle → abgelehnt (Fehlermeldung, Rolle bleibt); Rollenliste sortiert nach Rangstufe absteigend, danach nach Bezeichnung; eigene Rolle erscheint mit Rangstufe 0.

- **REC-004** (P0, Status: Ist) Fünf Grundtypen (Tabelle R1.2) bestimmen die Grundrolle jedes Kontos. Alle Verhaltensentscheidungen (Lehrkraft-Kürzel, Kinder, eigene Klasse, Schreibschutz der Ansichtskonten, Menüs, Datenumfang) hängen an der Grundrolle, nicht am Namen der eigenen Rolle.
  Abnahme: Konto mit eigener Rolle vom Grundtyp `ansicht` wird bei jeder schreibenden Anfrage wie `zuschauer` behandelt (403, Text siehe REC-020); Umbenennen der eigenen Rolle ändert kein Verhalten.

- **REC-005** (P0, Status: Ist) Jedes Konto hat genau eine Grundrolle und höchstens eine eigene Rolle (Konto-Felder `role`, `custom_role`); zwei eigene Rollen je Konto sind nicht möglich. Mehrfach-Zuordnungen gibt es nur für Zweige (Abteilungsleitung) und Kinder (Eltern, Schulbegleitung). Verknüpfungen: Lehrkraft über Lehrkraft-Kürzel, Schüler/in über Schüler-ID, Eltern über Eltern-Kind-Verknüpfung (je Paar nur einmal). Abgeleitete Titel zählen nicht als Rolle.
  Abnahme: Zweite eigene Rolle zuweisen → nicht möglich (Auswahl bietet nur eine); gleiche Eltern-Kind-Verknüpfung zweimal setzen → nur ein Eintrag; Konto mit Grundrolle `lehrer` ohne Kürzel kann angelegt werden und sieht keine Unterrichtsdaten (Meldung statt Fehler 500).

- **REC-006** (P1, Status: Ist) Klassenleitung ist keine Konto-Rolle, sondern ein abgeleiteter Titel: Eine Lehrkraft (oder Abteilungsleitung), die in den Stammdaten als Klassenleitung einer Klasse eingetragen ist, sieht zusätzlich Plan, Klassenbuch-Übersicht und Atteste der eigenen Klasse. Der Umfang „Eigene Klassenleitung“ hängt ausschließlich an diesem Stammdaten-Eintrag; keine doppelte Pflege.
  Abnahme: Lehrkraft L wird in den Stammdaten als Klassenleitung von 5a eingetragen → ohne Rechteänderung sieht L Atteste von 5a und nicht von 5b; wird der Eintrag entfernt, verschwindet die Sicht bei der nächsten Anfrage.

- **REC-007** (P2, Status: Ist) Das Profil zeigt „Ihre Rolle“ als abgeleiteten Titel: eigene Rolle bzw. Rollenbezeichnung; bei Lehrkraft/Abteilungsleitung mit Klassenleitung „Klassenleitung <Klassenname>“; bei Abteilungsleitung je Zweig „Zweig <Name>“; bei Schulbegleitung und Eltern die Liste der Kinder. Rangfolge der Titel für die Anzeige: Lehrkraft, Klassenleitung, Abteilungsleitung, Sekretariat, Schulleitung.
  Abnahme: Lehrkraft mit Klassenleitung 5a → Profil zeigt „Lehrkraft · Klassenleitung 5a“; Abteilungsleitung des Zweigs „Unterstufe“ → „Abteilungsleitung · Zweig Unterstufe“; Eltern mit zwei Kindern → beide Kinder aufgelistet.

- **REC-008** (P0, Status: Ist) Volljährigkeit bestimmt sich aus dem Geburtsdatum (18 Jahre, Stichtag in Zeitzone Europe/Berlin); das Konto-Kennzeichen „volljährig“ (`users.adult`) gilt nur ohne Geburtsdatum. Die Rechte wechseln bei jeder Anfrage am Geburtstag ohne Zutun: Schüler/innen erhalten `student_absence.report` und `student_documents.read` mit Umfang „Nur selbst“ (Standardrechte 4 → 6). Minderjährige Schüler/innen melden sich nie selbst krank.
  Abnahme: Mit fester Uhr: Schüler/in, 17 Jahre 364 Tage → 4 Rechte, Selbst-Krankmeldung 403; am nächsten Tag (18.) → 6 Rechte, Selbst-Krankmeldung gelingt; Konto ohne Geburtsdatum mit Kennzeichen „volljährig“ = ja → ebenfalls 6 Rechte.

### R1.4 Wirkung der Volljährigkeit auf Schul-Abweichungen

Hinweis: Volljährige Schüler/innen behalten die zwei Rechte mit Umfang „Nur selbst“ auch dann, wenn die Schule dem Schüler-Profil das Recht entzogen hat (Regel REC-061).

## R2 Eigene Rollen der Schule

| Feld | Grenze | Regel |
|---|---|---|
| Name | 1 bis 80 Zeichen | Mehrfache Leerzeichen werden zusammengezogen. Eindeutig ohne Beachtung der Groß-/Kleinschreibung, gegen eingebaute Rollenbezeichnungen und gegen andere eigene Rollen |
| Kurzbeschreibung | max. 300 Zeichen | Wird beim Speichern auf 300 Zeichen gekürzt |
| Grundtyp | eine von 5 (R1.2) | Bestimmt die Grundrolle; nach Anlage unveränderlich |
| Vorlage | eine eingebaute oder eigene Rolle | Eine eigene Vorlage wird auf ihre eingebaute Vorlage aufgelöst; nach Anlage unveränderlich |
| Kennung | max. 20 Zeichen | Präfix `x-` plus ASCII-Name, gekürzt auf 18 Zeichen; ohne Name `rolle`; bei Kollision Zähler 2, 3, … (so gekürzt, dass 20 Zeichen nicht überschritten werden) |

Löschregeln eigener Rollen:

| Fall | Ergebnis |
|---|---|
| Keine Konten mit der Rolle | Löschen sofort; alle Abweichungen der Rolle werden entfernt |
| Konten vorhanden, keine Zielrolle | 409: „Die Rolle hat noch N Konto/Konten. Bitte eine Zielrolle wählen.“ |
| Zielrolle nicht gefunden oder gleich der gelöschten Rolle | 422 „Unbekannte Zielrolle“ |
| Zielrolle hat anderen Grundtyp | 422: „Die Zielrolle muss denselben Grundtyp haben“ |
| Zielrolle nicht verwaltbar | 422: „Konten dieser Zielrolle darf die Verwaltung nicht zuweisen.“ |
| Zielrolle ausgeblendet | 422 (im Altbestand wirkungslos, siehe REC-015) |
| Erfolg | Konten wechseln in die Zielrolle (Grundrolle und eigene Rolle). Protokoll nennt Name, Grundtyp, verschobene Konto-IDs, Zielrolle |

- **REC-009** (P1, Status: Ist) Eigene Rollen haben die Felder und Grenzen der Tabelle R2. Überlange Namen (> 80 Zeichen) werden mit 422 am Feld abgewiesen [unklar: Altbestand reagiert bei Überlänge nicht definiert; Standard für den Neubau: 422].
  Abnahme: Name „Vertretungs-Team“ (1×) anlegen → Kennung `x-vertretungs-team` (≤ 20 Zeichen); gleicher Name in anderer Schreibweise („VERTRETUNGS-TEAM“) → 409 „Name vergeben“; Name mit 81 Zeichen → 422; Beschreibung mit 400 Zeichen → gespeichert mit 300; zwei Rollen mit gleichem ASCII-Anfang → Kennungen erhalten Zähler 2, 3 und bleiben ≤ 20 Zeichen.

- **REC-010** (P1, Status: Ist) Anlage einer eigenen Rolle: Name, Kurzbeschreibung, Grundtyp, Vorlage. Die Rolle übernimmt die Standardrechte der Vorlage und eine **einmalige Kopie** der Abweichungen der Vorlage zum Anlagezeitpunkt (auch Abweichungen mit Erteilung „nein“). Spätere Änderungen an der Vorlage wirken nicht auf die Kopie. Die Rolle erhält keine Umfänge außer denen der Vorlage und ihrer Abweichungen. Protokoll: `role.create`.
  Abnahme: Vorlage `lehrer` mit Abweichung (Recht X entzogen) → neue Rolle hat X ebenfalls nicht; danach X der Vorlage wieder erteilen → neue Rolle behält „entzogen“; Anlage steht im Protokoll (`role.create`).

- **REC-011** (P2, Status: offen) Die Vorlage „Administration“ ist wählbar. Beim Anlegen zeigt der Dialog dieselben Warnungen (REC-047) für die übernommenen heiklen Rechte wie bei jeder Erteilung; im Altbestand werden ihre Rechte (auch Rechte-Verwaltung) ohne Warnung und ohne Selbstaussperr-Schutz kopiert (der Schutz gilt nur für die eingebaute Administration).
  Abnahme: Rolle mit Vorlage `admin` anlegen → Dialog listet die Warnungen für alle übernommenen Rechte mit Hinweis (z. B. `rights.manage`, `watch.read`) und speichert erst nach Bestätigung; Protokoll nennt die Vorlage.

- **REC-012** (P2, Status: Ist) Bearbeiten: nur Name und Kurzbeschreibung; Grundtyp und Vorlage sind nach der Anlage festgelegt; Namensprüfung wie bei Anlage. Protokoll: `role.update`.
  Abnahme: PUT mit geändertem Grundtyp → Feld ignoriert bzw. 422; Umbenennen auf Namen einer anderen Rolle → 409; Umbenennen schreibt `role.update`.

- **REC-013** (P0, Status: Ist) Löschen einer eigenen Rolle folgt der Löschregel-Tabelle R2 (Konten nur in eine Rolle **desselben Grundtyps** übertragbar, sonst 409/422; die Zielrolle darf eine eingebaute Rolle sein, z. B. bei Grundtyp Personal die Schulleitung). Der Dialog zeigt, wie viele Konten betroffen sind und wohin sie gehen. Protokoll: `role.delete` mit verschobenen Konto-IDs und Zielrolle.
  Abnahme: Rolle mit 3 Konten löschen ohne Zielrolle → 409 mit Text und Zahl 3; Zielrolle anderer Grundtyp → 422; gültige Zielrolle → alle 3 Konten haben danach Grundrolle und eigene Rolle der Zielrolle, die gelöschte Rolle samt Abweichungen ist weg, Protokoll nennt die 3 Konto-IDs.

- **REC-014** (P2, Status: Ist) Eingebaute Rollen lassen sich ausblenden (`role.hide`/`role.show`), aber nur solange sie keine Konten haben (sonst Fehler „Die Rolle hat noch Konten und lässt sich nicht ausblenden“) und nie die Administration. Ausgeblendete Rollen fehlen in der Rollenliste der Benutzerverwaltung und sind für neue Konten und Zuweisungen unbekannt (422). Eigene Rollen sind nicht ausblendbar.
  Abnahme: Rolle `hausmeister` ohne Konten ausblenden → fehlt in Rollenauswahl, Konto-Anlage mit dieser Rolle → 422; mit vorhandenem Konto → Fehler; `admin` ausblenden → abgelehnt; wieder einblenden → verfügbar.

- **REC-015** (P1, Status: offen) Die Prüfung „Zielrolle ist ausgeblendet“ beim Löschen einer eigenen Rolle muss am gespeicherten Ausblenden-Status der Rolle erfolgen (im Altbestand liefert die Rollenauskunft immer „nicht ausgeblendet“, die Prüfung greift nie).
  Abnahme: Eingebaute Rolle R ausgeblendet, eigene Rolle mit Konten gleichen Grundtyps löschen mit Zielrolle R → 422 „Unbekannte Zielrolle“; Konten bleiben unverändert.

- **REC-016** (P1, Status: Ist) Die Rollenliste der Benutzerverwaltung liefert die wirksame Matrix (eingebaute und eigene Rollen, ohne ausgeblendete) und je Rolle `manageable_by_me`. Die Liste verwaltbarer Rollen im Server ist maßgeblich; die Oberfläche spiegelt sie. Rollen, Bezeichnungen, Verwaltbarkeit, Zugangsbrief-Bezeichnungen, Anmelde-Richtlinien und Oberfläche beziehen die Rollenliste aus **einer** Quelle.
  Abnahme: Als Sekretariat: nur `schueler`, `eltern`, `schulbegleitung` mit `manageable_by_me` = ja; eine neue eigene Rolle erscheint ohne Codeänderung in Benutzerverwaltung, Zugangsbriefen und Anmelde-Richtlinien.

## R3 Zweige und Zuordnungen

| Feld Zweig | Grenze | Regel |
|---|---|---|
| Name | 1 bis 80 Zeichen | Eindeutig (409 „Ein Zweig mit diesem Namen existiert bereits“) |
| Standorte | max. 100 Einträge | Jeder Standort muss in den Schuldaten existieren (422) |
| Klassenstufen | max. 30 Einträge (ganze Zahlen) | Keine Prüfung gegen die Schuldaten |
| Klassen-IDs | max. 500 Einträge | Jede Klasse muss existieren (422) |

| Zuordnung | Gilt für Rolle | Prüfung |
|---|---|---|
| Zweige (IDs, mehrere) | abteilungsleitung | Unbekannter Zweig: 422 „Unbekannter Zweig: …“ |
| begleitete Kinder (Schüler-IDs, mehrere) | schulbegleitung | Unbekannte Schüler/innen: 422, bis zu 10 werden genannt |
| Kinder (mehrere) | eltern | Anlage und Änderung über das Konto selbst; Duplikate werden entfernt |

- **REC-017** (P1, Status: Ist) Zweige (Schulzweige/Abteilungen) mit den Feldern der Tabelle. Eine Klasse gehört zum Zweig, wenn ihre ID in der Klassenliste steht **oder** ihr Standort in den Standorten **oder** ihre Klassenstufe in den Klassenstufen. Konto und Zweig sind n:m verknüpft (mehrere Zweige je Konto; Anzeige nach Name sortiert). Wird ein Zweig gelöscht, verliert er alle Zuordnungen (keine Warnung). Protokoll: `branch.create`, `branch.update`, `branch.delete`.
  Abnahme: Zweig „Unterstufe“ mit Klassenstufen 5, 6 und Klasse 7a → Klassen 5x, 6x, 7a gehören dazu, 8a nicht; Doppelname → 409; Standort „X“ nicht in den Schuldaten → 422; Löschen entfernt Zuordnung aller Konten (Konto behält Rolle, verliert Zweig-Sicht).

- **REC-018** (P1, Status: Ist) Zuordnungen (Zweige, begleitete Kinder, Kinder) sind nur für die in der Tabelle genannten Rollen gültig; für andere Konten liefert die Zuordnungsroute 404. Die Zuordnungsliste zeigt nur Konten, die der Akteur verwalten darf (bei `rights.manage` alle). Änderungsrecht: `rights.manage` oder `users.manage` für das betreffende Konto; fremde Konten → 404. Protokoll: `rights.assign`.
  Abnahme: Zweig-Zuordnung auf ein Konto mit Rolle `lehrer` → 404; Sekretariat ordnet einer Schulbegleitung Kinder zu → 200; Sekretariat ordnet einer Abteilungsleitung einen Zweig zu → 404; unbekannter Zweig → 422; elf unbekannte Schüler-IDs → 422 mit genau 10 genannten.

- **REC-019** (P2, Status: Ist) Die Zweig-Sicht (`own_branch` = eigene Klassen plus Klassen der Zweige) gilt nur für Konten mit Grundrolle `abteilungsleitung`. Eigene Rollen mit Grundtyp Lehrkraft (Grundrolle `lehrer`) erhalten die Zweig-Klassen nicht, auch wenn ihre Vorlage die Abteilungsleitung ist [unklar: ob so gewollt; Standard bleibt Altbestand]. Eine Abteilungsleitung ohne Zweig hat keine Zweig-Sicht.
  Abnahme: Abteilungsleitung mit Zweig Z sieht Schüler aller Klassen von Z (`students.read`, Umfang eigener Zweig); ohne Zweig nur die eigenen Klassen; eigene Rolle (Grundtyp Lehrkraft, Vorlage Abteilungsleitung) sieht keine Zweig-Klassen.

## R4 Anzeige- und Nur-Lese-Rollen

- **REC-020** (P0, Status: Ist) Konten der Grundrolle `zuschauer` (und damit aller eigenen Rollen vom Grundtyp Ansicht) sind nur lesend. Jede schreibende Anfrage (POST, PUT, PATCH, DELETE) wird serverseitig mit 403 abgewiesen: „Ansichtskonto: Änderungen sind mit diesem Zugang nicht möglich.“ Ausnahmen: Abmelden und Kontoliste/Kontowechsel (`/auth/logout`, `/auth/accounts`). Das Konto zeigt in der Oberfläche ein Hinweisbanner.
  Abnahme: Als Zuschauer POST/PUT/PATCH/DELETE auf 20 verschiedene Fachrouten → jeweils 403 mit genanntem Text, keine Datenänderung; `POST /auth/logout` und Kontoliste → erlaubt; Banner sichtbar.

- **REC-021** (P1, Status: Ist) Erteilt die Schule einer Lese-Rolle ein Recht ausdrücklich (Abweichung mit Erteilung = ja), darf das Konto dafür schreiben; nur diese Erteilung gilt für die Änderung, die Standardrechte bleiben lesend. Das Änderungsprotokoll nennt bei Ansichtsrollen „schreiben erlaubt“ (Erteilung) bzw. „nur lesen“ (keine Erteilung). Erteilt wird mit Warnung (REC-050).
  Abnahme: Zuschauer-Rolle erhält ausdrücklich `announcement.post` → POST einer Mitteilung gelingt; POST auf `masterdata.edit`-Route (nur Standardrecht) → 403; Entzug der Erteilung → wieder 403; Protokollzeile zeigt „schreiben erlaubt“ bzw. „nur lesen“.

- **REC-022** (P0, Status: Ist) Anzeige-Sperre: Für die Anzeigerollen `zuschauer` und `monitor` bleibt eine Route mit 403 gesperrt, solange keines der geprüften Rechte ausdrücklich erteilt ist. Geschützt sind Atteste/Dokumente (Liste und Zusammenfassung), Förderkennzeichen der Schüler, Eltern-Kontakte einer Person und der Benachrichtigungs-Ausgang (Namen in Betreffzeilen).
  Abnahme: Als Zuschauer und als Monitor jeweils die vier Routen-Gruppen (Dokumente+Zusammenfassung, Förderkennzeichen, Eltern-Kontakte einer Schülerin, Benachrichtigungs-Ausgang) aufrufen → 403 (unabhängig davon, ob die ID existiert); nach ausdrücklicher Erteilung des geprüften Rechts → 200.

- **REC-023** (P0, Status: Ist) Die Zuschauer-Rolle erhält ausschließlich die 26 bewusst eingetragenen Rechte (Allowlist): plans.read_all, rooms.read, masterdata.read, masterdata.edit, timetable.generate, timetable.edit, substitution.read, substitution.edit, substitution.self_study, duties.manage, monitor.read, monitor.manage, students.read, register.read_all, exam.edit, exam.types.manage, support.catalog, announcement.post, messages.use, messages.broadcast, channels.use, channels.manage, channels.trash, teacher_requests.review, settings.edit, history.restore. Ausgeschlossen (Zweck): Gesundheits-, Förder-, Noten- und Lernstandsdaten, Atteste, gemeldete Chats und Nachrichten, Formular-Eingänge, Konten, Zugangsbriefe, Anmelderegeln, Protokolle, Schlüssel. Ein neues Recht erreicht die Rolle nur durch einen eigenen Eintrag. Die Rolle hat keine Umfänge (alle Einträge uneingeschränkt, nur lesend).
  Abnahme: Wirksame Rechte von `zuschauer` = exakt die 26; ein im Katalog neu hinzugefügtes Recht ist für `zuschauer` nicht erteilt; Rundgangs-Test: Zuschauer ruft alle Leseadressen des Systems auf → nur Adressen der erlaubten Rechte liefern Daten, alle anderen 403/404 gemäß R10; fremde Benutzerkonten → 404.

- **REC-024** (P2, Status: Ist) `monitor` ist Anzeigerolle (Anzeige-Sperre REC-022), aber nicht schreibgeschützt (nicht in der Nur-Lese-Liste); ihr einziges Standardrecht ist `monitor.read`; zeigt nur den Vertretungsplan, optional mit festem Standort. [unklar: Altbestand trennt „Anzeigerolle“ von „schreibgeschützt“; bleibt so, solange der Betreiber nichts anderes entscheidet.]
  Abnahme: Monitor-Konto: GET Monitoransicht 200; GET `/students/{id}/people` → 403; ein POST auf eine Route ohne erteiltes Recht → 403 (Rechtefehler, nicht „Ansichtskonto“-Text); Monitor-Menü bietet Konto wechseln, weiteres Konto, Abmelden, Standort wechseln.

## R5 Inhaber, Administration, eigenes Konto

- **REC-025** (P0, Status: Ist) **Inhaber-Konto**: das Konto mit dem Benutzernamen aus `SM_ADMIN_USER` (Standard `admin`); existiert es nicht, das älteste Administrationskonto. Die Ermittlung darf bis zu 60 s zwischengespeichert werden.
  Abnahme: `SM_ADMIN_USER` ungesetzt → Konto `admin` ist Inhaber; gesetzt auf „leitung“ → dieses Konto; fehlt das Konto → ältestes Administrationskonto (nach Anlagedatum); Wechsel wirkt spätestens nach 60 s.

- **REC-026** (P0, Status: Ist) **Inhaber-Schutz (direkter Weg)**: Ändernde Anfragen (POST, PUT, PATCH, DELETE) eines anderen Kontos auf das Inhaber-Konto (Konto-Route und Zuordnungsroute) werden mit 403 abgewiesen; der Versuch wird protokolliert (`user.owner_protected`). Meldung: „Nur der Inhaber selbst kann das Konto ändern, deaktivieren, löschen, sein Passwort oder seine Zwei-Faktor-Anmeldung zurücksetzen oder ihm Rechte entziehen.“ Gilt auch für die Administration (keine Ausnahme). Das Inhaber-Konto kann nicht beobachtet und nicht eingeschränkt werden (403).
  Abnahme: Zweiter Admin versucht je Inhaber herabstufen, deaktivieren, löschen, Passwort zurücksetzen, 2FA zurücksetzen, Rechte/Zuordnung ändern, Beobachtung setzen → jeweils 403 mit Meldung, Konto unverändert, je ein Protokolleintrag `user.owner_protected`; der Inhaber selbst darf sein eigenes Passwort ändern.

- **REC-027** (P0, Status: offen) Der Inhaber-Schutz gilt auf **allen** Wegen zentral im Konto-Dienst, nicht nur in der Konto-Route: auch Zugangsbrief-Stapel/Massen-Passwort-Zurücksetzen, Passwort-Zurücksetzen-Link/-Code durch die Verwaltung, API-Zugänge, CLI-Fremdzugriff über Schnittstellen, Importe und Sammelaktionen. Massen- und Einzelaktionen nutzen dieselbe Prüfung je Objekt. (Audit 17.10.: im Altbestand umging ein Massen-Reset über Zugangsbriefe den Schutz; Vorfall 16.10. mit gleichem Muster.)
  Abnahme: Als zweiter Admin (und als Sekretariat/Schulleitung mit Zugangsbrief-Recht) Stapel anlegen/Massen-Reset mit dem Inhaber-Konto in der Auswahl → Inhaber-Eintrag wird mit 403 abgewiesen bzw. nicht aufgenommen, Passwort des Inhabers unverändert, `user.owner_protected` protokolliert; dasselbe für `send-reset` und jeden weiteren Passwort-/2FA-ändernden Weg.

- **REC-028** (P3, Status: offen) Delegation: Der Inhaber kann einem zweiten Administrationskonto ausdrücklich das Recht geben, das Inhaber-Passwort zurückzusetzen. Betreiber-Wortlaut 17.10.: „Dem Admin soll man grundsätzlich nicht seine Admin-Rechte nehmen können. Das ist der einzige Account, den man nicht seine Rechte wegnehmen kann. Oder dessen Passwort man zurücksetzen kann. Es sei denn, es gibt einen zweiten Admin, dem der erste Admin den Zugang gegeben hat, seinen Password zurückzusetzen.“ Ohne diese ausdrückliche Delegation bleibt REC-026 unverändert. [unklar: Betreiber hat die Rückfrage „Soll ich das bauen?“ nicht beantwortet.]
  Abnahme: Ohne Delegation → 403 (REC-026); Inhaber delegiert an Admin B → B kann ausschließlich das Passwort des Inhabers zurücksetzen (alle Sitzungen enden, Pflichtwechsel), nicht herabstufen/löschen/deaktivieren; Delegation widerrufen → wieder 403; Delegation und Reset stehen im Audit.

- **REC-029** (P0, Status: Ist) **Letzter aktiver Administrator**: Herabstufen, Deaktivieren oder Löschen des letzten aktiven Administrationskontos → 409 (je Fall eigene Meldung; Herabstufen: „Der letzte aktive Admin kann nicht herabgestuft werden“).
  Abnahme: Einziger aktiver Admin: Herabstufen, Deaktivieren, Löschen → je 409 mit eigener Meldung; mit zweitem aktivem Admin → möglich (sofern nicht Inhaber, REC-026).

- **REC-030** (P0, Status: Ist) **Eigenes Konto**: Das eigene Konto deaktivieren, löschen, die eigene Rolle ändern oder das eigene Konto beobachten → jeweils 409 (Rollenänderung: „Die eigene Rolle kann nicht geändert werden“).
  Abnahme: Als beliebiger Verwalter die vier Aktionen auf das eigene Konto → je 409; Konto unverändert.

- **REC-031** (P0, Status: Ist) **Rollenwechsel** eines bestehenden Kontos (Umstellung ändert Grundrolle und eigene Rolle gemeinsam):

  | Regel | Ergebnis |
  |---|---|
  | Eigene Rolle des eigenen Kontos ändern | 409 |
  | Akteur darf Konten der **aktuellen** Rolle nicht verwalten | 404 (Konto nicht sichtbar) |
  | Akteur darf Konten der **neuen** Rolle nicht verwalten | 403 |
  | Ziel ist Administration, Akteur hat „keine Administrationskonten vergeben“-Sperre (REC-036) | 403, Protokoll `user.admin_grant_denied` |
  | Letzter aktiver Administrator soll herabgestuft werden | 409 |
  | Rolle unbekannt oder ausgeblendet | 422 „Unbekannte Rolle“ |
  | Zuordnungsdaten (Lehrkraft-Kürzel, Schüler-ID, Klasse) ungültig | 422 |

  Beim Wechsel weg von Eltern bleiben Kinder-Verknüpfungen bestehen [unklar: Umstellung entfernt sie im Altbestand nicht; Neubau: Verknüpfungen, die zur neuen Grundrolle nicht passen, werden beim Wechsel entfernt und protokolliert].
  Abnahme: Je Zeile der Tabelle ein Fall mit genanntem Ergebnis; Wechsel Eltern → Lehrkraft entfernt die Eltern-Kind-Verknüpfungen (Audit zeigt Anzahl).

- **REC-032** (P0, Status: Ist) **Verwaltbarkeit nach Umfang von `users.manage`**: Wer Konten welcher Grundrollen verwaltet, folgt dem Umfang des Rechts (auch bei eigenen Rollen über Vorlage und Abweichungen):

  | Umfang | Verwaltbare Grundrollen |
  |---|---|
  | Alle | alle 12 eingebauten Grundrollen |
  | Ohne Administration | alle außer `admin` (11) |
  | Nur Schüler/Eltern | `schueler`, `eltern`, `schulbegleitung` |
  | Recht nicht vorhanden | keine |

  Standard: ADM = Alle, SL = Ohne Administration, SEK = Nur Schüler/Eltern. Fremde, nicht verwaltbare Konten liefern 404; Anlage oder Zuweisung einer nicht verwaltbaren Rolle liefert 403.
  Abnahme: Sekretariat: GET Konto eines Lehrers → 404, Anlage eines Lehrer-Kontos → 403, Anlage eines Eltern-Kontos → 201; Schulleitung: Anlage eines Admin-Kontos → 403, GET Admin-Konto → 404; Admin: alles.

- **REC-033** (P0, Status: Ist) Passwort-Zurücksetzen und Zugangsbriefe: Zielkonten sind höchstens die, die der Akteur nach REC-032 verwalten dürfte, falls er `users.manage` hat; Akteure ohne `users.manage` (LEH, AL mit `passwords.reset`, Umfang Eigene Klassenleitung) erreichen nur Schüler/innen der eigenen Klassenleitung. Elternkonten setzen nur Sekretariat, Schulleitung, Administration zurück (ein Elternkonto kann mehrere Klassen betreffen). Nie das Inhaber-Konto (REC-026/027). [unklar: Altbestand vergibt `passwords.reset` an SL und SEK ohne Umfang; für Zugangsbriefe gilt dort laut Auswertung die Grenze der Konten-Verwaltung als Rückfall; Passwort-Route selbst nicht geprüft. Betreiber soll die engere Elternregel bestätigen.]
  Abnahme: Klassenleitung 5a: Reset einer Schülerin aus 5a → 200 (Einmalpasswort, Pflichtwechsel, alle Sitzungen des Kontos beendet, offene Codes ungültig); aus 5b → 404; Elternkonto → 404; Sekretariat: Elternkonto → 200, Lehrerkonto → 404; Schulleitung: Admin-Konto → 404.

## R6 Beobachtete Konten

- **REC-034** (P0, Status: Ist) Merkmal je Konto: beobachtet (ja/nein), optional „bis wann“ (muss in der Zukunft liegen, sonst 422), seit wann, wer es gesetzt hat. Der Zwischenspeicher der Merkmale beträgt höchstens 30 s und wird bei jeder Änderung geleert. Beobachtete Konten verlieren `watch.read` wirksam: sie sehen weder Menü noch Protokoll noch ihr eigenes Kennzeichen und können die Beobachtung nicht abschalten; Einsicht in die Beobachtung (Routen und Einstellung im eigenen Konto) → 404.
  Abnahme: Konto beobachten mit „bis“ in der Vergangenheit → 422; beobachtetes Konto ruft Beobachtungsliste und die Beobachtungs-Einstellung des eigenen Kontos auf → 404; Menü zeigt keinen Eintrag „Beobachtete Konten“; nach Ablauf von „bis“ ist das Konto spätestens 30 s später nicht mehr beobachtet.

- **REC-035** (P0, Status: Ist) Schalter „darf keine Administrationskonten anlegen oder Administrationsrechte vergeben“ je Konto (Standard bei beobachteten Konten: an). Ein Konto mit gesetztem Schalter darf keine Administrationskonten anlegen oder auf die Administration umstellen: 403 und Protokoll `user.admin_grant_denied`. Ausschalten kann den Schalter nur der Inhaber (sonst 403).
  Abnahme: Beobachtetes Konto mit Admin-Rolle legt ein Admin-Konto an → 403 + `user.admin_grant_denied`; stellt ein Konto auf `admin` um → 403; zweiter Admin schaltet den Schalter aus → 403; Inhaber schaltet aus → danach möglich.

- **REC-036** (P0, Status: Ist) Der Schalter aus REC-035 ist die Sperre in der Tabelle REC-031 („Ziel ist Administration“). Er wird zentral im Konto-Dienst geprüft und gilt für jeden Weg, der ein Konto mit Administrationsrolle erzeugt oder ein Konto auf die Administration umstellt (Anlage, Umstellung); Konten, die der Schalter nicht betrifft, dürfen Administrationskonten nur im Rahmen von REC-032 vergeben.
  Abnahme: Mit gesetztem Schalter: Anlage und Umstellung mit Rolle `admin` → je 403 + `user.admin_grant_denied`; Anlage einer Lehrkraft durch dasselbe Konto → erlaubt (sofern REC-032 es zulässt); Konto ohne Schalter (Admin) legt Admin-Konto an → erlaubt.

- **REC-037** (P0, Status: Ist) Protokollierung beobachteter Konten: jede Anfrage des Kontos (auch lesend); bei schreibenden Anfragen zusätzlich der Anfrage-Inhalt und die Audit-Einträge. Geheimnisse (Passwörter, Codes, Tokens, Schlüssel, Datei-Inhalte) werden geschwärzt. Inhalte werden verschlüsselt gespeichert. Grenzen: Anfrage-Inhalt max. 32 000 Bytes (mit Kürzungsvermerk), Textwert max. 4 000 Zeichen, Liste max. 200 Elemente; nicht lesbare Inhalte werden markiert. Aufbewahrung 180 Tage (einstellbar im Löschkonzept), danach Löschung. Ansicht: Liste der Konten, Detail mit Zeitleiste, Filter (Datum, Aktion, Status, Pfad), CSV-Export; Zugriff nur mit `watch.read`; Einträge zeigen Zeitpunkt, Aktion, Pfad (gekürzt), Status, Dauer.
  Abnahme: Beobachtetes Konto sendet POST mit Passwortfeld → Eintrag mit geschwärztem Passwort, Inhalt in der Datenbank nicht lesbar (verschlüsselt); Inhalt > 32 000 Bytes → gekürzt mit Vermerk; Eintrag älter als 180 Tage wird von der Wartung gelöscht; Aufruf der Ansicht ohne `watch.read` → 403 (beobachtetes Konto selbst: 404).

- **REC-038** (P0, Status: Ist) Setzen der Beobachtung: Recht `users.manage` für das Konto (sonst 403) **und** `watch.read` (sonst 404); Protokollaktion `user.watch_update` (ohne Inhalte). Reiter „Beobachtung“ in der Kontenverwaltung ist nur mit `watch.read` sichtbar. `watch.read` ist standardmäßig nur der Administration erteilt (Schulleitung zuweisbar) und gehört zum Selbstaussperr-Schutz (REC-053).
  Abnahme: Sekretariat ohne `watch.read` ruft die Beobachtungs-Einstellung → 404; Schulleitung ohne `watch.read` setzt Beobachtung → 404; Admin setzt → 200 und `user.watch_update` im Audit; eigenes Konto beobachten → 409.

- **REC-039** (P0, Status: offen) Zweck, Rechtsgrundlage und Information der Betroffenen für die Beobachtungsfunktion sind zu dokumentieren (Datenschutz-Unterlagen, Abstimmung mit Personalvertretung); Erkennbarkeit der Beobachtung für Betroffene wird nach Rechtsprüfung festgelegt. [unklar: Zweck und Rechtsgrundlage im Altbestand nicht dokumentiert; Audit 17.10.]
  Abnahme: Datenschutz-Dokumentation enthält einen Abschnitt „Beobachtete Konten“ mit Zweck, Rechtsgrundlage, Aufbewahrung (180 Tage) und Betroffenen-Information; ohne diesen Abschnitt ist die Funktion in Produktion nicht aktivierbar.

- **REC-040** (P1, Status: offen) Lesezugriffe auf das Beobachtungsprotokoll und deren CSV-Export werden selbst protokolliert (Wer, wann, welches Konto, ohne Inhalte).
  Abnahme: Ansicht eines Konto-Eintrags und CSV-Export durch Admin → je ein Audit-Eintrag mit Akteur, Zielkonto, Zeitpunkt.

## R7 Rechte-Katalog

### R7.1 Umfänge (Datenreichweite eines Rechts)

„Alle“ ist die Grundeinstellung ohne Einschränkung. Die übrigen Umfänge sind je Recht nur wählbar, wenn der Katalog sie für das Recht führt.

| Kennung | Bezeichnung | Bedeutung |
|---|---|---|
| `all` | Alle | Keine Einschränkung. Nur bei Rechten mit Umfangsauswahl wählbar; sonst bleibt es beim Standard |
| `own_classes` | Eigene Klassen | Klassen, die eine Lehrkraft unterrichtet (ein Kursteil genügt) oder als Klassenleitung führt. Bei Schüler/innen und Eltern die Klassen der Kinder. Bei Abteilungsleitung zusätzlich die Klassen des eigenen Zweigs |
| `own_courses` | Eigene Kurse | Kurse, in denen die Lehrkraft mindestens einen Kursteil unterrichtet |
| `class_teacher` | Eigene Klassenleitung | Nur Klassen, die als Klassenleitung in den Stammdaten eingetragen sind |
| `own_branch` | Eigener Zweig | Klassen des eigenen Zweigs (Zugehörigkeit siehe REC-017) |
| `own_lessons` | Eigene Stunden | Krankmeldung nur für die eigene Stunde (Kursteile, auch bei Vertretung) |
| `own` | Nur selbst | Nur die eigenen Daten |
| `own_children` | Eigene Kinder | Nur die Daten der verknüpften Kinder |
| `history_only` | Nur Verlauf | Nur der Versionsverlauf, keine weiteren Daten |
| `no_admins` | Ohne Administration | Konten aller Grundrollen außer der Administration |
| `students_parents` | Nur Schüler/Eltern | Konten der Grundrollen Schüler/in, Eltern und Schulbegleitung |

Es gibt keinen Umfang „Standort“; der Standort wirkt nur als Merkmal eines Zweigs.

### R7.2 Katalog (61 Rechte)

Spalten: **Standard-Rollen** nennt die Rollen, die das Recht im Standard haben; ein Umfang steht in Klammern, ohne Klammer gilt „Alle“. **Datenumfang** = wählbare Umfänge außer „Alle“ (– = nur uneingeschränkt). **Status**: aktiv = der Server prüft das Recht; geplant = angelegt und einstellbar, die Funktion prüft im Altbestand noch ein älteres Recht (Pflicht im Neubau: REC-044).

**Gruppe Pläne & Stammdaten (6)**

| Recht | Bedeutung | Standard-Rollen | Datenumfang | Status |
|---|---|---|---|---|
| `plans.read_all` | Klassen-, Lehrkraft- und Schülerpläne sehen | ADM, SL, SEK, PLA, ZUS; LEH (eigene Klassen); AL (eigener Zweig) | eigene Klassen, eigener Zweig | aktiv |
| `rooms.read` | Raumbelegung und Raumpläne; Lehrkräfte sehen Räume nur im eigenen Plan | ADM, SL, SEK, PLA, HM, ZUS | – | aktiv |
| `masterdata.read` | Lehrkräfte, Räume, Fächer, Klassen ansehen, ohne alle Pläne lesen zu dürfen | ADM, SL, SEK, PLA, ZUS | – | geplant |
| `masterdata.edit` | Lehrkräfte, Räume, Fächer, Klassen, Kurse anlegen und ändern | ADM, SL, SEK, PLA, ZUS | – | aktiv |
| `timetable.generate` | Automatische Planerstellung starten | ADM, PLA, ZUS | – | aktiv |
| `timetable.edit` | Stunden verschieben, Raum oder Lehrkraft ändern; schließt das Lesen aller Pläne ein | ADM, PLA, ZUS | – | aktiv |

**Gruppe Vertretung & Aufsicht (7)**

| Recht | Bedeutung | Standard-Rollen | Datenumfang | Status |
|---|---|---|---|---|
| `substitution.read` | Vertretungsplan der Schule. Schüler/innen und Eltern haben dieses Recht nicht; sie sehen Entfall, Vertretung und Raumänderung im eigenen Stundenplan | ADM, SL, SEK, PLA, LEH, AL, SB, ZUS | – | aktiv |
| `substitution.edit` | Abwesenheiten erfassen, Vertretungen planen und veröffentlichen | ADM, SL, SEK, PLA, ZUS | – | aktiv |
| `substitution.self_study` | Entscheidet, dass eine Klasse bei Ausfall allein arbeitet (ab welcher Klassenstufe, legt die Verwaltung fest); nicht die Lehrkraft selbst | ADM, SL, PLA, ZUS; AL (eigener Zweig) | eigener Zweig | geplant |
| `duties.manage` | Pausenbereiche, Verfügbarkeit der Lehrkräfte, faire Verteilung der Aufsichten | ADM, SL, PLA, ZUS | – | geplant |
| `absence.report_self` | Lehrkraft meldet sich selbst ab | LEH, AL | – | aktiv |
| `monitor.read` | Vertretungsmonitor und Aushang anzeigen | ADM, SL, SEK, PLA, HM, MON, ZUS | – | aktiv |
| `monitor.manage` | Anzeigetage, Laufband und Hinweise der Monitore | ADM, SL, SEK, ZUS | – | aktiv |

**Gruppe Schüler, Klassenbuch & Prüfungen (19)**

| Recht | Bedeutung | Standard-Rollen | Datenumfang | Status |
|---|---|---|---|---|
| `students.read` | Namen, Klassen, Kurse von Schüler/innen | ADM, SL, SEK, PLA, ZUS; LEH (eigene Klassen); AL (eigener Zweig) | eigene Klassen, eigener Zweig | aktiv |
| `students.birth_date` | Geburtsdatum setzen oder ändern; daraus ergibt sich die Volljährigkeit (Elternfreigabe, eigene Krankmeldung) | ADM, SL, SEK; LEH, AL (Eigene Klassenleitung) | Eigene Klassenleitung | aktiv |
| `register.read_all` | Gesamtes Klassenbuch einer Klasse. Fachlehrkräfte sehen nur eigene Stunden, Klassenleitung die ganze Klasse | ADM, SL, SEK, ZUS; AL (eigener Zweig) | eigener Zweig, Eigene Klassenleitung | geplant |
| `student_absence.report` | Krankmeldung für ein Kind eintragen (Eltern, Sekretariat, Lehrkraft für die eigene Stunde) | SEK; LEH (eigene Stunden); AL (eigener Zweig); ELT (eigene Kinder); SCH nur bei Volljährigkeit (nur selbst) | eigene Stunden, Eigene Klassenleitung, eigene Klassen, eigener Zweig, nur selbst, eigene Kinder | aktiv |
| `student_absence.read` | Krankmeldungen ansehen. Gesundheitsdaten: nie für die technische Administration | SL, SEK; LEH (Eigene Klassenleitung); AL (eigener Zweig); SCH (nur selbst); ELT (eigene Kinder) | Eigene Klassenleitung, eigene Klassen, eigener Zweig, nur selbst, eigene Kinder | aktiv |
| `student_documents.read` | Eingereichte Atteste und Dokumente. Gesundheitsdaten: nie für die technische Administration | SL, SEK; LEH, AL (Eigene Klassenleitung); SCH nur bei Volljährigkeit (nur selbst); ELT (eigene Kinder) | Eigene Klassenleitung, nur selbst, eigene Kinder | aktiv |
| `support.read` | Förderbedarf, Nachteilsausgleich und Nachweise; getrennt von den Schülerdaten | SL, SEK; LEH, AL (Eigene Klassenleitung) | Eigene Klassenleitung, eigener Zweig | aktiv |
| `support.manage` | Merkmale, Nachteilsausgleiche und Nachweise (PDF/Dateien) je Schüler/in eintragen und löschen | SL, SEK; LEH, AL (Eigene Klassenleitung) | Eigene Klassenleitung | aktiv |
| `support.catalog` | Festlegen, welche Arten von Nachteilsausgleich/Förderung es an der Schule gibt (z. B. Zeitzuschlag) | ADM, SL, SEK, ZUS | – | aktiv |
| `support.hints` | Bei Klausuren sehen, welche Schüler/innen welchen Nachteilsausgleich haben (ohne Diagnose und Nachweis) | SL, SEK; LEH, AL (eigene Kurse) | eigene Kurse | aktiv |
| `exam.edit` | Klausurtermine eintragen | ADM, SL, PLA, ZUS; LEH, AL (eigene Kurse) | eigene Kurse | aktiv |
| `exam.types.manage` | Welche Klausurarten es gibt (z. B. Klassenarbeit, Test) | ADM, SL, PLA, ZUS | – | geplant |
| `competency.read` | Kompetenzraster und Lernstand: Klassenübersicht, Lernpläne, Abzeichen, Lernentwicklungsbericht. Personenbezogen, nie für die technische Administration | SL; LEH (eigene Klassen); AL (eigener Zweig) | eigene Klassen, eigener Zweig | aktiv |
| `competency.assess` | Stufen je Kompetenz setzen, Selbsteinschätzungen bestätigen, Lernpläne führen, Abzeichen vergeben | SL; LEH (eigene Klassen); AL (eigener Zweig) | eigene Klassen, eigener Zweig | aktiv |
| `competency.manage` | Kompetenzrahmen (Bereiche, Kompetenzen, Niveaustufen) anlegen, importieren, ändern; Schul-Abzeichen festlegen; ohne Einblick in Lernstände | SL, LEH, AL | – | aktiv |
| `gradebook.use` | Noten, Leistungsarten und Gewichtung im Notenbuch eigener Kurse eintragen; Halbjahresnoten festlegen und sperren. Nie für die technische Administration | SL; LEH, AL (eigene Kurse) | eigene Kurse | aktiv |
| `gradebook.read_class` | Notenübersicht, Notenkonferenz-Liste und Versetzungswarnung der Klasse (lesend) | SL; LEH, AL (Eigene Klassenleitung) | Eigene Klassenleitung, eigener Zweig | aktiv |
| `gradebook.manage` | Notenskalen, Notenschlüssel, Einsicht für Schüler/innen und Versetzungswarnung der Schule festlegen; gesperrte Notenbücher wieder öffnen; sieht alle Notenbücher | SL | – | aktiv |
| `gradebook.export` | Gesperrte Halbjahres- und Zeugnisnoten als CSV für SchILD, ASV oder LUSD ausgeben | SL, SEK | – | aktiv |

**Gruppe Kommunikation & Kursräume (13)**

| Recht | Bedeutung | Standard-Rollen | Datenumfang | Status |
|---|---|---|---|---|
| `forms.submit` | Schulformulare online ausfüllen (z. B. Beurlaubung, Einverständnis); die Zielgruppe des Formulars bestimmt, welche Formulare sichtbar sind | SL, SEK, LEH, AL, SCH, ELT | – | aktiv |
| `forms.inbox` | Einreichungen ansehen, genehmigen, exportieren; enthält teils Gesundheitsdaten; nie für die technische Administration | SL, SEK; LEH, AL (Eigene Klassenleitung) | Eigene Klassenleitung | aktiv |
| `forms.manage` | Formular-Vorlagen anlegen, Ablauf und Aktionen festlegen, Bibliothek übernehmen; ohne Einblick in ausgefüllte Formulare | ADM, SL, SEK | – | aktiv |
| `announcement.post` | Schwarzes Brett und Aushang | ADM, SL, SEK, PLA, ZUS; LEH (eigene Klassen); AL (eigener Zweig) | eigene Klassen, eigener Zweig | aktiv |
| `messages.use` | Interne Nachrichten senden und lesen; wer wem schreiben darf, regeln die Schuleinstellungen | ADM, SL, SEK, PLA, LEH, AL, HM, SCH, ELT, ZUS | – | aktiv |
| `mail.custom_server` | Im Postfach ein E-Mail-Konto mit eigenem IMAP-/SMTP-Server verbinden (bekannte Anbieter stehen allen mit Postfach offen); nur für Personal gedacht | ADM, SL, SEK | – | aktiv |
| `messages.broadcast` | Nachrichten an Klassen, Kurse, Kollegium oder alle | ADM, SL, SEK, PLA, ZUS; LEH (eigene Klassen); AL (eigener Zweig) | eigene Klassen, eigener Zweig | aktiv |
| `messages.moderate` | Gemeldete Nachrichten ansehen und bearbeiten | ADM, SL | – | aktiv |
| `chats.review` | Gemeldete Chat-Auszüge nur mit Einwilligung von Kind bzw. Eltern lesen | SL | – | geplant |
| `channels.use` | Material, Aufgaben und Pinnwand der Kursräume | ADM, SL, LEH, AL, SB, SCH, ZUS | – | aktiv |
| `channels.view_children` | Freigegebenes Material und Aufgaben der Kursräume der eigenen Kinder; welche Bereiche, regelt die Schule | ELT (eigene Kinder) | eigene Kinder | aktiv |
| `channels.manage` | Ordner, Material, Freigaben, Aufgaben | ADM, SL, ZUS; LEH, AL (eigene Kurse) | eigene Kurse | aktiv |
| `channels.trash` | Gelöschtes Material, Aufgaben und Ordner wiederherstellen oder endgültig löschen (Aufbewahrung `trash_retention_days`, Standard 30 Tage) | ADM, SL, ZUS; LEH, AL (eigene Kurse) | eigene Kurse | aktiv |

**Gruppe Konten & Profile (4)**

| Recht | Bedeutung | Standard-Rollen | Datenumfang | Status |
|---|---|---|---|---|
| `users.manage` | Benutzerkonten anlegen, ändern, sperren | ADM (Alle); SL (Ohne Administration); SEK (Nur Schüler/Eltern) | Ohne Administration, Nur Schüler/Eltern | aktiv |
| `passwords.reset` | Passwort auf das Startpasswort oder ein selbst gesetztes zurücksetzen | ADM, SL, SEK; LEH, AL (Eigene Klassenleitung) | Eigene Klassenleitung, Nur Schüler/Eltern | aktiv |
| `profile.teacher_self` | Fächer, Klassen, Stunden und Zeiten selbst pflegen (als Antrag) | LEH, AL | – | aktiv |
| `teacher_requests.review` | Anträge von Lehrkräften genehmigen oder ablehnen | ADM, SL, PLA, ZUS | – | aktiv |

**Gruppe Verwaltung & System (12)**

| Recht | Bedeutung | Standard-Rollen | Datenumfang | Status |
|---|---|---|---|---|
| `settings.edit` | Schulweite Einstellungen (auch die Regeln des Postfachs und die Vorgaben der Benachrichtigungen) | ADM, SL, PLA, ZUS | – | aktiv |
| `rights.manage` | Die Seite „Rollen & Rechte“ bearbeiten (nur Administration und Schulleitung vorgesehen) | ADM, SL | – | aktiv |
| `login_policy.manage` | Passwortregeln, Zwei-Faktor-Anmeldung, Anmeldedienste, Anmelde-Richtlinien, IP-Sperren aufheben | ADM, SL | – | aktiv |
| `audit.read` | Audit-Protokoll aller Änderungen | ADM, SL | – | aktiv |
| `watch.read` | Verstärkte Protokollierung einzelner Konten einsehen und einschalten; ein beobachtetes Konto hat dieses Recht nie, auch nicht als Administration | ADM | – | aktiv |
| `privacy.manage` | Aufbewahrungsfristen einstellen, Warteliste der Ausgetretenen, Vorschau „Was würde gelöscht“, Löschprotokoll ohne Inhalte | ADM, SL | – | aktiv |
| `privacy.subject` | Auskunft für eine Person erzeugen (Art. 15/20) und eine Person sofort löschen (Art. 17); enthält Gesundheits- und Notendaten | SL | – | aktiv |
| `history.restore` | Versionsverlauf ansehen, Stand wiederherstellen | ADM, SL, ZUS; PLA (nur Verlauf) | nur Verlauf | aktiv |
| `system.admin` | Sicherungen, Schlüssel, Demo-Daten | ADM | – | aktiv |
| `license.manage` | Lizenzstand sehen, neue Lizenz einspielen und online prüfen, auch bei wegen Ablaufs gesperrter Anwendung; erhält Vorwarnungen vor dem Ablauf | ADM, SL | – | aktiv |
| `api.own` | Zugänge für Apps oder KI-Werkzeuge ausgeben (nur lesend, mit Bereichen und Filtern), höchstens mit dem, was das eigene Konto sehen darf; Gesundheits- und Förderdaten sind nie freigebbar | ADM, SL, SEK, PLA, LEH, AL | – | aktiv |
| `api.manage` | Alle API-Zugänge der Schule einsehen, deren Nutzung prüfen und widerrufen | ADM, SL | – | aktiv |

**Standardumfänge je Rolle (außer „Alle“)**

| Rolle | Einschränkungen im Standard |
|---|---|
| ADM | keine |
| SL (1) | `users.manage` = Ohne Administration |
| SEK (1) | `users.manage` = Nur Schüler/Eltern |
| PLA (1) | `history.restore` = Nur Verlauf |
| LEH (20) | eigene Kurse: `exam.edit`, `channels.manage`, `channels.trash`, `support.hints`, `gradebook.use` · eigene Klassen: `announcement.post`, `students.read`, `plans.read_all`, `messages.broadcast`, `competency.read`, `competency.assess` · Eigene Klassenleitung: `student_absence.read`, `student_documents.read`, `support.read`, `support.manage`, `passwords.reset`, `students.birth_date`, `forms.inbox`, `gradebook.read_class` · eigene Stunden: `student_absence.report` |
| AL (22) | eigene Kurse: `exam.edit`, `channels.manage`, `channels.trash`, `support.hints`, `gradebook.use` · eigener Zweig: `announcement.post`, `students.read`, `student_absence.read`, `student_absence.report`, `plans.read_all`, `messages.broadcast`, `register.read_all`, `substitution.self_study`, `competency.read`, `competency.assess` · Eigene Klassenleitung: `student_documents.read`, `support.read`, `support.manage`, `passwords.reset`, `students.birth_date`, `forms.inbox`, `gradebook.read_class` |
| SCH (3) | Nur selbst: `student_absence.read`; `student_absence.report` und `student_documents.read` (beide nur bei Volljährigkeit) |
| ELT (4) | Eigene Kinder: `student_absence.read`, `student_absence.report`, `student_documents.read`, `channels.view_children` |
| HM, SB, MON, ZUS | keine (bei SB für `substitution.read` und `channels.use` auffällig, da die Rolle an begleitete Kinder gebunden ist, siehe REC-059) |

### R7.3 Anforderungen Katalog

- **REC-041** (P0, Status: Ist) Der Rechte-Katalog (Tabellen R7.2) mit 61 Rechten in 6 Gruppen ist die **einzige Quelle** für Rechte: Kennung, Bezeichnung, Gruppe, Wirkung, wählbare Umfänge, Status. Die Rechte-Matrix, Standardrechte je Rolle, Umfangslisten, Oberflächentypen und die Matrix-Dokumentation leiten sich daraus ab; ein Test vergleicht Dokumentation und Katalog.
  Abnahme: Katalog enthält genau 61 Rechte mit Gruppenzahlen 6/7/19/13/4/12; die in dieser Spezifikation geführte Matrix (Abschnitt R7.2) stimmt im Test zeichengenau mit dem Katalog überein; ein Recht, das nur im Code, nicht im Katalog steht, lässt den Test fehlschlagen.

- **REC-042** (P0, Status: Ist) Umfänge nach Tabelle R7.1. Ein Umfang ist nur wählbar, wenn der Katalog ihn für das Recht führt; „Alle“ ist bei Rechten ohne Umfangsauswahl nicht wählbar (bleibt Standard). Die Umfangslogik (eigene Klassen, eigene Kurse, Klassenleitung, Zweig, Stunden, Kinder) ist **eine** zentrale Stelle; jede Route wendet sie an, fremde Datensätze liefern 404.
  Abnahme: Umfang `own_branch` für `gradebook.manage` setzen → 422 „Umfang … ist bei … nicht möglich“; Lehrkraft mit `students.read` (eigene Klassen) fragt Schüler einer fremden Klasse → 404, einer Klasse mit einem einzigen Kursteil der Lehrkraft → 200; Wechsel des Umfangs auf „Alle“ (bei Recht mit Auswahl) hebt die Einschränkung sofort auf.

- **REC-043** (P0, Status: Ist) Standardrechte und Standardumfänge je Rolle entsprechen den Spalten „Standard-Rollen“ und der Tabelle „Standardumfänge“. Mit „Zurücksetzen“ einer Rolle gilt wieder genau dieser Zustand.
  Abnahme: Je Rolle: Abweichungen anlegen, „Zurücksetzen“ → wirksame Rechte und Umfänge exakt wie Standard, Antwort nennt die Zahl gelöschter Abweichungen; Zähltest LEH 20 und AL 22 Umfangs-Einschränkungen, SCH 3, ELT 4, SL/SEK/PLA je 1.

- **REC-044** (P1, Status: offen) Jedes Recht des Katalogs wird von genau der Funktion geprüft, die es beschreibt. Für die sechs im Altbestand „geplanten“ Rechte (`masterdata.read`, `substitution.self_study`, `duties.manage`, `register.read_all`, `exam.types.manage`, `chats.review`) ist das im Neubau Pflicht; im Altbestand prüft die Funktion noch ein älteres Recht. Der Status „geplant“ entfällt in der Matrix, sobald die Funktion das Recht prüft. [unklar: Altbestand führt zusätzlich `license.manage` und Förderdaten-Rechte in einer Liste noch ersatzgeprüfter Funktionen, im Katalog aber als „aktiv“.]
  Abnahme: Für jedes der 61 Rechte existiert ein Test: Rolle ohne das Recht → zugehörige Funktion 403/404 (je R10); Rolle mit dem Recht → erlaubt; insbesondere `license.manage` entzogen → Lizenzseiten 403 (auch wenn `system.admin` vorhanden), `masterdata.read` allein → Stammdatenlisten lesbar, Pläne nicht.

- **REC-045** (P0, Status: Ist) Default-Deny für neue Funktionen: Jede neue Route/Funktion braucht einen Bereich, eine zentrale Rechteprüfung und eine maschinenlesbare Beschreibung; Routen ohne Bereich oder ohne Rechteprüfung lassen einen Test fehlschlagen; neue Leseroute, die ein Ansichtskonto erreichen kann, braucht einen ausdrücklichen Eintrag (freigegeben oder gesperrt). Ein neues Recht verlangt Katalog-Eintrag, Standard je Rolle, Umfang, Oberflächentyp und Matrix-Dokumentation.
  Abnahme: Testlauf mit einer Route ohne Bereich → Test rot; Zuschauer ruft neue, nicht eingetragene Leseroute auf → Test rot bzw. 403; neues Recht ohne Matrix-Dokumentation → Test rot.

## R8 Regeln zur freien Rechtevergabe

### R8.1 Heikle Rechte (vorgesehene Rollen; sonst Hinweis)

| Recht | Vorgesehen für | Hinweis (Kern) |
|---|---|---|
| `system.admin` | ADM | Systemverwaltung (Sicherungen, Schlüssel) ist für die Administration gedacht |
| `rights.manage` | ADM, SL | Wer Rechte verwaltet, kann sich selbst alles erteilen |
| `license.manage` | ADM, SL | Lizenz: Administration und Schulleitung |
| `login_policy.manage` | ADM, SL | Anmelderegeln |
| `audit.read` | ADM, SL | Protokoll nennt Personen und Änderungen |
| `watch.read` | ADM, SL | Beobachtete Konten: Inhaber/Administration und Schulleitung |
| `privacy.manage` | ADM, SL | Löschkonzept |
| `privacy.subject` | SL | Auskunft und Sofort-Löschen enthalten Gesundheits- und Notendaten |
| `users.manage` | ADM, SL, SEK | Konten verwalten (Passwörter, Rollen) ist für Verwaltungsrollen gedacht |
| `student_documents.read` | SL, SEK, LEH, AL, SCH, ELT | Atteste sind Gesundheitsdaten |
| `support.read`, `support.manage`, `support.hints` | SL, SEK, LEH, AL | Förderdaten sind sensibel |
| `forms.inbox` | SL, SEK, LEH, AL | Ausgefüllte Formulare enthalten teils Gesundheitsdaten |
| `forms.manage` | ADM, SL, SEK | Formulare gestalten |
| `competency.read`, `competency.assess`, `competency.manage` | SL, LEH, AL | Lernstände sind personenbezogen / werden von Lehrkräften und Leitung eingetragen / Kompetenzrahmen pflegen Lehrkräfte und Leitung |
| `chats.review` | SL | Gemeldete Chats liest nur die Schulleitung, mit Einwilligung |
| `mail.custom_server` | ADM, SL, AL, PLA, SEK, LEH | Eigene Mailserver sind für Personal-Konten gedacht, sonst wäre der Server als Netzwerk-Scanner nutzbar |
| `api.own` | ADM, SL, AL, PLA, SEK, LEH | API-Zugänge geben üblicherweise nur Personal-Konten aus |
| `api.manage` | ADM, SL | Alle API-Zugänge verwalten |
| `gradebook.use`, `gradebook.read_class` | SL, LEH, AL | Noten sehen und führen / Noten einer Klasse sehen |
| `gradebook.manage` | SL | Das Notenbuch der Schule verwaltet die Schulleitung |
| `gradebook.export` | SL, SEK | Noten exportieren |

### R8.2 Zweck-Listen je Grundrolle (Warnung für alles außerhalb von Zweck und Standard)

| Grundrolle | Zweck (ohne Warnung zulässig) | Zweck-Text |
|---|---|---|
| `schueler` | student_absence.read, channels.use, messages.use, forms.submit | Schüler/innen sehen üblicherweise nur eigene Daten |
| `eltern` | student_absence.report, student_absence.read, student_documents.read, messages.use, channels.use, channels.view_children, forms.submit | Eltern sehen üblicherweise nur die eigenen Kinder |
| `schulbegleitung` | channels.use, messages.use, student_absence.read, substitution.read | Schulbegleitung hat üblicherweise keine Elternrechte (keine Krankmeldung, keine Atteste) |
| `hausmeister` | rooms.read, monitor.read, monitor.manage, messages.use | Haustechnik bekommt üblicherweise keine Schüler- oder Personaldaten |
| `monitor` | monitor.read | Ein Monitor zeigt üblicherweise nur den Vertretungsplan |
| `zuschauer` | die 26 Rechte der Allowlist (REC-023) | Ansichtskonten sehen üblicherweise keine Gesundheits-, Noten-, Konto- oder Protokolldaten |

### R8.3 Verboten-Hinweise (Standard-Ausschluss)

- **Administration** (Hinweis „Gesundheits- und Personaldaten sieht die technische Administration üblicherweise nie“) bei 20 Rechten: `absence.report_self`, `student_absence.report`, `student_absence.read`, `profile.teacher_self`, `student_documents.read`, `support.read`, `support.manage`, `support.hints`, `chats.review`, `channels.view_children`, `forms.submit`, `forms.inbox`, `competency.read`, `competency.assess`, `competency.manage`, `gradebook.use`, `gradebook.read_class`, `gradebook.manage`, `gradebook.export`, `privacy.subject`. Diese 20 Rechte gehören nicht zu den Standardrechten der Administration.
- **Schüler/innen** (zwei Hinweise): `student_absence.report` – Standard ist nur die Selbstmeldung volljähriger Schüler/innen, mit dem Recht dürfen es alle Schüler/innen dieser Rolle; `student_documents.read` – Standard ist nur die Einreichung durch volljährige Schüler/innen, mit dem Recht alle Schüler/innen dieser Rolle.

### R8.4 Anforderungen freie Vergabe

- **REC-046** (P1, Status: Ist) **Grundsatz freie Vergabe** (Entscheidung Betreiber 16./17.10.2026): Jede Rolle kann jedes Recht des Katalogs bekommen können; die Standardrechte jeder Rolle bleiben unverändert. Wunsch-Wortlaut 16.10.: „Ich will, dass alle Rollen alle Berechtigungen rein theoretisch kriegen können.“ Verboten sind nur die harten Ablehnungen (REC-052) und die Selbstaussperrung (REC-053); alles andere wird mit **Warnung statt Verbot** (REC-047/048) vergeben. Die Datenobergrenze (REC-059) und die Hartgrenzen aus R9 bleiben davon unberührt.
  Abnahme: Für alle 12 Rollen und mindestens je 5 Rechte außerhalb des Standards (darunter `gradebook.use` für ELT, `rights.manage` für HM, `student_documents.read` für ADM) lässt sich die Erteilung nach Bestätigung speichern; keine dieser Erteilungen scheitert mit Fehler 4xx.

- **REC-047** (P0, Status: Ist) **Warnung bestimmen**, in dieser Reihenfolge, für die Grundrolle der Rolle (bei eigenen Rollen die Grundrolle des Grundtyps [unklar: ob der Altbestand bei eigenen Rollen zusätzlich die Vorlage berücksichtigt]): (1) Ist das Recht für die Grundrolle als Verboten-Hinweis hinterlegt (R8.3), gilt dieser Text. (2) Hat die Grundrolle eine Zweck-Liste (R8.2) und liegt das Recht weder dort noch im Standard der Rolle, gilt der Zweck-Text. (3) Ist das Recht heikel (R8.1) und gehört die Grundrolle nicht zu den vorgesehenen Rollen, gilt der Hinweistext. (4) Sonst keine Warnung. Die Liste „sensibler Rechte für Schüler-, Eltern- und Ansichtsrollen“ (24 Rechte) des Altbestands wird nicht ausgewertet und entfällt.
  Abnahme: ADM erhält `student_documents.read` → Verboten-Hinweis (Schritt 1); SCH erhält `gradebook.use` → Zweck-Text „Schüler/innen sehen üblicherweise nur eigene Daten“ (Schritt 2); PLA erhält `rights.manage` → Hinweis „Wer Rechte verwaltet, kann sich selbst alles erteilen“ (Schritt 3); SL erhält `rights.manage` (Standard) → keine Warnung (Schritt 4); HM erhält `monitor.manage` → keine Warnung (Zweck-Liste).

- **REC-048** (P0, Status: Ist) **Warn-Dialog**: Vor dem Erteilen eines Rechts mit Warnung fragt die Oberfläche als App-Dialog (kein Browser-Popup) nach und zeigt den Warntext; gespeichert wird erst nach ausdrücklicher Bestätigung. Eine Warnung ist ein Hinweis, kein Verbot. Der Server liefert die Warnung je Zelle der Matrix (`warning`), die Bestätigung gilt je Speichervorgang. Die erteilte Abweichung steht im Änderungsprotokoll (REC-056).
  Abnahme: Matrix: Zelle SCH × `gradebook.use` anklicken → Dialog mit Zweck-Text, „Abbrechen“ → keine Änderung, „Bestätigen“ + Speichern → Abweichung gespeichert und protokolliert; Tastatur: Dialog per Esc schließbar, Fokus im Dialog; kein `window.confirm`.

- **REC-049** (P1, Status: Ist) Die 26 heiklen Rechte mit vorgesehenen Rollen und Hinweisen entsprechen Tabelle R8.1; die Hinweistexte stehen nur dort (eine Quelle).
  Abnahme: Je Zeile der Tabelle R8.1: Erteilung an eine nicht vorgesehene Grundrolle liefert den Hinweis, Erteilung an eine vorgesehene keinen; Tabelle ist im Test gegen die Konfiguration abgeglichen.

- **REC-050** (P1, Status: Ist) Zweck-Listen je Grundrolle nach Tabelle R8.2. Lese-Rollen (Zuschauer) mit ausdrücklich erteiltem Schreibrecht erhalten zusätzlich den Hinweis, dass nur die ausdrückliche Erteilung schreibend wirkt (REC-021).
  Abnahme: Je Grundrolle der Tabelle: Recht außerhalb Zweck/Standard → Zweck-Text; Recht innerhalb → keine Warnung; Zuschauer × `masterdata.edit` ausdrücklich → Hinweis auf Schreibwirkung.

- **REC-051** (P1, Status: Ist) Verboten-Hinweise nach R8.3 (Administration 20, Schüler/in 2) werden angezeigt und gelten als Hinweis, nicht als Verbot. [unklar: harte Grenze, siehe REC-060.]
  Abnahme: Alle 20 Rechte der Administration zeigen den Hinweis; Schüler-Rolle × `student_absence.report` zeigt den Schüler-Hinweis (alle Schüler/innen der Rolle dürfen dann selbst melden).

- **REC-052** (P0, Status: Ist) **Harte Ablehnungen** (Änderung nicht möglich): unbekannte Rolle oder unbekanntes Recht → Fehler; Umfang „Alle“ oder ein anderer Umfang bei einem Recht ohne Umfangsauswahl → Fehler „Umfang … ist bei … nicht möglich“; Entzug einer durch REC-053 geschützten Kombination → Fehler. Abweichungen mit Erteilung = nein dürfen einen Umfang tragen, der Umfang wird ignoriert.
  Abnahme: PUT mit unbekanntem Recht → 422; Umfang `all` bei `rights.manage` → 422; `rights.manage` der Administration entziehen → 422; Erteilung „nein“ mit Umfang → 200, Umfang wirkungslos.

- **REC-053** (P0, Status: Ist) **Selbstaussperr-Schutz** (einzige feste Regel bei der Vergabe): Die eingebaute Administration (Grundrolle `admin`) behält immer `rights.manage`, `users.manage`, `license.manage`, `watch.read`; sie sind fest vergeben, in der Matrix mit Schloss gekennzeichnet („Schutz vor Selbstaussperrung: Die Administration behält Rechte-, Konten- und Lizenzverwaltung.“) und nicht entziehbar. Der Schutz gilt nur für die eingebaute Administration; eigene Rollen kennen ihn nicht.
  Abnahme: Entzug einer der vier Rechte von `admin` über Rechte-Seite oder Schnittstelle → abgelehnt; ein direkt in der Datenbank gespeicherter Entzug wird bei der Berechnung ignoriert (Recht bleibt wirksam); eigene Rolle mit Vorlage Administration: Entzug von `rights.manage` möglich; Zelle zeigt Schloss nur bei `admin`.

- **REC-054** (P0, Status: Ist) **Wirksame Rechte** werden bei jeder Anfrage in dieser Reihenfolge berechnet: (1) Standardrechte und Standardumfänge der Vorlage (bei eigenen Rollen die gewählte eingebaute Rolle), (2) Abweichungen der Schule unter der Kennung der Rolle; gespeicherte Abweichungen, die die Regeln heute nicht mehr erlauben, werden dabei still ignoriert, (3) Selbstaussperr-Schutz ergänzen, (4) volljährige Schüler/innen erhalten `student_absence.report` und `student_documents.read` mit Umfang „Nur selbst“ (REC-008/061). Änderungen wirken sofort, ohne Neustart.
  Abnahme: Fester Satz Abweichungen (davon eine ungültige) → wirksame Rechte stimmen mit dem Erwartungswert überein, die ungültige fehlt ohne Fehlermeldung; Änderung im Browser A ist in Browser B bei der nächsten Anfrage wirksam.

- **REC-055** (P1, Status: Ist) **Änderungsformat**: Je Recht eine Abweichung mit `granted` (Standard ja) und `scope`; Tabelle `role_overrides` (Spalten `role`, `permission`, `granted`, `scope`, `updated_at`, `updated_by`); keine Zeile = Standard. Umfang leer = Standardumfang der Vorlage; `all` hebt die Einschränkung auf; Eintrag `null` setzt das Recht auf Standard zurück. Eine ungültige Änderung lehnt die **gesamte** Änderung ab (Rollback, 422). „Zurücksetzen“ einer ganzen Rolle löscht alle Abweichungen und nennt deren Zahl.
  Abnahme: Änderung mit drei gültigen und einem ungültigen Recht → 422, keine der drei wirkt; `null` für ein Recht → Zeile verschwindet, Standard gilt; Zurücksetzen einer Rolle mit 7 Abweichungen → Antwort 7, Tabelle ohne Zeilen dieser Rolle.

- **REC-056** (P0, Status: Ist) **Protokoll der Rechteänderungen**: Aktionen `rights.update`, `rights.reset`, `rights.assign`, `role.hide`, `role.show`, `role.create`, `role.update`, `role.delete`, `branch.create`, `branch.update`, `branch.delete`, `user.update`, `user.delete`, `user.owner_protected`, `user.admin_grant_denied`, `user.watch_update` (16); Kontoanlage und -änderung (`user.create`, `user.update`) nennen `role_id`. Je Recht steht „vorher → nachher“, jeweils „nein“ (kein Recht), „ja“ (ohne Einschränkung) oder die Umfangsbezeichnung. Inhalte (Passwörter, Texte) stehen nie im Protokoll.
  Abnahme: Änderung `student_documents.read` bei LEH von „Eigene Klassenleitung“ auf „ja“ → Zeile „student_documents.read: Eigene Klassenleitung → ja“; Rolle zurücksetzen → `rights.reset`; Rolle löschen mit Konten → `role.delete` mit `moved` und `move_to`; Passwortänderung durch Verwaltung → `user.update` mit „password: gesetzt“ ohne Wert.

- **REC-057** (P1, Status: Ist) **Zugriff auf die Rechte-Seite**: Ansehen mit `rights.manage`, `users.manage` oder `audit.read` (eines genügt); Ändern von Rollen, Rechten, eigenen Rollen, Zweigen, Zuordnungen nur mit `rights.manage` (Zuordnungen auch mit `users.manage` für das betreffende Konto). Standard: Administration und Schulleitung.
  Abnahme: Sekretariat (hat `users.manage`) → Rechte-Seite lesbar, `PUT` auf Rolle → 403; Planer ohne eines der drei Rechte → 403 auf die Seite; Schulleitung ändert Rolle → 200.

- **REC-058** (P1, Status: Ist) **Rechte-Seite** unter Verwaltung (`/rechte`) mit Reitern Matrix, Rollen, Zweige, Zuordnungen. Matrix = Recht × Rolle (Rollen als Spalten), gruppiert in 6 einklappbare Gruppen (nicht 61 einzelne Schaltflächen), zeigt Standard und wirksam; Zellenzustände: erlaubt, nicht erlaubt, Schloss (nur Selbstaussperr-Schutz), Warnhinweis, Markierung „explizit“ (Abweichung vom Standard), geändert/vorgemerkt bis zum Speichern, Status „geplant“ je Recht. Rollen-Reiter: Hilfetext je Rolle, Dialoge zum Anlegen/Ändern/Löschen (Löschen zeigt Konten und Zielrolle), Ausblenden und Zurücksetzen je Rolle. Der Einrichtungsassistent (Schritt „Rollen & Rechte“) verweist hierher und stellt die Fragen: Gibt es Abteilungen oder Zweige? Welche Klassen gehören dazu? Sollen Lehrkräfte Mitteilungen an alle Klassen senden? Wer prüft gemeldete Nachrichten? Wer verteilt Aufsichten? Texte in Sie-Form, Erklärungen nur über Hilfe-Symbol.
  Abnahme: Seite zeigt 6 Gruppen, alle 61 Rechte, 12 Rollenspalten plus eigene Rollen; `admin` × `rights.manage` zeigt Schloss; geänderte Zelle bis zum Speichern markiert; Speichern → Protokoll; Seite auf 390 px Breite ohne waagerechten Bildlauf (Rollen als Karten oder gescrollte Spalte); jede Zelle per Tastatur erreichbar; Seite enthält keinen Erklär-Absatz.

- **REC-059** (P0, Status: offen) **Datenobergrenze je Grundtyp**: Unabhängig von den erteilten Rechten und Umfängen sehen und ändern Konten der Grundtypen Schüler/in und Eltern (und Grundrolle `schulbegleitung`) serverseitig nie mehr als die eigenen Daten bzw. die der verknüpften Kinder (`own`, `own_children`). Ein Recht ohne passenden Umfang (z. B. `gradebook.use`, `students.read`, `plans.read_all`) wirkt für diese Konten höchstens auf die eigenen Daten bzw. verknüpften Kinder; nie auf andere Kinder, nie auf Personal-Funktionen im Sinn von Verwaltung. Schulbegleitung: `substitution.read` und `channels.use` wirken nur für die begleiteten Kinder. (Audit 17.10.: im Altbestand dürfen Eltern/Schüler mit `gradebook.use` ohne Umfang alle Notenbücher bearbeiten; die Schutzgrenzen definiert der Neubau.)
  Abnahme: Rolle `eltern` erhält `gradebook.use` (nach Warndialog) → Elternkonto ruft das Notenbuch eines fremden Kurses ab → 404 und kann es nicht ändern; Rolle `schueler` erhält `students.read` → sieht nur die eigene Person; Schulbegleitung erhält `plans.read_all` → sieht nur Pläne der begleiteten Kinder; ein Test pro Grundtyp und pro Recht mit Datenbezug.

- **REC-060** (P0, Status: offen) **Administration und besondere Kategorien**: Die technische Administration erhält im Standard keines der 20 Rechte aus R8.3. Wird eines dennoch ausdrücklich erteilt, gilt bis zur Betreiberentscheidung die Regel: Verboten-Hinweis (REC-051), Bestätigung (REC-048) und Eintrag im Änderungsprotokoll (REC-056); Zugriffe auf diese Daten stehen im Audit. [unklar: Betreiber (16./17.10.) will freie Vergabe; das Sicherheits-Audit (17.10.) fordert „Administration sieht nie Gesundheits-, Noten- oder Förderdaten“ als harte Grenze; im Altbestand liegt die Vorgabe als Hinweis vor. Entscheidung des Betreibers offen: harte Grenze oder Warnung. Bis dahin gilt die Warnvariante.]
  Abnahme: Wirksame Standardrechte der Administration enthalten keines der 20 Rechte; Erteilung eines dieser Rechte an die Administration zeigt den Hinweis, speichert erst nach Bestätigung und erscheint im Protokoll; ein Zugriff der Administration auf Atteste, Krankmeldungsgründe, Noten oder Förderdaten ohne ausdrücklich erteiltes Recht → 403/404 gemäß R10.

- **REC-061** (P1, Status: Ist) **Volljährigkeit und Schul-Abweichung**: Volljährige Schüler/innen behalten `student_absence.report` und `student_documents.read` mit Umfang „Nur selbst“, auch wenn die Schule dem Schüler-Profil das Recht entzogen hat (die Volljährigkeits-Ergänzung ist Schritt 4 in REC-054 und überschreibt die Abweichung). [unklar: Betreiber soll festlegen, ob gewollt; Standard: gewollt, weil es um die Daten der Person selbst geht.]
  Abnahme: Schule entzieht der Rolle `schueler` `student_documents.read`; minderjähriges Konto → kein Zugriff; volljähriges Konto → Zugriff auf eigene Dokumente bleibt; Protokoll nennt die Abweichung weiterhin.

## R9 Querschnittsschutz der Rechte

- **REC-062** (P0, Status: offen) Alle Schutzregeln (Inhaber-Schutz, Sperre „keine Administrationskonten vergeben“, Verwaltbarkeit nach Umfang, Selbstaussperr-Schutz, Volljährigkeit, Elternfreigabe, Beobachtungs-Regeln) werden im Fachdienst geprüft, nicht im Routen-Handler. Einzel-, Sammel- und Massenaktionen sowie Import, Export, Zugangsbriefe, Schnittstellen-Zugänge und Konsolenbefehle laufen durch dieselbe Prüfung **je Objekt**. Neue Routen/Funktionen sind standardmäßig gesperrt, bis sie ausdrücklich freigegeben sind (Default-Deny; gilt auch für Schreib-Tokens, Demo-Schutz und Exporte). (Lehre Audit 17.10.: Schutz pro Objekt und Aktion prüfen, nicht pro Route.)
  Abnahme: Für jede Schutzregel ein Test, der alle Eintrittswege ausführt (Konto-Route, Sammel-Reset, Zugangsbrief-Stapel, `send-reset`, Import, API-Token, Konsole): überall dasselbe Ergebnis; ein neuer, nicht eingetragener Schreibweg für Schreib-Tokens ist gesperrt.

- **REC-063** (P0, Status: offen) Rechte und Sperren werden bei jeder Anfrage neu berechnet (Ist). Live-Verbindungen (Server-Sent Events) werden bei Abmeldung, Kontosperre, Herabstufung und Rechteänderung des Kontos geschlossen oder ihre Rechte neu geprüft; der Ereignisstrom wird nicht ausgeliefert, solange Passwortwechsel-, 2FA-Einrichtungs- oder Verknüpfungszwang gilt (Altbestand: Strom behält Rechte nach Abmeldung/Sperre/Herabstufung und läuft auch unter Zwang).
  Abnahme: Konto hält Live-Verbindung offen; Verwalter beendet alle Sitzungen/sperrt das Konto → Verbindung endet spätestens beim nächsten Keep-alive (`SM_SSE_PING_SECONDS`, Standard 20 s) und liefert keine weiteren Ereignisse; Rolle verliert Recht → nachfolgende Ereignisse enthalten keine Daten mehr aus dem Recht; Konto mit Passwortwechsel-Pflicht → Live-Verbindung 403.

- **REC-064** (P0, Status: Ist) Ein Feldregelwerk gilt für alle Ausgaben (Einzelansicht, Liste, Export, Feed): Das Geburtsdatum sehen nur Konten mit `students.birth_date` im jeweiligen Umfang und die Person selbst; in Sammel-Schnittstellen und Klassenseiten ist es sonst ausgeblendet. Kurswahl-Daten sind gestuft (Planung, Verwaltung, Betroffene). Jedes Feld wird gegen Rechte und Zweck geprüft (Datensparsamkeit).
  Abnahme: Lehrkraft ohne Klassenleitung ruft Schülerliste (Einzel, Sammel, Klassenseite) → kein Geburtsdatum in der Antwort; Klassenleitung der Klasse → Geburtsdatum der eigenen Klasse; Schüler/in → eigenes Geburtsdatum.

- **REC-065** (P0, Status: offen) Stammdaten-Exporte (JSON, CSV, Untis, SMO, OneRoster, ZIP) verlangen `students.read` im Umfang des Akteurs, geben das Geburtsdatum nur mit `students.birth_date` aus, schließen die Zuschauer-Rolle aus, bieten keinen Massen-Export für Ansichtskonten und werden im Audit protokolliert (Wer, wann, Format, Umfang, ohne Inhalte). CSV-Zellen werden zentral gegen Formel-Einschleusung entschärft (führende Zeichen =, +, -, @).
  Abnahme: Zuschauer-Konto und Lehrkraft ohne `students.read` rufen je Exportformat auf → 403/404 gemäß R10; Lehrkraft mit `students.read` (eigene Klassen) → Export enthält nur eigene Klassen, ohne Geburtsdatum; jeder erfolgreiche Export erzeugt einen Audit-Eintrag; Zelle „=1+1“ erscheint in jeder CSV als Text.

- **REC-066** (P0, Status: Ist) API-Zugänge (`api.own`, `api.manage`) geben nie mehr, als das ausstellende Konto selbst sehen darf; Gesundheits- und Förderdaten sind nie freigebbar (harte Grenze, unabhängig von Rechten und Rolle).
  Abnahme: Lehrkraft mit Klassenleitung (sieht Atteste) stellt einen API-Zugang mit allen Bereichen aus → Antworten des Zugangs enthalten nie Atteste, Krankmeldungsgründe, Förderdaten; Versuch, einen Bereich „Förderdaten“ zu wählen → 422.

- **REC-067** (P0, Status: offen) Der Elternzugriff endet mit der Volljährigkeit des Kindes für **alle** Ausgaben (Stundenplan, Kalender-Feed, Dokumente, Krankmeldungsgründe, Benachrichtigungen), außer das volljährige Kind gibt den Bereich frei (Freigabe je Bereich, jederzeit widerrufbar; Regeln im Bereich Schüler/innen und Eltern). Jede Eltern-Sicht prüft dieselbe zentrale Stelle.
  Abnahme: Kind wird 18 (feste Uhr): Eltern-Konto → Stundenplan, Kalender-Feed, Dokumente → 404, solange keine Freigabe besteht; nach Freigabe des Bereichs „Stundenplan“ → nur dieser Bereich wieder sichtbar; Widerruf → wieder 404.

## R10 Regel 404 gegen 403

**Grundsatz (Entscheidung 16.10.2026):** Fremde Daten liefern „nicht gefunden“ (404) statt „verboten“ (403), damit nicht erkennbar ist, dass es sie gibt.

- **REC-068** (P0, Status: Ist) **404-Regel**: Ist ein Datensatz für die anfragende Person nicht sichtbar – weil die ID nicht existiert, weil der Datensatz außerhalb des Umfangs ihrer Rechte liegt oder weil er einer anderen Person/Familie/Klasse/einem anderen Kurs gehört –, antwortet der Server mit 404, unabhängig davon, ob der Datensatz existiert. Das gilt für Lesen, Ändern, Löschen und Unterressourcen. Die Prüfung des Umfangs erfolgt in jeder Route (über die zentrale Umfangslogik, REC-042).
  Abnahme: Für jede Zeile mit „404“ in der Tabelle von REC-071: Anfrage mit existierender fremder ID und Anfrage mit nicht existierender ID liefern denselben Status, denselben Text und dieselbe Struktur (REC-070).

- **REC-069** (P0, Status: Ist) **403-Regel**: 403 nur dort, wo kein Datensatz zu verbergen ist oder die Person den Datensatz sieht, aber die Aktion nicht darf und die Meldung hilft: (a) Funktion ohne Recht, nicht datensatzbezogen (Antwort für jede ID gleich), mit Begründung; (b) Person sieht den Datensatz in anderem Zusammenhang, darf aber diesen Aspekt/diese Aktion nicht (Fachlehrkraft mit Unterricht bei der Person: Status/Vermerk/Löschen einer Krankmeldung); (c) Lehrkraft-Konto ohne Zuordnung, mit Hinweis auf das Sekretariat; (d) Schreibversuch eines Ansichtskontos; (e) Anlage/Umstellung auf eine nicht verwaltbare Rolle; (f) Schutzregeln (Inhaber-Konto, Sperre „keine Administrationskonten“, Anzeige-Sperre); (g) Elternteil schreibt in einen sichtbaren Kursraum; (h) Anmeldesperren und Lizenz-Sperre (Kennungen siehe ANM). 401 gilt nur ohne gültige Sitzung/Zugangsdaten.
  Abnahme: Je Buchstabe (a)–(h) ein Test mit erwartetem Status 403 (bzw. 401) und Begründungstext in Sie-Form; ein Test, dass keiner dieser Fälle einen 403 liefert, der die Existenz eines fremden Datensatzes verrät (gleiche Antwort für jede ID).

- **REC-070** (P0, Status: Ist) **Gleichartige Antworten**: 404-Antworten für „existiert nicht“ und „nicht sichtbar“ sind gleich in Status, Fehlertext (`{"detail": "…"}`), Struktur und Kopfzeilen; der Fehlertext nennt weder Name noch Typ noch Besitzer des Datensatzes. Fehlertexte stehen auf Deutsch. Unerwartete Fehler zeigen „Das hat nicht geklappt“ mit einer Fehlernummer (Request-ID), nie interne Details.
  Abnahme: Je Datenart eine Abfrage mit existierender fremder und eine mit unbekannter ID → Antworten sind in Status, Text, Struktur und Kopfzeilen (außer Datum und Request-ID) identisch; Antwort enthält weder ID noch Namen.

- **REC-071** (P0, Status: Ist) **Anwendung je Datenart** (jede Zeile ist abzunehmen):

  | Datenart | Fall | Antwort |
  |---|---|---|
  | Benutzerkonten | Akteur darf Konten dieser Grundrolle nicht verwalten (Lesen, Ändern, Löschen, Sitzungen, Kontakt, Beobachtung, Verbundene Konten, Zuordnung, API-Zugänge des Kontos) | 404 |
  | Benutzerkonten | Anlage oder Umstellung auf nicht verwaltbare Rolle | 403 |
  | Benutzerkonten | Inhaber-Konto: ändernde Anfrage eines anderen Kontos | 403 + `user.owner_protected` |
  | Benutzerkonten | Beobachtetes Konto ruft Beobachtungs-Routen oder die Beobachtungs-Einstellung des eigenen Kontos | 404 |
  | Rollen, Zweige, Zuordnungen | Unbekannte Rolle/Zweig in der Adresse; Zuordnung für ein Konto, dessen Rolle sie nicht kennt | 404 |
  | Rollen | Unbekannte oder ausgeblendete Rolle als Wert in Anlage/Umstellung | 422 |
  | Schülerdaten, Pläne, Klassen | Schüler/in, Eltern, Schulbegleitung mit fremder Schüler-ID; Lehrkraft mit Klasse außerhalb des Umfangs; unbekannte Klasse; Klassentermine | 404 (Listen: gefiltert bzw. leer) |
  | Krankmeldungen | Lehrkraft ohne Unterricht bei der Person | 404 |
  | Krankmeldungen | Fachlehrkraft mit Unterricht bei der Person, ohne Zuständigkeit für Status/Vermerk/Löschen | 403 |
  | Krankmeldungen | Klassenleitung, Sekretariat, Schulleitung | 200 |
  | Atteste und Dokumente | Fremdes Kind/fremde Klasse trotz Recht (Umfang verletzt) | 404 |
  | Atteste/Dokumente, Förderkennzeichen, Eltern-Kontakte einer Person, Benachrichtigungs-Ausgang | Zuschauer/Monitor ohne ausdrücklich erteiltes Recht (Anzeige-Sperre, Antwort unabhängig von der ID) | 403 |
  | Förderdaten | Person ohne Klassenleitung der Klasse bzw. ohne Recht im Umfang | 404 |
  | Noten und Notenbuch | Notenbuch eines Kurses/Kursverbands, der nicht zu den eigenen Kursen gehört; Klasse außerhalb der eigenen Klassenleitung | 404 |
  | Lernstand/Kompetenzen | Schüler/in außerhalb des Umfangs | 404 |
  | Kursräume, Dateien, Pinnwand | Raum/Datei, in dem die Person nicht Mitglied, Elternteil oder Aufsicht ist; Löschen einer fremden Datei (rund 40 Routen) | 404 |
  | Kursräume | Elternteil schreibt in einem sichtbaren Kursraum | 403 |
  | Selbstauskunft, Elternzugang | Fremde Person/fremdes Kind | 404 |
  | Nachrichten und Chats | Fremde Unterhaltung oder Nachricht | 404 |
  | Formulare, Eingang | Einreichung außerhalb des Umfangs | 404 |
  | Zugangsbrief-Stapel | Person ist nicht Ersteller und nicht Administration | 404 (abgelaufener Stapel: 410) |
  | Lehrkraft-Konto ohne Zuordnung | Funktion, die die Zuordnung braucht (Hinweis auf das Sekretariat) | 403 |
  | Ansichtskonto | Schreibversuch | 403 (Text REC-020) |
  | Funktion ohne Recht | z. B. Rechte-Seite ändern ohne `rights.manage`, nicht datensatzbezogen | 403 mit Begründung |
  | Ohne Sitzung | Beliebige geschützte Funktion | 401 |
  | Anmeldesperren | Passwortwechsel-, 2FA-Einrichtungs-, Verknüpfungs-Pflicht, Lizenz gesperrt | 403 mit Kennung (siehe ANM-005) |

  Abnahme: Zu jeder Zeile existiert ein automatischer Test mit den angegebenen Konten und dem erwarteten Status; die Testliste enthält mindestens 42 Fälle.

- **REC-072** (P1, Status: Ist) Listen und Suchen liefern nur Datensätze im Umfang des Akteurs (gefiltert oder leer) und keine Hinweise auf ausgeblendete Treffer (kein Zähler, kein „n weitere“); die Schüler-/Eltern-Suche im Postfach liefert nur erlaubte Empfänger.
  Abnahme: Schülerliste als Lehrkraft (eigene Klassen) enthält nur Schüler aus eigenen Klassen, Gesamtzahl im Kopf stimmt mit der gefilterten Zahl überein; Eltern-Suche nach dem Vornamen eines fremden Kindes → leere Liste.

- **REC-073** (P1, Status: offen) Alarm bei Massenzugriffen: Viele Anfragen mit fremden oder unbekannten IDs hintereinander (typisches Durchprobieren) lösen einen Hinweis für die Schulleitung/Administration aus und werden im Audit gebündelt vermerkt. [unklar: Schwellenwerte nicht vorgegeben; Audit 17.10. „kein Alarm bei Massenzugriffen“.]
  Abnahme: 200 aufeinanderfolgende Abfragen eines Kontos mit fremden IDs binnen 10 Minuten → ein Alarm-Eintrag im Audit und ein sichtbarer Hinweis für Administration und Schulleitung (Schwelle konfigurierbar); normale Nutzung löst nichts aus.

- **REC-074** (P1, Status: Ist) Rechte-Matrix-Tests: Jede neue Sichtbarkeitsregel erhält einen Test über alle betroffenen Rollen, jeweils mit Konto innerhalb und außerhalb des Umfangs (Eltern minder-/volljähriger Kinder, mit und ohne Freigabe; Fachlehrkraft; Klassenleitung; Zuschauer), geprüft **pro Objekt und Aktion**.
  Abnahme: Testsuite enthält je Datenart aus REC-071 mindestens einen Positiv- und einen Negativfall; ein neues Recht ohne Matrix-Test lässt die Suite scheitern.

---

# TEIL B – ANMELDUNG, SSO, ZWEI-FAKTOR, SITZUNGEN, KONTEN (ANM)

## B1 Anmeldung mit Benutzername und Passwort (zwei Schritte, Code nur bei Bedarf)

**Prüfreihenfolge** (Anmeldung mit Benutzername und Passwort):

| Schritt | Prüfung | Ergebnis bei Fehler |
|---|---|---|
| 1 | Drosselung (Abschnitt B3) | 429 `too_many_attempts`, Kopfzeile `Retry-After` in Sekunden; zählt nicht als Fehlversuch |
| 2 | Benutzername klein geschrieben, max. 80 Zeichen; Konto suchen | – |
| 3 | Passwort prüfen | 401 `invalid_credentials`; zählt als Fehlversuch (gleiche Antwort für unbekanntes Konto) |
| 4 | Konto aktiv | 403 `account_disabled`; zählt als Fehlversuch |
| 5 | Zwei-Faktor aktiv, Code fehlt | 200 mit `totp_required=true`, ohne Sitzung; zählt nicht |
| 5a | Zwei-Faktor aktiv, Code falsch oder bereits verwendet | 401 `invalid_credentials`; zählt als Fehlversuch |
| 6 | Startpasswort-Frist abgelaufen (Passwortwechsel noch offen) | 403 `initial_password_expired`; zählt als Fehlversuch |
| 7 | Anmeldeweg „Passwort“ laut Anmelde-Richtlinie erlaubt | 403 `method_not_allowed` mit Kopfzeile `X-Login-Methods`; zählt als Fehlversuch |
| 8 | Erfolg | Erfolgseintrag, Sitzung, Cookie; Antwort mit Benutzer und CSRF-Token |
| 8a | Ersteinrichtung (Startpasswort, fehlende Pflicht-Verknüpfung) | Sitzung nur zum Verbinden (Anmeldeart `password_setup`) |
| 8b | Parameter `add=true` | Bisheriges Konto bleibt als weiteres Konto angemeldet (Abschnitt B8) |

**Weitere Antwortcodes**

| Code | Bedeutung | Auslöser |
|---|---|---|
| 401 `not_authenticated` | nicht angemeldet | Endpunkt mit Anmeldepflicht |
| 401 `invalid_token` | API-Token ungültig | abgelaufen, widerrufen oder Konto inaktiv |
| 403 `csrf_failed` | CSRF-Prüfung fehlgeschlagen | ändernde Anfrage ohne passenden `X-CSRF-Token` (Sitzung) bzw. Herkunft nicht passend (Kontoliste ohne Sitzung) |
| 403 `password_change_required` | Passwortwechsel nötig | alle Endpunkte außer Anmelde-Pfaden |
| 403 `totp_setup_required` | Zwei-Faktor-Einrichtung nötig | alle Endpunkte außer Anmelde-Pfaden (nur Sitzung) |
| 403 `link_required` | Pflicht-Verknüpfung fehlt | alle Endpunkte außer Anmelde-Pfaden und Identitäten |
| 403 | Ansichtskonto darf nicht ändern | ändernde Anfrage ohne ausdrücklich erteilte Rechte |
| 403 `license_locked` | Lizenz gesperrt | nur Anmelde-Pfade und Lizenz-Eingabe erreichbar |
| 409 | Selbstaussperrung | Regel würde den eigenen Anmeldeweg entfernen (Richtlinie speichern) |
| 429 | Zu viele Anfragen | Drosselung, Grenzen der Codes, allgemeines Limit; stets mit `Retry-After` |

**Anmeldesperren (Gating je Anfrage)**

| Zustand | Erlaubte Pfade | Antwort sonst |
|---|---|---|
| Passwortwechsel erforderlich | Anmelde-Pfade (`/auth/`) | 403 `password_change_required` |
| Zwei-Faktor-Einrichtung erforderlich | Anmelde-Pfade (`/auth/`) | 403 `totp_setup_required` |
| Pflicht-Verknüpfung fehlt | Anmelde-Pfade und Identitäten (`/me/identities`) | 403 `link_required` |
| Lizenz gesperrt | Anmelde-Pfade und Lizenz-Eingabe | 403 `license_locked` |
| Ansichtskonto | Abmelden und Kontoliste (`/auth/logout`, `/auth/accounts`) | 403 (Text REC-020) |

- **ANM-001** (P0, Status: Ist) **Zweistufige Anmeldung, Code nur bei Bedarf** (Entscheidung Betreiber 16.10.2026, Wunsch-Wortlaut: „die Abfrage für den Bestätigungscode … gar nicht abgefragt wird, das ist nämlich auch ein bisschen sinnlos“): Schritt 1 = Benutzername und Passwort. Hat das Konto keine aktive Zwei-Faktor-Anmeldung, entsteht mit Schritt 1 die Sitzung. Hat es eine, antwortet der Server mit `totp_required=true` (200, keine Sitzung, kein Cookie, weder Erfolg noch Fehlversuch); erst jetzt blendet die Oberfläche das Code-Feld ein und sendet dieselbe Anmeldung mit dem Einmalcode (Schritt 2). Ein Schritt 1 zählt nie als Erfolg (sonst wäre das Raten des Codes unbegrenzt). Fehlermeldungen beziehen sich nur auf vorhandene Felder. Die Oberfläche unterscheidet „erfolgreich“ und „Code nötig“. [unklar: Das Sicherheitsaudit (13./17.10.) fordert eine Antwort, die bei 2FA-Konten ohne gültigen Code wie ein falsches Passwort aussieht (Konto-Orakel); der Betreiber hat am 16.10. die zweistufige Fassung gewählt, die spätere Entscheidung gilt. Abwägung: falsche Passwörter und falsche Codes zählen gegen die Drosselung, Schritt 1 mit richtigem Passwort verrät dem Besitzer des Passworts nur, dass 2FA aktiv ist.]
  Abnahme: Konto ohne 2FA: ein Aufruf mit richtigem Passwort → 200, Cookie `sm_session`, kein Code-Feld in der Oberfläche; Konto mit 2FA: Aufruf ohne Code → 200 `totp_required=true`, kein Cookie, Fehlversuchszähler unverändert, Code-Feld erscheint; Aufruf mit falschem Code → 401 und Fehlversuchszähler +1; mit richtigem Code → Sitzung. Beim Konto ohne 2FA erscheint nie der Text „Bestätigungscode“.

- **ANM-002** (P0, Status: Ist) **Neutrale Fehlermeldungen, keine Konto-Erkennung**: Unbekannter Benutzername, falsches Passwort und (bei 2FA) falscher Code liefern dieselbe Antwort 401 `invalid_credentials`; Text: „Benutzername oder Passwort ist falsch.“ [unklar: Wortlaut der Meldung bei falschem Code; Altbestand zeigt eine eigene Meldung]. Bei unbekanntem Benutzernamen läuft eine Scheinprüfung gleicher Dauer; der Passwort-Hash eines ungültigen Hashs gilt als falsch. Login-Anfragen sind JSON-Aufrufe (kein HTML-Formular, damit kein Login-CSRF).
  Abnahme: 50 Anmeldungen mit unbekanntem und 50 mit bekanntem Konto/falschem Passwort → identische Antwort (Status, Text, Struktur); Konto mit ausgeschalteter Anmeldung (`account_disabled`) wird erst nach richtigem Passwort erkannt; Antwortzeit unbekannter Name ≈ bekannter Name (gleiche Hash-Rechenzeit, Test mit dem Aufwandsfaktor aus ANM-014).

- **ANM-003** (P0, Status: Ist) Die Prüfreihenfolge, Statuscodes und Zählregeln der Tabelle „Prüfreihenfolge“ gelten verbindlich. Die Anmelde-Richtlinie wirkt erst nach Passwort, Aktivstatus und Code (Schritte 6 und 7).
  Abnahme: Je Zeile der Tabelle ein Test mit erwartetem Status und Wirkung auf den Fehlversuchszähler; gedrosselte Anfrage (Schritt 1) erhöht den Zähler nie; Erfolg setzt Paar- und Kontozähler zurück (ANM-026/028).

- **ANM-004** (P1, Status: Ist) Die Antwortcodes der Tabelle „Weitere Antwortcodes“ gelten; alle Fehlertexte stehen auf Deutsch und in Sie-Form; `Retry-After` wird in der Oberfläche als Restzeit in Klartext angezeigt (z. B. „Bitte versuchen Sie es in 30 Sekunden erneut.“). Jede Anfrage, die 401 erhält, führt zur Prüfung der Sitzung; die Oberfläche leitet dann zur Anmeldung (öffentliche Seiten wie Passwort-Zurücksetzen, Test-Postausgang und SSO-Schaltflächen leiten nie zur Anmeldung).
  Abnahme: Anfrage ohne Sitzung auf geschützte Funktion → 401 `not_authenticated`, Oberfläche zeigt Anmeldung; öffentliche Seite „Passwort vergessen“ ohne Sitzung → bleibt stehen; 429 → Restzeit sichtbar.

- **ANM-005** (P0, Status: Ist) **Anmeldesperren**: Solange Passwortwechsel, Zwei-Faktor-Einrichtung oder Pflicht-Verknüpfung offen sind oder die Lizenz gesperrt ist, sind ausschließlich die Pfade der Tabelle „Anmeldesperren“ erreichbar; alles andere liefert 403 mit der Kennung. Ausnahme Passwortwechsel: ist der Anmeldeweg „Passwort“ für das Konto nicht erlaubt, gibt es keinen Zwang. Die Administration kann sich trotz Lizenzsperre anmelden. Der Zwang gilt auch für den Live-Strom (REC-063).
  Abnahme: Konto mit Pflichtwechsel: GET Stundenplan → 403 `password_change_required`, `POST /auth/password` → 200; Konto mit fehlender Pflicht-Verknüpfung: `/me/identities` erreichbar, Stundenplan 403 `link_required`; gesperrte Lizenz: Admin meldet sich an, ruft Lizenz-Eingabe auf (200), Stundenplan → 403 `license_locked`.

- **ANM-006** (P1, Status: Ist) **Anmeldeseite**: Logo, Feld Benutzername, Feld Passwort (verdeckt, Auge-Schaltfläche; Anzeige nur bewusst), ein Anmelden-Knopf; Code-Feld nur im zweiten Schritt (ANM-001); Anbieter-Knöpfe nur für eingeschaltete Anbieter (ANM-044); „Passwort vergessen“ nur, wenn ein Versand möglich ist, sonst der Hinweis „Bitte wenden Sie sich an das Sekretariat.“; Erklärungen nur hinter „?“; keine Test-Knöpfe; keine Rollen-Schnellanmeldung (nur in der Demo-Instanz, siehe Betrieb). Passwortformulare tragen ein verstecktes Benutzernamen-Feld und die Attribute `autocomplete` `username`, `current-password`, `new-password` mit stabilen Namen, damit Passwort-Manager das Konto richtig erkennen; das neue Passwort steht auf einer eigenen Seite. Die Wartezeit der Drosselung erscheint als Restzeit in Klartext.
  Abnahme: Bildschirmprüfung 390 px und 1280 px, hell/dunkel: Seite hat kein Erklär-Absatz, Passwortfeld ist verdeckt, Auge schaltet; Chromium-Passwortspeicher bietet gespeicherte Zugangsdaten an und erkennt das Konto beim Ändern; ohne Mailversand fehlt der Link „Passwort vergessen“ und der Hinweis steht da; Tastatur: Reihenfolge Benutzername → Passwort → Anmelden.

- **ANM-007** (P2, Status: Ist) Die öffentliche Konfiguration der Anmeldeseite (`/auth/config`, `/auth/capabilities`, `/auth/password-reset/options`) nennt ohne Anmeldung nur: eingeschaltete Anbieter (Kennung, Beschriftung), verfügbare Reset-Kanäle, Mindestlängen der Passwörter (Standard 10, Schüler/innen 8). Sie enthält keine Geheimnisse, keine Konten-Hinweise und nur Anbieter, die wirklich eingerichtet und eingeschaltet sind (auch Schulkonto/OIDC nur bei Einrichtung, aus Einstellungsseite **oder** Umgebung).
  Abnahme: Anbieter ohne Client-ID/Geheimnis erscheint nicht; Anbieter nur in der Oberfläche eingerichtet (nicht in der Umgebung) erscheint ebenfalls (Altbestand meldete OIDC nur aus der Umgebung); Antwort enthält keine Client-Geheimnisse.

- **ANM-008** (P0, Status: offen) Die Weiterleitung nach der Anmeldung (Parameter für die Zielseite) und die Anbieter-Adresse beim Verbinden werden strikt auf **interne Pfade der eigenen Anwendung** beschränkt (Schutz vor offener Weiterleitung); externe Ziele, Schema-relative Adressen und Adressen mit anderem Host werden verworfen.
  Abnahme: Ziel `https://fremd.example/x`, `//fremd.example` und `/\fremd.example` → nach der Anmeldung Startseite; Ziel `/stundenplan` → Stundenplan; Verbinden mit manipulierter Rückkehr-Adresse → abgewiesen.

## B2 Passwörter

- **ANM-009** (P0, Status: Ist) **Längen**: Mindestlänge Schüler/innen 8 Zeichen, übrige Rollen (Personal, Eltern, Monitor, eigene Rollen nach Grundrolle) 10 Zeichen; Höchstlänge 256 Zeichen; die Eingabefelder begrenzen ebenfalls auf 256 Zeichen [Altbestand: Felder akzeptieren bis 1024]. Die Mindestlänge je Rolle wird öffentlich abgerufen (ANM-007); Hinweistexte (Handbuch, Datenschutzhinweise) leiten die Zahlen aus der Konfiguration ab (Widerspruch im Altbestand: Hinweise für Schüler/innen nennen 10).
  Abnahme: Passwort mit 7 Zeichen bei Schüler → 422 mit Grund; 9 Zeichen bei Lehrkraft → 422; 10 Zeichen → angenommen; 257 Zeichen → 422; Anzeige der Mindestlänge in der Oberfläche entspricht der Serverregel; Eltern 10, Schulbegleitung (Grundtyp Eltern) 10.

- **ANM-010** (P0, Status: Ist) **Inhaltsregeln** für alle Wege (Anlage, Setzen, Ändern, Zurücksetzen): mindestens 4 verschiedene Zeichen; das Passwort darf den Benutzernamen (ab 3 Zeichen, ohne Beachtung der Groß-/Kleinschreibung) nicht enthalten; es darf nicht in der Liste häufiger Passwörter stehen (Vergleich in Kleinschreibung); Ablehnung mit „zu leicht zu erraten“ und Gründen (422). Keine Pflicht zu Zeichenklassen (Groß/Klein, Ziffern, Sonderzeichen). Neues Passwort muss sich vom bisherigen unterscheiden (Passwortwechsel des eigenen Kontos). Kein Passwortverlauf, kein periodischer Ablauf (kein Zwangswechsel nach Zeit).
  Abnahme: „aaaabbbb12“ ist erlaubt, „aaaaaaaaaa“ (1 Zeichen) → 422; Benutzer `maria.klein` mit Passwort `xxMARIA.KLEINxx9` → 422; „Passwort1234“ (Liste) → 422; Wechsel auf das bisherige Passwort → 422; nach 400 Tagen kein Zwangswechsel.

- **ANM-011** (P0, Status: offen) Die Liste häufiger Passwörter umfasst mindestens 3000 Einträge (Anforderung nach ASVS; Altbestand ca. 108 Einträge).
  Abnahme: Die Liste im Neubau hat ≥ 3000 eindeutige Einträge; Stichprobe 20 bekannte Trivialpasswörter (nicht in der alten Liste) → 422.

- **ANM-012** (P1, Status: offen) Passwortregeln kommen **vom Server**, nicht fest aus dem Frontend; die Oberfläche zeigt Mindestlänge und Hinweise aus der Serverauskunft, serverseitig ist jede Regel durchgesetzt.
  Abnahme: Mindestlänge im Server ändern (Test) → Hinweis in der Oberfläche folgt ohne Neubau des Frontends; Umgehen der Oberflächenprüfung per direktem Aufruf → Server lehnt ab.

- **ANM-013** (P2, Status: Ist) **Leak-Prüfung** (Have-I-Been-Pwned-Bereichsabfrage): Standard aus; einschaltbar per `SM_HIBP_CHECK` oder Schuleinstellung `hibp_check`. Geprüft werden nur selbst gewählte Passwörter (eigenes Passwort ändern, Zurücksetzen per Code oder Link), nicht Vergabe durch die Verwaltung oder Kontoanlage. Übertragen werden nur die ersten 5 Zeichen des SHA-1-Werts (k-Anonymität; das Klartext-Passwort erreicht den Dienst nie); Zeitlimit 3 s; Antwortgröße max. 2 000 000 Byte; bei Ausfall des Dienstes wird das Passwort angenommen (fail-open) und der Vorgang protokolliert; Treffer → Ablehnung „aus bekannten Datenlecks“. Der Zielhost steht fest in der Liste erlaubter Ziele. [unklar: Einschalten entscheidet der Betreiber; Datenschutz-Dokumente nennen sonst „kein Drittlandtransfer“, der Dienst liegt in den USA.]
  Abnahme: Mit Schalter an und Dienst-Attrappe: Treffer → 422 „aus bekannten Datenlecks“; Anfrage an die Attrappe enthält genau 5 Hex-Zeichen; Dienst nicht erreichbar → Passwort angenommen + Protokolleintrag; Verwaltung setzt Passwort → keine Abfrage; Schalter aus → keine Abfrage.

- **ANM-014** (P0, Status: Ist) **Passwort-Hash**: scrypt (Standardbibliothek), gespeichert als `scrypt$N$r$p$Salt$Hash` (Base64 ohne Auffüllung; Parameter stehen im Hash, Nachrüstung möglich). N = 32768 (2^15) für selbst gewählte Passwörter, N = 2048 (2^11) für erzeugte Startpasswörter; r = 8, p = 1, Schlüssellänge 32 Byte, Salt 16 Byte zufällig je Hash, Speicherlimit mindestens 64 MiB; Vergleich in konstanter Zeit. In Produktion muss `SM_SCRYPT_N` eine Zweierpotenz ≥ 16384 (2^14) sein (sonst Startabbruch; überhaupt: keine Zweierpotenz oder < 2 → Startabbruch). Bei erfolgreicher Anmeldung wird neu gehasht, wenn der gespeicherte N kleiner als konfiguriert ist (nicht beim Pflicht-Passwortwechsel). Ein ungültiger Hash gilt als falsch.
  Abnahme: Neues Passwort → Hash beginnt mit `scrypt$32768$8$1$`; Startpasswort-Hash `scrypt$2048$8$1$`; Konto mit alter N 4096 meldet sich an → danach Hash mit 32768; `SM_SCRYPT_N=1000` → Startabbruch; `SM_SCRYPT_N=8192` in Produktion → Startabbruch; manipulierter Hash → Anmeldung 401.

- **ANM-015** (P0, Status: Ist) **Startpasswort-Erzeugung**: Kryptografisch sicherer Zufall. Standard-Startpasswort = 3 Gruppen zu je 4 Zeichen mit Bindestrich (Schema `xxxx-xxxx-xxxx`, etwa 59 Bit) für Kontoanlage, Zurücksetzen durch Verwaltung, Massenanlage, Konsole ohne Passwort; Erst-Admin und Konsolenbefehl `create-admin` ohne Passwort: 4 Gruppen zu je 4 Zeichen (etwa 79 Bit). Zeichenvorrat 31 Zeichen: Kleinbuchstaben ohne i, l, o und Ziffern 2 bis 9 (gut tippbar, auf dem Handy ohne Großschreibung). Das Startpasswort wird nur einmal angezeigt (Antwort auf die Anforderung bzw. Brief), nicht zwischengespeichert und nur als Hash samt Ablauf gespeichert (nie entschlüsselbar). Der Modus „altes Startpasswort wieder gültig“ entfällt; stattdessen wird ein neues erzeugt.
  Abnahme: 1000 erzeugte Startpasswörter: Muster `^[a-hjkmnp-z2-9]{4}(-[a-hjkmnp-z2-9]{4}){2}$`, nie i/l/o/0/1; Erst-Admin-Passwort 4 Gruppen; Datenbank enthält nur Hash und Frist, kein umkehrbares Passwort; zweiter Abruf des Startpassworts desselben Reset → nicht möglich.

- **ANM-016** (P0, Status: Ist) **Startpasswort-Frist und Pflichtwechsel**: Ein Startpasswort gilt `initial_password_days` Tage (Standard 14, Einstellbereich 1 bis 90; Schuleinstellung). Nach Ablauf wird die Anmeldung mit dem richtigen Passwort mit 403 `initial_password_expired` abgelehnt (zählt als Fehlversuch); ein neues Startpasswort ist nötig. Gespeichert werden nur Hash des Kontos zur Vergabe und Ablaufdatum; die Marke erlischt bei Passwortwechsel oder Löschen. Pflicht-Wechsel (`must_change_password`) ist Standard „ja“ bei Kontoanlage, Massenanlage, Zurücksetzen durch die Verwaltung und Startpasswort; bis zum Wechsel gilt ANM-005. Der Brief nennt die Gültigkeitsfrist des Startpassworts (Altbestand: Brief nennt sie nicht).
  Abnahme: Startpasswort Tag 15 → 403 `initial_password_expired`; Tag 13 → Anmeldung mit Pflichtwechsel; `initial_password_days=0` oder 91 → 422; nach Wechsel Marke weg; der Brieftext enthält „14 Tage“ bzw. den eingestellten Wert.

- **ANM-017** (P0, Status: Ist) **Eigenes Passwort ändern** (`POST /auth/password`): altes Passwort nötig (falls gesetzt), neues nach ANM-009/010 (und Leak-Prüfung, falls an); alle anderen Sitzungen des Kontos enden, die aktuelle bleibt; Protokoll `auth.password_change`. Falsches altes Passwort zählt als Fehlversuch (Drosselung, ANM-029).
  Abnahme: Zweite Sitzung desselben Kontos ist nach der Änderung beendet (401), die erste bleibt; falsches altes Passwort 6× → Wartezeit 60 s (Tabelle ANM-025); Audit-Eintrag ohne Passwort.

- **ANM-018** (P0, Status: Ist) **Drei Wege, ein Passwort zu setzen**, alle mit denselben Regeln für Passwort, Drosselung und Anmelde-Richtlinie: (1) Verwaltung (`users.manage` bzw. `passwords.reset`) erzeugt immer ein neues Startpasswort (Pflichtwechsel, alle Sitzungen beendet, offene Reset-Codes entwertet); setzt sie ein selbst gewähltes Passwort, gelten die Passwortregeln (422 mit Gründen), Pflichtwechsel-Standard ja, das eigene Konto geht nicht über diesen Weg; (2) Zugangsbrief-Stapel (Abschnitt B11); (3) Selbst-Zurücksetzen (Abschnitt B10). Protokoll `user.update` mit „password: gesetzt“ ohne Wert.
  Abnahme: Je Weg ein Test mit zu kurzem Passwort → 422 und gleichem Grund; Verwaltung setzt eigenes Passwort über diesen Weg → abgelehnt; alle Sitzungen des Zielkontos danach beendet.

- **ANM-019** (P0, Status: Ist) **Erst-Admin beim ersten Start** (nur wenn noch kein Konto existiert): `SM_ADMIN_PASSWORD` gesetzt → dieses Passwort, kein Pflichtwechsel (Regelverstoß nur Warnung im Protokoll); leer in Produktion/Demo → Startpasswort 4×4 Zeichen mit Pflichtwechsel, abgelegt im Datenverzeichnis in der Datei `ERST-ADMIN.txt` (Rechte 600), nie im Protokoll; die Datei wird nach dem ersten Passwortwechsel des Admin gelöscht (auch beim Start, wenn kein Admin mehr Pflichtwechsel hat); leer in Entwicklung → bekanntes Entwicklungs-Passwort mit Pflichtwechsel (nur Entwicklungsmodus); Datei nicht schreibbar → Fehlermeldung, Passwort wird nicht protokolliert, Zurücksetzen über Konsole. Benutzername aus `SM_ADMIN_USER` (Standard `admin`).
  Abnahme: Produktionsstart ohne `SM_ADMIN_PASSWORD` → `ERST-ADMIN.txt` mit Rechten 600 vorhanden, Serverprotokoll enthält das Passwort nicht, Anmeldung erzwingt Passwortwechsel, danach ist die Datei gelöscht; zweiter Start legt kein weiteres Konto an; `SM_ADMIN_PASSWORD` = bekanntes Entwicklungs-Passwort in Produktion → Startfehler (ANM-020).

- **ANM-020** (P0, Status: Ist) **Start-Prüfungen für Anmeldung und Schlüssel** (Betriebsmodi `SM_MODE` = production/demo/development, abgeleitet aus `SM_ENV`): Startabbruch bei: `SM_MODE` oder `SM_ENV` ungültig oder widersprüchlich; `SM_SECRET_KEY` fehlt oder < 32 Zeichen (Produktion); `SM_ENCRYPTION_KEYS` fehlt oder fehlerhaft (Produktion); `SM_DEV_OUTBOX=1` in Produktion; `SM_SSO_DEV_MOCK=1` außerhalb der Entwicklung (oder Demo/öffentliche Demo); `SM_SCRYPT_N` ungültig oder in Produktion < 16384; `SM_AUTH_CODE_MINUTES` < 1 oder > 1440; `SM_SMS_PROVIDER` unbekannt (erlaubt: leer, `log`, `webhook`, `twilio`, `seven`), SMS-Webhook ohne http(s)-URL, `twilio` ohne SID/Token/Absender, `seven` ohne Token, `SM_SMS_TIMEOUT` ≤ 0; nicht lesbare Zahlenwerte. Im ausdrücklichen Produktionsmodus zusätzlich Fehler bei: Platzhalter im Geheimnis (beginnt mit `BITTE_AENDERN` oder enthält `CHANGE_ME`), fehlende oder nicht-https `SM_BASE_URL` (außer lokal), `SM_COOKIE_SECURE=0`, bekanntes Entwicklungs-Passwort oder Platzhalter als `SM_ADMIN_PASSWORD`, `SM_LOAD_DEMO=1`, `SM_DEMO_PUBLIC=1`. Warnungen: SQLite ab etwa 500 Konten (PostgreSQL empfohlen), kein E-Mail-Versand, `SM_REQUIRE_2FA_ROLES` leer (Empfehlung admin, schulleitung, sekretariat), `SM_AUTO_BACKUP_HOURS=0`, `SM_TRUST_PROXY` nicht gesetzt, SMS-Anbieter `log` in Produktion. Ohne `SM_MODE` und ohne `SM_ENV=production` gilt der Entwicklungsmodus (Standard von `SM_ENV`: development) – Risiko Fehlkonfiguration.
  Abnahme: Je Zeile ein Startversuch mit der Fehlkonfiguration → Prozess bricht mit Meldung ab, die die Variable nennt (nicht den Wert); Produktion mit gültigen Werten startet; Warnungen erscheinen im Start-Protokoll ohne Abbruch.

## B3 Drosselung statt Sperre (Missbrauchsschutz bei der Anmeldung)

**Drei Zähler**

| Zähler | Schwelle | Zählfenster | Wartezeit | Wirkt auf | Zurückgesetzt durch |
|---|---|---|---|---|---|
| Paar: Benutzername + IP | 5 Fehlversuche (`SM_LOGIN_MAX_FAILURES`) | 15 Minuten (`SM_LOGIN_LOCK_MINUTES`), gezählt seit dem letzten Erfolg des Kontos | 30 s × 2^(Überschuss), Deckel 900 s (= `SM_LOGIN_LOCK_MINUTES` × 60, mindestens 30 s) | Anmeldung dieses Kontos von dieser IP | Erfolg des Kontos (auch SSO, Passwort-Zurücksetzen); Aufheben durch die Verwaltung |
| IP insgesamt | 30 Fehlversuche (`SM_LOGIN_MAX_FAILURES_IP`) plus erfolgreiche Anmeldungen dieser IP im Fenster | 15 Minuten | 2 s × 2^(Überschuss ÷ 10, ganzzahlig), Deckel 60 s | alle Konten von dieser IP; greift nur, wenn das Paar mindestens 1 Fehlversuch hat (der erste Versuch eines Kontos von dieser IP ist immer frei) | nur Ablauf des Fensters oder Aufheben durch die Verwaltung (kein Reset durch Erfolg) |
| Konto insgesamt | 20 Fehlversuche (4 × `SM_LOGIN_MAX_FAILURES`) je Konto seit letztem Erfolg | 15 Minuten | 30 s × 2^(Überschuss), Deckel 900 s | nur IPs **ohne** Erfolg dieses Kontos in den letzten 60 Tagen (bekannte IP ausgenommen) | Erfolg des Kontos; Aufheben durch die Verwaltung |

**Wartezeiten Paar und Konto**

| Fehlversuche im Fenster | Wartezeit ab letztem Fehlversuch |
|---|---|
| 1 bis 4 | keine (frei) |
| 5 | 30 Sekunden |
| 6 | 60 Sekunden |
| 7 | 120 Sekunden |
| 8 | 240 Sekunden |
| 9 | 480 Sekunden |
| 10 und mehr | 900 Sekunden (Deckel) |

**Wartezeiten IP insgesamt**

| Fehlversuche über der IP-Schwelle | Wartezeit ab letztem Fehlversuch |
|---|---|
| 0 bis 9 | 2 Sekunden |
| 10 bis 19 | 4 Sekunden |
| 20 bis 29 | 8 Sekunden |
| 30 bis 39 | 16 Sekunden |
| 40 bis 49 | 32 Sekunden |
| 50 und mehr | 60 Sekunden (Deckel) |

- **ANM-021** (P0, Status: Ist) **Grundsatz**: keine harte Kontosperre und keine Sperre einer ganzen Schul-IP, sondern gestaffelte Wartezeit (Schutz vor gezieltem Aussperren fremder Konten; Schulnetze hinter gemeinsamer Adresse/NAT werden nie ausgesperrt). Entscheidung 16./17.10.2026 (ersetzt die frühere Sperre pro Benutzername/IP von 15 Minuten).
  Abnahme: Lasttest 300 Konten hinter **einer** IP, davon 75 mit einem Tippfehler im ersten Versuch → alle 300 melden sich nach dem zweiten Versuch an, keine 429 für Konten ohne Fehlversuch; ein Angreifer mit 10 Fehlversuchen gegen ein Konto sperrt dieses Konto nicht für dessen bekannte IP (Konto-Zähler wirkt dort nicht).

- **ANM-022** (P0, Status: Ist) **Was zählt**: Als Fehlversuch zählen falsches Passwort (auch unbekanntes Konto), inaktives Konto nach richtigem Passwort, falscher oder bereits verwendeter Zwei-Faktor-Code, abgelaufenes Startpasswort und nicht erlaubter Anmeldeweg. Nicht gezählt werden gedrosselte Anfragen, Schritt 1 einer Zwei-Faktor-Anmeldung mit richtigem Passwort und Erfolge. Fehlversuche werden je Benutzername und IP gespeichert (Anmeldeversuche, nicht verschlüsselt, siehe ANM-031).
  Abnahme: Je Fall der Aufzählung: Zähler +1 bzw. unverändert wie angegeben; 10 gedrosselte Wiederholungen verlängern die Wartezeit nicht.

- **ANM-023** (P0, Status: Ist) **Drosselung vor der Passwortprüfung**: Ist eine Wartezeit aktiv, wird das Passwort gar nicht geprüft; die Antwort ist 429 `too_many_attempts` mit `Retry-After` in Sekunden – auch bei richtigem Passwort („gesperrtes Konto und richtiges Passwort: trotzdem 429 bis Ablauf“). Die Oberfläche zeigt die Restzeit.
  Abnahme: Paar mit 5 Fehlversuchen, 6. Versuch mit **richtigem** Passwort innerhalb von 30 s → 429, `Retry-After` ≤ 30; nach Ablauf → Anmeldung gelingt.

- **ANM-024** (P1, Status: Ist) **Konfiguration**: `SM_LOGIN_MAX_FAILURES` = 5 (Fehlversuche, Schwelle Paar und Grundlage der Konto-Schwelle 4×), `SM_LOGIN_MAX_FAILURES_IP` = 30, `SM_LOGIN_LOCK_MINUTES` = 15 (Zählfenster in Minuten und Deckel der Wartezeit). Alle drei sind Umgebungsvariablen.
  Abnahme: Start mit `SM_LOGIN_MAX_FAILURES=3` → Wartezeit beginnt beim 3. Fehlversuch (Konto-Schwelle 12); Standardstart → 5 und 20.

- **ANM-025** (P0, Status: Ist) Die Wartezeiten der Tabellen „Paar und Konto“ (30 s verdoppelt je weiterem Fehlversuch bis 900 s) und „IP insgesamt“ (2 s, alle 10 weiteren Fehlversuche verdoppelt, bis 60 s) gelten verbindlich.
  Abnahme: Testfolge mit Uhr-Attrappe: Fehlversuche 1–4 frei; 5 → 30 s; 6 → 60 s; 7 → 120 s; 8 → 240 s; 9 → 480 s; ≥ 10 → 900 s; IP: 30 → 2 s, ab 40 → 4 s, ab 50 → 8 s … Deckel 60 s.

- **ANM-026** (P0, Status: Ist) **Paar-Zähler** (Benutzername + IP): wirkt nur auf die Anmeldung dieses Kontos von dieser IP; Zählung seit dem letzten Erfolg des Kontos innerhalb des Fensters; Erfolg des Kontos (auch SSO, Passwort-Zurücksetzen) setzt ihn zurück.
  Abnahme: 5 Fehlversuche von IP A → Konto von IP B weiterhin sofort anmeldbar; Erfolg von IP A → Zähler 0; Passwort-Zurücksetzen per Code → Zähler 0.

- **ANM-027** (P0, Status: Ist) **IP-Zähler**: Schwelle 30 Fehlversuche plus erfolgreiche Anmeldungen dieser IP im Fenster; wirkt auf alle Konten dieser IP, aber nur, wenn das Paar bereits mindestens 1 Fehlversuch hat – der erste Versuch eines Kontos von dieser IP ist immer frei; kein Zurücksetzen durch Erfolg, nur Ablauf des Fensters oder Aufheben durch die Verwaltung.
  Abnahme: 200 Anmeldungen verschiedener Konten hinter einer IP mit je einem Erfolg → keine Wartezeit; 31 Fehlversuche + 0 Erfolge, danach Konto mit erstem Versuch → sofort; dasselbe Konto mit zweitem Fehlversuch → 2 s Wartezeit.

- **ANM-028** (P0, Status: Ist) **Konto-Zähler**: 20 Fehlversuche je Konto seit dem letzten Erfolg; wirkt nur für IPs, von denen das Konto in den letzten 60 Tagen keinen Erfolg hatte (bekannte IP ausgenommen); Erfolg des Kontos (auch Passwort-Reset) setzt Paar- und Konto-Zähler zurück.
  Abnahme: 20 verteilte Fehlversuche von 20 fremden IPs → 21. Versuch von einer **neuen** IP: Wartezeit 30 s (Überschuss 1) bzw. gemäß Tabelle; derselbe Versuch von der bekannten IP: nur Paar-Zähler wirkt; Erfolg → alle Zähler des Kontos 0.

- **ANM-029** (P0, Status: Ist) Passwortprüfungen innerhalb der Sitzung (Passwort ändern, Zwei-Faktor abschalten, E-Mail/Handynummer ändern oder entfernen) unterliegen derselben Sperre; ein falsches Passwort zählt als Fehlversuch.
  Abnahme: 5× falsches altes Passwort beim Ändern → 6. Versuch → 429; 2FA-Abschalten mit falschem Passwort zählt ebenso.

- **ANM-030** (P1, Status: Ist) **Sperren sichtbar und aufhebbar**: Die Seite „Sicherheit“ (`/sicherheit`) listet aktive Sperren mit Restzeit; Konten-Einträge nur für Konten verwaltbarer Rollen, IP-Einträge nur mit `login_policy.manage`. Aufheben: Konto (Benutzername) mit `users.manage` und verwaltbarer Rolle löscht alle Fehlversuche des Kontos; IP mit `login_policy.manage` (Administration, Schulleitung) löscht die Fehlversuche der IP (`GET`/`DELETE /login-locks`); Konsolenbefehl `unlock` (Administration).
  Abnahme: Sekretariat hebt Sperre eines Schüler-Kontos auf → 200; Sperre eines Lehrer-Kontos → 404; IP-Sperre aufheben als Sekretariat → 403 bzw. Eintrag nicht sichtbar, als Schulleitung → 200; Restzeit in der Liste ± 1 s korrekt.

- **ANM-031** (P1, Status: Ist) **Aufbewahrung**: Anmeldeversuche 30 Tage (Wartung löscht Älteres); „bekannte IP“ = Erfolg von dieser IP in den letzten 60 Tagen; Passwort-Zurücksetzen und SSO sind nicht gedrosselt, haben aber eigene Limits (Abschnitt B10). Beim Löschen eines Kontos werden dessen Anmelde-Fehlversuche gelöscht.
  Abnahme: Versuch von 31 Tagen alter Zeile wird von der Wartung entfernt; Konto löschen → keine Zeile mit dem Benutzernamen in den Anmeldeversuchen.

- **ANM-032** (P0, Status: Ist) **Client-IP**: Socket-Adresse; nur mit `SM_TRUST_PROXY=1` wird `X-Forwarded-For` (Position je `SM_PROXY_COUNT` von rechts, Standard 1) bzw. sonst `X-Real-IP` ausgewertet, und nur von Absendern aus `SM_TRUSTED_PROXIES` (Standard nur Loopback; alter Name `SM_FORWARDED_ALLOW_IPS`); `X-Forwarded-Proto` ebenfalls nur von vertrauenswürdigem Proxy. Die Anwendung wird nie direkt veröffentlicht, sondern hinter einem Reverse-Proxy betrieben. Ohne Proxy-Vertrauen warnt der Start (Drosselung sähe nur die Proxy-Adresse).
  Abnahme: Direktaufruf mit gefälschtem `X-Forwarded-For` von nicht vertrauter Adresse → Drosselung zählt die Socket-Adresse; Aufruf über den konfigurierten Proxy → echte Client-IP; Start ohne `SM_TRUST_PROXY` → Warnung.

- **ANM-033** (P1, Status: Ist) **Allgemeines Rate-Limit** (`SM_RATE_LIMIT` = 1): je IP 6000 Anfragen/Minute (zugleich Burst), je Konto (Sitzung oder Token) 1200 Anfragen/Minute (`SM_RATE_IP_PER_MIN`, `SM_RATE_ACCOUNT_PER_MIN`); gezählt werden `/api/` und `/ical/`; ausgenommen Live-Strom, Gesundheitsprüfung, Metriken; Antwort 429 mit `Retry-After` und Grund `rate_limited`; Speicher höchstens 50 000 IP-Schlüssel und 20 000 Zugangsdaten-Zuordnungen, Schlüssel sind gekürzte Hashes der Zugangsdaten; Geltung je Knoten. Zusätzlich begrenzt der Reverse-Proxy den Anmeldeaufruf auf 10 je Minute und IP.
  Abnahme: Mit niedrig gesetzten Werten (Testinstanz): Überschreitung → 429 mit `Retry-After`; Live-Strom und Gesundheitsprüfung nie gebremst; Standardwerte 6000/1200.

- **ANM-034** (P1, Status: offen) Anmeldefehler (Fehlversuche, gedrosselte Anfragen, Sperr-Aufhebungen) werden im Audit festgehalten (Benutzername, IP, Zeitpunkt, Grund, ohne Passwörter) und Passwort-Spraying (viele Konten, wenige Versuche je Konto, wenige IPs) wird erkannt und gemeldet. [unklar: Erkennungsschwellen nicht vorgegeben; IP-Speicherung im Audit gegen die Zusage „gekürzte IP“ abstimmen (Datenschutz).]
  Abnahme: 50 Fehlversuche gegen 50 verschiedene Konten von einer IP in 10 Minuten → Alarm-Eintrag im Audit/Sicherheitsseite; jeder Fehlversuch hat einen Audit-Eintrag ohne Passwort.

## B4 Zwei-Faktor-Anmeldung (TOTP)

- **ANM-035** (P0, Status: Ist) **Verfahren**: TOTP nach RFC 6238 (App-Code, z. B. Authenticator-App) ist der einzige Zweitfaktor (kein SMS- oder E-Mail-Code als zweiter Faktor). HMAC-SHA1, Periode 30 s, 6 Ziffern, Prüfung mit Zeitfenster ±1 Schritt (bis 90 s Abweichung). Geheimnis: 20 Zufalls-Bytes, Base32 (32 Zeichen), verschlüsselt gespeichert (Rewrap bei Schlüsselrotation). Ein Code ist nur einmal innerhalb seines Gültigkeitsfensters verwendbar (Schutz vor Wiederholung).
  Abnahme: Code aus Referenz-Implementierung für aktuellen und je ±1 Schritt → akzeptiert, ±2 Schritte → abgelehnt; derselbe Code ein zweites Mal binnen 30 s → 401; Geheimnis in der Datenbank nicht im Klartext lesbar.

- **ANM-036** (P0, Status: Ist) **Einrichtung**: `POST /auth/2fa/setup` erzeugt ein inaktives Geheimnis und liefert `secret` und `otpauth_url` (QR-Code in der Oberfläche); `POST /auth/2fa/enable` mit `code` bestätigt und aktiviert; eine begonnene Einrichtung behält ihr Geheimnis, ein neues Geheimnis nur mit Parameter `neu=true`. Einrichten, Aktivieren und Abschalten nur mit Sitzung, nicht mit API-Token. Erst nach der Aktivierung ist 2FA aktiv.
  Abnahme: Setup zweimal → gleiches Geheimnis; Setup mit `neu=true` → anderes Geheimnis; Enable mit falschem Code → 422/401 und 2FA bleibt aus; mit API-Token → 403; nach Enable fordert die Anmeldung den Code (ANM-001).

- **ANM-037** (P0, Status: Ist) **Vorgabe der Schule** (Sicherheits-Einstellungen, Recht `login_policy.manage`): `twofa_mode` = `off` | `recommended` (Standard) | `required`; `twofa_roles` = betroffene Rollen (Standard admin, schulleitung, sekretariat; wählbar admin, schulleitung, planer, sekretariat, abteilungsleitung, lehrer). `recommended` = Hinweis auf der Startseite; `required` = Pflicht für die Rollen in `twofa_roles`; `off` = keine Vorgabe. Zusätzlich gilt `SM_REQUIRE_2FA_ROLES` (Rollenliste) als immer verpflichtend, unabhängig von der Schuleinstellung (Umgebungsvariable wird nicht gegen die Rollenliste geprüft).
  Abnahme: `required` + Rolle `sekretariat`: Sekretariat-Konto ohne 2FA kann nur die Einrichtung durchführen (ANM-038); `recommended` → nur Hinweis; `SM_REQUIRE_2FA_ROLES=lehrer` + `twofa_mode=off` → Lehrkraft muss trotzdem einrichten; Änderung der Einstellung ohne `login_policy.manage` → 403.

- **ANM-038** (P0, Status: Ist) **Pflicht ohne Einrichtung**: Ein Konto, für das 2FA verpflichtend ist, aber nicht eingerichtet, erhält eine Sitzung nur zur Einrichtung; alle Endpunkte außer den Anmelde-Pfaden liefern 403 `totp_setup_required` (nur bei Sitzung, nicht bei API-Token); eine eigene Seite führt durch die Einrichtung.
  Abnahme: Pflichtkonto ohne 2FA nach Passwort-Anmeldung: GET Stundenplan → 403 `totp_setup_required`, `POST /auth/2fa/setup` → 200; nach Enable → alles erreichbar.

- **ANM-039** (P0, Status: Ist) **Abschalten und Notweg**: Das Konto schaltet 2FA mit eigener Sitzung und aktuellem Passwort ab (Sperre ANM-029 beachtet; Protokoll `auth.2fa_disable`). Die Verwaltung darf 2FA eines Kontos **abschalten** (Geheimnis wird gelöscht; Konto bearbeiten, Zurücksetzen mit `disable_2fa`, Konsolenbefehl `disable-2fa`), aber nie einschalten (422 „2FA kann nur vom Benutzer selbst aktiviert werden“). Für das Inhaber-Konto gilt REC-026/027. Ein Passwort-Zurücksetzen lässt 2FA aktiv (der Code bleibt nötig).
  Abnahme: Admin schaltet 2FA eines Lehrers ab → Anmeldung ohne Code; Admin schaltet ein → 422; Passwort-Reset eines 2FA-Kontos → Anmeldung verlangt weiter den Code; zweiter Admin schaltet 2FA des Inhabers ab → 403.

- **ANM-040** (P0, Status: offen) **Pflicht für die Administration**: Zwei-Faktor ist für Konten der Grundrolle `admin` Pflicht (nicht nur empfohlen); die Administration kann diese Pflicht nicht abschalten. (Audit 17.10. überstimmt die Voreinstellung „empfohlen“ vom 16.10.; Sicherheitsdokumente nennen als Beispiel auch Schulleitung, Planung, Sekretariat – siehe ANM-037 für die einstellbare Pflicht der übrigen Rollen.)
  Abnahme: Neu angelegtes Admin-Konto: nach der ersten Anmeldung 403 `totp_setup_required` bis zur Einrichtung; `twofa_mode=off` ändert das nicht.

- **ANM-041** (P0, Status: offen) **Wiederherstellungscodes**: Bei Einrichtung von 2FA erzeugt der Server Wiederherstellungscodes, zeigt sie einmalig, speichert sie nur gehasht, jeder Code ist einmal verwendbar und ersetzt bei der Anmeldung den TOTP-Code; ein Verbrauch ist im Audit sichtbar und erzeugt eine Benachrichtigung an das Konto. Ein 2FA-Reset widerruft Sitzungen und Tokens des Kontos. [unklar: Anzahl und Format der Codes nicht vorgegeben; im Altbestand gibt es als Notweg nur das Abschalten durch Administration oder Konsole.]
  Abnahme: Nach Aktivierung werden Codes angezeigt; Anmeldung mit einem Code → Sitzung; derselbe Code ein zweites Mal → 401; Datenbank enthält nur Hashes; „Neue Codes erzeugen“ macht alte ungültig.

- **ANM-042** (P1, Status: offen) Der Wiederverwendungsschutz für TOTP-Codes gilt **über alle Prozesse und Knoten** (gemeinsamer Speicher), nicht nur je Prozess (Altbestand: prozesslokal).
  Abnahme: Mit zwei Serverprozessen: derselbe Code erst an Prozess 1 (Erfolg), dann an Prozess 2 binnen 30 s → 401.

- **ANM-043** (P1, Status: offen) **Passkeys (WebAuthn)** als weiterer Anmeldeweg: unter Konto › Sicherheit hinzufügen, benennen, entfernen; Anmeldung ohne Passwort; ein Passkey erfüllt die Zwei-Faktor-Pflicht; Bibliothek mit fester Version; Hinzufügen/Entfernen im Audit. Betreiber-Wunsch A-27 (Passwort-Manager, fälschungssichere Geräteerkennung).
  Abnahme: Test mit simuliertem Authenticator: Passkey registrieren → Anmeldung ohne Passwort gelingt; bei Pflichtkonto zählt der Passkey als Zwei-Faktor; entfernen → Anmeldung mit diesem Passkey scheitert; Audit-Einträge für Hinzufügen und Entfernen.

## B5 Anmeldung über Anbieter (SSO)

**Anbieter und Einstellungen**

| Anbieter | Kennung | Rückkehr-Adresse (Callback) | Einstellungen (Oberfläche oder `SM_*`) | Besonderheiten |
|---|---|---|---|---|
| Microsoft (Entra ID, Schul- und Arbeitskonten) | `microsoft` | `<SM_BASE_URL>/api/v1/auth/sso/microsoft/callback` (Port erlaubt, https Pflicht) | Client-ID (= Anwendungs-ID), Client-Secret, Mandant (`SM_SSO_MICROSOFT_CLIENT_ID`, `_CLIENT_SECRET`, `_TENANT`) | Code-Ablauf mit PKCE und Nonce; stille Anmeldung möglich; Mandant = Verzeichnis-ID (eine Schule) oder `organizations` (mehrere) |
| Google | `google` | `…/api/v1/auth/sso/google/callback` | Client-ID, Client-Secret, optional Workspace-Domain (`SM_SSO_GOOGLE_CLIENT_ID`, `_CLIENT_SECRET`, `_HD`) und erlaubte E-Mail-Domains | offizieller Knopf (Google Identity Services, One Tap); ID-Token geht an den Server |
| Apple | `apple` | `…/api/v1/auth/sso/apple/callback` (Rückgabe per POST/`form_post`) | Services-ID (= Client-ID), Team-ID, Schlüssel-ID, Inhalt der Schlüsseldatei (`SM_SSO_APPLE_CLIENT_ID`, `_TEAM_ID`, `_KEY_ID`, `_PRIVATE_KEY`) | Server erzeugt das Client-Secret selbst (ES256, kurz gültig; Apple erlaubt höchstens sechs Monate); Adresse muss auf Port 443 liegen; keine stille Anmeldung |
| Schulkonto (OpenID Connect) | `oidc` | `…/api/v1/auth/oidc/callback` (alter Pfad bleibt bestehen, `/auth/oidc/*`) | Issuer, Client-ID, Client-Secret (optional), Scopes (Standard `openid profile email`), Benutzernamen-Claim (Standard `preferred_username`), Auto-Anlage (Standard 0), Standardrolle (Standard `lehrer`), Beschriftung (Standard „Single Sign-on“) (`SM_OIDC_*`) | beliebiger OIDC-Anbieter (z. B. Keycloak, IServ, Authentik); nie simuliert |

Weitere Werte: Der Test-Anbieter `SM_SSO_DEV_MOCK` (Standard 0) ist nur in der Entwicklung erlaubt. Umgebungsvariablen haben Vorrang vor der Oberfläche.

- **ANM-044** (P0, Status: Ist) **Sichtbarkeit**: Auf der Anmeldeseite erscheint ein Anbieter-Knopf **nur**, wenn der Anbieter vollständig eingerichtet (Client-ID und Geheimnis bzw. Schlüssel) **und** eingeschaltet ist. Ohne eingeschalteten Anbieter lädt die Anmeldeseite nichts von Dritten. Es gibt keine Test- oder Platzhalterknöpfe (Betreiber 16.10.: „Ich will, dass es keine Testdinger sind, sondern offiziell“; „bitte die offiziellen Dinger benutzen“). Der Knopf „Mit Schulkonto anmelden“ erscheint nur, wenn die Schule einen eigenen OIDC-Anbieter eingerichtet hat, ist nicht Teil der festen Knopfreihe und wird nie simuliert. [unklar: Betreiber wollte „Mit Schulkonto anmelden“ entfernt haben (16.10.); der Altbestand behält OIDC als optionalen, nur bei Einrichtung sichtbaren Anbieter.]
  Abnahme: Frische Instanz ohne Einrichtung: Anmeldeseite zeigt keinen Anbieter-Knopf und löst keine Anfrage an Dritte aus (Netzwerkprotokoll des Browsers); Google eingerichtet und eingeschaltet → nur Google-Knopf; Google eingerichtet, ausgeschaltet → kein Knopf, kein Google-Skript; OIDC eingerichtet → „Mit Schulkonto anmelden“ (bzw. Beschriftung `SM_OIDC_LABEL`), ohne OIDC nie.

- **ANM-045** (P0, Status: Ist) **Ablauf** (Code-Ablauf): (1) Klick auf den Knopf → Weiterleitung zum Anbieter mit `state`, `nonce` und (Microsoft/OIDC) PKCE; (2) Rückkehr zur Callback-Adresse (GET, Apple per POST); (3) Server prüft das Token des Anbieters; (4) Konto finden (ANM-046); (5) Anmelde-Richtlinie für diese Anmeldeart prüfen (ANM-065); (6) Sitzung anlegen (neue Sitzung bei jeder Anmeldung, keine Fixierung); (7) Weiterleitung nur auf eigene Seiten (ANM-008). Der Anbieter liefert nie ein Passwort an die Anwendung.
  Abnahme: Anbieter-Attrappe durchläuft den Ablauf: Rückkehr mit falschem `state` → Fehlerseite „Anmeldung nicht möglich“ (deutscher Text je Fehlerfall), keine Sitzung; Rückkehr mit richtigem Ergebnis → Sitzung, Weiterleitung auf `/`; Rückkehr, bei der die Richtlinie die Anmeldeart verbietet → 403 `method_not_allowed`.

- **ANM-046** (P0, Status: Ist) **Konto-Zuordnung**: Die Anbieter-Anmeldung findet ein **bestehendes** Konto über (a) eine verbundene Identität (Tabelle `user_identities`: Anbieter, Kennung beim Anbieter, E-Mail, Zeitpunkt der letzten Anmeldung, Name nur bei der ersten Apple-Anmeldung) oder (b) eine von der Verwaltung reservierte (vorgemerkte) E-Mail-Adresse. Eine Zuordnung per E-Mail gilt nur mit **bestätigter** Adresse (Microsoft: nur bei fester Verzeichnis-ID als Mandant gelten E-Mail-Adressen als bestätigt). Findet sich kein Konto, entsteht standardmäßig keines; nur die ausdrückliche Option `sso_create` (Standard aus; OIDC: `SM_OIDC_AUTO_CREATE`) legt ein Konto mit der konfigurierten Standardrolle an – nie ein Administrationskonto. Apple-Relay-Adressen passen nicht zu vorgemerkten Schul-Adressen; dann verbindet die Person im Profil. [unklar: „Wer darf ein Konto per Anbieter erstellen“ ist im Altbestand nur als E-Mail-Zuordnung abgebildet.]
  Abnahme: Anbieter-Identität ohne Konto und ohne `sso_create` → keine Sitzung, kein Konto angelegt; mit vorgemerkter E-Mail → Konto gefunden und Identität verbunden; unbestätigte Anbieter-E-Mail → keine Zuordnung per E-Mail; `sso_create` an → Konto mit Standardrolle, nie `admin`; Identität eines Admin-Kontos über OIDC-Benutzernamen-Claim wird nicht automatisch zugeordnet.

- **ANM-047** (P0, Status: offen) **Zwei-Faktor und Anbieter-Anmeldung**: Die Zwei-Faktor-Regel (Pflicht je Rolle, ANM-037/040) gilt auf **allen** Anmeldewegen. Ist für das Konto 2FA verpflichtend oder eingerichtet, verlangt die Anmeldung über einen Anbieter nach der Anbieter-Prüfung den lokalen Code (bzw. erzwingt die Einrichtung `totp_setup_required`); die Anmeldung beim Anbieter ersetzt die lokale 2FA nicht. [unklar: ob eine nachweislich vom Anbieter durchgeführte Mehrfaktor-Anmeldung (Claim) als Ersatz anerkannt wird; Altbestand: „es gilt die Anmeldung des Anbieters inklusive dessen Zwei-Faktor“; Audit 17.10.: „SSO umgeht lokale 2FA“.]
  Abnahme: Admin-Konto (2FA Pflicht) mit eingerichtetem TOTP meldet sich per Microsoft an → danach Code-Abfrage, erst dann Sitzung; Pflichtkonto ohne TOTP → Sitzung nur zur Einrichtung.

- **ANM-048** (P0, Status: Ist) **Schutz des Anbieter-Ablaufs**: Authorization Code mit PKCE (S256); `state` und `nonce` (24 Zufalls-Bytes, URL-sicher) im verschlüsselten Status-Cookie `sm_sso_<Anbieter>` (Gültigkeit 600 s, einmalig verwendbar, Pfad `/api/v1/auth`; eine nur signierte Variante gibt es ausschließlich für den Test-Anbieter); ID-Token wird geprüft auf Signatur (JWKS des Anbieters), `iss`, `aud`, `exp`, `nonce`; Anbieter-Konfiguration (Discovery) und Schlüssel (JWKS) werden 3600 s zwischengespeichert; ausgehende Verbindungen nur an geprüfte öffentliche Ziele (`SM_OUTBOUND_ALLOW` für Ausnahmen). Ein Wechsel von `SM_ENCRYPTION_KEYS` macht laufende Anbieter-Anmeldungen ungültig.
  Abnahme: Manipuliertes `nonce`/`aud`/`iss`, abgelaufenes `exp`, fremde Signatur → je abgelehnt; Status-Cookie zweimal verwendet → zweites Mal abgelehnt; Cookie älter als 600 s → abgelehnt; OIDC-Aussteller mit internem Ziel (Loopback/privates Netz) → Verbindung verweigert, ohne Antwortinhalt in der Fehlermeldung.

- **ANM-049** (P2, Status: Ist) **Automatische (stille) Anmeldung**: nur für Microsoft und Google, je Anbieter abschaltbar, **Standard aus** (Risiko auf gemeinsam genutzten Schulrechnern; der Betreiber wollte „flüssiger“ anmelden, die Umsetzung ist bewusst aus). Microsoft: Wer sich zuletzt mit Microsoft angemeldet hat und noch dort angemeldet ist, wird beim Öffnen der Anmeldeseite ohne Klick angemeldet (`prompt=none`, einmal je Tab; Scheitern zeigt ohne Fehlermeldung die gewohnte Seite). Google: One Tap mit Auto-Auswahl („Weiter als …“). Apple: keine stille Anmeldung. Hinweis-Cookies: `sm_sso_hint` enthält nur die Anbieter-Kennung (90 Tage), `sm_sso_who` die verschlüsselte E-Mail (httponly, 90 Tage); beide werden beim Abmelden gelöscht; nach dem Abmelden erfolgt keine stille Rückanmeldung bis zur nächsten Anmeldung. Stille Fehler (`login_required`, `interaction_required`, `consent_required`, `account_selection_required`) werden nicht als Fehler angezeigt. [unklar: Betreiber hat „Standard aus“ nicht bestätigt; Rechtsgrundlage/Einwilligung für die 90-Tage-Cookies nicht beschrieben.]
  Abnahme: Neu eingerichteter Anbieter → „automatische Anmeldung“ aus; eingeschaltet + Microsoft-Sitzung im Browser → Anmeldeseite meldet ohne Klick an; Abmelden → Cookies `sm_sso_hint` und `sm_sso_who` gelöscht, nächste Anmeldeseite meldet nicht automatisch an; Apple-Einstellung hat keine solche Option.

- **ANM-050** (P1, Status: Ist) **Microsoft**: offizieller Knopf „Mit Microsoft anmelden“ (Weiterleitung, kein Skript des Anbieters), App-Registrierung „Nur dieses Verzeichnis“ (Variante je Schule) oder „mehrere Verzeichnisse“ (zentrale Registrierung); Plattform Web, Umleitungs-Adresse mit Port erlaubt (Microsoft verlangt den Port in der Rückkehr-Adresse, sonst Fehler 404), https Pflicht; Berechtigungen nur `openid`, `profile`, `email` (delegiert); Client-Secret wird beim Anbieter nur einmal angezeigt und hat ein Ablaufdatum (notieren). Entscheidet die Schul-IT, dass Nutzer nicht selbst zustimmen dürfen, erteilt sie einmalig die Administratorzustimmung für die Schule.
  Abnahme: Einrichtung mit Mandanten-ID und Test-Knopf „Verbindung testen“ → Erfolgsmeldung; Mandant `organizations` → E-Mail-Adressen gelten **nicht** als bestätigt; Rückkehr-Adresse ohne Port bei Instanz mit Port → Fehler bereits beim Test.

- **ANM-051** (P1, Status: Ist) **Google**: Knopf von Google (Google Identity Services) mit FedCM, One Tap optional; der Browser erhält das ID-Token von Google, der Server prüft Signatur, `iss`, `aud`, `exp`, `nonce`; fehlt das Skript (Werbeblocker), erscheint der gewöhnliche Knopf mit Weiterleitung. Zustimmungsbildschirm „Intern“ (Workspace) oder „Extern“, Bereiche nur `openid`, `email`, `profile`, Status „In Produktion“; autorisierte JavaScript-Quellen nur Schema, Host, Port ohne Pfad; Weiterleitungs-URI exakt (Pfad, Schreibweise, ohne Muster); optional Workspace-Domain (`hd`) und erlaubte E-Mail-Domains. Google sichert bei Quellen mit Port nichts zu: nach dem Eintragen Probeanmeldung; One Tap zeigt Google nur auf https.
  Abnahme: Mit Attrappe: gültiges ID-Token der erlaubten Domain → Anmeldung; Token einer anderen Domain bei gesetztem `hd` → abgelehnt; Skript blockiert → Weiterleitungs-Knopf funktioniert.

- **ANM-052** (P2, Status: Ist) **Apple**: Knopf von Apple (Popup, schwarz, Beschriftung „Mit Apple anmelden“, Sprachvariante de_DE), Rückfall Weiterleitung (`form_post`); Server prüft ID-Token (Apples öffentliche Schlüssel, `iss`, `aud`, `exp`, `nonce`) und erzeugt das Client-Secret (ES256) aus der hinterlegten Schlüsseldatei; Name und E-Mail liefert Apple nur bei der ersten Anmeldung; Relay-Adressen („E-Mail-Adresse verbergen“) werden normal behandelt, passen aber nicht zu vorgemerkten Adressen; Domain nur ohne Port; **Adresse muss auf Port 443 liegen** (kein localhost, kein eigener Port), die Einstellungsseite zeigt dazu einen Hinweis, solange `SM_BASE_URL` einen Port hat. Kosten: Apple Developer Program 99 US-Dollar/Jahr (Gebührenbefreiung für Bildungseinrichtungen beantragbar).
  Abnahme: `SM_BASE_URL` mit Port → Einstellungsseite zeigt den Port-Hinweis bei Apple; ID-Token mit falscher `aud` → abgelehnt; Rückgabe per POST wird akzeptiert, Cookie `sm_sso_apple` mit SameSite=None und Secure bei https.

- **ANM-053** (P1, Status: Ist) **Schulkonto (OIDC)**: Beliebiger OIDC-Anbieter mit Code-Ablauf, vertraulichem Client und Token-Abruf per TLS; Weiterleitungs-URI `…/api/v1/auth/oidc/callback`; Aussteller-Adresse, Client-ID, Client-Secret; Benutzername aus dem konfigurierten Claim; Auto-Anlage nur wenn `SM_OIDC_AUTO_CREATE=1`, dann mit `SM_OIDC_DEFAULT_ROLE`. Aktiv nur mit Aussteller **und** Client-ID.
  Abnahme: Ohne Issuer oder Client-ID kein Knopf; mit Attrappe-Aussteller Ablauf wie ANM-045; Auto-Anlage aus → kein Konto.

- **ANM-054** (P0, Status: Ist) **Einrichtungsseite „Anmeldedienste“** (`/anmeldedienste`, nur Administration/Rolle `admin`, Prüfung im Server): je Anbieter die Adressen zum Kopieren (Rückkehr-Adresse, Quelle), Felder für Client-ID und Geheimnis/Schlüssel, Mandant bzw. Domains, Schalter „Einschalten“, Schalter „automatische Anmeldung“, Knopf „Verbindung testen“. Geheimnisse werden verschlüsselt gespeichert und nie wieder angezeigt (nur ersetzbar). Ausschalten entfernt die Anbieter-Skripte sofort. Die Seite hat eine Überschrift (h1), keine Erklär-Absätze (Hilfe hinter „?“) und zeigt den Apple-Port-Hinweis. Umgebungsvariablen `SM_SSO_*`/`SM_OIDC_*` haben Vorrang und sind als „vom Server vorgegeben“ gekennzeichnet.
  Abnahme: Als Schulleitung `GET /sso/providers/config` → 403/404 (nur Administration); Geheimnis speichern → Antwort und spätere Anzeige zeigen es nie, Datenbankfeld verschlüsselt; „Verbindung testen“ mit falscher Client-ID → verständliche deutsche Fehlermeldung; Ausschalten → beim nächsten Laden der Anmeldeseite kein Skript.

- **ANM-055** (P1, Status: Ist) **Verbundene Konten**: Im Profil je Anbieter Status („verbunden als …, seit …“), Verbinden (Anmeldung beim Anbieter) und Trennen (`GET/POST/DELETE /me/identities…`). Die Verwaltung (`users.manage`, verwaltbare Rolle) kann für ein Konto eine Identität vorab reservieren (E-Mail-Adresse bei einem Anbieter) und eine Verknüpfung entfernen (`GET/POST/DELETE /users/{id}/identities…`; Reiter „Verbundene Konten“ im Konto-Dialog). Eine Pflicht-Verbindung (Anmelde-Richtlinie) lässt sich nicht trennen. [unklar: Altbestand beschreibt das Trennen einer Pflicht-Verbindung nicht; Standard: nicht trennbar.]
  Abnahme: Verbinden → Eintrag „verbunden als <E-Mail>, seit <Datum>“; Trennen → nächste Anbieter-Anmeldung findet das Konto nicht mehr; Sekretariat reserviert für Lehrerkonto → 404; Pflicht-Verbindung trennen → 409.

- **ANM-056** (P1, Status: Ist) **Pflicht-Verknüpfung**: Verlangt die Anmelde-Richtlinie eine Verbindung zu einem Anbieter und fehlt sie, erhält das Konto `link_required` (ANM-005); erreichbar sind nur Anmelde-Pfade und Identitäten; die Seite „Konten verbinden“ (`/konten-verbinden`) stellt die Pflicht-Verbindungen her. Bei Ersteinrichtung (Startpasswort plus fehlende Pflicht-Verknüpfung mit verfügbarem Anbieter) entsteht eine Sitzung nur zum Verbinden (`password_setup`). Das Startpasswort wird nur gedruckt, wenn die Passwort-Anmeldung erlaubt ist oder eine Pflicht-Verknüpfung besteht; sonst steht im Brief der Hinweis zum Anmeldeweg. Klassenbericht: Konten mit fehlender Pflicht-Verknüpfung, mit Zählung.
  Abnahme: Konto mit Pflicht „Microsoft“ meldet sich mit Startpasswort an → Sitzung nur zum Verbinden, Stundenplan 403 `link_required`, nach Verbinden alles erreichbar; Bericht zählt Konten ohne Verbindung.

- **ANM-057** (P0, Status: offen) **Anbieter für Minderjährige**: Google und Apple sind für die Rolle Schüler/in standardmäßig **nicht** erlaubt (Standardregel der Anmelde-Richtlinie, steuerbar je Rolle, Klasse, Jahrgang, Person); sie sind eine freiwillige Option für Personal und Eltern. Die Passwort-Anmeldung bleibt gleichwertig (Freiwilligkeit der Einwilligung). Microsoft ist sinnvoll für Schulen mit Microsoft 365. [unklar: Empfehlung des Assistenten (16.10.), vom Betreiber nicht bestätigt; der Altbestand erlaubt standardmäßig alle Anmeldewege (ANM-066).]
  Abnahme: Frische Instanz, Rolle `schueler`: Anbieter „Google“ und „Apple“ in der wirksamen Richtlinie nicht erlaubt (Vorschau der Person zeigt Herkunft „Standard“); Lehrkraft: erlaubt, falls eingeschaltet; Schüler-Anmeldung über Google → 403 `method_not_allowed`.

- **ANM-058** (P0, Status: Ist) **Datenfluss und Skripte**: Skripte von Google/Apple werden erst geladen, wenn der Anbieter aktiv ist; die Content-Security-Policy der Anwendung passt sich daran an und wird von der Anwendung gesetzt (der Reverse-Proxy darf keine eigene feste Richtlinie setzen, sonst werden Anbieter-Skripte blockiert); Microsoft braucht kein Skript. Beim Ausschalten entfallen die Skripte sofort. Ohne Anbieter keine Fremdquellen im Browser. Die Anmeldeseite hat neben „oder“ ein „?“, das den Datenschutz kurz erklärt (Google/Apple sehen IP-Adresse und Browser; ID-Token mit Kennung, Name, E-Mail geht an die Schule). Die Datenschutzerklärung nennt diese Drittanbieter-Skripte (Zusage „keine fremden Skripte“ gilt nur ohne SSO).
  Abnahme: Anbieter aus: Antwort-Kopfzeile CSP ohne Google/Apple-Quellen; Google an: CSP enthält die Google-Quellen und der Browser lädt das Skript erst nach der Anmeldeseite; „?“ zeigt den Datenschutztext; Proxy-Konfiguration ohne eigene CSP-Zeile.

- **ANM-059** (P2, Status: Ist) **Knopf-Gestaltung** nach den Vorgaben der Anbieter: Google-Knopf und Apple-Knopf kommen zur Laufzeit vom Anbieter (Apple schwarz, de_DE); Microsoft: „Mit Microsoft anmelden“ mit vierfarbigem eingebettetem Logo (unverändert), Höhe 41 px, Rahmen `#8C8C8C`, Text `#5E5E5E`, Schrift Segoe UI 15 px, im dunklen Schema Fläche `#2F2F2F`. Im Entwicklungs-Testbetrieb trägt ein simulierter Knopf den Zusatz „(Test)“.
  Abnahme: Microsoft-Knopf misst 41 px Höhe, Farbwerte wie angegeben (hell/dunkel); Google- und Apple-Logos liegen nicht im Projekt.

- **ANM-060** (P0, Status: Ist) **Adressen**: `SM_BASE_URL` ist die Adresse, unter der Nutzer die Seite öffnen (mit Port, ohne Schluss-Schrägstrich); aus ihr werden alle Mail-Links, die Anmelde-Adresse (`/login`) und alle Rückkehr-Adressen gebildet. In Produktion Pflicht und https (außer lokal). Google/Microsoft verlangen die exakte Adresse, Apple nur Domain ohne Port auf Port 443.
  Abnahme: `SM_BASE_URL` fehlt in Produktion → Startfehler; http-Adresse → Startfehler; Rückkehr-Adressen in der Einstellungsseite entsprechen exakt `<SM_BASE_URL>/api/v1/auth/sso/<anbieter>/callback`.

- **ANM-061** (P0, Status: Ist) **Test-Anbieter** nur in der Entwicklung: mit `SM_SSO_DEV_MOCK=1` und `SM_ENV=development` erscheinen nicht eingerichtete Anbieter als „Mit … anmelden (Test)“ und simulieren die Anmeldung (Code 120 s gültig); sobald ein Anbieter eingerichtet und eingeschaltet ist, entfällt die Kennzeichnung; in Produktion, Demo oder öffentlicher Demo verweigert der Start den Schalter. Test-Anmeldung nur an verknüpfte oder vorgemerkte Konten, nie an Administrationskonten; das Schulkonto wird nie simuliert.
  Abnahme: `SM_SSO_DEV_MOCK=1` mit `SM_ENV=production` → Startabbruch; Entwicklung → „(Test)“-Knöpfe; Test-Anmeldung als Admin-Konto → abgelehnt.

- **ANM-062** (P3, Status: offen) **Zentraler Anmelde-Vermittler** (für viele Schulen mit eigenen Subdomains; Empfehlung bei der **zweiten** Schule, bis dahin eine feste Adresse auf Port 443): Bei den Anbietern steht nur eine Rückkehr-Adresse. Die Schul-Instanz leitet mit `state`, `nonce`, Schulkennung und signiertem Rückgabe-Hinweis an den Vermittler; dieser prüft die Rückgabe-Adresse gegen eine hinterlegte Liste, führt den Anbieter-Ablauf (eigene `state`, `nonce`, PKCE S256, vollständige Token-Prüfung, bei Microsoft zusätzlich den Mandanten) und gibt eine eigene signierte Behauptung zurück: höchstens 60 s gültig, einmal einlösbar, JWT mit Ed25519 oder ES256, Felder `aud`, `iss`, `sub`, `email`, `email_verified`, `nonce`, `jti`, Übergabe per Formular-POST oder Fragment (nicht im Abfrageteil). Die Schul-Instanz prüft Signatur, `aud` (nur eigene Adresse), `exp`, `jti` (einmalig), `state`, `nonce` und lehnt Werte anderer Schulen ab. Der Vermittler speichert nur eine kurze Zwischenablage (wenige Minuten), kein Anmeldeprotokoll mit E-Mail im Klartext; Auftragsverarbeitung und Verzeichniseintrag sind vorab zu klären.
  Abnahme: Test mit zwei Schul-Instanzen: Behauptung für Schule A bei Schule B → abgewiesen; zweites Einlösen derselben `jti` → abgewiesen; Behauptung älter als 60 s → abgewiesen; Rückgabe-Adresse nicht auf der Liste → Vermittler verweigert.

- **ANM-063** (P3, Status: offen) **Landes-Login** (Schulconnex/VIDIS) und LTI 1.3 als spätere Anbindung („groß, später“); Voraussetzung für den Verkauf in einzelnen Bundesländern; die OIDC-Grundlage besteht, Aufnahme in den Katalog ist Vertrag und Zertifizierung. QR-Login für Kinder nur auf ausdrücklichen Wunsch und nach Klärung der Sicherheitsfragen. [unklar: Bedingungen der Länder nicht geprüft; Betreiber-Entscheidung offen.]
  Abnahme: Dokumentierte Entscheidung des Betreibers (Ja/Nein, Termin); bei Ja: Anbindung als zusätzlicher Anbieter mit Anmelde-Richtlinie, ohne Änderung der Passwort-Anmeldung.

- **ANM-064** (P3, Status: offen) Erinnerung an Erneuerungstermine der Anbieter-Zugänge: Die Einstellungsseite erinnert vor Ablauf des Microsoft-Clientschlüssels, des jährlichen Apple-Entwicklerkontos und des Apple-Schlüssels (Termin einzutragen; Altbestand: keine Erinnerung).
  Abnahme: Termin eingetragen → vor dem Termin erscheint ein Hinweis für die Administration auf Startseite und Einstellungsseite; nach dem Termin bleibt er bis zur Erneuerung sichtbar [unklar: Vorlaufzeit legt der Betreiber fest].

## B6 Anmelde-Richtlinie und Sicherheits-Einstellungen

- **ANM-065** (P0, Status: Ist) **Anmelde-Richtlinie**: Regeln legen fest, wer sich wie anmelden darf. Felder: erlaubte Anmeldewege (Passwort, Microsoft, Apple, Google, Schulkonto; mindestens ein Weg, leere Liste → 422), Kanäle für das Zurücksetzen (E-Mail, SMS), Pflicht-Verknüpfungen zu Anbietern, „eigene Verknüpfung erlaubt“, „Zuordnung per E-Mail beim ersten Anbieter-Login“ und „Passwort vergessen per“ (Selbstbedienung erlaubt). Die Richtlinie wirkt bei Anmeldung (Schritt 7), Passwort-Zurücksetzen, Verknüpfung und Ersteinrichtung. Ändern nur mit `login_policy.manage` (Administration, Schulleitung); Änderungen wirken sofort (Zwischenspeicher höchstens 5 s, wird bei jeder Änderung geleert). Eine Regel, die den **eigenen** Anmeldeweg des Änderers entfernt, wird mit 409 abgelehnt.
  Abnahme: Regel „nur Microsoft“ für Rolle `lehrer` → Lehrkraft-Anmeldung mit Passwort 403 `method_not_allowed` mit Kopfzeile `X-Login-Methods`; Regel ohne Weg → 422; Schulleitung entfernt für ihre eigene Person alle erreichbaren Wege → 409; Änderung wirkt für das nächste Anmelden ohne Neustart (≤ 5 s); Änderung ohne `login_policy.manage` → 403.

- **ANM-066** (P1, Status: Ist) **Standardwerte** (Schule): alle Anmeldewege erlaubt; Reset-Kanäle E-Mail und SMS; keine Pflicht-Verknüpfungen; eigene Verknüpfung erlaubt; Zuordnung per E-Mail beim ersten Anbieter-Login aus; „Passwort vergessen per“: Schüler/innen **aus**, Eltern und Lehrkräfte an (Begründung: Kinder haben selten eine bestätigte E-Mail-Adresse oder Handynummer, die Klassenleitung hilft sofort). Ist die Option aus, antwortet „Passwort vergessen“ neutral ohne Versand; der Hinweis lautet in Sie-Form „Bitte wenden Sie sich an Ihre Klassenleitung.“ [Sie-Form aus dem früheren „Bitte wende dich an deine Klassenleitung“ abgeleitet]. Hinweis: Wird die Schüler-Regel auf „erben“ gestellt, erhalten Schüler/innen die Option zurück (Hinweis in der Oberfläche).
  Abnahme: Frische Instanz: wirksame Richtlinie für `schueler` → Passwort-Zurücksetzen nicht erlaubt, `eltern`/`lehrer` erlaubt; „Passwort vergessen“ eines Schülers → neutrale Antwort, kein Versand, Hinweistext; Schüler-Regel auf „erben“ → Schüler erlaubt.

- **ANM-067** (P1, Status: Ist) **Rangfolge je Feld** (erste gesetzte Regel gewinnt): 1. Person, 2. Klasse (Zielgruppe, dann alle), 3. Jahrgang (Zielgruppe, dann alle), 4. Rolle, 5. Standard der Schule, 6. Voreinstellung. Zielgruppen (Schüler/innen oder Eltern) gibt es nur bei Jahrgang und Klasse. Je Feld „erbt“ oder eigener Wert; leer bei „Passwort vergessen per“ heißt nicht erlaubt. Der geerbte Wert wird mit seiner Herkunft angezeigt.
  Abnahme: Regel Rolle `lehrer` „Passwort aus“, Regel Person X „Passwort an“ → X darf; Regel Klasse 5a (Zielgruppe Eltern) gilt nicht für Schüler/innen der 5a; Vorschau einer Person zeigt je Feld Wert und Herkunft (z. B. „Klasse 5a“).

- **ANM-068** (P1, Status: Ist) **Eltern mit mehreren Kindern**: Wege, Kanäle und Pflicht-Verknüpfungen sind die Vereinigung über alle Kinder; ein Schalter ist wahr, wenn eine Regel wahr ist.
  Abnahme: Kind A (Regel: nur Passwort), Kind B (Regel: Passwort und Microsoft) → Elternkonto darf beide Wege; Pflicht-Verknüpfung nur bei Kind B → gilt für das Elternkonto.

- **ANM-069** (P0, Status: Ist) **Schutz der Administration in der Richtlinie**: Für die Administration ist Passwort immer erlaubt und es gibt keine Pflicht-Verknüpfungen (Schutz vor Aussperrung); Regeln für das Admin-Konto ändert nur der Admin selbst (Hinweis in der Oberfläche: Das Admin-Konto bleibt immer mit Passwort anmeldbar).
  Abnahme: Regel „kein Passwort“ für Rolle `admin` → wirkungslos, Admin meldet sich mit Passwort an; Schulleitung ändert eine Regel auf Person `admin` → 403.

- **ANM-070** (P2, Status: offen) Richtlinien-Ebenen **Klassengruppe** und **Abteilung** (zusätzlich zu Person, Klasse, Jahrgang, Rolle) sowie die Frage „wer darf ein Konto per Anbieter erstellen“ als echte Regel statt nur E-Mail-Zuordnung (Betreiber-Wunsch A-22/A-43). Die Rangfolge (ANM-067) wird um die neuen Ebenen erweitert und in Server und Oberfläche aus **einer** Liste gespeist.
  Abnahme: Regel auf Klassengruppe „Abi-Klassen“ wirkt für alle Klassen der Gruppe; Rangfolge Klasse > Gruppe > Jahrgang; Bericht listet die Gruppe als Zielgruppe.

- **ANM-071** (P1, Status: Ist) **Oberfläche „Anmelde-Richtlinien“** (`/anmelde-richtlinien`, `login_policy.manage`): Ebenen Schule/Rolle/Klasse/Jahrgang/Person, Ziel-Gruppen mit Personen-Suche, **Vorschau** für eine Person (wirksame Werte mit Herkunft), **Bericht** je Gruppe (Konten mit fehlender Pflicht-Verknüpfung, mit Zählung); Hinweis für Administratoren, welche Versandwege fehlen (E-Mail/SMS), wenn Kanäle nicht verfügbar sind; Erklärungen hinter „?“.
  Abnahme: Vorschau Person → 6 Felder mit Herkunft; Bericht zählt Konten ohne Pflicht-Verbindung; ohne SMTP zeigt die Seite „E-Mail-Versand nicht eingerichtet“ (Sie-Form).

- **ANM-072** (P0, Status: Ist) **Sicherheits-Einstellungen der Schule** (Seite „Sicherheit“, `/sicherheit`, `login_policy.manage`; Zwischenspeicher 5 s):

  | Schlüssel | Standard | Bereich | Wirkung |
  |---|---|---|---|
  | `twofa_mode` | `recommended` | `off`, `recommended`, `required` | Zwei-Faktor-Vorgabe für Personal |
  | `twofa_roles` | admin, schulleitung, sekretariat | admin, schulleitung, planer, sekretariat, abteilungsleitung, lehrer | betroffene Rollen |
  | `staff_idle_minutes` | 720 (12 Stunden) | 15 bis 10080 Minuten | Leerlauf-Abmeldung Personal |
  | `initial_password_days` | 14 | 1 bis 90 Tage | Startpasswort-Frist |
  | `hibp_check` | aus | ein, aus | Leak-Prüfung neuer selbst gewählter Passwörter |

  Außerdem listet die Seite aktive Anmelde-Sperren mit Restzeit und erlaubt das Aufheben (ANM-030). Werte außerhalb des Bereichs → 422.
  Abnahme: `staff_idle_minutes=14` oder `10081` → 422; `initial_password_days=91` → 422; Änderung ohne `login_policy.manage` → 403; Änderung wirkt höchstens 5 s später; die Seite zeigt Sperren mit Restzeit.

## B7 Sitzungen, Cookies, Abmelden

**Cookies**

| Cookie | Inhalt | HttpOnly | SameSite | Secure | Pfad | Laufzeit |
|---|---|---|---|---|---|---|
| `sm_session` | Sitzungs-Token | ja | Lax | ja, wenn `SM_COOKIE_SECURE=1` oder Anfrage über HTTPS (hinter Proxy über `X-Forwarded-Proto`, nur mit Proxy-Vertrauen) | `/` | 30 Tage (`SM_SESSION_MAX_DAYS`) |
| `sm_sessions` | Tokens weiterer Konten, durch `~` getrennt; max. 4 weitere | ja | Lax | wie `sm_session` | `/` | 30 Tage |
| `sm_sso_hint` | Kennung des zuletzt genutzten Anbieters | nein | Lax | nur `SM_COOKIE_SECURE` | `/` | 90 Tage |
| `sm_sso_who` | verschlüsselte E-Mail für stilles SSO | ja | Lax | nur `SM_COOKIE_SECURE` | `/` | 90 Tage |
| `sm_sso_<Anbieter>` | verschlüsselter Status (Zustand, Nonce) | ja | Lax; bei Apple (Rückgabe per Formular) None | bei Formular-Rückgabe und HTTPS ja; sonst `SM_COOKIE_SECURE` | `/api/v1/auth` | 600 Sekunden |

- **ANM-073** (P0, Status: Ist) **Sitzungs-Token und CSRF**: Sitzungs-Token = 32 Zufalls-Bytes (URL-sicher) im Cookie; in der Datenbank nur als HMAC-SHA256 mit `SM_SECRET_KEY` gespeichert (nie der Token selbst). Neue Sitzung bei jeder Anmeldung (keine Fixierung). Je Sitzung ein CSRF-Token (24 Zufalls-Bytes), das bei POST, PUT, PATCH und DELETE mit Sitzungs-Cookie im Header `X-CSRF-Token` mitgesendet werden muss (sonst 403 `csrf_failed`); die Anmeldung liefert es in der Antwort. Für Konto-Endpunkte ohne Sitzung (Kontoliste/Kontowechsel) gilt Header `X-Requested-With: schulmanager` plus passende Herkunft (Origin). Ein Wechsel von `SM_SECRET_KEY` macht alle Sitzungen, API-Token und offenen Codes ungültig; ohne schreibbares Datenverzeichnis erzeugt die Entwicklung einen zufälligen Schlüssel je Start.
  Abnahme: Schreibender Aufruf mit Cookie ohne `X-CSRF-Token` → 403 `csrf_failed`; mit Token einer anderen Sitzung → 403; Datenbankabzug enthält keinen verwendbaren Sitzungswert (Anmeldung mit dem gespeicherten Wert scheitert); zwei Anmeldungen ergeben zwei verschiedene Token; Schlüsselwechsel → alle Sitzungen 401.

- **ANM-074** (P0, Status: Ist) **Dauer**: Absolute Sitzungsdauer 30 Tage ab Anmeldung (`SM_SESSION_MAX_DAYS`, danach nicht verlängerbar; zugleich Cookie-Laufzeit). Leerlauf-Abmeldung: Schüler/innen, Eltern, Monitor 10080 Minuten (7 Tage, `SM_SESSION_IDLE_MINUTES`); Personal (Grundrollen admin, schulleitung, planer, sekretariat, abteilungsleitung, lehrer, schulbegleitung, hausmeister) = Minimum aus Schuleinstellung `staff_idle_minutes` (Standard 720 Minuten = 12 Stunden, Bereich 15 bis 10080) und `SM_SESSION_IDLE_MINUTES`. [unklar: Sicherheitsprüfung 13.10. verlangt zu prüfen, ob 7 Tage Leerlauf für Schüler/Eltern angemessen sind.]
  Abnahme: Mit Uhr-Attrappe: Lehrkraft-Sitzung 12 h 1 min inaktiv → 401; Schüler-Sitzung 6 Tage inaktiv → gültig, 7 Tage 1 min → 401; aktive Sitzung nach 30 Tagen 1 min → 401; `staff_idle_minutes=60` → Lehrkraft nach 61 min 401.

- **ANM-075** (P1, Status: Ist) **Gleitende Verlängerung**: Bei Aktivität wird das Ablaufdatum höchstens alle 60 s fortgeschrieben: neues Ablaufdatum = Minimum aus (jetzt + Leerlaufdauer) und (Anmeldung + 30 Tage). Die Ablaufprüfung erfolgt bei jeder Anfrage; abgelaufen = nicht angemeldet. Abgelaufene Sitzungen löscht der Wartungslauf (alle 3600 s, `SM_MAINTENANCE_INTERVAL`, mindestens 5 s). [unklar: ein Hinweis vor der Leerlauf-Abmeldung ist im Altbestand nicht vorhanden.]
  Abnahme: Zwei Anfragen im Abstand von 30 s verändern das Ablaufdatum nur einmal; Anfrage nach 61 s verschiebt es; Wartungslauf entfernt abgelaufene Zeilen.

- **ANM-076** (P1, Status: Ist) **Sitzungsliste und Beenden**: Das Konto sieht unter „Meine Sitzungen“ (Profil) nur aktive Sitzungen mit Anmeldezeit, letzter Aktivität, Ablauf, IP und Browser (max. 300 Zeichen); die Verwaltung mit Recht für verwaltbare Konten ebenso (`GET /users/{id}/sessions`). Einzelne Sitzung beenden: `DELETE /sessions/{id}`; alle Sitzungen eines Kontos beenden: `DELETE /users/{id}/sessions` (beim eigenen Konto „Alle anderen Sitzungen beenden“, die aktuelle bleibt). Fremde Konten ohne Verwaltungsrecht → 404. Es gibt keine Obergrenze für gleichzeitige Sitzungen je Konto (mehrere Geräte).
  Abnahme: Liste zeigt die sechs Felder; „Alle anderen beenden“ lässt die aktuelle bestehen und beendet die zweite (401); Sekretariat sieht Sitzungen eines Schülerkontos, nicht die eines Lehrers (404).

- **ANM-077** (P0, Status: Ist) **Sitzungen enden automatisch** bei: Passwort gesetzt, geändert oder zurückgesetzt (bei eigenem Passwortwechsel außer der aktuellen), Passwort-Zurücksetzen per Code, Startpasswort-Erzeugung, Konto deaktiviert oder gelöscht. Reaktivieren beendet nichts.
  Abnahme: Je Auslöser: zweite Sitzung des Kontos → 401; Reaktivieren → keine Änderung bestehender Sitzungen (es gibt keine).

- **ANM-078** (P0, Status: Ist) **Cookie-Regeln**: Die Cookies der Tabelle werden mit den genannten Attributen gesetzt; keine Passwörter oder Klartext-Adressen in Cookies; Anbieter-Status wird nach einmaliger Verwendung gelöscht; `Secure` bei HTTPS automatisch; in Produktion ist `SM_COOKIE_SECURE=1` Pflicht (`SM_COOKIE_SECURE=0` ist dort ein Startfehler).
  Abnahme: Antwort der Anmeldung über https enthält `sm_session` mit HttpOnly, SameSite=Lax, Secure, Path=/, Max-Age 2 592 000; kein Cookie enthält Passwort oder E-Mail im Klartext; JavaScript kann `sm_session` nicht lesen.

- **ANM-079** (P0, Status: Ist) **Abmelden**: Es gibt einen Knopf „Abmelden“ unten in der Seitenleiste (fest, nicht scrollbar), im Handy-Menü und im Benutzermenü; vor dem Abmelden fragt ein App-Dialog „Möchten Sie sich wirklich abmelden?“ [Sie-Form abgeleitet aus „Willst du dich wirklich abmelden?“] mit Ja/Nein. Abmelden beendet die Sitzung serverseitig (der alte Cookie wirkt danach nicht mehr), löscht `sm_session`, `sm_sso_hint` und `sm_sso_who`, leert alle kontobezogenen Zwischenspeicher der Oberfläche (sonst sähe das nächste Konto im selben Tab fremde Daten) und zeigt „Sie sind abgemeldet.“ mit den noch angemeldeten weiteren Konten (siehe B8). Nach dem Abmelden zeigt auch der Zurück-Knopf des Browsers keine Kontodaten. Das Profil bietet „Sitzung beenden“ und „Alle anderen Sitzungen beenden“. Protokoll `auth.logout`.
  Abnahme: Abmelden → alter Cookie (nachgesendet) → 401; Browser „Zurück“ zeigt Anmeldung/Abgemeldet-Seite ohne Namen oder Plandaten; zweites Konto im selben Tab sieht keine Daten des ersten (Zwischenspeicher leer); Dialog per Tastatur bedienbar.

- **ANM-080** (P1, Status: offen) Beim Abmelden werden auch lokale Schlüssel im Browser (z. B. Chat-Schlüssel) entfernt (Altbestand: bleiben nach der Abmeldung im Browser).
  Abnahme: Nach Abmelden enthalten Browser-Speicher (localStorage/IndexedDB) keine Chat-Schlüssel des Kontos mehr; erneute Anmeldung erfordert wieder die Geräte-Freigabe nach den Regeln des Bereichs Nachrichten.

- **ANM-081** (P1, Status: offen) **Adresse**: Sitzungen und Cookies gelten je Adresse (Ursprung: Host und Port) und je Browser; das gleiche System unter einer zweiten Adresse (z. B. Heimnetz-Adresse mit anderem Port neben der Domain) hat getrennte Anmeldungen. Es gibt genau **eine** Adresse für Nutzer (`SM_BASE_URL`); Zugriffe über andere Adressen werden automatisch dorthin umgeleitet. [unklar: Betreiber hat die Frage „Heimnetz-Adresse automatisch auf die Domain umleiten?“ und „HTTP-Zugang im Heimnetz abschalten?“ (derzeit `SM_COOKIE_SECURE=0` auf der Hauptinstanz) nicht beantwortet.]
  Abnahme: Aufruf über eine Nebenadresse → Umleitung auf `SM_BASE_URL`; Anmeldung unter der Hauptadresse bleibt nach dem Aufruf der Nebenadresse bestehen (keine „verschwundenen“ Konten); Anfrage über http in Produktion → Umleitung auf die https-Hauptadresse.

- **ANM-082** (P0, Status: offen) **Widerruf aller Zugangs-Token**: Persönliche API-Token (Abschnitt B12) und Geräte-Token enden bei Passwortwechsel, Passwort-Zurücksetzen, Kontosperre, Zwei-Faktor-Zurücksetzen, „Sitzungen beenden“, Herabstufung, Austritt und Volljährigkeit (Altbestand: API-Token überleben Passwortwechsel, Sperre und 2FA-Reset; live bestätigt).
  Abnahme: API-Token des Kontos ist gültig; nach Passwortwechsel (bzw. je Auslöser) → `Authorization: Bearer` liefert 401 `invalid_token`.

- **ANM-083** (P2, Status: offen) **„Angemeldet bleiben“ und Geräte-Token**: „Angemeldet bleiben“ bindet das Gerät an einen Passkey oder ein nur gehasht gespeichertes Geräte-Token (HttpOnly, Secure, SameSite=Strict); unter „Meine Geräte“ lesbar (Gerätebezeichnung statt roher Browser-Kennung) und widerrufbar; kein Fingerprinting; Datenbankinhalte allein ermöglichen keine Anmeldung. Monitor-Geräte nutzen ein widerrufbares Geräte-Token statt der Abmeldung nach 30 Tagen. Audit für Widerruf und Kontowechsel.
  Abnahme: Gerät A „angemeldet bleiben“ → nach Browser-Neustart angemeldet; „Gerät widerrufen“ → nächste Anfrage 401; Datenbank enthält nur Hash des Token; Monitor-Gerät bleibt über 31 Tage angemeldet, bis es widerrufen wird.

## B8 Mehrere Konten im selben Browser (Kontowechsel)

- **ANM-084** (P1, Status: Ist) **Kontowechsel**: Wunsch-Wortlaut 12.10.: „Und kannst du bitte das mit dem Account Switchen machen?“ Je Browser sind bis zu **5** Konten gleichzeitig angemeldet (1 aktives + höchstens 4 weitere; Cookie `sm_sessions`). „Weiteres Konto anmelden“ (Anmeldung mit `add=true`) fügt ein Konto hinzu; das bisherige bleibt angemeldet, die Übernahme erfolgt erst nach vollständig erfolgreicher Anmeldung (bei Code-Pflicht ändert sich bis zum zweiten Schritt nichts). Wechseln geschieht ohne Passwort, nur mit gültiger weiterer Sitzung, setzt ein neues Sitzungs-Cookie und wird protokolliert (`auth.switch_account`). Die Kontoliste nennt aktives Konto zuerst, höchstens 5, mit Name und Rolle; ungültige weitere Sitzungen werden beim Auflisten entfernt, doppelte Konten nur einmal gespeichert. Ansichtskonten (Zuschauer) dürfen wechseln. Zwei-Faktor funktioniert auch im Kontowechsel.
  Abnahme: Sechstes Konto hinzufügen → abgelehnt (Meldung); Konto B hinzufügen, zu B wechseln → Anfragen laufen mit Rechten von B; Konto A bleibt bestehen; bei 2FA-Konto zwischen Schritt 1 und 2 bleiben die bestehenden Sitzungen unverändert; abgelaufene weitere Sitzung wird in der Liste nicht mehr angeboten; Zuschauer wechselt erfolgreich, ein Schreibzugriff bleibt 403.

- **ANM-085** (P0, Status: Ist) **Keine Vermischung, nur im eigenen Browser**: Konten bleiben nur im eigenen Browser; ein Fremder, der dieselbe Adresse öffnet, ist nie automatisch angemeldet (Betreiber 12.10.: „Du musst wirklich sicher sein … Kannst du doch nochmal bitte explizit drüber gehen.“). Jedes Konto hat eigene Rechte; jeder Aufruf läuft nur mit dem aktiven Konto; Wechseln, Abmelden und Hinzufügen verlangen den CSRF-Schutzwert; die Zwischenspeicher der Oberfläche werden bei Wechsel, Abmelden und 401 zentral zurückgesetzt (jeder Zwischenspeicher je Konto meldet sich zur Rücksetzung an). Eltern- und Lehrerkonto parallel zeigen nie Daten des anderen.
  Abnahme: Browser A mit zwei Konten; Browser B (ohne Cookie) ruft Kontoliste → leer/401; im Test mit Eltern- und Lehrerkonto parallel: nach Wechsel zeigt die Oberfläche keinen Datensatz des vorigen Kontos (Plan, Kinderliste, Toasts); Wechsel ohne CSRF-Wert → 403.

- **ANM-086** (P1, Status: Ist) **Abmelden mit mehreren Konten**: „Abmelden“ beendet nur das aktive Konto, die anderen bleiben angemeldet (inaktiv). Danach zeigt die Seite „Sie sind abgemeldet.“ die noch gültigen Konten mit „Weiter als …“, einem × zum Abmelden je Konto (auch ohne aktive Sitzung, Protokoll `auth.logout`) und „Mit anderem Konto anmelden“; ohne weitere Konten direkt die Anmeldung; es gibt keinen automatischen Sprung in ein anderes Konto. „Weiteres Konto anmelden“ öffnet ein Anmeldefenster (App-Dialog) über der aktuellen Seite mit „Abbrechen“; es gibt keinen Sprung zur Startseite.
  Abnahme: Zwei Konten angemeldet, Abmelden → Seite listet das zweite Konto, kein Datenabruf des ersten möglich; × beim zweiten → Anmeldeseite; „Weiteres Konto anmelden“ + Abbrechen → aktuelle Seite unverändert.

- **ANM-087** (P2, Status: Ist) **Oberfläche Kontowechsel**: Benutzermenü „Kontowechsel“ (alle in diesem Browser angemeldeten Konten, Wechsel mit einem Klick), „Weiteres Konto anmelden“ und „Abmelden“; im Monitor-Menü zusätzlich „Standort wechseln“. Texte in Sie-Form. [unklar: Bedienung auf Tablet und Handy im Altbestand angekündigt, Ergebnis nicht berichtet; Anforderung: 390 px ohne waagerechten Bildlauf, Zielgrößen ≥ 44 px.]
  Abnahme: Auf 390 px und 1280 px Wechsel zwischen zwei Konten per Mausklick, Tastatur (Fokus, Enter) und Touch möglich; Monitor-Menü zeigt „Standort wechseln“.

- **ANM-088** (P3, Status: offen) **Konten über mehrere Schulen** (Eltern mit Kindern an zwei Schulen): gemeinsamer Anmeldepunkt über mehrere Schul-Instanzen hinweg, empfohlen bei der zweiten Schule (zentraler Anmeldepunkt für viele Schul-Subdomains, siehe ANM-062). Bis dahin ist je Schule eine Instanz mit eigenen Konten die Regel.
  Abnahme: Zweite Schule angebunden: Eltern wechseln mit einem Klick zwischen den Schulen, ohne Passwort-Wiederholung, Sitzungen bleiben je Schule getrennt.

## B9 Konten (Anlegen, Sperren, Löschen)

- **ANM-089** (P1, Status: Ist) **Eine Rolle je Konto**: Eine Person mit mehreren Funktionen (z. B. Lehrkraft und Elternteil) hat mehrere Konten und wechselt über den Kontowechsel (B8); es gibt keine Zusammenführung zu einem Konto mit mehreren Grundrollen (REC-005). [unklar: Zusammenführen vorhandener Konten ist im Altbestand nicht beschrieben.]
  Abnahme: Lehrkraft und Elternteil derselben Person: zwei Konten, im Wechsler beide sichtbar, Daten getrennt; ein Konto mit zwei Grundrollen ist nicht anlegbar.

- **ANM-090** (P0, Status: Ist) **Benutzername**: nur Kleinbuchstaben a–z, Ziffern 0–9 sowie `.`, `_`, `-`; Umlaute werden umgeschrieben (ä→ae, ö→oe, ü→ue, ß→ss); Großbuchstaben werden klein; höchstens 80 Zeichen (Überlänge wird ohne Fehler gekürzt); leer nach Bereinigung → 422; vorhanden (ohne Beachtung der Groß-/Kleinschreibung) → 409. Das Anmeldefeld akzeptiert bis 200 Zeichen und kürzt auf 80. Auf dem Handy wird aus Benutzernamen gern Großschreibung; deshalb wird klein geschrieben.
  Abnahme: „Müller.Anna“ → `mueller.anna`; Name mit 100 Zeichen → gespeichert mit 80; „@@@“ → 422; „ADMIN“ bei vorhandenem `admin` → 409; Anmeldung mit „Mueller.ANNA“ gelingt.

- **ANM-091** (P1, Status: Ist) **Konto anlegen** (`users.manage`, Rolle verwaltbar nach REC-032): Anlage mit eingebauter Grundrolle, eine eigene Rolle wird danach zugewiesen [unklar: ob die Anlage-Route eine eigene Rolle direkt annimmt]. Standard: Konto aktiv, Zwei-Faktor aus, volljährig „nein“, Anzeigename = Benutzername, Startpasswort erzeugt (einmalig angezeigt), Pflicht-Wechsel „ja“. Zuordnungsdaten (Lehrkraft-Kürzel, Schüler-ID, Klasse, Kinder, Zweige) werden nach REC-018 geprüft (422). Protokoll `user.create` (mit `role_id`).
  Abnahme: Anlage ohne Angaben → Konto mit den genannten Standards; Anlage mit unbekanntem Kürzel → 422; Anlage einer nicht verwaltbaren Rolle → 403; Startpasswort steht im Antwortfeld nur dieses eine Mal.

- **ANM-092** (P1, Status: Ist) **Massenanlage** (`POST /users/bulk`) nur für die Rollen `schueler`, `lehrer`, `eltern` (sonst 422), optional mit Klassen. Schüler/in: Benutzername `vorname.nachname` in ASCII, bei Dubletten Zähler 2, 3, …; nur Schüler ohne Konto; Anzeigename aus den Schuldaten. Eltern: `eltern.vorname.nachname` je Schüler/in ohne Elternkonto, Anzeigename „Eltern von <Name>“. Lehrkraft: Kürzel klein; nur Lehrkräfte, die in den gewählten Klassen unterrichten oder dort Klassenleitung sind; nur ohne vorhandenes Konto. Die Antwort enthält je Konto Benutzername, Anzeigename, Startpasswort und Klasse (Grundlage der Zugangsbriefe); bei volljährigen Schüler/innen entsteht kein automatisches Elternkonto.
  Abnahme: Klasse mit 3 Schüler/innen, davon zwei gleichen Namens → Benutzernamen `max.mustermann` und `max.mustermann2`; zweiter Lauf legt keine neuen Konten an; Rolle `sekretariat` bei Massenanlage → 422; volljährige Schülerin → kein Elternkonto.

- **ANM-093** (P1, Status: Ist) **Eltern-Konten und Kinder-Verknüpfung**: Ein Elternkonto gilt für alle Kinder (Geschwister); Verknüpfung als n:m (`parent_links`, je Paar einmal): Liste der Kinder abrufen, setzen (ganze Liste), einzeln hinzufügen und entfernen (`users.manage`; Abrufen: Umfang geprüft). Beim Löschen eines Elternkontos werden Verknüpfungen entfernt.
  Abnahme: Zwei Kinder → ein Elternkonto mit beiden; ein Kind entfernen → Eltern sehen nur das andere (Fremdes → 404); doppelte Verknüpfung wird dedupliziert.

- **ANM-094** (P0, Status: Ist) **Deaktivieren und Reaktivieren**: Deaktivieren beendet alle Sitzungen des Kontos; API-Token wirken nicht mehr (401); Anmeldung nach richtigem Passwort → 403 `account_disabled`. Reaktivieren beendet nichts. Ausnahmen: eigenes Konto 409, letzter aktiver Administrator 409 (REC-029), Inhaber-Konto 403 (REC-026).
  Abnahme: Deaktiviertes Konto mit offener Sitzung → nächste Anfrage 401; Anmeldung → 403 `account_disabled`; Reaktivieren → Anmeldung gelingt.

- **ANM-095** (P0, Status: Ist) **Löschen eines Kontos** (Datenschutz): endgültig. Entfernt werden Sitzungen, API-Zugänge (Token), Eltern-Kind-Verknüpfungen und die Anmelde-Fehlversuche des Benutzernamens. In Protokollen wird die Benutzer-ID geleert und der Benutzername auf `gelöscht#<ID>` gesetzt; bei Versionen, Mitteilungen, Krankmeldungen und Abwesenheitsereignissen wird die Verfasser-ID geleert und der Akteur-Name `gelöscht#<ID>`. Protokoll `user.delete`. Ausnahmen: eigenes Konto 409, letzter Administrator 409, Inhaber 403.
  Abnahme: Konto löschen → Sitzung 401, Token 401, Eltern-Kind-Zeilen weg, keine Fehlversuche mit dem Namen; Audit-Zeilen zeigen `gelöscht#<ID>` statt des Namens; Krankmeldung dieses Verfassers zeigt keine Verfasser-ID.

- **ANM-096** (P0, Status: offen) **Vollständige Pseudonymisierung beim Löschen**: Auch Namen in Ankündigungen (`author_name`), Abwesenheiten, Dokumenten und Kursraum-Beiträgen werden beim Löschen pseudonymisiert; der Benutzername bleibt im Audit nicht im Klartext stehen (Altbestand: unvollständig; Audit-Befund 17.10.).
  Abnahme: Konto mit Ankündigung, Dokument, Kursraum-Beitrag und Abwesenheit löschen → Volltextsuche in allen Tabellen nach Benutzername und Anzeigename ergibt keinen Treffer.

- **ANM-097** (P0, Status: offen) **Verknüpfung passend zur Rolle; verwaiste Konten**: `teacher_id` und `student_id` werden nur passend zur Rolle gesetzt (Lehrkraft-Verknüpfung nur bei Grundtyp Lehrkraft, Schüler-Verknüpfung nur bei Schüler/in). Wird eine Schülerin, ein Schüler oder eine Lehrkraft aus den Stammdaten gelöscht, kann sich das verknüpfte Konto nicht mehr anmelden (laufende Sitzungen enden); die Benutzerverwaltung zeigt es als „ohne Datensatz“ mit „deaktivieren“ bzw. „löschen“; Eltern sehen kein Kind mehr ohne Klasse.
  Abnahme: Konto der Rolle `eltern` mit `teacher_id` setzen → 422; Stammdatensatz löschen → Konto-Anmeldung 403 bzw. Sitzung 401, Anzeige „ohne Datensatz“.

- **ANM-098** (P1, Status: Ist) **Demo-Konten**: Eigenes Passwort und 2FA von Demo-Konten sind nicht änderbar; andere Konten dürfen Demo-Konten nicht ändern (403). Demo-Konten mit dem Demo-Passwort sind in Produktion gesperrt (beim Start gesperrt und im Systembereich gemeldet); `SM_LOAD_DEMO=1` und `SM_DEMO_PUBLIC=1` sind in Produktion Fehler. Demo-Schutz als Allowlist: jede schreibende Route ist gesperrt, außer sie ist ausdrücklich freigegeben. Das Demo-Passwort setzt `SM_DEMO_PASSWORD`; im Demo-Modus entsteht beim allerersten Start ein Einmalpasswort für den Erst-Admin.
  Abnahme: Demo-Konto ändert Passwort → 403; Produktion mit Demo-Konto-Datenbestand → Konten nach dem Start gesperrt; neue schreibende Route in der Demo ohne Freigabe → gesperrt.

- **ANM-099** (P2, Status: Ist) **Kontenverwaltung**: Liste (`GET /users`, `users.manage`, zusätzlich `watch.read` für das Beobachtungs-Kennzeichen), Konto-Dialog mit Reitern „Kontakt“, „Verbundene Konten“, „Beobachtung“ (nur mit `watch.read`), „Zugangsbriefe“; Sitzungen anderer Konten einsehen und beenden; API-Token je Konto; Klassen-Seite „Konten einer Klasse“ mit Zugang zu den Zugangsbriefen; Rollenauswahl ohne ausgeblendete Rollen.
  Abnahme: Sekretariat sieht Reiter ohne „Beobachtung“; Schulleitung mit `watch.read` (zugewiesen) sieht ihn; Dialog zeigt nur die nach REC-032 verwaltbaren Konten.

## B10 Passwort vergessen, Kontakte und Bestätigungscodes

**Werte für Codes, Links und Token**

| Merkmal | Wert |
|---|---|
| Bestätigungs- und Reset-Code | 6 Ziffern (zufällig, mit führenden Nullen) |
| Speicherung | HMAC aus Zweck, Konto und Code; kein Klartext |
| Gültigkeit | `SM_AUTH_CODE_MINUTES` Minuten (Standard 15; erlaubt 1 bis 1440, sonst Startabbruch) für Code, Link und Reset-Token |
| Versuche je Code | 5 Fehlversuche, danach ist der Code verbraucht |
| Mehrere Codes gleichen Zwecks | ein neuer Code entwertet offene ältere (nur ein offener Code je Zweck) |
| Fehlversuch bei mehreren offenen Reset-Codes | zählt auf alle offenen Reset-Codes des Kontos (gemeinsame Versuchszahl) |
| Einmalig | ja, atomar (bei parallelen Anfragen nur ein Gewinner) |
| Link (E-Mail) | 32 Zufalls-Bytes; gleiche Gültigkeit; einmal verwendbar |
| Reset-Token nach Prüfung | 32 Zufalls-Bytes; Gültigkeit `SM_AUTH_CODE_MINUTES`; einmal; Mindestlänge in der Anfrage 10 Zeichen |
| Zieladresse | verschlüsselt gespeichert |
| Bereinigung | Codes 1 Stunde nach Ablauf gelöscht; Zeilen der Mengenbegrenzung 1 Stunde nach ihrem Ablauf (Ablauf = 1 Stunde nach der Anfrage) |

**Limits**

| Limit | Wert | Wirkt auf | Verhalten bei Überschreitung |
|---|---|---|---|
| Bestätigungscodes je Konto und Art (E-Mail oder Handy) | 5 je Stunde | Konto | 429 „Zu viele Anfragen“, `Retry-After` 3600 s |
| Bestätigungscodes je IP | 20 je Stunde | IP | 429 |
| Reset-Anfragen je Kennung (Benutzername, E-Mail, Handynummer; auch unbekannte) | 5 je Stunde | Kennung | 429 |
| Reset-Anfragen je IP | 20 je Stunde | IP | 429 |
| Reset-Codes je Konto (alle Kennungen) | 5 je Stunde | Konto | still verworfen, gleiche Antwort |
| Reset-Fehlversuche je IP | 30 je Stunde | IP | 429 |
| Admin: Link oder Code senden | 10 je Stunde | Zielkonto | 429 |
| Konten je Kennung (z. B. Eltern mit gleicher Adresse) | höchstens 5 | Kennung | weitere werden nicht berücksichtigt |
| Mindestlaufzeit Reset-Anfrage | 0,35 s plus Zufall 0 bis 39 ms | – | gleiche Laufzeit für bekannte und unbekannte Kennungen |

Der Admin-Versand zählt auf das Konto-Limit der Reset-Codes gleicher Art. Feste Texte: Antwort der Anfrage immer „Falls ein Konto dazu passt, ist ein Code unterwegs.“; falscher Code „Der Code ist falsch oder abgelaufen.“ (400); ungültiger Link „Der Link ist ungültig oder abgelaufen.“ (400); Restversuche „Noch N Versuch(e).“; Frist „Die Zeit zum Zurücksetzen ist abgelaufen.“ (400).

- **ANM-100** (P0, Status: Ist) **Passwort vergessen (öffentlich, ohne Anmeldung)** – Ablauf: (1) Kennung eingeben (Benutzername, E-Mail-Adresse oder Handynummer; die Art wird erkannt); (2) Kanal: `auto` = E-Mail-Kennung → E-Mail, Handynummer → SMS, Benutzername → E-Mail, sonst SMS; (3) Antwort stets gleich und neutral (Text oben) mit Mindestlaufzeit 0,35 s + Zufall 0–39 ms; (4) nur wenn ein Konto passt, aktiv ist, der Anmeldeweg „Passwort“ erlaubt ist, der Kanal laut Richtlinie erlaubt und der Kontakt **bestätigt** ist, wird ein Code (E-Mail zusätzlich mit Link) gesendet; andernfalls gleiche Antwort ohne Versand; (5) Code oder Link-Token prüfen (`POST /auth/password-reset/request`, `/verify`, `/confirm`) → Reset-Token; (6) neues Passwort nach ANM-009/010 (und Leak-Prüfung, falls an), sonst 422 mit Meldungen; (7) Erfolg: Passwort gesetzt, Pflichtwechsel aus, Startpasswort-Marke entfernt, alle Sitzungen beendet, offene Codes verbraucht, Erfolgseintrag hebt Paar- und Kontozähler auf, 2FA bleibt aktiv, Weiterleitung zur Anmeldeseite mit Hinweis „Passwort geändert“ (`/login?reset=ok`), Protokoll `auth.password_reset`. Der Link der E-Mail führt auf `/passwort-zuruecksetzen?token=…`. Oberfläche (Wunsch 12.10.: „Kannst du da bitte weniger Text reinhauen … Das ist viel zu viel.“): ein Feld, ein Knopf, dann Code, dann neues Passwort; Erklärungen hinter „?“. Passwort-Zurücksetzen und SSO sind nicht gedrosselt (Limits siehe Tabelle).
  Abnahme: Bekanntes und unbekanntes Konto → identische Antwort und Antwortzeit ≥ 0,35 s; Code mit Zustellung per Test-Postausgang → neues Passwort gesetzt, alle anderen Sitzungen weg, 2FA-Konto verlangt weiter den Code; zweite Verwendung desselben Link-Tokens → 400; deaktiviertes Konto, nicht bestätigter Kontakt, unerlaubter Kanal oder unerlaubter Anmeldeweg → neutrale Antwort, kein Versand.

- **ANM-101** (P0, Status: Ist) Code-, Link- und Token-Werte nach Tabelle: 6-stelliger Code, 5 Versuche je Code (danach verbraucht), Gültigkeit 15 Minuten (`SM_AUTH_CODE_MINUTES`), neuer Code entwertet ältere, gemeinsamer Versuchszähler aller offenen Reset-Codes, atomares Einlösen (Reset-Token verbraucht sich bei parallelen Anfragen nur einmal), Speicherung nur als HMAC.
  Abnahme: 5 falsche Codes → 6. (auch richtiger) Versuch „Der Code ist falsch oder abgelaufen.“; zwei parallele `confirm`-Aufrufe mit demselben Token → genau einer gelingt; Code nach 16 Minuten → abgelehnt; neuer Code macht den alten ungültig; Datenbank enthält keine Klartext-Codes.

- **ANM-102** (P0, Status: Ist) Limits nach Tabelle (5/Stunde je Konto und Art, 20/Stunde je IP, 5/Stunde je Kennung, 5/Stunde je Konto für Reset-Codes still verworfen, 30 Fehlversuche/Stunde je IP, Admin 10/Stunde, höchstens 5 Konten je Kennung). Überschreitung liefert 429 mit `Retry-After` (3600 s bei Stundenlimits), außer „still verworfen“.
  Abnahme: 6. Reset-Anfrage für dieselbe Kennung binnen einer Stunde → 429; 21. Anfrage von derselben IP → 429; 6. Reset-Code für dasselbe Konto über verschiedene Kennungen → gleiche Antwort ohne Versand; 31. Fehlversuch derselben IP → 429; 11. Admin-Versand → 429.

- **ANM-103** (P1, Status: Ist) **Verfügbarkeit nur bei möglichem Versand**: „Passwort vergessen“, Kanal-Optionen und Admin-Knöpfe („Link per E-Mail“, „Code per SMS senden“) erscheinen nur, wenn der Versand wirklich möglich ist (E-Mail: SMTP und Zustellung eingerichtet oder Test-Postausgang; SMS: Anbieter eingerichtet oder Test-Postausgang). Sonst steht auf der Anmeldeseite „Bitte wenden Sie sich an das Sekretariat.“; Rücksetz-Codes werden nie auf einer öffentlichen Seite angezeigt. Administratoren sehen unter „Anmelde-Richtlinien“, was fehlt. Betreiber-Wunsch 12.10.: „das mit der SMS soll nur angezeigt werden, wenn die Server das überhaupt machen.“ Schulseitig kann eingestellt werden, dass nur Lehrkräfte Passwörter zurücksetzen dürfen („Passwort vergessen per“, ANM-066).
  Abnahme: Instanz ohne `SM_SMTP_HOST`/`SM_SMTP_FROM` und ohne SMS-Anbieter: Anmeldeseite ohne Link, mit Hinweis; mit nur E-Mail: nur Kanal E-Mail; `SM_NOTIFY_DISPATCHER=0` → E-Mail gilt als nicht verfügbar.

- **ANM-104** (P1, Status: Ist) **Eigene Kontakte** (Profil › „E-Mail & Handynummer“): E-Mail ändern → Code an die **neue** Adresse (6 Ziffern, 15 Minuten) und Bestätigungslink (Anmeldung nötig); die Adresse gilt erst nach Bestätigung; die alte bestätigte Adresse erhält einen Hinweis. E-Mail: eine Adresse, höchstens 254 Zeichen, keine Kopfzeilen-Trennzeichen (sonst 422). Handynummer: Code per SMS (6 Ziffern, 15 Minuten), Eingabe mit Vorwahl (`0171 …` oder `+49 …`) [unklar: Formatdetails]. Das aktuelle Passwort wird verlangt, falls gesetzt (Sperre ANM-029). Kontakt entfernen: `POST /me/contact/{kind}/remove` (Passwort nötig, offene Codes werden entwertet). Bestätigte Kontakte zeigen „bestätigt“. Anzeige maskiert (E-Mail: erster Buchstabe, dann •••, dann Domain; Handynummer: nur letzte Ziffern); die Telefonnummer ist zusätzlich als Hash für die Suche gespeichert, Zieladressen verschlüsselt.
  Abnahme: Neue Adresse erst nach Code gültig, bis dahin gilt die alte; Hinweis geht an die alte; 255-Zeichen-Adresse → 422; Anzeige `m•••@domain.de`; Entfernen eines Kontakts ohne aktuelles Passwort (obwohl gesetzt) → abgelehnt, mit Passwort → Kontakt weg und offene Codes ungültig.

- **ANM-105** (P1, Status: Ist) **Kontakt durch die Verwaltung**: `users.manage` (Sekretariat nur für Schüler/innen und Eltern) setzt E-Mail/Handynummer eines Kontos und markiert sie ohne Code als bestätigt (`GET`/`PUT /users/{id}/contact`); `POST /users/{id}/send-reset` sendet Link oder Code an den bestätigten Kontakt, wenn Konto aktiv, Passwort-Anmeldung erlaubt, Kontakt bestätigt und Versand eingerichtet ist (sonst 409 mit Grund); 10 je Stunde und Zielkonto; Inhaber-Konto geschützt (REC-027).
  Abnahme: Sekretariat setzt Kontakt eines Lehrers → 404; `send-reset` ohne Versand → 409 mit Grund; mit Versand → Nachricht im Test-Postausgang, Konto-Limit +1.

- **ANM-106** (P1, Status: Ist) **Konto-Nachrichten** (Postausgang für Codes, Links, Briefe): Zustellung im Hintergrund über die Warteschlange; Empfänger, Text und Anhänge verschlüsselt; Klartext wird nach Zustellung oder endgültigem Fehlschlag gelöscht; Anzeige in Protokollen maskiert; Empfängeradresse höchstens 254 Zeichen, Betreff höchstens 300, Anhänge je E-Mail höchstens 20 MB (Summe, sonst Versand verweigert). Zwecke: `password_reset`, `verify_email`, `verify_phone`, `contact_notice`, `letter`, `auth`. Ausgehende Verbindungen (SMTP, SMS-Webhook, Dienste) gehen nur an geprüfte öffentliche Ziele (Ausnahmen `SM_OUTBOUND_ALLOW`).
  Abnahme: Nach Zustellung enthält die Zeile keinen Klartext; Anhänge 21 MB → Versand verweigert; Protokolle zeigen nur maskierte Adressen; SMTP-Ziel im privaten Netz → abgelehnt.

- **ANM-107** (P1, Status: Ist) **Versandwege und Konfiguration**: E-Mail über SMTP (`SM_SMTP_HOST`, `SM_SMTP_PORT` 587, `SM_SMTP_USER`, `SM_SMTP_PASSWORD`, `SM_SMTP_FROM`, `SM_SMTP_TLS` = `starttls` | `ssl` | `none`); SMS über `SM_SMS_PROVIDER` (leer, `log`, `webhook`, `twilio`, `seven`; Anbieter-Pflichtfelder siehe ANM-020) mit `SM_SMS_URL`, `SM_SMS_TOKEN`, `SM_SMS_ACCOUNT_SID`, `SM_SMS_FROM`, `SM_SMS_TIMEOUT` (Standard 10 s); Zustellung durch `SM_NOTIFY_DISPATCHER` (Standard 1). E-Mail-Versand nur mit Host und Absender.
  Abnahme: SMS-Webhook-Attrappe empfängt Empfänger und Text per POST; `twilio` ohne SID → Startabbruch; Standard `SM_SMS_TIMEOUT` 10.

- **ANM-108** (P0, Status: offen) **Test-Postausgang nur Entwicklung und gehärtet**: Der Test-Postausgang (Mails/SMS werden nur angezeigt, nie zugestellt; letzte 50 Nachrichten; Aufbewahrung 24 Stunden; Anhänge-Download mit Sicherheitsheadern `nosniff`, Sandbox, `no-store`) ist nur in der Entwicklung verfügbar (`SM_DEV_OUTBOX`, Standard 1 nur wenn nicht Produktion und `SM_BASE_URL` lokal; in Produktion Startabbruch), liefert in Produktion 403/404 und ist im Neubau zusätzlich **nur für angemeldete Administratoren** oder nur für eigene Nachrichten sichtbar (Altbestand: ohne Anmeldung nutzbar; „Passwort vergessen“ ohne Anmeldung in der Vorschau).
  Abnahme: Entwicklung ohne Anmeldung `GET /dev-outbox` → 401/403; als Admin → letzte 50 Nachrichten; Produktion → 404/403; Zeilen älter als 24 Stunden werden von der Wartung gelöscht.

- **ANM-109** (P2, Status: offen) **Versand in der Oberfläche einrichten** (Betreiber-Wunsch A-18): Server (SMTP) und SMS-Anbieter lassen sich unter Einstellungen › Schnittstellen eintragen (nicht nur per Umgebungsvariable); Passwörter/Tokens verschlüsselt und nie wieder angezeigt; Testversand mit verständlicher Fehlermeldung; Werte aus der Umgebung haben Vorrang und sind als „vom Server vorgegeben“ gekennzeichnet.
  Abnahme: SMTP-Daten in der Oberfläche eintragen → Testversand erfolgreich; falsche Daten → deutsche Fehlermeldung ohne Details; gespeichertes Passwort wird nie angezeigt; Umgebungswert überschreibt Oberfläche.

## B11 Zugangsbriefe (Startpasswörter als Brief)

Hinweis: Layout, Formularbezug und Druckdetails der Briefe stehen im Bereich Formulare/Briefe; hier stehen Berechtigung, Lebensdauer, Grenzen und Schutz.

- **ANM-110** (P0, Status: Ist) **Stapel**: Ein Stapel sammelt Startpasswörter ausgewählter Konten (`POST /letters/batches`). Für jeden Eintrag wird ein **neues** Startpasswort erzeugt (Pflichtwechsel, alle Sitzungen des Kontos beendet, offene Reset-Codes entwertet) und verschlüsselt im Stapel gespeichert; das Konto selbst speichert nur Hash und Frist. Lebensdauer 60 Minuten (`SM_LETTER_BATCH_MINUTES`, Bereich 1 bis 1440); nach Ablauf wird der Stapel gelöscht (Wartung oder nächster Zugriff), ein Zugriff liefert 410 mit Hinweis. Sichtbar nur für den Ersteller oder die Administration (sonst 404); ein Eintrag ist nur für Konten sichtbar, die der Betrachter zurücksetzen darf (Klassenleitung: nur Schüler/innen eigener Klassen). Grenzen: höchstens 5000 Einträge je Stapel (Speicherung), 500 Konten je Stapel-Anlage über die Route, 2000 Briefe je direkter PDF-Erzeugung ohne Speicherung (`POST /users/letters.pdf`), 5000 Konten in einer Auswahl. Antworten werden nicht zwischengespeichert (`no-store`).
  Abnahme: Stapel mit 3 Konten → 3 neue Startpasswörter (alte Passwörter ungültig, Sitzungen weg); Zugriff nach 61 Minuten → 410; fremder Nutzer → 404; Klassenleitung 5a: Eintrag einer Schülerin aus 5b nicht sichtbar; 501 Konten → 422; Antwortkopf `Cache-Control: no-store`.

- **ANM-111** (P0, Status: Ist) **Rechte und Protokoll**: Stapel anlegen mit `users.manage`; Ansehen, Herunterladen (Sammel-PDF, ZIP, Einzel-PDF) und Versenden mit `users.manage` oder `passwords.reset`; die Zielmenge folgt REC-033; Klassen-Seite „Konten einer Klasse“ bietet den Zugang. Jeder Download und Versand wird protokolliert (`letters.download`, `letters.send`) ohne Passwort. Der Inhaber-Schutz gilt auch hier (REC-027).
  Abnahme: Lehrkraft ohne Klassenleitung ruft einen Stapel ab → 404/403; Download erzeugt Audit-Zeile `letters.download` ohne Passwort; Versand `letters.send`.

- **ANM-112** (P0, Status: Ist) **Startpasswörter erscheinen nie auf dem Bildschirm**, nie in der Adresse und nie im lokalen Speicher: Die Stapel-Seite (`/zugangsdaten/{id}`) zeigt einen Ablauf-Countdown und die Einträge, aber keine Passwörter; sie sind nur im PDF enthalten (und beim E-Mail-Versand nur als PDF-Anhang). Die Oberfläche übergibt den Stapel nur über den Router-Zustand. Beim einzelnen Zurücksetzen erscheint das Einmalpasswort genau einmal (Antwort auf die Anforderung), danach nur noch „Brief als PDF“. Passwörter erscheinen auch nicht in Screenshots, Berichten oder Protokollen.
  Abnahme: Stapel-Seite enthält im DOM und in den Antworten keine Passwörter; Adresse und `localStorage`/`sessionStorage` enthalten nach dem Öffnen keine Stapeldaten; Einzel-Reset: zweiter Abruf zeigt das Passwort nicht mehr.

- **ANM-113** (P1, Status: Ist) **Brief**: Eine Seite je Brief; Inhalt: Schulname (aus Konfiguration), Datum, Titel, Zugangsdaten-Kasten (Anmelde-Adresse = `SM_BASE_URL` plus `/login`, Name, Rolle, Benutzername, Startpasswort), QR-Code zur Anmelde-Adresse, Anleitung, Hinweise; das Startpasswort wird nur gedruckt, wenn die Passwort-Anmeldung erlaubt ist oder eine Pflicht-Verknüpfung besteht (sonst Hinweis zum Anmeldeweg); bei generiertem Passwort Hinweis „nur Kleinbuchstaben, Ziffern, Bindestriche; kein 0/o, 1/l/i“; Anrede Sie-Form für alle Rollen; Titel für Eltern „Zugangsdaten für die Eltern von …“; bei Pflicht-Verknüpfung „Verbinden Sie nach dem ersten Anmelden …“; der Brief nennt die Gültigkeit des Startpassworts (ANM-016). Sortierung: Klasse (natürliche Reihenfolge), Nachname, Vorname, Schüler/innen vor Eltern, Personal zuletzt. Dateiname `Klasse_Nachname_Vorname.pdf`, Eltern mit Zusatz `_Eltern`, ASCII und eindeutig; Namenszusätze („van“, „von“) werden beim Aufteilen beachtet; ZIP = eine PDF je Person; ein Elternkonto für mehrere Kinder ist ein Konto (ein Brief je Konto).
  Abnahme: Stapel mit „Anna van der Berg“, Eltern und Lehrkraft → Reihenfolge wie beschrieben, Dateinamen ASCII ohne Kollision; Brief in Sie-Form; QR-Code führt auf `<SM_BASE_URL>/login`; Konto mit nur-Microsoft-Richtlinie → kein Passwort gedruckt, Hinweis zum Anmeldeweg.

- **ANM-114** (P1, Status: Ist) **Versand per E-Mail**: Ziel `student`, `parents` oder `both`; volljährige Schüler/innen nie über Eltern, nur selbst; eine Mail je Person und Adresse mit dem Brief als PDF-Anhang; Adressen werden dedupliziert, Konten ohne Adresse und nicht verfügbarer Versand werden gesondert zurückgemeldet; Versand nur an aktive Elternkonten mit Adresse. Der Mailtext enthält kein Passwort und weist darauf hin, dass der Brief nach dem Festlegen des eigenen Passworts zu löschen ist. Betreff an Eltern „Zugangsdaten Ihres Kindes … für …“, sonst „Ihre Zugangsdaten für …“. Vorschau und Zusammenfassung zeigen vor dem Versand, wer erreichbar ist.
  Abnahme: Zwei Geschwister, ein Elternkonto mit einer Adresse → die Adresse erhält die Mail einmal (dedupliziert), eine Mail je Person und Adresse mit PDF-Anhang; volljährige Schülerin bei Ziel `parents` → keine Mail an Eltern; Konto ohne Adresse erscheint in der Rückmeldung; Mailtext ohne Passwort.

- **ANM-115** (P0, Status: offen) Das **eigene Konto** des Erstellers wird nicht in einen Stapel aufgenommen (Altbestand: Stapel erlaubt das eigene Konto, die Sitzung endet; der Einzelweg `/users/{id}/password` verbietet es).
  Abnahme: Stapel mit dem eigenen Konto in der Auswahl → Eintrag abgelehnt (422/409); eigene Sitzung bleibt bestehen.

## B12 API-Token, Konsole, Protokoll, Betriebsfragen

- **ANM-116** (P0, Status: Ist) **Persönliche API-Token** (Details und Zugänge mit Bereichen im Bereich Integrationen): Präfix `smt_` plus 32 Zufalls-Bytes, gespeichert nur als HMAC mit `SM_SECRET_KEY`, Klartext einmalig bei der Anlage; Laufzeit 1 bis 3650 Tage; Erzeugung nur für das **eigene** Konto (fremdes Konto 403) und nur mit Sitzung oder eigenem Token; ein Token stellt nur Token mit Pflichtlaufzeit aus, höchstens mit der eigenen Restlaufzeit (Restlaufzeit unter 1 Tag → 422); Name höchstens 100 Zeichen (Standard „API-Token“); abgelaufen, widerrufen oder Konto inaktiv → 401 `invalid_token`; „letzte Nutzung“ wird höchstens alle 60 s aktualisiert; persönliche Token werden nach Ablauf sofort, Zugänge mit Bereichen 30 Tage nach Ablauf bereinigt; Änderungen am Konto (Passwort, 2FA) nur mit Sitzung; kein CSRF-Schutz nötig (Bearer).
  Abnahme: Admin stellt für ein anderes Konto ein Token aus → 403; Token mit 7 Tagen stellt Token mit 30 Tagen aus → 422; abgelaufenes Token → 401 `invalid_token`; Datenbank enthält keinen Klartext.

- **ANM-117** (P0, Status: offen) Persönliche API-Token haben eine **Pflichtlaufzeit** (nicht unbefristet), werden nur an Konten mit dem Recht `api.own` oder ausdrücklicher Freigabe ausgestellt, wirken nur auf freigegebene Bereiche (z. B. `/open/`), erlauben Schreibzugriff nur über eine Allowlist (Default-Deny) und enden bei den Auslösern aus ANM-082.
  Abnahme: Ausstellen ohne Laufzeit → 422; Konto ohne `api.own` → 403; Schreibaufruf mit Token auf nicht freigegebene Route → 403; Widerruf-Auslöser beenden das Token.

- **ANM-118** (P0, Status: Ist) **Konsole (Notweg, nur auf dem Server durch den Betreiber)**: `create-admin` (ohne Passwort: 4×4 Zeichen, Pflichtwechsel; mit Passwort: Passwortregeln geprüft, kein Pflichtwechsel); `reset-password` (ohne Passwort: 3×4 Zeichen, Pflichtwechsel, Sitzungen beendet; Ausgabe auf der Konsole); `disable-2fa`; `unlock` (Sperre aufheben). Dies ist der Notweg bei verlorener Zwei-Faktor-App, solange es keine Wiederherstellungscodes gibt (ANM-041).
  Abnahme: `reset-password` ohne Angabe → Konsole zeigt Startpasswort `xxxx-xxxx-xxxx`, Konto mit Pflichtwechsel, alle Sitzungen weg; `disable-2fa` → Konto meldet sich ohne Code an; `unlock` hebt die Sperre auf.

- **ANM-119** (P0, Status: Ist) **Protokollierte Anmelde- und Kontoereignisse** (Revisionsprotokoll, ohne Inhalte/Passwörter): Anmeldung, Abmelden (`auth.logout`), Kontowechsel (`auth.switch_account`), Sitzung beenden, Passwort ändern (`auth.password_change`), Passwort-Reset (`auth.password_reset`), 2FA abschalten (`auth.2fa_disable`), Brief-Download und -Versand (`letters.download`, `letters.send`), Konto anlegen/ändern/löschen (`user.create`, `user.update`, `user.delete`), Inhaber-Schutz (`user.owner_protected`), Admin-Vergabe verweigert (`user.admin_grant_denied`), Beobachtung (`user.watch_update`) sowie alle Aktionen aus REC-056.
  Abnahme: Je Aktion eine Audit-Zeile mit Akteur, Ziel, Zeit, ohne Passwort/Code/Token.

- **ANM-120** (P0, Status: offen) **Jede schreibende Kontoaktion wird protokolliert**: auch 2FA-Einrichtung, Kalender-Link anlegen/erneuern/löschen, Kontakt ändern/entfernen, Passkey/Geräte hinzufügen/widerrufen, Outbox-Wiederholung und zurückgezogene Anträge (Altbestand: diese Aktionen ohne Protokoll). Audit-Zeiten werden in UTC gespeichert; Zeitfilter mit Zeitzonen-Offset werden nach UTC umgerechnet.
  Abnahme: Je genannter Aktion genau ein Audit-Eintrag ohne Inhalte; ein Test iteriert über alle schreibenden Konto-Routen und fordert einen Eintrag; Abfrage `since=2026-10-18T10:00+02:00` liefert dieselben Zeilen wie `since=2026-10-18T08:00Z`.

- **ANM-121** (P3, Status: offen) **Eine Instanz je Schule**: Jede Schule hat eine eigene Instanz unter eigener Subdomain, Anmeldung nur für Konten dieser Schule; ein zentraler Anmeldepunkt für viele Subdomains kommt erst bei der zweiten Schule (ANM-062/088). Betreiber-Frage 16.10.: „Jede Schule bekommt eine eigene Subdomain, und dort können sich nur Leute dieser Schule anmelden.“
  Abnahme: Konto der Schule A ist auf der Instanz von Schule B nicht vorhanden (Anmeldung scheitert wie unbekanntes Konto); Instanzen teilen keine Sitzungen.

- **ANM-122** (P1, Status: offen) **Client-IP bei VPN und IPv6**: Anfragen hinter VPN oder IPv6-Weiterleitung erscheinen im Altbestand mit einer internen Adresse statt der Client-IP; im Neubau wird die echte Client-IP korrekt aus dem Proxy-Header bestimmt (ANM-032) und für IPv6 gilt eine einheitliche Zuordnung für Protokoll und Drosselung, sodass nicht alle IPv6-Nutzer wie eine Adresse wirken. [unklar: Gruppierung von IPv6-Adressen (Adresse oder Präfix) für Drosselung nicht vorgegeben.]
  Abnahme: Anfrage über Test-Proxy mit IPv6-Quelladresse erscheint in Protokoll und Anmeldeversuchen mit dieser Adresse (nicht mit Proxy- oder Docker-Adresse); zwei verschiedene IPv6-Nutzer teilen keinen Drosselungszähler [Zuordnung nach Festlegung].

- **ANM-123** (P2, Status: Ist) **Persönlicher Kalender-Link** (iCal): `GET`/`POST`/`DELETE /me/ical-url`; der Token steht im Adresspfad (`/ical/{token}.ics`), weil Kalenderprogramme keine Kopfzeilen senden; gespeichert nur als HMAC, Klartext einmalig bei Erzeugung; „neu erzeugen“ macht den alten Link ungültig, „löschen“ entfernt ihn; Protokolle maskieren den Pfad; Antwort mit privatem Cache. Elternzugriff nach Volljährigkeit siehe REC-067.
  Abnahme: Erzeugen zeigt die Adresse einmal; neu erzeugen → alter Link 404; Datenbank enthält nur Hash; Serverprotokoll zeigt `/ical/***`.

## B13 Konfiguration und Oberfläche der Anmelde-Seiten

**Konfigurationswerte (Umgebungsvariablen `SM_*`), soweit sie Anmeldung, Sitzung, Passwort, Codes und Konten betreffen**

| Name | Standard | Einheit/Bereich | Wirkung |
|---|---|---|---|
| `SM_MODE` | leer (abgeleitet) | `production`, `demo`, `development` | Betriebsmodus (ANM-020) |
| `SM_ENV` | `development` | `development`, `production` | Umgebung; Standards für Cookie-Secure, Log-Format, Dokumentation, Test-Postausgang |
| `SM_BASE_URL` | lokale Adresse, Port 8000 | Adresse ohne Schluss-`/` | Links, Anmelde-Adresse, Rückkehr-Adressen; Produktion https |
| `SM_APP_NAME` | Produktname aus Branding | Text | Name in Oberfläche, Briefen, Mails (einzige Stelle) |
| `SM_SECRET_KEY` | Entwicklung: automatisch; Produktion Pflicht | Text, mindestens 32 Zeichen | HMAC von Sitzungs-, API-Token, Codes, SSO-Status |
| `SM_ENCRYPTION_KEYS` | Produktion Pflicht | Liste `kid:Schlüssel` (32 Byte, Base64), erster = aktiv | Verschlüsselung (TOTP-Geheimnisse, Codeziele, Brief-Stapel, Outbox) |
| `SM_COOKIE_SECURE` | 1 in Produktion, sonst 0 | 0/1 | Secure-Attribut (zusätzlich automatisch bei HTTPS) |
| `SM_SESSION_IDLE_MINUTES` | 10080 | Minuten | Leerlauf Schüler/Eltern/Monitor; Obergrenze für Personal |
| `SM_SESSION_MAX_DAYS` | 30 | Tage | Absolute Sitzungsdauer, Cookie-Laufzeit |
| `SM_LOGIN_MAX_FAILURES` | 5 | Fehlversuche | Schwelle Paar; Konto-Schwelle = 4 × |
| `SM_LOGIN_MAX_FAILURES_IP` | 30 | Fehlversuche | Grundschwelle IP |
| `SM_LOGIN_LOCK_MINUTES` | 15 | Minuten | Zählfenster und Deckel der Wartezeit |
| `SM_REQUIRE_2FA_ROLES` | leer | Rollenliste | Rollen mit immer verpflichtender Zwei-Faktor-Anmeldung |
| `SM_AUTH_CODE_MINUTES` | 15 | 1 bis 1440 Minuten | Gültigkeit von Bestätigungs-/Reset-Codes, Links, Token |
| `SM_HIBP_CHECK` | 0 | 0/1 | Leak-Prüfung global |
| `SM_SCRYPT_N` | 32768 | Zweierpotenz, Produktion ≥ 16384 | Kostenfaktor Passwort-Hash |
| `SM_LETTER_BATCH_MINUTES` | 60 | 1 bis 1440 Minuten | Lebensdauer eines Brief-Stapels |
| `SM_ADMIN_USER` / `SM_ADMIN_PASSWORD` | `admin` / leer | Text | Erst-Admin; zugleich Inhaber-Konto |
| `SM_TRUST_PROXY` / `SM_PROXY_COUNT` / `SM_TRUSTED_PROXIES` | 0 / 1 / leer (nur Loopback) | 0/1; Stufen ≥ 1; Adressen/Netze | Vertrauen in Proxy-Header |
| `SM_RATE_LIMIT` / `SM_RATE_IP_PER_MIN` / `SM_RATE_ACCOUNT_PER_MIN` | 1 / 6000 / 1200 | 0/1; Anfragen je Minute | Allgemeines Limit |
| `SM_MAINTENANCE_INTERVAL` | 3600 | Sekunden (min. 5) | Wartungslauf (Sitzungen, Codes, Anmeldeversuche, Stapel) |
| `SM_SSE_PING_SECONDS` | 20 | Sekunden | Keep-alive des Live-Stroms |
| `SM_OUTBOUND_ALLOW` | leer | Hosts, IPs, Netze | Ausnahmen vom Schutz gegen interne Ziele |
| `SM_NOTIFY_DISPATCHER` | 1 | 0/1 | Zustellung der Konto-Nachrichten; 0 = E-Mail gilt als nicht verfügbar |
| `SM_SMTP_*`, `SM_SMS_*`, `SM_DEV_OUTBOX` | siehe ANM-107/108 | – | Versandwege |
| `SM_SSO_*`, `SM_OIDC_*` | leer | – | Anbieter (Tabelle B5) |
| `SM_ENABLE_DOCS` | `off` in Produktion, sonst `admin` | `off`, `admin`, `public` | API-Dokumentation |
| `SM_METRICS_TOKEN` | leer | Text | Messwerte nur mit Bearer-Token |

- **ANM-124** (P1, Status: Ist) Die Werte der Tabelle (Standardwerte, Einheiten, Bereiche) gelten; jede dokumentierte `SM_*`-Variable kommt im Betrieb (Container/Dienst) tatsächlich in der Anwendung an; die Vorlage der Umgebungsdatei enthält nur Platzhalter und keine Kommentare hinter Werten (sie dient als Umgebungsdatei des Dienstes); Geheimnisse stehen nie im Code, im Repository oder im Chat. Nicht lesbare Zahlenwerte führen zum Startabbruch mit Nennung der Variablen.
  Abnahme: Ein Test setzt jede Variable der Tabelle im Betriebsumfeld auf einen Nicht-Standardwert und prüft, dass die Anwendung ihn sieht; Standardstart ohne Variablen liefert die Standardwerte der Tabelle; `SM_SESSION_MAX_DAYS=abc` → Startabbruch mit Variablenname.

- **ANM-125** (P1, Status: Ist) **Feste Texte** (deutsch, Sie-Form, in **einem** Textkatalog; Produktname aus `SM_APP_NAME`): „Benutzername oder Passwort ist falsch.“ · „Bitte wenden Sie sich an das Sekretariat.“ · „Sie sind abgemeldet.“ · „Möchten Sie sich wirklich abmelden?“ · „Falls ein Konto dazu passt, ist ein Code unterwegs.“ · „Der Code ist falsch oder abgelaufen.“ · „Der Link ist ungültig oder abgelaufen.“ · „Noch N Versuch(e).“ · „Die Zeit zum Zurücksetzen ist abgelaufen.“ · „Passwort geändert“ · „Ansichtskonto: Änderungen sind mit diesem Zugang nicht möglich.“ · „Nur der Inhaber selbst kann das Konto ändern, deaktivieren, löschen, sein Passwort oder seine Zwei-Faktor-Anmeldung zurücksetzen oder ihm Rechte entziehen.“ · „Schutz vor Selbstaussperrung: Die Administration behält Rechte-, Konten- und Lizenzverwaltung.“ · „Die Rolle hat noch N Konto/Konten. Bitte eine Zielrolle wählen.“ · „2FA kann nur vom Benutzer selbst aktiviert werden“ · Knöpfe/Titel: „Abmelden“, „Weiteres Konto anmelden“, „Konto wechseln“, „Weiter als …“, „Mit anderem Konto anmelden“, „Sitzung beenden“, „Alle anderen Sitzungen beenden“, „Passwort zurücksetzen“, „Verbindung testen“, „Mit Microsoft anmelden“, „Mit Apple anmelden“, „Mit Schulkonto anmelden“, „E-Mail & Handynummer“, „Meine Sitzungen“, „Verbundene Konten“, „Ihre Rolle“. Alle Texte stehen in Sie-Form auch für Schüler/innen („du“, „dein“ nicht).
  Abnahme: Ein Test durchsucht den Textkatalog nach „du“, „dein“, „dir“, „wende dich“ → keine Treffer; jeder Text der Aufzählung ist im Katalog vorhanden und wird im jeweiligen Fehlerfall ausgeliefert; Produktname in Briefen und Mails folgt `SM_APP_NAME`.

- **ANM-126** (P2, Status: Ist) **Seiten und Adressparameter**: `/login` (Anmeldung), Seite „Abgemeldet“, `/profil` (Abschnitte Zwei-Faktor, Kalender-Link, Meine Sitzungen, Ihre Rolle, Kontakt und Wiederherstellung, Verbundene Konten, Datenexport), Passwort ändern, Passwort vergessen, `/passwort-zuruecksetzen` (Parameter `token`), `/konten-verbinden`, `/anmeldedienste`, `/anmelde-richtlinien`, `/sicherheit`, `/zugangsdaten/{id}`, `/rechte`, `/beobachtete-konten`, `/test-postausgang` (nur Entwicklung); Rückmeldungen über Adressparameter: `/profil` mit `kontakt`, `verbunden`, `sso_error`; `/login` mit `reset=ok`. Jede Seite hat eine Überschrift (h1). Öffentliche Seiten (Passwort vergessen/zurücksetzen, SSO-Knöpfe, Test-Postausgang) leiten nie zur Anmeldung. Frontend-Prüfungen blenden nur aus; die Entscheidung trifft der Server.
  Abnahme: Jede Seite erreichbar für die erlaubte Rolle und mit 403/Weiterleitung für andere (Server-Antwort geprüft); `/anmeldedienste` mit Schulleitung → 403/404; jede Seite hat genau eine h1; `/login?reset=ok` zeigt „Passwort geändert“.

- **ANM-127** (P2, Status: Ist) **Anbieter-Fehlerseiten**: Fehler der Anbieter-Anmeldung (Abbruch durch die Person, Token-Fehler, Rückkehr ohne gültigen Status) zeigen je Fehlerfall einen eigenen deutschen Text in Sie-Form auf der Anmeldeseite (Parameter `sso_error` am Zielort); Fehler der stillen Anmeldung werden nicht angezeigt. [unklar: Wortlaute im Altbestand nicht erfasst; im Textkatalog (ANM-125) festzulegen.]
  Abnahme: Abbruch beim Anbieter → Anmeldeseite mit Fehlertext zum Abbruch; manipulierter Status → anderer Text; stille Anmeldung scheitert → keine Meldung.

- **ANM-128** (P1, Status: offen) **Barrierefreiheit und Handy der Anmelde- und Konto-Seiten** (BITV 2.0 / WCAG 2.1 AA): 390 px Breite ohne waagerechten Bildlauf, Zielflächen ≥ 44 px, Kontrast nach WCAG 2.1 AA, hell und dunkel, vollständige Tastaturbedienung (sichtbarer Fokus, sinnvolle Reihenfolge, Dialoge mit Fokusfalle und Esc), Beschriftungen und Hilfen per `aria-describedby`, Fehler am Feld, 200 % Zoom ohne Verlust, Bewegung reduzieren; Auge-Schaltfläche des Passwortfelds mit zugänglichem Namen und Zustand; Passwort-Manager-Unterstützung (ANM-006). (Altbestand: nur Auge-Schaltfläche und Passwort-Manager-Unterstützung belegt.)
  Abnahme: Automatische Prüfung (z. B. axe-core) auf `/login`, Passwort vergessen/zurücksetzen, `/profil`, `/konten-verbinden`, `/sicherheit` ohne Verstöße der Stufe AA; Playwright-Bildschirmfoto bei 390 px ohne Bildlauf; Tastaturdurchlauf Anmeldung → Code → Abmelden ohne Maus möglich.

## Anhang A – Zuordnung der Befunde des Altbestands

| Befund | Entscheidung / Anforderung |
|---|---|
| Zielrolle „ausgeblendet“ wird beim Löschen nicht geprüft | REC-015 |
| Passwort-Zurücksetzen ohne Umfang bei SL/SEK | REC-033 (Zielmenge begrenzt) |
| Schulbegleitung: Zweckliste enthält `student_absence.read`; `substitution.read`/`channels.use` ohne Umfang; Kinder im Konto-Detail nur bei Eltern | REC-050, REC-059; [unklar: Kinder-Ausgabe für Schulbegleitung im Konto-Detail] |
| Liste „sensibler Rechte für Schüler-, Eltern-, Ansichtsrollen“ (24) ungenutzt | entfällt (REC-047) |
| Volljährigkeit überschreibt Schul-Abweichung | REC-061 |
| Vorlage „Administration“ ohne Warnung kopiert | REC-011 |
| Zweig-Sicht nur Grundrolle `abteilungsleitung` | REC-019 |
| Unwirksame gespeicherte Abweichungen werden still ignoriert | REC-054 (so übernommen) |
| Schulleitung hat von Haus aus kein `timetable.generate`/`.edit` | Standard (Tabelle R7.2), kein Fehler |
| Zuschauer hat `history.restore` im Standard | R7.2; schreibend nur bei ausdrücklicher Erteilung (REC-021) |
| Umfangsbezeichnung „Nur Schüler/Eltern“ nennt Schulbegleitung nicht | Bezeichnung bleibt, der Hilfetext nennt Schulbegleitung (R7.1) |
| Zwei Ordnungen (Anzeige-Gruppen, Grundtypen) | R1.1: beide bleiben mit klar getrennter Bedeutung (Anzeige-Gruppe nur Darstellung) |
| Monitor ist Anzeigerolle, aber nicht schreibgeschützt | REC-024 |
| Erteilung ohne Umfangsauswahl | REC-052 |
| Kein Umfang „Standort“ | R7.1 |
| Klassenleitung als Titel, nicht als Konto | REC-006 |
| Rollenname über 80 Zeichen | REC-009 |
| Entwicklungsmodus als Standard; Passwort des Erst-Admin; Hash-Aufwand der Startpasswörter; gemeinsame Versuchszahl der Reset-Codes; Leak-Prüfung fail-open; unterschiedliche Cookie-Regel der Hinweis-Cookies | ANM-020, ANM-019, ANM-014/015, ANM-101, ANM-013, ANM-078 ([unklar: Secure-Regel der Hinweis-Cookies]) |
| Keine Wiederherstellungscodes; TOTP-Replay-Schutz prozesslokal | ANM-041, ANM-042 |
| Brieftext nennt die Startpasswort-Frist nicht | ANM-016, ANM-113 |

## Anhang B – Offene Entscheidungen des Betreibers (für das Neubau-Team zu klären)

1. Administration und Gesundheits-/Noten-/Förderdaten: harte Grenze oder Warnung (REC-060).
2. Delegation des Inhaber-Passworts an einen zweiten Administrator (REC-028).
3. Elternkonten nur durch Sekretariat, Schulleitung, Administration zurücksetzen (REC-033).
4. Google/Apple für Schüler/innen standardmäßig aus (ANM-057); automatische Anmeldung Standard aus (ANM-049).
5. Leak-Prüfung einschalten (ANM-013); Apple (Port 443, 99 US-Dollar/Jahr), Vermittler, Landes-Login (ANM-052, ANM-062, ANM-063).
6. Umleitung der Nebenadresse und Abschalten des HTTP-Zugangs im Heimnetz (ANM-081).
7. Volljährigkeits-Ergänzung gegen Schul-Abweichung (REC-061); Rechtsgrundlage und Information zur Beobachtung (REC-039).
8. Zwei-Faktor-Pflicht über die Administration hinaus (ANM-037/040); Wiederherstellungscodes (Zahl, Format) (ANM-041).

## Zählung

Anforderungen gesamt 202: REC-001 bis REC-074 (74), ANM-001 bis ANM-128 (128). Priorität P0 114, P1 63, P2/P3 25. Status: Ist = im Altbestand gebaut; offen = gefordert, noch nicht gebaut.

<!--ENDE-->
