import { Platform } from 'react-native';
// Import submodules directly instead of the package root: the root re-exports the
// push-token modules (TokenEmitter / DevicePushTokenAutoRegistration.fx), which throw
// in Expo Go on Android because remote push was removed from Expo Go in SDK 53.
// Local scheduled notifications still work in Expo Go.
import { setNotificationHandler } from 'expo-notifications/build/NotificationsHandler';
import { requestPermissionsAsync } from 'expo-notifications/build/NotificationPermissions';
import { scheduleNotificationAsync } from 'expo-notifications/build/scheduleNotificationAsync';
import { setNotificationChannelAsync } from 'expo-notifications/build/setNotificationChannelAsync';
import { SchedulableTriggerInputTypes } from 'expo-notifications/build/Notifications.types';

// AndroidImportance.HIGH — the enum is type-only, so its numeric value is used here.
const ANDROID_IMPORTANCE_HIGH = 6;

// Never let notification setup break app boot: the handler only affects how alerts
// look while the app is in the foreground, so a failure here is non-fatal.
try {
  setNotificationHandler({
    handleNotification: async () => ({
      shouldShowBanner: true,
      shouldShowList: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
    }),
  });
} catch {
  // Notifications unavailable in this runtime; reminders still work in-app.
}

export async function ensureNotificationPermission() {
  const { status } = await requestPermissionsAsync();
  return status === 'granted';
}

export async function scheduleReminderNotification(title, timeHHMM) {
  try {
    const ok = await ensureNotificationPermission();
    if (!ok) return null;

    const [h, m] = String(timeHHMM || '09:00').split(':').map(Number);
    const hour = Number.isFinite(h) ? h : 9;
    const minute = Number.isFinite(m) ? m : 0;

    if (Platform.OS === 'android') {
      await setNotificationChannelAsync('memora', {
        name: 'MEMORA gentle prompts',
        importance: ANDROID_IMPORTANCE_HIGH,
      });
    }

    return await scheduleNotificationAsync({
      content: { title: 'MEMORA gently reminds you', body: String(title) },
      trigger: {
        type: SchedulableTriggerInputTypes.DAILY,
        hour,
        minute,
        channelId: 'memora',
      },
    });
  } catch {
    return null;
  }
}
