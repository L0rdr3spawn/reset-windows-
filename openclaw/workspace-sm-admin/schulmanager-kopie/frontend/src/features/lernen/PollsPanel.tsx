/** Abstimmungen eines Kursraums (Bereich „Tests & Umfragen“). */
import { useState } from 'react';
import { Icon } from '../../components/Icon';
import { Empty, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { learnApi } from './api';
import { PollCard } from './PollCard';
import { PollDialog } from './PollDialog';
import { Markdown } from '../channels/MarkdownView';
import './lernen.css';

export default function PollsPanel({ channelId, childId }: { channelId: number; childId?: string | null }) {
  const q = useApi((signal) => learnApi.polls(channelId, childId, signal), [channelId, childId], { live: [`channel:${channelId}:`] });
  const [creating, setCreating] = useState(false);
  const toast = useToast();
  if (q.error && !q.data) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  const { polls, can_create } = q.data;
  const after = async (fn: () => Promise<unknown>, message?: string) => {
    await fn();
    if (message) toast.success(message);
    q.reload();
  };
  return (
    <section className="stack" aria-label="Abstimmungen">
      {can_create && (
        <div>
          <button type="button" className="btn btn-primary" onClick={() => setCreating(true)}>
            <Icon name="plus" /> Neue Abstimmung
          </button>
        </div>
      )}
      {polls.length === 0 ? (
        <Empty icon="checkCircle" title="Noch keine Abstimmung">
          {can_create ? 'Stellen Sie eine Frage mit mehreren Antworten.' : 'Sobald eine Abstimmung gestellt wird, erscheint sie hier.'}
        </Empty>
      ) : (
        <ul className="ln-cards">
          {polls.map((p) => (
            <li key={p.id} className="card ln-card">
              <PollCard
                question={<Markdown text={p.question} />}
                options={p.options}
                poll={p}
                onVote={(choices) => after(() => learnApi.vote(channelId, p.id, choices), 'Stimme gespeichert')}
                onClose={p.editable ? () => after(() => learnApi.closePoll(channelId, p.id), 'Abstimmung beendet') : undefined}
                onDelete={p.editable ? () => after(() => learnApi.deletePoll(channelId, p.id), 'Abstimmung gelöscht') : undefined}
              />
            </li>
          ))}
        </ul>
      )}
      {creating && <PollDialog onClose={() => setCreating(false)} onSubmit={(input) => after(() => learnApi.createPoll(channelId, input), 'Abstimmung gestartet')} />}
    </section>
  );
}
