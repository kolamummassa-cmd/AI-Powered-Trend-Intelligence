import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type PlatformDistribution } from "@/features/dashboard/api/dashboard-api";

export function PlatformDistributionCard({ data }: { data: PlatformDistribution[] }) {
  const max = Math.max(1, ...data.map((row) => row.trend_count));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Trends by platform</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {data.length === 0 && (
          <p className="text-sm text-muted-foreground">
            We&apos;re setting up trend sources. Check back shortly.
          </p>
        )}
        {data.map((row) => (
          <div key={row.slug} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span>{row.name}</span>
              <span className="text-muted-foreground">{row.trend_count}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${(row.trend_count / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
