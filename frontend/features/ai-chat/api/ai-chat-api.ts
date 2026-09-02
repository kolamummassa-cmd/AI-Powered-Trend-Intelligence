import { apiClient } from "@/lib/api/client";
import { type AIJob } from "@/features/ai-jobs/api/ai-jobs-api";
import { type PaginatedResponse } from "@/features/trends/api/trends-api";

export const PLATFORM_CONVERSIONS = [
  { value: "linkedin", label: "LinkedIn post" },
  { value: "twitter_thread", label: "Twitter/X thread" },
  { value: "carousel", label: "Carousel outline" },
  { value: "shorts_script", label: "Shorts script" },
] as const;

export type PlatformConversion = (typeof PLATFORM_CONVERSIONS)[number]["value"];

export interface ChatMessage {
  id: string;
  content: string;
  role: "user" | "assistant";
  message: string;
  created_at: string;
}

export async function fetchChatMessages(contentId: string) {
  const { data } = await apiClient.get<PaginatedResponse<ChatMessage>>("/chat/messages/", {
    params: { content: contentId },
  });
  return data;
}

export async function refineContent(contentId: string, instruction: string) {
  const { data } = await apiClient.post<AIJob>("/chat/refine/", {
    content_id: contentId,
    instruction,
  });
  return data;
}

export async function convertContentForPlatform(
  contentId: string,
  platform: PlatformConversion,
) {
  const { data } = await apiClient.post<AIJob>("/chat/convert/", {
    content_id: contentId,
    platform,
  });
  return data;
}
