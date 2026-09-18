import { api } from "./client";
import { Collection } from "@/types";

export const collectionsApi = {
  list: () => api.get<Collection[]>("/api/v1/collections"),

  create: (input: {
    name: string;
    description?: string;
    theme_id?: string;
    notion_page_id?: string;
    notion_page_url?: string;
  }) =>
    api.post<Collection>("/api/v1/collections", input),

  get: (id: string) => api.get<Collection>(`/api/v1/collections/${id}`),

  /** Deletes the collection and all of its vocabulary entries. Requires explicit confirmation. */
  remove: (id: string) =>
    api.delete<{ success: boolean; data: { deleted_collection_id: string } }>(
      `/api/v1/collections/${id}`,
      { confirm: true }
    ),
};
