"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { firstError, useResendVerification, useVerifyEmail } from "@/features/auth/api/use-auth-mutations";

function VerifyEmailContent() {
  const params = useSearchParams();
  const emailFromLink = params.get("email") ?? "";
  const verifyMutation = useVerifyEmail();
  const resendMutation = useResendVerification();
  const [outcome, setOutcome] = useState<"success" | "error" | "awaiting" | "sent">("awaiting");
  const [errorMessage, setErrorMessage] = useState(
    "",
  );
  const [email, setEmail] = useState(emailFromLink);
  const [code, setCode] = useState("");

  function verifyCode() {
    if (!email.trim() || code.trim().length !== 6) {
      setOutcome("error");
      setErrorMessage("Enter the email address used to create your account and its six-digit code.");
      return;
    }
    verifyMutation.mutate(
      { email: email.trim(), code: code.trim() },
      {
        onSuccess: () => setOutcome("success"),
        onError: (error) => {
          setOutcome("error");
          setErrorMessage(firstError(error, "This verification code is invalid or has expired."));
        },
      },
    );
  }

  function resendVerification() {
    if (!email.trim()) {
      setOutcome("error");
      setErrorMessage("Enter the email address you used to create your account.");
      return;
    }
    resendMutation.mutate(email.trim(), {
      onSuccess: () => setOutcome("sent"),
      onError: (error) => {
        setOutcome("error");
        setErrorMessage(firstError(error, "We could not send another verification email."));
      },
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email verification</CardTitle>
        <CardDescription>
          {outcome === "success" && "Your email is verified. You can now use AI analysis and content generation."}
          {outcome === "awaiting" && "Enter the six-digit code sent to your email before using AI features."}
          {outcome === "sent" && "If this is the email address used for an unverified account, a six-digit code is on its way. Check your inbox and spam folder."}
          {outcome === "error" && errorMessage}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {outcome !== "success" && (
          <>
            <Input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              aria-label="Email address"
            />
            <Input
              value={code}
              onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder="Six-digit verification code"
              inputMode="numeric"
              autoComplete="one-time-code"
              aria-label="Six-digit verification code"
            />
            <Button className="w-full" onClick={verifyCode} disabled={verifyMutation.isPending}>
              {verifyMutation.isPending ? "Verifying code..." : "Verify email"}
            </Button>
            <Button className="w-full" onClick={resendVerification} disabled={resendMutation.isPending}>
              {resendMutation.isPending ? "Sending verification code..." : "Resend verification code"}
            </Button>
          </>
        )}
        <Button asChild className="w-full" variant={outcome === "success" ? "default" : "outline"}>
          <Link href="/dashboard">Continue to dashboard</Link>
        </Button>
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
