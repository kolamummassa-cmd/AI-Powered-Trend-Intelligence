import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type ContentType,
  createBrief,
  createGeneratedContent,
  fetchBriefsForTrend,
  fetchGeneratedContent,
  fetchSavedContent,
  setContentSaved,
} from "@/features/content-studio/api/content-studio-api";
import { type AudienceType } from "@/features/trends/api/trends-api";

export function useGeneratedContent(id: string) {
  return useQuery({
    queryKey: ["generated-content", id],
    queryFn: () => fetchGeneratedContent(id),
    enabled: Boolean(id),
  });
}

export function useBriefsForTrend(trendSlug: string) {
  return useQuery({
    queryKey: ["content-briefs", trendSlug],
    queryFn: () => fetchBriefsForTrend(trendSlug),
    enabled: Boolean(trendSlug),
  });
}

export function useCreateBrief(trendSlug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (perspective?: AudienceType | "") => createBrief(trendSlug, perspective),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["content-briefs", trendSlug] });
    },
  });
}

export function useCreateGeneratedContent(trendSlug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ briefId, contentType }: { briefId: string; contentType: ContentType }) =>
      createGeneratedContent(briefId, contentType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["content-briefs", trendSlug] });
    },
  });
}

export function useSetContentSaved(trendSlug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contentId, isSaved }: { contentId: string; isSaved: boolean }) =>
      setContentSaved(contentId, isSaved),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["content-briefs", trendSlug] });
      queryClient.invalidateQueries({ queryKey: ["saved-content"] });
    },
  });
}

export function useSavedContent() {
  return useQuery({
    queryKey: ["saved-content"],
    queryFn: fetchSavedContent,
  });
}
