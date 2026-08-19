"use client";

import { FolderOpenIcon, LayoutDashboardIcon, TrendingUpIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { ThemeToggle } from "@/components/ui/theme-toggle";
import { NotificationBell } from "@/features/notifications/components/notification-bell";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboardIcon },
  { href: "/trends", label: "Trends", icon: TrendingUpIcon },
  { href: "/content", label: "Content Library", icon: FolderOpenIcon },
] as const;

export function DashboardNav() {
  const pathname = usePathname();

  return (
    <nav
      className="sticky top-0 z-40 flex h-[72px] items-center justify-between gap-1 border-b border-black/[0.06] bg-white/90 px-2 backdrop-blur-[18px] dark:border-white/[0.06] dark:bg-[rgba(15,23,42,0.75)] sm:px-8"
      suppressHydrationWarning
    >
      <div className="flex items-center gap-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2 whitespace-nowrap rounded-lg px-2.5 py-1.5 text-sm font-medium transition-all sm:px-3",
                // text-foreground/60 (not text-muted-foreground) for
                // inactive tabs — against this nav's frosted, patterned
                // backdrop, muted-foreground's lighter gray was reported
                // as barely legible in light mode. Deriving from
                // --foreground at reduced opacity keeps solid contrast
                // in both themes since --foreground is near-black in
                // light mode and near-white in dark mode.
                active
                  ? "bg-[linear-gradient(135deg,#2563eb,#3b82f6_55%,#14b8a6)] text-white shadow-[0_0_30px_rgba(37,99,235,0.35)]"
                  : "text-foreground/60 hover:bg-muted hover:text-foreground",
              )}
            >
              <item.icon className="size-4" />
              {/* Icon-only below sm — three full labels plus the theme
                  toggle and bell no longer fit comfortably starting
                  around 375px-wide phones. */}
              <span className="hidden sm:inline">{item.label}</span>
            </Link>
          );
        })}
      </div>
      <div className="flex items-center gap-2">
        <ThemeToggle />
        <NotificationBell />
      </div>
    </nav>
  );
}
