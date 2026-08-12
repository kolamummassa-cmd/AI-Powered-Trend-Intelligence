import { type Notification } from "@/features/notifications/api/notifications-api";

export function formatNotification(notification: Notification): {
  title: string;
  href: string | null;
} {
  const { type, payload } = notification;

  switch (type) {
    case "new_high_value_trend":
      return {
        title: `New high-value trend: ${payload.title ?? "Untitled"}`,
        href: payload.trend_slug ? `/trends/${payload.trend_slug}` : null,
      };
    case "expiring_trend":
      return {
        title: `Trend expiring soon: ${payload.title ?? "Untitled"}`,
        href: payload.trend_slug ? `/trends/${payload.trend_slug}` : null,
      };
    case "generation_complete":
      return {
        title: payload.content_id
          ? `Content ready for ${payload.trend_title ?? "your trend"}`
          : `Content brief ready for ${payload.trend_title ?? "your trend"}`,
        href: payload.content_id
          ? `/content/${payload.content_id}`
          : payload.trend_slug
            ? `/trends/${payload.trend_slug}`
            : null,
      };
    default:
      return { title: "New notification", href: null };
  }
}
