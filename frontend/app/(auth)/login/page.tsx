"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/context/auth-context";
import { FormError } from "@/features/auth/components/form-error";
import { GoogleSignInButton } from "@/features/auth/components/google-sign-in-button";
import { firstError, useGoogleAuth, useLogin } from "@/features/auth/api/use-auth-mutations";
import { type LoginFormValues, loginSchema } from "@/lib/validations/auth";

export default function LoginPage() {
  const router = useRouter();
  const { setSession } = useAuth();
  const loginMutation = useLogin();
  const googleMutation = useGoogleAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  function onSubmit(values: LoginFormValues) {
    loginMutation.mutate(values, {
      onSuccess: (data) => {
        setSession(data);
        toast.success("Welcome back.");
        router.push("/dashboard");
      },
      onError: (error) => {
        toast.error(firstError(error, "Invalid email or password."));
      },
    });
  }

  function onGoogleCredential(idToken: string) {
    googleMutation.mutate(idToken, {
      onSuccess: (data) => {
        setSession(data);
        toast.success("Welcome.");
        router.push("/dashboard");
      },
      onError: (error) => toast.error(firstError(error, "Google sign-in failed.")),
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sign in</CardTitle>
        <CardDescription>Pick up right where you left off.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" autoComplete="email" {...register("email")} />
            <FormError message={errors.email?.message} />
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Password</Label>
              <Link href="/forgot-password" className="text-xs text-muted-foreground hover:text-foreground">
                Forgot password?
              </Link>
            </div>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register("password")}
            />
            <FormError message={errors.password?.message} />
          </div>
          <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? "Signing in..." : "Sign in"}
          </Button>
        </form>

        <div className="relative text-center text-xs text-muted-foreground">
          <span className="bg-card px-2">or</span>
        </div>

        <GoogleSignInButton onCredential={onGoogleCredential} />

        <p className="text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-primary hover:underline">
            Create one
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
