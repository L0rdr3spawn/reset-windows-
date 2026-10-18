import { describe, expect, it } from 'vitest';
import { suggestSubjectCode } from '../subjectCode';

describe('suggestSubjectCode', () => {
  it('nimmt die ersten Buchstaben', () => {
    expect(suggestSubjectCode('Informatik', [])).toBe('INF');
    expect(suggestSubjectCode('Ökologie', [])).toBe('OEK');
  });
  it('mehrere Wörter: Anfangsbuchstaben', () => {
    expect(suggestSubjectCode('Darstellendes Spiel', [])).toBe('DS');
  });
  it('vergebene Kürzel bekommen eine Ziffer', () => {
    expect(suggestSubjectCode('Informatik', ['inf'])).toBe('INF2');
    expect(suggestSubjectCode('Informatik', ['INF', 'INF2'])).toBe('INF3');
  });
  it('leerer Name', () => {
    expect(suggestSubjectCode('  ', [])).toBe('');
  });
});
