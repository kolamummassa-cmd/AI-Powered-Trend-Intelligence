"use client";

import { ArrowLeftIcon, ChevronDownIcon, ExternalLinkIcon, RefreshCwIcon, ThumbsDownIcon, ThumbsUpIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ContentStudioPanel } from "@/features/content-studio/components/content-studio-panel";
import { useAIJob, useRetryAIJob } from "@/features/ai-jobs/api/use-ai-job";
import { AUDIENCE_LABELS, type AudienceType, type TrendSourceLink } from "@/features/trends/api/trends-api";
import { useReanalyzeTrend, useTrend, useTrendFeedback } from "@/features/trends/api/use-trend";
import { ScoreBar } from "@/features/trends/components/score-bar";

const STATUS_VARIANT = {
  active: "success",
  expiring: "warning",
  expired: "outline",
} as const;

const RELEVANCE_FIELDS = [
  { key: "business_relevance", label: "For businesses" },
  { key: "founder_relevance", label: "For founders" },
  { key: "entrepreneurship_relevance", label: "Opportunity to explore" },
  { key: "ai_relevance", label: "Connection to AI" },
] as const;

const TREND_STAGE_VARIANT = {
  emerging: "outline",
  growing: "success",
  peaking: "warning",
  declining: "secondary",
} as const;

const EMPTY_ANALYSIS_VALUES = new Set(["", "-", "n/a", "na", "none", "null", "undefined"]);

function meaningfulText(value: string | null | undefined) {
  // Some earlier AI responses stored invisible zero-width characters or
  // placeholder words. Neither should create an empty-looking card.
  const text = (value ?? "").replace(/[\u200B-\u200F\u2060\uFEFF]/g, "").trim();
  return EMPTY_ANALYSIS_VALUES.has(text.toLowerCase()) ? "" : text;
}

export function TrendDetail({ slug }: { slug: string }) {
  const { data: trend, isLoading, isError, refetch } = useTrend(slug);
  const reanalyze = useReanalyzeTrend(slug);
  const feedback = useTrendFeedback(slug);
  const [jobId, setJobId] = useState<string>();
  const { data: job } = useAIJob(jobId);
  const retryJob = useRetryAIJob();
  const queryClient = useQueryClient();
  const jobIsActive = job?.status === "queued" || job?.status === "running";

  function requestAnalysis() {
    reanalyze.mutate(undefined, { onSuccess: (nextJob) => setJobId(nextJob.id) });
  }

  useEffect(() => {
    if (job?.status === "completed") {
      void queryClient.invalidateQueries({ queryKey: ["trend", slug] });
      void queryClient.invalidateQueries({ queryKey: ["trends"] });
    }
  }, [job?.status, queryClient, slug]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (isError || !trend) {
    return (
      <div className="rounded-lg border border-dashed border-border py-16 text-center">
        <p className="text-muted-foreground">Could not load this trend.</p>
        <div className="mt-4 flex justify-center gap-2">
        <Button variant="outline" onClick={() => refetch()}>Retry</Button>
        <Button asChild variant="outline">
          <Link href="/trends">Back to trends</Link>
        </Button>
        </div>
      </div>
    );
  }

  const analysis = trend.latest_analysis;
  const displayTitle = trend.opportunity_headline || trend.title;
  const intelligenceItems = [
    { label: "What’s happening", text: meaningfulText(trend.what_is_happening) },
    { label: "Why it’s spreading", text: meaningfulText(trend.why_spreading) },
    { label: "Why it matters", text: meaningfulText(trend.why_it_matters) },
  ].filter((item) => Boolean(item.text));
  const relevanceItems = analysis
    ? RELEVANCE_FIELDS.map(({ key, label }) => ({ label, text: meaningfulText(analysis[key]) })).filter(
        (item) => Boolean(item.text),
      )
    : [];
  const lifespan = meaningfulText(trend.estimated_lifespan);
  const hasLifecycle = Boolean(lifespan || trend.trend_stage);
  const hasAnalysisExplanation = intelligenceItems.length > 0 || relevanceItems.length > 0;
  const needsAnalysisExplanation = !analysis || !hasAnalysisExplanation;
  const overview = analysis || trend.analyzed_at
    ? meaningfulText(trend.what_is_happening) || meaningfulText(trend.summary)
    : meaningfulText(trend.source_excerpt) || meaningfulText(trend.summary);

  return (
    <div className="space-y-6 pb-6">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-4">
        <Button
          asChild
          variant="ghost"
          size="sm"
          className="border border-primary/60 bg-primary/5 text-foreground hover:bg-primary/10 hover:text-foreground"
        >
          <Link href="/trends">
            <ArrowLeftIcon />
            Back to trends
          </Link>
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="border-primary bg-primary/10 text-primary hover:bg-primary/20 hover:text-primary"
          onClick={requestAnalysis}
          disabled={reanalyze.isPending || jobIsActive}
        >
          <RefreshCwIcon className={reanalyze.isPending || jobIsActive ? "animate-spin" : undefined} />
          {reanalyze.isPending || jobIsActive ? "Queueing..." : analysis ? "Re-analyze" : "Analyze now"}
        </Button>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-4xl">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold tabular-nums text-muted-foreground">01</span>
            <h1 className="text-3xl font-semibold tracking-[-0.035em] sm:text-4xl">{displayTitle}</h1>
            <Badge variant={STATUS_VARIANT[trend.status]}>{trend.status}</Badge>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {trend.category && <Badge variant="secondary">{trend.category.name}</Badge>}
            {trend.platforms.map((platform) => (
              <Badge key={platform} variant="outline">
                {platform}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {trend.opportunity_headline && (
        <p className="-mt-3 text-sm text-muted-foreground">
          Original source headline: {trend.title}
        </p>
      )}

      {overview && (
        <p className="max-w-3xl break-words text-base leading-6 text-muted-foreground">{overview}</p>
      )}

      <SourceEvidence links={trend.source_links} />

      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <ContentStudioPanel trendSlug={trend.slug} bestAudience={trend.best_audience || undefined} />

        <aside className="rounded-2xl border border-accent/25 bg-linear-to-br from-accent/12 via-card to-sky-500/8 p-5 shadow-sm transition-shadow hover:shadow-md sm:p-6">
          <div className="flex items-baseline justify-between gap-3">
            <h2 className="text-xl font-semibold tracking-tight">Evidence scores</h2>
            <span className="text-xs font-medium tracking-[0.2em] text-muted-foreground">03</span>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">
            A clear view of how strong, actionable, and well-supported this trend is.
          </p>
          <div className="mt-6 space-y-5 rounded-xl border border-accent/20 bg-card/85 p-4">
            <ScoreBar label="Trend strength" score={trend.trend_score} />
            <ScoreBar label="Opportunity to act" score={trend.opportunity_score} />
            <ScoreBar label="Evidence confidence" score={trend.confidence_score} />
          </div>
          <div className="mt-4 rounded-lg border border-accent/20 bg-background/70 p-3 text-xs leading-5 text-muted-foreground">
            {analysis
              ? `${trend.source_count} independent source${trend.source_count === 1 ? "" : "s"} · ${trend.source_freshness} evidence.`
              : "No analysis yet. Select Analyze now to calculate these scores from the available sources."}
          </div>
        </aside>
      </div>

      {needsAnalysisExplanation && (
        <Card className="border-dashed border-primary/50 bg-primary/5">
          <CardHeader>
            <CardTitle className="text-base">Detailed analysis is not ready yet</CardTitle>
            <p className="text-sm text-muted-foreground">
              Run analysis to see a plain explanation of what is happening, why it matters, and who can act on it.
            </p>
          </CardHeader>
          <CardContent>
            <Button size="sm" onClick={requestAnalysis} disabled={reanalyze.isPending || jobIsActive}>
              <RefreshCwIcon className={reanalyze.isPending || jobIsActive ? "animate-spin" : undefined} />
              {reanalyze.isPending || jobIsActive ? "Queueing..." : "Analyze this trend"}
            </Button>
          </CardContent>
        </Card>
      )}

      {reanalyze.isError && (
        <p className="text-sm text-danger">
          Could not queue analysis. Check that an AI provider key is configured.
        </p>
      )}

      {job && (
        <div className="rounded-md border border-border bg-muted/50 p-3 text-sm" role="status">
          {job.status === "queued" && "Analysis is queued."}
          {job.status === "running" && "AI is analyzing this trend…"}
          {job.status === "completed" && "Analysis complete — the trend details have refreshed."}
          {job.status === "failed" && (
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span>Analysis failed: {job.error_message || "Please try again."}</span>
              {job.can_retry && <Button size="sm" variant="outline" onClick={() => retryJob.mutate(job.id, { onSuccess: (nextJob) => setJobId(nextJob.id) })}>Retry</Button>}
            </div>
          )}
        </div>
      )}

      {trend.audience_relevance && (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle className="text-base">Audience relevance</CardTitle>
              {trend.best_audience && (
                <Badge variant="accent">
                  Best audience: {AUDIENCE_LABELS[trend.best_audience as AudienceType]}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <ScoreBar
              label="Content Creators"
              score={trend.audience_relevance.content_creators}
            />
            <ScoreBar label="Founders" score={trend.audience_relevance.founders} />
            <ScoreBar label="Investors" score={trend.audience_relevance.investors} />
            <p className="text-xs text-muted-foreground">
              Best audience is an intelligence signal only — anyone can create content about this
              trend from any perspective in Content Studio below.
            </p>
          </CardContent>
        </Card>
      )}

      {trend.action_summary && (
        <Card className="overflow-hidden border-slate-700 bg-linear-to-br from-slate-950 via-slate-900 to-primary/55 text-slate-50">
          <CardHeader>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-warning">Decision brief</p>
            <CardTitle className="text-xl text-white">Why this is worth acting on now</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <p className="max-w-4xl text-sm leading-6 text-slate-200">{trend.action_summary}</p>
            <div className="grid gap-2 sm:grid-cols-3">
              <DecisionMetric label="Opportunity" value={trend.opportunity_score} />
              <DecisionMetric label="Confidence" value={trend.confidence_score} />
              <DecisionMetric label="Sources" value={trend.source_count} suffix="" />
            </div>
            <div className="flex flex-wrap items-center gap-2 border-t border-white/10 pt-4 text-sm text-slate-300">
              <span>Was this analysis useful?</span>
              <Button size="sm" variant="outline" disabled={feedback.isPending} onClick={() => feedback.mutate({ isHelpful: true })}>
                <ThumbsUpIcon /> Yes
              </Button>
              <Button size="sm" variant="outline" disabled={feedback.isPending} onClick={() => feedback.mutate({ isHelpful: false })}>
                <ThumbsDownIcon /> Not yet
              </Button>
              {feedback.isSuccess && <span className="text-emerald-300">Thanks—your feedback improves future analyses.</span>}
            </div>
          </CardContent>
        </Card>
      )}

      {(intelligenceItems.length > 0 || hasLifecycle) && (
        <Card className="border-accent/20 bg-linear-to-br from-accent/12 via-card to-sky-500/6">
          <CardHeader>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent-foreground">The signal in plain language</p>
            <CardTitle className="text-xl">Trend intelligence</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm md:grid-cols-3">
            {intelligenceItems.map(({ label, text }, index) => (
              <div key={label} className="rounded-xl border border-accent/15 bg-card/85 p-4">
                <p className="text-xs font-semibold tracking-[0.16em] text-accent-foreground">0{index + 1}</p>
                <p className="mt-3 text-base font-semibold text-foreground">{label}</p>
                <p className="mt-2 leading-6 text-black/70 dark:text-white/70">{text}</p>
              </div>
            ))}
            {hasLifecycle && (
              <div className="rounded-xl border border-accent/15 bg-card/85 p-4">
                <p className="text-xs font-semibold tracking-[0.16em] text-accent-foreground">0{intelligenceItems.length + 1}</p>
                <p className="mt-3 text-base font-semibold text-foreground">Trend timing</p>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-sm">
                  {lifespan && (
                    <p className="rounded-full bg-accent/10 px-3 py-1.5 text-muted-foreground">
                      Lifespan: <span className="font-medium text-foreground">{lifespan}</span>
                    </p>
                  )}
                  {trend.trend_stage && (
                    <div className="flex items-center gap-2 rounded-full bg-accent/10 px-3 py-1.5">
                      <span className="text-muted-foreground">Stage</span>
                      <Badge variant={TREND_STAGE_VARIANT[trend.trend_stage]}>
                        {trend.trend_stage}
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {relevanceItems.length > 0 && (
        <Card className="border-primary/15 bg-linear-to-br from-primary/7 via-card to-warning/5">
          <CardHeader>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Find your angle</p>
            <CardTitle className="text-xl">Practical perspectives</CardTitle>
            <p className="text-sm text-muted-foreground">
              AI-generated explanations of how this trend could matter to different people.
            </p>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {relevanceItems.map(({ label, text }, index) => (
              <div key={label} className="rounded-xl border border-primary/15 bg-card/85 p-4">
                <p className="text-xs font-semibold tracking-[0.16em] text-primary">PERSPECTIVE 0{index + 1}</p>
                <p className="mt-2 text-base font-semibold text-foreground">{label}</p>
                <p className="mt-2 leading-6 text-black/70 dark:text-white/70">{text}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {(trend.best_audience || trend.suggested_content_angle) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Content opportunity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {trend.best_audience && (
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">Best audience</p>
                <Badge variant="accent">
                  {AUDIENCE_LABELS[trend.best_audience as AudienceType]}
                </Badge>
              </div>
            )}
            {trend.suggested_content_angle && (
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">Suggested content angle</p>
                <p className="text-sm text-black/70 dark:text-white/70">{trend.suggested_content_angle}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

    </div>
  );
}

function SourceEvidence({ links }: { links: TrendSourceLink[] }) {
  return (
    <details className="group rounded-xl border border-primary/20 bg-card shadow-sm transition-shadow hover:shadow-md">
      <summary className="flex cursor-pointer items-center justify-between gap-3 px-6 py-4">
        <span className="text-base font-semibold">Source evidence</span>
        <span className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <span className="group-open:hidden">Show sources</span>
          <span className="hidden group-open:inline">Hide sources</span>
          <span className="tracking-[0.2em]">{links.length} · 04</span>
          <ChevronDownIcon className="size-4 transition-transform duration-150 group-open:rotate-180" aria-hidden="true" />
        </span>
      </summary>
      <Card className="border-0 shadow-none">
        <CardContent className="space-y-2 pt-2">
          {links.length === 0 && (
            <p className="text-sm text-muted-foreground">No sources recorded yet.</p>
          )}
          {links.map((link) => (
            <div
              key={`${link.platform_slug}-${link.created_at}`}
              className="flex items-center justify-between gap-2 rounded-md border border-primary/20 px-3 py-2 text-sm"
            >
              <div className="min-w-0 space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{link.platform}</Badge>
                  <span className="text-xs text-muted-foreground">{new Date(link.created_at).toLocaleString()}</span>
                  <span className="text-xs text-muted-foreground">
                    Credibility {link.credibility_weight}/100 · relevance {link.relevance_score}/100
                  </span>
                </div>
                <p className="truncate text-sm font-medium text-foreground">{link.source_title}</p>
              </div>
              {link.source_url && (
                <a
                  href={link.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-primary hover:underline"
                >
                  View <ExternalLinkIcon className="size-3.5" />
                </a>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </details>
  );
}

function DecisionMetric({
  label,
  value,
  suffix = "/100",
}: {
  label: string;
  value: number | null;
  suffix?: string;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/8 px-4 py-3">
      <p className="text-xs font-medium text-slate-300">{label}</p>
      <p className="mt-1 text-lg font-semibold text-white">
        {value ?? "—"}
        {value !== null && <span className="ml-0.5 text-sm font-medium text-slate-300">{suffix}</span>}
      </p>
    </div>
  );
}
