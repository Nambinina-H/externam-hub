"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getEmailSettings, testEmail, updateEmailSettings } from "@/services/settings";

export default function SettingsPage() {
  const [host, setHost] = useState("smtp.gmail.com");
  const [port, setPort] = useState(587);
  const [user, setUser] = useState("");
  const [from, setFrom] = useState("");
  const [fromName, setFromName] = useState("");
  const [password, setPassword] = useState("");
  const [passwordSet, setPasswordSet] = useState(false);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testTo, setTestTo] = useState("");
  const [testing, setTesting] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const s = await getEmailSettings();
      setHost(s.smtp_host);
      setPort(s.smtp_port);
      setUser(s.smtp_user);
      setFrom(s.from_email);
      setFromName(s.from_name);
      setPasswordSet(s.password_set);
      setPassword("");
    } catch {
      toast.error("Impossible de charger la configuration email");
    } finally {
      setLoading(false);
    }
  }

  // biome-ignore lint/correctness/useExhaustiveDependencies: chargement initial unique au montage
  useEffect(() => {
    void load();
  }, []);

  function applyGmailPreset() {
    setHost("smtp.gmail.com");
    setPort(587);
    if (!from && user) setFrom(user);
    toast.info(
      "Preset Gmail. Le mot de passe doit être un mot de passe d'application (16 car.), pas ton mot de passe.",
    );
  }

  async function onSave(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await updateEmailSettings({
        smtp_host: host,
        smtp_port: port,
        smtp_user: user,
        from_email: from,
        from_name: fromName,
        smtp_password: password || undefined,
      });
      toast.success("Configuration email enregistrée");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de l'enregistrement");
    } finally {
      setSaving(false);
    }
  }

  async function onTest() {
    if (!testTo.trim()) {
      toast.error("Saisis une adresse de test.");
      return;
    }
    setTesting(true);
    try {
      const res = await testEmail(testTo.trim());
      toast.success(`Email de test envoyé à ${res.to}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de l'envoi de test");
    } finally {
      setTesting(false);
    }
  }

  const gmailMismatch = host.includes("gmail.com") && from && user && from !== user;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-semibold text-2xl">Paramètres</h1>
        <p className="text-muted-foreground text-sm">Configuration de l&apos;envoi d&apos;emails (SMTP).</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 lg:items-start">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <CardTitle>Email (SMTP)</CardTitle>
                <CardDescription>Sert à envoyer les rapports hebdo aux clients.</CardDescription>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={applyGmailPreset} disabled={loading}>
                Preset Gmail
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSave} className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="smtp-host" className="font-medium text-sm">
                  Hôte SMTP
                </label>
                <Input
                  id="smtp-host"
                  value={host}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setHost(e.target.value)}
                  disabled={loading}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="smtp-port" className="font-medium text-sm">
                  Port
                </label>
                <Input
                  id="smtp-port"
                  type="number"
                  value={port}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setPort(Number(e.target.value))}
                  disabled={loading}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="smtp-user" className="font-medium text-sm">
                  Utilisateur
                </label>
                <Input
                  id="smtp-user"
                  value={user}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setUser(e.target.value)}
                  placeholder="adresse@gmail.com"
                  disabled={loading}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="smtp-from" className="font-medium text-sm">
                  Expéditeur (From)
                </label>
                <Input
                  id="smtp-from"
                  value={from}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setFrom(e.target.value)}
                  placeholder="adresse@gmail.com"
                  disabled={loading}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5 sm:col-span-2">
                <label htmlFor="smtp-from-name" className="font-medium text-sm">
                  Nom d&apos;expéditeur
                </label>
                <Input
                  id="smtp-from-name"
                  value={fromName}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setFromName(e.target.value)}
                  placeholder="Nambinina Hasina Rasoanaivo"
                  disabled={loading}
                />
                <span className="text-muted-foreground text-xs">
                  Réutilisable dans les modèles d&apos;email via la variable{" "}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-[11px]">{"{{expediteur}}"}</code> (et{" "}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-[11px]">{"{{email}}"}</code> pour
                  l&apos;adresse).
                </span>
              </div>
              <div className="flex flex-col gap-1.5 sm:col-span-2">
                <label htmlFor="smtp-password" className="font-medium text-sm">
                  Mot de passe {passwordSet ? "(laisser vide pour conserver l'actuel)" : "d'application"}
                </label>
                <Input
                  id="smtp-password"
                  type="password"
                  value={password}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                  placeholder={passwordSet ? "•••••••••••• (inchangé)" : "Mot de passe d'application (16 car.)"}
                  disabled={loading}
                  autoComplete="off"
                />
              </div>

              {gmailMismatch ? (
                <p className="text-destructive text-xs sm:col-span-2">
                  Avec Gmail, l&apos;expéditeur doit être identique à l&apos;utilisateur, sinon l&apos;email part en
                  spam ou est rejeté.
                </p>
              ) : null}

              <div className="sm:col-span-2">
                <Button type="submit" disabled={saving || loading}>
                  {saving ? "Enregistrement…" : "Enregistrer"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tester l&apos;envoi</CardTitle>
            <CardDescription>Envoie un email de test à l&apos;adresse ci-dessous.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="flex flex-1 flex-col gap-1.5">
              <label htmlFor="test-to" className="font-medium text-sm">
                Adresse de test
              </label>
              <Input
                id="test-to"
                value={testTo}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setTestTo(e.target.value)}
                placeholder="toi@exemple.com"
              />
            </div>
            <Button type="button" variant="outline" onClick={() => void onTest()} disabled={testing || !testTo.trim()}>
              {testing ? "Envoi…" : "Tester l'envoi"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
