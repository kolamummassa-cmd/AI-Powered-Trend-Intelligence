"use client";

import { ArrowLeftIcon, ExternalLinkIcon, RefreshCwIcon } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ContentStudioPanel } from "@/features/content-studio/components/content-studio-panel";
import { AUDIENCE_LABELS, type AudienceType } from "@/features/trends/api/trends-api";
import { useReanalyzeTrend, useTrend } from "@/features/trends/api/use-trend";
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
  const { data: trend, isLoading, isError } = useTrend(slug);
  const reanalyze = useReanalyzeTrend(slug);

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
        <Button asChild variant="outline" className="mt-4">
          <Link href="/trends">Back to trends</Link>
        </Button>
      </div>
    );
  }

  const analysis = trend.latest_analysis;
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
          onClick={() => reanalyze.mutate()}
          disabled={reanalyze.isPending}
        >
          <RefreshCwIcon className={reanalyze.isPending ? "animate-spin" : undefined} />
          {reanalyze.isPending ? "Analyzing..." : analysis ? "Re-analyze" : "Analyze now"}
        </Button>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">{trend.title}</h1>
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

      {trend.summary && <p className="max-w-3xl text-muted-foreground">{trend.summary}</p>}

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
            <p className="text-sm text-muted-foreground">{trend.why_it_matters}</p>
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
                <p className="text-sm text-muted-foreground">{trend.what_is_happening}</p>
              </div>
            )}
            {trend.why_spreading && (
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">Why it&apos;s spreading</p>
                <p className="text-sm text-muted-foreground">{trend.why_spreading}</p>
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
        <Card>
          <CardHeader>
            <CardTitle className="text-base">AI relevance breakdown</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            {RELEVANCE_FIELDS.map(({ key, label }) => (
              <div key={key} className="space-y-1">
                <p className="text-sm font-medium text-foreground">{label}</p>
                <p className="text-sm text-muted-foreground">{analysis[key]}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Sources ({trend.source_links.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
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
                <p className="text-sm text-muted-foreground">{trend.suggested_content_angle}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <ContentStudioPanel trendSlug={trend.slug} bestAudience={trend.best_audience || undefined} />
    </div>
  );
}
