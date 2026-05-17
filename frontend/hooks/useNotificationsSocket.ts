"use client";
import { useEffect, useRef } from "react";
import { toast } from "sonner";

import { useAuthStore } from "@/store/auth";

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost/api/v1/ws/notifications";

/**
 * Subscribes to backend WebSocket notifications.
 * Auto-reconnects with exponential backoff (capped).
 */
export function useNotificationsSocket(onMessage?: (data: unknown) => void) {
  const token = useAuthStore((s) => s.accessToken);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  useEffect(() => {
    if (!token) return;
    let alive = true;
    let pingInt: ReturnType<typeof setInterval> | null = null;

    const connect = () => {
      if (!alive) return;
      const ws = new WebSocket(`${WS_URL}?token=${encodeURIComponent(token)}`);
      wsRef.current = ws;

      ws.onopen = () => {
        retryRef.current = 0;
        pingInt = setInterval(() => {
          try { ws.send("ping"); } catch { /* ignore */ }
        }, 25000);
      };
      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          if (data?.type === "job.assigned") {
            toast.success(`New job assigned: ${data.title}`);
          }
          onMessage?.(data);
        } catch {
          /* non-JSON, ignore */
        }
      };
      ws.onclose = () => {
        if (pingInt) clearInterval(pingInt);
        if (!alive) return;
        const backoff = Math.min(30_000, 1000 * 2 ** retryRef.current++);
        setTimeout(connect, backoff);
      };
      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      alive = false;
      if (pingInt) clearInterval(pingInt);
      wsRef.current?.close();
    };
  }, [token, onMessage]);
}
