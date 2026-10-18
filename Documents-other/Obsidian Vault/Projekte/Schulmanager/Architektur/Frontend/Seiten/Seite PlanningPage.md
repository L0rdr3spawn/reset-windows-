---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/PlanningPage.tsx, pages/planning/*"
stand: 2026-10-12 22:54
generator: schulmanager-regen
---

# Seite PlanningPage

> Frontend · 13 Datei(en) · 3307 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Planungs-Werkstatt mit Reitern: Stundentafeln, Kurse, Generator (Job-Fortschritt, Entwurf übernehmen), Auto-Planer, Zeitraster & Schuljahr, Einstellungen und Qualitätsbericht. Die Reiter liegen in `pages/planning/`.

**Route:** `/planung`, `/planung/:tab`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/PlanningPage.tsx` | 61 | Planungs-Werkstatt mit Reitern: Stundentafeln, Kurse, Generator (Job-Fortschritt, Entwurf übernehmen), Auto-Planer, Zeitraster &… |
| `frontend/src/pages/planning/AutoPlanCard.tsx` | 163 |  |
| `frontend/src/pages/planning/CalendarPanel.tsx` | 354 | Planung › „Zeitraster & Schuljahr“ (R3, Entwurf §8, §15.2 V4, Texte §15.5): Schule, Schuljahr und Wochenzählung, Unterrichtstage… |
| `frontend/src/pages/planning/CoursesEditor.tsx` | 344 |  |
| `frontend/src/pages/planning/CurriculaEditor.tsx` | 507 |  |
| `frontend/src/pages/planning/GeneratorPanel.tsx` | 323 |  |
| `frontend/src/pages/planning/HolidayImportPanel.tsx` | 167 | Planung › „Zeitraster & Schuljahr“: Ferien und Feiertage automatisch aus einer öffentlichen API übernehmen (Land + Bundesland, Au… |
| `frontend/src/pages/planning/NewSubjectDialog.tsx` | 86 |  |
| `frontend/src/pages/planning/RebuildCourses.tsx` | 168 |  |
| `frontend/src/pages/planning/ReportTiles.tsx` | 325 |  |
| `frontend/src/pages/planning/SettingsPanels.tsx` | 640 |  |
| `frontend/src/pages/planning/curricula.ts` | 83 | Zuordnung Stundentafel → Klasse (gleiche Regel wie `schulmanager/planning.py::resolve_curricula`): eine Tafel, die die Klasse unt… |
| `frontend/src/pages/planning/holidayImport.ts` | 86 | Ferien & Feiertage aus öffentlicher API (`/holiday-import`, Recht `masterdata.edit`) – Endpunkte und reine Hilfen. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| POST | `/data/{…}` | [[Routen features_data]] · `create_item` (`features_data.py:709`) |
| DELETE | `/data/{…}/{…}` | [[Routen features_data]] · `delete_item` (`features_data.py:800`) |
| PUT | `/data/{…}/{…}` | [[Routen features_data]] · `update_item` (`features_data.py:747`) |
| PUT | `/settings` | [[Routen features_data]] · `put_settings` (`features_data.py:997`) |
| POST | `/settings/calendar-preview` | [[Routen features_data]] · `calendar_preview` (`features_data.py:1037`) |
| GET | `/holiday-import` | [[Routen features_holiday_import]] · `get_state` (`features_holiday_import.py:63`) |
| PUT | `/holiday-import` | [[Routen features_holiday_import]] · `put_settings` (`features_holiday_import.py:68`) |
| POST | `/holiday-import/apply` | [[Routen features_holiday_import]] · `apply` (`features_holiday_import.py:100`) |
| GET | `/holiday-import/countries` | [[Routen features_holiday_import]] · `list_countries` (`features_holiday_import.py:81`) |
| POST | `/holiday-import/preview` | [[Routen features_holiday_import]] · `preview` (`features_holiday_import.py:94`) |
| GET | `/holiday-import/regions` | [[Routen features_holiday_import]] · `list_regions` (`features_holiday_import.py:87`) |
| POST | `/planning/assign-teachers` | [[Routen features_planning]] · `assign_teachers` (`features_planning.py:105`) |
| GET | `/planning/autoplan` | [[Routen features_planning]] · `autoplan_status` (`features_planning.py:226`) |
| POST | `/planning/autoplan/run` | [[Routen features_planning]] · `autoplan_run` (`features_planning.py:233`) |
| POST | `/planning/courses-from-curricula` | [[Routen features_planning]] · `courses_from_curricula` (`features_planning.py:69`) |
| POST | `/planning/generate` | [[Routen features_planning]] · `generate` (`features_planning.py:164`) |
| GET | `/planning/jobs/{…}` | [[Routen features_planning]] · `get_job` (`features_planning.py:250`) |
| POST | `/planning/jobs/{…}/apply` | [[Routen features_planning]] · `apply_job` (`features_planning.py:279`) |
| POST | `/planning/jobs/{…}/cancel` | [[Routen features_planning]] · `cancel_job` (`features_planning.py:264`) |
| GET | `/planning/report` | [[Routen features_planning]] · `report` (`features_planning.py:119`) |
| GET | `/planning/report/details` | [[Routen features_planning]] · `report_details` (`features_planning.py:141`) |

## Backend-Notizen

[[Routen features_data]], [[Routen features_holiday_import]], [[Routen features_planning]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`, `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `format`, `misc` …
- [[Frontend Komponenten]] – `Abbr`, `ConfirmChanges`, `Help`, `HelpTip`, `Icon` …

## Wird genutzt von

- [[Frontend App und Routing]]
- [[Seite DashboardPage]]
- [[Seite MasterDataPage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
