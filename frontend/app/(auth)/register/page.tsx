"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiErrorMessage } from "@/lib/api";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8, "At least 8 characters"),
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
});
type FormValues = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);
  const [submitting, setSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setSubmitting(true);
    try {
      const tokens = await authService.register(values);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await authService.me();
      setUser(me);
      toast.success(`Welcome, ${me.full_name || me.email}`);
      router.replace(me.role === "admin" ? "/admin" : "/employee");
    } catch (err) {
      toast.error(apiErrorMessage(err, "Registration failed"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Create your account</CardTitle>
        <CardDescription>
          New accounts join as employees. The very first account becomes the system admin.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="first_name">First name</Label>
              <Input id="first_name" autoComplete="given-name" {...register("first_name")} />
              {errors.first_name && (
                <p className="text-xs text-red-500">{errors.first_name.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="last_name">Last name</Label>
              <Input id="last_name" autoComplete="family-name" {...register("last_name")} />
              {errors.last_name && (
                <p className="text-xs text-red-500">{errors.last_name.message}</p>
              )}
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" autoComplete="email" {...register("email")} />
            {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              {...register("password")}
            />
            {errors.password && (
              <p className="text-xs text-red-500">{errors.password.message}</p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Creating account…" : "Create account"}
          </Button>
          <p className="text-center text-xs text-[hsl(var(--muted-foreground))]">
            Already have an account?{" "}
            <a href="/login" className="underline">
              Sign in
            </a>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
