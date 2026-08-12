import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

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

function useInvalidateAfterChat(contentId: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["chat-messages", contentId] });
    queryClient.invalidateQueries({ queryKey: ["generated-content", contentId] });
  };
}

export function useRefineContent(contentId: string) {
  const invalidate = useInvalidateAfterChat(contentId);
  return useMutation({
    mutationFn: (instruction: string) => refineContent(contentId, instruction),
    onSuccess: invalidate,
  });
}

export function useConvertForPlatform(contentId: string) {
  const invalidate = useInvalidateAfterChat(contentId);
  return useMutation({
    mutationFn: (platform: PlatformConversion) => convertContentForPlatform(contentId, platform),
    onSuccess: invalidate,
  });
}
