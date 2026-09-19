import React, { useEffect, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import {
  ActivityIndicator,
  Platform,
  Pressable,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useNavigation, useRoute } from "@react-navigation/native";
import Animated, { FadeInUp } from "react-native-reanimated";
import { Ionicons } from "@expo/vector-icons";

import { collectionsApi } from "@/api/collections";
import { getApiErrorMessage } from "@/api/client";
import { vocabularyApi } from "@/api/vocabulary";
import { AnimatedPressable } from "@/components/AnimatedPressable";
import { useThemeColors } from "@/theme/ThemeContext";
import { speakText } from "@/utils/speech";
import { Collection, VocabularyExplanation } from "@/types";

const RECENT_SEARCHES_KEY = "lexishelf.recent-searches";
type Difficulty = "simple" | "standard" | "advanced";

export function SearchScreen() {
  const colors = useThemeColors();
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const initialQuery = (route.params?.query ?? "").trim();
  const [query, setQuery] = useState(initialQuery);
  const [sentenceContext, setSentenceContext] = useState("");
  const [explanation, setExplanation] = useState<VocabularyExplanation | null>(null);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("simple");
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<"synced" | "not_linked" | "failed" | null>(null);

  async function requestExplanation(term = query, context = sentenceContext) {
    const trimmedTerm = term.trim();
    if (!trimmedTerm || isLoading) return;

    setQuery(trimmedTerm);
    setIsLoading(true);
    setError(null);
    setSaveMessage(null);
    setSaveStatus(null);
    setExplanation(null);
    try {
      const result = await vocabularyApi.explain({
        term: trimmedTerm,
        sentence_context: context.trim() || undefined,
        difficulty_level: difficulty,
      });
      setExplanation(result);
      setRecentSearches((current) => {
        const next = [trimmedTerm, ...current.filter((item) => item.toLowerCase() !== trimmedTerm.toLowerCase())].slice(0, 8);
        void AsyncStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(next));
        return next;
      });
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Could not explain this term."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    AsyncStorage.getItem(RECENT_SEARCHES_KEY)
      .then((stored) => setRecentSearches(stored ? JSON.parse(stored) : []))
      .catch(() => setRecentSearches([]));

    collectionsApi.list().then((items) => {
      setCollections(items);
      setSelectedCollectionId((current) => current ?? items[0]?.id ?? null);
    }).catch(() => setCollections([]));

  }, []);

  useEffect(() => {
    if (!initialQuery) return;
    setSentenceContext("");
    void requestExplanation(initialQuery, "");
    navigation.setParams({ query: undefined });
  }, [initialQuery]);

  const speakTerm = () => {
    if (!explanation) return;
    speakText(explanation.normalized_term);
  };

  const shareExplanation = async () => {
    if (!explanation) return;
    await Share.share({
      message: `${explanation.term}${explanation.part_of_speech ? ` (${explanation.part_of_speech})` : ""}\n\n${explanation.simple_meaning}\n\nExample: ${explanation.example}`,
      title: explanation.term,
    });
  };

  const exploreTerm = (term: string) => {
    setSentenceContext("");
    void requestExplanation(term, "");
  };

  const saveExplanation = async () => {
    if (!explanation || !selectedCollectionId || isSaving) return;

    setIsSaving(true);
    setSaveMessage(null);
    setSaveStatus(null);
    try {
      const savedEntry = await vocabularyApi.create({
        collection_id: selectedCollectionId,
        term: explanation.term,
        sentence_context: sentenceContext.trim() || null,
        example: explanation.example,
        synonyms: explanation.synonyms,
        part_of_speech: explanation.part_of_speech,
        pronunciation: explanation.pronunciation,
        usage_note: explanation.usage_note,
        meaning: explanation.meaning,
        simple_explanation: explanation.simple_meaning,
        contextual_explanation: explanation.contextual_meaning,
        difficulty_level: difficulty,
      });
      setSaveMessage(savedEntry.notion_message ?? "Saved to your collection.");
      setSaveStatus(savedEntry.notion_sync ?? null);
    } catch (saveError) {
      setSaveMessage(getApiErrorMessage(saveError, "Could not save this term."));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Text style={[styles.header, { color: colors.text }]}>Look up a word</Text>
      <Text style={[styles.subtitle, { color: colors.muted }]}>Understand the language in front of you, without leaving the page.</Text>

      <View style={[styles.searchField, { backgroundColor: colors.surface, borderColor: colors.border }]}>
        <Ionicons name="search-outline" size={20} color={colors.muted} />
        <TextInput
          value={query}
          onChangeText={(value) => {
            setQuery(value);
            setSaveMessage(null);
          }}
          onSubmitEditing={() => void requestExplanation()}
          placeholder="Word, phrase, idiom..."
          placeholderTextColor={colors.muted}
          style={[styles.searchInput, { color: colors.text }]}
          returnKeyType="search"
        />
        {query ? (
          <Pressable accessibilityLabel="Clear search" onPress={() => { setQuery(""); setExplanation(null); }} hitSlop={8}>
            <Ionicons name="close-circle" size={20} color={colors.muted} />
          </Pressable>
        ) : null}
      </View>

      <TextInput
        value={sentenceContext}
        onChangeText={setSentenceContext}
        placeholder="Sentence context (optional)"
        placeholderTextColor={colors.muted}
        style={[styles.contextInput, { backgroundColor: colors.surface, color: colors.text, borderColor: colors.border }]}
        multiline
      />

      <View style={[styles.difficultyControl, { backgroundColor: colors.surface }]}>
        {(["simple", "standard", "advanced"] as const).map((option) => {
          const selected = difficulty === option;
          return (
            <Pressable
              key={option}
              onPress={() => setDifficulty(option)}
              style={[styles.difficultyOption, selected && { backgroundColor: colors.primary }]}
            >
              <Text style={{ color: selected ? colors.onPrimary : colors.muted, fontSize: 12, fontWeight: "700", textTransform: "capitalize" }}>{option}</Text>
            </Pressable>
          );
        })}
      </View>

      <AnimatedPressable
        accessibilityRole="button"
        disabled={!query.trim() || isLoading}
        onPress={() => void requestExplanation()}
        style={[
          styles.primaryButton,
          { backgroundColor: colors.primary, opacity: !query.trim() || isLoading ? 0.45 : 1 },
        ]}
      >
        {isLoading ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={[styles.primaryButtonText, { color: colors.onPrimary }]}>Explain</Text>}
      </AnimatedPressable>

      {error ? <Text style={[styles.feedback, { color: colors.danger }]}>{error}</Text> : null}

      {!explanation && !isLoading && recentSearches.length ? (
        <View style={styles.recentsBlock}>
          <View style={styles.recentsHeader}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>Recent lookups</Text>
            <Pressable onPress={() => { setRecentSearches([]); void AsyncStorage.removeItem(RECENT_SEARCHES_KEY); }}>
              <Text style={{ color: colors.muted, fontSize: 12, fontWeight: "600" }}>Clear</Text>
            </Pressable>
          </View>
          <View style={styles.recentRow}>
            {recentSearches.map((term) => (
              <Pressable key={term} onPress={() => exploreTerm(term)} style={[styles.recentChip, { borderColor: colors.border, backgroundColor: colors.surface }]}>
                <Ionicons name="time-outline" size={14} color={colors.muted} />
                <Text style={{ color: colors.text, fontSize: 13 }}>{term}</Text>
              </Pressable>
            ))}
          </View>
        </View>
      ) : null}

      {explanation ? (
        <Animated.View entering={FadeInUp.duration(280)} style={[styles.resultCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <View style={styles.resultHeader}>
            <View style={styles.termGroup}>
              <View style={styles.termRow}>
                <Text style={[styles.term, { color: colors.text }]}>{explanation.term}</Text>
                {explanation.part_of_speech ? <Text style={[styles.partOfSpeech, { color: colors.primary }]}>{explanation.part_of_speech}</Text> : null}
              </View>
              {explanation.pronunciation ? <Text style={[styles.pronunciation, { color: colors.muted }]}>{explanation.pronunciation}</Text> : null}
              {explanation.normalized_term.toLowerCase() !== explanation.term.toLowerCase() ? (
                <Text style={[styles.normalized, { color: colors.muted }]}>Base form: {explanation.normalized_term}</Text>
              ) : null}
            </View>
            <View style={styles.resultActions}>
              {Platform.OS === "web" ? (
                <Pressable accessibilityLabel="Hear pronunciation" onPress={speakTerm} style={[styles.iconButton, { borderColor: colors.border }]}>
                  <Ionicons name="volume-medium-outline" size={20} color={colors.primary} />
                </Pressable>
              ) : null}
              <Pressable accessibilityLabel="Share explanation" onPress={() => void shareExplanation()} style={[styles.iconButton, { borderColor: colors.border }]}>
                <Ionicons name="share-outline" size={19} color={colors.primary} />
              </Pressable>
            </View>
          </View>

          <View style={[styles.primaryMeaning, { backgroundColor: colors.surfaceElevated }]}>
            <Text style={[styles.label, { color: colors.muted }]}>In plain English</Text>
            <Text style={[styles.primaryMeaningText, { color: colors.text }]}>{explanation.simple_meaning}</Text>
          </View>

          {explanation.contextual_meaning ? (
            <View style={[styles.contextBlock, { borderLeftColor: colors.primary }]}>
              <Text style={[styles.label, { color: colors.muted }]}>In this context</Text>
              <Text style={[styles.body, styles.compactBody, { color: colors.text }]}>{explanation.contextual_meaning}</Text>
            </View>
          ) : null}

          {difficulty !== "simple" ? (
            <>
              <Text style={[styles.label, { color: colors.muted }]}>Dictionary meaning</Text>
              <Text style={[styles.body, { color: colors.text }]}>{explanation.meaning}</Text>
            </>
          ) : null}

          <Text style={[styles.label, { color: colors.muted }]}>Example</Text>
          <Text style={[styles.body, styles.example, { color: colors.text, borderLeftColor: colors.primary }]}>{explanation.example}</Text>

          {explanation.synonyms.length ? (
            <>
              <Text style={[styles.label, { color: colors.muted }]}>Explore nearby words</Text>
              <View style={styles.synonymRow}>
                {explanation.synonyms.map((synonym) => (
                <Pressable key={synonym} onPress={() => exploreTerm(synonym)} style={[styles.synonym, { backgroundColor: colors.surfaceElevated }]}>
                  <Text style={{ color: colors.text }}>{synonym}</Text>
                  <Ionicons name="arrow-forward" size={13} color={colors.muted} />
                </Pressable>
                ))}
              </View>
            </>
          ) : null}

          {explanation.usage_note ? (
            <View style={[styles.usageNote, { borderColor: colors.border }]}>
              <Ionicons name="bulb-outline" size={17} color={colors.primary} />
              <Text style={[styles.usageNoteText, { color: colors.muted }]}>{explanation.usage_note}</Text>
            </View>
          ) : null}

          <View style={[styles.divider, { backgroundColor: colors.border }]} />
          <Text style={[styles.label, { color: colors.muted }]}>Save to collection</Text>
          {collections.length ? (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.collectionRow}>
              {collections.map((collection) => {
                const selected = collection.id === selectedCollectionId;
                return (
                  <Pressable
                    accessibilityRole="button"
                    key={collection.id}
                    onPress={() => setSelectedCollectionId(collection.id)}
                    style={[
                      styles.collectionOption,
                      { backgroundColor: selected ? colors.primary : colors.surfaceElevated, borderColor: selected ? colors.primary : colors.border },
                    ]}
                  >
                    {collection.notion_page_id ? <Ionicons name="document-text-outline" size={14} color={selected ? colors.onPrimary : colors.muted} /> : null}
                    <Text style={{ color: selected ? colors.onPrimary : colors.text, fontWeight: "600" }}>{collection.name}</Text>
                  </Pressable>
                );
              })}
            </ScrollView>
          ) : (
            <Pressable onPress={() => navigation.navigate("Collections")} style={[styles.createCollectionAction, { borderColor: colors.border }]}>
              <Text style={[styles.emptyCollections, { color: colors.muted }]}>No shelves yet.</Text>
              <Text style={{ color: colors.primary, fontWeight: "700" }}>Create a collection</Text>
            </Pressable>
          )}

          <AnimatedPressable
            accessibilityRole="button"
            disabled={!selectedCollectionId || isSaving}
            onPress={() => void saveExplanation()}
            style={[
              styles.saveButton,
              { borderColor: colors.primary, opacity: !selectedCollectionId || isSaving ? 0.45 : 1 },
            ]}
          >
            <Text style={[styles.saveButtonText, { color: colors.primary }]}>{isSaving ? "Saving..." : "Save word"}</Text>
          </AnimatedPressable>
          {saveMessage ? (
            <View style={styles.saveFeedback}>
              <Ionicons
                name={saveStatus === "synced" ? "cloud-done-outline" : saveStatus === "failed" ? "warning-outline" : "checkmark-circle-outline"}
                size={17}
                color={saveStatus === "failed" ? colors.danger : colors.primary}
              />
              <Text style={[styles.saveFeedbackText, { color: saveStatus === "failed" ? colors.danger : colors.muted }]}>{saveMessage}</Text>
            </View>
          ) : null}
        </Animated.View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 20, paddingTop: 60, paddingBottom: 48 },
  header: { fontSize: 26, fontWeight: "800", letterSpacing: 0 },
  subtitle: { fontSize: 14, lineHeight: 20, marginTop: 3, marginBottom: 22 },
  searchField: { minHeight: 52, flexDirection: "row", alignItems: "center", gap: 10, borderRadius: 8, borderWidth: 1, paddingHorizontal: 14, marginBottom: 10 },
  searchInput: { flex: 1, minHeight: 50, fontSize: 16 },
  contextInput: { minHeight: 72, borderRadius: 8, borderWidth: 1, padding: 14, fontSize: 15, marginBottom: 10, textAlignVertical: "top" },
  difficultyControl: { flexDirection: "row", borderRadius: 8, padding: 4, marginBottom: 12 },
  difficultyOption: { flex: 1, minHeight: 34, borderRadius: 6, alignItems: "center", justifyContent: "center" },
  primaryButton: { minHeight: 48, borderRadius: 8, alignItems: "center", justifyContent: "center", marginBottom: 16 },
  primaryButtonText: { fontSize: 15, fontWeight: "700" },
  recentsBlock: { marginTop: 8 },
  recentsHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 11 },
  sectionTitle: { fontSize: 15, fontWeight: "700" },
  recentRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  recentChip: { minHeight: 36, flexDirection: "row", alignItems: "center", gap: 6, borderWidth: 1, borderRadius: 8, paddingHorizontal: 10 },
  resultCard: { borderRadius: 8, borderWidth: 1, padding: 18 },
  resultHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 18 },
  termGroup: { flex: 1 },
  termRow: { flexDirection: "row", alignItems: "baseline", flexWrap: "wrap", gap: 8 },
  term: { fontSize: 26, fontWeight: "800" },
  partOfSpeech: { fontSize: 12, fontWeight: "800", textTransform: "uppercase" },
  pronunciation: { fontSize: 13, marginTop: 4 },
  normalized: { fontSize: 12, marginTop: 3 },
  resultActions: { flexDirection: "row", gap: 7 },
  iconButton: { width: 38, height: 38, borderWidth: 1, borderRadius: 8, alignItems: "center", justifyContent: "center" },
  primaryMeaning: { borderRadius: 8, padding: 15, marginBottom: 18 },
  primaryMeaningText: { fontSize: 17, lineHeight: 25, fontWeight: "600" },
  contextBlock: { borderLeftWidth: 3, paddingLeft: 13, marginBottom: 18 },
  label: { fontSize: 12, fontWeight: "600", textTransform: "uppercase", marginBottom: 4 },
  body: { fontSize: 15, lineHeight: 22, marginBottom: 16 },
  compactBody: { marginBottom: 0 },
  example: { borderLeftWidth: 3, paddingLeft: 12 },
  synonymRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 16 },
  synonym: { flexDirection: "row", alignItems: "center", gap: 6, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 7 },
  usageNote: { flexDirection: "row", alignItems: "flex-start", gap: 9, borderTopWidth: 1, borderBottomWidth: 1, paddingVertical: 12 },
  usageNoteText: { flex: 1, fontSize: 13, lineHeight: 19 },
  divider: { height: StyleSheet.hairlineWidth, marginVertical: 18 },
  collectionRow: { gap: 8, paddingVertical: 4, paddingRight: 8 },
  collectionOption: { flexDirection: "row", alignItems: "center", gap: 6, borderRadius: 8, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 9 },
  emptyCollections: { fontSize: 13, marginVertical: 8 },
  createCollectionAction: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", borderWidth: 1, borderRadius: 8, paddingHorizontal: 12, marginTop: 4 },
  saveButton: { minHeight: 44, borderRadius: 8, borderWidth: 1, alignItems: "center", justifyContent: "center", marginTop: 12 },
  saveButtonText: { fontSize: 14, fontWeight: "700" },
  feedback: { fontSize: 13, lineHeight: 18, marginTop: 4, marginBottom: 12 },
  saveFeedback: { flexDirection: "row", alignItems: "flex-start", gap: 7, marginTop: 11 },
  saveFeedbackText: { flex: 1, fontSize: 13, lineHeight: 18 },
});
