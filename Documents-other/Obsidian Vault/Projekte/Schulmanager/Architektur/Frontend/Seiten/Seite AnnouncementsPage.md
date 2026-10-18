---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/AnnouncementsPage.tsx"
stand: 2026-10-12 22:56
generator: schulmanager-regen
---

# Seite AnnouncementsPage

> Frontend · 1 Datei(en) · 275 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Mitteilungen an Gruppen schreiben und verwalten (im Menü inzwischen als Postfach-Ordner geführt).

**Route:** `/mitteilungen`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/AnnouncementsPage.tsx` | 275 | Mitteilungen an Gruppen schreiben und verwalten (im Menü inzwischen als Postfach-Ordner geführt). |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/announcements` | [[Routen features_announcements]] · `list_announcements` (`features_announcements.py:194`) |
| POST | `/announcements` | [[Routen features_announcements]] · `create_announcement` (`features_announcements.py:208`) |
| DELETE | `/announcements/{…}` | [[Routen features_announcements]] · `delete_announcement` (`features_announcements.py:244`) |
| PUT | `/announcements/{…}` | [[Routen features_announcements]] · `update_announcement` (`features_announcements.py:226`) |

## Backend-Notizen

[[Routen features_announcements]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `format`, `permissions` …
- [[Frontend Komponenten]] – `Icon`, `Modal`, `SearchSelect`, `ui`

## Wird genutzt von

- [[Feature nachrichten]]
- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
