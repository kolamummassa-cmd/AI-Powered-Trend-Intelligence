"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormError } from "@/features/auth/components/form-error";
import { firstError, useConfirmPasswordReset } from "@/features/auth/api/use-auth-mutations";
import { type ResetPasswordFormValues, resetPasswordSchema } from "@/lib/validations/auth";

function ResetPasswordContent() {
  const router = useRouter();
  const params = useSearchParams();
  const uid = params.get("uid");
  const token = params.get("token");
  const confirmMutation = useConfirmPasswordReset();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormValues>({ resolver: zodResolver(resetPasswordSchema) });

  if (!uid || !token) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Invalid link</CardTitle>
          <CardDescription>This reset link is missing information.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild className="w-full" variant="outline">
            <Link href="/forgot-password">Request a new link</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  function onSubmit(values: ResetPasswordFormValues) {
    confirmMutation.mutate(
      { uid: uid as string, token: token as string, new_password: values.new_password },
      {
        onSuccess: () => {
          toast.success("Password reset — sign in with your new password.");
          router.push("/login");
        },
        onError: (error) => toast.error(firstError(error, "This link is invalid or has expired.")),
      },
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Set a new password</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="new_password">New password</Label>
            <Input
              id="new_password"
              type="password"
              autoComplete="new-password"
              {...register("new_password")}
            />
            <FormError message={errors.new_password?.message} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new_password_confirm">Confirm new password</Label>
            <Input
              id="new_password_confirm"
              type="password"
              autoComplete="new-password"
              {...register("new_password_confirm")}
            />
            <FormError message={errors.new_password_confirm?.message} />
          </div>
          <Button type="submit" className="w-full" disabled={confirmMutation.isPending}>
            {confirmMutation.isPending ? "Resetting..." : "Reset password"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordContent />
    </Suspense>
  );
}
