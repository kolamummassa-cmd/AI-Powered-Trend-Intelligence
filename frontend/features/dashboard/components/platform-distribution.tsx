import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type PlatformDistribution } from "@/features/dashboard/api/dashboard-api";

export function PlatformDistributionCard({ data }: { data: PlatformDistribution[] }) {
  const coreSources = data.filter((row) => row.kuzana_priority_weight >= 80);
  const globalSources = data.filter((row) => row.kuzana_priority_weight < 80);
  const coreCount = coreSources.reduce((total, row) => total + row.trend_count, 0);
  const globalCount = globalSources.reduce((total, row) => total + row.trend_count, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Kuzana source coverage</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {data.length === 0 && (
          <p className="text-sm text-muted-foreground">
            We&apos;re setting up trend sources. Check back shortly.
          </p>
        )}
        {data.length > 0 && (
          <>
            <div className="rounded-md border border-accent/30 bg-accent/5 p-3 text-sm">
              <p className="font-medium">Kuzana core</p>
              <p className="mt-1 text-muted-foreground">
                {coreSources.length} source{coreSources.length === 1 ? "" : "s"} · {coreCount} trend{coreCount === 1 ? "" : "s"}
              </p>
            </div>
            <SourceRows rows={coreSources} emptyMessage="No Kuzana-core sources are active yet." />
            <details className="rounded-md border border-border p-3">
              <summary className="cursor-pointer text-sm font-medium">
                Global signal sources · {globalSources.length} source{globalSources.length === 1 ? "" : "s"} · {globalCount} trends
              </summary>
              <div className="mt-3">
                <SourceRows rows={globalSources} emptyMessage="No global signal sources are active." />
              </div>
            </details>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function SourceRows({ rows, emptyMessage }: { rows: PlatformDistribution[]; emptyMessage: string }) {
  const max = Math.max(1, ...rows.map((row) => row.trend_count));
  if (rows.length === 0) return <p className="text-sm text-muted-foreground">{emptyMessage}</p>;
  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <div key={row.slug} className="space-y-1">
          <div className="flex items-center justify-between gap-2 text-sm">
            <span>{row.name}</span>
            <span className="shrink-0 text-muted-foreground">{row.trend_count}</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-primary" style={{ width: `${(row.trend_count / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
