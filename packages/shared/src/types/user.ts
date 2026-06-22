export type UserRole = "USER" | "ADMIN" | "SUPERADMIN" | "META_ADS_EXPERT";

export interface AuthUser {
  id: number;
  firstname: string;
  lastname: string;
  email: string;
  company?: string | null;
  phone_number?: string | null;
  role: UserRole;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
