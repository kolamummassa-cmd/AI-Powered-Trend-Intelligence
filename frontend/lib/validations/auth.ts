import { z } from "zod";

// Mirrors the backend's AUTH_PASSWORD_VALIDATORS minimum length
// (config/settings/base.py) so the user sees the same rule client-side
// instead of round-tripping to find out.
const passwordSchema = z.string().min(10, "Must be at least 10 characters.");

export const registerSchema = z
  .object({
    email: z.string().email("Enter a valid email address."),
    password: passwordSchema,
    password_confirm: z.string(),
  })
  .refine((data) => data.password === data.password_confirm, {
    message: "Passwords do not match.",
    path: ["password_confirm"],
  });

export type RegisterFormValues = z.infer<typeof registerSchema>;

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(1, "Password is required."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export const forgotPasswordSchema = z.object({
  email: z.string().email("Enter a valid email address."),
});

export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z
  .object({
    new_password: passwordSchema,
    new_password_confirm: z.string(),
  })
  .refine((data) => data.new_password === data.new_password_confirm, {
    message: "Passwords do not match.",
    path: ["new_password_confirm"],
  });

export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;
