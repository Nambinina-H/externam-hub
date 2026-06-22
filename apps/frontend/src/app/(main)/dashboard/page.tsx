"use client";

import { useEffect } from "react";

import { useRouter } from "next/navigation";

import { landingForRole } from "@/navigation/sidebar/sidebar-items";
import { useAuthStore } from "@/stores/auth-store";

/** Entrée neutre après connexion : redirige vers l'accueil selon le rôle (sans page « dashboard »). */
export default function DashboardIndex() {
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
