import React from "react";
import { DarkTheme, DefaultTheme, NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { Ionicons } from "@expo/vector-icons";

import { useAuth } from "@/auth/AuthContext";
import { AgentChatScreen } from "@/screens/AgentChatScreen";
import { AuthScreen } from "@/screens/AuthScreen";
import { CollectionDetailScreen } from "@/screens/CollectionDetailScreen";
import { CollectionsScreen } from "@/screens/CollectionsScreen";
import { HomeScreen } from "@/screens/HomeScreen";
import { ReviewScreen } from "@/screens/ReviewScreen";
import { SearchScreen } from "@/screens/SearchScreen";
import { ThemeSelectorScreen } from "@/screens/ThemeSelectorScreen";
import { useTheme } from "@/theme/ThemeContext";

export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  CollectionDetail: { collectionId: string };
};

export type MainTabParamList = {
  Home: undefined;
  Search: { query?: string } | undefined;
  Collections: undefined;
  Review: undefined;
  AgentChat: undefined;
  ThemeSelector: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

const tabIcons: Record<keyof MainTabParamList, keyof typeof Ionicons.glyphMap> = {
  Home: "home-outline",
  Search: "search-outline",
  Collections: "library-outline",
  Review: "school-outline",
  AgentChat: "sparkles-outline",
  ThemeSelector: "color-palette-outline",
};

function MainTabs() {
  const { theme } = useTheme();
  const colors = theme.colors;

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.muted,
        tabBarHideOnKeyboard: true,
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600", letterSpacing: 0 },
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          height: 66,
          paddingBottom: 8,
          paddingTop: 7,
        },
        tabBarIcon: ({ color, size }) => (
          <Ionicons name={tabIcons[route.name]} color={color} size={size} />
        ),
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Search" component={SearchScreen} />
      <Tab.Screen name="Collections" component={CollectionsScreen} />
      <Tab.Screen name="Review" component={ReviewScreen} />
      <Tab.Screen name="AgentChat" component={AgentChatScreen} options={{ title: "Chat" }} />
      <Tab.Screen name="ThemeSelector" component={ThemeSelectorScreen} options={{ title: "Theme" }} />
    </Tab.Navigator>
  );
}

export function RootNavigator() {
  const { user, isRestoring } = useAuth();
  const { theme } = useTheme();
  const colors = theme.colors;

  if (isRestoring) return null;

  return (
    <NavigationContainer
      theme={{
        ...(theme.isDark ? DarkTheme : DefaultTheme),
        colors: {
          ...(theme.isDark ? DarkTheme.colors : DefaultTheme.colors),
          primary: colors.primary,
          background: colors.background,
          card: colors.surface,
          text: colors.text,
          border: colors.border,
          notification: colors.danger,
        },
      }}
    >
      <Stack.Navigator screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.background } }}>
        {user ? (
          <>
            <Stack.Screen name="Main" component={MainTabs} />
            <Stack.Screen name="CollectionDetail" component={CollectionDetailScreen} />
          </>
        ) : (
          <Stack.Screen name="Auth" component={AuthScreen} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
