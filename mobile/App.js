import React, { useState } from 'react';
import { ActivityIndicator, Modal, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { AuthProvider, useAuth } from './src/lib/auth';
import { COLORS, LANGUAGES } from './src/theme';
import { languageLabel, t } from './src/i18n';
import { BigButton } from './src/components/ui';
import AuthScreen from './src/screens/AuthScreen';
import PinScreen from './src/screens/PinScreen';
import TodayScreen from './src/screens/TodayScreen';
import MemoriesScreen from './src/screens/MemoriesScreen';
import RoutineScreen from './src/screens/RoutineScreen';
import RemindersScreen from './src/screens/RemindersScreen';
import GamesScreen from './src/screens/GamesScreen';
import VoiceScreen from './src/screens/VoiceScreen';

// Full set of reachable screens. Only PRIMARY_TABS appear in the bottom bar;
// the rest (routine, reminders) are secondary and reached from Today.
const TAB_ICONS = {
  today: '🏠', memories: '▣', games: '🧠', voice: '🎙',
  routine: '📅', reminders: '⏰',
};
const TAB_KEYS = {
  today: 'tabToday', memories: 'tabMemories', games: 'tabGames', voice: 'tabVoice',
  routine: 'tabRoutine', reminders: 'tabReminders',
};
const TAB_PINS = { memories: true };
const PRIMARY_TABS = ['today', 'memories', 'games', 'voice'];

function PatientShell() {
  const { user, loading, logout, currentPatient, pinVerified, setLanguage } = useAuth();
  const [tab, setTab] = useState('today');
  const [pinAsk, setPinAsk] = useState(false);
  const [pendingTab, setPendingTab] = useState(null);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);
  const [signOutAsk, setSignOutAsk] = useState(false);

  const lang = currentPatient?.primary_language || 'en-IN';
  const tabs = PRIMARY_TABS.map((id) => ({
    id,
    icon: TAB_ICONS[id],
    label: t(lang, TAB_KEYS[id]),
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
    if (TAB_PINS[id] && !pinVerified) {
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
          <TouchableOpacity
            style={styles.brandIcon}
            onLongPress={() => setSignOutAsk(true)}
            accessibilityRole="button"
            accessibilityLabel={t(lang, 'signOut')}
          >
            <Text style={{ color: '#fff', fontSize: 22 }}>♡</Text>
          </TouchableOpacity>
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
        </View>
      </View>

      <View style={{ flex: 1 }}>
        {tab === 'today' && <TodayScreen go={go} openVoice={() => setVoiceOpen(true)} />}
        {tab === 'memories' && <MemoriesScreen />}
        {tab === 'routine' && <RoutineScreen />}
        {tab === 'reminders' && <RemindersScreen />}
        {tab === 'games' && <GamesScreen />}
        {tab === 'voice' && <VoiceScreen />}
      </View>

      <View style={styles.tabbar}>
        {tabs.map((x) => (
          <TouchableOpacity
            key={x.id}
            style={[styles.tab, tab === x.id && styles.tabOn]}
            onPress={() => (x.id === 'voice' ? setVoiceOpen(true) : go(x.id))}
            accessibilityRole="button"
            accessibilityLabel={x.label}
          >
            <Text style={[styles.tabIcon, tab === x.id && { color: '#fff' }]}>{x.icon}</Text>
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

      <Modal visible={signOutAsk} transparent animationType="fade" onRequestClose={() => setSignOutAsk(false)}>
        <View style={styles.signOutOverlay}>
          <View style={styles.signOutSheet}>
            <Text style={styles.signOutTitle}>{t(lang, 'signOut')}?</Text>
            <View style={{ height: 14 }} />
            <BigButton title={t(lang, 'signOut')} variant="danger" onPress={logout} />
            <View style={{ height: 10 }} />
            <BigButton title={t(lang, 'close')} variant="outline" onPress={() => setSignOutAsk(false)} />
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
  signOutOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', alignItems: 'center', justifyContent: 'center', padding: 24 },
  signOutSheet: { backgroundColor: '#fff', borderRadius: 24, padding: 24, width: '100%' },
  signOutTitle: { fontSize: 22, fontWeight: '800', color: COLORS.text, textAlign: 'center' },
  tabbar: {
    flexDirection: 'row', backgroundColor: '#fffdfa', borderTopWidth: 1, borderTopColor: COLORS.cardBorder,
    paddingHorizontal: 8, paddingVertical: 8, gap: 6,
  },
  tab: { flex: 1, minHeight: 76, borderRadius: 16, alignItems: 'center', justifyContent: 'center', paddingVertical: 8, backgroundColor: '#f5f2ea' },
  tabOn: { backgroundColor: COLORS.indigo },
  tabIcon: { fontSize: 26, color: COLORS.text, marginBottom: 2 },
  tabText: { fontSize: 15, fontWeight: '800', color: COLORS.text, textAlign: 'center', lineHeight: 19 },
  closeVoice: { margin: 16, marginBottom: 0, backgroundColor: '#fff', borderWidth: 1, borderColor: COLORS.cardBorder, borderRadius: 14, padding: 14, alignItems: 'center' },
  closeVoiceText: { fontSize: 17, fontWeight: '800', color: COLORS.indigo },
});
