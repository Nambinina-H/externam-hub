import { create } from "zustand";

/** Vue active du workspace mail : la boîte d'envoi ou l'éditeur de modèles. */
export type MailView = "sent" | "templates";

interface MailViewStore {
  view: MailView;
  setView: (view: MailView) => void;
}

export const useMailView = create<MailViewStore>((set) => ({
  view: "sent",
  setView: (view) => set({ view }),
}));
