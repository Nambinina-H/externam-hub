import { clientApi } from "./api";

export interface AuditChange {
  field: string;
  before: string;
  after: string;
}

export interface AuditLog {
  id: number;
  actor_id: number | null;
  actor_email: string | null;
  actor_role: string | null;
  method: string;
  path: string;
  action: string;
  /** Diff champ par champ pour les modifications client/utilisateur. */
  changes: AuditChange[] | null;
  status_code: number;
  request_id: string | null;
  created_at: string;
}

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface AuditFilters {
  page?: number;
  size?: number;
  /** Sous-chaîne d'email d'acteur. */
  actor?: string;
  /** Méthode HTTP exacte (POST, DELETE…). */
  method?: string;
  /** Date ISO (YYYY-MM-DD) incluse. */
  dateFrom?: string;
  dateTo?: string;
}

/** Journal d'audit (admin uniquement) — actions mutantes, les plus récentes d'abord. */
export function listAuditLogs(filters: AuditFilters = {}) {
  const { page = 1, size = 50, actor, method, dateFrom, dateTo } = filters;
  const q = new URLSearchParams({ page: String(page), size: String(size) });
  if (actor) q.set("actor", actor);
  if (method) q.set("method", method);
  if (dateFrom) q.set("date_from", dateFrom);
  if (dateTo) q.set("date_to", dateTo);
  return clientApi<Page<AuditLog>>(`/audit?${q.toString()}`);
}
