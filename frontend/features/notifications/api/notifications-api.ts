import { apiClient } from "@/lib/api/client";
import { type PaginatedResponse } from "@/features/trends/api/trends-api";

export type NotificationType =
  | "new_high_value_trend"
  | "expiring_trend"
  | "generation_complete";

export interface NotificationPayload {
  trend_id?: string;
  trend_slug?: string;
  title?: string;
  trend_title?: string;
  trend_score?: number;
  opportunity_score?: number;
  brief_id?: string;
  content_id?: string;
  content_type?: string;
}

export interface Notification {
  id: string;
  type: NotificationType;
  payload: NotificationPayload;
  read_at: string | null;
  created_at: string;
}

export async function fetchNotifications(unreadOnly?: boolean) {
  const { data } = await apiClient.get<PaginatedResponse<Notification>>("/notifications/", {
    params: unreadOnly ? { unread: "true" } : undefined,
  });
  return data;
}

export async function fetchUnreadCount() {
  const { data } = await apiClient.get<{ unread_count: number }>("/notifications/unread-count/");
  return data.unread_count;
}

export async function markNotificationsRead(ids?: string[]) {
  const { data } = await apiClient.post<{ marked: number }>("/notifications/mark-read/", {
    ids,
  });
  return data;
}
