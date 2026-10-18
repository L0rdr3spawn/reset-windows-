import { createElement, isValidElement, type ReactElement, type ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import type { AbsentClassDetail, AbsentTeacherDetail, Entry, TeacherStat } from '../../api/types';
import { AbsentTeachersCard } from '../../components/AbsentTeachersCard';
import { EntryTable } from '../../components/EntryTable';
import {
  ABSENCE_REASON_FIELD,
  casesLabel,
  classAbsenceRows,
  classAbsenceText,
  filterClassRows,
  groupWithClassRows,
  periodsLabel,
  statRows,
  statsWeek,
  withoutClassAbsences,
} from '../substitution';

function entry(id: string, extra: Partial<Entry>): Entry {
  return {
    id,
    date: '2026-10-07',
    period: 0,
    period_label: '1.',
    time: '07:55',
    kind: 'vertretung',
    classes: ['7a'],
    subject: 'M',
    teacher: 'MUE',
    substitute: 'SCH',
    room: 'R1',
    new_room: null,
    moved_from: null,
    lesson_id: 'L1',
    part: 0,
    note: '',
    warning: false,
    manual: false,
    site: 'S1',
    ...extra,
  };
}

const details: AbsentClassDetail[] = [
  { class: '7a', name: '7a', source: 'absence', full_day: true, periods: [], reason: 'Wandertag' },
  { class: '10X', name: '10X', source: 'rhythm', full_day: true, periods: [], reason: 'Berufsschule' },
  { class: '5b', name: '5b', source: 'absence', full_day: false, periods: [3, 4], reason: 'Theater' },
];

// Wandertag der 7a: sechs Stunden „Klasse abwesend“ vom Server; 10X nur laut Rhythmus
const wandertag = [0, 1, 2, 3, 4, 5].map((p) =>
  entry(`ka${p}`, { kind: 'klasse_abwesend', period: p, substitute: null, note: 'Klasse abwesend: Wandertag', source: 'absence' }),
);
const plan = [
  ...wandertag,
  entry('rh', { kind: 'klasse_abwesend', classes: ['10X'], substitute: null, note: 'Klasse abwesend: Berufsschule', source: 'rhythm' }),
  entry('v', { classes: ['8c'], period: 2 }),
];

describe('B-04: abwesende Lehrkräfte und Klassen', () => {
  it('beschreibt Stunden als Bereiche oder ganztägig', () => {
    expect(periodsLabel([], false)).toBe('ganztägig');
    expect(periodsLabel([1, 2], true)).toBe('ganztägig');
    expect(periodsLabel([2, 3, 4])).toBe('3.–5. Std.');
    expect(periodsLabel([4, 0, 2, 3])).toBe('1., 3.–5. Std.');
    expect(casesLabel(1)).toBe('1 Fall');
    expect(casesLabel(0)).toBe('0 Fälle');
  });

  it('zeigt nur gemeldete Klassen-Abwesenheiten, eine Zeile je Klasse, Rhythmus nie (Kriterium 4/5)', () => {
    const rows = classAbsenceRows(details);
    expect(rows.map((r) => r.class)).toEqual(['5b', '7a']);
    expect(classAbsenceText(rows[1])).toBe('ganztägig nicht im Haus · Wandertag');
    expect(classAbsenceText(rows[0])).toBe('4.–5. Std. nicht im Haus · Theater');
    expect(withoutClassAbsences(plan).map((e) => e.id)).toEqual(['v']);
  });

  it('filtert Klassen-Zeilen nach Text, Art und Klasse', () => {
    const rows = classAbsenceRows(details);
    expect(filterClassRows(rows, { text: 'wander' }).map((r) => r.class)).toEqual(['7a']);
    expect(filterClassRows(rows, { kinds: ['vertretung'] })).toEqual([]);
    expect(filterClassRows(rows, { kinds: ['klasse_abwesend'], classId: '5b' }).map((r) => r.class)).toEqual(['5b']);
  });

  it('zeigt beim Filter auf eine Lehrkraft keine Klassen-Zeilen (sonst leere Tabelle ohne „Keine Änderungen“)', () => {
    const rows = classAbsenceRows(details);
    expect(filterClassRows(rows, { teacher: 'BER' })).toEqual([]);
    expect(filterClassRows(rows, { teacher: 'BER', entries: plan })).toEqual([]);
    expect(filterClassRows(rows, { teacher: '' })).toHaveLength(2);
  });

  it('zeigt beim Filter auf eine Lehrkraft die Klasse, in der ihr Unterricht wegen des Wandertags entfällt', () => {
    // Prüfung R2-A: „nur meine“ blendete den eigenen entfallenden Unterricht sonst ganz aus („Keine Änderungen“)
    const rows = classAbsenceRows(details);
    expect(filterClassRows(rows, { teacher: 'MUE', entries: plan }).map((r) => r.class)).toEqual(['7a']);
    // Rhythmus-Einträge machen keine Klasse sichtbar, andere Lehrkräfte auch nicht
    const rhythmOnly = plan.filter((e) => e.source === 'rhythm');
    expect(filterClassRows(rows, { teacher: 'MUE', entries: rhythmOnly })).toEqual([]);
    expect(filterClassRows(rows, { teacher: 'SCH', entries: plan })).toEqual([]);
    expect(filterClassRows(rows, { teacher: 'MUE', entries: plan, text: 'theater' })).toEqual([]);
  });

  it('ordnet Klassen-Zeilen in die Gruppen nach Klasse ein', () => {
    const rows = classAbsenceRows(details);
    const groups = groupWithClassRows(withoutClassAbsences(plan), rows);
    expect(groups.map(([k, row, list]) => [k, row?.class ?? null, list.length])).toEqual([
      ['5b', '5b', 0],
      ['7a', '7a', 0],
      ['8c', null, 1],
    ]);
  });

  it('rendert den Wandertag im Plan als genau eine Zeile (auch im Druck)', () => {
    const html = renderToStaticMarkup(
      createElement(EntryTable, { entries: withoutClassAbsences(plan), classAbsences: classAbsenceRows(details), caption: 'Plan' }),
    );
    expect(html.match(/<td>[^<]*nicht im Haus · Wandertag/g)).toHaveLength(1);
    expect(html).not.toContain('Berufsschule');
    expect(html).not.toContain('Klasse abwesend: Wandertag');
    const flat = renderToStaticMarkup(
      createElement(EntryTable, { entries: withoutClassAbsences(plan), classAbsences: classAbsenceRows(details), caption: 'Plan', grouped: false }),
    );
    expect(flat.match(/<td>[^<]*nicht im Haus · /g)).toHaveLength(2);
  });
});

describe('EntryTable: Hinweis-Spalte bleibt auf dem Desktop sichtbar', () => {
  it('bricht Klassenlisten und Raum alt/neu nur zwischen den Kürzeln um', () => {
    const e = entry('q', { classes: ['Q1-1', 'Q1-2'], room: 'S1-R5a', new_room: 'S1-R5b', kind: 'raumaenderung' });
    const html = renderToStaticMarkup(createElement(EntryTable, { entries: [e], caption: 'Plan', grouped: false }));
    expect(html).toContain('<td><span class="nowrap">Q1-1</span>, <span class="nowrap">Q1-2</span></td>');
    expect(html).toMatch(/<td><span class="strike faint nowrap">S1-R5a<\/span> <strong class="nowrap">S1-R5b<\/strong><\/td>/);
  });
});

describe('U-59: Wochenstatistik', () => {
  it('nutzt die Schultage der Einstellungen', () => {
    expect(statsWeek('2026-10-07', 5)).toEqual({ from: '2026-10-05', to: '2026-10-09' });
    expect(statsWeek('2026-10-07', 6)).toEqual({ from: '2026-10-05', to: '2026-10-10' });
    expect(statsWeek('2026-10-07', 4)).toEqual({ from: '2026-10-05', to: '2026-10-08' });
    expect(statsWeek('2026-10-07', undefined)).toEqual({ from: '2026-10-05', to: '2026-10-09' });
  });

  it('zeigt auch Lehrkräfte, die nur Aufsichten haben', () => {
    const row = (teacher: string, extra: Partial<TeacherStat>): TeacherStat => ({
      teacher,
      name: teacher,
      substitutions: 0,
      cancelled_own: 0,
      duties: 0,
      supervisions: 0,
      ...extra,
    });
    const rows = statRows([row('A', {}), row('B', { duties: 2 }), row('C', { substitutions: 3 }), row('D', { supervisions: 1 })]);
    expect(rows.map((r) => r.teacher)).toEqual(['C', 'D', 'B']);
  });
});

describe('Kriterium 3: Karte „Abwesende Lehrkräfte“', () => {
  const absent: AbsentTeacherDetail[] = [
    { teacher: 'BUS', name: 'Frau Busch', full_day: true, periods: [], cases: 5 },
    { teacher: 'BER', name: 'Herr Bergmann', full_day: false, periods: [2, 3, 4], cases: 1 },
  ];

  /** Zeilen (`<tr onClick>`) aus dem Element-Baum – die Karte selbst hat keine Hooks. */
  function rows(node: ReactNode, out: ReactElement<{ onClick?: () => void }>[] = []) {
    if (Array.isArray(node)) node.forEach((n) => rows(n, out));
    else if (isValidElement<{ children?: ReactNode; onClick?: () => void }>(node)) {
      if (node.type === 'tr' && node.props.onClick) out.push(node);
      rows(node.props.children, out);
    }
    return out;
  }

  it('zeigt eine Zeile je Person mit Kürzel, Name, Stunden und Fällen', () => {
    const html = renderToStaticMarkup(createElement(AbsentTeachersCard, { details: absent, selected: '', onSelect: () => {}, date: '2026-10-12' }));
    expect(html).toContain('Abwesende Lehrkräfte');
    expect(html.match(/<tr class="clickable/g)).toHaveLength(2);
    expect(html).toMatch(/BUS<\/button><\/td><td>Frau Busch<\/td><td class="nowrap">ganztägig<\/td><td class="num nowrap">5 Fälle/);
    expect(html).toMatch(/BER<\/button><\/td><td>Herr Bergmann<\/td><td class="nowrap">3\.–5\. Std\.<\/td><td class="num nowrap">1 Fall/);
    expect(html).not.toContain('aria-pressed="true"');
    expect(renderToStaticMarkup(createElement(AbsentTeachersCard, { details: [], selected: '', onSelect: () => {}, date: '2026-10-12' }))).toBe('');
  });

  it('Klick filtert auf die Lehrkraft, zweiter Klick hebt den Filter auf', () => {
    const picked: (string | null)[] = [];
    const tree = AbsentTeachersCard({ details: absent, selected: '', onSelect: (t) => picked.push(t), date: '2026-10-12' });
    rows(tree)[0].props.onClick?.();
    const again = AbsentTeachersCard({ details: absent, selected: 'BUS', onSelect: (t) => picked.push(t), date: '2026-10-12' });
    rows(again)[0].props.onClick?.();
    rows(again)[1].props.onClick?.();
    expect(picked).toEqual(['BUS', null, 'BER']);
    const html = renderToStaticMarkup(createElement(AbsentTeachersCard, { details: absent, selected: 'BUS', onSelect: () => {}, date: '2026-10-12' }));
    expect(html).toContain('class="clickable selected"');
    expect(html.match(/aria-pressed="true"/g)).toHaveLength(1);
  });

  it('Knopf hat eine feste Beschriftung (Zustand nur über aria-pressed) und die Tabelle ein lesbares Datum', () => {
    // Prüfung R2-A: vorher „Nur Einträge zeigen von Herr Bergmann“ bzw. „Alle Einträge zeigen …“ je nach Zustand
    const off = renderToStaticMarkup(createElement(AbsentTeachersCard, { details: absent, selected: '', onSelect: () => {}, date: '2026-10-12' }));
    const on = renderToStaticMarkup(createElement(AbsentTeachersCard, { details: absent, selected: 'BER', onSelect: () => {}, date: '2026-10-12' }));
    for (const html of [off, on]) expect(html).toContain('aria-label="Nach Lehrkraft filtern: BER, Herr Bergmann"');
    expect(off).toContain('Abwesende Lehrkräfte am 12.10.2026');
  });
});

describe('U-60: Feld „Grund“ im Abwesenheits-Dialog', () => {
  it('nennt bei Lehrkräften den richtigen Kreis und nie „nur für die Schulleitung“', () => {
    expect(ABSENCE_REASON_FIELD.teacher.label).toBe('Grund (vertraulich)');
    expect(ABSENCE_REASON_FIELD.teacher.help).toContain('Sekretariat');
    expect(ABSENCE_REASON_FIELD.teacher.help).toContain('Lehrkraft selbst');
    for (const f of Object.values(ABSENCE_REASON_FIELD)) expect(`${f.label} ${f.help}`).not.toMatch(/nur für die Schulleitung/);
    expect(ABSENCE_REASON_FIELD.class.label).toBe('Grund');
    expect(ABSENCE_REASON_FIELD.class.help).toContain('Monitor');
    // Raum-Gründe erscheinen nicht im Plan (Hinweis „Raum … gesperrt – Ersatzraum …“), nur für `substitution.edit`
    expect(ABSENCE_REASON_FIELD.room.help).not.toMatch(/Erscheint im Vertretungsplan/);
    expect(ABSENCE_REASON_FIELD.room.help).toContain('Sekretariat');
  });
});
