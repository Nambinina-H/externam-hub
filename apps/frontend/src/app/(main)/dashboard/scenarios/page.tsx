import { Clapperboard } from "lucide-react";

export default function ScenariosPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-semibold text-2xl">Scénarios</h1>
        <p className="text-muted-foreground text-sm">
          Espace Scénariste — l&apos;écriture et la gestion des scripts arriveront prochainement.
        </p>
      </div>
      <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-12 text-center">
        <Clapperboard className="size-10 text-muted-foreground" />
        <p className="text-muted-foreground text-sm">Cette section sera bientôt disponible.</p>
      </div>
    </div>
  );
}
