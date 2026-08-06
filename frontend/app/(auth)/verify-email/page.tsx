"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { firstError, useVerifyEmail } from "@/features/auth/api/use-auth-mutations";

function VerifyEmailContent() {
  const params = useSearchParams();
  const uid = params.get("uid");
  const token = params.get("token");
  const verifyMutation = useVerifyEmail();
  const [outcome, setOutcome] = useState<"pending" | "success" | "error">("pending");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!uid || !token) {
      setOutcome("error");
      setErrorMessage("This verification link is missing information.");
      return;
    }
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email verification</CardTitle>
        <CardDescription>
          {outcome === "pending" && "Confirming your email..."}
          {outcome === "success" && "Your email is verified."}
          {outcome === "error" && errorMessage}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button asChild className="w-full">
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
