"use client";

import * as React from "react";

import { useRouter } from "next/navigation";

import { Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import type { NavGroup, NavMainItem } from "@/navigation/sidebar/sidebar-items";
import { spacesForRole } from "@/navigation/sidebar/sidebar-items";
import { useAuthStore } from "@/stores/auth-store";

type SearchItem = {
  group: string;
  label: string;
  url: string;
  icon?: NavMainItem["icon"];
  disabled?: boolean;
  newTab?: boolean;
};

// Construit les entrées de recherche à partir des groupes des espaces accessibles au rôle.
function buildSearchItems(groups: NavGroup[]): SearchItem[] {
  const groupLabels = new Set(groups.flatMap((group) => (group.label ? [group.label] : [])));
  const subItemGroup = (groupLabel: string | undefined, itemTitle: string) =>
    groupLabels.has(itemTitle) ? (groupLabel ?? "Autre") : itemTitle;

  return groups.flatMap((group) =>
    group.items.flatMap((item) => {
      if (item.subItems) {
        return item.subItems.map((sub) => ({
          group: subItemGroup(group.label, item.title),
          label: sub.title,
          url: sub.url,
          icon: item.icon,
          disabled: sub.comingSoon,
          newTab: sub.newTab,
        }));
      }
      return [
        {
          group: group.label ?? "Autre",
          label: item.title,
          url: item.url,
          icon: item.icon,
          disabled: item.comingSoon,
          newTab: item.newTab,
        },
      ];
    }),
  );
}

function getAvailableItems(items: SearchItem[]) {
  return items.filter((item) => !item.disabled && !item.url.includes("coming-soon"));
}

function groupBy(items: SearchItem[]) {
  const groups = [...new Set(items.map((item) => item.group))];
  return groups.map((group) => ({
    group,
    items: items.filter((item) => item.group === group),
  }));
}

export function SearchDialog() {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const router = useRouter();
  const role = useAuthStore((s) => s.user?.role);

  const searchItems = React.useMemo(
    () => buildSearchItems(spacesForRole(role).flatMap((space) => space.groups)),
    [role],
  );
  const recommendations = React.useMemo(() => getAvailableItems(searchItems), [searchItems]);

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "j" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const handleOpenChange = (value: boolean) => {
    setOpen(value);
    if (!value) setQuery("");
  };

  const handleSelect = (item: SearchItem) => {
    if (item.disabled) return;
    handleOpenChange(false);
    if (item.newTab) {
      window.open(item.url, "_blank", "noopener,noreferrer");
    } else {
      router.push(item.url);
    }
  };

  const renderGroups = (items: SearchItem[]) =>
    groupBy(items).map(({ group, items: groupItems }, index) => (
      <React.Fragment key={group}>
        {index > 0 && <CommandSeparator />}
        <CommandGroup heading={group}>
          {groupItems.map((item) => (
            <CommandItem
              disabled={item.disabled}
              key={`${group}-${item.url}-${item.label}`}
              value={`${item.group} ${item.label}`}
              onSelect={() => handleSelect(item)}
            >
              {item.icon && <item.icon />}
              <span>{item.label}</span>

              {item.disabled && (
                <Badge variant="outline" className="text-xs">
                  Bientôt
                </Badge>
              )}
            </CommandItem>
          ))}
        </CommandGroup>
      </React.Fragment>
    ));

  return (
    <>
      <Button
        onClick={() => handleOpenChange(true)}
        variant="link"
        className="px-0! font-normal text-muted-foreground hover:no-underline"
      >
        <Search data-icon="inline-start" />
        Rechercher
        <kbd className="inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-medium text-[10px]">
          <span className="text-xs">⌘</span>J
        </kbd>
      </Button>
      <CommandDialog open={open} onOpenChange={handleOpenChange}>
        <Command>
          <CommandInput placeholder="Rechercher une page…" value={query} onValueChange={setQuery} />
          <CommandList>
            <CommandEmpty>Aucun résultat.</CommandEmpty>
            {query ? renderGroups(searchItems) : renderGroups(recommendations)}
          </CommandList>
        </Command>
      </CommandDialog>
    </>
  );
}
