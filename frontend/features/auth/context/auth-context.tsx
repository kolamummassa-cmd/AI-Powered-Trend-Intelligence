"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";

import { refreshAccessToken, setTokens } from "@/lib/api/client";
import {
  type AuthTokens,
  type AuthUser,
  getMe,
  logout as logoutRequest,
} from "@/features/auth/api/auth-api";

interface AuthContextValue {
  user: AuthUser | undefined;
  /** True until we've checked storage for a token AND (if one exists) resolved /me/. */
  isLoading: boolean;
  isAuthenticated: boolean;
  setSession: (tokens: AuthTokens) => void;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const router = useRouter();

  // Both start "unknown" until the mount effect uses the HttpOnly refresh
  // cookie to restore an in-memory access token. This avoids redirecting a
  // real session to login during hydration.
  const [hasToken, setHasToken] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    refreshAccessToken().then((access) => {
      if (active) setHasToken(Boolean(access));
    });
    return () => {
      active = false;
    };
  }, []);

  const { data: user, isLoading: isMeLoading } = useQuery({
    queryKey: ["me"],
    queryFn: getMe,
    enabled: hasToken === true,
    retry: false,
  });

  function setSession(tokens: AuthTokens) {
    setTokens(tokens);
    setHasToken(true);
    queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  async function signOut() {
    try {
      await logoutRequest();
    } catch {
      // Token may already be expired/blacklisted — still clear local
      // state and send the user back to login either way.
    }
    setTokens(null);
    setHasToken(false);
    queryClient.setQueryData(["me"], undefined);
    queryClient.removeQueries({ queryKey: ["me"] });
    router.push("/login");
  }

  const stillResolving = hasToken === null || (hasToken && isMeLoading);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading: stillResolving,
        isAuthenticated: Boolean(user),
        setSession,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
