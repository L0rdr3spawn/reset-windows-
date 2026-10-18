---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/SetupPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite SetupPage

> Frontend · 1 Datei(en) · 199 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Einrichtungs-Assistent für eine neue Schule: Lizenz → Schuldaten → Stammdaten (auch per Import) → Schüler → Unterricht → Stundenplan → Konten und Rollen.

**Route:** `/einrichtung`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/SetupPage.tsx` | 199 | `/einrichtung` – Einrichtungs-Assistent für eine neue Schule: Schritt für Schritt von der Lizenz über Schuldaten, Stammdaten (auc… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| PUT | `/settings` | [[Routen features_data]] · `put_settings` (`features_data.py:997`) |
| GET | `/setup/status` | [[Routen setup]] · `setup_status` (`setup.py:17`) |

## Backend-Notizen

[[Routen features_data]], [[Routen setup]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`
- [[Frontend Basis]] – `ToastContext`, `misc`, `useApi`
- [[Frontend Komponenten]] – `HelpTip`, `Icon`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
