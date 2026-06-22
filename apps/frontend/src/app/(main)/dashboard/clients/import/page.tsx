"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useState } from "react";

import { toast } from "sonner";

import type { ImportMapping, ImportPreview } from "@externam/shared";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { importClients, importPreview } from "@/services/clients";

const NONE = "none";

// Champs internes que l'on peut alimenter depuis une colonne du CSV.
const FIELDS: { key: keyof ImportMapping; label: string; hints: string[]; required?: boolean }[] = [
  { key: "name", label: "Nom du client", hints: ["nom", "name", "client"], required: true },
  { key: "company", label: "Entreprise", hints: ["entreprise", "société", "societe", "company", "raison sociale"] },
  { key: "emails", label: "Emails", hints: ["email", "mail", "courriel", "e-mail"] },
  { key: "phone", label: "Téléphone", hints: ["tel", "téléphone", "telephone", "phone", "mobile", "numéro", "numero"] },
];

/** Devine la colonne correspondant à un champ d'après les mots-clés (pour éviter des clics). */
function guessMapping(headers: string[]): ImportMapping {
  const mapping: ImportMapping = {};
  for (const field of FIELDS) {
    const match = headers.find((h) => field.hints.some((hint) => h.toLowerCase().includes(hint)));
    if (match) mapping[field.key] = match;
  }
  return mapping;
}

export default function ImportClientsPage() {
  const router = useRouter();
  const [csv, setCsv] = useState("");
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [mapping, setMapping] = useState<ImportMapping>({});
  const [autoLink, setAutoLink] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [importing, setImporting] = useState(false);

  async function onAnalyze() {
    if (!csv.trim()) return;
    setAnalyzing(true);
    try {
      const result = await importPreview(csv);
      if (result.headers.length === 0) {
        toast.error("Aucune colonne détectée. Vérifie que la 1ʳᵉ ligne contient les en-têtes.");
        return;
      }
      setPreview(result);
      setMapping(guessMapping(result.headers));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de l'analyse du CSV");
    } finally {
      setAnalyzing(false);
    }
  }

  function setField(key: keyof ImportMapping, value: string | null) {
    setMapping((prev) => ({ ...prev, [key]: !value || value === NONE ? null : value }));
  }

  async function onImport() {
    if (!mapping.name) {
      toast.error("Choisis la colonne du nom du client (obligatoire).");
      return;
    }
    setImporting(true);
    try {
      const result = await importClients(csv, mapping, autoLink);
      const linked = result.linked !== undefined ? `, ${result.linked} lié(s) à un portefeuille` : "";
      toast.success(`${result.created} créé(s), ${result.updated} mis à jour, ${result.skipped} ignoré(s)${linked}.`);
      router.push("/dashboard/clients");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de l'import");
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-semibold text-2xl">Importer des clients</h1>
          <p className="text-muted-foreground text-sm">
            Colle ton fichier CSV, puis associe chaque colonne au champ interne correspondant.
          </p>
        </div>
        <Link href="/dashboard/clients" className={buttonVariants({ variant: "ghost" })}>
          Retour
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>1. Coller le CSV</CardTitle>
          <CardDescription>La première ligne doit contenir les en-têtes de colonnes.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Textarea
            value={csv}
            onChange={(e) => setCsv(e.target.value)}
            placeholder={"NOM,Entreprise,Téléphone,Email\nJean Dupont,Acme Inc.,0612345678,jean@acme.com"}
            rows={8}
            className="max-h-64 overflow-y-auto font-mono text-xs"
          />
          <div>
            <Button onClick={onAnalyze} disabled={analyzing || !csv.trim()}>
              {analyzing ? "Analyse…" : "Analyser"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {preview ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle>2. Associer les colonnes</CardTitle>
              <CardDescription>
                {preview.count} ligne(s) détectée(s). Le nom est obligatoire ; un client existant (même nom) est mis à
                jour, les lignes sans nom sont ignorées.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              {FIELDS.map((field) => (
                <div key={field.key} className="flex flex-col gap-1.5">
                  <span className="font-medium text-sm">
                    {field.label}
                    {field.required ? <span className="text-destructive"> *</span> : null}
                  </span>
                  <Select value={mapping[field.key] ?? NONE} onValueChange={(v) => setField(field.key, v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={NONE}>— Ignorer —</SelectItem>
                      {preview.headers.map((header) => (
                        <SelectItem key={header} value={header}>
                          {header}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>3. Aperçu</CardTitle>
              <CardDescription>Les 5 premières lignes du fichier.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {preview.headers.map((header) => (
                        <TableHead key={header}>{header}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {preview.sample.map((row, index) => (
                      <TableRow key={index}>
                        {preview.headers.map((header) => (
                          <TableCell key={header} className="text-sm whitespace-nowrap">
                            {row[header]}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <label className="flex items-start gap-2 text-sm">
              <Checkbox
                checked={autoLink}
                onCheckedChange={(v) => setAutoLink(Boolean(v))}
                className="mt-0.5"
              />
              <span>
                Lier automatiquement aux portefeuilles business
                <span className="block text-muted-foreground text-xs">
                  Par cohérence (nom / entreprise / domaine email). Nécessite d&apos;avoir synchronisé les
                  portefeuilles ; les liaisons manuelles existantes ne sont pas modifiées.
                </span>
              </span>
            </label>
            <Button onClick={onImport} disabled={importing || !mapping.name}>
              {importing ? "Import…" : `Importer ${preview.count} ligne(s)`}
            </Button>
          </div>
        </>
      ) : null}
    </div>
  );
}
