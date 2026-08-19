"use client";

import { createContext, useContext, useEffect, useState } from "react";

type Theme = "light" | "dark";

const STORAGE_KEY = "trend-intelligence-theme";

const ThemeContext = createContext<{ theme: Theme; toggleTheme: () => void } | null>(null);

function resolveInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  // Deliberately does NOT fall back to prefers-color-scheme — product
  // decision (2026-08-20): light mode is the default for every first
  // visit regardless of OS/browser theme, until the user explicitly
  // toggles (at which point their choice is remembered via localStorage).
  return "light";
}

/**
 * Manual light/dark toggle for the authenticated dashboard shell.
 *
 * Reads localStorage first, falls back to light mode (not the OS
 * preference — light is the deliberate default for first-time visitors),
 * then keeps both in sync on every toggle. Applies `.dark` to `document.documentElement`
 * (not a nested wrapper div) because inherited `color` values are resolved
 * at the scope where they're declared — a nested `.dark` wouldn't override
 * `<body>`'s own light-mode color — and because Radix Dialog/DropdownMenu
 * portal their content to `document.body`, escaping any nested `.dark`
 * scope entirely.
 *
 * A blocking inline script (see app/layout.tsx) sets the class before
 * first paint so there's no light-mode flash for dark-mode users.
 * resolveInitialTheme() is passed as a lazy useState initializer rather
 * than being read in an effect: React (re-)runs this component function
 * fresh on the client during hydration, so `window` is already defined
 * by the time it fires — no extra effect-driven setState needed to
 * "correct" the value after mount.
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(resolveInitialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  function toggleTheme() {
    setTheme((prev) => {
      const next: Theme = prev === "dark" ? "light" : "dark";
      window.localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  }

  return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within a ThemeProvider");
  return ctx;
}
