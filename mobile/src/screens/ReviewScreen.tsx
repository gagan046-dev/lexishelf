import React, { useCallback, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import Animated, { FadeInUp, ZoomOut } from "react-native-reanimated";

import { getApiErrorMessage } from "@/api/client";
import { vocabularyApi } from "@/api/vocabulary";
import { MarkdownText } from "@/components/MarkdownText";
import { useThemeColors } from "@/theme/ThemeContext";
import { speakText } from "@/utils/speech";
import { VocabularyEntry } from "@/types";

type Grade = "again" | "hard" | "good" | "easy";

const GRADE_OPTIONS: { grade: Grade; label: string }[] = [
  { grade: "again", label: "Again" },
  { grade: "hard", label: "Hard" },
  { grade: "good", label: "Good" },
  { grade: "easy", label: "Easy" },
];

export function ReviewScreen() {
  const colors = useThemeColors();
  const [queue, setQueue] = useState<VocabularyEntry[]>([]);
  const [totalDue, setTotalDue] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isRevealed, setIsRevealed] = useState(false);
  const [isGrading, setIsGrading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setIsLoading(true);
    setError(null);
    setIsRevealed(false);
    vocabularyApi.listDueForReview(30)
      .then((entries) => {
        setQueue(entries);
        setTotalDue(entries.length);
      })
      .catch((loadError) => {
        setQueue([]);
        setError(getApiErrorMessage(loadError, "Could not load words due for review."));
      })
      .finally(() => setIsLoading(false));
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const current = queue[0];

  const grade = async (result: Grade) => {
    if (!current || isGrading) return;
    setIsGrading(true);
    try {
      await vocabularyApi.review(current.id, result);
      setQueue((remaining) => remaining.slice(1));
      setIsRevealed(false);
    } catch (gradeError) {
      setError(getApiErrorMessage(gradeError, "Could not save this review."));
    } finally {
      setIsGrading(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (!current) {
    return (
      <View style={styles.centered}>
        <Ionicons name="checkmark-done-circle-outline" size={48} color={colors.primary} />
        <Text style={[styles.emptyTitle, { color: colors.text }]}>All caught up!</Text>
        <Text style={[styles.emptyCopy, { color: colors.muted }]}>
          No saved words are due for review right now. Come back later.
        </Text>
        {error ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}
      </View>
    );
  }

  const remaining = queue.length;
  const hasDetail = Boolean(
    current.simple_explanation || current.meaning || current.contextual_explanation || current.example || current.usage_note,
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>Review</Text>
        <Text style={[styles.progress, { color: colors.muted }]}>{remaining} of {totalDue} remaining</Text>
      </View>

      {error ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}

      <Animated.View
        key={current.id}
        entering={FadeInUp.duration(240)}
        exiting={ZoomOut.duration(160)}
        style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}
      >
        <ScrollView contentContainerStyle={styles.cardScroll}>
          <View style={styles.termRow}>
            <Text style={[styles.term, { color: colors.text }]}>{current.term}</Text>
            <Pressable accessibilityLabel={`Hear ${current.term}`} hitSlop={8} onPress={() => speakText(current.term)}>
              <Ionicons name="volume-medium-outline" size={20} color={colors.muted} />
            </Pressable>
          </View>
          {current.part_of_speech ? <Text style={[styles.wordType, { color: colors.primary }]}>{current.part_of_speech}</Text> : null}
          {current.pronunciation ? <Text style={[styles.pronunciation, { color: colors.muted }]}>{current.pronunciation}</Text> : null}

          {isRevealed ? (
            <Animated.View entering={FadeInUp.duration(200)} style={styles.detail}>
              {current.simple_explanation ? (
                <View style={styles.detailSection}>
                  <Text style={[styles.detailLabel, { color: colors.muted }]}>Simple meaning</Text>
                  <MarkdownText style={[styles.detailBody, { color: colors.text }]}>{current.simple_explanation}</MarkdownText>
                </View>
              ) : null}
              {current.meaning ? (
                <View style={styles.detailSection}>
                  <Text style={[styles.detailLabel, { color: colors.muted }]}>Meaning</Text>
                  <MarkdownText style={[styles.detailBody, { color: colors.text }]}>{current.meaning}</MarkdownText>
                </View>
              ) : null}
              {current.example ? (
                <View style={styles.detailSection}>
                  <Text style={[styles.detailLabel, { color: colors.muted }]}>Example</Text>
                  <MarkdownText style={[styles.detailBody, { color: colors.text, fontStyle: "italic" }]}>{current.example}</MarkdownText>
                </View>
              ) : null}
              {current.synonyms.length ? (
                <Text style={[styles.synonyms, { color: colors.muted }]}>Similar: {current.synonyms.join(", ")}</Text>
              ) : null}
              {!hasDetail ? <Text style={[styles.detailBody, { color: colors.muted }]}>No saved meaning for this word.</Text> : null}
            </Animated.View>
          ) : null}
        </ScrollView>
      </Animated.View>

      {isRevealed ? (
        <View style={styles.gradeRow}>
          {GRADE_OPTIONS.map((option) => (
            <Pressable
              key={option.grade}
              disabled={isGrading}
              onPress={() => void grade(option.grade)}
              style={[styles.gradeButton, { borderColor: colors.border, opacity: isGrading ? 0.5 : 1 }]}
            >
              <Text style={{ color: colors.text, fontWeight: "700", fontSize: 13 }}>{option.label}</Text>
            </Pressable>
          ))}
        </View>
      ) : (
        <Pressable onPress={() => setIsRevealed(true)} style={[styles.revealButton, { backgroundColor: colors.primary }]}>
          <Text style={{ color: colors.onPrimary, fontWeight: "700", fontSize: 15 }}>Show answer</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, paddingTop: 60 },
  centered: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "baseline", marginBottom: 16 },
  title: { fontSize: 22, fontWeight: "800" },
  progress: { fontSize: 13 },
  error: { fontSize: 13, lineHeight: 18, marginBottom: 12 },
  card: { flex: 1, borderRadius: 8, borderWidth: 1, padding: 20, marginBottom: 18 },
  cardScroll: { flexGrow: 1 },
  termRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  term: { fontSize: 26, fontWeight: "800" },
  wordType: { fontSize: 13, fontWeight: "700", marginTop: 6 },
  pronunciation: { fontSize: 13, marginTop: 2 },
  detail: { marginTop: 20 },
  detailSection: { marginBottom: 14 },
  detailLabel: { fontSize: 11, fontWeight: "700", textTransform: "uppercase", marginBottom: 4 },
  detailBody: { fontSize: 15, lineHeight: 21 },
  synonyms: { fontSize: 13, marginTop: 4 },
  revealButton: { minHeight: 50, borderRadius: 8, alignItems: "center", justifyContent: "center" },
  gradeRow: { flexDirection: "row", gap: 8 },
  gradeButton: { flex: 1, minHeight: 50, borderWidth: 1, borderRadius: 8, alignItems: "center", justifyContent: "center" },
  emptyTitle: { fontSize: 19, fontWeight: "800", marginTop: 14, marginBottom: 6 },
  emptyCopy: { fontSize: 14, lineHeight: 20, textAlign: "center", maxWidth: 300 },
});
