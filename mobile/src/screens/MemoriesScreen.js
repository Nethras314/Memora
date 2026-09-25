import React, { useCallback, useEffect, useState } from 'react';
import { Image, Modal, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { speak } from '../lib/speech';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS, MEMORY_CATEGORIES } from '../theme';

export default function MemoriesScreen() {
  const { currentPatient } = useAuth();
  const pid = currentPatient?.id || 1;
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [category, setCategory] = useState('Person');
  const [title, setTitle] = useState('');
  const [details, setDetails] = useState('');
  const [photo, setPhoto] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems((await api.getMemories(pid)) || []);
    } catch {
      setError('Could not load memories. Check connection.');
    } finally {
      setLoading(false);
    }
  }, [pid]);

  useEffect(() => { load(); }, [load]);

  function openAdd() {
    setEditing(null); setCategory('Person'); setTitle(''); setDetails(''); setPhoto(null); setError(''); setModal(true);
  }
  function openEdit(m) {
    setEditing(m); setCategory(m.category || 'Person'); setTitle(m.title || ''); setDetails(m.details || ''); setPhoto(null); setError(''); setModal(true);
  }

  async function pickPhoto() {
    const res = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.7 });
    if (!res.canceled && res.assets?.[0]) setPhoto(res.assets[0]);
  }

  async function takePhoto() {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) return;
    const res = await ImagePicker.launchCameraAsync({ quality: 0.7 });
    if (!res.canceled && res.assets?.[0]) setPhoto(res.assets[0]);
  }

  async function save() {
    if (title.trim().length < 2 || details.trim().length < 2) { setError('Please add a title and details.'); return; }
    setSaving(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('patient_id', String(pid));
      fd.append('category', category);
      fd.append('title', title.trim());
      fd.append('details', details.trim());
      if (photo) {
        const uri = photo.uri;
        const name = photo.fileName || uri.split('/').pop() || 'photo.jpg';
        const type = photo.mimeType || (name.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg');
        fd.append('photo', { uri, name, type });
      }
      if (editing) await api.updateMemory(editing.id, fd, pid);
      else await api.createMemory(fd);
      setModal(false);
      await load();
    } catch {
      setError('Could not save. Check fields and connection.');
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!confirmDelete) return;
    try {
      await api.deleteMemory(confirmDelete, pid);
      setConfirmDelete(null);
      await load();
    } catch {
      setError('Could not delete memory.');
    }
  }

  return (
    <Screen>
      <View style={styles.header}>
        <SectionTitle title="Personal Memory Bank" sub="Familiar people, places and comforts." />
        <BigButton title="+ Save memory" onPress={openAdd} />
      </View>
      {loading ? <Card><Text style={styles.muted}>Loading your familiar moments…</Text></Card> : null}
      {!loading && items.length === 0 ? (
        <Card style={{ alignItems: 'center' }}>
          <Text style={{ fontSize: 54 }}>🖼️</Text>
          <Text style={styles.emptyTitle}>No memories saved yet</Text>
          <Text style={styles.muted}>Add a photo of family, food, or home.</Text>
          <View style={{ height: 12 }} />
          <BigButton title="+ Save your first memory" onPress={openAdd} />
        </Card>
      ) : null}
      {items.map((m) => (
        <Card key={m.id}>
          {m.photo_url ? <Image source={{ uri: m.photo_url }} style={styles.photo} /> : <View style={styles.placeholder}><Text style={{ fontSize: 44 }}>🖼️</Text></View>}
          <Text style={styles.cat}>{m.category}</Text>
          <Text style={styles.mTitle}>{m.title}</Text>
          <Text style={styles.mDetails}>{m.details}</Text>
          <View style={styles.actions}>
            <TouchableOpacity style={styles.actionBtn} onPress={() => speak(`${m.title}. ${m.details}`)}>
              <Text style={styles.actionText}>🔊 Listen</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.actionBtn} onPress={() => openEdit(m)}>
              <Text style={styles.actionText}>✏️ Edit</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.actionBtn, styles.dangerBtn]} onPress={() => setConfirmDelete(m.id)}>
              <Text style={[styles.actionText, { color: COLORS.danger }]}>🗑 Delete</Text>
            </TouchableOpacity>
          </View>
        </Card>
      ))}

      <Modal visible={modal} animationType="slide" onRequestClose={() => setModal(false)}>
        <Screen>
          <SectionTitle title={editing ? 'Edit familiar moment' : 'Save a familiar moment'} sub="Recognition and comfort." />
          <Text style={styles.label}>CATEGORY</Text>
          <View style={styles.chips}>
            {MEMORY_CATEGORIES.map((c) => (
              <TouchableOpacity key={c} style={[styles.chip, category === c && styles.chipOn]} onPress={() => setCategory(c)}>
                <Text style={[styles.chipText, category === c && { color: '#fff' }]}>{c}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={styles.label}>TITLE</Text>
          <TextInput style={styles.input} value={title} onChangeText={setTitle} placeholder="E.g., Eldest Daughter Anitha" />
          <Text style={styles.label}>DETAILS</Text>
          <TextInput style={[styles.input, { minHeight: 100 }]} value={details} onChangeText={setDetails} multiline placeholder="E.g., Anitha calls every evening." />
          <Text style={styles.label}>PHOTO (OPTIONAL)</Text>
          <View style={{ flexDirection: 'row', gap: 10 }}>
            <View style={{ flex: 1 }}><BigButton title="🖼 Gallery" variant="mint" onPress={pickPhoto} /></View>
            <View style={{ flex: 1 }}><BigButton title="📷 Camera" variant="gold" onPress={takePhoto} /></View>
          </View>
          {photo ? <Text style={styles.muted}>Selected: {photo.uri.split('/').pop()}</Text> : null}
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <View style={{ height: 12 }} />
          <BigButton title={saving ? 'Saving…' : editing ? 'Update memory' : 'Save memory'} onPress={save} disabled={saving} />
          <View style={{ height: 10 }} />
          <BigButton title="Cancel" variant="outline" onPress={() => setModal(false)} />
        </Screen>
      </Modal>

      <Modal visible={!!confirmDelete} transparent animationType="fade" onRequestClose={() => setConfirmDelete(null)}>
        <View style={styles.confirmWrap}>
          <View style={styles.confirm}>
            <Text style={styles.confirmTitle}>Delete this memory?</Text>
            <Text style={styles.muted}>This cannot be undone.</Text>
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
  header: { gap: 12 },
  muted: { fontSize: 17, color: COLORS.muted, lineHeight: 24 },
  emptyTitle: { fontSize: 21, fontWeight: '800', color: COLORS.text, marginTop: 8 },
  photo: { width: '100%', height: 200, borderRadius: 16, marginBottom: 12 },
  placeholder: { width: '100%', height: 160, borderRadius: 16, backgroundColor: '#eeece7', alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  cat: { fontSize: 13, fontWeight: '800', color: COLORS.indigo, textTransform: 'uppercase' },
  mTitle: { fontSize: 22, fontWeight: '800', color: COLORS.text, marginTop: 2 },
  mDetails: { fontSize: 18, color: '#5d687e', marginTop: 4, lineHeight: 26 },
  actions: { flexDirection: 'row', gap: 10, marginTop: 14 },
  actionBtn: { flex: 1, minHeight: 60, borderRadius: 16, backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#e8e2d5', alignItems: 'center', justifyContent: 'center' },
  dangerBtn: { backgroundColor: '#fef2f2', borderColor: '#fecaca' },
  actionText: { fontSize: 17, fontWeight: '800', color: COLORS.indigo },
  label: { fontSize: 13, fontWeight: '800', color: COLORS.text, marginTop: 14, marginBottom: 6 },
  input: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#dcd6cc', borderRadius: 14, padding: 16, fontSize: 18, minHeight: 60 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  chip: { paddingHorizontal: 16, paddingVertical: 12, borderRadius: 999, backgroundColor: '#eef0fc', minHeight: 52, justifyContent: 'center' },
  chipOn: { backgroundColor: COLORS.indigo },
  chipText: { fontSize: 16, fontWeight: '800', color: COLORS.indigo },
  error: { color: COLORS.danger, fontSize: 16, fontWeight: '700', marginTop: 10 },
  confirmWrap: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', alignItems: 'center', justifyContent: 'center', padding: 24 },
  confirm: { backgroundColor: '#fff', borderRadius: 24, padding: 24, width: '100%' },
  confirmTitle: { fontSize: 22, fontWeight: '800', color: COLORS.text },
});
