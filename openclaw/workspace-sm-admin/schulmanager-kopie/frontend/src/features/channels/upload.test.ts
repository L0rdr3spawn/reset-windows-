import { describe, expect, it } from 'vitest';
import { collectDropped, confirmAbortUploads, usableFiles } from './MaterialUpload';
import { canEdit, dirOf, draftToInput, folderPaths, folderVisibilityText, nextHeldLesson, shiftText, visibilityText } from './logic';
import { settleDialog, subscribeDialogs } from '../../lib/confirm';

describe('Ordner-Upload (A-45)', () => {
  it('Ordnerpfad aus webkitRelativePath', () => {
    expect(dirOf('Projekt/Bilder/a.png')).toBe('Projekt/Bilder');
    expect(dirOf('a.png')).toBe('');
    expect(dirOf('Projekt\\Texte\\b.txt')).toBe('Projekt/Texte');
    expect(dirOf('../x/./a.png')).toBe('x');
  });
  it('alle Ordnerpfade inkl. übergeordneter, flach zuerst', () => {
    expect(folderPaths([{ dir: 'Projekt/Bilder/Alt' }, { dir: '' }, { dir: 'Projekt/Texte' }])).toEqual([
      'Projekt',
      'Projekt/Bilder',
      'Projekt/Texte',
      'Projekt/Bilder/Alt',
    ]);
  });
});

/** Nachbau der Einträge, die Browser beim Ablegen von Ordnern liefern (webkitGetAsEntry). */
function fileEntry(name: string, body = 'x') {
  return { name, isFile: true, isDirectory: false, file: (ok: (f: File) => void) => ok(new File([body], name)) };
}
function dirEntry(name: string, children: unknown[]) {
  return {
    name,
    isFile: false,
    isDirectory: true,
    // readEntries liefert in Stücken und zuletzt eine leere Liste (wie Chromium bei > 100 Einträgen)
    createReader: () => {
      const batches = [children.slice(0, 1), children.slice(1), []];
      return { readEntries: (ok: (b: unknown[]) => void) => ok(batches.shift() ?? []) };
    },
  };
}
function transfer(entries: unknown[]): DataTransfer {
  return { items: entries.map((e) => ({ kind: 'file', webkitGetAsEntry: () => e })), files: [] } as unknown as DataTransfer;
}

describe('Ordner per Drag & Drop (A-45)', () => {
  it('liest abgelegte Ordner rekursiv mit Pfad und überspringt Systemdateien', async () => {
    const dt = transfer([
      dirEntry('Projekt', [fileEntry('plan.pdf'), dirEntry('Bilder', [fileEntry('a.png'), fileEntry('.DS_Store'), dirEntry('Alt', [fileEntry('b.tif')])]), fileEntry('Thumbs.db')]),
      fileEntry('lose.txt'),
    ]);
    const out = await collectDropped(dt);
    expect(out.map((f) => `${f.dir}|${f.file.name}`)).toEqual(['Projekt|plan.pdf', 'Projekt/Bilder|a.png', 'Projekt/Bilder/Alt|b.tif', '|lose.txt']);
    expect(folderPaths(out)).toEqual(['Projekt', 'Projekt/Bilder', 'Projekt/Bilder/Alt']);
  });
  it('Ordner-Auswahl überspringt wie das Ablegen versteckte Ordner (.git) und Systemdateien', () => {
    const pick = (path: string) => ({ file: new File(['x'], path.split('/').pop() ?? path), dir: dirOf(path) });
    const out = usableFiles(['Projekt/plan.pdf', 'Projekt/.git/objects/ab/cdef12', 'Projekt/.idea/workspace.xml', 'Projekt/Bilder/Thumbs.db', 'Projekt/Bilder/a.png'].map(pick));
    expect(out.map((f) => `${f.dir}|${f.file.name}`)).toEqual(['Projekt|plan.pdf', 'Projekt/Bilder|a.png']);
    expect(folderPaths(out)).toEqual(['Projekt', 'Projekt/Bilder']);
  });
  it('ohne Ordner-Schnittstelle: nur die Dateien', async () => {
    const files = [new File(['x'], 'a.pdf'), new File(['y'], '.hidden')];
    const dt = { items: [{ kind: 'file', webkitGetAsEntry: () => null }], files } as unknown as DataTransfer;
    expect((await collectDropped(dt)).map((f) => f.file.name)).toEqual(['a.pdf']);
  });
});

describe('Schließen während des Hochladens (A-45)', () => {
  it('fragt im App-Dialog nach, solange Dateien warten – auch beim Schließen über die Werkzeugleiste', async () => {
    const asked: string[] = [];
    const stop = subscribeDialogs((q) => {
      const r = q[0];
      if (r && r.kind === 'confirm' && !asked.includes(r.opts.message)) {
        asked.push(r.opts.message);
        settleDialog(r, false);
      }
    });
    try {
      expect(await confirmAbortUploads(0)).toBe(true);
      expect(await confirmAbortUploads(3)).toBe(false);
      expect(asked).toEqual([expect.stringContaining('3 Dateien werden noch hochgeladen')]);
    } finally {
      stop();
    }
  });
});

describe('Freigabe (A-46)', () => {
  it('zur nächsten Stunde', () => {
    expect(draftToInput({ mode: 'next_lesson', from: '', lesson: null })).toEqual({ visibility: 'next_lesson' });
    const lessons = [
      { status: 'normal' as const, started: true, key: 'a' },
      { status: 'entfall' as const, started: false, key: 'b' },
      { status: 'geaendert' as const, started: false, key: 'c' },
    ];
    expect(nextHeldLesson(lessons)?.key).toBe('c');
    expect(nextHeldLesson([])).toBeNull();
  });
  it('Entfall-Hinweis', () => {
    const lesson = { date: '2026-10-12', lesson_id: 'L1', period: 0, label: 'Mo, 12.10. · 1. Std.', key: 'k' };
    expect(shiftText({ shift: null })).toBe('');
    expect(shiftText({ shift: { status: 'verschoben', reason: 'Entfall', release_at: null, to_label: 'Di, 13.10. · 3. Std.', to_date: '2026-10-13' } })).toBe(
      'Entfall → Di, 13.10. · 3. Std.',
    );
    expect(
      visibilityText({
        visibility: 'lesson',
        state: 'lesson',
        lesson: { ...lesson, shift: { status: 'verschoben', reason: 'Entfall', release_at: null, to_label: null, to_date: null } },
        visible_from: null,
        release_at: null,
      }),
    ).toContain('keine weitere Stunde');
    expect(folderVisibilityText({ visibility: 'hidden', state: 'hidden' })).toBe('verborgen');
  });
  it('fremdes Material im Klassenraum', () => {
    expect(canEdit({ can_edit: false }, true)).toBe(false);
    expect(canEdit({}, true)).toBe(true);
    expect(canEdit({ can_edit: true }, false)).toBe(false);
  });
});
