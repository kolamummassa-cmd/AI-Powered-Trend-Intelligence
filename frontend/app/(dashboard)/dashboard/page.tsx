"use client";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/context/auth-context";
import { DashboardOverview } from "@/features/dashboard/components/dashboard-overview";

export default function DashboardPage() {
  const { user, signOut } = useAuth();

  return (
    <main className="flex flex-1 flex-col gap-6 p-4 sm:p-8">
      <div className="flex flex-col gap-3 rounded-2xl border border-primary/20 bg-linear-to-br from-primary/10 via-card to-warning/10 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Trend intelligence</p>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="truncate text-black/70 dark:text-white/70">Signed in as {user?.email}</p>
        </div>
        <Button variant="outline" onClick={() => signOut()} className="self-start sm:self-auto">
          Sign out
        </Button>
      </div>

      <DashboardOverview />
    </main>
  );
}
