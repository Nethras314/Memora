import React, { useCallback, useEffect, useState } from 'react';
import { Modal, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { scheduleReminderNotification } from '../lib/notifications';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS, TASK_CATEGORIES } from '../theme';
import { t } from '../i18n';

export default function RoutineScreen() {
  const { currentPatient } = useAuth();
  const pid = currentPatient?.id || 1;
  const lang = currentPatient?.primary_language || 'en-IN';
  const [tasks, setTasks] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [title, setTitle] = useState('');
  const [time, setTime] = useState('09:00');
  const [category, setCategory] = useState('Routine');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [t, r] = await Promise.all([api.getTasks(pid), api.getReminders(pid)]);
      setTasks(t || []);
      setReminders(r || []);
    } catch {}
    finally { setLoading(false); }
  }, [pid]);

  useEffect(() => { load(); }, [load]);

  async function toggle(id) {
    try {
      const updated = await api.toggleTask(id, pid);
      setTasks((p) => p.map((t) => (t.id === id ? updated : t)));
    } catch {}
  }

  async function add() {
    if (title.trim().length < 2) { setError('Please name the routine step.'); return; }
    if (!/^\d{2}:\d{2}$/.test(time.trim())) { setError('Time must look like 09:00.'); return; }
    setSaving(true);
    setError('');
    try {
      await api.createTask({ patient_id: pid, title: title.trim(), task_time: time.trim(), category });
      setModal(false); setTitle(''); setTime('09:00'); setCategory('Routine');
      await load();
    } catch { setError('Could not add step. Try again.'); }
    finally { setSaving(false); }
  }

  async function reset() {
    try {
      await api.resetTasks(pid);
      await load();
    } catch {}
  }

  const doneCount = tasks.filter((t) => t.done).length;

  return (
    <Screen>
      <View style={{ gap: 12 }}>
        <SectionTitle title={t(lang, 'routineTitle')} sub={t(lang, 'routineSub')} />
        <View style={{ flexDirection: 'row', gap: 10 }}>
          <View style={{ flex: 1 }}><BigButton title={`↺ ${t(lang, 'resetToday')}`} variant="outline" onPress={reset} /></View>
          <View style={{ flex: 1 }}><BigButton title={`+ ${t(lang, 'addStep')}`} onPress={() => setModal(true)} /></View>
        </View>
      </View>

      <Card>
        <Text style={styles.count}>{doneCount} / {tasks.length} completed</Text>
        {loading ? <Text style={styles.muted}>Loading schedule…</Text> : null}
        {!loading && tasks.length === 0 ? <Text style={styles.muted}>No routine steps yet. Add one above.</Text> : null}
        {tasks.map((t) => (
          <View key={t.id} style={styles.taskRow}>
            <TouchableOpacity style={styles.taskMain} onPress={() => toggle(t.id)}>
              <Text style={{ fontSize: 28 }}>{t.done ? '✅' : '⭕'}</Text>
              <View style={{ flex: 1 }}>
                <Text style={[styles.taskTitle, t.done && styles.done]}>{t.title}</Text>
                <Text style={styles.muted}>{t.category} • {t.task_time}</Text>
              </View>
            </TouchableOpacity>
          </View>
        ))}
      </Card>

      <Card>
        <SectionTitle eyebrow="Gentle alerts" title="Today's reminders" />
        {reminders.slice(0, 6).map((r) => (
          <View key={r.id} style={styles.remRow}>
            <View style={[styles.dot, r.done && { backgroundColor: COLORS.green }]} />
            <Text style={[styles.taskTitle, (r.done || r.enabled === false) && styles.done, { flex: 1 }]}>{r.title}</Text>
            <Text style={styles.muted}>{r.reminder_time}</Text>
          </View>
        ))}
        {reminders.length === 0 ? <Text style={styles.muted}>No gentle alerts for today.</Text> : null}
      </Card>

      <Modal visible={modal} animationType="slide" onRequestClose={() => setModal(false)}>
        <Screen>
          <SectionTitle title={t(lang, 'addStep')} sub="A gentle step for today's flow." />
          <Text style={styles.label}>STEP NAME</Text>
          <TextInput style={styles.input} value={title} onChangeText={setTitle} placeholder="E.g., Morning walk in courtyard" />
          <Text style={styles.label}>TIME (HH:MM, 24-HOUR)</Text>
          <TextInput style={styles.input} value={time} onChangeText={setTime} placeholder="09:00" keyboardType="numbers-and-punctuation" maxLength={5} />
          <Text style={styles.label}>CATEGORY</Text>
          <View style={styles.chips}>
            {TASK_CATEGORIES.map((c) => (
              <TouchableOpacity key={c} style={[styles.chip, category === c && styles.chipOn]} onPress={() => setCategory(c)}>
                <Text style={[styles.chipText, category === c && { color: '#fff' }]}>{c}</Text>
              </TouchableOpacity>
            ))}
          </View>
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <View style={{ height: 12 }} />
          <BigButton title={saving ? 'Saving…' : 'Add step'} onPress={async () => { await add(); if (title) scheduleReminderNotification(title, time); }} disabled={saving} />
          <View style={{ height: 10 }} />
          <BigButton title="Cancel" variant="outline" onPress={() => setModal(false)} />
        </Screen>
      </Modal>
    </Screen>
  );
}

const styles = StyleSheet.create({
  count: { fontSize: 16, fontWeight: '800', color: COLORS.indigo, backgroundColor: '#eef0fc', alignSelf: 'flex-start', paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999, marginBottom: 10 },
  muted: { fontSize: 16, color: COLORS.muted, lineHeight: 23 },
  taskRow: { backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#e8e2d5', borderRadius: 18, marginTop: 10 },
  taskMain: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 16, minHeight: 76 },
  taskTitle: { fontSize: 19, fontWeight: '700', color: COLORS.text },
  done: { textDecorationLine: 'line-through', color: '#9aa1b2' },
  remRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: COLORS.cardBorder },
  dot: { width: 14, height: 14, borderRadius: 7, backgroundColor: COLORS.gold },
  label: { fontSize: 13, fontWeight: '800', color: COLORS.text, marginTop: 14, marginBottom: 6 },
  input: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#dcd6cc', borderRadius: 14, padding: 16, fontSize: 18, minHeight: 60 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  chip: { paddingHorizontal: 16, paddingVertical: 12, borderRadius: 999, backgroundColor: '#eef0fc', minHeight: 52, justifyContent: 'center' },
  chipOn: { backgroundColor: COLORS.indigo },
  chipText: { fontSize: 16, fontWeight: '800', color: COLORS.indigo },
  error: { color: COLORS.danger, fontSize: 16, fontWeight: '700', marginTop: 10 },
});
