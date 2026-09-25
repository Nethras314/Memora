import React, { useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';
import { useAuth } from '../lib/auth';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS } from '../theme';

export default function AuthScreen() {
  const { login, signup } = useAuth();
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError('');
    try {
      if (mode === 'login') await login(email.trim(), password);
      else await signup({ email: email.trim(), password, full_name: fullName.trim() || email.trim(), role: 'caregiver' });
    } catch (e) {
      setError(e?.response?.data?.detail || 'Sign in failed. Check your connection and try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen>
      <View style={styles.logo}>
        <View style={styles.logoIcon}><Text style={{ fontSize: 34, color: '#fff' }}>♡</Text></View>
        <Text style={styles.brand}>MEMORA</Text>
        <Text style={styles.tagline}>TOGETHER, EACH DAY</Text>
      </View>
      <Card>
        <SectionTitle title={mode === 'login' ? 'Welcome back' : 'Create account'} sub="A calm space for memories, routines and games." />
        {mode === 'signup' ? (
          <TextInput style={styles.input} placeholder="Your name" value={fullName} onChangeText={setFullName} autoCapitalize="words" />
        ) : null}
        <TextInput style={styles.input} placeholder="Email" value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
        <TextInput style={styles.input} placeholder="Password" value={password} onChangeText={setPassword} secureTextEntry />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <View style={{ height: 12 }} />
        <BigButton title={busy ? 'Please wait…' : mode === 'login' ? 'Start MEMORA →' : 'Create account →'} onPress={submit} disabled={busy} />
        <View style={{ height: 12 }} />
        <BigButton
          title={mode === 'login' ? 'New here? Create account' : 'Have an account? Sign in'}
          variant="outline"
          onPress={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError(''); }}
        />
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  logo: { alignItems: 'center', marginTop: 24, marginBottom: 8 },
  logoIcon: { width: 72, height: 72, borderRadius: 24, backgroundColor: COLORS.indigo, alignItems: 'center', justifyContent: 'center' },
  brand: { fontSize: 40, fontWeight: '800', color: COLORS.text, marginTop: 10 },
  tagline: { letterSpacing: 3, color: COLORS.muted, fontSize: 12, fontWeight: '700' },
  input: {
    backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#dcd6cc', borderRadius: 14,
    paddingHorizontal: 16, paddingVertical: 16, fontSize: 18, marginTop: 10, minHeight: 60,
  },
  error: { color: COLORS.danger, fontSize: 16, marginTop: 10, fontWeight: '600' },
});
