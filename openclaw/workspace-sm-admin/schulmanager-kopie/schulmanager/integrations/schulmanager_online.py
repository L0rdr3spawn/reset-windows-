"""Exportpaket für *Schulmanager Online* und andere Schulsysteme.

Schulmanager Online (schulmanager-online.de) bietet nach unserem Kenntnisstand
**keine öffentliche API** für Stunden-/Vertretungspläne. Der Austausch läuft daher
dateibasiert über das von dort (und vielen anderen Systemen) unterstützte
Untis-Format (GPU-/DIF-Dateien) plus CSV-Stammdaten. :func:`export_package`
erzeugt ein ZIP mit:

* ``untis/GPU0xx.TXT`` – Stundenplan, Unterricht, Klassen, Lehrkräfte, Räume,
  Fächer, Schüler, Kurswahlen, Vertretungen (Windows-1252, siehe :mod:`.untis_gpu`)
* ``csv/*.csv`` – Schüler, Lehrkräfte, Klassen, Räume, Fächer, Unterricht
  (``;``, UTF-8 mit BOM, siehe :mod:`.csv_io`)
* ``LIESMICH.txt`` – Schritt-für-Schritt-Anleitung (Deutsch)
* ``manifest.json`` – maschinenlesbare Übersicht (Dateien, Zeilen, Zeitraum)
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any, Optional

from ..calendar_utils import base_start, default_days
from ..models import School
from . import csv_io, untis_gpu
from ._common import plans_by_date

__all__ = ["export_package", "readme_text"]

_CSV_FILES = [
    ("schueler.csv", "students", "Schüler: ID;Nachname;Vorname;Klasse;Kurse"),
    ("lehrer.csv", "teachers", "Lehrkräfte: Kürzel;Name;Fächer;Deputat;…"),
    ("klassen.csv", "classes", "Klassen: Kürzel;Name;Jahrgang;Schülerzahl;Klassenraum;…"),
    ("raeume.csv", "rooms", "Räume: Kürzel;Name;Raumtyp;Standort;Kapazität"),
    ("faecher.csv", "subjects", "Fächer: Kürzel;Name;Raumtyp;Hauptfach;…"),
    ("unterricht.csv", "lessons", "Stundenplan als Tabelle (eine Zeile je Block)"),
]
_GPU_DESC = {
    "GPU001.TXT": "Stundenplan (eine Zeile je Stunde, Klasse und Kopplungszeile)",
    "GPU002.TXT": "Unterricht (Wochenstunden, Kopplungen, Lehrkräfte, Fächer)",
    "GPU003.TXT": "Klassen",
    "GPU004.TXT": "Lehrkräfte",
    "GPU005.TXT": "Räume",
    "GPU006.TXT": "Fächer",
    "GPU010.TXT": "Schüler",
    "GPU014.TXT": "Vertretungen (aus dem gewählten Zeitraum)",
    "GPU015.TXT": "Kurswahlen der Schüler (Kopplungen/Oberstufe)",
}


def readme_text(school: School, dates: list[str], created: datetime, files: list[tuple[str, int]]) -> str:
    """Deutsche Importanleitung (Inhalt von ``LIESMICH.txt``)."""
    span = f"{dates[0]} bis {dates[-1]} ({len(dates)} Tag(e))" if dates else "keine (nur Stundenplan)"
    listing = "\n".join(f"  {path:<24} {rows:>6} Zeilen" for path, rows in files)
    return f"""SCHULMANAGER – EXPORTPAKET FÜR SCHULMANAGER ONLINE UND ANDERE SCHULSYSTEME
==========================================================================

Schule:        {school.settings.school_name}
Erstellt am:   {created.astimezone(timezone.utc):%d.%m.%Y %H:%M} UTC
Vertretungen:  {span}
Wochen:        laufende Schulwochen 1 … 52 (Wochenangaben als Liste oder Rhythmus)

INHALT
------
{listing}
  LIESMICH.txt             diese Anleitung
  manifest.json            maschinenlesbare Übersicht

untis/ = Untis-Austauschformat („GPU-/DIF-Dateien“): Komma-getrennt, Texte in
Anführungszeichen, Zeichensatz Windows-1252 (ANSI), Tage 1 = Montag … 7 = Sonntag, Stunden ab 1.
csv/   = Tabellen für Excel/LibreOffice: Semikolon-getrennt, UTF-8 mit BOM.

WICHTIG VORAB
-------------
* Schnittstelle: Schulmanager Online bietet nach unserem Kenntnisstand keine
  öffentliche Programmierschnittstelle (API) für Stunden- und Vertretungspläne.
  Der Austausch erfolgt deshalb über Dateien im Untis-Format, die Schulmanager
  Online (und viele andere Systeme) importieren können. Menüpunkte können je nach
  Version anders heißen – maßgeblich ist die Online-Hilfe Ihres Systems.
* Datenschutz (DSGVO): Das Paket enthält personenbezogene Daten (Namen, Klassen,
  Kurswahlen, Vertretungen). Nur über sichere Wege weitergeben, nicht per
  unverschlüsselter E-Mail versenden, nach dem Import löschen.
* Testen: Den ersten Import bitte mit einer Testinstanz bzw. kurz vor einem
  Wochenwechsel durchführen und Stichproben prüfen (eine Klasse, eine Lehrkraft,
  ein Oberstufenkurs, eine Religions-/Ethik-Kopplung).
* Kürzel: Andere Systeme ordnen Lehrkräfte, Klassen, Räume und Fächer über die
  Kürzel zu. Bitte Kürzel in beiden Systemen identisch halten.

A) STUNDENPLAN IN SCHULMANAGER ONLINE IMPORTIEREN
-------------------------------------------------
1. ZIP-Datei entpacken (Windows: Rechtsklick → „Alle extrahieren…“).
2. In Schulmanager Online mit einem Konto anmelden, das den Stundenplan
   verwalten darf (Administration/Stundenplanung).
3. Das Stundenplan-Modul öffnen und den Import aus Untis wählen
   (Bezeichnung z. B. „Stundenplan importieren“ → „Untis“ / „GPU-Dateien“).
4. Dateien aus dem Ordner „untis“ hochladen: mindestens GPU001.TXT
   (Stundenplan); werden weitere Dateien angeboten, zusätzlich GPU002.TXT
   (Unterricht/Kopplungen), GPU003–GPU006 (Klassen, Lehrkräfte, Räume, Fächer)
   sowie GPU010/GPU015 (Schüler, Kurswahlen für Kurse und Religion/Ethik).
5. Gültigkeitsbeginn wählen (in der Regel der Montag der kommenden Woche).
6. Zuordnungsdialog prüfen: unbekannte Kürzel zuordnen oder vorher angleichen.
7. Import abschließen und Stichproben prüfen. Wochen: Stunden, die nur in
   einzelnen Wochen oder im Rhythmus stattfinden, stehen unter einer eigenen
   Unterrichtsnummer mit dem Text „(Woche 1)“ bzw. „(Woche 1, 3)“ – ggf. in
   Schulmanager Online die Wochenzuordnung (Periodizität) dieser Stunden
   kontrollieren.

B) VERTRETUNGSPLAN ÜBERTRAGEN
----------------------------
1. Im Schulmanager unter „Import/Export“ das Paket für den gewünschten Zeitraum
   erzeugen (z. B. heute und morgen). Die Vertretungen stehen in
   untis/GPU014.TXT.
2. In Schulmanager Online im Vertretungsplan-Bereich den Import aus Untis
   (GPU014 / „Vertretungen aus Untis“) wählen und GPU014.TXT hochladen.
3. Bei jeder Änderung wiederholen (typisch: morgens vor Unterrichtsbeginn und
   mittags für den Folgetag).
4. Automatisierung: Das Paket kann per API-Token zeitgesteuert abgerufen werden
   (GET /api/v1/export/schulmanager-online.zip, z. B. per Aufgabenplanung/cron und
   curl). Das Hochladen in Schulmanager Online bleibt ein manueller Schritt,
   solange dort keine Schnittstelle angeboten wird. Für eigene Systeme stehen
   signierte Webhooks (HMAC-SHA256, Header X-Schulmanager-Signature) bereit.

C) STAMMDATEN (SCHÜLER, LEHRKRÄFTE, KLASSEN)
-------------------------------------------
* csv/schueler.csv, csv/lehrer.csv, csv/klassen.csv: in Schulmanager Online über
  den CSV-/Excel-Import der jeweiligen Verwaltung einlesen und Spalten zuordnen.
* Empfehlung: Schülerdaten möglichst direkt aus der Schulverwaltung (SchILD-NRW,
  ASV-BW/ASV-BY, LUSD, Magellan …) übernehmen und aus diesem Paket nur
  Stundenplan und Vertretungen verwenden – so entstehen keine Doppelungen.
* Spalte „Kurse“: Kursteile im Format „Kurs-ID#Teil“ (z. B. Religion/Ethik,
  Oberstufenkurse).

D) ANDERE SYSTEME
-----------------
* Untis: Datei → Import/Export → Untis → DIF-/GPU-Dateien importieren
  (Achtung: überschreibt ggf. vorhandene Daten – vorher sichern).
* Schulserver und Schul-Apps (z. B. IServ-Stundenplanmodul, DieSchulApp,
  Vertretungsplan-Uploader von Schulportalen, Infobildschirme): akzeptieren
  meist GPU001.TXT (Stundenplan) und GPU014.TXT (Vertretungen); manche zusätzlich
  GPU002.TXT für Gruppen/Kopplungen.
* Tabellenkalkulation: csv/*.csv direkt mit Excel oder LibreOffice öffnen.
* Kalender-Apps (Outlook, Google, Apple): statt Dateien den persönlichen
  iCal-Link aus dem Profil im Schulmanager abonnieren (aktualisiert sich selbst).

E) ZURÜCK IN DEN SCHULMANAGER
----------------------------
* Untis-Dateien (aus Untis oder aus diesem Paket): „Import/Export“ → „Untis“
  (einzelne GPU-Dateien oder das ganze ZIP hochladen).
* Schülerlisten aus SchILD-NRW/ASV/LUSD/Magellan: „Import/Export“ → „CSV“ mit
  passendem Preset; Konfession/Religionsunterricht wird automatisch der
  Religions-/Ethik-Kopplung der Klasse zugeordnet.

TECHNISCHE HINWEISE
-------------------
* Kopplungen (Religion/Ethik, Oberstufenschienen) = mehrere Zeilen mit derselben
  Unterrichtsnummer in GPU001/GPU002.
* GPU002 Feld 39 und GPU006 Feld 16 enthalten eine technische Kennung „sm1;…“
  für den verlustfreien Rückimport in den Schulmanager; andere Systeme können
  sie ignorieren.
* Einige Untis-Felder (u. a. Deputat in GPU004, Doppelstunden in GPU002, das
  Art-Bitfeld in GPU014) sind nach bestem Wissen belegt. Bitte vor einem
  Produktivimport mit der eigenen Untis-Version gegenprüfen.
"""


def export_package(school: School, plans: Any = None, *, created: Optional[datetime] = None,
                   include_students: bool = True) -> bytes:
    """ZIP-Paket (Untis-GPU + CSV + LIESMICH.txt + manifest.json) als Bytes.

    ``plans``: Vertretungspläne als Liste von DayPlan-Dicts oder ``{Datum: DayPlan}``
    (``None`` = nur Stundenplan/Stammdaten). ``include_students=False`` lässt
    Schülerdaten (GPU010/GPU015/schueler.csv) weg (Datensparsamkeit).
    """
    created = created or datetime.now(timezone.utc)
    plans_d = plans_by_date(plans)
    gpu = untis_gpu.export_files(school, list(plans_d.values()))
    if not include_students:
        gpu = {k: v for k, v in gpu.items() if k not in ("GPU010.TXT", "GPU015.TXT")}
    files: dict[str, bytes] = {f"untis/{name}": data for name, data in gpu.items()}
    manifest_files = [{"path": f"untis/{name}", "description": _GPU_DESC.get(name, ""), "encoding": "windows-1252",
                       "rows": data.count(b"\r\n")} for name, data in gpu.items()]
    for fname, what, desc in _CSV_FILES:
        if what == "students" and not include_students:
            continue
        text = csv_io.export_csv(school, what)
        data = text.encode("utf-8")
        files[f"csv/{fname}"] = data
        manifest_files.append({"path": f"csv/{fname}", "description": desc, "encoding": "utf-8-sig",
                               "rows": max(0, text.count("\r\n") - 1)})
    dates = sorted(plans_d)
    listing = [(f["path"], f["rows"]) for f in manifest_files]
    files["LIESMICH.txt"] = ("﻿" + readme_text(school, dates, created, listing)).replace(
        "\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
    manifest = {
        "format": "schulmanager-export", "version": 1, "target": "schulmanager-online",
        "created_at": created.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "school": school.settings.school_name,
        "week_numbering": school.settings.week_numbering,
        "school_year_start": base_start(school.settings).isoformat(),
        "school_days": default_days(school.settings),
        "substitution_dates": dates, "files": manifest_files,
        "counts": {"classes": len(school.classes), "teachers": len(school.teachers), "rooms": len(school.rooms),
                   "subjects": len(school.subjects), "courses": len(school.courses), "lessons": len(school.lessons),
                   "students": len(school.students) if include_students else 0,
                   "substitution_entries": sum(len(p.get("entries") or []) for p in plans_d.values())},
    }
    files["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in ["LIESMICH.txt", "manifest.json"] + sorted(p for p in files if "/" in p):
            zf.writestr(path, files[path])
    return buf.getvalue()
