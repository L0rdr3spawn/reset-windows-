---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/students/"
stand: 2026-10-12 22:43
generator: schulmanager-regen
---

# Feature students

> Frontend · 24 Datei(en) · 3435 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Schüler-Selbstbedienung und Akten: Atteste & Dokumente, Fehlzeiten-Akte (`/fehlzeiten/:studentId`), Noten (`/noten`), Förderinformationen.

## Routen des Moduls (`module.tsx`)

| Pfad | Seite | Rechte/Rollen | Titel |
|---|---|---|---|
| `/meine-uebersicht` | `Navigateto=""replace` | – | Start |
| `/dokumente` | `DocumentsPage` | anyOf: ['student_documents.read'] | Atteste & Dokumente |
| `/fehlzeiten/:studentId` | `RecordPage` | anyOf: ['student_absence.read'] | Fehlzeiten |
| `/noten` | `GradesPage` | roles: ['schueler', 'eltern'] | Meine Noten |

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/students/AbsenceActions.tsx` | 222 | Aktionen an einer Meldung (Familie, volljährige Schüler/innen): zurücknehmen, „Ich komme früher zurück“ (verkürzen), verlängern,… |
| `frontend/src/features/students/AbsenceHistory.tsx` | 48 | Meldungsprotokoll der Fehlzeiten: „krank gemeldet am … von … (Kanal)“ und der Verlauf (nur anhängend). Die volle Sicht (Klassenle… |
| `frontend/src/features/students/AbsenceStats.tsx` | 389 | Fehlzeiten-Übersicht mit Anteilen: wie viele Unterrichtsstunden gab es, wie viele davon gefehlt (Anzahl, Prozent), je Fach mit Am… |
| `frontend/src/features/students/BirthDateEditor.tsx` | 56 | Geburtsdatum einer Schülerin/eines Schülers setzen (Recht „Geburtsdatum pflegen“, `PUT /students/{id}/birth-date`). Daraus folgt… |
| `frontend/src/features/students/DocumentsPage.tsx` | 211 | „Atteste & Dokumente“ (`/dokumente`) für Sekretariat, Schulleitung und Klassenleitungen: Prüf-Eingang (geprüft/abgelehnt mit Verm… |
| `frontend/src/features/students/ExamHints.tsx` | 29 | Hinweis bei Klausuren/Tests: Schüler/innen mit Nachteilsausgleich (nur Art, Minuten, Fächer, Hilfsmittel). |
| `frontend/src/features/students/FamilyAbsences.tsx` | 176 | Krankmeldungen für Schüler/innen und Eltern (je Kind) – Teil der Seite `/krankmeldungen`. Karten sauber untereinander, jedes Elem… |
| `frontend/src/features/students/FamilyHome.tsx` | 202 | Startseiten-Bereich für Schüler/innen und Eltern (je Kind): Wochenplan (Kalenderwoche), Hinweis auf fehlende Atteste mit Weg zum… |
| `frontend/src/features/students/GradesPage.tsx` | 171 | „Meine Noten“ (`/noten`) für Schüler/innen und Eltern (je Kind): alle Noten nach Fach – Klausuren/Tests und bewertete Hausaufgabe… |
| `frontend/src/features/students/RecordPage.tsx` | 241 | `/fehlzeiten/:studentId` – Fehlzeiten eines Kindes im Schuljahr: Summen (Tage/Stunden entschuldigt, unentschuldigt, offen; Verspä… |
| `frontend/src/features/students/ReportCard.tsx` | 299 | Karte „Krank melden“ für volljährige Schüler/innen und Eltern (je Kind): ein großer Knopf „Für heute krank melden“ (ein Klick + B… |
| `frontend/src/features/students/StudentDetail.tsx` | 93 | Stammdaten → Schüler/in: Eltern, Klassenleitung, Fachlehrkräfte sowie Merkmale & Nachweise (Nachteilsausgleich). |
| `frontend/src/features/students/SupportCatalogDialog.tsx` | 140 | Katalog der Merkmale/Nachteilsausgleiche der Schule (Zeitzuschlag, Duden, ADHS …) – Stammdaten → Schüler/innen. |
| `frontend/src/features/students/SupportSection.tsx` | 191 | Förderung & Nachteilsausgleich eines Kindes: Merkmale aus dem Katalog der Schule (Zeitzuschlag, Hilfsmittel, ADHS …), ggf. je Fac… |
| `frontend/src/features/students/api.ts` | 44 | Endpunkte der Schüler-Selbstbedienung (§9.6). |
| `frontend/src/features/students/badge.tsx` | 34 | Menü-Badges der Schüler-Selbstbedienung (klein, wird beim App-Start geladen – siehe module.tsx): Personal: offene Dokumente + feh… |
| `frontend/src/features/students/components.tsx` | 276 | Bausteine der Schüler-Selbstbedienung: Attest-Badge, Liste der Meldungen, Dokumentliste und Einreichen-Formular (Krankmelden selb… |
| `frontend/src/features/students/logic.ts` | 90 | Reine Hilfsfunktionen der Schüler-Selbstbedienung (ohne React, getestet in students.test.ts). |
| `frontend/src/features/students/module.tsx` | 58 | Feature-Modul „Schüler-Selbstbedienung“ (ARCHITECTURE.md §9.6) für die Registry (`features/registry.ts`). * „Meine Übersicht“ gib… |
| `frontend/src/features/students/students.css` | 121 | Stylesheet |
| `frontend/src/features/students/supportApi.ts` | 111 | Nachteilsausgleich & Förderung: API-Aufrufe und Typen (Katalog, Einträge, Hinweise bei Klausuren, Personen). |
| `frontend/src/features/students/types.ts` | 96 | Typen der Schüler-Selbstbedienung (§9.6) – Spiegel von `schulmanager/server/routes/features_student_self.py`. |
| `frontend/src/features/students/useChild.tsx` | 37 | Kinderauswahl für Eltern – gemeinsam für Startseite, Krankmeldungen, Noten und Kursräume (ein gemerktes Kind, Speicher-Schlüssel… |
| `frontend/src/features/students/widgets.tsx` | 100 | Startseiten-Kachel des Personals „Atteste & Dokumente“ (Klassenleitung: eigene Klasse, inkl. heutiger Krankmeldungen). Die Famili… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/absence-stats` | [[Routen features_absence_stats]] · `absence_stats` (`features_absence_stats.py:313`) |
| GET | `/absence-stats/class` | [[Routen features_absence_stats]] · `class_absence_stats` (`features_absence_stats.py:346`) |
| GET | `/channels/overview` | [[Routen features_channels]] · `channels_overview` (`features_channels.py:1411`) |
| GET | `/chats` | [[Routen features_chats]] · `list_chats` (`features_chats.py:757`) |
| GET | `/exams/{…}/results` | [[Routen features_grades]] · `get_results` (`features_grades.py:77`) |
| PUT | `/exams/{…}/results` | [[Routen features_grades]] · `put_results` (`features_grades.py:99`) |
| GET | `/grades` | [[Routen features_grades]] · `student_grades` (`features_grades.py:153`) |
| GET | `/classes/{…}/accounts` | [[Routen features_letters]] · `class_accounts` (`features_letters.py:347`) |
| GET | `/messages/conversations` | [[Routen features_messages]] · `list_conversations` (`features_messages.py:894`) |
| GET | `/messages/unread` | [[Routen features_messages]] · `get_unread` (`features_messages.py:806`) |
| PUT | `/students/{…}/birth-date` | [[Routen features_parent_access]] · `put_birth_date` (`features_parent_access.py:135`) |
| GET | `/student-absences` | [[Routen features_student_absences]] · `list_student_absences` (`features_student_absences.py:277`) |
| POST | `/student-absences` | [[Routen features_student_absences]] · `report_student_absence` (`features_student_absences.py:455`) |
| DELETE | `/student-absences/{…}` | [[Routen features_student_absences]] · `delete_student_absence` (`features_student_absences.py:641`) |
| PATCH | `/student-absences/{…}` | [[Routen features_student_absences]] · `patch_student_absence` (`features_student_absences.py:601`) |
| DELETE | `/student-absences/{…}` | [[Routen features_student_absences]] · `delete_student_absence` (`features_student_absences.py:641`) |
| POST | `/student-absences/{…}/extend` | [[Routen features_student_absences]] · `extend_absence` (`features_student_absences.py:812`) |
| POST | `/student-absences/{…}/request-withdrawal` | [[Routen features_student_absences]] · `request_withdrawal` (`features_student_absences.py:872`) |
| POST | `/student-absences/{…}/return-leave` | [[Routen features_student_absences]] · `return_leave` (`features_student_absences.py:895`) |
| POST | `/student-absences/{…}/shorten` | [[Routen features_student_absences]] · `shorten_absence` (`features_student_absences.py:748`) |
| GET | `/student-absences/preview` | [[Routen features_student_absences]] · `report_preview` (`features_student_absences.py:244`) |
| GET | `/student-absences/record` | [[Routen features_student_absences]] · `student_record` (`features_student_absences.py:943`) |
| GET | `/me/student-overview` | [[Routen features_student_self]] · `student_overview` (`features_student_self.py:442`) |
| GET | `/student-documents` | [[Routen features_student_self]] · `list_documents` (`features_student_self.py:223`) |
| POST | `/student-documents` | [[Routen features_student_self]] · `submit_document` (`features_student_self.py:253`) |
| DELETE | `/student-documents/{…}` | [[Routen features_student_self]] · `delete_document` (`features_student_self.py:364`) |
| PATCH | `/student-documents/{…}` | [[Routen features_student_self]] · `handle_document` (`features_student_self.py:313`) |
| GET | `/student-documents/summary` | [[Routen features_student_self]] · `documents_summary` (`features_student_self.py:404`) |
| GET | `/exams/support-hints` | [[Routen features_support]] · `exam_hints` (`features_support.py:416`) |
| GET | `/students/{…}/people` | [[Routen features_support]] · `student_people` (`features_support.py:494`) |
| GET | `/students/{…}/support` | [[Routen features_support]] · `list_support` (`features_support.py:253`) |
| POST | `/students/{…}/support` | [[Routen features_support]] · `create_support` (`features_support.py:311`) |
| DELETE | `/students/{…}/support/{…}` | [[Routen features_support]] · `delete_support` (`features_support.py:350`) |
| GET | `/students/support-flags` | [[Routen features_support]] · `flags` (`features_support.py:391`) |
| GET | `/support/catalog` | [[Routen features_support]] · `get_catalog` (`features_support.py:176`) |
| POST | `/support/catalog` | [[Routen features_support]] · `create_catalog` (`features_support.py:197`) |
| DELETE | `/support/catalog/{…}` | [[Routen features_support]] · `delete_catalog` (`features_support.py:232`) |
| PUT | `/support/catalog/{…}` | [[Routen features_support]] · `update_catalog` (`features_support.py:216`) |

## Backend-Notizen

[[Routen features_absence_stats]], [[Routen features_channels]], [[Routen features_chats]], [[Routen features_grades]], [[Routen features_letters]], [[Routen features_messages]], [[Routen features_parent_access]], [[Routen features_student_absences]], [[Routen features_student_self]], [[Routen features_support]]

## Nutzt (Frontend)

- [[Feature chats]] – `api`
- [[Feature classes]] – `CalendarWeek`
- [[Feature messages]] – `api`
- [[Feature zugangsdaten]] – `api`, `components`
- [[Frontend API-Schicht]] – `client`, `endpoints`, `files`, `types`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `misc`, `permissions` …
- [[Frontend Komponenten]] – `FileUpload`, `HelpTip`, `Icon`, `Modal`, `SearchSelect` …
- [[Seite StudentAbsencesPage]] – `StudentAbsencesPage`

## Wird genutzt von

- [[Frontend App und Routing]] – die Feature-Registry lädt `./*/module.tsx` automatisch (`import.meta.glob`)
- [[Feature channels]]
- [[Feature classes]]
- [[Seite DashboardPage]]
- [[Seite ExamsPage]]
- [[Seite MasterDataPage]]
- [[Seite StudentAbsencesPage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
