import React, { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { createAudioPlayer } from 'expo-audio';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { speak, stopSpeech } from '../lib/speech';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS, LANGUAGES } from '../theme';

export default function VoiceScreen() {
  const { currentPatient } = useAuth();
  const pid = currentPatient?.id || 1;
  const [language, setLanguage] = useState(currentPatient?.primary_language || 'ta-IN');
  const [question, setQuestion] = useState('');
  const [reply, setReply] = useState('MEMORA is ready to listen. Ask about family, reminders, or foods.');
  const [loading, setLoading] = useState(false);
  const playerRef = useRef(null);

  useEffect(() => () => {
    try { playerRef.current?.remove(); } catch {}
    playerRef.current = null;
  }, []);

  function playBase64(b64) {
    try {
      try { playerRef.current?.remove(); } catch {}
      const player = createAudioPlayer({ uri: `data:audio/wav;base64,${b64}` });
      playerRef.current = player;
      player.play();
    } catch {}
  }

  async function ask(text) {
    const q = (text || '').trim();
    if (!q || loading) return;
    setLoading(true);
    setQuestion(q);
    try {
      const res = await api.voiceInteract({ patient_id: pid, question_text: q, language_code: language });
      setReply(res.reply_text || 'I am here with you.');
      if (res.audio_base64) playBase64(res.audio_base64);
      else speak(res.reply_text, language);
    } catch {
      setReply("I'm here with you. Please try asking again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <SectionTitle eyebrow="Sarvam AI voice" title="🎙 Talk to MEMORA" sub="Tap a suggestion, or type like speaking." />
      <Card>
        <Text style={styles.label}>LANGUAGE</Text>
        <View style={styles.chips}>
          {LANGUAGES.map((l) => (
            <TouchableOpacity key={l.code} style={[styles.chip, language === l.code && styles.chipOn]} onPress={() => setLanguage(l.code)}>
              <Text style={[styles.chipText, language === l.code && { color: '#fff' }]}>{l.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {question ? <View style={styles.asked}><Text style={styles.askedText}>You asked: “{question}”</Text></View> : null}
        <View style={styles.reply}>
          <Text style={styles.replyText}>{loading ? 'Thinking gently…' : reply}</Text>
        </View>
        <View style={{ flexDirection: 'row', gap: 10 }}>
          <View style={{ flex: 1 }}><BigButton title="🔊 Hear again" variant="mint" onPress={() => speak(reply, language)} /></View>
          <View style={{ flex: 1 }}><BigButton title="🔇 Stop" variant="outline" onPress={stopSpeech} /></View>
        </View>
      </Card>

      <Card>
        <Text style={styles.label}>TRY ASKING</Text>
        {['Who is my daughter?', 'What is my favourite food?', 'What is my next reminder?', 'What is my name?'].map((s) => (
          <TouchableOpacity key={s} style={styles.suggest} onPress={() => ask(s)}>
            <Text style={styles.suggestText}>{s}</Text>
          </TouchableOpacity>
        ))}
        <View style={styles.row}>
          <TextInput style={[styles.input, { flex: 1 }]} value={question} onChangeText={setQuestion} placeholder="Type: Who is my daughter?" onSubmitEditing={() => ask(question)} returnKeyType="send" />
          <TouchableOpacity style={styles.send} onPress={() => ask(question)}>
            <Text style={styles.sendText}>Ask →</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.note}>Microphone recording uses your typed question on mobile — Sarvam AI still answers aloud.</Text>
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
  asked: { backgroundColor: '#f5f3ff', borderWidth: 1, borderColor: '#e0e7ff', borderRadius: 16, padding: 14, marginBottom: 10 },
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
