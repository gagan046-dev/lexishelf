import { api } from "./client";

export type NotionPage = {
  id: string;
  title: string;
  url?: string | null;
};

type NotionPageSearchResult = {
  pages: NotionPage[];
  has_more: boolean;
  next_cursor?: string | null;
};

export const notionApi = {
  authorizationUrl: () => api.get<{ authorization_url: string }>("/api/v1/notion/oauth/authorize"),
  searchPages: (query = "") =>
    api.get<NotionPageSearchResult>(`/api/v1/notion/pages/search?query=${encodeURIComponent(query)}`),
};