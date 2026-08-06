import { apiClient } from "@/lib/api/client";

export interface Category {
  id: string;
  name: string;
  slug: string;
}

export interface TrendListItem {
  id: string;
  title: string;
  slug: string;
  category: Category | null;
  summary: string;
  status: "active" | "expiring" | "expired";
  estimated_lifespan: string;
  first_detected_at: string;
  last_seen_at: string;
  platforms: string[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface TrendListParams {
  search?: string;
  category?: string;
  platform?: string;
  status?: string;
  page?: number;
}

export async function fetchTrends(params: TrendListParams) {
  const { data } = await apiClient.get<PaginatedResponse<TrendListItem>>("/trends/", {
    params,
  });
  return data;
}
