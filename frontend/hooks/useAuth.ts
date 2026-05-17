"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth";
import type { UserRole } from "@/types/api";

/**
 * Ensures the user is hydrated; optionally enforces role.
 * Returns { user, ready }.
 */
export function useAuth(requireRole?: UserRole) {
  const router = useRouter();
  const { user, accessToken, hydrated, setUser, logout } = useAuthStore();

  useEffect(() => {
    if (!hydrated) return;
    if (!accessToken) {
      router.replace("/login");
      return;
    }
    if (!user) {
      authService
        .me()
        .then(setUser)
        .catch(() => {
          logout();
          router.replace("/login");
        });
    }
  }, [hydrated, accessToken, user, router, setUser, logout]);

  useEffect(() => {
    if (requireRole && user && user.role !== requireRole) {
      router.replace(user.role === "admin" ? "/admin" : "/employee");
    }
  }, [requireRole, user, router]);

  return { user, ready: hydrated && !!user };
}
