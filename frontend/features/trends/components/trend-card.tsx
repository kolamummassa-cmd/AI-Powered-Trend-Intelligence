import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AUDIENCE_LABELS,
  TREND_STAGE_LABELS,
  type TrendListItem,
} from "@/features/trends/api/trends-api";

const STATUS_VARIANT = {
  active: "success",
  expiring: "warning",
  expired: "outline",
} as const;

const STAGE_VARIANT = {
  emerging: "outline",
  growing: "success",
  peaking: "warning",
  declining: "secondary",
} as const;

// Links through to the dedicated trend detail page (source timeline,
// AI explanation, scores) added in Phase 3.
export function TrendCard({ trend }: { trend: TrendListItem }) {
  const displayTitle = trend.opportunity_headline || trend.title;
  const audienceCue = trend.best_audience === "founders"
    ? trend.founder_hook
    : trend.best_audience === "investors"
      ? trend.investor_hook
      : trend.best_audience === "content_creators"
        ? trend.creator_hook
        : "";
  const audienceLabel = trend.best_audience
    ? AUDIENCE_LABELS[trend.best_audience]
    : "";
  const preview = trend.analyzed_at
    ? trend.what_is_happening || trend.summary
    : trend.source_excerpt || trend.summary;

  return (
    <Link href={`/trends/${trend.slug}`} className="block">
      <Card className="h-full border-border shadow-sm transition-[border-color,box-shadow,transform] hover:-translate-y-0.5 hover:border-primary/35 hover:shadow-md">
        <CardHeader>
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base">{displayTitle}</CardTitle>
            <Badge variant={STATUS_VARIANT[trend.status]}>{trend.status}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {preview && (
            <p className="line-clamp-2 break-words text-sm text-black/70 dark:text-white/70">
              {preview}
            </p>
          )}
          {audienceCue && (
            <p className="line-clamp-2 text-sm font-medium text-foreground/80">
              For {audienceLabel}: {audienceCue}
            </p>
          )}
          {trend.opportunity_headline && (
            <p className="line-clamp-1 text-xs text-muted-foreground">
              Source: {trend.title}
            </p>
          )}
          <div className="flex flex-wrap items-center gap-2">
            {trend.signal_areas.map((area) => (
              <Badge key={area} variant="default">{area}</Badge>
            ))}
            {trend.category && <Badge variant="secondary">{trend.category.name}</Badge>}
            {trend.platforms.map((platform) => (
              <Badge key={platform} variant="outline">
                {platform}
              </Badge>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            {trend.source_count} source{trend.source_count === 1 ? "" : "s"} · {trend.source_freshness}
          </p>
          {(trend.best_audience || trend.trend_stage) && (
            <div className="flex flex-wrap items-center gap-2">
              {trend.best_audience && (
                <Badge variant="accent">Best for {AUDIENCE_LABELS[trend.best_audience]}</Badge>
              )}
              {trend.trend_stage && (
                <Badge variant={STAGE_VARIANT[trend.trend_stage]}>
                  {TREND_STAGE_LABELS[trend.trend_stage]}
                </Badge>
              )}
            </div>
          )}
          {trend.trend_score !== null && (
            <p className="text-xs text-muted-foreground">
              Trend score <span className="font-medium text-foreground">{trend.trend_score}</span>
              {trend.opportunity_score !== null && (
                <>
                  {" "}
                  · Opportunity{" "}
                  <span className="font-medium text-foreground">{trend.opportunity_score}</span>
                </>
              )}
            </p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
