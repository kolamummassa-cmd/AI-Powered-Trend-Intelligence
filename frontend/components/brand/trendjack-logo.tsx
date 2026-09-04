import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

/** A compact original mark: a rising signal becomes the letter J. */
export function TrendJackMark({ className, ...props }: ComponentProps<"svg">) {
  return (
    <svg
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
      className={cn("shrink-0", className)}
      {...props}
    >
      <defs>
        <linearGradient id="trendjack-gradient" x1="6" y1="5" x2="34" y2="35" gradientUnits="userSpaceOnUse">
          <stop stopColor="#fb923c" />
          <stop offset="0.55" stopColor="#f97316" />
          <stop offset="1" stopColor="#ea580c" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="11" fill="url(#trendjack-gradient)" />
      <path d="M10 25.5 16.2 19.3l4.5 4.5L30 14.5" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M30 14.5v7M30 14.5h-7" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M25 23.5v3.3c0 3.2-2.6 5.7-5.7 5.7h-1.8" stroke="white" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function TrendJackBrand({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <TrendJackMark className="size-8" />
      {!compact && (
        <span className="leading-none">
          <span className="block text-base font-semibold tracking-tight">TrendJack</span>
          <span className="block pt-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-primary">Hunter</span>
        </span>
      )}
    </span>
  );
}
