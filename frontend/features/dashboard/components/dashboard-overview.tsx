"use client";

import { FlameIcon, LayoutGridIcon, SparklesIcon, TrendingUpIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardStats } from "@/features/dashboard/api/use-dashboard-stats";
import { PlatformDistributionCard } from "@/features/dashboard/components/platform-distribution";
import { StatCard } from "@/features/dashboard/components/stat-card";
import { useTrends } from "@/features/trends/api/use-trends";
import { TrendCard } from "@/features/trends/components/trend-card";

export function DashboardOverview() {
  const { data: stats, isLoading, isError } = useDashboardStats();
  const { data: highPriority } = useTrends({ high_priority: true });

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    );
  }

  if (isError || !stats) {
    return (
      <p className="text-sm text-danger">Could not load dashboard stats. Is the backend running?</p>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total trends" value={stats.total_trends} icon={LayoutGridIcon} />
        <StatCard
          label="Active"
          value={stats.active_trends}
          icon={TrendingUpIcon}
          accent="success"
        />
        <StatCard label="New today" value={stats.new_today} icon={SparklesIcon} />
        <StatCard
          label="High priority"
          value={stats.high_priority_trends}
          icon={FlameIcon}
          accent="warning"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight">High-priority trends</h2>
            <Button asChild variant="ghost" size="sm">
              <Link href="/trends?high_priority=true">View all</Link>
            </Button>
          </div>
          {highPriority && highPriority.results.length === 0 && (
            <div className="rounded-lg border border-dashed border-border py-12 text-center">
              <p className="text-muted-foreground">
                No high-priority trends yet — check back once more trends are analyzed.
              </p>
            </div>
          )}
          {highPriority && highPriority.results.length > 0 && (
            <div className="grid gap-4 sm:grid-cols-2">
              {highPriority.results.slice(0, 4).map((trend) => (
                <TrendCard key={trend.id} trend={trend} />
              ))}
            </div>
          )}
        </div>

        <PlatformDistributionCard data={stats.platform_distribution} />
      </div>
    </div>
  );
}
