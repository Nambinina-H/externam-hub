"use client";

import { useState } from "react";

import { Plus } from "lucide-react";

import { ClientFormDialog } from "@/app/(main)/dashboard/clients/_components/client-form-dialog";
import { Button } from "@/components/ui/button";
import { useClientsStore } from "@/stores/clients-store";

/** Bouton « + » global (navbar) qui ouvre le modal de création de client. */
export function QuickAddClient() {
  const [open, setOpen] = useState(false);
  const requestRefresh = useClientsStore((s) => s.requestRefresh);

  return (
    <>
      <Button
        size="icon-sm"
        variant="outline"
        onClick={() => setOpen(true)}
        aria-label="Ajouter un client"
        title="Ajouter un client"
      >
        <Plus />
      </Button>
      <ClientFormDialog open={open} onOpenChange={setOpen} onSaved={requestRefresh} />
    </>
  );
}
