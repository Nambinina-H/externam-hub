"use client";

import { useEffect } from "react";

import { useRouter } from "next/navigation";

import { landingForRole } from "@/navigation/sidebar/sidebar-items";
import { useAuthStore } from "@/stores/auth-store";

/** Toute URL /dashboard/* inconnue (ancien lien, favori, ex. /dashboard/default) renvoie
 *  vers l'accueil du rôle plutôt que vers un cul-de-sac « page introuvable ». */
export default function DashboardNotFound() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const fetchMe = useAuthStore((s) => s.fetchMe);

  useEffect(() => {
    if (!user) void fetchMe();
  }, [user, fetchMe]);

  useEffect(() => {
    if (user) router.replace(landingForRole(user.role));
  }, [user, router]);

  return null;
}
