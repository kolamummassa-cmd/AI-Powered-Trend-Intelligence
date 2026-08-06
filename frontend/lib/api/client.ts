import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

/**
 * Single Axios instance for the whole app. Every feature module's
 * api/ folder imports this rather than creating its own client, so
 * base URL, auth headers, and error handling stay in one place.
 */
export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1",
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Token storage is a placeholder until Phase 1 (Authentication) wires
// real JWT issuance/refresh. Kept in one place so that swap is a
// one-file change, not a search-and-replace across every feature.
const ACCESS_TOKEN_KEY = "trend_intel_access_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) {
    window.sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
  } else {
    window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Centralised place to react to 401s (redirect to login once
    // Phase 1 auth flows exist) rather than handling it per-call.
    if (error.response?.status === 401) {
      setAccessToken(null);
    }
    return Promise.reject(error);
  },
);
