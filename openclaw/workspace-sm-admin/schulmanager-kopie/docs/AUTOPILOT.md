# Autopilot: laufende Weiterentwicklung (10.10. – 17.10.2026)

Auftrag (10.10.2026): „Bis nächste Woche durcharbeiten lassen und immer mehr optimieren, verbessern, ausbauen.“
Diese Datei ist das Gedächtnis des Autopiloten: Jede Runde liest sie zuerst und ergänzt am Ende das Protokoll.

## Ablauf einer Runde
1. Stand lesen: diese Datei, `docs/OFFENE-PUNKTE.md`, `docs/PRODUKT-BACKLOG.md`, `docs/code/README.md`, `CLAUDE.md`.
2. Laufen noch Agenten/Workflows aus der letzten Runde → nichts Neues starten, auf ihr Ergebnis warten.
3. Ergebnisse der letzten Runde integrieren: `ruff check .`, komplette Testsuite, `npm run lint`, vitest; bei grün
   committen und auf `claude/magical-newton-dcni3v` pushen; `docs/OFFENE-PUNKTE.md` und `docs/code/*` aktuell halten.
4. Nächste Runde starten: die zwei wichtigsten offenen Umsetzungs-Pakete (ohne Dateikonflikte) + ein Design-Paket,
   jedes mit anschließender Prüfung (Fehler suchen, reproduzieren, beheben, Regressionstest) und Browser-Rundgang bei
   Oberflächenänderungen. Reihenfolge: Pflicht-Anforderungen des Auftraggebers (A-xx) → P0 → P1 → P2 → Feinschliff
   (Leistung, Barrierefreiheit, Texte, Design).
5. Protokoll unten ergänzen (Runde, Pakete, Ergebnis, Commit) und dem Auftraggeber 2–4 Zeilen Stand schreiben.

## Regeln
- Nur auf den Branch `claude/magical-newton-dcni3v` pushen, nur mit grünen Tests. Kein Pull Request ohne Auftrag.
- Rückmeldungen aus der Testliste (Artifact „Schulmanager Testliste“) haben Vorrang vor dem Backlog.
- Neue Wünsche des Auftraggebers → `docs/ANFORDERUNGEN.md` (neue ID) und vorne einplanen.
- Höchstens drei Umsetzungs-/Design-Agenten gleichzeitig (Nutzungslimit). Bei Limit: pausieren, nach dem Reset weiter.
- **Kosten**: Gearbeitet wird nur über das Abo des Auftraggebers (kein API-Schlüssel in der Umgebung). Sobald erkennbar
  ist, dass API- oder Extra-Nutzung bezahlt wird (Hinweis auf Extra-Nutzung/Abrechnung, gesetzter `ANTHROPIC_API_KEY`):
  sofort alle Agenten/Workflows stoppen, Weckruf deaktivieren und auf den Auftraggeber warten. Ein Limit-Fehler bedeutet
  nur Pause bis zum Reset – nie über Umwege weiterarbeiten.
- Keine echten personenbezogenen Daten; Datenschutz und Sicherheit vor Funktionsumfang.
- Ende: Samstag, 17.10.2026, 20:00 (Europe/Berlin) – dann Weckruf abschalten und Abschlussbericht schreiben.
- Stopp jederzeit, wenn der Auftraggeber „Stopp“ schreibt.

## Protokoll
| Runde | Datum | Pakete | Ergebnis | Commit |
|---|---|---|---|---|
| 0 | 10.10. | Konten & Anmeldung, Prüfrunde (20 Befunde), Auge-Symbol, Anforderungsliste, CLAUDE.md | Tests grün (483/172) | c66ec82, f523c78 |
| 1 | 10.–11.10. | R1-U1 Stundentafel & Fächer, R1-U2 Kursräume + Elternzugriff (0013), R1-D1 Design-Grundlagen (DESIGN.md, Hilfe, Navigation je Gerät); Prüfrunde (16 Befunde behoben); Code-Doku 04–09 + README, OFFENE-PUNKTE | Tests grün (529/1, vitest 221) | 5ff05e4 + Abschluss |
| 2 | 11.10. | R2-A Vertretungsplan (abwesende Lehrkräfte getrennt, keine „fehlenden Klassen“, Compose/Backup/.env), R2-B Krankmeldungen nur für Berechtigte + API-Token/Export, R2-D Fehlermeldungen + Konto-Cache; Prüfrunde (14 Befunde behoben); Entwurf Kalender & Zeitraster (A-67–A-69) | Tests grün (563/1, vitest 288); zweimal Nutzungslimit (Pause bis Reset) | siehe Log |
| 3 | 11.10. | R3-A1 Wochen 1–53/Wochenangaben/7 Tage (Backend), R3-A2 Oberfläche – gebaut; Prüfung, R3-B (B-07), R3-D (B-12) und Abnahme G1 offen | Tests grün (683/4, vitest 334) | 4f60130 |

**Gestoppt am 11.10.2026, 23:12 (Europe/Berlin) auf Wunsch des Auftraggebers („stop“).** Weckruf deaktiviert, alle Agenten beendet. Offen für die Fortsetzung: Prüfungen R3-A1/R3-A2, Pakete R3-B und R3-D, Abnahme G1 (Workflow-Skript `team-runde-3`, Wiederaufnahme mit gecachten Bau-Ergebnissen möglich).
