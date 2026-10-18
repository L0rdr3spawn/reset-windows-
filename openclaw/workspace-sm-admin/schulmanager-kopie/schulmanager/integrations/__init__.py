"""Integrationen: Datenaustausch mit anderen Schul- und Kalendersystemen.

Module (nur Standardbibliothek, alle arbeiten auf ``School`` bzw. DayPlan-Dicts):

* :mod:`.untis_gpu` – Untis-GPU/DIF-Dateien: ``export_zip(school, plans)``,
  ``import_files(files, school)`` → ``(school, warnings)``; Stundenplan, Unterricht/Kopplungen,
  Stammdaten, Schüler, Kurswahlen, Vertretungen (GPU001–006, 010, 014, 015).
* :mod:`.schulmanager_online` – ``export_package(school, plans)``: ZIP mit Untis-Dateien,
  CSV-Stammdaten und deutscher Importanleitung (``LIESMICH.txt``); dateibasiert, da
  Schulmanager Online keine öffentliche API anbietet.
* :mod:`.csv_io` – ``export_csv(school, what)`` / ``import_csv(school, what, text, mapping)``
  (``;``, UTF-8-BOM, Presets für SchILD-NRW, ASV, LUSD, Magellan; Religionswahl aus Konfession).
* :mod:`.ical` – ``calendar(school, kind, ref, date_from, date_to, plans)``: RFC-5545-Kalender
  inkl. Ferien, Wochenangaben und Vertretungen.
* :mod:`.webhooks` – ``payload(event, data)``, ``sign(body, secret)``, ``verify(...)``
  (HMAC-SHA256, Header ``X-Schulmanager-Signature``).
"""
