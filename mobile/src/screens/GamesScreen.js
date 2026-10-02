import React, { useCallback, useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { speak } from '../lib/speech';
import { BigButton, Card, Screen, SectionTitle } from '../components/ui';
import { COLORS } from '../theme';
import { t } from '../i18n';
import PhotoGame from './PhotoGame';

export default function GamesScreen() {
  const { currentPatient } = useAuth();
  const pid = currentPatient?.id || 1;
  const lang = currentPatient?.primary_language || 'en-IN';

  const [config, setConfig] = useState(null);
  const [phase, setPhase] = useState('idle');
  const [input, setInput] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const startRef = useRef(0);

  const [gk, setGk] = useState(null);
  const [gkMsg, setGkMsg] = useState('');
  const [att, setAtt] = useState(null);
  const [attMsg, setAttMsg] = useState('');

  const loadGame = useCallback(async () => {
    setLoading(true);
    setLoadError(false);
    try {
      const c = await api.getNextGame(pid, 'sequence_memory');
      setConfig(c);
      setPhase('idle');
      setInput([]);
      setResult(null);
    } catch {
      setLoadError(true);
    }
    finally { setLoading(false); }
  }, [pid]);

  const loadExtras = useCallback(async () => {
    try {
      const q = await api.getGkQuestion(lang);
      setGk(q);
      setGkMsg('');
    } catch {}
    try {
      const a = await api.getAttentionQuestion(lang);
      setAtt(a);
      setAttMsg('');
    } catch {}
  }, [lang]);

  useEffect(() => {
    loadGame();
    loadExtras();
  }, [loadGame, loadExtras]);

  function start() {
    if (!config) return;
    setPhase('showing');
    setInput([]);
    setResult(null);
    speak(config.guidance_cue || t(lang, 'watchSymbols'), lang);
  }

  function beginPlay() {
    setPhase('playing');
    startRef.current = Date.now();
    speak(t(lang, 'tapInOrder'), lang);
  }

  function hearGk() {
    if (!gk) return;
    speak(`${gk.question} ${gk.options.join(', ')}`, lang);
  }

  function hearAtt() {
    if (!att) return;
    speak(`${att.question} ${att.options.join(', ')}`, lang);
  }

  function hearSequence() {
    if (!config) return;
    speak(config.guidance_cue || t(lang, 'watchSymbols'), lang);
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
      setResult({ ok });
      setPhase('finished');
      speak(ok ? t(lang, 'wonderfulPerfect') : t(lang, 'lovelyEffort'), lang);
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
      <SectionTitle title={t(lang, 'gamesTitle')} sub={t(lang, 'gamesSub')} />

      <PhotoGame />

      <Card>
        <View style={styles.gameHead}>
          <Text style={styles.gameTitle}>🧠 {t(lang, 'memorySequence')}</Text>
        </View>
        <Text style={styles.cue}>{config?.guidance_cue || t(lang, 'watchSymbols')}</Text>
        <BigButton title={`🔊 ${t(lang, 'hearAgain')}`} variant="mint" onPress={hearSequence} />

        <View style={styles.stage}>
          {phase === 'idle' ? (
            loadError ? (
              <View style={{ alignItems: 'center', gap: 10 }}>
                <Text style={styles.result}>{t(lang, 'loadErrorMsg')}</Text>
                <BigButton title={t(lang, 'tryAgain')} variant="outline" onPress={loadGame} />
              </View>
            ) : (
              <BigButton title={loading ? 'Loading…' : t(lang, 'startGame')} onPress={start} disabled={loading || !config} />
            )
          ) : null}
          {phase === 'showing' ? (
            <View style={{ alignItems: 'center', gap: 16 }}>
              <View style={styles.seqRow}>
                {(config?.sequence || []).map((s, i) => (
                  <View key={i} style={styles.seqTile}><Text style={styles.seqText}>{s}</Text></View>
                ))}
              </View>
              <BigButton title={t(lang, 'imReadyToTap')} onPress={beginPlay} />
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
              <Text style={[styles.result, { color: result.ok ? COLORS.green : COLORS.indigo }]}>
                {result.ok ? t(lang, 'wonderfulPerfect') : t(lang, 'lovelyEffort')}
              </Text>
              <BigButton title={t(lang, 'nextRound')} onPress={loadGame} />
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
        <Text style={styles.eyebrow}>{t(lang, 'memoryRecall')}</Text>
        <Text style={styles.gameTitle}>{t(lang, 'generalKnowledge')}</Text>
        <Text style={styles.q}>{gk?.question || t(lang, 'loadingQuestion')}</Text>
        <View style={styles.optRow}>
          {(gk?.options || []).map((o, i) => (
            <TouchableOpacity
              key={i}
              style={styles.miniOpt}
              onPress={() => {
                speak(o, lang);
                const ok = o === gk.answer;
                setGkMsg(ok ? `✓ ${t(lang, 'correctRecall')}` : t(lang, 'tryOnceMore'));
                if (ok) speak(t(lang, 'correctRecall'), lang);
              }}
            >
              <Text style={styles.miniOptText}>{o}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {gkMsg ? <Text style={styles.feedback}>{gkMsg}</Text> : null}
        <View style={{ height: 10 }} />
        <View style={{ flexDirection: 'row', gap: 10 }}>
          <View style={{ flex: 1 }}><BigButton title={`🔊 ${t(lang, 'hearAgain')}`} variant="mint" onPress={hearGk} /></View>
          <View style={{ flex: 1 }}><BigButton title={t(lang, 'newQuestion')} variant="mint" onPress={async () => { try { setGk(await api.getGkQuestion(lang)); setGkMsg(''); } catch {} }} /></View>
        </View>
      </Card>

      <Card>
        <Text style={styles.eyebrow}>{t(lang, 'visualFocus')}</Text>
        <Text style={styles.gameTitle}>{t(lang, 'oddOneOut')}</Text>
        <Text style={styles.q}>{att?.question || t(lang, 'loadingQuestion')}</Text>
        <View style={styles.optRow}>
          {(att?.options || []).map((o, i) => (
            <TouchableOpacity
              key={i}
              style={styles.miniOpt}
              onPress={() => {
                speak(o, lang);
                const ok = o === att.answer;
                setAttMsg(ok ? `✓ ${t(lang, 'exactlyRight')} ${att.explanation || ''}` : t(lang, 'tryOnceMore'));
                if (ok) speak(`${t(lang, 'exactlyRight')} ${att.explanation || ''}`, lang);
              }}
            >
              <Text style={styles.miniOptText}>{o}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {attMsg ? <Text style={styles.feedback}>{attMsg}</Text> : null}
        <View style={{ height: 10 }} />
        <View style={{ flexDirection: 'row', gap: 10 }}>
          <View style={{ flex: 1 }}><BigButton title={`🔊 ${t(lang, 'hearAgain')}`} variant="mint" onPress={hearAtt} /></View>
          <View style={{ flex: 1 }}><BigButton title={t(lang, 'newPuzzle')} variant="gold" onPress={async () => { try { setAtt(await api.getAttentionQuestion(lang)); setAttMsg(''); } catch {} }} /></View>
        </View>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  eyebrow: { fontSize: 12, letterSpacing: 2, color: COLORS.muted, fontWeight: '700', textTransform: 'uppercase' },
  gameHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  gameTitle: { fontSize: 22, fontWeight: '800', color: COLORS.text },
  cue: { fontSize: 17, color: COLORS.muted, marginVertical: 10, lineHeight: 24 },
  stage: { backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#e8e2d5', borderRadius: 18, padding: 20, minHeight: 170, justifyContent: 'center' },
  seqRow: { flexDirection: 'row', gap: 12, justifyContent: 'center', flexWrap: 'wrap' },
  seqTile: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#eee', borderRadius: 18, padding: 12, minWidth: 64, alignItems: 'center' },
  seqText: { fontSize: 46 },
  progress: { fontSize: 17, fontWeight: '800', color: COLORS.indigo },
  result: { fontSize: 21, fontWeight: '800', textAlign: 'center' },
  options: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 16, justifyContent: 'center' },
  opt: { width: 76, height: 76, borderRadius: 20, backgroundColor: '#fff', borderWidth: 1, borderColor: '#e2ddd2', alignItems: 'center', justifyContent: 'center' },
  q: { fontSize: 19, fontWeight: '600', color: COLORS.text, marginVertical: 10, lineHeight: 27 },
  optRow: { flexDirection: 'row', gap: 10 },
  miniOpt: { flex: 1, minHeight: 64, backgroundColor: COLORS.cream, borderWidth: 1, borderColor: '#e8e2d5', borderRadius: 16, alignItems: 'center', justifyContent: 'center', padding: 8 },
  miniOptText: { fontSize: 16, fontWeight: '700', color: COLORS.text, textAlign: 'center' },
  feedback: { fontSize: 16, fontWeight: '700', color: '#047857', backgroundColor: '#ecfdf5', padding: 12, borderRadius: 12, marginTop: 10 },
});
