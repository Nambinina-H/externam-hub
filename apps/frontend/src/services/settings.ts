import { clientApi } from "./api";

export interface EmailSettings {
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  from_email: string;
  /** Nom d'expéditeur (nom et prénom), réutilisable comme variable {{expediteur}}. */
  from_name: string;
  /** Le mot de passe n'est jamais renvoyé ; on sait seulement s'il est défini. */
  password_set: boolean;
  source: "db" | "env";
}

export interface EmailSettingsUpdate {
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  from_email: string;
  from_name: string;
  /** Vide/omis = conserver le mot de passe déjà enregistré. */
  smtp_password?: string;
}

export function getEmailSettings() {
  return clientApi<EmailSettings>("/settings/email");
}

export function updateEmailSettings(payload: EmailSettingsUpdate) {
  return clientApi<EmailSettings>("/settings/email", { method: "PUT", body: JSON.stringify(payload) });
}

/** Envoie un email de test à l'adresse choisie (jamais aux clients de la base). */
export function testEmail(to: string) {
  return clientApi<{ status: string; to: string }>("/settings/email/test", {
    method: "POST",
    body: JSON.stringify({ to }),
  });
}
