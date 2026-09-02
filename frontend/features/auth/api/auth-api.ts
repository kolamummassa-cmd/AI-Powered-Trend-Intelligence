import { apiClient } from "@/lib/api/client";

export interface AuthTokens {
  access: string;
}

export interface AuthUser {
  id: string;
  email: string;
  is_verified: boolean;
  auth_provider: "email" | "google";
  timezone: string;
  created_at: string;
  profile: {
    display_name: string;
    avatar_url: string;
    role: string;
    preferences: Record<string, unknown>;
  };
}

export interface RegisterPayload {
  email: string;
  password: string;
  password_confirm: string;
  role?: string;
}

export interface RegisterResponse extends AuthTokens {
  user: { id: string; email: string; is_verified: boolean };
}

export async function register(payload: RegisterPayload) {
  const { data } = await apiClient.post<RegisterResponse>("/auth/register/", payload);
  return data;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResponse extends AuthTokens {
  email: string;
  is_verified: boolean;
}

export async function login(payload: LoginPayload) {
  const { data } = await apiClient.post<LoginResponse>("/auth/login/", payload);
  return data;
}

export async function logout() {
  await apiClient.post("/auth/logout/");
}

export async function verifyEmail(uid: string, token: string) {
  const { data } = await apiClient.post<{ detail: string }>("/auth/verify-email/", {
    uid,
    token,
  });
  return data;
}

export async function resendVerification(email: string) {
  const { data } = await apiClient.post<{ detail: string }>("/auth/resend-verification/", {
    email,
  });
  return data;
}

export async function requestPasswordReset(email: string) {
  const { data } = await apiClient.post<{ detail: string }>("/auth/password-reset/", { email });
  return data;
}

export async function confirmPasswordReset(uid: string, token: string, new_password: string) {
  const { data } = await apiClient.post<{ detail: string }>("/auth/password-reset/confirm/", {
    uid,
    token,
    new_password,
  });
  return data;
}

export async function googleAuth(idToken: string) {
  const { data } = await apiClient.post<RegisterResponse>("/auth/google/", {
    id_token: idToken,
  });
  return data;
}

export async function getMe() {
  const { data } = await apiClient.get<AuthUser>("/auth/me/");
  return data;
}

export async function updateMe(payload: Partial<Pick<AuthUser, "timezone">> & {
  profile?: Partial<AuthUser["profile"]>;
}) {
  const { data } = await apiClient.patch<AuthUser>("/auth/me/", payload);
  return data;
}
