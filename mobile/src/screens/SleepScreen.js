import React, { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Slider from '@react-native-community/slider';
import { createAudioPlayer } from 'expo-audio';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS } from '../theme';

export default function SleepScreen() {
  const [score, setScore] = useState(82);
  const [playing, setPlaying] = useState(false);
  const [msg, setMsg] = useState('Ready for a peaceful evening.');
  const playerRef = useRef(null);
  const timerRef = useRef(null);

  useEffect(() => () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    try { playerRef.current?.remove(); } catch {}
    playerRef.current = null;
  }, []);

  async function playTone() {
    if (playing) return;
    setPlaying(true);
    setMsg('🌙 Soft soothing tone playing…');
    try {
      const player = createAudioPlayer({ uri: 'https://actions.google.com/sounds/v1/ambiences/loop_soft_wind.ogg' });
      playerRef.current = player;
      player.volume = 0.25;
      player.play();
      timerRef.current = setTimeout(() => {
        try { playerRef.current?.remove(); } catch {}
        playerRef.current = null;
        setPlaying(false);
        setMsg('Tone ended. Rest peacefully. 🌙');
      }, 8000);
    } catch {
      setPlaying(false);
      setMsg('Audio unavailable offline. Breathe slowly instead.');
    }
  }

  return (
    <Screen>
      <SectionTitle title="Deep Sleep Support" sub="Calm evening wind-down for restful sleep." />
      <Card style={{ alignItems: 'center' }}>
        <Text style={styles.eyebrow}>Sleep score</Text>
        <View style={[styles.ring, { borderColor: COLORS.indigo }]}>
          <Text style={styles.score}>{Math.round(score)}%</Text>
          <Text style={styles.restful}>restful</Text>
        </View>
        <Slider
          style={{ width: '85%', height: 60 }}
          minimumValue={0}
          maximumValue={100}
          value={score}
          onValueChange={setScore}
          minimumTrackTintColor={COLORS.indigo}
          maximumTrackTintColor="#e9e5dc"
        />
        <Text style={styles.note}>Move the slider each morning to track rest.</Text>
      </Card>
      <Card>
        <Text style={styles.calmTitle}>🌙 Evening calm mode</Text>
        <Text style={styles.note}>A soft ambient sound to soothe the mind before sleep.</Text>
        <View style={{ height: 12 }} />
        <BigButton title={playing ? 'Playing gentle sound…' : 'Play calming wind-down sound'} onPress={playTone} disabled={playing} />
        <View style={styles.msg}><Text style={styles.msgText}>{msg}</Text></View>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  eyebrow: { fontSize: 12, letterSpacing: 2, color: COLORS.muted, fontWeight: '700', textTransform: 'uppercase' },
  ring: { width: 200, height: 200, borderRadius: 100, borderWidth: 18, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center', marginVertical: 16 },
  score: { fontSize: 46, fontWeight: '800', color: COLORS.indigo },
  restful: { fontSize: 15, color: COLORS.muted },
  note: { fontSize: 16, color: COLORS.muted, lineHeight: 23, textAlign: 'center' },
  calmTitle: { fontSize: 22, fontWeight: '800', color: COLORS.text },
  msg: { backgroundColor: '#e7f4f0', borderWidth: 1, borderColor: '#d2e8e0', borderRadius: 16, padding: 14, marginTop: 12 },
  msgText: { fontSize: 16, color: '#205147', fontWeight: '600' },
});
