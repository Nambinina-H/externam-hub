"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";

import { Pencil, Trash2 } from "lucide-react";
import { toast } from "sonner";

import type { AuthUser, UserRole } from "@externam/shared";

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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ROLE_LABELS } from "@/navigation/sidebar/role-labels";
import { createUser, deleteUser, listUsers } from "@/services/users";
import { useAuthStore } from "@/stores/auth-store";

import { ROLE_ITEMS, ROLE_OPTIONS, UserEditDialog } from "./_components/user-edit-dialog";

export default function UsersPage() {
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [loading, setLoading] = useState(true);
  const currentUserId = useAuthStore((s) => s.user?.id);

  const [firstname, setFirstname] = useState("");
  const [lastname, setLastname] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("META_ADS_EXPERT");
  const [submitting, setSubmitting] = useState(false);

  const [editUser, setEditUser] = useState<AuthUser | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<AuthUser | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      const res = await listUsers();
      setUsers(res.items);
    } catch {
      toast.error("Impossible de charger les utilisateurs");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await createUser({ firstname, lastname, email, password, role });
      toast.success("Utilisateur créé");
      setFirstname("");
      setLastname("");
      setEmail("");
      setPassword("");
      setRole("META_ADS_EXPERT");
      await refresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de la création");
    } finally {
      setSubmitting(false);
    }
  }

  function onEdit(user: AuthUser) {
    setEditUser(user);
    setEditOpen(true);
  }

  async function confirmDelete() {
    const target = deleteTarget;
    setDeleteTarget(null);
    if (!target) return;
    try {
      await deleteUser(target.id);
      setUsers((prev) => prev.filter((u) => u.id !== target.id));
      toast.success("Utilisateur supprimé");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de la suppression");
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-semibold text-2xl">Utilisateurs</h1>
        <p className="text-muted-foreground text-sm">Gère l&apos;équipe et les rôles d&apos;accès.</p>
      </div>

      <form onSubmit={onCreate} className="grid gap-3 rounded-xl border p-4 md:grid-cols-3 md:items-end">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="u-firstname" className="font-medium text-sm">
            Prénom
          </label>
          <Input
            id="u-firstname"
            value={firstname}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setFirstname(e.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="u-lastname" className="font-medium text-sm">
            Nom
          </label>
          <Input
            id="u-lastname"
            value={lastname}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setLastname(e.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="u-email" className="font-medium text-sm">
            Email
          </label>
          <Input
            id="u-email"
            type="email"
            value={email}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="u-password" className="font-medium text-sm">
            Mot de passe
          </label>
          <Input
            id="u-password"
            type="password"
            value={password}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
            placeholder="8 caractères min."
            minLength={8}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="u-role" className="font-medium text-sm">
            Rôle
          </label>
          <Select value={role} onValueChange={(v) => setRole(v as UserRole)} items={ROLE_ITEMS}>
            <SelectTrigger id="u-role">
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
        </div>
        <Button type="submit" disabled={submitting} className="md:self-end">
          {submitting ? "Création…" : "Créer l'utilisateur"}
        </Button>
      </form>

      <div className="rounded-xl border">
        <Table containerClassName="max-h-[33rem] overflow-y-auto">
          <TableHeader className="sticky top-0 z-10 bg-background [&_th]:bg-background">
            <TableRow>
              <TableHead>Nom</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Rôle</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                  Chargement…
                </TableCell>
              </TableRow>
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                  Aucun utilisateur.
                </TableCell>
              </TableRow>
            ) : (
              users.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">
                    {u.firstname} {u.lastname}
                    {u.id === currentUserId ? <span className="text-muted-foreground text-xs"> (toi)</span> : null}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{u.email}</TableCell>
                  <TableCell>
                    <span className="rounded bg-muted px-2 py-0.5 font-medium text-xs">
                      {ROLE_LABELS[u.role] ?? u.role}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        size="icon-sm"
                        variant="outline"
                        onClick={() => onEdit(u)}
                        aria-label="Modifier"
                        title="Modifier"
                      >
                        <Pencil />
                      </Button>
                      <Button
                        size="icon-sm"
                        variant="outline"
                        onClick={() => setDeleteTarget(u)}
                        disabled={u.id === currentUserId}
                        aria-label="Supprimer"
                        title={u.id === currentUserId ? "Vous ne pouvez pas vous supprimer" : "Supprimer"}
                        className="text-destructive hover:text-destructive disabled:opacity-40"
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

      <UserEditDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        user={editUser}
        isSelf={editUser?.id === currentUserId}
        onSaved={refresh}
      />

      <AlertDialog
        open={deleteTarget !== null}
        onOpenChange={(o) => {
          if (!o) setDeleteTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Supprimer cet utilisateur ?</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteTarget
                ? `Le compte de ${deleteTarget.firstname} ${deleteTarget.lastname} (${deleteTarget.email}) sera définitivement supprimé.`
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
