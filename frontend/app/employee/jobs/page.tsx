"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { JobsTable } from "@/features/jobs/jobs-table";
import { apiErrorMessage } from "@/lib/api";
import { jobsService } from "@/services/jobs.service";
import type { JobStatus } from "@/types/api";

export default function EmployeeJobsPage() {
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<JobStatus | "">("");
  const [page, setPage] = useState(1);

  const jobs = useQuery({
    queryKey: ["jobs", "mine", { q, status, page }],
    queryFn: () =>
      jobsService.list({
        page,
        size: 20,
        q: q || undefined,
        status: (status || undefined) as JobStatus | undefined,
      }),
  });

  const statusMut = useMutation({
  mutationFn: ({ id, status, comment }: { id: string; status: JobStatus; comment?: string | null }) => jobsService.setStatus(id, status, comment),
    onSuccess: () => {
      toast.success("Status updated");
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">My Jobs</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">Update job status as you progress.</p>
      </div>
      <Card>
        <CardContent className="grid gap-3 pt-5 md:grid-cols-3">
          <div className="relative">
            <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-[hsl(var(--muted-foreground))]" />
            <Input
              className="pl-7"
              placeholder="Search"
              value={q}
              onChange={(e) => { setQ(e.target.value); setPage(1); }}
            />
          </div>
          <Select value={status} onChange={(e) => { setStatus(e.target.value as JobStatus | ""); setPage(1); }}>
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </Select>
        </CardContent>
      </Card>

      {jobs.isLoading ? (
        <p className="text-sm text-[hsl(var(--muted-foreground))]">Loading…</p>
      ) : (
        <JobsTable
          jobs={jobs.data?.items ?? []}
          canEdit={false}
          canDelete={false}
          onStatusChange={(j, s, c) => statusMut.mutate({ id: j.id, status: s, comment: c })}
        />
      )}
    </div>
  );
}
