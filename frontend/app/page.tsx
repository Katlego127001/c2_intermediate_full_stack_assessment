"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuthStore } from "@/store/auth";

export default function Home() {
  const router = useRouter();
  const { hydrated, accessToken, user } = useAuthStore();

  useEffect(() => {
    if (!hydrated) return;
    if (!accessToken) return router.replace("/login");
    if (user) router.replace(user.role === "admin" ? "/admin" : "/employee");
    else router.replace("/login");
  }, [hydrated, accessToken, user, router]);

  return (
    <div className="flex h-screen items-center justify-center text-sm text-[hsl(var(--muted-foreground))]">
      Redirecting…
    </div>
  );
}
