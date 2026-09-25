import React, { useCallback, useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS } from '../theme';

export default function ProgressScreen() {
  const { currentPatient } = useAuth();
  const pid = currentPatient?.id || 1;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try { setData(await api.getProgress(pid)); } catch {}
    finally { setLoading(false); }
  }, [pid]);

  useEffect(() => { load(); }, [load]);

  return (
    <Screen>
      <SectionTitle title="My Progress" sub="Gentle summary for you and family." />
      <Card>
        {loading ? <Text style={styles.muted}>Loading progress…</Text> : null}
        {!loading && !data ? (
          <View style={{ gap: 10 }}>
            <Text style={styles.muted}>Progress is unavailable right now.</Text>
            <BigButton title="Try again" onPress={load} />
          </View>
        ) : null}
        {data ? (
          <View style={{ gap: 12 }}>
            <View style={styles.hero}>
              <Text style={styles.big}>{data.routine_completion_pct}%</Text>
              <Text style={styles.heroSub}>routine complete • {data.completed_tasks}/{data.total_tasks} steps</Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>🧠 Cognitive stability</Text>
              <Text style={styles.value}>{data.cognitive_stability_score} / 100</Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>🎮 Game sessions</Text>
              <Text style={styles.value}>{data.recent_sessions_count}</Text>
            </View>
            <View style={styles.focus}>
              <Text style={styles.focusTitle}>💡 Gentle suggestion</Text>
              <Text style={styles.focusText}>{data.recommended_focus}</Text>
            </View>
            <Text style={styles.eyebrow}>Recent sessions</Text>
            {(data.cognitive_trend || []).map((s, i) => (
              <View key={i} style={styles.trend}>
                <Text style={styles.trendText}>{s.date}</Text>
                <Text style={styles.trendText}>Score {s.score}</Text>
                <Text style={styles.trendText}>Level {s.level}</Text>
              </View>
            ))}
            <BigButton title="🔄 Refresh" variant="outline" onPress={load} />
          </View>
        ) : null}
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  muted: { fontSize: 17, color: COLORS.muted },
  hero: { backgroundColor: COLORS.indigo, borderRadius: 20, padding: 20, alignItems: 'center' },
  big: { fontSize: 52, fontWeight: '800', color: '#fff' },
  heroSub: { color: '#ddd9ff', fontSize: 16, marginTop: 4 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#e8e2d5', borderRadius: 16, padding: 16 },
  label: { fontSize: 18, fontWeight: '700', color: COLORS.text },
  value: { fontSize: 19, fontWeight: '800', color: COLORS.indigo },
  focus: { backgroundColor: '#e7f2ee', borderWidth: 1, borderColor: '#d3e6df', borderRadius: 16, padding: 16 },
  focusTitle: { fontSize: 17, fontWeight: '800', color: '#205147' },
  focusText: { fontSize: 17, color: '#205147', marginTop: 6, lineHeight: 25 },
  eyebrow: { fontSize: 12, letterSpacing: 2, color: COLORS.muted, fontWeight: '700', textTransform: 'uppercase', marginTop: 4 },
  trend: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: COLORS.cardBorder },
  trendText: { fontSize: 16, color: COLORS.text, fontWeight: '600' },
});
