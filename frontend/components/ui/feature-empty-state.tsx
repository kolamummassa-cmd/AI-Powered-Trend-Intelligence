import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface EmptyStateBenefit {
  icon: LucideIcon;
  title: string;
  description: string;
}

// Shared "nothing here yet" template — pill badge, bold black
// headline, short description, one action, then a row of benefit
// cards explaining what will show up once there's data. Modeled on
// Hootsuite's onboarding screens (Perch/Lumen/etc): every empty state
// in the app should feel designed, not like a placeholder.
export function FeatureEmptyState({
  badge,
  title,
  description,
  action,
  benefits,
}: {
  badge: string;
  title: ReactNode;
  description?: string;
  action?: ReactNode;
  benefits?: EmptyStateBenefit[];
}) {
  return (
    <div className="rounded-2xl border border-border bg-card p-8 sm:p-10">
      <Badge variant="accent" className="font-medium">
        {badge}
      </Badge>
      <h3 className="mt-4 max-w-xl text-2xl font-bold tracking-tight text-black dark:text-white">
        {title}
      </h3>
      {description && (
        <p className="mt-2 max-w-xl text-black/70 dark:text-white/70">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}

      {benefits && benefits.length > 0 && (
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {benefits.map((benefit) => (
            <Card key={benefit.title} className="border-border/70 bg-background/40">
              <CardHeader>
                <span className="flex size-9 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <benefit.icon className="size-4" />
                </span>
                <CardTitle className="mt-2 text-sm text-black dark:text-white">
                  {benefit.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-black/70 dark:text-white/70">{benefit.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
