import nacl from 'tweetnacl';
import { describe, expect, it } from 'vitest';
import { fingerprint, fromB64, open, rewrapKey, seal, toB64, type LocalDevice, type MemberDevice } from './crypto';
import { canonicalSecret, detectKeyChanges, formatLinkCode, generateRecoveryCode, linkUrl, openBackup, parseLinkCode, passwordProblem, sealBackup } from './keys';

function device(id: number): LocalDevice {
  const kp = nacl.box.keyPair();
  return { userId: id, deviceId: id, publicKey: toB64(kp.publicKey), secretKey: toB64(kp.secretKey) };
}
const member = (d: LocalDevice, kind: 'device' | 'archive' = 'device'): MemberDevice => ({ device_id: d.deviceId, user_id: Number(d.userId), public_key: d.publicKey, kind });

describe('Verlauf übertragen', () => {
  it('neues Gerät liest eine Nachricht nach dem Neuverpacken durch das alte Gerät', () => {
    const sender = device(1);
    const oldDev = device(2);
    const newDev = device(3);
    const sealed = seal({ v: 1, text: 'Hallo Kevin' }, [member(oldDev)], sender);
    const k = sealed.keys[0];
    const base = { nonce: sealed.nonce, ciphertext: sealed.ciphertext, sender_key: sender.publicKey };
    expect(open({ ...base, key: null }, newDev)).toBeNull();
    // Server liefert dem alten Gerät den Schlüssel samt Absenderschlüssel
    const w = rewrapKey({ wrapper_key: sender.publicKey, nonce: k.nonce, wrapped: k.wrapped }, fromB64(oldDev.secretKey), newDev.publicKey);
    expect(w).not.toBeNull();
    // nur mit dem Verpackerschlüssel lesbar
    expect(open({ ...base, key: { ...w!, wrapper_key: oldDev.publicKey } }, newDev)?.text).toBe('Hallo Kevin');
    expect(open({ ...base, key: { ...w! } }, newDev)).toBeNull();
    // ein fremdes Gerät kann weder öffnen noch neu verpacken
    expect(open({ ...base, key: { ...w!, wrapper_key: oldDev.publicKey } }, device(9))).toBeNull();
    expect(rewrapKey({ wrapper_key: sender.publicKey, nonce: k.nonce, wrapped: k.wrapped }, fromB64(device(9).secretKey), newDev.publicKey)).toBeNull();
  });

  it('Code und Link', () => {
    expect(formatLinkCode('abcd2345')).toBe('ABCD-2345');
    expect(parseLinkCode('abcd-2345')).toBe('ABCD2345');
    expect(parseLinkCode(linkUrl('ABCD2345', 'https://s.example'))).toBe('ABCD2345');
  });
});

describe('Backup mit Passwort', () => {
  it('Archivschlüssel lässt sich nur mit dem richtigen Code öffnen', async () => {
    const archive = nacl.box.keyPair();
    const code = generateRecoveryCode();
    expect(code).toMatch(/^([A-Z2-9]{5}-){4}[A-Z2-9]{5}$/);
    const blob = await sealBackup(archive.secretKey, code, 100_000);
    expect(blob).not.toContain(toB64(archive.secretKey));
    expect(await openBackup(blob, code)).toEqual(archive.secretKey);
    // Tippvarianten des Codes sind egal
    expect(await openBackup(blob, code.toLowerCase().replace(/-/g, ' '))).toEqual(archive.secretKey);
    expect(await openBackup(blob, 'falsch-falsch-falsch')).toBeNull();
    expect(await openBackup('kaputt', code)).toBeNull();
    // manipuliert
    const b = JSON.parse(blob) as { box: string };
    b.box = toB64(nacl.randomBytes(48));
    expect(await openBackup(JSON.stringify(b), code)).toBeNull();
  });

  it('zu wenige Runden im Blob werden abgelehnt', async () => {
    const blob = JSON.parse(await sealBackup(nacl.randomBytes(32), 'x'.repeat(12), 100_000)) as { iter: number };
    blob.iter = 10;
    expect(await openBackup(JSON.stringify(blob), 'x'.repeat(12))).toBeNull();
  });

  it('Passwortregeln', () => {
    expect(passwordProblem('kurz')).toMatch(/Mindestens/);
    expect(passwordProblem('aaaaaaaaaaaaaaaa')).toMatch(/einfach/);
    expect(passwordProblem('Ein ganzer Satz ist gut')).toBeNull();
    expect(passwordProblem(generateRecoveryCode())).toBeNull();
    expect(canonicalSecret('Mein Satz')).toBe('Mein Satz');
  });
});

describe('Schlüsselwechsel', () => {
  it('meldet ersetzte und zusätzliche Schlüssel, nicht den ersten Kontakt', () => {
    const kevin = device(2);
    const first = detectKeyChanges({}, [member(kevin)], 1);
    expect(first.changes).toEqual([]);
    const seen = first.next;
    expect(detectKeyChanges(seen, [member(kevin)], 1).changes).toEqual([]);
    const kevin2 = { ...device(2), deviceId: 5 };
    const replaced = detectKeyChanges(seen, [member(kevin2)], 1);
    expect(replaced.changes).toEqual([{ userId: 2, kind: 'changed', fingerprints: [fingerprint(kevin2.publicKey)] }]);
    const extra = detectKeyChanges(seen, [member(kevin), member(kevin2)], 1);
    expect(extra.changes[0].kind).toBe('added');
    // Archiv-Schlüssel und eigene Geräte zählen nicht
    expect(detectKeyChanges(seen, [member(kevin), member(device(2), 'archive'), member(device(1))], 1).changes).toEqual([]);
    // entfernte Geräte allein sind keine Warnung
    expect(detectKeyChanges({ '2': [fingerprint(kevin.publicKey), 'AAAA'] }, [member(kevin)], 1).changes).toEqual([]);
  });
});
