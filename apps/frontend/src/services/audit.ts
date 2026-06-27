import { clientApi } from "./api";

export interface AuditLog {
  id: number;
  actor_id: number | null;
  actor_email: string | null;
  actor_role: string | null;
  method: string;
  path: string;
  action: string;
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

/** Journal d'audit (admin uniquement) — actions mutantes, les plus récentes d'abord. */
export function listAuditLogs(page = 1, size = 50) {
  return clientApi<Page<AuditLog>>(`/audit?page=${page}&size=${size}`);
}
