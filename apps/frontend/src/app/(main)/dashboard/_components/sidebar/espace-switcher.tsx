"use client";

import { ChevronsUpDown } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";
import type { NavSpace } from "@/navigation/sidebar/sidebar-items";

interface Props {
  spaces: NavSpace[];
  active?: NavSpace;
  onSelect: (space: NavSpace) => void;
}

export function EspaceSwitcher({ spaces, active, onSelect }: Props) {
  if (!active) return null;
  const ActiveIcon = active.icon;

  const label = (
    <>
      <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
        <ActiveIcon className="size-4" />
      </div>
      <div className="grid flex-1 text-left text-sm leading-tight">
        <span className="truncate font-medium">{active.label}</span>
        <span className="truncate text-muted-foreground text-xs">Espace</span>
      </div>
    </>
  );

  // Un seul espace accessible : affichage fixe (pas de menu).
  if (spaces.length <= 1) {
    return (
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton size="lg" className="pointer-events-none">
            {label}
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    );
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <SidebarMenuButton
                size="lg"
                className="data-popup-open:bg-sidebar-accent data-popup-open:text-sidebar-accent-foreground"
              />
            }
          >
            {label}
            <ChevronsUpDown className="ml-auto size-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-(--anchor-width) min-w-56 rounded-lg" align="start" side="right" sideOffset={4}>
            {spaces.map((space) => {
              const Icon = space.icon;
              return (
                <DropdownMenuItem key={space.id} onClick={() => onSelect(space)} className="gap-2">
                  <Icon className="size-4" />
                  {space.label}
                </DropdownMenuItem>
              );
            })}
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
