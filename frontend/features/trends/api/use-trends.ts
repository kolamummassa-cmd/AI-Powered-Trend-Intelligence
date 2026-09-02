import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/features/auth/context/auth-context";
import { fetchTrendingTicker, fetchTrends, type TrendListParams } from "@/features/trends/api/trends-api";
import { shouldRetryRequest } from "@/lib/api/client";

export function useTrends(params: TrendListParams) {
  const { isAuthenticated, isLoading } = useAuth();
  return useQuery({
    queryKey: ["trends", params],
    queryFn: () => fetchTrends(params),
    placeholderData: (previous) => previous,
    enabled: !isLoading && isAuthenticated,
    retry: shouldRetryRequest,
  });
}

// Public landing page only — no auth required, safe to call before login.
export function useTrendingTicker() {
  return useQuery({
    queryKey: ["trending-ticker"],
    queryFn: fetchTrendingTicker,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}
