---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/LicensePage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite LicensePage

> Frontend · 1 Datei(en) · 162 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Lizenz der Schule: Stand, Laufzeit, Grenzen, letzte Online-Bestätigung; neue Lizenzdatei einspielen und jetzt prüfen.

**Route:** `/lizenz`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/LicensePage.tsx` | 162 | `/lizenz` – Lizenz der Schule (nur Administration): Stand, Laufzeit, Grenzen, letzte Online-Bestätigung beim Anbieter; neue Lizen… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/license` | [[Routen license]] · `get_license` (`license.py:25`) |
| PUT | `/license` | [[Routen license]] · `put_license` (`license.py:35`) |
| POST | `/license/check` | [[Routen license]] · `check_license` (`license.py:49`) |

## Backend-Notizen

[[Routen license]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`
- [[Frontend Basis]] – `ToastContext`, `dates`, `misc`, `useApi`
- [[Frontend Komponenten]] – `HelpTip`, `Icon`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
