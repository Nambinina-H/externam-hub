"use client";

import { useEffect, useMemo, useState } from "react";

import { usePathname, useRouter } from "next/navigation";

import { useShallow } from "zustand/react/shallow";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { APP_CONFIG } from "@/config/app-config";
import { landingForRole, spaceForPath, spacesForRole } from "@/navigation/sidebar/sidebar-items";
import { useAuthStore } from "@/stores/auth-store";
import { usePreferencesStore } from "@/stores/preferences/preferences-provider";

import { EspaceSwitcher } from "./espace-switcher";
import { NavMain } from "./nav-main";
import { NavUser } from "./nav-user";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { sidebarCollapsible, isSynced } = usePreferencesStore(
    useShallow((s) => ({ sidebarCollapsible: s.sidebarCollapsible, isSynced: s.isSynced })),
  );
  const collapsible = isSynced ? sidebarCollapsible : props.collapsible;

  const user = useAuthStore((s) => s.user);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!user) void fetchMe();
  }, [user, fetchMe]);

  const accessibleSpaces = useMemo(() => spacesForRole(user?.role), [user?.role]);
  const [activeId, setActiveId] = useState<string | null>(null);

  // Espace actif : celui de l'URL si autorisé, sinon le choix manuel, sinon le 1er accessible.
  const activeSpace = useMemo(() => {
    const fromPath = spaceForPath(pathname);
    if (fromPath && accessibleSpaces.some((s) => s.id === fromPath.id)) return fromPath;
    return accessibleSpaces.find((s) => s.id === activeId) ?? accessibleSpaces[0];
  }, [pathname, accessibleSpaces, activeId]);

  // Garde-fou : si l'URL appartient à un espace interdit pour ce rôle, on redirige vers l'accueil autorisé.
  useEffect(() => {
    if (!user) return;
    const target = spaceForPath(pathname);
    if (target && !accessibleSpaces.some((s) => s.id === target.id)) {
      router.replace(accessibleSpaces[0]?.groups[0]?.items[0]?.url ?? landingForRole(user.role));
    }
  }, [user, pathname, accessibleSpaces, router]);

  function onSelectSpace(spaceId: string) {
    const space = accessibleSpaces.find((s) => s.id === spaceId);
    if (!space) return;
    setActiveId(space.id);
    router.push(space.groups[0]?.items[0]?.url ?? landingForRole(user?.role));
  }

  return (
    <Sidebar {...props} variant="sidebar" collapsible={collapsible}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <div className="flex h-8 items-center px-2 font-semibold text-base">{APP_CONFIG.name}</div>
          </SidebarMenuItem>
        </SidebarMenu>
        <EspaceSwitcher spaces={accessibleSpaces} active={activeSpace} onSelect={(space) => onSelectSpace(space.id)} />
      </SidebarHeader>
      <SidebarContent>{activeSpace ? <NavMain items={activeSpace.groups} /> : null}</SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  );
}
