import React from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import Animated, { FadeInDown } from "react-native-reanimated";
import { Ionicons } from "@expo/vector-icons";

import { useTheme } from "@/theme/ThemeContext";
import { themes } from "@/theme/themes";

export function ThemeSelectorScreen() {
  const { theme, setThemeId } = useTheme();
  const colors = theme.colors;

  return (
    <View style={styles.container}>
      <Text style={[styles.header, { color: colors.text }]}>Make it yours</Text>
      <Text style={[styles.subtitle, { color: colors.muted }]}>Your theme follows you across LexiShelf.</Text>

      <FlatList
        data={themes}
        keyExtractor={(item) => item.id}
        renderItem={({ item, index }) => {
          const selected = item.id === theme.id;
          return (
            <Animated.View entering={FadeInDown.delay(index * 40).duration(260)}>
              <Pressable
                onPress={() => setThemeId(item.id)}
                style={[
                  styles.row,
                  { backgroundColor: item.colors.background, borderColor: selected ? colors.primary : item.colors.border },
                ]}
              >
                <View style={[styles.preview, { backgroundColor: item.colors.surface, borderColor: item.colors.border }]}>
                  <View style={[styles.swatch, { backgroundColor: item.colors.primary }]} />
                  <View style={[styles.previewLine, { backgroundColor: item.colors.text }]} />
                  <View style={[styles.previewLine, styles.previewLineShort, { backgroundColor: item.colors.muted }]} />
                </View>
                <View style={styles.themeCopy}>
                  <Text style={[styles.name, { color: item.colors.text }]}>{item.name}</Text>
                  <Text style={[styles.themeMode, { color: item.colors.muted }]}>{item.isDark ? "Dark" : "Light"}</Text>
                </View>
                {selected ? (
                  <View style={[styles.selectedIcon, { backgroundColor: item.colors.primary }]}>
                    <Ionicons name="checkmark" size={16} color={item.colors.onPrimary} />
                  </View>
                ) : null}
              </Pressable>
            </Animated.View>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, paddingTop: 60 },
  header: { fontSize: 26, fontWeight: "800", letterSpacing: 0 },
  subtitle: { fontSize: 14, lineHeight: 20, marginTop: 3, marginBottom: 22 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 8,
    borderWidth: 2,
    padding: 12,
    marginBottom: 10,
  },
  name: { fontSize: 15, fontWeight: "600" },
  preview: { width: 62, height: 48, borderRadius: 6, borderWidth: 1, padding: 8, justifyContent: "center", marginRight: 12 },
  swatch: { width: 16, height: 6, borderRadius: 3, marginBottom: 6 },
  previewLine: { width: 34, height: 3, borderRadius: 2, marginBottom: 4 },
  previewLineShort: { width: 24, marginBottom: 0 },
  themeCopy: { flex: 1 },
  themeMode: { fontSize: 12, marginTop: 2 },
  selectedIcon: { width: 26, height: 26, borderRadius: 13, alignItems: "center", justifyContent: "center" },
});
