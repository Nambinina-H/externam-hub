import type { AuthUser } from "@externam/shared";
import { create } from "zustand";

import { getMe, logout as logoutService } from "@/services/auth";

interface AuthState {
  user: AuthUser | null;
  loading: boolean;
  setUser: (user: AuthUser | null) => void;
  fetchMe: () => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: false,
  setUser: (user) => set({ user }),
  fetchMe: async () => {
    set({ loading: true });
    try {
      const user = await getMe();
      set({ user });
    } catch {
      set({ user: null });
    } finally {
      set({ loading: false });
    }
  },
  logout: async () => {
    await logoutService();
    set({ user: null });
  },
}));
