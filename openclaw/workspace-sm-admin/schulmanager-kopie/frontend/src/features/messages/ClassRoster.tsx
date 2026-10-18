/**
 * Klassenansicht in der Empfängerauswahl: nach einer Klasse suchen → Klassenleitung, Lehrkräfte und (für Personal mit
 * Sicht auf die Klasse) alle Kinder mit ihren Eltern. Eltern zeigen ihre Kinder auch in anderen Klassen. Schnellknöpfe
 * fügen – wenn erlaubt – die Gruppe als Rundschreiben hinzu, sonst die einzelnen Personen.
 */
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { useApi } from '../../hooks/useApi';
import { messagesApi } from './api';
import { Avatar } from './components';
import { addRecipient, plural, recipientKey } from './logic';
import type { ClassRoster, GroupOption, Person, Recipient } from './types';

function addAll(list: Recipient[], items: (Recipient | null | undefined)[]): Recipient[] {
  return items.reduce<Recipient[]>((acc, r) => (r ? addRecipient(acc, r) : acc), list);
}

function PersonRow({ p, selected, onAdd, extra }: { p: Person; selected: Set<string>; onAdd: (r: Recipient) => void; extra?: string }) {
  const chosen = selected.has(recipientKey(p));
  return (
    <span className="pf-roster-person">
      <Avatar name={p.name} role={p.role} size={22} />
      <span className="pf-roster-name">
        {p.name}
        {extra ? <span className="xsmall muted"> · {extra}</span> : null}
      </span>
      <button type="button" className="btn btn-ghost btn-sm" disabled={chosen} aria-label={`${p.name} hinzufügen`} onClick={() => onAdd(p)}>
        {chosen ? <Icon name="check" /> : <Icon name="plus" />}
      </button>
    </span>
  );
}

export function ClassRosterPanel({ classId, value, onChange, onClose }: { classId: string; value: Recipient[]; onChange: (list: Recipient[]) => void; onClose: () => void }) {
  const q = useApi<ClassRoster>((signal) => messagesApi.classRoster(classId, signal), [classId]);
  const selected = new Set(value.map(recipientKey));
  const add = (items: (Recipient | null | undefined)[]) => onChange(addAll(value, items));
  const data = q.data;
  const group = (kind: string): GroupOption | undefined => data?.groups.find((g) => g.kind === kind);
  const kids = (data?.students ?? []).map((s) => s.account).filter((x): x is Person => !!x);
  const parents = (data?.students ?? []).flatMap((s) => s.parents);
  const teachers = [...(data?.leads ?? []), ...(data?.teachers ?? [])];

  // Schnellknöpfe: Gruppe (Rundschreiben), sonst einzelne Personen
  const quick: { label: string; items: Recipient[] }[] = [];
  if (data) {
    const g = {
      kids: group('class'),
      parents: group('class_parents'),
      lead: group('class_lead'),
      teachers: group('class_teachers'),
    };
    const kidsItems = g.kids ? [g.kids] : data.full ? kids : [];
    const parentItems = g.parents ? [g.parents] : data.full ? parents : [];
    if (kidsItems.length)
      quick.push({
        label: `Kinder${g.kids ? '' : ` (${kids.length})`}`,
        items: kidsItems,
      });
    if (parentItems.length)
      quick.push({
        label: `Eltern${g.parents ? '' : ` (${parents.length})`}`,
        items: parentItems,
      });
    if (kidsItems.length && parentItems.length)
      quick.push({
        label: 'Kinder und Eltern',
        items: [...kidsItems, ...parentItems],
      });
    const leadItems = g.lead ? [g.lead] : data.leads;
    if (leadItems.length) quick.push({ label: 'Klassenleitung', items: leadItems });
    const teacherItems = g.teachers ? [g.teachers] : teachers;
    if (teacherItems.length) quick.push({ label: 'Alle Lehrkräfte der Klasse', items: teacherItems });
  }

  return (
    <section className="pf-roster card stack-sm" aria-label={`Klasse ${data?.class.name ?? classId}`}>
      <div className="row-between">
        <strong>Klasse {data?.class.name ?? classId}</strong>
        <button type="button" className="btn btn-ghost btn-icon" aria-label="Klassenansicht schließen" onClick={onClose}>
          <Icon name="x" />
        </button>
      </div>
      {q.error ? <p className="pf-error-text small">{errorMessage(q.error)}</p> : null}
      {!data && !q.error && <p className="small muted">Lädt …</p>}
      {data && (
        <>
          {quick.length > 0 && (
            <div className="row pf-roster-quick" role="group" aria-label="Schnell hinzufügen">
              {quick.map((b) => (
                <button key={b.label} type="button" className="btn btn-sm" onClick={() => add(b.items)}>
                  <Icon name="plus" /> {b.label}
                </button>
              ))}
            </div>
          )}
          {teachers.length > 0 && (
            <div className="stack-sm">
              <span className="xsmall muted">Lehrkräfte</span>
              {data.leads.map((p) => (
                <PersonRow key={p.id} p={p} selected={selected} onAdd={(r) => add([r])} extra="Klassenleitung" />
              ))}
              {data.teachers.map((p) => (
                <PersonRow key={p.id} p={p} selected={selected} onAdd={(r) => add([r])} />
              ))}
            </div>
          )}
          {data.full && (
            <div className="stack-sm">
              <span className="xsmall muted">{plural(data.students.length, 'Kind', 'Kinder')} mit Eltern</span>
              <ul className="pf-roster-kids">
                {data.students.map((s) => (
                  <li key={s.student_id}>
                    {s.account ? (
                      <PersonRow p={s.account} selected={selected} onAdd={(r) => add([r])} />
                    ) : (
                      <span className="pf-roster-name">
                        {s.name} <span className="xsmall muted">(kein Konto)</span>
                      </span>
                    )}
                    {s.parents.map((p) => {
                      const others = (p.children ?? []).filter((c) => c.id !== s.student_id);
                      const extra = others.length ? `auch ${others.map((c) => `${c.name} (${c.class})`).join(', ')}` : '';
                      return (
                        <span key={p.id} className="pf-roster-parent">
                          <PersonRow p={p} selected={selected} onAdd={(r) => add([r])} extra={extra} />
                        </span>
                      );
                    })}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  );
}
