import type {
  Client,
  ClientCreateInput,
  ClientUpdateInput,
  ImportMapping,
  ImportPreview,
  ImportResult,
} from "@externam/shared";

import { clientApi } from "./api";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export function listClients(page = 1, size = 50) {
  return clientApi<Page<Client>>(`/clients?page=${page}&size=${size}`);
}

export function createClient(input: ClientCreateInput) {
  return clientApi<Client>("/clients", { method: "POST", body: JSON.stringify(input) });
}

export function updateClient(id: number, input: ClientUpdateInput) {
  return clientApi<Client>(`/clients/${id}`, { method: "PATCH", body: JSON.stringify(input) });
}

export function deleteClient(id: number) {
  return clientApi<null>(`/clients/${id}`, { method: "DELETE" });
}

export function importPreview(csv: string) {
  return clientApi<ImportPreview>("/clients/import/preview", { method: "POST", body: JSON.stringify({ csv }) });
}

export function importClients(csv: string, mapping: ImportMapping, autoLink = false) {
  return clientApi<ImportResult>("/clients/import", {
    method: "POST",
    body: JSON.stringify({ csv, mapping, auto_link: autoLink }),
  });
}
