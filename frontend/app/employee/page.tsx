"use client";
import { useQuery } from "@tanstack/react-query";
import { Briefcase, CalendarClock, CheckCircle2, Clock, ListTodo } from "lucide-react";

import React from "react";
import { Empty } from "@/components/empty";
import { StatCard } from "@/components/stat-card";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";
import { dashboardService } from "@/services/dashboard.service";
import type { EmployeeDashboardData } from "@/types/api";
import { useAuthStore } from "@/store/auth";

const priorityBadge: Record<string, "muted" | "info" | "warning" | "danger"> = {
  low: "muted",
  medium: "info",
  high: "warning",
  critical: "danger",
};

export default function EmployeeDashboardPage() {
  const auth = useAuthStore((s) => ({ hydrated: s.hydrated, token: s.accessToken }));

  const { data, isLoading } = useQuery<EmployeeDashboardData | undefined>({
    queryKey: ["dashboard", "employee"],
    queryFn: dashboardService.employee,
    enabled: Boolean(auth.hydrated && auth.token),
    refetchInterval: 30_000,
  });

  if (!auth.hydrated || isLoading) return <p className="text-sm text-[hsl(var(--muted-foreground))]">Loading…</p>;
  if (!data) return <Empty title="No data" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Welcome, {data.profile.full_name}</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">{data.profile.department || "—"}</p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Assigned" value={data.jobs.total} icon={<Briefcase />} accent="primary" />
        <StatCard label="Pending" value={data.jobs.pending} icon={<ListTodo />} accent="warning" />
        <StatCard label="In Progress" value={data.jobs.in_progress} icon={<Clock />} accent="info" />
        <StatCard label="Completed" value={data.jobs.completed} icon={<CheckCircle2 />} accent="success" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarClock size={18} /> Upcoming due dates
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data.alerts && data.alerts.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-semibold">Alerts</h3>
              <ul className="mt-2 space-y-2">
                {data.alerts.map((a: { id: string; title: string; message?: string | null; priority: string; status: string }) => (
                  <li key={a.id} className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium">{a.title}</p>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">{a.message}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={priorityBadge[a.priority]}>{a.priority}</Badge>
                      <Badge variant="warning">{a.status.replace("_", " ")}</Badge>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.upcoming.length === 0 ? (
            <Empty title="No upcoming due dates" hint="You're all caught up." />
          ) : (
            <ul className="divide-y divide-[hsl(var(--border))]">
              {data.upcoming.map((j) => (
                <li key={j.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium">{j.title}</p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">
                      Due {formatDate(j.due_date)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={priorityBadge[j.priority]}>{j.priority}</Badge>
                    <Badge variant="muted">{j.status.replace("_", " ")}</Badge>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
