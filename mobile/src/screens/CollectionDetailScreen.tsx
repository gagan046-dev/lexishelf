import React, { useCallback, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useFocusEffect, useNavigation, useRoute } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";

import { collectionsApi } from "@/api/collections";
import { getApiErrorMessage } from "@/api/client";
import { vocabularyApi } from "@/api/vocabulary";
import { ConfirmModal } from "@/components/ConfirmModal";
import { VocabularyEntryRow } from "@/components/VocabularyEntryRow";
import { useThemeColors } from "@/theme/ThemeContext";
import { Collection, VocabularyEntry } from "@/types";

export function CollectionDetailScreen() {
  const colors = useThemeColors();
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { collectionId } = route.params as { collectionId: string };

  const [collection, setCollection] = useState<Collection | null>(null);
  const [entries, setEntries] = useState<VocabularyEntry[]>([]);
  const [deleteCollectionVisible, setDeleteCollectionVisible] = useState(false);
  const [isDeletingCollection, setIsDeletingCollection] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setIsLoading(true);
    setError(null);
    Promise.all([collectionsApi.get(collectionId), vocabularyApi.listByCollection(collectionId)])
      .then(([collectionResult, entriesResult]) => {
        setCollection(collectionResult);
        setEntries(entriesResult);
      })
      .catch((loadError) => setError(getApiErrorMessage(loadError, "Could not load this collection.")))
      .finally(() => setIsLoading(false));
  }, [collectionId]);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const handleDeleteEntry = async (entryId: string) => {
    const previous = entries;
    setEntries((current) => current.filter((entry) => entry.id !== entryId));
    try {
      await vocabularyApi.remove(entryId);
    } catch (err) {
      setEntries(previous);
      setError(getApiErrorMessage(err, "Could not delete this word."));
    }
  };

  const handleDeleteCollection = async () => {
    setIsDeletingCollection(true);
    try {
      await collectionsApi.remove(collectionId);
      setDeleteCollectionVisible(false);
      navigation.goBack();
    } catch (deleteError) {
      setIsDeletingCollection(false);
      setDeleteCollectionVisible(false);
      setError(getApiErrorMessage(deleteError, "Could not delete this collection."));
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Pressable accessibilityLabel="Back" onPress={() => navigation.goBack()} style={[styles.iconButton, { borderColor: colors.border }]}>
          <Ionicons name="arrow-back" size={21} color={colors.text} />
        </Pressable>
        <View style={styles.titleGroup}>
          <Text style={[styles.title, { color: colors.text }]} numberOfLines={1}>{collection?.name ?? "Collection"}</Text>
          <Text style={[styles.subtitle, { color: colors.muted }]}>{entries.length} saved words</Text>
        </View>
        <Pressable accessibilityLabel="Delete collection" onPress={() => setDeleteCollectionVisible(true)} style={[styles.iconButton, { borderColor: colors.border }]}>
          <Ionicons name="trash-outline" size={20} color={colors.danger} />
        </Pressable>
      </View>

      {collection?.description ? <Text style={[styles.description, { color: colors.muted }]}>{collection.description}</Text> : null}
      {error ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}

      <FlatList
        data={entries}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <VocabularyEntryRow entry={item} onDelete={handleDeleteEntry} />}
        contentContainerStyle={entries.length ? styles.list : styles.emptyList}
        refreshing={isLoading && entries.length > 0}
        onRefresh={load}
        ListEmptyComponent={isLoading ? (
          <ActivityIndicator color={colors.primary} />
        ) : (
          <View style={styles.emptyState}>
            <Ionicons name="bookmark-outline" size={28} color={colors.primary} />
            <Text style={[styles.emptyTitle, { color: colors.text }]}>No saved words yet</Text>
            <Text style={[styles.emptyCopy, { color: colors.muted }]}>Look up a word and save it to this collection.</Text>
            <Pressable
              onPress={() => navigation.navigate("Main", { screen: "Search" })}
              style={[styles.addWordButton, { backgroundColor: colors.primary }]}
            >
              <Text style={{ color: colors.onPrimary, fontWeight: "700" }}>Look up a word</Text>
            </Pressable>
          </View>
        )}
      />

      <ConfirmModal
        visible={deleteCollectionVisible}
        title={`Delete "${collection?.name ?? "this collection"}"?`}
        message={`This will permanently remove this collection and all ${entries.length} saved words from LexiShelf. This does NOT delete anything from Notion.`}
        confirmLabel={isDeletingCollection ? "Deleting…" : "Delete Collection"}
        onCancel={() => setDeleteCollectionVisible(false)}
        onConfirm={handleDeleteCollection}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, paddingTop: 60 },
  headerRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  iconButton: { width: 42, height: 42, borderWidth: 1, borderRadius: 8, alignItems: "center", justifyContent: "center" },
  titleGroup: { flex: 1 },
  title: { fontSize: 20, fontWeight: "800" },
  subtitle: { fontSize: 12, marginTop: 2 },
  description: { fontSize: 14, lineHeight: 20, marginTop: 16 },
  error: { fontSize: 13, lineHeight: 18, marginTop: 12 },
  list: { paddingTop: 18, paddingBottom: 24 },
  emptyList: { flexGrow: 1, justifyContent: "center" },
  emptyState: { alignItems: "center", paddingHorizontal: 24, paddingBottom: 60 },
  emptyTitle: { fontSize: 18, fontWeight: "700", marginTop: 13, marginBottom: 5 },
  emptyCopy: { fontSize: 14, lineHeight: 20, textAlign: "center" },
  addWordButton: { minHeight: 44, borderRadius: 8, paddingHorizontal: 16, alignItems: "center", justifyContent: "center", marginTop: 17 },
});
