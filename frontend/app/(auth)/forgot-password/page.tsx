"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormError } from "@/features/auth/components/form-error";
import { useRequestPasswordReset } from "@/features/auth/api/use-auth-mutations";
import { type ForgotPasswordFormValues, forgotPasswordSchema } from "@/lib/validations/auth";

export default function ForgotPasswordPage() {
  const resetMutation = useRequestPasswordReset();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormValues>({ resolver: zodResolver(forgotPasswordSchema) });

  if (resetMutation.isSuccess) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Check your email</CardTitle>
          <CardDescription>
            If an account exists for that address, a reset link is on its way.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild className="w-full" variant="outline">
            <Link href="/login">Back to sign in</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reset your password</CardTitle>
        <CardDescription>Enter the email you signed up with.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form
          onSubmit={handleSubmit((values) => resetMutation.mutate(values.email))}
          className="space-y-4"
        >
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" autoComplete="email" {...register("email")} />
            <FormError message={errors.email?.message} />
          </div>
          <Button type="submit" className="w-full" disabled={resetMutation.isPending}>
            {resetMutation.isPending ? "Sending..." : "Send reset link"}
          </Button>
        </form>
        <p className="text-center text-sm text-muted-foreground">
          <Link href="/login" className="text-primary hover:underline">
            Back to sign in
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
