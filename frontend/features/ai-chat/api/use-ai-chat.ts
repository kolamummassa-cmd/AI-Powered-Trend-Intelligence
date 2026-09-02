import { useMutation, useQuery } from "@tanstack/react-query";

import {
  type PlatformConversion,
  convertContentForPlatform,
  fetchChatMessages,
  refineContent,
} from "@/features/ai-chat/api/ai-chat-api";

export function useChatMessages(contentId: string) {
  return useQuery({
    queryKey: ["chat-messages", contentId],
    queryFn: () => fetchChatMessages(contentId),
    enabled: Boolean(contentId),
  });
}

export function useRefineContent(contentId: string) {
  return useMutation({
    mutationFn: (instruction: string) => refineContent(contentId, instruction),
  });
}

export function useConvertForPlatform(contentId: string) {
  return useMutation({
    mutationFn: (platform: PlatformConversion) => convertContentForPlatform(contentId, platform),
  });
}
