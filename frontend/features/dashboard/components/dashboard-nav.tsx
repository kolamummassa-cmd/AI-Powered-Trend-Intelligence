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
      className="fixed inset-x-0 bottom-0 z-40 flex h-16 items-center justify-around border-t border-black/[0.06] bg-white/95 px-2 backdrop-blur-[18px] dark:border-white/[0.06] dark:bg-[rgba(15,23,42,0.95)] md:sticky md:top-0 md:h-screen md:w-56 md:shrink-0 md:flex-col md:items-stretch md:justify-start md:border-r md:border-t-0 md:px-3 md:py-4"
      suppressHydrationWarning
    >
      <Link
        href="/dashboard"
        className="hidden size-9 items-center justify-center rounded-lg bg-[linear-gradient(135deg,#2563eb,#3b82f6_55%,#14b8a6)] text-white shadow-[0_0_20px_rgba(37,99,235,0.35)] md:mb-8 md:flex"
        aria-label="Dashboard home"
      >
        <ActivityIcon className="size-4" />
      </Link>

      <div className="flex flex-1 items-center justify-around gap-1 md:flex-col md:items-stretch md:justify-start md:gap-1.5">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex min-w-14 flex-col items-center gap-1 rounded-xl px-2 py-2 text-[11px] font-medium transition-all md:w-full md:flex-row md:gap-3 md:px-3 md:text-sm",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-black/60 hover:bg-muted hover:text-black dark:text-white/60 dark:hover:text-white",
              )}
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
