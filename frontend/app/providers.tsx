"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";
import { Toaster } from "sonner";

import { AuthProvider } from "@/features/auth/context/auth-context";
import { ThemeProvider, useTheme } from "@/lib/theme-provider";

// Split out so it can call useTheme() from inside ThemeProvider — Sonner
// needs to know light vs dark to theme its own toasts correctly.
function ThemedToaster() {
  const { theme } = useTheme();
  return <Toaster theme={theme} position="top-right" richColors closeButton />;
}

export function Providers({ children }: { children: React.ReactNode }) {
  // One QueryClient per component tree instance (not module scope) so
  // it isn't shared across requests during SSR.
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      }),
  );

  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          {children}
          <ThemedToaster />
          {process.env.NODE_ENV === "development" && (
            <ReactQueryDevtools initialIsOpen={false} />
          )}
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
