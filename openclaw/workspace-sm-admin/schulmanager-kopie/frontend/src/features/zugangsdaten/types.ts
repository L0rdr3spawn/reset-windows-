/**
 * Typen der Zugangsbriefe (§11.3) – Spiegel von `schulmanager/server/routes/features_letters.py`.
 * Passwörter kommen nie über diese Schnittstellen, nur in den PDFs.
 */

/** Verweis auf einen Brief-Stapel (Antwort von Anlegen/Zurücksetzen) */
export interface LetterBatchRef {
  id: string;
  /** ISO-Zeitpunkt (UTC, mit „Z“) */
  expires_at: string;
  count?: number;
}

export interface BatchChild {
  student_id: string;
  name: string;
  class_id: string | null;
}

export interface BatchEntry {
  user_id: number;
  username: string;
  display_name: string;
  role: string;
  class_id: string | null;
  class_name: string | null;
  student_id: string | null;
  /** volljährige Schülerin/volljähriger Schüler: Brief nur an die eigene Adresse */
  adult?: boolean;
  children: BatchChild[];
  /** Konto existiert noch */
  exists: boolean;
  has_email: boolean;
  /** verknüpfte Elternkonten (nur bei Schüler/innen) */
  parents: number;
  parents_with_email: number;
  /** Startpasswort wird gedruckt (Richtlinie erlaubt Passwort oder Ersteinrichtung nötig) */
  password_printed: boolean;
  /** nur Anbieter-Anmeldung erlaubt: Anbieter-Namen */
  login_methods: string[];
  /** Pflicht-Verknüpfungen (Anbieter-Namen) */
  required_links: string[];
  filename: string;
  title: string;
}

export interface BatchInfo {
  id: string;
  title: string;
  count: number;
  created_at: string;
  expires_at: string;
  /** Sekunden bis zum Ablauf (Serverzeit beim Abruf) */
  expires_in: number;
  created_by: { id: number; name: string } | null;
  login_url: string;
  email_available: boolean;
  entries: BatchEntry[];
}

export interface BatchCreateBody {
  user_ids?: number[];
  student_ids?: string[];
  /** auch die Elternkonten der Schüler/innen */
  parents?: boolean;
  /** fehlende Konten anlegen */
  create_missing?: boolean;
}

export interface BatchCreateResult extends LetterBatchRef {
  reset: number;
  created: number;
  title: string;
}

/** `student` = an das Konto selbst, `parents` = an die Eltern (Elternbriefe: an das Elternkonto), `both` = beides */
export type SendTarget = 'student' | 'parents' | 'both';

export interface SendRow {
  user_id: number;
  display_name: string;
  role: string;
  recipients?: string[];
  failed?: string[];
}

export interface SendResult {
  sent: SendRow[];
  no_address: SendRow[];
  unavailable: SendRow[];
  email_available?: boolean;
}

// ---------------------------------------------------------------------------------------------- Passwörter

export interface PasswordInfo {
  user_id: number;
  /** das Passwort ist noch das Startpasswort (mit Frist) */
  initial_pending: boolean;
  initial_expires_at: string | null;
  initial_expired: boolean;
  must_change_password: boolean;
}

export interface PasswordResult {
  user_id: number;
  mode: 'new' | 'set';
  must_change_password: boolean;
  /** nur bei `new`: das neue Einmalpasswort – wird vom Server genau einmal geliefert */
  temp_password?: string;
  letter_batch?: LetterBatchRef | null;
}

export interface ClassAccount {
  user_id: number;
  username: string;
  display_name: string;
  role: string;
  active: boolean;
  must_change_password: boolean;
  last_login: string | null;
  has_email: boolean;
  has_initial: boolean;
  initial_expires_at?: string | null;
  can_reset: boolean;
}

export interface ClassAccountsStudent {
  student_id: string;
  name: string;
  birth_date: string | null;
  account: ClassAccount | null;
  parents: ClassAccount[];
}

export interface ClassAccounts {
  class_id: string;
  /** darf Konten verwalten (users.manage für Schüler/innen) */
  can_manage: boolean;
  students: ClassAccountsStudent[];
}
