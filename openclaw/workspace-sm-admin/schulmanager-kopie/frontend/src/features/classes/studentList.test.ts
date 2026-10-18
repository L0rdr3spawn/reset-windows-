import { describe, expect, it } from 'vitest';
import { ageOn, checkRows, fixCase, gradeFromName, hasEmails, isAdult, parseDate, parseStudentList, splitName, toApiStudents } from './studentList';

const pick = (text: string) => parseStudentList(text).rows.map((r) => [r.first_name, r.last_name]);

describe('parseStudentList', () => {
  it('Excel-Tabelle mit Kopfzeile, E-Mail, Geburtsdatum und Eltern', () => {
    const text = [
      'Nr\tNachname\tVorname\tE-Mail\tGeburtsdatum\tElternteil 1\tE-Mail Elternteil 1\tElternteil 2\tE-Mail Elternteil 2',
      '1\tMüller\tJürgen\tjuergen@example.org\t03.04.2014\tAnna Müller\tanna@example.org\t\t',
      '',
      '2\tÖzdemir\tAyşe\t\t2008-01-31\t\t\tMehmet Özdemir\tmehmet@example.org',
    ].join('\n');
    const res = parseStudentList(text);
    expect(res.header).toBe(true);
    expect(res.format).toBe('tabelle');
    expect(res.columns).toContain('Geburtsdatum');
    expect(res.rows).toHaveLength(2);
    const [a, b] = res.rows;
    expect(a).toMatchObject({ first_name: 'Jürgen', last_name: 'Müller', email: 'juergen@example.org', birth_date: '2014-04-03', line: 2 });
    expect(a?.parents).toEqual([{ name: 'Anna Müller', email: 'anna@example.org' }]);
    expect(b).toMatchObject({ first_name: 'Ayşe', last_name: 'Özdemir', birth_date: '2008-01-31', line: 4 });
    expect(b?.parents).toEqual([{ name: 'Mehmet Özdemir', email: 'mehmet@example.org' }]);
  });

  it('Tabelle ohne Kopfzeile: Nachname, Vorname; laufende Nummer, E-Mail und „ja“ erkannt', () => {
    const res = parseStudentList('1\tSchmidt\tAnna-Lena\tanna@example.org\tja\n2\tvon der Heide\tMax\t\tnein');
    expect(res.header).toBe(false);
    expect(res.rows.map((r) => [r.first_name, r.last_name, r.email, r.adult])).toEqual([
      ['Anna-Lena', 'Schmidt', 'anna@example.org', true],
      ['Max', 'von der Heide', '', false],
    ]);
  });

  it('CSV mit Semikolon und Anführungszeichen', () => {
    const res = parseStudentList('"Name";"Vorname";"Klasse"\n"Weiß";"Lea";"5a"\n"Groß";"Tim";"5a"');
    expect(res.header).toBe(true);
    expect(pick('"Name";"Vorname";"Klasse"\n"Weiß";"Lea";"5a"')).toEqual([['Lea', 'Weiß']]);
    expect(res.rows).toHaveLength(2);
  });

  it('„Nachname, Vorname“ je Zeile', () => {
    expect(pick('Mustermann, Max\nMüller-Lüdenscheidt, Anna Maria\n\n  Becker ,  Ben  ')).toEqual([
      ['Max', 'Mustermann'],
      ['Anna Maria', 'Müller-Lüdenscheidt'],
      ['Ben', 'Becker'],
    ]);
  });

  it('„Vorname Nachname“ mit Aufzählung, Namenszusatz, E-Mail und Datum', () => {
    const res = parseStudentList('1. Max Mustermann\n2) Lisa von der Heide lisa@example.org 1.2.2012\n- Ömer Yılmaz');
    expect(res.format).toBe('text');
    expect(res.rows.map((r) => [r.first_name, r.last_name])).toEqual([
      ['Max', 'Mustermann'],
      ['Lisa', 'von der Heide'],
      ['Ömer', 'Yılmaz'],
    ]);
    expect(res.rows[1]).toMatchObject({ email: 'lisa@example.org', birth_date: '2012-02-01' });
  });

  it('Großbuchstaben werden normalisiert, Doppelnamen bleiben erhalten', () => {
    expect(pick('MÜLLER-LÜDENSCHEIDT, JÜRGEN')).toEqual([['Jürgen', 'Müller-Lüdenscheidt']]);
    expect(fixCase('VON DER HEIDE')).toBe('von der Heide');
    expect(fixCase('McDonald')).toBe('McDonald');
  });

  it('leere Eingabe und Leerzeilen', () => {
    expect(parseStudentList('  \n\n').format).toBe('leer');
    expect(parseStudentList('﻿Anna Schmidt\r\n\r\nBen Becker\r\n').rows).toHaveLength(2);
  });
});

describe('Hilfen', () => {
  it('splitName', () => {
    expect(splitName('Anna Lena Schmidt')).toEqual(['Anna Lena', 'Schmidt']);
    expect(splitName('Schmidt')).toEqual(['', 'Schmidt']);
  });

  it('parseDate und Alter', () => {
    const today = new Date(2026, 9, 10);
    expect(parseDate('31.12.2008')).toBe('2008-12-31');
    expect(parseDate('1.2.12', today)).toBe('2012-02-01');
    expect(parseDate('31.02.2010')).toBe('');
    expect(ageOn('2008-10-10', today)).toBe(18);
    expect(ageOn('2008-10-11', today)).toBe(17);
    expect(isAdult({ birth_date: '2008-10-11', adult: true }, today)).toBe(false);
    expect(isAdult({ birth_date: '', adult: true }, today)).toBe(true);
  });

  it('checkRows: Fehler, Duplikate, vorhandene Namen', () => {
    const rows = parseStudentList('Max Mustermann\nmax mustermann\nNur\nAnna Schmidt kaputt@').rows;
    const checks = checkRows(rows, ['Anna Schmidt']);
    expect(checks[0]?.warnings).toContain('Name doppelt in der Liste');
    expect(checks[1]?.warnings).toContain('Name doppelt in der Liste');
    expect(checks[2]?.errors).toContain('Vorname fehlt');
    expect(checks[3]?.errors).toContain('E-Mail-Adresse ungültig');
    expect(checks[3]?.warnings).toContain('Name gibt es schon');
  });

  it('toApiStudents und hasEmails', () => {
    const rows = parseStudentList('Nachname\tVorname\tE-Mail Eltern\nMuster\tMax\teltern@example.org').rows;
    expect(toApiStudents(rows)).toEqual([
      { first_name: 'Max', last_name: 'Muster', email: null, birth_date: null, adult: false, parents: [{ name: '', email: 'eltern@example.org' }] },
    ]);
    expect(hasEmails(rows)).toEqual({ students: 0, parents: 1 });
  });

  it('gradeFromName', () => {
    expect(gradeFromName('7b')).toBe(7);
    expect(gradeFromName('Q1-2')).toBe(11);
    expect(gradeFromName('EF')).toBe(10);
    expect(gradeFromName('Abend')).toBeNull();
  });
});
