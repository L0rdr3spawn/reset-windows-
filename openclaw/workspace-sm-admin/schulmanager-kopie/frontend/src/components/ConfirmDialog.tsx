import { useState, type ReactNode } from 'react';
import { Modal } from './Modal';
import { AsyncButton } from './ui';

/**
 * Bestätigungsdialog im Stil der App (statt `window.confirm`): Titel, Text, „Abbrechen“ und eine Hauptaktion.
 * `danger` färbt die Hauptaktion rot (nur für Löschen/Leeren). `onConfirm` darf asynchron sein; der Dialog schließt
 * nach Erfolg, bei einem Fehler bleibt er offen und der Fehler erscheint als Meldung.
 */
export function ConfirmDialog({
  title,
  children,
  confirmLabel,
  danger,
  confirmDisabled,
  onConfirm,
  onCancel,
}: {
  title: ReactNode;
  children?: ReactNode;
  confirmLabel: string;
  danger?: boolean;
  /** Hauptaktion gesperrt, bis eine nötige Auswahl getroffen ist */
  confirmDisabled?: boolean;
  onConfirm: () => Promise<unknown> | void;
  onCancel: () => void;
}) {
  const [done, setDone] = useState(false);
  return (
    <Modal
      title={title}
      onClose={onCancel}
      footer={
        <>
          <button type="button" className="btn" onClick={onCancel}>
            Abbrechen
          </button>
          <AsyncButton
            className={danger ? 'btn btn-danger' : 'btn btn-primary'}
            disabled={done || confirmDisabled}
            onClick={async () => {
              await onConfirm();
              setDone(true);
              onCancel();
            }}
          >
            {confirmLabel}
          </AsyncButton>
        </>
      }
    >
      <div className="stack">{children}</div>
    </Modal>
  );
}
