---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/DutiesPage.tsx"
stand: 2026-10-12 22:48
generator: schulmanager-regen
---

# Seite DutiesPage

> Frontend · 1 Datei(en) · 335 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Pausenaufsichten: Bereiche, Raster je Tag und Pause, faire automatische Verteilung.

**Route:** `/aufsichten`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/DutiesPage.tsx` | 335 | Pausenaufsichten: Bereiche, Raster je Tag und Pause, faire automatische Verteilung. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| POST | `/data/{…}` | [[Routen features_data]] · `create_item` (`features_data.py:709`) |
| DELETE | `/data/{…}/{…}` | [[Routen features_data]] · `delete_item` (`features_data.py:800`) |
| PUT | `/data/{…}/{…}` | [[Routen features_data]] · `update_item` (`features_data.py:747`) |
| POST | `/duties/generate` | [[Routen features_planning]] · `generate_duties` (`features_planning.py:289`) |

## Backend-Notizen

[[Routen features_data]], [[Routen features_planning]]

## Nutzt (Frontend)

- [[Feature teacher]] – `windows`
- [[Frontend API-Schicht]] – `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `format`, `misc` …
- [[Frontend Komponenten]] – `Abbr`, `Icon`, `Modal`, `SearchSelect`, `WeekNav` …

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
