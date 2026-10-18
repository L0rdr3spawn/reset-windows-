/**
 * Menü-Badge „Planvorschläge“ (bewusst klein: wird beim App-Start geladen, siehe module.tsx) und Live-Hinweis, wenn ein
 * neues Vorschlagspaket zur Entscheidung vorliegt.
 */
import { useEffect, useRef } from 'react';
import { useUser } from '../../context/AuthContext';
import { useOptionalToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { can } from '../../lib/permissions';
import { setBadge } from '../registry';
import { proposalsApi, type ProposalSummary } from './api';

export const PROPOSALS_BADGE = 'planpruefung.offen';
export const PROPOSAL_RIGHTS = ['timetable.generate', 'timetable.edit', 'settings.edit'] as const;

export function useProposalSummary(enabled: boolean) {
  return useApi<ProposalSummary>((signal) => proposalsApi.summary(signal), [enabled], { enabled, live: ['proposals'] });
}

export function ProposalBadge() {
  const user = useUser();
  const toast = useOptionalToast();
  const enabled = can(user, [...PROPOSAL_RIGHTS]);
  const q = useProposalSummary(enabled);
  const last = useRef<number | null>(null);
  useEffect(() => {
    const open = enabled ? (q.data?.open ?? 0) : 0;
    setBadge(PROPOSALS_BADGE, open);
    if (q.data && enabled) {
      if (last.current !== null && open > last.current) toast?.info('Neuer Vorschlag für den Stundenplan – unter „Planvorschläge“ entscheiden Sie.');
      last.current = open;
    }
  }, [enabled, q.data, toast]);
  useEffect(() => () => setBadge(PROPOSALS_BADGE, 0), []);
  return null;
}
