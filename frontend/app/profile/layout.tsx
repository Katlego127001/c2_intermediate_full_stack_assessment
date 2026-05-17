"use client";
import { AppShell } from "@/components/app-shell";
import { useAuthStore } from "@/store/auth";

export default function ProfileLayout({ children }: { children: React.ReactNode }) {
  const role = useAuthStore((s) => s.user?.role) ?? "employee";
  return <AppShell role={role}>{children}</AppShell>;
}
