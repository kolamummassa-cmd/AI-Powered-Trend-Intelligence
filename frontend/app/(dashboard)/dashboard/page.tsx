"use client";

import Link from "next/link";

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

      <div className="flex flex-wrap gap-4">
        <Card className="max-w-md flex-1">
          <CardHeader>
            <CardTitle>Phase 1 checkpoint</CardTitle>
            <CardDescription>
              Authentication is wired end to end. The content studio lands in a later phase.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Email verified: {user?.is_verified ? "yes" : "not yet"}
          </CardContent>
        </Card>

        <Card className="max-w-md flex-1">
          <CardHeader>
            <CardTitle>Phase 2 checkpoint</CardTitle>
            <CardDescription>
              Trend monitoring is live: platform adapters, dedup, and a searchable trend feed.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline">
              <Link href="/trends">View trends</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
