/**
 * B-13: verständliche Fehlermeldungen. Die Fehlerkörper sind echte Antworten des Backends (FastAPI/Pydantic,
 * aufgezeichnet am 11.10.2026 gegen die Demo: POST /absences, PUT /settings, PATCH /users/{id}).
 */
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { FormErrors, Field } from '../components/ui';
import { toastErrorContent } from '../context/ToastContext';
import { ApiError, describeDetail, errorInfo, formErrors, http, KNOWN_DETAILS } from './client';
import { fieldKey, looksTechnical, translateValidation } from './errors';

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const v = (type: string, loc: (string | number)[], msg: string, ctx?: Record<string, unknown>) => ({ type, loc, msg, input: null, ...(ctx ? { ctx } : {}) });

/** Die zehn häufigsten Fehlertypen (plus Varianten) mit erwarteter Meldung. */
const CASES: [string, unknown[], string][] = [
  ['1 fehlt (POST /absences ohne Datum)', [v('missing', ['body', 'date_from'], 'Field required')], 'Bitte ein Startdatum angeben.'],
  [
    '2 ungültiges Datum',
    [v('date_from_datetime_parsing', ['body', 'date_from'], 'Input should be a valid date or datetime, invalid character in year', { error: 'invalid character in year' })],
    'Startdatum: Bitte ein gültiges Datum angeben.',
  ],
  ['3 zu lang', [v('string_too_long', ['body', 'reason'], 'String should have at most 500 characters', { max_length: 500 })], 'Grund: Bitte höchstens 500 Zeichen eingeben.'],
  ['4 leer (min_length 1)', [v('string_too_short', ['body', 'ref'], 'String should have at least 1 character', { min_length: 1 })], 'Bitte eine Auswahl treffen.'],
  ['5 zu groß', [v('less_than_equal', ['body', 'periods'], 'Input should be less than or equal to 16', { le: 16 })], 'Stunden: Bitte einen Wert bis 16 angeben.'],
  ['6 zu klein', [v('greater_than_equal', ['body', 'periods'], 'Input should be greater than or equal to 1', { ge: 1 })], 'Stunden: Bitte einen Wert ab 1 angeben.'],
  ['7 keine Zahl (Listeneintrag)', [v('int_parsing', ['body', 'periods', 0], 'Input should be a valid integer, unable to parse string as an integer')], 'Stunden: Bitte eine ganze Zahl angeben.'],
  ['8 unbekannte Auswahl', [v('literal_error', ['body', 'kind'], "Input should be 'teacher', 'class', 'room' or 'lesson'", { expected: "'teacher', 'class', 'room' or 'lesson'" })], 'Art: Bitte einen der angebotenen Werte wählen.'],
  ['9 Ja/Nein', [v('bool_parsing', ['body', 'active'], 'Input should be a valid boolean, unable to interpret input')], 'Bitte Ja oder Nein wählen.'],
  ['10 unbekanntes Feld', [v('extra_forbidden', ['body', 'foo'], 'Extra inputs are not permitted')], 'Das Formular ist nicht mehr aktuell. Bitte die Seite neu laden.'],
  ['11 kaputtes JSON', [v('json_invalid', ['body', 1], 'JSON decode error', { error: 'Expecting property name enclosed in double quotes' })], 'Die Eingabe konnte nicht gelesen werden. Bitte erneut versuchen.'],
  ['12 Liste leer', [v('too_short', ['body', 'student_ids'], 'List should have at least 1 item after validation, not 0', { field_type: 'List', min_length: 1, actual_length: 0 })], 'Bitte mindestens eine Schülerin oder einen Schüler wählen.'],
  ['13 Kommazahl', [v('float_parsing', ['body', 'max_hours'], 'Input should be a valid number')], 'Deputat: Bitte eine Zahl angeben.'],
  ['14 Uhrzeit', [v('time_parsing', ['body', 'start'], 'Input should be in a valid time format')], 'Beginn: Bitte eine gültige Uhrzeit angeben (hh:mm).'],
  ['15 Muster', [v('string_pattern_mismatch', ['body', 'code'], "String should match pattern '^[A-Z]+$'", { pattern: '^[A-Z]+$' })], 'Code: Bitte die Schreibweise prüfen.'],
];

describe('Validierungsfehler auf Deutsch (B-13 Kriterium 1 und 3)', () => {
  it.each(CASES)('%s', (_name, detail, expected) => {
    const text = describeDetail(422, detail);
    expect(text).toBe(expected);
    // nie technische Pfade oder englische Servertexte
    expect(text).not.toMatch(/body\.|date_from|Field required|Input should|Extra inputs|\bloc\b/);
  });

  it('Stichprobe: echte Antwort von POST /absences ohne Datum → „Bitte ein Startdatum angeben.“', async () => {
    const body = { detail: [{ type: 'missing', loc: ['body', 'date_from'], msg: 'Field required', input: { kind: 'teacher', ref: 'LUD' } }] };
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(body), { status: 422, headers: { 'Content-Type': 'application/json', 'X-Request-ID': 'ceb1c0d1053f458b81d08687da272005' } }));
    vi.stubGlobal('fetch', fetchMock);
    const err = await http.post('/absences', { kind: 'teacher', ref: 'LUD' }).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    const e = err as ApiError;
    expect(e.message).toBe('Bitte ein Startdatum angeben.');
    expect(e.fields).toEqual({ date_from: 'Bitte ein Startdatum angeben.' });
    expect(e.unexpected).toBe(false);
    expect(toastErrorContent(e)).toEqual({ title: 'Bitte ein Startdatum angeben.' });
  });

  it('mehrere Fehler: je Feld ein Text, Meldung ohne Pfade, Toast als Liste', () => {
    const detail = [
      v('missing', ['body', 'date_from'], 'Field required'),
      v('string_too_long', ['body', 'reason'], 'String should have at most 500 characters', { max_length: 500 }),
    ];
    const t = translateValidation(detail);
    expect(t.fields).toEqual({ date_from: 'Bitte ein Startdatum angeben.', reason: 'Bitte höchstens 500 Zeichen eingeben.' });
    expect(t.message).toBe('Bitte ein Startdatum angeben. Grund: Bitte höchstens 500 Zeichen eingeben.');
    const e = new ApiError(422, t.message, detail);
    expect(toastErrorContent(e)).toEqual({ title: 'Bitte die Eingaben prüfen.', details: ['Bitte ein Startdatum angeben.', 'Grund: Bitte höchstens 500 Zeichen eingeben.'] });
  });

  it('Formulare ergänzen die Zuordnungsliste (labels), unbekannte Felder bleiben ohne Code', () => {
    const detail = [v('missing', ['body', 'ref'], 'Field required'), v('greater_than_equal', ['body', 'max_exams_per_week'], 'Input should be greater than or equal to 0', { ge: 0 })];
    expect(describeDetail(422, detail)).toBe('Bitte eine Auswahl treffen. Bitte einen Wert ab 0 angeben.');
    const labels = { ref: { label: 'Lehrkraft', missing: 'Bitte eine Lehrkraft wählen.' }, max_exams_per_week: 'Klausuren je Woche' };
    expect(describeDetail(422, detail, labels)).toBe('Bitte eine Lehrkraft wählen. Klausuren je Woche: Bitte einen Wert ab 0 angeben.');
    const e = new ApiError(422, 'x', detail);
    expect(formErrors(e, labels).fields).toEqual({ ref: 'Bitte eine Lehrkraft wählen.', max_exams_per_week: 'Bitte einen Wert ab 0 angeben.' });
    // verschachtelte Felder: ganzer Pfad, sonst das letzte Stück
    expect(fieldKey(['body', 'items', 2, 'name'])).toBe('items.name');
    expect(describeDetail(422, [v('missing', ['body', 'items', 2, 'name'], 'Field required')])).toBe('Bitte einen Namen angeben.');
    expect(describeDetail(422, [v('missing', ['query', 'date'], 'Field required')])).toBe('Bitte ein Datum angeben.');
  });
});

describe('Fehler am Feld (B-13 Kriterium 2)', () => {
  it('Field name=… zeigt den Serverfehler innerhalb von FormErrors, verknüpft und sichtbar', () => {
    const err = new ApiError(422, 'Bitte ein Startdatum angeben.', [v('missing', ['body', 'date_from'], 'Field required')]);
    const html = renderToStaticMarkup(
      createElement(FormErrors, {
        error: err,
        children: [
          createElement(Field, { key: 'a', label: 'Erster Fehltag', name: 'date_from', htmlFor: 'f1', children: createElement('input', { id: 'f1', type: 'date' }) }),
          createElement(Field, { key: 'b', label: 'Grund', name: 'reason', htmlFor: 'f2', children: createElement('input', { id: 'f2' }) }),
        ],
      }),
    );
    expect(html).toContain('class="error-text"');
    expect(html).toContain('Bitte ein Startdatum angeben.');
    expect(html.match(/error-text/g)?.length).toBe(1);
  });

  it('eigener Feldfehler hat Vorrang, ohne FormErrors kein Serverfehler', () => {
    const own = renderToStaticMarkup(createElement(Field, { label: 'Datum', name: 'date', error: 'Bitte wählen.', children: createElement('input') }));
    expect(own).toContain('Bitte wählen.');
    const none = renderToStaticMarkup(createElement(Field, { label: 'Datum', name: 'date', children: createElement('input') }));
    expect(none).not.toContain('error-text');
  });
});

describe('Unerwartete Fehler (B-13 Kriterium 4)', () => {
  it('500 zeigt „Das hat nicht geklappt“ mit Fehlernummer aus der Request-ID', async () => {
    const body = { detail: 'Interner Serverfehler', request_id: '05b5b963bafc4d1cbedb956bfc2e1b45' };
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(body), { status: 500, headers: { 'X-Request-ID': '05b5b963bafc4d1cbedb956bfc2e1b45' } })));
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const e = (await http.get('/x').catch((x: unknown) => x)) as ApiError;
    expect(e.unexpected).toBe(true);
    expect(e.errorId).toBe('05B5B963');
    expect(e.message).toBe('Das hat nicht geklappt. Bitte später erneut versuchen. Fehlernummer: 05B5B963');
  });

  it('Request-ID aus dem Fehlertext, wenn die Kopfzeile fehlt (z. B. hinter einem Proxy)', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ detail: 'Interner Serverfehler', request_id: 'abcdef0123456789' }), { status: 500 })));
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const e = (await http.get('/x').catch((x: unknown) => x)) as ApiError;
    expect(e.errorId).toBe('ABCDEF01');
  });

  it('echter 500 ohne Request-ID (Kopfzeile fehlt, request_id null) zeigt die mitgeschickte ID als Fehlernummer', async () => {
    // so antwortet das Backend bei unbehandelten Fehlern: die äußerste Fehlerbehandlung läuft außerhalb der
    // Request-ID-Middleware (geprüft per TestClient am 11.10.2026)
    const fetchMock = vi.fn(async (_url: string, _init?: RequestInit) => new Response(JSON.stringify({ detail: 'Interner Serverfehler', request_id: null }), { status: 500 }));
    vi.stubGlobal('fetch', fetchMock);
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const e = (await http.post('/absences', { kind: 'teacher' }).catch((x: unknown) => x)) as ApiError;
    const sent = (fetchMock.mock.calls[0]?.[1]?.headers as Record<string, string>)['X-Request-ID'] ?? '';
    expect(sent).toMatch(/^[0-9a-f]{32}$/); // passt zu `_RID_RE` der Middleware, der Server übernimmt sie
    expect(e.unexpected).toBe(true);
    expect(e.requestId).toBe(sent);
    expect(e.errorId).toBe(sent.slice(0, 8).toUpperCase());
    expect(e.message).toBe(`Das hat nicht geklappt. Bitte später erneut versuchen. Fehlernummer: ${e.errorId}`);
    // jede Anfrage bekommt eine eigene ID
    await http.get('/x').catch(() => undefined);
    expect((fetchMock.mock.calls[1]?.[1]?.headers as Record<string, string>)['X-Request-ID']).not.toBe(sent);
  });

  it('englische Texte und unbekannte Codes werden nie angezeigt', () => {
    expect(errorInfo(405, 'Method Not Allowed', 'r1').message).toMatch(/^Das hat nicht geklappt.*Fehlernummer: R1$/);
    expect(errorInfo(400, 'some_new_code', null)).toMatchObject({ unexpected: true, message: 'Das hat nicht geklappt. Bitte später erneut versuchen.' });
    expect(errorInfo(409, { code: 'brand_new', detail: 'x' }, null).unexpected).toBe(true);
    expect(errorInfo(502, null, null).unexpected).toBe(true);
    expect(errorInfo(418, null, null).unexpected).toBe(true);
    // bekannte Status mit allgemeinem Text statt englischem Servertext
    expect(describeDetail(404, 'Not Found')).toBe('Nicht gefunden.');
    expect(describeDetail(403, 'forbidden')).toBe('Dafür fehlt die Berechtigung.');
    // deutscher Text des Servers bleibt, auch bei 502 (z. B. Anmeldedienst nicht erreichbar)
    expect(errorInfo(502, { code: 'provider', message: 'Microsoft ist gerade nicht erreichbar.' }, null)).toMatchObject({ unexpected: false, message: 'Microsoft ist gerade nicht erreichbar.' });
    expect(describeDetail(422, 'Unbekannte Rolle: gott')).toBe('Unbekannte Rolle: gott');
    expect(describeDetail(409, { conflicts: ['Raum R1 belegt'] })).toBe('Konflikt: Raum R1 belegt');
  });

  it('Netzfehler bleibt „Server nicht erreichbar“ (kein Serverfehler)', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))));
    const e = (await http.get('/x').catch((x: unknown) => x)) as ApiError;
    expect(e.status).toBe(0);
    expect(e.unexpected).toBe(false);
    expect(e.message).toMatch(/Server nicht erreichbar/);
  });

  it('looksTechnical erkennt Codes und Englisch, nicht deutsche Sätze', () => {
    for (const t of ['not_authenticated', 'Not Found', 'Field required', 'Method Not Allowed', 'forbidden', 'Internal Server Error', 'body.date_from: invalid']) {
      expect(looksTechnical(t), t).toBe(true);
    }
    for (const t of ['Keine Berechtigung für diese Aktion', 'Nicht gefunden', 'Unbekannte Rolle: gott', 'Raum R1 ist belegt', 'Der Server ist nicht erreichbar.', 'Ungültiges Datum für date: morgen']) {
      expect(looksTechnical(t), t).toBe(false);
    }
  });
});

describe('Bekannte Codes und Berechtigungs-Texte (U-75)', () => {
  it('not_authenticated und invalid_token haben deutsche Texte', () => {
    expect(KNOWN_DETAILS.not_authenticated).toBeTruthy();
    expect(KNOWN_DETAILS.invalid_token).toBeTruthy();
    expect(describeDetail(401, 'not_authenticated')).toBe('Bitte erneut anmelden.');
    expect(describeDetail(401, 'invalid_token')).toMatch(/erneut anmelden/);
  });

  it('jeder String-Code des Backends steht in KNOWN_DETAILS', () => {
    // Liste aus `grep -rn 'HTTPException(4.., "<code>"' schulmanager/server` (11.10.2026)
    for (const code of ['not_authenticated', 'invalid_token', 'csrf_failed', 'password_change_required', 'totp_setup_required', 'link_required', 'totp_required', 'invalid_totp', 'too_many_attempts', 'method_not_allowed']) {
      expect(KNOWN_DETAILS[code], code).toBeTruthy();
    }
  });

  it('Toast bei 403 ohne doppeltes „Keine Berechtigung“', () => {
    const a = new ApiError(403, describeDetail(403, 'Keine Berechtigung für diese Aktion'), 'Keine Berechtigung für diese Aktion');
    expect(toastErrorContent(a).title).toBe('Keine Berechtigung für diese Aktion');
    const b = new ApiError(403, describeDetail(403, 'forbidden'), 'forbidden');
    expect(toastErrorContent(b).title).toBe('Dafür fehlt die Berechtigung.');
    const c = new ApiError(403, 'Nur für die eigene Klasse.', 'Nur für die eigene Klasse.');
    expect(toastErrorContent(c).title).toBe('Keine Berechtigung: Nur für die eigene Klasse.');
  });
});
