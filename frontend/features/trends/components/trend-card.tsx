import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type TrendListItem } from "@/features/trends/api/trends-api";

const STATUS_VARIANT = {
  active: "success",
  expiring: "warning",
  expired: "outline",
} as const;

// Not a link yet — the dedicated trend detail page (source timeline,
// AI explanation, scores) is a later phase. This card is Phase 2's
// proof that ingestion -> dedup -> API -> UI works end to end.
export function TrendCard({ trend }: { trend: TrendListItem }) {
  return (
    <Card>
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
      </CardContent>
    </Card>
  );
}
