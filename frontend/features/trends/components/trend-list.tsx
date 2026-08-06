"use client";

import { SearchIcon } from "lucide-react";
import { useState } from "react";

import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useTrends } from "@/features/trends/api/use-trends";
import { TrendCard } from "@/features/trends/components/trend-card";

const STATUS_OPTIONS = ["all", "active", "expiring", "expired"] as const;

export function TrendList() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<(typeof STATUS_OPTIONS)[number]>("all");

  const { data, isLoading, isError } = useTrends({
    search: search || undefined,
    status: status === "all" ? undefined : status,
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search trends..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as (typeof STATUS_OPTIONS)[number])}
          className="h-10 rounded-md border border-input bg-transparent px-3 text-sm"
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option} value={option} className="bg-card">
              {option === "all" ? "All statuses" : option}
            </option>
          ))}
        </select>
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      )}

      {isError && (
        <p className="text-sm text-danger">Could not load trends. Is the backend running?</p>
      )}

      {data && data.results.length === 0 && (
        <div className="rounded-lg border border-dashed border-border py-16 text-center">
          <p className="text-muted-foreground">
            No trends yet. Run <code className="text-foreground">seed_platforms</code> and a
            poll task to populate this list.
          </p>
        </div>
      )}

      {data && data.results.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.results.map((trend) => (
            <TrendCard key={trend.id} trend={trend} />
          ))}
        </div>
      )}
    </div>
  );
}
