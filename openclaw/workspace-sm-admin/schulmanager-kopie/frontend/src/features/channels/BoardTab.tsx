/**
 * Bereich „Pinnwand“: Beiträge mit einer Ebene Antworten, Anheften (Lehrende), eigene Beiträge bearbeiten,
 * Moderation (Lehrende löschen fremde Beiträge). Teilnehmende schreiben nur, wenn der Kursraum es erlaubt.
 */
import { useState } from 'react';
import { errorMessage } from '../../api/client';
import { FileList } from '../../components/FileList';
import { FileUpload } from '../../components/FileUpload';
import { Icon } from '../../components/Icon';
import { AsyncButton, Empty, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { channelsApi } from './api';
import { formatWhen } from './logic';
import { Markdown } from './MarkdownView';
import type { ChannelDetail, Post, PostsResponse } from './types';

function Composer({
  channelId,
  parentId,
  maxLength,
  placeholder,
  onDone,
  onCancel,
  compact,
}: {
  channelId: number;
  parentId?: number;
  maxLength: number;
  placeholder: string;
  onDone: () => void;
  onCancel?: () => void;
  compact?: boolean;
}) {
  const [text, setText] = useState('');
  const [files, setFiles] = useState<string[]>([]);
  const [round, setRound] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const id = `kr-post-${parentId ?? 'new'}`;
  const send = async () => {
    if (!text.trim()) return;
    try {
      await channelsApi.createPost(channelId, { body: text, parent_id: parentId ?? null, attachment_ids: files });
      setText('');
      setFiles([]);
      setRound((r) => r + 1);
      setError(null);
      onDone();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <div className={`kr-composer${compact ? ' compact' : ''}`}>
      <label htmlFor={id} className="sr-only">
        {parentId ? 'Antwort schreiben' : 'Neuer Beitrag'}
      </label>
      <textarea id={id} rows={compact ? 2 : 3} value={text} maxLength={maxLength} placeholder={placeholder} onChange={(e) => setText(e.target.value)} />
      {error && (
        <p role="alert" className="kr-error">
          {error}
        </p>
      )}
      <div className="row-between">
        <FileUpload key={round} purpose="channel_post" compact label="Datei anhängen" maxFiles={10} onChange={(f) => setFiles(f.map((x) => x.id))} />
        <div className="row">
          {onCancel && (
            <button type="button" className="btn btn-sm" onClick={onCancel}>
              Abbrechen
            </button>
          )}
          <AsyncButton className="btn btn-sm btn-primary" onClick={send} disabled={!text.trim()}>
            <Icon name="check" /> {parentId ? 'Antworten' : 'Veröffentlichen'}
          </AsyncButton>
        </div>
      </div>
    </div>
  );
}

function PostView({
  post,
  channelId,
  canReply,
  maxLength,
  onChanged,
}: {
  post: Post;
  channelId: number;
  canReply: boolean;
  maxLength: number;
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(post.body);
  const [replying, setReplying] = useState(false);
  const toast = useToast();
  const isReply = post.parent_id !== null;
  const save = async () => {
    try {
      await channelsApi.patchPost(channelId, post.id, { body: draft });
      setEditing(false);
      onChanged();
    } catch (e) {
      toast.error(e);
    }
  };
  const remove = async () => {
    try {
      await channelsApi.deletePost(channelId, post.id);
      toast.success(post.own ? 'Beitrag gelöscht' : 'Beitrag entfernt');
      onChanged();
    } catch (e) {
      toast.error(e);
    }
  };
  const pin = async () => {
    try {
      await channelsApi.patchPost(channelId, post.id, { pinned: !post.pinned });
      onChanged();
    } catch (e) {
      toast.error(e);
    }
  };
  return (
    <article className={`kr-post${isReply ? ' reply' : ''}${post.pinned ? ' pinned' : ''}`} aria-label={`${isReply ? 'Antwort' : 'Beitrag'} von ${post.author_name}`}>
      <header className="kr-post-head">
        <strong className="kr-post-author">{post.author_name}</strong>
        {post.author_is_teacher && <span className="badge badge-primary">Lehrkraft</span>}
        {post.pinned && (
          <span className="badge badge-warning">
            <Icon name="lock" /> angeheftet
          </span>
        )}
        <span className="xsmall muted">
          {formatWhen(post.created_at)}
          {post.edited_at ? ' · bearbeitet' : ''}
        </span>
      </header>
      {post.deleted ? (
        <p className="small muted">Dieser Beitrag wurde gelöscht.</p>
      ) : editing ? (
        <div className="stack-sm">
          <label htmlFor={`kr-edit-${post.id}`} className="sr-only">
            Beitrag bearbeiten
          </label>
          <textarea id={`kr-edit-${post.id}`} rows={3} value={draft} maxLength={maxLength} onChange={(e) => setDraft(e.target.value)} />
          <div className="row-end">
            <button type="button" className="btn btn-sm" onClick={() => setEditing(false)}>
              Abbrechen
            </button>
            <AsyncButton className="btn btn-sm btn-primary" onClick={save} disabled={!draft.trim()}>
              Speichern
            </AsyncButton>
          </div>
        </div>
      ) : (
        <Markdown text={post.body} className="kr-post-body" />
      )}
      {!post.deleted && post.attachments.length > 0 && <FileList files={post.attachments} compact label="Anhänge" />}
      {!post.deleted && (
        <div className="kr-post-actions">
          {!isReply && canReply && (
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => setReplying((r) => !r)} aria-expanded={replying}>
              <Icon name="undo" /> Antworten
            </button>
          )}
          {post.can_edit && !editing && (
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => setEditing(true)}>
              <Icon name="edit" /> Bearbeiten
            </button>
          )}
          {post.can_pin && (
            <AsyncButton className="btn btn-sm btn-ghost" onClick={pin}>
              <Icon name={post.pinned ? 'unlock' : 'lock'} /> {post.pinned ? 'Lösen' : 'Anheften'}
            </AsyncButton>
          )}
          {post.can_delete && (
            <AsyncButton
              className="btn btn-sm btn-ghost"
              confirm={post.own ? 'Beitrag löschen?' : !isReply && post.replies?.length ? 'Beitrag samt Antworten entfernen?' : 'Beitrag entfernen?'}
              onClick={remove}
            >
              <Icon name="trash" /> {post.own ? 'Löschen' : 'Entfernen'}
            </AsyncButton>
          )}
        </div>
      )}
      {post.replies && post.replies.length > 0 && (
        <div className="kr-replies">
          {post.replies.map((r) => (
            <PostView key={r.id} post={r} channelId={channelId} canReply={false} maxLength={maxLength} onChanged={onChanged} />
          ))}
        </div>
      )}
      {replying && (
        <Composer
          channelId={channelId}
          parentId={post.id}
          maxLength={maxLength}
          placeholder="Antwort schreiben …"
          compact
          onCancel={() => setReplying(false)}
          onDone={() => {
            setReplying(false);
            onChanged();
          }}
        />
      )}
    </article>
  );
}

export default function BoardTab({ detail }: { detail: ChannelDetail }) {
  const ch = detail.channel;
  const [before, setBefore] = useState<number | null>(null);
  const [older, setOlder] = useState<Post[]>([]);
  const childId = detail.child?.id ?? null;
  const q = useApi<PostsResponse>((signal) => channelsApi.posts(ch.id, null, signal, childId), [ch.id, childId], { live: [`channel:${ch.id}:`] });
  const toast = useToast();
  const data = q.data;
  const perms = data?.permissions ?? detail.permissions;
  const loadOlder = async () => {
    const cursor = before ?? data?.next_before ?? null;
    if (!cursor) return;
    try {
      const res = await channelsApi.posts(ch.id, cursor, undefined, childId);
      setOlder((o) => [...o, ...res.posts.filter((p) => !p.pinned)]);
      setBefore(res.has_more ? res.next_before : -1);
    } catch (e) {
      toast.error(e);
    }
  };
  const reload = () => {
    setOlder([]);
    setBefore(null);
    q.reload();
  };
  const posts = [...(data?.posts ?? []), ...older.filter((o) => !(data?.posts ?? []).some((p) => p.id === o.id))];
  const hasMore = before === null ? !!data?.has_more : before > 0;
  return (
    <div className="stack-sm kr-board">
      {perms.post ? (
        <Composer channelId={ch.id} maxLength={detail.limits.max_post} placeholder="Neuer Beitrag – Frage, Hinweis, Link …" onDone={reload} />
      ) : (
        <p className="small muted">
          {ch.archived
            ? 'Der Kursraum ist archiviert.'
            : ch.role === 'supervisor' || ch.role === 'parent'
              ? 'Sie lesen die Pinnwand mit (nur lesen).'
              : perms.reply
                ? 'Neue Beiträge schreiben in diesem Kursraum nur die Lehrenden – antworten können Sie.'
                : 'Neue Beiträge schreiben in diesem Kursraum nur die Lehrenden.'}
        </p>
      )}
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {data && !posts.length && <Empty icon="info">Noch keine Beiträge.</Empty>}
      {posts.map((p) => (
        <PostView key={p.id} post={p} channelId={ch.id} canReply={perms.reply} maxLength={detail.limits.max_post} onChanged={reload} />
      ))}
      {hasMore && (
        <div className="center">
          <AsyncButton className="btn" onClick={loadOlder}>
            Ältere Beiträge laden
          </AsyncButton>
        </div>
      )}
    </div>
  );
}
