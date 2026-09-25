import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { COLORS, TOUCH, TYPE } from '../theme';

export function Screen({ children, style }) {
  return (
    <SafeAreaView style={[styles.safe, style]}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

export function Card({ children, style }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function BigButton({ title, onPress, variant = 'primary', disabled }) {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      onPress={onPress}
      disabled={disabled}
      style={[
        styles.btn,
        variant === 'primary' && styles.btnPrimary,
        variant === 'light' && styles.btnLight,
        variant === 'mint' && styles.btnMint,
        variant === 'gold' && styles.btnGold,
        variant === 'danger' && styles.btnDanger,
        variant === 'outline' && styles.btnOutline,
        disabled && { opacity: 0.5 },
      ]}
    >
      <Text style={[styles.btnText, variant === 'light' || variant === 'outline' ? { color: COLORS.indigo } : null]}>{title}</Text>
    </TouchableOpacity>
  );
}

export function SectionTitle({ eyebrow, title, sub }) {
  return (
    <View style={{ marginBottom: 12 }}>
      {eyebrow ? <Text style={styles.eyebrow}>{eyebrow}</Text> : null}
      <Text style={styles.title}>{title}</Text>
      {sub ? <Text style={styles.sub}>{sub}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.cream },
  scroll: { padding: 20, paddingBottom: 120, gap: 16 },
  card: {
    backgroundColor: COLORS.paper,
    borderColor: COLORS.cardBorder,
    borderWidth: 1,
    borderRadius: 24,
    padding: 20,
  },
  eyebrow: { fontSize: 12, letterSpacing: 2, color: COLORS.muted, fontWeight: '700', textTransform: 'uppercase' },
  title: { fontSize: TYPE.title, fontWeight: '800', color: COLORS.text, marginTop: 4 },
  sub: { fontSize: TYPE.body, color: COLORS.muted, marginTop: 4, lineHeight: 26 },
  btn: {
    minHeight: TOUCH.bigButton,
    borderRadius: TOUCH.radius,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  btnPrimary: { backgroundColor: COLORS.indigo },
  btnLight: { backgroundColor: '#ffffff', borderWidth: 1, borderColor: COLORS.cardBorder },
  btnMint: { backgroundColor: COLORS.mint },
  btnGold: { backgroundColor: COLORS.peach },
  btnDanger: { backgroundColor: COLORS.danger },
  btnOutline: { backgroundColor: '#ffffff', borderWidth: 1, borderColor: COLORS.indigo },
  btnText: { color: '#ffffff', fontSize: 19, fontWeight: '800' },
});
