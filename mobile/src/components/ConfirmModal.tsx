import React from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";
import Animated, { FadeIn, ZoomIn } from "react-native-reanimated";

import { useThemeColors } from "@/theme/ThemeContext";

type Props = {
  visible: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

/** Reusable confirmation dialog used for destructive actions (deleting a word or a collection). */
export function ConfirmModal({
  visible,
  title,
  message,
  confirmLabel = "Delete",
  destructive = true,
  onConfirm,
  onCancel,
}: Props) {
  const colors = useThemeColors();

  if (!visible) return null;

  return (
    <Modal transparent animationType="none" visible={visible} onRequestClose={onCancel}>
      <Animated.View entering={FadeIn.duration(200)} style={styles.backdrop}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onCancel} />
        <Animated.View
          entering={ZoomIn.duration(220)}
          style={[styles.card, { backgroundColor: colors.surfaceElevated, borderColor: colors.border }]}
        >
          <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
          <Text style={[styles.message, { color: colors.muted }]}>{message}</Text>

          <View style={styles.actions}>
            <Pressable style={[styles.button, { borderColor: colors.border }]} onPress={onCancel}>
              <Text style={[styles.buttonText, { color: colors.text }]}>Cancel</Text>
            </Pressable>
            <Pressable
              style={[
                styles.button,
                styles.primaryButton,
                { backgroundColor: destructive ? colors.danger : colors.primary },
              ]}
              onPress={onConfirm}
            >
              <Text style={[styles.buttonText, { color: destructive ? "#FFFFFF" : colors.onPrimary }]}>{confirmLabel}</Text>
            </Pressable>
          </View>
        </Animated.View>
      </Animated.View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  card: {
    width: "100%",
    maxWidth: 360,
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
  },
  title: { fontSize: 18, fontWeight: "700", marginBottom: 8 },
  message: { fontSize: 14, lineHeight: 20, marginBottom: 20 },
  actions: { flexDirection: "row", justifyContent: "flex-end", gap: 12 },
  button: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "transparent",
  },
  primaryButton: { borderWidth: 0 },
  buttonText: { fontSize: 14, fontWeight: "600" },
});
