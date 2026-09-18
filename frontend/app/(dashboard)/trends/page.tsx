import { Suspense } from "react";

import { PageIntro } from "@/components/ui/page-intro";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendList } from "@/features/trends/components/trend-list";

export default function TrendsPage() {
  return (
    <main className="flex flex-1 flex-col gap-6 p-4 sm:p-8">
      <PageIntro
        eyebrow="Signal discovery"
        title="Trends"
        description="Everything detected so far, across every connected source. Find the signals worth turning into action."
      />
      <Suspense fallback={<Skeleton className="h-40 w-full" />}>
        <TrendList />
      </Suspense>
    </main>
  );
}
