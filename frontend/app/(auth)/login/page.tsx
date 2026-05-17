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
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});
type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
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
      const tokens = await authService.login(values.email, values.password);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await authService.me();
      setUser(me);
      toast.success(`Welcome back, ${me.full_name || me.email}`);
      router.replace(me.role === "admin" ? "/admin" : "/employee");
    } catch (err) {
      toast.error(apiErrorMessage(err, "Login failed"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Sign in to JobTracker</CardTitle>
        <CardDescription>Enter your credentials to access the dashboard.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" autoComplete="email" {...register("email")} />
            {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" autoComplete="current-password" {...register("password")} />
            {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
          </div>
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
          <p className="text-center text-xs text-[hsl(var(--muted-foreground))]">
            Don&apos;t have an account?{" "}
            <a href="/register" className="underline">
              Create one
            </a>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
