/**
 * Auth store — persisted to localStorage.
 * Holds the access/refresh tokens + current user snapshot.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { CurrentUser } from "@/types/api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: CurrentUser | null;
  hydrated: boolean;
  setTokens: (access: string, refresh: string) => void;
  setUser: (u: CurrentUser | null) => void;
  logout: () => void;
  _setHydrated: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      hydrated: false,
      setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),
      setUser: (u) => set({ user: u }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
      _setHydrated: () => set({ hydrated: true }),
    }),
    {
      name: "jobtracker.auth",
      onRehydrateStorage: () => (state) => state?._setHydrated(),
    },
  ),
);
