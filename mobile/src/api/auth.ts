import { api } from "./client";
import { AuthSession } from "@/types";

export const authApi = {
  register: (input: { email: string; password: string }) =>
    api.post<AuthSession>("/api/v1/auth/register", input),
  login: (input: { email: string; password: string }) =>
    api.post<AuthSession>("/api/v1/auth/login", input),
  forgotPassword: (input: { email: string }) =>
    api.post<{ message: string; dev_reset_token?: string | null }>(
      "/api/v1/auth/forgot-password",
      input,
    ),
  resetPassword: (input: { token: string; new_password: string }) =>
    api.post<AuthSession>("/api/v1/auth/reset-password", input),
};