import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";

export interface HealthCheckResponse {
  status: "ok" | "degraded";
  database: "ok" | "unavailable";
}

async function fetchHealth(): Promise<HealthCheckResponse> {
  const { data } = await apiClient.get<HealthCheckResponse>("/health/");
  return data;
}

/**
 * Polls the backend health endpoint. Used today only to prove the
 * frontend and backend are actually wired together end to end; the
 * dashboard's real widgets (Phase 4) will follow this same
 * feature/api/hook pattern.
 */
export function useHealthCheck() {
  return useQuery({
    queryKey: ["system-health"],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  });
}
