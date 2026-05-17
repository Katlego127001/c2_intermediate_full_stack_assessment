"use client";
import {
  Briefcase,
  LayoutDashboard,
  LogOut,
  Menu,
  Users,
  UserCircle,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { useNotificationsSocket } from "@/hooks/useNotificationsSocket";
import { cn } from "@/lib/utils";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth";

interface NavItem { href: string; label: string; icon: React.ReactNode; }

export function AppShell({ children, role }: { children: React.ReactNode; role: "admin" | "employee" }) {
  const { ready, user } = useAuth(role);
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const logout = useAuthStore((s) => s.logout);
  const qc = useQueryClient();

  useNotificationsSocket();

  const items: NavItem[] =
    role === "admin"
      ? [
          { href: "/admin", label: "Dashboard", icon: <LayoutDashboard size={16} /> },
          { href: "/admin/jobs", label: "Jobs", icon: <Briefcase size={16} /> },
          { href: "/admin/employees", label: "Employees", icon: <Users size={16} /> },
          { href: "/profile", label: "Profile", icon: <UserCircle size={16} /> },
        ]
      : [
          { href: "/employee", label: "Dashboard", icon: <LayoutDashboard size={16} /> },
          { href: "/employee/jobs", label: "My Jobs", icon: <Briefcase size={16} /> },
          { href: "/profile", label: "Profile", icon: <UserCircle size={16} /> },
        ];

  async function handleLogout() {
    await authService.logout();
    logout();
    // Remove all cached queries so the next signed-in user doesn't see stale data
    try {
      qc.removeQueries();
    } catch (e) {
      // swallow; best-effort cache clear
    }
    try {
      qc.clear();
    } catch (e) {
      /* ignore */
    }
    try {
      // ensure persisted auth store is removed from localStorage
      localStorage.removeItem("jobtracker.auth");
    } catch (e) {
      /* ignore */
    }
    router.replace("/login");
  }

  if (!ready) {
    return (
      <div className="flex h-screen items-center justify-center text-sm text-[hsl(var(--muted-foreground))]">
        Loading…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-[hsl(var(--border))] bg-[hsl(var(--card))] px-4">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setOpen(!open)}
            aria-label="Toggle menu"
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </Button>
          <Link href={role === "admin" ? "/admin" : "/employee"} className="font-semibold tracking-tight">
            JobTracker
          </Link>
          <span
            className="ml-2 hidden rounded-full bg-[hsl(var(--muted))] px-2 py-0.5 text-xs uppercase tracking-wider text-[hsl(var(--muted-foreground))] sm:inline"
            title={`Role: ${role}`}
            aria-label={`Role: ${role}`}
          >
            {role}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden text-sm text-[hsl(var(--muted-foreground))] sm:inline" title={user?.full_name || user?.email}>
            {user?.full_name || user?.email}
          </span>
          <ThemeToggle />
          <Button variant="ghost" size="icon" aria-label="Logout" title="Logout" onClick={handleLogout}>
            <LogOut size={16} />
          </Button>
        </div>
      </header>

      <div className="flex">
        <aside
          className={cn(
            "fixed z-20 mt-14 h-[calc(100vh-3.5rem)] w-60 -translate-x-full border-r border-[hsl(var(--border))] bg-[hsl(var(--card))] transition-transform md:sticky md:top-14 md:translate-x-0",
            open && "translate-x-0",
          )}
        >
          <nav className="flex flex-col gap-1 p-3">
            {items.map((item) => {
              const active = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  title={item.label}
                  aria-label={item.label}
                  className={cn(
                    "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                    active
                      ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]"
                      : "hover:bg-[hsl(var(--muted))]",
                  )}
                >
                  {item.icon}
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        <main className="min-h-[calc(100vh-3.5rem)] flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
