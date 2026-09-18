import React, { useCallback, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useFocusEffect, useNavigation } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";

import { collectionsApi } from "@/api/collections";
import { getApiErrorMessage } from "@/api/client";
import { vocabularyApi } from "@/api/vocabulary";
import { useAuth } from "@/auth/AuthContext";
import { AnimatedFadeIn } from "@/components/AnimatedFadeIn";
import { CollectionCard } from "@/components/CollectionCard";
import { useThemeColors } from "@/theme/ThemeContext";
import { Collection } from "@/types";

export function HomeScreen() {
  const colors = useThemeColors();
  const navigation = useNavigation<any>();
  const { logout } = useAuth();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dueCount, setDueCount] = useState(0);

  const load = useCallback(() => {
    setIsLoading(true);
    setError(null);
    collectionsApi.list()
      .then(setCollections)
      .catch((loadError) => {
        setCollections([]);
        setError(getApiErrorMessage(loadError, "Could not load your shelves."));
      })
      .finally(() => setIsLoading(false));
    vocabularyApi.listDueForReview(100).then((entries) => setDueCount(entries.length)).catch(() => setDueCount(0));
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const savedWordCount = collections.reduce((total, collection) => total + collection.word_count, 0);

  return (
    <View style={[styles.container, { backgroundColor: "transparent" }]}>
      <AnimatedFadeIn>
        <View style={styles.headerRow}>
          <View>
            <Text style={[styles.brand, { color: colors.primary }]}>LexiShelf</Text>
            <Text style={[styles.greeting, { color: colors.text }]}>Your reading, remembered.</Text>
          </View>
          <Pressable accessibilityLabel="Sign out" onPress={() => void logout()} hitSlop={8} style={[styles.iconButton, { borderColor: colors.border }]}>
            <Ionicons name="log-out-outline" color={colors.muted} size={20} />
          </Pressable>
        </View>
      </AnimatedFadeIn>

      <AnimatedFadeIn index={1}>
        <View style={[styles.searchBox, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <Ionicons name="search-outline" size={19} color={colors.muted} />
          <TextInput
            placeholder="Search a word or phrase"
            placeholderTextColor={colors.muted}
            onSubmitEditing={(event) => navigation.navigate("Search", { query: event.nativeEvent.text })}
            style={[styles.searchInput, { color: colors.text }]}
          />
        </View>
      </AnimatedFadeIn>

      <AnimatedFadeIn index={2}>
        <View style={[styles.stats, { borderColor: colors.border }]}>
          <View style={styles.stat}>
            <Text style={[styles.statValue, { color: colors.text }]}>{savedWordCount}</Text>
            <Text style={[styles.statLabel, { color: colors.muted }]}>Saved words</Text>
          </View>
          <View style={[styles.statDivider, { backgroundColor: colors.border }]} />
          <View style={styles.stat}>
            <Text style={[styles.statValue, { color: colors.text }]}>{collections.length}</Text>
            <Text style={[styles.statLabel, { color: colors.muted }]}>Collections</Text>
          </View>
          <View style={[styles.statDivider, { backgroundColor: colors.border }]} />
          <Pressable style={styles.stat} onPress={() => navigation.navigate("Review")}>
            <Text style={[styles.statValue, { color: dueCount ? colors.primary : colors.text }]}>{dueCount}</Text>
            <Text style={[styles.statLabel, { color: colors.muted }]}>Due for review</Text>
          </Pressable>
        </View>
      </AnimatedFadeIn>

      <View style={styles.sectionRow}>
        <Text style={[styles.sectionLabel, { color: colors.text }]}>Recent collections</Text>
        <Pressable onPress={() => navigation.navigate("Collections")}>
          <Text style={{ color: colors.primary, fontSize: 13, fontWeight: "700" }}>View all</Text>
        </Pressable>
      </View>

      {error ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}

      <FlatList
        data={collections.slice(0, 4)}
        keyExtractor={(item) => item.id}
        contentContainerStyle={!collections.length ? styles.emptyList : styles.list}
        refreshing={isLoading && collections.length > 0}
        onRefresh={load}
        renderItem={({ item, index }) => (
          <AnimatedFadeIn index={index + 3}>
            <CollectionCard
              collection={item}
              onPress={() => navigation.navigate("CollectionDetail", { collectionId: item.id })}
            />
          </AnimatedFadeIn>
        )}
        ListEmptyComponent={isLoading ? (
          <ActivityIndicator color={colors.primary} />
        ) : (
          <View style={styles.emptyState}>
            <Text style={[styles.emptyTitle, { color: colors.text }]}>A quiet shelf, for now.</Text>
            <Text style={[styles.emptyCopy, { color: colors.muted }]}>Create a collection, then save words as you discover them.</Text>
            <Pressable onPress={() => navigation.navigate("Collections")} style={[styles.emptyAction, { borderColor: colors.primary }]}>
              <Text style={{ color: colors.primary, fontWeight: "700" }}>Create collection</Text>
            </Pressable>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, paddingTop: 60 },
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  brand: { fontSize: 14, fontWeight: "800", textTransform: "uppercase" },
  greeting: { fontSize: 25, fontWeight: "800", letterSpacing: 0, marginTop: 2 },
  iconButton: { width: 42, height: 42, borderWidth: 1, borderRadius: 8, alignItems: "center", justifyContent: "center" },
  searchBox: { minHeight: 50, flexDirection: "row", alignItems: "center", borderRadius: 8, borderWidth: 1, paddingHorizontal: 14, marginTop: 24, marginBottom: 16, gap: 9 },
  searchInput: { flex: 1, fontSize: 15, minHeight: 48 },
  stats: { flexDirection: "row", borderTopWidth: 1, borderBottomWidth: 1, paddingVertical: 15, marginBottom: 25 },
  stat: { flex: 1 },
  statValue: { fontSize: 22, fontWeight: "800" },
  statLabel: { fontSize: 12, marginTop: 2 },
  statDivider: { width: 1, marginHorizontal: 20 },
  sectionRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 12 },
  sectionLabel: { fontSize: 16, fontWeight: "700" },
  list: { paddingBottom: 24 },
  emptyList: { flexGrow: 1 },
  emptyState: { alignItems: "flex-start", paddingTop: 24 },
  emptyTitle: { fontSize: 17, fontWeight: "700", marginBottom: 5 },
  emptyCopy: { fontSize: 14, lineHeight: 20, maxWidth: 330 },
  emptyAction: { borderWidth: 1, borderRadius: 8, paddingHorizontal: 14, paddingVertical: 9, marginTop: 16 },
  error: { fontSize: 13, lineHeight: 18, marginBottom: 12 },
});
