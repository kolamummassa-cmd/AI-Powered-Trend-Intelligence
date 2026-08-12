"use client";

import { SearchIcon } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useState } from "react";

import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AUDIENCE_LABELS,
  AUDIENCE_TYPES,
  TREND_STAGE_LABELS,
  TREND_STAGES,
  type AudienceType,
  type TrendStage,
} from "@/features/trends/api/trends-api";
import { useTrends } from "@/features/trends/api/use-trends";
import { TrendCard } from "@/features/trends/components/trend-card";

const STATUS_OPTIONS = ["all", "active", "expiring", "expired"] as const;
// "All Audiences" is just omitting the filter — there is one unified
// trends feed regardless of which audience is selected here.
const AUDIENCE_OPTIONS = ["all", ...AUDIENCE_TYPES] as const;
const STAGE_OPTIONS = ["all", ...TREND_STAGES] as const;

export function TrendList() {
  const searchParams = useSearchParams();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<(typeof STATUS_OPTIONS)[number]>("all");
  const [audience, setAudience] = useState<(typeof AUDIENCE_OPTIONS)[number]>("all");
  const [stage, setStage] = useState<(typeof STAGE_OPTIONS)[number]>("all");
  const [highPriorityOnly, setHighPriorityOnly] = useState(
    searchParams.get("high_priority") === "true",
  );

  const { data, isLoading, isError } = useTrends({
    search: search || undefined,
    status: status === "all" ? undefined : status,
    audience: audience === "all" ? undefined : (audience as AudienceType),
    stage: stage === "all" ? undefined : (stage as TrendStage),
    high_priority: highPriorityOnly || undefined,
  });

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Trends are collected, deduplicated and scored automatically in the background — nothing
        here requires you to trigger a run.
      </p>
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
        <select
          value={audience}
          onChange={(e) => setAudience(e.target.value as (typeof AUDIENCE_OPTIONS)[number])}
          className="h-10 rounded-md border border-input bg-transparent px-3 text-sm"
        >
          {AUDIENCE_OPTIONS.map((option) => (
            <option key={option} value={option} className="bg-card">
              {option === "all" ? "All audiences" : AUDIENCE_LABELS[option]}
            </option>
          ))}
        </select>
        <select
          value={stage}
          onChange={(e) => setStage(e.target.value as (typeof STAGE_OPTIONS)[number])}
          className="h-10 rounded-md border border-input bg-transparent px-3 text-sm"
        >
          {STAGE_OPTIONS.map((option) => (
            <option key={option} value={option} className="bg-card">
              {option === "all" ? "Any stage" : TREND_STAGE_LABELS[option]}
            </option>
          ))}
        </select>
        <label className="flex h-10 items-center gap-2 rounded-md border border-input px-3 text-sm">
          <input
            type="checkbox"
            checked={highPriorityOnly}
            onChange={(e) => setHighPriorityOnly(e.target.checked)}
          />
          High priority only
        </label>
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
            We&apos;re scanning the latest conversations for relevant trends. New insights will
            appear here automatically.
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
