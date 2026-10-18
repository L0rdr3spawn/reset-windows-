import { describe, expect, it } from "vitest";
import type { Curriculum, SchoolClass } from "../../api/types";
import { profileEqual } from "../../features/teacher/windows";
import {
  curriculumOrder,
  curriculumScope,
  curriculumSearchText,
  deltasFor,
  deviation,
  duplicateSubjects,
  effectiveEntries,
  GRADE_MAX,
  GRADE_MIN,
  gradeOptions,
  matrixSubjects,
  resolveCurricula,
  setEffectiveHours,
} from "./curricula";

const cls = (id: string, grade: number): SchoolClass => ({
  id,
  name: id,
  grade,
  students: 0,
  home_room: null,
  site: "",
  max_periods_per_day: 8,
  unavailable: [],
  class_teacher: null,
});
const cur = (
  id: string,
  grades: number[],
  classes: string[] = [],
): Curriculum => ({ id, name: id, grades, classes, entries: [] });

const CLASSES = [cls("5a", 5), cls("5b", 5), cls("11IT", 11), cls("1a", 1)];

describe("Stundentafel-Zuordnung (wie planning.resolve_curricula)", () => {
  it("Klasse hat Vorrang vor Jahrgang", () => {
    const res = resolveCurricula(
      [cur("J5", [5]), cur("K5b", [], ["5b"])],
      CLASSES,
    );
    expect(res["5a"]).toEqual({
      curriculum: "J5",
      source: "grade",
      candidates: ["J5"],
      conflict: false,
    });
    expect(res["5b"]?.curriculum).toBe("K5b");
    expect(res["11IT"]?.source).toBeNull();
  });

  it("gleichrangige Tafeln sind ein Konflikt", () => {
    const list = [
      cur("J5", [5]),
      cur("J5neu", [5]),
      cur("IT1", [], ["11IT"]),
      cur("IT2", [], ["11IT"]),
    ];
    const res = resolveCurricula(list, CLASSES);
    expect(res["5a"]?.conflict).toBe(true);
    expect(res["5a"]?.curriculum).toBeNull();
    expect(res["11IT"]?.candidates).toEqual(["IT1", "IT2"]);
    const scope = curriculumScope("IT1", list, CLASSES);
    expect(scope.conflicts).toEqual([{ classId: "11IT", others: ["IT2"] }]);
  });

  it("Jahrgangstafel wird für Klassen mit eigener Tafel überdeckt", () => {
    const list = [cur("J5", [5]), cur("K5b", [], ["5b"])];
    expect(curriculumScope("J5", list, CLASSES)).toEqual({
      classes: ["5a"],
      conflicts: [],
      shadowed: ["5b"],
    });
  });

  it("Suche nach einer Klasse findet die für sie gültige Tafel (auch über den Jahrgang)", () => {
    const list = [cur("J5", [5]), cur("K5b", [], ["5b"])];
    const res = resolveCurricula(list, CLASSES);
    expect(curriculumSearchText(list[0]!, res, CLASSES)).toContain("5a");
    expect(curriculumSearchText(list[0]!, res, CLASSES)).not.toContain("5b");
    expect(curriculumSearchText(list[1]!, res, CLASSES)).toContain("5b");
  });

  it("Tafel mit Klassen ignoriert ihre Jahrgänge", () => {
    const res = resolveCurricula([cur("X", [5], ["11IT"])], CLASSES);
    expect(res["5a"]?.source).toBeNull();
    expect(res["11IT"]?.curriculum).toBe("X");
  });
});

describe("Hilfen", () => {
  it("doppelte Fächer", () => {
    expect([
      ...duplicateSubjects([
        { subject: "M", hours: 2, double: false },
        { subject: "M", hours: 1, double: false },
        { subject: "", hours: 1, double: false },
      ]),
    ]).toEqual(["M"]);
  });
  it("Jahrgänge frei aus Klassen und Auswahl", () => {
    expect(gradeOptions(CLASSES, [14])).toEqual([1, 5, 11, 14]);
  });
  it("Profilvergleich berücksichtigt Fachvorschläge", () => {
    const base = {
      subjects: ["D", "ROB"],
      preferred_classes: [],
      max_hours: 20,
      time_windows: [],
      wishes: [],
      new_subjects: [{ id: "ROB", name: "Robotik", room_type: null }],
    };
    expect(profileEqual({ ...base, subjects: ["D"] }, base)).toBe(true);
    expect(
      profileEqual({ ...base, new_subjects: [], subjects: ["D"] }, base),
    ).toBe(false);
  });
});

describe("Jahrgangsgrenzen wie im Backend (features_data.GRADE_MIN/MAX = 0–20)", () => {
  // Prüfung R1: Stammdaten-Formular begrenzte Klassen auf 1–13, obwohl Backend und Stundentafeln 0–20 erlauben
  const master = Object.values(
    import.meta.glob("../MasterDataPage.tsx", { query: "?raw", import: "default", eager: true }) as Record<string, string>,
  )[0] ?? "";
  it("Stammdaten-Klassenformular nutzt dieselben Grenzen", () => {
    expect([GRADE_MIN, GRADE_MAX]).toEqual([0, 20]);
    expect(master).toMatch(/key: 'grade',[^}]*min: GRADE_MIN, max: GRADE_MAX/);
  });
});

describe("Jahrgänge und abgeleitete Stundentafeln", () => {
  const profiles = [
    { id: "JG5", name: "Jahrgang 5", short: "5", grade: 5, color: "", description: "", department: "", curriculum: "ST5" },
    { id: "5IF", name: "5 Informatik", short: "5 IF", grade: 5, color: "#1d4ed8", description: "", department: "", curriculum: "ST5IF" },
  ];
  const base: Curriculum = { id: "ST5", name: "Stundentafel 5", grades: [], classes: [], entries: [{ subject: "D", hours: 4, double: false }, { subject: "M", hours: 4, double: false }, { subject: "KU", hours: 2, double: true }] };
  const derived: Curriculum = { id: "ST5IF", name: "5 Informatik", grades: [], classes: [], entries: [], base: "ST5", deltas: [{ subject: "IF", hours: 2, double: true }, { subject: "KU", hours: -1, double: false }] };
  const all = [base, derived];
  const classes = [{ ...cls("5a", 5), profile: "JG5" }, { ...cls("5c", 5), profile: "5IF" }, cls("5x", 5)];

  it("wirksame Zeilen = Basis plus Abweichungen", () => {
    const eff = Object.fromEntries(effectiveEntries(all, derived).map((e) => [e.subject, e.hours]));
    expect(eff).toEqual({ D: 4, M: 4, KU: 1, IF: 2 });
    expect(effectiveEntries(all, { ...derived, deltas: [{ subject: "KU", hours: -5, double: false }] }).map((e) => e.subject)).toEqual(["D", "M"]);
    expect(deviation(all, derived, "KU")).toEqual({ base: 2, delta: -1 });
    expect(deviation(all, derived, "IF")).toEqual({ base: 0, delta: 2 });
    expect(deviation(all, derived, "D")).toBeNull();
    expect(deviation(all, base, "D")).toBeNull();
  });

  it("Zuordnung über den Jahrgang, Klasse vor Jahrgang, Stufe als Altbestand", () => {
    const res = resolveCurricula(all, classes, profiles);
    expect(res["5a"]).toMatchObject({ curriculum: "ST5", source: "profile" });
    expect(res["5c"]).toMatchObject({ curriculum: "ST5IF", source: "profile" });
    expect(res["5x"]).toMatchObject({ curriculum: null, source: null });
    const own: Curriculum = { id: "KL-5c", name: "eigene", grades: [], classes: ["5c"], entries: [] };
    const res2 = resolveCurricula([...all, own], classes, profiles);
    expect(res2["5c"]).toMatchObject({ curriculum: "KL-5c", source: "class" });
    expect(curriculumScope("ST5IF", [...all, own], classes, profiles).shadowed).toEqual(["5c"]);
    expect(resolveCurricula([{ ...base, grades: [5] }], [cls("5x", 5)], [])["5x"]).toMatchObject({ source: "grade" });
  });

  it("Zelle setzen: eigene Zeile bzw. Abweichung; 0 streicht das Fach", () => {
    const own = setEffectiveHours(all, base, "M", 5);
    expect(own.entries.find((e) => e.subject === "M")?.hours).toBe(5);
    expect(setEffectiveHours(all, base, "D", 0).entries.map((e) => e.subject)).toEqual(["M", "KU"]);
    expect(setEffectiveHours(all, base, "SP", 3).entries.at(-1)).toEqual({ subject: "SP", hours: 3, double: false });
    const d = setEffectiveHours(all, derived, "KU", 2, true);
    expect(d.deltas?.find((x) => x.subject === "KU")).toBeUndefined();   // wieder wie Basis
    expect(effectiveEntries(all, setEffectiveHours(all, derived, "D", 0)).map((e) => e.subject)).toEqual(["M", "KU", "IF"]);
    expect(deltasFor(base.entries, [{ subject: "D", hours: 4, double: false }, { subject: "M", hours: 5, double: false }])).toEqual([
      { subject: "M", hours: 1, double: false },
      { subject: "KU", hours: -2, double: true },
    ]);
  });

  it("Spaltenreihenfolge und Fächer der Matrix", () => {
    const os: Curriculum = { id: "OS", name: "Oberstufe", grades: [], classes: [], entries: [{ subject: "PH", hours: 3, double: false }] };
    const sonder: Curriculum = { id: "S", name: "Praxis", grades: [], classes: ["9P"], entries: [] };
    const order = curriculumOrder([os, sonder, derived, base], [...profiles, { ...profiles[0]!, id: "JG12", name: "Jahrgang 12", grade: 12, curriculum: "OS" }]);
    expect(order.map((c) => c.id)).toEqual(["ST5IF", "ST5", "OS", "S"]);
    expect(matrixSubjects([base, derived, os], [{ id: "PH" }, { id: "D" }, { id: "M" }, { id: "KU" }])).toEqual(["PH", "D", "M", "KU", "IF"]);
    expect(curriculumSearchText(derived, resolveCurricula(all, classes, profiles), classes, profiles)).toContain("5 informatik 5 if");
  });
});
