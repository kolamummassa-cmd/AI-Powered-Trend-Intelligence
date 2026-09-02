import { apiClient } from "@/lib/api/client";
import { type AIJob } from "@/features/ai-jobs/api/ai-jobs-api";

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
  // `title` is always the unmodified publisher/source headline. The
  // opportunity headline is optional, evidence-gated editorial framing.
  title: string;
  opportunity_headline: string;
  founder_hook: string;
  investor_hook: string;
  creator_hook: string;
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
  source_count: number;
  source_freshness: "fresh" | "recent" | "aging";
  // Surfaced on the card itself, not just the detail page — best_audience
  // is an intelligence signal only (see TrendDetail's note below), never
  // a restriction on who can generate content about this trend.
  best_audience: AudienceType | "";
  trend_stage: TrendStage | "";
  kuzana_relevance_score: number | null;
  kuzana_theme: string;
  kuzana_geo_relevance: string;
}

export interface TrendSourceLink {
  platform: string;
  platform_slug: string;
  source_url: string;
  published_at: string | null;
  credibility_weight: number;
  relevance_score: number;
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
  action_summary: string;
  kuzana_relevance_score: number;
  kuzana_relevance_reason: string;
  kuzana_theme: string;
  kuzana_geo_relevance: string;
  kuzana_audience: string;
  kuzana_content_format: string;
  kuzana_practical_takeaway: string;
  opportunity_headline: string;
  founder_hook: string;
  investor_hook: string;
  creator_hook: string;
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
  action_summary: string;
  kuzana_relevance_reason: string;
  kuzana_audience: string;
  kuzana_content_format: string;
  kuzana_practical_takeaway: string;
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
  kuzana_only?: boolean;
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
  const { data } = await apiClient.post<AIJob>(`/trends/${slug}/reanalyze/`);
  return data;
}

export async function submitTrendFeedback(slug: string, isHelpful: boolean, comment = "") {
  const { data } = await apiClient.post(`/trends/${slug}/feedback/`, {
    is_helpful: isHelpful,
    comment,
  });
  return data;
}

// Public, unauthenticated slice of live trend titles — powers the
// "Trending Now" ticker on the marketing landing page. Works whether
// or not the visitor is signed in.
export async function fetchTrendingTicker() {
  const { data } = await apiClient.get<{ titles: string[] }>("/trends/trending-ticker/");
  return data;
}
