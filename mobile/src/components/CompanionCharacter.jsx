import React, { useCallback, useEffect, useRef } from 'react';
import { StyleSheet, View } from 'react-native';
import LottieView from 'lottie-react-native';
import { COLORS } from '../theme';

// Looping ambient states. Mirrors backend reply `mood` names where relevant.
const STATE_SOURCES = {
  idle: require('../../assets/lottie/idle.json'),
  listening: require('../../assets/lottie/listening.json'),
  thinking: require('../../assets/lottie/thinking.json'),
  speaking: require('../../assets/lottie/speaking.json'),
};

// One-shot reaction animations played after a reply, then back to ambient.
const REACTION_SOURCES = {
  happy: require('../../assets/lottie/happy.json'),
  encourage: require('../../assets/lottie/encourage.json'),
  wave: require('../../assets/lottie/wave.json'),
};

// Fallback if onAnimationFinish never fires (e.g. player hiccup).
const REACTION_TIMEOUT_MS = 4000;

const STATE_LABELS = {
  idle: 'MEMORA is resting with you',
  listening: 'MEMORA is listening',
  thinking: 'MEMORA is thinking',
  speaking: 'MEMORA is speaking',
};

/**
 * Animated companion character.
 *
 * @param {'idle'|'listening'|'thinking'|'speaking'} state  Ambient loop to show.
 * @param {'happy'|'encourage'|'wave'|null} reaction        Optional one-shot reaction.
 * @param {number} size                                     Rendered box size in px.
 * @param {(reaction: string) => void} onReactionDone        Called when a reaction finishes.
 */
export default function CompanionCharacter({ state = 'idle', reaction = null, size = 220, onReactionDone }) {
  const ref = useRef(null);
  const doneRef = useRef(false);

  const activeReaction = reaction && REACTION_SOURCES[reaction] ? reaction : null;
  const source = activeReaction ? REACTION_SOURCES[activeReaction] : (STATE_SOURCES[state] || STATE_SOURCES.idle);
  const loop = !activeReaction;

  // Restart playback whenever the shown animation changes.
  useEffect(() => {
    doneRef.current = false;
    const id = setTimeout(() => {
      try {
        ref.current?.play();
      } catch {}
    }, 0);
    return () => clearTimeout(id);
  }, [source]);

  const finish = useCallback(() => {
    if (doneRef.current) return;
    doneRef.current = true;
    if (typeof onReactionDone === 'function') onReactionDone(activeReaction);
  }, [onReactionDone, activeReaction]);

  // Safety net so a stuck animation can never trap the UI in a reaction.
  useEffect(() => {
    if (!activeReaction) return undefined;
    const id = setTimeout(finish, REACTION_TIMEOUT_MS);
    return () => clearTimeout(id);
  }, [activeReaction, finish]);

  const halo = size * 0.84;

  return (
    <View
      style={[styles.wrap, { width: size, height: size }]}
      accessible
      accessibilityRole="image"
      accessibilityLabel={STATE_LABELS[state] || 'MEMORA companion'}
      pointerEvents="none"
    >
      <View style={[styles.halo, { width: halo, height: halo, borderRadius: halo / 2 }]} />
      <LottieView
        ref={ref}
        source={source}
        autoPlay
        loop={loop}
        speed={0.9}
        resizeMode="contain"
        onAnimationFinish={activeReaction ? finish : undefined}
        style={{ width: size, height: size }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { alignItems: 'center', justifyContent: 'center' },
  halo: {
    position: 'absolute',
    backgroundColor: COLORS.mint,
    opacity: 0.55,
  },
});
