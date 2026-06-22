"use client";

import { useEffect, useState } from "react";

import type { Client, MetaCampaign, MetaPortfolio } from "@externam/shared";
import { ChevronDown, ChevronRight, Search } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { listAccountCampaigns, listPortfolios, syncPortfolios } from "@/services/ads";
import { listClients, updateClient } from "@/services/clients";

// Filtre de liaison (la prop `items` sert au libellé du <SelectValue/>).
const LINK_ITEMS = [
  { value: "all", label: "Toutes liaisons" },
  { value: "linked", label: "Liés à un client" },
  { value: "unlinked", label: "Non liés" },
];

export default function MetaAccountsPage() {
  const [portfolios, setPortfolios] = useState<MetaPortfolio[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [clientsError, setClientsError] = useState<string | null>(null);
  // Étape 1 : campagnes par compte (chargées à la demande, en dépliant un compte).
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [campaignsByAccount, setCampaignsByAccount] = useState<Record<string, MetaCampaign[]>>({});
  const [loadingCampaigns, setLoadingCampaigns] = useState<Set<string>>(new Set());
  const [campaignError, setCampaignError] = useState<Record<string, string>>({});
  const [query, setQuery] = useState("");
  const [linkFilter, setLinkFilter] = useState("all");

  async function load() {
    setLoading(true);
    setError(null);
    setClientsError(null);
    // Chargements indépendants : un échec côté clients ne doit pas masquer les portefeuilles (et inversement).
    const [p, c] = await Promise.allSettled([listPortfolios(), listClients()]);
    if (p.status === "fulfilled") {
      setPortfolios(p.value.portfolios);
      setLastSyncedAt(p.value.last_synced_at);
    } else {
      setError(p.reason instanceof Error ? p.reason.message : "Erreur de chargement des portefeuilles");
    }
    if (c.status === "fulfilled") setClients(c.value.items);
    else setClientsError(c.reason instanceof Error ? c.reason.message : "Erreur de chargement des clients");
    setLoading(false);
  }

  async function onSync() {
    setSyncing(true);
    try {
      const r = await syncPortfolios();
      toast.success(
        `Synchro Meta : ${r.portfolios.created} nouveau(x) portefeuille(s), ${r.accounts.created} compte(s) ajouté(s), ` +
          `${r.accounts.removed} retiré(s).`,
      );
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Échec de la synchronisation Meta");
    } finally {
      setSyncing(false);
    }
  }

  // biome-ignore lint/correctness/useExhaustiveDependencies: chargement initial unique au montage
  useEffect(() => {
    void load();
  }, []);

  function linkedClient(portfolioId: string | null) {
    return portfolioId ? clients.find((c) => c.meta_business_id === portfolioId) : undefined;
  }

  async function onLink(portfolio: MetaPortfolio, value: string | null) {
    try {
      const newId = !value || value === "none" ? null : Number(value);
      const current = portfolio.id ? clients.find((c) => c.meta_business_id === portfolio.id) : undefined;
      if (current && current.id !== newId) {
        await updateClient(current.id, { meta_business_id: null });
      }
      if (newId) {
        await updateClient(newId, { meta_business_id: portfolio.id });
      }
      await load();
      toast.success("Liaison mise à jour");
    } catch {
      toast.error("Échec de la liaison");
    }
  }

  async function toggleAccount(accountId: string) {
    const willOpen = !expanded.has(accountId);
    setExpanded((prev) => {
      const next = new Set(prev);
      if (willOpen) next.add(accountId);
      else next.delete(accountId);
      return next;
    });
    // Chargement paresseux, une seule fois par compte.
    if (!willOpen || campaignsByAccount[accountId] || loadingCampaigns.has(accountId)) return;
    setLoadingCampaigns((prev) => new Set(prev).add(accountId));
    try {
      const campaigns = await listAccountCampaigns(accountId);
      setCampaignsByAccount((prev) => ({ ...prev, [accountId]: campaigns }));
    } catch (e) {
      setCampaignError((prev) => ({
        ...prev,
        [accountId]: e instanceof Error ? e.message : "Erreur de chargement des campagnes",
      }));
    } finally {
      setLoadingCampaigns((prev) => {
        const next = new Set(prev);
        next.delete(accountId);
        return next;
      });
    }
  }

  // Inclure/exclure une campagne du rapport, mémorisé sur le client lié (maj optimiste).
  async function toggleCampaign(client: Client, campaignId: string, include: boolean) {
    const current = client.managed_campaign_ids ?? [];
    const next = include ? [...current, campaignId] : current.filter((id) => id !== campaignId);
    setClients((prev) => prev.map((c) => (c.id === client.id ? { ...c, managed_campaign_ids: next } : c)));
    try {
      await updateClient(client.id, { managed_campaign_ids: next });
    } catch (e) {
      setClients((prev) => prev.map((c) => (c.id === client.id ? { ...c, managed_campaign_ids: current } : c)));
      toast.error(e instanceof Error ? e.message : "Échec de l'enregistrement de la sélection");
    }
  }

  // Inclure/exclure d'un coup toutes les campagnes d'un compte.
  async function setCampaignsForAccount(client: Client, campaignIds: string[], include: boolean) {
    const current = client.managed_campaign_ids ?? [];
    const set = new Set(current);
    for (const id of campaignIds) {
      if (include) set.add(id);
      else set.delete(id);
    }
    const next = [...set];
    setClients((prev) => prev.map((c) => (c.id === client.id ? { ...c, managed_campaign_ids: next } : c)));
    try {
      await updateClient(client.id, { managed_campaign_ids: next });
    } catch (e) {
      setClients((prev) => prev.map((c) => (c.id === client.id ? { ...c, managed_campaign_ids: current } : c)));
      toast.error(e instanceof Error ? e.message : "Échec de l'enregistrement de la sélection");
    }
  }

  const totalAccounts = portfolios.reduce((sum, p) => sum + p.accounts.length, 0);
  const linkedCount = portfolios.filter((p) => Boolean(linkedClient(p.id))).length;
  // `items` permet à <SelectValue/> d'afficher le nom du client (et non son id).
  const clientItems = [
    { value: "none", label: "— Aucun —" },
    ...clients.map((c) => ({ value: String(c.id), label: c.name })),
  ];

  // Recherche (portefeuille / compte / id / client lié) + filtre de liaison.
  const q = query.trim().toLowerCase();
  const filteredPortfolios = portfolios.filter((portfolio) => {
    const linked = linkedClient(portfolio.id);
    if (linkFilter === "linked" && !linked) return false;
    if (linkFilter === "unlinked" && linked) return false;
    if (!q) return true;
    return (
      portfolio.name.toLowerCase().includes(q) ||
      (portfolio.id ?? "").toLowerCase().includes(q) ||
      (linked?.name ?? "").toLowerCase().includes(q) ||
      portfolio.accounts.some(
        (account) => account.name.toLowerCase().includes(q) || account.account_id.toLowerCase().includes(q),
      )
    );
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-semibold text-2xl">Portefeuilles business</h1>
          <p className="text-muted-foreground text-sm">
            Comptes publicitaires regroupés par portefeuille. Lie chaque portefeuille à un client.
          </p>
          <p className="mt-1 text-muted-foreground text-xs">
            {lastSyncedAt
              ? `Dernière synchro Meta : ${new Date(lastSyncedAt).toLocaleString("fr-FR")}`
              : "Jamais synchronisé depuis Meta."}
          </p>
        </div>
        <Button size="sm" onClick={() => void onSync()} disabled={syncing}>
          {syncing ? "Synchronisation…" : "Synchroniser depuis Meta"}
        </Button>
      </div>

      {error ? (
        <div className="rounded-xl border border-dashed p-6 text-center text-muted-foreground text-sm">
          {error}
          {error.includes("META_ACCESS_TOKEN")
            ? " — ajoute le token dans apps/backend/.env puis redémarre le backend."
            : null}
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {clientsError ? (
            <div className="rounded-lg border border-dashed p-3 text-muted-foreground text-sm">
              Liaison clients indisponible ({clientsError}). Les portefeuilles restent consultables.
            </div>
          ) : null}
          {!loading ? (
            <div className="flex flex-wrap gap-2 text-sm">
              <span className="rounded-lg border bg-muted/40 px-2.5 py-1">
                <span className="font-semibold">{portfolios.length}</span> portefeuilles
              </span>
              <span className="rounded-lg border bg-muted/40 px-2.5 py-1">
                <span className="font-semibold">{totalAccounts}</span> comptes publicitaires
              </span>
              <span className="rounded-lg border bg-muted/40 px-2.5 py-1">
                <span className="font-semibold">{linkedCount}</span> liés à un client
              </span>
            </div>
          ) : null}
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative w-full max-w-xs">
              <Search className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Rechercher (portefeuille, compte, client…)"
                className="pl-8"
              />
            </div>
            <Select value={linkFilter} onValueChange={(v) => setLinkFilter(v ?? "all")} items={LINK_ITEMS}>
              <SelectTrigger className="w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LINK_ITEMS.map((it) => (
                  <SelectItem key={it.value} value={it.value}>
                    {it.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <span className="ml-auto text-muted-foreground text-sm">
              {filteredPortfolios.length} / {portfolios.length}
            </span>
          </div>
          <div className="rounded-xl border">
            <Table containerClassName="max-h-[40rem] overflow-y-auto">
              <TableHeader className="sticky top-0 z-10 bg-background [&_th]:bg-background">
                <TableRow>
                  <TableHead>Portefeuille</TableHead>
                  <TableHead>Comptes publicitaires</TableHead>
                  <TableHead className="w-64">Client lié</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: 10 }, (_, i) => i).map((i) => (
                    <TableRow key={`pf-skeleton-${i}`}>
                      <TableCell className="align-top">
                        <Skeleton className="h-4 w-40" />
                        <Skeleton className="mt-1.5 h-3 w-28" />
                      </TableCell>
                      <TableCell className="align-top">
                        <Skeleton className="h-4 w-44" />
                        <Skeleton className="mt-1.5 h-3 w-32" />
                      </TableCell>
                      <TableCell className="align-top">
                        <Skeleton className="h-8 w-full" />
                      </TableCell>
                    </TableRow>
                  ))
                ) : portfolios.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="h-24 text-center text-muted-foreground">
                      Aucun portefeuille en base. Clique sur « Synchroniser depuis Meta ».
                    </TableCell>
                  </TableRow>
                ) : filteredPortfolios.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="h-24 text-center text-muted-foreground">
                      Aucun portefeuille ne correspond à la recherche.
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredPortfolios.map((portfolio) => {
                    const linked = linkedClient(portfolio.id);
                    return (
                      <TableRow key={portfolio.id ?? portfolio.name}>
                        <TableCell className="align-top">
                          <div className="font-medium">{portfolio.name}</div>
                          <div className="text-muted-foreground text-xs">ID : {portfolio.id ?? "—"}</div>
                        </TableCell>
                        <TableCell className="align-top">
                          <div className="flex flex-col gap-2">
                            {portfolio.accounts.map((account) => {
                              const open = expanded.has(account.id);
                              const campaigns = campaignsByAccount[account.id];
                              // Tri : campagnes actives d'abord, puis par nom.
                              const sortedCampaigns = campaigns
                                ? [...campaigns].sort(
                                    (a, b) =>
                                      (a.effective_status === "ACTIVE" ? 0 : 1) -
                                        (b.effective_status === "ACTIVE" ? 0 : 1) || a.name.localeCompare(b.name),
                                  )
                                : [];
                              const includedCount =
                                linked && campaigns
                                  ? campaigns.filter((c) => (linked.managed_campaign_ids ?? []).includes(c.id)).length
                                  : 0;
                              return (
                                <div key={account.id} className="flex flex-col gap-1">
                                  <button
                                    type="button"
                                    onClick={() => void toggleAccount(account.id)}
                                    className="flex flex-wrap items-center gap-x-2 text-left text-sm hover:text-foreground"
                                  >
                                    {open ? (
                                      <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" />
                                    ) : (
                                      <ChevronRight className="size-3.5 shrink-0 text-muted-foreground" />
                                    )}
                                    <span>{account.name}</span>
                                    <span className="text-muted-foreground text-xs">ID : {account.account_id}</span>
                                  </button>

                                  {open ? (
                                    <div className="ml-[7px] flex flex-col gap-1 border-l pl-3">
                                      {loadingCampaigns.has(account.id) ? (
                                        <span className="text-muted-foreground text-xs">Chargement des campagnes…</span>
                                      ) : campaignError[account.id] ? (
                                        <span className="text-destructive text-xs">{campaignError[account.id]}</span>
                                      ) : campaigns && campaigns.length > 0 ? (
                                        <>
                                          {linked ? (
                                            <div className="flex flex-wrap items-center gap-2 text-xs">
                                              <span className="text-muted-foreground">
                                                {includedCount}/{campaigns.length} incluse
                                                {campaigns.length > 1 ? "s" : ""}
                                              </span>
                                              <button
                                                type="button"
                                                onClick={() =>
                                                  void setCampaignsForAccount(
                                                    linked,
                                                    campaigns.map((c) => c.id),
                                                    true,
                                                  )
                                                }
                                                className="text-primary hover:underline"
                                              >
                                                Tout inclure
                                              </button>
                                              <span className="text-muted-foreground">·</span>
                                              <button
                                                type="button"
                                                onClick={() =>
                                                  void setCampaignsForAccount(
                                                    linked,
                                                    campaigns.map((c) => c.id),
                                                    false,
                                                  )
                                                }
                                                className="text-muted-foreground hover:underline"
                                              >
                                                Tout exclure
                                              </button>
                                            </div>
                                          ) : (
                                            <span className="text-muted-foreground text-xs italic">
                                              Lie ce portefeuille à un client (colonne de droite) pour choisir les
                                              campagnes à inclure dans le rapport.
                                            </span>
                                          )}
                                          {sortedCampaigns.map((c) => {
                                            const included = (linked?.managed_campaign_ids ?? []).includes(c.id);
                                            return (
                                              <label
                                                key={c.id}
                                                className={cn(
                                                  "flex flex-wrap items-center gap-2 text-xs",
                                                  linked ? "cursor-pointer" : "cursor-not-allowed opacity-70",
                                                )}
                                              >
                                                <input
                                                  type="checkbox"
                                                  className="size-3.5 shrink-0 accent-primary"
                                                  checked={included}
                                                  disabled={!linked}
                                                  onChange={() =>
                                                    linked && void toggleCampaign(linked, c.id, !included)
                                                  }
                                                />
                                                <span className="font-medium">{c.name}</span>
                                                <span className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground">
                                                  {c.objective_label}
                                                </span>
                                                <span
                                                  className={cn(
                                                    "rounded px-1.5 py-0.5",
                                                    c.effective_status === "ACTIVE"
                                                      ? "bg-green-600/10 text-green-700 dark:text-green-400"
                                                      : "bg-muted text-muted-foreground",
                                                  )}
                                                >
                                                  {c.effective_status === "ACTIVE"
                                                    ? "Active"
                                                    : c.effective_status === "PAUSED"
                                                      ? "En pause"
                                                      : (c.effective_status ?? "—")}
                                                </span>
                                              </label>
                                            );
                                          })}
                                        </>
                                      ) : (
                                        <span className="text-muted-foreground text-xs">Aucune campagne.</span>
                                      )}
                                    </div>
                                  ) : null}
                                </div>
                              );
                            })}
                          </div>
                        </TableCell>
                        <TableCell className="align-top">
                          <Select
                            value={linked ? String(linked.id) : "none"}
                            onValueChange={(v) => onLink(portfolio, v)}
                            items={clientItems}
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Aucun" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">— Aucun —</SelectItem>
                              {clients.map((c) => (
                                <SelectItem key={c.id} value={String(c.id)}>
                                  {c.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </div>
  );
}
