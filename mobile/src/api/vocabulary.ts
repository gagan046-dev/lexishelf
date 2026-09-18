import { api } from "./client";
import { VocabularyEntry, VocabularyEntrySearchResult, VocabularyExplanation } from "@/types";

export const vocabularyApi = {
  explain: (input: {
    term: string;
    sentence_context?: string;
    difficulty_level?: "simple" | "standard" | "advanced";
  }) => api.post<VocabularyExplanation>("/api/v1/vocabulary/explain", input),

  listByCollection: (collectionId: string) =>
    api.get<VocabularyEntry[]>(`/api/v1/vocabulary?collection_id=${collectionId}`),

  /** Searches saved words across every one of the user's collections. */
  search: (query: string) =>
    api.get<VocabularyEntrySearchResult[]>(`/api/v1/vocabulary/search?query=${encodeURIComponent(query)}`),

  create: (input: Partial<VocabularyEntry> & { collection_id: string; term: string }) =>
    api.post<VocabularyEntry>("/api/v1/vocabulary", input),

  /** Deletes a single saved word/phrase. */
  remove: (id: string) =>
    api.delete<{ success: boolean; data: { deleted_entry_id: string } }>(`/api/v1/vocabulary/${id}`),

  listDueForReview: (limit = 20) =>
    api.get<VocabularyEntry[]>(`/api/v1/vocabulary/review/due?limit=${limit}`),

  review: (entryId: string, result: "again" | "hard" | "good" | "easy") =>
    api.post<{ entry_id: string; review_due_at: string; review_interval_days: number; review_streak: number }>(
      `/api/v1/vocabulary/${entryId}/review`,
      { result },
    ),
};
