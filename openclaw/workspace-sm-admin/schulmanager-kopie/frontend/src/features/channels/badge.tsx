/** Unsichtbare Hintergrund-Komponente: Zahl „neue Inhalte“ (Material + Beiträge) am Menüeintrag „Kursräume“. */
import { useEffect } from 'react';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { can } from '../../lib/permissions';
import { setBadge } from '../registry';
import { channelsApi } from './api';
import { badgeCount } from './logic';

export const NEW_BADGE = 'kursraeume.neu';

export function ChannelsBadge() {
  const user = useUser();
  const enabled = can(user, ['channels.use', 'channels.manage']);
  const { data } = useApi((signal) => channelsApi.list({}, signal), [user.id], { enabled, live: ['channels'] });
  useEffect(() => setBadge(NEW_BADGE, enabled && data ? badgeCount(data.channels) : 0), [enabled, data]);
  useEffect(() => () => setBadge(NEW_BADGE, 0), []);
  return null;
}
