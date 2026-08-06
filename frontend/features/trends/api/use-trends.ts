import { useQuery } from "@tanstack/react-query";

import { fetchTrends, type TrendListParams } from "@/features/trends/api/trends-api";

export function useTrends(params: TrendListParams) {
  return useQuery({
    queryKey: ["trends", params],
    queryFn: () => fetchTrends(params),
    placeholderData: (previous) => previous,
  });
}
