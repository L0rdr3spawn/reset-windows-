/**
 * Menü-Badge „Anträge von Lehrkräften“ (bewusst klein: wird beim App-Start geladen, siehe module.tsx).
 */
import { useEffect } from 'react';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { can } from '../../lib/permissions';
import { setBadge } from '../registry';
import { teacherRequestsApi } from './api';
import type { RequestsSummary } from './types';

/** Schlüssel des Menü-Badges „Anträge von Lehrkräften“. */
export const REQUESTS_BADGE = 'lehrkraft.antraege';

/** Hält die Zahl offener Anträge am Menü aktuell (Live-Ereignis `teacher_requests`). */
export function RequestsBadge() {
  const user = useUser();
  const enabled = can(user, 'teacher_requests.review');
  const q = useApi<RequestsSummary>(() => teacherRequestsApi.summary(), [enabled], { enabled, live: ['teacher_requests'] });
  useEffect(() => {
    setBadge(REQUESTS_BADGE, enabled ? (q.data?.open ?? 0) : 0);
  }, [enabled, q.data]);
  useEffect(() => () => setBadge(REQUESTS_BADGE, 0), []);
  return null;
}
