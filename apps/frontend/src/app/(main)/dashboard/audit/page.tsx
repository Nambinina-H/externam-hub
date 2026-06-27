"use client";

import { useEffect, useState } from "react";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { ROLE_LABELS } from "@/navigation/sidebar/role-labels";
import { type AuditLog, listAuditLogs } from "@/services/audit";

const PAGE_SIZE = 50;

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

  useEffect(() => {
    setLoading(true);
    listAuditLogs(page, PAGE_SIZE)
      .then((res) => {
        setLogs(res.items);
        setTotal(res.total);
      })
      .catch(() => toast.error("Impossible de charger le journal d'activité"))
      .finally(() => setLoading(false));
  }, [page]);

  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-semibold text-2xl">Journal d&apos;activité</h1>
        <p className="text-muted-foreground text-sm">
          Toutes les actions (création, modification, suppression) effectuées sur l&apos;application, les plus récentes
          d&apos;abord.
        </p>
      </div>

      <div className="rounded-xl border">
        <Table containerClassName="max-h-[40rem] overflow-y-auto">
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
                  Aucune action enregistrée pour l&apos;instant.
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
                  <TableCell className="font-medium">{log.action}</TableCell>
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

      <div className="flex items-center justify-between">
        <span className="text-muted-foreground text-sm">{total} action(s)</span>
        <div className="flex items-center gap-2">
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
    </div>
  );
}
