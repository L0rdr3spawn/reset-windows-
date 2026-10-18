---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/MasterDataPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite MasterDataPage

> Frontend · 1 Datei(en) · 846 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Generisches CRUD für alle Sammlungen des Planungsdokuments (Standorte, Fächer, Lehrkräfte, Räume, Klassen, Schüler, Ferien …) mit Sperrregeln-Editor und CSV-Anbindung.

**Route:** `/stammdaten`, `/stammdaten/:tab`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/MasterDataPage.tsx` | 846 | Generisches CRUD für alle Sammlungen des Planungsdokuments (Standorte, Fächer, Lehrkräfte, Räume, Klassen, Schüler, Ferien …) mit… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| PUT | `/classes/{…}/curriculum` | [[Routen features_classes]] · `put_class_curriculum` (`features_classes.py:516`) |
| POST | `/data/{…}` | [[Routen features_data]] · `create_item` (`features_data.py:709`) |
| DELETE | `/data/{…}/{…}` | [[Routen features_data]] · `delete_item` (`features_data.py:800`) |
| PUT | `/data/{…}/{…}` | [[Routen features_data]] · `update_item` (`features_data.py:747`) |

## Backend-Notizen

[[Routen features_classes]], [[Routen features_data]]

## Nutzt (Frontend)

- [[Feature classes]] – `ClassCurriculumSection`, `api`, `types`
- [[Feature students]] – `BirthDateEditor`, `StudentDetail`, `SupportCatalogDialog`, `supportApi`
- [[Feature teacher]] – `TeacherFields`, `windows`
- [[Frontend API-Schicht]] – `client`, `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `colors`, `dates`, `format` …
- [[Frontend Komponenten]] – `Abbr`, `ClassPlanningFields`, `ConfirmChanges`, `Icon`, `Modal` …
- [[Seite PlanningPage]] – `curricula`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
