import { ExternalLink } from "lucide-react";

import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

// Mail client complet du template (sidebar dossiers + inbox + lecture), embarqué via /mail
// pour avoir sa propre mise en page sans conflit avec la sidebar du dashboard.
export default function Page() {
  return (
    <div className="flex h-[calc(100vh-8rem)] min-h-[34rem] flex-col gap-2">
      <div className="flex items-center justify-between gap-3">
        <h1 className="font-semibold text-2xl">Mail</h1>
        <Link
          href="/mail"
          target="_blank"
          rel="noreferrer"
          prefetch={false}
          aria-label="Ouvrir en plein écran"
          className={buttonVariants({ variant: "ghost", size: "icon-sm" })}
        >
          <ExternalLink />
        </Link>
      </div>
      <iframe src="/mail" title="Mail" className="min-h-0 flex-1 rounded-xl border bg-background" />
    </div>
  );
}
