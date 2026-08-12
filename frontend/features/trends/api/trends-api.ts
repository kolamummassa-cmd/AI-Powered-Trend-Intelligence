import { apiClient } from "@/lib/api/client";

export interface Category {
  id: string;
  name: string;
  slug: string;
}

export const TREND_STAGES = ["emerging", "growing", "peaking", "declining"] as const;
export type TrendStage = (typeof TREND_STAGES)[number];

export const TREND_STAGE_LABELS: Record<TrendStage, string> = {
  emerging: "Emerging",
  growing: "Growing",
  peaking: "Peaking",
  declining: "Declining",
};

export interface TrendListItem {
  id: string;
  title: string;
  slug: string;
  category: Category | null;
  summary: string;
  status: "active" | "expiring" | "expired";
  estimated_lifespan: string;
  trend_score: number | null;
  opportunity_score: number | null;
  confidence_score: number | null;
  analyzed_at: string | null;
  first_detected_at: string;
  last_seen_at: string;
  platforms: string[];
  // Surfaced on the card itself, not just the detail page — best_audience
  // is an intelligence signal only (see TrendDetail's note below), never
  // a restriction on who can generate content about this trend.
  best_audience: AudienceType | "";
  trend_stage: TrendStage | "";
}

export interface TrendSourceLink {
  platform: string;
  platform_slug: string;
  source_url: string;
  created_at: string;
}

// The three personas the platform serves. Shared everywhere audience
// relevance / content perspective shows up (trend detail, Content
// Studio, the trends list filter) so labels stay consistent.
export const AUDIENCE_TYPES = ["content_creators", "founders", "investors"] as const;
export type AudienceType = (typeof AUDIENCE_TYPES)[number];

export const AUDIENCE_LABELS: Record<AudienceType, string> = {
  content_creators: "Content Creators",
  founders: "Founders",
  investors: "Investors",
};

export interface AudienceRelevance {
  content_creators: number;
  founders: number;
  investors: number;
}

export interface TrendAnalysis {
  business_relevance: string;
  founder_relevance: string;
  entrepreneurship_relevance: string;
  ai_relevance: string;
  trend_score: number;
  opportunity_score: number;
  confidence_score: number;
  content_creator_score: number;
  founder_score: number;
  investor_score: number;
  best_audience: AudienceType | "";
  why_it_matters: string;
  what_is_happening: string;
  trend_stage: TrendStage | "";
  suggested_content_angle: string;
  model_used: string;
  created_at: string;
}

export interface TrendDetail extends TrendListItem {
  why_spreading: string;
  source_links: TrendSourceLink[];
  latest_analysis: TrendAnalysis | null;
  // AUDIENCE RELEVANCE (per-persona scores) and BEST AUDIENCE (the
  // single derived label, inherited from TrendListItem) are
  // intentionally separate fields — see apps.trends.models.Trend's
  // docstring on the backend for why these must never be confused with
  // each other or with a user's chosen Content Perspective (which lives
  // on ContentBrief, not here).
  audience_relevance: AudienceRelevance | null;
  why_it_matters: string;
  what_is_happening: string;
  suggested_content_angle: string;
  created_at: string;
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
  high_priority?: boolean;
  audience?: AudienceType;
  stage?: TrendStage;
  ordering?: string;
  page?: number;
}

export async function fetchTrends(params: TrendListParams) {
  const { data } = await apiClient.get<PaginatedResponse<TrendListItem>>("/trends/", {
    params,
  });
  return data;
}

export async function fetchTrend(slug: string) {
  const { data } = await apiClient.get<TrendDetail>(`/trends/${slug}/`);
  return data;
}

export async function reanalyzeTrend(slug: string) {
  const { data } = await apiClient.post<{ detail: string }>(`/trends/${slug}/reanalyze/`);
  return data;
}
