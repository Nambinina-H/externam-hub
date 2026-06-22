"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";

import { toast } from "sonner";

import type { AuthUser, UserRole } from "@externam/shared";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ROLE_LABELS } from "@/navigation/sidebar/role-labels";
import { updateUser } from "@/services/users";

// Rôles attribuables pour l'instant (réutilisé par la page Utilisateurs).
export const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: "META_ADS_EXPERT", label: ROLE_LABELS.META_ADS_EXPERT },
  { value: "SUPERADMIN", label: ROLE_LABELS.SUPERADMIN },
];
export const ROLE_ITEMS = ROLE_OPTIONS.map((r) => ({ value: r.value, label: r.label }));

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user: AuthUser | null;
  /** L'admin modifie son propre compte : on bloque le changement de rôle. */
  isSelf: boolean;
  onSaved: () => void;
}

export function UserEditDialog({ open, onOpenChange, user, isSelf, onSaved }: Props) {
  const [firstname, setFirstname] = useState("");
  const [lastname, setLastname] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<UserRole>("META_ADS_EXPERT");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open || !user) return;
    setFirstname(user.firstname);
    setLastname(user.lastname);
    setEmail(user.email);
    setRole(user.role);
    setPassword("");
  }, [open, user]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!user) return;
    setSubmitting(true);
    try {
      await updateUser(user.id, {
        firstname,
        lastname,
        email,
        ...(isSelf ? {} : { role }),
        ...(password ? { password } : {}),
      });
      toast.success("Utilisateur mis à jour");
      onOpenChange(false);
      onSaved();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de la mise à jour");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Modifier l&apos;utilisateur</DialogTitle>
          <DialogDescription>Mets à jour les informations et le rôle du membre.</DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="ue-firstname" className="font-medium text-sm">
              Prénom
            </label>
            <Input
              id="ue-firstname"
              value={firstname}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setFirstname(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="ue-lastname" className="font-medium text-sm">
              Nom
            </label>
            <Input
              id="ue-lastname"
              value={lastname}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setLastname(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-1.5 sm:col-span-2">
            <label htmlFor="ue-email" className="font-medium text-sm">
              Email
            </label>
            <Input
              id="ue-email"
              type="email"
              value={email}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="ue-role" className="font-medium text-sm">
              Rôle
            </label>
            <Select
              value={role}
              onValueChange={(v) => setRole(v as UserRole)}
              items={ROLE_ITEMS}
              disabled={isSelf}
            >
              <SelectTrigger id="ue-role" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ROLE_OPTIONS.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {isSelf ? (
              <span className="text-muted-foreground text-xs">Tu ne peux pas changer ton propre rôle.</span>
            ) : null}
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="ue-password" className="font-medium text-sm">
              Nouveau mot de passe
            </label>
            <Input
              id="ue-password"
              type="password"
              value={password}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
              placeholder="Laisser vide pour ne pas changer"
              autoComplete="off"
            />
          </div>

          <div className="flex justify-end gap-2 pt-1 sm:col-span-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Enregistrement…" : "Enregistrer"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
