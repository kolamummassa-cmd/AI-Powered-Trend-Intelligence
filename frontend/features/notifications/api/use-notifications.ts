import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/features/auth/context/auth-context";
import {
  fetchNotifications,
  fetchUnreadCount,
  markNotificationsRead,
} from "@/features/notifications/api/notifications-api";
import { shouldRetryRequest } from "@/lib/api/client";

export function useNotifications(unreadOnly?: boolean) {
  const { isAuthenticated, isLoading } = useAuth();
  return useQuery({
    queryKey: ["notifications", { unreadOnly }],
    queryFn: () => fetchNotifications(unreadOnly),
    enabled: !isLoading && isAuthenticated,
    retry: shouldRetryRequest,
  });
}

export function useUnreadCount() {
  const { isAuthenticated, isLoading } = useAuth();
  return useQuery({
    queryKey: ["notifications-unread-count"],
    queryFn: fetchUnreadCount,
    refetchInterval: 30_000,
    enabled: !isLoading && isAuthenticated,
    retry: shouldRetryRequest,
  });
}

export function useMarkNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ids?: string[]) => markNotificationsRead(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });
}
