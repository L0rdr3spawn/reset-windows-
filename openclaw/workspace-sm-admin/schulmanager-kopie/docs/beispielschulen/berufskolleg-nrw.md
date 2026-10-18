# Beispielschule `berufskolleg-nrw` – Berufskolleg Lindenhain Wesselbrück (fiktiv)

> **Fiktiv.** Schule, Orte, Adressen und Klassennamen sind erfunden. Die Datei enthält **keine personenbezogenen Daten**:
> keine Namen, Kürzel, Fotos oder Stundenpläne realer Schüler/innen oder Lehrkräfte und keine Klassenlisten realer
> Schulen. Verwendet wurden nur amtliche bzw. allgemeine Rahmendaten (APO-BK, Erlasse, Bildungspläne, Ferienordnung,
> aggregierte Statistik). Was nicht belegt ist, steht in der JSON unter `annahme` bzw. `annahmen[]`.

Daten: [`berufskolleg-nrw.json`](berufskolleg-nrw.json) · Schuljahr 2026/27 · Stand 10.10.2026

## Kurzbeschreibung

Ein kleines Berufskolleg in Nordrhein-Westfalen mit **6 Bildungsgängen**. Jeder hat eine eigene **„Klasse 11“
(Unterstufe)**, aber die Klassen lernen jeweils etwas anderes und folgen einem anderen Rhythmus:

| Bildungsgang (APO-BK) | Klassen | Form / Rhythmus | Std./Woche |
|---|---|---|---|
| Fachinformatiker/in, Fachklassen des dualen Systems (A 1.1) | FI11a–c, FI12a–b, FIA13, FIS13 | Teilzeit, 1 langer + 1 kurzer Tag; **FI11c im Wochenmuster (Woche 1/2)** | 12 |
| Bauberufe Hochbau – Maurer/in u. a. (A 1.1) | BAU11a–b, MAU12, MAU13 | **Blockunterricht** nach Landeserlass (3–4 Blöcke je Stufe) | 38 je Blockwoche |
| Berufsfachschule Informationstechnische/r Assistent/in + FHR (C 1) | ITA11–13 | Vollzeit; ITA12 mit 4 Wochen Praktikum | 34 |
| Fachoberschule Informatik, Kl. 11/12 (C) | FOS11a–b, FOS12 | Kl. 11: 3 Betriebstage + 2 Schultage; Kl. 12: Vollzeit | 12 / 32 |
| Berufliches Gymnasium AHR Mathematik/Informatik (D 21) | GI11a–b, GI12, GI13 | Vollzeit; EF im Klassenverband, Q1/Q2 im **Kurssystem** (LK INF + M) | 32–33 |
| Ausbildungsvorbereitung (A 2.1/A 2.2) | AV11a, AV11b, AVT11 | Vollzeit mit 3 Praktikumstagen bzw. Teilzeit | 16 / 12 |

Zahlen: **24 Klassen, 543 Schüler/innen, 2 Standorte** (Hauptstandort HS, Bautechnik-Zentrum BZ, 20 Min. Wegezeit),
**28 Lehrkräfte** (22 Vollzeit à 25,5 Std., 6 Teilzeit), **34 Räume**, 10-Stunden-Raster ab 07:30 mit Doppelstunden.
Klassengruppen: IT-Zweig, Bau, Abitur-Klassen, Fachabi-Klassen, Duale Fachklassen, Blockklassen, Vollzeitklassen,
Klasse 11 (alle Bildungsgänge), Standort BZ. Eine Klasse darf in mehreren Gruppen sein, z. B. FOS12 in IT-Zweig,
Fachabi und Vollzeit.

Die Schule ist absichtlich klein. So läuft der Stundenplan-Generator schnell durch und die Testfälle bleiben
überschaubar. Echte Berufskollegs haben oft 2.000–4.000 Schüler/innen.

## Wofür sich die Schule zum Testen eignet

- **Mehrere Bildungsgänge mit eigener Klasse 11** und eigenen Klassennamen (Anforderung A-38).
- **Klassengruppen, die sich überschneiden** (A-43).
- **Unterschiedliche Rhythmen in einer Schule**:
  - Teilzeittage
  - Rhythmus „jede 2. Woche“ nur für eine Klasse (FI 11c)
  - Blockunterricht mit festen Kalenderwochen
  - Praktikumstage und Praktikumsblock
  - früheres Unterrichtsende der Abiturklasse
- **Feier- und Ferientage innerhalb von Blockwochen**, um die Jahresstunden zu prüfen (Soll laut Stundentafel
  gegen das, was im Kalender tatsächlich ankommt).
- **Oberstufe mit Kurssystem**: Leistungskurse und Grundkurse, eine neu einsetzende Fremdsprache und ein
  Religion/Philosophie-Band.
- **Zwei Standorte**:
  - Wegezeit für Lehrkräfte
  - Bauklassen nur am BZ
  - Sporthalle am BZ nur Mo–Mi verfügbar
- **Geteilter Unterricht**: Fachpraxis, Labore und Lehrbauhalle mit 2 Gruppen gleichzeitig.
- **Klassenfrequenz-Grenzfälle**: AVT11 liegt unter dem Mindestwert, MAU13 genau auf dem Mindestwert 16.
- **Versetzung zum Schuljahresende** über verschiedene Stufenbezeichnungen und Abschlussjahrgänge (A-39).

## Testliste – bitte ausfüllen und zurückgeben

Bitte die letzte Spalte ausfüllen: **OK**, oder was stattdessen passiert ist und **wie es sein soll**. Die Tabelle
kann so, wie sie ist, zurückkommen.

| Nr. | Was testen | Wie | Erwartet (Soll) | Ihre Rückmeldung (Ist / wie es sein soll) |
|---|---|---|---|---|
| 1 | Struktur anlegen/importieren | Bildungsgänge, Klassen, Gruppen und Standorte aus der JSON übernehmen | 6 Bildungsgänge, 24 Klassen, 9 Gruppen, 543 Schüler/innen, 2 Standorte | |
| 2 | Klasse 11 je Bildungsgang | Gruppe „Klasse 11“ öffnen, dann je Klasse die Stundentafel | 13 Klassen; FI11a 12 Std., ITA11 34, GI11a 33, BAU11a 38 je Blockwoche, FOS11a 12, AV11a 16 | |
| 3 | Gruppen überschneiden sich | Gruppen „IT-Zweig“, „Fachabi“ und „Vollzeit“ vergleichen | FOS12 ist in allen drei Gruppen. ITA11–13 sind in IT-Zweig und Fachabi. | |
| 4 | Teilzeit-Unterrichtstage | Plan von FI11a erzeugen | Unterricht nur Mo 1.–8. und Do 1.–4. Stunde, sonst frei | |
| 5 | Wochenmuster (Woche 1/2) | Plan von FI11c für die Wochen ab 07.09. und ab 14.09.2026 | Woche 1: Mi und Do je 8 Std. Woche 2: nur Mi. Im Mittel 12 Std. | |
| 6 | Blockunterricht | Kalender von BAU11a, MAU12 und MAU13 für Sept.–Dez. 2026 | MAU13 07.–25.09., MAU12 28.09.–16.10., BAU11a/b 02.–20.11., MAU13 23.11.–22.12. Die Stufen überschneiden sich nie. | |
| 7 | Feiertage im Block | MAU12, Block 19.05.–04.06.2027 | Kein Unterricht am 27.05. (Fronleichnam) und am 28.05. (beweglicher Ferientag). Der Block beginnt erst Mi 19.05. (Pfingstferientag ist der 18.05.). | |
| 8 | Soll/Ist der Jahresstunden | Jahresauswertung der Bauklassen | Unterstufe 494 Std. (65 Tage), Mittelstufe 456 (60), Oberstufe 382 (50). **Warnung** bei MAU12 und MAU13, weil das Soll 480 ist. | |
| 9 | Praktikum | FOS11a in einer normalen Woche; ITA12 im Februar 2027 | FOS11a: Mi–Fr kein Unterricht (Betrieb). ITA12: 01.–26.02.2027 kein Unterricht. | |
| 10 | Früheres Unterrichtsende | GI13 nach dem 19.03.2027 | Keine Stunden mehr. Lehrkräfte werden frei, z. B. für Vertretungen. | |
| 11 | Kurssystem Oberstufe | Kurse in GI12/GI13 | LK INF und M je 5 Std., GK je 3 Std., Spanisch 4. Religion ev., Religion kath. und PP laufen parallel in derselben Stunde. | |
| 12 | Doppelstunden | Fächer mit `doppelstunde_bevorzugt` | Lage nur in 1–2, 3–4, 5–6, 7–8 oder 9–10, nie über eine Pause hinweg | |
| 13 | Geteilter Unterricht | BAU-PRA (Teilung 2) bei BAU11a | 2 Lehrkräfte für Fachpraxis und 2 Lehrbauhallen gleichzeitig belegt | |
| 14 | Zwei Standorte | Lehrkraft mit Unterricht an HS und BZ am selben Tag | Ein Wechsel ist nur über eine große Pause oder die Mittagspause möglich (20 Min.). Bauklassen haben nur Räume am BZ. | |
| 15 | Eingeschränkte Raumverfügbarkeit | Sport der Bauklassen in einer Blockwoche | Sport liegt nur Mo–Mi, weil die Sporthalle am BZ nur dann frei ist | |
| 16 | Ferien und Feiertage | Kalender 2026/27 | 1. Schultag Mi 02.09.2026. Frei: 17.–31.10., 23.12.–06.01., 08.02., 22.03.–03.04., 06./07.05., 17./18.05., 27./28.05.2027. Sommerferien ab 19.07.2027. | |
| 17 | Nachmittagsunterricht | Plan von GI12, Montag | Unterricht bis zur 10. Stunde (16:10) | |
| 18 | Klassenfrequenz | Hinweise/Validierung | AVT11 (14) wird als „unter Mindestwert“ markiert. MAU13 (16) liegt genau auf der Grenze und bekommt keine Warnung. | |
| 19 | Lehrkräfte-Abdeckung | Lehrkräfte automatisch zuweisen | Jedes Fach hat geeignete Lehrkräfte. Bedarf ca. 532 Std., Kapazität 658,5 Std. Keine Lehrkraft über 25,5 Std. (Teilzeit: über ihr Deputat). | |
| 20 | Versetzung zum Schuljahresende | Schuljahreswechsel auslösen | Jahrgang 11→12 und 12→13, Bezeichnungen passend (z. B. EF→Q1). FIA13, FIS13, MAU13, ITA13, FOS12, GI13 und alle AV-Klassen gehen ab. | |

Wenn eine Funktion fehlt, bitte „fehlt“ eintragen und kurz beschreiben, wie sie sein soll.

## Wichtige Annahmen (Auszug, vollständig in der JSON)

- Die Bündelungsfächer für Fachinformatiker und Bau sowie die Verteilung auf Wochenstunden sind erfunden. Belegt sind
  nur die Jahressummen:
  - Fachinformatiker: 320/280/280 Std. laut KMK
  - berufsübergreifender Lernbereich: je 40 Std. pro Fach und Jahr
  - insgesamt 480 Std. pro Jahr laut Anlage A 1.1
- Die Stundentafeln für ITA, FOS 12, Berufliches Gymnasium und AV sind plausible Annahmen innerhalb der belegten
  Rahmen.
- Für die Bau-Blockzeiten 2026/27 gibt es zwei Fassungen. Verwendet ist die Fassung BASS 12-61 Nr. 1.4 mit der
  Änderung vom 26.06.2026. Die PDF-Fassung nennt ein 2-Block-Modell. Vor einem echten Einsatz bitte im Erlass prüfen.
- Die drei beweglichen Ferientage (08.02., 07.05., 28.05.2027) sind schulintern fiktiv gewählt.
- Die Primärquellen (recht.nrw.de, bass.schule.nrw, schulministerium.nrw, berufsbildung.nrw.de) ließen sich hier nicht
  direkt öffnen. Die Werte stammen aus Websuche-Auszügen dieser Seiten.

## Quellen

| ID | Quelle | Stand |
|---|---|---|
| Q01 | [APO-BK (BASS 13-33 Nr. 1.1)](https://bass.schule.nrw/3129.htm) | BASS 2026/2027 |
| Q02 | [Bildungsplan Fachklassen Politik/Gesellschaftslehre – Rahmenstundentafel A 1.1](https://www.qua-lis.nrw.de/system/files/media/document/file/bp_fachklassen_wuv_politik-gesellschaftslehre.pdf) | abgerufen 10.10.2026 |
| Q03 | [Bildungsplan Fachklassen Politik/Gesellschaftslehre, Gestaltung (BP 2023)](https://berufsbildung.nrw.de/system/files/media/document/file/fachklassen_gest_politik-gesellschaftslehre_bp2023.pdf) | 2023 |
| Q04 | [KMK-Rahmenlehrplan Fachinformatiker/in](https://www.kmk.org/fileadmin/Dateien/pdf/Bildung/BeruflicheBildung/rlp/Fachinformatiker_19-12-13_EL.pdf) | Beschluss 13.12.2019 |
| Q05 | [Lernfeldübersicht Fachinformatiker/in (Zeitrichtwerte)](https://kstl.de/wp-content/uploads/2020/04/Lernfelder-FI-AwE.pdf) | 2020 |
| Q06 | [Bildungsplan NRW Fachinformatiker/in](https://www.berufsbildung.nrw.de/cms/upload/_lehrplaene/a/fachinformatiker.pdf) | RdErl. 27.08.2021 |
| Q07 | [Umsetzung RLP in Bildungsplan NRW (Bündelungsfächer)](https://berufsbildung.nrw.de/system/files/media/document/file/6_umsetzung_rlp_in_bpl_frau_strate.pdf) | März 2020 |
| Q08 | [BIBB Berufesuche Maurer/in (neu ab 01.08.2026)](https://www.bibb.de/dienst/berufesuche/en/index_berufesuche.php/profile/apprenticeship/maurer26) | abgerufen 10.10.2026 |
| Q09 | [Vorläufiger Bildungsplan NRW Maurer/in 2026](https://berufsbildung.nrw.de/system/files/media/document/file/bau-hoch_maurer_vbp2026.pdf) | in Kraft 01.08.2026 |
| Q10 | [Baulinks: Neue Ausbildungsordnungen Bauberufe](https://www.baulinks.de/webplugin/2026/1123.php4) | 2026 |
| Q11 | [BASS 12-61 Nr. 1.4 Blockunterricht an Berufskollegs](https://bass.schule.nrw/20199.htm) | inkl. Änderung 26.06.2026 |
| Q12 | [BASS 12-61 Nr. 1.4 (PDF-Fassung)](https://bass.schule.nrw/pdf/3623.pdf) | abweichende Blockzeiten |
| Q13 | [Öffentlicher Blockplan Bau/Maurer 2026/27 eines Berufskollegs (nur Abgleich, ohne Personendaten)](https://bk-beckum.kreis-warendorf.de/fileadmin/bkbeckum-2021/bkbeckum/downloads/Blockpl%C3%A4ne/Blockplan_Bau_Maurer_26_27_.pdf) | 2026/27 |
| Q14 | [MSB NRW: Ferienordnung bis 2029/30](https://www.schulministerium.nrw/ferienordnung-fuer-nordrhein-westfalen-fuer-die-schuljahre-bis-202930) | abgerufen 10.10.2026 |
| Q15 | [BASS 12-65 Nr. 1 Ferienordnung (bewegliche Ferientage)](https://bass.schule.nrw/191.htm) | RdErl. 19.05.2022 |
| Q16 | [Feiertage NRW 2027](https://www.schnelle-online.info/NRW/Feiertage-NRW-2027.html) | abgerufen 10.10.2026 |
| Q17 | [Feiertage NRW 2026](https://www.kalenderpedia.de/feiertage/feiertage-nrw-2026.html) | abgerufen 10.10.2026 |
| Q18 | [MSB NRW: Klassenrichtwerte vollzeitschulischer Angebote (AV 26/29, BFS 28/31)](https://www.schulministerium.nrw/node/26629) | Datum nicht ermittelt |
| Q19 | [VO zu § 93 Abs. 2 SchulG (Pflichtstunden BK 25,5; § 6 Klassenbildungswerte)](https://recht.nrw.de/lrgv/rechtsverordnung/01082026-verordnung-zur-ausfuehrung-des-ss-93-abs-2-schulgesetz-vo-zu-ss-93/) | Fassung 01.08.2026 |
| Q20 | [MSB NRW: FAQ nebenberufliche Lehrkräfte am BK](https://www.schulministerium.nrw/lehrkraefte/ich-moechte-lehrerin-werden/nebenberufliche-lehrkraefte-am-berufskolleg/fragen-und) | abgerufen 10.10.2026 |
| Q21 | [MSB NRW: Fachoberschule (FHR/AHR)](https://www.schulministerium.nrw/fachoberschule-fhrahr) | abgerufen 10.10.2026 |
| Q22 | [BASS 13-31 Nr. 1 Praktikum-Ausbildungsordnung](https://bass.schule.nrw/6911.htm) | BASS 2026/2027 |
| Q23 | [BASS: FOS Fachbereich Informatik, vorläufige Bildungspläne](https://bass.schule.nrw/20154.htm) | in Kraft 01.08.2025 |
| Q24 | [BASS 15-37: Anlage C 1, Fachbereich Informatik (ITA + FHR)](https://bass.schule.nrw/20049.htm) | Bildungspläne 07/2024 |
| Q25 | [Bildungsplan C 1 ITA – Datenbanken](https://www.berufsbildung.nrw.de/cms/upload/_lehrplaene/c/informatik/bfsc1_ita_datenbank_2024.pdf) | 2024 |
| Q26 | [Standardsicherung NRW: Bildungsgang Anlage D 21](https://www.standardsicherung.schulministerium.nrw.de/cms/zentralabitur-berufliches-gymnasium/bildungsgaenge/bildungsgang.php?id=21) | abgerufen 10.10.2026 |
| Q27 | [Bildungspläne Berufliches Gymnasium D 21 (Informatik)](https://berufsbildung.nrw.de/bildungsgaenge-bildungsplaene/bildungsplaene-berufliches-gymnasium-und-fachoberschule-anlage-d-10) | abgerufen 10.10.2026 |
| Q28 | [APO-BK Anlage D, ältere Fassung (Stundentafel-Muster)](https://recht.nrw.de/system/files/BHA/23439-31143-sgv_223_19990526_2_anlage4.pdf) | ältere Fassung |
| Q29 | [APO-BK Anlage A 2.1 Ausbildungsvorbereitung](https://recht.nrw.de/system/files/BA/4634-51588-sgv_223_19990526_2_anlagea21.pdf) | abgerufen 10.10.2026 |
| Q30 | [MSB NRW: 8. Änderungsverordnung APO-BK (Entwurf)](https://www.schulministerium.nrw/25062026-8-aenderungsverordnung-zur-ausbildungs-und-pruefungsordnung-bk) | 25.06.2026 |
| Q31 | [MSB NRW: Schulwesen aus quantitativer Sicht 2024/25](https://www.schulministerium.nrw/system/files/media/document/file/quantita_2024.pdf) | 19.09.2025 |
| Q32 | [MSB NRW: Statistische Daten 2025/26](https://www.schulministerium.nrw/system/files/media/document/file/statistische_daten_2025-26_250822.pdf) | 22.08.2025 |
| Q33 | [Schuldatenbank Stadt Münster (aggregierte Schülerzahlen)](https://www.stadt-muenster.de/schulamt/schule-in-muenster/schuldatenbank/schulen/detailansicht/schule/95) | 2025/26 |
