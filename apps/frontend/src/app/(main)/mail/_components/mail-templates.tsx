"use client";

import { useEffect, useRef, useState } from "react";

import type { Client } from "@externam/shared";
import { toast } from "sonner";

import { EmailReadingView } from "@/app/(main)/dashboard/_components/email-reading-view";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { APP_CONFIG } from "@/config/app-config";
import { cn } from "@/lib/utils";
import { listClients } from "@/services/clients";
import {
  deleteClientTemplate,
  type EmailTemplate,
  getBaseTemplate,
  getClientTemplate,
  getTemplatePlaceholders,
  listTemplateOverrides,
  type Placeholder,
  previewTemplate,
  updateBaseTemplate,
  upsertClientTemplate,
} from "@/services/reports";
import { getEmailSettings } from "@/services/settings";

type Selection = { type: "base" } | { type: "client"; id: number; name: string };
type Field = "subject" | "intro" | "closing" | "signature";

/** Éditeur de modèles d'email, intégré dans l'onglet « Modèles » du mail. */
export function MailTemplates() {
  const [clients, setClients] = useState<Client[]>([]);
  const [overrides, setOverrides] = useState<number[]>([]);
  const [placeholders, setPlaceholders] = useState<Placeholder[]>([]);
  const [selection, setSelection] = useState<Selection>({ type: "base" });

  const [subject, setSubject] = useState("");
  const [intro, setIntro] = useState("");
  const [closing, setClosing] = useState("");
  const [signature, setSignature] = useState("");
  const [isOverride, setIsOverride] = useState(false);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewSubject, setPreviewSubject] = useState("");
  const [fromEmail, setFromEmail] = useState("");
  const lastFocused = useRef<Field>("intro");

  function apply(t: EmailTemplate) {
    setSubject(t.subject);
    setIntro(t.intro);
    setClosing(t.closing);
    setSignature(t.signature);
    setIsOverride(t.is_override);
  }

  // biome-ignore lint/correctness/useExhaustiveDependencies: chargement initial unique au montage
  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        const [cs, ov, ph, base] = await Promise.all([
          listClients(),
          listTemplateOverrides(),
          getTemplatePlaceholders(),
          getBaseTemplate(),
        ]);
        setClients(cs.items);
        setOverrides(ov);
        setPlaceholders(ph);
        apply(base);
      } catch {
        toast.error("Impossible de charger les modèles");
      } finally {
        setLoading(false);
      }
    })();
    getEmailSettings()
      .then((s) => setFromEmail(s.from_email))
      .catch(() => undefined);
  }, []);

  // Aperçu live (debounce) avec données d'exemple.
  useEffect(() => {
    const handle = setTimeout(async () => {
      try {
        const clientId = selection.type === "client" ? selection.id : null;
        const res = await previewTemplate({ subject, intro, closing, signature, client_id: clientId });
        setPreviewHtml(res.html);
        setPreviewSubject(res.subject);
      } catch {
        /* aperçu best-effort */
      }
    }, 400);
    return () => clearTimeout(handle);
  }, [subject, intro, closing, signature, selection]);

  async function selectBase() {
    setSelection({ type: "base" });
    try {
      apply(await getBaseTemplate());
    } catch {
      toast.error("Erreur de chargement");
    }
  }

  async function selectClient(client: Client) {
    setSelection({ type: "client", id: client.id, name: client.name });
    try {
      apply(await getClientTemplate(client.id));
    } catch {
      toast.error("Erreur de chargement");
    }
  }

  function insertPlaceholder(key: string) {
    const token = `{{${key}}}`;
    const setter =
      lastFocused.current === "subject"
        ? setSubject
        : lastFocused.current === "closing"
          ? setClosing
          : lastFocused.current === "signature"
            ? setSignature
            : setIntro;
    setter((v) => (v ? `${v} ${token}` : token));
  }

  async function onSave() {
    setSaving(true);
    try {
      if (selection.type === "base") {
        await updateBaseTemplate({ subject, intro, closing, signature });
        toast.success("Modèle de base enregistré");
      } else {
        await upsertClientTemplate(selection.id, { subject, intro, closing, signature });
        setIsOverride(true);
        setOverrides((prev) => (prev.includes(selection.id) ? prev : [...prev, selection.id]));
        toast.success(`Modèle personnalisé pour ${selection.name}`);
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Échec de l'enregistrement");
    } finally {
      setSaving(false);
    }
  }

  async function onRevert() {
    if (selection.type !== "client") return;
    try {
      await deleteClientTemplate(selection.id);
      setOverrides((prev) => prev.filter((id) => id !== selection.id));
      apply(await getClientTemplate(selection.id));
      toast.success("Revenu au modèle de base");
    } catch {
      toast.error("Échec");
    }
  }

  const title = selection.type === "base" ? "Modèle de base" : `Personnalisation — ${selection.name}`;

  return (
    <div className="grid h-full min-h-0 gap-3 p-3 lg:grid-cols-[15rem_22rem_1fr]">
      {/* 1. Liste : base + clients */}
      <div className="flex min-h-0 flex-col overflow-hidden rounded-xl border">
        <div className="min-h-0 flex-1 overflow-y-auto">
          <button
            type="button"
            onClick={() => void selectBase()}
            className={cn(
              "flex w-full items-center justify-between border-b px-3 py-2.5 text-left text-sm hover:bg-muted/50",
              selection.type === "base" && "bg-muted font-medium",
            )}
          >
            Modèle de base
          </button>
          <div className="px-3 py-2 text-muted-foreground text-xs">Clients</div>
          {loading ? (
            <div className="space-y-2 px-3">
              {Array.from({ length: 6 }, (_, i) => i).map((i) => (
                <Skeleton key={`tpl-skel-${i}`} className="h-4 w-40" />
              ))}
            </div>
          ) : (
            clients.map((client) => (
              <button
                key={client.id}
                type="button"
                onClick={() => void selectClient(client)}
                className={cn(
                  "flex w-full items-center justify-between gap-2 border-b px-3 py-2 text-left text-sm hover:bg-muted/50",
                  selection.type === "client" && selection.id === client.id && "bg-muted font-medium",
                )}
              >
                <span className="truncate">{client.name}</span>
                {overrides.includes(client.id) ? (
                  <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">perso</span>
                ) : null}
              </button>
            ))
          )}
        </div>
      </div>

      {/* 2. Éditeur */}
      <div className="flex min-h-0 flex-col gap-3 overflow-y-auto rounded-xl border p-4">
        <div className="flex items-center justify-between gap-2">
          <span className="font-medium text-sm">{title}</span>
          {selection.type === "client" && isOverride ? (
            <span className="rounded bg-primary/10 px-2 py-0.5 text-primary text-xs">personnalisé</span>
          ) : selection.type === "client" ? (
            <span className="rounded bg-muted px-2 py-0.5 text-muted-foreground text-xs">hérite de la base</span>
          ) : null}
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="t-subject" className="font-medium text-sm">
            Objet
          </label>
          <Input
            id="t-subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            onFocus={() => {
              lastFocused.current = "subject";
            }}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="t-intro" className="font-medium text-sm">
            Message d&apos;intro
          </label>
          <Textarea
            id="t-intro"
            value={intro}
            onChange={(e) => setIntro(e.target.value)}
            onFocus={() => {
              lastFocused.current = "intro";
            }}
            rows={4}
            className="max-h-40"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="t-closing" className="font-medium text-sm">
            Note de clôture
          </label>
          <Textarea
            id="t-closing"
            value={closing}
            onChange={(e) => setClosing(e.target.value)}
            onFocus={() => {
              lastFocused.current = "closing";
            }}
            rows={2}
            className="max-h-28"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="t-signature" className="font-medium text-sm">
            Signature
          </label>
          <Textarea
            id="t-signature"
            value={signature}
            onChange={(e) => setSignature(e.target.value)}
            onFocus={() => {
              lastFocused.current = "signature";
            }}
            rows={3}
            className="max-h-32"
            placeholder={"Nambinina Hasina RASOANAIVO\n+261 34 24 451 46"}
          />
          <span className="text-muted-foreground text-xs">
            Le séparateur <code className="rounded bg-muted px-1 py-0.5 font-mono text-[11px]">--</code> est ajouté
            automatiquement au-dessus. Laisse vide pour ne pas afficher de signature.
          </span>
        </div>

        <div className="flex flex-col gap-1.5">
          <span className="font-medium text-sm">Variables (clic pour insérer)</span>
          <div className="flex flex-wrap gap-1.5">
            {placeholders.map((p) => (
              <button
                key={p.key}
                type="button"
                title={p.label}
                onClick={() => insertPlaceholder(p.key)}
                className="rounded border bg-muted/40 px-1.5 py-0.5 font-mono text-[11px] hover:bg-muted"
              >
                {`{{${p.key}}}`}
              </button>
            ))}
          </div>
          <span className="text-muted-foreground text-xs">
            Le détail des campagnes (par compte, selon l&apos;objectif) est ajouté automatiquement entre l&apos;intro et
            la note de clôture.
          </span>
        </div>

        <div className="mt-auto flex items-center justify-between gap-2 pt-2">
          {selection.type === "client" && isOverride ? (
            <Button type="button" variant="ghost" size="sm" onClick={() => void onRevert()}>
              Revenir à la base
            </Button>
          ) : (
            <span />
          )}
          <Button onClick={() => void onSave()} disabled={saving || loading}>
            {saving ? "Enregistrement…" : selection.type === "base" ? "Enregistrer la base" : "Personnaliser ce client"}
          </Button>
        </div>
      </div>

      {/* 3. Aperçu live façon email */}
      <div className="flex min-h-0 flex-col overflow-hidden rounded-xl border">
        <div className="border-b px-3 py-2 text-muted-foreground text-sm">Aperçu (données d&apos;exemple)</div>
        <div className="min-h-0 flex-1">
          <EmailReadingView
            subject={previewSubject}
            date={new Date().toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}
            fromName={APP_CONFIG.name}
            fromEmail={fromEmail || undefined}
            to={
              selection.type === "client"
                ? (clients.find((c) => c.id === selection.id)?.emails?.[0] ?? selection.name)
                : "client@exemple.com"
            }
            html={previewHtml}
            loading={!previewHtml}
          />
        </div>
      </div>
    </div>
  );
}
