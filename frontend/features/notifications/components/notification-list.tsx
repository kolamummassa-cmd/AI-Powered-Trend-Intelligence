"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarkNotificationsRead, useNotifications } from "@/features/notifications/api/use-notifications";
import { formatNotification } from "@/features/notifications/lib/format-notification";
import { cn } from "@/lib/utils";

export function NotificationList() {
  const { data, isLoading, isError } = useNotifications();
  const markRead = useMarkNotificationsRead();

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
        ))}
      </div>
    );
  }

  if (isError) {
    return <p className="text-sm text-danger">Could not load notifications.</p>;
  }

  if (!data || data.results.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border py-16 text-center">
        <p className="text-muted-foreground">
          Nothing here yet. You&apos;ll see alerts for high-value trends, trends expiring soon,
          and finished content generations.
        </p>
      </div>
    );
  }

  const hasUnread = data.results.some((n) => !n.read_at);

  return (
    <div className="space-y-3">
      {hasUnread && (
        <div className="flex justify-end">
          <Button variant="outline" size="sm" onClick={() => markRead.mutate(undefined)}>
            Mark all read
          </Button>
        </div>
      )}
      <div className="space-y-2">
        {data.results.map((notification) => {
          const { title, href } = formatNotification(notification);
          const body = (
            <div
              className={cn(
                "flex items-center justify-between gap-3 rounded-md border border-border px-4 py-3 text-sm",
                !notification.read_at && "border-primary/40 bg-primary/5",
              )}
            >
              <span className={cn(!notification.read_at && "font-medium")}>{title}</span>
              <span className="shrink-0 text-xs text-muted-foreground">
                {new Date(notification.created_at).toLocaleString()}
              </span>
            </div>
          );

          return (
            <div key={notification.id} onClick={() => markRead.mutate([notification.id])}>
              {href ? <Link href={href}>{body}</Link> : body}
            </div>
          );
        })}
      </div>
    </div>
  );
}
