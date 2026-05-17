"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { formatDateTime } from "@/lib/utils";
import type { Employee, Job, JobPriority, JobStatus } from "@/types/api";

const createSchema = z.object({
  title: z.string().min(1, "Title is required").max(200),
  description: z.string().min(1, "Description is required").max(5000),
  priority: z.enum(["low", "medium", "high", "critical"]),
  status: z.enum(["pending", "in_progress", "completed"]),
  due_date: z.string().min(1, "Due date is required"),
  assigned_employee_id: z.string().min(1, "Assignee is required"),
});

// Edit schema: allow optional description/due/assignee when editing an existing job
const editSchema = z.object({
  title: z.string().min(1, "Title is required").max(200),
  description: z.string().max(5000).optional().or(z.literal("")),
  priority: z.enum(["low", "medium", "high", "critical"]),
  status: z.enum(["pending", "in_progress", "completed"]),
  due_date: z.string().optional().or(z.literal("")),
  assigned_employee_id: z.string().optional().or(z.literal("")),
});
export type JobFormValues = z.infer<typeof editSchema>;

interface Props {
  initial?: Job | null;
  employees: Employee[];
  onSubmit: (values: {
    title: string;
    description?: string;
    priority: JobPriority;
    status: JobStatus;
    due_date?: string | null;
    assigned_employee_id?: string | null;
  }) => Promise<void> | void;
  onCancel: () => void;
  submitting?: boolean;
}

export function JobForm({ initial, employees, onSubmit, onCancel, submitting }: Props) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<JobFormValues>({
    resolver: zodResolver(initial ? editSchema : createSchema),
    defaultValues: {
      title: initial?.title ?? "",
      description: initial?.description ?? "",
      priority: (initial?.priority as JobPriority) ?? "medium",
      status: (initial?.status as JobStatus) ?? "pending",
      due_date: initial?.due_date ? initial.due_date.slice(0, 16) : "",
      assigned_employee_id: initial?.assigned_employee_id ?? "",
    },
  });

  useEffect(() => {
    reset({
      title: initial?.title ?? "",
      description: initial?.description ?? "",
      priority: (initial?.priority as JobPriority) ?? "medium",
      status: (initial?.status as JobStatus) ?? "pending",
      due_date: initial?.due_date ? initial.due_date.slice(0, 16) : "",
      assigned_employee_id: initial?.assigned_employee_id ?? "",
    });
  }, [initial, reset]);

  return (
    <form
      onSubmit={handleSubmit((v) =>
        onSubmit({
          title: v.title.trim(),
          description: v.description?.trim() || undefined,
          priority: v.priority,
          status: v.status,
          due_date: v.due_date ? new Date(v.due_date).toISOString() : null,
          assigned_employee_id: v.assigned_employee_id || null,
        }),
      )}
      className="space-y-4"
    >
      <div className="space-y-1.5">
        <Label htmlFor="title">Title</Label>
        {initial && (
          <div className="text-xs text-[hsl(var(--muted-foreground))] mb-1">Created: {formatDateTime(initial.created_at)}</div>
        )}
        <Input id="title" {...register("title")} />
        {errors.title && <p className="text-xs text-red-500">{errors.title.message}</p>}
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="description">Description</Label>
        <Textarea id="description" rows={3} {...register("description")} />
        {errors.description && <p className="text-xs text-red-500">{errors.description.message}</p>}
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="priority">Priority</Label>
          <Select id="priority" {...register("priority")}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="status">Status</Label>
          <Select id="status" {...register("status")}>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </Select>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="due_date">Due date</Label>
          <Input id="due_date" type="datetime-local" {...register("due_date")} />
          {errors.due_date && <p className="text-xs text-red-500">{errors.due_date.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="assigned_employee_id">Assignee</Label>
          <Select id="assigned_employee_id" {...register("assigned_employee_id")}>
            <option value="">— Unassigned —</option>
            {employees.map((e) => (
              <option key={e.id} value={e.id}>
                {e.full_name} {e.department ? `· ${e.department}` : ""}
              </option>
            ))}
          </Select>
          {errors.assigned_employee_id && <p className="text-xs text-red-500">{errors.assigned_employee_id.message}</p>}
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : initial ? "Save changes" : "Create job"}
        </Button>
      </div>
    </form>
  );
}
