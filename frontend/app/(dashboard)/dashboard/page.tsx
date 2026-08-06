"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/features/auth/context/auth-context";

export default function DashboardPage() {
  const { user, signOut } = useAuth();

  return (
    <main className="flex flex-1 flex-col gap-6 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Signed in as {user?.email}</p>
        </div>
        <Button variant="outline" onClick={() => signOut()}>
          Sign out
        </Button>
      </div>

      <Card className="max-w-md">
        <CardHeader>
          <CardTitle>Phase 1 checkpoint</CardTitle>
          <CardDescription>
            Authentication is wired end to end. Trend monitoring and the content studio land
            in the phases ahead.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Email verified: {user?.is_verified ? "yes" : "not yet"}
        </CardContent>
      </Card>
    </main>
  );
}
