import type { UserRole } from "@externam/shared";

/** Libellés FR des rôles, pour l'affichage (badge user). */
export const ROLE_LABELS: Record<UserRole, string> = {
  SUPERADMIN: "Super admin",
  ADMIN: "Admin",
  META_ADS_EXPERT: "Expert Meta Ads",
  USER: "Utilisateur",
};
