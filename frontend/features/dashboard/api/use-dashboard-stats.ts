import { useQuery } from "@tanstack/react-query";

import { fetchDashboardStats } from "@/features/dashboard/api/dashboard-api";
import { useAuth } from "@/features/auth/context/auth-context";
import { shouldRetryRequest } from "@/lib/api/client";

export function useDashboardStats() {
  const { isAuthenticated, isLoading } = useAuth();
  return useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: fetchDashboardStats,
    refetchInterval: 60_000,
    enabled: !isLoading && isAuthenticated,
    retry: shouldRetryRequest,
  });
}
