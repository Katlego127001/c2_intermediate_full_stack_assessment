"use client";
import { useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Empty } from "@/components/empty";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { formatDate, formatDateTime } from "@/lib/utils";
import type { Job, JobStatus } from "@/types/api";

const priorityBadge: Record<string, "muted" | "info" | "warning" | "danger"> = {
  low: "muted",
  medium: "info",
  high: "warning",
  critical: "danger",
};
const statusBadge: Record<string, "warning" | "info" | "success"> = {
  pending: "warning",
  in_progress: "info",
  completed: "success",
};

interface Props {
  jobs: Job[];
  canEdit: boolean;
  canDelete: boolean;
  onEdit?: (job: Job) => void;
  onDelete?: (job: Job) => void;
  onStatusChange?: (job: Job, status: JobStatus, comment?: string | undefined) => void;
}

export function JobsTable({ jobs, canEdit, canDelete, onEdit, onDelete, onStatusChange }: Props) {
  const [open, setOpen] = useState(false);
  const [comment, setComment] = useState("");
  const [pendingJob, setPendingJob] = useState<Job | null>(null);
  const [pendingStatus, setPendingStatus] = useState<JobStatus | null>(null);

  if (jobs.length === 0) return <Empty title="No jobs found" hint="Try adjusting your filters." />;
  return (
    <div className="overflow-x-auto rounded-md border border-[hsl(var(--border))]">
      <table className="w-full text-sm">
        <thead className="bg-[hsl(var(--muted))] text-xs uppercase text-[hsl(var(--muted-foreground))]">
          <tr>
            <th className="px-3 py-2 text-left">Title</th>
            <th className="px-3 py-2 text-left">Assignee</th>
            <th className="px-3 py-2 text-left">Priority</th>
            <th className="px-3 py-2 text-left">Status</th>
            <th className="px-3 py-2 text-left">Due</th>
            <th className="px-3 py-2 text-left">Created</th>
            {(canEdit || canDelete) && <th className="px-3 py-2 text-right">Actions</th>}
          </tr>
        </thead>
        <tbody>
          {jobs.map((j) => (
            <tr key={j.id} className="border-t border-[hsl(var(--border))]">
              <td className="px-3 py-2">
                <div className="font-medium">{j.title}</div>
                {j.description && (
                  <div className="line-clamp-1 text-xs text-[hsl(var(--muted-foreground))]">
                    {j.description}
                  </div>
                )}
                {j.last_status_comment && (
                  <div className="mt-1 text-xs italic text-[hsl(var(--muted-foreground))]">"{j.last_status_comment}"</div>
                )}
              </td>
              <td className="px-3 py-2">{j.assignee?.full_name || "—"}</td>
              <td className="px-3 py-2">
                <Badge variant={priorityBadge[j.priority]}>{j.priority}</Badge>
              </td>
              <td className="px-3 py-2">
                {onStatusChange ? (
                  <>
                    <Select
                      className="h-8 max-w-[140px]"
                      value={j.status}
                      onChange={(e) => {
                        const newStatus = e.target.value as JobStatus;
                        // Open modal to collect an optional, professional comment
                        setPendingJob(j);
                        setPendingStatus(newStatus as JobStatus);
                        setComment("");
                        setOpen(true);
                      }}
                    >
                      <option value="pending">Pending</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                    </Select>
                    <Dialog open={open} onOpenChange={(o) => setOpen(o)}>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Record status update</DialogTitle>
                          <p className="text-sm text-[hsl(var(--muted-foreground))]">
                            Add an optional note to provide context for this status change. This will be recorded in the activity log and visible to team members.
                          </p>
                        </DialogHeader>
                        <div className="mt-4">
                          <Label htmlFor="status_comment">Comment</Label>
                          <Input
                            id="status_comment"
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            placeholder="e.g. Completed initial review, awaiting sign-off"
                          />
                        </div>
                        <DialogFooter>
                          <div className="flex gap-2">
                            <Button variant="ghost" onClick={() => {
                                setOpen(false);
                                setPendingJob(null);
                                setPendingStatus(null);
                              }}>Cancel</Button>
                            <Button onClick={() => {
                                if (pendingJob && pendingStatus) {
                                  onStatusChange?.(pendingJob, pendingStatus, comment || undefined);
                                }
                                setOpen(false);
                                setPendingJob(null);
                                setPendingStatus(null);
                              }}>Confirm</Button>
                          </div>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </>
                ) : (
                  <Badge variant={statusBadge[j.status]}>{j.status.replace("_", " ")}</Badge>
                )}
              </td>
              <td className="px-3 py-2 text-[hsl(var(--muted-foreground))]">{formatDate(j.due_date)}</td>
              <td className="px-3 py-2 text-[hsl(var(--muted-foreground))]">{formatDateTime(j.created_at)}</td>
              {(canEdit || canDelete) && (
                <td className="px-3 py-2">
                  <div className="flex justify-end gap-1">
                    {canEdit && (
                      <Button size="icon" variant="ghost" aria-label="Edit" onClick={() => onEdit?.(j)}>
                        <Pencil size={14} />
                      </Button>
                    )}
                    {canDelete && (
                      <Button
                        size="icon"
                        variant="ghost"
                        aria-label="Delete"
                        onClick={() => onDelete?.(j)}
                      >
                        <Trash2 size={14} className="text-red-500" />
                      </Button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
