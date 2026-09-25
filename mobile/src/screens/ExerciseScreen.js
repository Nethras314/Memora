import React, { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { speak, stopSpeech } from '../lib/speech';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS } from '../theme';

const PHASES = [
  { text: 'Breathe in slowly…', hint: 'Fill your chest gently' },
  { text: 'Hold gently…', hint: 'Keep calm and relaxed' },
  { text: 'Breathe out slowly…', hint: 'Release all tension' },
  { text: 'Rest comfortably…', hint: 'Peace and stillness' },
];

export default function ExerciseScreen() {
  const [active, setActive] = useState(false);
  const [phase, setPhase] = useState(0);
  const timer = useRef(null);

  useEffect(() => {
    if (active) {
      speak(PHASES[phase].text);
      timer.current = setInterval(() => {
        setPhase((p) => {
          const n = (p + 1) % 4;
          speak(PHASES[n].text);
          return n;
        });
      }, 4000);
    } else {
      stopSpeech();
      if (timer.current) clearInterval(timer.current);
    }
    return () => { if (timer.current) clearInterval(timer.current); };
  }, [active]);

  useEffect(() => () => stopSpeech(), []);
  const expanded = active && (phase === 0 || phase === 1);

  return (
    <Screen>
      <SectionTitle title="Gentle Movement & Breathing" sub="Slow rhythm. Stop if you feel dizzy." />
      <Card style={{ alignItems: 'center' }}>
        <Text style={styles.eyebrow}>Breathing circle</Text>
        <View style={[styles.circle, expanded && styles.circleBig]}>
          <Text style={{ fontSize: 64 }}>🌿</Text>
        </View>
        <Text style={styles.phase}>{PHASES[phase].text}</Text>
        <Text style={styles.hint}>{PHASES[phase].hint}</Text>
        <View style={{ height: 14 }} />
        <BigButton title={active ? '⏸ Pause breathing' : '▶ Start calm breathing'} onPress={() => setActive(!active)} />
      </Card>
      <Card>
        <SectionTitle eyebrow="Daily gentle movement" title="Movement ideas" />
        {[['🧘 Shoulder rolls & neck tilt', '1 min'], ['🚶 Slow courtyard walk', '5 mins'], ['🙆 Seated arm stretch', '2 mins']].map(([t, d]) => (
          <View key={t} style={styles.moveRow}>
            <Text style={styles.moveText}>{t}</Text>
            <Text style={styles.moveTime}>{d}</Text>
          </View>
        ))}
        <View style={styles.safety}>
          <Text style={styles.safetyText}><Text style={{ fontWeight: '800' }}>Gentle safety notice: </Text>movements should stay light and comfortable. Stop if there is dizziness or pain.</Text>
        </View>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  eyebrow: { fontSize: 12, letterSpacing: 2, color: COLORS.muted, fontWeight: '700', textTransform: 'uppercase' },
  circle: { width: 210, height: 210, borderRadius: 105, backgroundColor: COLORS.mint, borderWidth: 4, borderColor: '#bedcd4', alignItems: 'center', justifyContent: 'center', marginVertical: 18, transform: [{ scale: 0.92 }] },
  circleBig: { transform: [{ scale: 1.08 }] },
  phase: { fontSize: 24, fontWeight: '800', color: COLORS.text, textAlign: 'center' },
  hint: { fontSize: 17, color: COLORS.muted, marginTop: 4 },
  moveRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#e8e2d5', borderRadius: 16, padding: 16, marginTop: 10 },
  moveText: { fontSize: 18, fontWeight: '700', color: COLORS.text, flex: 1 },
  moveTime: { fontSize: 15, color: COLORS.muted, backgroundColor: '#fff', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 10, fontWeight: '700' },
  safety: { backgroundColor: '#e7f2ee', borderWidth: 1, borderColor: '#d3e6df', borderRadius: 16, padding: 16, marginTop: 12 },
  safetyText: { fontSize: 16, color: '#205147', lineHeight: 24 },
});
