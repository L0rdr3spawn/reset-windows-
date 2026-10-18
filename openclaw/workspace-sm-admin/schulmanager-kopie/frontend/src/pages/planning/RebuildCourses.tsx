import { useState } from 'react';
import { planning } from '../../api/endpoints';
import type { RebuildResult } from '../../api/types';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { HelpTip } from '../../components/HelpTip';
import { Alert, AsyncButton } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { invalidate } from '../../hooks/useCollection';

function List({ items, max = 12 }: { items: string[]; max?: number }) {
  if (!items.length) return null;
  return (
    <ul className="small">
      {items.slice(0, max).map((x, i) => (
        <li key={i}>{x}</li>
      ))}
      {items.length > max && <li>… {items.length - max} weitere</li>}
    </ul>
  );
}

function counts(r: RebuildResult): string {
  return [
    `${r.created.length} neu`,
    `${r.changed.length} geändert`,
    `${r.removed.length} entfernt`,
    r.removed_lessons ? `${r.removed_lessons} Stunden fallen aus dem Plan` : '',
  ]
    .filter(Boolean)
    .join(' · ');
}

/** Ergebnis von „Kurse erzeugen“: Zahlen, Warnungen und – falls nötig – Hinweis mit Direktknopf zum Neuberechnen. */
export function RebuildResultView({ result, onReplan, replanLabel = 'Stundenplan neu berechnen' }: { result: RebuildResult; onReplan?: () => void; replanLabel?: string }) {
  return (
    <div className="stack">
      <Alert kind={result.warnings.length ? 'warning' : 'success'} title={`Kurse erzeugt: ${counts(result)}`}>
        <List items={result.warnings} max={20} />
      </Alert>
      {result.replan_needed && (
        <Alert
          kind="warning"
          title={
            <>
              Der Stundenplan passt noch nicht zu den neuen Wochenstunden{' '}
              <HelpTip label="Erklärung: Neu berechnen">Neu berechnen und den Entwurf übernehmen, damit die Änderungen im Plan erscheinen.</HelpTip>
            </>
          }
          action={
            onReplan ? (
              <button type="button" className="btn btn-primary btn-sm" onClick={onReplan}>
                <Icon name="play" /> {replanLabel}
              </button>
            ) : undefined
          }
        />
      )}
    </div>
  );
}

/**
 * „Kurse erzeugen“ mit Vorschau: zeigt vorher neue/geänderte/entfernte Kurse, Konflikte und Kurse mit eigenen
 * Anpassungen (bleiben erhalten oder werden auf Wunsch zurückgesetzt). Das Ergebnis geht an `onDone`
 * (Anzeige mit `RebuildResultView`).
 */
export function RebuildCourses({ onDone, className = 'btn' }: { onDone: (r: RebuildResult | null) => void; className?: string }) {
  const toast = useToast();
  const [preview, setPreview] = useState<RebuildResult | null>(null);
  const [reset, setReset] = useState(false);

  const load = async (resetManual: boolean) => {
    try {
      setPreview(await planning.coursesFromCurricula({ dry_run: true, reset_manual: resetManual }));
    } catch (e) {
      toast.error(e, 'Vorschau');
    }
  };

  const run = async () => {
    try {
      const r = await planning.coursesFromCurricula({ reset_manual: reset });
      onDone(r);
      setPreview(null);
      invalidate('courses');
    } catch (e) {
      toast.error(e, 'Kurse erzeugen');
    }
  };

  return (
    <>
      <AsyncButton
        className={className}
        onClick={async () => {
          setReset(false);
          onDone(null);
          await load(false);
        }}
      >
        <Icon name="sparkles" /> Kurse erzeugen …
      </AsyncButton>

      {preview && (
        <Modal
          size="lg"
          title="Kurse aus Stundentafeln erzeugen"
          onClose={() => setPreview(null)}
          footer={
            <>
              <button type="button" className="btn" onClick={() => setPreview(null)}>
                Abbrechen
              </button>
              <AsyncButton className="btn btn-primary" onClick={run}>
                <Icon name="check" /> Kurse erzeugen
              </AsyncButton>
            </>
          }
        >
          <div className="stack">
            <p style={{ margin: 0 }}>
              <strong>Vorschau:</strong> {counts(preview)}
            </p>
            {preview.conflicts.length > 0 && (
              <Alert kind="error" title="Überschneidende Stundentafeln – Kurse dieser Klassen bleiben unverändert">
                <List items={preview.warnings.filter((w) => w.startsWith('Konflikt'))} />
              </Alert>
            )}
            {preview.kept.length > 0 && (
              <Alert kind={reset ? 'warning' : 'info'} title={reset ? 'Eigene Anpassungen werden verworfen' : 'Eigene Anpassungen bleiben erhalten'}>
                <List items={preview.kept.map((k) => `${k.label}: ${k.labels.join(', ')}${k.fields.includes('hours') ? ` (Stundentafel: ${k.curriculum_hours} Std.)` : ''}`)} />
              </Alert>
            )}
            {(preview.kept.length > 0 || reset) && (
              <label className="check">
                <input
                  type="checkbox"
                  checked={reset}
                  onChange={(e) => {
                    setReset(e.target.checked);
                    void load(e.target.checked);
                  }}
                />{' '}
                Anpassungen verwerfen (wieder wie Stundentafel)
              </label>
            )}
            {preview.changed.length > 0 && (
              <details className="disclosure">
                <summary>{preview.changed.length} Kurse ändern sich</summary>
                <List items={preview.changed.map((c) => c.label)} max={40} />
              </details>
            )}
            {preview.removed.length > 0 && (
              <details className="disclosure">
                <summary>{preview.removed.length} Kurse werden entfernt</summary>
                <List items={preview.removed} max={40} />
              </details>
            )}
            {preview.warnings.filter((w) => !w.startsWith('Konflikt')).length > 0 && (
              <Alert kind="warning" title="Hinweise">
                <List items={preview.warnings.filter((w) => !w.startsWith('Konflikt'))} />
              </Alert>
            )}
          </div>
        </Modal>
      )}

    </>
  );
}
