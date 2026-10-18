/**
 * Menü-Badge der Nachschreibtermine: Lehrkräfte = Termine, die noch festzulegen sind; Klassenleitung/Sekretariat und
 * Familien = fehlende Atteste (klein, wird beim App-Start geladen – siehe module.tsx).
 */
import { useEffect } from 'react';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { can, isFamily } from '../../lib/permissions';
import { setBadge } from '../registry';
import { makeupsApi } from './api';

export const MAKEUP_BADGE = 'nachschreiben';

export function MakeupBadge() {
  const user = useUser();
  const enabled = can(user, ['exam.edit', 'student_absence.read']) && user.role !== 'admin';
  const q = useApi((signal) => makeupsApi.summary(signal), [enabled], { enabled, live: ['makeups', 'student_absences', 'student_documents', 'exams'] });
  useEffect(() => {
    const s = q.data;
    setBadge(MAKEUP_BADGE, enabled && s ? (isFamily(user) ? s.attest_missing : s.open + s.attest_missing) : 0);
  }, [enabled, q.data, user]);
  useEffect(() => () => setBadge(MAKEUP_BADGE, 0), []);
  return null;
}
