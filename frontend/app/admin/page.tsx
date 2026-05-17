"use client";
import { useQuery } from "@tanstack/react-query";
import { Briefcase, CheckCircle2, Clock, ListTodo, UserCheck, Users, UserX } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Empty } from "@/components/empty";
import { StatCard } from "@/components/stat-card";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDateTime } from "@/lib/utils";
import { dashboardService } from "@/services/dashboard.service";

const COLORS = ["#f59e0b", "#3b82f6", "#10b981"];

export default function AdminDashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "admin"],
    queryFn: dashboardService.admin,
    refetchInterval: 30_000,
  });

  if (isLoading) return <p className="text-sm text-[hsl(var(--muted-foreground))]">Loading dashboard…</p>;
  if (!data) return <Empty title="No data" />;

  const statusPieData = [
    { name: "Pending", value: data.jobs.pending },
    { name: "In Progress", value: data.jobs.in_progress },
    { name: "Completed", value: data.jobs.completed },
  ];

  const workloadBarData = data.workload.slice(0, 8).map((w) => ({
    name: w.full_name.split(" ")[0],
    Pending: w.pending,
    InProgress: w.in_progress,
    Completed: w.completed,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Admin Dashboard</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">Overview of jobs and team workload.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total Jobs" value={data.jobs.total} icon={<Briefcase />} accent="primary" />
        <StatCard label="Pending" value={data.jobs.pending} icon={<ListTodo />} accent="warning" />
        <StatCard label="In Progress" value={data.jobs.in_progress} icon={<Clock />} accent="info" />
        <StatCard label="Completed" value={data.jobs.completed} icon={<CheckCircle2 />} accent="success" />
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
        <StatCard label="Employees" value={data.employees.total} icon={<Users />} accent="primary" />
        <StatCard label="Active" value={data.employees.active} icon={<UserCheck />} accent="success" />
        <StatCard label="Inactive" value={data.employees.inactive} icon={<UserX />} accent="danger" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Workload by employee</CardTitle></CardHeader>
          <CardContent>
            {workloadBarData.length === 0 ? (
              <Empty title="No assigned jobs yet" />
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={workloadBarData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="name" fontSize={12} />
                    <YAxis allowDecimals={false} fontSize={12} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Pending" stackId="a" fill="#f59e0b" />
                    <Bar dataKey="InProgress" stackId="a" fill="#3b82f6" />
                    <Bar dataKey="Completed" stackId="a" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Job status</CardTitle></CardHeader>
          <CardContent>
            {data.jobs.total === 0 ? (
              <Empty title="No jobs yet" />
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={statusPieData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90}>
                      {statusPieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Recent activity</CardTitle></CardHeader>
        <CardContent>
          {data.recent_activity.length === 0 ? (
            <Empty title="Nothing to show yet" />
          ) : (
            <ul className="divide-y divide-[hsl(var(--border))]">
              {data.recent_activity.map((a) => (
                <li key={a.id} className="flex items-center justify-between py-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Badge variant="info">{a.action}</Badge>
                    <span className="text-[hsl(var(--muted-foreground))]">{a.entity_type}</span>
                    <span className="font-medium">{a.actor_email || "system"}</span>
                  </div>
                  <span className="text-xs text-[hsl(var(--muted-foreground))]">
                    {formatDateTime(a.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
