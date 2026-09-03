import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import * as authApi from "@/features/auth/api/auth-api";

function firstError(error: unknown, fallback: string): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data;
    if (data?.error?.detail) {
      const detail = data.error.detail;
      if (typeof detail === "string") return detail;
      if (typeof detail === "object") {
        const firstKey = Object.keys(detail)[0];
        const value = detail[firstKey];
        return Array.isArray(value) ? value[0] : String(value ?? fallback);
      }
    }
  }
  return fallback;
}

export function useRegister() {
  return useMutation({
    mutationFn: authApi.register,
  });
}

export function useLogin() {
  return useMutation({
    mutationFn: authApi.login,
  });
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: ({ email, code }: { email: string; code: string }) =>
      authApi.verifyEmail(email, code),
  });
}

export function useResendVerification() {
  return useMutation({
    mutationFn: authApi.resendVerification,
  });
}

export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: authApi.requestPasswordReset,
  });
}

export function useConfirmPasswordReset() {
  return useMutation({
    mutationFn: ({ uid, token, new_password }: { uid: string; token: string; new_password: string }) =>
      authApi.confirmPasswordReset(uid, token, new_password),
  });
}

export function useGoogleAuth() {
  return useMutation({
    mutationFn: authApi.googleAuth,
  });
}

export { firstError };
