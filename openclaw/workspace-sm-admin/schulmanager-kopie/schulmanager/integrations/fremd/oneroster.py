"""OneRoster 1.2 – CSV-Bindung: lesen (→ Bundle) und schreiben (Stammdaten).

Spaltenlisten nach der Spezifikation „1EdTech OneRoster 1.2 CSV Binding“
(https://www.imsglobal.org/spec/oneroster/v1p2/bind/csv); die ausgezogene Liste liegt unter
``tests/fixtures/fremdsysteme/oneroster/oneroster_v1p2_csv_columns.json``.

Lesen: ``orgs``, ``academicSessions``, ``courses``, ``classes`` (``homeroom`` → Klasse, ``scheduled`` → Kurs), ``users``,
``roles`` (1.2) bzw. ``users.role`` (1.1), ``enrollments``, ``demographics`` (Geburtsdatum), ``categories``, ``lineItems``,
``results``. Datensätze mit ``status = tobedeleted`` werden übersprungen. Toleranz: Komma/Semikolon, BOM, Windows-1252,
Dateien in Unterordnern (ZIP), Groß-/Kleinschreibung der Dateinamen.

Schreiben: :func:`export_zip` liefert ``manifest``, ``orgs``, ``academicSessions``, ``courses``, ``classes``, ``users``,
``roles``, ``enrollments``, ``demographics`` aus dem Planungsdokument (ohne Noten – das Notenbuch hat eigene Exporte).
"""
from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime, timezone
from typing import Optional

from .._common import decode_bytes, grade_from_name
from .model import Bundle, FCourse, FEnrol, FGradeItem, FPerson
from .text import clean, parse_date

COLUMNS = {
    "orgs": ["sourcedId", "status", "dateLastModified", "name", "type", "identifier", "parentSourcedId"],
    "academicSessions": ["sourcedId", "status", "dateLastModified", "title", "type", "startDate", "endDate",
                         "parentSourcedId", "schoolYear"],
    "courses": ["sourcedId", "status", "dateLastModified", "schoolYearSourcedId", "title", "courseCode", "grades",
                "orgSourcedId", "subjects", "subjectCodes"],
    "classes": ["sourcedId", "status", "dateLastModified", "title", "grades", "courseSourcedId", "classCode", "classType",
                "location", "schoolSourcedId", "termSourcedIds", "subjects", "subjectCodes", "periods"],
    "users": ["sourcedId", "status", "dateLastModified", "enabledUser", "username", "userIds", "givenName", "familyName",
              "middleName", "identifier", "email", "sms", "phone", "agentSourcedIds", "grades", "password",
              "userMasterIdentifier", "preferredGivenName", "preferredMiddleName", "preferredFamilyName",
              "primaryOrgSourcedId", "pronouns"],
    "roles": ["sourcedId", "status", "dateLastModified", "userSourcedId", "roleType", "role", "beginDate", "endDate",
              "orgSourcedId", "userProfileSourcedId"],
    "enrollments": ["sourcedId", "status", "dateLastModified", "classSourcedId", "schoolSourcedId", "userSourcedId",
                    "role", "primary", "beginDate", "endDate"],
    "demographics": ["sourcedId", "status", "dateLastModified", "birthDate", "sex", "americanIndianOrAlaskaNative",
                     "asian", "blackOrAfricanAmerican", "nativeHawaiianOrOtherPacificIslander", "white",
                     "demographicRaceTwoOrMoreRaces", "hispanicOrLatinoEthnicity", "countryOfBirthCode",
                     "stateOfBirthAbbreviation", "cityOfBirth", "publicSchoolResidenceStatus"],
    "categories": ["sourcedId", "status", "dateLastModified", "title", "weight"],
    "lineItems": ["sourcedId", "status", "dateLastModified", "title", "description", "assignDate", "dueDate",
                  "classSourcedId", "categorySourcedId", "academicSessionSourcedId", "resultValueMin", "resultValueMax",
                  "schoolSourcedId"],
    "results": ["sourcedId", "status", "dateLastModified", "lineItemSourcedId", "studentSourcedId", "scoreStatus", "score",
                "scoreDate", "comment", "textScore", "classSourcedId", "inProgress", "incomplete", "late", "missing"],
}
GRADED = {"fully graded", "partially graded"}


def _table(files: dict[str, bytes], name: str, b: Bundle) -> list[dict[str, str]]:
    want = f"{name}.csv".lower()
    key = next((n for n in files if n.replace("\\", "/").rsplit("/", 1)[-1].lower() == want), None)
    if key is None:
        return []
    text, _enc = decode_bytes(files[key])
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    delim = ";" if first.count(";") > first.count(",") else ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    if not rows:
        return []
    head = [h.strip() for h in rows[0]]
    required = {"sourcedId"}
    if not required <= set(head):
        b.problem("format", f"{name}.csv", "Spalte sourcedId fehlt – Datei übersprungen")
        return []
    out = []
    for line, row in enumerate(rows[1:], start=2):
        if not any(c.strip() for c in row):
            continue
        rec = {h: (row[i].strip() if i < len(row) else "") for i, h in enumerate(head)}
        if not rec.get("sourcedId"):
            b.problem("zeile", f"{name}.csv:{line}", "sourcedId fehlt – Zeile übersprungen")
            continue
        if rec.get("status", "").lower() == "tobedeleted":
            continue
        rec["_line"] = str(line)
        out.append(rec)
    return out


def _num(v: str) -> Optional[float]:
    try:
        return float(v.replace(",", ".")) if v.strip() else None
    except ValueError:
        return None


def read_oneroster(files: dict[str, bytes], *, instance: str = "standard", today: Optional[datetime] = None) -> Bundle:
    b = Bundle(system="oneroster", source="OneRoster CSV", instance=instance)
    today_iso = (today or datetime.now(timezone.utc)).date().isoformat()
    for n, d in files.items():
        if n.lower().endswith("manifest.csv"):
            text, _e = decode_bytes(d)
            for r in csv.reader(io.StringIO(text)):
                if len(r) >= 2 and r[0].strip() == "oneroster.version":
                    b.version = r[1].strip()
    orgs = _table(files, "orgs", b)
    schools = [o for o in orgs if o.get("type") == "school"] or orgs
    if schools:
        b.info["school"] = schools[0].get("name", "")
    sessions = _table(files, "academicSessions", b)
    if sessions:
        b.info["sessions"] = [{"title": s.get("title"), "type": s.get("type"), "start": s.get("startDate"),
                               "end": s.get("endDate")} for s in sessions]
    courses = {c["sourcedId"]: c for c in _table(files, "courses", b)}
    demo = {d["sourcedId"]: parse_date(d.get("birthDate", "")) for d in _table(files, "demographics", b)}
    roles: dict[str, str] = {}
    for r in _table(files, "roles", b):
        roles.setdefault(r.get("userSourcedId", ""), r.get("role", ""))
    classes = {c["sourcedId"]: c for c in _table(files, "classes", b)}
    enrolls = _table(files, "enrollments", b)
    role_from_enrol: dict[str, str] = {}
    for e in enrolls:
        role_from_enrol.setdefault(e.get("userSourcedId", ""), e.get("role", ""))
    for u in _table(files, "users", b):
        sid = u["sourcedId"]
        raw = (u.get("role") or roles.get(sid) or role_from_enrol.get(sid) or "").lower()
        role = "teacher" if raw in ("teacher", "aide") else "student" if raw == "student" else "other"
        name_mid = u.get("middleName", "")
        first = clean(u.get("givenName", "")) + (f" {clean(name_mid)}" if name_mid else "")
        enabled = u.get("enabledUser", "true").strip().lower() not in ("false", "0", "nein")
        b.persons[sid] = FPerson(src_id=sid, first=first.strip(), last=clean(u.get("familyName", "")), role=role,
                                 email=clean(u.get("email", "")).lower(), username=clean(u.get("username", "")),
                                 ident=clean(u.get("identifier", "")), birth=demo.get(sid, ""),
                                 status="active" if enabled else "suspended")
        if not (b.persons[sid].first or b.persons[sid].last):
            b.problem("zeile", f"users.csv:{u['_line']}", "Name fehlt")
            del b.persons[sid]
    homeroom: dict[str, dict] = {}
    for cid, c in classes.items():
        code = clean(c.get("classCode", "")) or clean(c.get("title", ""))
        if c.get("classType", "").lower() == "homeroom":
            grade_raw = c.get("grades", "").split(",")[0].strip().lstrip("0")
            grade = int(grade_raw) if grade_raw.isdigit() else grade_from_name(code)
            if grade is not None:
                b.classes.append({"id": code, "name": clean(c.get("title", "")) or code, "grade": grade})
            else:
                b.problem("zeile", f"classes.csv:{c['_line']}", f"Klasse {code}: Jahrgang nicht erkennbar")
            homeroom[cid] = {"code": code}
            continue
        crs = courses.get(c.get("courseSourcedId", ""), {})
        b.courses[cid] = FCourse(src_id=cid, short=code, full=clean(c.get("title", "")), ident=code,
                                 category=clean(crs.get("title", "")), grade=c.get("grades", ""),
                                 subject=c.get("subjects", ""), kind="course")
    for e in enrolls:
        cid, uid = e.get("classSourcedId", ""), e.get("userSourcedId", "")
        if uid not in b.persons:
            if uid:
                b.problem("referenz", f"enrollments.csv:{e['_line']}", f"Person {uid} unbekannt")
            continue
        end = parse_date(e.get("endDate", ""))
        begin = parse_date(e.get("beginDate", ""))
        active = not (end and end < today_iso) and not (begin and begin > today_iso)
        if cid in homeroom:
            if b.persons[uid].role == "student" and active:
                b.persons[uid].class_hint = homeroom[cid]["code"]
            continue
        if cid not in b.courses:
            b.problem("referenz", f"enrollments.csv:{e['_line']}", f"Klasse {cid} unbekannt")
            continue
        r = (e.get("role", "") or "").lower()
        b.enrols.append(FEnrol(cid, uid, "teacher" if r in ("teacher", "aide") else "student", active,
                               "" if active else "beendet"))
    cats = {c["sourcedId"]: c.get("title", "") for c in _table(files, "categories", b)}
    items: dict[str, FGradeItem] = {}
    for li in _table(files, "lineItems", b):
        cid = li.get("classSourcedId", "")
        if cid not in b.courses:
            continue
        items[li["sourcedId"]] = FGradeItem(src_id=li["sourcedId"], course=cid, title=clean(li.get("title", ""), 120) or "Bewertung",
                                            kind="manual", max_points=_num(li.get("resultValueMax", "")),
                                            date=parse_date(li.get("dueDate", "")) or parse_date(li.get("assignDate", "")),
                                            category=cats.get(li.get("categorySourcedId", ""), ""))
    for r in _table(files, "results", b):
        it = items.get(r.get("lineItemSourcedId", ""))
        pid = r.get("studentSourcedId", "")
        if it is None or pid not in b.persons:
            continue
        if r.get("scoreStatus", "").lower() not in GRADED:
            continue
        score = _num(r.get("score", ""))
        text = clean(r.get("textScore", ""))
        if score is None and not text:
            b.problem("zeile", f"results.csv:{r['_line']}", "Ergebnis ohne Wert")
            continue
        it.results[pid] = (score, "" if score is not None else text)
    b.grade_items = [i for i in items.values() if i.results]
    enrolled = {e.person for e in b.enrols}
    b.info["enrolled_persons"] = len(enrolled)
    return b


# ===================================================================================== Schreiben
def _csv(name: str, rows: list[dict]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    cols = COLUMNS[name]
    w.writerow(cols)
    for r in rows:
        w.writerow([r.get(c, "") for c in cols])
    return buf.getvalue().encode("utf-8")


def export_zip(school, *, school_name: str = "Schule", school_year_end: int = 0) -> bytes:
    """Planungsdokument → OneRoster-1.2-CSV-ZIP (Stammdaten). ``sourcedId`` ist die interne ID mit Präfix."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    org = "org-schule"
    year = school_year_end or (datetime.now().year + (1 if datetime.now().month >= 8 else 0))
    base = {"status": "active", "dateLastModified": now}
    rows: dict[str, list[dict]] = {k: [] for k in COLUMNS}
    rows["orgs"].append({**base, "sourcedId": org, "name": school_name, "type": "school", "identifier": ""})
    rows["academicSessions"].append({**base, "sourcedId": f"as-{year}", "title": f"Schuljahr {year - 1}/{year}",
                                     "type": "schoolYear", "startDate": f"{year - 1}-08-01", "endDate": f"{year}-07-31",
                                     "schoolYear": str(year)})
    subjects = {s.id: s.name for s in school.subjects}
    for s in school.subjects:
        rows["courses"].append({**base, "sourcedId": f"crs-{s.id}", "title": s.name, "courseCode": s.id,
                                "orgSourcedId": org, "subjects": s.name, "subjectCodes": s.id})
    for c in school.classes:
        rows["classes"].append({**base, "sourcedId": f"cls-{c.id}", "title": c.name, "grades": f"{c.grade:02d}",
                                "courseSourcedId": "", "classCode": c.id, "classType": "homeroom",
                                "schoolSourcedId": org, "termSourcedIds": f"as-{year}"})
    for course in school.courses:
        for i, part in enumerate(course.parts):
            rows["classes"].append({**base, "sourcedId": f"cls-{course.id}#{i}",
                                    "title": course.label or f"{subjects.get(part.subject, part.subject)} {','.join(course.classes)}",
                                    "courseSourcedId": f"crs-{part.subject}", "classCode": f"{course.id}#{i}",
                                    "classType": "scheduled", "schoolSourcedId": org, "termSourcedIds": f"as-{year}",
                                    "subjects": subjects.get(part.subject, ""), "subjectCodes": part.subject})
    for t in school.teachers:
        first, _, last = t.name.rpartition(" ")
        rows["users"].append({**base, "sourcedId": f"usr-{t.id}", "enabledUser": "true", "username": t.id,
                              "givenName": first, "familyName": last or t.name, "identifier": t.id, "email": t.email,
                              "primaryOrgSourcedId": org})
        rows["roles"].append({**base, "sourcedId": f"role-{t.id}", "userSourcedId": f"usr-{t.id}", "roleType": "primary",
                              "role": "teacher", "orgSourcedId": org})
        for course in school.courses:
            for i, part in enumerate(course.parts):
                if part.teacher == t.id:
                    rows["enrollments"].append({**base, "sourcedId": f"enr-{t.id}-{course.id}#{i}",
                                                "classSourcedId": f"cls-{course.id}#{i}", "schoolSourcedId": org,
                                                "userSourcedId": f"usr-{t.id}", "role": "teacher", "primary": "true"})
    by_course: dict[str, list] = {}
    for course in school.courses:
        for i, part in enumerate(course.parts):
            by_course.setdefault(f"{course.id}#{i}", [])
    for s in school.students:
        first, _, last = s.name.rpartition(" ")
        rows["users"].append({**base, "sourcedId": f"usr-{s.id}", "enabledUser": "true", "username": s.id,
                              "givenName": first, "familyName": last or s.name, "identifier": s.id,
                              "primaryOrgSourcedId": org})
        rows["roles"].append({**base, "sourcedId": f"role-{s.id}", "userSourcedId": f"usr-{s.id}", "roleType": "primary",
                              "role": "student", "orgSourcedId": org})
        rows["enrollments"].append({**base, "sourcedId": f"enr-{s.id}-home", "classSourcedId": f"cls-{s.class_id}",
                                    "schoolSourcedId": org, "userSourcedId": f"usr-{s.id}", "role": "student",
                                    "primary": "true"})
        if s.birth_date:
            rows["demographics"].append({**base, "sourcedId": f"usr-{s.id}", "birthDate": s.birth_date})
        for course in school.courses:
            if s.class_id in course.classes:
                for i, part in enumerate(course.parts):
                    if part.students is None or s.id in part.students:
                        rows["enrollments"].append({**base, "sourcedId": f"enr-{s.id}-{course.id}#{i}",
                                                    "classSourcedId": f"cls-{course.id}#{i}", "schoolSourcedId": org,
                                                    "userSourcedId": f"usr-{s.id}", "role": "student"})
    manifest = "propertyName,value\r\nmanifest.version,1.0\r\noneroster.version,1.2\r\n" + "".join(
        f"file.{n},{'bulk' if rows[n] else 'absent'}\r\n" for n in COLUMNS if n not in ("categories", "lineItems", "results"))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.csv", manifest)
        for name in COLUMNS:
            if name in ("categories", "lineItems", "results"):
                continue
            zf.writestr(f"{name}.csv", _csv(name, rows[name]))
    return buf.getvalue()
