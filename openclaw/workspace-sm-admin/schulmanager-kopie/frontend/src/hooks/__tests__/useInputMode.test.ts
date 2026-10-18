import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { FINE_POINTER_QUERY, inputModeFor, useInputMode } from '../useInputMode';

function Probe() {
  const m = useInputMode();
  return createElement('span', null, `${m.mode}|${m.fine}|${m.touch}`);
}

function render(fine: boolean): string {
  vi.stubGlobal('window', {
    matchMedia: (q: string) => ({ matches: q === FINE_POINTER_QUERY ? fine : false, addEventListener() {}, removeEventListener() {} }),
  });
  return renderToString(createElement(Probe)).replace(/<[^>]+>/g, '');
}

describe('useInputMode', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('inputModeFor', () => {
    expect(inputModeFor(true)).toBe('fine');
    expect(inputModeFor(false)).toBe('touch');
  });
  it('Maus/Touchpad → fine', () => expect(render(true)).toBe('fine|true|false'));
  it('Handy/Tablet → touch', () => expect(render(false)).toBe('touch|false|true'));
  it('ohne matchMedia → touch', () => {
    vi.stubGlobal('window', {});
    expect(renderToString(createElement(Probe)).replace(/<[^>]+>/g, '')).toBe('touch|false|true');
  });
});
