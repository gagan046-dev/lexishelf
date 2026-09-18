import * as Speech from "expo-speech";
import { Platform } from "react-native";

// expo-speech drives native TTS (iOS/Android); it has no web backend, so web keeps the browser's own engine.
export function speakText(text: string) {
  if (!text) return;

  if (Platform.OS === "web") {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 0.82;
    window.speechSynthesis.speak(utterance);
    return;
  }

  Speech.stop();
  Speech.speak(text, { language: "en-US", rate: 0.82 });
}
