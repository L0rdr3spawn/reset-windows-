/**
 * Verständliche Fehlermeldungen (B-13, A-59): übersetzt Validierungsfehler des Backends (FastAPI/Pydantic,
 * `detail: [{type, loc, msg, ctx}]`) ins Deutsche und ersetzt Feldcodes durch Beschriftungen.
 *
 * - {@link FIELD_LABELS}: allgemeine Zuordnung Feldcode → Beschriftung; Formulare ergänzen sie mit eigenen `labels`.
 * - {@link translateValidation}: Meldung ohne technische Pfade (`message`), Texte je Feld (`fields`) für `Field`.
 * - {@link looksTechnical}: erkennt englische Servertexte und Codes – die werden nie angezeigt.
 *
 * Reine Logik ohne DOM/React (vitest in `node`).
 */

export interface ValidationItem {
  type?: unknown;
  loc?: unknown;
  msg?: unknown;
  ctx?: unknown;
}

/** Beschriftung eines Felds; `ask` = Ergänzung für „Bitte … angeben.“ (mit Artikel), `missing` = eigener Text. */
export interface FieldLabel {
  label: string;
  ask?: string;
  missing?: string;
}

/** Je Formular ergänzbare Zuordnung Feldcode (z. B. `date_from`, `items.name`) → Beschriftung. */
export type FieldLabels = Record<string, string | FieldLabel>;

/** Allgemeine Zuordnungsliste (häufige Felder der API). Formulare ergänzen per `labels`. */
export const FIELD_LABELS: Readonly<Record<string, FieldLabel>> = {
  date_from: { label: 'Startdatum', ask: 'ein Startdatum' },
  date_to: { label: 'Enddatum', ask: 'ein Enddatum' },
  date: { label: 'Datum', ask: 'ein Datum' },
  day: { label: 'Tag', ask: 'einen Tag' },
  days: { label: 'Tage', missing: 'Bitte mindestens einen Tag wählen.' },
  start: { label: 'Beginn', ask: 'einen Beginn' },
  end: { label: 'Ende', ask: 'ein Ende' },
  period: { label: 'Stunde', ask: 'eine Stunde' },
  periods: { label: 'Stunden', ask: 'die Stunden' },
  week: { label: 'Woche', ask: 'eine Woche' },
  weeks: { label: 'Wochen', missing: 'Bitte mindestens eine Woche wählen.' },
  due_at: { label: 'Fällig am', ask: 'ein Fälligkeitsdatum' },
  visible_from: { label: 'Sichtbar ab', ask: 'ein Datum für „Sichtbar ab“' },
  kind: { label: 'Art', missing: 'Bitte eine Art wählen.' },
  ref: { label: 'Auswahl', missing: 'Bitte eine Auswahl treffen.' },
  reason: { label: 'Grund', ask: 'einen Grund' },
  note: { label: 'Vermerk', ask: 'einen Vermerk' },
  name: { label: 'Name', ask: 'einen Namen' },
  display_name: { label: 'Anzeigename', ask: 'einen Anzeigenamen' },
  username: { label: 'Benutzername', ask: 'einen Benutzernamen' },
  password: { label: 'Passwort', ask: 'ein Passwort' },
  new_password: { label: 'Neues Passwort', ask: 'ein neues Passwort' },
  email: { label: 'E-Mail-Adresse', ask: 'eine E-Mail-Adresse' },
  phone: { label: 'Telefonnummer', ask: 'eine Telefonnummer' },
  role: { label: 'Rolle', missing: 'Bitte eine Rolle wählen.' },
  status: { label: 'Status', missing: 'Bitte einen Status wählen.' },
  code: { label: 'Code', ask: 'den Code' },
  title: { label: 'Titel', ask: 'einen Titel' },
  subject: { label: 'Betreff', ask: 'einen Betreff' },
  body: { label: 'Text', ask: 'einen Text' },
  text: { label: 'Text', ask: 'einen Text' },
  message: { label: 'Nachricht', ask: 'eine Nachricht' },
  description: { label: 'Beschreibung', ask: 'eine Beschreibung' },
  url: { label: 'Adresse', ask: 'eine Adresse' },
  visibility: { label: 'Sichtbarkeit', missing: 'Bitte die Sichtbarkeit wählen.' },
  recipients: { label: 'Empfänger', missing: 'Bitte mindestens einen Empfänger wählen.' },
  student_id: { label: 'Schüler/in', missing: 'Bitte eine Schülerin oder einen Schüler wählen.' },
  student_ids: { label: 'Schüler/innen', missing: 'Bitte mindestens eine Schülerin oder einen Schüler wählen.' },
  teacher_id: { label: 'Lehrkraft', missing: 'Bitte eine Lehrkraft wählen.' },
  teacher: { label: 'Lehrkraft', missing: 'Bitte eine Lehrkraft wählen.' },
  class_id: { label: 'Klasse', missing: 'Bitte eine Klasse wählen.' },
  class_ids: { label: 'Klassen', missing: 'Bitte mindestens eine Klasse wählen.' },
  course_id: { label: 'Kurs', missing: 'Bitte einen Kurs wählen.' },
  lesson: { label: 'Stunde', missing: 'Bitte eine Stunde wählen.' },
  lesson_id: { label: 'Stunde', missing: 'Bitte eine Stunde wählen.' },
  room: { label: 'Raum', missing: 'Bitte einen Raum wählen.' },
  room_id: { label: 'Raum', missing: 'Bitte einen Raum wählen.' },
  site: { label: 'Standort', missing: 'Bitte einen Standort wählen.' },
  grade: { label: 'Jahrgang', ask: 'einen Jahrgang' },
  folder_id: { label: 'Ordner', missing: 'Bitte einen Ordner wählen.' },
  attachment_ids: { label: 'Anhänge' },
  file_ids: { label: 'Dateien' },
  school_name: { label: 'Schulname', ask: 'einen Schulnamen' },
  school_year_start: { label: 'Beginn des Schuljahres', ask: 'den Beginn des Schuljahres' },
  week_numbering: { label: 'Wochenzählung' },
  school_days: { label: 'Unterrichtstage', missing: 'Bitte mindestens einen Unterrichtstag wählen.' },
  week_pattern: { label: 'Rhythmus' },
  rhythm: { label: 'Rhythmus' },
  max_hours: { label: 'Deputat', ask: 'ein Deputat' },
  time_limit: { label: 'Laufzeit', ask: 'eine Laufzeit' },
};

/** Ein übersetzter Validierungsfehler. */
export interface FieldIssue {
  /** Feldcode ohne `body`/`query`/Listenindex, z. B. `date_from` oder `items.name`; leer = ganzes Formular */
  field: string;
  /** Beschriftung oder leer, wenn unbekannt */
  label: string;
  /** Text am Feld, z. B. „Bitte ein gültiges Datum angeben.“ */
  text: string;
  /** Meldung ohne Feld daneben, z. B. „Startdatum: Bitte ein gültiges Datum angeben.“ */
  summary: string;
  /** Pydantic-Typ (`missing`, `string_too_long` …) */
  type: string;
}

export interface TranslatedValidation {
  /** eine Meldung für Toast/Alert (ohne technische Pfade) */
  message: string;
  /** Feldcode → Text am Feld (nur Felder, nicht formularweite Fehler) */
  fields: Record<string, string>;
  issues: FieldIssue[];
}

const LOC_ROOTS = new Set(['body', 'query', 'path', 'header', 'cookie', 'form']);

/** Feldcode aus `loc`: `['body','items',2,'name']` → `items.name`, `['query','date']` → `date`. */
export function fieldKey(loc: unknown): string {
  if (!Array.isArray(loc)) return '';
  const parts = loc.filter((x): x is string => typeof x === 'string');
  if (parts.length && LOC_ROOTS.has(parts[0] as string)) parts.shift();
  return parts.join('.');
}

function lookup(key: string, labels?: FieldLabels): FieldLabel | null {
  if (!key) return null;
  const parts = key.split('.');
  // erst der ganze Pfad, dann immer kürzere Enden (`items.name` → `name`)
  for (let i = 0; i < parts.length; i++) {
    const k = parts.slice(i).join('.');
    const own = labels?.[k];
    if (own) return typeof own === 'string' ? { label: own } : own;
    const general = FIELD_LABELS[k];
    if (general) return general;
  }
  return null;
}

const GERMAN = /[äöüßÄÖÜ„“]|\b(der|die|das|den|dem|des|und|oder|nicht|kein|keine|ist|sind|bitte|für|mit|nur|ein|eine|einen|wird|werden|kann|zu|im|am|vom|bei|nach|schon|bereits|ungültig\w*|fehlt)\b/i;
const ENGLISH = /\b(the|is|are|not|no|found|invalid|error|required|field|should|must|allowed|method|internal|input|value|valid|unable|failed|denied|forbidden|unauthorized|missing|too|many|requests|entity|large|already|exists|cannot|could|please|bad|request|gateway|timeout|unavailable|service|payload|unprocessable|content)\b/i;

/**
 * Ist ein Servertext für die Oberfläche ungeeignet? Codes (`not_authenticated`, `x.y`) und englische Texte
 * („Not Found“, „Field required“, „Method Not Allowed“) ja, deutsche Sätze nein.
 */
export function looksTechnical(text: string): boolean {
  const t = text.trim();
  if (!t) return true;
  if (/^[a-z][a-z0-9]*([_.][a-z0-9]+)+$/.test(t)) return true; // snake_case-/Punkt-Code
  if (/^[a-z]+$/.test(t)) return true; // einzelnes kleines Wort, z. B. „forbidden“
  if (/\b(body|query)\.[a-z_]+/.test(t) || /Traceback|Exception|Error:/.test(t)) return true;
  if (GERMAN.test(t)) return false;
  return ENGLISH.test(t);
}

function num(v: unknown): string {
  return typeof v === 'number' ? String(v).replace('.', ',') : String(v ?? '');
}

function ctxOf(item: ValidationItem): Record<string, unknown> {
  return item.ctx && typeof item.ctx === 'object' ? (item.ctx as Record<string, unknown>) : {};
}

function missingText(meta: FieldLabel | null): string {
  if (meta?.missing) return meta.missing;
  if (meta?.ask) return `Bitte ${meta.ask} angeben.`;
  if (meta) return `Bitte „${meta.label}“ angeben.`;
  return 'Bitte alle Pflichtangaben ausfüllen.';
}

/** Formularweite Fehler (kein Feld anzeigen) */
const FORM_LEVEL: Record<string, string> = {
  extra_forbidden: 'Das Formular ist nicht mehr aktuell. Bitte die Seite neu laden.',
  json_invalid: 'Die Eingabe konnte nicht gelesen werden. Bitte erneut versuchen.',
  json_type: 'Die Eingabe konnte nicht gelesen werden. Bitte erneut versuchen.',
};

const DATE_TYPES = /^(date_(parsing|type|from_datetime_parsing|from_datetime_inexact))$/;
const DATETIME_TYPES = /^(datetime_(parsing|type|object_invalid|from_date_parsing)|timezone_(aware|naive))$/;

/** Text am Feld für einen Pydantic-Fehlertyp (ohne Beschriftung, außer bei „fehlt“). */
function textFor(type: string, item: ValidationItem, meta: FieldLabel | null): string {
  const ctx = ctxOf(item);
  switch (true) {
    case type === 'missing':
      return missingText(meta);
    case type === 'string_too_short':
      return Number(ctx.min_length ?? 1) <= 1 ? missingText(meta) : `Bitte mindestens ${num(ctx.min_length)} Zeichen eingeben.`;
    case type === 'string_too_long':
      return `Bitte höchstens ${num(ctx.max_length)} Zeichen eingeben.`;
    case type === 'too_short':
      return Number(ctx.min_length ?? 1) <= 1 ? (meta?.missing ?? 'Bitte mindestens einen Eintrag wählen.') : `Bitte mindestens ${num(ctx.min_length)} Einträge wählen.`;
    case type === 'too_long':
      return `Bitte höchstens ${num(ctx.max_length)} Einträge wählen.`;
    case type === 'greater_than_equal':
      return `Bitte einen Wert ab ${num(ctx.ge)} angeben.`;
    case type === 'greater_than':
      return `Bitte einen Wert über ${num(ctx.gt)} angeben.`;
    case type === 'less_than_equal':
      return `Bitte einen Wert bis ${num(ctx.le)} angeben.`;
    case type === 'less_than':
      return `Bitte einen Wert unter ${num(ctx.lt)} angeben.`;
    case type === 'multiple_of':
      return `Bitte ein Vielfaches von ${num(ctx.multiple_of)} angeben.`;
    case /^int_(parsing|type|from_float|parsing_size)$/.test(type):
      return 'Bitte eine ganze Zahl angeben.';
    case /^(float|decimal)_(parsing|type)$/.test(type) || type === 'finite_number':
      return 'Bitte eine Zahl angeben.';
    case DATE_TYPES.test(type):
      return 'Bitte ein gültiges Datum angeben.';
    case type === 'date_past':
      return 'Bitte ein Datum in der Vergangenheit angeben.';
    case type === 'date_future':
      return 'Bitte ein Datum in der Zukunft angeben.';
    case DATETIME_TYPES.test(type):
      return 'Bitte ein gültiges Datum mit Uhrzeit angeben.';
    case /^time_(parsing|type)$/.test(type):
      return 'Bitte eine gültige Uhrzeit angeben (hh:mm).';
    case /^bool_(parsing|type)$/.test(type):
      return 'Bitte Ja oder Nein wählen.';
    case type === 'literal_error' || type === 'enum':
      return 'Bitte einen der angebotenen Werte wählen.';
    case type === 'string_type':
      return 'Bitte einen Text angeben.';
    case type === 'string_pattern_mismatch':
      return 'Bitte die Schreibweise prüfen.';
    case /^url_/.test(type):
      return 'Bitte eine gültige Adresse angeben.';
    case /^(list|set|tuple|frozen_set)_type$/.test(type):
      return 'Bitte die Auswahl prüfen.';
    case type === 'value_error' || type === 'assertion_error': {
      const msg = String(item.msg ?? '').replace(/^(Value error|Assertion failed),\s*/i, '');
      return msg && !looksTechnical(msg) ? msg.replace(/([^.!?])$/, '$1.') : 'Bitte die Eingabe prüfen.';
    }
    default: {
      // unbekannter Typ: deutschen Text des Servers übernehmen, englischen nie
      const msg = String(item.msg ?? '');
      return msg && !looksTechnical(msg) ? msg : 'Bitte die Eingabe prüfen.';
    }
  }
}

/** Einen Validierungsfehler übersetzen. */
export function translateIssue(item: ValidationItem, labels?: FieldLabels): FieldIssue {
  const type = typeof item.type === 'string' ? item.type : '';
  const formLevel = FORM_LEVEL[type];
  if (formLevel) return { field: '', label: '', text: formLevel, summary: formLevel, type };
  const field = fieldKey(item.loc);
  const meta = lookup(field, labels);
  const text = textFor(type, item, meta);
  const label = meta?.label ?? '';
  // „Bitte ein Startdatum angeben.“ nennt das Feld schon; sonst Beschriftung voranstellen (wenn bekannt)
  const named = !label || text.includes(label) || (!!meta?.ask && text.includes(meta.ask)) || (!!meta?.missing && text === meta.missing);
  const summary = named ? text : `${label}: ${text}`;
  return { field, label, text, summary, type };
}

/** Liste von Validierungsfehlern übersetzen (doppelte Meldungen zusammengefasst). */
export function translateValidation(items: readonly unknown[], labels?: FieldLabels): TranslatedValidation {
  const issues: FieldIssue[] = [];
  const fields: Record<string, string> = {};
  const seen = new Set<string>();
  for (const raw of items) {
    const item: ValidationItem = raw && typeof raw === 'object' ? (raw as ValidationItem) : { msg: String(raw) };
    const issue = translateIssue(item, labels);
    if (seen.has(issue.summary)) continue;
    seen.add(issue.summary);
    issues.push(issue);
    if (issue.field && !(issue.field in fields)) fields[issue.field] = issue.text;
  }
  const message = issues.length ? issues.map((i) => i.summary).join(' ') : 'Bitte die Eingabe prüfen.';
  return { message, fields, issues };
}

/** Pydantic-Liste? (`[{loc, msg, type}]`) */
export function isValidationList(detail: unknown): detail is unknown[] {
  return Array.isArray(detail) && detail.length > 0 && detail.every((d) => d && typeof d === 'object' && ('loc' in d || 'type' in d));
}

/** Kurze Fehlernummer für den Support (erste 8 Zeichen der Request-ID, groß). */
export function shortErrorId(requestId: string): string {
  return requestId.replace(/[^0-9a-zA-Z]/g, '').slice(0, 8).toUpperCase();
}

/** Text für unerwartete Fehler (Serverfehler, Codes, englische Texte). */
export function unexpectedText(errorId?: string | null): string {
  return errorId ? `Das hat nicht geklappt. Bitte später erneut versuchen. Fehlernummer: ${errorId}` : 'Das hat nicht geklappt. Bitte später erneut versuchen.';
}
