import { clientApi } from "./api";

export interface ReportPreview {
  html: string;
  subject: string;
  start: string;
  end: string;
}

export interface SendReportResult {
  status: string;
  client_id: number;
  recipients: string[];
}

export interface SendDayResult {
  sent: number;
  /** Envois en échec (SMTP refusé, client sans email…). */
  failed: number;
  /** Nombre de clients concernés aujourd'hui. */
  total: number;
  weekday: number;
}

/** Rend le HTML du rapport hebdo d'un client (aperçu, sans envoi). */
export function previewReport(id: number) {
  return clientApi<ReportPreview>(`/clients/${id}/report-preview`);
}

/** Envoie le rapport d'un client aux emails choisis. */
export function sendReport(id: number, to: string[]) {
  return clientApi<SendReportResult>(`/clients/${id}/send-report`, {
    method: "POST",
    body: JSON.stringify({ to }),
  });
}

/** Envoie les rapports de tous les clients actifs dont le jour d'envoi = aujourd'hui. */
export function sendDayReports() {
  return clientApi<SendDayResult>("/reports/send-day", { method: "POST" });
}

// --- Modèles d'email ---

export interface EmailTemplate {
  subject: string;
  intro: string;
  closing: string;
  /** Bloc signature libre (le séparateur « -- » est ajouté au rendu). */
  signature: string;
  /** true = surcharge propre au client ; false = hérité du modèle de base. */
  is_override: boolean;
}

export interface TemplateInput {
  subject: string;
  intro: string;
  closing: string;
  signature: string;
}

export interface TemplatePreview {
  html: string;
  subject: string;
}

export interface Placeholder {
  key: string;
  label: string;
}

export function getTemplatePlaceholders() {
  return clientApi<Placeholder[]>("/reports/template/placeholders");
}

export function getBaseTemplate() {
  return clientApi<EmailTemplate>("/reports/template");
}

export function updateBaseTemplate(input: TemplateInput) {
  return clientApi<EmailTemplate>("/reports/template", { method: "PUT", body: JSON.stringify(input) });
}

export function listTemplateOverrides() {
  return clientApi<number[]>("/reports/template/overrides");
}

export function getClientTemplate(id: number) {
  return clientApi<EmailTemplate>(`/reports/template/client/${id}`);
}

export function upsertClientTemplate(id: number, input: TemplateInput) {
  return clientApi<EmailTemplate>(`/reports/template/client/${id}`, { method: "PUT", body: JSON.stringify(input) });
}

export function deleteClientTemplate(id: number) {
  return clientApi<{ status: string; client_id: number }>(`/reports/template/client/${id}`, { method: "DELETE" });
}

/** Aperçu en direct d'un modèle (données d'exemple, instantané). */
export function previewTemplate(input: TemplateInput & { client_id?: number | null }) {
  return clientApi<TemplatePreview>("/reports/template/preview", { method: "POST", body: JSON.stringify(input) });
}
