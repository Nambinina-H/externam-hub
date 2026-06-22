import type { UserRole } from "@externam/shared";
import {
  Banknote,
  Clapperboard,
  Fingerprint,
  type LucideIcon,
  Mail,
  Megaphone,
  ScrollText,
  Settings,
  Shield,
  Users,
} from "lucide-react";

export interface NavSubItem {
  title: string;
  url: string;
  icon?: LucideIcon;
  comingSoon?: boolean;
  newTab?: boolean;
  isNew?: boolean;
}

export interface NavMainItem {
  title: string;
  url: string;
  icon?: LucideIcon;
  subItems?: NavSubItem[];
  comingSoon?: boolean;
  newTab?: boolean;
  isNew?: boolean;
}

export interface NavGroup {
  id: number;
  label?: string;
  items: NavMainItem[];
}

/** Un « espace » = un module produit. Ce que l'utilisateur voit dépend de son rôle. */
export interface NavSpace {
  id: string;
  label: string;
  icon: LucideIcon;
  roles: UserRole[];
  groups: NavGroup[];
}

// ADMIN reste un alias legacy de SUPERADMIN (accès total).
const FULL_ACCESS: UserRole[] = ["SUPERADMIN", "ADMIN"];

export const spaces: NavSpace[] = [
  {
    id: "meta-ads",
    label: "Meta Ads",
    icon: Megaphone,
    roles: [...FULL_ACCESS, "META_ADS_EXPERT"],
    groups: [
      {
        id: 1,
        label: "Meta Ads",
        items: [
          { title: "Clients", url: "/dashboard/clients", icon: Users },
          { title: "Portefeuille business", url: "/dashboard/ads/meta/accounts", icon: Banknote },
          { title: "Envoi de rapports", url: "/dashboard/mail", icon: Mail },
          { title: "Création campagnes", url: "/dashboard/ads/meta/campaigns", icon: Megaphone, comingSoon: true },
          { title: "Paramètres", url: "/dashboard/settings", icon: Settings },
        ],
      },
    ],
  },
  {
    id: "scenariste",
    label: "Scénariste",
    icon: Clapperboard,
    roles: [...FULL_ACCESS, "SCENARISTE"],
    groups: [
      {
        id: 1,
        label: "Scénarios",
        items: [{ title: "Scénarios", url: "/dashboard/scenarios", icon: ScrollText }],
      },
    ],
  },
  {
    id: "administration",
    label: "Administration",
    icon: Shield,
    roles: FULL_ACCESS,
    groups: [
      {
        id: 1,
        label: "Équipe",
        items: [{ title: "Utilisateurs", url: "/dashboard/users", icon: Fingerprint }],
      },
    ],
  },
];

/** Espaces accessibles à un rôle donné. */
export function spacesForRole(role: UserRole | undefined): NavSpace[] {
  if (!role) return [];
  return spaces.filter((space) => space.roles.includes(role));
}

/** Espace auquel appartient une URL (pour suivre l'espace actif + le garde-fou de route). */
export function spaceForPath(path: string): NavSpace | undefined {
  const matches = (url: string) => path === url || path.startsWith(`${url}/`);
  return spaces.find((space) =>
    space.groups.some((group) =>
      group.items.some((item) => matches(item.url) || item.subItems?.some((sub) => matches(sub.url))),
    ),
  );
}

/** Page d'accueil après connexion, selon le rôle. */
export function landingForRole(role: UserRole | undefined): string {
  if (role === "SUPERADMIN" || role === "ADMIN") return "/dashboard/users";
  if (role === "SCENARISTE") return "/dashboard/scenarios";
  return "/dashboard/clients";
}
