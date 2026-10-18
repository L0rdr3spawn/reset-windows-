/**
 * Benachrichtigungszentrale (Glocke): `/notifications` (schulmanager/server/routes/features_notifications.py,
 * docs/BENACHRICHTIGUNGEN.md). Jedes Konto sieht nur die eigenen.
 */
import { http } from '../../api/client';

export type NotificationMode = 'aus' | 'app' | 'mail';

export interface AppNotification {
  id: number;
  kind: string;
  kind_label: string;
  title: string;
  body: string;
  link: string;
  read: boolean;
  created_at: string | null;
  student_id: string | null;
  /** Eltern: Name des Kindes, um das es geht */
  child?: string;
}

export interface NotificationList {
  items: AppNotification[];
  unread: number;
  more: boolean;
}

export interface NotificationKind {
  kind: string;
  label: string;
  group: string;
  help: string;
  default: NotificationMode;
  mode: NotificationMode;
  school_mode: NotificationMode;
  locked: boolean;
  own: boolean;
}

export interface NotificationSettings {
  kinds: NotificationKind[];
  modes: { value: NotificationMode; label: string }[];
  digest: boolean;
  quiet_enabled: boolean;
  quiet_from: string;
  quiet_to: string;
  mail_available: boolean;
  retention_days: number;
}

export interface SchoolKind {
  kind: string;
  label: string;
  group: string;
  help: string;
  default: NotificationMode;
  mode: NotificationMode;
  locked: boolean;
}

export interface SchoolNotificationSettings {
  kinds: SchoolKind[];
  modes: { value: NotificationMode; label: string }[];
  retention_days: number;
  retention_min: number;
  retention_max: number;
  mail_available: boolean;
}

export interface SettingsPatch {
  modes?: Record<string, NotificationMode>;
  digest?: boolean;
  quiet_enabled?: boolean;
  quiet_from?: string;
  quiet_to?: string;
}

export const notificationsApi = {
  list: (params: { unread?: boolean; limit?: number; before?: number } = {}, signal?: AbortSignal) =>
    http.get<NotificationList>('/notifications', { unread: params.unread ? 1 : undefined, limit: params.limit, before: params.before }, { signal }),
  count: (signal?: AbortSignal) => http.get<{ unread: number }>('/notifications/count', undefined, { signal }),
  markRead: (ids: number[] | null, read = true) => http.post<{ changed: number; unread: number }>('/notifications/read', { ids, read }),
  remove: (id: number) => http.del<{ unread: number }>(`/notifications/${id}`),
  clearRead: () => http.del<{ deleted: number; unread: number }>('/notifications?read=1'),
  settings: (signal?: AbortSignal) => http.get<NotificationSettings>('/notifications/settings', undefined, { signal }),
  saveSettings: (patch: SettingsPatch) => http.put<NotificationSettings>('/notifications/settings', patch),
  school: (signal?: AbortSignal) => http.get<SchoolNotificationSettings>('/notifications/school', undefined, { signal }),
  saveSchool: (rules: Record<string, { mode: NotificationMode; locked: boolean }>, retention_days?: number) =>
    http.put<SchoolNotificationSettings>('/notifications/school', { rules, retention_days }),
};
