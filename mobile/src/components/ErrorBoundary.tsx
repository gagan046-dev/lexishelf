import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useThemeColors } from "@/theme/ThemeContext";

type Props = { children: React.ReactNode };
type State = { error: Error | null };

class ErrorBoundaryBase extends React.Component<Props & { colors: ReturnType<typeof useThemeColors> }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Surface unexpected render crashes without leaking their detail beyond the local console.
    console.error("Unhandled UI error", error, info.componentStack);
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    const colors = this.props.colors;
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Text style={[styles.title, { color: colors.text }]}>Something went wrong</Text>
        <Text style={[styles.message, { color: colors.muted }]}>
          LexiShelf hit an unexpected error. Your saved words and collections are safe.
        </Text>
        <Pressable
          onPress={() => this.setState({ error: null })}
          style={[styles.button, { backgroundColor: colors.primary }]}
        >
          <Text style={{ color: colors.onPrimary, fontWeight: "700" }}>Try again</Text>
        </Pressable>
      </View>
    );
  }
}

export function ErrorBoundary({ children }: Props) {
  const colors = useThemeColors();
  return <ErrorBoundaryBase colors={colors}>{children}</ErrorBoundaryBase>;
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  title: { fontSize: 20, fontWeight: "800", marginBottom: 8 },
  message: { fontSize: 14, lineHeight: 20, textAlign: "center", marginBottom: 20, maxWidth: 320 },
  button: { minHeight: 46, borderRadius: 8, paddingHorizontal: 20, alignItems: "center", justifyContent: "center" },
});
