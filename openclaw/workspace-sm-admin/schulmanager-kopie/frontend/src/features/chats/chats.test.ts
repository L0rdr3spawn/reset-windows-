import nacl from 'tweetnacl';
import { describe, expect, it } from 'vitest';
import { insertAt, isEmojiOnly, truncateText } from '../../lib/emoji';
import { searchEmoji } from '../../lib/emojiData';
import { decryptImage, encryptImage, fromB64, open, seal, sniffImageType, toB64, type LocalDevice } from './crypto';

function device(id: number): LocalDevice {
  const kp = nacl.box.keyPair();
  return { userId: id, deviceId: id, publicKey: toB64(kp.publicKey), secretKey: toB64(kp.secretKey) };
}

describe('Emoji', () => {
  it('erkennt Nachrichten, die nur aus Emoji bestehen', () => {
    expect(isEmojiOnly('😀')).toBe(true);
    expect(isEmojiOnly('👍🏽 🇩🇪 👨‍👩‍👧')).toBe(true);
    expect(isEmojiOnly('❤️')).toBe(true);
    expect(isEmojiOnly('Hallo 😀')).toBe(false);
    expect(isEmojiOnly('123')).toBe(false);
    expect(isEmojiOnly('')).toBe(false);
    expect(isEmojiOnly('😀😀😀😀😀😀😀')).toBe(false);
  });

  it('kürzt, ohne Emoji zu zerreißen', () => {
    const text = '😀'.repeat(10);
    expect(truncateText(text, 4)).toBe('😀😀😀😀…');
    expect(truncateText('👨‍👩‍👧x', 1)).toBe('👨‍👩‍👧…');
    expect(truncateText('kurz', 10)).toBe('kurz');
  });

  it('fügt an der Cursorposition ein und respektiert das Limit', () => {
    expect(insertAt('Hallo Welt', 5, 5, '😀')).toEqual({ value: 'Hallo😀 Welt', caret: 7 });
    expect(insertAt('abc', 1, 3, '😀')).toEqual({ value: 'a😀', caret: 3 });
    expect(insertAt('abc', null, null, '😀').value).toBe('abc😀');
    expect(insertAt('abc', 1, 1, '😀', 4)).toEqual({ value: 'abc', caret: 1 });
  });

  it('sucht nach deutschen Stichwörtern', () => {
    expect(searchEmoji('herz').some((x) => x.e === '❤️')).toBe(true);
    expect(searchEmoji('lach').length).toBeGreaterThan(3);
    expect(searchEmoji('   ')).toEqual([]);
    expect(searchEmoji('xyzxyz')).toEqual([]);
  });
});

describe('Chat-Verschlüsselung mit Emoji und Bildern', () => {
  it('Emoji und Bild-Verweise überstehen Ver- und Entschlüsselung', () => {
    const a = device(1);
    const b = device(2);
    const img = { id: 'a'.repeat(32), key: 'k', nonce: 'n', mime: 'image/gif', name: 'x.gif', size: 3 };
    const sealed = seal({ v: 1, text: 'Hi 👋🏽 👨‍👩‍👧 🇩🇪', images: [img] }, [{ device_id: 2, user_id: 2, public_key: b.publicKey }], a);
    const k = sealed.keys[0];
    const got = open({ nonce: sealed.nonce, ciphertext: sealed.ciphertext, sender_key: a.publicKey, key: { nonce: k.nonce, wrapped: k.wrapped } }, b);
    expect(got?.text).toBe('Hi 👋🏽 👨‍👩‍👧 🇩🇪');
    expect(got?.images).toEqual([img]);
  });

  it('verwirft unzulässige Bildtypen im Verweis (z. B. SVG)', () => {
    const a = device(1);
    const b = device(2);
    const bad = { id: 'z', key: 'k', nonce: 'n', mime: 'image/svg+xml', name: 'x.svg', size: 1 };
    const sealed = seal({ v: 1, text: 'x', images: [bad] }, [{ device_id: 2, user_id: 2, public_key: b.publicKey }], a);
    const k = sealed.keys[0];
    const got = open({ nonce: sealed.nonce, ciphertext: sealed.ciphertext, sender_key: a.publicKey, key: { nonce: k.nonce, wrapped: k.wrapped } }, b);
    expect(got?.images).toBeUndefined();
  });

  it('Bild-Blob ist ohne Schlüssel unlesbar und manipulationssicher', () => {
    const bytes = new Uint8Array([0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 1, 2, 3, 4]);
    const enc = encryptImage(bytes);
    expect(enc.blob.length).toBe(bytes.length + 16);
    expect(Array.from(enc.blob.slice(0, 6))).not.toEqual(Array.from(bytes.slice(0, 6)));
    expect(decryptImage(enc.blob, enc)).toEqual(bytes);
    const other = encryptImage(bytes);
    expect(decryptImage(enc.blob, { key: other.key, nonce: enc.nonce })).toBeNull();
    const tampered = new Uint8Array(enc.blob);
    tampered[3] ^= 1;
    expect(decryptImage(tampered, enc)).toBeNull();
    expect(fromB64(enc.key).length).toBe(32);
  });

  it('erkennt Bildtypen am Inhalt', () => {
    expect(sniffImageType(new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))).toBe('image/png');
    expect(sniffImageType(new Uint8Array([0xff, 0xd8, 0xff, 0xe0]))).toBe('image/jpeg');
    expect(sniffImageType(new TextEncoder().encode('GIF89a....'))).toBe('image/gif');
    expect(sniffImageType(new TextEncoder().encode('RIFF....WEBPVP8 '))).toBe('image/webp');
    expect(sniffImageType(new TextEncoder().encode('<svg xmlns="http://www.w3.org/2000/svg"/>'))).toBeNull();
    expect(sniffImageType(new Uint8Array())).toBeNull();
  });
});
