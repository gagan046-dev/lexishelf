import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: false,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

const REVIEW_REMINDER_ID = "lexishelf-review-reminder";

async function ensurePermission(): Promise<boolean> {
  const current = await Notifications.getPermissionsAsync();
  if (current.granted) return true;
  const requested = await Notifications.requestPermissionsAsync();
  return requested.granted;
}

/** Keeps a single daily 9am local reminder in sync with the current due-for-review count. */
export async function syncReviewReminder(dueCount: number): Promise<void> {
  if (Platform.OS === "web") return;

  await Notifications.cancelScheduledNotificationAsync(REVIEW_REMINDER_ID).catch(() => undefined);
  if (dueCount <= 0) return;

  const granted = await ensurePermission();
  if (!granted) return;

  await Notifications.scheduleNotificationAsync({
    identifier: REVIEW_REMINDER_ID,
    content: {
      title: "Words are waiting for review",
      body: `You have ${dueCount} word${dueCount === 1 ? "" : "s"} due. A quick review keeps them memorized.`,
    },
    trigger: {
      hour: 9,
      minute: 0,
      repeats: true,
    },
  });
}
