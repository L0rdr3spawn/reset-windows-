import { describe, expect, it } from 'vitest';
import { entryText } from './supportApi';

describe('entryText', () => {
  it('zeigt Art, Minuten, Hilfsmittel und Fächer', () => {
    expect(entryText({ label: 'Zeitzuschlag', minutes: 15, aids: '' }, ['Deutsch'])).toBe('Zeitzuschlag +15 Min. (Deutsch)');
    expect(entryText({ label: 'Wörterbuch/Duden erlaubt', minutes: null, aids: 'Duden' })).toBe('Wörterbuch/Duden erlaubt: Duden');
  });
});
