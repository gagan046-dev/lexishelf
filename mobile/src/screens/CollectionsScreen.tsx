import React, { useCallback, useEffect, useRef, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Linking,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useFocusEffect, useNavigation } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";

import { collectionsApi } from "@/api/collections";
import { ApiError, getApiErrorMessage } from "@/api/client";
import { notionApi, NotionPage } from "@/api/notion";
import { vocabularyApi } from "@/api/vocabulary";
import { AnimatedFadeIn } from "@/components/AnimatedFadeIn";
import { CollectionCard } from "@/components/CollectionCard";
import { useTheme } from "@/theme/ThemeContext";
import { themes } from "@/theme/themes";
import { Collection, VocabularyEntrySearchResult } from "@/types";

const COLLECTION_DRAFT_KEY = "lexishelf.collection-draft";

type CollectionDraft = {
  name: string;
  description: string;
  themeId: string;
};

export function CollectionsScreen() {
  const { theme } = useTheme();
  const colors = theme.colors;
  const navigation = useNavigation<any>();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [themeId, setThemeId] = useState(theme.id);
  const [notionPages, setNotionPages] = useState<NotionPage[]>([]);
  const [selectedNotionPage, setSelectedNotionPage] = useState<NotionPage | null>(null);
  const [isLoadingNotion, setIsLoadingNotion] = useState(false);
  const [notionMessage, setNotionMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const notionPopupRef = useRef<Window | null>(null);
  const notionPopupTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<VocabularyEntrySearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const load = useCallback(() => {
    setIsLoading(true);
    setError(null);
    collectionsApi.list()
      .then(setCollections)
      .catch((loadError) => {
        setCollections([]);
        setError(getApiErrorMessage(loadError, "Could not load collections."));
      })
      .finally(() => setIsLoading(false));
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  useEffect(() => {
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      setSearchResults([]);
      setIsSearching(false);
      return undefined;
    }
    setIsSearching(true);
    const timeout = setTimeout(() => {
      vocabularyApi.search(trimmed)
        .then(setSearchResults)
        .catch(() => setSearchResults([]))
        .finally(() => setIsSearching(false));
    }, 300);
    return () => clearTimeout(timeout);
  }, [searchQuery]);

  useEffect(() => {
    AsyncStorage.getItem(COLLECTION_DRAFT_KEY)
      .then((storedDraft) => {
        if (!storedDraft) return;
        const draft = JSON.parse(storedDraft) as CollectionDraft;
        setName(draft.name);
        setDescription(draft.description);
        setThemeId(draft.themeId);
        setIsCreateOpen(true);
        setNotionMessage("Your collection draft was restored.");
        void loadNotionPages();
      })
      .catch(() => AsyncStorage.removeItem(COLLECTION_DRAFT_KEY));
  }, []);

  useEffect(() => {
    if (Platform.OS !== "web") return undefined;

    const handleNotionConnected = (event: MessageEvent) => {
      if (event.source !== notionPopupRef.current || event.data?.type !== "lexishelf:notion-connected") return;
      notionPopupRef.current = null;
      if (notionPopupTimerRef.current) clearInterval(notionPopupTimerRef.current);
      notionPopupTimerRef.current = null;
      void loadNotionPages(true);
    };
    window.addEventListener("message", handleNotionConnected);
    return () => {
      window.removeEventListener("message", handleNotionConnected);
      if (notionPopupTimerRef.current) clearInterval(notionPopupTimerRef.current);
    };
  }, []);

  const loadNotionPages = async (selectFirstPage = false) => {
    setIsLoadingNotion(true);
    setNotionMessage(null);
    try {
      const result = await notionApi.searchPages();
      setNotionPages(result.pages);
      if (!result.pages.length) {
        setSelectedNotionPage(null);
        setNotionMessage("Notion connected, but no pages were shared. Grant access to at least one page.");
      } else if (selectFirstPage) {
        setSelectedNotionPage(result.pages[0]);
        setNotionMessage(`Notion connected. “${result.pages[0].title}” is selected for this collection.`);
      }
    } catch (notionError) {
      setNotionPages([]);
      setNotionMessage(
        notionError instanceof ApiError && notionError.errorCode === "NOTION_NOT_CONNECTED"
          ? "Connect Notion to choose where this collection is stored."
          : getApiErrorMessage(notionError, "Could not load Notion pages."),
      );
    } finally {
      setIsLoadingNotion(false);
    }
  };

  const connectNotion = async () => {
    try {
      await AsyncStorage.setItem(
        COLLECTION_DRAFT_KEY,
        JSON.stringify({ name, description, themeId } satisfies CollectionDraft),
      );
      const result = await notionApi.authorizationUrl();
      if (Platform.OS === "web") {
        const popup = window.open(
          result.authorization_url,
          "lexishelf-notion-oauth",
          "popup=yes,width=560,height=760",
        );
        if (popup) {
          notionPopupRef.current = popup;
          if (notionPopupTimerRef.current) clearInterval(notionPopupTimerRef.current);
          notionPopupTimerRef.current = setInterval(() => {
            if (!popup.closed) return;
            if (notionPopupTimerRef.current) clearInterval(notionPopupTimerRef.current);
            notionPopupTimerRef.current = null;
            notionPopupRef.current = null;
            void loadNotionPages(true);
          }, 750);
          setNotionMessage("Finish connecting in the Notion window. Your draft is safe here.");
          return;
        }
      }
      await Linking.openURL(result.authorization_url);
      setNotionMessage("Complete authorization, then return here. Your draft is saved.");
    } catch (notionError) {
      setNotionMessage(getApiErrorMessage(notionError, "Could not start Notion authorization."));
    }
  };

  const openCreate = () => {
    setName("");
    setDescription("");
    setThemeId(theme.id);
    setSelectedNotionPage(null);
    setNotionPages([]);
    setNotionMessage(null);
    setError(null);
    setIsCreateOpen(true);
    void loadNotionPages();
  };

  const closeCreate = () => {
    setIsCreateOpen(false);
    void AsyncStorage.removeItem(COLLECTION_DRAFT_KEY);
  };

  const createCollection = async () => {
    const trimmedName = name.trim();
    if (!trimmedName || isCreating) return;

    setIsCreating(true);
    setError(null);
    try {
      const collection = await collectionsApi.create({
        name: trimmedName,
        description: description.trim() || undefined,
        theme_id: themeId,
        notion_page_id: selectedNotionPage?.id,
        notion_page_url: selectedNotionPage?.url ?? undefined,
      });
      await AsyncStorage.removeItem(COLLECTION_DRAFT_KEY);
      setIsCreateOpen(false);
      await load();
      navigation.navigate("CollectionDetail", { collectionId: collection.id });
    } catch (createError) {
      setError(getApiErrorMessage(createError, "Could not create the collection."));
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <View>
          <Text style={[styles.header, { color: colors.text }]}>Collections</Text>
          <Text style={[styles.subtitle, { color: colors.muted }]}>Keep new words close at hand.</Text>
        </View>
        <Pressable
          accessibilityLabel="Create collection"
          accessibilityRole="button"
          onPress={openCreate}
          style={({ pressed }) => [
            styles.addButton,
            { backgroundColor: colors.primary, opacity: pressed ? 0.78 : 1 },
          ]}
        >
          <Ionicons name="add" size={23} color={colors.onPrimary} />
        </Pressable>
      </View>

      {error && !isCreateOpen ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}

      <View style={[styles.searchBox, { backgroundColor: colors.surface, borderColor: colors.border }]}>
        <Ionicons name="search-outline" size={18} color={colors.muted} />
        <TextInput
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholder="Search saved words in every collection"
          placeholderTextColor={colors.muted}
          style={[styles.searchInput, { color: colors.text }]}
        />
        {searchQuery ? (
          <Pressable accessibilityLabel="Clear search" onPress={() => setSearchQuery("")} hitSlop={8}>
            <Ionicons name="close-circle" size={18} color={colors.muted} />
          </Pressable>
        ) : null}
      </View>

      {searchQuery.trim() ? (
        <FlatList
          data={searchResults}
          keyExtractor={(item) => item.id}
          contentContainerStyle={searchResults.length ? styles.list : styles.emptyList}
          renderItem={({ item, index }) => (
            <AnimatedFadeIn index={index}>
              <Pressable
                onPress={() => navigation.navigate("CollectionDetail", { collectionId: item.collection_id })}
                style={[styles.searchResult, { backgroundColor: colors.surface, borderColor: colors.border }]}
              >
                <View style={styles.searchResultHeader}>
                  <Text style={[styles.searchResultTerm, { color: colors.text }]}>{item.term}</Text>
                  {item.part_of_speech ? <Text style={[styles.searchResultType, { color: colors.primary }]}>{item.part_of_speech}</Text> : null}
                </View>
                <View style={[styles.searchResultBadge, { backgroundColor: colors.surfaceElevated }]}>
                  <Ionicons name="library-outline" size={12} color={colors.muted} />
                  <Text style={{ color: colors.muted, fontSize: 12 }}>{item.collection_name}</Text>
                </View>
              </Pressable>
            </AnimatedFadeIn>
          )}
          ListEmptyComponent={
            isSearching ? (
              <ActivityIndicator color={colors.primary} />
            ) : (
              <View style={styles.emptyState}>
                <Text style={[styles.emptyTitle, { color: colors.text }]}>No matches</Text>
                <Text style={[styles.emptyCopy, { color: colors.muted }]}>No saved words match “{searchQuery.trim()}”.</Text>
              </View>
            )
          }
        />
      ) : (
        <FlatList
        data={collections}
        keyExtractor={(item) => item.id}
        contentContainerStyle={collections.length ? styles.list : styles.emptyList}
        refreshing={isLoading && collections.length > 0}
        onRefresh={load}
        renderItem={({ item, index }) => (
          <AnimatedFadeIn index={index}>
            <CollectionCard
              collection={item}
              onPress={() => navigation.navigate("CollectionDetail", { collectionId: item.id })}
            />
          </AnimatedFadeIn>
        )}
        ListEmptyComponent={
          isLoading ? (
            <ActivityIndicator color={colors.primary} />
          ) : (
            <View style={styles.emptyState}>
              <View style={[styles.emptyIcon, { backgroundColor: colors.surface }]}>
                <Ionicons name="library-outline" size={28} color={colors.primary} />
              </View>
              <Text style={[styles.emptyTitle, { color: colors.text }]}>Start your first shelf</Text>
              <Text style={[styles.emptyCopy, { color: colors.muted }]}>Create a collection for words from a book, course, or topic.</Text>
              <Pressable onPress={openCreate} style={[styles.emptyAction, { borderColor: colors.primary }]}>
                <Text style={[styles.emptyActionText, { color: colors.primary }]}>Create collection</Text>
              </Pressable>
            </View>
          )
        }
      />
      )}

      <Modal visible={isCreateOpen} transparent animationType="fade" onRequestClose={closeCreate}>
        <KeyboardAvoidingView
          behavior={Platform.OS === "ios" ? "padding" : undefined}
          style={[styles.modalBackdrop, { backgroundColor: theme.isDark ? "rgba(0,0,0,0.68)" : "rgba(17,24,39,0.34)" }]}
        >
          <View style={[styles.modal, { backgroundColor: colors.background, borderColor: colors.border }]}>
            <View style={styles.modalHeader}>
              <View>
                <Text style={[styles.modalTitle, { color: colors.text }]}>New collection</Text>
                <Text style={[styles.modalSubtitle, { color: colors.muted }]}>Give this shelf a clear purpose.</Text>
              </View>
              <Pressable accessibilityLabel="Close" hitSlop={8} onPress={closeCreate}>
                <Ionicons name="close" size={24} color={colors.muted} />
              </Pressable>
            </View>

            <ScrollView keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>

            <Text style={[styles.fieldLabel, { color: colors.text }]}>Name</Text>
            <TextInput
              autoFocus
              maxLength={80}
              onChangeText={setName}
              placeholder="e.g. The Left Hand of Darkness"
              placeholderTextColor={colors.muted}
              style={[styles.input, { backgroundColor: colors.surface, borderColor: colors.border, color: colors.text }]}
              value={name}
            />

            <Text style={[styles.fieldLabel, { color: colors.text }]}>Description <Text style={{ color: colors.muted }}>(optional)</Text></Text>
            <TextInput
              maxLength={240}
              multiline
              onChangeText={setDescription}
              placeholder="What belongs on this shelf?"
              placeholderTextColor={colors.muted}
              style={[styles.input, styles.descriptionInput, { backgroundColor: colors.surface, borderColor: colors.border, color: colors.text }]}
              value={description}
            />

            <Text style={[styles.fieldLabel, { color: colors.text }]}>Cover palette</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.paletteRow}>
              {themes.map((option) => {
                const selected = option.id === themeId;
                return (
                  <Pressable
                    accessibilityLabel={`${option.name} palette`}
                    key={option.id}
                    onPress={() => setThemeId(option.id)}
                    style={[
                      styles.palette,
                      { backgroundColor: option.colors.surface, borderColor: selected ? colors.primary : option.colors.border },
                    ]}
                  >
                    <View style={[styles.paletteSwatch, { backgroundColor: option.colors.primary }]} />
                    <Text style={[styles.paletteName, { color: option.colors.text }]}>{option.name}</Text>
                  </Pressable>
                );
              })}
            </ScrollView>

            <Text style={[styles.fieldLabel, { color: colors.text }]}>Notion page <Text style={{ color: colors.muted }}>(optional)</Text></Text>
            {isLoadingNotion ? (
              <ActivityIndicator color={colors.primary} style={styles.notionLoader} />
            ) : notionPages.length ? (
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.notionPageRow}>
                <Pressable
                  onPress={() => setSelectedNotionPage(null)}
                  style={[styles.notionPage, { borderColor: selectedNotionPage ? colors.border : colors.primary, backgroundColor: colors.surface }]}
                >
                  <Ionicons name="phone-portrait-outline" size={18} color={colors.muted} />
                  <Text style={[styles.notionPageName, { color: colors.text }]}>Local only</Text>
                </Pressable>
                {notionPages.map((page) => {
                  const selected = page.id === selectedNotionPage?.id;
                  return (
                    <Pressable
                      key={page.id}
                      onPress={() => setSelectedNotionPage(page)}
                      style={[styles.notionPage, { borderColor: selected ? colors.primary : colors.border, backgroundColor: colors.surface }]}
                    >
                      <Ionicons name="document-text-outline" size={18} color={selected ? colors.primary : colors.muted} />
                      <Text style={[styles.notionPageName, { color: colors.text }]} numberOfLines={2}>{page.title}</Text>
                    </Pressable>
                  );
                })}
              </ScrollView>
            ) : null}

            {notionMessage ? <Text style={[styles.notionMessage, { color: colors.muted }]}>{notionMessage}</Text> : null}
            <View style={styles.notionActions}>
              <Pressable onPress={() => void connectNotion()} style={[styles.secondaryButton, { borderColor: colors.border }]}>
                <Ionicons name="link-outline" size={16} color={colors.primary} />
                <Text style={{ color: colors.primary, fontWeight: "700" }}>Connect Notion</Text>
              </Pressable>
              <Pressable onPress={() => void loadNotionPages()} style={[styles.secondaryButton, { borderColor: colors.border }]}>
                <Ionicons name="refresh" size={16} color={colors.primary} />
                <Text style={{ color: colors.primary, fontWeight: "700" }}>Refresh</Text>
              </Pressable>
            </View>

            {error ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}

            <Pressable
              disabled={!name.trim() || isCreating}
              onPress={() => void createCollection()}
              style={({ pressed }) => [
                styles.createButton,
                { backgroundColor: colors.primary, opacity: !name.trim() || isCreating ? 0.45 : pressed ? 0.78 : 1 },
              ]}
            >
              {isCreating ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={[styles.createButtonText, { color: colors.onPrimary }]}>Create collection</Text>}
            </Pressable>
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, paddingTop: 60 },
  headerRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 22 },
  header: { fontSize: 26, fontWeight: "800", letterSpacing: 0 },
  subtitle: { fontSize: 14, marginTop: 3 },
  addButton: { width: 44, height: 44, borderRadius: 8, alignItems: "center", justifyContent: "center" },
  searchBox: { minHeight: 46, flexDirection: "row", alignItems: "center", borderRadius: 8, borderWidth: 1, paddingHorizontal: 12, marginBottom: 16, gap: 8 },
  searchInput: { flex: 1, fontSize: 14, minHeight: 44 },
  searchResult: { borderRadius: 8, borderWidth: 1, padding: 14, marginBottom: 10 },
  searchResultHeader: { flexDirection: "row", alignItems: "baseline", gap: 8, marginBottom: 8 },
  searchResultTerm: { fontSize: 15, fontWeight: "700" },
  searchResultType: { fontSize: 12, fontWeight: "700" },
  searchResultBadge: { flexDirection: "row", alignSelf: "flex-start", alignItems: "center", gap: 6, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 4 },
  list: { paddingBottom: 28 },
  emptyList: { flexGrow: 1, justifyContent: "center", paddingBottom: 80 },
  emptyState: { alignItems: "center", paddingHorizontal: 24 },
  emptyIcon: { width: 58, height: 58, borderRadius: 8, alignItems: "center", justifyContent: "center", marginBottom: 16 },
  emptyTitle: { fontSize: 18, fontWeight: "700", marginBottom: 6 },
  emptyCopy: { fontSize: 14, lineHeight: 20, textAlign: "center", maxWidth: 310 },
  emptyAction: { borderWidth: 1, borderRadius: 8, paddingHorizontal: 16, paddingVertical: 10, marginTop: 18 },
  emptyActionText: { fontSize: 14, fontWeight: "700" },
  error: { fontSize: 13, lineHeight: 18, marginBottom: 12 },
  modalBackdrop: { flex: 1, justifyContent: "center", padding: 20 },
  modal: { width: "100%", maxWidth: 520, maxHeight: "90%", alignSelf: "center", borderWidth: 1, borderRadius: 8, padding: 20 },
  modalHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 22 },
  modalTitle: { fontSize: 22, fontWeight: "800" },
  modalSubtitle: { fontSize: 13, marginTop: 3 },
  fieldLabel: { fontSize: 13, fontWeight: "700", marginBottom: 7 },
  input: { borderWidth: 1, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 11, fontSize: 15, marginBottom: 16 },
  descriptionInput: { minHeight: 76, textAlignVertical: "top" },
  paletteRow: { gap: 8, paddingBottom: 18 },
  palette: { width: 92, minHeight: 66, borderWidth: 2, borderRadius: 8, justifyContent: "center", padding: 9 },
  paletteSwatch: { width: 22, height: 8, borderRadius: 4, marginBottom: 7 },
  paletteName: { fontSize: 12, fontWeight: "700" },
  notionLoader: { alignSelf: "flex-start", marginVertical: 12 },
  notionPageRow: { gap: 8, paddingBottom: 10 },
  notionPage: { width: 130, minHeight: 68, borderWidth: 2, borderRadius: 8, padding: 10, gap: 6 },
  notionPageName: { fontSize: 12, fontWeight: "700" },
  notionMessage: { fontSize: 12, lineHeight: 17, marginBottom: 9 },
  notionActions: { flexDirection: "row", gap: 8, marginBottom: 18 },
  secondaryButton: { minHeight: 38, flexDirection: "row", alignItems: "center", gap: 6, borderWidth: 1, borderRadius: 8, paddingHorizontal: 10 },
  createButton: { minHeight: 48, borderRadius: 8, alignItems: "center", justifyContent: "center", marginTop: 4 },
  createButtonText: { fontSize: 15, fontWeight: "800" },
});
