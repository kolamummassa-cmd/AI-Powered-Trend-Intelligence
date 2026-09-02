import { useMutation, useQuery } from "@tanstack/react-query";

import { fetchAIJob, retryAIJob } from "@/features/ai-jobs/api/ai-jobs-api";

export function useAIJob(jobId?: string) {
  return useQuery({
    queryKey: ["ai-job", jobId],
    queryFn: () => fetchAIJob(jobId!),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 1500 : false;
    },
  });
}

export function useRetryAIJob() {
  return useMutation({ mutationFn: retryAIJob });
}
