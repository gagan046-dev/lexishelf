import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

// expo-secure-store uses Keychain (iOS) / Keystore-backed EncryptedSharedPreferences (Android),
// keeping the auth JWT off plain-text disk. It has no web implementation, so web keeps AsyncStorage.
const useSecureStore = Platform.OS !== "web";

export const secureSession = {
  getItem: (key: string) => (useSecureStore ? SecureStore.getItemAsync(key) : AsyncStorage.getItem(key)),
  setItem: (key: string, value: string) =>
    useSecureStore ? SecureStore.setItemAsync(key, value) : AsyncStorage.setItem(key, value),
  removeItem: (key: string) =>
    useSecureStore ? SecureStore.deleteItemAsync(key) : AsyncStorage.removeItem(key),
};
