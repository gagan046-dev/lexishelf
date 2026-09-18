import { api } from "./client";
import { ChatResponse } from "@/types";

export const chatApi = {
  send: (input: { message: string; collection_id?: string; conversation_id?: string }) =>
    api.post<ChatResponse>("/api/v1/chat", input),
};