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
import { PasswordInput } from "@/components/ui/password-input";
import { FormError } from "@/features/auth/components/form-error";
import { GoogleSignInButton } from "@/features/auth/components/google-sign-in-button";
import { firstError, useGoogleAuth, useRegister } from "@/features/auth/api/use-auth-mutations";
import { useAuth } from "@/features/auth/context/auth-context";
import { type RegisterFormValues, registerSchema } from "@/lib/validations/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { setSession } = useAuth();
  const registerMutation = useRegister();
  const googleMutation = useGoogleAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) });

  function onSubmit(values: RegisterFormValues) {
    registerMutation.mutate(values, {
      onSuccess: (data) => {
        router.push(`/verify-email?email=${encodeURIComponent(data.email)}`);
      },
      onError: (error) => toast.error(firstError(error, "Could not create your account.")),
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
        <CardTitle>Create your account</CardTitle>
        <CardDescription>Start with one recommended opportunity, then turn it into publish-ready content.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" autoComplete="email" {...register("email")} />
            <FormError message={errors.email?.message} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <PasswordInput
              id="password"
              autoComplete="new-password"
              {...register("password")}
            />
            <FormError message={errors.password?.message} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password_confirm">Confirm password</Label>
            <PasswordInput
              id="password_confirm"
              autoComplete="new-password"
              {...register("password_confirm")}
            />
            <FormError message={errors.password_confirm?.message} />
          </div>
          <Button type="submit" className="w-full" disabled={registerMutation.isPending}>
            {registerMutation.isPending ? "Creating account..." : "Create account"}
          </Button>
        </form>

        <div className="relative text-center text-xs text-muted-foreground">
          <span className="bg-card px-2">or</span>
        </div>

        <GoogleSignInButton onCredential={onGoogleCredential} />

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </p>
        <p className="text-center text-xs text-muted-foreground">After registration, verify your email and we&apos;ll guide you to your first opportunity.</p>
      </CardContent>
    </Card>
  );
}
