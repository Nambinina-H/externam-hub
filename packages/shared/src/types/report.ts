/** Métriques ads agrégées d'une semaine (miroir de WeeklyMetrics côté backend). */
export interface WeeklyAdsMetrics {
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  ctr: number;
  cpc: number;
}
