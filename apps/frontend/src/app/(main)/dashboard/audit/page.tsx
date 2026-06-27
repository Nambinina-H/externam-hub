"use client";

import { useEffect, useState } from "react";

import { Search } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { ROLE_LABELS } from "@/navigation/sidebar/role-labels";
import { type AuditLog, listAuditLogs } from "@/services/audit";

const PAGE_SIZE = 50;

const METHOD_ITEMS = [
  { value: "all", label: "Toutes les méthodes" },
  { value: "POST", label: "Création (POST)" },
  { value: "PATCH", label: "Modification (PATCH)" },
  { value: "PUT", label: "Modification (PUT)" },
  { value: "DELETE", label: "Suppression (DELETE)" },
];

const METHOD_CLASS: Record<string, string> = {
  POST: "bg-green-600/10 text-green-700 dark:text-green-400",
  PATCH: "bg-amber-600/10 text-amber-700 dark:text-amber-400",
  PUT: "bg-amber-600/10 text-amber-700 dark:text-amber-400",
  DELETE: "bg-red-600/10 text-red-700 dark:text-red-400",
};

function statusClass(code: number) {
  if (code >= 500) return "text-red-600 dark:text-red-400";
  if (code >= 400) return "text-amber-600 dark:text-amber-400";
  return "text-green-600 dark:text-green-400";
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [actor, setActor] = useState("");
  const [method, setMethod] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Un changement de filtre revient à la 1re page.
  function onFilter(setter: (v: string) => void, value: string) {
    setPage(1);
    setter(value);
  }

  function resetFilters() {
    setPage(1);
    setActor("");
    setMethod("all");
    setDateFrom("");
    setDateTo("");
  }

  useEffect(() => {
    const handle = setTimeout(() => {
      setLoading(true);
      listAuditLogs({
        page,
        size: PAGE_SIZE,
        actor: actor || undefined,
        method: method === "all" ? undefined : method,
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
      })
        .then((res) => {
          setLogs(res.items);
          setTotal(res.total);
        })
        .catch(() => toast.error("Impossible de charger le journal d'activité"))
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(handle);
  }, [page, actor, method, dateFrom, dateTo]);

  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const hasFilter = actor !== "" || method !== "all" || dateFrom !== "" || dateTo !== "";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-semibold text-2xl">Journal d&apos;activité</h1>
        <p className="text-muted-foreground text-sm">
          Toutes les actions (création, modification, suppression) effectuées sur l&apos;application, les plus récentes
          d&apos;abord.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative w-full max-w-xs">
          <Search className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={actor}
            onChange={(e) => onFilter(setActor, e.target.value)}
            placeholder="Acteur (email)"
            className="pl-8"
          />
        </div>
        <Select value={method} onValueChange={(v) => onFilter(setMethod, v ?? "all")} items={METHOD_ITEMS}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {METHOD_ITEMS.map((it) => (
              <SelectItem key={it.value} value={it.value}>
                {it.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="flex items-center gap-1.5">
          <span className="text-muted-foreground text-sm">Du</span>
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => onFilter(setDateFrom, e.target.value)}
            aria-label="Date de début"
            className="w-40"
          />
          <span className="text-muted-foreground text-sm">au</span>
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => onFilter(setDateTo, e.target.value)}
            aria-label="Date de fin"
            className="w-40"
          />
        </div>
        {hasFilter ? (
          <Button variant="ghost" size="sm" onClick={resetFilters}>
            Réinitialiser
          </Button>
        ) : null}
        <span className="ml-auto text-muted-foreground text-sm">{total} action(s)</span>
      </div>

      <div className="rounded-xl border">
        <Table containerClassName="max-h-[36rem] overflow-y-auto">
          <TableHeader className="sticky top-0 z-10 bg-background [&_th]:bg-background">
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Acteur</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Méthode</TableHead>
              <TableHead>Chemin</TableHead>
              <TableHead className="text-right">Statut</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  Chargement…
                </TableCell>
              </TableRow>
            ) : logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  Aucune action ne correspond.
                </TableCell>
              </TableRow>
            ) : (
              logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="whitespace-nowrap text-muted-foreground text-sm">
                    {new Date(log.created_at).toLocaleString("fr-FR")}
                  </TableCell>
                  <TableCell className="text-sm">
                    {log.actor_email ?? "—"}
                    {log.actor_role ? (
                      <span className="ml-1 text-muted-foreground text-xs">
                        ({ROLE_LABELS[log.actor_role as keyof typeof ROLE_LABELS] ?? log.actor_role})
                      </span>
                    ) : null}
                  </TableCell>
                  <TableCell className="font-medium">
                    {log.action}
                    {log.changes && log.changes.length > 0 ? (
                      <ul className="mt-1 space-y-0.5">
                        {log.changes.map((c) => (
                          <li key={c.field} className="font-normal text-muted-foreground text-xs">
                            {c.field} : <span className="line-through">{c.before}</span> →{" "}
                            <span className="text-foreground">{c.after}</span>
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </TableCell>
                  <TableCell>
                    <span
                      className={cn("rounded px-1.5 py-0.5 font-mono text-xs", METHOD_CLASS[log.method] ?? "bg-muted")}
                    >
                      {log.method}
                    </span>
                  </TableCell>
                  <TableCell className="font-mono text-muted-foreground text-xs">{log.path}</TableCell>
                  <TableCell className={cn("text-right font-medium text-sm", statusClass(log.status_code))}>
                    {log.status_code}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-end gap-2">
        <Button variant="outline" size="sm" disabled={page <= 1 || loading} onClick={() => setPage((p) => p - 1)}>
          Précédent
        </Button>
        <span className="text-muted-foreground text-sm">
          Page {page} / {lastPage}
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= lastPage || loading}
          onClick={() => setPage((p) => p + 1)}
        >
          Suivant
        </Button>
      </div>
    </div>
  );
}
