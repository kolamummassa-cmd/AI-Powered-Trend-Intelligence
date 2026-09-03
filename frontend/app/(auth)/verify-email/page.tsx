"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { firstError, useResendVerification, useVerifyEmail } from "@/features/auth/api/use-auth-mutations";

function VerifyEmailContent() {
  const params = useSearchParams();
  const uid = params.get("uid");
  const token = params.get("token");
  const emailFromLink = params.get("email") ?? "";
  const verifyMutation = useVerifyEmail();
  const resendMutation = useResendVerification();
  const hasParams = Boolean(uid && token);
  // Computed directly from the URL params available at first render —
  // no need for an effect just to derive state that's already known
  // synchronously (only the actual async verification call below needs one).
  const [outcome, setOutcome] = useState<"pending" | "success" | "error" | "awaiting" | "sent">(
    hasParams ? "pending" : "awaiting",
  );
  const [errorMessage, setErrorMessage] = useState(
    "",
  );
  const [email, setEmail] = useState(emailFromLink);

  useEffect(() => {
    if (!uid || !token) return;
    verifyMutation.mutate(
      { uid, token },
      {
        onSuccess: () => setOutcome("success"),
        onError: (error) => {
          setOutcome("error");
          setErrorMessage(firstError(error, "This verification link is invalid or has expired."));
        },
      },
    );
    // Only ever run once per mount, against whatever uid/token showed
    // up in the URL — not on every re-render of the mutation object.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uid, token]);

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
          {outcome === "pending" && "Confirming your email..."}
          {outcome === "success" && "Your email is verified. You can now use AI analysis and content generation."}
          {outcome === "awaiting" && "Check your inbox and open the verification link before using AI features."}
          {outcome === "sent" && "A fresh verification link has been sent. Check your inbox and spam folder."}
          {outcome === "error" && errorMessage}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {!hasParams && outcome !== "success" && (
          <>
            <Input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              aria-label="Email address"
            />
            <Button className="w-full" onClick={resendVerification} disabled={resendMutation.isPending}>
              {resendMutation.isPending ? "Sending verification email..." : "Resend verification email"}
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
