import { apiClient } from "@/lib/api/client";

export interface PlatformDistribution {
  slug: string;
  name: string;
  trend_count: number;
}

export interface DashboardStats {
  total_trends: number;
  active_trends: number;
  expiring_trends: number;
  new_today: number;
  high_priority_trends: number;
  analyzed_trends: number;
  platform_distribution: PlatformDistribution[];
}

export async function fetchDashboardStats() {
  const { data } = await apiClient.get<DashboardStats>("/trends/stats/");
  return data;
}
