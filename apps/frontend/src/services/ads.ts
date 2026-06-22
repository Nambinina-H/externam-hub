import type { MetaCampaign, PortfoliosResponse, SyncResult } from "@externam/shared";

import { clientApi } from "./api";

/** Portefeuilles persistés (lecture base, rapide) — via GET /api/ads/portfolios. */
export function listPortfolios() {
  return clientApi<PortfoliosResponse>("/ads/portfolios");
}

/** Campagnes d'un compte publicitaire (live Meta si token, sinon fictives) — GET /api/ads/accounts/{id}/campaigns. */
export function listAccountCampaigns(accountId: string) {
  return clientApi<MetaCampaign[]>(`/ads/accounts/${encodeURIComponent(accountId)}/campaigns`);
}

/** Rafraîchit la base depuis Meta (upsert + soft-remove) — via POST /api/ads/portfolios/sync. */
export function syncPortfolios() {
  return clientApi<SyncResult>("/ads/portfolios/sync", { method: "POST" });
}
