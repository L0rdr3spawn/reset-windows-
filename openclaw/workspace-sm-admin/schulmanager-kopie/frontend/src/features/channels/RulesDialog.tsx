/**
 * „Abschluss & Bedingungen“ eines Elements: wann gilt es als erledigt, und wann wird es für Teilnehmende freigegeben
 * (Bedingungen mit UND/ODER: anderes Element erledigt, Punkte/Note, Gruppe, Datum, Zeitfreigabe).
 */
import { useId, useState } from 'react';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import {
  addGroup,
  addLeaf,
  emptyTree,
  isLeaf,
  isoToLocal,
  LEAF_LABELS,
  leafCount,
  localToIso,
  MODE_HINTS,
  newLeaf,
  progressApi,
  removeAt,
  replaceLeaf,
  setOp,
  treeProblem,
  type CompletionMode,
  type ElementRow,
  type ElementsResponse,
  type Leaf,
  type LeafType,
  type Node,
} from './progress';
import type { Item } from './types';

const MAX_DEPTH = 2; // Untergruppen unter der Wurzel (der Server erlaubt 3 Ebenen)

function LeafEditor({
  leaf,
  data,
  selfKey,
  onChange,
  onRemove,
}: {
  leaf: Leaf;
  data: ElementsResponse;
  selfKey: string;
  onChange: (l: Leaf) => void;
  onRemove: () => void;
}) {
  const id = useId();
  const others = data.elements.filter((e) => e.completion && `${e.element_type}:${e.element_id}` !== selfKey);
  const gradable = others.filter((e) => e.modes.some((m) => m.mode === 'graded'));
  const pick = (list: ElementRow[], current: { element_type: string; element_id: number }) => (
    <select
      aria-label="Element"
      value={current.element_id ? `${current.element_type}:${current.element_id}` : ''}
      onChange={(e) => {
        const [t, i] = e.target.value.split(':');
        onChange({ ...leaf, element_type: t, element_id: Number(i) } as Leaf);
      }}
    >
      <option value="">Element wählen …</option>
      {list.map((e) => (
        <option key={`${e.element_type}:${e.element_id}`} value={`${e.element_type}:${e.element_id}`}>
          {e.title} ({e.kind_label})
        </option>
      ))}
    </select>
  );
  return (
    <div className="kr-cond-leaf">
      <span className="kr-cond-kind">{LEAF_LABELS[leaf.type]}</span>
      {leaf.type === 'completed' && pick(others, leaf)}
      {leaf.type === 'score' && (
        <>
          {pick(gradable, leaf)}
          <label className="kr-cond-num" htmlFor={`${id}-p`}>
            ab
          </label>
          <input id={`${id}-p`} type="number" min={0} max={100} value={leaf.min_percent} onChange={(e) => onChange({ ...leaf, min_percent: Number(e.target.value) })} />
          <span>%</span>
        </>
      )}
      {leaf.type === 'note' && (
        <>
          {pick(gradable, leaf)}
          <label className="kr-cond-num" htmlFor={`${id}-n`}>
            Note
          </label>
          <input id={`${id}-n`} type="number" min={1} max={6} step={0.1} value={leaf.max_note} onChange={(e) => onChange({ ...leaf, max_note: Number(e.target.value) })} />
          <span>oder besser</span>
        </>
      )}
      {leaf.type === 'group' && (
        <select aria-label="Gruppe" value={leaf.group_id || ''} onChange={(e) => onChange({ ...leaf, group_id: Number(e.target.value) })}>
          <option value="">Gruppe wählen …</option>
          {data.groups.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </select>
      )}
      {leaf.type === 'date' && (
        <>
          <label htmlFor={`${id}-f`}>Ab</label>
          <input id={`${id}-f`} type="datetime-local" value={isoToLocal(leaf.from)} onChange={(e) => onChange({ ...leaf, from: localToIso(e.target.value) })} />
          <label htmlFor={`${id}-u`}>Bis</label>
          <input id={`${id}-u`} type="datetime-local" value={isoToLocal(leaf.until)} onChange={(e) => onChange({ ...leaf, until: localToIso(e.target.value) })} />
        </>
      )}
      <button type="button" className="btn btn-sm btn-ghost" onClick={onRemove}>
        <Icon name="trash" />
        <span className="sr-only">Bedingung entfernen</span>
      </button>
    </div>
  );
}

function GroupEditor({
  node,
  path,
  depth,
  root,
  data,
  selfKey,
  onChange,
}: {
  node: Node;
  path: number[];
  depth: number;
  root: Node;
  data: ElementsResponse;
  selfKey: string;
  onChange: (n: Node) => void;
}) {
  const id = useId();
  const types: LeafType[] = ['completed', 'score', 'note', 'date', 'release', ...(data.groups_available ? (['group'] as LeafType[]) : [])];
  const add = (type: LeafType) => {
    const first = data.elements.find((e) => e.completion && `${e.element_type}:${e.element_id}` !== selfKey);
    onChange(addLeaf(root, path, newLeaf(type, first, data.groups[0]?.id)));
  };
  return (
    <div className={`kr-cond-group${depth ? ' kr-cond-sub' : ''}`}>
      <div className="row kr-cond-head">
        <label htmlFor={`${id}-op`} className="sr-only">
          Verknüpfung
        </label>
        <select id={`${id}-op`} value={node.op} onChange={(e) => onChange(setOp(root, path, e.target.value as 'and' | 'or'))}>
          <option value="and">Alle Bedingungen müssen erfüllt sein (UND)</option>
          <option value="or">Mindestens eine Bedingung genügt (ODER)</option>
        </select>
        {depth > 0 && (
          <button type="button" className="btn btn-sm btn-ghost" onClick={() => onChange(removeAt(root, path))}>
            <Icon name="trash" /> Gruppe entfernen
          </button>
        )}
      </div>
      <ul className="kr-cond-list">
        {node.items.map((child, i) => (
          <li key={i}>
            {isLeaf(child) ? (
              <LeafEditor leaf={child} data={data} selfKey={selfKey} onChange={(l) => onChange(replaceLeaf(root, [...path, i], l))} onRemove={() => onChange(removeAt(root, [...path, i]))} />
            ) : (
              <GroupEditor node={child} path={[...path, i]} depth={depth + 1} root={root} data={data} selfKey={selfKey} onChange={onChange} />
            )}
          </li>
        ))}
      </ul>
      <div className="row">
        <label htmlFor={`${id}-add`} className="sr-only">
          Bedingung hinzufügen
        </label>
        <select
          id={`${id}-add`}
          value=""
          onChange={(e) => {
            if (e.target.value) add(e.target.value as LeafType);
          }}
        >
          <option value="">+ Bedingung hinzufügen …</option>
          {types.map((t) => (
            <option key={t} value={t}>
              {LEAF_LABELS[t]}
            </option>
          ))}
        </select>
        {depth < MAX_DEPTH && (
          <button type="button" className="btn btn-sm" onClick={() => onChange(addGroup(root, path))}>
            <Icon name="plus" /> Untergruppe
          </button>
        )}
      </div>
    </div>
  );
}

function Editor({ data, item, onClose, onDone }: { data: ElementsResponse; item: Item; onClose: () => void; onDone: () => void }) {
  const channelId = item.channel_id;
  const selfKey = `item:${item.id}`;
  const me = data.elements.find((e) => `${e.element_type}:${e.element_id}` === selfKey);
  const toast = useToast();
  const modeId = useId();
  const passId = useId();
  const [mode, setMode] = useState<CompletionMode | ''>(me?.completion?.mode ?? '');
  const [pass, setPass] = useState(String(me?.completion?.pass_percent ?? 50));
  const [tree, setTree] = useState<Node>(me?.availability?.tree ?? emptyTree());
  const [error, setError] = useState<string | null>(null);
  const modes = me?.modes ?? [];
  const problem = treeProblem(tree);

  const save = async () => {
    if (problem) {
      setError(problem);
      return;
    }
    try {
      if (mode) {
        const pct = Number(pass);
        await progressApi.setCompletion(channelId, 'item', item.id, { mode, pass_percent: mode === 'passed' ? (Number.isFinite(pct) ? pct : 50) : null });
      } else if (me?.completion) {
        await progressApi.removeCompletion(channelId, 'item', item.id);
      }
      await progressApi.setAvailability(channelId, 'item', item.id, leafCount(tree) ? tree : null);
      toast.success('Gespeichert');
      onDone();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  return (
    <Modal
      title={`Abschluss & Bedingungen: ${item.title}`}
      size="lg"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save} disabled={!!problem}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        {error && <Alert kind="error">{error}</Alert>}
        <fieldset className="kr-fieldset stack-sm">
          <legend>Wann gilt das Element als erledigt?</legend>
          <div className="field">
            <label htmlFor={modeId}>
              Abschlussbedingung
              <HelpTip>Mit einer Bedingung sehen Teilnehmende ein „Erledigt“-Häkchen und der Kursraum zeigt einen Fortschrittsbalken. Ohne Bedingung wird das Element nicht verfolgt.</HelpTip>
            </label>
            <select id={modeId} value={mode} onChange={(e) => setMode(e.target.value as CompletionMode | '')}>
              <option value="">Nicht verfolgen</option>
              {modes.map((m) => (
                <option key={m.mode} value={m.mode}>
                  {m.label}
                </option>
              ))}
            </select>
            {mode && <span className="hint">{MODE_HINTS[mode]}</span>}
          </div>
          {mode === 'passed' && (
            <div className="field">
              <label htmlFor={passId}>
                Mindestpunktzahl in Prozent
                <HelpTip>Ohne Prozentwert in der Bewertung gilt Note 4 oder besser als bestanden.</HelpTip>
              </label>
              <input id={passId} type="number" min={0} max={100} value={pass} onChange={(e) => setPass(e.target.value)} />
            </div>
          )}
        </fieldset>

        <fieldset className="kr-fieldset stack-sm">
          <legend>
            Wann wird es freigegeben?
            <HelpTip>
              Teilnehmende sehen ein gesperrtes Element nur mit Titel und „Verfügbar, sobald …“. „Verborgen“ sperrt immer. Die Zeitfreigabe (geplant oder zur Stunde) gilt zusätzlich – außer Sie nehmen sie als Bedingung „Zeitfreigabe erreicht“ in die Verknüpfung auf.
            </HelpTip>
          </legend>
          {!tree.items.length && <p className="small muted">Keine zusätzlichen Bedingungen.</p>}
          <GroupEditor node={tree} path={[]} depth={0} root={tree} data={data} selfKey={selfKey} onChange={setTree} />
          {!data.groups_available && <p className="xsmall muted">Noch keine Gruppen im Kursraum.</p>}
          {problem && <p className="small kr-problem">{problem}</p>}
        </fieldset>
      </div>
    </Modal>
  );
}

export default function RulesDialog({ item, onClose, onDone }: { item: Item; onClose: () => void; onDone: () => void }) {
  const q = useApi<ElementsResponse>((signal) => progressApi.elements(item.channel_id, signal), [item.channel_id]);
  return q.data ? (
    <Editor data={q.data} item={item} onClose={onClose} onDone={onDone} />
  ) : (
    <Modal title={`Abschluss & Bedingungen: ${item.title}`} onClose={onClose}>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : <Loading />}
    </Modal>
  );
}
