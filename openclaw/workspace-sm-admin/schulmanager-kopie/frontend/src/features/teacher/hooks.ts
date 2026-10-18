/**
 * React-Hooks der Lehrer-Selbstverwaltung / des Lehrer-Scopes.
 */
import { useApi } from '../../hooks/useApi';
import { timetableScopeApi } from './api';
import type { AllowedRefs } from './types';

/**
 * Freigegebene Pläne des Kontos (`GET /timetable/allowed`). Bei `enabled = false` (z. B. Planung mit Vollzugriff)
 * wird nichts geladen und `allowed` bleibt `null` (= keine Einschränkung im Frontend).
 */
export function useAllowedRefs(enabled: boolean): { allowed: AllowedRefs | null; loading: boolean; error: unknown } {
  const q = useApi<AllowedRefs>(() => timetableScopeApi.allowed(), [], {
    enabled,
    live: ['courses', 'classes', 'students', 'teachers'],
  });
  return { allowed: enabled ? (q.data ?? null) : null, loading: enabled && q.loading && !q.data, error: q.error };
}
