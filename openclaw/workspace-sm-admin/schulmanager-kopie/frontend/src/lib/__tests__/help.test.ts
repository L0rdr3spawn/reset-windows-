import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  HELP_DELAY_MS,
  HELP_GRACE_MS,
  INITIAL_HELP,
  addTokens,
  createHelpController,
  getHelpInline,
  helpTransition,
  helpTriggerOptions,
  isHelpKey,
  isTypingTarget,
  openHelpFor,
  placeHelp,
  registerHelpKey,
  removeTokens,
  resetActiveHelp,
  setHelpInline,
  subscribeHelpInline,
  type HelpMode,
} from '../help';
import { bottomNavItems, bottomNavLabel, shouldRestoreMenuFocus } from '../layout';

function setup(opts: { button?: boolean } = {}) {
  const modes: HelpMode[] = [];
  const c = createHelpController((m) => modes.push(m), opts);
  return { c, modes, mode: () => c.state.mode };
}

describe('Hilfe: Hover-Timer (A-60, ~2 s)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    resetActiveHelp();
  });
  afterEach(() => vi.useRealTimers());

  it('öffnet erst nach 2 s Zeiger auf dem Namen', () => {
    const { c, mode } = setup();
    c.send({ type: 'pointerEnter', pointer: 'mouse' });
    expect(mode()).toBe('pending');
    vi.advanceTimersByTime(HELP_DELAY_MS - 1);
    expect(mode()).toBe('pending');
    vi.advanceTimersByTime(1);
    expect(mode()).toBe('hover');
    expect(HELP_DELAY_MS).toBe(2000);
  });

  it('Verlassen vor Ablauf bricht ab', () => {
    const { c, mode, modes } = setup();
    c.send({ type: 'pointerEnter', pointer: 'mouse' });
    vi.advanceTimersByTime(1500);
    c.send({ type: 'pointerLeave' });
    vi.advanceTimersByTime(5000);
    expect(mode()).toBe('closed');
    expect(modes).not.toContain('hover');
  });

  it('bleibt offen, solange der Zeiger auf der Hilfe steht, schließt nach Nachlaufzeit', () => {
    const { c, mode } = setup();
    c.send({ type: 'pointerEnter', pointer: 'mouse' });
    vi.advanceTimersByTime(HELP_DELAY_MS);
    c.send({ type: 'pointerLeave' });
    c.send({ type: 'popoverEnter' });
    vi.advanceTimersByTime(HELP_GRACE_MS * 3);
    expect(mode()).toBe('hover');
    c.send({ type: 'popoverLeave' });
    vi.advanceTimersByTime(HELP_GRACE_MS - 1);
    expect(mode()).toBe('hover');
    vi.advanceTimersByTime(1);
    expect(mode()).toBe('closed');
  });

  it('Mausklick auf die Beschriftung (Fokus ins Feld) bricht die Wartezeit ab', () => {
    const { c, mode } = setup();
    c.send({ type: 'pointerEnter', pointer: 'mouse' });
    c.send({ type: 'activate', pointer: 'mouse' });
    vi.advanceTimersByTime(HELP_DELAY_MS * 2);
    expect(mode()).toBe('closed');
  });

  it('Stift verhält sich wie die Maus', () => {
    const { c, mode } = setup();
    c.send({ type: 'pointerEnter', pointer: 'pen' });
    vi.advanceTimersByTime(HELP_DELAY_MS);
    expect(mode()).toBe('hover');
  });
});

describe('Hilfe: Rechtsklick', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    resetActiveHelp();
  });
  afterEach(() => vi.useRealTimers());

  it('öffnet sofort und angeheftet; Verlassen schließt nicht', () => {
    const { c, mode } = setup();
    c.send({ type: 'pointerEnter', pointer: 'mouse' });
    c.send({ type: 'contextMenu' });
    expect(mode()).toBe('pinned');
    c.send({ type: 'pointerLeave' });
    vi.advanceTimersByTime(10_000);
    expect(mode()).toBe('pinned');
  });

  it('Escape und Klick außerhalb schließen', () => {
    const { c, mode } = setup();
    c.send({ type: 'contextMenu' });
    c.send({ type: 'escape' });
    expect(mode()).toBe('closed');
    c.send({ type: 'contextMenu' });
    c.send({ type: 'outside' });
    expect(mode()).toBe('closed');
  });

  it('Rechtsklick während der Wartezeit: kein späterer Moduswechsel durch den Timer', () => {
    const { c, mode } = setup();
    c.send({ type: 'pointerEnter', pointer: 'mouse' });
    c.send({ type: 'contextMenu' });
    vi.advanceTimersByTime(HELP_DELAY_MS * 2);
    expect(mode()).toBe('pinned');
  });
});

describe('Hilfe: Touch', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    resetActiveHelp();
  });
  afterEach(() => vi.useRealTimers());

  it('Berührung startet keinen Hover-Timer', () => {
    const { c, mode } = setup();
    c.send({ type: 'pointerEnter', pointer: 'touch' });
    vi.advanceTimersByTime(HELP_DELAY_MS * 2);
    expect(mode()).toBe('closed');
  });

  it('Antippen des Namens öffnet, erneutes Antippen schließt', () => {
    const { c, mode } = setup();
    c.send({ type: 'activate', pointer: 'touch' });
    expect(mode()).toBe('pinned');
    c.send({ type: 'activate', pointer: 'touch' });
    expect(mode()).toBe('closed');
  });

  it('Antippen außerhalb schließt', () => {
    const { c, mode } = setup();
    c.send({ type: 'activate', pointer: 'touch' });
    c.send({ type: 'outside' });
    expect(mode()).toBe('closed');
  });
});

describe('Hilfe: Tastatur und Hilfe-Knopf', () => {
  beforeEach(() => resetActiveHelp());

  it('Taste schaltet angeheftet ↔ zu', () => {
    const { c, mode } = setup();
    c.send({ type: 'key' });
    expect(mode()).toBe('pinned');
    c.send({ type: 'key' });
    expect(mode()).toBe('closed');
  });

  it('Hilfe-Knopf: Mausklick schaltet um, Hover-Hilfe wird beim Klick angeheftet', () => {
    const { c, mode } = setup({ button: true });
    c.send({ type: 'activate', pointer: 'mouse' });
    expect(mode()).toBe('pinned');
    c.send({ type: 'activate', pointer: 'mouse' });
    expect(mode()).toBe('closed');
    const s = helpTransition({ ...INITIAL_HELP, mode: 'hover' }, { type: 'activate', pointer: 'mouse' }, { button: true });
    expect(s[0].mode).toBe('pinned');
    // Tastatur-Klick (ohne pointerdown)
    c.send({ type: 'activate', pointer: '' });
    expect(mode()).toBe('pinned');
  });

  it('F1 öffnet die Hilfe des Felds über aria-describedby', () => {
    expect(isHelpKey({ key: 'F1' })).toBe(true);
    expect(isHelpKey({ key: 'F1', ctrlKey: true })).toBe(false);
    expect(isHelpKey({ key: '?' }, true)).toBe(false);
    const { c, mode } = setup();
    const off = registerHelpKey('h1help', () => c.send({ type: 'key' }));
    expect(openHelpFor('x-hint h1help')).toBe(true);
    expect(mode()).toBe('pinned');
    expect(openHelpFor('unbekannt')).toBe(false);
    expect(openHelpFor(null)).toBe(false);
    off();
    expect(openHelpFor('h1help')).toBe(false);
  });
});

describe('Hilfe: Tastenwahl und Einstellung', () => {
  it('„?“ nur außerhalb von Texteingaben', () => {
    expect(isHelpKey({ key: '?' }, false)).toBe(true);
    expect(isHelpKey({ key: '?' }, true)).toBe(false);
    expect(isHelpKey({ key: 'F1' }, true)).toBe(true);
    expect(isTypingTarget({ tagName: 'INPUT', type: 'text' })).toBe(true);
    expect(isTypingTarget({ tagName: 'input', type: 'password' })).toBe(true);
    expect(isTypingTarget({ tagName: 'TEXTAREA' })).toBe(true);
    expect(isTypingTarget({ tagName: 'INPUT', type: 'checkbox' })).toBe(false);
    expect(isTypingTarget({ tagName: 'SELECT' })).toBe(false);
    expect(isTypingTarget({ tagName: 'DIV', isContentEditable: true })).toBe(true);
    expect(isTypingTarget(null)).toBe(false);
  });

  it('„Hilfetexte immer anzeigen“ meldet Änderungen (ohne localStorage in Node)', () => {
    const seen: boolean[] = [];
    const off = subscribeHelpInline(() => seen.push(getHelpInline()));
    expect(getHelpInline()).toBe(false);
    setHelpInline(true);
    setHelpInline(false);
    off();
    setHelpInline(true);
    expect(seen).toEqual([true, false]);
    setHelpInline(false);
  });
});

describe('Hilfe: höchstens eine offen', () => {
  beforeEach(() => resetActiveHelp());

  it('Öffnen einer zweiten Hilfe schließt die erste', () => {
    const a = setup();
    const b = setup();
    a.c.send({ type: 'contextMenu' });
    b.c.send({ type: 'activate', pointer: 'touch' });
    expect(a.mode()).toBe('closed');
    expect(b.mode()).toBe('pinned');
    a.c.dispose();
    b.c.dispose();
  });
});

describe('Hilfe: eigenständiger Name (HelpText außerhalb eines Labels, role="button")', () => {
  // Regression: der Name war als Knopf ausgezeichnet, ein Mausklick bzw. der Klick eines Bildschirmlesers (ohne
  // vorheriges pointerdown) tat aber nichts.
  it('Klick per Maus oder Bildschirmleser schaltet um', () => {
    const opts = helpTriggerOptions(false);
    expect(opts.button).toBe(true);
    for (const pointer of ['mouse', '']) {
      const [open] = helpTransition(INITIAL_HELP, { type: 'activate', pointer }, opts);
      expect(open.mode, pointer).toBe('pinned');
      const [closed] = helpTransition(open, { type: 'activate', pointer }, opts);
      expect(closed.mode, pointer).toBe('closed');
    }
  });

  it('im Label mit Feld bleibt der Mausklick beim Feld', () => {
    const opts = helpTriggerOptions(true);
    expect(opts.button).toBe(false);
    expect(helpTransition(INITIAL_HELP, { type: 'activate', pointer: 'mouse' }, opts)[0].mode).toBe('closed');
    expect(helpTransition(INITIAL_HELP, { type: 'activate', pointer: 'touch' }, opts)[0].mode).toBe('pinned');
  });
});

describe('Hilfe: Hilfsfunktionen', () => {
  it('aria-describedby-Listen ohne Doppelte, bestehende Einträge bleiben', () => {
    expect(addTokens('a b', ['b', 'c'])).toBe('a b c');
    expect(addTokens(null, ['x'])).toBe('x');
    expect(removeTokens('a b c', ['b'])).toBe('a c');
    expect(removeTokens(null, ['b'])).toBe('');
  });

  it('Popover unter dem Namen, sonst darüber, immer im sichtbaren Bereich (390 px)', () => {
    const view = { width: 390, height: 844 };
    const pop = { width: 300, height: 80 };
    expect(placeHelp({ left: 20, top: 100, bottom: 120 }, pop, view)).toEqual({ left: 20, top: 126, above: false });
    // rechter Rand: nach links geschoben
    expect(placeHelp({ left: 300, top: 100, bottom: 120 }, pop, view).left).toBe(390 - 300 - 8);
    // unterer Rand: darüber
    const up = placeHelp({ left: 20, top: 800, bottom: 820 }, pop, view);
    expect(up.above).toBe(true);
    expect(up.top).toBe(800 - 6 - 80);
  });
});

describe('Untere Leiste am Handy', () => {
  const nav = (paths: string[]) => paths.map((path) => ({ path, label: path === '/vertretung' ? 'Vertretungsplan' : path }));

  it('bevorzugt Start, Stundenplan, Vertretung, Postfach; höchstens 4', () => {
    const items = nav(['/', '/stundenplan', '/vertretung', '/klausuren', '/nachrichten', '/profil']);
    expect(bottomNavItems(items).map((i) => i.path)).toEqual(['/', '/stundenplan', '/vertretung', '/nachrichten']);
  });

  it('füllt mit weiteren Einträgen auf, Profil nie', () => {
    expect(bottomNavItems(nav(['/monitor', '/profil'])).map((i) => i.path)).toEqual(['/monitor']);
    expect(bottomNavItems(nav(['/', '/klausuren', '/profil'])).map((i) => i.path)).toEqual(['/', '/klausuren']);
  });

  it('kurze Beschriftungen', () => {
    expect(bottomNavLabel({ path: '/vertretung', label: 'Vertretungsplan' })).toBe('Vertretung');
    expect(bottomNavLabel({ path: '/stundenplan', label: 'Stundenplan' })).toBe('Stundenplan');
  });
});

describe('Ausgeklapptes Menü: Fokus beim Schließen', () => {
  // Regression: der Fokus blieb beim Öffnen hinter dem Hintergrund und ging beim Schließen in der verborgenen Leiste verloren
  const body = { id: 'body' };
  const inSide = { id: 'link' };
  const main = { id: 'main' };
  const sidebar = { contains: (n: { id: string }) => n === inSide };

  it('zurück zum Auslöser, wenn der Fokus in der Seitenleiste lag oder verloren ging', () => {
    expect(shouldRestoreMenuFocus(inSide, sidebar, body)).toBe(true);
    expect(shouldRestoreMenuFocus(body, sidebar, body)).toBe(true);
    expect(shouldRestoreMenuFocus(null, sidebar, body)).toBe(true);
  });

  it('nach Seitenwechsel bleibt der Fokus im Inhalt', () => {
    expect(shouldRestoreMenuFocus(main, sidebar, body)).toBe(false);
  });
});
