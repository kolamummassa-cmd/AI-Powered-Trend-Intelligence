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
  if (isError) return <div className="rounded-2xl border border-destructive/20 bg-destructive/5 p-5"><p className="font-medium">Notifications are temporarily unavailable.</p><p className="mt-1 text-sm text-muted-foreground">Your alerts are safe. Please try loading them again.</p><Button className="mt-4" variant="outline" size="sm" onClick={() => refetch()}>Retry</Button></div>;
  if (!data || data.results.length === 0) return <div className="rounded-2xl border border-accent/20 bg-linear-to-br from-accent/10 via-card to-sky-500/6 px-6 py-12 text-center sm:px-10"><span className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-accent/15 text-accent-foreground"><BellRingIcon className="size-6" aria-hidden="true" /></span><p className="mt-5 text-xs font-semibold uppercase tracking-[0.18em] text-accent-foreground">Inbox clear</p><h2 className="mt-2 text-2xl font-semibold tracking-tight">You&apos;re all caught up</h2><p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-muted-foreground">When a high-value trend, expiring opportunity, or finished draft needs attention, it will appear here.</p><Button asChild className="mt-6" size="sm"><Link href="/trends">Explore trends</Link></Button></div>;

  const hasUnread = data.results.some((item) => !item.read_at);
  const visible = filter === "unread" ? data.results.filter((item) => !item.read_at) : data.results;

  return <div className="space-y-4"><div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border bg-card/80 p-2"><div className="flex gap-2"><Button size="sm" variant={filter === "all" ? "default" : "outline"} onClick={() => setFilter("all")}>All</Button><Button size="sm" variant={filter === "unread" ? "default" : "outline"} onClick={() => setFilter("unread")}>Unread</Button></div>{hasUnread && <Button variant="outline" size="sm" onClick={() => markRead.mutate(undefined)}>Mark all read</Button>}</div><div className="space-y-2">{visible.map((notification) => { const { title, href, category } = formatNotification(notification); const Icon = TYPE_ICON[category]; const item = <div className={cn("flex items-start gap-3 rounded-xl border border-border bg-card px-4 py-3 text-sm transition-colors hover:bg-muted", !notification.read_at && "border-primary/20 bg-linear-to-r from-primary/8 via-card to-warning/5")}><Icon className="mt-0.5 size-4 shrink-0 text-primary" /><div className="min-w-0 flex-1"><p className={cn(!notification.read_at && "font-medium")}>{title}</p><p className="mt-1 text-xs text-muted-foreground">{category} · {relativeTime(notification.created_at)}</p></div></div>; return href ? <Link key={notification.id} href={href} onClick={() => markRead.mutate([notification.id])} className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary">{item}</Link> : <button key={notification.id} type="button" onClick={() => markRead.mutate([notification.id])} className="block w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary">{item}</button>; })}</div>{visible.length === 0 && <div className="rounded-xl border border-dashed border-accent/30 bg-accent/5 p-6 text-center text-sm text-muted-foreground">No unread notifications. You&apos;re up to date.</div>}</div>;
}
