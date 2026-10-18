/**
 * Bilder & GIFs in Chats: auswählen/einfügen/ziehen (`readImageFile`), im Browser verschlüsseln (siehe `crypto.ts`)
 * und in Nachrichten anzeigen (`ChatImage`: lädt das verschlüsselte Blob, entschlüsselt es lokal, zeigt es per
 * Blob-URL – animierte GIFs bleiben animiert). Der Server sieht nie ein Bild im Klartext.
 */
import { useEffect, useState } from 'react';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { chatsApi } from './api';
import { decryptImage, MAX_IMAGE_BYTES, sniffImageType, toB64, type ImageRef } from './crypto';

export interface PendingImage {
  key: string;
  name: string;
  mime: string;
  bytes: Uint8Array;
  previewUrl: string;
}

export class ImageError extends Error {}

const MAX_SIDE = 2048;

/** Große Fotos (nicht GIF) verkleinern, damit sie unter das Limit passen. */
async function shrink(file: Blob, mime: string): Promise<Uint8Array | null> {
  if (mime === 'image/gif' || typeof createImageBitmap !== 'function' || typeof document === 'undefined') return null;
  try {
    const bmp = await createImageBitmap(file);
    const scale = Math.min(1, MAX_SIDE / Math.max(bmp.width, bmp.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(bmp.width * scale));
    canvas.height = Math.max(1, Math.round(bmp.height * scale));
    canvas.getContext('2d')?.drawImage(bmp, 0, 0, canvas.width, canvas.height);
    const out = await new Promise<Blob | null>((res) => canvas.toBlob(res, 'image/jpeg', 0.85));
    return out ? new Uint8Array(await out.arrayBuffer()) : null;
  } catch {
    return null;
  }
}

/** Liest eine Datei als sendefertiges Bild: Typ aus dem Inhalt, Größe ≤ 5 MB (große Fotos werden verkleinert). */
export async function readImageFile(file: File): Promise<PendingImage> {
  let bytes: Uint8Array = new Uint8Array(await file.arrayBuffer());
  let mime = sniffImageType(bytes);
  if (!mime) throw new ImageError(`„${file.name || 'Datei'}“ ist kein Bild (erlaubt: PNG, JPEG, GIF, WebP).`);
  if (bytes.length > MAX_IMAGE_BYTES) {
    const small = await shrink(file, mime);
    if (!small || small.length > MAX_IMAGE_BYTES) {
      throw new ImageError(`„${file.name || 'Bild'}“ ist zu groß (höchstens 5 MB${mime === 'image/gif' ? '; GIFs werden nicht verkleinert' : ''}).`);
    }
    bytes = small;
    mime = 'image/jpeg';
  }
  const ext = mime === 'image/jpeg' ? 'jpg' : mime.slice(6);
  const name = (file.name || `bild.${ext}`).replace(/\.[^.]+$/, '') + `.${ext}`;
  const previewUrl = URL.createObjectURL(new Blob([bytes as BlobPart], { type: mime }));
  return { key: `${Date.now()}-${Math.random().toString(36).slice(2)}`, name, mime, bytes, previewUrl };
}

/** Bilddateien aus Zwischenablage/Ziehen&Ablegen. */
export function imageFiles(list: FileList | DataTransferItemList | null | undefined): File[] {
  if (!list) return [];
  const out: File[] = [];
  for (let i = 0; i < list.length; i++) {
    const it = list[i];
    const f = 'getAsFile' in it ? (it.kind === 'file' ? it.getAsFile() : null) : it;
    if (f && (f.type.startsWith('image/') || !f.type)) out.push(f);
  }
  return out;
}

/** Entschlüsseltes Bild als Bytes (z. B. zum Mitschicken an die Moderation). */
export async function fetchImageBytes(chatId: number, ref: ImageRef): Promise<Uint8Array | null> {
  const blob = await chatsApi.image(chatId, ref.id);
  return decryptImage(blob, ref);
}

export async function fetchImageBase64(chatId: number, ref: ImageRef): Promise<string | null> {
  const bytes = await fetchImageBytes(chatId, ref);
  return bytes ? toB64(bytes) : null;
}

/** Vorschau-Leiste der noch nicht gesendeten Bilder. */
export function PendingImages({ images, onRemove }: { images: PendingImage[]; onRemove: (key: string) => void }) {
  if (!images.length) return null;
  return (
    <ul className="ch-pending" aria-label="Angehängte Bilder">
      {images.map((p) => (
        <li key={p.key}>
          <img src={p.previewUrl} alt={p.name} />
          <button type="button" className="btn btn-icon btn-sm ch-pending-x" aria-label={`${p.name} entfernen`} onClick={() => onRemove(p.key)}>
            <Icon name="x" />
          </button>
        </li>
      ))}
    </ul>
  );
}

/** Ein Bild einer Nachricht: laden → lokal entschlüsseln → anzeigen (Klick = groß). */
export function ChatImage({ chatId, image, small = false }: { chatId: number; image: ImageRef; small?: boolean }) {
  const [url, setUrl] = useState<string | null>(null);
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading');
  const [big, setBig] = useState(false);

  useEffect(() => {
    let alive = true;
    let made: string | null = null;
    setState('loading');
    chatsApi
      .image(chatId, image.id)
      .then((blob) => {
        const plain = decryptImage(blob, image);
        if (!alive) return;
        if (!plain || sniffImageType(plain) !== image.mime) {
          setState('error');
          return;
        }
        made = URL.createObjectURL(new Blob([plain as BlobPart], { type: image.mime }));
        setUrl(made);
        setState('ok');
      })
      .catch(() => alive && setState('error'));
    return () => {
      alive = false;
      if (made) URL.revokeObjectURL(made);
    };
  }, [chatId, image]);

  if (state === 'error') return <p className="small muted ch-img-fail">Bild nicht verfügbar (gelöscht oder nicht lesbar).</p>;
  if (state === 'loading' || !url) return <div className="ch-img-wait muted small">Bild wird geladen …</div>;
  return (
    <>
      <button type="button" className="ch-img-btn" onClick={() => setBig(true)} aria-label={`Bild ${image.name || ''} vergrößern`}>
        <img className={`msg-img${small ? ' msg-img-small' : ''}`} src={url} alt={image.name || 'Bild'} />
      </button>
      {big && (
        <Modal title={image.name || 'Bild'} onClose={() => setBig(false)} size="lg">
          <img className="ch-img-big" src={url} alt={image.name || 'Bild'} />
        </Modal>
      )}
    </>
  );
}
