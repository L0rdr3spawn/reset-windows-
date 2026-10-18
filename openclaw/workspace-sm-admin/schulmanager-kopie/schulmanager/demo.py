"""Erzeugt eine realistische Beispielschule (~2600 Schüler, ~170 Lehrkräfte, 2 Standorte).

Wochen: Schuljahr ab 31.08.2026 (Woche 1, ``cycle_start``), Rhythmus-Beispiele (jede 2. Woche), Unterricht Mo–Fr.

* Standort "Hauptstandort": Jahrgänge 5–8 (je 14 Klassen)
* Standort "Außenstelle Nord": Jahrgänge 9–10 (je 14 Klassen) + Oberstufe 11/12
  (je 5 Tutorengruppen mit gekoppelten Kursschienen)
* Religion/Ethik als Kopplung von je zwei Parallelklassen
* Rhythmus-Klassen: 9P/10P jeden Mittwoch Praxistag,
  10X/10Y jede 2. Woche ab Woche 1 mittwochs und jede 2. Woche ab Woche 2 dienstags+donnerstags an der
  Berufsschule (Rhythmus)
* Abendunterricht: Raster mit 12 Stunden (11./12. Stunde 16:50/17:40), Abendklasse „ABK“
  (Erwachsenenbildung, Jg. 13, erst ab 16:00), Lehrkraft „nur ab 16:00“ (VES) und zwei
  Lehrkräfte „erst ab 10:00“ (SPT, ZEH, mit Rhythmus-Variante: jede 2. Woche ab Woche 1 bzw. 2) über Zeitfenster; die erste Lehrkraft
  (Demo-Konto ``lehrer1``) hat Wunschklassen (``preferred_classes``).
"""
from __future__ import annotations

import random
from collections import defaultdict

from .models import (Course, CoursePart, Curriculum, CurriculumEntry, Duty, Holiday,
                     Room, School, SchoolClass, Settings, Site, Student, Subject,
                     SupervisionArea, Teacher, TimeRule)

SUBJECTS = [
    ("D", "Deutsch", None, True, False), ("M", "Mathematik", None, True, False),
    ("E", "Englisch", None, True, False), ("F", "Französisch", None, True, False),
    ("GE", "Geschichte", None, False, False), ("EK", "Erdkunde", None, False, False),
    ("PO", "Politik", None, False, False), ("BI", "Biologie", "Biologie", False, False),
    ("CH", "Chemie", "Chemie", False, False), ("PH", "Physik", "Physik", False, False),
    ("IF", "Informatik", "Informatik", False, False), ("KU", "Kunst", "Kunst", False, False),
    ("MU", "Musik", "Musik", False, False), ("SP", "Sport", "Sporthalle", False, True),
    ("ER", "Ev. Religion", None, False, False), ("KR", "Kath. Religion", None, False, False),
    ("PL", "Praktische Philosophie", None, False, False),
]
COLORS = ["#e57373", "#64b5f6", "#81c784", "#ffb74d", "#ba68c8", "#4db6ac", "#f06292",
          "#aed581", "#ffd54f", "#90a4ae", "#7986cb", "#a1887f", "#4dd0e1", "#dce775",
          "#ce93d8", "#80cbc4", "#bcaaa4"]

CURRICULA = {
    5: dict(D=4, M=4, E=5, BI=2, EK=2, PO=1, KU=2, MU=2, SP=3),
    6: dict(D=4, M=4, E=4, F=4, BI=2, GE=2, KU=2, MU=1, SP=3),
    7: dict(D=4, M=4, E=4, F=3, GE=2, EK=1, PH=2, CH=2, BI=1, KU=2, MU=1, SP=3),
    8: dict(D=4, M=4, E=3, F=3, GE=2, EK=2, PO=2, PH=2, CH=2, BI=2, KU=1, MU=1, SP=3),
    9: dict(D=3, M=4, E=3, F=3, GE=2, EK=1, PO=2, PH=2, CH=2, BI=2, IF=2, KU=1, MU=1, SP=3),
    10: dict(D=3, M=3, E=3, F=3, GE=2, EK=2, PO=2, PH=2, CH=2, BI=2, IF=1, KU=1, MU=1, SP=3),
}
DOUBLE = {"SP", "CH", "PH", "BI", "KU", "IF"}

COMBOS = [("D", "E"), ("D", "GE"), ("M", "PH"), ("M", "IF"), ("M", "BI"), ("E", "F"),
          ("E", "GE"), ("BI", "CH"), ("CH", "PH"), ("SP", "BI"), ("SP", "E"), ("SP", "D"),
          ("KU", "D"), ("MU", "M"), ("MU", "E"), ("F", "D"), ("EK", "PO"), ("GE", "PO"),
          ("ER", "D"), ("KR", "E"), ("PL", "D"), ("EK", "SP"), ("IF", "PH"), ("KU", "GE"),
          ("M", "EK"), ("PL", "GE"), ("ER", "GE"), ("KR", "M"), ("CH", "M"), ("KU", "E"),
          ("MU", "D"), ("PO", "SP"), ("F", "GE")]

FIRST = ["Anna", "Ben", "Clara", "David", "Emma", "Felix", "Greta", "Hannah", "Ida", "Jonas",
         "Klara", "Leon", "Mia", "Noah", "Paul", "Lena", "Sophie", "Tim", "Lukas", "Marie",
         "Elias", "Lea", "Finn", "Emilia", "Luis", "Mila", "Henry", "Ella", "Matteo", "Frieda",
         "Amir", "Aylin", "Mehmet", "Sara", "Yusuf", "Zoe", "Milan", "Nora", "Theo", "Lina"]
LAST = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
        "Schulz", "Hoffmann", "Koch", "Bauer", "Richter", "Klein", "Wolf", "Schröder",
        "Neumann", "Schwarz", "Zimmermann", "Braun", "Krüger", "Hofmann", "Hartmann", "Lange",
        "Schmitt", "Werner", "Krause", "Meier", "Lehmann", "Schmid", "Schulze", "Maier",
        "Köhler", "Herrmann", "König", "Walter", "Mayer", "Huber", "Kaiser", "Fuchs",
        "Peters", "Lang", "Scholz", "Möller", "Weiß", "Jung", "Hahn", "Schubert", "Vogel",
        "Friedrich", "Keller", "Günther", "Frank", "Berger", "Winkler", "Roth", "Beck",
        "Lorenz", "Baumann", "Franke", "Albrecht", "Schuster", "Simon", "Ludwig", "Böhm",
        "Winter", "Kraus", "Martin", "Schumacher", "Krämer", "Vogt", "Stein", "Jäger",
        "Otto", "Sommer", "Groß", "Seidel", "Heinrich", "Brandt", "Haas", "Schreiber",
        "Graf", "Schulte", "Dietrich", "Ziegler", "Kuhn", "Kühn", "Pohl", "Engel", "Horn",
        "Busch", "Bergmann", "Thomas", "Voigt", "Sauer", "Arnold", "Wolff", "Pfeiffer"]

LK_BANDS = [["D", "M", "E", "BI", "GE"], ["M", "E", "PH", "CH", "PO"]]
GK_BANDS = [["D", "E", "F", "GE", "KU", "MU"], ["M", "BI", "CH", "PH", "IF", "EK"],
            ["D", "M", "E", "PO", "PL", "ER"], ["GE", "EK", "BI", "KR", "PL", "KU"],
            ["SP", "SP", "SP", "SP", "SP", "SP"], ["E", "F", "PH", "IF", "MU", "PO"]]


EVENING_TIMES = ["16:50", "17:40"]   # 11./12. Stunde (Abendunterricht, 16:00 ist bereits die 10. Stunde)
EVENING_CLASS = "ABK"
EVENING_CURRICULUM = {"D": 3, "E": 3, "M": 3}


def build_demo(seed: int = 7, classes_per_grade: int = 14) -> School:
    rng = random.Random(seed)
    base = Settings()
    st = Settings(school_name="Gesamtschule Am Stadtpark (Demo)",
                  cycle_start="2026-08-31", site_travel_periods=1,
                  periods=len(base.period_times) + len(EVENING_TIMES),
                  period_times=list(base.period_times) + EVENING_TIMES)
    sc = School(settings=st)
    sc.sites = [Site("S1", "Hauptstandort"), Site("S2", "Außenstelle Nord")]
    sc.subjects = [Subject(i, n, r, core, 2 if dbl else 1, COLORS[k])
                   for k, (i, n, r, core, dbl) in enumerate(SUBJECTS)]

    # Räume -----------------------------------------------------------------
    special = {
        "S1": dict(Biologie=3, Chemie=3, Physik=3, Kunst=3, Musik=3, Informatik=2, Sporthalle=6, Kursraum=8),
        "S2": dict(Biologie=3, Chemie=3, Physik=3, Kunst=2, Musik=2, Informatik=3, Sporthalle=6, Kursraum=20),
    }
    for site, types in special.items():
        for typ, n in types.items():
            for i in range(1, n + 1):
                sc.rooms.append(Room(f"{site}-{typ[:3].upper()}{i}", f"{typ} {i} ({site})", typ, site,
                                     90 if typ == "Sporthalle" else 30))

    # Klassen ---------------------------------------------------------------
    letters = "abcdefghijklmnopqrstuvw"
    for grade in range(5, 11):
        site = "S1" if grade <= 8 else "S2"
        maxp = 7 if grade <= 6 else 8 if grade <= 8 else 9
        for k in range(classes_per_grade):
            cid = f"{grade}{letters[k]}"
            sc.classes.append(SchoolClass(cid, cid, grade, rng.randint(26, 29), f"{site}-R{cid}",
                                          site, maxp))
    # Rhythmus-Klassen
    sc.classes.append(SchoolClass("9P", "9P (Praxisklasse)", 9, 22, "S2-R9P", "S2", 9,
                                  [TimeRule(days=[2], note="Praxistag im Betrieb")]))
    sc.classes.append(SchoolClass("10P", "10P (Praxisklasse)", 10, 22, "S2-R10P", "S2", 9,
                                  [TimeRule(days=[2], note="Praxistag im Betrieb")]))
    for cid in ("10X", "10Y"):
        sc.classes.append(SchoolClass(cid, f"{cid} (Berufsschul-Kooperation)", 10, 20, f"S2-R{cid}", "S2", 9,
                                      [TimeRule(days=[2], note="Berufsschule (jede 2. Woche ab Woche 1)",
                                                rhythm={"every": 2, "from_week": 1, "to_week": 0}),
                                       TimeRule(days=[1, 3], note="Berufsschule (jede 2. Woche ab Woche 2)",
                                                rhythm={"every": 2, "from_week": 2, "to_week": 0})]))
    for grade in (11, 12):
        for k in range(5):
            cid = f"Q{grade - 10}-{k + 1}"
            sc.classes.append(SchoolClass(cid, f"Jg. {grade} Tutorium {k + 1}", grade, 24, f"S2-R{cid}", "S2", 10))
    for c in sc.classes:
        sc.rooms.append(Room(c.home_room, f"Klassenraum {c.name}", "Klassenraum", c.site, 32))

    # Stundentafeln -----------------------------------------------------------
    for grade, hours in CURRICULA.items():
        sc.curricula.append(Curriculum(f"ST{grade}", f"Stundentafel Jahrgang {grade}", grades=[grade],
                                       entries=[CurriculumEntry(s, h, s in DOUBLE and h >= 2) for s, h in hours.items()]))
    sc.curricula.append(Curriculum("ST-PRAX", "Praxisklassen (4 Tage)", classes=["9P", "10P"], entries=[
        CurriculumEntry(s, h, s in DOUBLE and h >= 2) for s, h in
        dict(D=4, M=4, E=3, PO=2, BI=2, PH=2, GE=2, IF=2, SP=3, PL=2).items()]))
    sc.curricula.append(Curriculum("ST-KOOP", "Berufsschul-Kooperation (Woche 1/2)", classes=["10X", "10Y"], entries=[
        CurriculumEntry(s, h, s in DOUBLE and h >= 2) for s, h in
        dict(D=3, M=3, E=3, PO=2, BI=2, PH=2, GE=2, SP=2, PL=1).items()]))
    sc.curricula.append(Curriculum("ST-OS", "Oberstufe (Kurse über Schienen)", grades=[11, 12], entries=[]))

    # Kopplungen: Religion/Ethik je zwei Parallelklassen -----------------------
    for grade in range(5, 11):
        cls = [c.id for c in sc.classes if c.grade == grade and len(c.id) <= 3 and c.id[-1].islower()]
        for i in range(0, len(cls) - 1, 2):
            pair = cls[i:i + 2]
            sc.courses.append(Course(f"REL-{'-'.join(pair)}", pair,
                                     [CoursePart("ER", label="ev"), CoursePart("KR", label="kath"),
                                      CoursePart("PL", label="PP")], 2, label=f"Religion/PP {'+'.join(pair)}"))
    # Oberstufen-Schienen
    for grade in (11, 12):
        groups = [c.id for c in sc.classes if c.grade == grade]
        q = f"Q{grade - 10}"
        for b, subjects in enumerate(LK_BANDS):
            sc.courses.append(Course(f"{q}-LK{b + 1}", groups,
                                     [CoursePart(s, label=f"{s}-LK{b + 1}") for s in subjects], 5,
                                     double=True, label=f"{q} LK-Schiene {b + 1}"))
        for b, subjects in enumerate(GK_BANDS):
            sc.courses.append(Course(f"{q}-GK{b + 1}", groups,
                                     [CoursePart(s, label=f"{s}-GK{b + 1}") for s in subjects],
                                     2 if subjects[0] == "SP" else 3,
                                     double=subjects[0] == "SP", label=f"{q} GK-Schiene {b + 1}"))

    # Lehrer ------------------------------------------------------------------
    from .planning import build_courses_from_curricula
    build_courses_from_curricula(sc)
    demand: dict[str, float] = defaultdict(float)
    for c in sc.courses:
        for p in c.parts:
            demand[p.subject] += c.hours
    capacity: dict[str, float] = defaultdict(float)
    used_short: set[str] = set()
    used_names: set[str] = set()
    n = 0
    while True:
        deficit = {s: demand[s] * 1.15 - capacity[s] for s in demand}
        s, gap = max(deficit.items(), key=lambda kv: kv[1])
        if gap <= 0:
            break
        combos = [c for c in COMBOS if s in c]
        a, b = rng.choice(combos)
        other = b if a == s else a
        hours = rng.choices([25, 20, 14], weights=[70, 18, 12])[0]
        capacity[s] += hours * 0.6
        capacity[other] += hours * 0.4
        n += 1
        last = rng.choice(LAST)
        short = (last[:3].upper().replace("Ä", "AE").replace("Ö", "OE").replace("Ü", "UE"))
        k = 1
        while short in used_short:
            short = f"{last[:2].upper()}{k}"
            k += 1
        used_short.add(short)
        unavailable = []
        if hours < 20:
            unavailable.append(TimeRule(days=[rng.randrange(5)], note="Teilzeit: freier Tag"))
        sites = [] if rng.random() < 0.8 else [rng.choice(["S1", "S2"])]
        wishes = []
        if rng.random() < 0.25:
            wishes.append(rng.choice([TimeRule(periods=[0], note="möglichst nicht zur 1. Stunde"),
                                      TimeRule(days=[4], periods=[6, 7, 8, 9], note="Freitagnachmittag frei"),
                                      TimeRule(days=[rng.randrange(5)], note="Wunsch: freier Tag")]))
        title = rng.choice(['Frau', 'Herr'])
        name = f"{title} {last}"
        k = 0
        while name in used_names:  # gleichnamige Lehrkräfte unterscheidbar machen (Doppelname, ohne Zufall)
            second = LAST[(len(used_names) + k) % len(LAST)]
            if second != last:
                name = f"{title} {last}-{second}"
            k += 1
        used_names.add(name)
        sc.teachers.append(Teacher(short, name, [s, other], hours,
                                   max_per_day=7, unavailable=unavailable, sites=sites, wishes=wishes))

    _add_evening_school(sc, used_short)

    # Schüler -----------------------------------------------------------------
    sid = 0
    part_ids = defaultdict(list)
    for c in sc.courses:
        for i, _ in enumerate(c.parts):
            part_ids[c.id].append(f"{c.id}#{i}")
    for cls in sc.classes:
        os_courses = [c for c in sc.courses if cls.id in c.classes and len(c.parts) > 1]
        for _ in range(cls.students):
            sid += 1
            courses = [rng.choice(part_ids[c.id]) for c in os_courses]
            sc.students.append(Student(f"S{sid:05d}", f"{rng.choice(FIRST)} {rng.choice(LAST)}", cls.id, courses))

    # Pausenaufsicht ------------------------------------------------------------
    sc.areas = [SupervisionArea("HOF1", "Schulhof", "S1", 3), SupervisionArea("MENSA1", "Mensa", "S1", 1),
                SupervisionArea("HOF2", "Schulhof Nord", "S2", 2), SupervisionArea("FOY2", "Foyer Nord", "S2", 1)]

    # Ferien (Beispieldaten – bitte an das eigene Bundesland anpassen) ---------
    sc.holidays = [
        Holiday("H1", "Herbstferien (Beispiel)", "2026-10-17", "2026-10-31"),
        Holiday("H2", "Weihnachtsferien (Beispiel)", "2026-12-23", "2027-01-06"),
        Holiday("H3", "Tag der Deutschen Einheit", "2026-10-03", "2026-10-03", kind="feiertag"),
    ]
    _ = Duty  # Aufsichten werden vom Aufsichtsplaner erzeugt
    # Jahrgänge statt nackter Klassenstufen-Nummern (gleicher Weg wie die Umstellung alter Dokumente)
    from .legacy import migrate_grade_profiles
    migrate_grade_profiles(sc)
    for p in sc.grade_profiles:
        p.color = COLORS[(p.grade or 0) % len(COLORS)]
    return sc


def _add_evening_school(sc: School, used_short: set[str]) -> None:
    """Abendunterricht & Lehrer-Selbstauskunft (ohne Zufallszahlen – die übrige Demo bleibt unverändert).

    * Abendklasse ABK (Erwachsenenbildung, Jg. 13) am Hauptstandort, Unterricht erst ab 16:00 (10.–12. Stunde)
    * VES „nur ab 16:00“ (Abendunterricht), SPT „erst ab 10:00“, ZEH „erst ab 10:00“ (Woche 2 freitags frei)
    * die erste Lehrkraft (Demo-Konto ``lehrer1``) gibt Wunschklassen an
    """
    from .planning import build_courses_from_curricula
    from .teacher_profile import apply_windows, normalize_windows

    st = sc.settings
    first_evening = next(i for i, t in enumerate(st.period_times) if t >= "16:00")
    cls = SchoolClass(EVENING_CLASS, "13 Abendkurs (Erwachsenenbildung)", 13, 18, f"S1-R{EVENING_CLASS}", "S1",
                      st.periods, [TimeRule(periods=list(range(first_evening)),
                                            note="Abendkurs: Unterricht erst ab 16:00")])
    sc.classes.append(cls)
    sc.rooms.append(Room(cls.home_room, f"Klassenraum {cls.name}", "Klassenraum", cls.site, 32))
    sc.curricula.append(Curriculum("ST-ABK", "Abendkurs (Erwachsenenbildung)", classes=[EVENING_CLASS], entries=[
        CurriculumEntry(s, h) for s, h in EVENING_CURRICULUM.items()]))
    build_courses_from_curricula(sc)  # erzeugt ABK-D/E/M; bestehende Kurse bleiben identisch

    def tid(wanted: str) -> str:
        short, k = wanted, 1
        while short in used_short:
            short = f"{wanted[:2]}{k}"
            k += 1
        used_short.add(short)
        return short

    workdays = list(range(st.days))
    specials = [
        # (Kürzel, Name, Fächer, Deputat, Zeitfenster, Standorte, Abendkurse)
        (tid("VES"), "Frau Vesper", ["D", "E"], 6,
         [{"days": workdays, "start": "16:00", "end": "21:00", "weeks": []}], ["S1"], ["D", "E"]),
        (tid("SPT"), "Herr Spät", ["M", "PH"], 20,
         [{"days": workdays, "start": "10:00", "end": "18:30", "weeks": []}], [], ["M"]),
        (tid("ZEH"), "Frau Zehner", ["E", "BI"], 18,
         [{"days": workdays, "start": "10:00", "end": "17:00", "weeks": [],
           "rhythm": {"every": 2, "from_week": 1, "to_week": 0}},
          {"days": workdays[:-1], "start": "10:00", "end": "17:00", "weeks": [],
           "rhythm": {"every": 2, "from_week": 2, "to_week": 0}}], [], []),
    ]
    courses = sc.index("courses")
    for short, name, subjects, hours, windows, sites, evening in specials:
        t = Teacher(short, name, subjects, hours, max_per_day=7, sites=sites,
                    time_windows=normalize_windows(windows, st))
        apply_windows(t, st)
        sc.teachers.append(t)
        for subj in evening:
            course = courses.get(f"{EVENING_CLASS}-{subj}")
            if course is not None:
                course.parts[0].teacher = short
    # Wunschklassen der ersten Lehrkraft (lehrer1): erste Klassen, deren Stundentafel ihre Fächer enthält
    if sc.teachers:
        first = sc.teachers[0]
        from .planning import curriculum_for_class
        prefs = []
        for c in sc.classes:
            cur = curriculum_for_class(sc, c.id)
            if cur and any(e.subject in first.subjects for e in cur.entries):
                prefs.append(c.id)
            if len(prefs) >= 2:
                break
        first.preferred_classes = prefs
