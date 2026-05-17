"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { JobForm } from "@/features/jobs/job-form";
import { JobsTable } from "@/features/jobs/jobs-table";
import { apiErrorMessage } from "@/lib/api";
import { employeesService } from "@/services/employees.service";
import { jobsService } from "@/services/jobs.service";
import type { Job, JobPriority, JobStatus } from "@/types/api";

export default function AdminJobsPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<JobStatus | "">("");
  const [priority, setPriority] = useState<JobPriority | "">("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Job | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState<Job | null>(null);

  const jobs = useQuery({
    queryKey: ["jobs", { page, q, status, priority }],
    queryFn: () =>
      jobsService.list({
        page,
        size: 20,
        q: q || undefined,
        status: (status || undefined) as JobStatus | undefined,
        priority: (priority || undefined) as JobPriority | undefined,
      }),
  });

  const employees = useQuery({
    queryKey: ["employees", "all"],
    queryFn: () => employeesService.list({ size: 100 }),
  });

  const createMut = useMutation({
    mutationFn: jobsService.create,
    onSuccess: () => {
      toast.success("Job created");
      setOpen(false);
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof jobsService.update>[1] }) =>
      jobsService.update(id, payload),
    onSuccess: () => {
      toast.success("Job updated");
      setOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => jobsService.remove(id),
    onSuccess: () => {
      toast.success("Job deleted");
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Jobs</h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">Create, assign and manage jobs.</p>
        </div>
        <Button onClick={() => { setEditing(null); setOpen(true); }}>
          <Plus size={16} /> New Job
        </Button>
      </div>

      <Card>
        <CardContent className="grid gap-3 pt-5 md:grid-cols-4">
          <div className="relative">
            <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-[hsl(var(--muted-foreground))]" />
            <Input
              className="pl-7"
              placeholder="Search title or description"
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
          <Select value={priority} onChange={(e) => { setPriority(e.target.value as JobPriority | ""); setPage(1); }}>
            <option value="">All priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </Select>
        </CardContent>
      </Card>

      {jobs.isLoading ? (
        <p className="text-sm text-[hsl(var(--muted-foreground))]">Loading jobs…</p>
      ) : (
        <>
          <JobsTable
            jobs={jobs.data?.items ?? []}
            canEdit
            canDelete
            onEdit={(j) => { setEditing(j); setOpen(true); }}
            onDelete={(j) => {
              // Open our confirmation dialog instead of the native confirm()
              setDeleting(j);
              setDeleteOpen(true);
            }}
          />
          {jobs.data && jobs.data.pages > 1 && (
            <div className="flex items-center justify-end gap-2 text-sm">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                Prev
              </Button>
              <span>Page {page} of {jobs.data.pages}</span>
              <Button variant="outline" size="sm" disabled={page >= jobs.data.pages} onClick={() => setPage(page + 1)}>
                Next
              </Button>
            </div>
          )}
        </>
      )}

      <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) setEditing(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "Edit job" : "Create job"}</DialogTitle>
          </DialogHeader>
          <JobForm
            initial={editing}
            // pass only active employees as possible assignees
            employees={(employees.data?.items ?? []).filter((e) => e.employment_status === "active")}
            submitting={createMut.isPending || updateMut.isPending}
            onCancel={() => { setOpen(false); setEditing(null); }}
            onSubmit={async (payload) => {
              if (editing) updateMut.mutate({ id: editing.id, payload });
              else createMut.mutate(payload);
            }}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={(o) => { setDeleteOpen(o); if (!o) setDeleting(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm job deletion</DialogTitle>
            <p className="text-sm text-[hsl(var(--muted-foreground))]">This will remove the job from active lists. The record is soft-deleted and retained for audit; it can only be restored from backups. Please confirm you want to proceed.</p>
          </DialogHeader>
          <div className="mt-4">
            <p className="font-medium">{deleting ? deleting.title : ""}</p>
            <p className="text-sm text-[hsl(var(--muted-foreground))] mt-2">Assigned to: {deleting?.assignee?.full_name ?? "—"}</p>
          </div>
          <DialogFooter>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => { setDeleteOpen(false); setDeleting(null); }}>Cancel</Button>
              <Button
                variant="destructive"
                onClick={() => {
                  if (deleting) deleteMut.mutate(deleting.id);
                  setDeleteOpen(false);
                  setDeleting(null);
                }}
              >
                Delete job
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
