import "react-native-gesture-handler";
import React from "react";
import { StatusBar } from "expo-status-bar";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { RootNavigator } from "@/navigation/RootNavigator";
import { AuthProvider } from "@/auth/AuthContext";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ThemeProvider, useTheme } from "@/theme/ThemeContext";

function ThemedApplication() {
  const { theme } = useTheme();

  return (
    <ErrorBoundary>
      <AuthProvider>
        <StatusBar style={theme.isDark ? "light" : "dark"} backgroundColor={theme.colors.background} />
        <RootNavigator />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <ThemeProvider>
          <ThemedApplication />
        </ThemeProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
