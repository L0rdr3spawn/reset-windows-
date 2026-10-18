/**
 * Reine Hilfen des Formular-Baukastens (ohne React): Vorlagen-Gerüst, Felder bearbeiten, Antworten vorbereiten und
 * vorab prüfen (der Server prüft immer erneut), Statusdarstellung.
 */
import type { Answers, FieldType, FormAction, FormDefinition, FormField, FormStatus, FormStep, Submission, TemplateStatus } from './api';

export const FIELD_ORDER: FieldType[] = [
  'text',
  'textarea',
  'number',
  'date',
  'daterange',
  'select',
  'multiselect',
  'yesno',
  'confirm',
  'signature',
  'file',
  'student',
  'periods',
  'scale',
];

/** Felder mit Auswahlmöglichkeiten */
export const hasOptions = (t: FieldType): boolean => t === 'select' || t === 'multiselect';

export function emptyDefinition(): FormDefinition {
  return {
    fields: [],
    intro: '',
    once: false,
    legacy_pdf: null,
    audience: { roles: ['eltern'], scope: 'all', classes: [], grades: [] },
    workflow: { steps: [], auto_complete: false },
    deadline: { open_from: null, open_until: null, decide_days: null, remind_days: null },
    actions: [],
    notify: { submitter: true },
  };
}

/** Nächste freie Feldkennung (`f1`, `f2` …) */
export function nextFieldId(fields: readonly FormField[]): string {
  const used = new Set(fields.map((f) => f.id));
  let n = fields.length + 1;
  while (used.has(`f${n}`)) n += 1;
  return `f${n}`;
}

export function newField(type: FieldType, fields: readonly FormField[], label = ''): FormField {
  const f: FormField = { id: nextFieldId(fields), type, label, required: type === 'signature' || type === 'confirm' || type === 'student' };
  if (hasOptions(type)) f.options = ['Option 1', 'Option 2'];
  return f;
}

/** Element von `from` nach `from + dir` verschieben (Grenzen werden eingehalten). */
export function moveItem<T>(list: readonly T[], from: number, dir: -1 | 1): T[] {
  const to = from + dir;
  if (to < 0 || to >= list.length) return [...list];
  const copy = [...list];
  const [item] = copy.splice(from, 1);
  copy.splice(to, 0, item as T);
  return copy;
}

export const TYPE_HINT: Record<FieldType, string> = {
  text: 'Eine Zeile',
  textarea: 'Mehrere Zeilen',
  number: 'Zahl, optional mit Grenzen',
  date: 'Ein Tag',
  daterange: 'Von – bis',
  select: 'Eine Antwort aus einer Liste',
  multiselect: 'Mehrere Antworten aus einer Liste',
  yesno: 'Ja oder Nein',
  confirm: 'Häkchen „Ich bestätige“',
  signature: 'Name + Datum (Unterschrift online)',
  file: 'Foto/PDF anhängen',
  student: 'Kind bzw. Schüler/in',
  periods: 'Unterrichtsstunden wählen',
  scale: 'Skala von 1 bis 5',
};

/** Felder, die eine Aktion als Quelle braucht, passend zum Aktionsfeld */
export function fieldsOfType(fields: readonly FormField[], ...types: FieldType[]): FormField[] {
  return fields.filter((f) => types.includes(f.type));
}

/** Aktionen, die auf ein gelöschtes Feld zeigen, bereinigen (Feld wird ersetzt/entfernt). */
export function dropFieldRefs(actions: readonly FormAction[], fieldId: string): FormAction[] {
  return actions
    .map((a) => ({
      ...a,
      student: a.student === fieldId ? null : a.student,
      range: a.range === fieldId ? null : a.range,
      periods: a.periods === fieldId ? null : a.periods,
      reason: a.reason === fieldId ? null : a.reason,
      date: a.date === fieldId ? null : a.date,
    }))
    .filter((a) => !(a.type === 'create_absence' && !a.range) && !(a.type === 'calendar_entry' && !a.date));
}

// ---------------------------------------------------------------------------------------------- Antworten
export function initialAnswers(defn: FormDefinition): Answers {
  const out: Answers = {};
  for (const f of defn.fields) {
    switch (f.type) {
      case 'multiselect':
      case 'periods':
      case 'file':
        out[f.id] = [];
        break;
      case 'daterange':
        out[f.id] = { from: '', to: '' };
        break;
      case 'confirm':
        out[f.id] = false;
        break;
      case 'yesno':
        out[f.id] = null;
        break;
      case 'signature':
        out[f.id] = { name: '' };
        break;
      default:
        out[f.id] = '';
    }
  }
  return out;
}

function isEmpty(f: FormField, v: unknown): boolean {
  if (v === null || v === undefined || v === '') return true;
  if (Array.isArray(v)) return v.length === 0;
  if (f.type === 'daterange') return !(v as { from?: string }).from;
  if (f.type === 'signature') return !String((v as { name?: string }).name ?? '').trim();
  if (f.type === 'confirm') return v !== true;
  return false;
}

/** Fehler je Feldkennung (leer = in Ordnung). Der Server prüft immer erneut. */
export function answerErrors(defn: FormDefinition, answers: Answers, studentId: string | null | undefined, needsStudent: boolean): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const f of defn.fields) {
    if (f.type === 'student') {
      if (!studentId) errors[f.id] = 'Bitte auswählen.';
      continue;
    }
    const v = answers[f.id];
    if (f.required && isEmpty(f, v)) {
      errors[f.id] = f.type === 'confirm' ? 'Bitte bestätigen.' : f.type === 'signature' ? 'Bitte mit vollem Namen unterschreiben.' : 'Bitte ausfüllen.';
      continue;
    }
    if (f.type === 'daterange' && !isEmpty(f, v)) {
      const r = v as { from: string; to: string };
      if (r.to && r.to < r.from) errors[f.id] = 'Das Ende liegt vor dem Beginn.';
    }
    if (f.type === 'number' && v !== '' && v !== null && v !== undefined) {
      const n = Number(String(v).replace(',', '.'));
      if (Number.isNaN(n)) errors[f.id] = 'Bitte eine Zahl eingeben.';
      else if ((f.min !== undefined && n < f.min) || (f.max !== undefined && n > f.max)) errors[f.id] = `Erlaubt: ${f.min ?? '…'} bis ${f.max ?? '…'}.`;
    }
  }
  if (needsStudent && !studentId && !defn.fields.some((f) => f.type === 'student')) errors.__student = 'Bitte die Schülerin / den Schüler auswählen.';
  return errors;
}

// ---------------------------------------------------------------------------------------------- Status
export type Tone = 'success' | 'warning' | 'danger' | 'info' | 'primary';

export const STATUS_TONE: Record<FormStatus, Tone> = {
  eingereicht: 'info',
  in_pruefung: 'warning',
  genehmigt: 'success',
  abgelehnt: 'danger',
  erledigt: 'success',
  zurueckgezogen: 'primary',
};

export const TEMPLATE_TONE: Record<TemplateStatus, Tone> = { entwurf: 'warning', aktiv: 'success', archiviert: 'primary' };
export const TEMPLATE_LABEL: Record<TemplateStatus, string> = { entwurf: 'Entwurf', aktiv: 'Aktiv', archiviert: 'Archiviert' };

export const isOpen = (s: Pick<Submission, 'status'>): boolean => s.status === 'eingereicht' || s.status === 'in_pruefung';

export const EVENT_LABEL: Record<string, string> = {
  eingereicht: 'Eingereicht',
  geprueft: 'Schritt freigegeben',
  genehmigt: 'Genehmigt',
  abgelehnt: 'Abgelehnt',
  erledigt: 'Als erledigt markiert',
  zurueckgezogen: 'Zurückgezogen',
  scan: 'Unterschriebener Scan hochgeladen',
  aktion: 'Aktion ausgeführt',
  erinnerung: 'Erinnerung',
  kommentar: 'Vermerk',
};

/** Kurzfassung des Ablaufs: „Klassenleitung → Schulleitung“ bzw. „Direkt erledigt“ / „Manuell abschließen“. */
export function workflowText(steps: readonly FormStep[], autoComplete: boolean, labels: Record<string, string>): string {
  if (steps.length) return steps.map((s) => s.label || labels[s.approver] || s.approver).join(' → ');
  return autoComplete ? 'Sofort erledigt' : 'Eingang prüft und schließt ab';
}

/** Vorlage veröffentlichen? Liefert den Grund, warum nicht (oder `null`). */
export function publishBlocker(defn: FormDefinition, title: string): string | null {
  if (!title.trim()) return 'Bitte einen Titel angeben.';
  if (!defn.fields.length) return 'Bitte mindestens ein Feld hinzufügen.';
  if (defn.fields.some((f) => !f.label.trim())) return 'Jedes Feld braucht eine Beschriftung.';
  if (defn.fields.some((f) => hasOptions(f.type) && !(f.options ?? []).some((o) => o.trim()))) return 'Auswahlfelder brauchen mindestens eine Möglichkeit.';
  if (!defn.audience.roles.length) return 'Bitte festlegen, wer das Formular ausfüllen darf.';
  return null;
}

/** Textliche Ausgabe der Zielgruppe */
export function audienceText(defn: FormDefinition, roleLabels: Record<string, string>): string {
  const who = defn.audience.roles.map((r) => roleLabels[r] ?? r).join(', ');
  const where = defn.audience.scope === 'classes' ? `Klassen ${defn.audience.classes.join(', ')}` : defn.audience.scope === 'grades' ? `Jahrgänge ${defn.audience.grades.join(', ')}` : 'alle Klassen';
  return `${who} · ${where}`;
}
