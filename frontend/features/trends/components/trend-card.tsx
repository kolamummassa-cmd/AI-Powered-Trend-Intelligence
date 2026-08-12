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
  return (
    <Link href={`/trends/${trend.slug}`} className="block">
      <Card className="h-full transition-colors hover:border-primary/50">
        <CardHeader>
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base">{trend.title}</CardTitle>
            <Badge variant={STATUS_VARIANT[trend.status]}>{trend.status}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {trend.summary && (
            <p className="line-clamp-2 text-sm text-muted-foreground">{trend.summary}</p>
          )}
          <div className="flex flex-wrap items-center gap-2">
            {trend.category && <Badge variant="secondary">{trend.category.name}</Badge>}
            {trend.platforms.map((platform) => (
              <Badge key={platform} variant="outline">
                {platform}
              </Badge>
            ))}
          </div>
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
