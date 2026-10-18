import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import { AbbrList, ClassAbbr, RoomAbbr, SiteAbbr, SubjectAbbr, TeacherAbbr } from '../components/Abbr';
import { data as dataApi } from '../api/endpoints';
import type { CollectionName, CollectionTypes, TimeRule } from '../api/types';
import { Icon } from '../components/Icon';
import { Modal } from '../components/Modal';
import { ClassPlanningFields, classPlanningOf } from '../components/ClassPlanningFields';
import { ClassExamLimitsFields } from '../components/ExamLimits';
import { useConfirmChanges } from '../components/ConfirmChanges';
import { RuleEditor } from '../components/RuleEditor';
import { MultiSelect, SearchSelect, type SelectOption } from '../components/SearchSelect';
import { VirtualTable, type Column } from '../components/VirtualTable';
import { AsyncButton, ErrorBox, Field, Loading, Tabs } from '../components/ui';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { invalidate, useCollection, useSettings } from '../hooks/useCollection';
import { useDebounced, useTitle } from '../hooks/misc';
import { subjectColor, textOn } from '../lib/colors';
import { dateRangeLabel } from '../lib/dates';
import { matchesQuery, sortBy } from '../lib/format';
import { can } from '../lib/permissions';
import { describeRule } from '../lib/rules';
import { classPlanningText, HOLIDAY_KIND_LABELS, holidayKindOf, schoolDaysOf } from '../lib/weeks';
import type { HolidayKind, Settings } from '../api/types';
import { TeacherAvailabilityField } from '../features/teacher/TeacherFields';
import { CommuteField } from '../features/teacher/CommuteField';
import { GRADE_MAX, GRADE_MIN } from './planning/curricula';
import { DeleteClassesDialog, GradeLevelsView } from '../features/gradeLevels/GradeLevelsView';
import { classesApi } from '../features/classes/api';
import { ClassCurriculumSection } from '../features/classes/ClassCurriculumSection';
import type { CurriculumRow } from '../features/classes/types';
import { BirthDateEditor } from '../features/students/BirthDateEditor';
import { StudentDetail } from '../features/students/StudentDetail';
import { SupportCatalogDialog } from '../features/students/SupportCatalogDialog';
import { supportApi } from '../features/students/supportApi';
import { useApi } from '../hooks/useApi';
import { confirmAsk } from '../lib/confirm';

type MdName = 'teachers' | 'classes' | 'rooms' | 'subjects' | 'sites' | 'holidays' | 'events' | 'students' | 'areas';
type Item = CollectionTypes[MdName];
type AnyRec = Record<string, unknown>;

interface Refs {
  sites: SelectOption[];
  rooms: SelectOption[];
  subjects: SelectOption[];
  teachers: SelectOption[];
  classes: SelectOption[];
  roomTypes: string[];
  courseParts: (classId: string) => SelectOption[];
  /** Tage der Regel- und Zeitfenster-Editoren ab Montag bis zum letzten Schulöffnungstag (R3: bis 7 = Mo–So) */
  days: number;
  periods: number;
  periodTimes: string[];
  periodMinutes: number;
  /** R3: Unterrichtstage der Schule, Wochen des Schuljahres, Recht auf Planungsfelder (`timetable.edit`) */
  schoolDays: number[];
  yearWeeks: number;
  canPlan: boolean;
  settings: Pick<Settings, 'days' | 'school_days'> | null;
}

type FieldType =
  | 'text'
  | 'email'
  | 'number'
  | 'bool'
  | 'color'
  | 'date'
  | 'select'
  | 'multiselect'
  | 'rules'
  | 'datalist'
  /** Verfügbarkeit einer Lehrkraft: Sperrzeiten und Wünsche in einem Editor (Raster + Rhythmus + „gilt ab“) */
  | 'availability'
  /** Pendeln zwischen Standorten (nur bei mehr als einem Standort sichtbar) */
  | 'commute'
  /** R3: Unterrichtstage einer Klasse (`school_days`) */
  | 'planning'
  /** Klassenarbeiten je Woche/Tag einer Klasse (Vorgabe von Jahrgang/Schule oder eigene Werte) */
  | 'examLimits'
  /** R3: Art eines Ferieneintrags */
  | 'holidayKind';

interface FieldDef {
  key: string;
  label: string;
  type: FieldType;
  options?: (refs: Refs, item: AnyRec) => SelectOption[];
  list?: (refs: Refs) => string[];
  hint?: string;
  required?: boolean;
  min?: number;
  max?: number;
  nullable?: boolean;
  wide?: boolean;
  /** nur anzeigen, wenn die Schule mehr als einen Standort hat */
  multiSite?: boolean;
}

interface Def {
  name: MdName;
  label: string;
  singular: string;
  /** Server vergibt ID automatisch, wenn leer */
  autoId: boolean;
  idLabel: string;
  fields: FieldDef[];
  columns: (refs: Refs) => Column<AnyRec>[];
  blank: () => AnyRec;
  search: (x: AnyRec) => string;
}

const s = (v: unknown) => (v === null || v === undefined ? '' : String(v));
const arr = (v: unknown): string[] => (Array.isArray(v) ? v.map(String) : []);
const rules = (v: unknown): TimeRule[] => (Array.isArray(v) ? (v as TimeRule[]) : []);

const DEFS: Def[] = [
  {
    name: 'teachers',
    label: 'Lehrkräfte',
    singular: 'Lehrkraft',
    autoId: false,
    idLabel: 'Kürzel',
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'email', label: 'E-Mail', type: 'email', hint: 'für Benachrichtigungen bei Vertretungen' },
      { key: 'subjects', label: 'Fächer (Lehrbefähigung)', type: 'multiselect', options: (r) => r.subjects, wide: true },
      {
        key: 'preferred_classes',
        label: 'Wunschklassen (hauptsächlich unterrichtete Klassen)',
        type: 'multiselect',
        options: (r) => r.classes,
        wide: true,
        hint: 'Werden bei „Lehrkräfte zuweisen“ bevorzugt.',
      },
      { key: 'sites', label: 'Standorte (leer = alle)', type: 'multiselect', options: (r) => r.sites, wide: true, multiSite: true },
      { key: 'commute', label: 'Pendeln zwischen Standorten', type: 'commute', wide: true, multiSite: true },
      { key: 'max_hours', label: 'Deputat (Std./Woche)', type: 'number', min: 0, max: 40 },
      { key: 'max_per_day', label: 'max. Stunden pro Tag', type: 'number', min: 1, max: 16 },
      { key: 'max_subs_per_week', label: 'max. Vertretungen pro Woche', type: 'number', min: 0, max: 20 },
      { key: 'availability', label: 'Verfügbarkeit (Sperrzeiten und Wünsche)', type: 'availability', wide: true },
    ],
    columns: () => [
      { key: 'id', header: 'Kürzel', render: (x) => <strong><TeacherAbbr id={s(x.id)} /></strong>, sortValue: (x) => s(x.id), width: '90px' },
      { key: 'name', header: 'Name', render: (x) => s(x.name), sortValue: (x) => s(x.name) },
      { key: 'subjects', header: 'Fächer', render: (x) => <AbbrList kind="subject" ids={arr(x.subjects)} /> },
      { key: 'max_hours', header: 'Deputat', className: 'num', render: (x) => s(x.max_hours), sortValue: (x) => Number(x.max_hours), width: '90px' },
      { key: 'sites', header: 'Standorte', render: (x) => <AbbrList kind="site" ids={arr(x.sites)} empty="alle" /> },
      { key: 'rules', header: 'Sperr./Wünsche', render: (x) => `${rules(x.unavailable).length} / ${rules(x.wishes).length}`, width: '130px' },
    ],
    blank: () => ({
      id: '',
      name: '',
      email: '',
      subjects: [],
      preferred_classes: [],
      commute_mode: 'free',
      commute_gap: 0,
      sites: [],
      max_hours: 25,
      max_per_day: 7,
      max_subs_per_week: 3,
      time_windows: [],
      work_grid: {},
      unavailable: [],
      wishes: [],
    }),
    search: (x) => `${s(x.id)} ${s(x.name)} ${arr(x.subjects).join(' ')}`,
  },
  {
    name: 'classes',
    label: 'Klassen',
    singular: 'Klasse',
    autoId: false,
    idLabel: 'Kürzel',
    fields: [
      { key: 'name', label: 'Anzeigename', type: 'text', required: true },
      { key: 'grade', label: 'Klassenstufe', type: 'number', min: GRADE_MIN, max: GRADE_MAX, required: true },
      { key: 'students', label: 'Anzahl Schüler/innen', type: 'number', min: 0, max: 60 },
      { key: 'site', label: 'Standort', type: 'select', options: (r) => r.sites },
      { key: 'home_room', label: 'Klassenraum', type: 'select', options: (r) => r.rooms, nullable: true },
      { key: 'class_teacher', label: 'Klassenleitung', type: 'select', options: (r) => r.teachers, nullable: true },
      { key: 'max_periods_per_day', label: 'max. Stunden pro Tag', type: 'number', min: 1, max: 14 },
      { key: 'examLimits', label: 'Klassenarbeiten / Klausuren', type: 'examLimits', wide: true },
      { key: 'planning', label: 'Planung', type: 'planning', wide: true },
      {
        key: 'unavailable',
        label: 'Rhythmus: Zeiten ohne Unterricht an der Schule',
        type: 'rules',
        wide: true,
        hint: 'Beispiele: jeden Mittwoch Praxistag → Tag Mi; Woche 1 Mittwoch weg → Ausgewählte Wochen 1 + Mi; jede 2. Woche Di und Do weg → Rhythmus (Abstand 2) + Di + Do.',
      },
    ],
    columns: (refs) => [
      { key: 'id', header: 'Kürzel', render: (x) => <strong><ClassAbbr id={s(x.id)} /></strong>, sortValue: (x) => s(x.id), width: '90px' },
      { key: 'name', header: 'Anzeigename', render: (x) => s(x.name), sortValue: (x) => s(x.name) },
      { key: 'grade', header: 'Stufe', className: 'num', render: (x) => s(x.grade), sortValue: (x) => Number(x.grade), width: '60px' },
      { key: 'students', header: 'SuS', className: 'num', render: (x) => s(x.students), sortValue: (x) => Number(x.students), width: '70px' },
      { key: 'site', header: 'Standort', render: (x) => <SiteAbbr id={s(x.site)} />, sortValue: (x) => s(x.site), width: '110px' },
      { key: 'home_room', header: 'Raum', render: (x) => <RoomAbbr id={s(x.home_room)} />, width: '110px' },
      { key: 'class_teacher', header: 'Leitung', render: (x) => <TeacherAbbr id={s(x.class_teacher)} />, width: '90px' },
      { key: 'planning', header: 'Planung', render: (x) => <span className="small">{classPlanningText(x as never, refs.settings)}</span>, width: '150px' },
      { key: 'rules', header: 'Rhythmus', render: (x) => (rules(x.unavailable).length ? <span className="badge badge-info">{rules(x.unavailable).length} Regel(n)</span> : ''), width: '140px' },
      {
        key: 'exams',
        header: 'Klausuren',
        render: (x) => ((x.max_exams_per_week ?? null) !== null || (x.max_exams_per_day ?? null) !== null ? <span className="small">eigene: {s(x.max_exams_per_week ?? '–')}/Wo, {s(x.max_exams_per_day ?? '–')}/Tag</span> : <span className="small muted">Vorgabe</span>),
        width: '150px',
      },
    ],
    blank: () => ({ id: '', name: '', grade: 5, students: 25, home_room: null, site: '', max_periods_per_day: 8, unavailable: [], class_teacher: null }),
    search: (x) => `${s(x.id)} ${s(x.name)} ${s(x.class_teacher)} ${s(x.site)}`,
  },
  {
    name: 'rooms',
    label: 'Räume',
    singular: 'Raum',
    autoId: false,
    idLabel: 'Raumnummer',
    fields: [
      { key: 'name', label: 'Bezeichnung', type: 'text' },
      { key: 'type', label: 'Raumtyp', type: 'datalist', list: (r) => r.roomTypes, hint: 'z. B. Klassenraum, Sporthalle, Chemie, Informatik' },
      { key: 'site', label: 'Standort', type: 'select', options: (r) => r.sites },
      { key: 'capacity', label: 'Plätze', type: 'number', min: 0, max: 500 },
    ],
    columns: () => [
      { key: 'id', header: 'Raum', render: (x) => <strong><RoomAbbr id={s(x.id)} /></strong>, sortValue: (x) => s(x.id) },
      { key: 'name', header: 'Bezeichnung', render: (x) => s(x.name), sortValue: (x) => s(x.name) },
      { key: 'type', header: 'Typ', render: (x) => s(x.type), sortValue: (x) => s(x.type), width: '160px' },
      { key: 'site', header: 'Standort', render: (x) => <SiteAbbr id={s(x.site)} />, sortValue: (x) => s(x.site), width: '110px' },
      { key: 'capacity', header: 'Plätze', className: 'num', render: (x) => s(x.capacity), sortValue: (x) => Number(x.capacity), width: '90px' },
    ],
    blank: () => ({ id: '', name: '', type: 'Klassenraum', site: '', capacity: 30 }),
    search: (x) => `${s(x.id)} ${s(x.name)} ${s(x.type)} ${s(x.site)}`,
  },
  {
    name: 'subjects',
    label: 'Fächer',
    singular: 'Fach',
    autoId: false,
    idLabel: 'Kürzel',
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'room_type', label: 'Benötigter Raumtyp (leer = Klassenraum)', type: 'datalist', list: (r) => r.roomTypes, nullable: true },
      { key: 'core', label: 'Hauptfach (möglichst früh am Tag)', type: 'bool' },
      { key: 'max_per_day', label: 'max. Blöcke pro Tag', type: 'number', min: 1, max: 4 },
      { key: 'color', label: 'Farbe im Stundenplan', type: 'color' },
    ],
    columns: () => [
      {
        key: 'id',
        header: 'Kürzel',
        render: (x) => {
          const bg = subjectColor(s(x.id), s(x.color));
          return (
            <span className="badge" style={{ background: bg, color: textOn(bg), borderColor: 'transparent' }}>
              <SubjectAbbr id={s(x.id)} />
            </span>
          );
        },
        sortValue: (x) => s(x.id),
      },
      { key: 'name', header: 'Name', render: (x) => s(x.name), sortValue: (x) => s(x.name) },
      { key: 'room_type', header: 'Raumtyp', render: (x) => s(x.room_type) || 'Klassenraum' },
      { key: 'core', header: 'Hauptfach', render: (x) => (x.core ? 'ja' : ''), width: '110px' },
      { key: 'max_per_day', header: 'max./Tag', className: 'num', render: (x) => s(x.max_per_day), width: '100px' },
    ],
    blank: () => ({ id: '', name: '', room_type: null, core: false, max_per_day: 1, color: '' }),
    search: (x) => `${s(x.id)} ${s(x.name)} ${s(x.room_type)}`,
  },
  {
    name: 'sites',
    label: 'Standorte',
    singular: 'Standort',
    autoId: true,
    idLabel: 'Kürzel',
    fields: [{ key: 'name', label: 'Name', type: 'text', required: true }],
    columns: () => [
      { key: 'id', header: 'Kürzel', render: (x) => <strong><SiteAbbr id={s(x.id)} /></strong>, sortValue: (x) => s(x.id) },
      { key: 'name', header: 'Name', render: (x) => s(x.name), sortValue: (x) => s(x.name) },
    ],
    blank: () => ({ id: '', name: '' }),
    search: (x) => `${s(x.id)} ${s(x.name)}`,
  },
  {
    name: 'holidays',
    label: 'Ferien & Feiertage',
    singular: 'Ferien/Feiertag',
    autoId: true,
    idLabel: 'ID',
    fields: [
      { key: 'name', label: 'Bezeichnung', type: 'text', required: true },
      { key: 'kind', label: 'Art', type: 'holidayKind' },
      { key: 'date_from', label: 'Von', type: 'date', required: true },
      { key: 'date_to', label: 'Bis', type: 'date', required: true },
    ],
    columns: () => [
      { key: 'name', header: 'Bezeichnung', render: (x) => s(x.name), sortValue: (x) => s(x.name) },
      { key: 'kind', header: 'Art', render: (x) => HOLIDAY_KIND_LABELS[holidayKindOf({ name: s(x.name), kind: x.kind as HolidayKind | undefined })], width: '190px' },
      { key: 'range', header: 'Zeitraum', render: (x) => dateRangeLabel(s(x.date_from), s(x.date_to)), sortValue: (x) => s(x.date_from) },
    ],
    blank: () => ({ id: '', name: '', kind: 'ferien', date_from: '', date_to: '' }),
    search: (x) => `${s(x.name)} ${s(x.date_from)}`,
  },
  {
    name: 'events',
    label: 'Termine',
    singular: 'Termin',
    autoId: true,
    idLabel: 'ID',
    fields: [
      { key: 'title', label: 'Titel', type: 'text', required: true },
      {
        key: 'kind',
        label: 'Art',
        type: 'select',
        options: () => [
          { value: 'termin', label: 'Termin (zur Info)' },
          { value: 'pflicht', label: 'Anwesenheit Pflicht (z. B. Unterricht am Samstag)' },
        ],
        required: true,
      },
      { key: 'date_from', label: 'Von', type: 'date', required: true },
      { key: 'date_to', label: 'Bis (leer = ein Tag)', type: 'date' },
      { key: 'time_from', label: 'Beginn (HH:MM, leer = ganztägig)', type: 'text' },
      { key: 'time_to', label: 'Ende (HH:MM)', type: 'text' },
      { key: 'classes', label: 'Klassen (leer = ganze Schule)', type: 'multiselect', options: (r) => r.classes, wide: true },
      { key: 'teachers', label: 'Teilnehmende Lehrkräfte (fehlen im Unterricht → Vertretung automatisch)', type: 'multiselect', options: (r) => r.teachers, wide: true },
      { key: 'location', label: 'Ort', type: 'text' },
      { key: 'note', label: 'Hinweis', type: 'text', wide: true },
    ],
    columns: () => [
      { key: 'title', header: 'Titel', render: (x) => s(x.title), sortValue: (x) => s(x.title) },
      { key: 'kind', header: 'Art', render: (x) => (x.kind === 'pflicht' ? 'Pflicht' : 'Termin'), width: '90px' },
      {
        key: 'range',
        header: 'Wann',
        render: (x) => `${dateRangeLabel(s(x.date_from), s(x.date_to) || s(x.date_from))}${x.time_from ? `, ${s(x.time_from)}${x.time_to ? `–${s(x.time_to)}` : ''}` : ''}`,
        sortValue: (x) => s(x.date_from),
      },
      { key: 'classes', header: 'Für', render: (x) => <AbbrList kind="class" ids={arr(x.classes)} empty="ganze Schule" /> },
    ],
    blank: () => ({ id: '', title: '', kind: 'termin', date_from: '', date_to: '', time_from: '', time_to: '', classes: [], grades: [], teachers: [], location: '', note: '' }),
    search: (x) => `${s(x.title)} ${s(x.date_from)} ${arr(x.classes).join(' ')}`,
  },
  {
    name: 'students',
    label: 'Schüler/innen',
    singular: 'Schüler/in',
    autoId: true,
    idLabel: 'Schüler-ID',
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'class_id', label: 'Klasse', type: 'select', options: (r) => r.classes, required: true },
      {
        key: 'courses',
        label: 'Kurswahlen (Oberstufe/Wahlpflicht/Religion)',
        type: 'multiselect',
        options: (r, item) => r.courseParts(s(item.class_id)),
        wide: true,
        hint: 'Ohne Wahl gehört die Person zu allen parallelen Teilen eines Kurses.',
      },
    ],
    columns: () => [
      { key: 'name', header: 'Name', render: (x) => s(x.name), sortValue: (x) => s(x.name) },
      { key: 'class_id', header: 'Klasse', render: (x) => <ClassAbbr id={s(x.class_id)} />, sortValue: (x) => s(x.class_id), width: '110px' },
      { key: 'id', header: 'ID', render: (x) => <span className="mono small">{s(x.id)}</span>, sortValue: (x) => s(x.id), width: '140px' },
      { key: 'courses', header: 'Kurswahlen', className: 'num', render: (x) => arr(x.courses).length || '', width: '110px' },
    ],
    blank: () => ({ id: '', name: '', class_id: '', courses: [] }),
    search: (x) => `${s(x.name)} ${s(x.class_id)} ${s(x.id)}`,
  },
  {
    name: 'areas',
    label: 'Aufsichtsbereiche',
    singular: 'Aufsichtsbereich',
    autoId: true,
    idLabel: 'ID',
    fields: [
      { key: 'name', label: 'Bezeichnung', type: 'text', required: true },
      { key: 'site', label: 'Standort', type: 'select', options: (r) => r.sites },
      { key: 'needed', label: 'benötigte Aufsichten je Pause', type: 'number', min: 1, max: 10 },
    ],
    columns: () => [
      { key: 'name', header: 'Bereich', render: (x) => s(x.name), sortValue: (x) => s(x.name) },
      { key: 'site', header: 'Standort', render: (x) => s(x.site), sortValue: (x) => s(x.site), width: '110px' },
      { key: 'needed', header: 'Aufsichten', className: 'num', render: (x) => s(x.needed), width: '110px' },
    ],
    blank: () => ({ id: '', name: '', site: '', needed: 1 }),
    search: (x) => `${s(x.name)} ${s(x.site)}`,
  },
];

/** Reiter „Klassenstufen“ (eigene Ansicht, keine Tabelle einer Sammlung) steht direkt vor „Klassen“. */
const GRADE_TAB = 'klassenstufen';
function masterTabs(): { key: string; label: string }[] {
  const tabs = DEFS.map((d) => ({ key: d.name as string, label: d.label }));
  const at = tabs.findIndex((t) => t.key === 'classes');
  tabs.splice(at < 0 ? tabs.length : at, 0, { key: GRADE_TAB, label: 'Jahrgänge' });
  return tabs;
}

function FieldInput({
  def,
  item,
  set,
  refs,
  disabled,
  isNew = false,
}: {
  def: FieldDef;
  item: AnyRec;
  set: (k: string, v: unknown) => void;
  refs: Refs;
  disabled: boolean;
  isNew?: boolean;
}) {
  if (def.multiSite && refs.sites.length <= 1) return null;
  const id = `md-${def.key}`;
  const v = item[def.key];
  let input: ReactNode;
  switch (def.type) {
    case 'number':
      input = (
        <input
          id={id}
          type="number"
          min={def.min}
          max={def.max}
          value={v === null || v === undefined ? '' : Number(v)}
          disabled={disabled}
          required={def.required}
          onChange={(e) => set(def.key, e.target.value === '' ? 0 : Number(e.target.value))}
        />
      );
      break;
    case 'bool':
      return (
        <div className={`field${def.wide ? ' span-all' : ''}`}>
          <span className="field-label">&nbsp;</span>
          <label className="check">
            <input type="checkbox" checked={!!v} disabled={disabled} onChange={(e) => set(def.key, e.target.checked)} /> {def.label}
          </label>
        </div>
      );
    case 'color':
      input = (
        <div className="row">
          <input id={id} type="color" value={s(v) || subjectColor(s(item.id))} disabled={disabled} onChange={(e) => set(def.key, e.target.value)} />
          <button type="button" className="btn btn-sm btn-ghost" disabled={disabled} onClick={() => set(def.key, '')}>
            automatisch
          </button>
        </div>
      );
      break;
    case 'date':
      input = <input id={id} type="date" value={s(v)} disabled={disabled} required={def.required} onChange={(e) => set(def.key, e.target.value)} />;
      break;
    case 'select': {
      const opts = def.options?.(refs, item) ?? [];
      input = (
        <select id={id} value={s(v)} disabled={disabled} onChange={(e) => set(def.key, e.target.value === '' && def.nullable ? null : e.target.value)}>
          <option value="">{def.nullable ? '– keine –' : '– bitte wählen –'}</option>
          {opts.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
              {o.sub ? ` (${o.sub})` : ''}
            </option>
          ))}
        </select>
      );
      break;
    }
    case 'multiselect':
      return (
        <div className={`field${def.wide ? ' span-all' : ''}`}>
          {disabled ? (
            <>
              <span className="field-label">{def.label}</span>
              <span>{arr(v).join(', ') || '–'}</span>
            </>
          ) : (
            <MultiSelect label={def.label} options={def.options?.(refs, item) ?? []} values={arr(v)} onChange={(vals) => set(def.key, vals)} />
          )}
          {def.hint && <span className="hint">{def.hint}</span>}
        </div>
      );
    case 'rules':
      return (
        <div className="span-all">
          <RuleEditor
            label={def.label}
            help={def.hint}
            rules={rules(v)}
            onChange={(r) => set(def.key, r)}
            days={refs.days}
            periods={refs.periods}
            yearWeeks={refs.yearWeeks}
          />
        </div>
      );
    case 'examLimits':
      return (
        <div className="span-all">
          <ClassExamLimitsFields
            value={{ max_exams_per_week: item.max_exams_per_week as number | null | undefined, max_exams_per_day: item.max_exams_per_day as number | null | undefined }}
            grade={Number(item.grade) || undefined}
            disabled={disabled}
            onChange={(v) => {
              set('max_exams_per_week', v.max_exams_per_week ?? null);
              set('max_exams_per_day', v.max_exams_per_day ?? null);
            }}
          />
        </div>
      );
    case 'planning':
      return (
        <div className="span-all">
          <ClassPlanningFields
            value={classPlanningOf(item as never)}
            onChange={(p) => {
              set('school_days', p.school_days);
              set('profile', p.profile);
            }}
            settings={refs.settings}
            disabled={disabled || !refs.canPlan}
            profileDisabled={disabled}
          />
        </div>
      );
    case 'holidayKind':
      input = (
        <select id={id} value={holidayKindOf({ name: s(item.name), kind: v as HolidayKind | undefined })} disabled={disabled} onChange={(e) => set(def.key, e.target.value)}>
          {(Object.keys(HOLIDAY_KIND_LABELS) as HolidayKind[]).map((k) => (
            <option key={k} value={k}>
              {HOLIDAY_KIND_LABELS[k]}
            </option>
          ))}
        </select>
      );
      break;
    case 'availability':
      return (
        <TeacherAvailabilityField
          teacherId={s(item.id)}
          isNew={isNew}
          unavailable={rules(item.unavailable)}
          wishes={rules(item.wishes)}
          onChange={(r) => {
            // Zeitfenster und Raster sind in den Sperrzeiten aufgegangen
            set('unavailable', r.unavailable);
            set('wishes', r.wishes);
            set('work_grid', {});
            set('time_windows', []);
          }}
          disabled={disabled}
          refs={refs}
          profile={{ subjects: arr(item.subjects), preferred_classes: arr(item.preferred_classes), max_hours: Number(item.max_hours ?? 0) }}
        />
      );
    case 'commute':
      return (
        <CommuteField
          mode={s(item.commute_mode) || (item.commutes === false ? 'never' : 'free')}
          gap={Number(item.commute_gap ?? 0)}
          onChange={(m, g) => {
            set('commute_mode', m);
            set('commute_gap', g);
            set('commutes', m !== 'never');
          }}
          disabled={disabled}
        />
      );
    case 'datalist':
      input = (
        <>
          <input id={id} type="text" list={`${id}-list`} value={s(v)} disabled={disabled} onChange={(e) => set(def.key, e.target.value === '' && def.nullable ? null : e.target.value)} />
          <datalist id={`${id}-list`}>
            {(def.list?.(refs) ?? []).map((x) => (
              <option key={x} value={x} />
            ))}
          </datalist>
        </>
      );
      break;
    default:
      input = <input id={id} type={def.type === 'email' ? 'email' : 'text'} value={s(v)} disabled={disabled} required={def.required} onChange={(e) => set(def.key, e.target.value)} />;
  }
  return (
    <Field label={def.label + (def.required ? ' *' : '')} htmlFor={id} hint={def.hint} className={def.wide ? 'span-all' : undefined}>
      {input}
    </Field>
  );
}

function EditModal({ def, initial, refs, canEdit, onClose }: { def: Def; initial: AnyRec; refs: Refs; canEdit: boolean; onClose: () => void }) {
  const toast = useToast();
  const user = useUser();
  const isNew = !initial.id;
  const confirm = useConfirmChanges();
  const [item, setItem] = useState<AnyRec>(() => structuredClone(initial));
  const set = (k: string, v: unknown) => setItem((x) => ({ ...x, [k]: v }));
  const name = def.name as CollectionName;
  // Klassen: Stundentafel wird zusammen mit der Klasse gespeichert
  const [curRows, setCurRows] = useState<CurriculumRow[] | null>(null);
  const [curDirty, setCurDirty] = useState(false);

  const save = async () => {
    const missing = def.fields.filter((f) => f.required && (item[f.key] === '' || item[f.key] === null || item[f.key] === undefined));
    if (isNew && !def.autoId && !s(item.id).trim()) missing.unshift({ key: 'id', label: def.idLabel, type: 'text' });
    if (missing.length) {
      toast.warning('Bitte Pflichtfelder ausfüllen', missing.map((m) => m.label));
      return;
    }
    try {
      if (isNew) {
        const body = { ...item };
        if (!s(body.id).trim()) delete body.id;
        await dataApi.create(name, body as Partial<CollectionTypes[typeof name]>);
        toast.success(`${def.singular} angelegt`);
      } else {
        // 409 `plan_change` (Unterrichtstage einer Klasse): Liste zeigen, mit „Trotzdem übernehmen“ ?force=1
        const done = await confirm.run(async (force) => {
          await dataApi.update(name, s(item.id), item as unknown as CollectionTypes[typeof name], force);
          return true;
        });
        if (!done) return;
        toast.success(`${def.singular} gespeichert`);
      }
      if (def.name === 'classes' && curRows && curDirty && (!isNew || curRows.length > 0)) {
        try {
          await classesApi.putCurriculum(s(item.id), curRows);
          toast.success('Stundentafel gespeichert – der Stundenplan wird automatisch ergänzt');
          invalidate('curricula');
          invalidate('courses');
        } catch (e) {
          toast.error(e, 'Stundentafel');
        }
      }
      invalidate(name);
      onClose();
    } catch (e) {
      toast.error(e, 'Speichern');
    }
  };

  const [deletingClass, setDeletingClass] = useState(false);
  const remove = async () => {
    // Klassen: eigener Dialog mit Folgen (Schüler/innen, Kurse, Stunden) und Verschieben der Schüler/innen
    if (def.name === 'classes') {
      setDeletingClass(true);
      return;
    }
    if (!(await confirmAsk({ title: `${def.singular} löschen`, message: `${def.singular} „${s(item.name) || s(item.id)}“ löschen?`, confirmLabel: 'Löschen', danger: true }))) return;
    try {
      await dataApi.remove(name, s(item.id));
    } catch (e) {
      if (e instanceof ApiError && e.isConflict) {
        if (!(await confirmAsk({ title: 'Verweise vorhanden', confirmLabel: 'Trotzdem löschen', danger: true, message: `${e.message}\n${e.conflicts.slice(0, 12).join('\n')}\n\nTrotzdem löschen? Verweise werden entfernt.` }))) return;
        try {
          await dataApi.remove(name, s(item.id), true);
        } catch (e2) {
          toast.error(e2, 'Löschen');
          return;
        }
      } else {
        toast.error(e, 'Löschen');
        return;
      }
    }
    toast.success(`${def.singular} gelöscht`);
    invalidate(name);
    onClose();
  };

  return (
    <Modal
      size="lg"
      title={isNew ? `${def.singular} anlegen` : `${def.singular}: ${s(item.name) || s(item.id)}`}
      onClose={onClose}
      footer={
        canEdit ? (
          <>
            {!isNew && (
              <button type="button" className="btn btn-ghost" onClick={remove}>
                <Icon name="trash" /> Löschen
              </button>
            )}
            <button type="button" className="btn" onClick={onClose}>
              Abbrechen
            </button>
            <AsyncButton className="btn btn-primary" onClick={save}>
              Speichern
            </AsyncButton>
          </>
        ) : undefined
      }
    >
      <form
        className="form-grid"
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <Field
          label={`${def.idLabel}${!def.autoId && isNew ? ' *' : ''}`}
          htmlFor="md-id"
          hint={isNew ? (def.autoId ? 'leer lassen = automatisch' : 'eindeutig, später nicht änderbar') : 'nicht änderbar'}
        >
          <input id="md-id" type="text" value={s(item.id)} disabled={!isNew || !canEdit} onChange={(e) => set('id', e.target.value.trim())} />
        </Field>
        {def.fields.map((f) => (
          <FieldInput key={f.key} def={f} item={item} set={set} refs={refs} disabled={!canEdit} isNew={isNew} />
        ))}
        {def.name === 'classes' && (
          <ClassCurriculumSection
            classId={isNew ? null : s(item.id)}
            grade={Number(item.grade) || 0}
            profile={s(item.profile) || null}
            rows={curRows}
            onRows={setCurRows}
            onEdit={(r) => {
              setCurRows(r);
              setCurDirty(true);
            }}
            disabled={!canEdit}
          />
        )}
        <button type="submit" hidden />
      </form>
      {def.name === 'students' && !isNew && can(user, 'students.birth_date') && (
        <BirthDateEditor studentId={s(item.id)} name={s(item.name)} value={typeof item.birth_date === 'string' ? item.birth_date : null} />
      )}
      {def.name === 'students' && !isNew && <StudentDetail studentId={s(item.id)} classId={s(item.class_id)} />}
      {confirm.dialog}
      {deletingClass && (
        <DeleteClassesDialog
          title={`Klasse ${s(item.name) || s(item.id)}`}
          ids={[s(item.id)]}
          onClose={() => setDeletingClass(false)}
          onDone={() => {
            invalidate(name);
            onClose();
          }}
        />
      )}
    </Modal>
  );
}

function CollectionView({ def, refs, canEdit }: { def: Def; refs: Refs; canEdit: boolean }) {
  const col = useCollection(def.name);
  const [q, setQ] = useState('');
  const query = useDebounced(q, 120);
  const [classFilter, setClassFilter] = useState<string | null>(null);
  const [edit, setEdit] = useState<AnyRec | null>(null);
  const [catalogOpen, setCatalogOpen] = useState(false);
  const user = useUser();
  const supportSeen = def.name === 'students' && can(user, ['support.read', 'support.hints']);
  const flags = useApi((signal) => supportApi.flags(signal), [], { live: ['student_support', 'support_catalog'], enabled: supportSeen });
  const [search, setSearch] = useSearchParams();
  const deepLink = def.name === 'teachers' ? search.get('lehrkraft') : null;
  useEffect(() => {
    if (!deepLink || !col.data) return;
    const hit = (col.data as unknown as AnyRec[]).find((x) => s(x.id) === deepLink);
    if (hit) setEdit(hit);
    const sp = new URLSearchParams(search);
    sp.delete('lehrkraft');
    setSearch(sp, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deepLink, col.data]);
  const rows = useMemo(() => {
    let list = (col.data ?? []) as unknown as AnyRec[];
    if (def.name === 'students' && classFilter) list = list.filter((x) => x.class_id === classFilter);
    if (query) list = list.filter((x) => matchesQuery(def.search(x), query));
    return list;
  }, [col.data, query, classFilter, def]);
  const columns = useMemo(() => {
    const cols = def.columns(refs);
    if (def.name === 'classes')
      cols.push({
        key: 'rhythm',
        header: 'Regeln',
        render: (x) => (
          <span className="small muted" title={rules(x.unavailable).map((r) => describeRule(r)).join('\n')}>
            {rules(x.unavailable)
              .map((r) => describeRule(r))
              .join('; ')}
          </span>
        ),
      });
    if (def.name === 'students' && supportSeen)
      cols.push({
        key: 'support',
        header: 'Merkmale',
        render: (x) => (
          <span className="row" style={{ gap: 4, flexWrap: 'wrap' }}>
            {(flags.data?.flags[s(x.id)] ?? []).map((f) => (
              <span key={f} className="badge badge-primary">
                {f}
              </span>
            ))}
          </span>
        ),
      });
    return cols;
  }, [def, refs, supportSeen, flags.data]);

  if (col.error) return <ErrorBox error={col.error} onRetry={col.reload} />;
  if (!col.data) return <Loading />;

  return (
    <div>
      <div className="toolbar">
        <div className="field wide">
          <label htmlFor={`q-${def.name}`}>Suche in {def.label}</label>
          <input id={`q-${def.name}`} type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Suchbegriff …" />
        </div>
        {def.name === 'students' && (
          <div className="field">
            <SearchSelect label="Klasse" options={refs.classes} value={classFilter} onChange={setClassFilter} allowClear placeholder="alle Klassen" />
          </div>
        )}
        {def.name === 'students' && can(user, ['support.catalog', 'support.manage', 'support.read']) && (
          <button type="button" className="btn" onClick={() => setCatalogOpen(true)}>
            Katalog der Merkmale
          </button>
        )}
        {canEdit && (
          <button type="button" className="btn btn-primary" onClick={() => setEdit({ ...def.blank(), ...(def.name === 'students' && classFilter ? { class_id: classFilter } : {}) })}>
            <Icon name="plus" /> {def.singular} anlegen
          </button>
        )}
      </div>
      <VirtualTable rows={rows} columns={columns} rowKey={(x) => s(x.id)} onRowClick={(x) => setEdit(x)} caption={def.label} height="64vh" />
      {edit && <EditModal def={def} initial={edit} refs={refs} canEdit={canEdit} onClose={() => setEdit(null)} />}
      {catalogOpen && <SupportCatalogDialog onClose={() => setCatalogOpen(false)} />}
    </div>
  );
}

export default function MasterDataPage() {
  useTitle('Stammdaten');
  const user = useUser();
  const navigate = useNavigate();
  const { tab } = useParams<{ tab: string }>();
  const canEdit = can(user, 'masterdata.edit');
  const canPlan = can(user, 'timetable.edit');
  const { data: settings } = useSettings();
  const sites = useCollection('sites');
  const rooms = useCollection('rooms');
  const subjects = useCollection('subjects');
  const teachers = useCollection('teachers');
  const classes = useCollection('classes');
  const gradeTab = tab === GRADE_TAB;
  const active = DEFS.find((d) => d.name === tab) ?? (DEFS[0] as Def);
  const courses = useCollection('courses', active.name === 'students');

  const refs: Refs = useMemo(
    () => ({
      sites: (sites.data ?? []).map((x) => ({ value: x.id, label: x.name })),
      rooms: sortBy(rooms.data ?? [], (x) => x.id).map((x) => ({ value: x.id, label: x.id, sub: x.type })),
      subjects: sortBy(subjects.data ?? [], (x) => x.id).map((x) => ({ value: x.id, label: `${x.id} – ${x.name}` })),
      teachers: sortBy(teachers.data ?? [], (x) => x.name).map((x) => ({ value: x.id, label: x.name, sub: x.id })),
      classes: sortBy(classes.data ?? [], (x) => x.name).map((x) => ({ value: x.id, label: x.name })),
      roomTypes: [...new Set([...(rooms.data ?? []).map((r) => r.type), ...(subjects.data ?? []).map((x) => x.room_type ?? '')].filter(Boolean))].sort(),
      courseParts: (classId: string) =>
        (courses.data ?? [])
          .filter((c) => !classId || c.classes.includes(classId))
          .flatMap((c) =>
            c.parts.length > 1 || c.classes.length > 1
              ? c.parts.map((p, i) => ({ value: `${c.id}#${i}`, label: `${c.label || c.id}: ${p.label || p.subject}`, sub: p.teacher ?? undefined }))
              : [],
          ),
      // bis zum letzten Schulöffnungstag (Schule und Klassen mit eigenen Unterrichtstagen, R3)
      days: Math.max(...schoolDaysOf(settings), ...(classes.data ?? []).flatMap((c) => c.school_days ?? [])) + 1,
      periods: settings?.periods ?? 10,
      periodTimes: (settings?.period_times ?? []).slice(0, settings?.periods ?? 10),
      periodMinutes: (settings as { period_minutes?: number } | undefined)?.period_minutes ?? 45,
      schoolDays: schoolDaysOf(settings),
      yearWeeks: 52,
      canPlan,
      settings: settings ?? null,
    }),
    [sites.data, rooms.data, subjects.data, teachers.data, classes.data, courses.data, settings, canPlan],
  );

  return (
    <div className="page">
      <div className="page-head">
        <h1>Stammdaten</h1>
        {!canEdit && <span className="badge">nur lesen</span>}
      </div>
      <Tabs label="Stammdaten-Bereiche" tabs={masterTabs()} active={gradeTab ? GRADE_TAB : active.name} onChange={(k) => navigate(`/stammdaten/${k}`)} />
      <div role="tabpanel" aria-label={gradeTab ? 'Klassenstufen' : active.label}>
        {gradeTab ? <GradeLevelsView /> : <CollectionView key={active.name} def={active} refs={refs} canEdit={canEdit} />}
      </div>
    </div>
  );
}

export type { Item };
