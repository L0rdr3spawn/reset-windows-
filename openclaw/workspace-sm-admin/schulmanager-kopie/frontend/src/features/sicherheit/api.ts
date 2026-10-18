/** Endpunkte der Sicherheits-Einstellungen und der Anmelde-Drosselung (Bericht S-04/S-06/S-17). */
import { http } from '../../api/client';
import type { LocksResponse, SecuritySettings, SettingsPatch } from './types';

export const securityApi = {
  settings: (signal?: AbortSignal) => http.get<SecuritySettings>('/security/settings', undefined, { signal }),
  save: (patch: SettingsPatch) => http.put<SecuritySettings>('/security/settings', patch),
  locks: (signal?: AbortSignal) => http.get<LocksResponse>('/login-locks', undefined, { signal }),
  unlockUser: (username: string) => http.del<{ cleared: number }>(`/login-locks?username=${encodeURIComponent(username)}`),
  unlockIp: (ip: string) => http.del<{ cleared: number }>(`/login-locks?ip=${encodeURIComponent(ip)}`),
};
