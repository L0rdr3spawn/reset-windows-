/** Typen der API-Zugänge (Server: `routes/features_api_access.py`, docs/API-ZUGAENGE.md). */

export type FilterKind = 'classes' | 'teachers' | 'rooms' | 'students' | 'sites';
export type AccessStatus = 'active' | 'expired' | 'revoked';

export type AccessFilters = Partial<Record<FilterKind, string[]>>;

export interface AreaInfo {
  id: string;
  label: string;
  description: string;
  filters: FilterKind[];
  available: boolean;
  write: boolean;
  write_available: boolean;
}

export interface ValueOption {
  id: string;
  name: string;
  class_id?: string;
}

export interface AccessMeta {
  areas: AreaInfo[];
  filters: { id: FilterKind; label: string }[];
  values: Record<FilterKind, ValueOption[] | null>;
  not_offered: { id: string; reason: string }[];
  limits: { default_expires_days: number; max_expires_days: number; default_rate: number; max_rate: number; max_access: number };
  can_manage_all: boolean;
  can_create: boolean;
  docs: { llms: string; openapi: string; scopes: string };
}

export interface AccessItem {
  id: number;
  name: string;
  purpose: string;
  prefix: string;
  status: AccessStatus;
  owner: { id: number; name: string };
  created_at: string | null;
  expires_at: string | null;
  last_used: string | null;
  revoked_at: string | null;
  use_count: number;
  areas: string[];
  write: string[];
  filters: AccessFilters;
  ip_allow: string[];
  rate_limit: number;
  summary?: string[];
}

export interface AccessLogLine {
  at: string | null;
  method: string;
  path: string;
  area: string;
  outcome: string;
  ip: string | null;
}

export interface AccessDetail extends AccessItem {
  log: AccessLogLine[];
  log_total: number;
}

export interface CreatedAccess extends AccessItem {
  token: string;
  examples: string[];
}

export interface AccessDraft {
  name: string;
  purpose: string;
  expires_days: number;
  areas: string[];
  write: string[];
  filters: AccessFilters;
  ip_allow: string[];
  rate_limit: number;
}

export interface Preview {
  can: string[];
  cannot: string[];
  warnings: string[];
  examples: string[];
}
