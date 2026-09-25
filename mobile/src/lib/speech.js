import * as Speech from 'expo-speech';

export function speak(text, language = 'en-IN') {
  try {
    Speech.stop();
    Speech.speak(String(text || ''), { language, rate: 0.85 });
  } catch {}
}

export function stopSpeech() {
  try {
    Speech.stop();
  } catch {}
}
