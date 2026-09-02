"use client";

import { MoonIcon, SunIcon } from "lucide-react";
import { useEffect, useState } from "react";

import { useTheme } from "@/lib/theme-provider";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  // The server always renders assuming "light" (the SSR fallback in
  // resolveInitialTheme) — swapping Sun/Moon before the client has
  // mounted and resolved the real stored preference would mismatch the
  // server-rendered icon, so we hold a neutral placeholder until after
  // hydration.
  const [mounted, setMounted] = useState(false);
  // eslint-disable-next-line react-hooks/set-state-in-effect -- deliberate mount-detection flag, not fixable via a lazy initializer since it must run after hydration completes.
  useEffect(() => setMounted(true), []);

  return (
    <button
      type="button"
      onClick={toggleTheme}
      // Guarded by `mounted` for the same reason the icon below is —
      // `theme` resolves to its real value on the client's very first
      // render (see resolveInitialTheme's docstring), but the server
      // always rendered the "dark" fallback, so reading `theme` here
      // unconditionally mismatched the server-rendered aria-label and
      // broke hydration for the whole page.
      aria-label={
        !mounted ? "Toggle theme" : theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
      }
      className="flex h-10 items-center gap-2 rounded-full bg-black/[0.04] px-3 text-sm font-medium transition-colors hover:bg-black/[0.08] dark:bg-white/[0.04] dark:hover:bg-white/[0.08]"
    >
      {!mounted ? (
        <span className="size-4" />
      ) : theme === "dark" ? (
        <SunIcon className="size-4" />
      ) : (
        <MoonIcon className="size-4" />
      )}
      <span>{!mounted ? "Theme" : theme === "dark" ? "Light mode" : "Dark mode"}</span>
    </button>
  );
}
