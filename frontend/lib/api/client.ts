import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

/**
 * Single Axios instance for the whole app. Every feature module's
 * api/ folder imports this rather than creating its own client, so
 * base URL, auth headers, and token refresh stay in one place.
 */
export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1",
  timeout: 15_000,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// A plain client (no interceptors) for the one call — refreshing the
// token — that must never itself trigger the refresh-on-401 logic below.
const refreshClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1",
  timeout: 15_000,
  withCredentials: true,
});

// The access token lives only in this module's memory. On a page refresh,
// the app obtains a replacement from the HttpOnly refresh cookie, which is
// never exposed to JavaScript and therefore cannot be stolen by an XSS read.
let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setTokens(tokens: { access: string } | null) {
  accessToken = tokens?.access ?? null;
}

/** React Query uses this for read endpoints: a 429 is a wait signal, not a failure to hammer. */
export function shouldRetryRequest(failureCount: number, error: unknown) {
  if (axios.isAxiosError(error) && error.response?.status === 429) return false;
  return failureCount < 2;
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

export async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = refreshClient
      .post<{ access: string }>("/auth/token/refresh/")
      .then((res) => {
        setTokens({ access: res.data.access });
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
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retried?: boolean })
      | undefined;
    const isAuthEndpoint =
      original?.url?.includes("/auth/login") ||
      original?.url?.includes("/auth/register") ||
      original?.url?.includes("/auth/token/refresh") ||
      original?.url?.includes("/auth/logout");

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
