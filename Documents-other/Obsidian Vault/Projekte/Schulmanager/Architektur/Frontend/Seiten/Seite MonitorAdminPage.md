---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/MonitorAdminPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite MonitorAdminPage

> Frontend · 1 Datei(en) · 148 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Vertretungsmonitore einstellen: Tage, Überschrift, Laufband, Hinweise (mit Ablaufdatum) je Standort.

**Route:** `/monitore`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/MonitorAdminPage.tsx` | 148 | `/monitore` – Vertretungsmonitore einstellen (Recht `monitor.manage`: Admin, Schulleitung, Sekretariat): je Standort bzw. „Alle S… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/monitor/config` | [[Routen features_substitutions]] · `monitor_config_list` (`features_substitutions.py:603`) |
| PUT | `/monitor/config/{…}` | [[Routen features_substitutions]] · `monitor_config_save` (`features_substitutions.py:612`) |

## Backend-Notizen

[[Routen features_substitutions]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `endpoints`, `types`
- [[Frontend Basis]] – `ToastContext`, `misc`, `useApi`
- [[Frontend Komponenten]] – `HelpTip`, `Icon`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
