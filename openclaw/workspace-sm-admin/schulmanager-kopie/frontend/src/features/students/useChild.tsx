/**
 * Kinderauswahl für Eltern – gemeinsam für Startseite, Krankmeldungen, Noten und Kursräume (ein gemerktes Kind,
 * Speicher-Schlüssel `sm-child`). Schüler/innen haben keine Auswahl (`child` ist dann `undefined`).
 */
import { useUser } from '../../context/AuthContext';
import { useStoredState } from '../../hooks/misc';
import { pickChild } from './logic';

export const CHILD_KEY = 'sm-child';

export function useFamilyChild(): { parent: boolean; child: string | undefined; setChild: (id: string) => void; kids: { id: string; name: string; class_id?: string | null }[] } {
  const user = useUser();
  const parent = user.role === 'eltern';
  const [stored, setStored] = useStoredState<string | null>(CHILD_KEY, null);
  const kids = user.students ?? [];
  const child = parent ? pickChild(kids, stored) ?? undefined : undefined;
  return { parent, child, setChild: setStored, kids };
}

/** Auswahlfeld „Kind“ – nur bei Eltern mit mehreren Kindern sichtbar. */
export function ChildSelect({ kids, value, onChange, id = 'st-child' }: { kids: { id: string; name: string; class_id?: string | null }[]; value: string | undefined; onChange: (id: string) => void; id?: string }) {
  if (kids.length < 2) return null;
  return (
    <div className="field st-child">
      <label htmlFor={id}>Kind</label>
      <select id={id} value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
        {kids.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
            {c.class_id ? ` (${c.class_id})` : ''}
          </option>
        ))}
      </select>
    </div>
  );
}
