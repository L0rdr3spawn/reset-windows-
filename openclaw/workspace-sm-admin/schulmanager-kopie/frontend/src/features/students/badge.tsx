/**
 * Menü-Badges der Schüler-Selbstbedienung (klein, wird beim App-Start geladen – siehe module.tsx):
 * Personal: offene Dokumente + fehlende Atteste (`schueler.dokumente`), Familien: fehlende Atteste (`schueler.atteste`).
 */
import { useEffect } from 'react';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { can, isFamily } from '../../lib/permissions';
import { setBadge } from '../registry';
import { documentsApi } from './api';
import { badgeCount } from './logic';

export const DOCS_BADGE = 'schueler.dokumente';
export const FAMILY_BADGE = 'schueler.atteste';

export function DocumentsBadge() {
  const user = useUser();
  const family = isFamily(user);
  const enabled = can(user, 'student_documents.read');
  const q = useApi((signal) => documentsApi.summary(signal), [enabled], { enabled, live: ['student_documents', 'student_absences'] });
  useEffect(() => {
    const n = enabled ? badgeCount(q.data, family) : 0;
    setBadge(family ? FAMILY_BADGE : DOCS_BADGE, n);
  }, [enabled, family, q.data]);
  useEffect(
    () => () => {
      setBadge(DOCS_BADGE, 0);
      setBadge(FAMILY_BADGE, 0);
    },
    [],
  );
  return null;
}
