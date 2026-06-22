"use client";

import { useEffect, useState } from "react";

import Link from "next/link";

import type { Client, DayOfWeek, MetaPortfolio } from "@externam/shared";
import { Pencil, Search, Trash2 } from "lucide-react";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button, buttonVariants } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { listPortfolios } from "@/services/ads";
import { deleteClient, listClients, updateClient } from "@/services/clients";
import { useClientsStore } from "@/stores/clients-store";

import { ClientFormDialog } from "./_components/client-form-dialog";
import { DAY_ITEMS, DAYS } from "./_components/clients-constants";

// Filtres de la barre de recherche (la prop `items` sert au libellé du <SelectValue/>).
const STATUS_ITEMS = [
  { value: "all", label: "Tous les statuts" },
  { value: "active", label: "Actifs" },
  { value: "inactive", label: "Inactifs" },
];
const DAY_FILTER_ITEMS = [{ value: "all", label: "Tous les jours" }, ...DAY_ITEMS];

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [portfolios, setPortfolios] = useState<MetaPortfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [editClient, setEditClient] = useState<Client | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Client | null>(null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [dayFilter, setDayFilter] = useState("all");
  const refreshKey = useClientsStore((s) => s.refreshKey);

  async function refresh() {
    setLoading(true);
    try {
      const [clientsRes, portfoliosRes] = await Promise.all([listClients(), listPortfolios()]);
      setClients(clientsRes.items);
      setPortfolios(portfoliosRes.portfolios);
    } catch {
      toast.error("Impossible de charger les clients");
    } finally {
      setLoading(false);
    }
  }

  // Nom du portefeuille business lié au client (via meta_business_id), ou son id en secours.
  function portfolioLabel(businessId: string | null | undefined) {
    if (!businessId) return null;
    return portfolios.find((p) => p.id === businessId)?.name ?? businessId;
  }

  // Recharge au montage + à chaque demande (ex. création via le bouton « + » de la navbar).
  // biome-ignore lint/correctness/useExhaustiveDependencies: rechargement contrôlé par refreshKey
  useEffect(() => {
    void refresh();
  }, [refreshKey]);

  async function onChangeDay(client: Client, value: DayOfWeek) {
    try {
      await updateClient(client.id, { report_day: value });
      setClients((prev) => prev.map((c) => (c.id === client.id ? { ...c, report_day: value } : c)));
      toast.success(`${client.name} : envoi le ${DAYS[value]}`);
    } catch {
      toast.error("Échec de la mise à jour");
    }
  }

  async function onToggleActive(client: Client, active: boolean) {
    try {
      await updateClient(client.id, { is_active: active });
      setClients((prev) => prev.map((c) => (c.id === client.id ? { ...c, is_active: active } : c)));
    } catch {
      toast.error("Échec de la mise à jour");
    }
  }

  function onEdit(client: Client) {
    setEditClient(client);
    setEditOpen(true);
  }

  async function onDelete(client: Client) {
    try {
      await deleteClient(client.id);
      setClients((prev) => prev.filter((c) => c.id !== client.id));
      toast.success("Client supprimé");
    } catch {
      toast.error("Échec de la suppression");
    }
  }

  async function confirmDelete() {
    const target = deleteTarget;
    setDeleteTarget(null);
    if (target) await onDelete(target);
  }

  // Recherche (nom / entreprise / email / portefeuille) + filtres statut & jour d'envoi.
  const q = query.trim().toLowerCase();
  const filtered = clients.filter((client) => {
    if (statusFilter === "active" && !client.is_active) return false;
    if (statusFilter === "inactive" && client.is_active) return false;
    if (dayFilter !== "all" && String(client.report_day) !== dayFilter) return false;
    if (!q) return true;
    return (
      client.name.toLowerCase().includes(q) ||
      (client.company ?? "").toLowerCase().includes(q) ||
      client.emails.some((email) => email.toLowerCase().includes(q)) ||
      (portfolioLabel(client.meta_business_id) ?? "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-semibold text-2xl">Clients</h1>
          <p className="text-muted-foreground text-sm">
            Gère les clients, leur portefeuille Meta Ads et le jour d&apos;envoi. Ajoute un client via le bouton{" "}
            <span className="font-medium">+</span> en haut à droite.
          </p>
        </div>
        <Link href="/dashboard/clients/import" className={buttonVariants({ variant: "outline" })}>
          Importer un CSV
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative w-full max-w-xs">
          <Search className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Rechercher (nom, entreprise, email…)"
            className="pl-8"
          />
        </div>
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v ?? "all")} items={STATUS_ITEMS}>
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_ITEMS.map((it) => (
              <SelectItem key={it.value} value={it.value}>
                {it.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={dayFilter} onValueChange={(v) => setDayFilter(v ?? "all")} items={DAY_FILTER_ITEMS}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {DAY_FILTER_ITEMS.map((it) => (
              <SelectItem key={it.value} value={it.value}>
                {it.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="ml-auto text-muted-foreground text-sm">
          {filtered.length} / {clients.length}
        </span>
      </div>

      <div className="rounded-xl border">
        <Table containerClassName="max-h-[33rem] overflow-y-auto">
          <TableHeader className="[&_th]:sticky [&_th]:top-0 [&_th]:z-20 [&_th]:bg-background">
            <TableRow>
              <TableHead>Nom</TableHead>
              <TableHead>Entreprise</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Portefeuille business</TableHead>
              <TableHead>Jour d&apos;envoi</TableHead>
              <TableHead>Actif</TableHead>
              <TableHead>Dernier envoi</TableHead>
              <TableHead className="sticky top-0 right-0 z-20 border-l bg-background text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array.from({ length: 10 }, (_, i) => i).map((i) => (
                <TableRow key={`client-skeleton-${i}`}>
                  <TableCell>
                    <Skeleton className="h-4 w-28" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-40" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-8 w-32" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="size-4" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell className="sticky right-0 border-l bg-background text-right">
                    <Skeleton className="ml-auto h-7 w-20" />
                  </TableCell>
                </TableRow>
              ))
            ) : clients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                  Aucun client. Ajoute-en un via le bouton + en haut, ou importe un CSV.
                </TableCell>
              </TableRow>
            ) : filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                  Aucun client ne correspond à la recherche.
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((client) => (
                <TableRow key={client.id} className="group/row">
                  <TableCell className="font-medium">{client.name}</TableCell>
                  <TableCell className="text-muted-foreground">{client.company ?? "—"}</TableCell>
                  <TableCell>
                    {client.emails.length > 0 ? (
                      <span className="text-sm">{client.emails.join(", ")}</span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {portfolioLabel(client.meta_business_id) ?? "—"}
                  </TableCell>
                  <TableCell>
                    <Select
                      value={String(client.report_day)}
                      onValueChange={(v) => onChangeDay(client, Number(v) as DayOfWeek)}
                      items={DAY_ITEMS}
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {DAYS.map((label, index) => (
                          <SelectItem key={label} value={String(index)}>
                            {label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Checkbox
                      checked={client.is_active}
                      onCheckedChange={(v) => onToggleActive(client, Boolean(v))}
                      aria-label="Actif"
                    />
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {client.last_report_sent_at
                      ? new Date(client.last_report_sent_at).toLocaleDateString("fr-FR")
                      : "—"}
                  </TableCell>
                  <TableCell className="sticky right-0 z-10 border-l bg-background text-right group-hover/row:bg-muted/50">
                    <div className="flex justify-end gap-2">
                      <Button
                        size="icon-sm"
                        variant="outline"
                        onClick={() => onEdit(client)}
                        aria-label="Modifier"
                        title="Modifier"
                      >
                        <Pencil />
                      </Button>
                      <Button
                        size="icon-sm"
                        variant="outline"
                        onClick={() => setDeleteTarget(client)}
                        aria-label="Supprimer"
                        title="Supprimer"
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <ClientFormDialog open={editOpen} onOpenChange={setEditOpen} client={editClient} onSaved={refresh} />

      <AlertDialog
        open={deleteTarget !== null}
        onOpenChange={(o) => {
          if (!o) setDeleteTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Supprimer ce client ?</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteTarget
                ? `« ${deleteTarget.name} » sera définitivement supprimé. Cette action est irréversible.`
                : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={confirmDelete}>
              Supprimer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
