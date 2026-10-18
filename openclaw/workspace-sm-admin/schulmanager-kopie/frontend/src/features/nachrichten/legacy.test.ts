import { describe, expect, it } from 'vitest';
import { legacyTarget } from './legacy';

describe('alte Adressen → /nachrichten', () => {
  it('Liste, Ordner und Filter', () => {
    expect(legacyTarget('/postfach')).toBe('/nachrichten');
    expect(legacyTarget('/postfach/', '?ordner=archiv')).toBe('/nachrichten?f=archiv');
    expect(legacyTarget('/postfach', '?ordner=mitteilungen')).toBe('/nachrichten?f=mitteilungen');
    expect(legacyTarget('/chats')).toBe('/nachrichten?f=chats');
    expect(legacyTarget('/chats', '?link=ABC')).toBe('/nachrichten?link=ABC&f=chats');
    expect(legacyTarget('/mitteilungen')).toBe('/nachrichten?f=mitteilungen');
  });
  it('Unterhaltungen', () => {
    expect(legacyTarget('/postfach/12')).toBe('/nachrichten/b/12');
    expect(legacyTarget('/chats/7')).toBe('/nachrichten/c/7');
    expect(legacyTarget('/postfach/abc')).toBe('/nachrichten');
  });
  it('Verfassen behält die Vorbelegung (Klassenraum „Nachricht schreiben“)', () => {
    expect(legacyTarget('/postfach/neu', '?lehrkraft=A%26B')).toBe('/nachrichten/neu?lehrkraft=A%26B');
    expect(legacyTarget('/postfach/einstellungen')).toBe('/nachrichten/einstellungen');
  });
  it('Moderation', () => {
    expect(legacyTarget('/postfach/moderation')).toBe('/nachrichten/moderation');
    expect(legacyTarget('/chats/moderation')).toBe('/nachrichten/moderation/chats');
  });
  it('fremde Adressen bleiben unberührt', () => {
    expect(legacyTarget('/stundenplan')).toBeNull();
  });
});
