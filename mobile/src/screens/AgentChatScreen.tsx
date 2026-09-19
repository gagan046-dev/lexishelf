import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInUp } from "react-native-reanimated";
import { Ionicons } from "@expo/vector-icons";

import { chatApi } from "@/api/chat";
import { getApiErrorMessage } from "@/api/client";
import { collectionsApi } from "@/api/collections";
import { telegramApi } from "@/api/telegram";
import { AnimatedPressable } from "@/components/AnimatedPressable";
import { MarkdownText } from "@/components/MarkdownText";
import { useThemeColors } from "@/theme/ThemeContext";
import { AgentAction, Collection } from "@/types";

type ChatMessage = {
  id: string;
  role: "user" | "agent";
  text: string;
  actions?: AgentAction[];
};

export function AgentChatScreen() {
  const colors = useThemeColors();
  const insets = useSafeAreaInsets();
  const listRef = useRef<FlatList<ChatMessage>>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [collections, setCollections] = useState<Collection[]>([]);
  const [collectionId, setCollectionId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isTelegramModalOpen, setIsTelegramModalOpen] = useState(false);

  useEffect(() => {
    collectionsApi.list().then(setCollections).catch(() => setCollections([]));
  }, []);

  const send = async () => {
    const message = draft.trim();
    if (!message || isSending) return;

    const messageId = Date.now().toString();
    setMessages((current) => [...current, { id: `${messageId}-user`, role: "user", text: message }]);
    setDraft("");
    setError(null);
    setIsSending(true);
    try {
      const response = await chatApi.send({
        message,
        collection_id: collectionId ?? undefined,
      });
      setMessages((current) => [
        ...current,
        {
          id: response.request_id || `${messageId}-agent`,
          role: "agent",
          text: response.message,
          actions: response.actions,
        },
      ]);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "The assistant could not respond."));
    } finally {
      setIsSending(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { paddingTop: insets.top + 20 }]}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={Platform.OS === "ios" ? insets.bottom : 0}
    >
      <View style={styles.headerRow}>
        <View style={styles.headerCopy}>
          <Text style={[styles.header, { color: colors.text }]}>Agent Chat</Text>
          <Text style={[styles.subtitle, { color: colors.muted }]}>Ask LexiShelf to explain, organize, and save vocabulary.</Text>
        </View>
        <Pressable
          accessibilityLabel="Connect Telegram"
          onPress={() => setIsTelegramModalOpen(true)}
          style={[styles.telegramButton, { borderColor: colors.border }]}
        >
          <Ionicons name="paper-plane-outline" size={18} color={colors.primary} />
        </Pressable>
      </View>

      {collections.length ? (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.collectionRow}
          style={styles.collectionScroller}
        >
          <Pressable
            onPress={() => setCollectionId(null)}
            style={[
              styles.collectionOption,
              { backgroundColor: collectionId ? colors.surface : colors.primary, borderColor: collectionId ? colors.border : colors.primary },
            ]}
          >
            <Text style={{ color: collectionId ? colors.text : colors.onPrimary, fontWeight: "600" }}>No collection</Text>
          </Pressable>
          {collections.map((collection) => {
            const selected = collection.id === collectionId;
            return (
              <Pressable
                key={collection.id}
                onPress={() => setCollectionId(collection.id)}
                style={[
                  styles.collectionOption,
                  { backgroundColor: selected ? colors.primary : colors.surface, borderColor: selected ? colors.primary : colors.border },
                ]}
              >
                <Text style={{ color: selected ? colors.onPrimary : colors.text, fontWeight: "600" }}>{collection.name}</Text>
              </Pressable>
            );
          })}
        </ScrollView>
      ) : null}

      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(item) => item.id}
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
        renderItem={({ item }) => (
          <Animated.View
            entering={FadeInUp.duration(220)}
            style={[
              styles.bubble,
              item.role === "user"
                ? { backgroundColor: colors.primary, alignSelf: "flex-end" }
                : { backgroundColor: colors.surface, alignSelf: "flex-start", borderColor: colors.border, borderWidth: 1 },
            ]}
          >
            <MarkdownText style={{ color: item.role === "user" ? colors.onPrimary : colors.text, lineHeight: 20 }}>
              {item.text}
            </MarkdownText>
            {item.actions?.map((action, index) => (
              <View key={`${action.type}-${index}`} style={[styles.actionRow, { borderTopColor: colors.border }]}>
                <Text style={{ color: action.status === "success" ? colors.primary : colors.danger, fontSize: 12, fontWeight: "700" }}>
                  {action.status === "success" ? "Completed" : "Failed"}
                </Text>
                <Text style={{ color: colors.muted, fontSize: 12, flex: 1 }}>{action.message}</Text>
              </View>
            ))}
          </Animated.View>
        )}
        ListEmptyComponent={(
          <View style={styles.emptyState}>
            <Text style={[styles.emptyTitle, { color: colors.text }]}>Ask about what you are reading</Text>
            <Text style={[styles.emptyBody, { color: colors.muted }]}>Explain a phrase, create a collection, or save a result to a selected collection.</Text>
          </View>
        )}
        contentContainerStyle={styles.messages}
      />

      {isSending ? (
        <View style={styles.thinkingRow}>
          <ActivityIndicator size="small" color={colors.primary} />
          <Text style={{ color: colors.muted, fontSize: 13 }}>Working on your request...</Text>
        </View>
      ) : null}
      {error ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}

      <View style={styles.composerRow}>
        <TextInput
          value={draft}
          onChangeText={setDraft}
          onSubmitEditing={() => void send()}
          placeholder='e.g. "Explain omen and save it"'
          placeholderTextColor={colors.muted}
          style={[styles.input, { backgroundColor: colors.surface, color: colors.text, borderColor: colors.border }]}
          returnKeyType="send"
        />
        <AnimatedPressable
          accessibilityLabel="Send message"
          accessibilityRole="button"
          disabled={!draft.trim() || isSending}
          onPress={() => void send()}
          style={[styles.sendButton, { backgroundColor: colors.primary, opacity: !draft.trim() || isSending ? 0.4 : 1 }]}
        >
          <Text style={[styles.sendButtonText, { color: colors.onPrimary }]}>Send</Text>
        </AnimatedPressable>
      </View>

      <TelegramLinkModal visible={isTelegramModalOpen} onClose={() => setIsTelegramModalOpen(false)} />
    </KeyboardAvoidingView>
  );
}

function TelegramLinkModal({ visible, onClose }: { visible: boolean; onClose: () => void }) {
  const colors = useThemeColors();
  const [code, setCode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) return;
    setIsLoading(true);
    setError(null);
    telegramApi.getLinkCode()
      .then((result) => setCode(result.code))
      .catch((requestError) => setError(getApiErrorMessage(requestError, "Could not generate a link code.")))
      .finally(() => setIsLoading(false));
  }, [visible]);

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.modalBackdrop}>
        <View style={[styles.modal, { backgroundColor: colors.background, borderColor: colors.border }]}>
          <Text style={[styles.modalTitle, { color: colors.text }]}>Connect Telegram</Text>
          <Text style={[styles.modalSubtitle, { color: colors.muted }]}>
            Chat with your LexiShelf assistant straight from Telegram, on any device.
          </Text>

          {isLoading ? (
            <ActivityIndicator color={colors.primary} style={{ marginVertical: 20 }} />
          ) : error ? (
            <Text style={[styles.error, { color: colors.danger }]}>{error}</Text>
          ) : code ? (
            <>
              <View style={[styles.codeBox, { backgroundColor: colors.surfaceElevated, borderColor: colors.border }]}>
                <Text style={[styles.codeText, { color: colors.text }]}>{code}</Text>
              </View>
              <Text style={[styles.modalStep, { color: colors.muted }]}>1. Open Telegram and find your LexiShelf bot.</Text>
              <Text style={[styles.modalStep, { color: colors.muted }]}>2. Send: /link {code}</Text>
              <Text style={[styles.modalStep, { color: colors.muted }]}>3. You're linked — chat with it anytime.</Text>
              <Text style={[styles.modalNote, { color: colors.muted }]}>This code expires in 10 minutes.</Text>
            </>
          ) : null}

          <Pressable onPress={onClose} style={[styles.modalClose, { borderColor: colors.primary }]}>
            <Text style={{ color: colors.primary, fontWeight: "700" }}>Done</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" },
  headerCopy: { flex: 1, marginRight: 12 },
  telegramButton: { width: 38, height: 38, borderWidth: 1, borderRadius: 8, alignItems: "center", justifyContent: "center" },
  header: { fontSize: 20, fontWeight: "700", marginBottom: 12 },
  subtitle: { fontSize: 14, lineHeight: 20, marginTop: -7, marginBottom: 16 },
  collectionScroller: { flexGrow: 0, marginBottom: 8 },
  collectionRow: { gap: 8, paddingRight: 8 },
  collectionOption: { borderRadius: 8, borderWidth: 1, paddingHorizontal: 11, paddingVertical: 8 },
  messages: { flexGrow: 1, paddingVertical: 12 },
  bubble: { borderRadius: 8, padding: 12, marginBottom: 10, maxWidth: "88%" },
  actionRow: { borderTopWidth: StyleSheet.hairlineWidth, flexDirection: "row", gap: 8, marginTop: 10, paddingTop: 9 },
  emptyState: { flex: 1, justifyContent: "center", paddingHorizontal: 24 },
  emptyTitle: { fontSize: 18, fontWeight: "700", marginBottom: 6, textAlign: "center" },
  emptyBody: { fontSize: 14, lineHeight: 20, textAlign: "center" },
  thinkingRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 },
  error: { fontSize: 13, lineHeight: 18, marginBottom: 8 },
  composerRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  input: { flex: 1, minHeight: 48, borderRadius: 8, borderWidth: 1, paddingHorizontal: 14, fontSize: 15 },
  sendButton: { height: 48, borderRadius: 8, justifyContent: "center", paddingHorizontal: 16 },
  sendButtonText: { fontSize: 14, fontWeight: "700" },
  modalBackdrop: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: "rgba(0,0,0,0.5)" },
  modal: { borderRadius: 8, borderWidth: 1, padding: 20 },
  modalTitle: { fontSize: 20, fontWeight: "800", marginBottom: 6 },
  modalSubtitle: { fontSize: 13, lineHeight: 19, marginBottom: 16 },
  codeBox: { alignSelf: "flex-start", borderWidth: 1, borderRadius: 8, paddingHorizontal: 18, paddingVertical: 12, marginBottom: 16 },
  codeText: { fontSize: 28, fontWeight: "800", letterSpacing: 4 },
  modalStep: { fontSize: 14, lineHeight: 21 },
  modalNote: { fontSize: 12, marginTop: 10, marginBottom: 4 },
  modalClose: { minHeight: 44, borderWidth: 1, borderRadius: 8, alignItems: "center", justifyContent: "center", marginTop: 18 },
});
