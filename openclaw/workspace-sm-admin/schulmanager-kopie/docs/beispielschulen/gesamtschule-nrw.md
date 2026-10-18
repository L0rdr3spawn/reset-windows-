# Beispielschule `gesamtschule-nrw` – Gesamtschule Musterhausen-Ost (fiktiv)

> **Fiktiv.** Schule, Orte und Standorte sind erfunden. Die Datei enthält **keine personenbezogenen Daten**:
> keine Namen, Kürzel, Fotos oder Stundenpläne realer Schüler/innen oder Lehrkräfte und keine Klassenlisten realer
> Schulen. Lehrkräfte sind nur als Anzahl und Fächerkombination angegeben. Verwendet wurden nur amtliche bzw.
> allgemeine Rahmendaten (APO-S I, APO-GOSt, VO zu § 93 Abs. 2 SchulG, Erlasse, Ferienordnung, Feiertagsgesetz,
> aggregierte Schulstatistik). Was nicht belegt ist, steht in der JSON als `annahme` bzw. in `annahmen[]`.

Daten: [`gesamtschule-nrw.json`](gesamtschule-nrw.json) · Schuljahr 2026/27 · Stand 10.10.2026

## Kurzbeschreibung

Eine große **Gesamtschule im gebundenen Ganztag** mit **2500 Schüler/innen** an **zwei Standorten**. Sie ist mit
12 Zügen bewusst groß, damit Last- und Standorttests möglich sind. Zur Schule gehören die Sekundarstufe I, zwei
Sprachfördergruppen und eine gymnasiale Oberstufe.

| Bildungsgang | Klassen | Form / Rhythmus | Std./Woche |
|---|---|---|---|
| `sek1-ge` – Sekundarstufe I (Jg. 5–10) | 5a–l … 10a–l (72 Klassen, davon 12 Klassen des Gemeinsamen Lernens: e, j) | Rhythmus (nur Kunst/Musik ab Kl. 7 im Wechsel: jede 2. Woche ab Woche 1 bzw. 2); E-/G-Kurse; Wahlpflicht ab 7; Förderkurse; Betriebspraktikum Jg. 9 als Block | 30 / 30 / 31 / 32 / 33 / 32 (= 188) |
| `sfg-daz` – Sprachfördergruppen für neu Zugewanderte | SFG-U (Jg. 5–7), SFG-O (Jg. 8–10), je 16 | wöchentlich, DaZ-Schwerpunkt (12 Std. Deutsch als Zweitsprache) | 30 / 32 |
| `gost-ge` – gymnasiale Oberstufe | EF-1–8, Q1-1–8, Q2-1–7 (23 Tutorgruppen) | Kurssystem (LK 5, GK 3, Vertiefungs-/Projektkurs 2), Q2 mit frühem Unterrichtsende | Ø 34 |

**Standorte** (Wegezeit 15 Minuten, entspricht 1 Stunde Abstand):

- **Unterstufe – Haus Nord (U)**: Jg. 5–7 und SFG-U, 37 Klassen, 972 Schüler/innen.
- **Oberstufe – Haus Süd (O)**: Jg. 8–10, SFG-O und Oberstufe, 60 Klassen bzw. Tutorgruppen, 1528 Schüler/innen.

**Weitere Zahlen**:

- 97 Klassen bzw. Tutorgruppen, 2500 Schüler/innen (Sek I 1944, Oberstufe 556: EF 200, Q1 186, Q2 170)
- 36 Fächer, 30 Klassengruppen
- 187 Lehrkräfte (ca. 164,6 Vollzeitstellen) und zusätzlich 10 Lehrkräfte für Sonderpädagogik
- 165 Räume

**Zeitraster**: 08:00, 45 Minuten ohne Wechselzeit (90-Minuten-Blöcke), Pausen 20 / 20 / 60 / 10 Minuten. Der Ganztag
geht Mo/Di/Do bis zur 8. Stunde (15:40) und Mi/Fr bis zur 6. Stunde (13:10).

## Wofür sich die Schule zum Testen eignet

- **Last** (A-02): rund 2500 Schüler/innen, 97 Lerngruppen und 187 Lehrkräfte. Dazu kommen viele parallele Kurse:
  E-/G-Kurse, Wahlpflicht, Religion, Förderung und Oberstufen-Schienen.
- **Zwei Standorte**:
  - Wegezeit für Lehrkräfte; Anteile laut Annahme: 35 % nur U, 45 % nur O, 20 % an beiden.
  - Fachräume je Standort.
  - Klassen wechseln bei der Versetzung von 7 nach 8 den Standort.
- **Fachleistungsdifferenzierung**: Je Band aus 4 Klassen gibt es 2 Erweiterungs- und 2 Grundkurse gleichzeitig.
  Das gilt für M und E ab Kl. 7, D ab Kl. 8 und Chemie ab Kl. 9. Chemie in Jg. 9/10 braucht 4 Chemieräume
  gleichzeitig.
- **Wahlpflichtband ab Kl. 7**: 13 Gruppen aus 12 Klassen gleichzeitig (F, S, NW, Wirtschaft und Arbeitswelt,
  Darstellen und Gestalten, Informatik), jeweils mit passenden Fachräumen.
- **Rhythmus** (A-28, A-29):
  - Rhythmus: Kunst jede 2. Woche ab Woche 1, Musik jede 2. Woche ab Woche 2 (Jg. 7–10), sonst jede Woche gleich.
  - Dazu ein Block, das Betriebspraktikum Jg. 9 (3 Wochen).
- **Klassen mit Besonderheiten**:
  - Klassen des Gemeinsamen Lernens mit 24 Schüler/innen; die Unterschreitung der Bandbreite ist zulässig.
  - Sprachfördergruppen mit eigener Stundentafel und altersgemischtem Jahrgang.
  - Testfall: Wechsel einer Schülerin aus der Sprachfördergruppe in eine Regelklasse.
- **Religion mit 4 Optionen** (ER, KR, IR, PP): 5 Gruppen je Band, und **Förderkurse** über Ergänzungsstunden.
- **Ganztag**: lange und kurze Tage, Mittagspause 60 Minuten, Doppelstunden nur innerhalb der 90-Minuten-Blöcke.
- **Oberstufe**:
  - 18 bzw. 17 Leistungskurse in 2 Schienen, 9 bis 11 GK-Schienen.
  - Q2 mit Unterrichtsende vor dem Abitur (fiktiver Termin).

## Testliste – bitte ausfüllen und zurückgeben

Bitte die letzte Spalte ausfüllen: **OK**, oder was stattdessen passiert ist und **wie es sein soll**. Die Tabelle
kann so, wie sie ist, zurückkommen.

| Nr. | Was testen | Wie | Erwartet (Soll) | Ihre Rückmeldung (Ist / wie es sein soll) |
|---|---|---|---|---|
| 1 | Struktur importieren | Bildungsgänge, Klassen, Gruppen, Fächer und Standorte aus der JSON übernehmen | 3 Bildungsgänge, 97 Klassen/Tutorgruppen, 30 Gruppen, 36 Fächer, 2500 Schüler/innen. Standort U: 37 Klassen/972 SuS, Standort O: 60/1528. | |
| 2 | Stundentafel und Rahmen | Stundentafeln Jg. 5–10 öffnen | 30 / 30 / 31 / 32 / 33 / 32 Std., Summe 188 (davon 179 Kern- und 9 Ergänzungsstunden). Jede Stufe liegt im Rahmen (z. B. Jg. 9: 31–34). | |
| 3 | Stundentafel Jg. 9 im Detail | 9a öffnen | D 4, M 4, E 4 (je E/G), GL 3, CH 2 (E/G), PH 1, WI 2, TC 1, WP 3, KU 2 (Woche 1), MU 2 (Woche 2), Religion 2, SP 3, Förder 2 = 33 | |
| 4 | Rhythmus (jede 2. Woche) | Plan von 7a in der Woche ab 07.09. und ab 14.09.2026 | Woche ab 31.08. = Woche 1, ab 07.09. = Woche 2, ab 14.09. = Woche 3. Kunst-Doppelstunde nur in Woche 1 und 3, Musik-Doppelstunde nur in Woche 2. Jg. 5/6 haben KU und MU jede Woche. | |
| 5 | E-/G-Kurse | Band B7-1 (7a–7d), Mathematik | 4 Kurse (M-E1, M-E2, M-G1, M-G2) liegen gleichzeitig, 4 Std. Deutsch erst ab Jg. 8, Chemie erst ab Jg. 9 differenziert. | |
| 6 | Chemie-Raumengpass | Plan von Jg. 9 erzeugen | Die 4 CH-Kurse eines Bandes liegen gleichzeitig in den 4 Chemieräumen am Standort O. Zwei Bänder liegen nie gleichzeitig in Chemie. | |
| 7 | Wahlpflichtband | Plan von Jg. 7 (Standort U) | 13 Gruppen gleichzeitig über 7a–7l, 3 Std.: F 2, S 3, NW 3 (NW-Räume), AW 2 (Technik), DG 2 (Aula/Mehrzweckraum), IF 1 (Informatik) | |
| 8 | Religion und Förderband | Band B5-2 (5e–5h) | Religion: 5 Gruppen gleichzeitig (ER 1, KR 2, IR 1, PP 1). Förderband: 5 Gruppen gleichzeitig, Jg. 5–7 1 Std., ab Jg. 8 2 Std. | |
| 9 | Zeitraster | Einstellungen → Zeitraster | 1. Std. 08:00–08:45, 2. 08:45–09:30, 3. 09:50, 5. 11:40, 7. 14:10–14:55, 8. bis 15:40, 9. 15:50, 10. 16:35–17:20 | |
| 10 | Doppelstunden | Fächer mit `doppelstunde_bevorzugt` | Lage nur in 1–2, 3–4, 5–6, 7–8 oder 9–10, nie über eine Pause hinweg | |
| 11 | Ganztag | Wochenplan einer Klasse aus Jg. 5 und Jg. 9 | Mo/Di/Do Unterricht bis zur 8. Std. möglich, Mi/Fr höchstens bis zur 6. Std. Mittagspause 13:10–14:10. | |
| 12 | Zwei Standorte | Lehrkraft mit Unterricht in Jg. 7 (U) und Jg. 8 (O) am selben Tag | Zwischen einem Wechsel liegt mindestens eine freie Stunde oder eine große Pause (15 Min. Wegezeit). Klassen von U haben nur Räume an U. | |
| 13 | Klassen des Gemeinsamen Lernens | Validierung/Hinweise für 5e, 5j … 10j | 24 Schüler/innen. Keine Warnung (bzw. nur der Hinweis „Gemeinsames Lernen“), obwohl der Wert unter 25 liegt. | |
| 14 | Sprachfördergruppe | SFG-U öffnen, dann eine Schülerin nach 6c versetzen | SFG-U: 16 SuS, 30 Std. (DaZ 12 als Doppelstunden). Nach dem Wechsel: SFG-U 15, 6c +1, ihr Plan folgt dem von 6c. | |
| 15 | Blockphase Betriebspraktikum | Pläne 9a–9l vom 22.02. bis 12.03.2027 | kein Unterricht (Wochen 26–28; laufende Wochen ab 31.08.2026, Ferien zählen mit). Frei gewordene Lehrkräfte werden für Vertretungen vorgeschlagen. | |
| 16 | Oberstufe | Kursübersicht EF/Q1/Q2 | EF: 77 GK + 9 VK. Q1: 18 LK + 60 GK + 2 Projektkurse. Q2: 17 LK + 56 GK. LK 5 Std., GK 3, VK/PK 2. | |
| 17 | LK-Schienen | Q1, LK-Schiene A | D-LK1, D-LK3, M-LK2, E-LK1, E-LK3, BI-LK2, GE-LK1, SW-LK2, KU-LK1 gleichzeitig (Schiene B entsprechend) | |
| 18 | Unterrichtsende Q2 | Plan Q2 ab 12.04.2027 | keine Q2-Stunden mehr (fiktiver Termin) | |
| 19 | Ferien und Feiertage | Kalender 2026/27 | 1. Schultag Mi 02.09.2026. Frei: 17.–31.10., 23.12.–06.01., 08.02. (fiktiv), 22.03.–03.04., 06./07.05., 17./18.05., 27./28.05.2027. Sommerferien ab 19.07.2027. 41 Schulwochen. | |
| 20 | Generator unter Last | Gesamtplan erzeugen, Zeit messen | Plan ohne Doppelbelegung von Klassen, Lehrkräften und Räumen. Fehlende Stunden und Konflikte werden im Qualitätsbericht genannt. Laufzeit bitte notieren. | |
| 21 | Live-Vertretung | 3 Lehrkräfte an einem Dienstag krank melden | Ab Jg. 7 entfallen Randstunden bzw. Stunden werden verlegt, Jg. 5/6 werden immer vertreten. Vorschläge bevorzugen Lehrkräfte am selben Standort. | |
| 22 | Lehrkräfte-Abdeckung | Lehrkräfte aus `faecherkombinationen` anlegen (fiktive Kürzel L001–L187), automatisch zuweisen | Jedes Fach ist gedeckt. Bedarf ca. 3169 Std., Kapazität ca. 3861 Std. Deputat 25,5 → ganzzahlig 25/26. | |
| 23 | Versetzung | Schuljahreswechsel auslösen | 7a (U) → 8a am Standort O (Raum und Standort wechseln mit). 10a–10l gehen in die EF, Q2 verlässt die Schule. Die Sprachfördergruppen bleiben bestehen. | |
| 24 | Konfig-Export/Import | Schule exportieren und in eine leere Instanz importieren | gleiche Zahlen wie in Test 1, gleiche Stundentafeln, Gruppen und Standorte | |

## Hinweise zum Import in den Schulmanager

- **Zeitraster und Schuljahr**:
  - `Settings.period_times` = `zeitraster.stunden[].von`
  - `period_minutes` = 45
  - `breaks[].after` = `nach_stunde − 1`
  - `school_year_start` = 2026-08-31 (Woche 1)
  - `site_travel_periods` = 1
- **Rhythmus-Einträge**: Einträge mit `rhythmus {alle_wochen: 2, ab_woche: 1}` bzw. `ab_woche: 2` werden zu `Course.rhythm = {every: 2, from_week: 1, to_week: 0}` bzw. `from_week: 2`.
- **Kopplungen**: Einträge mit `kopplung` werden als gekoppelter Kurs über die genannte Klassengruppe angelegt
  (`Course.classes` = Band bzw. Jahrgang, `Course.parts` = Teilgruppen). Dazu gehören Religion, E-/G-Kurse,
  Wahlpflicht und Förderband.
- **Ganztag**: Die kurzen Tage Mi/Fr werden als `TimeRule(days=[2, 4], periods=[6, 7, 8, 9])` je Sek-I-Klasse
  abgebildet.
- **Blockphasen**: `Absence(kind="class")` für jede Klasse des Jahrgangs und den Zeitraum `von`–`bis`.
- **Lehrkräfte**: aus `faecherkombinationen` mit fiktiven Kürzeln erzeugen. Die Standortbindung laut
  `standortbindung` wird zu `Teacher.sites`.

## Quellen

Der direkte Abruf der NRW-Portale (bass.schule.nrw, schulministerium.nrw, recht.nrw.de) war in der Arbeitsumgebung
**nicht möglich** (DNS-Fehler bzw. Proxy-Sperre). Die Werte stammen aus den **Auszügen der Websuche** zu genau diesen
URLs (Abruf 10.10.2026). Vor einer produktiven Nutzung bitte im Originaldokument prüfen. Das gilt besonders für die
Stundentafel der Gesamtschule: Die Suchauszüge mischten mehrere Fassungen.

| ID | Quelle | Stand | Verwendet für |
|---|---|---|---|
| Q-ST-GE | [APO-S I Anlage 4 – Stundentafel Gesamtschule (VO zur Einführung von Wirtschaft und Informatik, BASS 13-21)](https://bass.schule.nrw/19173.htm) | BASS 2026/27 | Gesamt 188, Kernstunden 179, Ergänzung 9, Rahmen je Jahrgang (5: 28–31, 6: 29–32, 7/8: 30–33, 9/10: 31–34), IF 2 Std. in 5/6, Wirtschaft ≥ 6, Technik/Hauswirtschaft ≥ 4, GL 6/12, WP ab 7 |
| Q-ST-GE-ALT | [APO-S I Anlage 4, ältere Fassung (SGV 223 vom 02.11.2012)](https://recht.nrw.de/system/files/BHA/23878-33005-sgv_223_20121102_1_anlage4.pdf) | 2012 | nur Orientierung für Einzelfachsummen (als Annahme gekennzeichnet) |
| Q-GE-REGELN | [Schulministerium NRW: Schulformspezifische rechtliche Regelungen](https://www.schulministerium.nrw/schulformspezifische-rechtliche-regelungen) | inkl. 6. ÄndVO APO-S I vom 06.06.2024 | E-/G-Differenzierung (M/E ab 7, D ab 8 oder 9, BI/PH/CH ab 9); Wahlpflichtangebote ab 7 |
| Q-GOST | [APO-GOSt NRW (Rechtsportal)](https://recht.nrw.de/system/files/BH/12644-25175.htm) | geltende Fassung | LK 5, GK 3, neu einsetzende FS 4, VK/PK 2; Q-Phase 2 LK + mind. 7 GK; 102 Std. (Ø 34) |
| Q-GOST-ENTWURF | [Entwurf APO-GOSt neu – Synopse](https://www.schulministerium.nrw/system/files/media/document/file/260422_entwurf_apo-gost_neu_vvzapo-gost_neu_synopse.pdf) | Entwurf 22.04.2026 | Hinweis: Die Oberstufenregeln können sich ändern |
| Q-AVO | [Anlage zur VO zu § 93 Abs. 2 SchulG – Relationen, Richtwerte, Bandbreiten](https://bass.schule.nrw/anlagen/20305-1.pdf) | Schuljahr 2026/27 | Gesamtschule 5–10: 18,63 / 27 / 25–29; Sek II: 12,70 |
| Q-VO93 | [VO zu § 93 Abs. 2 SchulG (BASS 11-11 Nr. 1)](https://bass.schule.nrw/6218.htm) | BASS 2026/27, geändert 13.05.2025 | Pflichtstunden Gesamtschule 25,5 |
| Q-ITNRW-KLASSE | [IT.NRW: Schüler/innen je Klasse 2024/25](https://www.it.nrw/nrw-zahl-der-schuelerinnen-und-schueler-je-klasse-steigt-auf-239-127366) | 2025 (Schuljahr 2024/25) | Ø Klassengröße Gesamtschule 27,0 |
| Q-N4T | [News4teachers (berichtet IT.NRW-Werte)](https://www.news4teachers.de/2025/05/dicht-an-dicht-schuelerzahl-pro-klasse-gestiegen-gymnasien-besonders-betroffen/) | Mai 2025 | Schüler je Vollzeitlehrereinheit Gesamtschule 11,4 (Sekundärquelle) |
| Q-ZEIT | [RdErl. Unterrichtsbeginn, Wochenstunden, Pausen (BASS 12-63 Nr. 3)](https://bass.schule.nrw/15325.htm) | RdErl. 05.05.2015 mit Änderungen | Beginn 7.30–8.30 Uhr; Vormittagspausen ≥ 40 Min.; Mittagspause 60 Min. |
| Q-ZUWANDERUNG | [RdErl. Integration und Deutschförderung neu zugewanderter Schüler/innen (BASS 13-63 Nr. 3)](https://bass.schule.nrw/18425.htm) | RdErl. 15.10.2018 | Differenzierungsformen; bis zu 1 Jahr eigene Lerngruppe; Umfang im Zeitrahmen der Stundentafel |
| Q-KAOA | [KAoA-Standardelement Praxiselemente (SBO 6.2.3), Handreichung](https://www.wuppertal.de/microsite/schule-beruf/schuelerinnen/content/schueler-studienorientierung.php.media/302313/09.2019__KH_Praxiselemente.pdf) | 09/2019 | Betriebspraktikum als Standardelement. Dauer und Termin sind Annahmen. |
| Q-FERIEN | [Ferienordnung NRW (BASS 12-65 Nr. 1)](https://bass.schule.nrw/191.htm) | BASS 2026/27 | Ferientermine 2026/27 |
| Q-FERIEN-MSB | [Schulministerium NRW: Ferienordnung bis 2029/30](https://www.schulministerium.nrw/service/ferienordnung-nrw-bis-2029-30) | – | Sommerferien 2027; 3 bewegliche Ferientage 2026/27 |
| Q-FEIERTAGE | [Feiertagsgesetz NRW § 2 (Spiegel)](https://lexmea.de/de/gesetz/feiertg-nrw/2) | – | gesetzliche Feiertage. Ostern 2027 = 28.03. wurde selbst berechnet. |

## Wichtigste Annahmen (vollständig in der JSON)

- **Stundentafel**:
  - Gesamt- und Kernstunden, Ergänzungsstunden und der Rahmen je Jahrgang folgen Anlage 4.
  - Die Aufteilung auf Fächer und Jahrgänge ist geschätzt. Ein Skript hat die Summen geprüft.
- **Schulkonferenz-Entscheidungen** (fiktiv):
  - D-Differenzierung ab 8, Chemie ab 9
  - 2 E- und 2 G-Kurse je Band
  - Wahlpflichtangebot mit 13 Gruppen
  - Kunst/Musik im Wechsel Woche 1/2
  - Islamische Religionslehre als vierte Option
- **Lerngruppen**: Klassen des Gemeinsamen Lernens mit 24 Schüler/innen; Sprachfördergruppen mit je 16 und
  30 bzw. 32 Stunden.
- **Organisation**: Standortaufteilung 5–7 / 8–13, 15 Minuten Wegezeit und Ganztagszeiten sind Annahmen.
- **Oberstufe**: Kursanzahlen, Kursgrößen (ca. 20–26) und Schienen sind Annahmen.
- **Termine** (fiktiv): Betriebspraktikum, Q2-Unterrichtsende und bewegliche Ferientage.
- **Lehrkräfte und Räume** (geschätzt): Fächerkombinationen, Teilzeitquote 30 %, 8 % Anrechnungsstunden,
  Standortbindung und Raumzahlen.
