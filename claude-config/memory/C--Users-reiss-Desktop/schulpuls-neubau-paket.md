---
name: schulpuls-neubau-paket
description: "Fertiges Spezifikationspaket für den Schulpuls-Neubau ohne Altcode (Master-Prompt + 16 Hauptdateien + Anhang), Orte und Struktur"
metadata:
  node_type: memory
  type: project
  originSessionId: 6b3b3b78-3724-4c16-8183-7144a0471201
  modified: 2026-10-18T14:42:03.186Z
---

Am 2026-10-18 wurde für das Experiment "Neubau mit 0 % Altcode vergleichen" ein Spezifikationspaket erstellt (aus allen echten Gesprächstexten, Ist-Zustands-Lesung des Codes, Rechts-/Sicherheitsrecherchen).

**Orte:** `C:\Users\reiss\Desktop\Schulpuls-Neubau-Paket\` (+ `.zip` daneben) und intern `C:\Users\reiss\Documents\claude\schulpuls-atlas\doku\intern\NEUBAU-PAKET\` (nie ausliefern). Einstieg: `paket\00_MASTER_PROMPT.md`; Fragen an den Nutzer: `paket\ENTSCHEIDUNGEN_FUER_DEN_BETREIBER.md` (E-S1 + E-01…E-40 in `10_ROADMAP_OFFENE_PUNKTE.md` §2).

**Struktur:** Hauptdateien 01–11 (Kennungen STP VER KLB NOT KUR NAC FOR STA LEH SCH REC ANM SIC DAT BEN INT BET OBE REH QUA PRI; Datenmodell = DAM, Datenschutz-Prozesse in 06 = DSG, offene Punkte in 10 = 9xx). Rund 2.000 Anforderungen mit je einer Abnahme-Zeile. `anhang\` = Rohnotizen (Z1–Z9 Werte/Tabellen, I1–I15 Ist-Zustand, W1–W8, G1–G6). Prüfskript `pruefe_paket.py` (Kennungen, Verweise, Marker) liegt beim Paket.

**Why:** Der Nutzer will sehen, ob ein komplett neu geschriebenes Programm besser wird; Messlatte sind dieselben Abnahme-Zeilen (09 Vergleichs-Experiment).

**How to apply:** Wenn der Nutzer nach dem Neubau/Vergleich fragt, zuerst dort nachsehen. Nicht erneut alles neu lesen. Siehe [[schulpuls-atlas]] und [[plan-max5x-limits]] (Agenten in Wellen, nie große Agenten wieder aufnehmen).
