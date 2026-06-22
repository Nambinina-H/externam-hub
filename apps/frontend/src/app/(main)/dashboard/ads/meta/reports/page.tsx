export default function MetaAdsReportsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-semibold text-2xl">Rapports hebdomadaires</h1>
        <p className="text-muted-foreground text-sm">
          Publication hebdomadaire des statistiques de chaque campagne Meta Ads.
        </p>
      </div>
      <div className="rounded-xl border border-dashed p-10 text-center text-muted-foreground">
        À venir : stats par campagne (dépenses, impressions, clics, conversions) et envoi automatique du rapport hebdo.
      </div>
    </div>
  );
}
