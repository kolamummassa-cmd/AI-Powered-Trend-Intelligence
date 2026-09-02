import { type LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: number | string;
  icon: LucideIcon;
  accent?: "default" | "success" | "warning";
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between gap-4 pt-6">
        <div>
          <p className="text-sm text-black/70 dark:text-white/70">{label}</p>
          <p className="text-3xl font-semibold tracking-tight">{value}</p>
        </div>
        <div
          className={cn(
            "flex size-10 shrink-0 items-center justify-center rounded-full",
            accent === "success" && "bg-success/15 text-success",
            accent === "warning" && "bg-warning/15 text-warning",
            (!accent || accent === "default") && "bg-primary/10 text-primary",
          )}
        >
          <Icon className="size-5" />
        </div>
      </CardContent>
    </Card>
  );
}
