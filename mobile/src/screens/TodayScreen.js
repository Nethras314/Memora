import React, { useCallback, useEffect, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { speak } from '../lib/speech';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS } from '../theme';

export default function TodayScreen({ go, openVoice }) {
  const { currentPatient } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [t, r] = await Promise.all([
        api.getTasks(currentPatient?.id || 1),
        api.getReminders(currentPatient?.id || 1),
      ]);
      setTasks(t || []);
      setReminders((r || []).filter((x) => x.enabled !== false));
    } catch {}
  }, [currentPatient]);

  useEffect(() => { load(); }, [load]);

  const done = tasks.filter((t) => t.done).length;
  const pct = tasks.length ? Math.round((done / tasks.length) * 100) : 0;

  return (
    <Screen style={refreshing ? { opacity: 0.85 } : null}>
      <Card style={styles.hero}>
        <Text style={styles.heroDate}>TODAY • {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</Text>
        <Text style={styles.heroHi}>Good morning,{'\n'}{currentPatient?.name || 'friend'}.</Text>
        <Text style={styles.heroSub}>Ask me about family, your next reminder, or a fun activity.</Text>
        <View style={{ height: 14 }} />
        <BigButton title="🎙 Talk to MEMORA →" variant="light" onPress={openVoice} />
        <View style={{ height: 10 }} />
        <BigButton title="View today's routine" onPress={() => go('routine')} />
        <View style={styles.pctBox}>
          <Text style={styles.pct}>{pct}%</Text>
          <Text style={styles.pctSub}>daily routine completed</Text>
        </View>
      </Card>

      <Card>
        <SectionTitle eyebrow="Quick actions" title="Easy to reach" />
        <View style={styles.grid}>
          <TouchableOpacity style={[styles.quick, { backgroundColor: COLORS.mint }]} onPress={openVoice}>
            <Text style={styles.quickIcon}>💬</Text><Text style={styles.quickText}>Ask a question →</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.quick, { backgroundColor: '#eeece7' }]} onPress={() => go('memories')}>
            <Text style={styles.quickIcon}>▣</Text><Text style={styles.quickText}>Open memories →</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.quick, { backgroundColor: COLORS.peach }]} onPress={() => go('games')}>
            <Text style={styles.quickIcon}>🧠</Text><Text style={styles.quickText}>Try an activity →</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.quick, { backgroundColor: '#f3f0ea' }]} onPress={() => go('reminders')}>
            <Text style={styles.quickIcon}>♧</Text><Text style={styles.quickText}>See reminders →</Text>
          </TouchableOpacity>
        </View>
      </Card>

      <Card>
        <SectionTitle eyebrow="Gentle prompts" title={`Today's reminders (${reminders.length})`} />
        {reminders.slice(0, 4).map((r) => (
          <View key={r.id} style={styles.row}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, flex: 1 }}>
              <View style={[styles.dot, r.done && { backgroundColor: COLORS.green }]} />
              <Text style={[styles.rowTitle, r.done && styles.done]}>{r.title}</Text>
            </View>
            <Text style={styles.time}>{r.reminder_time}</Text>
          </View>
        ))}
        {reminders.length === 0 ? <Text style={styles.muted}>No gentle prompts yet.</Text> : null}
        <View style={{ height: 12 }} />
        <BigButton title="Manage all reminders →" variant="mint" onPress={() => { speak(`You have ${reminders.length} reminders today.`); go('reminders'); }} />
      </Card>

      <View style={{ flexDirection: 'row', gap: 10 }}>
        <View style={{ flex: 1 }}><BigButton title="🔄 Refresh" variant="outline" onPress={async () => { setRefreshing(true); await load(); setRefreshing(false); }} /></View>
        <View style={{ flex: 1 }}><BigButton title="🎮 Games" onPress={() => go('games')} /></View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: { backgroundColor: COLORS.indigo },
  heroDate: { color: '#dcd9ff', fontSize: 13, fontWeight: '800', letterSpacing: 2 },
  heroHi: { color: '#fff', fontSize: 34, fontWeight: '800', marginTop: 6, lineHeight: 40 },
  heroSub: { color: '#ecebff', fontSize: 18, marginTop: 8, lineHeight: 26 },
  pctBox: { backgroundColor: 'rgba(255,255,255,0.12)', borderRadius: 20, padding: 16, alignItems: 'center', marginTop: 16 },
  pct: { color: '#fff', fontSize: 48, fontWeight: '800' },
  pctSub: { color: '#ddd9ff', fontSize: 15 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  quick: { width: '48%', minHeight: 120, borderRadius: 20, padding: 16, justifyContent: 'space-between' },
  quickIcon: { fontSize: 30 },
  quickText: { fontSize: 17, fontWeight: '800', color: COLORS.text },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: COLORS.cardBorder },
  dot: { width: 14, height: 14, borderRadius: 7, backgroundColor: COLORS.gold },
  rowTitle: { fontSize: 18, fontWeight: '600', color: COLORS.text, flex: 1 },
  done: { textDecorationLine: 'line-through', color: '#9aa1b2' },
  time: { fontSize: 16, color: COLORS.muted, fontWeight: '700' },
  muted: { fontSize: 17, color: COLORS.muted },
});
