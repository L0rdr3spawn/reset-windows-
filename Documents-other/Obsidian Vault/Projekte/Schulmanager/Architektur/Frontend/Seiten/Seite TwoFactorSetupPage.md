---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/TwoFactorSetupPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite TwoFactorSetupPage

> Frontend · 1 Datei(en) · 33 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Pflichtseite, wenn die Rolle laut `SM_REQUIRE_2FA_ROLES` Zwei-Faktor-Anmeldung braucht.

**Route:** `/zwei-faktor`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/TwoFactorSetupPage.tsx` | 33 | Pflichtseite, wenn die Rolle laut SM_REQUIRE_2FA_ROLES Zwei-Faktor-Anmeldung braucht. |

## API-Aufrufe

Diese Einheit ruft selbst keine Endpunkte auf.

## Nutzt (Frontend)

- [[Frontend Basis]] – `AuthContext`, `misc`, `permissions`
- [[Frontend Komponenten]] – `ui`
- [[Seite ProfilePage]] – `ProfilePage`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
