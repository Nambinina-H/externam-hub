/** Jour de la semaine, aligné backend : 0 = lundi … 6 = dimanche. */
export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export interface Client {
  id: number;
  name: string;
  company?: string | null;
  contact_name?: string | null;
  phone?: string | null;
  /** Emails destinataires (on choisit lequel à l'envoi du rapport). */
  emails: string[];
  /** Portefeuille (business) Meta : le rapport agrège tous ses comptes pub. */
  meta_business_id?: string | null;
  meta_ad_account_id?: string | null;
  /** Campagnes Meta gérées par l'agence (allowlist) = incluses dans le rapport. */
  managed_campaign_ids: string[];
  report_day: DayOfWeek;
  is_active: boolean;
  last_report_sent_at?: string | null;
  created_at: string;
}

export interface ClientCreateInput {
  name: string;
  company?: string | null;
  contact_name?: string | null;
  phone?: string | null;
  emails: string[];
  meta_business_id?: string | null;
  meta_ad_account_id?: string | null;
  managed_campaign_ids?: string[];
  report_day: DayOfWeek;
  is_active?: boolean;
}

export type ClientUpdateInput = Partial<ClientCreateInput>;

/** Étapes d'import CSV : aperçu des en-têtes + mapping colonnes → champs. */
export interface ImportPreview {
  headers: string[];
  sample: Record<string, string>[];
  count: number;
}

export interface ImportMapping {
  name?: string | null;
  company?: string | null;
  emails?: string | null;
  contact_name?: string | null;
  phone?: string | null;
}

export interface ImportResult {
  created: number;
  updated: number;
  skipped: number;
  /** Présent si l'auto-liaison aux portefeuilles a été demandée : nombre de clients liés. */
  linked?: number;
}
