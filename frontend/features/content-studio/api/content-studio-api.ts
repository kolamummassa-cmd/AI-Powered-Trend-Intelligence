import { apiClient } from "@/lib/api/client";
import { type AIJob } from "@/features/ai-jobs/api/ai-jobs-api";
import { type AudienceType, type PaginatedResponse } from "@/features/trends/api/trends-api";

export const CONTENT_TYPES = [
  "hook",
  "script_30",
  "post",
  "script_60",
  "cta",
  "hashtags",
  "thumbnail_suggestion",
  "remix_template",
] as const;

export type ContentType = (typeof CONTENT_TYPES)[number];

export const CONTENT_TYPE_LABELS: Record<ContentType, string> = {
  hook: "Hook",
  script_30: "30s script",
  post: "Post",
  script_60: "60s script",
  cta: "Call to action",
  hashtags: "Hashtags",
  thumbnail_suggestion: "Thumbnail suggestion",
  remix_template: "Remix template",
};

// These are written for someone deciding what to create, not for a marketer.
// They make it clear that each generated item has a different job.
export const CONTENT_TYPE_DESCRIPTIONS: Record<ContentType, string> = {
  hook: "Three opening lines designed to make people stop and listen.",
  script_30: "A short video script for a video of about 30 seconds.",
  post: "A ready-to-edit written post for LinkedIn, X, or another social platform.",
  script_60: "A fuller video script for a video of about one minute.",
  cta: "Short closing lines that tell the audience what to do next.",
  hashtags: "Searchable topic labels that help the right people find the post.",
  thumbnail_suggestion: "An idea for the cover image and headline people see before opening a video.",
  remix_template: "A repeatable content format you or other creators can adapt to similar trends.",
};

export interface GeneratedContent {
  id: string;
  brief: string;
  trend_title: string;
  trend_slug: string;
  perspective: AudienceType | "";
  brief_context: string;
  content_type: ContentType;
  body: string;
  version: number;
  is_saved: boolean;
  model_used: string;
  created_at: string;
}

export interface ContentBrief {
  id: string;
  trend: string;
  trend_title: string;
  trend_slug: string;
  business_angle: string;
  founder_angle: string;
  educational_angle: string;
  marketing_angle: string;
  talking_points: string[];
  // CONTENT PERSPECTIVE: the persona the user chose when generating
  // this brief — independent of the trend's best_audience. content_angle
  // is the angle written specifically from that perspective.
  perspective: AudienceType | "";
  content_angle: string;
  model_used: string;
  created_at: string;
  generated_content: GeneratedContent[];
}

export async function fetchBriefsForTrend(trendSlug: string) {
  const { data } = await apiClient.get<PaginatedResponse<ContentBrief>>("/content/briefs/", {
    params: { trend: trendSlug },
  });
  return data;
}

export async function createBrief(trendSlug: string, perspective?: AudienceType | "") {
  const { data } = await apiClient.post<AIJob>("/content/briefs/", {
    trend_slug: trendSlug,
    perspective: perspective || undefined,
  });
  return data;
}

export async function createGeneratedContent(briefId: string, contentType: ContentType) {
  const { data } = await apiClient.post<AIJob>("/content/pieces/", {
    brief_id: briefId,
    content_type: contentType,
  });
  return data;
}

export async function setContentSaved(contentId: string, isSaved: boolean) {
  const { data } = await apiClient.patch<GeneratedContent>(`/content/pieces/${contentId}/`, {
    is_saved: isSaved,
  });
  return data;
}

export async function updateContentBody(contentId: string, body: string) {
  const { data } = await apiClient.patch<GeneratedContent>(`/content/pieces/${contentId}/`, { body });
  return data;
}

export async function deleteContentBrief(briefId: string) {
  await apiClient.delete(`/content/briefs/${briefId}/`);
}

export async function deleteGeneratedContent(contentId: string) {
  await apiClient.delete(`/content/pieces/${contentId}/`);
}

export async function fetchGeneratedContent(id: string) {
  const { data } = await apiClient.get<GeneratedContent>(`/content/pieces/${id}/`);
  return data;
}

export async function fetchSavedContent() {
  const { data } = await apiClient.get<PaginatedResponse<GeneratedContent>>("/content/pieces/", {
    params: { is_saved: "true" },
  });
  return data;
}

export async function fetchContentVersions(briefId: string, contentType: ContentType) {
  const { data } = await apiClient.get<PaginatedResponse<GeneratedContent>>("/content/pieces/", {
    params: { brief: briefId },
  });
  return data.results.filter((item) => item.content_type === contentType).sort((a, b) => b.version - a.version);
}
