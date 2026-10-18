"""Rollen- und Rechtematrix (ARCHITECTURE.md §6, docs/ROLLEN-RECHTE.md).

* :data:`CATALOGUE` – Rechtekatalog (Bereich, Kurzname, Hilfetext, mögliche Umfänge, Status).
* :data:`ROLE_PERMISSIONS` – Standardrechte je Rolle (Schulen können abweichen: :func:`effective_rights`).
* Feste Mindestregeln: :data:`LOCKED_GRANT`, :data:`LOCKED_DENY`, :data:`ASSIGNABLE_ONLY`, :data:`RESTRICTED_TO`,
  :data:`SCOPE_LIMIT` – in „Rollen & Rechte“ nicht änderbar.
* :data:`PERMISSION_SCOPES` – Einschränkungen eines Rechts je Rolle, z. B. Lehrkräfte dürfen
  ``students.read`` nur für ``own_classes``. ``None``/fehlend = uneingeschränkt.
  Werte: ``no_admins``, ``students_parents``, ``own_courses``, ``own_classes``, ``class_teacher``, ``own_lessons``
  (Krankmeldungen für die eigene Stunde, ``absence_access``), ``own``, ``own_children``, ``history_only``,
  ``own_branch`` (Zweig der Abteilungsleitung).
* :func:`can_manage_role` – wer welche Konten verwalten darf.
* :func:`own_class_ids` – Klassen einer Lehrkraft / eines Schülers / der Kinder (für Sichtbarkeit).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..models import School

ALL = "all"   # Scope-Kennung für „uneingeschränkt“ (intern ``None``)

# Kontorollen (Reihenfolge = Anzeige). Klassenleitung ist KEINE Kontorolle, sondern ergibt sich aus der
# Klassenzuordnung (``SchoolClass.class_teacher``); Abteilungsleitung bekommt ihre Zweige per Zuordnung.
ROLES: tuple[str, ...] = ("admin", "schulleitung", "abteilungsleitung", "planer", "sekretariat", "lehrer",
                         "hausmeister", "schulbegleitung", "schueler", "eltern", "monitor", "zuschauer")
ROLE_LABELS: dict[str, str] = {
    "admin": "Administration", "schulleitung": "Schulleitung", "abteilungsleitung": "Abteilungsleitung",
    "planer": "Stundenplanung", "sekretariat": "Sekretariat", "lehrer": "Lehrkraft",
    "hausmeister": "Hausmeister/in", "schulbegleitung": "Schulbegleitung", "schueler": "Schüler/in",
    "eltern": "Eltern", "monitor": "Monitor (Anzeige)", "zuschauer": "Zuschauer/in (nur lesen)",
}
STAFF_ROLES = frozenset({"admin", "schulleitung", "abteilungsleitung", "planer", "sekretariat", "lehrer"})
# Rollen mit Bezug zu einzelnen Kindern: sehen nur ihre Kinder
CHILD_ROLES = frozenset({"schueler", "eltern", "schulbegleitung"})

ROLE_INFO: dict[str, dict] = {
    "admin": {"description": "Technischer Betrieb: Konten, Einstellungen, Sicherungen. Sieht keine Gesundheitsdaten.",
              "level": 6, "kind": "tech"},
    "schulleitung": {"description": "Leitet die Schule: sieht und verwaltet nahezu alles, vergibt Rollen und Rechte.",
                     "level": 5, "kind": "staff"},
    "sekretariat": {"description": "Verwaltung: Stammdaten, Krankmeldungen, Mitteilungen, Konten von Schülern/Eltern.",
                    "level": 4, "kind": "staff"},
    "planer": {"description": "Stundenplanung: Stundenplan erstellen und ändern, Vertretungen, Klausuren.",
               "level": 4, "kind": "staff"},
    "abteilungsleitung": {"description": "Leitet einen Schulzweig (Abteilung): wie Lehrkraft, aber mit Blick auf alle "
                                         "Klassen des eigenen Zweigs.", "level": 3, "kind": "staff",
                          "link": "branches"},
    "lehrer": {"description": "Unterricht: eigener Plan, eigene Kurse und Klassen; als Klassenleitung zusätzlich "
                              "die geleitete Klasse.", "level": 1, "kind": "staff"},
    "hausmeister": {"description": "Haustechnik: Raumpläne und Anzeige, keine Schülerdaten.", "level": 1,
                    "kind": "limited"},
    "schulbegleitung": {"description": "Begleitet ein Kind im Schulalltag: sieht dessen Stundenplan, Kursräume und "
                                       "Material – ohne Elternrechte (keine Krankmeldung).", "level": 0,
                        "kind": "child", "link": "students"},
    "schueler": {"description": "Eigener Plan, Kursräume, Postfach.", "level": 0, "kind": "child", "link": "student"},
    "eltern": {"description": "Pläne und Krankmeldung der eigenen Kinder.", "level": 0, "kind": "child",
               "link": "students"},
    "monitor": {"description": "Anzeigegerät (Vertretungsplan im Foyer).", "level": 0, "kind": "display"},
    "zuschauer": {"description": "Vorführ-/Prüfzugang: sieht wie Leitung/Planung/Sekretariat, ändert nichts.",
                  "level": 0, "kind": "display"},
}
# Abgeleitete Titel (kein eigenes Konto)
DERIVED_ROLES: list[dict] = [
    {"id": "klassenleitung", "label": "Klassenleitung",
     "description": "Lehrkraft, die in den Stammdaten als Klassenleitung einer Klasse eingetragen ist. Sieht zusätzlich "
                    "Plan, Klassenbuch-Übersicht und Atteste der eigenen Klasse (bei der Lehrkraft: Umfang "
                    "„Eigene Klassenleitung“)."},
]
# Rangfolge für die Anzeige „Lehrkraft → Klassenleitung → Abteilungsleitung → Sekretariat/Schulleitung“
HIERARCHY: tuple[str, ...] = ("lehrer", "klassenleitung", "abteilungsleitung", "sekretariat", "schulleitung")

AREAS: list[tuple[str, str]] = [
    ("plaene", "Pläne & Stammdaten"),
    ("vertretung", "Vertretung & Aufsicht"),
    ("schueler", "Schüler, Klassenbuch & Prüfungen"),
    ("kommunikation", "Kommunikation & Kursräume"),
    ("konten", "Konten & Profile"),
    ("verwaltung", "Verwaltung & System"),
]

SCOPE_LABELS: dict[str, str] = {
    ALL: "Alle", "own_classes": "Eigene Klassen", "own_courses": "Eigene Kurse",
    "class_teacher": "Eigene Klassenleitung", "own_branch": "Eigener Zweig", "own": "Nur selbst",
    "own_children": "Eigene Kinder", "no_admins": "Ohne Administration", "students_parents": "Nur Schüler/Eltern",
    "history_only": "Nur Verlauf", "own_lessons": "Eigene Stunden",
}


def _p(area: str, label: str, help_: str, scopes: tuple[str, ...] = (), status: str = "aktiv") -> tuple:
    return area, label, help_, scopes, status


# id -> (Bereich, Kurzname, Hilfetext, mögliche Einschränkungen außer „Alle“, Status).
# Status ``aktiv``: der Server prüft das Recht; ``geplant``: Recht ist angelegt und einstellbar, die zugehörige
# Funktion prüft bisher noch das ältere Recht.
CATALOGUE: dict[str, tuple] = {
    "plans.read_all": _p("plaene", "Pläne lesen", "Klassen-, Lehrer- und Schülerpläne. Mit Einschränkung nur Pläne "
                         "eigener (bzw. geleiteter) Klassen.", ("own_classes", "own_branch")),
    "rooms.read": _p("plaene", "Raumpläne lesen", "Raumbelegung und Raumpläne (z. B. Hausmeister). Lehrkräfte sehen "
                     "Räume nur in ihrem eigenen Plan."),
    "masterdata.read": _p("plaene", "Stammdaten lesen", "Lehrkräfte, Räume, Fächer, Klassen ansehen – ohne alle Pläne "
                          "lesen zu dürfen.", status="geplant"),
    "masterdata.edit": _p("plaene", "Stammdaten bearbeiten", "Lehrkräfte, Räume, Fächer, Klassen, Kurse anlegen und "
                          "ändern."),
    "timetable.generate": _p("plaene", "Stundenplan generieren", "Automatische Planerstellung starten."),
    "timetable.edit": _p("plaene", "Stundenplan bearbeiten", "Stunden verschieben, Raum/Lehrkraft ändern. Schließt das "
                         "Lesen aller Pläne ein."),
    "substitution.read": _p("vertretung", "Vertretungsplan lesen", "Den Vertretungsplan der Schule ansehen. Schüler/innen "
                            "und Eltern haben das Recht nicht – sie sehen Entfall, Vertretung und Raumänderung direkt "
                            "im eigenen Stundenplan."),
    "substitution.edit": _p("vertretung", "Vertretungen bearbeiten", "Abwesenheiten erfassen, Vertretungen planen und "
                            "veröffentlichen."),
    "substitution.self_study": _p("vertretung", "Eigenarbeit freigeben", "Entscheiden, dass eine Klasse bei Ausfall allein "
                                  "arbeitet (ab welcher Klassenstufe, legt die Verwaltung fest) – nicht die "
                                  "Lehrkraft selbst.", ("own_branch",), "geplant"),
    "duties.manage": _p("vertretung", "Aufsichten verwalten", "Pausenbereiche, Verfügbarkeit der Lehrkräfte und faire "
                        "Verteilung der Aufsichten festlegen.", status="geplant"),
    "absence.report_self": _p("vertretung", "Eigene Krankmeldung", "Lehrkraft meldet sich selbst ab."),
    "monitor.read": _p("vertretung", "Monitor-Ansicht", "Vertretungsmonitor/Aushang anzeigen."),
    "monitor.manage": _p("vertretung", "Monitore einstellen", "Anzeigetage, Laufband und Hinweise der Monitore."),
    "students.read": _p("schueler", "Schülerdaten lesen", "Namen, Klassen, Kurse von Schülern. Lehrkräfte nur eigener "
                        "Klassen.", ("own_classes", "own_branch")),
    "students.birth_date": _p("schueler", "Geburtsdatum pflegen", "Geburtsdatum von Schüler/innen setzen oder ändern. "
                              "Daraus ergibt sich die Volljährigkeit (Elternfreigabe, eigene Krankmeldung). "
                              "Lehrkräfte nur für die Klasse, die sie leiten.", ("class_teacher",)),
    "register.read_all": _p("schueler", "Klassenbuch gesamt lesen", "Gesamtes Klassenbuch einer Klasse einsehen. "
                            "Fachlehrkräfte sehen nur eigene Stunden, Klassenleitung die ganze Klasse.",
                            ("own_branch", "class_teacher"), "geplant"),
    "student_absence.report": _p("schueler", "Schüler krankmelden", "Krankmeldung für ein Kind eintragen (Eltern, "
                                 "Sekretariat, Lehrkraft für die eigene Stunde).",
                                 ("own_lessons", "class_teacher", "own_classes", "own_branch", "own", "own_children")),
    "student_absence.read": _p("schueler", "Krankmeldungen lesen", "Krankmeldungen von Schülern ansehen "
                               "(Gesundheitsdaten: nie für die technische Administration).",
                               ("class_teacher", "own_classes", "own_branch", "own", "own_children")),
    "student_documents.read": _p("schueler", "Atteste & Dokumente", "Eingereichte Atteste/Dokumente. Gesundheitsdaten: "
                                 "nie für die technische Administration.", ("class_teacher", "own", "own_children")),
    "support.read": _p("schueler", "Nachteilsausgleich & Förderung", "Förderbedarf, Nachteilsausgleich und "
                       "Nachweise ansehen – getrennt von den Schülerdaten.", ("class_teacher", "own_branch")),
    "support.manage": _p("schueler", "Nachteilsausgleich pflegen", "Merkmale, Nachteilsausgleiche und Nachweise "
                         "(PDF/Dateien) je Schüler/in eintragen und löschen.", ("class_teacher",)),
    "support.catalog": _p("schueler", "Katalog der Merkmale", "Festlegen, welche Arten von Nachteilsausgleich/"
                          "Förderung es an der Schule gibt (z. B. Zeitzuschlag, ADHS)."),
    "support.hints": _p("schueler", "Ausgleichs-Hinweis bei Klausuren", "Bei Klausuren/Tests sehen, welche "
                        "Schüler/innen welchen Nachteilsausgleich haben (ohne Diagnose und Nachweis).",
                        ("own_courses",)),
    "forms.submit": _p("kommunikation", "Formulare ausfüllen", "Formulare der Schule online ausfüllen (z. B. Beurlaubung, "
                       "Einverständnis). Welche Formulare, bestimmt die Zielgruppe des Formulars."),
    "forms.inbox": _p("kommunikation", "Formular-Eingang", "Einreichungen ansehen, genehmigen, exportieren. Lehrkräfte nur für "
                      "die Klasse, die sie leiten. Enthält teils Gesundheitsdaten: nie für die technische "
                      "Administration.", ("class_teacher",)),
    "forms.manage": _p("kommunikation", "Formulare gestalten", "Formular-Vorlagen anlegen, Ablauf und Aktionen festlegen, "
                       "Bibliothek übernehmen – ohne Einblick in ausgefüllte Formulare."),
    "exam.edit": _p("schueler", "Klausuren bearbeiten", "Klausurtermine eintragen. Lehrkräfte nur für eigene Kurse.",
                    ("own_courses",)),
    "exam.types.manage": _p("schueler", "Klausurarten verwalten", "Welche Klausurarten es gibt (z. B. Klassenarbeit, "
                            "Test).", status="geplant"),
    "announcement.post": _p("kommunikation", "Mitteilungen veröffentlichen", "Schwarzes Brett/Aushang. Lehrkräfte nur "
                            "für eigene Klassen.", ("own_classes", "own_branch")),
    "messages.use": _p("kommunikation", "Postfach nutzen", "Interne Nachrichten senden und lesen. Wer wem schreiben "
                       "darf, regeln die Einstellungen der Schule."),
    "mail.custom_server": _p("kommunikation", "Eigene Mailserver eintragen", "Im Postfach ein E-Mail-Konto bei einem "
                             "anderen Anbieter mit eigenem IMAP-/SMTP-Server verbinden (z. B. der Mailserver der "
                             "Schule). Die bekannten Anbieter (Google, GMX …) stehen allen mit Postfach offen. "
                             "Nur für Personal."),
    "messages.broadcast": _p("kommunikation", "An Gruppen senden", "Nachrichten an Klassen, Kurse, Kollegium oder alle.",
                             ("own_classes", "own_branch")),
    "messages.moderate": _p("kommunikation", "Gemeldete Nachrichten prüfen", "Gemeldete Nachrichten ansehen und "
                            "bearbeiten."),
    "chats.review": _p("kommunikation", "Gemeldete Chat-Auszüge", "Gemeldete Chat-Auszüge nur mit Einwilligung von Kind "
                       "bzw. Eltern lesen.", status="geplant"),
    "channels.use": _p("kommunikation", "Kursräume nutzen", "Material, Aufgaben und Pinnwand der Kursräume."),
    "channels.view_children": _p("kommunikation", "Kursräume der Kinder lesen", "Freigegebenes Material und Aufgaben "
                                 "der Kursräume der eigenen Kinder (Eltern; welche Bereiche, regelt die Schule).",
                                 ("own_children",)),
    "channels.manage": _p("kommunikation", "Kursräume verwalten", "Ordner, Material, Freigaben, Aufgaben. Lehrkräfte "
                          "nur eigene Kurse.", ("own_courses",)),
    "competency.read": _p("schueler", "Lernstand lesen", "Kompetenzraster und Lernstand der Schüler/innen ansehen "
                          "(Klassenübersicht, Lernpläne, Abzeichen, Lernentwicklungsbericht). Lehrkräfte nur eigener "
                          "Klassen. Lernstände sind personenbezogen: nie für die technische Administration.",
                          ("own_classes", "own_branch")),
    "competency.assess": _p("schueler", "Lernstand eintragen", "Stufen je Kompetenz setzen, Selbsteinschätzungen "
                            "bestätigen, Lernpläne führen, Abzeichen vergeben. Lehrkräfte nur eigener Klassen.",
                            ("own_classes", "own_branch")),
    "competency.manage": _p("schueler", "Kompetenzrahmen & Abzeichen verwalten", "Kompetenzrahmen (Bereiche, Kompetenzen, "
                            "Niveaustufen) anlegen, importieren und ändern sowie Abzeichen der Schule festlegen – ohne "
                            "Einblick in Lernstände."),
    "gradebook.use": _p("schueler", "Notenbuch führen", "Noten, Leistungsarten und Gewichtung im Notenbuch eigener Kurse "
                        "eintragen, Halbjahresnoten festlegen und sperren. Noten sind personenbezogen: nie für die "
                        "technische Administration.", ("own_courses",)),
    "gradebook.read_class": _p("schueler", "Noten der Klasse lesen", "Notenübersicht, Notenkonferenz-Liste und "
                               "Versetzungswarnung der Klasse ansehen (Klassenleitung, lesend).",
                               ("class_teacher", "own_branch")),
    "gradebook.manage": _p("schueler", "Notenbuch verwalten", "Notenskalen, Notenschlüssel, Einsicht für Schüler/innen "
                           "und Versetzungswarnung der Schule festlegen, gesperrte Notenbücher wieder öffnen. "
                           "Sieht alle Notenbücher."),
    "gradebook.export": _p("schueler", "Noten exportieren", "Gesperrte Halbjahres-/Zeugnisnoten als CSV für SchILD, ASV "
                           "oder LUSD ausgeben."),
    "channels.trash": _p("kommunikation", "Kursraum-Papierkorb nutzen", "Gelöschtes Material, Aufgaben und Ordner "
                         "wiederherstellen oder endgültig löschen. Lehrkräfte nur eigene Kurse.", ("own_courses",)),
    "users.manage": _p("konten", "Konten verwalten", "Benutzerkonten anlegen, ändern, sperren.",
                       ("no_admins", "students_parents")),
    "passwords.reset": _p("konten", "Passwörter zurücksetzen", "Passwort auf das Startpasswort oder ein selbst "
                          "gesetztes zurücksetzen. Lehrkräfte nur für Schüler/innen der Klassen, die sie leiten.",
                          ("class_teacher", "students_parents")),
    "profile.teacher_self": _p("konten", "Eigenes Lehrerprofil", "Fächer, Klassen, Stunden und Zeiten selbst pflegen "
                               "(als Antrag)."),
    "teacher_requests.review": _p("konten", "Profil-Anträge prüfen", "Anträge von Lehrkräften genehmigen oder ablehnen."),
    "settings.edit": _p("verwaltung", "Einstellungen bearbeiten", "Schulweite Einstellungen (auch die Regeln des "
                        "Postfachs)."),
    "rights.manage": _p("verwaltung", "Rollen & Rechte verwalten", "Diese Seite bearbeiten. Nur Administration und "
                        "Schulleitung."),
    "login_policy.manage": _p("verwaltung", "Anmelde-Richtlinien", "Passwortregeln, 2FA, Anmeldedienste."),
    "audit.read": _p("verwaltung", "Protokoll lesen", "Audit-Protokoll aller Änderungen."),
    "privacy.manage": _p("verwaltung", "Löschkonzept verwalten", "Aufbewahrungsfristen einstellen, Warteliste der "
                         "Ausgetretenen, Vorschau „Was würde gelöscht“ und Löschprotokoll (ohne Einblick in Inhalte)."),
    "privacy.subject": _p("verwaltung", "Betroffenenrechte erfüllen", "Auskunft für eine Person erzeugen (Art. 15/20) "
                          "und eine Person sofort löschen (Art. 17). Enthält Gesundheits- und Notendaten: nie für die "
                          "technische Administration."),
    "history.restore": _p("verwaltung", "Verlauf & Wiederherstellung", "Versionsverlauf ansehen, Stand wiederherstellen.",
                          ("history_only",)),
    "system.admin": _p("verwaltung", "Systemverwaltung", "Sicherungen, Schlüssel, Demo-Daten."),
    "license.manage": _p("verwaltung", "Lizenz verwalten", "Lizenzstand sehen, neue Lizenz einspielen und online "
                         "prüfen – auch wenn die Anwendung wegen einer abgelaufenen Lizenz gesperrt ist. Bekommt "
                         "Vorwarnungen vor dem Ablauf."),
    "api.own": _p("verwaltung", "Eigene API-Zugänge", "Zugänge für Apps oder KI-Werkzeuge ausgeben (nur lesend, mit "
                  "Bereichen und Filtern) – höchstens mit dem, was das eigene Konto selbst sehen darf. Gesundheits- und "
                  "Förderdaten sind nie freigebbar."),
    "api.manage": _p("verwaltung", "API-Zugänge verwalten", "Alle API-Zugänge der Schule einsehen, deren Nutzung prüfen "
                     "und widerrufen."),
}
PERMISSIONS: dict[str, str] = {pid: meta[1] for pid, meta in CATALOGUE.items()}
PERMISSION_AREA: dict[str, str] = {pid: meta[0] for pid, meta in CATALOGUE.items()}

_ALL = set(PERMISSIONS)

# --------------------------------------------------------------------------------- Standardrechte je Rolle
_ADMIN_DENIED = {"absence.report_self", "student_absence.report", "student_absence.read", "profile.teacher_self",
                 "student_documents.read", "support.read", "support.manage", "support.hints", "chats.review",
                 "channels.view_children", "forms.submit", "forms.inbox", "competency.read", "competency.assess",
                 "competency.manage"}
_ADMIN_DENIED |= {"gradebook.use", "gradebook.read_class", "gradebook.manage", "gradebook.export"}
_ADMIN_DENIED |= {"privacy.subject"}
_LEHRER = frozenset({
    "absence.report_self", "exam.edit", "announcement.post", "plans.read_all", "students.read", "substitution.read",
    "student_absence.report", "student_absence.read", "profile.teacher_self", "channels.use",
    "channels.manage", "channels.trash", "messages.use", "messages.broadcast", "student_documents.read", "support.read",
    "support.manage", "support.hints", "passwords.reset", "students.birth_date", "api.own", "forms.submit",
    "forms.inbox", "competency.read", "competency.assess", "competency.manage"})
_LEHRER = _LEHRER | frozenset({"gradebook.use", "gradebook.read_class"})
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    # Technische Administration: keine Gesundheitsdokumente (Atteste) – Datensparsamkeit, §9.6
    "admin": frozenset(_ALL - _ADMIN_DENIED),
    "schulleitung": frozenset({
        "users.manage", "settings.edit", "masterdata.edit", "masterdata.read", "substitution.edit", "exam.edit",
        "substitution.read", "announcement.post", "plans.read_all", "rooms.read", "students.read",
        "student_absence.read", "audit.read", "privacy.manage", "privacy.subject",
        "history.restore", "monitor.read", "monitor.manage", "teacher_requests.review", "channels.use",
        "channels.manage", "channels.trash", "messages.use", "messages.broadcast", "messages.moderate", "student_documents.read",
        "login_policy.manage", "passwords.reset", "rights.manage", "register.read_all", "support.read", "support.manage",
        "students.birth_date", "mail.custom_server",
        "support.catalog", "support.hints", "duties.manage", "substitution.self_study", "exam.types.manage",
        "chats.review", "license.manage", "api.own", "api.manage", "forms.submit", "forms.inbox", "forms.manage",
        "competency.read", "competency.assess", "competency.manage"}),
    "planer": frozenset({
        "settings.edit", "masterdata.edit", "masterdata.read", "timetable.generate", "timetable.edit",
        "substitution.edit", "substitution.read", "exam.edit", "announcement.post", "plans.read_all", "rooms.read", "students.read",
        "history.restore", "monitor.read", "teacher_requests.review", "messages.use", "messages.broadcast",
        "duties.manage", "substitution.self_study", "exam.types.manage", "api.own"}),
    "sekretariat": frozenset({
        "users.manage", "masterdata.edit", "masterdata.read", "substitution.edit", "substitution.read",
        "announcement.post", "plans.read_all", "rooms.read", "students.read", "student_absence.report",
        "student_absence.read",
        "monitor.read", "monitor.manage", "messages.use", "messages.broadcast", "student_documents.read",
        "register.read_all", "passwords.reset", "support.read", "support.manage", "support.catalog",
        "support.hints", "students.birth_date", "api.own", "forms.submit", "forms.inbox", "forms.manage",
        "mail.custom_server"}),
    # Lehrkräfte: nur eigene Fächer/Kurse und die zugehörigen Klassen (Scopes unten), kein Monitor
    "lehrer": _LEHRER,
    # Abteilungsleitung: wie Lehrkraft, aber mit Blick auf die Klassen des eigenen Zweigs
    "abteilungsleitung": _LEHRER | {"register.read_all", "substitution.self_study"},
    "hausmeister": frozenset({"rooms.read", "monitor.read", "messages.use"}),
    "schulbegleitung": frozenset({"channels.use", "substitution.read"}),
    "schueler": frozenset({"student_absence.read", "channels.use", "messages.use", "forms.submit"}),
    "eltern": frozenset({"student_absence.report", "student_absence.read", "messages.use",
                         "student_documents.read", "channels.view_children", "forms.submit"}),
    "monitor": frozenset({"monitor.read"}),
}
ROLE_PERMISSIONS["schulleitung"] = ROLE_PERMISSIONS["schulleitung"] | {
    "gradebook.use", "gradebook.read_class", "gradebook.manage", "gradebook.export"}
ROLE_PERMISSIONS["sekretariat"] = ROLE_PERMISSIONS["sekretariat"] | {"gradebook.export"}
# Zuschauer/in (Vorführung, Prüfung): sieht alles wie Schulleitung, Planung und Sekretariat zusammen – ohne
# Systemverwaltung (Sicherungen, Schlüssel). Jede ändernde Anfrage lehnt der Server ab (``deps.authenticate``).
ROLE_PERMISSIONS["zuschauer"] = frozenset(
    (ROLE_PERMISSIONS["schulleitung"] | ROLE_PERMISSIONS["planer"] | ROLE_PERMISSIONS["sekretariat"])
    - {"system.admin", "student_absence.report", "absence.report_self", "profile.teacher_self", "rights.manage",
       "license.manage", "api.own", "api.manage", "forms.submit", "privacy.manage", "privacy.subject"})
READ_ONLY_ROLES = frozenset({"zuschauer"})

PERMISSION_SCOPES: dict[str, dict[str, str]] = {
    "schulleitung": {"users.manage": "no_admins"},
    "sekretariat": {"users.manage": "students_parents"},
    "planer": {"history.restore": "history_only"},
    # Krankmeldungen (B-06, ``absence_access``): lesen/verwalten nur als Klassenleitung, melden zusätzlich für die
    # eigene Stunde (Kursteile, auch Vertretung); Fachlehrkräfte lesen nur mit Schulschalter „presence“
    "lehrer": {"exam.edit": "own_courses", "announcement.post": "own_classes", "students.read": "own_classes",
               "student_absence.read": "class_teacher", "student_absence.report": "own_lessons",
               # Erweiterung 2: Pläne nur eigener Klassen/Kurse (+ eigener Plan, eigene Vertretungen)
               "plans.read_all": "own_classes", "channels.manage": "own_courses",
               "channels.trash": "own_courses", "messages.broadcast": "own_classes", "student_documents.read": "class_teacher",
               "support.read": "class_teacher", "support.manage": "class_teacher",
               "support.hints": "own_courses", "passwords.reset": "class_teacher",
               "students.birth_date": "class_teacher", "forms.inbox": "class_teacher",
               "competency.read": "own_classes", "competency.assess": "own_classes"},
    "abteilungsleitung": {"exam.edit": "own_courses", "announcement.post": "own_branch", "students.read": "own_branch",
                          "student_absence.read": "own_branch", "student_absence.report": "own_branch",
                          "plans.read_all": "own_branch", "channels.manage": "own_courses",
                          "channels.trash": "own_courses", "messages.broadcast": "own_branch", "student_documents.read": "class_teacher",
                          "support.read": "class_teacher", "support.manage": "class_teacher",
                          "support.hints": "own_courses", "register.read_all": "own_branch",
                          "substitution.self_study": "own_branch", "passwords.reset": "class_teacher",
                          "students.birth_date": "class_teacher", "forms.inbox": "class_teacher",
                          "competency.read": "own_branch", "competency.assess": "own_branch"},
    "schueler": {"student_absence.read": "own", "student_absence.report": "own", "student_documents.read": "own"},
    "eltern": {"student_absence.read": "own_children", "student_absence.report": "own_children",
               "student_documents.read": "own_children", "channels.view_children": "own_children"},
}
PERMISSION_SCOPES["lehrer"].update({"gradebook.use": "own_courses", "gradebook.read_class": "class_teacher"})
PERMISSION_SCOPES["abteilungsleitung"].update({"gradebook.use": "own_courses", "gradebook.read_class": "class_teacher"})

# Welche Rollen eine Rolle mit ``users.manage`` anlegen/ändern/löschen darf
MANAGEABLE_ROLES: dict[str, frozenset[str]] = {
    "admin": frozenset(ROLES),
    "schulleitung": frozenset(set(ROLES) - {"admin"}),
    "sekretariat": frozenset({"schueler", "eltern", "schulbegleitung"}),
}

# --------------------------------------------------------------------------------- Feste Mindestregeln
# Diese Regeln lassen sich in „Rollen & Rechte“ nicht ändern (Datenschutz, Betriebssicherheit).
# Rollen mit eingeschränktem Zweck bekommen ausschließlich diese Rechte:
ASSIGNABLE_ONLY: dict[str, frozenset[str]] = {
    "schueler": frozenset({"student_absence.read", "channels.use", "messages.use", "forms.submit"}),
    "eltern": frozenset({"student_absence.report", "student_absence.read", "student_documents.read", "messages.use",
                         "channels.use", "channels.view_children", "forms.submit"}),
    "schulbegleitung": frozenset({"channels.use", "messages.use", "student_absence.read", "substitution.read"}),
    "hausmeister": frozenset({"rooms.read", "monitor.read", "monitor.manage", "messages.use"}),
    "monitor": frozenset({"monitor.read"}),
}
_ASSIGNABLE_REASON = {
    "schueler": "Schüler/innen sehen nur eigene Daten – Personalrechte sind ausgeschlossen.",
    "eltern": "Eltern sehen nur die eigenen Kinder – Personalrechte sind ausgeschlossen.",
    "schulbegleitung": "Schulbegleitung hat keine Elternrechte (keine Krankmeldung, keine Atteste).",
    "hausmeister": "Hausmeister/in bekommt keine Schüler- oder Personaldaten.",
    "monitor": "Ein Monitor zeigt nur den Vertretungsplan.",
}
# Rechte nur für bestimmte Rollen (sensibel)
RESTRICTED_TO: dict[str, tuple[frozenset[str], str]] = {
    "system.admin": (frozenset({"admin"}), "Systemverwaltung bleibt der Administration vorbehalten."),
    "rights.manage": (frozenset({"admin", "schulleitung"}),
                      "Rechte verwalten dürfen nur Administration und Schulleitung."),
    "license.manage": (frozenset({"admin", "schulleitung"}), "Lizenz: nur Administration und Schulleitung."),
    "login_policy.manage": (frozenset({"admin", "schulleitung"}), "Anmelderegeln: nur Administration und Schulleitung."),
    "audit.read": (frozenset({"admin", "schulleitung"}), "Das Protokoll lesen nur Administration und Schulleitung."),
    "privacy.manage": (frozenset({"admin", "schulleitung"}), "Das Löschkonzept verwalten nur Administration und Schulleitung."),
    "privacy.subject": (frozenset({"schulleitung"}), "Auskunft und Sofort-Löschen (Gesundheits-/Notendaten) nur die Schulleitung."),
    "users.manage": (frozenset({"admin", "schulleitung", "sekretariat"}), "Konten verwalten: nur Verwaltungsrollen."),
    "student_documents.read": (frozenset({"schulleitung", "sekretariat", "lehrer", "abteilungsleitung", "schueler",
                                          "eltern"}), "Atteste (Gesundheitsdaten) sieht die technische Administration "
                                                      "nie."),
    "support.read": (frozenset({"schulleitung", "sekretariat", "lehrer", "abteilungsleitung"}),
                     "Förderdaten sind sensibel – nicht für Technik/Planung."),
    "support.manage": (frozenset({"schulleitung", "sekretariat", "lehrer", "abteilungsleitung"}),
                       "Förderdaten sind sensibel – nicht für Technik/Planung."),
    "support.hints": (frozenset({"schulleitung", "sekretariat", "lehrer", "abteilungsleitung"}),
                      "Förderdaten sind sensibel – nicht für Technik/Planung."),
    "forms.inbox": (frozenset({"schulleitung", "sekretariat", "lehrer", "abteilungsleitung"}),
                    "Ausgefüllte Formulare enthalten teils Gesundheitsdaten – nicht für Technik/Planung."),
    "forms.manage": (frozenset({"admin", "schulleitung", "sekretariat"}),
                     "Formulare gestalten: nur Administration, Schulleitung und Sekretariat."),
    "forms.submit": (frozenset({"schulleitung", "sekretariat", "lehrer", "abteilungsleitung", "schueler", "eltern"}),
                     "Die technische Administration füllt keine Formulare aus."),
    "competency.read": (frozenset({"schulleitung", "lehrer", "abteilungsleitung"}),
                        "Lernstände sind personenbezogen – nur Lehrkräfte und Leitung."),
    "competency.assess": (frozenset({"schulleitung", "lehrer", "abteilungsleitung"}),
                          "Lernstände tragen nur Lehrkräfte und Leitung ein."),
    "competency.manage": (frozenset({"schulleitung", "lehrer", "abteilungsleitung"}),
                          "Kompetenzrahmen pflegen nur Lehrkräfte und Leitung."),
    "chats.review": (frozenset({"schulleitung"}), "Gemeldete Chats nur durch die Schulleitung, mit Einwilligung."),
    "mail.custom_server": (frozenset({"admin", "schulleitung", "abteilungsleitung", "planer", "sekretariat", "lehrer"}),
                           "Eigene Mailserver tragen nur Personal-Konten ein (nie Schüler, Eltern, Hausmeister, "
                           "Monitor) – sonst ließe sich der Server als Netzwerk-Scanner missbrauchen."),
    "api.own": (frozenset({"admin", "schulleitung", "abteilungsleitung", "planer", "sekretariat", "lehrer"}),
                "API-Zugänge geben nur Personal-Konten aus (nie Schüler, Eltern, Hausmeister, Monitor)."),
    "api.manage": (frozenset({"admin", "schulleitung"}), "Alle API-Zugänge verwalten: nur Administration und "
                                                          "Schulleitung."),
}
_GRADEBOOK_WHO = frozenset({"schulleitung", "lehrer", "abteilungsleitung"})
RESTRICTED_TO.update({
    "gradebook.use": (_GRADEBOOK_WHO, "Noten sehen und führen nur Lehrkräfte und Leitung."),
    "gradebook.read_class": (_GRADEBOOK_WHO, "Noten einer Klasse sehen nur Lehrkräfte und Leitung."),
    "gradebook.manage": (frozenset({"schulleitung"}), "Das Notenbuch der Schule verwaltet nur die Schulleitung."),
    "gradebook.export": (frozenset({"schulleitung", "sekretariat"}),
                         "Noten exportieren nur Schulleitung und Sekretariat."),
})
# Dauerhaft vergeben bzw. entzogen
LOCKED_GRANT: dict[str, dict[str, str]] = {
    "admin": {p: "Die Administration muss immer Konten, Einstellungen, Rechte und die Lizenz verwalten können (sonst Aussperrung)."
              for p in ("users.manage", "settings.edit", "rights.manage", "system.admin", "license.manage")},
}
LOCKED_DENY: dict[str, dict[str, str]] = {
    "admin": {p: "Gesundheits- und Personaldaten sieht die technische Administration nie." for p in _ADMIN_DENIED},
    "schueler": {"student_absence.report": "Nur volljährige Schüler/innen melden sich selbst krank (Konto-Einstellung).",
                 "student_documents.read": "Dokumente reichen nur volljährige Schüler/innen selbst ein "
                                           "(Konto-Einstellung)."},
}
# Mögliche Umfänge je Rolle und Recht; fehlt der Eintrag, gelten die Optionen des Rechts. Der erste Wert ist der
# Rückfall, falls ein gespeicherter Umfang nicht (mehr) zulässig ist.
SCOPE_LIMIT: dict[tuple[str, str], tuple[tuple[str, ...], str]] = {}


def _limit(roles: tuple[str, ...], perms: tuple[str, ...], allowed: tuple[str, ...], reason: str) -> None:
    for r in roles:
        for p in perms:
            SCOPE_LIMIT[(r, p)] = (allowed, reason)


_limit(("lehrer",), ("students.read", "plans.read_all"), ("own_classes",),
       "Lehrkräfte sehen nur Daten eigener Klassen (Datenschutz).")
# Krankmeldungen (B-06): lesen als Klassenleitung (oder eigene Klassen), melden für die eigene Stunde
_limit(("lehrer",), ("student_absence.read",), ("class_teacher", "own_classes"),
       "Krankmeldungen sind Gesundheitsdaten: Lehrkräfte sehen sie als Klassenleitung bzw. für eigene Klassen.")
_limit(("lehrer",), ("student_absence.report",), ("own_lessons", "class_teacher", "own_classes"),
       "Lehrkräfte melden für die eigene Stunde bzw. als Klassenleitung.")
_limit(("lehrer", "abteilungsleitung"), ("passwords.reset",), ("class_teacher",),
       "Passwörter setzen Lehrkräfte nur für Schüler/innen der Klassen zurück, die sie leiten.")
_limit(("lehrer", "abteilungsleitung"), ("students.birth_date",), ("class_teacher",),
       "Das Geburtsdatum pflegen Lehrkräfte nur für Schüler/innen der Klassen, die sie leiten.")
_limit(("lehrer", "abteilungsleitung"), ("student_documents.read", "support.read", "support.manage", "forms.inbox"),
       ("class_teacher",),
       "Gesundheits-/Förderdaten nur für die Klassenleitung der eigenen Klasse.")
_limit(("abteilungsleitung",), ("students.read", "plans.read_all", "student_absence.read", "student_absence.report"),
       ("own_branch", "own_classes"), "Abteilungsleitung sieht nur den eigenen Zweig.")
_limit(("schueler",), ("student_absence.read", "student_absence.report", "student_documents.read"), ("own",),
       "Schüler/innen sehen nur sich selbst.")
_limit(("eltern",), ("student_absence.read", "student_absence.report", "student_documents.read"), ("own_children",),
       "Eltern sehen nur die eigenen Kinder.")
_limit(("schulbegleitung",), ("student_absence.read",), ("own_children",), "Nur das begleitete Kind.")
_limit(("lehrer",), ("competency.read", "competency.assess"), ("own_classes",),
       "Lehrkräfte sehen und pflegen den Lernstand nur eigener Klassen.")
_limit(("abteilungsleitung",), ("competency.read", "competency.assess"), ("own_branch", "own_classes"),
       "Abteilungsleitung sieht nur den eigenen Zweig.")
_limit(("lehrer", "abteilungsleitung"), ("gradebook.use",), ("own_courses",),
       "Lehrkräfte führen das Notenbuch nur für eigene Kurse.")
_limit(("lehrer", "abteilungsleitung"), ("gradebook.read_class",), ("class_teacher",),
       "Lehrkräfte sehen die Noten einer Klasse nur als Klassenleitung.")
_limit(("sekretariat",), ("users.manage",), ("students_parents",),
       "Sekretariat verwaltet nur Schüler-, Eltern- und Begleitungskonten.")


def scope_options(role: str, perm: str) -> tuple[str, ...]:
    """Wählbare Umfänge (``all`` = uneingeschränkt) für ein Recht in einer Rolle; leer = nicht einstellbar."""
    lim = SCOPE_LIMIT.get((role, perm))
    if lim:
        return lim[0]
    meta = CATALOGUE.get(perm)
    return (ALL, *meta[3]) if meta and meta[3] else ()


def lock_info(role: str, perm: str) -> dict | None:
    """``{"state": "granted"|"denied", "reason": …}``, wenn das Recht in der Rolle fest vorgegeben ist."""
    if role == "monitor":
        return {"state": "granted" if perm in ROLE_PERMISSIONS[role] else "denied",
                "reason": "Diese Rolle ist fest vorgegeben."}
    if role in READ_ONLY_ROLES:
        return {"state": "granted" if perm in ROLE_PERMISSIONS[role] else "denied",
                "reason": "Ansichtskonto: fest vorgegeben, ändert nie etwas."}
    if perm in LOCKED_GRANT.get(role, {}):
        return {"state": "granted", "reason": LOCKED_GRANT[role][perm]}
    if perm in LOCKED_DENY.get(role, {}):
        return {"state": "denied", "reason": LOCKED_DENY[role][perm]}
    only = ASSIGNABLE_ONLY.get(role)
    if only is not None and perm not in only:
        return {"state": "denied", "reason": _ASSIGNABLE_REASON.get(role, "Für diese Rolle nicht vorgesehen.")}
    restricted = RESTRICTED_TO.get(perm)
    if restricted and role not in restricted[0]:
        return {"state": "denied", "reason": restricted[1]}
    return None


def validate_override(role: str, perm: str, granted: bool, scope: str | None) -> str | None:
    """Fehlertext, wenn die Änderung gegen eine feste Regel verstößt, sonst ``None``.
    ``scope``: ``None`` = Standard der Rolle, ``all`` = uneingeschränkt, sonst Umfang."""
    if role not in ROLES:
        return f"Unbekannte Rolle: {role}"
    if perm not in CATALOGUE:
        return f"Unbekanntes Recht: {perm}"
    lock = lock_info(role, perm)
    if lock and lock["state"] == "granted" and not granted:
        return lock["reason"]
    if lock and lock["state"] == "denied" and granted:
        return lock["reason"]
    if granted and scope is not None and scope not in scope_options(role, perm):
        return (f"Umfang „{SCOPE_LABELS.get(scope, scope)}“ ist für {ROLE_LABELS[role]} bei „{PERMISSIONS[perm]}“ "
                "nicht zulässig.")
    return None


def effective_rights(role: str, adult: bool = False,
                     overrides: dict[str, tuple[bool, str | None]] | None = None) -> tuple[set[str], dict[str, str]]:
    """Wirksame Rechte und Einschränkungen einer Rolle: Standard + Schul-Einstellungen, danach feste Regeln.

    ``overrides``: ``{recht: (erteilt, umfang|None)}``; Einträge, die feste Regeln verletzen, werden ignoriert.
    Rückgabe ``(rechte, {recht: umfang})`` – nur eingeschränkte Rechte stehen in der Umfangs-Map."""
    perms = set(ROLE_PERMISSIONS.get(role, frozenset()))
    scopes = dict(PERMISSION_SCOPES.get(role, {}))
    if role in READ_ONLY_ROLES or role == "monitor":   # fest vorgegeben
        return perms, scopes
    for perm, (granted, scope) in (overrides or {}).items():
        if validate_override(role, perm, granted, scope) is not None:
            continue
        if not granted:
            perms.discard(perm)
            scopes.pop(perm, None)
            continue
        perms.add(perm)
        if scope == ALL:
            scopes.pop(perm, None)
        elif scope is not None:
            scopes[perm] = scope
    perms |= set(LOCKED_GRANT.get(role, {}))
    perms -= set(LOCKED_DENY.get(role, {}))
    if role in ASSIGNABLE_ONLY:
        perms &= ASSIGNABLE_ONLY[role]
    perms = {p for p in perms if not (p in RESTRICTED_TO and role not in RESTRICTED_TO[p][0])}
    for (r, perm), (allowed, _reason) in SCOPE_LIMIT.items():
        if r == role and perm in perms and scopes.get(perm, ALL) not in allowed:
            scopes[perm] = allowed[0]
    if role == "schueler" and adult:
        perms |= {"student_absence.report", "student_documents.read"}
        scopes.update({"student_absence.report": "own", "student_documents.read": "own"})
    return perms, {p: s for p, s in scopes.items() if p in perms}


def permissions_for(role: str, adult: bool = False,
                    overrides: dict[str, tuple[bool, str | None]] | None = None) -> set[str]:
    """Rechte einer Rolle (Standard bzw. mit Schul-Einstellungen ``overrides``). Nur volljährige Schüler
    (``users.adult``) melden sich selbst krank („Jetzt krank melden“) und reichen eigene Dokumente ein – für
    Minderjährige tun das die Eltern."""
    return effective_rights(role, adult, overrides)[0]


def scope_for(role: str, permission: str) -> str | None:
    """Einschränkung eines Rechts für die Rolle (``None`` = uneingeschränkt)."""
    return PERMISSION_SCOPES.get(role, {}).get(permission)


def manageable_roles(role: str) -> frozenset[str]:
    return MANAGEABLE_ROLES.get(role, frozenset())


def can_manage_role(actor_role: str, target_role: str) -> bool:
    """Darf ``actor_role`` Konten der Rolle ``target_role`` verwalten?"""
    return target_role in manageable_roles(actor_role)


def teacher_class_ids(school: "School", teacher_id: str | None) -> set[str]:
    """Klassen, die eine Lehrkraft unterrichtet (irgendein Kursteil) oder als Klassenleitung führt."""
    if not teacher_id:
        return set()
    out: set[str] = set()
    for c in school.courses:
        if any(p.teacher == teacher_id for p in c.parts):
            out.update(c.classes)
    for cls in school.classes:
        if cls.class_teacher == teacher_id:
            out.add(cls.id)
    return out


def lead_class_ids(school: "School", teacher_id: str | None) -> set[str]:
    """Klassen, die eine Lehrkraft als Klassenleitung führt."""
    if not teacher_id:
        return set()
    return {cls.id for cls in school.classes if cls.class_teacher == teacher_id}


def teacher_course_ids(school: "School", teacher_id: str | None) -> set[str]:
    """Kurse, in denen die Lehrkraft mindestens einen Kursteil unterrichtet."""
    if not teacher_id:
        return set()
    return {c.id for c in school.courses if any(p.teacher == teacher_id for p in c.parts)}


def branch_class_ids(school: "School", branches) -> set[str]:
    """Klassen der Zweige (``branches``: Liste von ``{sites, grades, class_ids}``): Klasse gehört dazu, wenn ihre ID,
    ihr Standort oder ihre Klassenstufe im Zweig eingetragen ist."""
    out: set[str] = set()
    for b in branches or []:
        ids, sites, grades = set(b.get("class_ids") or []), set(b.get("sites") or []), set(b.get("grades") or [])
        for cls in school.classes:
            if cls.id in ids or (cls.site and cls.site in sites) or cls.grade in grades:
                out.add(cls.id)
    return out


def own_class_ids(school: "School", user) -> set[str]:
    """Eigene Klassen eines Benutzers (``AuthUser``): Lehrkraft → unterrichtete Klassen, Abteilungsleitung zusätzlich
    die Klassen der eigenen Zweige, Schüler/Eltern/Schulbegleitung → Klassen der (begleiteten) Kinder, sonst leer."""
    if user.role == "lehrer":
        return teacher_class_ids(school, user.teacher_id)
    if user.role == "abteilungsleitung":
        return teacher_class_ids(school, user.teacher_id) | branch_class_ids(school, getattr(user, "branches", None))
    if user.role in CHILD_ROLES:
        ids = set(user.student_ids)
        return {s.class_id for s in school.students if s.id in ids}
    return set()


def matrix() -> dict:
    """Rechtematrix (Standard) für das Frontend (``GET /api/v1/roles``); wirksame Werte: ``rights.effective_matrix``."""
    return {
        "roles": [{"id": r, "label": ROLE_LABELS[r]} for r in ROLES],
        "permissions": [{"id": p, "label": label} for p, label in PERMISSIONS.items()],
        "matrix": {r: sorted(ROLE_PERMISSIONS[r]) for r in ROLES},
        "scopes": PERMISSION_SCOPES,
        "manageable": {r: sorted(v) for r, v in MANAGEABLE_ROLES.items()},
    }
