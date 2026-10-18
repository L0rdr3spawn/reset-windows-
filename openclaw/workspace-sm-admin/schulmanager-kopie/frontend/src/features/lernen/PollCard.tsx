/**
 * Eine Abstimmung: Antworten wählen und Ergebnis als Balken – im Kursraum und im Chat dieselbe Darstellung.
 * Die Texte kommen von außen (Kursraum: vom Server, Chat: aus der Ende-zu-Ende-verschlüsselten Nachricht).
 */
import { useEffect, useId, useState, type ReactNode } from 'react';
import { AsyncButton } from '../../components/ui';
import { formatDateTime } from '../../lib/dates';
import type { PollState } from './api';
import { barPercent, pollFacts, toggleChoice } from './logic';
import './lernen.css';

export function Bar({ percent, label }: { percent: number; label: string }) {
  // SVG statt Inline-Style: Breite als Attribut, Farbe über Design-Tokens
  return (
    <svg className="ln-bar" role="img" aria-label={label} viewBox="0 0 100 10" preserveAspectRatio="none" focusable="false">
      <rect className="ln-bar-bg" x="0" y="0" width="100" height="10" rx="2" />
      {percent > 0 && <rect className="ln-bar-fill" x="0" y="0" width={Math.max(percent, 1.5)} height="10" rx="2" />}
    </svg>
  );
}

export function PollCard({
  question,
  options,
  poll,
  onVote,
  onClose,
  onDelete,
  compact,
}: {
  question: ReactNode;
  options: string[];
  poll: PollState;
  onVote: (choices: number[]) => Promise<unknown>;
  onClose?: () => Promise<unknown>;
  onDelete?: () => Promise<unknown>;
  compact?: boolean;
}) {
  const uid = useId();
  const [selected, setSelected] = useState<number[]>(poll.mine);
  const mineKey = poll.mine.join(',');
  useEffect(() => setSelected(poll.mine), [mineKey, poll.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const voting = poll.can_vote;
  const counts = poll.counts;
  const total = poll.total ?? 0;
  const changed = selected.join(',') !== mineKey;
  const facts = pollFacts(poll, (iso) => formatDateTime(iso));
  const type = poll.multiple ? 'checkbox' : 'radio';

  return (
    <div className={`ln-poll${compact ? ' ln-compact' : ''}`}>
      <div className="ln-poll-q">{question}</div>
      <p className="ln-facts small muted">{facts.join(' · ')}</p>
      <fieldset className="ln-options" disabled={!voting}>
        <legend className="sr-only">Antworten</legend>
        {options.map((text, i) => {
          const n = counts?.[i] ?? 0;
          const pct = barPercent(n, total);
          const mine = poll.mine.includes(i);
          const label = counts ? `${text}: ${n} ${n === 1 ? 'Stimme' : 'Stimmen'} (${pct} %)` : text;
          return (
            <div key={i} className={`ln-option${mine ? ' is-mine' : ''}`}>
              <label className="ln-option-head">
                {voting ? (
                  <input type={type} name={`${uid}-o`} checked={selected.includes(i)} onChange={() => setSelected((s) => toggleChoice(s, i, poll.multiple, poll.max_choices))} />
                ) : (
                  <span className="ln-mark" aria-hidden="true">
                    {mine ? '✓' : ''}
                  </span>
                )}
                <span className="ln-option-text">{text}</span>
                {counts && (
                  <span className="ln-option-count mono">
                    {n} · {pct} %
                  </span>
                )}
              </label>
              {counts && <Bar percent={pct} label={label} />}
              {poll.voters?.[String(i)]?.length ? <p className="ln-voters small muted">{poll.voters[String(i)]!.join(', ')}</p> : null}
            </div>
          );
        })}
      </fieldset>
      <div className="ln-poll-foot">
        {poll.show_results ? (
          <span className="small muted">{total === 1 ? '1 Person hat' : `${total} Personen haben`} abgestimmt</span>
        ) : poll.closed ? null : (
          <span className="small muted">Ergebnis noch nicht sichtbar</span>
        )}
        <span className="ln-poll-actions">
          {voting && (
            <AsyncButton className="btn btn-primary btn-sm" disabled={!selected.length || (poll.voted && !changed)} onClick={() => onVote(selected)}>
              {poll.voted && !poll.anonymous ? 'Stimme ändern' : 'Abstimmen'}
            </AsyncButton>
          )}
          {!voting && poll.voted && !poll.closed && poll.anonymous && <span className="badge badge-success">Stimme abgegeben</span>}
          {onClose && !poll.closed && (
            <AsyncButton className="btn btn-sm" confirm="Abstimmung jetzt beenden? Danach ist keine Stimme mehr möglich." onClick={onClose}>
              Beenden
            </AsyncButton>
          )}
          {onDelete && (
            <AsyncButton className="btn btn-sm btn-ghost" confirm="Abstimmung samt allen Stimmen löschen?" onClick={onDelete}>
              Löschen
            </AsyncButton>
          )}
        </span>
      </div>
    </div>
  );
}

export default PollCard;
