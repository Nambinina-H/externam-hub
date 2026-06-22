/** Compte publicitaire Meta (act_…). */
export interface MetaAdAccount {
  id: string;
  account_id: string;
  name: string;
  currency?: string | null;
  account_status?: number | null;
}

/** Campagne Meta d'un compte publicitaire (objectif normalisé en libellé FR). */
export interface MetaCampaign {
  id: string;
  name: string;
  objective: string | null;
  objective_label: string;
  status: string | null;
  effective_status: string | null;
}

/** Portefeuille (business) Meta + ses comptes pub. Un portefeuille = un client. */
export interface MetaPortfolio {
  id: string | null;
  name: string;
  accounts: MetaAdAccount[];
}

/** Réponse de GET /ads/portfolios : lecture depuis la base + date de dernière synchro. */
export interface PortfoliosResponse {
  portfolios: MetaPortfolio[];
  last_synced_at: string | null;
}

interface SyncCounts {
  created: number;
  updated: number;
  removed: number;
}

/** Résultat de POST /ads/portfolios/sync (upsert + soft-remove). */
export interface SyncResult {
  portfolios: SyncCounts;
  accounts: SyncCounts;
  synced_at: string;
}
