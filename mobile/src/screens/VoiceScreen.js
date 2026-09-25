import React, { useEffect, useRef, useState } from 'react';
import { Platform, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { File } from 'expo-file-system';
import {
  createAudioPlayer,
  RecordingPresets,
  requestRecordingPermissionsAsync,
  setAudioModeAsync,
  useAudioRecorder,
  useAudioRecorderState,
} from 'expo-audio';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { speak, stopSpeech } from '../lib/speech';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS, LANGUAGES } from '../theme';
import { t } from '../i18n';

// Elderly users may forget to stop, so cap one answer and send it for them.
const MAX_RECORD_MS = 10000;
// Backend rejects decoded audio above 4 MB; stay under it.
const MAX_UPLOAD_BYTES = 3 * 1024 * 1024;

const MIME_BY_EXTENSION = {
  m4a: 'audio/m4a',
  mp4: 'audio/mp4',
  webm: 'audio/webm',
  wav: 'audio/wav',
  caf: 'audio/x-caf',
  '3gp': 'audio/3gpp',
};

export default function VoiceScreen() {
  const { currentPatient } = useAuth();
  const pid = currentPatient?.id || 1;
  const [language, setLanguage] = useState(currentPatient?.primary_language || 'en-IN');
  const [question, setQuestion] = useState('');
  const [reply, setReply] = useState(t(currentPatient?.primary_language || 'en-IN', 'readyToListen'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const playerRef = useRef(null);
  const autoStopRef = useRef(null);

  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const recorderState = useAudioRecorderState(recorder, 200);
  const recording = recorderState.isRecording;
  const seconds = Math.floor((recorderState.durationMillis || 0) / 1000);

  useEffect(() => () => {
    clearTimeout(autoStopRef.current);
    try { recorder.stop(); } catch {}
    try { playerRef.current?.remove(); } catch {}
    playerRef.current = null;
  }, [recorder]);

  function playBase64(b64) {
    try {
      try { playerRef.current?.remove(); } catch {}
      const player = createAudioPlayer({ uri: `data:audio/wav;base64,${b64}` });
      playerRef.current = player;
      player.play();
    } catch {}
  }

  async function call({ text, audioBase64, contentType }) {
    if (loading) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.voiceInteract({
        patient_id: pid,
        question_text: text || null,
        audio_base64: audioBase64 || null,
        audio_content_type: contentType || null,
        language_code: language,
      });
      setQuestion(res.transcription || text || '');
      setReply(res.reply_text || 'I am here with you.');
      if (res.audio_base64) playBase64(res.audio_base64);
      else speak(res.reply_text, language);
    } catch {
      setReply("I'm here with you. Please try asking again.");
    } finally {
      setLoading(false);
    }
  }

  async function sendRecording(uri) {
    if (!uri) {
      setError("I couldn't hear that clearly. Please try again, or type your question.");
      return;
    }
    try {
      const file = new File(uri);
      const size = file.size ?? 0;
      if (size > MAX_UPLOAD_BYTES) {
        setError('That was a little long. Please try a shorter sentence.');
        return;
      }
      const audioBase64 = await file.base64();
      if (!audioBase64) throw new Error('empty recording');
      const ext = (file.extension || '').replace('.', '').toLowerCase();
      const contentType = MIME_BY_EXTENSION[ext] || (Platform.OS === 'web' ? 'audio/webm' : 'audio/m4a');
      await call({ audioBase64, contentType });
    } catch {
      setError("I couldn't hear that clearly. Please try again, or type your question.");
    }
  }

  async function stopRecording() {
    clearTimeout(autoStopRef.current);
    autoStopRef.current = null;
    if (!recorderState.isRecording) return;
    try {
      await recorder.stop();
    } catch {}
    try {
      // Restore normal playback routing after the mic session.
      await setAudioModeAsync({ allowsRecording: false, playsInSilentMode: true });
    } catch {}
    await sendRecording(recorder.uri);
  }

  async function startRecording() {
    setError('');
    stopSpeech();
    try {
      const permission = await requestRecordingPermissionsAsync();
      if (!permission.granted) {
        setError('Microphone permission is needed to hear you. You can also type your question.');
        return;
      }
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
      await recorder.prepareToRecordAsync();
      recorder.record();
      speak('Listening. Please speak now.', language);
      autoStopRef.current = setTimeout(() => { stopRecording(); }, MAX_RECORD_MS);
    } catch {
      setError('The microphone is not available right now. You can type your question instead.');
    }
  }

  function toggleRecording() {
    if (recording) stopRecording();
    else startRecording();
  }

  return (
    <Screen>
      <SectionTitle eyebrow="Sarvam AI voice" title="🎙 Talk to MEMORA" sub="Press the big button and speak. Or type below." />
      <Card>
        <Text style={styles.label}>LANGUAGE</Text>
        <View style={styles.chips}>
          {LANGUAGES.map((l) => (
            <TouchableOpacity key={l.code} style={[styles.chip, language === l.code && styles.chipOn]} onPress={() => setLanguage(l.code)}>
              <Text style={[styles.chipText, language === l.code && { color: '#fff' }]}>{l.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity
          style={[styles.mic, recording && styles.micOn]}
          onPress={toggleRecording}
          disabled={loading}
          accessibilityRole="button"
          accessibilityLabel={recording ? 'Stop listening' : 'Start speaking'}
        >
          <Text style={styles.micIcon}>{recording ? '⏹' : '🎙'}</Text>
          <Text style={[styles.micText, recording && { color: '#fff' }]}>
            {recording ? `${t(language, 'listening')}… ${seconds}s` : loading ? t(language, 'thinking') : t(language, 'tapSpeak')}
          </Text>
        </TouchableOpacity>
        {recording ? <Text style={styles.hint}>Speak slowly and clearly. It stops on its own after 10 seconds.</Text> : null}
        {error ? <Text style={styles.error}>{error}</Text> : null}

        {question ? <View style={styles.asked}><Text style={styles.askedText}>You asked: “{question}”</Text></View> : null}
        <View style={styles.reply}>
          <Text style={styles.replyText}>{loading ? 'Thinking gently…' : reply}</Text>
        </View>
        <View style={{ flexDirection: 'row', gap: 10 }}>
          <View style={{ flex: 1 }}><BigButton title={`🔊 ${t(language, 'hearAgain')}`} variant="mint" onPress={() => speak(reply, language)} /></View>
          <View style={{ flex: 1 }}><BigButton title={`🔇 ${t(language, 'stop')}`} variant="outline" onPress={stopSpeech} /></View>
        </View>
      </Card>

      <Card>
        <Text style={styles.label}>{t(language, 'tryAsking').toUpperCase()}</Text>
        {['Who is my daughter?', 'What is my favourite food?', 'What is my next reminder?', 'What is my name?'].map((s) => (
          <TouchableOpacity key={s} style={styles.suggest} onPress={() => call({ text: s })}>
            <Text style={styles.suggestText}>{s}</Text>
          </TouchableOpacity>
        ))}
        <View style={styles.row}>
          <TextInput style={[styles.input, { flex: 1 }]} value={question} onChangeText={setQuestion} placeholder={t(language, 'typePlaceholder')} onSubmitEditing={() => call({ text: question })} returnKeyType="send" />
          <TouchableOpacity style={styles.send} onPress={() => call({ text: question })}>
            <Text style={styles.sendText}>Ask →</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.note}>{t(language, 'voiceNote')}</Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  label: { fontSize: 13, fontWeight: '800', color: COLORS.text, marginBottom: 8 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 12 },
  chip: { paddingHorizontal: 16, paddingVertical: 12, borderRadius: 999, backgroundColor: '#eef0fc', minHeight: 52, justifyContent: 'center' },
  chipOn: { backgroundColor: COLORS.indigo },
  chipText: { fontSize: 16, fontWeight: '800', color: COLORS.indigo },
  mic: {
    backgroundColor: '#f5f2ea', borderWidth: 2, borderColor: COLORS.indigo, borderRadius: 22,
    minHeight: 96, alignItems: 'center', justifyContent: 'center', gap: 4, marginTop: 4,
  },
  micOn: { backgroundColor: COLORS.indigo },
  micIcon: { fontSize: 34 },
  micText: { fontSize: 19, fontWeight: '800', color: COLORS.text },
  hint: { fontSize: 15, color: COLORS.muted, marginTop: 8, lineHeight: 22 },
  error: { fontSize: 16, color: COLORS.danger, fontWeight: '700', marginTop: 10, lineHeight: 23 },
  asked: { backgroundColor: '#f5f3ff', borderWidth: 1, borderColor: '#e0e7ff', borderRadius: 16, padding: 14, marginTop: 14, marginBottom: 10 },
  askedText: { fontSize: 17, color: COLORS.indigo, fontWeight: '600' },
  reply: { backgroundColor: COLORS.mint, borderWidth: 1, borderColor: '#c1e2d9', borderRadius: 16, padding: 18, minHeight: 110, justifyContent: 'center', marginBottom: 12 },
  replyText: { fontSize: 20, color: '#1c473f', fontWeight: '600', lineHeight: 28 },
  suggest: { backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#e8e2d5', borderRadius: 16, padding: 16, marginTop: 8, minHeight: 60, justifyContent: 'center' },
  suggestText: { fontSize: 18, fontWeight: '600', color: COLORS.text },
  row: { flexDirection: 'row', gap: 10, marginTop: 12 },
  input: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#dcd6cc', borderRadius: 14, padding: 16, fontSize: 18, minHeight: 60 },
  send: { backgroundColor: COLORS.indigo, borderRadius: 14, paddingHorizontal: 20, alignItems: 'center', justifyContent: 'center', minHeight: 60 },
  sendText: { color: '#fff', fontSize: 18, fontWeight: '800' },
  note: { fontSize: 15, color: COLORS.muted, marginTop: 10, lineHeight: 22 },
});
