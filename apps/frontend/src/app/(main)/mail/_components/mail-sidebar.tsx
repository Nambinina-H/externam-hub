"use client";

import * as React from "react";

import { Separator } from "@/components/ui/separator";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import { getEmailSettings } from "@/services/settings";

import { mailNavigation } from "./data";
import { type MailView, useMailView } from "./use-mail-view";

export function MailSidebar() {
  const [email, setEmail] = React.useState("");
  const view = useMailView((s) => s.view);
  const setView = useMailView((s) => s.setView);

  React.useEffect(() => {
    getEmailSettings()
      .then((settings) => setEmail(settings.from_email))
      .catch(() => {});
  }, []);

  const display = email || "SMTP non configuré";
  const initial = email ? email.charAt(0).toUpperCase() : "@";

  return (
    <Sidebar collapsible="icon" className="absolute inset-y-0 h-full **:data-[sidebar=sidebar]:bg-background">
      <SidebarHeader className="gap-3 py-3 pb-1">
        <div className="flex items-center gap-2">
          <span className={markerClassName}>{initial}</span>
          <div className="flex min-w-0 flex-col group-data-[state=collapsed]:hidden">
            <div className="truncate font-medium text-sm leading-tight">{display}</div>
            <div className="truncate text-muted-foreground text-xs leading-tight">Compte SMTP</div>
          </div>
        </div>

        <Separator />
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu className="gap-1">
            {mailNavigation.navMain.map((nav) => (
              <SidebarMenuItem key={nav.id}>
                <SidebarMenuButton
                  className="[&_svg]:size-3.5"
                  size="sm"
                  isActive={view === nav.id}
                  tooltip={nav.title}
                  onClick={() => setView(nav.id as MailView)}
                >
                  <nav.icon />
                  <span className="font-medium">{nav.title}</span>
                </SidebarMenuButton>
                {nav.label ? <SidebarMenuBadge className="font-medium">{nav.label}</SidebarMenuBadge> : null}
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}

const markerClassName = cn(
  "flex size-7 min-w-7 shrink-0 items-center justify-center rounded-sm p-0",
  "bg-primary text-primary-foreground text-xs",
);
