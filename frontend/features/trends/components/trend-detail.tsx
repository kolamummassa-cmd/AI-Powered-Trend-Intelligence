"use client";

import { ArrowLeftIcon, ExternalLinkIcon, RefreshCwIcon, ThumbsDownIcon, ThumbsUpIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ContentStudioPanel } from "@/features/content-studio/components/content-studio-panel";
import { useAIJob, useRetryAIJob } from "@/features/ai-jobs/api/use-ai-job";
import { AUDIENCE_LABELS, type AudienceType } from "@/features/trends/api/trends-api";
import { useReanalyzeTrend, useTrend, useTrendFeedback } from "@/features/trends/api/use-trend";
import { ScoreBar } from "@/features/trends/components/score-bar";

const STATUS_VARIANT = {
  active: "success",
  expiring: "warning",
  expired: "outline",
} as const;

const RELEVANCE_FIELDS = [
  { key: "business_relevance", label: "Business relevance" },
  { key: "founder_relevance", label: "Founder relevance" },
  { key: "entrepreneurship_relevance", label: "Entrepreneurship opportunity" },
  { key: "ai_relevance", label: "AI relevance" },
] as const;

const TREND_STAGE_VARIANT = {
  emerging: "outline",
  growing: "success",
  peaking: "warning",
  declining: "secondary",
} as const;

export function TrendDetail({ slug }: { slug: string }) {
  const { data: trend, isLoading, isError, refetch } = useTrend(slug);
  const reanalyze = useReanalyzeTrend(slug);
  const feedback = useTrendFeedback(slug);
  const [jobId, setJobId] = useState<string>();
  const { data: job } = useAIJob(jobId);
  const retryJob = useRetryAIJob();
  const queryClient = useQueryClient();
  const jobIsActive = job?.status === "queued" || job?.status === "running";

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
  const audienceHooks = [
    { audience: "founders" as const, copy: trend.founder_hook },
    { audience: "investors" as const, copy: trend.investor_hook },
    { audience: "content_creators" as const, copy: trend.creator_hook },
  ].filter(({ copy }) => Boolean(copy));
  const hasIntelligence = Boolean(
    trend.what_is_happening || trend.why_spreading || trend.estimated_lifespan || trend.trend_stage,
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Button asChild variant="ghost" size="sm" className="-ml-2">
          <Link href="/trends">
            <ArrowLeftIcon />
            Back to trends
          </Link>
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => reanalyze.mutate(undefined, { onSuccess: (nextJob) => setJobId(nextJob.id) })}
          disabled={reanalyze.isPending || jobIsActive}
        >
          <RefreshCwIcon className={reanalyze.isPending || jobIsActive ? "animate-spin" : undefined} />
          {reanalyze.isPending || jobIsActive ? "Queueing..." : analysis ? "Re-analyze" : "Analyze now"}
        </Button>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">{displayTitle}</h1>
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

      {trend.kuzana_relevance_score !== null && (
        <Card className="border-accent/30">
          <CardHeader><CardTitle className="text-base">Why Kuzana should cover this</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex flex-wrap gap-2">
              <Badge variant="accent">Kuzana relevance {trend.kuzana_relevance_score}/100</Badge>
              {trend.kuzana_theme && <Badge variant="outline">{trend.kuzana_theme.replaceAll("_", " ")}</Badge>}
              {trend.kuzana_geo_relevance && <Badge variant="outline">{trend.kuzana_geo_relevance.replaceAll("_", " ")}</Badge>}
              {trend.kuzana_content_format && <Badge variant="outline">{trend.kuzana_content_format}</Badge>}
            </div>
            {trend.kuzana_relevance_reason && <p>{trend.kuzana_relevance_reason}</p>}
            {trend.kuzana_audience && <p className="text-muted-foreground">Best for: {trend.kuzana_audience}</p>}
            {trend.kuzana_practical_takeaway && <p className="font-medium">Practical takeaway: {trend.kuzana_practical_takeaway}</p>}
          </CardContent>
        </Card>
      )}

      {audienceHooks.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Audience cues</CardTitle></CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">
            {audienceHooks.map(({ audience, copy }) => (
              <div key={audience} className="space-y-1 rounded-md border border-border p-3">
                <p className="text-sm font-medium">For {AUDIENCE_LABELS[audience]}</p>
                <p className="text-sm text-muted-foreground">{copy}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {trend.summary && (
        <p className="max-w-3xl break-words text-black/70 dark:text-white/70">{trend.summary}</p>
      )}

      <ContentStudioPanel trendSlug={trend.slug} bestAudience={trend.best_audience || undefined} />

      <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        <Badge variant={trend.source_freshness === "fresh" ? "success" : "outline"}>
          {trend.source_freshness}
        </Badge>
        <span>{trend.source_count} independent source{trend.source_count === 1 ? "" : "s"}</span>
        {trend.confidence_score !== null && <span>· AI confidence {trend.confidence_score}/100</span>}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <ScoreBar label="Trend score" score={trend.trend_score} />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <ScoreBar label="Opportunity score" score={trend.opportunity_score} />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <ScoreBar label="Confidence score" score={trend.confidence_score} />
          </CardContent>
        </Card>
      </div>

      {!analysis && (
        <p className="text-sm text-muted-foreground">
          AI analysis hasn&apos;t run for this trend yet — scores and explanations will appear
          here once it does. Use &quot;Analyze now&quot; above to run it immediately.
        </p>
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

      {trend.why_it_matters && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Why this matters</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-black/70 dark:text-white/70">{trend.why_it_matters}</p>
          </CardContent>
        </Card>
      )}

      {trend.action_summary && (
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader>
            <CardTitle className="text-base">Why this is worth acting on now</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-foreground">{trend.action_summary}</p>
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <span>Was this analysis useful?</span>
              <Button size="sm" variant="outline" disabled={feedback.isPending} onClick={() => feedback.mutate({ isHelpful: true })}>
                <ThumbsUpIcon /> Yes
              </Button>
              <Button size="sm" variant="outline" disabled={feedback.isPending} onClick={() => feedback.mutate({ isHelpful: false })}>
                <ThumbsDownIcon /> Not yet
              </Button>
              {feedback.isSuccess && <span className="text-success">Thanks—your feedback improves future analyses.</span>}
            </div>
          </CardContent>
        </Card>
      )}

      {hasIntelligence && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Trend intelligence</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {trend.what_is_happening && (
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">What&apos;s happening</p>
                <p className="text-sm text-black/70 dark:text-white/70">{trend.what_is_happening}</p>
              </div>
            )}
            {trend.why_spreading && (
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">Why it&apos;s spreading</p>
                <p className="text-sm text-black/70 dark:text-white/70">{trend.why_spreading}</p>
              </div>
            )}
            <div className="flex flex-wrap items-center gap-4">
              {trend.estimated_lifespan && (
                <p className="text-muted-foreground">
                  Estimated lifespan:{" "}
                  <span className="text-foreground">{trend.estimated_lifespan}</span>
                </p>
              )}
              {trend.trend_stage && (
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Trend stage:</span>
                  <Badge variant={TREND_STAGE_VARIANT[trend.trend_stage]}>
                    {trend.trend_stage}
                  </Badge>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {analysis && (
        <details className="rounded-lg border border-border bg-card">
          <summary className="cursor-pointer px-6 py-4 text-base font-semibold">AI relevance breakdown</summary>
          <Card className="border-0 shadow-none">
          <CardHeader>
            <CardTitle className="text-base">AI relevance breakdown</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            {RELEVANCE_FIELDS.map(({ key, label }) => (
              <div key={key} className="space-y-1">
                <p className="text-sm font-medium text-foreground">{label}</p>
                <p className="text-sm text-black/70 dark:text-white/70">{analysis[key]}</p>
              </div>
            ))}
          </CardContent>
          </Card>
        </details>
      )}

      <details className="rounded-lg border border-border bg-card">
        <summary className="cursor-pointer px-6 py-4 text-base font-semibold">Sources ({trend.source_links.length})</summary>
        <Card className="border-0 shadow-none">
          <CardContent className="space-y-2 pt-2">
          {trend.source_links.length === 0 && (
            <p className="text-sm text-muted-foreground">No sources recorded yet.</p>
          )}
          {trend.source_links.map((link) => (
            <div
              key={`${link.platform_slug}-${link.created_at}`}
              className="flex items-center justify-between gap-2 rounded-md border border-border px-3 py-2 text-sm"
            >
              <div className="flex items-center gap-2">
                <Badge variant="outline">{link.platform}</Badge>
                <span className="text-muted-foreground">
                  {new Date(link.created_at).toLocaleString()}
                </span>
                <span className="text-xs text-muted-foreground">
                  Credibility {link.credibility_weight}/100 · relevance {link.relevance_score}/100
                </span>
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
