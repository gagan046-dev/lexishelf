import React, { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useNavigation } from "@react-navigation/native";
import Animated, { Layout, ZoomOut } from "react-native-reanimated";
import { Ionicons } from "@expo/vector-icons";

import { ConfirmModal } from "@/components/ConfirmModal";
import { useThemeColors } from "@/theme/ThemeContext";
import { speakText } from "@/utils/speech";
import { VocabularyEntry } from "@/types";

type Props = {
  entry: VocabularyEntry;
  onDelete: (id: string) => void;
};

const LEVEL_LABEL: Record<string, string> = {
  simple: "Simple",
  standard: "Standard",
  advanced: "Advanced",
};

export function VocabularyEntryRow({ entry, onDelete }: Props) {
  const colors = useThemeColors();
  const navigation = useNavigation<any>();
  const [confirmVisible, setConfirmVisible] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const hasExplanation = Boolean(entry.meaning || entry.simple_explanation || entry.contextual_explanation);

  return (
    <Animated.View
      layout={Layout.springify()}
      exiting={ZoomOut.duration(220)}
      style={[styles.row, { backgroundColor: colors.surface, borderColor: colors.border }]}
    >
      <View style={styles.headerRow}>
        <View style={styles.textGroup}>
          <View style={styles.termRow}>
            <Text style={[styles.term, { color: colors.text }]}>{entry.term}</Text>
            {entry.part_of_speech ? <Text style={[styles.wordType, { color: colors.primary }]}>{entry.part_of_speech}</Text> : null}
            <Pressable accessibilityLabel={`Hear ${entry.term}`} hitSlop={8} onPress={() => speakText(entry.term)}>
              <Ionicons name="volume-medium-outline" size={16} color={colors.muted} />
            </Pressable>
            {entry.pronunciation ? <Text style={[styles.pronunciation, { color: colors.muted }]}>{entry.pronunciation}</Text> : null}
          </View>
          {entry.example || entry.sentence_context ? (
            <Text style={[styles.example, { color: colors.muted }]} numberOfLines={expanded ? undefined : 2}>
              {entry.example || entry.sentence_context}
            </Text>
          ) : null}
          {entry.synonyms.length ? <Text style={[styles.synonyms, { color: colors.muted }]} numberOfLines={1}>Similar: {entry.synonyms.join(", ")}</Text> : null}
        </View>

        <Pressable
          accessibilityLabel={expanded ? "Hide meaning" : "View meaning"}
          hitSlop={8}
          onPress={() => setExpanded((current) => !current)}
          style={styles.iconButton}
        >
          <Ionicons name={expanded ? "chevron-up" : "chevron-down"} size={20} color={colors.muted} />
        </Pressable>
        <Pressable
          accessibilityLabel={`Delete ${entry.term}`}
          hitSlop={8}
          onPress={() => setConfirmVisible(true)}
          style={styles.iconButton}
        >
          <Ionicons name="trash-outline" size={18} color={colors.danger} />
        </Pressable>
      </View>

      {expanded ? (
        <View style={[styles.detail, { borderTopColor: colors.border }]}>
          {entry.difficulty_level ? (
            <View style={[styles.levelBadge, { backgroundColor: colors.surfaceElevated }]}>
              <Text style={{ color: colors.primary, fontSize: 11, fontWeight: "700" }}>
                {LEVEL_LABEL[entry.difficulty_level] ?? entry.difficulty_level} explanation
              </Text>
            </View>
          ) : null}

          {hasExplanation ? (
            <>
              {entry.simple_explanation ? (
                <View style={styles.detailSection}>
                  <Text style={[styles.detailLabel, { color: colors.muted }]}>Simple meaning</Text>
                  <Text style={[styles.detailBody, { color: colors.text }]}>{entry.simple_explanation}</Text>
                </View>
              ) : null}
              {entry.meaning ? (
                <View style={styles.detailSection}>
                  <Text style={[styles.detailLabel, { color: colors.muted }]}>Meaning</Text>
                  <Text style={[styles.detailBody, { color: colors.text }]}>{entry.meaning}</Text>
                </View>
              ) : null}
              {entry.contextual_explanation ? (
                <View style={styles.detailSection}>
                  <Text style={[styles.detailLabel, { color: colors.muted }]}>In this context</Text>
                  <Text style={[styles.detailBody, { color: colors.text }]}>{entry.contextual_explanation}</Text>
                </View>
              ) : null}
              {entry.usage_note ? (
                <View style={styles.detailSection}>
                  <Text style={[styles.detailLabel, { color: colors.muted }]}>Usage note</Text>
                  <Text style={[styles.detailBody, { color: colors.text }]}>{entry.usage_note}</Text>
                </View>
              ) : null}
            </>
          ) : (
            <View style={styles.noExplanation}>
              <Text style={[styles.detailBody, { color: colors.muted }]}>No saved meaning for this entry.</Text>
              <Pressable
                onPress={() => navigation.navigate("Main", { screen: "Search", params: { query: entry.term } })}
                style={[styles.lookupButton, { borderColor: colors.primary }]}
              >
                <Text style={{ color: colors.primary, fontWeight: "700", fontSize: 13 }}>Look up again</Text>
              </Pressable>
            </View>
          )}
        </View>
      ) : null}

      <ConfirmModal
        visible={confirmVisible}
        title={`Delete "${entry.term}"?`}
        message="This removes it from this collection in LexiShelf. It won't change anything already saved to Notion."
        onCancel={() => setConfirmVisible(false)}
        onConfirm={() => {
          setConfirmVisible(false);
          onDelete(entry.id);
        }}
      />
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  row: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    marginBottom: 10,
  },
  headerRow: { flexDirection: "row", alignItems: "flex-start" },
  textGroup: { flex: 1, marginRight: 8 },
  termRow: { flexDirection: "row", alignItems: "baseline", flexWrap: "wrap", gap: 7 },
  term: { fontSize: 15, fontWeight: "700" },
  wordType: { fontSize: 12, fontWeight: "700" },
  pronunciation: { fontSize: 12 },
  example: { fontSize: 13, lineHeight: 18, marginTop: 5, fontStyle: "italic" },
  synonyms: { fontSize: 12, marginTop: 5 },
  iconButton: { padding: 6 },
  detail: { borderTopWidth: StyleSheet.hairlineWidth, marginTop: 12, paddingTop: 12 },
  levelBadge: { alignSelf: "flex-start", borderRadius: 6, paddingHorizontal: 8, paddingVertical: 4, marginBottom: 10 },
  detailSection: { marginBottom: 10 },
  detailLabel: { fontSize: 11, fontWeight: "700", textTransform: "uppercase", marginBottom: 3 },
  detailBody: { fontSize: 14, lineHeight: 20 },
  noExplanation: { alignItems: "flex-start" },
  lookupButton: { borderWidth: 1, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 7, marginTop: 8 },
});
