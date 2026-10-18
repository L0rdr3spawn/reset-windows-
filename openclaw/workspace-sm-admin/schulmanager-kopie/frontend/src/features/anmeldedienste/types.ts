/** Typen der Anmeldedienste (§11.4) – Antworten von `routes/features_sso.py`. */

export type ProviderId = 'microsoft' | 'apple' | 'google' | 'oidc';

/** `GET /auth/sso/providers` */
export interface SsoProvider {
  id: ProviderId | string;
  label: string;
  /** Test-Anbieter (nur Entwicklung) */
  mock: boolean;
  /** Art der Anmeldung: `gis` = Google Identity Services, `apple_js` = Sign in with Apple JS, `microsoft` = offizieller Knopf + Weiterleitung */
  flow?: SsoFlow;
  /** automatische Anmeldung eingeschaltet (One Tap mit Auto-Auswahl bzw. stilles Microsoft-SSO) */
  auto?: boolean;
  /** öffentliche Client-ID (nur `gis` / `apple_js`) */
  client_id?: string;
  /** Apple: Rückkehr-Adresse für `AppleID.auth.init` */
  redirect_uri?: string;
}

export type SsoFlow = 'redirect' | 'microsoft' | 'gis' | 'apple_js';

export interface Identity {
  provider: string;
  label: string;
  email: string | null;
  email_verified: boolean;
  linked: boolean;
  /** vom Admin/Sekretariat vorgemerkt, noch nicht angemeldet */
  pending: boolean;
  mock: boolean;
  /** von der Schule angelegt (Vormerkung) */
  managed: boolean;
  created_at: string | null;
  last_login_at: string | null;
}

export interface Block {
  code: 'link_not_allowed' | 'required' | 'last_method' | string;
  message: string;
}

/** Ein Eintrag in `GET /me/identities` → `providers` */
export interface MyProvider {
  id: string;
  label: string;
  mock: boolean;
  available: boolean;
  required: boolean;
  linked: boolean;
  identity: Identity | null;
  can_link: boolean;
  can_unlink: boolean;
  unlink_block: Block | null;
}

export interface MyIdentities {
  providers: MyProvider[];
  linked: string[];
  available: SsoProvider[];
  required: string[];
  self_link: boolean;
  methods: string[];
}

/** `GET /users/{id}/identities` */
export interface UserIdentities {
  items: Identity[];
  providers: { id: string; label: string; available: boolean; mock: boolean; required: boolean }[];
  required: string[];
  self_link: boolean;
}

export type ProviderStatus = 'active' | 'mock' | 'disabled' | 'missing';

export type ConfigField = 'client_id' | 'client_secret' | 'tenant' | 'hosted_domain' | 'team_id' | 'key_id' | 'private_key' | 'issuer' | 'label' | 'allowed_domains';

/** `GET /sso/providers/config` → `providers[]` */
export interface ProviderSetup {
  id: string;
  label: string;
  default_label: string;
  status: ProviderStatus;
  enabled: boolean;
  configured: boolean;
  db_enabled: boolean;
  mock: boolean;
  /** automatische Anmeldung eingeschaltet */
  auto_signin: boolean;
  /** `one_tap` (Google) / `silent` (Microsoft) / `null` (nicht möglich) */
  auto_kind: 'one_tap' | 'silent' | null;
  /** eigene Adresse ohne Pfad (z. B. https://schule.example:10489) */
  origin: string;
  /** „Autorisierte JavaScript-Quellen“ (Google/Apple), sonst leer */
  js_origins: string[];
  /** Hinweise zur eigenen Adresse (Port, https) */
  warnings: string[];
  /** Adressen, von denen bei aktivem Anbieter Skripte geladen werden */
  script_hosts: string[];
  fields: Partial<Record<ConfigField, string | string[]>>;
  field_names: ConfigField[];
  required: ConfigField[];
  missing: ConfigField[];
  secrets: Partial<Record<'client_secret' | 'private_key', boolean>>;
  env_fields: string[];
  env_vars: Partial<Record<ConfigField, string>>;
  redirect_uri: string;
  updated_at: string | null;
}

export interface SetupOverview {
  providers: ProviderSetup[];
  mock_enabled: boolean;
  production: boolean;
  base_url: string;
  field_labels: Record<string, string>;
}

export interface ProviderUpdate {
  enabled?: boolean;
  auto_signin?: boolean;
  client_id?: string;
  client_secret?: string;
  clear_client_secret?: boolean;
  tenant?: string;
  hosted_domain?: string;
  team_id?: string;
  key_id?: string;
  private_key?: string;
  clear_private_key?: boolean;
  issuer?: string;
  label?: string;
  allowed_domains?: string[];
}

export interface TestResult {
  ok: boolean;
  message: string;
  issuer?: string | null;
  authorization_endpoint?: string | null;
  token_endpoint?: string | null;
  /** Signaturschlüssel (JWKS) abrufbar geprüft */
  jwks_ok?: boolean;
  note?: string | null;
}
