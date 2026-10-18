export type TwofaMode = 'off' | 'recommended' | 'required';

export interface SecuritySettings {
  twofa_mode: TwofaMode;
  twofa_roles: string[];
  staff_idle_minutes: number;
  initial_password_days: number;
  /** durch `SM_REQUIRE_2FA_ROLES` fest vorgegebene Pflicht-Rollen */
  env_required_roles: string[];
  role_choices: { id: string; label: string }[];
  idle_range: [number, number];
  password_days_range: [number, number];
  student_idle_minutes: number;
  lock: { max_failures: number; max_failures_ip: number; base_delay_seconds: number; max_delay_seconds: number };
}

export type SettingsPatch = Partial<Pick<SecuritySettings, 'twofa_mode' | 'twofa_roles' | 'staff_idle_minutes' | 'initial_password_days'>>;

export interface LoginLock {
  kind: 'user' | 'ip' | 'account';
  username: string | null;
  ip: string | null;
  failures: number;
  /** Sekunden bis zum nächsten erlaubten Versuch */
  wait: number;
  last_failure: string | null;
  role?: string | null;
  role_label?: string | null;
}

export interface LocksResponse {
  locks: LoginLock[];
}
