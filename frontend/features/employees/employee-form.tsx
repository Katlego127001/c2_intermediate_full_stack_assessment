"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import type { Employee } from "@/types/api";

const createSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email address" }).nonempty({ message: "Email is required" }),
  password: z.string().min(8, { message: "Password must be at least 8 characters" }).nonempty({ message: "Password is required" }),
  first_name: z.string().min(1, { message: "First name is required" }),
  last_name: z.string().min(1, { message: "Last name is required" }),
  phone_number: z.string().refine((v: string) => {
    if (!v) return false; // required on create
    const s = v.replace(/[\s\-()]+/g, "");
    return /^\+?\d{7,15}$/.test(s);
  }, { message: "Please enter a valid phone number (digits, optional leading +)" }),
  department: z.string().min(1, { message: "Department is required" }),
  role: z.enum(["admin", "employee"]),
  employment_status: z.enum(["active", "inactive"]),
});

const updateSchema = z.object({
  first_name: z.string().min(1),
  last_name: z.string().min(1),
  phone_number: z.string().optional().or(z.literal("")).refine((v: string | undefined) => {
    if (!v) return true;
    const s = v.replace(/[\s\-()]+/g, "");
    return /^\+?\d{7,15}$/.test(s);
  }, { message: "Invalid phone number" }),
  department: z.string().optional().or(z.literal("")),
  role: z.enum(["admin", "employee"]),
  employment_status: z.enum(["active", "inactive"]),
});

interface Props {
  initial?: Employee | null;
  submitting?: boolean;
  onCancel: () => void;
  onSubmit: (values: Record<string, unknown>) => void;
}

export function EmployeeForm({ initial, submitting, onSubmit, onCancel }: Props) {
  const editing = !!initial;
  const schema = editing ? updateSchema : createSchema;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema as never),
    defaultValues: {
      email: "",
      password: "",
      first_name: initial?.first_name ?? "",
      last_name: initial?.last_name ?? "",
      phone_number: initial?.phone_number ?? "",
      department: initial?.department ?? "",
      role: initial?.role ?? "employee",
      employment_status: initial?.employment_status ?? "active",
    },
  });

  return (
    <form onSubmit={handleSubmit((v) => onSubmit(v as Record<string, unknown>))} className="space-y-4" noValidate>
      {/* show a form-level summary when creating and there are multiple errors */}
      {!editing && Object.keys(errors).length > 0 && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
          <strong className="block font-medium">Please fix the following:</strong>
          <ul className="mt-1 list-disc list-inside">
            {Object.entries(errors).map(([k, v]) => (
              <li key={k}>{(v as any)?.message ?? k}</li>
            ))}
          </ul>
        </div>
      )}
      {!editing && (
        <>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" {...register("email" as const)} />
            {"email" in errors && (errors as Record<string, { message?: string }>).email?.message && (
              <p className="text-xs text-red-500">{(errors as Record<string, { message?: string }>).email!.message}</p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Temp password</Label>
            <Input id="password" type="text" {...register("password" as const)} />
            {"password" in errors && (errors as Record<string, { message?: string }>).password?.message && (
              <p className="text-xs text-red-500">{(errors as Record<string, { message?: string }>).password!.message}</p>
            )}
          </div>
        </>
      )}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="first_name">First name</Label>
          <Input id="first_name" {...register("first_name" as const)} />
          {(errors as Record<string, { message?: string }>).first_name?.message && (
            <p className="text-xs text-red-500">{(errors as Record<string, { message?: string }>).first_name!.message}</p>
          )}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="last_name">Last name</Label>
          <Input id="last_name" {...register("last_name" as const)} />
          {(errors as Record<string, { message?: string }>).last_name?.message && (
            <p className="text-xs text-red-500">{(errors as Record<string, { message?: string }>).last_name!.message}</p>
          )}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="phone_number">Phone</Label>
          <Input id="phone_number" {...register("phone_number" as const)} />
          {(errors as Record<string, { message?: string }>).phone_number?.message && (
            <p className="text-xs text-red-500">{(errors as Record<string, { message?: string }>).phone_number!.message}</p>
          )}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="department">Department</Label>
          <Input id="department" {...register("department" as const)} />
          {(errors as Record<string, { message?: string }>).department?.message && (
            <p className="text-xs text-red-500">{(errors as Record<string, { message?: string }>).department!.message}</p>
          )}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="role">Role</Label>
          <Select id="role" {...register("role" as const)}>
            <option value="employee">Employee</option>
            <option value="admin">Admin</option>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="employment_status">Status</Label>
          <Select id="employment_status" {...register("employment_status" as const)}>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </Select>
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : editing ? "Save" : "Create"}
        </Button>
      </div>
    </form>
  );
}
