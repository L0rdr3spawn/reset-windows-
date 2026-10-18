/**
 * Menü-Badge der Formulare: Eingang = Einreichungen, die auf die eigene Entscheidung warten; Familien = erwartete
 * Rückmeldungen (Einwilligungen/Fristen), die noch fehlen (klein, wird beim App-Start geladen – siehe module.tsx).
 */
import { useEffect } from 'react';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { can } from '../../lib/permissions';
import { setBadge } from '../registry';
import { formsApi } from './api';

export const FORMS_BADGE = 'formulare';

export function FormsBadge() {
  const user = useUser();
  const enabled = can(user, ['forms.submit', 'forms.inbox']);
  const q = useApi((signal) => formsApi.summary(signal), [enabled], { enabled, live: ['forms'] });
  useEffect(() => {
    const s = q.data;
    setBadge(FORMS_BADGE, enabled && s ? s.to_decide + s.to_fill : 0);
  }, [enabled, q.data]);
  useEffect(() => () => setBadge(FORMS_BADGE, 0), []);
  return null;
}
