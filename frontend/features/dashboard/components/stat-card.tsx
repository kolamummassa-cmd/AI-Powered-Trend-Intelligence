import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number | string;
  accent?: "default" | "success" | "warning";
}) {
  return (
    <Card
      className={cn(
        accent === "success" && "border-l-4 border-l-success",
        accent === "warning" && "border-l-4 border-l-warning",
        (!accent || accent === "default") && "border-l-4 border-l-primary",
      )}
    >
      <CardContent className="space-y-1 pt-6">
        <p className="text-sm font-semibold text-foreground">{label}</p>
        <p className="text-3xl font-semibold tracking-tight">{value}</p>
      </CardContent>
    </Card>
  );
}
