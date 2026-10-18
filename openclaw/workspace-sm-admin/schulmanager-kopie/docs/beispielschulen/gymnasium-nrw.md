# Beispielschule `gymnasium-nrw` – Gymnasium Sonnenhügel Musterhausen (fiktiv)

> **Fiktiv.** Schule, Ort und Standort sind erfunden. Die Datei enthält **keine personenbezogenen Daten**:
> keine Namen, Kürzel, Fotos oder Stundenpläne realer Schüler/innen oder Lehrkräfte und keine Klassenlisten realer
> Schulen. Lehrkräfte sind nur als Anzahl und Fächerkombination angegeben. Verwendet wurden nur amtliche bzw.
> allgemeine Rahmendaten (APO-S I, APO-GOSt, VO zu § 93 Abs. 2 SchulG, Ferienordnung, Feiertagsgesetz, aggregierte
> Schulstatistik). Was nicht belegt ist, steht in der JSON als `annahme` bzw. in `annahmen[]`.

Daten: [`gymnasium-nrw.json`](gymnasium-nrw.json) · Schuljahr 2026/27 · Stand 10.10.2026

## Kurzbeschreibung

Ein vierzügiges **G9-Gymnasium** mit **1000 Schüler/innen** an **einem Standort**. Die Schule hat zwei Zweige in der
Sekundarstufe I und eine gymnasiale Oberstufe mit Kurssystem:

| Bildungsgang | Klassen | Form / Rhythmus | Std./Woche |
|---|---|---|---|
| `sek1-g9` – Sekundarstufe I (G9) | 5a–c … 10a–c (18 Klassen) | wöchentlich; 2. Fremdsprache ab Kl. 7, Wahlpflicht II ab Kl. 9 | 30 / 30 / 31 / 31 / 32 / 32 |
| `sek1-g9-bili` – bilingualer Zweig Englisch | 5d … 10d (6 Klassen) | wöchentlich; Geschichte/Erdkunde bilingual über Ergänzungsstunden | 30 / 30 / 31 / 32 / 32 / 32 |
| `gost` – gymnasiale Oberstufe | EF-1–5, Q1-1–5, Q2-1–4 (14 Tutorgruppen) | Kurssystem (LK 5, GK 3, Spanisch neu 4, Vertiefungs-/Projektkurs 2); Blockphasen | Ø 34 |

Zahlen: **38 Klassen bzw. Tutorgruppen, 1000 Schüler/innen** (Sek I 650, Oberstufe 350: EF 130, Q1 116, Q2 104),
**31 Fächer**, **29 Klassengruppen**, **70 Lehrkräfte** (ca. 61,6 Vollzeitstellen, Deputat 25,5), **61 Räume**
(24 Klassenräume, 18 Kursräume, 19 Fachräume einschließlich 4 Hallenteilen). Zeitraster: Beginn 07:50, 45 Minuten,
5 Minuten Wechselzeit, 10 Stunden pro Tag, Pausen 20 / 20 / 60 Minuten.

Die Q2 ist 2026/27 der **erste G9-Abiturjahrgang** (2026 gab es an den meisten Gymnasien kein reguläres Abitur).

## Wofür sich die Schule zum Testen eignet

- **Zwei Bildungsgänge im selben Jahrgang** (A-38): 8a und 8d haben unterschiedliche Stundentafeln (8d: Erdkunde
  bilingual 3 Std. statt Erdkunde 2 Std.).
- **Stundentafel je Jahrgang** mit Doppelstunden-Wunsch und Ergänzungsstunden (A-04, A-35, A-30).
- **Klassengruppen** (A-43): Jahrgänge, Regelzweig, Religionsbänder, bilingualer Zweig, Erprobungsstufe,
  Oberstufen-Jahrgangsstufen. Eine Klasse ist in mehreren Gruppen.
- **Kopplungen**:
  - Religion/Praktische Philosophie: je 2 Klassen bilden 3 Gruppen.
  - 2. Fremdsprache ab Kl. 7: Französisch und Latein für alle 4 Klassen gleichzeitig.
  - Wahlpflicht II ab Kl. 9: 5 Gruppen gleichzeitig.
  - Förderband: 4 Gruppen für die 3 Regelklassen.
- **Oberstufe mit Kurssystem**: Leistungskurs- und Grundkurs-Schienen, neu einsetzende Fremdsprache mit 4 Stunden,
  Vertiefungs- und Projektkurse.
- **Blockphasen in einem sonst wöchentlichen Plan**:
  - Betriebspraktikum der EF (2 Wochen)
  - Unterrichtsende der Q2 vor dem Abitur
  - In beiden Fällen werden Lehrkräfte frei und stehen für Vertretung zur Verfügung.
- **Vertretung nach Altersstufe** (A-05): Die Erprobungsstufe (Kl. 5/6) wird immer vertreten. Ab Kl. 7 darf eine
  Randstunde entfallen.
- **Fachräume mit realistischer Auslastung** (ca. 30–65 %), dazu eine Aula/Bühne als seltener Spezialraum.
- **Kalender 2026/27 NRW**: echte Ferien und Feiertage, 3 bewegliche Ferientage (fiktiv gewählt), 41 Schulwochen.

## Testliste – bitte ausfüllen und zurückgeben

Bitte die letzte Spalte ausfüllen: **OK**, oder was stattdessen passiert ist und **wie es sein soll**. Die Tabelle
kann so, wie sie ist, zurückkommen.

| Nr. | Was testen | Wie | Erwartet (Soll) | Ihre Rückmeldung (Ist / wie es sein soll) |
|---|---|---|---|---|
| 1 | Struktur importieren | Bildungsgänge, Klassen, Gruppen, Fächer und Standort aus der JSON übernehmen | 3 Bildungsgänge, 38 Klassen/Tutorgruppen, 29 Gruppen, 31 Fächer, 1000 Schüler/innen, 1 Standort | |
| 2 | Stundentafel Kl. 5 | Stundentafel von 5a öffnen | 30 Std.: D 5, M 4, E 5, EK 2, PW 1, BI 2, PH 1, IF 1, KU 2, MU 2, Religion/PP 2, SP 3 | |
| 3 | Zweiter Bildungsgang im selben Jahrgang | 8a und 8d vergleichen | 8a: 31 Std. mit EK 2. 8d: 32 Std. mit Erdkunde bilingual (EKB) 3 statt EK 2. | |
| 4 | Klassengruppen | Gruppen „Bilingualer Zweig“ und „Erprobungsstufe“ öffnen | BILI = 5d–10d (6 Klassen). ERPROBUNG = 5a–6d (8 Klassen). 5d ist in BILI, JG5, REL5cd und ERPROBUNG. | |
| 5 | Religion parallel | Plan von 5a und 5b | ER, KR und PP liegen in derselben Stunde (3 Gruppen, 2 Std./Woche) | |
| 6 | 2. Fremdsprache als Jahrgangsband | Plan von 7a–7d | Französisch (3 Gruppen) und Latein (2 Gruppen) laufen gleichzeitig, 4 Std. in Kl. 7 | |
| 7 | Wahlpflicht II | Plan von 9a–9d | 5 Gruppen gleichzeitig (Spanisch, Informatik ×2, Biologie-Chemie, Darstellendes Spiel), 3 Std.; DS in der Aula, IF in Informatikräumen | |
| 8 | Förderband | Plan von 6a–6c und 6d | 6a–6c: 1 Std. Förderband (4 Gruppen gleichzeitig). 6d hat kein Förderband, dafür 1 Std. Englisch mehr (bilingual). | |
| 9 | Zeitraster | Einstellungen → Zeitraster | Beginn 07:50, 45 Min., 5 Min. Wechsel. Pausen nach der 2. und 4. Stunde (je 20 Min.), Mittagspause nach der 6. (60 Min.). 7. Std. 14:15–15:00, 10. Std. 16:45–17:30. | |
| 10 | Doppelstunden | Sport in Kl. 5 (3 Std., Doppelstunde gewünscht) | eine Doppel- und eine Einzelstunde. Die Doppelstunde liegt nie über einer Pause (z. B. nie 2.+3. Stunde). | |
| 11 | Max. Stunden pro Tag | Pläne aller Klassen | Sek I höchstens 8 Stunden am Tag, Oberstufe höchstens 10 | |
| 12 | LK-Schienen | Kurse der Q1 | LK-Schiene A (D, M, E, BI, GE, PH) und LK-Schiene B (D, M, E, BI, SW, KU), je 5 Std. Alle Kurse einer Schiene liegen gleichzeitig. | |
| 13 | Kursanzahl Oberstufe | Kursübersicht EF/Q1/Q2 | EF: 51 GK + 4 Vertiefungskurse. Q1: 12 LK + 36 GK + 1 Projektkurs. Q2: 11 LK + 32 GK. Spanisch-GK 4 Std. | |
| 14 | Ferien und Feiertage | Kalender 2026/27 | 1. Schultag Mi 02.09.2026. Frei: 17.–31.10., 23.12.–06.01., 08.02. (fiktiv), 22.03.–03.04., 06./07.05., 17./18.05., 27./28.05.2027. Sommerferien ab 19.07.2027. | |
| 15 | Blockphase EF | Plan EF-1 bis EF-5, 18.–29.01.2027 | kein Unterricht (Betriebspraktikum, Wochen 21–22; laufende Wochen ab 31.08.2026, Ferien zählen mit). Die EF-Kurslehrkräfte erscheinen als frei bzw. vertretungsbereit. | |
| 16 | Unterrichtsende Q2 | Plan Q2 ab 12.04.2027 | keine Q2-Stunden mehr (fiktiver Termin). Frei gewordene Lehrkräfte werden für Vertretungen vorgeschlagen. | |
| 17 | Vertretung nach Altersstufe | Lehrkraft mit Randstunde in 6a und 8a krank melden | 6a: Vertretung oder Betreuung, kein Entfall. 8a: Randstunde darf entfallen. | |
| 18 | Fachräume | Stundenplan generieren und Raumbelegung prüfen | BI/CH/PH nur in passenden Fachräumen, Sport nur in den 4 Hallenteilen. Auslastung etwa 30–65 % (Aula ca. 13 %), kein Raum doppelt belegt. | |
| 19 | Lehrkräfte-Abdeckung | Lehrkräfte aus `faecherkombinationen` anlegen (fiktive Kürzel L001–L070), automatisch zuweisen | Jedes Fach ist gedeckt. Bedarf ca. 1279 Std., Kapazität ca. 1445 Std. Deputat 25,5 → ganzzahlig 25/26. | |
| 20 | Klassenfrequenz | Validierung/Hinweise | Alle Sek-I-Klassen haben 26–28 Schüler/innen (Bandbreite 25–29) → keine Warnung | |
| 21 | Versetzung | Schuljahreswechsel auslösen | 5a → 6a … 9a → 10a. 10a–10d gehen in die EF, Q2 verlässt die Schule. d-Klassen bleiben im bilingualen Zweig. | |
| 22 | Konfig-Export/Import | Schule exportieren und in eine leere Instanz importieren | gleiche Zahlen wie in Test 1, gleiche Stundentafeln und Gruppen | |

## Hinweise zum Import in den Schulmanager

- **Zeitraster**:
  - `Settings.period_times` = `zeitraster.stunden[].von`
  - `Settings.period_minutes` = 45
  - `Settings.breaks[].after` = `nach_stunde − 1` (im Modell 0-basiert)
  - `school_year_start` = 2026-08-31
- **Fächer**: `fachraum` → `Subject.room_type`. Kopplungseinträge der Stundentafel (`ER/KR/PP`, `F/L`, `WP`, `FÖ`)
  werden als **Kurs mit mehreren Teilen** (`Course.parts`) über die genannte Klassengruppe angelegt, nicht als
  einfacher Stundentafel-Eintrag.
- **Oberstufe**: Jede Schiene wird ein gekoppelter Kurs über alle Tutorgruppen der Stufe. Die Vertiefungs- und
  Projektkurse bekommen eine eigene 2-stündige Schiene.
- **Blockphasen**: `Absence(kind="class")` für jede betroffene Klasse und den Zeitraum `von`–`bis`.
- **Lehrkräfte**: aus `faecherkombinationen` mit fiktiven Kürzeln erzeugen. Etwa 30 % Teilzeit (Annahme).
- **Ferien**: Einträge aus `ferien_feiertage_2026_27` werden zu `Holiday`.

## Quellen

Der direkte Abruf der NRW-Portale (bass.schule.nrw, schulministerium.nrw, recht.nrw.de) war in der Arbeitsumgebung
**nicht möglich** (DNS-Fehler bzw. Proxy-Sperre). Die Werte stammen aus den **Auszügen der Websuche** zu genau diesen
URLs (Abruf 10.10.2026). Vor einer produktiven Nutzung bitte im Originaldokument prüfen.

| ID | Quelle | Stand | Verwendet für |
|---|---|---|---|
| Q-ST-GY | [APO-S I Anlage 3a – Stundentafel Gymnasium G9 (ab 01.08.2021)](https://www.schulministerium.nrw/system/files/media/document/file/Stundentafel_SI_G9_Anlage_3a_ab_210801_neu_ab_Klasse5.pdf) | Fassung ab 01.08.2021 | Lernbereichssummen, Kernstunden 59/123/182, Gesamt 182–188, Rahmen 28–30 / 30–33, Informatik 2 Std. in 5/6, Mindeststunden je Fach |
| Q-GOST | [APO-GOSt NRW (Rechtsportal)](https://recht.nrw.de/system/files/BH/12644-25175.htm) | geltende Fassung | LK 5, GK 3, neu einsetzende FS 4, VK/PK 2; EF nur GK; Q-Phase 2 LK + mind. 7 GK; 102 Std. (Ø 34) |
| Q-GOST-ENTWURF | [Entwurf APO-GOSt neu – Synopse](https://www.schulministerium.nrw/system/files/media/document/file/260422_entwurf_apo-gost_neu_vvzapo-gost_neu_synopse.pdf) | Entwurf 22.04.2026 | Hinweis: Die Oberstufenregeln können sich ändern |
| Q-G9-ABI | [Land NRW: Pressemitteilung zum Abitur 2026 nach Rückkehr zu G9](https://www.land.nrw/pressemitteilung/nach-rueckkehr-von-g8-zu-g9-nordrhein-westfalen-bestehen-rund-27000-schuelerinnen) | 2026 | erster G9-Abiturjahrgang 2027 |
| Q-AVO | [Anlage zur VO zu § 93 Abs. 2 SchulG – Relationen, Richtwerte, Bandbreiten](https://bass.schule.nrw/anlagen/20305-1.pdf) | Schuljahr 2026/27 | Gymnasium 5–10: 19,87 / 27 / 25–29; Sek II: 12,70 |
| Q-VO93 | [VO zu § 93 Abs. 2 SchulG (BASS 11-11 Nr. 1)](https://bass.schule.nrw/6218.htm) | BASS 2026/27, geändert 13.05.2025 | Pflichtstunden Gymnasium 25,5 |
| Q-ITNRW-KLASSE | [IT.NRW: Schüler/innen je Klasse 2024/25](https://www.it.nrw/nrw-zahl-der-schuelerinnen-und-schueler-je-klasse-steigt-auf-239-127366) | 2025 (Schuljahr 2024/25) | Ø Klassengröße Gymnasium 27,1 |
| Q-N4T | [News4teachers (berichtet IT.NRW-Werte)](https://www.news4teachers.de/2025/05/dicht-an-dicht-schuelerzahl-pro-klasse-gestiegen-gymnasien-besonders-betroffen/) | Mai 2025 | Schüler je Vollzeitlehrereinheit Gymnasium 14,5 (Sekundärquelle) |
| Q-ZEIT | [RdErl. Unterrichtsbeginn, Wochenstunden, Pausen (BASS 12-63 Nr. 3)](https://bass.schule.nrw/15325.htm) | RdErl. 05.05.2015 mit Änderungen | Beginn 7.30–8.30 Uhr; Vormittagspausen ≥ 40 Min.; Mittagspause 60 Min. (Sek I) |
| Q-FERIEN | [Ferienordnung NRW (BASS 12-65 Nr. 1)](https://bass.schule.nrw/191.htm) | BASS 2026/27 | Ferientermine 2026/27 |
| Q-FERIEN-MSB | [Schulministerium NRW: Ferienordnung bis 2029/30](https://www.schulministerium.nrw/service/ferienordnung-nrw-bis-2029-30) | – | Sommerferien 2027; 3 bewegliche Ferientage 2026/27 |
| Q-FEIERTAGE | [Feiertagsgesetz NRW § 2 (Spiegel)](https://lexmea.de/de/gesetz/feiertg-nrw/2) | – | gesetzliche Feiertage. Ostern 2027 = 28.03. wurde selbst berechnet. |
| Q-KAOA | [KAoA-Standardelement Praxiselemente (SBO 6.2.3), Handreichung](https://www.wuppertal.de/microsite/schule-beruf/schuelerinnen/content/schueler-studienorientierung.php.media/302313/09.2019__KH_Praxiselemente.pdf) | 09/2019 | Betriebspraktikum als Standardelement. Dauer und Termin sind Annahmen. |

## Wichtigste Annahmen (vollständig in der JSON)

- **Stundentafel**:
  - Die Lernbereichssummen und der Rahmen aus Anlage 3a sind eingehalten.
  - Die Verteilung auf einzelne Jahrgänge und Fächer ist geschätzt. Ein Skript hat die Summen geprüft.
- **Schulspezifische Angebote** (alles Annahmen):
  - bilingualer Zweig
  - Wahlpflichtangebot
  - 2. Fremdsprache Französisch/Latein
  - Förderband
- **Oberstufe**: Kursanzahlen, Kursgrößen (ca. 19–26) und Schienen sind plausible Annahmen.
- **Termine** (fiktiv):
  - Zeitraster
  - bewegliche Ferientage
  - Praktikumszeitraum
  - Q2-Unterrichtsende
- **Lehrkräfte und Räume**: Fächerkombinationen, Teilzeitquote 30 %, 8 % Anrechnungsstunden und die Raumzahlen
  sind geschätzt.
