import React, { useCallback, useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { speak } from '../lib/speech';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS } from '../theme';

export default function GamesScreen() {
  const { currentPatient } = useAuth();
  const pid = currentPatient?.id || 1;

  const [config, setConfig] = useState(null);
  const [phase, setPhase] = useState('idle');
  const [input, setInput] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const startRef = useRef(0);
  const timerRef = useRef(null);

  const [gk, setGk] = useState(null);
  const [gkMsg, setGkMsg] = useState('');
  const [att, setAtt] = useState(null);
  const [attMsg, setAttMsg] = useState('');

  const loadGame = useCallback(async () => {
    setLoading(true);
    try {
      const c = await api.getNextGame(pid, 'sequence_memory');
      setConfig(c);
      setPhase('idle');
      setInput([]);
      setResult(null);
    } catch {}
    finally { setLoading(false); }
  }, [pid]);

  const loadExtras = useCallback(async () => {
    try { setGk(await api.getGkQuestion()); setGkMsg(''); } catch {}
    try { setAtt(await api.getAttentionQuestion()); setAttMsg(''); } catch {}
  }, []);

  useEffect(() => {
    loadGame();
    loadExtras();
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [loadGame, loadExtras]);

  function start() {
    if (!config) return;
    setPhase('showing');
    setInput([]);
    setResult(null);
    speak(config.guidance_cue || 'Watch the symbols gently.');
    timerRef.current = setTimeout(() => {
      setPhase('playing');
      startRef.current = Date.now();
      speak('Your turn. Tap them in the same order.');
    }, config.display_duration_ms || 3000);
  }

  async function pick(symbol) {
    if (phase !== 'playing' || !config?.sequence) return;
    const next = [...input, symbol];
    setInput(next);
    if (next.length === config.sequence.length) {
      const latency = Date.now() - startRef.current;
      let mistakes = 0;
      config.sequence.forEach((s, i) => { if (next[i] !== s) mistakes += 1; });
      const ok = mistakes === 0;
      const accuracy = ok ? 1.0 : Math.max(0, 1 - mistakes / config.sequence.length);
      setResult({ ok, latency, accuracy, mistakes });
      setPhase('finished');
      speak(ok ? 'Excellent memory! Well done.' : 'Good try! Practice makes us stronger.');
      try {
        await api.logCognitiveSession({
          patient_id: pid,
          game_type: 'sequence_memory',
          difficulty_level: config.difficulty_level,
          score: ok ? 100 : Math.round(accuracy * 100),
          accuracy,
          reaction_time_ms: latency,
          mistake_count: mistakes,
        });
      } catch {}
    }
  }

  return (
    <Screen>
      <SectionTitle title="AI Cognitive Activities" sub="Gentle exercises. AI tunes the difficulty for you." />

      <Card>
        <View style={styles.gameHead}>
          <Text style={styles.gameTitle}>🧠 Memory Sequence</Text>
          {config ? <Text style={styles.level}>AI Level {config.difficulty_level}</Text> : null}
        </View>
        <Text style={styles.cue}>{config?.guidance_cue || 'Watch the symbols, then tap in order.'}</Text>

        <View style={styles.stage}>
          {phase === 'idle' ? <BigButton title={loading ? 'Loading…' : 'Start Game →'} onPress={start} disabled={loading || !config} /> : null}
          {phase === 'showing' ? (
            <View style={styles.seqRow}>
              {(config?.sequence || []).map((s, i) => (
                <View key={i} style={styles.seqTile}><Text style={styles.seqText}>{s}</Text></View>
              ))}
            </View>
          ) : null}
          {phase === 'playing' ? (
            <View style={{ alignItems: 'center', gap: 8 }}>
              <Text style={styles.progress}>Selected {input.length} of {config?.sequence?.length}</Text>
              <View style={styles.seqRow}>
                {input.map((s, i) => (<Text key={i} style={{ fontSize: 34 }}>{s}</Text>))}
              </View>
            </View>
          ) : null}
          {phase === 'finished' && result ? (
            <View style={{ alignItems: 'center', gap: 8 }}>
              <Text style={[styles.result, { color: result.ok ? COLORS.green : '#b45309' }]}>
                {result.ok ? '✓ Wonderful! Perfect sequence!' : 'Good attempt! Keep enjoying.'}
              </Text>
              <Text style={styles.muted}>Reaction time: {(result.latency / 1000).toFixed(1)}s • AI is tuning next level…</Text>
              <BigButton title="Next AI round →" onPress={loadGame} />
            </View>
          ) : null}
        </View>

        {phase === 'playing' ? (
          <View style={styles.options}>
            {(config?.options || []).map((o, i) => (
              <TouchableOpacity key={i} style={styles.opt} onPress={() => pick(o)}>
                <Text style={{ fontSize: 38 }}>{o}</Text>
              </TouchableOpacity>
            ))}
          </View>
        ) : null}
      </Card>

      <Card>
        <Text style={styles.eyebrow}>Memory recall</Text>
        <Text style={styles.gameTitle}>General Knowledge</Text>
        <Text style={styles.q}>{gk?.question || 'Loading question…'}</Text>
        <View style={styles.optRow}>
          {(gk?.options || []).map((o, i) => (
            <TouchableOpacity
              key={i}
              style={styles.miniOpt}
              onPress={() => {
                const ok = o === gk.answer;
                setGkMsg(ok ? '✓ Correct! Excellent recall.' : 'Try again, you can do it.');
                if (ok) speak('Correct! Excellent recall.');
              }}
            >
              <Text style={styles.miniOptText}>{o}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {gkMsg ? <Text style={styles.feedback}>{gkMsg}</Text> : null}
        <View style={{ height: 10 }} />
        <BigButton title="New question" variant="mint" onPress={async () => { try { setGk(await api.getGkQuestion()); setGkMsg(''); } catch {} }} />
      </Card>

      <Card>
        <Text style={styles.eyebrow}>Visual focus</Text>
        <Text style={styles.gameTitle}>Odd One Out</Text>
        <Text style={styles.q}>{att?.question || 'Spot the difference.'}</Text>
        <View style={styles.optRow}>
          {(att?.options || []).map((o, i) => (
            <TouchableOpacity
              key={i}
              style={styles.miniOpt}
              onPress={() => {
                const ok = o === att.answer;
                setAttMsg(ok ? `✓ Exactly right! ${att.explanation || ''}` : 'Try once more.');
                if (ok) speak('Exactly right! Wonderful focus.');
              }}
            >
              <Text style={styles.miniOptText}>{o}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {attMsg ? <Text style={styles.feedback}>{attMsg}</Text> : null}
        <View style={{ height: 10 }} />
        <BigButton title="New puzzle" variant="gold" onPress={async () => { try { setAtt(await api.getAttentionQuestion()); setAttMsg(''); } catch {} }} />
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  eyebrow: { fontSize: 12, letterSpacing: 2, color: COLORS.muted, fontWeight: '700', textTransform: 'uppercase' },
  gameHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  gameTitle: { fontSize: 22, fontWeight: '800', color: COLORS.text },
  level: { fontSize: 13, fontWeight: '800', color: COLORS.indigo, backgroundColor: '#eef0fc', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 12 },
  cue: { fontSize: 17, color: COLORS.muted, marginVertical: 10, lineHeight: 24 },
  stage: { backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#e8e2d5', borderRadius: 18, padding: 20, minHeight: 170, justifyContent: 'center' },
  seqRow: { flexDirection: 'row', gap: 12, justifyContent: 'center', flexWrap: 'wrap' },
  seqTile: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#eee', borderRadius: 18, padding: 12, minWidth: 64, alignItems: 'center' },
  seqText: { fontSize: 46 },
  progress: { fontSize: 17, fontWeight: '800', color: COLORS.indigo },
  result: { fontSize: 21, fontWeight: '800', textAlign: 'center' },
  muted: { fontSize: 15, color: COLORS.muted, textAlign: 'center' },
  options: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 16, justifyContent: 'center' },
  opt: { width: 76, height: 76, borderRadius: 20, backgroundColor: '#fff', borderWidth: 1, borderColor: '#e2ddd2', alignItems: 'center', justifyContent: 'center' },
  q: { fontSize: 19, fontWeight: '600', color: COLORS.text, marginVertical: 10, lineHeight: 27 },
  optRow: { flexDirection: 'row', gap: 10 },
  miniOpt: { flex: 1, minHeight: 64, backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#e8e2d5', borderRadius: 16, alignItems: 'center', justifyContent: 'center', padding: 8 },
  miniOptText: { fontSize: 16, fontWeight: '700', color: COLORS.text, textAlign: 'center' },
  feedback: { fontSize: 16, fontWeight: '700', color: '#047857', backgroundColor: '#ecfdf5', padding: 12, borderRadius: 12, marginTop: 10 },
});
