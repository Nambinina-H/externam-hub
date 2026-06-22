import { create } from "zustand";

/**
 * Signal de rafraîchissement de la liste des clients.
 * Permet au bouton « + » (navbar, global) de demander à la page Clients de se recharger
 * après une création, sans couplage direct entre les deux composants.
 */
interface ClientsState {
  refreshKey: number;
  requestRefresh: () => void;
}

export const useClientsStore = create<ClientsState>((set) => ({
  refreshKey: 0,
  requestRefresh: () => set((state) => ({ refreshKey: state.refreshKey + 1 })),
}));
