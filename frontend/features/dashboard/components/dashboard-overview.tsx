"use client";

import { ArrowRightIcon, FlameIcon, LayoutGridIcon, SparklesIcon, TrendingUpIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardStats } from "@/features/dashboard/api/use-dashboard-stats";
import { PlatformDistributionCard } from "@/features/dashboard/components/platform-distribution";
import { StatCard } from "@/features/dashboard/components/stat-card";
import { useTrends } from "@/features/trends/api/use-trends";
import { TrendCard } from "@/features/trends/components/trend-card";

export function DashboardOverview() {
  const { data: stats, isLoading, isError, refetch } = useDashboardStats();
  const { data: highPriority } = useTrends({ high_priority: true, kuzana_only: true });

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
      <div className="rounded-lg border border-border bg-muted/40 p-5">
        <p className="font-medium">We couldn&apos;t load your dashboard right now.</p>
        <p className="mt-1 text-sm text-muted-foreground">Please try again in a moment.</p>
        <Button className="mt-4" size="sm" variant="outline" onClick={() => refetch()}>
          Retry
        </Button>
      </div>
    );
  }

  const recommended = highPriority?.results[0];

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

      <section className="rounded-xl border border-primary/30 bg-primary/5 p-5 sm:p-6">
        <p className="text-sm font-medium text-primary">Recommended Kuzana opportunity</p>
        {!highPriority && <Skeleton className="mt-3 h-28 w-full" />}
        {recommended ? (
          <div className="mt-2 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-2xl space-y-2">
              <h2 className="text-xl font-semibold tracking-tight">{recommended.title}</h2>
              <p className="text-sm text-muted-foreground">
                {recommended.summary || "A newly scored opportunity worth reviewing today."}
              </p>
              <div className="flex flex-wrap gap-2 text-sm">
                <span>Opportunity {recommended.opportunity_score ?? "—"}/100</span>
                <span>· {recommended.source_count} sources</span>
                <span>· {recommended.source_freshness}</span>
                {recommended.best_audience && <span>· Best for {recommended.best_audience.replaceAll("_", " ")}</span>}
              </div>
            </div>
            <Button asChild>
              <Link href={`/trends/${recommended.slug}`}>
                Review and act <ArrowRightIcon />
              </Link>
            </Button>
          </div>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">
            We&apos;re still evaluating today&apos;s signals. Check the trend feed for the latest coverage.
          </p>
        )}
      </section>

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight">High-priority trends</h2>
            <Button asChild variant="ghost" size="sm">
              <Link href="/trends?high_priority=true">View all</Link>
            </Button>
          </div>
          {!highPriority && <div className="grid gap-4 sm:grid-cols-2"><Skeleton className="h-40 w-full" /><Skeleton className="h-40 w-full" /></div>}
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
