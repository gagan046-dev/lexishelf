import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import Animated, { useSharedValue, withTiming } from "react-native-reanimated";
import { StyleSheet } from "react-native";

import { Theme, defaultTheme, getThemeById } from "./themes";

const STORAGE_KEY = "lexishelf.theme_id";

type ThemeContextValue = {
  theme: Theme;
  setThemeId: (id: string) => void;
};

const ThemeContext = createContext<ThemeContextValue>({
  theme: defaultTheme,
  setThemeId: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(defaultTheme);
  const [previousTheme, setPreviousTheme] = useState<Theme>(defaultTheme);
  const fade = useSharedValue(1);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((storedId) => {
      if (storedId) setTheme(getThemeById(storedId));
    });
  }, []);

  const setThemeId = (id: string) => {
    setPreviousTheme(theme);
    const nextTheme = getThemeById(id);
    fade.value = 0;
    setTheme(nextTheme);
    fade.value = withTiming(1, { duration: 350 });
    AsyncStorage.setItem(STORAGE_KEY, id).catch(() => {});
  };

  const value = useMemo(() => ({ theme, setThemeId }), [theme]);

  return (
    <ThemeContext.Provider value={value}>
      {/* Crossfades the previous theme's background out while the new one fades in. */}
      <Animated.View style={[StyleSheet.absoluteFill, { backgroundColor: previousTheme.colors.background }]} />
      <Animated.View
        style={[StyleSheet.absoluteFill, { backgroundColor: theme.colors.background, opacity: fade }]}
      />
      <Animated.View style={{ flex: 1 }}>{children}</Animated.View>
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}

export function useThemeColors() {
  return useTheme().theme.colors;
}
