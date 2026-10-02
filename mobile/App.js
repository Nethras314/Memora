import React, { useState } from 'react';
import { ActivityIndicator, Modal, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { AuthProvider, useAuth } from './src/lib/auth';
import { COLORS, LANGUAGES } from './src/theme';
import { languageLabel, t } from './src/i18n';
import AuthScreen from './src/screens/AuthScreen';
import PinScreen from './src/screens/PinScreen';
import TodayScreen from './src/screens/TodayScreen';
import MemoriesScreen from './src/screens/MemoriesScreen';
import RoutineScreen from './src/screens/RoutineScreen';
import RemindersScreen from './src/screens/RemindersScreen';
import GamesScreen from './src/screens/GamesScreen';
import VoiceScreen from './src/screens/VoiceScreen';
import CalmScreen from './src/screens/CalmScreen';
import ProgressScreen from './src/screens/ProgressScreen';

const TAB_ICONS = {
  today: '🏠', voice: '🎙', memories: '▣', routine: '📅',
  reminders: '⏰', games: '🧠', calm: '🌿', progress: '📈',
};
const TAB_KEYS = {
  today: 'tabToday', voice: 'tabVoice', memories: 'tabMemories', routine: 'tabRoutine',
  reminders: 'tabReminders', games: 'tabGames', calm: 'tabCalm', progress: 'tabProgress',
};
const TAB_PINS = { memories: true };

function PatientShell() {
  const { user, loading, logout, currentPatient, pinVerified, setLanguage } = useAuth();
  const [tab, setTab] = useState('today');
  const [pinAsk, setPinAsk] = useState(false);
  const [pendingTab, setPendingTab] = useState(null);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);

  const lang = currentPatient?.primary_language || 'en-IN';
  const tabs = Object.keys(TAB_ICONS).map((id) => ({
    id,
    pin: !!TAB_PINS[id],
    label: `${TAB_ICONS[id]}\n${t(lang, TAB_KEYS[id])}`,
  }));

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.indigo} />
        <Text style={styles.muted}>Loading MEMORA…</Text>
      </View>
    );
  }
  if (!user) return <AuthScreen />;

  function go(id) {
    const def = tabs.find((x) => x.id === id);
    if (def?.pin && !pinVerified) {
      setPendingTab(id);
      setPinAsk(true);
      return;
    }
    setTab(id);
  }

  function unlocked() {
    setPinAsk(false);
    if (pendingTab) { setTab(pendingTab); setPendingTab(null); }
  }

  return (
    <SafeAreaView style={styles.root} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <View style={styles.brandRow}>
          <View style={styles.brandIcon}><Text style={{ color: '#fff', fontSize: 22 }}>♡</Text></View>
          <View>
            <Text style={styles.brand}>MEMORA</Text>
            <Text style={styles.patient}>{currentPatient?.name || 'Your gentle space'}</Text>
          </View>
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity
            onPress={() => setLangOpen(true)}
            style={styles.langBtn}
            accessibilityRole="button"
            accessibilityLabel={t(lang, 'chooseLanguage')}
          >
            <Text style={styles.langBtnText}>🌐 {languageLabel(lang).split(' (')[0]}</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={logout} style={styles.logout}>
            <Text style={styles.logoutText}>{t(lang, 'signOut')}</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={{ flex: 1 }}>
        {tab === 'today' && <TodayScreen go={go} openVoice={() => setVoiceOpen(true)} />}
        {tab === 'memories' && <MemoriesScreen />}
        {tab === 'routine' && <RoutineScreen />}
        {tab === 'reminders' && <RemindersScreen />}
        {tab === 'games' && <GamesScreen />}
        {tab === 'voice' && <VoiceScreen />}
        {tab === 'calm' && <CalmScreen />}
        {tab === 'progress' && <ProgressScreen />}
      </View>

      <View style={styles.tabbar}>
        {tabs.map((x) => (
          <TouchableOpacity key={x.id} style={[styles.tab, tab === x.id && styles.tabOn]} onPress={() => (x.id === 'voice' ? setVoiceOpen(true) : go(x.id))}>
            <Text style={[styles.tabText, tab === x.id && { color: '#fff' }]}>{x.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Modal visible={voiceOpen} animationType="slide" onRequestClose={() => setVoiceOpen(false)}>
        <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.cream }}>
          <TouchableOpacity style={styles.closeVoice} onPress={() => setVoiceOpen(false)}>
            <Text style={styles.closeVoiceText}>✕ Close voice</Text>
          </TouchableOpacity>
          <VoiceScreen />
        </SafeAreaView>
      </Modal>

      <Modal visible={pinAsk} animationType="slide" onRequestClose={() => setPinAsk(false)}>
        <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.cream }}>
          <PinScreen onUnlocked={unlocked} onCancel={() => setPinAsk(false)} />
        </SafeAreaView>
      </Modal>

      <Modal visible={langOpen} animationType="slide" transparent onRequestClose={() => setLangOpen(false)}>
        <View style={styles.langOverlay}>
          <View style={styles.langSheet}>
            <Text style={styles.langTitle}>🌐 {t(lang, 'chooseLanguage')}</Text>
            {LANGUAGES.map((l) => {
              const active = l.code === lang;
              return (
                <TouchableOpacity
                  key={l.code}
                  style={[styles.langOption, active && styles.langOptionOn]}
                  onPress={() => { setLanguage(l.code); setLangOpen(false); }}
                  accessibilityRole="button"
                  accessibilityState={{ selected: active }}
                >
                  <Text style={[styles.langOptionText, active && { color: '#fff' }]}>{l.label}</Text>
                </TouchableOpacity>
              );
            })}
            <TouchableOpacity style={styles.langCancel} onPress={() => setLangOpen(false)}>
              <Text style={styles.langCancelText}>{t(lang, 'close')}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <PatientShell />
      </AuthProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: COLORS.cream },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10, backgroundColor: COLORS.cream },
  muted: { fontSize: 17, color: COLORS.muted },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: '#fffdfa', borderBottomWidth: 1, borderBottomColor: COLORS.cardBorder, paddingHorizontal: 16, paddingVertical: 12,
  },
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  brandIcon: { width: 46, height: 46, borderRadius: 15, backgroundColor: COLORS.indigo, alignItems: 'center', justifyContent: 'center' },
  brand: { fontSize: 21, fontWeight: '800', color: COLORS.text },
  patient: { fontSize: 14, color: COLORS.muted },
  logout: { paddingHorizontal: 16, paddingVertical: 12, borderRadius: 14, backgroundColor: '#f3f0ea', minHeight: 48, justifyContent: 'center' },
  logoutText: { fontSize: 16, fontWeight: '800', color: COLORS.text },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  langBtn: { paddingHorizontal: 12, paddingVertical: 12, borderRadius: 14, backgroundColor: '#e8f3ef', minHeight: 48, justifyContent: 'center' },
  langBtnText: { fontSize: 15, fontWeight: '800', color: COLORS.indigo },
  langOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  langSheet: { backgroundColor: COLORS.paper, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 20, paddingBottom: 32 },
  langTitle: { fontSize: 20, fontWeight: '800', color: COLORS.text, marginBottom: 16 },
  langOption: { paddingHorizontal: 16, paddingVertical: 16, borderRadius: 16, backgroundColor: '#f5f2ea', marginBottom: 10, minHeight: 60, justifyContent: 'center' },
  langOptionOn: { backgroundColor: COLORS.indigo },
  langOptionText: { fontSize: 18, fontWeight: '800', color: COLORS.text },
  langCancel: { marginTop: 8, paddingVertical: 14, borderRadius: 16, backgroundColor: '#fff', borderWidth: 1, borderColor: COLORS.cardBorder, alignItems: 'center' },
  langCancelText: { fontSize: 17, fontWeight: '800', color: COLORS.indigo },
  tabbar: {
    flexDirection: 'row', backgroundColor: '#fffdfa', borderTopWidth: 1, borderTopColor: COLORS.cardBorder,
    paddingHorizontal: 6, paddingVertical: 8, gap: 4,
  },
  tab: { flex: 1, minHeight: 62, borderRadius: 14, alignItems: 'center', justifyContent: 'center', paddingVertical: 6, backgroundColor: '#f5f2ea' },
  tabOn: { backgroundColor: COLORS.indigo },
  tabText: { fontSize: 12, fontWeight: '800', color: COLORS.text, textAlign: 'center', lineHeight: 16 },
  closeVoice: { margin: 16, marginBottom: 0, backgroundColor: '#fff', borderWidth: 1, borderColor: COLORS.cardBorder, borderRadius: 14, padding: 14, alignItems: 'center' },
  closeVoiceText: { fontSize: 17, fontWeight: '800', color: COLORS.indigo },
});
