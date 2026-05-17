"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiErrorMessage } from "@/lib/api";
import { authService } from "@/services/auth.service";
import { employeesService } from "@/services/employees.service";

export default function ProfilePage() {
  const qc = useQueryClient();
  const profile = useQuery({ queryKey: ["me", "employee"], queryFn: employeesService.me });

  const [phone, setPhone] = useState("");
  const phoneMut = useMutation({
    mutationFn: (p: string | null) => employeesService.updateMe(p),
    onSuccess: () => {
      toast.success("Phone updated");
      // Invalidate both the auth 'me' and the employee profile cache to ensure UI shows updated phone
      qc.invalidateQueries({ queryKey: ["me", "employee"] });
      qc.invalidateQueries({ queryKey: ["me"] });
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<{ current_password: string; new_password: string }>();
  const pwMut = useMutation({
    mutationFn: ({ current_password, new_password }: { current_password: string; new_password: string }) =>
      authService.changePassword(current_password, new_password),
    onSuccess: () => {
      toast.success("Password changed");
      reset();
    },
    onError: (e) => toast.error(apiErrorMessage(e)),
  });

  if (profile.isLoading) return <p className="text-sm text-[hsl(var(--muted-foreground))]">Loading…</p>;
  if (!profile.data) return <p>No profile</p>;

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card>
        <CardHeader><CardTitle>My profile</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm">
          <Row k="Name" v={profile.data.full_name} />
          <Row k="Email" v={profile.data.email} />
          <Row k="Department" v={profile.data.department || "—"} />
          <Row k="Role" v={profile.data.role} />
          <Row k="Status" v={profile.data.employment_status} />
          <div className="pt-2">
            <Label htmlFor="phone">Phone number</Label>
            <div className="mt-1 flex gap-2">
              <Input
                id="phone"
                defaultValue={profile.data.phone_number ?? ""}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+27 11 …"
              />
              <Button onClick={() => phoneMut.mutate(phone || null)} disabled={phoneMut.isPending}>
                Save
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Change password</CardTitle></CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit((v) => pwMut.mutate(v))}
            className="space-y-3"
          >
            <div className="space-y-1.5">
              <Label htmlFor="current_password">Current password</Label>
              <Input id="current_password" type="password" {...register("current_password", { required: true })} />
              {errors.current_password && <p className="text-xs text-red-500">Required</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="new_password">New password</Label>
              <Input id="new_password" type="password" {...register("new_password", { required: true, minLength: 8 })} />
              {errors.new_password && <p className="text-xs text-red-500">At least 8 characters</p>}
            </div>
            <Button type="submit" disabled={pwMut.isPending}>
              {pwMut.isPending ? "Updating…" : "Update password"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between border-b border-[hsl(var(--border))] pb-1.5">
      <span className="text-[hsl(var(--muted-foreground))]">{k}</span>
      <span className="font-medium">{v}</span>
    </div>
  );
}
