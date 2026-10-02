import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Image, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { speak } from '../lib/speech';
import { BigButton, Card } from '../components/ui';
import { COLORS } from '../theme';
import { t } from '../i18n';

export default function PhotoGame() {
  const { currentPatient } = useAuth();
  const pid = currentPatient?.id || 1;
  const lang = currentPatient?.primary_language || 'en-IN';

  const [round, setRound] = useState(null);
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const startRef = useRef(0);

  const loadRound = useCallback(async () => {
    setLoading(true);
    setMsg('');
    try {
      setRound(await api.getNextPhotoGame(pid, lang));
    } catch {
      setRound(null);
    } finally {
      setLoading(false);
    }
  }, [pid, lang]);

  useEffect(() => {
    loadRound();
  }, [loadRound]);

  useEffect(() => {
    if (!round) return;
    startRef.current = Date.now();
    speak(t(lang, 'whoIsThis'), lang);
  }, [round, lang]);

  function hearAgain() {
    if (!round) return;
    speak(`${t(lang, 'whoIsThis')} ${round.options.join(', ')}`, lang);
  }

  function choose(option) {
    if (!round) return;
    speak(option, lang);
    const ok = option === round.correct_title;
    setMsg(ok ? t(lang, 'wonderfulPerfect') : t(lang, 'lovelyEffort'));
    if (ok) speak(t(lang, 'exactlyRight'), lang);
    const reaction = Math.max(100, Date.now() - startRef.current);
    try {
      api.logCognitiveSession({
        patient_id: pid,
        game_type: 'photo_recognition',
        difficulty_level: 1,
        score: ok ? 100 : 50,
        accuracy: ok ? 1.0 : 0.0,
        reaction_time_ms: reaction,
        mistake_count: ok ? 0 : 1,
      });
    } catch {}
  }

  return (
    <Card>
      <Text style={styles.eyebrow}>{t(lang, 'visualFocus')}</Text>
      <Text style={styles.gameTitle}>🖼️ {t(lang, 'photoGameTitle')}</Text>
      <Text style={styles.sub}>{t(lang, 'photoGameSub')}</Text>

      {loading ? <Text style={styles.muted}>{t(lang, 'loadingQuestion')}</Text> : null}

      {!loading && !round ? (
        <View style={{ alignItems: 'center', gap: 12, marginTop: 12 }}>
          <Text style={styles.muted}>{t(lang, 'tryOnceMore')}</Text>
          <BigButton title={t(lang, 'newQuestion')} variant="mint" onPress={loadRound} />
        </View>
      ) : null}

      {!loading && round ? (
        <View style={{ alignItems: 'center', gap: 14, marginTop: 14 }}>
          {round.photo_url ? (
            <Image source={{ uri: round.photo_url }} style={styles.photo} resizeMode="cover" />
          ) : null}
          <Text style={styles.q}>{t(lang, 'whoIsThis')}</Text>
          <View style={styles.optRow}>
            {(round.options || []).map((o, i) => (
              <TouchableOpacity key={i} style={styles.opt} onPress={() => choose(o)}>
                <Text style={styles.optText}>{o}</Text>
              </TouchableOpacity>
            ))}
          </View>
          {msg ? <Text style={styles.feedback}>{msg}</Text> : null}
          <View style={{ flexDirection: 'row', gap: 10, alignSelf: 'stretch' }}>
            <View style={{ flex: 1 }}><BigButton title={`🔊 ${t(lang, 'hearAgain')}`} variant="mint" onPress={hearAgain} /></View>
            <View style={{ flex: 1 }}><BigButton title={t(lang, 'newPuzzle')} variant="gold" onPress={loadRound} /></View>
          </View>
        </View>
      ) : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  eyebrow: { fontSize: 12, letterSpacing: 2, color: COLORS.muted, fontWeight: '700', textTransform: 'uppercase' },
  gameTitle: { fontSize: 22, fontWeight: '800', color: COLORS.text, marginTop: 2 },
  sub: { fontSize: 16, color: COLORS.muted, marginTop: 4, lineHeight: 23 },
  muted: { fontSize: 17, color: COLORS.muted, lineHeight: 24 },
  photo: { width: '100%', height: 220, borderRadius: 18, backgroundColor: '#eeece7' },
  q: { fontSize: 21, fontWeight: '800', color: COLORS.text, textAlign: 'center' },
  optRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, justifyContent: 'center' },
  opt: { minWidth: 120, minHeight: 64, paddingHorizontal: 20, borderRadius: 16, backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#e8e2d5', alignItems: 'center', justifyContent: 'center' },
  optText: { fontSize: 20, fontWeight: '800', color: COLORS.text },
  feedback: { fontSize: 17, fontWeight: '700', color: '#047857', backgroundColor: '#ecfdf5', padding: 14, borderRadius: 14, textAlign: 'center', alignSelf: 'stretch' },
});
