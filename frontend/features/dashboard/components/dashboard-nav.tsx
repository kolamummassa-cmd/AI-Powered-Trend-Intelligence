"use client";

import { ActivityIcon, FolderOpenIcon, LayoutDashboardIcon, TrendingUpIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { ThemeToggle } from "@/components/ui/theme-toggle";
import { NotificationBell } from "@/features/notifications/components/notification-bell";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboardIcon },
  { href: "/trends", label: "Trends", icon: TrendingUpIcon },
  { href: "/content", label: "Content", icon: FolderOpenIcon },
] as const;

export function DashboardNav() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 flex h-16 items-center justify-around border-t border-border bg-sidebar/95 px-2 backdrop-blur-[18px] dark:bg-sidebar/95 md:sticky md:top-0 md:h-screen md:w-64 md:shrink-0 md:flex-col md:items-stretch md:justify-start md:border-r md:border-t-0 md:px-4 md:py-5"
      suppressHydrationWarning
    >
      <Link
        href="/dashboard"
        className="hidden items-center gap-2 text-base font-semibold tracking-tight md:mb-10 md:flex"
        aria-label="Dashboard home"
      >
        <span className="flex size-7 items-center justify-center rounded-md bg-foreground text-primary-foreground">
          <ActivityIcon className="size-3.5" />
        </span>
        Kuzana
      </Link>

      <div className="flex flex-1 items-center justify-around gap-1 md:flex-col md:items-stretch md:justify-start md:gap-1.5">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex min-w-14 flex-col items-center gap-1 rounded-lg px-2 py-2 text-[11px] font-medium transition-colors md:w-full md:flex-row md:gap-3 md:px-3 md:text-sm",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-sidebar-foreground/75 hover:bg-muted hover:text-sidebar-foreground",
              )}
              aria-current={active ? "page" : undefined}
            >
              <item.icon className="size-5" />
              <span className="text-center leading-tight md:text-left">{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div className="hidden flex-col items-center gap-2 md:flex">
        <NotificationBell />
        <ThemeToggle />
      </div>
    </nav>
  );
}
