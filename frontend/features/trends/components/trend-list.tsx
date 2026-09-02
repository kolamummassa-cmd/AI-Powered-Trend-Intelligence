"use client";

import { SearchIcon } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { FeatureEmptyState } from "@/components/ui/feature-empty-state";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AUDIENCE_LABELS, AUDIENCE_TYPES, TREND_STAGE_LABELS, TREND_STAGES,
  type AudienceType, type TrendStage,
} from "@/features/trends/api/trends-api";
import { useTrends } from "@/features/trends/api/use-trends";
import { TrendCard } from "@/features/trends/components/trend-card";

const STATUS_OPTIONS = ["all", "active", "expiring", "expired"] as const;
const AUDIENCE_OPTIONS = ["all", ...AUDIENCE_TYPES] as const;
const STAGE_OPTIONS = ["all", ...TREND_STAGES] as const;

export function TrendList() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [status, setStatus] = useState<(typeof STATUS_OPTIONS)[number]>((searchParams.get("status") as (typeof STATUS_OPTIONS)[number]) || "all");
  const [audience, setAudience] = useState<(typeof AUDIENCE_OPTIONS)[number]>((searchParams.get("audience") as (typeof AUDIENCE_OPTIONS)[number]) || "all");
  const [stage, setStage] = useState<(typeof STAGE_OPTIONS)[number]>((searchParams.get("stage") as (typeof STAGE_OPTIONS)[number]) || "all");
  const [highPriorityOnly, setHighPriorityOnly] = useState(searchParams.get("high_priority") === "true");
  const [kuzanaOnly, setKuzanaOnly] = useState(searchParams.get("kuzana_only") === "true");
  const [page, setPage] = useState(Number(searchParams.get("page")) || 1);
  const [debouncedSearch, setDebouncedSearch] = useState(search);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (debouncedSearch) params.set("search", debouncedSearch);
    if (status !== "all") params.set("status", status);
    if (audience !== "all") params.set("audience", audience);
    if (stage !== "all") params.set("stage", stage);
    if (highPriorityOnly) params.set("high_priority", "true");
    if (kuzanaOnly) params.set("kuzana_only", "true");
    if (page > 1) params.set("page", String(page));
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }, [audience, debouncedSearch, highPriorityOnly, kuzanaOnly, page, pathname, router, stage, status]);

  const { data, isLoading, isFetching, isError, refetch } = useTrends({
    search: debouncedSearch || undefined,
    status: status === "all" ? undefined : status,
    audience: audience === "all" ? undefined : (audience as AudienceType),
    stage: stage === "all" ? undefined : (stage as TrendStage),
    high_priority: highPriorityOnly || undefined,
    kuzana_only: kuzanaOnly || undefined,
    page,
  });
  const resetPage = () => setPage(1);

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Find an opportunity, understand the evidence, then take action.</p>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1"><SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input placeholder="Search trends..." value={search} onChange={(e) => { setSearch(e.target.value); resetPage(); }} className="border-primary/60 pl-9" /></div>
        <select value={status} onChange={(e) => { setStatus(e.target.value as typeof status); resetPage(); }} className="h-10 w-full rounded-md border border-primary/60 bg-transparent px-3 text-sm sm:w-auto">{STATUS_OPTIONS.map((option) => <option key={option} value={option} className="bg-card">{option === "all" ? "All statuses" : option}</option>)}</select>
        <select value={audience} onChange={(e) => { setAudience(e.target.value as typeof audience); resetPage(); }} className="h-10 w-full rounded-md border border-primary/60 bg-transparent px-3 text-sm sm:w-auto">{AUDIENCE_OPTIONS.map((option) => <option key={option} value={option} className="bg-card">{option === "all" ? "All audiences" : AUDIENCE_LABELS[option]}</option>)}</select>
        <select value={stage} onChange={(e) => { setStage(e.target.value as typeof stage); resetPage(); }} className="h-10 w-full rounded-md border border-primary/60 bg-transparent px-3 text-sm sm:w-auto">{STAGE_OPTIONS.map((option) => <option key={option} value={option} className="bg-card">{option === "all" ? "Any stage" : TREND_STAGE_LABELS[option]}</option>)}</select>
        <label className="flex h-10 w-full items-center gap-2 rounded-md border border-primary/60 px-3 text-sm sm:w-auto"><input type="checkbox" checked={highPriorityOnly} onChange={(e) => { setHighPriorityOnly(e.target.checked); resetPage(); }} />High priority</label>
        <label className="flex h-10 w-full items-center gap-2 rounded-md border border-primary/60 px-3 text-sm sm:w-auto"><input type="checkbox" checked={kuzanaOnly} onChange={(e) => { setKuzanaOnly(e.target.checked); resetPage(); }} />Kuzana relevant</label>
      </div>
      {data && <p className="text-sm text-muted-foreground">{data.count} result{data.count === 1 ? "" : "s"} found{isFetching ? " · Updating…" : ""}</p>}
      {isLoading && <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-40 w-full" />)}</div>}
      {isError && <div className="rounded-lg border border-border bg-muted/40 p-5"><p className="font-medium">We couldn&apos;t load trends right now.</p><p className="mt-1 text-sm text-muted-foreground">Your filters are still saved. Please try again.</p><Button className="mt-4" size="sm" variant="outline" onClick={() => refetch()}>Retry</Button></div>}
      {data && data.results.length === 0 && <FeatureEmptyState badge="Trend engine" title="No matching trends yet." description="Try broadening your search or filters. New signals are added automatically as they are verified." benefits={[{ title: "1. Collect signals", description: "Sources are scanned continuously." }, { title: "2. Analyze opportunities", description: "Every useful signal is scored." }, { title: "3. Turn a trend into content", description: "Generate a brief when a relevant trend appears." }]} />}
      {data && data.results.length > 0 && <><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{data.results.map((trend) => <TrendCard key={trend.id} trend={trend} />)}</div><div className="flex items-center justify-between"><Button variant="outline" disabled={!data.previous || isFetching} onClick={() => setPage((value) => Math.max(1, value - 1))}>Previous</Button><span className="text-sm text-muted-foreground">Page {page}</span><Button variant="outline" disabled={!data.next || isFetching} onClick={() => setPage((value) => value + 1)}>Next</Button></div></>}
    </div>
  );
}
