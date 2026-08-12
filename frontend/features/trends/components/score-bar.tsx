import { cn } from "@/lib/utils";

// Shared 0-100 score visualization for trend/opportunity/confidence
// scores. Color intent (danger/warning/success) is decoupled from the
// raw number so we can tune the thresholds in one place.
function scoreVariant(score: number) {
  if (score >= 70) return "bg-success";
  if (score >= 40) return "bg-warning";
  return "bg-danger";
}

export function ScoreBar({
  label,
  score,
  className,
}: {
  label: string;
  score: number | null;
  className?: string;
}) {
  const hasScore = score !== null && score !== undefined;

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium text-foreground">{hasScore ? score : "—"}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        {hasScore && (
          <div
            className={cn("h-full rounded-full transition-all", scoreVariant(score))}
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        )}
      </div>
    </div>
  );
}
