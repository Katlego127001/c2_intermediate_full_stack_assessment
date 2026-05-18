"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Search } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Empty } from "@/components/empty";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { EmployeeForm } from "@/features/employees/employee-form";
import { apiErrorMessage } from "@/lib/api";
import { employeesService } from "@/services/employees.service";
import type { Employee, EmploymentStatus, UserRole } from "@/types/api";

export default function AdminEmployeesPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<EmploymentStatus | "">("");
  const [role, setRole] = useState<UserRole | "">("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Employee | null>(null);

  const employees = useQuery({
    queryKey: ["employees", { page, q, status, role }],
    queryFn: () =>
      employeesService.list({
        page,
        size: 20,
        q: q || undefined,
        status: (status || undefined) as EmploymentStatus | undefined,
        role: (role || undefined) as UserRole | undefined,
      }),
  });

  const createMut = useMutation({
    mutationFn: employeesService.create,
    onSuccess: () => {
      toast.success("Employee created");
      setOpen(false);
      qc.invalidateQueries({ queryKey: ["employees"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof employeesService.update>[1] }) =>
      employeesService.update(id, payload),
    onSuccess: () => {
      toast.success("Employee updated");
      setOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["employees"] });
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  });

  const statusMut = useMutation({
    mutationFn: ({ id, s }: { id: string; s: EmploymentStatus }) => employeesService.setStatus(id, s),
    onSuccess: () => {
      toast.success("Status updated");
      qc.invalidateQueries({ queryKey: ["employees"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Employees</h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">Manage team members and access.</p>
        </div>
        <Button onClick={() => { setEditing(null); setOpen(true); }}>
          <Plus size={16} /> Add Employee
        </Button>
      </div>

      <Card>
        <CardContent className="grid gap-3 pt-5 md:grid-cols-4">
          <div className="relative md:col-span-2">
            <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-[hsl(var(--muted-foreground))]" />
            <Input
              className="pl-7"
              placeholder="Search name, email or department"
              value={q}
              onChange={(e) => { setQ(e.target.value); setPage(1); }}
            />
          </div>
          <Select value={role} onChange={(e) => { setRole(e.target.value as UserRole | ""); setPage(1); }}>
            <option value="">All roles</option>
            <option value="admin">Admin</option>
            <option value="employee">Employee</option>
          </Select>
          <Select value={status} onChange={(e) => { setStatus(e.target.value as EmploymentStatus | ""); setPage(1); }}>
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </Select>
        </CardContent>
      </Card>

      {employees.isLoading ? (
        <p className="text-sm text-[hsl(var(--muted-foreground))]">Loading…</p>
      ) : (employees.data?.items?.length ?? 0) === 0 ? (
        <Empty title="No employees found" />
      ) : (
        <div className="overflow-x-auto rounded-md border border-[hsl(var(--border))]">
          <table className="w-full text-sm">
            <thead className="bg-[hsl(var(--muted))] text-xs uppercase text-[hsl(var(--muted-foreground))]">
              <tr>
                <th className="px-3 py-2 text-left">Name</th>
                <th className="px-3 py-2 text-left">Email</th>
                <th className="px-3 py-2 text-left">Department</th>
                <th className="px-3 py-2 text-left">Role</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(
                // Sort client-side by full_name to provide a stable, predictable
                // ordering so status updates don't move rows unexpectedly.
                employees.data!.items.slice().sort((a, b) => a.full_name.localeCompare(b.full_name))
              ).map((e) => (
                <tr key={e.id} className="border-t border-[hsl(var(--border))]">
                  <td className="px-3 py-2 font-medium">{e.full_name}</td>
                  <td className="px-3 py-2 text-[hsl(var(--muted-foreground))]">{e.email}</td>
                  <td className="px-3 py-2">{e.department || "—"}</td>
                  <td className="px-3 py-2">
                    <Badge variant={e.role === "admin" ? "info" : "muted"}>{e.role}</Badge>
                  </td>
                  <td className="px-3 py-2">
                    <Badge variant={e.employment_status === "active" ? "success" : "danger"}>
                      {e.employment_status}
                    </Badge>
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex justify-end gap-1">
                      {e.role === "admin" ? (
                        <Button size="sm" variant="ghost" disabled title="Admin accounts cannot be deactivated">
                          {e.employment_status === "active" ? "Deactivate" : "Activate"}
                        </Button>
                      ) : (
                        <Button size="sm" variant="ghost"
                          onClick={() => statusMut.mutate({ id: e.id, s: e.employment_status === "active" ? "inactive" : "active" })}
                        >
                          {e.employment_status === "active" ? "Deactivate" : "Activate"}
                        </Button>
                      )}
                      <Button size="icon" variant="ghost" aria-label="Edit"
                        onClick={() => { setEditing(e); setOpen(true); }}
                      >
                        <Pencil size={14} />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {employees.data && employees.data.pages > 1 && (
        <div className="flex items-center justify-end gap-2 text-sm">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Prev</Button>
          <span>Page {page} of {employees.data.pages}</span>
          <Button variant="outline" size="sm" disabled={page >= employees.data.pages} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      )}

      <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) setEditing(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "Edit employee" : "Add employee"}</DialogTitle>
          </DialogHeader>
          <EmployeeForm
            initial={editing}
            submitting={createMut.isPending || updateMut.isPending}
            onCancel={() => { setOpen(false); setEditing(null); }}
            onSubmit={(values) => {
              if (editing) {
                updateMut.mutate({
                  id: editing.id,
                  payload: {
                    first_name: values.first_name as string,
                    last_name: values.last_name as string,
                    phone_number: (values.phone_number as string) || null,
                    department: (values.department as string) || null,
                    role: values.role as UserRole,
                    employment_status: values.employment_status as EmploymentStatus,
                  },
                });
              } else {
                createMut.mutate({
                  email: values.email as string,
                  password: values.password as string,
                  first_name: values.first_name as string,
                  last_name: values.last_name as string,
                  // phone and department are required for creation
                  phone_number: values.phone_number as string,
                  department: values.department as string,
                  role: values.role as UserRole,
                  employment_status: values.employment_status as EmploymentStatus,
                });
              }
            }}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
