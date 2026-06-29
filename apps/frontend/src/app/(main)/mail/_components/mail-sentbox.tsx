"use client";

import { useEffect, useMemo, useState } from "react";

import type { Client } from "@externam/shared";
import { Check, Search, Send } from "lucide-react";
import { toast } from "sonner";

import { EmailReadingView } from "@/app/(main)/dashboard/_components/email-reading-view";
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
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";
import { APP_CONFIG } from "@/config/app-config";
import { cn, getInitials } from "@/lib/utils";
import { listClients } from "@/services/clients";
import { previewReport, sendDayReports, sendReport } from "@/services/reports";
import { getEmailSettings } from "@/services/settings";

const DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];

function formatDate(value: string | null | undefined) {
  if (!value) return "Jamais";
  return new Date(value).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

export function MailSentbox() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [smtpEmail, setSmtpEmail] = useState("");

  const [preview, setPreview] = useState<{ html: string; subject: string } | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [recipients, setRecipients] = useState<string[]>([]);

  const [sending, setSending] = useState(false);
  const [sendingDay, setSendingDay] = useState(false);
  const [confirmClient, setConfirmClient] = useState(false);
  const [confirmDay, setConfirmDay] = useState(false);

  async function refreshClients() {
    const res = await listClients(1, 100); // 100 = taille de page max côté backend
    setClients(res.items);
  }

  // biome-ignore lint/correctness/useExhaustiveDependencies: chargement initial unique au montage
  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        await refreshClients();
      } catch {
        toast.error("Impossible de charger les clients");
      } finally {
        setLoading(false);
      }
    })();
    getEmailSettings()
      .then((s) => setSmtpEmail(s.from_email))
      .catch(() => undefined);
  }, []);

  const selectedClient = useMemo(() => clients.find((c) => c.id === selectedId) ?? null, [clients, selectedId]);

  // Aperçu du rapport RÉEL (campagnes gérées + données Meta) au choix d'un client.
  useEffect(() => {
    if (selectedId == null) {
      setPreview(null);
      return;
    }
    setPreview(null);
    setPreviewing(true);
    previewReport(selectedId)
      .then((r) => setPreview({ html: r.html, subject: r.subject }))
      .catch(() => setPreview(null))
      .finally(() => setPreviewing(false));
  }, [selectedId]);

  function onSelect(client: Client) {
    setSelectedId(client.id);
    setRecipients(client.emails);
  }

  function toggleRecipient(email: string) {
    setRecipients((prev) => (prev.includes(email) ? prev.filter((e) => e !== email) : [...prev, email]));
  }

  async function doSendClient() {
    if (!selectedClient || recipients.length === 0) return;
    setSending(true);
    try {
      await sendReport(selectedClient.id, recipients);
      toast.success(`Rapport envoyé à ${selectedClient.name}`);
      await refreshClients();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Échec de l'envoi");
    } finally {
      setSending(false);
      setConfirmClient(false); // ferme la modale après l'envoi
    }
  }

  async function doSendDay() {
    setSendingDay(true);
    try {
      const r = await sendDayReports();
      if (r.failed > 0) {
        toast.error(`${r.sent}/${r.total} envoyé(s) — ${r.failed} en échec. Vérifie la config SMTP (Paramètres).`);
      } else {
        toast.success(`${r.sent} rapport(s) envoyé(s) pour aujourd'hui`);
      }
      await refreshClients();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Échec de l'envoi groupé");
    } finally {
      setSendingDay(false);
      setConfirmDay(false); // ferme la modale après l'envoi groupé
    }
  }

  // Seuls les clients actifs reçoivent un rapport : on ne liste qu'eux dans la Boîte d'envoi.
  const q = query.trim().toLowerCase();
  const active = clients.filter((c) => c.is_active);
  const filtered = q
    ? active.filter((c) => c.name.toLowerCase().includes(q) || c.emails.some((e) => e.toLowerCase().includes(q)))
    : active;

  const recipientNode = selectedClient ? (
    selectedClient.emails.length ? (
      <div className="flex flex-wrap gap-1.5">
        {selectedClient.emails.map((email) => {
          const on = recipients.includes(email);
          return (
            <button
              key={email}
              type="button"
              onClick={() => toggleRecipient(email)}
              className={cn(
                "flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs transition-colors",
                on ? "border-primary/40 bg-primary/10 text-foreground" : "text-muted-foreground hover:bg-muted",
              )}
            >
              {on ? <Check className="size-3" /> : null}
              {email}
            </button>
          );
        })}
      </div>
    ) : (
      <span className="text-destructive text-xs">Aucun email enregistré</span>
    )
  ) : null;

  return (
    <>
      <ResizablePanelGroup orientation="horizontal" className="h-full">
        <ResizablePanel defaultSize="38%" minSize="28%" className="min-h-0">
          <div className="flex h-full min-h-0 flex-col gap-3 py-3">
            <div className="flex items-center justify-between gap-2 px-2">
              <div className="flex items-center">
                <SidebarTrigger />
                <Separator orientation="vertical" className="mr-2 ml-1 h-4 data-vertical:self-center" />
                <h1 className="font-medium text-xl leading-none">Boîte d&apos;envoi</h1>
              </div>
              <Button size="sm" variant="outline" onClick={() => setConfirmDay(true)} disabled={sendingDay}>
                {sendingDay ? "Envoi…" : "Envoyer le jour"}
              </Button>
            </div>

            <div className="px-2">
              <Separator />
            </div>

            <div className="relative px-2">
              <Search className="absolute top-1/2 left-4 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Rechercher un client…"
                className="h-8 pl-8"
              />
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto">
              {loading ? (
                <div className="flex flex-col gap-3 p-3">
                  {Array.from({ length: 8 }, (_, i) => i).map((i) => (
                    <div key={`sb-skel-${i}`} className="flex items-center gap-3">
                      <Skeleton className="size-9 rounded-sm" />
                      <div className="flex-1 space-y-1.5">
                        <Skeleton className="h-3.5 w-32" />
                        <Skeleton className="h-3 w-44" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : filtered.length === 0 ? (
                <div className="grid h-full place-items-center px-6 text-center text-muted-foreground text-sm">
                  Aucun client.
                </div>
              ) : (
                filtered.map((client) => {
                  const selected = client.id === selectedId;
                  return (
                    <button
                      key={client.id}
                      type="button"
                      onClick={() => onSelect(client)}
                      className={cn(
                        "relative block w-full border-transparent border-b p-3 text-left transition-colors hover:bg-muted/50",
                        selected &&
                          "bg-muted/70 before:absolute before:inset-y-0 before:left-0 before:w-0.5 before:bg-primary",
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <Avatar className="size-9 after:rounded-sm">
                          <AvatarFallback className="rounded-sm bg-background text-xs">
                            {getInitials(client.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0 flex-1 space-y-1">
                          <div className="flex items-start justify-between gap-2">
                            <span className="truncate font-medium text-sm">{client.name}</span>
                            <span className="shrink-0 text-muted-foreground text-xs">
                              {formatDate(client.last_report_sent_at)}
                            </span>
                          </div>
                          <p className="truncate text-muted-foreground text-xs">{client.emails[0] ?? "Pas d'email"}</p>
                          <p className="truncate text-muted-foreground text-xs">
                            Envoi : {DAYS[client.report_day] ?? "—"}
                          </p>
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        <ResizablePanel defaultSize="62%" minSize="34%" className="min-h-0">
          {!selectedClient ? (
            <div className="grid h-full place-items-center px-6 text-center text-muted-foreground text-sm">
              Sélectionne un client pour prévisualiser et envoyer son rapport.
            </div>
          ) : (
            <EmailReadingView
              subject={preview?.subject ?? ""}
              date={new Date().toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}
              fromName={APP_CONFIG.name}
              fromEmail={smtpEmail || undefined}
              to={recipientNode}
              html={preview?.html ?? ""}
              loading={previewing}
              footer={
                <div className="flex items-center justify-between gap-2 pt-1">
                  <span className="text-muted-foreground text-xs">{recipients.length} destinataire(s)</span>
                  <Button onClick={() => setConfirmClient(true)} disabled={previewing || recipients.length === 0}>
                    <Send className="size-4" />
                    Envoyer maintenant
                  </Button>
                </div>
              }
            />
          )}
        </ResizablePanel>
      </ResizablePanelGroup>

      {/* Confirmation : envoi à un client */}
      <AlertDialog open={confirmClient} onOpenChange={setConfirmClient}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Envoyer le rapport ?</AlertDialogTitle>
            <AlertDialogDescription>
              Le rapport de « {selectedClient?.name} » sera envoyé immédiatement par email à :{" "}
              {recipients.join(", ") || "(aucun destinataire)"}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction onClick={() => void doSendClient()} disabled={sending}>
              {sending ? "Envoi…" : "Confirmer l'envoi"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Confirmation : envoi groupé du jour */}
      <AlertDialog open={confirmDay} onOpenChange={setConfirmDay}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Envoyer les rapports du jour ?</AlertDialogTitle>
            <AlertDialogDescription>
              Tous les clients actifs dont le jour d&apos;envoi est aujourd&apos;hui recevront leur rapport par email.
              Action immédiate.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction onClick={() => void doSendDay()} disabled={sendingDay}>
              {sendingDay ? "Envoi…" : "Confirmer l'envoi"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
