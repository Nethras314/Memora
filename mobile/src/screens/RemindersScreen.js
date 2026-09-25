import React, { useCallback, useEffect, useState } from 'react';
import { Modal, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { scheduleReminderNotification } from '../lib/notifications';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS, REMINDER_CATEGORIES, REMINDER_FREQUENCIES } from '../theme';

export default function RemindersScreen() {
  const { currentPatient } = useAuth();
  const pid = currentPatient?.id || 1;
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [title, setTitle] = useState('');
  const [time, setTime] = useState('09:00');
  const [category, setCategory] = useState('Custom');
  const [frequency, setFrequency] = useState('Daily');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setItems((await api.getReminders(pid)) || []); } catch {}
    finally { setLoading(false); }
  }, [pid]);

  useEffect(() => { load(); }, [load]);

  function openAdd() { setEditing(null); setTitle(''); setTime('09:00'); setCategory('Custom'); setFrequency('Daily'); setError(''); setModal(true); }
  function openEdit(r) { setEditing(r); setTitle(r.title || ''); setTime((r.reminder_time || '09:00').slice(0, 5)); setCategory(r.category || 'Custom'); setFrequency(r.frequency || 'Daily'); setError(''); setModal(true); }

  async function save() {
    if (title.trim().length < 2) { setError('Please name the reminder.'); return; }
    if (!/^\d{2}:\d{2}$/.test(time.trim())) { setError('Time must look like 09:00.'); return; }
    setSaving(true);
    setError('');
    try {
      const payload = { patient_id: pid, title: title.trim(), reminder_time: time.trim(), category, frequency };
      if (editing) await api.updateReminder(editing.id, payload, pid);
      else await api.createReminder(payload);
      scheduleReminderNotification(title.trim(), time.trim());
      setModal(false);
      await load();
    } catch { setError('Could not save reminder.'); }
    finally { setSaving(false); }
  }

  async function toggleEnabled(id) {
    try {
      await api.toggleReminderEnabled(id, pid);
      await load();
    } catch {}
  }

  async function remove() {
    if (!confirmDelete) return;
    try {
      await api.deleteReminder(confirmDelete, pid);
      setConfirmDelete(null);
      await load();
    } catch {}
  }

  return (
    <Screen>
      <View style={{ gap: 12 }}>
        <SectionTitle title="Reminders" sub="Gentle prompts for medicine, meals, water, and rest." />
        <BigButton title="+ Add reminder" onPress={openAdd} />
      </View>
      <Card>
        {loading ? <Text style={styles.muted}>Loading reminders…</Text> : null}
        {!loading && items.length === 0 ? <Text style={styles.muted}>No reminders yet. Add a gentle prompt above.</Text> : null}
        {items.map((r) => (
          <View key={r.id} style={[styles.row, r.enabled === false && { opacity: 0.6 }]}>
            <View style={{ flex: 1 }}>
              <Text style={styles.cat}>{r.category || 'Custom'} • {r.frequency || 'Daily'}</Text>
              <Text style={styles.title}>{r.title}</Text>
              <Text style={styles.time}>⏰ {r.reminder_time}</Text>
            </View>
            <View style={styles.btnCol}>
              <TouchableOpacity style={[styles.mini, r.enabled !== false && styles.miniOn]} onPress={() => toggleEnabled(r.id)}>
                <Text style={styles.miniText}>{r.enabled === false ? 'Off' : 'On'}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.mini} onPress={() => openEdit(r)}><Text style={styles.miniText}>Edit</Text></TouchableOpacity>
              <TouchableOpacity style={styles.mini} onPress={() => setConfirmDelete(r.id)}><Text style={[styles.miniText, { color: COLORS.danger }]}>Delete</Text></TouchableOpacity>
            </View>
          </View>
        ))}
      </Card>

      <Modal visible={modal} animationType="slide" onRequestClose={() => setModal(false)}>
        <Screen>
          <SectionTitle title={editing ? 'Edit reminder' : 'Add reminder'} sub="A calm prompt at the right time of day." />
          <Text style={styles.label}>TITLE</Text>
          <TextInput style={styles.input} value={title} onChangeText={setTitle} placeholder="E.g., Take afternoon tablet" />
          <Text style={styles.label}>TIME (HH:MM)</Text>
          <TextInput style={styles.input} value={time} onChangeText={setTime} placeholder="09:00" maxLength={5} keyboardType="numbers-and-punctuation" />
          <Text style={styles.label}>REPEAT</Text>
          <View style={styles.chips}>
            {REMINDER_FREQUENCIES.map((f) => (
              <TouchableOpacity key={f} style={[styles.chip, frequency === f && styles.chipOn]} onPress={() => setFrequency(f)}>
                <Text style={[styles.chipText, frequency === f && { color: '#fff' }]}>{f}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={styles.label}>CATEGORY</Text>
          <View style={styles.chips}>
            {REMINDER_CATEGORIES.map((c) => (
              <TouchableOpacity key={c} style={[styles.chip, category === c && styles.chipOn]} onPress={() => setCategory(c)}>
                <Text style={[styles.chipText, category === c && { color: '#fff' }]}>{c}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={styles.note}>Saving also schedules a gentle phone notification.</Text>
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <View style={{ height: 12 }} />
          <BigButton title={saving ? 'Saving…' : editing ? 'Save changes' : 'Add reminder'} onPress={save} disabled={saving} />
          <View style={{ height: 10 }} />
          <BigButton title="Cancel" variant="outline" onPress={() => setModal(false)} />
        </Screen>
      </Modal>

      <Modal visible={!!confirmDelete} transparent animationType="fade" onRequestClose={() => setConfirmDelete(null)}>
        <View style={styles.confirmWrap}>
          <View style={styles.confirm}>
            <Text style={styles.confirmTitle}>Delete this reminder?</Text>
            <View style={{ height: 14 }} />
            <BigButton title="Delete" variant="danger" onPress={remove} />
            <View style={{ height: 10 }} />
            <BigButton title="Keep it" variant="outline" onPress={() => setConfirmDelete(null)} />
          </View>
        </View>
      </Modal>
    </Screen>
  );
}

const styles = StyleSheet.create({
  muted: { fontSize: 17, color: COLORS.muted, lineHeight: 24 },
  row: { backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#e8e2d5', borderRadius: 18, padding: 16, marginTop: 10, flexDirection: 'row', gap: 12 },
  cat: { fontSize: 13, fontWeight: '800', color: COLORS.indigo, textTransform: 'uppercase' },
  title: { fontSize: 20, fontWeight: '800', color: COLORS.text, marginTop: 2 },
  time: { fontSize: 17, color: COLORS.muted, marginTop: 4, fontWeight: '700' },
  btnCol: { gap: 8, justifyContent: 'center' },
  mini: { minWidth: 84, minHeight: 48, borderRadius: 12, backgroundColor: '#fff', borderWidth: 1, borderColor: '#dcd6cc', alignItems: 'center', justifyContent: 'center', paddingHorizontal: 10 },
  miniOn: { backgroundColor: '#ecfdf5', borderColor: '#a7f3d0' },
  miniText: { fontSize: 16, fontWeight: '800', color: COLORS.text },
  label: { fontSize: 13, fontWeight: '800', color: COLORS.text, marginTop: 14, marginBottom: 6 },
  input: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#dcd6cc', borderRadius: 14, padding: 16, fontSize: 18, minHeight: 60 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  chip: { paddingHorizontal: 16, paddingVertical: 12, borderRadius: 999, backgroundColor: '#eef0fc', minHeight: 52, justifyContent: 'center' },
  chipOn: { backgroundColor: COLORS.indigo },
  chipText: { fontSize: 16, fontWeight: '800', color: COLORS.indigo },
  note: { fontSize: 15, color: COLORS.muted, marginTop: 12 },
  error: { color: COLORS.danger, fontSize: 16, fontWeight: '700', marginTop: 10 },
  confirmWrap: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', alignItems: 'center', justifyContent: 'center', padding: 24 },
  confirm: { backgroundColor: '#fff', borderRadius: 24, padding: 24, width: '100%' },
  confirmTitle: { fontSize: 22, fontWeight: '800', color: COLORS.text },
});
