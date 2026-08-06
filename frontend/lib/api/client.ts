import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

/**
 * Single Axios instance for the whole app. Every feature module's
 * api/ folder imports this rather than creating its own client, so
 * base URL, auth headers, and token refresh stay in one place.
 */
export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1",
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
  },
});

// A plain client (no interceptors) for the one call — refreshing the
// token — that must never itself trigger the refresh-on-401 logic below.
const refreshClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1",
  timeout: 15_000,
});

// sessionStorage is a deliberate, temporary choice: it's simple and
// scoped to the tab, but it's readable by any script on the page, so
// it's vulnerable to XSS the same way any JS-accessible token storage
// is. Revisit before real production traffic — the safer pattern is a
// short-lived access token kept in memory only, with the refresh token
// in an httpOnly cookie the backend sets/reads directly.
const ACCESS_TOKEN_KEY = "trend_intel_access_token";
const REFRESH_TOKEN_KEY = "trend_intel_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(tokens: { access: string; refresh?: string } | null) {
  if (typeof window === "undefined") return;
  if (tokens) {
    window.sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
    if (tokens.refresh) {
      window.sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
    }
  } else {
    window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

// Coalesces concurrent 401s into a single refresh call rather than
// firing one refresh request per failed request.
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  if (!refreshPromise) {
    refreshPromise = refreshClient
      .post<{ access: string }>("/auth/token/refresh/", { refresh })
      .then((res) => {
        setTokens({ access: res.data.access, refresh });
        return res.data.access;
      })
      .catch(() => {
        setTokens(null);
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;
    const isAuthEndpoint = original?.url?.includes("/auth/login") || original?.url?.includes("/auth/register");

    if (error.response?.status === 401 && original && !original._retried && !isAuthEndpoint) {
      original._retried = true;
      const newAccess = await refreshAccessToken();
      if (newAccess) {
        original.headers.set("Authorization", `Bearer ${newAccess}`);
        return apiClient(original);
      }
    }

    return Promise.reject(error);
  },
);
