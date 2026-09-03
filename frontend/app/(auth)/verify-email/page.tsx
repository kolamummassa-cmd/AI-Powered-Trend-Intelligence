"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { firstError, useVerifyEmail } from "@/features/auth/api/use-auth-mutations";

function VerifyEmailContent() {
  const params = useSearchParams();
  const router = useRouter();
  const emailFromLink = params.get("email") ?? "";
  const verifyMutation = useVerifyEmail();
  const [outcome, setOutcome] = useState<"error" | "awaiting" | "verifying">("awaiting");
  const [errorMessage, setErrorMessage] = useState(
    "",
  );
  const [code, setCode] = useState("");

  function verifyCode(verificationCode: string) {
    if (!emailFromLink || verificationCode.length !== 6) {
      return;
    }
    setOutcome("verifying");
    verifyMutation.mutate(
      { email: emailFromLink, code: verificationCode },
      {
        onSuccess: () => router.replace("/dashboard"),
        onError: (error) => {
          setOutcome("error");
          setErrorMessage(firstError(error, "This verification code is invalid or has expired."));
        },
      },
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email verification</CardTitle>
        <CardDescription>
          {outcome === "awaiting" && "Enter the six-digit code sent to your email to continue."}
          {outcome === "verifying" && "Verifying your code..."}
          {outcome === "error" && errorMessage}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {emailFromLink ? (
          <>
            <Input
              value={code}
              onChange={(event) => {
                const nextCode = event.target.value.replace(/\D/g, "").slice(0, 6);
                setCode(nextCode);
                if (nextCode.length === 6 && !verifyMutation.isPending) verifyCode(nextCode);
              }}
              placeholder="Six-digit verification code"
              inputMode="numeric"
              autoComplete="one-time-code"
              aria-label="Six-digit verification code"
              disabled={verifyMutation.isPending}
            />
          </>
        ) : (
          <p className="text-sm text-muted-foreground">Start by creating an account so we know where to send your code.</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyEmailContent />
    </Suspense>
  );
}
