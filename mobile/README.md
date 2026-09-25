# MEMORA Mobile (Expo) — Dementia Patient App

Patient-facing companion to the MEMORA web app. Same FastAPI + Supabase backend, rebuilt with large touch targets, voice-first flow, and gentle pacing for dementia patients.

## Screens (mirrors web patient features)

| Mobile tab | Web equivalent |
|---|---|
| Today | `TodayDashboard.jsx` — greeting, progress %, quick actions, reminders preview |
| Talk (modal) | `VoiceAssistantModal.jsx` — Sarvam AI Q&A, 4 languages, audio playback, typed fallback |
| Memories (PIN) | `MemoriesPage.jsx` + `PinModal.jsx` — photo cards, listen-aloud, add/edit/delete, camera + gallery |
| Routine | `RoutinePage.jsx` — tap-to-complete steps, add step, reset today |
| Reminds | `RemindersPage.jsx` — add/edit/enable/delete + local push notification scheduling |
| Games | `ActivitiesPage.jsx` — DDA sequence game (`next-game`/`log-session`), GK, odd-one-out |
| Calm | `ExercisePage.jsx` + `SleepPage.jsx` — guided breathing with voice, movement ideas, sleep tracker + calm sound |
| Progress | `CaregiverDashboard.jsx` (patient view) — routine %, stability score, trend, suggestion |

Admin / caregiver management stays on web.

## Dementia-friendly rules applied

- Min 60–68px touch targets, 18–22px body text, one task per screen
- Positive, failure-free language ("Good try! Practice makes us stronger.")
- Voice read-aloud on games, memories, reminders, breathing (`expo-speech` 0.85x)
- PIN gate on Memories, same server-side `POST /auth/verify-pin`
- High-contrast MEMORA palette (`#4943a5` / `#faf8f2`), no tiny icons alone

## Setup

```bash
cd mobile
npm install
cp .env.example .env
# Edit .env: EXPO_PUBLIC_API_URL=http://<YOUR-PC-LAN-IP>:8000/api
npx expo start
```

- Backend must listen on LAN: `py -m uvicorn app.main:app --host 0.0.0.0 --port 8000` from `backend/`
- Phone + PC on same Wi-Fi; scan QR with Expo Go
- Same login as web (Supabase or demo fallback); token stored in `expo-secure-store`

## Notes

- Built on **Expo SDK 57** (React 19.2.3, React Native 0.86.3) — matches the current Expo Go.
- Voice screen sends typed questions to `POST /voice/interact` and plays Sarvam `audio_base64` via `expo-audio`
- Reminder scheduling uses `expo-notifications` with a repeating DAILY trigger
- `babel-preset-expo` is pinned in devDependencies — Metro resolves Babel presets from the project root, and npm otherwise nests it under `expo/node_modules`, which breaks the transformer
- Photos use `expo-image-picker` with `mediaTypes: ['images']`

