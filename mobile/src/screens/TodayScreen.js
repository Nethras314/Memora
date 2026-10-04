import React, { useCallback, useEffect, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { speak } from '../lib/speech';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS } from '../theme';
import { t, tCaregiver } from '../i18n';

const RAG_COLORS = { green: COLORS.statusGreen, amber: COLORS.statusAmber, red: COLORS.statusRed };
const STATUS_KEY = { green: 'stable', amber: 'watch', red: 'needsAttention' };
const FLAG_KEY = { green: 'flagGreen', amber: 'flagAmber', red: 'flagRed' };

export default function TodayScreen({ go, openVoice }) {
  const { user, currentPatient } = useAuth();
  const role = (user?.role || 'caregiver').toLowerCase();
  const isClinician = ['caregiver', 'doctor', 'admin'].includes(role === 'caretaker' ? 'caregiver' : role);
  const lang = currentPatient?.primary_language || 'en-IN';
  const [tasks, setTasks] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [glance, setGlance] = useState(null);

  const load = useCallback(async () => {
    setLoadError(false);
    try {
      const [t, r] = await Promise.all([
        api.getTasks(currentPatient?.id || 1),
        api.getReminders(currentPatient?.id || 1),
      ]);
      setTasks(t || []);
      setReminders((r || []).filter((x) => x.enabled !== false));
    } catch {
      setLoadError(true);
    }
  }, [currentPatient]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!isClinician) return;
    let active = true;
    setGlance(null);
    api.getCaregiverGlance(currentPatient?.id || 1)
      .then((g) => { if (active) setGlance(g); })
      .catch(() => { if (active) setGlance(null); });
    return () => { active = false; };
  }, [currentPatient, isClinician]);

  const done = tasks.filter((t) => t.done).length;
  const pct = tasks.length ? Math.round((done / tasks.length) * 100) : 0;
  const status = glance?.status || 'amber';
  const flagKey = FLAG_KEY[status] || 'flagAmber';

  return (
    <Screen style={refreshing ? { opacity: 0.85 } : null}>
      <Card style={styles.hero}>
        <Text style={styles.heroDate}>TODAY • {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</Text>
        <Text style={styles.heroHi}>{t(lang, 'greeting')}{'\n'}{currentPatient?.name || 'friend'}.</Text>
        <Text style={styles.heroSub}>{t(lang, 'heroSub')}</Text>
        <View style={{ height: 14 }} />
        <BigButton title={`🎙 ${t(lang, 'talkToMemora')}`} variant="light" onPress={openVoice} />
        <View style={{ height: 10 }} />
        <BigButton title={t(lang, 'viewRoutine')} onPress={() => go('routine')} />
        <View style={styles.pctBox}>
          <Text style={styles.pct}>{pct}%</Text>
          <Text style={styles.pctSub}>{t(lang, 'dailyRoutineDone')}</Text>
        </View>
      </Card>

      {isClinician ? (
        <Card>
          <SectionTitle
            eyebrow={tCaregiver(lang, 'caregiverToday')}
            title={glance ? `${glance.index ?? '—'}/100` : '…'}
            sub={tCaregiver(lang, 'stabilityIndex')}
          />
          {glance ? (
            <View style={{ gap: 12 }}>
              <View style={styles.glanceRow}>
                <View style={[styles.glanceDot, { backgroundColor: RAG_COLORS[status] || COLORS.statusAmber }]} />
                <Text style={styles.glanceStatus}>{tCaregiver(lang, STATUS_KEY[status] || 'watch')}</Text>
                <Text style={styles.glanceDelta}>
                  {glance.index_delta != null ? `${glance.index_delta > 0 ? '+' : ''}${glance.index_delta}` : ''}
                </Text>
              </View>
              <View>
                <View style={styles.glanceBarWrap}>
                  <View style={[styles.glanceBar, { width: `${Math.max(0, Math.min(100, glance.routine_pct || 0))}%` }]} />
                </View>
                <Text style={styles.glanceSub}>{tCaregiver(lang, 'routineAdherence')}: {glance.routine_pct ?? 0}%</Text>
              </View>
              <Text style={styles.glanceFlag}>{tCaregiver(lang, flagKey)}</Text>
            </View>
          ) : <Text style={styles.muted}>…</Text>}
        </Card>
      ) : null}

      {loadError ? (
        <Card style={{ alignItems: 'center', gap: 12 }}>
          <Text style={styles.muted}>{t(lang, 'loadErrorMsg')}</Text>
          <BigButton title={t(lang, 'tryAgain')} variant="outline" onPress={load} />
        </Card>
      ) : null}

      <Card>
        <SectionTitle eyebrow={t(lang, 'quickActions')} title={t(lang, 'easyToReach')} />
        <View style={styles.grid}>
          <TouchableOpacity style={[styles.quick, { backgroundColor: COLORS.mint }]} onPress={openVoice}>
            <Text style={styles.quickIcon}>💬</Text><Text style={styles.quickText}>{t(lang, 'askQuestion')}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.quick, { backgroundColor: '#eeece7' }]} onPress={() => go('memories')}>
            <Text style={styles.quickIcon}>▣</Text><Text style={styles.quickText}>{t(lang, 'openMemories')}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.quick, { backgroundColor: COLORS.peach }]} onPress={() => go('games')}>
            <Text style={styles.quickIcon}>🧠</Text><Text style={styles.quickText}>{t(lang, 'tryActivity')}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.quick, { backgroundColor: '#f3f0ea' }]} onPress={() => go('reminders')}>
            <Text style={styles.quickIcon}>♧</Text><Text style={styles.quickText}>{t(lang, 'seeReminders')}</Text>
          </TouchableOpacity>
        </View>
      </Card>

      <Card>
        <SectionTitle eyebrow={t(lang, 'gentlePrompts')} title={`${t(lang, 'todaysReminders')} (${reminders.length})`} />
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
        <BigButton title={t(lang, 'manageReminders')} variant="mint" onPress={() => { speak(`You have ${reminders.length} reminders today.`); go('reminders'); }} />
      </Card>

      <View style={{ flexDirection: 'row', gap: 10 }}>
        <View style={{ flex: 1 }}><BigButton title={`🔄 ${t(lang, 'refresh')}`} variant="outline" onPress={async () => { setRefreshing(true); await load(); setRefreshing(false); }} /></View>
        <View style={{ flex: 1 }}><BigButton title={`🎮 ${t(lang, 'games')}`} onPress={() => go('games')} /></View>
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
  glanceRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  glanceDot: { width: 12, height: 12, borderRadius: 6 },
  glanceStatus: { fontSize: 16, fontWeight: '800', color: COLORS.text, flex: 1 },
  glanceDelta: { fontSize: 16, fontWeight: '800', color: COLORS.indigo },
  glanceBarWrap: { height: 10, borderRadius: 5, backgroundColor: '#e5dfd4', overflow: 'hidden', marginBottom: 6 },
  glanceBar: { height: 10, borderRadius: 5, backgroundColor: COLORS.green },
  glanceSub: { fontSize: 15, color: COLORS.muted, fontWeight: '700' },
  glanceFlag: { fontSize: 16, color: COLORS.text, lineHeight: 24 },
});
