import { useMutation, useQuery } from "@tanstack/react-query";

import { fetchTrend, reanalyzeTrend, submitTrendFeedback } from "@/features/trends/api/trends-api";

export function useTrend(slug: string) {
  return useQuery({
    queryKey: ["trend", slug],
    queryFn: () => fetchTrend(slug),
    enabled: Boolean(slug),
  });
}

export function useReanalyzeTrend(slug: string) {
  return useMutation({
    mutationFn: () => reanalyzeTrend(slug),
  });
}

export function useTrendFeedback(slug: string) {
  return useMutation({
    mutationFn: ({ isHelpful, comment }: { isHelpful: boolean; comment?: string }) =>
      submitTrendFeedback(slug, isHelpful, comment),
  });
}
