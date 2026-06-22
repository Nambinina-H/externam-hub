"use client";

import { MailSentbox } from "./mail-sentbox";
import { MailTemplates } from "./mail-templates";
import { useMailView } from "./use-mail-view";

/** Bascule entre la boîte d'envoi et l'éditeur de modèles, piloté par la sidebar mail. */
export function MailWorkspace() {
  const view = useMailView((s) => s.view);
  return view === "templates" ? <MailTemplates /> : <MailSentbox />;
}
