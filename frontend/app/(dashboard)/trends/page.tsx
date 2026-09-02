import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { TrendList } from "@/features/trends/components/trend-list";

export default function TrendsPage() {
  return (
    <main className="flex flex-1 flex-col gap-6 p-4 sm:p-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Trends</h1>
        <p className="text-black/70 dark:text-white/70">
          Everything detected so far, across every connected source.
        </p>
      </div>
      <Suspense fallback={<Skeleton className="h-40 w-full" />}>
        <TrendList />
      </Suspense>
    </main>
  );
}
