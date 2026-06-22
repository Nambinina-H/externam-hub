"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";

import { toast } from "sonner";

import type { Client, DayOfWeek, MetaPortfolio } from "@externam/shared";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { listPortfolios } from "@/services/ads";
import { createClient, updateClient } from "@/services/clients";

import { DAY_ITEMS, DAYS } from "./clients-constants";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Si fourni → mode édition ; sinon → création. */
  client?: Client | null;
  /** Appelé après une création/mise à jour réussie (pour recharger la liste). */
  onSaved?: () => void;
}

export function ClientFormDialog({ open, onOpenChange, client, onSaved }: Props) {
  const isEdit = Boolean(client);

  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState(""); // emails séparés par des virgules
  const [businessId, setBusinessId] = useState<string | null>(null);
  const [portfolios, setPortfolios] = useState<MetaPortfolio[]>([]);
  const [day, setDay] = useState<DayOfWeek>(0);
  const [isActive, setIsActive] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // (Ré)initialise les champs à chaque ouverture / changement de client édité.
  useEffect(() => {
    if (!open) return;
    setName(client?.name ?? "");
    setCompany(client?.company ?? "");
    setPhone(client?.phone ?? "");
    setEmail((client?.emails ?? []).join(", "));
    setBusinessId(client?.meta_business_id ?? null);
    setDay((client?.report_day ?? 0) as DayOfWeek);
    setIsActive(client?.is_active ?? true);
  }, [open, client]);

  // Charge les portefeuilles (depuis la base) pour le sélecteur, à l'ouverture.
  useEffect(() => {
    if (!open) return;
    listPortfolios()
      .then((r) => setPortfolios(r.portfolios))
      .catch(() => {});
  }, [open]);

  const portfolioItems = [
    { value: "none", label: "— Aucun —" },
    ...portfolios.filter((p) => p.id).map((p) => ({ value: p.id as string, label: p.name })),
  ];

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      const emails = email
        .split(",")
        .map((e) => e.trim())
        .filter(Boolean);
      const payload = {
        name,
        company: company || null,
        phone: phone || null,
        emails,
        meta_business_id: businessId,
        report_day: day,
        is_active: isActive,
      };
      if (client) {
        await updateClient(client.id, payload);
        toast.success("Client mis à jour");
      } else {
        await createClient(payload);
        toast.success("Client ajouté");
      }
      onOpenChange(false);
      onSaved?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de l'enregistrement");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Modifier le client" : "Nouveau client"}</DialogTitle>
          <DialogDescription>
            {isEdit ? "Mets à jour les informations du client." : "Renseigne les informations du client."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="cf-name" className="font-medium text-sm">
              Nom
            </label>
            <Input
              id="cf-name"
              value={name}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
              placeholder="Jean Dupont"
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="cf-company" className="font-medium text-sm">
              Entreprise
            </label>
            <Input
              id="cf-company"
              value={company}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setCompany(e.target.value)}
              placeholder="Acme Inc."
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="cf-phone" className="font-medium text-sm">
              Téléphone
            </label>
            <Input
              id="cf-phone"
              value={phone}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setPhone(e.target.value)}
              placeholder="06 12 34 56 78"
            />
          </div>
          <div className="flex flex-col gap-1.5 sm:col-span-2">
            <label htmlFor="cf-emails" className="font-medium text-sm">
              Email(s)
            </label>
            <Input
              id="cf-emails"
              value={email}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
              placeholder="contact@acme.com, compta@acme.com"
            />
          </div>
          <div className="flex flex-col gap-1.5 sm:col-span-2">
            <label htmlFor="cf-portfolio" className="font-medium text-sm">
              Portefeuille business
            </label>
            <Select
              value={businessId ?? "none"}
              onValueChange={(v) => setBusinessId(!v || v === "none" ? null : v)}
              items={portfolioItems}
            >
              <SelectTrigger id="cf-portfolio" className="w-full">
                <SelectValue placeholder="Aucun" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">— Aucun —</SelectItem>
                {portfolios
                  .filter((p) => p.id)
                  .map((p) => (
                    <SelectItem key={p.id} value={p.id as string}>
                      {p.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
            <span className="text-muted-foreground text-xs">
              Le rapport agrège tous les comptes pub de ce portefeuille.
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="cf-day" className="font-medium text-sm">
              Jour d&apos;envoi
            </label>
            <Select value={String(day)} onValueChange={(v) => setDay(Number(v) as DayOfWeek)} items={DAY_ITEMS}>
              <SelectTrigger id="cf-day" className="w-full">
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
          </div>
          <label className="flex items-center gap-2 sm:col-span-2">
            <Checkbox checked={isActive} onCheckedChange={(v) => setIsActive(Boolean(v))} />
            <span className="text-sm">Actif (reçoit les rapports)</span>
          </label>

          <div className="flex justify-end gap-2 pt-1 sm:col-span-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Enregistrement…" : isEdit ? "Enregistrer" : "Ajouter"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
