export type Collection = {
  id: string;
  name: string;
  description?: string | null;
  notion_page_id?: string | null;
  notion_page_url?: string | null;
  theme_id: string;
  word_count: number;
  created_at: string;
  updated_at: string;
};

export type VocabularyEntry = {
  id: string;
  collection_id: string;
  term: string;
  phrase?: string | null;
  sentence_context?: string | null;
  meaning?: string | null;
  simple_explanation?: string | null;
  contextual_explanation?: string | null;
  example?: string | null;
  synonyms: string[];
  part_of_speech?: string | null;
  pronunciation?: string | null;
  usage_note?: string | null;
  difficulty_level?: "simple" | "standard" | "advanced" | null;
  notion_sync?: "synced" | "not_linked" | "failed" | null;
  notion_message?: string | null;
  review_due_at: string;
  review_interval_days: number;
  review_streak: number;
  created_at: string;
  updated_at: string;
};

export type VocabularyEntrySearchResult = VocabularyEntry & { collection_name: string };

export type VocabularyExplanation = {
  term: string;
  normalized_term: string;
  part_of_speech?: string | null;
  pronunciation?: string | null;
  meaning: string;
  simple_meaning: string;
  contextual_meaning?: string | null;
  example: string;
  synonyms: string[];
  usage_note?: string | null;
  confidence: number;
};

export type AgentAction = {
  type: string;
  status: "success" | "failure";
  message: string;
  error_code?: string | null;
  data: Record<string, unknown>;
};

export type ChatResponse = {
  message: string;
  actions: AgentAction[];
  request_id: string;
};

export type AuthUser = {
  id: string;
  email: string;
};

export type AuthSession = {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
};
