"use client";

import { RadarIcon } from "lucide-react";

import { useTrendingTicker } from "@/features/trends/api/use-trends";

// Live proof-of-product strip for the public landing page, modeled on
// Hootsuite's own "Trending Now — Powered by Lumen" ticker. Renders
// nothing until there's real data to show — no skeleton, no fake
// placeholder titles, since the entire point is that this is real.
export function TrendingTicker() {
  const { data, isLoading, isError } = useTrendingTicker();
  const titles = data?.titles ?? [];

  if (isLoading || isError || titles.length === 0) {
    return null;
  }

  // Duplicated once so the CSS animation (translateX -50%) loops seamlessly.
  const items = [...titles, ...titles];

  return (
    <div className="overflow-hidden border-b border-border bg-background py-2.5">
      <div className="trending-ticker-track">
        {[0, 1].map((copy) => (
          <div key={copy} className="flex shrink-0 items-center gap-8 pr-8" aria-hidden={copy === 1}>
            <span className="flex shrink-0 items-center gap-1.5 pl-4 text-xs font-semibold uppercase tracking-wide text-black dark:text-white">
              <RadarIcon className="size-3.5 text-primary" />
              Trending now
            </span>
            {items.map((title, i) => (
              <span key={`${copy}-${i}`} className="flex shrink-0 items-center gap-8 text-sm text-black dark:text-white">
                {title}
                <span className="text-black/20 dark:text-white/20">•</span>
              </span>
            ))}
            <span className="shrink-0 pr-4 text-xs text-muted-foreground">
              Powered by our AI trend engine
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
