"use client";

import { BellRingIcon, CheckCircle2Icon, FlameIcon, TimerIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarkNotificationsRead, useNotifications } from "@/features/notifications/api/use-notifications";
import { formatNotification, relativeTime } from "@/features/notifications/lib/format-notification";
import { cn } from "@/lib/utils";

const TYPE_ICON = { Opportunity: FlameIcon, "Time-sensitive": TimerIcon, "Content ready": CheckCircle2Icon, Update: BellRingIcon };

export function NotificationList() {
  const { data, isLoading, isError, refetch } = useNotifications();
  const markRead = useMarkNotificationsRead();
  const [filter, setFilter] = useState<"all" | "unread">("all");

  if (isLoading) return <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 w-full" />)}</div>;
  if (isError) return <div className="rounded-lg border border-border bg-muted/40 p-5"><p className="font-medium">Notifications are temporarily unavailable.</p><Button className="mt-3" variant="outline" size="sm" onClick={() => refetch()}>Retry</Button></div>;
  if (!data || data.results.length === 0) return <div className="rounded-lg border border-dashed border-border py-16 text-center"><p className="font-medium">You&apos;re all caught up.</p><p className="mt-2 text-sm text-muted-foreground">When a high-value trend, expiring opportunity, or finished draft needs attention, it will appear here.</p><Button asChild className="mt-4" size="sm"><Link href="/trends">Explore trends</Link></Button></div>;

  const hasUnread = data.results.some((item) => !item.read_at);
  const visible = filter === "unread" ? data.results.filter((item) => !item.read_at) : data.results;

  return <div className="space-y-3"><div className="flex flex-wrap items-center justify-between gap-2"><div className="flex gap-2"><Button size="sm" variant={filter === "all" ? "default" : "outline"} onClick={() => setFilter("all")}>All</Button><Button size="sm" variant={filter === "unread" ? "default" : "outline"} onClick={() => setFilter("unread")}>Unread</Button></div>{hasUnread && <Button variant="outline" size="sm" onClick={() => markRead.mutate(undefined)}>Mark all read</Button>}</div><div className="space-y-2">{visible.map((notification) => { const { title, href, category } = formatNotification(notification); const Icon = TYPE_ICON[category]; const item = <div className={cn("flex items-start gap-3 rounded-md border border-border px-4 py-3 text-sm transition-colors hover:bg-muted", !notification.read_at && "border-primary/40 bg-primary/5")}><Icon className="mt-0.5 size-4 shrink-0 text-primary" /><div className="min-w-0 flex-1"><p className={cn(!notification.read_at && "font-medium")}>{title}</p><p className="mt-1 text-xs text-muted-foreground">{category} · {relativeTime(notification.created_at)}</p></div></div>; return href ? <Link key={notification.id} href={href} onClick={() => markRead.mutate([notification.id])} className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary">{item}</Link> : <button key={notification.id} type="button" onClick={() => markRead.mutate([notification.id])} className="block w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary">{item}</button>; })}</div>{visible.length === 0 && <p className="rounded-md border border-dashed border-border p-5 text-center text-sm text-muted-foreground">No unread notifications. You&apos;re up to date.</p>}</div>;
}
