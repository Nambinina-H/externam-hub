import type { AuthUser, UserRole } from "@externam/shared";

import { clientApi } from "./api";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface CreateUserInput {
  firstname: string;
  lastname: string;
  email: string;
  password: string;
  role: UserRole;
}

export function listUsers(page = 1, size = 50) {
  return clientApi<Page<AuthUser>>(`/users?page=${page}&size=${size}`);
}

export function createUser(input: CreateUserInput) {
  return clientApi<AuthUser>("/users", { method: "POST", body: JSON.stringify(input) });
}

export interface UpdateUserInput {
  firstname?: string;
  lastname?: string;
  email?: string;
  role?: UserRole;
  password?: string;
}

export function updateUser(id: number, input: UpdateUserInput) {
  return clientApi<AuthUser>(`/users/${id}`, { method: "PATCH", body: JSON.stringify(input) });
}

export function deleteUser(id: number) {
  return clientApi<null>(`/users/${id}`, { method: "DELETE" });
}
