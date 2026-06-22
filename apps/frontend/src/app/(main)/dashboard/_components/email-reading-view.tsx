"use client";

import type { ReactNode } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { getInitials } from "@/lib/utils";

interface Props {
  subject: string;
  date?: string;
  fromName: string;
  fromEmail?: string;
  /** Destinataire(s) : texte simple ou cases à cocher interactives. */
  to: ReactNode;
  /** Corps HTML de l'email (rendu fidèle dans un iframe). */
  html: string;
  loading?: boolean;
  /** Barre d'action optionnelle en bas (ex. bouton Envoyer). */
  footer?: ReactNode;
}

/** Rendu « lecture d'email » (objet + expéditeur/destinataire + corps), façon mail client. */
export function EmailReadingView({ subject, date, fromName, fromEmail, to, html, loading, footer }: Props) {
  return (
    <div className="flex h-full min-h-0 flex-col gap-3 px-4 py-3">
      <div className="space-y-1.5">
        <div className="font-medium leading-snug">{subject || "(sans objet)"}</div>
        {date ? <div className="text-muted-foreground text-xs leading-none">{date}</div> : null}
      </div>

      <Separator />

      <div className="flex gap-2.5">
        <Avatar className="size-9 after:rounded-sm">
          <AvatarFallback className="rounded-sm bg-background">{getInitials(fromName)}</AvatarFallback>
        </Avatar>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-sm">{fromName}</span>
            {fromEmail ? (
              <>
                <Separator className="h-3 data-vertical:self-center" orientation="vertical" />
                <span className="text-muted-foreground text-xs">{fromEmail}</span>
              </>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-muted-foreground text-xs">
            <span>À :</span>
            {to}
          </div>
        </div>
      </div>

      <Separator />

      <div className="min-h-0 flex-1 overflow-hidden rounded-lg border bg-[#f4f4f7]">
        {loading ? (
          <Skeleton className="h-full w-full" />
        ) : html ? (
          <iframe title="Aperçu de l'email" srcDoc={html} sandbox="" className="h-full w-full" />
        ) : (
          <div className="grid h-full place-items-center text-muted-foreground text-sm">Aperçu indisponible.</div>
        )}
      </div>

      {footer}
    </div>
  );
}
