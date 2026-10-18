---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/elternzugriff/"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Feature elternzugriff

> Frontend · 1 Datei(en) · 133 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Baustein (kein eigenes Modul): Abschnitt, in dem volljährige Schüler/innen festlegen, welche Bereiche ihre Eltern sehen.

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/elternzugriff/ParentAccessSection.tsx` | 133 | Profil-Abschnitt „Was dürfen meine Eltern sehen?“ (A-44) – nur für Schüler/innen. Volljährige legen je Bereich fest, was verknüpf… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/parent-access` | [[Routen features_parent_access]] · `get_parent_access` (`features_parent_access.py:70`) |
| PUT | `/parent-access` | [[Routen features_parent_access]] · `put_parent_access` (`features_parent_access.py:76`) |

## Backend-Notizen

[[Routen features_parent_access]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `useApi`
- [[Frontend Komponenten]] – `Help`, `Icon`, `ui`

## Wird genutzt von

- [[Frontend Komponenten]]
- [[Seite ProfilePage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
