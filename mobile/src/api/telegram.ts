import { api } from "./client";

export const telegramApi = {
  getLinkCode: () => api.get<{ code: string; expires_at: string }>("/api/v1/telegram/link/code"),
};
