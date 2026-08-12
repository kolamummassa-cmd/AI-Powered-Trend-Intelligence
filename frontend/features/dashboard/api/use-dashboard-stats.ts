import { useQuery } from "@tanstack/react-query";

import { fetchDashboardStats } from "@/features/dashboard/api/dashboard-api";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: fetchDashboardStats,
    refetchInterval: 60_000,
  });
}
