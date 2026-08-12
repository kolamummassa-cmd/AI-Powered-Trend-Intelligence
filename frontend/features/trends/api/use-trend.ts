import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchTrend, reanalyzeTrend } from "@/features/trends/api/trends-api";

export function useTrend(slug: string) {
  return useQuery({
    queryKey: ["trend", slug],
    queryFn: () => fetchTrend(slug),
    enabled: Boolean(slug),
  });
}

export function useReanalyzeTrend(slug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => reanalyzeTrend(slug),
    onSuccess: () => {
      // In dev (CELERY_TASK_ALWAYS_EAGER) analysis has already run by
      // the time this resolves, so one refetch is enough. In a real
      // async deployment the task is still queued — refetch again
      // shortly after so the page catches up without a manual reload.
      queryClient.invalidateQueries({ queryKey: ["trend", slug] });
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["trend", slug] });
      }, 5000);
    },
  });
}
