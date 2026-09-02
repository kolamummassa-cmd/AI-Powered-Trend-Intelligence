"use client";

import { BellIcon } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useMarkNotificationsRead, useNotifications, useUnreadCount } from "@/features/notifications/api/use-notifications";
import { formatNotification } from "@/features/notifications/lib/format-notification";

export function NotificationBell() {
  const { data: unreadCount } = useUnreadCount();
  const { data } = useNotifications();
  const markRead = useMarkNotificationsRead();

  const notifications = data?.results.slice(0, 8) ?? [];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="relative gap-2">
          <BellIcon />
          <span>Notifications</span>
          {Boolean(unreadCount) && (
            <Badge
              variant="destructive"
              className="absolute -right-1 -top-1 flex size-5 items-center justify-center rounded-full p-0 text-[10px]"
            >
              {(unreadCount ?? 0) > 9 ? "9+" : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="max-h-96 overflow-y-auto">
        <div className="flex items-center justify-between px-2 py-1.5">
          <p className="text-sm font-medium">Notifications</p>
          {Boolean(unreadCount) && (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto p-0 text-xs"
              onClick={() => markRead.mutate(undefined)}
            >
              Mark all read
            </Button>
          )}
        </div>
        {notifications.length === 0 && (
          <p className="px-2 py-4 text-center text-sm text-muted-foreground">
            You&apos;re all caught up.
          </p>
        )}
        {notifications.map((notification) => {
          const { title, href } = formatNotification(notification);
          const content = (
            <div
              className={
                "rounded-md px-2 py-2 text-sm hover:bg-muted " +
                (notification.read_at ? "text-muted-foreground" : "font-medium text-foreground")
              }
            >
              {title}
            </div>
          );
          return (
            <div key={notification.id}>
              {href ? (
                <Link href={href} onClick={() => markRead.mutate([notification.id])}>
                  {content}
                </Link>
              ) : (
                content
              )}
            </div>
          );
        })}
        <div className="border-t border-border px-2 pt-1.5">
          <Link href="/notifications" className="block py-1.5 text-center text-sm text-primary">
            View all
          </Link>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
