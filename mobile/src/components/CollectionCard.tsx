import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { useThemeColors } from "@/theme/ThemeContext";
import { Collection } from "@/types";

type Props = {
  collection: Collection;
  onPress: () => void;
};

export function CollectionCard({ collection, onPress }: Props) {
  const colors = useThemeColors();

  return (
    <Pressable
      onPress={onPress}
      style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}
    >
      <View style={styles.headerRow}>
        <View style={[styles.bookMark, { backgroundColor: colors.surfaceElevated }]}>
          <Ionicons name="book-outline" size={18} color={colors.primary} />
        </View>
        <View style={styles.copy}>
          <Text style={[styles.title, { color: colors.text }]}>{collection.name}</Text>
          {collection.description ? <Text style={[styles.description, { color: colors.muted }]} numberOfLines={1}>{collection.description}</Text> : null}
        </View>
        <Ionicons name="chevron-forward" size={18} color={colors.muted} />
      </View>
      <View style={styles.metaRow}>
        <Text style={[styles.subtitle, { color: colors.muted }]}>{collection.word_count} {collection.word_count === 1 ? "word" : "words"}</Text>
        <View style={styles.syncState}>
          <Ionicons name={collection.notion_page_id ? "cloud-done-outline" : "phone-portrait-outline"} size={14} color={collection.notion_page_id ? colors.primary : colors.muted} />
          <Text style={{ color: collection.notion_page_id ? colors.primary : colors.muted, fontSize: 12 }}>{collection.notion_page_id ? "Notion linked" : "Local"}</Text>
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 8,
    borderWidth: 1,
    padding: 16,
    marginBottom: 12,
  },
  headerRow: { flexDirection: "row", alignItems: "center", gap: 11 },
  bookMark: { width: 38, height: 38, borderRadius: 7, alignItems: "center", justifyContent: "center" },
  copy: { flex: 1 },
  title: { fontSize: 16, fontWeight: "700" },
  description: { fontSize: 12, marginTop: 2 },
  metaRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: 13 },
  subtitle: { fontSize: 12 },
  syncState: { flexDirection: "row", alignItems: "center", gap: 5 },
});
