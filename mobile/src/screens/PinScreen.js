import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS } from '../theme';

export default function PinScreen({ onUnlocked, onCancel }) {
  const { currentPatient, setPinVerified } = useAuth();
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function verify(next) {
    if (next.length < 4 || busy) return;
    setBusy(true);
    setError('');
    try {
      await api.verifyPin(next, currentPatient?.id || 1);
      setPinVerified(true);
      setPin('');
      onUnlocked?.();
    } catch {
      setError('Incorrect PIN. Please try again or ask family.');
      setPin('');
    } finally {
      setBusy(false);
    }
  }

  function digit(d) {
    const next = (pin + d).slice(0, 4);
    setPin(next);
    setError('');
    if (next.length === 4) verify(next);
  }

  return (
    <Screen>
      <Card style={{ alignItems: 'center' }}>
        <SectionTitle eyebrow="Private" title="🔐 Memory Bank" sub="Enter the 4-digit PIN to open familiar moments." />
        <View style={styles.dots}>
          {[0, 1, 2, 3].map((i) => (
            <View key={i} style={[styles.dot, pin.length > i && styles.dotOn]} />
          ))}
        </View>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <View style={styles.pad}>
          {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((n) => (
            <TouchableOpacity key={n} style={styles.key} onPress={() => digit(n)}>
              <Text style={styles.keyText}>{n}</Text>
            </TouchableOpacity>
          ))}
          <TouchableOpacity style={styles.key} onPress={() => { setPin(''); setError(''); }}>
            <Text style={styles.keySmall}>Clear</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.key} onPress={() => digit('0')}>
            <Text style={styles.keyText}>0</Text>
          </TouchableOpacity>
          <View style={[styles.key, styles.keyGhost]}><Text style={styles.keySmall}>4 digits</Text></View>
        </View>
        <View style={{ height: 12 }} />
        <BigButton title="← Back" variant="outline" onPress={onCancel} />
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  dots: { flexDirection: 'row', gap: 16, marginVertical: 16 },
  dot: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, borderColor: '#c9c4ba' },
  dotOn: { backgroundColor: COLORS.indigo, borderColor: COLORS.indigo },
  error: { color: COLORS.danger, fontSize: 17, fontWeight: '700', textAlign: 'center', marginBottom: 8 },
  pad: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, justifyContent: 'center', maxWidth: 340 },
  key: {
    width: 100, height: 72, borderRadius: 18, backgroundColor: COLORS.cream,
    borderWidth: 1, borderColor: '#e8e2d5', alignItems: 'center', justifyContent: 'center',
  },
  keyGhost: { backgroundColor: 'transparent', borderWidth: 0 },
  keyText: { fontSize: 28, fontWeight: '700', color: COLORS.text },
  keySmall: { fontSize: 15, fontWeight: '700', color: COLORS.muted },
});
