/**
 * Kalenderwoche: Prüfungen, Hausaufgaben, Termine und Abwesenheit als Blöcke bzw. kleine Zeichen in den Stundenfeldern
 * (reine Funktionen ohne React, getestet in calendar.test.ts). Reihenfolge: erst `overlayExams` (Klausur-/Nachschreib-
 * Blöcke ersetzen den Regelplan in ihren Stunden), dann Hausaufgaben, Tests, Termine, Hinweise, Abwesenheit.
 */
import type { Cell } from '../../api/types';
import { examTarget } from '../channels/examRoom';
import type { CalendarDay, CalendarExam, CalendarHomework } from './CalendarWeek';

/** Was schon in einer Stunde hängt und deshalb nicht mehr im Tageskopf stehen muss. */
export interface Attached {
  ha: Set<number>;
  exam: Set<string>;
  absent: Set<number>;
  event: Set<string>;
}

export const newAttached = (): Attached => ({ ha: new Set(), exam: new Set(), absent: new Set(), event: new Set() });

type Link = NonNullable<Cell['links']>[number];

const addLink = (c: Cell, link: Link) => {
  c.links = [...(c.links ?? []), link];
};
const endOf = (c: Pick<Cell, 'start' | 'length'>) => c.start + Math.max(1, c.length);
const overlaps = (c: Pick<Cell, 'start' | 'length'>, s: number, e: number) => c.start < e && s < endOf(c);
const live = (c: Cell) => !c.status?.cancelled;

const EXAM_LABEL: Record<CalendarExam['kind'], string> = { klausur: 'Klausur', test: 'Test', nachschreiben: 'Nachschreiben' };
export const examWhen = (x: Pick<CalendarExam, 'start' | 'length'>) => `${x.start + 1}.${x.length > 1 ? `–${x.start + x.length}.` : ''} Std.`;

/** Zelle mit Stunden [s, e) herausschneiden: übrig bleiben die Teile davor und danach. */
function carve(c: Cell, s: number, e: number): Cell[] {
  const out: Cell[] = [];
  if (c.start < s) out.push({ ...c, lesson_id: `${c.lesson_id}~a`, length: s - c.start, links: undefined });
  if (endOf(c) > e) out.push({ ...c, lesson_id: `${c.lesson_id}~b`, start: e, length: endOf(c) - e, links: undefined });
  return out;
}

const sameSet = (a: readonly string[], b: readonly string[]) => a.length === b.length && a.every((x) => b.includes(x));

/** Welche Stunden verdrängt die Prüfung? Schüler/Lehrkraft/Raum: alles in diesen Stunden; Klasse: Stunden desselben Kurses
 * bzw. ganzer Klassen (parallele Gruppen-/Wahlkurse bleiben stehen). */
function displaced(kind: string, c: Cell, x: CalendarExam, sameCourseHere: boolean): boolean {
  if (kind !== 'class') return true;
  if (sameCourseHere) return c.course_id === x.course_id;
  return !!x.classes?.length && sameSet(c.classes, x.classes);
}

/**
 * Klausuren und Nachschreibtermine erscheinen als eigener Block in genau ihren Stunden (mit Raum, Lehrkraft, Klassen) –
 * auch wenn dort laut Regelplan ein anderes Fach liegt („Klausur M statt D“). Tests bleiben als Zeichen an der Stunde
 * des Fachs, wenn dort eine liegt, sonst ebenfalls Block. Liefert die neue Zellenliste und je Prüfung die Zelle, an der
 * weitere Zeichen (Nachteilsausgleich, fehlt …) hängen.
 */
export function overlayExams(
  cells: Cell[],
  days: readonly CalendarDay[],
  kind: string,
  subjectName: (s: string) => string | undefined,
  attached: Attached,
  child?: string,
): { cells: Cell[]; targets: Map<string, Cell> } {
  let out = cells;
  const targets = new Map<string, Cell>();
  days.forEach((d, di) => {
    for (const x of d.exams) {
      const len = Math.max(1, x.length);
      const s = x.start;
      const e = s + len;
      if (x.kind === 'test') {
        const same = out.filter((c) => c.day === di && live(c) && overlaps(c, s, e) && (x.course_id ? c.course_id === x.course_id : c.subject === x.subject));
        const here = same[0] ?? out.find((c) => c.day === di && live(c) && !c.exam && x.subject && c.subject === x.subject);
        if (here) {
          attached.exam.add(x.id);
          targets.set(x.id, here);
          if (here.status?.label === 'Klausur' && !here.status.cancelled) here.status = undefined; // Server markiert auch Tests als „Klausur“
          addLink(here, { kind: 'exam', label: 'Test', to: examTarget(x, d.date, child) ?? '', title: `${x.kind_label}: ${x.title || x.label} (${examWhen(x)})` });
          continue;
        }
      }
      const under = out.filter((c) => c.day === di && overlaps(c, s, e) && !c.exam);
      const sameCourseHere = under.some((c) => c.course_id === x.course_id);
      const gone = under.filter((c) => displaced(kind, c, x, sameCourseHere));
      const goneSubjects = [...new Set(gone.filter((c) => c.subject && c.subject !== x.subject).map((c) => subjectName(c.subject) ?? c.subject))];
      const rest = out.filter((c) => !gone.includes(c));
      const carved = gone.flatMap((c) => carve(c, s, e));
      const label = EXAM_LABEL[x.kind];
      const block: Cell = {
        lesson_id: `x:${x.id}@${d.date}#${s}`,
        course_id: x.course_id ?? '',
        day: di,
        start: s,
        length: len,
        weeks: [],
        subject: x.subject || '',
        subject_name: x.subject ? (subjectName(x.subject) ?? x.subject) : x.label || x.title,
        color: '',
        teachers: x.teachers ?? [],
        rooms: x.room ? [x.room] : [],
        classes: x.classes ?? [],
        label: x.label,
        locked: false,
        parts: [],
        status: { label, cancelled: false, note: [x.title && x.title !== x.label ? x.title : '', goneSubjects.length ? `statt ${goneSubjects.join(', ')}` : ''].filter(Boolean).join(' · ') || undefined },
        exam: { id: x.id, kind: x.kind, to: examTarget(x, d.date, child) },
      };
      attached.exam.add(x.id);
      targets.set(x.id, block);
      out = [...rest, ...carved, block];
    }
  });
  return { cells: out, targets };
}

const coversPeriod = (c: Cell, day: number, p: number) => c.day === day && c.start <= p && p < endOf(c);

/** Hausaufgaben an die vom Server bestimmte Stunde (`slot`) hängen (Regel: `calendar_week` im Server). Ohne Treffer bleibt
 * die Aufgabe im Tageskopf. Kein Zugang zum Kursraum: Zeichen ohne Link. */
export function withHomework(cells: Cell[], days: readonly CalendarDay[], attached: Attached): Cell[] {
  days.forEach((d, di) => {
    for (const h of d.homework) {
      if (h.slot == null) continue;
      const here = cells.filter((c) => coversPeriod(c, di, h.slot as number) && live(c));
      const target = here.find((c) => !c.exam && h.course_id && c.course_id === h.course_id) ?? here.find((c) => !c.exam) ?? here[0];
      if (!target) continue;
      attached.ha.add(h.item_id);
      addLink(target, homeworkLink(h, d.date));
    }
  });
  return cells;
}

const dueText = (iso: string) => {
  const [y, m, dd] = iso.split('-');
  return y && m && dd ? `${dd}.${m}.` : iso;
};

export function homeworkLink(h: CalendarHomework, placedDate: string): Link {
  const done = typeof h.submitted === 'number' ? ` ${h.submitted}/${h.expected ?? '?'}` : '';
  const state = h.status_label ? ` – ${h.status_label}` : done ? ` – ${done.trim()} abgegeben` : '';
  const due = h.due_date && h.due_date !== placedDate ? ` (fällig ${dueText(h.due_date)} ${h.time})` : h.time ? ` (fällig ${h.time})` : '';
  return {
    kind: 'ha',
    label: `HA${done}`,
    to: h.can_open === false ? '' : `/kursraeume/${h.channel_id}?tab=aufgaben&aufgabe=${h.item_id}`,
    title: `${h.subject_name ? `${h.subject_name}: ` : ''}${h.title}${due}${state}`,
    done: h.status === 'abgegeben' || h.status === 'bewertet',
  };
}

/** Stunde (0-basiert), in der eine Uhrzeit „HH:MM“ liegt: letzte Stunde, die nicht später beginnt. */
export function periodAt(time: string, periodTimes: readonly string[]): number | null {
  const m = /(\d{1,2}):(\d{2})/.exec(time);
  if (!m) return null;
  const t = Number(m[1]) * 60 + Number(m[2]);
  let found: number | null = null;
  periodTimes.forEach((pt, i) => {
    const s = /(\d{1,2}):(\d{2})/.exec(pt);
    if (s && Number(s[1]) * 60 + Number(s[2]) <= t) found = i;
  });
  return found;
}

/** Termine mit Uhrzeit an die Stunde hängen, in der sie beginnen (ganztägige bleiben im Tageskopf). */
export function withEvents(cells: Cell[], days: readonly CalendarDay[], periodTimes: readonly string[], attached: Attached): Cell[] {
  days.forEach((d, di) => {
    for (const ev of d.events) {
      const p = ev.time_from ? periodAt(ev.time_from, periodTimes) : null;
      if (p == null) continue;
      const day = cells.filter((c) => c.day === di && live(c));
      const target = day.find((c) => coversPeriod(c, di, p)) ?? day.filter((c) => c.start > p).sort((a, b) => a.start - b.start)[0];
      if (!target) continue;
      attached.event.add(ev.id);
      const time = `${ev.time_from}${ev.time_to ? `–${ev.time_to}` : ''}`;
      addLink(target, {
        kind: ev.kind === 'pflicht' ? 'duty' : 'event',
        label: ev.kind === 'pflicht' ? 'Pflicht' : 'Termin',
        to: '',
        title: `${ev.kind === 'pflicht' ? 'Pflichttermin: ' : ''}${ev.title} ${time}${ev.location ? ` · ${ev.location}` : ''}${ev.note ? ` · ${ev.note}` : ''}`,
      });
    }
  });
  return cells;
}

const ABSENT_LABEL: Record<string, string> = { krank: 'krank', fehlt: 'gefehlt', beurlaubung: 'beurlaubt' };

/** Stunden, in denen die Schülerin/der Schüler gefehlt hat (krank, beurlaubt, gefehlt), rot gestrichelt markieren –
 * Meldungen ohne Stundenangabe gelten für den ganzen Tag. Zu spät/früher gegangen nicht. Das rote Zeichen führt zur
 * Seite „Krankmeldungen“ (`onOpen` merkt vorher das Kind). */
export function withAbsence(cells: Cell[], days: readonly CalendarDay[], attached: Attached, onOpen: () => void): Cell[] {
  for (const c of cells) {
    const list = (days[c.day]?.attendance ?? []).filter((a) => ABSENT_LABEL[a.kind]);
    const hit = list.filter((a) => !a.periods.length || a.periods.some((p) => p >= c.start && p < endOf(c)));
    if (!hit.length || c.status?.cancelled) continue;
    c.absent = ABSENT_LABEL[(hit.find((a) => a.kind === 'krank') ?? hit[0]).kind];
    hit.forEach((a) => attached.absent.add(a.id));
    addLink(c, { kind: 'absent', label: c.absent, to: '/krankmeldungen', title: 'Krankmeldungen öffnen', onClick: onOpen });
  }
  return cells;
}

/** Hinweise zu Prüfungen: Nachteilsausgleich (Lehrkräfte), fehlende Schüler/innen (Lehrkräfte) bzw. eigener Nachschreibbedarf
 * (Familie). `students`: Name + Kurztext je Prüfung; `missing`: Namen derer, die nachschreiben müssen. */
export function withExamNotes(
  targets: ReadonlyMap<string, Cell>,
  notes: { support?: Record<string, { name: string; summary: string }[]>; missing?: Record<string, string[]>; own?: Record<string, string> },
): void {
  for (const [id, cell] of targets) {
    const sup = notes.support?.[id] ?? [];
    for (const s of sup) addLink(cell, { kind: 'support', label: 'NTA', to: '', title: `${s.name}: ${s.summary}` });
    for (const name of notes.missing?.[id] ?? []) addLink(cell, { kind: 'missing', label: 'fehlt', to: '/nachschreiben', title: `${name} – Nachschreiben nötig` });
    const own = notes.own?.[id];
    if (own) addLink(cell, { kind: 'makeup', label: 'Nachschreiben', to: '/nachschreiben', title: own });
  }
}
