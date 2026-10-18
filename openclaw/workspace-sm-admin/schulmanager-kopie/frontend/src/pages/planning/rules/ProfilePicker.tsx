/** Schulart/Profil als Vorlage: passende Wichtigkeiten und nur die Bausteine, die diese Schulart braucht. */
import { Icon } from '../../../components/Icon';
import type { RuleTemplate } from './model';

export function ProfilePicker({
  templates,
  value,
  onPick,
  onDelete,
  disabled,
}: {
  templates: RuleTemplate[];
  value: string;
  onPick: (t: RuleTemplate) => void;
  onDelete?: (t: RuleTemplate) => void;
  disabled?: boolean;
}) {
  return (
    <div className="rule-profile-grid">
      {templates.map((t) => (
        <div key={t.id} style={{ position: 'relative' }}>
          <button type="button" className="rule-profile" aria-pressed={t.id === value} disabled={disabled} onClick={() => onPick(t)} style={{ width: '100%', height: '100%' }}>
            <strong>
              {t.name}
              {!t.builtin && <span className="badge badge-info" style={{ marginLeft: 6 }}>eigene</span>}
            </strong>
            <span className="small muted">{t.description || 'Eigene Vorlage dieser Schule.'}</span>
          </button>
          {!t.builtin && onDelete && !disabled && (
            <button type="button" className="btn btn-sm btn-ghost" style={{ position: 'absolute', top: 4, right: 4 }} aria-label={`Vorlage ${t.name} löschen`} onClick={() => onDelete(t)}>
              <Icon name="trash" />
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
